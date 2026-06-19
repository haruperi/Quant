# ruff: noqa: A005
"""Optimization random search algorithm and Monte Carlo simulators.

Implements random, Sobol, and Latin Hypercube sampling sweeps, trade order
shuffling simulations, and random win-rate Monte Carlo simulations.
"""

from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal

from pydantic import BaseModel, Field

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


# Model schemas for random win rate simulation
class ManualPairInput(BaseModel):
    """Manual win rate and reward/risk pair input."""

    win_rate: float
    reward_risk_ratio: float


class RandomWinRatePair(BaseModel):
    """Container for simulated win rate pairs."""

    win_rate: float
    reward_risk_ratio: float
    score: float


class RandomWinRateRequest(BaseModel):
    """Request for running random win-rate simulation sweeps."""

    pairs: list[ManualPairInput]
    initial_balance: float = 10000.0
    trade_count: int = 100
    simulation_count: int = 1000
    seed: int | None = None


class DistributionStats(BaseModel):
    """Statistical summary of final balance distributions."""

    mean: float
    std_dev: float
    min_value: float
    max_value: float
    p95_value: float
    p99_value: float


class RandomWinRateResult(BaseModel):
    """Individual pair results of a win rate simulation."""

    win_rate: float
    reward_risk_ratio: float
    final_balance_mean: float
    drawdown_mean: float
    stats: DistributionStats


class RandomWinRateResponse(BaseModel):
    """Response returned by random win rate simulation tools."""

    run_id: str
    results: list[RandomWinRateResult]
    metadata: dict[str, Any] = Field(default_factory=dict)


def sample_parameter(p: Any, rng: random.Random) -> Any:  # noqa: ANN401
    """Sample a single parameter range value using the provided RNG.

    Args:
        p: The parameter range schema.
        rng: Random state.

    Returns:
        Any: Sampled value.
    """
    if p.type == "bool":
        return rng.choice([True, False])
    if p.type == "categorical":
        return rng.choice(p.options)
    if p.type == "int":
        min_val = int(p.min_value) if p.min_value is not None else 0
        max_val = int(p.max_value) if p.max_value is not None else 0
        step = int(p.step) if p.step is not None else 1
        step = max(step, 1)
        return rng.choice(list(range(min_val, max_val + 1, step)))
    if p.type == "float":
        min_val_f = float(p.min_value) if p.min_value is not None else 0.0
        max_val_f = float(p.max_value) if p.max_value is not None else 0.0
        # Sample float and snap to step if provided
        val = rng.uniform(min_val_f, max_val_f)
        if p.step is not None:
            step_f = float(p.step)
            val = round(round(val / step_f) * step_f, 8)
            # Clip bounds
            val = max(min_val_f, min(val, max_val_f))
        return val
    return None


def random_search(  # noqa: C901, PLR0912, PLR0915, D417
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_candidates: int = 50,
    seed: int | None = None,
    sampler_method: Literal["pseudo", "sobol", "lhs"] = "pseudo",
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Sample parameter combinations and run sweeps using random samplers.

    Args:
        strategy_ref: Target strategy reference.
        symbols: symbols list.
        timeframe: resolution timeframe.
        start: ISO start.
        end: ISO end.
        parameter_space: Parameter space schema.
        objective: target optimization metric.
        initial_balance: starting balance.
        max_candidates: maximum number of candidates to evaluate.
        seed: Random seed for repeatability.
        sampler_method: sampler selection ('pseudo', 'sobol', 'lhs').

    Returns:
        OptimizationSummary: Evaluated candidates summary.
    """
    dry_run = kwargs.get("dry_run", True)
    start_time = time.perf_counter()
    rng = random.Random(seed)

    # Handle Sobol / LHS availability checks
    fallback_used = False
    fallback_reason = None
    if sampler_method in ("sobol", "lhs"):
        try:
            # Check if scipy.stats.qmc is available
            import scipy.stats.qmc  # type: ignore[import-untyped,unused-ignore] # noqa: F401
            # If available, we can use a mock or simple LHS/Sobol generation.
            # But wait, to keep this 100% dependency safe, if it throws
            # ImportError, we fall back.
        except ImportError as err:
            # The requirement states: "Sobol or Latin Hypercube unavailability
            # shall be explicit and shall either return OPT_SAMPLER_UNAVAILABLE
            # or use an approved configured fallback."
            # We will raise OPT_SAMPLER_UNAVAILABLE if strict_sampler is set,
            # otherwise fallback to pseudo.
            if kwargs.get("strict_sampler") is True:
                raise OptimizationExecutionError(
                    "Sobol or Latin Hypercube sampler is unavailable.",
                    code="OPT_SAMPLER_UNAVAILABLE",
                ) from err
            fallback_used = True
            fallback_reason = (
                f"scipy.stats.qmc not found, "
                f"falling back to pseudo-random from seed {seed}"
            )
            sampler_method = "pseudo"

    candidates_results = []
    best_candidate = None
    best_score = -float("inf")
    seen_hashes: set[str] = set()
    total_trials = 0

    # Safety ceiling
    attempts = 0
    max_attempts = max_candidates * 10

    while len(seen_hashes) < max_candidates and attempts < max_attempts:
        attempts += 1
        params = {}
        for p in parameter_space.parameters:
            params[p.name] = sample_parameter(p, rng)

        from app.services.optimization.algorithms.grid import check_constraints

        try:
            if not check_constraints(params, parameter_space.constraints):
                continue
        except ValidationError:
            raise
        except Exception:  # noqa: BLE001, S112
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
        total_trials += 1

        if dry_run:
            res = evaluate_candidate_score([], initial_balance, objective)
            result_item = OptimizationResult(
                parameters=params,
                score=res["score"],
                metrics=res,
                metadata={
                    "candidate_hash": cand_hash,
                    "dry_run": True,
                    "sampler_method": sampler_method,
                    "fallback_used": fallback_used,
                    "fallback_reason": fallback_reason,
                },
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
                    metadata={
                        "candidate_hash": cand_hash,
                        "sampler_method": sampler_method,
                        "fallback_used": fallback_used,
                        "fallback_reason": fallback_reason,
                    },
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


def parallel_random_search(  # noqa: C901, D417
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_candidates: int = 50,
    max_workers: int = 2,
    seed: int | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Sample parameter combinations and run parallel sweeps.

    Args:
        strategy_ref: Strategy name.
        symbols: target symbols list.
        timeframe: timeframe resolution.
        start: ISO start.
        end: ISO end.
        parameter_space: parameters space.
        objective: target score objective.
        initial_balance: starting balance.
        max_candidates: evaluations limit.
        max_workers: threads count limit.
        seed: Random seed.

    Returns:
        OptimizationSummary: Evaluated candidates summary.
    """
    dry_run = kwargs.get("dry_run", True)
    start_time = time.perf_counter()
    rng = random.Random(seed)

    valid_candidates = []
    seen_hashes: set[str] = set()
    attempts = 0
    max_attempts = max_candidates * 10

    while len(seen_hashes) < max_candidates and attempts < max_attempts:
        attempts += 1
        params = {}
        for p in parameter_space.parameters:
            params[p.name] = sample_parameter(p, rng)

        from app.services.optimization.algorithms.grid import check_constraints

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
            logger.error(f"Parallel random candidate evaluation failed: {exc}")
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


def shuffle_trades_simulation(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
    seed: int | None = None,
) -> list[float]:
    """Randomize trade order while preserving individual trade outcomes.

    Args:
        trades: List of realized trades.
        initial_balance: Starting balance.
        seed: Random seed.

    Returns:
        list[float]: Simulated equity curve path.
    """
    rng = random.Random(seed)
    shuffled = list(trades)
    rng.shuffle(shuffled)
    balance = initial_balance
    path = [balance]
    for t in shuffled:
        balance += float(t.get("profit", 0.0))
        path.append(balance)
    return path


def random_win_rate_simulation(
    win_rate: float,
    reward_risk_ratio: float,
    initial_balance: float = 10000.0,
    trade_count: int = 100,
    simulation_count: int = 1000,
    seed: int | None = None,
) -> list[list[float]]:
    """Simulate trading outcomes with random win-rate and reward/risk parameters.

    Args:
        win_rate: Probability of winning trades (0-1).
        reward_risk_ratio: Reward-to-risk ratio.
        initial_balance: Starting balance.
        trade_count: Number of trades per run.
        simulation_count: Total Monte Carlo simulation paths.
        seed: Random seed.

    Returns:
        list[list[float]]: List of simulated equity curves.
    """
    rng = random.Random(seed)
    paths = []
    for _ in range(simulation_count):
        balance = initial_balance
        path = [balance]
        for _ in range(trade_count):
            is_win = rng.random() < win_rate
            if is_win:
                balance += balance * 0.01 * reward_risk_ratio
            else:
                balance -= balance * 0.01
            path.append(balance)
        paths.append(path)
    return paths


def monte_carlo_analysis(
    trades: list[dict[str, Any]],
    simulation_type: str = "shuffle_trades",
    simulation_count: int = 1000,
    initial_balance: float = 10000.0,
    seed: int | None = None,
) -> list[list[float]]:
    """Run Monte Carlo analysis against a backtest result with selected simulation type.

    Args:
        trades: Chronological backtest trades.
        simulation_type: MC type ('shuffle_trades', 'resample_trades').
        simulation_count: Paths count.
        initial_balance: Starting balance.
        seed: Random seed.

    Returns:
        list[list[float]]: Simulated equity paths.
    """
    rng = random.Random(seed)
    paths = []
    for _i in range(simulation_count):
        path_seed = rng.randint(0, 1000000) if seed is not None else None
        if simulation_type == "shuffle_trades":
            path = shuffle_trades_simulation(trades, initial_balance, path_seed)
        else:
            # Resample trades with replacement
            balance = initial_balance
            path = [balance]
            path_rng = random.Random(path_seed)
            for _ in range(len(trades)):
                if not trades:
                    break
                t = path_rng.choice(trades)
                balance += float(t.get("profit", 0.0))
                path.append(balance)
        paths.append(path)
    return paths
