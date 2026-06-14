# ruff: noqa: N802, ARG002, TRY002, TRY004
"""Unit tests for the CTraderClient broker service."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from app.core.config import settings
from app.services.brokers.ctrader import CTraderClient, get_ctrader_client
from app.utils.errors import ConfigurationError, ExternalServiceError
from ctrader_open_api.messages.OpenApiCommonModelMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
    ProtoPayloadType,
)
from ctrader_open_api.messages.OpenApiMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
    ProtoOAAccountAuthReq,
    ProtoOAApplicationAuthReq,
    ProtoOAGetAccountListByAccessTokenReq,
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

    class SuccessMockClient(BaseMockClient):
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
            elif isinstance(msg, ProtoOAAccountAuthReq) and self.message_cb:
                self.message_cb(
                    self, MockMessage(ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_RES)
                )

    mocker.patch("app.services.brokers.ctrader.Client", SuccessMockClient)

    # Mock Protobuf extract helper to return mock accounts list
    mock_extract = mocker.patch("ctrader_open_api.protobuf.Protobuf.extract")

    mock_acc = MagicMock()
    mock_acc.ctidTraderAccountId = 12345
    mock_acc.isLive = False

    mock_accounts_res = MagicMock()
    mock_accounts_res.ctidTraderAccount = [mock_acc]

    # We configure extract to return appropriate objects based on message payloadType
    def side_effect(message: Any) -> Any:
        if (
            message.payloadType
            == ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES
        ):
            return mock_accounts_res
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

    class SuccessMockClient(BaseMockClient):
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
            elif isinstance(msg, ProtoOAAccountAuthReq) and self.message_cb:
                self.message_cb(
                    self, MockMessage(ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_RES)
                )

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

    class SuccessMockClient(BaseMockClient):
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
            elif isinstance(msg, ProtoOAAccountAuthReq) and self.message_cb:
                self.message_cb(
                    self, MockMessage(ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_RES)
                )

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
