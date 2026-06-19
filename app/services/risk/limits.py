"""Deterministic limits engine.

Evaluates pre-trade limits in a strict, sequential order, prioritizing hard-blocking
governance gates before execution feasibility and tail-risk exposure checks.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any, Protocol

from pydantic import Field

from app.services.risk.models import (
    ProposedTrade,
    RiskAssessmentRequest,
    RiskConfig,
    RiskContract,
    RiskDecisionStatus,
    RiskMode,
    RiskReasonCode,
    RiskSeverity,
)
from app.utils.logger import logger
from app.utils.normalization import to_utc_datetime, utc_now


class LimitCheck(Protocol):
    """Protocol representing a single deterministic pre-trade risk limit check."""

    def __call__(
        self, request: RiskAssessmentRequest, config: RiskConfig, /
    ) -> LimitResult:
        """Evaluate the limit check."""
        ...


class LimitResult(RiskContract):
    """The result of evaluating a single limit check."""

    limit_name: str = Field(
        ..., description="Unique name of the evaluated limit check."
    )
    status: RiskDecisionStatus = Field(
        ..., description="Decision outcome status for this limit."
    )
    reason_code: RiskReasonCode = Field(
        ..., description="Reason code associated with any breach."
    )
    message: str = Field(..., description="Human-readable detail message.")
    severity: RiskSeverity = Field(..., description="Severity level of any violation.")
    breached: bool = Field(..., description="True if a breach was triggered.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Calculated values or context info."
    )


# --- Helper to check if context matches a live mode ---
def _is_live_sensitive(request: RiskAssessmentRequest) -> bool:
    """Check if request environment or mode is live-sensitive."""
    mode = request.market_context.get("mode")
    env = request.market_context.get("environment")
    if mode in {
        RiskMode.MICRO_LIVE,
        RiskMode.FULL_LIVE,
        "micro_live",
        "full_live",
    }:
        return True
    return env in {"production", "live"}


# --- 1. Kill Switch Check ---
def check_kill_switch_state(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if the global, portfolio, or strategy kill switch is active."""
    from app.services.risk.kill_switch import get_kill_switch_manager

    manager = get_kill_switch_manager()
    is_live = request.market_context.get("mode") in {
        "micro_live",
        "full_live",
    } or request.market_context.get("environment") in {"production", "live"}

    # 1. Global context override check
    if request.market_context.get("kill_switch_active", False):
        return LimitResult(
            limit_name="kill_switch_state",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
            message="Global kill switch is active.",
            severity=RiskSeverity.EMERGENCY_HALT,
            breached=True,
        )

    # 2. Query Manager for Global / Portfolio block
    if manager.is_blocked("global", "*", is_live=is_live) or manager.is_blocked(
        "portfolio", "*", is_live=is_live
    ):
        return LimitResult(
            limit_name="kill_switch_state",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
            message="Global or portfolio kill switch is active.",
            severity=RiskSeverity.EMERGENCY_HALT,
            breached=True,
        )

    # 3. Check strategy block
    action = request.proposed_action
    if action:
        # Check single strategy ID
        strategy_id = getattr(action, "strategy_id", None)
        if strategy_id and manager.is_blocked(
            "strategy", str(strategy_id), is_live=is_live
        ):
            return LimitResult(
                limit_name="kill_switch_state",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
                message=f"Kill switch is active for strategy '{strategy_id}'.",
                severity=RiskSeverity.EMERGENCY_HALT,
                breached=True,
            )

        # Check multi-strategy allocations block
        allocations = getattr(action, "allocations", None)
        if isinstance(allocations, dict):
            for strat_id in allocations:
                if manager.is_blocked("strategy", str(strat_id), is_live=is_live):
                    return LimitResult(
                        limit_name="kill_switch_state",
                        status=RiskDecisionStatus.BLOCK,
                        reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
                        message=f"Kill switch is active for strategy '{strat_id}'.",
                        severity=RiskSeverity.EMERGENCY_HALT,
                        breached=True,
                    )

        # Check symbol block (which automatically checks base/quote currency legs in
        # manager)
        symbol = getattr(action, "symbol", None)
        if symbol and manager.is_blocked("symbol", str(symbol), is_live=is_live):
            return LimitResult(
                limit_name="kill_switch_state",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
                message=(
                    f"Kill switch is active for symbol '{symbol}' or its currency legs."
                ),
                severity=RiskSeverity.EMERGENCY_HALT,
                breached=True,
            )

    return LimitResult(
        limit_name="kill_switch_state",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Kill switch is inactive.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 2. Stale Evidence Check ---
def check_stale_evidence_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if input snapshots are stale or missing required live parameters."""
    now = utc_now()
    stale_limit = float(request.market_context.get("max_stale_seconds", 60.0))

    # Check proposed trade timestamp or context freshness
    freshness = request.market_context.get("freshness")
    if freshness is None:
        if _is_live_sensitive(request):
            return LimitResult(
                limit_name="stale_evidence",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.STALE_EVIDENCE,
                message="Live mode blocked: missing freshness metadata.",
                severity=RiskSeverity.CRITICAL_BREACH,
                breached=True,
            )
        return LimitResult(
            limit_name="stale_evidence",
            status=RiskDecisionStatus.NEEDS_MORE_EVIDENCE,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message="Missing freshness metadata.",
            severity=RiskSeverity.WARNING,
            breached=True,
        )

    fresh_dt = to_utc_datetime(freshness)
    age = (now - fresh_dt).total_seconds()
    if not math.isfinite(age) or not math.isfinite(stale_limit):
        return LimitResult(
            limit_name="stale_evidence",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Freshness calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if age > stale_limit:
        status = (
            RiskDecisionStatus.BLOCK
            if _is_live_sensitive(request)
            else RiskDecisionStatus.REJECT
        )
        return LimitResult(
            limit_name="stale_evidence",
            status=status,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(f"Evidence is stale by {age:.1f}s (max allowed: {stale_limit}s)."),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"age_seconds": age},
        )

    return LimitResult(
        limit_name="stale_evidence",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Evidence freshness is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 3. Max Drawdown Limit ---
def check_max_drawdown_limit(
    request: RiskAssessmentRequest, config: RiskConfig
) -> LimitResult:
    """Check if total drawdown exceeds soft or hard limit ceilings."""
    drawdown = request.market_context.get("drawdown")
    if drawdown is None:
        balance = request.portfolio_state.balance
        equity = request.portfolio_state.equity
        drawdown = (
            max(Decimal(0), (balance - equity) / balance) if balance > 0 else Decimal(0)
        )

    drawdown = Decimal(str(drawdown))
    if (
        not math.isfinite(float(drawdown))
        or not math.isfinite(float(config.max_total_loss_pct))
        or not math.isfinite(float(config.max_total_loss_pct_advisory))
    ):
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Drawdown calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if drawdown > config.max_total_loss_pct:
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.DRAWDOWN_BREACH,
            message=(
                f"Hard total drawdown limit breached: {drawdown:.2%} > "
                f"{config.max_total_loss_pct:.2%}."
            ),
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
            details={"drawdown": float(drawdown)},
        )

    if drawdown > config.max_total_loss_pct_advisory:
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message=(
                f"Advisory drawdown limit warning: {drawdown:.2%} > "
                f"{config.max_total_loss_pct_advisory:.2%}."
            ),
            severity=RiskSeverity.WARNING,
            breached=True,
            details={"drawdown": float(drawdown)},
        )

    return LimitResult(
        limit_name="max_drawdown_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Total drawdown is within safe ceilings.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 4. Daily Loss Limit ---
def check_daily_loss_limit(
    request: RiskAssessmentRequest, config: RiskConfig
) -> LimitResult:
    """Check if realized and floating daily loss exceeds the profile limits."""
    daily_loss_pct = request.market_context.get("daily_loss_pct")
    if daily_loss_pct is None:
        if _is_live_sensitive(request):
            return LimitResult(
                limit_name="daily_loss_limit",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.STALE_EVIDENCE,
                message="Live mode blocked: missing daily loss metrics.",
                severity=RiskSeverity.CRITICAL_BREACH,
                breached=True,
            )
        return LimitResult(
            limit_name="daily_loss_limit",
            status=RiskDecisionStatus.NEEDS_MORE_EVIDENCE,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message="Missing daily loss metrics.",
            severity=RiskSeverity.WARNING,
            breached=True,
        )

    daily_loss_pct = Decimal(str(daily_loss_pct))
    if not math.isfinite(float(daily_loss_pct)) or not math.isfinite(
        float(config.max_daily_loss_pct)
    ):
        return LimitResult(
            limit_name="daily_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Daily loss calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if daily_loss_pct >= config.max_daily_loss_pct:
        status = (
            RiskDecisionStatus.BLOCK
            if _is_live_sensitive(request)
            else RiskDecisionStatus.REJECT
        )
        return LimitResult(
            limit_name="daily_loss_limit",
            status=status,
            reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
            message=(
                f"Daily loss limit breached: {daily_loss_pct:.2%} >= "
                f"{config.max_daily_loss_pct:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"daily_loss_pct": float(daily_loss_pct)},
        )

    return LimitResult(
        limit_name="daily_loss_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Daily loss is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 5. Max Strategy Loss Limit ---
def check_strategy_loss_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if a specific strategy drawdown limit is exceeded."""
    strat_loss_pct = request.market_context.get("strategy_loss_pct")
    strat_limit = Decimal(
        str(request.market_context.get("max_strategy_loss_pct", "0.04"))
    )

    if strat_loss_pct is None:
        return LimitResult(
            limit_name="strategy_loss_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No strategy loss details provided. Skipping.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    strat_loss_pct = Decimal(str(strat_loss_pct))
    if not math.isfinite(float(strat_loss_pct)) or not math.isfinite(
        float(strat_limit)
    ):
        return LimitResult(
            limit_name="strategy_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Strategy loss calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if strat_loss_pct >= strat_limit:
        return LimitResult(
            limit_name="strategy_loss_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
            message=(
                f"Strategy loss limit breached: {strat_loss_pct:.2%} >= "
                f"{strat_limit:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"strategy_loss_pct": float(strat_loss_pct)},
        )

    return LimitResult(
        limit_name="strategy_loss_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Strategy loss is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 6. News Blackout Check ---
def check_news_blackout(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if news blackout window is active for the target symbols."""
    is_blackout = request.market_context.get("news_blackout_active", False)
    if is_blackout:
        return LimitResult(
            limit_name="news_blackout",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.NEWS_BLACKOUT,
            message="High impact news blackout window is active.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    return LimitResult(
        limit_name="news_blackout",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Outside of news blackout windows.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 7. Rollover Blackout Check ---
def check_rollover_blackout(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if broker midnight rollover blackout window is active."""
    is_blackout = request.market_context.get("rollover_blackout_active", False)
    if is_blackout:
        return LimitResult(
            limit_name="rollover_blackout",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.ROLLOVER_BLACKOUT,
            message=("Rollover blackout window surrounding broker midnight is active."),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    return LimitResult(
        limit_name="rollover_blackout",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Outside of rollover blackout windows.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 8. Spread Limit Check ---
def check_spread_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if current market spread exceeds the maximum allowed."""
    spread = request.market_context.get("spread")
    max_spread = Decimal(str(request.market_context.get("max_spread", "0.0050")))

    if spread is None:
        return LimitResult(
            limit_name="spread_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No spread provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    spread = Decimal(str(spread))
    if not math.isfinite(float(spread)) or not math.isfinite(float(max_spread)):
        return LimitResult(
            limit_name="spread_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Spread calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if spread > max_spread:
        return LimitResult(
            limit_name="spread_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SPREAD_BREACH,
            message=f"Spread limit breached: {spread} > {max_spread}.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"spread": float(spread)},
        )

    return LimitResult(
        limit_name="spread_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Spread is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 9. Slippage Limit Check ---
def check_slippage_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if current estimated execution slippage is within bounds."""
    slippage = request.market_context.get("slippage")
    max_slippage = Decimal(str(request.market_context.get("max_slippage", "0.0020")))

    if slippage is None:
        return LimitResult(
            limit_name="slippage_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No slippage provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    slippage = Decimal(str(slippage))
    if not math.isfinite(float(slippage)) or not math.isfinite(float(max_slippage)):
        return LimitResult(
            limit_name="slippage_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Slippage calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if slippage > max_slippage:
        return LimitResult(
            limit_name="slippage_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SLIPPAGE_BREACH,
            message=f"Slippage limit breached: {slippage} > {max_slippage}.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"slippage": float(slippage)},
        )

    return LimitResult(
        limit_name="slippage_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Slippage is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 10. Trade Frequency Limit Check ---
def check_trade_frequency_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if short-term trade frequency limits are exceeded."""
    freq = request.market_context.get("trade_frequency")
    max_freq = int(request.market_context.get("max_trade_frequency", 10))

    if freq is None:
        return LimitResult(
            limit_name="trade_frequency_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No trade frequency data provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    try:
        freq_f = float(freq)
    except (ValueError, TypeError) as e:
        return LimitResult(
            limit_name="trade_frequency_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=f"Invalid trade frequency input: {e}",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if not math.isfinite(float(freq_f)) or not math.isfinite(float(max_freq)):
        return LimitResult(
            limit_name="trade_frequency_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Trade frequency calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if int(freq) > max_freq:
        return LimitResult(
            limit_name="trade_frequency_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.FREQUENCY_BREACH,
            message=(
                f"Trade frequency limit breached: {freq} > {max_freq} per minute."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"trade_frequency": int(freq)},
        )

    return LimitResult(
        limit_name="trade_frequency_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Trade frequency is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 11. Pending Order Limit Check ---
def check_pending_order_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if the count of open pending orders exceeds the configured capacity."""
    pending_count = request.market_context.get("pending_orders_count")
    max_pending = int(request.market_context.get("max_pending_orders", 5))

    if pending_count is None:
        return LimitResult(
            limit_name="pending_order_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No pending order count provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    try:
        pending_f = float(pending_count)
    except (ValueError, TypeError) as e:
        return LimitResult(
            limit_name="pending_order_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=f"Invalid pending orders count input: {e}",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if not math.isfinite(float(pending_f)) or not math.isfinite(float(max_pending)):
        return LimitResult(
            limit_name="pending_order_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Pending orders count calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if int(pending_count) > max_pending:
        return LimitResult(
            limit_name="pending_order_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.FREQUENCY_BREACH,
            message=(f"Pending order limit breached: {pending_count} > {max_pending}."),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"pending_orders_count": int(pending_count)},
        )

    return LimitResult(
        limit_name="pending_order_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Pending order count is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 12. Portfolio Exposure Limit Check ---
def check_portfolio_exposure_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if portfolio gross exposure exceeds total capital limits."""
    gross_exposure = Decimal(
        str(request.market_context.get("portfolio_gross_exposure", "0.0"))
    )
    equity = request.portfolio_state.equity
    max_portfolio_exposure = Decimal(
        str(request.market_context.get("max_portfolio_exposure", "5.0"))
    )

    proposed_exposure = Decimal(0)
    if isinstance(request.proposed_action, ProposedTrade):
        proposed_exposure = request.proposed_action.volume * Decimal(
            str(request.market_context.get("contract_size", 100000))
        )

    total_exposure = gross_exposure + proposed_exposure
    if equity <= 0:
        return LimitResult(
            limit_name="portfolio_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message="Exposure check failed: portfolio equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if (
        not math.isfinite(float(total_exposure))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_portfolio_exposure))
    ):
        return LimitResult(
            limit_name="portfolio_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Portfolio exposure calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    ratio = total_exposure / equity
    if ratio > max_portfolio_exposure:
        return LimitResult(
            limit_name="portfolio_exposure_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message=(
                f"Portfolio exposure limit breached: {ratio:.2f}x > "
                f"{max_portfolio_exposure:.2f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"exposure_ratio": float(ratio)},
        )

    return LimitResult(
        limit_name="portfolio_exposure_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Portfolio exposure is within safe capacity.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 13. Symbol Exposure Limit Check ---
def check_symbol_exposure_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if single symbol gross exposure exceeds concentration limits."""
    symbol = ""
    if isinstance(request.proposed_action, ProposedTrade):
        symbol = request.proposed_action.symbol

    if not symbol:
        return LimitResult(
            limit_name="symbol_exposure_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No symbol exposure check required.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    symbol_exposure = Decimal(
        str(request.market_context.get(f"symbol_exposure_{symbol}", "0.0"))
    )
    equity = request.portfolio_state.equity
    max_symbol_exposure = Decimal(
        str(request.market_context.get("max_symbol_exposure", "1.0"))
    )

    proposed_exposure = Decimal(0)
    if isinstance(request.proposed_action, ProposedTrade):
        proposed_exposure = request.proposed_action.volume * Decimal(
            str(request.market_context.get("contract_size", 100000))
        )

    total_exposure = symbol_exposure + proposed_exposure
    if equity <= 0:
        return LimitResult(
            limit_name="symbol_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message="Symbol exposure check failed: equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if (
        not math.isfinite(float(total_exposure))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_symbol_exposure))
    ):
        return LimitResult(
            limit_name="symbol_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Symbol exposure calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    ratio = total_exposure / equity
    if ratio > max_symbol_exposure:
        return LimitResult(
            limit_name="symbol_exposure_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message=(
                f"Symbol {symbol} exposure limit breached: {ratio:.2f}x > "
                f"{max_symbol_exposure:.2f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"symbol": symbol, "exposure_ratio": float(ratio)},
        )

    return LimitResult(
        limit_name="symbol_exposure_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=f"Symbol {symbol} exposure is within concentration ceilings.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 14. Currency Exposure Limit Check ---
def check_currency_exposure_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if target currency gross exposure exceeds concentration ceilings."""
    gross_ccy_exposure = Decimal(
        str(request.market_context.get("currency_gross_exposure", "0.0"))
    )
    equity = request.portfolio_state.equity
    max_ccy_exposure = Decimal(
        str(request.market_context.get("max_currency_exposure", "1.5"))
    )

    if equity <= 0:
        return LimitResult(
            limit_name="currency_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.CURRENCY_BREACH,
            message="Currency exposure check failed: equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if (
        not math.isfinite(float(gross_ccy_exposure))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_ccy_exposure))
    ):
        return LimitResult(
            limit_name="currency_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Currency exposure calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    ratio = gross_ccy_exposure / equity
    if ratio > max_ccy_exposure:
        return LimitResult(
            limit_name="currency_exposure_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CURRENCY_BREACH,
            message=(
                f"Currency exposure limit breached: {ratio:.2f}x > "
                f"{max_ccy_exposure:.2f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"exposure_ratio": float(ratio)},
        )

    return LimitResult(
        limit_name="currency_exposure_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Currency exposure is within concentration limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 15. Correlated Cluster Exposure Limit Check ---
def check_correlation_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if cluster exposure or correlation exceeds limits."""
    # 1. Check individual correlation limit (correlation_limit)
    portfolio_corr = Decimal(
        str(request.market_context.get("portfolio_correlation", "0.0"))
    )
    max_corr = _config.correlation_threshold
    reject_thresh = min(
        Decimal("0.95"),
        max(Decimal("0.80"), max_corr * Decimal("1.5")),
    )

    if not math.isfinite(float(portfolio_corr)) or not math.isfinite(float(max_corr)):
        return LimitResult(
            limit_name="correlation_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Correlation calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if abs(portfolio_corr) >= reject_thresh:
        return LimitResult(
            limit_name="correlation_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CORRELATION_BREACH,
            message=(
                f"Proposed trade individual correlation {portfolio_corr:.2f} exceeds "
                f"hard rejection ceiling of {reject_thresh:.2f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"marginal_correlation": float(portfolio_corr)},
        )

    # 2. Check cluster exposure limit (correlated_cluster_limit)
    cluster_exposure = Decimal(
        str(request.market_context.get("correlated_cluster_exposure", "0.0"))
    )
    equity = request.portfolio_state.equity
    max_cluster_exposure = Decimal(
        str(request.market_context.get("max_correlated_exposure", "2.0"))
    )

    if equity <= 0:
        return LimitResult(
            limit_name="correlated_cluster_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.CORRELATION_BREACH,
            message="Cluster check failed: portfolio equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if (
        not math.isfinite(float(cluster_exposure))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_cluster_exposure))
    ):
        return LimitResult(
            limit_name="correlated_cluster_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Correlation exposure calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    ratio = cluster_exposure / equity
    if ratio > max_cluster_exposure:
        return LimitResult(
            limit_name="correlated_cluster_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CORRELATION_BREACH,
            message=(
                f"Correlated cluster exposure limit breached: {ratio:.2f}x > "
                f"{max_cluster_exposure:.2f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"exposure_ratio": float(ratio)},
        )

    return LimitResult(
        limit_name="correlated_cluster_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Correlated cluster and individual correlation are within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 16. VaR Limit Check ---
def check_var_limit(request: RiskAssessmentRequest, _config: RiskConfig) -> LimitResult:
    """Check if portfolio Value-at-Risk exceeds configuration ceilings."""
    var_val = request.market_context.get("var_metric")
    equity = request.portfolio_state.equity
    max_var_ratio = Decimal(str(request.market_context.get("max_var_ratio", "0.05")))

    if var_val is None:
        return LimitResult(
            limit_name="var_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No Value-at-Risk metric provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    var_val = Decimal(str(var_val))
    if (
        not math.isfinite(float(var_val))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_var_ratio))
    ):
        return LimitResult(
            limit_name="var_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="VaR calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if equity <= 0:
        return LimitResult(
            limit_name="var_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.VAR_BREACH,
            message="VaR check failed: portfolio equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    ratio = var_val / equity
    if ratio > max_var_ratio:
        return LimitResult(
            limit_name="var_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.VAR_BREACH,
            message=f"Value-at-Risk limit breached: {ratio:.2%} > {max_var_ratio:.2%}.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"var_ratio": float(ratio)},
        )

    return LimitResult(
        limit_name="var_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Value-at-Risk is within safe bounds.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 17. Expected Shortfall Limit Check ---
def check_expected_shortfall_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if portfolio Expected Shortfall exceeds tail risk ceilings."""
    es_val = request.market_context.get("es_metric")
    equity = request.portfolio_state.equity
    max_es_ratio = Decimal(str(request.market_context.get("max_es_ratio", "0.08")))

    if es_val is None:
        return LimitResult(
            limit_name="expected_shortfall_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No Expected Shortfall metric provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    es_val = Decimal(str(es_val))
    if (
        not math.isfinite(float(es_val))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_es_ratio))
    ):
        return LimitResult(
            limit_name="expected_shortfall_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Expected Shortfall calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if equity <= 0:
        return LimitResult(
            limit_name="expected_shortfall_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.ES_BREACH,
            message="ES check failed: portfolio equity is zero or negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    ratio = es_val / equity
    if ratio > max_es_ratio:
        return LimitResult(
            limit_name="expected_shortfall_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.ES_BREACH,
            message=(
                f"Expected Shortfall limit breached: {ratio:.2%} > {max_es_ratio:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"es_ratio": float(ratio)},
        )

    return LimitResult(
        limit_name="expected_shortfall_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Expected Shortfall is within safe bounds.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 18. Stress Loss Limit Check ---
def check_stress_loss_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if maximum projected shock stress loss exceeds limits."""
    stress_val = request.market_context.get("stress_loss_val")
    equity = request.portfolio_state.equity
    max_stress_ratio = Decimal(
        str(request.market_context.get("max_stress_ratio", "0.15"))
    )

    if stress_val is None:
        return LimitResult(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No stress scenario loss provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    stress_val = Decimal(str(stress_val))
    if (
        not math.isfinite(float(stress_val))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_stress_ratio))
    ):
        return LimitResult(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Stress loss calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if equity <= 0:
        return LimitResult(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.STRESS_BREACH,
            message="Stress check failed: portfolio equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    ratio = stress_val / equity
    if ratio > max_stress_ratio:
        return LimitResult(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STRESS_BREACH,
            message=(
                f"Stress loss limit breached: {ratio:.2%} > {max_stress_ratio:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"stress_ratio": float(ratio)},
        )

    return LimitResult(
        limit_name="stress_loss_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Max projected stress loss is within survival capacity.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 19. Leverage Limit Check ---
def check_leverage_limit(
    request: RiskAssessmentRequest, config: RiskConfig
) -> LimitResult:
    """Check if effective leverage is below target settings."""
    leverage = request.market_context.get("effective_leverage")
    if leverage is None:
        gross = Decimal(
            str(request.market_context.get("portfolio_gross_exposure", "0.0"))
        )
        equity = request.portfolio_state.equity
        leverage = gross / equity if equity > 0 else Decimal(0)

    leverage = Decimal(str(leverage))
    if not math.isfinite(float(leverage)) or not math.isfinite(
        float(config.max_effective_leverage)
    ):
        return LimitResult(
            limit_name="leverage_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Leverage calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if leverage > config.max_effective_leverage:
        return LimitResult(
            limit_name="leverage_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.LEVERAGE_BREACH,
            message=(
                f"Leverage limit breached: {leverage:.1f}x > "
                f"{config.max_effective_leverage:.1f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"leverage": float(leverage)},
        )

    return LimitResult(
        limit_name="leverage_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Effective leverage is within safe capacity.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- 20. Margin Limit Check ---
def check_margin_limit(
    request: RiskAssessmentRequest, config: RiskConfig
) -> LimitResult:
    """Check if margin utilization is below target settings."""
    margin_used = request.portfolio_state.margin_used
    equity = request.portfolio_state.equity

    if equity <= 0:
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.MARGIN_BREACH,
            message="Margin check failed: portfolio equity is zero or negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    ratio = margin_used / equity
    if (
        not math.isfinite(float(ratio))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(margin_used))
        or not math.isfinite(float(config.max_margin_utilization_pct))
    ):
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Margin calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if ratio > config.max_margin_utilization_pct:
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.MARGIN_BREACH,
            message=(
                f"Margin utilization limit breached: {ratio:.2%} > "
                f"{config.max_margin_utilization_pct:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"margin_utilization": float(ratio)},
        )

    return LimitResult(
        limit_name="margin_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Margin utilization is within safe ceilings.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


# --- Sequence definition ---
ORDERED_LIMIT_CHECKS: tuple[LimitCheck, ...] = (
    check_kill_switch_state,
    check_stale_evidence_limit,
    check_max_drawdown_limit,
    check_daily_loss_limit,
    check_strategy_loss_limit,
    check_news_blackout,
    check_rollover_blackout,
    check_spread_limit,
    check_slippage_limit,
    check_trade_frequency_limit,
    check_pending_order_limit,
    check_portfolio_exposure_limit,
    check_symbol_exposure_limit,
    check_currency_exposure_limit,
    check_correlation_limit,
    check_var_limit,
    check_expected_shortfall_limit,
    check_stress_loss_limit,
    check_leverage_limit,
    check_margin_limit,
)

REGISTERED_LIMIT_NAMES: set[str] = {
    "kill_switch_state",
    "stale_evidence",
    "max_drawdown_limit",
    "daily_loss_limit",
    "strategy_loss_limit",
    "news_blackout",
    "rollover_blackout",
    "spread_limit",
    "slippage_limit",
    "trade_frequency_limit",
    "pending_order_limit",
    "portfolio_exposure_limit",
    "symbol_exposure_limit",
    "currency_exposure_limit",
    "correlated_cluster_limit",
    "var_limit",
    "expected_shortfall_limit",
    "stress_loss_limit",
    "leverage_limit",
    "margin_limit",
    "check_kill_switch_state",
    "check_stale_evidence_limit",
    "check_max_drawdown_limit",
    "check_daily_loss_limit",
    "check_strategy_loss_limit",
    "check_news_blackout",
    "check_rollover_blackout",
    "check_spread_limit",
    "check_slippage_limit",
    "check_trade_frequency_limit",
    "check_pending_order_limit",
    "check_portfolio_exposure_limit",
    "check_symbol_exposure_limit",
    "check_currency_exposure_limit",
    "check_correlation_limit",
    "check_var_limit",
    "check_expected_shortfall_limit",
    "check_stress_loss_limit",
    "check_leverage_limit",
    "check_margin_limit",
    "stale_evidence_limit",
    "correlation_limit",
}

FUNCTION_TO_LIMIT_NAMES: dict[LimitCheck, set[str]] = {
    check_kill_switch_state: {"kill_switch_state"},
    check_stale_evidence_limit: {"stale_evidence", "stale_evidence_limit"},
    check_max_drawdown_limit: {"max_drawdown_limit"},
    check_daily_loss_limit: {"daily_loss_limit"},
    check_strategy_loss_limit: {"strategy_loss_limit"},
    check_news_blackout: {"news_blackout"},
    check_rollover_blackout: {"rollover_blackout"},
    check_spread_limit: {"spread_limit"},
    check_slippage_limit: {"slippage_limit"},
    check_trade_frequency_limit: {"trade_frequency_limit"},
    check_pending_order_limit: {"pending_order_limit"},
    check_portfolio_exposure_limit: {"portfolio_exposure_limit"},
    check_symbol_exposure_limit: {"symbol_exposure_limit"},
    check_currency_exposure_limit: {"currency_exposure_limit"},
    check_correlation_limit: {"correlated_cluster_limit", "correlation_limit"},
    check_var_limit: {"var_limit"},
    check_expected_shortfall_limit: {"expected_shortfall_limit"},
    check_stress_loss_limit: {"stress_loss_limit"},
    check_leverage_limit: {"leverage_limit"},
    check_margin_limit: {"margin_limit"},
}


class LimitEngine:
    """Consolidated runner executing and aggregating limits check pipelines."""

    def __init__(self, config: RiskConfig) -> None:
        """Initialize engine with active risk config."""
        self.config = config

    def execute(self, request: RiskAssessmentRequest) -> list[LimitResult]:
        """Execute the full, ordered sequence of limit checks.

        Args:
            request: The current evaluation state containing context snapshots.

        Returns:
            list[LimitResult]: Result outcomes of all checkpoints.
        """
        enabled_limits = request.market_context.get("enabled_limits")
        run_limits = request.market_context.get("run_limits")

        checked_limits: list[Any] = []
        if isinstance(enabled_limits, list | tuple | set):
            checked_limits.extend(enabled_limits)
        if isinstance(run_limits, list | tuple | set):
            checked_limits.extend(run_limits)

        unknown_names = [
            name for name in checked_limits if name not in REGISTERED_LIMIT_NAMES
        ]
        if unknown_names:
            logger.error(f"Unknown limit name(s) in request: {unknown_names}")
            msg = (
                f"Unknown limit name(s) in run_limits/enabled_limits: "
                f"{', '.join(map(str, unknown_names))}"
            )
            return [
                LimitResult(
                    limit_name="invalid_limit_name",
                    status=RiskDecisionStatus.BLOCK,
                    reason_code=RiskReasonCode.INVALID_INPUT,
                    message=msg,
                    severity=RiskSeverity.CRITICAL_BREACH,
                    breached=True,
                )
            ]

        run_set = set(checked_limits)

        results = []
        for check_func in ORDERED_LIMIT_CHECKS:
            func_name = getattr(check_func, "__name__", "")
            if run_set:
                func_names = {
                    func_name,
                    func_name.replace("check_", ""),
                }
                func_names.update(FUNCTION_TO_LIMIT_NAMES.get(check_func, set()))
                if not (func_names & run_set):
                    continue

            try:
                res = check_func(request, self.config)
                results.append(res)
            except Exception as e:  # noqa: BLE001
                # Wrap calculation failure
                logger.error(f"Limit check failure in '{func_name}': {e}")
                results.append(
                    LimitResult(
                        limit_name=func_name.replace("check_", ""),
                        status=RiskDecisionStatus.BLOCK,
                        reason_code=RiskReasonCode.UNEXPECTED_ERROR,
                        message=f"Limit check calculation failed: {e}",
                        severity=RiskSeverity.CRITICAL_BREACH,
                        breached=True,
                    )
                )
        return results


def run_limit_checks(
    request: RiskAssessmentRequest,
    risk_config: RiskConfig | None = None,
) -> tuple[
    RiskDecisionStatus,
    RiskReasonCode,
    str,
    list[str],
    str,
    list[LimitResult],
]:
    """Stateless runner function evaluating all limit checks and aggregating.

    Args:
        request: The active risk assessment request.
        risk_config: Optional configuration override.

    Returns:
        tuple[status, reason_code, message, composite_breach_flags,
              primary_failure_limit, limit_results]
    """
    config = risk_config or request.risk_config
    engine = LimitEngine(config=config)
    results = engine.execute(request)

    # Precedence scoring:
    # blocked > fail > needs_more_evidence > warn > pass
    # 0: BLOCK (blocked)
    # 1: REJECT (fail)
    # 2: NEEDS_MORE_EVIDENCE
    # 3: NEEDS_APPROVAL / REDUCE_SIZE / WARNING (warn)
    # 4: APPROVE / OK (pass)
    aggregated_status = RiskDecisionStatus.APPROVE
    reason_code = RiskReasonCode.OK
    message = "All limit checks cleared."
    primary_failure_limit = ""
    composite_breach_flags = []

    status_ranks = {
        RiskDecisionStatus.BLOCK: 0.0,
        RiskDecisionStatus.REJECT: 1.0,
        RiskDecisionStatus.NEEDS_MORE_EVIDENCE: 2.0,
        RiskDecisionStatus.NEEDS_APPROVAL: 3.0,
        RiskDecisionStatus.REDUCE_SIZE: 3.5,
    }

    worst_rank = 4.0

    for res in results:
        if res.breached or res.status != RiskDecisionStatus.APPROVE:
            composite_breach_flags.append(res.limit_name)

        current_rank = status_ranks.get(res.status, 4.0)
        if res.severity == RiskSeverity.WARNING and res.breached:
            current_rank = 3.8

        if current_rank < worst_rank:
            worst_rank = current_rank
            aggregated_status = res.status
            reason_code = res.reason_code
            message = res.message
            primary_failure_limit = res.limit_name

    # Include warning flags
    warning_flags = [
        r.limit_name
        for r in results
        if r.severity == RiskSeverity.WARNING and r.breached
    ]
    for w in warning_flags:
        if w not in composite_breach_flags:
            composite_breach_flags.append(w)

    return (
        aggregated_status,
        reason_code,
        message,
        sorted(composite_breach_flags),
        primary_failure_limit,
        results,
    )


def check_risk_limits(
    request: RiskAssessmentRequest,
    config: RiskConfig,
) -> list[LimitResult]:
    """Evaluate all configured risk limits sequentially.

    Args:
        request: The active risk assessment request.
        config: The RiskConfig config profile.

    Returns:
        list[LimitResult]: The results of evaluating each limit check.
    """
    engine = LimitEngine(config=config)
    return engine.execute(request)
