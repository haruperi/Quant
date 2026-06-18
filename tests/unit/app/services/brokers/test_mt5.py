"""Unit tests for the MT5Client broker service."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from app.services.brokers.mt5 import (
    MT5Client,
    get_account_info,
    get_history_deal_info,
    get_history_order_info,
    get_mt5_client,
    get_order_info,
    get_position_info,
    get_symbol_info,
    get_terminal_info,
    trade,
)
from app.utils.errors import ConfigurationError, ExternalServiceError
from app.utils.settings import settings
from pytest_mock import MockerFixture


def test_mt5_client_initialization_defaults() -> None:
    """Test MT5Client initialization fallback to settings defaults."""
    client = MT5Client()
    assert client.path == settings.mt5_terminal_path

    # settings.mt5_login is string in config, MT5Client parses to int
    expected_login = int(settings.mt5_login) if settings.mt5_login.isdigit() else None
    assert client.login == expected_login
    assert client.password == settings.mt5_password
    assert client.server == settings.mt5_server
    assert len(client.default_symbols) > 0


def test_mt5_client_initialization_custom() -> None:
    """Test MT5Client initialization with custom parameters."""
    custom_symbols = ["EURUSD", "GBPUSD"]
    client = MT5Client(
        path="C:\\custom\\path.exe",
        login=123456,
        password="custom_password",  # pragma: allowlist secret
        server="custom_server",
        default_symbols=custom_symbols,
    )
    assert client.path == "C:\\custom\\path.exe"
    assert client.login == 123456
    assert client.password == "custom_password"  # pragma: allowlist secret
    assert client.server == "custom_server"
    assert client.default_symbols == custom_symbols


def test_mt5_client_connect_success(mocker: MockerFixture) -> None:
    """Test successful MT5 connect and login sequence."""
    # Mock mt5 library calls
    mock_init = mocker.patch("MetaTrader5.initialize", return_value=True)
    mock_login = mocker.patch("MetaTrader5.login", return_value=True)
    mock_symbol_select = mocker.patch("MetaTrader5.symbol_select", return_value=True)

    client = MT5Client(login=123456, password="pwd", server="server")
    result = client.connect()

    assert result is True
    mock_init.assert_called_once()
    mock_login.assert_called_once_with(
        123456,
        password="pwd",  # pragma: allowlist secret
        server="server",
    )
    assert mock_symbol_select.call_count == len(client.default_symbols)


def test_mt5_client_connect_missing_credentials(mocker: MockerFixture) -> None:
    """Test connect raising ConfigurationError when credentials are missing."""
    mocker.patch.object(settings, "mt5_login", "")
    client = MT5Client(login=None)
    with pytest.raises(ConfigurationError, match="login account ID is required"):
        client.connect()

    mocker.patch.object(settings, "mt5_password", "")
    client2 = MT5Client(login=123456, password="")
    with pytest.raises(ConfigurationError, match="password is required"):
        client2.connect()

    mocker.patch.object(settings, "mt5_server", "")
    client3 = MT5Client(login=123456, password="pwd", server="")
    with pytest.raises(ConfigurationError, match="server name is required"):
        client3.connect()


def test_mt5_client_connect_initialize_failure(mocker: MockerFixture) -> None:
    """Test connect raising ExternalServiceError when initialization fails."""
    mocker.patch("MetaTrader5.initialize", return_value=False)
    mocker.patch("MetaTrader5.last_error", return_value=(1, "Init failed error"))

    client = MT5Client(login=123456, password="pwd", server="server")
    with pytest.raises(
        ExternalServiceError, match="MetaTrader 5 initialization failed"
    ):
        client.connect()


def test_mt5_client_connect_initialize_exception(mocker: MockerFixture) -> None:
    """Test connect raising ExternalServiceError when initialization crashes."""
    mocker.patch("MetaTrader5.initialize", side_effect=Exception("Init crash"))

    client = MT5Client(login=123456, password="pwd", server="server")
    with pytest.raises(
        ExternalServiceError,
        match="Failed to initialize MetaTrader 5 due to an exception",
    ):
        client.connect()


def test_mt5_client_connect_login_failure(mocker: MockerFixture) -> None:
    """Test connect raising ExternalServiceError when login fails."""
    mocker.patch("MetaTrader5.initialize", return_value=True)
    mocker.patch("MetaTrader5.login", return_value=False)
    mocker.patch("MetaTrader5.last_error", return_value=(2, "Login failed error"))
    mock_shutdown = mocker.patch("MetaTrader5.shutdown")

    client = MT5Client(login=123456, password="pwd", server="server")
    with pytest.raises(ExternalServiceError, match="MetaTrader 5 login failed"):
        client.connect()

    # Terminal must be shut down to release resource if login fails
    mock_shutdown.assert_called_once()


def test_mt5_client_connect_login_exception(mocker: MockerFixture) -> None:
    """Test connect raising ExternalServiceError when login raises exception."""
    mocker.patch("MetaTrader5.initialize", return_value=True)
    mocker.patch("MetaTrader5.login", side_effect=Exception("Login crash"))
    mock_shutdown = mocker.patch("MetaTrader5.shutdown")

    client = MT5Client(login=123456, password="pwd", server="server")
    with pytest.raises(
        ExternalServiceError,
        match="Failed to login to MetaTrader 5 due to an exception",
    ):
        client.connect()

    mock_shutdown.assert_called_once()


def test_mt5_client_connect_symbol_failure(mocker: MockerFixture) -> None:
    """Test connect succeeding even when some symbol selections fail."""
    mocker.patch("MetaTrader5.initialize", return_value=True)
    mocker.patch("MetaTrader5.login", return_value=True)

    # Fail selection for EURUSD only, succeed for others
    def side_effect(symbol: str, select: bool) -> bool:
        return symbol != "EURUSD"

    mocker.patch("MetaTrader5.symbol_select", side_effect=side_effect)
    mocker.patch("MetaTrader5.last_error", return_value=(3, "Symbol error"))

    client = MT5Client(login=123456, password="pwd", server="server")
    result = client.connect()

    assert result is True


def test_mt5_client_connect_symbol_exception(mocker: MockerFixture) -> None:
    """Test connect succeeding even when symbol selection raises an exception."""
    mocker.patch("MetaTrader5.initialize", return_value=True)
    mocker.patch("MetaTrader5.login", return_value=True)

    # Throw exception for EURUSD, succeed for others
    def side_effect(symbol: str, select: bool) -> bool:
        if symbol == "EURUSD":
            raise ValueError("Symbol select crash")
        return True

    mocker.patch("MetaTrader5.symbol_select", side_effect=side_effect)

    client = MT5Client(login=123456, password="pwd", server="server")
    result = client.connect()

    assert result is True


def test_mt5_client_is_connected_true(mocker: MockerFixture) -> None:
    """Test is_connected returning True when terminal is connected."""
    mock_terminal_info = MagicMock()
    mock_terminal_info.connected = True
    mocker.patch("MetaTrader5.terminal_info", return_value=mock_terminal_info)

    client = MT5Client()
    assert client.is_connected() is True


def test_mt5_client_is_connected_false(mocker: MockerFixture) -> None:
    """Test is_connected returning False when terminal is not connected."""
    mock_terminal_info = MagicMock()
    mock_terminal_info.connected = False
    mocker.patch("MetaTrader5.terminal_info", return_value=mock_terminal_info)

    client = MT5Client()
    assert client.is_connected() is False


def test_mt5_client_is_connected_none(mocker: MockerFixture) -> None:
    """Test is_connected returning False when terminal_info returns None."""
    mocker.patch("MetaTrader5.terminal_info", return_value=None)

    client = MT5Client()
    assert client.is_connected() is False


def test_mt5_client_is_connected_exception(mocker: MockerFixture) -> None:
    """Test is_connected returning False on exceptions."""
    mocker.patch("MetaTrader5.terminal_info", side_effect=Exception("Terminal down"))

    client = MT5Client()
    assert client.is_connected() is False


def test_mt5_client_shutdown_success(mocker: MockerFixture) -> None:
    """Test graceful shutdown."""
    mock_shutdown = mocker.patch("MetaTrader5.shutdown")

    client = MT5Client()
    client.shutdown()
    mock_shutdown.assert_called_once()


def test_mt5_client_shutdown_exception(mocker: MockerFixture) -> None:
    """Test shutdown handles exceptions without raising."""
    mocker.patch("MetaTrader5.shutdown", side_effect=Exception("Shutdown error"))

    client = MT5Client()
    # Should not raise exception
    client.shutdown()


def test_mt5_client_connect_path_none(mocker: MockerFixture) -> None:
    """Test connect when terminal path is None."""
    mocker.patch("MetaTrader5.initialize", return_value=True)
    mocker.patch("MetaTrader5.login", return_value=True)
    mocker.patch("MetaTrader5.symbol_select", return_value=True)
    mocker.patch.object(settings, "mt5_terminal_path", "")

    client = MT5Client(path="", login=123456, password="pwd", server="server")
    result = client.connect()
    assert result is True


def test_mt5_client_login_account_none() -> None:
    """Test _login_account raising ConfigurationError when login is None."""
    client = MT5Client()
    client.login = None
    with pytest.raises(ConfigurationError, match="login account ID is required"):
        client._login_account()


def test_get_mt5_client_singleton() -> None:
    """Test get_mt5_client returns a singleton instance."""
    client1 = get_mt5_client()
    client2 = get_mt5_client()
    assert client1 is client2
    assert isinstance(client1, MT5Client)


def test_ensure_connected_triggers_connect(mocker: MockerFixture) -> None:
    """Test wrapper functions trigger connect when client is disconnected."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", side_effect=[False, True])
    mock_connect = mocker.patch.object(client, "connect", return_value=True)

    # Calling a wrapper function should trigger connect
    mocker.patch("MetaTrader5.terminal_info", return_value=MagicMock())
    get_terminal_info()

    mock_connect.assert_called_once()


def test_get_terminal_info(mocker: MockerFixture) -> None:
    """Test get_terminal_info wrapper."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mock_data = MagicMock()
    mock_terminal = mocker.patch("MetaTrader5.terminal_info", return_value=mock_data)

    res = get_terminal_info()
    assert res is mock_data
    mock_terminal.assert_called_once()


def test_get_account_info(mocker: MockerFixture) -> None:
    """Test get_account_info wrapper."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mock_data = MagicMock()
    mock_account = mocker.patch("MetaTrader5.account_info", return_value=mock_data)

    res = get_account_info()
    assert res is mock_data
    mock_account.assert_called_once()


def test_get_symbol_info(mocker: MockerFixture) -> None:
    """Test get_symbol_info wrapper select and retrieval."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mock_select = mocker.patch("MetaTrader5.symbol_select", return_value=True)
    mock_data = MagicMock()
    mock_info = mocker.patch("MetaTrader5.symbol_info", return_value=mock_data)

    res = get_symbol_info("EURUSD")
    assert res is mock_data
    mock_select.assert_called_once_with("EURUSD", True)
    mock_info.assert_called_once_with("EURUSD")


def test_get_position_info(mocker: MockerFixture) -> None:
    """Test get_position_info wrapper with and without arguments."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mock_get = mocker.patch("MetaTrader5.positions_get", return_value=())

    get_position_info()
    mock_get.assert_called_with()

    get_position_info(symbol="EURUSD")
    mock_get.assert_called_with(symbol="EURUSD")

    get_position_info(ticket=123)
    mock_get.assert_called_with(ticket=123)


def test_get_order_info(mocker: MockerFixture) -> None:
    """Test get_order_info wrapper with and without arguments."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mock_get = mocker.patch("MetaTrader5.orders_get", return_value=())

    get_order_info()
    mock_get.assert_called_with()

    get_order_info(symbol="EURUSD")
    mock_get.assert_called_with(symbol="EURUSD")

    get_order_info(ticket=123)
    mock_get.assert_called_with(ticket=123)


def test_get_history_order_info(mocker: MockerFixture) -> None:
    """Test get_history_order_info wrapper with filters."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mock_get = mocker.patch("MetaTrader5.history_orders_get", return_value=())

    get_history_order_info()
    args, kwargs = mock_get.call_args
    assert args[0] == 1
    assert isinstance(args[1], datetime)
    assert not kwargs

    get_history_order_info(ticket=123)
    mock_get.assert_called_with(ticket=123)

    get_history_order_info(date_from=1000, date_to=2000, group="*EUR*")
    mock_get.assert_called_with(1000, 2000, group="*EUR*")


def test_get_history_deal_info(mocker: MockerFixture) -> None:
    """Test get_history_deal_info wrapper with filters."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mock_get = mocker.patch("MetaTrader5.history_deals_get", return_value=())

    get_history_deal_info()
    args, kwargs = mock_get.call_args
    assert args[0] == 1
    assert isinstance(args[1], datetime)
    assert not kwargs

    get_history_deal_info(ticket=123)
    mock_get.assert_called_with(ticket=123)

    get_history_deal_info(date_from=1000, date_to=2000, group="*EUR*")
    mock_get.assert_called_with(1000, 2000, group="*EUR*")


def test_trade_success(mocker: MockerFixture) -> None:
    """Test trade wrapper success path."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mock_res = MagicMock()
    mock_res.retcode = 10009  # TRADE_RETCODE_DONE
    mock_send = mocker.patch("MetaTrader5.order_send", return_value=mock_res)

    req = {"action": 1}
    res = trade(req)
    assert res is mock_res
    mock_send.assert_called_once_with(req)


def test_trade_rejection(mocker: MockerFixture) -> None:
    """Test trade wrapper order rejection retcode."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mock_res = MagicMock()
    mock_res.retcode = 10015  # Rejected retcode
    mock_res.comment = "Rejected comment"
    mocker.patch("MetaTrader5.order_send", return_value=mock_res)

    with pytest.raises(ExternalServiceError, match="Trade order rejected"):
        trade({"action": 1})


def test_trade_none_result(mocker: MockerFixture) -> None:
    """Test trade wrapper returning None raises ExternalServiceError."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mocker.patch("MetaTrader5.order_send", return_value=None)
    mocker.patch("MetaTrader5.last_error", return_value=(999, "send error"))

    with pytest.raises(ExternalServiceError, match="Trade execution failed"):
        trade({"action": 1})


def test_trade_exception(mocker: MockerFixture) -> None:
    """Test trade wrapper exception raising ExternalServiceError."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mocker.patch("MetaTrader5.order_send", side_effect=Exception("API Crash"))

    with pytest.raises(
        ExternalServiceError, match="Failed to send trade order due to exception"
    ):
        trade({"action": 1})


def test_mt5_client_delegation_success(mocker: MockerFixture) -> None:
    """Test lookup delegation to MetaTrader5 library."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mocker.patch("MetaTrader5.symbols_total", return_value=500)

    assert client.symbols_total() == 500


def test_mt5_client_delegation_auto_connect(mocker: MockerFixture) -> None:
    """Test lookup delegation triggers auto-connect for callable attributes."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", side_effect=[False, True])
    mock_connect = mocker.patch.object(client, "connect", return_value=True)
    mocker.patch("MetaTrader5.symbols_total", return_value=500)

    assert client.symbols_total() == 500
    mock_connect.assert_called_once()


def test_mt5_client_delegation_constants(mocker: MockerFixture) -> None:
    """Test lookup delegation for non-callable attributes (constants)."""
    client = get_mt5_client()
    mocker.patch.object(client, "is_connected", return_value=True)
    mocker.patch("MetaTrader5.TRADE_ACTION_DEAL", 1, create=True)

    mock_connect = mocker.patch.object(client, "connect")
    assert client.TRADE_ACTION_DEAL == 1
    mock_connect.assert_not_called()


def test_mt5_client_delegation_attribute_error() -> None:
    """Test delegation raising AttributeError for missing library attributes."""
    client = get_mt5_client()
    with pytest.raises(
        AttributeError,
        match="'MT5Client' object has no attribute 'non_existent_method'",
    ):
        _ = client.non_existent_method
