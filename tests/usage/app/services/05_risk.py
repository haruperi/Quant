# ruff: noqa: E501, E402
"""Usage example script for app/services/risk.

Demonstrates typical workflows using the official risk AI tools.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[4])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from app.services.risk import (
    PortfolioState,
    PositionSizingRequest,
    ProposedTrade,
    RiskApprovalToken,
    StressScenario,
    build_portfolio_risk_snapshot,
    calculate_position_size,
    check_risk_kill_switch,
    generate_risk_report,
    review_trade_risk,
    run_risk_scenario_analysis,
    validate_risk_approval_token,
)


def run_examples() -> None:
    """Execute risk service usage examples."""
    print("=== STARTING RISK SERVICE USAGE EXAMPLES ===")

    # 1. Setup sample configuration and portfolio state
    config = {
        "profile_name": "prop_firm_default",
        "config_version": "1.0.0",
        "config_hash": "cfg_hash_xyz",
        "max_daily_loss_pct": Decimal("0.05"),
        "max_total_loss_pct": Decimal("0.10"),
    }

    portfolio = PortfolioState(
        account_id="account-001",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        positions=[],
        orders=[],
        strategy_allocations={"mean-reversion-v1": Decimal("5000.00")},
        historical_returns=[Decimal("0.01"), Decimal("-0.002"), Decimal("0.005")],
        as_of=datetime.now(UTC),
    )

    # Example 1: Build Snapshot & Sizing
    print("\n--- Example 1: Portfolio Risk Snapshot & Position Sizing ---")

    snapshot_response = cast(
        "Any",
        build_portfolio_risk_snapshot(
            portfolio_state=portfolio,
            risk_config=config,
            request_id="req-risk-001",
        ),
    )
    print(f"Snapshot status: {snapshot_response['status']}")
    print(f"Snapshot message: {snapshot_response['message']}")

    sizing_request = PositionSizingRequest(
        symbol="EURUSD",
        method="fixed_risk",
        risk_percent=Decimal("1.0"),
        stop_loss_pips=Decimal("30.0"),
    )
    sizing_response = cast(
        "Any",
        calculate_position_size(
            sizing_request=sizing_request,
            portfolio_state=portfolio,
            risk_config=config,
            request_id="req-risk-002",
        ),
    )
    print(f"Sizing status: {sizing_response['status']}")
    print(f"Calculated Volume: {sizing_response['data']['calculated_volume']} lots")

    # Example 2: Review Trade Risk & Validate Token
    print("\n--- Example 2: Trade Risk Review & Token Validation ---")

    proposed_trade = ProposedTrade(
        strategy_id="mean-reversion-v1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.10"),
        requires_live_execution=False,
    )

    decision_response = cast(
        "Any",
        review_trade_risk(
            proposed_trade=proposed_trade,
            portfolio_state=portfolio,
            risk_config=config,
            request_id="req-risk-003",
        ),
    )
    print(f"Decision status: {decision_response['status']}")
    print(f"Decision result: {decision_response['data']['status'].upper()}")
    print(f"Decision explanation: {decision_response['data']['reason']}")

    # Check kill switch
    kill_switch_res = cast(
        "Any",
        check_risk_kill_switch(
            scope={"account_id": "account-001", "strategy_id": "mean-reversion-v1"},
            request_id="req-risk-004",
        ),
    )
    print(f"Kill switch status: {kill_switch_res['status']}")
    print(f"Kill switch active: {kill_switch_res['data']['kill_switch_active']}")

    # Validate approval token
    approval_token = RiskApprovalToken(
        token_id="tok-001",
        request_id="req-risk-003",
        workflow_id="wf-001",
        approved_action="execute_trade",
        approver="risk_manager_1",
        expiry_time=datetime.now(UTC) + timedelta(hours=1),
        config_hash="cfg_hash_xyz",
        decision_hash="dec_hash_xyz",
        scope={"symbol": "EURUSD"},
        nonce="nonce_val",
        signature="sig_val",
    )
    token_response = cast(
        "Any",
        validate_risk_approval_token(
            token=approval_token,
            expected_scope={"symbol": "EURUSD"},
            request_id="req-risk-005",
        ),
    )
    print(f"Token validation: {token_response['status']}")
    print(f"Token valid flag: {token_response['data']['valid']}")

    # Example 3: Scenarios & Reports
    print("\n--- Example 3: Scenario Analysis & Report Generation ---")

    scenarios = [
        StressScenario(name="USD Shock", price_shocks={"EURUSD": Decimal("-0.02")}),
        StressScenario(name="Spread Widening", spread_multiplier=Decimal("3.0")),
    ]

    scenario_response = cast(
        "Any",
        run_risk_scenario_analysis(
            portfolio_state=portfolio,
            scenarios=scenarios,
            risk_config=config,
            request_id="req-risk-006",
        ),
    )
    print(f"Scenario analysis: {scenario_response['status']}")
    print(f"USD Shock stop-out trigger: {scenario_response['data'][0]['is_stop_out']}")
    print(
        f"Spread Widening margin-call trigger: {scenario_response['data'][1]['is_margin_call']}"
    )

    report_response = cast(
        "Any",
        generate_risk_report(
            risk_decision_package=decision_response["data"],
            output_format="markdown",
            request_id="req-risk-007",
        ),
    )
    print(f"Report generation: {report_response['status']}")
    print(f"Report length: {len(report_response['data']['content'])} chars")

    print("\n=== ALL RISK SERVICE USAGE EXAMPLES COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    run_examples()
