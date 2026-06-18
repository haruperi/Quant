# ruff: noqa: EM102
"""Trading execution contracts module.

Defines OrderIntent, TradeRequest, TradeResult, ExecutionReport,
Fill, and BrokerCapabilities.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator

from app.contracts.base import Contract
from app.utils.normalization import normalize_timestamp


class OrderIntent(Contract):
    """Canonical post-risk pre-execution trade intention contract."""

    intent_id: str = Field(..., description="Unique OrderIntent ID.")
    symbol: str = Field(..., description="Canonical Symbol name.")
    action: Literal[
        "buy", "sell", "buy_limit", "sell_limit", "buy_stop", "sell_stop"
    ] = Field(
        ...,
        description="Execution order action.",
    )
    volume: float = Field(..., gt=0.0, description="Order volume in lots.")
    price: float | None = Field(
        default=None, description="Limit/stop price constraint if applicable."
    )
    stop_loss: float | None = Field(
        default=None, description="Optional stop loss level."
    )
    take_profit: float | None = Field(
        default=None, description="Optional take profit level."
    )
    order_type: Literal["market", "limit", "stop", "stop_limit"] = Field(
        ..., description="Order execution type."
    )
    time_in_force: Literal["GTC", "IOC", "FOK", "DAY"] = Field(
        default="GTC", description="Time in force."
    )
    risk_decision_id: str = Field(..., description="Approved RiskDecision identifier.")


class TradeRequest(Contract):
    """Canonical execution request sent to a broker provider adapter."""

    request_id: str = Field(..., description="Unique execution Request ID.")
    order_intent: OrderIntent = Field(..., description="Associated OrderIntent.")
    submitted_at: str = Field(..., description="UTC timestamp of submission.")
    execution_provider: str = Field(
        ..., description="Target execution adapter (e.g. mt5, ctrader)."
    )
    account_id: str = Field(..., description="Target trading account identifier.")

    @field_validator("submitted_at")
    @classmethod
    def validate_submitted_time(cls, v: str) -> str:
        """Validate timestamp format."""
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            raise ValueError(f"Invalid submitted_at timestamp: {v}") from e


class TradeResult(Contract):
    """Standard outcome response after execution adapter returns."""

    trade_id: str = Field(..., description="Unique trade identification.")
    request_id: str = Field(..., description="Matching TradeRequest ID.")
    status: Literal[
        "accepted",
        "rejected",
        "pending",
        "partially_filled",
        "filled",
        "cancelled",
        "expired",
        "failed",
        "reconciled",
    ] = Field(
        ...,
        description="Neutral execution state.",
    )
    fill_price: float | None = Field(
        default=None, description="Average execution price."
    )
    fill_volume: float = Field(default=0.0, ge=0.0, description="Executed volume.")
    commission: float = Field(default=0.0, description="Total commission cost.")
    slippage_points: float = Field(
        default=0.0, description="Slippage recorded in broker points."
    )
    reconciliation_status: Literal[
        "none", "reconciled", "mismatch", "investigating"
    ] = Field(
        default="none",
        description="Reconciliation checkpoint.",
    )
    error_code: str | None = Field(
        default=None, description="Broker-neutral error code classification."
    )
    error_message: str | None = Field(default=None, description="Raw error details.")
    execution_time_ms: float | None = Field(
        default=None, description="Provider round-trip latency."
    )


class Fill(Contract):
    """Individual fill transaction receipt."""

    fill_id: str = Field(..., description="Durable unique deal/fill identifier.")
    order_id: str = Field(..., description="Matching broker order ticket.")
    symbol: str = Field(..., description="Symbol name.")
    price: float = Field(..., gt=0.0, description="Fill price.")
    quantity: float = Field(..., gt=0.0, description="Filled volume size.")
    commission: float = Field(default=0.0, description="Commission cost.")
    slippage: float = Field(default=0.0, description="Slippage in price units.")
    provider_deal_id: str = Field(..., description="Adapter specific fill/deal ticket.")
    timestamp: str = Field(..., description="UTC ISO 8601 fill execution time.")

    @field_validator("timestamp")
    @classmethod
    def validate_fill_time(cls, v: str) -> str:
        """Validate timestamp format."""
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            raise ValueError(f"Invalid timestamp: {v}") from e


class ExecutionReport(Contract):
    """The canonical broker-neutral execution update report."""

    report_id: str = Field(..., description="Report identifier.")
    order_id: str = Field(..., description="Broker order ID.")
    symbol: str = Field(..., description="Symbol name.")
    action: str = Field(..., description="Buy/sell direction.")
    status: str = Field(..., description="Report status.")
    price: float = Field(..., ge=0.0, description="Order price level.")
    quantity: float = Field(..., ge=0.0, description="Order volume size.")
    cumulative_quantity: float = Field(
        ..., ge=0.0, description="Accumulated fill size."
    )
    leaves_quantity: float = Field(..., ge=0.0, description="Remaining volume size.")
    commission: float = Field(default=0.0, description="Total commission.")
    slippage: float = Field(default=0.0, description="Recorded slippage.")
    latency_ms: float = Field(default=0.0, description="Recorded execution speed.")
    provider_order_id: str = Field(
        ..., description="Raw provider order ticket identifier."
    )
    timestamp: str = Field(..., description="UTC ISO timestamp.")

    @field_validator("timestamp")
    @classmethod
    def validate_report_time(cls, v: str) -> str:
        """Validate timestamp format."""
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            raise ValueError(f"Invalid timestamp: {v}") from e


class BrokerCapabilities(Contract):
    """Supported order features and policies of an execution provider."""

    order_types: list[str] = Field(
        default_factory=list, description="Supported order types."
    )
    fill_policies: list[str] = Field(
        default_factory=list, description="Supported fill policy options."
    )
    asset_classes: list[str] = Field(
        default_factory=list, description="Supported asset classes."
    )
    time_in_force_options: list[str] = Field(
        default_factory=list, description="Supported TIF variants."
    )
    margin_mode: Literal["netting", "hedging"] = Field(
        ..., description="Broker account margin reconciliation mode."
    )
    hedging_netting_mode: Literal["netting", "hedging"] = Field(
        ..., description="Position mode."
    )
    provider_limits: dict[str, Any] = Field(
        default_factory=dict, description="Custom broker-specific limitation metadata."
    )
