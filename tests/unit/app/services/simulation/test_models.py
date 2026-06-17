# ruff: noqa: E501
"""Unit tests for simulator model components (spread, slippage, liquidity, fee, swap, margin, tick)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.simulation.models import (
    FeeModel,
    LiquidityModel,
    MarginModel,
    SlippageModel,
    SpreadModel,
    SwapModel,
    TickGenerator,
)
from app.services.simulation.validation.schema import SymbolSpec
from app.utils.errors import SimulationError


def test_spread_model() -> None:
    """Test spread model BID/ASK pricing calculations."""
    model = SpreadModel(model_type="FIXED_SPREAD", fixed_points=20)
    ask = model.calculate_ask(Decimal("1.10000"), Decimal("0.00001"))
    assert ask == Decimal("1.10020")

    model_var = SpreadModel(model_type="VARIABLE_SPREAD", min_points=10, max_points=30)
    ask_var = model_var.calculate_ask(
        Decimal("1.10000"), Decimal("0.00001"), bar_time="2026-06-17T10:00:00Z"
    )
    assert ask_var >= Decimal("1.10010")
    assert ask_var <= Decimal("1.10030")

    # Test negative bid rejection
    with pytest.raises(SimulationError, match="Bid price cannot be negative"):
        model.calculate_ask(Decimal("-1.0"), Decimal("0.00001"))


def test_slippage_model() -> None:
    """Test slippage price deterioration calculations."""
    model = SlippageModel(model_type="FIXED_SLIPPAGE", fixed_points=5)
    # Buy slippage increases price
    buy_price = model.calculate_price(Decimal("1.10000"), "BUY", Decimal("0.00001"))
    assert buy_price == Decimal("1.10005")

    # Sell slippage decreases price
    sell_price = model.calculate_price(Decimal("1.10000"), "SELL", Decimal("0.00001"))
    assert sell_price == Decimal("1.09995")


def test_liquidity_model() -> None:
    """Test liquidity filling logic."""
    model = LiquidityModel(
        model_type="VOLUME_LIMIT_LIQUIDITY", max_volume_pct=Decimal("0.5")
    )
    res = model.evaluate_fill(
        requested_volume=Decimal("1.0"),
        direction="BUY",
        available_market_volume=Decimal("1.0"),
    )
    assert res["filled_volume"] == Decimal("0.5")
    assert res["unfilled_volume"] == Decimal("0.5")
    assert res["status"] == "partial"


def test_fee_model() -> None:
    """Test broker transaction commission fee calculations."""
    model = FeeModel(
        model_type="PERCENT_NOTIONAL_COMMISSION", pct_notional=Decimal("0.0005")
    )
    comm = model.calculate_commission(
        filled_volume=Decimal("1.0"),
        fill_price=Decimal("1.10000"),
        contract_size=Decimal("100000.0"),
    )
    # 1.0 lot * 100,000 size * 1.10000 price * 0.0005 fee pct = 55.0 USD
    assert comm == Decimal("55.00")


def test_swap_model() -> None:
    """Test overnight rollover swap interest calculations."""
    model = SwapModel(model_type="NATIVE_SWAP")
    swap = model.calculate_swap(
        volume=Decimal("1.0"),
        direction="BUY",
        swap_long=Decimal("-1.5"),
        swap_short=Decimal("0.5"),
        swap_mode="points",
        point=Decimal("0.00001"),
        contract_size=Decimal("100000.0"),
        open_price=Decimal("1.10000"),
        is_triple_day=False,
    )
    # 1.0 lot * 100,000 size * -1.5 points * 0.00001 point = -1.5 USD
    assert swap == Decimal("-1.50")


def test_margin_model() -> None:
    """Test leverage-based margin requirement calculations."""
    model = MarginModel(leverage=Decimal("100.0"))
    margin = model.calculate_position_margin(
        volume=Decimal("1.0"),
        entry_price=Decimal("1.10000"),
        contract_size=Decimal("100000.0"),
        asset_class="FX",
    )
    # For FX: (1.0 * 100,000) / 100 = 1,000.0 USD
    assert margin == Decimal("1000.00")


def test_tick_generator() -> None:
    """Test synthetic tick path generation."""
    spec = SymbolSpec(symbol="EURUSD")
    spread_model = SpreadModel(model_type="FIXED_SPREAD", fixed_points=15)
    generator = TickGenerator(spec, spread_model, tick_model="M1_TICKS")

    bar = {
        "timestamp": "2026-06-17T10:00:00Z",
        "open": 1.10000,
        "high": 1.10050,
        "low": 1.09950,
        "close": 1.10020,
        "volume": 4,
    }
    ticks = generator.generate_ticks_for_bar(bar)
    assert len(ticks) == 4
    assert ticks[0]["bid"] == Decimal("1.10000")  # Open
    assert ticks[3]["bid"] == Decimal("1.10020")  # Close

    # Test volumes <= 1, 2, 3
    bar["volume"] = 1
    ticks = generator.generate_ticks_for_bar(bar)
    assert len(ticks) == 1

    bar["volume"] = 2
    ticks = generator.generate_ticks_for_bar(bar)
    assert len(ticks) == 2

    bar["volume"] = 3
    ticks = generator.generate_ticks_for_bar(bar)
    assert len(ticks) == 3

    # Test bearish bar four price path
    bar_bear = {
        "timestamp": "2026-06-17T10:00:00Z",
        "open": 1.10020,
        "high": 1.10050,
        "low": 1.09950,
        "close": 1.10000,
        "volume": 4,
    }
    ticks = generator.generate_ticks_for_bar(bar_bear)
    assert len(ticks) == 4

    # Test invalid OHLC (negative price)
    bar_bad = dict(bar)
    bar_bad["open"] = -1.10
    with pytest.raises(SimulationError, match="OHLC price values must be positive"):
        generator.generate_ticks_for_bar(bar_bad)

    # Test invalid OHLC (high < low)
    bar_bad2 = dict(bar)
    bar_bad2["high"] = 1.09
    bar_bad2["low"] = 1.10
    with pytest.raises(SimulationError, match="Invalid OHLC bounds"):
        generator.generate_ticks_for_bar(bar_bad2)


def test_tick_generator_unsupported_model() -> None:
    """Test TickGenerator validation for unsupported model type."""
    spec = SymbolSpec(symbol="EURUSD")
    spread_model = SpreadModel(model_type="FIXED_SPREAD", fixed_points=15)
    with pytest.raises(SimulationError, match="Unsupported tick model"):
        TickGenerator(spec, spread_model, tick_model="UNSUPPORTED")


def test_tick_generator_synthetic_and_real() -> None:
    """Test TickGenerator synthetic and real tick models."""
    spec = SymbolSpec(symbol="EURUSD")
    spread_model = SpreadModel(model_type="FIXED_SPREAD", fixed_points=15)

    # Test SYNTHETIC_TICKS
    generator = TickGenerator(spec, spread_model, tick_model="SYNTHETIC_TICKS")
    bar = {
        "timestamp": "2026-06-17T10:00:00Z",
        "open": 1.10000,
        "high": 1.10050,
        "low": 1.09950,
        "close": 1.10020,
        "volume": 10,
    }
    ticks = generator.generate_ticks_for_bar(bar)
    assert len(ticks) > 0

    # Test REAL_TICKS fallback
    generator_real = TickGenerator(spec, spread_model, tick_model="REAL_TICKS")
    ticks_real = generator_real.generate_ticks_for_bar(bar)
    assert len(ticks_real) == 4


def test_swap_model_extra_modes() -> None:
    """Test SwapModel variations: NO_SWAP, side logic, other swap modes, and exceptions."""
    # Test invalid model type exception
    with pytest.raises(SimulationError, match="Unsupported swap model"):
        SwapModel(model_type="INVALID_MODEL")

    # Test NO_SWAP
    no_swap_model = SwapModel(model_type="NO_SWAP")
    assert no_swap_model.calculate_swap(
        volume=Decimal("1.0"),
        direction="BUY",
        swap_long=Decimal("-1.5"),
        swap_short=Decimal("0.5"),
        swap_mode="points",
        point=Decimal("0.00001"),
        contract_size=Decimal("100000.0"),
        open_price=Decimal("1.10000"),
    ) == Decimal("0.0")

    # Test Native Swap - Sell direction
    model = SwapModel(model_type="NATIVE_SWAP")
    swap_sell = model.calculate_swap(
        volume=Decimal("1.0"),
        direction="SELL",
        swap_long=Decimal("-1.5"),
        swap_short=Decimal("0.5"),
        swap_mode="points",
        point=Decimal("0.00001"),
        contract_size=Decimal("100000.0"),
        open_price=Decimal("1.10000"),
        is_triple_day=False,
    )
    # 1.0 lot * 100,000 size * 0.5 points * 0.00001 point = 0.5 USD
    assert swap_sell == Decimal("0.50")

    # Test triple swap day multiplier
    swap_triple = model.calculate_swap(
        volume=Decimal("1.0"),
        direction="BUY",
        swap_long=Decimal("-1.5"),
        swap_short=Decimal("0.5"),
        swap_mode="points",
        point=Decimal("0.00001"),
        contract_size=Decimal("100000.0"),
        open_price=Decimal("1.10000"),
        is_triple_day=True,
    )
    # 1.0 lot * 100,000 size * -1.5 points * 0.00001 point * 3 = -4.5 USD
    assert swap_triple == Decimal("-4.50")

    # Test other modes: money, percent, interest
    swap_money = model.calculate_swap(
        volume=Decimal("2.0"),
        direction="BUY",
        swap_long=Decimal("-5.00"),
        swap_short=Decimal("2.00"),
        swap_mode="money",
        point=Decimal("0.00001"),
        contract_size=Decimal("100000.0"),
        open_price=Decimal("1.10000"),
    )
    # 2.0 lots * -5.00 rate = -10.00 USD
    assert swap_money == Decimal("-10.00")

    swap_percent = model.calculate_swap(
        volume=Decimal("1.0"),
        direction="BUY",
        swap_long=Decimal("1.80"),  # 1.8% annual
        swap_short=Decimal("0.50"),
        swap_mode="percent",
        point=Decimal("0.00001"),
        contract_size=Decimal("100000.0"),
        open_price=Decimal("1.10000"),
    )
    # 1.0 * 100,000 * 1.10000 * (1.80 / 100) / 360 = 5.50 USD
    assert swap_percent == Decimal("5.50")

    swap_interest = model.calculate_swap(
        volume=Decimal("1.0"),
        direction="BUY",
        swap_long=Decimal("1.80"),
        swap_short=Decimal("0.50"),
        swap_mode="interest",
        point=Decimal("0.00001"),
        contract_size=Decimal("100000.0"),
        open_price=Decimal("1.10000"),
    )
    assert swap_interest == Decimal("5.50")

    # Test exceptions
    with pytest.raises(SimulationError, match="Invalid position direction"):
        model.calculate_swap(
            volume=Decimal("1.0"),
            direction="INVALID",
            swap_long=Decimal("1.0"),
            swap_short=Decimal("1.0"),
            swap_mode="points",
            point=Decimal("0.01"),
            contract_size=Decimal(100),
            open_price=Decimal(100),
        )

    with pytest.raises(SimulationError, match="Unsupported swap mode"):
        model.calculate_swap(
            volume=Decimal("1.0"),
            direction="BUY",
            swap_long=Decimal("1.0"),
            swap_short=Decimal("1.0"),
            swap_mode="unsupported_mode",
            point=Decimal("0.01"),
            contract_size=Decimal(100),
            open_price=Decimal(100),
        )


def test_fee_model_variations() -> None:
    """Test FeeModel variations: unsupported model, maker/taker, tiered, cap bounds."""
    # Test invalid model type exception
    with pytest.raises(SimulationError, match="Unsupported commission model"):
        FeeModel(model_type="INVALID_FEE")

    # Test NO_COMMISSION
    no_comm = FeeModel(model_type="NO_COMMISSION")
    assert no_comm.calculate_commission(
        Decimal("1.0"), Decimal("100.0"), Decimal("10.0")
    ) == Decimal("0.0")

    # Test FIXED_COMMISSION & PER_TRADE_COMMISSION
    fixed_model = FeeModel(model_type="FIXED_COMMISSION", fixed_commission=10.0)
    assert fixed_model.calculate_commission(
        Decimal("2.0"), Decimal("1.1"), Decimal(1000)
    ) == Decimal("10.0")

    per_trade_model = FeeModel(model_type="PER_TRADE_COMMISSION", fixed_commission=15.0)
    assert per_trade_model.calculate_commission(
        Decimal("2.0"), Decimal("1.1"), Decimal(1000)
    ) == Decimal("15.0")

    # Test PER_LOT_COMMISSION
    per_lot_model = FeeModel(model_type="PER_LOT_COMMISSION", per_lot_commission=5.0)
    assert per_lot_model.calculate_commission(
        Decimal("2.5"), Decimal("1.1"), Decimal(1000)
    ) == Decimal("12.50")

    # Test MAKER_TAKER_COMMISSION
    maker_taker = FeeModel(
        model_type="MAKER_TAKER_COMMISSION", maker_rate="0.0002", taker_rate="0.0005"
    )
    # Notional: 2.0 lots * 100 size * 100.0 price = 20,000.0
    # Maker: 20000 * 0.0002 = 4.0
    # Taker: 20000 * 0.0005 = 10.0
    assert maker_taker.calculate_commission(
        Decimal("2.0"), Decimal("100.0"), Decimal("100.0"), is_maker=True
    ) == Decimal("4.00")
    assert maker_taker.calculate_commission(
        Decimal("2.0"), Decimal("100.0"), Decimal("100.0"), is_maker=False
    ) == Decimal("10.00")

    # Test TIERED_COMMISSION
    # Tiers: [(1.0, 0.0010), (5.0, 0.0005), (10.0, 0.0002)]
    tiered = FeeModel(
        model_type="TIERED_COMMISSION",
        pct_notional="0.0001",
        tiers=[(1.0, "0.0010"), (5.0, "0.0005")],
    )
    # 0.5 lots -> Tier 1.0 -> 0.0010 rate
    # Notional = 0.5 * 100 * 10.0 = 500.0 -> 500 * 0.0010 = 0.5
    assert tiered.calculate_commission(
        Decimal("0.5"), Decimal("10.0"), Decimal("100.0")
    ) == Decimal("0.50")
    # 3.0 lots -> Tier 5.0 -> 0.0005 rate
    # Notional = 3.0 * 100 * 10.0 = 3,000 -> 3000 * 0.0005 = 1.5
    assert tiered.calculate_commission(
        Decimal("3.0"), Decimal("10.0"), Decimal("100.0")
    ) == Decimal("1.50")
    # 10.0 lots -> Fallback pct_notional (0.0001)
    # Notional = 10.0 * 100 * 10.0 = 10,000 -> 10000 * 0.0001 = 1.0
    assert tiered.calculate_commission(
        Decimal("10.0"), Decimal("10.0"), Decimal("100.0")
    ) == Decimal("1.00")

    # Test Min/Max bounds
    bounded = FeeModel(
        model_type="PERCENT_NOTIONAL_COMMISSION",
        pct_notional="0.01",
        min_commission="2.0",
        max_commission="10.0",
    )
    # Low commission: notional = 1 * 10 * 1 = 10 -> 10 * 0.01 = 0.1 -> minimum 2.0 applied
    assert bounded.calculate_commission(
        Decimal("1.0"), Decimal("1.0"), Decimal("10.0")
    ) == Decimal("2.00")
    # High commission: notional = 1 * 1000 * 10 = 10,000 -> 10000 * 0.01 = 100 -> maximum 10.0 applied
    assert bounded.calculate_commission(
        Decimal("1.0"), Decimal("10.0"), Decimal("1000.0")
    ) == Decimal("10.00")

    # Volume <= 0 edge case
    assert bounded.calculate_commission(
        Decimal("0.0"), Decimal("10.0"), Decimal("10.0")
    ) == Decimal("0.0")


def test_slippage_model_variations() -> None:
    """Test SlippageModel variations and validation exceptions."""
    # Test invalid model type exception
    with pytest.raises(SimulationError, match="Unsupported slippage model"):
        SlippageModel(model_type="INVALID_SLIPPAGE")

    # Test base price <= 0 exception
    model = SlippageModel(model_type="FIXED_SLIPPAGE", fixed_points=5)
    with pytest.raises(SimulationError, match="Base price must be positive"):
        model.calculate_price(Decimal("-1.0"), "BUY", Decimal("0.01"))

    # Test invalid direction exception
    with pytest.raises(SimulationError, match="Invalid order direction"):
        model.calculate_price(Decimal("1.0"), "INVALID", Decimal("0.01"))

    # Test SPREAD_RELATIVE_SLIPPAGE
    model_rel = SlippageModel(model_type="SPREAD_RELATIVE_SLIPPAGE")
    price_rel = model_rel.calculate_price(
        base_price=Decimal("1.10000"),
        direction="BUY",
        point=Decimal("0.00001"),
        spread_points=10,
    )
    # spread_points=10 -> slippage_points = 10 // 2 = 5 -> price = 1.10005
    assert price_rel == Decimal("1.10005")

    # Test VOLATILITY_SLIPPAGE
    model_vol = SlippageModel(
        model_type="VOLATILITY_SLIPPAGE", volatility_multiplier="0.5", min_points=2
    )
    # Volatility = 20.0 -> points = 20 * 0.5 = 10 -> price = 1.10010
    price_vol = model_vol.calculate_price(
        base_price=Decimal("1.10000"),
        direction="BUY",
        point=Decimal("0.00001"),
        volatility=Decimal("20.0"),
    )
    assert price_vol == Decimal("1.10010")

    # Test VOLUME_SLIPPAGE
    model_vol2 = SlippageModel(
        model_type="VOLUME_SLIPPAGE", volume_multiplier="0.1", min_points=1
    )
    # Volume = 50.0 -> points = 50 * 0.1 = 5 -> price = 1.10005
    price_vol2 = model_vol2.calculate_price(
        base_price=Decimal("1.10000"),
        direction="BUY",
        point=Decimal("0.00001"),
        volume=Decimal("50.0"),
    )
    assert price_vol2 == Decimal("1.10005")

    # Test max slippage cap
    model_cap = SlippageModel(
        model_type="FIXED_SLIPPAGE", fixed_points=20, max_slippage_points=5
    )
    price_cap = model_cap.calculate_price(
        base_price=Decimal("1.10000"), direction="BUY", point=Decimal("0.00001")
    )
    # fixed_points=20 but capped at 5 -> price = 1.10005
    assert price_cap == Decimal("1.10005")


def test_liquidity_model_variations() -> None:
    """Test LiquidityModel options, exceptions, and order book walking."""
    # Test invalid model type exception
    with pytest.raises(SimulationError, match="Unsupported liquidity model"):
        LiquidityModel(model_type="INVALID_LIQ")

    # Test volume below min exception
    model = LiquidityModel(model_type="INFINITE_LIQUIDITY", min_fill_volume=0.1)
    with pytest.raises(SimulationError, match="below minimum fill volume"):
        model.evaluate_fill(Decimal("0.05"), "BUY")

    # Test volume limit liquidity rejected because filled < min_fill_volume
    model_lim = LiquidityModel(
        model_type="VOLUME_LIMIT_LIQUIDITY",
        max_volume_pct=Decimal("0.1"),
        min_fill_volume=Decimal("0.5"),
    )
    res_lim = model_lim.evaluate_fill(
        requested_volume=Decimal("2.0"),
        direction="BUY",
        available_market_volume=Decimal(
            "1.0"
        ),  # allowed = 1.0 * 0.1 = 0.1 < min_fill (0.5)
    )
    assert res_lim["status"] == "rejected"
    assert res_lim["filled_volume"] == Decimal("0.0")

    # Test order book walking missing book depth exception
    model_book = LiquidityModel(model_type="ORDER_BOOK_LIQUIDITY")
    with pytest.raises(SimulationError, match="Order book depth data required"):
        model_book.evaluate_fill(Decimal("1.0"), "BUY")

    # Test order book walking full fill
    book_depth = [
        {"price": 1.10000, "volume": 0.5},
        {"price": 1.10010, "volume": 1.0},
    ]
    res_book = model_book.evaluate_fill(
        requested_volume=Decimal("1.0"), direction="BUY", order_book_depth=book_depth
    )
    assert res_book["status"] == "success"
    # filled 0.5 @ 1.10000, and 0.5 @ 1.10010 -> VWAP = (0.5 * 1.10000 + 0.5 * 1.10010) / 1.0 = 1.10005
    assert res_book["filled_volume"] == Decimal("1.0")
    assert res_book["vwap_price"] == Decimal("1.10005")

    # Test order book walking partial fill
    res_book_partial = model_book.evaluate_fill(
        requested_volume=Decimal("2.0"), direction="BUY", order_book_depth=book_depth
    )
    assert res_book_partial["status"] == "partial"
    assert res_book_partial["filled_volume"] == Decimal("1.5")
    assert res_book_partial["unfilled_volume"] == Decimal("0.5")

    # Test order book walking rejected because filled < min_fill_volume
    model_book_min = LiquidityModel(
        model_type="ORDER_BOOK_LIQUIDITY", min_fill_volume=Decimal("2.0")
    )
    res_book_rej = model_book_min.evaluate_fill(
        requested_volume=Decimal("2.0"),
        direction="BUY",
        order_book_depth=book_depth,  # total available volume is 1.5 < min_fill 2.0
    )
    assert res_book_rej["status"] == "rejected"
    assert res_book_rej["filled_volume"] == Decimal("0.0")


def test_spread_model_extra_cases() -> None:
    """Test SpreadModel unsupported model, negative spread points, and native spread fallback."""
    with pytest.raises(SimulationError, match="Unsupported spread model"):
        SpreadModel(model_type="INVALID_SPREAD_MODEL")

    model = SpreadModel(model_type="NATIVE_SPREAD", fixed_points=20)
    with pytest.raises(SimulationError, match="Negative spread detected"):
        model.calculate_ask(
            Decimal("1.10000"), Decimal("0.00001"), record_spread_points=-5
        )

    # Native spread fallback to fixed points when record_spread_points is None
    native_model = SpreadModel(model_type="NATIVE_SPREAD", fixed_points=15)
    assert native_model.get_spread_points(record_spread_points=None) == 15
    assert native_model.get_spread_points(record_spread_points=25) == 25
