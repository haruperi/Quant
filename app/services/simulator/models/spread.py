"""Simulator spread models.

Exports deterministic spread configuration and application helpers. The module
has no import-time side effects.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.simulator.models.tick import SimulatorTick
from app.utils.errors import ValidationError


@dataclass(frozen=True, slots=True)
class FixedSpreadModel:
    """Apply a deterministic fixed spread around a reference mid price.

    Args:
        spread_points: Spread width in points.
        point: Symbol point size.
        model_id: Stable model identifier.

    Raises:
        ValidationError: If spread or point values are invalid.
    """

    spread_points: float = 10.0
    point: float = 0.00001
    model_id: str = "fixed_points_v1"

    def __post_init__(self) -> None:
        """Validate fixed spread settings."""
        if self.spread_points < 0:
            raise ValidationError(
                "spread_points must be non-negative.",
                code="SIM_DATA_NEGATIVE_SPREAD",
            )
        if self.point <= 0:
            raise ValidationError("point must be greater than zero.")

    def build_tick(
        self,
        *,
        timestamp: str,
        symbol: str,
        mid_price: float,
        volume: float | None = None,
        source: str = "simulator",
    ) -> SimulatorTick:
        """Build a bid/ask tick from a mid price.

        Args:
            timestamp: UTC ISO timestamp.
            symbol: Symbol name.
            mid_price: Reference mid price.
            volume: Optional volume proxy.
            source: Source label.

        Returns:
            SimulatorTick: Deterministic tick with spread applied.

        Raises:
            ValidationError: If mid price is invalid.
        """
        if mid_price <= 0:
            raise ValidationError("mid_price must be greater than zero.")
        half_spread = self.spread_points * self.point / 2
        return SimulatorTick(
            timestamp=timestamp,
            symbol=symbol,
            bid=round(mid_price - half_spread, 10),
            ask=round(mid_price + half_spread, 10),
            last=mid_price,
            volume=volume,
            spread_points=self.spread_points,
            source=source,
        )


@dataclass(frozen=True, slots=True)
class VariableSpreadModel:
    """Apply variable spread generated using seeded randomness.

    Args:
        min_spread_points: Minimum spread width in points.
        max_spread_points: Maximum spread width in points.
        point: Symbol point size.
        seed: Random generator seed.
        model_id: Stable model identifier.
    """

    min_spread_points: float = 5.0
    max_spread_points: float = 30.0
    point: float = 0.00001
    seed: int = 42
    model_id: str = "variable_points_v1"

    def __post_init__(self) -> None:
        """Validate variable spread settings."""
        if (
            self.min_spread_points < 0
            or self.max_spread_points < self.min_spread_points
        ):
            raise ValidationError(
                "spread_points bounds must be valid and non-negative."
            )
        if self.point <= 0:
            raise ValidationError("point must be greater than zero.")

    def build_tick(
        self,
        *,
        timestamp: str,
        symbol: str,
        mid_price: float,
        volume: float | None = None,
        source: str = "simulator",
        tick_index: int = 0,
    ) -> SimulatorTick:
        """Build a bid/ask tick from a mid price with variable spread.

        Args:
            timestamp: UTC ISO timestamp.
            symbol: Symbol name.
            mid_price: Reference mid price.
            volume: Optional volume proxy.
            source: Source label.
            tick_index: Incremental index for seeded deterministic randomness.

        Returns:
            SimulatorTick: Deterministic tick with variable spread applied.

        Raises:
            ValidationError: If mid price is invalid.
        """
        import random

        if mid_price <= 0:
            raise ValidationError("mid_price must be greater than zero.")
        rng = random.Random(self.seed + tick_index)
        spread_points = rng.uniform(self.min_spread_points, self.max_spread_points)
        half_spread = spread_points * self.point / 2
        return SimulatorTick(
            timestamp=timestamp,
            symbol=symbol,
            bid=round(mid_price - half_spread, 10),
            ask=round(mid_price + half_spread, 10),
            last=mid_price,
            volume=volume,
            spread_points=round(spread_points, 4),
            source=source,
        )
