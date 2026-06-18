"""Strategy capital allocation governance.

Handles equal-risk budgets, volatility parity budgets, correlation-adjusted parity,
drawdown adjustments, and proposed allocation limit validations.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    PortfolioState,
    ProposedAllocation,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)


def equal_risk_allocation(
    strategies: list[str], total_budget: Decimal
) -> dict[str, Decimal]:
    """Calculate equal-risk budget allocation across active strategies.

    Args:
        strategies: List of active strategy identifiers.
        total_budget: Total capital budget to allocate.

    Returns:
        dict[str, Decimal]: Map of strategy ID to allocated capital.
    """
    if not strategies:
        return {}
    if total_budget <= Decimal("0.0"):
        return dict.fromkeys(strategies, Decimal("0.0"))

    num_strategies = Decimal(str(len(strategies)))
    equal_share = total_budget / num_strategies

    return dict.fromkeys(strategies, equal_share)


def volatility_parity_allocation(
    strategies: list[str], volatilities: dict[str, Decimal], total_budget: Decimal
) -> dict[str, Decimal]:
    """Calculate volatility parity allocation inversely proportional to risk.

    Args:
        strategies: List of active strategy identifiers.
        volatilities: Dictionary mapping strategy ID to rolling volatility.
        total_budget: Total capital budget to allocate.

    Returns:
        dict[str, Decimal]: Map of strategy ID to allocated capital.
    """
    if not strategies:
        return {}
    if total_budget <= Decimal("0.0"):
        return dict.fromkeys(strategies, Decimal("0.0"))

    default_vol = Decimal("0.02")
    inv_vols: dict[str, Decimal] = {}
    sum_inv_vol = Decimal("0.0")

    for strat in strategies:
        vol = volatilities.get(strat, default_vol)
        if vol <= Decimal("0.0"):
            vol = default_vol
        inv_vol = Decimal("1.0") / vol
        inv_vols[strat] = inv_vol
        sum_inv_vol += inv_vol

    if sum_inv_vol <= Decimal("0.0"):
        return equal_risk_allocation(strategies, total_budget)

    allocations: dict[str, Decimal] = {}
    for strat in strategies:
        weight = inv_vols[strat] / sum_inv_vol
        allocations[strat] = weight * total_budget

    return allocations


def correlation_adjusted_risk_parity_allocation(
    strategies: list[str],
    volatilities: dict[str, Decimal],
    correlation_matrix: dict[str, dict[str, Decimal]],
    total_budget: Decimal,
) -> dict[str, Decimal]:
    """Calculate correlation-adjusted volatility parity allocations.

    Adjusts the inverse-volatility weight of each strategy by the mean correlation
    of its returns with all other active strategies in the portfolio.

    Args:
        strategies: List of active strategy identifiers.
        volatilities: Dictionary mapping strategy ID to rolling volatility.
        correlation_matrix: Pairwise Pearson correlation dictionary.
        total_budget: Total capital budget to allocate.

    Returns:
        dict[str, Decimal]: Map of strategy ID to allocated capital.
    """
    if not strategies:
        return {}
    if total_budget <= Decimal("0.0"):
        return dict.fromkeys(strategies, Decimal("0.0"))

    default_vol = Decimal("0.02")
    default_corr = Decimal("0.0")
    inv_factors: dict[str, Decimal] = {}
    sum_inv_factor = Decimal("0.0")

    for strat in strategies:
        vol = volatilities.get(strat, default_vol)
        if vol <= Decimal("0.0"):
            vol = default_vol

        # Compute average correlation with other active strategies
        corr_sum = Decimal("0.0")
        corr_count = 0
        strat_corrs = correlation_matrix.get(strat, {})

        for other in strategies:
            if other == strat:
                continue
            corr_val = strat_corrs.get(other, default_corr)
            corr_sum += Decimal(str(corr_val))
            corr_count += 1

        avg_corr = (
            corr_sum / Decimal(str(corr_count)) if corr_count > 0 else Decimal("0.0")
        )

        # Denominator represents volatility adjusted by diversification factor
        denom = vol * (Decimal("1.0") + avg_corr)
        if denom <= Decimal("0.0"):
            denom = Decimal("0.0001")

        inv_factor = Decimal("1.0") / denom
        inv_factors[strat] = inv_factor
        sum_inv_factor += inv_factor

    if sum_inv_factor <= Decimal("0.0"):
        return equal_risk_allocation(strategies, total_budget)

    allocations: dict[str, Decimal] = {}
    for strat in strategies:
        weight = inv_factors[strat] / sum_inv_factor
        allocations[strat] = weight * total_budget

    return allocations


def apply_regime_weighting(
    allocations: dict[str, Decimal], regime_multiplier: Decimal
) -> dict[str, Decimal]:
    """Scale allocations based on a market regime multiplier.

    Args:
        allocations: Map of strategy ID to allocated capital.
        regime_multiplier: Regime-based scaling factor (e.g. 0.5 for caution).

    Returns:
        dict[str, Decimal]: Adjusted allocations.
    """
    return {strat: alloc * regime_multiplier for strat, alloc in allocations.items()}


def apply_drawdown_adjustment(
    allocations: dict[str, Decimal], strategy_drawdown_multipliers: dict[str, Decimal]
) -> dict[str, Decimal]:
    """Scale allocations down individually based on strategy drawdown status.

    Args:
        allocations: Map of strategy ID to allocated capital.
        strategy_drawdown_multipliers: Throttling multipliers by strategy.

    Returns:
        dict[str, Decimal]: Adjusted allocations.
    """
    adjusted: dict[str, Decimal] = {}
    for strat, alloc in allocations.items():
        multiplier = strategy_drawdown_multipliers.get(strat, Decimal("1.0"))
        adjusted[strat] = alloc * multiplier
    return adjusted


def _check_basic_limits(
    portfolio_state: PortfolioState,
    proposal: ProposedAllocation,
    config: RiskConfig,
) -> LimitResult | None:
    """Validate proposal against total equity budget and strategy caps."""
    equity = portfolio_state.equity
    if equity <= Decimal("0.0"):
        return LimitResult(
            limit_name="verify_allocation_limits",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.MARGIN_BREACH,
            message="Cannot allocate budget with zero or negative account equity.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    # 1. Reject allocations breaching total portfolio limits (cannot exceed equity)
    total_proposed = sum(proposal.allocations.values())
    if total_proposed > equity:
        return LimitResult(
            limit_name="verify_allocation_limits",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.MARGIN_BREACH,
            message=(
                f"Total proposed allocation exceeds account equity: "
                f"{total_proposed:.2f} > {equity:.2f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"total_proposed": float(total_proposed), "equity": float(equity)},
        )

    # 2. Reject allocations breaching individual strategy limits
    max_single_limit = equity * config.max_strategy_allocation_pct
    for strat_id, alloc in proposal.allocations.items():
        if alloc > max_single_limit:
            return LimitResult(
                limit_name="verify_allocation_limits",
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.ALLOCATION_LIMIT_BREACH,
                message=(
                    f"Proposed allocation for '{strat_id}' exceeds maximum single "
                    f"strategy allocation limit of "
                    f"{config.max_strategy_allocation_pct:.0%}: "
                    f"{alloc:.2f} > {max_single_limit:.2f}."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                details={"strategy_id": strat_id, "proposed": float(alloc)},
            )
    return None


def _check_allocation_increase_gates(
    portfolio_state: PortfolioState,
    proposal: ProposedAllocation,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult | None:
    """Enforce performance evidence checks and governed approval tokens."""
    strategy_evidence = market_context.get("strategy_evidence", {})
    is_live = market_context.get("mode") in {
        "micro_live",
        "full_live",
    } or market_context.get("environment") in {"production", "live"}

    for strat_id, proposed_alloc in proposal.allocations.items():
        current_alloc = portfolio_state.strategy_allocations.get(
            strat_id, Decimal("0.0")
        )

        if proposed_alloc > current_alloc:
            evidence = strategy_evidence.get(strat_id)
            if not evidence:
                status = (
                    RiskDecisionStatus.REJECT
                    if is_live
                    else RiskDecisionStatus.NEEDS_MORE_EVIDENCE
                )
                msg = (
                    f"Missing historical performance evidence to increase "
                    f"allocation for strategy '{strat_id}'."
                )
                return LimitResult(
                    limit_name="verify_allocation_limits",
                    status=status,
                    reason_code=RiskReasonCode.STALE_EVIDENCE,
                    message=msg,
                    severity=(
                        RiskSeverity.WARNING
                        if not is_live
                        else RiskSeverity.HARD_BREACH
                    ),
                    breached=True,
                )

            trades = int(evidence.get("trade_count", 0))
            sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))

            if trades < config.min_backtest_trades:
                status = (
                    RiskDecisionStatus.REJECT
                    if is_live
                    else RiskDecisionStatus.NEEDS_MORE_EVIDENCE
                )
                return LimitResult(
                    limit_name="verify_allocation_limits",
                    status=status,
                    reason_code=RiskReasonCode.STALE_EVIDENCE,
                    message=(
                        f"Insufficient trades for strategy '{strat_id}': "
                        f"{trades} < required {config.min_backtest_trades}."
                    ),
                    severity=(
                        RiskSeverity.WARNING
                        if not is_live
                        else RiskSeverity.HARD_BREACH
                    ),
                    breached=True,
                )

            if sharpe < config.min_backtest_sharpe:
                status = (
                    RiskDecisionStatus.REJECT
                    if is_live
                    else RiskDecisionStatus.NEEDS_MORE_EVIDENCE
                )
                return LimitResult(
                    limit_name="verify_allocation_limits",
                    status=status,
                    reason_code=RiskReasonCode.STALE_EVIDENCE,
                    message=(
                        f"Sharpe ratio for strategy '{strat_id}' too low: "
                        f"{sharpe:.2f} < required {config.min_backtest_sharpe:.2f}."
                    ),
                    severity=(
                        RiskSeverity.WARNING
                        if not is_live
                        else RiskSeverity.HARD_BREACH
                    ),
                    breached=True,
                )

            increase_pct = Decimal("1.0")
            if current_alloc > Decimal("0.0"):
                increase_pct = (proposed_alloc - current_alloc) / current_alloc

            if increase_pct > config.max_allocation_increase_pct:
                approval_token_valid = market_context.get("approval_token_valid", False)
                if not approval_token_valid:
                    return LimitResult(
                        limit_name="verify_allocation_limits",
                        status=RiskDecisionStatus.NEEDS_APPROVAL,
                        reason_code=RiskReasonCode.APPROVAL_REQUIRED,
                        message=(
                            f"Allocation increase of {increase_pct:.1%} for "
                            f"strategy '{strat_id}' exceeds limit threshold of "
                            f"{config.max_allocation_increase_pct:.1%}. "
                            f"Governed approval token required."
                        ),
                        severity=RiskSeverity.WARNING,
                        breached=True,
                        details={
                            "strategy_id": strat_id,
                            "increase_pct": float(increase_pct),
                        },
                    )
    return None


def verify_allocation_limits(
    portfolio_state: PortfolioState,
    proposal: ProposedAllocation,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Enforce capital boundaries and gate allocation increases.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposal: Requested allocation mappings.
        market_context: Injected market parameters and evidence.
        config: Active risk configuration limits.

    Returns:
        LimitResult: Outcome of the allocation check.
    """
    basic_check = _check_basic_limits(portfolio_state, proposal, config)
    if basic_check is not None:
        return basic_check

    increase_check = _check_allocation_increase_gates(
        portfolio_state, proposal, market_context, config
    )
    if increase_check is not None:
        return increase_check

    return LimitResult(
        limit_name="verify_allocation_limits",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=(
            "Proposed strategy allocations comply with limits and governance policies."
        ),
        severity=RiskSeverity.INFO,
        breached=False,
    )
