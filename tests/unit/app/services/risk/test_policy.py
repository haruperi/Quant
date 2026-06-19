"""Unit tests for Risk Policy resolution and override token validation."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.services.risk.config import load_risk_config
from app.services.risk.models import (
    PolicyRule,
    PolicyScope,
    RiskApprovalToken,
    RiskConfig,
    RiskDecisionStatus,
    RiskMode,
)
from app.services.risk.policy import (
    resolve_policy,
    validate_override_token,
    validate_risk_budget_gates,
)
from app.utils.normalization import utc_now


@pytest.fixture
def base_config() -> RiskConfig:
    """Load default base risk config."""
    return load_risk_config("default")


def test_resolve_policy_default_no_rules(base_config: RiskConfig) -> None:
    """Test policy resolution when no rules are applied."""
    context = {"environment": "local", "mode": RiskMode.SIMULATION}
    result = resolve_policy(base_config, [], context)
    assert result.status == RiskDecisionStatus.APPROVE
    assert result.resolved_config.max_daily_loss_pct == base_config.max_daily_loss_pct
    assert result.policy_hash == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4"  # pragma: allowlist secret
        "649b934ca495991b7852b855"  # pragma: allowlist secret
    )  # sha256 of empty str


def test_resolve_policy_with_matching_rules(base_config: RiskConfig) -> None:
    """Test policy resolution with scoped rules matching the context."""
    rules = [
        PolicyRule(
            rule_id="r1",
            scope=PolicyScope(strategy_id="mean-reversion-v1"),
            overrides={"max_daily_loss_pct": 0.08},
        ),
        PolicyRule(
            rule_id="r2",
            scope=PolicyScope(symbol="EURUSD"),
            overrides={"max_effective_leverage": 20.0},
        ),
    ]

    # Context matching both rules
    context = {
        "strategy_id": "mean-reversion-v1",
        "symbol": "EURUSD",
        "environment": "local",
    }
    result = resolve_policy(base_config, rules, context)
    assert result.status == RiskDecisionStatus.APPROVE
    assert result.resolved_config.max_daily_loss_pct == Decimal("0.08")
    assert result.resolved_config.max_effective_leverage == Decimal("20.0")


def test_resolve_policy_precedence(base_config: RiskConfig) -> None:
    """Test that policy precedence works correctly (more specific overrides win)."""
    # symbol scope is more specific than strategy, which is more specific than account
    rules = [
        PolicyRule(
            rule_id="r_acc",
            scope=PolicyScope(account_id="acc-123"),
            overrides={"max_daily_loss_pct": 0.06},
        ),
        PolicyRule(
            rule_id="r_strat",
            scope=PolicyScope(strategy_id="mean-reversion-v1"),
            overrides={"max_daily_loss_pct": 0.07},
        ),
        PolicyRule(
            rule_id="r_sym",
            scope=PolicyScope(symbol="EURUSD"),
            overrides={"max_daily_loss_pct": 0.08},
        ),
    ]

    context = {
        "account_id": "acc-123",
        "strategy_id": "mean-reversion-v1",
        "symbol": "EURUSD",
        "environment": "local",
    }
    result = resolve_policy(base_config, rules, context)
    assert result.status == RiskDecisionStatus.APPROVE
    # Symbol wins precedence
    assert result.resolved_config.max_daily_loss_pct == Decimal("0.08")


def test_resolve_policy_expiry(base_config: RiskConfig) -> None:
    """Test that expired rules are ignored during resolution."""
    now = utc_now()
    rules = [
        PolicyRule(
            rule_id="expired_rule",
            scope=PolicyScope(strategy_id="expired-strat"),
            overrides={"max_daily_loss_pct": 0.08},
            expiry_time=now - timedelta(seconds=1),
        ),
        PolicyRule(
            rule_id="valid_rule",
            scope=PolicyScope(strategy_id="expired-strat"),
            overrides={"max_effective_leverage": 15.0},
            expiry_time=now + timedelta(hours=1),
        ),
    ]

    context = {"strategy_id": "expired-strat", "environment": "local"}
    result = resolve_policy(base_config, rules, context)
    # Expired override ignored
    assert result.resolved_config.max_daily_loss_pct == base_config.max_daily_loss_pct
    # Valid override applied
    assert result.resolved_config.max_effective_leverage == Decimal("15.0")


def test_resolve_policy_ceiling_violation(base_config: RiskConfig) -> None:
    """Test that resolving overrides exceeding ceilings fails closed (rejection)."""
    rules = [
        PolicyRule(
            rule_id="unsafe_override",
            scope=PolicyScope(strategy_id="unsafe-strat"),
            overrides={"max_daily_loss_pct": 0.25},  # Hard ceiling is 0.20
        ),
    ]

    context = {"strategy_id": "unsafe-strat", "environment": "local"}
    result = resolve_policy(base_config, rules, context)
    assert result.status == RiskDecisionStatus.REJECT
    assert len(result.breaches) > 0


def test_resolve_policy_live_sensitive_blocked(base_config: RiskConfig) -> None:
    """Test that live sensitive modes block configs without live authorization."""
    context = {"environment": "production", "mode": RiskMode.FULL_LIVE}
    # base_config loaded from "default" has allow_live_execution=False
    result = resolve_policy(base_config, [], context)
    assert result.status == RiskDecisionStatus.BLOCK
    assert "Execution blocked" in result.reason


def test_validate_override_token() -> None:
    """Test validation checks on RiskApprovalToken limit overrides."""
    now = utc_now()
    cfg_hash = "cfg_hash_123"

    token = RiskApprovalToken(
        token_id="tok-001",
        request_id="req-1",
        workflow_id="wf-1",
        approved_action="override_limits",
        approver="risk_manager",
        expiry_time=now + timedelta(minutes=30),
        config_hash=cfg_hash,
        decision_hash="dec-1",
        scope={"symbol": "EURUSD", "environment": "staging"},
        nonce="nonce-1",
        signature="sig-1",
    )

    # Valid check
    assert validate_override_token(token, {"symbol": "EURUSD"}, cfg_hash) is True

    # Expired token check
    expired_token = token.model_copy(update={"expiry_time": now - timedelta(seconds=1)})
    assert (
        validate_override_token(expired_token, {"symbol": "EURUSD"}, cfg_hash) is False
    )

    # Config hash mismatch check
    assert (
        validate_override_token(token, {"symbol": "EURUSD"}, "different_hash") is False
    )

    # Scope mismatch check
    assert validate_override_token(token, {"symbol": "GBPUSD"}, cfg_hash) is False

    # Live override role verification check (only authorized roles)
    unauthorized_token = token.model_copy(update={"approver": "strategy_developer"})
    assert (
        validate_override_token(unauthorized_token, {"symbol": "EURUSD"}, cfg_hash)
        is False
    )


def test_validate_risk_budget_gates(base_config: RiskConfig) -> None:
    """Test risk budget gate validation logic."""
    assert (
        validate_risk_budget_gates("strat-1", Decimal("1000.00"), base_config) is True
    )

    # Check that negative or zero limits fail
    invalid_config = base_config.model_copy(
        update={"max_risk_per_trade": Decimal("-0.01")}
    )
    assert (
        validate_risk_budget_gates("strat-1", Decimal("1000.00"), invalid_config)
        is False
    )


def test_risk_policy_engine_resolution(base_config: RiskConfig) -> None:
    """Test RiskPolicyEngine matching and resolution with bundle and policies."""
    from app.services.risk.models import PolicyRule, PolicyScope
    from app.services.risk.policy import (
        PolicyBundle,
        PolicyResolutionQuery,
        PolicyVersion,
        RiskPolicy,
        RiskPolicyEngine,
    )

    version = PolicyVersion(version_id="v1.0.0", author="compliance_officer")
    policy = RiskPolicy(
        policy_id="pol-001",
        profile_name="default",
        rules=[
            PolicyRule(
                rule_id="rule-leverage",
                scope=PolicyScope(
                    environment="production", mode=RiskMode.FULL_LIVE, symbol="EURUSD"
                ),
                overrides={
                    "max_effective_leverage": Decimal("10.0"),
                    "allow_live_execution": True,
                },
            )
        ],
    )
    bundle = PolicyBundle(bundle_id="bundle-1", version=version, policies=[policy])
    engine = RiskPolicyEngine(bundle=bundle)

    query = PolicyResolutionQuery(
        environment="production",
        mode="full_live",
        symbol="EURUSD",
    )
    # Resolve config with overrides, version metadata, and scope metadata
    result = engine.resolve(query, base_config)
    assert result.status == RiskDecisionStatus.APPROVE
    assert result.resolved_config.max_effective_leverage == Decimal("10.0")
    assert result.policy_version == "v1.0.0"
    assert result.policy_scope is not None
    assert result.policy_scope.get("environment") == "production"


def test_check_policy_permission_scenarios() -> None:
    """Test check_policy_permission role constraints by environment."""
    from app.services.risk.policy import check_policy_permission

    # In production/staging, only admin, compliance_officer, risk_manager are allowed
    assert check_policy_permission("admin", "override_limits", "production") is True
    assert (
        check_policy_permission("compliance_officer", "override_limits", "staging")
        is True
    )
    assert (
        check_policy_permission("risk_manager", "override_limits", "production") is True
    )
    assert (
        check_policy_permission("developer", "override_limits", "production") is False
    )
    assert check_policy_permission("operator", "override_limits", "production") is False

    # force_resume requires admin or compliance_officer in prod/staging
    assert check_policy_permission("admin", "force_resume", "production") is True
    assert (
        check_policy_permission("compliance_officer", "force_resume", "production")
        is True
    )
    assert (
        check_policy_permission("risk_manager", "force_resume", "production") is False
    )

    # In local/simulation, developers and operators are allowed
    assert check_policy_permission("developer", "override_limits", "local") is True
    assert check_policy_permission("operator", "override_limits", "local") is True
    assert check_policy_permission("visitor", "override_limits", "local") is False


def test_policy_override_request_validation() -> None:
    """Test PolicyOverrideRequest validation structure."""
    from datetime import timedelta

    from app.services.risk.policy import PolicyOverrideRequest

    now = utc_now()
    token = RiskApprovalToken(
        token_id="tok-002",
        request_id="req-2",
        workflow_id="wf-2",
        approved_action="override_limits",
        approver="compliance_officer",
        expiry_time=now + timedelta(minutes=30),
        config_hash="hash_123",
        decision_hash="dec-2",
        scope={"symbol": "EURUSD"},
        nonce="nonce-2",
        signature="sig-2",
    )

    req = PolicyOverrideRequest(
        request_id="req-2",
        token=token,
        target_overrides={"max_effective_leverage": 15.0},
    )
    assert req.request_id == "req-2"
    assert req.token.token_id == "tok-002"
    assert req.target_overrides["max_effective_leverage"] == 15.0
