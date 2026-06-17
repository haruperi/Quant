# ruff: noqa: E501
"""Risk governor and pre-trade authorization checks.

This module coordinates stateless risk reviews, double-spend gates, and decision package constructs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from app.services.risk.limits import run_risk_governor_checks
from app.services.risk.models import (
    PortfolioState,
    ProposedTrade,
    RiskApprovalToken,
    RiskConfig,
    RiskDecisionPackage,
)
from app.utils.logger import logger

# In-memory reservation cache for double-spend prevention
_PENDING_APPROVAL_RESERVATIONS: dict[str, datetime] = {}


class RiskGovernor:
    """Core governor evaluating trading proposals against rules and double spend checks."""

    def __init__(self, risk_config: RiskConfig) -> None:
        """Initialize governor with profile configuration."""
        self.risk_config = risk_config

    def evaluate_proposal(
        self,
        proposed_trade: ProposedTrade,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any] | None = None,
        calendar_evidence: list[dict[str, Any]] | None = None,
        trade_history: list[dict[str, Any]] | None = None,
        kill_switch_active: bool = False,
        request_id: str | None = None,
        workflow_id: str | None = None,
    ) -> RiskDecisionPackage:
        """Run all deterministic pre-trade risk checks for a proposal."""
        req_id = request_id or "req_default"
        wf_id = workflow_id or "wf_default"
        now = datetime.now(UTC)

        # 1. Double spend prevention gate for live execution requests
        if proposed_trade.requires_live_execution:
            owner = self.risk_config.double_spend_prevention_owner
            if not owner:
                logger.error(
                    "Double-spend prevention owner is not configured for live pre-trade workflow."
                )
                return RiskDecisionPackage(
                    decision_id=f"dec_{req_id}",
                    request_id=req_id,
                    workflow_id=wf_id,
                    status="block",
                    rule_key="DOUBLE_SPEND_OWNER_MISSING",
                    primary_failure_limit="DOUBLE_SPEND_BLOCKED",
                    composite_breach_flags=["PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED"],
                    snapshot_as_of=portfolio_state.as_of,
                    config_hash=self.risk_config.config_hash,
                    reason="Pre-trade approval failed closed because double-spend prevention owner is not configured.",
                )

            if owner == "risk_cache":
                # Check if this workflow or symbol has an active reservation
                if wf_id in _PENDING_APPROVAL_RESERVATIONS:
                    res_time = _PENDING_APPROVAL_RESERVATIONS[wf_id]
                    if (
                        now - res_time
                    ).total_seconds() < self.risk_config.freshness_tolerance_seconds:
                        logger.warning(
                            f"Concurrent double spend reservation block on workflow {wf_id}"
                        )
                        return RiskDecisionPackage(
                            decision_id=f"dec_{req_id}",
                            request_id=req_id,
                            workflow_id=wf_id,
                            status="block",
                            rule_key="DOUBLE_SPEND_RESERVATION_ACTIVE",
                            primary_failure_limit="DOUBLE_SPEND_BLOCKED",
                            composite_breach_flags=[
                                "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED"
                            ],
                            snapshot_as_of=portfolio_state.as_of,
                            config_hash=self.risk_config.config_hash,
                            reason="Pre-trade approval failed closed to prevent double spend of capital.",
                        )
                # Reserve slot
                _PENDING_APPROVAL_RESERVATIONS[wf_id] = now

        # 2. Run all checks in deterministic order
        check_results = run_risk_governor_checks(
            portfolio_state=portfolio_state,
            risk_config=self.risk_config,
            proposed_trade=proposed_trade,
            market_context=market_context,
            calendar_evidence=calendar_evidence,
            trade_history=trade_history,
            kill_switch_active=kill_switch_active,
        )

        # Evaluate precedence: block > error > reject > needs_more_evidence > needs_approval > warn > approve
        final_status: Literal[
            "approve",
            "warn",
            "needs_approval",
            "needs_more_evidence",
            "reject",
            "block",
            "error",
        ] = "approve"
        primary_failure: str | None = None
        composite_breaches: list[str] = []
        failure_messages: list[str] = []

        status_rank = {
            "block": 7,
            "error": 6,
            "reject": 5,
            "needs_more_evidence": 4,
            "needs_approval": 3,
            "warn": 2,
            "approve": 1,
        }

        status_map: dict[
            str,
            Literal[
                "approve",
                "warn",
                "needs_approval",
                "needs_more_evidence",
                "reject",
                "block",
                "error",
            ],
        ] = {
            "pass": "approve",
            "warn": "warn",
            "needs_more_evidence": "needs_more_evidence",
            "fail": "reject",
            "blocked": "block",
        }

        current_max_rank = 1
        for res in check_results:
            mapped_status = status_map.get(res.status, "error")

            if mapped_status != "approve":
                composite_breaches.append(res.limit_name.upper())
                failure_messages.append(res.message)

            rank = status_rank.get(mapped_status, 1)
            if rank > current_max_rank:
                current_max_rank = rank
                final_status = mapped_status
                primary_failure = res.limit_name.upper()

        reason_str = (
            "; ".join(failure_messages)
            if failure_messages
            else "All pre-trade risk checks passed successfully."
        )

        # Emit audit logs for material decisions
        logger.info(
            f"Pre-trade risk review complete. Status: {final_status}. Primary failure: {primary_failure}.",
            extra={
                "request_id": req_id,
                "workflow_id": wf_id,
                "status": final_status,
                "primary_failure": primary_failure,
            },
        )

        # Generate approval token if approval required
        approval_token: RiskApprovalToken | None = None
        if final_status == "needs_approval":
            approval_token = RiskApprovalToken(
                token_id=f"tok_{req_id}",
                request_id=req_id,
                workflow_id=wf_id,
                approved_action="execute_trade",
                approver="risk_governor",
                expiry_time=datetime.now(UTC),
                config_hash=self.risk_config.config_hash,
                decision_hash=f"hash_{req_id}",
                scope={
                    "symbol": proposed_trade.symbol,
                    "strategy_id": proposed_trade.strategy_id,
                },
                nonce="nonce_val",
                signature="sig_val",
            )

        return RiskDecisionPackage(
            decision_id=f"dec_{req_id}",
            request_id=req_id,
            workflow_id=wf_id,
            status=final_status,
            rule_key="PRE_TRADE_GOVERNOR",
            primary_failure_limit=primary_failure,
            composite_breach_flags=composite_breaches,
            approval_required=(final_status == "needs_approval"),
            approval_token=approval_token,
            snapshot_as_of=portfolio_state.as_of,
            config_hash=self.risk_config.config_hash,
            reason=reason_str,
            metadata={
                "double_spend_gate_applied": proposed_trade.requires_live_execution
            },
        )


def run_portfolio_risk_governor(
    proposed_trade: ProposedTrade,
    portfolio_state: PortfolioState,
    risk_config: RiskConfig,
    market_context: dict[str, Any] | None = None,
    calendar_evidence: list[dict[str, Any]] | None = None,
    trade_history: list[dict[str, Any]] | None = None,
    kill_switch_active: bool = False,
    request_id: str | None = None,
    workflow_id: str | None = None,
) -> RiskDecisionPackage:
    """Exposed deterministic function executing pre-trade risk evaluation."""
    governor = RiskGovernor(risk_config)
    return governor.evaluate_proposal(
        proposed_trade=proposed_trade,
        portfolio_state=portfolio_state,
        market_context=market_context,
        calendar_evidence=calendar_evidence,
        trade_history=trade_history,
        kill_switch_active=kill_switch_active,
        request_id=request_id,
        workflow_id=workflow_id,
    )
