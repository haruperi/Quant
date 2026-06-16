"""Usage examples for the HaruQuantAI strategy service.

Demonstrates registry validation, vectorized trend strategy execution, stateful
event hook processing, atomic state rollback on failure, state checkpoints,
and configuration security injection vetting checks.
"""

# ruff: noqa: E501, E402, NPY002, RUF012, ARG002
import sys
from pathlib import Path

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[4])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

import numpy as np
import pandas as pd
from app.services.strategies import (
    ReadOnlyExecutionStateSnapshot,
    StrategyExecutionContext,
    StrategyRefInput,
    StrategyRiskProfile,
    StrategySide,
    TradeIntent,
    create_state_checkpoint,
    list_strategies,
    register_strategy,
    run_strategy_hook,
    run_vectorized_strategy_signals,
    validate_and_restore_checkpoint,
    validate_strategy_config,
    validate_strategy_ref,
    vet_and_sandbox_code,
)
from app.utils.errors import (
    SimArbitraryCodeRejectedError,
    StrategyError,
)
from pydantic import BaseModel, Field

# --- Mock Vectorized Trend Strategy ---


class EmaTrendConfig(BaseModel):
    """Pydantic config model for EMA Trend Strategy."""

    fast_ema_period: int = Field(10, ge=1)
    slow_ema_period: int = Field(20, ge=1)


class EmaTrendStrategy:
    """Mock vectorized EMA crossover strategy conforming to StrategyProtocol."""

    strategy_id = "ema_trend_v1"
    version = "1.0.0"
    lifecycle_status = "BACKTEST_APPROVED"
    permitted_environments = ["BACKTEST", "REPLAY"]
    config_schema = {"type": "object"}
    config_model = EmaTrendConfig
    risk_profile = StrategyRiskProfile(max_gross_exposure=Decimal("150000.00"))
    max_data_latency_tolerance = pd.Timedelta(hours=2)
    min_expected_alpha = 0.02
    max_acceptable_transaction_cost = 0.05

    def run_vectorized_signals(
        self,
        data: pd.DataFrame,
        indicators: pd.DataFrame,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> list[TradeIntent]:
        """Generate signals when close exceeds fast/slow EMA threshold."""
        intents = []

        # Simple crossover logic
        # Buy if price is above fast EMA and fast EMA is above slow EMA
        # Indicators dataframe has already been shifted N-1 to avoid lookahead.
        for idx, row in data.iterrows():
            ts = idx if isinstance(idx, pd.Timestamp) else idx[1]
            close = row["close"]

            # Mock calculation of EMA based on shift index for simplicity
            fast_ema = (
                close * 0.995 if idx < data.index[len(data) // 2] else close * 1.005
            )
            slow_ema = (
                close * 0.990 if idx < data.index[len(data) // 2] else close * 1.010
            )

            # Signal triggers
            side: StrategySide = "HOLD"
            if close > fast_ema > slow_ema:
                side = "BUY"
            elif close < fast_ema < slow_ema:
                side = "SELL"

            if side in ("BUY", "SELL"):
                # Sizing metadata guides the simulation module
                lineage = {
                    "expected_alpha": "0.03",  # exceeds min_expected_alpha 0.02
                    "estimated_transaction_cost": "0.01",  # below max cost 0.05
                    "source": "vectorized_run",
                }

                intents.append(
                    TradeIntent(
                        intent_id=f"intent-ema-{ts.strftime('%Y%m%d%H%M%S')}",
                        decision_id=f"decision-ema-{ts.strftime('%Y%m%d%H%M%S')}",
                        idempotency_key=f"idem-ema-{ts.strftime('%Y%m%d%H%M%S')}",
                        strategy_id=self.strategy_id,
                        strategy_version=self.version,
                        symbol="EURUSD",
                        side=side,
                        intent_type="OPEN",
                        signal_timestamp=ts,
                        decision_timestamp=ts + pd.Timedelta(hours=1),
                        allow_partial_fills=True,
                        min_fill_size=Decimal("0.01"),
                        lineage=lineage,
                    )
                )

        return intents


# --- Mock Stateful Recovery Event Strategy ---


class RecoveryStatefulStrategy:
    """Mock stateful event strategy responding to custom transaction and bar events."""

    strategy_id = "recovery_v1"
    version = "1.0.0"
    lifecycle_status = "BACKTEST_APPROVED"
    permitted_environments = ["BACKTEST", "REPLAY"]
    config_schema = None
    config_model = None
    risk_profile = None

    def run_vectorized_signals(
        self,
        data: pd.DataFrame,
        indicators: pd.DataFrame,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> list[TradeIntent]:
        """Stateful strategies do not use vectorized signals in this demo."""
        return []

    def __init__(self) -> None:
        self.deals_processed = 0
        self.recovery_level = 0
        self.last_deal_side = "HOLD"

    def on_init(
        self, context: StrategyExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Initialize local state parameters."""
        self.deals_processed = 0
        self.recovery_level = 0
        self.last_deal_side = "HOLD"
        return {"state_updates": {"deals_processed": 0, "recovery_level": 0}}

    def on_fill_update(
        self,
        fill_event: dict[str, Any],
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Progress recovery level based on deal fills and state snapshots."""
        self.deals_processed += 1
        side = fill_event.get("side", "BUY")
        self.last_deal_side = side

        # Martingale levels increment on loss deal
        is_loss = fill_event.get("profit", 0.0) < 0.0
        if is_loss:
            self.recovery_level += 1
        else:
            self.recovery_level = max(0, self.recovery_level - 1)

        # Potential error injection check
        if fill_event.get("force_failure", False):
            raise RuntimeError("Database error during fill logging")

        return {
            "state_updates": {
                "deals_processed": self.deals_processed,
                "recovery_level": self.recovery_level,
                "last_deal_side": self.last_deal_side,
            }
        }


# --- Setup Helper ---


def generate_ohlcv_sample(rows: int = 10) -> pd.DataFrame:
    """Generate mock timezone-aware price dataframe."""
    start_time = datetime(2026, 6, 16, 10, 0, 0, tzinfo=UTC)
    timestamps = [start_time + timedelta(hours=i) for i in range(rows)]

    np.random.seed(42)
    close_prices = np.cumprod(1.0 + np.random.normal(0, 0.005, rows)) * 1.1200
    df = pd.DataFrame(
        {
            "open": close_prices * 0.999,
            "high": close_prices * 1.002,
            "low": close_prices * 0.998,
            "close": close_prices,
            "volume": np.random.randint(100, 500, rows).astype(float),
            "symbol": ["EURUSD"] * rows,
        },
        index=pd.DatetimeIndex(timestamps, name="timestamp"),
    )
    return df


# --- Demos ---


def demo_registry_and_validation() -> None:
    """Demonstrates registry checks, versioning constraints, and lifecycle validation."""
    print("\n--- 1. Registry & Reference Validation Demo ---")

    # 1. Register strategies
    register_strategy(cast("Any", EmaTrendStrategy))
    register_strategy(cast("Any", RecoveryStatefulStrategy))
    print(f"Registered Strategies: {list_strategies()}")

    # 2. Validate reference constraints
    # Under BACKTEST, EMA Trend (RESEARCH/APPROVED) is validated
    res_valid = validate_strategy_ref(
        strategy_id="ema_trend_v1",
        version_constraint=">=1.0.0,<2.0.0",
        environment="BACKTEST",
        request_id="req-validation-001",
    )
    print(f"Validation Ref Status: {res_valid['status']}")
    if res_valid["status"] == "success":
        ref = res_valid["data"]["strategy_ref"]
        print(f"Resolved Ref strategy_id: {ref.strategy_id} version: {ref.version}")

    # 3. Validation failure environment permissions (e.g. executing in unpermitted LIVE)
    res_invalid_env = validate_strategy_ref(
        strategy_id="ema_trend_v1",
        environment="LIVE",
    )
    print(f"LIVE Validation Status (Expected Error): {res_invalid_env['status']}")
    print(f"Error Code: {res_invalid_env['error']['code']}")


def demo_vectorized_signal_execution() -> None:
    """Demonstrates running vectorized strategies with shifted lookahead checks and stale data detection."""
    print("\n--- 2. Vectorized Signal Generation Demo ---")

    data = generate_ohlcv_sample(10)
    # Mock indicator outputs
    indicators = pd.DataFrame(index=data.index)
    indicators["signal_val"] = 0.0

    ref = StrategyRefInput(strategy_id="ema_trend_v1", environment="BACKTEST")
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 16, 21, 0, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="test_seed",
        request_id="req-vector-001",
        correlation_id="corr-vector-001",
    )

    # 1. Successful run
    res = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=data,
        indicators=indicators,
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        context=ctx,
        config={"fast_ema_period": 10, "slow_ema_period": 20},
    )
    print(f"Vectorized Run Status: {res['status']}")
    print(f"Number of generated TradeIntents: {len(res['data']['trade_intents'])}")

    # 2. Stale data latency limit breach (last bar is 2026-06-16 19:00, decision is 2026-06-16 23:00 -> diff 4h > 2h limit)
    ctx_stale = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime(2026, 6, 16, 23, 0, tzinfo=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="test_seed",
        request_id="req-stale-002",
        correlation_id="corr-stale-002",
    )
    res_stale = run_vectorized_strategy_signals(
        strategy_ref=ref,
        market_data=data,
        indicators=indicators,
        context=ctx_stale,
    )
    print(f"Stale Run Status (Expected Error): {res_stale['status']}")
    print(f"Error Code: {res_stale['error']['code']}")


def demo_stateful_event_hook_execution() -> None:
    """Demonstrates executing hook methods, atomic state rollback on error, and checkpoint validation."""
    print("\n--- 3. Stateful Event Hooks & Checkpoint Demo ---")

    strat = RecoveryStatefulStrategy()
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime.now(tz=UTC),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="seed",
        request_id="req-hook-001",
        correlation_id="corr-hook-001",
    )

    # 1. Success execution
    fill_payload = {"side": "BUY", "profit": -15.50}  # a loss deal
    res = run_strategy_hook(
        strategy_instance=strat,
        hook_name="on_fill_update",
        payload=fill_payload,
        read_only_state=None,
        context=ctx,
        config={},
    )
    print(f"First hook status: {res['status']}")
    print(f"Strategy recovery_level state: {strat.recovery_level}")

    # 2. Re-execution with error (atomic rollback check)
    # The recovery level is currently 1.
    # We call on_fill_update again with force_failure=True. It will raise RuntimeError.
    res_err = run_strategy_hook(
        strategy_instance=strat,
        hook_name="on_fill_update",
        payload={"side": "BUY", "profit": -10.00, "force_failure": True},
        read_only_state=None,
        context=ctx,
        config={},
    )
    print(f"Second hook status (Expected Error): {res_err['status']}")
    print(f"Error Code: {res_err['error']['code']}")
    # Assert state did not corrupt (reverted back to 1)
    print(
        f"Strategy recovery_level after rollback: {strat.recovery_level} (Expected: 1)"
    )

    # 3. Checkpointing and restoration
    checkpoint = create_state_checkpoint(
        strategy_id="recovery_v1",
        version="1.0.0",
        config={},
        payload={
            "deals_processed": strat.deals_processed,
            "recovery_level": strat.recovery_level,
        },
    )
    print(f"Checkpoint Checksum: {checkpoint.checksum}")

    restored_payload = validate_and_restore_checkpoint(
        checkpoint=checkpoint,
        strategy_id="recovery_v1",
        version="1.0.0",
        config={},
    )
    print(f"Restored Checkpoint Payload: {restored_payload}")


def demo_security_vetting() -> None:
    """Demonstrates configuration security checks and arbitrary code injection rejections."""
    print("\n--- 4. Configuration Security Vetting Demo ---")

    # 1. Configuration injection check
    unsafe_config = {
        "fast_ema_period": 10,
        "slow_ema_period": 20,
        "malicious_eval": 'eval(\'__import__("os").system("whoami")\')',
    }

    try:
        validate_strategy_config(cast("Any", EmaTrendStrategy), unsafe_config)
    except StrategyError as exc:
        print(f"Caught expected security config exception (code={exc.code}): {exc}")

    # 2. Dynamic Python string code execution rejection
    try:
        vet_and_sandbox_code("print('Executing arbitrary injected code!')")
    except SimArbitraryCodeRejectedError as exc:
        print(f"Caught expected sandboxing exception (code={exc.code}): {exc}")


if __name__ == "__main__":
    print("==================================================")
    print("STARTING STRATEGY SERVICE USAGE DEMO (04_strategy.py)")
    print("==================================================")

    demo_registry_and_validation()
    demo_vectorized_signal_execution()
    demo_stateful_event_hook_execution()
    demo_security_vetting()

    print("==================================================")
    print("DEMO SCRIPT EXECUTED SUCCESSFULLY")
    print("==================================================")
