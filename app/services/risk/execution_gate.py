"""Execution Feasibility Gate Engine.

Validates spread, slippage, stop levels, freeze levels, lot size granularities,
market session states, and strategy trade frequencies.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from pydantic import Field

from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    ExecutionRiskSnapshot,
    PortfolioState,
    ProposedTrade,
    RiskConfig,
    RiskContract,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)


class SlippagePolicy(RiskContract):
    """Configuration/limits for execution slippage."""

    max_slippage: Decimal | None = Field(
        default=None, description="Absolute maximum allowed slippage."
    )
    slippage_sigma_multiplier: Decimal = Field(
        default=Decimal("2.0"), description="Multiplier for rolling volatility check."
    )


class SpreadPolicy(RiskContract):
    """Configuration/limits for bid/ask spread."""

    max_spread: Decimal | None = Field(
        default=None, description="Absolute maximum allowed spread."
    )
    spread_sigma_multiplier: Decimal = Field(
        default=Decimal("3.0"), description="Multiplier for rolling volatility check."
    )
    m1_spread_to_sigma_ratio_filter: Decimal = Field(
        default=Decimal("1.5"), description="Strict multiplier for M1 timeframe."
    )


class BrokerConstraintSnapshot(RiskContract):
    """Snapshot of active broker constraints for a symbol."""

    symbol: str = Field(..., description="Symbol for constraints.")
    stop_level: Decimal = Field(
        default=Decimal("0.0"), description="Minimum stop distance in points/pips."
    )
    freeze_level: Decimal = Field(
        default=Decimal("0.0"),
        description="Minimum order modification freeze distance in points/pips.",
    )
    volume_min: Decimal = Field(
        default=Decimal("0.01"), description="Minimum allowed trade size in lots."
    )
    volume_max: Decimal = Field(
        default=Decimal("100.0"), description="Maximum allowed trade size in lots."
    )
    volume_step: Decimal = Field(
        default=Decimal("0.01"), description="Lot step size increment."
    )
    filling_mode: str | None = Field(
        default=None, description="Allowed execution filling mode (e.g. FOK, IOC)."
    )
    session_open: bool = Field(
        default=True, description="True if symbol session is currently open."
    )
    tradable: bool = Field(
        default=True, description="True if symbol is tradable at the broker."
    )
    pip_size: Decimal = Field(
        default=Decimal("0.0001"), description="Point/pip size coefficient."
    )
    freshness: datetime | None = Field(
        default=None, description="Metadata quote freshness timestamp."
    )


class ExecutionFeasibilityResult(RiskContract):
    """Result details of execution feasibility evaluations."""

    status: RiskDecisionStatus = Field(
        ..., description="Decision outcome status for this limit."
    )
    reason_code: RiskReasonCode = Field(
        ..., description="Reason code associated with any breach."
    )
    message: str = Field(..., description="Human-readable detail message.")
    severity: RiskSeverity = Field(..., description="Severity level of any violation.")
    breached: bool = Field(..., description="True if a breach was triggered.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Calculated values or context info."
    )
    reduced_volume: Decimal | None = Field(
        default=None,
        description="Recommended safe size if volume was the only breach.",
    )


def check_spread_limit(
    spread: Decimal,
    volatility: Decimal,
    policy: SpreadPolicy,
    is_m1: bool = False,
) -> tuple[bool, str]:
    """Validate if current spread is within policy limits.

    Args:
        spread: Active bid/ask spread.
        volatility: Price standard deviation.
        policy: The spread policy to enforce.
        is_m1: True if timeframe is M1.

    Returns:
        tuple (pass_status: bool, error_message: str)
    """
    if policy.max_spread is not None and spread > policy.max_spread:
        msg = (
            f"Spread {spread} exceeds absolute max spread limit of {policy.max_spread}."
        )
        return False, msg

    if volatility > Decimal("0.0"):
        multiplier = (
            policy.m1_spread_to_sigma_ratio_filter
            if is_m1
            else policy.spread_sigma_multiplier
        )
        limit = volatility * multiplier
        if spread > limit:
            msg = (
                f"Spread {spread} exceeds volatility limit of {limit} "
                f"({multiplier}x sigma)."
            )
            return False, msg

    return True, ""


def check_slippage_limit(
    slippage: Decimal,
    volatility: Decimal,
    policy: SlippagePolicy,
) -> tuple[bool, str]:
    """Validate if projected slippage exceeds rolling volatility limits.

    Args:
        slippage: Intended slippage allowance.
        volatility: Price standard deviation.
        policy: The slippage policy to enforce.

    Returns:
        tuple (pass_status: bool, error_message: str)
    """
    if policy.max_slippage is not None and slippage > policy.max_slippage:
        msg = (
            f"Slippage {slippage} exceeds absolute max slippage limit of "
            f"{policy.max_slippage}."
        )
        return False, msg

    if volatility > Decimal("0.0"):
        limit = volatility * policy.slippage_sigma_multiplier
        if slippage > limit:
            msg = (
                f"Slippage allowance {slippage} exceeds volatility threshold of "
                f"{limit} ({policy.slippage_sigma_multiplier}x sigma)."
            )
            return False, msg

    return True, ""


def check_stop_distance_validity(
    proposed_trade: ProposedTrade,
    stop_level: Decimal,
    freeze_level: Decimal,
    pip_size: Decimal,
) -> tuple[bool, str]:
    """Verify stop loss distance complies with broker minimum stop and freeze levels.

    Also checks target/stop loss representability under point/pip size increments.

    Args:
        proposed_trade: Candidate proposed trade.
        stop_level: Minimum stop distance in points/pips.
        freeze_level: Minimum order modification freeze distance in points/pips.
        pip_size: Point/pip size coefficient.

    Returns:
        tuple (pass_status: bool, error_message: str)
    """
    price = proposed_trade.price
    sl = (
        proposed_trade.intended_stop
        if proposed_trade.intended_stop is not None
        else proposed_trade.stop_loss
    )
    tp = proposed_trade.intended_target

    if price <= Decimal("0.0"):
        return True, ""

    tolerance = Decimal("1e-9")

    # Stop Loss checks
    if sl is not None and sl != Decimal("0.0"):
        remainder_sl = sl % pip_size
        if remainder_sl > tolerance and abs(remainder_sl - pip_size) > tolerance:
            msg = (
                f"Stop loss price {sl} cannot be represented under broker "
                f"point size of {pip_size}."
            )
            return False, msg

        distance = abs(price - sl)
        min_dist = stop_level * pip_size
        min_freeze = freeze_level * pip_size

        if distance < min_dist:
            msg = (
                f"Stop loss distance of {distance} for {proposed_trade.symbol} "
                f"is below broker stop_level threshold of {min_dist} "
                f"({stop_level} pips)."
            )
            return False, msg

        if distance < min_freeze:
            msg = (
                f"Stop loss distance of {distance} for {proposed_trade.symbol} "
                f"is inside broker freeze_level threshold of {min_freeze} "
                f"({freeze_level} pips)."
            )
            return False, msg

    # Take Profit checks
    if tp is not None and tp != Decimal("0.0"):
        remainder_tp = tp % pip_size
        if remainder_tp > tolerance and abs(remainder_tp - pip_size) > tolerance:
            msg = (
                f"Target price {tp} cannot be represented under broker "
                f"point size of {pip_size}."
            )
            return False, msg

    return True, ""


def check_lot_step_validity(
    volume: Decimal,
    volume_min: Decimal,
    volume_max: Decimal,
    volume_step: Decimal,
) -> tuple[bool, str, Decimal | None]:
    """Validate lot volume size against broker constraints and rounding granularity.

    Args:
        volume: Intended proposed lot volume.
        volume_min: Minimum allowed volume.
        volume_max: Maximum allowed volume.
        volume_step: Volume step granularity size.

    Returns:
        tuple (pass_status: bool, error_message: str, reduced_volume: Decimal | None)
    """
    if volume < volume_min:
        return (
            False,
            f"Volume {volume} is below broker minimum of {volume_min}.",
            None,
        )

    if volume > volume_max:
        if volume_max >= volume_min:
            return (
                False,
                f"Volume {volume} exceeds broker maximum of {volume_max}.",
                volume_max,
            )
        return (
            False,
            f"Volume {volume} exceeds broker maximum of {volume_max}.",
            None,
        )

    # Granularity step check
    remainder = (volume - volume_min) % volume_step
    tolerance = Decimal("1e-9")
    if remainder > tolerance and abs(remainder - volume_step) > tolerance:
        reduced = volume - remainder
        if volume_min <= reduced <= volume_max:
            msg = (
                f"Volume {volume} does not align with broker lot step size "
                f"of {volume_step}."
            )
            return False, msg, reduced
        msg = (
            f"Volume {volume} does not align with broker lot step size "
            f"of {volume_step}."
        )
        return False, msg, None

    return True, "", None


def check_trade_frequency_limit(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade,
    market_context: dict[str, Any],
) -> tuple[bool, str]:
    """Verify trade frequency limits across symbol, strategy, account, and portfolio.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Candidate proposed trade.
        market_context: Market details.

    Returns:
        tuple (pass_status: bool, error_message: str)
    """
    lookback = int(market_context.get("trade_frequency_lookback_seconds", 60))
    now = datetime.now(UTC)

    limit_symbol = market_context.get("max_trades_per_min_symbol")
    limit_strategy = market_context.get("max_trades_per_min_strategy")
    limit_account = market_context.get("max_trades_per_min_account")
    limit_portfolio = market_context.get("max_trades_per_min_portfolio")

    symbol_count = 0
    strategy_count = 0
    total_count = 0

    for pos in portfolio_state.positions:
        open_time = pos.open_time
        if open_time.tzinfo is None:
            open_time = open_time.replace(tzinfo=UTC)

        age = (now - open_time).total_seconds()
        if age <= lookback:
            total_count += 1
            if pos.symbol == proposed_trade.symbol:
                symbol_count += 1
            if pos.strategy_id == proposed_trade.strategy_id:
                strategy_count += 1

    if limit_symbol is not None and symbol_count >= int(limit_symbol):
        return (
            False,
            f"Trade frequency limit breached for symbol '{proposed_trade.symbol}': "
            f"{symbol_count} trades in last {lookback}s (limit: {limit_symbol}).",
        )

    if limit_strategy is not None and strategy_count >= int(limit_strategy):
        msg = (
            f"Trade frequency limit breached for strategy "
            f"'{proposed_trade.strategy_id}': {strategy_count} trades in "
            f"last {lookback}s (limit: {limit_strategy})."
        )
        return False, msg

    if limit_account is not None and total_count >= int(limit_account):
        return (
            False,
            f"Trade frequency limit breached for account: "
            f"{total_count} trades in last {lookback}s (limit: {limit_account}).",
        )

    if limit_portfolio is not None and total_count >= int(limit_portfolio):
        return (
            False,
            f"Trade frequency limit breached for portfolio: "
            f"{total_count} trades in last {lookback}s (limit: {limit_portfolio}).",
        )

    return True, ""


def check_holding_time_limit(
    proposed_trade: ProposedTrade,
    market_context: dict[str, Any],
) -> tuple[bool, str]:
    """Validate expected holding period against policy limits.

    Args:
        proposed_trade: Proposed candidate trade.
        market_context: Market details.

    Returns:
        tuple (pass_status: bool, error_message: str)
    """
    expected = proposed_trade.expected_holding_period
    if expected is None or expected <= 0:
        return True, ""

    max_duration = market_context.get(
        f"{proposed_trade.symbol}_max_holding_time"
    ) or market_context.get("max_holding_time")
    if max_duration is not None:
        max_duration_s = float(max_duration)
        if expected > max_duration_s:
            msg = (
                f"Expected holding duration of {expected}s exceeds maximum "
                f"allowed duration of {max_duration_s}s."
            )
            return False, msg

    return True, ""


def _resolve_metadata_and_defaults(
    symbol: str, market_context: dict[str, Any], is_live: bool
) -> tuple[
    Decimal | None,
    Decimal | None,
    Decimal | None,
    Decimal | None,
    Decimal | None,
    Decimal | None,
    ExecutionFeasibilityResult | None,
]:
    keys = [
        "stop_level",
        "freeze_level",
        "volume_min",
        "volume_max",
        "volume_step",
        "pip_size",
    ]
    raw_vals = {}
    for k in keys:
        raw_vals[k] = market_context.get(f"{symbol}_{k}") or market_context.get(k)

    if not is_live:
        defaults = {
            "stop_level": Decimal("0.0"),
            "freeze_level": Decimal("0.0"),
            "volume_min": Decimal("0.01"),
            "volume_max": Decimal("100.0"),
            "volume_step": Decimal("0.01"),
            "pip_size": Decimal("0.0001"),
        }
        for k, default_val in defaults.items():
            if raw_vals[k] is None:
                raw_vals[k] = default_val

    missing = [k for k in keys if raw_vals[k] is None]
    if missing:
        msg = f"Broker metadata is missing fields: {', '.join(missing)}."
        res = ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
        return None, None, None, None, None, None, res

    try:
        vals = {k: Decimal(str(raw_vals[k])) for k in keys}
    except (ValueError, TypeError) as e:
        res = ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=f"Broker metadata contains invalid types: {e}.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
        return None, None, None, None, None, None, res

    if (
        vals["volume_min"] <= 0
        or vals["volume_max"] <= 0
        or vals["volume_step"] <= 0
        or vals["pip_size"] <= 0
    ):
        res = ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message="Broker metadata contains non-positive values (inconsistent).",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
        return None, None, None, None, None, None, res

    if vals["volume_min"] > vals["volume_max"]:
        msg = (
            f"Broker metadata is inconsistent: "
            f"volume_min {vals['volume_min']} > volume_max {vals['volume_max']}."
        )
        res = ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
        return None, None, None, None, None, None, res

    return (
        vals["stop_level"],
        vals["freeze_level"],
        vals["volume_min"],
        vals["volume_max"],
        vals["volume_step"],
        vals["pip_size"],
        None,
    )


def _evaluate_spread_and_slippage(
    symbol: str,
    market_context: dict[str, Any],
    config: RiskConfig,
    pip_size: Decimal,
    is_live: bool,
) -> tuple[Decimal, Decimal, ExecutionFeasibilityResult | None]:
    spread = Decimal(
        str(
            market_context.get(f"{symbol}_spread")
            or market_context.get("spread", "0.0002")
        )
    )
    volatility = Decimal(
        str(
            market_context.get(f"{symbol}_volatility")
            or market_context.get("volatility", "0.0")
        )
    )

    spread_policy = SpreadPolicy(
        max_spread=Decimal(str(market_context.get("max_spread")))
        if market_context.get("max_spread") is not None
        else None,
        spread_sigma_multiplier=Decimal(
            str(
                market_context.get(
                    "spread_sigma_multiplier", config.max_spread_multiplier
                )
            )
        ),
        m1_spread_to_sigma_ratio_filter=Decimal(
            str(
                market_context.get(
                    "m1_spread_to_sigma_ratio_filter",
                    config.m1_spread_to_sigma_ratio_filter,
                )
            )
        ),
    )
    is_m1 = (
        market_context.get("timeframe") == "M1"
        or config.profile_name == "m1_micro_scalping"
    )
    spread_pass, spread_msg = check_spread_limit(
        spread, volatility, spread_policy, is_m1
    )
    if not spread_pass:
        res = ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SPREAD_BREACH,
            message=spread_msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
        return Decimal("0.0"), Decimal("0.0"), res

    slippage_pips = Decimal(
        str(
            market_context.get(f"{symbol}_slippage_limit")
            or market_context.get("slippage_limit", config.max_slippage_pips)
        )
    )
    slippage = slippage_pips * pip_size

    # Non-live multiplier defaults to 10.0
    mult_default = "10.0" if not is_live else "2.0"
    slippage_policy = SlippagePolicy(
        max_slippage=Decimal(str(market_context.get("max_slippage")))
        if market_context.get("max_slippage") is not None
        else None,
        slippage_sigma_multiplier=Decimal(
            str(market_context.get("slippage_sigma_multiplier", mult_default))
        ),
    )
    slippage_pass, slippage_msg = check_slippage_limit(
        slippage, volatility, slippage_policy
    )
    if not slippage_pass:
        res = ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SLIPPAGE_BREACH,
            message=slippage_msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
        return Decimal("0.0"), Decimal("0.0"), res

    return spread, slippage, None


def _evaluate_trade_constraints(
    proposed_trade: ProposedTrade,
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    stop_level: Decimal,
    freeze_level: Decimal,
    vol_min: Decimal,
    vol_max: Decimal,
    vol_step: Decimal,
    pip_size: Decimal,
) -> ExecutionFeasibilityResult | None:
    # Stop distance & price representation limits
    stop_pass, stop_msg = check_stop_distance_validity(
        proposed_trade, stop_level, freeze_level, pip_size
    )
    if not stop_pass:
        return ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SLIPPAGE_BREACH,
            message=stop_msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    # Lot step & volume step granularity limits
    vol_pass, vol_msg, reduced = check_lot_step_validity(
        proposed_trade.volume, vol_min, vol_max, vol_step
    )
    if not vol_pass:
        status = (
            RiskDecisionStatus.REDUCE_SIZE
            if reduced is not None
            else RiskDecisionStatus.REJECT
        )
        severity = (
            RiskSeverity.SOFT_BREACH
            if reduced is not None
            else RiskSeverity.HARD_BREACH
        )
        return ExecutionFeasibilityResult(
            status=status,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=vol_msg,
            severity=severity,
            breached=True,
            reduced_volume=reduced,
        )

    # Filling mode limit checks
    symbol = proposed_trade.symbol
    filling_mode = market_context.get(f"{symbol}_filling_mode") or market_context.get(
        "filling_mode"
    )
    if filling_mode is not None:
        proposed_mode = proposed_trade.order_type
        if proposed_mode is not None:
            allowed_modes = [m.strip().upper() for m in str(filling_mode).split(",")]
            if proposed_mode.upper() not in allowed_modes:
                msg = (
                    f"Order type/filling mode {proposed_mode} is not "
                    f"authorized by broker allowed modes: {allowed_modes}."
                )
                return ExecutionFeasibilityResult(
                    status=RiskDecisionStatus.REJECT,
                    reason_code=RiskReasonCode.INVALID_INPUT,
                    message=msg,
                    severity=RiskSeverity.HARD_BREACH,
                    breached=True,
                )

    # Max holding-time checks
    hold_pass, hold_msg = check_holding_time_limit(proposed_trade, market_context)
    if not hold_pass:
        return ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=hold_msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    # Trade frequency limits
    freq_pass, freq_msg = check_trade_frequency_limit(
        portfolio_state, proposed_trade, market_context
    )
    if not freq_pass:
        return ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.FREQUENCY_BREACH,
            message=freq_msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    return None


def _evaluate_metadata_status(
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
) -> tuple[bool, bool, ExecutionFeasibilityResult | None]:
    """Check metadata freshness and presence.

    Returns:
        tuple of (skip_checks, is_live, error_result)
    """
    if proposed_trade is None:
        return (
            True,
            False,
            ExecutionFeasibilityResult(
                status=RiskDecisionStatus.APPROVE,
                reason_code=RiskReasonCode.OK,
                message="No proposed trade to evaluate for execution feasibility.",
                severity=RiskSeverity.INFO,
                breached=False,
            ),
        )

    symbol = proposed_trade.symbol
    freshness = market_context.get(f"{symbol}_freshness") or market_context.get(
        "freshness"
    )
    is_live = market_context.get("mode") in {
        "micro_live",
        "full_live",
    } or market_context.get("environment") in {"production", "live"}

    # Check if any broker metadata is provided (prefixed or base)
    metadata_keys = [
        f"{symbol}_stop_level",
        "stop_level",
        f"{symbol}_freeze_level",
        "freeze_level",
        f"{symbol}_volume_min",
        "volume_min",
        f"{symbol}_volume_max",
        "volume_max",
        f"{symbol}_volume_step",
        "volume_step",
        f"{symbol}_pip_size",
        "pip_size",
    ]
    has_any_metadata = any(market_context.get(k) is not None for k in metadata_keys)

    if not is_live and not has_any_metadata:
        msg = (
            "Execution feasibility checks skipped "
            "(no broker metadata provided in non-live mode)."
        )
        return (
            True,
            False,
            ExecutionFeasibilityResult(
                status=RiskDecisionStatus.APPROVE,
                reason_code=RiskReasonCode.OK,
                message=msg,
                severity=RiskSeverity.INFO,
                breached=False,
            ),
        )

    if freshness is None:
        if is_live:
            msg = (
                "Live mode blocked: missing broker "
                "constraint metadata freshness timestamp."
            )
            return (
                False,
                is_live,
                ExecutionFeasibilityResult(
                    status=RiskDecisionStatus.BLOCK,
                    reason_code=RiskReasonCode.STALE_EVIDENCE,
                    message=msg,
                    severity=RiskSeverity.CRITICAL_BREACH,
                    breached=True,
                ),
            )
    else:
        from app.utils.normalization import to_utc_datetime, utc_now

        now = utc_now()
        fresh_dt = to_utc_datetime(freshness)
        stale_limit = float(market_context.get("max_stale_seconds", 60.0))
        age = (now - fresh_dt).total_seconds()
        if age > stale_limit:
            msg = (
                f"Broker metadata is stale by {age:.1f}s (max allowed: {stale_limit}s)."
            )
            return (
                False,
                is_live,
                ExecutionFeasibilityResult(
                    status=RiskDecisionStatus.REJECT,
                    reason_code=RiskReasonCode.STALE_EVIDENCE,
                    message=msg,
                    severity=RiskSeverity.HARD_BREACH,
                    breached=True,
                ),
            )

    return False, is_live, None


def check_execution_feasibility(  # noqa: PLR0911
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> ExecutionFeasibilityResult:
    """Evaluate pre-trade execution feasibility limits on a candidate trade.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Optional candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        ExecutionFeasibilityResult showing feasibility approval status.
    """
    _skip_checks, is_live, err_res = _evaluate_metadata_status(
        proposed_trade, market_context
    )
    if err_res is not None:
        return err_res

    if proposed_trade is None:
        return ExecutionFeasibilityResult(
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No proposed trade to evaluate for execution feasibility.",
            severity=RiskSeverity.INFO,
            breached=False,
        )
    symbol = proposed_trade.symbol

    # 2. Presence & consistency check helper
    (
        stop_level,
        freeze_level,
        vol_min,
        vol_max,
        vol_step,
        pip_size,
        err_res,
    ) = _resolve_metadata_and_defaults(symbol, market_context, is_live)
    if err_res is not None:
        return err_res

    # Narrow Decimal | None → Decimal after guard (guaranteed by _resolve)
    stop_level = cast("Decimal", stop_level)
    freeze_level = cast("Decimal", freeze_level)
    vol_min = cast("Decimal", vol_min)
    vol_max = cast("Decimal", vol_max)
    vol_step = cast("Decimal", vol_step)
    pip_size = cast("Decimal", pip_size)

    # 3. Check market open / session constraints
    session_open = market_context.get(f"{symbol}_session_open", True)
    tradable = market_context.get(f"{symbol}_tradable", True)
    session = market_context.get("session", "OPEN")
    market_open = session != "CLOSED" and session_open and tradable
    if not market_open:
        msg = f"Execution gate rejected: {symbol} market is closed or suspended."
        return ExecutionFeasibilityResult(
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SPREAD_BREACH,
            message=msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    # 4. Spread and slippage check helper
    spread, slippage, err_res = _evaluate_spread_and_slippage(
        symbol, market_context, config, pip_size, is_live
    )
    if err_res is not None:
        return err_res

    # 5. Trade constraints checks helper
    err_res = _evaluate_trade_constraints(
        proposed_trade,
        portfolio_state,
        market_context,
        stop_level,
        freeze_level,
        vol_min,
        vol_max,
        vol_step,
        pip_size,
    )
    if err_res is not None:
        return err_res

    # Build snapshot details
    details = {
        "spread": float(spread),
        "slippage": float(slippage),
        "stop_level": float(stop_level),
        "freeze_level": float(freeze_level),
        "lot_step": float(vol_step),
        "session_open": session_open,
        "tradable": tradable,
    }
    if proposed_trade.expected_holding_period is not None:
        details["expected_holding_period"] = proposed_trade.expected_holding_period

    return ExecutionFeasibilityResult(
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Execution feasibility checks passed successfully.",
        severity=RiskSeverity.INFO,
        breached=False,
        details=details,
    )


class ExecutionRiskGate:
    """Engine for validating execution feasibility.

    Validates spread, slippage, and broker constraints.
    """

    def __init__(self, config: RiskConfig) -> None:
        """Initialize risk gate with active configuration profile."""
        self.config = config

    def check_execution_feasibility(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
    ) -> ExecutionFeasibilityResult:
        """Evaluate pre-trade execution feasibility limits on a candidate trade."""
        return check_execution_feasibility(
            portfolio_state, proposed_trade, market_context, self.config
        )


# --- Backward compatibility wrappers ---


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
