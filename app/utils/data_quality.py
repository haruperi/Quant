"""Data-quality validation helpers for utility-layer diagnostics.

This module validates OHLCV-like tabular inputs and returns bounded,
deterministic diagnostics. It never repairs, resamples, enriches, persists, or
fetches market data; those workflows belong to the data domain.
"""
# ruff: noqa: ANN401

from __future__ import annotations

import math
import time
from typing import Any, Literal, TypedDict

from app.utils.dataframe_tools import OHLCV_COLUMNS, _pandas, dataframe_columns
from app.utils.errors import ValidationError
from app.utils.logger import logger
from app.utils.normalization import normalize_timestamp_sequence
from app.utils.standard import (
    StandardResponse,
    build_metadata,
    error_response,
    response_from_exception,
    success_response,
)

TOOL_NAME = "validate_ohlcv_quality"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL: Literal["low"] = "low"
REQUIRES_APPROVAL = False
READS = False
WRITES = False
UPDATES = False
DELETES = False
TRADES = False
REQUIRES_NETWORK = False

IssueSeverity = Literal["info", "warning", "error", "critical"]


class QualityIssue(TypedDict):
    """Bounded data-quality issue returned by OHLCV validation."""

    code: str
    severity: IssueSeverity
    message: str
    column: str | None
    row_count: int
    sample: list[dict[str, object]]


class QualityProfile(TypedDict):
    """Summary counters for a validated OHLCV dataset."""

    rows: int
    columns: list[str]
    has_timestamp: bool
    has_symbol: bool
    issue_count: int
    critical_count: int
    error_count: int
    warning_count: int


def _add_issue(  # noqa: PLR0913
    issues: list[QualityIssue],
    *,
    code: str,
    severity: IssueSeverity,
    message: str,
    column: str | None,
    row_index: int | None,
    value: object,
    issue_limit: int,
    sample_limit: int,
) -> None:
    """Append or update an issue group with bounded samples."""
    for issue in issues:
        if issue["code"] == code and issue["column"] == column:
            issue["row_count"] += 1
            if len(issue["sample"]) < sample_limit:
                issue["sample"].append({"row_index": row_index, "value": value})
            return
    if len(issues) >= issue_limit:
        return
    issues.append(
        {
            "code": code,
            "severity": severity,
            "message": message,
            "column": column,
            "row_count": 1,
            "sample": [{"row_index": row_index, "value": value}],
        },
    )


def _numeric_value(value: object) -> float | None:
    """Return a finite float candidate or ``None`` for non-numeric values."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def prepare_ohlcv_data(dataframe: Any, *, timestamp_column: str | None = None) -> Any:
    """Return a copy of an OHLCV dataframe with UTC timestamp normalization.

    Args:
        dataframe: pandas ``DataFrame``-like object.
        timestamp_column: Optional timestamp column to normalize.

    Returns:
        A copied dataframe with a normalized timestamp column or index.

    Raises:
        ValidationError: If input is not a pandas dataframe or timestamps fail.
    """
    pd = _pandas()
    if not isinstance(dataframe, pd.DataFrame):
        raise ValidationError("dataframe must be a pandas DataFrame.")
    prepared = dataframe.copy(deep=True)
    column = timestamp_column
    if column is None and "timestamp" in prepared.columns:
        column = "timestamp"
    if column is not None:
        if column not in prepared.columns:
            message = f"{column} timestamp column is missing."
            raise ValidationError(message)
        prepared[column] = normalize_timestamp_sequence(prepared[column])
    elif not prepared.index.empty:
        prepared.index = pd.DatetimeIndex(
            list(normalize_timestamp_sequence(prepared.index)),
        )
    return prepared


def inspect_ohlcv_quality(  # noqa: C901, PLR0912
    dataframe: Any,
    *,
    expected_symbol: str | None = None,
    timestamp_column: str | None = None,
    issue_limit: int = 100,
    sample_limit: int = 5,
) -> dict[str, object]:
    """Inspect OHLCV data and return deterministic quality diagnostics.

    Args:
        dataframe: pandas ``DataFrame``-like object.
        expected_symbol: Optional symbol expected in a ``symbol`` column.
        timestamp_column: Optional timestamp column name.
        issue_limit: Maximum issue groups to return.
        sample_limit: Maximum samples per issue group.

    Returns:
        Mapping with pass flag, score, issue list, profile, and remediation.

    Raises:
        ValidationError: If limits or dataframe input are invalid.
    """
    if issue_limit <= 0:
        raise ValidationError("issue_limit must be greater than zero.")
    if sample_limit < 0:
        raise ValidationError("sample_limit must be non-negative.")

    pd = _pandas()
    if not isinstance(dataframe, pd.DataFrame):
        raise ValidationError("dataframe must be a pandas DataFrame.")

    frame = dataframe.copy(deep=False)
    columns = dataframe_columns(frame)
    issues: list[QualityIssue] = []
    rows = len(frame)

    for column in OHLCV_COLUMNS:
        if column not in columns:
            _add_issue(
                issues,
                code="MISSING_COLUMN",
                severity="critical",
                message="Required OHLCV column is missing.",
                column=column,
                row_index=None,
                value=column,
                issue_limit=issue_limit,
                sample_limit=sample_limit,
            )

    if rows == 0:
        _add_issue(
            issues,
            code="EMPTY_DATASET",
            severity="error",
            message="OHLCV dataset is empty.",
            column=None,
            row_index=None,
            value="empty",
            issue_limit=issue_limit,
            sample_limit=sample_limit,
        )

    timestamp_name = timestamp_column or (
        "timestamp" if "timestamp" in columns else None
    )
    if timestamp_name is not None and timestamp_name in columns:
        sequence = normalize_timestamp_sequence(frame[timestamp_name])
        timestamps = list(sequence)
        if len(set(timestamps)) != len(timestamps):
            _add_issue(
                issues,
                code="DUPLICATE_TIMESTAMP",
                severity="error",
                message="Duplicate timestamps were detected.",
                column=timestamp_name,
                row_index=None,
                value="duplicate",
                issue_limit=issue_limit,
                sample_limit=sample_limit,
            )
        if timestamps != sorted(timestamps):
            _add_issue(
                issues,
                code="NON_MONOTONIC_TIMESTAMP",
                severity="error",
                message="Timestamps must be sorted ascending.",
                column=timestamp_name,
                row_index=None,
                value="non_monotonic",
                issue_limit=issue_limit,
                sample_limit=sample_limit,
            )

    expected = expected_symbol.strip() if expected_symbol else None
    for row_index, row in enumerate(frame.to_dict(orient="records")):
        if expected and "symbol" in row and row.get("symbol") != expected:
            _add_issue(
                issues,
                code="SYMBOL_MISMATCH",
                severity="warning",
                message="Row symbol differs from expected symbol.",
                column="symbol",
                row_index=row_index,
                value=row.get("symbol"),
                issue_limit=issue_limit,
                sample_limit=sample_limit,
            )
        numeric: dict[str, float] = {}
        for column in ("open", "high", "low", "close", "volume"):
            if column not in row:
                continue
            value = _numeric_value(row[column])
            if value is None or math.isnan(value) or math.isinf(value):
                _add_issue(
                    issues,
                    code="NON_FINITE_NUMERIC_VALUE",
                    severity="critical",
                    message="OHLCV numeric values must be finite numbers.",
                    column=column,
                    row_index=row_index,
                    value=row[column],
                    issue_limit=issue_limit,
                    sample_limit=sample_limit,
                )
                continue
            numeric[column] = value
            if column != "volume" and value <= 0:
                _add_issue(
                    issues,
                    code="NON_POSITIVE_PRICE",
                    severity="critical",
                    message="OHLC prices must be positive.",
                    column=column,
                    row_index=row_index,
                    value=value,
                    issue_limit=issue_limit,
                    sample_limit=sample_limit,
                )
            if column == "volume" and value < 0:
                _add_issue(
                    issues,
                    code="NEGATIVE_VOLUME",
                    severity="error",
                    message="Volume must not be negative.",
                    column=column,
                    row_index=row_index,
                    value=value,
                    issue_limit=issue_limit,
                    sample_limit=sample_limit,
                )
        if {"low", "high"} <= numeric.keys() and numeric["low"] > numeric["high"]:
            _add_issue(
                issues,
                code="LOW_ABOVE_HIGH",
                severity="critical",
                message="Low price must not be greater than high price.",
                column="low",
                row_index=row_index,
                value={"low": numeric["low"], "high": numeric["high"]},
                issue_limit=issue_limit,
                sample_limit=sample_limit,
            )
        if {"open", "high", "low", "close"} <= numeric.keys():
            for column in ("open", "close"):
                if (
                    numeric[column] < numeric["low"]
                    or numeric[column] > numeric["high"]
                ):
                    _add_issue(
                        issues,
                        code="OHLC_OUTSIDE_RANGE",
                        severity="critical",
                        message="Open/close price must be inside high/low range.",
                        column=column,
                        row_index=row_index,
                        value=numeric[column],
                        issue_limit=issue_limit,
                        sample_limit=sample_limit,
                    )

    critical = sum(1 for issue in issues if issue["severity"] == "critical")
    errors = sum(1 for issue in issues if issue["severity"] == "error")
    warnings = sum(1 for issue in issues if issue["severity"] == "warning")
    penalty = critical * 25 + errors * 10 + warnings * 3
    score = max(0, 100 - penalty)
    profile: QualityProfile = {
        "rows": rows,
        "columns": columns,
        "has_timestamp": timestamp_name in columns if timestamp_name else False,
        "has_symbol": "symbol" in columns,
        "issue_count": len(issues),
        "critical_count": critical,
        "error_count": errors,
        "warning_count": warnings,
    }
    return {
        "passed": critical == 0 and errors == 0,
        "quality_score": score,
        "severity": "critical"
        if critical
        else "error"
        if errors
        else "warning"
        if warnings
        else "info",
        "issues": issues,
        "profile": profile,
        "remediation": [
            "Reject or review rows with critical OHLCV diagnostics.",
            "Repair/resample only in the tools.data domain.",
        ],
    }


def validate_ohlcv_quality(
    dataframe: Any,
    *,
    expected_symbol: str | None = None,
    timestamp_column: str | None = None,
    request_id: str | None = None,
) -> StandardResponse:
    """Official tool wrapper for OHLCV quality inspection.

    Args:
        dataframe: pandas ``DataFrame``-like object.
        expected_symbol: Optional expected symbol value.
        timestamp_column: Optional timestamp column.
        request_id: Optional trace request identifier.

    Returns:
        Standard HaruQuant tool response envelope.
    """
    start = time.perf_counter()
    metadata = build_metadata(
        tool_name=TOOL_NAME,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=TOOL_RISK_LEVEL,
        request_id=request_id,
        reads=READS,
        writes=WRITES,
        updates=UPDATES,
        deletes=DELETES,
        trades=TRADES,
        requires_network=REQUIRES_NETWORK,
        start_time=start,
    )
    logger.info(
        "ohlcv quality validation called",
        extra={"event_name": "tool_called", "request_id": request_id},
    )
    try:
        result = inspect_ohlcv_quality(
            dataframe,
            expected_symbol=expected_symbol,
            timestamp_column=timestamp_column,
        )
        logger.info(
            "ohlcv quality validation completed",
            extra={"event_name": "tool_success", "request_id": request_id},
        )
        return success_response(
            message="OHLCV quality validation completed.",
            data=result,
            metadata=build_metadata(
                tool_name=TOOL_NAME,
                tool_version=TOOL_VERSION,
                tool_category=TOOL_CATEGORY,
                tool_risk_level=TOOL_RISK_LEVEL,
                request_id=request_id,
                reads=READS,
                writes=WRITES,
                updates=UPDATES,
                deletes=DELETES,
                trades=TRADES,
                requires_network=REQUIRES_NETWORK,
                start_time=start,
            ),
        )
    except ValidationError as exc:
        logger.warning(
            "ohlcv quality validation rejected input",
            extra={"event_name": "tool_validation_failed", "request_id": request_id},
        )
        return error_response(
            message="OHLCV quality validation failed.",
            code=exc.code,
            details=str(exc),
            metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "ohlcv quality validation raised exception",
            extra={"event_name": "tool_exception", "request_id": request_id},
        )
        return response_from_exception(
            exception=exc,
            metadata=metadata,
            message="OHLCV quality validation failed.",
        )
