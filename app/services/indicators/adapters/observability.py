# ruff: noqa: E501
"""Observability and SLO monitoring adapter for the indicators service."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.utils.logger import logger


@dataclass
class SLOMonitor:
    """SLO monitoring engine tracking indicator latency, error rates, and timeouts.

    Attributes:
        error_threshold: Maximum acceptable non-transient error rate (defaults to 0.001 / 0.1%).
        timeout_threshold: Maximum acceptable timeout rate (defaults to 0.0005 / 0.05%).
        measurement_window_seconds: Historical window in seconds (defaults to 3600 / 1 hour).
        alert_routing_keys: Metadata map containing destination keys for alert escalation.
    """

    error_threshold: float = 0.001
    timeout_threshold: float = 0.0005
    measurement_window_seconds: int = 3600
    alert_routing_keys: dict[str, str] = field(
        default_factory=lambda: {
            "severity": "warning",
            "channel": "slack",
            "route_id": "quant-indicators-alerts",
        }
    )

    def __post_init__(self) -> None:
        """Initialize empty state parameters."""
        self.error_count: int = 0
        self.timeout_count: int = 0
        self.total_requests: int = 0
        self.history: list[dict[str, Any]] = []

    def record_request(
        self,
        duration_seconds: float,
        is_error: bool,
        is_timeout: bool,
    ) -> None:
        """Record execution metrics and slide the rolling measurement window."""
        now = time.time()
        self.history.append(
            {
                "timestamp": now,
                "duration": duration_seconds,
                "is_error": is_error,
                "is_timeout": is_timeout,
            }
        )
        self._slide_window(now)

    def _slide_window(self, now: float) -> None:
        """Remove history items falling outside of the measurement window duration."""
        cutoff = now - self.measurement_window_seconds
        self.history = [h for h in self.history if h["timestamp"] >= cutoff]

        self.total_requests = len(self.history)
        self.error_count = sum(1 for h in self.history if h["is_error"])
        self.timeout_count = sum(1 for h in self.history if h["is_timeout"])

    @property
    def current_error_rate(self) -> float:
        """Get the current error rate within the window."""
        if self.total_requests == 0:
            return 0.0
        return self.error_count / self.total_requests

    @property
    def current_timeout_rate(self) -> float:
        """Get the current timeout rate within the window."""
        if self.total_requests == 0:
            return 0.0
        return self.timeout_count / self.total_requests

    def check_slo_status(self) -> dict[str, Any]:
        """Verify metric targets and return status and routing metadata.

        Returns:
            A status dictionary indicating if targets passed and routing details.
        """
        error_violation = self.current_error_rate > self.error_threshold
        timeout_violation = self.current_timeout_rate > self.timeout_threshold

        slo_passed = not (error_violation or timeout_violation)

        if not slo_passed:
            logger.warning(
                f"Indicators SLO violation detected! "
                f"Error rate: {self.current_error_rate:.4%}, "
                f"Timeout rate: {self.current_timeout_rate:.4%}",
                extra={
                    "event_name": "slo_violation",
                    "error_rate": self.current_error_rate,
                    "timeout_rate": self.current_timeout_rate,
                    "alert_routing": self.alert_routing_keys,
                },
            )

        return {
            "slo_passed": slo_passed,
            "error_rate": self.current_error_rate,
            "error_threshold": self.error_threshold,
            "error_violation": error_violation,
            "timeout_rate": self.current_timeout_rate,
            "timeout_threshold": self.timeout_threshold,
            "timeout_violation": timeout_violation,
            "alert_routing": (self.alert_routing_keys if not slo_passed else None),
        }


# Global SLO monitor instance
global_slo_monitor = SLOMonitor()
