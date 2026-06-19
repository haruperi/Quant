"""Optimization grid search algorithm.

Provides strict iterator-based grid sweeps, parameter constraints validation,
and parallel grid search orchestration.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from typing import Any

from app.services.optimization.helpers import (
    OptimizationExecutionError,
    build_candidate_hash,
    run_strategy_backtest,
)
from app.services.optimization.models import (
    OptimizationResult,
    OptimizationSummary,
    ParameterCandidate,
    ParameterSpace,
)
from app.services.optimization.scoring import evaluate_candidate_score
from app.utils.errors import ValidationError
from app.utils.logger import logger


def generate_parameter_grid(space: ParameterSpace) -> dict[str, list[Any]]:
    """Generate search values lists from parameter space definitions.

    Args:
        space: Parameter space boundaries.

    Returns:
        dict[str, list[Any]]: Parameter names mapped to generated sweep values.
    """
    grid: dict[str, list[Any]] = {}
    for p in space.parameters:
        if p.type == "int":
            min_val = int(p.min_value) if p.min_value is not None else 0
            max_val = int(p.max_value) if p.max_value is not None else 0
            step = int(p.step) if p.step is not None else 1
            step = max(step, 1)
            grid[p.name] = list(range(min_val, max_val + 1, step))
        elif p.type == "float":
            min_val_f = float(p.min_value) if p.min_value is not None else 0.0
            max_val_f = float(p.max_value) if p.max_value is not None else 0.0
            step_f = float(p.step) if p.step is not None else 0.1
            step_f = max(step_f, 1e-6)
            vals = []
            curr = min_val_f
            # Add small epsilon to avoid floating point truncation
            while curr <= max_val_f + 1e-9:
                vals.append(round(curr, 8))
                curr += step_f
            grid[p.name] = vals
        elif p.type == "categorical":
            grid[p.name] = list(p.options or [])
        elif p.type == "bool":
            grid[p.name] = [True, False]
    return grid


def check_constraints(params: dict[str, Any], constraints: list[str]) -> bool:
    """Evaluate Python constraint expressions safely against candidate parameters.

    Args:
        params: Parameters to test.
        constraints: Python logic statements.

    Returns:
        bool: True if all expressions evaluate to True.

    Raises:
        ValidationError: If expressions contain unsafe code.
    """
    for constraint in constraints:
        if (
            "__" in constraint
            or "import" in constraint
            or "eval" in constraint
            or "exec" in constraint
        ):
            msg = f"Unsafe constraint expression blocked: {constraint}"
            raise ValidationError(
                msg,
                code="INVALID_INPUT",
            )
        try:
            safe_context = {**params, "abs": abs, "min": min, "max": max}
            if not eval(constraint, {"__builtins__": None}, safe_context):  # noqa: S307
                return False
        except Exception as exc:
            msg = f"Failed to evaluate constraint '{constraint}': {exc}"
            raise ValidationError(
                msg,
                code="INVALID_INPUT",
            ) from exc
    return True


def grid_search(  # noqa: D417
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Exhaustively sweep parameter grid.

    Grid combinations are generated using a strict iterator to keep memory
    usage bounded.

    Args:
        strategy_ref: Target strategy name.
        symbols: symbols ticker array.
        timeframe: resolution timeframe.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameters space boundaries.
        objective: target optimization metric.
        initial_balance: starting balance.

    Returns:
        OptimizationSummary: Evaluated candidates summary.
    """
    dry_run = kwargs.get("dry_run", True)
    start_time = time.perf_counter()

    grid = generate_parameter_grid(parameter_space)
    keys = list(grid.keys())

    # Build Cartesian product iterator
    combinations_iter = product(*(grid[k] for k in keys))

    candidates_results = []
    best_candidate = None
    best_score = -float("inf")
    seen_hashes = set()
    total_trials = 0

    for combo in combinations_iter:
        params = dict(zip(keys, combo, strict=True))
        total_trials += 1

        # Check parameter constraints
        try:
            if not check_constraints(params, parameter_space.constraints):
                continue
        except ValidationError:
            # Re-raise unsafe constraints
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Constraint evaluation failed: {exc}")
            continue

        cand_hash = build_candidate_hash(
            strategy_hash=strategy_ref,
            data_hash=f"{start}_{end}",
            cost_model_hash="default",
            realism_profile_hash="default",
            objective_hash=objective,
            engine_type="event_driven",
            module_version="1.0.0",
            parameters=params,
            space=parameter_space,
        )

        if cand_hash in seen_hashes:
            continue
        seen_hashes.add(cand_hash)

        if dry_run:
            # Dry run returns mock details immediately
            res = evaluate_candidate_score(
                [], initial_balance, objective, trial_count=1
            )
            result_item = OptimizationResult(
                parameters=params,
                score=res["score"],
                metrics=res,
                metadata={"candidate_hash": cand_hash, "dry_run": True},
            )
        else:
            try:
                bt_res = run_strategy_backtest(
                    strategy_ref=strategy_ref,
                    symbols=symbols,
                    timeframe=timeframe,
                    start=start,
                    end=end,
                    parameters=params,
                    initial_balance=initial_balance,
                    **kwargs,
                )
                res = evaluate_candidate_score(
                    bt_res.trades, initial_balance, objective, trial_count=total_trials
                )
                result_item = OptimizationResult(
                    parameters=params,
                    score=res["score"],
                    metrics=res,
                    metadata={"candidate_hash": cand_hash},
                )
            except OptimizationExecutionError as exc:
                logger.error(f"Candidate execution failed: {exc}")
                continue

        candidates_results.append(result_item)
        if result_item.score > best_score:
            best_score = result_item.score
            best_candidate = ParameterCandidate(
                parameters=params, candidate_hash=cand_hash
            )

    # Empty fallback
    if not best_candidate:
        best_candidate = ParameterCandidate(parameters={}, candidate_hash="empty")
        best_score = 0.0

    runtime_ms = (time.perf_counter() - start_time) * 1000
    return OptimizationSummary(
        best_candidate=best_candidate,
        best_score=best_score,
        objective=objective,
        runtime_ms=runtime_ms,
        total_candidates=len(candidates_results),
        candidates=candidates_results,
    )


def parallel_grid_search(  # noqa: C901, D417
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_workers: int = 2,
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Run parameter-grid candidate evaluations in parallel using ThreadPoolExecutor.

    Args:
        strategy_ref: Target strategy name.
        symbols: symbols list.
        timeframe: resolution.
        start: ISO start.
        end: ISO end.
        parameter_space: Parameters space boundaries.
        objective: target metric objective.
        initial_balance: starting balance.
        max_workers: threads concurrency limit.

    Returns:
        OptimizationSummary: Evaluated candidates summary.
    """
    dry_run = kwargs.get("dry_run", True)
    start_time = time.perf_counter()

    grid = generate_parameter_grid(parameter_space)
    keys = list(grid.keys())
    combinations = list(product(*(grid[k] for k in keys)))

    # Filter candidates in-memory before running to support deduplication
    valid_candidates = []
    seen_hashes = set()

    for combo in combinations:
        params = dict(zip(keys, combo, strict=True))
        if not check_constraints(params, parameter_space.constraints):
            continue

        cand_hash = build_candidate_hash(
            strategy_hash=strategy_ref,
            data_hash=f"{start}_{end}",
            cost_model_hash="default",
            realism_profile_hash="default",
            objective_hash=objective,
            engine_type="event_driven",
            module_version="1.0.0",
            parameters=params,
            space=parameter_space,
        )
        if cand_hash in seen_hashes:
            continue
        seen_hashes.add(cand_hash)
        valid_candidates.append((params, cand_hash))

    def eval_one(item: tuple[dict[str, Any], str]) -> OptimizationResult | None:
        params, cand_hash = item
        if dry_run:
            res = evaluate_candidate_score([], initial_balance, objective)
            return OptimizationResult(
                parameters=params,
                score=res["score"],
                metrics=res,
                metadata={"candidate_hash": cand_hash, "dry_run": True},
            )
        try:
            bt_res = run_strategy_backtest(
                strategy_ref=strategy_ref,
                symbols=symbols,
                timeframe=timeframe,
                start=start,
                end=end,
                parameters=params,
                initial_balance=initial_balance,
                **kwargs,
            )
            res = evaluate_candidate_score(
                bt_res.trades,
                initial_balance,
                objective,
                trial_count=len(valid_candidates),
            )
            return OptimizationResult(
                parameters=params,
                score=res["score"],
                metrics=res,
                metadata={"candidate_hash": cand_hash},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Parallel candidate evaluation failed: {exc}")
            return None

    candidates_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(eval_one, valid_candidates)
        for r in results:
            if r is not None:
                candidates_results.append(r)

    best_candidate = None
    best_score = -float("inf")
    for r in candidates_results:
        if r.score > best_score:
            best_score = r.score
            best_candidate = ParameterCandidate(
                parameters=r.parameters,
                candidate_hash=r.metadata.get("candidate_hash", "unknown"),
            )

    if not best_candidate:
        best_candidate = ParameterCandidate(parameters={}, candidate_hash="empty")
        best_score = 0.0

    runtime_ms = (time.perf_counter() - start_time) * 1000
    return OptimizationSummary(
        best_candidate=best_candidate,
        best_score=best_score,
        objective=objective,
        runtime_ms=runtime_ms,
        total_candidates=len(candidates_results),
        candidates=candidates_results,
    )
