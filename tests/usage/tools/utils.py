"""Usage example for tools/utils/logger.py.

This script demonstrates how to import, configure, and use the structured logger.
"""

import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

# Add the project root to sys.path to allow direct execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the default root logger as exported from the tools.utils package
from tools.utils import (  # noqa: E402
    # standard imports
    SecurityError,
    build_error_event,
    build_metadata,
    canonical_json,
    circuit_open_response,
    # logger imports
    clear_trace_context,
    configure_logging,
    ensure_dir,
    ensure_parent_dir,
    error_response,
    exception_to_error_payload,
    format_utc_timestamp,
    generate_correlation_id,
    generate_event_id,
    generate_request_id,
    generate_workflow_id,
    get_logger,
    is_stale,
    logger,
    message_for,
    normalize_path,
    normalize_timestamp,
    set_trace_context,
    success_response,
    validate_ohlcv_records,
    validate_request_id,
    validate_standard_response,
    validate_timestamp_sequence,
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


if __name__ == "__main__":
    example_01_logger()
    example_02_standard_response()
    example_03_error_utilities()
    example_04_identity_utilities()
    example_05_normalization_utilities()
    example_06_path_utilities()
