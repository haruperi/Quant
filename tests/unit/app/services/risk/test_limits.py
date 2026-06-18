"""Unit tests for the pre-trade limits engine."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.services.risk import (
    PortfolioState,
    ProposedTrade,
    RiskAssessmentRequest,
    RiskConfig,
    RiskDecisionStatus,
    RiskMode,
    RiskReasonCode,
    RiskSeverity,
    run_limit_checks,
)
from app.services.risk.config import load_risk_config
from app.services.risk.limits import (
    check_daily_loss_limit,
    check_kill_switch_state,
    check_max_drawdown_limit,
    check_portfolio_exposure_limit,
    check_stale_evidence_limit,
)
from app.utils.normalization import utc_now


@pytest.fixture
def base_config() -> RiskConfig:
    """Load default base risk config."""
    return load_risk_config("default")


@pytest.fixture
def normal_portfolio() -> PortfolioState:
    """Provide a normal portfolio state."""
    return PortfolioState(
        account_id="acc-123",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("1000.00"),
        free_margin=Decimal("99000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=utc_now(),
        positions=[],
    )


@pytest.fixture
def base_request(normal_portfolio: PortfolioState) -> RiskAssessmentRequest:
    """Provide a baseline RiskAssessmentRequest."""
    trade = ProposedTrade(
        strategy_id="strategy-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.10"),
    )
    return RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=normal_portfolio,
        risk_config=load_risk_config("default"),
        calendar_evidence=[],
        market_context={
            "kill_switch_active": False,
            "freshness": utc_now(),
            "daily_loss_pct": 0.0,
            "mode": RiskMode.PAPER,
        },
    )


def test_check_kill_switch_state(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test kill switch detection."""
    # Pass path
    res = check_kill_switch_state(base_request, base_config)
    assert not res.breached
    assert res.status == RiskDecisionStatus.APPROVE

    # Fail path
    base_request.market_context["kill_switch_active"] = True
    res_fail = check_kill_switch_state(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.BLOCK
    assert res_fail.reason_code == RiskReasonCode.KILL_SWITCH_ACTIVE


def test_check_stale_evidence_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test snapshot evidence freshness and fail-closed checks."""
    # Pass path
    res = check_stale_evidence_limit(base_request, base_config)
    assert not res.breached

    # Fail path (stale age)
    base_request.market_context["freshness"] = utc_now() - timedelta(seconds=120)
    res_stale = check_stale_evidence_limit(base_request, base_config)
    assert res_stale.breached
    assert res_stale.status == RiskDecisionStatus.REJECT

    # Missing evidence in Live mode -> BLOCK (fail-closed)
    base_request.market_context["mode"] = RiskMode.FULL_LIVE
    del base_request.market_context["freshness"]
    res_missing_live = check_stale_evidence_limit(base_request, base_config)
    assert res_missing_live.status == RiskDecisionStatus.BLOCK
    assert res_missing_live.reason_code == RiskReasonCode.STALE_EVIDENCE


def test_check_max_drawdown_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test max drawdown limit gates (soft vs hard breach)."""
    # config has max_total_loss_pct = 0.10, advisory = 0.08
    # Pass path
    res = check_max_drawdown_limit(base_request, base_config)
    assert not res.breached

    # Warning path (soft breach)
    base_request.market_context["drawdown"] = 0.09
    res_warn = check_max_drawdown_limit(base_request, base_config)
    assert res_warn.breached
    assert res_warn.status == RiskDecisionStatus.APPROVE
    assert res_warn.severity == RiskSeverity.WARNING

    # Fail path (hard block)
    base_request.market_context["drawdown"] = 0.12
    res_fail = check_max_drawdown_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.BLOCK
    assert res_fail.reason_code == RiskReasonCode.DRAWDOWN_BREACH


def test_check_daily_loss_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test daily loss percentage checks."""
    # config has max_daily_loss_pct = 0.05
    # Pass path
    res = check_daily_loss_limit(base_request, base_config)
    assert not res.breached

    # Fail path
    base_request.market_context["daily_loss_pct"] = 0.06
    res_fail = check_daily_loss_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_check_portfolio_exposure_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test total portfolio exposure calculations."""
    base_request.portfolio_state.equity = Decimal("100000.00")
    base_request.market_context["portfolio_gross_exposure"] = 490000.0
    base_request.market_context["max_portfolio_exposure"] = 5.0

    # 490,000 + 0.1 lot (10,000) = 500,000 (exactly 5.0x equity) -> Pass
    res = check_portfolio_exposure_limit(base_request, base_config)
    assert not res.breached

    # Adding more exposure -> Fail
    base_request.market_context["portfolio_gross_exposure"] = 495000.0
    res_fail = check_portfolio_exposure_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_run_limit_checks_aggregation(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test sequential aggregation precedence and primary failure selection."""
    # 1. No breaches -> approve
    status, _code, _msg, flags, primary, _results = run_limit_checks(
        base_request, base_config
    )
    assert status == RiskDecisionStatus.APPROVE
    assert not flags
    assert primary == ""

    # 2. Add an exposure breach (REJECT)
    base_request.market_context["portfolio_gross_exposure"] = 600000.0
    status, code, _msg, flags, primary, _results = run_limit_checks(
        base_request, base_config
    )
    assert status == RiskDecisionStatus.REJECT
    assert code == RiskReasonCode.CONCENTRATION_BREACH
    assert "portfolio_exposure_limit" in flags
    assert primary == "portfolio_exposure_limit"

    # 3. Daily loss breach (REJECT, runs before portfolio exposure)
    base_request.market_context["daily_loss_pct"] = 0.06
    status, code, _msg, flags, primary, _results = run_limit_checks(
        base_request, base_config
    )
    assert status == RiskDecisionStatus.REJECT
    assert code == RiskReasonCode.DAILY_LOSS_BREACH  # Selected over concentration
    assert "daily_loss_limit" in flags
    assert "portfolio_exposure_limit" in flags
    assert primary == "daily_loss_limit"

    # 4. Add a kill switch active breach (BLOCK, which overrides REJECT entirely)
    base_request.market_context["kill_switch_active"] = True
    status, code, _msg, flags, primary, _results = run_limit_checks(
        base_request, base_config
    )
    assert status == RiskDecisionStatus.BLOCK
    assert code == RiskReasonCode.KILL_SWITCH_ACTIVE
    assert "kill_switch_state" in flags
    assert primary == "kill_switch_state"
