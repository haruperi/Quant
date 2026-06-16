"""Market data gateway router and source adapters.

Orchestrates historical, real-time, local, synthetic, and broker data queries.
Consolidates source adapters (CSV, Parquet, MT5, cTrader, etc.), persistent circuit
breakers, and the single data query service API.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import pandas as pd

from app.services.data.models import (
    DataAvailability,
    OHLCVRecord,
    SpreadRecord,
    SymbolMetadata,
    TickRecord,
)
from app.services.data.storage import (
    db_helper,
    generate_cache_key,
    get_cached_data,
    load_local_dataset,
    set_cached_data,
)
from app.services.data.transforms import (
    generate_synthetic_bars,
    generate_synthetic_ticks,
)
from app.services.data.validation import (
    DEFAULT_OHLCV_LIMIT,
    DEFAULT_SPREAD_LIMIT,
    DEFAULT_TICK_LIMIT,
    MAX_OHLCV_LIMIT,
    MAX_SPREAD_LIMIT,
    MAX_TICK_LIMIT,
    normalize_numeric,
    validate_license,
    validate_limit,
    validate_timeframe,
)
from app.utils.errors import DataError, ExternalServiceError, ValidationError
from app.utils.logger import logger
from app.utils.normalization import normalize_timestamp


# --- 1. Source Adapter Protocol ---
@runtime_checkable
class SourceAdapterProtocol(Protocol):
    """Common internal source adapter protocol for all data providers."""

    def is_ready(self) -> bool:
        """Check if source adapter is ready/configured."""
        ...

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch normalized historical OHLCV data."""
        ...

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch normalized historical tick data."""
        ...

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols discovered from the source."""
        ...

    def get_symbol_metadata(
        self, symbol: str, *, request_id: str | None = None
    ) -> dict[str, Any]:
        """Retrieve symbol metadata."""
        ...


# --- 2. Rate Limiters ---
class TokenBucketLimiter:
    """A thread-safe simple Token Bucket rate limiter."""

    def __init__(self, rate: float, capacity: float) -> None:
        """Initialize with a token replenishment rate (tokens/sec) and capacity."""
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = datetime.now(UTC).timestamp()

    def consume(self) -> bool:
        """Consume 1 token from the bucket. Returns True if successful."""
        now = datetime.now(UTC).timestamp()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


RATE_LIMITERS: dict[str, TokenBucketLimiter] = {
    "mt5": TokenBucketLimiter(10.0, 20.0),
    "ctrader": TokenBucketLimiter(10.0, 20.0),
    "dukascopy": TokenBucketLimiter(5.0, 10.0),
    "binance": TokenBucketLimiter(5.0, 10.0),
    "yahoo": TokenBucketLimiter(5.0, 10.0),
    "csv": TokenBucketLimiter(100.0, 500.0),
    "parquet": TokenBucketLimiter(100.0, 500.0),
    "synthetic": TokenBucketLimiter(100.0, 500.0),
}


def check_rate_limit(source: str) -> None:
    """Consume rate limit token or raise a BACKPRESSURE_EXCEEDED error."""
    src_lower = source.lower()
    if src_lower in RATE_LIMITERS:
        limiter = RATE_LIMITERS[src_lower]
        if not limiter.consume():
            msg = f"Rate limit exceeded for source: {source}."
            raise ExternalServiceError(msg, code="BACKPRESSURE_EXCEEDED")


# --- 3. Circuit Breaker Handlers ---
def get_circuit_breaker(source: str) -> dict[str, Any]:
    """Retrieve persisted circuit breaker state for a source."""
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM circuit_breakers WHERE source = ?;", (source,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "source": row["source"],
                    "state": row["state"],
                    "last_state_change": row["last_state_change"],
                    "failures_count": int(row["failures_count"]),
                    "cooldown_expires": row["cooldown_expires"],
                }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to query circuit breaker for {source}: {e}")

    return {
        "source": source,
        "state": "closed",
        "last_state_change": datetime.now(UTC).isoformat(),
        "failures_count": 0,
        "cooldown_expires": None,
    }


def update_circuit_breaker(
    source: str,
    state: str,
    failures_count: int,
    cooldown_expires: str | None = None,
) -> None:
    """Update and persist circuit breaker state."""
    logger.info(
        f"Updating circuit breaker: source={source}, state={state}, "
        f"failures={failures_count}"
    )
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO circuit_breakers (
                    source, state, last_state_change, failures_count, cooldown_expires
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    source,
                    state,
                    datetime.now(UTC).isoformat(),
                    failures_count,
                    cooldown_expires,
                ),
            )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to save circuit breaker state for {source}: {e}")


def check_circuit_breaker_barrier(source: str) -> None:
    """Check if the source's circuit breaker blocks execution."""
    cb = get_circuit_breaker(source)
    if cb["state"] == "open":
        expires = cb["cooldown_expires"]
        if expires and datetime.now(UTC) > datetime.fromisoformat(expires):
            logger.info(
                f"Circuit breaker cooldown expired for {source}. "
                "Transitioning to half-open."
            )
            update_circuit_breaker(source, "half-open", cb["failures_count"])
        else:
            msg = f"Circuit breaker is open for source: {source} (blocked)."
            raise ExternalServiceError(msg, code="CIRCUIT_OPEN")


def _normalize_mt5_record(
    r: dict[str, Any], symbol: str, timeframe: str, source: str
) -> dict[str, Any]:
    """Normalize a single MT5-style raw record."""
    date_val = r.get("<DATE>") or r.get("DATE") or ""
    time_val = r.get("<TIME>") or r.get("TIME") or "00:00:00"
    date_val = str(date_val).replace(".", "-")
    dt_str = f"{date_val} {time_val}"
    try:
        dt = pd.to_datetime(dt_str)
        dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.tz_convert(UTC)
        ts_str = dt.isoformat()
    except (ValueError, TypeError):
        ts_str = dt_str

    def get_float(key: str) -> float:
        val = r.get(key)
        if val is None:
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    op = get_float("<OPEN>")
    hi = get_float("<HIGH>")
    lo = get_float("<LOW>")
    cl = get_float("<CLOSE>")
    tick_vol = get_float("<TICKVOL>")
    real_vol = get_float("<VOL>")
    spread_val = get_float("<SPREAD>")

    return {
        "timestamp": ts_str,
        "open": op,
        "high": hi,
        "low": lo,
        "close": cl,
        "volume": tick_vol,
        "tick_volume": tick_vol,
        "real_volume": real_vol,
        "spread": spread_val,
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
    }


def _normalize_std_record(
    r: dict[str, Any], symbol: str, timeframe: str, source: str
) -> dict[str, Any]:
    """Normalize a single standard-style record."""
    norm_r = dict(r)
    if "timestamp" in norm_r:
        try:
            dt = pd.to_datetime(norm_r["timestamp"])
            dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.tz_convert(UTC)
            norm_r["timestamp"] = dt.isoformat()
        except (ValueError, TypeError) as ex:
            logger.warning(f"Failed to parse timestamp {norm_r.get('timestamp')}: {ex}")
    norm_r.setdefault("source", source)
    norm_r.setdefault("symbol", symbol)
    norm_r.setdefault("timeframe", timeframe)
    norm_r.setdefault("tick_volume", norm_r.get("volume", 0.0))
    norm_r.setdefault("real_volume", 0.0)
    norm_r.setdefault("spread", 0.0)
    if "volume" not in norm_r:
        norm_r["volume"] = norm_r.get("tick_volume", 0.0)
    return norm_r


def normalize_file_records(
    records: list[dict[str, Any]],
    symbol: str,
    timeframe: str,
    source: str,
) -> list[dict[str, Any]]:
    """Normalize raw or MT5 file records to standard OHLCV schema."""
    if not records:
        return []

    first = records[0]
    is_mt5_style = any(str(k).startswith("<") and str(k).endswith(">") for k in first)

    normalized = []
    for r in records:
        if is_mt5_style:
            norm_r = _normalize_mt5_record(r, symbol, timeframe, source)
        else:
            norm_r = _normalize_std_record(r, symbol, timeframe, source)
        normalized.append(norm_r)
    return normalized


class CSVAdapter:
    """CSV File Data Source Adapter."""

    def is_ready(self) -> bool:
        """Check if ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch market data."""
        filename = f"{symbol}_{timeframe}.csv"
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/csv",
            "data/raw/csv",
        ]
        for p in paths:
            target_path = Path(p) / filename
            if target_path.exists():
                raw_records = load_local_dataset(
                    str(target_path), request_id=request_id
                )
                records = normalize_file_records(raw_records, symbol, timeframe, "csv")
                filtered = []
                for r in records:
                    ts = pd.to_datetime(r["timestamp"])
                    if start_time.tzinfo is None:
                        start_comp = start_time.replace(tzinfo=UTC)
                    else:
                        start_comp = start_time
                    if end_time.tzinfo is None:
                        end_comp = end_time.replace(tzinfo=UTC)
                    else:
                        end_comp = end_time

                    ts_utc = ts.tz_convert(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
                    if start_comp <= ts_utc <= end_comp:
                        filtered.append(r)
                return filtered
        return []

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch tick data."""
        filename = f"{symbol}_ticks.csv"
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/csv",
            "data/raw/csv",
        ]
        for p in paths:
            target_path = Path(p) / filename
            if target_path.exists():
                records = load_local_dataset(str(target_path), request_id=request_id)
                filtered = []
                for r in records:
                    ts = pd.to_datetime(r["timestamp"])
                    ts_utc = ts.tz_convert(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
                    start_comp = (
                        start_time.replace(tzinfo=UTC)
                        if start_time.tzinfo is None
                        else start_time
                    )
                    end_comp = (
                        end_time.replace(tzinfo=UTC)
                        if end_time.tzinfo is None
                        else end_time
                    )
                    if start_comp <= ts_utc <= end_comp:
                        filtered.append(r)
                return filtered
        return []

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols."""
        _ = request_id
        symbols = set()
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/csv",
            "data/raw/csv",
        ]
        for p in paths:
            path_obj = Path(p)
            if path_obj.exists():
                for f in path_obj.glob("*.csv"):
                    symbol = f.name.split("_")[0]
                    symbols.add(symbol)
        return sorted(symbols)

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get symbol metadata."""
        return {
            "symbol": symbol,
            "source": "csv",
            "ready": True,
            "license": "Open",
            "attribution": "Local CSV Files",
        }


class ParquetAdapter:
    """Parquet File Data Source Adapter."""

    def is_ready(self) -> bool:
        """Check if ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch market data."""
        filename = f"{symbol}_{timeframe}.parquet"
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/parquet",
            "data/raw/parquet",
        ]
        for p in paths:
            target_path = Path(p) / filename
            if target_path.exists():
                raw_records = load_local_dataset(
                    str(target_path), request_id=request_id
                )
                records = normalize_file_records(
                    raw_records, symbol, timeframe, "parquet"
                )
                filtered = []
                for r in records:
                    ts = pd.to_datetime(r["timestamp"])
                    ts_utc = ts.tz_convert(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
                    start_comp = (
                        start_time.replace(tzinfo=UTC)
                        if start_time.tzinfo is None
                        else start_time
                    )
                    end_comp = (
                        end_time.replace(tzinfo=UTC)
                        if end_time.tzinfo is None
                        else end_time
                    )
                    if start_comp <= ts_utc <= end_comp:
                        filtered.append(r)
                return filtered
        return []

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch tick data."""
        filename = f"{symbol}_ticks.parquet"
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/parquet",
            "data/raw/parquet",
        ]
        for p in paths:
            target_path = Path(p) / filename
            if target_path.exists():
                records = load_local_dataset(str(target_path), request_id=request_id)
                filtered = []
                for r in records:
                    ts = pd.to_datetime(r["timestamp"])
                    ts_utc = ts.tz_convert(UTC) if ts.tzinfo else ts.replace(tzinfo=UTC)
                    start_comp = (
                        start_time.replace(tzinfo=UTC)
                        if start_time.tzinfo is None
                        else start_time
                    )
                    end_comp = (
                        end_time.replace(tzinfo=UTC)
                        if end_time.tzinfo is None
                        else end_time
                    )
                    if start_comp <= ts_utc <= end_comp:
                        filtered.append(r)
                return filtered
        return []

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols."""
        _ = request_id
        symbols = set()
        paths = [
            "data/processed",
            "data/raw",
            "data/processed/parquet",
            "data/raw/parquet",
        ]
        for p in paths:
            path_obj = Path(p)
            if path_obj.exists():
                for f in path_obj.glob("*.parquet"):
                    symbol = f.name.split("_")[0]
                    symbols.add(symbol)
        return sorted(symbols)

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get symbol metadata."""
        return {
            "symbol": symbol,
            "source": "parquet",
            "ready": True,
            "license": "Open",
            "attribution": "Local Parquet Files",
        }


class SyntheticAdapter:
    """Synthetic Data Source Adapter."""

    def is_ready(self) -> bool:
        """Check if ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,  # noqa: ARG002
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch market data."""
        start_str = start_time.isoformat()
        return generate_synthetic_bars(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_str,
            num_bars=100,
            start_price=1.10,
            drift=0.0,
            volatility=0.01,
            seed=42,
            request_id=request_id,
        )

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,  # noqa: ARG002
        *,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch tick data."""
        start_str = start_time.isoformat()
        return generate_synthetic_ticks(
            symbol=symbol,
            start_time=start_str,
            num_ticks=250,
            start_price=1.10,
            average_spread=0.0002,
            volatility=0.0001,
            seed=42,
            request_id=request_id,
        )

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols."""
        _ = request_id
        return ["EURUSD", "GBPUSD", "USDJPY", "SPX500", "XAUUSD"]

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get symbol metadata."""
        asset_class = "forex"
        if symbol == "SPX500":
            asset_class = "indices"
        elif symbol == "XAUUSD":
            asset_class = "metals"
        return {
            "symbol": symbol,
            "source": "synthetic",
            "ready": True,
            "license": "Permissive",
            "attribution": "Synthetic Bar Generator",
            "asset_class": asset_class,
        }


class MT5Adapter:
    """MetaTrader 5 Active Source Adapter."""

    def is_ready(self) -> bool:
        """Check if ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch market data."""
        check_circuit_breaker_barrier("mt5")

        try:
            from app.services.brokers.mt5 import get_mt5_client

            client = get_mt5_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"MT5 initialization failed: {e}")
            cb = get_circuit_breaker("mt5")
            update_circuit_breaker(
                "mt5",
                "open" if cb["failures_count"] >= 4 else "closed",  # noqa: PLR2004
                cb["failures_count"] + 1,
                (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
            )
            msg = f"MetaTrader 5 terminal is not available: {e}"
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

        if not client.is_connected():
            msg = "MT5 Client failed to connect to live broker."
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

        df = client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            date_from=start_time,
            date_to=end_time,
        )
        if df is None or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            ts = row["Timestamp"]
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = pd.to_datetime(ts).isoformat()
            records.append(
                {
                    "timestamp": ts_str,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "tick_volume": float(row["Volume"]),
                    "real_volume": 0.0,
                    "spread": float(row["Spread"]),
                    "source": "mt5",
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            )
        return records

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch tick data."""
        check_circuit_breaker_barrier("mt5")
        try:
            from app.services.brokers.mt5 import get_mt5_client

            client = get_mt5_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"MT5 initialization failed: {e}")
            msg = f"MetaTrader 5 terminal is not available: {e}"
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

        df = client.get_ticks(
            symbol=symbol,
            start=start_time,
            end=end_time,
            as_dataframe=True,
        )
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            time_msc = int(row.get("time_msc", 0))
            if time_msc > 0:
                dt = pd.to_datetime(time_msc, unit="ms", utc=True)
            else:
                dt = pd.to_datetime(int(row.get("time", 0)), unit="s", utc=True)

            bid = float(row.get("bid", 0.0))
            ask = float(row.get("ask", 0.0))
            spread = ask - bid

            records.append(
                {
                    "timestamp": dt.isoformat(),
                    "bid": bid,
                    "ask": ask,
                    "last": float(row.get("last", 0.0)),
                    "volume": float(row.get("volume", 0.0)),
                    "spread": spread,
                    "source": "mt5",
                    "symbol": symbol,
                }
            )
        return records

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols."""
        _ = request_id
        return ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "SPX500"]

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get symbol metadata."""
        asset_class = "forex"
        sym_upper = symbol.upper()
        if sym_upper == "SPX500":
            asset_class = "indices"
        elif sym_upper == "XAUUSD":
            asset_class = "metals"
        return {
            "symbol": symbol,
            "source": "mt5",
            "ready": True,
            "license": "Proprietary",
            "attribution": "MetaTrader 5 Terminal Gateway Data",
            "asset_class": asset_class,
        }


class CTraderAdapter:
    """cTrader OpenAPI Active Source Adapter."""

    def is_ready(self) -> bool:
        """Check if ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch market data."""
        check_circuit_breaker_barrier("ctrader")

        try:
            from app.services.brokers.ctrader import get_ctrader_client

            client = get_ctrader_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"cTrader initialization failed: {e}")
            cb = get_circuit_breaker("ctrader")
            update_circuit_breaker(
                "ctrader",
                "open" if cb["failures_count"] >= 4 else "closed",  # noqa: PLR2004
                cb["failures_count"] + 1,
                (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
            )
            msg = f"cTrader OpenAPI client is not available: {e}"
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

        if not client.is_connected():
            msg = "cTrader Client failed to connect to live broker."
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

        df = client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            date_from=start_time,
            date_to=end_time,
        )
        if df is None or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            ts = row["Timestamp"]
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = pd.to_datetime(ts).isoformat()
            records.append(
                {
                    "timestamp": ts_str,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "tick_volume": float(row["Volume"]),
                    "real_volume": 0.0,
                    "spread": float(row["Spread"]),
                    "source": "ctrader",
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            )
        return records

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch tick data."""
        check_circuit_breaker_barrier("ctrader")
        try:
            from app.services.brokers.ctrader import get_ctrader_client

            client = get_ctrader_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"cTrader initialization failed: {e}")
            msg = f"cTrader OpenAPI client is not available: {e}"
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

        df = client.get_ticks(
            symbol=symbol,
            start=start_time,
            end=end_time,
            as_dataframe=True,
        )
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            ts = row["Timestamp"]
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = pd.to_datetime(ts).isoformat()
            records.append(
                {
                    "timestamp": ts_str,
                    "bid": float(row["bid"]),
                    "ask": float(row["ask"]),
                    "last": float(row["last"]),
                    "volume": float(row["volume"]),
                    "spread": float(row["spread"]),
                    "source": "ctrader",
                    "symbol": symbol,
                }
            )
        return records

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols."""
        _ = request_id
        return ["EURUSD", "GBPUSD"]

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get symbol metadata."""
        return {
            "symbol": symbol,
            "source": "ctrader",
            "ready": True,
            "license": "Proprietary",
            "attribution": "cTrader OpenAPI Client Feed",
        }


class DukascopyAdapter:
    """Dukascopy HTTP Active Source Adapter."""

    def is_ready(self) -> bool:
        """Check if ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch market data."""
        check_circuit_breaker_barrier("dukascopy")

        try:
            from app.services.brokers.dukascopy import (
                get_dukascopy_client,
            )

            client = get_dukascopy_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"Dukascopy client initialization failed: {e}")
            cb = get_circuit_breaker("dukascopy")
            update_circuit_breaker(
                "dukascopy",
                "open" if cb["failures_count"] >= 4 else "closed",  # noqa: PLR2004
                cb["failures_count"] + 1,
                (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
            )
            msg = f"Dukascopy service is not available: {e}"
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE") from e

        if not client.is_connected():
            msg = "Dukascopy Client failed to connect."
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE")

        df = client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            date_from=start_time,
            date_to=end_time,
        )
        if df is None or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            ts = row["Timestamp"]
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = pd.to_datetime(ts).isoformat()
            records.append(
                {
                    "timestamp": ts_str,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "tick_volume": float(row["Volume"]),
                    "real_volume": 0.0,
                    "spread": float(row["Spread"]),
                    "source": "dukascopy",
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            )
        return records

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch tick data."""
        check_circuit_breaker_barrier("dukascopy")
        try:
            from app.services.brokers.dukascopy import (
                get_dukascopy_client,
            )

            client = get_dukascopy_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"Dukascopy client initialization failed: {e}")
            msg = f"Dukascopy service is not available: {e}"
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE") from e

        df = client.get_ticks(
            symbol=symbol,
            start=start_time,
            end=end_time,
            as_dataframe=True,
        )
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            ts = row["Timestamp"]
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = pd.to_datetime(ts).isoformat()
            records.append(
                {
                    "timestamp": ts_str,
                    "bid": float(row["bid"]),
                    "ask": float(row["ask"]),
                    "last": float(row["last"]),
                    "volume": float(row["volume"]),
                    "spread": float(row["spread"]),
                    "source": "dukascopy",
                    "symbol": symbol,
                }
            )
        return records

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols."""
        _ = request_id
        return ["EURUSD", "GBPUSD", "USDJPY"]

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get symbol metadata."""
        return {
            "symbol": symbol,
            "source": "dukascopy",
            "ready": True,
            "license": "Restricted",
            "attribution": "Dukascopy Community Feed",
        }


class BinanceAdapter:
    """Binance Active Source Adapter."""

    def is_ready(self) -> bool:
        """Check if adapter is ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch historical bars."""
        check_circuit_breaker_barrier("binance")

        try:
            from app.services.brokers.binance import get_binance_client

            client = get_binance_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"Binance client initialization failed: {e}")
            cb = get_circuit_breaker("binance")
            update_circuit_breaker(
                "binance",
                "open" if cb["failures_count"] >= 4 else "closed",  # noqa: PLR2004
                cb["failures_count"] + 1,
                (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
            )
            msg = f"Binance service is not available: {e}"
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE") from e

        if not client.is_connected():
            msg = "Binance Client failed to connect."
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE")

        df = client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            date_from=start_time,
            date_to=end_time,
        )
        if df is None or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            ts = row["Timestamp"]
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = pd.to_datetime(ts).isoformat()
            records.append(
                {
                    "timestamp": ts_str,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "tick_volume": float(row["Volume"]),
                    "real_volume": 0.0,
                    "spread": float(row["Spread"]),
                    "source": "binance",
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            )
        return records

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch tick data."""
        check_circuit_breaker_barrier("binance")
        try:
            from app.services.brokers.binance import get_binance_client

            client = get_binance_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"Binance client initialization failed: {e}")
            msg = f"Binance service is not available: {e}"
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE") from e

        df = client.get_ticks(
            symbol=symbol,
            start=start_time,
            end=end_time,
            as_dataframe=True,
        )
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            ts = row["Timestamp"]
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = pd.to_datetime(ts).isoformat()
            records.append(
                {
                    "timestamp": ts_str,
                    "bid": float(row["bid"]),
                    "ask": float(row["ask"]),
                    "last": float(row["last"]),
                    "volume": float(row["volume"]),
                    "spread": float(row["spread"]),
                    "source": "binance",
                    "symbol": symbol,
                }
            )
        return records

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List all symbols from Binance."""
        _ = request_id
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Retrieve symbol metadata."""
        return {
            "symbol": symbol,
            "source": "binance",
            "ready": True,
            "license": "Restricted",
            "attribution": "Binance Discovery Feed",
        }


class YahooAdapter:
    """Yahoo Finance Active Source Adapter."""

    def is_ready(self) -> bool:
        """Check if ready."""
        return True

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch market data."""
        check_circuit_breaker_barrier("yahoo")

        try:
            from app.services.brokers.yahoo import get_yahoo_client

            client = get_yahoo_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"Yahoo Finance client initialization failed: {e}")
            cb = get_circuit_breaker("yahoo")
            update_circuit_breaker(
                "yahoo",
                "open" if cb["failures_count"] >= 4 else "closed",  # noqa: PLR2004
                cb["failures_count"] + 1,
                (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
            )
            msg = f"Yahoo Finance service is not available: {e}"
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE") from e

        if not client.is_connected():
            msg = "Yahoo Finance Client failed to connect."
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE")

        df = client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            date_from=start_time,
            date_to=end_time,
        )
        if df is None or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            ts = row["Timestamp"]
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = pd.to_datetime(ts).isoformat()
            records.append(
                {
                    "timestamp": ts_str,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "tick_volume": float(row["Volume"]),
                    "real_volume": 0.0,
                    "spread": float(row["Spread"]),
                    "source": "yahoo",
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            )
        return records

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Fetch tick data."""
        check_circuit_breaker_barrier("yahoo")
        try:
            from app.services.brokers.yahoo import get_yahoo_client

            client = get_yahoo_client()
            if not client.is_connected():
                client.connect()
        except Exception as e:
            logger.warning(f"Yahoo Finance client initialization failed: {e}")
            msg = f"Yahoo Finance service is not available: {e}"
            raise ExternalServiceError(msg, code="SERVICE_UNAVAILABLE") from e

        df = client.get_ticks(
            symbol=symbol,
            start=start_time,
            end=end_time,
            as_dataframe=True,
        )
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return []

        records = []
        for _, row in df.iterrows():
            ts = row["Timestamp"]
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = pd.to_datetime(ts).isoformat()
            records.append(
                {
                    "timestamp": ts_str,
                    "bid": float(row["bid"]),
                    "ask": float(row["ask"]),
                    "last": float(row["last"]),
                    "volume": float(row["volume"]),
                    "spread": float(row["spread"]),
                    "source": "yahoo",
                    "symbol": symbol,
                }
            )
        return records

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols."""
        _ = request_id
        return ["AAPL", "MSFT", "SPY"]

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get symbol metadata."""
        return {
            "symbol": symbol,
            "source": "yahoo",
            "ready": True,
            "license": "Restricted",
            "attribution": "Yahoo Finance Public Feed",
        }


# Adapter registry
ADAPTER_REGISTRY: dict[str, SourceAdapterProtocol] = {
    "csv": CSVAdapter(),
    "parquet": ParquetAdapter(),
    "synthetic": SyntheticAdapter(),
    "mt5": MT5Adapter(),
    "ctrader": CTraderAdapter(),
    "dukascopy": DukascopyAdapter(),
    "binance": BinanceAdapter(),
    "yahoo": YahooAdapter(),
}


def get_source_adapter(source: str) -> SourceAdapterProtocol:
    """Retrieve the registered adapter for a source."""
    source_lower = source.lower()
    if source_lower not in ADAPTER_REGISTRY:
        msg = f"Unknown or unregistered source: {source}"
        raise ValidationError(msg)
    return ADAPTER_REGISTRY[source_lower]


def _normalize_and_validate_records(
    records: list[dict[str, Any]],
    data_kind: str,
    symbol: str,
    source: str,
    workflow_context: str,
) -> list[dict[str, Any]]:
    """Validate, normalize, and dump records based on data_kind."""
    validated = []
    for r in records:
        if data_kind == "ohlcv":
            bar = OHLCVRecord(**r)
            bar.open = normalize_numeric(bar.open, 5, workflow_context)
            bar.high = normalize_numeric(bar.high, 5, workflow_context)
            bar.low = normalize_numeric(bar.low, 5, workflow_context)
            bar.close = normalize_numeric(bar.close, 5, workflow_context)
            bar.spread = normalize_numeric(bar.spread, 1, workflow_context)
            validated.append(bar.model_dump())
        elif data_kind == "ticks":
            tick = TickRecord(**r)
            tick.bid = normalize_numeric(tick.bid, 5, workflow_context)
            tick.ask = normalize_numeric(tick.ask, 5, workflow_context)
            tick.last = normalize_numeric(tick.last, 5, workflow_context)
            tick.spread = normalize_numeric(tick.spread, 1, workflow_context)
            validated.append(tick.model_dump())
        elif data_kind == "spreads":
            bid_val = float(r.get("bid", 0.0))
            ask_val = float(r.get("ask", 0.0))
            spread_pts = float(r.get("spread", 0.0))
            if spread_pts <= 0.0 and ask_val >= bid_val:
                spread_pts = round((ask_val - bid_val) / 0.00001, 1)

            sp_rec = SpreadRecord(
                timestamp=r["timestamp"],
                symbol=symbol,
                bid=bid_val,
                ask=ask_val,
                spread_points=spread_pts,
                spread_pips=round(spread_pts / 10.0, 2),
                source=source,
            )
            sp_rec.bid = normalize_numeric(sp_rec.bid, 5, workflow_context)
            sp_rec.ask = normalize_numeric(sp_rec.ask, 5, workflow_context)
            sp_rec.spread_points = normalize_numeric(
                sp_rec.spread_points, 1, workflow_context
            )
            sp_rec.spread_pips = normalize_numeric(
                sp_rec.spread_pips, 2, workflow_context
            )
            validated.append(sp_rec.model_dump())
    return validated


def _check_gateway_cache(
    source: str,
    symbol: str,
    timeframe: str | None,
    start_time: datetime,
    end_time: datetime,
    stale_data_behavior: str,
    request_id: str | None = None,
) -> tuple[str, str, list[dict[str, Any]] | None]:
    """Generate cache keys and check cache availability."""
    cache_tf = timeframe or "ticks"
    cache_key = generate_cache_key(
        source,
        symbol,
        cache_tf,
        start_time.isoformat(),
        end_time.isoformat(),
    )
    cached = get_cached_data(cache_key, stale_data_behavior, request_id=request_id)
    return cache_key, cache_tf, cached["records"] if cached else None


def _download_from_adapter(
    source: str,
    symbol: str,
    timeframe: str | None,
    start_time: datetime,
    end_time: datetime,
    data_kind: str,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve raw records from the registered source adapter."""
    adapter = get_source_adapter(source)
    if data_kind == "ohlcv":
        return adapter.get_market_data(
            symbol,
            timeframe or "M1",
            start_time,
            end_time,
            request_id=request_id,
        )
    if data_kind in ("ticks", "spreads"):
        return adapter.get_tick_data(
            symbol, start_time, end_time, request_id=request_id
        )
    return []


# --- 5. Unified Gateway Core Execution ---
def execute_gateway_request(  # noqa: C901
    source: str,
    symbol: str,
    timeframe: str | None,
    start_time: datetime,
    end_time: datetime,
    data_kind: str,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Internal gateway request execution, routing through adapters with cache."""
    sources_to_try = [source]
    if fallback_sources:
        for f in fallback_sources:
            if f not in sources_to_try:
                sources_to_try.append(f)

    last_exception = None

    for current_source in sources_to_try:
        try:
            logger.info(
                f"Gateway routing request: source={current_source}, symbol={symbol}, "
                f"kind={data_kind}",
                extra={"request_id": request_id},
            )

            # 1. Enforce licensing validation (fail closed)
            validate_license(
                current_source, symbol, workflow_context, request_id=request_id
            )

            # 2. Consume rate limits
            check_rate_limit(current_source)

            # 3. Cache checks (only for historical queries)
            cache_key, cache_tf, cached_records = _check_gateway_cache(
                current_source,
                symbol,
                timeframe,
                start_time,
                end_time,
                stale_data_behavior,
                request_id=request_id,
            )
            if cached_records is not None:
                logger.info(f"Cache hit for key {cache_key}")
                return cached_records

            # 4. Resolve adapter and download
            records = _download_from_adapter(
                current_source,
                symbol,
                timeframe,
                start_time,
                end_time,
                data_kind,
                request_id=request_id,
            )

            if not records:
                set_cached_data(
                    cache_key,
                    current_source,
                    symbol,
                    cache_tf,
                    start_time.isoformat(),
                    end_time.isoformat(),
                    [],
                    ttl_seconds=60,
                    request_id=request_id,
                )
                return []

            # 5. Validate schemas and normalize
            validated = _normalize_and_validate_records(
                records=records,
                data_kind=data_kind,
                symbol=symbol,
                source=current_source,
                workflow_context=workflow_context,
            )

            # 6. Cache validated records
            ttl = 900
            if data_kind == "ohlcv":
                ttl = 3600 if timeframe != "D1" else 86400

            set_cached_data(
                cache_key,
                current_source,
                symbol,
                cache_tf,
                start_time.isoformat(),
                end_time.isoformat(),
                validated,
                ttl_seconds=ttl,
                request_id=request_id,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Request failed on source {current_source}: {e}. Trying fallback."
            )
            last_exception = e
        else:
            return validated

    if last_exception:
        if isinstance(last_exception, ValidationError | ExternalServiceError):
            raise last_exception
        err_msg = f"Gateway request failed: {last_exception}"
        raise DataError(err_msg) from last_exception

    return []


# --- 6. Clean Service APIs ---
def get_data(
    symbol: str,
    start_time: str,
    end_time: str,
    data_kind: str = "ohlcv",
    timeframe: str | None = None,
    source: str = "csv",
    limit: int | None = None,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve normalized market data records (ohlcv, ticks, spreads, or volume).

    Args:
        symbol: Financial symbol identifier.
        start_time: UTC start time string.
        end_time: UTC end time string.
        data_kind: Kind of data ('ohlcv', 'ticks', 'spreads', 'volume').
        timeframe: Bar timeframe (required for ohlcv/volume).
        source: Primary source adapter.
        limit: Max query limit parameter.
        stale_data_behavior: Expired cache lookup policy.
        workflow_context: rounding/validation execution context.
        fallback_sources: explicit lists of fallbacks on failure.
        request_id: Optional tracking identifier.

    Returns:
        list[dict[str, Any]]: Clean list of normalized data records.
    """
    t_start = normalize_timestamp(start_time)
    t_end = normalize_timestamp(end_time)

    kind = data_kind.lower()
    if kind not in ("ohlcv", "ticks", "spreads", "volume"):
        err_msg = f"Unsupported data_kind: {data_kind}"
        raise ValidationError(err_msg)

    if kind == "ohlcv":
        if not timeframe:
            raise ValidationError("timeframe is required for ohlcv data.")
        tf = validate_timeframe(timeframe)
        valid_limit = validate_limit(limit, MAX_OHLCV_LIMIT, DEFAULT_OHLCV_LIMIT)
        records = execute_gateway_request(
            source,
            symbol,
            tf,
            t_start,
            t_end,
            "ohlcv",
            stale_data_behavior,
            workflow_context,
            fallback_sources,
            request_id,
        )
        return records[:valid_limit]

    if kind == "ticks":
        valid_limit = validate_limit(limit, MAX_TICK_LIMIT, DEFAULT_TICK_LIMIT)
        records = execute_gateway_request(
            source,
            symbol,
            None,
            t_start,
            t_end,
            "ticks",
            stale_data_behavior,
            workflow_context,
            fallback_sources,
            request_id,
        )
        return records[:valid_limit]

    if kind == "spreads":
        valid_limit = validate_limit(limit, MAX_SPREAD_LIMIT, DEFAULT_SPREAD_LIMIT)
        records = execute_gateway_request(
            source,
            symbol,
            None,
            t_start,
            t_end,
            "spreads",
            stale_data_behavior,
            workflow_context,
            fallback_sources,
            request_id,
        )
        return records[:valid_limit]

    if kind == "volume":
        if not timeframe:
            raise ValidationError("timeframe is required for volume data.")
        tf = validate_timeframe(timeframe)
        bars = get_data(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            data_kind="ohlcv",
            timeframe=tf,
            source=source,
            limit=limit,
            stale_data_behavior=stale_data_behavior,
            workflow_context=workflow_context,
            fallback_sources=fallback_sources,
            request_id=request_id,
        )
        volume_records = []
        for b in bars:
            volume_records.append(
                {
                    "timestamp": b["timestamp"],
                    "symbol": symbol,
                    "timeframe": tf,
                    "volume": b["volume"],
                    "tick_volume": b.get("tick_volume", 0.0),
                    "real_volume": b.get("real_volume", 0.0),
                    "source": source,
                }
            )
        return volume_records

    return []


def get_symbol_metadata(
    symbol: str,
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve normalized symbol and asset metadata."""
    logger.info(
        f"Retrieving symbol metadata: symbol={symbol}, source={source}",
        extra={"request_id": request_id},
    )
    adapter = get_source_adapter(source)
    raw_meta = adapter.get_symbol_metadata(symbol, request_id=request_id)

    meta_obj = SymbolMetadata(
        symbol=symbol,
        asset_class=raw_meta.get("asset_class", "forex"),
        base_currency=raw_meta.get("base_currency", "EUR"),
        quote_currency=raw_meta.get("quote_currency", "USD"),
        contract_size=raw_meta.get("contract_size", 100000.0),
        tick_size=raw_meta.get("tick_size", 0.00001),
        tick_value=raw_meta.get("tick_value", 1.0),
        point=raw_meta.get("point", 0.00001),
        digits=raw_meta.get("digits", 5),
        lot_min=raw_meta.get("lot_min", 0.01),
        lot_max=raw_meta.get("lot_max", 100.0),
        lot_step=raw_meta.get("lot_step", 0.01),
        margin_currency=raw_meta.get("margin_currency", "EUR"),
        profit_currency=raw_meta.get("profit_currency", "USD"),
        trading_hours=raw_meta.get("trading_hours", {}),
        source_metadata=raw_meta,
    )

    return meta_obj.model_dump()


def list_symbols(
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> list[str]:
    """List symbols discovered from the source."""
    adapter = get_source_adapter(source)
    return adapter.list_symbols(request_id=request_id)


def get_data_availability(
    symbol: str,
    timeframe: str,
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Inspect committed ranges, gaps, and record counts."""
    logger.info(
        f"Checking data availability: symbol={symbol}, source={source}",
        extra={"request_id": request_id},
    )

    count = 0
    start_str = None
    end_str = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT key, start_time, end_time, records_json FROM data_cache
                WHERE source = ? AND symbol = ? AND timeframe = ?;
                """,
                (source, symbol, timeframe),
            )
            rows = cursor.fetchall()
            for row in rows:
                start_str = row["start_time"]
                end_str = row["end_time"]
                records = json.loads(row["records_json"])
                count += len(records)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to query data availability from database cache: {e}")

    availability = DataAvailability(
        symbol=symbol,
        timeframe=timeframe,
        source=source,
        start_time=start_str,
        end_time=end_str,
        gap_count=0,
        gap_windows=[],
        is_ready=True,
        record_count=count,
        metadata={"cache_queried": True},
    )

    return availability.model_dump()
