# ruff: noqa: E501
"""Live trade executor and execution safety checks.

Validates, packages, and classifies live order intents through the gate
chain before any broker mutation can occur. Live mutations are disabled by
default; this module returns ``packaged_only`` results unless live mutation
is explicitly enabled and all mandatory gates pass.

Ownership:
    - Owns live execution safety checks, side-effect classification,
      shadow execution packaging, and broker-mutation isolation.
    - Does NOT implement broker adapters. Broker calls go through approved
      adapter ports (not yet implemented; placeholder bridge used).
    - Does NOT grant AI chat, UI, API, backtest, or optimization workflows
      authority to execute live broker mutations.

Public exports:
    LiveSideEffectMode, LiveTradeExecutor, execute_live_order_intent,
    validate_live_execution_request.

Side effects:
    None on import. No broker sessions are opened, no threads started,
    no network connections made.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from app.services.live.gates import (
    LiveGateDecision,
    LiveGateResult,
    evaluate_live_gate,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.utils.settings import Settings


class LiveSideEffectMode(StrEnum):
    """Classification of the side-effect state for every live result.

    Every live result envelope must include one of these values.

    Attributes:
        NONE: No side effects occurred (e.g., validation-only requests).
        PACKAGED_ONLY: Request was packaged but no broker call was made.
        BROKER_MUTATION_ATTEMPTED: A broker call was attempted (outcome unknown until confirmed/rejected).
        BROKER_MUTATION_CONFIRMED: Broker acknowledged the mutation.
        BROKER_MUTATION_REJECTED: Broker explicitly rejected the mutation.
        UNKNOWN_OUTCOME: Broker outcome cannot be determined (timeout, malformed response).
        INCIDENT: A live incident occurred; manual review required.
    """

    NONE = "none"
    PACKAGED_ONLY = "packaged_only"
    BROKER_MUTATION_ATTEMPTED = "broker_mutation_attempted"
    BROKER_MUTATION_CONFIRMED = "broker_mutation_confirmed"
    BROKER_MUTATION_REJECTED = "broker_mutation_rejected"
    UNKNOWN_OUTCOME = "unknown_outcome"
    INCIDENT = "incident"


@dataclass(frozen=True)
class LiveExecutionResult:
    """Immutable result envelope for a live execution request.

    Attributes:
        status: 'success' | 'error' | 'blocked'.
        side_effect_mode: One of ``LiveSideEffectMode`` values.
        message: Human-readable summary.
        action: The requested action name.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.
        gate_results: Ordered list of gate evaluation results.
        data: Optional structured output payload (redacted, JSON-safe).
        error_code: Approved error code on failure.
        retry_safety: 'safe_to_retry' | 'retry_after_reconciliation' | 'do_not_retry'.
        audit_ref: Optional audit evidence reference.
        execution_ms: Total execution time in milliseconds.
    """

    status: str
    side_effect_mode: LiveSideEffectMode
    message: str
    action: str
    request_id: str | None
    correlation_id: str | None
    gate_results: list[LiveGateResult]
    data: dict[str, Any] | None = None
    error_code: str | None = None
    retry_safety: str = "do_not_retry"
    audit_ref: str | None = None
    execution_ms: float = 0.0


class LiveTradeExecutor:
    """Stateless live trade executor safety gateway.

    Evaluates the gate chain and packages or routes live order intents.
    Live mutation is disabled by default; all calls return ``packaged_only``
    unless live mutation is explicitly enabled and all gates pass.

    Usage:
        executor = LiveTradeExecutor(config=settings)
        result = executor.execute(action="submit_order", request=request_dict)
    """

    def __init__(self, *, config: Settings) -> None:
        """Initialize the executor with the live runtime configuration.

        Args:
            config: Validated ``Settings`` instance.
        """
        self._config = config
        logger.info(
            f"live_executor.initialized live_enabled={config.live_enabled!r} live_mode={config.live_mode!r}"
        )

    def execute(
        self,
        *,
        action: str,
        request: dict[str, Any],
        approval_context: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
        session_active: bool = True,
        reconciliation_clean: bool = True,
        context_timestamp: datetime | None = None,
    ) -> LiveExecutionResult:
        """Execute a live action intent through the mandatory gate chain.

        Validates the request, runs all mandatory gates, and:
        - If any gate blocks: returns a blocked result with no broker call.
        - If all gates pass and live mutation is disabled: returns packaged_only.
        - If all gates pass and live mutation is enabled: packages the request
          for broker routing (actual broker call is a future extension behind
          an approved adapter contract).

        Args:
            action: Requested live action (e.g., 'submit_order').
            request: Validated request payload dict.
            approval_context: Optional approval context for approval-required actions.
            idempotency_key: Idempotency key for duplicate detection.
            request_id: Trace identifier.
            correlation_id: Optional correlation identifier.
            session_active: Whether a live session is currently active.
            reconciliation_clean: Whether broker reconciliation is current.
            context_timestamp: Optional context freshness timestamp.

        Returns:
            ``LiveExecutionResult`` with the final decision and side-effect mode.
        """
        start = time.perf_counter()

        # Validate request dict
        validation_result = validate_live_execution_request(
            action=action,
            request=request,
            request_id=request_id,
        )
        if validation_result is not None:
            return LiveExecutionResult(
                status="error",
                side_effect_mode=LiveSideEffectMode.NONE,
                message=validation_result,
                action=action,
                request_id=request_id,
                correlation_id=correlation_id,
                gate_results=[],
                error_code="INVALID_INPUT",
                retry_safety="do_not_retry",
                execution_ms=(time.perf_counter() - start) * 1000,
            )

        # Evaluate gate chain
        gate_results = evaluate_live_gate(
            action=action,
            config=self._config,
            approval_context=approval_context,
            idempotency_key=idempotency_key,
            reconciliation_clean=reconciliation_clean,
            context_timestamp=context_timestamp,
            request_id=request_id,
            correlation_id=correlation_id,
            session_active=session_active,
        )

        # Check for any gate failures
        failed_gate = next(
            (
                r
                for r in gate_results
                if r.decision in {LiveGateDecision.BLOCK, LiveGateDecision.ERROR}
            ),
            None,
        )
        if failed_gate is not None:
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning(
                f"live_executor.blocked action={action!r} gate={failed_gate.gate_name!r} error_code={failed_gate.error_code!r} request_id={request_id!r}"
            )
            return LiveExecutionResult(
                status="blocked",
                side_effect_mode=LiveSideEffectMode.NONE,
                message=failed_gate.message,
                action=action,
                request_id=request_id,
                correlation_id=correlation_id,
                gate_results=gate_results,
                error_code=failed_gate.error_code,
                retry_safety=failed_gate.retry_safety,
                execution_ms=elapsed,
            )

        # All gates passed — determine side-effect mode
        # Production live mutation is NOT enabled until all Proposed Decisions
        # in the phase spec are updated to Decision: Approved.
        # Until then, this executor always returns packaged_only.
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            f"live_executor.packaged action={action!r} live_mode={self._config.live_mode!r} request_id={request_id!r} elapsed_ms={round(elapsed, 3)!r}"
        )
        return LiveExecutionResult(
            status="success",
            side_effect_mode=LiveSideEffectMode.PACKAGED_ONLY,
            message=(
                f"Action '{action}' was packaged successfully. "
                "Live broker mutation is not enabled; no broker call was made. "
                "Package-only success is not broker acceptance or execution evidence."
            ),
            action=action,
            request_id=request_id,
            correlation_id=correlation_id,
            gate_results=gate_results,
            data={"packaged_action": action, "packaged_request": request},
            retry_safety="safe_to_retry",
            execution_ms=elapsed,
        )


def execute_live_order_intent(
    *,
    action: str,
    request: dict[str, Any],
    config: Settings,
    approval_context: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    session_active: bool = True,
    reconciliation_clean: bool = True,
    context_timestamp: datetime | None = None,
) -> LiveExecutionResult:
    """Module-level convenience wrapper for ``LiveTradeExecutor.execute``.

    Creates a stateless executor with the given config and delegates to it.
    Prefer instantiating ``LiveTradeExecutor`` directly when reusing across
    multiple requests in the same session.

    Args:
        action: Requested live action.
        request: Request payload dict.
        config: Live runtime settings.
        approval_context: Optional approval context.
        idempotency_key: Idempotency key.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.
        session_active: Whether a live session is active.
        reconciliation_clean: Whether reconciliation is current.
        context_timestamp: Optional context freshness timestamp.

    Returns:
        ``LiveExecutionResult`` with decision and side-effect mode.
    """
    executor = LiveTradeExecutor(config=config)
    return executor.execute(
        action=action,
        request=request,
        approval_context=approval_context,
        idempotency_key=idempotency_key,
        request_id=request_id,
        correlation_id=correlation_id,
        session_active=session_active,
        reconciliation_clean=reconciliation_clean,
        context_timestamp=context_timestamp,
    )


def validate_live_execution_request(
    *,
    action: str,
    request: dict[str, Any],
    request_id: str | None = None,
) -> str | None:
    """Validate a live execution request before gate evaluation.

    Returns None when the request is valid. Returns a human-readable error
    string when validation fails. This is a schema boundary check only;
    business logic and risk policy belong to other modules.

    Args:
        action: Requested action name.
        request: Request payload dict.
        request_id: Trace identifier (used in logging only).

    Returns:
        None when valid, or an error message string when invalid.
    """
    if not isinstance(action, str) or not action.strip():
        logger.warning(
            f"live_executor.validation.invalid_action action={action!r} request_id={request_id!r}"
        )
        return "action must be a non-empty string."

    if not isinstance(request, dict):
        logger.warning(
            f"live_executor.validation.invalid_request_type action={action!r} request_id={request_id!r}"
        )
        return "request must be a dict."

    # Reject empty requests
    if not request:
        logger.warning(
            f"live_executor.validation.empty_request action={action!r} request_id={request_id!r}"
        )
        return "request must not be empty."

    return None
