"""Downstream integration layer with the Analytics Service.

Maps simulator trades and equity curves to standard analytics scorecard inputs.
"""

from __future__ import annotations

from typing import Any, cast

from app.services.analytics import build_analytics_report


def build_scorecard_from_simulator_result(
    trades: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
    run_id: str,
    phase: str = "simulation",
    schema_version: str = "1.0.0",
) -> dict[str, Any]:
    """Map simulator trades and equity curve to a standard analytics scorecard.

    Args:
        trades: List of reconstructed closed trades.
        equity_curve: List of recorded equity curve points.
        run_id: Trace execution run identifier.
        phase: Operating phase label.
        schema_version: Version of the results.

    Returns:
        dict[str, Any]: Compiled scorecard metrics or empty dict.
    """
    trading_result = {
        "schema_version": schema_version,
        "result_id": run_id,
        "phase": phase,
        "trades": trades,
        "equity_curve": equity_curve,
    }
    response = build_analytics_report(trading_result)
    if response.get("status") == "success" and isinstance(response.get("data"), dict):
        return cast("dict[str, Any]", response["data"])
    return {}
