"""Data schemas and Pydantic models for market data.

Defines OHLCV, Tick, and Spread schemas, input query contracts, metadata mappings,
and validation rules.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.normalization import normalize_timestamp


def validate_utc_timestamp_helper(v: str) -> str:
    """Validate and normalize timestamp to UTC string format.

    Args:
        v: The input timestamp string.

    Returns:
        str: ISO 8601 normalized UTC timestamp.

    Raises:
        ValueError: If formatting is invalid.
    """
    try:
        dt = normalize_timestamp(v)
        return dt.isoformat()
    except Exception as e:
        err_msg = f"Invalid timestamp format: {v}"
        raise ValueError(err_msg) from e


class OHLCVRecord(BaseModel):
    """Pydantic model representing a single normalized OHLCV bar."""

    timestamp: str = Field(..., description="UTC ISO 8601 timestamp string.")
    open: str | float = Field(..., description="Bar open price.")
    high: str | float = Field(..., description="Bar high price.")
    low: str | float = Field(..., description="Bar low price.")
    close: str | float = Field(..., description="Bar close price.")
    volume: str | float = Field(..., description="Aggregated trading volume.")
    tick_volume: str | float = Field(..., description="Tick volume count.")
    real_volume: str | float = Field(..., description="Real volume value.")
    spread: str | float = Field(..., description="Average or end spread.")
    source: str = Field(..., description="Origin source adapter name.")
    symbol: str = Field(..., description="Trading symbol name.")
    timeframe: str = Field(..., description="Timeframe identifier (e.g. M5).")

    @field_validator("timestamp")
    @classmethod
    def validate_utc_timestamp(cls, v: str) -> str:
        """Validate and normalize timestamp using the shared helper."""
        return validate_utc_timestamp_helper(v)

    @model_validator(mode="after")
    def validate_ohlc_order(self) -> "OHLCVRecord":
        """Verify that high is the maximum value and low is the minimum value."""
        try:
            op = float(self.open)
            hi = float(self.high)
            lo = float(self.low)
            cl = float(self.close)
        except (ValueError, TypeError) as e:
            err_msg = f"Inconsistent price values: {e}"
            raise ValueError(err_msg) from e

        if hi < max(op, cl) or lo > min(op, cl) or hi < lo:
            err_inc = f"OHLC inconsistency: open={op}, high={hi}, low={lo}, close={cl}"
            raise ValueError(err_inc)
        return self


class TickRecord(BaseModel):
    """Pydantic model representing a single normalized market tick."""

    timestamp: str = Field(..., description="UTC ISO 8601 timestamp string.")
    bid: str | float = Field(..., description="Bid price.")
    ask: str | float = Field(..., description="Ask price.")
    last: str | float = Field(..., description="Last traded price.")
    volume: str | float = Field(..., description="Tick volume size.")
    spread: str | float = Field(..., description="Derived spread.")
    source: str = Field(..., description="Source adapter.")
    symbol: str = Field(..., description="Symbol.")

    @field_validator("timestamp")
    @classmethod
    def validate_utc_timestamp(cls, v: str) -> str:
        """Validate and normalize timestamp using the shared helper."""
        return validate_utc_timestamp_helper(v)

    @model_validator(mode="after")
    def validate_tick_constraints(self) -> "TickRecord":
        """Validate tick constraints.

        Requires ask >= bid and at least one quote price to exist.
        """
        has_bid = self.bid is not None and str(self.bid) != ""
        has_ask = self.ask is not None and str(self.ask) != ""
        has_last = self.last is not None and str(self.last) != ""

        if not (has_bid or has_ask or has_last):
            raise ValueError("At least one of bid, ask, or last must be provided.")

        if has_bid and has_ask:
            b = float(self.bid)
            a = float(self.ask)
            if a < b:
                err_msg = f"Ask ({a}) cannot be less than Bid ({b})."
                raise ValueError(err_msg)
        return self


class SpreadRecord(BaseModel):
    """Pydantic model representing a single normalized spread snapshot."""

    timestamp: str = Field(..., description="UTC ISO 8601 timestamp string.")
    symbol: str = Field(..., description="Trading symbol name.")
    bid: str | float = Field(..., description="Bid price.")
    ask: str | float = Field(..., description="Ask price.")
    spread_points: str | float = Field(..., description="Spread in broker points.")
    spread_pips: str | float = Field(..., description="Spread in pips.")
    source: str = Field(..., description="Source adapter.")

    @field_validator("timestamp")
    @classmethod
    def validate_utc_timestamp(cls, v: str) -> str:
        """Validate and normalize timestamp using the shared helper."""
        return validate_utc_timestamp_helper(v)

    @model_validator(mode="after")
    def validate_spread_values(self) -> "SpreadRecord":
        """Verify bid-ask spread rules."""
        b = float(self.bid)
        a = float(self.ask)
        if a < b:
            err_msg = f"Ask ({a}) cannot be less than Bid ({b}) in spread snapshot."
            raise ValueError(err_msg)
        return self


class SymbolMetadata(BaseModel):
    """Pydantic model representing normalized symbol specification details."""

    symbol: str = Field(..., description="Trading symbol name.")
    asset_class: str = Field(
        ..., description="Asset class (forex, commodity, index, crypto)."
    )
    base_currency: str = Field(..., description="Base currency.")
    quote_currency: str = Field(..., description="Quote currency.")
    contract_size: float = Field(..., description="Size of one standard lot contract.")
    tick_size: str | float = Field(..., description="Minimum price movement increment.")
    tick_value: str | float = Field(
        ..., description="Profit value of one tick movement for 1 lot."
    )
    point: str | float = Field(..., description="Point value size.")
    digits: int = Field(
        ..., description="Number of decimal digits in price representation."
    )
    lot_min: float = Field(..., description="Minimum lot size allowed.")
    lot_max: float = Field(..., description="Maximum lot size allowed.")
    lot_step: float = Field(..., description="Incremental lot step size.")
    margin_currency: str = Field(..., description="Base margin calculation currency.")
    profit_currency: str = Field(..., description="Base profit calculation currency.")
    trading_hours: dict[str, Any] = Field(
        ..., description="Symbol specific trading hours calendar."
    )
    source_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw metadata preserved from source adapter.",
    )


class DataAvailability(BaseModel):
    """Pydantic model indicating current historical database records coverage."""

    symbol: str = Field(..., description="Symbol.")
    timeframe: str = Field(..., description="Timeframe.")
    source: str = Field(..., description="Source.")
    start_time: str | None = Field(None, description="Earliest recorded UTC.")
    end_time: str | None = Field(None, description="Latest recorded UTC.")
    gap_count: int = Field(0, description="Identified internal gaps count.")
    gap_windows: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of gap start/end timestamp mappings.",
    )
    is_ready: bool = Field(True, description="Indicating if the source is responsive.")
    record_count: int = Field(0, description="Total committed records count.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Custom availability metadata."
    )
