"""Strategy lifecycle promotion and live readiness governance.

Enforces strict gates for strategy transitions from backtesting to live-sensitive modes.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)

# Canonical progression stages
STAGE_SEQUENCE = [
    "backtest",
    "walk-forward",
    "simulation",
    "paper",
    "shadow",
    "micro-live",
    "full-live",
]


def _verify_backtest_to_wf(
    strategy_id: str, evidence: dict[str, Any], config: RiskConfig
) -> LimitResult:
    """Validate transition from backtest to walk-forward."""
    trades = int(evidence.get("trade_count", 0))
    sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))
    drawdown = Decimal(str(evidence.get("max_drawdown", "1.0")))

    if trades < config.min_backtest_trades:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Backtest trade count for '{strategy_id}' too low: "
                f"{trades} < required {config.min_backtest_trades}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    if sharpe < config.min_backtest_sharpe:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Backtest Sharpe ratio for '{strategy_id}' too low: "
                f"{sharpe:.2f} < required {config.min_backtest_sharpe:.2f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    if drawdown > config.max_backtest_drawdown:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Backtest max drawdown for '{strategy_id}' too high: "
                f"{drawdown:.2%} > limit {config.max_backtest_drawdown:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    return LimitResult(
        limit_name="lifecycle_promotion",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=f"Backtest to walk-forward promotion for '{strategy_id}' approved.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def _verify_wf_to_sim(
    strategy_id: str, evidence: dict[str, Any], config: RiskConfig
) -> LimitResult:
    """Validate transition from walk-forward to simulation."""
    trades = int(evidence.get("trade_count", 0))
    sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))

    if trades < config.min_wf_trades:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Walk-forward trade count for '{strategy_id}' too low: "
                f"{trades} < required {config.min_wf_trades}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    if sharpe < config.min_wf_sharpe:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Walk-forward Sharpe ratio for '{strategy_id}' too low: "
                f"{sharpe:.2f} < required {config.min_wf_sharpe:.2f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    return LimitResult(
        limit_name="lifecycle_promotion",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=f"Walk-forward to simulation promotion for '{strategy_id}' approved.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def _verify_sim_to_paper(
    strategy_id: str, evidence: dict[str, Any], config: RiskConfig
) -> LimitResult:
    """Validate transition from simulation to paper."""
    trades = int(evidence.get("trade_count", 0))
    profit_factor = Decimal(str(evidence.get("profit_factor", "0.0")))

    if trades < config.min_sim_trades:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Simulation trade count for '{strategy_id}' too low: "
                f"{trades} < required {config.min_sim_trades}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    if profit_factor < config.min_sim_profit_factor:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Simulation profit factor for '{strategy_id}' too low: "
                f"{profit_factor:.2f} < required {config.min_sim_profit_factor:.2f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    return LimitResult(
        limit_name="lifecycle_promotion",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=f"Simulation to paper promotion for '{strategy_id}' approved.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def _verify_paper_to_shadow(
    strategy_id: str, evidence: dict[str, Any], config: RiskConfig
) -> LimitResult:
    """Validate transition from paper to shadow."""
    trades = int(evidence.get("trade_count", 0))
    sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))

    if trades < config.min_paper_trades:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Paper trade count for '{strategy_id}' too low: "
                f"{trades} < required {config.min_paper_trades}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    if sharpe < config.min_paper_sharpe:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Paper Sharpe ratio for '{strategy_id}' too low: "
                f"{sharpe:.2f} < required {config.min_paper_sharpe:.2f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    return LimitResult(
        limit_name="lifecycle_promotion",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=f"Paper to shadow promotion for '{strategy_id}' approved.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def _verify_shadow_to_micro(
    strategy_id: str, evidence: dict[str, Any], config: RiskConfig
) -> LimitResult:
    """Validate transition from shadow to micro-live."""
    tracking_error = Decimal(str(evidence.get("tracking_error", "1.0")))
    duration_days = int(evidence.get("duration_days", 0))

    if duration_days < config.min_shadow_days:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Shadow duration for '{strategy_id}' too short: "
                f"{duration_days} days < required {config.min_shadow_days} days."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    if tracking_error > config.max_shadow_tracking_error:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Shadow tracking error for '{strategy_id}' too high: "
                f"{tracking_error:.4f} > limit {config.max_shadow_tracking_error:.4f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    return LimitResult(
        limit_name="lifecycle_promotion",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=f"Shadow to micro-live promotion for '{strategy_id}' approved.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def _verify_micro_to_full(
    strategy_id: str, evidence: dict[str, Any], config: RiskConfig
) -> LimitResult:
    """Validate transition from micro-live to full-live."""
    duration_days = int(evidence.get("duration_days", 0))
    sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))

    if duration_days < config.min_live_days:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Micro-live duration for '{strategy_id}' too short: "
                f"{duration_days} days < required {config.min_live_days} days."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    if sharpe < config.min_live_sharpe:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Micro-live Sharpe ratio for '{strategy_id}' too low: "
                f"{sharpe:.2f} < required {config.min_live_sharpe:.2f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    return LimitResult(
        limit_name="lifecycle_promotion",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=f"Micro-live to full-live promotion for '{strategy_id}' approved.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def evaluate_lifecycle_promotion(
    strategy_id: str,
    current_stage: str,
    target_stage: str,
    evidence: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Validate if a strategy is eligible to promote to the target lifecycle stage.

    Args:
        strategy_id: Strategy identifier.
        current_stage: Active stage name (e.g. 'backtest').
        target_stage: Requested stage name.
        evidence: Metrics and statistics gathered in the current stage.
        config: Active risk configuration limits.

    Returns:
        LimitResult: Outcome of the promotion gate review.
    """
    c_stage = current_stage.lower().strip()
    t_stage = target_stage.lower().strip()

    if c_stage not in STAGE_SEQUENCE or t_stage not in STAGE_SEQUENCE:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=(
                f"Invalid stage name: current='{current_stage}', "
                f"target='{target_stage}'."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    c_idx = STAGE_SEQUENCE.index(c_stage)
    t_idx = STAGE_SEQUENCE.index(t_stage)

    # 1. Same stage or demotions are always approved
    if t_idx <= c_idx:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message=(
                f"Lifecycle transition from '{c_stage}' to '{t_stage}' "
                f"is approved (maintenance/demotion)."
            ),
            severity=RiskSeverity.INFO,
            breached=False,
        )

    # 2. Check progression order: no skipping gates (cannot jump more than 1 step)
    if t_idx > c_idx + 1:
        return LimitResult(
            limit_name="lifecycle_promotion",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.LIFECYCLE_GATES_BREACH,
            message=(
                f"Lifecycle skip-gate transition blocked for '{strategy_id}': "
                f"cannot jump from '{c_stage}' directly to '{t_stage}' "
                f"without intermediate gates."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    # 3. Check specific stage gates
    gates = {
        ("backtest", "walk-forward"): _verify_backtest_to_wf,
        ("walk-forward", "simulation"): _verify_wf_to_sim,
        ("simulation", "paper"): _verify_sim_to_paper,
        ("paper", "shadow"): _verify_paper_to_shadow,
        ("shadow", "micro-live"): _verify_shadow_to_micro,
        ("micro-live", "full-live"): _verify_micro_to_full,
    }

    handler = gates.get((c_stage, t_stage))
    if handler:
        return handler(strategy_id, evidence, config)

    return LimitResult(
        limit_name="lifecycle_promotion",
        status=RiskDecisionStatus.REJECT,
        reason_code=RiskReasonCode.LIFECYCLE_GATES_BREACH,
        message=f"Unhandled transition from '{c_stage}' to '{t_stage}'.",
        severity=RiskSeverity.HARD_BREACH,
        breached=True,
    )


def evaluate_live_readiness(
    strategy_id: str,
    proposed_stage: str,
    market_context: dict[str, Any],
    _config: RiskConfig,
) -> LimitResult:
    """Enforce audit, kill switch and reconciliation readiness checks.

    Applies to live stages.

    Args:
        strategy_id: Strategy identifier.
        proposed_stage: The stage requested for activation.
        market_context: Injected runtime flags.
        _config: Active risk configuration.

    Returns:
        LimitResult: Outcome of the readiness gate review.
    """
    stage = proposed_stage.lower().strip()

    # Readiness controls apply to live-sensitive stages only
    live_sensitive_stages = {"shadow", "micro-live", "full-live"}
    if stage not in live_sensitive_stages:
        return LimitResult(
            limit_name="live_readiness",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message=(
                f"Proposed stage '{proposed_stage}' is not live-sensitive. "
                f"Readiness checks skipped."
            ),
            severity=RiskSeverity.INFO,
            breached=False,
        )

    # 1. Reject live readiness without audit persistence
    audit_active = market_context.get("audit_persistence_active", False)
    if not audit_active:
        return LimitResult(
            limit_name="live_readiness",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Live readiness blocked for '{strategy_id}': "
                f"audit persistence is not active."
            ),
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    # 2. Reject live readiness without kill switch configured
    kill_switch_configured = market_context.get("kill_switch_configured", False)
    if not kill_switch_configured:
        return LimitResult(
            limit_name="live_readiness",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Live readiness blocked for '{strategy_id}': "
                f"kill switch is not configured."
            ),
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    # 3. Reject live readiness without reconciliation and idempotency evidence
    reconciliation_active = market_context.get("portfolio_reconciliation_active", False)
    idempotency_evidence = market_context.get("idempotency_evidence_present", False)

    if not reconciliation_active or not idempotency_evidence:
        return LimitResult(
            limit_name="live_readiness",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(
                f"Live readiness blocked for '{strategy_id}': missing "
                f"portfolio reconciliation or idempotency evidence."
            ),
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    return LimitResult(
        limit_name="live_readiness",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=(
            f"Live readiness checks passed for strategy '{strategy_id}' "
            f"in stage '{proposed_stage}'."
        ),
        severity=RiskSeverity.INFO,
        breached=False,
    )


def review_live_readiness(
    strategy_id: str,
    proposed_stage: str,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Review live readiness parameters for strategy promotion.

    Args:
        strategy_id: Strategy identifier.
        proposed_stage: The stage requested for activation.
        market_context: Injected runtime flags.
        config: Active risk configuration.

    Returns:
        LimitResult: Outcome of the readiness gate review.
    """
    return evaluate_live_readiness(strategy_id, proposed_stage, market_context, config)
