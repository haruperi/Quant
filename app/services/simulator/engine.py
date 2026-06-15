# ruff: noqa: ANN401, C901, PLR0912, PLR0915, PLR2004, S105, BLE001, SLF001
"""Core in-memory broker simulator service engine.

This module provides the SimulatorClient class and associated helper wrappers,
offering a fully mockable in-memory trading broker environment.
"""

from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.services.brokers.mt5 import get_mt5_client as get_real_mt5_client
from app.services.simulator.models import (
    SimulatorAccountInfo,
    SimulatorDealInfo,
    SimulatorOrderInfo,
    SimulatorPositionInfo,
    SimulatorSymbolInfo,
    SimulatorTerminalInfo,
    SimulatorTradeResult,
)
from app.utils.errors import ConfigurationError, ExternalServiceError
from app.utils.logger import logger


class SimulatorClient:
    """In-memory trading client simulator.

    Manages connection state, account details, symbols specifications, local
    positions, active pending orders, historical orders, and deals.
    """

    # MT5 Compatibility Constants
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    ORDER_TIME_GTC = 0
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_PENDING = 5
    TRADE_ACTION_SLTP = 6
    TRADE_ACTION_MODIFY = 7
    TRADE_ACTION_REMOVE = 8

    _instance: "SimulatorClient | None" = None

    def __init__(self) -> None:
        """Initialize the SimulatorClient."""
        self._is_connected = False
        self.login = 87654321
        self.password = "simulated_secure_password"  # pragma: allowlist secret
        self.server = "HaruQuant-Simulator"
        self.company = "HaruQuant AI LLC"
        self.currency = "USD"
        self.leverage = 100
        self.balance = 100000.0
        self.credit = 0.0

        self.positions: dict[int, dict[str, Any]] = {}
        self.orders: dict[int, dict[str, Any]] = {}
        self.history_orders: dict[int, dict[str, Any]] = {}
        self.history_deals: dict[int, dict[str, Any]] = {}

        self.symbols: dict[str, dict[str, Any]] = {
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
            },
        }

        self._next_ticket = 100000
        self._next_deal = 500000
        self._error = "Success"
        self._is_mt5_connected = False

        logger.info("SimulatorClient initialized successfully.")

    def connect(self) -> bool:
        """Connect to the in-memory simulator terminal and initialize MT5 if available.

        Returns:
            bool: True.
        """
        self._is_connected = True
        self._is_mt5_connected = False

        logger.info("Initializing MetaTrader 5 inside Simulator...")
        try:
            mt5_client = get_real_mt5_client()
            if mt5_client.connect():
                self._is_mt5_connected = True
                logger.info(
                    "Simulator successfully connected to MetaTrader 5 "
                    "for real specs and calculations."
                )
                for sym in settings.ALL_SYMBOLS:
                    mt5_client.symbol_select(sym, True)
        except Exception as e:
            logger.warning(
                "Simulator failed to connect to MT5 (Error: %s). "
                "Falling back to local offline mode.",
                e,
            )

        logger.info("SimulatorClient connected.")
        return True

    def disconnect(self) -> None:
        """Disconnect/shutdown the connection to the simulator and MetaTrader 5."""
        self._is_connected = False
        if self._is_mt5_connected:
            try:
                get_real_mt5_client().shutdown()
            except Exception as e:
                logger.error("Error shutting down MT5 client from simulator: %s", e)
            self._is_mt5_connected = False
        logger.info("SimulatorClient disconnected.")

    def shutdown(self) -> None:
        """Shut down the client connection (for MT5 compatibility)."""
        self.disconnect()

    def is_connected(self) -> bool:
        """Check if connected to the simulator.

        Returns:
            bool: Connected status.
        """
        return self._is_connected

    def last_error(self) -> str:
        """Get the last error description.

        Returns:
            str: The error string.
        """
        return self._error

    def symbols_total(self) -> int:
        """Get total number of simulated symbols.

        Returns:
            int: Symbol count.
        """
        return len(self.symbols)

    def subscribe_spots(self, symbol: str) -> None:
        """Subscribe to prices for a symbol.

        Args:
            symbol: Symbol name.

        Raises:
            ConfigurationError: If symbol is invalid.
        """
        if symbol not in self.symbols:
            msg = f"Symbol {symbol} not configured in simulator."
            logger.error(msg)
            raise ConfigurationError(msg)
        logger.info("Subscribed to simulated symbol spots: %s", symbol)

    def unsubscribe_spots(self, symbol: str) -> None:
        """Unsubscribe from prices for a symbol.

        Args:
            symbol: Symbol name.
        """
        logger.info("Unsubscribed from simulated symbol spots: %s", symbol)

    def symbol_info_tick(self, symbol: str) -> Any:
        """Get tick rates for a symbol.

        Args:
            symbol: The symbol name.

        Returns:
            Any: Mock tick object with bid, ask, and last, or MT5 tick object.
        """
        if self._is_mt5_connected:
            tick = get_real_mt5_client().symbol_info_tick(symbol)
            if tick is not None:
                return tick

        logger.warning(
            "MT5 not connected. Using simulated tick for %s",
            symbol,
        )
        sym = self.symbols.get(symbol)
        if not sym:
            return None

        class Tick:
            def __init__(self, bid: float, ask: float, last: float) -> None:
                self.bid = bid
                self.ask = ask
                self.last = last

        return Tick(sym["bid"], sym["ask"], sym["last"])

    def calculate_total_profit(self) -> float:
        """Calculate dynamic total floating profit for open positions.

        Returns:
            float: Dynamic profit sum.
        """
        total = 0.0
        for pos in list(self.positions.values()):
            symbol = pos["symbol"]
            sym_data = self.symbols.get(symbol)

            if self._is_mt5_connected:
                tick = get_real_mt5_client().symbol_info_tick(symbol)
                if tick is not None:
                    current_price = tick.bid if pos["type"] == 0 else tick.ask
                    pos["price_current"] = current_price
                    profit = self.order_calc_profit(
                        pos["type"],
                        symbol,
                        pos["volume"],
                        pos["price_open"],
                        current_price,
                    )
                    if profit is not None:
                        pos["profit"] = profit
                    total += pos["profit"]
                    continue

            logger.warning(
                "MT5 not connected. Using simulated profit logic for position %s on %s",
                pos.get("ticket"),
                symbol,
            )
            if sym_data:
                # Update current position price & profit dynamically
                current_price = sym_data["bid"] if pos["type"] == 0 else sym_data["ask"]
                pos["price_current"] = current_price
                diff = (
                    (current_price - pos["price_open"])
                    if pos["type"] == 0
                    else (pos["price_open"] - current_price)
                )
                contract_size = sym_data["trade_contract_size"]
                pos["profit"] = diff * (pos["volume"] * contract_size)
                total += pos["profit"]
        return total

    def calculate_total_margin(self) -> float:
        """Calculate dynamic total margin for open positions.

        Returns:
            float: Total margin.
        """
        total = 0.0
        for pos in list(self.positions.values()):
            margin = self.order_calc_margin(
                pos["type"], pos["symbol"], pos["volume"], pos["price_open"]
            )
            if margin:
                total += margin
        return total

    def order_calc_margin(
        self, action: int, symbol: str, volume: float, price: float
    ) -> float | None:
        """Calculate required margin for an order.

        Args:
            action: 0 for Buy, 1 for Sell.
            symbol: Symbol name.
            volume: Volume in lots.
            price: Price level.

        Returns:
            float | None: Required margin.
        """
        if self._is_mt5_connected:
            margin = get_real_mt5_client().order_calc_margin(
                action, symbol, volume, price
            )
            if margin is not None:
                return float(margin)

        logger.warning(
            "MT5 not connected. Using simulated margin for %s with "
            "volume %s at price %s",
            symbol,
            volume,
            price,
        )

        sym = self.symbols.get(symbol)
        if not sym:
            return None
        contract_size = sym["trade_contract_size"]
        # Standard margin calculation = (Contract Size * Volume * Price) / Leverage
        margin = (contract_size * volume * price) / self.leverage
        return float(margin)

    def order_calc_profit(
        self,
        action: int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float | None:
        """Calculate expected profit.

        Args:
            action: 0 for Buy, 1 for Sell.
            symbol: Symbol name.
            volume: Volume in lots.
            price_open: Open price level.
            price_close: Close price level.

        Returns:
            float | None: Profit.
        """
        if self._is_mt5_connected:
            profit = get_real_mt5_client().order_calc_profit(
                action, symbol, volume, price_open, price_close
            )
            if profit is not None:
                return float(profit)

        logger.warning(
            "MT5 not connected. Using simulated profit logic for %s with "
            "volume %s (open: %s, close: %s)",
            symbol,
            volume,
            price_open,
            price_close,
        )
        sym = self.symbols.get(symbol)
        if not sym:
            return None
        contract_size = sym["trade_contract_size"]
        diff = (price_close - price_open) if action == 0 else (price_open - price_close)
        return float(diff * (volume * contract_size))

    def _get_ticket(self) -> int:
        """Get unique ticket ID.

        Returns:
            int: Ticket.
        """
        self._next_ticket += 1
        return self._next_ticket

    def _get_deal(self) -> int:
        """Get unique deal ID.

        Returns:
            int: Deal ID.
        """
        self._next_deal += 1
        return self._next_deal

    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid in MT5 or configured locally."""
        if self._is_mt5_connected:
            return get_real_mt5_client().symbol_info(symbol) is not None
        logger.warning(
            "MT5 not connected. Using simulated symbol validation for %s",
            symbol,
        )
        return symbol in self.symbols

    def _get_entry_price(self, symbol: str, req_type: int) -> float:
        """Get current entry price (ask for BUY, bid for SELL)."""
        tick = self.symbol_info_tick(symbol)
        if tick is not None:
            return float(tick.ask if req_type == 0 else tick.bid)

        sym_data = self.symbols.get(symbol, {})
        return float(
            sym_data.get("ask", 0.0) if req_type == 0 else sym_data.get("bid", 0.0)
        )

    def _get_close_price(self, symbol: str, pos_type: int) -> float:
        """Get current close price for position (bid for BUY, ask for SELL)."""
        tick = self.symbol_info_tick(symbol)
        if tick is not None:
            return float(tick.bid if pos_type == 0 else tick.ask)

        sym_data = self.symbols.get(symbol, {})
        return float(
            sym_data.get("bid", 0.0) if pos_type == 0 else sym_data.get("ask", 0.0)
        )

    def execute_trade(self, request: dict[str, Any]) -> SimulatorTradeResult:
        """Execute a trade request on the simulator in-memory engine.

        Args:
            request: The trading parameters dictionary.

        Returns:
            SimulatorTradeResult: The transaction execution outcome.

        Raises:
            ExternalServiceError: If the request is invalid or connection fails.
        """
        if not self._is_connected:
            raise ExternalServiceError(
                "Client is not connected.", code="BROKER_UNAVAILABLE"
            )

        action = request.get("action")
        symbol = request.get("symbol", "")
        volume = request.get("volume", 0.0)
        req_type = request.get("type", 0)

        # 1. Close/Partial Close Position (TRADE_ACTION_DEAL + Position ID)
        if action == 1 and request.get("position") is not None:
            pos_ticket = request["position"]
            if pos_ticket not in self.positions:
                raise ExternalServiceError("Position not found.", code="INVALID_INPUT")
            pos = self.positions[pos_ticket]

            close_vol = min(volume, pos["volume"])
            if not self._is_valid_symbol(pos["symbol"]):
                raise ExternalServiceError("Invalid symbol.", code="INVALID_INPUT")

            close_price = self._get_close_price(pos["symbol"], pos["type"])
            profit = self.order_calc_profit(
                pos["type"], pos["symbol"], close_vol, pos["price_open"], close_price
            )
            if profit is None:
                profit = 0.0

            # Adjust Balance
            self.balance += profit

            # Create close order history
            ord_ticket = self._get_ticket()
            now_ts = int(datetime.now(UTC).timestamp())
            ord_data = {
                "ticket": ord_ticket,
                "symbol": pos["symbol"],
                "type": 1 if pos["type"] == 0 else 0,
                "volume_initial": close_vol,
                "volume_current": 0.0,
                "price_open": close_price,
                "sl": pos["sl"],
                "tp": pos["tp"],
                "price_current": close_price,
                "price_stoplimit": 0.0,
                "magic": request.get("magic", 0),
                "time_setup": now_ts,
                "time_setup_msc": now_ts * 1000,
                "time_expiration": 0,
                "time_done": now_ts,
                "time_done_msc": now_ts * 1000,
                "state": 4,
                "position_id": pos_ticket,
                "position_by_id": 0,
                "comment": request.get("comment", ""),
            }
            self.history_orders[ord_ticket] = ord_data

            # Create close deal history
            deal_ticket = self._get_deal()
            deal_data = {
                "ticket": deal_ticket,
                "order": ord_ticket,
                "position_id": pos_ticket,
                "symbol": pos["symbol"],
                "volume": close_vol,
                "price": close_price,
                "type": 1 if pos["type"] == 0 else 0,
                "entry": 1,
                "time": now_ts,
                "time_msc": now_ts * 1000,
                "commission": 0.0,
                "profit": profit,
                "swap": 0.0,
                "magic": request.get("magic", 0),
                "comment": request.get("comment", ""),
            }
            self.history_deals[deal_ticket] = deal_data

            # Update/Remove position
            if close_vol >= pos["volume"]:
                del self.positions[pos_ticket]
            else:
                pos["volume"] -= close_vol

            return SimulatorTradeResult(
                ord_ticket, deal_ticket, comment="Position closed"
            )

        # 2. Modify Position SL/TP (TRADE_ACTION_SLTP)
        if action in (3, 6):
            pos_ticket = request.get("position")
            if not pos_ticket or pos_ticket not in self.positions:
                raise ExternalServiceError("Position not found.", code="INVALID_INPUT")
            pos = self.positions[pos_ticket]
            pos["sl"] = request.get("sl", pos["sl"])
            pos["tp"] = request.get("tp", pos["tp"])
            pos["time_update"] = int(datetime.now(UTC).timestamp())
            pos["time_update_msc"] = pos["time_update"] * 1000
            return SimulatorTradeResult(pos_ticket, 0, comment="SL/TP modified")

        # 3. Cancel Pending Order (TRADE_ACTION_REMOVE)
        if action in (4, 8):
            cancel_ticket = request.get("order")
            if not cancel_ticket or cancel_ticket not in self.orders:
                raise ExternalServiceError("Order not found.", code="INVALID_INPUT")
            ord_data = self.orders.pop(cancel_ticket)
            ord_data["state"] = 2  # Canceled
            now_ts = int(datetime.now(UTC).timestamp())
            ord_data["time_done"] = now_ts
            ord_data["time_done_msc"] = now_ts * 1000
            self.history_orders[cancel_ticket] = ord_data
            return SimulatorTradeResult(cancel_ticket, 0, comment="Order canceled")

        # 4. Modify Pending Order (TRADE_ACTION_MODIFY)
        if action in (2, 7):
            modify_ticket = request.get("order")
            if not modify_ticket or modify_ticket not in self.orders:
                raise ExternalServiceError("Order not found.", code="INVALID_INPUT")
            ord_data = self.orders[modify_ticket]
            ord_data["price_open"] = request.get("price", ord_data["price_open"])
            ord_data["volume_current"] = request.get(
                "volume", ord_data["volume_current"]
            )
            ord_data["sl"] = request.get("sl", ord_data["sl"])
            ord_data["tp"] = request.get("tp", ord_data["tp"])
            return SimulatorTradeResult(modify_ticket, 0, comment="Order modified")

        # 5. Place Pending Order (TRADE_ACTION_PENDING)
        if action == 5:
            if not self._is_valid_symbol(symbol):
                raise ExternalServiceError("Invalid symbol.", code="INVALID_INPUT")
            ord_ticket = self._get_ticket()
            now_ts = int(datetime.now(UTC).timestamp())
            tick = self.symbol_info_tick(symbol)
            price_current = tick.bid if tick is not None else 0.0
            ord_data = {
                "ticket": ord_ticket,
                "symbol": symbol,
                "type": req_type,
                "volume_initial": volume,
                "volume_current": volume,
                "price_open": request.get("price", 0.0),
                "sl": request.get("sl", 0.0),
                "tp": request.get("tp", 0.0),
                "price_current": price_current,
                "price_stoplimit": request.get("price_stoplimit", 0.0),
                "magic": request.get("magic", 0),
                "time_setup": now_ts,
                "time_setup_msc": now_ts * 1000,
                "time_expiration": request.get("type_time", 0),
                "time_done": 0,
                "time_done_msc": 0,
                "state": 1,
                "position_id": 0,
                "position_by_id": 0,
                "comment": request.get("comment", ""),
            }
            self.orders[ord_ticket] = ord_data
            return SimulatorTradeResult(ord_ticket, 0, comment="Pending order placed")

        # 6. Market Open Deal (TRADE_ACTION_DEAL)
        if action == 1:
            if not self._is_valid_symbol(symbol):
                raise ExternalServiceError("Invalid symbol.", code="INVALID_INPUT")
            now_ts = int(datetime.now(UTC).timestamp())
            ord_ticket = self._get_ticket()

            # For Buy orders we enter on ask, Sell orders enter on bid
            entry_price = self._get_entry_price(symbol, req_type)

            # Create order history
            ord_data = {
                "ticket": ord_ticket,
                "symbol": symbol,
                "type": req_type,
                "volume_initial": volume,
                "volume_current": 0.0,
                "price_open": entry_price,
                "sl": request.get("sl", 0.0),
                "tp": request.get("tp", 0.0),
                "price_current": entry_price,
                "price_stoplimit": 0.0,
                "magic": request.get("magic", 0),
                "time_setup": now_ts,
                "time_setup_msc": now_ts * 1000,
                "time_expiration": 0,
                "time_done": now_ts,
                "time_done_msc": now_ts * 1000,
                "state": 4,
                "position_id": ord_ticket,
                "position_by_id": 0,
                "comment": request.get("comment", ""),
            }
            self.history_orders[ord_ticket] = ord_data

            # Create deal record
            deal_ticket = self._get_deal()
            deal_data = {
                "ticket": deal_ticket,
                "order": ord_ticket,
                "position_id": ord_ticket,
                "symbol": symbol,
                "volume": volume,
                "price": entry_price,
                "type": req_type,
                "entry": 0,
                "time": now_ts,
                "time_msc": now_ts * 1000,
                "commission": 0.0,
                "profit": 0.0,
                "swap": 0.0,
                "magic": request.get("magic", 0),
                "comment": request.get("comment", ""),
            }
            self.history_deals[deal_ticket] = deal_data

            # Add to active open positions
            pos_data = {
                "ticket": ord_ticket,
                "symbol": symbol,
                "type": req_type,
                "volume": volume,
                "price_open": entry_price,
                "sl": request.get("sl", 0.0),
                "tp": request.get("tp", 0.0),
                "price_current": entry_price,
                "swap": 0.0,
                "profit": 0.0,
                "magic": request.get("magic", 0),
                "time": now_ts,
                "time_msc": now_ts * 1000,
                "time_update": now_ts,
                "time_update_msc": now_ts * 1000,
                "identifier": ord_ticket,
                "comment": request.get("comment", ""),
            }
            self.positions[ord_ticket] = pos_data

            return SimulatorTradeResult(
                ord_ticket, deal_ticket, comment="Order executed"
            )

        err_msg = f"Unsupported trade action: {action}"
        raise ExternalServiceError(err_msg, code="INVALID_INPUT")

    @classmethod
    def get_instance(cls) -> "SimulatorClient":
        """Get the shared singleton instance of SimulatorClient."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Getter and wrapper functions matching standard broker adapters
def get_simulator_client() -> SimulatorClient:
    """Get the shared singleton instance of SimulatorClient.

    Returns:
        SimulatorClient: Client singleton.
    """
    return SimulatorClient.get_instance()


def _ensure_connected() -> None:
    """Ensure client is connected."""
    client = get_simulator_client()
    if not client.is_connected():
        client.connect()


def get_terminal_info() -> SimulatorTerminalInfo:
    """Get the terminal settings and status.

    Returns:
        SimulatorTerminalInfo: Info wrapper.
    """
    _ensure_connected()
    client = get_simulator_client()
    return SimulatorTerminalInfo(client.is_connected())


def get_account_info() -> SimulatorAccountInfo:
    """Get info on the current trading account.

    Returns:
        SimulatorAccountInfo: Account info wrapper.
    """
    _ensure_connected()
    client = get_simulator_client()
    return SimulatorAccountInfo(client)


def get_symbol_info(symbol: str) -> SimulatorSymbolInfo | None:
    """Get info about a symbol.

    Args:
        symbol: Instrument name.

    Returns:
        SimulatorSymbolInfo | None: Symbol info or None.
    """
    _ensure_connected()
    client = get_simulator_client()
    if client._is_mt5_connected:
        sym_info = get_real_mt5_client().symbol_info(symbol)
        if sym_info is not None:
            return SimulatorSymbolInfo(sym_info)
    logger.warning(
        "MT5 not connected. Using simulated symbol specs for %s",
        symbol,
    )
    sym_data = client.symbols.get(symbol)
    if not sym_data:
        return None
    return SimulatorSymbolInfo(sym_data)


def get_position_info(
    symbol: str | None = None, ticket: int | None = None
) -> list[SimulatorPositionInfo]:
    """Get active open positions.

    Args:
        symbol: Optional filter.
        ticket: Optional filter.

    Returns:
        list[SimulatorPositionInfo]: List of open positions.
    """
    _ensure_connected()
    client = get_simulator_client()
    # Force updating floating profit calculation on positions fetch
    client.calculate_total_profit()

    results = []
    for pos in client.positions.values():
        if symbol is not None and pos["symbol"] != symbol:
            continue
        if ticket is not None and pos["ticket"] != ticket:
            continue
        results.append(SimulatorPositionInfo(pos))
    return results


def get_order_info(
    symbol: str | None = None, ticket: int | None = None
) -> list[SimulatorOrderInfo]:
    """Get active pending orders.

    Args:
        symbol: Optional filter.
        ticket: Optional filter.

    Returns:
        list[SimulatorOrderInfo]: List of active pending orders.
    """
    _ensure_connected()
    client = get_simulator_client()
    results = []
    for ord_data in client.orders.values():
        if symbol is not None and ord_data["symbol"] != symbol:
            continue
        if ticket is not None and ord_data["ticket"] != ticket:
            continue
        results.append(SimulatorOrderInfo(ord_data))
    return results


def get_history_order_info(
    date_from: Any = None,
    date_to: Any = None,
    group: str | None = None,
    ticket: int | None = None,
) -> list[SimulatorOrderInfo]:
    """Get historical orders.

    Args:
        date_from: Date filter.
        date_to: Date filter.
        group: Symbol group filter.
        ticket: Ticket filter.

    Returns:
        list[SimulatorOrderInfo]: List of historical orders.
    """
    _ensure_connected()
    client = get_simulator_client()
    results = []
    for ord_data in client.history_orders.values():
        if ticket is not None and ord_data["ticket"] != ticket:
            continue
        if group is not None:
            clean_group = group.replace("*", "").upper()
            if clean_group not in ord_data["symbol"].upper():
                continue
        # Standard range filter check if datetime or int provided
        time_done = ord_data["time_done"]
        if date_from is not None:
            limit = (
                int(date_from.timestamp())
                if hasattr(date_from, "timestamp")
                else int(date_from)
            )
            if time_done < limit:
                continue
        if date_to is not None:
            limit = (
                int(date_to.timestamp())
                if hasattr(date_to, "timestamp")
                else int(date_to)
            )
            if time_done > limit:
                continue
        results.append(SimulatorOrderInfo(ord_data))
    return results


def get_history_deal_info(
    date_from: Any = None,
    date_to: Any = None,
    group: str | None = None,
    ticket: int | None = None,
) -> list[SimulatorDealInfo]:
    """Get historical deals.

    Args:
        date_from: Date filter.
        date_to: Date filter.
        group: Symbol group filter.
        ticket: Ticket filter.

    Returns:
        list[SimulatorDealInfo]: List of historical deals.
    """
    _ensure_connected()
    client = get_simulator_client()
    results = []
    for deal_data in client.history_deals.values():
        if ticket is not None and deal_data["ticket"] != ticket:
            continue
        if group is not None:
            clean_group = group.replace("*", "").upper()
            if clean_group not in deal_data["symbol"].upper():
                continue
        time_done = deal_data["time"]
        if date_from is not None:
            limit = (
                int(date_from.timestamp())
                if hasattr(date_from, "timestamp")
                else int(date_from)
            )
            if time_done < limit:
                continue
        if date_to is not None:
            limit = (
                int(date_to.timestamp())
                if hasattr(date_to, "timestamp")
                else int(date_to)
            )
            if time_done > limit:
                continue
        results.append(SimulatorDealInfo(deal_data))
    return results


def trade(request: dict[str, Any]) -> SimulatorTradeResult:
    """Execute trading order against the simulator engine.

    Args:
        request: Order specification parameters.

    Returns:
        SimulatorTradeResult: Execution results.
    """
    _ensure_connected()
    client = get_simulator_client()
    return client.execute_trade(request)


def get_mt5_client() -> SimulatorClient:
    """Get the shared singleton instance of SimulatorClient for MT5 compatibility.

    Returns:
        SimulatorClient: Client singleton.
    """
    return SimulatorClient.get_instance()


def get_ctrader_client() -> SimulatorClient:
    """Get the shared singleton instance of SimulatorClient for cTrader compatibility.

    Returns:
        SimulatorClient: Client singleton.
    """
    return SimulatorClient.get_instance()
