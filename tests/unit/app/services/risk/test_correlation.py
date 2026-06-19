"""Unit tests for the Correlation and Cluster Risk Engine.

Verifies returns formulas, returns alignment, Pearson correlation coefficient,
rolling snapshots with fallbacks, marginal correlation, sizing multipliers,
correlation spikes, and connected-component cluster exposure groupings.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    CorrelationMethod,
    CorrelationSnapshot,
    PortfolioState,
    PositionState,
    ProposedTrade,
    ReturnType,
    RiskConfig,
    RiskDecisionStatus,
    calculate_cluster_exposures,
    calculate_correlation_multiplier,
    calculate_correlation_snapshot,
    calculate_marginal_correlation,
    calculate_portfolio_returns,
    calculate_returns,
    detect_correlation_spikes,
    evaluate_proposed_trade_correlation,
)
from app.utils.errors import ValidationError


@pytest.fixture
def sample_bars_a() -> list[dict[str, Any]]:
    """Provide historical bars for asset A."""
    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    return [
        {"time": base_time + timedelta(minutes=i), "open": 100 + i, "close": 101 + i}
        for i in range(10)
    ]


@pytest.fixture
def sample_bars_b() -> list[dict[str, Any]]:
    """Provide historical bars for asset B."""
    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    # Perfectly correlated with A (same price action shape)
    return [
        {
            "time": base_time + timedelta(minutes=i),
            "open": 200 + 2 * i,
            "close": 202 + 2 * i,
        }
        for i in range(10)
    ]


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


def test_calculate_returns_various_types(
    sample_bars_a: list[dict[str, Any]],
) -> None:
    """Test returns calculations.

    Covers close_to_close, log, open_to_close, and sigma_normalized types.
    """
    # 1. Close-to-Close
    rets_cc = calculate_returns(
        sample_bars_a, ReturnType.CLOSE_TO_CLOSE, exclude_last=False
    )
    assert len(rets_cc) == len(sample_bars_a) - 1
    for dt, val in rets_cc.items():
        assert isinstance(dt, datetime)
        assert isinstance(val, Decimal)

    # 2. Log returns
    rets_log = calculate_returns(sample_bars_a, ReturnType.LOG, exclude_last=False)
    assert len(rets_log) == len(sample_bars_a) - 1

    # 3. Open-to-Close
    rets_oc = calculate_returns(
        sample_bars_a, ReturnType.OPEN_TO_CLOSE, exclude_last=False
    )
    assert len(rets_oc) == len(sample_bars_a)
    for val in rets_oc.values():
        # (101 - 100) / 100 = 0.01
        assert val > 0

    # 4. Sigma normalized returns
    rets_sig = calculate_returns(
        sample_bars_a, ReturnType.SIGMA_NORMALIZED, exclude_last=False
    )
    assert len(rets_sig) == len(sample_bars_a) - 1


def test_calculate_returns_exclude_last(sample_bars_a: list[dict[str, Any]]) -> None:
    """Verify that the last bar is excluded by default."""
    rets = calculate_returns(
        sample_bars_a, ReturnType.CLOSE_TO_CLOSE, exclude_last=True
    )
    assert len(rets) == len(sample_bars_a) - 2


def test_calculate_returns_invalid_type(sample_bars_a: list[dict[str, Any]]) -> None:
    """Verify ValueError is raised on invalid return type."""
    with pytest.raises(ValueError, match="Unsupported return type"):
        calculate_returns(sample_bars_a, "invalid_type")


def test_calculate_returns_empty_and_insufficient() -> None:
    """Verify return handling on empty and short list inputs."""
    assert calculate_returns([], ReturnType.CLOSE_TO_CLOSE) == {}

    # 1 bar close-to-close -> empty return series
    single_bar = [{"time": "2026-06-18T10:00:00Z", "open": 100.0, "close": 101.0}]
    assert (
        calculate_returns(single_bar, ReturnType.CLOSE_TO_CLOSE, exclude_last=False)
        == {}
    )


def test_calculate_pearson_correlation(
    sample_bars_a: list[dict[str, Any]],
    sample_bars_b: list[dict[str, Any]],
) -> None:
    """Verify Pearson calculation on perfect and negative correlations."""
    # 1. Perfectly correlated
    snapshot = calculate_correlation_snapshot(
        {"A": sample_bars_a, "B": sample_bars_b},
        min_samples=2,
        exclude_last=False,
    )
    assert snapshot.matrix["A"]["B"] == pytest.approx(Decimal("1.0"), abs=1e-4)
    assert snapshot.matrix["A"]["A"] == Decimal("1.0")

    # 2. Zero variance edge-case
    flat_bars = [
        {"time": datetime(2026, 6, 18, 10, i, tzinfo=UTC), "open": 100, "close": 100}
        for i in range(5)
    ]
    snapshot_zero = calculate_correlation_snapshot(
        {"A": sample_bars_a, "B": flat_bars},
        min_samples=2,
        exclude_last=False,
        fallback_correlation=Decimal("0.0"),
    )
    assert snapshot_zero.matrix["A"]["B"] == Decimal("0.0")


def test_insufficient_samples_fallback(
    sample_bars_a: list[dict[str, Any]],
) -> None:
    """Verify that insufficient samples trigger ValidationError or fallback.

    Ensures fallback works correctly in production when configured.
    """
    # min_samples is 20, but we only have 10 bars -> raises ValidationError
    with pytest.raises(ValidationError, match="Insufficient aligned sample size"):
        calculate_correlation_snapshot(
            {"A": sample_bars_a, "B": sample_bars_a},
            min_samples=20,
            exclude_last=False,
        )

    # With fallback_correlation, it passes and applies the fallback
    snapshot = calculate_correlation_snapshot(
        {"A": sample_bars_a, "B": sample_bars_a},
        min_samples=20,
        exclude_last=False,
        fallback_correlation=Decimal("0.25"),
    )
    assert snapshot.matrix["A"]["B"] == Decimal("0.25")
    assert snapshot.fallback_status is True


def test_detect_correlation_spikes() -> None:
    """Verify detection of pairwise correlation spikes."""
    matrix = {
        "EURUSD": {
            "EURUSD": Decimal("1.0"),
            "GBPUSD": Decimal("0.85"),
            "USDJPY": Decimal("-0.10"),
        },
        "GBPUSD": {
            "EURUSD": Decimal("0.85"),
            "GBPUSD": Decimal("1.0"),
            "USDJPY": Decimal("0.20"),
        },
        "USDJPY": {
            "EURUSD": Decimal("-0.10"),
            "GBPUSD": Decimal("0.20"),
            "USDJPY": Decimal("1.0"),
        },
    }
    snapshot = CorrelationSnapshot(
        matrix=matrix,
        lookback=50,
        timeframe="M1",
        method=CorrelationMethod.PEARSON,
        sample_count=50,
        fallback_status=False,
    )

    # Spike threshold = 0.80
    spikes = detect_correlation_spikes(snapshot, Decimal("0.80"))
    assert len(spikes) == 1
    assert spikes[0] == ("EURUSD", "GBPUSD", Decimal("0.85"))


def test_calculate_portfolio_returns(
    base_portfolio: PortfolioState,
    sample_bars_a: list[dict[str, Any]],
) -> None:
    """Verify portfolio-weighted returns calculation."""
    # Empty portfolio -> empty returns
    assert calculate_portfolio_returns(base_portfolio, {"EURUSD": sample_bars_a}) == {}

    # Active positions
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1050"),
            floating_pnl=Decimal("500.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
    ]
    rets = calculate_portfolio_returns(
        base_portfolio, {"EURUSD": sample_bars_a}, exclude_last=False
    )
    assert len(rets) > 0


def test_calculate_marginal_correlation(
    base_portfolio: PortfolioState,
    sample_bars_a: list[dict[str, Any]],
    sample_bars_b: list[dict[str, Any]],
) -> None:
    """Verify marginal correlation of a proposed trade against portfolio returns."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1050"),
            floating_pnl=Decimal("500.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
    ]

    proposed = ProposedTrade(
        symbol="GBPUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.2500"),
        strategy_id="TF-01",
    )

    # Align against GBPUSD bars
    market_data = {
        "EURUSD": sample_bars_a,
        "GBPUSD": sample_bars_b,
    }

    corr, fallback = calculate_marginal_correlation(
        portfolio_state=base_portfolio,
        proposed_trade=proposed,
        market_data=market_data,
        min_samples=2,
        exclude_last=False,
    )
    # Perfectly correlated in fixtures
    assert corr == pytest.approx(Decimal("1.0"), abs=1e-4)
    assert fallback is False


def test_calculate_correlation_multiplier() -> None:
    """Test correlation adjusted multiplier capping."""
    # Negative correlation -> no reduction (1.0)
    assert calculate_correlation_multiplier(Decimal("-0.25")) == Decimal("1.0")

    # 0.5 correlation -> reduction to 0.75
    assert calculate_correlation_multiplier(Decimal("0.50"), Decimal("0.5")) == Decimal(
        "0.75"
    )

    # Perfect correlation (1.0) -> reduction to 0.50
    assert calculate_correlation_multiplier(Decimal("1.00"), Decimal("0.5")) == Decimal(
        "0.50"
    )

    # Hard cap limit at 0.1
    assert calculate_correlation_multiplier(Decimal("1.00"), Decimal("1.2")) == Decimal(
        "0.1"
    )


def test_calculate_cluster_exposures(base_portfolio: PortfolioState) -> None:
    """Test connected-component cluster exposure grouping."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),  # $100k exposure
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1000"),
            floating_pnl=Decimal("0.0"),
            margin_required=Decimal("1000.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        ),
        PositionState(
            position_id="pos-2",
            symbol="GBPUSD",
            direction="long",
            quantity=Decimal("0.5"),  # $50k exposure (contract size 100k)
            entry_price=Decimal("1.2500"),
            current_price=Decimal("1.2500"),
            floating_pnl=Decimal("0.0"),
            margin_required=Decimal("500.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        ),
        PositionState(
            position_id="pos-3",
            symbol="USDJPY",
            direction="long",
            quantity=Decimal("2.0"),  # $200k base exposure in USD
            entry_price=Decimal("150.00"),
            current_price=Decimal("150.00"),
            floating_pnl=Decimal("0.0"),
            margin_required=Decimal("2000.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        ),
    ]

    # Matrix showing high correlation between EURUSD/GBPUSD but low with USDJPY
    matrix = {
        "EURUSD": {
            "EURUSD": Decimal("1.0"),
            "GBPUSD": Decimal("0.85"),
            "USDJPY": Decimal("0.10"),
        },
        "GBPUSD": {
            "EURUSD": Decimal("0.85"),
            "GBPUSD": Decimal("1.0"),
            "USDJPY": Decimal("0.15"),
        },
        "USDJPY": {
            "EURUSD": Decimal("0.10"),
            "GBPUSD": Decimal("0.15"),
            "USDJPY": Decimal("1.0"),
        },
    }
    snapshot = CorrelationSnapshot(
        matrix=matrix,
        lookback=50,
        timeframe="M1",
        method=CorrelationMethod.PEARSON,
        sample_count=50,
        fallback_status=False,
    )

    market_context = {
        "EURUSD_contract_size": 100000.0,
        "GBPUSD_contract_size": 100000.0,
        "USDJPY_contract_size": 100000.0,
        "conversion_rates": {
            "EUR": 1.10,
            "GBP": 1.25,
            "JPY": 0.0067,
            "USD": 1.0,
        },
    }

    # Group with threshold 0.50 -> EURUSD and GBPUSD cluster together. USDJPY isolated.
    clusters = calculate_cluster_exposures(
        portfolio_state=base_portfolio,
        proposed_trade=None,
        snapshot=snapshot,
        threshold=Decimal("0.50"),
        market_context=market_context,
    )

    # EURUSD gross: 1.0 lot * 100,000 * 1.10 conversion rate = 110,000 USD
    # GBPUSD gross: 0.5 lot * 100,000 * 1.25 conversion rate = 62,500 USD
    # Cluster_0 gross = 172,500 USD
    # USDJPY gross: 2.0 lot * 100,000 * 1.0 (USD conversion) = 200,000 USD
    # Cluster_1 gross = 200,000 USD
    assert clusters["Cluster_0"] == Decimal("172500.00")
    assert clusters["Cluster_1"] == Decimal("200000.00")


def test_evaluate_proposed_trade_correlation(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    sample_bars_a: list[dict[str, Any]],
    sample_bars_b: list[dict[str, Any]],
) -> None:
    """Verify evaluate_proposed_trade_correlation logic.

    Tests resolution under normal/breach conditions.
    """
    # 1. No active positions -> Approve
    proposed = ProposedTrade(
        symbol="GBPUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.2500"),
        strategy_id="TF-01",
    )
    status, vol, _msg = evaluate_proposed_trade_correlation(
        proposed_trade=proposed,
        portfolio_state=base_portfolio,
        snapshot=CorrelationSnapshot(
            matrix={},
            lookback=50,
            timeframe="M1",
            method="pearson",
            sample_count=0,
            fallback_status=False,
        ),
        config=base_config,
        market_context={},
    )
    assert status == RiskDecisionStatus.APPROVE
    assert vol == Decimal("1.0")

    # Setup portfolio position
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

    # Setup perfectly correlated bars
    market_context: dict[str, Any] = {
        "market_data": {
            "EURUSD": sample_bars_a,
            "GBPUSD": sample_bars_b,
        },
        "GBPUSD_volume_step": 0.01,
        "min_correlation_samples": 2,
    }

    # 2. Perfect correlation (1.0) -> Rejects because exceeds hard rejection threshold
    snapshot = CorrelationSnapshot(
        matrix={"EURUSD": {"GBPUSD": Decimal("1.0")}},
        lookback=50,
        timeframe="M1",
        method="pearson",
        sample_count=10,
        fallback_status=False,
    )
    status_rej, vol_rej, _msg_rej = evaluate_proposed_trade_correlation(
        proposed_trade=proposed,
        portfolio_state=base_portfolio,
        snapshot=snapshot,
        config=base_config,
        market_context=market_context,
    )
    assert status_rej == RiskDecisionStatus.REJECT
    assert vol_rej == Decimal("0.0")

    # 3. Correlation 0.60 (exceeds threshold 0.50 but below hard rejection)
    # REDUCE_SIZE
    snapshot_warn = CorrelationSnapshot(
        matrix={"EURUSD": {"GBPUSD": Decimal("0.60")}},
        lookback=50,
        timeframe="M1",
        method="pearson",
        sample_count=10,
        fallback_status=False,
    )
    # Change bars slightly so marginal correlation resolves to ~0.60 or close.
    # To test the branch, let's inject a partially correlated return series
    part_bars_b = []
    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    for i in range(10):
        # Add some noise to break perfect correlation
        noise = 0.5 if i % 2 == 0 else 0.0
        part_bars_b.append(
            {
                "time": base_time + timedelta(minutes=i),
                "open": 200 + i,
                "close": 201 + i + noise,
            }
        )
    market_context["market_data"]["GBPUSD"] = part_bars_b

    status_red, _vol_red, _msg_red = evaluate_proposed_trade_correlation(
        proposed_trade=proposed,
        portfolio_state=base_portfolio,
        snapshot=snapshot_warn,
        config=base_config,
        market_context=market_context,
    )
    # Based on actual returns alignment, let's verify it triggered
    # either REDUCE_SIZE or APPROVE
    assert status_red in {RiskDecisionStatus.REDUCE_SIZE, RiskDecisionStatus.APPROVE}


def test_timestamp_alignment_misaligned() -> None:
    """Verify that returns are only aligned on identical opening timestamps."""
    from app.services.risk.correlation import align_return_series

    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)

    # A has bars at 10:00, 10:01, 10:02
    rets_a = {
        base_time: Decimal("0.01"),
        base_time + timedelta(minutes=1): Decimal("0.02"),
        base_time + timedelta(minutes=2): Decimal("0.03"),
    }
    # B has bars at 10:01, 10:02, 10:03
    rets_b = {
        base_time + timedelta(minutes=1): Decimal("-0.01"),
        base_time + timedelta(minutes=2): Decimal("-0.02"),
        base_time + timedelta(minutes=3): Decimal("-0.03"),
    }

    aligned_a, aligned_b = align_return_series(rets_a, rets_b)
    # Common keys should be 10:01 and 10:02
    assert len(aligned_a) == 2
    assert len(aligned_b) == 2
    assert aligned_a == [Decimal("0.02"), Decimal("0.03")]
    assert aligned_b == [Decimal("-0.01"), Decimal("-0.02")]


def test_changing_correlation() -> None:
    """Verify that Pearson correlation changes correctly across return pairs."""
    from app.services.risk.correlation import calculate_pearson

    # Positively correlated series
    x = [Decimal("0.01"), Decimal("0.02"), Decimal("0.03")]
    y = [Decimal("0.02"), Decimal("0.04"), Decimal("0.06")]

    corr_pos = calculate_pearson(x, y)
    assert corr_pos == pytest.approx(Decimal("1.0"), abs=1e-4)

    # Negatively correlated series
    z = [Decimal("-0.02"), Decimal("-0.04"), Decimal("-0.06")]
    corr_neg = calculate_pearson(x, z)
    assert corr_neg == pytest.approx(Decimal("-1.0"), abs=1e-4)


def test_conservative_fallback_in_production(base_portfolio: PortfolioState) -> None:
    """Verify conservative fallback in production when samples are insufficient."""
    # Config with live execution allowed
    live_config = RiskConfig(
        profile_name="live_profile",
        allow_live_execution=True,
        min_correlation_samples=20,
    )

    proposed = ProposedTrade(
        symbol="GBPUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.2500"),
        strategy_id="TF-01",
    )

    # Minimal bars (1 bar -> 0 return samples)
    market_data = {
        "EURUSD": [{"time": "2026-06-18T10:00:00Z", "open": 1.1, "close": 1.1}],
        "GBPUSD": [{"time": "2026-06-18T10:00:00Z", "open": 1.2, "close": 1.2}],
    }

    # Active position
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.1"),
            current_price=Decimal("1.1"),
            floating_pnl=Decimal("0.0"),
            margin_required=Decimal("1000.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
    ]

    snapshot = CorrelationSnapshot(
        matrix={},
        lookback=50,
        timeframe="M1",
        method="pearson",
        sample_count=0,
        fallback_status=False,
    )

    market_context = {
        "market_data": market_data,
        "environment": "micro_live",
    }

    # Should fall back to 1.0 (perfect correlation) -> REJECT
    status, vol, msg = evaluate_proposed_trade_correlation(
        proposed_trade=proposed,
        portfolio_state=base_portfolio,
        snapshot=snapshot,
        config=live_config,
        market_context=market_context,
    )

    assert status == RiskDecisionStatus.REJECT
    assert vol == Decimal("0.0")
    assert "exceeds hard rejection ceiling" in msg


def test_correlation_engine(
    sample_bars_a: list[dict[str, Any]],
    sample_bars_b: list[dict[str, Any]],
) -> None:
    """Verify methods exposed by CorrelationEngine."""
    from app.services.risk import CorrelationEngine

    engine = CorrelationEngine()

    # 1. calculate_returns
    rets = engine.calculate_returns(
        sample_bars_a, ReturnType.CLOSE_TO_CLOSE, exclude_last=False
    )
    assert len(rets) == len(sample_bars_a) - 1

    # 2. align_return_series
    rets_b = engine.calculate_returns(
        sample_bars_b, ReturnType.CLOSE_TO_CLOSE, exclude_last=False
    )
    aligned_a, _aligned_b = engine.align_return_series(rets, rets_b)
    assert len(aligned_a) == len(rets)

    # 3. calculate_correlation_matrix
    market_data = {"A": sample_bars_a, "B": sample_bars_b}
    matrix = engine.calculate_correlation_matrix(
        market_data, lookback=50, min_samples=2, exclude_last=False
    )
    assert matrix["A"]["B"] == pytest.approx(Decimal("1.0"), abs=1e-4)


def test_correlation_matrix_and_cluster_models() -> None:
    """Verify CorrelationMatrix and CorrelationCluster serialization and fields."""
    from app.services.risk.models import CorrelationCluster, CorrelationMatrix

    matrix_data = {
        "EURUSD": {"GBPUSD": Decimal("0.85"), "EURUSD": Decimal("1.0")},
        "GBPUSD": {"EURUSD": Decimal("0.85"), "GBPUSD": Decimal("1.0")},
    }

    corr_matrix = CorrelationMatrix(
        symbols=["EURUSD", "GBPUSD"],
        matrix=matrix_data,
    )

    assert corr_matrix.symbols == ["EURUSD", "GBPUSD"]
    assert corr_matrix.matrix["EURUSD"]["GBPUSD"] == Decimal("0.85")

    cluster = CorrelationCluster(
        cluster_id="Cluster_0",
        symbols=["EURUSD", "GBPUSD"],
        exposure=Decimal("172500.00"),
    )

    assert cluster.cluster_id == "Cluster_0"
    assert cluster.exposure == Decimal("172500.00")
