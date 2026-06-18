"""Unit tests for the FX currency exposure engine."""

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
    RiskMode,
    calculate_currency_exposure,
    decompose_position,
)
from app.utils.errors import ValidationError


@pytest.fixture
def base_config() -> RiskConfig:
    """Provide standard risk config."""
    return RiskConfig(
        profile_name="test_exposure",
        allow_live_execution=False,
    )


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
        "EURUSD_contract_size": 100000.0,
        "EURUSD_price": 1.10,
        "USDJPY_contract_size": 100000.0,
        "USDJPY_price": 150.0,
        "mode": RiskMode.PAPER,
        "conversion_rates": {
            "EUR": 1.10,
            "JPY": 0.0067,
        },
    }


def test_decompose_position() -> None:
    """Test position decomposition into currency legs."""
    # Long 1.0 standard lot EURUSD (contract 100k, price 1.10)
    legs_long = decompose_position(
        symbol="EURUSD",
        side="buy",
        quantity=Decimal("1.0"),
        price=Decimal("1.10"),
        contract_size=Decimal("100000.0"),
        base_ccy="EUR",
        quote_ccy="USD",
    )
    # Expected: Long 100k EUR, Short 110k USD
    assert len(legs_long) == 2
    assert legs_long[0].currency == "EUR"
    assert legs_long[0].signed_amount == Decimal("100000.0")
    assert legs_long[1].currency == "USD"
    assert legs_long[1].signed_amount == Decimal("-110000.0")

    # Short 0.5 lot USDJPY (contract 100k, price 150.0)
    legs_short = decompose_position(
        symbol="USDJPY",
        side="sell",
        quantity=Decimal("0.5"),
        price=Decimal("150.0"),
        contract_size=Decimal("100000.0"),
        base_ccy="USD",
        quote_ccy="JPY",
    )
    # Expected: Short 50k USD, Long 7.5M JPY
    assert len(legs_short) == 2
    assert legs_short[0].currency == "USD"
    assert legs_short[0].signed_amount == Decimal("-50000.0")
    assert legs_short[1].currency == "JPY"
    assert legs_short[1].signed_amount == Decimal("7500000.0")


def test_exposure_aggregation(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test currency exposure aggregation and USD conversion."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]

    res = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )

    # EUR leg: Long 100,000 EUR * 1.10 = 110,000 USD gross and net
    assert "EUR" in res
    assert res["EUR"].gross == Decimal("110000.0")
    assert res["EUR"].net == Decimal("110000.0")

    # USD leg: Short 110,000 USD gross = 110,000 USD, net = -110,000 USD
    assert "USD" in res
    assert res["USD"].gross == Decimal("110000.0")
    assert res["USD"].net == Decimal("-110000.0")


def test_exposure_conversion_failure(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test behavior when conversion rate is missing."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURMXN",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("20.00"),
            current_price=Decimal("20.00"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]
    context = eur_usd_context.copy()
    context["conversion_rates"] = {}

    with pytest.raises(ValidationError, match="Missing conversion rate for MXN to USD"):
        calculate_currency_exposure(base_portfolio, None, base_config, context)


def test_pending_order_exposure_policies(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test ignore, full-potential, near-market-only, and prob-weighted policies."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        )
    ]
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 1.0,
            "price": 1.09,
            "distance_pips": 100.0,
            "probability": 0.3,
            "status": "active",
        }
    ]

    # 1. ignore policy
    base_config.pending_order_policy = "ignore"
    res_ignore = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_ignore["EUR"].net == Decimal("110000.0")

    # 2. full-potential policy
    base_config.pending_order_policy = "full-potential"
    res_full = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_full["EUR"].net == Decimal("220000.0")

    # 3. near-market-only policy (threshold 50 pips)
    base_config.pending_order_policy = "near-market-only"
    # Order has distance 100 pips > 50 pips, should be excluded
    res_near_ex = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_near_ex["EUR"].net == Decimal("110000.0")

    # Change order distance to 30 pips <= 50 pips, should be included
    base_portfolio.orders[0]["distance_pips"] = 30.0
    res_near_in = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_near_in["EUR"].net == Decimal("220000.0")

    # 4. probability-weighted policy
    base_config.pending_order_policy = "probability-weighted"
    res_prob = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert res_prob["EUR"].net == Decimal("143000.00")


def test_live_mode_fail_closed_checks(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test live environment fail-closed behavior for unknown/unreconciled states."""
    base_portfolio.positions = []
    base_portfolio.orders = [
        {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 1.0,
            "price": 1.10,
            "status": "unknown",
        }
    ]

    base_config.pending_order_policy = "full-potential"
    context = eur_usd_context.copy()
    context["mode"] = RiskMode.FULL_LIVE

    # 1. Unknown order status should raise ValidationError
    with pytest.raises(ValidationError, match="Fail-Closed: Unknown order status"):
        calculate_currency_exposure(base_portfolio, None, base_config, context)

    base_portfolio.orders[0]["status"] = "active"

    # 2. Unreconciled portfolio state should raise ValidationError
    context["is_reconciled"] = False
    with pytest.raises(
        ValidationError, match="Fail-Closed: Portfolio state is unreconciled"
    ):
        calculate_currency_exposure(base_portfolio, None, base_config, context)


def test_proposed_trade_evaluation(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test that candidate proposed trade is included in calculations."""
    base_portfolio.positions = []
    proposed = ProposedTrade(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.10"),
    )

    res = calculate_currency_exposure(
        base_portfolio, proposed, base_config, eur_usd_context
    )
    assert res["EUR"].net == Decimal("110000.0")


def test_custom_currency_clusters(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test aggregation of custom currency clusters from config/context."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        ),
        PositionState(
            position_id="pos-2",
            symbol="USDJPY",
            direction="short",
            quantity=Decimal("0.5"),
            entry_price=Decimal("150.0"),
            current_price=Decimal("150.0"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        ),
    ]

    base_config.currency_clusters = {"USD_CLUSTER": ["EUR", "JPY"]}

    res = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context
    )
    assert "USD_CLUSTER" in res
    assert res["USD_CLUSTER"].gross == Decimal("160250.0")
    assert res["USD_CLUSTER"].net == Decimal("160250.0")


def test_exposure_filtering_by_strategy_and_symbol(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    eur_usd_context: dict[str, Any],
) -> None:
    """Test filtering currency exposure calculations by strategy ID and symbol."""
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.10"),
            current_price=Decimal("1.10"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-1",
            open_time=datetime.now(UTC),
        ),
        PositionState(
            position_id="pos-2",
            symbol="USDJPY",
            direction="short",
            quantity=Decimal("0.5"),
            entry_price=Decimal("150.0"),
            current_price=Decimal("150.0"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("1000.00"),
            strategy_id="strat-2",
            open_time=datetime.now(UTC),
        ),
    ]

    # 1. Filter by strategy-1 -> only EURUSD should be included
    res_strat1 = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context, strategy_id="strat-1"
    )
    assert "EUR" in res_strat1
    assert "JPY" not in res_strat1

    # 2. Filter by strategy-2 -> only USDJPY should be included
    res_strat2 = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context, strategy_id="strat-2"
    )
    assert "JPY" in res_strat2
    assert "EUR" not in res_strat2

    # 3. Filter by symbol USDJPY -> only USDJPY should be included
    res_symbol = calculate_currency_exposure(
        base_portfolio, None, base_config, eur_usd_context, symbol="USDJPY"
    )
    assert "JPY" in res_symbol
    assert "EUR" not in res_symbol
