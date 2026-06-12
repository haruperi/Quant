"""Unit tests for notification helpers."""

from app.utils import (
    FakeNotificationAdapter,
    NotificationRouter,
    broadcast_notification,
    render_notification,
    route_notification,
)


def test_notification_routing_fake_adapter_and_suppression() -> None:
    """Fake adapters cover sent, disabled, throttled, and dedupe paths."""
    adapter = FakeNotificationAdapter(channel="email")
    router = NotificationRouter(
        adapters={"email": adapter},
        throttle_seconds=10,
        dedupe_window_seconds=10,
    )
    sent = route_notification(
        router,
        channel="email",
        title="Alert",
        body="token=abcdef1234567890abcdef1234567890",
        dedupe_key="a",
    )
    throttled = route_notification(router, channel="email", title="Alert", body="Again")

    assert sent.status == "sent"
    assert throttled.status == "throttled"
    assert "[REDACTED]" in adapter.sent_messages[0]["body"]


def test_notification_disabled_failure_and_rendering() -> None:
    """Notifications support disabled channels, fake failures, and rendering."""
    failing = FakeNotificationAdapter(channel="desktop", fail=True)
    router = NotificationRouter(adapters={"desktop": failing})
    router.enabled_channels = set()
    disabled = route_notification(router, channel="desktop", title="A", body="B")
    router.enabled_channels.add("desktop")
    failed = route_notification(router, channel="desktop", title="A", body="B")
    rendered = render_notification(title="T", body="**secret=abc**", markdown=False)
    broadcast = broadcast_notification(
        router, channels=["desktop"], title="A", body="B"
    )

    assert disabled.status == "suppressed"
    assert failed.status == "failed"
    assert "**" not in rendered["body"]
    assert broadcast[0].status == "failed"
