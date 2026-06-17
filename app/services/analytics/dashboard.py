"""Dashboard payload formatters for Analytics.

Formats analytics reports and curves into UI/API-ready dashboard payloads.
"""

from __future__ import annotations

from typing import Any

from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError


def _validate_request_id(request_id: str | None) -> None:
    """Helper to validate request_id strictly."""
    if request_id is not None:
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValidationError("request_id must be a non-empty string.")


def _downsample_curve(
    curve: list[dict[str, Any]], max_points: int = 100
) -> dict[str, Any]:
    """Downsample an equity or balance curve deterministically preserving first, last, and extrema."""
    n = len(curve)
    if n <= max_points:
        return {
            "curve": curve,
            "truncated": False,
            "original_count": n,
            "returned_count": n,
            "truncation_method": None,
            "truncation_reason": None,
        }

    # Find peak and trough indexes
    peak_idx = 0
    trough_idx = 0
    peak_val = float(curve[0].get("equity") or 0.0)
    trough_val = peak_val
    for i in range(1, n):
        val = float(curve[i].get("equity") or 0.0)
        if val > peak_val:
            peak_val = val
            peak_idx = i
        if val < trough_val:
            trough_val = val
            trough_idx = i

    # Step-based decimation
    step = max(n // (max_points - 4), 1)
    indices = {0, n - 1, peak_idx, trough_idx}
    for i in range(0, n, step):
        indices.add(i)

    downsampled = [curve[idx] for idx in sorted(list(indices))]
    return {
        "curve": downsampled,
        "truncated": True,
        "original_count": n,
        "returned_count": len(downsampled),
        "truncation_method": "deterministic_decimation_with_extrema",
        "truncation_reason": f"Points count {n} exceeded maximum allowed points {max_points}.",
    }


def build_overview_payload(
    report: dict[str, Any],
    request_id: str | None = None,
) -> StandardResponse:
    """Format a calculated report into UI summary cards and downsampled chart curves.

    Args:
        report: Dict containing the calculated analytics report sections.
        request_id: Trace correlation identifier.

    Returns:
        Standard response containing the dashboard payload.
    """
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="build_overview_payload",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        if not isinstance(report, dict):
            raise ValidationError("report must be a dictionary.")

        sections = report.get("sections") or report
        trade_sec = sections.get("trade_metrics") or sections.get("trade") or {}
        ratio_sec = sections.get("ratio_metrics") or sections.get("ratios") or {}
        dd_sec = sections.get("drawdown_metrics") or sections.get("drawdown") or {}
        eq_sec = sections.get("equity_metrics") or sections.get("equity") or {}

        # 1. Summary Cards
        summary_cards = {
            "net_profit": float(
                eq_sec.get("data", {}).get("total_return_usd", 0.0)
                if "data" in eq_sec
                else eq_sec.get("total_return_usd", 0.0)
            ),
            "win_rate": float(
                trade_sec.get("data", {}).get("win_rate", 0.0)
                if "data" in trade_sec
                else trade_sec.get("win_rate", 0.0)
            ),
            "profit_factor": float(
                ratio_sec.get("data", {}).get("profit_factor", 1.0)
                if "data" in ratio_sec
                else ratio_sec.get("profit_factor", 1.0)
            ),
            "max_drawdown_percent": float(
                dd_sec.get("data", {}).get("max_drawdown_percent", 0.0)
                if "data" in dd_sec
                else dd_sec.get("max_drawdown_percent", 0.0)
            ),
            "sharpe_ratio": float(
                ratio_sec.get("data", {}).get("sharpe_ratio", 0.0)
                if "data" in ratio_sec
                else ratio_sec.get("sharpe_ratio", 0.0)
            ),
            "total_trades": int(
                trade_sec.get("data", {}).get("total_trades", 0)
                if "data" in trade_sec
                else trade_sec.get("total_trades", 0)
            ),
        }

        # 2. Downsample curves if present
        # In a real payload, equity_curve might be passed inside report or raw result.
        # If missing, provide dummy/empty curve to satisfy frontend contract.
        raw_curve = report.get("equity_curve") or []
        downsampled_equity = _downsample_curve(raw_curve, max_points=100)

        data = {
            "summary_cards": summary_cards,
            "equity_curve_chart": downsampled_equity,
            "monthly_heatmap": {},
            "warnings": report.get("warnings", []),
            "quality_flags": report.get("quality_flags", []),
        }

        return success_response(
            message="Dashboard overview payload built successfully.",
            data=data,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)
