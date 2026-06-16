"""Authentication context and deterministic authorization helpers.

Exported AI Tools:
    - validate_auth_context: Official low-risk read-only auth context validator.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from app.utils.errors import SecurityError, ValidationError
from app.utils.identity import validate_request_id, validate_workflow_id
from app.utils.logger import logger
from app.utils.standard import (
    StandardResponse,
    build_metadata,
    error_response,
    success_response,
)

TOOL_NAME = "validate_auth_context"
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

PrincipalType = Literal["owner", "operator", "service", "agent", "viewer"]
DecisionStatus = Literal["allowed", "denied"]


def _string_set(value: object) -> set[str]:
    """Return a set of strings from an iterable object."""
    if value is None:
        return set()
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise ValidationError("auth collection fields must be iterable.")
    return {str(item) for item in value}


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Immutable authentication context."""

    principal_id: str
    principal_type: PrincipalType
    roles: frozenset[str]
    permissions: frozenset[str]
    scopes: frozenset[str]
    request_id: str
    workflow_id: str
    correlation_id: str | None = None


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    """Deterministic authorization decision."""

    status: DecisionStatus
    allowed: bool
    reason: str
    missing_permissions: tuple[str, ...]


def build_auth_context(
    *,
    principal_id: str,
    principal_type: PrincipalType,
    roles: set[str] | frozenset[str],
    permissions: set[str] | frozenset[str],
    scopes: set[str] | frozenset[str],
    request_id: str,
    workflow_id: str,
    correlation_id: str | None = None,
) -> AuthContext:
    """Build and validate an immutable auth context."""
    if not principal_id.strip():
        raise ValidationError("principal_id must be non-empty.", code="INVALID_INPUT")
    if principal_type not in {"owner", "operator", "service", "agent", "viewer"}:
        raise ValidationError("principal_type is invalid.", code="INVALID_INPUT")
    return AuthContext(
        principal_id=principal_id.strip(),
        principal_type=principal_type,
        roles=frozenset(roles),
        permissions=frozenset(permissions),
        scopes=frozenset(scopes),
        request_id=validate_request_id(request_id),
        workflow_id=validate_workflow_id(workflow_id),
        correlation_id=correlation_id,
    )


def authorize_action(
    context: AuthContext | None,
    *,
    required_permissions: set[str] | frozenset[str],
    required_scopes: set[str] | frozenset[str] = frozenset(),
) -> AuthorizationDecision:
    """Return a deny-by-default authorization decision."""
    if context is None:
        return AuthorizationDecision(
            "denied", False, "missing auth context", tuple(required_permissions)
        )
    missing_permissions = tuple(
        sorted(set(required_permissions) - set(context.permissions))
    )
    missing_scopes = tuple(sorted(set(required_scopes) - set(context.scopes)))
    missing = (*missing_permissions, *missing_scopes)
    if missing:
        return AuthorizationDecision(
            "denied", False, "missing permissions or scopes", missing
        )
    return AuthorizationDecision("allowed", True, "authorized", ())


def require_authorization(
    context: AuthContext | None,
    *,
    required_permissions: set[str] | frozenset[str],
    required_scopes: set[str] | frozenset[str] = frozenset(),
) -> None:
    """Raise ``SecurityError`` when authorization fails."""
    decision = authorize_action(
        context,
        required_permissions=required_permissions,
        required_scopes=required_scopes,
    )
    if not decision.allowed:
        raise SecurityError(decision.reason, code="AUTHORIZATION_FAILED")


def validate_auth_context(
    payload: dict[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only auth context validator.

    Use this tool to validate an auth context payload (e.g. principal_id, type, roles).

    Args:
        payload (dict[str, object]): The auth context payload to validate.
        request_id (str | None, optional): Optional trace request ID.

    Returns:
        StandardResponse: Standard tool response envelope.

    Errors:
        INVALID_INPUT: The payload is missing required auth fields or uses
            malformed collection values.
        PERMISSION_DENIED: The auth context violates security validation.
        TOOL_EXECUTION_FAILED: An unexpected validation runtime failure occurred.

    Side effects:
        Emits structured tool call, validation failure, success, and exception
        logs. It does not mutate auth state or grant permissions.
    """
    start = time.perf_counter()
    logger.info(
        "validate_auth_context called",
        extra={"event_name": "tool_called", "request_id": request_id},
    )
    metadata = build_metadata(
        tool_name=TOOL_NAME,
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
        start_time=start,
    )
    try:
        build_auth_context(
            principal_id=str(payload["principal_id"]),
            principal_type=payload["principal_type"],  # type: ignore[arg-type]
            roles=_string_set(payload.get("roles")),
            permissions=_string_set(payload.get("permissions")),
            scopes=_string_set(payload.get("scopes")),
            request_id=str(payload["request_id"]),
            workflow_id=str(payload["workflow_id"]),
            correlation_id=(
                str(payload["correlation_id"])
                if payload.get("correlation_id") is not None
                else None
            ),
        )
        logger.info(
            "validate_auth_context completed",
            extra={"event_name": "tool_success", "request_id": request_id},
        )
    except (KeyError, TypeError, ValidationError, SecurityError) as exc:
        logger.warning(
            "validate_auth_context validation failed",
            extra={"event_name": "tool_validation_failed", "request_id": request_id},
        )
        code = getattr(exc, "code", "INVALID_INPUT")
        return error_response(
            message="Auth context is invalid.",
            code=code,
            details=str(exc),
            metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "validate_auth_context raised exception",
            extra={"event_name": "tool_exception", "request_id": request_id},
        )
        return error_response(
            message="Auth context validation failed.",
            code="TOOL_EXECUTION_FAILED",
            details=f"{exc.__class__.__name__}: {exc}",
            metadata=metadata,
        )
    return success_response(
        message="Auth context is valid.",
        data={"valid": True},
        metadata=metadata,
    )
