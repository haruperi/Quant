# ruff: noqa: BLE001, C901, PLR0915, PLR0912, PLR0911
"""MQL5-compatible Trade class wrapping trading operations.

Integrates idempotency checks, concurrency queue locks, parameter validations,
execution readiness gating, connection circuit breakers, synchronous timeouts,
and reconciliation updates.
"""

import concurrent.futures
import threading
import time
from typing import Any

from app.services.brokers.router import get_active_broker_name, get_broker_module
from app.services.trader.account_info import AccountInfo
from app.services.trader.concurrency import ConcurrencyQueue
from app.services.trader.idempotency import IdempotencyService
from app.services.trader.position_info import PositionInfo
from app.services.trader.rate_limiter import get_rate_limiter
from app.services.trader.readiness import ReadinessService
from app.services.trader.reconciliation import ReconciliationService
from app.services.trader.result import (
    BrokerResponseNormalizer,
    NormalizedTradeResult,
    ResultBuilder,
)
from app.services.trader.store import TradeStore, get_default_store
from app.services.trader.symbol_info import SymbolInfo
from app.services.trader.terminal_info import TerminalInfo
from app.services.trader.validation import ValidationService


class Trade:
    """Provides methods for executing trade operations with safety boundaries."""

    # Global tracking of startup reconciliation pass
    _startup_reconciliation_passed = False

    # Graceful shutdown and kill-switch states
    _is_shutting_down = False
    _in_flight_requests = 0
    _in_flight_lock = threading.Lock()
    _kill_switch_active = False
    _bypass_kill_switch = False

    def __init__(self, store: TradeStore | None = None) -> None:
        """Initialize Trade helper with default parameters and services.

        Args:
            store: Optional repository store instance.
        """
        self._symbol: str = ""
        self._magic: int = 99999
        self._deviation: int = 20
        self._filling: int = 1  # Default to ORDER_FILLING_FOK
        self._result: Any = None

        self._store = store or get_default_store()
        self._idempotency = IdempotencyService(self._store)
        self._validation = ValidationService()
        self._readiness = ReadinessService()
        self._reconciliation = ReconciliationService(self._store)
        self._concurrency = ConcurrencyQueue.get_instance()

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

    @staticmethod
    def _attach_trace_context(
        result: NormalizedTradeResult,
        request_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> None:
        """Attach structural trace identifiers to a normalized result.

        Args:
            result: Normalized trade result object.
            request_id: Deterministic request identifier.
            correlation_id: Correlation identifier propagated through execution.
            trace_id: Trace identifier propagated through execution.
        """
        result.request_id = request_id
        result.correlation_id = correlation_id
        result.trace_id = trace_id

    def _send_request(self, request: dict[str, Any]) -> bool:
        """Send a trade request dictionary to the active broker with safety checks.

        Args:
            request: Trade request dictionary.

        Returns:
            bool: True if trade was executed successfully.
        """
        if Trade._kill_switch_active and not Trade._bypass_kill_switch:
            self._result = ResultBuilder.failure(
                "Blocked by active kill switch", retcode=10001
            )
            return False

        with Trade._in_flight_lock:
            if Trade._is_shutting_down:
                self._result = ResultBuilder.failure(
                    "Service is shutting down", retcode=10001
                )
                return False
            Trade._in_flight_requests += 1

        try:
            # 1. Resolve basic parameters for key generation and locking
            acc = AccountInfo()
            account_id = str(acc.login())
            symbol = request.get("symbol", self._symbol)

            if not symbol:
                order_ticket = request.get("order")
                position_ticket = request.get("position")
                if order_ticket:
                    from app.services.trader.order_info import OrderInfo

                    ord_info = OrderInfo()
                    if ord_info.select(order_ticket):
                        symbol = ord_info.symbol()
                if not symbol and position_ticket:
                    pos_info = PositionInfo()
                    if pos_info.select_by_ticket(position_ticket):
                        symbol = pos_info.symbol()
                # Final fallback
                if not symbol:
                    symbol = "GLOBAL"
            if "symbol" not in request and symbol:
                request["symbol"] = symbol

            action_type = request.get("action", 1)
            volume = request.get("volume", 0.0)
            price = request.get("price", 0.0)
            slippage = request.get("deviation", self._deviation)
            active_broker = get_active_broker_name()

            # 2. Idempotency Check
            idem_key = self._idempotency.generate_key(
                account_id, symbol, action_type, volume, price, slippage
            )
            request_id = str(request.get("request_id") or idem_key)
            correlation_id = str(request.get("correlation_id") or request_id)
            trace_id = str(request.get("trace_id") or correlation_id)
            request["request_id"] = request_id
            request["correlation_id"] = correlation_id
            request["trace_id"] = trace_id
            existing = self._idempotency.check_duplicate(idem_key)
            if existing:
                if existing["status"] == "in_progress":
                    self._result = ResultBuilder.failure(
                        "already in progress", retcode=10004
                    )
                    self._attach_trace_context(
                        self._result, request_id, correlation_id, trace_id
                    )
                    return False
                if existing["status"] == "completed":
                    res_dict = existing["result"]
                    self._result = BrokerResponseNormalizer.normalize_response(
                        active_broker, res_dict
                    )
                    self._attach_trace_context(
                        self._result, request_id, correlation_id, trace_id
                    )
                    return self._result.retcode in (10009, 10008, 0)

            # 3. Startup Reconciliation Gate Check
            if (
                self._reconciliation.block_trading_on_startup
                and not Trade._startup_reconciliation_passed
            ):
                # Attempt to run startup reconciliation once
                try:
                    broker = get_broker_module()
                    raw_positions = broker.get_position_info() or []
                    raw_orders = broker.get_order_info() or []

                    # Convert broker models to basic dicts for reconcile
                    live_positions = []
                    for p in raw_positions:
                        live_positions.append(
                            {
                                "ticket": getattr(p, "ticket", 0),
                                "volume": getattr(p, "volume", 0.0),
                                "type": getattr(p, "type", 0),
                                "profit": getattr(p, "profit", 0.0),
                            }
                        )
                    live_orders = []
                    for o in raw_orders:
                        live_orders.append(
                            {
                                "ticket": getattr(o, "ticket", 0),
                                "volume_current": getattr(o, "volume_current", 0.0),
                            }
                        )

                    self._reconciliation.reconcile(
                        live_positions, live_orders, acc.equity()
                    )
                    Trade._startup_reconciliation_passed = True
                except Exception as e:
                    self._result = ResultBuilder.failure(
                        f"Blocked: Startup reconciliation pass failed. Error: {e}",
                        retcode=10010,
                    )
                    return False

            # 4. Sequential Concurrency Lock
            with self._concurrency.lock_sync(account_id, symbol):
                # Mark key in progress
                self._idempotency.register_in_progress(idem_key, request)

                # 5. Readiness verification
                term = TerminalInfo()
                readiness_res = self._readiness.run_execution_readiness_check(
                    active_broker, symbol, term, acc
                )
                if not readiness_res["passed"]:
                    self._result = ResultBuilder.failure(
                        "Readiness check failed: " + ", ".join(readiness_res["errors"]),
                        retcode=10001,
                    )
                    self._attach_trace_context(
                        self._result, request_id, correlation_id, trace_id
                    )
                    self._idempotency.register_completed(
                        idem_key, self._result.to_dict()
                    )
                    return False

                # 6. Parameter Validation & Decimal precision normalization
                try:
                    sym_info = SymbolInfo(symbol)
                    # Ensure symbol specifications are cached/refreshed
                    sym_info.refresh()
                    sanitized_req = self._validation.validate_order_request(
                        request, sym_info, acc
                    )
                except Exception as e:
                    from app.utils.logger import logger

                    logger.exception("Validation failed in Trade._send_request")
                    self._result = ResultBuilder.failure(
                        str(e),
                        retcode=10001,
                    )
                    self._attach_trace_context(
                        self._result, request_id, correlation_id, trace_id
                    )
                    self._idempotency.register_completed(
                        idem_key, self._result.to_dict()
                    )
                    return False

                # 7. Execution of Broker Request with explicit Timeout (5 seconds)
                limiter = get_rate_limiter(active_broker)
                if not limiter.acquire():
                    self._result = ResultBuilder.failure(
                        f"Rate limit exceeded for provider '{active_broker}'.",
                        retcode=10004,
                    )
                    self._attach_trace_context(
                        self._result, request_id, correlation_id, trace_id
                    )
                    self._idempotency.register_completed(
                        idem_key, self._result.to_dict()
                    )
                    return False

                broker = get_broker_module()
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                future = executor.submit(broker.trade, sanitized_req)
                try:
                    raw_result = future.result(timeout=5.0)
                    self._result = ResultBuilder.success(active_broker, raw_result)
                    self._attach_trace_context(
                        self._result, request_id, correlation_id, trace_id
                    )
                except concurrent.futures.TimeoutError:
                    # Timeout represents an Unknown Outcome -> forced reconciliation
                    self._result = ResultBuilder.failure(
                        "Synchronous broker call timed out after 5 seconds. "
                        "Flagged as Unknown Outcome.",
                        retcode=10005,
                    )
                    self._attach_trace_context(
                        self._result, request_id, correlation_id, trace_id
                    )
                    # Trigger forced reconciliation pass
                    try:
                        raw_positions = broker.get_position_info() or []
                        raw_orders = broker.get_order_info() or []
                        live_positions = [
                            {
                                "ticket": getattr(p, "ticket", 0),
                                "volume": getattr(p, "volume", 0.0),
                                "type": getattr(p, "type", 0),
                                "profit": getattr(p, "profit", 0.0),
                            }
                            for p in raw_positions
                        ]
                        live_orders = [
                            {
                                "ticket": getattr(o, "ticket", 0),
                                "volume_current": getattr(o, "volume_current", 0.0),
                            }
                            for o in raw_orders
                        ]
                        self._reconciliation.reconcile(
                            live_positions, live_orders, acc.equity()
                        )
                    except Exception as rec_err:
                        self._result.comment += (
                            f" Forced reconciliation failed: {rec_err}"
                        )
                except Exception as e:
                    # Broker adapter execution error -> set exact string e
                    self._result = ResultBuilder.failure(str(e), retcode=10001)
                    self._attach_trace_context(
                        self._result, request_id, correlation_id, trace_id
                    )
                finally:
                    executor.shutdown(wait=False)

                # 8. Update Local TradeStore State based on result details
                is_success = self._result.retcode in (10009, 10008, 0)
                if is_success:
                    deal_ticket = self._result.deal
                    order_ticket = self._result.order
                    if deal_ticket > 0:
                        self._store.save_execution(deal_ticket, self._result.to_dict())
                        # If this deal opened a position, store it locally
                        if action_type == 1:  # Deal
                            self._store.save_position(
                                deal_ticket,
                                {
                                    "ticket": deal_ticket,
                                    "symbol": symbol,
                                    "volume": volume,
                                    "type": request.get("type", 0),
                                    "price": self._result.price,
                                    "profit": 0.0,
                                },
                            )
                    if order_ticket > 0:
                        self._store.save_order(order_ticket, self._result.to_dict())

                    # If position closing operation succeeded, remove position locally
                    if "position" in request and (
                        request.get("type") in (0, 1)
                        or "close" in str(request.get("comment", "")).lower()
                    ):
                        self._store.delete_position(request["position"])

                # Register completed idempotency log
                self._idempotency.register_completed(idem_key, self._result.to_dict())
                return is_success
        finally:
            with Trade._in_flight_lock:
                Trade._in_flight_requests -= 1

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
            symbol: Optional symbol name.
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
            symbol: Optional symbol name.
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

    @classmethod
    def set_kill_switch(cls, active: bool, flatten_positions: bool = False) -> None:
        """Set the global kill switch state.

        If active, blocks all new trade requests, cancels all active pending
        orders immediately, and flattens all open positions if
        flatten_positions is True.
        """
        cls._kill_switch_active = active
        if active:
            from app.utils.logger import logger

            logger.warning("GLOBAL KILL SWITCH ACTIVATED!")

            cls._bypass_kill_switch = True
            try:
                # Cancel all active pending orders immediately
                try:
                    from app.services.brokers.router import get_broker_module

                    broker = get_broker_module()
                    if broker:
                        raw_orders = broker.get_order_info() or []
                        for o in raw_orders:
                            ticket = getattr(o, "ticket", 0)
                            if ticket > 0:
                                t = cls()
                                t.order_delete(ticket)
                except Exception as e:
                    logger.error(
                        f"Error cancelling orders during kill switch activation: {e}"
                    )

                # Flatten all open positions if flatten_positions is True
                if flatten_positions:
                    try:
                        from app.services.brokers.router import get_broker_module

                        broker = get_broker_module()
                        if broker:
                            raw_positions = broker.get_position_info() or []
                            for p in raw_positions:
                                ticket = getattr(p, "ticket", 0)
                                if ticket > 0:
                                    t = cls()
                                    t.position_close(ticket)
                    except Exception as e:
                        logger.error(
                            "Error flattening positions during kill switch "
                            f"activation: {e}"
                        )
            finally:
                cls._bypass_kill_switch = False

    @classmethod
    def shutdown(cls, timeout: float = 5.0) -> None:
        """Shutdown the trading service gracefully.

        Args:
            timeout: Timeout window in seconds to allow in-flight requests to resolve.
        """
        cls._is_shutting_down = True

        # Allow in-flight requests to resolve
        start_time = time.time()
        while time.time() - start_time < timeout:
            if cls._in_flight_requests <= 0:
                break
            time.sleep(0.1)

        # Flush states using default store and broker module
        try:
            from app.services.brokers.router import get_broker_module
            from app.services.trader.reconciliation import ReconciliationService
            from app.services.trader.store import get_default_store

            store = get_default_store()
            broker = get_broker_module()

            # Reconcile if broker is available and connected
            if broker and hasattr(broker, "get_terminal_info"):
                term_info = broker.get_terminal_info()
                if term_info and getattr(term_info, "connected", False):
                    raw_positions = broker.get_position_info() or []
                    raw_orders = broker.get_order_info() or []

                    live_positions = [
                        {
                            "ticket": getattr(p, "ticket", 0),
                            "volume": getattr(p, "volume", 0.0),
                            "type": getattr(p, "type", 0),
                            "profit": getattr(p, "profit", 0.0),
                        }
                        for p in raw_positions
                    ]

                    live_orders = [
                        {
                            "ticket": getattr(o, "ticket", 0),
                            "volume_current": getattr(o, "volume_current", 0.0),
                        }
                        for o in raw_orders
                    ]

                    recon = ReconciliationService(store)
                    recon.reconcile(live_positions, live_orders, 0.0)
        except Exception as e:
            from app.utils.logger import logger

            logger.error(f"Error during graceful shutdown: {e}")
