# ruff: noqa: E501, E402
"""Usage example script for app/services/analytics.

Demonstrates typical workflows using the official analytics AI tools.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[4])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from typing import Any, cast

from app.services.analytics import (
    bootstrap_probability_above_threshold,
    build_analytics_report,
    build_overview_payload,
    evaluate_strategy_quality,
    profit_factor,
    sample_size_warning,
    total_trades,
    win_rate,
)


def run_examples() -> None:
    """Execute analytics service usage examples."""
    print("=== STARTING ANALYTICS SERVICE USAGE EXAMPLES ===")

    # 1. Setup sample trading results
    trading_result = {
        "schema_version": "1.3.1",
        "result_id": "bt_run_example_06",
        "phase": "backtest",
        "strategy_id": "strategy_trend_follower",
        "strategy_version": "v1.2",
        "account_base_currency": "USD",
        "start_time": "2026-01-01T00:00:00Z",
        "end_time": "2026-01-31T23:59:59Z",
        "symbols": ["EURUSD"],
        "timeframe": "H1",
        "trades": [
            {
                "trade_id": "t1",
                "symbol": "EURUSD",
                "direction": "long",
                "open_time": "2026-01-02T00:00:00Z",
                "close_time": "2026-01-02T04:00:00Z",
                "net_pnl": 150.0,
                "initial_risk": 50.0,
                "mae": -10.0,
                "mfe": 200.0,
            },
            {
                "trade_id": "t2",
                "symbol": "EURUSD",
                "direction": "short",
                "open_time": "2026-01-03T00:00:00Z",
                "close_time": "2026-01-03T06:00:00Z",
                "net_pnl": -50.0,
                "initial_risk": 50.0,
                "mae": -60.0,
                "mfe": 5.0,
            },
        ],
        "equity_curve": [
            {"timestamp": "2026-01-01T00:00:00Z", "equity": 10000.0},
            {"timestamp": "2026-01-02T04:00:00Z", "equity": 10150.0},
            {"timestamp": "2026-01-03T06:00:00Z", "equity": 10100.0},
        ],
        "benchmark_curve": [
            {"timestamp": "2026-01-01T00:00:00Z", "equity": 10000.0},
            {"timestamp": "2026-01-02T04:00:00Z", "equity": 10050.0},
            {"timestamp": "2026-01-03T06:00:00Z", "equity": 10020.0},
        ],
        "metadata": {"data_quality_status": "passed"},
    }

    # Example 1: Direct metric tool calls
    print("\n--- Example 1: Basic Metric Tool Calls ---")
    trades_list = trading_result["trades"]

    t_count = cast("Any", total_trades(trades_list, request_id="req_an_01"))
    print(f"Total trades status: {t_count['status']}, result: {t_count['data']}")

    w_rate = cast("Any", win_rate(trades_list, request_id="req_an_02"))
    print(f"Win rate status: {w_rate['status']}, result: {w_rate['data']}")

    pf = cast("Any", profit_factor(trades_list, request_id="req_an_03"))
    print(f"Profit factor status: {pf['status']}, result: {pf['data']}")

    # Example 2: Sample size and statistical checks
    print("\n--- Example 2: Sample Size Warning and Bootstrapping ---")

    warning = cast(
        "Any",
        sample_size_warning(
            len(trades_list), min_recommended=10, request_id="req_an_04"
        ),
    )
    print(f"Sample size warning result: {warning['data']}")

    returns = [0.01, -0.005, 0.012, 0.004, -0.003]
    prob = cast(
        "Any",
        bootstrap_probability_above_threshold(
            returns, threshold=0.0, seed=42, request_id="req_an_05"
        ),
    )
    print(f"Probability above threshold (0.0): {prob['data']}")

    # Example 3: Build Report and Evaluate Quality
    print("\n--- Example 3: Full Report Generation & Quality Scorecard ---")

    report_resp = cast(
        "Any", build_analytics_report(trading_result, request_id="req_an_06")
    )
    print(f"Report build status: {report_resp['status']}")

    if report_resp["status"] == "success":
        report = report_resp["data"]
        print(f"Report ID: {report['report_id']}")
        print(f"Report Status: {report['report_status']}")

        # Evaluate quality using scorecard tool
        scorecard_resp = cast(
            "Any", evaluate_strategy_quality(report, request_id="req_an_07")
        )
        print(f"Scorecard evaluation: {scorecard_resp['status']}")

        if scorecard_resp["status"] == "success":
            card = scorecard_resp["data"]
            print(f"Score: {card['score']}")
            print(f"Strengths: {card['strengths']}")
            print(f"Warnings: {card['warnings']}")
            print(f"Recommended Action: {card['recommended_action']}")

        # Format dashboard overview payload
        dashboard_resp = cast(
            "Any", build_overview_payload(report, request_id="req_an_08")
        )
        print(f"Dashboard formatting status: {dashboard_resp['status']}")
        if dashboard_resp["status"] == "success":
            db_data = dashboard_resp["data"]
            print(f"Dashboard summary cards: {db_data['summary_cards']}")
            print(
                f"Equity chart points returned: {db_data['equity_curve_chart']['returned_count']}"
            )

    print("\n=== ALL ANALYTICS SERVICE USAGE EXAMPLES COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    run_examples()
