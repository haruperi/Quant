"""Unit tests for official AI-callable risk tools facade."""

from datetime import UTC, datetime

import pytest
from agentic.tools.risk import (
    assess_risk_regime,
    build_portfolio_risk_snapshot,
    calculate_correlation_matrix,
    calculate_currency_exposure,
    calculate_expected_shortfall,
    calculate_portfolio_var,
    calculate_position_size,
    check_risk_kill_switch,
    check_risk_limits,
    create_risk_decision_package,
    generate_risk_report,
    get_shared_store,
    load_risk_policy,
    review_allocation_proposal,
    review_live_readiness,
    review_strategy_admission,
    review_trade_risk,
    run_portfolio_risk_governor,
    run_stress_scenario_analysis,
    validate_risk_approval_token,
    validate_risk_policy,
)
from app.services.risk.kill_switch import get_kill_switch_manager
from app.services.risk.models import KillSwitchStateEnum


@pytest.fixture(autouse=True)
def clean_test_state():
    # 1. Reset shared store
    store = get_shared_store()
    with store._lock:
        store._drawdown_states.clear()
        store._revoked_tokens.clear()
        store._audit_events.clear()
        store._policy_rules.clear()
        store._decisions.clear()
        store._decisions_by_request.clear()

    # 2. Reset kill switches
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
    with store._lock:
        store._drawdown_states.clear()
        store._revoked_tokens.clear()
        store._audit_events.clear()
        store._policy_rules.clear()
        store._decisions.clear()
        store._decisions_by_request.clear()
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


def test_build_portfolio_risk_snapshot():
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    market_context = {"mode": "paper"}
    res = build_portfolio_risk_snapshot(
        portfolio_state=portfolio,
        market_context=market_context,
        request_id="req_snap_tool",
    )
    assert res["status"] == "success"
    assert res["metadata"]["trades"] is False
    assert res["metadata"]["tool_name"] == "build_portfolio_risk_snapshot"
    assert "exposure" in res["data"]


def test_review_trade_risk():
    trade = {
        "strategy_id": "strat_1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1,
    }
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    market_context = {
        "mode": "paper",
        "environment": "local",
        "freshness": datetime.now(UTC).isoformat(),
        "daily_loss_pct": 0.0,
        "max_stress_ratio": 2.0,
    }
    res = review_trade_risk(
        proposed_trade=trade,
        portfolio_state=portfolio,
        market_context=market_context,
        request_id="req_review_tool",
    )
    assert res["status"] == "success"
    assert res["metadata"]["trades"] is False
    assert res["data"]["status"] == "approve"


def test_calculate_position_size():
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    trade = {
        "strategy_id": "strat_1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1,
    }
    market_context = {
        "mode": "paper",
        "symbol_metadata": {
            "EURUSD": {
                "min_volume": 0.01,
                "max_volume": 100.0,
                "lot_step": 0.01,
                "contract_size": 100000,
                "tick_size": 0.00001,
                "tick_value": 1.0,
                "quote_currency": "USD",
            }
        },
        "sizing_request": {
            "method": "fixed_fractional",
            "risk_percent": 0.01,
            "stop_loss_pips": 20.0,
        },
    }
    res = calculate_position_size(
        portfolio_state=portfolio,
        proposed_trade=trade,
        market_context=market_context,
        request_id="req_sizing_tool",
    )
    assert res["status"] == "success"
    assert "calculated_volume" in res["data"]


def test_assess_risk_regime():
    market_context = {
        "spreads": {"EURUSD": [0.0001, 0.0002, 0.00015]},
        "market_data": {
            "EURUSD": [
                {"timestamp": "2026-06-18T00:00:00Z", "close": 1.08},
                {"timestamp": "2026-06-18T01:00:00Z", "close": 1.085},
            ]
        },
    }
    res = assess_risk_regime(
        symbol="EURUSD",
        market_context=market_context,
        request_id="req_regime_tool",
    )
    assert res["status"] == "success"
    assert "regime" in res["data"]


def test_check_risk_kill_switch():
    res = check_risk_kill_switch(
        scope="global",
        target="*",
        request_id="req_ks_tool",
    )
    assert res["status"] == "success"
    assert "is_blocked" in res["data"]
    assert res["data"]["is_blocked"] is False


def test_run_stress_scenario_analysis():
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    trade = {
        "strategy_id": "strat_1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1,
    }
    market_context = {
        "mode": "paper",
        "symbol_metadata": {
            "EURUSD": {
                "min_volume": 0.01,
                "max_volume": 100.0,
                "lot_step": 0.01,
                "contract_size": 100000,
                "tick_size": 0.00001,
                "tick_value": 1.0,
                "quote_currency": "USD",
            }
        },
    }
    res = run_stress_scenario_analysis(
        portfolio_state=portfolio,
        proposed_trade=trade,
        market_context=market_context,
        request_id="req_scenario_tool",
    )
    assert res["status"] == "success"
    assert isinstance(res["data"], list)
    assert len(res["data"]) > 0


def test_generate_risk_report(tmp_path):
    report_file = tmp_path / "risk_report.json"
    res = generate_risk_report(
        request_id="req_report_tool",
        write_to_path=str(report_file),
    )
    assert res["status"] == "success"
    assert res["data"]["total_decisions_logged"] == 0
    assert report_file.exists()


# --- New Tools Tests ---


def test_load_risk_policy():
    res = load_risk_policy(profile_name="default", request_id="req_load_policy")
    assert res["status"] == "success"
    assert res["data"]["profile_name"] == "default"


def test_validate_risk_policy():
    policy = {
        "profile_name": "test_profile",
        "allow_live_execution": False,
        "max_daily_loss_pct": 0.05,
        "max_effective_leverage": 30.0,
    }
    res = validate_risk_policy(policy_data=policy, request_id="req_val_policy")
    assert res["status"] == "success"
    assert res["data"]["status"] == "valid"


def test_calculate_currency_exposure():
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    market_context = {"mode": "paper"}
    res = calculate_currency_exposure(
        portfolio_state=portfolio,
        proposed_trade=None,
        market_context=market_context,
        request_id="req_exposure",
    )
    assert res["status"] == "success"
    assert isinstance(res["data"], dict)


def test_calculate_correlation_matrix():
    market_data = {
        "EURUSD": [
            {
                "timestamp": "2026-06-18T00:00:00Z",
                "close": 1.08,
                "open": 1.08,
                "high": 1.09,
                "low": 1.07,
            },
            {
                "timestamp": "2026-06-18T01:00:00Z",
                "close": 1.085,
                "open": 1.08,
                "high": 1.09,
                "low": 1.07,
            },
            {
                "timestamp": "2026-06-18T02:00:00Z",
                "close": 1.082,
                "open": 1.08,
                "high": 1.09,
                "low": 1.07,
            },
        ],
        "GBPUSD": [
            {
                "timestamp": "2026-06-18T00:00:00Z",
                "close": 1.28,
                "open": 1.28,
                "high": 1.29,
                "low": 1.27,
            },
            {
                "timestamp": "2026-06-18T01:00:00Z",
                "close": 1.285,
                "open": 1.28,
                "high": 1.29,
                "low": 1.27,
            },
            {
                "timestamp": "2026-06-18T02:00:00Z",
                "close": 1.282,
                "open": 1.28,
                "high": 1.29,
                "low": 1.27,
            },
        ],
    }
    res = calculate_correlation_matrix(
        market_data=market_data,
        lookback=3,
        timeframe="H1",
        min_samples=2,
        exclude_last=False,
    )
    assert res["status"] == "success"
    assert "EURUSD" in res["data"]


def test_calculate_portfolio_var():
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    market_context = {
        "mode": "paper",
        "returns": {
            "EURUSD": [0.001, -0.002, 0.0015],
        },
        "prices": {
            "EURUSD": 1.08,
        },
    }
    res = calculate_portfolio_var(
        portfolio_state=portfolio,
        market_context=market_context,
        request_id="req_var",
    )
    assert res["status"] == "success"
    assert "var_value" in res["data"]


def test_calculate_expected_shortfall():
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    market_context = {
        "mode": "paper",
        "returns": {
            "EURUSD": [0.001, -0.002, 0.0015],
        },
        "prices": {
            "EURUSD": 1.08,
        },
    }
    res = calculate_expected_shortfall(
        portfolio_state=portfolio,
        market_context=market_context,
        request_id="req_es",
    )
    assert res["status"] == "success"
    assert "expected_shortfall_value" in res["data"]


def test_check_risk_limits():
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    trade = {
        "strategy_id": "strat_1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1,
    }
    res = check_risk_limits(
        proposed_trade=trade,
        portfolio_state=portfolio,
        request_id="req_limits",
    )
    assert res["status"] == "success"
    assert isinstance(res["data"], list)


def test_review_live_readiness():
    market_context = {"mode": "paper"}
    res = review_live_readiness(
        strategy_id="strat_1",
        proposed_stage="paper",
        market_context=market_context,
    )
    assert res["status"] == "success"
    assert "status" in res["data"]


def test_create_risk_decision_package():
    res = create_risk_decision_package(
        decision_id="dec_1",
        request_id="req_1",
        workflow_id="wf_1",
        status="approve",
        rule_key="all_pass",
        config_hash="abc",
        reason="Limits cleared",
        composite_breach_flags=[],
        calculated_volume=0.1,
    )
    assert res["status"] == "success"
    assert res["data"]["decision_id"] == "dec_1"


def test_review_strategy_admission():
    admission_request = {
        "strategy_id": "strat_1",
        "evidence": {},
    }
    res = review_strategy_admission(
        strategy_admission_request=admission_request,
        request_id="req_admit_tool",
    )
    assert res["status"] == "success"
    assert res["data"]["status"] == "reject"


def test_review_allocation_proposal():
    allocation = {
        "allocations": {"strat_1": 5000.0, "strat_2": 5000.0},
        "as_of": datetime.now(UTC).isoformat(),
    }
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    res = review_allocation_proposal(
        proposed_allocation=allocation,
        portfolio_state=portfolio,
        market_context={"strategy_stress_factors": {"strat_1": 0.01, "strat_2": 0.01}},
        request_id="req_alloc_tool",
    )
    assert res["status"] == "success"
    assert res["data"]["status"] == "needs_more_evidence"


def test_run_portfolio_risk_governor():
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    market_context = {"mode": "paper"}
    res = run_portfolio_risk_governor(
        portfolio_state=portfolio,
        market_context=market_context,
        request_id="req_gov_tool",
    )
    assert res["status"] == "success"
    assert res["data"]["status"] == "needs_more_evidence"


def test_validate_risk_approval_token():
    from app.services.risk.audit import RiskDecisionTokenSigner
    from app.services.risk.config import load_risk_config

    config = load_risk_config("default")
    signer = RiskDecisionTokenSigner(get_shared_store())

    token = signer.sign_token(
        decision_id="dec-1",
        request_id="req-1",
        workflow_id="wf-1",
        approved_action="override_limits",
        config_hash=config.contract_hash(),
        decision_hash="dec-1",
        scope={"symbol": "EURUSD", "environment": "staging"},
        expiry_seconds=300,
    )

    res = validate_risk_approval_token(
        token=token.model_dump(),
        expected_scope={"symbol": "EURUSD", "environment": "staging"},
        request_id="req_validate_token",
    )
    assert res["status"] == "success"
    assert res["data"]["is_valid"] is True


def test_tool_invalid_input_error():
    # Send malformed data to trigger validation exception
    res = review_trade_risk(
        proposed_trade={},
        portfolio_state={},
        market_context={"mode": "paper"},
        request_id="req_invalid_input",
    )
    assert res["status"] == "error"
    assert res["error"]["code"] in {"TOOL_EXECUTION_FAILED", "VALIDATION_FAILED"}


def test_live_sensitive_tools_fail_closed_validation():
    trade = {
        "strategy_id": "strat_1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1,
    }
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }

    # Live mode with missing operator_role and freshness should fail validation
    market_context = {
        "mode": "full_live",
        "environment": "production",
    }
    res = review_trade_risk(
        proposed_trade=trade,
        portfolio_state=portfolio,
        market_context=market_context,
        request_id="req_live_fail",
    )
    assert res["status"] == "error"
    assert res["error"]["code"] in {"TOOL_EXECUTION_FAILED", "VALIDATION_FAILED"}
    assert "Missing or unauthorized operator role" in res["error"]["details"]


def test_kill_switch_active_blocking():
    manager = get_kill_switch_manager()
    with manager._lock:
        manager.states["global"] = {
            "state": KillSwitchStateEnum.ACTIVE,
            "reason": "Emergency halt",
            "triggered_at": datetime.now(UTC).isoformat(),
            "triggered_by": "operator",
        }
        manager.save()

    res = check_risk_kill_switch(
        scope="global",
        target="*",
        request_id="req_ks_active",
    )
    assert res["status"] == "success"
    assert res["data"]["is_blocked"] is True
    assert res["data"]["state"] == "active"
    assert res["data"]["reason"] == "Emergency halt"


def test_metadata_correctness():
    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }

    # build_portfolio_risk_snapshot is read-only
    res = build_portfolio_risk_snapshot(
        portfolio_state=portfolio,
        market_context={"mode": "paper"},
        request_id="req_meta_check",
    )
    assert res["status"] == "success"
    assert res["metadata"]["places_trade"] is False
    assert res["metadata"]["read_only"] is True

    # review_trade_risk is not read-only
    trade = {
        "strategy_id": "strat_1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1,
    }
    res2 = review_trade_risk(
        proposed_trade=trade,
        portfolio_state=portfolio,
        market_context={"mode": "paper"},
        request_id="req_meta_check_2",
    )
    assert res2["status"] == "success"
    assert res2["metadata"]["places_trade"] is False
    assert res2["metadata"]["read_only"] is False
