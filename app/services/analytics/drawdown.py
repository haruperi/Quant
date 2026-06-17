"""Drawdown metrics calculations for Analytics.

Implements all metrics, statistics, and indices based on drawdown series.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from app.services.analytics.equity import (
    _parse_equity_curve,
    drawdown_duration_series,
    drawdown_series,
)
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


# --- Core Kernels ---


def max_strategy_drawdown(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    peak = parsed[0][1]
    max_dd = 0.0
    for dt, eq in parsed:
        peak = max(peak, eq)
        max_dd = max(max_dd, peak - eq)
    return max_dd


def max_strategy_drawdown_percent(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    peak = parsed[0][1]
    max_dd = 0.0
    for dt, eq in parsed:
        peak = max(peak, eq)
        if peak > 0:
            max_dd = max(max_dd, (peak - eq) / peak)
    return max_dd * 100.0


def max_relative_drawdown_percent(
    strategy_equity: list[float], benchmark_equity: list[float]
) -> float:
    from app.services.analytics.equity import relative_drawdown_series

    rel_dd = relative_drawdown_series(strategy_equity, benchmark_equity)
    return max(rel_dd, default=0.0) * 100.0


def max_drawdown(returns: list[float]) -> float:
    if not returns:
        return 0.0
    eq = [10000.0]
    for r in returns:
        eq.append(eq[-1] * (1.0 + r))
    dds = drawdown_series(eq)
    return max(dds, default=0.0) * 100.0


def avg_drawdown(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for dt, eq in parsed]
    dds = drawdown_series(equities)
    active_dds = [d for d in dds if d > 0]
    if not active_dds:
        return 0.0
    return (sum(active_dds) / len(active_dds)) * 100.0


def drawdown_distribution(equity_curve: Any) -> dict[str, float]:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return {}
    equities = [eq for dt, eq in parsed]
    dds = [d * 100.0 for d in drawdown_series(equities)]
    if not dds:
        return {}
    sorted_dds = sorted(dds)
    n = len(sorted_dds)
    return {
        "mean": sum(dds) / n,
        "std": math.sqrt(sum((x - (sum(dds) / n)) ** 2 for x in dds) / max(n - 1, 1)),
        "50th": sorted_dds[int(n * 0.50)],
        "90th": sorted_dds[int(n * 0.90)],
        "95th": sorted_dds[int(n * 0.95)],
        "99th": sorted_dds[int(n * 0.99)],
    }


def max_drawdown_duration_from_returns(returns: list[float]) -> float:
    if not returns:
        return 0.0
    eq = [10000.0]
    for r in returns:
        eq.append(eq[-1] * (1.0 + r))
    # construct artificial hourly times
    eq_curve = [(datetime.fromtimestamp(i * 3600, UTC), eq[i]) for i in range(len(eq))]
    return max(drawdown_duration_series(eq_curve), default=0.0)


def max_drawdown_duration(equity_curve: Any) -> float:
    durations = drawdown_duration_series(equity_curve)
    return max(durations, default=0.0)


def avg_drawdown_duration(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return 0.0
    durations = drawdown_duration_series(equity_curve)
    active_durs = [d for d in durations if d > 0]
    if not active_durs:
        return 0.0
    # Average length of drawdown episodes
    # Find contiguous non-zero periods
    episodes = []
    curr = 0.0
    for d in active_durs:
        curr = max(curr, d)
        if d == 0.0:
            if curr > 0.0:
                episodes.append(curr)
            curr = 0.0
    if curr > 0.0:
        episodes.append(curr)
    return sum(episodes) / len(episodes) if episodes else 0.0


def time_to_recovery(equity_curve: Any) -> list[float]:
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        return []
    recovery_times = []
    peak = parsed[0][1]
    peak_time = parsed[0][0]
    in_drawdown = False
    for dt, eq in parsed[1:]:
        if eq >= peak:
            if in_drawdown:
                recovery_time = (dt - peak_time).total_seconds() / 3600.0  # hours
                recovery_times.append(recovery_time)
                in_drawdown = False
            peak = eq
            peak_time = dt
        else:
            in_drawdown = True
    return recovery_times


def recovery_factor(net_profit: float, max_drawdown_val: float) -> float:
    if max_drawdown_val <= 0:
        return 0.0
    return net_profit / max_drawdown_val


def max_close_to_close_drawdown_percent(
    trades: list[dict[str, Any]], initial_balance: float = 10000.0
) -> float:
    from app.services.analytics.trade import balance_curve

    curve = balance_curve(trades, initial_balance)
    equities = [c["equity"] for c in curve]
    dds = drawdown_series(equities)
    return max(dds, default=0.0) * 100.0


def account_size_required(
    trades: list[dict[str, Any]], initial_balance: float = 10000.0
) -> float:
    from app.services.analytics.trade import balance_curve

    max_dd_usd = max_strategy_drawdown(balance_curve(trades, initial_balance))
    # Required size is initial_balance + maximum decline to ensure no margin calls
    return initial_balance + max_dd_usd


def avg_yearly_max_drawdown(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    by_year: dict[int, list[tuple[datetime, float]]] = {}
    for dt, eq in parsed:
        by_year.setdefault(dt.year, []).append((dt, eq))

    yearly_dds = []
    for y, curve in by_year.items():
        yearly_dds.append(max_strategy_drawdown_percent(curve))
    return sum(yearly_dds) / len(yearly_dds) if yearly_dds else 0.0


def ulcer_index(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for dt, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return 0.0
    mean_sq = sum(d**2 for d in dds) / len(dds)
    return math.sqrt(mean_sq) * 100.0


def pain_index(equity_curve: Any) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for dt, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return 0.0
    return (sum(dds) / len(dds)) * 100.0


def pain_ratio(annualized_return: float, pain_idx: float) -> float:
    if pain_idx <= 0:
        return 0.0
    return annualized_return / pain_idx


def calmar_ratio(annualized_return: float, max_dd: float) -> float:
    if max_dd <= 0:
        return 0.0
    return annualized_return / max_dd


def fouse_ratio(annualized_return: float, ulcer_idx: float) -> float:
    if ulcer_idx <= 0:
        return 0.0
    return annualized_return / ulcer_idx


def sterling_ratio(cagr: float, avg_yearly_max_dd: float) -> float:
    # CAGR / (AvgYearlyMaxDD + 10%)
    denom = abs(avg_yearly_max_dd) + 10.0
    if denom <= 0:
        return 0.0
    return cagr / denom


def rina_index(select_net_prof: float, avg_dd: float, time_in_market: float) -> float:
    # select_net_profit / (avg_drawdown * time_in_market)
    denom = avg_dd * time_in_market
    if denom <= 0:
        return 0.0
    return select_net_prof / denom


def net_profit_as_percent_of_max_strategy_drawdown(
    net_prof: float, max_dd_usd: float
) -> float:
    if max_dd_usd <= 0:
        return 0.0
    return (net_prof / max_dd_usd) * 100.0


def select_net_profit_as_percent_of_max_strategy_drawdown(
    select_net_prof: float, max_dd_usd: float
) -> float:
    return net_profit_as_percent_of_max_strategy_drawdown(select_net_prof, max_dd_usd)


def adjusted_net_profit_as_percent_of_max_strategy_drawdown(
    adj_net_prof: float, max_dd_usd: float
) -> float:
    return net_profit_as_percent_of_max_strategy_drawdown(adj_net_prof, max_dd_usd)


def return_on_max_strategy_drawdown(total_ret: float, max_dd_pct: float) -> float:
    if max_dd_pct <= 0:
        return 0.0
    return total_ret / max_dd_pct


def return_on_max_close_to_close_drawdown(
    net_prof: float, max_close_dd_usd: float
) -> float:
    if max_close_dd_usd <= 0:
        return 0.0
    return net_prof / max_close_dd_usd


def drawdown_probability(equity_curve: Any, threshold: float) -> float:
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return 0.0
    equities = [eq for dt, eq in parsed]
    dds = [d * 100.0 for d in drawdown_series(equities)]
    if not dds:
        return 0.0
    over_threshold = sum(1 for d in dds if d >= threshold)
    return over_threshold / len(dds)


# --- Official AI Tools ---


def calculate_drawdown_metrics(
    equity_curve: Any, request_id: str | None = None
) -> StandardResponse:
    """Calculate aggregate drawdown metrics from an equity curve."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="calculate_drawdown_metrics",
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
        equities = [eq for dt, eq in parsed]
        dds = drawdown_series(equities)
        max_dd = max(dds, default=0.0) * 100.0
        durations = drawdown_duration_series(equity_curve)
        max_dur = max(durations, default=0.0)
        underwater = avg_underwater_drawdown_percent = avg_drawdown(equity_curve)

        data = {
            "max_drawdown_percent": max_dd,
            "max_drawdown_duration_hours": max_dur,
            "avg_drawdown_percent": underwater,
            "ulcer_index": ulcer_index(equity_curve),
            "pain_index": pain_index(equity_curve),
        }
        return success_response(
            message="Successfully calculated drawdown metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)
