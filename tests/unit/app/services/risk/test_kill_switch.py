"""Unit tests for emergency kill switches and trigger governance.

Verifies status checks, persistence, auto-triggering on breaches, and
gated resume authorizations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    KillSwitchStateEnum,
    LimitResult,
    ProposedTrade,
    RiskAssessmentRequest,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)
from app.services.risk.kill_switch import (
    KillSwitchManager,
    get_kill_switch_manager,
)
from app.utils.errors import ValidationError
from app.utils.event_bus import InMemoryEventBus


@pytest.fixture
def temp_persistence_path(tmp_path: Any) -> Any:
    """Fixture to generate a temporary file path for state persistence."""
    return tmp_path / "kill_switch_state.json"


@pytest.fixture
def manager(temp_persistence_path: Any) -> KillSwitchManager:
    """Fixture to initialize a fresh KillSwitchManager."""
    return KillSwitchManager(persistence_path=temp_persistence_path)


@pytest.fixture
def base_request() -> RiskAssessmentRequest:
    """Fixture for a baseline RiskAssessmentRequest."""
    from app.services.risk import PortfolioState
    from app.services.risk.config import load_risk_config

    portfolio = PortfolioState(
        account_id="acc-123",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[],
    )

    trade = ProposedTrade(
        strategy_id="strat1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
    )

    return RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=load_risk_config("default"),
        calendar_evidence=[],
        market_context={
            "kill_switch_active": False,
            "freshness": datetime.now(UTC),
            "daily_loss_pct": 0.0,
            "mode": "paper",
        },
    )


def test_initial_state_inactive(manager: KillSwitchManager) -> None:
    """Verify that all initial states are inactive."""
    assert not manager.is_blocked("global", "*")
    assert not manager.is_blocked("portfolio", "*")
    assert not manager.is_blocked("strategy", "strat1")
    assert not manager.is_blocked("symbol", "EURUSD")


def test_trigger_global(manager: KillSwitchManager) -> None:
    """Verify triggering global halts blocks everything."""
    manager.trigger("global", "*", "Emergency operator halt")
    assert manager.is_blocked("global", "*")
    assert manager.is_blocked("strategy", "strat1")
    assert manager.is_blocked("symbol", "EURUSD")


def test_trigger_portfolio(manager: KillSwitchManager) -> None:
    """Verify triggering portfolio halts blocks everything except global."""
    manager.trigger("portfolio", "*", "Portfolio reconciliation error")
    assert not manager.is_blocked("global", "*")  # global itself is not active
    assert manager.is_blocked("strategy", "strat1")
    assert manager.is_blocked("symbol", "EURUSD")


def test_trigger_strategy(manager: KillSwitchManager) -> None:
    """Verify triggering a strategy halt only blocks that strategy."""
    manager.trigger("strategy", "strat1", "Strategy drawdown breach")
    assert manager.is_blocked("strategy", "strat1")
    assert not manager.is_blocked("strategy", "strat2")
    assert not manager.is_blocked("symbol", "EURUSD")


def test_trigger_symbol_and_currency(manager: KillSwitchManager) -> None:
    """Verify symbol and currency leg halts block appropriately."""
    # 1. Symbol halt
    manager.trigger("symbol", "EURUSD", "Extreme spread widening")
    assert manager.is_blocked("symbol", "EURUSD")
    assert not manager.is_blocked("symbol", "GBPUSD")

    # 2. Reset symbol, trigger currency leg
    manager.resume("symbol", "EURUSD", operator_role="admin")
    assert not manager.is_blocked("symbol", "EURUSD")

    # Halt base currency leg (EUR)
    manager.trigger("currency", "EUR", "EUR liquidity blackout")
    assert manager.is_blocked("currency", "EUR")
    # EURUSD has EUR leg -> blocked
    assert manager.is_blocked("symbol", "EURUSD")
    # GBPUSD does not have EUR leg -> not blocked
    assert not manager.is_blocked("symbol", "GBPUSD")


def test_persistence_save_load(temp_persistence_path: Any) -> None:
    """Verify states are serialized and restored successfully from disk."""
    m1 = KillSwitchManager(persistence_path=temp_persistence_path)
    m1.trigger("strategy", "strat_x", "Custom halt")

    # Initialize a new manager using same path
    m2 = KillSwitchManager(persistence_path=temp_persistence_path)
    assert m2.is_blocked("strategy", "strat_x")


def test_persistence_corruption_fail_closed(temp_persistence_path: Any) -> None:
    """Verify corrupt persistence data fails closed (blocks everything)."""
    # Write invalid JSON to file
    temp_persistence_path.parent.mkdir(parents=True, exist_ok=True)
    temp_persistence_path.write_text("invalid_json_corrupted", encoding="utf-8")

    m = KillSwitchManager(persistence_path=temp_persistence_path)
    # Fail closed should lock global switch
    assert m.is_blocked("global", "*", is_live=True)
    assert m.states["global"]["state"] == "locked"


def test_governed_resume_validation(manager: KillSwitchManager) -> None:
    """Verify resume deactivation requires tokens or admin/compliance roles."""
    manager.trigger("strategy", "strat1", "Daily limit breach")
    assert manager.is_blocked("strategy", "strat1")

    # A. Resume without token or role raises ValidationError
    with pytest.raises(ValidationError) as exc:
        manager.resume("strategy", "strat1")
    assert exc.value.code == "APPROVAL_REQUIRED"

    # B. Resume with admin/compliance role succeeds
    manager.resume("strategy", "strat1", operator_role="admin")
    assert not manager.is_blocked("strategy", "strat1")

    # C. Trigger again, resume with token succeeds
    manager.trigger("strategy", "strat1", "Daily limit breach")
    manager.resume("strategy", "strat1", approval_token="token_123")
    assert not manager.is_blocked("strategy", "strat1")


def test_locked_state_resume(manager: KillSwitchManager) -> None:
    """Verify locked states cannot be resumed via token and require admin/compliance."""
    with manager._lock:
        manager.states["global"] = {
            "state": KillSwitchStateEnum.LOCKED,
            "reason": "Audit chain error",
            "triggered_at": datetime.now(UTC).isoformat(),
            "triggered_by": "system",
        }

    # Token alone cannot resume locked switches
    with pytest.raises(ValidationError) as exc:
        manager.resume("global", "*", approval_token="token_123")
    assert exc.value.code == "PERMISSION_DENIED"

    # Admin/compliance role is required
    manager.resume("global", "*", operator_role="compliance")
    assert not manager.is_blocked("global", "*")


def test_evaluate_triggers_manual_and_audit(
    manager: KillSwitchManager, base_request: RiskAssessmentRequest
) -> None:
    """Verify auto-triggers parse manual halt and audit chain failures."""
    # 1. Manual operator halt
    base_request.market_context = {
        "manual_operator_halt": True,
        "operator_id": "haru_user",
    }
    triggered = manager.evaluate_triggers(base_request, [])
    assert "global" in triggered
    assert manager.is_blocked("global", "*")
    assert manager.states["global"]["triggered_by"] == "haru_user"

    # Reset
    manager.resume("global", "*", operator_role="admin")

    # 2. Audit chain failure (locks global switch)
    base_request.market_context = {"audit_chain_verification_failed": True}
    triggered = manager.evaluate_triggers(base_request, [])
    assert "global" in triggered
    assert manager.states["global"]["state"] == KillSwitchStateEnum.LOCKED


def test_evaluate_triggers_reconciliation_and_broker(
    manager: KillSwitchManager, base_request: RiskAssessmentRequest
) -> None:
    """Verify auto-triggers parse reconciliation issues and broker disconnection."""
    # 1. Reconciliation failure
    base_request.market_context = {"portfolio_unreconciled": True}
    triggered = manager.evaluate_triggers(base_request, [])
    assert "portfolio" in triggered
    assert manager.is_blocked("portfolio", "*")

    # Reset
    manager.resume("portfolio", "*", operator_role="admin")

    # 2. Broker disconnected in live execution mode
    base_request.market_context = {"provider_status": "disconnected"}
    triggered = manager.evaluate_triggers(base_request, [], is_live=True)
    assert "global" in triggered
    assert manager.is_blocked("global", "*")


def test_evaluate_triggers_limit_breaches(
    manager: KillSwitchManager, base_request: RiskAssessmentRequest
) -> None:
    """Verify triggers are pulled automatically on specific limit breaches."""
    # A. Daily loss breach -> global switch
    daily_loss_breach = LimitResult(
        limit_name="daily_loss_limit",
        status=RiskDecisionStatus.REJECT,
        reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
        message="Daily loss threshold exceeded",
        severity=RiskSeverity.HARD_BREACH,
        breached=True,
    )
    triggered = manager.evaluate_triggers(base_request, [daily_loss_breach])
    assert "global" in triggered
    assert manager.is_blocked("global", "*")

    manager.resume("global", "*", operator_role="admin")

    # B. Drawdown breach -> global switch
    drawdown_breach = LimitResult(
        limit_name="drawdown_limit",
        status=RiskDecisionStatus.REJECT,
        reason_code=RiskReasonCode.DRAWDOWN_BREACH,
        message="Total drawdown threshold exceeded",
        severity=RiskSeverity.CRITICAL_BREACH,
        breached=True,
    )
    triggered = manager.evaluate_triggers(base_request, [drawdown_breach])
    assert "global" in triggered

    manager.resume("global", "*", operator_role="admin")

    # C. Extreme spread -> symbol-specific switch
    spread_breach = LimitResult(
        limit_name="spread_limit",
        status=RiskDecisionStatus.REJECT,
        reason_code=RiskReasonCode.SPREAD_BREACH,
        message="Spread exceeded extreme limit",
        severity=RiskSeverity.CRITICAL_BREACH,
        breached=True,
    )
    triggered = manager.evaluate_triggers(base_request, [spread_breach])
    assert "symbol" in triggered
    assert manager.is_blocked("symbol", "EURUSD")
    assert not manager.is_blocked("symbol", "GBPUSD")


def test_evaluate_triggers_margin_emergency(
    manager: KillSwitchManager, base_request: RiskAssessmentRequest
) -> None:
    """Verify margin emergency triggers portfolio-level switch."""
    margin_breach = LimitResult(
        limit_name="margin_limit",
        status=RiskDecisionStatus.BLOCK,
        reason_code=RiskReasonCode.MARGIN_BREACH,
        message="Projected margin exceeds emergency limit",
        severity=RiskSeverity.CRITICAL_BREACH,
        breached=True,
    )
    triggered = manager.evaluate_triggers(base_request, [margin_breach])
    assert "portfolio" in triggered
    assert manager.is_blocked("portfolio", "*")


def test_event_dispatching(manager: KillSwitchManager) -> None:
    """Verify that triggering and resuming switches dispatches events to event bus."""
    bus = InMemoryEventBus()
    events_triggered: list[dict[str, Any]] = []
    events_resumed: list[dict[str, Any]] = []

    bus.subscribe("risk.kill_switch.triggered", events_triggered.append)
    bus.subscribe("risk.kill_switch.resumed", events_resumed.append)

    # Trigger switch
    manager.trigger("strategy", "strat1", "Test trigger", event_bus=bus)
    assert len(events_triggered) == 1
    assert events_triggered[0]["payload"]["scope"] == "strategy"
    assert events_triggered[0]["payload"]["target"] == "strat1"

    # Resume switch
    manager.resume("strategy", "strat1", operator_role="admin", event_bus=bus)
    assert len(events_resumed) == 1
    assert events_resumed[0]["payload"]["scope"] == "strategy"
    assert events_resumed[0]["payload"]["target"] == "strat1"


def test_singleton_get_kill_switch_manager(temp_persistence_path: Any) -> None:
    """Verify the global singleton retrieval works correctly."""
    m1 = get_kill_switch_manager(persistence_path=temp_persistence_path)
    m2 = get_kill_switch_manager()
    assert m1 is m2
