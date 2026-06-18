"""Position sizing engine.

Provides stateless calculators for fixed risk, fixed fractional,
volatility-adjusted, milestone, and Kelly sizing methods, complying
with broker lot restrictions and risk caps.
"""

from __future__ import annotations

import math
from decimal import Decimal
from enum import StrEnum
from typing import Any

from app.services.risk.models import (
    PortfolioState,
    PositionSizingRequest,
    PositionSizingResult,
    RiskConfig,
)
from app.utils.logger import logger


class SizingMethod(StrEnum):
    """Position sizing calculator types."""

    FIXED_LOT = "fixed_lot"
    FIXED_RISK = "fixed_risk"
    FIXED_FRACTIONAL = "fixed_fractional"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    CORRELATION_ADJUSTED = "correlation_adjusted"
    MILESTONE = "milestone"
    KELLY = "kelly"


def _resolve_specs(
    symbol: str, market_context: dict[str, Any]
) -> tuple[dict[str, Any] | None, str]:
    """Resolve and validate symbol specifications from market context."""
    volume_min = market_context.get("volume_min")
    volume_max = market_context.get("volume_max")
    volume_step = market_context.get("volume_step")
    contract_size = market_context.get("contract_size")

    if (
        volume_min is None
        or volume_max is None
        or volume_step is None
        or contract_size is None
    ):
        logger.warning(f"Sizing rejected: missing symbol spec for {symbol}.")
        return None, "missing_symbol_metadata"

    conversion_rate = Decimal(str(market_context.get("conversion_rate", "1.0")))
    if conversion_rate <= 0:
        logger.warning("Sizing rejected: invalid conversion rate.")
        return None, "invalid_conversion_rate"

    digits = int(market_context.get("digits", 5))
    tick_size = market_context.get("tick_size")
    tick_size = (
        Decimal(str(tick_size)) if tick_size is not None else Decimal(10) ** -digits
    )

    tick_value = market_context.get("tick_value")
    tick_value = (
        Decimal(str(tick_value))
        if tick_value is not None
        else tick_size * Decimal(str(contract_size)) * conversion_rate
    )

    if tick_size <= 0 or tick_value <= 0:
        logger.warning("Sizing rejected: invalid tick size or tick value.")
        return None, "invalid_tick_metadata"

    return {
        "volume_min": Decimal(str(volume_min)),
        "volume_max": Decimal(str(volume_max)),
        "volume_step": Decimal(str(volume_step)),
        "contract_size": Decimal(str(contract_size)),
        "conversion_rate": conversion_rate,
        "digits": digits,
        "tick_size": tick_size,
        "tick_value": tick_value,
    }, ""


def _resolve_volatility_stop(
    request: PositionSizingRequest,
    market_context: dict[str, Any],
    digits: int,
    constraints_applied: list[str],
) -> tuple[Decimal, Decimal]:
    """Calculate price and pip stop distance under volatility regime."""
    atr_value = request.atr_value
    multiplier = request.multiplier or Decimal("2.0")
    m1_vol = market_context.get("m1_volatility")

    if m1_vol is not None:
        stop_distance_price = Decimal(str(m1_vol)) * Decimal(str(multiplier))
        constraints_applied.append("m1_volatility_stop")
    elif atr_value is not None:
        stop_distance_price = Decimal(str(atr_value)) * Decimal(str(multiplier))
        constraints_applied.append("atr_volatility_stop")
    else:
        raise ValueError("Missing volatility inputs.")

    pip_size = Decimal("0.01") if digits in {2, 3} else Decimal("0.0001")
    stop_distance_pips = stop_distance_price / pip_size
    return stop_distance_price, stop_distance_pips


def _resolve_risk_amount(
    method: SizingMethod,
    request: PositionSizingRequest,
    equity: Decimal,
    max_risk_amt: Decimal,
    constraints_applied: list[str],
) -> Decimal:
    """Resolve the target risk capital amount."""
    risk_amount = Decimal("0.0")
    if method == SizingMethod.FIXED_RISK:
        if request.risk_amount is not None:
            risk_amount = Decimal(str(request.risk_amount))
        elif request.risk_percent is not None:
            risk_amount = equity * Decimal(str(request.risk_percent))
        else:
            risk_amount = max_risk_amt

    elif method in {
        SizingMethod.FIXED_FRACTIONAL,
        SizingMethod.VOLATILITY_ADJUSTED,
        SizingMethod.CORRELATION_ADJUSTED,
        SizingMethod.MILESTONE,
    }:
        risk_pct = request.risk_percent or Decimal("0.02")
        risk_amount = equity * Decimal(str(risk_pct))

    if risk_amount > max_risk_amt:
        risk_amount = max_risk_amt
        constraints_applied.append("max_risk_per_trade_cap")

    return risk_amount


def _calc_raw_size(
    method: SizingMethod,
    request: PositionSizingRequest,
    market_context: dict[str, Any],
    risk_amount: Decimal,
    stop_distance_price: Decimal,
    tick_size: Decimal,
    tick_value: Decimal,
    equity: Decimal,
    contract_size: Decimal,
    conversion_rate: Decimal,
    constraints_applied: list[str],
) -> Decimal:
    """Compute initial raw lot size for the chosen method."""
    if method == SizingMethod.FIXED_LOT:
        return Decimal(str(request.fixed_volume or Decimal("0.10")))

    if method in {
        SizingMethod.FIXED_RISK,
        SizingMethod.FIXED_FRACTIONAL,
        SizingMethod.VOLATILITY_ADJUSTED,
        SizingMethod.CORRELATION_ADJUSTED,
        SizingMethod.MILESTONE,
    }:
        risk_per_lot = (stop_distance_price / tick_size) * tick_value
        raw_size = risk_amount / risk_per_lot

        if method == SizingMethod.CORRELATION_ADJUSTED:
            corr_coef = Decimal(str(market_context.get("portfolio_correlation", "0.0")))
            corr_mult = max(Decimal("0.1"), Decimal("1.0") - corr_coef * Decimal("0.5"))
            raw_size *= corr_mult
            constraints_applied.append("correlation_adjustment")
        return raw_size

    if method == SizingMethod.KELLY:
        win_rate = Decimal(str(market_context.get("kelly_win_rate", "0.50")))
        win_loss_ratio = Decimal(str(market_context.get("kelly_win_loss_ratio", "1.5")))
        trade_count = int(market_context.get("historical_trade_count", 0))
        min_trades = int(market_context.get("kelly_min_trades", 30))

        if win_loss_ratio > 0:
            kelly_fraction = win_rate - (Decimal("1.0") - win_rate) / win_loss_ratio
        else:
            kelly_fraction = Decimal("0.0")

        kelly_fraction = max(Decimal("0.0"), kelly_fraction)

        if trade_count < min_trades:
            kelly_fraction = Decimal("0.0")
            constraints_applied.append("kelly_advisory_insufficient_evidence")
        else:
            constraints_applied.append("kelly_fraction_applied")

        if stop_distance_price > 0:
            risk_per_lot = (stop_distance_price / tick_size) * tick_value
            return (kelly_fraction * equity) / risk_per_lot
        return (kelly_fraction * equity) / (contract_size * conversion_rate)

    return Decimal("0.0")


def _apply_reductions(
    raw_size: Decimal,
    market_context: dict[str, Any],
    constraints_applied: list[str],
) -> Decimal:
    """Apply drawdown, currency, and correlation reductions."""
    size = raw_size
    step_down = Decimal(str(market_context.get("drawdown_step_down_multiplier", "1.0")))
    if step_down < 1:
        size *= step_down
        constraints_applied.append("drawdown_step_down")

    ccy_reduction = Decimal(
        str(market_context.get("currency_exposure_reduction", "1.0"))
    )
    if ccy_reduction < 1:
        size *= ccy_reduction
        constraints_applied.append("currency_exposure_reduction")

    cluster_reduction = Decimal(
        str(market_context.get("correlation_cluster_reduction", "1.0"))
    )
    if cluster_reduction < 1:
        size *= cluster_reduction
        constraints_applied.append("correlation_cluster_reduction")

    return size


def calculate_position_size(
    request: PositionSizingRequest,
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> PositionSizingResult:
    """Statelessly calculate position sizing and apply risk/broker constraints."""
    symbol = request.symbol
    method = SizingMethod(request.method)
    constraints_applied: list[str] = []

    # 1. Resolve and validate specifications
    specs, err_constraint = _resolve_specs(symbol, market_context)
    if specs is None:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=method,
            constraints_applied=[err_constraint],
            risk_contribution=Decimal("0.0"),
        )

    # Unpack specifications
    volume_min = specs["volume_min"]
    volume_max = specs["volume_max"]
    volume_step = specs["volume_step"]
    contract_size = specs["contract_size"]
    conversion_rate = specs["conversion_rate"]
    digits = specs["digits"]
    tick_size = specs["tick_size"]
    tick_value = specs["tick_value"]

    # 2. Stop distance resolver
    stop_distance_pips = Decimal("0.0")
    stop_distance_price = Decimal("0.0")

    if method == SizingMethod.VOLATILITY_ADJUSTED:
        try:
            stop_distance_price, stop_distance_pips = _resolve_volatility_stop(
                request, market_context, digits, constraints_applied
            )
        except ValueError:
            logger.warning("Sizing rejected: missing volatility inputs.")
            return PositionSizingResult(
                calculated_volume=Decimal("0.0"),
                sizing_method=method,
                constraints_applied=["missing_volatility_inputs"],
                risk_contribution=Decimal("0.0"),
            )
    elif request.stop_loss_pips is not None:
        stop_distance_pips = Decimal(str(request.stop_loss_pips))
        pip_size = Decimal("0.01") if digits in {2, 3} else Decimal("0.0001")
        stop_distance_price = stop_distance_pips * pip_size

    # Stop distance check for risk models
    if (
        method
        in {
            SizingMethod.FIXED_RISK,
            SizingMethod.FIXED_FRACTIONAL,
            SizingMethod.VOLATILITY_ADJUSTED,
            SizingMethod.CORRELATION_ADJUSTED,
        }
        and stop_distance_price <= 0
    ):
        logger.warning(f"Sizing rejected: invalid stop distance {stop_distance_price}.")
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=method,
            constraints_applied=["invalid_stop_distance"],
            risk_contribution=Decimal("0.0"),
        )

    # 3. Resolve Risk Capital
    equity = portfolio_state.equity
    if equity <= 0:
        logger.warning("Sizing rejected: portfolio equity is zero or negative.")
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=method,
            constraints_applied=["zero_or_negative_equity"],
            risk_contribution=Decimal("0.0"),
        )

    max_risk_pct = getattr(config, "max_risk_per_trade", Decimal("0.02"))
    max_risk_amt = equity * max_risk_pct
    risk_amount = _resolve_risk_amount(
        method, request, equity, max_risk_amt, constraints_applied
    )

    # 4. Sizing computation
    raw_size = _calc_raw_size(
        method,
        request,
        market_context,
        risk_amount,
        stop_distance_price,
        tick_size,
        tick_value,
        equity,
        contract_size,
        conversion_rate,
        constraints_applied,
    )

    # 5. Apply reductions
    raw_size = _apply_reductions(raw_size, market_context, constraints_applied)

    # 6. Rounded volume step constraints
    volume_steps_count = math.floor(raw_size / volume_step)
    calculated_volume = Decimal(str(volume_steps_count)) * volume_step

    if calculated_volume > volume_max:
        calculated_volume = volume_max
        constraints_applied.append("volume_max_cap")
    elif calculated_volume < volume_min:
        logger.warning(
            f"Sizing rejected: calculated size {calculated_volume} is below "
            f"broker minimum {volume_min}."
        )
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            stop_distance_pips=stop_distance_pips,
            sizing_method=method,
            constraints_applied=sorted([*constraints_applied, "below_minimum_volume"]),
            risk_contribution=Decimal("0.0"),
        )

    risk_per_lot_calc = Decimal("0.0")
    if stop_distance_price > 0:
        risk_per_lot_calc = (stop_distance_price / tick_size) * tick_value
    else:
        risk_per_lot_calc = contract_size * conversion_rate

    risk_contribution = calculated_volume * risk_per_lot_calc

    return PositionSizingResult(
        calculated_volume=calculated_volume,
        stop_distance_pips=stop_distance_pips,
        sizing_method=method,
        constraints_applied=sorted(constraints_applied),
        risk_contribution=risk_contribution,
    )
