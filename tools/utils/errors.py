"""Deterministic HaruQuant error utilities.

This module provides support helpers, not official AI tools. It exports typed
HaruQuant exceptions, the approved deterministic error-code registry, safe
error-code normalization, fallback messages, and exception-to-error-payload
mapping helpers.

Public exports:
    APPROVED_ERROR_CODES, ERROR_MESSAGES, Error, ValidationError,
    ConfigurationError, SecurityError, DataError, ExternalServiceError,
    error_name, message_for, normalize_error_code, code_for_exception,
    details_for_exception, exception_to_error_payload, raise_for_invalid_code.

Side effects:
    None. Importing this module does not configure logging, read files, import
    optional dependencies, call networks, or mutate live trading state.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from tools.utils.logger import logger

APPROVED_ERROR_CODES = frozenset(
    {
        "INVALID_INPUT",
        "PERMISSION_DENIED",
        "DATA_NOT_FOUND",
        "EMPTY_RESULT",
        "SERVICE_UNAVAILABLE",
        "BROKER_UNAVAILABLE",
        "DATABASE_ERROR",
        "NETWORK_ERROR",
        "TIMEOUT",
        "VALIDATION_FAILED",
        "TOOL_EXECUTION_FAILED",
        "UNKNOWN_ERROR",
        "INVALID_AUTH_CONTEXT",
        "AUTHORIZATION_FAILED",
        "INVALID_EVENT",
        "EVENT_PUBLISH_FAILED",
        "EVENT_HANDLER_FAILED",
        "EVENT_DEAD_LETTER_FAILED",
        "QUEUE_FULL",
        "BACKPRESSURE_EXCEEDED",
        "NOTIFICATION_FAILED",
        "NOTIFICATION_SUPPRESSED",
        "NOTIFICATION_THROTTLED",
        "OBSERVABILITY_ERROR",
        "METRICS_EXPORT_FAILED",
        "CLOCK_DRIFT_DETECTED",
        "CIRCUIT_OPEN",
        "SECRET_VERSION_CONFLICT",
    }
)

ERROR_MESSAGES: dict[str, str] = {
    "INVALID_INPUT": "The request input is invalid.",
    "PERMISSION_DENIED": "The request is not permitted.",
    "DATA_NOT_FOUND": "The requested data was not found.",
    "EMPTY_RESULT": "The request completed but returned no results.",
    "SERVICE_UNAVAILABLE": "The required service is unavailable.",
    "BROKER_UNAVAILABLE": "The broker service is unavailable.",
    "DATABASE_ERROR": "A database operation failed.",
    "NETWORK_ERROR": "A network operation failed.",
    "TIMEOUT": "The operation timed out.",
    "VALIDATION_FAILED": "Response validation failed.",
    "TOOL_EXECUTION_FAILED": "The tool failed during execution.",
    "UNKNOWN_ERROR": "An unknown error occurred.",
    "INVALID_AUTH_CONTEXT": "The authentication context is invalid.",
    "AUTHORIZATION_FAILED": "Authorization failed.",
    "INVALID_EVENT": "The event payload is invalid.",
    "EVENT_PUBLISH_FAILED": "The event could not be published.",
    "EVENT_HANDLER_FAILED": "The event handler failed.",
    "EVENT_DEAD_LETTER_FAILED": "The event could not be dead-lettered.",
    "QUEUE_FULL": "The queue is full.",
    "BACKPRESSURE_EXCEEDED": "Backpressure limits were exceeded.",
    "NOTIFICATION_FAILED": "Notification delivery failed.",
    "NOTIFICATION_SUPPRESSED": "Notification delivery was suppressed.",
    "NOTIFICATION_THROTTLED": "Notification delivery was throttled.",
    "OBSERVABILITY_ERROR": "An observability operation failed.",
    "METRICS_EXPORT_FAILED": "Metrics export failed.",
    "CLOCK_DRIFT_DETECTED": "Clock drift was detected.",
    "CIRCUIT_OPEN": "The circuit is open and the operation was blocked.",
    "SECRET_VERSION_CONFLICT": "Secret conflict detected.",  # pragma: allowlist secret
}


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


class Error(Exception):
    """Base deterministic utility error with a stable error code.

    Use this for support helpers that need to raise typed HaruQuant exceptions
    while remaining safely mappable at official tool boundaries.

    Args:
        message: Human-readable error details.
        code: Optional approved deterministic error code.

    Raises:
        ValidationError: If an explicit code is not approved.
    """

    code = "UNKNOWN_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize the error with deterministic message and code."""
        super().__init__(message)
        if code is not None:
            self.code = normalize_error_code(code)


class ValidationError(Error):
    """Input, payload, or output validation failure."""

    code = "VALIDATION_FAILED"


class ConfigurationError(Error):
    """Invalid or missing runtime configuration."""

    code = "SERVICE_UNAVAILABLE"


class SecurityError(Error):
    """Permission, authorization, or redaction failure."""

    code = "PERMISSION_DENIED"


class DataError(Error):
    """Data lookup, shape, or availability failure."""

    code = "DATA_NOT_FOUND"


class ExternalServiceError(Error):
    """External service, network, broker, or timeout failure."""

    code = "SERVICE_UNAVAILABLE"


def _validate_code_text(code: object, field_name: str = "code") -> str:
    """Return an uppercase code string or raise a typed validation error."""
    if not isinstance(code, str) or not code.strip():
        message = f"{field_name} must be a non-empty string."
        raise ValidationError(message)
    return code.strip().upper()


def normalize_error_code(
    code: str | None,
    *,
    default: str = "UNKNOWN_ERROR",
) -> str:
    """Return an approved deterministic error code.

    Use this at tool boundaries and response builders before emitting errors.
    Unknown codes resolve to ``default`` when approved, otherwise
    ``UNKNOWN_ERROR``.

    Args:
        code: Candidate error code.
        default: Approved fallback code.

    Returns:
        Approved deterministic error code.

    Side effects:
        Logs unknown-code normalization for diagnostics.
    """
    fallback = default.strip().upper() if isinstance(default, str) else "UNKNOWN_ERROR"
    if fallback not in APPROVED_ERROR_CODES:
        fallback = "UNKNOWN_ERROR"
    if not isinstance(code, str) or not code.strip():
        return fallback
    normalized = code.strip().upper()
    if normalized in APPROVED_ERROR_CODES:
        return normalized
    logger.warning(
        "unknown error code normalized",
        extra={
            "event_name": "error_code_normalized",
            "error_code": normalized,
        },
    )
    return fallback


def raise_for_invalid_code(code: str) -> None:
    """Raise when ``code`` is not in the approved error-code registry.

    Use this in tests or strict validation paths where unknown codes should be
    rejected instead of normalized.

    Args:
        code: Candidate error code.

    Raises:
        ValidationError: If the code is empty or not approved.

    Side effects:
        None.
    """
    normalized = _validate_code_text(code)
    if normalized not in APPROVED_ERROR_CODES:
        message = f"error code is not approved: {normalized}"
        raise ValidationError(message)


def error_name(code: str) -> str:
    """Return a deterministic human-readable name for an error code.

    Args:
        code: Error code to convert.

    Returns:
        Title-cased display name. Unknown codes are normalized safely first.

    Raises:
        ValidationError: If ``code`` is empty.

    Side effects:
        None.
    """
    normalized = normalize_error_code(_validate_code_text(code))
    return normalized.replace("_", " ").title()


def message_for(code: str, default: str | None = None) -> str:
    """Return the deterministic default message for an error code.

    Args:
        code: Error code to look up.
        default: Optional caller-provided fallback message for unknown codes.

    Returns:
        Known default message, provided fallback, or the ``UNKNOWN_ERROR``
        message for unknown codes.

    Raises:
        ValidationError: If ``code`` is empty.

    Side effects:
        None.
    """
    candidate = _validate_code_text(code)
    if candidate in ERROR_MESSAGES:
        return ERROR_MESSAGES[candidate]
    if default is not None:
        return default
    return ERROR_MESSAGES["UNKNOWN_ERROR"]


def code_for_exception(
    exception: BaseException,
    *,
    default: str = "TOOL_EXECUTION_FAILED",
) -> str:
    """Return a safe deterministic code for an exception.

    Args:
        exception: Exception to inspect. Compatible future domain errors may
            expose a string ``code`` attribute.
        default: Approved fallback for unknown non-HaruQuant exceptions.

    Returns:
        Approved deterministic error code.

    Side effects:
        None.
    """
    raw_code = getattr(exception, "code", None)
    if isinstance(raw_code, str):
        return normalize_error_code(raw_code, default=default)
    return normalize_error_code(default)


def details_for_exception(exception: BaseException) -> str:
    """Return safe human-readable details for an exception.

    Args:
        exception: Exception to describe.

    Returns:
        String details containing exception type and message. The raw exception
        object is never returned.

    Side effects:
        None.
    """
    return f"{exception.__class__.__name__}: {exception}"


def exception_to_error_payload(
    exception: BaseException,
    *,
    default_code: str = "TOOL_EXECUTION_FAILED",
) -> ErrorPayload:
    """Map an exception to a standard error payload.

    Args:
        exception: Exception to map.
        default_code: Approved fallback code for unknown exceptions.

    Returns:
        Mapping with deterministic ``code`` and string ``details``.

    Side effects:
        None.
    """
    return {
        "code": code_for_exception(exception, default=default_code),
        "details": details_for_exception(exception),
    }


def validate_error_payload(payload: Mapping[str, object]) -> ErrorPayload:
    """Validate and normalize a mapping into an error payload.

    Args:
        payload: Candidate payload containing ``code`` and ``details``.

    Returns:
        Normalized error payload.

    Raises:
        ValidationError: If required fields are missing or malformed.

    Side effects:
        None.
    """
    code = payload.get("code")
    details = payload.get("details")
    if set(payload) != {"code", "details"}:
        raise ValidationError("error must contain exactly code and details.")
    if not isinstance(details, str) or not details:
        raise ValidationError("error.details must be a non-empty string.")
    return {"code": normalize_error_code(_validate_code_text(code)), "details": details}
