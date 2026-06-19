"""Unit tests for strategy capital allocation governance.

Verifies parity calculators, regime weighting, drawdown adjustments,
and limit validations for proposed allocations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    AllocationMethod,
    AllocationReviewRequest,
    PortfolioState,
    ProposedAllocation,
    RiskAllocator,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
    calculate_correlation_adjusted_budget,
    calculate_equal_risk_budget,
    calculate_regime_weighted_budget,
    calculate_volatility_parity_budget,
)
from app.services.risk.allocation import (
    apply_drawdown_adjustment,
    apply_regime_weighting,
    correlation_adjusted_risk_parity_allocation,
    equal_risk_allocation,
    verify_allocation_limits,
    volatility_parity_allocation,
)


@pytest.fixture
def base_portfolio() -> PortfolioState:
    """Fixture for baseline PortfolioState."""
    return PortfolioState(
        account_id="acc-alloc",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[],
        orders=[],
        strategy_allocations={
            "strat1": Decimal("3000.00"),
            "strat2": Decimal("3000.00"),
        },
    )


@pytest.fixture
def base_config() -> RiskConfig:
    """Fixture for baseline RiskConfig with custom allocation settings."""
    return RiskConfig(
        profile_name="default",
        allocation_method="correlation_adjusted_parity",
        max_allocation_increase_pct=Decimal("0.20"),
        max_strategy_allocation_pct=Decimal("0.50"),
        min_backtest_trades=100,
        min_backtest_sharpe=Decimal("1.5"),
    )


def test_equal_risk_allocation() -> None:
    """Verify equal-risk allocation divides budget evenly."""
    strategies = ["strat1", "strat2", "strat3", "strat4"]
    budget = Decimal("1000.00")
    allocs = equal_risk_allocation(strategies, budget)
    assert len(allocs) == 4
    for strat in strategies:
        assert allocs[strat] == Decimal("250.00")

    # Empty inputs
    assert equal_risk_allocation([], budget) == {}
    assert equal_risk_allocation(strategies, Decimal("0.00")) == {
        "strat1": Decimal("0.00"),
        "strat2": Decimal("0.00"),
        "strat3": Decimal("0.00"),
        "strat4": Decimal("0.00"),
    }


def test_volatility_parity_allocation() -> None:
    """Verify volatility parity allocates inversely proportional to volatility."""
    strategies = ["strat1", "strat2"]
    vols = {"strat1": Decimal("0.01"), "strat2": Decimal("0.03")}
    budget = Decimal("1000.00")

    allocs = volatility_parity_allocation(strategies, vols, budget)
    # inv_vol1 = 100, inv_vol2 = 33.333... sum = 133.333...
    # weight1 = 100/133.333 = 0.75, weight2 = 0.25
    assert allocs["strat1"] == pytest.approx(Decimal("750.00"))
    assert allocs["strat2"] == pytest.approx(Decimal("250.00"))

    # Fallback to equal risk if all vols are 0 or missing
    allocs_fallback = volatility_parity_allocation(strategies, {}, budget)
    assert allocs_fallback["strat1"] == Decimal("500.00")
    assert allocs_fallback["strat2"] == Decimal("500.00")


def test_correlation_adjusted_risk_parity_allocation() -> None:
    """Verify correlation adjusted parity calculates weights correctly."""
    strategies = ["strat1", "strat2", "strat3"]
    vols = {
        "strat1": Decimal("0.02"),
        "strat2": Decimal("0.02"),
        "strat3": Decimal("0.02"),
    }
    # strat1 is highly correlated with others (0.8),
    # strat2 and strat3 are uncorrelated (0.0)
    correlation_matrix = {
        "strat1": {"strat2": Decimal("0.8"), "strat3": Decimal("0.8")},
        "strat2": {"strat1": Decimal("0.8"), "strat3": Decimal("0.0")},
        "strat3": {"strat1": Decimal("0.8"), "strat2": Decimal("0.0")},
    }
    budget = Decimal("1000.00")

    allocs = correlation_adjusted_risk_parity_allocation(
        strategies, vols, correlation_matrix, budget
    )
    # strat1: avg_corr = 0.8, denom = 0.02 * (1 + 0.8) = 0.036, inv = 27.78
    # strat2: avg_corr = 0.4, denom = 0.02 * (1 + 0.4) = 0.028, inv = 35.71
    # strat3: avg_corr = 0.4, denom = 0.02 * (1 + 0.4) = 0.028, inv = 35.71
    # strat1 should get less budget than strat2 and strat3 because of higher correlation
    assert allocs["strat1"] < allocs["strat2"]
    assert allocs["strat2"] == pytest.approx(allocs["strat3"])


def test_apply_regime_weighting_and_drawdown() -> None:
    """Verify multipliers are applied correctly."""
    allocs = {"strat1": Decimal("500.00"), "strat2": Decimal("500.00")}

    scaled = apply_regime_weighting(allocs, Decimal("0.5"))
    assert scaled["strat1"] == Decimal("250.00")
    assert scaled["strat2"] == Decimal("250.00")

    drawdown_mults = {"strat1": Decimal("0.8"), "strat2": Decimal("1.0")}
    adjusted = apply_drawdown_adjustment(allocs, drawdown_mults)
    assert adjusted["strat1"] == Decimal("400.00")
    assert adjusted["strat2"] == Decimal("500.00")


def test_verify_allocation_limits_basic(
    base_portfolio: PortfolioState, base_config: RiskConfig
) -> None:
    """Verify verification logic for basic pass/fail limits."""
    # Pass path: proposed allocations within limits
    proposal = ProposedAllocation(
        allocations={"strat1": Decimal("3000.00"), "strat2": Decimal("3000.00")},
        as_of=datetime.now(UTC),
    )
    res = verify_allocation_limits(base_portfolio, proposal, {}, base_config)
    assert res.status == RiskDecisionStatus.APPROVE
    assert not res.breached

    # Breach total equity budget
    proposal_huge = ProposedAllocation(
        allocations={"strat1": Decimal("6000.00"), "strat2": Decimal("6000.00")},
        as_of=datetime.now(UTC),
    )
    res_huge = verify_allocation_limits(base_portfolio, proposal_huge, {}, base_config)
    assert res_huge.status == RiskDecisionStatus.REJECT
    assert res_huge.reason_code == RiskReasonCode.MARGIN_BREACH

    # Breach individual strategy allocation cap (> 50% of equity)
    proposal_single_huge = ProposedAllocation(
        allocations={"strat1": Decimal("5500.00"), "strat2": Decimal("1000.00")},
        as_of=datetime.now(UTC),
    )
    res_single = verify_allocation_limits(
        base_portfolio, proposal_single_huge, {}, base_config
    )
    assert res_single.status == RiskDecisionStatus.REJECT
    assert res_single.reason_code == RiskReasonCode.ALLOCATION_LIMIT_BREACH


def test_verify_allocation_limits_increase_governance(
    base_portfolio: PortfolioState, base_config: RiskConfig
) -> None:
    """Verify performance evidence checks and governed approval token requirements."""
    # Propose allocation increase: strat1 increases from 3000 to 4000 (+33.3% > +20%)
    proposal = ProposedAllocation(
        allocations={"strat1": Decimal("4000.00"), "strat2": Decimal("3000.00")},
        as_of=datetime.now(UTC),
    )

    # A. Missing evidence
    res_no_evidence = verify_allocation_limits(
        base_portfolio, proposal, {}, base_config
    )
    assert res_no_evidence.status == RiskDecisionStatus.NEEDS_MORE_EVIDENCE
    assert res_no_evidence.reason_code == RiskReasonCode.STALE_EVIDENCE

    # B. Insufficient evidence stats
    market_context: dict[str, Any] = {
        "strategy_evidence": {
            "strat1": {
                "trade_count": 50,  # Required 100
                "sharpe_ratio": 1.8,
            }
        }
    }
    res_bad_stats = verify_allocation_limits(
        base_portfolio, proposal, market_context, base_config
    )
    assert res_bad_stats.status == RiskDecisionStatus.NEEDS_MORE_EVIDENCE
    assert "Insufficient trades" in res_bad_stats.message

    # C. Sufficient evidence stats but exceeds increase threshold
    # -> Requires approval token
    market_context["strategy_evidence"]["strat1"]["trade_count"] = 120
    res_need_approval = verify_allocation_limits(
        base_portfolio, proposal, market_context, base_config
    )
    assert res_need_approval.status == RiskDecisionStatus.NEEDS_APPROVAL
    assert res_need_approval.reason_code == RiskReasonCode.APPROVAL_REQUIRED

    # D. Valid approval token provided -> Passes
    market_context["approval_token_valid"] = True
    res_approved = verify_allocation_limits(
        base_portfolio, proposal, market_context, base_config
    )
    assert res_approved.status == RiskDecisionStatus.APPROVE
    assert not res_approved.breached


def test_budget_calculation_functions() -> None:
    """Test standalone budget calculation functions."""
    strategies = ["strat1", "strat2"]
    volatilities = {"strat1": Decimal("0.02"), "strat2": Decimal("0.02")}
    correlation_matrix = {
        "strat1": {"strat2": Decimal("0.5")},
        "strat2": {"strat1": Decimal("0.5")},
    }
    budget = Decimal("1000.00")

    equal = calculate_equal_risk_budget(strategies, budget)
    assert equal["strat1"] == Decimal("500.00")

    vol = calculate_volatility_parity_budget(strategies, volatilities, budget)
    assert vol["strat1"] == Decimal("500.00")

    corr = calculate_correlation_adjusted_budget(
        strategies, volatilities, correlation_matrix, budget
    )
    assert corr["strat1"] == Decimal("500.00")

    regime = calculate_regime_weighted_budget(
        strategies, volatilities, correlation_matrix, budget, Decimal("0.8")
    )
    assert regime["strat1"] == Decimal("400.00")


def test_risk_allocator_calculate_allocated_budget(base_config: RiskConfig) -> None:
    """Test RiskAllocator.calculate_allocated_budget options."""
    allocator = RiskAllocator(base_config)
    strategies = ["strat1", "strat2"]
    volatilities = {"strat1": Decimal("0.02"), "strat2": Decimal("0.02")}
    correlation_matrix = {
        "strat1": {"strat2": Decimal("0.5")},
        "strat2": {"strat1": Decimal("0.5")},
    }
    drawdown_multipliers = {"strat1": Decimal("0.5"), "strat2": Decimal("1.0")}
    market_context: dict[str, Any] = {
        "volatilities": volatilities,
        "correlation_matrix": correlation_matrix,
        "regime_multiplier": Decimal("0.5"),
        "strategy_drawdown_multipliers": drawdown_multipliers,
    }
    budget = Decimal("1000.00")

    # Equal risk
    allocs = allocator.calculate_allocated_budget(
        strategies, budget, market_context, AllocationMethod.EQUAL_RISK
    )
    assert allocs["strat1"] == Decimal("500.00")

    # Volatility parity
    allocs = allocator.calculate_allocated_budget(
        strategies, budget, market_context, AllocationMethod.VOLATILITY_PARITY
    )
    assert allocs["strat1"] == Decimal("500.00")

    # Drawdown adjusted
    allocs = allocator.calculate_allocated_budget(
        strategies, budget, market_context, AllocationMethod.DRAWDOWN_ADJUSTED
    )
    assert allocs["strat1"] == Decimal("250.00")
    assert allocs["strat2"] == Decimal("500.00")

    # Default live logic
    market_context["mode"] = "full_live"
    base_config.allocation_method = "default"
    allocs = allocator.calculate_allocated_budget(
        strategies, budget, market_context, None
    )
    assert allocs["strat1"] == Decimal("500.00")


def test_risk_allocator_review_limits(
    base_portfolio: PortfolioState, base_config: RiskConfig
) -> None:
    """Test advanced limit validation rules."""
    allocator = RiskAllocator(base_config)
    proposal = ProposedAllocation(
        allocations={"strat1": Decimal("3000.00"), "strat2": Decimal("3000.00")},
        as_of=datetime.now(UTC),
    )

    # 1. Test symbol budget limits
    market_context: dict[str, Any] = {
        "strategy_to_symbols": {"strat1": ["EURUSD"], "strat2": ["GBPUSD"]},
        "symbol_budget_limit": {"EURUSD": Decimal("2000.00")},
    }
    req = AllocationReviewRequest(
        portfolio_state=base_portfolio,
        proposal=proposal,
        market_context=market_context,
        config=base_config,
    )
    res = allocator.review_allocation(req)
    assert res.status == RiskDecisionStatus.REJECT
    assert "EURUSD" in res.message

    # 2. Test currency budget limits
    market_context = {
        "strategy_to_currencies": {"strat1": "EUR", "strat2": "GBP"},
        "currency_budget_limit": {"EUR": Decimal("2000.00")},
    }
    req = AllocationReviewRequest(
        portfolio_state=base_portfolio,
        proposal=proposal,
        market_context=market_context,
        config=base_config,
    )
    res = allocator.review_allocation(req)
    assert res.status == RiskDecisionStatus.REJECT
    assert "EUR" in res.message

    # 3. Test correlation cluster limits
    correlation_matrix = {
        "strat1": {"strat2": Decimal("0.8")},
        "strat2": {"strat1": Decimal("0.8")},
    }
    market_context = {
        "correlation_matrix": correlation_matrix,
        "cluster_budget_limit": {"cluster_0": Decimal("5000.00")},
    }
    req = AllocationReviewRequest(
        portfolio_state=base_portfolio,
        proposal=proposal,
        market_context=market_context,
        config=base_config,
    )
    res = allocator.review_allocation(req)
    assert res.status == RiskDecisionStatus.REJECT
    assert "correlation cluster" in res.message

    # 4. Test VaR and Expected Shortfall limits
    volatilities = {"strat1": Decimal("0.10"), "strat2": Decimal("0.10")}
    market_context = {
        "volatilities": volatilities,
        "correlation_matrix": correlation_matrix,
        "max_var_limit": Decimal("100.00"),
    }
    req = AllocationReviewRequest(
        portfolio_state=base_portfolio,
        proposal=proposal,
        market_context=market_context,
        config=base_config,
    )
    res = allocator.review_allocation(req)
    assert res.status == RiskDecisionStatus.REJECT
    assert res.reason_code == RiskReasonCode.VAR_BREACH

    # 5. Test stress loss limits
    market_context = {
        "strategy_stress_factors": {
            "strat1": Decimal("0.10"),
            "strat2": Decimal("0.20"),
        },
        "max_stress_loss_limit": Decimal("500.00"),
    }
    req = AllocationReviewRequest(
        portfolio_state=base_portfolio,
        proposal=proposal,
        market_context=market_context,
        config=base_config,
    )
    res = allocator.review_allocation(req)
    assert res.status == RiskDecisionStatus.REJECT
    assert res.reason_code == RiskReasonCode.STRESS_BREACH

    # 6. Test margin limits
    market_context = {
        "strategy_margin_factors": {
            "strat1": Decimal("0.05"),
            "strat2": Decimal("0.10"),
        },
        "max_margin_limit": Decimal("300.00"),
    }
    req = AllocationReviewRequest(
        portfolio_state=base_portfolio,
        proposal=proposal,
        market_context=market_context,
        config=base_config,
    )
    res = allocator.review_allocation(req)
    assert res.status == RiskDecisionStatus.REJECT
    assert res.reason_code == RiskReasonCode.MARGIN_BREACH

    # 7. Test drawdown step-down limits
    market_context = {
        "strategy_drawdown_multipliers": {"strat1": Decimal("0.5")},
    }
    proposal_increase = ProposedAllocation(
        allocations={"strat1": Decimal("3500.00"), "strat2": Decimal("3000.00")},
        as_of=datetime.now(UTC),
    )
    req = AllocationReviewRequest(
        portfolio_state=base_portfolio,
        proposal=proposal_increase,
        market_context=market_context,
        config=base_config,
    )
    res = allocator.review_allocation(req)
    assert res.status == RiskDecisionStatus.REJECT
    assert res.reason_code == RiskReasonCode.DRAWDOWN_BREACH
