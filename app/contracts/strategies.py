"""Strategies contracts module.

Defines StrategyInput and StrategySignal contracts.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.contracts.base import Contract


class StrategyInput(Contract):
    """Canonical input for strategy execution."""

    market_data_refs: list[str] = Field(
        default_factory=list,
        description="References (hashes or IDs) of input market data slices.",
    )
    indicator_refs: list[str] = Field(
        default_factory=list,
        description="References (hashes or IDs) of computed indicators.",
    )
    portfolio_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Current portfolio context snapshot values.",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy hyperparameters and settings.",
    )
    start_time: str = Field(..., description="UTC ISO start boundary.")
    end_time: str = Field(..., description="UTC ISO end boundary.")


class StrategySignal(Contract):
    """Canonical output from a strategy to be reviewed by Risk."""

    # Restrict fields to prevent direct broker-specific placement fields
    model_config = ConfigDict(extra="forbid")

    strategy_id: str = Field(..., description="Strategy identifier.")
    strategy_version: str = Field(..., description="Strategy code version.")
    parameter_hash: str = Field(..., description="Hash of the parameters config used.")
    symbol: str = Field(..., description="Target symbol name.")
    side: Literal["buy", "sell", "exit"] = Field(
        ..., description="Signal side direction."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Signal confidence level."
    )
    validity_window: int = Field(
        ..., gt=0, description="Validity window duration in seconds."
    )
    reason: str = Field(..., description="Human or rule-based reason for generation.")
    evidence_references: list[str] = Field(
        default_factory=list,
        description="Required audit references proving the signal logic.",
    )
    source_data_hash: str = Field(
        ..., description="Hash of the triggering market data state."
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol_non_empty(cls, v: str) -> str:
        """Reject empty symbols."""
        if not v or not v.strip():
            raise ValueError("symbol must be a non-empty string.")
        return v.strip()

    @model_validator(mode="after")
    def validate_evidence_and_fields(self) -> StrategySignal:
        """Ensure evidence is present and reject broker specific fields."""
        if not self.evidence_references:
            raise ValueError("evidence_references is required and cannot be empty.")
        return self
