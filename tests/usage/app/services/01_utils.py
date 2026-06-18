"""Usage examples for all shared utility functions in app/utils.

Demonstrates the unified public registry exports for logging, standard envelopes,
identities, normalization, security, dataframe tools, data quality, schema validation,
event buses, circuit breakers, notifications, and error handling.
"""

# ruff: noqa: E501, E402
import sys
from pathlib import Path

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[4])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import tempfile
from datetime import timedelta
from typing import Any, cast

import pandas as pd
from app.utils import (
    CircuitBreaker,
    FakeNotificationAdapter,
    InMemoryEventBus,
    NotificationRouter,
    ValidationError,
    align_dataframe_datetime,
    build_event_envelope,
    build_metadata,
    canonical_json,
    circuit_open_response,
    clear_trace_context,
    configure_logging,
    decrypt_text,
    encrypt_text,
    ensure_parent_dir,
    error_response,
    format_utc_timestamp,
    generate_correlation_id,
    generate_encryption_key,
    generate_event_id,
    generate_idempotency_id,
    generate_prefixed_id,
    generate_request_id,
    generate_workflow_id,
    hash_password,
    inspect_ohlcv_quality,
    is_stale,
    logger,
    parameter_combinations,
    parse_datetime,
    publish_event,
    redact_payload,
    response_from_exception,
    route_notification,
    serialize_dataframe_records,
    set_trace_context,
    success_response,
    to_naive_utc,
    to_utc_datetime,
    utc_now,
    validate_id,
    validate_input_schema,
    validate_ohlcv_quality,
    validate_request_id,
    validate_standard_response,
    validate_timestamp_sequence,
    validate_workflow_id,
    verify_password,
)


def example_01_logging_and_tracing() -> None:
    """Demonstrate configure_logging, logger usage, and trace context propagation."""
    print("\n--- 1. Logging & Tracing Demo ---")
    # Configure logging for local run
    configure_logging(level="INFO")

    # Set context propagation parameters
    set_trace_context(
        request_id=generate_request_id(),
        workflow_id=generate_workflow_id(),
        correlation_id=generate_correlation_id(),
    )

    logger.info(
        "Demo log showing trace context injection", extra={"metric_type": "telemetry"}
    )

    # Reset trace contexts
    clear_trace_context()
    logger.info("Context cleared; this log will have no trace metadata fields")


def example_02_standard_responses() -> None:
    """Demonstrate standardized success, error, and exception response envelope creation."""
    print("\n--- 2. Standard Responses Demo ---")
    # Success envelope
    meta_success = build_metadata(tool_name="get_rates_tool")
    resp = success_response(
        data={"rates": {"EURUSD": 1.10}},
        message="Rates loaded successfully.",
        metadata=meta_success,
    )
    print("Success Envelope:", canonical_json(resp))
    validate_standard_response(resp)

    # Error envelope
    meta_err = build_metadata(tool_name="get_rates_tool")
    err = error_response(
        code="VALIDATION_FAILED",
        message="Required parameter 'symbol' is missing.",
        details="The symbol query parameter was empty.",
        metadata=meta_err,
    )
    print("Error Envelope:", canonical_json(err))
    validate_standard_response(err)

    # Exception envelope conversion
    try:
        raise ValueError("Simulated connection timeout")  # noqa: TRY301
    except ValueError as ex:
        meta_ex = build_metadata(tool_name="fetch_ticks")
        ex_resp = response_from_exception(exception=ex, metadata=meta_ex)
        print("Exception Envelope:", canonical_json(ex_resp))


def example_03_identities() -> None:
    """Demonstrate prefix-validated, collision-resistant ULID/UUID identifiers."""
    print("\n--- 3. Prefixed Identifiers Demo ---")
    req_id = generate_request_id()
    wf_id = generate_workflow_id()
    event_id = generate_event_id()
    idemp_id = generate_idempotency_id()
    custom_id = generate_prefixed_id("strategy")

    print(f"Generated Request ID:      {req_id}")
    print(f"Generated Workflow ID:     {wf_id}")
    print(f"Generated Event ID:        {event_id}")
    print(f"Generated Idempotency ID:  {idemp_id}")
    print(f"Generated Custom ID:       {custom_id}")

    # Validation checks
    assert validate_request_id(req_id) == req_id
    assert validate_workflow_id(wf_id) == wf_id
    assert validate_id(custom_id, expected_prefix="strategy") == custom_id
    print("All ID validations completed successfully.")


def example_04_datetimes_and_normalizations() -> None:
    """Demonstrate timezone-aware UTC datetime parsing, staleness checks, and drift detection."""
    print("\n--- 4. Datetime Normalizations Demo ---")
    now_utc = utc_now()
    print(f"Current UTC Timestamp: {now_utc}")
    print(f"Formatted UTC:         {format_utc_timestamp(now_utc)}")

    # Parsing variations
    parsed_date = parse_datetime("2026-06-16T12:00:00Z")
    naive_date = to_naive_utc(parsed_date)
    utc_date = to_utc_datetime(naive_date)
    assert parsed_date == utc_date
    print(f"Successfully normalized '{parsed_date}' to naive and back to aware UTC.")

    # Staleness check (e.g. 5 minutes ago)
    old_time = utc_now() - timedelta(minutes=10)
    assert is_stale(old_time, max_age_seconds=300) is True
    print("Staleness checks successfully validated.")

    # Sequence checks
    timestamps = [
        "2026-06-16T12:00:00Z",
        "2026-06-16T12:01:00Z",
        "2026-06-16T12:02:00Z",
    ]
    validate_timestamp_sequence(timestamps)
    print("Timestamp sequence validated successfully.")


def example_05_security_and_redaction() -> None:
    """Demonstrate secure hashing, text encryption, and key redaction."""
    print("\n--- 5. Security & Redaction Demo ---")
    # Password hashing
    password = "SuperSecretPassword123"  # pragma: allowlist secret
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    print("Password hash verified successfully.")

    # Text encryption
    key = generate_encryption_key()
    plain_text = "Highly confidential strategy parameters"
    cipher_text = encrypt_text(plain_text, key=key)
    decrypted = decrypt_text(cipher_text, key=key)
    assert plain_text == decrypted
    print(f"Encrypted message: {cipher_text[:20]}... Decrypted: '{decrypted}'")

    # Sensitive key redaction
    payload = {
        "api_key": "1234-abcd-5678",  # pragma: allowlist secret
        "username": "haru_quant",
        "db_password": "super_secret_db_password",  # pragma: allowlist secret
    }
    redacted = redact_payload(payload)
    print("Redacted Payload:", redacted)


def example_06_dataframe_and_combinations() -> None:
    """Demonstrate lazy alignment, data mapping, and grid parameter combinatorics."""
    print("\n--- 6. DataFrames & Combinations Demo ---")
    # Parameter grid optimization helpers
    grid = {
        "fast_ema": [5, 10],
        "slow_ema": [20, 30],
    }
    combinations = parameter_combinations(grid)
    print(f"Parameter combinations for grid: {combinations}")

    # DataFrame alignment and conversion
    df = pd.DataFrame(
        [
            {"timestamp": "2026-06-16 10:00:00", "close": 1.1000},
            {"timestamp": "2026-06-16 10:01:00", "close": 1.1005},
        ]
    )
    aligned_df = align_dataframe_datetime(df, timestamp_column="timestamp")
    records = serialize_dataframe_records(aligned_df)
    print("Serialized records:", records)


def example_07_data_quality() -> None:
    """Demonstrate bar checks, volume checks, and data profiles creation."""
    print("\n--- 7. Data Quality Checking Demo ---")
    records = [
        {
            "timestamp": "2026-06-16T10:00:00Z",
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.10,
            "volume": 100,
        },
        {
            "timestamp": "2026-06-16T10:01:00Z",
            "open": 1.10,
            "high": 1.12,
            "low": 1.08,
            "close": 1.11,
            "volume": 200,
        },
    ]

    df = pd.DataFrame(records)
    res = inspect_ohlcv_quality(df)
    issues = cast("list[Any]", res.get("issues", []))
    print(f"Data Quality Profiles: Passed={res['passed']}, Issues Count={len(issues)}")
    resp = validate_ohlcv_quality(df)
    print("Validate OHLCV Quality response status:", resp["status"])


def example_08_validations() -> None:
    """Demonstrate input and output validation checks."""
    print("\n--- 8. Schema Validation Demo ---")
    schema = {
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "minLength": 3},
            "quantity": {"type": "number", "minimum": 0.1},
        },
        "required": ["symbol", "quantity"],
    }

    # Validate correct request
    valid_input = {"symbol": "EURUSD", "quantity": 1.5}
    validate_input_schema(valid_input, schema)
    print("Valid inputs passed validation successfully.")

    # Validate incorrect request
    invalid_input = {"symbol": "EU", "quantity": 0.0}
    try:
        validate_input_schema(invalid_input, schema)
    except ValidationError as ex:
        print(f"Caught schema validation expected error: {ex}")


def example_09_event_bus() -> None:
    """Demonstrate internal Event Bus publisher/subscriber pattern."""
    print("\n--- 9. Event Bus Pub/Sub Demo ---")
    bus = InMemoryEventBus(max_queue_size=100)

    # Subscribe to target channel
    def handle_signal(envelope: Any) -> None:
        print(
            f"Subscriber received event '{envelope['event_type']}' with payload: {envelope['payload']}"
        )

    bus.subscribe("strategy.signals", handle_signal)

    # Dispatch/Publish signal event
    envelope = build_event_envelope(
        event_type="strategy.signals",
        source="strategy_runner",
        payload={"action": "BUY", "symbol": "EURUSD", "size": 0.1},
    )
    publish_event(bus, envelope)


def example_10_circuit_breakers() -> None:
    """Demonstrate circuit-breaker triggers and telemetry counters."""
    print("\n--- 10. Circuit Breakers & Metrics Demo ---")
    cb = CircuitBreaker(name="demo_breaker", failure_threshold=2, cooldown_seconds=1.0)

    # First attempt: success
    if cb.allow_request():
        print("First request allowed.")
        cb.record_success()

    # Throw mock failures to open circuit
    cb.record_failure()
    cb.record_failure()

    # Next attempt should block execution
    if not cb.allow_request():
        print("Third request blocked (circuit is OPEN).")
        meta = build_metadata(tool_name="get_data")
        resp = circuit_open_response(metadata=meta)
        print("Circuit Open Response Envelope:", canonical_json(resp))


def example_11_notifications() -> None:
    """Demonstrate rendered alerts and mock channel routing."""
    print("\n--- 11. Notifications Router Demo ---")
    from app.utils.notifications import NotificationAdapter, NotificationChannel

    adapters: dict[NotificationChannel, NotificationAdapter] = {
        "desktop": FakeNotificationAdapter(channel="desktop"),
    }
    router = NotificationRouter(adapters=adapters)

    # Route message
    res = route_notification(
        router,
        channel="desktop",
        title="System warning",
        body="Disk space low on server A.",
    )
    print(f"Routed Notification Status: {res.status}, Delivered: {res.channel}")


def example_12_paths() -> None:
    """Demonstrate path creation and directory checks."""
    print("\n--- 12. Safe Paths Demo ---")
    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = Path(temp_dir) / "data" / "raw" / "EURUSD.csv"

        # Automatically create nested parent directories safely
        ensure_parent_dir(target_file)

        # Write dummy data to confirm
        with target_file.open("w") as f:
            f.write("timestamp,close\n2026-06-16T12:00:00Z,1.1000")

        assert target_file.exists()
        print(f"Verified safe paths creation for target file: '{target_file}'")


if __name__ == "__main__":
    print("==================================================")
    print("STARTING SHRED UTILITIES DEMO SCRIPT (01_utils.py)")
    print("==================================================")

    example_01_logging_and_tracing()
    example_02_standard_responses()
    example_03_identities()
    example_04_datetimes_and_normalizations()
    example_05_security_and_redaction()
    example_06_dataframe_and_combinations()
    example_07_data_quality()
    example_08_validations()
    example_09_event_bus()
    example_10_circuit_breakers()
    example_11_notifications()
    example_12_paths()

    print("==================================================")
    print("DEMO SCRIPT EXECUTED SUCCESSFULLY")
    print("==================================================")
