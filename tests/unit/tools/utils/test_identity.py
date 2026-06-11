"""Unit tests for tools.utils.identity."""

import re
from datetime import UTC, datetime

import pytest
from tools.utils.errors import ValidationError
from tools.utils.identity import (
    DEFAULT_VERSION,
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
from tools.utils.standard import (
    build_metadata,
    success_response,
    validate_standard_response,
)

ID_HEX_PATTERN = re.compile(r"^[a-f0-9]{32}$")
PREFIXED_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*_[a-f0-9]{32}$")


def test_generate_id_returns_collision_resistant_hex_values() -> None:
    values = {generate_id() for _ in range(100)}

    assert len(values) == 100
    assert all(ID_HEX_PATTERN.fullmatch(value) for value in values)


def test_generate_prefixed_id_validates_safe_prefixes() -> None:
    generated = generate_prefixed_id("audit")

    assert generated.startswith("audit_")
    assert PREFIXED_ID_PATTERN.fullmatch(generated)
    assert validate_id(generated, expected_prefix="audit") == generated


def test_generate_prefixed_id_rejects_empty_or_unsafe_prefixes() -> None:
    for prefix in ["", " ", "Req", "request id", "req_", "req.value", "token=abc"]:
        with pytest.raises(ValidationError, match="prefix"):
            generate_prefixed_id(prefix)


def test_trace_id_generators_use_expected_prefixes_and_are_unique() -> None:
    generated = {
        generate_request_id(),
        generate_workflow_id(),
        generate_correlation_id(),
        generate_causation_id(),
        generate_event_id(),
        generate_idempotency_id(),
    }

    assert len(generated) == 6
    assert any(value.startswith("req_") for value in generated)
    assert any(value.startswith("wf_") for value in generated)
    assert any(value.startswith("corr_") for value in generated)
    assert any(value.startswith("cause_") for value in generated)
    assert any(value.startswith("event_") for value in generated)
    assert any(value.startswith("idem_") for value in generated)
    assert all(PREFIXED_ID_PATTERN.fullmatch(value) for value in generated)


def test_request_and_workflow_validators_enforce_expected_prefixes() -> None:
    request_id = generate_request_id()
    workflow_id = generate_workflow_id()

    assert validate_request_id(request_id) == request_id
    assert validate_workflow_id(workflow_id) == workflow_id

    with pytest.raises(ValidationError, match="expected prefix"):
        validate_request_id(workflow_id)

    with pytest.raises(ValidationError, match="expected prefix"):
        validate_workflow_id(request_id)


def test_validate_id_rejects_invalid_inputs() -> None:
    invalid_values: list[object] = [
        "",
        "req-123",
        "req_user-text",
        "req_zzzz",
        "req_abc token",
        datetime.now(UTC),
        object(),
    ]
    for value in invalid_values:
        with pytest.raises(ValidationError):
            validate_id(value)


def test_ensure_version_defaults_and_validates_versions() -> None:
    assert ensure_version(None) == DEFAULT_VERSION
    assert ensure_version("v0-draft") == "v0-draft"
    assert ensure_version(" 2.1.0 ") == "2.1.0"

    with pytest.raises(ValidationError, match="version"):
        ensure_version("")

    with pytest.raises(ValidationError, match="version"):
        ensure_version("v1 beta")


def test_request_id_propagates_through_standard_metadata() -> None:
    request_id = generate_request_id()
    metadata = build_metadata(
        tool_name="identity_usage",
        execution_ms=0,
        request_id=validate_request_id(request_id),
    )
    response = success_response(
        message="ok",
        data={"request_id": request_id},
        metadata=metadata,
    )

    validate_standard_response(response)
    assert response["metadata"]["request_id"] == request_id
