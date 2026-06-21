"""Public registry for the utilities domain.

This module exposes only approved public names. It is import-safe and
side-effect free: importing it does not configure logging, read
configuration files, open network connections, or load heavy optional
dependencies such as pydantic-settings (dotenv).

Lightweight modules are imported eagerly. ``app.utils.settings`` is
deferred via ``__getattr__`` because ``pydantic_settings`` triggers
dotenv scanning at class-body evaluation time.

Compatibility review (v8): all public names in ``__all__`` are stable.
Removals or renames require a new versioned specification and a registry
review before merging.

Export groups
-------------
Eager:
    auth, data_quality, dataframe_tools, errors, event_bus, identity,
    logger, normalization, notifications, observability, paths,
    security, standard, validations
Lazy:
    settings
"""

from __future__ import annotations

from importlib import import_module

# ── auth.py exports ──────────────────────────────────────────────────────
from app.utils.auth import (
    AuthContext,
    AuthorizationDecision,
    authorize_action,
    build_auth_context,
    require_authorization,
    validate_auth_context,
)

# ── data_quality.py exports ──────────────────────────────────────────────
from app.utils.data_quality import (
    QualityIssue,
    QualityProfile,
    inspect_ohlcv_quality,
    prepare_ohlcv_data,
    validate_ohlcv_quality,
)

# ── dataframe_tools.py exports ───────────────────────────────────────────
from app.utils.dataframe_tools import (
    OHLC_COLUMNS,
    OHLCV_COLUMNS,
    align_dataframe_datetime,
    align_dataframe_time_index,
    bar_to_record,
    bars_to_records,
    chunk_sequence,
    chunked,
    compare_dataframes,
    compare_ohlc,
    compare_ohlcv,
    dataframe_columns,
    generate_parameter_combinations,
    iter_dataframe_records,
    parameter_combinations,
    serialize_dataframe_records,
)

# ── errors.py exports ────────────────────────────────────────────────────
from app.utils.errors import (
    APPROVED_ERROR_CODES,
    ConfigurationError,
    DataError,
    Error,
    ErrorPayload,
    ErrorRouter,
    ErrorRouteResult,
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
    route_error,
    validate_error_payload,
)

# ── event_bus.py exports ─────────────────────────────────────────────────
from app.utils.event_bus import (
    EventEnvelope,
    InMemoryEventBus,
    PublishResult,
    build_event_envelope,
    publish_event,
)

# ── identity.py exports ──────────────────────────────────────────────────
from app.utils.identity import (
    DEFAULT_VERSION,
    ID_PREFIXES,
    ensure_version,
    generate_causation_id,
    generate_correlation_id,
    generate_event_id,
    generate_id,
    generate_idempotency_id,
    generate_prefixed_id,
    generate_request_id,
    generate_workflow_id,
    validate_id,
    validate_request_id,
    validate_workflow_id,
)

# ── logger.py exports ────────────────────────────────────────────────────
from app.utils.logger import (
    clear_trace_context,
    configure_logging,
    get_logger,
    logger,
    set_trace_context,
)

# ── normalization.py exports ─────────────────────────────────────────────
from app.utils.normalization import (
    DEFAULT_TIMEZONE,
    UTC,
    ClockDriftStatus,
    TimestampIssue,
    check_clock_drift,
    format_timestamp,
    format_utc_timestamp,
    is_stale,
    normalize_timestamp,
    normalize_timestamp_column,
    normalize_timestamp_sequence,
    parse_datetime,
    to_naive_utc,
    to_utc_datetime,
    utc_now,
    validate_timestamp_sequence,
)

# ── notifications.py exports ─────────────────────────────────────────────
from app.utils.notifications import (
    DesktopNotificationAdapter,
    EmailNotificationAdapter,
    FakeNotificationAdapter,
    NotificationMessage,
    NotificationResult,
    NotificationRouter,
    TelegramNotificationAdapter,
    broadcast_notification,
    render_notification,
    route_notification,
)

# ── observability.py exports ─────────────────────────────────────────────
from app.utils.observability import (
    GRAFANA_DASHBOARD_EXPECTATIONS,
    CircuitBreaker,
    HealthSnapshot,
    MetricRecord,
    MetricRegistry,
    build_health_snapshot,
    check_clock_drift_health,
    export_prometheus_metrics,
    record_metric,
    record_tool_call_metric,
)

# ── paths.py exports ─────────────────────────────────────────────────────
from app.utils.paths import (
    ensure_dir,
    ensure_parent_dir,
    normalize_path,
    safe_join,
    validate_path_within_root,
)

# ── security.py exports ──────────────────────────────────────────────────
from app.utils.security import (
    MAX_REDACTION_DEPTH,
    SECRET_VERSION_NOT_FOUND,
    SENSITIVE_KEY_PATTERN,
    RedactionDiagnostics,
    SecretVersion,
    classify_secret_key,
    decrypt_text,
    decrypt_value,
    encrypt_text,
    encrypt_value,
    generate_encryption_key,
    hash_password,
    load_encryption_key,
    redact_mapping,
    redact_mapping_with_diagnostics,
    redact_payload,
    redact_text,
    redact_value,
    select_active_secret_version,
    verify_password,
)

# ── standard.py exports ──────────────────────────────────────────────────
from app.utils.standard import (
    AlertDeduplicator,
    DataQualityIssue,
    ErrorEvent,
    StandardEnvelope,
    StandardResponse,
    ToolError,
    ToolMetadata,
    build_data_quality_issue,
    build_error_event,
    build_error_response,
    build_metadata,
    build_success_response,
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

# ── validations.py exports ───────────────────────────────────────────────
from app.utils.validations import (
    VALID_ENVIRONMENT_MODES,
    VALID_RISK_LEVELS,
    VALIDATION_FAILED,
    ValidationResult,
    validate_approval_packet,
    validate_data_freshness,
    validate_evidence_pack,
    validate_handoff_payload,
    validate_input_schema,
    validate_mapping_schema,
    validate_numeric_range,
    validate_output_schema,
    validate_registry_entry,
    validate_required_fields,
    validate_schema_version,
    validation_failed_paths,
)

# ── settings.py exports (lazy — avoids eager pydantic-settings / dotenv) ─
_LAZY_SETTINGS_EXPORTS: frozenset[str] = frozenset(
    {
        "CONFIGURATION_ERROR",
        "HARUQUANT_HOME",
        "HaruQuantConfigurationError",
        "Settings",
        "load_config",
        "settings",
        "validate_config",
    }
)

__all__ = [
    "APPROVED_ERROR_CODES",
    "CONFIGURATION_ERROR",
    "DEFAULT_TIMEZONE",
    "DEFAULT_VERSION",
    "GRAFANA_DASHBOARD_EXPECTATIONS",
    "HARUQUANT_HOME",
    "ID_PREFIXES",
    "MAX_REDACTION_DEPTH",
    "OHLCV_COLUMNS",
    "OHLC_COLUMNS",
    "SECRET_VERSION_NOT_FOUND",
    "SENSITIVE_KEY_PATTERN",
    "UTC",
    "VALIDATION_FAILED",
    "VALID_ENVIRONMENT_MODES",
    "VALID_RISK_LEVELS",
    "AlertDeduplicator",
    "AuthContext",
    "AuthorizationDecision",
    "CircuitBreaker",
    "ClockDriftStatus",
    "ConfigurationError",
    "DataError",
    "DataQualityIssue",
    "DesktopNotificationAdapter",
    "EmailNotificationAdapter",
    "Error",
    "ErrorEvent",
    "ErrorPayload",
    "ErrorRouteResult",
    "ErrorRouter",
    "EventEnvelope",
    "ExternalServiceError",
    "FakeNotificationAdapter",
    "HaruQuantConfigurationError",
    "HealthSnapshot",
    "InMemoryEventBus",
    "MetricRecord",
    "MetricRegistry",
    "NotificationMessage",
    "NotificationResult",
    "NotificationRouter",
    "PublishResult",
    "QualityIssue",
    "QualityProfile",
    "RedactionDiagnostics",
    "SecretVersion",
    "SecurityError",
    "Settings",
    "StandardEnvelope",
    "StandardResponse",
    "TelegramNotificationAdapter",
    "TimestampIssue",
    "ToolError",
    "ToolMetadata",
    "ValidationError",
    "ValidationResult",
    "align_dataframe_datetime",
    "align_dataframe_time_index",
    "authorize_action",
    "bar_to_record",
    "bars_to_records",
    "broadcast_notification",
    "build_auth_context",
    "build_data_quality_issue",
    "build_error_event",
    "build_error_response",
    "build_event_envelope",
    "build_health_snapshot",
    "build_metadata",
    "build_success_response",
    "canonical_json",
    "check_clock_drift",
    "check_clock_drift_health",
    "chunk_sequence",
    "chunked",
    "circuit_open_response",
    "classify_secret_key",
    "clear_trace_context",
    "code_for_exception",
    "compare_dataframes",
    "compare_ohlc",
    "compare_ohlcv",
    "configure_logging",
    "dataframe_columns",
    "decrypt_text",
    "decrypt_value",
    "details_for_exception",
    "encrypt_text",
    "encrypt_value",
    "ensure_dir",
    "ensure_parent_dir",
    "ensure_version",
    "error_name",
    "error_response",
    "exception_to_error_payload",
    "export_prometheus_metrics",
    "format_timestamp",
    "format_utc_timestamp",
    "generate_causation_id",
    "generate_correlation_id",
    "generate_encryption_key",
    "generate_event_id",
    "generate_id",
    "generate_idempotency_id",
    "generate_parameter_combinations",
    "generate_prefixed_id",
    "generate_request_id",
    "generate_workflow_id",
    "get_execution_ms",
    "get_logger",
    "hash_password",
    "inspect_ohlcv_quality",
    "is_official_tool_allowed",
    "is_stale",
    "iter_dataframe_records",
    "load_config",
    "load_encryption_key",
    "logger",
    "message_for",
    "normalize_error_code",
    "normalize_path",
    "normalize_timestamp",
    "normalize_timestamp_column",
    "normalize_timestamp_sequence",
    "parameter_combinations",
    "parse_datetime",
    "prepare_ohlcv_data",
    "publish_event",
    "raise_for_invalid_code",
    "record_metric",
    "record_tool_call_metric",
    "redact_mapping",
    "redact_mapping_with_diagnostics",
    "redact_payload",
    "redact_text",
    "redact_value",
    "render_notification",
    "require_authorization",
    "response_from_exception",
    "route_error",
    "route_notification",
    "safe_join",
    "select_active_secret_version",
    "serialize_dataframe_records",
    "set_trace_context",
    "settings",
    "stable_identifier",
    "success_response",
    "to_naive_utc",
    "to_utc_datetime",
    "utc_now",
    "validate_approval_packet",
    "validate_auth_context",
    "validate_config",
    "validate_data_freshness",
    "validate_error_payload",
    "validate_evidence_pack",
    "validate_handoff_payload",
    "validate_id",
    "validate_input_schema",
    "validate_mapping_schema",
    "validate_metric_labels",
    "validate_numeric_range",
    "validate_ohlcv_quality",
    "validate_ohlcv_records",
    "validate_output_schema",
    "validate_path_within_root",
    "validate_registry_entry",
    "validate_request_id",
    "validate_required_fields",
    "validate_schema_version",
    "validate_standard_response",
    "validate_timestamp_sequence",
    "validate_workflow_id",
    "validation_failed_paths",
    "verify_password",
]


def __getattr__(name: str) -> object:
    """Lazily resolve settings exports to avoid eager dotenv loading.

    Resolved values are cached in the module's global namespace so that
    subsequent attribute accesses bypass this function entirely.

    Args:
        name: The attribute name being accessed on this package.

    Returns:
        The requested public symbol from ``app.utils.settings``.

    Raises:
        AttributeError: If ``name`` is not an approved public export.
    """
    if name in _LAZY_SETTINGS_EXPORTS:
        module = import_module("app.utils.settings")
        value: object = getattr(module, name)
        globals()[name] = value
        return value
    message = f"module 'app.utils' has no attribute {name!r}"
    raise AttributeError(message)
