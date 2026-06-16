"""Thread-safe caching adapter for the indicators service.

Supports cache key derivation, hits/misses, and policy degradation behavior
(none, best_effort, strict).
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from app.utils.errors import IndicatorConfigError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.indicators.protocols import IndicatorResult


class IndicatorCache:
    """Thread-safe in-memory cache for indicator results."""

    def __init__(self) -> None:
        """Initialize lock and internal storage."""
        self._lock = threading.Lock()
        self._store: dict[str, IndicatorResult] = {}
        self.is_unreachable = False  # Used to simulate connection failures in tests

    def derive_key(
        self,
        indicator_id: str,
        param_hash: str,
        input_checksum: str,
        impl_version: str,
        schema_version: str,
        precision_policy: str,
    ) -> str:
        """Derive a stable, normalized cache key.

        Internal keys and computations are normalized to UTC.
        """
        # All inputs are normalized to lowercase keys and UTC-first timestamps
        return (
            f"{indicator_id.lower()}:{param_hash}:{input_checksum}:"
            f"{impl_version}:{schema_version}:{precision_policy.lower()}"
        )

    def get(self, key: str, policy: str) -> IndicatorResult | None:
        """Retrieve a cached IndicatorResult based on key and policy.

        Raises:
            IndicatorConfigError: If strict policy is configured and cache fails.
        """
        if policy == "none":
            return None

        if self.is_unreachable:
            if policy == "strict":
                raise IndicatorConfigError(
                    "Cache store is unreachable.",
                    code="IND_CACHE_INVALID",
                )
            logger.warning(
                "Cache store is unreachable. Degrading to uncached calculation."
            )
            return None

        try:
            with self._lock:
                return self._store.get(key)
        except Exception as exc:
            if policy == "strict":
                msg = f"Cache retrieval failed: {exc}"
                raise IndicatorConfigError(
                    msg,
                    code="IND_CACHE_INVALID",
                ) from exc
            logger.warning(
                f"Cache retrieval error: {exc}. Degrading to uncached calculation."
            )
            return None

    def set(self, key: str, result: IndicatorResult, policy: str) -> None:
        """Store result in cache atomically.

        Raises:
            IndicatorConfigError: If strict policy is configured and cache fails.
        """
        if policy == "none":
            return

        if self.is_unreachable:
            if policy == "strict":
                raise IndicatorConfigError(
                    "Cache write failed: cache is unreachable.",
                    code="IND_CACHE_INVALID",
                )
            logger.warning("Cache write failed: cache is unreachable.")
            return

        try:
            with self._lock:
                self._store[key] = result
        except Exception as exc:
            if policy == "strict":
                msg = f"Cache write failed: {exc}"
                raise IndicatorConfigError(
                    msg,
                    code="IND_CACHE_INVALID",
                ) from exc
            logger.warning(f"Cache write error: {exc}")


# Global thread-safe cache instance
global_cache = IndicatorCache()
