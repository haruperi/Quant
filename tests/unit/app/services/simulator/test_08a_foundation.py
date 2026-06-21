"""Unit tests for simulator 08A foundation contracts."""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import cast

import pytest
from app.services.simulator import (
    DEFAULT_AMBIGUOUS_SL_TP_POLICY,
    DEFERRED_PHASE1_SCOPE,
    SIM_ENGINE_ERROR_TAXONOMY,
    BrokerRuleProfile,
    CommissionModel,
    DeterministicJournal,
    EngineExtensionPoints,
    EngineOrder,
    EnginePosition,
    EventDrivenExecutionEngine,
    ExecutionLatencyModel,
    FixedLiquidityModel,
    FixedSlippageModel,
    FixedSpreadModel,
    LimitOrderQueueConfig,
    MarginModel,
    MarketHaltState,
    MarketHoursConfig,
    RegulatoryScope,
    ResourceQuota,
    ResumeCheckpoint,
    SimulatorActorContext,
    SimulatorBacktestRequestV1,
    SimulatorExecutionProvider,
    SimulatorSymbolSpec,
    SimulatorTick,
    SwapModel,
    apply_limit_queue,
    build_data_manifest_hash,
    build_environment_diagnostic,
    build_event_priority_order,
    build_markdown_report,
    build_optimization_work_units,
    build_parent_child_lineage,
    build_skipped_trade_diagnostic,
    build_trade_intents,
    can_batch_ticks,
    compare_canary_metrics,
    decide_gap_handling,
    decide_roll_action,
    deterministic_data_quality_checks,
    evaluate_market_session,
    evaluate_pending_order_trigger,
    evaluate_sl_tp_trigger,
    evaluate_stopout,
    is_non_fatal_diagnostic,
    normalize_order_volume,
    resolve_pegged_order_price,
    run_backtest,
    update_trailing_stop,
    validate_asset_class_scope,
    validate_engine_error_code,
    validate_fill_policy,
    validate_fractional_volume,
    validate_pegged_order_configuration,
    validate_pending_order_type,
    validate_phase1_scope,
    validate_resource_quota,
    validate_stop_prices,
    validate_trailing_stop_configuration,
    verify_resume_checkpoint,
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
    metadata = _mapping_value(result, "metadata")
    latency = _mapping_value(metadata, "execution_latency_model")
    audit = _mapping_value(metadata, "audit")
    artifacts = _mapping_value(result, "artifact_manifest")
    journal_manifest = _mapping_value(artifacts, "journal_manifest")
    run_configuration = _mapping_value(artifacts, "run_configuration")
    telemetry = _mapping_value(metadata, "telemetry")
    extension_points = _mapping_value(metadata, "extension_points")
    regulatory_scope = _mapping_value(metadata, "regulatory_scope")
    assert metadata["module"] == "simulator"
    assert metadata["operation"] == "event_driven_execution"
    assert metadata["tool_risk_level"] == "medium"
    assert metadata["side_effects"] == "simulated_only"
    assert metadata["ambiguous_sl_tp_policy"] == DEFAULT_AMBIGUOUS_SL_TP_POLICY
    assert metadata["state_authority"] == "engine_owned"
    assert audit["request_id"] == "req_engine"
    assert latency["total_ms"] == 0.0
    assert journal_manifest["filename"] == "journal_manifest.json"
    assert journal_manifest["retention_tier"] == "research_180_days"
    assert run_configuration["engine_version"] == result["engine_version"]
    assert telemetry["run_status"] == "success"
    assert extension_points["matching"] == "market_order"
    assert regulatory_scope["first_scope"] == "US equities and ETFs"
    assert "08A canonical tick-engine foundation" in report


def test_engine_rejects_first_tick_lookahead_through_tool() -> None:
    """Verify first-tick current-bar and future data is rejected."""
    payload = _payload()
    payload["metadata"] = {
        "first_tick_bar_open": "2026-01-01T00:05:00Z",
        "raw_ohlcv_points": [{"timestamp": "2026-01-01T00:05:00Z"}],
    }

    response = run_backtest(payload)

    validate_standard_response(response)
    assert response["status"] == "error"
    assert _error(response)["code"] == "SIM_LOOKAHEAD_DETECTED"


def test_engine_latency_model_and_ambiguous_policy_validation() -> None:
    """Verify latency components and ambiguous SL/TP policy boundaries."""
    request = SimulatorBacktestRequestV1(
        request_id="req_latency",
        actor_context=SimulatorActorContext(actor_id="tester"),
        strategy_ref="trend_following",
        symbols=("EURUSD",),
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        metadata={
            "execution_latency_model": {
                "strategy_compute_ms": 1.0,
                "broker_routing_ms": 2.0,
                "venue_gateway_ms": 3.0,
                "matching_engine_ms": 4.0,
            },
        },
    )
    result = EventDrivenExecutionEngine().run(request).to_dict()
    metadata = _mapping_value(result, "metadata")
    latency = _mapping_value(metadata, "execution_latency_model")
    assert latency["total_ms"] == 10.0

    with pytest.raises(ValidationError):
        ExecutionLatencyModel(strategy_compute_ms=-1)

    bad = SimulatorBacktestRequestV1(
        request_id="req_bad_policy",
        actor_context=SimulatorActorContext(actor_id="tester"),
        strategy_ref="trend_following",
        symbols=("EURUSD",),
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        metadata={"ambiguous_sl_tp_policy": "tp_first"},
    )
    with pytest.raises(ValidationError):
        EventDrivenExecutionEngine().run(bad)


def test_engine_matching_uses_liquidity_before_slippage_and_state_snapshots() -> None:
    """Verify engine-owned matching, accounting, and read-only snapshots."""
    engine = EventDrivenExecutionEngine()
    request = SimulatorBacktestRequestV1(
        request_id="req_match",
        actor_context=SimulatorActorContext(actor_id="tester"),
        strategy_ref="trend_following",
        symbols=("EURUSD",),
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        initial_balance=1000.0,
    )
    engine.run(request)

    deal = engine.execute_market_order(
        tick=SimulatorTick(
            timestamp="2026-01-01T00:00:01Z",
            symbol="EURUSD",
            bid=1.1,
            ask=1.1001,
        ),
        side="buy",
        requested_volume=1.0,
        liquidity_model=FixedLiquidityModel(max_volume_per_tick=0.5),
        slippage_model=FixedSlippageModel(slippage_points=2),
        commission_model=CommissionModel(amount_per_lot=4.0),
        time_in_force="IOC",
    )
    snapshot = engine.snapshot()

    assert deal.volume == 0.5
    assert deal.price == 1.10012
    assert deal.commission == 2.0
    assert deal.diagnostic_code == "SIM_IOC_REMAINDER_CANCELLED"
    assert len(snapshot.positions) == 1
    assert len(snapshot.orders) == 1
    assert len(snapshot.deals) == 1
    assert snapshot.account["commission_base"] == 2.0
    assert snapshot.account["margin_base"] > 0
    with pytest.raises(TypeError):
        cast("dict[str, object]", snapshot.positions)["blocked"] = next(
            iter(snapshot.positions.values())
        )


def test_engine_volume_stop_position_and_stopout_gates() -> None:
    """Verify volume normalization, stop validation, and broker risk gates."""
    symbol_spec = SimulatorSymbolSpec(
        symbol="EURUSD",
        lot_min=0.01,
        lot_max=1.0,
        lot_step=0.01,
    )
    normalized = normalize_order_volume(0.105, symbol_spec)
    assert normalized.raw_volume == 0.105
    assert normalized.normalized_volume == 0.1
    assert normalized.rounding_policy == "floor_to_step"
    assert normalized.adjusted is True

    validate_stop_prices(side="buy", entry_price=1.2, sl=1.1, tp=1.3)
    with pytest.raises(ValidationError):
        validate_stop_prices(side="buy", entry_price=1.2, sl=1.21)
    with pytest.raises(ValidationError):
        validate_stop_prices(side="sell", entry_price=1.2, tp=1.3)

    engine = EventDrivenExecutionEngine()
    request = SimulatorBacktestRequestV1(
        request_id="req_risk_gates",
        actor_context=SimulatorActorContext(actor_id="tester"),
        strategy_ref="trend_following",
        symbols=("EURUSD",),
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        initial_balance=1000.0,
    )
    engine.run(request)
    first_deal = engine.execute_market_order(
        tick=SimulatorTick(
            timestamp="2026-01-01T00:00:01Z",
            symbol="EURUSD",
            bid=1.1,
            ask=1.2,
        ),
        side="buy",
        requested_volume=0.105,
        symbol_spec=symbol_spec,
        time_in_force="IOC",
        broker_profile=BrokerRuleProfile(max_positions=1),
    )
    assert first_deal.volume == 0.1
    first_order = engine.orders[first_deal.order_id]
    assert first_order.raw_requested_volume == 0.105
    assert first_order.requested_volume == 0.1
    assert first_order.volume_rounding_policy == "floor_to_step"
    assert first_order.volume_adjusted is True
    with pytest.raises(ValidationError):
        engine.execute_market_order(
            tick=SimulatorTick(
                timestamp="2026-01-01T00:00:02Z",
                symbol="EURUSD",
                bid=1.1,
                ask=1.2,
            ),
            side="sell",
            requested_volume=0.1,
            symbol_spec=symbol_spec,
            time_in_force="IOC",
            broker_profile=BrokerRuleProfile(max_positions=1),
        )

    engine.account.balance_base = 10.0
    engine.account.margin_base = 100.0
    stopout = evaluate_stopout(
        engine.account,
        broker_profile=BrokerRuleProfile(stopout_level_percent=50.0),
    )
    assert stopout.status == "blocked"
    assert stopout.code == "SIM_MARGIN_STOP_OUT"
    with pytest.raises(ValidationError):
        engine.execute_market_order(
            tick=SimulatorTick(
                timestamp="2026-01-01T00:00:03Z",
                symbol="EURUSD",
                bid=1.1,
                ask=1.2,
            ),
            side="buy",
            requested_volume=0.1,
            symbol_spec=symbol_spec,
            time_in_force="IOC",
            broker_profile=BrokerRuleProfile(stopout_level_percent=50.0),
        )


def test_engine_optimization_work_units_and_resume_policy() -> None:
    """Verify deterministic optimization keys and resume compatibility checks."""
    request = SimulatorBacktestRequestV1(
        request_id="req_work_units",
        actor_context=SimulatorActorContext(actor_id="tester"),
        strategy_ref="trend_following",
        symbols=("EURUSD",),
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
    )
    units = build_optimization_work_units(
        request,
        [{"short_window": 5}, {"short_window": 10}],
    )
    assert len(units) == 2
    assert units[0].work_unit_id.startswith("simwu_")
    assert units[0].strategy_id == "trend_following"

    config_hash = units[0].config_hash
    data_hash = build_data_manifest_hash(request)
    compatible = verify_resume_checkpoint(
        ResumeCheckpoint(
            config_hash=config_hash,
            data_manifest_hash=data_hash,
            engine_version=units[0].engine_version,
            last_journal_sequence=2,
            random_seed_state="seed_state",
        ),
        expected_config_hash=config_hash,
        expected_data_manifest_hash=data_hash,
        expected_engine_version=units[0].engine_version,
        expected_next_sequence=3,
    )
    assert compatible.status == "compatible"

    incompatible = verify_resume_checkpoint(
        ResumeCheckpoint(
            config_hash="different",
            data_manifest_hash=data_hash,
            engine_version=units[0].engine_version,
            last_journal_sequence=2,
            random_seed_state="seed_state",
        ),
        expected_config_hash=config_hash,
        expected_data_manifest_hash=data_hash,
        expected_engine_version=units[0].engine_version,
        expected_next_sequence=3,
    )
    assert incompatible.status == "incompatible"
    assert incompatible.code == "SIM_CHECKPOINT_INCOMPATIBLE"


def test_engine_extension_scope_quota_canary_and_error_taxonomy() -> None:
    """Verify extension metadata, scope gates, quotas, and taxonomy helpers."""
    assert EngineExtensionPoints().to_dict()["optimization"] == "isolated_work_units"
    assert RegulatoryScope().to_dict()["fx_production_realistic_requirement"] == (
        "not_applicable"
    )
    assert "distributed_workers" in DEFERRED_PHASE1_SCOPE
    assert "SIM_LOOKAHEAD_DETECTED" in SIM_ENGINE_ERROR_TAXONOMY
    validate_engine_error_code("SIM_LOOKAHEAD_DETECTED")
    with pytest.raises(ValidationError):
        validate_engine_error_code("SIM_NOT_REAL")

    with pytest.raises(ValidationError):
        validate_phase1_scope({"requested_future_scope": ["distributed_workers"]})
    with pytest.raises(ValidationError):
        validate_resource_quota(
            wall_clock_seconds=10,
            temporary_storage_bytes=1,
            quota=ResourceQuota(max_wall_clock_seconds=1),
        )

    assert can_batch_ticks(possible_events_before_next_boundary=False) is True
    assert can_batch_ticks(possible_events_before_next_boundary=True) is False
    assert decide_roll_action("calendar_spread").action == "calendar_spread"
    assert build_environment_diagnostic().environment_hash.startswith("env_")
    assert (
        compare_canary_metrics(
            {"ending_balance": 100.0},
            {"ending_balance": 100.01},
            tolerance=0.1,
        ).status
        == "pass"
    )
    assert (
        compare_canary_metrics(
            {"ending_balance": 100.0},
            {"ending_balance": 101.0},
            tolerance=0.1,
        ).code
        == "SIM_CANARY_DIVERGENCE"
    )


def test_engine_trade_intents_event_order_and_lineage_are_deterministic() -> None:
    """Verify deterministic trade intents, event order, and lineage."""
    signals = [
        {
            "signal_id": "sig_2",
            "timestamp": "2026-01-01T00:01:00Z",
            "symbol": "EURUSD",
            "side": "buy",
            "volume": 0.2,
        },
        {
            "signal_id": "sig_1",
            "timestamp": "2026-01-01T00:00:00Z",
            "symbol": "EURUSD",
            "side": "sell",
            "volume": 0.1,
        },
    ]
    seed: dict[str, object] = {"run_id": "simrun_test"}
    first = build_trade_intents(signals, seed_material=seed)
    second = build_trade_intents(signals, seed_material=seed)
    assert [intent.intent_id for intent in first] == [
        intent.intent_id for intent in second
    ]

    ordered = build_event_priority_order(
        [
            {
                "timestamp": "2026-01-01T00:00:01Z",
                "priority": 5,
                "event_type": "deal",
            },
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "priority": 10,
                "event_type": "signal",
            },
        ]
    )
    assert [record.event_type for record in ordered] == ["signal", "deal"]

    lineage = build_parent_child_lineage(
        parent_order_id="parent_1",
        child_order_ids=("child_1", "child_2"),
        fill_ids=("fill_1",),
    )
    assert lineage.parent_order_id == "parent_1"
    assert lineage.child_order_ids == ("child_1", "child_2")


def test_engine_broker_rules_diagnostics_and_quality_gates() -> None:
    """Verify deterministic broker rules, diagnostics, and data checks."""
    assert validate_fill_policy("ioc") == "IOC"
    with pytest.raises(ValidationError):
        validate_fill_policy(
            "RETURN",
            broker_profile=BrokerRuleProfile(supported_fill_policies=("IOC",)),
        )

    diagnostic = build_skipped_trade_diagnostic(
        code="SIM_MARKET_CLOSED",
        reason="session is closed",
        field_path="orders[0]",
    )
    assert diagnostic.code == "SIM_MARKET_CLOSED"
    assert diagnostic.retryable is False
    assert diagnostic.field_path == "orders[0]"

    validate_asset_class_scope("FX")
    with pytest.raises(ValidationError):
        validate_asset_class_scope("EQUITY")
    validate_fractional_volume(quantity=0.25, volume_step=0.01)
    with pytest.raises(ValidationError):
        validate_fractional_volume(quantity=0.255, volume_step=0.01)

    empty = deterministic_data_quality_checks([], survivorship_bias_flag=True)
    assert empty[0].code == "SIM_DATA_EMPTY"
    assert empty[0].survivorship_bias_flag is True

    duplicate = deterministic_data_quality_checks(
        [
            SimulatorTick(
                timestamp="2026-01-01T00:00:00Z",
                symbol="EURUSD",
                bid=1.0,
                ask=1.1,
            ),
            SimulatorTick(
                timestamp="2026-01-01T00:00:00Z",
                symbol="EURUSD",
                bid=1.0,
                ask=1.1,
            ),
        ]
    )
    assert duplicate[0].code == "SIM_DATA_DUPLICATE_TIMESTAMP"

    engine = EventDrivenExecutionEngine()
    request = SimulatorBacktestRequestV1(
        request_id="req_fill_policy",
        actor_context=SimulatorActorContext(actor_id="tester"),
        strategy_ref="trend_following",
        symbols=("EURUSD",),
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
    )
    engine.run(request)
    with pytest.raises(ValidationError):
        engine.execute_market_order(
            tick=SimulatorTick(
                timestamp="2026-01-01T00:00:01Z",
                symbol="EURUSD",
                bid=1.0,
                ask=1.1,
            ),
            side="buy",
            requested_volume=0.1,
            time_in_force="DAY",
        )


def test_engine_market_hours_gap_and_queue_policies() -> None:
    """Verify market sessions, gaps, halts, and queue-ahead behavior."""
    open_state = evaluate_market_session(
        "2026-01-01T12:00:00Z",
        config=MarketHoursConfig(session_start="09:00", session_end="17:00"),
    )
    assert open_state.is_open is True

    closed_state = evaluate_market_session(
        "2026-01-03T12:00:00Z",
        config=MarketHoursConfig(session_start="09:00", session_end="17:00"),
    )
    assert closed_state.is_open is False
    assert closed_state.code == "SIM_MARKET_CLOSED"

    break_state = evaluate_market_session(
        "2026-01-01T12:30:00Z",
        config=MarketHoursConfig(
            session_start="09:00",
            session_end="17:00",
            session_breaks=("12:00-13:00",),
        ),
    )
    assert break_state.reason == "session_break"

    halt_state = evaluate_market_session(
        "2026-01-01T12:00:00Z",
        halt_state=MarketHaltState(
            active=True,
            halt_type="symbol",
            reason="symbol halted",
        ),
    )
    assert halt_state.code == "SIM_MARKET_HALT_ACTIVE"

    rejected_gap = decide_gap_handling(policy="reject")
    assert rejected_gap.code == "SIM_GAP_HANDLING_REJECTED"
    filled_gap = decide_gap_handling(policy="fill_at_open", ambiguous_sl_tp=True)
    assert "conservative_worst_outcome" in filled_gap.details

    with pytest.raises(ValidationError):
        apply_limit_queue(1.0, 1.0)
    queued = apply_limit_queue(
        1.0,
        0.8,
        config=LimitOrderQueueConfig(
            queue_model="configured_queue_ahead",
            touch_fill_enabled=True,
            queue_ahead_volume=0.3,
            fill_allocation_method="fifo",
        ),
    )
    assert queued == 0.5


def test_engine_fill_policy_lifecycle_and_average_price() -> None:
    """Verify FOK, RETURN, partial fills, and average-price recalculation."""
    engine = EventDrivenExecutionEngine()
    request = SimulatorBacktestRequestV1(
        request_id="req_lifecycle",
        actor_context=SimulatorActorContext(actor_id="tester"),
        strategy_ref="trend_following",
        symbols=("EURUSD",),
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        initial_balance=1000.0,
    )
    engine.run(request)
    tick = SimulatorTick(
        timestamp="2026-01-01T00:00:01Z",
        symbol="EURUSD",
        bid=1.0,
        ask=1.1,
    )

    with pytest.raises(ValidationError):
        engine.execute_market_order(
            tick=tick,
            side="buy",
            requested_volume=1.0,
            liquidity_model=FixedLiquidityModel(max_volume_per_tick=0.5),
            time_in_force="FOK",
        )

    return_deal = engine.execute_market_order(
        tick=tick,
        side="buy",
        requested_volume=1.0,
        liquidity_model=FixedLiquidityModel(max_volume_per_tick=0.4),
        time_in_force="RETURN",
    )
    assert return_deal.volume == 0.4
    assert any(order.status == "pending" for order in engine.orders.values())

    second_deal = engine.execute_market_order(
        tick=SimulatorTick(
            timestamp="2026-01-01T00:00:02Z",
            symbol="EURUSD",
            bid=1.2,
            ask=1.3,
        ),
        side="buy",
        requested_volume=0.6,
        liquidity_model=FixedLiquidityModel(max_volume_per_tick=1.0),
        time_in_force="IOC",
    )
    assert second_deal.volume == 0.6
    snapshot = engine.snapshot()
    assert len(snapshot.deals) == 2
    position = next(iter(snapshot.positions.values()))
    assert position.volume == 1.0
    assert position.average_price == 1.22


def test_engine_pending_order_trigger_rules_cover_supported_types() -> None:
    """Verify limit, stop, and stop-limit pending-order trigger rules."""
    tick = SimulatorTick(
        timestamp="2026-01-01T00:00:00Z",
        symbol="EURUSD",
        bid=1.08,
        ask=1.12,
    )
    cases = [
        ("buy_limit", "buy", 1.13, None, True, False),
        ("sell_limit", "sell", 1.07, None, True, False),
        ("buy_stop", "buy", 1.11, None, True, False),
        ("sell_stop", "sell", 1.09, None, True, False),
        ("buy_stop_limit", "buy", 1.10, 1.13, True, True),
        ("sell_stop_limit", "sell", 1.09, 1.07, True, True),
    ]
    for order_type, side, price, stop_limit, triggered, activated in cases:
        assert validate_pending_order_type(order_type) == order_type
        order = EngineOrder(
            order_id=f"order_{order_type}",
            symbol="EURUSD",
            side="buy" if side == "buy" else "sell",
            requested_volume=1.0,
            filled_volume=0.0,
            status="pending",
            created_at=tick.timestamp,
            order_price=price,
            stop_limit_price=stop_limit,
            order_type=order_type,
        )

        result = evaluate_pending_order_trigger(order, tick)

        assert result.triggered is triggered
        assert result.activated is activated
        assert result.fill_price is not None


def test_engine_places_and_triggers_pending_orders() -> None:
    """Verify pending-order records execute through engine-owned state."""
    engine = EventDrivenExecutionEngine()
    open_tick = SimulatorTick(
        timestamp="2026-01-01T00:00:00Z",
        symbol="EURUSD",
        bid=1.20,
        ask=1.21,
    )
    order = engine.place_pending_order(
        tick=open_tick,
        order_type="buy_limit",
        requested_volume=0.5,
        order_price=1.10,
        time_in_force="IOC",
        sl=1.05,
        tp=1.15,
    )
    assert order.status == "pending"
    assert order.sl == 1.05
    assert order.tp == 1.15

    deals = engine.trigger_pending_orders(
        tick=SimulatorTick(
            timestamp="2026-01-01T00:00:01Z",
            symbol="EURUSD",
            bid=1.09,
            ask=1.10,
        ),
        liquidity_model=FixedLiquidityModel(max_volume_per_tick=1.0),
    )

    assert len(deals) == 1
    assert deals[0].volume == 0.5
    assert engine.orders[order.order_id].status == "filled"
    assert len(engine.snapshot().positions) == 1

    stop_limit = engine.place_pending_order(
        tick=open_tick,
        order_type="buy_stop_limit",
        requested_volume=0.5,
        order_price=1.15,
        stop_limit_price=1.12,
        time_in_force="IOC",
    )
    activation_only = engine.trigger_pending_orders(
        tick=SimulatorTick(
            timestamp="2026-01-01T00:00:02Z",
            symbol="EURUSD",
            bid=1.19,
            ask=1.20,
        ),
        liquidity_model=FixedLiquidityModel(max_volume_per_tick=1.0),
    )
    assert activation_only == []
    assert engine.orders[stop_limit.order_id].status == "activated"


def test_engine_sl_tp_and_advanced_order_config_gates() -> None:
    """Verify SL/TP triggers and configured trailing/pegged gates."""
    position = EnginePosition(
        position_id="pos_buy",
        symbol="EURUSD",
        side="buy",
        volume=1.0,
        average_price=1.10,
        margin=100.0,
        opened_at="2026-01-01T00:00:00Z",
    )
    sl_result = evaluate_sl_tp_trigger(
        position,
        SimulatorTick(
            timestamp="2026-01-01T00:00:01Z",
            symbol="EURUSD",
            bid=1.04,
            ask=1.06,
        ),
        sl=1.05,
        tp=1.15,
    )
    assert sl_result.triggered is True
    assert sl_result.trigger_type == "sl"

    tp_result = evaluate_sl_tp_trigger(
        position,
        SimulatorTick(
            timestamp="2026-01-01T00:00:02Z",
            symbol="EURUSD",
            bid=1.16,
            ask=1.18,
        ),
        sl=1.05,
        tp=1.15,
    )
    assert tp_result.trigger_type == "tp"

    accepted_trailing = validate_trailing_stop_configuration(
        trailing_stop_points=10.0,
        configured=True,
    )
    assert accepted_trailing.field_path == "trailing_stop_points"
    trailing_update = update_trailing_stop(
        position,
        SimulatorTick(
            timestamp="2026-01-01T00:00:03Z",
            symbol="EURUSD",
            bid=1.20,
            ask=1.22,
        ),
        current_sl=1.05,
        trailing_stop_points=100.0,
    )
    assert trailing_update.updated is True
    assert trailing_update.new_sl == 1.199
    with pytest.raises(ValidationError):
        validate_trailing_stop_configuration(
            trailing_stop_points=10.0,
            configured=False,
        )

    accepted_pegged = validate_pegged_order_configuration(
        pegged_reference="mid",
        configured=True,
    )
    assert accepted_pegged.field_path == "pegged_reference"
    pegged_price = resolve_pegged_order_price(
        SimulatorTick(
            timestamp="2026-01-01T00:00:04Z",
            symbol="EURUSD",
            bid=1.20,
            ask=1.22,
        ),
        pegged_reference="mid",
    )
    assert pegged_price.price == 1.21
    with pytest.raises(ValidationError):
        validate_pegged_order_configuration(
            pegged_reference="unknown",
            configured=True,
        )


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
