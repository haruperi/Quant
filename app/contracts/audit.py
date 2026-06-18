# ruff: noqa: EM102
"""Audit trail contracts module.

Defines AuditEvent.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from app.contracts.base import Contract
from app.utils.normalization import normalize_timestamp


class AuditEvent(Contract):
    """The canonical audit log record contract."""

    event_id: str = Field(..., description="Unique audit event ID.")
    event_type: str = Field(
        ..., description="Audit event category (e.g. risk.policy_change, trading.fill)."
    )
    severity: Literal["info", "warning", "error", "critical"] = Field(
        ..., description="Audit event severity level."
    )
    actor: str = Field(
        ..., description="The user, service account, or agent initiating action."
    )
    subject: str = Field(..., description="The target entity being modified/queried.")
    action: str = Field(
        ...,
        description="The specific operation performed (e.g. approve, reject, execute).",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="References to verification payloads or data hashes.",
    )
    redacted_payload_hash: str | None = Field(
        default=None,
        description="SHA256 hash of the fully redacted operation details.",
    )
    timestamp: str = Field(..., description="UTC ISO 8601 creation time of event.")

    @field_validator("timestamp")
    @classmethod
    def validate_audit_time(cls, v: str) -> str:
        """Validate timestamp format."""
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            raise ValueError(f"Invalid timestamp: {v}") from e
