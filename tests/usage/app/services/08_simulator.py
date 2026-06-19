# ruff: noqa: E402
"""Executable simulator service examples."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path

project_root = str(Path(__file__).resolve().parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.simulator import (
    DeterministicJournal,
    FixedLiquidityModel,
    FixedSlippageModel,
    FixedSpreadModel,
    MarginModel,
    build_markdown_report,
    run_backtest,
)
from app.utils.standard import validate_standard_response


def _request() -> dict[str, object]:
    """Return a minimal deterministic simulator request."""
    return {
        "request_id": "req_usage_08",
        "actor_context": {"actor_id": "usage-runner", "roles": ["researcher"]},
        "strategy_ref": "trend_following",
        "strategy_config": {"short_window": 5, "long_window": 10},
        "symbols": ["EURUSD"],
        "timeframe": "M1",
        "start": "2026-01-01T00:00:00Z",
        "end": "2026-01-01T01:00:00Z",
        "initial_balance": 100000.0,
    }


def _mapping(value: object) -> Mapping[str, object]:
    """Return a narrowed mapping for usage assertions."""
    assert isinstance(value, Mapping)
    return value


def _data(response: Mapping[str, object]) -> Mapping[str, object]:
    """Return a narrowed response data mapping for usage assertions."""
    return _mapping(response["data"])


def example_01_run_backtest() -> None:
    """Demonstrate canonical backtest request and result envelope."""
    response = run_backtest(_request())
    validate_standard_response(response)
    assert response["status"] == "success"
    result = _mapping(_data(response)["result"])
    summary = _mapping(result["summary_metrics"])
    assert summary["total_trades"] == 0.0


def example_02_tick_engine_and_orders() -> None:
    """Demonstrate deterministic tick construction and IOC diagnostics."""
    tick = FixedSpreadModel(spread_points=10).build_tick(
        timestamp="2026-01-01T00:00:00Z",
        symbol="EURUSD",
        mid_price=1.1,
    )
    liquidity = FixedLiquidityModel(max_volume_per_tick=0.5).fill(
        1.0, time_in_force="IOC"
    )
    assert tick.ask > tick.bid
    assert liquidity.diagnostic_code == "SIM_IOC_REMAINDER_CANCELLED"


def example_03_execution_costs_and_slippage() -> None:
    """Demonstrate slippage and margin calculations."""
    slippage = FixedSlippageModel(slippage_points=1).apply(
        side="buy",
        expected_price=1.1,
        executable_price=1.10005,
        filled_volume=1.0,
    )
    margin = MarginModel(leverage=100).calculate(
        contract_size=100000,
        volume=1.0,
        price=1.1,
    )
    assert slippage.final_price == 1.10006
    assert margin == 1100.0


def example_04_positions_and_accounting() -> None:
    """Demonstrate 08A accounting placeholder metrics."""
    response = run_backtest(_request())
    result = _mapping(_data(response)["result"])
    summary = _mapping(result["summary_metrics"])
    assert summary["ending_balance"] == 100000.0


def example_05_journal_and_event_log() -> None:
    """Demonstrate deterministic journal event logs."""
    journal = DeterministicJournal(
        run_id="simrun_usage",
        config_hash="id_config",
        data_manifest_hash="id_data",
        engine_version="usage",
    )
    record = journal.append("simulator.example", {"status": "success"})
    assert record.sequence == 1
    assert journal.manifest().last_sequence == 1


def example_06_strategy_adapter() -> None:
    """Demonstrate blocked arbitrary strategy code."""
    request = _request()
    request["strategy_config"] = {"source": "def run(): return 1"}
    response = run_backtest(request)
    assert response["status"] == "error"
    assert response["error"] == {
        "code": "SIM_ARBITRARY_CODE_REJECTED",
        "details": "Raw arbitrary Python strategy code is not accepted.",
    }


def example_07_metrics_and_reports() -> None:
    """Demonstrate summary metrics and Markdown reports."""
    response = run_backtest(_request())
    response_data = _data(response)
    markdown = build_markdown_report(dict(response_data))
    assert "Simulator Report" in markdown


def example_08_resume_cancel_and_resource_limits() -> None:
    """Demonstrate queue, cancellation, and fail-closed invalid input paths."""
    queued_request = _request()
    queued_request["metadata"] = {"service_mode": True, "workers_saturated": True}
    queued = run_backtest(queued_request)
    assert queued["status"] == "success"
    assert _data(queued)["status"] == "queued"

    cancelled_request = _request()
    cancelled_request["metadata"] = {"cancel_requested": True}
    cancelled = run_backtest(cancelled_request)
    assert cancelled["status"] == "success"
    assert _data(cancelled)["status"] == "cancelled"

    invalid_request = _request()
    invalid_request["start"] = "2026-01-02T00:00:00Z"
    invalid_request["end"] = "2026-01-01T00:00:00Z"
    invalid = run_backtest(invalid_request)
    assert invalid["status"] == "error"
    assert invalid["error"] is not None


def main() -> None:
    """Run all simulator examples."""
    example_01_run_backtest()
    example_02_tick_engine_and_orders()
    example_03_execution_costs_and_slippage()
    example_04_positions_and_accounting()
    example_05_journal_and_event_log()
    example_06_strategy_adapter()
    example_07_metrics_and_reports()
    example_08_resume_cancel_and_resource_limits()


if __name__ == "__main__":
    main()
