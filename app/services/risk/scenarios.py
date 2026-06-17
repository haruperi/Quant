"""Risk scenarios and stress analysis.

This module implements what-if simulations and stress scenario analysis.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.services.risk.models import PortfolioState, RiskConfig, ScenarioResult


class StressScenario(BaseModel):
    """Stress scenario definition containing market move assumptions."""

    name: str
    price_shocks: dict[str, Decimal] = Field(default_factory=dict)
    spread_multiplier: Decimal = Field(default=Decimal("1.0"))

    model_config = {"allow_inf_nan": False, "arbitrary_types_allowed": True}


class ScenarioRegistry:
    """Registry storing pre-configured stress scenarios."""

    def __init__(self) -> None:
        """Initialize registry."""
        self._scenarios: dict[str, StressScenario] = {}

    def register(self, scenario: StressScenario) -> None:
        """Register a stress scenario."""
        self._scenarios[scenario.name] = scenario

    def get(self, name: str) -> StressScenario | None:
        """Retrieve scenario by name."""
        return self._scenarios.get(name)

    def list_all(self) -> list[StressScenario]:
        """Return list of all registered scenarios."""
        return list(self._scenarios.values())


def build_default_scenario_registry() -> ScenarioRegistry:
    """Construct default scenario registry with standard stress scenarios."""
    registry = ScenarioRegistry()

    # 1. USD Shock (USD depreciates by 2%)
    registry.register(
        StressScenario(
            name="USD Shock",
            price_shocks={
                "EURUSD": Decimal("0.02"),
                "GBPUSD": Decimal("0.02"),
                "USDJPY": Decimal("-0.02"),
            },
            spread_multiplier=Decimal("1.0"),
        )
    )

    # 2. Spread Widening (3x spreads)
    registry.register(
        StressScenario(
            name="Spread Widening", price_shocks={}, spread_multiplier=Decimal("3.0")
        )
    )

    # 3. Correlation Break
    registry.register(
        StressScenario(
            name="Correlation Break",
            price_shocks={"EURUSD": Decimal("-0.03"), "GBPUSD": Decimal("0.03")},
            spread_multiplier=Decimal("1.5"),
        )
    )

    return registry


def evaluate_scenarios(
    portfolio_state: PortfolioState,
    scenarios: list[StressScenario],
    risk_config: RiskConfig,
) -> list[ScenarioResult]:
    """Run stress scenario evaluations against a portfolio state."""
    results: list[ScenarioResult] = []

    for scenario in scenarios:
        # Calculate impact of shocks on floating PnL
        shock_impact = Decimal("0.0")
        for pos in portfolio_state.positions:
            shock = scenario.price_shocks.get(pos.symbol, Decimal("0.0"))
            if shock != 0:
                direction_mult = (
                    Decimal("1.0") if pos.direction == "long" else Decimal("-1.0")
                )
                shock_impact += pos.quantity * pos.entry_price * shock * direction_mult

        projected_equity = portfolio_state.equity + shock_impact
        # Drawdown = (balance - projected_equity) / balance
        projected_drawdown = Decimal("0.0")
        if portfolio_state.balance > 0:
            projected_drawdown = (
                portfolio_state.balance - projected_equity
            ) / portfolio_state.balance

        # Margin call check: utilization > max_margin_utilization
        margin_util = Decimal("0.0")
        if projected_equity > 0:
            # simple assumption: margin required scales by spread multiplier
            projected_margin = portfolio_state.margin_used * scenario.spread_multiplier
            margin_util = projected_margin / projected_equity

        is_margin_call = margin_util > risk_config.max_margin_utilization_pct
        is_stop_out = (
            margin_util > Decimal("0.95") or projected_equity <= 0
        )  # 95% margin level stop out standard

        results.append(
            ScenarioResult(
                scenario_name=scenario.name,
                impact_pct=(shock_impact / portfolio_state.equity)
                if portfolio_state.equity > 0
                else Decimal("0.0"),
                projected_equity=max(projected_equity, Decimal("0.0")),
                projected_drawdown_pct=projected_drawdown,
                margin_utilization_pct=margin_util,
                is_margin_call=is_margin_call,
                is_stop_out=is_stop_out,
            )
        )

    return results
