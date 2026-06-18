"""Unit tests for the Margin Governance module.

Verifies margin, leverage, pending-order margin policies,
and exit-liquidity stress checks.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    PortfolioState,
    PositionState,
    ProposedTrade,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
)
from app.services.risk.margin import (
    calculate_current_margin,
    calculate_free_margin_after_orders,
    calculate_projected_margin,
    exit_liquidity_stress_check,
    verify_margin_limits,
)
from app.utils.errors import ValidationError


@pytest.fixture
def base_portfolio() -> PortfolioState:
    """Fixture for baseline PortfolioState."""
    return PortfolioState(
        account_id="acc-margin",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("1000.00"),
        free_margin=Decimal("9000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            PositionState(
                position_id="pos-eur",
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
        ],
        orders=[],
        strategy_allocations={"TF-01": Decimal("5000.00")},
    )


@pytest.fixture
def base_config() -> RiskConfig:
    """Fixture for baseline RiskConfig."""
    return RiskConfig(
        profile_name="default",
        max_margin_utilization_pct=Decimal("0.80"),
        max_effective_leverage=Decimal("30.0"),
        max_risk_per_trade=Decimal("0.02"),
    )


@pytest.fixture
def market_context() -> dict[str, Any]:
    """Fixture for market context."""
    return {
        "EURUSD_contract_size": 100000.0,
        "EURUSD_pip_size": 0.0001,
        "EURUSD_spread": 0.0002,
        "conversion_rates": {
            "EUR": 1.10,
            "USD": 1.0,
        },
    }


def test_margin_calculations(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify current and projected margin calculations."""
    # Current margin should be 1000
    assert calculate_current_margin(base_portfolio) == Decimal("1000.0")

    # Proposed trade: buy 1.0 EURUSD at 1.10
    # contract size = 100k, leverage = 30 (capped by config from default broker 30)
    # margin_quote = (1.0 * 100000 * 1.10) / 30 = 3666.67 USD
    # rate = 1.0 (quote USD to account USD)
    # projected_margin = 1000 + 3666.67 = 4666.67
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    proj = calculate_projected_margin(
        base_portfolio, trade, market_context, base_config
    )
    assert proj == pytest.approx(Decimal("4666.6667"))


def test_missing_margin_metadata(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify that calculations reject missing broker metadata."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    bad_context = {"conversion_rates": {"USD": 1.0}}
    with pytest.raises(ValidationError, match="Missing contract size metadata"):
        calculate_projected_margin(base_portfolio, trade, bad_context, base_config)


def test_free_margin_pending_orders_policies(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify free margin calculation under different pending order policies."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    # Add active pending order: buy 1.0 EURUSD at 1.10
    # margin required: 3666.67 USD
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "status": "active",
            "quantity": 1.0,
            "price": 1.1000,
            "probability": 0.5,
            "distance_pips": 20.0,
        }
    ]

    # 1. Ignore policy
    base_config.pending_order_policy = "ignore"
    free_ignore = calculate_free_margin_after_orders(
        base_portfolio, trade, market_context, base_config
    )
    # free_margin = 10000 - 4666.67 = 5333.33
    assert free_ignore == pytest.approx(Decimal("5333.3333"))

    # 2. Full potential policy
    base_config.pending_order_policy = "full-potential"
    free_full = calculate_free_margin_after_orders(
        base_portfolio, trade, market_context, base_config
    )
    # free_margin = 10000 - 4666.67 - 3666.67 = 1666.67
    assert free_full == pytest.approx(Decimal("1666.6667"))

    # 3. Probability weighted policy
    base_config.pending_order_policy = "probability-weighted"
    free_prob = calculate_free_margin_after_orders(
        base_portfolio, trade, market_context, base_config
    )
    # free_margin = 10000 - 4666.67 - (3666.67 * 0.5) = 3500.00
    assert free_prob == pytest.approx(Decimal("3500.00"))


def test_exit_liquidity_stress_check(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify exit liquidity stress check triggers fail under wide spreads."""
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )

    # Normal spread check passes
    exit_pass, exit_loss = exit_liquidity_stress_check(
        base_portfolio,
        trade,
        market_context,
        base_config,
        spread_multiplier=Decimal("5.0"),
    )
    # exit loss = (1.0 + 1.0) * 100000 * 0.0002 * 5 = 200 USD.
    # free_margin = 5333.33 -> passes
    assert exit_pass
    assert exit_loss == Decimal("200.00")

    # High spread multiplier triggers failure
    exit_fail, fail_loss = exit_liquidity_stress_check(
        base_portfolio,
        trade,
        market_context,
        base_config,
        spread_multiplier=Decimal("150.0"),
    )
    # loss = 2.0 * 100k * 0.0002 * 150 = 6000 USD > 5333.33 -> fails
    assert not exit_fail
    assert fail_loss == Decimal("6000.00")


def test_verify_margin_limits(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify limit checks for margin utilization and leverage limits."""
    # Pass path
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.5"),
        price=Decimal("1.1000"),
    )
    res = verify_margin_limits(base_portfolio, trade, market_context, base_config)
    assert res.status == RiskDecisionStatus.APPROVE
    assert not res.breached

    # Margin utilization breach (> 80%)
    # proposed volume = 2.0 lots -> margin = 7333.33.
    # total projected = 8333.33. Ratio = 83.33% > 80%
    trade_large = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("2.0"),
        price=Decimal("1.1000"),
    )
    res_large = verify_margin_limits(
        base_portfolio, trade_large, market_context, base_config
    )
    assert res_large.status == RiskDecisionStatus.REJECT
    assert res_large.reason_code == RiskReasonCode.MARGIN_BREACH

    # Leverage breach
    # total gross exposure for 4.0 lots EURUSD = 5.0 lots * 100000 * 1.10 = 550,000 USD
    # leverage = 550k / 10k = 55.0 > 30.0 config cap
    trade_leverage = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("4.0"),
        price=Decimal("1.1000"),
    )
    base_config.max_margin_utilization_pct = Decimal("5.0")
    res_lev = verify_margin_limits(
        base_portfolio, trade_leverage, market_context, base_config
    )
    assert res_lev.status == RiskDecisionStatus.REJECT
    assert res_lev.reason_code == RiskReasonCode.LEVERAGE_BREACH
