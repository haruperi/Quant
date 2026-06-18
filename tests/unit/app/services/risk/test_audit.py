"""Unit tests for risk governance tokens and audit chain verification."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.risk.audit import (
    create_risk_audit_event,
    create_risk_decision_token,
    revoke_risk_approval_token,
    validate_risk_approval_token,
    verify_risk_audit_chain,
)
from app.services.risk.models import (
    ProposedTrade,
    RiskDecisionPackage,
    RiskDecisionStatus,
)
from app.services.risk.storage import InMemoryRiskStateStore


def test_decision_token_signing_and_validation():
    store = InMemoryRiskStateStore()
    config_hash = "abc123config"
    decision_hash = "xyz789decision"

    token = create_risk_decision_token(
        decision_id="dec_1",
        request_id="req_1",
        workflow_id="wf_1",
        approved_action="execute_trade",
        config_hash=config_hash,
        decision_hash=decision_hash,
        scope={"symbol": "EURUSD", "strategy_id": "strat_1"},
        expiry_seconds=300,
    )
    assert token.token_id.startswith("tok_")
    assert token.signature != ""

    # Validate success path
    is_valid = validate_risk_approval_token(
        token=token,
        expected_scope={"symbol": "EURUSD", "strategy_id": "strat_1"},
        active_config_hash=config_hash,
        active_policy_hash="",
        state_store=store,
    )
    assert is_valid is True

    # Validate config mismatch fails
    assert not validate_risk_approval_token(
        token=token,
        expected_scope={"symbol": "EURUSD", "strategy_id": "strat_1"},
        active_config_hash="mismatched_config_hash",
        active_policy_hash="",
        state_store=store,
    )

    # Validate scope mismatch fails
    assert not validate_risk_approval_token(
        token=token,
        expected_scope={"symbol": "GBPUSD", "strategy_id": "strat_1"},
        active_config_hash=config_hash,
        active_policy_hash="",
        state_store=store,
    )

    # Validate revocation fails
    revoke_risk_approval_token(token.token_id, store)
    assert not validate_risk_approval_token(
        token=token,
        expected_scope={"symbol": "EURUSD", "strategy_id": "strat_1"},
        active_config_hash=config_hash,
        active_policy_hash="",
        state_store=store,
    )


def test_token_expiry_validation():
    store = InMemoryRiskStateStore()
    config_hash = "abc123config"
    decision_hash = "xyz789decision"

    # Create expired token (expiry_seconds < 0)
    token = create_risk_decision_token(
        decision_id="dec_1",
        request_id="req_1",
        workflow_id="wf_1",
        approved_action="execute_trade",
        config_hash=config_hash,
        decision_hash=decision_hash,
        scope={"symbol": "EURUSD"},
        expiry_seconds=-10,
    )
    assert not validate_risk_approval_token(
        token=token,
        expected_scope={"symbol": "EURUSD"},
        active_config_hash=config_hash,
        active_policy_hash="",
        state_store=store,
    )


def test_audit_event_chaining_and_tamper_detection():
    store = InMemoryRiskStateStore()
    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    decision1 = RiskDecisionPackage(
        decision_id="dec_1",
        request_id="req_1",
        workflow_id="wf_1",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limits_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="cfg_hash_1",
        reason="Limits cleared",
    )

    # Genesis event block
    event1 = create_risk_audit_event(decision1, trade, store)
    assert event1.previous_hash == "0" * 64
    assert event1.hash != ""

    # Check database chain valid
    assert verify_risk_audit_chain(store) is True

    # Second block
    decision2 = RiskDecisionPackage(
        decision_id="dec_2",
        request_id="req_2",
        workflow_id="wf_1",
        status=RiskDecisionStatus.REJECT,
        rule_key="drawdown_limit",
        snapshot_as_of=datetime.now(UTC),
        config_hash="cfg_hash_1",
        reason="Drawdown limit breached",
    )
    event2 = create_risk_audit_event(decision2, trade, store)
    assert event2.previous_hash == event1.hash
    assert verify_risk_audit_chain(store) is True

    # Simulate Tampering in block 1
    event1.details["proposed_action"]["volume"] = 99.0
    # Re-verify chain should catch it
    assert verify_risk_audit_chain(store) is False
