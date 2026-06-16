# ruff: noqa: E501, RUF012, ARG002
"""Unit tests for vectorized batch strategy signal execution."""

from datetime import UTC, datetime
from typing import Any, Literal

import numpy as np
import pandas as pd
import pytest
from app.services.strategies import (
    StrategyExecutionContext,
    StrategyRefInput,
    TradeIntent,
    register_strategy,
    run_vectorized_strategy_signals,
    unregister_strategy,
)


class VectorizedMockStrategy:
    """Mock strategy returning customizable TradeIntents for vectorized testing."""

    strategy_id = "vec_mock"
    version = "1.0.0"
    lifecycle_status = "RESEARCH"
    permitted_environments = ["BACKTEST"]
    config_schema = None
    config_model = None
    risk_profile = None
    max_data_latency_tolerance = pd.Timedelta(hours=2)

    def run_vectorized_signals(
        self,
        data: pd.DataFrame,
        indicators: pd.DataFrame,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> list[TradeIntent]:
        # Return intents based on indicators column
        intents = []
        for idx, row in indicators.iterrows():
            ts = idx if isinstance(idx, pd.Timestamp) else idx[1]
            val = row["signal_val"]
            if np.isnan(val) or val == 0:
                continue

            side: Literal["BUY", "SELL", "HOLD"] = "BUY" if val > 0 else "SELL"

            # Use alpha and transaction cost hints for suppression test
            lineage = {
                "expected_alpha": str(config.get("mock_alpha", "0.05")),
                "estimated_transaction_cost": str(config.get("mock_cost", "0.01")),
            }

            intents.append(
                TradeIntent(
                    intent_id=f"intent-{ts.isoformat()}",
                    decision_id=f"decision-{ts.isoformat()}",
                    idempotency_key=f"idem-{ts.isoformat()}",
                    strategy_id=self.strategy_id,
                    strategy_version=self.version,
                    symbol="EURUSD",
                    side=side,
                    intent_type="OPEN",
                    signal_timestamp=ts,
                    # Under Timing Policy, the decision is at the Open of the next bar (e.g. + 1 hour)
                    decision_timestamp=ts + pd.Timedelta(hours=1),
                    lineage=lineage,
                )
            )
        return intents


class LookaheadVectorizedStrategy(VectorizedMockStrategy):
    """Strategy that leaks future data (signal timestamp is at or after decision timestamp)."""

    strategy_id = "lookahead_mock"

    def run_vectorized_signals(self, data, indicators, context, config):
        intents = super().run_vectorized_signals(data, indicators, context, config)
        # Mutate to lookahead
        for intent in intents:
            intent.signal_timestamp = intent.decision_timestamp
        return intents


@pytest.fixture(autouse=True)
def setup_mock_strategies():
    """Register mocks and clean up afterwards."""
    register_strategy(VectorizedMockStrategy)
    register_strategy(LookaheadVectorizedStrategy)
    yield
    unregister_strategy("vec_mock")
    unregister_strategy("lookahead_mock")


def generate_mock_data(
    periods: int = 10, tz_naive: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate sample timezone-aware dataframes for testing."""
    tz = None if tz_naive else UTC
    idx = pd.date_range("2026-06-16T12:00:00", periods=periods, freq="h", tz=tz)

    df_data = pd.DataFrame(index=idx)
    df_data["close"] = np.linspace(1.1000, 1.1100, periods)

    df_ind = pd.DataFrame(index=idx)
    # 0 = no signal, 1 = buy, -1 = sell
    df_ind["signal_val"] = [0, 0, 1, 0, -1, 0, 1, 0, 0, 0]

    return df_data, df_ind


def test_vectorized_signals_success():
    """Verify that vectorized execution runs successfully and shifts indicators."""
    df_data, df_ind = generate_mock_data()

    ref = StrategyRefInput(strategy_id="vec_mock", environment="BACKTEST")
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 16, 22, 0, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="seed",
        request_id="req-123",
        correlation_id="corr-123",
    )

    res = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=df_data,
        indicators=df_ind,
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        context=ctx,
        config={"mock_alpha": "0.1"},
    )

    assert res["status"] == "success"
    intents = res["data"]["trade_intents"]
    # 3 signals in df_ind (indices 2, 4, 6)
    # The indicators are shifted by 1 row before calculation.
    # Original indexes:
    # idx 2: 14:00 (BUY) -> shifts to 15:00
    # idx 4: 16:00 (SELL) -> shifts to 17:00
    # idx 6: 18:00 (BUY) -> shifts to 19:00
    assert len(intents) == 3
    assert intents[0].side == "BUY"
    assert intents[1].side == "SELL"


def test_timing_policy_validation():
    """Verify unsupported timing policy fails."""
    df_data, df_ind = generate_mock_data()
    ref = StrategyRefInput(strategy_id="vec_mock", environment="BACKTEST")

    res = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=df_data,
        indicators=df_ind,
        timing_policy="INTRABAR_EVENT",
    )
    assert res["status"] == "error"
    assert res["error"]["code"] == "STRATEGY_UNSUPPORTED_TIMING_POLICY"


def test_lookahead_risk_detection():
    """Verify lookahead risk throws STRATEGY_LOOKAHEAD_DETECTED."""
    df_data, df_ind = generate_mock_data()
    ref = StrategyRefInput(strategy_id="lookahead_mock", environment="BACKTEST")
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 16, 22, 0, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="seed",
        request_id="req-123",
        correlation_id="corr-123",
    )

    res = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=df_data,
        indicators=df_ind,
        context=ctx,
    )
    assert res["status"] == "error"
    assert res["error"]["code"] == "STRATEGY_LOOKAHEAD_DETECTED"


def test_timezone_naive_fails():
    """Verify timezone naive dataframes fail input quality check."""
    df_data, df_ind = generate_mock_data(tz_naive=True)
    ref = StrategyRefInput(strategy_id="vec_mock", environment="BACKTEST")

    res = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=df_data,
        indicators=df_ind,
    )
    assert res["status"] == "error"
    assert res["error"]["code"] == "STRATEGY_INTERNAL_ERROR"


def test_stale_data_latency():
    """Verify max_data_latency_tolerance triggers STRATEGY_STALE_DATA."""
    df_data, df_ind = generate_mock_data()
    ref = StrategyRefInput(strategy_id="vec_mock", environment="BACKTEST")

    # decision timestamp is 2026-06-16 23:00. Last bar timestamp is 2026-06-16 21:00.
    # Difference is 2 hours. Limit is 2 hours.
    # Let's set decision to 2026-06-16 23:01 (exceeds limit)
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 16, 23, 1, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="seed",
        request_id="req-123",
        correlation_id="corr-123",
    )

    res = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=df_data,
        indicators=df_ind,
        context=ctx,
    )
    assert res["status"] == "error"
    assert res["error"]["code"] == "STRATEGY_STALE_DATA"


def test_alpha_and_cost_suppression():
    """Verify expected alpha and cost thresholds suppress intents."""
    df_data, df_ind = generate_mock_data()
    ref = StrategyRefInput(strategy_id="vec_mock", environment="BACKTEST")
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 16, 22, 0, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="seed",
        request_id="req-123",
        correlation_id="corr-123",
    )

    # 1. Thresholds block (min alpha 0.15, mock alpha is 0.1)
    res_suppressed = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=df_data,
        indicators=df_ind,
        context=ctx,
        config={"min_expected_alpha": 0.15, "mock_alpha": "0.10"},
    )
    assert res_suppressed["status"] == "success"
    # No intents emitted
    assert len(res_suppressed["data"]["trade_intents"]) == 0
    assert res_suppressed["data"]["diagnostics"]["status"] == "suppressed"

    # 2. Transaction cost blocks
    res_cost = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=df_data,
        indicators=df_ind,
        context=ctx,
        config={"max_acceptable_transaction_cost": 0.005, "mock_cost": "0.01"},
    )
    assert len(res_cost["data"]["trade_intents"]) == 0
