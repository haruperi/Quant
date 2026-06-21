# ruff: noqa: TC001
"""Provider protocols module.

Defines runtime structural interfaces (Protocols) that adapters and storage
systems must conform to, ensuring raw broker and database models remain hidden
behind canonical contract boundaries.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

# These imports are required at runtime because the Protocols are decorated
# with @runtime_checkable and isinstance() checks resolve method signatures
# at import time via the typing machinery.
from app.contracts.market import DataSlice, Symbol
from app.contracts.portfolio import AccountSnapshot, Position
from app.contracts.trading import ExecutionReport, Fill, TradeRequest, TradeResult


@runtime_checkable
class MarketDataProvider(Protocol):
    """Protocol for fetching market data bars and ticks."""

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> DataSlice:
        """Fetch historical bars and return a canonical DataSlice."""
        ...

    def get_ticks(self, symbol: str, start: str, end: str) -> DataSlice:
        """Fetch historical tick stream and return a canonical DataSlice."""
        ...


@runtime_checkable
class ExecutionProvider(Protocol):
    """Protocol for submitting and cancelling broker trades."""

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Submit a TradeRequest to the broker and return the execution TradeResult."""
        ...

    def cancel_order(self, request_id: str, order_id: str) -> TradeResult:
        """Cancel an active pending order."""
        ...


@runtime_checkable
class AccountProvider(Protocol):
    """Protocol for retrieving broker account information."""

    def get_account_snapshot(self) -> AccountSnapshot:
        """Retrieve the current AccountSnapshot metrics."""
        ...


@runtime_checkable
class PositionProvider(Protocol):
    """Protocol for reading open positions."""

    def get_open_positions(self) -> list[Position]:
        """Fetch all active open Positions."""
        ...


@runtime_checkable
class OrderProvider(Protocol):
    """Protocol for tracking active orders."""

    def get_active_orders(self) -> list[ExecutionReport]:
        """Retrieve list of active pending orders as ExecutionReports."""
        ...


@runtime_checkable
class SymbolInfoProvider(Protocol):
    """Protocol for retrieving Symbol specification metadata."""

    def get_symbol_info(self, symbol: str) -> Symbol:
        """Fetch canonical Symbol information specification details."""
        ...


@runtime_checkable
class BrokerErrorMapper(Protocol):
    """Protocol for translating broker-specific exceptions to neutral error codes."""

    def map_error(self, raw_error: object) -> str:
        """Map raw error payload to a canonical error code string.

        Args:
            raw_error: Any broker exception or error object.

        Returns:
            Canonical error code string (e.g. ``'BROKER_UNAVAILABLE'``).
        """
        ...


@runtime_checkable
class ExecutionJournal(Protocol):
    """Protocol for persisted logs of execution reports and fills."""

    def record_report(self, report: ExecutionReport) -> None:
        """Log a canonical ExecutionReport to the journal."""
        ...

    def record_fill(self, fill: Fill) -> None:
        """Log a canonical Fill transaction receipt to the journal."""
        ...


@runtime_checkable
class TradeStore(Protocol):
    """Protocol for persisted positions, executions, and reconciliation records.

    Implementations must support idempotency keys to prevent duplicate
    order submissions and reconciliation records to detect broker/local
    state divergence.
    """

    def save_trade_result(self, result: TradeResult) -> None:
        """Persist a canonical TradeResult."""
        ...

    def get_trade_result(self, trade_id: str) -> TradeResult | None:
        """Retrieve a persisted TradeResult by trade ID."""
        ...

    def save_position(self, position: Position) -> None:
        """Persist or update an active Position state."""
        ...

    def get_position(self, position_id: str) -> Position | None:
        """Retrieve a persisted Position by position ID."""
        ...

    def save_idempotency_key(self, key: str, trade_id: str) -> None:
        """Register an idempotency key bound to a trade ID.

        Callers check this before submitting to prevent duplicate orders
        when retrying after transient failures.

        Args:
            key: Idempotency key (e.g. ``'req_<uuid>'``).
            trade_id: The trade ID already associated with this key.
        """
        ...

    def get_idempotency_key(self, key: str) -> str | None:
        """Look up whether an idempotency key has already been processed.

        Args:
            key: Idempotency key to look up.

        Returns:
            The previously recorded trade ID, or ``None`` if not found.
        """
        ...

    def save_reconciliation_record(
        self,
        trade_id: str,
        broker_state: dict[str, Any],
        local_state: dict[str, Any],
        status: str,
    ) -> None:
        """Persist a reconciliation record comparing broker and local state.

        Args:
            trade_id: The trade being reconciled.
            broker_state: State as reported by the broker.
            local_state: State as recorded locally.
            status: Reconciliation outcome (e.g. ``'matched'``, ``'mismatch'``).
        """
        ...
