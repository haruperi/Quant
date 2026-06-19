"""Unit tests for the RiskGovernor reporting and metrics module."""

import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.risk import (
    InMemoryRiskStateStore,
    PortfolioState,
    ProposedTrade,
    RiskAssessmentRequest,
    RiskConfig,
    RiskDecisionStatus,
    RiskGovernor,
)
from app.services.risk.reports import (
    RISK_METRICS_REGISTRY,
    generate_risk_report,
)
from app.utils.errors import ValidationError


def test_generate_report_success():
    """Verify that reports compile correctly from storage without recomputing."""
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    req.request_id = "req_report_test"

    # Make a couple of decisions
    gov.review_trade_risk(req)

    # Generate the report
    report = generate_risk_report(
        state_store=store,
        audit_sink=store,
        decision_store=store,
        request_id="trace_report",
    )

    assert report.report_id.startswith("report")
    assert report.policy_profile == "default"
    assert report.mode == "paper"
    assert len(report.decisions) == 1
    assert report.decisions[0].status == RiskDecisionStatus.APPROVE
    assert report.decisions[0].symbol == "EURUSD"
    assert report.decisions[0].volume == 0.1
    assert report.metadata["risk.request_id"] == "trace_report"


def test_report_file_output_and_traversal_guard():
    """Verify optional file output and path traversal guard safety."""
    store = InMemoryRiskStateStore()

    # Test path traversal guard outside workspace
    with pytest.raises(ValidationError, match="Path traversal detected"):
        generate_risk_report(
            state_store=store,
            audit_sink=store,
            decision_store=store,
            write_to_path="../outside_report.json",
        )

    # Test valid path write
    with tempfile.TemporaryDirectory():
        # We must write inside the workspace (current folder)
        # So we write to a temporary file inside a folder under the project root
        report_file = Path("report_temp_test.json").resolve()
        try:
            report = generate_risk_report(
                state_store=store,
                audit_sink=store,
                decision_store=store,
                write_to_path=str(report_file),
            )
            assert report_file.exists()
            content = report_file.read_text()
            assert report.report_id in content
        finally:
            # Clean up
            if report_file.exists():
                report_file.unlink()


def test_observability_registry_recording():
    """Verify metrics are successfully registered in RISK_METRICS_REGISTRY."""
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    # Clear registry records before check
    RISK_METRICS_REGISTRY.records.clear()

    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    req.request_id = "req_metrics_test"

    gov.review_trade_risk(req)

    # Verify metrics exist
    metric_names = [m["name"] for m in RISK_METRICS_REGISTRY.records]
    assert "haruquant_risk_governor_latency_ms" in metric_names
    assert "haruquant_risk_decision_total" in metric_names
    assert "haruquant_risk_audit_persistence_health" in metric_names
    assert "haruquant_risk_kill_switch_state" in metric_names


def test_report_warnings_and_breaches():
    """Verify that warnings are correctly segregated from breaches in reports."""
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
            "drawdown": 0.09,  # Triggers advisory warning
        },
    )
    req.request_id = "req_warning_test"

    decision = gov.review_trade_risk(req)

    # Check that warning_flags exists in decision details
    assert "warning_flags" in decision.details
    assert "max_drawdown_limit" in decision.details["warning_flags"]

    # Generate report
    report = generate_risk_report(
        state_store=store,
        audit_sink=store,
        decision_store=store,
    )

    assert "max_drawdown_limit" in report.warnings
    assert "max_drawdown_limit" not in report.breaches


def test_report_json_serialization_and_redaction():
    """Verify JSON serialization, Decimal/datetime conversion, and redaction logic."""
    from app.services.risk.reports import RiskDecisionSummary, RiskReport

    dec = RiskDecisionSummary(
        decision_id="dec_1",
        request_id="req_1",
        status="reject",
        rule_key="test_rule",
        reason="Rejected because password=my_secret_pwd was incorrect",
        timestamp=datetime.now(UTC),
        symbol="EURUSD",
        volume=0.5,
    )

    report = RiskReport(
        report_id="report_test",
        generated_at=datetime.now(UTC),
        policy_profile="default",
        config_hash="abc123config_hash_of_64_chars_length_long_enough",
        mode="paper",
        portfolio_exposure=1000.0,
        breaches=[],
        warnings=[],
        decisions=[dec],
        metadata={
            "risk.user_key": (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."  # pragma: allowlist secret
                "eyJzdWIiOiIxMjM0NTY3ODkwIi"  # pragma: allowlist secret
                "wibmFtZSI6IkpvaG4gRG9lIi"  # pragma: allowlist secret
                "wiaWF0IjoxNTE2MjM5MDIyfQ."  # pragma: allowlist secret
                "SflKxwRJSMeKKF2QT4fwpMeJ"  # pragma: allowlist secret
                "f36POk6yJV_adQssw5c"  # pragma: allowlist secret
            ),
            "risk.safe_key": "safe_value",
        },
    )

    json_str = report.to_json()
    assert "[REDACTED]" in json_str
    # Verify metadata JWT is redacted
    assert "eyJhbGci" not in json_str
    # Verify reason password is redacted
    assert "my_secret_pwd" not in json_str
    # Verify config_hash is preserved
    assert "abc123config_hash_of_64_chars_length_long_enough" in json_str


def test_report_no_recompute_and_fallback():
    """Verify report generation does not recompute and falls back to snapshot values."""
    from app.services.risk.models import PortfolioRiskSnapshot

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )

    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={
            "mode": "paper",
            "environment": "local",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
            "max_stress_ratio": 2.0,
        },
    )
    req.request_id = "req_fallback_test"

    decision = gov.review_trade_risk(req)

    # Clear audit events to replace with our modified decision event
    store._audit_events.clear()

    # Manually delete metrics from details to force fallback to risk_snapshot
    if "var" in decision.details:
        del decision.details["var"]
    if "stress_loss" in decision.details:
        del decision.details["stress_loss"]
    if "portfolio_exposure" in decision.details:
        del decision.details["portfolio_exposure"]

    decision.risk_snapshot = PortfolioRiskSnapshot(
        positions=[],
        pending_orders=[],
        in_flight_orders=[],
        exposure=Decimal("9999.0"),
        var_es=Decimal("123.45"),
        stress_loss=Decimal("0.5"),
        drawdown=Decimal("0.0"),
    )
    store.save_decision(decision)

    # Write a new audit event with the modified decision
    from app.services.risk.audit import create_risk_audit_event

    create_risk_audit_event(decision, req.proposed_action, store)

    # Generate report and check fallbacks
    report = generate_risk_report(
        state_store=store,
        audit_sink=store,
        decision_store=store,
    )

    assert report.portfolio_exposure == 9999.0
    assert report.var == 123.45
    assert report.stress_loss == 0.5
