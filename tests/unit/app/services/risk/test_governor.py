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
    assert decision.status == RiskDecisionStatus.HALT_STRATEGY
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


def test_governor_trade_review_market_regime_reject():
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
            "tick_availability": False,  # Triggers illiquid regime
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    req.request_id = "req_regime_reject"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.REJECT
    assert decision.rule_key == "market_regime_gate"
    assert "market_regime_gate" in decision.composite_breach_flags
    assert decision.details is not None
    assert "regime_result" in decision.details
    assert decision.details["regime_result"]["regime"] == "illiquid"


def test_governor_trade_review_market_regime_approve():
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
            "tick_frequency": 30,
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    req.request_id = "req_regime_approve"

    decision = gov.review_trade_risk(req)
    # The regime is normal/approved, and other limits should pass
    assert decision.status == RiskDecisionStatus.APPROVE, (
        f"Failed: status={decision.status}, reason={decision.reason}, "
        f"rule_key={decision.rule_key}, "
        f"composite_breach_flags={decision.composite_breach_flags}"
    )
    assert "regime_result" in req.market_context
    assert req.market_context["regime_result"]["regime"] == "normal"


def test_governor_execution_feasibility_gate():
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
        volume=Decimal("150.0"),  # Exceeds max volume
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
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
            "EURUSD_stop_level": 5.0,
            "EURUSD_freeze_level": 2.0,
            "EURUSD_volume_min": Decimal("0.01"),
            "EURUSD_volume_max": Decimal("100.0"),  # trade volume is 150.0
            "EURUSD_volume_step": Decimal("0.01"),
            "EURUSD_pip_size": Decimal("0.0001"),
            "EURUSD_spread": 0.0002,
            "EURUSD_volatility": Decimal("0.0001"),
            "contract_size": Decimal("1.0"),
            "max_stress_ratio": 2.0,
        },
    )
    req.request_id = "req_execution_feasibility"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.REDUCE_SIZE
    assert decision.calculated_volume == Decimal("100.0")
    assert "execution_feasibility_gate" in decision.composite_breach_flags


def test_governor_dispatch_checks():
    from app.services.risk.governor import run_risk_governor_checks

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
    req.request_id = "req_dispatch_trade"

    # Test run_risk_governor_checks top-level helper
    decision = run_risk_governor_checks(req)
    assert decision.status == RiskDecisionStatus.APPROVE
    assert decision.calculated_volume == Decimal("0.1")


def test_governor_lifecycle_review_helpers():
    from app.services.risk.governor import (
        review_live_readiness,
        review_mode_promotion,
    )

    # Test review_live_readiness
    res_ready = review_live_readiness(
        strategy_id="strat_1",
        proposed_stage="simulation",
        market_context={"backtest_active": True},
        config=RiskConfig(profile_name="default"),
    )
    assert res_ready.strategy_id == "strat_1"

    # Test review_mode_promotion
    res_promote = review_mode_promotion(
        strategy_id="strat_1",
        current_stage="research",
        target_stage="simulation",
        evidence={"trade_count": 100},
        config=RiskConfig(profile_name="default"),
    )
    assert res_promote.strategy_id == "strat_1"


def test_governor_needs_more_evidence_outcome():
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
            # Omit freshness -> triggers NEEDS_MORE_EVIDENCE
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    req.request_id = "req_needs_more_evidence"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.NEEDS_MORE_EVIDENCE
    assert "stale_evidence" in decision.composite_breach_flags


def test_governor_needs_approval_outcome():
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
            "spread": Decimal("0.01"),
            "max_spread": Decimal("0.005"),
            "is_overrideable": True,
        },
    )
    req.request_id = "req_needs_approval"

    # Should return NEEDS_APPROVAL due to warning override configuration
    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.NEEDS_APPROVAL
    assert "Requires governed override" in decision.reason


def test_governor_halt_outcomes():
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    # 1. Global Kill Switch => HALT_ALL
    gov.kill_switch_manager.trigger("global", "*", "Emergency halt", "admin")

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
    req.request_id = "req_halt_all"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.HALT_ALL
    assert "Immediate shutdown" in decision.reason

    # Deactivate global kill switch
    gov.kill_switch_manager.resume("global", "*", "Resume", "admin")

    # 2. Strategy Kill Switch => HALT_STRATEGY
    gov.kill_switch_manager.trigger("strategy", "strat_1", "Halt strategy", "admin")
    req.request_id = "req_halt_strategy"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.HALT_STRATEGY
    assert "Strategy shutdown" in decision.reason


def test_governor_namespace_exports():
    import app.services.risk.governor as gov_mod

    expected_classes = [
        "RiskGovernor",
        "RiskGovernorDecision",
        "RiskDecisionPackage",
        "RiskAssessmentRequest",
        "ProposedTrade",
        "RiskPolicyEngine",
        "RegimeRiskEngine",
        "LimitEngine",
        "VolatilitySizingEngine",
        "CurrencyExposureEngine",
        "CorrelationEngine",
        "PortfolioVaREngine",
        "ExpectedShortfallEngine",
        "StressTestingEngine",
        "MarginRiskEngine",
        "DrawdownGovernor",
        "ExecutionRiskGate",
        "RiskAllocator",
    ]

    expected_funcs = [
        "run_risk_governor_checks",
        "run_portfolio_risk_governor",
        "review_trade_risk",
    ]

    for cls_name in expected_classes:
        assert hasattr(gov_mod, cls_name), (
            f"Class {cls_name} not found in governor.py namespace"
        )

    for func_name in expected_funcs:
        assert hasattr(gov_mod, func_name), (
            f"Function {func_name} not found in governor.py namespace"
        )


def test_governor_constructor_with_custom_kill_switch() -> None:
    """Test constructor with explicitly injected kill switch manager."""
    from pathlib import Path

    from app.services.risk.kill_switch import KillSwitchManager
    from app.services.risk.storage import InMemoryRiskStateStore

    store = InMemoryRiskStateStore()
    ks_mgr = KillSwitchManager(persistence_path=Path("dummy_ks.json"))
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
        kill_switch_manager=ks_mgr,
    )
    assert gov.kill_switch_manager is ks_mgr


def test_governor_invalid_request_types() -> None:
    """Test governor input validations raising ValidationError."""
    from app.utils.errors import ValidationError

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

    # 1. Invalid request type
    with pytest.raises(ValidationError, match="Invalid request type"):
        gov.review_trade_risk("invalid_request")  # type: ignore[arg-type]

    # 2. proposed_action is not ProposedTrade
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
        proposed_action=ProposedAllocation(allocations={}, as_of=datetime.now(UTC)),
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
    )
    with pytest.raises(
        ValidationError, match="proposed_action must be a ProposedTrade"
    ):
        gov.review_trade_risk(req)


def test_governor_request_id_collision() -> None:
    """Test governor raising DataError on request ID collision."""
    from app.utils.errors import DataError

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

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
    trade = ProposedTrade(
        strategy_id="strat_1", symbol="EURUSD", side="buy", volume=Decimal("0.1")
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        market_context={"mode": "paper"},
    )
    req.request_id = "req_collision"

    # Save first decision
    gov.review_trade_risk(req)

    # Re-evaluate with different trade volume -> collision
    trade2 = ProposedTrade(
        strategy_id="strat_1", symbol="EURUSD", side="buy", volume=Decimal("0.2")
    )
    req2 = RiskAssessmentRequest(
        proposed_action=trade2,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        market_context={"mode": "paper"},
    )
    req2.request_id = "req_collision"

    with pytest.raises(DataError, match="collision: different materials"):
        gov.review_trade_risk(req2)


def test_governor_policy_reject_early_exit() -> None:
    """Test policy resolution REJECT early exit."""
    from app.services.risk.models import PolicyRule, PolicyScope

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

    # Insert a policy rule that overrides daily loss above limit -> rejects
    rule = PolicyRule(
        rule_id="rule_reject",
        scope=PolicyScope(),
        overrides={
            "max_daily_loss_pct": Decimal("0.50")
        },  # exceeds hard ceiling of 0.20
    )
    store.save_rule(rule)

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
    trade = ProposedTrade(
        strategy_id="strat_1", symbol="EURUSD", side="buy", volume=Decimal("0.1")
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        market_context={"mode": "paper"},
    )
    req.request_id = "req_policy_reject"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.REJECT
    assert decision.rule_key == "policy_resolution"


def test_governor_live_mode_audit_chain_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test live mode blocks execution if audit chain is tampered."""
    from app.services.risk.config import load_risk_config

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

    # Mock verify_risk_audit_chain to return False
    monkeypatch.setattr(
        "app.services.risk.governor.verify_risk_audit_chain", lambda _: False
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
    trade = ProposedTrade(
        strategy_id="strat_1", symbol="EURUSD", side="buy", volume=Decimal("0.1")
    )

    # Load live config so allow_live_execution is True
    live_cfg = load_risk_config("live_conservative")
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=live_cfg,
        market_context={"mode": "full_live", "environment": "production"},
    )
    req.request_id = "req_live_audit_fail"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.BLOCK
    assert decision.rule_key == "audit_chain_verification_failed"


def test_module_level_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that module-level convenience function gates run correctly."""
    from app.services.risk.governor import (
        review_allocation_proposal,
        review_strategy_admission,
        review_trade_risk,
        run_portfolio_risk_governor,
        run_risk_governor_checks,
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

    # 1. review_trade_risk helper
    trade = ProposedTrade(
        strategy_id="strat_1", symbol="EURUSD", side="buy", volume=Decimal("0.1")
    )
    req_trade = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    res_trade = review_trade_risk(req_trade)
    assert res_trade.status == RiskDecisionStatus.APPROVE

    # 2. review_allocation_proposal helper
    proposal = ProposedAllocation(
        allocations={"strat_1": Decimal("3500.00")},
        as_of=datetime.now(UTC),
    )
    req_alloc = RiskAssessmentRequest(
        proposed_action=proposal,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
    )
    req_alloc.market_context["strategy_evidence"] = {
        "strat_1": {"trade_count": 150, "sharpe_ratio": Decimal("1.8")}
    }
    res_alloc = review_allocation_proposal(req_alloc)
    assert res_alloc.status == RiskDecisionStatus.APPROVE

    # 3. review_strategy_admission helper
    admission = StrategyAdmissionRequest(
        strategy_id="strat_1",
        evidence={"trade_count": 120, "sharpe_ratio": 1.6, "max_drawdown": 0.12},
    )
    req_admit = RiskAssessmentRequest(
        proposed_action=admission,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
    )
    res_admit = review_strategy_admission(req_admit)
    assert res_admit.status == RiskDecisionStatus.APPROVE

    # 4. run_portfolio_risk_governor helper
    req_port = RiskAssessmentRequest(
        proposed_action=ProposedAllocation(
            allocations={}, as_of=datetime.now(UTC)
        ),  # portfolio run
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    res_port = run_portfolio_risk_governor(req_port)
    assert res_port.status == RiskDecisionStatus.APPROVE

    # 5. run_risk_governor_checks helper routing
    res_route = run_risk_governor_checks(req_trade)
    assert res_route.status == RiskDecisionStatus.APPROVE


def test_governor_trade_review_with_market_data() -> None:
    """Test governor trade review with market data for correlation/VaR."""
    from app.services.risk.storage import InMemoryRiskStateStore

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

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
        positions=[],
    )

    # 5 bars for EURUSD and GBPUSD
    m_data = {
        "EURUSD": [
            {"time": "2026-06-19T12:00:00Z", "open": 1.10, "close": 1.11},
            {"time": "2026-06-19T12:01:00Z", "open": 1.11, "close": 1.10},
            {"time": "2026-06-19T12:02:00Z", "open": 1.10, "close": 1.09},
            {"time": "2026-06-19T12:03:00Z", "open": 1.09, "close": 1.10},
            {"time": "2026-06-19T12:04:00Z", "open": 1.10, "close": 1.11},
        ],
        "GBPUSD": [
            {"time": "2026-06-19T12:00:00Z", "open": 1.25, "close": 1.26},
            {"time": "2026-06-19T12:01:00Z", "open": 1.26, "close": 1.25},
            {"time": "2026-06-19T12:02:00Z", "open": 1.25, "close": 1.24},
            {"time": "2026-06-19T12:03:00Z", "open": 1.24, "close": 1.25},
            {"time": "2026-06-19T12:04:00Z", "open": 1.25, "close": 1.26},
        ],
    }

    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
            "market_data": m_data,
            "correlation_lookback": 5,
            "timeframe": "M1",
            "min_correlation_samples": 2,
            "var_lookback": 5,
            "min_samples": 2,
            "EURUSD_price": 1.10,
            "GBPUSD_price": 1.25,
            "EURUSD_contract_size": 100000.0,
            "GBPUSD_contract_size": 100000.0,
        },
    )
    req.request_id = "req_with_m_data"

    decision = gov.review_trade_risk(req)
    assert decision.status == RiskDecisionStatus.APPROVE


def test_governor_uncovered_paths(monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: PLR0915
    """Test various edge cases, tokens, exceptions, and sizing."""
    from datetime import UTC, datetime, timedelta
    from decimal import Decimal

    from app.services.risk.models import RiskApprovalToken, RiskDecisionStatus

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

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
        positions=[],
    )

    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )

    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )

    # Mocking validation/permission checks for token review
    monkeypatch.setattr(
        "app.services.risk.audit.validate_risk_approval_token",
        lambda *_, **__: True,
    )
    monkeypatch.setattr(
        "app.services.risk.policy.check_policy_permission", lambda *_, **__: True
    )

    # 1a. token as RiskApprovalToken object
    tok = RiskApprovalToken(
        token_id="tok_123",
        request_id="req_1",
        workflow_id="wf_1",
        approved_action="override",
        expiry_time=datetime.now(UTC) + timedelta(hours=1),
        config_hash="abc",
        decision_hash="xyz",
        scope={},
        signature="sig1",
        nonce="n1",
        approver="owner",
    )
    req.request_id = None
    res = gov.review_trade_risk(req, approval_token=tok)  # type: ignore[arg-type]
    assert res.status == RiskDecisionStatus.APPROVE

    # 1b. token as dict
    tok_dict = tok.model_dump()
    tok_dict["expiry_time"] = tok_dict["expiry_time"].isoformat()
    req.request_id = None
    res = gov.review_trade_risk(req, approval_token=tok_dict)  # type: ignore[arg-type]
    assert res.status == RiskDecisionStatus.APPROVE

    # 1c. token as json string
    import json

    tok_json = json.dumps(tok_dict)
    req.request_id = None
    res = gov.review_trade_risk(req, approval_token=tok_json)
    assert res.status == RiskDecisionStatus.APPROVE

    # 1d. token signature fails validation (validate_risk_approval_token returns False)
    monkeypatch.setattr(
        "app.services.risk.audit.validate_risk_approval_token",
        lambda *_, **__: False,
    )
    req.request_id = None
    res = gov.review_trade_risk(req, approval_token=tok)  # type: ignore[arg-type]
    assert res.status == RiskDecisionStatus.APPROVE

    # 1e. check_policy_permission returns False
    monkeypatch.setattr(
        "app.services.risk.audit.validate_risk_approval_token",
        lambda *_, **__: True,
    )
    monkeypatch.setattr(
        "app.services.risk.policy.check_policy_permission",
        lambda *_, **__: False,
    )
    req.request_id = None
    res = gov.review_trade_risk(req, approval_token=tok)  # type: ignore[arg-type]
    assert res.status == RiskDecisionStatus.APPROVE

    # 2. Test Exception fallback paths in review_trade_risk
    # 2a. calculate_currency_exposure raises Exception
    def mock_calc_curr_exp(*args, **kwargs):
        raise ValueError("Simulated currency exposure error")

    monkeypatch.setattr(
        "app.services.risk.exposure.calculate_currency_exposure", mock_calc_curr_exp
    )
    req.request_id = None
    res = gov.review_trade_risk(req)
    assert res.status == RiskDecisionStatus.APPROVE

    # 2b. evaluate_margin_governance raises Exception
    def mock_eval_margin(*args, **kwargs):
        raise ValueError("Simulated margin error")

    monkeypatch.setattr(
        "app.services.risk.margin.evaluate_margin_governance", mock_eval_margin
    )
    req.request_id = None
    res = gov.review_trade_risk(req)
    assert res.status == RiskDecisionStatus.APPROVE

    # 2c. evaluate_stress_scenarios raises Exception
    def mock_eval_stress(*args, **kwargs):
        raise ValueError("Simulated stress error")

    monkeypatch.setattr(
        "app.services.risk.governor.build_default_scenario_registry", mock_eval_stress
    )
    req.request_id = None
    res = gov.review_trade_risk(req)
    assert res.status == RiskDecisionStatus.APPROVE

    # 3. Sizing calculation error (governor sizing calculation error log path)
    def mock_calc_pos_size(*args, **kwargs):
        raise ValueError("Simulated sizing calculation error")

    monkeypatch.setattr(
        "app.services.risk.governor.calculate_position_size", mock_calc_pos_size
    )
    req.market_context["sizing_request"] = {"method": "fixed_lot", "fixed_volume": 1.0}
    req.request_id = None
    res = gov.review_trade_risk(req)
    assert res.status == RiskDecisionStatus.APPROVE

    # 4. Sizing rejected gate (calculated_vol <= 0)
    from unittest.mock import MagicMock

    mock_sizing_res = MagicMock()
    mock_sizing_res.calculated_volume = Decimal("0.0")
    mock_sizing_res.constraints_applied = ["max_risk_limit"]
    monkeypatch.setattr(
        "app.services.risk.governor.calculate_position_size",
        lambda *_, **__: mock_sizing_res,
    )
    req.request_id = None
    res = gov.review_trade_risk(req)
    assert res.status == RiskDecisionStatus.REJECT
    assert "max_risk_limit" in res.reason

    # 5. run_risk_governor_checks routing for other request types
    # 5a. ProposedAllocation
    alloc_req = RiskAssessmentRequest(
        proposed_action=ProposedAllocation(allocations={}, as_of=datetime.now(UTC)),
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    res = gov.run_risk_governor_checks(alloc_req)
    assert res.status == RiskDecisionStatus.APPROVE

    # 5b. StrategyAdmissionRequest
    admit_req = RiskAssessmentRequest(
        proposed_action=StrategyAdmissionRequest(
            strategy_id="strat_1",
            evidence={"trade_count": 120, "sharpe_ratio": 1.6, "max_drawdown": 0.12},
        ),
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    res = gov.run_risk_governor_checks(admit_req)
    assert res.status == RiskDecisionStatus.APPROVE

    # 6. Correlation cluster exposure reduction branch
    # Reset mocks to sensible defaults
    monkeypatch.setattr(
        "app.services.risk.correlation.calculate_symbol_cluster_exposure",
        lambda *_, **__: Decimal("50.0"),
    )
    monkeypatch.setattr(
        "app.services.risk.correlation._get_symbol_gross_exposure",
        lambda *_, **__: Decimal("100.0"),
    )
    req.market_context["max_correlated_exposure"] = (
        "0.01"  # 0.01 * 10000 = 100 equity limit
    )
    req.proposed_action.price = Decimal("1.10")  # type: ignore[union-attr]
    req.proposed_action.volume = Decimal("0.1")  # type: ignore[union-attr]
    req.market_context.pop("sizing_request", None)
    req.market_context["market_data"] = {
        "EURUSD": [
            {"time": "2026-06-19T12:00:00Z", "open": 1.10, "close": 1.11},
            {"time": "2026-06-19T12:01:00Z", "open": 1.11, "close": 1.10},
        ]
    }
    req.request_id = None
    res = gov.review_trade_risk(req)
    assert req.market_context.get("correlation_cluster_reduction") is not None
