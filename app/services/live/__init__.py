"""Live runtime service public registry.

This module exposes the approved public API of the live runtime service.
It acts as a strict middleware/gateway for live-route trading requests and
does NOT implement broker adapters, strategy logic, risk policy, or UI
rendering.

Ownership boundaries:
    - OWNS: Live readiness validation, gate evaluation, response
      classification, error mapping, session lifecycle, monitoring,
      reconciliation authority state.
    - DOES NOT OWN: Broker adapter implementation, market-data ingestion,
      strategy signal generation, risk policy creation, approval-policy
      creation, UI rendering, websocket management, or frontend workflow
      policy.

Public exports:
    LiveSession, LiveSessionStatus, LiveGateDecision, LiveGateResult,
    LiveTradeExecutor, LiveSideEffectMode, LiveMonitor, LiveHealthSnapshot,
    start_live_session, stop_live_session, recover_live_session,
    get_live_session_status, evaluate_live_gate, require_live_approval,
    enforce_kill_switch_gate, execute_live_order_intent,
    validate_live_execution_request, reconcile_state,
    check_live_readiness, record_live_incident, emit_live_monitoring_event.

Side effects:
    None. Importing this module does NOT start broker sessions, open sockets,
    spawn threads, start async tasks, initialize broker SDK sessions, resolve
    raw secret values, or mutate any state.
"""

from __future__ import annotations

from app.services.live.executor import (
    LiveSideEffectMode,
    LiveTradeExecutor,
    execute_live_order_intent,
    validate_live_execution_request,
)
from app.services.live.gates import (
    LiveGateDecision,
    LiveGateResult,
    enforce_kill_switch_gate,
    evaluate_live_gate,
    require_live_approval,
)
from app.services.live.monitoring import (
    LiveHealthSnapshot,
    LiveMonitor,
    check_live_readiness,
    emit_live_monitoring_event,
    record_live_incident,
)
from app.services.live.reconciliation import (
    ReconciliationResult,
    reconcile_state,
)
from app.services.live.session import (
    LiveSession,
    LiveSessionStatus,
    get_live_session_status,
    recover_live_session,
    start_live_session,
    stop_live_session,
)

__all__ = [
    # Gates
    "LiveGateDecision",
    "LiveGateResult",
    "LiveHealthSnapshot",
    # Monitoring
    "LiveMonitor",
    # Session
    "LiveSession",
    "LiveSessionStatus",
    # Executor
    "LiveSideEffectMode",
    "LiveTradeExecutor",
    # Reconciliation
    "ReconciliationResult",
    "check_live_readiness",
    "emit_live_monitoring_event",
    "enforce_kill_switch_gate",
    "evaluate_live_gate",
    "execute_live_order_intent",
    "get_live_session_status",
    "reconcile_state",
    "record_live_incident",
    "recover_live_session",
    "require_live_approval",
    "start_live_session",
    "stop_live_session",
    "validate_live_execution_request",
]
