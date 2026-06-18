"""Strategy quality scorecard for Analytics.

Evaluates an analytics report to produce a non-binding scorecard with warnings, strengths, and recommended action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.analytics.models import MetricDefinition, validate_metric_catalog
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError

__all__ = [
    "MetricDefinition",
    "ScorecardResult",
    "ScorecardRule",
    "evaluate_strategy_quality",
    "validate_metric_catalog",
]


@dataclass(frozen=True, slots=True)
class ScorecardRule:
    """Non-binding analytics scorecard rule.

    Args:
        metric_name: Metric Definition Catalog key the rule evaluates.
        threshold: Numeric threshold for the rule.
        direction: Passing direction: ``gte`` or ``lte``.
        warning_code: Stable warning or quality-flag code.
        severity: Warning severity.
        recommendation: Non-binding recommendation text.

    Side effects:
        None.
    """

    metric_name: str
    threshold: float
    direction: str
    warning_code: str
    severity: str = "warning"
    recommendation: str = "Review before promotion."


@dataclass(frozen=True, slots=True)
class ScorecardResult:
    """Non-binding strategy-quality scorecard result.

    Args:
        score: Normalized 0-to-100 quality score.
        strengths: Positive evidence strings.
        warnings: Warning evidence strings.
        recommended_action: Non-binding recommended action.
        is_binding_decision: Always ``False`` for Analytics outputs.
        quality_flags: Structured quality flags.

    Side effects:
        None.
    """

    score: float
    strengths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommended_action: str = "Review before promotion."
    is_binding_decision: bool = False
    quality_flags: list[dict[str, Any]] = field(default_factory=list)


def _validate_request_id(request_id: str | None) -> None:
    """Helper to validate request_id strictly."""
    if request_id is not None:
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValidationError("request_id must be a non-empty string.")


def evaluate_strategy_quality(
    report: dict[str, Any],
    request_id: str | None = None,
) -> StandardResponse:
    """Evaluate a strategy report to provide a non-binding quality score, strengths, and weaknesses.

    Args:
        report: Dict containing the calculated analytics report sections.
        request_id: Trace correlation identifier.

    Returns:
        Standard response containing the quality evaluation decision.
    """
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="evaluate_strategy_quality",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        if not isinstance(report, dict):
            raise ValidationError("report must be a dictionary.")

        # Extract metrics safely from different report structures
        # Report can contain nested sections like 'trade_metrics', 'ratio_metrics', 'drawdown_metrics'
        sections = report.get("sections") or report

        trade_sec = sections.get("trade_metrics") or sections.get("trade") or {}
        ratio_sec = sections.get("ratio_metrics") or sections.get("ratios") or {}
        dd_sec = sections.get("drawdown_metrics") or sections.get("drawdown") or {}

        # Default values
        p_factor = float(ratio_sec.get("profit_factor", 1.0))
        w_rate = float(trade_sec.get("win_rate", 0.5))
        total_tr = int(trade_sec.get("total_trades", 0))
        max_dd = float(dd_sec.get("max_drawdown_percent", 0.0))
        sharpe = float(ratio_sec.get("sharpe_ratio", 0.0))

        score = 100.0
        strengths = []
        warnings = []

        if p_factor >= 1.5:
            strengths.append("Robust profit factor (> 1.5)")
        elif p_factor < 1.2:
            score -= 20.0
            warnings.append("Low profit factor (< 1.2)")

        if w_rate >= 0.55:
            strengths.append("High win rate (> 55%)")
        elif w_rate < 0.45:
            score -= 15.0
            warnings.append("Low win rate (< 45%)")

        if total_tr >= 100:
            strengths.append("Sufficient sample size (> 100 trades)")
        elif total_tr < 50:
            score -= 15.0
            warnings.append(
                "Small sample size (< 50 trades) makes statistics less reliable"
            )

        if max_dd <= 10.0 and max_dd > 0:
            strengths.append("Low maximum drawdown (<= 10%)")
        elif max_dd > 25.0:
            score -= 25.0
            warnings.append("High drawdown (> 25%) risk exposure")

        if sharpe >= 1.5:
            strengths.append("Excellent risk-adjusted returns (Sharpe >= 1.5)")
        elif sharpe < 1.0:
            score -= 15.0
            warnings.append(
                "Sharpe ratio (< 1.0) shows sub-optimal risk-adjusted return"
            )

        # Keep score within [0, 100]
        score = max(min(score, 100.0), 0.0)

        # Recommended action based on score
        if score >= 80:
            rec_action = (
                "Promote to paper trading sandbox for out-of-sample validation."
            )
        elif score >= 50:
            rec_action = "Perform parameter sensitivity checks and adjust sizing down before promotion."
        else:
            rec_action = (
                "Reject. Reject promotion. Review strategy entries/exits/rules."
            )

        data = {
            "score": score,
            "strengths": strengths,
            "warnings": warnings,
            "recommended_action": rec_action,
            "is_binding_decision": False,
            "disclaimer": "This report represents non-binding analytics evidence and decision context only. It does not certify live-readiness or execute orders.",
        }

        return success_response(
            message="Strategy quality scorecard evaluation completed.",
            data=data,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)
