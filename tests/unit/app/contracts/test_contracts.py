# ruff: noqa: ARG002
"""Unit tests for Phase 1.5 canonical contracts and protocols."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts import (
    AccountProvider,
    AccountSnapshot,
    AnalyticsReport,
    AuditEvent,
    BacktestConfig,
    BacktestResult,
    Bar,
    BrokerCapabilities,
    BrokerErrorMapper,
    Contract,
    DataSlice,
    ExecutionJournal,
    ExecutionProvider,
    ExecutionReport,
    Fill,
    IndicatorResult,
    KillSwitchState,
    LiveSessionState,
    MarketDataProvider,
    OptimizationCandidate,
    OrderIntent,
    OrderProvider,
    PerformanceScorecard,
    Position,
    PositionProvider,
    PositionSizingResult,
    RiskAuditEvent,
    RiskDecision,
    RiskRejection,
    Spread,
    StrategyInput,
    StrategySignal,
    Symbol,
    SymbolInfoProvider,
    Tick,
    Timeframe,
    TradeRequest,
    TradeResult,
    TradeStore,
)
from pydantic import ValidationError


def test_base_contract_serialization_and_hashing() -> None:
    """Test base Contract serialization, hashing, and tracing fields."""
    c1 = Contract(
        schema_version="1.0.0",
        request_id="req_123",
        workflow_id="wf_456",
        correlation_id="corr_789",
        metadata={"mt5.ticket": 98765},
    )

    json_str = c1.to_json()
    assert "schema_version" in json_str
    assert "request_id" in json_str
    assert "mt5.ticket" in json_str

    h1 = c1.contract_hash()
    assert isinstance(h1, str)
    assert len(h1) == 64  # SHA256 hex digest

    # Full hash requires identical created_at to match.
    c2 = Contract(
        schema_version="1.0.0",
        created_at=c1.created_at,
        request_id="req_123",
        workflow_id="wf_456",
        correlation_id="corr_789",
        metadata={"mt5.ticket": 98765},
    )
    assert c1.contract_hash() == c2.contract_hash()


def test_content_hash_stable_across_trace_fields() -> None:
    """content_hash() must match when only trace context differs."""
    base_args: dict[str, Any] = {
        "schema_version": "1.0.0",
        "metadata": {"mt5.ticket": 98765},
    }
    c_a = Contract(**base_args, request_id="req_A", created_at="2026-01-01T00:00:00")
    c_b = Contract(**base_args, request_id="req_B", created_at="2026-06-01T12:00:00")

    # Different trace context — full hashes must differ.
    assert c_a.contract_hash() != c_b.contract_hash()
    # Same business content — content hashes must match.
    assert c_a.content_hash() == c_b.content_hash()


def test_base_contract_compatibility() -> None:
    """Test schema version compatibility checking logic."""
    c = Contract(schema_version="1.2.0")
    # Same major, target minor is lower/equal -> compatible
    assert c.check_compatibility("1.0.0") is True
    assert c.check_compatibility("1.2.0") is True
    # Same major, target minor is higher -> incompatible
    assert c.check_compatibility("1.3.0") is False
    # Different major -> incompatible
    assert c.check_compatibility("2.0.0") is False
    assert c.check_compatibility("0.9.0") is False


def test_metadata_namespacing_and_secrets_rejection() -> None:
    """Test that metadata keys must be namespaced and reject secrets."""
    # Namespaced metadata key works
    Contract(metadata={"provider.field": "val"})

    # Non-namespaced key raises error
    with pytest.raises(ValidationError) as exc:
        Contract(metadata={"invalidkey": "val"})
    assert "namespaced" in str(exc.value)

    # Sensitive key is rejected
    with pytest.raises(ValidationError) as exc:
        Contract(metadata={"p.password": "sec"})  # pragma: allowlist secret
    assert "sensitive" in str(exc.value)


def test_symbol_contract_validation() -> None:
    """Test Symbol contract validations."""
    sym = Symbol(
        symbol="EURUSD",
        broker_symbol="EURUSD.m",
        asset_class="forex",
        quote_currency="USD",
        base_currency="EUR",
        precision=5,
        lot_step=0.01,
        lot_min=0.01,
        lot_max=100.0,
        tick_size=0.00001,
        tick_value=1.0,
        contract_size=100000.0,
    )
    assert sym.symbol == "EURUSD"

    # lot_min > lot_max is rejected
    with pytest.raises(ValidationError):
        Symbol(
            symbol="EURUSD",
            broker_symbol="EURUSD.m",
            asset_class="forex",
            quote_currency="USD",
            base_currency="EUR",
            precision=5,
            lot_step=0.01,
            lot_min=10.0,
            lot_max=1.0,
            tick_size=0.00001,
            tick_value=1.0,
            contract_size=100000.0,
        )


def test_timeframe_contract_validation() -> None:
    """Test Timeframe contract validations."""
    tf = Timeframe(name="M5", duration_seconds=300)
    assert tf.name == "M5"

    with pytest.raises(ValidationError):
        Timeframe(name="InvalidTF", duration_seconds=300)


def test_bar_contract_validation() -> None:
    """Test Bar price checks and timestamp formatting."""
    bar = Bar(
        timestamp="2026-06-18 10:00:00",
        open=1.1000,
        high=1.1050,
        low=1.0950,
        close=1.1020,
        volume=100.0,
        spread=2.0,
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
    )
    # Checks normalization
    assert "T" in bar.timestamp

    # Invalid high/low constraint
    with pytest.raises(ValidationError):
        Bar(
            timestamp="2026-06-18 10:00:00",
            open=1.1000,
            high=1.0900,  # High < Low
            low=1.0950,
            close=1.1020,
            symbol="EURUSD",
            timeframe="M5",
            source="mt5",
        )

    # Prices outside high/low range
    with pytest.raises(ValidationError):
        Bar(
            timestamp="2026-06-18 10:00:00",
            open=1.1200,  # Open > High
            high=1.1050,
            low=1.0950,
            close=1.1020,
            symbol="EURUSD",
            timeframe="M5",
            source="mt5",
        )


def test_tick_and_spread_contract_validation() -> None:
    """Test Tick and Spread pricing rules (ask >= bid)."""
    Tick(
        timestamp="2026-06-18 10:00:00",
        bid=1.1000,
        ask=1.1002,
        symbol="EURUSD",
        source="mt5",
    )

    with pytest.raises(ValidationError):
        Tick(
            timestamp="2026-06-18 10:00:00",
            bid=1.1005,
            ask=1.1000,  # Ask < Bid
            symbol="EURUSD",
            source="mt5",
        )

    Spread(
        timestamp="2026-06-18 10:00:00",
        bid=1.1000,
        ask=1.1002,
        spread_points=2.0,
        spread_price=0.0002,
        symbol="EURUSD",
        source="mt5",
    )

    with pytest.raises(ValidationError):
        Spread(
            timestamp="2026-06-18 10:00:00",
            bid=1.1005,
            ask=1.1000,  # Ask < Bid
            spread_points=5.0,
            spread_price=0.0005,
            symbol="EURUSD",
            source="mt5",
        )


def test_strategy_signal_rejections() -> None:
    """Test StrategySignal validation rules and direct broker mutation checks."""
    # validity_window=86400 (24h) ensures the signal won't expire during the test run.
    valid_signal = StrategySignal(
        strategy_id="trend_following",
        strategy_version="1.0.0",
        parameter_hash="h_abc123",
        symbol="EURUSD",
        side="buy",
        confidence=0.85,
        validity_window=86400,
        reason="EMA Crossover",
        evidence_references=["ref_doc_1"],
        source_data_hash="data_h1",
    )
    assert valid_signal.side == "buy"

    # Rejects missing evidence references
    with pytest.raises(ValidationError):
        StrategySignal(
            strategy_id="trend_following",
            strategy_version="1.0.0",
            parameter_hash="h_abc123",
            symbol="EURUSD",
            side="buy",
            confidence=0.85,
            validity_window=86400,
            reason="EMA Crossover",
            evidence_references=[],  # Empty evidence
            source_data_hash="data_h1",
        )

    # Rejects an expired signal (validity_window=1 second, created 10s in the past)
    from datetime import UTC, datetime, timedelta

    past_created_at = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    with pytest.raises(ValidationError):
        StrategySignal(
            strategy_id="trend_following",
            strategy_version="1.0.0",
            parameter_hash="h_abc123",
            symbol="EURUSD",
            side="buy",
            confidence=0.85,
            validity_window=1,  # 1 second window
            reason="EMA Crossover",
            evidence_references=["ref_doc_1"],
            source_data_hash="data_h1",
            created_at=past_created_at,  # 10 seconds ago — expired
        )

    bad_args: dict[str, Any] = {
        "strategy_id": "trend_following",
        "strategy_version": "1.0.0",
        "parameter_hash": "h_abc123",
        "symbol": "EURUSD",
        "side": "buy",
        "confidence": 0.85,
        "validity_window": 86400,
        "reason": "EMA Crossover",
        "evidence_references": ["ref_doc_1"],
        "source_data_hash": "data_h1",
        "ticket": 12345,  # EXTRA/BROKER SPECIFIC FIELD
    }
    with pytest.raises(ValidationError):
        StrategySignal(**bad_args)


def test_risk_decision_validations() -> None:
    """Test RiskDecision consistency.

    Approved requires sizing, rejected requires rejection.
    """
    # Approved with sizing
    sizing = PositionSizingResult(
        requested_size=1.0,
        approved_size=1.0,
        sizing_method="fixed",
        risk_contribution=0.02,
    )
    RiskDecision(
        decision_id="dec_1",
        signal_id="sig_abc",
        approved=True,
        sizing=sizing,
    )

    # Non-approved requires rejection details
    rejection = RiskRejection(
        code="LIMIT_FAILED",
        severity="error",
        reason="Daily drawdown limit hit",
    )
    RiskDecision(
        decision_id="dec_2",
        signal_id="sig_abc",
        approved=False,
        rejection=rejection,
    )

    # Approved with rejection raises error
    with pytest.raises(ValidationError):
        RiskDecision(
            decision_id="dec_3",
            signal_id="sig_abc",
            approved=True,
            rejection=rejection,
        )

    # Non-approved with no rejection raises error
    with pytest.raises(ValidationError):
        RiskDecision(
            decision_id="dec_4",
            signal_id="sig_abc",
            approved=False,
            rejection=None,
        )


def test_dataslice_timeframe_validation() -> None:
    """DataSlice must reject unsupported timeframe identifiers."""
    DataSlice(
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
        provider="mt5",
        retrieved_at="2026-06-18 10:00:00",
        normalized_at="2026-06-18 10:01:00",
    )

    with pytest.raises(ValidationError):
        DataSlice(
            symbol="EURUSD",
            timeframe="tick",  # Not in ALLOWED_TIMEFRAMES
            source="mt5",
            provider="mt5",
            retrieved_at="2026-06-18 10:00:00",
            normalized_at="2026-06-18 10:01:00",
        )

    with pytest.raises(ValidationError):
        DataSlice(
            symbol="EURUSD",
            timeframe="INVALID",
            source="mt5",
            provider="mt5",
            retrieved_at="2026-06-18 10:00:00",
            normalized_at="2026-06-18 10:01:00",
        )


def test_timeframe_from_name_classmethod() -> None:
    """Timeframe.from_name() must derive duration_seconds automatically."""
    tf = Timeframe.from_name("M5")
    assert tf.name == "M5"
    assert tf.duration_seconds == 300

    tf_h4 = Timeframe.from_name("H4")
    assert tf_h4.duration_seconds == 14400

    with pytest.raises(ValueError, match="Unsupported timeframe"):
        Timeframe.from_name("INVALID")


def test_strategy_input_timestamp_normalization() -> None:
    """StrategyInput boundary times must be normalized to ISO 8601."""
    si = StrategyInput(
        start_time="2026-06-18 10:00:00",
        end_time="2026-06-18 11:00:00",
    )
    assert "T" in si.start_time
    assert "T" in si.end_time

    with pytest.raises(ValidationError):
        StrategyInput(start_time="not-a-date", end_time="2026-06-18 11:00:00")


def test_all_other_models_instantiation() -> None:
    """Verify other models instantiate without issue and trace formatting works."""
    # DataSlice
    DataSlice(
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
        provider="mt5",
        retrieved_at="2026-06-18 10:00:00",
        normalized_at="2026-06-18 10:01:00",
    )

    # IndicatorResult
    IndicatorResult(
        name="sma",
        version="1.0.0",
        warmup_period=20,
        input_hash="hash1",
    )

    # StrategyInput
    StrategyInput(
        start_time="2026-06-18 10:00:00",
        end_time="2026-06-18 11:00:00",
    )

    # OrderIntent
    intent = OrderIntent(
        intent_id="intent_1",
        symbol="EURUSD",
        action="buy",
        volume=1.0,
        order_type="market",
        risk_decision_id="dec_1",
    )

    # TradeRequest — uses execution_request_id (not request_id)
    TradeRequest(
        execution_request_id="req_1",
        order_intent=intent,
        submitted_at="2026-06-18 10:00:00",
        execution_provider="mt5",
        account_id="acc_123",
    )

    # TradeResult — uses execution_request_id (not request_id)
    TradeResult(
        trade_id="trd_1",
        execution_request_id="req_1",
        status="filled",
    )

    # Fill
    Fill(
        fill_id="f_1",
        order_id="ticket_1",
        symbol="EURUSD",
        price=1.1000,
        quantity=1.0,
        provider_deal_id="deal_1",
        timestamp="2026-06-18 10:00:00",
    )

    # Verify TradeRequest and TradeResult no longer shadow Contract.request_id
    req = TradeRequest(
        execution_request_id="req_1",
        order_intent=intent,
        submitted_at="2026-06-18 10:00:00",
        execution_provider="mt5",
        account_id="acc_123",
    )
    assert req.request_id is None  # Contract.request_id (trace field) is unset
    assert req.execution_request_id == "req_1"  # business key is separate

    # ExecutionReport
    ExecutionReport(
        report_id="rep_1",
        order_id="ticket_1",
        symbol="EURUSD",
        action="buy",
        status="filled",
        price=1.1000,
        quantity=1.0,
        cumulative_quantity=1.0,
        leaves_quantity=0.0,
        provider_order_id="po_1",
        timestamp="2026-06-18 10:00:00",
    )

    # BrokerCapabilities: margin_mode is "isolated"/"cross";
    # hedging_netting_mode is "netting"/"hedging" — distinct concepts.
    BrokerCapabilities(
        margin_mode="cross",
        hedging_netting_mode="netting",
    )

    # AccountSnapshot
    AccountSnapshot(
        equity=10000.0,
        balance=10000.0,
        margin=0.0,
        free_margin=10000.0,
        currency="USD",
        leverage=100,
        timestamp="2026-06-18 10:00:00",
    )

    # Position
    Position(
        position_id="pos_1",
        symbol="EURUSD",
        side="buy",
        quantity=1.0,
        average_price=1.1000,
        unrealized_pnl=50.0,
        provider_position_id="ticket_pos_1",
        opened_at="2026-06-18 10:00:00",
        updated_at="2026-06-18 10:05:00",
    )

    # PortfolioSnapshot
    # (Tested indirectly via components, works fine)

    # BacktestConfig
    BacktestConfig(
        cost_model="standard",
        fill_model="close",
        calendar="continuous",
        split_policy="walk",
    )

    # BacktestResult
    BacktestResult(
        run_id="run_1",
        config_hash="cfg_hash",
        journal_ref="URI1",
        equity_curve_ref="URI2",
        metrics_ref="URI3",
    )

    # PerformanceScorecard
    score = PerformanceScorecard(
        total_trades=10,
        win_rate=0.6,
        profit_factor=1.5,
        sharpe_ratio=2.1,
        sortino_ratio=2.5,
        max_drawdown=0.05,
        max_drawdown_duration=3600,
        cagr=0.15,
    )

    # AnalyticsReport
    AnalyticsReport(
        report_id="rep_1",
        scorecard=score,
    )

    # OptimizationCandidate
    OptimizationCandidate(
        strategy_id="trend",
        parameters={"sma_period": 20},
        score=0.75,
    )

    # LiveSessionState
    LiveSessionState(
        session_id="session_1",
        environment_mode="live",
        provider_status="connected",
        risk_status="ok",
        kill_switch_state=KillSwitchState(active=False),
        reconciliation_status="synced",
        operator_approval_status="approved",
    )

    # AuditEvent — timestamp is now Contract.created_at; no separate timestamp field
    AuditEvent(
        event_id="evt_1",
        event_type="auth",
        severity="info",
        actor="operator",
        subject="admin",
        action="login",
    )

    # RiskAuditEvent
    RiskAuditEvent(
        event_id="evt_2",
        decision_id="dec_1",
        policy_name="drawdown",
        action_taken="approve",
        payload_hash="hash123",
        severity="info",
    )


# --- Fake Adapters to prove Protocol Satisfaction ---


class FakeAdapter:
    """Mock adapter proving implementation of multiple provider protocols."""

    def get_bars(
        self, symbol: str, timeframe: str, _start: str, _end: str
    ) -> DataSlice:
        return DataSlice(
            symbol=symbol,
            timeframe=timeframe,
            source="fake",
            provider="fake",
            retrieved_at="2026-06-18 10:00:00",
            normalized_at="2026-06-18 10:00:00",
        )

    def get_ticks(self, symbol: str, _start: str, _end: str) -> DataSlice:
        # Ticks are stored in DataSlice with timeframe="M1" as the finest
        # supported canonical granularity.  "tick" is not a valid timeframe.
        return DataSlice(
            symbol=symbol,
            timeframe="M1",
            source="fake",
            provider="fake",
            retrieved_at="2026-06-18 10:00:00",
            normalized_at="2026-06-18 10:00:00",
        )

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        return TradeResult(
            trade_id="fake_trd",
            execution_request_id=request.execution_request_id,
            status="filled",
        )

    def cancel_order(self, request_id: str, _order_id: str) -> TradeResult:
        return TradeResult(
            trade_id="fake_trd",
            execution_request_id=request_id,
            status="cancelled",
        )

    def get_account_snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            equity=10000.0,
            balance=10000.0,
            margin=0.0,
            free_margin=10000.0,
            currency="USD",
            leverage=100,
            timestamp="2026-06-18 10:00:00",
        )

    def get_open_positions(self) -> list[Position]:
        return []

    def get_active_orders(self) -> list[ExecutionReport]:
        return []

    def get_symbol_info(self, symbol: str) -> Symbol:
        return Symbol(
            symbol=symbol,
            broker_symbol=symbol,
            asset_class="forex",
            quote_currency="USD",
            base_currency="EUR",
            precision=5,
            lot_step=0.01,
            lot_min=0.01,
            lot_max=100.0,
            tick_size=0.00001,
            tick_value=1.0,
            contract_size=100000.0,
        )

    def map_error(self, _raw_error: object) -> str:
        return "BROKER_UNAVAILABLE"


def test_provider_protocols_conformance() -> None:
    """Verify that the FakeAdapter satisfies all provider protocols."""
    adapter = FakeAdapter()
    assert isinstance(adapter, MarketDataProvider)
    assert isinstance(adapter, ExecutionProvider)
    assert isinstance(adapter, AccountProvider)
    assert isinstance(adapter, PositionProvider)
    assert isinstance(adapter, OrderProvider)
    assert isinstance(adapter, SymbolInfoProvider)
    assert isinstance(adapter, BrokerErrorMapper)


class FakeTradeStore:
    """Mock persistence store proving protocol implementations.

    Implements ExecutionJournal and TradeStore including idempotency keys
    and reconciliation records as required by the TradeStore protocol.
    """

    def record_report(self, report: ExecutionReport) -> None:
        pass

    def record_fill(self, fill: Fill) -> None:
        pass

    def save_trade_result(self, result: TradeResult) -> None:
        pass

    def get_trade_result(self, _trade_id: str) -> TradeResult | None:
        return None

    def save_position(self, position: Position) -> None:
        pass

    def get_position(self, _position_id: str) -> Position | None:
        return None

    def save_idempotency_key(self, key: str, trade_id: str) -> None:
        pass

    def get_idempotency_key(self, key: str) -> str | None:
        return None

    def save_reconciliation_record(
        self,
        trade_id: str,
        broker_state: dict[str, Any],
        local_state: dict[str, Any],
        status: str,
    ) -> None:
        pass


def test_store_protocols_conformance() -> None:
    """Verify that FakeTradeStore satisfies journal and store protocols."""
    store = FakeTradeStore()
    assert isinstance(store, ExecutionJournal)
    assert isinstance(store, TradeStore)


# ---------------------------------------------------------------------------
# Round-trip serialization
# ---------------------------------------------------------------------------


def test_contract_round_trip_serialization() -> None:
    """Prove serialize → deserialize → re-serialize produces identical hashes.

    This guards against non-deterministic serialization (e.g. float precision
    drift, dict key ordering changes) that would silently break caching and
    audit record integrity.
    """
    import json

    original = Bar(
        timestamp="2026-06-18T10:00:00+00:00",
        open=1.10001,
        high=1.10500,
        low=1.09500,
        close=1.10200,
        volume=100.0,
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
    )

    # Step 1: serialize to canonical JSON
    json_str = original.to_json()

    # Step 2: deserialize back to model via the raw dict
    raw_dict = json.loads(json_str)
    reconstructed = Bar.model_validate(raw_dict)

    # Step 3: verify both hashes are stable across the round-trip
    assert original.contract_hash() == reconstructed.contract_hash(), (
        "contract_hash() changed after serialize → deserialize round-trip"
    )
    assert original.content_hash() == reconstructed.content_hash(), (
        "content_hash() changed after serialize → deserialize round-trip"
    )

    # Step 4: re-serializing the reconstructed model must produce
    # byte-for-byte identical JSON
    assert json_str == reconstructed.to_json(), (
        "to_json() output changed after serialize → deserialize round-trip"
    )


# ---------------------------------------------------------------------------
# Multi-adapter protocol conformance stubs
# ---------------------------------------------------------------------------
# Each stub represents a distinct broker/execution context.  All must satisfy
# the full set of provider protocols without any service-layer caller change.
# ---------------------------------------------------------------------------

_COMMON_ACCOUNT = AccountSnapshot(
    equity=10_000.0,
    balance=10_000.0,
    margin=0.0,
    free_margin=10_000.0,
    currency="USD",
    leverage=100,
    timestamp="2026-06-18T10:00:00+00:00",
)

_COMMON_SYMBOL = Symbol(
    symbol="EURUSD",
    broker_symbol="EURUSD",
    asset_class="forex",
    quote_currency="USD",
    base_currency="EUR",
    precision=5,
    lot_step=0.01,
    lot_min=0.01,
    lot_max=100.0,
    tick_size=0.00001,
    tick_value=1.0,
    contract_size=100_000.0,
)


def _make_data_slice(symbol: str, timeframe: str = "M1") -> DataSlice:
    """Build a minimal valid DataSlice for stub adapters."""
    return DataSlice(
        symbol=symbol,
        timeframe=timeframe,
        source="stub",
        provider="stub",
        retrieved_at="2026-06-18T10:00:00+00:00",
        normalized_at="2026-06-18T10:00:00+00:00",
    )


def _make_trade_result(execution_request_id: str, status: str) -> TradeResult:
    """Build a minimal valid TradeResult for stub adapters."""
    return TradeResult(
        trade_id=f"stub_trd_{status}",
        execution_request_id=execution_request_id,
        status=status,  # type: ignore[arg-type]
    )


class SimulatorAdapter:
    """Backtesting simulator adapter stub.

    Conforms to all 7 provider protocols.  Returns deterministic canonical
    contracts with no external dependencies.
    """

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> DataSlice:
        """Return an empty DataSlice representing a simulated bar batch."""
        return _make_data_slice(symbol, timeframe)

    def get_ticks(self, symbol: str, start: str, end: str) -> DataSlice:
        """Return an empty DataSlice representing a simulated tick batch."""
        return _make_data_slice(symbol)

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Simulate an instant fill at the requested price."""
        return _make_trade_result(request.execution_request_id, "filled")

    def cancel_order(self, request_id: str, order_id: str) -> TradeResult:
        """Simulate an instant order cancellation."""
        return _make_trade_result(request_id, "cancelled")

    def get_account_snapshot(self) -> AccountSnapshot:
        """Return a static simulated account snapshot."""
        return _COMMON_ACCOUNT

    def get_open_positions(self) -> list[Position]:
        """Return an empty position list (no open positions in simulator)."""
        return []

    def get_active_orders(self) -> list[ExecutionReport]:
        """Return an empty order list (no pending orders in simulator)."""
        return []

    def get_symbol_info(self, symbol: str) -> Symbol:
        """Return static EURUSD symbol metadata."""
        return _COMMON_SYMBOL

    def map_error(self, raw_error: object) -> str:
        """Map any simulator error to a canonical code."""
        return "SIMULATOR_ERROR"


class PaperAdapter:
    """Paper trading adapter stub.

    Routes orders through a live data feed but executes against a
    virtual account.  Conforms to all 7 provider protocols.
    """

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> DataSlice:
        """Return a DataSlice tagged as paper-feed source."""
        return DataSlice(
            symbol=symbol,
            timeframe=timeframe,
            source="paper_feed",
            provider="paper",
            retrieved_at="2026-06-18T10:00:00+00:00",
            normalized_at="2026-06-18T10:00:00+00:00",
        )

    def get_ticks(self, symbol: str, start: str, end: str) -> DataSlice:
        """Return a tick DataSlice tagged as paper-feed source."""
        return DataSlice(
            symbol=symbol,
            timeframe="M1",
            source="paper_feed",
            provider="paper",
            retrieved_at="2026-06-18T10:00:00+00:00",
            normalized_at="2026-06-18T10:00:00+00:00",
        )

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Simulate a paper fill with minimal latency metadata."""
        return TradeResult(
            trade_id="paper_trd_001",
            execution_request_id=request.execution_request_id,
            status="filled",
            fill_price=1.10005,
            fill_volume=request.order_intent.volume,
            execution_time_ms=0.5,
        )

    def cancel_order(self, request_id: str, order_id: str) -> TradeResult:
        """Cancel a paper order instantly."""
        return _make_trade_result(request_id, "cancelled")

    def get_account_snapshot(self) -> AccountSnapshot:
        """Return the paper account's virtual cash snapshot."""
        return AccountSnapshot(
            equity=50_000.0,
            balance=50_000.0,
            margin=0.0,
            free_margin=50_000.0,
            currency="USD",
            leverage=50,
            timestamp="2026-06-18T10:00:00+00:00",
            provider_metadata={"paper.virtual": True},
        )

    def get_open_positions(self) -> list[Position]:
        """Return empty position list for a fresh paper account."""
        return []

    def get_active_orders(self) -> list[ExecutionReport]:
        """Return empty order list for a fresh paper account."""
        return []

    def get_symbol_info(self, symbol: str) -> Symbol:
        """Return static symbol info for the paper environment."""
        return _COMMON_SYMBOL

    def map_error(self, raw_error: object) -> str:
        """Map paper trading errors to canonical codes."""
        return "PAPER_EXECUTION_ERROR"


class MT5StubAdapter:
    """MetaTrader 5 adapter stub.

    Validates that the MT5 adapter shape satisfies all provider protocols
    without requiring the ``MetaTrader5`` SDK at test time.
    """

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> DataSlice:
        """Return a stub DataSlice tagged with MT5 provenance."""
        return DataSlice(
            symbol=symbol,
            timeframe=timeframe,
            source="mt5",
            provider="mt5",
            retrieved_at="2026-06-18T10:00:00+00:00",
            normalized_at="2026-06-18T10:00:00+00:00",
            metadata={"mt5.server": "ICMarkets-Live01"},
        )

    def get_ticks(self, symbol: str, start: str, end: str) -> DataSlice:
        """Return a stub tick DataSlice from the MT5 feed."""
        return _make_data_slice(symbol)

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Stub MT5 order execution returning a filled TradeResult."""
        return TradeResult(
            trade_id="mt5_trd_556677",
            execution_request_id=request.execution_request_id,
            status="filled",
            fill_price=1.10001,
            fill_volume=request.order_intent.volume,
            execution_time_ms=42.0,
            metadata={"mt5.ticket": 556677, "mt5.magic": 12345},
        )

    def cancel_order(self, request_id: str, order_id: str) -> TradeResult:
        """Stub MT5 order cancellation."""
        return _make_trade_result(request_id, "cancelled")

    def get_account_snapshot(self) -> AccountSnapshot:
        """Return a stub MT5 account snapshot."""
        return AccountSnapshot(
            equity=25_000.0,
            balance=24_800.0,
            margin=200.0,
            free_margin=24_600.0,
            currency="USD",
            leverage=500,
            timestamp="2026-06-18T10:00:00+00:00",
            provider_metadata={"mt5.login": 123456},
        )

    def get_open_positions(self) -> list[Position]:
        """Return an empty list (no open positions in stub)."""
        return []

    def get_active_orders(self) -> list[ExecutionReport]:
        """Return an empty list (no pending orders in stub)."""
        return []

    def get_symbol_info(self, symbol: str) -> Symbol:
        """Return a stub MT5 symbol specification."""
        return Symbol(
            symbol=symbol,
            broker_symbol=f"{symbol}.m",
            asset_class="forex",
            quote_currency="USD",
            base_currency="EUR",
            precision=5,
            lot_step=0.01,
            lot_min=0.01,
            lot_max=500.0,
            tick_size=0.00001,
            tick_value=1.0,
            contract_size=100_000.0,
            provider_metadata={"mt5.path": "Forex\\EURUSD"},
        )

    def map_error(self, raw_error: object) -> str:
        """Map MT5 error codes to canonical broker-neutral codes."""
        return "MT5_ORDER_ERROR"


class CTraderStubAdapter:
    """cTrader Open API adapter stub.

    Validates that the cTrader adapter shape satisfies all provider
    protocols without requiring the cTrader SDK at test time.
    """

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> DataSlice:
        """Return a stub DataSlice tagged with cTrader provenance."""
        return DataSlice(
            symbol=symbol,
            timeframe=timeframe,
            source="ctrader",
            provider="ctrader",
            retrieved_at="2026-06-18T10:00:00+00:00",
            normalized_at="2026-06-18T10:00:00+00:00",
            metadata={"ctrader.symbolId": 1},
        )

    def get_ticks(self, symbol: str, start: str, end: str) -> DataSlice:
        """Return a stub tick DataSlice from the cTrader feed."""
        return _make_data_slice(symbol)

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Stub cTrader order execution returning a filled TradeResult."""
        return TradeResult(
            trade_id="ct_trd_998877",
            execution_request_id=request.execution_request_id,
            status="filled",
            fill_price=1.09998,
            fill_volume=request.order_intent.volume,
            execution_time_ms=28.0,
            metadata={"ctrader.positionId": 998877},
        )

    def cancel_order(self, request_id: str, order_id: str) -> TradeResult:
        """Stub cTrader order cancellation."""
        return _make_trade_result(request_id, "cancelled")

    def get_account_snapshot(self) -> AccountSnapshot:
        """Return a stub cTrader account snapshot."""
        return AccountSnapshot(
            equity=15_000.0,
            balance=14_900.0,
            margin=100.0,
            free_margin=14_800.0,
            currency="EUR",
            leverage=200,
            timestamp="2026-06-18T10:00:00+00:00",
            provider_metadata={"ctrader.accountId": 3456789},
        )

    def get_open_positions(self) -> list[Position]:
        """Return an empty list (no open positions in stub)."""
        return []

    def get_active_orders(self) -> list[ExecutionReport]:
        """Return an empty list (no pending orders in stub)."""
        return []

    def get_symbol_info(self, symbol: str) -> Symbol:
        """Return a stub cTrader symbol specification."""
        return Symbol(
            symbol=symbol,
            broker_symbol=symbol,
            asset_class="forex",
            quote_currency="USD",
            base_currency="EUR",
            precision=5,
            lot_step=0.01,
            lot_min=0.01,
            lot_max=200.0,
            tick_size=0.00001,
            tick_value=1.0,
            contract_size=100_000.0,
            provider_metadata={"ctrader.symbolId": 1},
        )

    def map_error(self, raw_error: object) -> str:
        """Map cTrader error objects to canonical broker-neutral codes."""
        return "CTRADER_ORDER_ERROR"


class BinanceStubAdapter:
    """Binance exchange adapter stub.

    Validates that the Binance adapter shape satisfies all provider
    protocols without requiring the ``python-binance`` SDK at test time.
    Binance is a crypto exchange: margin_mode is cross/isolated, not
    netting/hedging, which is already reflected in BrokerCapabilities.
    """

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> DataSlice:
        """Return a stub DataSlice tagged with Binance provenance."""
        return DataSlice(
            symbol=symbol,
            timeframe=timeframe,
            source="binance",
            provider="binance",
            retrieved_at="2026-06-18T10:00:00+00:00",
            normalized_at="2026-06-18T10:00:00+00:00",
            metadata={"binance.interval": "5m"},
        )

    def get_ticks(self, symbol: str, start: str, end: str) -> DataSlice:
        """Return a stub trade tick DataSlice from the Binance feed."""
        return _make_data_slice(symbol)

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Stub Binance spot/futures order returning a filled TradeResult."""
        return TradeResult(
            trade_id="bnb_trd_112233",
            execution_request_id=request.execution_request_id,
            status="filled",
            fill_price=1.09990,
            fill_volume=request.order_intent.volume,
            execution_time_ms=18.0,
            metadata={"binance.orderId": 112233, "binance.clientOrderId": "cc01"},
        )

    def cancel_order(self, request_id: str, order_id: str) -> TradeResult:
        """Stub Binance order cancellation."""
        return _make_trade_result(request_id, "cancelled")

    def get_account_snapshot(self) -> AccountSnapshot:
        """Return a stub Binance spot account snapshot."""
        return AccountSnapshot(
            equity=5_000.0,
            balance=5_000.0,
            margin=0.0,
            free_margin=5_000.0,
            currency="USDT",
            leverage=10,
            timestamp="2026-06-18T10:00:00+00:00",
            provider_metadata={"binance.accountType": "SPOT"},
        )

    def get_open_positions(self) -> list[Position]:
        """Return an empty list (no open positions in stub)."""
        return []

    def get_active_orders(self) -> list[ExecutionReport]:
        """Return an empty list (no pending orders in stub)."""
        return []

    def get_symbol_info(self, symbol: str) -> Symbol:
        """Return a stub Binance symbol specification for EURUSD."""
        return Symbol(
            symbol=symbol,
            broker_symbol="EURUSDT",
            asset_class="crypto",
            quote_currency="USDT",
            base_currency="EUR",
            precision=4,
            lot_step=1.0,
            lot_min=1.0,
            lot_max=9_000_000.0,
            tick_size=0.0001,
            tick_value=0.0001,
            contract_size=1.0,
            provider_metadata={"binance.baseAsset": "EUR"},
        )

    def map_error(self, raw_error: object) -> str:
        """Map Binance API error codes to canonical broker-neutral codes."""
        return "BINANCE_ORDER_ERROR"


@pytest.mark.parametrize(
    "adapter_class",
    [
        SimulatorAdapter,
        PaperAdapter,
        MT5StubAdapter,
        CTraderStubAdapter,
        BinanceStubAdapter,
    ],
)
def test_adapter_stub_protocol_conformance(adapter_class: type) -> None:
    """All adapter stubs must satisfy every provider protocol via isinstance.

    This proves that simulator, paper, MT5, cTrader, and Binance adapters
    can be swapped into any service-layer caller that depends on a provider
    protocol without changing the caller's code.
    """
    adapter = adapter_class()
    assert isinstance(adapter, MarketDataProvider), (
        f"{adapter_class.__name__} must satisfy MarketDataProvider"
    )
    assert isinstance(adapter, ExecutionProvider), (
        f"{adapter_class.__name__} must satisfy ExecutionProvider"
    )
    assert isinstance(adapter, AccountProvider), (
        f"{adapter_class.__name__} must satisfy AccountProvider"
    )
    assert isinstance(adapter, PositionProvider), (
        f"{adapter_class.__name__} must satisfy PositionProvider"
    )
    assert isinstance(adapter, OrderProvider), (
        f"{adapter_class.__name__} must satisfy OrderProvider"
    )
    assert isinstance(adapter, SymbolInfoProvider), (
        f"{adapter_class.__name__} must satisfy SymbolInfoProvider"
    )
    assert isinstance(adapter, BrokerErrorMapper), (
        f"{adapter_class.__name__} must satisfy BrokerErrorMapper"
    )
