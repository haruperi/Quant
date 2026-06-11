"""Unit tests for auth helpers."""

import pytest
from tools.utils import (
    SecurityError,
    authorize_action,
    build_auth_context,
    generate_request_id,
    generate_workflow_id,
    require_authorization,
    validate_auth_context,
)


def test_authorize_action_is_deny_by_default() -> None:
    """Missing or insufficient context is denied."""
    denied = authorize_action(None, required_permissions={"read"})
    context = build_auth_context(
        principal_id="agent-1",
        principal_type="agent",
        roles={"researcher"},
        permissions={"read"},
        scopes={"utils"},
        request_id=generate_request_id(),
        workflow_id=generate_workflow_id(),
    )
    allowed = authorize_action(context, required_permissions={"read"})

    assert denied.allowed is False
    assert allowed.allowed is True
    with pytest.raises(SecurityError):
        require_authorization(context, required_permissions={"write"})


def test_validate_auth_context_official_response() -> None:
    """Auth context validator returns standard envelopes."""
    response = validate_auth_context(
        {
            "principal_id": "svc",
            "principal_type": "service",
            "roles": ["service"],
            "permissions": ["read"],
            "scopes": ["utils"],
            "request_id": generate_request_id(),
            "workflow_id": generate_workflow_id(),
        },
    )
    invalid = validate_auth_context({})

    assert response["status"] == "success"
    assert invalid["status"] == "error"
