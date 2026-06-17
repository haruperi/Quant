"""Risk metrics calculations for Analytics.

Implements volatility, VaR, CVaR, ruin probabilities, and nominal exposure metrics.
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


def _to_float_list(series: Any) -> list[float]:
    if series is None:
        return []
    if hasattr(series, "tolist"):
        return cast("list[float]", series.tolist())
    if isinstance(series, list):
        return [float(x) for x in series]
    return []


# --- Core Kernels ---


def risk_adjusted_efficiency(net_profit: float, total_risk: float) -> float:
    if total_risk <= 0:
        return 0.0
    return net_profit / total_risk


def profit_per_pip_risk(trades: list[dict[str, Any]]) -> float:
    # reward-to-risk based on profit relative to adverse excursion
    total_prof = sum(float(t.get("profit_loss") or t.get("pnl") or 0.0) for t in trades)
    total_mae = sum(abs(float(t.get("mae") or 0.0)) for t in trades)
    if total_mae <= 0:
        return 0.0
    return total_prof / total_mae


def volatility(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(var) * 100.0


def annualized_volatility(returns: list[float], periods: int = 252) -> float:
    return volatility(returns) * math.sqrt(periods)


def downside_volatility(returns: list[float], target: float = 0.0) -> float:
    downside = [r - target for r in returns if r < target]
    if len(downside) < 2:
        return 0.0
    # standard downside deviation divides by N or N-1
    var = sum(d**2 for d in downside) / (len(returns) - 1)
    return math.sqrt(var) * 100.0


def upside_potential_ratio(returns: list[float], target: float = 0.0) -> float:
    upside = [max(r - target, 0.0) for r in returns]
    if not upside:
        return 0.0
    avg_upside = sum(upside) / len(returns)
    down_vol = downside_volatility(returns, target) / 100.0
    if down_vol <= 0:
        return 0.0
    return avg_upside / down_vol


def value_at_risk(returns: list[float], confidence: float = 0.95) -> float:
    if not returns:
        return 0.0
    sorted_ret = sorted(returns)
    alpha_val = 1.0 - confidence
    idx = int(len(sorted_ret) * alpha_val)
    # Return as a positive percentage of loss
    return abs(sorted_ret[idx]) * 100.0 if idx < len(sorted_ret) else 0.0


def conditional_var(returns: list[float], confidence: float = 0.95) -> float:
    if not returns:
        return 0.0
    sorted_ret = sorted(returns)
    alpha_val = 1.0 - confidence
    idx = int(len(sorted_ret) * alpha_val)
    tail = sorted_ret[:idx] if idx > 0 else sorted_ret[:1]
    # Return as a positive percentage of loss
    return (sum(abs(r) for r in tail) / len(tail)) * 100.0


def expected_shortfall(returns: list[float], confidence: float = 0.95) -> float:
    return conditional_var(returns, confidence)


def max_nominal_exposure_simple(trades: list[dict[str, Any]]) -> float:
    # simply use max exposure
    exposures = []
    for t in trades:
        size = float(t.get("size") or t.get("volume") or 0.0)
        price = float(t.get("open_price") or t.get("entry_price") or 1.0)
        exposures.append(size * price)
    return max(exposures, default=0.0)


def max_gross_exposure(trades: list[dict[str, Any]]) -> float:
    return max_nominal_exposure_simple(trades)


def exposure_time_ratio(
    trades: list[dict[str, Any]], period_duration_hours: float
) -> float:
    from app.services.analytics.trade import percent_time_in_market

    return percent_time_in_market(trades, period_duration_hours)


def time_weighted_avg_exposure(
    trades: list[dict[str, Any]], period_duration_hours: float
) -> float:
    from app.services.analytics.trade import (
        _get_trade_duration,
        get_ordered_closed_trades,
    )

    closed = get_ordered_closed_trades(trades)
    if not closed or period_duration_hours <= 0:
        return 0.0
    tot_exp_time = 0.0
    for t in closed:
        size = float(t.get("size") or t.get("volume") or 0.0)
        price = float(t.get("open_price") or t.get("entry_price") or 1.0)
        dur = _get_trade_duration(t)
        tot_exp_time += (size * price) * dur
    return tot_exp_time / period_duration_hours


def portfolio_margin_utilization_curve(
    portfolio_state_logs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    curve = []
    for state in portfolio_state_logs:
        eq = float(state.get("equity") or 0.0)
        margin = float(state.get("margin_used") or 0.0)
        util = margin / eq if eq > 0 else 0.0
        t_val = state.get("timestamp") or state.get("time") or "1970-01-01T00:00:00Z"
        ts = (
            t_val
            if isinstance(t_val, str)
            else datetime.fromtimestamp(float(t_val)).isoformat()
        )
        curve.append({"timestamp": ts, "margin_utilization": util})
    return curve


def compounding_risk_of_ruin(
    trades: list[dict[str, Any]], initial_balance: float, ruin_threshold: float
) -> float:
    from app.services.analytics.trade import risk_of_ruin

    # wrapper utilizing risk_of_ruin
    return risk_of_ruin(trades, initial_balance, ruin_threshold, iterations=1000)


def historical_var_by_symbol(
    trades_by_symbol: dict[str, list[dict[str, Any]]],
) -> dict[str, float]:
    result = {}
    for sym, trades in trades_by_symbol.items():
        pnls = [float(t.get("profit_loss") or t.get("pnl") or 0.0) for t in trades]
        if not pnls:
            result[sym] = 0.0
            continue
        sorted_pnls = sorted(pnls)
        idx = int(len(sorted_pnls) * 0.05)
        result[sym] = abs(sorted_pnls[idx]) if idx < len(sorted_pnls) else 0.0
    return result


def portfolio_var_from_covariance(
    weights: list[float], covariance: list[list[float]]
) -> float:
    # weights: w, covariance: cov
    # var = w^T * cov * w
    n = len(weights)
    if n == 0 or len(covariance) != n:
        return 0.0
    res = 0.0
    for i in range(n):
        for j in range(n):
            res += weights[i] * covariance[i][j] * weights[j]
    return math.sqrt(res) if res > 0 else 0.0


def calculate_risk_metrics(
    returns: Any, request_id: str | None = None
) -> StandardResponse:
    """Calculate aggregate risk metrics such as VaR, CVaR, and volatility."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="calculate_risk_metrics",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        ret_list = _to_float_list(returns)
        if not ret_list:
            raise ValidationError(
                "returns series must contain at least one valid number."
            )

        data = {
            "volatility": volatility(ret_list),
            "annualized_volatility": annualized_volatility(ret_list),
            "downside_volatility": downside_volatility(ret_list),
            "value_at_risk_95": value_at_risk(ret_list, 0.95),
            "conditional_var_95": conditional_var(ret_list, 0.95),
        }
        return success_response(
            message="Successfully calculated risk metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)
