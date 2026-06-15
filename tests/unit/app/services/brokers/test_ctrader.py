# ruff: noqa: N802, ARG002, TRY002, TRY004, PLR0915
"""Unit tests for the CTraderClient broker service."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from app.core.config import settings
from app.services.brokers.ctrader import (
    CTraderClient,
    get_account_info,
    get_ctrader_client,
    get_history_deal_info,
    get_history_order_info,
    get_order_info,
    get_position_info,
    get_symbol_info,
    get_terminal_info,
    trade,
)
from app.utils.errors import ConfigurationError, ExternalServiceError
from ctrader_open_api.messages.OpenApiCommonModelMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
    ProtoPayloadType,
)
from ctrader_open_api.messages.OpenApiMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
    ProtoOAAccountAuthReq,
    ProtoOAApplicationAuthReq,
    ProtoOAAssetListReq,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOASymbolsListReq,
    ProtoOATraderReq,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
    ProtoOAPayloadType,
)
from pytest_mock import MockerFixture


class MockMessage:
    """Mock for cTrader Open API protobuf message wrapper."""

    def __init__(self, payload_type: int) -> None:
        self.payloadType = payload_type


class BaseMockClient:
    """Base class for mocking Twisted-based cTrader Client callbacks."""

    def __init__(self, host: str, port: int, protocol: Any) -> None:
        self.host = host
        self.port = port
        self.connection_cb: Any = None
        self.disconnection_cb: Any = None
        self.message_cb: Any = None

    def setConnectedCallback(self, cb: Any) -> None:
        self.connection_cb = cb

    def setDisconnectedCallback(self, cb: Any) -> None:
        self.disconnection_cb = cb

    def setMessageReceivedCallback(self, cb: Any) -> None:
        self.message_cb = cb

    def startService(self) -> None:
        if self.connection_cb:
            self.connection_cb(self)

    def stopService(self) -> None:
        pass

    def send(self, msg: Any) -> None:
        pass


class SuccessMockClient(BaseMockClient):
    """Mock cTrader client that successfully handshakes and authenticates."""

    def send(self, msg: Any) -> None:
        if isinstance(msg, ProtoOAApplicationAuthReq) and self.message_cb:
            self.message_cb(
                self,
                MockMessage(ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES),
            )
        elif isinstance(msg, ProtoOAGetAccountListByAccessTokenReq) and self.message_cb:
            self.message_cb(
                self,
                MockMessage(
                    ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES
                ),
            )
        elif isinstance(msg, ProtoOAAccountAuthReq) and self.message_cb:
            self.message_cb(
                self, MockMessage(ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_RES)
            )
        elif isinstance(msg, ProtoOATraderReq) and self.message_cb:
            self.message_cb(self, MockMessage(ProtoOAPayloadType.PROTO_OA_TRADER_RES))
        elif isinstance(msg, ProtoOASymbolsListReq) and self.message_cb:
            self.message_cb(
                self, MockMessage(ProtoOAPayloadType.PROTO_OA_SYMBOLS_LIST_RES)
            )
        elif isinstance(msg, ProtoOAAssetListReq) and self.message_cb:
            self.message_cb(
                self, MockMessage(ProtoOAPayloadType.PROTO_OA_ASSET_LIST_RES)
            )


def test_ctrader_client_initialization_defaults() -> None:
    """Test CTraderClient initialization fallback to settings defaults."""
    client = CTraderClient()
    assert client.client_id == settings.ctrader_client_id
    assert client.client_secret == settings.ctrader_client_secret
    assert client.access_token == settings.ctrader_access_token
    assert client.account_id == settings.ctrader_account_id
    assert client.environment == settings.ctrader_environment


def test_ctrader_client_initialization_custom() -> None:
    """Test CTraderClient initialization with custom parameters."""
    client = CTraderClient(
        client_id="custom_id",
        client_secret="custom_secret",
        access_token="custom_token",
        account_id=98765,
        environment="live",
    )
    assert client.client_id == "custom_id"
    assert client.client_secret == "custom_secret"
    assert client.access_token == "custom_token"
    assert client.account_id == 98765
    assert client.environment == "live"


def test_ctrader_client_connect_success(mocker: MockerFixture) -> None:
    """Test successful cTrader connect and auth handshake flow."""
    mock_reactor = mocker.patch("twisted.internet.reactor", create=True)
    mock_reactor.running = False

    mocker.patch("app.services.brokers.ctrader.Client", SuccessMockClient)

    # Mock Protobuf extract helper to return mock accounts list and trader info
    mock_extract = mocker.patch("ctrader_open_api.protobuf.Protobuf.extract")

    mock_acc = MagicMock()
    mock_acc.ctidTraderAccountId = 12345
    mock_acc.isLive = False

    mock_accounts_res = MagicMock()
    mock_accounts_res.ctidTraderAccount = [mock_acc]

    mock_trader = MagicMock()
    mock_trader.traderLogin = 12345
    mock_trader.brokerName = "Broker"
    mock_trader.balance = 100000
    mock_trader.depositAssetId = 1
    mock_trader.maxLeverage = 500
    mock_trader.accountType = "DEMO"

    mock_trader_res = MagicMock()
    mock_trader_res.trader = mock_trader

    mock_symbol = MagicMock()
    mock_symbol.symbolId = 1
    mock_symbol.symbolName = "EURUSD"
    mock_symbol.description = "EURUSD symbol"
    mock_symbols_res = MagicMock()
    mock_symbols_res.symbol = [mock_symbol]

    mock_asset = MagicMock()
    mock_asset.assetId = 1
    mock_asset.name = "USD"
    mock_asset.displayName = "US Dollar"
    mock_asset.digits = 2
    mock_assets_res = MagicMock()
    mock_assets_res.asset = [mock_asset]

    # We configure extract to return appropriate objects based on message payloadType
    def side_effect(message: Any) -> Any:
        if (
            message.payloadType
            == ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES
        ):
            return mock_accounts_res
        if message.payloadType == ProtoOAPayloadType.PROTO_OA_TRADER_RES:
            return mock_trader_res
        if message.payloadType == ProtoOAPayloadType.PROTO_OA_SYMBOLS_LIST_RES:
            return mock_symbols_res
        if message.payloadType == ProtoOAPayloadType.PROTO_OA_ASSET_LIST_RES:
            return mock_assets_res
        return MagicMock()

    mock_extract.side_effect = side_effect

    client = CTraderClient(
        client_id="id",
        client_secret="secret",
        access_token="token",
        account_id=12345,
    )
    result = client.connect()

    assert result is True
    assert client.is_connected() is True
    assert client.is_app_authenticated() is True
    assert client.is_account_authorized() is True
    assert client.account_id == 12345
    assert client.trader_info is not None
    assert client.trader_info.traderLogin == 12345
    assert client.trader_info.brokerName == "Broker"


def test_ctrader_client_connect_missing_credentials(mocker: MockerFixture) -> None:
    """Test ConfigurationError when required settings are missing."""
    mocker.patch.object(settings, "ctrader_client_id", "")
    mocker.patch.object(settings, "ctrader_client_secret", "")
    mocker.patch.object(settings, "ctrader_access_token", "")

    client = CTraderClient(client_id=None, client_secret="secret", access_token="token")
    with pytest.raises(ConfigurationError, match="client ID is required"):
        client.connect()

    client2 = CTraderClient(client_id="id", client_secret=None, access_token="token")
    with pytest.raises(ConfigurationError, match="client secret is required"):
        client2.connect()

    client3 = CTraderClient(client_id="id", client_secret="secret", access_token=None)
    with pytest.raises(ConfigurationError, match="access token is required"):
        client3.connect()


def test_ctrader_client_connect_timeout_tcp(mocker: MockerFixture) -> None:
    """Test connection timeout on TCP socket phase."""
    mocker.patch("twisted.internet.reactor", create=True)

    class TimeoutTcpMockClient(BaseMockClient):
        def startService(self) -> None:
            # Simulate socket timeout by not invoking connection callback
            pass

    mocker.patch("app.services.brokers.ctrader.Client", TimeoutTcpMockClient)

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    mocker.patch.object(client._connected_event, "wait", return_value=False)

    with pytest.raises(ExternalServiceError, match="cTrader TCP connection timed out"):
        client.connect()


def test_ctrader_client_connect_timeout_auth(mocker: MockerFixture) -> None:
    """Test connection timeout during handshake phase."""
    mocker.patch("twisted.internet.reactor", create=True)

    class TimeoutAuthMockClient(BaseMockClient):
        def send(self, msg: Any) -> None:
            # Do NOT reply to trigger auth timeout
            pass

    mocker.patch("app.services.brokers.ctrader.Client", TimeoutAuthMockClient)

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    mocker.patch.object(client._connected_event, "wait", return_value=True)
    mocker.patch.object(client._auth_event, "wait", return_value=False)

    with pytest.raises(
        ExternalServiceError, match="cTrader authentication handshake timed out"
    ):
        client.connect()


def test_ctrader_client_connect_app_auth_error(mocker: MockerFixture) -> None:
    """Test auth failure due to application authentication error response."""
    mocker.patch("twisted.internet.reactor", create=True)

    class AppAuthErrorMockClient(BaseMockClient):
        def send(self, msg: Any) -> None:
            # Reply with an error message
            if self.message_cb:
                self.message_cb(
                    self, MockMessage(ProtoOAPayloadType.PROTO_OA_ERROR_RES)
                )

    mocker.patch("app.services.brokers.ctrader.Client", AppAuthErrorMockClient)

    mock_extract = mocker.patch("ctrader_open_api.protobuf.Protobuf.extract")
    mock_err = MagicMock()
    mock_err.description = "Invalid Client ID"
    mock_err.errorCode = "INVALID_CLIENT_ID"
    mock_extract.return_value = mock_err

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    mocker.patch.object(client._connected_event, "wait", return_value=True)
    mocker.patch.object(client._auth_event, "wait", return_value=True)

    with pytest.raises(
        ExternalServiceError, match="INVALID_CLIENT_ID: Invalid Client ID"
    ):
        client.connect()


def test_ctrader_client_connect_empty_accounts(mocker: MockerFixture) -> None:
    """Test auth failure when token has no associated accounts."""
    mocker.patch("twisted.internet.reactor", create=True)

    class EmptyAccountsMockClient(BaseMockClient):
        def send(self, msg: Any) -> None:
            if isinstance(msg, ProtoOAApplicationAuthReq) and self.message_cb:
                self.message_cb(
                    self,
                    MockMessage(ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES),
                )
            elif (
                isinstance(msg, ProtoOAGetAccountListByAccessTokenReq)
                and self.message_cb
            ):
                self.message_cb(
                    self,
                    MockMessage(
                        ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES
                    ),
                )

    mocker.patch("app.services.brokers.ctrader.Client", EmptyAccountsMockClient)

    mock_extract = mocker.patch("ctrader_open_api.protobuf.Protobuf.extract")
    mock_res = MagicMock()
    mock_res.ctidTraderAccount = []
    mock_extract.return_value = mock_res

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    mocker.patch.object(client._connected_event, "wait", return_value=True)
    mocker.patch.object(client._auth_event, "wait", return_value=True)

    with pytest.raises(
        ExternalServiceError, match="No accounts associated with access token"
    ):
        client.connect()


def test_ctrader_client_connect_account_not_found(mocker: MockerFixture) -> None:
    """Test auth failure when custom account ID does not match account list."""
    mocker.patch("twisted.internet.reactor", create=True)

    class AccountNotFoundMockClient(BaseMockClient):
        def send(self, msg: Any) -> None:
            if isinstance(msg, ProtoOAApplicationAuthReq) and self.message_cb:
                self.message_cb(
                    self,
                    MockMessage(ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES),
                )
            elif (
                isinstance(msg, ProtoOAGetAccountListByAccessTokenReq)
                and self.message_cb
            ):
                self.message_cb(
                    self,
                    MockMessage(
                        ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES
                    ),
                )

    mocker.patch("app.services.brokers.ctrader.Client", AccountNotFoundMockClient)

    mock_extract = mocker.patch("ctrader_open_api.protobuf.Protobuf.extract")

    mock_acc = MagicMock()
    mock_acc.ctidTraderAccountId = 12345
    mock_res = MagicMock()
    mock_res.ctidTraderAccount = [mock_acc]

    mock_extract.return_value = mock_res

    client = CTraderClient(
        client_id="id",
        client_secret="secret",
        access_token="token",
        account_id=99999,
    )
    mocker.patch.object(client._connected_event, "wait", return_value=True)
    mocker.patch.object(client._auth_event, "wait", return_value=True)

    with pytest.raises(
        ExternalServiceError, match="Specified account ID 99999 not found"
    ):
        client.connect()


def test_ctrader_client_disconnect(mocker: MockerFixture) -> None:
    """Test client disconnect correctly resets connected state flags."""
    mocker.patch("twisted.internet.reactor", create=True)

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    client.client = MagicMock()
    client._is_connected = True
    client._is_app_authenticated = True
    client._is_account_authorized = True

    client.disconnect()

    assert client.is_connected() is False
    assert client.is_app_authenticated() is False
    assert client.is_account_authorized() is False
    client.client.stopService.assert_called_once()


def test_get_ctrader_client_singleton() -> None:
    """Test get_ctrader_client returns a singleton instance."""
    client1 = get_ctrader_client()
    client2 = get_ctrader_client()
    assert client1 is client2
    assert isinstance(client1, CTraderClient)


def test_ctrader_client_connect_already_connected() -> None:
    """Test connect returns True immediately if already connected and authorized."""
    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    client._is_connected = True
    client._is_account_authorized = True
    assert client.connect() is True


def test_ctrader_client_connect_live_environment(mocker: MockerFixture) -> None:
    """Test connect uses live environment endpoints when configured."""
    mocker.patch("twisted.internet.reactor", create=True)

    mocker.patch("app.services.brokers.ctrader.Client", SuccessMockClient)

    mock_extract = mocker.patch("ctrader_open_api.protobuf.Protobuf.extract")
    mock_acc = MagicMock()
    mock_acc.ctidTraderAccountId = 12345
    mock_acc.isLive = True
    mock_accounts_res = MagicMock()
    mock_accounts_res.ctidTraderAccount = [mock_acc]
    mock_extract.return_value = mock_accounts_res

    client = CTraderClient(
        client_id="id",
        client_secret="secret",
        access_token="token",
        account_id=12345,
        environment="live",
    )
    result = client.connect()

    assert result is True
    assert client.environment == "live"
    # Ensure client was initialized with the live host
    from ctrader_open_api import (  # type: ignore[import-untyped, unused-ignore]
        EndPoints,
    )

    assert client.client.host == EndPoints.PROTOBUF_LIVE_HOST
    assert client.client.port == EndPoints.PROTOBUF_PORT


def test_ctrader_client_connect_default_account_selection(
    mocker: MockerFixture,
) -> None:
    """Test connect automatically selects the first account if none is specified."""
    mocker.patch("twisted.internet.reactor", create=True)
    mocker.patch.object(settings, "ctrader_account_id", None)

    mocker.patch("app.services.brokers.ctrader.Client", SuccessMockClient)

    mock_extract = mocker.patch("ctrader_open_api.protobuf.Protobuf.extract")
    mock_acc1 = MagicMock()
    mock_acc1.ctidTraderAccountId = 11111
    mock_acc1.isLive = False
    mock_acc2 = MagicMock()
    mock_acc2.ctidTraderAccountId = 22222
    mock_acc2.isLive = False

    mock_accounts_res = MagicMock()
    mock_accounts_res.ctidTraderAccount = [mock_acc1, mock_acc2]
    mock_extract.return_value = mock_accounts_res

    client = CTraderClient(
        client_id="id",
        client_secret="secret",
        access_token="token",
        account_id=None,
    )
    result = client.connect()

    assert result is True
    # Should automatically select the first account id
    assert client.account_id == 11111


def test_ctrader_client_disconnect_exception(mocker: MockerFixture) -> None:
    """Test client disconnect handles exceptions raised by stopService."""
    mocker.patch("twisted.internet.reactor", create=True)

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    client.client = MagicMock()
    client.client.stopService.side_effect = Exception("Stop error")
    client._is_connected = True

    client.disconnect()

    assert client.is_connected() is False
    client.client.stopService.assert_called_once()


def test_ctrader_client_connect_initialization_failure(
    mocker: MockerFixture,
) -> None:
    """Test connect handles client initialization exceptions."""
    mocker.patch("twisted.internet.reactor", create=True)
    mocker.patch(
        "app.services.brokers.ctrader.Client",
        side_effect=Exception("Init error"),
    )

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    with pytest.raises(
        ExternalServiceError, match="Failed to initialize cTrader Open API service"
    ):
        client.connect()


def test_ctrader_client_connect_send_app_auth_failure(
    mocker: MockerFixture,
) -> None:
    """Test connect handles exception when sending app auth request."""
    mocker.patch("twisted.internet.reactor", create=True)

    class FailSendMockClient(BaseMockClient):
        def send(self, msg: Any) -> None:
            if isinstance(msg, ProtoOAApplicationAuthReq):
                raise Exception("Send error")

    mocker.patch("app.services.brokers.ctrader.Client", FailSendMockClient)

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    mocker.patch.object(client._connected_event, "wait", return_value=True)
    mocker.patch.object(client._auth_event, "wait", return_value=True)

    with pytest.raises(ExternalServiceError, match="App auth send error"):
        client.connect()


def test_ctrader_client_connect_send_accounts_failure(
    mocker: MockerFixture,
) -> None:
    """Test connect handles exception when sending account list request."""
    mocker.patch("twisted.internet.reactor", create=True)

    class FailAccountsMockClient(BaseMockClient):
        def send(self, msg: Any) -> None:
            if isinstance(msg, ProtoOAApplicationAuthReq) and self.message_cb:
                self.message_cb(
                    self,
                    MockMessage(ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES),
                )
            elif isinstance(msg, ProtoOAGetAccountListByAccessTokenReq):
                raise Exception("Send error")

    mocker.patch("app.services.brokers.ctrader.Client", FailAccountsMockClient)
    mocker.patch("ctrader_open_api.protobuf.Protobuf.extract", return_value=MagicMock())

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    mocker.patch.object(client._connected_event, "wait", return_value=True)
    mocker.patch.object(client._auth_event, "wait", return_value=True)

    with pytest.raises(ExternalServiceError, match="Account list send error"):
        client.connect()


def test_ctrader_client_connect_send_auth_req_failure(
    mocker: MockerFixture,
) -> None:
    """Test connect handles exception when sending account auth request."""
    mocker.patch("twisted.internet.reactor", create=True)

    class FailAuthReqMockClient(BaseMockClient):
        def send(self, msg: Any) -> None:
            if isinstance(msg, ProtoOAApplicationAuthReq) and self.message_cb:
                self.message_cb(
                    self,
                    MockMessage(ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES),
                )
            elif (
                isinstance(msg, ProtoOAGetAccountListByAccessTokenReq)
                and self.message_cb
            ):
                self.message_cb(
                    self,
                    MockMessage(
                        ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES
                    ),
                )
            elif isinstance(msg, ProtoOAAccountAuthReq):
                raise Exception("Send error")

    mocker.patch("app.services.brokers.ctrader.Client", FailAuthReqMockClient)

    mock_extract = mocker.patch("ctrader_open_api.protobuf.Protobuf.extract")
    mock_acc = MagicMock()
    mock_acc.ctidTraderAccountId = 12345
    mock_acc.isLive = False
    mock_accounts_res = MagicMock()
    mock_accounts_res.ctidTraderAccount = [mock_acc]
    mock_extract.return_value = mock_accounts_res

    client = CTraderClient(
        client_id="id",
        client_secret="secret",
        access_token="token",
        account_id=12345,
    )
    mocker.patch.object(client._connected_event, "wait", return_value=True)
    mocker.patch.object(client._auth_event, "wait", return_value=True)

    with pytest.raises(ExternalServiceError, match="Account auth send error"):
        client.connect()


def test_ctrader_client_on_message_extract_exception(
    mocker: MockerFixture,
) -> None:
    """Test _on_message handles exceptions in Protobuf.extract."""
    mocker.patch("twisted.internet.reactor", create=True)

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    client.client = MagicMock()

    mocker.patch(
        "ctrader_open_api.protobuf.Protobuf.extract",
        side_effect=Exception("Extract error"),
    )

    # Invoke _on_message directly
    msg = MockMessage(ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES)
    # This should not raise exception but return early
    client._on_message(None, msg)


def test_ctrader_client_on_disconnected(mocker: MockerFixture) -> None:
    """Test _on_disconnected callback sets correct flags and error state."""
    mocker.patch("twisted.internet.reactor", create=True)

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    client._is_connected = True
    client._is_app_authenticated = True
    client._is_account_authorized = True

    client._on_disconnected(None, "Connection lost")

    assert client.is_connected() is False
    assert client.is_app_authenticated() is False
    assert client.is_account_authorized() is False
    assert client._error == "Connection lost"


def test_ctrader_client_on_message_payload_error_res(
    mocker: MockerFixture,
) -> None:
    """Test _on_message handles PROTO_OA_ERROR_RES / ERROR_RES payload types."""
    mocker.patch("twisted.internet.reactor", create=True)

    client = CTraderClient(client_id="id", client_secret="secret", access_token="token")
    client.client = MagicMock()

    mock_extract = mocker.patch("ctrader_open_api.protobuf.Protobuf.extract")
    mock_err = MagicMock()
    mock_err.description = "System error"
    mock_err.errorCode = "SYSTEM_ERROR"
    mock_extract.return_value = mock_err

    # Trigger with ProtoPayloadType.ERROR_RES (which is common model error res)
    msg = MockMessage(ProtoPayloadType.ERROR_RES)
    client._on_message(None, msg)

    assert client._error == "SYSTEM_ERROR: System error"


def test_ctrader_client_send_request_success(mocker: MockerFixture) -> None:
    """Test send_request synchronous response wait succeeds."""
    client = CTraderClient()
    client._is_connected = True
    mock_twisted_client = MagicMock()
    client.client = mock_twisted_client

    expected_response = MagicMock()
    expected_response.payloadType = 12345

    def mock_send(req: Any) -> None:
        assert len(client._message_callbacks) == 1
        cb = client._message_callbacks[0]
        cb(expected_response, 12345)

    mock_twisted_client.send.side_effect = mock_send

    req = MagicMock()
    res = client.send_request(req, response_payload_type=12345, timeout=1.0)
    assert res == expected_response
    assert len(client._message_callbacks) == 0


def test_ctrader_client_send_request_timeout(mocker: MockerFixture) -> None:
    """Test send_request raises ExternalServiceError on timeout."""
    client = CTraderClient()
    client._is_connected = True
    client.client = MagicMock()

    req = MagicMock()
    with pytest.raises(ExternalServiceError, match="Request timed out"):
        client.send_request(req, response_payload_type=12345, timeout=0.01)


def test_ctrader_client_send_request_error(mocker: MockerFixture) -> None:
    """Test send_request raises ExternalServiceError when error response received."""
    client = CTraderClient()
    client._is_connected = True
    mock_twisted_client = MagicMock()
    client.client = mock_twisted_client

    error_response = MagicMock()
    error_response.description = "Auth failed"
    error_response.errorCode = "AUTH_FAILED"

    def mock_send(req: Any) -> None:
        cb = client._message_callbacks[0]
        cb(error_response, ProtoOAPayloadType.PROTO_OA_ERROR_RES)

    mock_twisted_client.send.side_effect = mock_send

    req = MagicMock()
    with pytest.raises(
        ExternalServiceError, match="cTrader request error: AUTH_FAILED: Auth failed"
    ):
        client.send_request(req, response_payload_type=12345, timeout=1.0)


def test_ctrader_client_subscribe_unsubscribe_spots(mocker: MockerFixture) -> None:
    """Test spot price subscription methods."""
    client = CTraderClient()
    client._is_connected = True
    client.client = MagicMock()

    mock_light_sym = MagicMock()
    mock_light_sym.symbolId = 42
    client._symbol_map = {"EURUSD": mock_light_sym}

    mock_send = mocker.patch.object(client, "send_request")

    client.subscribe_spots("EURUSD")
    assert 42 in client._subscribed_symbols
    mock_send.assert_called_once()

    mock_send.reset_mock()
    client.unsubscribe_spots("EURUSD")
    assert 42 not in client._subscribed_symbols
    mock_send.assert_called_once()


def test_ctrader_client_order_calc_margin_and_profit(mocker: MockerFixture) -> None:
    """Test order_calc_margin and order_calc_profit calculations."""
    client = CTraderClient()
    client._is_connected = True
    client.client = MagicMock()

    mock_light_sym = MagicMock()
    mock_light_sym.symbolId = 42
    client._symbol_map = {"EURUSD": mock_light_sym}

    # cTrader margin is a list of ProtoOAExpectedMargin containing buyMargin/sellMargin
    mock_margin = MagicMock()
    mock_margin.volume = 100000
    mock_margin.buyMargin = 150000
    mock_margin.sellMargin = 150000

    mock_margin_res = MagicMock()
    mock_margin_res.margin = [mock_margin]
    mock_margin_res.moneyDigits = 2

    mock_symbol_detail = MagicMock()
    mock_symbol_detail.lotSize = 100000
    mock_symbol_detail_res = MagicMock()
    mock_symbol_detail_res.symbol = [mock_symbol_detail]

    def mock_send_request(req: Any, payload_type: int) -> Any:
        if payload_type == ProtoOAPayloadType.PROTO_OA_EXPECTED_MARGIN_RES:
            return mock_margin_res
        if payload_type == ProtoOAPayloadType.PROTO_OA_SYMBOL_BY_ID_RES:
            return mock_symbol_detail_res
        return MagicMock()

    mocker.patch.object(client, "send_request", side_effect=mock_send_request)

    margin = client.order_calc_margin(0, "EURUSD", 1.0, 1.2)
    assert margin == 1500.0

    profit = client.order_calc_profit(0, "EURUSD", 1.0, 1.2, 1.21)
    assert profit == pytest.approx(1000.0)


def test_ctrader_wrappers_and_helpers(mocker: MockerFixture) -> None:
    """Test get_terminal_info, get_account_info, and other broker wrappers."""
    mock_reactor = mocker.patch("twisted.internet.reactor", create=True)
    mock_reactor.running = True

    client = get_ctrader_client()
    client._is_connected = True
    client._is_account_authorized = True

    mock_trader = MagicMock()
    mock_trader.traderLogin = 999
    mock_trader.ctidTraderAccountId = 123
    mock_trader.accountType = "DEMO"
    mock_trader.brokerName = "MockBroker"
    mock_trader.depositAssetId = 1
    mock_trader.maxLeverage = 100
    mock_trader.balance = 500000
    mock_trader.moneyDigits = 2
    client.trader_info = mock_trader

    term = get_terminal_info()
    assert term is not None
    assert term.connected is True
    assert "cTrader" in term.name

    acc = get_account_info()
    assert acc is not None
    assert acc.login == 999
    assert acc.balance == 5000.0

    mock_light_sym = MagicMock()
    mock_light_sym.symbolId = 10
    mock_light_sym.symbolName = "GBPUSD"
    mock_light_sym.description = "GBP vs USD"
    mock_light_sym.symbolCategoryId = 1
    client._symbol_map = {"GBPUSD": mock_light_sym}
    client._symbol_id_to_name = {10: "GBPUSD"}

    mock_sym = MagicMock()
    mock_sym.digits = 5
    mock_sym.tradingMode = 1
    mock_sym.lotSize = 100000
    mock_sym_res = MagicMock()
    mock_sym_res.symbol = [mock_sym]

    mocker.patch.object(client, "send_request", return_value=mock_sym_res)
    sym = get_symbol_info("GBPUSD")
    assert sym is not None
    assert sym.name == "GBPUSD"
    assert sym.digits == 5

    mock_pos = MagicMock()
    mock_pos.positionId = 101
    mock_pos.tradeData.symbolId = 10
    mock_pos.tradeData.tradeSide = 1
    mock_pos.tradeData.volume = 20000
    mock_pos.price = 120000
    mock_pos.moneyDigits = 2
    mock_reconcile_res = MagicMock()
    mock_reconcile_res.position = [mock_pos]
    mock_reconcile_res.order = []

    mocker.patch.object(client, "send_request", return_value=mock_reconcile_res)
    positions = get_position_info("GBPUSD")
    assert len(positions) == 1
    assert positions[0].ticket == 101
    assert positions[0].volume == 0.2

    # 6. get_order_info
    mock_order = MagicMock()
    mock_order.orderId = 301
    mock_order.tradeData.symbolId = 10
    mock_order.tradeData.tradeSide = 1
    mock_order.tradeData.volume = 10000
    mock_order.orderType = 2
    mock_order.limitPrice = 125000
    mock_order.orderStatus = 1
    mock_reconcile_res.order = [mock_order]

    mocker.patch.object(client, "send_request", return_value=mock_reconcile_res)
    orders = get_order_info("GBPUSD")
    assert len(orders) == 1
    assert orders[0].ticket == 301

    # 7. get_history_order_info & get_history_deal_info
    mock_history_order_res = MagicMock()
    mock_history_order_res.order = [mock_order]
    mocker.patch.object(client, "send_request", return_value=mock_history_order_res)
    hist_orders = get_history_order_info(date_from=1000, date_to=2000, group="GBP")
    assert len(hist_orders) == 1

    mock_deal = MagicMock()
    mock_deal.dealId = 401
    mock_deal.orderId = 301
    mock_deal.positionId = 101
    mock_deal.symbolId = 10
    mock_deal.volume = 10000
    mock_deal.executionPrice = 124000
    mock_deal.tradeSide = 1
    mock_deal.executionTimestamp = 1600000000
    mock_deal.moneyDigits = 2
    mock_deal_res = MagicMock()
    mock_deal_res.deal = [mock_deal]
    mocker.patch.object(client, "send_request", return_value=mock_deal_res)
    deals = get_history_deal_info(date_from=1000, date_to=2000, group="GBP")
    assert len(deals) == 1

    # 8. trade - Action DEAL (New market order)
    mock_exec_event = MagicMock()
    mock_exec_event.order.orderId = 501
    mock_exec_event.deal.dealId = 601
    mocker.patch.object(client, "send_request", return_value=mock_exec_event)
    res_deal = trade(
        {"action": 1, "symbol": "GBPUSD", "volume": 0.1, "type": 0, "price": 1.25}
    )
    assert res_deal.order == 501
    assert res_deal.deal == 601

    # 9. trade - Action DEAL (Close position)
    res_close = trade(
        {
            "action": 1,
            "symbol": "GBPUSD",
            "volume": 0.1,
            "type": 1,
            "position": 101,
            "price": 1.24,
        }
    )
    assert res_close.order == 501

    # 10. trade - Action MODIFY
    res_modify = trade(
        {
            "action": 2,
            "order": 301,
            "price": 1.26,
            "volume": 0.2,
            "sl": 1.20,
            "tp": 1.30,
        }
    )
    assert res_modify.order == 501

    # 11. trade - Action REMOVE
    res_remove = trade({"action": 4, "order": 301})
    assert res_remove.order == 301

    # 12. trade - Action PENDING (Place limit order)
    res_pending = trade(
        {
            "action": 5,
            "symbol": "GBPUSD",
            "volume": 0.1,
            "type": 2,
            "price": 1.23,
            "sl": 1.20,
            "tp": 1.26,
        }
    )
    assert res_pending.order == 501

    # 13. trade - Action SLTP
    res_sltp = trade({"action": 3, "position": 101, "sl": 1.19, "tp": 1.22})
    assert res_sltp.order == 501


def test_ctrader_additional_coverage_details(mocker: MockerFixture) -> None:
    """Test edge cases and exception branches in wrappers to reach 80%+ coverage."""
    client = get_ctrader_client()
    client._is_connected = True
    client._is_account_authorized = True
    client._symbol_map = {}
    client._subscribed_symbols = set()

    # 1. get_symbol_info symbol not in map
    assert get_symbol_info("INVALID") is None

    # 2. get_symbol_info exception path
    client._symbol_map = {"EURUSD": MagicMock()}
    mocker.patch.object(client, "send_request", side_effect=Exception("API error"))
    assert get_symbol_info("EURUSD") is None

    # 3. get_position_info exception path
    assert get_position_info() == []

    # 4. get_order_info exception path
    assert get_order_info() == []

    # 5. get_history_order_info exception path
    assert get_history_order_info() == []

    # 6. get_history_deal_info exception path
    assert get_history_deal_info() == []

    # 7. order_calc_margin edge cases
    assert client.order_calc_margin(0, "INVALID", 1.0, 1.2) is None
    mocker.patch.object(
        client, "send_request", side_effect=Exception("Margin API error")
    )
    assert client.order_calc_margin(0, "EURUSD", 1.0, 1.2) is None

    # 8. order_calc_profit edge cases
    assert client.order_calc_profit(0, "INVALID", 1.0, 1.2, 1.21) is None
    mocker.patch.object(
        client, "send_request", side_effect=Exception("Profit API error")
    )
    assert client.order_calc_profit(0, "EURUSD", 1.0, 1.2, 1.21) is None

    # 9. subscribe_spots/unsubscribe_spots edge cases
    client.subscribe_spots("INVALID")  # Should log warning and return
    client.unsubscribe_spots("INVALID")  # Should return
    client._symbol_map = {"EURUSD": MagicMock(symbolId=42)}
    client.unsubscribe_spots("EURUSD")  # Not subscribed, should return

    # 10. trade unsupported action
    with pytest.raises(ExternalServiceError, match="Unsupported trade action"):
        trade({"action": 999})

    # 11. trade exception handling
    mocker.patch.object(
        client, "send_request", side_effect=Exception("Trade exception")
    )
    with pytest.raises(ExternalServiceError, match="Trade failed"):
        trade(
            {"action": 1, "symbol": "EURUSD", "volume": 0.1, "type": 0, "price": 1.25}
        )

    # 12. get_account_info when trader_info is None
    client.trader_info = None
    assert get_account_info() is None

    # 13. last_error and symbols_total
    client._error = "Test error"
    assert client.last_error() == "Test error"
    client._error = None
    assert client.last_error() == "Success"
    assert client.symbols_total() == 1

    # 14. _ensure_connected path when not connected
    client._is_connected = False
    mock_connect = mocker.patch.object(client, "connect", return_value=True)
    # This should call connect() via _ensure_connected() inside wrappers
    get_terminal_info()
    mock_connect.assert_called_once()


def test_ctrader_account_info_dynamic_currency() -> None:
    """Test CTraderAccountInfo resolves currency dynamically from asset map."""
    from app.services.brokers.ctrader import CTraderAccountInfo

    mock_trader = MagicMock()
    mock_trader.traderLogin = 12345
    mock_trader.ctidTraderAccountId = 9876
    mock_trader.accountType = "DEMO"
    mock_trader.brokerName = "MockBroker"
    mock_trader.depositAssetId = 42
    mock_trader.maxLeverage = 100
    mock_trader.balance = 500000
    mock_trader.moneyDigits = 2

    mock_client = MagicMock()
    mock_client._asset_map = {42: "CHF"}

    # Resolves from client._asset_map
    acc = CTraderAccountInfo(mock_trader, mock_client)
    assert acc.currency == "CHF"

    # Fallback to f"Asset ID {depositAssetId}" when not found in client or map
    acc_fallback = CTraderAccountInfo(mock_trader, None)
    assert acc_fallback.currency == "Asset ID 42"

    # Fallback to hardcoded list (e.g. ID 1 is USD)
    mock_trader_usd = MagicMock()
    mock_trader_usd.depositAssetId = 1
    mock_trader_usd.traderLogin = 12345
    mock_trader_usd.ctidTraderAccountId = 9876
    mock_trader_usd.accountType = "DEMO"
    mock_trader_usd.brokerName = "MockBroker"
    mock_trader_usd.maxLeverage = 100
    mock_trader_usd.balance = 500000
    mock_trader_usd.moneyDigits = 2

    acc_usd = CTraderAccountInfo(mock_trader_usd, None)
    assert acc_usd.currency == "USD"
