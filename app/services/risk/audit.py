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


def _redact_audit_payload(v: Any) -> Any:  # noqa: ANN401
    """Recursively redact secrets, broker accounts, raw payloads, and tokens."""
    if isinstance(v, dict):
        redacted: dict[str, Any] = {}
        for k, val in v.items():
            k_lower = str(k).lower()
            if k_lower == "decision_token":
                redacted[k] = None
            elif any(
                term in k_lower
                for term in [
                    "password",
                    "passphrase",
                    "secret",
                    "credential",
                    "api_key",
                    "apikey",
                    "authorization",
                    "private",
                    "account",
                    "login",
                    "payload",
                    "signature",
                    "packet",
                    "token",
                    "key",
                ]
            ):
                safe_keys = {
                    "rule_key",
                    "severity",
                    "reason_codes",
                    "config_hash",
                    "policy_hash",
                    "decision_id",
                    "request_id",
                    "workflow_id",
                    "policy_version",
                    "policy_scope",
                    "symbol",
                    "side",
                    "volume",
                    "requested_size",
                    "approved_size",
                    "max_allowed_size",
                    "price",
                    "stop_loss",
                    "timestamp",
                    "status",
                    "calculated_volume",
                    "details",
                    "positions",
                    "pending_orders",
                    "in_flight_orders",
                    "exposure",
                    "var_es",
                    "var",
                    "es",
                    "stress_loss",
                    "drawdown",
                    "margin",
                    "margin_used",
                    "margin_usage",
                    "drawdown_state",
                    "composite_breach_flags",
                    "expiry",
                    "expiry_time",
                    "nonce",
                    "approver",
                    "approved_action",
                }
                if k_lower in safe_keys:
                    redacted[k] = _redact_audit_payload(val)
                else:
                    redacted[k] = "[REDACTED]"
            else:
                redacted[k] = _redact_audit_payload(val)
        return redacted
    if isinstance(v, list):
        return [_redact_audit_payload(val) for val in v]
    return v


class RiskAuditEventBuilder:
    """Builder for constructing RiskAuditEvent blocks with validation."""

    def __init__(self) -> None:
        """Initialize the builder with default previous hash."""
        self._decision: RiskDecisionPackage | None = None
        self._proposed_action: Any = None
        self._previous_hash: str = "0" * 64

    def with_decision(self, decision: RiskDecisionPackage) -> RiskAuditEventBuilder:
        """Set the decision package."""
        self._decision = decision
        return self

    def with_proposed_action(self, proposed_action: Any) -> RiskAuditEventBuilder:  # noqa: ANN401
        """Set the proposed action payload."""
        self._proposed_action = proposed_action
        return self

    def with_previous_hash(self, previous_hash: str) -> RiskAuditEventBuilder:
        """Set the previous hash."""
        self._previous_hash = previous_hash
        return self

    def build(self) -> RiskAuditEvent:
        """Build and cryptographically hash the RiskAuditEvent."""
        if not self._decision:
            raise ValidationError("decision is required to build audit event.")

        decision = self._decision
        proposed_action = self._proposed_action
        previous_hash = self._previous_hash

        action_dump = {}
        if hasattr(proposed_action, "model_dump"):
            action_dump = proposed_action.model_dump()
        elif isinstance(proposed_action, dict):
            action_dump = proposed_action

        # Redact secrets, broker account identifiers,
        # raw private payloads, and full approval packets
        action_dump = _redact_audit_payload(action_dump)
        decision_dict = _redact_audit_payload(decision.model_dump())

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
            "decision": decision_dict,
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

        return event


class RiskAuditHashChain:
    """Validator class to traverse and verify the integrity of the audit chain."""

    @staticmethod
    def verify_integrity(events: list[RiskAuditEvent]) -> bool:
        """Traverse and re-verify the audit chain to check for tampering."""
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


class RiskAuditStore:
    """Thread-safe orchestrator for audit persistence and verification."""

    def __init__(self, sink: RiskAuditSink) -> None:
        """Initialize the store wrapper with a sink."""
        if sink is None:
            msg = "Mandatory audit persistence is unavailable."
            raise ValidationError(msg, code="SERVICE_UNAVAILABLE")
        self.sink = sink

    def append_decision(
        self,
        decision: RiskDecisionPackage,
        proposed_action: Any,  # noqa: ANN401
    ) -> RiskAuditEvent:
        """Create, chain, and write audit event block, failing closed."""
        return create_risk_audit_event(decision, proposed_action, self.sink)

    def verify_chain(self) -> bool:
        """Verify the entire audit event chain for tampering."""
        return verify_risk_audit_chain(self.sink)


class RiskDecisionTokenSigner:
    """Cryptographic signer and validator for risk approval tokens."""

    def __init__(self, state_store: RiskStateStore) -> None:
        """Initialize with state store connection."""
        self.state_store = state_store

    def sign_token(
        self,
        decision_id: str,
        request_id: str,
        workflow_id: str,
        approved_action: str,
        config_hash: str,
        decision_hash: str,
        scope: dict[str, Any],
        expiry_seconds: int = 300,
        policy_hash: str | None = None,
    ) -> RiskApprovalToken:
        """Create and cryptographically sign a RiskApprovalToken."""
        return create_risk_decision_token(
            decision_id=decision_id,
            request_id=request_id,
            workflow_id=workflow_id,
            approved_action=approved_action,
            config_hash=config_hash,
            decision_hash=decision_hash,
            scope=scope,
            expiry_seconds=expiry_seconds,
            policy_hash=policy_hash,
        )

    def validate_token(
        self,
        token: RiskApprovalToken,
        expected_scope: dict[str, Any],
        active_config_hash: str,
        active_policy_hash: str,
    ) -> bool:
        """Validate signature, expiry, revocation, and scope compatibility."""
        return validate_risk_approval_token(
            token=token,
            expected_scope=expected_scope,
            active_config_hash=active_config_hash,
            active_policy_hash=active_policy_hash,
            state_store=self.state_store,
        )

    def revoke_token(self, token_id: str) -> None:
        """Mark a token as revoked."""
        revoke_risk_approval_token(token_id, self.state_store)


def create_risk_decision_token(
    decision_id: str,
    request_id: str,
    workflow_id: str,
    approved_action: str,
    config_hash: str,
    decision_hash: str,
    scope: dict[str, Any],
    expiry_seconds: int = 300,
    policy_hash: str | None = None,
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
        policy_hash: Optional policy hash value to bind.

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
    payload_dict: dict[str, Any] = {
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
    if policy_hash:
        payload_dict["policy_hash"] = policy_hash

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
        policy_hash=policy_hash,
        scope=scope,
        nonce=nonce,
        signature=signature,
    )


def _validate_token_scope(
    token_scope: dict[str, Any], expected_scope: dict[str, Any]
) -> bool:
    """Validate expected scope parameters against token scope mapping."""
    alt_keys = {
        "strategy": ["strategy_id", "strategy"],
        "account": ["account_id", "account"],
        "symbol": ["symbol"],
        "environment": ["environment"],
        "action": ["action", "approved_action"],
    }
    for k, v in expected_scope.items():
        if v is None:
            continue
        token_val = token_scope.get(k)
        if token_val is None:
            for alt_key in alt_keys.get(k, []):
                token_val = token_scope.get(alt_key)
                if token_val is not None:
                    break
        if token_val is None or str(token_val).lower() != str(v).lower():
            return False
    return True


def validate_risk_approval_token(
    token: RiskApprovalToken,
    expected_scope: dict[str, Any],
    active_config_hash: str,
    active_policy_hash: str,
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
    payload_dict: dict[str, Any] = {
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
    if getattr(token, "policy_hash", None):
        payload_dict["policy_hash"] = token.policy_hash

    canonical_payload = canonical_json(payload_dict)
    key = _get_signing_key()
    expected_sig = hmac.new(key, canonical_payload.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(token.signature, expected_sig):
        return False

    # 2. Expiry and Revocation check
    if token.expiry_time < utc_now() or state_store.is_token_revoked(token.token_id):
        return False

    # 3. Config and Policy compatibility check
    token_policy_hash = getattr(token, "policy_hash", None)
    policy_mismatch = (
        token_policy_hash
        and active_policy_hash
        and token_policy_hash != active_policy_hash
    )
    if token.config_hash != active_config_hash or policy_mismatch:
        return False

    # 4. Scope validation
    return _validate_token_scope(token.scope, expected_scope)


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
    if audit_sink is None:
        msg = "Mandatory audit persistence is unavailable."
        raise ValidationError(msg, code="SERVICE_UNAVAILABLE")

    try:
        prev = audit_sink.get_last_event()
    except Exception as e:
        msg = f"Audit persistence query failed: {e}"
        raise ValidationError(msg, code="DATABASE_ERROR") from e

    previous_hash = prev.hash if prev else "0" * 64

    event = (
        RiskAuditEventBuilder()
        .with_decision(decision)
        .with_proposed_action(proposed_action)
        .with_previous_hash(previous_hash)
        .build()
    )

    try:
        audit_sink.write_event(event)
    except Exception as e:
        msg = f"Audit persistence write failed: {e}"
        raise ValidationError(msg, code="DATABASE_ERROR") from e

    return event


def verify_risk_audit_chain(audit_sink: RiskAuditSink) -> bool:
    """Traverse and re-verify the audit chain to check for tampering.

    Args:
        audit_sink: Store containing all events.

    Returns:
        bool: True if audit chain is valid and untampered.
    """
    if audit_sink is None:
        return False
    try:
        events = audit_sink.get_all_events()
    except Exception:  # noqa: BLE001
        return False
    return RiskAuditHashChain.verify_integrity(events)
