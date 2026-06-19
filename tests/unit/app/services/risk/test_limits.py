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
    LimitResult,
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


def test_unknown_limit_name_rejection(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test rejection of unknown limit names in market context."""
    base_request.market_context["run_limits"] = ["invalid_limit_name_xyz"]
    status, code, message, flags, primary, _results = run_limit_checks(
        base_request, base_config
    )
    assert status == RiskDecisionStatus.BLOCK
    assert code == RiskReasonCode.INVALID_INPUT
    assert "invalid_limit_name" in flags
    assert primary == "invalid_limit_name"
    assert "Unknown limit name" in message


def test_precedence_ordering_and_tie_breaking(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test aggregation status precedence rules and stable tie-breaking."""
    # news_blackout and rollover_blackout both fail (REJECT).
    # Since news_blackout runs first in ORDERED_LIMIT_CHECKS, it wins the tie-breaker.
    base_request.market_context["news_blackout_active"] = True
    base_request.market_context["rollover_blackout_active"] = True

    status, _code, _message, flags, primary, _results = run_limit_checks(
        base_request, base_config
    )
    assert status == RiskDecisionStatus.REJECT
    assert primary == "news_blackout"
    assert "news_blackout" in flags
    assert "rollover_blackout" in flags

    # BLOCK should override REJECT
    base_request.market_context["kill_switch_active"] = True
    status, _code, _message, flags, primary, _results = run_limit_checks(
        base_request, base_config
    )
    assert status == RiskDecisionStatus.BLOCK
    assert primary == "kill_switch_state"


def test_non_finite_math_checks(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test that non-finite values in math limits trigger fail-closed BLOCK."""
    from app.services.risk.limits import (
        check_correlation_limit,
        check_currency_exposure_limit,
        check_daily_loss_limit,
        check_expected_shortfall_limit,
        check_leverage_limit,
        check_margin_limit,
        check_max_drawdown_limit,
        check_pending_order_limit,
        check_portfolio_exposure_limit,
        check_slippage_limit,
        check_spread_limit,
        check_strategy_loss_limit,
        check_stress_loss_limit,
        check_symbol_exposure_limit,
        check_trade_frequency_limit,
        check_var_limit,
    )

    # 1. Drawdown
    base_request.market_context["drawdown"] = float("nan")
    assert (
        check_max_drawdown_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 2. Daily Loss
    base_request.market_context["daily_loss_pct"] = float("nan")
    assert (
        check_daily_loss_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 3. Strategy Loss
    base_request.market_context["strategy_loss_pct"] = float("nan")
    assert (
        check_strategy_loss_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 4. Spread
    base_request.market_context["spread"] = float("nan")
    assert (
        check_spread_limit(base_request, base_config).status == RiskDecisionStatus.BLOCK
    )

    # 5. Slippage
    base_request.market_context["slippage"] = float("nan")
    assert (
        check_slippage_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 6. Trade Frequency
    base_request.market_context["trade_frequency"] = float("nan")
    assert (
        check_trade_frequency_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 7. Pending Order
    base_request.market_context["pending_orders_count"] = float("nan")
    assert (
        check_pending_order_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 8. Portfolio Exposure
    base_request.market_context["portfolio_gross_exposure"] = float("nan")
    assert (
        check_portfolio_exposure_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 9. Symbol Exposure
    base_request.market_context["symbol_exposure_EURUSD"] = float("nan")
    assert (
        check_symbol_exposure_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 10. Currency Exposure
    base_request.market_context["currency_gross_exposure"] = float("nan")
    assert (
        check_currency_exposure_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 11. Correlation
    base_request.market_context["correlated_cluster_exposure"] = float("nan")
    assert (
        check_correlation_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 12. VaR
    base_request.market_context["var_metric"] = float("nan")
    assert check_var_limit(base_request, base_config).status == RiskDecisionStatus.BLOCK

    # 13. Expected Shortfall
    base_request.market_context["es_metric"] = float("nan")
    assert (
        check_expected_shortfall_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 14. Stress Loss
    base_request.market_context["stress_loss_val"] = float("nan")
    assert (
        check_stress_loss_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 15. Leverage
    base_request.market_context["effective_leverage"] = float("nan")
    assert (
        check_leverage_limit(base_request, base_config).status
        == RiskDecisionStatus.BLOCK
    )

    # 16. Margin
    base_request.portfolio_state.margin_used = Decimal("NaN")
    assert (
        check_margin_limit(base_request, base_config).status == RiskDecisionStatus.BLOCK
    )


def test_limit_engine_calculation_failure(
    base_request: RiskAssessmentRequest,
    base_config: RiskConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test how LimitEngine wraps limit check runtime calculation failures."""
    from app.services.risk.limits import LimitEngine

    def mock_check(req: RiskAssessmentRequest, conf: RiskConfig) -> LimitResult:
        raise ValueError("Simulated calculation error")

    import sys

    monkeypatch.setattr(
        sys.modules[LimitEngine.__module__],
        "ORDERED_LIMIT_CHECKS",
        (mock_check,),
    )

    engine = LimitEngine(config=base_config)
    results = engine.execute(base_request)
    assert len(results) == 1
    assert results[0].status == RiskDecisionStatus.BLOCK
    assert results[0].reason_code == RiskReasonCode.UNEXPECTED_ERROR
    assert "calculation failed" in results[0].message


def test_check_strategy_loss_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test strategy drawdown limit gates."""
    from app.services.risk.limits import check_strategy_loss_limit

    # Pass
    res = check_strategy_loss_limit(base_request, base_config)
    assert not res.breached
    assert res.status == RiskDecisionStatus.APPROVE

    # Fail
    base_request.market_context["strategy_loss_pct"] = 0.05
    base_request.market_context["max_strategy_loss_pct"] = 0.04
    res_fail = check_strategy_loss_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_check_news_blackout(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test high impact news blackout gating."""
    from app.services.risk.limits import check_news_blackout

    # Pass
    res = check_news_blackout(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["news_blackout_active"] = True
    res_fail = check_news_blackout(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_check_rollover_blackout(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test broker midnight rollover blackout window gating."""
    from app.services.risk.limits import check_rollover_blackout

    # Pass
    res = check_rollover_blackout(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["rollover_blackout_active"] = True
    res_fail = check_rollover_blackout(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_check_spread_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test spread threshold gates."""
    from app.services.risk.limits import check_spread_limit

    # Pass
    res = check_spread_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["spread"] = 0.0060
    base_request.market_context["max_spread"] = 0.0050
    res_fail = check_spread_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_check_slippage_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test execution slippage limit gates."""
    from app.services.risk.limits import check_slippage_limit

    # Pass
    res = check_slippage_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["slippage"] = 0.0030
    base_request.market_context["max_slippage"] = 0.0020
    res_fail = check_slippage_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_check_trade_frequency_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test short-term trade frequency throttling."""
    from app.services.risk.limits import check_trade_frequency_limit

    # Pass
    res = check_trade_frequency_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["trade_frequency"] = 12
    base_request.market_context["max_trade_frequency"] = 10
    res_fail = check_trade_frequency_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Invalid input
    base_request.market_context["trade_frequency"] = "invalid_non_numeric"
    res_invalid = check_trade_frequency_limit(base_request, base_config)
    assert res_invalid.breached
    assert res_invalid.status == RiskDecisionStatus.BLOCK
    assert res_invalid.reason_code == RiskReasonCode.INVALID_INPUT


def test_check_pending_order_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test pending order capacity checks."""
    from app.services.risk.limits import check_pending_order_limit

    # Pass
    res = check_pending_order_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["pending_orders_count"] = 6
    base_request.market_context["max_pending_orders"] = 5
    res_fail = check_pending_order_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Invalid input
    base_request.market_context["pending_orders_count"] = "invalid_non_numeric"
    res_invalid = check_pending_order_limit(base_request, base_config)
    assert res_invalid.breached
    assert res_invalid.status == RiskDecisionStatus.BLOCK
    assert res_invalid.reason_code == RiskReasonCode.INVALID_INPUT


def test_check_symbol_exposure_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test symbol-level concentration limits."""
    from app.services.risk.limits import check_symbol_exposure_limit

    # Pass
    res = check_symbol_exposure_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["symbol_exposure_EURUSD"] = 100000.0
    base_request.market_context["contract_size"] = 100000.0
    base_request.market_context["max_symbol_exposure"] = 1.0
    base_request.portfolio_state.equity = Decimal("100000.00")
    # Proposed volume is 0.1 -> 10,000 exposure.
    # Total exposure 110,000 > equity 100,000.
    res_fail = check_symbol_exposure_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Negative equity
    base_request.portfolio_state.equity = Decimal("-10.00")
    res_neg = check_symbol_exposure_limit(base_request, base_config)
    assert res_neg.status == RiskDecisionStatus.BLOCK


def test_check_currency_exposure_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test gross currency exposure concentration checks."""
    from app.services.risk.limits import check_currency_exposure_limit

    # Pass
    res = check_currency_exposure_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["currency_gross_exposure"] = 160000.0
    base_request.market_context["max_currency_exposure"] = 1.5
    base_request.portfolio_state.equity = Decimal("100000.00")
    res_fail = check_currency_exposure_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Negative equity
    base_request.portfolio_state.equity = Decimal("0.00")
    res_neg = check_currency_exposure_limit(base_request, base_config)
    assert res_neg.status == RiskDecisionStatus.BLOCK


def test_check_correlation_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test correlated exposure cluster concentration limits."""
    from app.services.risk.limits import check_correlation_limit

    # Pass
    res = check_correlation_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["correlated_cluster_exposure"] = 210000.0
    base_request.market_context["max_correlated_exposure"] = 2.0
    base_request.portfolio_state.equity = Decimal("100000.00")
    res_fail = check_correlation_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Negative equity
    base_request.portfolio_state.equity = Decimal("0.00")
    res_neg = check_correlation_limit(base_request, base_config)
    assert res_neg.status == RiskDecisionStatus.BLOCK


def test_check_var_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test portfolio Value-at-Risk percentage limits."""
    from app.services.risk.limits import check_var_limit

    # Pass
    res = check_var_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["var_metric"] = 6000.0
    base_request.market_context["max_var_ratio"] = 0.05
    base_request.portfolio_state.equity = Decimal("100000.00")
    res_fail = check_var_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Negative equity
    base_request.portfolio_state.equity = Decimal("0.00")
    res_neg = check_var_limit(base_request, base_config)
    assert res_neg.status == RiskDecisionStatus.BLOCK


def test_check_expected_shortfall_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test portfolio Expected Shortfall tail-risk limits."""
    from app.services.risk.limits import check_expected_shortfall_limit

    # Pass
    res = check_expected_shortfall_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["es_metric"] = 9000.0
    base_request.market_context["max_es_ratio"] = 0.08
    base_request.portfolio_state.equity = Decimal("100000.00")
    res_fail = check_expected_shortfall_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Negative equity
    base_request.portfolio_state.equity = Decimal("0.00")
    res_neg = check_expected_shortfall_limit(base_request, base_config)
    assert res_neg.status == RiskDecisionStatus.BLOCK


def test_check_stress_loss_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test stress testing shock impact limits."""
    from app.services.risk.limits import check_stress_loss_limit

    # Pass
    res = check_stress_loss_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["stress_loss_val"] = 16000.0
    base_request.market_context["max_stress_ratio"] = 0.15
    base_request.portfolio_state.equity = Decimal("100000.00")
    res_fail = check_stress_loss_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Negative equity
    base_request.portfolio_state.equity = Decimal("0.00")
    res_neg = check_stress_loss_limit(base_request, base_config)
    assert res_neg.status == RiskDecisionStatus.BLOCK


def test_check_leverage_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test effective portfolio leverage limits."""
    from app.services.risk.limits import check_leverage_limit

    # Pass
    res = check_leverage_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.market_context["effective_leverage"] = 35.0
    base_config.max_effective_leverage = Decimal("30.0")
    res_fail = check_leverage_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT


def test_check_margin_limit(
    base_request: RiskAssessmentRequest, base_config: RiskConfig
) -> None:
    """Test portfolio margin utilization limit checks."""
    from app.services.risk.limits import check_margin_limit

    # Pass
    res = check_margin_limit(base_request, base_config)
    assert not res.breached

    # Fail
    base_request.portfolio_state.margin_used = Decimal("85000.00")
    base_request.portfolio_state.equity = Decimal("100000.00")
    base_config.max_margin_utilization_pct = Decimal("0.80")
    res_fail = check_margin_limit(base_request, base_config)
    assert res_fail.breached
    assert res_fail.status == RiskDecisionStatus.REJECT

    # Negative equity
    base_request.portfolio_state.equity = Decimal("0.00")
    res_neg = check_margin_limit(base_request, base_config)
    assert res_neg.status == RiskDecisionStatus.BLOCK
