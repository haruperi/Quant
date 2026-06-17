from decimal import Decimal

import pytest
from app.services.risk.kill_switch import (
    KillSwitchService,
    KillSwitchStateMachine,
    StepDownControls,
    classify_drawdown_regime,
)
from app.services.risk.models import RiskConfig
from app.utils.errors import ValidationError


def test_kill_switch_state_machine():
    sm = KillSwitchStateMachine()
    # Initial inactive
    assert sm.state == "inactive"

    # Trigger active
    sm.trigger("Adverse price spike")
    assert sm.state == "active"

    # Try resume without approval id raises ValidationError
    with pytest.raises(ValidationError):
        sm.resume("")

    # Resume clear status
    sm.resume("auth_approver_123")
    assert sm.state == "inactive"


def test_kill_switch_service():
    service = KillSwitchService()
    # Reset
    if service.check_kill_switch():
        service.state_machine.resume("reset")

    assert not service.check_kill_switch()
    assert not service.evaluate_new_entry_block()

    service.state_machine.trigger("test trigger")
    assert service.check_kill_switch()
    assert service.evaluate_new_entry_block()

    # Cleanup
    service.state_machine.resume("cleanup")


def test_drawdown_regime_classification():
    cfg = RiskConfig(max_daily_loss_pct=Decimal("0.05"))

    # 0.5% drawdown <= 1.5% -> normal
    assert classify_drawdown_regime(Decimal("0.005"), cfg) == "normal"

    # 2.0% drawdown <= 3.0% -> caution
    assert classify_drawdown_regime(Decimal("0.02"), cfg) == "caution"

    # 4.0% drawdown <= 4.5% -> restricted
    assert classify_drawdown_regime(Decimal("0.04"), cfg) == "restricted"

    # 4.8% drawdown < 5.0% -> blocked
    assert classify_drawdown_regime(Decimal("0.048"), cfg) == "blocked"

    # 5.5% drawdown >= 5.0% -> kill_switch_required
    assert classify_drawdown_regime(Decimal("0.055"), cfg) == "kill_switch_required"


def test_step_down_controls():
    StepDownControls.reset()
    assert StepDownControls.get_risk_multiplier("normal") == Decimal("1.0")
    assert StepDownControls.get_risk_multiplier("caution") == Decimal("0.75")
    assert StepDownControls.get_risk_multiplier("restricted") == Decimal("0.50")
    assert StepDownControls.get_risk_multiplier("blocked") == Decimal("0.0")
