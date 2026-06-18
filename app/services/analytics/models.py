"""Analytics catalog and schema support models.

This module defines the small, read-only catalog records used by the Analytics
service to classify official tools, metric definitions, and schema behavior.
It performs no I/O, network calls, database mutations, broker calls, or trading
side effects on import.

Exports:
    AnalyticsMetadata, AnalyticsConfig, AnalyticsRequest, AnalyticsResult,
    MetricDefinition, ToolDefinition, MetricDefinitionCatalog,
    OFFICIAL_ANALYTICS_TOOL_CATALOG, METRIC_DEFINITION_CATALOG,
    SCHEMA_COMPATIBILITY_MATRIX, validate_metric_catalog.

Side effects:
    None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.utils.errors import ValidationError

CapabilityStability = Literal[
    "stable",
    "approved_experimental",
    "deprecated",
    "internal_support_only",
]
MetricRole = Literal[
    "calculated_fact",
    "diagnostic_estimate",
    "warning_evidence",
    "scorecard_input",
    "non_binding_review_context",
]
SchemaStatus = Literal[
    "accepted",
    "deprecated",
    "legacy_adapted",
    "rejected",
    "unsupported_future",
]


@dataclass(frozen=True, slots=True)
class AnalyticsMetadata:
    """Trace and reproducibility metadata for analytics payloads.

    Args:
        request_id: Optional request trace identifier.
        workflow_id: Optional workflow trace identifier.
        schema_version: Version of the analytics schema.
        analytics_engine_version: Version of the analytics engine.
        source_context: Source lineage or run context.

    Side effects:
        None.
    """

    request_id: str | None = None
    workflow_id: str | None = None
    schema_version: str = "1.3.1"
    analytics_engine_version: str = "1.0.0"
    source_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AnalyticsConfig:
    """Deterministic analytics configuration.

    Args:
        annualization_periods: Period count used for annualized ratios.
        breakeven_epsilon: Absolute PnL tolerance for breakeven classification.
        monetary_precision_mode: Monetary precision mode used in reports.
        derived_ratio_tolerance: Deterministic tolerance for float ratios.
        max_dashboard_points: Maximum points returned in dashboard series.

    Side effects:
        None.
    """

    annualization_periods: int = 252
    breakeven_epsilon: float = 1e-9
    monetary_precision_mode: str = "float64_with_tolerance"
    derived_ratio_tolerance: float = 1e-9
    max_dashboard_points: int = 500


@dataclass(frozen=True, slots=True)
class AnalyticsRequest:
    """Canonical analytics request wrapper.

    Args:
        payload: Input payload to analyze.
        config: Deterministic analytics configuration.
        metadata: Trace and reproducibility metadata.

    Side effects:
        None.
    """

    payload: dict[str, Any]
    config: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    metadata: AnalyticsMetadata = field(default_factory=AnalyticsMetadata)


@dataclass(frozen=True, slots=True)
class AnalyticsResult:
    """Canonical analytics result wrapper.

    Args:
        status: Result status string.
        data: JSON-safe analytics payload.
        warnings: Warning objects emitted while calculating the result.
        quality_flags: Quality flags emitted while calculating the result.
        metadata: Trace and reproducibility metadata.

    Side effects:
        None.
    """

    status: Literal["completed", "partial", "failed"]
    data: dict[str, Any]
    warnings: list[dict[str, Any]] = field(default_factory=list)
    quality_flags: list[dict[str, Any]] = field(default_factory=list)
    metadata: AnalyticsMetadata = field(default_factory=AnalyticsMetadata)


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """Approved definition for a metric exposed by analytics.

    Args:
        name: Stable metric name.
        formula: Human-readable formula.
        units: Metric units.
        required_inputs: Required input field names.
        optional_inputs: Optional input field names.
        accepted_aliases: Accepted source aliases.
        return_scale: Return scale such as fraction, percent, or currency.
        annualization_basis: Annualization basis or ``None``.
        sample_convention: Sample or population convention.
        minimum_sample_size: Minimum sample size before the metric is reliable.
        undefined_behavior: How undefined values are represented.
        golden_fixture: Expected fixture behavior for regression tests.
        role: How the metric may be used by reports and scorecards.
        confidence: Confidence label for derived or proxy metrics.

    Side effects:
        None.
    """

    name: str
    formula: str
    units: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...] = ()
    accepted_aliases: tuple[str, ...] = ()
    return_scale: str = "scalar"
    annualization_basis: str | None = None
    sample_convention: str = "sample"
    minimum_sample_size: int = 1
    undefined_behavior: str = "return None and emit warning metadata"
    golden_fixture: str = "covered by analytics unit tests"
    role: MetricRole = "calculated_fact"
    confidence: Literal["normal", "degraded"] = "normal"


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Public analytics tool catalog entry.

    Args:
        name: Stable public tool name.
        input_schema: Human-readable input schema summary.
        output_schema: Human-readable output schema summary.
        errors: Stable error codes used by the tool.
        side_effects: Side-effect summary.
        stability: Stability classification.
        agent_api_safe: Whether the tool is safe for agent/API use.
        tests: Test files or usage scripts covering the tool.

    Side effects:
        None.
    """

    name: str
    input_schema: str
    output_schema: str
    errors: tuple[str, ...]
    side_effects: str
    stability: CapabilityStability
    agent_api_safe: bool
    tests: tuple[str, ...]


MetricDefinitionCatalog = dict[str, MetricDefinition]

METRIC_DEFINITION_CATALOG: MetricDefinitionCatalog = {
    "total_return": MetricDefinition(
        name="total_return",
        formula="((ending_equity - initial_equity) / initial_equity) * 100",
        units="percent",
        required_inputs=("equity_curve",),
        accepted_aliases=("return_on_initial_capital",),
        return_scale="percent",
        undefined_behavior="return 0.0 when initial equity is missing or zero",
    ),
    "return_on_initial_capital": MetricDefinition(
        name="return_on_initial_capital",
        formula="(net_profit / initial_capital) * 100",
        units="percent",
        required_inputs=("equity_curve",),
        accepted_aliases=("total_return",),
        return_scale="percent",
        undefined_behavior="return 0.0 when initial capital is missing or zero",
    ),
    "r_multiple": MetricDefinition(
        name="r_multiple",
        formula="net_pnl / initial_risk",
        units="R",
        required_inputs=("net_pnl", "initial_risk"),
        optional_inputs=("profit_loss", "risk"),
        accepted_aliases=("r_multiples", "get_r_multiples"),
        return_scale="R",
        undefined_behavior="skip values without non-zero risk",
        golden_fixture="100 profit over 50 risk equals 2R",
    ),
    "r_multiple_proxy_profit_loss": MetricDefinition(
        name="r_multiple_proxy_profit_loss",
        formula="profit_loss / 1.0 when explicit risk is unavailable",
        units="R proxy",
        required_inputs=("profit_loss",),
        return_scale="R",
        undefined_behavior="emit degraded confidence warning metadata",
        role="diagnostic_estimate",
        confidence="degraded",
    ),
    "win_rate": MetricDefinition(
        name="win_rate",
        formula="winning_closed_trades / closed_trades",
        units="fraction",
        required_inputs=("closed_trades",),
        accepted_aliases=("win_rate_fraction",),
        return_scale="fraction",
        undefined_behavior="return 0.0 when no closed trades exist",
    ),
    "profit_factor": MetricDefinition(
        name="profit_factor",
        formula="gross_profit / abs(gross_loss)",
        units="ratio",
        required_inputs=("closed_trades",),
        return_scale="ratio",
        undefined_behavior="return 0.0 for no trades and capped sentinel for no losses",
        role="scorecard_input",
    ),
    "max_drawdown": MetricDefinition(
        name="max_drawdown",
        formula="max peak-to-valley decline",
        units="currency or fraction by function",
        required_inputs=("equity_curve",),
        return_scale="scalar",
        undefined_behavior="return 0.0 when no drawdown exists",
        role="scorecard_input",
    ),
    "sharpe_ratio": MetricDefinition(
        name="sharpe_ratio",
        formula="mean(excess_returns) / std(excess_returns)",
        units="ratio",
        required_inputs=("returns",),
        return_scale="ratio",
        annualization_basis="configured periods",
        minimum_sample_size=2,
        undefined_behavior="return 0.0 for insufficient variance or sample size",
        role="scorecard_input",
    ),
}

OFFICIAL_ANALYTICS_TOOL_CATALOG: dict[str, ToolDefinition] = {
    "build_analytics_report": ToolDefinition(
        name="build_analytics_report",
        input_schema="TradingResult dictionary with trades and equity_curve.",
        output_schema="StandardResponse containing versioned AnalyticsReport data.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="stable",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_report.py",),
    ),
    "build_portfolio_analytics_report": ToolDefinition(
        name="build_portfolio_analytics_report",
        input_schema="Portfolio result dictionary with component_results.",
        output_schema="StandardResponse containing portfolio analytics summary.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="approved_experimental",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_report.py",),
    ),
    "evaluate_strategy_quality": ToolDefinition(
        name="evaluate_strategy_quality",
        input_schema="Analytics report dictionary.",
        output_schema="StandardResponse containing non-binding scorecard context.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="stable",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_scorecard.py",),
    ),
    "calculate_trade_metrics": ToolDefinition(
        name="calculate_trade_metrics",
        input_schema="List/dataframe-like collection of trade records.",
        output_schema="StandardResponse containing aggregate trade metrics.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="stable",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_metrics.py",),
    ),
    "calculate_equity_metrics": ToolDefinition(
        name="calculate_equity_metrics",
        input_schema="List/dataframe-like equity curve.",
        output_schema="StandardResponse containing equity and return metrics.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="stable",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_metrics.py",),
    ),
    "calculate_drawdown_metrics": ToolDefinition(
        name="calculate_drawdown_metrics",
        input_schema="List/dataframe-like equity curve.",
        output_schema="StandardResponse containing drawdown metrics.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="stable",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_metrics.py",),
    ),
    "calculate_risk_metrics": ToolDefinition(
        name="calculate_risk_metrics",
        input_schema="Numeric return series.",
        output_schema="StandardResponse containing risk metrics.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="stable",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_metrics.py",),
    ),
    "calculate_benchmark_metrics": ToolDefinition(
        name="calculate_benchmark_metrics",
        input_schema="Strategy and benchmark return series.",
        output_schema="StandardResponse containing aligned benchmark metrics.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="stable",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_metrics.py",),
    ),
    "calculate_statistical_validation": ToolDefinition(
        name="calculate_statistical_validation",
        input_schema="Numeric return series.",
        output_schema="StandardResponse containing statistical validation data.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; deterministic when seeded lower-level helpers are used",
        stability="stable",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_report.py",),
    ),
    "calculate_prop_firm_compliance": ToolDefinition(
        name="calculate_prop_firm_compliance",
        input_schema="Analytics report dictionary.",
        output_schema="StandardResponse containing non-binding compliance context.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="approved_experimental",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_report.py",),
    ),
    "build_overview_payload": ToolDefinition(
        name="build_overview_payload",
        input_schema="Validated AnalyticsReport dictionary.",
        output_schema="StandardResponse containing dashboard-ready overview payload.",
        errors=("VALIDATION_FAILED", "TOOL_EXECUTION_FAILED"),
        side_effects="read-only; no writes, trades, database mutations, or network",
        stability="stable",
        agent_api_safe=True,
        tests=("tests/unit/app/services/analytics/test_metrics.py",),
    ),
}

SCHEMA_COMPATIBILITY_MATRIX: dict[str, SchemaStatus] = {
    "1.0.0": "legacy_adapted",
    "1.1.0": "legacy_adapted",
    "1.2.0": "deprecated",
    "1.3.1": "accepted",
    "2.0.0": "unsupported_future",
}

WARNING_SEVERITY_LEVELS = (
    "informational",
    "warning",
    "major",
    "critical",
    "blocker",
)


def validate_metric_catalog(
    catalog: MetricDefinitionCatalog | None = None,
) -> dict[str, Any]:
    """Validate that metric catalog entries are complete and unique.

    Args:
        catalog: Optional catalog to validate. Defaults to
            ``METRIC_DEFINITION_CATALOG``.

    Returns:
        JSON-safe validation summary.

    Raises:
        ValidationError: If a catalog entry is malformed.

    Side effects:
        None.
    """
    active_catalog = METRIC_DEFINITION_CATALOG if catalog is None else catalog
    if not isinstance(active_catalog, dict) or not active_catalog:
        raise ValidationError("metric catalog must be a non-empty dictionary.")

    names: set[str] = set()
    for key, definition in active_catalog.items():
        if key in names:
            raise ValidationError(f"duplicate metric definition: {key}")
        names.add(key)
        if not isinstance(definition, MetricDefinition):
            raise ValidationError(f"metric definition for {key} is invalid.")
        if key != definition.name:
            raise ValidationError(f"metric catalog key mismatch for {key}.")
        if not definition.formula.strip():
            raise ValidationError(f"metric {key} must define a formula.")
        if not definition.required_inputs:
            raise ValidationError(f"metric {key} must define required inputs.")
        if definition.minimum_sample_size < 0:
            raise ValidationError(
                f"metric {key} must not use a negative minimum sample size."
            )

    return {
        "status": "valid",
        "metric_count": len(active_catalog),
        "metrics": sorted(active_catalog),
    }


# Compatibility aliases named by the implementation plan.
Request = AnalyticsRequest
Result = AnalyticsResult
Config = AnalyticsConfig
Metadata = AnalyticsMetadata
