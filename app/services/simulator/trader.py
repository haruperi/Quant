"""In-memory simulator execution provider and MT5-style compatibility facade.

Exports a simulator-only execution adapter plus legacy MT5-like helper classes
used by existing trader tests. Importing this module does not connect to MT5;
MT5 is consulted only when ``SimulatorClient.connect()`` is explicitly called.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatch
from typing import Any, Literal, cast

import MetaTrader5

from app.contracts.portfolio import AccountSnapshot, Position
from app.contracts.trading import TradeRequest, TradeResult
from app.utils.errors import ConfigurationError, ExternalServiceError
from app.utils.logger import logger

TRADE_ACTION_DEAL = 1
TRADE_ACTION_MODIFY = 2
TRADE_ACTION_SLTP = 3
TRADE_ACTION_REMOVE = 4
TRADE_ACTION_PENDING = 5
TRADE_RETCODE_DONE = 10009


@dataclass(slots=True)
class SimulatorTradeResult:
    """MT5-style trade result object.

    Args:
        retcode: MT5-style return code.
        order: Order ticket.
        deal: Deal ticket.
        volume: Executed volume.
        price: Execution price.
        bid: Current bid.
        ask: Current ask.
        comment: Human-readable status.
    """

    retcode: int
    order: int = 0
    deal: int = 0
    volume: float = 0.0
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    comment: str = ""


@dataclass(slots=True)
class SimulatorTickInfo:
    """MT5-style symbol tick snapshot."""

    bid: float
    ask: float
    last: float


@dataclass(slots=True)
class SimulatorTerminalInfo:
    """MT5-style terminal information snapshot."""

    connected: bool
    trade_allowed: bool = True
    dlls_allowed: bool = True
    ping_last: int = 500
    company: str = "HaruQuant AI"
    name: str = "HaruQuant Broker Simulator"
    path: str = "In-Memory"


class SimulatorSymbolInfo:
    """MT5-style symbol information wrapper.

    Args:
        data: Symbol metadata mapping.

    Raises:
        KeyError: If required fields are absent.
    """

    name: str
    bid: float
    ask: float
    trade_contract_size: float

    def __init__(self, data: dict[str, Any]) -> None:
        """Expose symbol metadata as attributes."""
        for key, value in data.items():
            setattr(self, key, value)


class SimulatorAccountInfo:
    """MT5-style account information wrapper.

    Args:
        client: Simulator client whose state should be summarized.

    Raises:
        No explicit exceptions are raised.
    """

    def __init__(self, client: SimulatorClient) -> None:
        """Calculate account fields from the client state."""
        self.login = client.login
        self.balance = client.balance
        self.credit = client.credit
        self.profit = client.calculate_total_profit()
        self.margin = client.calculate_total_margin()
        self.equity = self.balance + self.credit + self.profit
        self.margin_free = self.equity - self.margin
        self.margin_level = (
            self.equity / self.margin * 100 if self.margin > 0 else 100000.0
        )
        self.leverage = client.leverage
        self.currency = client.currency


class _RecordView:
    """Simple attribute wrapper for order, deal, and position dictionaries."""

    ticket: int

    def __init__(self, data: dict[str, Any]) -> None:
        """Expose dictionary keys as attributes."""
        for key, value in data.items():
            setattr(self, key, value)


class SimulatorExecutionProvider:
    """ExecutionProvider-compatible simulator adapter.

    Args:
        client: Optional simulator client.

    Raises:
        No exceptions are raised during construction.
    """

    def __init__(self, client: SimulatorClient | None = None) -> None:
        """Initialize adapter with a simulator client."""
        self.client = client or SimulatorClient.get_instance()

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Execute a canonical TradeRequest in simulator state only.

        Args:
            request: Canonical trade request.

        Returns:
            TradeResult: Canonical trade result.

        Raises:
            ExternalServiceError: If simulator execution fails.
        """
        self.client.connect()
        intent = request.order_intent
        order_type = 0 if intent.action.startswith("buy") else 1
        raw = {
            "action": 1 if intent.order_type == "market" else 5,
            "symbol": intent.symbol,
            "volume": intent.volume,
            "type": order_type,
            "price": intent.price or 0.0,
        }
        result = self.client.execute_trade(raw)
        status: Literal["filled", "failed"] = (
            "filled" if result.retcode == TRADE_RETCODE_DONE else "failed"
        )
        return TradeResult(
            trade_id=str(result.order),
            request_id=request.request_id,
            status=status,
            fill_price=result.price,
            fill_volume=result.volume,
            commission=0.0,
            slippage_points=0.0,
            error_code=None if status == "filled" else "SIM_INTERNAL_ERROR",
            error_message=None if status == "filled" else result.comment,
        )

    def cancel_order(self, request_id: str, order_id: str) -> TradeResult:
        """Cancel a pending simulator order.

        Args:
            request_id: Request identifier.
            order_id: Pending order id.

        Returns:
            TradeResult: Cancel result.

        Raises:
            ExternalServiceError: If the order does not exist.
        """
        result = self.client.execute_trade({"action": 4, "order": int(order_id)})
        return TradeResult(
            trade_id=str(result.order),
            request_id=request_id,
            status="cancelled",
            fill_price=None,
            fill_volume=0.0,
            error_code=None,
            error_message=None,
        )

    def get_account_snapshot(self) -> AccountSnapshot:
        """Return a canonical account snapshot."""
        info = SimulatorAccountInfo(self.client)
        return AccountSnapshot(
            equity=info.equity,
            balance=info.balance,
            margin=info.margin,
            free_margin=info.margin_free,
            currency=info.currency,
            leverage=info.leverage,
            timestamp=datetime.now(UTC).isoformat(),
        )

    def get_open_positions(self) -> list[Position]:
        """Return canonical open positions."""
        positions = []
        now = datetime.now(UTC).isoformat()
        for raw in self.client.positions.values():
            side: Literal["buy", "sell"] = (
                "buy" if int(raw.get("type", 0)) == 0 else "sell"
            )
            positions.append(
                Position(
                    position_id=str(raw["ticket"]),
                    symbol=str(raw["symbol"]),
                    side=side,
                    quantity=float(raw["volume"]),
                    average_price=float(raw["price_open"]),
                    unrealized_pnl=float(raw.get("profit", 0.0)),
                    provider_position_id=str(raw["ticket"]),
                    opened_at=now,
                    updated_at=now,
                )
            )
        return positions


class SimulatorClient:
    """Singleton in-memory MT5-style simulator client.

    Args:
        No public constructor arguments are accepted.

    Raises:
        No exceptions are raised during construction.
    """

    _instance: SimulatorClient | None = None

    def __init__(self) -> None:
        """Initialize offline simulator state."""
        self.login = 10001
        self.balance = 100000.0
        self.credit = 0.0
        self.leverage = 100
        self.currency = "USD"
        self.positions: dict[int, dict[str, Any]] = {}
        self.orders: dict[int, dict[str, Any]] = {}
        self.history_orders: dict[int, dict[str, Any]] = {}
        self.history_deals: dict[int, dict[str, Any]] = {}
        self._next_ticket = 100000
        self._next_deal = 500000
        self._is_connected = False
        self._is_mt5_connected = False
        self._error = "Success"
        self.symbols = _default_symbols()

    @classmethod
    def get_instance(cls) -> SimulatorClient:
        """Return the singleton simulator client.

        Returns:
            SimulatorClient: Shared simulator client.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def connect(self) -> bool:
        """Connect to simulator and opportunistically mirror MT5 metadata."""
        self._is_connected = True
        try:
            if MetaTrader5.initialize():
                if MetaTrader5.login(self.login):
                    self._is_mt5_connected = True
                    for symbol in list(self.symbols):
                        MetaTrader5.symbol_select(symbol, True)
                else:
                    self._is_mt5_connected = False
                    MetaTrader5.shutdown()
        except Exception as exc:  # noqa: BLE001
            logger.warning("simulator MT5 mirror unavailable: %s", exc)
            self._is_mt5_connected = False
        return True

    def disconnect(self) -> None:
        """Disconnect simulator and MT5 mirror if active."""
        if self._is_mt5_connected:
            MetaTrader5.shutdown()
        self._is_mt5_connected = False
        self._is_connected = False

    def shutdown(self) -> None:
        """Shutdown simulator connection."""
        self.disconnect()

    def is_connected(self) -> bool:
        """Return connection status."""
        return self._is_connected

    def last_error(self) -> str:
        """Return last simulator error string."""
        return self._error

    def symbols_total(self) -> int:
        """Return configured symbol count."""
        return len(self.symbols)

    def subscribe_spots(self, symbol: str) -> None:
        """Subscribe to a symbol feed in simulator mode."""
        if symbol not in self.symbols:
            message = f"Symbol {symbol} not configured in simulator."
            raise ConfigurationError(message)

    def unsubscribe_spots(self, symbol: str) -> None:
        """Unsubscribe from a symbol feed in simulator mode."""
        if symbol not in self.symbols:
            message = f"Symbol {symbol} not configured in simulator."
            raise ConfigurationError(message)

    def symbol_info_tick(self, symbol: str) -> SimulatorTickInfo | None:
        """Return the current tick for a symbol."""
        if symbol not in self.symbols:
            return None
        if self._is_mt5_connected:
            tick = MetaTrader5.symbol_info_tick(symbol)
            if tick is not None:
                return SimulatorTickInfo(tick.bid, tick.ask, tick.last)
        data = self.symbols[symbol]
        return SimulatorTickInfo(
            bid=float(data["bid"]),
            ask=float(data["ask"]),
            last=float(data["last"]),
        )

    def symbol_info(self, symbol: str) -> SimulatorSymbolInfo | None:
        """Return symbol info for a symbol."""
        if symbol not in self.symbols:
            return None
        if self._is_mt5_connected:
            info = MetaTrader5.symbol_info(symbol)
            if info is not None:
                data = {
                    key: getattr(info, key)
                    for key in (
                        "name",
                        "description",
                        "path",
                        "digits",
                        "point",
                        "trade_tick_size",
                        "trade_contract_size",
                        "volume_min",
                        "volume_max",
                        "volume_step",
                        "swap_mode",
                        "swap_long",
                        "swap_short",
                        "bid",
                        "ask",
                        "last",
                        "spread",
                        "trade_mode",
                    )
                }
                self.symbols[symbol].update(data)
                return SimulatorSymbolInfo(data)
        return SimulatorSymbolInfo(dict(self.symbols[symbol]))

    def order_calc_margin(
        self, action: int, symbol: str, volume: float, price: float
    ) -> float | None:
        """Calculate required margin."""
        if symbol not in self.symbols:
            return None
        if self._is_mt5_connected:
            return cast(
                "float | None",
                MetaTrader5.order_calc_margin(action, symbol, volume, price),
            )
        info = self.symbols[symbol]
        return float(info["trade_contract_size"]) * volume * price / self.leverage

    def order_calc_profit(
        self,
        action: int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float | None:
        """Calculate position profit."""
        if symbol not in self.symbols:
            return None
        if self._is_mt5_connected:
            return cast(
                "float | None",
                MetaTrader5.order_calc_profit(
                    action, symbol, volume, price_open, price_close
                ),
            )
        direction = 1 if action == 0 else -1
        contract = float(self.symbols[symbol]["trade_contract_size"])
        return (price_close - price_open) * direction * volume * contract

    def calculate_total_profit(self) -> float:
        """Calculate current floating profit."""
        total = 0.0
        for position in self.positions.values():
            symbol = str(position.get("symbol", ""))
            if symbol not in self.symbols:
                continue
            tick = self.symbol_info_tick(symbol)
            if tick is None:
                continue
            close_price = tick.bid if int(position.get("type", 0)) == 0 else tick.ask
            profit = self.order_calc_profit(
                int(position.get("type", 0)),
                symbol,
                float(position.get("volume", 0.0)),
                float(position.get("price_open", 0.0)),
                close_price,
            )
            total += profit or 0.0
        return total

    def calculate_total_margin(self) -> float:
        """Calculate current used margin."""
        total = 0.0
        for position in self.positions.values():
            margin = self.order_calc_margin(
                int(position.get("type", 0)),
                str(position.get("symbol", "")),
                float(position.get("volume", 0.0)),
                float(position.get("price_open", 0.0)),
            )
            total += margin or 0.0
        return total

    def execute_trade(self, request: dict[str, Any]) -> SimulatorTradeResult:
        """Execute an MT5-style simulator trade request."""
        if not self._is_connected:
            raise ExternalServiceError("Client is not connected.")
        action = int(request.get("action", -1))
        if action == TRADE_ACTION_DEAL:
            return self._execute_deal(request)
        if action == TRADE_ACTION_PENDING:
            return self._place_pending(request)
        if action == TRADE_ACTION_MODIFY:
            return self._modify_order(request)
        if action == TRADE_ACTION_SLTP:
            return self._modify_position_stops(request)
        if action == TRADE_ACTION_REMOVE:
            return self._cancel_order(request)
        raise ExternalServiceError("Unsupported trade action.")

    def _execute_deal(self, request: dict[str, Any]) -> SimulatorTradeResult:
        if "position" in request:
            return self._close_position(request)
        symbol = str(request.get("symbol", ""))
        if symbol not in self.symbols:
            raise ExternalServiceError("Invalid symbol.")
        ticket = self._next_ticket
        deal = self._next_deal
        self._next_ticket += 1
        self._next_deal += 1
        order_type = int(request.get("type", 0))
        tick = self.symbol_info_tick(symbol)
        if tick is None:
            raise ExternalServiceError("Invalid symbol.")
        price = tick.ask if order_type == 0 else tick.bid
        volume = float(request.get("volume", 0.0))
        now = _now_ts()
        position = {
            "ticket": ticket,
            "symbol": symbol,
            "type": order_type,
            "volume": volume,
            "price_open": price,
            "sl": float(request.get("sl", 0.0)),
            "tp": float(request.get("tp", 0.0)),
            "price_current": price,
            "swap": 0.0,
            "profit": 0.0,
            "magic": int(request.get("magic", 0)),
            "time": now,
            "time_msc": now * 1000,
            "time_update": now,
            "time_update_msc": now * 1000,
            "identifier": ticket,
            "comment": str(request.get("comment", "")),
        }
        self.positions[ticket] = position
        self.history_orders[ticket] = {**position, "state": 4}
        self.history_deals[deal] = {**position, "ticket": deal, "order": ticket}
        return SimulatorTradeResult(
            TRADE_RETCODE_DONE,
            ticket,
            deal,
            volume,
            price,
            tick.bid,
            tick.ask,
            "Order executed",
        )

    def _close_position(self, request: dict[str, Any]) -> SimulatorTradeResult:
        ticket = int(request.get("position", 0))
        if ticket not in self.positions:
            raise ExternalServiceError("Position not found.")
        position = self.positions[ticket]
        symbol = str(position.get("symbol", ""))
        if symbol not in self.symbols:
            raise ExternalServiceError("Invalid symbol.")
        close_volume = float(request.get("volume", position["volume"]))
        tick = self.symbol_info_tick(symbol)
        if tick is None:
            raise ExternalServiceError("Invalid symbol.")
        close_price = tick.bid if int(position["type"]) == 0 else tick.ask
        profit = self.order_calc_profit(
            int(position["type"]),
            symbol,
            close_volume,
            float(position["price_open"]),
            close_price,
        )
        self.balance += profit or 0.0
        remaining = round(float(position["volume"]) - close_volume, 10)
        now = _now_ts()
        order_ticket = self._next_ticket
        deal = self._next_deal
        self._next_ticket += 1
        self._next_deal += 1
        close_record = {
            **position,
            "ticket": order_ticket,
            "order": order_ticket,
            "volume": close_volume,
            "time": now,
            "state": 4,
        }
        self.history_orders[order_ticket] = close_record
        self.history_deals[deal] = {**close_record, "ticket": deal}
        if remaining > 0:
            position["volume"] = remaining
        else:
            del self.positions[ticket]
        return SimulatorTradeResult(
            TRADE_RETCODE_DONE,
            order_ticket,
            deal,
            close_volume,
            close_price,
            tick.bid,
            tick.ask,
            "Position closed",
        )

    def _place_pending(self, request: dict[str, Any]) -> SimulatorTradeResult:
        symbol = str(request.get("symbol", ""))
        if symbol not in self.symbols:
            raise ExternalServiceError("Invalid symbol.")
        ticket = self._next_ticket
        self._next_ticket += 1
        now = _now_ts()
        order = {
            "ticket": ticket,
            "symbol": symbol,
            "type": int(request.get("type", 2)),
            "volume_current": float(request.get("volume", 0.0)),
            "volume_initial": float(request.get("volume", 0.0)),
            "price_open": float(request.get("price", 0.0)),
            "sl": float(request.get("sl", 0.0)),
            "tp": float(request.get("tp", 0.0)),
            "magic": int(request.get("magic", 0)),
            "comment": str(request.get("comment", "")),
            "time_setup": now,
            "time": now,
            "state": 1,
        }
        self.orders[ticket] = order
        return SimulatorTradeResult(
            TRADE_RETCODE_DONE,
            ticket,
            0,
            cast("float", order["volume_current"]),
            cast("float", order["price_open"]),
            comment="Pending order placed",
        )

    def _modify_order(self, request: dict[str, Any]) -> SimulatorTradeResult:
        ticket = int(request.get("order", 0))
        if ticket not in self.orders:
            raise ExternalServiceError("Order not found.")
        order = self.orders[ticket]
        if "price" in request:
            order["price_open"] = float(request["price"])
        if "volume" in request:
            order["volume_current"] = float(request["volume"])
        if "sl" in request:
            order["sl"] = float(request["sl"])
        if "tp" in request:
            order["tp"] = float(request["tp"])
        return SimulatorTradeResult(
            TRADE_RETCODE_DONE,
            ticket,
            0,
            float(order["volume_current"]),
            float(order["price_open"]),
            comment="Order modified",
        )

    def _modify_position_stops(self, request: dict[str, Any]) -> SimulatorTradeResult:
        ticket = int(request.get("position", 0))
        if ticket not in self.positions:
            raise ExternalServiceError("Position not found.")
        if "sl" in request:
            self.positions[ticket]["sl"] = float(request["sl"])
        if "tp" in request:
            self.positions[ticket]["tp"] = float(request["tp"])
        return SimulatorTradeResult(
            TRADE_RETCODE_DONE, ticket, 0, comment="SL/TP modified"
        )

    def _cancel_order(self, request: dict[str, Any]) -> SimulatorTradeResult:
        ticket = int(request.get("order", 0))
        if ticket not in self.orders:
            raise ExternalServiceError("Order not found.")
        order = self.orders.pop(ticket)
        order["state"] = 2
        self.history_orders[ticket] = order
        return SimulatorTradeResult(
            TRADE_RETCODE_DONE, ticket, 0, comment="Order canceled"
        )


def _now_ts() -> int:
    """Return current UTC epoch seconds."""
    return int(datetime.now(UTC).timestamp())


def _default_symbols() -> dict[str, dict[str, Any]]:
    """Return default offline symbol metadata."""
    return {
        "EURUSD": {
            "name": "EURUSD",
            "digits": 5,
            "point": 0.00001,
            "trade_tick_size": 0.00001,
            "trade_contract_size": 100000.0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
            "swap_mode": 1,
            "swap_long": -7.6,
            "swap_short": 3.1,
            "bid": 1.10000,
            "ask": 1.10010,
            "last": 1.10005,
            "spread": 10,
            "description": "Euro vs US Dollar",
            "path": "Forex",
            "trade_mode": 4,
        }
    }


def _filter_records(
    records: list[dict[str, Any]],
    *,
    ticket: int | None = None,
    symbol: str | None = None,
    group: str | None = None,
    date_from: int | datetime | None = None,
    date_to: int | datetime | None = None,
) -> list[_RecordView]:
    """Filter MT5-style record dictionaries."""
    start = _to_epoch(date_from)
    end = _to_epoch(date_to)
    filtered = []
    for record in records:
        if ticket is not None and int(record.get("ticket", -1)) != ticket:
            continue
        if symbol is not None and record.get("symbol") != symbol:
            continue
        if group is not None and not fnmatch(str(record.get("symbol", "")), group):
            continue
        record_time = int(record.get("time", record.get("time_setup", 0)))
        if start is not None and record_time < start:
            continue
        if end is not None and record_time > end:
            continue
        filtered.append(_RecordView(record))
    return filtered


def _to_epoch(value: int | datetime | None) -> int | None:
    """Convert date filters to epoch seconds."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return int(value.timestamp())
    return int(value)


def get_simulator_client() -> SimulatorClient:
    """Return the shared simulator client."""
    return SimulatorClient.get_instance()


def get_mt5_client() -> SimulatorClient:
    """Return simulator as an MT5-compatible client."""
    return get_simulator_client()


def get_ctrader_client() -> SimulatorClient:
    """Return simulator as a cTrader-compatible client."""
    return get_simulator_client()


def get_terminal_info() -> SimulatorTerminalInfo:
    """Return terminal info, connecting the simulator if needed."""
    client = get_simulator_client()
    if not client.is_connected():
        client.connect()
    return SimulatorTerminalInfo(connected=client.is_connected())


def get_account_info() -> SimulatorAccountInfo:
    """Return account info, connecting the simulator if needed."""
    client = get_simulator_client()
    if not client.is_connected():
        client.connect()
    return SimulatorAccountInfo(client)


def get_symbol_info(symbol: str) -> SimulatorSymbolInfo | None:
    """Return symbol info."""
    client = get_simulator_client()
    if not client.is_connected():
        client.connect()
    return client.symbol_info(symbol)


def trade(request: dict[str, Any]) -> SimulatorTradeResult:
    """Execute a simulator trade request."""
    client = get_simulator_client()
    if not client.is_connected():
        client.connect()
    return client.execute_trade(request)


def get_position_info(
    *, ticket: int | None = None, symbol: str | None = None
) -> list[_RecordView]:
    """Return filtered open positions."""
    client = get_simulator_client()
    return _filter_records(
        list(client.positions.values()), ticket=ticket, symbol=symbol
    )


def get_order_info(
    *, ticket: int | None = None, symbol: str | None = None
) -> list[_RecordView]:
    """Return filtered pending orders."""
    client = get_simulator_client()
    return _filter_records(list(client.orders.values()), ticket=ticket, symbol=symbol)


def get_history_order_info(
    *,
    ticket: int | None = None,
    group: str | None = None,
    date_from: int | datetime | None = None,
    date_to: int | datetime | None = None,
) -> list[_RecordView]:
    """Return filtered history orders."""
    client = get_simulator_client()
    return _filter_records(
        list(client.history_orders.values()),
        ticket=ticket,
        group=group,
        date_from=date_from,
        date_to=date_to,
    )


def get_history_deal_info(
    *,
    ticket: int | None = None,
    group: str | None = None,
    date_from: int | datetime | None = None,
    date_to: int | datetime | None = None,
) -> list[_RecordView]:
    """Return filtered history deals."""
    client = get_simulator_client()
    return _filter_records(
        list(client.history_deals.values()),
        ticket=ticket,
        group=group,
        date_from=date_from,
        date_to=date_to,
    )
