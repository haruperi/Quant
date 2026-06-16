# ruff: noqa: E501, PD011, PT018, NPY002, DTZ001, RUF100
"""Unit tests for volatility indicators (ATR, ADR, Rolling Volatility)."""

import numpy as np
import pytest
from app.services.indicators.batch.volatility import (
    AverageDailyRange,
    AverageTrueRange,
    RollingVolatility,
)
from app.services.indicators.errors import (
    IndicatorParameterError,
)
from app.services.indicators.protocols import IndicatorConfig

from tests.unit.app.services.indicators.test_trend import generate_mock_ohlcv


def test_atr_constant_price():
    """Verify ATR over constant price equals 0."""
    df = generate_mock_ohlcv(20, constant_price=1.2000)
    atr_ind = AverageTrueRange()

    config = IndicatorConfig(indicator_id="atr", parameters={"period": 5})
    res = atr_ind.calculate(df, config)

    # First 4 rows are NaN, 5th row is seed (0)
    assert res.values["atr_5"].iloc[:4].isna().all()
    assert np.allclose(res.values["atr_5"].iloc[4:], 0.0)


def test_adr_constant_price():
    """Verify ADR over constant price equals 0."""
    df = generate_mock_ohlcv(20, constant_price=1.2000)
    adr_ind = AverageDailyRange()

    config = IndicatorConfig(indicator_id="adr", parameters={"period": 5})
    res = adr_ind.calculate(df, config)

    # First 4 rows are NaN, 5th row onwards are 0
    assert res.values["adr_5"].iloc[:4].isna().all()
    assert np.allclose(res.values["adr_5"].iloc[4:], 0.0)


def test_volatility_constant_price():
    """Verify Rolling Volatility over constant price equals 0."""
    df = generate_mock_ohlcv(20, constant_price=1.2000)
    vol_ind = RollingVolatility()

    config = IndicatorConfig(
        indicator_id="rolling_volatility",
        parameters={"period": 5, "return_type": "log"},
    )
    res = vol_ind.calculate(df, config)

    # Volatility needs 5 returns, which takes 6 price rows
    assert res.values["rolling_volatility_close_5"].iloc[:5].isna().all()
    assert np.allclose(res.values["rolling_volatility_close_5"].iloc[5:], 0.0)


def test_volatility_simple_returns():
    """Verify Rolling Volatility can run on simple returns."""
    df = generate_mock_ohlcv(20)  # Random prices
    vol_ind = RollingVolatility()

    config = IndicatorConfig(
        indicator_id="rolling_volatility",
        parameters={"period": 5, "return_type": "simple"},
    )
    res = vol_ind.calculate(df, config)
    assert "rolling_volatility_close_5" in res.output_columns
    assert res.values["rolling_volatility_close_5"].iloc[:5].isna().all()
    assert not res.values["rolling_volatility_close_5"].iloc[5:].isna().any()
    # Volatility must be non-negative
    assert (res.values["rolling_volatility_close_5"].dropna() >= 0.0).all()


def test_volatility_invalid_parameters():
    """Verify standard volatility parameter ranges are guarded."""
    vol_ind = RollingVolatility()
    with pytest.raises(IndicatorParameterError):
        vol_ind.validate_parameters({"period": 1})  # must be >= 2
    with pytest.raises(IndicatorParameterError):
        vol_ind.validate_parameters({"period": 5, "return_type": "invalid"})
