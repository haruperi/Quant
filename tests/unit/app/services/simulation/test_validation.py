# ruff: noqa: E501
"""Unit tests for simulation schemas, metadata, and data quality check gates."""

from __future__ import annotations

import pytest
from app.services.simulation.validation.quality import check_data_quality
from app.services.simulation.validation.schema import (
    SimulationBacktestRequestV1,
)
from app.utils.errors import SimulationError


def test_request_schema_defaults() -> None:
    """Test SimulationBacktestRequestV1 Pydantic model initialization."""
    req = SimulationBacktestRequestV1(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="H1",
        start="2026-06-01T00:00:00Z",
        end="2026-06-10T00:00:00Z",
    )
    assert req.initial_balance == 10000.0
    assert req.account_currency == "USD"
    assert req.tick_model == "M1_TICKS"


def test_check_data_quality_valid() -> None:
    """Test data quality checks with valid OHLCV records."""
    records = [
        {
            "timestamp": "2026-06-17T10:00:00Z",
            "symbol": "EURUSD",
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.10,
            "volume": 10,
        },
        {
            "timestamp": "2026-06-17T10:01:00Z",
            "symbol": "EURUSD",
            "open": 1.10,
            "high": 1.12,
            "low": 1.09,
            "close": 1.11,
            "volume": 12,
        },
    ]
    report = check_data_quality(records, expected_symbol="EURUSD", timeframe="M1")
    assert report.status == "passed"
    assert report.history_quality == 100.0
    assert len(report.issues) == 0


def test_check_data_quality_invalid() -> None:
    """Test data quality checks trigger failures on negative prices and non-monotonic time."""
    records = [
        {
            "timestamp": "2026-06-17T10:01:00Z",
            "symbol": "EURUSD",
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.10,
            "volume": 10,
        },
        {
            "timestamp": "2026-06-17T10:00:00Z",
            "symbol": "EURUSD",
            "open": -1.10,
            "high": 1.12,
            "low": 1.09,
            "close": 1.11,
            "volume": 12,
        },  # Non-monotonic time & negative price
    ]
    with pytest.raises(SimulationError, match="Severe data quality errors found"):
        check_data_quality(
            records, expected_symbol="EURUSD", timeframe="M1", block_on_severe=True
        )


def test_data_quality_empty_records() -> None:
    """Test data quality checks with empty input dataset."""
    # When block_on_severe=True, should raise SimulationError
    with pytest.raises(SimulationError, match=r"Cannot run backtest on empty data\."):
        check_data_quality(
            [], expected_symbol="EURUSD", timeframe="M1", block_on_severe=True
        )

    # When block_on_severe=False, should return failed report
    report = check_data_quality(
        [], expected_symbol="EURUSD", timeframe="M1", block_on_severe=False
    )
    assert report.status == "failed"
    assert report.history_quality == 0.0
    assert len(report.issues) == 1
    assert report.issues[0]["code"] == "SIM_DATA_EMPTY"


def test_data_quality_duplicates_and_invalid_timestamps() -> None:
    """Test data quality checks logic with duplicate and invalid formatted timestamps."""
    records = [
        {
            "timestamp": "2026-06-17T10:00:00Z",
            "symbol": "EURUSD",
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.10,
            "volume": 10,
        },
        {
            "timestamp": "2026-06-17T10:00:00Z",
            "symbol": "EURUSD",
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.10,
            "volume": 10,
        },  # Duplicate
        {
            "timestamp": "invalid-timestamp-string",
            "symbol": "EURUSD",
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.10,
            "volume": 10,
        },  # Invalid timestamp format (exception handled)
    ]
    # Do not raise block_on_severe so we can inspect report
    report = check_data_quality(
        records, expected_symbol="EURUSD", timeframe="M1", block_on_severe=False
    )
    assert report.status == "failed"
    assert report.metrics["duplicate_timestamps"] == 1
    # Check that report.to_dict() returns dictionary representation
    report_dict = report.to_dict()
    assert report_dict["symbol"] == "EURUSD"
    assert report_dict["status"] == "failed"
    assert report_dict["history_quality"] < 100.0


def test_data_quality_missing_timestamp() -> None:
    """Test data quality checks handle records with missing timestamp key."""
    records = [
        {
            "symbol": "EURUSD",
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.10,
            "volume": 10,
        },
        {
            "timestamp": "2026-06-17T10:00:00Z",
            "symbol": "EURUSD",
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.10,
            "volume": 10,
        },
    ]
    report = check_data_quality(
        records, expected_symbol="EURUSD", timeframe="M1", block_on_severe=False
    )
    assert report.status == "passed"
