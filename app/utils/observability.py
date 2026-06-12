"""Metrics, health, clock-drift, and circuit-breaker primitives.

This module is import-safe without Prometheus. Metrics are recorded in a
caller-owned in-memory registry and can be exported to a Prometheus-compatible
text format without external services.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from threading import RLock
from typing import Literal, TypedDict

from app.utils.errors import ExternalServiceError, ValidationError
from app.utils.logger import logger
from app.utils.normalization import format_utc_timestamp, utc_now
from app.utils.standard import validate_metric_labels

MetricKind = Literal["counter", "gauge", "histogram"]
HealthStatus = Literal[
    "healthy", "degraded", "critical", "unsupported", "not_configured"
]
CircuitState = Literal["closed", "open", "half_open"]

GRAFANA_DASHBOARD_EXPECTATIONS = (
    "system_health",
    "tool_health",
    "event_bus_health",
    "notification_health",
    "error_routing",
    "auth_failures",
    "data_quality_validation_health",
)


class MetricRecord(TypedDict):
    """Stored metric sample."""

    name: str
    kind: MetricKind
    value: float
    labels: dict[str, str]
    timestamp: str


class HealthSnapshot(TypedDict):
    """Sanitized component health snapshot."""

    component: str
    status: HealthStatus
    details: dict[str, object]
    last_error_at: str | None
    last_success_at: str | None
    degraded: bool
    critical: bool


@dataclass
class MetricRegistry:
    """Thread-safe in-memory metric registry."""

    records: list[MetricRecord] = field(default_factory=list)
    _lock: RLock = field(default_factory=RLock)

    def record(
        self,
        *,
        name: str,
        kind: MetricKind,
        value: float,
        labels: Mapping[str, object] | None = None,
    ) -> MetricRecord:
        """Record one metric sample after label validation."""
        if kind not in {"counter", "gauge", "histogram"}:
            raise ValidationError("metric kind is invalid.")
        if not name.strip():
            raise ValidationError("metric name must be non-empty.")
        if not isinstance(value, int | float):
            raise ValidationError("metric value must be numeric.")
        safe_labels = validate_metric_labels(labels or {})
        record: MetricRecord = {
            "name": name,
            "kind": kind,
            "value": float(value),
            "labels": safe_labels,
            "timestamp": format_utc_timestamp(utc_now()),
        }
        with self._lock:
            self.records.append(record)
        return record

    def export_prometheus_text(self) -> str:
        """Export recorded metrics in Prometheus-compatible text format."""
        with self._lock:
            rows = list(self.records)
        lines: list[str] = []
        for record in rows:
            labels = ",".join(
                f'{key}="{value}"' for key, value in sorted(record["labels"].items())
            )
            suffix = f"{{{labels}}}" if labels else ""
            lines.append(f"# TYPE {record['name']} {record['kind']}")
            lines.append(f"{record['name']}{suffix} {record['value']}")
        return "\n".join(lines)


@dataclass
class CircuitBreaker:
    """Thread-safe circuit breaker with closed/open/half-open states."""

    name: str
    failure_threshold: int = 3
    cooldown_seconds: float = 30.0
    registry: MetricRegistry | None = None
    state: CircuitState = "closed"
    consecutive_failures: int = 0
    opened_at: float | None = None
    _lock: RLock = field(default_factory=RLock)

    def allow_request(self) -> bool:
        """Return whether work may proceed through the circuit."""
        with self._lock:
            if self.state != "open":
                return True
            if self.opened_at is None:
                return False
            if time.monotonic() - self.opened_at >= self.cooldown_seconds:
                self._transition("half_open")
                return True
            return False

    def record_success(self) -> None:
        """Record a successful provider attempt."""
        with self._lock:
            self.consecutive_failures = 0
            self.opened_at = None
            self._transition("closed")

    def record_failure(self) -> None:
        """Record a failed provider attempt and open if threshold is reached."""
        with self._lock:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.failure_threshold:
                self.opened_at = time.monotonic()
                self._transition("open")

    def _transition(self, state: CircuitState) -> None:
        """Transition state and record observable metrics."""
        if self.state == state:
            return
        self.state = state
        logger.warning(
            "circuit breaker state transition",
            extra={"event_name": "circuit_state_changed"},
        )
        if self.registry is not None:
            self.registry.record(
                name="haruquant_circuit_breaker_state",
                kind="gauge",
                value={"closed": 0.0, "half_open": 0.5, "open": 1.0}[state],
                labels={"component": self.name, "state": state},
            )


def record_metric(
    registry: MetricRegistry,
    *,
    name: str,
    kind: MetricKind,
    value: float,
    labels: Mapping[str, object] | None = None,
) -> MetricRecord:
    """Record a metric without external dependencies."""
    return registry.record(name=name, kind=kind, value=value, labels=labels)


def record_tool_call_metric(
    registry: MetricRegistry,
    *,
    tool_name: str,
    status: Literal["success", "error"],
    latency_ms: float,
) -> list[MetricRecord]:
    """Record standard tool call count and latency metrics."""
    return [
        registry.record(
            name="haruquant_tool_calls_total",
            kind="counter",
            value=1.0,
            labels={"tool": tool_name, "status": status},
        ),
        registry.record(
            name="haruquant_tool_latency_ms",
            kind="histogram",
            value=latency_ms,
            labels={"tool": tool_name, "status": status},
        ),
    ]


def build_health_snapshot(
    *,
    component: str,
    status: HealthStatus,
    details: Mapping[str, object] | None = None,
    last_error_at: str | None = None,
    last_success_at: str | None = None,
) -> HealthSnapshot:
    """Build a sanitized component health snapshot."""
    if status not in {
        "healthy",
        "degraded",
        "critical",
        "unsupported",
        "not_configured",
    }:
        raise ValidationError("health status is invalid.")
    if not component.strip():
        raise ValidationError("component must be non-empty.")
    safe_details = {
        key: value
        for key, value in (details or {}).items()
        if "token" not in key.lower() and "secret" not in key.lower()
    }
    return {
        "component": component,
        "status": status,
        "details": safe_details,
        "last_error_at": last_error_at,
        "last_success_at": last_success_at,
        "degraded": status == "degraded",
        "critical": status == "critical",
    }


def check_clock_drift_health(
    *,
    observed_offset_seconds: float | None,
    warning_threshold_seconds: float,
    critical_threshold_seconds: float,
    source: str = "system_clock",
) -> HealthSnapshot:
    """Return health status for wall-clock drift."""
    if observed_offset_seconds is None:
        return build_health_snapshot(
            component=source,
            status="unsupported",
            details={"reason": "clock drift source is not configured"},
        )
    offset = abs(float(observed_offset_seconds))
    if offset >= critical_threshold_seconds:
        status: HealthStatus = "critical"
    elif offset >= warning_threshold_seconds:
        status = "degraded"
    else:
        status = "healthy"
    if status in {"degraded", "critical"}:
        logger.warning(
            "clock drift detected",
            extra={
                "event_name": "clock_drift_detected",
                "error_code": "CLOCK_DRIFT_DETECTED",
            },
        )
    return build_health_snapshot(
        component=source,
        status=status,
        details={
            "offset_seconds": observed_offset_seconds,
            "warning_threshold_seconds": warning_threshold_seconds,
            "critical_threshold_seconds": critical_threshold_seconds,
            "timestamp": format_utc_timestamp(utc_now()),
        },
    )


def export_prometheus_metrics(registry: MetricRegistry) -> str:
    """Export registry metrics as Prometheus-compatible text."""
    try:
        return registry.export_prometheus_text()
    except Exception as exc:
        logger.warning(
            "observability export failed",
            extra={
                "event_name": "observability_export_failed",
                "error_code": "OBSERVABILITY_ERROR",
            },
        )
        raise ExternalServiceError(
            "observability export failed.", code="OBSERVABILITY_ERROR"
        ) from exc
