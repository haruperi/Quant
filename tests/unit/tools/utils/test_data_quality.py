"""Unit tests for OHLCV quality helpers."""

from tools.utils import (
    data_quality,
    dataframe_tools,
    inspect_ohlcv_quality,
    prepare_ohlcv_data,
    validate_ohlcv_quality,
)

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
