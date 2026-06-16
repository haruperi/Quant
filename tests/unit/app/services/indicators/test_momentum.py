# ruff: noqa: E501, PD011, PT018, NPY002, DTZ001, RUF100
"""Unit tests for momentum indicators (RSI, Williams %R)."""

import numpy as np
import pytest
from app.services.indicators.batch.momentum import RelativeStrengthIndex, WilliamsR
from app.services.indicators.errors import (
    IndicatorParameterError,
)
from app.services.indicators.protocols import IndicatorConfig

from tests.unit.app.services.indicators.test_trend import generate_mock_ohlcv


def test_rsi_constant_price():
    """Verify RSI over flat prices returns 50."""
    df = generate_mock_ohlcv(20, constant_price=1.2000)
    rsi_ind = RelativeStrengthIndex()

    config = IndicatorConfig(indicator_id="rsi", parameters={"period": 5})
    res = rsi_ind.calculate(df, config)

    # Warmup needs 5 changes = 6 prices
    assert res.values["rsi_close_5"].iloc[:5].isna().all()
    assert np.allclose(res.values["rsi_close_5"].iloc[5:], 50.0)


def test_rsi_bounds():
    """Verify RSI output ranges remain between 0 and 100 for random inputs."""
    df = generate_mock_ohlcv(40)
    rsi_ind = RelativeStrengthIndex()

    config = IndicatorConfig(indicator_id="rsi", parameters={"period": 14})
    res = rsi_ind.calculate(df, config)

    valid_vals = res.values["rsi_close_14"].dropna()
    assert (valid_vals >= 0.0).all()
    assert (valid_vals <= 100.0).all()


def test_williams_r_degenerate_window():
    """Verify Williams %R returns NaN when HighestHigh equals LowestLow."""
    df = generate_mock_ohlcv(20, constant_price=1.2000)
    wr_ind = WilliamsR()

    config = IndicatorConfig(indicator_id="williams_r", parameters={"period": 5})
    res = wr_ind.calculate(df, config)

    # Since high == low everywhere, range is 0. Williams %R must be NaN
    assert res.values["williams_r_5"].isna().all()


def test_williams_r_bounds():
    """Verify Williams %R is between -100 and 0 for random inputs."""
    df = generate_mock_ohlcv(40)
    wr_ind = WilliamsR()

    config = IndicatorConfig(indicator_id="williams_r", parameters={"period": 14})
    res = wr_ind.calculate(df, config)

    valid_vals = res.values["williams_r_14"].dropna()
    assert (valid_vals >= -100.0).all()
    assert (valid_vals <= 0.0).all()


def test_momentum_invalid_parameters():
    """Verify momentum parameters are validated."""
    wr_ind = WilliamsR()
    with pytest.raises(IndicatorParameterError):
        wr_ind.validate_parameters({"period": 0})
    with pytest.raises(IndicatorParameterError):
        wr_ind.validate_parameters({"period": -14})
