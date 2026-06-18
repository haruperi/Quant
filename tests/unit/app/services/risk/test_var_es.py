"""Unit tests for the Value-at-Risk (VaR) and Expected Shortfall (ES) Engine.

Verifies parametric/historical VaR, Expected Shortfall, covariance matrix
estimation, shrinkage methods, Euler risk decomposition, currency conversions,
and validation gates.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    ExpectedShortfallMethod,
    ExpectedShortfallSnapshot,
    PortfolioState,
    PositionState,
    RiskConfig,
    VaRMethod,
    VaRSnapshot,
    calculate_var_es_snapshots,
)
from app.services.risk.var_es import (
    calculate_covariance,
    calculate_covariance_matrix,
    calculate_ewma_covariance,
    calculate_historical_var_es,
    calculate_parametric_var_es,
    calculate_portfolio_volatility,
    calculate_risk_contributions,
    shrink_covariance_matrix,
    validate_covariance_matrix,
)
from app.utils.errors import ValidationError


@pytest.fixture
def sample_bars_a() -> list[dict[str, Any]]:
    """Provide historical bars for asset A with alternating returns."""
    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    bars = []
    price = 100.0
    for i in range(25):
        change = 1.0 if i % 2 == 0 else -1.5
        price += change
        bars.append(
            {
                "time": base_time + timedelta(minutes=i),
                "open": price - change,
                "close": price,
            }
        )
    return bars


@pytest.fixture
def sample_bars_b() -> list[dict[str, Any]]:
    """Provide historical bars for asset B with alternating returns."""
    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    bars = []
    price = 200.0
    for i in range(25):
        change = 2.0 if i % 2 == 0 else -3.0
        price += change
        bars.append(
            {
                "time": base_time + timedelta(minutes=i),
                "open": price - change,
                "close": price,
            }
        )
    return bars


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
def base_config() -> RiskConfig:
    """Provide base risk config."""
    return RiskConfig(
        profile_name="test_profile",
        correlation_threshold=Decimal("0.50"),
    )


def test_covariance_math() -> None:
    """Verify sample covariance and EWMA covariance calculations."""
    x = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01"), Decimal("0.03")]
    y = [Decimal("0.02"), Decimal("0.04"), Decimal("-0.02"), Decimal("0.06")]

    # Sample Covariance (perfectly correlated, y = 2*x)
    # Mean x = 0.0125, Mean y = 0.025
    # Covariance = 2 * Var(x)
    # Var(x) = sum(dx^2)/3 = (0.0025 + 0.000625 + 0.000025 + 0.005625) / 3 = 0.0003
    # Covariance = 0.0006
    cov = calculate_covariance(x, y)
    assert cov == pytest.approx(Decimal("0.0005833"), abs=1e-6)

    # EWMA Covariance
    cov_ewma = calculate_ewma_covariance(x, y, decay=Decimal("0.90"))
    assert isinstance(cov_ewma, Decimal)
    assert cov_ewma != Decimal("0.0")

    # Degenerate case < 2 samples
    assert calculate_covariance([Decimal("0.01")], [Decimal("0.02")]) == Decimal("0.0")
    assert calculate_ewma_covariance([Decimal("0.01")], [Decimal("0.02")]) == Decimal(
        "0.0"
    )


def test_covariance_matrix_and_shrinkage() -> None:
    """Verify covariance matrix calculation and diagonal shrinkage logic."""
    returns_db = {
        "A": [Decimal("0.01"), Decimal("-0.01"), Decimal("0.02")],
        "B": [Decimal("0.02"), Decimal("-0.02"), Decimal("0.04")],
    }
    matrix = calculate_covariance_matrix(returns_db, method="parametric")
    assert "A" in matrix
    assert "B" in matrix
    assert matrix["A"]["B"] == matrix["B"]["A"]

    # Shrinkage: delta = 0.20
    shrunk = shrink_covariance_matrix(matrix, shrinkage_intensity=Decimal("0.20"))
    assert shrunk["A"]["A"] == matrix["A"]["A"]  # Diagonal remains variance
    assert shrunk["B"]["B"] == matrix["B"]["B"]
    assert shrunk["A"]["B"] == matrix["A"]["B"] * Decimal("0.80")  # Off-diagonal shrunk

    # Validation
    validate_covariance_matrix(shrunk)


def test_validate_covariance_matrix_failure() -> None:
    """Verify validation exceptions for negative variance or asymmetric matrix."""
    bad_matrix = {
        "A": {"A": Decimal("-0.001"), "B": Decimal("0.0005")},
        "B": {"A": Decimal("0.0005"), "B": Decimal("0.001")},
    }
    with pytest.raises(ValidationError, match="negative variance"):
        validate_covariance_matrix(bad_matrix)

    asym_matrix = {
        "A": {"A": Decimal("0.001"), "B": Decimal("0.0005")},
        "B": {"A": Decimal("0.001"), "B": Decimal("0.001")},  # B["A"] = 0.001 != A["B"]
    }
    with pytest.raises(ValidationError, match="asymmetry detected"):
        validate_covariance_matrix(asym_matrix)


def test_portfolio_volatility_and_euler_contributions() -> None:
    """Verify portfolio volatility and component risk contribution Euler consistency."""
    weights = {"A": Decimal("0.60"), "B": Decimal("0.40")}
    matrix = {
        "A": {"A": Decimal("0.0004"), "B": Decimal("0.0002")},
        "B": {"A": Decimal("0.0002"), "B": Decimal("0.0009")},
    }
    vol = calculate_portfolio_volatility(weights, matrix)
    # Variance = (0.6)^2 * 0.0004 + (0.4)^2 * 0.0009 + 2 * (0.6) * (0.4) * 0.0002
    #          = 0.000144 + 0.000144 + 0.000096 = 0.000384
    # Vol = sqrt(0.000384) approx 0.0195959
    assert vol == pytest.approx(Decimal(str(math.sqrt(0.000384))), abs=1e-6)

    _mrc, crc = calculate_risk_contributions(
        weights=weights,
        matrix=matrix,
        portfolio_vol=vol,
        confidence=Decimal("0.95"),
        total_gross_exposure=Decimal("100000.00"),
    )
    # Euler's rule: sum(crc[i]) should sum to the absolute portfolio VaR
    var_abs = sum(crc.values())

    # Direct calculation of VaR
    z = Decimal(str(pytest.importorskip("statistics").NormalDist().inv_cdf(0.95)))
    expected_var = z * vol * Decimal("100000.00")
    assert var_abs == pytest.approx(expected_var, abs=1e-4)


def test_calculate_parametric_var_es() -> None:
    """Verify parametric VaR and Expected Shortfall analytical math."""
    weights = {"A": Decimal("1.0")}
    matrix = {"A": {"A": Decimal("0.0004")}}
    vol = Decimal("0.02")  # sqrt(0.0004)
    exposure = Decimal("50000.00")

    vol_res, var_val, es_val = calculate_parametric_var_es(
        weights=weights,
        matrix=matrix,
        confidence=Decimal("0.95"),
        total_gross_exposure=exposure,
    )
    assert vol_res == vol

    z = Decimal(str(pytest.importorskip("statistics").NormalDist().inv_cdf(0.95)))
    expected_var = z * vol * exposure
    assert var_val == pytest.approx(expected_var, abs=1e-4)
    assert es_val > var_val  # Tail risk should exceed threshold risk


def test_calculate_historical_var_es() -> None:
    """Verify historical percentile selection and tail average math."""
    aligned_returns = {
        "A": [
            Decimal("-0.05"),
            Decimal("-0.02"),
            Decimal("-0.01"),
            Decimal("0.03"),
            Decimal("0.05"),
        ]
    }
    weights = {"A": Decimal("1.0")}
    exposure = Decimal("100000.00")

    # Sorted returns: [-0.05, -0.02, -0.01, 0.03, 0.05] (n=5)
    # At confidence 0.80, (1 - 0.80) * 5 = 1st index
    # idx = 1 -> returns[1] = -0.02 -> VaR = 0.02 * 100k = 2000
    # Tail returns are returns[:2] = [-0.05, -0.02]
    # Average = -(-0.07)/2 = 0.035 -> ES = 3.5% * 100k = 3500
    var_val, es_val = calculate_historical_var_es(
        aligned_returns=aligned_returns,
        weights=weights,
        confidence=Decimal("0.80"),
        total_gross_exposure=exposure,
    )
    assert var_val == Decimal("2000.00")
    assert es_val == Decimal("3500.00")


def test_calculate_var_es_snapshots_full_flow(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    sample_bars_a: list[dict[str, Any]],
    sample_bars_b: list[dict[str, Any]],
) -> None:
    """Test full calculator integration flow from portfolio and market data context."""
    # Setup open position
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1000"),
            floating_pnl=Decimal("0.0"),
            margin_required=Decimal("1000.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
    ]

    market_context = {
        "EURUSD_contract_size": 100000.0,
        "GBPUSD_contract_size": 100000.0,
        "conversion_rates": {
            "EUR": 1.10,
            "GBP": 1.25,
            "USD": 1.0,
        },
        "market_data": {
            "EURUSD": sample_bars_a,
            "GBPUSD": sample_bars_b,
        },
    }

    # Verify parametric snapshots
    var_snap, es_snap = calculate_var_es_snapshots(
        portfolio_state=base_portfolio,
        proposed_trade=None,
        market_context=market_context,
        config=base_config,
        min_samples=10,
        exclude_last=False,
    )

    assert isinstance(var_snap, VaRSnapshot)
    assert isinstance(es_snap, ExpectedShortfallSnapshot)
    assert var_snap.exposure == Decimal("110000.00")  # EURUSD 1 lot gross exposure
    assert var_snap.result > 0
    assert es_snap.average_tail_loss > var_snap.result

    # Verify historical snapshots
    var_hist, es_hist = calculate_var_es_snapshots(
        portfolio_state=base_portfolio,
        proposed_trade=None,
        market_context=market_context,
        config=base_config,
        var_method=VaRMethod.HISTORICAL,
        es_method=ExpectedShortfallMethod.HISTORICAL,
        min_samples=10,
        exclude_last=False,
    )
    assert var_hist.result > 0
    assert es_hist.average_tail_loss > var_hist.result


def test_calculate_var_es_snapshots_insufficient_samples(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    sample_bars_a: list[dict[str, Any]],
) -> None:
    """Verify that insufficient historical return data raises ValidationError."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1000"),
            floating_pnl=Decimal("0.0"),
            margin_required=Decimal("1000.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
    ]
    # We only have 25 bars in sample_bars_a
    # If min_samples = 50, it must fail closed
    market_context = {
        "EURUSD_contract_size": 100000.0,
        "market_data": {
            "EURUSD": sample_bars_a,
        },
    }
    with pytest.raises(ValidationError, match="Insufficient aligned samples"):
        calculate_var_es_snapshots(
            portfolio_state=base_portfolio,
            proposed_trade=None,
            market_context=market_context,
            config=base_config,
            min_samples=50,
        )
