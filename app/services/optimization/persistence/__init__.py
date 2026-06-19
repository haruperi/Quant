"""Optimization persistence package.

Exports checkpoints and database repositories for optimization states.
"""

from __future__ import annotations

from app.services.optimization.persistence.checkpoint import (
    OPT_ATOMIC_WRITE_FAILED,
    OPT_CHECKPOINT_CORRUPTED,
    OPT_INTRADAY_RULE_DATA_UNAVAILABLE,
    OPT_NOISY_OBJECTIVE_NOT_ALLOWED,
    OPT_PBO_THRESHOLD_FAILED,
    OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED,
    OPT_PRUNED_BY_HARD_GATE,
    OPT_TRIAL_COUNT_METHOD_UNSUPPORTED,
    STOCHASTIC_REALISM_CONFLICT,
)
from app.services.optimization.persistence.repository import (
    InMemoryOptimizationRepository,
    OptimizationRepository,
    OptimizationRunRecord,
    ProgressTracker,
    load_optimization_run,
    save_optimization_run,
    update_optimization_progress,
)

__all__ = [
    "OPT_ATOMIC_WRITE_FAILED",
    "OPT_CHECKPOINT_CORRUPTED",
    "OPT_INTRADAY_RULE_DATA_UNAVAILABLE",
    "OPT_NOISY_OBJECTIVE_NOT_ALLOWED",
    "OPT_PBO_THRESHOLD_FAILED",
    "OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED",
    "OPT_PRUNED_BY_HARD_GATE",
    "OPT_TRIAL_COUNT_METHOD_UNSUPPORTED",
    "STOCHASTIC_REALISM_CONFLICT",
    "InMemoryOptimizationRepository",
    "OptimizationRepository",
    "OptimizationRunRecord",
    "ProgressTracker",
    "load_optimization_run",
    "save_optimization_run",
    "update_optimization_progress",
]
