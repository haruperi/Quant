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

    c2 = Contract(
        schema_version="1.0.0",
        created_at=c1.created_at,
        request_id="req_123",
        workflow_id="wf_456",
        correlation_id="corr_789",
        metadata={"mt5.ticket": 98765},
    )
    assert c1.contract_hash() == c2.contract_hash()


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
    valid_signal = StrategySignal(
        strategy_id="trend_following",
        strategy_version="1.0.0",
        parameter_hash="h_abc123",
        symbol="EURUSD",
        side="buy",
        confidence=0.85,
        validity_window=60,
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
            validity_window=60,
            reason="EMA Crossover",
            evidence_references=[],  # Empty evidence
            source_data_hash="data_h1",
        )

    bad_args: dict[str, Any] = {
        "strategy_id": "trend_following",
        "strategy_version": "1.0.0",
        "parameter_hash": "h_abc123",
        "symbol": "EURUSD",
        "side": "buy",
        "confidence": 0.85,
        "validity_window": 60,
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

    # TradeRequest
    TradeRequest(
        request_id="req_1",
        order_intent=intent,
        submitted_at="2026-06-18 10:00:00",
        execution_provider="mt5",
        account_id="acc_123",
    )

    # TradeResult
    TradeResult(
        trade_id="trd_1",
        request_id="req_1",
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

    # BrokerCapabilities
    BrokerCapabilities(
        margin_mode="netting",
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

    # AuditEvent
    AuditEvent(
        event_id="evt_1",
        event_type="auth",
        severity="info",
        actor="operator",
        subject="admin",
        action="login",
        timestamp="2026-06-18 10:00:00",
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
        return DataSlice(
            symbol=symbol,
            timeframe="tick",
            source="fake",
            provider="fake",
            retrieved_at="2026-06-18 10:00:00",
            normalized_at="2026-06-18 10:00:00",
        )

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        return TradeResult(
            trade_id="fake_trd",
            request_id=request.request_id,
            status="filled",
        )

    def cancel_order(self, request_id: str, _order_id: str) -> TradeResult:
        return TradeResult(
            trade_id="fake_trd",
            request_id=request_id,
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

    def map_error(self, _raw_error: Any) -> str:
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

    Implements ExecutionJournal and TradeStore.
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


def test_store_protocols_conformance() -> None:
    """Verify that FakeTradeStore satisfies journal and store protocols."""
    store = FakeTradeStore()
    assert isinstance(store, ExecutionJournal)
    assert isinstance(store, TradeStore)
