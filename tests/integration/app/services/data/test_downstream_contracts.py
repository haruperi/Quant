"""Integration tests verifying canonical-contract stability across service boundaries.

These tests exercise the full canonical contract pipeline end-to-end: construction,
serialization, deserialization, hashing, and cross-domain validation.  They do not
depend on any external broker SDK, agent tool, or live data feed.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest
from app.contracts import (
    AccountSnapshot,
    Bar,
    DataSlice,
    IndicatorResult,
    OrderIntent,
    PortfolioSnapshot,
    Position,
    PositionSizingResult,
    RiskDecision,
    RiskRejection,
    StrategySignal,
    TradeRequest,
    TradeResult,
)
from app.contracts.audit import AuditEvent
from app.contracts.trading import BrokerCapabilities
from pydantic import ValidationError as PydanticValidationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(UTC).isoformat()


def _bar(symbol: str = "EURUSD", timeframe: str = "M5") -> Bar:
    return Bar(
        timestamp="2026-06-18T10:00:00+00:00",
        open=1.10001,
        high=1.10500,
        low=1.09500,
        close=1.10200,
        volume=500.0,
        symbol=symbol,
        timeframe=timeframe,
        source="synthetic",
    )


def _data_slice(symbol: str = "EURUSD", timeframe: str = "M5") -> DataSlice:
    return DataSlice(
        bars=[_bar(symbol, timeframe)],
        symbol=symbol,
        timeframe=timeframe,
        source="synthetic",
        provider="synthetic",
        retrieved_at="2026-06-18T10:00:00+00:00",
        normalized_at="2026-06-18T10:00:00+00:00",
    )


def _order_intent(symbol: str = "EURUSD") -> OrderIntent:
    return OrderIntent(
        intent_id="intent_integration_01",
        symbol=symbol,
        action="buy",
        volume=1.0,
        order_type="market",
        risk_decision_id="dec_integration_01",
    )


def _trade_request(intent: OrderIntent | None = None) -> TradeRequest:
    oi = intent or _order_intent()
    return TradeRequest(
        execution_request_id="req_integration_01",
        order_intent=oi,
        submitted_at="2026-06-18T10:00:00+00:00",
        execution_provider="synthetic",
        account_id="acc_test_01",
    )


# ---------------------------------------------------------------------------
# Contract serialization determinism
# ---------------------------------------------------------------------------


def test_bar_round_trip_hash_stability() -> None:
    """Serialize → deserialize → re-serialize must yield identical hashes.

    Guards against float precision drift, key ordering changes, or
    timestamp formatting differences corrupting cache keys.
    """
    original = _bar()
    json_str = original.to_json()
    reconstructed = Bar.model_validate(json.loads(json_str))

    assert original.contract_hash() == reconstructed.contract_hash(), (
        "contract_hash() diverged after round-trip serialization"
    )
    assert original.content_hash() == reconstructed.content_hash(), (
        "content_hash() diverged after round-trip serialization"
    )
    assert json_str == reconstructed.to_json(), (
        "to_json() output changed after round-trip serialization"
    )


def test_data_slice_round_trip_hash_stability() -> None:
    """DataSlice with nested Bar list must survive a round-trip without hash drift."""
    original = _data_slice()
    json_str = original.to_json()
    reconstructed = DataSlice.model_validate(json.loads(json_str))

    assert original.contract_hash() == reconstructed.contract_hash()
    assert original.content_hash() == reconstructed.content_hash()
    assert json_str == reconstructed.to_json()


def test_trade_request_round_trip_hash_stability() -> None:
    """TradeRequest with nested OrderIntent must survive a round-trip."""
    original = _trade_request()
    json_str = original.to_json()
    reconstructed = TradeRequest.model_validate(json.loads(json_str))

    assert original.contract_hash() == reconstructed.contract_hash()
    assert original.content_hash() == reconstructed.content_hash()
    assert json_str == reconstructed.to_json()


def test_risk_decision_approved_round_trip() -> None:
    """Approved RiskDecision with nested OrderIntent must survive a round-trip."""
    intent = _order_intent()
    sizing = PositionSizingResult(
        requested_size=1.0,
        approved_size=1.0,
        sizing_method="fixed_fractional",
        risk_contribution=0.01,
    )
    original = RiskDecision(
        decision_id="dec_rt_01",
        signal_id="sig_hash_rt_01",
        approved=True,
        sizing=sizing,
        approved_order_intent=intent,
    )
    json_str = original.to_json()
    reconstructed = RiskDecision.model_validate(json.loads(json_str))

    assert original.contract_hash() == reconstructed.contract_hash()
    assert original.content_hash() == reconstructed.content_hash()


# ---------------------------------------------------------------------------
# Cross-domain pipeline validation
# ---------------------------------------------------------------------------


def test_full_signal_to_execution_pipeline() -> None:
    """Prove every contract in the pipeline serializes and carries correct hashes.

    Exercises the canonical pipeline:
    Bar → DataSlice → IndicatorResult → StrategySignal → OrderIntent →
    TradeRequest → TradeResult.

    No external dependency — all data is synthetic.
    """
    # Stage 1: Market data
    bar = _bar()
    data_slice = DataSlice(
        bars=[bar],
        symbol="EURUSD",
        timeframe="M5",
        source="synthetic",
        provider="synthetic",
        retrieved_at="2026-06-18T10:00:00+00:00",
        normalized_at="2026-06-18T10:00:00+00:00",
    )
    data_hash = data_slice.content_hash()
    assert data_hash  # non-empty

    # Stage 2: Indicator
    indicator = IndicatorResult(
        name="sma",
        version="1.0.0",
        parameters={"period": 20},
        warmup_period=20,
        input_hash=data_hash,
        output_columns=["sma_20"],
    )
    indicator_hash = indicator.content_hash()
    assert indicator_hash

    # Stage 3: Strategy signal (long validity so it does not expire)
    signal = StrategySignal(
        strategy_id="sma_cross",
        strategy_version="1.0.0",
        parameter_hash="param_hash_01",
        symbol="EURUSD",
        side="buy",
        confidence=0.75,
        validity_window=86400,
        reason="SMA cross-over detected",
        evidence_references=[indicator_hash],
        source_data_hash=data_hash,
    )
    signal_hash = signal.content_hash()
    assert signal_hash

    # Stage 4: Risk decision
    sizing = PositionSizingResult(
        requested_size=1.0,
        approved_size=0.5,
        sizing_method="fixed_fractional",
        risk_contribution=0.005,
    )
    intent = _order_intent()
    decision = RiskDecision(
        decision_id="dec_pipeline_01",
        signal_id=signal_hash,
        approved=True,
        sizing=sizing,
        approved_order_intent=intent,
    )
    assert decision.approved
    assert decision.approved_order_intent is not None

    # Stage 5: Trade request → result
    request = _trade_request(intent)
    result = TradeResult(
        trade_id="trd_pipeline_01",
        execution_request_id=request.execution_request_id,
        status="filled",
        fill_price=1.10005,
        fill_volume=0.5,
        execution_time_ms=22.0,
    )

    # All hashes must be non-empty and stable
    for contract in (bar, data_slice, indicator, signal, decision, request, result):
        h = contract.content_hash()
        assert h, f"{type(contract).__name__}.content_hash() is empty"
        assert len(h) == 64, (
            f"{type(contract).__name__}.content_hash() returned unexpected value: {h!r}"
        )


# ---------------------------------------------------------------------------
# content_hash excludes trace fields
# ---------------------------------------------------------------------------


def test_content_hash_excludes_trace_fields_pipeline() -> None:
    """content_hash() must remain stable when only trace fields differ.

    Simulates two identical StrategySignal contracts produced at slightly
    different timestamps (e.g. retry, replay, audit copy).  Only
    contract_hash() should differ; content_hash() must match.
    """
    # Use the current time so the 86400s validity window does not expire.
    fresh_created_at = datetime.now(UTC).isoformat()
    common_kwargs: dict[str, Any] = {
        "strategy_id": "sma_cross",
        "strategy_version": "1.0.0",
        "parameter_hash": "param_hash_01",
        "symbol": "EURUSD",
        "side": "buy",
        "confidence": 0.75,
        "validity_window": 86400,
        "reason": "SMA cross-over detected",
        "evidence_references": ["indicator_hash_xx"],
        "source_data_hash": "data_hash_xx",
        "created_at": fresh_created_at,
    }

    sig_a = StrategySignal(**common_kwargs)
    sig_b = StrategySignal(**common_kwargs, request_id="req_replay_01")

    assert sig_a.content_hash() == sig_b.content_hash(), (
        "content_hash() must not change when only trace fields differ"
    )
    # contract_hash() covers ALL fields including request_id
    assert sig_a.contract_hash() != sig_b.contract_hash(), (
        "contract_hash() must differ when request_id changes"
    )


# ---------------------------------------------------------------------------
# Cross-domain rejection pipeline
# ---------------------------------------------------------------------------


def test_rejected_risk_decision_pipeline() -> None:
    """A rejected RiskDecision must carry a RiskRejection and no OrderIntent.

    Proves that the mutual-exclusivity validator works end-to-end when
    the decision comes from a full pipeline context.
    """
    rejection = RiskRejection(
        code="MAX_DRAWDOWN_LIMIT",
        severity="error",
        reason="Daily drawdown limit of 3% breached.",
        violated_limit="daily_drawdown_pct",
        evidence={"current_drawdown_pct": 3.12, "limit_pct": 3.0},
        remediation_metadata={"action": "halt_new_orders_today"},
    )
    decision = RiskDecision(
        decision_id="dec_rejected_01",
        signal_id="sig_hash_rejected_01",
        approved=False,
        rejection=rejection,
    )
    assert not decision.approved
    assert decision.rejection is not None
    assert decision.rejection.code == "MAX_DRAWDOWN_LIMIT"
    assert decision.approved_order_intent is None

    # Round-trip must be stable
    reconstructed = RiskDecision.model_validate(json.loads(decision.to_json()))
    assert decision.content_hash() == reconstructed.content_hash()


def test_invalid_risk_decision_both_approved_and_rejected() -> None:
    """RiskDecision with approved=True and a rejection must be refused."""
    with pytest.raises(PydanticValidationError):
        RiskDecision(
            decision_id="dec_invalid_01",
            signal_id="sig_hash_01",
            approved=True,
            rejection=RiskRejection(
                code="CONFLICT",
                severity="error",
                reason="Conflicting state.",
            ),
        )


# ---------------------------------------------------------------------------
# AccountSnapshot and PortfolioSnapshot stability
# ---------------------------------------------------------------------------


def test_portfolio_snapshot_round_trip() -> None:
    """PortfolioSnapshot with nested account + positions must survive round-trip."""
    account = AccountSnapshot(
        equity=50_000.0,
        balance=49_500.0,
        margin=500.0,
        free_margin=49_000.0,
        currency="USD",
        leverage=100,
        timestamp="2026-06-18T10:00:00+00:00",
    )
    position = Position(
        position_id="pos_intg_01",
        symbol="EURUSD",
        side="buy",
        quantity=1.0,
        average_price=1.10000,
        unrealized_pnl=205.0,
        provider_position_id="broker_pos_999",
        opened_at="2026-06-18T09:00:00+00:00",
        updated_at="2026-06-18T10:00:00+00:00",
    )
    snapshot = PortfolioSnapshot(
        account=account,
        positions=[position],
        pending_exposure=0.0,
        risk_budget=0.02,
    )

    json_str = snapshot.to_json()
    reconstructed = PortfolioSnapshot.model_validate(json.loads(json_str))

    assert snapshot.contract_hash() == reconstructed.contract_hash()
    assert snapshot.content_hash() == reconstructed.content_hash()
    assert json_str == reconstructed.to_json()


# ---------------------------------------------------------------------------
# AuditEvent immutability
# ---------------------------------------------------------------------------


def test_audit_event_has_no_extra_timestamp_field() -> None:
    """AuditEvent must not expose a redundant `timestamp` field.

    The event time is carried exclusively by Contract.created_at.
    """
    event = AuditEvent(
        event_id="evt_intg_01",
        event_type="order.placed",
        severity="info",
        actor="risk_engine",
        subject="order_intent_01",
        action="approve",
        evidence=["some_hash_xx"],
    )
    dumped = json.loads(event.to_json())

    # Must carry created_at from the base contract
    assert "created_at" in dumped, "AuditEvent must carry created_at from Contract"

    # Must NOT carry a separate timestamp field
    assert "timestamp" not in dumped, (
        "AuditEvent must not have a separate 'timestamp' field — use created_at"
    )


# ---------------------------------------------------------------------------
# BrokerCapabilities validation
# ---------------------------------------------------------------------------


def test_broker_capabilities_margin_mode_validation() -> None:
    """BrokerCapabilities must enforce margin_mode Literal values.

    margin_mode covers isolated/cross (scope of margin calculation).
    hedging_netting_mode covers netting/hedging (position management mode).
    They are distinct concepts; mixing them must raise ValidationError.
    """
    # Valid cross margin mode
    caps = BrokerCapabilities(
        order_types=["market", "limit", "stop"],
        margin_mode="cross",
        hedging_netting_mode="hedging",
        provider_limits={
            "broker_id": "mt5_icmarkets",
            "supports_partial_fill": True,
            "supports_stop_loss": True,
            "supports_take_profit": True,
        },
    )
    assert caps.margin_mode == "cross"
    assert caps.hedging_netting_mode == "hedging"

    # Invalid margin_mode (netting is NOT a margin mode)
    with pytest.raises(PydanticValidationError):
        BrokerCapabilities(
            order_types=["market"],
            margin_mode="netting",  # type: ignore[arg-type]  # wrong — must be "isolated" or "cross"
            hedging_netting_mode="netting",
            provider_limits={
                "broker_id": "mt5_test",
                "supports_partial_fill": False,
                "supports_stop_loss": False,
                "supports_take_profit": False,
            },
        )
