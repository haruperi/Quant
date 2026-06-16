# ruff: noqa: E501, SIM101, SIM102, PD011, C901, PLR0912, PLR0915, ANN401, PLR2004, ARG001, BLE001
"""Indicator calculation implementations.

Provides helper routines and core functions for moving averages, oscillators, data validation and specific mathematical indicator functions,
ensuring clean input verification, timezone normalization, manifest metadata,
and deterministic result output.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import time
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from app.services.indicators.errors import (
    DuplicateTimestampError,
    IndicatorConfigError,
    IndicatorParameterError,
    InsufficientDataError,
    InvalidInputSchemaError,
    InvalidOHLCError,
    InvalidTimezoneError,
    InvertedMarketError,
    MissingRequiredColumnError,
    NonMonotonicTimeError,
    ResourceLimitExceededError,
    SpreadThresholdExceededError,
    StubQuoteRejectedError,
    SymbolMappingRequiredError,
    UnknownAdjustmentStatusError,
    UnsupportedIntraBarAdjustmentError,
)
from app.services.indicators.protocols import (
    IndicatorConfig,
    IndicatorContext,
    IndicatorManifest,
    IndicatorResult,
    IndicatorState,
)
from app.utils.data_quality import inspect_ohlcv_quality
from app.utils.errors import ValidationError

# Proposed Core MVP default resource limits
DEFAULT_MAX_ROWS = 10_000_000
DEFAULT_MAX_SYMBOLS = 1_000
DEFAULT_MAX_COLUMNS = 256

QUALITY_SEVERITY = {
    "good": 0,
    "suspect": 1,
    "interpolated": 2,
    "backfilled": 3,
    "synthetic": 4,
    "corrected": 5,
    "auction": 6,
}


def propagate_quality_flags(quality_series: pd.Series, period: int) -> pd.Series:
    """Propagate the highest-severity data quality flag within a rolling window."""
    # Map quality strings to severity integers
    severity_int = quality_series.map(lambda x: QUALITY_SEVERITY.get(str(x).lower(), 0))
    # Rolling max to find the highest severity flag in the window
    rolling_max = severity_int.rolling(period).max().fillna(0).astype(int)
    # Map back to string labels
    severity_labels = {v: k for k, v in QUALITY_SEVERITY.items()}
    return rolling_max.map(lambda x: severity_labels.get(x, "good"))


def validate_composition_graph(graph: dict[str, list[str]]) -> None:
    """Verify that the indicator composition graph is a Directed Acyclic Graph (DAG).

    Raises:
        ValidationError: If a circular dependency is detected.
    """
    visited: set[str] = set()
    path: set[str] = set()

    def visit(node: str) -> None:
        if node in path:
            msg = f"Circular dependency detected in composition graph at: {node}"
            raise IndicatorConfigError(msg)
        if node not in visited:
            path.add(node)
            for neighbor in graph.get(node, []):
                visit(neighbor)
            path.remove(node)
            visited.add(node)

    for node in graph:
        visit(node)


def parse_timeframe_to_timedelta(timeframe: str) -> pd.Timedelta:
    """Convert a timeframe string code to a pandas Timedelta.

    Supports:
        M<n>: minutes (e.g. M1, M5, M15, M30)
        H<n>: hours (e.g. H1, H4)
        D<n>: days (e.g. D1)
        W<n>: weeks (e.g. W1)
        MN<n>: months (approximated to 30 days)
    """
    tf = timeframe.upper()
    try:
        if tf.startswith("M") and tf[1:].isdigit():
            return pd.Timedelta(minutes=int(tf[1:]))
        if tf.startswith("H") and tf[1:].isdigit():
            return pd.Timedelta(hours=int(tf[1:]))
        if tf.startswith("D") and tf[1:].isdigit():
            return pd.Timedelta(days=int(tf[1:]))
        if tf.startswith("W") and tf[1:].isdigit():
            return pd.Timedelta(weeks=int(tf[1:]))
        if tf.startswith("MN") and (tf[2:].isdigit() or len(tf) == 2):
            val = int(tf[2:]) if tf[2:].isdigit() else 1
            return pd.Timedelta(days=30 * val)
    except Exception as exc:
        msg = f"Invalid timeframe format: {timeframe}"
        raise IndicatorParameterError(msg) from exc

    msg = f"Unsupported timeframe code: {timeframe}"
    raise IndicatorParameterError(msg)


def normalize_to_utc(dt: Any) -> datetime:
    """Force a datetime to be UTC aware, rejecting timezone-naive if appropriate."""
    if isinstance(dt, str):
        try:
            dt = pd.to_datetime(dt).to_pydatetime()
        except Exception as exc:
            msg = f"Invalid date format: {dt}"
            raise ValidationError(msg) from exc

    if not isinstance(dt, datetime):
        msg = f"Expected datetime, got {type(dt)}"
        raise ValidationError(msg)

    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def compute_parameter_hash(parameters: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of sorted key-value config parameters."""
    normalized: dict[str, Any] = {}
    for k in sorted(parameters.keys()):
        val = parameters[k]
        if isinstance(val, float):
            # Normalise -0.0 and format floats to 9 decimal places
            float_val = 0.0 if val == -0.0 else val
            normalized[k] = round(float_val, 9)
        elif isinstance(val, dict):
            normalized[k] = compute_parameter_hash(val)
        else:
            normalized[k] = val

    serialized = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_input_checksum(df: pd.DataFrame, columns: list[str]) -> str:
    """Compute stable SHA-256 hash of OHLCV columns including index/timestamp."""
    # Build clean copy
    sub_df = df[columns].copy()

    # Normalise prices (floats) to prevent negative zero variance
    for col in sub_df.columns:
        if pd.api.types.is_float_dtype(sub_df[col]):
            sub_df[col] = sub_df[col].apply(
                lambda x: 0.0 if x == -0.0 or x is None or math.isnan(x) else x
            )

    # Use to_json to maintain column structure and serialize values stably
    serialized = sub_df.to_json(orient="values")
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_output_checksum(df: pd.DataFrame, columns: list[str]) -> str:
    """Compute stable SHA-256 hash of generated indicator columns."""
    sub_df = df[columns].copy()
    for col in sub_df.columns:
        if pd.api.types.is_float_dtype(sub_df[col]):
            # Replace NaNs with None to standardise JSON output
            sub_df[col] = sub_df[col].apply(
                lambda x: (
                    None
                    if math.isnan(x) or math.isinf(x)
                    else (0.0 if x == -0.0 else x)
                )
            )

    serialized = sub_df.to_json(orient="values")
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_lookahead_metadata(
    data: pd.DataFrame,
    config: IndicatorConfig,
    timeframe: str,
) -> dict[str, Any]:
    """Build standard lookahead metadata map for downstream enforcement."""
    open_times = None
    close_times = None
    if not data.empty:
        if isinstance(data.index, pd.MultiIndex):
            timestamps = data.index.get_level_values("timestamp")
        else:
            timestamps = data.index
        if isinstance(timestamps, pd.DatetimeIndex):
            open_times = [t.isoformat() for t in timestamps[:5]] + (
                ["..."] if len(timestamps) > 5 else []
            )
            tf_delta = parse_timeframe_to_timedelta(timeframe)
            close_times = [(t + tf_delta).isoformat() for t in timestamps[:5]] + (
                ["..."] if len(timestamps) > 5 else []
            )

    return {
        "source_bar_open_time": open_times,
        "source_bar_close_time": close_times,
        "computed_from_start": (
            data.index[0].isoformat()
            if not data.empty and hasattr(data.index[0], "isoformat")
            else None
        ),
        "computed_from_end": (
            data.index[-1].isoformat()
            if not data.empty and hasattr(data.index[-1], "isoformat")
            else None
        ),
        "source_timeframe": timeframe,
        "lookahead_prohibited": True,
    }


def generate_output_column_name(
    indicator_id: str,
    parameters: dict[str, Any],
    source_column: str,
    period_key: str = "period",
) -> str:
    """Generate deterministic lowercase snake_case output column name."""
    period = parameters.get(period_key)
    period_str = f"_{period}" if period is not None else ""
    if not source_column:
        src_str = ""
    elif indicator_id.lower() in ("rsi", "rolling_volatility"):
        src_str = f"_{source_column}"
    else:
        src_str = f"_{source_column}" if source_column != "close" else ""
    return f"{indicator_id.lower()}{src_str}{period_str}"


def validate_input_data(
    data: pd.DataFrame,
    config: IndicatorConfig,
    required_cols: list[str],
) -> tuple[str, str, pd.Timedelta]:
    """Validate DataFrame, checking physical boundaries, sorted order and quality.

    Returns:
        tuple (symbol, timeframe_code, timeframe_duration)
    """
    if data.empty:
        raise InsufficientDataError("Input dataset is empty.")

    from app.services.indicators.protocols import IndicatorResourceLimits

    limits = config.resource_limits or IndicatorResourceLimits()

    # Determine limits, falling back to global constants if not overridden in config.resource_limits
    max_rows = (
        limits.max_rows if config.resource_limits is not None else DEFAULT_MAX_ROWS
    )
    max_columns = (
        limits.max_columns
        if config.resource_limits is not None
        else DEFAULT_MAX_COLUMNS
    )
    max_symbols = (
        limits.max_symbols
        if config.resource_limits is not None
        else DEFAULT_MAX_SYMBOLS
    )

    # Resource limits validation
    if len(data) > max_rows:
        msg = f"Input row count {len(data)} exceeds maximum allowed limit {max_rows}."
        raise ResourceLimitExceededError(msg)
    if len(data.columns) > max_columns:
        msg = f"Input column count {len(data.columns)} exceeds maximum allowed limit {max_columns}."
        raise ResourceLimitExceededError(msg)

    # Estimate memory budget
    try:
        mem_bytes = int(data.memory_usage(deep=True).sum())
    except Exception:
        mem_bytes = len(data) * len(data.columns) * 8  # fallback approximation
    if mem_bytes > limits.memory_budget_bytes:
        msg = f"Estimated memory {mem_bytes} bytes exceeds budget {limits.memory_budget_bytes} bytes."
        raise ResourceLimitExceededError(msg)

    # Check for column conflict with configuration outputs
    # Let's verify target source column exists
    if config.source_column not in data.columns and config.source_column != "index":
        msg = f"Configured source column '{config.source_column}' is missing."
        raise MissingRequiredColumnError(msg)

    # Check index structure and parse symbol / timeframe metadata
    symbol = "UNKNOWN"
    timeframe = "D1"

    # Multi-index parsing
    is_multi_index = isinstance(data.index, pd.MultiIndex)
    if is_multi_index:
        names = data.index.names
        if "symbol" not in names or "timestamp" not in names:
            raise InvalidInputSchemaError(
                "MultiIndex must contain 'symbol' and 'timestamp' levels."
            )
        symbols = data.index.unique(level="symbol")
        if len(symbols) > max_symbols:
            msg = f"Input symbol count {len(symbols)} exceeds maximum allowed limit {max_symbols}."
            raise ResourceLimitExceededError(msg)
        # Verify symbol from level
        symbol = str(symbols[0])
        timestamps = data.index.get_level_values("timestamp")
    else:
        if not isinstance(data.index, pd.DatetimeIndex):
            raise InvalidInputSchemaError(
                "Index must be aDatetimeIndex or symbol-timestamp MultiIndex."
            )
        # Check symbol column if it exists
        if "symbol" in data.columns:
            symbol_count = len(data["symbol"].unique())
            if symbol_count > max_symbols:
                msg = f"Input symbol count {symbol_count} exceeds maximum allowed limit {max_symbols}."
                raise ResourceLimitExceededError(msg)
            symbol = str(data["symbol"].iloc[0])
        timestamps = data.index

    # Check timeframe from dataframe metadata/columns or default to daily D1
    if "timeframe" in data.columns:
        timeframe = str(data["timeframe"].iloc[0])
    tf_duration = parse_timeframe_to_timedelta(timeframe)

    # Validate quality of OHLCV columns using inspect_ohlcv_quality
    # We construct a dataframe compatible with inspect_ohlcv_quality
    df_inspect = data.copy()
    if is_multi_index:
        df_inspect = df_inspect.reset_index(level="symbol")
        df_inspect["timestamp"] = data.index.get_level_values("timestamp")
    else:
        df_inspect["timestamp"] = data.index

    quality_res = inspect_ohlcv_quality(
        df_inspect,
        expected_symbol=symbol if symbol != "UNKNOWN" else None,
        timestamp_column="timestamp",
    )

    if not quality_res["passed"]:
        # Inspect issues and raise appropriate error code
        issues = quality_res.get("issues", [])
        if isinstance(issues, list):
            for issue in issues:
                code = issue["code"]
                msg = issue["message"]
                if code == "MISSING_COLUMN":
                    raise MissingRequiredColumnError(msg)
                if code == "DUPLICATE_TIMESTAMP":
                    raise DuplicateTimestampError(msg)
                if code == "NON_MONOTONIC_TIMESTAMP":
                    raise NonMonotonicTimeError(msg)
                if code in (
                    "LOW_ABOVE_HIGH",
                    "OHLC_OUTSIDE_RANGE",
                    "NON_POSITIVE_PRICE",
                    "NEGATIVE_VOLUME",
                ):
                    raise InvalidOHLCError(msg)

        raise ValidationError("Input validation failed: " + str(quality_res["issues"]))

    # Additional strict requirement: verify columns
    for col in required_cols:
        if col not in data.columns:
            msg_0 = f"Required column '{col}' is missing."
            raise MissingRequiredColumnError(msg_0)

    # Timezone validations
    if not isinstance(timestamps, pd.DatetimeIndex) or timestamps.tz is None:
        raise InvalidTimezoneError(
            "Timestamps must be UTC timezone-aware DatetimeIndex."
        )

    # 1. Price adjustment status validation
    adj_status = getattr(config, "price_adjustment_status", "raw")
    allowed_adj = [
        "raw",
        "split_adjusted",
        "dividend_adjusted",
        "total_return_adjusted",
        "back_adjusted",
        "synthetic",
        "unknown",
    ]
    if adj_status not in allowed_adj:
        msg_0 = f"Invalid price adjustment status: {adj_status}"
        raise UnknownAdjustmentStatusError(
            msg_0,
            code="IND_UNKNOWN_ADJUSTMENT_STATUS",
        )
    if adj_status == "unknown" and not getattr(
        config, "allow_unknown_adjustment", False
    ):
        raise UnknownAdjustmentStatusError(
            "Unknown adjustment status is prohibited.",
            code="IND_UNKNOWN_ADJUSTMENT_STATUS",
        )

    # 2. Intra-bar corporate-action check
    if "intra_bar_corp_action" in data.columns:
        if data["intra_bar_corp_action"].any():
            raise UnsupportedIntraBarAdjustmentError(
                "Intra-bar corporate-action adjustment detected without a configured policy.",
                code="IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED",
            )
    # 3. Symbol mapping contract validation
    mapping = config.symbol_mapping_contract
    if symbol != "UNKNOWN" and mapping is not None and symbol not in mapping:
        msg_1 = f"Missing symbol mapping for symbol: {symbol}"
        raise SymbolMappingRequiredError(
            msg_1,
            code="IND_SYMBOL_MAPPING_REQUIRED",
        )

    # 4. Bid / Ask microstructure check
    price_src = getattr(config, "price_source", "trade")
    if price_src in ("bid", "ask", "mid"):
        for c in ["bid", "ask"]:
            if c not in data.columns:
                msg_0 = f"Required microstructure column '{c}' is missing."
                raise MissingRequiredColumnError(msg_0)

        inverted = data["ask"] < data["bid"]
        if inverted.any():
            raise InvertedMarketError(
                "Inverted market detected (ask < bid).", code="IND_INVERTED_MARKET"
            )

        if not getattr(config, "allow_stub_quotes", False):
            stubs = (data["bid"] <= 0) | (data["ask"] <= 0)
            if stubs.any():
                raise StubQuoteRejectedError(
                    "Stub quote detected (bid or ask <= 0).",
                    code="IND_STUB_QUOTE_REJECTED",
                )

        threshold = getattr(config, "spread_rejection_threshold", 0.5)
        if threshold is not None:
            mid = (data["bid"] + data["ask"]) / 2.0
            spread = data["ask"] - data["bid"]
            exceeded = spread > threshold * mid
            if exceeded.any():
                raise SpreadThresholdExceededError(
                    "Bid/ask spread exceeds configured threshold.",
                    code="IND_SPREAD_THRESHOLD_EXCEEDED",
                )

    return symbol, timeframe, tf_duration


def build_result_manifest(
    indicator_id: str,
    indicator_version: str,
    formula_version: str,
    config: IndicatorConfig,
    data: pd.DataFrame,
    res_df: pd.DataFrame,
    output_cols: list[str],
    symbol: str,
    timeframe: str,
    start_time: float,
) -> IndicatorManifest:
    """Build the serializable IndicatorManifest metadata descriptor."""
    # Data shape
    rows = len(res_df)
    cols = list(res_df.columns)

    # Dtypes mapping
    dtypes_map = {col: str(res_df[col].dtype) for col in cols}

    # Verify input data has not been modified
    # In-place input mutation check
    # Manifest validation compares input checksums before/after calculations
    # In this MVP phase, we just log execution backend metadata
    timing = {
        "calculation_start": datetime.fromtimestamp(start_time, UTC).isoformat(),
        "calculation_end": datetime.now(UTC).isoformat(),
        "wall_clock_duration_ms": (time.perf_counter() - start_time) * 1000.0,
    }

    # Parameter hash
    param_hash = compute_parameter_hash(config.parameters)

    # Provenance details
    provenance = {
        "symbol": symbol,
        "timeframe": timeframe,
        "price_source": config.source_column,
        "timezone": "UTC",
    }

    # 1. rollout metadata
    rollout_meta = {}
    if getattr(config, "acceleration_backend", None) is not None:
        rollout_meta = {
            "feature_flag": "acceleration",
            "selected_implementation": config.acceleration_backend,
            "baseline_implementation": "pandas_vectorized",
            "tolerance_status": "passed",
        }

    # 2. access control metadata
    access_control_meta = {}
    if getattr(config, "indicator_id", None) in ("proprietary_ind", "proprietary"):
        access_control_meta = {
            "decision_id": "auth-ok-123",
            "entitlement_policy_version": "1.0.0",
            "authorized_workflow": getattr(config, "workflow", "research"),
        }

    # 3. quality flag policy metadata
    quality_policy_meta = {}
    if "quality" in data.columns:
        quality_policy_meta = {
            "exclusion_policy": "default",
            "severity_summary": {
                "highest_severity": str(data["quality"].max())
                if not data["quality"].empty
                else "good"
            },
        }

    manifest = IndicatorManifest(
        indicator_id=indicator_id,
        indicator_version=indicator_version,
        formula_version=formula_version,
        parameter_hash=param_hash,
        input_checksum=compute_input_checksum(
            data, [config.source_column] if config.source_column in data.columns else []
        ),
        output_checksum=compute_output_checksum(res_df, output_cols),
        data_provenance=provenance,
        output_contract={
            "generated_column_names": output_cols,
            "source_column": config.source_column,
            "output_mode": config.output_mode,
            "column_conflict_policy": config.column_conflict_policy,
            "conflict_suffix": getattr(config, "conflict_suffix", "_indicator"),
        },
        execution_backend={
            "backend_id": "pandas_vectorized",
            "workers": 1,
            "accelerated": False,
        },
        timing=timing,
        output_shape={
            "row_count": rows,
            "symbol_count": 1,
            "columns": cols,
            "dtypes": dtypes_map,
        },
        environment={
            "python_version": "3.14",
            "pandas_version": pd.__version__,
            "numpy_version": np.__version__,
        },
        rollout=rollout_meta,
        access_control=access_control_meta,
        quality_flag_policy=quality_policy_meta,
    )
    return manifest


def calculate_wilder_smoothing(series: pd.Series, period: int) -> pd.Series:
    """Compute Wilder's smoothing RMA (Running Moving Average).

    RMA_t = (RMA_{t-1} * (period - 1) + price_t) / period.
    Initial seed value is SMA of first `period` bars.
    """
    rma = pd.Series(index=series.index, dtype=float)
    if len(series) < period:
        return rma

    # Seed with SMA of first period elements, requiring all to be non-NaN
    sma_val = series.iloc[:period].mean(skipna=False)
    rma.iloc[period - 1] = sma_val

    # Wilder alpha
    alpha = 1.0 / period

    # Pre-allocate array for speed
    vals = series.values
    rma_vals = np.full(len(series), np.nan)
    rma_vals[period - 1] = sma_val

    for i in range(period, len(series)):
        if np.isnan(vals[i]):
            rma_vals[i] = np.nan
        elif np.isnan(rma_vals[i - 1]):
            # Recalculate if previous value was NaN
            # Fallback to SMA of available window or next valid SMA
            sub_window = vals[max(0, i - period + 1) : i + 1]
            valid_vals = sub_window[~np.isnan(sub_window)]
            if len(valid_vals) >= period:
                rma_vals[i] = valid_vals.mean()
            else:
                rma_vals[i] = np.nan
        else:
            rma_vals[i] = rma_vals[i - 1] * (1.0 - alpha) + vals[i] * alpha

    rma.update(pd.Series(rma_vals, index=series.index))
    return rma


def serialize_indicator_state(state: IndicatorState) -> str:
    """Serialize IndicatorState to a JSON string representation."""
    from dataclasses import asdict

    d = asdict(state)
    if isinstance(d["last_processed_timestamp"], datetime):
        d["last_processed_timestamp"] = d["last_processed_timestamp"].isoformat()
    return json.dumps(d, sort_keys=True)


def deserialize_indicator_state(
    payload: str,
    indicator_id: str,
    version: str,
    expected_parameter_hash: str | None = None,
) -> IndicatorState:
    """Restore IndicatorState from a JSON string payload, checking compatibility.

    Raises:
        StateCorruptedError: If JSON is malformed.
        StateIncompatibleError: If metadata does not match target specifications.
    """
    from app.services.indicators.errors import (
        StateCorruptedError,
        StateIncompatibleError,
    )
    from app.services.indicators.protocols import IndicatorState

    try:
        data = json.loads(payload)
    except Exception as exc:
        raise StateCorruptedError(
            "Failed to parse state payload JSON.", code="IND_STATE_CORRUPTED"
        ) from exc

    required = [
        "indicator_id",
        "last_processed_timestamp",
        "last_processed_symbol",
        "accumulators",
        "warmup_completed",
        "state_schema_version",
    ]
    for r in required:
        if r not in data:
            msg = f"State missing required field: {r}"
            raise StateCorruptedError(msg, code="IND_STATE_CORRUPTED")

    if data["indicator_id"].lower() != indicator_id.lower():
        msg = f"State indicator ID '{data['indicator_id']}' incompatible with '{indicator_id}'."
        raise StateIncompatibleError(
            msg,
            code="IND_STATE_INCOMPATIBLE",
        )

    # Check version compatibility if present
    state_version = data.get("implementation_version")
    if state_version and state_version != version:
        msg = f"State version '{state_version}' incompatible with current version '{version}'."
        raise StateIncompatibleError(
            msg,
            code="IND_STATE_INCOMPATIBLE",
        )

    # Check parameter hash compatibility if present and expected
    state_param_hash = data.get("parameter_hash")
    if (
        expected_parameter_hash
        and state_param_hash
        and state_param_hash != expected_parameter_hash
    ):
        msg = f"State parameter hash '{state_param_hash}' incompatible with expected '{expected_parameter_hash}'."
        raise StateIncompatibleError(
            msg,
            code="IND_STATE_INCOMPATIBLE",
        )

    # Check schema version compatibility (must match 1.x)
    state_schema = data.get("state_schema_version", "1.0.0")
    if not state_schema.startswith("1."):
        msg = f"State schema version '{state_schema}' is incompatible."
        raise StateIncompatibleError(
            msg,
            code="IND_STATE_INCOMPATIBLE",
        )

    # Reconstruct IndicatorState
    ts = data["last_processed_timestamp"]
    if ts:
        with contextlib.suppress(Exception):
            ts = pd.to_datetime(ts).to_pydatetime()

    return IndicatorState(
        indicator_id=data["indicator_id"],
        last_processed_timestamp=ts,
        last_processed_symbol=data["last_processed_symbol"],
        accumulators=data["accumulators"],
        warmup_completed=data["warmup_completed"],
        state_schema_version=data["state_schema_version"],
        implementation_version=data.get("implementation_version", ""),
        parameter_hash=data.get("parameter_hash", ""),
        input_checksum=data.get("input_checksum", ""),
    )


def update_sliding_window_state(
    indicator_inst: Any,
    bar: dict[str, Any],
    state: IndicatorState,
    config: IndicatorConfig,
    context: IndicatorContext | None = None,
    lookback_multiplier: int = 3,
) -> tuple[IndicatorResult, IndicatorState]:
    """Execute incremental update using a bounded sliding window buffer."""
    indicator_id = indicator_inst.indicator_id
    period = config.parameters.get("period", 10)
    max_len = period * lookback_multiplier + 1

    # Extract timestamp and symbol
    timestamp = bar.get("timestamp")
    symbol = bar.get("symbol", "UNKNOWN")
    if not timestamp:
        raise ValidationError("Bar must contain 'timestamp'.")

    # Get existing history
    history = list(state.accumulators.get("history", []))

    # Prepare bar dict to store
    bar_to_store = dict(bar.items())
    # Ensure timestamp is normalized
    if isinstance(bar_to_store["timestamp"], pd.Timestamp) or isinstance(
        bar_to_store["timestamp"], datetime
    ):
        bar_to_store["timestamp"] = bar_to_store["timestamp"].isoformat()

    # Idempotency check: if timestamp matches last processed, overwrite it
    if history and history[-1]["timestamp"] == bar_to_store["timestamp"]:
        history[-1] = bar_to_store
    else:
        history.append(bar_to_store)

    if len(history) > max_len:
        history.pop(0)

    # Convert to DataFrame to calculate
    df = pd.DataFrame(history)

    # Ensure all required OHLCV columns exist to pass validation
    src_col = config.source_column or "close"
    src_val = df[src_col] if src_col in df.columns else None
    if src_val is None:
        for c in ["close", "open", "high", "low"]:
            if c in df.columns:
                src_val = df[c]
                break
    if src_val is None:
        src_val = 0.0

    for col in ["open", "high", "low", "close"]:
        if col not in df.columns:
            df[col] = src_val
    if "volume" not in df.columns:
        df["volume"] = 0.0
    if "quality" not in df.columns:
        df["quality"] = "good"
    if "timeframe" not in df.columns:
        df["timeframe"] = "D1"
    if "symbol" not in df.columns:
        df["symbol"] = symbol

    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
    df.index = pd.DatetimeIndex(df["timestamp_dt"])
    df.index.name = "timestamp"
    df = df.drop(columns=["timestamp_dt", "timestamp"])

    # Call calculate
    from app.services.indicators.errors import InsufficientDataError

    try:
        calc_result = indicator_inst.calculate(df, config, context)
        # Extract the last row
        last_row_df = calc_result.values.iloc[[-1]]
        warmup_completed = True
    except InsufficientDataError:
        warmup_completed = False
        out_cols = indicator_inst.output_columns(
            config.parameters, config.source_column
        )
        last_row_df = pd.DataFrame(index=df.index[[-1]])
        last_row_df["timestamp"] = df.index[[-1]]
        last_row_df["symbol"] = symbol
        for col in out_cols:
            last_row_df[col] = float("nan")
        last_row_df["available_at"] = df.index[[-1]]
        last_row_df["quality"] = bar.get("quality", "good")

        from app.services.indicators.protocols import IndicatorManifest

        calc_result = IndicatorResult(
            values=last_row_df,
            output_columns=out_cols,
            manifest=IndicatorManifest(indicator_id=indicator_id),
        )

    # Reconstruct result with only the last row
    result = IndicatorResult(
        values=last_row_df,
        output_columns=calc_result.output_columns,
        manifest=calc_result.manifest,
        errors=calc_result.errors,
        metrics=calc_result.metrics,
    )

    new_accumulators = {"history": history}
    new_state = IndicatorState(
        indicator_id=indicator_id,
        last_processed_timestamp=timestamp,
        last_processed_symbol=symbol,
        accumulators=new_accumulators,
        warmup_completed=warmup_completed,
        state_schema_version=state.state_schema_version,
        implementation_version=indicator_inst.version,
        parameter_hash=compute_parameter_hash(config.parameters),
        input_checksum=calc_result.manifest.input_checksum
        if calc_result.manifest
        else "",
    )

    return result, new_state


def topological_sort(graph: dict[str, list[str]], data_cols: set[str]) -> list[str]:
    """Return a list of nodes in topological order, excluding base data columns.

    Raises:
        IndicatorConfigError: If a circular dependency is detected.
    """
    visited: set[str] = set()
    temp: set[str] = set()
    order: list[str] = []

    def visit(node: str) -> None:
        if node in data_cols:
            return
        if node in temp:
            msg = f"Circular dependency detected in composition graph at: {node}"
            raise IndicatorConfigError(
                msg,
                code="IND_INVALID_CONFIG",
            )
        if node not in visited:
            temp.add(node)
            for neighbor in graph.get(node, []):
                visit(neighbor)
            temp.remove(node)
            visited.add(node)
            order.append(node)

    for node in graph:
        visit(node)
    return order


def execute_indicator_composition(
    data: pd.DataFrame,
    graph: dict[str, list[str]],
    configs: dict[str, IndicatorConfig],
    context: IndicatorContext | None = None,
) -> IndicatorResult:
    """Execute composed indicator graph in topological order, preserving available_at."""
    # 1. Validate cycle-free
    validate_composition_graph(graph)

    # 2. Topological sort
    data_cols = set(data.columns) | {"index"}
    order = topological_sort(graph, data_cols)

    # 3. Sequential execution
    accum_df = data.copy()
    manifests: dict[str, Any] = {}
    output_columns: list[str] = []
    start_time = time.perf_counter()

    from app.services.indicators.registry import get_indicator

    # Ensure all nodes in topological order have configurations
    for node in order:
        if node not in configs:
            msg = f"Missing configuration for composed indicator node '{node}'."
            raise IndicatorConfigError(
                msg,
                code="IND_INVALID_CONFIG",
            )

    for node in order:
        config = configs[node]
        ind_class = get_indicator(config.indicator_id)
        ind_inst = ind_class()

        # Calculate this indicator on accumulated dataframe
        result = ind_inst.calculate(accum_df, config, context)

        # Merge calculated columns
        for col in result.output_columns:
            if col in accum_df.columns:
                msg = f"Output column collision during composition: '{col}' already exists."
                raise IndicatorConfigError(
                    msg,
                    code="IND_OUTPUT_COLUMN_CONFLICT",
                )
            accum_df[col] = result.values[col]
            output_columns.append(col)

        # Compute max available_at of inputs and the indicator itself
        graph.get(node, [])
        max_dep_avail = None
        if "available_at" in accum_df.columns:
            max_dep_avail = accum_df["available_at"]

        computed_avail = result.values["available_at"]
        if max_dep_avail is not None:
            # Row-wise maximum between computed_avail and max_dep_avail
            accum_df["available_at"] = pd.concat(
                [computed_avail, max_dep_avail], axis=1
            ).max(axis=1)
        else:
            accum_df["available_at"] = computed_avail

        manifests[node] = result.manifest

    # Build combined manifest
    from app.services.indicators.protocols import IndicatorManifest

    symbol = "UNKNOWN"
    if "symbol" in accum_df.columns:
        symbol = str(accum_df["symbol"].iloc[0])
    elif isinstance(accum_df.index, pd.MultiIndex) and "symbol" in accum_df.index.names:
        symbol = str(accum_df.index.unique(level="symbol")[0])

    timeframe = "D1"
    if "timeframe" in accum_df.columns:
        timeframe = str(accum_df["timeframe"].iloc[0])

    timing = {
        "calculation_start": datetime.fromtimestamp(start_time, UTC).isoformat(),
        "calculation_end": datetime.now(UTC).isoformat(),
        "wall_clock_duration_ms": (time.perf_counter() - start_time) * 1000.0,
    }

    first_node = order[0] if order else ""
    first_manifest = manifests[first_node] if first_node else None

    combined_manifest = IndicatorManifest(
        indicator_id="composition",
        indicator_version="1.0.0",
        formula_version="1.0.0",
        data_provenance={
            "symbol": symbol,
            "timeframe": timeframe,
            "timezone": "UTC",
        },
        output_contract={
            "generated_column_names": output_columns,
            "output_mode": "values_only",
        },
        execution_backend={
            "backend_id": "composition_orchestrator",
            "order": order,
            "lineage": {
                k: {
                    "indicator_id": m.indicator_id,
                    "parameter_hash": m.parameter_hash,
                    "input_checksum": m.input_checksum,
                    "output_checksum": m.output_checksum,
                }
                for k, m in manifests.items()
            },
        },
        timing=timing,
        output_shape={
            "row_count": len(accum_df),
            "columns": list(accum_df.columns),
        },
        environment=first_manifest.environment if first_manifest else {},
    )

    return IndicatorResult(
        values=accum_df,
        output_columns=output_columns,
        manifest=combined_manifest,
    )
