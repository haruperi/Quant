"""Standard tool envelopes and deterministic utility contracts.

This module provides support helpers, not official AI tools. It exports
standard response builders, validation helpers, error classes, error-code
lookups, deterministic JSON serialization, and execution timing helpers.

Public exports:
    Error, ValidationError, ConfigurationError, DataError, SecurityError,
    ExternalServiceError, StandardErrorPayload, StandardMetadata,
    ToolMetadata, ToolError, StandardResponse, StandardEnvelope,
    build_metadata, success_response, build_success_response,
    error_response, build_error_response, validate_standard_response,
    get_execution_ms, canonical_json, error_name, message_for,
    stable_identifier, build_data_quality_issue, validate_ohlcv_records,
    circuit_open_response, build_error_event, validate_metric_labels,
    is_official_tool_allowed, AlertDeduplicator.

Side effects:
    None. Importing this module does not configure logging, touch the
    filesystem, import optional dependencies, call networks, or mutate
    live trading state.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections.abc import Mapping
from typing import Final, Literal, NotRequired, TypedDict

from app.utils.errors import (
    ErrorPayload,
    SecurityError,
    ValidationError,
    exception_to_error_payload,
    normalize_error_code,
    validate_error_payload,
)
from app.utils.logger import logger as project_logger

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

ToolStatus = Literal["success", "error"]
ToolRiskLevel = Literal["low", "medium", "high", "critical"]
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
IssueSeverity = Literal["info", "warning", "error", "critical"]

# ---------------------------------------------------------------------------
# Module-level constants (immutable)
# ---------------------------------------------------------------------------

SUCCESS_STATUS: Final = "success"
ERROR_STATUS: Final = "error"
DEFAULT_TOOL_VERSION: Final[str] = "1.0.0"
DEFAULT_TOOL_CATEGORY: Final[str] = "utils"
DEFAULT_TOOL_RISK_LEVEL: Final[ToolRiskLevel] = "low"

STANDARD_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {"status", "message", "data", "error", "metadata"}
)
STANDARD_METADATA_KEYS: Final[frozenset[str]] = frozenset(
    {
        "tool_name",
        "tool_version",
        "tool_category",
        "tool_risk_level",
        "request_id",
        "execution_ms",
        "reads",
        "writes",
        "updates",
        "deletes",
        "trades",
        "requires_network",
        "read_only",
        "writes_file",
        "modifies_database",
        "places_trade",
    }
)

OHLC_COLUMNS: Final[tuple[str, ...]] = ("open", "high", "low", "close")

SENSITIVE_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(pass(word)?|api_?key|token|credential|secret"
    r"|private_?key|authorization)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(eyJ[A-Za-z0-9_\-=]+\.[A-Za-z0-9_\-=]+\.?[A-Za-z0-9_\-./+=]*)"
    r"|([a-f0-9]{32,})",
    re.IGNORECASE,
)
HIGH_CARDINALITY_LABEL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(^|_)(id|uuid|guid|email|account|user|session|token"
    r"|request|correlation)($|_)",
    re.IGNORECASE,
)

# Type alias — keep StandardErrorPayload as the canonical name used by
# callers who already import from errors.py directly.
StandardErrorPayload = ErrorPayload


# ---------------------------------------------------------------------------
# TypedDict schemas
# ---------------------------------------------------------------------------


class StandardMetadata(TypedDict):
    """Metadata required on every standard tool envelope."""

    tool_name: str
    tool_version: str
    tool_category: str
    tool_risk_level: ToolRiskLevel
    request_id: str | None
    execution_ms: float
    reads: bool
    writes: bool
    updates: bool
    deletes: bool
    trades: bool
    requires_network: bool
    read_only: bool
    writes_file: bool
    modifies_database: bool
    places_trade: bool


# Contract alias — callers importing by the specified public name receive
# the same type.
ToolMetadata = StandardMetadata


class ToolError(ValidationError):
    """Standard tool-layer validation or execution error.

    Use this at official AI tool boundaries when an expected failure must
    be raised rather than returned as an envelope.  The ``code`` attribute
    maps to an approved deterministic error code.

    Args:
        message: Human-readable error details.
        code: Optional approved error code; defaults to
            ``"TOOL_EXECUTION_FAILED"``.
    """

    code = "TOOL_EXECUTION_FAILED"


class StandardResponse(TypedDict):
    """Standard HaruQuant tool response envelope."""

    status: ToolStatus
    message: str
    data: object | None
    error: StandardErrorPayload | None
    metadata: StandardMetadata


class DataQualityIssue(TypedDict):
    """Bounded diagnostic issue for data-quality reporting."""

    code: str
    severity: IssueSeverity
    message: str
    column: str | None
    row_count: int
    samples: list[object]


class ErrorEvent(TypedDict):
    """Sanitized standard error event payload."""

    event_id: str
    event_type: str
    error: StandardErrorPayload
    request_id: str | None
    metadata: dict[str, object]


class StandardEnvelope(StandardResponse, total=False):
    """Backward-compatible typed alias for the standard response envelope."""

    validation_warnings: NotRequired[list[str]]


# ---------------------------------------------------------------------------
# Internal validation helpers
# ---------------------------------------------------------------------------


def _validate_non_empty_string(value: object, field_name: str) -> str:
    """Return a stripped string or raise a deterministic validation error."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} must be a non-empty string.")  # noqa: EM102
    return value.strip()


def _sanitize_text(value: str) -> str:
    """Return text with secret-like values redacted."""
    text = SENSITIVE_VALUE_PATTERN.sub("[REDACTED]", value)
    return re.sub(
        r"((?:pass(?:word)?|api_?key|token|credential|secret"
        r"|authorization)\s*[:=]\s*)[^\s,;&'\"]+",
        r"\1[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )


def _sanitize_value(value: object) -> object:
    """Return a JSON-like value with secret-like fields redacted."""
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, list | tuple | set):
        return [_sanitize_value(item) for item in value]
    return value


def _sanitize_mapping(
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Return a mapping with sensitive keys and values redacted."""
    sanitized: dict[str, object] = {}
    for key, value in payload.items():
        if SENSITIVE_KEY_PATTERN.search(str(key)):
            sanitized[str(key)] = "[REDACTED]"
        else:
            sanitized[str(key)] = _sanitize_value(value)
    return sanitized


def _validate_metadata(metadata: Mapping[str, object]) -> None:  # noqa: C901
    """Validate all fields of a standard envelope metadata mapping.

    Checks presence, absence of unknown keys, and correct types for every
    metadata field including the four derived boolean fields.
    """
    keys = set(metadata.keys())
    missing = STANDARD_METADATA_KEYS - keys
    if missing:
        raise ValidationError(f"metadata is missing keys: {sorted(missing)}")  # noqa: EM102
    extra = keys - STANDARD_METADATA_KEYS
    if extra:
        raise ValidationError(f"metadata has unexpected keys: {sorted(extra)}")  # noqa: EM102
    for key in ("tool_name", "tool_version", "tool_category"):
        if not isinstance(metadata[key], str) or not metadata[key]:
            raise ValidationError(f"metadata.{key} must be a non-empty string.")  # noqa: EM102
    if metadata["tool_risk_level"] not in {"low", "medium", "high", "critical"}:
        raise ValidationError("metadata.tool_risk_level is invalid.")
    if metadata["request_id"] is not None and not isinstance(
        metadata["request_id"], str
    ):
        raise ValidationError("metadata.request_id must be a string or None.")
    if not isinstance(metadata["execution_ms"], int | float):
        raise ValidationError("metadata.execution_ms must be numeric.")
    if float(metadata["execution_ms"]) < 0:
        raise ValidationError("metadata.execution_ms must be non-negative.")
    bool_fields = (
        "reads",
        "writes",
        "updates",
        "deletes",
        "trades",
        "requires_network",
        "read_only",
        "writes_file",
        "modifies_database",
        "places_trade",
    )
    for key in bool_fields:
        if not isinstance(metadata[key], bool):
            raise ValidationError(f"metadata.{key} must be a boolean.")  # noqa: EM102


def _validate_error_payload(error: object) -> None:
    """Validate a standard envelope error payload mapping."""
    if not isinstance(error, Mapping):
        raise ValidationError("error responses must include an error mapping.")
    validate_error_payload(error)


# ---------------------------------------------------------------------------
# Deduplication helper
# ---------------------------------------------------------------------------


class AlertDeduplicator:
    """Bounded in-memory alert deduplicator for standard helper tests.

    Use this when a caller needs deterministic repeated-alert suppression
    before a future notification router exists. It is caller-owned, bounded,
    and has no module-global cache.

    Args:
        window_seconds: Minimum seconds before the same key is allowed again.
        max_entries: Maximum remembered keys.

    Side effects:
        Mutates only this instance's bounded cache.
    """

    def __init__(
        self,
        *,
        window_seconds: float,
        max_entries: int = 128,
    ) -> None:
        """Initialize a bounded deduplication cache.

        Args:
            window_seconds: Suppression window in seconds.
            max_entries: Maximum number of distinct keys retained.
        """
        if window_seconds < 0:
            raise ValidationError("window_seconds must be non-negative.")
        if max_entries <= 0:
            raise ValidationError("max_entries must be greater than zero.")
        self.window_seconds = float(window_seconds)
        self.max_entries = int(max_entries)
        self._seen: dict[str, float] = {}

    def allow(self, key: str, *, now: float | None = None) -> bool:
        """Return whether an alert key is currently allowed.

        Args:
            key: Stable alert fingerprint.
            now: Optional monotonic timestamp for deterministic tests.

        Returns:
            ``True`` when the alert should be emitted, otherwise
            ``False``.

        Side effects:
            Updates this instance's bounded cache when an alert is
            allowed.
        """
        fingerprint = _validate_non_empty_string(key, "key")
        current = time.monotonic() if now is None else float(now)
        previous = self._seen.get(fingerprint)
        if previous is not None and current - previous < self.window_seconds:
            return False
        if len(self._seen) >= self.max_entries and fingerprint not in self._seen:
            oldest = min(self._seen, key=self._seen.__getitem__)
            del self._seen[oldest]
        self._seen[fingerprint] = current
        return True


# ---------------------------------------------------------------------------
# Core utility functions
# ---------------------------------------------------------------------------


def stable_identifier(
    payload: object,
    *,
    prefix: str = "id",
) -> str:
    """Return a deterministic identifier for JSON-serializable payloads.

    Use this for reproducible fingerprints, event IDs, and tests that
    need deterministic ID behavior without randomness.

    Args:
        payload: JSON-serializable fingerprint material.
        prefix: Non-empty identifier prefix.

    Returns:
        Stable identifier in ``prefix_digest`` format.

    Side effects:
        None.
    """
    safe_prefix = _validate_non_empty_string(prefix, "prefix")
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{safe_prefix}_{digest[:16]}"


def get_execution_ms(start_time: float) -> float:
    """Return elapsed milliseconds from a ``time.perf_counter()`` start.

    Use this in official AI tools to populate ``metadata.execution_ms``.

    Args:
        start_time: Monotonic start timestamp captured with
            ``time.perf_counter()``.

    Returns:
        Elapsed milliseconds rounded to three decimals.

    Side effects:
        None.
    """
    if not isinstance(start_time, int | float):
        raise ValidationError("start_time must be a numeric perf_counter value.")
    elapsed_ms = (time.perf_counter() - float(start_time)) * 1000
    return round(max(elapsed_ms, 0.0), 3)


def build_data_quality_issue(
    *,
    code: str,
    severity: IssueSeverity,
    message: str,
    column: str | None,
    row_count: int,
    samples: list[object] | None = None,
    max_samples: int = 5,
) -> DataQualityIssue:
    """Build a bounded data-quality diagnostic issue.

    Use this for diagnostic reporting only. It does not repair, clean,
    resample, persist, or enrich market data; those workflows belong to
    ``tools.data``.

    Args:
        code: Stable issue code.
        severity: Issue severity.
        message: Human-readable diagnostic message.
        column: Related column name or ``None``.
        row_count: Number of affected rows.
        samples: Optional sample payloads.
        max_samples: Maximum retained sample count.

    Returns:
        Data-quality issue with code, severity, message, column, row
        count, and bounded samples.

    Side effects:
        None.
    """
    normalized_code = _validate_non_empty_string(code, "code").upper()
    if severity not in {"info", "warning", "error", "critical"}:
        raise ValidationError("severity must be info, warning, error, or critical.")
    if row_count < 0:
        raise ValidationError("row_count must be non-negative.")
    if max_samples < 0:
        raise ValidationError("max_samples must be non-negative.")
    bounded_samples = list(samples or [])[:max_samples]
    return {
        "code": normalized_code,
        "severity": severity,
        "message": _validate_non_empty_string(message, "message"),
        "column": column,
        "row_count": int(row_count),
        "samples": bounded_samples,
    }


def validate_ohlcv_records(  # noqa: C901, PLR0912
    records: list[Mapping[str, object]],
    *,
    expected_symbol: str | None = None,
    issue_limit: int = 50,
    sample_limit: int = 5,
) -> list[DataQualityIssue]:
    """Return bounded OHLCV data-quality diagnostics for record mappings.

    Use this as a standard diagnostic helper before specialized data
    modules exist. It reports issues only; it never repairs, cleans,
    resamples, or persists data.

    Args:
        records: Row-like OHLCV records.
        expected_symbol: Optional expected symbol to verify when a symbol
            column exists.
        issue_limit: Maximum number of issue groups returned.
        sample_limit: Maximum samples retained per issue.

    Returns:
        Bounded list of data-quality issues.

    Side effects:
        None.
    """
    if issue_limit <= 0:
        raise ValidationError("issue_limit must be greater than zero.")
    if sample_limit < 0:
        raise ValidationError("sample_limit must be non-negative.")

    issue_map: dict[tuple[str, str | None], DataQualityIssue] = {}

    def add_issue(
        *,
        code: str,
        severity: IssueSeverity,
        message: str,
        column: str | None,
        sample: object,
    ) -> None:
        key = (code, column)
        if key not in issue_map:
            if len(issue_map) >= issue_limit:
                return
            issue_map[key] = build_data_quality_issue(
                code=code,
                severity=severity,
                message=message,
                column=column,
                row_count=0,
                samples=[],
                max_samples=sample_limit,
            )
        issue = issue_map[key]
        issue["row_count"] += 1
        if len(issue["samples"]) < sample_limit:
            issue["samples"].append(sample)

    if records and not any("symbol" in record for record in records):
        add_issue(
            code="SYMBOL_NOT_AVAILABLE",
            severity="info",
            message=(
                "Symbol verification is not available because no symbol column exists."
            ),
            column="symbol",
            sample={"verification": "not_available"},
        )

    expected = expected_symbol.strip() if expected_symbol else None
    for row_index, record in enumerate(records):
        for column in OHLC_COLUMNS:
            if column not in record:
                add_issue(
                    code="INVALID_INPUT",
                    severity="error",
                    message="Mandatory OHLC column is missing.",
                    column=column,
                    sample={"row_index": row_index, "column": column},
                )

        for column in OHLC_COLUMNS:
            value = record.get(column)
            sample = {
                "row_index": row_index,
                "column": column,
                "value": value,
            }
            if not isinstance(value, int | float):
                add_issue(
                    code="NON_NUMERIC_PRICE",
                    severity="error",
                    message="OHLC price must be numeric.",
                    column=column,
                    sample=sample,
                )
                continue
            numeric_value = float(value)
            if math.isnan(numeric_value) or math.isinf(numeric_value):
                add_issue(
                    code="NON_FINITE_PRICE",
                    severity="critical",
                    message="OHLC price must not be NaN or infinity.",
                    column=column,
                    sample=sample,
                )
            if numeric_value < 0:
                add_issue(
                    code="NEGATIVE_PRICE",
                    severity="critical",
                    message="OHLC price must not be negative.",
                    column=column,
                    sample=sample,
                )
            if numeric_value == 0:
                add_issue(
                    code="ZERO_PRICE",
                    severity="error",
                    message="OHLC price must not be zero.",
                    column=column,
                    sample=sample,
                )

        high = record.get("high")
        low = record.get("low")
        if isinstance(high, int | float) and isinstance(low, int | float):
            high_value = float(high)
            low_value = float(low)
            if not any(math.isnan(v) or math.isinf(v) for v in (high_value, low_value)):
                if low_value > high_value:
                    add_issue(
                        code="LOW_ABOVE_HIGH",
                        severity="critical",
                        message=("Low price must not be greater than high price."),
                        column="low",
                        sample={
                            "row_index": row_index,
                            "low": low,
                            "high": high,
                        },
                    )
                for column in OHLC_COLUMNS:
                    value = record.get(column)
                    if isinstance(value, int | float):
                        numeric_value = float(value)
                        if numeric_value > high_value or numeric_value < low_value:
                            add_issue(
                                code="OHLC_OUTSIDE_HIGH_LOW",
                                severity="critical",
                                message=("OHLC value must stay within high/low range."),
                                column=column,
                                sample={
                                    "row_index": row_index,
                                    "column": column,
                                    "value": value,
                                    "low": low,
                                    "high": high,
                                },
                            )

        if expected and "symbol" in record and record.get("symbol") != expected:
            add_issue(
                code="SYMBOL_MISMATCH",
                severity="warning",
                message=("Record symbol does not match expected symbol."),
                column="symbol",
                sample={
                    "row_index": row_index,
                    "expected": expected,
                    "actual": record.get("symbol"),
                },
            )

    return list(issue_map.values())[:issue_limit]


# ---------------------------------------------------------------------------
# Metadata builder
# ---------------------------------------------------------------------------


def build_metadata(
    *,
    tool_name: str,
    start_time: float | None = None,
    execution_ms: float | None = None,
    tool_version: str = DEFAULT_TOOL_VERSION,
    tool_category: str = DEFAULT_TOOL_CATEGORY,
    tool_risk_level: ToolRiskLevel = DEFAULT_TOOL_RISK_LEVEL,
    request_id: str | None = None,
    reads: bool = False,
    writes: bool = False,
    updates: bool = False,
    deletes: bool = False,
    trades: bool = False,
    requires_network: bool = False,
    writes_file: bool = False,
) -> StandardMetadata:
    """Build metadata for a standard HaruQuant tool envelope.

    Use this from official AI tools after validation and before returning
    a standard success or error envelope.

    Args:
        tool_name: Stable public tool name.
        start_time: Optional ``time.perf_counter()`` start value.
        execution_ms: Optional explicit elapsed milliseconds for
            deterministic tests. If omitted, ``start_time`` is used; if
            both are omitted, ``0.0`` is used.
        tool_version: Stable tool version.
        tool_category: Tool category such as ``utils`` or ``data``.
        tool_risk_level: Risk level: ``low``, ``medium``, ``high``, or
            ``critical``.
        request_id: Optional trace request identifier.
        reads: Whether the tool reads external or persisted state.
        writes: Whether the tool writes external or persisted state.
        updates: Whether the tool updates existing state.
        deletes: Whether the tool deletes state.
        trades: Whether the tool can trade or mutate trading state.
        requires_network: Whether the tool requires network access.
        writes_file: Whether the tool writes to the filesystem.

    Returns:
        Complete standard metadata mapping.

    Side effects:
        None.
    """
    name = _validate_non_empty_string(tool_name, "tool_name")
    version = _validate_non_empty_string(tool_version, "tool_version")
    category = _validate_non_empty_string(tool_category, "tool_category")
    if tool_risk_level not in {"low", "medium", "high", "critical"}:
        raise ValidationError("tool_risk_level must be low, medium, high, or critical.")
    if request_id is not None:
        request_id = _validate_non_empty_string(request_id, "request_id")
    if execution_ms is not None and execution_ms < 0:
        raise ValidationError("execution_ms must be greater than or equal to 0.")

    elapsed = execution_ms
    if elapsed is None and start_time is not None:
        elapsed = get_execution_ms(start_time)
    if elapsed is None:
        elapsed = 0.0

    return {
        "tool_name": name,
        "tool_version": version,
        "tool_category": category,
        "tool_risk_level": tool_risk_level,
        "request_id": request_id,
        "execution_ms": round(float(elapsed), 3),
        "reads": bool(reads),
        "writes": bool(writes),
        "updates": bool(updates),
        "deletes": bool(deletes),
        "trades": bool(trades),
        "requires_network": bool(requires_network),
        "read_only": bool(reads and not writes and not updates and not deletes),
        "writes_file": bool(writes_file),
        "modifies_database": bool(writes or updates or deletes),
        "places_trade": bool(trades),
    }


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def success_response(
    *,
    message: str,
    data: object | None,
    metadata: StandardMetadata,
) -> StandardResponse:
    """Build a standard success response envelope.

    Use this when an official AI tool completes successfully.

    Args:
        message: Human-readable success summary.
        data: JSON-compatible or caller-owned payload.
        metadata: Complete standard metadata mapping.

    Returns:
        Standard response with ``status="success"`` and ``error=None``.

    Side effects:
        Logs a structured success event.
    """
    response: StandardResponse = {
        "status": SUCCESS_STATUS,
        "message": _validate_non_empty_string(message, "message"),
        "data": data,
        "error": None,
        "metadata": metadata,
    }
    project_logger.info(
        "standard tool response built",
        extra={
            "event_name": "standard_response_success",
            "error_code": None,
        },
    )
    return response


# Contract alias matching the specified public name.
build_success_response = success_response


def error_response(
    *,
    message: str,
    code: str,
    details: str,
    metadata: StandardMetadata,
) -> StandardResponse:
    """Build a standard error response envelope.

    Use this for expected validation failures and sanitized execution
    failures in official AI tools. This helper does not raise for valid
    error inputs.

    Args:
        message: Human-readable error summary.
        code: Stable deterministic error code.
        details: Sanitized actionable error details.
        metadata: Complete standard metadata mapping.

    Returns:
        Standard response with ``status="error"`` and structured error
        payload.

    Side effects:
        Logs a structured error event.
    """
    normalized_code = normalize_error_code(code)
    response: StandardResponse = {
        "status": ERROR_STATUS,
        "message": _validate_non_empty_string(message, "message"),
        "data": None,
        "error": {
            "code": normalized_code,
            "details": _validate_non_empty_string(details, "details"),
        },
        "metadata": metadata,
    }
    project_logger.warning(
        "standard tool error response built",
        extra={
            "event_name": "standard_response_error",
            "error_code": normalized_code,
        },
    )
    return response


# Contract alias matching the specified public name.
build_error_response = error_response


def response_from_exception(
    *,
    exception: Exception,
    metadata: StandardMetadata,
    message: str = "Tool execution failed.",
) -> StandardResponse:
    """Map an exception with an optional ``code`` attribute to an error envelope.

    Use this in official tools' ``except`` blocks after logging or
    capturing the original exception. Details are limited to the
    exception type and message; callers must avoid putting secrets in
    exception messages.

    Args:
        exception: Exception to map.
        metadata: Complete standard metadata mapping.
        message: Human-readable summary for the envelope.

    Returns:
        Standard error response.

    Side effects:
        Logs the exception through the project logger.
    """
    payload = exception_to_error_payload(exception)
    project_logger.exception(
        "standard exception mapped to response",
        extra={
            "event_name": "standard_response_exception",
            "error_code": payload["code"],
        },
    )
    return error_response(
        message=message,
        code=payload["code"],
        details=payload["details"],
        metadata=metadata,
    )


def circuit_open_response(
    *,
    metadata: StandardMetadata,
    provider: str | None = None,
    details: str | None = None,
) -> StandardResponse:
    """Return a deterministic fail-fast circuit-open error envelope.

    Use this when a caller detects an open circuit and must block work
    before side effects. It does not retry or execute provider calls.

    Args:
        metadata: Complete standard metadata mapping.
        provider: Optional provider or subsystem name.
        details: Optional sanitized deterministic details.

    Returns:
        Standard error response with ``CIRCUIT_OPEN``.

    Side effects:
        Logs a structured error response event.
    """
    provider_name = provider.strip() if provider else "provider"
    safe_details = details or f"{provider_name} circuit is open; operation blocked."
    return error_response(
        message="Circuit is open; operation blocked.",
        code="CIRCUIT_OPEN",
        details=_sanitize_text(safe_details),
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_standard_response(
    response: Mapping[str, object],
) -> None:
    """Validate a standard HaruQuant tool response envelope.

    Use this in tests, official tool wrappers, and usage examples to fail
    fast when an envelope violates the public contract.

    Args:
        response: Mapping to validate.

    Returns:
        ``None`` when the response is valid.

    Raises:
        ValidationError: If top-level keys, metadata, status, message,
            or error fields are malformed.

    Side effects:
        None.
    """
    keys = set(response.keys())
    missing = STANDARD_TOP_LEVEL_KEYS - keys
    if missing:
        raise ValidationError(f"standard response is missing keys: {sorted(missing)}")  # noqa: EM102
    extra = keys - STANDARD_TOP_LEVEL_KEYS
    if extra:
        raise ValidationError(f"standard response has unexpected keys: {sorted(extra)}")  # noqa: EM102

    status = response["status"]
    if status not in {SUCCESS_STATUS, ERROR_STATUS}:
        raise ValidationError("status must be either success or error.")

    if not isinstance(response["message"], str):
        raise ValidationError("message must be a string.")

    metadata = response["metadata"]
    if not isinstance(metadata, Mapping):
        raise ValidationError("metadata must be a mapping.")
    _validate_metadata(metadata)

    error = response["error"]
    if status == SUCCESS_STATUS and error is not None:
        raise ValidationError("success responses must set error to None.")
    if status == ERROR_STATUS:
        _validate_error_payload(error)


# ---------------------------------------------------------------------------
# Error events
# ---------------------------------------------------------------------------


def build_error_event(
    *,
    code: str,
    details: str,
    request_id: str | None = None,
    event_type: str = "utility.error",
    metadata: Mapping[str, object] | None = None,
) -> ErrorEvent:
    """Build a sanitized standard error event.

    Use this before routing errors to logs, alerting, or future event
    buses. Sensitive values are redacted from details and metadata.

    Args:
        code: Stable error code.
        details: Error details to sanitize.
        request_id: Optional request identifier.
        event_type: Stable event type.
        metadata: Optional event metadata.

    Returns:
        Sanitized error event with deterministic event ID.

    Side effects:
        None.
    """
    normalized_code = normalize_error_code(code)
    safe_details = _sanitize_text(details)
    safe_metadata = _sanitize_mapping(metadata or {})
    event_material = {
        "code": normalized_code,
        "details": safe_details,
        "request_id": request_id,
        "event_type": event_type,
        "metadata": safe_metadata,
    }
    return {
        "event_id": stable_identifier(event_material, prefix="event"),
        "event_type": _validate_non_empty_string(event_type, "event_type"),
        "error": {"code": normalized_code, "details": safe_details},
        "request_id": request_id,
        "metadata": safe_metadata,
    }


# ---------------------------------------------------------------------------
# Metric label validation
# ---------------------------------------------------------------------------


def validate_metric_labels(
    labels: Mapping[str, object],
    *,
    max_labels: int = 12,
    max_value_length: int = 64,
    normalize_high_cardinality: bool = False,
) -> dict[str, str]:
    """Validate and optionally normalize safe metric labels.

    Use this before emitting metrics or creating dashboard variables.
    Sensitive labels are always rejected. High-cardinality labels are
    rejected unless deterministic normalization is explicitly requested.

    Args:
        labels: Metric label mapping.
        max_labels: Maximum label count.
        max_value_length: Maximum value length before rejection or
            normalization.
        normalize_high_cardinality: Whether high-cardinality labels
            should be converted to stable fingerprints instead of
            rejected.

    Returns:
        Safe string label mapping.

    Side effects:
        None.
    """
    if max_labels <= 0:
        raise ValidationError("max_labels must be greater than zero.")
    if max_value_length <= 0:
        raise ValidationError("max_value_length must be greater than zero.")
    if len(labels) > max_labels:
        raise ValidationError("too many metric labels.")

    safe_labels: dict[str, str] = {}
    for key, value in labels.items():
        label_key = _validate_non_empty_string(key, "label key")
        if SENSITIVE_KEY_PATTERN.search(label_key):
            raise SecurityError("sensitive metric label keys are not allowed.")
        label_value = str(value)
        if SENSITIVE_VALUE_PATTERN.search(label_value):
            raise SecurityError("sensitive metric label values are not allowed.")
        high_cardinality = (
            HIGH_CARDINALITY_LABEL_PATTERN.search(label_key) is not None
            or len(label_value) > max_value_length
        )
        if high_cardinality and not normalize_high_cardinality:
            raise ValidationError("high-cardinality metric labels are not allowed.")
        if high_cardinality:
            label_value = stable_identifier(
                {"key": label_key, "value": label_value},
                prefix="label",
            )
        safe_labels[label_key] = label_value
    return safe_labels


# ---------------------------------------------------------------------------
# Tool registry helper
# ---------------------------------------------------------------------------


def is_official_tool_allowed(
    tool_name: str,
    approved_tools: set[str],
) -> bool:
    """Return whether an official tool is approved for attachment.

    Use this in agent attachment checks before exposing a tool. It only
    answers whether a public tool name is on the approved set; it does
    not execute tools or make trading, risk, broker, portfolio, or
    strategy decisions.

    Args:
        tool_name: Public tool name.
        approved_tools: Approved public tool names.

    Returns:
        ``True`` when the tool name is approved.

    Side effects:
        None.
    """
    return _validate_non_empty_string(tool_name, "tool_name") in approved_tools


# ---------------------------------------------------------------------------
# Canonical serialization
# ---------------------------------------------------------------------------


def canonical_json(payload: object) -> str:
    """Serialize a payload into deterministic canonical JSON.

    Use this for reproducible tests, idempotency material, signatures,
    and diagnostics that need stable key ordering.

    Args:
        payload: JSON-serializable payload.

    Returns:
        Deterministic JSON string with sorted keys and compact separators.

    Raises:
        ValidationError: If the payload is not JSON serializable.

    Side effects:
        None.
    """
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            f"payload must be canonical JSON serializable: {exc}"  # noqa: EM102
        ) from exc
