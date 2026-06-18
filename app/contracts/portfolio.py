# ruff: noqa: EM102
"""Portfolio state contracts module.

Defines AccountSnapshot, Position, and PortfolioSnapshot.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator

from app.contracts.base import Contract
from app.utils.normalization import normalize_timestamp


class AccountSnapshot(Contract):
    """Snapshot of account cash, margin, and equity metrics."""

    equity: float = Field(..., description="Current net asset equity value.")
    balance: float = Field(..., description="Account cash balance.")
    margin: float = Field(..., ge=0.0, description="Used/allocated margin amount.")
    free_margin: float = Field(
        ..., description="Available margin for opening positions."
    )
    currency: str = Field(..., description="Account currency representation.")
    leverage: int = Field(..., gt=0, description="Account leverage multiplier.")
    timestamp: str = Field(..., description="UTC ISO 8601 calculation timestamp.")

    @field_validator("timestamp")
    @classmethod
    def validate_snap_time(cls, v: str) -> str:
        """Validate timestamp format."""
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            raise ValueError(f"Invalid timestamp: {v}") from e


class Position(Contract):
    """Canonical representation of an open trading position."""

    position_id: str = Field(..., description="Durable unique position ID.")
    symbol: str = Field(..., description="Symbol name.")
    side: Literal["buy", "sell"] = Field(..., description="Position direction.")
    quantity: float = Field(..., gt=0.0, description="Position size in lots.")
    average_price: float = Field(..., gt=0.0, description="Average entry price level.")
    unrealized_pnl: float = Field(..., description="Floating profit or loss value.")
    realized_pnl: float = Field(default=0.0, description="Realized transaction PnL.")
    margin: float = Field(default=0.0, ge=0.0, description="Allocated margin size.")
    provider_position_id: str = Field(
        ..., description="Broker ticket reference identifier."
    )
    opened_at: str = Field(..., description="UTC position open timestamp.")
    updated_at: str = Field(..., description="UTC last update timestamp.")

    @field_validator("opened_at", "updated_at")
    @classmethod
    def validate_pos_times(cls, v: str) -> str:
        """Validate timestamp format."""
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            raise ValueError(f"Invalid timestamp: {v}") from e


class PortfolioSnapshot(Contract):
    """Standardized composite snapshot of the entire portfolio state."""

    account: AccountSnapshot = Field(..., description="Account snapshot metrics.")
    positions: list[Position] = Field(
        default_factory=list, description="List of currently active positions."
    )
    pending_exposure: float = Field(
        default=0.0, description="Value of unfilled order exposure."
    )
    risk_budget: float = Field(
        default=0.0, ge=0.0, description="Allocated risk budget utilization."
    )
    correlation_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Calculated asset correlation details.",
    )
    freshness_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Freshness validation timestamps map.",
    )
