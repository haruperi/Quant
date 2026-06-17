from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.governor import run_portfolio_risk_governor
from app.services.risk.models import PortfolioState, ProposedTrade, RiskConfig


@pytest.fixture
def base_config():
    return RiskConfig(
        max_daily_loss_pct=Decimal("0.05"),
        max_total_loss_pct=Decimal("0.10"),
        double_spend_prevention_owner="risk_cache",
    )


@pytest.fixture
def base_portfolio():
    return PortfolioState(
        account_id="acc_123",
        balance=Decimal(10000),
        equity=Decimal(10000),
        margin_used=Decimal(0),
        free_margin=Decimal(10000),
        floating_pnl=Decimal(0),
        realized_pnl=Decimal(0),
        currency="USD",
        historical_returns=[
            Decimal("0.01"),
            Decimal("-0.01"),
            Decimal("0.02"),
            Decimal("-0.02"),
            Decimal("0.005"),
        ],
        as_of=datetime.now(UTC),
    )


def test_governor_happy_path(base_portfolio, base_config):
    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
        price=Decimal("1.0"),
        stop_loss=Decimal("0.99"),
        requires_live_execution=False,
    )
    decision = run_portfolio_risk_governor(
        proposed_trade=trade,
        portfolio_state=base_portfolio,
        risk_config=base_config,
        market_context={"spread": 1.0, "slippage": 0.5},
    )
    assert decision.status == "approve"


def test_governor_news_blackout_warning(base_portfolio, base_config):
    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
        price=Decimal("1.0"),
        stop_loss=Decimal("0.99"),
        requires_live_execution=False,
    )
    # 5 minutes news event
    news = [{"title": "NFP", "time": datetime.now(UTC).isoformat(), "impact": "high"}]
    decision = run_portfolio_risk_governor(
        proposed_trade=trade,
        portfolio_state=base_portfolio,
        risk_config=base_config,
        calendar_evidence=news,
        market_context={"spread": 1.0, "slippage": 0.5},
    )
    assert decision.status == "block"
    assert "NEWS_BLACKOUT" in decision.composite_breach_flags


def test_governor_double_spend_gate(base_portfolio, base_config):
    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
        price=Decimal("1.0"),
        stop_loss=Decimal("0.99"),
        requires_live_execution=True,
    )
    # First request approved
    decision1 = run_portfolio_risk_governor(
        proposed_trade=trade,
        portfolio_state=base_portfolio,
        risk_config=base_config,
        request_id="req_1",
        workflow_id="wf_1",
        market_context={"spread": 1.0, "slippage": 0.5},
    )
    assert decision1.status == "approve"

    # Second concurrent request with same workflow_id triggers double spend block
    decision2 = run_portfolio_risk_governor(
        proposed_trade=trade,
        portfolio_state=base_portfolio,
        risk_config=base_config,
        request_id="req_2",
        workflow_id="wf_1",
        market_context={"spread": 1.0, "slippage": 0.5},
    )
    assert decision2.status == "block"
    assert "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED" in decision2.composite_breach_flags
