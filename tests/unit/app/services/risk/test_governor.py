"""Unit tests for the RiskGovernor orchestrator pipeline."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.governor import RiskGovernor
from app.services.risk.kill_switch import get_kill_switch_manager
from app.services.risk.models import (
    KillSwitchStateEnum,
    PortfolioState,
    ProposedAllocation,
    ProposedTrade,
    RiskAssessmentRequest,
    RiskConfig,
    RiskDecisionStatus,
    StrategyAdmissionRequest,
)
from app.services.risk.storage import InMemoryRiskStateStore


@pytest.fixture(autouse=True)
def clean_kill_switch():
    manager = get_kill_switch_manager()
    with manager._lock:
        manager.states = {
            "global": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "portfolio": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "strategies": {},
            "symbols": {},
            "currencies": {},
        }
        manager.save()
    yield
    with manager._lock:
        manager.states = {
            "global": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "portfolio": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "strategies": {},
            "symbols": {},
            "currencies": {},
        }
        manager.save()


def test_governor_trade_review_success():
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    req.request_id = "req_success"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.APPROVE
    assert decision.calculated_volume == Decimal("0.1")
    assert "decision_token" in decision.details

    # Verify audit event logged
    assert len(store._audit_events) == 1
    assert store._audit_events[0].decision_id == decision.decision_id


def test_governor_trade_review_idempotency():
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={"mode": "paper"},
    )
    req.request_id = "req_dup"

    decision1 = gov.review_trade_risk(req)
    # Re-evaluating same request ID -> returns identical decision cached
    decision2 = gov.review_trade_risk(req)
    assert decision1.decision_id == decision2.decision_id


def test_governor_kill_switch_blocking():
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    # Trigger switch for strategy_1
    gov.kill_switch_manager.trigger("strategy", "strat_1", "Manual halt", "admin")

    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={"mode": "paper"},
    )
    req.request_id = "req_kill_switch"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.BLOCK
    assert decision.rule_key == "kill_switch_state"


def test_governor_allocation_review():
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        strategy_allocations={"strat_1": Decimal("3000.00")},
    )

    # allocation increase from 3000 to 3500 (+16%, below 20% limit)
    proposal = ProposedAllocation(
        allocations={"strat_1": Decimal("3500.00")},
        as_of=datetime.now(UTC),
    )

    req = RiskAssessmentRequest(
        proposed_action=proposal,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
    )
    req.request_id = "req_alloc"

    # With backtest statistics evidence present
    req.market_context["strategy_evidence"] = {
        "strat_1": {"trade_count": 150, "sharpe_ratio": Decimal("1.8")}
    }

    decision = gov.review_allocation_proposal(req)
    assert decision.status == RiskDecisionStatus.APPROVE


def test_governor_strategy_admission():
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    admission = StrategyAdmissionRequest(
        strategy_id="strat_1",
        evidence={
            "trade_count": 120,
            "sharpe_ratio": 1.7,
            "max_drawdown": 0.12,
        },
    )
    req = RiskAssessmentRequest(
        proposed_action=admission,
        portfolio_state=PortfolioState(
            account_id="acc_admit",
            balance=Decimal("1.0"),
            equity=Decimal("1.0"),
            margin_used=Decimal("0.0"),
            free_margin=Decimal("1.0"),
            floating_pnl=Decimal("0.0"),
            realized_pnl=Decimal("0.0"),
            currency="USD",
            as_of=datetime.now(UTC),
        ),
        risk_config=RiskConfig(profile_name="default"),
    )
    req.request_id = "req_admission"

    decision = gov.review_strategy_admission(req)
    assert decision.status == RiskDecisionStatus.APPROVE
