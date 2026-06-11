"""Usage example for tools/utils/logger.py.

This script demonstrates how to import, configure, and use the structured logger.
"""

import sys
import tempfile
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

# Add the project root to sys.path to allow direct execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the default root logger as exported from the tools.utils package
from tools.utils import (  # noqa: E402
    FakeNotificationAdapter,
    InMemoryEventBus,
    MetricRegistry,
    NotificationRouter,
    # standard imports
    SecurityError,
    authorize_action,
    build_auth_context,
    build_error_event,
    build_event_envelope,
    build_health_snapshot,
    build_metadata,
    canonical_json,
    chunked,
    circuit_open_response,
    # logger imports
    clear_trace_context,
    configure_logging,
    ensure_dir,
    ensure_parent_dir,
    error_response,
    exception_to_error_payload,
    export_prometheus_metrics,
    format_utc_timestamp,
    generate_correlation_id,
    generate_event_id,
    generate_request_id,
    generate_workflow_id,
    get_logger,
    hash_password,
    inspect_ohlcv_quality,
    is_stale,
    load_runtime_settings,
    logger,
    message_for,
    normalize_path,
    normalize_timestamp,
    parameter_combinations,
    record_metric,
    redact_mapping,
    render_notification,
    route_error,
    set_trace_context,
    success_response,
    validate_auth_context,
    validate_input_schema,
    validate_ohlcv_records,
    validate_request_id,
    validate_standard_response,
    validate_timestamp_sequence,
    verify_password,
)


def example_01_logger() -> None:
    """Run logging system usage demonstrations."""
    print("\n" + "=" * 100)
    print("--- 1. Logging System Usage Demonstrations ---")
    print("=" * 100)
    # Log debug message using the default imported root logger
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Obtain a logger instance
    log = get_logger("usage_example")

    # 1. Local human-readable development console logging with color and file
    print("--- 1. Configuring Local Development Console Logging ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        dev_log_dir = Path(tmpdir) / "data" / "logs"
        configure_logging(
            level="DEBUG",
            use_json=False,
            use_color=True,
            log_dir_path=dev_log_dir,
        )

        log.info("This is an info message with dev configuration")

        # Set thread trace context
        set_trace_context(request_id="req-abc-999", workflow_id="wf-xyz-888")
        log.info("Message with trace identifiers active")

        # Verify file creation and output
        app_file = dev_log_dir / "app.log"
        if app_file.exists():
            print(f"Success: Dev log file created at {app_file}")
            print("Dev File Content:")
            print(app_file.read_text(encoding="utf-8").strip())

        # Reset logging configuration to close the file handler before exiting block
        # (This is necessary to release file lock on Windows)
        configure_logging(level="INFO", use_json=False, use_color=True)

    # 2. Production Structured JSON logging
    print("\n--- 2. Configuring Production JSON Logging ---")
    configure_logging(level="INFO", use_json=True)

    # Secrets and private payloads must be automatically redacted
    log.info("User logged in with password=secretpassword123 credentials.")
    log.warning("Attempted service call using api_key: key123456789.")

    clear_trace_context()

    # 3. Safe Rotating File Logging with Multi-File routing
    print("\n--- 3. Configuring Safe Rotating File Logging ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "data" / "logs"
        configure_logging(
            level="DEBUG",
            use_json=True,
            log_dir_path=log_dir,
            max_bytes=1024,
            backup_count=2,
        )

        log.debug("This is a debug message routed to debug.log and app.log")
        log.info("Access log event", extra={"event_name": "user_auth_success"})
        log.error("Database connection failed routed to errors.log")

        # Verify files creation
        print("Success: Log files created under:", log_dir)
        for name in ("app.log", "debug.log", "access.log", "errors.log"):
            p = log_dir / name
            if p.exists():
                lines = len(p.read_text().splitlines())
                print(f"- File {name} exists, lines count: {lines}")

        # Reset logging configuration to close the file handler before exiting block
        # (This is necessary to release file lock on Windows)
        configure_logging(level="INFO", use_json=True)


def example_02_standard_response() -> None:
    """Demonstrate success and error handling with standard envelopes."""
    print("\n" + "=" * 100)
    print("--- 2. Standard Response Handling (Success/Error Envelopes) ---")
    print("=" * 100)
    start_time = time.perf_counter()
    metadata = build_metadata(
        tool_name="validate_research_payload",
        start_time=start_time,
        request_id="req-usage-001",
        reads=False,
        writes=False,
        trades=False,
        requires_network=False,
    )
    success = success_response(
        message="Research payload passed validation.",
        data={"symbol": "EURUSD", "timeframe": "1h", "valid": True},
        metadata=metadata,
    )
    validate_standard_response(success)
    print(canonical_json(success))

    error_metadata = build_metadata(
        tool_name="validate_research_payload",
        execution_ms=0,
        request_id="req-usage-002",
    )
    error = error_response(
        message="Research payload failed validation.",
        code="INVALID_INPUT",
        details="symbol must be a non-empty string",
        metadata=error_metadata,
    )
    validate_standard_response(error)
    print(canonical_json(error))

    circuit = circuit_open_response(
        metadata=build_metadata(tool_name="quote_provider", execution_ms=0),
        provider="quote_provider",
    )
    validate_standard_response(circuit)
    print(canonical_json(circuit))

    issues = validate_ohlcv_records(
        [
            {"symbol": "EURUSD", "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15},
            {"symbol": "EURUSD", "open": -1.1, "high": 1.2, "low": 1.0, "close": 1.15},
        ],
        expected_symbol="EURUSD",
    )
    print(canonical_json({"issues": issues}))

    event = build_error_event(
        code="NETWORK_ERROR",
        details="provider request failed token=secret123",  # pragma: allowlist secret
        request_id="req-usage-003",
        metadata={
            "provider": "quotes",
            "api_key": "secret123",  # pragma: allowlist secret
        },
    )
    print(canonical_json(event))


def example_03_error_utilities() -> None:
    """Demonstrate typed errors and deterministic exception mapping."""
    print("\n" + "=" * 100)
    print("--- 3. Typed Errors and Deterministic Exception Mapping ---")
    print("=" * 100)
    payload = exception_to_error_payload(SecurityError("agent is not approved"))
    print(canonical_json(payload))
    print(message_for(payload["code"]))


def example_04_identity_utilities() -> None:
    """Demonstrate trace ID generation and request ID propagation."""
    print("\n" + "=" * 100)
    print("--- 4. Trace ID Generation and Request ID Propagation ---")
    print("=" * 100)
    request_id = validate_request_id(generate_request_id())
    identity_payload = {
        "request_id": request_id,
        "workflow_id": generate_workflow_id(),
        "correlation_id": generate_correlation_id(),
        "event_id": generate_event_id(),
    }
    metadata = build_metadata(
        tool_name="identity_usage",
        execution_ms=0,
        request_id=request_id,
    )
    response = success_response(
        message="Identity helpers generated trace IDs.",
        data=identity_payload,
        metadata=metadata,
    )
    validate_standard_response(response)
    print(canonical_json(response))


def example_05_normalization_utilities() -> None:
    """Demonstrate UTC-first timestamp normalization helpers."""
    print("\n" + "=" * 100)
    print("--- 5. UTC-First Timestamp Normalization Helpers ---")
    print("=" * 100)
    normalized = normalize_timestamp(
        "2026-06-11T12:30:00+02:00",
        assumed_timezone="UTC",
    )
    print(format_utc_timestamp(normalized))

    now = datetime(2026, 6, 11, 10, 45, tzinfo=UTC)
    issues = validate_timestamp_sequence(
        [
            "2026-06-11T10:00:00Z",
            "2026-06-11T10:00:00Z",
            "2026-06-11T09:59:00Z",
        ],
    )
    print(
        canonical_json(
            {
                "is_stale": is_stale(normalized, max_age_seconds=60, now=now),
                "timestamp_issues": issues,
            },
        ),
    )


def example_06_path_utilities() -> None:
    """Demonstrate safe path normalization and explicit directory creation."""
    print("\n" + "=" * 100)
    print("--- 6. Safe Path Normalization and Explicit Directory Creation ---")
    print("=" * 100)
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        normalized = normalize_path("audit/events/event.json", base_dir=base_dir)
        cache_dir = ensure_dir("cache", base_dir=base_dir)
        artifact_path = ensure_parent_dir(
            "artifacts/run-001/result.json",
            base_dir=base_dir,
        )
        print(
            canonical_json(
                {
                    "normalized": str(normalized.relative_to(base_dir)),
                    "cache_exists": cache_dir.is_dir(),
                    "artifact_parent_exists": artifact_path.parent.is_dir(),
                },
            ),
        )


def example_07_dataframe_tools() -> None:
    """Demonstrate dataframe helper primitives and lazy optional dependency errors."""
    print("\n" + "=" * 100)
    print("--- 7. Dataframe Helper Primitives ---")
    print("=" * 100)
    print(
        canonical_json(
            {
                "chunks": chunked([1, 2, 3], size=2),
                "parameter_combinations": parameter_combinations(
                    {"fast": [5, 10], "slow": [20]},
                ),
            },
        ),
    )


def example_08_schema_validation() -> None:
    """Demonstrate schema validation official tool envelopes."""
    print("\n" + "=" * 100)
    print("--- 8. Schema Validation Helpers ---")
    print("=" * 100)
    schema_response = validate_input_schema(
        {"schema_version": "1.0.0", "name": "demo"},
        {"required": ("schema_version",), "schema_version": "1.0.0"},
        request_id="req-usage-schema",
    )
    validate_standard_response(schema_response)
    print(canonical_json(schema_response))


def example_09_data_quality() -> None:
    """Demonstrate OHLCV diagnostics and lazy pandas failure behavior."""
    print("\n" + "=" * 100)
    print("--- 9. Data Quality Diagnostics ---")
    print("=" * 100)
    issues = validate_ohlcv_records(
        [
            {"symbol": "EURUSD", "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15},
            {"symbol": "EURUSD", "open": 0, "high": 1.2, "low": 1.0, "close": 1.15},
        ],
        expected_symbol="EURUSD",
    )
    print(canonical_json({"record_issues": issues}))
    try:
        inspect_ohlcv_quality(object())
    except Exception as exc:  # noqa: BLE001
        print(canonical_json(exception_to_error_payload(exc)))


def example_10_security() -> None:
    """Demonstrate security redaction and password hashing helpers."""
    print("\n" + "=" * 100)
    print("--- 10. Security Helpers ---")
    print("=" * 100)
    password_hash = hash_password("usage-password", salt=b"1234567890123456")
    print(
        canonical_json(
            {
                "redacted": redact_mapping({"api_key": "secret", "safe": "ok"}),
                "password_verified": verify_password("usage-password", password_hash),
            },
        ),
    )


def example_11_settings() -> None:
    """Demonstrate immutable runtime settings loading."""
    print("\n" + "=" * 100)
    print("--- 11. Runtime Settings Helpers ---")
    print("=" * 100)
    settings = load_runtime_settings(
        {
            "HARUQUANT_HOME": str(Path.cwd() / ".haruquant"),
            "ALLOW_LIVE_MUTATIONS": "false",
            "STRICT_VALIDATION": "true",
        },
    )
    print(
        canonical_json(
            {
                "environment": settings.environment,
                "allow_live_mutations": settings.allow_live_mutations,
                "strict_validation": settings.strict_validation,
            },
        ),
    )


def example_12_auth() -> None:
    """Demonstrate auth context validation and deny-by-default decisions."""
    print("\n" + "=" * 100)
    print("--- 12. Auth Helpers ---")
    print("=" * 100)
    request_id = generate_request_id()
    workflow_id = generate_workflow_id()
    context = build_auth_context(
        principal_id="usage-agent",
        principal_type="agent",
        roles={"researcher"},
        permissions={"utils.read"},
        scopes={"usage"},
        request_id=request_id,
        workflow_id=workflow_id,
    )
    decision = authorize_action(context, required_permissions={"utils.read"})
    response = validate_auth_context(
        {
            "principal_id": context.principal_id,
            "principal_type": context.principal_type,
            "roles": list(context.roles),
            "permissions": list(context.permissions),
            "scopes": list(context.scopes),
            "request_id": request_id,
            "workflow_id": workflow_id,
        },
    )
    print(canonical_json({"authorized": decision.allowed, "reason": decision.reason}))
    print(canonical_json(response))


def example_13_event_bus() -> None:
    """Demonstrate sanitized Event Bus publish behavior."""
    print("\n" + "=" * 100)
    print("--- 13. Event Bus Helpers ---")
    print("=" * 100)
    bus = InMemoryEventBus()
    event = build_event_envelope(
        event_type="utility.usage",
        source="usage_example",
        payload={"token": "secret", "status": "ok"},
    )
    print(canonical_json(asdict(bus.publish(event))))


def example_14_error_routing() -> None:
    """Demonstrate sanitized error routing."""
    print("\n" + "=" * 100)
    print("--- 14. Error Routing Helpers ---")
    print("=" * 100)
    result = route_error(
        SecurityError("token=secret should be redacted"),
        source="usage_example",
    )
    print(canonical_json(asdict(result)))


def example_15_notifications() -> None:
    """Demonstrate fake/local notification routing."""
    print("\n" + "=" * 100)
    print("--- 15. Notification Helpers ---")
    print("=" * 100)
    adapter = FakeNotificationAdapter(channel="desktop")
    router = NotificationRouter(adapters={"desktop": adapter})
    notification = router.route(
        channel="desktop",
        title="Usage example",
        body="token=secret",
        dedupe_key="usage-example",
    )
    print(canonical_json(asdict(notification)))
    print(canonical_json(render_notification(title="Notice", body="**hello**")))


def example_16_observability() -> None:
    """Demonstrate metrics export and health snapshots."""
    print("\n" + "=" * 100)
    print("--- 16. Observability Helpers ---")
    print("=" * 100)
    registry = MetricRegistry()
    record_metric(
        registry,
        name="haruquant_usage_total",
        kind="counter",
        value=1,
        labels={"component": "utils"},
    )
    print(export_prometheus_metrics(registry))
    print(canonical_json(build_health_snapshot(component="utils", status="healthy")))


if __name__ == "__main__":
    example_01_logger()
    example_02_standard_response()
    example_03_error_utilities()
    example_04_identity_utilities()
    example_05_normalization_utilities()
    example_06_path_utilities()
    example_07_dataframe_tools()
    example_08_schema_validation()
    example_09_data_quality()
    example_10_security()
    example_11_settings()
    example_12_auth()
    example_13_event_bus()
    example_14_error_routing()
    example_15_notifications()
    example_16_observability()
