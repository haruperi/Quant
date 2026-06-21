"""Simulator margin models.

Exports deterministic FX-style margin calculations. The module is side-effect
free and does not query live accounts.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.errors import ValidationError


@dataclass(frozen=True, slots=True)
class MarginModel:
    """Calculate notional margin for leveraged instruments.

    Args:
        leverage: Account leverage multiplier.
        model_id: Stable model identifier.

    Raises:
        ValidationError: If leverage is invalid.
    """

    leverage: int = 100
    model_id: str = "fx_notional_v1"

    def __post_init__(self) -> None:
        """Validate margin settings."""
        if self.leverage <= 0:
            raise ValidationError("leverage must be greater than zero.")

    def calculate(
        self,
        *,
        contract_size: float,
        volume: float,
        price: float,
    ) -> float:
        """Calculate required margin.

        Args:
            contract_size: Units per lot.
            volume: Trade volume in lots.
            price: Execution or mark price.

        Returns:
            float: Required margin.

        Raises:
            ValidationError: If inputs are invalid.
        """
        if contract_size <= 0 or volume < 0 or price <= 0:
            raise ValidationError("contract_size, volume, and price must be valid.")
        return round(contract_size * volume * price / self.leverage, 10)
