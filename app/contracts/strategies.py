"""Strategies contracts module.

Defines StrategyInput and StrategySignal contracts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.contracts.base import Contract
from app.utils.normalization import normalize_timestamp


class StrategyInput(Contract):
    """Canonical input for strategy execution.

    Attributes:
        market_data_refs: Hashes or IDs of input DataSlice contracts.
        indicator_refs: Hashes or IDs of computed IndicatorResult contracts.
        portfolio_context: Current portfolio snapshot values.
        config: Strategy hyperparameters and settings.
        start_time: UTC ISO 8601 start boundary of the evaluation window.
        end_time: UTC ISO 8601 end boundary of the evaluation window.
    """

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
    start_time: str = Field(..., description="UTC ISO 8601 start boundary.")
    end_time: str = Field(..., description="UTC ISO 8601 end boundary.")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_boundary_times(cls, v: str) -> str:
        """Validate and normalize evaluation window boundary timestamps.

        Args:
            v: The timestamp string to validate.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` cannot be parsed as a valid timestamp.
        """
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            # Catch broadly: normalize_timestamp may raise app.utils.errors
            # ValidationError (not stdlib ValueError) for bad input strings.
            raise ValueError(f"Invalid boundary timestamp: {v}") from e  # noqa: EM102


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
        """Reject empty or whitespace-only symbol strings.

        Args:
            v: Symbol string to validate.

        Returns:
            Stripped, non-empty symbol string.

        Raises:
            ValueError: If ``v`` is empty or whitespace-only.
        """
        if not v or not v.strip():
            raise ValueError("symbol must be a non-empty string.")
        return v.strip()

    @model_validator(mode="after")
    def validate_signal_integrity(self) -> StrategySignal:
        """Validate evidence references and reject expired signals.

        A signal is considered expired if more seconds have elapsed since
        ``created_at`` than ``validity_window`` allows.  Evidence must be
        non-empty to guarantee audit traceability.

        Returns:
            The validated StrategySignal instance.

        Raises:
            ValueError: If ``evidence_references`` is empty, if
                ``created_at`` cannot be parsed, or if the signal has
                already expired relative to the current UTC time.
        """
        if not self.evidence_references:
            raise ValueError("evidence_references is required and cannot be empty.")
        # Parse created_at and compute elapsed seconds outside any branch
        # that raises ValueError so the expiry check propagates cleanly.
        try:
            created = datetime.fromisoformat(self.created_at)
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            elapsed = (datetime.now(UTC) - created).total_seconds()
        except Exception as e:
            # Broad catch is intentional: datetime.fromisoformat may raise
            # ValueError; timezone arithmetic may raise OverflowError.
            raise ValueError(
                f"Could not evaluate signal expiry from created_at "  # noqa: EM102
                f"'{self.created_at}': {e}"
            ) from e
        if elapsed > self.validity_window:
            raise ValueError(
                f"Signal has expired: {elapsed:.1f}s elapsed, "  # noqa: EM102
                f"validity_window={self.validity_window}s."
            )
        return self
