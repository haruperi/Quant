"""Unit tests for schema validation helpers."""

from tools.utils import (
    validate_approval_packet,
    validate_input_schema,
    validate_mapping_schema,
    validate_numeric_range,
    validation_failed_paths,
)


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
