# ruff: noqa
"""Unit tests for simulator EventDrivenExecutionEngine and SimTrader query/trade semantics."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.simulation.engine import EventDrivenExecutionEngine
from app.services.simulation.trader import SimTrader
from app.services.simulation.validation.schema import SymbolSpec
from app.utils.errors import SimulationError


@pytest.fixture
def symbol_spec() -> SymbolSpec:
    """SymbolSpec fixture."""
    return SymbolSpec(
        symbol="EURUSD",
        point=Decimal("0.00001"),
        tick_size=Decimal("0.00001"),
        tick_value=Decimal("1.0"),
        contract_size=Decimal("100000.0"),
        volume_min=Decimal("0.01"),
        volume_max=Decimal("100.0"),
        volume_step=Decimal("0.01"),
    )


def test_engine_accounting(symbol_spec: SymbolSpec) -> None:
    """Test engine balance, equity, and floating PnL tracking."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))

    # Execute market BUY order of 1 lot at 1.10000
    engine.execute_order(
        symbol="EURUSD",
        direction="BUY",
        volume=Decimal("1.0"),
        price=Decimal("1.10000"),
        sl=None,
        tp=None,
        symbol_spec=symbol_spec,
    )

    assert len(engine.positions) == 1
    pos = next(iter(engine.positions.values()))
    assert pos["volume"] == Decimal("1.0")
    assert pos["price"] == Decimal("1.10000")

    # Simulate price tick up to 1.10050 bid (profit of 50 pips / points * 100,000 = 500 USD)
    tick = {
        "time": "2026-06-17T10:00:01Z",
        "symbol": "EURUSD",
        "bid": 1.10050,
        "ask": 1.10065,
    }
    engine.process_tick(tick, symbol_spec)

    assert engine.balance == Decimal("10000.0")
    assert engine.equity == Decimal("10050.0")


def test_engine_stop_loss(symbol_spec: SymbolSpec) -> None:
    """Test engine SL/TP hit detection and closing positions."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))

    # Execute market BUY order with Stop Loss at 1.09900
    engine.execute_order(
        symbol="EURUSD",
        direction="BUY",
        volume=Decimal("1.0"),
        price=Decimal("1.10000"),
        sl=Decimal("1.09900"),
        tp=None,
        symbol_spec=symbol_spec,
    )

    # Tick price drops to 1.09850 (crosses SL)
    tick = {
        "time": "2026-06-17T10:00:01Z",
        "symbol": "EURUSD",
        "bid": 1.09850,
        "ask": 1.09865,
    }
    engine.process_tick(tick, symbol_spec)

    # Position should be closed at SL price 1.09900
    assert len(engine.positions) == 0
    assert len(engine.deals) == 2  # 1 open deal, 1 close deal
    assert engine.balance == Decimal("9900.0")  # -100 USD loss


def test_trader_order_send(symbol_spec: SymbolSpec) -> None:
    """Test SimTrader MT5-style order send requests."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Send Buy Market request
    req = {
        "action": SimTrader.TRADE_ACTION_DEAL,
        "symbol": "EURUSD",
        "type": 0,  # Buy
        "volume": 0.1,
        "price": 1.10000,
    }
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE
    assert "deal" in res

    # Confirm position open
    pos = trader.positions_get(symbol="EURUSD")
    assert pos is not None
    assert len(pos) == 1
    assert pos[0]["volume"] == Decimal("0.1")


def test_trader_order_send_margin_rejected(symbol_spec: SymbolSpec) -> None:
    """Test SimTrader margin calculation and rejection."""
    engine = EventDrivenExecutionEngine(
        initial_balance=Decimal("100.0")
    )  # very low balance
    trader = SimTrader(engine, {"EURUSD": symbol_spec})
    req = {
        "action": SimTrader.TRADE_ACTION_DEAL,
        "symbol": "EURUSD",
        "type": 0,
        "volume": 10.0,  # huge volume -> large margin requirement
        "price": 1.10000,
    }
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_NO_MONEY


def test_trader_order_send_invalid_volume(symbol_spec: SymbolSpec) -> None:
    """Test SimTrader invalid volume rejection."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Below min volume
    req = {
        "action": SimTrader.TRADE_ACTION_DEAL,
        "symbol": "EURUSD",
        "type": 0,
        "volume": 0.001,
        "price": 1.10000,
    }
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_VOLUME

    # Volume step mismatch
    req["volume"] = 0.105  # step is 0.01
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_VOLUME


def test_trader_order_send_invalid_symbol(symbol_spec: SymbolSpec) -> None:
    """Test SimTrader invalid symbol rejection."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})
    req = {
        "action": SimTrader.TRADE_ACTION_DEAL,
        "symbol": "UNKNOWN",
        "type": 0,
        "volume": 0.1,
        "price": 1.10000,
    }
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_REJECT


def test_trader_order_send_pending_actions(symbol_spec: SymbolSpec) -> None:
    """Test SimTrader pending actions (submit, modify, cancel)."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Submit PENDING BUY_LIMIT order
    req = {
        "action": SimTrader.TRADE_ACTION_PENDING,
        "symbol": "EURUSD",
        "type": 2,  # Buy Limit
        "volume": 0.1,
        "price": 1.09000,
        "sl": 1.08000,
        "tp": 1.11000,
    }
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE
    order_id = res["order"]
    assert trader.orders_total() == 1

    # Modify PENDING order
    req_mod = {
        "action": SimTrader.TRADE_ACTION_MODIFY,
        "symbol": "EURUSD",
        "order": order_id,
        "volume": 0.1,
        "price": 1.09100,
        "sl": 1.08100,
        "tp": 1.11100,
    }
    res_mod = trader.order_send(req_mod)
    assert res_mod["retcode"] == SimTrader.TRADE_RETCODE_DONE
    assert engine.orders[order_id]["price"] == Decimal("1.09100")

    # Remove/Cancel PENDING order
    req_rem = {
        "action": SimTrader.TRADE_ACTION_REMOVE,
        "symbol": "EURUSD",
        "order": order_id,
    }
    res_rem = trader.order_send(req_rem)
    assert res_rem["retcode"] == SimTrader.TRADE_RETCODE_DONE
    assert trader.orders_total() == 0


def test_trader_order_send_sltp_modify(symbol_spec: SymbolSpec) -> None:
    """Test SimTrader modifying position SL/TP."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Open a position first
    req = {
        "action": SimTrader.TRADE_ACTION_DEAL,
        "symbol": "EURUSD",
        "type": 0,
        "volume": 0.1,
        "price": 1.10000,
    }
    res = trader.order_send(req)
    res["deal"]

    positions = trader.positions_get(symbol="EURUSD")
    assert positions is not None
    assert len(positions) == 1
    pos_id = positions[0]["id"]

    # Modify SL/TP of this position
    req_sltp = {
        "action": SimTrader.TRADE_ACTION_SLTP,
        "symbol": "EURUSD",
        "position": pos_id,
        "volume": 0.1,
        "sl": 1.09500,
        "tp": 1.12000,
    }
    res_sltp = trader.order_send(req_sltp)
    assert res_sltp["retcode"] == SimTrader.TRADE_RETCODE_DONE
    assert engine.positions[pos_id]["sl"] == Decimal("1.09500")


def test_trader_position_and_order_queries(symbol_spec: SymbolSpec) -> None:
    """Test SimTrader queries, history, margins, and profit calculations."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Submit Buy Limit
    trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 2,
            "volume": 0.2,
            "price": 1.09000,
        }
    )

    orders = trader.orders_get()
    assert orders is not None
    assert len(orders) == 1
    assert trader.orders_total() == 1

    # Execute Market Buy
    trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
            "price": 1.10000,
        }
    )

    assert trader.positions_total() == 1

    # Check history queries
    assert len(trader.history_deals_get()) == 1
    assert len(trader.history_orders_get()) == 0  # no completed pending orders yet

    # Check account info
    info = trader.account_info()
    assert info["balance"] == 10000.0
    assert info["equity"] == 10000.0

    # Margin and profit calculators
    margin_calc = trader.order_calc_margin(0, "EURUSD", 0.5, 1.10000)
    assert margin_calc == 500.0

    profit_calc = trader.order_calc_profit(0, "EURUSD", 1.0, 1.10000, 1.10050)
    assert profit_calc == 50.0


def test_engine_hedging_mode(symbol_spec: SymbolSpec) -> None:
    """Test EventDrivenExecutionEngine hedging mode where every deal opens a separate position."""
    engine = EventDrivenExecutionEngine(
        initial_balance=Decimal("10000.0"), hedging=True
    )

    # Open Buy position 1
    engine.execute_order(
        "EURUSD", "BUY", Decimal("1.0"), Decimal("1.10000"), None, None, symbol_spec
    )
    assert len(engine.positions) == 1

    # Open Buy position 2 (under hedging, this opens a second position)
    engine.execute_order(
        "EURUSD", "BUY", Decimal("1.0"), Decimal("1.10050"), None, None, symbol_spec
    )
    assert len(engine.positions) == 2


def test_engine_stopout_liquidation(symbol_spec: SymbolSpec) -> None:
    """Test EventDrivenExecutionEngine stopout liquidation."""
    engine = EventDrivenExecutionEngine(
        initial_balance=Decimal("1000.0"),
        leverage=Decimal("100.0"),
        stopout_level_pct=Decimal("50.0"),
    )

    # Execute market BUY order (Margin = 1 lot * 100,000 / 100 = 1000 USD)
    engine.execute_order(
        "EURUSD", "BUY", Decimal("1.0"), Decimal("1.10000"), None, None, symbol_spec
    )

    # Simulate a price drop: equity falls below 500 USD (50% of margin)
    # Price drop of 60 pips: loss = 60 * 10 = 600 USD. Equity = 1000 - 600 = 400 USD
    tick = {
        "time": "2026-06-17T10:00:01Z",
        "symbol": "EURUSD",
        "bid": 1.09400,
        "ask": 1.09415,
    }
    engine.process_tick(tick, symbol_spec)

    # Stopout should liquidate the position
    assert len(engine.positions) == 0


def test_trader_pegged_orders(symbol_spec: SymbolSpec) -> None:
    """Test pegged order repricing on tick updates."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Submit a pegged order pegged to BID with offset +10 points (0.00010)
    req = {
        "action": SimTrader.TRADE_ACTION_PENDING,
        "symbol": "EURUSD",
        "type": 2,  # Buy Limit
        "volume": 0.1,
        "price": 1.09000,
        "pegged_ref": "BID",
        "pegged_offset_points": 10.0,
    }
    # First set a tick so last_tick is populated
    tick0 = {
        "time": "2026-06-17T10:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.09500,
        "ask": 1.09515,
    }
    engine.process_tick(tick0, symbol_spec)

    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE
    order_id = res["order"]

    # Current pegged price should be 1.09500 + 10 * 0.00001 = 1.09510
    assert engine.orders[order_id]["price"] == Decimal("1.09510")

    # Tick BID moves to 1.09600
    tick1 = {
        "time": "2026-06-17T10:00:01Z",
        "symbol": "EURUSD",
        "bid": 1.09600,
        "ask": 1.09615,
    }
    engine.process_tick(tick1, symbol_spec)

    # Pegged price should update to 1.09600 + 0.00010 = 1.09610
    assert engine.orders[order_id]["price"] == Decimal("1.09610")


def test_trader_trailing_stops(symbol_spec: SymbolSpec) -> None:
    """Test trailing stops adjusting Stop Loss on tick updates."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Open a BUY position with trailing stop of 20 points (0.00020)
    # SL is initially set to 1.09900
    req = {
        "action": SimTrader.TRADE_ACTION_DEAL,
        "symbol": "EURUSD",
        "type": 0,  # Buy
        "volume": 1.0,
        "price": 1.10000,
        "sl": 1.09900,
        "trailing_stop": 20.0,
    }
    # Seed a tick
    tick0 = {
        "time": "2026-06-17T10:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.10000,
        "ask": 1.10015,
    }
    engine.process_tick(tick0, symbol_spec)

    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE

    # Get the position ID from positions_get
    pos_list = trader.positions_get()
    assert pos_list is not None
    assert len(pos_list) == 1
    pos_id = pos_list[0]["id"]
    pos = engine.positions[pos_id]
    assert pos["sl"] == Decimal("1.09900")

    # Tick BID moves up to 1.10050. New SL should trail: 1.10050 - 20 points = 1.10030
    tick1 = {
        "time": "2026-06-17T10:00:01Z",
        "symbol": "EURUSD",
        "bid": 1.10050,
        "ask": 1.10065,
    }
    engine.process_tick(tick1, symbol_spec)
    assert pos["sl"] == Decimal("1.10030")

    # Tick BID moves down to 1.10020. SL should NOT move down (remain 1.10030)
    tick2 = {
        "time": "2026-06-17T10:00:02Z",
        "symbol": "EURUSD",
        "bid": 1.10020,
        "ask": 1.10035,
    }
    engine.process_tick(tick2, symbol_spec)
    assert pos["sl"] == Decimal("1.10030")


def test_trader_stop_limit_orders(symbol_spec: SymbolSpec) -> None:
    """Test stop-limit order execution behavior."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Submit a BUY_STOP_LIMIT pending order: stop price = 1.10050, limit price = 1.10020
    req = {
        "action": SimTrader.TRADE_ACTION_PENDING,
        "symbol": "EURUSD",
        "type": 6,  # Buy Stop Limit
        "volume": 0.5,
        "price": 1.10050,
        "stop_limit_price": 1.10020,
    }
    # Seed a tick
    tick0 = {
        "time": "2026-06-17T10:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.10000,
        "ask": 1.10015,
    }
    engine.process_tick(tick0, symbol_spec)

    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE
    order_id = res["order"]
    assert engine.orders[order_id]["type"] == "BUY_STOP_LIMIT"

    # Price ask rises to 1.10060 (touches stop price of 1.10050)
    # Order should convert to BUY_LIMIT at limit price 1.10020
    tick1 = {
        "time": "2026-06-17T10:00:01Z",
        "symbol": "EURUSD",
        "bid": 1.10045,
        "ask": 1.10060,
    }
    engine.process_tick(tick1, symbol_spec)

    assert order_id in engine.orders
    assert engine.orders[order_id]["type"] == "BUY_LIMIT"
    assert engine.orders[order_id]["price"] == Decimal("1.10020")

    # Price ask drops to 1.10015 (touches limit price of 1.10020) -> should trigger fill
    tick2 = {
        "time": "2026-06-17T10:00:02Z",
        "symbol": "EURUSD",
        "bid": 1.10000,
        "ask": 1.10015,
    }
    engine.process_tick(tick2, symbol_spec)

    assert order_id not in engine.orders
    assert len(engine.positions) == 1


def test_trader_stops_level_validation(symbol_spec: SymbolSpec) -> None:
    """Test stops level validation rules."""
    # Set stops level to 10 points (0.00010) in symbol_spec
    symbol_spec.stops_level = Decimal("10.0")

    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Seed tick: ask=1.10015, bid=1.10000
    tick = {
        "time": "2026-06-17T10:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.10000,
        "ask": 1.10015,
    }
    engine.process_tick(tick, symbol_spec)

    # 1. Market BUY order with SL too close (e.g. SL = 1.10010, distance is 5 points < 10 points)
    req = {
        "action": SimTrader.TRADE_ACTION_DEAL,
        "symbol": "EURUSD",
        "type": 0,
        "volume": 0.1,
        "price": 1.10015,
        "sl": 1.10010,
    }
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 2. Market BUY order with TP too close (e.g. TP = 1.10020, distance is 5 points < 10 points)
    req = {
        "action": SimTrader.TRADE_ACTION_DEAL,
        "symbol": "EURUSD",
        "type": 0,
        "volume": 0.1,
        "price": 1.10015,
        "tp": 1.10020,
    }
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 3. Pending BUY_LIMIT too close to market price (e.g. limit price = 1.10012, distance is 3 points < 10 points)
    req = {
        "action": SimTrader.TRADE_ACTION_PENDING,
        "symbol": "EURUSD",
        "type": 2,
        "volume": 0.1,
        "price": 1.10012,
    }
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS


def test_trader_freeze_level_validation(symbol_spec: SymbolSpec) -> None:
    """Test freeze level validation rules."""
    # Set freeze level to 5 points (0.00005)
    symbol_spec.freeze_level = Decimal("5.0")

    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Seed tick: ask=1.10015, bid=1.10000
    tick = {
        "time": "2026-06-17T10:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.10000,
        "ask": 1.10015,
    }
    engine.process_tick(tick, symbol_spec)

    # Submit a BUY_LIMIT order far from market price (price = 1.09000)
    req = {
        "action": SimTrader.TRADE_ACTION_PENDING,
        "symbol": "EURUSD",
        "type": 2,
        "volume": 0.1,
        "price": 1.09000,
    }
    res = trader.order_send(req)
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE
    order_id = res["order"]

    # Move price ask extremely close to the pending order price (e.g. ask = 1.09003, distance is 3 points < 5 points)
    tick_frozen = {
        "time": "2026-06-17T10:00:01Z",
        "symbol": "EURUSD",
        "bid": 1.08988,
        "ask": 1.09003,
    }
    engine.process_tick(tick_frozen, symbol_spec)

    # Attempting to modify the pending order should fail due to freeze level
    req_mod = {
        "action": SimTrader.TRADE_ACTION_MODIFY,
        "symbol": "EURUSD",
        "order": order_id,
        "price": 1.08500,
    }
    res_mod = trader.order_send(req_mod)
    assert res_mod["retcode"] == SimTrader.TRADE_RETCODE_FREEZE

    # Attempting to cancel/remove the pending order should also fail due to freeze level
    req_rem = {
        "action": SimTrader.TRADE_ACTION_REMOVE,
        "symbol": "EURUSD",
        "order": order_id,
    }
    res_rem = trader.order_send(req_rem)
    assert res_rem["retcode"] == SimTrader.TRADE_RETCODE_FREEZE


def test_trader_netting_reconciliation(symbol_spec: SymbolSpec) -> None:
    """Test netting account mode position reconciliation and reversing."""
    # Hedging is False by default
    engine = EventDrivenExecutionEngine(
        initial_balance=Decimal("10000.0"), hedging=False
    )
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # 1. Open BUY position of 0.2 lots at 1.10000
    trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.2,
            "price": 1.10000,
        }
    )
    pos_list = trader.positions_get()
    assert pos_list is not None
    assert len(pos_list) == 1
    assert pos_list[0]["volume"] == Decimal("0.2")
    assert pos_list[0]["type"] == "BUY"

    # 2. Add to BUY position: 0.1 lots at 1.10030
    trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
            "price": 1.10030,
        }
    )
    pos_list = trader.positions_get()
    assert pos_list is not None
    assert len(pos_list) == 1
    # Total volume: 0.3, average price: (0.2 * 1.10000 + 0.1 * 1.10030) / 0.3 = 1.10010
    assert pos_list[0]["volume"] == Decimal("0.3")
    assert pos_list[0]["price"] == Decimal("1.10010")

    # 3. Sell 0.1 lots (partial close of the buy position) at 1.10050
    trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,  # Sell
            "volume": 0.1,
            "price": 1.10050,
        }
    )
    pos_list = trader.positions_get()
    assert pos_list is not None
    assert len(pos_list) == 1
    assert pos_list[0]["volume"] == Decimal("0.2")

    # 4. Sell 0.4 lots (reversing position: closes 0.2 lots of BUY and opens 0.2 lots of SELL) at 1.10000
    trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,  # Sell
            "volume": 0.4,
            "price": 1.10000,
        }
    )
    pos_list = trader.positions_get()
    assert pos_list is not None
    assert len(pos_list) == 1
    assert pos_list[0]["volume"] == Decimal("0.2")
    assert pos_list[0]["type"] == "SELL"
    assert pos_list[0]["price"] == Decimal("1.10000")


def test_trader_stops_and_freeze_comprehensive(symbol_spec: SymbolSpec) -> None:
    """Comprehensive test covering all branches of stops and freeze validations."""
    symbol_spec.stops_level = Decimal("10.0")
    symbol_spec.freeze_level = Decimal("5.0")

    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Seed tick: ask=1.10015, bid=1.10000
    tick = {
        "time": "2026-06-17T10:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.10000,
        "ask": 1.10015,
    }
    engine.process_tick(tick, symbol_spec)

    # 1. Market SELL order with SL too close (bid=1.10000, sl=1.10005, distance = 5 points < 10 points)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,  # Sell
            "volume": 0.1,
            "price": 1.10000,
            "sl": 1.10005,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # Market SELL order with TP too close (bid=1.10000, tp=1.09995, distance = 5 points < 10 points)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,
            "volume": 0.1,
            "price": 1.10000,
            "tp": 1.09995,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 2. Pending SELL_LIMIT too close (bid=1.10000, price=1.10005, distance = 5 points < 10 points)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 3,  # Sell Limit
            "volume": 0.1,
            "price": 1.10005,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # Pending BUY_STOP too close (ask=1.10015, price=1.10020, distance = 5 points < 10 points)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 4,  # Buy Stop
            "volume": 0.1,
            "price": 1.10020,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # Pending SELL_STOP too close (bid=1.10000, price=1.09995, distance = 5 points < 10 points)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 5,  # Sell Stop
            "volume": 0.1,
            "price": 1.09995,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 3. Pending BUY_STOP_LIMIT checks
    # price too close (ask=1.10015, price=1.10020, stops=10 points)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 6,
            "volume": 0.1,
            "price": 1.10020,
            "stop_limit_price": 1.10020,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # price ok (1.10030), stop_limit_price too close (1.10025, distance = 5 points < 10 points)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 6,
            "volume": 0.1,
            "price": 1.10030,
            "stop_limit_price": 1.10025,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # sl too close (limit=1.10030, sl=1.10025)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 6,
            "volume": 0.1,
            "price": 1.10050,
            "stop_limit_price": 1.10030,
            "sl": 1.10025,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # tp too close (limit=1.10030, tp=1.10035)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 6,
            "volume": 0.1,
            "price": 1.10050,
            "stop_limit_price": 1.10030,
            "tp": 1.10035,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 4. Pending SELL_STOP_LIMIT checks
    # price too close (bid=1.10000, price=1.09995, stops=10 points)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 7,
            "volume": 0.1,
            "price": 1.09995,
            "stop_limit_price": 1.09995,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # price ok (1.09980), stop_limit_price too close (1.09985, distance = 5 points < 10 points)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 7,
            "volume": 0.1,
            "price": 1.09980,
            "stop_limit_price": 1.09985,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # sl too close (limit=1.09980, sl=1.09985)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 7,
            "volume": 0.1,
            "price": 1.09960,
            "stop_limit_price": 1.09980,
            "sl": 1.09985,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # tp too close (limit=1.09980, tp=1.09975)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 7,
            "volume": 0.1,
            "price": 1.09960,
            "stop_limit_price": 1.09980,
            "tp": 1.09975,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 5. Position SLTP stops level checks
    # Open BUY position first
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
            "price": 1.10015,
        }
    )
    pos_list = trader.positions_get()
    assert pos_list is not None
    pos_id = pos_list[0]["id"]

    # Modify SL too close (bid=1.10000, sl=1.09995)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_SLTP,
            "symbol": "EURUSD",
            "position": pos_id,
            "sl": 1.09995,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # Modify TP too close (bid=1.10000, tp=1.10005)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_SLTP,
            "symbol": "EURUSD",
            "position": pos_id,
            "tp": 1.10005,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # Clear positions to open a SELL position in netting mode without netting out
    engine.positions.clear()

    # Open SELL position
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,
            "volume": 0.1,
            "price": 1.10000,
        }
    )
    pos_list = trader.positions_get()
    assert pos_list is not None
    pos_id_sell = next(p["id"] for p in pos_list if p["type"] == "SELL")

    # Modify SL too close (ask=1.10015, sl=1.10020)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_SLTP,
            "symbol": "EURUSD",
            "position": pos_id_sell,
            "sl": 1.10020,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # Modify TP too close (ask=1.10015, tp=1.10010)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_SLTP,
            "symbol": "EURUSD",
            "position": pos_id_sell,
            "tp": 1.10010,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 6. Freeze level validation for position SLTP and pending modify/remove
    symbol_spec.stops_level = Decimal("0.0")
    # Position freeze checks (close=bid=1.10000. Set SL=1.09998, tp=1.10002)
    # Recreate BUY position with SL/TP close to freeze limit
    engine.positions.clear()
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
            "price": 1.10015,
            "sl": 1.09998,
        }
    )
    pos_list = trader.positions_get()
    assert pos_list is not None
    pos_id = pos_list[0]["id"]
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_SLTP,
            "symbol": "EURUSD",
            "position": pos_id,
            "sl": 1.09990,  # try to modify SL which is 1.09998 (distance 2 points < 5 points)
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_FREEZE

    # Netting opposite deal close freeze check
    # Try to close BUY position by selling 0.1 lots
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,
            "volume": 0.1,
            "price": 1.10000,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_FREEZE

    # Netting opposite deal close freeze check for TP
    engine.positions.clear()
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
            "price": 1.09990,
            "tp": 1.10002,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE
    pos_list = trader.positions_get()
    assert pos_list is not None
    pos_id = pos_list[0]["id"]
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,
            "volume": 0.1,
            "price": 1.10000,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_FREEZE

    # 7. Hedging close position freeze check
    engine_hedge = EventDrivenExecutionEngine(
        initial_balance=Decimal("10000.0"), hedging=True
    )
    trader_hedge = SimTrader(engine_hedge, {"EURUSD": symbol_spec})
    engine_hedge.process_tick(
        {
            "time": "2026-06-17T10:00:00Z",
            "symbol": "EURUSD",
            "bid": 1.10000,
            "ask": 1.10015,
        },
        symbol_spec,
    )  # ask=1.10015, bid=1.10000

    # Open Buy position under Hedging
    res = trader_hedge.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
            "price": 1.10015,
            "sl": 1.09998,
        }
    )
    pos_list_hedge = trader_hedge.positions_get()
    assert pos_list_hedge is not None
    pos_id_hedge = pos_list_hedge[0]["id"]

    # Close it with position parameter specified (SL is close)
    res = trader_hedge.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,
            "volume": 0.1,
            "price": 1.10000,
            "position": pos_id_hedge,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_FREEZE

    # Close it with position parameter specified (TP is close)
    engine_hedge.positions.clear()
    res = trader_hedge.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
            "price": 1.10015,
            "tp": 1.10002,
        }
    )
    pos_list_hedge = trader_hedge.positions_get()
    assert pos_list_hedge is not None
    pos_id_hedge = pos_list_hedge[0]["id"]
    res = trader_hedge.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,
            "volume": 0.1,
            "price": 1.10000,
            "position": pos_id_hedge,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_FREEZE

    # 8. Modifying non-existent position SLTP
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_SLTP,
            "symbol": "EURUSD",
            "position": "non_existent_position_id",
            "sl": 1.09900,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_POSITION_NOT_FOUND

    # 9. Pending order missing stop_limit_price checks
    symbol_spec.stops_level = Decimal("10.0")
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 6,  # Buy Stop Limit
            "volume": 0.1,
            "price": 1.10040,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_REJECT

    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 7,  # Sell Stop Limit
            "volume": 0.1,
            "price": 1.09960,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_REJECT

    # 10. Unsupported pending order type check
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 99,  # Invalid type
            "volume": 0.1,
            "price": 1.10000,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_REJECT


def test_trader_modify_pending_and_cancel_stops_and_freeze(
    symbol_spec: SymbolSpec,
) -> None:
    """Test modifying and removing pending orders under stops level and freeze level conditions."""
    symbol_spec.stops_level = Decimal("10.0")
    symbol_spec.freeze_level = Decimal("5.0")

    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Seed tick: ask=1.10015, bid=1.10000
    tick = {
        "time": "2026-06-17T10:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.10000,
        "ask": 1.10015,
    }
    engine.process_tick(tick, symbol_spec)

    # 1. Modify BUY_LIMIT checks
    # Submit a valid BUY_LIMIT order first
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 2,  # Buy Limit
            "volume": 0.1,
            "price": 1.10000,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE
    order_id = next(iter(engine.orders.keys()))

    # Modify BUY_LIMIT stops level violations
    # Price too close to ask (ask=1.10015, price=1.10010, stops=10 points -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10010,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # SL too close to price (price=1.10000, sl=1.09995 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10000,
            "sl": 1.09995,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # TP too close to price (price=1.10000, tp=1.10005 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10000,
            "tp": 1.10005,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 2. Modify SELL_LIMIT checks
    engine.orders.clear()
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 3,  # Sell Limit
            "volume": 0.1,
            "price": 1.10020,
        }
    )
    order_id = next(iter(engine.orders.keys()))

    # Price too close to bid (bid=1.10000, price=1.10005 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10005,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # SL too close to price (price=1.10020, sl=1.10025 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10020,
            "sl": 1.10025,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # TP too close to price (price=1.10020, tp=1.10015 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10020,
            "tp": 1.10015,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 3. Modify BUY_STOP checks
    engine.orders.clear()
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 4,  # Buy Stop
            "volume": 0.1,
            "price": 1.10030,
        }
    )
    order_id = next(iter(engine.orders.keys()))

    # Price too close to ask (ask=1.10015, price=1.10020 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10020,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # SL too close to price (price=1.10030, sl=1.10025 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10030,
            "sl": 1.10025,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # TP too close to price (price=1.10030, tp=1.10035 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10030,
            "tp": 1.10035,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 4. Modify SELL_STOP checks
    engine.orders.clear()
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 5,  # Sell Stop
            "volume": 0.1,
            "price": 1.09980,
        }
    )
    order_id = next(iter(engine.orders.keys()))

    # Price too close to bid (bid=1.10000, price=1.09995 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.09995,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # SL too close to price (price=1.09980, sl=1.09985 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.09980,
            "sl": 1.09985,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # TP too close to price (price=1.09980, tp=1.09975 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.09980,
            "tp": 1.09975,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 5. Modify BUY_STOP_LIMIT checks
    engine.orders.clear()
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 6,  # Buy Stop Limit
            "volume": 0.1,
            "price": 1.10040,
            "stop_limit_price": 1.10030,
        }
    )
    order_id = next(iter(engine.orders.keys()))

    # Stop price too close to ask (ask=1.10015, price=1.10020 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10020,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # Limit price too close to stop price (price=1.10040, stop_limit_price=1.10035 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10040,
            "stop_limit_price": 1.10035,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # SL too close to limit price (limit=1.10030, sl=1.10025 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10040,
            "stop_limit_price": 1.10030,
            "sl": 1.10025,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # TP too close to limit price (limit=1.10030, tp=1.10035 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.10040,
            "stop_limit_price": 1.10030,
            "tp": 1.10035,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 6. Modify SELL_STOP_LIMIT checks
    engine.orders.clear()
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 7,  # Sell Stop Limit
            "volume": 0.1,
            "price": 1.09960,
            "stop_limit_price": 1.09980,
        }
    )
    order_id = next(iter(engine.orders.keys()))

    # Stop price too close to bid (bid=1.10000, price=1.09995 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.09995,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # Limit price too close to stop price (price=1.09960, stop_limit_price=1.09965 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.09960,
            "stop_limit_price": 1.09965,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # SL too close to limit price (limit=1.09980, sl=1.09985 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.09960,
            "stop_limit_price": 1.09980,
            "sl": 1.09985,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # TP too close to limit price (limit=1.09980, tp=1.09975 -> distance 5 < 10)
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.09960,
            "stop_limit_price": 1.09980,
            "tp": 1.09975,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_INVALID_STOPS

    # 7. Modify and Cancel Freeze level checks
    # Create order at price 1.10000, which is far from ask=1.10015 (distance 15 points >= 10 stops level)
    engine.orders.clear()
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 2,  # Buy Limit
            "volume": 0.1,
            "price": 1.10000,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE
    order_id = next(iter(engine.orders.keys()))

    # Move market price close to order price: ask=1.10003, bid=1.09995
    # Old order price 1.10000 is now within 3 points of ask (3 < 5 freeze level)
    tick_close = {
        "time": "2026-06-17T10:00:30Z",
        "symbol": "EURUSD",
        "bid": 1.09995,
        "ask": 1.10003,
    }
    engine.process_tick(tick_close, symbol_spec)

    # Try modifying this order -> should violate freeze level
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": order_id,
            "price": 1.09990,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_FREEZE

    # Try removing this order -> should violate freeze level
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_REMOVE,
            "symbol": "EURUSD",
            "order": order_id,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_FREEZE

    # Try modify non-existent order
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_MODIFY,
            "symbol": "EURUSD",
            "order": "non_existent_id",
            "price": 1.10000,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_ORDER_NOT_FOUND

    # Try remove non-existent order
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_REMOVE,
            "symbol": "EURUSD",
            "order": "non_existent_id",
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_ORDER_NOT_FOUND


def test_engine_pegged_and_trailing_stops_extra_cases(symbol_spec: SymbolSpec) -> None:
    """Test pegged orders and trailing stops additional execution branches in engine."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    # Seed tick: ask=1.10015, bid=1.10000
    tick1 = {
        "time": "2026-06-17T10:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.10000,
        "ask": 1.10015,
    }
    engine.process_tick(tick1, symbol_spec)

    # 1. Pegged orders with ASK and MID references
    trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 2,  # Buy Limit
            "volume": 0.1,
            "pegged_ref": "ASK",
            "pegged_offset_points": -20,  # 20 points below ask
        }
    )
    trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 2,
            "volume": 0.1,
            "pegged_ref": "MID",
            "pegged_offset_points": -10,
        }
    )
    trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_PENDING,
            "symbol": "EURUSD",
            "type": 2,
            "volume": 0.1,
            "pegged_ref": "INVALID_REF",  # should be skipped
            "pegged_offset_points": 0,
        }
    )

    # Update tick with new prices: bid=1.10050, ask=1.10065
    tick2 = {
        "time": "2026-06-17T10:01:00Z",
        "symbol": "EURUSD",
        "bid": 1.10050,
        "ask": 1.10065,
    }
    engine.process_tick(tick2, symbol_spec)

    pegged_ask_order = next(
        o for o in engine.orders.values() if o.get("pegged_ref") == "ASK"
    )
    assert pegged_ask_order["price"] == Decimal("1.10045")

    # 2. Trailing stop in SELL position and trailing stop with initial SL=None
    # Let's open a SELL position with trailing stop (20 points) and NO initial SL
    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 1,  # Sell
            "volume": 0.1,
            "price": 1.10050,
            "trailing_stop": 20,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE
    pos_list = trader.positions_get()
    assert pos_list is not None
    pos_id = pos_list[0]["id"]

    # Trailing stop distance = 20 points = 0.00020
    tick3 = {
        "time": "2026-06-17T10:02:00Z",
        "symbol": "EURUSD",
        "bid": 1.10015,
        "ask": 1.10030,
    }
    engine.process_tick(tick3, symbol_spec)
    pos = engine.positions[pos_id]
    assert pos["sl"] == Decimal("1.10050")

    # Check trailing stop symbol mismatch
    tick_mismatch = {
        "time": "2026-06-17T10:02:30Z",
        "symbol": "GBPUSD",
        "bid": 1.20000,
        "ask": 1.20010,
    }
    engine.process_tick(tick_mismatch, symbol_spec)


def test_engine_stopout_liquidation_extra(symbol_spec: SymbolSpec) -> None:
    """Test that stopout levels trigger liquidation of positions."""
    engine = EventDrivenExecutionEngine(
        initial_balance=Decimal("120.0"),
        leverage=Decimal("100.0"),
        stopout_level_pct=Decimal("50.0"),
    )
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    tick1 = {
        "time": "2026-06-17T10:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.09990,
        "ask": 1.10000,
    }
    engine.process_tick(tick1, symbol_spec)

    res = trader.order_send(
        {
            "action": SimTrader.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "type": 0,  # Buy
            "volume": 0.1,
            "price": 1.10000,
        }
    )
    assert res["retcode"] == SimTrader.TRADE_RETCODE_DONE

    tick2 = {
        "time": "2026-06-17T10:01:00Z",
        "symbol": "EURUSD",
        "bid": 1.09000,
        "ask": 1.09010,
    }
    engine.process_tick(tick2, symbol_spec)

    pos_list = trader.positions_get()
    assert pos_list is not None
    assert len(pos_list) == 0
    assert len(engine.deals) > 1
    liquidation_deal = engine.deals[-1]
    assert liquidation_deal["comment"] == "Stopout liquidation"


def test_engine_sharpe_ratio_multi_day(symbol_spec: SymbolSpec) -> None:
    """Test metrics Sharpe Ratio calculation with multi-day equity curve snapshots."""
    from app.services.simulation.report import calculate_metrics

    equity_curve = [
        ("2026-06-15T10:00:00Z", Decimal("10000.0")),
        ("2026-06-16T10:00:00Z", Decimal("10100.0")),
        ("2026-06-17T10:00:00Z", Decimal("10050.0")),
    ]
    deals = [
        {"profit": 100.0, "entry": "out", "commission": 2.0, "swap": 0.0},
        {"profit": -50.0, "entry": "out", "commission": 1.0, "swap": 0.0},
    ]

    metrics = calculate_metrics(deals, equity_curve, Decimal("10000.0"))
    assert metrics["sharpe_ratio"] != 0.0
    assert metrics["winning_trades"] == 1
    assert metrics["losing_trades"] == 1


def test_trader_calc_margin_and_profit_exceptions(symbol_spec: SymbolSpec) -> None:
    """Test order_calc_margin and order_calc_profit error paths."""
    engine = EventDrivenExecutionEngine(initial_balance=Decimal("10000.0"))
    trader = SimTrader(engine, {"EURUSD": symbol_spec})

    with pytest.raises(SimulationError, match="not found"):
        trader.order_calc_margin(0, "INVALID_SYMBOL", 0.1, 1.10)

    with pytest.raises(SimulationError, match="not found"):
        trader.order_calc_profit(0, "INVALID_SYMBOL", 0.1, 1.10, 1.11)
