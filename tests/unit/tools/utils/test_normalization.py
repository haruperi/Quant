"""Unit tests for tools.utils.normalization."""

from datetime import UTC, date, datetime

import pytest
from tools.utils.errors import ValidationError
from tools.utils.normalization import (
    DEFAULT_TIMEZONE,
    check_clock_drift,
    format_utc_timestamp,
    is_stale,
    normalize_timestamp,
    normalize_timestamp_column,
    normalize_timestamp_sequence,
    parse_datetime,
    to_naive_utc,
    to_utc_datetime,
    validate_timestamp_sequence,
)
from tools.utils.standard import get_execution_ms


def test_default_timezone_is_utc() -> None:
    assert DEFAULT_TIMEZONE == "UTC"


def test_parse_datetime_handles_iso_z_and_offsets_as_utc() -> None:
    assert parse_datetime("2026-06-11T10:30:00Z") == datetime(
        2026,
        6,
        11,
        10,
        30,
        tzinfo=UTC,
    )
    assert parse_datetime("2026-06-11T12:30:00+02:00") == datetime(
        2026,
        6,
        11,
        10,
        30,
        tzinfo=UTC,
    )


def test_naive_datetime_uses_explicit_assumed_timezone() -> None:
    naive = datetime.fromisoformat("2026-06-11T12:00:00")

    normalized = normalize_timestamp(naive, assumed_timezone="Africa/Cairo")

    assert normalized == datetime(2026, 6, 11, 9, 0, tzinfo=UTC)


def test_to_utc_datetime_and_naive_utc_conversion() -> None:
    aware = datetime(2026, 6, 11, 12, 0, tzinfo=UTC)

    assert to_utc_datetime(aware) == aware
    assert to_naive_utc(aware) == aware.replace(tzinfo=None)


def test_format_utc_timestamp_ends_with_z() -> None:
    formatted = format_utc_timestamp("2026-06-11T12:30:00+02:00")

    assert formatted == "2026-06-11T10:30:00Z"


def test_epoch_seconds_and_dates_parse_without_local_timezone() -> None:
    assert parse_datetime(0) == datetime(1970, 1, 1, tzinfo=UTC)
    assert parse_datetime(date(2026, 6, 11)) == datetime(2026, 6, 11, tzinfo=UTC)


def test_unparseable_and_unknown_timezone_inputs_fail_clearly() -> None:
    with pytest.raises(ValidationError, match="ISO-8601"):
        parse_datetime("not-a-date")

    with pytest.raises(ValidationError, match="unknown timezone"):
        parse_datetime("2026-06-11T12:00:00", assumed_timezone="Mars/Base")

    with pytest.raises(ValidationError, match="datetime"):
        parse_datetime(object())  # type: ignore[arg-type]


def test_stale_checks_are_deterministic_with_injected_now() -> None:
    now = datetime(2026, 6, 11, 12, 0, tzinfo=UTC)

    assert is_stale("2026-06-11T11:59:00Z", max_age_seconds=30, now=now)
    assert not is_stale("2026-06-11T11:59:45Z", max_age_seconds=30, now=now)

    with pytest.raises(ValidationError, match="max_age_seconds"):
        is_stale(now, max_age_seconds=-1, now=now)


def test_normalize_timestamp_sequence_returns_utc_datetimes() -> None:
    normalized = normalize_timestamp_sequence(
        ["2026-06-11T12:00:00+02:00", datetime.fromisoformat("2026-06-11T10:01:00")],
    )

    assert normalized == [
        datetime(2026, 6, 11, 10, 0, tzinfo=UTC),
        datetime(2026, 6, 11, 10, 1, tzinfo=UTC),
    ]


def test_validate_timestamp_sequence_reports_duplicate_and_non_monotonic() -> None:
    issues = validate_timestamp_sequence(
        [
            "2026-06-11T10:00:00Z",
            "2026-06-11T10:00:00Z",
            "2026-06-11T09:59:00Z",
            "bad",
        ],
    )

    assert [issue["code"] for issue in issues] == [
        "DUPLICATE_TIMESTAMP",
        "NON_MONOTONIC_TIMESTAMP",
        "INVALID_TIMESTAMP",
    ]
    assert issues[0]["index"] == 1
    assert issues[1]["index"] == 2
    assert issues[2]["index"] == 3


def test_validate_timestamp_sequence_can_allow_duplicates() -> None:
    issues = validate_timestamp_sequence(
        ["2026-06-11T10:00:00Z", "2026-06-11T10:00:00Z"],
        allow_duplicates=True,
    )

    assert issues == []


def test_normalize_timestamp_column_returns_new_rows() -> None:
    rows = [{"created_at": "2026-06-11T12:00:00+02:00", "value": 1}]

    normalized = normalize_timestamp_column(rows, column="created_at")

    assert normalized[0]["created_at"] == datetime(2026, 6, 11, 10, 0, tzinfo=UTC)
    assert rows[0]["created_at"] == "2026-06-11T12:00:00+02:00"


def test_normalize_timestamp_column_rejects_missing_or_invalid_values() -> None:
    with pytest.raises(ValidationError, match="missing"):
        normalize_timestamp_column([{"other": "2026-06-11T10:00:00Z"}], column="ts")

    with pytest.raises(ValidationError, match="column"):
        normalize_timestamp_column([], column="")

    with pytest.raises(ValidationError, match="datetime-like"):
        normalize_timestamp_column([{"ts": object()}], column="ts")


def test_clock_drift_status_is_deterministic() -> None:
    status = check_clock_drift(
        "2026-06-11T11:59:00Z",
        now="2026-06-11T12:00:00Z",
        max_drift_seconds=30,
    )

    assert status == {
        "drift_detected": True,
        "drift_seconds": 60.0,
        "max_drift_seconds": 30.0,
        "checked_at": "2026-06-11T12:00:00Z",
    }

    with pytest.raises(ValidationError, match="max_drift_seconds"):
        check_clock_drift("2026-06-11T12:00:00Z", max_drift_seconds=-1)


def test_execution_timing_policy_remains_monotonic() -> None:
    assert get_execution_ms(0.0) >= 0
