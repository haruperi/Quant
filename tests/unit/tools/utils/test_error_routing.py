"""Unit tests for error routing helpers."""

from tools.utils import ErrorRouter, InMemoryEventBus, ValidationError, route_error


def test_error_router_routes_and_suppresses_duplicates() -> None:
    """Repeated errors are suppressed within the dedupe window."""
    bus = InMemoryEventBus()
    router = ErrorRouter(bus=bus, dedupe_window_seconds=60)

    first = router.route_error(error=ValidationError("bad token=secret"), source="unit")
    second = router.route_error(
        error=ValidationError("bad token=secret"), source="unit"
    )

    assert first.status == "routed"
    assert second.status == "suppressed"
    assert "secret" not in first.route_key


def test_route_error_helper_uses_temporary_bus() -> None:
    """Top-level route helper returns a deterministic result."""
    result = route_error({"code": "INVALID_INPUT", "details": "bad"}, source="unit")

    assert result.status == "routed"
