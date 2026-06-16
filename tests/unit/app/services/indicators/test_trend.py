# ruff: noqa: E501, PD011, PT018, NPY002, DTZ001, RUF100
"""Unit tests for trend indicators (SMA, EMA, ADX)."""

from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from app.services.indicators.batch.trend import (
    AverageDirectionalIndex,
    ExponentialMovingAverage,
    SimpleMovingAverage,
)
from app.services.indicators.errors import (
    IndicatorParameterError,
    InsufficientDataError,
)
from app.services.indicators.protocols import IndicatorConfig


def generate_mock_ohlcv(
    rows: int,
    constant_price: float | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "D1",
) -> pd.DataFrame:
    """Generate aligned mock OHLCV DataFrame for testing."""
    start_time = datetime(2026, 1, 1, tzinfo=UTC)
    timestamps = [start_time + timedelta(days=i) for i in range(rows)]

    if constant_price is not None:
        high = np.full(rows, constant_price)
        low = np.full(rows, constant_price)
        open_val = np.full(rows, constant_price)
        close = np.full(rows, constant_price)
        volume = np.full(rows, 100.0)
    else:
        # Volatile random data
        np.random.seed(42)
        close = np.cumprod(1.0 + np.random.normal(0, 0.01, rows)) * 1.10
        high = close * 1.01
        low = close * 0.99
        open_val = close * 0.995
        volume = np.random.uniform(50.0, 150.0, rows)

    df = pd.DataFrame(
        {
            "open": open_val,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "quality": ["good"] * rows,
            "symbol": [symbol] * rows,
            "timeframe": [timeframe] * rows,
        },
        index=pd.DatetimeIndex(timestamps, name="timestamp"),
    )
    return df


def test_sma_constant_price():
    """Verify SMA over constant price equals the constant price after warmup."""
    df = generate_mock_ohlcv(20, constant_price=1.2500)
    sma_ind = SimpleMovingAverage()

    config = IndicatorConfig(indicator_id="sma", parameters={"period": 5})
    res = sma_ind.calculate(df, config)

    # First 4 rows (0, 1, 2, 3) must be NaN
    assert res.values["sma_5"].iloc[:4].isna().all()
    # Subsequent rows must equal 1.2500
    assert np.allclose(res.values["sma_5"].iloc[4:], 1.2500)
    assert res.output_columns == ["sma_5"]
    assert "available_at" in res.values.columns
    assert "quality" in res.values.columns
    assert res.manifest.indicator_id == "sma"


def test_sma_invalid_parameters():
    """Verify validation of invalid parameter ranges."""
    sma_ind = SimpleMovingAverage()
    with pytest.raises(IndicatorParameterError):
        sma_ind.validate_parameters({"period": 0})
    with pytest.raises(IndicatorParameterError):
        sma_ind.validate_parameters({"period": -5})
    with pytest.raises(IndicatorParameterError):
        sma_ind.validate_parameters({"period": "invalid"})


def test_sma_insufficient_data():
    """Verify behavior on insufficient data size."""
    df = generate_mock_ohlcv(5)
    sma_ind = SimpleMovingAverage()
    config = IndicatorConfig(indicator_id="sma", parameters={"period": 10})
    with pytest.raises(InsufficientDataError):
        sma_ind.calculate(df, config)


def test_ema_constant_price_convergence():
    """Verify EMA over constant price converges according to seed policy."""
    df = generate_mock_ohlcv(20, constant_price=1.2500)
    ema_ind = ExponentialMovingAverage()

    config = IndicatorConfig(indicator_id="ema", parameters={"period": 5})
    res = ema_ind.calculate(df, config)

    # First 4 rows must be NaN, 5th row must be SMA (1.25)
    assert res.values["ema_5"].iloc[:4].isna().all()
    assert np.allclose(res.values["ema_5"].iloc[4:], 1.2500)


def test_adx_calculations():
    """Verify ADX calculations and outputs match standard schema."""
    df = generate_mock_ohlcv(40)  # Random prices
    adx_ind = AverageDirectionalIndex()

    config = IndicatorConfig(indicator_id="adx", parameters={"period": 14})
    res = adx_ind.calculate(df, config)

    assert len(res.output_columns) == 3
    assert "adx_14" in res.output_columns
    assert "plus_di_14" in res.output_columns
    assert "minus_di_14" in res.output_columns

    # Check that warmup is at least 27 bars (2 * 14 - 1)
    # So first 27 values are NaN (indices 0 to 26)
    assert res.values["adx_14"].iloc[:27].isna().all()
    assert not res.values["adx_14"].iloc[27:].isna().any()

    # DIs must be between 0 and 100
    di_plus = res.values["plus_di_14"].dropna()
    di_minus = res.values["minus_di_14"].dropna()
    assert (di_plus >= 0).all()
    assert (di_plus <= 100).all()
    assert (di_minus >= 0).all()
    assert (di_minus <= 100).all()
