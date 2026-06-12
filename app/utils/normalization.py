"""UTC-first timestamp normalization helpers for HaruQuant utilities.

This module provides support helpers, not official AI tools. It exports
datetime parsing, UTC conversion, ISO ``Z`` formatting, deterministic stale
checks, and timestamp sequence diagnostics for event, notification, health, and
data freshness workflows.

Public exports:
    DEFAULT_TIMEZONE, UTC, TimestampIssue, ClockDriftStatus, parse_datetime,
    normalize_timestamp, normalize_timestamp_sequence, normalize_timestamp_column,
    to_utc_datetime, to_naive_utc, format_utc_timestamp, utc_now, is_stale,
    validate_timestamp_sequence, check_clock_drift.

Side effects:
    None. Importing this module does not configure logging, read files, call
    networks, import optional dependencies, or use the local machine timezone.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC as DATETIME_UTC
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from typing import Literal, NoReturn, TypedDict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.utils.errors import ValidationError
from app.utils.logger import logger

DEFAULT_TIMEZONE = "UTC"
UTC = DATETIME_UTC
FALLBACK_TIMEZONES: dict[str, tzinfo] = {
    "Africa/Cairo": timezone(timedelta(hours=3), name="Africa/Cairo"),
}
TimestampIssueCode = Literal[
    "INVALID_TIMESTAMP",
    "NON_MONOTONIC_TIMESTAMP",
    "DUPLICATE_TIMESTAMP",
]


class TimestampIssue(TypedDict):
    """Timestamp sequence diagnostic issue."""

    code: TimestampIssueCode
    message: str
    index: int
    timestamp: str | None


class ClockDriftStatus(TypedDict):
    """Clock drift diagnostic status."""

    drift_detected: bool
    drift_seconds: float
    max_drift_seconds: float
    checked_at: str


def _raise_validation(message: str, *, field_name: str) -> NoReturn:
    """Log and raise a deterministic validation error."""
    logger.warning(
        "timestamp normalization validation failed",
        extra={
            "event_name": "timestamp_normalization_validation_failed",
            "field_name": field_name,
            "error_code": "INVALID_INPUT",
        },
    )
    raise ValidationError(message, code="INVALID_INPUT")


def _timezone_from(value: str | tzinfo) -> tzinfo:
    """Resolve a timezone name or tzinfo object without using local time."""
    if isinstance(value, tzinfo):
        return value
    if not isinstance(value, str) or not value.strip():
        _raise_validation(
            "assumed_timezone must be a non-empty timezone name.",
            field_name="assumed_timezone",
        )
    name = value.strip()
    if name.upper() == DEFAULT_TIMEZONE:
        return UTC
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        if name in FALLBACK_TIMEZONES:
            return FALLBACK_TIMEZONES[name]
        message = f"unknown timezone: {name}"
        raise ValidationError(message, code="INVALID_INPUT") from exc


def _parse_iso_string(value: str) -> datetime:
    """Parse an ISO datetime string with deterministic UTC ``Z`` support."""
    candidate = value.strip()
    if not candidate:
        _raise_validation("datetime string must be non-empty.", field_name="value")
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        message = f"datetime string is not ISO-8601 parseable: {value}"
        raise ValidationError(message, code="INVALID_INPUT") from exc
    return parsed


def parse_datetime(
    value: datetime | date | str | float,
    *,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
) -> datetime:
    """Parse a datetime-like value into a UTC-aware ``datetime``.

    Args:
        value: A ``datetime``, ``date``, ISO string, or epoch seconds value.
        assumed_timezone: Explicit timezone used only for naive datetime values.

    Returns:
        UTC-aware datetime.

    Raises:
        ValidationError: If the input is not datetime-like or cannot be parsed.

    Side effects:
        None.
    """
    timezone_assumption = _timezone_from(assumed_timezone)
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min)
    elif isinstance(value, str):
        parsed = _parse_iso_string(value)
    elif isinstance(value, int | float):
        try:
            parsed = datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, OSError, ValueError) as exc:
            message = f"epoch timestamp is invalid: {value}"
            raise ValidationError(message, code="INVALID_INPUT") from exc
    else:
        _raise_validation(
            "value must be a datetime, date, ISO string, or epoch seconds.",
            field_name="value",
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone_assumption)
    return parsed.astimezone(UTC)


def normalize_timestamp(
    value: datetime | date | str | float,
    *,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
) -> datetime:
    """Normalize a datetime-like value to a UTC-aware ``datetime``.

    Args:
        value: Datetime-like value to normalize.
        assumed_timezone: Explicit timezone used for naive inputs.

    Returns:
        UTC-aware datetime.

    Side effects:
        None.
    """
    return parse_datetime(value, assumed_timezone=assumed_timezone)


def to_utc_datetime(
    value: datetime | date | str | float,
    *,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
) -> datetime:
    """Convert a datetime-like value to a UTC-aware ``datetime``."""
    return normalize_timestamp(value, assumed_timezone=assumed_timezone)


def to_naive_utc(
    value: datetime | date | str | float,
    *,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
) -> datetime:
    """Convert a datetime-like value to a timezone-free UTC ``datetime``."""
    return normalize_timestamp(value, assumed_timezone=assumed_timezone).replace(
        tzinfo=None,
    )


def format_utc_timestamp(
    value: datetime | date | str | float,
    *,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
    timespec: Literal["auto", "hours", "minutes", "seconds", "milliseconds"] = (
        "seconds"
    ),
) -> str:
    """Format a datetime-like value as a UTC ISO string ending in ``Z``.

    Args:
        value: Datetime-like value to format.
        assumed_timezone: Explicit timezone used for naive inputs.
        timespec: ISO formatting precision.

    Returns:
        UTC ISO timestamp ending in ``Z``.

    Side effects:
        None.
    """
    normalized = normalize_timestamp(value, assumed_timezone=assumed_timezone)
    return normalized.isoformat(timespec=timespec).replace("+00:00", "Z")


def utc_now() -> datetime:
    """Return the current wall-clock time as a UTC-aware datetime."""
    return datetime.now(UTC)


def is_stale(
    timestamp: datetime | date | str | float,
    *,
    max_age_seconds: float,
    now: datetime | date | str | float | None = None,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
) -> bool:
    """Return whether a timestamp is older than a deterministic max age.

    Args:
        timestamp: Datetime-like value to evaluate.
        max_age_seconds: Maximum accepted age in seconds.
        now: Optional injected current time. If omitted, UTC wall-clock time is
            used.
        assumed_timezone: Explicit timezone used for naive inputs.

    Returns:
        ``True`` when the timestamp is stale.

    Raises:
        ValidationError: If ``max_age_seconds`` is negative.

    Side effects:
        None.
    """
    if max_age_seconds < 0:
        _raise_validation(
            "max_age_seconds must be greater than or equal to zero.",
            field_name="max_age_seconds",
        )
    current = (
        utc_now()
        if now is None
        else normalize_timestamp(
            now,
            assumed_timezone=assumed_timezone,
        )
    )
    observed = normalize_timestamp(timestamp, assumed_timezone=assumed_timezone)
    return (current - observed).total_seconds() > max_age_seconds


def normalize_timestamp_sequence(
    values: Iterable[datetime | date | str | int | float],
    *,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
) -> list[datetime]:
    """Normalize a sequence of datetime-like values to UTC-aware datetimes."""
    return [
        normalize_timestamp(value, assumed_timezone=assumed_timezone)
        for value in values
    ]


def normalize_timestamp_column(
    rows: Iterable[Mapping[str, object]],
    *,
    column: str,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
    output_column: str | None = None,
) -> list[dict[str, object]]:
    """Normalize timestamp values inside row mappings.

    Args:
        rows: Iterable of row-like mappings.
        column: Source timestamp column.
        assumed_timezone: Explicit timezone used for naive timestamp values.
        output_column: Optional destination column. Defaults to ``column``.

    Returns:
        New row dictionaries with UTC-aware datetime values.

    Raises:
        ValidationError: If the column name is empty, missing, or unparseable.

    Side effects:
        None. Input mappings are not mutated.
    """
    if not isinstance(column, str) or not column.strip():
        _raise_validation("column must be a non-empty string.", field_name="column")
    target_column = column if output_column is None else output_column
    if not isinstance(target_column, str) or not target_column.strip():
        _raise_validation(
            "output_column must be a non-empty string.",
            field_name="output_column",
        )

    normalized_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        if column not in row:
            message = f"timestamp column is missing at index {index}: {column}"
            raise ValidationError(message, code="INVALID_INPUT")
        normalized = dict(row)
        raw_value = row[column]
        if not isinstance(raw_value, datetime | date | str | int | float):
            _raise_validation(
                "timestamp column value must be datetime-like.",
                field_name=column,
            )
        normalized[target_column] = normalize_timestamp(
            raw_value,
            assumed_timezone=assumed_timezone,
        )
        normalized_rows.append(normalized)
    return normalized_rows


def validate_timestamp_sequence(
    values: Iterable[datetime | date | str | int | float],
    *,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
    allow_duplicates: bool = False,
) -> list[TimestampIssue]:
    """Return deterministic diagnostics for timestamp ordering issues.

    Args:
        values: Timestamp values to validate in order.
        assumed_timezone: Explicit timezone used for naive timestamp values.
        allow_duplicates: Whether duplicate adjacent timestamps are permitted.

    Returns:
        List of timestamp diagnostics for invalid, duplicate, or non-monotonic
        values.

    Side effects:
        None.
    """
    issues: list[TimestampIssue] = []
    previous: datetime | None = None
    for index, value in enumerate(values):
        try:
            current = normalize_timestamp(value, assumed_timezone=assumed_timezone)
        except ValidationError:
            issues.append(
                {
                    "code": "INVALID_TIMESTAMP",
                    "message": "Timestamp could not be normalized.",
                    "index": index,
                    "timestamp": None,
                },
            )
            continue
        formatted = format_utc_timestamp(current)
        if previous is not None:
            if current < previous:
                issues.append(
                    {
                        "code": "NON_MONOTONIC_TIMESTAMP",
                        "message": "Timestamp is earlier than the previous value.",
                        "index": index,
                        "timestamp": formatted,
                    },
                )
            if current == previous and not allow_duplicates:
                issues.append(
                    {
                        "code": "DUPLICATE_TIMESTAMP",
                        "message": "Timestamp duplicates the previous value.",
                        "index": index,
                        "timestamp": formatted,
                    },
                )
        previous = current
    return issues


def check_clock_drift(
    observed_at: datetime | date | str | float,
    *,
    now: datetime | date | str | float | None = None,
    max_drift_seconds: float = 5.0,
    assumed_timezone: str | tzinfo = DEFAULT_TIMEZONE,
) -> ClockDriftStatus:
    """Return a UTC clock-drift diagnostic status.

    Args:
        observed_at: Timestamp from a remote system or workflow event.
        now: Optional injected local UTC time for deterministic tests.
        max_drift_seconds: Absolute drift threshold in seconds.
        assumed_timezone: Explicit timezone used for naive inputs.

    Returns:
        Clock drift status with checked-at timestamp.

    Raises:
        ValidationError: If ``max_drift_seconds`` is negative.

    Side effects:
        None.
    """
    if max_drift_seconds < 0:
        _raise_validation(
            "max_drift_seconds must be greater than or equal to zero.",
            field_name="max_drift_seconds",
        )
    current = (
        utc_now()
        if now is None
        else normalize_timestamp(
            now,
            assumed_timezone=assumed_timezone,
        )
    )
    observed = normalize_timestamp(observed_at, assumed_timezone=assumed_timezone)
    drift_seconds = abs((current - observed).total_seconds())
    return {
        "drift_detected": drift_seconds > max_drift_seconds,
        "drift_seconds": round(drift_seconds, 6),
        "max_drift_seconds": float(max_drift_seconds),
        "checked_at": format_utc_timestamp(current),
    }
