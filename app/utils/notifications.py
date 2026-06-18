"""Notification routing primitives with fake/local adapters only.

The utilities layer decides routing mechanics, redaction, throttling, and
deduplication. It does not send live email, Telegram, webhook, or desktop
messages unless a caller supplies an explicit adapter.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
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
        """Route a notification to an enabled caller-owned adapter."""
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
