"""TradeStore interface and in-memory implementation.

Defines the repository contract for persistence of orders, positions,
deals, and idempotency records required by the trader boundary.
"""

import time
from abc import ABC, abstractmethod
from typing import Any

from app.utils.logger import logger


class TradeStore(ABC):
    """Abstract base class representing the TradeStore repository contract."""

    @abstractmethod
    def get_idempotency_record(self, key: str) -> dict[str, Any] | None:
        """Retrieve idempotency record by key.

        Args:
            key: The idempotency key.

        Returns:
            dict[str, Any] | None: The record dictionary or None if not found.
        """

    @abstractmethod
    def save_idempotency_record(
        self, key: str, record: dict[str, Any], ttl_seconds: int = 86400
    ) -> None:
        """Save an idempotency record.

        Args:
            key: The idempotency key.
            record: The record to save.
            ttl_seconds: Time to live in seconds.
        """

    @abstractmethod
    def get_order(self, ticket: int) -> dict[str, Any] | None:
        """Retrieve an order by ticket.

        Args:
            ticket: The order ticket.

        Returns:
            dict[str, Any] | None: The order details or None if not found.
        """

    @abstractmethod
    def save_order(self, ticket: int, order: dict[str, Any]) -> None:
        """Save order details.

        Args:
            ticket: The order ticket.
            order: The order dictionary.
        """

    @abstractmethod
    def get_orders(self) -> list[dict[str, Any]]:
        """Retrieve all active orders.

        Returns:
            list[dict[str, Any]]: List of active orders.
        """

    @abstractmethod
    def get_position(self, ticket: int) -> dict[str, Any] | None:
        """Retrieve a position by ticket.

        Args:
            ticket: The position ticket.

        Returns:
            dict[str, Any] | None: The position details or None if not found.
        """

    @abstractmethod
    def save_position(self, ticket: int, position: dict[str, Any]) -> None:
        """Save position details.

        Args:
            ticket: The position ticket.
            position: The position dictionary.
        """

    @abstractmethod
    def delete_position(self, ticket: int) -> None:
        """Remove a position.

        Args:
            ticket: The position ticket.
        """

    @abstractmethod
    def get_positions(self) -> list[dict[str, Any]]:
        """Retrieve all active positions.

        Returns:
            list[dict[str, Any]]: List of active positions.
        """

    @abstractmethod
    def get_execution(self, ticket: int) -> dict[str, Any] | None:
        """Retrieve an execution deal by ticket.

        Args:
            ticket: The deal ticket.

        Returns:
            dict[str, Any] | None: The deal details or None if not found.
        """

    @abstractmethod
    def save_execution(self, ticket: int, execution: dict[str, Any]) -> None:
        """Save execution deal details.

        Args:
            ticket: The deal ticket.
            execution: The deal dictionary.
        """

    @abstractmethod
    def get_executions(self) -> list[dict[str, Any]]:
        """Retrieve all execution deals.

        Returns:
            list[dict[str, Any]]: List of deals.
        """


class InMemoryTradeStore(TradeStore):
    """In-memory implementation of the TradeStore interface."""

    def __init__(self) -> None:
        """Initialize the dictionaries."""
        self._idempotency: dict[str, tuple[dict[str, Any], float]] = {}
        self._orders: dict[int, dict[str, Any]] = {}
        self._positions: dict[int, dict[str, Any]] = {}
        self._executions: dict[int, dict[str, Any]] = {}
        logger.info("InMemoryTradeStore initialized.")

    def get_idempotency_record(self, key: str) -> dict[str, Any] | None:
        """Retrieve idempotency record, checking TTL expiration."""
        if key not in self._idempotency:
            return None
        record, expires_at = self._idempotency[key]
        if time.time() > expires_at:
            logger.debug(f"Idempotency key {key} expired.")
            del self._idempotency[key]
            return None
        return record

    def save_idempotency_record(
        self, key: str, record: dict[str, Any], ttl_seconds: int = 86400
    ) -> None:
        """Save idempotency record with absolute expiration time."""
        expires_at = time.time() + ttl_seconds
        self._idempotency[key] = (record, expires_at)
        logger.debug(f"Saved idempotency key {key} with TTL {ttl_seconds}s.")

    def get_order(self, ticket: int) -> dict[str, Any] | None:
        """Retrieve order."""
        return self._orders.get(ticket)

    def save_order(self, ticket: int, order: dict[str, Any]) -> None:
        """Save order."""
        self._orders[ticket] = order
        logger.debug(f"Saved order ticket {ticket}.")

    def get_orders(self) -> list[dict[str, Any]]:
        """Get all orders."""
        return list(self._orders.values())

    def get_position(self, ticket: int) -> dict[str, Any] | None:
        """Retrieve position."""
        return self._positions.get(ticket)

    def save_position(self, ticket: int, position: dict[str, Any]) -> None:
        """Save position."""
        self._positions[ticket] = position
        logger.debug(f"Saved position ticket {ticket}.")

    def delete_position(self, ticket: int) -> None:
        """Delete position."""
        if ticket in self._positions:
            del self._positions[ticket]
            logger.debug(f"Deleted position ticket {ticket}.")

    def get_positions(self) -> list[dict[str, Any]]:
        """Get all positions."""
        return list(self._positions.values())

    def get_execution(self, ticket: int) -> dict[str, Any] | None:
        """Retrieve execution deal."""
        return self._executions.get(ticket)

    def save_execution(self, ticket: int, execution: dict[str, Any]) -> None:
        """Save execution deal."""
        self._executions[ticket] = execution
        logger.debug(f"Saved execution deal ticket {ticket}.")

    def get_executions(self) -> list[dict[str, Any]]:
        """Get all execution deals."""
        return list(self._executions.values())


# Global singleton instance of in-memory store for default fallback
_default_store = InMemoryTradeStore()


def get_default_store() -> TradeStore:
    """Get default singleton TradeStore instance.

    Returns:
        TradeStore: The default in-memory store.
    """
    return _default_store
