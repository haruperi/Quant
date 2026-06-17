# ruff: noqa
"""Slippage models for simulation.

Implements fixed, relative, variable, volatility-based, and volume-dependent slippage,
ensuring execution prices worsen directionally based on order side (Buy/Sell).
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any

from app.utils.errors import SimulationError


class SlippageModel:
    """Evaluates slippage and calculates adjusted execution prices directionally."""

    def __init__(
        self, model_type: str = "NO_SLIPPAGE", fixed_points: int = 0, **kwargs: Any
    ) -> None:
        """Initialize slippage model."""
        self.model_type = model_type.upper()
        self.fixed_points = fixed_points
        self.min_points = kwargs.get("min_points", 0)
        self.max_points = kwargs.get("max_points", 5)
        self.global_seed = kwargs.get("global_seed", 42)
        self.max_slippage_points = kwargs.get("max_slippage_points")

        # Volatility-based parameters
        self.volatility_multiplier = Decimal(
            str(kwargs.get("volatility_multiplier", "0.5"))
        )

        # Volume-dependent parameters
        self.volume_multiplier = Decimal(str(kwargs.get("volume_multiplier", "0.1")))

        valid_models = {
            "NO_SLIPPAGE",
            "FIXED_SLIPPAGE",
            "VARIABLE_SLIPPAGE",
            "SPREAD_RELATIVE_SLIPPAGE",
            "VOLATILITY_SLIPPAGE",
            "VOLUME_SLIPPAGE",
        }
        if self.model_type not in valid_models:
            msg = f"Unsupported slippage model: {model_type}"
            raise SimulationError(
                msg,
                code="SIM_UNSUPPORTED_SLIPPAGE_MODEL",
            )

    def calculate_slippage_points(
        self,
        direction: str,  # "BUY" or "SELL"
        spread_points: int | None = None,
        bar_time: str | None = None,
        volatility: Decimal | None = None,
        volume: Decimal | None = None,
    ) -> int:
        """Calculate slippage points based on the active model type."""
        if self.model_type == "NO_SLIPPAGE":
            return 0

        points = 0
        if self.model_type == "FIXED_SLIPPAGE":
            points = self.fixed_points

        elif self.model_type == "VARIABLE_SLIPPAGE":
            # Generate deterministic variable slippage using hash
            seed_str = f"slippage_{self.global_seed}_{bar_time or ''}"
            h = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
            diff = self.max_points - self.min_points
            points = self.min_points + (h % (diff + 1))

        elif self.model_type == "SPREAD_RELATIVE_SLIPPAGE":
            # Slippage is a percentage/fraction of spread points (e.g. 50% of spread)
            actual_spread = spread_points if spread_points is not None else 10
            # Default to half of spread points, at least 1
            points = max(1, actual_spread // 2)

        elif self.model_type == "VOLATILITY_SLIPPAGE":
            # Points scale with volatility
            actual_vol = volatility if volatility is not None else Decimal("0.0")
            points = int(actual_vol * self.volatility_multiplier)
            points = max(self.min_points, points)

        elif self.model_type == "VOLUME_SLIPPAGE":
            # Points scale with volume
            actual_vol = volume if volume is not None else Decimal("0.0")
            points = int(actual_vol * self.volume_multiplier)
            points = max(self.min_points, points)

        # Apply slippage cap if configured
        if self.max_slippage_points is not None:
            points = min(points, self.max_slippage_points)

        return max(0, points)

    def calculate_price(
        self,
        base_price: Decimal,
        direction: str,
        point: Decimal,
        spread_points: int | None = None,
        bar_time: str | None = None,
        volatility: Decimal | None = None,
        volume: Decimal | None = None,
    ) -> Decimal:
        """Worsen the execution price directionally based on side and calculated slippage."""
        if base_price <= 0:
            raise SimulationError(
                "Base price must be positive.", code="SIM_INVALID_PRICE"
            )

        slippage_points = self.calculate_slippage_points(
            direction=direction.upper(),
            spread_points=spread_points,
            bar_time=bar_time,
            volatility=volatility,
            volume=volume,
        )

        slippage_value = Decimal(str(slippage_points)) * point

        # Buy: price increases (worse)
        # Sell: price decreases (worse)
        if direction.upper() in {"BUY", "BUY_LIMIT", "BUY_STOP", "BUY_STOP_LIMIT"}:
            return base_price + slippage_value
        if direction.upper() in {"SELL", "SELL_LIMIT", "SELL_STOP", "SELL_STOP_LIMIT"}:
            return base_price - slippage_value
        msg = f"Invalid order direction: {direction}"
        raise SimulationError(msg, code="SIM_INVALID_CONFIG")
