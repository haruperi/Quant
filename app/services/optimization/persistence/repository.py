"""Optimization run storage repositories and progress trackers.

Provides abstract database interfaces, thread-safe progress tracking, in-memory
and file-backed database adapters, and exponential backoff retry managers.
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from app.services.optimization.helpers import OptimizationExecutionError

R = TypeVar("R")


class OptimizationRunRecord(BaseModel):
    """Database record for saving optimization run state.

    Args:
        run_id: Optimization run ID.
        strategy_ref: Strategy registration reference.
        parameter_space_hash: Parameter space schema hash.
        objective: target optimization metric.
        status: workflow status code.
        progress: progress completion fraction (0-100).
        total_candidates: Total count of candidate trials.
        candidates: Candidate results dictionary payloads.
    """

    run_id: str = Field(..., description="Run unique identifier.")
    strategy_ref: str = Field(..., description="Strategy name.")
    parameter_space_hash: str = Field(..., description="Hash of the space.")
    objective: str = Field(..., description="Objective name.")
    status: str = Field(..., description="State status.")
    progress: float = Field(default=0.0, description="Run progress percentage.")
    total_candidates: int = Field(default=0, description="Total candidates count.")
    candidates: list[dict[str, Any]] = Field(
        default_factory=list, description="Evaluated candidates list."
    )


class OptimizationRepository(ABC):
    """Abstract interface port for Optimization state persistence databases."""

    @abstractmethod
    def save_run(self, run_id: str, record: OptimizationRunRecord) -> None:
        """Persist optimization run record."""

    @abstractmethod
    def load_run(self, run_id: str) -> OptimizationRunRecord:
        """Load optimization run record."""

    @abstractmethod
    def update_progress(self, run_id: str, progress: float, status: str) -> None:
        """Update progress status fields."""


class InMemoryOptimizationRepository(OptimizationRepository):
    """Thread-safe in-memory database repository adapter."""

    def __init__(self) -> None:
        """Initialize in-memory records map."""
        self._records: dict[str, OptimizationRunRecord] = {}
        self._lock = threading.Lock()

    def save_run(self, run_id: str, record: OptimizationRunRecord) -> None:
        """Save run record under lock."""
        with self._lock:
            self._records[run_id] = record.model_copy(deep=True)

    def load_run(self, run_id: str) -> OptimizationRunRecord:
        """Load run record under lock."""
        with self._lock:
            if run_id not in self._records:
                msg = f"Run {run_id} not found in repository."
                raise OptimizationExecutionError(
                    msg,
                    code="DATA_NOT_FOUND",
                )
            return self._records[run_id].model_copy(deep=True)

    def update_progress(self, run_id: str, progress: float, status: str) -> None:
        """Update progress fields under lock."""
        with self._lock:
            if run_id not in self._records:
                msg = f"Run {run_id} not found in repository."
                raise OptimizationExecutionError(
                    msg,
                    code="DATA_NOT_FOUND",
                )
            record = self._records[run_id]
            record.progress = progress
            record.status = status


class ProgressTracker:
    """Thread-safe progress accumulator for parallel workers coordination."""

    def __init__(self, total: int) -> None:
        """Initialize progress tracking limits.

        Args:
            total: Expected count of trials.
        """
        self.total = total
        self.completed = 0
        self._lock = threading.Lock()

    def increment(self) -> None:
        """Safely record one finished unit under lock."""
        with self._lock:
            self.completed += 1

    def get_progress(self) -> float:
        """Return progress fraction (0-100)."""
        with self._lock:
            if self.total <= 0:
                return 100.0
            return (self.completed / self.total) * 100.0


def retry_with_backoff(
    action: Callable[..., R],
    *args: Any,  # noqa: ANN401
    attempts: int = 3,
    initial_delay: float = 0.1,
    **kwargs: Any,  # noqa: ANN401
) -> R:
    """Execute action retrying Safe transient errors with exponential backoff.

    Args:
        action: Callable callback action.
        *args: Variable arguments for the action.
        attempts: Try counts limit.
        initial_delay: Initial sleep duration in seconds.
        **kwargs: Keyword arguments for the action.

    Returns:
        R: Action outcome.

    Raises:
        Exception: Re-raises final error if retry count exceeded.
    """
    delay = initial_delay
    last_exc = None
    for attempt in range(attempts):
        try:
            return action(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt == attempts - 1:
                break
            time.sleep(delay)
            delay *= 2.0
    raise last_exc or OptimizationExecutionError("Action failed after retries.")


# Global helpers referencing Dependency Injected repositories
def save_optimization_run(
    repo: OptimizationRepository,
    run_id: str,
    record: OptimizationRunRecord,
) -> None:
    """Save optimization run via repository with retries."""
    retry_with_backoff(repo.save_run, run_id, record)


def load_optimization_run(
    repo: OptimizationRepository,
    run_id: str,
) -> OptimizationRunRecord:
    """Load optimization run via repository with retries."""
    return retry_with_backoff(repo.load_run, run_id)


def update_optimization_progress(
    repo: OptimizationRepository,
    run_id: str,
    progress: float,
    status: str,
) -> None:
    """Update optimization progress via repository with retries."""
    retry_with_backoff(repo.update_progress, run_id, progress, status)
