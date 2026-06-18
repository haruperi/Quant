"""Live state contracts module.

Defines KillSwitchState and LiveSessionState.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.contracts.base import Contract


class KillSwitchState(Contract):
    """The canonical safety kill-switch configuration."""

    active: bool = Field(
        ...,
        description=(
            "Whether the emergency kill switch is active (blocking trade edits)."
        ),
    )
    triggered_at: str | None = Field(
        default=None, description="UTC ISO 8601 trigger timestamp."
    )
    triggered_by: str | None = Field(
        default=None, description="Identity triggering switch."
    )
    reason: str | None = Field(
        default=None, description="Detailed text explaining trigger cause."
    )


class LiveSessionState(Contract):
    """Execution status monitoring state for a live strategy trading run."""

    session_id: str = Field(..., description="Live session ID.")
    environment_mode: Literal["research", "simulation", "paper", "live"] = Field(
        ...,
        description="Target execution environment tier.",
    )
    provider_status: str = Field(
        ...,
        description=("Provider connection status (e.g., connected, disconnected)."),
    )
    risk_status: str = Field(..., description="Pre-trade validation status.")
    kill_switch_state: KillSwitchState = Field(
        ..., description="Safety kill switch snapshot state."
    )
    reconciliation_status: str = Field(
        ..., description="State sync reconciliation category."
    )
    operator_approval_status: str = Field(
        ...,
        description=("Operator manual approval state (e.g. pending, approved)."),
    )
