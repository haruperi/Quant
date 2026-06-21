# ruff: noqa: TC001
"""Risk contracts module.

Defines RiskDecision, RiskRejection, PositionSizingResult, and RiskAuditEvent.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from app.contracts.base import Contract
from app.contracts.trading import OrderIntent


class RiskRejection(Contract):
    """Details explaining why a strategy proposal or signal was rejected."""

    code: str = Field(..., description="Stable, deterministic risk error code.")
    severity: Literal["info", "warning", "error", "critical"] = Field(
        ..., description="Severity of the violation."
    )
    reason: str = Field(..., description="Human-readable reason for rejection.")
    violated_limit: str | None = Field(
        default=None, description="Name of the violated risk limit."
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Audit material proving violation."
    )
    remediation_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Actionable steps or parameters for remediation.",
    )


class PositionSizingResult(Contract):
    """Details of the position sizing step."""

    requested_size: float = Field(
        ..., ge=0.0, description="Requested trade volume size in lots."
    )
    approved_size: float = Field(
        ..., ge=0.0, description="Approved trade volume size in lots."
    )
    sizing_method: str = Field(
        ..., description="Position calculator type (e.g. fixed_fractional, kelly)."
    )
    constraints_applied: list[str] = Field(
        default_factory=list,
        description="Limit/constraints evaluated during sizing.",
    )
    risk_contribution: float = Field(
        ...,
        ge=0.0,
        description="Calculated portfolio risk or margin contribution.",
    )


class RiskDecision(Contract):
    """The canonical outcome of the risk review process."""

    decision_id: str = Field(..., description="Unique decision ID.")
    signal_id: str = Field(
        ..., description="Target StrategySignal contract hash or ID."
    )
    approved: bool = Field(..., description="True if proposal passes all risk limits.")
    sizing: PositionSizingResult | None = Field(
        default=None, description="Applied sizing details."
    )
    rejection: RiskRejection | None = Field(
        default=None, description="Applied rejection details."
    )
    approved_order_intent: OrderIntent | None = Field(
        default=None,
        description="Approved OrderIntent produced after all risk gates pass.",
    )
    risk_signature: str | None = Field(
        default=None,
        description="Cryptographic or validation signature of decision state.",
    )

    @model_validator(mode="after")
    def validate_outcome_consistency(self) -> RiskDecision:
        """Enforce mutual exclusivity of approval and rejection states.

        A non-approved decision must carry a ``RiskRejection`` explaining
        why.  An approved decision must not carry a rejection, as that
        would produce an ambiguous audit record.

        Returns:
            The validated RiskDecision instance.

        Raises:
            ValueError: If a non-approved decision has no rejection, or if
                an approved decision carries a rejection object.
        """
        if not self.approved and self.rejection is None:
            raise ValueError("Rejection details must be provided if not approved.")
        if self.approved and self.rejection is not None:
            raise ValueError("Rejection details must not be provided if approved.")
        return self


class RiskAuditEvent(Contract):
    """Event payload generated during risk checks."""

    event_id: str = Field(..., description="Event identifier.")
    event_type: str = Field(default="risk.audit", description="Risk audit type.")
    decision_id: str = Field(..., description="Decision identifier.")
    policy_name: str = Field(..., description="Evaluated policy rule category.")
    action_taken: str = Field(
        ..., description="Outcome action (e.g. block, approve, scale)."
    )
    payload_hash: str = Field(..., description="Hash code of the evaluated signal.")
    severity: Literal["info", "warning", "error", "critical"] = Field(
        ..., description="Event severity."
    )
