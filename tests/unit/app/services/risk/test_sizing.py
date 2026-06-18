"""Unit tests for the position sizing engine."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    PortfolioState,
    PositionSizingRequest,
    RiskConfig,
    SizingMethod,
    calculate_position_size,
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
        "tick_value": 1.0,  # $1 per tick/point per standard lot
        "conversion_rate": 1.0,
    }


def test_invalid_sizing_inputs(
    base_portfolio: PortfolioState, base_config: RiskConfig
) -> None:
    """Test validation failure conditions."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("-10.0"),  # Negative stop
    )

    # 1. Negative stop distance -> 0.0 lot
    res = calculate_position_size(
        req,
        base_portfolio,
        {
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
            "contract_size": 100000.0,
        },
        base_config,
    )
    assert res.calculated_volume == Decimal("0.0")
    assert "invalid_stop_distance" in res.constraints_applied

    # 2. Missing symbol specs -> 0.0 lot
    res_missing = calculate_position_size(req, base_portfolio, {}, base_config)
    assert res_missing.calculated_volume == Decimal("0.0")
    assert "missing_symbol_metadata" in res_missing.constraints_applied


def test_fixed_lot_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test static lot sizing with broker steps formatting."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_LOT,
        fixed_volume=Decimal("1.2345"),
    )

    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    # 1.2345 should round down to volume_step 0.01 -> 1.23 lots
    assert res.calculated_volume == Decimal("1.23")


def test_fixed_risk_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test fixed risk sizing logic."""
    # Equity = 100,000. Max risk per trade = 2% (2,000 USD).
    # Stop loss distance = 20 pips = 200 points.
    # Risk per standard lot = 200 points * $1 tick_value = $200.
    # Raw volume = $2000 / $200 = 10.0 lots.
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )

    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    assert res.calculated_volume == Decimal("10.0")
    assert res.risk_contribution == Decimal("2000.00")

    # Override with static risk_amount of $1,000.
    req_amt = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("20.0"),
        risk_amount=Decimal("1000.00"),
    )
    res_amt = calculate_position_size(
        req_amt, base_portfolio, eur_usd_context, base_config
    )
    # $1000 / $200 = 5.0 lots
    assert res_amt.calculated_volume == Decimal("5.00")


def test_volatility_adjusted_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test ATR volatility-adjusted sizing calculations."""
    # ATR = 0.00100 (10 pips). Multiplier = 2.0x.
    # Stop distance = 20 pips (200 points).
    # Risk amount = 100,000 * 2% = 2,000 USD.
    # Raw size = 2000 / (200 points * 1.0 tick_val) = 10.0 lots.
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED,
        atr_value=Decimal("0.00100"),
        multiplier=Decimal("2.0"),
        risk_percent=Decimal("0.02"),
    )

    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    assert res.calculated_volume == Decimal("10.0")
    assert "atr_volatility_stop" in res.constraints_applied

    # Test M1 volatility override in context
    eur_usd_context["m1_volatility"] = 0.00050  # 5 pips
    res_m1 = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    # Stop distance = 0.00050 * 2.0 = 0.00100 (10 pips = 100 points).
    # Risk per standard lot = 100 points * $1 = $100.
    # Raw size = 2000 / 100 = 20.0 lots.
    assert res_m1.calculated_volume == Decimal("20.0")
    assert "m1_volatility_stop" in res_m1.constraints_applied


def test_sizing_downward_multipliers(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test drawdown step-down and exposure reductions."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )

    # Inject multipliers: step-down 0.5, ccy-red 0.8, cluster-red 0.9
    eur_usd_context["drawdown_step_down_multiplier"] = 0.5
    eur_usd_context["currency_exposure_reduction"] = 0.8
    eur_usd_context["correlation_cluster_reduction"] = 0.9

    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    # Raw size = 10.0 lots
    # Adjusted size = 10.0 * 0.5 * 0.8 * 0.9 = 3.6 lots
    assert res.calculated_volume == Decimal("3.60")
    assert "drawdown_step_down" in res.constraints_applied
    assert "currency_exposure_reduction" in res.constraints_applied
    assert "correlation_cluster_reduction" in res.constraints_applied


def test_jpy_pair_sizing(
    base_portfolio: PortfolioState, base_config: RiskConfig
) -> None:
    """Test FX JPY pair pip and quote digit scaling."""
    # USDJPY has digits = 3 (1 pip = 0.01).
    # Stop distance = 50 pips = 0.50 price difference = 500 points.
    # Account is USD. USDJPY tick_value is $0.91 (approx 100 / 110 JPY).
    # Risk amount = 100,000 * 1% = 1,000 USD.
    # Risk per standard lot = 500 points * $0.91 = $455.
    # Raw volume = 1000 / 455 = 2.1978... lots -> Rounded to 2.19.
    jpy_context = {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "contract_size": 100000.0,
        "digits": 3,
        "tick_size": 0.001,
        "tick_value": 0.91,
        "conversion_rate": 0.0091,  # JPY to USD rate
    }
    req = PositionSizingRequest(
        symbol="USDJPY",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("50.0"),
        risk_percent=Decimal("0.01"),
    )

    res = calculate_position_size(req, base_portfolio, jpy_context, base_config)
    assert res.calculated_volume == Decimal("2.19")


def test_correlation_adjusted_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test correlation adjusted sizing formula."""
    # Raw size = 10.0 lots.
    # Correlation coefficient = 0.8.
    # Multiplier = 1.0 - (0.8 * 0.5) = 0.6x.
    # Sized volume = 10.0 * 0.6 = 6.0 lots.
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.CORRELATION_ADJUSTED,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )

    eur_usd_context["portfolio_correlation"] = 0.8
    res = calculate_position_size(req, base_portfolio, eur_usd_context, base_config)
    assert res.calculated_volume == Decimal("6.00")
    assert "correlation_adjustment" in res.constraints_applied


def test_kelly_reference_sizing(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test Kelly reference sizing and historical trades threshold gating."""
    req = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.KELLY,
        stop_loss_pips=Decimal("20.0"),
    )

    # 1. Under minimum trade history evidence.
    # Kelly is advisory-only (returns 0.0 lot).
    eur_usd_context["kelly_win_rate"] = 0.60
    eur_usd_context["kelly_win_loss_ratio"] = 2.0
    eur_usd_context["historical_trade_count"] = 10
    eur_usd_context["kelly_min_trades"] = 30

    res_insufficient = calculate_position_size(
        req, base_portfolio, eur_usd_context, base_config
    )
    assert res_insufficient.calculated_volume == Decimal("0.00")
    assert (
        "kelly_advisory_insufficient_evidence" in res_insufficient.constraints_applied
    )

    # 2. Meets evidence threshold -> Kelly size calculated
    # Kelly fraction = p - (1-p)/R = 0.6 - (1 - 0.6)/2 = 0.6 - 0.2 = 0.4 (40%)
    # Kelly capital amount = 100,000 * 0.4 = 40,000 USD.
    # Risk per standard lot = 200 points * $1 = $200.
    # Raw size = 40000 / 200 = 200 lots.
    # Cap to volume_max (100.0 lots)
    eur_usd_context["historical_trade_count"] = 50
    res_sufficient = calculate_position_size(
        req, base_portfolio, eur_usd_context, base_config
    )
    assert res_sufficient.calculated_volume == Decimal("100.00")
    assert "kelly_fraction_applied" in res_sufficient.constraints_applied
    assert "volume_max_cap" in res_sufficient.constraints_applied
