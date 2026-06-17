# ruff: noqa
"""Commission and transaction fee models for simulation.

Implements fixed, per-lot, per-trade, percent-notional, tiered, and maker/taker commissions,
including min/max boundary constraints and account currency conversions.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.utils.errors import SimulationError


class FeeModel:
    """Calculates broker commissions and transaction fees for executed fills."""

    def __init__(self, model_type: str = "NO_COMMISSION", **kwargs: Any) -> None:
        """Initialize fee model parameters."""
        self.model_type = model_type.upper()
        self.fixed_commission = Decimal(str(kwargs.get("fixed_commission", "0.0")))
        self.per_lot_commission = Decimal(
            str(kwargs.get("per_lot_commission", "0.0"))
        )  # per standard lot (usually 100,000 units)
        self.pct_notional = Decimal(
            str(kwargs.get("pct_notional", "0.0"))
        )  # percentage of notional value (e.g. 0.0005 for 0.05%)
        self.min_commission = kwargs.get("min_commission")
        self.max_commission = kwargs.get("max_commission")

        # Maker / Taker rates
        self.maker_rate = Decimal(str(kwargs.get("maker_rate", "0.0")))
        self.taker_rate = Decimal(str(kwargs.get("taker_rate", "0.0")))

        # Tiered pricing thresholds e.g. [(limit_vol, rate)]
        self.tiers = kwargs.get("tiers", [])

        valid_models = {
            "NO_COMMISSION",
            "FIXED_COMMISSION",
            "PER_LOT_COMMISSION",
            "PER_TRADE_COMMISSION",
            "PERCENT_NOTIONAL_COMMISSION",
            "TIERED_COMMISSION",
            "MAKER_TAKER_COMMISSION",
        }
        if self.model_type not in valid_models:
            msg = f"Unsupported commission model: {model_type}"
            raise SimulationError(
                msg,
                code="SIM_UNSUPPORTED_COMMISSION_MODEL",
            )

    def calculate_commission(
        self,
        filled_volume: Decimal,
        fill_price: Decimal,
        contract_size: Decimal,
        is_maker: bool = False,
        fx_rate: Decimal = Decimal("1.0"),
    ) -> Decimal:
        """Calculate commission in account currency for an executed deal.

        Args:
            filled_volume: Volume of the fill (in standard lots or units).
            fill_price: Price of the fill.
            contract_size: Unit contract size per lot (e.g. 100,000 for FX).
            is_maker: Whether the order was maker (passive) or taker (aggressive).
            fx_rate: Conversion rate from commission currency to account currency.
        """
        if filled_volume <= 0:
            return Decimal("0.0")

        # Notional value calculation
        notional_val = filled_volume * contract_size * fill_price

        raw_comm = Decimal("0.0")

        if self.model_type == "NO_COMMISSION":
            return Decimal("0.0")

        if self.model_type in {"FIXED_COMMISSION", "PER_TRADE_COMMISSION"}:
            raw_comm = self.fixed_commission

        elif self.model_type == "PER_LOT_COMMISSION":
            # filled_volume is typically in standard lots
            raw_comm = filled_volume * self.per_lot_commission

        elif self.model_type == "PERCENT_NOTIONAL_COMMISSION":
            raw_comm = notional_val * self.pct_notional

        elif self.model_type == "MAKER_TAKER_COMMISSION":
            rate = self.maker_rate if is_maker else self.taker_rate
            raw_comm = notional_val * rate

        elif self.model_type == "TIERED_COMMISSION":
            # Apply tiered rates based on filled_volume
            selected_rate = self.pct_notional
            for volume_limit, rate in sorted(self.tiers, key=lambda x: x[0]):
                if filled_volume <= Decimal(str(volume_limit)):
                    selected_rate = Decimal(str(rate))
                    break
            raw_comm = notional_val * selected_rate

        # Enforce limits in commission currency if defined
        if self.min_commission is not None:
            raw_comm = max(raw_comm, Decimal(str(self.min_commission)))
        if self.max_commission is not None:
            raw_comm = min(raw_comm, Decimal(str(self.max_commission)))

        # Convert to account currency
        comm_in_account_currency = raw_comm * fx_rate

        # Round to standard 2 decimal places (or base precision)
        return comm_in_account_currency.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
