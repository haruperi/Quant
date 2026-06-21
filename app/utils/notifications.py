"""Notification routing primitives with fake/local adapters only.

The utilities layer decides routing mechanics, redaction, throttling, and
deduplication. It does not send live email, Telegram, webhook, or desktop
messages unless a caller supplies an explicit adapter.

Public exports:
    NotificationMessage, NotificationResult, NotificationAdapter,
    FakeNotificationAdapter, NotificationRouter,
    render_notification, route_notification, broadcast_notification.

Side effects:
    None on import. All I/O is deferred to caller-supplied adapters.
"""

from __future__ import annotations

import json
import smtplib
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from email.message import EmailMessage
from threading import RLock
from typing import Literal, Protocol, TypedDict

from app.utils.errors import ConfigurationError, ExternalServiceError, ValidationError
from app.utils.logger import logger
from app.utils.security import redact_mapping, redact_text

NotificationChannel = Literal["email", "telegram", "desktop", "webhook"]
NotificationStatus = Literal[
    "sent", "failed", "suppressed", "throttled", "deduplicated"
]
NotificationSeverity = Literal["info", "warning", "error", "critical"]


class NotificationMessage(TypedDict):
    """Sanitized notification message payload."""

    title: str
    body: str
    severity: NotificationSeverity
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class NotificationResult:
    """Result from a notification routing attempt."""

    status: NotificationStatus
    message: str
    channel: NotificationChannel
    provider: str
    latency_ms: float


class NotificationAdapter(Protocol):
    """Adapter interface for caller-owned notification transports."""

    provider_name: str
    channel: NotificationChannel

    def send(self, message: NotificationMessage, *, timeout_seconds: float) -> None:
        """Send a sanitized message through the adapter."""


@dataclass
class FakeNotificationAdapter:
    """Thread-safe fake notification adapter for tests and local usage."""

    channel: NotificationChannel
    provider_name: str = "fake"
    fail: bool = False
    sent_messages: list[NotificationMessage] = field(default_factory=list)
    _lock: RLock = field(default_factory=RLock)

    def send(self, message: NotificationMessage, *, timeout_seconds: float) -> None:
        """Record or fail a fake notification send."""
        if timeout_seconds <= 0:
            raise ExternalServiceError("notification send timed out.", code="TIMEOUT")
        if self.fail:
            raise ExternalServiceError("notification provider failed.")
        with self._lock:
            self.sent_messages.append(message)


@dataclass
class NotificationRouter:
    """Thread-safe notification router with throttling and deduplication."""

    adapters: Mapping[NotificationChannel, NotificationAdapter]
    enabled_channels: set[NotificationChannel] = field(default_factory=set)
    throttle_seconds: float = 0.0
    dedupe_window_seconds: float = 60.0
    _last_sent: dict[NotificationChannel, float] = field(default_factory=dict)
    _dedupe: dict[str, float] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)

    def __post_init__(self) -> None:
        """Default enabled channels to available adapters."""
        if not self.enabled_channels:
            self.enabled_channels = set(self.adapters.keys())

    def route(
        self,
        *,
        channel: NotificationChannel,
        title: str,
        body: str,
        severity: NotificationSeverity = "info",
        metadata: Mapping[str, object] | None = None,
        dedupe_key: str | None = None,
        timeout_seconds: float = 5.0,
    ) -> NotificationResult:
        """Route a sanitized notification to a registered channel adapter.

        Applies throttle and deduplication guards before dispatching.
        The adapter is called outside the internal lock to prevent
        deadlocks on slow I/O.

        Args:
            channel: Target notification channel.
            title: Notification title. Will be redacted of secret material.
            body: Notification body. Will be redacted of secret material.
            severity: Notification severity level. Defaults to ``"info"``.
            metadata: Optional metadata mapping. Will be redacted.
            dedupe_key: Optional deduplication key. Identical keys within
                ``dedupe_window_seconds`` are suppressed.
            timeout_seconds: Adapter send timeout in seconds.
                Defaults to 5.0.

        Returns:
            ``NotificationResult`` with status, provider, and latency.

        Raises:
            ValidationError: If channel, severity, title, or body is
                invalid.
            ConfigurationError: If no adapter is registered for the
                channel.

        Side effects:
            Calls ``adapter.send()``; mutates throttle and dedupe state.
            Provider credentials are never logged.
        """
        start = time.perf_counter()
        if channel not in {"email", "telegram", "desktop", "webhook"}:
            raise ValidationError("notification channel is invalid.")
        if severity not in {"info", "warning", "error", "critical"}:
            raise ValidationError("notification severity is invalid.")
        if not title.strip() or not body.strip():
            raise ValidationError("notification title and body are required.")

        with self._lock:
            if channel not in self.enabled_channels:
                return _result(
                    "suppressed",
                    "notification channel disabled",
                    channel,
                    "none",
                    start,
                )
            adapter = self.adapters.get(channel)
            if adapter is None:
                raise ConfigurationError("notification adapter is not configured.")
            now = time.monotonic()
            previous_send = self._last_sent.get(channel)
            if (
                previous_send is not None
                and now - previous_send < self.throttle_seconds
            ):
                return _result(
                    "throttled",
                    "notification throttled",
                    channel,
                    adapter.provider_name,
                    start,
                )
            if dedupe_key:
                previous = self._dedupe.get(dedupe_key)
                if previous is not None and now - previous < self.dedupe_window_seconds:
                    return _result(
                        "deduplicated",
                        "duplicate notification suppressed",
                        channel,
                        adapter.provider_name,
                        start,
                    )
                self._dedupe[dedupe_key] = now
            self._last_sent[channel] = now

        message = render_notification(
            title=title,
            body=body,
            severity=severity,
            metadata=metadata or {},
        )
        try:
            adapter.send(message, timeout_seconds=timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "notification provider failed",
                extra={
                    "event_name": "notification_failed",
                    "error_code": getattr(exc, "code", "TOOL_EXECUTION_FAILED"),
                },
            )
            return _result(
                "failed",
                "notification provider failed",
                channel,
                adapter.provider_name,
                start,
            )
        logger.info(
            "notification routed",
            extra={
                "event_name": "notification_sent",
                "request_id": message["metadata"].get("request_id"),
            },
        )
        return _result(
            "sent", "notification sent", channel, adapter.provider_name, start
        )


def _result(
    status: NotificationStatus,
    message: str,
    channel: NotificationChannel,
    provider: str,
    start: float,
) -> NotificationResult:
    """Build a notification result."""
    return NotificationResult(
        status=status,
        message=message,
        channel=channel,
        provider=provider,
        latency_ms=round((time.perf_counter() - start) * 1000, 3),
    )


def render_notification(
    *,
    title: str,
    body: str,
    severity: NotificationSeverity = "info",
    metadata: Mapping[str, object] | None = None,
    markdown: bool = False,
) -> NotificationMessage:
    """Render a sanitized notification with optional markdown-safe fallback."""
    safe_title = redact_text(title.strip())
    safe_body = redact_text(body.strip())
    if not markdown:
        safe_body = safe_body.replace("**", "").replace("__", "")
    return {
        "title": safe_title,
        "body": safe_body,
        "severity": severity,
        "metadata": redact_mapping(metadata or {}),
    }


def route_notification(
    router: NotificationRouter,
    *,
    channel: NotificationChannel,
    title: str,
    body: str,
    severity: NotificationSeverity = "info",
    metadata: Mapping[str, object] | None = None,
    dedupe_key: str | None = None,
) -> NotificationResult:
    """Route a notification through a caller-owned router."""
    return router.route(
        channel=channel,
        title=title,
        body=body,
        severity=severity,
        metadata=metadata,
        dedupe_key=dedupe_key,
    )


def broadcast_notification(
    router: NotificationRouter,
    *,
    channels: Sequence[NotificationChannel],
    title: str,
    body: str,
    severity: NotificationSeverity = "info",
) -> list[NotificationResult]:
    """Route one sanitized notification to multiple channels."""
    return [
        router.route(channel=channel, title=title, body=body, severity=severity)
        for channel in channels
    ]


class DesktopNotificationAdapter:
    """Thread-safe adapter for native desktop notifications.

    Supports Windows (via PowerShell), macOS (via AppleScript), and
    Linux (via notify-send).
    """

    provider_name: str = "desktop"
    channel: NotificationChannel = "desktop"

    def send(self, message: NotificationMessage, *, timeout_seconds: float) -> None:
        """Send a native desktop notification to the host operating system.

        Args:
            message: The notification message dictionary.
            timeout_seconds: Timeout ceiling for the external subprocess command.

        Raises:
            ExternalServiceError: If the shell notification execution fails
                or times out.
        """
        title = message["title"]
        body = message["body"]

        if sys.platform == "win32":
            # Windows: Run PowerShell to trigger standard NotifyIcon BalloonTip
            ps_script = (
                "[void] [System.Reflection.Assembly]::"
                "LoadWithPartialName('System.Windows.Forms'); "
                "$notification = New-Object System.Windows.Forms.NotifyIcon; "
                "$notification.Icon = [System.Drawing.SystemIcons]::Information; "
                "$notification.BalloonTipIcon = 'Info'; "
                f"$notification.BalloonTipTitle = {self._ps_quote(title)}; "
                f"$notification.BalloonTipText = {self._ps_quote(body)}; "
                "$notification.Visible = $True; "
                "$notification.ShowBalloonTip(10000); "
                "Start-Sleep -Seconds 1"
            )
            try:
                subprocess.run(  # noqa: S603
                    ["powershell", "-Command", ps_script],  # noqa: S607
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as e:
                raise ExternalServiceError(
                    "PowerShell notification command timed out.",
                    code="TIMEOUT",
                ) from e
            except Exception as e:
                msg = f"Failed to send Windows notification: {e}"
                raise ExternalServiceError(msg) from e
        elif sys.platform == "darwin":
            # macOS: AppleScript notification
            escaped_body = body.replace('"', '\\"')
            escaped_title = title.replace('"', '\\"')
            script = (
                f'display notification "{escaped_body}" with title "{escaped_title}"'
            )
            try:
                subprocess.run(  # noqa: S603
                    ["osascript", "-e", script],  # noqa: S607
                    capture_output=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except Exception as e:
                msg = f"Failed to send macOS notification: {e}"
                raise ExternalServiceError(msg) from e
        else:
            # Linux / Unix: notify-send
            try:
                subprocess.run(  # noqa: S603
                    ["notify-send", title, body],  # noqa: S607
                    capture_output=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except Exception as e:
                msg = f"Failed to send Linux notification: {e}"
                raise ExternalServiceError(msg) from e

    def _ps_quote(self, s: str) -> str:
        """Helper to escape and single-quote string for PowerShell command lines."""
        escaped = s.replace("'", "''")
        return f"'{escaped}'"


class TelegramNotificationAdapter:
    """Thread-safe adapter for sending Telegram messages via the Bot API."""

    provider_name: str = "telegram"
    channel: NotificationChannel = "telegram"

    def __init__(self, bot_token: str, chat_id: str) -> None:
        """Initialize the Telegram adapter.

        Args:
            bot_token: Secret bot authorization token.
            chat_id: Target channel/user ID.
        """
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, message: NotificationMessage, *, timeout_seconds: float) -> None:
        """Send a message to the configured Telegram chat.

        Args:
            message: The notification message payload.
            timeout_seconds: HTTP client request timeout.

        Raises:
            ConfigurationError: If the bot credentials are missing.
            ExternalServiceError: If the Telegram Bot API call fails.
        """
        if not self.bot_token or not self.chat_id:
            msg = "Telegram bot token and chat ID must be configured."
            raise ConfigurationError(msg)

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        text = f"<b>{message['title']}</b>\n\n{message['body']}"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as response:  # noqa: S310
                response.read()
        except urllib.error.URLError as e:
            msg = f"Telegram API request failed: {e}"
            raise ExternalServiceError(msg) from e


class EmailNotificationAdapter:
    """Thread-safe adapter for sending email messages via SMTP."""

    provider_name: str = "smtp"
    channel: NotificationChannel = "email"

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        recipient: str | None = None,
    ) -> None:
        """Initialize the SMTP email adapter.

        Args:
            host: SMTP server address.
            port: SMTP connection port.
            username: Sender email username.
            password: Sender email password.
            recipient: Target recipient email. Defaults to username.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.recipient = recipient or username

    def send(self, message: NotificationMessage, *, timeout_seconds: float) -> None:
        """Send an email through the SMTP gateway.

        Args:
            message: The notification message payload.
            timeout_seconds: Connection and communication timeout.

        Raises:
            ConfigurationError: If required credentials or host
                configurations are missing.
            ExternalServiceError: If sending email fails.
        """
        if not self.host or not self.port:
            raise ConfigurationError("SMTP host and port must be configured.")

        msg = EmailMessage()
        msg.set_content(message["body"])
        msg["Subject"] = message["title"]
        msg["From"] = self.username or "HaruQuant <no-reply@haruquant.com>"
        msg["To"] = self.recipient or self.username

        try:
            # Connect via SMTP
            with smtplib.SMTP(self.host, self.port, timeout=timeout_seconds) as server:
                if self.port == 587:  # noqa: PLR2004
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
        except Exception as e:
            err_msg = f"Email SMTP send failed: {e}"
            raise ExternalServiceError(err_msg) from e
