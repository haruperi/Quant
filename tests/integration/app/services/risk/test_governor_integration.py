"""Integration tests verifying end-to-end Risk Governance contract boundaries.

These tests exercise the full governor pipeline using in-memory stores to
confirm approval tokens, kill-switch logic, and audit chaining work together
as a deterministic system across module boundaries.

No broker SDK dependency. No real account credentials. All synthetic data.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.audit import (
    verify_risk_audit_chain,
)
from app.services.risk.governor import RiskGovernor
from app.services.risk.kill_switch import get_kill_switch_manager
from app.services.risk.models import (
    KillSwitchStateEnum,
    PortfolioState,
    ProposedTrade,
    RiskAssessmentRequest,
    RiskAuditEvent,
    RiskConfig,
    RiskDecisionStatus,
)
from app.services.risk.policy import resolve_policy
from app.services.risk.storage import InMemoryRiskStateStore

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_kill_switches() -> Generator[None]:
    """Reset kill switch state before and after each test."""
    manager = get_kill_switch_manager()
    with manager._lock:
        manager.states = {
            "global": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "portfolio": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "strategies": {},
            "symbols": {},
            "currencies": {},
        }
        manager.save()
    yield
    with manager._lock:
        manager.states = {
            "global": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "portfolio": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "strategies": {},
            "symbols": {},
            "currencies": {},
        }
        manager.save()


@pytest.fixture
def store() -> InMemoryRiskStateStore:
    """Fresh in-memory store per test."""
    return InMemoryRiskStateStore()


@pytest.fixture
def governor(store: InMemoryRiskStateStore) -> RiskGovernor:
    """RiskGovernor wired with in-memory stores."""
    return RiskGovernor(
        state_store=store,
        audit_sink=store,
        policy_store=store,
        decision_store=store,
    )


def _make_request(request_id: str = "req-001") -> RiskAssessmentRequest:
    """Build a minimal valid RiskAssessmentRequest with synthetic data."""
    trade = ProposedTrade(
        strategy_id="test-strategy",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.10"),
    )
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={
            "mode": "simulation",
            "freshness": datetime.now(UTC).isoformat(),
            "daily_loss_pct": 0.0,
        },
    )
    req.request_id = request_id
    return req


# ---------------------------------------------------------------------------
# End-to-end governor pipeline tests
# ---------------------------------------------------------------------------


class TestGovernorEndToEnd:
    """Full-pipeline integration tests for the RiskGovernor."""

    def test_simulation_mode_decision_is_deterministic(
        self, governor: RiskGovernor
    ) -> None:
        """Same request produces the same cached decision (idempotency)."""
        req = _make_request("req-determinism")
        decision_a = governor.review_trade_risk(req)
        decision_b = governor.review_trade_risk(req)
        assert decision_a.decision_id == decision_b.decision_id
        assert decision_a.status == decision_b.status

    def test_missing_stop_loss_does_not_crash(self, governor: RiskGovernor) -> None:
        """ProposedTrade without stop loss must return a decision (not exception)."""
        req = _make_request("req-no-sl")
        assert isinstance(req.proposed_action, ProposedTrade)
        req.proposed_action.stop_loss = None
        decision = governor.review_trade_risk(req)
        assert decision.status in {
            RiskDecisionStatus.APPROVE,
            RiskDecisionStatus.REDUCE_SIZE,
            RiskDecisionStatus.REJECT,
            RiskDecisionStatus.BLOCK,
        }

    def test_audit_event_persisted_after_review(
        self,
        governor: RiskGovernor,
        store: InMemoryRiskStateStore,
    ) -> None:
        """Review must persist at least one audit event."""
        req = _make_request("req-audit")
        decision = governor.review_trade_risk(req)
        events: list[RiskAuditEvent] = store._audit_events
        assert len(events) >= 1
        assert events[0].decision_id == decision.decision_id

    def test_policy_resolve_returns_valid_profile(self) -> None:
        """Policy resolver returns a valid result for default config."""
        from app.services.risk.models import RiskConfig

        config = RiskConfig(profile_name="default")
        result = resolve_policy(
            base_config=config, rules=[], context={"mode": "simulation"}
        )
        assert result is not None
        assert hasattr(result, "status")


# ---------------------------------------------------------------------------
# Kill-switch gating tests
# ---------------------------------------------------------------------------


class TestKillSwitchGating:
    """Tests verifying kill-switch blocks governor approvals deterministically."""

    def test_active_global_kill_switch_blocks_trade_review(
        self, governor: RiskGovernor
    ) -> None:
        """Active global kill switch must cause governor to reject the request."""
        governor.kill_switch_manager.trigger(
            scope="global",
            target="*",
            reason="Integration test manual halt",
            triggered_by="test",
        )
        req = _make_request("req-ks-block")
        decision = governor.review_trade_risk(req)
        assert decision.status in {
            RiskDecisionStatus.BLOCK,
            RiskDecisionStatus.REJECT,
            RiskDecisionStatus.HALT_ALL,
        }

    def test_inactive_kill_switch_does_not_block(self, governor: RiskGovernor) -> None:
        """With no kill switches active, governor proceeds normally."""
        req = _make_request("req-ks-ok")
        decision = governor.review_trade_risk(req)
        assert decision.status != RiskDecisionStatus.HALT_ALL


# ---------------------------------------------------------------------------
# Audit chain integrity tests
# ---------------------------------------------------------------------------


class TestAuditChainIntegrity:
    """Tests verifying audit chaining works across multi-step governor calls."""

    def test_two_sequential_reviews_produce_valid_chain(
        self,
        governor: RiskGovernor,
        store: InMemoryRiskStateStore,
    ) -> None:
        """Two sequential reviews produce a verifiable audit chain."""
        governor.review_trade_risk(_make_request("req-chain-1"))
        governor.review_trade_risk(_make_request("req-chain-2"))
        events: list[RiskAuditEvent] = store._audit_events
        assert len(events) >= 2
        assert verify_risk_audit_chain(store) is True


# ---------------------------------------------------------------------------
# Token round-trip tests
# ---------------------------------------------------------------------------


class TestTokenRoundTrip:
    """Integration test for token creation validation via the governor."""

    def test_approve_decision_contains_token(self, governor: RiskGovernor) -> None:
        """An approved decision must include a decision token in its details."""
        req = _make_request("req-token")
        decision = governor.review_trade_risk(req)
        if decision.status == RiskDecisionStatus.APPROVE:
            assert "decision_token" in decision.details
            assert decision.details["decision_token"] != ""

    def test_audit_event_has_non_empty_hash(
        self, store: InMemoryRiskStateStore, governor: RiskGovernor
    ) -> None:
        """Audit events created by the governor must have non-empty event hashes."""
        governor.review_trade_risk(_make_request("req-hash"))
        events: list[RiskAuditEvent] = store._audit_events
        assert len(events) >= 1
        assert events[0].hash != ""
