# ruff: noqa: PLR0915
"""Unit tests for the generic Trade classes."""

from unittest.mock import MagicMock

import pytest
from app.routes.brokers import get_broker_module
from app.services.trader import (
    AccountInfo,
    DealInfo,
    HistoryOrderInfo,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TerminalInfo,
    Trade,
)
from app.utils.errors import classify_broker_error, trading_retry_delay
from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def mock_market_weekday(mocker: MockerFixture) -> None:
    """Mock datetime in validation module to always return a weekday."""
    import datetime as real_datetime

    mock_dt = mocker.patch("app.services.trader.validation.datetime.datetime")
    # Make now() return a fixed Wednesday datetime in UTC (June 17, 2026 is Wednesday)
    wednesday_dt = real_datetime.datetime(
        2026, 6, 17, 12, 0, 0, tzinfo=real_datetime.UTC
    )
    mock_dt.now.return_value = wednesday_dt


@pytest.fixture
def mock_broker(mocker: MockerFixture) -> MagicMock:
    """Fixture providing a mock broker module."""
    mock_mod = MagicMock()

    # Mock terminal info data
    term_data = MagicMock()
    term_data.language = "English"
    term_data.company = "MockBroker"
    term_data.name = "MockTerminal"
    term_data.path = "/mock/path"
    term_data.data_path = "/mock/data"
    term_data.commondata_path = "/mock/common"
    term_data.build = 1350
    term_data.connected = True
    term_data.trade_allowed = True
    term_data.dlls_allowed = False
    term_data.ping_last = 500
    mock_mod.get_terminal_info.return_value = term_data

    # Mock account info data
    acc_data = MagicMock()
    acc_data.login = 998877
    acc_data.server = "MockRealServer"
    acc_data.leverage = 500
    acc_data.limit_orders = 100
    acc_data.trade_allowed = True
    acc_data.trade_expert = True
    acc_data.margin_mode = "Hedging"
    acc_data.balance = 10000.0
    acc_data.credit = 100.0
    acc_data.profit = 250.0
    acc_data.equity = 10350.0
    acc_data.margin = 500.0
    acc_data.margin_free = 9850.0
    acc_data.margin_level = 2070.0
    acc_data.name = "John Doe"
    acc_data.currency = "USD"
    acc_data.company = "MockBroker"
    acc_data.margin_so_so = 50.0
    mock_mod.get_account_info.return_value = acc_data

    # Mock symbol info data
    sym_data = MagicMock()
    sym_data.name = "EURUSD"
    sym_data.description = "Euro vs US Dollar"
    sym_data.path = "Forex/EURUSD"
    sym_data.digits = 5
    sym_data.point = 0.00001
    sym_data.trade_tick_size = 0.00001
    sym_data.trade_mode = 4
    sym_data.trade_contract_size = 100000.0
    sym_data.volume_min = 0.01
    sym_data.volume_max = 100.0
    sym_data.volume_step = 0.01
    sym_data.swap_mode = 1
    sym_data.swap_long = -0.5
    sym_data.swap_short = -0.2
    sym_data.bid = 1.08500
    sym_data.ask = 1.08515
    sym_data.last = 1.08507
    sym_data.spread = 15
    mock_mod.get_symbol_info.return_value = sym_data

    # Mock position data
    pos_data = MagicMock()
    pos_data.ticket = 1111
    pos_data.symbol = "EURUSD"
    pos_data.type = 0  # BUY
    pos_data.volume = 0.1
    pos_data.price_open = 1.08000
    pos_data.price_current = 1.08500
    pos_data.sl = 1.07500
    pos_data.tp = 1.09000
    pos_data.swap = 1.5
    pos_data.profit = 50.0
    pos_data.comment = "Mock Position"
    pos_data.time = 1600000000
    pos_data.time_msc = 1600000000000
    pos_data.time_update = 1600000100
    pos_data.time_update_msc = 1600000100000
    pos_data.magic = 12345
    pos_data.identifier = 1111
    mock_mod.get_position_info.return_value = [pos_data]

    # Mock order data
    ord_data = MagicMock()
    ord_data.ticket = 2222
    ord_data.symbol = "EURUSD"
    ord_data.type = 2  # BUY_LIMIT
    ord_data.volume_initial = 0.2
    ord_data.volume_current = 0.2
    ord_data.price_open = 1.07000
    ord_data.price_current = 1.08500
    ord_data.sl = 1.06500
    ord_data.tp = 1.08000
    ord_data.comment = "Mock Pending Order"
    ord_data.time_setup = 1600000000
    ord_data.time_setup_msc = 1600000000000
    ord_data.time_expiration = 1600100000
    ord_data.time_done = 0
    ord_data.time_done_msc = 0
    ord_data.type_time = 0
    ord_data.type_filling = 0
    ord_data.state = 1  # PLACED
    ord_data.magic = 12345
    ord_data.position_id = 0
    ord_data.position_by_id = 0
    ord_data.price_stoplimit = 0.0
    mock_mod.get_order_info.return_value = [ord_data]

    # Mock history order data
    hist_ord_data = MagicMock()
    hist_ord_data.ticket = 3333
    hist_ord_data.symbol = "EURUSD"
    hist_ord_data.type = 0  # BUY
    hist_ord_data.volume_initial = 0.1
    hist_ord_data.volume_current = 0.0
    hist_ord_data.price_open = 1.08100
    hist_ord_data.price_current = 1.08200
    hist_ord_data.sl = 0.0
    hist_ord_data.tp = 0.0
    hist_ord_data.comment = "Mock Hist Order"
    hist_ord_data.time_setup = 1600000000
    hist_ord_data.time_setup_msc = 1600000000000
    hist_ord_data.time_expiration = 0
    hist_ord_data.time_done = 1600000200
    hist_ord_data.time_done_msc = 1600000200000
    hist_ord_data.type_time = 0
    hist_ord_data.type_filling = 0
    hist_ord_data.state = 4  # FILLED
    hist_ord_data.magic = 12345
    hist_ord_data.position_id = 1111
    hist_ord_data.position_by_id = 1111
    hist_ord_data.price_stoplimit = 0.0
    mock_mod.get_history_order_info.return_value = [hist_ord_data]

    # Mock deal data
    deal_data = MagicMock()
    deal_data.ticket = 4444
    deal_data.order = 3333
    deal_data.position_id = 1111
    deal_data.symbol = "EURUSD"
    deal_data.volume = 0.1
    deal_data.price = 1.08100
    deal_data.type = 0  # BUY
    deal_data.entry = 0  # IN
    deal_data.time = 1600000200
    deal_data.time_msc = 1600000200000
    deal_data.commission = -1.5
    deal_data.swap = 0.0
    deal_data.profit = 0.0
    deal_data.magic = 12345
    deal_data.comment = "Mock Deal"
    mock_mod.get_history_deal_info.return_value = [deal_data]

    # Mock trade client
    mock_client = MagicMock()
    mock_client.ORDER_TYPE_BUY = 0
    mock_client.ORDER_TYPE_SELL = 1
    mock_client.ORDER_TYPE_BUY_LIMIT = 2
    mock_client.ORDER_TYPE_SELL_LIMIT = 3
    mock_client.ORDER_TYPE_BUY_STOP = 4
    mock_client.ORDER_TYPE_SELL_STOP = 5
    mock_client.TRADE_ACTION_DEAL = 1
    mock_client.TRADE_ACTION_PENDING = 5
    mock_client.TRADE_ACTION_SLTP = 3
    mock_client.TRADE_ACTION_MODIFY = 2
    mock_client.TRADE_ACTION_REMOVE = 4
    mock_client.ORDER_TIME_GTC = 1

    mock_mod.get_mt5_client.return_value = mock_client
    mock_mod.get_ctrader_client.return_value = mock_client

    # Mock trade result
    trade_res = MagicMock()
    trade_res.order = 5555
    trade_res.deal = 6666
    trade_res.retcode = 10009
    trade_res.volume = 0.02
    trade_res.price = 1.08500
    trade_res.bid = 1.08490
    trade_res.ask = 1.08510
    trade_res.comment = "Request executed"
    mock_mod.trade.return_value = trade_res

    mocker.patch("app.routes.brokers.get_broker_module", return_value=mock_mod)
    mocker.patch(
        "app.services.trader.terminal_info.get_broker_module", return_value=mock_mod
    )
    mocker.patch(
        "app.services.trader.account_info.get_broker_module", return_value=mock_mod
    )
    mocker.patch(
        "app.services.trader.symbol_info.get_broker_module", return_value=mock_mod
    )
    mocker.patch(
        "app.services.trader.order_info.get_broker_module", return_value=mock_mod
    )
    mocker.patch(
        "app.services.trader.history_order_info.get_broker_module",
        return_value=mock_mod,
    )
    mocker.patch(
        "app.services.trader.position_info.get_broker_module", return_value=mock_mod
    )
    mocker.patch(
        "app.services.trader.deal_info.get_broker_module", return_value=mock_mod
    )
    mocker.patch("app.services.trader.trade.get_broker_module", return_value=mock_mod)
    mocker.patch("app.services.trader.trade.get_active_broker_name", return_value="mt5")
    mocker.patch("app.services.brokers.router.get_broker_module", return_value=mock_mod)

    return mock_mod


def test_resolver_mt5(mocker: MockerFixture) -> None:
    """Test broker resolver for MT5."""
    # Resolve resolver import locally
    import app.services.brokers.mt5 as mock_mt5

    mocker.patch("app.routes.brokers.get_broker_module", return_value=mock_mt5)

    res = get_broker_module()
    assert res == mock_mt5


def test_resolver_actual_resolution(mocker: MockerFixture) -> None:
    """Test get_broker_module resolution without mocking the function itself."""
    # Test MT5 resolution
    mocker.patch(
        "app.services.brokers.router.get_active_broker_name", return_value="mt5"
    )
    res_mt5 = get_broker_module()
    from app.services.brokers import mt5

    assert res_mt5 == mt5

    # Test cTrader resolution
    pytest.importorskip("ctrader_open_api")
    mocker.patch(
        "app.services.brokers.router.get_active_broker_name", return_value="ctrader"
    )
    res_ctrader = get_broker_module()
    from app.services.brokers import ctrader

    assert res_ctrader == ctrader

    # Test Simulator resolution
    mocker.patch(
        "app.services.brokers.router.get_active_broker_name", return_value="simulator"
    )
    res_sim = get_broker_module()
    from app.services import simulator

    assert res_sim == simulator


def test_terminal_info(mock_broker: MagicMock) -> None:
    """Test TerminalInfo class wrapper properties."""
    term = TerminalInfo()
    assert term.language() == "English"
    assert term.company() == "MockBroker"
    assert term.name() == "MockTerminal"
    assert term.path() == "/mock/path"
    assert term.data_path() == "/mock/data"
    assert term.common_data_path() == "/mock/common"
    assert term.build() == 1350
    assert term.connected() is True
    assert term.trade_allowed() is True
    assert term.dlls_allowed() is False
    assert term.ping_last() == 500

    assert term.info_integer(0) == 1350
    assert term.info_integer(1) == 1
    assert term.info_integer(3) == 0
    assert term.info_string(0) == "English"
    assert term.info_string(2) == "MockTerminal"


def test_account_info(mock_broker: MagicMock) -> None:
    """Test AccountInfo class wrapper properties."""
    acc = AccountInfo()
    assert acc.login() == 998877
    assert acc.trade_mode() == 2
    assert acc.trade_mode_description() == "Real"
    assert acc.leverage() == 500
    assert acc.limit_orders() == 100
    assert acc.trade_allowed() is True
    assert acc.trade_expert() is True
    assert acc.margin_so_mode() == 0
    assert acc.margin_mode() == 0
    assert acc.margin_mode_description() == "Hedging"
    assert acc.balance() == 10000.0
    assert acc.credit() == 100.0
    assert acc.profit() == 250.0
    assert acc.equity() == 10350.0
    assert acc.margin() == 500.0
    assert acc.free_margin() == 9850.0
    assert acc.free_margin_mode() == 0
    assert acc.margin_level() == 2070.0
    assert acc.margin_so_level() == 50.0
    assert acc.name() == "John Doe"
    assert acc.server() == "MockRealServer"
    assert acc.currency() == "USD"
    assert acc.company() == "MockBroker"

    assert acc.info_integer(0) == 998877
    assert acc.info_integer(2) == 500
    assert acc.info_integer(6) == 0
    assert acc.info_double(0) == 10000.0
    assert acc.info_double(3) == 10350.0
    assert acc.info_string(0) == "John Doe"
    assert acc.info_string(2) == "USD"


def test_symbol_info(mock_broker: MagicMock) -> None:
    """Test SymbolInfo class wrapper properties."""
    sym = SymbolInfo("EURUSD")
    assert sym.name() == "EURUSD"
    assert sym.name("GBPUSD") is True
    assert sym.name() == "GBPUSD"

    sym.name("EURUSD")
    assert sym.refresh() is True
    assert sym.refresh_rates() is True
    assert sym.select(True) is True
    assert sym.is_synchronized() is True
    assert sym.digits() == 5
    assert sym.point() == 0.00001
    assert sym.tick_size() == 0.00001
    assert sym.trade_mode() == 4
    assert sym.trade_mode_description() == "Full Access"
    assert sym.contract_size() == 100000.0
    assert sym.volume_min() == 0.01
    assert sym.volume_max() == 100.0
    assert sym.volume_step() == 0.01
    assert sym.swap_mode() == 1
    assert sym.swap_long() == -0.5
    assert sym.swap_short() == -0.2
    assert sym.bid() == 1.08500
    assert sym.ask() == 1.08515
    assert sym.last() == 1.08507
    assert sym.spread() == 15

    assert sym.info_integer(0) == 5
    assert sym.info_integer(2) == 1
    assert sym.info_double(0) == 0.00001
    assert sym.info_double(3) == 0.01
    assert sym.info_string(0) == "EURUSD"


def test_order_info(mock_broker: MagicMock) -> None:
    """Test OrderInfo class wrapper properties."""
    ord_info = OrderInfo(2222)
    assert ord_info.ticket() == 2222
    assert ord_info.time_setup() == 1600000000
    assert ord_info.time_setup_msc() == 1600000000000
    assert ord_info.time_expiration() == 1600100000
    assert ord_info.time_done() == 0
    assert ord_info.time_done_msc() == 0
    assert ord_info.type() == 2
    assert ord_info.type_description() == "Buy Limit"
    assert ord_info.type_time() == 0
    assert ord_info.type_time_description() == "GTC"
    assert ord_info.type_filling() == 0
    assert ord_info.type_filling_description() == "FOK"
    assert ord_info.state() == 1
    assert ord_info.state_description() == "Placed"
    assert ord_info.magic() == 12345
    assert ord_info.position_id() == 0
    assert ord_info.position_by_id() == 0
    assert ord_info.volume_initial() == 0.2
    assert ord_info.volume_current() == 0.2
    assert ord_info.price_open() == 1.07000
    assert ord_info.stop_loss() == 1.06500
    assert ord_info.take_profit() == 1.08000
    assert ord_info.price_current() == 1.08500
    assert ord_info.price_stop_limit() == 0.0
    assert ord_info.symbol() == "EURUSD"
    assert ord_info.comment() == "Mock Pending Order"

    assert ord_info.info_integer(0) == 2222
    assert ord_info.info_integer(4) == 12345
    assert ord_info.info_double(0) == 0.2
    assert ord_info.info_double(2) == 1.07000
    assert ord_info.info_string(0) == "EURUSD"
    assert ord_info.info_string(1) == "Mock Pending Order"


def test_history_order_info(mock_broker: MagicMock) -> None:
    """Test HistoryOrderInfo class wrapper properties."""
    hist = HistoryOrderInfo()
    assert hist.select(3333) is True
    assert hist.ticket() == 3333
    assert hist.time_setup() == 1600000000
    assert hist.time_setup_msc() == 1600000000000
    assert hist.time_expiration() == 0
    assert hist.time_done() == 1600000200
    assert hist.time_done_msc() == 1600000200000
    assert hist.type() == 0
    assert hist.type_description() == "Buy"
    assert hist.type_time() == 0
    assert hist.type_time_description() == "GTC"
    assert hist.type_filling() == 0
    assert hist.type_filling_description() == "FOK"
    assert hist.state() == 4
    assert hist.state_description() == "Filled"
    assert hist.magic() == 12345
    assert hist.position_id() == 1111
    assert hist.position_by_id() == 1111
    assert hist.volume_initial() == 0.1
    assert hist.volume_current() == 0.0
    assert hist.price_open() == 1.08100
    assert hist.stop_loss() == 0.0
    assert hist.take_profit() == 0.0
    assert hist.price_current() == 1.08200
    assert hist.price_stop_limit() == 0.0
    assert hist.symbol() == "EURUSD"
    assert hist.comment() == "Mock Hist Order"


def test_position_info(mock_broker: MagicMock) -> None:
    """Test PositionInfo class wrapper properties."""
    pos = PositionInfo()
    assert pos.select("EURUSD") is True
    assert pos.ticket() == 1111
    assert pos.time() == 1600000000
    assert pos.time_msc() == 1600000000000
    assert pos.time_update() == 1600000100
    assert pos.time_update_msc() == 1600000100000
    assert pos.type() == 0
    assert pos.type_description() == "Buy"
    assert pos.magic() == 12345
    assert pos.identifier() == 1111
    assert pos.volume() == 0.1
    assert pos.price_open() == 1.08000
    assert pos.stop_loss() == 1.07500
    assert pos.take_profit() == 1.09000
    assert pos.price_current() == 1.08500
    assert pos.swap() == 1.5
    assert pos.profit() == 50.0
    assert pos.symbol() == "EURUSD"
    assert pos.comment() == "Mock Position"


def test_deal_info(mock_broker: MagicMock) -> None:
    """Test DealInfo class wrapper properties."""
    deal = DealInfo(4444)
    assert deal.ticket() == 4444
    assert deal.order() == 3333
    assert deal.time() == 1600000200
    assert deal.time_msc() == 1600000200000
    assert deal.type() == 0
    assert deal.type_description() == "Buy"
    assert deal.entry() == 0
    assert deal.entry_description() == "Entry In"
    assert deal.magic() == 12345
    assert deal.position_id() == 1111
    assert deal.volume() == 0.1
    assert deal.price() == 1.08100
    assert deal.commission() == -1.5
    assert deal.swap() == 0.0
    assert deal.profit() == 0.0
    assert deal.symbol() == "EURUSD"
    assert deal.comment() == "Mock Deal"


def test_trade_actions(mock_broker: MagicMock) -> None:
    """Test Trade class trading execution methods."""
    trade = Trade()
    trade.set_symbol("EURUSD")
    trade.set_order_filling(1)
    trade.set_deviation_in_points(10)
    trade.set_expert_magic_number(54321)

    # Buy
    assert trade.buy(0.05) is True
    assert trade.result_order() == 5555
    assert trade.result_deal() == 6666
    assert trade.result_retcode() == 10009
    assert trade.result_price() == 1.08500
    assert trade.result_volume() == 0.02
    assert trade.result_bid() == 1.08490
    assert trade.result_ask() == 1.08510
    assert trade.result_comment() == "Request executed"
    assert trade._result.request_id.startswith("idem_")
    assert trade._result.correlation_id == trade._result.request_id
    assert trade._result.trace_id == trade._result.correlation_id

    # Sell
    assert trade.sell(0.05) is True
    assert trade.result_order() == 5555

    # BuyLimit
    assert trade.buy_limit(0.1, 1.08000) is True

    # SellLimit
    assert trade.sell_limit(0.1, 1.09000) is True

    # BuyStop
    assert trade.buy_stop(0.1, 1.09000) is True

    # SellStop
    assert trade.sell_stop(0.1, 1.08000) is True

    # PositionOpen
    assert trade.position_open("EURUSD", 0, 0.1, 1.08500, 0.0, 0.0) is True
    assert trade.position_open("EURUSD", 1, 0.1, 1.08500, 0.0, 0.0) is True

    # PositionModify
    assert trade.position_modify("EURUSD", 1.07000, 1.10000) is True

    # PositionClose
    assert trade.position_close("EURUSD") is True

    # OrderModify
    assert trade.order_modify(2222, 1.07500, 1.06500, 1.08500) is True

    # OrderDelete
    assert trade.order_delete(2222) is True


def test_trade_failure(mock_broker: MagicMock) -> None:
    """Test Trade class handling of broker exceptions."""
    mock_broker.trade.side_effect = Exception("Broker rejects request")
    trade = Trade()
    trade.set_symbol("EURUSD")

    assert trade.buy(0.05) is False
    assert trade.result_retcode() == 10001
    assert trade.result_comment() == "Broker rejects request"


def test_kill_switch_blocking(mock_broker: MagicMock) -> None:
    """Test that active kill switch blocks new trade requests."""
    Trade.set_kill_switch(True)
    try:
        trade = Trade()
        trade.set_symbol("EURUSD")
        assert trade.buy(0.05) is False
        assert trade.result_retcode() == 10001
        assert "kill switch" in trade.result_comment().lower()
    finally:
        Trade.set_kill_switch(False)


def test_shutdown_blocking(mock_broker: MagicMock) -> None:
    """Test that graceful shutdown blocks new trade requests."""
    Trade.shutdown(timeout=0.01)
    try:
        trade = Trade()
        trade.set_symbol("EURUSD")
        assert trade.buy(0.05) is False
        assert trade.result_retcode() == 10001
        assert "shutting down" in trade.result_comment().lower()
    finally:
        Trade._is_shutting_down = False


def test_kill_switch_actions(mock_broker: MagicMock) -> None:
    """Test that activating the kill switch cancels pending orders and closes positions.

    Verifies order removal and position close.
    """
    from app.services.trader.store import InMemoryTradeStore, get_default_store

    store = get_default_store()
    assert isinstance(store, InMemoryTradeStore)
    store._idempotency.clear()
    store._orders.clear()
    store._positions.clear()
    store._executions.clear()

    mock_broker.trade.reset_mock()

    Trade.set_kill_switch(True, flatten_positions=True)
    try:
        mock_broker.get_order_info.assert_called()
        mock_broker.get_position_info.assert_called()
        # It should have called trade at least twice (one for remove order,
        # one for close position)
        assert mock_broker.trade.call_count >= 2
    finally:
        Trade.set_kill_switch(False)


def test_service_router_matches_legacy_route(mocker: MockerFixture) -> None:
    """Service-level broker router remains compatible with legacy route wrapper."""
    from app.routes.brokers import get_broker_module as get_route_broker
    from app.services.brokers.router import get_broker_module as get_service_broker

    mocker.patch(
        "app.services.brokers.router.get_active_broker_name", return_value="simulator"
    )

    assert get_route_broker() is get_service_broker()


def test_trade_consumes_rate_limit_token(
    mock_broker: MagicMock, mocker: MockerFixture
) -> None:
    """Outbound trade execution consumes provider rate-limit capacity."""
    limiter = MagicMock()
    limiter.check_rate_limit.return_value = True
    limiter.acquire.return_value = False
    mocker.patch("app.services.trader.readiness.get_rate_limiter", return_value=limiter)
    mocker.patch("app.services.trader.trade.get_rate_limiter", return_value=limiter)

    trade = Trade()
    trade.set_symbol("EURUSD")

    assert trade.buy(0.05) is False
    limiter.acquire.assert_called_once_with()
    assert "Rate limit exceeded" in trade.result_comment()
    mock_broker.trade.assert_not_called()


def test_trading_error_classification_and_retry_delay() -> None:
    """Broker retcodes map to deterministic classifications and retry delays."""
    error = classify_broker_error({"retcode": 10004, "comment": "requote"})

    assert error["code"] == "TIMEOUT"
    assert error["classification"] == "transient"
    assert error["retcode"] == 10004
    assert 0.25 <= trading_retry_delay(0) <= 0.30
