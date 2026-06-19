"""Optimization Service helpers and backtest adapters.

Provides execution helpers, dynamic strategy loading, parameter space hashing,
and JSON-safe serialization contracts.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import math
import sys
import warnings
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from app.utils.errors import Error
from app.utils.standard import StandardResponse, canonical_json

if TYPE_CHECKING:
    from app.services.optimization.models import ParameterSpace

# Constants
Infinity = float("inf")
OPT_JSON_SERIALIZATION_FAILED = "OPT_JSON_SERIALIZATION_FAILED"


class OptimizationExecutionError(Error):
    """Execution error within the optimization service."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize optimization execution error."""
        super().__init__(message)
        self.code = code or "OPT_EXECUTION_FAILED"


@dataclass(frozen=True, slots=True)
class EngineOptimizationResult:
    """Optimization-ready result contract built from engine outputs."""

    run_id: str
    ending_balance: float
    net_profit: float
    total_trades: int
    trades: list[dict[str, Any]]
    processed_ticks: int
    analytics: dict[str, Any]
    success: bool


def strategy_id(strategy: Any) -> str:  # noqa: ANN401
    """Return the deterministic strategy identifier for a strategy class or instance.

    Args:
        strategy: Strategy class, instance, or identifier.

    Returns:
        str: Deterministic strategy identifier.
    """
    if isinstance(strategy, type):
        return str(strategy.__name__)
    if hasattr(strategy, "strategy_ref"):
        return str(strategy.strategy_ref)
    if hasattr(strategy, "__name__"):
        return str(strategy.__name__)
    return str(type(strategy).__name__)


def normalize_engine_type(engine_type: str) -> str:
    """Normalize legacy engine labels to supported execution engine names.

    Args:
        engine_type: Candidate engine label.

    Returns:
        str: Normalized engine name.
    """
    if not engine_type:
        return "event_driven"
    val = engine_type.strip().lower()
    if val in ("legacy", "event_driven", "eventdriven", "event-driven"):
        return "event_driven"
    return val


def load_strategy_from_path(file_path: str, class_name: str) -> type:
    """Load a strategy class from a python file dynamically.

    Args:
        file_path: Path to python file.
        class_name: Target class name to load.

    Returns:
        type: Loaded class object.

    Raises:
        OptimizationExecutionError: If loading fails.
    """
    path = Path(file_path)
    if not path.exists():
        msg = f"Strategy file not found: {file_path}"
        raise OptimizationExecutionError(
            msg,
            code="OPT_STRATEGY_LOAD_FAILED",
        )

    module_name = f"dynamic_strategy_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise OptimizationExecutionError(
            "Could not build module spec.",
            code="OPT_STRATEGY_LOAD_FAILED",
        )

    try:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        strategy_class = getattr(module, class_name)
        return cast("type", strategy_class)
    except Exception as exc:
        msg = f"Failed to load strategy class: {exc}"
        raise OptimizationExecutionError(
            msg,
            code="OPT_STRATEGY_LOAD_FAILED",
        ) from exc


def run_strategy_backtest(  # noqa: C901, PLR0912, PLR0915, D417
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameters: dict[str, Any],
    initial_balance: float = 10000.0,
    engine_type: str = "event_driven",
    **kwargs: Any,  # noqa: ANN401
) -> EngineOptimizationResult:
    """Run one optimization candidate through the backtest engine.

    Args:
        strategy_ref: Strategy name reference.
        symbols: symbols list.
        timeframe: Bar timeframe.
        start: ISO start date.
        end: ISO end date.
        parameters: Strategy configuration parameters.
        initial_balance: Starting cash balance.
        engine_type: Engine implementation selection.

    Returns:
        EngineOptimizationResult: Converted backtest metrics.

    Raises:
        OptimizationExecutionError: If execution fails.
    """
    if not strategy_ref:
        raise OptimizationExecutionError(
            "strategy_ref is required.", code="OPT_STRATEGY_LOAD_FAILED"
        )
    if not symbols:
        raise OptimizationExecutionError(
            "symbols cannot be empty.", code="OPT_SYMBOL_SETUP_FAILED"
        )

    normalized_engine = normalize_engine_type(engine_type)
    if normalized_engine != "event_driven":
        msg = f"Unsupported engine type: {engine_type}"
        raise OptimizationExecutionError(
            msg,
            code="OPT_ENGINE_CREATION_FAILED",
        )

    adapter_version = kwargs.get("adapter_version", "0.8.0")
    if adapter_version != "0.8.0":
        raise OptimizationExecutionError(
            "Backtest adapter version mismatch.",
            code="OPT_CANDIDATE_EXECUTION_FAILED",
        )

    if (
        kwargs.get("stochastic_realism") is True
        and kwargs.get("deterministic_only") is True
    ):
        raise OptimizationExecutionError(
            "Stochastic realism is active in deterministic-only mode.",
            code="OPT_NOISY_OBJECTIVE_NOT_ALLOWED",
        )

    from app.services.simulator.engine import EventDrivenExecutionEngine
    from app.services.simulator.orchestrator import BacktestOrchestrator

    engine = EventDrivenExecutionEngine()
    orchestrator = BacktestOrchestrator(engine=engine)

    payload = {
        "request_id": kwargs.get("request_id") or "opt_req_123",
        "actor_context": kwargs.get("actor_context")
        or {"actor_id": "optimization-service", "roles": ["researcher"]},
        "strategy_ref": strategy_ref,
        "symbols": symbols,
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "strategy_config": parameters,
        "initial_balance": initial_balance,
        "metadata": kwargs.get("metadata") or {},
    }

    try:
        response = orchestrator.execute(payload)
    except Exception as exc:
        msg = f"Candidate execution failed: {exc}"
        raise OptimizationExecutionError(
            msg,
            code="OPT_CANDIDATE_EXECUTION_FAILED",
        ) from exc

    if response.get("status") == "error":
        err = response.get("error") or {}
        code = err.get("code") or "OPT_CANDIDATE_EXECUTION_FAILED"
        details = err.get("details") or response.get("message") or "Backtest run failed"
        raise OptimizationExecutionError(details, code=code)

    data = response.get("data") or {}
    run_id = data.get("run_id") or "unknown_run"
    metrics = data.get("summary_metrics") or {}

    # Extract deals from engine state
    deals_list: list[dict[str, Any]] = []
    for deal in engine.deals.values():
        deals_list.append(
            {
                "deal_id": deal.deal_id,
                "order_id": deal.order_id,
                "symbol": deal.symbol,
                "side": str(deal.side),
                "volume": deal.volume,
                "price": deal.price,
                "commission": deal.commission,
                "margin": deal.margin,
                "executed_at": deal.executed_at,
            }
        )

    # Pair deals into round-trip closed trades
    realized_trades = []
    open_buys: dict[str, list[dict[str, Any]]] = {}
    open_sells: dict[str, list[dict[str, Any]]] = {}

    sorted_deals = sorted(deals_list, key=lambda d: d["executed_at"])
    for d_dict in sorted_deals:
        sym = str(d_dict["symbol"])
        side = str(d_dict["side"])
        vol = float(d_dict["volume"])
        price = float(d_dict["price"])
        comm = float(d_dict["commission"])

        if "buy" in side.lower():
            if open_sells.get(sym):
                match = open_sells[sym].pop(0)
                profit = (match["price"] - price) * vol * 100000.0 - (
                    comm + match["commission"]
                )
                realized_trades.append(
                    {
                        "symbol": sym,
                        "direction": "sell",
                        "open_price": match["price"],
                        "close_price": price,
                        "volume": vol,
                        "profit": profit,
                        "open_time": match["executed_at"],
                        "close_time": d_dict["executed_at"],
                    }
                )
            else:
                open_buys.setdefault(sym, []).append(d_dict)
        elif open_buys.get(sym):
            match = open_buys[sym].pop(0)
            profit = (price - match["price"]) * vol * 100000.0 - (
                comm + match["commission"]
            )
            realized_trades.append(
                {
                    "symbol": sym,
                    "direction": "buy",
                    "open_price": match["price"],
                    "close_price": price,
                    "volume": vol,
                    "profit": profit,
                    "open_time": match["executed_at"],
                    "close_time": d_dict["executed_at"],
                }
            )
        else:
            open_sells.setdefault(sym, []).append(d_dict)

    ending_balance = metrics.get("ending_balance", initial_balance)
    net_profit = ending_balance - initial_balance

    return EngineOptimizationResult(
        run_id=run_id,
        ending_balance=ending_balance,
        net_profit=net_profit,
        total_trades=len(realized_trades),
        trades=realized_trades,
        processed_ticks=int(metrics.get("processed_ticks", 0)),
        analytics=metrics,
        success=True,
    )


def run_strategy_backtest_from_path(
    file_path: str,
    class_name: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameters: dict[str, Any],
    initial_balance: float = 10000.0,
    engine_type: str = "event_driven",
    **kwargs: Any,  # noqa: ANN401
) -> EngineOptimizationResult:
    """Load a strategy class from disk and run one candidate simulation.

    Args:
        file_path: Strategy source code file path.
        class_name: Class name in module.
        symbols: symbols list.
        timeframe: resolution timeframe.
        start: start date ISO string.
        end: end date ISO string.
        parameters: Strategy config dictionary.
        initial_balance: initial balance.
        engine_type: engine type label.
        kwargs: Extra keyword arguments.

    Returns:
        EngineOptimizationResult: simulator execution result.
    """
    strategy_class = load_strategy_from_path(file_path, class_name)
    setattr(strategy_class, "strategy_id", class_name)  # noqa: B010
    from app.services.strategies.registry import register_strategy

    register_strategy(strategy_class)

    return run_strategy_backtest(
        strategy_ref=strategy_class.__name__,
        symbols=symbols,
        timeframe=timeframe,
        start=start,
        end=end,
        parameters=parameters,
        initial_balance=initial_balance,
        engine_type=engine_type,
        **kwargs,
    )


def parameter_space_hash(parameter_space: ParameterSpace) -> str:
    """Generate a deterministic order-invariant SHA-256 hash of a parameter space.

    Args:
        parameter_space: The parameter space definition.

    Returns:
        str: 64-character hex hash representation.
    """
    sorted_params = sorted(parameter_space.parameters, key=lambda p: p.name)
    param_list = []
    for p in sorted_params:
        p_dict = p.model_dump()
        for k in ("min_value", "max_value", "step"):
            if p_dict.get(k) is not None:
                p_dict[k] = round(float(p_dict[k]), 8)
        if p_dict.get("options") is not None:
            with contextlib.suppress(Exception):
                p_dict["options"] = sorted(p_dict["options"])
        param_list.append(p_dict)

    sorted_constraints = sorted(parameter_space.constraints)

    canonical_repr = {
        "parameters": param_list,
        "constraints": sorted_constraints,
    }

    json_bytes = canonical_json(canonical_repr).encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()


def get_active_parameters(
    parameters: dict[str, Any], space: ParameterSpace
) -> dict[str, Any]:
    """Filter out inactive conditional parameters.

    Args:
        parameters: Candidate parameters.
        space: Parameter space schema defining conditionals.

    Returns:
        dict[str, Any]: Only active parameters mapping.
    """
    active = {}
    param_map = {p.name: p for p in space.parameters}

    def is_active(name: str) -> bool:
        p = param_map.get(name)
        if not p:
            return True
        if p.conditional_on is None:
            return True
        parent_name = p.conditional_on
        if not is_active(parent_name):
            return False
        parent_value = parameters.get(parent_name)
        if p.conditional_values is None:
            return False
        return parent_value in p.conditional_values

    for name, val in parameters.items():
        if is_active(name):
            active[name] = round(val, 8) if isinstance(val, float) else val
    return active


def build_candidate_hash(
    strategy_hash: str,
    data_hash: str,
    cost_model_hash: str,
    realism_profile_hash: str,
    objective_hash: str,
    engine_type: str,
    module_version: str,
    parameters: dict[str, Any],
    space: ParameterSpace,
) -> str:
    """Deterministically generate candidate hash.

    Args:
        strategy_hash: strategy ID/code hash.
        data_hash: market data range hash.
        cost_model_hash: cost model configuration hash.
        realism_profile_hash: simulator realism config hash.
        objective_hash: scoring function hash.
        engine_type: backtest engine selection type.
        module_version: optimization package version.
        parameters: candidate parameter dictionary.
        space: parameter space constraints defining active variables.

    Returns:
        str: Deduplication SHA-256 hash.
    """
    active_params = get_active_parameters(parameters, space)
    sorted_params = {k: active_params[k] for k in sorted(active_params)}

    payload = {
        "strategy_hash": strategy_hash,
        "data_hash": data_hash,
        "cost_model_hash": cost_model_hash,
        "realism_profile_hash": realism_profile_hash,
        "objective_hash": objective_hash,
        "engine_type": engine_type.lower().strip(),
        "module_version": module_version,
        "parameters": sorted_params,
    }
    json_bytes = canonical_json(payload).encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()


def json_safe_serialize(obj: Any) -> Any:  # noqa: ANN401, PLR0911
    """Serialize an object into a JSON-safe format.

    Args:
        obj: Input object.

    Returns:
        Any: JSON-safe serialized object.
    """
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            warnings.warn(
                "NaN or Infinity value serialized as null", RuntimeWarning, stacklevel=2
            )
            return None
        return obj
    if isinstance(obj, int | str | bool):
        return obj
    if isinstance(obj, Decimal):
        return str(obj.normalize())
    if isinstance(obj, datetime | date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): json_safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple | set):
        return [json_safe_serialize(v) for v in obj]

    msg = f"Unsupported serialization type: {type(obj)}"
    raise OptimizationExecutionError(
        msg,
        code=OPT_JSON_SERIALIZATION_FAILED,
    )


def parametric_simulation(
    win_rate: float,
    reward_risk_ratio: float,
    risk_per_trade: float,
    trade_count: int,
    simulation_count: int,
    initial_balance: float,
    seed: int | None = None,
) -> dict[str, Any]:
    """Simulate account equity paths using win rate and reward/risk ratios.

    Args:
        win_rate: Probability of winning trades (0-1).
        reward_risk_ratio: Reward-to-risk ratio.
        risk_per_trade: Percentage fraction risked per trade.
        trade_count: Number of consecutive trades per run.
        simulation_count: Total Monte Carlo iterations.
        initial_balance: Starting account balance.
        seed: Random seed for repeatability.

    Returns:
        dict[str, Any]: Compiled paths, drawdowns, and final equity results.
    """
    import random

    if seed is not None:
        random.seed(seed)
    equity_paths = []
    drawdowns = []
    final_equity = []
    for _ in range(simulation_count):
        balance = initial_balance
        path = [balance]
        peak = balance
        dd_path = [0.0]
        for _ in range(trade_count):
            is_win = random.random() < win_rate
            if is_win:
                balance *= 1.0 + risk_per_trade * reward_risk_ratio
            else:
                balance *= 1.0 - risk_per_trade
            path.append(balance)
            peak = max(peak, balance)
            dd = (peak - balance) / peak if peak > 0 else 0.0
            dd_path.append(dd)
        equity_paths.append(path)
        drawdowns.append(dd_path)
        final_equity.append(balance)
    return {
        "equity_paths": equity_paths,
        "drawdowns": drawdowns,
        "final_equity": final_equity,
    }


def optimization_tool_context(**kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
    """Extract standard request parameters from tool keyword arguments."""
    return {
        "request_id": kwargs.get("request_id"),
        "agent_name": kwargs.get("agent_name") or "optimization-agent",
        "environment": kwargs.get("environment") or "BACKTEST",
        "dry_run": kwargs.get("dry_run", True),
    }


def optimization_business_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip out standard routing headers and return business logic payload only."""
    business = dict(payload)
    for k in (
        "request_id",
        "agent_name",
        "environment",
        "dry_run",
        "correlation_id",
        "workflow_id",
    ):
        business.pop(k, None)
    return business


def package_optimization_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Package a strategy request validation envelope without executing search jobs."""
    # Ensure dry_run defaults to True if omitted
    dry_run = payload.get("dry_run", True)

    # We can validate parameters using models
    from app.services.optimization.models import OptimizationRequest

    # Construct request to validate
    req = OptimizationRequest(**payload)

    req_hash = hashlib.sha256(
        canonical_json(req.model_dump()).encode("utf-8")
    ).hexdigest()[:12]
    return {
        "status": "success",
        "message": "Optimization request packaged and validated successfully.",
        "data": {
            "run_id": f"packaged_{req_hash}",
            "dry_run": dry_run,
            "request_payload": req.model_dump(),
        },
    }


def optimization_tool_result(
    tool_name: str,
    status: str,
    request_id: str | None,
    data: Any,  # noqa: ANN401
    errors: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
    audit: dict[str, Any] | None = None,
    side_effects: dict[str, Any] | None = None,
    start_time: float | None = None,
) -> StandardResponse:
    """Build the standard HaruQuant optimization result envelope."""
    from app.utils.standard import build_metadata, error_response, success_response

    inner = {
        "tool_name": tool_name,
        "status": status,
        "request_id": request_id,
        "data": data,
        "errors": errors or [],
        "warnings": warnings or [],
        "audit": audit or {},
        "side_effects": side_effects or {"places_trade": False},
    }

    metadata = build_metadata(
        tool_name=tool_name,
        start_time=start_time,
        request_id=request_id,
        reads=True,
    )

    if status in {"failed", "rejected"}:
        details = (
            str(errors[0].get("details") or "Execution failed")
            if errors
            else "Execution failed"
        )
        return error_response(
            message=f"Tool {tool_name} completed with status: {status}",
            code="TOOL_EXECUTION_FAILED",
            details=details,
            metadata=metadata,
        )

    return success_response(
        message=f"Tool {tool_name} completed successfully.",
        data=inner,
        metadata=metadata,
    )
