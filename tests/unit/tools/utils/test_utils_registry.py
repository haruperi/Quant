"""Unit tests for the tools/utils registry."""

import sys


def test_utils_registry_exports() -> None:
    """Verify that only the approved public names are declared in __all__."""
    import tools.utils

    expected_exports = {
        "APPROVED_ERROR_CODES",
        "AlertDeduplicator",
        "ClockDriftStatus",
        "ConfigurationError",
        "DEFAULT_VERSION",
        "DEFAULT_TIMEZONE",
        "DataError",
        "DataQualityIssue",
        "Error",
        "ErrorPayload",
        "ErrorEvent",
        "ExternalServiceError",
        "ID_PREFIXES",
        "SecurityError",
        "StandardEnvelope",
        "StandardResponse",
        "TimestampIssue",
        "UTC",
        "ValidationError",
        "build_metadata",
        "build_data_quality_issue",
        "build_error_event",
        "canonical_json",
        "check_clock_drift",
        "clear_trace_context",
        "circuit_open_response",
        "code_for_exception",
        "configure_logging",
        "details_for_exception",
        "ensure_version",
        "error_name",
        "error_response",
        "ensure_dir",
        "ensure_parent_dir",
        "exception_to_error_payload",
        "format_utc_timestamp",
        "generate_causation_id",
        "generate_correlation_id",
        "generate_event_id",
        "generate_id",
        "generate_idempotency_id",
        "generate_prefixed_id",
        "generate_request_id",
        "generate_workflow_id",
        "get_execution_ms",
        "get_logger",
        "is_official_tool_allowed",
        "is_stale",
        "logger",
        "message_for",
        "normalize_error_code",
        "normalize_path",
        "normalize_timestamp",
        "normalize_timestamp_column",
        "normalize_timestamp_sequence",
        "parse_datetime",
        "raise_for_invalid_code",
        "response_from_exception",
        "set_trace_context",
        "stable_identifier",
        "success_response",
        "to_naive_utc",
        "to_utc_datetime",
        "utc_now",
        "validate_error_payload",
        "validate_id",
        "validate_metric_labels",
        "validate_ohlcv_records",
        "validate_request_id",
        "validate_standard_response",
        "validate_timestamp_sequence",
        "validate_workflow_id",
    }

    assert hasattr(tools.utils, "__all__")
    assert set(tools.utils.__all__) == expected_exports


def test_registry_import_side_effects() -> None:
    """Verify that importing tools.utils does not run unwanted side-effects.

    Specifically, check that heavy modules like pandas, cryptography, etc.
    are not loaded into sys.modules just by importing tools.utils.
    """
    # Ensure tools.utils is not yet imported (or clean it if it is)
    if "tools.utils" in sys.modules:
        del sys.modules["tools.utils"]

    import tools.utils  # noqa: F401

    # Assert that heavy optional libraries are not eagerly loaded
    assert "pandas" not in sys.modules
    assert "cryptography" not in sys.modules
    assert "dotenv" not in sys.modules
