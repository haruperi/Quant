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
from app.utils.errors import ValidationError
from app.utils.logger import logger


class RiskStepDownState(StrEnum):
    """Drawdown-based throttling categories/states."""

    NORMAL = "normal"
    CAUTION = "caution"
    DEFENSIVE = "defensive"
    RECOVERY_ONLY = "recovery_only"
    HALTED = "halted"


DrawdownThrottlingState = RiskStepDownState


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
    config: RiskConfig | None = None,
) -> tuple[bool, str]:
    """Check if the proposed trade constitutes catch-up or revenge risk behavior.

    Rejects proposed trades with lot volumes exceeding scaled average baseline
    when the portfolio is in a drawdown throttling state (multiplier < 1.0).

    Args:
        proposed_trade: Candidate proposed trade.
        drawdown_state: Active DrawdownState.
        market_context: Context containing historical volume metadata.
        config: Optional active risk config profile.

    Returns:
        tuple (revenge_detected: bool, reason_message: str)
    """
    if proposed_trade is None:
        return False, ""

    # Allow revenge/catch-up trade bypass under simulation policy
    # if explicitly configured
    is_simulation = (
        market_context.get("mode") == "simulation"
        or market_context.get("environment") == "simulation"
    )
    allow_revenge = market_context.get("allow_revenge_trading") is True or (
        config is not None
        and config.experimental_features.get("allow_revenge_trading") is True
    )
    if is_simulation and allow_revenge:
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


def _check_reset_approval(market_context: dict[str, Any]) -> LimitResult | None:
    """Check if drawdown reset is requested and operator token is valid."""
    is_reset = (
        market_context.get("reset_drawdown") is True
        or market_context.get("reset_drawdown_state") is True
    )
    if is_reset and not (
        market_context.get("approval_token_valid")
        or market_context.get("approval_token")
    ):
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.APPROVAL_REQUIRED,
            message="Drawdown reset requires operator approval token.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    return None


def _check_daily_loss(
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult | None:
    """Check if daily drawdown limit is reached."""
    daily_start_raw = market_context.get("daily_start_balance")
    if daily_start_raw is not None:
        daily_start_balance = Decimal(str(daily_start_raw))
        daily_dd = calculate_daily_drawdown(portfolio_state, daily_start_balance)
        if daily_dd >= config.max_daily_loss_pct:
            return LimitResult(
                limit_name="max_drawdown_limit",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
                message=(
                    f"Daily hard loss limit breached: {daily_dd:.2%} >= "
                    f"{config.max_daily_loss_pct:.2%}."
                ),
                severity=RiskSeverity.CRITICAL_BREACH,
                breached=True,
            )
    return None


def _check_strategy_loss(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult | None:
    """Check if strategy-level drawdown limit is reached."""
    if proposed_trade is None:
        return None

    strategy_id = proposed_trade.strategy_id
    strat_peak_raw = market_context.get(f"{strategy_id}_peak_equity")
    if strat_peak_raw is not None:
        strat_peak = Decimal(str(strat_peak_raw))
    else:
        strat_peak = portfolio_state.strategy_allocations.get(
            strategy_id, Decimal("0.0")
        )

    max_strat_loss = Decimal(
        str(
            market_context.get("max_strategy_loss_pct")
            or config.experimental_features.get("max_strategy_loss_pct")
            or "0.04"
        )
    )
    if strat_peak > 0:
        strat_dd = calculate_strategy_drawdown(strategy_id, portfolio_state, strat_peak)
        if strat_dd >= max_strat_loss:
            return LimitResult(
                limit_name="max_drawdown_limit",
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.DRAWDOWN_BREACH,
                message=(
                    f"Strategy loss limit breached for strategy '{strategy_id}': "
                    f"{strat_dd:.2%} >= {max_strat_loss:.2%}."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
            )
    return None


def apply_drawdown_throttle(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Implement drawdown-aware risk throttling before hard loss limits are hit.

    Applies risk step-down multipliers as drawdown increases, checks
    strategy-level limits, daily hard loss limits, revenge trading
    behaviors, and reset approval requirements.
    """
    # 1. Reset approval check
    result = _check_reset_approval(market_context)

    # 2. Daily hard loss limit check
    if result is None:
        result = _check_daily_loss(portfolio_state, market_context, config)

    # 3. Strategy-level loss limit check
    if result is None:
        result = _check_strategy_loss(
            portfolio_state, proposed_trade, market_context, config
        )

    # 4. Total Drawdown and Revenge Checks
    if result is None:
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

        # 4.1. Hard halt limit check
        if throttling_state == DrawdownThrottlingState.HALTED:
            result = LimitResult(
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
        else:
            # 4.2. Check for revenge/catch-up trade behavior
            is_revenge, revenge_msg = check_revenge_trading(
                proposed_trade, state, market_context, config
            )
            if is_revenge:
                result = LimitResult(
                    limit_name="max_drawdown_limit",
                    status=RiskDecisionStatus.REJECT,
                    reason_code=RiskReasonCode.DRAWDOWN_BREACH,
                    message=revenge_msg,
                    severity=RiskSeverity.HARD_BREACH,
                    breached=True,
                    details=state.model_dump(),
                )
            # If in warning or scaled states, return advisory warnings
            elif throttling_state in {
                DrawdownThrottlingState.CAUTION,
                DrawdownThrottlingState.DEFENSIVE,
                DrawdownThrottlingState.RECOVERY_ONLY,
            }:
                result = LimitResult(
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
            else:
                result = LimitResult(
                    limit_name="max_drawdown_limit",
                    status=RiskDecisionStatus.APPROVE,
                    reason_code=RiskReasonCode.OK,
                    message="Total drawdown is within safe limits.",
                    severity=RiskSeverity.INFO,
                    breached=False,
                    details=state.model_dump(),
                )

    return result


def verify_drawdown_limits(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Enforce total drawdown limits and check for revenge trading behavior.

    Delegates check sequence directly to apply_drawdown_throttle.
    """
    return apply_drawdown_throttle(
        portfolio_state, proposed_trade, market_context, config
    )


class DrawdownGovernor:
    """Orchestrator for managing portfolio and strategy drawdowns.

    Throttles risk based on step-down thresholds and multipliers.
    """

    def __init__(self, config: RiskConfig | None = None) -> None:
        """Initialize with optional active configuration profile.

        Args:
            config: Optional active risk config profile.
        """
        self.config = config

    def calculate_daily_drawdown(
        self, portfolio_state: PortfolioState, daily_start_balance: Decimal
    ) -> Decimal:
        """Calculate daily drawdown percentage."""
        return calculate_daily_drawdown(portfolio_state, daily_start_balance)

    def calculate_total_drawdown(
        self, portfolio_state: PortfolioState, peak_balance: Decimal
    ) -> Decimal:
        """Calculate total account drawdown percentage."""
        return calculate_total_drawdown(portfolio_state, peak_balance)

    def calculate_strategy_drawdown(
        self,
        strategy_id: str,
        portfolio_state: PortfolioState,
        strategy_peak_equity: Decimal,
    ) -> Decimal:
        """Calculate drawdown for a specific strategy's allocated capital."""
        return calculate_strategy_drawdown(
            strategy_id, portfolio_state, strategy_peak_equity
        )

    def determine_drawdown_throttling(
        self, drawdown: Decimal, soft_limit: Decimal, hard_limit: Decimal
    ) -> tuple[RiskStepDownState, Decimal]:
        """Map a drawdown level to a throttling category and multiplier."""
        return determine_drawdown_throttling(drawdown, soft_limit, hard_limit)

    def apply_drawdown_throttle(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig | None = None,
    ) -> LimitResult:
        """Implement drawdown-aware risk throttling before hard loss limits are hit."""
        active_config = config or self.config
        if active_config is None:
            raise ValidationError(
                "DrawdownGovernor requires a RiskConfig to apply throttling."
            )
        return apply_drawdown_throttle(
            portfolio_state, proposed_trade, market_context, active_config
        )

    def persist_state(self, state: DrawdownState, file_path: str | Path) -> None:
        """Serialize and write DrawdownState to a JSON file."""
        persist_drawdown_state(state, file_path)

    def restore_state(self, file_path: str | Path) -> DrawdownState | None:
        """Restore and deserialize DrawdownState from a JSON file."""
        return restore_drawdown_state(file_path)
