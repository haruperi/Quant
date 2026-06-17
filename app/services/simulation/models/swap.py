# ruff: noqa
"""Swap (overnight rollover charge) models for simulation.

Implements overnight rolls based on points, money, percent, and interest,
supporting triple-swap calculations (defaulting to Wednesday) and currency conversions.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.utils.errors import SimulationError


class SwapModel:
    """Calculates overnight swap charges or credits for open positions."""

    def __init__(self, model_type: str = "NO_SWAP", **kwargs: Any) -> None:
        """Initialize swap model parameters."""
        self.model_type = model_type.upper()
        self.global_seed = kwargs.get("global_seed", 42)

        valid_models = {
            "NO_SWAP",
            "NATIVE_SWAP",
        }
        if self.model_type not in valid_models:
            msg = f"Unsupported swap model: {model_type}"
            raise SimulationError(
                msg,
                code="SIM_UNSUPPORTED_SWAP_MODEL",
            )

    def calculate_swap(
        self,
        volume: Decimal,
        direction: str,  # "BUY" or "SELL"
        swap_long: Decimal,
        swap_short: Decimal,
        swap_mode: str,  # "points", "money", "percent", "interest"
        point: Decimal,
        contract_size: Decimal,
        open_price: Decimal,
        is_triple_day: bool = False,
        fx_rate: Decimal = Decimal("1.0"),
    ) -> Decimal:
        """Calculate swap charge/credit for a single overnight rollover.

        Args:
            volume: Position volume (lots).
            direction: Position direction ("BUY" or "SELL").
            swap_long: Long swap rate.
            swap_short: Short swap rate.
            swap_mode: Swap mode ("points", "money", "percent", "interest").
            point: Instrument point size.
            contract_size: Instrument contract size.
            open_price: Position open price.
            is_triple_day: Whether this is the triple-swap day.
            fx_rate: Conversion rate from profit currency to account currency.
        """
        if self.model_type == "NO_SWAP":
            return Decimal("0.0")

        # Determine rate based on side
        side = direction.upper()
        if side in {"BUY", "BUY_LIMIT", "BUY_STOP", "BUY_STOP_LIMIT"}:
            rate = swap_long
        elif side in {"SELL", "SELL_LIMIT", "SELL_STOP", "SELL_STOP_LIMIT"}:
            rate = swap_short
        else:
            msg = f"Invalid position direction: {direction}"
            raise SimulationError(msg, code="SIM_INVALID_CONFIG")

        multiplier = Decimal("3.0") if is_triple_day else Decimal("1.0")

        raw_swap = Decimal("0.0")
        mode = swap_mode.lower()

        if mode == "points":
            # Swap = Volume * contract_size * rate * point
            raw_swap = volume * contract_size * rate * point

        elif mode == "money":
            # Swap = Volume * rate
            raw_swap = volume * rate

        elif mode in {"percent", "interest"}:
            # Swap = Volume * contract_size * open_price * (rate / 100) / 360
            raw_swap = (
                volume * contract_size * open_price * (rate / Decimal("100.0"))
            ) / Decimal("360.0")

        else:
            msg = f"Unsupported swap mode in symbol specification: {swap_mode}"
            raise SimulationError(
                msg,
                code="SIM_UNSUPPORTED_SWAP_MODEL",
            )

        # Convert to account currency and apply multiplier
        swap_in_account = raw_swap * multiplier * fx_rate

        return swap_in_account.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
