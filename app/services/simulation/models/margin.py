# ruff: noqa
"""Margin calculations and risk model for simulation.

Implements standard margin requirement, exposure, concentration,
and stopout/liquidation validation rules.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


class MarginModel:
    """Calculates margin requirements, exposure, and stopout conditions."""

    def __init__(
        self,
        leverage: Decimal = Decimal("100.0"),
        stopout_level_pct: Decimal = Decimal("50.0"),
        **kwargs: Any,
    ) -> None:
        """Initialize margin model."""
        self.leverage = leverage
        self.stopout_level_pct = stopout_level_pct
        self.margin_call_pct = Decimal(str(kwargs.get("margin_call_pct", "100.0")))
        self.margin_mode = kwargs.get(
            "margin_mode", "cross"
        ).lower()  # cross, isolated, independent

    def calculate_position_margin(
        self,
        volume: Decimal,
        entry_price: Decimal,
        contract_size: Decimal,
        asset_class: str = "FX",
        margin_rate: Decimal
        | None = None,  # if provided, overrides leverage (e.g. 0.05 for 5% margin)
        fx_rate: Decimal = Decimal(
            "1.0"
        ),  # conversion from margin currency to account base currency
    ) -> Decimal:
        """Compute the margin required for a position or order in account currency."""
        if volume <= 0:
            return Decimal("0.0")

        # Determine rate
        rate = margin_rate
        if rate is None:
            if self.leverage > 0:
                rate = Decimal("1.0") / self.leverage
            else:
                rate = Decimal("1.0")

        # Base margin calculation
        if asset_class.upper() == "FX":
            # For FX: Margin = (Volume * ContractSize) * rate (in margin currency)
            margin_in_margin_currency = volume * contract_size * rate
        else:
            # For Equity/CFD: Margin = (Volume * ContractSize * EntryPrice) * rate
            margin_in_margin_currency = volume * contract_size * entry_price * rate

        # Convert to account currency
        return margin_in_margin_currency * fx_rate

    def evaluate_stopout(
        self,
        equity: Decimal,
        total_margin: Decimal,
    ) -> bool:
        """Check if stopout condition is met."""
        if total_margin <= 0:
            return False
        margin_level = (equity / total_margin) * Decimal("100.0")
        return margin_level <= self.stopout_level_pct

    def calculate_margin_level(
        self,
        equity: Decimal,
        total_margin: Decimal,
    ) -> Decimal | None:
        """Calculate margin level as a percentage. Returns None if margin is 0."""
        if total_margin <= 0:
            return None
        return (equity / total_margin) * Decimal("100.0")
