# ruff: noqa: E501
"""Idempotency service implementation.

Computes request hashes, tracks lifecycle stages (in_progress vs. completed),
and intercepts duplicate requests to prevent double-executions.
"""

import hashlib
import time
from typing import Any

from app.services.trader.store import TradeStore
from app.utils.logger import logger


class IdempotencyService:
    """Manages trading request idempotency keys and lifecycle records."""

    def __init__(self, store: TradeStore) -> None:
        """Initialize IdempotencyService with a TradeStore instance.

        Args:
            store: Persistent store reference.
        """
        self.store = store

    def generate_key(
        self,
        account_id: str,
        symbol: str,
        action_type: int,
        volume: float,
        price: float,
        slippage: int,
        window_seconds: int = 10,
    ) -> str:
        """Generate a deterministic idempotency key.

        Args:
            account_id: The trading account ID.
            symbol: The financial instrument symbol.
            action_type: The transaction action type.
            volume: The request volume.
            price: The request price.
            slippage: Maximum deviation points.
            window_seconds: Timestamp bucket size in seconds.

        Returns:
            str: Hexadecimal SHA-256 hash.
        """
        # Bucketize timestamp to group closely sent duplicates
        window = int(time.time() / window_seconds)
        payload = f"{account_id}:{symbol.upper()}:{action_type}:{volume:.4f}:{price:.6f}:{slippage}:{window}"
        key_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"idem_{key_hash}"

    def check_duplicate(self, key: str) -> dict[str, Any] | None:
        """Query store for an existing record matching the key.

        Args:
            key: The idempotency key.

        Returns:
            dict[str, Any] | None: The record dictionary or None if first time.
        """
        return self.store.get_idempotency_record(key)

    def register_in_progress(
        self, key: str, request_data: dict[str, Any], ttl_seconds: int = 60
    ) -> None:
        """Mark the key as 'in_progress' in the store.

        Args:
            key: The idempotency key.
            request_data: Request attributes to store.
            ttl_seconds: In-progress timeout to prevent lockups on crash.
        """
        record = {
            "status": "in_progress",
            "request": request_data,
            "created_at": time.time(),
            "result": None,
        }
        self.store.save_idempotency_record(key, record, ttl_seconds)
        logger.debug(f"Registered idempotency key {key} as 'in_progress'.")

    def register_completed(
        self, key: str, result_dict: dict[str, Any], ttl_seconds: int = 86400
    ) -> None:
        """Mark the key as 'completed' and store the execution result.

        Args:
            key: The idempotency key.
            result_dict: Normalized trade execution result dictionary.
            ttl_seconds: Keep history for 24 hours.
        """
        record = self.store.get_idempotency_record(key) or {}
        record["status"] = "completed"
        record["result"] = result_dict
        record["completed_at"] = time.time()

        self.store.save_idempotency_record(key, record, ttl_seconds)
        logger.info(f"Registered idempotency key {key} as 'completed'.")
