"""Data transformation, aggregation, synthetic generation, and labeling utilities.

Implements resampling, tick-to-bar aggregation, lookahead-free alignment,
Geometric Brownian Motion (GBM) synthetic generators, and deterministic data labeling.
"""

import math
from datetime import timedelta
from typing import Any

import numpy as np
import pandas as pd

from app.services.data.validation import validate_timeframe
from app.utils.errors import ValidationError
from app.utils.logger import logger


def _clean_numpy_types(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert numpy integers and floats in records to native Python types."""
    for row in records:
        for k, v in row.items():
            if isinstance(v, np.integer):
                row[k] = int(v)
            elif isinstance(v, np.floating):
                row[k] = float(v)
    return records


def timeframe_to_pandas_freq(tf: str) -> str:
    """Convert a timeframe string into a pandas frequency string.

    Args:
        tf: Timeframe identifier (e.g., 'M5', 'H1').

    Returns:
        str: Pandas-compatible frequency string.
    """
    upper_tf = tf.upper()
    if upper_tf.startswith("MN"):
        val = int(upper_tf[2:])
        return f"{val}ME"  # Month end

    unit = upper_tf[0]
    try:
        val = int(upper_tf[1:])
    except ValueError as e:
        msg = f"Invalid timeframe value format: {tf}"
        raise ValidationError(msg) from e

    if unit == "M":
        return f"{val}min"
    if unit == "H":
        return f"{val}h"
    if unit == "D":
        return f"{val}D"
    if unit == "W":
        return f"{val}W"
    msg = f"Invalid timeframe unit: {tf}"
    raise ValidationError(msg)


def timeframe_to_minutes(tf: str) -> int:
    """Convert a timeframe string into minutes.

    Args:
        tf: Timeframe identifier (e.g., 'M5', 'H1').

    Returns:
        int: Duration in minutes.
    """
    upper_tf = tf.upper()
    if upper_tf.startswith("MN"):
        val = int(upper_tf[2:])
        return val * 43200  # Approximating a month as 30 days

    unit = upper_tf[0]
    try:
        val = int(upper_tf[1:])
    except ValueError as e:
        msg = f"Invalid timeframe value format: {tf}"
        raise ValidationError(msg) from e

    if unit == "M":
        return val
    if unit == "H":
        return val * 60
    if unit == "D":
        return val * 1440
    if unit == "W":
        return val * 10080
    msg = f"Invalid timeframe unit: {tf}"
    raise ValidationError(msg)


def resample_ohlcv(  # noqa: C901
    records: list[dict[str, Any]],
    target_timeframe: str,
    *,
    spread_policy: str = "average",
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Resample normalized OHLCV records into higher timeframes.

    Args:
        records: List of normalized OHLCV dictionary records.
        target_timeframe: Timeframe name to resample to (e.g. 'M15').
        spread_policy: Metric to aggregate spread ('average', 'max', 'last').
        request_id: Optional tracking identifier.

    Returns:
        list[dict[str, Any]]: Resampled OHLCV records list.

    Raises:
        ValidationError: If target timeframe is invalid or lower than source.
    """
    logger.info(
        f"Resampling {len(records)} records to {target_timeframe} using "
        f"spread_policy={spread_policy}",
        extra={"request_id": request_id},
    )

    if not records:
        return []

    validate_timeframe(target_timeframe)

    # Validate source timeframe from records
    source_tf = records[0].get("timeframe")
    if not source_tf:
        raise ValidationError("Source records missing timeframe field.")

    validate_timeframe(source_tf)

    src_mins = timeframe_to_minutes(source_tf)
    tgt_mins = timeframe_to_minutes(target_timeframe)

    if tgt_mins < src_mins:
        msg = (
            f"Cannot resample to a lower timeframe: "
            f"source={source_tf} ({src_mins}m), target={target_timeframe} ({tgt_mins}m)"
        )
        raise ValidationError(msg)

    # Convert to DataFrame
    df = pd.DataFrame(records)
    if "symbol" in df.columns and (df["symbol"] != df["symbol"].iloc[0]).any():
        raise ValidationError("Cannot resample records containing multiple symbols.")

    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp_dt")
    df = df.sort_index()

    # Define aggregations based on available columns
    standard_cols = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
        "tick_volume": "sum",
        "real_volume": "sum",
        "symbol": "first",
        "source": "first",
    }
    agg_dict = {c: standard_cols[c] for c in standard_cols if c in df.columns}

    if "spread" in df.columns:
        if spread_policy == "max":
            agg_dict["spread"] = "max"
        elif spread_policy == "last":
            agg_dict["spread"] = "last"
        else:
            agg_dict["spread"] = "mean"

    pandas_freq = timeframe_to_pandas_freq(target_timeframe)

    # Perform resampling
    resampled_df = df.resample(pandas_freq, label="left", closed="left").agg(agg_dict)

    # Drop rows that have all NaN prices
    price_cols = [
        c for c in ["open", "high", "low", "close"] if c in resampled_df.columns
    ]
    resampled_df = resampled_df.dropna(subset=price_cols, how="all")

    # Reset index and formatting
    resampled_df = resampled_df.reset_index()
    resampled_df["timestamp"] = resampled_df["timestamp_dt"].dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    resampled_df = resampled_df.drop(columns=["timestamp_dt"])
    resampled_df["timeframe"] = target_timeframe

    # Fill NaNs with standard defaults
    if "volume" in resampled_df.columns:
        resampled_df["volume"] = resampled_df["volume"].fillna(0.0)
    if "tick_volume" in resampled_df.columns:
        resampled_df["tick_volume"] = resampled_df["tick_volume"].fillna(0.0)
    if "real_volume" in resampled_df.columns:
        resampled_df["real_volume"] = resampled_df["real_volume"].fillna(0.0)
    if "spread" in resampled_df.columns:
        resampled_df["spread"] = resampled_df["spread"].fillna(0.0)

    # Convert numeric outputs to Python native types (float or int)
    result = resampled_df.to_dict(orient="records")
    return _clean_numpy_types(result)


def align_multitimeframe_data(
    datasets: dict[str, list[dict[str, Any]]],
    target_timestamps: list[str],
    *,
    allow_lookahead: bool = False,
    alignment_method: str = "last_known_closed_bar",
    request_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Align multiple timeframe datasets to target timestamps without lookahead.

    Args:
        datasets: Dict mapping timeframe string to list of bar records.
        target_timestamps: List of target UTC timestamp strings to align to.
        allow_lookahead: If True, lookahead boundary check is bypassed.
        alignment_method: Alignment rule identifier ('last_known_closed_bar').
        request_id: Optional tracking identifier.

    Returns:
        dict[str, list[dict[str, Any]]]: Mapped aligned records per timeframe.
    """
    logger.info(
        "Aligning datasets with %d timeframes to %d targets "
        "(allow_lookahead=%s, method=%s)",
        len(datasets),
        len(target_timestamps),
        allow_lookahead,
        alignment_method,
        extra={"request_id": request_id},
    )

    if not target_timestamps:
        return {tf: [] for tf in datasets}

    # Prepare targets DataFrame
    target_df = pd.DataFrame({"timestamp": target_timestamps})
    target_df["timestamp_dt"] = pd.to_datetime(target_df["timestamp"])
    target_df = target_df.sort_values("timestamp_dt")

    aligned_results: dict[str, list[dict[str, Any]]] = {}

    for tf, records in datasets.items():
        if not records:
            aligned_results[tf] = []
            continue

        df_source = pd.DataFrame(records)
        df_source["timestamp_dt"] = pd.to_datetime(df_source["timestamp"])
        df_source = df_source.sort_values("timestamp_dt")

        interval_mins = timeframe_to_minutes(tf)

        if not allow_lookahead:
            # Shift the timestamp key by the bar duration to denote when it closes
            df_source["align_key"] = df_source["timestamp_dt"] + pd.to_timedelta(
                interval_mins, unit="m"
            )
        else:
            df_source["align_key"] = df_source["timestamp_dt"]

        # Run merge_asof
        merged = pd.merge_asof(
            target_df,
            df_source,
            left_on="timestamp_dt",
            right_on="align_key",
            direction="backward",
            suffixes=("", "_src"),
        )

        # Cleanup columns
        if "timestamp_dt" in merged.columns:
            merged = merged.drop(columns=["timestamp_dt"])
        if "align_key" in merged.columns:
            merged = merged.drop(columns=["align_key"])
        if "timestamp_src" in merged.columns:
            src_ts = pd.to_datetime(merged["timestamp_src"])
            merged["bar_open_timestamp"] = src_ts.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            merged = merged.drop(columns=["timestamp_src"])
        if "timestamp_dt_src" in merged.columns:
            merged = merged.drop(columns=["timestamp_dt_src"])

        # Convert NaNs to None for JSON serializability
        merged = merged.where(merged.notna(), None)

        records_list = merged.to_dict(orient="records")
        # Ensure numpy types are converted
        _clean_numpy_types(records_list)

        aligned_results[tf] = records_list

    return aligned_results


def aggregate_ticks_to_bars(  # noqa: C901, PLR0912
    ticks: list[dict[str, Any]],
    timeframe: str,
    *,
    repair: bool = False,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Aggregate tick records into OHLCV bars.

    Args:
        ticks: List of normalized tick records.
        timeframe: Bar timeframe to aggregate into.
        repair: If True, sort ticks by timestamp if unsorted.
        request_id: Optional tracking identifier.

    Returns:
        list[dict[str, Any]]: Aggregated OHLCV records.

    Raises:
        ValidationError: If ticks are not sorted (and repair is False).
    """
    logger.info(
        f"Aggregating {len(ticks)} ticks to timeframe {timeframe} (repair={repair})",
        extra={"request_id": request_id},
    )

    if not ticks:
        return []

    validate_timeframe(timeframe)

    df = pd.DataFrame(ticks)
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])

    # Verify chronological sorting
    if not df["timestamp_dt"].is_monotonic_increasing:
        if not repair:
            msg = "Ticks are not sorted chronologically."
            raise ValidationError(msg)
        df = df.sort_values("timestamp_dt")

    # Resolve price column to use
    if "last" in df.columns and df["last"].notna().any():
        price_col = "last"
    elif "price" in df.columns and df["price"].notna().any():
        price_col = "price"
    elif "bid" in df.columns and df["bid"].notna().any():
        price_col = "bid"
    else:
        msg = "No valid price field (last, price, bid) found in ticks."
        raise ValidationError(msg)

    # Floor timestamps to timeframe interval
    freq = timeframe_to_pandas_freq(timeframe)
    df["bar_time"] = df["timestamp_dt"].dt.floor(freq)

    agg_dict: dict[str, list[str] | str] = {
        price_col: ["first", "max", "min", "last"],
    }

    if "volume" in df.columns:
        agg_dict["volume"] = "sum"

    df["tick_count"] = 1
    agg_dict["tick_count"] = "sum"

    if "ask" in df.columns and "bid" in df.columns:
        df["spread_val"] = df["ask"] - df["bid"]
        agg_dict["spread_val"] = "mean"

    # Perform groupby aggregation
    grouped = df.groupby("bar_time").agg(agg_dict)

    # Flatten multi-index columns
    grouped.columns = ["_".join(col).strip() for col in list(grouped.columns)]
    grouped = grouped.reset_index()

    # Map to standardized bar names
    rename_map = {
        f"{price_col}_first": "open",
        f"{price_col}_max": "high",
        f"{price_col}_min": "low",
        f"{price_col}_last": "close",
        "volume_sum": "volume",
        "tick_count_sum": "tick_volume",
        "spread_val_mean": "spread",
    }
    grouped = grouped.rename(columns=rename_map)

    # Add timeframe and symbol if constant in input
    if "symbol" in df.columns:
        grouped["symbol"] = df["symbol"].iloc[0]
    if "source" in df.columns:
        grouped["source"] = df["source"].iloc[0]
    else:
        grouped["source"] = "tick_aggregation"

    grouped["timeframe"] = timeframe
    grouped["timestamp"] = grouped["bar_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Drop temp columns
    drop_cols = [
        c
        for c in ["bar_time", "price_first", "price_max", "price_min", "price_last"]
        if c in grouped.columns
    ]
    grouped = grouped.drop(columns=drop_cols)

    # Fallback missing columns
    if "volume" not in grouped.columns:
        grouped["volume"] = 0.0
    if "spread" not in grouped.columns:
        grouped["spread"] = 0.0

    result = grouped.to_dict(orient="records")
    # Clean numpy types
    return _clean_numpy_types(result)


def generate_synthetic_ticks(
    symbol: str,
    start_time: str,
    num_ticks: int,
    start_price: float,
    average_spread: float,
    volatility: float,
    *,
    volume_behavior: str = "random",
    seed: int | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Generate deterministic synthetic tick data using random walks.

    Args:
        symbol: Market symbol name.
        start_time: Start date string (UTC).
        num_ticks: Total tick count to generate.
        start_price: Starting mid-price.
        average_spread: Average spread to keep around the price.
        volatility: Price volatility factor (step size relative deviation).
        volume_behavior: Tick volume simulation rules ('random', 'constant').
        seed: Optional deterministic seed value.
        request_id: Optional tracking identifier.

    Returns:
        list[dict[str, Any]]: List of generated tick records.
    """
    logger.info(
        f"Generating {num_ticks} synthetic ticks for {symbol} starting at "
        f"{start_price} (volatility={volatility}, seed={seed})",
        extra={"request_id": request_id},
    )

    if num_ticks <= 0:
        return []

    if start_price <= 0:
        raise ValidationError("start_price must be positive.")
    if average_spread < 0:
        raise ValidationError("average_spread cannot be negative.")
    if volatility < 0:
        raise ValidationError("volatility cannot be negative.")

    rng = np.random.default_rng(seed)

    start_dt = pd.to_datetime(start_time)
    current_time = start_dt
    current_price = float(start_price)

    ticks = []

    # Pre-generate steps
    returns = rng.normal(0, volatility, num_ticks)
    time_deltas = rng.integers(1, 5, num_ticks)  # 1 to 4 seconds increment

    if volume_behavior == "random":
        volumes = rng.uniform(1.0, 100.0, num_ticks)
    else:
        volumes = np.ones(num_ticks) * 10.0

    for i in range(num_ticks):
        current_price = current_price * math.exp(returns[i])
        current_time = current_time + timedelta(seconds=int(time_deltas[i]))

        spread = average_spread
        bid = current_price - spread / 2.0
        ask = current_price + spread / 2.0

        ticks.append(
            {
                "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "symbol": symbol,
                "bid": float(bid),
                "ask": float(ask),
                "last": float(current_price),
                "volume": float(volumes[i]),
                "spread": float(spread),
                "source": "synthetic",
            }
        )

    return ticks


def generate_synthetic_bars(
    symbol: str,
    timeframe: str,
    start_time: str,
    num_bars: int,
    start_price: float,
    drift: float,
    volatility: float,
    *,
    spread_behavior: str = "constant",
    volume_behavior: str = "random",
    method: str = "gbm",
    seed: int | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Generate deterministic synthetic bar data (OHLCV) using GBM.

    Args:
        symbol: Market symbol name.
        timeframe: Bar timeframe (e.g. 'M5').
        start_time: Start date string (UTC).
        num_bars: Total bars count to generate.
        start_price: Starting open price.
        drift: Trend drift factor.
        volatility: Volatility factor.
        spread_behavior: Spread simulation rules ('constant', 'random').
        volume_behavior: Volume rules ('random', 'constant').
        method: Core generator method ('gbm').
        seed: Optional deterministic seed value.
        request_id: Optional tracking identifier.

    Returns:
        list[dict[str, Any]]: List of generated OHLCV bar records.
    """
    logger.info(
        f"Generating {num_bars} synthetic bars for {symbol} using {method} "
        f"starting at {start_price} (volatility={volatility}, seed={seed})",
        extra={"request_id": request_id},
    )

    if num_bars <= 0:
        return []

    if start_price <= 0:
        raise ValidationError("start_price must be positive.")
    if volatility < 0:
        raise ValidationError("volatility cannot be negative.")

    validate_timeframe(timeframe)

    if method.lower() != "gbm":
        msg = f"Unsupported synthetic bar generation method: {method}"
        raise ValidationError(msg)

    rng = np.random.default_rng(seed)

    start_dt = pd.to_datetime(start_time)
    interval_mins = timeframe_to_minutes(timeframe)

    current_price = float(start_price)
    bars = []

    # Sim parameters
    dt = 1.0  # per step

    # Pre-generate GBM paths
    # S_t = S_{t-1} * exp((drift - 0.5 * vol^2) * dt + vol * sqrt(dt) * Z)
    gbm_coef = (drift - 0.5 * volatility**2) * dt
    random_normals = rng.normal(0, 1, num_bars)

    if volume_behavior == "random":
        volumes = rng.uniform(10.0, 1000.0, num_bars)
    else:
        volumes = np.ones(num_bars) * 100.0

    if spread_behavior == "random":
        spreads = rng.uniform(0.1, 5.0, num_bars)
    else:
        spreads = np.ones(num_bars) * 2.0

    for i in range(num_bars):
        open_price = current_price

        # Simulate Close price
        close_price = open_price * math.exp(gbm_coef + volatility * random_normals[i])

        # Simulate realistic High and Low bounds
        # Draw separate small steps to simulate intra-bar noise
        noise_high = abs(rng.normal(0, volatility * 0.15)) * open_price
        noise_low = abs(rng.normal(0, volatility * 0.15)) * open_price

        high_price = max(open_price, close_price) + noise_high
        low_price = min(open_price, close_price) - noise_low

        bar_time = start_dt + timedelta(minutes=int(i * interval_mins))

        bars.append(
            {
                "timestamp": bar_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "symbol": symbol,
                "open": float(open_price),
                "high": float(high_price),
                "low": float(low_price),
                "close": float(close_price),
                "volume": float(volumes[i]),
                "tick_volume": float(volumes[i] / 2.0),
                "real_volume": float(volumes[i]),
                "spread": float(spreads[i]),
                "timeframe": timeframe,
                "source": "synthetic",
            }
        )

        # Set close as starting point for next bar
        current_price = close_price

    return bars


def label_market_data(
    records: list[dict[str, Any]],
    *,
    horizon: int,
    threshold: float,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Generate deterministic historical labels without claiming predictive value.

    Labels represent:
      - 1: Upward trend (close rises by >= threshold% within horizon bars).
      - -1: Downward trend (close falls by >= threshold% within horizon bars).
      - 0: Neutral (no threshold boundary touched within horizon).

    Args:
        records: List of OHLCV bar records.
        horizon: Configurable lookahead horizon window (number of bars).
        threshold: Trend trigger threshold percentage (e.g. 0.01 for 1%).
        request_id: Optional tracking identifier.

    Returns:
        list[dict[str, Any]]: Original records enriched with a 'label' field.

    Raises:
        ValidationError: If horizon or threshold inputs are invalid.
    """
    logger.info(
        "Labeling %d records with horizon=%d, threshold=%f",
        len(records),
        horizon,
        threshold,
        extra={"request_id": request_id},
    )

    if horizon <= 0:
        raise ValidationError("horizon must be a positive integer.")
    if threshold < 0:
        raise ValidationError("threshold cannot be negative.")

    if not records:
        return []

    # Validate that close price is present in records
    if "close" not in records[0]:
        raise ValidationError("Records missing mandatory close price column.")

    prices = [float(r["close"]) for r in records]
    n = len(prices)

    labeled_records = []

    for i in range(n):
        label = 0
        end_idx = min(i + horizon + 1, n)

        # Find the first price that crosses the threshold
        for j in range(i + 1, end_idx):
            ret = (prices[j] - prices[i]) / prices[i]
            if ret >= threshold:
                label = 1
                break
            if ret <= -threshold:
                label = -1
                break

        # Shallow copy to preserve original record fields and append label
        new_rec = dict(records[i])
        new_rec["label"] = label
        new_rec["label_metadata"] = {
            "method": "horizon_threshold",
            "horizon": horizon,
            "threshold": threshold,
            "claims_predictive_value": False,
        }
        labeled_records.append(new_rec)

    return labeled_records
