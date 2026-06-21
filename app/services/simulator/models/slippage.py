"""Simulator slippage models.

Exports deterministic slippage calculations. The module has no import-time side
effects and does not access brokers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.utils.errors import ValidationError

OrderSide = Literal["buy", "sell"]


@dataclass(frozen=True, slots=True)
class SlippageResult:
    """Result of a slippage calculation.

    Args:
        expected_price: Requested or reference price.
        executable_price: Raw executable bid or ask.
        slippage_points: Applied slippage points.
        final_price: Final fill price.
    """

    expected_price: float
    executable_price: float
    slippage_points: float
    final_price: float


@dataclass(frozen=True, slots=True)
class FixedSlippageModel:
    """Apply deterministic fixed slippage only to filled quantity.

    Args:
        slippage_points: Points applied in adverse direction.
        point: Symbol point size.
        model_id: Stable model identifier.

    Raises:
        ValidationError: If settings are invalid.
    """

    slippage_points: float = 0.0
    point: float = 0.00001
    model_id: str = "fixed_points_v1"

    def __post_init__(self) -> None:
        """Validate slippage settings."""
        if self.slippage_points < 0 or self.point <= 0:
            raise ValidationError("slippage_points and point must be valid.")

    def apply(
        self,
        *,
        side: OrderSide,
        expected_price: float,
        executable_price: float,
        filled_volume: float,
    ) -> SlippageResult:
        """Calculate slippage for an executed fill.

        Args:
            side: Buy or sell direction.
            expected_price: Requested or reference price.
            executable_price: Bid or ask before slippage.
            filled_volume: Filled volume; zero volume receives no slippage.

        Returns:
            SlippageResult: Calculated final price and point impact.

        Raises:
            ValidationError: If prices, side, or volume are invalid.
        """
        if side not in {"buy", "sell"}:
            raise ValidationError("side must be buy or sell.")
        if expected_price <= 0 or executable_price <= 0 or filled_volume < 0:
            raise ValidationError("price and volume inputs are invalid.")
        applied_points = self.slippage_points if filled_volume > 0 else 0.0
        delta = applied_points * self.point
        final_price = (
            executable_price + delta if side == "buy" else executable_price - delta
        )
        return SlippageResult(
            expected_price=expected_price,
            executable_price=executable_price,
            slippage_points=applied_points,
            final_price=round(final_price, 10),
        )


@dataclass(frozen=True, slots=True)
class VolatilitySlippageModel:
    """Apply volatility-proportional slippage.

    Args:
        base_slippage_points: Base slippage floor.
        volatility_multiplier: Scaler for rolling volatility points.
        point: Symbol point size.
        model_id: Stable model identifier.
    """

    base_slippage_points: float = 2.0
    volatility_multiplier: float = 1.5
    point: float = 0.00001
    model_id: str = "volatility_based_v1"

    def __post_init__(self) -> None:
        """Validate volatility slippage settings."""
        if self.base_slippage_points < 0 or self.volatility_multiplier < 0:
            raise ValidationError("slippage metrics must be non-negative.")
        if self.point <= 0:
            raise ValidationError("point size must be positive.")

    def apply(
        self,
        *,
        side: OrderSide,
        expected_price: float,
        executable_price: float,
        filled_volume: float,
        volatility: float = 0.0001,
    ) -> SlippageResult:
        """Calculate volatility-adjusted slippage for an executed fill."""
        if side not in {"buy", "sell"}:
            raise ValidationError("side must be buy or sell.")
        if expected_price <= 0 or executable_price <= 0 or filled_volume < 0:
            raise ValidationError("price and volume inputs are invalid.")
        if volatility < 0:
            raise ValidationError("volatility must be non-negative.")
        applied_points = (
            (
                self.base_slippage_points
                + self.volatility_multiplier * (volatility / self.point)
            )
            if filled_volume > 0
            else 0.0
        )
        delta = applied_points * self.point
        final_price = (
            executable_price + delta if side == "buy" else executable_price - delta
        )
        return SlippageResult(
            expected_price=expected_price,
            executable_price=executable_price,
            slippage_points=applied_points,
            final_price=round(final_price, 10),
        )


@dataclass(frozen=True, slots=True)
class VolumeSlippageModel:
    """Apply volume-dependent slippage.

    Args:
        base_slippage_points: Base slippage floor.
        volume_multiplier: Scaler per lot.
        point: Symbol point size.
        model_id: Stable model identifier.
    """

    base_slippage_points: float = 1.0
    volume_multiplier: float = 0.5
    point: float = 0.00001
    model_id: str = "volume_based_v1"

    def __post_init__(self) -> None:
        """Validate volume slippage settings."""
        if self.base_slippage_points < 0 or self.volume_multiplier < 0:
            raise ValidationError("slippage metrics must be non-negative.")
        if self.point <= 0:
            raise ValidationError("point size must be positive.")

    def apply(
        self,
        *,
        side: OrderSide,
        expected_price: float,
        executable_price: float,
        filled_volume: float,
    ) -> SlippageResult:
        """Calculate volume-dependent slippage for an executed fill."""
        if side not in {"buy", "sell"}:
            raise ValidationError("side must be buy or sell.")
        if expected_price <= 0 or executable_price <= 0 or filled_volume < 0:
            raise ValidationError("price and volume inputs are invalid.")
        applied_points = (
            (self.base_slippage_points + self.volume_multiplier * filled_volume)
            if filled_volume > 0
            else 0.0
        )
        delta = applied_points * self.point
        final_price = (
            executable_price + delta if side == "buy" else executable_price - delta
        )
        return SlippageResult(
            expected_price=expected_price,
            executable_price=executable_price,
            slippage_points=applied_points,
            final_price=round(final_price, 10),
        )
