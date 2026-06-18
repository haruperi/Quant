"""Indicator contracts module.

Defines canonical indicator contracts such as IndicatorResult.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.contracts.base import Contract


class IndicatorResult(Contract):
    """Canonical representation of an indicator run result."""

    name: str = Field(..., description="Name of the computed indicator.")
    version: str = Field(..., description="Version of the indicator formula/code.")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Formula-specific hyper-parameters used."
    )
    warmup_period: int = Field(
        ..., ge=0, description="Warmup period in number of bars required."
    )
    input_hash: str = Field(
        ..., description="SHA256 fingerprint hash of input dataset used."
    )
    output_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata for computed output columns."
    )
    output_columns: list[str] = Field(
        default_factory=list, description="Explicit list of generated column names."
    )
