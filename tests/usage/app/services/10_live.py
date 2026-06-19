# ruff: noqa: E501
"""Phase 10 Live Runtime — Usage Examples.

Demonstrates the official public capabilities of the live runtime service.
Each function covers a standard workflow, important edge case, or fail-closed
path. All examples run without broker connections, real accounts, or live
mutations.

Run this file directly: python tests/usage/app/services/10_live.py

Examples:
    example_01_live_config_and_readiness: Config validation and disabled-by-default.
    example_02_session_lifecycle: Start, pause, stop, recovery.
    example_03_live_gates: Approval, kill-switch, stale-context gate decisions.
    example_04_shadow_and_dry_run_execution: Package-only execution paths.
    example_05_live_executor_boundary: Executor safety checks.
    example_06_reconciliation_and_incidents: Reconciliation states and mismatches.
    example_07_monitoring_and_health: Health, cost budget, latency, incidents.
    example_08_emergency_actions: Governed pause, mass actions, audit requirements.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.services.live.executor import (
    LiveSideEffectMode,
    LiveTradeExecutor,
    execute_live_order_intent,
    validate_live_execution_request,
)
from app.services.live.gates import (
    LiveGateDecision,
    enforce_kill_switch_gate,
    evaluate_live_gate,
    require_live_approval,
)
from app.services.live.monitoring import (
    LiveMonitor,
    check_live_readiness,
    emit_live_monitoring_event,
    record_live_incident,
)
from app.services.live.reconciliation import reconcile_state
from app.services.live.session import (
    LiveSessionStatus,
    get_live_session_status,
    recover_live_session,
    start_live_session,
    stop_live_session,
)
from app.utils.settings import Settings, validate_config

# ── Helper ────────────────────────────────────────────────────────────────────


def _make_settings(**overrides: object) -> Settings:
    """Build a Settings instance with optional overrides for testing."""
    cfg = Settings()
    for key, value in overrides.items():
        object.__setattr__(cfg, key, value)
    return cfg


def _reset_session() -> None:
    import app.services.live.session as session_mod

    session_mod._active_session = None


def _print_section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


# ── Example 01 ────────────────────────────────────────────────────────────────


def example_01_live_config_and_readiness() -> None:
    """Demonstrate live config validation and disabled-by-default mutation policy.

    Key takeaways:
    - live_enabled defaults to False (fail-closed)
    - live_mode defaults to package_only (safest rung)
    - validate_config catches live/broker config inconsistencies without
      leaking secret values
    - load_config() returns the settings singleton safely
    """
    _print_section("Example 01: Live Config & Readiness")

    # Default settings — live is disabled
    cfg = Settings()
    print(f"Default live_enabled: {cfg.live_enabled}")  # False
    print(f"Default live_mode: {cfg.live_mode}")  # package_only
    print(f"Default workflow timeout: {cfg.live_workflow_timeout_seconds}s")
    print(f"Default max staleness: {cfg.live_max_staleness_seconds}s")

    # validate_config with defaults (should be clean)
    errors = validate_config(cfg)
    print(f"\nConfig validation errors (defaults): {errors}")  # []

    # Simulate a live config where live_mode=micro_live but live_enabled=False
    bad_cfg = _make_settings(live_mode="micro_live", live_enabled=False)
    errors = validate_config(bad_cfg)
    print(f"\nConfig validation errors (bad state): {errors}")
    assert any("live_enabled" in e for e in errors), (
        "Expected live_mode/enabled mismatch error"
    )

    # Simulate live_enabled with MT5 but empty credentials
    mt5_cfg = _make_settings(
        live_enabled=True, mt5_enabled=True, mt5_login="", mt5_server=""
    )
    errors = validate_config(mt5_cfg)
    print(f"\nConfig validation errors (MT5 missing creds): {len(errors)} error(s)")
    # Note: password is checked but NOT printed in errors (redacted)
    assert any("mt5_login" in e for e in errors)

    print("\n✓ Example 01 complete — live defaults to disabled (fail-closed)")


# ── Example 02 ────────────────────────────────────────────────────────────────


def example_02_session_lifecycle() -> None:
    """Demonstrate session start, stop, recovery diagnostics, and status events.

    Key takeaways:
    - Sessions cannot be started without valid config
    - Only one active session at a time (single-session guard)
    - stop_live_session stops accepting requests before preserving state
    - Recovery returns PAUSED when unknown outcomes exist
    """
    _print_section("Example 02: Session Lifecycle")
    _reset_session()

    cfg = Settings()

    # Start a session
    session = start_live_session(
        config=cfg, session_id="sess-001", request_id="req-start-1"
    )
    print(f"Session started: {session.session_id}")
    print(f"Status: {session.status}")
    print(f"live_enabled: {session.live_enabled}")
    print(f"live_mode: {session.live_mode}")
    print(f"Events: {[e.event_type for e in session.events]}")
    assert session.status == LiveSessionStatus.ACTIVE

    # Check status
    status = get_live_session_status(request_id="req-status-1")
    print(f"\nStatus envelope: accepting_requests={status['accepting_requests']}")
    assert status["accepting_requests"] is True

    # Stop the session
    stopped = stop_live_session(session_id="sess-001", reason="example_complete")
    print(f"\nStopped: {stopped.status}")
    print(f"Stop events: {[e.event_type for e in stopped.events]}")
    assert stopped.status == LiveSessionStatus.STOPPED

    # Verify status after stop
    status_after = get_live_session_status()
    print(f"Status after stop: accepting_requests={status_after['accepting_requests']}")
    assert status_after["accepting_requests"] is False

    # Recovery — clean context → ACTIVE
    recovered_clean = recover_live_session(
        session_id="sess-recovery-clean",
        recovery_context={
            "has_unknown_outcomes": False,
            "reconciliation_pending": False,
        },
        config=cfg,
    )
    print(f"\nRecovery (clean): {recovered_clean.status}")
    assert recovered_clean.status == LiveSessionStatus.ACTIVE

    # Recovery — unknown outcomes → PAUSED (must review before mutations)
    recovered_paused = recover_live_session(
        session_id="sess-recovery-paused",
        recovery_context={
            "has_unknown_outcomes": True,
            "reconciliation_pending": False,
        },
        config=cfg,
    )
    print(f"Recovery (unknown outcomes): {recovered_paused.status}")
    assert recovered_paused.status == LiveSessionStatus.PAUSED

    print("\n✓ Example 02 complete — session lifecycle verified")


# ── Example 03 ────────────────────────────────────────────────────────────────


def example_03_live_gates() -> None:
    """Demonstrate approval gates, kill-switch gates, and stale-state decisions.

    Key takeaways:
    - Gates evaluate in deterministic order; first failure stops the chain
    - Kill-switch fails closed on check errors
    - Approval context is rejected when expired, wrong-action, or missing fields
    - Reconciliation required returns retry_after_reconciliation
    """
    _print_section("Example 03: Live Gates")

    # Gate 1: live disabled → BLOCK immediately
    cfg_disabled = Settings()  # live_enabled=False
    results = evaluate_live_gate(action="submit_order", config=cfg_disabled)
    print(f"Live disabled gate decision: {results[0].decision}")
    assert results[0].decision == LiveGateDecision.BLOCK
    assert results[0].error_code == "LIVE_DISABLED"

    # Gate chain: all pass when live enabled and kill switch clear
    cfg_live = _make_settings(live_enabled=True, live_mode="shadow")
    with patch("app.services.live.gates.check_risk_kill_switch", return_value=False):
        results = evaluate_live_gate(
            action="submit_order",
            config=cfg_live,
            session_active=True,
            reconciliation_clean=True,
        )
        print(f"\nAll-pass results: {[r.gate_name for r in results]}")
        assert all(r.decision == LiveGateDecision.PASS for r in results)

    # Kill switch active → BLOCK at kill-switch gate
    with patch("app.services.live.gates.check_risk_kill_switch", return_value=True):
        results = evaluate_live_gate(
            action="submit_order",
            config=cfg_live,
            session_active=True,
            reconciliation_clean=True,
        )
        blocked = next(r for r in results if r.decision == LiveGateDecision.BLOCK)
        print(f"\nKill-switch blocked at gate: {blocked.gate_name}")
        assert blocked.error_code == "LIVE_KILL_SWITCH_ACTIVE"

    # Kill switch check error → fail closed
    with patch(
        "app.services.live.gates.check_risk_kill_switch",
        side_effect=ConnectionError("timeout"),
    ):
        result = enforce_kill_switch_gate()
        print(f"\nKill-switch error decision: {result.decision}")
        assert result.decision == LiveGateDecision.ERROR

    # Stale context → BLOCK
    stale_ts = datetime.now(UTC) - timedelta(seconds=999)
    with patch("app.services.live.gates.check_risk_kill_switch", return_value=False):
        results = evaluate_live_gate(
            action="submit_order",
            config=cfg_live,
            session_active=True,
            context_timestamp=stale_ts,
        )
        stale_block = next(r for r in results if r.decision == LiveGateDecision.BLOCK)
        print(f"Stale context error code: {stale_block.error_code}")
        assert stale_block.error_code == "LIVE_STALE_CONTEXT"

    # Reconciliation required → BLOCK + retry_after_reconciliation
    with patch("app.services.live.gates.check_risk_kill_switch", return_value=False):
        results = evaluate_live_gate(
            action="submit_order",
            config=cfg_live,
            session_active=True,
            reconciliation_clean=False,
        )
        recon_block = next(r for r in results if r.decision == LiveGateDecision.BLOCK)
        print(
            f"Reconciliation error code: {recon_block.error_code}, retry: {recon_block.retry_safety}"
        )
        assert recon_block.retry_safety == "retry_after_reconciliation"

    # Approval validation
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    good_ctx = {
        "approval_id": "apv-ex-001",
        "action_type": "submit_order",
        "approval_state": "approved",
        "expiration_timestamp": future,
        "approver_identity_ref": "operator-1",
        "audit_metadata": {"approved_by": "operator"},
    }
    apv_result = require_live_approval(
        approval_context=good_ctx, required_action="submit_order"
    )
    print(f"\nApproval (valid): {apv_result.decision}")
    assert apv_result.decision == LiveGateDecision.PASS

    # Expired approval → BLOCK
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    expired_ctx = {**good_ctx, "expiration_timestamp": past}
    apv_expired = require_live_approval(
        approval_context=expired_ctx, required_action="submit_order"
    )
    print(f"Approval (expired): {apv_expired.decision}")
    assert apv_expired.decision == LiveGateDecision.BLOCK

    print("\n✓ Example 03 complete — gates evaluated deterministically")


# ── Example 04 ────────────────────────────────────────────────────────────────


def example_04_shadow_and_dry_run_execution() -> None:
    """Demonstrate dry-run/shadow execution paths without broker mutation.

    Key takeaways:
    - All results have a side_effect_mode field
    - Package-only results are NOT broker acceptance or evidence
    - No broker adapter is called in package-only mode
    - Shadow/paper execution runs without real broker account
    """
    _print_section("Example 04: Shadow & Dry-Run Execution")

    # Default (live disabled) → blocked, side_effect_mode=none
    result_blocked = execute_live_order_intent(
        action="submit_order",
        request={"symbol": "EURUSD", "volume": 0.01, "order_type": "market"},
        config=Settings(),
    )
    print(f"Blocked result status: {result_blocked.status}")
    print(f"Side effect mode: {result_blocked.side_effect_mode}")
    assert result_blocked.side_effect_mode == LiveSideEffectMode.NONE

    # Live enabled in shadow mode → packaged_only
    shadow_cfg = _make_settings(live_enabled=True, live_mode="shadow")
    with patch("app.services.live.gates.check_risk_kill_switch", return_value=False):
        result_shadow = execute_live_order_intent(
            action="submit_order",
            request={"symbol": "EURUSD", "volume": 0.01, "order_type": "market"},
            config=shadow_cfg,
            session_active=True,
            reconciliation_clean=True,
        )
        print(f"\nShadow result status: {result_shadow.status}")
        print(f"Side effect mode: {result_shadow.side_effect_mode}")
        assert result_shadow.side_effect_mode == LiveSideEffectMode.PACKAGED_ONLY
        # Package-only is not broker acceptance
        assert (
            "not broker acceptance" in result_shadow.message.lower()
            or "no broker call" in result_shadow.message.lower()
        )

    # Different action types also get packaged correctly
    with patch("app.services.live.gates.check_risk_kill_switch", return_value=False):
        for action in ["cancel_order", "close_position", "modify_order"]:
            r = execute_live_order_intent(
                action=action,
                request={"order_id": "ord-1"},
                config=shadow_cfg,
                session_active=True,
                reconciliation_clean=True,
            )
            print(f"Action '{action}': status={r.status}, mode={r.side_effect_mode}")

    print("\n✓ Example 04 complete — shadow/dry-run paths verified, no broker calls")


# ── Example 05 ────────────────────────────────────────────────────────────────


def example_05_live_executor_boundary() -> None:
    """Demonstrate executor safety checks and rejection of invalid requests.

    Key takeaways:
    - Empty action → error, INVALID_INPUT
    - Empty request dict → error, INVALID_INPUT
    - Non-dict request → error, INVALID_INPUT
    - execution_ms is always populated
    """
    _print_section("Example 05: Live Executor Boundary")

    executor = LiveTradeExecutor(config=Settings())

    # Empty action
    r1 = executor.execute(action="", request={"k": "v"})
    print(f"Empty action: status={r1.status}, code={r1.error_code}")
    assert r1.status == "error"
    assert r1.error_code == "INVALID_INPUT"

    # Empty request dict
    r2 = executor.execute(action="submit_order", request={})
    print(f"Empty request: status={r2.status}, code={r2.error_code}")
    assert r2.status == "error"

    # Non-dict request
    r3 = executor.execute(action="submit_order", request="not-a-dict")  # type: ignore[arg-type]
    print(f"Non-dict request: status={r3.status}, code={r3.error_code}")
    assert r3.status == "error"

    # validate_live_execution_request directly
    assert (
        validate_live_execution_request(action="submit_order", request={"k": "v"})
        is None
    )
    assert validate_live_execution_request(action="", request={"k": "v"}) is not None
    assert (
        validate_live_execution_request(action="submit_order", request={}) is not None
    )

    # All results have execution_ms
    for r in [r1, r2, r3]:
        assert r.execution_ms >= 0.0

    print("\n✓ Example 05 complete — executor boundary checks verified")


# ── Example 06 ────────────────────────────────────────────────────────────────


def example_06_reconciliation_and_incidents() -> None:
    """Demonstrate reconciliation states, mismatch detection, and incidents.

    Key takeaways:
    - Empty input → clean status
    - Missing broker position → mismatch
    - Unknown outcomes → retry_after_reconciliation
    - Reconciliation ID is stable and unique
    """
    _print_section("Example 06: Reconciliation & Incidents")

    # Clean reconciliation
    clean = reconcile_state(request_id="req-recon-1")
    print(f"Clean reconciliation: status={clean.status}")
    assert clean.status == "clean"
    assert clean.retry_safety == "safe_to_retry"

    # Missing broker position
    with_missing = reconcile_state(
        internal_positions=[],
        broker_positions=[{"position_id": "pos-1", "symbol": "EURUSD", "volume": 0.1}],
        request_id="req-recon-2",
    )
    print(
        f"Missing position: status={with_missing.status}, missing={with_missing.missing_count}"
    )
    assert with_missing.missing_count >= 1
    assert with_missing.retry_safety == "retry_after_reconciliation"

    # Extra local position
    with_extra = reconcile_state(
        internal_positions=[{"position_id": "pos-x"}],
        broker_positions=[],
        request_id="req-recon-3",
    )
    print(f"Extra position: status={with_extra.status}, extra={with_extra.extra_count}")
    assert with_extra.extra_count >= 1

    # Field mismatch
    int_pos = {"position_id": "pos-m", "symbol": "GBPUSD", "volume": 0.1, "type": "buy"}
    brk_pos = {"position_id": "pos-m", "symbol": "GBPUSD", "volume": 0.5, "type": "buy"}
    with_mismatch = reconcile_state(
        internal_positions=[int_pos],
        broker_positions=[brk_pos],
        request_id="req-recon-4",
    )
    print(
        f"Field mismatch: status={with_mismatch.status}, mismatched={with_mismatch.mismatched_count}"
    )
    assert with_mismatch.mismatched_count >= 1

    # Custom reconciliation ID
    custom = reconcile_state(reconciliation_id="custom-recon-123")
    print(f"Custom ID: {custom.reconciliation_id}")
    assert custom.reconciliation_id == "custom-recon-123"

    print("\n✓ Example 06 complete — reconciliation states verified")


# ── Example 07 ────────────────────────────────────────────────────────────────


def example_07_monitoring_and_health() -> None:
    """Demonstrate latency, ingestion health, tool health, cost, and readiness.

    Key takeaways:
    - LiveMonitor tracks tool success/failure and updates health states
    - Cost budget exceeded → record_cost returns False
    - Stale state or ingestion failure blocks readiness
    - Events are emitted as structured JSON-safe dicts
    """
    _print_section("Example 07: Monitoring & Health")

    monitor = LiveMonitor(
        live_enabled=True,
        live_mode="shadow",
        cost_budget_usd=100.0,
        session_active=True,
    )

    # Record tool success with latency
    monitor.record_tool_success("check_live_readiness", latency_ms=8.5)
    monitor.record_tool_success("evaluate_live_gate", latency_ms=12.0)
    print("Tool successes recorded.")

    # Record failures
    for _ in range(3):
        monitor.record_tool_failure("some_degraded_tool")
    print("3 failures recorded for 'some_degraded_tool'.")

    # Health snapshot
    snapshot = monitor.get_health_snapshot()
    print(f"\nOverall health: {snapshot.overall_health}")
    print(f"Readiness blocks: {snapshot.readiness_blocks}")
    print(f"Latency p99: {snapshot.latency_p99_ms} ms")

    # Cost tracking
    within = monitor.record_cost(50.0)
    print(f"\nCost $50 within budget: {within}")
    assert within is True
    exceeded = monitor.record_cost(60.0)  # total now $110 > $100 budget
    print(f"Cost $60 exceeds budget: {not exceeded}")
    assert exceeded is False

    # Readiness with cost budget exceeded
    result = check_live_readiness(monitor=monitor, request_id="req-health-1")
    print(f"\nReadiness after budget exceeded: ready={result['ready']}")
    assert result["ready"] is False

    # Stale state
    monitor2 = LiveMonitor(session_active=True)
    monitor2.set_stale_state(True)
    result2 = check_live_readiness(monitor=monitor2)
    print(f"Readiness with stale state: ready={result2['ready']}")
    assert result2["ready"] is False

    # Incident recording
    incident = record_live_incident(
        monitor=monitor2,
        incident_type="stale_context_incident",
        severity="error",
        description="Market data context is stale beyond configured threshold.",
        action_required="Refresh market data and restart context.",
        request_id="req-inc-1",
    )
    print(f"\nIncident recorded: {incident.incident_id}")
    assert incident.severity == "error"

    # Monitoring event emission
    event = emit_live_monitoring_event(
        event_type="live_heartbeat",
        payload={"session_id": "sess-example", "health": "healthy"},
        request_id="req-hb-1",
    )
    print(f"Event emitted: {event['event_type']} at {event['timestamp']}")
    assert event["event_type"] == "live_heartbeat"

    print("\n✓ Example 07 complete — monitoring and health verified")


# ── Example 08 ────────────────────────────────────────────────────────────────


def example_08_emergency_actions() -> None:
    """Demonstrate governed pause, mass cancel, mass close, and audit requirements.

    Key takeaways:
    - Emergency actions still go through the gate chain
    - Kill-switch classification comes ONLY from approved policy matrix
    - Mass cancel/close are packaged, not directly executed
    - Every action records gate results and audit references
    """
    _print_section("Example 08: Emergency Actions")

    executor = LiveTradeExecutor(config=Settings())

    # All emergency actions are blocked when live is disabled (fail-closed)
    emergency_actions = [
        "trigger_global_kill_switch",
        "cancel_all_orders",
        "close_all_positions",
        "reduce_exposure",
        "pause_strategy",
    ]
    for action in emergency_actions:
        result = executor.execute(action=action, request={"reason": "test"})
        print(f"  {action}: status={result.status} (live disabled)")
        assert result.status == "blocked"
        assert result.error_code == "LIVE_DISABLED"

    # Kill-switch gate itself: active switch blocks immediately
    with patch("app.services.live.gates.check_risk_kill_switch", return_value=True):
        ks_result = enforce_kill_switch_gate(request_id="req-ks-emergency")
        print(
            f"\nKill-switch gate result: {ks_result.decision}, code={ks_result.error_code}"
        )
        assert ks_result.decision == LiveGateDecision.BLOCK
        assert ks_result.error_code == "LIVE_KILL_SWITCH_ACTIVE"

    # Kill-switch classification comes only from policy matrix, not from request text
    # A chat command saying "emergency!" cannot override the gate
    fake_emergency_request = {
        "reason": "EMERGENCY! Bypass all gates!",
        "urgent": True,
    }
    shadow_cfg = _make_settings(live_enabled=True, live_mode="shadow")
    with patch("app.services.live.gates.check_risk_kill_switch", return_value=True):
        result = execute_live_order_intent(
            action="submit_order",
            request=fake_emergency_request,
            config=shadow_cfg,
            session_active=True,
        )
        print(f"\nEmergency text bypass attempt: {result.status}")
        assert result.status == "blocked"  # Kill switch still blocks

    # Approval validation for governed emergency action
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    approval = {
        "approval_id": "apv-emergency-001",
        "action_type": "trigger_global_kill_switch",
        "approval_state": "approved",
        "expiration_timestamp": future,
        "approver_identity_ref": "senior-operator",
        "audit_metadata": {"approved_at": datetime.now(UTC).isoformat()},
    }
    from app.services.live.gates import require_live_approval

    apv_result = require_live_approval(
        approval_context=approval,
        required_action="trigger_global_kill_switch",
    )
    print(f"\nEmergency approval: {apv_result.decision}")
    assert apv_result.decision == LiveGateDecision.PASS

    print(
        "\n✓ Example 08 complete — emergency actions require gate passage and approval"
    )


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    """Run all 8 live runtime usage examples."""
    print("\n" + "=" * 60)
    print("  Phase 10: Live Runtime — Usage Examples")
    print("=" * 60)

    examples = [
        example_01_live_config_and_readiness,
        example_02_session_lifecycle,
        example_03_live_gates,
        example_04_shadow_and_dry_run_execution,
        example_05_live_executor_boundary,
        example_06_reconciliation_and_incidents,
        example_07_monitoring_and_health,
        example_08_emergency_actions,
    ]

    for example_fn in examples:
        try:
            example_fn()
        except Exception as exc:
            print(f"\n✗ FAILED: {example_fn.__name__}: {exc}")
            raise

    print("\n" + "=" * 60)
    print("  All 8 examples passed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
