"""Schema validation helpers and official read-only validation tools.

Exported AI Tools:
    - validate_input_schema: Official low-risk read-only input schema validator.
    - validate_output_schema: Official low-risk read-only output schema validator.
    - validate_handoff_payload: Official low-risk read-only handoff payload validator.
    - validate_evidence_pack: Official low-risk read-only evidence pack validator.
    - validate_approval_packet: Official low-risk read-only approval packet validator.
    - validate_registry_entry: Official low-risk read-only registry entry validator.
    - validate_data_freshness: Official low-risk read-only data freshness validator.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict

from tools.utils.errors import ValidationError
from tools.utils.logger import logger
from tools.utils.standard import (
    StandardResponse,
    build_metadata,
    error_response,
    success_response,
)

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL: Literal["low"] = "low"
REQUIRES_APPROVAL = False
READS = False
WRITES = False
UPDATES = False
DELETES = False
TRADES = False
REQUIRES_NETWORK = False
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
    if not isinstance(payload, Mapping):
        raise ValidationError("payload must be a mapping.", code="INVALID_INPUT")
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
    if not isinstance(payload, Mapping):
        raise ValidationError("payload must be a mapping.", code="INVALID_INPUT")
    if not isinstance(schema, Mapping):
        raise ValidationError("schema must be a mapping.", code="INVALID_INPUT")
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
    logger.info(
        "%s called",
        tool_name,
        extra={"event_name": "tool_called", "request_id": request_id},
    )
    metadata = build_metadata(
        tool_name=tool_name,
        start_time=start_time,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=TOOL_RISK_LEVEL,
        request_id=request_id,
        reads=READS,
        writes=WRITES,
        updates=UPDATES,
        deletes=DELETES,
        trades=TRADES,
        requires_network=REQUIRES_NETWORK,
    )
    if result["valid"]:
        logger.info(
            "%s completed successfully",
            tool_name,
            extra={"event_name": "tool_success", "request_id": request_id},
        )
        return success_response(
            message=result["message"],
            data=result,
            metadata=metadata,
        )
    logger.warning(
        "%s validation failed",
        tool_name,
        extra={"event_name": "tool_validation_failed", "request_id": request_id},
    )
    return error_response(
        message=result["message"],
        code=result["code"],
        details=str(result["details"]),
        metadata=metadata,
    )


def _tool_failure_response(
    *,
    tool_name: str,
    exception: Exception,
    request_id: str | None,
    start_time: float,
) -> StandardResponse:
    """Return a fail-closed standard envelope for wrapper failures."""
    event_name = (
        "tool_validation_failed"
        if isinstance(exception, ValidationError | TypeError)
        else "tool_exception"
    )
    if event_name == "tool_validation_failed":
        logger.warning(
            "%s failed",
            tool_name,
            extra={"event_name": event_name, "request_id": request_id},
        )
    else:
        logger.exception(
            "%s failed",
            tool_name,
            extra={"event_name": event_name, "request_id": request_id},
        )
    metadata = build_metadata(
        tool_name=tool_name,
        start_time=start_time,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=TOOL_RISK_LEVEL,
        request_id=request_id,
        reads=READS,
        writes=WRITES,
        updates=UPDATES,
        deletes=DELETES,
        trades=TRADES,
        requires_network=REQUIRES_NETWORK,
    )
    code = getattr(exception, "code", "TOOL_EXECUTION_FAILED")
    return error_response(
        message=f"{tool_name} failed.",
        code=code,
        details=f"{exception.__class__.__name__}: {exception}",
        metadata=metadata,
    )


def _run_schema_tool(  # noqa: PLR0913
    *,
    tool_name: str,
    payload: Mapping[str, object],
    request_id: str | None,
    start_time: float,
    schema: Mapping[str, object] | None = None,
    reject_extra: bool = False,
) -> StandardResponse:
    """Run a schema validator and map every failure to a standard envelope."""
    try:
        active_schema = schema
        if active_schema is None:
            active_schema = {
                "required": (),
                "allowed": tuple(payload),
            }
        return _tool_response(
            tool_name=tool_name,
            result=validate_mapping_schema(
                payload,
                active_schema,
                reject_extra=reject_extra,
            ),
            request_id=request_id,
            start_time=start_time,
        )
    except (TypeError, ValidationError) as exc:
        return _tool_failure_response(
            tool_name=tool_name,
            exception=exc,
            request_id=request_id,
            start_time=start_time,
        )
    except Exception as exc:  # noqa: BLE001
        return _tool_failure_response(
            tool_name=tool_name,
            exception=exc,
            request_id=request_id,
            start_time=start_time,
        )


def validate_input_schema(
    payload: Mapping[str, object],
    schema: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only input schema validator.

    Use this tool before consuming externally supplied input payloads.

    Args:
        payload: Candidate input mapping.
        schema: Simple mapping schema with required, allowed, schema_version,
            and compatible_versions keys.
        request_id: Optional trace request identifier.

    Returns:
        Standard tool response envelope.

    Errors:
        INVALID_INPUT, VALIDATION_FAILED, or TOOL_EXECUTION_FAILED.

    Side effects:
        Emits structured logs only.
    """
    start = time.perf_counter()
    return _run_schema_tool(
        tool_name="validate_input_schema",
        payload=payload,
        schema=schema,
        request_id=request_id,
        start_time=start,
        reject_extra=True,
    )


def validate_output_schema(
    payload: Mapping[str, object],
    schema: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only output schema validator.

    Use this tool before handing tool or agent output to another workflow.

    Args:
        payload: Candidate output mapping.
        schema: Simple mapping schema with required, allowed, schema_version,
            and compatible_versions keys.
        request_id: Optional trace request identifier.

    Returns:
        Standard tool response envelope.

    Errors:
        INVALID_INPUT, VALIDATION_FAILED, or TOOL_EXECUTION_FAILED.

    Side effects:
        Emits structured logs only.
    """
    start = time.perf_counter()
    return _run_schema_tool(
        tool_name="validate_output_schema",
        payload=payload,
        schema=schema,
        request_id=request_id,
        start_time=start,
        reject_extra=True,
    )


def validate_handoff_payload(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only handoff payload validator.

    Args:
        payload: Handoff mapping requiring request_id and workflow_id.
        request_id: Optional trace request identifier.

    Returns:
        Standard tool response envelope.

    Errors:
        INVALID_INPUT, VALIDATION_FAILED, or TOOL_EXECUTION_FAILED.

    Side effects:
        Emits structured logs only.
    """
    start = time.perf_counter()
    schema = {"required": ("request_id", "workflow_id"), "allowed": ()}
    return _run_schema_tool(
        tool_name="validate_handoff_payload",
        payload=payload,
        schema=schema,
        request_id=request_id,
        start_time=start,
        reject_extra=False,
    )


def validate_evidence_pack(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only evidence pack validator.

    Args:
        payload: Evidence mapping requiring an evidence field.
        request_id: Optional trace request identifier.

    Returns:
        Standard tool response envelope.

    Errors:
        INVALID_INPUT, VALIDATION_FAILED, or TOOL_EXECUTION_FAILED.

    Side effects:
        Emits structured logs only.
    """
    start = time.perf_counter()
    schema = {"required": ("evidence",), "allowed": ()}
    return _run_schema_tool(
        tool_name="validate_evidence_pack",
        payload=payload,
        schema=schema,
        request_id=request_id,
        start_time=start,
        reject_extra=False,
    )


def validate_approval_packet(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only approval packet validator.

    Args:
        payload: Approval mapping requiring approval_id and action.
        request_id: Optional trace request identifier.

    Returns:
        Standard tool response envelope.

    Errors:
        INVALID_INPUT, VALIDATION_FAILED, or TOOL_EXECUTION_FAILED.

    Side effects:
        Emits structured logs only.
    """
    start = time.perf_counter()
    schema = {"required": ("approval_id", "action"), "allowed": ()}
    return _run_schema_tool(
        tool_name="validate_approval_packet",
        payload=payload,
        schema=schema,
        request_id=request_id,
        start_time=start,
        reject_extra=False,
    )


def validate_registry_entry(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only registry entry validator.

    Args:
        payload: Registry mapping requiring name and version.
        request_id: Optional trace request identifier.

    Returns:
        Standard tool response envelope.

    Errors:
        INVALID_INPUT, VALIDATION_FAILED, or TOOL_EXECUTION_FAILED.

    Side effects:
        Emits structured logs only.
    """
    start = time.perf_counter()
    schema = {"required": ("name", "version"), "allowed": ()}
    return _run_schema_tool(
        tool_name="validate_registry_entry",
        payload=payload,
        schema=schema,
        request_id=request_id,
        start_time=start,
        reject_extra=False,
    )


def validate_data_freshness(
    payload: Mapping[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only data freshness validator.

    Args:
        payload: Freshness mapping requiring timestamp.
        request_id: Optional trace request identifier.

    Returns:
        Standard tool response envelope.

    Errors:
        INVALID_INPUT, VALIDATION_FAILED, or TOOL_EXECUTION_FAILED.

    Side effects:
        Emits structured logs only.
    """
    start = time.perf_counter()
    schema = {"required": ("timestamp",), "allowed": ()}
    return _run_schema_tool(
        tool_name="validate_data_freshness",
        payload=payload,
        schema=schema,
        request_id=request_id,
        start_time=start,
        reject_extra=False,
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
