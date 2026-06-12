"""Unit tests for schema validation helpers."""

import pytest
from tools.utils import (
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
from tools.utils.errors import ValidationError


def test_mapping_schema_rejects_unknown_and_missing_fields() -> None:
    """Simple mapping schemas enforce required and allowed fields."""
    schema = {"required": ("symbol",), "allowed": ("symbol",)}

    assert validate_mapping_schema({"symbol": "EURUSD"}, schema)["valid"] is True
    missing = validate_mapping_schema({}, schema)
    extra = validate_mapping_schema({"symbol": "EURUSD", "bad": True}, schema)
    assert missing["valid"] is False
    assert extra["details"]["extra"] == ["bad"]


def test_official_schema_tools_return_envelopes() -> None:
    """Official validation helpers return standard envelopes."""
    response = validate_input_schema(
        {"schema_version": "1.0.0", "name": "tool"},
        {"required": ("schema_version",), "schema_version": "1.0.0"},
    )
    approval = validate_approval_packet({"approval_id": "appr_1", "action": "read"})
    failed = validate_numeric_range(float("inf"), field_name="price")

    assert response["status"] == "success"
    assert approval["status"] == "success"
    assert validation_failed_paths(failed) == []


def test_numeric_range_reports_type_and_bounds_failures() -> None:
    """Numeric validation rejects non-numeric, infinite, and out-of-range values."""
    assert validate_numeric_range("1", field_name="price")["code"] == "INVALID_INPUT"
    assert validate_numeric_range(0.5, field_name="risk", minimum=1)["code"] == (
        "VALIDATION_FAILED"
    )
    assert (
        validate_numeric_range(2, field_name="risk", maximum=1)["details"]["maximum"]
        == 1
    )


def test_schema_version_validation_paths() -> None:
    """Schema versions handle missing, compatible, incompatible, and malformed cases."""
    assert validate_schema_version(None, None)["valid"] is True
    assert validate_schema_version(None, "1.0.0")["valid"] is False
    assert validate_schema_version("1.1.0", "1.2.0")["valid"] is True
    assert (
        validate_schema_version(
            "1.0.0",
            "2.0.0",
            compatible_versions=("1.0.0",),
        )["valid"]
        is True
    )
    assert validate_schema_version("bad", "1.0.0")["code"] == "VALIDATION_FAILED"
    assert validate_schema_version("2.0.0", "1.0.0")["valid"] is False


def test_mapping_schema_rejects_bad_schema_shapes() -> None:
    """Schema helper rejects malformed required and version fields."""
    with pytest.raises(ValidationError, match="required"):
        validate_mapping_schema({"name": "x"}, {"required": "name"})

    with pytest.raises(ValidationError, match="schema version"):
        validate_mapping_schema(
            {"schema_version": 1},
            {"required": (), "schema_version": "1.0.0"},
        )


def test_required_fields_reports_null_fields() -> None:
    """Required-field validation distinguishes missing and null fields."""
    result = validate_required_fields({"name": None}, ("name", "version"))

    assert result["valid"] is False
    assert result["details"] == {"missing": ["version"], "null": ["name", "version"]}


def test_official_schema_tools_return_error_envelopes() -> None:
    """Official schema wrappers convert validation failures into standard errors."""
    response = validate_output_schema({}, {"required": ("result",)})
    handoff = validate_handoff_payload({"request_id": "req_1"})
    evidence = validate_evidence_pack({})
    registry = validate_registry_entry({"name": "tool"})
    freshness = validate_data_freshness({})

    for item in (response, handoff, evidence, registry, freshness):
        assert item["status"] == "error"
        assert item["error"] is not None
        assert item["metadata"]["tool_category"] == "utils"


def test_official_schema_tools_fail_closed_for_malformed_schemas() -> None:
    """Malformed wrapper inputs return standard errors instead of raw exceptions."""
    bad_schema = validate_input_schema({"name": "tool"}, {"required": "name"})
    bad_payload = validate_handoff_payload(object())  # type: ignore[arg-type]

    assert bad_schema["status"] == "error"
    assert bad_schema["error"] is not None
    assert bad_schema["error"]["code"] == "INVALID_INPUT"
    assert bad_payload["status"] == "error"
    assert bad_payload["error"] is not None
    assert bad_payload["error"]["code"] == "INVALID_INPUT"


def test_validation_failed_paths_extracts_single_and_many_paths() -> None:
    """Path extraction supports both a single path and a path list."""
    assert validation_failed_paths(
        {
            "valid": False,
            "message": "bad",
            "code": "VALIDATION_FAILED",
            "details": {"path": "payload.name"},
        },
    ) == ["payload.name"]
    assert validation_failed_paths(
        {
            "valid": False,
            "message": "bad",
            "code": "VALIDATION_FAILED",
            "details": {"paths": ["a", 2]},
        },
    ) == ["a", "2"]
