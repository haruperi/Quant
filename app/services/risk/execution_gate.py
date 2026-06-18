"""Execution Feasibility Gate Engine.

Validates spread, slippage, stop levels, freeze levels, lot size granularities,
market session states, and strategy trade frequencies.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    ExecutionRiskSnapshot,
    PortfolioState,
    ProposedTrade,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)


def check_spread_to_sigma(
    spread: Decimal,
    volatility: Decimal,
    multiplier: Decimal = Decimal("3.0"),
) -> bool:
    """Validate if current spread is wider than a rolling volatility threshold.

    Args:
        spread: Active bid/ask spread.
        volatility: Rolling price standard deviation/volatility.
        multiplier: Scaling factor.

    Returns:
        True if spread is feasible (within safe volatility boundaries).
    """
    if volatility <= Decimal("0.0"):
        return True
    return spread <= volatility * multiplier


def check_slippage_to_sigma(
    slippage: Decimal,
    volatility: Decimal,
    multiplier: Decimal = Decimal("2.0"),
) -> bool:
    """Validate if projected slippage threshold exceeds rolling volatility.

    Args:
        slippage: Intended slippage allowance.
        volatility: Price standard deviation.
        multiplier: Scaling factor.

    Returns:
        True if slippage is feasible.
    """
    if volatility <= Decimal("0.0"):
        return True
    return slippage <= volatility * multiplier


def check_stop_freeze_level(
    proposed_trade: ProposedTrade,
    stop_level: Decimal,
    freeze_level: Decimal,
    pip_size: Decimal,
) -> tuple[bool, str]:
    """Verify stop loss distance complies with broker minimum stop and freeze levels.

    Args:
        proposed_trade: Candidate proposed trade.
        stop_level: Minimum stop distance in pips/points.
        freeze_level: Minimum order modification freeze distance in pips/points.
        pip_size: Point/pip size coefficient.

    Returns:
        tuple (pass_status: bool, error_message: str)
    """
    symbol = proposed_trade.symbol
    price = proposed_trade.price
    sl = proposed_trade.stop_loss

    if sl is None or sl == Decimal("0.0"):
        return True, ""

    if price <= Decimal("0.0"):
        return True, ""

    distance = abs(price - sl)
    min_dist = stop_level * pip_size
    min_freeze = freeze_level * pip_size

    if distance < min_dist:
        return (
            False,
            f"Stop loss distance of {distance} for {symbol} is below broker "
            f"stop_level threshold of {min_dist} ({stop_level} pips).",
        )

    if distance < min_freeze:
        return (
            False,
            f"Stop loss distance of {distance} for {symbol} is inside broker "
            f"freeze_level threshold of {min_freeze} ({freeze_level} pips).",
        )

    return True, ""


def check_volume_feasibility(
    volume: Decimal,
    volume_min: Decimal,
    volume_max: Decimal,
    volume_step: Decimal,
) -> tuple[bool, str]:
    """Validate lot volume size against broker constraints and rounding granularity.

    Args:
        volume: Intended proposed lot volume.
        volume_min: Minimum allowed volume.
        volume_max: Maximum allowed volume.
        volume_step: Volume step granularity size.

    Returns:
        tuple (pass_status: bool, error_message: str)
    """
    if volume < volume_min:
        return (
            False,
            f"Volume {volume} is below broker minimum of {volume_min}.",
        )

    if volume > volume_max:
        return (
            False,
            f"Volume {volume} exceeds broker maximum of {volume_max}.",
        )

    # Granularity step check
    remainder = (volume - volume_min) % volume_step
    # Handle floating point inaccuracies safely by checking if remainder
    # is close to 0 or step
    tolerance = Decimal("1e-9")
    if remainder > tolerance and abs(remainder - volume_step) > tolerance:
        return (
            False,
            f"Volume {volume} does not align with broker lot step size "
            f"of {volume_step}.",
        )

    return True, ""


def check_trade_frequency(
    portfolio_state: PortfolioState,
    strategy_id: str,
    max_trades_per_min: int = 5,
    lookback_seconds: int = 60,
) -> tuple[bool, str]:
    """Limit the number of trades placed by a strategy to prevent runaway loops.

    Args:
        portfolio_state: Current portfolio state.
        strategy_id: strategy name filter.
        max_trades_per_min: Maximum number of executions allowed in lookback.
        lookback_seconds: Frequency duration window in seconds.

    Returns:
        tuple (pass_status: bool, error_message: str)
    """
    now = datetime.now(UTC)
    recent_count = 0

    for pos in portfolio_state.positions:
        if pos.strategy_id != strategy_id:
            continue
        # Convert open_time to offset-aware UTC if needed
        open_time = pos.open_time
        if open_time.tzinfo is None:
            open_time = open_time.replace(tzinfo=UTC)

        age = (now - open_time).total_seconds()
        if age <= lookback_seconds:
            recent_count += 1

    if recent_count >= max_trades_per_min:
        return (
            False,
            f"Trade frequency limit breached for '{strategy_id}': "
            f"{recent_count} trades placed in last {lookback_seconds}s "
            f"(limit: {max_trades_per_min}).",
        )

    return True, ""


def evaluate_execution_feasibility(
    _portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    _config: RiskConfig,
) -> ExecutionRiskSnapshot:
    """Evaluate all execution feasibility metrics and return a snapshot.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        ExecutionRiskSnapshot containing metrics.
    """
    if proposed_trade is None:
        return ExecutionRiskSnapshot(
            spread=Decimal("0.0"),
            slippage=Decimal("0.0"),
            stop_level=Decimal("0.0"),
            freeze_level=Decimal("0.0"),
            lot_step=Decimal("0.01"),
            marketability=True,
        )

    symbol = proposed_trade.symbol
    spread = Decimal(str(market_context.get(f"{symbol}_spread", "0.0002")))

    # Slippage allowance (default 3.0 pips)
    slippage_pips = Decimal(
        str(
            market_context.get(f"{symbol}_slippage_limit")
            or market_context.get("slippage_limit", "3.0")
        )
    )
    pip_size = Decimal(str(market_context.get(f"{symbol}_pip_size", "0.0001")))
    slippage = slippage_pips * pip_size

    stop_level = Decimal(str(market_context.get(f"{symbol}_stop_level", "0.0")))
    freeze_level = Decimal(str(market_context.get(f"{symbol}_freeze_level", "0.0")))
    lot_step = Decimal(str(market_context.get(f"{symbol}_volume_step", "0.01")))

    # Resolve market session states
    session_open = market_context.get(f"{symbol}_session_open", True)
    tradable = market_context.get(f"{symbol}_tradable", True)
    session = market_context.get("session", "OPEN")
    marketability = session != "CLOSED" and session_open and tradable

    return ExecutionRiskSnapshot(
        spread=spread,
        slippage=slippage,
        stop_level=stop_level,
        freeze_level=freeze_level,
        lot_step=lot_step,
        marketability=marketability,
    )


def verify_execution_limits(  # noqa: PLR0911
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Check pre-trade execution feasibility limits on a candidate trade.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Optional candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        LimitResult showing execution gate approval status.
    """
    if proposed_trade is None:
        return LimitResult(
            limit_name="spread_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No proposed trade to evaluate for execution feasibility.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    symbol = proposed_trade.symbol
    snapshot = evaluate_execution_feasibility(
        portfolio_state, proposed_trade, market_context, config
    )

    # 1. Marketability session check
    if not snapshot.marketability:
        return LimitResult(
            limit_name="spread_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SPREAD_BREACH,
            message=f"Execution gate rejected: {symbol} market is closed or suspended.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details=snapshot.model_dump(),
        )

    # 2. Spread-to-sigma check
    volatility = Decimal(str(market_context.get(f"{symbol}_volatility", "0.0")))
    # If volatility is provided, enforce spread/sigma ratio
    if volatility > Decimal("0.0"):
        spread_multiplier = Decimal(
            str(market_context.get("spread_sigma_multiplier", "3.0"))
        )
        if not check_spread_to_sigma(snapshot.spread, volatility, spread_multiplier):
            return LimitResult(
                limit_name="spread_limit",
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.SPREAD_BREACH,
                message=(
                    f"Spread {snapshot.spread} exceeds volatility limit of "
                    f"{volatility * spread_multiplier} ({spread_multiplier}x sigma)."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                details=snapshot.model_dump(),
            )

        # 3. Slippage-to-sigma check
        slippage_multiplier = Decimal(
            str(market_context.get("slippage_sigma_multiplier", "2.0"))
        )
        if not check_slippage_to_sigma(
            snapshot.slippage, volatility, slippage_multiplier
        ):
            return LimitResult(
                limit_name="slippage_limit",
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.SLIPPAGE_BREACH,
                message=(
                    f"Slippage allowance {snapshot.slippage} exceeds "
                    f"volatility threshold of "
                    f"{volatility * slippage_multiplier}."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                details=snapshot.model_dump(),
            )

    # 4. Stop and freeze level compliance
    pip_size = Decimal(str(market_context.get(f"{symbol}_pip_size", "0.0001")))
    stop_pass, stop_msg = check_stop_freeze_level(
        proposed_trade, snapshot.stop_level, snapshot.freeze_level, pip_size
    )
    if not stop_pass:
        return LimitResult(
            limit_name="slippage_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SLIPPAGE_BREACH,
            message=stop_msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details=snapshot.model_dump(),
        )

    # 5. Volume granularities
    volume_min = Decimal(str(market_context.get(f"{symbol}_volume_min", "0.01")))
    volume_max = Decimal(str(market_context.get(f"{symbol}_volume_max", "100.0")))
    vol_pass, vol_msg = check_volume_feasibility(
        proposed_trade.volume, volume_min, volume_max, snapshot.lot_step
    )
    if not vol_pass:
        return LimitResult(
            limit_name="slippage_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=vol_msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details=snapshot.model_dump(),
        )

    # 6. Trade frequency limit
    max_freq = int(market_context.get("max_trades_per_minute", 5))
    freq_pass, freq_msg = check_trade_frequency(
        portfolio_state, proposed_trade.strategy_id, max_freq
    )
    if not freq_pass:
        return LimitResult(
            limit_name="trade_frequency_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.FREQUENCY_BREACH,
            message=freq_msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details=snapshot.model_dump(),
        )

    return LimitResult(
        limit_name="spread_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Execution feasibility checks passed successfully.",
        severity=RiskSeverity.INFO,
        breached=False,
        details=snapshot.model_dump(),
    )
