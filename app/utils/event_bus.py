"""In-memory Event Bus and pub/sub primitives for utilities."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from threading import RLock
from typing import Literal, TypedDict

from app.core.security import redact_mapping
from app.utils.errors import ValidationError
from app.utils.identity import generate_event_id
from app.utils.normalization import format_utc_timestamp, utc_now

EventSeverity = Literal["info", "warning", "error", "critical"]
DeliveryStatus = Literal["delivered", "failed", "dropped", "duplicate", "conflict"]
EventHandler = Callable[[dict[str, object]], None]


class EventEnvelope(TypedDict):
    """Standard utility event envelope."""

    event_id: str
    event_type: str
    event_version: str
    source: str
    severity: EventSeverity
    timestamp: str
    request_id: str | None
    correlation_id: str | None
    causation_id: str | None
    idempotency_key: str | None
    payload: dict[str, object]
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Event publish result."""

    status: DeliveryStatus
    message: str
    event_id: str | None
    delivered_count: int = 0
    failed_count: int = 0


@dataclass
class InMemoryEventBus:
    """Thread-safe bounded in-memory Event Bus for tests and local workflows."""

    max_queue_size: int = 1000
    fail_fast_when_full: bool = True
    _handlers: dict[str, list[EventHandler]] = field(default_factory=dict)
    _queue: deque[EventEnvelope] = field(default_factory=deque)
    _idempotency: dict[str, str] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register an event handler."""
        if not event_type.strip():
            raise ValidationError("event_type must be non-empty.", code="INVALID_INPUT")
        with self._lock:
            self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unregister an event handler if present."""
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            self._handlers[event_type] = [item for item in handlers if item != handler]

    def publish(self, event: EventEnvelope) -> PublishResult:
        """Publish an event to registered handlers."""
        with self._lock:
            key = event.get("idempotency_key")
            material = str(event.get("event_id"))
            if key is not None and key in self._idempotency:
                if self._idempotency[key] == material:
                    return PublishResult(
                        "duplicate", "duplicate event ignored", event["event_id"]
                    )
                return PublishResult(
                    "conflict", "idempotency conflict", event["event_id"]
                )
            if len(self._queue) >= self.max_queue_size:
                if self.fail_fast_when_full:
                    return PublishResult(
                        "dropped", "event queue is full", event["event_id"]
                    )
                self._queue.popleft()
            self._queue.append(event)
            if key is not None:
                self._idempotency[key] = material
            handlers = list(self._handlers.get(event["event_type"], []))
        delivered = 0
        failed = 0
        for handler in handlers:
            try:
                handler(dict(event))
                delivered += 1
            except Exception:  # noqa: BLE001
                failed += 1
        status: DeliveryStatus = "failed" if failed else "delivered"
        return PublishResult(
            status, "event published", event["event_id"], delivered, failed
        )

    def queue_depth(self) -> int:
        """Return current queue depth."""
        with self._lock:
            return len(self._queue)

    def idempotency_size(self) -> int:
        """Return idempotency cache size."""
        with self._lock:
            return len(self._idempotency)


def build_event_envelope(
    *,
    event_type: str,
    source: str,
    payload: Mapping[str, object],
    severity: EventSeverity = "info",
    event_version: str = "1.0.0",
    request_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    idempotency_key: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> EventEnvelope:
    """Build a sanitized utility event envelope."""
    if not event_type.strip():
        raise ValidationError("event_type must be non-empty.", code="INVALID_INPUT")
    if not source.strip():
        raise ValidationError("source must be non-empty.", code="INVALID_INPUT")
    if severity not in {"info", "warning", "error", "critical"}:
        raise ValidationError("severity is invalid.", code="INVALID_INPUT")
    return {
        "event_id": generate_event_id(),
        "event_type": event_type,
        "event_version": event_version,
        "source": source,
        "severity": severity,
        "timestamp": format_utc_timestamp(utc_now()),
        "request_id": request_id,
        "correlation_id": correlation_id,
        "causation_id": causation_id,
        "idempotency_key": idempotency_key,
        "payload": redact_mapping(payload),
        "metadata": redact_mapping(metadata or {}),
    }


def publish_event(
    bus: InMemoryEventBus,
    event: EventEnvelope,
    *,
    timeout_seconds: float | None = None,
) -> PublishResult:
    """Publish an event through a caller-owned bus."""
    start = time.perf_counter()
    result = bus.publish(event)
    if timeout_seconds is not None and time.perf_counter() - start > timeout_seconds:
        return PublishResult("failed", "event publish timed out", event["event_id"])
    return result
