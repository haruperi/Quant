# ruff: noqa: E501
"""Unit tests for the Trend Following Strategy."""

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest
from app.services.strategies import (
    BaseStrategy,
    StrategyConfigError,
    StrategyExecutionContext,
    TradeIntent,
    get_strategy,
    list_strategies,
    run_vectorized_strategy_signals,
    validate_strategy_config,
    validate_strategy_ref,
)
from app.services.strategies.source.trend_following import (
    TrendFollowingStrategy,
)


def test_trend_following_registration():
    """Verify TrendFollowingStrategy is automatically registered and conforms to protocols."""
    assert "trend_following:1.0.0" in list_strategies()
    strategy_class = get_strategy("trend_following")
    assert strategy_class == TrendFollowingStrategy
    assert issubclass(TrendFollowingStrategy, BaseStrategy)


def test_trend_following_config_validation():
    """Verify configuration validation behaves correctly with edge cases."""
    # 1. Valid config
    valid_cfg = {
        "symbol": "EURUSD",
        "fast_period": 10,
        "slow_period": 20,
        "filter_period": 50,
    }
    validated = validate_strategy_config(TrendFollowingStrategy, valid_cfg)
    assert validated["symbol"] == "EURUSD"
    assert validated["fast_period"] == 10
    assert validated["slow_period"] == 20
    assert validated["filter_period"] == 50

    # 2. Invalid periods (must be minimum=1)
    invalid_cfg_zero = {
        "symbol": "EURUSD",
        "fast_period": 0,
        "slow_period": 20,
        "filter_period": 50,
    }
    with pytest.raises(StrategyConfigError):
        validate_strategy_config(TrendFollowingStrategy, invalid_cfg_zero)

    # 3. Invalid periods exceeding maximum (fast_period maximum is 100)
    invalid_cfg_max = {
        "symbol": "EURUSD",
        "fast_period": 101,
        "slow_period": 200,
        "filter_period": 300,
    }
    with pytest.raises(StrategyConfigError):
        validate_strategy_config(TrendFollowingStrategy, invalid_cfg_max)

    # 4. Invalid periods violating step constraint (e.g. non-integer/float values like 10.5 for integer type)
    invalid_cfg_type_float = {
        "symbol": "EURUSD",
        "fast_period": 10.5,
        "slow_period": 20,
        "filter_period": 50,
    }
    with pytest.raises(StrategyConfigError):
        validate_strategy_config(TrendFollowingStrategy, invalid_cfg_type_float)

    # 5. Invalid crossover constraints (fast must be less than slow) validated in on_init
    invalid_cfg_crossover = {
        "symbol": "EURUSD",
        "fast_period": 20,
        "slow_period": 20,
        "filter_period": 50,
    }
    strategy = TrendFollowingStrategy()
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 17, 3, 0, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="test_seed",
        request_id="req-123",
        correlation_id="corr-123",
    )
    with pytest.raises(StrategyConfigError):
        strategy.on_init(ctx, invalid_cfg_crossover)


def test_trend_following_indicator_calculations():
    """Verify that indicators and shifted columns are computed correctly."""
    strategy = TrendFollowingStrategy()
    config = {
        "symbol": "EURUSD",
        "fast_period": 2,
        "slow_period": 4,
        "filter_period": 6,
    }

    # Generate basic prices
    idx = pd.date_range("2026-06-16T12:00:00", periods=10, freq="h", tz=UTC)
    df = pd.DataFrame({"close": np.linspace(1.1000, 1.1100, 10)}, index=idx)

    # Calculate indicators
    df_ind = strategy._calculate_indicators(df, config)
    assert "fast_ema" in df_ind.columns
    assert "slow_ema" in df_ind.columns
    assert "filter_ema" in df_ind.columns

    # Shift features
    df_shifted = strategy._shift_features(df_ind)
    assert "fast_signal" in df_shifted.columns
    assert "slow_signal" in df_shifted.columns
    assert "filter_signal" in df_shifted.columns
    assert "prev_fast_signal" in df_shifted.columns
    assert "prev_slow_signal" in df_shifted.columns

    # Check shift offset (shift(1) and shift(2))
    assert df_shifted["fast_signal"].iloc[1] == df_ind["fast_ema"].iloc[0]
    assert df_shifted["prev_fast_signal"].iloc[2] == df_ind["fast_ema"].iloc[0]


def test_trend_following_signals_and_intents():
    """Verify vectorized run creates signal conditions and yields TradeIntents."""
    # Generate mock price dataframe that creates a clear bullish crossover
    # Fast EMA = 2, Slow EMA = 4, Filter EMA = 8
    idx = pd.date_range("2026-06-16T12:00:00", periods=15, freq="h", tz=UTC)
    prices = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
    opens = [1.0] * 15

    df = pd.DataFrame({"close": prices, "open": opens}, index=idx)

    # Validate ref
    res_ref = validate_strategy_ref("trend_following", environment="BACKTEST")
    assert res_ref["status"] == "success"

    ref = res_ref["data"]["strategy_ref"]
    # Decision timestamp is right at the end of the series
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 17, 3, 0, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="test_seed",
        request_id="req-123",
        correlation_id="corr-123",
    )

    res = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=df,
        indicators=pd.DataFrame(index=df.index),  # empty shifted indicator DataFrame
        context=ctx,
        config={
            "symbol": "EURUSD",
            "fast_period": 2,
            "slow_period": 4,
            "filter_period": 8,
        },
    )

    assert res["status"] == "success"
    intents = res["data"]["trade_intents"]
    assert len(intents) > 0

    # Verify lookahead checks (signal_timestamp must be strictly before decision_timestamp)
    for intent in intents:
        assert isinstance(intent, TradeIntent)
        assert intent.symbol == "EURUSD"
        assert intent.signal_timestamp < intent.decision_timestamp
        assert intent.side in ("BUY", "SELL")
        assert intent.intent_type in ("OPEN", "CLOSE")


def test_trend_following_event_lifecycle_hooks():
    """Verify that event lifecycle hooks on_init and on_bar behave correctly for event-driven execution."""
    strategy = TrendFollowingStrategy()
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
        "fast_period": 2,
        "slow_period": 4,
        "filter_period": 8,
    }

    # 1. Test on_init
    res_init = strategy.on_init(ctx, config)
    assert res_init == {"state_updates": {}, "trade_intents": []}

    # 2. Test on_bar with a single bar dict
    bar_data = {
        "timestamp": datetime(2026, 6, 17, 2, 0, tzinfo=UTC),
        "open": 1.1000,
        "high": 1.1050,
        "low": 1.0950,
        "close": 1.1020,
        "volume": 100.0,
    }
    res_bar = strategy.on_bar(
        bar=bar_data,
        indicators={},
        read_only_state=None,
        context=ctx,
        config=config,
    )
    assert "trade_intents" in res_bar
    assert "state_updates" in res_bar
