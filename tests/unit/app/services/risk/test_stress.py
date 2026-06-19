"""Unit tests for the Stress Testing Engine.

Verifies default and custom macro shocks, custom scenario validations,
margin/slippage impacts, and performance behavior under load.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    PortfolioState,
    PositionState,
    ProposedTrade,
    RiskConfig,
    StressScenarioRegistry,
    build_default_scenario_registry,
    validate_custom_scenario,
)
from app.services.risk.stress import (
    CorrelationToOneScenario,
    ForcedLiquidationScenario,
    GBPVolatilityScenario,
    JPYRiskOffScenario,
    MarginSpikeScenario,
    NewsCandleScenario,
    PlatformDisconnectScenario,
    PriceShockScenario,
    RolloverLiquidityScenario,
    SlippageShockScenario,
    SpreadWideningScenario,
    StaleQuoteScenario,
    USDShockScenario,
)
from app.utils.errors import ValidationError


@pytest.fixture
def base_portfolio() -> PortfolioState:
    """Fixture for baseline PortfolioState with EURUSD long position."""
    return PortfolioState(
        account_id="acc-123",
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
        ],
        orders=[],
        strategy_allocations={},
    )


@pytest.fixture
def base_config() -> RiskConfig:
    """Fixture for baseline RiskConfig."""
    return RiskConfig(
        profile_name="default",
        max_daily_loss_pct=Decimal("0.05"),
        max_total_loss_pct=Decimal("0.10"),
        max_total_loss_pct_advisory=Decimal("0.08"),
        max_effective_leverage=Decimal("30.0"),
    )


@pytest.fixture
def market_context() -> dict[str, Any]:
    """Fixture for standard market context."""
    return {
        "EURUSD_contract_size": 100000.0,
        "GBPUSD_contract_size": 100000.0,
        "USDJPY_contract_size": 100000.0,
        "EURUSD_pip_size": 0.0001,
        "GBPUSD_pip_size": 0.0001,
        "USDJPY_pip_size": 0.01,
        "EURUSD_spread": 0.0002,
        "GBPUSD_spread": 0.0002,
        "USDJPY_spread": 0.02,
        "conversion_rates": {
            "EUR": 1.10,
            "GBP": 1.25,
            "JPY": 0.009,
            "USD": 1.0,
        },
    }


def test_usd_shock_scenarios(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify USD Shock Up and USD Shock Down calculations."""
    usd_up = USDShockScenario(shock_direction="up")
    usd_down = USDShockScenario(shock_direction="down")

    # For EURUSD long (1.0 lot, contract size 100k, current 1.10)
    # USD Shock Up: EURUSD price shocks -10%. Price drops to 0.99.
    # PnL in Quote (USD): 1.0 * 100000 * (0.99 - 1.10) = -11000 USD
    # Since Rate=1.0, loss is 11000 USD.
    res_up = usd_up.evaluate(base_portfolio, None, market_context, base_config)
    assert res_up.scenario_name == "USD Shock Up"
    assert res_up.projected_equity == Decimal("0.0")  # Capped at 0
    assert res_up.impact_pct == Decimal("1.10")  # 11k / 10k
    assert not res_up.pass_status
    assert "USD_SHOCK_BREACH" in res_up.reason_codes

    # USD Shock Down: EURUSD price shocks +10%. Price rises to 1.21.
    # PnL = 1.0 * 100000 * (+0.11) = +11000 USD. Loss = 0.
    res_down = usd_down.evaluate(base_portfolio, None, market_context, base_config)
    assert res_down.scenario_name == "USD Shock Down"
    assert res_down.projected_equity == Decimal("10000.00")
    assert res_down.impact_pct == Decimal("0.0")
    assert res_down.pass_status


def test_jpy_risk_off_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify JPY Risk-Off (JPY appreciates, quote JPY pairs drop 10%)."""
    jpy_shock = JPYRiskOffScenario()

    # Position in JPY: long USDJPY 1.0 lot at 110.00
    base_portfolio.positions = [
        PositionState(
            position_id="pos-jpy",
            symbol="USDJPY",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("110.00"),
            current_price=Decimal("110.00"),
            floating_pnl=Decimal("0.0"),
            margin_required=Decimal("1000.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
    ]

    # USDJPY drops 10% to 99.00
    # PnL in Quote (JPY): 1.0 * 100000 * (99.00 - 110.00) = -1,100,000 JPY
    # Convert JPY to USD: Rate = 0.009 -> -9900 USD loss
    res = jpy_shock.evaluate(base_portfolio, None, market_context, base_config)
    assert not res.pass_status
    assert res.projected_equity == Decimal("100.00")  # 10k - 9.9k
    assert res.impact_pct == Decimal("0.99")
    assert "JPY_RISK_OFF_BREACH" in res.reason_codes


def test_gbp_volatility_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify GBP Volatility Shock evaluates worst-case ±15% and spread doubling."""
    gbp_vol = GBPVolatilityScenario()

    # Long GBPUSD 1.0 lot at 1.2500
    base_portfolio.positions = [
        PositionState(
            position_id="pos-gbp",
            symbol="GBPUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.2500"),
            current_price=Decimal("1.2500"),
            floating_pnl=Decimal("0.0"),
            margin_required=Decimal("1000.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
    ]

    # Max price loss is when GBPUSD drops 15% (price drops to 1.0625)
    # Price loss = 1.0 * 100000 * 0.1875 = 18750 USD
    # Spread cost doubling: GBPUSD spread = 0.0002.
    # Exit cost = 1.0 * 100000 * 0.0002 = 20 USD.
    # Total loss = 18770 USD
    res = gbp_vol.evaluate(base_portfolio, None, market_context, base_config)
    assert res.impact_pct == Decimal("1.8770")  # 18770 / 10000
    assert not res.pass_status


def test_spread_widening_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify cost impact of spread multiplying by 5."""
    scenario = SpreadWideningScenario()

    # EURUSD long 1.0 lot, spread = 0.0002
    # Additional cost of (5-1)/2 = 2x spread exit cost
    # Cost = 1.0 * 100000 * 0.0002 * 2 = 40 USD
    res = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert res.pass_status
    assert res.projected_equity == Decimal("9960.00")
    assert res.impact_pct == Decimal("0.0040")  # 40 / 10000


def test_slippage_shock_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify candidate slippage cost."""
    scenario = SlippageShockScenario()

    # No proposed trade -> 0 loss
    res_no_trade = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert res_no_trade.pass_status
    assert res_no_trade.impact_pct == Decimal("0.0")

    # Proposed Buy EURUSD 1.0 lot
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
    )
    # Slippage of 50 pips = 50 * 0.0001 = 0.0050
    # Cost = 1.0 * 100000 * 0.0050 = 500 USD
    res = scenario.evaluate(base_portfolio, trade, market_context, base_config)
    assert res.pass_status
    assert res.projected_equity == Decimal("9500.00")
    assert res.impact_pct == Decimal("0.05")  # 500 / 10000


def test_correlation_to_one_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify tail-risk recalculation with perfect correlation = 1.0."""
    scenario = CorrelationToOneScenario()

    # Positions: EURUSD long 1.0 lot (vol=0.01)
    market_context["EURUSD_volatility"] = Decimal("0.01")
    res = scenario.evaluate(base_portfolio, None, market_context, base_config)
    # Total Gross exposure: EURUSD long 1.0 lot = 110k USD.
    # Weights: EURUSD = 1.0
    # Volatility under correlation 1.0: 1.0 * 0.01 = 0.01
    # Stress VaR: 0.01 * 1.64485 * 110k = 1809.335 USD
    assert not res.pass_status
    assert res.impact_pct == pytest.approx(
        Decimal("1809.335") / Decimal("10000.00"), abs=1e-4
    )
    assert "CORRELATION_TO_ONE_BREACH" in res.reason_codes


def test_news_candle_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify News Candle 5% shock against direction of positions."""
    scenario = NewsCandleScenario()

    # EURUSD long 1.0 lot -> drops 5%.
    # Loss = 0.05 * 110k USD = 5500 USD
    res = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert not res.pass_status  # 5500 / 10000 = 55% > 8% advisory limit
    assert res.projected_equity == Decimal("4500.00")
    assert res.impact_pct == Decimal("0.55")


def test_rollover_liquidity_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify 10x spread cost increase during rollover."""
    scenario = RolloverLiquidityScenario()

    # EURUSD long 1.0 lot, spread = 0.0002
    # Additional cost of (10-1)/2 = 4.5x spread exit cost
    # Cost = 1.0 * 100000 * 0.0002 * 4.5 = 90 USD
    res = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert res.pass_status
    assert res.projected_equity == Decimal("9910.00")
    assert res.impact_pct == Decimal("0.0090")


def test_margin_spike_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify margin spike 2x causes breach if free margin drops below 0."""
    scenario = MarginSpikeScenario()

    # Equity = 10000. Position margin_required = 1000. Shock margin = 2000.
    # free_margin = 8000 >= 0 -> pass
    res_pass = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert res_pass.pass_status
    assert res_pass.impact_pct == Decimal("0.0")

    # Position margin_required = 6000. Shock margin = 12000.
    # free_margin = 10000 - 12000 = -2000. Shortfall = 2000.
    base_portfolio.positions[0].margin_required = Decimal("6000.0")
    res_fail = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert not res_fail.pass_status
    assert res_fail.impact_pct == Decimal("0.20")  # 2000 shortfall / 10000
    assert "MARGIN_CALL_BREACH" in res_fail.reason_codes


def test_platform_disconnect_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify platform disconnect evaluators fail closed."""
    scenario = PlatformDisconnectScenario()
    res = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert not res.pass_status
    assert "PLATFORM_DISCONNECTED" in res.reason_codes


def test_stale_quote_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify stale quotes are detected and trigger breach."""
    scenario = StaleQuoteScenario()

    # Fresh quote
    res_fresh = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert res_fresh.pass_status

    # Stale quote age detected
    market_context["quote_age_stale"] = True
    res_stale = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert not res_stale.pass_status
    assert "STALE_QUOTE_BREACH" in res_stale.reason_codes


def test_forced_liquidation_scenario(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify stop-out forced liquidation proximity evaluation."""
    scenario = ForcedLiquidationScenario()

    # Equity = 10000, margin = 1000. Stop out at 50% = 500. Proximity = 9500 > 0.
    res_pass = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert res_pass.pass_status
    assert res_pass.impact_pct == Decimal("0.0")

    # Equity = 1000, margin = 3000. Stop out at 50% = 1500.
    # Proximity = 1000 - 1500 = -500.
    base_portfolio.equity = Decimal("1000.00")
    base_portfolio.positions[0].margin_required = Decimal("3000.0")
    res_fail = scenario.evaluate(base_portfolio, None, market_context, base_config)
    assert not res_fail.pass_status
    assert res_fail.impact_pct == Decimal("0.50")  # 500 shortfall / 1000 equity
    assert "FORCE_LIQUIDATION_BREACH" in res_fail.reason_codes


def test_custom_scenario_validation() -> None:
    """Verify custom scenario config validation restricts unsafe configs."""
    # Valid config
    valid_config = {
        "name": "Custom Shock",
        "price_shocks": {
            "EURUSD": -0.05,
            "USDJPY": 0.05,
        },
    }
    scenario = validate_custom_scenario(valid_config)
    assert scenario.name == "Custom Shock"
    assert scenario.price_shocks["EURUSD"] == Decimal("-0.05")

    # Invalid name type
    with pytest.raises(ValidationError, match="must have a non-empty string 'name'"):
        validate_custom_scenario({"name": 123, "price_shocks": {}})

    # Invalid shocks type
    with pytest.raises(
        ValidationError, match="must have a dictionary of 'price_shocks'"
    ):
        validate_custom_scenario({"name": "Test", "price_shocks": []})

    # Unsafe shock value (> 100% price movement)
    unsafe_config = {
        "name": "Unsafe Shock",
        "price_shocks": {"EURUSD": 1.50},  # 150% shock
    }
    with pytest.raises(ValidationError, match="exceeds 100% boundary"):
        validate_custom_scenario(unsafe_config)


def test_scenario_registry_integration(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify registry registration and full evaluation flow."""
    registry = build_default_scenario_registry()
    results = registry.evaluate_portfolio(
        base_portfolio, None, market_context, base_config
    )

    # We registered 13 default scenarios
    assert len(results) == 13

    # Check that at least news candle shock is present and evaluates correctly
    news_res = next(r for r in results if r.scenario_name == "News Candle 5% Shock")
    assert news_res.impact_pct == Decimal("0.55")


def test_stress_engine_performance_load() -> None:
    """Performance check: 100 scenarios across 500 positions runs under 50ms."""
    registry = StressScenarioRegistry()
    # Register 100 price shock scenarios
    for i in range(100):
        shocks = {f"SYM_{j}": Decimal("-0.01") for j in range(500)}
        registry.register_scenario(
            f"Scenario_{i}", PriceShockScenario(f"Scenario_{i}", shocks)
        )

    # Construct portfolio with 500 positions
    positions = []
    for j in range(500):
        positions.append(
            PositionState(
                position_id=f"pos-{j}",
                symbol=f"SYM_{j}",
                direction="long",
                quantity=Decimal("0.10"),
                entry_price=Decimal("100.00"),
                current_price=Decimal("100.00"),
                floating_pnl=Decimal("0.0"),
                margin_required=Decimal("50.0"),
                strategy_id="TF-01",
                open_time=datetime.now(UTC),
            )
        )

    portfolio = PortfolioState(
        account_id="acc-load",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("25000.00"),
        free_margin=Decimal("75000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=positions,
        orders=[],
        strategy_allocations={},
    )

    market_context = {
        "contract_size": 1.0,
        "conversion_rates": {"USD": 1.0},
    }
    for j in range(500):
        market_context[f"SYM_{j}_contract_size"] = 1.0

    config = RiskConfig(
        max_total_loss_pct_advisory=Decimal("0.15"),
    )

    # Run performance timer
    start_time = time.perf_counter()
    results = registry.evaluate_portfolio(portfolio, None, market_context, config)
    end_time = time.perf_counter()

    elapsed_ms = (end_time - start_time) * 1000.0
    assert len(results) == 100
    # Strict performance constraint
    assert elapsed_ms < 50.0, (
        f"Stress evaluation took too long: {elapsed_ms:.2f}ms (target < 50ms)"
    )


def test_stress_testing_engine_and_evaluate_wrappers(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify StressTestingEngine and evaluate_* wrappers."""
    from app.services.risk import (
        StressTestingEngine,
        evaluate_correlation_to_one_shock,
        evaluate_jpy_risk_off_shock,
        evaluate_margin_spike_shock,
        evaluate_news_candle_shock,
        evaluate_platform_disconnect_shock,
        evaluate_rollover_liquidity_shock,
        evaluate_slippage_shock,
        evaluate_spread_widening_shock,
        evaluate_usd_shock,
    )

    # 1. StressTestingEngine check
    engine = StressTestingEngine(base_config)
    results = engine.run_analysis(base_portfolio, market_context, None)
    assert len(results) == 13

    # 2. evaluate_usd_shock
    res_usd = evaluate_usd_shock(base_portfolio, None, market_context, base_config)
    assert res_usd.scenario_name == "USD Shock Up"

    # 3. evaluate_jpy_risk_off_shock
    # Setup JPY position for evaluation
    base_portfolio.positions = [
        PositionState(
            position_id="pos-jpy",
            symbol="USDJPY",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("110.00"),
            current_price=Decimal("110.00"),
            floating_pnl=Decimal("0.0"),
            margin_required=Decimal("1000.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
    ]
    res_jpy = evaluate_jpy_risk_off_shock(
        base_portfolio, None, market_context, base_config
    )
    assert res_jpy.scenario_name == "JPY Risk-Off"

    # 4. evaluate_spread_widening_shock
    res_spread = evaluate_spread_widening_shock(
        base_portfolio, None, market_context, base_config
    )
    assert res_spread.scenario_name == "Spread Widening 5x"

    # 5. evaluate_slippage_shock
    res_slip = evaluate_slippage_shock(
        base_portfolio, None, market_context, base_config
    )
    assert res_slip.scenario_name == "Slippage Shock 50 pips"

    # 6. evaluate_correlation_to_one_shock
    market_context["USDJPY_volatility"] = Decimal("0.01")
    res_corr = evaluate_correlation_to_one_shock(
        base_portfolio, None, market_context, base_config
    )
    assert res_corr.scenario_name == "Correlation to One"

    # 7. evaluate_news_candle_shock
    res_news = evaluate_news_candle_shock(
        base_portfolio, None, market_context, base_config
    )
    assert res_news.scenario_name == "News Candle 5% Shock"

    # 8. evaluate_rollover_liquidity_shock
    res_roll = evaluate_rollover_liquidity_shock(
        base_portfolio, None, market_context, base_config
    )
    assert res_roll.scenario_name == "Rollover Liquidity Shock"

    # 9. evaluate_margin_spike_shock
    res_margin = evaluate_margin_spike_shock(
        base_portfolio, None, market_context, base_config
    )
    assert res_margin.scenario_name == "Margin Requirement Spike 2x"

    # 10. evaluate_platform_disconnect_shock
    res_platform = evaluate_platform_disconnect_shock(
        base_portfolio, None, market_context, base_config
    )
    assert res_platform.scenario_name == "Platform Disconnect"
    assert not res_platform.pass_status
