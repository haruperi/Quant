"""Stress Testing Engine.

Evaluates pre-trade portfolio resilience under historical and hypothetical
macro stress scenarios.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.risk.exposure import _resolve_base_quote as _orig_resolve_base_quote
from app.services.risk.exposure import _resolve_conversion_rate
from app.services.risk.models import (
    PortfolioState,
    ProposedTrade,
    RiskConfig,
    StressScenario,
    StressScenarioResult,
)
from app.utils.errors import ValidationError


def _resolve_base_quote(
    symbol: str, market_context: dict[str, Any] | None = None
) -> tuple[str, str]:
    """Resolve base and quote currencies, wrapper for optional market_context."""
    ctx = market_context if market_context is not None else {}
    return _orig_resolve_base_quote(symbol, ctx)


class StressScenarioRegistry:
    """Registry and orchestrator for executing portfolio stress tests."""

    def __init__(self) -> None:
        self.scenarios: dict[str, Any] = {}

    def register_scenario(self, name: str, evaluator: Any) -> None:  # noqa: ANN401
        """Register a stress scenario evaluator.

        Args:
            name: Unique name of the scenario.
            evaluator: A callable or object implementing an evaluate method.
        """
        self.scenarios[name] = evaluator

    def evaluate_portfolio(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> list[StressScenarioResult]:
        """Evaluate the portfolio and candidate trade against all registered scenarios.

        Args:
            portfolio_state: Current portfolio state.
            proposed_trade: Optional proposed candidate trade.
            market_context: Dict containing prices, quotes, and conversion rates.
            config: Active risk configuration profile.

        Returns:
            List of StressScenarioResult objects.
        """
        results = []
        for name, evaluator in self.scenarios.items():
            try:
                if hasattr(evaluator, "evaluate"):
                    result = evaluator.evaluate(
                        portfolio_state=portfolio_state,
                        proposed_trade=proposed_trade,
                        market_context=market_context,
                        config=config,
                    )
                else:
                    result = evaluator(
                        portfolio_state=portfolio_state,
                        proposed_trade=proposed_trade,
                        market_context=market_context,
                        config=config,
                    )
                results.append(result)
            except Exception:  # noqa: BLE001
                # Fail-closed for scenario errors
                results.append(
                    StressScenarioResult(
                        scenario_name=name,
                        impact_pct=Decimal("1.0"),
                        projected_equity=Decimal("0.0"),
                        pass_status=False,
                        reason_codes=["SCENARIO_EVALUATION_ERROR"],
                    )
                )
        return results


def calculate_price_shock_loss(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    price_shocks: dict[str, Decimal],
) -> Decimal:
    """Calculate the total net loss from a set of price shocks in account currency.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Optional candidate trade.
        market_context: Market details.
        price_shocks: Mapping of symbol to percentage price shock
            (e.g. Decimal("-0.10")).

    Returns:
        Positive Decimal value representing the total net loss. If net
        PnL is positive, returns 0.
    """
    account_ccy = portfolio_state.currency.upper()
    total_shock_pnl = Decimal("0.0")

    # 1. Open positions PnL impact
    for pos in portfolio_state.positions:
        symbol = pos.symbol
        shock = price_shocks.get(symbol, Decimal("0.0"))
        if shock == Decimal("0.0"):
            continue

        direction_sign = Decimal("1.0") if pos.direction == "long" else Decimal("-1.0")
        price = pos.current_price
        shocked_price = price * (Decimal("1.0") + shock)
        price_diff = shocked_price - price

        c_size_raw = market_context.get(
            f"{symbol}_contract_size"
        ) or market_context.get("contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))

        pnl_quote = pos.quantity * contract_size * price_diff * direction_sign
        _, quote_ccy = _resolve_base_quote(symbol)
        rate = _resolve_conversion_rate(quote_ccy, account_ccy, market_context)
        total_shock_pnl += pnl_quote * rate

    # 2. Proposed trade PnL impact
    if proposed_trade is not None:
        symbol = proposed_trade.symbol
        shock = price_shocks.get(symbol, Decimal("0.0"))
        if shock != Decimal("0.0"):
            direction_sign = (
                Decimal("1.0") if proposed_trade.side == "buy" else Decimal("-1.0")
            )
            price = proposed_trade.price
            if price == Decimal("0.0"):
                # Default to current position price or fallback from market_data
                for pos in portfolio_state.positions:
                    if pos.symbol == symbol:
                        price = pos.current_price
                        break
            if price == Decimal("0.0"):
                market_data = market_context.get("market_data", {})
                bars = market_data.get(symbol, [])
                if bars:
                    last_bar = bars[-1]
                    price_str = (
                        last_bar.get("close", "0.0")
                        if isinstance(last_bar, dict)
                        else getattr(last_bar, "close", "0.0")
                    )
                    price = Decimal(str(price_str))

            shocked_price = price * (Decimal("1.0") + shock)
            price_diff = shocked_price - price

            c_size_raw = market_context.get(
                f"{symbol}_contract_size"
            ) or market_context.get("contract_size", "100000.0")
            contract_size = Decimal(str(c_size_raw))

            pnl_quote = (
                proposed_trade.volume * contract_size * price_diff * direction_sign
            )
            _, quote_ccy = _resolve_base_quote(symbol)
            rate = _resolve_conversion_rate(quote_ccy, account_ccy, market_context)
            total_shock_pnl += pnl_quote * rate

    # Return positive value for loss
    loss = -total_shock_pnl
    return max(Decimal("0.0"), loss)


class PriceShockScenario:
    """Stress scenario implementing simple symbol price shocks."""

    def __init__(self, name: str, price_shocks: dict[str, Decimal]) -> None:
        self.name = name
        self.price_shocks = price_shocks

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Evaluate portfolio equity impact under symbol shocks."""
        equity = portfolio_state.equity
        loss = calculate_price_shock_loss(
            portfolio_state, proposed_trade, market_context, self.price_shocks
        )

        projected_equity = max(Decimal("0.0"), equity - loss)
        impact_pct = loss / equity if equity > Decimal("0.0") else Decimal("1.0")

        # Threshold check against max daily loss pct or general stress limit
        threshold = config.max_total_loss_pct_advisory
        pass_status = impact_pct <= threshold
        reason_codes = [] if pass_status else ["STRESS_LOSS_LIMIT_EXCEEDED"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class USDShockScenario:
    """Simulates macro USD strengthening or weakening by 10%."""

    def __init__(self, shock_direction: str = "up") -> None:
        self.name = f"USD Shock {shock_direction.capitalize()}"
        self.direction = shock_direction.lower()

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Evaluate portfolio with shocked USD exchange rates."""
        equity = portfolio_state.equity
        symbols = {pos.symbol for pos in portfolio_state.positions}
        if proposed_trade is not None:
            symbols.add(proposed_trade.symbol)

        price_shocks = {}
        # Apply shocks: USD base -> Up: +10%, Down: -10%.
        # USD quote -> Up: -10%, Down: +10%
        for symbol in symbols:
            base, quote = _resolve_base_quote(symbol)
            if base == "USD":
                price_shocks[symbol] = (
                    Decimal("0.10") if self.direction == "up" else Decimal("-0.10")
                )
            elif quote == "USD":
                price_shocks[symbol] = (
                    Decimal("-0.10") if self.direction == "up" else Decimal("0.10")
                )

        # Calculate loss with price shocks
        loss = calculate_price_shock_loss(
            portfolio_state, proposed_trade, market_context, price_shocks
        )
        projected_equity = max(Decimal("0.0"), equity - loss)
        impact_pct = loss / equity if equity > Decimal("0.0") else Decimal("1.0")

        pass_status = impact_pct <= config.max_total_loss_pct_advisory
        reason_codes = [] if pass_status else ["USD_SHOCK_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class JPYRiskOffScenario:
    """Simulates JPY appreciation (USDJPY -10%, EURJPY -10%, GBPJPY -10%)."""

    def __init__(self) -> None:
        self.name = "JPY Risk-Off"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Evaluate JPY pairs dropping due to appreciation."""
        equity = portfolio_state.equity
        symbols = {pos.symbol for pos in portfolio_state.positions}
        if proposed_trade is not None:
            symbols.add(proposed_trade.symbol)

        price_shocks = {}
        for symbol in symbols:
            _, quote = _resolve_base_quote(symbol)
            if quote == "JPY":
                price_shocks[symbol] = Decimal("-0.10")

        loss = calculate_price_shock_loss(
            portfolio_state, proposed_trade, market_context, price_shocks
        )
        projected_equity = max(Decimal("0.0"), equity - loss)
        impact_pct = loss / equity if equity > Decimal("0.0") else Decimal("1.0")

        pass_status = impact_pct <= config.max_total_loss_pct_advisory
        reason_codes = [] if pass_status else ["JPY_RISK_OFF_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class GBPVolatilityScenario:
    """GBP price shocks of 15% and spread doubling."""

    def __init__(self) -> None:
        self.name = "GBP Volatility Shock"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Evaluate double spreads and GBP price shocks."""
        equity = portfolio_state.equity
        symbols = {pos.symbol for pos in portfolio_state.positions}
        if proposed_trade is not None:
            symbols.add(proposed_trade.symbol)

        # 1. Price shock: evaluate worst-case of +15% and -15%
        gbp_shocks_up = {}
        gbp_shocks_down = {}
        for symbol in symbols:
            base, quote = _resolve_base_quote(symbol)
            if "GBP" in (base, quote):
                gbp_shocks_up[symbol] = Decimal("0.15")
                gbp_shocks_down[symbol] = Decimal("-0.15")

        loss_up = calculate_price_shock_loss(
            portfolio_state, proposed_trade, market_context, gbp_shocks_up
        )
        loss_down = calculate_price_shock_loss(
            portfolio_state, proposed_trade, market_context, gbp_shocks_down
        )
        max_price_loss = max(loss_up, loss_down)

        # 2. Spread cost doubling for GBP pairs
        spread_loss = Decimal("0.0")
        account_ccy = portfolio_state.currency.upper()
        for pos in portfolio_state.positions:
            symbol = pos.symbol
            base, quote = _resolve_base_quote(symbol)
            if "GBP" in (base, quote):
                spread_val = Decimal(
                    str(market_context.get(f"{symbol}_spread", "0.0002"))
                )
                c_size_raw = market_context.get(
                    f"{symbol}_contract_size"
                ) or market_context.get("contract_size", "100000.0")
                contract_size = Decimal(str(c_size_raw))
                # Widening by 2x means adding 1x of spread as additional exit loss
                cost_quote = pos.quantity * contract_size * spread_val
                _, quote_ccy = _resolve_base_quote(symbol)
                rate = _resolve_conversion_rate(quote_ccy, account_ccy, market_context)
                spread_loss += cost_quote * rate

        total_loss = max_price_loss + spread_loss
        projected_equity = max(Decimal("0.0"), equity - total_loss)
        impact_pct = total_loss / equity if equity > Decimal("0.0") else Decimal("1.0")

        pass_status = impact_pct <= config.max_total_loss_pct_advisory
        reason_codes = [] if pass_status else ["GBP_VOLATILITY_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class SpreadWideningScenario:
    """Extreme spread widening (5x) across all instruments."""

    def __init__(self) -> None:
        self.name = "Spread Widening 5x"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,  # noqa: ARG002
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Evaluate cost impact of spread multiplying by 5."""
        equity = portfolio_state.equity
        spread_loss = Decimal("0.0")
        account_ccy = portfolio_state.currency.upper()

        for pos in portfolio_state.positions:
            symbol = pos.symbol
            spread_val = Decimal(str(market_context.get(f"{symbol}_spread", "0.0002")))
            c_size_raw = market_context.get(
                f"{symbol}_contract_size"
            ) or market_context.get("contract_size", "100000.0")
            contract_size = Decimal(str(c_size_raw))

            # Widening by 5x means additional cost of (5-1)/2 = 2x spread
            cost_quote = pos.quantity * contract_size * spread_val * Decimal("2.0")
            _, quote_ccy = _resolve_base_quote(symbol)
            rate = _resolve_conversion_rate(quote_ccy, account_ccy, market_context)
            spread_loss += cost_quote * rate

        projected_equity = max(Decimal("0.0"), equity - spread_loss)
        impact_pct = spread_loss / equity if equity > Decimal("0.0") else Decimal("1.0")

        # Widened spread evaluates against stress advisory limits
        pass_status = impact_pct <= config.max_total_loss_pct_advisory
        reason_codes = [] if pass_status else ["SPREAD_WIDENING_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class SlippageShockScenario:
    """50 pips slippage on the candidate execution."""

    def __init__(self) -> None:
        self.name = "Slippage Shock 50 pips"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Evaluate candidate slippage cost."""
        equity = portfolio_state.equity
        if proposed_trade is None:
            return StressScenarioResult(
                scenario_name=self.name,
                impact_pct=Decimal("0.0"),
                projected_equity=equity,
                pass_status=True,
                reason_codes=[],
            )

        symbol = proposed_trade.symbol
        pip_size = Decimal(str(market_context.get(f"{symbol}_pip_size", "0.0001")))
        c_size_raw = market_context.get(
            f"{symbol}_contract_size"
        ) or market_context.get("contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))

        # Slippage of 50 pips
        slippage_quote = (
            Decimal("50.0") * pip_size * proposed_trade.volume * contract_size
        )
        _, quote_ccy = _resolve_base_quote(symbol)
        rate = _resolve_conversion_rate(
            quote_ccy, portfolio_state.currency.upper(), market_context
        )
        slippage_loss = slippage_quote * rate

        projected_equity = max(Decimal("0.0"), equity - slippage_loss)
        impact_pct = (
            slippage_loss / equity if equity > Decimal("0.0") else Decimal("1.0")
        )

        pass_status = impact_pct <= config.max_total_loss_pct_advisory
        reason_codes = [] if pass_status else ["SLIPPAGE_SHOCK_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class CorrelationToOneScenario:
    """Simulates extreme tail risk when all asset correlations collapse to 1.0."""

    def __init__(self) -> None:
        self.name = "Correlation to One"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Recalculate portfolio volatility and VaR assuming correlation is 1.0."""
        equity = portfolio_state.equity
        symbols = {pos.symbol for pos in portfolio_state.positions}
        if proposed_trade is not None:
            symbols.add(proposed_trade.symbol)

        if not symbols:
            return StressScenarioResult(
                scenario_name=self.name,
                impact_pct=Decimal("0.0"),
                projected_equity=equity,
                pass_status=True,
                reason_codes=[],
            )

        # 1. Fetch assets volatilities from market context
        vols = {}
        for s in symbols:
            # Look up volatility or default to 1% (0.01)
            vol_raw = market_context.get(f"{s}_volatility") or Decimal("0.01")
            vols[s] = Decimal(str(vol_raw))

        # 2. Compute exposures and weights
        from app.services.risk.var_es import _compute_exposures_and_weights

        account_ccy = portfolio_state.currency.upper()
        total_gross, weights = _compute_exposures_and_weights(
            portfolio_state, proposed_trade, market_context, account_ccy
        )

        # Volatility under correlation=1.0 is the weighted sum of absolute volatilities
        stress_vol = sum(
            abs(w) * vols.get(s, Decimal("0.01")) for s, w in weights.items()
        )

        # Calculate Stress VaR at 95% confidence
        z = Decimal("1.64485")  # Z for 0.95
        stress_loss = stress_vol * z * total_gross

        projected_equity = max(Decimal("0.0"), equity - stress_loss)
        impact_pct = stress_loss / equity if equity > Decimal("0.0") else Decimal("1.0")

        # Threshold checks
        pass_status = impact_pct <= config.max_total_loss_pct_advisory
        reason_codes = [] if pass_status else ["CORRELATION_TO_ONE_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class NewsCandleScenario:
    """Instant 5% shock against the direction of positions and proposed trade."""

    def __init__(self) -> None:
        self.name = "News Candle 5% Shock"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Calculate loss from 5% price movement against positions."""
        equity = portfolio_state.equity
        symbols = {pos.symbol for pos in portfolio_state.positions}
        if proposed_trade is not None:
            symbols.add(proposed_trade.symbol)

        price_shocks = {}
        # Unfavorable 5% shock: Long drops 5% (shock=-0.05), Short rises 5% (shock=0.05)
        for pos in portfolio_state.positions:
            price_shocks[pos.symbol] = (
                Decimal("-0.05") if pos.direction == "long" else Decimal("0.05")
            )

        if proposed_trade is not None:
            price_shocks[proposed_trade.symbol] = (
                Decimal("-0.05") if proposed_trade.side == "buy" else Decimal("0.05")
            )

        loss = calculate_price_shock_loss(
            portfolio_state, proposed_trade, market_context, price_shocks
        )
        projected_equity = max(Decimal("0.0"), equity - loss)
        impact_pct = loss / equity if equity > Decimal("0.0") else Decimal("1.0")

        pass_status = impact_pct <= config.max_total_loss_pct_advisory
        reason_codes = [] if pass_status else ["NEWS_CANDLE_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class RolloverLiquidityScenario:
    """Widens spreads by 10x and marks state as illiquid."""

    def __init__(self) -> None:
        self.name = "Rollover Liquidity Shock"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,  # noqa: ARG002
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Evaluate 10x spread cost increase during rollover."""
        equity = portfolio_state.equity
        spread_loss = Decimal("0.0")
        account_ccy = portfolio_state.currency.upper()

        for pos in portfolio_state.positions:
            symbol = pos.symbol
            spread_val = Decimal(str(market_context.get(f"{symbol}_spread", "0.0002")))
            c_size_raw = market_context.get(
                f"{symbol}_contract_size"
            ) or market_context.get("contract_size", "100000.0")
            contract_size = Decimal(str(c_size_raw))

            # Widening by 10x means additional cost of (10-1)/2 = 4.5x spread
            cost_quote = pos.quantity * contract_size * spread_val * Decimal("4.5")
            _, quote_ccy = _resolve_base_quote(symbol)
            rate = _resolve_conversion_rate(quote_ccy, account_ccy, market_context)
            spread_loss += cost_quote * rate

        projected_equity = max(Decimal("0.0"), equity - spread_loss)
        impact_pct = spread_loss / equity if equity > Decimal("0.0") else Decimal("1.0")

        pass_status = impact_pct <= config.max_total_loss_pct_advisory
        reason_codes = [] if pass_status else ["ROLLOVER_LIQUIDITY_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class MarginSpikeScenario:
    """Broker doubles margin requirements."""

    def __init__(self) -> None:
        self.name = "Margin Requirement Spike 2x"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> StressScenarioResult:
        """Check if doubled margin triggers margin call shortfall."""
        equity = portfolio_state.equity
        # Calculate proposed margin if any
        proposed_margin = Decimal("0.0")
        if proposed_trade is not None:
            symbol = proposed_trade.symbol
            price = proposed_trade.price
            if price == Decimal("0.0"):
                bars = market_context.get("market_data", {}).get(symbol, [])
                if bars:
                    last_bar = bars[-1]
                    price_str = (
                        last_bar.get("close", "0.0")
                        if isinstance(last_bar, dict)
                        else getattr(last_bar, "close", "0.0")
                    )
                    price = Decimal(str(price_str))

            c_size_raw = market_context.get(
                f"{symbol}_contract_size"
            ) or market_context.get("contract_size", "100000.0")
            contract_size = Decimal(str(c_size_raw))
            leverage = config.max_effective_leverage
            # Standard estimated margin = Size * ContractSize * Price / Leverage
            _, quote_ccy = _resolve_base_quote(symbol)
            rate = _resolve_conversion_rate(
                quote_ccy, portfolio_state.currency.upper(), market_context
            )
            proposed_margin = (
                proposed_trade.volume * contract_size * price / leverage
            ) * rate

        # Current total margin requirements
        current_margin = sum(pos.margin_required for pos in portfolio_state.positions)
        total_margin = current_margin + proposed_margin

        # Shocked margin requirements = 2x
        shocked_margin = total_margin * Decimal("2.0")

        # Margin Call Check
        free_margin = equity - shocked_margin
        shortfall = -free_margin if free_margin < Decimal("0.0") else Decimal("0.0")

        impact_pct = shortfall / equity if equity > Decimal("0.0") else Decimal("1.0")
        pass_status = free_margin >= Decimal("0.0")
        reason_codes = [] if pass_status else ["MARGIN_CALL_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class PlatformDisconnectScenario:
    """Simulates platform disconnect (connection down)."""

    def __init__(self) -> None:
        self.name = "Platform Disconnect"

    def evaluate(
        self,
        portfolio_state: PortfolioState,  # noqa: ARG002
        proposed_trade: ProposedTrade | None,  # noqa: ARG002
        market_context: dict[str, Any],  # noqa: ARG002
        config: RiskConfig,  # noqa: ARG002
    ) -> StressScenarioResult:
        """Evaluate platform disconnect breach."""
        # Sets status as fail since connection is down
        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=Decimal("1.0"),
            projected_equity=Decimal("0.0"),
            pass_status=False,
            reason_codes=["PLATFORM_DISCONNECTED"],
        )


class StaleQuoteScenario:
    """Checks for stale quote timestamp."""

    def __init__(self) -> None:
        self.name = "Stale Quote Check"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,  # noqa: ARG002
        market_context: dict[str, Any],
        config: RiskConfig,  # noqa: ARG002
    ) -> StressScenarioResult:
        """Evaluate stale quotes check (stale timestamp > 120s)."""
        stale_detected = market_context.get("quote_age_stale", False)
        pass_status = not stale_detected
        reason_codes = [] if pass_status else ["STALE_QUOTE_BREACH"]

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=Decimal("0.0") if pass_status else Decimal("1.0"),
            projected_equity=portfolio_state.equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class ForcedLiquidationScenario:
    """Forced liquidation proximity check (Equity drops below margin required)."""

    def __init__(self) -> None:
        self.name = "Forced Liquidation Proximity"

    def evaluate(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,  # noqa: ARG002
        market_context: dict[str, Any],  # noqa: ARG002
        config: RiskConfig,  # noqa: ARG002
    ) -> StressScenarioResult:
        """Check the size of loss required to trigger stop out / liquidation."""
        equity = portfolio_state.equity
        current_margin = sum(pos.margin_required for pos in portfolio_state.positions)

        # Proximity threshold: Stop out usually triggers when equity <= 50% margin
        stop_out_threshold = current_margin * Decimal("0.5")
        liquidation_proximity = equity - stop_out_threshold

        pass_status = liquidation_proximity > Decimal("0.0")
        reason_codes = [] if pass_status else ["FORCE_LIQUIDATION_BREACH"]

        impact_pct = (
            Decimal("0.0")
            if liquidation_proximity > Decimal("0.0")
            else (
                abs(liquidation_proximity) / equity
                if equity > Decimal("0.0")
                else Decimal("1.0")
            )
        )

        return StressScenarioResult(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


def build_default_scenario_registry() -> StressScenarioRegistry:
    """Build and return a pre-loaded stress testing scenario registry.

    Contains the 12 default macro and execution scenarios.
    """
    registry = StressScenarioRegistry()
    registry.register_scenario("USD Shock Up", USDShockScenario(shock_direction="up"))
    registry.register_scenario(
        "USD Shock Down", USDShockScenario(shock_direction="down")
    )
    registry.register_scenario("JPY Risk-Off", JPYRiskOffScenario())
    registry.register_scenario("GBP Volatility Shock", GBPVolatilityScenario())
    registry.register_scenario("Spread Widening 5x", SpreadWideningScenario())
    registry.register_scenario("Slippage Shock 50 pips", SlippageShockScenario())
    registry.register_scenario("Correlation to One", CorrelationToOneScenario())
    registry.register_scenario("News Candle 5% Shock", NewsCandleScenario())
    registry.register_scenario("Rollover Liquidity Shock", RolloverLiquidityScenario())
    registry.register_scenario("Margin Requirement Spike 2x", MarginSpikeScenario())
    registry.register_scenario("Platform Disconnect", PlatformDisconnectScenario())
    registry.register_scenario("Stale Quote Check", StaleQuoteScenario())
    registry.register_scenario(
        "Forced Liquidation Proximity", ForcedLiquidationScenario()
    )
    return registry


def validate_custom_scenario(config_dict: dict[str, Any]) -> StressScenario:
    """Validate a custom scenario configuration without arbitrary code execution.

    Args:
        config_dict: Configuration containing 'name' and 'price_shocks'.

    Returns:
        StressScenario model.

    Raises:
        ValidationError: If config keys or values are invalid/unsafe.
    """
    name = config_dict.get("name")
    if not isinstance(name, str) or not name.strip():
        msg = "Custom scenario config must have a non-empty string 'name'."
        raise ValidationError(msg)

    shocks_raw = config_dict.get("price_shocks")
    if not isinstance(shocks_raw, dict):
        msg = "Custom scenario config must have a dictionary of 'price_shocks'."
        raise ValidationError(msg)

    price_shocks: dict[str, Decimal] = {}
    for sym, val in shocks_raw.items():
        if not isinstance(sym, str) or not sym.strip():
            msg = f"Invalid symbol key in custom scenario 'price_shocks': {sym}"
            raise ValidationError(msg)
        try:
            dec_val = Decimal(str(val))
        except Exception as e:
            msg = f"Invalid numeric shock value for '{sym}' in custom scenario: {val}"
            raise ValidationError(msg) from e

        # Ensure shock percentage is within sane range [-1.0, 1.0]
        # (100% price movements)
        if abs(dec_val) > Decimal("1.0"):
            msg = (
                f"Unsafe shock value for '{sym}' in custom scenario: "
                f"{dec_val} exceeds 100% boundary."
            )
            raise ValidationError(msg)

        price_shocks[sym] = dec_val

    return StressScenario(name=name, price_shocks=price_shocks)


def run_stress_scenario_analysis(
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: RiskConfig,
    proposed_trade: ProposedTrade | None = None,
) -> list[StressScenarioResult]:
    """Evaluate portfolio resilience under registered stress test scenarios.

    Args:
        portfolio_state: Current portfolio state.
        market_context: Market context containing returns/prices history.
        config: Active risk configuration profile.
        proposed_trade: Optional candidate proposed trade.

    Returns:
        list[StressScenarioResult]: Outcome of stress scenarios evaluation.
    """
    registry = build_default_scenario_registry()
    return registry.evaluate_portfolio(
        portfolio_state=portfolio_state,
        proposed_trade=proposed_trade,
        market_context=market_context,
        config=config,
    )
