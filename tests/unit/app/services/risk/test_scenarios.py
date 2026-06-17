from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.models import PortfolioState, PositionState, RiskConfig
from app.services.risk.scenarios import (
    build_default_scenario_registry,
    evaluate_scenarios,
)


@pytest.fixture
def base_config():
    return RiskConfig(
        max_daily_loss_pct=Decimal("0.05"),
        max_margin_utilization_pct=Decimal("0.80"),
    )


@pytest.fixture
def base_portfolio():
    pos = PositionState(
        position_id="pos_1",
        symbol="EURUSD",
        direction="long",
        quantity=Decimal(10000),
        entry_price=Decimal("1.0"),
        current_price=Decimal("1.0"),
        floating_pnl=Decimal(0),
        margin_required=Decimal(1000),
        strategy_id="strat_1",
        open_time=datetime.now(UTC),
    )
    return PortfolioState(
        account_id="acc_123",
        balance=Decimal(10000),
        equity=Decimal(10000),
        margin_used=Decimal(1000),
        free_margin=Decimal(9000),
        floating_pnl=Decimal(0),
        realized_pnl=Decimal(0),
        positions=[pos],
        currency="USD",
        as_of=datetime.now(UTC),
    )


def test_registry_and_scenarios(base_portfolio, base_config):
    registry = build_default_scenario_registry()
    scenarios = registry.list_all()
    assert len(scenarios) >= 3

    results = evaluate_scenarios(base_portfolio, scenarios, base_config)
    assert len(results) == len(scenarios)

    # Check shock impact calculation
    usd_shock_res = next(r for r in results if r.scenario_name == "USD Shock")
    # Price shocks: {"EURUSD": 0.02} -> 10,000 units long EURUSD means
    # 10,000 * 1.0 * 0.02 * 1.0 = 200 USD profit.
    # impact_pct = 200 / 10000 = 0.02 (2%).
    assert usd_shock_res.impact_pct == Decimal("0.02")
    assert usd_shock_res.projected_equity == Decimal("10200.0")
