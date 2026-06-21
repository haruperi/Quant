"""Simulator commission and fee models.

Exports deterministic fee calculations. No broker, network, or filesystem side
effects occur at import time.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.errors import ValidationError


@dataclass(frozen=True, slots=True)
class CommissionModel:
    """Calculate linear commission per traded lot.

    Args:
        amount_per_lot: Commission amount per lot.
        currency: Commission currency.
        model_id: Stable model identifier.

    Raises:
        ValidationError: If amount is negative or currency is empty.
    """

    amount_per_lot: float = 0.0
    currency: str = "USD"
    model_id: str = "per_lot_v1"

    def __post_init__(self) -> None:
        """Validate commission settings."""
        if self.amount_per_lot < 0:
            raise ValidationError("amount_per_lot must be non-negative.")
        if not self.currency.strip():
            raise ValidationError("currency must be non-empty.")

    def calculate(self, volume: float) -> float:
        """Calculate commission for filled volume.

        Args:
            volume: Filled volume in lots.

        Returns:
            float: Commission amount.

        Raises:
            ValidationError: If volume is negative.
        """
        if volume < 0:
            raise ValidationError("volume must be non-negative.")
        return round(volume * self.amount_per_lot, 10)
