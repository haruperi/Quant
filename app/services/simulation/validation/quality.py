# ruff: noqa
"""Data quality validation gates and history quality calculator for Simulation.

This module provides sanity checks for symbol data feeds, identifying columns integrity,
inverted prices, duplicate/non-monotonic timestamps, and calculating MT5-style quality scores.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, cast

from app.utils.errors import SimulationError
from app.utils.standard import DataQualityIssue, validate_ohlcv_records


class DataQualityReport:
    """Consolidated representation of dataset validation checks and history quality."""

    def __init__(
        self,
        symbol: str,
        status: str,
        issues: list[DataQualityIssue],
        history_quality: float,
        metrics: dict[str, Any],
    ) -> None:
        """Initialize data quality report details."""
        self.symbol = symbol
        self.status = status
        self.issues = issues
        self.history_quality = history_quality
        self.metrics = metrics

    def to_dict(self) -> dict[str, Any]:
        """Convert report to standard serializable dictionary."""
        return {
            "symbol": self.symbol,
            "status": self.status,
            "issues": self.issues,
            "history_quality": self.history_quality,
            "metrics": self.metrics,
        }


def check_data_quality(
    records: list[dict[str, Any]] | list[Mapping[str, Any]],
    expected_symbol: str,
    timeframe: str,
    data_kind: str = "ohlcv",
    block_on_severe: bool = True,
    diagnostic_mode: bool = False,
) -> DataQualityReport:
    """Run data quality verification gates on input records.

    Verifies presence of mandatory columns, timestamp monotonicity, non-negative spreads,
    OHLC bounds correctness, and scores history quality.

    Raises:
        SimulationError: If block_on_severe is True, diagnostic_mode is False, and severe issues exist.
    """
    if not records:
        empty_issue: DataQualityIssue = {
            "code": "SIM_DATA_EMPTY",
            "severity": "error",
            "message": "The queried dataset is empty.",
            "column": None,
            "row_count": 0,
            "samples": [],
        }
        if block_on_severe and not diagnostic_mode:
            raise SimulationError(
                "Cannot run backtest on empty data.", code="SIM_DATA_EMPTY"
            )
        return DataQualityReport(
            symbol=expected_symbol,
            status="failed",
            issues=[empty_issue],
            history_quality=0.0,
            metrics={"total_rows": 0, "error_rows": 0},
        )

    # Use standard library validation
    ohlcv_records = [dict(dict(r).items()) for r in records]
    issues = validate_ohlcv_records(
        cast("list[Mapping[str, object]]", ohlcv_records),
        expected_symbol=expected_symbol,
    )

    # Extra checks: duplicates and non-monotonic timestamps
    last_time = None
    duplicate_count = 0
    non_monotonic_count = 0
    missing_columns_count = 0

    for idx, r in enumerate(ohlcv_records):
        ts_str = r.get("timestamp")
        if not ts_str:
            continue
        try:
            curr_time = datetime.fromisoformat(str(ts_str))
            if last_time is not None:
                if curr_time == last_time:
                    duplicate_count += 1
                    issues.append(
                        {
                            "code": "SIM_DATA_DUPLICATE_TIMESTAMP",
                            "severity": "error",
                            "message": f"Duplicate timestamp {ts_str} at row {idx}.",
                            "column": "timestamp",
                            "row_count": 1,
                            "samples": [r],
                        }
                    )
                elif curr_time < last_time:
                    non_monotonic_count += 1
                    issues.append(
                        {
                            "code": "SIM_DATA_NON_MONOTONIC_TIME",
                            "severity": "error",
                            "message": f"Non-monotonic timestamp {ts_str} (went backwards) at row {idx}.",
                            "column": "timestamp",
                            "row_count": 1,
                            "samples": [r],
                        }
                    )
            last_time = curr_time
        except Exception:
            pass

    # Evaluate severity
    has_severe = any(issue["severity"] in {"error", "critical"} for issue in issues)
    status = "failed" if has_severe else "passed"

    # Calculate MT5-style history quality (percentage of rows without issues)
    total_rows = len(ohlcv_records)
    error_rows = sum(
        len(issue["samples"])
        for issue in issues
        if issue["severity"] in {"error", "critical"}
    )
    history_quality = max(0.0, min(100.0, (1.0 - (error_rows / total_rows)) * 100.0))

    metrics = {
        "total_rows": total_rows,
        "error_rows": error_rows,
        "duplicate_timestamps": duplicate_count,
        "non_monotonic_timestamps": non_monotonic_count,
        "missing_columns": missing_columns_count,
    }

    if has_severe and block_on_severe and not diagnostic_mode:
        msg = f"Severe data quality errors found for symbol {expected_symbol}. Blocked promotion-realistic run."
        raise SimulationError(
            msg,
            code="SIM_DATA_QUALITY_FAILED",
        )

    return DataQualityReport(
        symbol=expected_symbol,
        status=status,
        issues=issues,
        history_quality=history_quality,
        metrics=metrics,
    )
