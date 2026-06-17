from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk import (
    PortfolioState,
    PositionSizingRequest,
    ProposedAllocation,
    ProposedTrade,
    RiskApprovalToken,
    RiskConfig,
    RiskDecisionPackage,
    StressScenario,
    assess_risk_regime,
    build_portfolio_risk_snapshot,
    calculate_position_size,
    create_risk_decision_package,
    generate_risk_report,
    review_allocation_proposal,
    review_strategy_admission,
    review_trade_risk,
    run_risk_scenario_analysis,
    validate_risk_approval_token,
)


@pytest.fixture
def base_config():
    return RiskConfig(
        max_daily_loss_pct=Decimal("0.05"),
        max_total_loss_pct=Decimal("0.10"),
    ).model_dump()


@pytest.fixture
def base_portfolio():
    return PortfolioState(
        account_id="acc_123",
        balance=Decimal(10000),
        equity=Decimal(10000),
        margin_used=Decimal(0),
        free_margin=Decimal(10000),
        floating_pnl=Decimal(0),
        realized_pnl=Decimal(0),
        currency="USD",
        historical_returns=[
            Decimal("0.01"),
            Decimal("-0.01"),
            Decimal("0.02"),
            Decimal("-0.02"),
            Decimal("0.005"),
        ],
        as_of=datetime.now(UTC),
    )


def test_build_portfolio_snapshot_tool(base_portfolio, base_config):
    res = build_portfolio_risk_snapshot(
        base_portfolio, base_config, request_id="req_snap"
    )
    assert res["status"] == "success"
    assert res["data"]["account_id"] == "acc_123"
    assert "metadata" in res


def test_review_trade_risk_tool(base_portfolio, base_config):
    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
        stop_loss=Decimal("0.99"),
    )
    res = review_trade_risk(
        trade,
        base_portfolio,
        market_context={"spread": 1.0, "slippage": 0.5},
        risk_config=base_config,
        request_id="req_review",
    )
    assert res["status"] == "success"
    assert res["data"]["status"] == "approve"


def test_calculate_position_size_tool(base_portfolio, base_config):
    req = PositionSizingRequest(
        symbol="EURUSD",
        method="fixed_risk",
        risk_percent=Decimal("1.0"),
        stop_loss_pips=Decimal("20.0"),
    )
    res = calculate_position_size(
        req, base_portfolio, base_config, request_id="req_size"
    )
    assert res["status"] == "success"
    assert Decimal(res["data"]["calculated_volume"]) == Decimal("0.5")


def test_assess_risk_regime_tool(base_portfolio, base_config):
    res = assess_risk_regime(base_portfolio, base_config, request_id="req_regime")
    assert res["status"] == "success"
    assert res["data"]["drawdown_regime"] == "normal"


def test_review_strategy_admission_tool():
    evidence = {"win_rate": "0.55", "profit_factor": "1.5"}
    res = review_strategy_admission("strat_1", evidence, request_id="req_admit")
    assert res["status"] == "success"
    assert res["data"]["status"] == "approved"


def test_review_allocation_proposal_tool(base_portfolio, base_config):
    proposal = ProposedAllocation(
        allocations={"strat_A": Decimal(2000), "strat_B": Decimal(2000)},
        as_of=datetime.now(UTC),
    )
    res = review_allocation_proposal(
        proposal, base_portfolio, base_config, request_id="req_alloc"
    )
    assert res["status"] == "success"
    assert res["data"]["status"] == "accepted"


def test_create_risk_decision_package_tool():
    res = create_risk_decision_package(
        "dec_1", "approve", "rule_ok", "Passed checks", request_id="req_create"
    )
    assert res["status"] == "success"
    assert res["data"]["status"] == "approve"


def test_validate_risk_approval_token_tool():
    token = RiskApprovalToken(
        token_id="tok_1",
        request_id="req_1",
        workflow_id="wf_1",
        approved_action="execute_trade",
        approver="admin",
        expiry_time=datetime.now(UTC)
        + pytest.importorskip("datetime").timedelta(hours=1),
        config_hash="hash_1",
        decision_hash="dec_hash",
        scope={"symbol": "EURUSD"},
        nonce="nonce_123",
        signature="sig",
    )
    res = validate_risk_approval_token(
        token, {"symbol": "EURUSD"}, request_id="req_val"
    )
    assert res["status"] == "success"
    assert res["data"]["valid"] is True


def test_run_risk_scenario_analysis_tool(base_portfolio, base_config):
    scenarios = [
        StressScenario(name="USD Shock", price_shocks={"EURUSD": Decimal("0.02")})
    ]
    res = run_risk_scenario_analysis(
        base_portfolio, scenarios, base_config, request_id="req_scenario"
    )
    assert res["status"] == "success"
    assert len(res["data"]) == 1


def test_generate_risk_report_tool():
    package = RiskDecisionPackage(
        decision_id="dec_1",
        request_id="req_1",
        workflow_id="wf_1",
        status="approve",
        rule_key="rule_ok",
        snapshot_as_of=datetime.now(UTC),
        config_hash="hash_1",
        reason="No breaches",
    )
    res = generate_risk_report(
        package, output_format="markdown", request_id="req_report"
    )
    assert res["status"] == "success"
    assert "# Risk Decision Report" in res["data"]["content"]


def test_payload_limits_depth(base_portfolio, base_config):
    # Create a deeply nested dict (depth 12)
    nested = {}
    curr = nested
    for _ in range(12):
        curr["key"] = {}
        curr = curr["key"]
    res = build_portfolio_risk_snapshot(
        base_portfolio, nested, request_id="deep_payload"
    )
    assert res["status"] == "error"
    assert res["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_payload_limits_large_dict(base_portfolio, base_config):
    large_dict = {str(i): idx for idx, i in enumerate(range(10005))}
    portfolio = base_portfolio.model_copy(update={"strategy_allocations": large_dict})
    res = build_portfolio_risk_snapshot(
        portfolio, base_config, request_id="large_payload"
    )
    assert res["status"] == "error"
    assert res["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_payload_limits_large_list(base_portfolio, base_config):
    large_list = [Decimal("0.01")] * 10005
    portfolio = base_portfolio.model_copy(update={"historical_returns": large_list})
    res = build_portfolio_risk_snapshot(
        portfolio, base_config, request_id="large_list_payload"
    )
    assert res["status"] == "error"
    assert res["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_tools_exception_handling(base_portfolio, base_config):
    # Pass invalid inputs to trigger exceptions in each tool and cover except blocks
    res = build_portfolio_risk_snapshot(None, base_config)
    assert res["status"] == "error"

    res = review_trade_risk(None, base_portfolio)
    assert res["status"] == "error"

    res = calculate_position_size(None, base_portfolio, base_config)
    assert res["status"] == "error"

    res = assess_risk_regime(None, base_config)
    assert res["status"] == "error"

    res = review_strategy_admission("strat_1", None)
    assert res["status"] == "error"

    res = review_allocation_proposal(None, base_portfolio, base_config)
    assert res["status"] == "error"

    res = create_risk_decision_package("dec_1", "invalid_status", "rule", "reason")
    assert res["status"] == "error"

    res = validate_risk_approval_token(None, {})
    assert res["status"] == "error"

    res = run_risk_scenario_analysis(
        None, [StressScenario(name="USD Shock")], base_config
    )
    assert res["status"] == "error"

    res = generate_risk_report(None)
    assert res["status"] == "error"


def test_tools_dict_inputs(base_portfolio, base_config):
    # Test that dict inputs are correctly parsed in tool wrapper functions
    portfolio_dict = base_portfolio.model_dump()
    config_dict = base_config

    # 1. build_portfolio_risk_snapshot
    res = build_portfolio_risk_snapshot(portfolio_dict, config_dict)
    assert res["status"] == "success"

    # 2. review_trade_risk
    trade_dict = {
        "strategy_id": "strat_1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1,
    }
    res = review_trade_risk(trade_dict, portfolio_dict, risk_config=config_dict)
    assert res["status"] == "success"

    # 3. calculate_position_size
    req_dict = {
        "symbol": "EURUSD",
        "method": "fixed_risk",
        "risk_percent": 1.0,
        "stop_loss_pips": 20.0,
    }
    res = calculate_position_size(req_dict, portfolio_dict, config_dict)
    assert res["status"] == "success"

    # 4. assess_risk_regime
    res = assess_risk_regime(portfolio_dict, config_dict)
    assert res["status"] == "success"

    # 5. review_allocation_proposal
    proposal_dict = {
        "allocations": {"strat_A": 2000, "strat_B": 2000},
        "as_of": datetime.now(UTC).isoformat(),
    }
    res = review_allocation_proposal(proposal_dict, portfolio_dict, config_dict)
    assert res["status"] == "success"

    # 6. validate_risk_approval_token
    token_dict = {
        "token_id": "tok_1",
        "request_id": "req_1",
        "workflow_id": "wf_1",
        "approved_action": "execute_trade",
        "approver": "admin",
        "expiry_time": (
            datetime.now(UTC) + pytest.importorskip("datetime").timedelta(hours=1)
        ).isoformat(),
        "config_hash": "hash_1",
        "decision_hash": "dec_hash",
        "scope": {"symbol": "EURUSD"},
        "nonce": "nonce_123",
        "signature": "sig",
    }
    res = validate_risk_approval_token(token_dict, {"symbol": "EURUSD"})
    assert res["status"] == "success"

    # 7. run_risk_scenario_analysis
    scenarios_list = [{"name": "USD Shock", "price_shocks": {"EURUSD": 0.02}}]
    res = run_risk_scenario_analysis(portfolio_dict, scenarios_list, config_dict)
    assert res["status"] == "success"

    # 8. generate_risk_report
    decision_dict = {
        "decision_id": "dec_1",
        "request_id": "req_1",
        "workflow_id": "wf_1",
        "status": "approve",
        "rule_key": "rule_ok",
        "snapshot_as_of": datetime.now(UTC).isoformat(),
        "config_hash": "hash_1",
        "reason": "No breaches",
    }
    res = generate_risk_report(decision_dict)
    assert res["status"] == "success"
