"""Concurrency ordering and locking logic.

Serializes trading requests per (account, symbol) scope using async locks
to prevent race conditions and interleaved state updates.
"""

import asyncio
import threading
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from app.utils.logger import logger


class ConcurrencyQueue:
    """Manager for locks per (account, symbol) scope to serialize execution."""

    _instance: "ConcurrencyQueue | None" = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize ConcurrencyQueue."""
        self._locks: dict[tuple[str, str], asyncio.Lock] = {}
        self._sync_locks: dict[tuple[str, str], threading.Lock] = {}
        self._internal_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ConcurrencyQueue":
        """Get the shared ConcurrencyQueue singleton.

        Returns:
            ConcurrencyQueue: ConcurrencyQueue singleton.
        """
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _get_lock(self, account_id: str, symbol: str) -> asyncio.Lock:
        """Get or create the asyncio.Lock for the (account, symbol) pair.

        Args:
            account_id: The trading account ID.
            symbol: The financial instrument symbol.

        Returns:
            asyncio.Lock: Lock instance.
        """
        key = (account_id, symbol)
        with self._internal_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    def _get_sync_lock(self, account_id: str, symbol: str) -> threading.Lock:
        """Get or create the threading.Lock for the (account, symbol) pair.

        Args:
            account_id: The trading account ID.
            symbol: The financial instrument symbol.

        Returns:
            threading.Lock: Lock instance.
        """
        key = (account_id, symbol)
        with self._internal_lock:
            if key not in self._sync_locks:
                self._sync_locks[key] = threading.Lock()
            return self._sync_locks[key]

    @asynccontextmanager
    async def lock(self, account_id: str, symbol: str) -> AsyncGenerator[None]:
        """Async context manager to acquire and release lock per (account, symbol).

        Args:
            account_id: The trading account ID.
            symbol: The financial instrument symbol.
        """
        async_lock = self._get_lock(account_id, symbol)
        logger.debug(
            f"Acquiring async lock for account={account_id}, symbol={symbol}..."
        )
        await async_lock.acquire()
        try:
            logger.debug(
                f"Acquired async lock for account={account_id}, symbol={symbol}."
            )
            yield
        finally:
            async_lock.release()
            logger.debug(
                f"Released async lock for account={account_id}, symbol={symbol}."
            )

    @contextmanager
    def lock_sync(self, account_id: str, symbol: str) -> Generator[None]:
        """Sync context manager to acquire and release lock per (account, symbol).

        Args:
            account_id: The trading account ID.
            symbol: The financial instrument symbol.
        """
        sync_lock = self._get_sync_lock(account_id, symbol)
        logger.debug(
            f"Acquiring sync lock for account={account_id}, symbol={symbol}..."
        )
        sync_lock.acquire()
        try:
            logger.debug(
                f"Acquired sync lock for account={account_id}, symbol={symbol}."
            )
            yield
        finally:
            sync_lock.release()
            logger.debug(
                f"Released sync lock for account={account_id}, symbol={symbol}."
            )
