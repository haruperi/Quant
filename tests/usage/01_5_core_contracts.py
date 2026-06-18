"""Usage examples for Phase 1.5 Core Domain Contracts.

Demonstrates the sequential flow of data, signals, and trades using
canonical contracts:
Data -> Indicator -> StrategySignal -> RiskDecision -> OrderIntent ->
Execution -> Reconciliation.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path to support direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.contracts import (
    AccountSnapshot,
    BacktestResult,
    Bar,
    DataSlice,
    ExecutionProvider,
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


class SimulatorExecutionProvider:
    """Simulated trade execution provider."""

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Process simulated execution."""
        msg = (
            f"[Simulator] Executing {request.order_intent.action} for "
            f"{request.order_intent.volume} lots..."
        )
        print(msg)
        return TradeResult(
            trade_id="sim_trd_987",
            request_id=request.request_id,
            status="filled",
            fill_price=request.order_intent.price or 1.1000,
            fill_volume=request.order_intent.volume,
            execution_time_ms=15.5,
        )

    def cancel_order(self, request_id: str, _order_id: str) -> TradeResult:
        return TradeResult(
            trade_id="sim_trd_canc",
            request_id=request_id,
            status="cancelled",
        )


class LiveExecutionProvider:
    """Live execution provider mimicking actual broker connection."""

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """Process live execution, carrying broker-specific metadata."""
        msg = (
            f"[Live MT5] Routing order to market for "
            f"{request.order_intent.volume} lots..."
        )
        print(msg)
        # Populate broker-specific ticket in namespaced metadata
        result_metadata = {
            "mt5.ticket": 556677,
            "mt5.magic": 12345,
            "mt5.reconciliation_ref": "mt5_ref_abc",
        }
        return TradeResult(
            trade_id="live_trd_3321",
            request_id=request.request_id,
            status="filled",
            fill_price=request.order_intent.price or 1.1005,
            fill_volume=request.order_intent.volume,
            execution_time_ms=85.2,
            metadata=result_metadata,
        )

    def cancel_order(self, request_id: str, _order_id: str) -> TradeResult:
        return TradeResult(
            trade_id="live_trd_canc",
            request_id=request_id,
            status="cancelled",
        )


def example_data_slice_construction() -> None:
    """Demonstrate Bar and DataSlice construction."""
    print("\n--- Example 1: Bar and DataSlice Construction ---")
    bar = Bar(
        timestamp=datetime.now(UTC).isoformat(),
        open=1.1000,
        high=1.1050,
        low=1.0950,
        close=1.1020,
        volume=100.0,
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
    )
    print(
        f"Created Bar: {bar.symbol} {bar.timeframe} @ {bar.timestamp} "
        f"(Close: {bar.close})"
    )

    data_slice = DataSlice(
        bars=[bar],
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
        provider="mt5",
        retrieved_at=datetime.now(UTC).isoformat(),
        normalized_at=datetime.now(UTC).isoformat(),
    )
    print(f"Created DataSlice hash: {data_slice.contract_hash()}")


def example_indicator_and_strategy_signal() -> None:
    """Demonstrate IndicatorResult and StrategySignal creation."""
    print("\n--- Example 2: Indicator and StrategySignal ---")
    ind_res = IndicatorResult(
        name="sma",
        version="1.0.0",
        parameters={"period": 20},
        warmup_period=20,
        input_hash="hash_input_123",
        output_columns=["sma_20"],
    )
    print(f"Created IndicatorResult hash: {ind_res.contract_hash()}")

    signal = StrategySignal(
        strategy_id="ma_crossover",
        strategy_version="1.1.0",
        parameter_hash="param_h_99",
        symbol="EURUSD",
        side="buy",
        confidence=0.8,
        validity_window=300,
        reason="SMA 20 crossover",
        evidence_references=[ind_res.contract_hash()],
        source_data_hash="market_hash_77",
    )
    print(
        f"Created StrategySignal: {signal.side} {signal.symbol} "
        f"(Confidence: {signal.confidence})"
    )


def example_risk_decision() -> None:
    """Demonstrate RiskDecision approving or rejecting OrderIntent."""
    print("\n--- Example 3: RiskDecision and OrderIntent ---")
    intent = OrderIntent(
        intent_id="intent_55",
        symbol="EURUSD",
        action="buy",
        volume=1.0,
        order_type="market",
        risk_decision_id="dec_77",
    )

    sizing = PositionSizingResult(
        requested_size=1.0,
        approved_size=1.0,
        sizing_method="fixed",
        risk_contribution=0.01,
    )

    # 1. Approved Decision
    approved_decision = RiskDecision(
        decision_id="dec_77",
        signal_id="sig_hash_99",
        approved=True,
        sizing=sizing,
        approved_order_intent=intent.model_dump(),
    )
    print(f"Approved RiskDecision hash: {approved_decision.contract_hash()}")

    # 2. Rejected Decision
    rejection = RiskRejection(
        code="LIMIT_FAILED",
        severity="error",
        reason="Daily drawdown limit breached.",
    )
    rejected_decision = RiskDecision(
        decision_id="dec_78",
        signal_id="sig_hash_99",
        approved=False,
        rejection=rejection,
    )
    assert rejected_decision.rejection is not None
    print(
        f"Rejected RiskDecision code: {rejected_decision.rejection.code} "
        f"(Reason: {rejected_decision.rejection.reason})"
    )


def example_provider_sharing() -> None:
    """Demonstrate simulator and live execution providers sharing the same protocol."""
    print("\n--- Example 4: Provider Sharing ExecutionProvider Protocol ---")
    intent = OrderIntent(
        intent_id="intent_101",
        symbol="GBPUSD",
        action="buy",
        volume=2.0,
        order_type="market",
        risk_decision_id="dec_88",
    )
    request = TradeRequest(
        request_id="req_999",
        order_intent=intent,
        submitted_at=datetime.now(UTC).isoformat(),
        execution_provider="mt5",
        account_id="acc_abc",
    )

    sim_provider: ExecutionProvider = SimulatorExecutionProvider()
    live_provider: ExecutionProvider = LiveExecutionProvider()

    # Both satisfy ExecutionProvider and process request
    sim_res = sim_provider.execute_trade(request)
    live_res = live_provider.execute_trade(request)

    print(f"Simulator Result Status: {sim_res.status} (Price: {sim_res.fill_price})")
    print(f"Live Result Status: {live_res.status} (Price: {live_res.fill_price})")


def example_metadata_reconciliation() -> None:
    """Demonstrate metadata namespacing and reading custom reconciliation keys."""
    print("\n--- Example 5: Metadata Namespacing and Reconciliation ---")
    intent = OrderIntent(
        intent_id="intent_202",
        symbol="USDJPY",
        action="sell",
        volume=0.5,
        order_type="market",
        risk_decision_id="dec_90",
    )
    request = TradeRequest(
        request_id="req_888",
        order_intent=intent,
        submitted_at=datetime.now(UTC).isoformat(),
        execution_provider="mt5",
        account_id="acc_abc",
    )

    live_provider = LiveExecutionProvider()
    res = live_provider.execute_trade(request)

    # Read namespaced metadata
    ticket = res.metadata.get("mt5.ticket")
    reconciliation_ref = res.metadata.get("mt5.reconciliation_ref")

    print(f"Retrieved namespaced 'mt5.ticket': {ticket}")
    print(f"Retrieved namespaced 'mt5.reconciliation_ref': {reconciliation_ref}")

    # Serialize containing namespaced metadata
    print(f"Serialized JSON: {res.to_json()[:200]}...")


def example_serialization() -> None:
    """Demonstrate serialization of complex objects."""
    print("\n--- Example 6: Serialization of PortfolioSnapshot and BacktestResult ---")
    acc = AccountSnapshot(
        equity=50000.0,
        balance=50000.0,
        margin=1000.0,
        free_margin=49000.0,
        currency="USD",
        leverage=100,
        timestamp=datetime.now(UTC).isoformat(),
    )
    pos = Position(
        position_id="pos_303",
        symbol="EURUSD",
        side="buy",
        quantity=1.0,
        average_price=1.1000,
        unrealized_pnl=250.0,
        provider_position_id="t_pos_1",
        opened_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )
    snap = PortfolioSnapshot(
        account=acc,
        positions=[pos],
        pending_exposure=0.0,
        risk_budget=0.02,
    )
    print(f"PortfolioSnapshot serialized string starts with: {snap.to_json()[:150]}...")

    backtest_res = BacktestResult(
        run_id="bt_run_999",
        config_hash="cfg_hash_888",
        journal_ref="s3://buckets/journals/run_999.json",
        equity_curve_ref="s3://buckets/curves/run_999.json",
        metrics_ref="s3://buckets/metrics/run_999.json",
    )
    print(
        f"BacktestResult serialized string starts with: "
        f"{backtest_res.to_json()[:150]}..."
    )


if __name__ == "__main__":
    example_data_slice_construction()
    example_indicator_and_strategy_signal()
    example_risk_decision()
    example_provider_sharing()
    example_metadata_reconciliation()
    example_serialization()
