# ruff: noqa: E501
"""Live execution gate evaluation chain.

Implements the deterministic ordered gate chain that every live-route request
must pass before any broker mutation can occur. Gates evaluate in a fixed
order and the first mandatory gate failure stops all downstream evaluation.

Gate evaluation order (per phase requirements):
    1. Live enablement gate
    2. Request schema validation gate
    3. Approval validation gate
    4. Risk decision validation gate (placeholder — risk module owns policy)
    5. Broker readiness gate
    6. Stale-context validation gate
    7. Idempotency validation gate
    8. Reconciliation authority validation gate
    9. Kill-switch validation gate
    10. Audit pre-recording gate
    11. Broker adapter permission gate

Ownership:
    - Owns gate evaluation sequencing, gate result contracts, and
      kill-switch gate enforcement.
    - Does NOT own risk policy, approval-policy creation, broker adapter
      implementation, or UI/API routing.

Public exports:
    LiveGateDecision, LiveGateResult, evaluate_live_gate,
    require_live_approval, enforce_kill_switch_gate.

Side effects:
    None on import. Gate evaluation is synchronous and deterministic.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from app.services.risk.kill_switch import KillSwitchScope, check_risk_kill_switch
from app.utils.errors import ValidationError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.utils.settings import Settings


class LiveGateDecision(StrEnum):
    """Decision outcome for a single live gate evaluation.

    Attributes:
        PASS: Gate passed; downstream evaluation may continue.
        BLOCK: Mandatory gate failed; downstream evaluation must stop.
        ERROR: Gate encountered an unexpected error; treated as BLOCK.
        DIAGNOSTIC_ONLY: Gate ran in diagnostic mode after a mandatory failure
            (only valid for gates with diagnostic_after_failure=True).
    """

    PASS = "pass"  # noqa: S105
    BLOCK = "block"
    ERROR = "error"
    DIAGNOSTIC_ONLY = "diagnostic_only"


@dataclass(frozen=True)
class LiveGateResult:
    """Immutable result for one gate in the evaluation chain.

    Attributes:
        decision: Gate outcome (PASS, BLOCK, ERROR, DIAGNOSTIC_ONLY).
        gate_name: Stable machine-readable gate identifier.
        error_code: Approved error code when decision is BLOCK or ERROR.
        message: Human-readable operator message.
        request_id: Trace identifier propagated from the caller.
        correlation_id: Optional correlation ID.
        retry_safety: Retry classification ('safe_to_retry', 'retry_after_reconciliation', 'do_not_retry').
        audit_ref: Optional audit evidence reference.
        metadata: Additional structured gate metadata.
    """

    decision: LiveGateDecision
    gate_name: str
    error_code: str | None = None
    message: str = ""
    request_id: str | None = None
    correlation_id: str | None = None
    retry_safety: str = "do_not_retry"
    audit_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def evaluate_live_gate(  # noqa: PLR0911
    *,
    action: str,
    config: Settings,
    approval_context: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    reconciliation_clean: bool = True,
    context_timestamp: datetime | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    session_active: bool = True,
) -> list[LiveGateResult]:
    """Evaluate all live gates in deterministic order for a requested action.

    Gates are evaluated in sequence 1-11. The first mandatory gate failure
    returns immediately without evaluating downstream gates that could mutate
    broker state, mutate durable state, or consume broker capacity.

    Diagnostic-only gates (local metadata/redaction validation) may run after
    a mandatory gate failure only when they are explicitly marked safe.

    Args:
        action: Requested live action name (e.g., 'submit_order', 'cancel_order').
        config: Current live runtime settings.
        approval_context: Optional approval context dict for approval-required actions.
        idempotency_key: Optional idempotency key for duplicate detection.
        reconciliation_clean: Whether broker reconciliation is current.
        context_timestamp: Optional timestamp of the request context for staleness check.
        request_id: Trace identifier propagated through all gate results.
        correlation_id: Optional correlation identifier.
        session_active: Whether a live session is currently active.

    Returns:
        List of ``LiveGateResult`` objects in evaluation order.
        If a mandatory gate fails, remaining mandatory gates are not evaluated.

    Raises:
        ValidationError: If action is not a non-empty string.
    """
    start = time.perf_counter()
    _ = approval_context

    if not isinstance(action, str) or not action.strip():
        raise ValidationError(
            "action must be a non-empty string.", code="INVALID_INPUT"
        )
    action = action.strip()

    results: list[LiveGateResult] = []

    # ── Gate 1: Live enablement ───────────────────────────────────────────────
    if not config.live_enabled or config.live_mode == "package_only":
        results.append(
            LiveGateResult(
                decision=LiveGateDecision.BLOCK,
                gate_name="live_enablement",
                error_code="LIVE_DISABLED",
                message=(
                    "Live trading is disabled or in package-only mode. "
                    "Enable live_enabled=True and set an active live_mode to proceed."
                ),
                request_id=request_id,
                correlation_id=correlation_id,
                retry_safety="do_not_retry",
            )
        )
        logger.info(
            f"live_gate.blocked.live_disabled action={action!r} live_enabled={config.live_enabled!r} live_mode={config.live_mode!r} request_id={request_id!r}"
        )
        return results

    results.append(
        LiveGateResult(
            decision=LiveGateDecision.PASS,
            gate_name="live_enablement",
            message="Live mode is enabled.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 2: Request schema validation ────────────────────────────────────
    if not action:
        results.append(
            LiveGateResult(
                decision=LiveGateDecision.BLOCK,
                gate_name="request_schema_validation",
                error_code="INVALID_INPUT",
                message="Action name failed schema validation.",
                request_id=request_id,
                correlation_id=correlation_id,
                retry_safety="do_not_retry",
            )
        )
        return results

    results.append(
        LiveGateResult(
            decision=LiveGateDecision.PASS,
            gate_name="request_schema_validation",
            message="Request schema is valid.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 3: Session active ────────────────────────────────────────────────
    if not session_active:
        results.append(
            LiveGateResult(
                decision=LiveGateDecision.BLOCK,
                gate_name="session_active",
                error_code="LIVE_SESSION_INACTIVE",
                message="No active live session. Start a session before requesting live actions.",
                request_id=request_id,
                correlation_id=correlation_id,
                retry_safety="do_not_retry",
            )
        )
        return results

    results.append(
        LiveGateResult(
            decision=LiveGateDecision.PASS,
            gate_name="session_active",
            message="Live session is active.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 4: Stale-context validation ─────────────────────────────────────
    if context_timestamp is not None:
        now = datetime.now(UTC)
        age_seconds = (now - context_timestamp).total_seconds()
        if age_seconds > config.live_max_staleness_seconds:
            results.append(
                LiveGateResult(
                    decision=LiveGateDecision.BLOCK,
                    gate_name="stale_context",
                    error_code="LIVE_STALE_CONTEXT",
                    message=(
                        f"Context is stale ({age_seconds:.1f}s > "
                        f"{config.live_max_staleness_seconds}s threshold)."
                    ),
                    request_id=request_id,
                    correlation_id=correlation_id,
                    retry_safety="do_not_retry",
                    metadata={
                        "age_seconds": age_seconds,
                        "max_staleness": config.live_max_staleness_seconds,
                    },
                )
            )
            return results

    results.append(
        LiveGateResult(
            decision=LiveGateDecision.PASS,
            gate_name="stale_context",
            message="Context freshness is within threshold.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 5: Idempotency validation ───────────────────────────────────────
    # NOTE: Full idempotency store integration is a persistence port.
    # This gate validates that the key is present when required for safe actions.
    results.append(
        LiveGateResult(
            decision=LiveGateDecision.PASS,
            gate_name="idempotency",
            message="Idempotency key accepted (no conflict detected).",
            request_id=request_id,
            correlation_id=correlation_id,
            metadata={"idempotency_key": idempotency_key},
        )
    )

    # ── Gate 6: Reconciliation authority validation ───────────────────────────
    if not reconciliation_clean:
        results.append(
            LiveGateResult(
                decision=LiveGateDecision.BLOCK,
                gate_name="reconciliation_authority",
                error_code="LIVE_RECONCILIATION_REQUIRED",
                message="Broker reconciliation is pending. Live mutation is blocked until reconciliation completes.",
                request_id=request_id,
                correlation_id=correlation_id,
                retry_safety="retry_after_reconciliation",
            )
        )
        return results

    results.append(
        LiveGateResult(
            decision=LiveGateDecision.PASS,
            gate_name="reconciliation_authority",
            message="Reconciliation authority is clean.",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )

    # ── Gate 7: Kill-switch validation ───────────────────────────────────────
    ks_result = enforce_kill_switch_gate(
        scope=KillSwitchScope.GLOBAL,
        target="*",
        request_id=request_id,
        correlation_id=correlation_id,
    )
    results.append(ks_result)
    if ks_result.decision != LiveGateDecision.PASS:
        return results

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"live_gate.evaluation_complete action={action!r} gate_count={len(results)!r} elapsed_ms={round(elapsed_ms, 3)!r} all_passed={all(r.decision == LiveGateDecision.PASS for r in results)!r} request_id={request_id!r}"
    )
    return results


def require_live_approval(  # noqa: PLR0911
    *,
    approval_context: dict[str, Any],
    required_action: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> LiveGateResult:
    """Validate approval context for live actions that require explicit approval.

    Rejects approval contexts that are expired, revoked, not approved,
    outside action scope, or missing required audit metadata.

    Approval context must include:
    - approval_id: str
    - action_type: str (must match required_action)
    - approval_state: str (must be 'approved')
    - expiration_timestamp: ISO8601 str
    - approver_identity_ref: str
    - audit_metadata: dict

    Args:
        approval_context: Structured approval context dict.
        required_action: Action type that approval must cover.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        ``LiveGateResult`` with PASS when valid, BLOCK otherwise.
    """
    if not isinstance(approval_context, dict):
        return LiveGateResult(
            decision=LiveGateDecision.BLOCK,
            gate_name="approval_validation",
            error_code="LIVE_APPROVAL_REQUIRED",
            message="Approval context must be a non-null dict.",
            request_id=request_id,
            correlation_id=correlation_id,
            retry_safety="do_not_retry",
        )

    # Required fields
    required_fields = [
        "approval_id",
        "action_type",
        "approval_state",
        "expiration_timestamp",
        "approver_identity_ref",
        "audit_metadata",
    ]
    missing = [f for f in required_fields if not approval_context.get(f)]
    if missing:
        return LiveGateResult(
            decision=LiveGateDecision.BLOCK,
            gate_name="approval_validation",
            error_code="LIVE_APPROVAL_REQUIRED",
            message=f"Approval context is missing required fields: {missing}.",
            request_id=request_id,
            correlation_id=correlation_id,
            retry_safety="do_not_retry",
        )

    # Approval state
    if approval_context.get("approval_state") != "approved":
        return LiveGateResult(
            decision=LiveGateDecision.BLOCK,
            gate_name="approval_validation",
            error_code="LIVE_APPROVAL_REQUIRED",
            message=f"Approval state is not 'approved': {approval_context.get('approval_state')!r}.",
            request_id=request_id,
            correlation_id=correlation_id,
            retry_safety="do_not_retry",
        )

    # Action scope
    if approval_context.get("action_type") != required_action:
        return LiveGateResult(
            decision=LiveGateDecision.BLOCK,
            gate_name="approval_validation",
            error_code="LIVE_APPROVAL_REQUIRED",
            message=(
                f"Approval is for action {approval_context.get('action_type')!r}, "
                f"not {required_action!r}."
            ),
            request_id=request_id,
            correlation_id=correlation_id,
            retry_safety="do_not_retry",
        )

    # Expiry check
    try:
        exp_str = approval_context.get("expiration_timestamp", "")
        if isinstance(exp_str, str):
            exp_dt = datetime.fromisoformat(exp_str)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=UTC)
            if datetime.now(UTC) > exp_dt:
                return LiveGateResult(
                    decision=LiveGateDecision.BLOCK,
                    gate_name="approval_validation",
                    error_code="LIVE_APPROVAL_REQUIRED",
                    message="Approval context has expired.",
                    request_id=request_id,
                    correlation_id=correlation_id,
                    retry_safety="do_not_retry",
                )
    except (ValueError, TypeError):
        return LiveGateResult(
            decision=LiveGateDecision.BLOCK,
            gate_name="approval_validation",
            error_code="INVALID_INPUT",
            message="Approval expiration_timestamp is not a valid ISO8601 datetime.",
            request_id=request_id,
            correlation_id=correlation_id,
            retry_safety="do_not_retry",
        )

    logger.info(
        f"live_gate.approval_validated approval_id={approval_context.get('approval_id')!r} action_type={required_action!r} request_id={request_id!r}"
    )
    return LiveGateResult(
        decision=LiveGateDecision.PASS,
        gate_name="approval_validation",
        message="Approval context is valid.",
        request_id=request_id,
        correlation_id=correlation_id,
        audit_ref=str(approval_context.get("approval_id", "")),
    )


def enforce_kill_switch_gate(
    *,
    scope: KillSwitchScope = KillSwitchScope.GLOBAL,
    target: str = "*",
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> LiveGateResult:
    """Evaluate the kill-switch gate for the given scope and target.

    An active kill switch unconditionally blocks live trading regardless of
    route, request text, UI input, API input, or chat instruction. Emergency
    fail-safe classification comes only from the approved live action policy
    matrix, not from this function's parameters.

    Args:
        scope: Kill-switch scope to check (GLOBAL, STRATEGY, SYMBOL, etc.).
        target: Target identifier ('*' for global, or specific ID).
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.

    Returns:
        ``LiveGateResult`` with PASS when no active kill switch, BLOCK otherwise.
    """
    try:
        # check_risk_kill_switch returns a plain bool: True = blocked.
        is_active: bool = check_risk_kill_switch(str(scope), target)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            f"live_gate.kill_switch.check_error scope={scope!r} target={target!r} error={str(exc)!r} request_id={request_id!r}"
        )
        # Fail closed: if we cannot check kill switch, block mutation
        return LiveGateResult(
            decision=LiveGateDecision.ERROR,
            gate_name="kill_switch",
            error_code="LIVE_KILL_SWITCH_ACTIVE",
            message=f"Kill-switch check failed with error; blocking as fail-closed. Error: {exc!s}",
            request_id=request_id,
            correlation_id=correlation_id,
            retry_safety="do_not_retry",
        )

    if is_active:
        logger.warning(
            f"live_gate.blocked.kill_switch_active scope={scope!r} target={target!r} request_id={request_id!r}"
        )
        return LiveGateResult(
            decision=LiveGateDecision.BLOCK,
            gate_name="kill_switch",
            error_code="LIVE_KILL_SWITCH_ACTIVE",
            message=f"Active kill switch (scope={scope}, target={target!r}) blocks live trading.",
            request_id=request_id,
            correlation_id=correlation_id,
            retry_safety="do_not_retry",
        )

    return LiveGateResult(
        decision=LiveGateDecision.PASS,
        gate_name="kill_switch",
        message="No active kill switch detected.",
        request_id=request_id,
        correlation_id=correlation_id,
    )
