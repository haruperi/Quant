# ruff: noqa: E501, RUF012, ARG002, DTZ003, RUF100
"""Unit tests for event-driven stateful strategy execution and checkpoints."""

from datetime import datetime

import pytest
from app.services.strategies import (
    StrategyCheckpointIncompatibleError,
    StrategyCheckpointInvalidError,
    StrategyExecutionContext,
    StrategyHardKilledError,
    create_state_checkpoint,
    run_strategy_hook,
    validate_and_restore_checkpoint,
)


class StatefulMockStrategy:
    """Mock stateful strategy class with mutable variables."""

    strategy_id = "stateful_mock"
    version = "1.0.0"

    def __init__(self) -> None:
        self.counter = 0
        self.last_symbol = ""

    def on_init(self, context, config):
        return {"state_updates": {"counter": 0}}

    def on_bar(self, bar, context, config):
        self.counter += 1
        self.last_symbol = bar.get("symbol", "")
        if bar.get("fail", False):
            raise RuntimeError("Simulation failure in on_bar")
        return {
            "trade_intents": [],
            "state_updates": {"counter": self.counter, "last_symbol": self.last_symbol},
        }

    def on_slow_hook(self, context, config):
        import time

        time.sleep(0.15)  # block longer than timeout budget
        return {}


def test_event_hook_success():
    """Verify that successful event hook execution mutates strategy state."""
    strat = StatefulMockStrategy()
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime.utcnow(),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="seed",
        request_id="req-1",
        correlation_id="corr-1",
    )
    config = {"param": 42}

    res = run_strategy_hook(
        strategy_instance=strat,
        hook_name="on_bar",
        payload={"symbol": "EURUSD"},
        read_only_state=None,
        context=ctx,
        config=config,
    )

    assert res["status"] == "success"
    assert strat.counter == 1
    assert strat.last_symbol == "EURUSD"
    assert res["data"]["state_updates"]["counter"] == 1


def test_event_hook_atomic_rollback():
    """Verify state rollback occurs if a hook execution fails (REQ-STRAT-094)."""
    strat = StatefulMockStrategy()
    strat.counter = 10
    strat.last_symbol = "GBPUSD"

    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime.utcnow(),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="seed",
        request_id="req-1",
        correlation_id="corr-1",
    )

    # Call on_bar with fail=True payload
    res = run_strategy_hook(
        strategy_instance=strat,
        hook_name="on_bar",
        payload={"symbol": "EURUSD", "fail": True},
        read_only_state=None,
        context=ctx,
        config={},
    )

    assert res["status"] == "error"
    # State must be rolled back to original values!
    assert strat.counter == 10
    assert strat.last_symbol == "GBPUSD"


def test_event_hook_timeout():
    """Verify that exceeding latency budget returns a StrategyTimeoutError (REQ-STRAT-344)."""
    strat = StatefulMockStrategy()
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime.utcnow(),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="seed",
        request_id="req-1",
        correlation_id="corr-1",
    )

    # Set timeout limit lower than sleep duration (timeout = 0.05s)
    res = run_strategy_hook(
        strategy_instance=strat,
        hook_name="on_slow_hook",
        payload={},
        read_only_state=None,
        context=ctx,
        config={},
        timeout_seconds=0.05,
    )

    assert res["status"] == "error"
    assert (
        res["error"]["code"] == "STRATEGY_TIMEOUT"
    )  # mapped from timeout limit exceeded


def test_hard_kill_signal():
    """Verify hard kill signal raises StrategyHardKilledError (REQ-STRAT-188)."""
    strat = StatefulMockStrategy()
    ctx = StrategyExecutionContext(
        environment="BACKTEST",
        decision_timestamp=datetime.utcnow(),
        timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
        seed_material="seed",
        request_id="req-1",
        correlation_id="corr-1",
        resource_budget_ref="HARD_KILL",
    )

    with pytest.raises(StrategyHardKilledError):
        run_strategy_hook(
            strategy_instance=strat,
            hook_name="on_bar",
            payload={"symbol": "EURUSD"},
            read_only_state=None,
            context=ctx,
            config={},
        )


def test_state_checkpoint_lifecycle():
    """Verify checkpoint serialization, checksum matching, and validation (REQ-STRAT-184, REQ-STRAT-185)."""
    config = {"fast": 10}
    state_payload = {"position_size": 1.5, "avg_price": 1.1020}

    # 1. Create checkpoint
    checkpoint = create_state_checkpoint(
        strategy_id="mystrat",
        version="1.0.0",
        config=config,
        payload=state_payload,
    )

    assert checkpoint.strategy_id == "mystrat"
    assert checkpoint.version == "1.0.0"

    # 2. Restore checkpoint successfully
    restored = validate_and_restore_checkpoint(
        checkpoint=checkpoint,
        strategy_id="mystrat",
        version="1.0.0",
        config=config,
    )
    assert restored == state_payload

    # 3. Check compatibility mismatch (strategy ID)
    with pytest.raises(StrategyCheckpointIncompatibleError):
        validate_and_restore_checkpoint(
            checkpoint=checkpoint,
            strategy_id="different_strat",
            version="1.0.0",
            config=config,
        )

    # 4. Check compatibility mismatch (config changed)
    with pytest.raises(StrategyCheckpointIncompatibleError):
        validate_and_restore_checkpoint(
            checkpoint=checkpoint,
            strategy_id="mystrat",
            version="1.0.0",
            config={"fast": 12},  # config changed
        )

    # 5. Check invalid checksum (data corruption)
    checkpoint_corrupted = checkpoint.model_copy()
    checkpoint_corrupted.payload["position_size"] = 99.9  # corrupt data
    with pytest.raises(StrategyCheckpointInvalidError):
        validate_and_restore_checkpoint(
            checkpoint=checkpoint_corrupted,
            strategy_id="mystrat",
            version="1.0.0",
            config=config,
        )
