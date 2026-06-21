"""Chronological replay clock and data feed.

Merges multi-symbol historical tick and bar datasets chronologically and manages
local warm-caching with checksum validation and TTL logic.
"""

from __future__ import annotations

import hashlib
import heapq
import json
from collections.abc import Iterator
from typing import Any, Literal, cast

from app.services.data import get_data
from app.services.data.storage import get_cached_data, set_cached_data
from app.services.simulator.models import SimulatorTick
from app.services.simulator.validation.quality import (
    align_record_timezones,
    apply_partial_data_policy,
    detect_data_gaps,
)
from app.utils.logger import logger


class ChronologicalDataFeed:
    """Ingests and replays multi-symbol tick or bar data chronologically.

    Args:
        symbols: Financial symbol identifiers.
        start: UTC start time string.
        end: UTC end time string.
        data_kind: Kind of data ('ticks' or 'ohlcv').
        timeframe: Bar timeframe (required for ohlcv).
        source: Primary source adapter.
        stale_data_behavior: Expired cache lookup policy.
        partial_data_policy: Missing-data policy ('fail_fast',
            'quarantine', or 'allow').
        max_gap_seconds: Maximum allowed gap in seconds.
        request_id: Optional tracking identifier.
        data_manifest_hash: Optional manifest hash for cache lookup.
        manifest_checksums: Optional mapping of symbol to expected checksum.
        ttl_seconds: Cache TTL in seconds.
    """

    def __init__(
        self,
        symbols: tuple[str, ...],
        start: str,
        end: str,
        data_kind: Literal["ticks", "ohlcv"] = "ticks",
        timeframe: str | None = None,
        source: str = "csv",
        stale_data_behavior: str = "refresh_and_return",
        partial_data_policy: str = "fail_fast",
        max_gap_seconds: float = 3600.0,
        request_id: str | None = None,
        data_manifest_hash: str | None = None,
        manifest_checksums: dict[str, str] | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        """Initialize the chronological data feed."""
        self.symbols = symbols
        self.start = start
        self.end = end
        self.data_kind = data_kind
        self.timeframe = timeframe
        self.source = source
        self.stale_data_behavior = stale_data_behavior
        self.partial_data_policy = partial_data_policy
        self.max_gap_seconds = max_gap_seconds
        self.request_id = request_id
        self.data_manifest_hash = data_manifest_hash
        self.manifest_checksums = manifest_checksums or {}
        self.ttl_seconds = ttl_seconds

    def load_data(self) -> dict[str, list[dict[str, Any]]]:
        """Load, cache-check, align, and validate symbol datasets.

        Returns:
            dict[str, list[dict[str, Any]]]: Loaded and aligned datasets by symbol.
        """
        symbol_data: dict[str, list[dict[str, Any]]] = {}

        for symbol in self.symbols:
            records = self._load_symbol_data_with_cache(symbol)
            aligned = align_record_timezones(records)
            symbol_data[symbol] = aligned

        # Apply partial data policy
        symbol_data = apply_partial_data_policy(symbol_data, self.partial_data_policy)

        # Detect gaps
        for symbol, records in symbol_data.items():
            gaps = detect_data_gaps(records, self.timeframe, self.max_gap_seconds)
            if gaps:
                logger.warning(
                    f"Data gaps detected for {symbol}: {len(gaps)} issues.",
                    extra={"request_id": self.request_id},
                )

        return symbol_data

    def _load_symbol_data_with_cache(self, symbol: str) -> list[dict[str, Any]]:
        """Load single-symbol records with manifest hash and checksum verification."""
        cache_key = None
        if self.data_manifest_hash:
            # key includes manifest hash, provider id, dataset id, symbol,
            # timeframe, date range, adjustment mode, schema version
            key_material = (
                f"{self.data_manifest_hash}:{self.source}:{self.data_kind}:"
                f"{symbol}:{self.timeframe or 'ticks'}:{self.start}_{self.end}:"
                f"raw:1.0.0"
            )
            cache_key = hashlib.sha256(key_material.encode("utf-8")).hexdigest()

            cached = get_cached_data(
                cache_key,
                stale_data_behavior=self.stale_data_behavior,
                request_id=self.request_id,
            )
            if cached and cached.get("records") is not None:
                records = cast("list[dict[str, Any]]", cached["records"])

                # Check checksum validation against the authoritative manifest
                # if provided
                expected_checksum = self.manifest_checksums.get(symbol)
                if expected_checksum:
                    actual_checksum = hashlib.sha256(
                        json.dumps(records).encode("utf-8")
                    ).hexdigest()
                    if actual_checksum != expected_checksum:
                        logger.warning(
                            f"Cache checksum mismatch for {symbol}. "
                            f"Expected {expected_checksum}, got {actual_checksum}."
                        )
                        # Invalid cache, proceed to reload
                    else:
                        logger.info(f"Warm cache hit (checksum verified) for {symbol}")
                        return records
                else:
                    logger.info(f"Warm cache hit for {symbol}")
                    return records

        # Cache miss or invalid cache
        logger.info(f"Loading data from gateway for symbol: {symbol}")
        records = get_data(
            symbol=symbol,
            start_time=self.start,
            end_time=self.end,
            data_kind=self.data_kind,
            timeframe=self.timeframe,
            source=self.source,
            stale_data_behavior=self.stale_data_behavior,
            request_id=self.request_id,
        )

        # Store to cache if key exists
        if cache_key and records:
            set_cached_data(
                key=cache_key,
                source=self.source,
                symbol=symbol,
                timeframe=self.timeframe or "ticks",
                start_time=self.start,
                end_time=self.end,
                records=records,
                ttl_seconds=self.ttl_seconds,
                raw_hash=self.data_manifest_hash,
                request_id=self.request_id,
            )

        return records

    def _make_tick_generator(
        self, records: list[dict[str, Any]], symbol: str
    ) -> Iterator[SimulatorTick]:
        """Generate SimulatorTick objects for a specific symbol."""
        for rec in records:
            yield SimulatorTick(
                timestamp=rec["timestamp"],
                symbol=symbol,
                bid=float(rec["bid"]),
                ask=float(rec["ask"]),
                last=(float(rec["last"]) if rec.get("last") is not None else None),
                volume=(
                    float(rec["volume"]) if rec.get("volume") is not None else None
                ),
                spread_points=(
                    float(rec["spread_points"])
                    if rec.get("spread_points") is not None
                    else None
                ),
                source=self.source,
            )

    def __iter__(self) -> Iterator[SimulatorTick | dict[str, Any]]:
        """Yield ticks or bars in strictly chronological order.

        Yields chronologically sorted records across multiple symbols.
        """
        datasets = self.load_data()

        iterators: list[Iterator[SimulatorTick | dict[str, Any]]] = []
        for symbol, records in datasets.items():
            if self.data_kind == "ticks":
                iterators.append(self._make_tick_generator(records, symbol))
            else:
                iterators.append(iter(records))

        # Define key extractor for merge sorting
        def key_fn(x: SimulatorTick | dict[str, Any]) -> str:
            if isinstance(x, SimulatorTick):
                return str(x.timestamp)
            return str(x["timestamp"])

        yield from heapq.merge(*iterators, key=key_fn)
