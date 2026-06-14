# ruff: noqa: TRY300, BLE001, PLR0913
"""MQL5-compatible Trade class wrapping trading operations.

Provides easy access to sending trade requests to the active broker.
"""

from typing import Any

from app.services.trader.position_info import PositionInfo
from app.services.trader.resolver import get_broker_module
from app.services.trader.symbol_info import SymbolInfo


class Trade:
    """Provides methods for executing trade operations."""

    def __init__(self) -> None:
        """Initialize Trade helper with default parameters."""
        self._symbol: str = ""
        self._magic: int = 99999
        self._deviation: int = 20
        self._filling: int = 1  # Default to ORDER_FILLING_FOK
        self._result: Any = None

    def set_symbol(self, symbol: str) -> None:
        """Set default symbol for trade operations.

        Args:
            symbol: Symbol name.
        """
        self._symbol = symbol

    def set_order_filling(self, filling: int) -> None:
        """Set order execution filling mode.

        Args:
            filling: Filling mode.
        """
        self._filling = filling

    def set_deviation_in_points(self, deviation: int) -> None:
        """Set maximum price deviation in points.

        Args:
            deviation: Deviation points.
        """
        self._deviation = deviation

    def set_expert_magic_number(self, magic: int) -> None:
        """Set Expert Advisor magic number.

        Args:
            magic: Magic identifier.
        """
        self._magic = magic

    def result_retcode(self) -> int:
        """Get result code of the last execution.

        Returns:
            int: Return code.
        """
        return int(getattr(self._result, "retcode", 0))

    def result_deal(self) -> int:
        """Get deal ticket of the last execution.

        Returns:
            int: Deal ticket.
        """
        return int(getattr(self._result, "deal", 0))

    def result_order(self) -> int:
        """Get order ticket of the last execution.

        Returns:
            int: Order ticket.
        """
        return int(getattr(self._result, "order", 0))

    def result_volume(self) -> float:
        """Get volume of the last executed request.

        Returns:
            float: Volume.
        """
        return float(getattr(self._result, "volume", 0.0))

    def result_price(self) -> float:
        """Get price of the last executed request.

        Returns:
            float: Price.
        """
        return float(getattr(self._result, "price", 0.0))

    def result_bid(self) -> float:
        """Get current bid price of the last executed request.

        Returns:
            float: Bid.
        """
        return float(getattr(self._result, "bid", 0.0))

    def result_ask(self) -> float:
        """Get current ask price of the last executed request.

        Returns:
            float: Ask.
        """
        return float(getattr(self._result, "ask", 0.0))

    def result_comment(self) -> str:
        """Get comments on the execution results.

        Returns:
            str: Comment string.
        """
        return str(getattr(self._result, "comment", ""))

    def _send_request(self, request: dict[str, Any]) -> bool:
        """Send a trade request dictionary to the active broker.

        Args:
            request: Trade request dictionary.

        Returns:
            bool: True if trade was executed successfully.
        """
        try:
            broker = get_broker_module()
            self._result = broker.trade(request)
            return True
        except Exception as e:

            class DummyResult:
                def __init__(self, err_msg: str) -> None:
                    self.retcode = 10001
                    self.deal = 0
                    self.order = 0
                    self.volume = 0.0
                    self.price = 0.0
                    self.bid = 0.0
                    self.ask = 0.0
                    self.comment = err_msg

            self._result = DummyResult(str(e))
            return False

    def buy(
        self,
        volume: float,
        symbol: str | None = None,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "",
    ) -> bool:
        """Open a long market position.

        Args:
            volume: Lot volume size.
            symbol: Optional symbol name (defaults to set_symbol).
            price: Open price (0.0 uses current ask price).
            sl: Stop loss level.
            tp: Take profit level.
            comment: Order comment.

        Returns:
            bool: True if execution succeeded.
        """
        target_symbol = symbol or self._symbol
        if not target_symbol:
            return False

        if price == 0.0:
            sym = SymbolInfo(target_symbol)
            price = sym.ask()

        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )

        order_type = getattr(client, "ORDER_TYPE_BUY", 0)
        action = getattr(client, "TRADE_ACTION_DEAL", 1)
        order_time = getattr(client, "ORDER_TIME_GTC", 1)

        request = {
            "action": action,
            "symbol": target_symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": self._deviation,
            "magic": self._magic,
            "comment": comment or "Buy market order",
            "type_time": order_time,
            "type_filling": self._filling,
        }
        return self._send_request(request)

    def sell(
        self,
        volume: float,
        symbol: str | None = None,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "",
    ) -> bool:
        """Open a short market position.

        Args:
            volume: Lot volume size.
            symbol: Optional symbol name (defaults to set_symbol).
            price: Open price (0.0 uses current bid price).
            sl: Stop loss level.
            tp: Take profit level.
            comment: Order comment.

        Returns:
            bool: True if execution succeeded.
        """
        target_symbol = symbol or self._symbol
        if not target_symbol:
            return False

        if price == 0.0:
            sym = SymbolInfo(target_symbol)
            price = sym.bid()

        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )

        order_type = getattr(client, "ORDER_TYPE_SELL", 1)
        action = getattr(client, "TRADE_ACTION_DEAL", 1)
        order_time = getattr(client, "ORDER_TIME_GTC", 1)

        request = {
            "action": action,
            "symbol": target_symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": self._deviation,
            "magic": self._magic,
            "comment": comment or "Sell market order",
            "type_time": order_time,
            "type_filling": self._filling,
        }
        return self._send_request(request)

    def buy_limit(
        self,
        volume: float,
        price: float,
        symbol: str | None = None,
        sl: float = 0.0,
        tp: float = 0.0,
        expiration: int = 0,
        comment: str = "",
    ) -> bool:
        """Place a Buy Limit pending order.

        Args:
            volume: Lot volume size.
            price: Order entry price.
            symbol: Optional symbol name.
            sl: Stop loss level.
            tp: Take profit level.
            expiration: Expiration time.
            comment: Comment.

        Returns:
            bool: True if execution succeeded.
        """
        target_symbol = symbol or self._symbol
        if not target_symbol:
            return False

        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )

        order_type = getattr(client, "ORDER_TYPE_BUY_LIMIT", 2)
        action = getattr(client, "TRADE_ACTION_PENDING", 5)
        order_time = expiration or getattr(client, "ORDER_TIME_GTC", 1)

        request = {
            "action": action,
            "symbol": target_symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": self._deviation,
            "magic": self._magic,
            "comment": comment or "Buy limit order",
            "type_time": order_time,
            "type_filling": self._filling,
        }
        return self._send_request(request)

    def sell_limit(
        self,
        volume: float,
        price: float,
        symbol: str | None = None,
        sl: float = 0.0,
        tp: float = 0.0,
        expiration: int = 0,
        comment: str = "",
    ) -> bool:
        """Place a Sell Limit pending order.

        Args:
            volume: Lot volume size.
            price: Order entry price.
            symbol: Optional symbol name.
            sl: Stop loss level.
            tp: Take profit level.
            expiration: Expiration time.
            comment: Comment.

        Returns:
            bool: True if execution succeeded.
        """
        target_symbol = symbol or self._symbol
        if not target_symbol:
            return False

        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )

        order_type = getattr(client, "ORDER_TYPE_SELL_LIMIT", 3)
        action = getattr(client, "TRADE_ACTION_PENDING", 5)
        order_time = expiration or getattr(client, "ORDER_TIME_GTC", 1)

        request = {
            "action": action,
            "symbol": target_symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": self._deviation,
            "magic": self._magic,
            "comment": comment or "Sell limit order",
            "type_time": order_time,
            "type_filling": self._filling,
        }
        return self._send_request(request)

    def buy_stop(
        self,
        volume: float,
        price: float,
        symbol: str | None = None,
        sl: float = 0.0,
        tp: float = 0.0,
        expiration: int = 0,
        comment: str = "",
    ) -> bool:
        """Place a Buy Stop pending order.

        Args:
            volume: Lot volume size.
            price: Order entry price.
            symbol: Optional symbol name.
            sl: Stop loss level.
            tp: Take profit level.
            expiration: Expiration time.
            comment: Comment.

        Returns:
            bool: True if execution succeeded.
        """
        target_symbol = symbol or self._symbol
        if not target_symbol:
            return False

        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )

        order_type = getattr(client, "ORDER_TYPE_BUY_STOP", 4)
        action = getattr(client, "TRADE_ACTION_PENDING", 5)
        order_time = expiration or getattr(client, "ORDER_TIME_GTC", 1)

        request = {
            "action": action,
            "symbol": target_symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": self._deviation,
            "magic": self._magic,
            "comment": comment or "Buy stop order",
            "type_time": order_time,
            "type_filling": self._filling,
        }
        return self._send_request(request)

    def sell_stop(
        self,
        volume: float,
        price: float,
        symbol: str | None = None,
        sl: float = 0.0,
        tp: float = 0.0,
        expiration: int = 0,
        comment: str = "",
    ) -> bool:
        """Place a Sell Stop pending order.

        Args:
            volume: Lot volume size.
            price: Order entry price.
            symbol: Optional symbol name.
            sl: Stop loss level.
            tp: Take profit level.
            expiration: Expiration time.
            comment: Comment.

        Returns:
            bool: True if execution succeeded.
        """
        target_symbol = symbol or self._symbol
        if not target_symbol:
            return False

        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )

        order_type = getattr(client, "ORDER_TYPE_SELL_STOP", 5)
        action = getattr(client, "TRADE_ACTION_PENDING", 5)
        order_time = expiration or getattr(client, "ORDER_TIME_GTC", 1)

        request = {
            "action": action,
            "symbol": target_symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": self._deviation,
            "magic": self._magic,
            "comment": comment or "Sell stop order",
            "type_time": order_time,
            "type_filling": self._filling,
        }
        return self._send_request(request)

    def position_open(
        self,
        symbol: str,
        order_type: int,
        volume: float,
        price: float,
        sl: float,
        tp: float,
        comment: str = "",
    ) -> bool:
        """Open a position with specified properties.

        Args:
            symbol: Symbol name.
            order_type: Order type (0=Buy, 1=Sell).
            volume: Lot volume size.
            price: Order price.
            sl: Stop loss price.
            tp: Take profit price.
            comment: Comment.

        Returns:
            bool: True if execution succeeded.
        """
        if order_type == 0:
            return self.buy(
                volume, symbol=symbol, price=price, sl=sl, tp=tp, comment=comment
            )
        return self.sell(
            volume, symbol=symbol, price=price, sl=sl, tp=tp, comment=comment
        )

    def position_close(self, symbol_or_ticket: str | int, deviation: int = -1) -> bool:
        """Close an active open position fully.

        Args:
            symbol_or_ticket: Position ticket integer or symbol name string.
            deviation: Price deviation in points.

        Returns:
            bool: True if position closed successfully.
        """
        pos = PositionInfo()
        if isinstance(symbol_or_ticket, int):
            if not pos.select_by_ticket(symbol_or_ticket):
                return False
        elif not pos.select(symbol_or_ticket):
            return False

        symbol = pos.symbol()
        volume = pos.volume()
        ticket = pos.ticket()
        pos_type = pos.type()

        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )

        close_type = (
            getattr(client, "ORDER_TYPE_SELL", 1)
            if pos_type == 0
            else getattr(client, "ORDER_TYPE_BUY", 0)
        )
        action = getattr(client, "TRADE_ACTION_DEAL", 1)
        order_time = getattr(client, "ORDER_TIME_GTC", 1)

        sym = SymbolInfo(symbol)
        price = sym.bid() if pos_type == 0 else sym.ask()

        request = {
            "action": action,
            "symbol": symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": deviation if deviation >= 0 else self._deviation,
            "magic": self._magic,
            "comment": "Close position",
            "type_time": order_time,
            "type_filling": self._filling,
        }
        return self._send_request(request)

    def position_modify(
        self, symbol_or_ticket: str | int, sl: float, tp: float
    ) -> bool:
        """Modify SL/TP of an active open position.

        Args:
            symbol_or_ticket: Position ticket integer or symbol name string.
            sl: Stop loss level price.
            tp: Take profit level price.

        Returns:
            bool: True if modification succeeded.
        """
        pos = PositionInfo()
        if isinstance(symbol_or_ticket, int):
            if not pos.select_by_ticket(symbol_or_ticket):
                return False
        elif not pos.select(symbol_or_ticket):
            return False

        ticket = pos.ticket()
        symbol = pos.symbol()

        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )
        action = getattr(client, "TRADE_ACTION_SLTP", 3)

        request = {
            "action": action,
            "symbol": symbol,
            "position": ticket,
            "sl": sl,
            "tp": tp,
        }
        return self._send_request(request)

    def order_modify(self, ticket: int, price: float, sl: float, tp: float) -> bool:
        """Modify a pending order properties.

        Args:
            ticket: Pending order ticket.
            price: New entry price.
            sl: New stop loss level.
            tp: New take profit level.

        Returns:
            bool: True if modification succeeded.
        """
        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )
        action = getattr(client, "TRADE_ACTION_MODIFY", 2)

        request = {
            "action": action,
            "order": ticket,
            "price": price,
            "sl": sl,
            "tp": tp,
        }
        return self._send_request(request)

    def order_delete(self, ticket: int) -> bool:
        """Cancel/Delete a pending order.

        Args:
            ticket: Pending order ticket.

        Returns:
            bool: True if cancellation succeeded.
        """
        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )
        action = getattr(client, "TRADE_ACTION_REMOVE", 4)

        request = {
            "action": action,
            "order": ticket,
        }
        return self._send_request(request)
