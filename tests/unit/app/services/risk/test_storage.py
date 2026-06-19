"""Unit tests for risk governance storage ports and InMemoryRiskStateStore."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.governor import RiskGovernor
from app.services.risk.models import (
    DrawdownState,
    KillSwitchReason,
    KillSwitchStateEnum,
    PolicyRule,
    PolicyScope,
    PortfolioState,
    ProposedTrade,
    RiskAssessmentRequest,
    RiskConfig,
    RiskDecisionPackage,
    RiskDecisionStatus,
)
from app.services.risk.storage import (
    InMemoryRiskStateStore,
    compute_decision_material_hash,
)
from app.utils.errors import DataError, ValidationError


def test_in_memory_drawdown_state():
    store = InMemoryRiskStateStore()
    assert store.get_drawdown_state("strat_1") is None

    state = DrawdownState(
        current_drawdown=Decimal("0.05"),
        soft_limit=Decimal("0.06"),
        hard_limit=Decimal("0.09"),
        multiplier=Decimal("1.0"),
    )
    store.save_drawdown_state(state, "strat_1")
    retrieved = store.get_drawdown_state("strat_1")
    assert retrieved is not None
    assert retrieved.current_drawdown == Decimal("0.05")

    # Verify invalid object raises ValidationError
    with pytest.raises(ValidationError):
        store.save_drawdown_state("invalid_state", "strat_1")


def test_in_memory_kill_switch_state():
    store = InMemoryRiskStateStore()
    state, reason, _, _ = store.get_kill_switch_state("global", "*")
    assert state == KillSwitchStateEnum.INACTIVE

    now = datetime.now(UTC)
    store.save_kill_switch_state(
        scope="symbol",
        target="EURUSD",
        state=KillSwitchStateEnum.ACTIVE,
        reason=KillSwitchReason.EXTREME_SPREAD,
        triggered_at=now,
        triggered_by="test",
    )
    state, reason, t, by = store.get_kill_switch_state("symbol", "EURUSD")
    assert state == KillSwitchStateEnum.ACTIVE
    assert reason == KillSwitchReason.EXTREME_SPREAD
    assert t == now
    assert by == "test"

    with pytest.raises(ValidationError):
        store.save_kill_switch_state(
            "invalid_scope", "EURUSD", KillSwitchStateEnum.ACTIVE
        )


def test_in_memory_token_revocation():
    store = InMemoryRiskStateStore()
    assert not store.is_token_revoked("tok_123")

    store.revoke_token("tok_123")
    assert store.is_token_revoked("tok_123")

    with pytest.raises(ValidationError):
        store.revoke_token("")


def test_in_memory_policy_rules():
    store = InMemoryRiskStateStore()
    assert len(store.get_rules()) == 0

    rule = PolicyRule(
        rule_id="rule_1",
        scope=PolicyScope(symbol="EURUSD"),
        overrides={"max_effective_leverage": 20.0},
    )
    store.save_rule(rule)
    rules = store.get_rules()
    assert len(rules) == 1
    assert rules[0].rule_id == "rule_1"

    with pytest.raises(ValidationError):
        store.save_rule("invalid_rule")


def test_in_memory_decisions_idempotency():
    store = InMemoryRiskStateStore()
    decision = RiskDecisionPackage(
        decision_id="dec_123",
        request_id="req_123",
        workflow_id="wf_123",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limit_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="cfg_hash",
        reason="Limits cleared",
    )
    store.save_decision(decision)

    # Retrieval
    assert store.get_decision("dec_123") == decision
    assert store.get_decision_by_request_id("req_123") == decision

    # Re-save same decision (idempotency check success)
    store.save_decision(decision)

    # Save a decision with duplicate request_id but different decision_id
    # -> raise DataError
    duplicate_request_decision = RiskDecisionPackage(
        decision_id="dec_456",
        request_id="req_123",
        workflow_id="wf_123",
        status=RiskDecisionStatus.REJECT,
        rule_key="limit_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="cfg_hash",
        reason="Breached limit",
    )
    with pytest.raises(DataError):
        store.save_decision(duplicate_request_decision)


def test_in_memory_persistence_failure_behavior():
    store = InMemoryRiskStateStore()

    state = DrawdownState(
        current_drawdown=Decimal("0.05"),
        soft_limit=Decimal("0.06"),
        hard_limit=Decimal("0.09"),
        multiplier=Decimal("1.0"),
    )
    rule = PolicyRule(
        rule_id="rule_1",
        scope=PolicyScope(symbol="EURUSD"),
        overrides={"max_effective_leverage": 20.0},
    )
    decision = RiskDecisionPackage(
        decision_id="dec_123",
        request_id="req_123",
        workflow_id="wf_123",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limit_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="cfg_hash",
        reason="Limits cleared",
    )

    # Enable simulated failure
    store.set_simulate_failure(True)

    with pytest.raises(DataError):
        store.get_drawdown_state("strat_1")
    with pytest.raises(DataError):
        store.save_drawdown_state(state, "strat_1")
    with pytest.raises(DataError):
        store.get_kill_switch_state("global", "*")
    with pytest.raises(DataError):
        store.save_kill_switch_state("global", "*", KillSwitchStateEnum.ACTIVE)
    with pytest.raises(DataError):
        store.is_token_revoked("tok_123")
    with pytest.raises(DataError):
        store.revoke_token("tok_123")
    with pytest.raises(DataError):
        store.get_rules()
    with pytest.raises(DataError):
        store.save_rule(rule)
    with pytest.raises(DataError):
        store.get_decision("dec_123")
    with pytest.raises(DataError):
        store.save_decision(decision)
    with pytest.raises(DataError):
        store.get_decision_by_request_id("req_123")
    with pytest.raises(DataError):
        store.get_decision_by_key("req_123", "wf_123", "sig_123", "mat_hash")


def test_in_memory_schema_version_mismatch():
    store = InMemoryRiskStateStore()

    bad_state = DrawdownState(
        schema_version="2.0.0",
        current_drawdown=Decimal("0.05"),
        soft_limit=Decimal("0.06"),
        hard_limit=Decimal("0.09"),
        multiplier=Decimal("1.0"),
    )
    with pytest.raises(ValidationError):
        store.save_drawdown_state(bad_state, "strat_1")

    bad_decision = RiskDecisionPackage(
        schema_version="2.0.0",
        decision_id="dec_123",
        request_id="req_123",
        workflow_id="wf_123",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limit_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="cfg_hash",
        reason="Limits cleared",
    )
    with pytest.raises(ValidationError):
        store.save_decision(bad_decision)


def test_in_memory_decisions_idempotency_compound_key():
    store = InMemoryRiskStateStore()
    decision = RiskDecisionPackage(
        decision_id="dec_123",
        request_id="req_123",
        workflow_id="wf_123",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limit_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="cfg_hash",
        reason="Limits cleared",
        details={"signal_id": "sig_123"},
    )

    store.save_decision(decision)

    # Compute key hash
    mat_hash = compute_decision_material_hash(decision)
    retrieved = store.get_decision_by_key("req_123", "wf_123", "sig_123", mat_hash)
    assert retrieved == decision

    # Re-save identical compound key and identical decision_id must succeed (idempotent)
    store.save_decision(decision)

    # Save a decision with same compound key but different decision_id
    # -> raise DataError
    duplicate_compound_decision = RiskDecisionPackage(
        decision_id="dec_999",
        request_id="req_123",
        workflow_id="wf_123",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limit_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="cfg_hash",
        reason="Limits cleared",
        details={"signal_id": "sig_123"},
    )
    with pytest.raises(DataError):
        store.save_decision(duplicate_compound_decision)

    # Try retrieving by key with invalid parameters
    with pytest.raises(ValidationError):
        store.get_decision_by_key("", "", "", "")


def test_live_fail_closed_behavior():
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
        },
    )

    # Enable simulated persistence failure on store
    store.set_simulate_failure(True)

    # Executing the risk review must raise DataError (fail closed)
    with pytest.raises(DataError):
        gov.review_trade_risk(req)
