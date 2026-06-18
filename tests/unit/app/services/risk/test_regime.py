"""Unit tests for Market regime assessment engine."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.services.risk.config import load_risk_config
from app.services.risk.models import (
    MarketRiskSnapshot,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
)
from app.services.risk.regime import (
    LiquidityRegime,
    NewsRegime,
    RiskRegime,
    RolloverRegime,
    SessionRegime,
    SpreadRegime,
    VolatilityRegime,
    assess_risk_regime,
)
from app.utils.normalization import utc_now


@pytest.fixture
def base_config() -> RiskConfig:
    """Load default base risk config."""
    return load_risk_config("default")


@pytest.fixture
def live_config() -> RiskConfig:
    """Load live conservative risk config."""
    return load_risk_config("live_conservative")


@pytest.fixture
def normal_snapshot() -> MarketRiskSnapshot:
    """Provide a normal, fresh market snapshot."""
    return MarketRiskSnapshot(
        spread=Decimal("0.0002"),
        volatility=Decimal("0.0150"),
        session="NY",
        freshness=utc_now(),
        rollover_time=None,
    )


def test_assess_risk_regime_normal(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test assessment under normal market conditions."""
    context = {
        "spread_mean": 0.0002,
        "spread_std": 0.0001,
        "vol_short": 0.015,
        "vol_med": 0.015,
        "vol_long": 0.015,
        "tick_frequency": 30,
        "missing_bars": 0,
        "stale_seconds": 2,
    }
    result = assess_risk_regime(normal_snapshot, [], base_config, context)
    assert result.status == RiskDecisionStatus.APPROVE
    assert result.regime == RiskRegime.NORMAL
    assert result.spread_regime == SpreadRegime.NORMAL
    assert result.volatility_regime == VolatilityRegime.NORMAL
    assert result.liquidity_regime == LiquidityRegime.NORMAL
    assert result.news_regime == NewsRegime.NORMAL
    assert result.session_regime == SessionRegime.ACTIVE
    assert result.rollover_regime == RolloverRegime.NORMAL
    assert result.reason_code == RiskReasonCode.OK


def test_assess_risk_regime_invalid_spread(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test rejection when spread is negative/inverted."""
    invalid_snap = normal_snapshot.model_copy(update={"spread": Decimal("-0.0001")})
    result = assess_risk_regime(invalid_snap, [], base_config)
    assert result.status == RiskDecisionStatus.BLOCK
    assert result.regime == RiskRegime.INVALID_QUOTE
    assert result.reason_code == RiskReasonCode.INVALID_INPUT


def test_assess_risk_regime_stale_data(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test rejection when quote freshness is older than threshold."""
    stale_snap = normal_snapshot.model_copy(
        update={"freshness": utc_now() - timedelta(seconds=61)}
    )
    # With default limit of 60s
    result = assess_risk_regime(stale_snap, [], base_config)
    assert result.status == RiskDecisionStatus.BLOCK
    assert result.regime == RiskRegime.STALE_DATA
    assert result.reason_code == RiskReasonCode.STALE_EVIDENCE


def test_assess_risk_regime_market_closed_or_suspended(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test block when market session is closed or symbol suspended."""
    closed_snap = normal_snapshot.model_copy(update={"session": "closed"})
    result = assess_risk_regime(closed_snap, [], base_config)
    assert result.status == RiskDecisionStatus.BLOCK
    assert result.regime == RiskRegime.MARKET_CLOSED

    suspended_context = {"is_suspended": True}
    result_susp = assess_risk_regime(
        normal_snapshot, [], base_config, suspended_context
    )
    assert result_susp.status == RiskDecisionStatus.BLOCK
    assert result_susp.regime == RiskRegime.SUSPENDED
    assert result_susp.reason_code == RiskReasonCode.LIFECYCLE_GATES_BREACH


def test_assess_risk_regime_spread_widening(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test classification of wide and extreme spread regimes using z-score."""
    # Historical spread statistics passed: mean=0.0002, std=0.0001
    context = {
        "spread_mean": 0.0002,
        "spread_std": 0.0001,
        "spread_z_score_threshold_normal": 1.5,
        "spread_z_score_threshold_wide": 3.0,
    }

    # Z-score = (0.0003 - 0.0002)/0.0001 = 1.0 -> NORMAL
    snap_normal = normal_snapshot.model_copy(update={"spread": Decimal("0.0003")})
    res_normal = assess_risk_regime(snap_normal, [], base_config, context)
    assert res_normal.spread_regime == SpreadRegime.NORMAL
    assert res_normal.status == RiskDecisionStatus.APPROVE

    # Z-score = (0.00045 - 0.0002)/0.0001 = 2.5 -> WIDE
    snap_wide = normal_snapshot.model_copy(update={"spread": Decimal("0.00045")})
    res_wide = assess_risk_regime(snap_wide, [], base_config, context)
    assert res_wide.spread_regime == SpreadRegime.WIDE
    assert res_wide.regime == RiskRegime.WIDE_SPREAD
    assert res_wide.status == RiskDecisionStatus.APPROVE

    # Z-score = (0.0006 - 0.0002)/0.0001 = 4.0 -> EXTREME -> REJECT
    snap_ext = normal_snapshot.model_copy(update={"spread": Decimal("0.0006")})
    res_ext = assess_risk_regime(snap_ext, [], base_config, context)
    assert res_ext.spread_regime == SpreadRegime.EXTREME
    assert res_ext.regime == RiskRegime.WIDE_SPREAD
    assert res_ext.status == RiskDecisionStatus.REJECT
    assert res_ext.reason_code == RiskReasonCode.SPREAD_BREACH


def test_assess_risk_regime_volatility_classifications(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test low, high, and spike volatility classification ratios."""
    # Base configuration test
    context_low = {"vol_short": 0.004, "vol_med": 0.010, "vol_long": 0.010}
    res_low = assess_risk_regime(normal_snapshot, [], base_config, context_low)
    assert res_low.volatility_regime == VolatilityRegime.LOW
    assert res_low.regime == RiskRegime.LOW_VOLATILITY

    context_high = {"vol_short": 0.015, "vol_med": 0.010, "vol_long": 0.010}
    res_high = assess_risk_regime(normal_snapshot, [], base_config, context_high)
    assert res_high.volatility_regime == VolatilityRegime.HIGH
    assert res_high.regime == RiskRegime.HIGH_VOLATILITY

    context_spike = {"vol_short": 0.025, "vol_med": 0.010, "vol_long": 0.010}
    res_spike = assess_risk_regime(normal_snapshot, [], base_config, context_spike)
    assert res_spike.volatility_regime == VolatilityRegime.SPIKE
    assert res_spike.regime == RiskRegime.HIGH_VOLATILITY
    assert res_spike.status == RiskDecisionStatus.REJECT
    assert res_spike.reason_code == RiskReasonCode.DAILY_LOSS_BREACH


def test_assess_risk_regime_liquidity_regimes(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test thin and illiquid liquidity regimes."""
    # Thin context (ticks/min <= 10 or missing_bars >= 2)
    context_thin = {"tick_frequency": 8}
    res_thin = assess_risk_regime(normal_snapshot, [], base_config, context_thin)
    assert res_thin.liquidity_regime == LiquidityRegime.THIN
    assert res_thin.status == RiskDecisionStatus.APPROVE

    # Illiquid context (ticks/min <= 2 or missing_bars >= 5)
    context_illiq = {"tick_frequency": 1.5}
    res_illiq = assess_risk_regime(normal_snapshot, [], base_config, context_illiq)
    assert res_illiq.liquidity_regime == LiquidityRegime.ILLIQUID
    assert res_illiq.status == RiskDecisionStatus.REJECT
    assert res_illiq.reason_code == RiskReasonCode.STALE_EVIDENCE


def test_assess_risk_regime_news_blackout(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test news blackout window matches and classifications."""
    now = utc_now()
    calendar = [
        {"time": now - timedelta(minutes=10), "symbol": "EURUSD", "impact": "LOW"},
        {"time": now + timedelta(minutes=3), "symbol": "EURUSD", "impact": "HIGH"},
    ]

    context = {"symbol": "EURUSD", "news_blackout_mins": 5.0}

    # News event is within 3 minutes (which is <= 5 mins blackout),
    # impact high -> blackout
    res = assess_risk_regime(normal_snapshot, calendar, base_config, context)
    assert res.news_regime == NewsRegime.BLACKOUT
    assert res.regime == RiskRegime.NEWS_BLACKOUT
    assert res.status == RiskDecisionStatus.REJECT
    assert res.reason_code == RiskReasonCode.NEWS_BLACKOUT


def test_assess_risk_regime_rollover_blackout(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test rollover blackout window matching."""
    now = utc_now()
    # Rollover scheduled in 3 minutes
    roll_time = now + timedelta(minutes=3)
    rollover_snap = normal_snapshot.model_copy(update={"rollover_time": roll_time})

    context = {"rollover_blackout_before_mins": 5.0}
    res = assess_risk_regime(rollover_snap, [], base_config, context)
    assert res.rollover_regime == RolloverRegime.BLACKOUT
    assert res.regime == RiskRegime.ROLLOVER_BLACKOUT
    assert res.status == RiskDecisionStatus.REJECT
    assert res.reason_code == RiskReasonCode.ROLLOVER_BLACKOUT


def test_assess_risk_regime_live_missing_evidence(
    live_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test that live profiles fail closed when news calendar evidence is missing."""
    # live_config has allow_live_execution=True
    context = {"require_news_calendar": True}
    # Empty calendar_evidence list should trigger fail-closed block
    res = assess_risk_regime(normal_snapshot, [], live_config, context)
    assert res.status == RiskDecisionStatus.BLOCK
    assert res.regime == RiskRegime.STALE_DATA
    assert res.reason_code == RiskReasonCode.STALE_EVIDENCE


def test_calculate_rolling_volatility_logic(
    base_config: RiskConfig, normal_snapshot: MarketRiskSnapshot
) -> None:
    """Test rolling volatility calculation helper from historical price series."""
    # Generate 65 prices where we have flat volatility
    prices = [Decimal("100.0")] * 70
    context = {"historical_prices": prices}
    res = assess_risk_regime(normal_snapshot, [], base_config, context)
    assert (
        res.volatility_regime == VolatilityRegime.LOW
    )  # flat returns yield 0 vol, below ratio

    # Spiking prices
    spiking_prices = [Decimal("100.0")] * 60 + [
        Decimal("102.0"),
        Decimal("98.0"),
        Decimal("105.0"),
        Decimal("93.0"),
        Decimal("110.0"),
    ]
    context_spike = {"historical_prices": spiking_prices}
    res_spike = assess_risk_regime(normal_snapshot, [], base_config, context_spike)
    assert res_spike.volatility_regime == VolatilityRegime.SPIKE
    assert res_spike.status == RiskDecisionStatus.REJECT
