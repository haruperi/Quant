# ruff: noqa
"""Liquidity models for simulation.

Implements infinite, volume-limit, and order-book liquidity verification,
supporting partial fill calculations and order-book level walking.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, NamedTuple

from app.utils.errors import SimulationError


class BookLevel(NamedTuple):
    """Represents a single price level in an order book depth of market."""

    price: Decimal
    volume: Decimal


class LiquidityModel:
    """Evaluates market liquidity and computes filled/unfilled volume and VWAP execution prices."""

    def __init__(self, model_type: str = "INFINITE_LIQUIDITY", **kwargs: Any) -> None:
        """Initialize liquidity model."""
        self.model_type = model_type.upper()
        self.max_volume_pct = Decimal(
            str(kwargs.get("max_volume_pct", "1.0"))
        )  # Default 100% of tick/bar volume
        self.min_fill_volume = Decimal(str(kwargs.get("min_fill_volume", "0.01")))

        valid_models = {
            "INFINITE_LIQUIDITY",
            "VOLUME_LIMIT_LIQUIDITY",
            "ORDER_BOOK_LIQUIDITY",
        }
        if self.model_type not in valid_models:
            msg = f"Unsupported liquidity model: {model_type}"
            raise SimulationError(
                msg,
                code="SIM_UNSUPPORTED_LIQUIDITY_MODEL",
            )

    def evaluate_fill(
        self,
        requested_volume: Decimal,
        direction: str,
        available_market_volume: Decimal | None = None,
        order_book_depth: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Evaluate how much of requested volume can be filled based on liquidity.

        Returns a dictionary with:
            filled_volume: Decimal
            unfilled_volume: Decimal
            vwap_price: Decimal | None (only computed if order-book is walked)
            status: str ("success", "partial", "rejected")
        """
        if requested_volume < self.min_fill_volume:
            msg = f"Requested volume {requested_volume} is below minimum fill volume {self.min_fill_volume}."
            raise SimulationError(
                msg,
                code="SIM_VOLUME_BELOW_MIN",
            )

        if self.model_type == "INFINITE_LIQUIDITY":
            return {
                "filled_volume": requested_volume,
                "unfilled_volume": Decimal("0.0"),
                "vwap_price": None,
                "status": "success",
            }

        if self.model_type == "VOLUME_LIMIT_LIQUIDITY":
            market_vol = (
                available_market_volume
                if available_market_volume is not None
                else Decimal("1000000.0")
            )
            allowed_market_vol = market_vol * self.max_volume_pct
            filled = min(requested_volume, allowed_market_vol)

            if filled < self.min_fill_volume:
                return {
                    "filled_volume": Decimal("0.0"),
                    "unfilled_volume": requested_volume,
                    "vwap_price": None,
                    "status": "rejected",
                }

            status = "success" if filled == requested_volume else "partial"
            return {
                "filled_volume": filled,
                "unfilled_volume": requested_volume - filled,
                "vwap_price": None,
                "status": status,
            }

        # ORDER_BOOK_LIQUIDITY: walk order book levels
        if not order_book_depth:
            # Fallback to volume limit if book depth is missing
            raise SimulationError(
                "Order book depth data required for ORDER_BOOK_LIQUIDITY model.",
                code="SIM_LIQUIDITY_UNAVAILABLE",
            )

        # Walk the book to fill volume
        # order_book_depth should be list of {"price": float/Decimal, "volume": float/Decimal} sorted by price
        filled_qty = Decimal("0.0")
        total_cost = Decimal("0.0")
        remaining = requested_volume

        for level in order_book_depth:
            price = Decimal(str(level["price"]))
            vol = Decimal(str(level["volume"]))
            take = min(remaining, vol)

            total_cost += take * price
            filled_qty += take
            remaining -= take

            if remaining <= 0:
                break

        if filled_qty < self.min_fill_volume:
            return {
                "filled_volume": Decimal("0.0"),
                "unfilled_volume": requested_volume,
                "vwap_price": None,
                "status": "rejected",
            }

        vwap = total_cost / filled_qty if filled_qty > 0 else None
        status = "success" if remaining <= 0 else "partial"

        return {
            "filled_volume": filled_qty,
            "unfilled_volume": remaining,
            "vwap_price": vwap,
            "status": status,
        }
