# ruff: noqa
"""Tick stream generation and modeling for simulation.

Implements synthetic tick generation (MQL5 Article #75 style), timeframe/M1 tick paths,
and real tick streams.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.utils.errors import SimulationError

if TYPE_CHECKING:
    from app.services.simulation.models.spread import SpreadModel
    from app.services.simulation.validation.schema import SymbolSpec


def calculate_symbol_hash(symbol_spec: SymbolSpec) -> str:
    """Compute stable SHA-256 hash of SymbolSpec canonical JSON representation."""
    # Serialize with sorted keys to ensure stability
    spec_dict = symbol_spec.model_dump()

    # Normalize decimals to strings/floats for JSON compatibility
    def convert_decimal(obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, dict):
            return {k: convert_decimal(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert_decimal(x) for x in obj]
        return obj

    normalized = convert_decimal(spec_dict)
    canonical_json = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class TickGenerator:
    """Generates tick streams for backtesting from OHLCV bar historical data."""

    def __init__(
        self,
        symbol_spec: SymbolSpec,
        spread_model: SpreadModel,
        tick_model: str = "M1_TICKS",
        global_seed: int = 42,
    ) -> None:
        """Initialize tick generator."""
        self.symbol_spec = symbol_spec
        self.spread_model = spread_model
        self.tick_model = tick_model.upper()
        self.global_seed = global_seed
        self.symbol_hash = calculate_symbol_hash(symbol_spec)

        valid_tick_models = {
            "TIMEFRAME_TICKS",
            "M1_TICKS",
            "REAL_TICKS",
            "SYNTHETIC_TICKS",
        }
        if self.tick_model not in valid_tick_models:
            msg = f"Unsupported tick model: {tick_model}"
            raise SimulationError(
                msg,
                code="SIM_UNSUPPORTED_TICK_MODEL",
            )

    def generate_ticks_for_bar(self, bar: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate bid/ask ticks for a single OHLCV bar."""
        open_val = Decimal(str(bar["open"]))
        high_val = Decimal(str(bar["high"]))
        low_val = Decimal(str(bar["low"]))
        close_val = Decimal(str(bar["close"]))
        bar_time = str(bar["timestamp"])
        spread_points = int(bar.get("spread", 15))
        volume = int(bar.get("volume", 4))

        if open_val <= 0 or high_val <= 0 or low_val <= 0 or close_val <= 0:
            raise SimulationError(
                "OHLC price values must be positive.", code="SIM_DATA_INVALID_OHLC"
            )
        if (
            low_val > high_val
            or open_val > high_val
            or open_val < low_val
            or close_val > high_val
            or close_val < low_val
        ):
            msg = f"Invalid OHLC bounds: O={open_val}, H={high_val}, L={low_val}, C={close_val}"
            raise SimulationError(
                msg,
                code="SIM_DATA_INVALID_OHLC",
            )

        bid_prices: list[Decimal] = []

        if self.tick_model in {"TIMEFRAME_TICKS", "M1_TICKS"}:
            # Simple four-price path (Open, High, Low, Close) or similar based on direction
            if volume <= 1:
                bid_prices = [close_val]
            elif volume == 2:
                bid_prices = [open_val, close_val]
            elif volume == 3:
                # Open -> High or Low -> Close
                if close_val >= open_val:
                    bid_prices = [open_val, low_val, close_val]
                else:
                    bid_prices = [open_val, high_val, close_val]
            # 4 ticks path
            elif close_val >= open_val:
                # Bullish bar: Open -> Low -> High -> Close
                bid_prices = [open_val, low_val, high_val, close_val]
            else:
                # Bearish bar: Open -> High -> Low -> Close
                bid_prices = [open_val, high_val, low_val, close_val]

        elif self.tick_model == "SYNTHETIC_TICKS":
            # Generate deterministic per-bar seed using SHA-256
            schema_version = "simulation.synthetic_ticks.v1"
            hash_input = (
                f"{schema_version}_{self.global_seed}_{self.symbol_hash}_{bar_time}_v1"
            )
            seed = int(hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:8], 16)

            # Seed a simple deterministic LCG (linear congruential generator) for local random walk
            # to avoid using global random state
            lcg_state = seed

            def next_random() -> float:
                nonlocal lcg_state
                # Standard LCG parameters
                lcg_state = (1103515245 * lcg_state + 12345) & 0x7FFFFFFF
                return lcg_state / 2147483647.0

            # MQL5 Article #75 algorithm inspired support points
            # Ensure volume is at least 4 for complete OHLC path, cap at 100 for performance
            effective_volume = max(4, min(volume, 100))

            # Key points
            if close_val >= open_val:
                # Bullish: Open -> Low -> High -> Close
                stages = [
                    (open_val, low_val),
                    (low_val, high_val),
                    (high_val, close_val),
                ]
            else:
                # Bearish: Open -> High -> Low -> Close
                stages = [
                    (open_val, high_val),
                    (high_val, low_val),
                    (low_val, close_val),
                ]

            # Distribute ticks among the three stages
            # Stage 1: ~25%, Stage 2: ~50%, Stage 3: ~25%
            ticks_left = effective_volume - 4  # Reserve Open, Low, High, Close
            ticks_per_stage = [0, 0, 0]
            for _ in range(ticks_left):
                r = next_random()
                if r < 0.25:
                    ticks_per_stage[0] += 1
                elif r < 0.75:
                    ticks_per_stage[1] += 1
                else:
                    ticks_per_stage[2] += 1

            # Build the path
            bid_prices.append(open_val)
            for idx, (start, end) in enumerate(stages):
                stage_ticks = ticks_per_stage[idx]
                if stage_ticks > 0:
                    diff = end - start
                    # Interpolate with a random-walk flavor
                    for step in range(1, stage_ticks + 1):
                        progress = Decimal(str(step)) / Decimal(str(stage_ticks + 1))
                        # Add a deterministic random noise perturbation
                        noise = (
                            Decimal(str(next_random() - 0.5)) * Decimal("0.2") * diff
                        )
                        price_step = start + (progress * diff) + noise
                        # Bound within start and end to avoid breaching HL bounds
                        price_step = max(
                            min(start, end), min(max(start, end), price_step)
                        )
                        # Normalize to tick size
                        price_step = (price_step / self.symbol_spec.tick_size).quantize(
                            Decimal(1), rounding="ROUND_HALF_UP"
                        ) * self.symbol_spec.tick_size
                        bid_prices.append(price_step)
                bid_prices.append(end)

            # Dedup contiguous identical prices
            dedupped: list[Decimal] = []
            for bp in bid_prices:
                if not dedupped or bp != dedupped[-1]:
                    dedupped.append(bp)
            bid_prices = dedupped

        else:
            # REAL_TICKS: bar processing is not directly done here,
            # but if fallback OHLC bars are supplied in real-ticks mode, do 4-tick path
            bid_prices = [open_val, low_val, high_val, close_val]

        # Convert bid prices to tick objects
        ticks = []
        point = self.symbol_spec.point
        for seq, bid in enumerate(bid_prices):
            # Enforce high/low bounds strictly
            bid = max(low_val, min(high_val, bid))
            ask = self.spread_model.calculate_ask(
                bid=bid,
                point=point,
                record_spread_points=spread_points,
                bar_time=bar_time,
            )
            ticks.append(
                {
                    "time": bar_time,
                    "symbol": self.symbol_spec.symbol,
                    "bid": bid,
                    "ask": ask,
                    "last": bid,
                    "volume": Decimal("1.0"),
                    "source": self.tick_model.lower(),
                    "bar_time": bar_time,
                    "sequence_in_bar": seq + 1,
                    "bar_open_flag": 1 if seq == 0 else 0,
                }
            )

        return ticks
