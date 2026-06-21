"""Simulator swap models.

Exports deterministic daily swap calculations for simulator accounting. The
module has no import-time side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.utils.errors import ValidationError

SwapSide = Literal["buy", "sell"]


@dataclass(frozen=True, slots=True)
class SwapModel:
    """Calculate simple daily swap by side.

    Args:
        long_per_lot_per_day: Long-side daily swap per lot.
        short_per_lot_per_day: Short-side daily swap per lot.
        model_id: Stable model identifier.
    """

    long_per_lot_per_day: float = 0.0
    short_per_lot_per_day: float = 0.0
    model_id: str = "daily_points_v1"

    def calculate(self, *, side: SwapSide, volume: float, days_held: int) -> float:
        """Calculate swap amount.

        Args:
            side: Position side.
            volume: Position volume.
            days_held: Full days held.

        Returns:
            float: Swap amount.

        Raises:
            ValidationError: If side, volume, or holding period are invalid.
        """
        if side not in {"buy", "sell"}:
            raise ValidationError("side must be buy or sell.")
        if volume < 0 or days_held < 0:
            raise ValidationError("volume and days_held must be non-negative.")
        rate = (
            self.long_per_lot_per_day if side == "buy" else self.short_per_lot_per_day
        )
        return round(rate * volume * days_held, 10)
