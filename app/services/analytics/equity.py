"""Equity and return series calculations for Analytics.

Implements all metrics, statistics, and series conversions based on equity curve logs.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, cast

from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError


def _validate_request_id(request_id: str | None) -> None:
    """Helper to validate request_id strictly."""
    if request_id is not None:
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValidationError("request_id must be a non-empty string.")


def _parse_time(t_val: Any) -> datetime | None:
    if isinstance(t_val, datetime):
        return t_val
    if isinstance(t_val, str):
        try:
            return datetime.fromisoformat(t_val.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(t_val, int | float):
        return datetime.fromtimestamp(float(t_val))
    return None


def _parse_equity_curve(equity_curve: Any) -> list[tuple[datetime, float]]:
    """Helper to convert equity curve inputs to a sorted list of (datetime, equity_value) tuples."""
    if equity_curve is None:
        return []
    if hasattr(equity_curve, "to_dict"):
        # Pandas DataFrame
        records = equity_curve.to_dict("records")
    elif isinstance(equity_curve, list):
        records = equity_curve
    else:
        return []

    result = []
    for r in records:
        if isinstance(r, dict):
            t_val = r.get("timestamp") or r.get("time") or r.get("date")
            eq_val = r.get("equity") or r.get("balance") or r.get("value")
            t_dt = _parse_time(t_val)
            if t_dt and eq_val is not None:
                result.append((t_dt, float(eq_val)))
        elif isinstance(r, tuple | list) and len(r) >= 2:
            t_dt = _parse_time(r[0])
            if t_dt and r[1] is not None:
                result.append((t_dt, float(r[1])))
    # Sort chronologically
    result.sort(key=lambda x: x[0])
    return result


def _to_float_list(series: Any) -> list[float]:
    if series is None:
        return []
    if hasattr(series, "tolist"):
        return cast("list[float]", series.tolist())
    if isinstance(series, list):
        return [float(x) for x in series]
    return []


# --- Core Kernels ---


def total_return_usd(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return 0.0
    return parsed[-1][1] - parsed[0][1]


def total_return(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2 or parsed[0][1] <= 0:
        return 0.0
    return ((parsed[-1][1] - parsed[0][1]) / parsed[0][1]) * 100.0


def return_on_initial_capital(equity_curve: Any) -> float:
    return total_return(equity_curve)


def returns_series(equity_values: list[float]) -> list[float]:
    if len(equity_values) < 2:
        return []
    series = []
    for i in range(1, len(equity_values)):
        prev = equity_values[i - 1]
        if prev <= 0:
            series.append(0.0)
        else:
            series.append((equity_values[i] - prev) / prev)
    return series


def log_returns_series(equity_values: list[float]) -> list[float]:
    if len(equity_values) < 2:
        return []
    series = []
    for i in range(1, len(equity_values)):
        prev = equity_values[i - 1]
        curr = equity_values[i]
        if prev <= 0 or curr <= 0:
            series.append(0.0)
        else:
            series.append(math.log(curr / prev))
    return series


def _group_returns(equity_curve: Any, bucket: str = "daily") -> list[float]:
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return []
    # Group by bucket format
    grouped: dict[str, float] = {}
    for dt, eq in parsed:
        if bucket == "daily":
            key = dt.strftime("%Y-%m-%d")
        elif bucket == "weekly":
            key = dt.strftime("%Y-%W")
        elif bucket == "monthly":
            key = dt.strftime("%Y-%m")
        else:  # annual
            key = dt.strftime("%Y")
        grouped[key] = eq  # Keep last value in group

    sorted_vals = [eq for key, eq in sorted(grouped.items())]
    return returns_series(sorted_vals)


def daily_returns(equity_curve: Any) -> list[float]:
    return _group_returns(equity_curve, "daily")


def weekly_returns(equity_curve: Any) -> list[float]:
    return _group_returns(equity_curve, "weekly")


def monthly_returns(equity_curve: Any) -> list[float]:
    return _group_returns(equity_curve, "monthly")


def annual_returns(equity_curve: Any) -> list[float]:
    return _group_returns(equity_curve, "annual")


def benchmark_returns(price_values: list[float]) -> list[float]:
    return returns_series(price_values)


def relative_drawdown_series(
    strategy_equity: list[float], benchmark_equity: list[float]
) -> list[float]:
    n = min(len(strategy_equity), len(benchmark_equity))
    if n == 0:
        return []
    strat_ret = [0.0] + returns_series(strategy_equity)
    bench_ret = [0.0] + returns_series(benchmark_equity)
    cum_strat = 1.0
    cum_bench = 1.0
    rel_dd = []
    peak_diff = -999.0
    for i in range(n):
        cum_strat *= 1.0 + strat_ret[i]
        cum_bench *= 1.0 + bench_ret[i]
        diff = cum_strat - cum_bench
        peak_diff = max(peak_diff, diff)
        # Relative drawdown is peak difference minus current difference
        rel_dd.append(max(peak_diff - diff, 0.0))
    return rel_dd


def drawdown_series(equity_values: list[float]) -> list[float]:
    if not equity_values:
        return []
    peak = equity_values[0]
    series = []
    for eq in equity_values:
        peak = max(peak, eq)
        if peak <= 0:
            series.append(0.0)
        else:
            series.append((peak - eq) / peak)
    return series


def drawdown_duration_series(equity_curve: Any) -> list[float]:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return []
    durations = []
    peak = parsed[0][1]
    peak_time = parsed[0][0]
    for dt, eq in parsed:
        if eq >= peak:
            peak = eq
            peak_time = dt
            durations.append(0.0)
        else:
            duration = (dt - peak_time).total_seconds() / 3600.0  # in hours
            durations.append(duration)
    return durations


def max_drawdown_duration_from_equity(equity_curve: Any) -> float:
    durations = drawdown_duration_series(equity_curve)
    return max(durations, default=0.0)


def max_strategy_drawdown_date(equity_curve: Any) -> str:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return "1970-01-01T00:00:00Z"
    peak = parsed[0][1]
    max_dd = 0.0
    valley_time = parsed[0][0]
    for dt, eq in parsed:
        peak = max(peak, eq)
        if peak > 0:
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
                valley_time = dt
    return valley_time.isoformat()


def avg_underwater_drawdown_percent(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for dt, eq in parsed]
    dd_vals = drawdown_series(equities)
    underwater = [d for d in dd_vals if d > 0]
    if not underwater:
        return 0.0
    return sum(underwater) / len(underwater) * 100.0


def calculate_drawdown_metrics(equity_curve: Any) -> dict[str, Any]:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return {}
    equities = [eq for dt, eq in parsed]
    dd_vals = drawdown_series(equities)
    max_dd = max(dd_vals, default=0.0)
    durations = drawdown_duration_series(equity_curve)
    max_dur = max(durations, default=0.0)
    underwater = avg_underwater_drawdown_percent(equity_curve)
    return {
        "max_drawdown_percent": max_dd * 100.0,
        "max_drawdown_duration_hours": max_dur,
        "avg_underwater_drawdown_percent": underwater,
        "max_drawdown_date": max_strategy_drawdown_date(equity_curve),
    }


def compute_equity_metrics(returns: list[float]) -> dict[str, Any]:
    if not returns:
        return {"total_return": 0.0, "std": 0.0}
    # Simulate equity curve from returns
    eq = [10000.0]
    for r in returns:
        eq.append(eq[-1] * (1.0 + r))
    pct_ret = returns
    avg = sum(pct_ret) / len(pct_ret)
    var = sum((x - avg) ** 2 for x in pct_ret) / max(len(pct_ret) - 1, 1)
    return {
        "total_return": ((eq[-1] - eq[0]) / eq[0]) * 100.0,
        "return_volatility": math.sqrt(var) * 100.0,
    }


def calculate_return_metrics(equity_curve: Any) -> dict[str, Any]:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return {}
    equities = [eq for dt, eq in parsed]
    pct_returns = returns_series(equities)
    total_ret = total_return(equity_curve)
    avg_ret = sum(pct_returns) / len(pct_returns) if pct_returns else 0.0
    return {
        "total_return_percent": total_ret,
        "average_return_percent": avg_ret * 100.0,
        "total_return_usd": total_return_usd(equity_curve),
    }


# --- Official AI Tools ---


def calculate_equity_metrics(
    equity_curve: Any, request_id: str | None = None
) -> StandardResponse:
    """Calculate aggregate return and drawdown metrics from an equity curve."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="calculate_equity_metrics",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        parsed = _parse_equity_curve(equity_curve)
        if not parsed:
            raise ValidationError(
                "equity_curve must contain at least one valid data point."
            )
        ret_metrics = calculate_return_metrics(equity_curve)
        dd_metrics = calculate_drawdown_metrics(equity_curve)
        data = {
            "total_return_percent": ret_metrics.get("total_return_percent", 0.0),
            "total_return_usd": ret_metrics.get("total_return_usd", 0.0),
            "max_drawdown_percent": dd_metrics.get("max_drawdown_percent", 0.0),
            "max_drawdown_duration_hours": dd_metrics.get(
                "max_drawdown_duration_hours", 0.0
            ),
            "max_drawdown_date": dd_metrics.get(
                "max_drawdown_date", "1970-01-01T00:00:00Z"
            ),
        }
        return success_response(
            message="Successfully calculated equity metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)
