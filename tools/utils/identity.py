"""Identity and traceability helpers for HaruQuant utilities.

This module provides support helpers, not official AI tools. It exports
collision-resistant ID generators, deterministic validators, and version
normalization for request, workflow, correlation, causation, event, and
idempotency traceability.

Public exports:
    DEFAULT_VERSION, ID_PREFIXES, generate_id, generate_prefixed_id,
    generate_request_id, generate_workflow_id, generate_correlation_id,
    generate_causation_id, generate_event_id, generate_idempotency_id,
    validate_id, validate_request_id, validate_workflow_id, ensure_version.

Side effects:
    None. Importing this module does not configure logging, read files, call
    networks, import optional dependencies, or mutate live trading state.
"""

from __future__ import annotations

import re
import uuid
from typing import NoReturn

from tools.utils.errors import ValidationError
from tools.utils.logger import logger

DEFAULT_VERSION = "1.0.0"
ID_PREFIXES = frozenset({"id", "req", "wf", "corr", "cause", "event", "idem"})
_PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,15}$")
_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,15}_[a-f0-9]{32}$")
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")


def _raise_validation(message: str, *, field_name: str) -> NoReturn:
    """Log and raise a deterministic validation error."""
    logger.warning(
        "identity validation failed",
        extra={
            "event_name": "identity_validation_failed",
            "field_name": field_name,
            "error_code": "INVALID_INPUT",
        },
    )
    raise ValidationError(message, code="INVALID_INPUT")


def _validate_prefix(prefix: object) -> str:
    """Return a safe ID prefix or raise a validation error."""
    if not isinstance(prefix, str) or not prefix.strip():
        _raise_validation("prefix must be a non-empty string.", field_name="prefix")
    candidate = prefix.strip()
    safe_prefix = candidate.lower()
    if candidate != safe_prefix:
        _raise_validation("prefix must be lowercase.", field_name="prefix")
    if not _PREFIX_PATTERN.fullmatch(safe_prefix):
        _raise_validation(
            "prefix must start with a letter and contain only lowercase letters, "
            "numbers, or hyphens.",
            field_name="prefix",
        )
    return safe_prefix


def generate_id() -> str:
    """Generate a collision-resistant unprefixed UUID4 hex identifier.

    Use this when a caller needs safe random ID material without embedding any
    raw user-provided text.

    Returns:
        A 32-character lowercase UUID4 hex string.

    Side effects:
        None.
    """
    return uuid.uuid4().hex


def generate_prefixed_id(prefix: str) -> str:
    """Generate a collision-resistant ID with a validated prefix.

    Args:
        prefix: Safe lowercase prefix, such as ``req`` or ``event``.

    Returns:
        ID in ``prefix_uuid4hex`` format.

    Raises:
        ValidationError: If the prefix is empty or unsafe.

    Side effects:
        None.
    """
    safe_prefix = _validate_prefix(prefix)
    return f"{safe_prefix}_{generate_id()}"


def generate_request_id() -> str:
    """Generate a request ID safe for logs, audit, tools, and handoffs."""
    return generate_prefixed_id("req")


def generate_workflow_id() -> str:
    """Generate a workflow ID safe for logs, audit, tools, and handoffs."""
    return generate_prefixed_id("wf")


def generate_correlation_id() -> str:
    """Generate a correlation ID for cross-module trace grouping."""
    return generate_prefixed_id("corr")


def generate_causation_id() -> str:
    """Generate a causation ID for event or workflow parentage."""
    return generate_prefixed_id("cause")


def generate_event_id() -> str:
    """Generate an event ID safe for audit records and event envelopes."""
    return generate_prefixed_id("event")


def generate_idempotency_id() -> str:
    """Generate an idempotency ID for caller-owned side-effect guards."""
    return generate_prefixed_id("idem")


def validate_id(value: object, *, expected_prefix: str | None = None) -> str:
    """Validate and return a safe generated identifier.

    Args:
        value: Candidate identifier.
        expected_prefix: Optional required prefix.

    Returns:
        The validated identifier.

    Raises:
        ValidationError: If the ID is not string-safe or the prefix mismatches.

    Side effects:
        None.
    """
    if not isinstance(value, str) or not value.strip():
        _raise_validation("id must be a non-empty string.", field_name="id")
    safe_value = value.strip()
    if not _ID_PATTERN.fullmatch(safe_value):
        _raise_validation(
            "id must use prefix_uuid4hex format with safe characters only.",
            field_name="id",
        )
    if expected_prefix is not None:
        safe_prefix = _validate_prefix(expected_prefix)
        if not safe_value.startswith(f"{safe_prefix}_"):
            _raise_validation(
                "id prefix does not match expected prefix.",
                field_name="id",
            )
    return safe_value


def validate_request_id(value: object) -> str:
    """Validate and return a request ID.

    Args:
        value: Candidate request ID.

    Returns:
        Validated request ID.

    Raises:
        ValidationError: If the ID is malformed or not a request ID.

    Side effects:
        None.
    """
    return validate_id(value, expected_prefix="req")


def validate_workflow_id(value: object) -> str:
    """Validate and return a workflow ID.

    Args:
        value: Candidate workflow ID.

    Returns:
        Validated workflow ID.

    Raises:
        ValidationError: If the ID is malformed or not a workflow ID.

    Side effects:
        None.
    """
    return validate_id(value, expected_prefix="wf")


def ensure_version(version: str | None, *, default: str = DEFAULT_VERSION) -> str:
    """Return a validated version string, falling back to the default.

    Args:
        version: Optional version string.
        default: Version to use when ``version`` is ``None``.

    Returns:
        Validated version string.

    Raises:
        ValidationError: If the selected version is empty or unsafe.

    Side effects:
        None.
    """
    selected = default if version is None else version
    if not isinstance(selected, str) or not selected.strip():
        _raise_validation("version must be a non-empty string.", field_name="version")
    safe_version = selected.strip()
    if not _VERSION_PATTERN.fullmatch(safe_version):
        _raise_validation(
            "version must contain only letters, numbers, dots, "
            "underscores, or hyphens.",
            field_name="version",
        )
    return safe_version
