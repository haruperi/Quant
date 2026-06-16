"""Unit tests for Pydantic models and precision contracts."""

from typing import Any

import pytest
from app.services.data.models import (
    OHLCVRecord,
    SpreadRecord,
    TickRecord,
)
from app.services.data.validation import normalize_numeric, validate_step_alignment
from app.utils.errors import ValidationError
from pydantic import ValidationError as PydanticValidationError


def test_ohlcv_record_validation() -> None:
    """Verify OHLCVRecord validations."""
    valid_data: dict[str, Any] = {
        "timestamp": "2026-06-01T00:00:00Z",
        "open": 1.1000,
        "high": 1.1050,
        "low": 1.0990,
        "close": 1.1010,
        "volume": 100,
        "tick_volume": 80,
        "real_volume": 0.0,
        "spread": 1.5,
        "source": "csv",
        "symbol": "EURUSD",
        "timeframe": "M5",
    }
    record = OHLCVRecord(**valid_data)
    assert record.symbol == "EURUSD"
    assert record.high == 1.1050

    # Inconsistent price structure (low > open)
    invalid_data = valid_data.copy()
    invalid_data["low"] = 1.1100
    with pytest.raises(PydanticValidationError):
        OHLCVRecord(**invalid_data)


def test_tick_record_validation() -> None:
    """Verify TickRecord validations."""
    valid_tick: dict[str, Any] = {
        "timestamp": "2026-06-01T12:00:00.123Z",
        "bid": 1.1005,
        "ask": 1.1006,
        "last": 1.1006,
        "volume": 1,
        "spread": 1.0,
        "source": "csv",
        "symbol": "EURUSD",
    }
    record = TickRecord(**valid_tick)
    assert record.bid == 1.1005

    # Bid > Ask violation
    invalid_tick = valid_tick.copy()
    invalid_tick["bid"] = 1.1010
    with pytest.raises(PydanticValidationError):
        TickRecord(**invalid_tick)

    # Empty bid/ask/last
    empty_tick = valid_tick.copy()
    empty_tick["bid"] = ""
    empty_tick["ask"] = ""
    empty_tick["last"] = ""
    with pytest.raises(PydanticValidationError):
        TickRecord(**empty_tick)


def test_spread_record_validation() -> None:
    """Verify SpreadRecord validations."""
    valid_spread: dict[str, Any] = {
        "timestamp": "2026-06-01T12:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.1000,
        "ask": 1.1002,
        "spread_points": 2.0,
        "spread_pips": 0.2,
        "source": "csv",
    }
    record = SpreadRecord(**valid_spread)
    assert record.spread_pips == 0.2

    # Ask < Bid violation
    invalid_spread = valid_spread.copy()
    invalid_spread["ask"] = 1.0999
    with pytest.raises(PydanticValidationError):
        SpreadRecord(**invalid_spread)


def test_precision_workflow_normalization() -> None:
    """Verify decimal vs float normalization policies."""
    # Research context returns float
    res_val = normalize_numeric(1.1234567, 5, "research")
    assert isinstance(res_val, float)
    assert res_val == 1.12346

    # Production/Risk contexts return decimal string representation
    prod_val = normalize_numeric(1.1234567, 5, "execution_bound")
    assert isinstance(prod_val, str)
    assert prod_val == "1.12346"


def test_precision_step_alignment() -> None:
    """Verify tick-size step alignment check."""
    # Valid alignment
    validate_step_alignment(1.10055, 0.00001, "risk")

    # Invalid alignment in risk context triggers error
    with pytest.raises(ValidationError):
        validate_step_alignment(1.100553, 0.00001, "risk")
