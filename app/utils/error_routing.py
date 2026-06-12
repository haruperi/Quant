"""Error routing and alert suppression helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from app.core.security import redact_mapping, redact_text
from app.utils.errors import ErrorPayload, exception_to_error_payload
from app.utils.event_bus import InMemoryEventBus, build_event_envelope

RouteStatus = Literal["routed", "suppressed", "failed"]


@dataclass(frozen=True, slots=True)
class ErrorRouteResult:
    """Error routing result."""

    status: RouteStatus
    message: str
    route_key: str
    event_id: str | None


@dataclass
class ErrorRouter:
    """Bounded deduplicating error router."""

    bus: InMemoryEventBus
    dedupe_window_seconds: float = 60.0
    _last_seen: dict[str, float] = field(default_factory=dict)

    def route_error(
        self,
        *,
        error: BaseException | ErrorPayload,
        source: str,
        request_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ErrorRouteResult:
        """Route an error event unless it is suppressed by deduplication."""
        payload = (
            error if isinstance(error, dict) else exception_to_error_payload(error)
        )
        route_key = f"{source}:{payload['code']}:{redact_text(payload['details'])}"
        now = time.monotonic()
        previous = self._last_seen.get(route_key)
        if previous is not None and now - previous < self.dedupe_window_seconds:
            return ErrorRouteResult(
                "suppressed", "duplicate error suppressed", route_key, None
            )
        self._last_seen[route_key] = now
        event = build_event_envelope(
            event_type="utility.error",
            source=source,
            severity="error",
            request_id=request_id,
            payload={
                "code": payload["code"],
                "details": redact_text(payload["details"]),
            },
            metadata=redact_mapping(metadata or {}),
            idempotency_key=route_key,
        )
        result = self.bus.publish(event)
        if result.status in {"delivered", "duplicate"}:
            return ErrorRouteResult(
                "routed", "error routed", route_key, event["event_id"]
            )
        return ErrorRouteResult("failed", result.message, route_key, event["event_id"])


def route_error(
    error: BaseException | ErrorPayload,
    *,
    source: str,
    bus: InMemoryEventBus | None = None,
    request_id: str | None = None,
) -> ErrorRouteResult:
    """Route an error through a caller-supplied or temporary in-memory bus."""
    router = ErrorRouter(bus=bus or InMemoryEventBus())
    return router.route_error(error=error, source=source, request_id=request_id)
