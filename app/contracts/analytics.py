"""Analytics contracts module.

Defines PerformanceScorecard and AnalyticsReport.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.contracts.base import Contract


class PerformanceScorecard(Contract):
    """Canonical performance evaluation scorecard metrics."""

    total_trades: int = Field(..., ge=0, description="Total executed trades count.")
    win_rate: float = Field(..., ge=0.0, le=1.0, description="Ratio of winning trades.")
    profit_factor: float = Field(
        ..., ge=0.0, description="Gross profit divided by gross loss."
    )
    sharpe_ratio: float = Field(..., description="Annualized Sharpe ratio coefficient.")
    sortino_ratio: float = Field(
        ..., description="Annualized Sortino ratio coefficient."
    )
    max_drawdown: float = Field(
        ..., description="Maximum drawdown percentage recorded."
    )
    max_drawdown_duration: int = Field(
        ..., ge=0, description="Maximum drawdown duration in seconds."
    )
    cagr: float = Field(..., description="Compound annual growth rate.")
    metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Raw dictionary of auxiliary performance ratio stats.",
    )


class AnalyticsReport(Contract):
    """Canonical structure representing a compiled analytics report."""

    report_id: str = Field(..., description="Unique report ID.")
    scorecard: PerformanceScorecard = Field(
        ..., description="Performance scorecard values."
    )
    run_references: list[str] = Field(
        default_factory=list,
        description="References to backtest or live session runs included.",
    )
    chart_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Data configurations for charts (drawdown, equity).",
    )
