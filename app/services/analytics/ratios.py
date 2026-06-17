"""Ratio metrics calculations for Analytics.

Implements Sharpe, Sortino, Omega, Profit Factor, Edge, and other performance ratios.
"""

from __future__ import annotations

import math
from typing import Any, cast

from app.services.analytics.risk import downside_volatility
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


def sharpe_ratio(returns: list[float], risk_free_rate: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    mean_ret = sum(returns) / len(returns)
    excess = mean_ret - risk_free_rate
    # volatility stddev
    std_ret = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
    std_ret = math.sqrt(std_ret)
    if std_ret == 0:
        return 0.0
    return excess / std_ret


def annualized_sharpe_ratio(
    returns: list[float], risk_free_rate: float = 0.0, periods: int = 252
) -> float:
    # Sharpe ratio * sqrt(periods)
    sr = sharpe_ratio(returns, risk_free_rate / periods)
    return sr * math.sqrt(periods)


def sortino_ratio(
    returns: list[float], risk_free_rate: float = 0.0, target: float = 0.0
) -> float:
    if len(returns) < 2:
        return 0.0
    mean_ret = sum(returns) / len(returns)
    excess = mean_ret - risk_free_rate
    down_vol = downside_volatility(returns, target) / 100.0
    if down_vol == 0:
        return 0.0
    return excess / down_vol


def omega_ratio(returns: list[float], target: float = 0.0) -> float:
    gains = sum(max(r - target, 0.0) for r in returns)
    losses = sum(max(target - r, 0.0) for r in returns)
    if losses == 0:
        return 999.0 if gains > 0 else 0.0
    return gains / losses


def gain_to_pain_ratio(returns: list[float]) -> float:
    gains = sum(r for r in returns if r > 0)
    losses = sum(abs(r) for r in returns if r < 0)
    if losses == 0:
        return 999.0 if gains > 0 else 0.0
    return gains / losses


def kappa_ratio(returns: list[float], target: float = 0.0, order: int = 3) -> float:
    if not returns:
        return 0.0
    mean = sum(returns) / len(returns)
    lpm = sum(max(target - r, 0.0) ** order for r in returns) / len(returns)
    if lpm == 0:
        return 0.0
    return float((mean - target) / (lpm ** (1.0 / order)))


def profit_factor(trades: list[dict[str, Any]]) -> float:
    # reuse trade implementation but return float
    t_list = [float(t.get("profit_loss") or t.get("pnl") or 0.0) for t in trades]
    wins = sum(x for x in t_list if x > 0)
    losses = sum(abs(x) for x in t_list if x < 0)
    if losses == 0:
        return 999.0 if wins > 0 else 0.0
    return wins / losses


def payoff_ratio(trades: list[dict[str, Any]]) -> float:
    from app.services.analytics.trade import avg_win_loss

    return avg_win_loss(trades)


def edge_ratio(trades: list[dict[str, Any]]) -> float:
    # E = WinRate * WinLoss - LossRate
    from app.services.analytics.trade import win_rate_fraction

    w = win_rate_fraction(trades)
    r = payoff_ratio(trades)
    return w * r - (1.0 - w)


def profit_to_mae_ratio(trades: list[dict[str, Any]]) -> float:
    from app.services.analytics.risk import profit_per_pip_risk

    return profit_per_pip_risk(trades)


def mfe_to_mae_ratio(trades: list[dict[str, Any]]) -> float:
    total_mfe = sum(float(t.get("mfe") or 0.0) for t in trades)
    total_mae = sum(abs(float(t.get("mae") or 0.0)) for t in trades)
    if total_mae <= 0:
        return 0.0
    return total_mfe / total_mae


def expectancy_over_std(trades: list[dict[str, Any]]) -> float:
    # sqn is sqrt(N) * expectancy / std. Here we return expectancy / std
    from app.services.analytics.trade import _get_trade_pnl, get_closed_trades

    closed = get_closed_trades(trades)
    n = len(closed)
    if n == 0:
        return 0.0
    pnls = [_get_trade_pnl(t) for t in closed]
    mean = sum(pnls) / n
    if n < 2:
        return 0.0
    var = sum((x - mean) ** 2 for x in pnls) / (n - 1)
    if var == 0:
        return 0.0
    return mean / math.sqrt(var)


def net_profit_as_percent_of_largest_loss(
    net_profit: float, largest_loss: float
) -> float:
    if largest_loss == 0:
        return 0.0
    return (net_profit / abs(largest_loss)) * 100.0


def select_net_profit_as_percent_of_largest_loss(
    select_net_profit: float, largest_loss: float
) -> float:
    return net_profit_as_percent_of_largest_loss(select_net_profit, largest_loss)


def adjusted_net_profit_as_percent_of_largest_loss(
    adjusted_net_profit: float, largest_loss: float
) -> float:
    return net_profit_as_percent_of_largest_loss(adjusted_net_profit, largest_loss)


def adjusted_profit_factor(trades: list[dict[str, Any]]) -> float:
    from app.services.analytics.trade import adjusted_gross_loss, adjusted_gross_profit

    ag_p = adjusted_gross_profit(trades)
    ag_l = abs(adjusted_gross_loss(trades))
    if ag_l == 0:
        return 999.0 if ag_p > 0 else 0.0
    return ag_p / ag_l


def select_profit_factor(trades: list[dict[str, Any]]) -> float:
    from app.services.analytics.trade import select_gross_loss, select_gross_profit

    sg_p = select_gross_profit(trades)
    sg_l = abs(select_gross_loss(trades))
    if sg_l == 0:
        return 999.0 if sg_p > 0 else 0.0
    return sg_p / sg_l


def calculate_ratio_metrics(
    returns: Any, request_id: str | None = None
) -> StandardResponse:
    """Calculate aggregate ratio metrics from return values."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="calculate_ratio_metrics",
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
            "sharpe_ratio": sharpe_ratio(ret_list),
            "annualized_sharpe_ratio": annualized_sharpe_ratio(ret_list),
            "sortino_ratio": sortino_ratio(ret_list),
            "omega_ratio": omega_ratio(ret_list),
            "gain_to_pain_ratio": gain_to_pain_ratio(ret_list),
        }
        return success_response(
            message="Successfully calculated ratio metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)
