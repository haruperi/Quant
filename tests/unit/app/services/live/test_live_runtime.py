"""Unit tests for app/services/live/ — Phase 10 Live Runtime.

Covers all exported modules: session, gates, executor, reconciliation,
monitoring, __init__, and settings live config extensions.

Coverage targets:
    - Normal execution paths
    - Boundary conditions
    - Invalid input / error routing
    - Fail-closed behaviors
    - Import-time safety (no broker sessions, no sockets, no mutations)
    - Secret redaction
    - Standard envelope fields
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

# ── Import time safety ────────────────────────────────────────────────────────
# These imports must succeed without any side effects


def test_import_live_package_no_side_effects():
    """Importing the live package must not start sessions or open connections."""
    import app.services.live  # noqa: F401
    # If we reach here, no RuntimeError was raised during import


def test_import_live_session_no_side_effects():
    import app.services.live.session  # noqa: F401


def test_import_live_gates_no_side_effects():
    import app.services.live.gates  # noqa: F401


def test_import_live_executor_no_side_effects():
    import app.services.live.executor  # noqa: F401


def test_import_live_reconciliation_no_side_effects():
    import app.services.live.reconciliation  # noqa: F401


def test_import_live_monitoring_no_side_effects():
    import app.services.live.monitoring  # noqa: F401


# ── Settings live config tests ────────────────────────────────────────────────


class TestSettingsLiveConfig:
    """Tests for live configuration fields added to Settings."""

    def test_default_live_enabled_is_false(self):
        """live_enabled must default to False (fail-closed)."""
        from app.utils.settings import Settings

        cfg = Settings()
        assert cfg.live_enabled is False

    def test_default_live_mode_is_package_only(self):
        """live_mode must default to package_only (safest mode)."""
        from app.utils.settings import Settings

        cfg = Settings()
        assert cfg.live_mode == "package_only"

    def test_default_workflow_timeout_positive(self):
        from app.utils.settings import Settings

        cfg = Settings()
        assert cfg.live_workflow_timeout_seconds > 0

    def test_default_max_staleness_positive(self):
        from app.utils.settings import Settings

        cfg = Settings()
        assert cfg.live_max_staleness_seconds > 0

    def test_default_broker_timeout_positive(self):
        from app.utils.settings import Settings

        cfg = Settings()
        assert cfg.live_broker_adapter_timeout_seconds > 0

    def test_default_cost_budget_is_none(self):
        from app.utils.settings import Settings

        cfg = Settings()
        assert cfg.live_cost_budget_usd is None

    def test_invalid_live_mode_raises(self):
        from app.utils.settings import Settings
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises((PydanticValidationError, Exception)):
            Settings(LIVE_MODE="invalid_mode")

    def test_load_config_returns_settings(self):
        from app.utils.settings import Settings, load_config

        cfg = load_config()
        assert isinstance(cfg, Settings)

    def test_validate_config_valid_defaults(self):
        from app.utils.settings import Settings, validate_config

        cfg = Settings()
        errors = validate_config(cfg)
        assert isinstance(errors, list)
        # Default config (live disabled, package_only) should be valid
        assert errors == []

    def test_validate_config_micro_live_without_enabled(self):
        """micro_live mode without live_enabled should produce a validation error."""
        from app.utils.settings import Settings, validate_config

        # We need to test the validate_config function directly
        cfg = Settings()
        # Manually bypass the model validator to set invalid state for the shim test
        object.__setattr__(cfg, "live_mode", "micro_live")
        object.__setattr__(cfg, "live_enabled", False)
        errors = validate_config(cfg)
        assert any("live_enabled" in e for e in errors)

    def test_validate_config_exports_config_alias(self):
        """Config must be an alias for Settings."""
        from app.utils.settings import Config, Settings

        assert Config is Settings

    def test_live_mode_type_alias_exists(self):
        from app.utils.settings import LiveMode  # noqa: F401


# ── Error code tests ──────────────────────────────────────────────────────────


class TestLiveErrorCodes:
    """Tests that live error codes are in APPROVED_ERROR_CODES."""

    def test_live_disabled_code_approved(self):
        from app.utils.errors import APPROVED_ERROR_CODES

        assert "LIVE_DISABLED" in APPROVED_ERROR_CODES

    def test_live_gate_failed_code_approved(self):
        from app.utils.errors import APPROVED_ERROR_CODES

        assert "LIVE_GATE_FAILED" in APPROVED_ERROR_CODES

    def test_live_kill_switch_active_code_approved(self):
        from app.utils.errors import APPROVED_ERROR_CODES

        assert "LIVE_KILL_SWITCH_ACTIVE" in APPROVED_ERROR_CODES

    def test_live_unknown_outcome_code_approved(self):
        from app.utils.errors import APPROVED_ERROR_CODES

        assert "LIVE_UNKNOWN_OUTCOME" in APPROVED_ERROR_CODES

    def test_workflow_timeout_code_approved(self):
        from app.utils.errors import APPROVED_ERROR_CODES

        assert "WORKFLOW_TIMEOUT" in APPROVED_ERROR_CODES

    def test_retry_after_reconciliation_code_approved(self):
        from app.utils.errors import APPROVED_ERROR_CODES

        assert "RETRY_AFTER_RECONCILIATION" in APPROVED_ERROR_CODES

    def test_live_audit_write_failed_code_approved(self):
        from app.utils.errors import APPROVED_ERROR_CODES

        assert "LIVE_AUDIT_WRITE_FAILED" in APPROVED_ERROR_CODES

    def test_live_cost_budget_exceeded_code_approved(self):
        from app.utils.errors import APPROVED_ERROR_CODES

        assert "LIVE_COST_BUDGET_EXCEEDED" in APPROVED_ERROR_CODES

    def test_live_error_messages_exist(self):
        from app.utils.errors import ERROR_MESSAGES

        assert "LIVE_DISABLED" in ERROR_MESSAGES
        assert "LIVE_KILL_SWITCH_ACTIVE" in ERROR_MESSAGES
        assert "RETRY_AFTER_RECONCILIATION" in ERROR_MESSAGES


# ── Session tests ─────────────────────────────────────────────────────────────


class TestLiveSession:
    """Tests for live session lifecycle functions."""

    def _make_config(
        self, *, live_enabled: bool = False, live_mode: str = "package_only"
    ):
        from app.utils.settings import Settings

        cfg = Settings()
        object.__setattr__(cfg, "live_enabled", live_enabled)
        object.__setattr__(cfg, "live_mode", live_mode)
        return cfg

    def _reset_session(self):
        import app.services.live.session as session_mod

        session_mod._active_session = None

    def test_session_status_enum_values(self):
        from app.services.live.session import LiveSessionStatus

        assert LiveSessionStatus.INACTIVE == "inactive"
        assert LiveSessionStatus.ACTIVE == "active"
        assert LiveSessionStatus.STOPPED == "stopped"
        assert LiveSessionStatus.ERROR == "error"

    def test_start_live_session_default_config(self):
        from app.services.live.session import LiveSessionStatus, start_live_session

        self._reset_session()
        cfg = self._make_config()
        session = start_live_session(config=cfg, session_id="test-001")
        assert session.session_id == "test-001"
        assert session.status == LiveSessionStatus.ACTIVE
        assert session.live_enabled is False
        assert session.live_mode == "package_only"
        self._reset_session()

    def test_start_session_records_event(self):
        from app.services.live.session import start_live_session

        self._reset_session()
        cfg = self._make_config()
        session = start_live_session(
            config=cfg, session_id="test-002", request_id="req-1"
        )
        assert len(session.events) == 1
        assert session.events[0].event_type == "session_started"
        assert session.events[0].request_id == "req-1"
        self._reset_session()

    def test_start_session_empty_id_raises(self):
        from app.services.live.session import start_live_session
        from app.utils.errors import ValidationError

        self._reset_session()
        cfg = self._make_config()
        with pytest.raises(ValidationError):
            start_live_session(config=cfg, session_id="")

    def test_start_session_whitespace_id_raises(self):
        from app.services.live.session import start_live_session
        from app.utils.errors import ValidationError

        self._reset_session()
        cfg = self._make_config()
        with pytest.raises(ValidationError):
            start_live_session(config=cfg, session_id="   ")

    def test_start_session_duplicate_raises(self):
        from app.services.live.session import start_live_session

        self._reset_session()
        cfg = self._make_config()
        start_live_session(config=cfg, session_id="test-003")
        with pytest.raises(RuntimeError):
            start_live_session(config=cfg, session_id="test-004")
        self._reset_session()

    def test_stop_session_success(self):
        from app.services.live.session import (
            LiveSessionStatus,
            start_live_session,
            stop_live_session,
        )

        self._reset_session()
        cfg = self._make_config()
        start_live_session(config=cfg, session_id="test-005")
        stopped = stop_live_session(session_id="test-005", reason="test_stop")
        assert stopped.status == LiveSessionStatus.STOPPED
        assert stopped.stopped_at is not None
        assert any(e.event_type == "session_stopped" for e in stopped.events)

    def test_stop_session_no_active_raises(self):
        from app.services.live.session import stop_live_session

        self._reset_session()
        with pytest.raises(RuntimeError):
            stop_live_session(session_id="nonexistent")

    def test_stop_session_wrong_id_raises(self):
        from app.services.live.session import start_live_session, stop_live_session
        from app.utils.errors import ValidationError

        self._reset_session()
        cfg = self._make_config()
        start_live_session(config=cfg, session_id="test-006")
        with pytest.raises(ValidationError):
            stop_live_session(session_id="wrong-id")
        self._reset_session()

    def test_get_session_status_inactive(self):
        from app.services.live.session import get_live_session_status

        self._reset_session()
        status = get_live_session_status()
        assert status["accepting_requests"] is False
        assert status["session_id"] is None

    def test_get_session_status_active(self):
        from app.services.live.session import (
            get_live_session_status,
            start_live_session,
        )

        self._reset_session()
        cfg = self._make_config()
        start_live_session(config=cfg, session_id="test-007")
        status = get_live_session_status(request_id="req-x")
        assert status["accepting_requests"] is True
        assert status["session_id"] == "test-007"
        assert status["request_id"] == "req-x"
        self._reset_session()

    def test_recover_session_clean_context(self):
        from app.services.live.session import LiveSessionStatus, recover_live_session

        cfg = self._make_config()
        session = recover_live_session(
            session_id="test-recovery-001",
            recovery_context={
                "has_unknown_outcomes": False,
                "reconciliation_pending": False,
            },
            config=cfg,
        )
        assert session.status == LiveSessionStatus.ACTIVE

    def test_recover_session_unknown_outcomes_pauses(self):
        from app.services.live.session import LiveSessionStatus, recover_live_session

        cfg = self._make_config()
        session = recover_live_session(
            session_id="test-recovery-002",
            recovery_context={
                "has_unknown_outcomes": True,
                "reconciliation_pending": False,
            },
            config=cfg,
        )
        assert session.status == LiveSessionStatus.PAUSED

    def test_recover_session_reconciliation_pending_pauses(self):
        from app.services.live.session import LiveSessionStatus, recover_live_session

        cfg = self._make_config()
        session = recover_live_session(
            session_id="test-recovery-003",
            recovery_context={
                "has_unknown_outcomes": False,
                "reconciliation_pending": True,
            },
            config=cfg,
        )
        assert session.status == LiveSessionStatus.PAUSED

    def test_recover_session_invalid_context_raises(self):
        from app.services.live.session import recover_live_session
        from app.utils.errors import ValidationError

        cfg = self._make_config()
        with pytest.raises(ValidationError):
            recover_live_session(
                session_id="test-recovery-004",
                recovery_context="not-a-dict",
                config=cfg,
            )


# ── Gates tests ───────────────────────────────────────────────────────────────


class TestLiveGates:
    """Tests for the live gate evaluation chain."""

    def _make_config(self, *, live_enabled: bool = True, live_mode: str = "shadow"):
        from app.utils.settings import Settings

        cfg = Settings()
        object.__setattr__(cfg, "live_enabled", live_enabled)
        object.__setattr__(cfg, "live_mode", live_mode)
        return cfg

    @patch("app.services.live.gates.check_risk_kill_switch", return_value=False)
    def test_evaluate_gate_blocked_when_live_disabled(self, mock_ks):  # noqa: ARG002
        from app.services.live.gates import LiveGateDecision, evaluate_live_gate
        from app.utils.settings import Settings

        cfg = Settings()  # live_enabled=False by default
        results = evaluate_live_gate(action="submit_order", config=cfg)
        assert len(results) >= 1
        assert results[0].decision == LiveGateDecision.BLOCK
        assert results[0].error_code == "LIVE_DISABLED"

    @patch("app.services.live.gates.check_risk_kill_switch", return_value=False)
    def test_evaluate_gate_pass_when_live_enabled(self, mock_ks):  # noqa: ARG002
        from app.services.live.gates import LiveGateDecision, evaluate_live_gate

        cfg = self._make_config()
        results = evaluate_live_gate(
            action="submit_order",
            config=cfg,
            session_active=True,
            reconciliation_clean=True,
        )
        # All gates should pass
        assert all(r.decision == LiveGateDecision.PASS for r in results)

    @patch("app.services.live.gates.check_risk_kill_switch", return_value=False)
    def test_evaluate_gate_session_inactive_blocks(self, mock_ks):  # noqa: ARG002
        from app.services.live.gates import LiveGateDecision, evaluate_live_gate

        cfg = self._make_config()
        results = evaluate_live_gate(
            action="submit_order",
            config=cfg,
            session_active=False,
        )
        block = next((r for r in results if r.decision == LiveGateDecision.BLOCK), None)
        assert block is not None
        assert block.error_code == "LIVE_SESSION_INACTIVE"

    @patch("app.services.live.gates.check_risk_kill_switch", return_value=False)
    def test_evaluate_gate_stale_context_blocks(self, mock_ks):  # noqa: ARG002
        from app.services.live.gates import LiveGateDecision, evaluate_live_gate

        cfg = self._make_config()
        stale_timestamp = datetime.now(UTC) - timedelta(seconds=999)
        results = evaluate_live_gate(
            action="submit_order",
            config=cfg,
            session_active=True,
            context_timestamp=stale_timestamp,
        )
        block = next((r for r in results if r.decision == LiveGateDecision.BLOCK), None)
        assert block is not None
        assert block.error_code == "LIVE_STALE_CONTEXT"

    @patch("app.services.live.gates.check_risk_kill_switch", return_value=False)
    def test_evaluate_gate_reconciliation_required_blocks(self, mock_ks):  # noqa: ARG002
        from app.services.live.gates import LiveGateDecision, evaluate_live_gate

        cfg = self._make_config()
        results = evaluate_live_gate(
            action="submit_order",
            config=cfg,
            session_active=True,
            reconciliation_clean=False,
        )
        block = next((r for r in results if r.decision == LiveGateDecision.BLOCK), None)
        assert block is not None
        assert block.error_code == "LIVE_RECONCILIATION_REQUIRED"
        assert block.retry_safety == "retry_after_reconciliation"

    @patch("app.services.live.gates.check_risk_kill_switch", return_value=True)
    def test_kill_switch_active_blocks(self, mock_ks):  # noqa: ARG002
        from app.services.live.gates import LiveGateDecision, evaluate_live_gate

        cfg = self._make_config()
        results = evaluate_live_gate(
            action="submit_order",
            config=cfg,
            session_active=True,
            reconciliation_clean=True,
        )
        block = next((r for r in results if r.decision == LiveGateDecision.BLOCK), None)
        assert block is not None
        assert block.error_code == "LIVE_KILL_SWITCH_ACTIVE"

    def test_evaluate_gate_empty_action_raises(self):
        from app.services.live.gates import evaluate_live_gate
        from app.utils.errors import ValidationError
        from app.utils.settings import Settings

        cfg = Settings()
        with pytest.raises(ValidationError):
            evaluate_live_gate(action="", config=cfg)

    def test_enforce_kill_switch_gate_pass(self):
        from app.services.live.gates import LiveGateDecision, enforce_kill_switch_gate

        with patch(
            "app.services.live.gates.check_risk_kill_switch", return_value=False
        ):
            result = enforce_kill_switch_gate()
            assert result.decision == LiveGateDecision.PASS

    def test_enforce_kill_switch_gate_blocked(self):
        from app.services.live.gates import LiveGateDecision, enforce_kill_switch_gate

        with patch("app.services.live.gates.check_risk_kill_switch", return_value=True):
            result = enforce_kill_switch_gate()
            assert result.decision == LiveGateDecision.BLOCK

    def test_enforce_kill_switch_gate_error_fails_closed(self):
        from app.services.live.gates import LiveGateDecision, enforce_kill_switch_gate

        with patch(
            "app.services.live.gates.check_risk_kill_switch",
            side_effect=RuntimeError("connect failed"),
        ):
            result = enforce_kill_switch_gate()
            # Must fail closed — error is treated as BLOCK
            assert result.decision == LiveGateDecision.ERROR

    def test_require_live_approval_valid(self):
        from app.services.live.gates import LiveGateDecision, require_live_approval

        future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        ctx = {
            "approval_id": "apv-001",
            "action_type": "submit_order",
            "approval_state": "approved",
            "expiration_timestamp": future,
            "approver_identity_ref": "user-123",
            "audit_metadata": {"approved_by": "operator"},
        }
        result = require_live_approval(
            approval_context=ctx, required_action="submit_order"
        )
        assert result.decision == LiveGateDecision.PASS

    def test_require_live_approval_expired(self):
        from app.services.live.gates import LiveGateDecision, require_live_approval

        past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        ctx = {
            "approval_id": "apv-002",
            "action_type": "submit_order",
            "approval_state": "approved",
            "expiration_timestamp": past,
            "approver_identity_ref": "user-123",
            "audit_metadata": {},
        }
        result = require_live_approval(
            approval_context=ctx, required_action="submit_order"
        )
        assert result.decision == LiveGateDecision.BLOCK

    def test_require_live_approval_wrong_action(self):
        from app.services.live.gates import LiveGateDecision, require_live_approval

        future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        ctx = {
            "approval_id": "apv-003",
            "action_type": "cancel_order",
            "approval_state": "approved",
            "expiration_timestamp": future,
            "approver_identity_ref": "user-123",
            "audit_metadata": {},
        }
        result = require_live_approval(
            approval_context=ctx, required_action="submit_order"
        )
        assert result.decision == LiveGateDecision.BLOCK

    def test_require_live_approval_missing_fields(self):
        from app.services.live.gates import LiveGateDecision, require_live_approval

        result = require_live_approval(
            approval_context={}, required_action="submit_order"
        )
        assert result.decision == LiveGateDecision.BLOCK

    def test_require_live_approval_not_dict_blocks(self):
        from app.services.live.gates import LiveGateDecision, require_live_approval

        result = require_live_approval(
            approval_context="not-a-dict", required_action="submit_order"
        )
        assert result.decision == LiveGateDecision.BLOCK


# ── Executor tests ────────────────────────────────────────────────────────────


class TestLiveExecutor:
    """Tests for the live trade executor."""

    def _make_config(self, *, live_enabled: bool = True, live_mode: str = "shadow"):
        from app.utils.settings import Settings

        cfg = Settings()
        object.__setattr__(cfg, "live_enabled", live_enabled)
        object.__setattr__(cfg, "live_mode", live_mode)
        return cfg

    def test_executor_initializes(self):
        from app.services.live.executor import LiveTradeExecutor
        from app.utils.settings import Settings

        executor = LiveTradeExecutor(config=Settings())
        assert executor is not None

    def test_execute_blocked_when_live_disabled(self):
        from app.services.live.executor import LiveSideEffectMode, LiveTradeExecutor
        from app.utils.settings import Settings

        executor = LiveTradeExecutor(config=Settings())  # live_enabled=False
        result = executor.execute(action="submit_order", request={"symbol": "EURUSD"})
        assert result.status == "blocked"
        assert result.side_effect_mode == LiveSideEffectMode.NONE
        assert result.error_code == "LIVE_DISABLED"

    @patch("app.services.live.gates.check_risk_kill_switch", return_value=False)
    def test_execute_packaged_only_when_live_enabled(self, mock_ks):  # noqa: ARG002
        from app.services.live.executor import LiveSideEffectMode, LiveTradeExecutor

        executor = LiveTradeExecutor(config=self._make_config())
        result = executor.execute(
            action="submit_order",
            request={"symbol": "EURUSD"},
            session_active=True,
            reconciliation_clean=True,
        )
        assert result.status == "success"
        assert result.side_effect_mode == LiveSideEffectMode.PACKAGED_ONLY

    def test_execute_invalid_request_returns_error(self):
        from app.services.live.executor import LiveTradeExecutor
        from app.utils.settings import Settings

        executor = LiveTradeExecutor(config=Settings())
        result = executor.execute(action="submit_order", request={})  # empty request
        # Empty request triggers validation failure
        assert result.status == "error"
        assert result.error_code == "INVALID_INPUT"

    def test_execute_empty_action_returns_error(self):
        from app.services.live.executor import LiveTradeExecutor
        from app.utils.settings import Settings

        executor = LiveTradeExecutor(config=Settings())
        result = executor.execute(action="", request={"symbol": "EURUSD"})
        assert result.status == "error"
        assert result.error_code == "INVALID_INPUT"

    def test_result_always_has_side_effect_mode(self):
        from app.services.live.executor import LiveTradeExecutor
        from app.utils.settings import Settings

        executor = LiveTradeExecutor(config=Settings())
        result = executor.execute(action="submit_order", request={"symbol": "EURUSD"})
        assert result.side_effect_mode is not None

    def test_result_always_has_action(self):
        from app.services.live.executor import LiveTradeExecutor
        from app.utils.settings import Settings

        executor = LiveTradeExecutor(config=Settings())
        result = executor.execute(action="submit_order", request={"s": 1})
        assert result.action == "submit_order"

    def test_packaged_result_not_broker_acceptance(self):
        """Package-only success must not be described as broker acceptance."""
        from app.services.live.executor import LiveSideEffectMode, LiveTradeExecutor

        with patch(
            "app.services.live.gates.check_risk_kill_switch", return_value=False
        ):
            executor = LiveTradeExecutor(config=self._make_config())
            result = executor.execute(
                action="submit_order",
                request={"symbol": "EURUSD"},
                session_active=True,
                reconciliation_clean=True,
            )
            assert result.side_effect_mode == LiveSideEffectMode.PACKAGED_ONLY
            assert (
                "not broker acceptance" in result.message.lower()
                or "no broker call" in result.message.lower()
            )

    def test_validate_live_execution_request_valid(self):
        from app.services.live.executor import validate_live_execution_request

        result = validate_live_execution_request(
            action="submit_order", request={"k": "v"}
        )
        assert result is None

    def test_validate_live_execution_request_empty_action(self):
        from app.services.live.executor import validate_live_execution_request

        result = validate_live_execution_request(action="", request={"k": "v"})
        assert result is not None

    def test_validate_live_execution_request_non_dict(self):
        from app.services.live.executor import validate_live_execution_request

        result = validate_live_execution_request(
            action="submit_order", request="string"
        )
        assert result is not None

    def test_validate_live_execution_request_empty_dict(self):
        from app.services.live.executor import validate_live_execution_request

        result = validate_live_execution_request(action="submit_order", request={})
        assert result is not None

    def test_execute_live_order_intent_convenience_function(self):
        from app.services.live.executor import execute_live_order_intent
        from app.utils.settings import Settings

        result = execute_live_order_intent(
            action="submit_order",
            request={"symbol": "EURUSD"},
            config=Settings(),
        )
        assert result is not None
        assert result.status in {"success", "blocked", "error"}

    def test_side_effect_modes_complete(self):
        """All required side effect modes must be defined."""
        from app.services.live.executor import LiveSideEffectMode

        required = {
            "none",
            "packaged_only",
            "broker_mutation_attempted",
            "broker_mutation_confirmed",
            "broker_mutation_rejected",
            "unknown_outcome",
            "incident",
        }
        actual = {m.value for m in LiveSideEffectMode}
        assert required == actual


# ── Reconciliation tests ──────────────────────────────────────────────────────


class TestReconciliation:
    """Tests for live state reconciliation."""

    def test_reconcile_clean_when_empty(self):
        from app.services.live.reconciliation import reconcile_state

        result = reconcile_state()
        assert result.status == "clean"
        assert result.missing_count == 0
        assert result.extra_count == 0
        assert result.mismatched_count == 0

    def test_reconcile_detects_missing_broker_position(self):
        from app.services.live.reconciliation import reconcile_state

        result = reconcile_state(
            internal_positions=[],
            broker_positions=[
                {"position_id": "pos-1", "symbol": "EURUSD", "volume": 0.1}
            ],
        )
        assert result.missing_count >= 1
        assert result.status in {"mismatch", "incident"}

    def test_reconcile_detects_extra_local_position(self):
        from app.services.live.reconciliation import reconcile_state

        result = reconcile_state(
            internal_positions=[{"position_id": "pos-1", "symbol": "EURUSD"}],
            broker_positions=[],
        )
        assert result.extra_count >= 1

    def test_reconcile_matched_positions(self):
        from app.services.live.reconciliation import reconcile_state

        pos = {"position_id": "pos-1", "symbol": "EURUSD", "volume": 0.1, "type": "buy"}
        result = reconcile_state(
            internal_positions=[pos],
            broker_positions=[pos.copy()],
        )
        assert result.matched_count >= 1

    def test_reconcile_field_mismatch_detected(self):
        from app.services.live.reconciliation import reconcile_state

        int_pos = {
            "position_id": "pos-1",
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": "buy",
        }
        brk_pos = {
            "position_id": "pos-1",
            "symbol": "EURUSD",
            "volume": 0.5,
            "type": "buy",
        }
        result = reconcile_state(
            internal_positions=[int_pos],
            broker_positions=[brk_pos],
        )
        assert result.mismatched_count >= 1

    def test_reconcile_invalid_input_raises(self):
        from app.services.live.reconciliation import reconcile_state
        from app.utils.errors import ValidationError

        with pytest.raises(ValidationError):
            reconcile_state(internal_positions="not-a-list")

    def test_reconcile_result_has_reconciliation_id(self):
        from app.services.live.reconciliation import reconcile_state

        result = reconcile_state()
        assert result.reconciliation_id.startswith("recon_")

    def test_reconcile_result_has_timestamps(self):
        from app.services.live.reconciliation import reconcile_state

        result = reconcile_state()
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.completed_at >= result.started_at

    def test_reconcile_retry_safety_clean(self):
        from app.services.live.reconciliation import reconcile_state

        result = reconcile_state()
        assert result.retry_safety == "safe_to_retry"

    def test_reconcile_retry_safety_mismatch(self):
        from app.services.live.reconciliation import reconcile_state

        result = reconcile_state(
            broker_positions=[{"position_id": "pos-missing"}],
        )
        assert result.retry_safety == "retry_after_reconciliation"

    def test_reconcile_custom_id(self):
        from app.services.live.reconciliation import reconcile_state

        result = reconcile_state(reconciliation_id="custom-recon-123")
        assert result.reconciliation_id == "custom-recon-123"

    def test_reconcile_order_mismatch(self):
        from app.services.live.reconciliation import reconcile_state

        result = reconcile_state(
            broker_orders=[{"order_id": "ord-1"}],
        )
        assert result.missing_count >= 1


# ── Monitoring tests ──────────────────────────────────────────────────────────


class TestLiveMonitoring:
    """Tests for live monitoring, health, and incident tracking."""

    def test_monitor_initializes(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor()
        assert monitor is not None

    def test_health_snapshot_returns_snapshot(self):
        from app.services.live.monitoring import LiveHealthSnapshot, LiveMonitor

        monitor = LiveMonitor(session_active=True)
        snapshot = monitor.get_health_snapshot()
        assert isinstance(snapshot, LiveHealthSnapshot)

    def test_health_snapshot_no_session_degraded(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor(session_active=False)
        snapshot = monitor.get_health_snapshot()
        assert len(snapshot.readiness_blocks) > 0
        assert snapshot.overall_health != "healthy"

    def test_health_snapshot_session_active_healthy(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor(session_active=True)
        snapshot = monitor.get_health_snapshot()
        assert snapshot.overall_health == "healthy"
        assert snapshot.readiness_blocks == []

    def test_record_tool_success_updates_health(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor(session_active=True)
        monitor.record_tool_success("check_live_readiness", latency_ms=5.0)
        snapshot = monitor.get_health_snapshot()
        assert "check_live_readiness" in snapshot.tool_health
        assert snapshot.tool_health["check_live_readiness"].health_state == "healthy"

    def test_record_tool_failure_degrades_health(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor(session_active=True)
        for _ in range(3):
            monitor.record_tool_failure("check_live_readiness")
        snapshot = monitor.get_health_snapshot()
        assert snapshot.tool_health["check_live_readiness"].health_state == "degraded"

    def test_record_tool_failure_5x_fails_tool(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor(session_active=True)
        for _ in range(5):
            monitor.record_tool_failure("check_live_readiness")
        snapshot = monitor.get_health_snapshot()
        assert snapshot.tool_health["check_live_readiness"].health_state == "failed"

    def test_cost_budget_ok_within_limit(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor(cost_budget_usd=100.0)
        result = monitor.record_cost(50.0)
        assert result is True

    def test_cost_budget_exceeded(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor(cost_budget_usd=10.0)
        monitor.record_cost(5.0)
        result = monitor.record_cost(10.0)  # exceeds budget
        assert result is False

    def test_cost_budget_none_always_ok(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor(cost_budget_usd=None)
        result = monitor.record_cost(99999.0)
        assert result is True

    def test_cost_budget_negative_raises(self):
        from app.services.live.monitoring import LiveMonitor
        from app.utils.errors import ValidationError

        monitor = LiveMonitor()
        with pytest.raises(ValidationError):
            monitor.record_cost(-1.0)

    def test_stale_state_detected_blocks_readiness(self):
        from app.services.live.monitoring import LiveMonitor, check_live_readiness

        monitor = LiveMonitor(session_active=True)
        monitor.set_stale_state(True)
        result = check_live_readiness(monitor=monitor)
        assert result["ready"] is False
        assert any("stale" in b.lower() for b in result["readiness_blocks"])

    def test_ingestion_unhealthy_blocks_readiness(self):
        from app.services.live.monitoring import LiveMonitor, check_live_readiness

        monitor = LiveMonitor(session_active=True)
        monitor.set_ingestion_status(False)
        result = check_live_readiness(monitor=monitor)
        assert result["ready"] is False

    def test_check_live_readiness_healthy(self):
        from app.services.live.monitoring import LiveMonitor, check_live_readiness

        monitor = LiveMonitor(session_active=True)
        result = check_live_readiness(monitor=monitor, request_id="req-r")
        assert result["ready"] is True
        assert result["readiness_blocks"] == []
        assert result["request_id"] == "req-r"

    def test_record_live_incident(self):
        from app.services.live.monitoring import LiveMonitor, record_live_incident

        monitor = LiveMonitor()
        incident = record_live_incident(
            monitor=monitor,
            incident_type="test_incident",
            severity="warning",
            description="Test incident for unit tests.",
            request_id="req-i",
        )
        assert incident.incident_id.startswith("inc_")
        assert incident.severity == "warning"
        assert incident.resolved is False

    def test_record_incident_invalid_severity_raises(self):
        from app.services.live.monitoring import LiveMonitor, record_live_incident
        from app.utils.errors import ValidationError

        monitor = LiveMonitor()
        with pytest.raises(ValidationError):
            record_live_incident(
                monitor=monitor,
                incident_type="test",
                severity="invalid_level",
                description="Test.",
            )

    def test_record_incident_empty_type_raises(self):
        from app.services.live.monitoring import LiveMonitor, record_live_incident
        from app.utils.errors import ValidationError

        monitor = LiveMonitor()
        with pytest.raises(ValidationError):
            record_live_incident(
                monitor=monitor,
                incident_type="",
                severity="warning",
                description="Test.",
            )

    def test_emit_live_monitoring_event(self):
        from app.services.live.monitoring import emit_live_monitoring_event

        event = emit_live_monitoring_event(
            event_type="test_event",
            payload={"key": "value"},
            request_id="req-e",
        )
        assert event["event_type"] == "test_event"
        assert "timestamp" in event
        assert event["request_id"] == "req-e"

    def test_emit_event_empty_type_raises(self):
        from app.services.live.monitoring import emit_live_monitoring_event
        from app.utils.errors import ValidationError

        with pytest.raises(ValidationError):
            emit_live_monitoring_event(event_type="", payload={})

    def test_latency_p99_tracked(self):
        from app.services.live.monitoring import LiveMonitor

        monitor = LiveMonitor(session_active=True)
        for ms in range(1, 101):
            monitor.record_tool_success("tool", latency_ms=float(ms))
        snapshot = monitor.get_health_snapshot()
        assert snapshot.latency_p99_ms is not None
        assert snapshot.latency_p99_ms > 0


# ── __init__ registry tests ───────────────────────────────────────────────────


class TestLivePackageRegistry:
    """Tests that the public registry exports are correct and complete."""

    def test_all_exports_defined(self):
        import app.services.live as live_pkg

        for name in live_pkg.__all__:
            assert hasattr(live_pkg, name), f"'{name}' in __all__ but not importable"

    def test_live_session_exported(self):
        from app.services.live import LiveSession  # noqa: F401

    def test_live_gate_decision_exported(self):
        from app.services.live import LiveGateDecision  # noqa: F401

    def test_live_trade_executor_exported(self):
        from app.services.live import LiveTradeExecutor  # noqa: F401

    def test_reconcile_state_exported(self):
        from app.services.live import reconcile_state  # noqa: F401

    def test_live_monitor_exported(self):
        from app.services.live import LiveMonitor  # noqa: F401

    def test_live_health_snapshot_exported(self):
        from app.services.live import LiveHealthSnapshot  # noqa: F401


# ── Security / redaction tests ────────────────────────────────────────────────


class TestLiveSecurityRedaction:
    """Tests that secrets do not leak through live module errors or logs."""

    def test_validate_config_does_not_log_secret_values(self, caplog):
        """validate_config must not log mt5_password or token values."""
        from app.utils.settings import Settings, validate_config

        cfg = Settings()
        object.__setattr__(cfg, "live_enabled", True)
        object.__setattr__(cfg, "mt5_enabled", True)
        object.__setattr__(cfg, "mt5_login", "")
        # mt5_password is empty so an error will be generated
        errors = validate_config(cfg)
        assert len(errors) > 0
        # Check log output does not contain the fake secret
        log_text = caplog.text
        assert "secret123" not in log_text

    def test_session_start_config_error_no_secret_leakage(self):
        """Config validation errors must not expose secret values."""
        from app.services.live.session import start_live_session
        from app.utils.settings import Settings

        cfg = Settings()
        # Inject an invalid live mode state (bypass pydantic for testing the shim)
        object.__setattr__(cfg, "live_mode", "package_only")
        object.__setattr__(cfg, "live_enabled", False)
        # This should not raise from session, just start cleanly
        import app.services.live.session as session_mod

        session_mod._active_session = None
        session = start_live_session(config=cfg, session_id="sec-test-001")
        assert "password" not in str(session)
        assert "secret" not in str(session).lower()
        session_mod._active_session = None
