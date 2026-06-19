"""Unit tests for app.utils.standard."""

import math
import time
from collections.abc import Mapping

import pytest
from app.utils.errors import (
    ConfigurationError,
    SecurityError,
    ValidationError,
    error_name,
    message_for,
)
from app.utils.standard import (
    AlertDeduplicator,
    build_data_quality_issue,
    build_error_event,
    build_metadata,
    canonical_json,
    circuit_open_response,
    error_response,
    get_execution_ms,
    is_official_tool_allowed,
    response_from_exception,
    stable_identifier,
    success_response,
    validate_metric_labels,
    validate_ohlcv_records,
    validate_standard_response,
)


def test_build_metadata_contains_required_contract_fields() -> None:
    metadata = build_metadata(
        tool_name="validate_payload",
        execution_ms=1.23456,
        request_id="req-001",
        reads=True,
    )

    assert metadata == {
        "tool_name": "validate_payload",
        "tool_version": "1.0.0",
        "tool_category": "utils",
        "tool_risk_level": "low",
        "request_id": "req-001",
        "execution_ms": 1.235,
        "reads": True,
        "writes": False,
        "updates": False,
        "deletes": False,
        "trades": False,
        "requires_network": False,
        "read_only": True,
        "writes_file": False,
        "modifies_database": False,
        "places_trade": False,
    }


def test_success_response_matches_standard_envelope() -> None:
    metadata = build_metadata(tool_name="validate_payload", execution_ms=0)

    response = success_response(
        message="Payload is valid.",
        data={"valid": True},
        metadata=metadata,
    )

    validate_standard_response(response)
    assert response["status"] == "success"
    assert response["error"] is None
    assert response["data"] == {"valid": True}
    assert response["metadata"]["tool_name"] == "validate_payload"


def test_error_response_matches_standard_envelope() -> None:
    metadata = build_metadata(tool_name="validate_payload", execution_ms=0)

    response = error_response(
        message="Payload is invalid.",
        code="INVALID_INPUT",
        details="field name is required",
        metadata=metadata,
    )

    validate_standard_response(response)
    assert response["status"] == "error"
    assert response["data"] is None
    assert response["error"] == {
        "code": "INVALID_INPUT",
        "details": "field name is required",
    }


def test_validate_standard_response_rejects_missing_top_level_key() -> None:
    metadata = build_metadata(tool_name="validate_payload", execution_ms=0)
    response = {
        "status": "success",
        "message": "ok",
        "data": {},
        "metadata": metadata,
    }

    with pytest.raises(ValidationError, match="missing keys"):
        validate_standard_response(response)


def test_validate_standard_response_rejects_missing_metadata_key() -> None:
    metadata = dict(build_metadata(tool_name="validate_payload", execution_ms=0))
    metadata.pop("execution_ms")
    response = {
        "status": "success",
        "message": "ok",
        "data": {},
        "error": None,
        "metadata": metadata,
    }

    with pytest.raises(ValidationError, match="metadata is missing keys"):
        validate_standard_response(response)


def test_validate_standard_response_rejects_malformed_error() -> None:
    metadata = build_metadata(tool_name="validate_payload", execution_ms=0)
    response = {
        "status": "error",
        "message": "bad",
        "data": None,
        "error": {"code": "INVALID_INPUT"},
        "metadata": metadata,
    }

    with pytest.raises(ValidationError, match="code and details"):
        validate_standard_response(response)


def test_validate_standard_response_rejects_success_with_error_payload() -> None:
    metadata = build_metadata(tool_name="validate_payload", execution_ms=0)
    response = {
        "status": "success",
        "message": "ok",
        "data": {},
        "error": {"code": "INVALID_INPUT", "details": "not allowed"},
        "metadata": metadata,
    }

    with pytest.raises(ValidationError, match="success responses"):
        validate_standard_response(response)


def test_canonical_json_is_deterministic_and_rejects_nan() -> None:
    left = {"b": [2, 1], "a": {"z": False, "n": None}}
    right = {"a": {"n": None, "z": False}, "b": [2, 1]}

    assert canonical_json(left) == canonical_json(right)
    assert canonical_json(left) == '{"a":{"n":null,"z":false},"b":[2,1]}'

    with pytest.raises(ValidationError, match="canonical JSON serializable"):
        canonical_json({"bad": math.nan})


def test_error_helpers_are_deterministic_for_known_and_unknown_codes() -> None:
    assert error_name("invalid_input") == "Invalid Input"
    assert message_for("INVALID_INPUT") == "The request input is invalid."
    assert message_for("FUTURE_DOMAIN_ERROR") == "An unknown error occurred."


def test_response_from_exception_uses_compatible_code_attribute() -> None:
    metadata = build_metadata(tool_name="load_settings", execution_ms=0)
    exc = ConfigurationError("missing environment variable")

    response = response_from_exception(
        exception=exc,
        metadata=metadata,
        message="Could not load settings.",
    )

    assert response["status"] == "error"
    assert response["error"] is not None
    assert response["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "ConfigurationError" in response["error"]["details"]


def test_get_execution_ms_uses_monotonic_duration() -> None:
    start = time.perf_counter()
    time.sleep(0.001)

    execution_ms = get_execution_ms(start)

    assert execution_ms >= 0
    assert round(execution_ms, 3) == execution_ms


def test_build_metadata_rejects_invalid_inputs() -> None:
    with pytest.raises(ValidationError, match="tool_name"):
        build_metadata(tool_name="", execution_ms=0)

    with pytest.raises(ValidationError, match="tool_risk_level"):
        build_metadata(
            tool_name="bad_tool",
            execution_ms=0,
            tool_risk_level="unsafe",  # type: ignore[arg-type]
        )

    with pytest.raises(ValidationError, match="execution_ms"):
        build_metadata(tool_name="bad_tool", execution_ms=-1)


def test_stable_identifier_is_deterministic() -> None:
    left = {"symbol": "EURUSD", "timeframe": "1h"}
    right = {"timeframe": "1h", "symbol": "EURUSD"}

    assert stable_identifier(left, prefix="req") == stable_identifier(
        right,
        prefix="req",
    )
    assert stable_identifier(left, prefix="req").startswith("req_")


def test_data_quality_issue_schema_bounds_samples() -> None:
    issue = build_data_quality_issue(
        code="negative_price",
        severity="critical",
        message="Negative price detected.",
        column="close",
        row_count=3,
        samples=[1, 2, 3],
        max_samples=2,
    )

    assert issue == {
        "code": "NEGATIVE_PRICE",
        "severity": "critical",
        "message": "Negative price detected.",
        "column": "close",
        "row_count": 3,
        "samples": [1, 2],
    }


def test_validate_ohlcv_records_reports_required_data_quality_cases() -> None:
    records: list[Mapping[str, object]] = [
        {"open": -1, "high": 2, "low": 1, "close": 1.5},
        {"open": 0, "high": 2, "low": 1, "close": 1.5},
        {"open": math.nan, "high": 2, "low": 1, "close": 1.5},
        {"open": math.inf, "high": 2, "low": 1, "close": 1.5},
        {"open": "bad", "high": 2, "low": 1, "close": 1.5},
        {"open": 3, "high": 2, "low": 1, "close": 1.5},
        {"open": 0.5, "high": 2, "low": 1, "close": 1.5},
        {"open": 1.5, "high": 0, "low": 1, "close": 1.5},
        {"open": 1.5, "high": -2, "low": -3, "close": -1.5},
        {"open": 1.5, "high": 2, "low": 3, "close": 1.5},
        {"open": 1.5, "high": 2, "low": 1, "close": 3},
        {"open": 1.5, "high": 2, "low": 1, "close": 0.5},
        {"symbol": "GBPUSD", "open": 1.5, "high": 2, "low": 1, "close": 1.5},
        {"symbol": "EURUSD", "open": 1.5, "high": 2, "low": 1, "close": 1.5},
        {"open": 1, "high": 1, "low": 1, "close": 1},
    ]

    issues = validate_ohlcv_records(
        records,
        expected_symbol="EURUSD",
        sample_limit=2,
    )
    codes = {issue["code"] for issue in issues}

    assert "NEGATIVE_PRICE" in codes
    assert "ZERO_PRICE" in codes
    assert "NON_FINITE_PRICE" in codes
    assert "NON_NUMERIC_PRICE" in codes
    assert "OHLC_OUTSIDE_HIGH_LOW" in codes
    assert "LOW_ABOVE_HIGH" in codes
    assert "SYMBOL_MISMATCH" in codes
    assert all(
        {"code", "severity", "message", "column", "row_count", "samples"} == set(issue)
        for issue in issues
    )
    assert all(len(issue["samples"]) <= 2 for issue in issues)


def test_validate_ohlcv_records_marks_symbol_verification_not_available() -> None:
    issues = validate_ohlcv_records(
        [{"open": 1.0, "high": 2.0, "low": 1.0, "close": 1.5}],
        expected_symbol="EURUSD",
    )

    assert issues[0]["code"] == "SYMBOL_NOT_AVAILABLE"
    assert issues[0]["samples"] == [{"verification": "not_available"}]


def test_validate_ohlcv_records_reports_missing_ohlc_columns_as_invalid_input() -> None:
    issues = validate_ohlcv_records([{"open": 1.0, "high": 2.0}])

    assert {issue["code"] for issue in issues} >= {"INVALID_INPUT"}
    invalid_columns = {
        issue["column"] for issue in issues if issue["code"] == "INVALID_INPUT"
    }
    assert invalid_columns >= {
        "low",
        "close",
    }


def test_validate_ohlcv_records_truncates_issue_list() -> None:
    records: list[Mapping[str, object]] = [
        {"open": "bad", "high": "bad", "low": "bad", "close": "bad"},
    ]

    issues = validate_ohlcv_records(records, issue_limit=2)

    assert len(issues) == 2


def test_circuit_open_response_fails_fast_with_standard_error() -> None:
    metadata = build_metadata(tool_name="provider_call", execution_ms=0)

    response = circuit_open_response(
        metadata=metadata,
        provider="quotes",
        details="quotes circuit is open",
    )

    validate_standard_response(response)
    assert response["status"] == "error"
    assert response["error"] is not None
    assert response["error"]["code"] == "CIRCUIT_OPEN"


def test_build_error_event_sanitizes_details_and_metadata() -> None:
    event = build_error_event(
        code="NETWORK_ERROR",
        details="request failed token=abc123",  # pragma: allowlist secret
        request_id="req-1",
        metadata={"api_key": "abc123", "safe": "value"},  # pragma: allowlist secret
    )

    assert event["event_id"].startswith("event_")
    assert "[REDACTED]" in event["error"]["details"]
    assert event["metadata"]["api_key"] == "[REDACTED]"
    assert event["metadata"]["safe"] == "value"


def test_validate_metric_labels_rejects_sensitive_and_high_cardinality_labels() -> None:
    assert validate_metric_labels({"module": "utils", "operation": "validate"}) == {
        "module": "utils",
        "operation": "validate",
    }

    with pytest.raises(SecurityError):
        validate_metric_labels({"api_key": "abc"})

    with pytest.raises(ValidationError, match="high-cardinality"):
        validate_metric_labels({"request_id": "req-123"})

    normalized = validate_metric_labels(
        {"request_id": "req-123"},
        normalize_high_cardinality=True,
    )
    assert normalized["request_id"].startswith("label_")


def test_is_official_tool_allowed_checks_approved_attachment_set() -> None:
    approved = {"validate_ohlcv_records", "redact_payload"}

    assert is_official_tool_allowed("validate_ohlcv_records", approved)
    assert not is_official_tool_allowed("internal_helper", approved)


def test_alert_deduplicator_is_bounded_and_deterministic() -> None:
    deduper = AlertDeduplicator(window_seconds=10, max_entries=2)

    assert deduper.allow("alert-a", now=1.0)
    assert not deduper.allow("alert-a", now=2.0)
    assert deduper.allow("alert-a", now=12.0)
    assert deduper.allow("alert-b", now=13.0)
    assert deduper.allow("alert-c", now=14.0)
    assert len(deduper._seen) == 2
