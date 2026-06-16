# ruff: noqa: E501, BLE001, E402
"""Unified usage example for the Market Data Service functions."""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

# Add project root to sys.path to allow execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.data import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    clear_data_cache,
    create_data_update_job,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    get_data,
    get_data_availability,
    get_data_update_job_status,
    get_market_hours,
    get_symbol_metadata,
    get_trading_sessions,
    label_market_data,
    list_symbols,
    resample_ohlcv,
    start_data_update_job,
    stop_data_update_job,
)
from app.services.data.storage import db_helper
from app.utils.logger import logger
from app.utils.normalization import normalize_timestamp

_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


def print_tail_table(records: list[dict[str, Any]]) -> None:
    """Print the last 5 records formatted as a clean Pandas DataFrame table."""
    if not records:
        print("  [No records retrieved]")
        return
    df = pd.DataFrame(records[-5:])
    cols = [
        "timestamp",
        "symbol",
        "timeframe",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "spread",
    ]
    cols_to_print = [c for c in cols if c in df.columns]
    if not cols_to_print:
        cols_to_print = df.columns.tolist()
    print(df[cols_to_print].to_string(index=False))


def example_01_metadata_and_discovery() -> None:
    """Demonstrate metadata and discovery queries including asset class filtering."""
    print("\n" + "=" * 100)
    print("--- 1. Symbol Discovery & Metadata ---")
    print("=" * 100)

    try:
        # 1. Discover symbols from the MT5 adapter
        symbols = list_symbols(source="mt5")
        print(f"Discovered MT5 symbols: {symbols}")

        # Search/Filter by classes (e.g., forex, indices, metals)
        print("\nSearching symbols by asset class:")
        for target_class in ["forex", "indices", "metals"]:
            matched = []
            for sym in symbols:
                meta = get_symbol_metadata(symbol=sym, source="mt5")
                if meta.get("asset_class", "").lower() == target_class:
                    matched.append(sym)
            print(f"  Asset class '{target_class}': {matched}")

        # 2. Get metadata for EURUSD
        metadata = get_symbol_metadata(symbol="EURUSD", source="mt5")
        print("\nMetadata for EURUSD:")
        for k, v in metadata.items():
            print(f"  {k:18}: {v}")

        # 3. Check data availability bounds
        availability = get_data_availability(
            symbol="EURUSD", timeframe="H1", source="mt5"
        )
        print("\nAvailability for EURUSD OHLCV:")
        for k, v in availability.items():
            print(f"  {k:18}: {v}")

    except Exception as e:
        print(f"Error in discovery/metadata: {e}")


def example_02a_data_retrieval_mt5() -> None:
    """Demonstrate MT5 historical data retrieval (fails closed if unavailable)."""
    print("\n" + "=" * 100)
    print("--- 2a. MT5 Historical Data Retrieval ---")
    print("=" * 100)
    try:
        print("Querying MT5 for EURUSD H1 bars...")
        records = get_data(
            symbol="EURUSD",
            timeframe="H1",
            data_kind="ohlcv",
            source="mt5",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-02T00:00:00Z",
        )
        print(f"Fetched {len(records)} bars from MT5.")
        if records:
            print("Tail (last 5 rows):")
            print_tail_table(records)
    except Exception as e:
        print(f"MT5 retrieval failed closed (expected in staging): {e}")


def example_02b_data_retrieval_ctrader() -> None:
    """Demonstrate cTrader historical data retrieval (fails closed if unavailable)."""
    print("\n" + "=" * 100)
    print("--- 2b. cTrader Historical Data Retrieval ---")
    print("=" * 100)
    try:
        print("Querying cTrader for EURUSD H1 bars...")
        records = get_data(
            symbol="EURUSD",
            timeframe="H1",
            data_kind="ohlcv",
            source="ctrader",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-02T00:00:00Z",
        )
        print(f"Fetched {len(records)} bars from cTrader.")
        if records:
            print("Tail (last 5 rows):")
            print_tail_table(records)
    except Exception as e:
        print(f"cTrader retrieval failed closed (expected in staging): {e}")


def example_02c_data_retrieval_dukascopy() -> None:
    """Demonstrate Dukascopy historical data retrieval (fails closed if unavailable)."""
    print("\n" + "=" * 100)
    print("--- 2c. Dukascopy Historical Data Retrieval ---")
    print("=" * 100)
    try:
        print("Querying Dukascopy for EURUSD H1 bars...")
        records = get_data(
            symbol="EURUSD",
            timeframe="H1",
            data_kind="ohlcv",
            source="dukascopy",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-02T00:00:00Z",
        )
        print(f"Fetched {len(records)} bars from Dukascopy.")
        if records:
            print("Tail (last 5 rows):")
            print_tail_table(records)
    except Exception as e:
        print(f"Dukascopy retrieval failed closed (expected in staging): {e}")


def example_02d_data_retrieval_yahoo() -> None:
    """Demonstrate Yahoo Finance historical data retrieval (fails closed if unavailable)."""
    print("\n" + "=" * 100)
    print("--- 2d. Yahoo Finance Historical Data Retrieval ---")
    print("=" * 100)
    try:
        print("Querying Yahoo Finance for AAPL H1 bars...")
        records = get_data(
            symbol="AAPL",
            timeframe="H1",
            data_kind="ohlcv",
            source="yahoo",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-02T00:00:00Z",
        )
        print(f"Fetched {len(records)} bars from Yahoo Finance.")
        if records:
            print("Tail (last 5 rows):")
            print_tail_table(records)
    except Exception as e:
        print(f"Yahoo Finance retrieval failed closed (expected in staging): {e}")


def example_02e_data_retrieval_binance() -> None:
    """Demonstrate Binance historical data retrieval (fails closed for discovery-only)."""
    print("\n" + "=" * 100)
    print("--- 2e. Binance Historical Data Retrieval ---")
    print("=" * 100)
    try:
        print("Querying Binance for BTCUSDT H1 bars...")
        records = get_data(
            symbol="BTCUSDT",
            timeframe="H1",
            data_kind="ohlcv",
            source="binance",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-02T00:00:00Z",
        )
        print(f"Fetched {len(records)} bars from Binance.")
        if records:
            print("Tail (last 5 rows):")
            print_tail_table(records)
    except Exception as e:
        print(
            f"Binance retrieval failed closed (expected in staging/discovery-only): {e}"
        )


def example_02f_data_retrieval_csv() -> None:
    """Demonstrate CSV file historical data retrieval."""
    print("\n" + "=" * 100)
    print("--- 2f. CSV Historical Data Retrieval ---")
    print("=" * 100)
    try:
        print("Querying CSV file for EURUSD H1 bars...")
        records = get_data(
            symbol="EURUSD",
            timeframe="H1",
            data_kind="ohlcv",
            source="csv",
            start_time="2025-01-02T00:00:00Z",
            end_time="2025-01-03T00:00:00Z",
        )
        print(f"Fetched {len(records)} bars from CSV adapter.")
        if records:
            print("Tail (last 5 rows):")
            print_tail_table(records)
    except Exception as e:
        print(f"CSV retrieval error: {e}")


def example_02g_data_retrieval_parquet() -> None:
    """Demonstrate Parquet file historical data retrieval."""
    print("\n" + "=" * 100)
    print("--- 2g. Parquet Historical Data Retrieval ---")
    print("=" * 100)
    try:
        print("Querying Parquet file for EURUSD H1 bars...")
        records = get_data(
            symbol="EURUSD",
            timeframe="H1",
            data_kind="ohlcv",
            source="parquet",
            start_time="2025-01-02T00:00:00Z",
            end_time="2025-01-03T00:00:00Z",
        )
        print(f"Fetched {len(records)} bars from Parquet adapter.")
        if records:
            print("Tail (last 5 rows):")
            print_tail_table(records)
    except Exception as e:
        print(f"Parquet retrieval error: {e}")


def example_02h_data_retrieval_caching() -> None:
    """Demonstrate historical data query caching utilization."""
    print("\n" + "=" * 100)
    print("--- 2h. Caching Utilization ---")
    print("=" * 100)
    try:
        symbol = "EURUSD"
        start_str = "2026-06-01T00:00:00Z"
        end_str = "2026-06-02T00:00:00Z"

        print("Query 1: Fetching EURUSD H1 bars from synthetic source (Cache Miss)...")
        t0 = time.perf_counter()
        records_1 = get_data(
            symbol=symbol,
            timeframe="H1",
            data_kind="ohlcv",
            source="synthetic",
            start_time=start_str,
            end_time=end_str,
        )
        duration_1 = (time.perf_counter() - t0) * 1000
        print(f"Successfully fetched {len(records_1)} bars in {duration_1:.2f} ms.")
        if records_1:
            print("Tail (last 5 rows, Miss):")
            print_tail_table(records_1)

        print("\nQuery 2: Re-fetching the same timeframe/range (Cache Hit)...")
        t1 = time.perf_counter()
        records_2 = get_data(
            symbol=symbol,
            timeframe="H1",
            data_kind="ohlcv",
            source="synthetic",
            start_time=start_str,
            end_time=end_str,
        )
        duration_2 = (time.perf_counter() - t1) * 1000
        print(f"Successfully fetched {len(records_2)} bars in {duration_2:.2f} ms.")
        if records_2:
            print("Tail (last 5 rows, Hit):")
            print_tail_table(records_2)

        speedup = duration_1 / duration_2 if duration_2 > 0 else 1.0
        print(f"Cache speedup: {speedup:.1f}x faster.")
    except Exception as e:
        print(f"Caching demonstration error: {e}")


def example_02i_data_retrieval_labeler() -> None:
    """Demonstrate labeling retrieved data."""
    print("\n" + "=" * 100)
    print("--- 2i. Data Labeler ---")
    print("=" * 100)
    try:
        print("Retrieving synthetic bars and applying triple-barrier labeling...")
        bars = get_data(
            symbol="EURUSD",
            timeframe="H1",
            data_kind="ohlcv",
            source="synthetic",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-02T00:00:00Z",
        )
        labeled = label_market_data(bars, horizon=3, threshold=0.001)
        print(f"Labeled {len(labeled)} bars.")
        if labeled:
            print("Tail (last 5 rows, Labeled):")
            print_tail_table(labeled)
    except Exception as e:
        print(f"Labeler retrieval error: {e}")


def example_03_timeframes_and_sessions() -> None:
    """Demonstrate timezone-aware session checks."""
    print("\n" + "=" * 100)
    print("--- 3. Timeframes & Market Hours ---")
    print("=" * 100)

    try:
        # 1. Fetch market hours for EURUSD
        hours = get_market_hours(symbol="EURUSD")
        print("Market hours:")
        for k, v in hours.items():
            print(f"  {k:15}: {v}")

        # 2. Fetch trading sessions windows
        start = normalize_timestamp("2026-06-15T08:00:00Z")
        end = normalize_timestamp("2026-06-15T18:00:00Z")
        sessions = get_trading_sessions(start_time=start, end_time=end)
        print(f"\nTrading sessions from {start.isoformat()} to {end.isoformat()}:")
        for i, s in enumerate(sessions[:5]):  # Show up to 5 sessions
            print(
                f"  {i + 1}. Session: {s.get('session_name')} | Start: {s.get('start')} | End: {s.get('end')}"
            )

    except Exception as e:
        print(f"Error in timeframe/session query: {e}")


def example_04_transformations() -> None:
    """Demonstrate tick aggregation, resampling, multi-timeframe merging, symbol concatenation, and alignment."""
    print("\n" + "=" * 100)
    print("--- 4. Data Transformations ---")
    print("=" * 100)

    try:
        # 1. Resample OHLCV
        # Generate 1-minute bars first
        one_min_bars = generate_synthetic_bars(
            symbol="EURUSD",
            timeframe="M1",
            start_time="2026-06-15T10:00:00Z",
            num_bars=30,
            start_price=1.1000,
            drift=0.0001,
            volatility=0.0002,
            seed=42,
        )
        print(f"Generated {len(one_min_bars)} M1 bars.")

        # Resample M1 to M5
        five_min_bars = resample_ohlcv(one_min_bars, target_timeframe="M5")
        print(f"Resampled to {len(five_min_bars)} M5 bars:")
        for bar in five_min_bars[:3]:
            print(
                f"  M5 Bar: {bar.get('timestamp')} | O: {bar.get('open'):.5f} | C: {bar.get('close'):.5f}"
            )

        # 2. Aggregate Ticks to Bars
        ticks = generate_synthetic_ticks(
            symbol="EURUSD",
            start_time="2026-06-15T12:00:00Z",
            num_ticks=100,
            start_price=1.1000,
            average_spread=0.0002,
            volatility=0.0001,
            seed=123,
        )
        print(f"\nGenerated {len(ticks)} synthetic ticks.")
        aggregated_bars = aggregate_ticks_to_bars(ticks, timeframe="M1")
        print(f"Aggregated ticks into {len(aggregated_bars)} M1 bars.")

        # 3. Lookahead-free Multi-timeframe Alignment & Timeframe Merging
        # Align M5 dataset to M1 timestamps (from M1 bar 6 onwards, i.e. 10:06 onwards)
        # Lookahead-free alignment shifts the M5 bar closed boundary to 5 minutes after open.
        print("\n--- Timeframe Merging & Multi-timeframe Alignment ---")
        m5_dataset = resample_ohlcv(one_min_bars, target_timeframe="M5")
        target_timestamps = [
            b["timestamp"] for b in one_min_bars[5:9]
        ]  # Timestamps 10:05 to 10:08

        aligned = align_multitimeframe_data(
            datasets={"M5": m5_dataset},
            target_timestamps=target_timestamps,
            allow_lookahead=False,  # Prevent lookahead bias
        )
        print("Aligned multi-timeframe datasets (M5 to M1 targets):")
        for i, target_ts in enumerate(target_timestamps):
            aligned_bar = aligned["M5"][i]
            print(f"  Target M1 Time: {target_ts}")
            print(
                f"    Aligned M5 Bar Open Time:  {aligned_bar.get('bar_open_timestamp')}"
            )
            print(f"    Aligned M5 Close Price:    {aligned_bar.get('close')}")

        # 4. Concatenate and Merge Symbols
        print("\n--- Concatenating and Merging Symbols ---")
        eurusd_bars = generate_synthetic_bars(
            symbol="EURUSD",
            timeframe="H1",
            start_time="2026-06-15T00:00:00Z",
            num_bars=5,
            start_price=1.1000,
            drift=0.0001,
            volatility=0.0002,
            seed=42,
        )
        gbpusd_bars = generate_synthetic_bars(
            symbol="GBPUSD",
            timeframe="H1",
            start_time="2026-06-15T00:00:00Z",
            num_bars=5,
            start_price=1.2500,
            drift=0.0001,
            volatility=0.0002,
            seed=43,
        )

        df_eur = pd.DataFrame(eurusd_bars)
        df_gbp = pd.DataFrame(gbpusd_bars)

        # Row-wise concatenation (Stacking symbols)
        stacked_df = pd.concat([df_eur, df_gbp], ignore_index=True)
        print(f"Row-wise concatenated symbols shape: {stacked_df.shape}")
        print("Stacked sample:")
        print(stacked_df[["timestamp", "symbol", "close"]].head(6))

        # Column-wise merging (Aligning symbols on timestamp)
        merged_symbols_df = df_eur[["timestamp", "close"]].merge(
            df_gbp[["timestamp", "close"]],
            on="timestamp",
            suffixes=("_EURUSD", "_GBPUSD"),
        )
        print(f"\nColumn-wise merged symbols shape: {merged_symbols_df.shape}")
        print("Merged sample:")
        print(merged_symbols_df.to_string(index=False))

    except Exception as e:
        print(f"Error during transformations: {e}")


def example_05_synthetic_generation() -> None:
    """Demonstrate synthetic walk generation and data labeling."""
    print("\n" + "=" * 100)
    print("--- 5. Synthetic Generation & Data Labeling ---")
    print("=" * 100)

    try:
        # 1. Generate synthetic walk bars (using standard H1 timeframe)
        bars = generate_synthetic_bars(
            symbol="GBPUSD",
            timeframe="H1",
            start_time="2026-06-15T00:00:00Z",
            num_bars=10,
            start_price=1.2500,
            drift=0.0001,
            volatility=0.001,
            seed=999,
        )
        print(f"Generated {len(bars)} synthetic GBPUSD bars.")

        # 2. Enrich with labels
        labeled = label_market_data(bars, horizon=3, threshold=0.001)
        print("\nLabeled records sample:")
        for r in labeled[:4]:
            print(
                f"  Time: {r.get('timestamp')} | Close: {r.get('close'):.5f} | Label: {r.get('label'):2} | Method: {r.get('label_metadata', {}).get('method')}"
            )

    except Exception as e:
        print(f"Error during synthetic walk: {e}")


def example_06_scheduling_jobs() -> None:
    """Demonstrate background data-scheduler sync job registration."""
    print("\n" + "=" * 100)
    print("--- 6. Scheduler Sync Job Registration ---")
    print("=" * 100)

    job_name = "usage_sync_eurusd"
    try:
        # Pre-clean the job if it exists in the database
        with db_helper.get_connection() as conn:
            conn.execute("DELETE FROM data_jobs WHERE name = ?;", (job_name,))

        # 1. Create a recurrent update job configuration
        job = create_data_update_job(
            name=job_name,
            source="synthetic",
            symbols=["EURUSD"],
            timeframes=["M1"],
            data_kind="ohlcv",
            storage_format="csv",
            storage_path="./data",
            schedule="*/5 * * * *",
        )
        print(f"Successfully registered update job: {job.get('name')}")
        print(f"  Job ID:     {job.get('id')}")
        print(f"  Source:     {job.get('source')}")
        print(f"  Schedule:   {job.get('schedule')}")

        # 2. Query job status
        status = get_data_update_job_status(name=job_name)
        print("\nJob status query:")
        print(f"  State:      {status.get('state')}")
        print(f"  Enabled:    {status.get('enabled')}")

        # 3. Start & Stop update job recurrent worker task
        print("\nStarting update job worker task...")
        start_data_update_job(name=job_name)
        print("Stopping update job worker task...")
        stop_data_update_job(name=job_name)

        # Yield execution to event loop to allow cancellation to propagate cleanly
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(asyncio.sleep(0.1))
            _BACKGROUND_TASKS.add(task)
            task.add_done_callback(_BACKGROUND_TASKS.discard)
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop_policy().get_event_loop()
                if not loop.is_closed():
                    loop.run_until_complete(asyncio.sleep(0.1))
            except Exception as e:
                logger.debug(f"Event loop yield ignored: {e}")

    except Exception as e:
        print(f"Error in scheduler workflow: {e}")


def example_07_cleanup() -> None:
    """Clear cache and tidy up SQLite records."""
    print("\n" + "=" * 100)
    print("--- 7. Caching Cleanup ---")
    print("=" * 100)

    try:
        # Tidy up database jobs
        with db_helper.get_connection() as conn:
            conn.execute(
                "DELETE FROM data_jobs WHERE name = ?;", ("usage_sync_eurusd",)
            )

        # Clear the cache namespace
        res = clear_data_cache(namespace="data_cache", dry_run=False)
        print(
            f"Successfully cleared data cache. Removed entries: {res.get('cleared_count', 0)}"
        )
    except Exception as e:
        print(f"Error clearing cache: {e}")


if __name__ == "__main__":
    example_01_metadata_and_discovery()
    example_02a_data_retrieval_mt5()
    example_02b_data_retrieval_ctrader()
    example_02c_data_retrieval_dukascopy()
    example_02d_data_retrieval_yahoo()
    example_02e_data_retrieval_binance()
    example_02f_data_retrieval_csv()
    example_02g_data_retrieval_parquet()
    example_02h_data_retrieval_caching()
    example_02i_data_retrieval_labeler()
    example_03_timeframes_and_sessions()
    example_04_transformations()
    example_05_synthetic_generation()
    example_06_scheduling_jobs()
    example_07_cleanup()
