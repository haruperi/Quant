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


class BasePositionSizer:
    """Base class for all position sizers."""

    def __init__(self, config: RiskConfig) -> None:
        """Initialize sizer with risk configuration."""
        self.config = config

    def calculate(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
        specs: dict[str, Any],
        stop_distance_price: Decimal,
        constraints_applied: list[str],
    ) -> Decimal:
        """Calculate raw lot size for this sizing method."""
        raise NotImplementedError


class FixedRiskSizer(BasePositionSizer):
    """Sizes positions based on a fixed dollar amount or percentage of equity."""

    def calculate(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
        specs: dict[str, Any],
        stop_distance_price: Decimal,
        constraints_applied: list[str],
    ) -> Decimal:
        """Calculate size using stop loss distance and target risk capital."""
        _ = market_context
        equity = portfolio_state.equity
        max_risk_pct = getattr(self.config, "max_risk_per_trade", Decimal("0.02"))
        max_risk_amt = equity * max_risk_pct

        if request.risk_amount is not None:
            risk_amount = Decimal(str(request.risk_amount))
        elif request.risk_percent is not None:
            risk_amount = equity * Decimal(str(request.risk_percent))
        else:
            risk_amount = max_risk_amt

        if risk_amount > max_risk_amt:
            risk_amount = max_risk_amt
            constraints_applied.append("max_risk_per_trade_cap")

        tick_size = Decimal(str(specs["tick_size"]))
        tick_value = Decimal(str(specs["tick_value"]))

        if stop_distance_price <= 0:
            return Decimal("0.0")

        risk_per_lot = (stop_distance_price / tick_size) * tick_value
        if risk_per_lot <= 0:
            return Decimal("0.0")

        return risk_amount / risk_per_lot


class FixedFractionalSizer(BasePositionSizer):
    """Sizes positions as a fixed fraction/percentage of total equity."""

    def calculate(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
        specs: dict[str, Any],
        stop_distance_price: Decimal,
        constraints_applied: list[str],
    ) -> Decimal:
        """Calculate fractional size based on equity."""
        _ = market_context
        equity = portfolio_state.equity
        risk_pct = request.risk_percent or Decimal("0.02")
        max_risk_pct = getattr(self.config, "max_risk_per_trade", Decimal("0.02"))

        if risk_pct > max_risk_pct:
            risk_pct = max_risk_pct
            constraints_applied.append("max_risk_per_trade_cap")

        risk_amount = equity * Decimal(str(risk_pct))
        tick_size = Decimal(str(specs["tick_size"]))
        tick_value = Decimal(str(specs["tick_value"]))

        if stop_distance_price <= 0:
            return Decimal("0.0")

        risk_per_lot = (stop_distance_price / tick_size) * tick_value
        if risk_per_lot <= 0:
            return Decimal("0.0")

        return risk_amount / risk_per_lot


class VolatilityAdjustedSizer(BasePositionSizer):
    """Sizes positions dynamically using volatility stop loss distances."""

    def calculate(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
        specs: dict[str, Any],
        stop_distance_price: Decimal,
        constraints_applied: list[str],
    ) -> Decimal:
        """Calculate size using volatility stop distance."""
        _ = market_context
        equity = portfolio_state.equity
        risk_pct = request.risk_percent or Decimal("0.02")
        max_risk_pct = getattr(self.config, "max_risk_per_trade", Decimal("0.02"))

        if risk_pct > max_risk_pct:
            risk_pct = max_risk_pct
            constraints_applied.append("max_risk_per_trade_cap")

        risk_amount = equity * Decimal(str(risk_pct))
        tick_size = Decimal(str(specs["tick_size"]))
        tick_value = Decimal(str(specs["tick_value"]))

        if stop_distance_price <= 0:
            return Decimal("0.0")

        risk_per_lot = (stop_distance_price / tick_size) * tick_value
        if risk_per_lot <= 0:
            return Decimal("0.0")

        return risk_amount / risk_per_lot


class KellyReferenceSizer(BasePositionSizer):
    """Calculates position sizing using the Kelly Criterion.

    Treated as advisory/upper-bound unless fractional Kelly is explicitly enabled.
    """

    def calculate(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
        specs: dict[str, Any],
        stop_distance_price: Decimal,
        constraints_applied: list[str],
    ) -> Decimal:
        """Calculate Kelly-fraction based position size."""
        _ = request
        equity = portfolio_state.equity
        win_rate = Decimal(str(market_context.get("kelly_win_rate", "0.50")))
        win_loss_ratio = Decimal(str(market_context.get("kelly_win_loss_ratio", "1.5")))
        trade_count = int(market_context.get("historical_trade_count", 0))

        min_trades = int(
            market_context.get("kelly_min_trades", self.config.min_kelly_trades)
        )

        if win_loss_ratio > 0:
            kelly_fraction = win_rate - (Decimal("1.0") - win_rate) / win_loss_ratio
        else:
            kelly_fraction = Decimal("0.0")

        kelly_fraction = max(Decimal("0.0"), kelly_fraction)

        kelly_mult = Decimal(str(market_context.get("kelly_multiplier", "1.0")))
        kelly_fraction *= kelly_mult

        if trade_count < min_trades:
            constraints_applied.append("kelly_advisory_insufficient_evidence")
            return Decimal("0.0")

        constraints_applied.append("kelly_fraction_applied")

        enable_fractional_kelly = market_context.get(
            "enable_fractional_kelly", False
        ) or self.config.experimental_features.get("enable_fractional_kelly", False)

        if not enable_fractional_kelly:
            constraints_applied.append("kelly_advisory_only")
            if market_context.get("is_live", False) or self.config.allow_live_execution:
                return Decimal("0.0")

        tick_size = Decimal(str(specs["tick_size"]))
        tick_value = Decimal(str(specs["tick_value"]))
        contract_size = Decimal(str(specs["contract_size"]))
        conversion_rate = Decimal(str(specs["conversion_rate"]))

        if stop_distance_price > 0:
            risk_per_lot = (stop_distance_price / tick_size) * tick_value
            return (kelly_fraction * equity) / risk_per_lot
        return (kelly_fraction * equity) / (contract_size * conversion_rate)


class MilestoneSizer(BasePositionSizer):
    """Sizes positions based on strategy milestone targets."""

    def calculate(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
        specs: dict[str, Any],
        stop_distance_price: Decimal,
        constraints_applied: list[str],
    ) -> Decimal:
        """Calculate milestone-adjusted position size."""
        equity = portfolio_state.equity
        risk_pct = request.risk_percent or Decimal("0.02")
        max_risk_pct = getattr(self.config, "max_risk_per_trade", Decimal("0.02"))

        if risk_pct > max_risk_pct:
            risk_pct = max_risk_pct
            constraints_applied.append("max_risk_per_trade_cap")

        risk_amount = equity * Decimal(str(risk_pct))
        tick_size = Decimal(str(specs["tick_size"]))
        tick_value = Decimal(str(specs["tick_value"]))

        if stop_distance_price <= 0:
            return Decimal("0.0")

        risk_per_lot = (stop_distance_price / tick_size) * tick_value
        if risk_per_lot <= 0:
            return Decimal("0.0")

        raw_size = risk_amount / risk_per_lot

        milestone_mult = Decimal(str(market_context.get("milestone_multiplier", "1.0")))
        if milestone_mult != 1:
            raw_size *= milestone_mult
            constraints_applied.append("milestone_adjustment")

        return raw_size


class CorrelationAdjustedSizer(BasePositionSizer):
    """Sizes positions adjusted by the symbol's correlation.

    Adjusts raw size by correlation with the active portfolio.
    """

    def calculate(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
        specs: dict[str, Any],
        stop_distance_price: Decimal,
        constraints_applied: list[str],
    ) -> Decimal:
        """Calculate correlation-adjusted size."""
        equity = portfolio_state.equity
        risk_pct = request.risk_percent or Decimal("0.02")
        max_risk_pct = getattr(self.config, "max_risk_per_trade", Decimal("0.02"))

        if risk_pct > max_risk_pct:
            risk_pct = max_risk_pct
            constraints_applied.append("max_risk_per_trade_cap")

        risk_amount = equity * Decimal(str(risk_pct))
        tick_size = Decimal(str(specs["tick_size"]))
        tick_value = Decimal(str(specs["tick_value"]))

        if stop_distance_price <= 0:
            return Decimal("0.0")

        risk_per_lot = (stop_distance_price / tick_size) * tick_value
        if risk_per_lot <= 0:
            return Decimal("0.0")

        raw_size = risk_amount / risk_per_lot

        corr_coef = Decimal(str(market_context.get("portfolio_correlation", "0.0")))
        corr_mult = max(Decimal("0.1"), Decimal("1.0") - corr_coef * Decimal("0.5"))
        raw_size *= corr_mult
        constraints_applied.append("correlation_adjustment")

        return raw_size


def calculate_sigma_stop_distance(
    market_context: dict[str, Any],
    digits: int,
    multiplier: Decimal = Decimal("2.0"),
    atr_value: Decimal | None = None,
    constraints_applied: list[str] | None = None,
) -> tuple[Decimal, Decimal]:
    """Calculate price and pip stop distance using volatility (M1 sigma or ATR).

    Args:
        market_context: Current market parameters.
        digits: Symbol quote digits (decimal places).
        multiplier: Volatility multiplier factor.
        atr_value: Optional pre-calculated ATR value.
        constraints_applied: Optional list to append resolved constraints.

    Returns:
        tuple[Decimal, Decimal]: (stop_distance_price, stop_distance_pips)
    """
    m1_vol = market_context.get("m1_volatility")
    if m1_vol is not None:
        stop_distance_price = Decimal(str(m1_vol)) * multiplier
        if constraints_applied is not None:
            constraints_applied.append("m1_volatility_stop")
    elif atr_value is not None:
        stop_distance_price = Decimal(str(atr_value)) * multiplier
        if constraints_applied is not None:
            constraints_applied.append("atr_volatility_stop")
    else:
        raise ValueError("Missing volatility inputs.")

    pip_size = Decimal("0.01") if digits in {2, 3} else Decimal("0.0001")
    stop_distance_pips = stop_distance_price / pip_size
    return stop_distance_price, stop_distance_pips


class VolatilitySizingEngine:
    """Production sizing engine coordinating different position sizers."""

    def __init__(self, config: RiskConfig) -> None:
        """Initialize VolatilitySizingEngine with active configuration."""
        self.config = config
        self._sizers: dict[SizingMethod, BasePositionSizer] = {
            SizingMethod.FIXED_RISK: FixedRiskSizer(config),
            SizingMethod.FIXED_FRACTIONAL: FixedFractionalSizer(config),
            SizingMethod.VOLATILITY_ADJUSTED: VolatilityAdjustedSizer(config),
            SizingMethod.CORRELATION_ADJUSTED: CorrelationAdjustedSizer(config),
            SizingMethod.MILESTONE: MilestoneSizer(config),
            SizingMethod.KELLY: KellyReferenceSizer(config),
        }

    def calculate_initial_risk_amount(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
    ) -> Decimal:
        """Calculate the initial risk currency amount factoring in equity and rules."""
        _ = request
        equity = portfolio_state.equity
        if equity <= 0:
            return Decimal("0.0")

        max_risk_pct = getattr(self.config, "max_risk_per_trade", Decimal("0.02"))

        strategy_id = market_context.get("strategy_id")
        budget_cap = Decimal("1.0")
        if strategy_id and portfolio_state.strategy_allocations:
            alloc_pct = portfolio_state.strategy_allocations.get(strategy_id)
            if alloc_pct is not None:
                budget_cap = Decimal(str(alloc_pct))

        max_risk_amt = equity * max_risk_pct * budget_cap

        drawdown_pct = Decimal(str(market_context.get("drawdown_pct", "0.0")))
        dd_thresholds = getattr(self.config, "drawdown_stepdown_thresholds", [])
        dd_multipliers = getattr(self.config, "drawdown_stepdown_multipliers", [])
        dd_mult = Decimal("1.0")
        for th, mult in zip(dd_thresholds, dd_multipliers, strict=False):
            if drawdown_pct >= th:
                dd_mult = min(dd_mult, mult)

        max_risk_amt *= dd_mult

        return max_risk_amt

    def _resolve_stop_distance(
        self,
        method: SizingMethod,
        request: PositionSizingRequest,
        market_context: dict[str, Any],
        digits: int,
        constraints_applied: list[str],
    ) -> tuple[Decimal, Decimal]:
        """Resolve price and pip stop loss distance."""
        stop_price = Decimal("0.0")
        stop_pips = Decimal("0.0")

        if method == SizingMethod.VOLATILITY_ADJUSTED:
            try:
                multiplier = request.multiplier or Decimal("2.0")
                stop_price, stop_pips = calculate_sigma_stop_distance(
                    market_context=market_context,
                    digits=digits,
                    multiplier=multiplier,
                    atr_value=request.atr_value,
                    constraints_applied=constraints_applied,
                )
            except ValueError as e:
                raise ValueError("missing_volatility_inputs") from e
        elif request.stop_loss_pips is not None:
            stop_pips = Decimal(str(request.stop_loss_pips))
            pip_size = Decimal("0.01") if digits in {2, 3} else Decimal("0.0001")
            stop_price = stop_pips * pip_size

        return stop_price, stop_pips

    def _apply_kelly_cap(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
        specs: dict[str, Any],
        stop_distance_price: Decimal,
        raw_size: Decimal,
        constraints_applied: list[str],
    ) -> Decimal:
        """Calculate and apply Kelly reference upper bound cap."""
        kelly_sizer = self._sizers[SizingMethod.KELLY]
        try:
            kelly_max = kelly_sizer.calculate(
                request=request,
                portfolio_state=portfolio_state,
                market_context=market_context,
                specs=specs,
                stop_distance_price=stop_distance_price,
                constraints_applied=[],
            )
            if kelly_max > 0 and raw_size > kelly_max:
                constraints_applied.append("kelly_upper_bound_cap")
                return kelly_max
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Kelly upper bound cap calculation skipped: {e}")
        return raw_size

    def _apply_broker_limits(
        self,
        raw_size: Decimal,
        volume_step: Decimal,
        volume_min: Decimal,
        volume_max: Decimal,
        constraints_applied: list[str],
    ) -> Decimal:
        """Apply broker step size, min, and max limits."""
        steps = math.floor(raw_size / volume_step)
        volume = Decimal(str(steps)) * volume_step

        if volume > volume_max:
            volume = volume_max
            constraints_applied.append("volume_max_cap")
        elif volume < volume_min:
            logger.warning(
                f"Sizing rejected: calculated size {volume} is below "
                f"broker minimum {volume_min}."
            )
            constraints_applied.append("below_minimum_volume")
            return Decimal("0.0")

        return volume

    def calculate_size(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
    ) -> PositionSizingResult:
        """Calculate position size statelessly, applying limits and constraints."""
        symbol = request.symbol
        method_str = request.method or SizingMethod.VOLATILITY_ADJUSTED.value
        try:
            method = SizingMethod(method_str)
        except ValueError:
            method = SizingMethod.VOLATILITY_ADJUSTED

        constraints_applied: list[str] = []

        specs, err_constraint = _resolve_specs(symbol, market_context)
        if specs is None:
            return PositionSizingResult(
                calculated_volume=Decimal("0.0"),
                sizing_method=method.value,
                constraints_applied=[err_constraint],
                risk_contribution=Decimal("0.0"),
            )

        stop_price, stop_pips = Decimal("0.0"), Decimal("0.0")
        try:
            stop_price, stop_pips = self._resolve_stop_distance(
                method, request, market_context, specs["digits"], constraints_applied
            )
        except ValueError:
            return PositionSizingResult(
                calculated_volume=Decimal("0.0"),
                sizing_method=method.value,
                constraints_applied=["missing_volatility_inputs"],
                risk_contribution=Decimal("0.0"),
            )

        if (
            method
            in {
                SizingMethod.FIXED_RISK,
                SizingMethod.FIXED_FRACTIONAL,
                SizingMethod.VOLATILITY_ADJUSTED,
                SizingMethod.CORRELATION_ADJUSTED,
            }
            and stop_price <= 0
        ):
            logger.warning(f"Sizing rejected: invalid stop distance {stop_price}.")
            return PositionSizingResult(
                calculated_volume=Decimal("0.0"),
                sizing_method=method.value,
                constraints_applied=["invalid_stop_distance"],
                risk_contribution=Decimal("0.0"),
            )

        if portfolio_state.equity <= 0:
            logger.warning("Sizing rejected: portfolio equity is <= 0.")
            return PositionSizingResult(
                calculated_volume=Decimal("0.0"),
                sizing_method=method.value,
                constraints_applied=["zero_or_negative_equity"],
                risk_contribution=Decimal("0.0"),
            )

        raw_size = Decimal("0.0")
        if method == SizingMethod.FIXED_LOT:
            raw_size = Decimal(str(request.fixed_volume or Decimal("0.10")))
        else:
            sizer = self._sizers.get(method)
            if sizer is not None:
                raw_size = sizer.calculate(
                    request=request,
                    portfolio_state=portfolio_state,
                    market_context=market_context,
                    specs=specs,
                    stop_distance_price=stop_price,
                    constraints_applied=constraints_applied,
                )

        raw_size = _apply_reductions(raw_size, market_context, constraints_applied)
        raw_size = self._apply_kelly_cap(
            request,
            portfolio_state,
            market_context,
            specs,
            stop_price,
            raw_size,
            constraints_applied,
        )

        calculated_volume = self._apply_broker_limits(
            raw_size=raw_size,
            volume_step=specs["volume_step"],
            volume_min=specs["volume_min"],
            volume_max=specs["volume_max"],
            constraints_applied=constraints_applied,
        )

        if calculated_volume <= 0:
            return PositionSizingResult(
                calculated_volume=Decimal("0.0"),
                stop_distance_pips=stop_pips,
                sizing_method=method.value,
                constraints_applied=sorted(constraints_applied),
                risk_contribution=Decimal("0.0"),
            )

        risk_per_lot_calc = Decimal("0.0")
        if stop_price > 0:
            risk_per_lot_calc = (stop_price / specs["tick_size"]) * specs["tick_value"]
        else:
            risk_per_lot_calc = specs["contract_size"] * specs["conversion_rate"]

        risk_contribution = calculated_volume * risk_per_lot_calc

        return PositionSizingResult(
            calculated_volume=calculated_volume,
            stop_distance_pips=stop_pips,
            sizing_method=method.value,
            constraints_applied=sorted(constraints_applied),
            risk_contribution=risk_contribution,
        )


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
    engine = VolatilitySizingEngine(config)
    return engine.calculate_size(request, portfolio_state, market_context)
