"""Unit tests for the RandomWalk grid trading strategy."""

from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
import pytest
from app.services.strategies import (
    BaseStrategy,
    ReadOnlyExecutionStateSnapshot,
    StrategyConfigError,
    StrategyExecutionContext,
    StrategyRefInput,
    get_strategy,
    list_strategies,
    run_vectorized_strategy_signals,
    validate_strategy_config,
)
from app.services.strategies.source.random_walk import (
    RandomWalkStrategy,
)


def test_random_walk_registration() -> None:
    """Verify RandomWalkStrategy is registered and conforms to protocol expectations."""
    assert "random_walk:1.0.0" in list_strategies()
    strategy_class = get_strategy("random_walk")
    assert strategy_class == RandomWalkStrategy
    assert issubclass(RandomWalkStrategy, BaseStrategy)


def test_random_walk_config_validation() -> None:
    """Verify configuration validation behaves correctly for RandomWalkStrategy."""
    # 1. Valid config
    valid_cfg = {
        "symbol": "EURUSD",
        "timeframe": "5m",
        "sell_magic": 2134,
        "buy_magic": 2323,
        "take_profit": 20.0,
        "stop_loss": 10.0,
        "total_volume": 0.3,
        "volume_per_trade": 0.02,
        "point_size": 0.00001,
    }
    validated = validate_strategy_config(RandomWalkStrategy, valid_cfg)
    assert validated["symbol"] == "EURUSD"
    assert validated["volume_per_trade"] == 0.02

    # 2. Invalid Pydantic validation (negative total_volume)
    invalid_pydantic = valid_cfg.copy()
    invalid_pydantic["total_volume"] = -0.5
    with pytest.raises(StrategyConfigError):
        validate_strategy_config(RandomWalkStrategy, invalid_pydantic)

    # 3. Invalid volume constraints on_init (volume_per_trade > total_volume)
    invalid_init = valid_cfg.copy()
    invalid_init["volume_per_trade"] = 0.5
    strategy = RandomWalkStrategy()
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 17, 3, 0, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="test_seed",
        request_id="req-123",
        correlation_id="corr-123",
    )
    with pytest.raises(StrategyConfigError) as exc:
        strategy.on_init(ctx, invalid_init)
    assert "cannot exceed total_volume" in str(exc.value)

    # 4. Zero/Negative volume limits on_init
    invalid_zero = valid_cfg.copy()
    invalid_zero["total_volume"] = 0.0
    with pytest.raises(StrategyConfigError) as exc:
        strategy.on_init(ctx, invalid_zero)
    assert "must be positive" in str(exc.value)


def test_random_walk_active_counts() -> None:
    """Verify that private active position counter helper works correctly."""
    strategy = RandomWalkStrategy()

    # Mock snapshot with some active positions
    snapshot = ReadOnlyExecutionStateSnapshot(
        snapshot_id="snap-1",
        snapshot_at=datetime(2026, 6, 17, 3, 0, tzinfo=UTC),
        source_module="simulation",
        open_positions=[
            {"symbol": "EURUSD", "magic": 2323, "side": "BUY", "ticket": 100},
            {"symbol": "EURUSD", "magic": 2323, "type": 0, "ticket": 101},  # Also BUY
            {"symbol": "EURUSD", "magic": 2134, "side": "SELL", "ticket": 200},
            {
                "symbol": "GBPUSD",
                "magic": 2323,
                "side": "BUY",
                "ticket": 300,
            },  # Different symbol
        ],
    )

    assert strategy._count_active_buys(snapshot, "EURUSD", 2323) == 2
    assert strategy._count_active_buys(snapshot, "EURUSD", 9999) == 0
    assert strategy._count_active_sells(snapshot, "EURUSD", 2134) == 1
    assert strategy._count_active_sells(snapshot, "GBPUSD", 2323) == 0


def test_random_walk_event_driven_grid_generation() -> None:
    """Verify that event-driven on_bar generates correct intents."""
    strategy = RandomWalkStrategy()
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 17, 3, 0, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="test_seed",
        request_id="req-123",
        correlation_id="corr-123",
    )
    config = {
        "symbol": "EURUSD",
        "buy_magic": 2323,
        "sell_magic": 2134,
        "total_volume": 0.04,
        "volume_per_trade": 0.02,
        "take_profit": 20.0,
        "stop_loss": 10.0,
        "point_size": 0.00001,
    }

    bar_data = {
        "timestamp": datetime(2026, 6, 17, 2, 55, tzinfo=UTC),
        "open": 1.1000,
        "high": 1.1050,
        "low": 1.0950,
        "close": 1.1020,
    }

    # 1. No open positions -> should emit both BUY and SELL grids (4 elements total)
    res_empty = strategy.on_bar(
        bar=bar_data,
        indicators={},
        read_only_state=None,
        context=ctx,
        config=config,
    )
    intents = res_empty["trade_intents"]
    assert len(intents) == 4

    buys = [i for i in intents if i.side == "BUY"]
    sells = [i for i in intents if i.side == "SELL"]
    assert len(buys) == 2
    assert len(sells) == 2

    # Check Buy elements pricing targets
    assert buys[0].stop_loss == Decimal("1.101")
    assert buys[0].take_profit == Decimal("1.104")
    assert buys[1].stop_loss == Decimal("1.1")
    assert buys[1].take_profit == Decimal("1.106")

    # 2. Existing active BUY position -> should emit ONLY SELL grid (2 elements)
    snapshot = ReadOnlyExecutionStateSnapshot(
        snapshot_id="snap-1",
        snapshot_at=datetime(2026, 6, 17, 3, 0, tzinfo=UTC),
        source_module="simulation",
        open_positions=[
            {"symbol": "EURUSD", "magic": 2323, "side": "BUY", "ticket": 100}
        ],
    )
    res_active = strategy.on_bar(
        bar=bar_data,
        indicators={},
        read_only_state=snapshot,
        context=ctx,
        config=config,
    )
    intents_active = res_active["trade_intents"]
    assert len(intents_active) == 2
    assert all(i.side == "SELL" for i in intents_active)


def test_random_walk_vectorized_signals() -> None:
    """Verify chronological position simulation runs inside run_vectorized_signals."""
    # Create simple market dataset
    idx = pd.date_range("2026-06-16T12:00:00", periods=4, freq="5min", tz=UTC)
    market_data = pd.DataFrame(
        {
            "open": [1.1000, 1.1000, 1.1020, 1.0960],
            "high": [1.1010, 1.1050, 1.1030, 1.0970],
            "low": [1.0990, 1.0990, 1.0950, 1.0950],
            "close": [1.1000, 1.1020, 1.0960, 1.0960],
        },
        index=idx,
    )

    # Use a decision timestamp close to the data index to pass latency check
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 16, 12, 20, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="test_seed",
        request_id="req-123",
        correlation_id="corr-123",
    )

    config = {
        "symbol": "EURUSD",
        "buy_magic": 2323,
        "sell_magic": 2134,
        "total_volume": 0.04,
        "volume_per_trade": 0.02,
        "take_profit": 20.0,
        "stop_loss": 10.0,
        "point_size": 0.00001,
    }

    # Run
    res = run_vectorized_strategy_signals(
        strategy_ref=StrategyRefInput(
            strategy_id="random_walk", environment="BACKTEST"
        ),
        market_data=market_data,
        indicators=pd.DataFrame(index=market_data.index),
        context=ctx,
        config=config,
    )

    assert res["status"] == "success"
    intents = res["data"]["trade_intents"]

    # Under this price path:
    # Bar 0 (12:00): Grid opens (2 BUY, 2 SELL) = 4 intents.
    # Bar 1 (12:05): Buy 1 SL hit, Buy 2 TP hit. Sells hit SL.
    #                Both grids re-opened = 4 intents.
    # Bar 2 (12:10): All buys and sells hit SL/TP.
    #                Both grids re-opened = 4 intents.
    # Bar 3 (12:15): All buys and sells hit SL/TP.
    #                Both grids re-opened = 4 intents.
    # Total = 16 intents.
    assert len(intents) == 16

    # Verify signal timestamps
    assert intents[0].signal_timestamp == datetime(2026, 6, 16, 11, 55, tzinfo=UTC)
    assert intents[0].decision_timestamp == datetime(2026, 6, 16, 12, 0, tzinfo=UTC)

    assert intents[-1].signal_timestamp == datetime(2026, 6, 16, 12, 10, tzinfo=UTC)
    assert intents[-1].decision_timestamp == datetime(2026, 6, 16, 12, 15, tzinfo=UTC)
