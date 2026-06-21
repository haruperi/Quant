"""Audit trail contracts module.

Defines AuditEvent.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.contracts.base import Contract


class AuditEvent(Contract):
    """The canonical audit log record contract.

    The event timestamp is carried by ``Contract.created_at``, which is
    set at construction time to UTC now. Consumers building audit timelines
    should read ``created_at`` as the authoritative event time.

    Attributes:
        event_id: Unique audit event identifier.
        event_type: Dotted category string (e.g. ``risk.policy_change``).
        severity: Event severity level.
        actor: User, service account, or agent initiating the action.
        subject: Target entity being modified or queried.
        action: Specific operation performed (e.g. ``approve``, ``execute``).
        evidence: References to verification payloads or data hashes.
        redacted_payload_hash: SHA256 hash of the fully redacted operation
            details, suitable for audit record integrity checks.
    """

    event_id: str = Field(..., description="Unique audit event ID.")
    event_type: str = Field(
        ...,
        description=("Audit event category (e.g. risk.policy_change, trading.fill)."),
    )
    severity: Literal["info", "warning", "error", "critical"] = Field(
        ..., description="Audit event severity level."
    )
    actor: str = Field(
        ...,
        description="The user, service account, or agent initiating action.",
    )
    subject: str = Field(
        ..., description="The target entity being modified or queried."
    )
    action: str = Field(
        ...,
        description=(
            "The specific operation performed (e.g. approve, reject, execute)."
        ),
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="References to verification payloads or data hashes.",
    )
    redacted_payload_hash: str | None = Field(
        default=None,
        description="SHA256 hash of the fully redacted operation details.",
    )
