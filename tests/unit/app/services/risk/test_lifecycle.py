"""Unit tests for strategy lifecycle promotion and live readiness gates.

Verifies sequential progression constraints, required out-of-sample metrics,
and security/auditing controls for live environments.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import RiskConfig, RiskDecisionStatus, RiskReasonCode
from app.services.risk.lifecycle import (
    RiskLifecycleState,
    evaluate_lifecycle_promotion,
    evaluate_live_readiness,
    review_live_readiness,
    review_mode_promotion,
    review_strategy_admission,
)


@pytest.fixture
def base_config() -> RiskConfig:
    """Fixture for baseline RiskConfig with stage gate metrics."""
    return RiskConfig(
        profile_name="default",
        min_backtest_trades=100,
        min_backtest_sharpe=Decimal("1.5"),
        max_backtest_drawdown=Decimal("0.20"),
        min_wf_trades=50,
        min_wf_sharpe=Decimal("1.2"),
        min_sim_trades=30,
        min_sim_profit_factor=Decimal("1.1"),
        min_paper_trades=20,
        min_paper_sharpe=Decimal("1.0"),
        max_shadow_tracking_error=Decimal("0.05"),
        min_shadow_days=14,
        min_live_days=30,
        min_live_sharpe=Decimal("1.0"),
    )


def test_invalid_lifecycle_stages(base_config: RiskConfig) -> None:
    """Verify that invalid stage names are rejected."""
    res = evaluate_lifecycle_promotion(
        "strat1", "invalid-stage", "backtest", {}, base_config
    )
    assert res.status == RiskDecisionStatus.REJECT
    assert res.reason_code == RiskReasonCode.INVALID_INPUT


def test_lifecycle_demotion_approved(base_config: RiskConfig) -> None:
    """Verify that same-stage transitions and demotions are always approved."""
    res_same = evaluate_lifecycle_promotion("strat1", "paper", "paper", {}, base_config)
    assert res_same.status == RiskDecisionStatus.APPROVE
    assert not res_same.breached

    res_demote = evaluate_lifecycle_promotion(
        "strat1", "paper", "simulation", {}, base_config
    )
    assert res_demote.status == RiskDecisionStatus.APPROVE
    assert not res_demote.breached


def test_lifecycle_skip_gate_blocked(base_config: RiskConfig) -> None:
    """Verify that skipping lifecycle stages is blocked."""
    res = evaluate_lifecycle_promotion(
        "strat1", "backtest", "simulation", {}, base_config
    )
    assert res.status == RiskDecisionStatus.REJECT
    assert "skip-gate" in res.message


def test_gate_backtest_to_walkforward(base_config: RiskConfig) -> None:
    """Verify metrics for backtest to walk-forward promotion."""
    # Pass
    evidence: dict[str, Any] = {
        "trade_count": 105,
        "sharpe_ratio": 1.6,
        "max_drawdown": 0.15,
    }
    res = evaluate_lifecycle_promotion(
        "strat1", "backtest", "walk-forward", evidence, base_config
    )
    assert res.status == RiskDecisionStatus.APPROVE

    # Fail trades
    evidence["trade_count"] = 90
    res_fail = evaluate_lifecycle_promotion(
        "strat1", "backtest", "walk-forward", evidence, base_config
    )
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Fail Sharpe
    evidence["trade_count"] = 105
    evidence["sharpe_ratio"] = 1.4
    res_fail = evaluate_lifecycle_promotion(
        "strat1", "backtest", "walk-forward", evidence, base_config
    )
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Fail drawdown
    evidence["sharpe_ratio"] = 1.6
    evidence["max_drawdown"] = 0.25
    res_fail = evaluate_lifecycle_promotion(
        "strat1", "backtest", "walk-forward", evidence, base_config
    )
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_gate_walkforward_to_simulation(base_config: RiskConfig) -> None:
    """Verify metrics for walk-forward to simulation promotion."""
    evidence: dict[str, Any] = {
        "trade_count": 55,
        "sharpe_ratio": 1.3,
    }
    res = evaluate_lifecycle_promotion(
        "strat1", "walk-forward", "simulation", evidence, base_config
    )
    assert res.status == RiskDecisionStatus.APPROVE

    evidence["trade_count"] = 40
    res_fail = evaluate_lifecycle_promotion(
        "strat1", "walk-forward", "simulation", evidence, base_config
    )
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_gate_simulation_to_paper(base_config: RiskConfig) -> None:
    """Verify metrics for simulation to paper promotion."""
    evidence: dict[str, Any] = {
        "trade_count": 35,
        "profit_factor": 1.2,
    }
    res = evaluate_lifecycle_promotion(
        "strat1", "simulation", "paper", evidence, base_config
    )
    assert res.status == RiskDecisionStatus.APPROVE

    evidence["profit_factor"] = 1.05
    res_fail = evaluate_lifecycle_promotion(
        "strat1", "simulation", "paper", evidence, base_config
    )
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_gate_paper_to_shadow(base_config: RiskConfig) -> None:
    """Verify metrics for paper to shadow promotion."""
    evidence: dict[str, Any] = {
        "trade_count": 25,
        "sharpe_ratio": 1.1,
    }
    res = evaluate_lifecycle_promotion(
        "strat1", "paper", "shadow", evidence, base_config
    )
    assert res.status == RiskDecisionStatus.APPROVE

    evidence["sharpe_ratio"] = 0.9
    res_fail = evaluate_lifecycle_promotion(
        "strat1", "paper", "shadow", evidence, base_config
    )
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_gate_shadow_to_microlive(base_config: RiskConfig) -> None:
    """Verify metrics for shadow to micro-live promotion."""
    evidence: dict[str, Any] = {
        "tracking_error": 0.04,
        "duration_days": 15,
    }
    res = evaluate_lifecycle_promotion(
        "strat1", "shadow", "micro-live", evidence, base_config
    )
    assert res.status == RiskDecisionStatus.APPROVE

    evidence["tracking_error"] = 0.06
    res_fail = evaluate_lifecycle_promotion(
        "strat1", "shadow", "micro-live", evidence, base_config
    )
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_gate_microlive_to_fulllive(base_config: RiskConfig) -> None:
    """Verify metrics for micro-live to full-live promotion."""
    evidence: dict[str, Any] = {
        "duration_days": 35,
        "sharpe_ratio": 1.2,
    }
    res = evaluate_lifecycle_promotion(
        "strat1", "micro-live", "full-live", evidence, base_config
    )
    assert res.status == RiskDecisionStatus.APPROVE

    evidence["duration_days"] = 20
    res_fail = evaluate_lifecycle_promotion(
        "strat1", "micro-live", "full-live", evidence, base_config
    )
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_live_readiness_checks(base_config: RiskConfig) -> None:
    """Verify readiness checklist enforcement for live environments."""
    # 1. Non-live sensitive stages pass automatically
    res_non_live = evaluate_live_readiness("strat1", "paper", {}, base_config)
    assert res_non_live.status == RiskDecisionStatus.APPROVE

    # 2. Live sensitive stage (shadow) fails if audit sink is inactive
    market_context: dict[str, Any] = {
        "audit_persistence_active": False,
        "kill_switch_configured": True,
        "portfolio_reconciliation_active": True,
        "idempotency_evidence_present": True,
    }
    res = evaluate_live_readiness("strat1", "shadow", market_context, base_config)
    assert res.status == RiskDecisionStatus.BLOCK

    # 3. Fails if kill switch is not configured
    market_context["audit_persistence_active"] = True
    market_context["kill_switch_configured"] = False
    res = evaluate_live_readiness("strat1", "shadow", market_context, base_config)
    assert res.status == RiskDecisionStatus.BLOCK

    # 4. Fails if reconciliation or idempotency evidence is missing
    market_context["kill_switch_configured"] = True
    market_context["portfolio_reconciliation_active"] = False
    res = evaluate_live_readiness("strat1", "shadow", market_context, base_config)
    assert res.status == RiskDecisionStatus.BLOCK

    # 5. Passes if all parameters are true
    market_context["portfolio_reconciliation_active"] = True
    res = evaluate_live_readiness("strat1", "shadow", market_context, base_config)
    assert res.status == RiskDecisionStatus.APPROVE


def test_risk_lifecycle_state_enum() -> None:
    """Verify that all lifecycle states are present in the StrEnum."""
    assert RiskLifecycleState.RESEARCH.value == "research"
    assert RiskLifecycleState.SIMULATION.value == "simulation"
    assert RiskLifecycleState.PAPER.value == "paper"
    assert RiskLifecycleState.SHADOW.value == "shadow"
    assert RiskLifecycleState.LIVE_READONLY.value == "live-read-only"
    assert RiskLifecycleState.MICRO_LIVE.value == "micro-live"
    assert RiskLifecycleState.FULL_LIVE.value == "full-live"


def test_strategy_admission_review(base_config: RiskConfig) -> None:
    """Verify strategy admission gate logic."""
    # 1. Missing evidence packages
    evidence_missing: dict[str, Any] = {
        "backtest": {},
        "walk_forward": {},
        # missing out_of_sample, simulation, risk_metrics
    }
    res = review_strategy_admission("strat1", evidence_missing, base_config)
    assert res.status == RiskDecisionStatus.REJECT
    assert res.reason_code == RiskReasonCode.STALE_EVIDENCE
    assert res.breached
    assert any("Missing required" in b for b in res.breaches)

    # 2. Complete evidence but failing metric thresholds
    evidence_fail = {
        "backtest": {
            "trade_count": 50,  # required min_backtest_trades=100
            "sharpe_ratio": "1.2",  # required min_backtest_sharpe=1.5
            "max_drawdown": "0.10",
        },
        "walk_forward": {},
        "out_of_sample": {},
        "simulation": {},
        "risk_metrics": {},
    }
    res = review_strategy_admission("strat1", evidence_fail, base_config)
    assert res.status == RiskDecisionStatus.REJECT
    assert res.breached
    assert any("trades low" in b for b in res.breaches)

    # 3. Approved admission
    evidence_pass = {
        "backtest": {
            "trade_count": 120,
            "sharpe_ratio": "1.8",
            "max_drawdown": "0.12",
        },
        "walk_forward": {},
        "out_of_sample": {},
        "simulation": {},
        "risk_metrics": {},
    }
    res = review_strategy_admission("strat1", evidence_pass, base_config)
    assert res.status == RiskDecisionStatus.APPROVE
    assert not res.breached


def test_live_readiness_new_checks(base_config: RiskConfig) -> None:
    """Verify readiness checklist with new required parameters."""
    market_context: dict[str, Any] = {
        "audit_persistence_active": True,
        "kill_switch_configured": True,
        "portfolio_reconciliation_active": True,
        "idempotency_evidence_present": True,
        "broker_metadata_available": True,
        "risk_config_available": True,
        "policy_enforcement_active": True,
    }

    # All pass
    res = review_live_readiness("strat1", "live-read-only", market_context, base_config)
    assert res.status == RiskDecisionStatus.APPROVE
    assert not res.breached

    # Fail closed when broker metadata is unavailable
    market_context["broker_metadata_available"] = False
    res = review_live_readiness("strat1", "live-read-only", market_context, base_config)
    assert res.status == RiskDecisionStatus.BLOCK
    assert res.breached
    assert any("broker metadata" in b for b in res.breaches)

    # Fail closed when policy enforcement is unavailable
    market_context["broker_metadata_available"] = True
    market_context["policy_enforcement_active"] = False
    res = review_live_readiness("strat1", "live-read-only", market_context, base_config)
    assert res.status == RiskDecisionStatus.BLOCK
    assert any("policy enforcement" in b for b in res.breaches)


def test_mode_promotion_new_transitions(base_config: RiskConfig) -> None:
    """Verify transition metric checking and sequential gates for new sequence."""
    evidence = {
        "trade_count": 100,
        "sharpe_ratio": "2.0",
        "profit_factor": "1.5",
        "tracking_error": "0.02",
        "duration_days": 40,
    }

    # 1. Research -> Simulation (Walk-forward checks)
    evidence["trade_count"] = 60  # min_wf_trades = 50
    evidence["sharpe_ratio"] = "1.3"  # min_wf_sharpe = 1.2
    res = review_mode_promotion(
        "strat1", "research", "simulation", evidence, base_config
    )
    assert res.status == RiskDecisionStatus.APPROVE

    # 2. Simulation -> Paper (Sim checks)
    evidence["trade_count"] = 35  # min_sim_trades = 30
    evidence["profit_factor"] = "1.2"  # min_sim_pf = 1.1
    res = review_mode_promotion("strat1", "simulation", "paper", evidence, base_config)
    assert res.status == RiskDecisionStatus.APPROVE

    # 3. Paper -> Shadow (Paper checks)
    # Missing approval token => status = NEEDS_APPROVAL
    res = review_mode_promotion("strat1", "paper", "shadow", evidence, base_config)
    assert res.status == RiskDecisionStatus.NEEDS_APPROVAL
    assert res.breached

    # With mock validation
    res = review_mode_promotion(
        "strat1",
        "paper",
        "shadow",
        evidence,
        base_config,
        market_context={"approval_token_valid": True},
    )
    assert res.status == RiskDecisionStatus.APPROVE

    # 4. Shadow -> Live-read-only
    res = review_mode_promotion(
        "strat1",
        "shadow",
        "live-read-only",
        evidence,
        base_config,
        market_context={"approval_token_valid": True},
    )
    assert res.status == RiskDecisionStatus.APPROVE

    # 5. Live-read-only -> Micro-live
    res = review_mode_promotion(
        "strat1",
        "live-read-only",
        "micro-live",
        evidence,
        base_config,
        market_context={"approval_token_valid": True},
    )
    assert res.status == RiskDecisionStatus.APPROVE

    # 6. Micro-live -> Full-live
    res = review_mode_promotion(
        "strat1",
        "micro-live",
        "full-live",
        evidence,
        base_config,
        market_context={"approval_token_valid": True},
    )
    assert res.status == RiskDecisionStatus.APPROVE
