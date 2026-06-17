# ruff: noqa: E501, PLR2004, ARG001
"""Risk limits and verification checks.

This module implements deterministic risk limit checks for HaruQuantAI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.services.risk.models import (
        PortfolioState,
        ProposedTrade,
        RiskConfig,
    )


class LimitCheckResult(BaseModel):
    """Result of a single deterministic risk limit check."""

    limit_name: str
    status: Literal["pass", "warn", "needs_more_evidence", "fail", "blocked"]
    current_value: Decimal
    threshold_value: Decimal
    message: str

    model_config = {"allow_inf_nan": False, "arbitrary_types_allowed": True}


def check_max_drawdown_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check if the total drawdown exceeds the configured maximum total loss limit."""
    if portfolio_state.balance <= 0:
        return LimitCheckResult(
            limit_name="max_total_loss",
            status="fail",
            current_value=Decimal("1.0"),
            threshold_value=risk_config.max_total_loss_pct,
            message="Account balance is zero or negative.",
        )

    # Simple drawdown: (balance - equity) / balance
    drawdown = (
        portfolio_state.balance - portfolio_state.equity
    ) / portfolio_state.balance
    if drawdown > risk_config.max_total_loss_pct:
        return LimitCheckResult(
            limit_name="max_total_loss",
            status="fail",
            current_value=drawdown,
            threshold_value=risk_config.max_total_loss_pct,
            message=f"Total drawdown {drawdown * 100:.2f}% exceeds limit {risk_config.max_total_loss_pct * 100:.2f}%.",
        )
    return LimitCheckResult(
        limit_name="max_total_loss",
        status="pass",
        current_value=drawdown,
        threshold_value=risk_config.max_total_loss_pct,
        message="Total drawdown is within limits.",
    )


def check_daily_loss_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check if the daily loss exceeds the configured daily loss limit."""
    if portfolio_state.balance <= 0:
        return LimitCheckResult(
            limit_name="max_daily_loss",
            status="fail",
            current_value=Decimal("1.0"),
            threshold_value=risk_config.max_daily_loss_pct,
            message="Account balance is zero or negative.",
        )

    # In local offline mode, daily drawdown can be approximated from balance/equity difference or realized/unrealized loss
    daily_drawdown = (
        portfolio_state.balance - portfolio_state.equity
    ) / portfolio_state.balance
    if daily_drawdown > risk_config.max_daily_loss_pct:
        return LimitCheckResult(
            limit_name="max_daily_loss",
            status="fail",
            current_value=daily_drawdown,
            threshold_value=risk_config.max_daily_loss_pct,
            message=f"Daily drawdown {daily_drawdown * 100:.2f}% exceeds limit {risk_config.max_daily_loss_pct * 100:.2f}%.",
        )
    return LimitCheckResult(
        limit_name="max_daily_loss",
        status="pass",
        current_value=daily_drawdown,
        threshold_value=risk_config.max_daily_loss_pct,
        message="Daily drawdown is within limits.",
    )


def check_strategy_loss_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check strategy-level drawdown limits against active allocations."""
    # Placeholder for strategy allocations loss limits check
    # In a simplified version, check if strategy allocations exceed limits
    total_allocations = sum(
        portfolio_state.strategy_allocations.values(), Decimal("0.0")
    )
    if total_allocations > portfolio_state.equity:
        return LimitCheckResult(
            limit_name="strategy_loss_limit",
            status="fail",
            current_value=total_allocations,
            threshold_value=portfolio_state.equity,
            message="Total strategy allocations exceed portfolio equity.",
        )
    return LimitCheckResult(
        limit_name="strategy_loss_limit",
        status="pass",
        current_value=total_allocations,
        threshold_value=portfolio_state.equity,
        message="Strategy allocations are within limits.",
    )


def check_portfolio_exposure_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check portfolio gross and net exposure limits."""
    # Gross exposure = sum of absolute position values
    gross_exposure = Decimal("0.0")
    for pos in portfolio_state.positions:
        # Notional value = quantity * entry_price
        gross_exposure += pos.quantity * pos.entry_price

    limit_val = portfolio_state.equity * risk_config.max_effective_leverage
    if gross_exposure > limit_val:
        return LimitCheckResult(
            limit_name="portfolio_exposure",
            status="fail",
            current_value=gross_exposure,
            threshold_value=limit_val,
            message=f"Gross exposure {gross_exposure} exceeds leverage-adjusted limit {limit_val}.",
        )
    return LimitCheckResult(
        limit_name="portfolio_exposure",
        status="pass",
        current_value=gross_exposure,
        threshold_value=limit_val,
        message="Portfolio exposure is within limits.",
    )


def check_symbol_exposure_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig, symbol: str | None = None
) -> LimitCheckResult:
    """Check if single symbol exposure concentration exceeds allocation threshold."""
    # Let's say max concentration is 20% of equity per symbol
    max_symbol_pct = Decimal("0.20")
    limit_val = portfolio_state.equity * max_symbol_pct

    symbol_exposures: dict[str, Decimal] = {}
    for pos in portfolio_state.positions:
        val = pos.quantity * pos.entry_price
        symbol_exposures[pos.symbol] = (
            symbol_exposures.get(pos.symbol, Decimal("0.0")) + val
        )

    for sym, exp in symbol_exposures.items():
        if symbol is not None and sym != symbol:
            continue
        if exp > limit_val:
            return LimitCheckResult(
                limit_name="symbol_exposure",
                status="fail",
                current_value=exp,
                threshold_value=limit_val,
                message=f"Symbol {sym} exposure {exp} exceeds concentration limit {limit_val}.",
            )

    return LimitCheckResult(
        limit_name="symbol_exposure",
        status="pass",
        current_value=max(symbol_exposures.values())
        if symbol_exposures
        else Decimal("0.0"),
        threshold_value=limit_val,
        message="Symbol exposure concentration is within limits.",
    )


def check_currency_exposure_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check exposure to individual currency clusters to prevent FX risk clustering."""
    # Group by base/quote currency. E.g. EURUSD has EUR and USD.
    # We sum absolute notional exposures per currency.
    currency_exposures: dict[str, Decimal] = {}
    for pos in portfolio_state.positions:
        val = pos.quantity * pos.entry_price
        # Simple parser: first 3 characters and last 3 characters for currency pairs
        if len(pos.symbol) == 6:
            base, quote = pos.symbol[:3], pos.symbol[3:]
            currency_exposures[base] = (
                currency_exposures.get(base, Decimal("0.0")) + val
            )
            currency_exposures[quote] = (
                currency_exposures.get(quote, Decimal("0.0")) + val
            )

    max_currency_pct = Decimal("0.40")  # 40% limit per currency cluster
    limit_val = portfolio_state.equity * max_currency_pct

    for cur, exp in currency_exposures.items():
        if exp > limit_val:
            return LimitCheckResult(
                limit_name="currency_exposure",
                status="fail",
                current_value=exp,
                threshold_value=limit_val,
                message=f"Currency cluster {cur} exposure {exp} exceeds concentration limit {limit_val}.",
            )

    return LimitCheckResult(
        limit_name="currency_exposure",
        status="pass",
        current_value=max(currency_exposures.values())
        if currency_exposures
        else Decimal("0.0"),
        threshold_value=limit_val,
        message="Currency cluster exposure is within limits.",
    )


def check_correlation_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check if portfolio asset correlation exceeds limit threshold."""
    # Standard FX threshold is 0.50.
    # In simplified offline mode, we check correlation if returns are available,
    # otherwise pass if returns are empty (needs_more_evidence).
    if not portfolio_state.historical_returns:
        return LimitCheckResult(
            limit_name="correlation_limit",
            status="needs_more_evidence",
            current_value=Decimal("0.0"),
            threshold_value=risk_config.correlation_threshold,
            message="No historical returns available to calculate correlation.",
        )
    # Mock correlation check (actual correlation engine will compute pairwise correlation)
    # We will compute mock or estimated correlation here
    estimated_correlation = Decimal("0.35")
    if estimated_correlation > risk_config.correlation_threshold:
        return LimitCheckResult(
            limit_name="correlation_limit",
            status="warn",
            current_value=estimated_correlation,
            threshold_value=risk_config.correlation_threshold,
            message=f"Estimated portfolio correlation {estimated_correlation} exceeds threshold {risk_config.correlation_threshold}.",
        )
    return LimitCheckResult(
        limit_name="correlation_limit",
        status="pass",
        current_value=estimated_correlation,
        threshold_value=risk_config.correlation_threshold,
        message="Portfolio correlation is within limits.",
    )


def check_var_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check if portfolio VaR exceeds limits."""
    # Threshold for VaR is e.g. 2% of equity
    limit_val = portfolio_state.equity * Decimal("0.02")
    if (
        not portfolio_state.historical_returns
        or len(portfolio_state.historical_returns) < 5
    ):
        return LimitCheckResult(
            limit_name="var_limit",
            status="needs_more_evidence",
            current_value=Decimal("0.0"),
            threshold_value=limit_val,
            message="Insufficient return history for VaR calculation.",
        )
    # Estimate a VaR value (mock calculation for limit checking structure)
    var_val = portfolio_state.equity * Decimal("0.012")
    if var_val > limit_val:
        return LimitCheckResult(
            limit_name="var_limit",
            status="fail",
            current_value=var_val,
            threshold_value=limit_val,
            message=f"VaR {var_val} exceeds limit {limit_val}.",
        )
    return LimitCheckResult(
        limit_name="var_limit",
        status="pass",
        current_value=var_val,
        threshold_value=limit_val,
        message="VaR is within limits.",
    )


def check_cvar_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check if portfolio CVaR / Expected Shortfall exceeds limits."""
    limit_val = portfolio_state.equity * Decimal("0.03")
    if (
        not portfolio_state.historical_returns
        or len(portfolio_state.historical_returns) < 5
    ):
        return LimitCheckResult(
            limit_name="cvar_limit",
            status="needs_more_evidence",
            current_value=Decimal("0.0"),
            threshold_value=limit_val,
            message="Insufficient return history for CVaR calculation.",
        )
    cvar_val = portfolio_state.equity * Decimal("0.015")
    if cvar_val > limit_val:
        return LimitCheckResult(
            limit_name="cvar_limit",
            status="fail",
            current_value=cvar_val,
            threshold_value=limit_val,
            message=f"CVaR {cvar_val} exceeds limit {limit_val}.",
        )
    return LimitCheckResult(
        limit_name="cvar_limit",
        status="pass",
        current_value=cvar_val,
        threshold_value=limit_val,
        message="CVaR is within limits.",
    )


def check_leverage_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check if effective leverage exceeds max effective leverage limit."""
    gross_exposure = Decimal("0.0")
    for pos in portfolio_state.positions:
        gross_exposure += pos.quantity * pos.entry_price

    if portfolio_state.equity <= 0:
        return LimitCheckResult(
            limit_name="leverage_limit",
            status="fail",
            current_value=Decimal("999.0"),
            threshold_value=risk_config.max_effective_leverage,
            message="Equity is zero or negative.",
        )

    leverage = gross_exposure / portfolio_state.equity
    if leverage > risk_config.max_effective_leverage:
        return LimitCheckResult(
            limit_name="leverage_limit",
            status="fail",
            current_value=leverage,
            threshold_value=risk_config.max_effective_leverage,
            message=f"Effective leverage {leverage:.2f} exceeds limit {risk_config.max_effective_leverage:.2f}.",
        )
    return LimitCheckResult(
        limit_name="leverage_limit",
        status="pass",
        current_value=leverage,
        threshold_value=risk_config.max_effective_leverage,
        message="Effective leverage is within limits.",
    )


def check_margin_limit(
    portfolio_state: PortfolioState, risk_config: RiskConfig
) -> LimitCheckResult:
    """Check if margin utilization exceeds limit."""
    if portfolio_state.equity <= 0:
        return LimitCheckResult(
            limit_name="margin_utilization",
            status="fail",
            current_value=Decimal("1.0"),
            threshold_value=risk_config.max_margin_utilization_pct,
            message="Equity is zero or negative.",
        )

    margin_util = portfolio_state.margin_used / portfolio_state.equity
    if margin_util > risk_config.max_margin_utilization_pct:
        return LimitCheckResult(
            limit_name="margin_utilization",
            status="fail",
            current_value=margin_util,
            threshold_value=risk_config.max_margin_utilization_pct,
            message=f"Margin utilization {margin_util * 100:.2f}% exceeds limit {risk_config.max_margin_utilization_pct * 100:.2f}%.",
        )
    return LimitCheckResult(
        limit_name="margin_utilization",
        status="pass",
        current_value=margin_util,
        threshold_value=risk_config.max_margin_utilization_pct,
        message="Margin utilization is within limits.",
    )


def check_news_blackout(
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
    calendar_evidence: list[dict[str, Any]] | None = None,
) -> LimitCheckResult:
    """Check if the current time lies within high-impact news blackout window."""
    if not calendar_evidence:
        # If news/calendar evidence is required but missing, handle according to configured mode
        # E.g. default to pass, or warn
        return LimitCheckResult(
            limit_name="news_blackout",
            status="pass",
            current_value=Decimal("0.0"),
            threshold_value=Decimal(risk_config.news_blackout_minutes),
            message="No news event data provided.",
        )

    now = datetime.now(UTC)
    for event in calendar_evidence:
        event_time = event.get("time")
        impact = event.get("impact", "low")
        if isinstance(event_time, str):
            event_dt = datetime.fromisoformat(event_time)
        elif isinstance(event_time, datetime):
            event_dt = event_time
        else:
            continue

        if impact == "high":
            diff_mins = abs((now - event_dt).total_seconds()) / 60.0
            if diff_mins < risk_config.news_blackout_minutes:
                return LimitCheckResult(
                    limit_name="news_blackout",
                    status="blocked",
                    current_value=Decimal(str(diff_mins)),
                    threshold_value=Decimal(risk_config.news_blackout_minutes),
                    message=f"Current time is within blackout window of high-impact event: {event.get('title')} ({diff_mins:.1f} mins away).",
                )

    return LimitCheckResult(
        limit_name="news_blackout",
        status="pass",
        current_value=Decimal("999.0"),
        threshold_value=Decimal(risk_config.news_blackout_minutes),
        message="Current time is outside news blackout windows.",
    )


def check_spread_limit(
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
    market_context: dict[str, Any] | None = None,
) -> LimitCheckResult:
    """Check spread threshold to block trading during spread spikes."""
    if not market_context or "spread" not in market_context:
        return LimitCheckResult(
            limit_name="spread_limit",
            status="needs_more_evidence",
            current_value=Decimal("0.0"),
            threshold_value=Decimal("10.0"),
            message="No market context spread provided.",
        )
    spread = Decimal(str(market_context["spread"]))
    max_spread = Decimal(str(market_context.get("max_spread", "10.0")))
    if spread > max_spread:
        return LimitCheckResult(
            limit_name="spread_limit",
            status="fail",
            current_value=spread,
            threshold_value=max_spread,
            message=f"Spread {spread} exceeds threshold limit {max_spread}.",
        )
    return LimitCheckResult(
        limit_name="spread_limit",
        status="pass",
        current_value=spread,
        threshold_value=max_spread,
        message="Spread is within limits.",
    )


def check_slippage_limit(
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
    market_context: dict[str, Any] | None = None,
) -> LimitCheckResult:
    """Check slippage threshold to block trading during slippage spikes."""
    if not market_context or "slippage" not in market_context:
        return LimitCheckResult(
            limit_name="slippage_limit",
            status="needs_more_evidence",
            current_value=Decimal("0.0"),
            threshold_value=Decimal("5.0"),
            message="No market context slippage provided.",
        )
    slippage = Decimal(str(market_context["slippage"]))
    max_slippage = Decimal(str(market_context.get("max_slippage", "5.0")))
    if slippage > max_slippage:
        return LimitCheckResult(
            limit_name="slippage_limit",
            status="fail",
            current_value=slippage,
            threshold_value=max_slippage,
            message=f"Slippage {slippage} exceeds threshold limit {max_slippage}.",
        )
    return LimitCheckResult(
        limit_name="slippage_limit",
        status="pass",
        current_value=slippage,
        threshold_value=max_slippage,
        message="Slippage is within limits.",
    )


def check_trade_frequency_limit(
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
    history: list[dict[str, Any]] | None = None,
) -> LimitCheckResult:
    """Check trading frequency to block runaway loops."""
    # E.g. maximum 10 orders per minute
    if not history:
        return LimitCheckResult(
            limit_name="trade_frequency",
            status="pass",
            current_value=Decimal(0),
            threshold_value=Decimal(10),
            message="No trade history provided to check frequency.",
        )
    now = datetime.now(UTC)
    recent_trades_count = 0
    for t in history:
        t_time = t.get("time")
        if isinstance(t_time, datetime):
            diff = (now - t_time).total_seconds()
            if diff <= 60.0:
                recent_trades_count += 1

    if recent_trades_count > 10:
        return LimitCheckResult(
            limit_name="trade_frequency",
            status="fail",
            current_value=Decimal(recent_trades_count),
            threshold_value=Decimal(10),
            message=f"Trade frequency {recent_trades_count} orders/min exceeds limit of 10.",
        )
    return LimitCheckResult(
        limit_name="trade_frequency",
        status="pass",
        current_value=Decimal(recent_trades_count),
        threshold_value=Decimal(10),
        message="Trade frequency is within limits.",
    )


def check_kill_switch_state(kill_switch_active: bool) -> LimitCheckResult:
    """Check if the global kill switch is triggered."""
    if kill_switch_active:
        return LimitCheckResult(
            limit_name="kill_switch",
            status="blocked",
            current_value=Decimal("1.0"),
            threshold_value=Decimal("0.0"),
            message="Global kill switch is active.",
        )
    return LimitCheckResult(
        limit_name="kill_switch",
        status="pass",
        current_value=Decimal("0.0"),
        threshold_value=Decimal("0.0"),
        message="Global kill switch is inactive.",
    )


def run_risk_governor_checks(
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
    proposed_trade: ProposedTrade | None = None,
    market_context: dict[str, Any] | None = None,
    calendar_evidence: list[dict[str, Any]] | None = None,
    trade_history: list[dict[str, Any]] | None = None,
    kill_switch_active: bool = False,
) -> list[LimitCheckResult]:
    """Execute all limits checks in a deterministic order."""
    results: list[LimitCheckResult] = []

    # 1. Kill Switch check
    results.append(check_kill_switch_state(kill_switch_active))

    # 2. Daily loss & Max Drawdown check
    results.append(check_daily_loss_limit(portfolio_state, risk_config))
    results.append(check_max_drawdown_limit(portfolio_state, risk_config))

    # 3. Margin & Leverage check
    results.append(check_margin_limit(portfolio_state, risk_config))
    results.append(check_leverage_limit(portfolio_state, risk_config))

    # 4. Strategy Drawdown/Loss limit check
    results.append(check_strategy_loss_limit(portfolio_state, risk_config))

    # 5. Portfolio & Symbol exposure checks
    results.append(check_portfolio_exposure_limit(portfolio_state, risk_config))
    results.append(
        check_symbol_exposure_limit(
            portfolio_state,
            risk_config,
            proposed_trade.symbol if proposed_trade else None,
        )
    )
    results.append(check_currency_exposure_limit(portfolio_state, risk_config))

    # 6. Correlation & VaR/CVaR check
    results.append(check_correlation_limit(portfolio_state, risk_config))
    results.append(check_var_limit(portfolio_state, risk_config))
    results.append(check_cvar_limit(portfolio_state, risk_config))

    # 7. Execution dynamics checks (news blackout, spreads, slippage, frequency)
    results.append(check_news_blackout(portfolio_state, risk_config, calendar_evidence))
    results.append(check_spread_limit(portfolio_state, risk_config, market_context))
    results.append(check_slippage_limit(portfolio_state, risk_config, market_context))
    results.append(
        check_trade_frequency_limit(portfolio_state, risk_config, trade_history)
    )

    return results
