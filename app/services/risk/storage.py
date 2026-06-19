"""Risk governance storage ports and in-memory store.

Defines the abstract repository interfaces for persisting risk state, policies,
decisions, and audit events, and provides a thread-safe in-memory store.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from decimal import Decimal
from threading import RLock
from typing import Any

from app.services.risk.models import (
    DrawdownState,
    KillSwitchReason,
    KillSwitchStateEnum,
    PolicyRule,
    RiskAuditEvent,
    RiskDecisionPackage,
)
from app.utils.errors import DataError, ValidationError
from app.utils.standard import canonical_json


def compute_decision_material_hash(decision: RiskDecisionPackage) -> str:
    """Compute a deterministic hash of the decision's material inputs.

    Uses request_id, workflow_id, config_hash, policy_hash, and the proposed
    action details.

    Args:
        decision: The decision package to hash.

    Returns:
        str: Deterministic SHA256 hex digest.
    """
    details = decision.details or {}
    proposed = details.get("proposed_action") or {}

    material = {
        "request_id": decision.request_id,
        "workflow_id": decision.workflow_id,
        "config_hash": decision.config_hash or "",
        "policy_hash": decision.policy_hash or "",
        "proposed_action": proposed,
    }

    def _coerce(v: Any) -> Any:  # noqa: ANN401
        if isinstance(v, Decimal):
            return float(v)
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, dict):
            return {k: _coerce(val) for k, val in v.items()}
        if isinstance(v, list):
            return [_coerce(val) for val in v]
        return v

    try:
        canonical_data = canonical_json(_coerce(material))
        return hashlib.sha256(canonical_data.encode()).hexdigest()
    except Exception as e:
        msg = f"Failed to compute decision material hash: {e}"
        raise ValidationError(msg) from e


def _check_schema_version(obj: Any) -> None:  # noqa: ANN401
    """Enforce schema-version compatibility.

    Raises ValidationError if there is a major version mismatch with
    current system (expects '1.x.x').
    """
    if hasattr(obj, "schema_version"):
        ver = obj.schema_version
        if ver and isinstance(ver, str):
            parts = ver.split(".")
            if parts and parts[0] != "1":
                msg = f"Schema version mismatch: expected major version 1, got {ver}"
                raise ValidationError(msg)


class RiskStateStore(ABC):
    """Port defining operations for drawdown state, kill switches, and token revocation.

    Implementors must persist drawdown tracking state, kill switch activation
    flags, and revocation sets for risk approval tokens.

    Schema-Version Compatibility:
        Implementors should verify schema major version compatibility on write.
        If a major mismatch occurs, raise a ValidationError.

    Failure Behavior:
        Must raise DataError on database or network connection errors.
        Must raise ValidationError on invalid argument types or constraints.
        Calls should fail closed if live execution cannot verify persistence.
    """

    @abstractmethod
    def get_drawdown_state(
        self, strategy_id: str | None = None
    ) -> DrawdownState | None:
        """Retrieve the drawdown state for the portfolio or a specific strategy.

        Args:
            strategy_id: Optional strategy identifier.

        Returns:
            DrawdownState | None: The active drawdown state, or None.

        Raises:
            DataError: If persistence is unavailable.
        """

    @abstractmethod
    def save_drawdown_state(
        self, state: DrawdownState, strategy_id: str | None = None
    ) -> None:
        """Save the drawdown state.

        Args:
            state: The DrawdownState model (required).
            strategy_id: Optional strategy identifier.

        Raises:
            DataError: If persistence is unavailable.
            ValidationError: If inputs are invalid or schema version mismatches.
        """

    @abstractmethod
    def get_kill_switch_state(
        self, scope: str, target: str
    ) -> tuple[
        KillSwitchStateEnum, KillSwitchReason | None, datetime | None, str | None
    ]:
        """Retrieve kill-switch state tuple.

        Args:
            scope: Target scope string (e.g. 'global', 'symbol') (required).
            target: Target scope identifier (e.g. 'EURUSD', '*') (required).

        Returns:
            (state, reason, triggered_at, triggered_by)

        Raises:
            DataError: If persistence is unavailable.
        """

    @abstractmethod
    def save_kill_switch_state(
        self,
        scope: str,
        target: str,
        state: KillSwitchStateEnum,
        reason: KillSwitchReason | None = None,
        triggered_at: datetime | None = None,
        triggered_by: str | None = None,
    ) -> None:
        """Save kill-switch state updates.

        Args:
            scope: Target scope (required).
            target: Target identifier (required).
            state: Target KillSwitchStateEnum (required).
            reason: Optional trigger reason.
            triggered_at: Optional triggering timestamp.
            triggered_by: Optional triggering operator.

        Raises:
            DataError: If persistence is unavailable.
            ValidationError: If inputs are invalid or schema mismatches.
        """

    @abstractmethod
    def is_token_revoked(self, token_id: str) -> bool:
        """Check if a decision token is marked as revoked.

        Args:
            token_id: Required token identifier.

        Returns:
            bool: True if token is revoked.

        Raises:
            DataError: If persistence is unavailable.
        """

    @abstractmethod
    def revoke_token(self, token_id: str) -> None:
        """Revoke a decision token.

        Args:
            token_id: Required token identifier.

        Raises:
            DataError: If persistence is unavailable.
            ValidationError: If token_id is empty.
        """


class RiskAuditSink(ABC):
    """Port defining write and verification access to the audit event chain.

    Failure Behavior:
        Must raise DataError on persistence failures (failing closed).
        Must raise ValidationError on malformed events.
    """

    @abstractmethod
    def write_event(self, event: RiskAuditEvent) -> None:
        """Append a validated event block to the audit store.

        Args:
            event: The validated RiskAuditEvent block (required).

        Raises:
            DataError: If persistence is unavailable.
            ValidationError: If event is malformed or schema version mismatches.
        """

    @abstractmethod
    def get_last_event(self) -> RiskAuditEvent | None:
        """Retrieve the latest audit event block in the chain.

        Returns:
            RiskAuditEvent | None: The latest event block or None.

        Raises:
            DataError: If persistence is unavailable.
        """

    @abstractmethod
    def get_all_events(self) -> list[RiskAuditEvent]:
        """Retrieve all audit events chronologically.

        Returns:
            list[RiskAuditEvent]: Sorted audit event logs.

        Raises:
            DataError: If persistence is unavailable.
        """


class RiskPolicyStore(ABC):
    """Port defining read and write operations for active policy rules.

    Failure Behavior:
        Must raise DataError on storage failures.
        Must raise ValidationError on schema conflicts or validation errors.
    """

    @abstractmethod
    def get_rules(self) -> list[PolicyRule]:
        """Retrieve all active policy rules.

        Returns:
            list[PolicyRule]: Active policy rules.

        Raises:
            DataError: If persistence is unavailable.
        """

    @abstractmethod
    def save_rule(self, rule: PolicyRule) -> None:
        """Store or update a policy rule.

        Args:
            rule: The PolicyRule model (required).

        Raises:
            DataError: If persistence is unavailable.
            ValidationError: If rule is invalid or schema version mismatches.
        """


class RiskDecisionStore(ABC):
    """Port defining operations for indexing and retrieving risk governor decisions.

    Supports idempotent indexing based on compound identifiers.

    Failure Behavior:
        Must raise DataError on persistence failures.
        Must raise ValidationError on schema mismatches or invalid parameters.
    """

    @abstractmethod
    def get_decision(self, decision_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by ID.

        Args:
            decision_id: Required unique identifier.

        Returns:
            RiskDecisionPackage | None: The stored decision package or None.

        Raises:
            DataError: If persistence is unavailable.
        """

    @abstractmethod
    def save_decision(self, decision: RiskDecisionPackage) -> None:
        """Persist decision package with idempotency handling.

        Idempotency rules:
            - Keyed by request ID, workflow ID, signal ID, and decision material hash.
            - Overwriting with the same decision payload must succeed.
            - Conflict on request ID with a different decision must raise DataError.

        Args:
            decision: RiskDecisionPackage (required).

        Raises:
            DataError: If duplicate request/keys conflict or store is unavailable.
            ValidationError: If inputs are invalid or schema version mismatches.
        """

    @abstractmethod
    def get_decision_by_request_id(self, request_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by original request ID.

        Args:
            request_id: Required original request ID.

        Returns:
            RiskDecisionPackage | None: Stored package or None.

        Raises:
            DataError: If persistence is unavailable.
        """

    @abstractmethod
    def get_decision_by_key(
        self,
        request_id: str,
        workflow_id: str,
        signal_id: str,
        decision_material_hash: str,
    ) -> RiskDecisionPackage | None:
        """Retrieve decision by original idempotency keys.

        Args:
            request_id: Required correlation request ID.
            workflow_id: Required workflow run identifier.
            signal_id: Signal identifier.
            decision_material_hash: Hash of decision material.

        Returns:
            RiskDecisionPackage | None: The matched decision package, or None.

        Raises:
            DataError: If persistence is unavailable.
            ValidationError: If inputs are invalid.
        """


class InMemoryRiskStateStore(
    RiskStateStore, RiskAuditSink, RiskPolicyStore, RiskDecisionStore
):
    """Thread-safe all-in-one in-memory implementation of risk storage ports."""

    def __init__(self) -> None:
        """Initialize the store maps and lock."""
        self._lock = RLock()
        self._simulate_failure: bool = False
        self._drawdown_states: dict[str, DrawdownState] = {}
        self._kill_switches: dict[
            str,
            dict[
                str,
                tuple[
                    KillSwitchStateEnum,
                    KillSwitchReason | None,
                    datetime | None,
                    str | None,
                ],
            ],
        ] = {
            "global": {"*": (KillSwitchStateEnum.INACTIVE, None, None, None)},
            "portfolio": {"*": (KillSwitchStateEnum.INACTIVE, None, None, None)},
            "strategy": {},
            "symbol": {},
            "currency": {},
        }
        self._revoked_tokens: set[str] = set()
        self._audit_events: list[RiskAuditEvent] = []
        self._policy_rules: dict[str, PolicyRule] = {}
        self._decisions: dict[str, RiskDecisionPackage] = {}
        self._decisions_by_request: dict[str, RiskDecisionPackage] = {}
        self._decisions_by_idempotency_key: dict[
            tuple[str, str, str, str], RiskDecisionPackage
        ] = {}

    def set_simulate_failure(self, enabled: bool) -> None:
        """Enable or disable simulated persistence failures for testing."""
        self._simulate_failure = enabled

    def _check_failure(self) -> None:
        """Raise DataError if simulated failure is enabled."""
        if self._simulate_failure:
            raise DataError("Simulated persistence failure.")

    def get_drawdown_state(
        self, strategy_id: str | None = None
    ) -> DrawdownState | None:
        """Retrieve the drawdown state from memory."""
        self._check_failure()
        key = strategy_id or "portfolio"
        with self._lock:
            return self._drawdown_states.get(key)

    def save_drawdown_state(
        self, state: DrawdownState, strategy_id: str | None = None
    ) -> None:
        """Save the drawdown state in memory."""
        self._check_failure()
        if not isinstance(state, DrawdownState):
            raise ValidationError("Invalid DrawdownState object.")
        _check_schema_version(state)
        key = strategy_id or "portfolio"
        with self._lock:
            self._drawdown_states[key] = state

    def get_kill_switch_state(
        self, scope: str, target: str
    ) -> tuple[
        KillSwitchStateEnum, KillSwitchReason | None, datetime | None, str | None
    ]:
        """Retrieve kill-switch state from memory."""
        self._check_failure()
        with self._lock:
            scope_map = self._kill_switches.get(scope)
            if scope_map is None:
                return KillSwitchStateEnum.INACTIVE, None, None, None
            return scope_map.get(
                target, (KillSwitchStateEnum.INACTIVE, None, None, None)
            )

    def save_kill_switch_state(
        self,
        scope: str,
        target: str,
        state: KillSwitchStateEnum,
        reason: KillSwitchReason | None = None,
        triggered_at: datetime | None = None,
        triggered_by: str | None = None,
    ) -> None:
        """Update kill-switch state in memory."""
        self._check_failure()
        if scope not in self._kill_switches:
            msg = f"Invalid kill switch scope: {scope}"
            raise ValidationError(msg)
        with self._lock:
            t = triggered_at or datetime.now(UTC)
            by = triggered_by or "system"
            self._kill_switches[scope][target] = (state, reason, t, by)

    def is_token_revoked(self, token_id: str) -> bool:
        """Check token revocation in memory."""
        self._check_failure()
        with self._lock:
            return token_id in self._revoked_tokens

    def revoke_token(self, token_id: str) -> None:
        """Add token to revocation set."""
        self._check_failure()
        if not token_id:
            raise ValidationError("token_id is required.")
        with self._lock:
            self._revoked_tokens.add(token_id)

    def write_event(self, event: RiskAuditEvent) -> None:
        """Write audit event block."""
        self._check_failure()
        if not isinstance(event, RiskAuditEvent):
            raise ValidationError("Invalid RiskAuditEvent object.")
        _check_schema_version(event)
        with self._lock:
            self._audit_events.append(event)

    def get_last_event(self) -> RiskAuditEvent | None:
        """Retrieve the latest block in memory."""
        self._check_failure()
        with self._lock:
            if not self._audit_events:
                return None
            return self._audit_events[-1]

    def get_all_events(self) -> list[RiskAuditEvent]:
        """Retrieve all events."""
        self._check_failure()
        with self._lock:
            return list(self._audit_events)

    def get_rules(self) -> list[PolicyRule]:
        """Retrieve active policy rules."""
        self._check_failure()
        with self._lock:
            return list(self._policy_rules.values())

    def save_rule(self, rule: PolicyRule) -> None:
        """Store policy rule in memory."""
        self._check_failure()
        if not isinstance(rule, PolicyRule):
            raise ValidationError("Invalid PolicyRule object.")
        _check_schema_version(rule)
        with self._lock:
            self._policy_rules[rule.rule_id] = rule

    def get_decision(self, decision_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by ID."""
        self._check_failure()
        with self._lock:
            return self._decisions.get(decision_id)

    def save_decision(self, decision: RiskDecisionPackage) -> None:
        """Persist decision in memory with idempotency handling.

        Checks:
            - Schema version compatibility.
            - Idempotency keyed by request ID.
            - Idempotency compound key:
              (request_id, workflow_id, signal_id, material_hash).
        """
        self._check_failure()
        if not isinstance(decision, RiskDecisionPackage):
            raise ValidationError("Invalid RiskDecisionPackage object.")
        _check_schema_version(decision)

        # Extract compound key fields
        req_id = decision.request_id
        wf_id = decision.workflow_id
        details = decision.details or {}
        proposed = details.get("proposed_action") or {}
        sig_id = proposed.get("signal_id") or details.get("signal_id") or ""
        mat_hash = details.get(
            "decision_material_hash"
        ) or compute_decision_material_hash(decision)

        key = (req_id, wf_id, str(sig_id), str(mat_hash))

        with self._lock:
            # Check duplicate request same material idempotency
            existing = self._decisions_by_request.get(decision.request_id)
            if existing is not None and existing.decision_id != decision.decision_id:
                # If existing request ID matches but different status or fields,
                # raise DataError
                msg = (
                    f"Idempotency conflict: request_id '{decision.request_id}' "
                    f"already processed with decision '{existing.decision_id}'."
                )
                raise DataError(msg)

            # Check compound key idempotency
            existing_by_key = self._decisions_by_idempotency_key.get(key)
            if (
                existing_by_key is not None
                and existing_by_key.decision_id != decision.decision_id
            ):
                msg = (
                    f"Idempotency conflict: decision for key {key} "
                    f"already processed with decision "
                    f"'{existing_by_key.decision_id}'."
                )
                raise DataError(msg)

            self._decisions[decision.decision_id] = decision
            self._decisions_by_request[decision.request_id] = decision
            self._decisions_by_idempotency_key[key] = decision

    def get_decision_by_request_id(self, request_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by request ID."""
        self._check_failure()
        with self._lock:
            return self._decisions_by_request.get(request_id)

    def get_decision_by_key(
        self,
        request_id: str,
        workflow_id: str,
        signal_id: str,
        decision_material_hash: str,
    ) -> RiskDecisionPackage | None:
        """Retrieve decision by idempotency keys from memory."""
        self._check_failure()
        if not request_id or not workflow_id:
            raise ValidationError("request_id and workflow_id are required.")
        key = (request_id, workflow_id, signal_id or "", decision_material_hash or "")
        with self._lock:
            return self._decisions_by_idempotency_key.get(key)
