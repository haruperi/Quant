# ruff: noqa: E501, PYI036, ANN401
"""Distributed tracing adapter compatible with OpenTelemetry W3C traceparent propagation."""

from __future__ import annotations

import re
import time
import uuid
from typing import Any, Self

from app.utils.logger import logger

# Regex to match standard W3C traceparent header format:
# version-trace_id-parent_id-trace_flags
# example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
TRACEPARENT_RE = re.compile(
    r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$"
)


def parse_traceparent(traceparent: str) -> dict[str, str] | None:
    """Parse W3C traceparent header string into constituent fields.

    Returns:
        A dict with trace_id, parent_id, version, flags, or None if invalid.
    """
    match = TRACEPARENT_RE.match(traceparent)
    if not match:
        return None
    version, trace_id, parent_id, flags = match.groups()
    return {
        "version": version,
        "trace_id": trace_id,
        "parent_id": parent_id,
        "flags": flags,
    }


class IndicatorSpan:
    """Context manager representing a tracing span for indicator calculations."""

    def __init__(
        self,
        name: str,
        traceparent: str | None = None,
        is_enabled: bool = True,
    ) -> None:
        """Initialize span tracking identifiers and options."""
        self.name = name
        self.is_enabled = is_enabled
        self.traceparent = traceparent
        self.start_time: float = 0.0
        self.trace_id: str = ""
        self.span_id: str = ""
        self.parent_id: str = ""

        if self.is_enabled:
            self.span_id = uuid.uuid4().hex[:16]
            if traceparent:
                parsed = parse_traceparent(traceparent)
                if parsed:
                    self.trace_id = parsed["trace_id"]
                    self.parent_id = parsed["parent_id"]
            if not self.trace_id:
                self.trace_id = uuid.uuid4().hex

    def __enter__(self) -> Self:
        """Record span start timestamp and emit trace initiation log."""
        if self.is_enabled:
            self.start_time = time.perf_counter()
            logger.info(
                f"Trace span started: {self.name}",
                extra={
                    "trace_id": self.trace_id,
                    "span_id": self.span_id,
                    "parent_id": self.parent_id,
                    "event_name": "trace_span_started",
                },
            )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Compute execution duration, emit span completion log, and exit."""
        if self.is_enabled:
            duration_ms = (time.perf_counter() - self.start_time) * 1000.0
            status = "success" if exc_type is None else "error"
            logger.info(
                f"Trace span ended: {self.name} ({status})",
                extra={
                    "trace_id": self.trace_id,
                    "span_id": self.span_id,
                    "parent_id": self.parent_id,
                    "duration_ms": duration_ms,
                    "status": status,
                    "event_name": "trace_span_ended",
                },
            )
