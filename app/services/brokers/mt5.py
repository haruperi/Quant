"""MetaTrader 5 broker client service.

This module provides the MT5Client class responsible for managing the lifecycle
of the MetaTrader 5 terminal connection, user authentication, and Market Watch
symbol registration.
"""

from datetime import UTC, datetime
from typing import Any

import MetaTrader5 as mt5  # type: ignore[import-untyped, unused-ignore]  # noqa: N813

from app.core.config import settings
from app.utils.errors import ConfigurationError, ExternalServiceError
from app.utils.logger import logger


class MT5Client:
    """Client for interacting with the MetaTrader 5 trading terminal.

    Handles terminal initialization, user account authentication, checking the
    connection status, selecting default symbols in Market Watch, and closing
    the connection.
    """

    _instance: "MT5Client | None" = None

    def __init__(
        self,
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        default_symbols: list[str] | None = None,
    ) -> None:
        """Initialize the MetaTrader 5 client with credentials and configuration.

        Args:
            path: Absolute path to the terminal64.exe executable.
            login: MetaTrader 5 account login ID.
            password: Password for the trading account.
            server: Trading server name.
            default_symbols: List of symbols to automatically select in Market Watch.
        """
        # Resolve config from parameters or settings fallback
        self.path = path or settings.mt5_terminal_path

        # Parse login ID
        raw_login = login if login is not None else settings.mt5_login
        if isinstance(raw_login, str) and raw_login.strip().isdigit():
            self.login: int | None = int(raw_login)
        elif isinstance(raw_login, int):
            self.login = raw_login
        else:
            self.login = None

        self.password = password or settings.mt5_password
        self.server = server or settings.mt5_server

        self.default_symbols = (
            default_symbols
            if default_symbols is not None
            else [
                "EURUSD",
                "GBPUSD",
                "USDJPY",
                "AUDUSD",
                "USDCAD",
                "USDCHF",
                "NZDUSD",
            ]
        )

        logger.info(
            "MT5Client initialized",
            extra={
                "path": self.path,
                "login": self.login,
                "server": self.server,
                "default_symbols_count": len(self.default_symbols),
            },
        )

    def connect(self) -> bool:
        """Start and initialize MT5 terminal, and login to the trading account.

        This method first attempts to initialize the MT5 terminal. Once initialized,
        it logs in to the specified trading account. Finally, it attempts to select
        all default symbols in the Market Watch.

        Returns:
            bool: True if connection, login, and symbol selection were completed
                successfully.

        Raises:
            ConfigurationError: If the account credentials or path are missing
                or invalid.
            ExternalServiceError: If MT5 initialization or account login fails.
        """
        self._validate_credentials()
        self._initialize_terminal()

        try:
            self._login_account()
        except Exception:
            # Ensure cleanup if login fails or throws
            mt5.shutdown()
            raise

        self._select_default_symbols()
        return True

    def _validate_credentials(self) -> None:
        """Validate that required MT5 credentials are provided."""
        if not self.login:
            msg = "MT5 login account ID is required."
            logger.error(msg)
            raise ConfigurationError(msg)
        if not self.password:
            msg = "MT5 password is required."
            logger.error(msg)
            raise ConfigurationError(msg)
        if not self.server:
            msg = "MT5 server name is required."
            logger.error(msg)
            raise ConfigurationError(msg)

    def _initialize_terminal(self) -> None:
        """Initialize the MT5 terminal connection."""
        logger.info("Initializing MetaTrader 5 terminal...")
        init_kwargs: dict[str, Any] = {}
        if self.path:
            init_kwargs["path"] = self.path

        try:
            init_success = mt5.initialize(**init_kwargs)
        except Exception as e:
            msg = f"Failed to initialize MetaTrader 5 due to an exception: {e}"
            logger.exception(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

        if not init_success:
            err_code = mt5.last_error()
            msg = f"MetaTrader 5 initialization failed. Error code: {err_code}"
            logger.error(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

        logger.info("MetaTrader 5 terminal initialized successfully.")

    def _login_account(self) -> None:
        """Log in to the trading account on the initialized terminal."""
        logger.info("Logging in to MetaTrader 5 account...")
        if self.login is None:
            msg = "MT5 login account ID is required."
            logger.error(msg)
            raise ConfigurationError(msg)
        try:
            login_success = mt5.login(
                self.login,
                password=self.password,
                server=self.server,
            )
        except Exception as e:
            msg = f"Failed to login to MetaTrader 5 due to an exception: {e}"
            logger.exception(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

        if not login_success:
            err_code = mt5.last_error()
            msg = (
                f"MetaTrader 5 login failed for account {self.login}. "
                f"Error code: {err_code}"
            )
            logger.error(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

        logger.info("Successfully logged in to MT5 account: %s", self.login)

    def _select_default_symbols(self) -> None:
        """Add all default symbols to the terminal Market Watch."""
        successful_symbols = []
        failed_symbols = []
        for symbol in self.default_symbols:
            try:
                selected = mt5.symbol_select(symbol, True)
                if selected:
                    successful_symbols.append(symbol)
                else:
                    err_code = mt5.last_error()
                    failed_symbols.append((symbol, err_code))
                    logger.warning(
                        "Failed to select symbol %s in Market Watch. Error code: %s",
                        symbol,
                        err_code,
                    )
            except Exception as e:  # noqa: BLE001
                failed_symbols.append((symbol, str(e)))
                logger.warning("Exception while selecting symbol %s: %s", symbol, e)

        logger.info(
            "Market Watch symbol selection complete",
            extra={
                "successful_count": len(successful_symbols),
                "failed_count": len(failed_symbols),
                "successful_symbols": successful_symbols,
                "failed_symbols": failed_symbols,
            },
        )

    def is_connected(self) -> bool:
        """Check if client is currently connected to the MT5 terminal and server.

        Returns:
            bool: True if connected to MT5 terminal and trading server, False otherwise.
        """
        try:
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                return False
            return bool(terminal_info.connected)
        except Exception as e:  # noqa: BLE001
            logger.debug("Error checking MT5 connection status: %s", e)
            return False

    def shutdown(self) -> None:
        """Shutdown the MT5 terminal connection and clean up resources."""
        logger.info("Shutting down MetaTrader 5 terminal connection...")
        try:
            mt5.shutdown()
            logger.info("MetaTrader 5 terminal connection shut down successfully.")
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Error during MetaTrader 5 shutdown: %s",
                e,
                exc_info=True,
            )

    @classmethod
    def get_instance(cls) -> "MT5Client":
        """Get the shared singleton instance of MT5Client."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Delegate attribute/method calls to the underlying MetaTrader5 library.

        This allows callers of MT5Client to access any MT5 library functions
        (e.g., symbols_total, symbol_info_tick) directly.

        Args:
            name: The name of the attribute or method to look up in mt5.

        Returns:
            Any: The attribute or method from MetaTrader5.

        Raises:
            AttributeError: If the attribute/method does not exist in MetaTrader5.
        """
        if hasattr(mt5, name):
            attr = getattr(mt5, name)
            if callable(attr) and not self.is_connected():
                logger.info(
                    "MT5 client not connected. Auto-connecting on delegated call: %s",
                    name,
                )
                self.connect()
            return attr
        msg = f"'MT5Client' object has no attribute '{name}'"
        raise AttributeError(msg)


__all__ = [
    "MT5Client",
    "get_account_info",
    "get_history_deal_info",
    "get_history_order_info",
    "get_mt5_client",
    "get_order_info",
    "get_position_info",
    "get_symbol_info",
    "get_terminal_info",
    "trade",
]


def get_mt5_client() -> MT5Client:
    """Get the shared singleton instance of MT5Client.

    If the instance does not exist, it is created.

    Returns:
        MT5Client: The shared MT5Client instance.
    """
    return MT5Client.get_instance()


def _ensure_connected() -> None:
    """Ensure the shared MT5Client is initialized and connected."""
    client = get_mt5_client()
    if not client.is_connected():
        logger.info("MT5 client is not connected. Attempting auto-connection...")
        client.connect()


def get_terminal_info() -> Any:  # noqa: ANN401
    """Get the MT5 terminal settings and status.

    Returns:
        Any: Named tuple with terminal info or None.
    """
    _ensure_connected()
    return mt5.terminal_info()


def get_account_info() -> Any:  # noqa: ANN401
    """Get information on the current trading account.

    Returns:
        Any: Named tuple with account info or None.
    """
    _ensure_connected()
    return mt5.account_info()


def get_symbol_info(symbol: str) -> Any:  # noqa: ANN401
    """Get information about a specific symbol.

    Args:
        symbol: Financial instrument name.

    Returns:
        Any: Named tuple with symbol info or None.
    """
    _ensure_connected()
    mt5.symbol_select(symbol, True)
    return mt5.symbol_info(symbol)


def get_position_info(symbol: str | None = None, ticket: int | None = None) -> Any:  # noqa: ANN401
    """Get open positions filtered by symbol or ticket.

    Args:
        symbol: Optional symbol filter.
        ticket: Optional position ticket filter.

    Returns:
        Any: Tuple of named tuples with position details or None.
    """
    _ensure_connected()
    if ticket is not None:
        return mt5.positions_get(ticket=ticket)
    if symbol is not None:
        return mt5.positions_get(symbol=symbol)
    return mt5.positions_get()


def get_order_info(symbol: str | None = None, ticket: int | None = None) -> Any:  # noqa: ANN401
    """Get active pending orders filtered by symbol or ticket.

    Args:
        symbol: Optional symbol filter.
        ticket: Optional order ticket filter.

    Returns:
        Any: Tuple of named tuples with pending order details or None.
    """
    _ensure_connected()
    if ticket is not None:
        return mt5.orders_get(ticket=ticket)
    if symbol is not None:
        return mt5.orders_get(symbol=symbol)
    return mt5.orders_get()


def get_history_order_info(
    date_from: Any = None,  # noqa: ANN401
    date_to: Any = None,  # noqa: ANN401
    group: str | None = None,
    ticket: int | None = None,
) -> Any:  # noqa: ANN401
    """Get historical orders from the specified time frame or ticket.

    Args:
        date_from: Start date (datetime, timestamp, or None).
        date_to: End date (datetime, timestamp, or None).
        group: Filter by symbol group.
        ticket: Filter by specific order ticket.

    Returns:
        Any: Tuple of named tuples with historical order details or None.
    """
    _ensure_connected()
    if ticket is not None:
        return mt5.history_orders_get(ticket=ticket)

    from_val = date_from if date_from is not None else 1
    to_val = date_to if date_to is not None else datetime.now(UTC)

    if group is not None:
        return mt5.history_orders_get(from_val, to_val, group=group)
    return mt5.history_orders_get(from_val, to_val)


def get_history_deal_info(
    date_from: Any = None,  # noqa: ANN401
    date_to: Any = None,  # noqa: ANN401
    group: str | None = None,
    ticket: int | None = None,
) -> Any:  # noqa: ANN401
    """Get historical deals from the specified time frame or ticket.

    Args:
        date_from: Start date (datetime, timestamp, or None).
        date_to: End date (datetime, timestamp, or None).
        group: Filter by symbol group.
        ticket: Filter by specific deal ticket.

    Returns:
        Any: Tuple of named tuples with historical deal details or None.
    """
    _ensure_connected()
    if ticket is not None:
        return mt5.history_deals_get(ticket=ticket)

    from_val = date_from if date_from is not None else 1
    to_val = date_to if date_to is not None else datetime.now(UTC)

    if group is not None:
        return mt5.history_deals_get(from_val, to_val, group=group)
    return mt5.history_deals_get(from_val, to_val)


def trade(request: dict[str, Any]) -> Any:  # noqa: ANN401
    """Send a trading request to the MT5 terminal.

    Args:
        request: Dictionary containing trading parameters.

    Returns:
        Any: OrderSendResult named tuple containing response details.

    Raises:
        ExternalServiceError: If the trade execution fails or returns an error.
    """
    _ensure_connected()
    try:
        result = mt5.order_send(request)
    except Exception as e:
        msg = f"Failed to send trade order due to exception: {e}"
        logger.exception(msg)
        raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

    if result is None:
        err_code = mt5.last_error()
        msg = f"Trade execution failed: order_send returned None. Error: {err_code}"
        logger.error(msg)
        raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

    if hasattr(result, "retcode") and result.retcode not in (10009, 10008):
        msg = (
            f"Trade order rejected. Retcode: {result.retcode}, "
            f"Comment: {getattr(result, 'comment', '')}"
        )
        logger.error(msg)
        raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

    return result
