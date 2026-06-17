from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.risk.limits import (
    check_currency_exposure_limit,
    check_daily_loss_limit,
    check_kill_switch_state,
    check_leverage_limit,
    check_margin_limit,
    check_max_drawdown_limit,
    check_news_blackout,
    check_slippage_limit,
    check_spread_limit,
    check_strategy_loss_limit,
    check_symbol_exposure_limit,
)
from app.services.risk.models import (
    PortfolioState,
    PositionState,
    RiskConfig,
)


@pytest.fixture
def base_config():
    return RiskConfig(
        max_daily_loss_pct=Decimal("0.05"),
        max_total_loss_pct=Decimal("0.10"),
        max_margin_utilization_pct=Decimal("0.80"),
        max_effective_leverage=Decimal("30.0"),
        correlation_threshold=Decimal("0.50"),
    )


@pytest.fixture
def healthy_portfolio():
    return PortfolioState(
        account_id="acc_123",
        balance=Decimal(10000),
        equity=Decimal(10000),
        margin_used=Decimal(1000),
        free_margin=Decimal(9000),
        floating_pnl=Decimal(0),
        realized_pnl=Decimal(0),
        currency="USD",
        positions=[],
        orders=[],
        strategy_allocations={},
        historical_returns=[Decimal("0.01"), Decimal("-0.005"), Decimal("0.02")],
        as_of=datetime.now(UTC),
    )


def test_drawdown_limits(healthy_portfolio, base_config):
    # Healthy portfolio passes
    res = check_max_drawdown_limit(healthy_portfolio, base_config)
    assert res.status == "pass"

    # Drawdown of 15% breaches max total loss of 10%
    breached_portfolio = healthy_portfolio.model_copy(update={"equity": Decimal(8400)})
    res = check_max_drawdown_limit(breached_portfolio, base_config)
    assert res.status == "fail"

    # Drawdown of 6% breaches max daily loss of 5%
    daily_breached = healthy_portfolio.model_copy(update={"equity": Decimal(9300)})
    res = check_daily_loss_limit(daily_breached, base_config)
    assert res.status == "fail"


def test_leverage_and_margin_limits(healthy_portfolio, base_config):
    # Add a large position
    pos = PositionState(
        position_id="pos_1",
        symbol="EURUSD",
        direction="long",
        quantity=Decimal(350000),  # Notional = 350,000
        entry_price=Decimal("1.0"),
        current_price=Decimal("1.0"),
        floating_pnl=Decimal(0),
        margin_required=Decimal(3500),
        strategy_id="strat_1",
        open_time=datetime.now(UTC),
    )
    portfolio = healthy_portfolio.model_copy(
        update={
            "positions": [pos],
            "margin_used": Decimal(9000),  # 90% utilization
        }
    )

    # Leverage = 350,000 / 10,000 = 35 (breaches 30 limit)
    res = check_leverage_limit(portfolio, base_config)
    assert res.status == "fail"

    # Margin = 90% (breaches 80% limit)
    res = check_margin_limit(portfolio, base_config)
    assert res.status == "fail"


def test_concentration_and_currency_exposure(healthy_portfolio, base_config):
    # Add positions in multiple pairs
    pos1 = PositionState(
        position_id="pos_1",
        symbol="EURUSD",
        direction="long",
        quantity=Decimal(30000),  # 30,000 USD
        entry_price=Decimal("1.0"),
        current_price=Decimal("1.0"),
        floating_pnl=Decimal(0),
        margin_required=Decimal(300),
        strategy_id="strat_1",
        open_time=datetime.now(UTC),
    )
    portfolio = healthy_portfolio.model_copy(update={"positions": [pos1]})

    # Check concentration (limit is 20% of equity = 2000 USD)
    res = check_symbol_exposure_limit(portfolio, base_config)
    assert res.status == "fail"

    # Check currency exposures (limit is 40% of equity = 4000 USD)
    res = check_currency_exposure_limit(portfolio, base_config)
    assert res.status == "fail"


def test_news_blackout(healthy_portfolio, base_config):
    now = datetime.now(UTC)
    # High impact news 5 minutes away
    news = [
        {
            "title": "NFP Report",
            "time": (now + timedelta(minutes=5)).isoformat(),
            "impact": "high",
        }
    ]
    res = check_news_blackout(healthy_portfolio, base_config, calendar_evidence=news)
    assert res.status == "blocked"

    # Low impact news does not trigger block
    low_news = [
        {
            "title": "Low Impact Event",
            "time": (now + timedelta(minutes=5)).isoformat(),
            "impact": "low",
        }
    ]
    res = check_news_blackout(
        healthy_portfolio, base_config, calendar_evidence=low_news
    )
    assert res.status == "pass"


def test_spread_and_slippage_limits(healthy_portfolio, base_config):
    # Spread spike
    context = {"spread": 12.0, "max_spread": 10.0}
    res = check_spread_limit(healthy_portfolio, base_config, market_context=context)
    assert res.status == "fail"

    # Slippage spike
    context = {"slippage": 6.0, "max_slippage": 5.0}
    res = check_slippage_limit(healthy_portfolio, base_config, market_context=context)
    assert res.status == "fail"


def test_kill_switch_state():
    res = check_kill_switch_state(True)
    assert res.status == "blocked"
    res = check_kill_switch_state(False)
    assert res.status == "pass"


def test_limit_edge_cases(healthy_portfolio, base_config):
    # 1. Zero balance / negative balance
    zero_balance_portfolio = healthy_portfolio.model_copy(
        update={"balance": Decimal(0)}
    )
    res = check_max_drawdown_limit(zero_balance_portfolio, base_config)
    assert res.status == "fail"
    res = check_daily_loss_limit(zero_balance_portfolio, base_config)
    assert res.status == "fail"

    # 2. Zero equity in leverage/margin checks
    zero_equity_portfolio = healthy_portfolio.model_copy(update={"equity": Decimal(0)})
    res = check_leverage_limit(zero_equity_portfolio, base_config)
    assert res.status == "fail"
    res = check_margin_limit(zero_equity_portfolio, base_config)
    assert res.status == "fail"

    # 3. Strategy allocations exceeding equity
    over_allocated_portfolio = healthy_portfolio.model_copy(
        update={"strategy_allocations": {"strat_1": Decimal(15000)}}
    )
    res = check_strategy_loss_limit(over_allocated_portfolio, base_config)
    assert res.status == "fail"
