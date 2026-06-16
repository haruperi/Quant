# ruff: noqa: E501, PD011, PT018, NPY002, DTZ001, ARG002, RUF012, S113, PTH123, C901, RUF100, PT012
"""Unit tests for advanced features of the indicator service."""

from typing import Any

import pandas as pd
import pytest
from app.services.indicators import (
    IndicatorConfig,
    IndicatorContext,
    IndicatorResult,
    IndicatorState,
    WarmupRequirement,
    sma,
)
from app.services.indicators.adapters.audit import global_audit_logger
from app.services.indicators.adapters.cache import global_cache
from app.services.indicators.calculations import (
    validate_composition_graph,
)
from app.services.indicators.errors import (
    IndicatorConfigError,
    ResourceLimitExceededError,
    StateCorruptedError,
    StateIncompatibleError,
)
from app.utils.errors import ValidationError

from tests.unit.app.services.indicators.test_trend import generate_mock_ohlcv


def test_incremental_sma_updates_and_serialization():
    """Verify that incremental updates calculate values, serialize, and deserialize correctly."""
    df = generate_mock_ohlcv(5, constant_price=10.0)
    config = IndicatorConfig(indicator_id="sma", parameters={"period": 3})

    # Initialize empty state
    state = IndicatorState(indicator_id="sma")
    from app.services.indicators.registry import get_indicator

    sma_class = get_indicator("sma")
    sma_inst = sma_class()

    # Feed bars one by one
    results = []
    for idx, row in df.iterrows():
        bar = row.to_dict()
        bar["timestamp"] = idx
        res, state = sma_inst.update(bar, state, config)
        results.append(res.values["sma_3"].iloc[0])

    # Warmup period 3: first two should be NaN, last three should be 10.0
    import numpy as np

    assert np.isnan(results[0])
    assert np.isnan(results[1])
    assert results[2] == 10.0
    assert results[3] == 10.0
    assert results[4] == 10.0

    # Test serialization/deserialization
    serialized = sma_inst.serialize_state(state)
    assert isinstance(serialized, str)
    assert "history" in serialized

    restored_state = sma_inst.deserialize_state(serialized)
    assert restored_state.indicator_id == "sma"
    assert restored_state.warmup_completed is True
    assert [bar["close"] for bar in restored_state.accumulators["history"]][-3:] == [
        10.0,
        10.0,
        10.0,
    ]


def test_incremental_state_validation_failures():
    """Verify that serialization/deserialization raises correct error codes on compatibility mismatch."""
    from app.services.indicators.registry import get_indicator

    sma_class = get_indicator("sma")
    sma_inst = sma_class()

    # Mismatched indicator id
    bad_state_payload = '{"indicator_id": "ema", "last_processed_timestamp": null, "last_processed_symbol": null, "accumulators": {}, "warmup_completed": false, "state_schema_version": "1.0.0"}'
    with pytest.raises(StateIncompatibleError) as exc:
        sma_inst.deserialize_state(bad_state_payload)
    assert exc.value.code == "IND_STATE_INCOMPATIBLE"

    # Corrupted payload JSON
    corrupted_payload = "not a json string"
    with pytest.raises(StateCorruptedError) as exc:
        sma_inst.deserialize_state(corrupted_payload)
    assert exc.value.code == "IND_STATE_CORRUPTED"


def test_incremental_idempotency():
    """Verify that incremental updates are idempotent for the same timestamp."""
    config = IndicatorConfig(indicator_id="sma", parameters={"period": 3})
    state = IndicatorState(indicator_id="sma")
    from app.services.indicators.registry import get_indicator

    sma_inst = get_indicator("sma")()

    bar = {"timestamp": "2026-06-16T10:00:00Z", "close": 10.0, "symbol": "AAPL"}
    _res1, state = sma_inst.update(bar, state, config)
    assert len(state.accumulators["history"]) == 1

    # Update again with same timestamp
    _res2, state = sma_inst.update(bar, state, config)
    # Length should still be 1 (idempotency overwrote the value)
    assert len(state.accumulators["history"]) == 1


def test_caching_policies_and_degradation():
    """Verify caching hits/misses and degradation behaviors."""
    df = generate_mock_ohlcv(10, constant_price=1.5)

    # 1. Warm Cache calculation
    IndicatorConfig(
        indicator_id="sma", parameters={"period": 3}, cache_policy="best_effort"
    )

    global_cache._store.clear()

    # First execution (cache miss, will write to cache)
    res1 = sma(df, period=3, error_mode="exception")

    # Second execution (cache hit)
    res2 = sma(df, period=3, error_mode="exception")

    assert res1.values["sma_3"].equals(res2.values["sma_3"])

    # 2. Simulate unreachable cache store
    global_cache.is_unreachable = True

    # Under best_effort policy, should degrade gracefully to uncached
    res_degraded = sma(df, period=3, error_mode="exception")
    assert not res_degraded.values.empty

    # Under strict policy, should raise IND_CACHE_INVALID
    with pytest.raises(IndicatorConfigError) as exc:
        sma(df, period=3, error_mode="exception", cache_policy="strict")
    assert exc.value.code == "IND_CACHE_INVALID"

    # Reset cache state
    global_cache.is_unreachable = False


def test_auditing_signatures_and_chain_integrity():
    """Verify audit trails generate signatures and maintain chain integrity."""
    df = generate_mock_ohlcv(5)
    context = IndicatorContext(
        actor="agent", request_id="req-123", correlation_id="corr-456"
    )

    # Perform a calculation to trigger audit logging
    sma(df, period=3, context=context)

    entries = global_audit_logger.get_entries()
    assert len(entries) >= 1

    last_entry = entries[-1]
    assert last_entry["request_metadata"]["actor"] == "agent"
    assert last_entry["request_metadata"]["request_id"] == "req-123"
    assert "signature" in last_entry

    # Verify audit chain integrity
    assert global_audit_logger.verify_chain() is True


def test_composition_validation_dag():
    """Verify cyclic indicator composition graphs are correctly blocked."""
    # Acyclic graph should pass
    acyclic = {"ema_10": ["close"], "macd": ["ema_10", "ema_20"], "ema_20": ["close"]}
    validate_composition_graph(acyclic)  # Should not raise

    # Cyclic graph should fail with IND_INVALID_CONFIG
    cyclic = {"ema_10": ["macd"], "macd": ["ema_10"]}
    with pytest.raises(ValidationError) as exc:
        validate_composition_graph(cyclic)
    assert exc.value.code == "IND_INVALID_CONFIG"


def test_resource_limits_enforcement():
    """Verify that inputs exceeding resource limits raise IND_RESOURCE_LIMIT_EXCEEDED."""
    df = generate_mock_ohlcv(10)

    # Temporarily set max rows to a small value for limit testing
    import app.services.indicators.calculations as calc

    original_max_rows = calc.DEFAULT_MAX_ROWS
    calc.DEFAULT_MAX_ROWS = 5

    try:
        # running SMA on df of length 10 should trigger limit exceeded
        with pytest.raises(ResourceLimitExceededError) as exc:
            sma(df, period=3)
        assert exc.value.code == "IND_RESOURCE_LIMIT_EXCEEDED"
    finally:
        # Revert changes
        calc.DEFAULT_MAX_ROWS = original_max_rows


def test_state_compatibility_validation_checks():
    """Verify that state deserialization validates version, parameter_hash, and schema version."""
    from app.services.indicators.registry import get_indicator

    sma_inst = get_indicator("sma")()

    # Mismatched implementation_version
    bad_version_payload = (
        '{"indicator_id": "sma", "last_processed_timestamp": null, '
        '"last_processed_symbol": null, "accumulators": {}, '
        '"warmup_completed": false, "state_schema_version": "1.0.0", '
        '"implementation_version": "2.0.0", "parameter_hash": ""}'
    )
    with pytest.raises(StateIncompatibleError) as exc:
        sma_inst.deserialize_state(bad_version_payload)
    assert exc.value.code == "IND_STATE_INCOMPATIBLE"
    assert "version" in str(exc.value)

    # Mismatched parameter_hash
    bad_param_payload = (
        '{"indicator_id": "sma", "last_processed_timestamp": null, '
        '"last_processed_symbol": null, "accumulators": {}, '
        '"warmup_completed": false, "state_schema_version": "1.0.0", '
        '"implementation_version": "1.0.0", "parameter_hash": "wrong_hash"}'
    )
    with pytest.raises(StateIncompatibleError) as exc:
        sma_inst.deserialize_state(
            bad_param_payload, expected_parameter_hash="expected_hash"
        )
    assert exc.value.code == "IND_STATE_INCOMPATIBLE"
    assert "parameter hash" in str(exc.value)

    # Incompatible schema version (e.g. 2.0.0)
    bad_schema_payload = (
        '{"indicator_id": "sma", "last_processed_timestamp": null, '
        '"last_processed_symbol": null, "accumulators": {}, '
        '"warmup_completed": false, "state_schema_version": "2.0.0", '
        '"implementation_version": "1.0.0", "parameter_hash": ""}'
    )
    with pytest.raises(StateIncompatibleError) as exc:
        sma_inst.deserialize_state(bad_schema_payload)
    assert exc.value.code == "IND_STATE_INCOMPATIBLE"
    assert "schema version" in str(exc.value)


def test_notebook_representation_methods():
    """Verify that HTML and pretty text representations of IndicatorResult render correctly."""
    df = generate_mock_ohlcv(10, constant_price=1.23)
    res = sma(df, period=3)

    # Test html repr
    html_repr = res._repr_html_()
    assert isinstance(html_repr, str)
    assert "Indicator Result: SMA" in html_repr
    assert "Parameter Hash" in html_repr
    assert "Summary Statistics" in html_repr

    # Test pretty repr
    class DummyPrettyPrinter:
        def __init__(self):
            self.output = ""

        def text(self, msg):
            self.output += msg

    p = DummyPrettyPrinter()
    res._repr_pretty_(p, False)
    assert "IndicatorResult: SMA" in p.output
    assert "Summary Stats" in p.output


def test_composed_indicator_execution():
    """Verify topological execution of composed indicator graphs and available_at propagation."""
    df = generate_mock_ohlcv(15, constant_price=10.0)

    # 1. Setup composed graph: sma_3 depends on close, ema_3 depends on sma_3
    graph = {
        "sma_3": ["close"],
        "ema_3": ["sma_3"],
    }
    configs = {
        "sma_3": IndicatorConfig(indicator_id="sma", parameters={"period": 3}),
        "ema_3": IndicatorConfig(
            indicator_id="ema", parameters={"period": 3}, source_column="sma_3"
        ),
    }

    from app.services.indicators.calculations import execute_indicator_composition

    result = execute_indicator_composition(df, graph, configs)

    # Verify execution output columns exist
    assert "sma_3" in result.output_columns
    assert "ema_sma_3_3" in result.output_columns
    assert "sma_3" in result.values.columns
    assert "ema_sma_3_3" in result.values.columns

    # Verify available_at propagation
    # Since ema_3 depends on sma_3, available_at should be correctly propagated
    assert "available_at" in result.values.columns

    # 2. Test cyclical graph raises IND_INVALID_CONFIG
    cyclic_graph = {
        "sma_3": ["ema_3"],
        "ema_3": ["sma_3"],
    }
    with pytest.raises(IndicatorConfigError) as exc:
        execute_indicator_composition(df, cyclic_graph, configs)
    assert exc.value.code == "IND_INVALID_CONFIG"

    # 3. Test missing configuration
    missing_config = {
        "sma_3": ["close"],
        "ema_3": ["sma_3"],
    }
    with pytest.raises(IndicatorConfigError) as exc:
        execute_indicator_composition(df, missing_config, {"sma_3": configs["sma_3"]})
    assert exc.value.code == "IND_INVALID_CONFIG"


def test_distributed_tracing_and_propagation():
    """Verify traceparent parsing, context span tracking, and workflow integration."""
    from app.services.indicators.adapters.tracing import (
        IndicatorSpan,
        parse_traceparent,
    )

    # 1. Parse traceparent
    invalid = parse_traceparent("invalid-traceparent-format")
    assert invalid is None

    valid_header = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    parsed = parse_traceparent(valid_header)
    assert parsed is not None
    assert parsed["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert parsed["parent_id"] == "00f067aa0ba902b7"
    assert parsed["flags"] == "01"

    # 2. Context span
    with IndicatorSpan("test_span", traceparent=valid_header, is_enabled=True) as span:
        assert span.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert span.parent_id == "00f067aa0ba902b7"
        assert len(span.span_id) == 16

    # 3. Running SMA workflow with tracing context
    df = generate_mock_ohlcv(10)
    ctx = IndicatorContext(tracing_enabled=True, traceparent=valid_header)
    res = sma(df, period=3, context=ctx)
    assert not res.values.empty
    assert res.lookahead_metadata["source_timeframe"] == "D1"


def test_canary_routing_and_comparisons():
    """Verify canary evaluation matching rules, delta calculations, tolerances, and routing."""
    from app.services.indicators.adapters.canary import (
        CanaryConfig,
        global_canary_router,
    )

    df = generate_mock_ohlcv(10, constant_price=10.0)
    prices = [10.0, 11.0, 9.5, 12.0, 10.5, 11.0, 10.0, 9.0, 11.5, 12.0]
    for col in ["open", "high", "low", "close"]:
        df[col] = prices

    # Setup Canary Config comparing SMA to EMA
    canary_conf = CanaryConfig(
        enabled=True,
        canary_indicator_id="ema",
        canary_parameters={"period": 3},
        target_actors=["test-actor"],
        select_canary_route=False,
    )

    # 1. Context not matching actor: should bypass canary comparison and execute baseline SMA
    ctx_bypass = IndicatorContext(actor="other-actor", request_id="req-bypass")
    res_bypass = sma(df, period=3, context=ctx_bypass, canary_config=canary_conf)
    assert "sma_3" in res_bypass.output_columns

    # 2. Context matching actor: should run baseline AND canary, and record comparison deltas
    global_canary_router.comparisons.clear()
    ctx_match = IndicatorContext(actor="test-actor", request_id="req-match")
    res_match = sma(df, period=3, context=ctx_match, canary_config=canary_conf)

    # Since select_canary_route is False, official output should still be the baseline (SMA)
    assert "sma_3" in res_match.output_columns

    # Check that a comparison record was logged
    assert len(global_canary_router.comparisons) == 1
    record = global_canary_router.comparisons[0]
    assert record.baseline_id == "sma"
    assert record.canary_id == "ema"
    assert (
        record.rollback_recommended is True
    )  # SMA and EMA values differ, so tolerance check fails and rollback is recommended
    assert record.tolerance_passed is False

    # 3. Select canary route is True: official output should be the canary (EMA)
    canary_conf_select = CanaryConfig(
        enabled=True,
        canary_indicator_id="ema",
        canary_parameters={"period": 3},
        target_actors=["test-actor"],
        select_canary_route=True,
    )
    res_canary = sma(df, period=3, context=ctx_match, canary_config=canary_conf_select)
    assert "ema_3" in res_canary.output_columns  # it returned EMA columns


def test_resource_limits_configurable():
    """Verify configurable resource limit constraints (memory, timeout, rows)."""
    from app.services.indicators.protocols import IndicatorResourceLimits

    df = generate_mock_ohlcv(10)

    # Constraint row count
    limits_rows = IndicatorResourceLimits(max_rows=5)
    with pytest.raises(ResourceLimitExceededError) as exc:
        sma(df, period=3, resource_limits=limits_rows)
    assert exc.value.code == "IND_RESOURCE_LIMIT_EXCEEDED"

    # Constraint memory budget
    limits_mem = IndicatorResourceLimits(memory_budget_bytes=10)
    with pytest.raises(ResourceLimitExceededError) as exc:
        sma(df, period=3, resource_limits=limits_mem)
    assert exc.value.code == "IND_RESOURCE_LIMIT_EXCEEDED"

    # Constraint timeout limits
    limits_timeout = IndicatorResourceLimits(timeout_seconds=0.000001)
    with pytest.raises(ResourceLimitExceededError) as exc:
        sma(df, period=3, resource_limits=limits_timeout)
    assert exc.value.code == "IND_RESOURCE_LIMIT_EXCEEDED"
    assert "timeout" in str(exc.value)


def test_column_conflict_policies_and_custom_naming():
    """Verify output column conflict policies (fail, overwrite, suffix) and custom output renaming."""
    df = generate_mock_ohlcv(10, constant_price=5.0)

    # 1. Custom naming policy validation
    from app.services.indicators.registry import execute_indicator_workflow

    res_custom = execute_indicator_workflow(
        "sma",
        df,
        {"period": 3},
        output_naming_policy="custom",
        custom_output_columns=["my_custom_sma"],
    )
    assert "my_custom_sma" in res_custom.output_columns
    assert "my_custom_sma" in res_custom.values.columns

    # Length mismatch custom columns
    with pytest.raises(ValidationError):
        execute_indicator_workflow(
            "sma",
            df,
            {"period": 3},
            output_naming_policy="custom",
            custom_output_columns=["one", "two"],
        )

    # Invalid character custom columns
    with pytest.raises(ValidationError):
        execute_indicator_workflow(
            "sma",
            df,
            {"period": 3},
            output_naming_policy="custom",
            custom_output_columns=["invalid-name-here!"],
        )

    # 2. Conflict Policy: fail
    # Pre-add column to input data to simulate conflict
    df_conflict = df.copy()
    df_conflict["sma_3"] = 1.0

    with pytest.raises(ValidationError) as exc:
        res = sma(df, period=3)
        res.join_to(df_conflict, mode="copy")
    assert exc.value.code == "IND_OUTPUT_COLUMN_CONFLICT"

    # 3. Conflict Policy: overwrite
    res_over = execute_indicator_workflow(
        "sma", df, {"period": 3}, column_conflict_policy="overwrite"
    )
    joined_over = res_over.join_to(df_conflict, mode="copy")
    # Check that values are overwritten with new SMA values (5.0) instead of old conflicted values (1.0)
    assert joined_over["sma_3"].iloc[-1] == 5.0

    # 4. Conflict Policy: suffix
    res_suffix = execute_indicator_workflow(
        "sma",
        df,
        {"period": 3},
        column_conflict_policy="suffix",
        conflict_suffix="_custom_sfx",
    )
    joined_suffix = res_suffix.join_to(df_conflict, mode="copy")
    assert "sma_3" in joined_suffix.columns
    assert "sma_3_custom_sfx" in joined_suffix.columns
    assert joined_suffix["sma_3_custom_sfx"].iloc[-1] == 5.0


def test_slo_monitoring_metrics():
    """Verify that SLOMonitor tracks error and timeout rates, triggering alert metadata."""
    from app.services.indicators.adapters.observability import SLOMonitor

    monitor = SLOMonitor(
        error_threshold=0.1, timeout_threshold=0.05, measurement_window_seconds=10
    )

    # 1. Healthy state
    monitor.record_request(0.01, is_error=False, is_timeout=False)
    status = monitor.check_slo_status()
    assert status["slo_passed"] is True
    assert status["error_rate"] == 0.0
    assert status["timeout_rate"] == 0.0

    # 2. Breach error rate (record 2 errors out of 5 requests -> 40% error rate)
    for _ in range(3):
        monitor.record_request(0.01, is_error=False, is_timeout=False)
    for _ in range(2):
        monitor.record_request(0.01, is_error=True, is_timeout=False)

    status_breached = monitor.check_slo_status()
    assert status_breached["slo_passed"] is False
    assert status_breached["error_violation"] is True
    assert status_breached["alert_routing"] is not None
    assert status_breached["alert_routing"]["channel"] == "slack"


def test_typing_marker_and_metadata():
    """Verify py.typed package typing file presence."""
    from pathlib import Path

    pkg_root = Path(__file__).resolve().parents[5] / "app" / "services" / "indicators"
    marker = pkg_root / "py.typed"
    assert marker.exists()


def test_price_adjustment_and_microstructure_validations():
    """Verify price adjustment, symbol mapping, and bid/ask microstructure validations."""
    from app.services.indicators.errors import (
        InvertedMarketError,
        SpreadThresholdExceededError,
        StubQuoteRejectedError,
        SymbolMappingRequiredError,
        UnknownAdjustmentStatusError,
        UnsupportedIntraBarAdjustmentError,
    )

    df = generate_mock_ohlcv(5)

    # 1. Invalid price adjustment status
    with pytest.raises(UnknownAdjustmentStatusError) as exc:
        sma(df, period=3, price_adjustment_status="invalid_status")
    assert exc.value.code == "IND_UNKNOWN_ADJUSTMENT_STATUS"

    # 2. Unknown price adjustment status when prohibited
    with pytest.raises(UnknownAdjustmentStatusError) as exc:
        sma(
            df,
            period=3,
            price_adjustment_status="unknown",
            allow_unknown_adjustment=False,
        )
    assert exc.value.code == "IND_UNKNOWN_ADJUSTMENT_STATUS"

    # 3. Intra-bar corporate action rejection
    df_corp = df.copy()
    df_corp["intra_bar_corp_action"] = [0.0, 0.0, 1.0, 0.0, 0.0]
    with pytest.raises(UnsupportedIntraBarAdjustmentError) as exc:
        sma(df_corp, period=3)
    assert exc.value.code == "IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED"

    # 4. Symbol mapping required but missing
    df_sym = df.copy()
    df_sym["symbol"] = "EURUSD"
    with pytest.raises(SymbolMappingRequiredError) as exc:
        sma(df_sym, period=3, symbol_mapping_contract={"GBPUSD": "GBP_USD"})
    assert exc.value.code == "IND_SYMBOL_MAPPING_REQUIRED"

    # 5. Microstructure bid/ask validation: missing required microstructure columns
    with pytest.raises(ValidationError) as exc:
        sma(df, period=3, price_source="bid")
    assert "Required microstructure column" in str(exc.value)

    # Setup bid/ask data
    df_micro = df.copy()
    df_micro["bid"] = [1.1200, 1.1210, 1.1190, 1.1220, 1.1205]
    df_micro["ask"] = [1.1202, 1.1212, 1.1192, 1.1222, 1.1207]

    # 6. Inverted market (ask < bid)
    df_inverted = df_micro.copy()
    df_inverted.loc[df_inverted.index[2], "ask"] = 1.1180
    with pytest.raises(InvertedMarketError) as exc:
        sma(df_inverted, period=3, price_source="bid")
    assert exc.value.code == "IND_INVERTED_MARKET"

    # 7. Stub quotes (bid or ask <= 0)
    df_stub = df_micro.copy()
    df_stub.loc[df_stub.index[2], "bid"] = 0.0
    with pytest.raises(StubQuoteRejectedError) as exc:
        sma(df_stub, period=3, price_source="bid", allow_stub_quotes=False)
    assert exc.value.code == "IND_STUB_QUOTE_REJECTED"

    # 8. Spread threshold exceeded
    df_spread = df_micro.copy()
    df_spread.loc[df_spread.index[2], "ask"] = (
        2.0  # huge spread relative to mid (1.119)
    )
    with pytest.raises(SpreadThresholdExceededError) as exc:
        sma(df_spread, period=3, price_source="bid", spread_rejection_threshold=0.1)
    assert exc.value.code == "IND_SPREAD_THRESHOLD_EXCEEDED"


def test_unsupported_out_of_core_and_acceleration():
    """Verify out-of-core rejection, acceleration fallback, and deprecation checks."""
    from app.services.indicators.errors import (
        AccelerationBackendUnavailableError,
        DeprecatedIndicatorError,
        UnsupportedOutOfCoreError,
    )

    df = generate_mock_ohlcv(5)

    # 1. Out-of-core rejection
    with pytest.raises(UnsupportedOutOfCoreError) as exc:
        sma(df, period=3, execution_backend="out_of_core")
    assert exc.value.code == "IND_UNSUPPORTED_OUT_OF_CORE"

    # 2. Acceleration backend unavailable
    with pytest.raises(AccelerationBackendUnavailableError) as exc:
        sma(df, period=3, acceleration_backend="unsupported_backend")
    assert exc.value.code == "IND_ACCELERATION_BACKEND_UNAVAILABLE"

    # 3. Acceleration fallback
    res = sma(df, period=3, acceleration_backend="numba")
    assert "sma_3" in res.output_columns
    assert res.manifest.rollout["selected_implementation"] == "numba"

    # 4. Deprecation validation
    from app.services.indicators.registry import get_indicator

    sma_class = get_indicator("sma")

    # Save original status
    original_status = getattr(sma_class, "status", "official")
    sma_class.status = "deprecated"

    try:
        # Default behavior: raises IND_DEPRECATED
        with pytest.raises(DeprecatedIndicatorError) as exc:
            sma(df, period=3)
        assert exc.value.code == "IND_DEPRECATED"

        # Explicit opt-in
        res_opt = sma(df, period=3, allow_deprecated=True)
        assert "sma_3" in res_opt.output_columns
    finally:
        sma_class.status = original_status


def test_input_mutation_detection():
    """Verify that unexpected in-place input mutation is detected and blocked."""
    from app.services.indicators.errors import InputMutationError
    from app.services.indicators.registry import (
        register_indicator,
        unregister_indicator,
    )

    class MutatingIndicator:
        indicator_id = "mutating_ind"
        name = "Mutating"
        version = "1.0.0"
        formula_version = "1.0.0"
        status = "official"
        dependencies = []

        def validate_parameters(self, parameters: dict[str, Any]) -> None:
            pass

        def required_columns(self, parameters: dict[str, Any]) -> list[str]:
            return ["close"]

        def output_columns(
            self,
            parameters: dict[str, Any],
            source: str | None = None,
            naming_policy: str | None = None,
        ) -> list[str]:
            return ["out"]

        def warmup_requirement(
            self,
            parameters: dict[str, Any],
            timeframe: str,
            calendar: str | None = None,
        ) -> WarmupRequirement:
            return WarmupRequirement("*", timeframe, 1)

        def validate_input(
            self,
            data: pd.DataFrame,
            config: IndicatorConfig,
            context: IndicatorContext | None = None,
        ) -> None:
            pass

        def calculate(
            self,
            data: pd.DataFrame,
            config: IndicatorConfig,
            context: IndicatorContext | None = None,
        ) -> IndicatorResult:
            # Prohibited: mutate the input in place
            data["close"] = data["close"] * 2.0
            res_df = pd.DataFrame(index=data.index)
            res_df["out"] = data["close"]
            from app.services.indicators.protocols import (
                IndicatorManifest,
                IndicatorResult,
            )

            return IndicatorResult(
                values=res_df,
                output_columns=["out"],
                manifest=IndicatorManifest(indicator_id="mutating_ind"),
            )

    register_indicator(MutatingIndicator)
    try:
        df = generate_mock_ohlcv(5)
        # Attempting calculation should raise IND_INPUT_MUTATION_DETECTED
        from app.services.indicators.registry import execute_indicator_workflow

        with pytest.raises(InputMutationError) as exc:
            execute_indicator_workflow("mutating_ind", df, {})
        assert exc.value.code == "IND_INPUT_MUTATION_DETECTED"
    finally:
        unregister_indicator("mutating_ind")


def test_custom_indicator_conformance_checks():
    """Verify custom indicator side-effect conformance validation."""
    from app.services.indicators.errors import CustomIndicatorRejectedError
    from app.services.indicators.registry import register_indicator

    # 1. Custom indicator performing network I/O
    class NetworkIndicator:
        indicator_id = "net_ind"
        name = "Net"
        version = "1.0.0"
        formula_version = "1.0.0"
        status = "experimental"
        dependencies = []

        def validate_parameters(self, p):
            pass

        def required_columns(self, p):
            return ["close"]

        def output_columns(self, p, s=None, n=None):
            return ["out"]

        def warmup_requirement(self, p, tf, c=None):
            return WarmupRequirement("*", tf, 1)

        def validate_input(self, d, c, cx=None):
            pass

        def calculate(self, data, config, context=None):
            import requests

            requests.get("https://example.com")
            res_df = pd.DataFrame(index=data.index)
            res_df["out"] = 1.0
            return IndicatorResult(values=res_df, output_columns=["out"], manifest=None)

    with pytest.raises(CustomIndicatorRejectedError) as exc:
        register_indicator(NetworkIndicator)
    assert exc.value.code == "IND_CUSTOM_INDICATOR_REJECTED"
    assert "Prohibited operation check failed: found network reference" in str(
        exc.value
    )

    # 2. Custom indicator writing to file
    class WritingIndicator:
        indicator_id = "write_ind"
        name = "Write"
        version = "1.0.0"
        formula_version = "1.0.0"
        status = "research-only"
        dependencies = []

        def validate_parameters(self, p):
            pass

        def required_columns(self, p):
            return ["close"]

        def output_columns(self, p, s=None, n=None):
            return ["out"]

        def warmup_requirement(self, p, tf, c=None):
            return WarmupRequirement("*", tf, 1)

        def validate_input(self, d, c, cx=None):
            pass

        def calculate(self, data, config, context=None):
            with open("test.txt", "w") as f:
                f.write("hello")
            res_df = pd.DataFrame(index=data.index)
            res_df["out"] = 1.0
            return IndicatorResult(values=res_df, output_columns=["out"], manifest=None)

    with pytest.raises(CustomIndicatorRejectedError) as exc:
        register_indicator(WritingIndicator)
    assert exc.value.code == "IND_CUSTOM_INDICATOR_REJECTED"
    assert "Prohibited operation check failed: found filesystem reference" in str(
        exc.value
    )
