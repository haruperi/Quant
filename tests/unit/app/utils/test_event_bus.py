"""Unit tests for Event Bus helpers."""

from typing import cast

from app.utils import (
    EventEnvelope,
    InMemoryEventBus,
    build_event_envelope,
    publish_event,
)


def test_event_bus_publish_duplicate_and_conflict() -> None:
    """Event Bus handles delivery, duplicate idempotency, and conflicts."""
    received: list[dict[str, object]] = []
    bus = InMemoryEventBus(max_queue_size=2)
    bus.subscribe("utility.test", received.append)
    event = build_event_envelope(
        event_type="utility.test",
        source="unit",
        payload={"token": "secret"},
        idempotency_key="idem-1",
    )
    duplicate = cast("EventEnvelope", dict(event))
    conflict = cast("EventEnvelope", dict(event))
    conflict["event_id"] = "event_conflict"

    assert publish_event(bus, event).status == "delivered"
    assert publish_event(bus, duplicate).status == "duplicate"
    assert publish_event(bus, conflict).status == "conflict"
    payload = received[0]["payload"]
    assert isinstance(payload, dict)
    assert payload["token"] == "[REDACTED]"


def test_event_bus_queue_full_drops() -> None:
    """Bounded queues fail fast when full."""
    bus = InMemoryEventBus(max_queue_size=1)
    first = build_event_envelope(event_type="a", source="unit", payload={})
    second = build_event_envelope(event_type="b", source="unit", payload={})

    assert bus.publish(first).status == "delivered"
    assert bus.publish(second).status == "dropped"
