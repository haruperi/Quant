"""Public registry for the utilities domain.

This module exports approved public names only. It is import-safe and
side-effect free, meaning importing this package does not configure logging,
read configuration files, open network connections, or import heavy optional
dependencies.
"""

from tools.utils.logger import (
    clear_trace_context,
    configure_logging,
    get_logger,
    logger,
    set_trace_context,
)
from tools.utils.standard import (
    AlertDeduplicator,
    ConfigurationError,
    DataError,
    DataQualityIssue,
    Error,
    ErrorEvent,
    ExternalServiceError,
    SecurityError,
    StandardEnvelope,
    StandardResponse,
    ValidationError,
    build_data_quality_issue,
    build_error_event,
    build_metadata,
    canonical_json,
    circuit_open_response,
    error_name,
    error_response,
    get_execution_ms,
    is_official_tool_allowed,
    message_for,
    response_from_exception,
    stable_identifier,
    success_response,
    validate_metric_labels,
    validate_ohlcv_records,
    validate_standard_response,
)

# The following list defines the approved public names exported by the utils domain.
# Since individual modules will be implemented incrementally, this list serves
# as the source of truth for public API boundaries.
__all__ = [
    "AlertDeduplicator",
    "ConfigurationError",
    "DataError",
    "DataQualityIssue",
    "Error",
    "ErrorEvent",
    "ExternalServiceError",
    "SecurityError",
    "StandardEnvelope",
    "StandardResponse",
    "ValidationError",
    "build_data_quality_issue",
    "build_error_event",
    "build_metadata",
    "canonical_json",
    "circuit_open_response",
    "clear_trace_context",
    "configure_logging",
    "error_name",
    "error_response",
    "get_execution_ms",
    "get_logger",
    "is_official_tool_allowed",
    "logger",
    "message_for",
    "response_from_exception",
    "set_trace_context",
    "stable_identifier",
    "success_response",
    "validate_metric_labels",
    "validate_ohlcv_records",
    "validate_standard_response",
]
