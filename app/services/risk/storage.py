"""Risk governance storage ports and in-memory store.

Defines the abstract repository interfaces for persisting risk state, policies,
decisions, and audit events, and provides a thread-safe in-memory store.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from threading import RLock

from app.services.risk.models import (
    DrawdownState,
    KillSwitchReason,
    KillSwitchStateEnum,
    PolicyRule,
    RiskAuditEvent,
    RiskDecisionPackage,
)
from app.utils.errors import DataError, ValidationError


class RiskStateStore(ABC):
    """Port defining operations for drawdown state, kill switches, and token revocation.

    Implementors must persist drawdown tracking state, kill switch activation
    flags, and revocation sets for risk approval tokens.
    """

    @abstractmethod
    def get_drawdown_state(
        self, strategy_id: str | None = None
    ) -> DrawdownState | None:
        """Retrieve the drawdown state for the portfolio or a specific strategy."""

    @abstractmethod
    def save_drawdown_state(
        self, state: DrawdownState, strategy_id: str | None = None
    ) -> None:
        """Save the drawdown state."""

    @abstractmethod
    def get_kill_switch_state(
        self, scope: str, target: str
    ) -> tuple[
        KillSwitchStateEnum, KillSwitchReason | None, datetime | None, str | None
    ]:
        """Retrieve kill-switch state tuple.

        Returns (state, reason, triggered_at, triggered_by).
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
        """Save kill-switch state updates."""

    @abstractmethod
    def is_token_revoked(self, token_id: str) -> bool:
        """Check if a decision token is marked as revoked."""

    @abstractmethod
    def revoke_token(self, token_id: str) -> None:
        """Revoke a decision token."""


class RiskAuditSink(ABC):
    """Port defining write and verification access to the audit event chain."""

    @abstractmethod
    def write_event(self, event: RiskAuditEvent) -> None:
        """Append a validated event block to the audit store."""

    @abstractmethod
    def get_last_event(self) -> RiskAuditEvent | None:
        """Retrieve the latest audit event block in the chain."""

    @abstractmethod
    def get_all_events(self) -> list[RiskAuditEvent]:
        """Retrieve all audit events chronologically."""


class RiskPolicyStore(ABC):
    """Port defining read and write operations for active policy rules."""

    @abstractmethod
    def get_rules(self) -> list[PolicyRule]:
        """Retrieve all active policy rules."""

    @abstractmethod
    def save_rule(self, rule: PolicyRule) -> None:
        """Store or update a policy rule."""


class RiskDecisionStore(ABC):
    """Port defining operations for indexing and retrieving risk governor decisions."""

    @abstractmethod
    def get_decision(self, decision_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by ID."""

    @abstractmethod
    def save_decision(self, decision: RiskDecisionPackage) -> None:
        """Persist decision package with idempotency handling."""

    @abstractmethod
    def get_decision_by_request_id(self, request_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by original request ID."""


class InMemoryRiskStateStore(
    RiskStateStore, RiskAuditSink, RiskPolicyStore, RiskDecisionStore
):
    """Thread-safe all-in-one in-memory implementation of risk storage ports."""

    def __init__(self) -> None:
        """Initialize the store maps and lock."""
        self._lock = RLock()
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

    def get_drawdown_state(
        self, strategy_id: str | None = None
    ) -> DrawdownState | None:
        """Retrieve the drawdown state from memory."""
        key = strategy_id or "portfolio"
        with self._lock:
            return self._drawdown_states.get(key)

    def save_drawdown_state(
        self, state: DrawdownState, strategy_id: str | None = None
    ) -> None:
        """Save the drawdown state in memory."""
        key = strategy_id or "portfolio"
        if not isinstance(state, DrawdownState):
            raise ValidationError("Invalid DrawdownState object.")
        with self._lock:
            self._drawdown_states[key] = state

    def get_kill_switch_state(
        self, scope: str, target: str
    ) -> tuple[
        KillSwitchStateEnum, KillSwitchReason | None, datetime | None, str | None
    ]:
        """Retrieve kill-switch state from memory."""
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
        if scope not in self._kill_switches:
            msg = f"Invalid kill switch scope: {scope}"
            raise ValidationError(msg)
        with self._lock:
            t = triggered_at or datetime.now(UTC)
            by = triggered_by or "system"
            self._kill_switches[scope][target] = (state, reason, t, by)

    def is_token_revoked(self, token_id: str) -> bool:
        """Check token revocation in memory."""
        with self._lock:
            return token_id in self._revoked_tokens

    def revoke_token(self, token_id: str) -> None:
        """Add token to revocation set."""
        if not token_id:
            raise ValidationError("token_id is required.")
        with self._lock:
            self._revoked_tokens.add(token_id)

    def write_event(self, event: RiskAuditEvent) -> None:
        """Write audit event block."""
        if not isinstance(event, RiskAuditEvent):
            raise ValidationError("Invalid RiskAuditEvent object.")
        with self._lock:
            self._audit_events.append(event)

    def get_last_event(self) -> RiskAuditEvent | None:
        """Retrieve the latest block in memory."""
        with self._lock:
            if not self._audit_events:
                return None
            return self._audit_events[-1]

    def get_all_events(self) -> list[RiskAuditEvent]:
        """Retrieve all events."""
        with self._lock:
            return list(self._audit_events)

    def get_rules(self) -> list[PolicyRule]:
        """Retrieve active policy rules."""
        with self._lock:
            return list(self._policy_rules.values())

    def save_rule(self, rule: PolicyRule) -> None:
        """Store policy rule in memory."""
        if not isinstance(rule, PolicyRule):
            raise ValidationError("Invalid PolicyRule object.")
        with self._lock:
            self._policy_rules[rule.rule_id] = rule

    def get_decision(self, decision_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by ID."""
        with self._lock:
            return self._decisions.get(decision_id)

    def save_decision(self, decision: RiskDecisionPackage) -> None:
        """Persist decision in memory with idempotency handling."""
        if not isinstance(decision, RiskDecisionPackage):
            raise ValidationError("Invalid RiskDecisionPackage object.")
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
            self._decisions[decision.decision_id] = decision
            self._decisions_by_request[decision.request_id] = decision

    def get_decision_by_request_id(self, request_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by request ID."""
        with self._lock:
            return self._decisions_by_request.get(request_id)
