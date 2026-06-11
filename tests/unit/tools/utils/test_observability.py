"""Unit tests for observability helpers."""

from tools.utils import (
    CircuitBreaker,
    MetricRegistry,
    build_health_snapshot,
    check_clock_drift_health,
    export_prometheus_metrics,
    record_metric,
    record_tool_call_metric,
)


def test_metric_registry_and_prometheus_export() -> None:
    """Metrics validate labels and export Prometheus-compatible text."""
    registry = MetricRegistry()
    record_metric(
        registry,
        name="haruquant_test_total",
        kind="counter",
        value=1,
        labels={"component": "utils"},
    )
    record_tool_call_metric(
        registry,
        tool_name="validate_input_schema",
        status="success",
        latency_ms=1.5,
    )

    exported = export_prometheus_metrics(registry)
    assert "haruquant_test_total" in exported
    assert "haruquant_tool_latency_ms" in exported


def test_health_clock_drift_and_circuit_breaker() -> None:
    """Health snapshots cover healthy, degraded, critical, and unsupported."""
    registry = MetricRegistry()
    breaker = CircuitBreaker(
        name="provider",
        failure_threshold=2,
        cooldown_seconds=0,
        registry=registry,
    )

    assert (
        build_health_snapshot(component="utils", status="healthy")["status"]
        == "healthy"
    )
    assert (
        check_clock_drift_health(
            observed_offset_seconds=None,
            warning_threshold_seconds=1,
            critical_threshold_seconds=2,
        )["status"]
        == "unsupported"
    )
    assert (
        check_clock_drift_health(
            observed_offset_seconds=1.5,
            warning_threshold_seconds=1,
            critical_threshold_seconds=2,
        )["status"]
        == "degraded"
    )
    assert (
        check_clock_drift_health(
            observed_offset_seconds=3,
            warning_threshold_seconds=1,
            critical_threshold_seconds=2,
        )["status"]
        == "critical"
    )

    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == "open"
    assert breaker.allow_request() is True
    assert str(breaker.state) == "half_open"
    breaker.record_success()
    assert str(breaker.state) == "closed"
