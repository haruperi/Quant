"""Unit tests for clean public service API exports in app/services/data/__init__.py."""

import sqlite3

import app.services.data as data_service
import pytest
from app.services.data import __all__ as data_all
from app.services.data.storage import db_helper
from app.utils.logger import logger


@pytest.fixture(autouse=True)
def clean_db() -> None:
    """Fixture to clean database before and after each test."""
    try:
        with db_helper.get_connection() as conn:
            conn.execute("DELETE FROM data_jobs;")
            conn.execute("DELETE FROM feed_state;")
    except sqlite3.Error as e:
        logger.warning("Database cleanup failed in public exports test: %s", e)


def test_public_exports_count() -> None:
    """Verify that exactly 21 clean service APIs are exported."""
    expected_service_apis = {
        "aggregate_ticks_to_bars",
        "align_multitimeframe_data",
        "clear_data_cache",
        "create_data_update_job",
        "generate_synthetic_bars",
        "generate_synthetic_ticks",
        "get_data",
        "get_data_availability",
        "get_data_update_job_status",
        "get_feed_status",
        "get_market_hours",
        "get_symbol_metadata",
        "get_trading_sessions",
        "label_market_data",
        "list_symbols",
        "load_local_dataset",
        "resample_ohlcv",
        "run_data_update_job_once",
        "save_market_data",
        "start_data_update_job",
        "stop_data_update_job",
    }
    assert set(data_all) == expected_service_apis
    assert len(data_all) == 21


def test_service_signatures_exist() -> None:
    """Ensure every exported service function is callable."""
    for api_name in data_all:
        api_func = getattr(data_service, api_name)
        assert callable(api_func)


def test_get_data_routing() -> None:
    """Exercise clean gateway get_data queries."""
    # 1. OHLCV Data
    res = data_service.get_data(
        symbol="EURUSD",
        timeframe="M5",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T01:00:00Z",
        source="synthetic",
        data_kind="ohlcv",
    )
    assert isinstance(res, list)
    assert len(res) > 0

    # 2. Tick Data
    res = data_service.get_data(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T00:05:00Z",
        source="synthetic",
        data_kind="ticks",
    )
    assert isinstance(res, list)
    assert len(res) > 0

    # 3. Spread Data
    res = data_service.get_data(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T00:05:00Z",
        source="synthetic",
        data_kind="spreads",
    )
    assert isinstance(res, list)
    assert len(res) > 0


def test_metadata_and_availability_services() -> None:
    """Exercise metadata and availability services."""
    # Symbol metadata
    res_meta = data_service.get_symbol_metadata(symbol="EURUSD", source="csv")
    assert isinstance(res_meta, dict)
    assert res_meta["symbol"] == "EURUSD"

    # List symbols
    res_list = data_service.list_symbols(source="csv")
    assert isinstance(res_list, list)

    # Data Availability
    res_avail = data_service.get_data_availability(
        symbol="EURUSD", timeframe="M5", source="csv"
    )
    assert isinstance(res_avail, dict)
    assert res_avail["symbol"] == "EURUSD"

    # Market Hours
    res_hours = data_service.get_market_hours(symbol="EURUSD")
    assert isinstance(res_hours, dict)
    assert res_hours["symbol"] == "EURUSD"

    # Trading Sessions
    import app.utils.normalization as norm_utils

    t_s = norm_utils.normalize_timestamp("2026-06-01T00:00:00Z")
    t_e = norm_utils.normalize_timestamp("2026-06-01T08:00:00Z")
    res_sessions = data_service.get_trading_sessions(start_time=t_s, end_time=t_e)
    assert isinstance(res_sessions, list)
    assert len(res_sessions) > 0


def test_storage_and_transforms_services() -> None:
    """Exercise storage and transforms services."""
    # Synthetic ticks & bars
    ticks = data_service.generate_synthetic_ticks(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        num_ticks=10,
        start_price=1.0,
        average_spread=0.0002,
        volatility=0.001,
        seed=42,
    )
    assert isinstance(ticks, list)
    assert len(ticks) == 10

    bars = data_service.generate_synthetic_bars(
        symbol="EURUSD",
        timeframe="M5",
        start_time="2026-06-01T00:00:00Z",
        num_bars=10,
        start_price=1.0,
        drift=0.0001,
        volatility=0.01,
        seed=42,
    )
    assert isinstance(bars, list)
    assert len(bars) == 10

    # Save and Load
    save_res = data_service.save_market_data(
        records=bars,
        path_str="artifacts/data/test_save.csv",
        format_str="csv",
        overwrite=True,
    )
    assert save_res["record_count"] == 10

    loaded = data_service.load_local_dataset(
        path_str="artifacts/data/test_save.csv",
    )
    assert isinstance(loaded, list)
    assert len(loaded) == 10

    # Resample
    resampled = data_service.resample_ohlcv(
        records=bars,
        target_timeframe="M15",
    )
    assert isinstance(resampled, list)

    # Align
    records_map = {"M5": bars}
    target_timestamps = [r["timestamp"] for r in bars]
    aligned = data_service.align_multitimeframe_data(
        datasets=records_map,
        target_timestamps=target_timestamps,
    )
    assert isinstance(aligned, dict)

    # Aggregate
    aggregated = data_service.aggregate_ticks_to_bars(
        ticks=ticks,
        timeframe="M1",
    )
    assert isinstance(aggregated, list)

    # Label
    labeled = data_service.label_market_data(
        records=bars,
        horizon=2,
        threshold=0.001,
    )
    assert isinstance(labeled, list)
    assert len(labeled) == 10
