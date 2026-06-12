"""Unit tests for OHLCV quality helpers."""

import math
from typing import cast

import pytest
from tools.utils import (
    data_quality,
    dataframe_tools,
    inspect_ohlcv_quality,
    prepare_ohlcv_data,
    validate_ohlcv_quality,
)
from tools.utils.errors import ValidationError

from tests.unit.tools.utils.test_dataframe_tools import FakeDataFrame, FakePandas


def _patch_pandas() -> None:
    """Patch data-quality helpers to use the fake pandas module."""
    data_quality._pandas = lambda: FakePandas  # type: ignore[attr-defined]
    dataframe_tools._pandas = lambda: FakePandas


def test_inspect_ohlcv_quality_reports_failures() -> None:
    """Invalid OHLCV rows produce bounded deterministic diagnostics."""
    _patch_pandas()
    frame = FakeDataFrame(
        [
            {
                "timestamp": "2026-06-11T10:00:00Z",
                "symbol": "EURUSD",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.1,
                "volume": 10,
            },
            {
                "timestamp": "2026-06-11T10:00:00Z",
                "symbol": "GBPUSD",
                "open": -1.0,
                "high": 0.9,
                "low": 1.0,
                "close": 0.8,
                "volume": -1,
            },
        ],
    )
    result = inspect_ohlcv_quality(frame, expected_symbol="EURUSD")

    issues = result["issues"]
    assert isinstance(issues, list)
    codes = {issue["code"] for issue in issues}
    assert result["passed"] is False
    assert "DUPLICATE_TIMESTAMP" in codes
    assert "SYMBOL_MISMATCH" in codes
    assert "LOW_ABOVE_HIGH" in codes


def test_validate_ohlcv_quality_returns_standard_response() -> None:
    """Official quality tool returns a standard success envelope."""
    _patch_pandas()
    frame = FakeDataFrame(
        [
            {
                "timestamp": "2026-06-11T10:00:00Z",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "volume": 100,
            },
        ],
    )
    prepared = prepare_ohlcv_data(frame)
    response = validate_ohlcv_quality(prepared, request_id="req_quality_123")

    assert response["status"] == "success"
    assert response["metadata"]["tool_name"] == "validate_ohlcv_quality"
    assert response["data"] is not None


def test_prepare_ohlcv_data_normalizes_index_and_rejects_bad_inputs() -> None:
    """Preparation supports timestamp index fallback and rejects invalid inputs."""
    _patch_pandas()
    frame = FakeDataFrame(
        [{"open": 1.1, "high": 1.2, "low": 1.0, "close": 1.1, "volume": 1}],
    )
    frame.index = FakePandas.DatetimeIndex(["2026-06-11T10:00:00Z"])

    prepared = prepare_ohlcv_data(frame)

    assert prepared is not frame
    assert prepared.index[0].isoformat().startswith("2026-06-11T10:00:00")
    with pytest.raises(ValidationError, match="DataFrame"):
        prepare_ohlcv_data(object())
    with pytest.raises(ValidationError, match="timestamp column is missing"):
        prepare_ohlcv_data(frame, timestamp_column="timestamp")


def test_inspect_ohlcv_quality_reports_empty_missing_and_non_monotonic_cases() -> None:
    """Quality inspection reports missing, empty, and unsorted timestamp cases."""
    _patch_pandas()
    empty = FakeDataFrame([])
    unsorted = FakeDataFrame(
        [
            {
                "timestamp": "2026-06-11T10:01:00Z",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.1,
                "volume": 1,
            },
            {
                "timestamp": "2026-06-11T10:00:00Z",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.1,
                "volume": 1,
            },
        ],
    )

    empty_result = inspect_ohlcv_quality(empty, issue_limit=10)
    unsorted_result = inspect_ohlcv_quality(unsorted)

    empty_issues = cast("list[dict[str, object]]", empty_result["issues"])
    unsorted_issues = cast("list[dict[str, object]]", unsorted_result["issues"])

    assert {issue["code"] for issue in empty_issues} == {
        "MISSING_COLUMN",
        "EMPTY_DATASET",
    }
    assert "NON_MONOTONIC_TIMESTAMP" in {issue["code"] for issue in unsorted_issues}


def test_inspect_ohlcv_quality_rejects_invalid_limits_and_dataframe() -> None:
    """Quality inspection validates dataframe type and issue/sample limits first."""
    _patch_pandas()
    frame = FakeDataFrame([])

    with pytest.raises(ValidationError, match="issue_limit"):
        inspect_ohlcv_quality(frame, issue_limit=0)
    with pytest.raises(ValidationError, match="sample_limit"):
        inspect_ohlcv_quality(frame, sample_limit=-1)
    with pytest.raises(ValidationError, match="DataFrame"):
        inspect_ohlcv_quality(object())


def test_inspect_ohlcv_quality_reports_nonfinite_and_range_cases() -> None:
    """Quality diagnostics include non-finite, non-positive, and range issues."""
    _patch_pandas()
    frame = FakeDataFrame(
        [
            {
                "timestamp": "2026-06-11T10:00:00Z",
                "open": math.nan,
                "high": 1.0,
                "low": 0.5,
                "close": 1.2,
                "volume": math.inf,
            },
            {
                "timestamp": "2026-06-11T10:01:00Z",
                "open": 0,
                "high": 1.0,
                "low": 0.5,
                "close": 0.4,
                "volume": -1,
            },
        ],
    )

    result = inspect_ohlcv_quality(frame)
    issues = cast("list[dict[str, object]]", result["issues"])
    codes = {issue["code"] for issue in issues}

    assert "NON_FINITE_NUMERIC_VALUE" in codes
    assert "NON_POSITIVE_PRICE" in codes
    assert "NEGATIVE_VOLUME" in codes
    assert "OHLC_OUTSIDE_RANGE" in codes


def test_validate_ohlcv_quality_returns_error_envelope_for_bad_input() -> None:
    """The official quality wrapper converts invalid inputs into standard errors."""
    _patch_pandas()

    response = validate_ohlcv_quality(object(), request_id="req_bad_quality")

    assert response["status"] == "error"
    assert response["error"] is not None
    assert response["error"]["code"] == "VALIDATION_FAILED"
    assert response["metadata"]["request_id"] == "req_bad_quality"
