"""Efficiency metrics calculations for Analytics.

Implements exit efficiency, capital efficiency, and return per adverse excursion.
"""

from __future__ import annotations

from typing import Any

from app.services.analytics.trade import (
    _get_trade_pnl,
    classify_trades,
    get_closed_trades,
)


def capital_efficiency(net_profit: float, nominal_capital_deployed: float) -> float:
    if nominal_capital_deployed <= 0:
        return 0.0
    return net_profit / nominal_capital_deployed


def return_per_unit_mae(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    net_prof = sum(_get_trade_pnl(t) for t in closed)
    total_mae = sum(abs(float(t.get("mae") or 0.0)) for t in closed)
    if total_mae <= 0:
        return 0.0
    return net_prof / total_mae


def return_per_calendar_day(net_profit: float, duration_days: float) -> float:
    if duration_days <= 0:
        return 0.0
    return net_profit / duration_days


def loss_containment_efficiency(trades: list[dict[str, Any]]) -> float:
    losses = classify_trades(trades)["losses"]
    if not losses:
        return 1.0
    efficiencies = []
    for t in losses:
        mae = abs(float(t.get("mae") or 0.0))
        pnl = abs(_get_trade_pnl(t))
        if mae > 0:
            # How much loss was contained relative to maximum adverse excursion
            # 1.0 means pnl = 0 (perfect containment), 0.0 means pnl = mae (no containment/stopped at worst point)
            eff = (mae - pnl) / mae
            efficiencies.append(max(min(eff, 1.0), 0.0))
    return sum(efficiencies) / len(efficiencies) if efficiencies else 1.0


def exit_efficiency(trades: list[dict[str, Any]]) -> float:
    # Exit efficiency: average of winning capture and losing containment
    from app.services.analytics.trade import mfe_efficiency

    win_eff = mfe_efficiency(trades)
    loss_eff = loss_containment_efficiency(trades)
    return (win_eff + loss_eff) / 2.0
