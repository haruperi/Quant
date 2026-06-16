"""Limits, precision, timeframe, and license validation rules.

Consolidates the functionality of limits, precision, timeframes, and licensing logic
into a single data-validation layer.
"""

import zoneinfo
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.services.data.storage import db_helper
from app.utils.errors import ValidationError
from app.utils.logger import logger

# --- 1. Limits Rules ---
DEFAULT_OHLCV_LIMIT: int = 5000
MAX_OHLCV_LIMIT: int = 50000

DEFAULT_TICK_LIMIT: int = 10000
MAX_TICK_LIMIT: int = 250000

DEFAULT_SPREAD_LIMIT: int = 10000
MAX_SPREAD_LIMIT: int = 250000

MAX_SYNTHETIC_BARS: int = 100000
MAX_SYNTHETIC_TICKS: int = 250000
MAX_PERSISTED_SYNTHETIC_SIZE: int = 1000000

DEFAULT_BACKFILL_OHLCV_CHUNK_RECORDS: int = 100000
DEFAULT_BACKFILL_OHLCV_CHUNK_DAYS: int = 30

DEFAULT_BACKFILL_TICK_CHUNK_RECORDS: int = 1000000
DEFAULT_BACKFILL_TICK_CHUNK_DAYS: int = 1

DEFAULT_CACHE_TTL_DAILY: int = 86400
DEFAULT_CACHE_TTL_INTRADAY: int = 3600
DEFAULT_CACHE_TTL_TICK: int = 900
DEFAULT_CACHE_TTL_LIVE: int = 0
MAX_CACHE_TTL_OVERRIDE_DAYS: int = 7

MAX_SYMBOLS_PER_JOB: int = 500
MAX_TIMEFRAMES_PER_JOB: int = 20
MIN_SCHEDULER_FREQUENCY_SECONDS: int = 60


def validate_limit(limit: int | None, max_allowed: int, default_value: int) -> int:
    """Validate and return a query limit.

    Args:
        limit: The requested limit value.
        max_allowed: The maximum allowed value for the limit.
        default_value: The default value to return if the requested limit is None.

    Returns:
        int: The validated limit value.

    Raises:
        ValidationError: If the limit is non-positive or exceeds max_allowed.
    """
    if limit is None:
        return default_value

    if limit <= 0:
        logger.error(f"Requested limit {limit} is non-positive.")
        raise ValidationError("Requested limit must be positive.")

    if limit > max_allowed:
        err_msg = (
            f"Requested limit {limit} exceeds maximum allowed limit {max_allowed}."
        )
        logger.error(err_msg)
        raise ValidationError(err_msg)

    return limit


# --- 2. Precision Rounding Policies ---
NumericType = int | float | str | Decimal


def normalize_numeric(
    value: NumericType, digits: int, workflow_context: str
) -> str | float:
    """Normalize numeric values according to workflow rules.

    Args:
        value: The raw numerical value (int, float, str, or Decimal).
        digits: Number of decimal places to round/quantize to.
        workflow_context: The execution context (e.g. 'research', 'backtest',
          'validation', 'risk', 'execution_bound').

    Returns:
        str | float: Decimal string representation for validation/risk/execution
                     workflows, or float for research.
    """
    if value is None:
        raise ValidationError("Numeric value cannot be None.")

    try:
        dec_val = Decimal(str(value))
    except Exception as e:
        err_msg = f"Failed to convert value {value} to Decimal: {e}"
        logger.error(err_msg)
        raise ValidationError(err_msg) from e

    # Quantize using ROUND_HALF_UP
    quant_str = f"1.{'0' * digits}" if digits > 0 else "1"
    quantized = dec_val.quantize(Decimal(quant_str), rounding=ROUND_HALF_UP)

    if workflow_context in (
        "backtest",
        "validation",
        "risk",
        "execution_bound",
    ):
        return f"{quantized:.{digits}f}"

    return float(quantized)


def validate_step_alignment(
    value: NumericType, step_size: NumericType, workflow_context: str
) -> None:
    """Validate that a value aligns perfectly with the allowed step size.

    Forces strict fail-closed precision mismatch error check for execution and
    risk contexts.

    Args:
        value: The numeric value (e.g., price, lot size).
        step_size: The alignment step (e.g., tick size, lot step).
        workflow_context: The active execution context.

    Raises:
        ValidationError: If alignment is invalid or precision mismatch is
        detected.
    """
    if value is None or step_size is None:
        raise ValidationError("Value and step size must be defined.")

    try:
        dec_val = Decimal(str(value))
        dec_step = Decimal(str(step_size))
    except Exception as e:
        err_conv = (
            f"Failed step alignment conversion. value={value}, step={step_size}: {e}"
        )
        logger.error(err_conv)
        raise ValidationError("Invalid numeric/step conversion.") from e

    if dec_step <= 0:
        raise ValidationError("Step size must be strictly positive.")

    remainder = dec_val % dec_step
    tolerance = Decimal("1e-9")
    if remainder > tolerance and (dec_step - remainder) > tolerance:
        warn_msg = (
            f"Precision mismatch detected: value={value} "
            f"is not a multiple of step={step_size}"
        )
        logger.warning(warn_msg)
        if workflow_context in ("risk", "execution_bound"):
            err_msg = (
                f"Precision mismatch. value {value} "
                f"does not align with step {step_size}."
            )
            raise ValidationError(err_msg)


# --- 3. Timeframes & Sessions ---
VALID_TIMEFRAMES: set[str] = {
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

SYDNEY_START: int = 22
SYDNEY_END: int = 7
TOKYO_START: int = 0
TOKYO_END: int = 9
LONDON_START: int = 8
LONDON_END: int = 17
NY_START: int = 13
NY_END: int = 22
HOURS_IN_DAY: int = 24
SECONDS_IN_HOUR: int = 3600


def validate_timeframe(timeframe: str) -> str:
    """Validate that a timeframe name is supported."""
    if not timeframe:
        raise ValidationError("Timeframe cannot be empty.")

    upper_tf = timeframe.upper()
    if upper_tf not in VALID_TIMEFRAMES:
        err_msg = f"Unsupported timeframe: {timeframe}"
        logger.error(err_msg)
        raise ValidationError(err_msg)

    return upper_tf


def validate_timezone(tz_name: str) -> str:
    """Validate that a timezone string is a valid IANA timezone."""
    try:
        zoneinfo.ZoneInfo(tz_name)
    except Exception as e:
        err_msg = f"Invalid timezone: {tz_name}"
        logger.error(f"Invalid IANA timezone name {tz_name}: {e}")
        raise ValidationError(err_msg) from e
    return tz_name


def get_market_hours(symbol: str, request_id: str | None = None) -> dict[str, Any]:
    """Get timezone-aware market hours for a given symbol."""
    logger.info(
        f"Retrieving market hours for {symbol}",
        extra={"request_id": request_id},
    )
    return {
        "symbol": symbol,
        "timezone": "UTC",
        "trading_days": {
            "Monday": {"start": "00:00", "end": "24:00"},
            "Tuesday": {"start": "00:00", "end": "24:00"},
            "Wednesday": {"start": "00:00", "end": "24:00"},
            "Thursday": {"start": "00:00", "end": "24:00"},
            "Friday": {"start": "00:00", "end": "24:00"},
        },
        "historical_hours_supported": False,
    }


def get_trading_sessions(
    start_time: datetime, end_time: datetime, request_id: str | None = None
) -> list[dict[str, Any]]:
    """Return normalized trading session windows and labels."""
    logger.info(
        f"Generating session windows between {start_time} and {end_time}",
        extra={"request_id": request_id},
    )
    sessions = []
    current = start_time.replace(minute=0, second=0, microsecond=0)
    while current < end_time:
        hour = current.hour
        active = []
        if hour >= SYDNEY_START or hour < SYDNEY_END:
            active.append("Sydney")
        if TOKYO_START <= hour < TOKYO_END:
            active.append("Tokyo")
        if LONDON_START <= hour < LONDON_END:
            active.append("London")
        if NY_START <= hour < NY_END:
            active.append("New York")

        for session in active:
            next_hour = (current.hour + 1) % HOURS_IN_DAY
            sessions.append(
                {
                    "session_name": session,
                    "start": current.isoformat(),
                    "end": (current.replace(hour=next_hour)).isoformat(),
                }
            )
        current = datetime.fromtimestamp(current.timestamp() + SECONDS_IN_HOUR, tz=UTC)

    return sessions


# --- 4. Licensing Constraints ---
DEFAULT_LICENSE_REGISTRY: dict[str, dict[str, Any]] = {
    "csv": {
        "license_type": "Open",
        "redistribution_restricted": False,
        "attribution": "Local CSV Ingestion",
    },
    "parquet": {
        "license_type": "Open",
        "redistribution_restricted": False,
        "attribution": "Local Parquet Ingestion",
    },
    "synthetic": {
        "license_type": "Permissive",
        "redistribution_restricted": False,
        "attribution": "HaruQuant Synthetic Bar/Tick Generator",
    },
    "mt5": {
        "license_type": "Proprietary",
        "redistribution_restricted": True,
        "attribution": "MetaTrader 5 Terminal Gateway Data",
    },
    "ctrader": {
        "license_type": "Proprietary",
        "redistribution_restricted": True,
        "attribution": "cTrader OpenAPI Client Feed",
    },
    "dukascopy": {
        "license_type": "Restricted",
        "redistribution_restricted": True,
        "attribution": "Dukascopy Community Feed",
    },
    "binance": {
        "license_type": "Restricted",
        "redistribution_restricted": True,
        "attribution": "Binance Public API Data",
    },
    "yahoo": {
        "license_type": "Restricted",
        "redistribution_restricted": True,
        "attribution": "Yahoo Finance Public Feed",
    },
}


def _ensure_licensing_table() -> None:
    """Ensure data_licenses table exists in database."""
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_licenses (
                    source TEXT,
                    symbol TEXT,
                    license_type TEXT NOT NULL,
                    redistribution_restricted INTEGER DEFAULT 0,
                    attribution TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (source, symbol)
                );
                """
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Could not initialize data_licenses table: {e}")


# Initialize table on load
_ensure_licensing_table()


def register_license(
    source: str,
    symbol: str,
    license_type: str,
    *,
    redistribution_restricted: bool,
    attribution: str | None = None,
    request_id: str | None = None,
) -> None:
    """Register or update license metadata for a source and symbol."""
    logger.info(
        f"Registering license: source={source}, symbol={symbol}",
        extra={"request_id": request_id},
    )

    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_licenses (
                    source, symbol, license_type, redistribution_restricted,
                    attribution, created_at
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    source,
                    symbol,
                    license_type,
                    1 if redistribution_restricted else 0,
                    attribution,
                    datetime.now(UTC).isoformat(),
                ),
            )
    except Exception as e:
        logger.error(
            f"Failed to save license for {source}:{symbol} to DB: {e}",
            extra={"request_id": request_id},
        )
        msg = f"Failed to register license: {e}"
        raise ValidationError(msg) from e


def validate_license(
    source: str,
    symbol: str,
    workflow_context: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate licensing constraints for a given workflow context."""
    logger.debug(
        f"Validating license: source={source}, symbol={symbol}, "
        f"context={workflow_context}",
        extra={"request_id": request_id},
    )

    license_info = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM data_licenses
                WHERE source = ? AND (symbol = ? OR symbol = '*');
                """,
                (source, symbol),
            )
            row = cursor.fetchone()
            if row:
                license_info = {
                    "license_type": row["license_type"],
                    "redistribution_restricted": bool(row["redistribution_restricted"]),
                    "attribution": row["attribution"],
                }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Database query error during license check: {e}")

    if not license_info and source in DEFAULT_LICENSE_REGISTRY:
        license_info = DEFAULT_LICENSE_REGISTRY[source]
        logger.debug(f"Resolved default license for source={source}")

    if not license_info:
        err_msg = (
            f"Missing license metadata for source={source}, symbol={symbol}. "
            f"Operation rejected (LICENSE_RESTRICTION)."
        )
        logger.error(err_msg, extra={"request_id": request_id})
        raise ValidationError("LICENSE_RESTRICTION: Metadata missing.")

    if license_info["redistribution_restricted"] and workflow_context in (
        "risk",
        "execution_bound",
    ):
        err_restrict = (
            f"Workflow {workflow_context} rejected due to redistribution "
            f"restrictions on source={source}, symbol={symbol} "
            f"(LICENSE_RESTRICTION)."
        )
        logger.error(err_restrict, extra={"request_id": request_id})
        raise ValidationError("LICENSE_RESTRICTION: Redistribution limits.")

    return license_info
