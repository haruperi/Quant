# ruff: noqa: PLR2004, E501
"""RateLimiter service for broker api throttling.

Provides a thread-safe token bucket rate limiter configured per provider.
"""

import threading
import time
from typing import Any

from app.utils.logger import logger


class RateLimiter:
    """Thread-safe token-bucket rate limiter per broker instance."""

    def __init__(self, capacity: float = 10.0, fill_rate: float = 2.0) -> None:
        """Initialize the RateLimiter.

        Args:
            capacity: Maximum tokens the bucket can hold.
            fill_rate: Number of tokens added to the bucket per second.
        """
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
        self.warning_start_time: float | None = None

    def _refill(self) -> None:
        """Refill the token bucket based on elapsed time since last refill."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)

    def check_rate_limit(self) -> bool:
        """Check if at least one token is available without consuming it.

        Returns:
            bool: True if a token is available.
        """
        with self.lock:
            self._refill()
            return self.tokens >= 1.0

    def acquire(self, tokens: float = 1.0) -> bool:
        """Consume tokens from the bucket.

        Args:
            tokens: The number of tokens to consume.

        Returns:
            bool: True if tokens were consumed successfully, False if rate limited.
        """
        with self.lock:
            self._refill()
            utilization = (self.capacity - self.tokens) / self.capacity
            now = time.time()

            # Observability: Warning if rate limit utilization exceeds 80%
            if utilization > 0.8:
                if self.warning_start_time is None:
                    self.warning_start_time = now
                elif now - self.warning_start_time > 300:  # 5 minutes
                    logger.warning(
                        "Rate limiter capacity utilization has exceeded 80% for over 5 minutes.",
                        extra={"utilization": utilization, "tokens": self.tokens},
                    )
            else:
                self.warning_start_time = None

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_status(self) -> dict[str, Any]:
        """Get the current rate limiter state.

        Returns:
            dict[str, Any]: Status dictionary containing tokens and utilization.
        """
        with self.lock:
            self._refill()
            return {
                "tokens": self.tokens,
                "capacity": self.capacity,
                "utilization": (self.capacity - self.tokens) / self.capacity,
            }


# Cache of rate limiters per provider instance
_limiters: dict[str, RateLimiter] = {}
_limiters_lock = threading.Lock()


def get_rate_limiter(provider: str) -> RateLimiter:
    """Get or create the RateLimiter singleton instance for a given provider.

    Args:
        provider: The broker provider name (e.g., 'mt5', 'ctrader', 'sim').

    Returns:
        RateLimiter: The RateLimiter instance.
    """
    with _limiters_lock:
        prov_key = provider.lower()
        if prov_key not in _limiters:
            # Different default rates based on broker type
            if prov_key == "ctrader":
                # cTrader Open API allows up to 50 requests per second
                _limiters[prov_key] = RateLimiter(capacity=30.0, fill_rate=10.0)
            elif prov_key == "mt5":
                # MT5 terminal calls are local but throttling prevents congestion
                _limiters[prov_key] = RateLimiter(capacity=20.0, fill_rate=5.0)
            else:
                # Simulator/Default
                _limiters[prov_key] = RateLimiter(capacity=100.0, fill_rate=50.0)
            logger.info(
                f"Created RateLimiter for provider '{prov_key}'",
                extra={
                    "capacity": _limiters[prov_key].capacity,
                    "fill_rate": _limiters[prov_key].fill_rate,
                },
            )
        return _limiters[prov_key]
