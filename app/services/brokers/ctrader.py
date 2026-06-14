"""cTrader Open API broker client service.

This module provides the CTraderClient class responsible for managing the lifecycle
of the connection and authorization handshake with the cTrader Open API endpoints.
"""

import threading
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
    ProtoOAApplicationAuthReq,
    ProtoOAGetAccountListByAccessTokenReq,
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
        except Exception as e:  # noqa: BLE001
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

    def _on_connected(self, _client: Any) -> None:  # noqa: ANN401
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
        except Exception as e:  # noqa: BLE001
            logger.exception("Failed to send ProtoOAApplicationAuthReq")
            self._error = f"App auth send error: {e}"
            self._auth_event.set()

    def _on_disconnected(self, _client: Any, reason: Any) -> None:  # noqa: ANN401
        """Callback triggered on socket disconnection."""
        logger.warning("cTrader connection lost. Reason: %s", reason)
        self._is_connected = False
        self._is_app_authenticated = False
        self._is_account_authorized = False
        self._error = str(reason)
        self._connected_event.set()  # Unblock connection wait
        self._auth_event.set()  # Unblock auth wait

    def _on_message(self, _client: Any, message: Any) -> None:  # noqa: ANN401
        """Callback triggered on receiving any protobuf message from cTrader."""
        payload_type = message.payloadType

        try:
            extracted = Protobuf.extract(message)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to extract cTrader protobuf payload: %s", e)
            return

        if payload_type == ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES:
            self._handle_app_auth_res()
        elif (
            payload_type == ProtoOAPayloadType.PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES
        ):
            self._handle_account_list_res(extracted)
        elif payload_type == ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_RES:
            self._handle_account_auth_res()
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
        except Exception as e:  # noqa: BLE001
            logger.exception("Failed to send ProtoOAGetAccountListByAccessTokenReq")
            self._error = f"Account list send error: {e}"
            self._auth_event.set()

    def _handle_account_list_res(self, extracted: Any) -> None:  # noqa: ANN401
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
                self._error = f"Specified account ID {self.account_id} not found."
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
        except Exception as e:  # noqa: BLE001
            logger.exception("Failed to send ProtoOAAccountAuthReq")
            self._error = f"Account auth send error: {e}"
            self._auth_event.set()

    def _handle_account_auth_res(self) -> None:
        """Handle account authorization success response."""
        logger.info("cTrader account %s authorized successfully.", self.account_id)
        self._is_account_authorized = True
        self._auth_event.set()

    def _handle_error_res(self, extracted: Any) -> None:  # noqa: ANN401
        """Handle cTrader error response."""
        err_msg = getattr(extracted, "description", "Unknown error response")
        err_code = getattr(extracted, "errorCode", "UNKNOWN")
        logger.error("cTrader error response received: %s - %s", err_code, err_msg)
        self._error = f"{err_code}: {err_msg}"
        self._auth_event.set()

    @classmethod
    def get_instance(cls) -> "CTraderClient":
        """Get the shared singleton instance of CTraderClient."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_ctrader_client() -> CTraderClient:
    """Get the shared singleton instance of CTraderClient.

    Returns:
        CTraderClient: The shared CTraderClient instance.
    """
    return CTraderClient.get_instance()
