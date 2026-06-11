"""Schema validation helpers and official read-only validation tools."""

from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict

from tools.utils.errors import ValidationError
from tools.utils.standard import (
    StandardResponse,
    build_metadata,
    error_response,
    success_response,
)

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL: Literal["low"] = "low"
SEMVER_PART_COUNT = 3


class ValidationResult(TypedDict):
    """Native validation result."""

    valid: bool
    message: str
    code: str
    details: dict[str, object]


def _ok(message: str = "Validation passed.") -> ValidationResult:
    """Return a successful validation result."""
    return {"valid": True, "message": message, "code": "OK", "details": {}}


def _fail(
    message: str, *, code: str, details: Mapping[str, object]
) -> ValidationResult:
    """Return a failed validation result."""
    return {
        "valid": False,
        "message": message,
        "code": code,
        "details": dict(details),
    }


def validate_numeric_range(
    value: object,
    *,
    field_name: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> ValidationResult:
    """Validate a finite numeric value against inclusive bounds."""
    if not isinstance(value, int | float) or isinstance(value, bool):
        return _fail(
            f"{field_name} must be numeric.",
            code="INVALID_INPUT",
            details={"field": field_name, "value": value},
        )
    numeric = float(value)
    if math.isnan(numeric) or math.isinf(numeric):
        return _fail(
            f"{field_name} must be finite.",
            code="INVALID_INPUT",
            details={"field": field_name, "value": str(value)},
        )
    if minimum is not None and numeric < minimum:
        return _fail(
            f"{field_name} must be greater than or equal to {minimum}.",
            code="VALIDATION_FAILED",
            details={"field": field_name, "minimum": minimum, "value": numeric},
        )
    if maximum is not None and numeric > maximum:
        return _fail(
            f"{field_name} must be less than or equal to {maximum}.",
            code="VALIDATION_FAILED",
            details={"field": field_name, "maximum": maximum, "value": numeric},
        )
    return _ok(f"{field_name} is valid.")


def validate_required_fields(
    payload: Mapping[str, object],
    required_fields: Sequence[str],
) -> ValidationResult:
    """Validate that required fields are present and non-``None``."""
    missing = [field for field in required_fields if field not in payload]
    null_fields = [field for field in required_fields if payload.get(field) is None]
    if missing or null_fields:
        return _fail(
            "Required fields are missing.",
            code="VALIDATION_FAILED",
            details={"missing": missing, "null": null_fields},
        )
    return _ok("Required fields are present.")


def _parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a semantic version string."""
    parts = version.split(".")
    if len(parts) != SEMVER_PART_COUNT or not all(part.isdigit() for part in parts):
        raise ValidationError(
            "version must use MAJOR.MINOR.PATCH.", code="INVALID_INPUT"
        )
    return int(parts[0]), int(parts[1]), int(parts[2])


def validate_schema_version(
    payload_version: str | None,
    schema_version: str | None,
    *,
    compatible_versions: Sequence[str] = (),
) -> ValidationResult:
    """Validate optional semantic-version compatibility."""
    if schema_version is None:
        return _ok("Schema version is not required.")
    if payload_version is None:
        return _fail(
            "Payload schema_version is required.",
            code="VALIDATION_FAILED",
            details={"expected": schema_version, "actual": None},
        )
    if payload_version == schema_version or payload_version in compatible_versions:
        return _ok("Schema version is compatible.")
    try:
        payload_major, payload_minor, _ = _parse_semver(payload_version)
        schema_major, schema_minor, _ = _parse_semver(schema_version)
    except ValidationError as exc:
        return _fail(
            str(exc), code="VALIDATION_FAILED", details={"path": "schema_version"}
        )
    compatible = payload_major == schema_major and payload_minor <= schema_minor
    if compatible:
        return _ok("Schema version is compatible.")
    return _fail(
        "Schema version is not compatible.",
        code="VALIDATION_FAILED",
        details={"expected": schema_version, "actual": payload_version},
    )


def validate_mapping_schema(
    payload: Mapping[str, object],
    schema: Mapping[str, object],
    *,
    reject_extra: bool = True,
) -> ValidationResult:
    """Validate a simple mapping schema.

    Supported schema keys are ``required``, ``allowed``, ``schema_version`` and
    ``compatible_versions``.
    """
    required = _string_sequence(schema.get("required", ()), "required")
    allowed = _string_sequence(schema.get("allowed", tuple(payload.keys())), "allowed")
    required_result = validate_required_fields(payload, required)
    if not required_result["valid"]:
        return required_result
    extra = sorted(set(payload) - set(allowed))
    if reject_extra and extra:
        return _fail(
            "Unknown fields are not allowed.",
            code="VALIDATION_FAILED",
            details={"extra": extra},
        )
    schema_version = schema.get("schema_version")
    compatible_versions = _string_sequence(
        schema.get("compatible_versions", ()),
        "compatible_versions",
    )
    if schema_version is not None:
        version_result = validate_schema_version(
            _optional_string(payload.get("schema_version")),
            _optional_string(schema_version),
            compatible_versions=compatible_versions,
        )
        if not version_result["valid"]:
            return version_result
    return _ok("Payload matches schema.")


def _string_sequence(value: object, field_name: str) -> tuple[str, ...]:
    """Return a tuple of strings or raise validation."""
    if not isinstance(value, Sequence) or isinstance(value, str):
        message = f"{field_name} must be a sequence."
        raise ValidationError(message, code="INVALID_INPUT")
    if not all(isinstance(item, str) and item for item in value):
        message = f"{field_name} must contain non-empty strings."
        raise ValidationError(
            message,
            code="INVALID_INPUT",
        )
    return tuple(value)


def _optional_string(value: object) -> str | None:
    """Return an optional string value."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError("schema version must be a string.", code="INVALID_INPUT")
    return value


def _tool_response(
    *,
    tool_name: str,
    result: ValidationResult,
    request_id: str | None,
    start_time: float,
) -> StandardResponse:
    """Wrap a native validation result in the standard tool schema."""
    metadata = build_metadata(
        tool_name=tool_name,
        start_time=start_time,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=TOOL_RISK_LEVEL,
        request_id=request_id,
        reads=False,
    )
    if result["valid"]:
        return success_response(
            message=result["message"],
            data=result,
            metadata=metadata,
        )
    return error_response(
        message=result["message"],
        code=result["code"],
        details=str(result["details"]),
        metadata=metadata,
    )


def validate_input_schema(
    payload: Mapping[str, object],
    schema: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only input schema validator."""
    start = time.perf_counter()
    return _tool_response(
        tool_name="validate_input_schema",
        result=validate_mapping_schema(payload, schema),
        request_id=request_id,
        start_time=start,
    )


def validate_output_schema(
    payload: Mapping[str, object],
    schema: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only output schema validator."""
    start = time.perf_counter()
    return _tool_response(
        tool_name="validate_output_schema",
        result=validate_mapping_schema(payload, schema),
        request_id=request_id,
        start_time=start,
    )


def validate_handoff_payload(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only handoff payload validator."""
    start = time.perf_counter()
    schema = {"required": ("request_id", "workflow_id"), "allowed": tuple(payload)}
    return _tool_response(
        tool_name="validate_handoff_payload",
        result=validate_mapping_schema(payload, schema, reject_extra=False),
        request_id=request_id,
        start_time=start,
    )


def validate_evidence_pack(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only evidence pack validator."""
    start = time.perf_counter()
    schema = {"required": ("evidence",), "allowed": tuple(payload)}
    return _tool_response(
        tool_name="validate_evidence_pack",
        result=validate_mapping_schema(payload, schema, reject_extra=False),
        request_id=request_id,
        start_time=start,
    )


def validate_approval_packet(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only approval packet validator."""
    start = time.perf_counter()
    schema = {"required": ("approval_id", "action"), "allowed": tuple(payload)}
    return _tool_response(
        tool_name="validate_approval_packet",
        result=validate_mapping_schema(payload, schema, reject_extra=False),
        request_id=request_id,
        start_time=start,
    )


def validate_registry_entry(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only registry entry validator."""
    start = time.perf_counter()
    schema = {"required": ("name", "version"), "allowed": tuple(payload)}
    return _tool_response(
        tool_name="validate_registry_entry",
        result=validate_mapping_schema(payload, schema, reject_extra=False),
        request_id=request_id,
        start_time=start,
    )


def validate_data_freshness(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only data freshness validator."""
    start = time.perf_counter()
    schema = {"required": ("timestamp",), "allowed": tuple(payload)}
    return _tool_response(
        tool_name="validate_data_freshness",
        result=validate_mapping_schema(payload, schema, reject_extra=False),
        request_id=request_id,
        start_time=start,
    )


def validation_failed_paths(result: ValidationResult) -> list[str]:
    """Return invalid field paths from a validation result where available."""
    path = result["details"].get("path")
    if isinstance(path, str):
        return [path]
    paths = result["details"].get("paths")
    if isinstance(paths, Sequence) and not isinstance(paths, str):
        return [str(item) for item in paths]
    return []
