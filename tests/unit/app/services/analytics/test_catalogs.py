"""Tests for analytics catalogs and schema support models."""

from __future__ import annotations

from pathlib import Path
from typing import get_origin

import app
import pytest
from app.services import analytics
from app.services.analytics.adapters import (
    BacktestResult,
    LiveTradingResult,
    PaperTradingResult,
    TradingResult,
)
from app.services.analytics.models import (
    METRIC_DEFINITION_CATALOG,
    OFFICIAL_ANALYTICS_TOOL_CATALOG,
    SCHEMA_COMPATIBILITY_MATRIX,
    AnalyticsConfig,
    AnalyticsMetadata,
    AnalyticsRequest,
    AnalyticsResult,
    MetricDefinition,
    validate_metric_catalog,
)
from app.services.analytics.report import AnalyticsReport, PortfolioAnalyticsReport
from app.services.analytics.scorecard import ScorecardResult, ScorecardRule
from app.utils.errors import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[5]


def test_metric_catalog_validation_success() -> None:
    result = validate_metric_catalog()

    assert result["status"] == "valid"
    assert result["metric_count"] == len(METRIC_DEFINITION_CATALOG)
    assert "r_multiple_proxy_profit_loss" in result["metrics"]


def test_metric_catalog_validation_rejects_malformed_definition() -> None:
    bad_catalog = {
        "bad": MetricDefinition(
            name="different",
            formula="x",
            units="ratio",
            required_inputs=("x",),
        )
    }

    with pytest.raises(ValidationError):
        validate_metric_catalog(bad_catalog)


def test_official_tool_catalog_documents_agent_safe_read_only_tools() -> None:
    entry = OFFICIAL_ANALYTICS_TOOL_CATALOG["build_analytics_report"]

    assert entry.agent_api_safe is True
    assert entry.stability == "stable"
    assert "read-only" in entry.side_effects
    assert "tests/unit/app/services/analytics/test_report.py" in entry.tests


def test_schema_matrix_and_support_models_are_json_safe() -> None:
    request = AnalyticsRequest(
        payload={"result_id": "run_1"},
        config=AnalyticsConfig(max_dashboard_points=100),
        metadata=AnalyticsMetadata(request_id="req_1"),
    )
    result = AnalyticsResult(
        status="partial",
        data={"report_id": "rep_1"},
        warnings=[{"code": "LOW_SAMPLE_SIZE"}],
    )

    assert request.config.max_dashboard_points == 100
    assert result.metadata.schema_version == "1.3.1"
    assert SCHEMA_COMPATIBILITY_MATRIX["1.3.1"] == "accepted"


def test_scorecard_records_are_non_binding() -> None:
    rule = ScorecardRule(
        metric_name="profit_factor",
        threshold=1.5,
        direction="gte",
        warning_code="LOW_PROFIT_FACTOR",
    )
    result = ScorecardResult(score=75.0)

    assert rule.metric_name == "profit_factor"
    assert result.is_binding_decision is False


def test_public_facade_and_root_exports() -> None:
    assert get_origin(analytics.MetricDefinitionCatalog) is dict
    assert analytics.validate_metric_catalog()["status"] == "valid"
    assert get_origin(app.MetricDefinitionCatalog) is dict
    assert (
        app.total_return(
            [
                {"timestamp": "2026-01-01T00:00:00Z", "equity": 100.0},
                {"timestamp": "2026-01-02T00:00:00Z", "equity": 110.0},
            ]
        )
        == 10.0
    )
    assert (
        app.return_on_initial_capital(
            [
                {"timestamp": "2026-01-01T00:00:00Z", "equity": 100.0},
                {"timestamp": "2026-01-02T00:00:00Z", "equity": 110.0},
            ]
        )
        == 10.0
    )


def test_adapter_type_aliases_are_canonical_dicts() -> None:
    assert get_origin(TradingResult) is dict
    assert get_origin(BacktestResult) is dict
    assert get_origin(PaperTradingResult) is dict
    assert get_origin(LiveTradingResult) is dict


def test_return_and_benchmark_helper_exports() -> None:
    equity_curve = [
        {"timestamp": "2026-01-01T00:00:00Z", "equity": 100.0},
        {"timestamp": "2026-02-01T00:00:00Z", "equity": 110.0},
        {"timestamp": "2026-03-01T00:00:00Z", "equity": 121.0},
    ]
    returns = [0.02, -0.01, 0.03]

    assert analytics.buy_and_hold_return([100.0, 121.0]) == 21.0
    assert analytics.cagr(100.0, 121.0, 2.0) == pytest.approx(10.0)
    assert analytics.compound_monthly_growth_rate(100.0, 121.0, 2.0) == pytest.approx(
        10.0
    )
    assert analytics.buy_and_hold_cagr([100.0, 121.0], 2.0) == pytest.approx(10.0)
    assert analytics.avg_monthly_return(equity_curve) == pytest.approx(10.0)
    assert analytics.monthly_return_stddev(equity_curve) >= 0.0
    assert analytics.annualized_return(returns) != 0.0
    assert analytics.geometric_mean_return(returns) != 0.0
    assert analytics.best_return(returns) == 0.03
    assert analytics.worst_return(returns) == -0.01
    assert analytics.return_volatility(returns) > 0.0
    assert analytics.downside_return_volatility(returns) == 0.0
    assert analytics.return_skewness(returns) != 0.0
    assert analytics.return_kurtosis([0.01, 0.02, -0.01, 0.03]) != 0.0

    capture = analytics.up_down_capture([0.02, -0.01], [0.01, -0.02])
    assert capture["up_capture"] == 2.0
    assert capture["down_capture"] == 0.5
    assert analytics.metrics_r_multiple_distribution([1.0, 2.0])["mean"] == 1.5


def test_report_schema_wrappers() -> None:
    report = AnalyticsReport(
        report_id="rep_1",
        report_status="partial",
        sections={"trade_metrics": {"status": "completed"}},
    )
    portfolio = PortfolioAnalyticsReport(
        portfolio_run_id="port_1",
        account_base_currency="USD",
        component_count=1,
        aggregate_metrics={"total_return_percent": 1.0},
    )

    assert report.report_status == "partial"
    assert portfolio.account_base_currency == "USD"


def test_analytics_read_only_boundary_has_no_forbidden_runtime_imports() -> None:
    analytics_dir = PROJECT_ROOT / "app" / "services" / "analytics"
    forbidden_tokens = (
        "MetaTrader5",
        "requests.",
        "sqlite3",
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "order_send",
        "history_deals_get",
    )

    for source_file in analytics_dir.glob("*.py"):
        source_text = source_file.read_text(encoding="utf-8")
        assert not any(token in source_text for token in forbidden_tokens)


def test_required_analytics_adrs_are_present() -> None:
    public_surface = PROJECT_ROOT / "docs" / "adr" / "ADR-ANALYTICS-PUBLIC-SURFACE.md"
    limits = PROJECT_ROOT / "docs" / "adr" / "ADR-ANALYTICS-LIMITS.md"

    assert public_surface.exists()
    assert "Status: Approved" in public_surface.read_text(encoding="utf-8")
    assert limits.exists()
    assert "Maximum trades per request" in limits.read_text(encoding="utf-8")
