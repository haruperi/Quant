# ruff: noqa: EM102
"""Market contracts module.

Defines canonical market contracts (Symbol, Timeframe, Bar, Tick, Spread, DataSlice)
and market error constants.
"""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.contracts.base import Contract
from app.utils.normalization import normalize_timestamp

# Canonical market-data error codes
ERR_SYMBOL_UNAVAILABLE = "SYMBOL_UNAVAILABLE"
ERR_UNSUPPORTED_TIMEFRAME = "UNSUPPORTED_TIMEFRAME"
ERR_STALE_DATA = "STALE_DATA"
ERR_PROVIDER_ERROR = "PROVIDER_ERROR"
ERR_MALFORMED_PAYLOAD = "MALFORMED_PAYLOAD"

ALLOWED_TIMEFRAMES = {
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "M10",
    "M12",
    "M15",
    "M20",
    "M30",
    "H1",
    "H2",
    "H3",
    "H4",
    "H6",
    "H8",
    "H12",
    "D1",
    "W1",
    "MN1",
}


def _validate_timestamp_iso(v: str) -> str:
    """Validate and normalize a timestamp to an ISO UTC string."""
    try:
        dt = normalize_timestamp(v)
        return dt.isoformat()
    except Exception as e:
        raise ValueError(f"Invalid timestamp format: {v}") from e


class Symbol(Contract):
    """Canonical Symbol specification details."""

    symbol: str = Field(..., description="Canonical Symbol name (e.g. EURUSD).")
    broker_symbol: str = Field(
        ..., description="Broker-specific symbol representation."
    )
    asset_class: str = Field(
        ..., description="Asset class (forex, commodity, index, crypto, etc.)."
    )
    quote_currency: str = Field(..., description="Quote currency.")
    base_currency: str = Field(..., description="Base currency.")
    precision: int = Field(
        ..., ge=0, description="Digits precision in price representation."
    )
    lot_step: float = Field(..., gt=0.0, description="Minimum lot increment size.")
    lot_min: float = Field(
        ..., gt=0.0, description="Minimum allowed trade size in lots."
    )
    lot_max: float = Field(
        ..., gt=0.0, description="Maximum allowed trade size in lots."
    )
    tick_size: float = Field(..., gt=0.0, description="Minimum price fluctuation step.")
    tick_value: float = Field(
        ..., gt=0.0, description="Value of one minimum tick step."
    )
    contract_size: float = Field(
        ..., gt=0.0, description="Size of one standard lot contract."
    )

    @model_validator(mode="after")
    def validate_lot_limits(self) -> Symbol:
        """Verify that lot limits make sense."""
        if self.lot_min > self.lot_max:
            msg = (
                f"lot_min ({self.lot_min}) cannot be "
                f"greater than lot_max ({self.lot_max})."
            )
            raise ValueError(msg)
        return self


class Timeframe(Contract):
    """Canonical Timeframe definition."""

    name: str = Field(..., description="Canonical timeframe name (e.g. M5, H1, D1).")
    duration_seconds: int = Field(
        ..., gt=0, description="Timeframe duration in seconds."
    )

    @field_validator("name")
    @classmethod
    def validate_timeframe_name(cls, v: str) -> str:
        """Reject unsupported timeframes."""
        if v not in ALLOWED_TIMEFRAMES:
            msg = (
                f"Unsupported timeframe: {v}. "
                f"Must be one of {sorted(ALLOWED_TIMEFRAMES)}"
            )
            raise ValueError(msg)
        return v


class Bar(Contract):
    """Canonical representation of a single OHLCV bar."""

    timestamp: str = Field(..., description="UTC ISO 8601 timestamp.")
    open: float = Field(..., gt=0.0, description="Bar open price.")
    high: float = Field(..., gt=0.0, description="Bar high price.")
    low: float = Field(..., gt=0.0, description="Bar low price.")
    close: float = Field(..., gt=0.0, description="Bar close price.")
    volume: float | None = Field(default=None, ge=0.0, description="Trading volume.")
    spread: float | None = Field(
        default=None, ge=0.0, description="Average or end spread."
    )
    symbol: str = Field(..., description="Canonical Symbol name.")
    timeframe: str = Field(..., description="Timeframe name (e.g. M15).")
    source: str = Field(..., description="Provider source identifier.")

    @field_validator("timestamp")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Validate timestamp sequence/format."""
        return _validate_timestamp_iso(v)

    @field_validator("timeframe")
    @classmethod
    def validate_tf(cls, v: str) -> str:
        """Verify timeframe is in approved set."""
        if v not in ALLOWED_TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe: {v}")
        return v

    @model_validator(mode="after")
    def validate_ohlc(self) -> Bar:
        """Enforce physical price boundaries."""
        if self.low > self.high:
            msg = (
                f"Low price ({self.low}) cannot be "
                f"greater than High price ({self.high})."
            )
            raise ValueError(msg)
        if self.open > self.high or self.close > self.high:
            raise ValueError("Open and Close prices must not exceed High price.")
        if self.open < self.low or self.close < self.low:
            raise ValueError("Open and Close prices must not fall below Low price.")
        return self


class Tick(Contract):
    """Canonical market tick representation."""

    timestamp: str = Field(..., description="UTC ISO 8601 timestamp.")
    bid: float = Field(..., gt=0.0, description="Bid price.")
    ask: float = Field(..., gt=0.0, description="Ask price.")
    last: float | None = Field(default=None, gt=0.0, description="Last trade price.")
    volume: float | None = Field(default=None, ge=0.0, description="Volume size.")
    symbol: str = Field(..., description="Canonical Symbol name.")
    source: str = Field(..., description="Origin source identifier.")

    @field_validator("timestamp")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Validate timestamp format."""
        return _validate_timestamp_iso(v)

    @model_validator(mode="after")
    def validate_tick_prices(self) -> Tick:
        """Require ask >= bid constraint."""
        if self.ask < self.bid:
            raise ValueError(f"Ask ({self.ask}) cannot be less than Bid ({self.bid}).")
        return self


class Spread(Contract):
    """Canonical spread snapshot."""

    bid: float = Field(..., gt=0.0, description="Bid price.")
    ask: float = Field(..., gt=0.0, description="Ask price.")
    spread_points: float = Field(..., ge=0.0, description="Spread size in points.")
    spread_price: float = Field(..., ge=0.0, description="Spread size in price.")
    timestamp: str = Field(..., description="UTC ISO 8601 timestamp.")
    symbol: str = Field(..., description="Symbol name.")
    source: str = Field(..., description="Source adapter name.")

    @field_validator("timestamp")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Validate timestamp format."""
        return _validate_timestamp_iso(v)

    @model_validator(mode="after")
    def validate_spread_prices(self) -> Spread:
        """Require ask >= bid constraint."""
        if self.ask < self.bid:
            raise ValueError(f"Ask ({self.ask}) cannot be less than Bid ({self.bid}).")
        return self


class DataSlice(Contract):
    """Canonical bounded batch of bars, ticks, or records."""

    bars: list[Bar] = Field(default_factory=list, description="Time series bars batch.")
    ticks: list[Tick] = Field(
        default_factory=list, description="Time series ticks batch."
    )
    symbol: str = Field(..., description="Symbol name.")
    timeframe: str = Field(..., description="Timeframe name.")
    source: str = Field(..., description="Data source name.")

    # Raw provider data lineage fields
    provider: str = Field(..., description="Retrieved raw provider.")
    provider_request_id: str | None = Field(
        default=None, description="Request ID from provider if available."
    )
    retrieved_at: str = Field(..., description="Timestamp when data was fetched.")
    normalized_at: str = Field(..., description="Timestamp when data was normalized.")
    transformation_hash: str | None = Field(
        default=None, description="Hash fingerprint of normalization rule."
    )
    source_hash: str | None = Field(
        default=None, description="SHA256 hash of original raw payload."
    )

    @field_validator("retrieved_at", "normalized_at")
    @classmethod
    def validate_lineage_times(cls, v: str) -> str:
        """Validate timestamp format."""
        return _validate_timestamp_iso(v)
