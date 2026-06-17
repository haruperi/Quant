# ruff: noqa: E501, ARG001, ARG004, PLR0911, SIM108, TRY301, B904
"""Risk sizing and allocation engines.

This module implements position sizing calculations and capital allocation algorithms.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from app.services.risk.models import (
    PortfolioState,
    PositionSizingRequest,
    PositionSizingResult,
    ProposedAllocation,
    RiskConfig,
)
from app.utils.errors import (
    InsufficientKEvidenceError,
    InsufficientVolatilityEvidenceError,
    InvalidPortfolioStateError,
    MissingStopLossError,
    ValidationError,
)


def get_pip_scale(symbol: str) -> Decimal:
    """Return pip scale for symbol, using MT5 values dynamically.

    Raises:
        ValidationError: If the symbol info cannot be retrieved from the broker.
    """
    try:
        from app.services.brokers.mt5 import get_symbol_info

        info = get_symbol_info(symbol)
        if info is not None:
            point = Decimal(str(info.point))
            digits = info.digits
            # Standard Forex conversion: if 3 or 5 digits, pip is 10 * point
            if digits in (3, 5):
                return Decimal(10) * point
            return point
    except Exception as e:
        msg = f"Failed to retrieve point/digits metadata from MT5 for symbol {symbol}: {e}"
        raise ValidationError(msg) from e

    msg = f"Symbol metadata not found in MT5 for symbol {symbol}."
    raise ValidationError(msg)


def get_contract_size(symbol: str) -> Decimal:
    """Return contract size for symbol, using MT5 values dynamically.

    Raises:
        ValidationError: If the symbol info cannot be retrieved from the broker.
    """
    try:
        from app.services.brokers.mt5 import get_symbol_info

        info = get_symbol_info(symbol)
        if info is not None and hasattr(info, "trade_contract_size"):
            return Decimal(str(info.trade_contract_size))
    except Exception as e:
        msg = f"Failed to retrieve contract size metadata from MT5 for symbol {symbol}: {e}"
        raise ValidationError(msg) from e

    msg = f"Symbol contract size metadata not found in MT5 for symbol {symbol}."
    raise ValidationError(msg)


def calculate_fixed_lot_size(request: PositionSizingRequest) -> Decimal:
    """Calculate fixed lot volume."""
    if request.fixed_volume is None:
        return Decimal("0.10")  # fallback default
    return request.fixed_volume


def calculate_fixed_risk_size(
    request: PositionSizingRequest,
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
) -> tuple[Decimal, Decimal]:
    """Calculate position size based on fixed account risk.

    Returns:
        Tuple of (calculated_volume, stop_distance_pips)
    """
    if portfolio_state.equity <= 0:
        raise InvalidPortfolioStateError(
            "Percentage-risk calculations require positive account equity."
        )

    if request.stop_loss_pips is None or request.stop_loss_pips <= 0:
        raise MissingStopLossError(
            "Stop loss is missing or invalid for fixed-risk sizing."
        )

    stop_pips = request.stop_loss_pips

    # Calculate risk amount
    risk_amount = Decimal("0.0")
    if request.risk_amount is not None:
        risk_amount = request.risk_amount
    elif request.risk_percent is not None:
        risk_amount = portfolio_state.equity * (request.risk_percent / Decimal("100.0"))
    else:
        # Fallback to config default daily loss pct
        risk_amount = portfolio_state.equity * (risk_config.max_daily_loss_pct)

    # Determine pip value per 1 lot in account currency (assuming USD base)
    pip_scale = get_pip_scale(request.symbol)
    contract_size = get_contract_size(request.symbol)
    # Pip value = contract_size * pip_scale
    pip_value = contract_size * pip_scale

    volume = risk_amount / (stop_pips * pip_value)
    # Clamp/round to 2 decimals
    rounded_volume = volume.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return max(rounded_volume, Decimal("0.01")), stop_pips


def calculate_milestone_size(
    request: PositionSizingRequest,
    portfolio_state: PortfolioState,
) -> Decimal:
    """Calculate position size based on account milestones."""
    equity = portfolio_state.equity
    if equity < Decimal(10000):
        return Decimal("0.10")
    if equity < Decimal(50000):
        return Decimal("0.50")
    if equity < Decimal(100000):
        return Decimal("1.00")
    return Decimal("2.00")


def calculate_kelly_size(
    request: PositionSizingRequest,
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
    trade_samples: list[dict[str, Any]] | None = None,
    has_waiver: bool = False,
) -> tuple[Decimal, Decimal]:
    """Calculate position size based on Kelly Criterion.

    Prohibits full Kelly unless waiver is provided.
    Requires minimum trades threshold (default 30).
    """
    samples = trade_samples or []
    if len(samples) < risk_config.min_kelly_trades:
        raise InsufficientKEvidenceError(
            "Insufficient historical trade evidence for Kelly Criterion."
        )

    # Calculate win rate and payoff ratio
    wins = sum(1 for t in samples if Decimal(str(t.get("profit", "0"))) > 0)
    win_rate = Decimal(wins) / Decimal(len(samples))

    total_wins_profit = sum(
        Decimal(str(t.get("profit", "0")))
        for t in samples
        if Decimal(str(t.get("profit", "0"))) > 0
    )
    total_losses_loss = sum(
        abs(Decimal(str(t.get("profit", "0"))))
        for t in samples
        if Decimal(str(t.get("profit", "0"))) <= 0
    )

    loss_count = len(samples) - wins
    if loss_count == 0 or total_losses_loss == 0:
        payoff_ratio = Decimal("2.0")  # default assumption
    else:
        avg_win = total_wins_profit / Decimal(wins) if wins > 0 else Decimal("0.0")
        avg_loss = total_losses_loss / Decimal(loss_count)
        payoff_ratio = avg_win / avg_loss if avg_loss > 0 else Decimal("2.0")

    # Kelly formula: f = w - (1 - w) / R
    if payoff_ratio <= 0:
        f = Decimal("0.0")
    else:
        f = win_rate - (Decimal("1.0") - win_rate) / payoff_ratio

    if f <= 0:
        return Decimal("0.01"), f

    # Apply Kelly fraction multiplier
    multiplier = risk_config.default_kelly_fraction
    if has_waiver:
        # Full Kelly allowed by waiver
        applied_fraction = f
    else:
        applied_fraction = f * multiplier

    # Translate fraction of capital to lot volume
    # E.g. risk amount = equity * applied_fraction
    risk_amount = portfolio_state.equity * applied_fraction
    pip_scale = get_pip_scale(request.symbol)
    contract_size = get_contract_size(request.symbol)
    pip_value = contract_size * pip_scale

    # Assume default 30 pips stop distance for Kelly translation
    stop_distance = Decimal("30.0")
    volume = risk_amount / (stop_distance * pip_value)

    rounded_volume = volume.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return max(rounded_volume, Decimal("0.01")), applied_fraction


def calculate_volatility_adjusted_size(
    request: PositionSizingRequest,
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
) -> tuple[Decimal, Decimal]:
    """Calculate volatility adjusted position size using ATR."""
    if request.atr_value is None or request.atr_value <= 0:
        raise InsufficientVolatilityEvidenceError(
            "Volatility (ATR) evidence is insufficient for calculation."
        )

    # Convert ATR to pips: e.g. ATR = 0.0030, pip_scale = 0.0001 -> 30 pips stop distance
    pip_scale = get_pip_scale(request.symbol)
    stop_distance_pips = request.atr_value / pip_scale
    if request.multiplier is not None:
        stop_distance_pips *= request.multiplier
    else:
        stop_distance_pips *= Decimal("1.5")  # default ATR multiplier

    # Now calculate via fixed risk using computed stop distance
    new_req = PositionSizingRequest(
        symbol=request.symbol,
        method="fixed_risk",
        risk_percent=request.risk_percent or Decimal("1.0"),
        stop_loss_pips=stop_distance_pips,
    )
    vol, _ = calculate_fixed_risk_size(new_req, portfolio_state, risk_config)
    return vol, stop_distance_pips


def calculate_fixed_fractional_size(
    request: PositionSizingRequest,
    portfolio_state: PortfolioState,
) -> Decimal:
    """Calculate fixed fractional position size."""
    fraction = request.risk_percent or Decimal("1.0")
    # Notional allocation = equity * fraction
    allocated_capital = portfolio_state.equity * (fraction / Decimal("100.0"))

    pip_scale = get_pip_scale(request.symbol)
    contract_size = get_contract_size(request.symbol)
    pip_value = contract_size * pip_scale

    # default stop distance
    stop_pips = Decimal("30.0")
    volume = allocated_capital / (stop_pips * pip_value)

    rounded_volume = volume.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return max(rounded_volume, Decimal("0.01"))


def calculate_position_size(
    sizing_request: PositionSizingRequest,
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
    trade_samples: list[dict[str, Any]] | None = None,
    has_waiver: bool = False,
) -> PositionSizingResult:
    """Calculate position size according to requested method."""
    method = sizing_request.method
    notes: list[str] = []

    try:
        if method == "fixed_lot":
            vol = calculate_fixed_lot_size(sizing_request)
            return PositionSizingResult(
                calculated_volume=vol,
                method_applied="fixed_lot",
                notes=["Applied fixed lot calculation."],
            )
        if method == "fixed_risk":
            vol, stop = calculate_fixed_risk_size(
                sizing_request, portfolio_state, risk_config
            )
            return PositionSizingResult(
                calculated_volume=vol,
                method_applied="fixed_risk",
                stop_distance_pips=stop,
                notes=["Applied fixed risk stop-dependent calculation."],
            )
        if method == "milestone":
            vol = calculate_milestone_size(sizing_request, portfolio_state)
            return PositionSizingResult(
                calculated_volume=vol,
                method_applied="milestone",
                notes=["Applied milestone-based calculation."],
            )
        if method == "kelly_criterion":
            try:
                vol, fraction = calculate_kelly_size(
                    sizing_request,
                    portfolio_state,
                    risk_config,
                    trade_samples,
                    has_waiver,
                )
                waiver_note = f"Kelly fraction {fraction:.4f} applied. " + (
                    "Waiver active." if has_waiver else "Fractional applied."
                )
                return PositionSizingResult(
                    calculated_volume=vol,
                    method_applied="kelly_criterion",
                    kelly_fraction_applied=fraction,
                    notes=[waiver_note],
                )
            except InsufficientKEvidenceError as e:
                # Sizing fallback to fixed risk if configured
                notes.append(f"Kelly failed: {e}. Falling back to fixed risk.")
                # Construct a fixed risk fallback request
                fallback_req = PositionSizingRequest(
                    symbol=sizing_request.symbol,
                    method="fixed_risk",
                    risk_percent=Decimal("1.0"),
                    stop_loss_pips=Decimal("30.0"),
                )
                vol, stop = calculate_fixed_risk_size(
                    fallback_req, portfolio_state, risk_config
                )
                return PositionSizingResult(
                    calculated_volume=vol,
                    method_applied="fixed_risk_fallback",
                    stop_distance_pips=stop,
                    notes=notes,
                )
        elif method == "volatility":
            vol, stop = calculate_volatility_adjusted_size(
                sizing_request, portfolio_state, risk_config
            )
            return PositionSizingResult(
                calculated_volume=vol,
                method_applied="volatility",
                stop_distance_pips=stop,
                notes=["Applied ATR-adjusted volatility calculation."],
            )
        elif method == "fixed_fractional":
            vol = calculate_fixed_fractional_size(sizing_request, portfolio_state)
            return PositionSizingResult(
                calculated_volume=vol,
                method_applied="fixed_fractional",
                notes=["Applied fixed fractional capital calculation."],
            )
        else:
            msg = f"Unknown sizing method: {method}"
            raise ValidationError(msg)
    except Exception as e:
        if isinstance(
            e,
            ValidationError
            | MissingStopLossError
            | InsufficientVolatilityEvidenceError
            | InvalidPortfolioStateError,
        ):
            raise
        msg = f"Sizing calculation failed: {e}"
        raise ValidationError(msg)


class AllocationService:
    """Service to evaluate capital allocation proposals across strategy baskets."""

    @staticmethod
    def propose(
        proposal: ProposedAllocation,
        portfolio_state: PortfolioState,
        risk_config: RiskConfig,
    ) -> dict[str, Any]:
        """Evaluate capital allocation proposal against risk parameters."""
        total_allocated = sum(proposal.allocations.values())
        if total_allocated > portfolio_state.equity:
            return {
                "status": "rejected",
                "reason": "Proposed capital allocation exceeds available portfolio equity.",
                "allocations": proposal.allocations,
            }

        # Check maximum allocation limits (e.g. 50% max per strategy)
        max_strategy_pct = Decimal("0.50")
        max_strategy_cap = portfolio_state.equity * max_strategy_pct
        for strat, amt in proposal.allocations.items():
            if amt > max_strategy_cap:
                return {
                    "status": "rejected",
                    "reason": f"Allocation to strategy {strat} exceeds max threshold of {max_strategy_cap}.",
                    "allocations": proposal.allocations,
                }

        return {
            "status": "accepted",
            "reason": "Proposed allocation meets all threshold validation checks.",
            "allocations": proposal.allocations,
        }

    @staticmethod
    def equal_capital(
        strategy_ids: list[str], available_capital: Decimal
    ) -> ProposedAllocation:
        """Split available capital equally across active strategy IDs."""
        if not strategy_ids:
            return ProposedAllocation(allocations={}, as_of=datetime.now(UTC))

        equal_share = available_capital / Decimal(len(strategy_ids))
        rounded_share = equal_share.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

        allocations = dict.fromkeys(strategy_ids, rounded_share)
        return ProposedAllocation(allocations=allocations, as_of=datetime.now(UTC))

    @staticmethod
    def confidence_weighted(
        strategy_confidences: dict[str, Decimal], available_capital: Decimal
    ) -> ProposedAllocation:
        """Allocate capital in proportion to positive strategy confidence scores."""
        # Filter negative and zero confidence scores
        filtered_conf = {k: v for k, v in strategy_confidences.items() if v > 0}
        if not filtered_conf:
            return ProposedAllocation(allocations={}, as_of=datetime.now(UTC))

        total_confidence = sum(filtered_conf.values())
        allocations = {}
        for s, conf in filtered_conf.items():
            share = available_capital * (conf / total_confidence)
            allocations[s] = share.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

        return ProposedAllocation(allocations=allocations, as_of=datetime.now(UTC))
