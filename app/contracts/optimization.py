"""Optimization contracts module.

Defines OptimizationCandidate.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.contracts.base import Contract


class OptimizationCandidate(Contract):
    """Canonical model representing an optimization parameter candidate."""

    strategy_id: str = Field(..., description="Target Strategy ID.")
    parameters: dict[str, Any] = Field(
        ..., description="Hyperparameter value settings."
    )
    score: float = Field(
        ..., description="Calculated objective function optimization score."
    )
    robustness_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Robustness indicators (e.g. Monte Carlo stability).",
    )
    validation_splits: list[str] = Field(
        default_factory=list,
        description="Dataset partition validation references.",
    )
    overfitting_checks: dict[str, Any] = Field(
        default_factory=dict,
        description="In-sample vs out-of-sample metrics comparison metadata.",
    )
    evidence_references: list[str] = Field(
        default_factory=list,
        description="Artifact evidence hashes for verification.",
    )
