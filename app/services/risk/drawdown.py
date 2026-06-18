"""Drawdown Governor Engine.

Calculates total, daily, and strategy-level drawdowns, manages state transitions,
persists throttling states, and checks for revenge/catch-up risk behavior.
"""

from __future__ import annotations

import json
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    DrawdownState,
    PortfolioState,
    ProposedTrade,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)
from app.utils.logger import logger


class DrawdownThrottlingState(StrEnum):
    """Drawdown-based throttling categories."""

    NORMAL = "normal"
    CAUTION = "caution"
    DEFENSIVE = "defensive"
    RECOVERY_ONLY = "recovery_only"
    HALTED = "halted"


def calculate_daily_drawdown(
    portfolio_state: PortfolioState, daily_start_balance: Decimal
) -> Decimal:
    """Calculate daily drawdown percentage.

    Based on daily starting balance and current equity.

    Args:
        portfolio_state: Current portfolio state.
        daily_start_balance: Portfolio balance at the start of the day.

    Returns:
        Decimal daily drawdown percentage.
    """
    if daily_start_balance <= Decimal("0.0"):
        return Decimal("0.0")
    return max(
        Decimal("0.0"),
        (daily_start_balance - portfolio_state.equity) / daily_start_balance,
    )


def calculate_total_drawdown(
    portfolio_state: PortfolioState, peak_balance: Decimal
) -> Decimal:
    """Calculate total account drawdown percentage from lifetime peak balance.

    Args:
        portfolio_state: Current portfolio state.
        peak_balance: Historic maximum balance/equity peak.

    Returns:
        Decimal total drawdown percentage.
    """
    if peak_balance <= Decimal("0.0"):
        return Decimal("0.0")
    return max(Decimal("0.0"), (peak_balance - portfolio_state.equity) / peak_balance)


def calculate_strategy_drawdown(
    strategy_id: str,
    portfolio_state: PortfolioState,
    strategy_peak_equity: Decimal,
) -> Decimal:
    """Calculate drawdown for a specific strategy's allocated capital.

    Args:
        strategy_id: Identifier of the strategy.
        portfolio_state: Current portfolio state.
        strategy_peak_equity: Peak equity allocated or realized by this strategy.

    Returns:
        Decimal strategy drawdown percentage.
    """
    allocation = portfolio_state.strategy_allocations.get(strategy_id, Decimal("0.0"))
    strat_pnl = sum(
        pos.floating_pnl
        for pos in portfolio_state.positions
        if pos.strategy_id == strategy_id
    )
    current_strat_equity = allocation + strat_pnl

    if strategy_peak_equity <= Decimal("0.0"):
        return Decimal("0.0")
    return max(
        Decimal("0.0"),
        (strategy_peak_equity - current_strat_equity) / strategy_peak_equity,
    )


def determine_drawdown_throttling(
    drawdown: Decimal, soft_limit: Decimal, hard_limit: Decimal
) -> tuple[DrawdownThrottlingState, Decimal]:
    """Map a drawdown level to a throttling category and risk scale multiplier.

    Args:
        drawdown: Current drawdown percentage.
        soft_limit: Soft drawdown advisory threshold.
        hard_limit: Hard drawdown halt threshold.

    Returns:
        tuple containing (DrawdownThrottlingState, multiplier)
    """
    # 1. Halted state: drawdown meets or exceeds hard limit
    if drawdown >= hard_limit:
        return DrawdownThrottlingState.HALTED, Decimal("0.0")

    # 2. Recovery-only state: drawdown is close to hard limit (within 80%)
    if drawdown >= hard_limit * Decimal("0.8"):
        return DrawdownThrottlingState.RECOVERY_ONLY, Decimal("0.2")

    # 3. Defensive state: drawdown has breached soft limit
    if drawdown >= soft_limit:
        return DrawdownThrottlingState.DEFENSIVE, Decimal("0.5")

    # 4. Caution state: drawdown is elevated but below soft limit (within 50%)
    if drawdown >= soft_limit * Decimal("0.5"):
        return DrawdownThrottlingState.CAUTION, Decimal("0.8")

    # 5. Normal state
    return DrawdownThrottlingState.NORMAL, Decimal("1.0")


def persist_drawdown_state(state: DrawdownState, file_path: str | Path) -> None:
    """Serialize and write DrawdownState to a JSON file.

    Args:
        state: Active DrawdownState model.
        file_path: Output target path.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        # Pydantic JSON serialization helper
        f.write(state.to_json())


def restore_drawdown_state(file_path: str | Path) -> DrawdownState | None:
    """Restore and deserialize DrawdownState from a JSON file.

    Handles missing files and data corruption by returning None.

    Args:
        file_path: Input source path.

    Returns:
        DrawdownState or None if file does not exist or is corrupt.
    """
    path = Path(file_path)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        required_keys = {"current_drawdown", "soft_limit", "hard_limit", "multiplier"}
        if not required_keys.issubset(data.keys()):
            logger.warning(
                "Corrupt drawdown state file: missing keys "
                f"{required_keys - data.keys()}"
            )
            return None

        return DrawdownState(
            current_drawdown=Decimal(str(data["current_drawdown"])),
            soft_limit=Decimal(str(data["soft_limit"])),
            hard_limit=Decimal(str(data["hard_limit"])),
            multiplier=Decimal(str(data["multiplier"])),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to restore drawdown state from {file_path}: {e}")
        return None


def check_revenge_trading(
    proposed_trade: ProposedTrade | None,
    drawdown_state: DrawdownState,
    market_context: dict[str, Any],
) -> tuple[bool, str]:
    """Check if the proposed trade constitutes catch-up or revenge risk behavior.

    Rejects proposed trades with lot volumes exceeding scaled average baseline
    when the portfolio is in a drawdown throttling state (multiplier < 1.0).

    Args:
        proposed_trade: Candidate proposed trade.
        drawdown_state: Active DrawdownState.
        market_context: Context containing historical volume metadata.

    Returns:
        tuple (revenge_detected: bool, reason_message: str)
    """
    if proposed_trade is None:
        return False, ""

    if drawdown_state.multiplier >= Decimal("1.0"):
        return False, ""

    symbol = proposed_trade.symbol
    avg_vol_raw = market_context.get(
        f"{symbol}_historical_avg_volume"
    ) or market_context.get("historical_avg_volume")
    if avg_vol_raw is None:
        return False, ""

    avg_vol = Decimal(str(avg_vol_raw))
    max_allowed_vol = avg_vol * drawdown_state.multiplier

    if proposed_trade.volume > max_allowed_vol:
        msg = (
            f"Revenge trading detected: proposed volume {proposed_trade.volume} lots "
            f"exceeds maximum allowed drawdown-scaled volume of {max_allowed_vol} lots "
            f"(historical average: {avg_vol} lots, "
            f"multiplier: {drawdown_state.multiplier})."
        )
        return True, msg
    return False, ""


def verify_drawdown_limits(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Enforce total drawdown limits and check for revenge trading behavior.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        LimitResult showing drawdown approval status.
    """
    peak_balance_raw = market_context.get("peak_balance")
    if peak_balance_raw is None:
        peak_balance = portfolio_state.balance
    else:
        peak_balance = Decimal(str(peak_balance_raw))

    drawdown = calculate_total_drawdown(portfolio_state, peak_balance)
    soft_limit = config.max_total_loss_pct_advisory
    hard_limit = config.max_total_loss_pct

    # Determine state and scale-down multiplier
    throttling_state, multiplier = determine_drawdown_throttling(
        drawdown, soft_limit, hard_limit
    )

    state = DrawdownState(
        current_drawdown=drawdown,
        soft_limit=soft_limit,
        hard_limit=hard_limit,
        multiplier=multiplier,
    )

    # 1. Hard halt limit check
    if throttling_state == DrawdownThrottlingState.HALTED:
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.DRAWDOWN_BREACH,
            message=(
                f"Total drawdown halt threshold breached: {drawdown:.2%} >= "
                f"{hard_limit:.2%}."
            ),
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
            details=state.model_dump(),
        )

    # 2. Check for revenge/catch-up trade behavior
    is_revenge, revenge_msg = check_revenge_trading(
        proposed_trade, state, market_context
    )
    if is_revenge:
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.DRAWDOWN_BREACH,
            message=revenge_msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details=state.model_dump(),
        )

    # If in warning or scaled states, return advisory warnings
    if throttling_state in {
        DrawdownThrottlingState.CAUTION,
        DrawdownThrottlingState.DEFENSIVE,
        DrawdownThrottlingState.RECOVERY_ONLY,
    }:
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.REDUCE_SIZE,
            reason_code=RiskReasonCode.DRAWDOWN_BREACH,
            message=(
                f"Drawdown throttling active ({throttling_state.value}): "
                f"risk sizing multiplier of {multiplier} enforced."
            ),
            severity=RiskSeverity.SOFT_BREACH,
            breached=False,
            details=state.model_dump(),
        )

    return LimitResult(
        limit_name="max_drawdown_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Total drawdown is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
        details=state.model_dump(),
    )
