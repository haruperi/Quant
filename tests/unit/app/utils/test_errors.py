"""Unit tests for app.utils.errors."""

import pytest
from app.utils.errors import (
    APPROVED_ERROR_CODES,
    ConfigurationError,
    DataError,
    Error,
    ExternalServiceError,
    SecurityError,
    ValidationError,
    code_for_exception,
    details_for_exception,
    error_name,
    exception_to_error_payload,
    message_for,
    normalize_error_code,
    raise_for_invalid_code,
    validate_error_payload,
)


class CompatibleDomainError(Exception):
    """Future-compatible domain error for mapping tests."""

    code = "AUTHORIZATION_FAILED"


def test_shared_exceptions_have_deterministic_codes_and_messages() -> None:
    cases = [
        (Error("unknown"), "UNKNOWN_ERROR"),
        (ValidationError("bad input"), "VALIDATION_FAILED"),
        (ConfigurationError("missing config"), "SERVICE_UNAVAILABLE"),
        (SecurityError("blocked"), "PERMISSION_DENIED"),
        (DataError("not found"), "DATA_NOT_FOUND"),
        (ExternalServiceError("down"), "SERVICE_UNAVAILABLE"),
    ]

    for error, expected_code in cases:
        assert error.code == expected_code
        assert str(error)
        assert expected_code in APPROVED_ERROR_CODES


def test_error_name_and_message_for_known_and_unknown_codes() -> None:
    assert error_name("invalid_input") == "Invalid Input"
    assert message_for("INVALID_INPUT") == "The request input is invalid."
    assert message_for("FUTURE_DOMAIN_ERROR") == "An unknown error occurred."
    assert message_for("FUTURE_DOMAIN_ERROR", default="fallback") == "fallback"


def test_normalize_error_code_is_safe_for_unknown_or_empty_codes() -> None:
    assert normalize_error_code("INVALID_EVENT") == "INVALID_EVENT"
    assert normalize_error_code("NOT_A_CODE") == "UNKNOWN_ERROR"
    assert normalize_error_code(None, default="TOOL_EXECUTION_FAILED") == (
        "TOOL_EXECUTION_FAILED"
    )


def test_raise_for_invalid_code_rejects_unknown_codes() -> None:
    raise_for_invalid_code("CIRCUIT_OPEN")

    with pytest.raises(ValidationError, match="not approved"):
        raise_for_invalid_code("FUTURE_DOMAIN_ERROR")


def test_code_for_exception_supports_haruquant_and_compatible_errors() -> None:
    assert code_for_exception(SecurityError("blocked")) == "PERMISSION_DENIED"
    assert code_for_exception(CompatibleDomainError("no role")) == (
        "AUTHORIZATION_FAILED"
    )
    assert code_for_exception(RuntimeError("boom")) == "TOOL_EXECUTION_FAILED"


def test_exception_to_error_payload_never_returns_raw_exception_objects() -> None:
    exception = RuntimeError("boom")

    payload = exception_to_error_payload(exception)

    assert payload == {"code": "TOOL_EXECUTION_FAILED", "details": "RuntimeError: boom"}
    assert isinstance(payload["details"], str)


def test_details_for_exception_is_human_readable() -> None:
    assert details_for_exception(ValueError("bad")) == "ValueError: bad"


def test_validate_error_payload_normalizes_and_rejects_malformed_payloads() -> None:
    assert validate_error_payload(
        {"code": "INVALID_INPUT", "details": "field is required"},
    ) == {"code": "INVALID_INPUT", "details": "field is required"}

    assert validate_error_payload(
        {"code": "FUTURE_DOMAIN_ERROR", "details": "unknown"},
    ) == {"code": "UNKNOWN_ERROR", "details": "unknown"}

    with pytest.raises(ValidationError, match="details"):
        validate_error_payload({"code": "INVALID_INPUT", "details": ""})
