"""Unit tests for notification helpers."""

import subprocess
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from app.utils import (
    DesktopNotificationAdapter,
    EmailNotificationAdapter,
    FakeNotificationAdapter,
    NotificationMessage,
    NotificationRouter,
    TelegramNotificationAdapter,
    broadcast_notification,
    render_notification,
    route_notification,
)
from app.utils.errors import ConfigurationError, ExternalServiceError


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


def test_desktop_notification_windows() -> None:
    adapter = DesktopNotificationAdapter()
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }

    with patch("sys.platform", "win32"), patch("subprocess.run") as mock_run:
        adapter.send(message, timeout_seconds=5.0)
        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "powershell" in args[0]
        assert "Test Title" in args[0][2]
        assert "Test Body" in args[0][2]


def test_desktop_notification_macos() -> None:
    adapter = DesktopNotificationAdapter()
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }

    with patch("sys.platform", "darwin"), patch("subprocess.run") as mock_run:
        adapter.send(message, timeout_seconds=5.0)
        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "osascript" in args[0]
        assert "Test Title" in args[0][2]
        assert "Test Body" in args[0][2]


def test_desktop_notification_linux() -> None:
    adapter = DesktopNotificationAdapter()
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }

    with patch("sys.platform", "linux"), patch("subprocess.run") as mock_run:
        adapter.send(message, timeout_seconds=5.0)
        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert args[0] == ["notify-send", "Test Title", "Test Body"]


def test_desktop_notification_failures() -> None:
    adapter = DesktopNotificationAdapter()
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }

    # Timeout
    with (
        patch("sys.platform", "win32"),
        patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=[], timeout=5.0),
        ),
    ):
        with pytest.raises(ExternalServiceError) as exc_info:
            adapter.send(message, timeout_seconds=5.0)
        assert exc_info.value.code == "TIMEOUT"

    # General failure
    with (
        patch("sys.platform", "win32"),
        patch("subprocess.run", side_effect=ValueError("OS error")),
    ):
        with pytest.raises(ExternalServiceError) as exc_info:
            adapter.send(message, timeout_seconds=5.0)
        assert "OS error" in str(exc_info.value)


def test_telegram_notification_success() -> None:
    adapter = TelegramNotificationAdapter(
        bot_token="fake_token",  # pragma: allowlist secret
        chat_id="fake_chat",
    )
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }

    mock_response = MagicMock()
    mock_response.read.return_value = b"success"

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        adapter.send(message, timeout_seconds=5.0)
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == ("https://api.telegram.org/botfake_token/sendMessage")
        assert req.data is not None
        assert req.method == "POST"


def test_telegram_notification_missing_credentials() -> None:
    adapter = TelegramNotificationAdapter(bot_token="", chat_id="")
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }
    with pytest.raises(ConfigurationError):
        adapter.send(message, timeout_seconds=5.0)


def test_telegram_notification_api_failure() -> None:
    adapter = TelegramNotificationAdapter(
        bot_token="fake_token",  # pragma: allowlist secret
        chat_id="fake_chat",
    )
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }

    with (
        patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("API failure"),
        ),
        pytest.raises(ExternalServiceError),
    ):
        adapter.send(message, timeout_seconds=5.0)


def test_email_notification_success() -> None:
    adapter = EmailNotificationAdapter(
        host="smtp.gmail.com",
        port=587,
        username="user@gmail.com",
        password="password",  # pragma: allowlist secret
        recipient="to@gmail.com",
    )
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }

    mock_smtp = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        adapter.send(message, timeout_seconds=5.0)

        mock_smtp_class.assert_called_once_with(
            "smtp.gmail.com",
            587,
            timeout=5.0,
        )
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user@gmail.com", "password")
        mock_smtp.send_message.assert_called_once()


def test_email_notification_missing_config() -> None:
    adapter = EmailNotificationAdapter(
        host="",
        port=0,
        username="",
        password="",
    )
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }
    with pytest.raises(ConfigurationError):
        adapter.send(message, timeout_seconds=5.0)


def test_email_notification_smtp_failure() -> None:
    adapter = EmailNotificationAdapter(
        host="smtp.gmail.com",
        port=587,
        username="user@gmail.com",
        password="password",  # pragma: allowlist secret
    )
    message: NotificationMessage = {
        "title": "Test Title",
        "body": "Test Body",
        "severity": "info",
        "metadata": {},
    }

    with (
        patch("smtplib.SMTP", side_effect=Exception("SMTP error")),
        pytest.raises(ExternalServiceError),
    ):
        adapter.send(message, timeout_seconds=5.0)
