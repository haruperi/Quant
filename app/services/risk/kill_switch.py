# ruff: noqa: E501, PLW0603, ARG001
"""Risk kill switch and step-down controls.

This module implements the global kill switch state machine and graduated step-down controls.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from app.utils.errors import ValidationError

if TYPE_CHECKING:
    from app.services.risk.models import RiskConfig

# Simulated persistent store for kill switch
_GLOBAL_KILL_SWITCH_TRIGGERED = False
_GLOBAL_KILL_SWITCH_REASON = ""
_GLOBAL_STEP_DOWN_LEVEL = Decimal("1.0")  # Multiplier applied to position limits


class KillSwitchStateMachine:
    """State machine governing global kill switch activation and restoration."""

    def __init__(self) -> None:
        """Initialize state machine."""

    @property
    def state(self) -> Literal["inactive", "active", "unknown"]:
        """Return the current state of the kill switch."""
        if _GLOBAL_KILL_SWITCH_TRIGGERED:
            return "active"
        return "inactive"

    def trigger(self, reason: str) -> None:
        """Trigger global order block and invalidate approvals."""
        global _GLOBAL_KILL_SWITCH_TRIGGERED, _GLOBAL_KILL_SWITCH_REASON
        _GLOBAL_KILL_SWITCH_TRIGGERED = True
        _GLOBAL_KILL_SWITCH_REASON = reason

    def resume(self, approval_id: str) -> None:
        """Clear trigger and restore trading status with authorization credentials."""
        global _GLOBAL_KILL_SWITCH_TRIGGERED, _GLOBAL_KILL_SWITCH_REASON
        if not approval_id:
            raise ValidationError("Approval ID is required to resume from kill switch.")
        _GLOBAL_KILL_SWITCH_TRIGGERED = False
        _GLOBAL_KILL_SWITCH_REASON = ""


class KillSwitchService:
    """Service coordinates kill switch triggers and validation queries."""

    def __init__(self) -> None:
        """Initialize service."""
        self.state_machine = KillSwitchStateMachine()

    def check_kill_switch(self) -> bool:
        """Return True if kill switch is currently active."""
        return self.state_machine.state == "active"

    def evaluate_new_entry_block(self) -> bool:
        """Return True if new orders are blocked."""
        return self.check_kill_switch()


def check_risk_kill_switch(
    scope: dict[str, str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Exposed official tool wrapper checking kill switch state."""
    service = KillSwitchService()
    active = service.check_kill_switch()

    # Standard tool envelope structure returned inside AI tool context
    return {
        "status": "success",
        "message": f"Kill switch check completed. Active: {active}",
        "data": {
            "kill_switch_active": active,
            "reason": _GLOBAL_KILL_SWITCH_REASON if active else "",
            "scope": scope or {},
        },
        "error": None,
    }


def classify_drawdown_regime(
    drawdown_pct: Decimal,
    risk_config: RiskConfig,
) -> Literal["normal", "caution", "restricted", "blocked", "kill_switch_required"]:
    """Classify the portfolio drawdown regime based on configured limits."""
    # Graduated bands based on daily loss threshold (default 5%)
    limit = risk_config.max_daily_loss_pct

    if drawdown_pct <= limit * Decimal("0.3"):  # <= 1.5%
        return "normal"
    if drawdown_pct <= limit * Decimal("0.6"):  # <= 3%
        return "caution"
    if drawdown_pct <= limit * Decimal("0.9"):  # <= 4.5%
        return "restricted"
    if drawdown_pct < limit:  # < 5.0%
        return "blocked"
    return "kill_switch_required"


class StepDownControls:
    """Manages graduated risk step-down level multipliers based on drawdown state."""

    @staticmethod
    def get_risk_multiplier(drawdown_state: str) -> Decimal:
        """Return position size / exposure limit multiplier."""
        global _GLOBAL_STEP_DOWN_LEVEL
        if drawdown_state == "normal":
            _GLOBAL_STEP_DOWN_LEVEL = Decimal("1.0")
        elif drawdown_state == "caution":
            _GLOBAL_STEP_DOWN_LEVEL = Decimal("0.75")
        elif drawdown_state == "restricted":
            _GLOBAL_STEP_DOWN_LEVEL = Decimal("0.50")
        elif drawdown_state in ("blocked", "kill_switch_required"):
            _GLOBAL_STEP_DOWN_LEVEL = Decimal("0.0")
        return _GLOBAL_STEP_DOWN_LEVEL

    @staticmethod
    def reset() -> None:
        """Reset step down level back to full size."""
        global _GLOBAL_STEP_DOWN_LEVEL
        _GLOBAL_STEP_DOWN_LEVEL = Decimal("1.0")
