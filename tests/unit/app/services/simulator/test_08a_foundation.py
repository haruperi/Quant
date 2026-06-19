"""Unit tests for simulator 08A foundation contracts."""

from __future__ import annotations

import importlib
from collections.abc import Mapping

import pytest
from app.services.simulator import (
    CommissionModel,
    DeterministicJournal,
    EventDrivenExecutionEngine,
    FixedLiquidityModel,
    FixedSlippageModel,
    FixedSpreadModel,
    MarginModel,
    SimulatorActorContext,
    SimulatorBacktestRequestV1,
    SimulatorExecutionProvider,
    SimulatorSymbolSpec,
    SimulatorTick,
    SwapModel,
    build_markdown_report,
    is_non_fatal_diagnostic,
    run_backtest,
)
from app.services.simulator.journal import JsonlJournal
from app.services.simulator.validation import (
    parse_backtest_request,
    validate_tick_records,
)
from app.utils.errors import ValidationError
from app.utils.standard import validate_standard_response


def _payload() -> dict[str, object]:
    return {
        "request_id": "req_test_08a",
        "actor_context": {"actor_id": "local-builder", "roles": ["researcher"]},
        "strategy_ref": "trend_following",
        "strategy_config": {"short_window": 5, "long_window": 10},
        "symbols": ["EURUSD"],
        "timeframe": "M1",
        "start": "2026-01-01T00:00:00Z",
        "end": "2026-01-01T01:00:00Z",
        "initial_balance": 100000.0,
    }


def _mapping_value(payload: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = payload[key]
    assert isinstance(value, Mapping)
    return value


def _data(response: Mapping[str, object]) -> Mapping[str, object]:
    return _mapping_value(response, "data")


def _error(response: Mapping[str, object]) -> Mapping[str, object]:
    return _mapping_value(response, "error")


def test_run_backtest_success_envelope_is_deterministic() -> None:
    """Verify official tool envelope and deterministic run ids."""
    first = run_backtest(_payload())
    second = run_backtest(_payload())

    validate_standard_response(first)
    validate_standard_response(second)
    assert first["status"] == "success"
    assert second["status"] == "success"
    assert isinstance(first["data"], dict)
    assert isinstance(second["data"], dict)
    first_data = _data(first)
    second_data = _data(second)
    first_metrics = _mapping_value(first_data, "summary_metrics")
    first_result = _mapping_value(first_data, "result")
    first_artifacts = _mapping_value(first_data, "artifacts")
    first_journal = _mapping_value(first_artifacts, "journal")
    first_metadata = _mapping_value(first_data, "metadata")
    assert first_data["run_id"] == second_data["run_id"]
    assert first_metrics["ending_balance"] == 100000.0
    assert first_data["status"] == "success"
    assert first_data["request_id"] == "req_test_08a"
    assert first_data["error"] is None
    assert first_data["warnings"] == []
    assert first_result["run_id"] == first_data["run_id"]
    assert first_journal["run_id"] == first_data["run_id"]
    assert first_metadata["pipeline"] == [
        "validated",
        "data_quality_checked",
        "signals_planned",
        "ticks_planned",
        "executed",
        "metrics_collected",
        "reporting_ready",
    ]


def test_run_backtest_rejects_raw_strategy_code() -> None:
    """Verify arbitrary strategy code is blocked before execution."""
    payload = _payload()
    payload["strategy_config"] = {"source": "def run():\n    return 1"}

    response = run_backtest(payload)

    validate_standard_response(response)
    assert response["status"] == "error"
    assert response["error"] == {
        "code": "SIM_ARBITRARY_CODE_REJECTED",
        "details": "Raw arbitrary Python strategy code is not accepted.",
    }


def test_run_backtest_orchestrator_control_envelopes() -> None:
    """Verify queued, cancelled, and diagnostic-failed simulator payloads."""
    queued_payload = _payload()
    queued_payload["metadata"] = {"service_mode": True, "workers_saturated": True}
    queued = run_backtest(queued_payload)

    cancelled_payload = _payload()
    cancelled_payload["metadata"] = {"cancel_requested": True}
    cancelled = run_backtest(cancelled_payload)

    diagnostic_payload = _payload()
    diagnostic_payload["metadata"] = {
        "diagnostic_mode": True,
        "force_diagnostic_failure": True,
    }
    diagnostic = run_backtest(diagnostic_payload)

    for response in (queued, cancelled, diagnostic):
        validate_standard_response(response)
        assert response["status"] == "success"
        assert isinstance(response["data"], dict)
        data = _data(response)
        run_id = data["run_id"]
        assert data["result"] is None
        assert isinstance(run_id, str)
        assert run_id.startswith("simrun_")

    queued_data = _data(queued)
    queued_metadata = _mapping_value(queued_data, "metadata")
    queued_queue = _mapping_value(queued_metadata, "queue")
    queued_retry = _mapping_value(queued_metadata, "retry")
    diagnostic_data = _data(diagnostic)
    diagnostic_error = _mapping_value(diagnostic_data, "error")
    assert queued_data["status"] == "queued"
    assert queued_queue["queue_position"] == 1
    assert queued_retry["retry_after_seconds"] == 1
    assert _data(cancelled)["status"] == "cancelled"
    assert diagnostic_data["status"] == "diagnostic_failed"
    assert diagnostic_error["code"] == "SIM_DATA_QUALITY_FAILED"


def test_run_backtest_orchestrator_fail_closed_boundaries() -> None:
    """Verify registry, sandbox, checkpoint, and artifact failures."""
    missing_strategy = _payload()
    missing_strategy["strategy_ref"] = "missing_strategy"
    missing_response = run_backtest(missing_strategy)
    assert missing_response["status"] == "error"
    assert _error(missing_response)["code"] == "SIM_INVALID_CONFIG"

    code_mode = _payload()
    code_mode["metadata"] = {"strategy_input_mode": "code"}
    code_response = run_backtest(code_mode)
    assert code_response["status"] == "error"
    assert _error(code_response)["code"] == "SIM_ARBITRARY_CODE_REJECTED"

    checkpoint = _payload()
    checkpoint["metadata"] = {
        "resume_from_checkpoint": "checkpoint_1",
        "checkpoint_compatible": False,
    }
    checkpoint_response = run_backtest(checkpoint)
    assert checkpoint_response["status"] == "error"
    assert _error(checkpoint_response)["code"] == "SIM_CHECKPOINT_INCOMPATIBLE"

    artifact_path = _payload()
    artifact_path["artifact_root_ref"] = "../outside"
    artifact_response = run_backtest(artifact_path)
    assert artifact_response["status"] == "error"
    assert _error(artifact_response)["code"] == "SIM_INVALID_CONFIG"

    bad_metadata = _payload()
    bad_metadata["metadata"] = "bad"
    metadata_response = run_backtest(bad_metadata)
    assert metadata_response["status"] == "error"
    assert _error(metadata_response)["code"] == "VALIDATION_FAILED"


def test_run_backtest_payload_size_limit() -> None:
    """Verify oversized simulator requests are rejected before execution."""
    payload = _payload()
    payload["metadata"] = {"large": "x" * 70000}

    response = run_backtest(payload)

    validate_standard_response(response)
    assert response["status"] == "error"
    assert _error(response)["code"] == "SIM_INVALID_CONFIG"


def test_models_are_deterministic_and_validate_boundaries() -> None:
    """Verify cost, spread, slippage, liquidity, swap, and margin models."""
    spread = FixedSpreadModel(spread_points=10, point=0.00001)
    tick = spread.build_tick(
        timestamp="2026-01-01T00:00:00Z",
        symbol="EURUSD",
        mid_price=1.1,
    )
    assert tick.bid == 1.09995
    assert tick.ask == 1.10005

    liquidity = FixedLiquidityModel(max_volume_per_tick=0.5).fill(
        1.0, time_in_force="IOC"
    )
    assert liquidity.filled_volume == 0.5
    assert liquidity.diagnostic_code == "SIM_IOC_REMAINDER_CANCELLED"
    assert is_non_fatal_diagnostic("SIM_IOC_REMAINDER_CANCELLED") is True
    assert is_non_fatal_diagnostic("SIM_INTERNAL_ERROR") is False

    slippage = FixedSlippageModel(slippage_points=2, point=0.00001).apply(
        side="buy",
        expected_price=1.1,
        executable_price=1.10005,
        filled_volume=0.5,
    )
    assert slippage.final_price == 1.10007
    assert CommissionModel(amount_per_lot=7).calculate(0.5) == 3.5
    assert (
        SwapModel(long_per_lot_per_day=-2).calculate(
            side="buy", volume=1.0, days_held=2
        )
        == -4.0
    )
    assert (
        MarginModel(leverage=100).calculate(contract_size=100000, volume=1.0, price=1.1)
        == 1100.0
    )


def test_journal_manifest_and_replay_hash_chain() -> None:
    """Verify journal sequence, hash chain, and manifest metadata."""
    journal = DeterministicJournal(
        run_id="simrun_test",
        config_hash="id_config",
        data_manifest_hash="id_data",
        engine_version="test",
    )

    first = journal.append("simulator.started", {"request_id": "req_1"})
    second = journal.append("simulator.completed", {"status": "success"})
    manifest = journal.manifest()

    assert first.sequence == 1
    assert second.previous_hash == first.record_hash
    assert manifest.last_sequence == 2
    assert journal.replay_payload()[0]["event_type"] == "simulator.started"


def test_engine_result_and_markdown_report() -> None:
    """Verify engine result contains report-ready disclosure fields."""
    request = SimulatorBacktestRequestV1(
        request_id="req_engine",
        actor_context=SimulatorActorContext(actor_id="tester"),
        strategy_ref="trend_following",
        symbols=("EURUSD",),
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
    )

    result = EventDrivenExecutionEngine().run(request).to_dict()
    report = build_markdown_report(result)

    assert result["broker_profile_id"] == "mt5_demo_reference_fx_v1"
    assert "08A foundation result only" in report


def test_simulator_import_has_no_runtime_side_effects() -> None:
    """Verify public import is lightweight and exposes expected facade."""
    module = importlib.import_module("app.services.simulator")

    assert hasattr(module, "run_backtest")
    assert hasattr(module, "SimulatorExecutionProvider")


def test_execution_provider_constructs_without_external_clients() -> None:
    """Verify adapter can be created without broker credentials or network clients."""
    provider = SimulatorExecutionProvider()

    assert provider.client is not None


def test_invalid_model_boundaries_raise_deterministic_errors() -> None:
    """Verify invalid model inputs fail closed."""
    with pytest.raises(ValidationError):
        FixedSpreadModel(spread_points=-1)
    with pytest.raises(ValidationError):
        FixedSpreadModel(point=0)
    with pytest.raises(ValidationError):
        FixedSpreadModel().build_tick(
            timestamp="2026-01-01T00:00:00Z",
            symbol="EURUSD",
            mid_price=0,
        )
    with pytest.raises(ValidationError):
        CommissionModel(amount_per_lot=-1)
    with pytest.raises(ValidationError):
        CommissionModel(currency="")
    with pytest.raises(ValidationError):
        CommissionModel().calculate(-1)
    with pytest.raises(ValidationError):
        MarginModel(leverage=0)
    with pytest.raises(ValidationError):
        MarginModel().calculate(contract_size=0, volume=1, price=1)
    with pytest.raises(ValidationError):
        FixedSlippageModel(slippage_points=-1)
    with pytest.raises(ValidationError):
        FixedSlippageModel().apply(
            side="hold",  # type: ignore[arg-type]
            expected_price=1,
            executable_price=1,
            filled_volume=1,
        )
    with pytest.raises(ValidationError):
        SwapModel().calculate(side="flat", volume=1, days_held=1)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        FixedLiquidityModel(max_volume_per_tick=0)
    with pytest.raises(ValidationError):
        FixedLiquidityModel().fill(0)


def test_invalid_tick_and_request_boundaries_raise() -> None:
    """Verify request and tick models validate boundary fields."""
    with pytest.raises(ValidationError):
        SimulatorTick(
            timestamp="2026-01-01T00:00:00Z",
            symbol="",
            bid=1.0,
            ask=1.1,
        )
    with pytest.raises(ValidationError):
        SimulatorTick(
            timestamp="2026-01-01T00:00:00Z",
            symbol="EURUSD",
            bid=1.2,
            ask=1.1,
        )
    with pytest.raises(ValidationError):
        SimulatorTick(
            timestamp="2026-01-01T00:00:00Z",
            symbol="EURUSD",
            bid=1.0,
            ask=1.1,
            volume=-1,
        )
    with pytest.raises(ValidationError):
        SimulatorTick(
            timestamp="2026-01-01T00:00:00Z",
            symbol="EURUSD",
            bid=1.0,
            ask=1.1,
            spread_points=-1,
        )
    with pytest.raises(ValidationError):
        SimulatorActorContext(actor_id="")
    with pytest.raises(ValidationError):
        SimulatorActorContext(actor_id="tester", roles=("",))
    with pytest.raises(ValidationError):
        SimulatorSymbolSpec(symbol="")
    with pytest.raises(ValidationError):
        SimulatorSymbolSpec(symbol="EURUSD", point=0)
    with pytest.raises(ValidationError):
        SimulatorSymbolSpec(symbol="EURUSD", lot_min=2, lot_max=1)
    with pytest.raises(ValidationError):
        SimulatorBacktestRequestV1(
            request_id="",
            actor_context=SimulatorActorContext(actor_id="tester"),
            strategy_ref="trend_following",
            symbols=("EURUSD",),
            timeframe="M1",
            start="2026-01-01T00:00:00Z",
            end="2026-01-01T01:00:00Z",
        )
    with pytest.raises(ValidationError):
        SimulatorBacktestRequestV1(
            request_id="req_bad",
            actor_context=SimulatorActorContext(actor_id="tester"),
            strategy_ref="trend_following",
            symbols=("EURUSD",),
            timeframe="M1",
            start="2026-01-02T00:00:00Z",
            end="2026-01-01T01:00:00Z",
        )
    with pytest.raises(ValidationError):
        SimulatorBacktestRequestV1(
            request_id="req_bad",
            actor_context=SimulatorActorContext(actor_id="tester"),
            strategy_ref="",
            symbols=("EURUSD",),
            timeframe="M1",
            start="2026-01-01T00:00:00Z",
            end="2026-01-01T01:00:00Z",
        )
    with pytest.raises(ValidationError):
        SimulatorBacktestRequestV1(
            request_id="req_bad",
            actor_context=SimulatorActorContext(actor_id="tester"),
            strategy_ref="trend_following",
            symbols=("",),
            timeframe="M1",
            start="2026-01-01T00:00:00Z",
            end="2026-01-01T01:00:00Z",
        )
    with pytest.raises(ValidationError):
        SimulatorBacktestRequestV1(
            request_id="req_bad",
            actor_context=SimulatorActorContext(actor_id="tester"),
            strategy_ref="trend_following",
            symbols=("EURUSD",),
            timeframe="M1",
            start="2026-01-01T00:00:00Z",
            end="2026-01-01T01:00:00Z",
            initial_balance=0,
        )


def test_schema_and_quality_validation_edges() -> None:
    """Verify schema and quality gates report deterministic failures."""
    payload = _payload()
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        parse_backtest_request(payload)

    no_actor = _payload()
    no_actor["actor_context"] = "bad"
    with pytest.raises(ValidationError):
        parse_backtest_request(no_actor)

    no_symbols = _payload()
    no_symbols["symbols"] = "EURUSD"
    with pytest.raises(ValidationError):
        parse_backtest_request(no_symbols)

    empty_issues = validate_tick_records([])
    assert empty_issues[0]["code"] == "SIM_DATA_EMPTY"

    issues = validate_tick_records(
        [{"timestamp": "2026-01-01T00:00:00Z", "symbol": "GBPUSD", "bid": 2, "ask": 1}],
        expected_symbol="EURUSD",
    )
    assert {issue["code"] for issue in issues} == {
        "SIM_INVALID_PRICE",
        "SIM_MISSING_SYMBOL",
    }


def test_jsonl_journal_persists_manifest(tmp_path) -> None:
    """Verify JSONL journal writes records and manifest when explicitly requested."""
    journal = JsonlJournal(
        artifact_root=tmp_path,
        run_id="simrun_jsonl",
        config_hash="id_config",
        data_manifest_hash="id_data",
        engine_version="test",
    )

    journal.append("simulator.persisted", {"status": "success"})
    manifest = journal.write_manifest()

    assert manifest.last_sequence == 1
    assert (tmp_path / "journal.jsonl").exists()
    assert (tmp_path / "journal_manifest.json").exists()
