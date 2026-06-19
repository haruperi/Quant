"""Unit tests for risk governance tokens and audit chain verification."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.audit import (
    RiskAuditEventBuilder,
    RiskAuditHashChain,
    RiskAuditStore,
    RiskDecisionTokenSigner,
    create_risk_audit_event,
    create_risk_decision_token,
    revoke_risk_approval_token,
    validate_risk_approval_token,
    verify_risk_audit_chain,
)
from app.services.risk.models import (
    ProposedTrade,
    RiskAuditEvent,
    RiskDecisionPackage,
    RiskDecisionStatus,
)
from app.services.risk.storage import InMemoryRiskStateStore, RiskAuditSink
from app.utils.errors import ValidationError


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


def test_redaction_rules():
    store = InMemoryRiskStateStore()

    # Action containing sensitive broker account identifier and raw private payloads
    trade_details = {
        "strategy_id": "strat_1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1,
        "account_id": "12345_broker_acc",
        "password": "supersecretpassword123",  # pragma: allowlist secret
        "api_key": "my_api_key_value",  # pragma: allowlist secret
        "private_payload": {"secret_data": "sensitive"},  # pragma: allowlist secret
    }

    decision = RiskDecisionPackage(
        decision_id="dec_redact",
        request_id="req_redact",
        workflow_id="wf_redact",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limits_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="cfg_hash_redact",
        reason="Limits cleared",
    )

    event = create_risk_audit_event(decision, trade_details, store)

    # Verify that sensitive fields are redacted in the logged details
    action_in_audit = event.details["proposed_action"]
    assert action_in_audit["account_id"] == "[REDACTED]"
    assert action_in_audit["password"] == "[REDACTED]"
    assert action_in_audit["api_key"] == "[REDACTED]"
    assert action_in_audit["private_payload"] == "[REDACTED]"

    # Safe fields must NOT be redacted
    assert action_in_audit["symbol"] == "EURUSD"
    assert action_in_audit["side"] == "buy"
    assert action_in_audit["volume"] == 0.1


def test_token_validation_with_policy_hash():
    store = InMemoryRiskStateStore()
    config_hash = "cfg_hash_xyz"
    policy_hash = "policy_hash_123"

    token = create_risk_decision_token(
        decision_id="dec_token_policy",
        request_id="req_token_policy",
        workflow_id="wf_token_policy",
        approved_action="execute_trade",
        config_hash=config_hash,
        decision_hash="dec_hash",
        scope={"symbol": "EURUSD"},
        expiry_seconds=300,
        policy_hash=policy_hash,
    )

    # Success validation with matching policy hash
    assert (
        validate_risk_approval_token(
            token=token,
            expected_scope={"symbol": "EURUSD"},
            active_config_hash=config_hash,
            active_policy_hash=policy_hash,
            state_store=store,
        )
        is True
    )

    # Failure validation with mismatched policy hash
    assert (
        validate_risk_approval_token(
            token=token,
            expected_scope={"symbol": "EURUSD"},
            active_config_hash=config_hash,
            active_policy_hash="mismatched_policy_hash_456",
            state_store=store,
        )
        is False
    )


def test_new_audit_classes_api():
    store = InMemoryRiskStateStore()
    audit_store = RiskAuditStore(store)
    signer = RiskDecisionTokenSigner(store)

    # Sign token
    token = signer.sign_token(
        decision_id="dec_signer",
        request_id="req_signer",
        workflow_id="wf_signer",
        approved_action="execute_trade",
        config_hash="config_hash",
        decision_hash="decision_hash",
        scope={"symbol": "EURUSD"},
        policy_hash="policy_hash",
    )
    assert token.signature != ""

    # Validate token
    assert (
        signer.validate_token(
            token=token,
            expected_scope={"symbol": "EURUSD"},
            active_config_hash="config_hash",
            active_policy_hash="policy_hash",
        )
        is True
    )

    # Revoke token
    signer.revoke_token(token.token_id)
    assert (
        signer.validate_token(
            token=token,
            expected_scope={"symbol": "EURUSD"},
            active_config_hash="config_hash",
            active_policy_hash="policy_hash",
        )
        is False
    )

    # Create event using builder
    decision = RiskDecisionPackage(
        decision_id="dec_builder",
        request_id="req_builder",
        workflow_id="wf_builder",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limits_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="config_hash",
        reason="Limits cleared",
    )
    builder = (
        RiskAuditEventBuilder()
        .with_decision(decision)
        .with_proposed_action({"symbol": "EURUSD"})
        .with_previous_hash("0" * 64)
    )
    event = builder.build()
    assert event.previous_hash == "0" * 64
    assert event.hash != ""

    # Verify hash chain manually
    assert RiskAuditHashChain.verify_integrity([event]) is True

    # Append event to store
    event_appended = audit_store.append_decision(decision, {"symbol": "EURUSD"})
    assert event_appended.previous_hash == "0" * 64
    assert audit_store.verify_chain() is True


def test_mandatory_audit_persistence_fail_closed():
    decision = RiskDecisionPackage(
        decision_id="dec_fail_closed",
        request_id="req_fail_closed",
        workflow_id="wf_fail_closed",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limits_gate",
        snapshot_as_of=datetime.now(UTC),
        config_hash="config_hash",
        reason="Limits cleared",
    )

    # 1. audit_sink is None raises ValidationError
    match_msg = r"Mandatory audit persistence is unavailable\."
    with pytest.raises(ValidationError, match=match_msg):
        create_risk_audit_event(decision, {"symbol": "EURUSD"}, None)

    # 2. audit_sink throws write exception
    class BadAuditSink(RiskAuditSink):
        def write_event(self, _event: RiskAuditEvent) -> None:
            raise RuntimeError("Database write error")

        def get_last_event(self) -> RiskAuditEvent | None:
            return None

        def get_all_events(self) -> list[RiskAuditEvent]:
            return []

    with pytest.raises(ValidationError, match="Audit persistence write failed"):
        create_risk_audit_event(decision, {"symbol": "EURUSD"}, BadAuditSink())
