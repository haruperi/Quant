"""Simulator liquidity models.

Exports bounded fill-volume models used before slippage is applied. The module
has no side effects on import.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.errors import ValidationError


@dataclass(frozen=True, slots=True)
class LiquidityFill:
    """Fillability result for a requested order volume.

    Args:
        requested_volume: Requested volume.
        filled_volume: Fillable volume.
        remainder_volume: Unfilled remainder.
        diagnostic_code: Optional non-fatal diagnostic.
    """

    requested_volume: float
    filled_volume: float
    remainder_volume: float
    diagnostic_code: str | None = None


@dataclass(frozen=True, slots=True)
class FixedLiquidityModel:
    """Cap fills at a configured maximum volume per tick.

    Args:
        max_volume_per_tick: Maximum fill volume available per tick.
        model_id: Stable model identifier.

    Raises:
        ValidationError: If the volume limit is invalid.
    """

    max_volume_per_tick: float = 100.0
    model_id: str = "fixed_volume_v1"

    def __post_init__(self) -> None:
        """Validate liquidity settings."""
        if self.max_volume_per_tick <= 0:
            raise ValidationError("max_volume_per_tick must be greater than zero.")

    def fill(
        self, requested_volume: float, *, time_in_force: str = "GTC"
    ) -> LiquidityFill:
        """Calculate fillable volume.

        Args:
            requested_volume: Requested order volume.
            time_in_force: Time-in-force policy.

        Returns:
            LiquidityFill: Filled and remainder volume details.

        Raises:
            ValidationError: If requested volume is invalid.
        """
        if requested_volume <= 0:
            raise ValidationError(
                "requested_volume must be greater than zero.",
                code="SIM_INVALID_VOLUME",
            )
        filled = min(requested_volume, self.max_volume_per_tick)
        remainder = round(requested_volume - filled, 10)
        diagnostic = (
            "SIM_IOC_REMAINDER_CANCELLED"
            if time_in_force == "IOC" and remainder > 0
            else None
        )
        return LiquidityFill(requested_volume, filled, remainder, diagnostic)


@dataclass(frozen=True, slots=True)
class OrderBookLevel:
    """Single level in an order-book depth queue.

    Args:
        price: Level price.
        volume: Available volume at level.
    """

    price: float
    volume: float

    def __post_init__(self) -> None:
        """Validate level parameters."""
        if self.price <= 0 or self.volume < 0:
            raise ValidationError("order book price and volume must be valid.")


@dataclass(frozen=True, slots=True)
class OrderBookLiquidityModel:
    """Order-book depth-walking model for simulating VWAP fills.

    Args:
        bids: Bid levels representing bids depth.
        asks: Ask levels representing asks depth.
        model_id: Stable model identifier.
    """

    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    model_id: str = "order_book_v1"

    def __post_init__(self) -> None:
        """Validate order book levels."""
        if not self.bids and not self.asks:
            raise ValidationError("order book must contain at least one level.")

    def fill(
        self,
        requested_volume: float,
        *,
        side: str,
        time_in_force: str = "GTC",
    ) -> LiquidityFill:
        """Calculate fillable volume by depth-walking the book.

        Args:
            requested_volume: Requested order volume.
            side: Side to check ('buy' walks asks, 'sell' walks bids).
            time_in_force: Time-in-force policy.

        Returns:
            LiquidityFill: Filled and remainder volume details.

        Raises:
            ValidationError: If volume is invalid or side is unknown.
        """
        if requested_volume <= 0:
            raise ValidationError(
                "requested_volume must be greater than zero.",
                code="SIM_INVALID_VOLUME",
            )
        if side not in {"buy", "sell"}:
            raise ValidationError("side must be buy or sell.")

        levels = self.asks if side == "buy" else self.bids
        filled = 0.0
        for lvl in levels:
            level_filled = min(requested_volume - filled, lvl.volume)
            filled += level_filled
            if filled >= requested_volume:
                break

        filled = round(filled, 10)
        remainder = round(requested_volume - filled, 10)
        diagnostic = (
            "SIM_IOC_REMAINDER_CANCELLED"
            if time_in_force == "IOC" and remainder > 0
            else None
        )
        return LiquidityFill(requested_volume, filled, remainder, diagnostic)
