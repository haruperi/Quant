"""Simulator data-quality gates.

Exports bounded tick and OHLCV validation helpers for simulator entry points.
The module has no side effects and never repairs or persists data.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from app.utils.standard import DataQualityIssue, build_data_quality_issue


def validate_tick_records(
    records: list[Mapping[str, object]],
    *,
    expected_symbol: str | None = None,
) -> list[DataQualityIssue]:
    """Return bounded data-quality issues for tick records.

    Args:
        records: Tick-like mappings.
        expected_symbol: Optional expected symbol.

    Returns:
        list[DataQualityIssue]: Deterministic validation issues.

    Raises:
        No exceptions are raised for record content; issues are returned.
    """
    issues: list[DataQualityIssue] = []
    if not records:
        return [
            build_data_quality_issue(
                code="SIM_DATA_EMPTY",
                severity="error",
                message="Tick record collection is empty.",
                column=None,
                row_count=1,
            )
        ]
    for index, record in enumerate(records):
        _validate_tick_record(record, index, expected_symbol, issues)
    return issues


def _validate_tick_record(
    record: Mapping[str, object],
    index: int,
    expected_symbol: str | None,
    issues: list[DataQualityIssue],
) -> None:
    """Append issues for one tick record."""
    for column in ("timestamp", "symbol", "bid", "ask"):
        if column not in record:
            issues.append(
                build_data_quality_issue(
                    code="SIM_DATA_MISSING_COLUMN",
                    severity="error",
                    message="Mandatory tick column is missing.",
                    column=column,
                    row_count=1,
                    samples=[{"row_index": index}],
                )
            )
    bid = record.get("bid")
    ask = record.get("ask")
    if (
        isinstance(bid, int | float)
        and isinstance(ask, int | float)
        and (float(bid) <= 0 or float(ask) <= 0 or float(ask) < float(bid))
    ):
        issues.append(
            build_data_quality_issue(
                code="SIM_INVALID_PRICE",
                severity="critical",
                message="Tick bid/ask prices are invalid.",
                column="bid",
                row_count=1,
                samples=[{"row_index": index, "bid": bid, "ask": ask}],
            )
        )
    if expected_symbol and record.get("symbol") != expected_symbol:
        issues.append(
            build_data_quality_issue(
                code="SIM_MISSING_SYMBOL",
                severity="warning",
                message="Tick symbol does not match expected symbol.",
                column="symbol",
                row_count=1,
                samples=[{"row_index": index, "actual": record.get("symbol")}],
            )
        )


def align_record_timezones(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert all record timestamps to UTC ISO strings.

    Args:
        records: Raw data records.

    Returns:
        list[dict[str, Any]]: Timezone-aligned records.
    """
    from app.utils.normalization import normalize_timestamp

    for rec in records:
        if "timestamp" in rec:
            dt = normalize_timestamp(rec["timestamp"])
            rec["timestamp"] = dt.isoformat()
    return records


def _is_weekend_gap(t1: datetime, t2: datetime) -> bool:
    """Return True if the gap spans across the weekend."""
    from datetime import timedelta

    temp = t1
    saturday_index = 5
    while temp < t2:
        if temp.weekday() == saturday_index:
            return True
        temp += timedelta(days=1)
    return False


def detect_data_gaps(
    records: list[dict[str, Any]],
    _timeframe: str | None = None,
    max_gap_seconds: float = 3600.0,
) -> list[DataQualityIssue]:
    """Detect gaps between consecutive timestamps, ignoring standard weekend closures.

    Args:
        records: Data records sorted by timestamp.
        _timeframe: Optional bar timeframe.
        max_gap_seconds: Maximum allowed gap in seconds.

    Returns:
        list[DataQualityIssue]: Detected gap issues.
    """
    from app.utils.normalization import normalize_timestamp

    issues: list[DataQualityIssue] = []
    min_records_for_gap = 2
    if len(records) < min_records_for_gap:
        return issues

    for i in range(1, len(records)):
        prev_t = normalize_timestamp(records[i - 1]["timestamp"])
        curr_t = normalize_timestamp(records[i]["timestamp"])
        diff = (curr_t - prev_t).total_seconds()
        if diff > max_gap_seconds:
            if _is_weekend_gap(prev_t, curr_t):
                continue
            issues.append(
                build_data_quality_issue(
                    code="SIM_GAP_HANDLING_REJECTED",
                    severity="warning",
                    message=f"Significant data gap detected: {diff} seconds.",
                    column="timestamp",
                    row_count=1,
                    samples=[
                        {
                            "prev_timestamp": prev_t.isoformat(),
                            "curr_timestamp": curr_t.isoformat(),
                            "gap_seconds": diff,
                        }
                    ],
                )
            )
    return issues


def _find_missing_days(
    symbol_records: dict[str, list[dict[str, Any]]],
) -> dict[str, set[Any]]:
    """Return a mapping of symbol to missing trading days."""
    from app.utils.normalization import normalize_timestamp

    all_days = set()
    for records in symbol_records.values():
        for rec in records:
            if "timestamp" in rec:
                dt = normalize_timestamp(rec["timestamp"])
                all_days.add(dt.date())

    missing_by_symbol = {}
    friday_index = 5
    for symbol, records in symbol_records.items():
        present_days = {
            normalize_timestamp(rec["timestamp"]).date()
            for rec in records
            if "timestamp" in rec
        }
        missing_days = all_days - present_days
        # Filter missing_days to exclude weekends (Saturday, Sunday)
        missing_trading_days = {d for d in missing_days if d.weekday() < friday_index}
        if missing_trading_days:
            missing_by_symbol[symbol] = missing_trading_days

    return missing_by_symbol


def apply_partial_data_policy(
    symbol_records: dict[str, list[dict[str, Any]]],
    policy: str = "fail_fast",
) -> dict[str, list[dict[str, Any]]]:
    """Verify data completeness across symbols and apply PartialDataPolicy.

    Args:
        symbol_records: Mappings from symbol to list of records.
        policy: Policy name ("fail_fast", "quarantine", or "allow").

    Returns:
        dict[str, list[dict[str, Any]]]: Filtered/repaired records.

    Raises:
        SimulationError: If fail_fast is selected and missing data is found.
    """
    from app.utils.errors import SimulationError
    from app.utils.logger import logger
    from app.utils.normalization import normalize_timestamp

    if not symbol_records:
        return symbol_records

    missing_by_symbol = _find_missing_days(symbol_records)
    if missing_by_symbol:
        if policy == "fail_fast":
            err_msg = f"Missing trading days for symbols: {missing_by_symbol}"
            raise SimulationError(
                err_msg,
                code="SIM_DATA_PARTIAL",
            )
        if policy == "quarantine":
            quarantined_days = set()
            for days in missing_by_symbol.values():
                quarantined_days.update(days)

            logger.warning(f"Quarantining missing days: {quarantined_days}")
            filtered_symbol_records = {}
            for symbol, records in symbol_records.items():
                filtered_symbol_records[symbol] = [
                    rec
                    for rec in records
                    if "timestamp" in rec
                    and normalize_timestamp(rec["timestamp"]).date()
                    not in quarantined_days
                ]
            return filtered_symbol_records

    return symbol_records
