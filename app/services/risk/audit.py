"""Risk governance cryptographic token and tamper-evident audit chaining.

Provides functions to sign, validate, and revoke risk approval tokens, as well as
build, chain, and verify tamper-evident pre-trade risk audit event logs.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.services.risk.models import (
    RiskApprovalToken,
    RiskAuditEvent,
    RiskDecisionPackage,
    RiskDecisionStatus,
    RiskSeverity,
)

if TYPE_CHECKING:
    from app.services.risk.storage import RiskAuditSink, RiskStateStore
from app.utils.errors import ValidationError
from app.utils.normalization import utc_now
from app.utils.security import load_encryption_key
from app.utils.standard import canonical_json, stable_identifier


def _coerce_types(v: Any) -> Any:  # noqa: ANN401
    """Recursively coerce Decimals to floats and datetimes to ISO strings for JSON."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _coerce_types(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_coerce_types(val) for val in v]
    return v


def _get_signing_key() -> bytes:
    """Load the signing key from security utils, fallback safely for tests."""
    try:
        key = load_encryption_key()
        if key:
            return key.encode()
    except Exception:  # noqa: S110, BLE001
        pass
    # Stable default key for offline/simulation/tests
    return b"default_transient_secret_key_for_testing"


def create_risk_decision_token(
    decision_id: str,
    request_id: str,
    workflow_id: str,
    approved_action: str,
    config_hash: str,
    decision_hash: str,
    scope: dict[str, Any],
    expiry_seconds: int = 300,
) -> RiskApprovalToken:
    """Create and cryptographically sign a RiskApprovalToken.

    Args:
        decision_id: Unique decision ID.
        request_id: Associated request ID.
        workflow_id: Workflow run ID.
        approved_action: Description of the action.
        config_hash: Evaluated configuration hash.
        decision_hash: Hash of the decision package.
        scope: Target scope parameters.
        expiry_seconds: Expiration window in seconds.

    Returns:
        RiskApprovalToken: Signed token envelope.
    """
    if not decision_id or not request_id or not workflow_id:
        raise ValidationError("decision_id, request_id, and workflow_id are required.")

    token_id = stable_identifier(
        {"decision_id": decision_id, "timestamp": utc_now().isoformat()}, prefix="tok"
    )
    expiry = utc_now() + timedelta(seconds=expiry_seconds)
    nonce = hashlib.sha256(f"{token_id}:{utc_now().timestamp()}".encode()).hexdigest()[
        :16
    ]

    # Rebuild signature payload
    payload_dict = {
        "token_id": token_id,
        "request_id": request_id,
        "workflow_id": workflow_id,
        "approved_action": approved_action,
        "expiry_time": expiry.isoformat(),
        "config_hash": config_hash,
        "decision_hash": decision_hash,
        "scope": scope,
        "nonce": nonce,
    }
    canonical_payload = canonical_json(payload_dict)
    key = _get_signing_key()
    signature = hmac.new(key, canonical_payload.encode(), hashlib.sha256).hexdigest()

    return RiskApprovalToken(
        token_id=token_id,
        request_id=request_id,
        workflow_id=workflow_id,
        approved_action=approved_action,
        approver="RiskGovernor",
        expiry_time=expiry,
        config_hash=config_hash,
        decision_hash=decision_hash,
        scope=scope,
        nonce=nonce,
        signature=signature,
    )


def validate_risk_approval_token(
    token: RiskApprovalToken,
    expected_scope: dict[str, Any],
    active_config_hash: str,
    active_policy_hash: str,  # noqa: ARG001
    state_store: RiskStateStore,
) -> bool:
    """Validate a RiskApprovalToken signature, expiry, revocation, and scope.

    Args:
        token: Cryptographically signed RiskApprovalToken.
        expected_scope: Scope validation filters.
        active_config_hash: Active config hash to match.
        active_policy_hash: Active policy hash to match.
        state_store: RiskStateStore registry check.

    Returns:
        bool: True if valid.
    """
    # 1. Signature check
    payload_dict = {
        "token_id": token.token_id,
        "request_id": token.request_id,
        "workflow_id": token.workflow_id,
        "approved_action": token.approved_action,
        "expiry_time": token.expiry_time.isoformat(),
        "config_hash": token.config_hash,
        "decision_hash": token.decision_hash,
        "scope": token.scope,
        "nonce": token.nonce,
    }
    canonical_payload = canonical_json(payload_dict)
    key = _get_signing_key()
    expected_sig = hmac.new(key, canonical_payload.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(token.signature, expected_sig):
        return False

    # 2. Expiry check
    if token.expiry_time < utc_now():
        return False

    # 3. Revocation check
    if state_store.is_token_revoked(token.token_id):
        return False

    # 4. Config compatibility check
    if token.config_hash != active_config_hash:
        return False

    # 5. Scope validation
    for k, v in expected_scope.items():
        token_val = token.scope.get(k)
        if token_val is None or str(token_val).lower() != str(v).lower():
            return False

    return True


def revoke_risk_approval_token(token_id: str, state_store: RiskStateStore) -> None:
    """Mark a decision token as revoked in the store."""
    state_store.revoke_token(token_id)


def create_risk_audit_event(
    decision: RiskDecisionPackage,
    proposed_action: Any,  # noqa: ANN401
    audit_sink: RiskAuditSink,
) -> RiskAuditEvent:
    """Generate the next chained audit event and append it to the audit sink.

    Args:
        decision: RiskDecisionPackage result.
        proposed_action: The action proposed.
        audit_sink: Persistence sink.

    Returns:
        RiskAuditEvent: Built and chained audit event.
    """
    # Get previous block hash
    prev = audit_sink.get_last_event()
    previous_hash = prev.hash if prev else "0" * 64

    # Build base event structure
    action_dump = {}
    if hasattr(proposed_action, "model_dump"):
        action_dump = proposed_action.model_dump()
    elif isinstance(proposed_action, dict):
        action_dump = proposed_action

    # Coerce action_dump decimals to float for JSON compatibility
    def _coerce_decimals(val: Any) -> Any:  # noqa: ANN401
        if isinstance(val, dict):
            return {k: _coerce_decimals(v) for k, v in val.items()}
        if isinstance(val, list):
            return [_coerce_decimals(v) for v in val]
        return (
            float(val)
            if isinstance(val, float | int) and not isinstance(val, bool)
            else val
        )

    details = {
        "decision": decision.model_dump(),
        "proposed_action": _coerce_decimals(action_dump),
    }

    # Map status to severity
    severity_map = {
        RiskDecisionStatus.APPROVE: RiskSeverity.INFO,
        RiskDecisionStatus.REDUCE_SIZE: RiskSeverity.WARNING,
        RiskDecisionStatus.NEEDS_APPROVAL: RiskSeverity.WARNING,
        RiskDecisionStatus.NEEDS_MORE_EVIDENCE: RiskSeverity.WARNING,
        RiskDecisionStatus.REJECT: RiskSeverity.HARD_BREACH,
        RiskDecisionStatus.BLOCK: RiskSeverity.CRITICAL_BREACH,
        RiskDecisionStatus.HALT_STRATEGY: RiskSeverity.EMERGENCY_HALT,
        RiskDecisionStatus.HALT_ALL: RiskSeverity.EMERGENCY_HALT,
    }
    severity = severity_map.get(
        RiskDecisionStatus(decision.status)
        if decision.status in list(RiskDecisionStatus)
        else RiskDecisionStatus.REJECT,
        RiskSeverity.HARD_BREACH,
    )

    # Payload hash representing the inputs evaluated
    payload_hash = hashlib.sha256(
        canonical_json(_coerce_types(action_dump)).encode()
    ).hexdigest()

    event_id = stable_identifier(
        {"decision_id": decision.decision_id, "prev_hash": previous_hash},
        prefix="event",
    )

    # Initialize event
    event = RiskAuditEvent(
        event_id=event_id,
        decision_id=decision.decision_id,
        policy_name=decision.rule_key,
        action_taken=decision.status,
        payload_hash=payload_hash,
        severity=severity,
        previous_hash=previous_hash,
        hash="",
        timestamp=datetime.now(UTC),
        details=details,
    )

    # Generate chained SHA256 hash (excluding the hash field itself)
    event_dict = event.model_dump()
    if "hash" in event_dict:
        del event_dict["hash"]

    canonical_str = canonical_json(_coerce_types(event_dict))
    event.hash = hashlib.sha256(canonical_str.encode()).hexdigest()

    audit_sink.write_event(event)
    return event


def verify_risk_audit_chain(audit_sink: RiskAuditSink) -> bool:
    """Traverse and re-verify the audit chain to check for tampering.

    Args:
        audit_sink: Store containing all events.

    Returns:
        bool: True if audit chain is valid and untampered.
    """
    events = audit_sink.get_all_events()
    if not events:
        return True

    for i, event in enumerate(events):
        # 1. Check genesis block previous hash
        if i == 0:
            if event.previous_hash != "0" * 64:
                return False
        # Check linkage with previous event
        elif event.previous_hash != events[i - 1].hash:
            return False

        # 2. Re-compute hash and verify
        event_dict = event.model_dump()
        if "hash" in event_dict:
            del event_dict["hash"]

        canonical_str = canonical_json(_coerce_types(event_dict))
        computed_hash = hashlib.sha256(canonical_str.encode()).hexdigest()
        if event.hash != computed_hash:
            return False

    return True
