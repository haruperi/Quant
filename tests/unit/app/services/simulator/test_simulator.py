# ruff: noqa: PLR0915
"""Unit tests for the SimulatorClient broker service."""

from datetime import UTC, datetime

import pytest
from app.services.simulator import (
    SimulatorAccountInfo,
    SimulatorClient,
    SimulatorSymbolInfo,
    SimulatorTerminalInfo,
    get_account_info,
    get_ctrader_client,
    get_history_deal_info,
    get_history_order_info,
    get_mt5_client,
    get_order_info,
    get_position_info,
    get_simulator_client,
    get_symbol_info,
    get_terminal_info,
    trade,
)
from app.utils.errors import ConfigurationError, ExternalServiceError
from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def reset_simulator_client(mocker: MockerFixture) -> None:
    """Fixture to reset the SimulatorClient singleton state before each test."""
    client = SimulatorClient.get_instance()
    client._is_connected = False
    client._is_mt5_connected = False
    client.balance = 100000.0
    client.credit = 0.0
    client.positions.clear()
    client.orders.clear()
    client.history_orders.clear()
    client.history_deals.clear()
    client._next_ticket = 100000
    client._next_deal = 500000
    client._error = "Success"

    # Restore default simulation symbols required for unit tests
    client.symbols.update(
        {
            "GBPUSD": {
                "name": "GBPUSD",
                "digits": 5,
                "point": 0.00001,
                "trade_tick_size": 0.00001,
                "trade_contract_size": 100000.0,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01,
                "swap_mode": 1,
                "swap_long": -5.2,
                "swap_short": 1.8,
                "bid": 1.25000,
                "ask": 1.25012,
                "last": 1.25006,
                "spread": 12,
                "description": "Pound vs US Dollar",
                "path": "Forex",
                "trade_mode": 4,
            },
            "USDJPY": {
                "name": "USDJPY",
                "digits": 3,
                "point": 0.001,
                "trade_tick_size": 0.001,
                "trade_contract_size": 100000.0,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01,
                "swap_mode": 1,
                "swap_long": -2.1,
                "swap_short": 0.8,
                "bid": 150.000,
                "ask": 150.015,
                "last": 150.008,
                "spread": 15,
                "description": "US Dollar vs Japanese Yen",
                "path": "Forex",
                "trade_mode": 4,
            },
            "XAUUSD": {
                "name": "XAUUSD",
                "digits": 2,
                "point": 0.01,
                "trade_tick_size": 0.01,
                "trade_contract_size": 100.0,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01,
                "swap_mode": 1,
                "swap_long": -15.0,
                "swap_short": 5.0,
                "bid": 2300.00,
                "ask": 2300.50,
                "last": 2300.25,
                "spread": 50,
                "description": "Gold vs US Dollar",
                "path": "Metals",
                "trade_mode": 4,
            },
        }
    )

    # Force offline fallback mode by default for standard tests
    mocker.patch("MetaTrader5.initialize", return_value=False)


def test_simulator_terminal_info() -> None:
    """Test SimulatorTerminalInfo attributes."""
    info = SimulatorTerminalInfo(connected=True)
    assert info.connected is True
    assert info.trade_allowed is True
    assert info.dlls_allowed is True
    assert info.ping_last == 500
    assert info.company == "HaruQuant AI"
    assert info.name == "HaruQuant Broker Simulator"
    assert info.path == "In-Memory"


def test_simulator_account_info() -> None:
    """Test SimulatorAccountInfo calculation logic."""
    client = SimulatorClient.get_instance()
    client.connect()

    # Check default calculations
    info = SimulatorAccountInfo(client)
    assert info.balance == 100000.0
    assert info.equity == 100000.0
    assert info.profit == 0.0
    assert info.margin == 0.0
    assert info.margin_free == 100000.0
    assert info.margin_level in {1000000.0, 100000.0}
    assert info.leverage == 100


def test_simulator_symbol_info() -> None:
    """Test SimulatorSymbolInfo initialization."""
    sym_data = {
        "name": "EURUSD",
        "description": "Euro",
        "path": "Forex",
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
        "bid": 1.10,
        "ask": 1.11,
        "last": 1.105,
        "spread": 10,
        "trade_mode": 4,
    }
    info = SimulatorSymbolInfo(sym_data)
    assert info.name == "EURUSD"
    assert info.bid == 1.10
    assert info.ask == 1.11
    assert info.trade_contract_size == 100000.0


def test_simulator_client_connection() -> None:
    """Test connect, disconnect, and shutdown methods."""
    client = SimulatorClient.get_instance()
    assert client.is_connected() is False

    assert client.connect() is True
    assert client.is_connected() is True

    client.disconnect()
    assert client.is_connected() is False

    client.connect()
    client.shutdown()
    assert client.is_connected() is False


def test_subscribe_unsubscribe_spots() -> None:
    """Test subscribe and unsubscribe spots."""
    client = SimulatorClient.get_instance()
    client.connect()

    # Success path
    client.subscribe_spots("EURUSD")
    client.unsubscribe_spots("EURUSD")

    # Failure path
    with pytest.raises(ConfigurationError, match="not configured in simulator"):
        client.subscribe_spots("INVALID_SYM")


def test_symbol_info_tick() -> None:
    """Test getting tick details for valid and invalid symbols."""
    client = SimulatorClient.get_instance()
    client.connect()

    tick = client.symbol_info_tick("EURUSD")
    assert tick is not None
    assert tick.bid == 1.10000
    assert tick.ask == 1.10010
    assert tick.last == 1.10005

    assert client.symbol_info_tick("INVALID") is None


def test_order_calc_margin_and_profit() -> None:
    """Test order margin and profit formulas."""
    client = SimulatorClient.get_instance()

    # EURUSD margin: (100000 * 1.0 * 1.10) / 100 = 1100.0
    margin = client.order_calc_margin(action=0, symbol="EURUSD", volume=1.0, price=1.10)
    assert margin == pytest.approx(1100.0)
    assert (
        client.order_calc_margin(action=0, symbol="INVALID", volume=1.0, price=1.10)
        is None
    )

    # EURUSD profit: Buy 1.0 lot open at 1.10, close at 1.12.
    # Calculation: (1.12 - 1.10) * 1.0 * 100000 = 2000.0
    profit = client.order_calc_profit(
        action=0, symbol="EURUSD", volume=1.0, price_open=1.10, price_close=1.12
    )
    assert profit == pytest.approx(2000.0)
    assert (
        client.order_calc_profit(
            action=0, symbol="INVALID", volume=1.0, price_open=1.10, price_close=1.12
        )
        is None
    )


def test_simulator_client_misc_edge_cases() -> None:
    """Test miscellaneous edge cases in SimulatorClient for full coverage."""
    client = SimulatorClient.get_instance()
    client.connect()

    # Test last_error
    assert client.last_error() == "Success"

    # Test symbols_total
    assert client.symbols_total() == 4

    # Test calculate_total_profit when position has an invalid symbol
    client.positions[999] = {
        "ticket": 999,
        "symbol": "INVALID_SYM",
        "type": 0,
        "volume": 1.0,
        "price_open": 1.10,
        "sl": 0.0,
        "tp": 0.0,
        "price_current": 1.10,
        "swap": 0.0,
        "profit": 0.0,
        "magic": 0,
        "time": 0,
        "time_msc": 0,
        "time_update": 0,
        "time_update_msc": 0,
        "identifier": 999,
        "comment": "",
    }
    # calculate_total_profit should skip/ignore the position without throwing
    assert client.calculate_total_profit() == 0.0

    # Test calculate_total_margin when position has an invalid symbol
    # order_calc_margin returns None, so margin shouldn't be added to total
    assert client.calculate_total_margin() == 0.0

    # Test execute_trade close position path with invalid symbol
    # (Since position symbol 'INVALID_SYM' is not in client.symbols)
    close_req = {
        "action": 1,
        "position": 999,
        "volume": 1.0,
    }
    with pytest.raises(ExternalServiceError, match="Invalid symbol"):
        client.execute_trade(close_req)

    # Remove the invalid position
    del client.positions[999]

    # Add a mock position that triggers profit is None -> profit = 0.0 logic
    # To do this, we can mock order_calc_profit to return None
    # Let's mock client.order_calc_profit to return None during close
    original_calc = client.order_calc_profit
    client.order_calc_profit = lambda *_args, **_kwargs: None  # type: ignore[method-assign]

    # Create valid position
    open_res = client.execute_trade(
        {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
        }
    )

    # Close it, profit is None, balance should remain unchanged
    prev_balance = client.balance
    close_res = client.execute_trade(
        {
            "action": 1,
            "position": open_res.order,
            "volume": 0.1,
        }
    )
    assert close_res.comment == "Position closed"
    assert client.balance == prev_balance

    # Restore original function
    client.order_calc_profit = original_calc  # type: ignore[method-assign]


def test_execute_trade_not_connected() -> None:
    """Test execute_trade fails closed when not connected."""
    client = SimulatorClient.get_instance()
    with pytest.raises(ExternalServiceError, match="Client is not connected"):
        client.execute_trade({"action": 1, "symbol": "EURUSD", "volume": 1.0})


def test_execute_trade_market_open_and_close() -> None:
    """Test full cycle of placing market order and closing it."""
    client = SimulatorClient.get_instance()
    client.connect()

    # 1. Open Buy Order
    req = {
        "action": 1,  # TRADE_ACTION_DEAL
        "symbol": "EURUSD",
        "volume": 0.5,
        "type": 0,  # Buy
        "sl": 1.09,
        "tp": 1.12,
        "magic": 12345,
        "comment": "Test buy",
    }
    res = client.execute_trade(req)
    assert res.retcode == 10009
    assert res.order > 0
    assert res.deal > 0
    assert res.comment == "Order executed"

    # Verify position is active
    pos_ticket = res.order
    assert pos_ticket in client.positions
    pos = client.positions[pos_ticket]
    assert pos["volume"] == 0.5
    assert pos["symbol"] == "EURUSD"
    assert pos["sl"] == 1.09
    assert pos["tp"] == 1.12
    assert pos["magic"] == 12345

    # 2. Modify position SL/TP
    mod_req = {
        "action": 3,  # TRADE_ACTION_SLTP
        "position": pos_ticket,
        "sl": 1.085,
        "tp": 1.125,
    }
    mod_res = client.execute_trade(mod_req)
    assert mod_res.comment == "SL/TP modified"
    assert client.positions[pos_ticket]["sl"] == 1.085
    assert client.positions[pos_ticket]["tp"] == 1.125

    # 3. Close the position
    close_req = {
        "action": 1,  # TRADE_ACTION_DEAL
        "position": pos_ticket,
        "volume": 0.5,
        "magic": 12345,
        "comment": "Close buy",
    }
    close_res = client.execute_trade(close_req)
    assert close_res.comment == "Position closed"
    assert pos_ticket not in client.positions
    assert len(client.history_orders) == 2
    assert len(client.history_deals) == 2


def test_execute_trade_partial_close() -> None:
    """Test partial close of a position."""
    client = SimulatorClient.get_instance()
    client.connect()

    req = {
        "action": 1,
        "symbol": "EURUSD",
        "volume": 1.0,
        "type": 0,  # Buy
    }
    res = client.execute_trade(req)
    pos_ticket = res.order

    # Close 0.4 lot of the 1.0 lot position
    close_req = {
        "action": 1,
        "position": pos_ticket,
        "volume": 0.4,
    }
    close_res = client.execute_trade(close_req)
    assert close_res.comment == "Position closed"
    assert client.positions[pos_ticket]["volume"] == 0.6


def test_execute_trade_pending_order_lifecycle() -> None:
    """Test pending order placement, modification, and cancellation."""
    client = SimulatorClient.get_instance()
    client.connect()

    # 1. Place Buy Limit Pending Order
    req = {
        "action": 5,  # TRADE_ACTION_PENDING
        "symbol": "EURUSD",
        "volume": 0.2,
        "type": 2,  # Buy Limit
        "price": 1.0950,
        "sl": 1.0850,
        "tp": 1.1100,
        "comment": "Pending test",
    }
    res = client.execute_trade(req)
    assert res.comment == "Pending order placed"
    ord_ticket = res.order
    assert ord_ticket in client.orders

    # 2. Modify Pending Order
    mod_req = {
        "action": 2,  # TRADE_ACTION_MODIFY
        "order": ord_ticket,
        "price": 1.0960,
        "volume": 0.25,
        "sl": 1.0860,
        "tp": 1.1110,
    }
    mod_res = client.execute_trade(mod_req)
    assert mod_res.comment == "Order modified"
    assert client.orders[ord_ticket]["price_open"] == 1.0960
    assert client.orders[ord_ticket]["volume_current"] == 0.25

    # 3. Cancel Pending Order
    cancel_req = {
        "action": 4,  # TRADE_ACTION_REMOVE
        "order": ord_ticket,
    }
    cancel_res = client.execute_trade(cancel_req)
    assert cancel_res.comment == "Order canceled"
    assert ord_ticket not in client.orders
    assert ord_ticket in client.history_orders
    assert client.history_orders[ord_ticket]["state"] == 2  # Canceled


def test_execute_trade_failures() -> None:
    """Test validation and input failure paths in execute_trade."""
    client = SimulatorClient.get_instance()
    client.connect()

    # Invalid symbol for market order
    with pytest.raises(ExternalServiceError, match="Invalid symbol"):
        client.execute_trade({"action": 1, "symbol": "INVALID", "volume": 1.0})

    # Invalid symbol for pending order
    with pytest.raises(ExternalServiceError, match="Invalid symbol"):
        client.execute_trade({"action": 5, "symbol": "INVALID", "volume": 1.0})

    # Close non-existent position
    with pytest.raises(ExternalServiceError, match="Position not found"):
        client.execute_trade({"action": 1, "position": 999999, "volume": 1.0})

    # Modify non-existent position SL/TP
    with pytest.raises(ExternalServiceError, match="Position not found"):
        client.execute_trade({"action": 3, "position": 999999})

    # Cancel non-existent pending order
    with pytest.raises(ExternalServiceError, match="Order not found"):
        client.execute_trade({"action": 4, "order": 999999})

    # Modify non-existent pending order
    with pytest.raises(ExternalServiceError, match="Order not found"):
        client.execute_trade({"action": 2, "order": 999999})

    # Unsupported action
    with pytest.raises(ExternalServiceError, match="Unsupported trade action"):
        client.execute_trade({"action": 99})


def test_wrapper_getters() -> None:
    """Test the module-level helper wrapper functions."""
    client = get_simulator_client()
    assert client is not None
    assert get_mt5_client() is client
    assert get_ctrader_client() is client

    # Make sure we start connected or getter forces connect
    term = get_terminal_info()
    assert term.connected is True

    acc = get_account_info()
    assert acc.login == client.login

    assert get_symbol_info("EURUSD") is not None
    assert get_symbol_info("INVALID") is None

    # Open a position for position/order/history tests
    trade_res = trade(
        {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
        }
    )

    positions = get_position_info()
    assert len(positions) == 1
    assert positions[0].ticket == trade_res.order

    # Get with ticket filter
    assert len(get_position_info(ticket=trade_res.order)) == 1
    assert len(get_position_info(ticket=999999)) == 0

    # Get with symbol filter
    assert len(get_position_info(symbol="EURUSD")) == 1
    assert len(get_position_info(symbol="GBPUSD")) == 0

    # Place pending order
    pend_res = trade(
        {
            "action": 5,
            "symbol": "EURUSD",
            "volume": 0.15,
            "type": 2,
            "price": 1.09,
        }
    )

    orders = get_order_info()
    assert len(orders) == 1
    assert orders[0].ticket == pend_res.order

    # Get order with ticket filter
    assert len(get_order_info(ticket=pend_res.order)) == 1
    assert len(get_order_info(ticket=999999)) == 0

    # Get order with symbol filter
    assert len(get_order_info(symbol="EURUSD")) == 1
    assert len(get_order_info(symbol="GBPUSD")) == 0


def test_history_wrapper_getters_filters() -> None:
    """Test get_history_order_info and get_history_deal_info with complex filters."""
    client = get_simulator_client()
    client.connect()

    # Place a pending order and cancel it to create history order
    pend_res = client.execute_trade(
        {
            "action": 5,
            "symbol": "EURUSD",
            "volume": 0.10,
            "type": 2,
            "price": 1.09,
        }
    )
    client.execute_trade({"action": 4, "order": pend_res.order})

    # Place a market deal and close it to create history order & deal
    deal_res = client.execute_trade(
        {
            "action": 1,
            "symbol": "GBPUSD",
            "volume": 0.20,
            "type": 0,
        }
    )
    client.execute_trade(
        {
            "action": 1,
            "position": deal_res.order,
            "volume": 0.20,
        }
    )

    # Check history orders
    all_hist_orders = get_history_order_info()
    assert (
        len(all_hist_orders) == 3
    )  # 1 pending cancel + 1 market open + 1 market close

    # Filter history orders by ticket
    assert len(get_history_order_info(ticket=pend_res.order)) == 1

    # Filter history orders by group wildcard
    assert len(get_history_order_info(group="EUR*")) == 1  # only EURUSD
    assert len(get_history_order_info(group="GBP*")) == 2  # open and close of GBPUSD

    # Filter history orders by date
    now_ts = int(datetime.now(UTC).timestamp())
    assert len(get_history_order_info(date_from=now_ts - 10, date_to=now_ts + 10)) == 3
    assert len(get_history_order_info(date_from=now_ts + 100)) == 0
    assert len(get_history_order_info(date_to=now_ts - 100)) == 0

    # Filter by date objects
    dt_from = datetime.fromtimestamp(now_ts - 10, UTC)
    dt_to = datetime.fromtimestamp(now_ts + 10, UTC)
    assert len(get_history_order_info(date_from=dt_from, date_to=dt_to)) == 3

    # Check history deals
    all_hist_deals = get_history_deal_info()
    assert len(all_hist_deals) == 2  # open and close deals

    # Filter history deals by ticket
    first_deal_ticket = all_hist_deals[0].ticket
    assert len(get_history_deal_info(ticket=first_deal_ticket)) == 1

    # Filter history deals by group
    assert len(get_history_deal_info(group="GBP*")) == 2
    assert len(get_history_deal_info(group="EUR*")) == 0

    # Filter history deals by date
    assert len(get_history_deal_info(date_from=now_ts - 10, date_to=now_ts + 10)) == 2
    assert len(get_history_deal_info(date_from=now_ts + 100)) == 0
    assert len(get_history_deal_info(date_to=now_ts - 100)) == 0

    # Filter history deals by datetime objects
    assert len(get_history_deal_info(date_from=dt_from, date_to=dt_to)) == 2


def test_simulator_client_with_mt5_connection(mocker: MockerFixture) -> None:
    """Test SimulatorClient and getters when connected to MT5."""
    mock_init = mocker.patch("MetaTrader5.initialize", return_value=True)
    mock_login = mocker.patch("MetaTrader5.login", return_value=True)
    mock_select = mocker.patch("MetaTrader5.symbol_select", return_value=True)
    mock_shutdown = mocker.patch("MetaTrader5.shutdown")

    mock_term_info = mocker.MagicMock()
    mock_term_info.connected = True
    mocker.patch("MetaTrader5.terminal_info", return_value=mock_term_info)

    # 2. Mock MT5 symbol_info
    mock_sym = mocker.MagicMock()
    mock_sym.name = "EURUSD"
    mock_sym.description = "Euro"
    mock_sym.path = "Forex"
    mock_sym.digits = 5
    mock_sym.point = 0.00001
    mock_sym.trade_tick_size = 0.00001
    mock_sym.trade_contract_size = 100000.0
    mock_sym.volume_min = 0.01
    mock_sym.volume_max = 100.0
    mock_sym.volume_step = 0.01
    mock_sym.swap_mode = 1
    mock_sym.swap_long = -7.6
    mock_sym.swap_short = 3.1
    mock_sym.bid = 1.1234
    mock_sym.ask = 1.1236
    mock_sym.last = 1.1235
    mock_sym.spread = 20
    mock_sym.trade_mode = 4
    mock_symbol_info = mocker.patch("MetaTrader5.symbol_info", return_value=mock_sym)

    # 3. Mock MT5 symbol_info_tick
    mock_tick = mocker.MagicMock()
    mock_tick.bid = 1.1234
    mock_tick.ask = 1.1236
    mock_tick.last = 1.1235
    mock_symbol_info_tick = mocker.patch(
        "MetaTrader5.symbol_info_tick", return_value=mock_tick
    )

    # 4. Mock MT5 margin and profit calculations
    mock_margin_calc = mocker.patch(
        "MetaTrader5.order_calc_margin", return_value=1250.0
    )
    mock_profit_calc = mocker.patch("MetaTrader5.order_calc_profit", return_value=350.0)

    # Execute connect
    client = SimulatorClient.get_instance()
    client._is_connected = False

    assert client.connect() is True
    assert client._is_mt5_connected is True
    mock_init.assert_called_once()
    mock_login.assert_called_once()
    assert mock_select.call_count >= 1

    # Check symbol info retrieval via wrapper
    info = get_symbol_info("EURUSD")
    assert info is not None
    assert info.name == "EURUSD"
    assert info.bid == 1.1234
    assert info.ask == 1.1236
    mock_symbol_info.assert_called_with("EURUSD")

    # Check tick retrieval
    tick = client.symbol_info_tick("EURUSD")
    assert tick is not None
    assert tick.bid == 1.1234
    mock_symbol_info_tick.assert_called_with("EURUSD")

    # Check margin calculation
    margin = client.order_calc_margin(
        action=0, symbol="EURUSD", volume=1.0, price=1.1236
    )
    assert margin == 1250.0
    mock_margin_calc.assert_called_with(0, "EURUSD", 1.0, 1.1236)

    # Check profit calculation
    profit = client.order_calc_profit(
        action=0,
        symbol="EURUSD",
        volume=1.0,
        price_open=1.1200,
        price_close=1.1234,
    )
    assert profit == 350.0
    mock_profit_calc.assert_called_with(0, "EURUSD", 1.0, 1.1200, 1.1234)

    # Test execute_trade using the connected path
    res = client.execute_trade(
        {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
        }
    )
    assert res.comment == "Order executed"
    pos = client.positions[res.order]
    assert pos["price_open"] == 1.1236  # Real mock tick ask

    # Test calculate_total_profit uses MT5
    total_prof = client.calculate_total_profit()
    assert total_prof == 350.0

    # Test disconnect closes MT5 terminal
    client.disconnect()
    assert client._is_mt5_connected is False
    mock_shutdown.assert_called_once()


def test_simulator_client_mt5_init_fail(mocker: MockerFixture) -> None:
    """Test SimulatorClient connect falling back when MT5 initialization fails."""
    mocker.patch("MetaTrader5.initialize", return_value=False)
    mocker.patch("MetaTrader5.last_error", return_value=(-1, "Mock fail"))

    client = SimulatorClient.get_instance()
    client._is_connected = False
    assert client.connect() is True
    assert client._is_mt5_connected is False


def test_simulator_client_mt5_login_fail(mocker: MockerFixture) -> None:
    """Test SimulatorClient connect falling back when MT5 login fails."""
    mocker.patch("MetaTrader5.initialize", return_value=True)
    mocker.patch("MetaTrader5.login", return_value=False)
    mocker.patch("MetaTrader5.last_error", return_value=(-2, "Mock login fail"))
    mock_shutdown = mocker.patch("MetaTrader5.shutdown")

    client = SimulatorClient.get_instance()
    client._is_connected = False
    assert client.connect() is True
    assert client._is_mt5_connected is False
    mock_shutdown.assert_called_once()
