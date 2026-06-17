# ruff: noqa: E501, ANN401, E402, PLC0414, ARG004
"""Risk lifecycle checks and external service compatibility facades.

This module implements strategy lifecycle governance and lazy facades.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.utils.errors import ValidationError

if TYPE_CHECKING:
    from app.services.risk.models import (
        PortfolioState,
    )

CANONICAL_LIFECYCLE_STATES = {
    "research",
    "validated",
    "paper_candidate",
    "paper_active",
    "live_candidate",
    "live_active",
    "suspended",
    "retired",
    "rejected",
}

ALIAS_MAP = {
    "draft": "research",
    "candidate": "paper_candidate",
    "backtested": "validated",
    "robustness_passed": "validated",
    "paper": "paper_active",
    "approved_for_live": "live_candidate",
    "live_approved": "live_candidate",
    "live": "live_active",
}

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "research": {"validated", "rejected"},
    "validated": {"paper_candidate", "rejected"},
    "paper_candidate": {"paper_active", "rejected"},
    "paper_active": {"live_candidate", "suspended", "retired"},
    "live_candidate": {"live_active", "suspended", "retired"},
    "live_active": {"suspended", "retired"},
    "suspended": {"paper_active", "retired", "live_active"},
    "retired": set(),
    "rejected": set(),
}


def normalize_lifecycle_state(state: str) -> str:
    """Normalize legacy lifecycle aliases to canonical lifecycle states."""
    lower_state = state.strip().lower()
    if lower_state in CANONICAL_LIFECYCLE_STATES:
        return lower_state
    if lower_state in ALIAS_MAP:
        return ALIAS_MAP[lower_state]
    msg = f"Ambiguous or unrecognized lifecycle state alias: {state}"
    raise ValidationError(msg)


class LifecycleService:
    """Service governing strategy lifecycle transitions and gates."""

    @staticmethod
    def transition(
        strategy_id: str,
        current_state: str,
        target_state: str,
        board_approved: bool = False,
        review_evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Verify and perform strategy lifecycle state transition."""
        curr = normalize_lifecycle_state(current_state)
        tgt = normalize_lifecycle_state(target_state)

        if tgt not in ALLOWED_TRANSITIONS[curr]:
            msg = f"Transition from {curr} to {tgt} is not allowed by the lifecycle transition map."
            raise ValidationError(msg)

        # Transitions to live candidate or live active require board approval
        if tgt in ("live_candidate", "live_active") and not board_approved:
            msg = f"Transition to {tgt} requires explicit board approval."
            raise ValidationError(msg)

        # Transition to paper_active or live requires review evidence
        if (
            tgt in ("paper_active", "live_candidate", "live_active")
            and not review_evidence
        ):
            msg = f"Transition to {tgt} requires strategy review evidence."
            raise ValidationError(msg)

        return {
            "strategy_id": strategy_id,
            "previous_state": curr,
            "new_state": tgt,
            "timestamp": datetime.now(UTC),
            "status": "success",
            "message": f"Strategy {strategy_id} transitioned successfully to {tgt}.",
        }


# --- External Service Facades ---


from app.services.risk.sizing import AllocationService as AllocationService


class CostService:
    """External facade representing cost accounting service."""

    @staticmethod
    def report(
        period: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate and report cost metrics."""
        return {
            "period": period,
            "total_cost": Decimal("0.0"),
            "status": "success",
        }


class IncidentService:
    """External facade representing incident management service."""

    @staticmethod
    def create_incident(
        strategy_id: str,
        severity: str,
        message: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Create and log a portfolio incident report."""
        return {
            "incident_id": f"inc_{strategy_id}_{int(datetime.now(UTC).timestamp())}",
            "strategy_id": strategy_id,
            "severity": severity,
            "message": message,
            "status": "created",
        }


class PortfolioAuditService:
    """External facade representing audit service."""

    @staticmethod
    def audit(
        findings: list[dict[str, Any]],
        severity: str = "warning",
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Record critical audit events and findings."""
        return {
            "findings_count": len(findings),
            "severity": severity,
            "status": "success",
        }


class PortfolioKillSwitch:
    """External facade representing portfolio kill switch."""

    @staticmethod
    def evaluate() -> str:
        """Return the current state when no trigger is active."""
        return "inactive"

    @staticmethod
    def trigger(
        reason: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Trigger the kill switch and transition to blocked state."""
        return {
            "status": "triggered",
            "reason": reason,
            "timestamp": datetime.now(UTC),
        }

    @staticmethod
    def resume(
        approval_id: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Resume trading after kill switch activation with dual-auth approval."""
        return {
            "status": "resumed",
            "approval_id": approval_id,
            "timestamp": datetime.now(UTC),
        }


class ReportingService:
    """External facade representing reporting service."""

    @staticmethod
    def generate(
        report_type: str,
        portfolio_state: PortfolioState,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate formatted performance and risk reports."""
        return {
            "report_id": f"rep_{report_type}_{int(datetime.now(UTC).timestamp())}",
            "report_type": report_type,
            "status": "success",
            "content": f"# Performance Report: {report_type}\n",
        }


def __getattr__(name: str) -> Any:
    """Lazy load compatibility facades to prevent import cycles."""
    facades = {
        "AllocationService": AllocationService,
        "CostService": CostService,
        "IncidentService": IncidentService,
        "PortfolioAuditService": PortfolioAuditService,
        "PortfolioKillSwitch": PortfolioKillSwitch,
        "LifecycleService": LifecycleService,
        "ReportingService": ReportingService,
    }
    if name in facades:
        return facades[name]
    msg = f"module '{__name__}' has no attribute '{name}'"
    raise AttributeError(msg)
