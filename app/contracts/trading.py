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

    # Named `execution_request_id` to avoid shadowing `Contract.request_id`
    # (the base trace/correlation field). This field is the primary business key.
    execution_request_id: str = Field(
        ..., description="Unique execution request identifier."
    )
    order_intent: OrderIntent = Field(..., description="Associated OrderIntent.")
    submitted_at: str = Field(..., description="UTC timestamp of submission.")
    execution_provider: str = Field(
        ..., description="Target execution adapter (e.g. mt5, ctrader)."
    )
    account_id: str = Field(..., description="Target trading account identifier.")

    @field_validator("submitted_at")
    @classmethod
    def validate_submitted_time(cls, v: str) -> str:
        """Validate and normalize the submission timestamp.

        Args:
            v: Raw timestamp string.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` cannot be parsed as a valid timestamp.
        """
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            # Broad catch: normalize_timestamp may raise app.utils.errors
            # ValidationError in addition to stdlib ValueError/TypeError.
            raise ValueError(f"Invalid submitted_at timestamp: {v}") from e


class TradeResult(Contract):
    """Standard outcome response after execution adapter returns."""

    trade_id: str = Field(..., description="Unique trade identification.")
    # Named `execution_request_id` to avoid shadowing `Contract.request_id`.
    execution_request_id: str = Field(
        ..., description="Matching TradeRequest execution_request_id."
    )
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
        """Validate and normalize the fill execution timestamp.

        Args:
            v: Raw timestamp string.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` cannot be parsed as a valid timestamp.
        """
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            raise ValueError(f"Invalid fill timestamp: {v}") from e


class ExecutionReport(Contract):
    """The canonical broker-neutral execution update report."""

    report_id: str = Field(..., description="Report identifier.")
    order_id: str = Field(..., description="Broker order ID.")
    symbol: str = Field(..., description="Symbol name.")
    action: Literal["buy", "sell"] = Field(..., description="Order direction.")
    status: Literal[
        "accepted",
        "pending",
        "partially_filled",
        "filled",
        "cancelled",
        "expired",
        "rejected",
        "failed",
    ] = Field(..., description="Broker-neutral execution report status.")
    price: float = Field(..., ge=0.0, description="Order price level.")
    quantity: float = Field(..., ge=0.0, description="Order volume size.")
    cumulative_quantity: float = Field(
        ..., ge=0.0, description="Accumulated fill size."
    )
    leaves_quantity: float = Field(..., ge=0.0, description="Remaining volume size.")
    commission: float = Field(default=0.0, description="Total commission.")
    slippage: float = Field(default=0.0, description="Recorded slippage.")
    latency_ms: float = Field(
        default=0.0, description="Round-trip execution latency in ms."
    )
    provider_order_id: str = Field(
        ..., description="Raw provider order ticket identifier."
    )
    timestamp: str = Field(..., description="UTC ISO timestamp.")

    @field_validator("timestamp")
    @classmethod
    def validate_report_time(cls, v: str) -> str:
        """Validate and normalize the execution report timestamp.

        Args:
            v: Raw timestamp string.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` cannot be parsed as a valid timestamp.
        """
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            raise ValueError(f"Invalid report timestamp: {v}") from e


class BrokerCapabilities(Contract):
    """Supported order features and policies of an execution provider.

    Note on ``margin_mode`` vs ``hedging_netting_mode``:

    - ``hedging_netting_mode``: Controls how positions for the same symbol are
      aggregated. ``"netting"`` collapses all positions into one net position;
      ``"hedging"`` allows multiple independent positions per symbol (MT5/cTrader
      typical modes).
    - ``margin_mode``: Controls how margin is calculated across open positions.
      ``"isolated"`` reserves margin per-position; ``"cross"`` shares the full
      account margin across all positions (common in crypto exchanges).
    """

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
    margin_mode: Literal["isolated", "cross"] = Field(
        ...,
        description=(
            "Margin calculation scope: 'isolated' reserves margin per-position;"
            " 'cross' shares account margin across all positions."
        ),
    )
    hedging_netting_mode: Literal["netting", "hedging"] = Field(
        ...,
        description=(
            "Position accounting mode: 'netting' collapses same-symbol positions;"
            " 'hedging' allows multiple independent positions per symbol."
        ),
    )
    provider_limits: dict[str, Any] = Field(
        default_factory=dict,
        description="Custom broker-specific limitation metadata.",
    )
