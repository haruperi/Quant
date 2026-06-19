"""Unit tests for new position sizing sizer classes and VolatilitySizingEngine."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    CorrelationAdjustedSizer,
    FixedFractionalSizer,
    FixedRiskSizer,
    KellyReferenceSizer,
    MilestoneSizer,
    PortfolioState,
    PositionSizingRequest,
    RiskConfig,
    SizingMethod,
    VolatilityAdjustedSizer,
    VolatilitySizingEngine,
    calculate_position_size,
    calculate_sigma_stop_distance,
)
from app.services.risk.config import load_risk_config


@pytest.fixture
def base_config() -> RiskConfig:
    """Load default base risk config."""
    cfg = load_risk_config("default")
    cfg.max_risk_per_trade = Decimal("0.05")
    return cfg


@pytest.fixture
def base_portfolio() -> PortfolioState:
    """Provide a standard portfolio state."""
    return PortfolioState(
        account_id="acc-123",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[],
    )


@pytest.fixture
def eur_usd_context() -> dict[str, Any]:
    """Provide standard EURUSD quote symbol context."""
    return {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "contract_size": 100000.0,
        "digits": 5,
        "tick_size": 0.00001,
        "tick_value": 1.0,
        "conversion_rate": 1.0,
    }


def test_calculate_sigma_stop_distance(eur_usd_context: dict[str, Any]) -> None:
    """Test volatility stop distance calculation."""
    # 1. Test M1 Volatility
    context_m1 = eur_usd_context.copy()
    context_m1["m1_volatility"] = 0.00050  # 5 pips
    price_dist, pip_dist = calculate_sigma_stop_distance(
        market_context=context_m1,
        digits=5,
        multiplier=Decimal("2.0"),
    )
    assert price_dist == Decimal("0.00100")
    assert pip_dist == Decimal("10.0")

    # 2. Test ATR fallback
    context_atr = eur_usd_context.copy()
    price_dist, pip_dist = calculate_sigma_stop_distance(
        market_context=context_atr,
        digits=5,
        multiplier=Decimal("3.0"),
        atr_value=Decimal("0.00040"),
    )
    assert price_dist == Decimal("0.00120")
    assert pip_dist == Decimal("12.0")

    # 3. Test Missing Volatility
    with pytest.raises(ValueError, match="Missing volatility inputs"):
        calculate_sigma_stop_distance(
            market_context=eur_usd_context,
            digits=5,
            multiplier=Decimal("2.0"),
        )


def test_fixed_risk_sizer(
    base_config: RiskConfig,
    base_portfolio: PortfolioState,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test FixedRiskSizer directly."""
    sizer = FixedRiskSizer(base_config)
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )
    constraints: list[str] = []
    specs = {
        "tick_size": Decimal("0.00001"),
        "tick_value": Decimal("1.0"),
    }
    stop_distance_price = Decimal("0.00200")
    size = sizer.calculate(
        request=req,
        portfolio_state=base_portfolio,
        market_context=eur_usd_context,
        specs=specs,
        stop_distance_price=stop_distance_price,
        constraints_applied=constraints,
    )
    assert size == Decimal("10.0")


def test_fixed_fractional_sizer(
    base_config: RiskConfig,
    base_portfolio: PortfolioState,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test FixedFractionalSizer directly."""
    sizer = FixedFractionalSizer(base_config)
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_FRACTIONAL,
        risk_percent=Decimal("0.01"),
    )
    constraints: list[str] = []
    specs = {
        "tick_size": Decimal("0.00001"),
        "tick_value": Decimal("1.0"),
    }
    stop_distance_price = Decimal("0.00100")
    size = sizer.calculate(
        request=req,
        portfolio_state=base_portfolio,
        market_context=eur_usd_context,
        specs=specs,
        stop_distance_price=stop_distance_price,
        constraints_applied=constraints,
    )
    assert size == Decimal("10.0")


def test_volatility_adjusted_sizer(
    base_config: RiskConfig,
    base_portfolio: PortfolioState,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test VolatilityAdjustedSizer directly."""
    sizer = VolatilityAdjustedSizer(base_config)
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED,
        risk_percent=Decimal("0.02"),
    )
    constraints: list[str] = []
    specs = {
        "tick_size": Decimal("0.00001"),
        "tick_value": Decimal("1.0"),
    }
    stop_distance_price = Decimal("0.00200")
    size = sizer.calculate(
        request=req,
        portfolio_state=base_portfolio,
        market_context=eur_usd_context,
        specs=specs,
        stop_distance_price=stop_distance_price,
        constraints_applied=constraints,
    )
    assert size == Decimal("10.0")


def test_milestone_sizer(
    base_config: RiskConfig,
    base_portfolio: PortfolioState,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test MilestoneSizer scaling logic."""
    sizer = MilestoneSizer(base_config)
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.MILESTONE,
        risk_percent=Decimal("0.02"),
    )
    constraints: list[str] = []
    specs = {
        "tick_size": Decimal("0.00001"),
        "tick_value": Decimal("1.0"),
    }
    stop_distance_price = Decimal("0.00200")

    size = sizer.calculate(
        request=req,
        portfolio_state=base_portfolio,
        market_context=eur_usd_context,
        specs=specs,
        stop_distance_price=stop_distance_price,
        constraints_applied=constraints,
    )
    assert size == Decimal("10.0")
    assert "milestone_adjustment" not in constraints

    context_milestone = eur_usd_context.copy()
    context_milestone["milestone_multiplier"] = 0.5
    size_scaled = sizer.calculate(
        request=req,
        portfolio_state=base_portfolio,
        market_context=context_milestone,
        specs=specs,
        stop_distance_price=stop_distance_price,
        constraints_applied=constraints,
    )
    assert size_scaled == Decimal("5.0")
    assert "milestone_adjustment" in constraints


def test_correlation_adjusted_sizer(
    base_config: RiskConfig,
    base_portfolio: PortfolioState,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test CorrelationAdjustedSizer direct calculation."""
    sizer = CorrelationAdjustedSizer(base_config)
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.CORRELATION_ADJUSTED,
        risk_percent=Decimal("0.02"),
    )
    constraints: list[str] = []
    specs = {
        "tick_size": Decimal("0.00001"),
        "tick_value": Decimal("1.0"),
    }
    stop_distance_price = Decimal("0.00200")

    context_corr = eur_usd_context.copy()
    context_corr["portfolio_correlation"] = 0.8
    size = sizer.calculate(
        request=req,
        portfolio_state=base_portfolio,
        market_context=context_corr,
        specs=specs,
        stop_distance_price=stop_distance_price,
        constraints_applied=constraints,
    )
    assert size == Decimal("6.0")
    assert "correlation_adjustment" in constraints


def test_kelly_reference_sizer_advisory_vs_fractional(
    base_config: RiskConfig,
    base_portfolio: PortfolioState,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test Kelly sizer evidence and live execution gating.

    Verifies advisory-only limits vs fractional Kelly.
    """
    sizer = KellyReferenceSizer(base_config)
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.KELLY,
    )
    specs = {
        "tick_size": Decimal("0.00001"),
        "tick_value": Decimal("1.0"),
        "contract_size": Decimal("100000.0"),
        "conversion_rate": Decimal("1.0"),
    }
    stop_distance_price = Decimal("0.00200")

    context_low_evidence = eur_usd_context.copy()
    context_low_evidence["kelly_win_rate"] = 0.60
    context_low_evidence["kelly_win_loss_ratio"] = 2.0
    context_low_evidence["historical_trade_count"] = 2
    context_low_evidence["kelly_min_trades"] = 5

    constraints: list[str] = []
    size_insufficient = sizer.calculate(
        request=req,
        portfolio_state=base_portfolio,
        market_context=context_low_evidence,
        specs=specs,
        stop_distance_price=stop_distance_price,
        constraints_applied=constraints,
    )
    assert size_insufficient == Decimal("0.0")
    assert "kelly_advisory_insufficient_evidence" in constraints

    context_sufficient = eur_usd_context.copy()
    context_sufficient["kelly_win_rate"] = 0.60
    context_sufficient["kelly_win_loss_ratio"] = 2.0
    context_sufficient["historical_trade_count"] = 10
    context_sufficient["kelly_min_trades"] = 5
    context_sufficient["is_live"] = True

    constraints = []
    size_advisory = sizer.calculate(
        request=req,
        portfolio_state=base_portfolio,
        market_context=context_sufficient,
        specs=specs,
        stop_distance_price=stop_distance_price,
        constraints_applied=constraints,
    )
    assert size_advisory == Decimal("0.0")
    assert "kelly_advisory_only" in constraints

    context_fractional = context_sufficient.copy()
    context_fractional["enable_fractional_kelly"] = True
    constraints = []
    size_fractional = sizer.calculate(
        request=req,
        portfolio_state=base_portfolio,
        market_context=context_fractional,
        specs=specs,
        stop_distance_price=stop_distance_price,
        constraints_applied=constraints,
    )
    assert size_fractional == Decimal("200.0")
    assert "kelly_fraction_applied" in constraints
    assert "kelly_advisory_only" not in constraints


def test_volatility_sizing_engine_coordination(
    base_config: RiskConfig,
    base_portfolio: PortfolioState,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test VolatilitySizingEngine coordinator class."""
    engine = VolatilitySizingEngine(base_config)

    initial_risk = engine.calculate_initial_risk_amount(
        request=PositionSizingRequest(symbol="EURUSD", method="fixed_risk"),
        portfolio_state=base_portfolio,
        market_context={},
    )
    assert initial_risk == Decimal("5000.00")

    base_config.drawdown_stepdown_thresholds = [Decimal("0.05")]
    base_config.drawdown_stepdown_multipliers = [Decimal("0.5")]
    initial_risk_dd = engine.calculate_initial_risk_amount(
        request=PositionSizingRequest(symbol="EURUSD", method="fixed_risk"),
        portfolio_state=base_portfolio,
        market_context={"drawdown_pct": "0.06"},
    )
    assert initial_risk_dd == Decimal("2500.00")

    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK.value,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )
    res = engine.calculate_size(req, base_portfolio, eur_usd_context)
    assert res.calculated_volume == Decimal("10.0")
    assert res.sizing_method == SizingMethod.FIXED_RISK.value


def test_zero_and_extreme_volatility_edge_cases(
    base_config: RiskConfig,
    base_portfolio: PortfolioState,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test volatility sizing edge cases (zero/huge volatility)."""
    req_vol = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED,
        risk_percent=Decimal("0.02"),
    )

    context_zero = eur_usd_context.copy()
    context_zero["m1_volatility"] = 0.0
    res_zero = calculate_position_size(
        req_vol, base_portfolio, context_zero, base_config
    )
    assert res_zero.calculated_volume == Decimal("0.0")
    assert "invalid_stop_distance" in res_zero.constraints_applied

    context_huge = eur_usd_context.copy()
    context_huge["m1_volatility"] = 50.0
    res_huge = calculate_position_size(
        req_vol, base_portfolio, context_huge, base_config
    )
    assert res_huge.calculated_volume == Decimal("0.0")
    assert "below_minimum_volume" in res_huge.constraints_applied


def test_governor_reduce_size_status(base_portfolio: PortfolioState) -> None:
    """Test governor yields reduce_size correctly."""
    from app.services.risk.governor import RiskGovernor
    from app.services.risk.models import ProposedTrade, RiskAssessmentRequest
    from app.services.risk.storage import InMemoryRiskStateStore

    config = load_risk_config("default")
    config.max_risk_per_trade = Decimal("0.02")

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(
        decision_store=store,
        policy_store=store,
        state_store=store,
        audit_sink=store,
    )

    trade = ProposedTrade(
        strategy_id="strategy-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("10.0"),
    )

    sizing_req = {
        "method": "fixed_risk",
        "stop_loss_pips": 20.0,
        "risk_percent": 0.002,
    }

    market_context = {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "contract_size": 100000.0,
        "digits": 5,
        "tick_size": 0.00001,
        "tick_value": 1.0,
        "conversion_rate": 1.0,
        "sizing_request": sizing_req,
        "mode": "paper",
        "environment": "local",
        "freshness": datetime.now(UTC).isoformat(),
        "daily_loss_pct": 0.0,
        "max_stress_ratio": 2.0,
    }

    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=base_portfolio,
        risk_config=config,
        market_context=market_context,
    )

    decision = gov.review_trade_risk(req)
    assert decision.status == "reduce_size"
    assert decision.calculated_volume == Decimal("1.0")
    assert trade.volume == Decimal("10.0")
