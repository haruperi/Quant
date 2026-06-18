"""Unit tests for official AI-callable risk tools facade."""

from datetime import UTC, datetime

import pytest
from app.services.risk.kill_switch import get_kill_switch_manager
from app.services.risk.models import KillSwitchStateEnum
from app.services.risk.tools import (
    assess_risk_regime_tool,
    build_portfolio_risk_snapshot_tool,
    calculate_position_size_tool,
    check_risk_kill_switch_tool,
    generate_risk_report_tool,
    get_shared_store,
    review_trade_risk_tool,
    run_risk_scenario_analysis_tool,
)


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


def test_build_portfolio_risk_snapshot_tool():
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
    res = build_portfolio_risk_snapshot_tool(
        portfolio_state=portfolio,
        market_context=market_context,
        request_id="req_snap_tool",
    )
    assert res["status"] == "success"
    assert res["metadata"]["trades"] is False
    assert res["metadata"]["tool_name"] == "build_portfolio_risk_snapshot_tool"
    assert "exposure" in res["data"]


def test_review_trade_risk_tool():
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
    res = review_trade_risk_tool(
        proposed_trade=trade,
        portfolio_state=portfolio,
        market_context=market_context,
        request_id="req_review_tool",
    )
    assert res["status"] == "success"
    assert res["metadata"]["trades"] is False
    assert res["data"]["status"] == "approve"


def test_calculate_position_size_tool():
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
    res = calculate_position_size_tool(
        portfolio_state=portfolio,
        proposed_trade=trade,
        market_context=market_context,
        request_id="req_sizing_tool",
    )
    assert res["status"] == "success"
    assert "calculated_volume" in res["data"]


def test_assess_risk_regime_tool():
    market_context = {
        "spreads": {"EURUSD": [0.0001, 0.0002, 0.00015]},
        "market_data": {
            "EURUSD": [
                {"timestamp": "2026-06-18T00:00:00Z", "close": 1.08},
                {"timestamp": "2026-06-18T01:00:00Z", "close": 1.085},
            ]
        },
    }
    res = assess_risk_regime_tool(
        symbol="EURUSD",
        market_context=market_context,
        request_id="req_regime_tool",
    )
    assert res["status"] == "success"
    assert "regime" in res["data"]


def test_check_risk_kill_switch_tool():
    res = check_risk_kill_switch_tool(
        scope="global",
        target="*",
        request_id="req_ks_tool",
    )
    assert res["status"] == "success"
    assert "is_blocked" in res["data"]
    assert res["data"]["is_blocked"] is False


def test_run_risk_scenario_analysis_tool():
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
    res = run_risk_scenario_analysis_tool(
        portfolio_state=portfolio,
        proposed_trade=trade,
        market_context=market_context,
        request_id="req_scenario_tool",
    )
    assert res["status"] == "success"
    assert isinstance(res["data"], list)
    assert len(res["data"]) > 0


def test_generate_risk_report_tool(tmp_path):
    report_file = tmp_path / "risk_report.json"
    res = generate_risk_report_tool(
        request_id="req_report_tool",
        write_to_path=str(report_file),
    )
    assert res["status"] == "success"
    assert res["data"]["total_decisions_logged"] == 0
    assert report_file.exists()
