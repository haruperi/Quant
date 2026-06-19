"""Strategy capital allocation governance.

Handles equal-risk budgets, volatility parity budgets, correlation-adjusted parity,
drawdown adjustments, and proposed allocation limit validations.
"""

from __future__ import annotations

import math
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import Field

from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    PortfolioState,
    ProposedAllocation,
    RiskConfig,
    RiskContract,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)

# Confidence level float constants for VaR/ES calculations
CONF_99 = 0.99
CONF_95 = 0.95
CONF_90 = 0.90

Z_99 = Decimal("2.326")
Z_95 = Decimal("1.645")
Z_90 = Decimal("1.282")


class AllocationMethod(StrEnum):
    """Supported capital allocation methods."""

    EQUAL_RISK = "equal_risk"
    VOLATILITY_PARITY = "volatility_parity"
    CORRELATION_ADJUSTED_PARITY = "correlation_adjusted_parity"
    REGIME_WEIGHTED = "regime_weighted"
    DRAWDOWN_ADJUSTED = "drawdown_adjusted"


class AllocationReviewRequest(RiskContract):
    """The request envelope for capital allocation reviews."""

    portfolio_state: PortfolioState = Field(
        ..., description="Current portfolio snapshot."
    )
    proposal: ProposedAllocation = Field(
        ..., description="Proposed strategy capital allocations."
    )
    market_context: dict[str, Any] = Field(
        default_factory=dict, description="Market parameters and evidence."
    )
    config: RiskConfig | None = Field(
        default=None, description="Optional active risk configuration limits."
    )


class AllocationReviewResult(RiskContract):
    """Outcome of the allocation governance review process."""

    status: RiskDecisionStatus = Field(
        ..., description="Final governance decision status."
    )
    reason_code: RiskReasonCode = Field(
        ..., description="Reason code associated with any breach."
    )
    message: str = Field(..., description="Human-readable detail message.")
    severity: RiskSeverity = Field(..., description="Severity level of the decision.")
    breached: bool = Field(..., description="True if any safety limits were breached.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Calculated values and context info."
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


def calculate_equal_risk_budget(
    strategies: list[str], total_budget: Decimal
) -> dict[str, Decimal]:
    """Calculate equal-risk budget allocation across active strategies."""
    return equal_risk_allocation(strategies, total_budget)


def calculate_volatility_parity_budget(
    strategies: list[str], volatilities: dict[str, Decimal], total_budget: Decimal
) -> dict[str, Decimal]:
    """Calculate volatility parity allocation inversely proportional to risk."""
    return volatility_parity_allocation(strategies, volatilities, total_budget)


def calculate_correlation_adjusted_budget(
    strategies: list[str],
    volatilities: dict[str, Decimal],
    correlation_matrix: dict[str, dict[str, Decimal]],
    total_budget: Decimal,
) -> dict[str, Decimal]:
    """Calculate correlation-adjusted volatility parity allocations."""
    return correlation_adjusted_risk_parity_allocation(
        strategies, volatilities, correlation_matrix, total_budget
    )


def calculate_regime_weighted_budget(
    strategies: list[str],
    volatilities: dict[str, Decimal],
    correlation_matrix: dict[str, dict[str, Decimal]],
    total_budget: Decimal,
    regime_multiplier: Decimal,
) -> dict[str, Decimal]:
    """Scale allocations based on a market regime multiplier."""
    base = correlation_adjusted_risk_parity_allocation(
        strategies, volatilities, correlation_matrix, total_budget
    )
    return apply_regime_weighting(base, regime_multiplier)


class RiskAllocator:
    """Governance engine checking strategy capital allocation proposals."""

    def __init__(self, config: RiskConfig) -> None:
        """Initialize the allocator engine with active configuration profile."""
        self.config = config

    def calculate_allocated_budget(
        self,
        strategies: list[str],
        total_budget: Decimal,
        market_context: dict[str, Any],
        method: AllocationMethod | str | None = None,
    ) -> dict[str, Decimal]:
        """Calculate strategy budgets based on chosen allocation method.

        Args:
            strategies: List of active strategy identifiers.
            total_budget: Total capital budget to allocate.
            market_context: Injected market parameters and evidence.
            method: Specific allocation method. If None, uses config default.

        Returns:
            dict[str, Decimal]: Map of strategy ID to allocated capital.
        """
        if not strategies:
            return {}
        if total_budget <= Decimal("0.0"):
            return dict.fromkeys(strategies, Decimal("0.0"))

        if method is None:
            method = self.config.allocation_method

        is_live = market_context.get("mode") in {
            "micro_live",
            "full_live",
        } or market_context.get("environment") in {"production", "live"}

        # Default live allocation behavior:
        # Conservative correlation-adjusted volatility risk parity
        if is_live and (not method or method == "default"):
            method = AllocationMethod.CORRELATION_ADJUSTED_PARITY

        volatilities = market_context.get("volatilities", {})
        correlation_matrix = market_context.get("correlation_matrix", {})
        regime_multiplier = Decimal(str(market_context.get("regime_multiplier", "1.0")))
        drawdown_multipliers = market_context.get("strategy_drawdown_multipliers", {})

        if method == AllocationMethod.EQUAL_RISK:
            res = calculate_equal_risk_budget(strategies, total_budget)
        elif method == AllocationMethod.VOLATILITY_PARITY:
            res = calculate_volatility_parity_budget(
                strategies, volatilities, total_budget
            )
        elif method == AllocationMethod.CORRELATION_ADJUSTED_PARITY:
            res = calculate_correlation_adjusted_budget(
                strategies, volatilities, correlation_matrix, total_budget
            )
        elif method == AllocationMethod.REGIME_WEIGHTED:
            res = calculate_regime_weighted_budget(
                strategies,
                volatilities,
                correlation_matrix,
                total_budget,
                regime_multiplier,
            )
        elif method == AllocationMethod.DRAWDOWN_ADJUSTED:
            base = calculate_correlation_adjusted_budget(
                strategies, volatilities, correlation_matrix, total_budget
            )
            res = apply_drawdown_adjustment(base, drawdown_multipliers)
        else:
            res = calculate_correlation_adjusted_budget(
                strategies, volatilities, correlation_matrix, total_budget
            )
        return res

    def review_allocation(
        self, request: AllocationReviewRequest
    ) -> AllocationReviewResult:
        """Evaluate the proposed allocation budgets against limits.

        Args:
            request: The review request envelope.

        Returns:
            AllocationReviewResult: Outcome of the check.
        """
        portfolio_state = request.portfolio_state
        proposal = request.proposal
        market_context = request.market_context
        config = request.config or self.config

        equity = portfolio_state.equity
        if equity <= Decimal("0.0"):
            return AllocationReviewResult(
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.MARGIN_BREACH,
                message="Cannot allocate budget with zero or negative account equity.",
                severity=RiskSeverity.CRITICAL_BREACH,
                breached=True,
            )

        checkers = [
            self._check_portfolio_budget,
            self._check_strategy_budget,
            self._check_symbol_budget,
            self._check_currency_budget,
            self._check_correlation_clusters,
            self._check_var_es,
            self._check_stress_loss,
            self._check_margin,
            self._check_drawdown,
            self._check_performance_evidence,
        ]

        for check in checkers:
            res = check(portfolio_state, proposal, market_context, config)
            if res is not None:
                return res

        return AllocationReviewResult(
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message=(
                "Proposed strategy allocations comply with limits "
                "and governance policies."
            ),
            severity=RiskSeverity.INFO,
            breached=False,
        )

    def _check_portfolio_budget(
        self,
        portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        _config: RiskConfig,
    ) -> AllocationReviewResult | None:
        equity = portfolio_state.equity
        total_proposed = sum(proposal.allocations.values())
        portfolio_budget_limit = Decimal(
            str(market_context.get("portfolio_budget_limit", equity))
        )
        if total_proposed > portfolio_budget_limit:
            return AllocationReviewResult(
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.MARGIN_BREACH,
                message=(
                    f"Total proposed allocation exceeds portfolio budget limit: "
                    f"{total_proposed:.2f} > {portfolio_budget_limit:.2f}."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                details={
                    "total_proposed": float(total_proposed),
                    "portfolio_budget_limit": float(portfolio_budget_limit),
                },
            )
        return None

    def _check_strategy_budget(
        self,
        portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> AllocationReviewResult | None:
        equity = portfolio_state.equity
        max_single_limit = equity * config.max_strategy_allocation_pct
        for strat_id, alloc in proposal.allocations.items():
            strategy_cap = Decimal(
                str(
                    market_context.get("strategy_budget_limit", {}).get(
                        strat_id, max_single_limit
                    )
                )
            )
            if alloc > strategy_cap:
                return AllocationReviewResult(
                    status=RiskDecisionStatus.REJECT,
                    reason_code=RiskReasonCode.ALLOCATION_LIMIT_BREACH,
                    message=(
                        f"Proposed allocation for '{strat_id}' "
                        f"exceeds strategy budget limit: "
                        f"{alloc:.2f} > {strategy_cap:.2f}."
                    ),
                    severity=RiskSeverity.HARD_BREACH,
                    breached=True,
                    details={
                        "strategy_id": strat_id,
                        "proposed": float(alloc),
                        "limit": float(strategy_cap),
                    },
                )
        return None

    def _check_symbol_budget(
        self,
        _portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        _config: RiskConfig,
    ) -> AllocationReviewResult | None:
        strategy_to_symbols = market_context.get("strategy_to_symbols", {})
        symbol_allocations: dict[str, Decimal] = {}
        for strat_id, alloc in proposal.allocations.items():
            symbols = strategy_to_symbols.get(strat_id, [strat_id])
            for sym in symbols:
                symbol_allocations[sym] = (
                    symbol_allocations.get(sym, Decimal("0.0")) + alloc
                )

        symbol_budget_limits = market_context.get("symbol_budget_limit", {})
        for sym, alloc in symbol_allocations.items():
            if sym in symbol_budget_limits:
                limit = Decimal(str(symbol_budget_limits[sym]))
                if alloc > limit:
                    return AllocationReviewResult(
                        status=RiskDecisionStatus.REJECT,
                        reason_code=RiskReasonCode.ALLOCATION_LIMIT_BREACH,
                        message=(
                            f"Proposed allocation for symbol '{sym}' "
                            f"exceeds budget limit: {alloc:.2f} > {limit:.2f}."
                        ),
                        severity=RiskSeverity.HARD_BREACH,
                        breached=True,
                        details={
                            "symbol": sym,
                            "allocation": float(alloc),
                            "limit": float(limit),
                        },
                    )
        return None

    def _check_currency_budget(
        self,
        portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        _config: RiskConfig,
    ) -> AllocationReviewResult | None:
        strategy_to_currencies = market_context.get("strategy_to_currencies", {})
        currency_allocations: dict[str, Decimal] = {}
        for strat_id, alloc in proposal.allocations.items():
            ccy = strategy_to_currencies.get(strat_id, portfolio_state.currency)
            currency_allocations[ccy] = (
                currency_allocations.get(ccy, Decimal("0.0")) + alloc
            )

        currency_budget_limits = market_context.get("currency_budget_limit", {})
        for ccy, alloc in currency_allocations.items():
            if ccy in currency_budget_limits:
                limit = Decimal(str(currency_budget_limits[ccy]))
                if alloc > limit:
                    return AllocationReviewResult(
                        status=RiskDecisionStatus.REJECT,
                        reason_code=RiskReasonCode.CURRENCY_BREACH,
                        message=(
                            f"Proposed allocation for currency '{ccy}' "
                            f"exceeds budget limit: {alloc:.2f} > {limit:.2f}."
                        ),
                        severity=RiskSeverity.HARD_BREACH,
                        breached=True,
                        details={
                            "currency": ccy,
                            "allocation": float(alloc),
                            "limit": float(limit),
                        },
                    )
        return None

    def _check_correlation_clusters(
        self,
        portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> AllocationReviewResult | None:
        equity = portfolio_state.equity
        correlation_matrix = market_context.get("correlation_matrix", {})
        if correlation_matrix:
            threshold = config.correlation_threshold
            visited: set[str] = set()
            clusters: list[list[str]] = []
            active_strategies = list(proposal.allocations.keys())

            for strat in active_strategies:
                if strat not in visited:
                    cluster = []
                    queue = [strat]
                    visited.add(strat)
                    while queue:
                        node = queue.pop(0)
                        cluster.append(node)
                        neighbors = correlation_matrix.get(node, {})
                        for other in active_strategies:
                            if other != node and other not in visited:
                                corr_val = Decimal(str(neighbors.get(other, "0.0")))
                                if corr_val >= threshold:
                                    visited.add(other)
                                    queue.append(other)
                    clusters.append(cluster)

            cluster_budget_limits = market_context.get("cluster_budget_limit", {})
            for idx, cluster in enumerate(clusters):
                cluster_alloc = sum(proposal.allocations[s] for s in cluster)
                cluster_id = f"cluster_{idx}"
                limit = Decimal(
                    str(cluster_budget_limits.get(cluster_id, equity * Decimal("0.60")))
                )
                if cluster_alloc > limit:
                    return AllocationReviewResult(
                        status=RiskDecisionStatus.REJECT,
                        reason_code=RiskReasonCode.CORRELATION_BREACH,
                        message=(
                            f"Proposed allocation for correlation cluster {cluster} "
                            f"exceeds limit: {cluster_alloc:.2f} > {limit:.2f}."
                        ),
                        severity=RiskSeverity.HARD_BREACH,
                        breached=True,
                        details={
                            "cluster": cluster,
                            "allocation": float(cluster_alloc),
                            "limit": float(limit),
                        },
                    )
        return None

    def _check_var_es(
        self,
        portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> AllocationReviewResult | None:
        equity = portfolio_state.equity
        volatilities = market_context.get("volatilities", {})
        correlation_matrix = market_context.get("correlation_matrix", {})
        if volatilities and correlation_matrix:
            portfolio_variance = Decimal("0.0")
            for s1, w1 in proposal.allocations.items():
                vol1 = Decimal(str(volatilities.get(s1, "0.02")))
                for s2, w2 in proposal.allocations.items():
                    vol2 = Decimal(str(volatilities.get(s2, "0.02")))
                    corr = Decimal(
                        str(
                            correlation_matrix.get(s1, {}).get(
                                s2, "1.0" if s1 == s2 else "0.0"
                            )
                        )
                    )
                    portfolio_variance += w1 * w2 * corr * vol1 * vol2

            portfolio_std = Decimal(str(math.sqrt(max(0.0, float(portfolio_variance)))))
            confidence_var = Decimal(
                str(market_context.get("var_confidence", config.var_confidence))
            )
            confidence_es = Decimal(
                str(market_context.get("es_confidence", config.es_confidence))
            )

            def get_z_score(conf: Decimal) -> Decimal:
                val = float(conf)
                if val >= CONF_99:
                    return Z_99
                if val >= CONF_95:
                    return Z_95
                if val >= CONF_90:
                    return Z_90
                return Z_95

            z_var = get_z_score(confidence_var)
            allocated_var = portfolio_std * z_var

            z_es = get_z_score(confidence_es)
            pdf_z = Decimal(
                str(1.0 / math.sqrt(2.0 * math.pi) * math.exp(-0.5 * float(z_es) ** 2))
            )
            allocated_es = portfolio_std * (pdf_z / (Decimal("1.0") - confidence_es))

            max_var_limit = Decimal(
                str(
                    market_context.get(
                        "max_var_limit", config.max_daily_loss_pct * equity
                    )
                )
            )
            if allocated_var > max_var_limit:
                return AllocationReviewResult(
                    status=RiskDecisionStatus.REJECT,
                    reason_code=RiskReasonCode.VAR_BREACH,
                    message=(
                        f"Proposed allocation VaR exceeds limit: "
                        f"{allocated_var:.2f} > {max_var_limit:.2f}."
                    ),
                    severity=RiskSeverity.HARD_BREACH,
                    breached=True,
                    details={
                        "var": float(allocated_var),
                        "limit": float(max_var_limit),
                    },
                )

            max_es_limit = Decimal(
                str(
                    market_context.get(
                        "max_es_limit", config.max_total_loss_pct * equity
                    )
                )
            )
            if allocated_es > max_es_limit:
                return AllocationReviewResult(
                    status=RiskDecisionStatus.REJECT,
                    reason_code=RiskReasonCode.ES_BREACH,
                    message=(
                        f"Proposed allocation Expected Shortfall exceeds limit: "
                        f"{allocated_es:.2f} > {max_es_limit:.2f}."
                    ),
                    severity=RiskSeverity.HARD_BREACH,
                    breached=True,
                    details={
                        "es": float(allocated_es),
                        "limit": float(max_es_limit),
                    },
                )
        return None

    def _check_stress_loss(
        self,
        portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> AllocationReviewResult | None:
        equity = portfolio_state.equity
        strategy_stress_factors = market_context.get("strategy_stress_factors", {})
        total_stress_loss = Decimal("0.0")
        for strat, alloc in proposal.allocations.items():
            factor = Decimal(str(strategy_stress_factors.get(strat, "0.15")))
            total_stress_loss += alloc * factor

        max_stress_loss_limit = Decimal(
            str(
                market_context.get(
                    "max_stress_loss_limit",
                    config.max_stress_loss_pct * equity,
                )
            )
        )
        if total_stress_loss > max_stress_loss_limit:
            return AllocationReviewResult(
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.STRESS_BREACH,
                message=(
                    f"Proposed allocation stress loss exceeds limit: "
                    f"{total_stress_loss:.2f} > {max_stress_loss_limit:.2f}."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                details={
                    "stress_loss": float(total_stress_loss),
                    "limit": float(max_stress_loss_limit),
                },
            )
        return None

    def _check_margin(
        self,
        portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> AllocationReviewResult | None:
        equity = portfolio_state.equity
        strategy_margin_factors = market_context.get("strategy_margin_factors", {})
        total_margin_requirement = Decimal("0.0")
        for strat, alloc in proposal.allocations.items():
            factor = Decimal(str(strategy_margin_factors.get(strat, "0.05")))
            total_margin_requirement += alloc * factor

        max_margin_limit = Decimal(
            str(
                market_context.get(
                    "max_margin_limit", config.max_margin_utilization_pct * equity
                )
            )
        )
        if total_margin_requirement > max_margin_limit:
            return AllocationReviewResult(
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.MARGIN_BREACH,
                message=(
                    f"Proposed allocation margin requirement exceeds limit: "
                    f"{total_margin_requirement:.2f} > {max_margin_limit:.2f}."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                details={
                    "margin_requirement": float(total_margin_requirement),
                    "limit": float(max_margin_limit),
                },
            )
        return None

    def _check_drawdown(
        self,
        portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        _config: RiskConfig,
    ) -> AllocationReviewResult | None:
        strategy_drawdown_multipliers = market_context.get(
            "strategy_drawdown_multipliers", {}
        )
        for strat, alloc in proposal.allocations.items():
            current_alloc = portfolio_state.strategy_allocations.get(
                strat, Decimal("0.0")
            )
            multiplier = Decimal(str(strategy_drawdown_multipliers.get(strat, "1.0")))
            if multiplier < Decimal("1.0"):
                max_allowed_alloc = current_alloc * multiplier
                if (
                    alloc > max_allowed_alloc + Decimal("0.01")
                    and alloc > current_alloc
                ):
                    return AllocationReviewResult(
                        status=RiskDecisionStatus.REJECT,
                        reason_code=RiskReasonCode.DRAWDOWN_BREACH,
                        message=(
                            f"Proposed allocation for '{strat}' exceeds "
                            f"drawdown step-down limit: {alloc:.2f} > "
                            f"{max_allowed_alloc:.2f} (multiplier: "
                            f"{multiplier})."
                        ),
                        severity=RiskSeverity.HARD_BREACH,
                        breached=True,
                        details={
                            "strategy_id": strat,
                            "allocation": float(alloc),
                            "limit": float(max_allowed_alloc),
                        },
                    )
        return None

    def _check_performance_evidence(
        self,
        portfolio_state: PortfolioState,
        proposal: ProposedAllocation,
        market_context: dict[str, Any],
        config: RiskConfig,
    ) -> AllocationReviewResult | None:
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
                    return AllocationReviewResult(
                        status=status,
                        reason_code=RiskReasonCode.STALE_EVIDENCE,
                        message=(
                            f"Missing historical performance evidence to increase "
                            f"allocation for strategy '{strat_id}'."
                        ),
                        severity=(
                            RiskSeverity.HARD_BREACH
                            if is_live
                            else RiskSeverity.WARNING
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
                    return AllocationReviewResult(
                        status=status,
                        reason_code=RiskReasonCode.STALE_EVIDENCE,
                        message=(
                            f"Insufficient trades for strategy '{strat_id}': "
                            f"{trades} < required {config.min_backtest_trades}."
                        ),
                        severity=(
                            RiskSeverity.HARD_BREACH
                            if is_live
                            else RiskSeverity.WARNING
                        ),
                        breached=True,
                    )

                if sharpe < config.min_backtest_sharpe:
                    status = (
                        RiskDecisionStatus.REJECT
                        if is_live
                        else RiskDecisionStatus.NEEDS_MORE_EVIDENCE
                    )
                    return AllocationReviewResult(
                        status=status,
                        reason_code=RiskReasonCode.STALE_EVIDENCE,
                        message=(
                            f"Sharpe ratio for strategy '{strat_id}' too low: "
                            f"{sharpe:.2f} < required {config.min_backtest_sharpe:.2f}."
                        ),
                        severity=(
                            RiskSeverity.HARD_BREACH
                            if is_live
                            else RiskSeverity.WARNING
                        ),
                        breached=True,
                    )

                increase_pct = Decimal("1.0")
                if current_alloc > Decimal("0.0"):
                    increase_pct = (proposed_alloc - current_alloc) / current_alloc

                if increase_pct > config.max_allocation_increase_pct:
                    approval_token_valid = market_context.get(
                        "approval_token_valid", False
                    )
                    if not approval_token_valid:
                        return AllocationReviewResult(
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


def review_allocation_proposal(
    request: AllocationReviewRequest,
) -> AllocationReviewResult:
    """Evaluate budget allocation proposal changes across multiple strategies.

    Args:
        request: The risk assessment request containing proposed allocation.

    Returns:
        AllocationReviewResult: Synthesized final decision package.
    """
    config = request.config
    if config is None:
        from app.services.risk.config import load_risk_config

        config = load_risk_config("default")

    allocator = RiskAllocator(config)
    return allocator.review_allocation(request)


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
    request = AllocationReviewRequest(
        portfolio_state=portfolio_state,
        proposal=proposal,
        market_context=market_context,
        config=config,
    )
    result = review_allocation_proposal(request)
    return LimitResult(
        limit_name="verify_allocation_limits",
        status=result.status,
        reason_code=result.reason_code,
        message=result.message,
        severity=result.severity,
        breached=result.breached,
        details=result.details,
    )
