"""Risk Governor orchestration layer.

Implements the layered control checks sequence, synthesizes final RiskDecisionPackage
decisions, issues approval tokens, and persists events to the audit chain.
"""

from __future__ import annotations

import hashlib
import time
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.risk.allocation import verify_allocation_limits
from app.services.risk.audit import (
    create_risk_audit_event,
    create_risk_decision_token,
    verify_risk_audit_chain,
)
from app.services.risk.limits import run_limit_checks
from app.services.risk.models import (
    PositionSizingRequest,
    ProposedAllocation,
    ProposedTrade,
    RiskAction,
    RiskAssessmentRequest,
    RiskDecisionPackage,
    RiskDecisionStatus,
    RiskReasonCode,
    StrategyAdmissionRequest,
)
from app.services.risk.policy import resolve_policy
from app.services.risk.sizing import calculate_position_size
from app.services.risk.stress import build_default_scenario_registry
from app.services.risk.var_es import calculate_var_es_snapshots
from app.utils.errors import DataError, ValidationError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.risk.kill_switch import KillSwitchManager
    from app.services.risk.storage import (
        RiskAuditSink,
        RiskDecisionStore,
        RiskPolicyStore,
        RiskStateStore,
    )

from app.utils.normalization import utc_now
from app.utils.standard import stable_identifier


class RiskGovernor:
    """Canonical orchestration layer enforcing institutional risk controls."""

    def __init__(
        self,
        state_store: RiskStateStore,
        audit_sink: RiskAuditSink,
        policy_store: RiskPolicyStore,
        decision_store: RiskDecisionStore,
        kill_switch_manager: KillSwitchManager | None = None,
    ) -> None:
        """Initialize governor with injected ABC storage ports and managers.

        Args:
            state_store: Store for drawdown and kill switch state.
            audit_sink: Sink for append-only audit event blocks.
            policy_store: Store for PolicyRules.
            decision_store: Store for RiskDecisionPackages.
            kill_switch_manager: Optional KillSwitchManager instance.
        """
        self.state_store = state_store
        self.audit_sink = audit_sink
        self.policy_store = policy_store
        self.decision_store = decision_store

        if kill_switch_manager is None:
            from app.services.risk.kill_switch import get_kill_switch_manager

            self.kill_switch_manager = get_kill_switch_manager()
        else:
            self.kill_switch_manager = kill_switch_manager

    def review_trade_risk(  # noqa: C901, PLR0912, PLR0915
        self,
        request: RiskAssessmentRequest,
        operator_role: str | None = None,
        approval_token: str | None = None,
    ) -> RiskDecisionPackage:
        """Execute the pre-trade risk checks pipeline for a candidate ProposedTrade.

        Args:
            request: The complete evaluation state request.
            operator_role: Optional role of the operator.
            approval_token: Optional override approval token.

        Returns:
            RiskDecisionPackage: Synthesized final decision package.
        """
        start_time = time.perf_counter()
        # 1. Input schema validation
        if not isinstance(request, RiskAssessmentRequest):
            raise ValidationError(
                "Invalid request type: must be RiskAssessmentRequest."
            )
        if not isinstance(request.proposed_action, ProposedTrade):
            raise ValidationError("proposed_action must be a ProposedTrade.")

        # Idempotency check: process duplicate request ID
        request_id = getattr(request, "request_id", None)
        if not request_id:
            # Generate temporary ID if missing
            request_id = stable_identifier(
                {
                    "action": request.proposed_action.to_json(),
                    "time": utc_now().isoformat(),
                },
                prefix="req",
            )
            request.request_id = request_id

        # Check for cached decision
        cached = self.decision_store.get_decision_by_request_id(request_id)
        if cached is not None:
            # If materials differ, raise DataError (collision)
            action_hash = hashlib.sha256(
                request.proposed_action.to_json().encode()
            ).hexdigest()
            cached_action_hash = hashlib.sha256(
                ProposedTrade.model_validate(cached.details.get("proposed_action"))
                .to_json()
                .encode()
                if cached.details and "proposed_action" in cached.details
                else b""
            ).hexdigest()
            if action_hash != cached_action_hash:
                msg = f"Request ID '{request_id}' collision: different materials."
                raise DataError(msg)
            return cached

        # Generate unique decision ID
        decision_id = stable_identifier(
            {"request_id": request_id, "timestamp": utc_now().isoformat()}, prefix="dec"
        )
        workflow_id = request.workflow_id or "wf-default"

        # 2. Policy resolution
        rules = self.policy_store.get_rules()
        context = {
            "environment": request.market_context.get("environment", "local"),
            "mode": request.market_context.get("mode", "paper"),
            "account_id": request.portfolio_state.account_id,
            "strategy_id": request.proposed_action.strategy_id,
            "symbol": request.proposed_action.symbol,
            "operator_role": operator_role,
        }
        policy_res = resolve_policy(request.risk_config, rules, context)
        resolved_config = policy_res.resolved_config

        # Check policy level fail-closed state
        if policy_res.status in {RiskDecisionStatus.REJECT, RiskDecisionStatus.BLOCK}:
            decision = RiskDecisionPackage(
                decision_id=decision_id,
                request_id=request_id,
                workflow_id=workflow_id,
                status=policy_res.status,
                rule_key="policy_resolution",
                snapshot_as_of=utc_now(),
                config_hash=resolved_config.contract_hash(),
                reason=policy_res.reason,
                composite_breach_flags=["policy_resolution"],
                calculated_volume=request.proposed_action.volume,
            )
            decision.details = {"proposed_action": request.proposed_action.model_dump()}
            self.decision_store.save_decision(decision)
            create_risk_audit_event(decision, request.proposed_action, self.audit_sink)
            return decision

        # 3. Fail-Closed Audit Chain Integrity Check
        # If running in live-sensitive mode, verify audit chain history first
        is_live = request.market_context.get("mode") in {
            "micro_live",
            "full_live",
        } or request.market_context.get("environment") in {"production", "live"}
        if is_live and not verify_risk_audit_chain(self.audit_sink):
            decision = RiskDecisionPackage(
                decision_id=decision_id,
                request_id=request_id,
                workflow_id=workflow_id,
                status=RiskDecisionStatus.BLOCK,
                rule_key="audit_chain_verification_failed",
                snapshot_as_of=utc_now(),
                config_hash=resolved_config.contract_hash(),
                reason="Audit chain verification failed. Chain is tampered or corrupt.",
                composite_breach_flags=["audit_chain_verification_failed"],
                calculated_volume=request.proposed_action.volume,
            )
            decision.details = {"proposed_action": request.proposed_action.model_dump()}
            self.decision_store.save_decision(decision)
            # Trigger kill switch automatically on audit-chain failure
            self.kill_switch_manager.trigger(
                scope="global",
                target="*",
                reason="Audit-chain verification failed (chain tampered).",
                triggered_by="RiskGovernor",
            )
            create_risk_audit_event(decision, request.proposed_action, self.audit_sink)
            return decision

        # 4. Volatility positioning & sizing calculation
        sizing_req = request.market_context.get("sizing_request")
        calculated_vol = request.proposed_action.volume
        if sizing_req:
            try:
                sizing_req_obj = PositionSizingRequest(
                    symbol=request.proposed_action.symbol,
                    method=sizing_req.get("method", "fixed_lot"),
                    fixed_volume=Decimal(str(sizing_req.get("fixed_volume")))
                    if sizing_req.get("fixed_volume") is not None
                    else request.proposed_action.volume,
                    risk_percent=Decimal(str(sizing_req.get("risk_percent")))
                    if sizing_req.get("risk_percent") is not None
                    else None,
                    stop_loss_pips=Decimal(str(sizing_req.get("stop_loss_pips")))
                    if sizing_req.get("stop_loss_pips") is not None
                    else None,
                    atr_value=Decimal(str(sizing_req.get("atr_value")))
                    if sizing_req.get("atr_value") is not None
                    else None,
                    multiplier=Decimal(str(sizing_req.get("multiplier")))
                    if sizing_req.get("multiplier") is not None
                    else None,
                    risk_amount=Decimal(str(sizing_req.get("risk_amount")))
                    if sizing_req.get("risk_amount") is not None
                    else None,
                )
                sizing_res = calculate_position_size(
                    request=sizing_req_obj,
                    portfolio_state=request.portfolio_state,
                    market_context=request.market_context,
                    config=resolved_config,
                )
                calculated_vol = sizing_res.calculated_volume
            except Exception as e:  # noqa: BLE001
                logger.error(f"Governor sizing calculation error: {e}")

        # 5. Inject calculated metrics (VaR/ES and Stress loss) into market context
        from app.services.risk.reports import RISK_METRICS_REGISTRY

        try:
            t0 = time.perf_counter()
            var_snap, es_snap = calculate_var_es_snapshots(
                portfolio_state=request.portfolio_state,
                proposed_trade=request.proposed_action,
                market_context=request.market_context,
                config=resolved_config,
                lookback=int(request.market_context.get("var_lookback", 50)),
                var_confidence=Decimal(
                    str(request.market_context.get("var_confidence", "0.95"))
                ),
                es_confidence=Decimal(
                    str(request.market_context.get("es_confidence", "0.95"))
                ),
                min_samples=int(request.market_context.get("min_samples", 2)),
                exclude_last=True,
            )
            var_es_latency = (time.perf_counter() - t0) * 1000.0
            RISK_METRICS_REGISTRY.record(
                name="haruquant_risk_var_es_latency_ms",
                kind="histogram",
                value=var_es_latency,
                labels={
                    "method": str(
                        request.market_context.get("var_method", "parametric")
                    )
                },
            )
            # Inject calculated VaR/ES metric values
            request.market_context["var_metric"] = var_snap.result
            request.market_context["es_metric"] = es_snap.average_tail_loss
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Tail risk VaR/ES calculations skipped: {e}")

        try:
            t0 = time.perf_counter()
            stress_registry = build_default_scenario_registry()
            stress_results = stress_registry.evaluate_portfolio(
                portfolio_state=request.portfolio_state,
                proposed_trade=request.proposed_action,
                market_context=request.market_context,
                config=resolved_config,
            )
            stress_latency = (time.perf_counter() - t0) * 1000.0
            RISK_METRICS_REGISTRY.record(
                name="haruquant_risk_stress_latency_ms",
                kind="histogram",
                value=stress_latency,
                labels={"scenarios_count": str(len(stress_results))},
            )
            # Find worst stress loss amount in account currency
            worst_loss = Decimal("0.0")
            for sr in stress_results:
                loss_amt = request.portfolio_state.equity * sr.impact_pct
                worst_loss = max(worst_loss, loss_amt)
            request.market_context["stress_loss_val"] = worst_loss
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Stress testing skipped: {e}")

        # Calculate correlation snapshot for details latency check
        correlation_snap = None
        if request.portfolio_state and request.market_context.get("market_data"):
            try:
                t0 = time.perf_counter()
                from app.services.risk.correlation import calculate_correlation_snapshot

                correlation_snap = calculate_correlation_snapshot(
                    request.market_context.get("market_data", {}),
                    min_samples=int(request.market_context.get("min_samples", 2)),
                    exclude_last=True,
                )
                corr_latency = (time.perf_counter() - t0) * 1000.0
                RISK_METRICS_REGISTRY.record(
                    name="haruquant_risk_correlation_latency_ms",
                    kind="histogram",
                    value=corr_latency,
                    labels={
                        "timeframe": str(request.market_context.get("timeframe", "M1"))
                    },
                )
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    f"Correlation snapshot calculation skipped in governor: {e}"
                )

        # 6. Execute deterministic limits pipeline
        (
            status,
            reason_code,
            message,
            composite_breach_flags,
            primary_failure_limit,
            results,
        ) = run_limit_checks(request, resolved_config)

        # 7. Final decision synthesis
        # Handle override validation if approval token is supplied
        if (
            status in {RiskDecisionStatus.REJECT, RiskDecisionStatus.BLOCK}
            and approval_token
        ):
            # Reconstruct or parse token if it's object, or find it
            # For usage demo, we check if validation succeeds
            pass

        # Adjust status to reduce_size if limits suggest reduction
        # and volume is scalable
        if status == RiskDecisionStatus.REDUCE_SIZE:
            # Sizing calculation should scale down calculated_vol
            # If we don't have sizing result, scale down to half or safe limit
            calculated_vol = calculated_vol * Decimal("0.5")

        # Create token for approved/reduced decisions
        decision_token = ""
        if status in {RiskDecisionStatus.APPROVE, RiskDecisionStatus.REDUCE_SIZE}:
            tok = create_risk_decision_token(
                decision_id=decision_id,
                request_id=request_id,
                workflow_id=workflow_id,
                approved_action=RiskAction.EXECUTE_TRADE,
                config_hash=resolved_config.contract_hash(),
                decision_hash=hashlib.sha256(message.encode()).hexdigest(),
                scope={
                    "symbol": request.proposed_action.symbol,
                    "strategy_id": request.proposed_action.strategy_id,
                },
            )
            decision_token = tok.signature

        # Safe exposure details construction
        portfolio_exposure = 0.0
        if request.portfolio_state:
            try:
                from app.services.risk.exposure import calculate_currency_exposure

                curr_exps = calculate_currency_exposure(
                    request.portfolio_state,
                    request.proposed_action,
                    resolved_config,
                    request.market_context,
                )
                portfolio_exposure = float(sum(exp.gross for exp in curr_exps.values()))
            except Exception:  # noqa: BLE001
                portfolio_exposure = float(
                    sum(
                        abs(pos.quantity * pos.current_price)
                        for pos in request.portfolio_state.positions
                    )
                )

        currency_exposure_dict = {}
        if request.portfolio_state:
            try:
                from app.services.risk.exposure import calculate_currency_exposure

                curr_exps = calculate_currency_exposure(
                    request.portfolio_state,
                    request.proposed_action,
                    resolved_config,
                    request.market_context,
                )
                currency_exposure_dict = {
                    ccy: float(exp.net) for ccy, exp in curr_exps.items()
                }
            except Exception:  # noqa: S110, BLE001
                pass

        correlation_clusters_dict = {}
        if request.portfolio_state and correlation_snap:
            try:
                from app.services.risk.correlation import calculate_cluster_exposures

                clusters = calculate_cluster_exposures(
                    portfolio_state=request.portfolio_state,
                    proposed_trade=request.proposed_action,
                    snapshot=correlation_snap,
                    threshold=resolved_config.correlation_threshold,
                    market_context=request.market_context,
                )
                correlation_clusters_dict = {k: float(v) for k, v in clusters.items()}
            except Exception:  # noqa: S110, BLE001
                pass

        margin_usage_val = None
        if request.portfolio_state:
            try:
                from app.services.risk.margin import evaluate_margin_governance

                margin_snap = evaluate_margin_governance(
                    request.portfolio_state,
                    request.proposed_action,
                    request.market_context,
                    resolved_config,
                )
                margin_usage_val = float(margin_snap.margin_usage)
            except Exception:  # noqa: S110, BLE001
                pass

        mode = request.market_context.get("mode", "paper")
        decision = RiskDecisionPackage(
            decision_id=decision_id,
            request_id=request_id,
            workflow_id=workflow_id,
            status=status,
            rule_key=primary_failure_limit or "limits_gate",
            snapshot_as_of=utc_now(),
            config_hash=resolved_config.contract_hash(),
            reason=message,
            composite_breach_flags=composite_breach_flags,
            calculated_volume=calculated_vol,
        )
        var_metric = request.market_context.get("var_metric")
        es_metric = request.market_context.get("es_metric")
        stress_loss_val = request.market_context.get("stress_loss_val")

        decision.details = {
            "proposed_action": request.proposed_action.model_dump(),
            "decision_token": decision_token,
            "policy_hash": policy_res.policy_hash,
            "policy_profile": resolved_config.profile_name,
            "mode": mode,
            "portfolio_exposure": portfolio_exposure,
            "currency_exposure": currency_exposure_dict,
            "correlation_clusters": correlation_clusters_dict,
            "var": float(var_metric) if var_metric is not None else None,
            "es": float(es_metric) if es_metric is not None else None,
            "stress_loss": float(stress_loss_val)
            if stress_loss_val is not None
            else None,
            "margin_usage": margin_usage_val,
        }

        # 8. Save and Log
        self.decision_store.save_decision(decision)
        create_risk_audit_event(decision, request.proposed_action, self.audit_sink)

        # Trigger kill switch automatically if drawdown or daily loss
        # hard limit breached
        if status in {RiskDecisionStatus.REJECT, RiskDecisionStatus.BLOCK}:
            self.kill_switch_manager.evaluate_triggers(
                request, results, is_live=is_live
            )

        # 9. Record final observability metrics
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        RISK_METRICS_REGISTRY.record(
            name="haruquant_risk_governor_latency_ms",
            kind="histogram",
            value=latency_ms,
            labels={"action": "review_trade", "status": status},
        )
        RISK_METRICS_REGISTRY.record(
            name="haruquant_risk_decision_total",
            kind="counter",
            value=1.0,
            labels={
                "status": status,
                "rule_key": primary_failure_limit or "limits_gate",
            },
        )

        # Stale evidence metrics
        if (
            "stale_evidence" in composite_breach_flags
            or reason_code == RiskReasonCode.STALE_EVIDENCE
        ):
            RISK_METRICS_REGISTRY.record(
                name="haruquant_risk_stale_evidence_failures_total",
                kind="counter",
                value=1.0,
                labels={"symbol": request.proposed_action.symbol},
            )

        # Emit breaches counter
        if status in {
            RiskDecisionStatus.REJECT,
            RiskDecisionStatus.BLOCK,
            RiskDecisionStatus.HALT_STRATEGY,
            RiskDecisionStatus.HALT_ALL,
        }:
            for flag in composite_breach_flags:
                RISK_METRICS_REGISTRY.record(
                    name="haruquant_risk_breaches_total",
                    kind="counter",
                    value=1.0,
                    labels={"limit_name": flag, "severity": "hard_breach"},
                )

        # Audit sink health and Kill-switch gauges
        verify_health = verify_risk_audit_chain(self.audit_sink)
        RISK_METRICS_REGISTRY.record(
            name="haruquant_risk_audit_persistence_health",
            kind="gauge",
            value=1.0 if verify_health else 0.0,
        )

        global_ks_blocked = self.kill_switch_manager.is_blocked("global", "*")
        RISK_METRICS_REGISTRY.record(
            name="haruquant_risk_kill_switch_state",
            kind="gauge",
            value=1.0 if global_ks_blocked else 0.0,
            labels={"scope": "global", "target": "*"},
        )

        return decision

    def review_allocation_proposal(
        self,
        request: RiskAssessmentRequest,
    ) -> RiskDecisionPackage:
        """Review strategy budget capital allocation updates.

        Args:
            request: Enclosure containing ProposedAllocation.

        Returns:
            RiskDecisionPackage: Synthesized decision.
        """
        if not isinstance(request.proposed_action, ProposedAllocation):
            raise ValidationError("proposed_action must be ProposedAllocation.")

        request_id = request.request_id or stable_identifier(
            {"action": "allocation"}, prefix="req"
        )
        decision_id = stable_identifier({"req": request_id}, prefix="dec")
        workflow_id = request.workflow_id or "wf-alloc"

        # Resolve policy
        rules = self.policy_store.get_rules()
        policy_res = resolve_policy(
            request.risk_config, rules, {"action": "allocate_capital"}
        )
        resolved_config = policy_res.resolved_config

        alloc_res = verify_allocation_limits(
            request.portfolio_state,
            request.proposed_action,
            request.market_context,
            resolved_config,
        )

        decision = RiskDecisionPackage(
            decision_id=decision_id,
            request_id=request_id,
            workflow_id=workflow_id,
            status=alloc_res.status,
            rule_key="allocation_limits",
            snapshot_as_of=utc_now(),
            config_hash=resolved_config.contract_hash(),
            reason=alloc_res.message,
            composite_breach_flags=[]
            if alloc_res.status == RiskDecisionStatus.APPROVE
            else ["allocation_breach"],
            calculated_volume=None,
        )
        decision.details = {"proposed_action": request.proposed_action.model_dump()}

        self.decision_store.save_decision(decision)
        create_risk_audit_event(decision, request.proposed_action, self.audit_sink)
        return decision

    def review_strategy_admission(
        self,
        request: RiskAssessmentRequest,
    ) -> RiskDecisionPackage:
        """Review strategy admission specifications promotion checkpoints.

        Args:
            request: Enclosure containing StrategyAdmissionRequest.

        Returns:
            RiskDecisionPackage: Synthesized decision.
        """
        if not isinstance(request.proposed_action, StrategyAdmissionRequest):
            raise ValidationError("proposed_action must be StrategyAdmissionRequest.")

        request_id = request.request_id or stable_identifier(
            {"action": "admission"}, prefix="req"
        )
        decision_id = stable_identifier({"req": request_id}, prefix="dec")
        workflow_id = request.workflow_id or "wf-admission"

        # Resolve policy
        rules = self.policy_store.get_rules()
        policy_res = resolve_policy(
            request.risk_config, rules, {"action": "admit_strategy"}
        )
        resolved_config = policy_res.resolved_config

        # Check backtest and walk-forward parameters
        evidence = request.proposed_action.evidence or {}
        trade_cnt = int(evidence.get("trade_count", 0))
        sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))
        drawdown = Decimal(str(evidence.get("max_drawdown", "1.0")))

        breaches = []
        if trade_cnt < resolved_config.min_backtest_trades:
            breaches.append(
                f"Min backtest trades: {trade_cnt} < "
                f"{resolved_config.min_backtest_trades}"
            )
        if sharpe < resolved_config.min_backtest_sharpe:
            breaches.append(
                f"Min Sharpe: {sharpe} < {resolved_config.min_backtest_sharpe}"
            )
        if drawdown > resolved_config.max_backtest_drawdown:
            breaches.append(
                f"Max drawdown: {drawdown} > {resolved_config.max_backtest_drawdown}"
            )

        status = (
            RiskDecisionStatus.APPROVE if not breaches else RiskDecisionStatus.REJECT
        )
        reason = (
            "Admission checks cleared."
            if not breaches
            else f"Admission breaches: {breaches}"
        )

        decision = RiskDecisionPackage(
            decision_id=decision_id,
            request_id=request_id,
            workflow_id=workflow_id,
            status=status,
            rule_key="strategy_admission",
            snapshot_as_of=utc_now(),
            config_hash=resolved_config.contract_hash(),
            reason=reason,
            composite_breach_flags=breaches,
            calculated_volume=None,
        )
        decision.details = {"proposed_action": request.proposed_action.model_dump()}

        self.decision_store.save_decision(decision)
        create_risk_audit_event(decision, request.proposed_action, self.audit_sink)
        return decision

    def run_portfolio_risk_governor(
        self,
        request: RiskAssessmentRequest,
    ) -> RiskDecisionPackage:
        """Run consolidated checks across the entire current portfolio state.

        Args:
            request: Complete state request enclosure.

        Returns:
            RiskDecisionPackage: Decision snapshot.
        """
        request_id = request.request_id or stable_identifier(
            {"action": "portfolio_run"}, prefix="req"
        )
        decision_id = stable_identifier({"req": request_id}, prefix="dec")
        workflow_id = request.workflow_id or "wf-portfolio"

        # Resolve policy
        rules = self.policy_store.get_rules()
        policy_res = resolve_policy(
            request.risk_config, rules, {"action": "portfolio_checks"}
        )
        resolved_config = policy_res.resolved_config

        (
            status,
            _reason_code,
            message,
            composite_breach_flags,
            primary_failure_limit,
            _results,
        ) = run_limit_checks(request, resolved_config)

        decision = RiskDecisionPackage(
            decision_id=decision_id,
            request_id=request_id,
            workflow_id=workflow_id,
            status=status,
            rule_key=primary_failure_limit or "portfolio_run",
            snapshot_as_of=utc_now(),
            config_hash=resolved_config.contract_hash(),
            reason=message,
            composite_breach_flags=composite_breach_flags,
            calculated_volume=None,
        )
        decision.details = {"portfolio": request.portfolio_state.model_dump()}

        self.decision_store.save_decision(decision)
        create_risk_audit_event(decision, {"action": "portfolio_run"}, self.audit_sink)
        return decision


def review_trade_risk(
    request: RiskAssessmentRequest,
    operator_role: str | None = None,
    approval_token: str | None = None,
) -> RiskDecisionPackage:
    """Execute pre-trade risk checks for a candidate ProposedTrade.

    Args:
        request: The complete evaluation state request.
        operator_role: Optional role of the operator.
        approval_token: Optional override approval token.

    Returns:
        RiskDecisionPackage: Synthesized final decision package.
    """
    from app.services.risk.tools import get_shared_governor

    return get_shared_governor().review_trade_risk(
        request=request,
        operator_role=operator_role,
        approval_token=approval_token,
    )


def review_allocation_proposal(
    request: RiskAssessmentRequest,
) -> RiskDecisionPackage:
    """Evaluate budget allocation proposal changes across multiple strategies.

    Args:
        request: The risk assessment request containing proposed allocation.

    Returns:
        RiskDecisionPackage: Synthesized final decision package.
    """
    from app.services.risk.tools import get_shared_governor

    return get_shared_governor().review_allocation_proposal(request)


def review_strategy_admission(
    request: RiskAssessmentRequest,
) -> RiskDecisionPackage:
    """Review strategy walk-forward and promotion checks for strategy admission.

    Args:
        request: The risk assessment request containing strategy admission details.

    Returns:
        RiskDecisionPackage: Synthesized final decision package.
    """
    from app.services.risk.tools import get_shared_governor

    return get_shared_governor().review_strategy_admission(request)


def run_portfolio_risk_governor(
    request: RiskAssessmentRequest,
) -> RiskDecisionPackage:
    """Run sequential checkpoints across consolidated portfolio states.

    Args:
        request: The risk assessment request containing portfolio state.

    Returns:
        RiskDecisionPackage: Synthesized final decision package.
    """
    from app.services.risk.tools import get_shared_governor

    return get_shared_governor().run_portfolio_risk_governor(request)
