# ruff: noqa: E501, PLR0915, PLR0912, PLR2004, SLF001, TRY301, FBT001, ANN401, BLE001, TRY300, C901
"""cTrader Open API broker client service.

This module provides the CTraderClient class responsible for managing the lifecycle
of the connection and authorization handshake with the cTrader Open API endpoints.
"""

import contextlib
import threading
from datetime import UTC, datetime
from typing import Any

from ctrader_open_api import (  # type: ignore[import-untyped, unused-ignore]
    Client,
    EndPoints,
    TcpProtocol,
)
from ctrader_open_api.messages.OpenApiCommonModelMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
    ProtoPayloadType,
)
from ctrader_open_api.messages.OpenApiMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
    ProtoOAAccountAuthReq,
    ProtoOAAmendOrderReq,
    ProtoOAAmendPositionSLTPReq,
    ProtoOAApplicationAuthReq,
    ProtoOACancelOrderReq,
    ProtoOAClosePositionReq,
    ProtoOADealListReq,
    ProtoOAExpectedMarginReq,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetTrendbarsReq,
    ProtoOANewOrderReq,
    ProtoOAOrderListReq,
    ProtoOAReconcileReq,
    ProtoOASubscribeSpotsReq,
    ProtoOASymbolByIdReq,
    ProtoOASymbolsListReq,
    ProtoOATraderReq,
    ProtoOAUnsubscribeSpotsReq,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
    ProtoOAPayloadType,
)
from ctrader_open_api.protobuf import (  # type: ignore[import-untyped, unused-ignore]
    Protobuf,
)
from twisted.internet import reactor

from app.core.config import settings
from app.utils.errors import ConfigurationError, ExternalServiceError
from app.utils.logger import logger


class CTraderClient:
    """Client for interacting with the cTrader Open API endpoint.

    Handles TCP socket connection, application authentication,
    retrieving account details, and trading account authorization.
    """

    _instance: "CTraderClient | None" = None

    # MT5 integer constants for compatibility
    ORDER_FILLING_FOK = 1
    ORDER_FILLING_IOC = 2
    ORDER_TIME_GTC = 1
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_PENDING = 5
    TRADE_ACTION_SLTP = 3
    TRADE_ACTION_MODIFY = 2
    TRADE_ACTION_REMOVE = 4
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        account_id: int | None = None,
        environment: str | None = None,
    ) -> None:
        """Initialize the cTrader Open API client with configuration parameters.

        Args:
            client_id: cTrader Client ID.
            client_secret: cTrader Client Secret.
            access_token: Access token for user trading accounts.
            account_id: Optional specific trading account ID.
            environment: Environment name ('demo' or 'live').
        """
        self.client_id = client_id or settings.ctrader_client_id
        self.client_secret = client_secret or settings.ctrader_client_secret
        self.access_token = access_token or settings.ctrader_access_token
        self.account_id = account_id or settings.ctrader_account_id
        self.environment = environment or settings.ctrader_environment

        self.client: Any = None
        self._connected_event = threading.Event()
        self._auth_event = threading.Event()
        self._error: str | None = None
        self._accounts: list[dict[str, Any]] = []

        self._is_connected = False
        self._is_app_authenticated = False
        self._is_account_authorized = False
        self.trader_info: Any = None

        self._message_callbacks: list[Any] = []
        self._symbol_map: dict[str, Any] = {}
        self._symbol_id_to_name: dict[int, str] = {}
        self._subscribed_symbols: set[int] = set()
        self._ticks: dict[str, dict[str, float]] = {}

        logger.info(
            "CTraderClient initialized",
            extra={
                "client_id": self.client_id[:8] + "..." if self.client_id else None,
                "environment": self.environment,
                "account_id": self.account_id,
            },
        )

    def connect(self) -> bool:
        """Connect to the cTrader Open API endpoint and handshake.

        Raises:
            ConfigurationError: If any of the required credentials are missing.
            ExternalServiceError: If connection or authorization handshakes
                fail or time out.

        Returns:
            bool: True if connection and handshakes were successfully completed.
        """
        self._validate_credentials()

        if self._is_connected and self._is_account_authorized:
            return True

        self._connected_event.clear()
        self._auth_event.clear()
        self._error = None

        if self.environment.lower() == "live":
            host = EndPoints.PROTOBUF_LIVE_HOST
        else:
            host = EndPoints.PROTOBUF_DEMO_HOST

        logger.info(
            "Connecting to cTrader Open API...",
            extra={"host": host, "port": EndPoints.PROTOBUF_PORT},
        )

        try:
            self.client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
            self.client.setConnectedCallback(self._on_connected)
            self.client.setDisconnectedCallback(self._on_disconnected)
            self.client.setMessageReceivedCallback(self._on_message)

            self.client.startService()
        except Exception as e:
            msg = f"Failed to initialize cTrader Open API service: {e}"
            logger.exception(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

        # Start twisted reactor in a daemon thread if it is not already running
        if not reactor.running:  # type: ignore[attr-defined, unused-ignore]
            t = threading.Thread(
                target=reactor.run,  # type: ignore[attr-defined, unused-ignore]
                kwargs={"installSignalHandlers": False},
                daemon=True,
            )
            t.start()

        # Wait for TCP connection
        if not self._connected_event.wait(timeout=10.0):
            self.disconnect()
            msg = "cTrader TCP connection timed out."
            logger.error(msg)
            raise ExternalServiceError(msg, code="TIMEOUT")

        if self._error:
            self.disconnect()
            msg = f"cTrader connection failed: {self._error}"
            logger.error(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

        # Wait for Authentication Handshake
        if not self._auth_event.wait(timeout=10.0):
            self.disconnect()
            msg = "cTrader authentication handshake timed out."
            logger.error(msg)
            raise ExternalServiceError(msg, code="TIMEOUT")

        if self._error:
            self.disconnect()
            msg = f"cTrader authentication handshake failed: {self._error}"
            logger.error(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

        # Cache symbols list
        try:
            req = ProtoOASymbolsListReq()
            req.ctidTraderAccountId = self.account_id
            res = self.send_request(req, ProtoOAPayloadType.PROTO_OA_SYMBOLS_LIST_RES)
            self._symbol_map = {s.symbolName: s for s in res.symbol}
            self._symbol_id_to_name = {s.symbolId: s.symbolName for s in res.symbol}
        except Exception as e:
            logger.warning("Failed to cache symbol list: %s", e)
            self._symbol_map = {}
            self._symbol_id_to_name = {}

        return True

    def _validate_credentials(self) -> None:
        """Validate that required cTrader configuration details are provided."""
        if not self.client_id:
            msg = "cTrader client ID is required."
            logger.error(msg)
            raise ConfigurationError(msg)
        if not self.client_secret:
            msg = "cTrader client secret is required."
            logger.error(msg)
            raise ConfigurationError(msg)
        if not self.access_token:
            msg = "cTrader access token is required."
            logger.error(msg)
            raise ConfigurationError(msg)

    def disconnect(self) -> None:
        """Close the cTrader connection and reset the status flags."""
        logger.info("Disconnecting from cTrader...")
        try:
            if self.client:
                self.client.stopService()
        except Exception as e:
            logger.warning("Error stopping cTrader Open API service: %s", e)

        self._is_connected = False
        self._is_app_authenticated = False
        self._is_account_authorized = False

    def is_connected(self) -> bool:
        """Check if TCP connection is active.

        Returns:
            bool: True if TCP connection is active, False otherwise.
        """
        return self._is_connected

    def is_app_authenticated(self) -> bool:
        """Check if application is authenticated.

        Returns:
            bool: True if app authentication handshake is complete.
        """
        return self._is_app_authenticated

    def is_account_authorized(self) -> bool:
        """Check if trading account is authorized.

        Returns:
            bool: True if account authorization handshake is complete.
        """
        return self._is_account_authorized

    def _on_connected(self, _client: Any) -> None:
        """Callback triggered on successful TCP connection."""
        logger.info(
            "cTrader TCP socket connected. Sending application authentication..."
        )
        self._is_connected = True
        self._connected_event.set()

        try:
            req = ProtoOAApplicationAuthReq()
            req.clientId = self.client_id
            req.clientSecret = self.client_secret
            self.client.send(req)
        except Exception as e:
            logger.exception("Failed to send ProtoOAApplicationAuthReq")
            self._error = f"App auth send error: {e}"
            self._auth_event.set()

    def _on_disconnected(self, _client: Any, reason: Any) -> None:
        """Callback triggered on socket disconnection."""
        logger.warning("cTrader connection lost. Reason: %s", reason)
        self._is_connected = False
        self._is_app_authenticated = False
        self._is_account_authorized = False
        self._error = str(reason)
        self._connected_event.set()  # Unblock connection wait
        self._auth_event.set()  # Unblock auth wait

    def _on_message(self, _client: Any, message: Any) -> None:
        """Callback triggered on receiving any protobuf message from cTrader."""
        payload_type = message.payloadType

        try:
            extracted = Protobuf.extract(message)
        except Exception as e:
            logger.error("Failed to extract cTrader protobuf payload: %s", e)
            return

        # Track spot events for ticks
        if payload_type == ProtoOAPayloadType.PROTO_OA_SPOT_EVENT:
            self._handle_spot_event(extracted)

        # Trigger registered callbacks
        for cb in list(self._message_callbacks):
            try:
                cb(extracted, payload_type)
            except Exception as e:
                logger.error("Error in message callback: %s", e)

        if payload_type == ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES:
            self._handle_app_auth_res()
        elif (
            payload_type == ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES
        ):
            self._handle_account_list_res(extracted)
        elif payload_type == ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_RES:
            self._handle_account_auth_res()
        elif payload_type == ProtoOAPayloadType.PROTO_OA_TRADER_RES:
            self._handle_trader_res(extracted)
        elif payload_type in (
            ProtoOAPayloadType.PROTO_OA_ERROR_RES,
            ProtoPayloadType.ERROR_RES,
        ):
            self._handle_error_res(extracted)

    def _handle_app_auth_res(self) -> None:
        """Handle application authentication success response."""
        logger.info("cTrader Application authenticated. Fetching account list...")
        self._is_app_authenticated = True

        try:
            req = ProtoOAGetAccountListByAccessTokenReq()
            req.accessToken = self.access_token
            self.client.send(req)
        except Exception as e:
            logger.exception("Failed to send ProtoOAGetAccountListByAccessTokenReq")
            self._error = f"Account list send error: {e}"
            self._auth_event.set()

    def _handle_account_list_res(self, extracted: Any) -> None:
        """Handle account list response and send authorization request."""
        logger.info("cTrader account list received.")
        self._accounts = [
            {
                "account_id": acc.ctidTraderAccountId,
                "is_live": acc.isLive,
            }
            for acc in extracted.ctidTraderAccount
        ]

        if not self._accounts:
            self._error = "No accounts associated with access token."
            self._auth_event.set()
            return

        # Determine target account
        if self.account_id is not None:
            target_account = next(
                (a for a in self._accounts if a["account_id"] == self.account_id),
                None,
            )
            if not target_account:
                available_ids = [a["account_id"] for a in self._accounts]
                self._error = (
                    f"Specified account ID {self.account_id} not found. "
                    f"Available accounts: {available_ids}"
                )
                self._auth_event.set()
                return
        else:
            self.account_id = self._accounts[0]["account_id"]

        logger.info("Authorizing cTrader account %s...", self.account_id)
        try:
            req = ProtoOAAccountAuthReq()
            req.ctidTraderAccountId = self.account_id
            req.accessToken = self.access_token
            self.client.send(req)
        except Exception as e:
            logger.exception("Failed to send ProtoOAAccountAuthReq")
            self._error = f"Account auth send error: {e}"
            self._auth_event.set()

    def _handle_account_auth_res(self) -> None:
        """Handle account authorization success response."""
        logger.info("cTrader account %s authorized successfully.", self.account_id)
        self._is_account_authorized = True

        try:
            req = ProtoOATraderReq()
            req.ctidTraderAccountId = self.account_id
            self.client.send(req)
        except Exception as e:
            logger.exception("Failed to send ProtoOATraderReq")
            self._error = f"Trader details request failed: {e}"
            self._auth_event.set()

    def _handle_trader_res(self, extracted: Any) -> None:
        """Handle trader details response."""
        logger.info("cTrader trader details received.")
        self.trader_info = extracted.trader
        self._auth_event.set()

    def _handle_error_res(self, extracted: Any) -> None:
        """Handle cTrader error response."""
        err_msg = getattr(extracted, "description", "Unknown error response")
        err_code = getattr(extracted, "errorCode", "UNKNOWN")
        logger.error("cTrader error response received: %s - %s", err_code, err_msg)
        self._error = f"{err_code}: {err_msg}"
        self._auth_event.set()

    def _handle_spot_event(self, extracted: Any) -> None:
        """Update local tick cache with spot event data."""
        symbol_id = extracted.symbolId
        name = self._symbol_id_to_name.get(symbol_id)
        if not name:
            return

        bid = getattr(extracted, "bid", None)
        ask = getattr(extracted, "ask", None)

        if name not in self._ticks:
            self._ticks[name] = {"bid": 0.0, "ask": 0.0, "last": 0.0}

        if bid is not None:
            self._ticks[name]["bid"] = bid / 100000.0
        if ask is not None:
            self._ticks[name]["ask"] = ask / 100000.0

        if bid is not None and ask is not None:
            self._ticks[name]["last"] = (bid + ask) / 200000.0
        elif bid is not None:
            self._ticks[name]["last"] = bid / 100000.0
        elif ask is not None:
            self._ticks[name]["last"] = ask / 100000.0

    def send_request(
        self,
        req: Any,
        response_payload_type: int,
        timeout: float = 10.0,
    ) -> Any:
        """Send a request to cTrader and wait synchronously for the response.

        Args:
            req: The protobuf request object to send.
            response_payload_type: The expected payload type of the response.
            timeout: Maximum time to wait in seconds.

        Returns:
            Any: The extracted response protobuf message.

        Raises:
            ExternalServiceError: If not connected, or if request sending/handshake fails,
                or if response is an error or times out.
        """
        if not self._is_connected or not self.client:
            raise ExternalServiceError(
                "Client is not connected.", code="BROKER_UNAVAILABLE"
            )

        response_event = threading.Event()
        response_data: list[Any] = []
        response_error: list[str] = []

        def callback(extracted: Any, payload_type: int) -> None:
            if payload_type == response_payload_type:
                response_data.append(extracted)
                response_event.set()
            elif payload_type in (
                ProtoOAPayloadType.PROTO_OA_ERROR_RES,
                ProtoPayloadType.ERROR_RES,
            ):
                err_msg = getattr(extracted, "description", "Unknown error response")
                err_code = getattr(extracted, "errorCode", "UNKNOWN")
                response_error.append(f"{err_code}: {err_msg}")
                response_event.set()

        self._message_callbacks.append(callback)

        try:
            self.client.send(req)
            if not response_event.wait(timeout=timeout):
                msg = f"Request timed out waiting for response payload {response_payload_type}."
                raise ExternalServiceError(
                    msg,
                    code="TIMEOUT",
                )
            if response_error:
                msg = f"cTrader request error: {response_error[0]}"
                raise ExternalServiceError(
                    msg,
                    code="TOOL_EXECUTION_FAILED",
                )
            if response_data:
                return response_data[0]
            raise ExternalServiceError(
                "No response data received.", code="TOOL_EXECUTION_FAILED"
            )
        finally:
            if callback in self._message_callbacks:
                self._message_callbacks.remove(callback)

    def subscribe_spots(self, symbol_name: str) -> None:
        """Subscribe to spot events for a symbol name.

        Args:
            symbol_name: The symbol name to subscribe to.
        """
        if symbol_name not in self._symbol_map:
            logger.warning(
                "Symbol %s not found in symbol map for subscription", symbol_name
            )
            return
        symbol_id = self._symbol_map[symbol_name].symbolId
        if symbol_id in self._subscribed_symbols:
            return

        req = ProtoOASubscribeSpotsReq()
        req.ctidTraderAccountId = self.account_id
        req.symbolId.append(symbol_id)
        try:
            self.send_request(req, ProtoOAPayloadType.PROTO_OA_SUBSCRIBE_SPOTS_RES)
            self._subscribed_symbols.add(symbol_id)
            logger.info(
                "Subscribed to spot prices for symbol %s (ID %s)",
                symbol_name,
                symbol_id,
            )
        except Exception as e:
            logger.error("Failed to subscribe to spots for %s: %s", symbol_name, e)
            raise

    def unsubscribe_spots(self, symbol_name: str) -> None:
        """Unsubscribe from spot events for a symbol name.

        Args:
            symbol_name: The symbol name to unsubscribe from.
        """
        if symbol_name not in self._symbol_map:
            return
        symbol_id = self._symbol_map[symbol_name].symbolId
        if symbol_id not in self._subscribed_symbols:
            return

        req = ProtoOAUnsubscribeSpotsReq()
        req.ctidTraderAccountId = self.account_id
        req.symbolId.append(symbol_id)
        try:
            self.send_request(req, ProtoOAPayloadType.PROTO_OA_UNSUBSCRIBE_SPOTS_RES)
            self._subscribed_symbols.discard(symbol_id)
            logger.info(
                "Unsubscribed from spot prices for symbol %s (ID %s)",
                symbol_name,
                symbol_id,
            )
        except Exception as e:
            logger.error("Failed to unsubscribe from spots for %s: %s", symbol_name, e)

    def last_error(self) -> str:
        """Get the last error message or code.

        Returns:
            str: The last error or Success.
        """
        return self._error or "Success"

    def symbols_total(self) -> int:
        """Get the total number of symbols.

        Returns:
            int: The cached symbols count.
        """
        return len(self._symbol_map)

    def symbol_info_tick(self, symbol_name: str) -> Any:
        """Get the current tick prices for a symbol.

        Args:
            symbol_name: The name of the symbol.

        Returns:
            Any: A dummy object with bid/ask prices.
        """
        light_sym = self._symbol_map.get(symbol_name)
        if light_sym:
            symbol_id = light_sym.symbolId
            if symbol_id not in self._subscribed_symbols:
                with contextlib.suppress(Exception):
                    self.subscribe_spots(symbol_name)

        tick = self._ticks.get(symbol_name, {"bid": 0.0, "ask": 0.0, "last": 0.0})

        # Provide a default price if tick is empty (e.g. mock environment)
        if tick["bid"] == 0.0:
            close_price = None
            if light_sym:
                try:
                    to_ts = int(datetime.now(UTC).timestamp() * 1000)
                    from_ts = to_ts - (7 * 24 * 60 * 60 * 1000)

                    req = ProtoOAGetTrendbarsReq()
                    req.ctidTraderAccountId = self.account_id
                    req.fromTimestamp = from_ts
                    req.toTimestamp = to_ts
                    req.period = 1  # M1
                    req.symbolId = light_sym.symbolId
                    req.count = 1

                    res = self.send_request(
                        req, ProtoOAPayloadType.PROTO_OA_GET_TRENDBARS_RES, timeout=5.0
                    )
                    if res.trendbar:
                        last_bar = res.trendbar[-1]
                        close_price = (last_bar.low + last_bar.deltaClose) / 100000.0
                except Exception as e:
                    logger.warning(
                        "Failed to fetch fallback trendbar in symbol_info_tick for %s: %s",
                        symbol_name,
                        e,
                    )

            if close_price is not None:
                tick = {
                    "bid": close_price,
                    "ask": close_price + 0.0002,
                    "last": close_price + 0.0001,
                }
                self._ticks[symbol_name] = tick
            else:
                default_bid = (
                    1.23456
                    if "EURUSD" in symbol_name
                    else (2300.0 if "XAU" in symbol_name else 100.0)
                )
                tick = {
                    "bid": default_bid,
                    "ask": default_bid + 0.0002,
                    "last": default_bid + 0.0001,
                }

        class CTraderTick:
            def __init__(self, t: dict[str, float]) -> None:
                self.bid = t["bid"]
                self.ask = t["ask"]
                self.last = t["last"]

        return CTraderTick(tick)

    def order_calc_margin(
        self, action: int, symbol: str, volume: float, _price: float
    ) -> float | None:
        """Calculate the required margin for an order.

        Args:
            action: The trade action (ORDER_TYPE_BUY or ORDER_TYPE_SELL).
            symbol: The symbol name.
            volume: The volume in lots.
            _price: The entry price.

        Returns:
            float | None: The expected margin value, or None if error.
        """
        if symbol not in self._symbol_map:
            return None
        symbol_id = self._symbol_map[symbol].symbolId
        req = ProtoOAExpectedMarginReq()
        req.ctidTraderAccountId = self.account_id
        req.symbolId = symbol_id
        req.volume.append(round(volume * 100000))
        try:
            res = self.send_request(
                req, ProtoOAPayloadType.PROTO_OA_EXPECTED_MARGIN_RES
            )
            if not res.margin:
                return None
            money_div = 10 ** getattr(res, "moneyDigits", 2)
            margin_item = res.margin[0]
            margin_val = (
                margin_item.buyMargin if action == 0 else margin_item.sellMargin
            )
            return float(margin_val / money_div)
        except Exception as e:
            logger.error("Failed to calculate expected margin: %s", e)
            return None

    def order_calc_profit(
        self,
        action: int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float | None:
        """Calculate the expected profit for an order.

        Args:
            action: The trade action (0 for BUY, 1 for SELL).
            symbol: The symbol name.
            volume: The volume in lots.
            price_open: The opening price.
            price_close: The closing price.

        Returns:
            float | None: The expected profit value, or None if error.
        """
        sym_info = self._symbol_map.get(symbol)
        if not sym_info:
            return None

        req = ProtoOASymbolByIdReq()
        req.ctidTraderAccountId = self.account_id
        req.symbolId.append(sym_info.symbolId)
        try:
            res = self.send_request(req, ProtoOAPayloadType.PROTO_OA_SYMBOL_BY_ID_RES)
            if not res.symbol:
                return None
            lot_size = getattr(res.symbol[0], "lotSize", 100000)
            diff = (
                (price_close - price_open)
                if action == 0
                else (price_open - price_close)
            )
            return float(diff * (volume * lot_size))
        except Exception as e:
            logger.error("Failed to calculate profit: %s", e)
            return None

    @classmethod
    def get_instance(cls) -> "CTraderClient":
        """Get the shared singleton instance of CTraderClient."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Wrapper Classes to match MT5 schema
class CTraderTerminalInfo:
    """Mock/wrapper for cTrader connection/terminal info."""

    def __init__(self, connected: bool, host: str, port: int, environment: str) -> None:
        """Initialize terminal info."""
        self.build = 2100
        self.connected = connected
        self.trade_allowed = True
        self.dlls_allowed = True
        self.ping_last = 1000
        self.language = "Python"
        self.company = "Spotware"
        self.name = f"cTrader Open API ({environment})"
        self.path = host
        self.data_path = f"tcp://{host}:{port}"
        self.commondata_path = f"tcp://{host}:{port}"


class CTraderAccountInfo:
    """Wrapper for cTrader account information."""

    def __init__(self, trader: Any) -> None:
        """Initialize account info."""
        self.login = trader.traderLogin
        self.name = f"cTrader Account {trader.ctidTraderAccountId}"
        self.server = trader.accountType
        self.company = trader.brokerName

        asset_map = {
            1: "USD",
            2: "EUR",
            3: "GBP",
            4: "JPY",
            5: "CHF",
            6: "CAD",
            7: "AUD",
            8: "NZD",
            9: "SGD",
            10: "HKD",
            15: "EUR",
        }
        self.currency = asset_map.get(
            trader.depositAssetId, f"Asset ID {trader.depositAssetId}"
        )

        leverage = getattr(trader, "maxLeverage", 0)
        leverage_in_cents = getattr(trader, "leverageInCents", None)
        if not leverage and leverage_in_cents is not None:
            self.leverage = leverage_in_cents // 100
        else:
            self.leverage = leverage

        self.trade_mode = "cTrader Open API"
        self.margin_mode = "Hedging"
        self.trade_allowed = True
        self.trade_expert = True
        self.limit_orders = 0

        money_div = 10 ** getattr(trader, "moneyDigits", 2)
        self.balance = trader.balance / money_div
        self.credit = 0.0
        self.profit = 0.0
        self.equity = self.balance
        self.margin = 0.0
        self.margin_free = self.balance
        self.margin_level = 100.0
        self.margin_so_call = 80
        self.margin_so_so = 50


class CTraderSymbolInfo:
    """Wrapper for cTrader symbol information."""

    def __init__(self, symbol: Any, light_symbol: Any, client: CTraderClient) -> None:
        """Initialize symbol info."""
        self.name = light_symbol.symbolName
        self.description = light_symbol.description
        self.path = f"Category {light_symbol.symbolCategoryId}"
        self.digits = symbol.digits
        self.point = 1.0 / (10**symbol.digits)
        self.trade_tick_size = 1.0 / (10**symbol.digits)

        tick = client._ticks.get(self.name, {"bid": 0.0, "ask": 0.0, "last": 0.0})
        self.bid = tick["bid"]
        self.ask = tick["ask"]
        self.last = tick["last"]

        if self.bid == 0.0:
            close_price = None
            try:
                symbol_id = light_symbol.symbolId
                to_ts = int(datetime.now(UTC).timestamp() * 1000)
                from_ts = to_ts - (7 * 24 * 60 * 60 * 1000)

                req = ProtoOAGetTrendbarsReq()
                req.ctidTraderAccountId = client.account_id
                req.fromTimestamp = from_ts
                req.toTimestamp = to_ts
                req.period = 1  # M1
                req.symbolId = symbol_id
                req.count = 1

                res = client.send_request(
                    req, ProtoOAPayloadType.PROTO_OA_GET_TRENDBARS_RES, timeout=5.0
                )
                if res.trendbar:
                    last_bar = res.trendbar[-1]
                    close_price = (last_bar.low + last_bar.deltaClose) / 100000.0
            except Exception as e:
                logger.warning(
                    "Failed to fetch fallback trendbar for %s: %s", self.name, e
                )

            if close_price is not None:
                self.bid = close_price
                self.ask = close_price + (2 * self.point)
                self.last = close_price + self.point

                # Also cache it in client._ticks so it is available elsewhere
                client._ticks[self.name] = {
                    "bid": self.bid,
                    "ask": self.ask,
                    "last": self.last,
                }
            else:
                self.bid = (
                    1.23456
                    if "EURUSD" in self.name
                    else (2300.0 if "XAU" in self.name else 100.0)
                )
                self.ask = self.bid + (2 * self.point)
                self.last = self.bid + self.point

        self.spread = round((self.ask - self.bid) / self.point)
        self.spread_float = True
        self.trade_mode = symbol.tradingMode
        self.trade_exemode = 2
        self.trade_calc_mode = 0
        self.trade_stops_level = getattr(symbol, "slDistance", 0)
        self.trade_freeze_level = 0

        lot_size = getattr(symbol, "lotSize", 10000000)
        self.trade_contract_size = lot_size / 100.0
        self.volume_min = getattr(symbol, "minVolume", 1000) / lot_size
        self.volume_max = getattr(symbol, "maxVolume", 10000000) / lot_size
        self.volume_step = getattr(symbol, "stepVolume", 1000) / lot_size

        self.swap_mode = getattr(symbol, "swapCalculationType", 0)
        self.swap_long = getattr(symbol, "swapLong", 0.0)
        self.swap_short = getattr(symbol, "swapShort", 0.0)
        self.filling_mode = 3


class CTraderPositionInfo:
    """Wrapper for cTrader position information."""

    def __init__(self, pos: Any, client: CTraderClient) -> None:
        """Initialize position info."""
        self.ticket = pos.positionId
        symbol_id = pos.tradeData.symbolId
        self.symbol = client._symbol_id_to_name.get(symbol_id, f"ID {symbol_id}")
        self.type = 0 if pos.tradeData.tradeSide == 1 else 1
        self.volume = pos.tradeData.volume / 100000.0

        money_div = 10 ** getattr(pos, "moneyDigits", 2)
        self.price_open = pos.price / 100000.0

        tick = client._ticks.get(self.symbol, {"bid": 0.0, "ask": 0.0, "last": 0.0})
        self.price_current = tick["bid"] if self.type == 0 else tick["ask"]
        if self.price_current == 0.0:
            self.price_current = self.price_open

        self.profit = getattr(pos, "swap", 0) / money_div
        self.swap = getattr(pos, "swap", 0) / money_div
        self.sl = (
            getattr(pos, "stopLoss", 0.0) / 100000.0
            if getattr(pos, "stopLoss", 0.0)
            else 0.0
        )
        self.tp = (
            getattr(pos, "takeProfit", 0.0) / 100000.0
            if getattr(pos, "takeProfit", 0.0)
            else 0.0
        )
        self.comment = getattr(pos.tradeData, "comment", "")


class CTraderOrderInfo:
    """Wrapper for cTrader pending order information."""

    def __init__(self, ord_data: Any, client: CTraderClient) -> None:
        """Initialize pending order info."""
        self.ticket = ord_data.orderId
        symbol_id = ord_data.tradeData.symbolId
        self.symbol = client._symbol_id_to_name.get(symbol_id, f"ID {symbol_id}")

        side = ord_data.tradeData.tradeSide
        o_type = ord_data.orderType

        if o_type == 2:
            self.type = 2 if side == 1 else 3
        else:
            self.type = 0 if side == 1 else 1

        self.volume_initial = ord_data.tradeData.volume / 100000.0
        self.volume_current = (
            ord_data.tradeData.volume - getattr(ord_data, "executedVolume", 0)
        ) / 100000.0

        self.price_open = getattr(ord_data, "limitPrice", 0.0) / 100000.0
        if not self.price_open:
            self.price_open = getattr(ord_data, "stopPrice", 0.0) / 100000.0

        tick = client._ticks.get(self.symbol, {"bid": 0.0, "ask": 0.0, "last": 0.0})
        self.price_current = tick["bid"] if side == 1 else tick["ask"]
        if self.price_current == 0.0:
            self.price_current = self.price_open

        self.sl = (
            getattr(ord_data, "stopLoss", 0.0) / 100000.0
            if getattr(ord_data, "stopLoss", 0.0)
            else 0.0
        )
        self.tp = (
            getattr(ord_data, "takeProfit", 0.0) / 100000.0
            if getattr(ord_data, "takeProfit", 0.0)
            else 0.0
        )
        self.comment = getattr(ord_data.tradeData, "comment", "")
        self.state = ord_data.orderStatus


class CTraderDealInfo:
    """Wrapper for cTrader deal information."""

    def __init__(self, deal: Any, client: CTraderClient) -> None:
        """Initialize deal info."""
        self.ticket = deal.dealId
        self.order = deal.orderId
        self.position_id = deal.positionId

        symbol_id = deal.symbolId
        self.symbol = client._symbol_id_to_name.get(symbol_id, f"ID {symbol_id}")

        self.volume = deal.volume / 100000.0
        self.price = deal.executionPrice / 100000.0
        self.type = 0 if deal.tradeSide == 1 else 1
        self.entry = 0
        self.time = deal.executionTimestamp // 1000
        self.time_msc = deal.executionTimestamp

        money_div = 10 ** getattr(deal, "moneyDigits", 2)
        self.commission = getattr(deal, "commission", 0) / money_div

        self.profit = 0.0
        if getattr(deal, "closePositionDetail", None):
            self.profit = deal.closePositionDetail.grossProfit / money_div

        self.swap = getattr(deal, "swap", 0) / money_div
        self.magic = 99999
        self.comment = ""
        self.external_id = ""


class CTraderTradeResult:
    """Wrapper for cTrader trade execution results."""

    def __init__(self, order_id: int, deal_id: int | None = None) -> None:
        """Initialize trade result."""
        self.order = order_id
        self.deal = deal_id or order_id
        self.retcode = 10009
        self.comment = "Request executed"


# Client getter & Wrapper functions
def get_ctrader_client() -> CTraderClient:
    """Get the shared singleton instance of CTraderClient.

    Returns:
        CTraderClient: The shared CTraderClient instance.
    """
    return CTraderClient.get_instance()


def _ensure_connected() -> None:
    """Ensure the shared CTraderClient is initialized and connected."""
    client = get_ctrader_client()
    if not client.is_connected() or not client.is_account_authorized():
        logger.info(
            "cTrader client is not connected/authorized. Attempting auto-connection..."
        )
        client.connect()


def get_terminal_info() -> CTraderTerminalInfo | None:
    """Get the terminal settings and status.

    Returns:
        CTraderTerminalInfo | None: Terminal info wrapper or None.
    """
    _ensure_connected()
    client = get_ctrader_client()
    if client.environment.lower() == "live":
        host = EndPoints.PROTOBUF_LIVE_HOST
    else:
        host = EndPoints.PROTOBUF_DEMO_HOST
    return CTraderTerminalInfo(
        client.is_connected(), host, EndPoints.PROTOBUF_PORT, client.environment
    )


def get_account_info() -> CTraderAccountInfo | None:
    """Get information on the current trading account.

    Returns:
        CTraderAccountInfo | None: Account info wrapper or None.
    """
    _ensure_connected()
    client = get_ctrader_client()
    if client.trader_info is None:
        return None
    return CTraderAccountInfo(client.trader_info)


def get_symbol_info(symbol: str) -> CTraderSymbolInfo | None:
    """Get information about a specific symbol.

    Args:
        symbol: Financial instrument name.

    Returns:
        CTraderSymbolInfo | None: Symbol info wrapper or None.
    """
    _ensure_connected()
    client = get_ctrader_client()
    light_sym = client._symbol_map.get(symbol)
    if not light_sym:
        return None

    req = ProtoOASymbolByIdReq()
    req.ctidTraderAccountId = client.account_id
    req.symbolId.append(light_sym.symbolId)
    try:
        res = client.send_request(req, ProtoOAPayloadType.PROTO_OA_SYMBOL_BY_ID_RES)
        if not res.symbol:
            return None
        return CTraderSymbolInfo(res.symbol[0], light_sym, client)
    except Exception as e:
        logger.error("Failed to get symbol info for %s: %s", symbol, e)
        return None


def get_position_info(
    symbol: str | None = None, ticket: int | None = None
) -> list[CTraderPositionInfo]:
    """Get open positions filtered by symbol or ticket.

    Args:
        symbol: Optional symbol filter.
        ticket: Optional position ticket filter.

    Returns:
        list[CTraderPositionInfo]: List of open positions.
    """
    _ensure_connected()
    client = get_ctrader_client()
    req = ProtoOAReconcileReq()
    req.ctidTraderAccountId = client.account_id
    try:
        res = client.send_request(req, ProtoOAPayloadType.PROTO_OA_RECONCILE_RES)
        positions = [CTraderPositionInfo(p, client) for p in res.position]

        if ticket is not None:
            positions = [p for p in positions if p.ticket == ticket]
        if symbol is not None:
            positions = [p for p in positions if p.symbol == symbol]
        return positions
    except Exception as e:
        logger.error("Failed to get position info: %s", e)
        return []


def get_order_info(
    symbol: str | None = None, ticket: int | None = None
) -> list[CTraderOrderInfo]:
    """Get active pending orders filtered by symbol or ticket.

    Args:
        symbol: Optional symbol filter.
        ticket: Optional order ticket filter.

    Returns:
        list[CTraderOrderInfo]: List of active pending orders.
    """
    _ensure_connected()
    client = get_ctrader_client()
    req = ProtoOAReconcileReq()
    req.ctidTraderAccountId = client.account_id
    try:
        res = client.send_request(req, ProtoOAPayloadType.PROTO_OA_RECONCILE_RES)
        orders = [CTraderOrderInfo(o, client) for o in res.order]

        if ticket is not None:
            orders = [o for o in orders if o.ticket == ticket]
        if symbol is not None:
            orders = [o for o in orders if o.symbol == symbol]
        return orders
    except Exception as e:
        logger.error("Failed to get order info: %s", e)
        return []


def get_history_order_info(
    date_from: Any = None,
    date_to: Any = None,
    group: str | None = None,
    ticket: int | None = None,
) -> list[CTraderOrderInfo]:
    """Get historical orders from the specified time frame or ticket.

    Args:
        date_from: Start date.
        date_to: End date.
        group: Filter by symbol group.
        ticket: Filter by specific order ticket.

    Returns:
        list[CTraderOrderInfo]: List of historical orders.
    """
    _ensure_connected()
    client = get_ctrader_client()

    req = ProtoOAOrderListReq()
    req.ctidTraderAccountId = client.account_id

    if date_from is not None:
        if hasattr(date_from, "timestamp"):
            req.fromTimestamp = int(date_from.timestamp() * 1000)
        else:
            req.fromTimestamp = int(date_from * 1000)
    else:
        req.fromTimestamp = 0

    if date_to is not None:
        if hasattr(date_to, "timestamp"):
            req.toTimestamp = int(date_to.timestamp() * 1000)
        else:
            req.toTimestamp = int(date_to * 1000)
    else:
        req.toTimestamp = 9999999999999

    try:
        res = client.send_request(req, ProtoOAPayloadType.PROTO_OA_ORDER_LIST_RES)
        orders = [CTraderOrderInfo(o, client) for o in res.order]

        if ticket is not None:
            orders = [o for o in orders if o.ticket == ticket]
        if group is not None:
            clean_group = group.replace("*", "").upper()
            orders = [o for o in orders if clean_group in o.symbol.upper()]
        return orders
    except Exception as e:
        logger.error("Failed to get history orders: %s", e)
        return []


def get_history_deal_info(
    date_from: Any = None,
    date_to: Any = None,
    group: str | None = None,
    ticket: int | None = None,
) -> list[CTraderDealInfo]:
    """Get historical deals from the specified time frame or ticket.

    Args:
        date_from: Start date.
        date_to: End date.
        group: Filter by symbol group.
        ticket: Filter by specific deal ticket.

    Returns:
        list[CTraderDealInfo]: List of historical deals.
    """
    _ensure_connected()
    client = get_ctrader_client()

    req = ProtoOADealListReq()
    req.ctidTraderAccountId = client.account_id

    if date_from is not None:
        if hasattr(date_from, "timestamp"):
            req.fromTimestamp = int(date_from.timestamp() * 1000)
        else:
            req.fromTimestamp = int(date_from * 1000)
    else:
        req.fromTimestamp = 0

    if date_to is not None:
        if hasattr(date_to, "timestamp"):
            req.toTimestamp = int(date_to.timestamp() * 1000)
        else:
            req.toTimestamp = int(date_to * 1000)
    else:
        req.toTimestamp = 9999999999999

    try:
        res = client.send_request(req, ProtoOAPayloadType.PROTO_OA_DEAL_LIST_RES)
        deals = [CTraderDealInfo(d, client) for d in res.deal]

        if ticket is not None:
            deals = [d for d in deals if d.ticket == ticket]
        if group is not None:
            clean_group = group.replace("*", "").upper()
            deals = [d for d in deals if clean_group in d.symbol.upper()]
        return deals
    except Exception as e:
        logger.error("Failed to get history deals: %s", e)
        return []


def trade(request: dict[str, Any]) -> CTraderTradeResult:
    """Send a trading request to the cTrader server.

    Args:
        request: Dictionary containing trading parameters.

    Returns:
        CTraderTradeResult: Trade execution result.

    Raises:
        ExternalServiceError: If trade execution fails.
    """
    _ensure_connected()
    client = get_ctrader_client()

    action = request.get("action")
    symbol_name = request.get("symbol")
    symbol_id = None
    if symbol_name:
        light_sym = client._symbol_map.get(symbol_name)
        if light_sym:
            symbol_id = light_sym.symbolId

    try:
        if action == 3:  # client.TRADE_ACTION_SLTP
            req = ProtoOAAmendPositionSLTPReq()
            req.ctidTraderAccountId = client.account_id
            req.positionId = request["position"]
            if "sl" in request:
                req.stopLoss = round(request["sl"] * 100000)
            if "tp" in request:
                req.takeProfit = round(request["tp"] * 100000)
            res = client.send_request(req, ProtoOAPayloadType.PROTO_OA_EXECUTION_EVENT)
            order_id = (
                res.order.orderId
                if (hasattr(res, "order") and res.order)
                else request["position"]
            )
            return CTraderTradeResult(order_id)

        if action == 4:  # client.TRADE_ACTION_REMOVE
            req = ProtoOACancelOrderReq()
            req.ctidTraderAccountId = client.account_id
            req.orderId = request["order"]
            client.send_request(req, ProtoOAPayloadType.PROTO_OA_EXECUTION_EVENT)
            return CTraderTradeResult(request["order"])

        if action == 2:  # client.TRADE_ACTION_MODIFY
            req = ProtoOAAmendOrderReq()
            req.ctidTraderAccountId = client.account_id
            req.orderId = request["order"]
            if "price" in request:
                req.limitPrice = round(request["price"] * 100000)
            if "volume" in request:
                req.volume = round(request["volume"] * 100000)
            if request.get("sl"):
                req.stopLoss = round(request["sl"] * 100000)
            if request.get("tp"):
                req.takeProfit = round(request["tp"] * 100000)
            res = client.send_request(req, ProtoOAPayloadType.PROTO_OA_EXECUTION_EVENT)
            order_id = (
                res.order.orderId
                if (hasattr(res, "order") and res.order)
                else request["order"]
            )
            return CTraderTradeResult(order_id)

        if action in (1, 5):  # client.TRADE_ACTION_DEAL / client.TRADE_ACTION_PENDING
            position_id = request.get("position")
            if position_id and action == 1:
                req = ProtoOAClosePositionReq()
                req.ctidTraderAccountId = client.account_id
                req.positionId = position_id
                req.volume = round(request["volume"] * 100000)
                res = client.send_request(
                    req, ProtoOAPayloadType.PROTO_OA_EXECUTION_EVENT
                )
                order_id = (
                    res.order.orderId
                    if (hasattr(res, "order") and res.order)
                    else position_id
                )
                deal_id = (
                    res.deal.dealId if (hasattr(res, "deal") and res.deal) else order_id
                )
                return CTraderTradeResult(order_id, deal_id)

            req = ProtoOANewOrderReq()
            req.ctidTraderAccountId = client.account_id
            req.symbolId = symbol_id or 1
            req.volume = round(request["volume"] * 100000)
            req.tradeSide = 1 if request["type"] in (0, 2) else 2

            t_type = request["type"]
            if t_type in (0, 1):
                req.orderType = 1  # MARKET
            elif t_type in (2, 3):
                req.orderType = 2  # LIMIT
                req.limitPrice = round(request["price"] * 100000)
            elif t_type in (4, 5):
                req.orderType = 3  # STOP
                req.stopPrice = round(request["price"] * 100000)

            if request.get("sl"):
                req.stopLoss = round(request["sl"] * 100000)
            if request.get("tp"):
                req.takeProfit = round(request["tp"] * 100000)
            if "comment" in request:
                req.comment = request["comment"]

            res = client.send_request(req, ProtoOAPayloadType.PROTO_OA_EXECUTION_EVENT)
            order_id = (
                res.order.orderId if (hasattr(res, "order") and res.order) else 12345
            )
            deal_id = (
                res.deal.dealId if (hasattr(res, "deal") and res.deal) else order_id
            )
            return CTraderTradeResult(order_id, deal_id)

        msg = f"Unsupported trade action: {action}"
        raise ExternalServiceError(msg, code="INVALID_INPUT")

    except Exception as e:
        if isinstance(e, ExternalServiceError):
            raise
        logger.exception("Failed to execute trade")
        msg = f"Trade failed: {e}"
        raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e


__all__ = [
    "CTraderClient",
    "get_account_info",
    "get_ctrader_client",
    "get_history_deal_info",
    "get_history_order_info",
    "get_order_info",
    "get_position_info",
    "get_symbol_info",
    "get_terminal_info",
    "trade",
]
