"""Unit tests for public agent tools exposed in agentic/tools/data/."""

import sqlite3

import agentic.tools.data as data_service
import pytest
from agentic.tools.data import __all__ as data_all
from app.services.data.scheduler import register_mock_feed
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
        logger.warning("Database cleanup failed in test_data_tools: %s", e)


def test_public_exports_count() -> None:
    """Verify that exactly 24 approved tools are exported."""
    expected_tools = {
        "get_market_data",
        "get_tick_data",
        "get_spread_data",
        "get_symbol_metadata",
        "list_symbols",
        "get_data_availability",
        "get_market_hours",
        "get_trading_sessions",
        "get_historical_volume",
        "save_market_data",
        "load_local_dataset",
        "resample_ohlcv",
        "align_multitimeframe_data",
        "generate_synthetic_ticks",
        "generate_synthetic_bars",
        "aggregate_ticks_to_bars",
        "label_market_data",
        "create_data_update_job",
        "start_data_update_job",
        "stop_data_update_job",
        "run_data_update_job_once",
        "get_data_update_job_status",
        "get_feed_status",
        "clear_data_cache",
    }
    assert set(data_all) == expected_tools
    assert len(data_all) == 24


def test_tool_signatures_exist() -> None:
    """Ensure every exported tool is callable."""
    for tool_name in data_all:
        tool_func = getattr(data_service, tool_name)
        assert callable(tool_func)


def test_market_and_tick_data_tools() -> None:
    """Exercise get_market_data, get_tick_data, and get_spread_data tools."""
    # 1. Market Data
    res = data_service.get_market_data(
        symbol="EURUSD",
        timeframe="M5",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T01:00:00Z",
        source="synthetic",
    )
    assert res["status"] == "success"

    # Error path
    err_res = data_service.get_market_data(
        symbol="",
        timeframe="invalid",
        start_time="invalid",
        end_time="invalid",
    )
    assert err_res["status"] == "error"

    # 2. Tick Data
    res = data_service.get_tick_data(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T00:05:00Z",
        source="synthetic",
    )
    assert res["status"] == "success"

    err_res = data_service.get_tick_data(
        symbol="",
        start_time="invalid",
        end_time="invalid",
    )
    assert err_res["status"] == "error"

    # 3. Spread Data
    res = data_service.get_spread_data(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T00:05:00Z",
        source="synthetic",
    )
    assert res["status"] == "success"

    err_res = data_service.get_spread_data(
        symbol="",
        start_time="invalid",
        end_time="invalid",
    )
    assert err_res["status"] == "error"


def test_metadata_and_availability_tools() -> None:
    """Exercise metadata and availability tools."""
    # Symbol metadata
    res = data_service.get_symbol_metadata(symbol="EURUSD", source="csv")
    assert res["status"] == "success"
    assert res["data"]["symbol"] == "EURUSD"

    err_res = data_service.get_symbol_metadata(symbol="", source="invalid")
    assert err_res["status"] == "error"

    # List symbols
    res = data_service.list_symbols(source="csv")
    assert res["status"] == "success"

    err_res = data_service.list_symbols(source="invalid")
    assert err_res["status"] == "error"

    # Data Availability
    res = data_service.get_data_availability(
        symbol="EURUSD", timeframe="M5", source="csv"
    )
    assert res["status"] == "success"

    err_res = data_service.get_data_availability(
        symbol="", timeframe="invalid", source="invalid"
    )
    assert "status" in err_res

    # Market Hours
    res = data_service.get_market_hours(symbol="EURUSD")
    assert res["status"] == "success"

    err_res = data_service.get_market_hours(symbol="")
    assert "status" in err_res

    # Trading Sessions
    res = data_service.get_trading_sessions(
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T08:00:00Z",
    )
    assert res["status"] == "success"

    err_res = data_service.get_trading_sessions(
        start_time="invalid",
        end_time="invalid",
    )
    assert err_res["status"] == "error"

    # Historical Volume
    res = data_service.get_historical_volume(
        symbol="EURUSD",
        timeframe="M5",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T01:00:00Z",
        source="synthetic",
    )
    assert res["status"] == "success"

    err_res = data_service.get_historical_volume(
        symbol="",
        timeframe="invalid",
        start_time="invalid",
        end_time="invalid",
    )
    assert err_res["status"] == "error"


def test_storage_and_transforms_tools() -> None:
    """Exercise storage and transforms tools."""
    # Synthetic ticks & bars
    res_ticks = data_service.generate_synthetic_ticks(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        num_ticks=10,
        seed=42,
    )
    assert res_ticks["status"] == "success"
    ticks = res_ticks["data"]

    err_ticks = data_service.generate_synthetic_ticks(
        symbol="",
        start_time="invalid",
    )
    assert err_ticks["status"] == "error"

    res_bars = data_service.generate_synthetic_bars(
        symbol="EURUSD",
        timeframe="M5",
        start_time="2026-06-01T00:00:00Z",
        num_bars=10,
        seed=42,
    )
    assert res_bars["status"] == "success"
    bars = res_bars["data"]

    err_bars = data_service.generate_synthetic_bars(
        symbol="",
        timeframe="invalid",
        start_time="invalid",
    )
    assert err_bars["status"] == "error"

    # Save and Load
    save_res = data_service.save_market_data(
        records=bars,
        path_str="artifacts/data/test_save.csv",
        format_str="csv",
        overwrite=True,
    )
    assert save_res["status"] == "success"

    load_res = data_service.load_local_dataset(
        path_str="artifacts/data/test_save.csv",
    )
    assert load_res["status"] == "success"
    assert len(load_res["data"]) == 10

    err_load = data_service.load_local_dataset(
        path_str="invalid_path.csv",
    )
    assert err_load["status"] == "error"

    # Resample
    resample_res = data_service.resample_ohlcv(
        records=bars,
        source_timeframe="M5",
        target_timeframe="M15",
    )
    assert resample_res["status"] == "success"

    err_resample = data_service.resample_ohlcv(
        records=[],
        source_timeframe="invalid",
        target_timeframe="invalid",
    )
    assert err_resample["status"] == "error"

    # Align
    records_map = {"M5": bars}
    align_res = data_service.align_multitimeframe_data(
        records_map=records_map,
        base_timeframe="M5",
    )
    assert align_res["status"] == "success"

    err_align = data_service.align_multitimeframe_data(
        records_map={},
        base_timeframe="invalid",
    )
    assert err_align["status"] == "error"

    # Aggregate
    agg_res = data_service.aggregate_ticks_to_bars(
        ticks=ticks,
        timeframe="M1",
    )
    assert agg_res["status"] == "success"

    err_agg = data_service.aggregate_ticks_to_bars(
        ticks=ticks,
        timeframe="invalid",
    )
    assert err_agg["status"] == "error"

    # Label
    label_res = data_service.label_market_data(
        records=bars,
        method="fixed_horizon",
        horizon=2,
    )
    assert label_res["status"] == "success"

    err_label = data_service.label_market_data(
        records=bars,
        method="invalid_method",
    )
    assert err_label["status"] == "error"


def test_scheduler_and_cache_tools() -> None:
    """Exercise scheduler and cache tools."""
    # Create Job
    job_name = "test_tool_job"
    res = data_service.create_data_update_job(
        name=job_name,
        source="csv",
        symbols=["EURUSD"],
        timeframes=["M5"],
        data_kind="bars",
        storage_format="csv",
        storage_path="data/raw",
        schedule="* * * * *",
    )
    assert res["status"] == "success"

    err_res = data_service.create_data_update_job(
        name="",
        source="",
        symbols=[],
        timeframes=[],
        data_kind="",
        storage_format="",
        storage_path="",
    )
    assert err_res["status"] == "error"

    # Start Job
    start_res = data_service.start_data_update_job(job_name)
    assert start_res["status"] == "success"

    err_start = data_service.start_data_update_job("non_existent_job")
    assert err_start["status"] == "error"

    # Stop Job
    stop_res = data_service.stop_data_update_job(job_name)
    assert stop_res["status"] == "success"

    err_stop = data_service.stop_data_update_job("non_existent_job")
    assert err_stop["status"] == "error"

    # Run Job Once
    run_res = data_service.run_data_update_job_once(job_name)
    assert run_res["status"] == "success"

    err_run = data_service.run_data_update_job_once("non_existent_job")
    assert err_run["status"] == "error"

    # Get Job Status
    status_res = data_service.get_data_update_job_status(job_name)
    assert status_res["status"] == "success"

    err_status = data_service.get_data_update_job_status("non_existent_job")
    assert err_status["status"] == "error"

    # Feed Status
    register_mock_feed("test_feed_id", "mt5", "EURUSD", "ticks")
    feed_res = data_service.get_feed_status(feed_id="test_feed_id")
    assert feed_res["status"] == "success"

    err_feed = data_service.get_feed_status(feed_id="non_existent")
    assert err_feed["status"] == "error"

    # Clear Data Cache
    clear_res = data_service.clear_data_cache(namespace="data_cache")
    assert clear_res["status"] == "success"

    err_clear = data_service.clear_data_cache(namespace="invalid")
    assert err_clear["status"] == "error"
