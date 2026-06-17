# ruff: noqa
"""Spread models for simulation.

Implements native, fixed, and variable spread structures, checks for negative spreads,
and supports deterministic randomized variable spreads.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any

from app.utils.errors import SimulationError


class SpreadModel:
    """Evaluates spreads and calculates Ask/Bid relationships deterministically."""

    def __init__(
        self, model_type: str = "NATIVE_SPREAD", fixed_points: int = 15, **kwargs: Any
    ) -> None:
        """Initialize spread model."""
        self.model_type = model_type.upper()
        self.fixed_points = fixed_points
        self.min_points = int(kwargs.get("min_points", 10))
        self.max_points = int(kwargs.get("max_points", 30))
        self.global_seed = kwargs.get("global_seed", 42)

        if self.model_type not in {"NATIVE_SPREAD", "FIXED_SPREAD", "VARIABLE_SPREAD"}:
            msg = f"Unsupported spread model: {model_type}"
            raise SimulationError(
                msg,
                code="SIM_UNSUPPORTED_SPREAD_MODEL",
            )

    def calculate_ask(
        self,
        bid: Decimal,
        point: Decimal,
        record_spread_points: int | None = None,
        bar_time: str | None = None,
    ) -> Decimal:
        """Return ask price based on current bid, point, and optional native spread points or time seed."""
        if bid < 0:
            raise SimulationError(
                "Bid price cannot be negative.", code="SIM_INVALID_PRICE"
            )

        spread_points = self.get_spread_points(record_spread_points, bar_time)
        if spread_points < 0:
            msg = f"Negative spread detected: {spread_points} points."
            raise SimulationError(
                msg,
                code="SIM_DATA_NEGATIVE_SPREAD",
            )

        return bid + (Decimal(str(spread_points)) * point)

    def get_spread_points(
        self, record_spread_points: int | None = None, bar_time: str | None = None
    ) -> int:
        """Calculate and return the spread points for the active model type."""
        if self.model_type == "FIXED_SPREAD":
            return self.fixed_points

        if self.model_type == "VARIABLE_SPREAD":
            # Generate deterministic variable spread using hash of timestamp and global seed
            seed_str = f"spread_{self.global_seed}_{bar_time or ''}"
            h = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
            diff = self.max_points - self.min_points
            return self.min_points + (h % (diff + 1))

        # NATIVE_SPREAD: Use recorded spread if available, fallback to fixed
        if record_spread_points is None:
            return self.fixed_points
        return record_spread_points
