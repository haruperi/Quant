"""Unit tests for scheduler leases, job states, feed overflows, and heartbeats."""

import sqlite3

import pytest
from app.services.data.scheduler import (
    create_data_update_job,
    get_data_update_job_status,
    get_feed_status,
    handle_feed_overflow,
    recover_crashed_jobs,
    register_mock_feed,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)
from app.services.data.storage import db_helper
from app.utils.errors import ValidationError
from app.utils.logger import logger


@pytest.fixture(autouse=True)
def cleanup_database() -> None:
    """Clean data_jobs and feed_state tables before/after each test."""
    try:
        with db_helper.get_connection() as conn:
            conn.execute("DELETE FROM data_jobs;")
            conn.execute("DELETE FROM feed_state;")
    except sqlite3.Error as e:
        logger.warning("Database cleanup failed: %s", e)


def test_real_time_feed_overflow_policies() -> None:
    """Verify overflow handler actions under different policies."""
    feed_id = "test_feed_id"
    register_mock_feed(feed_id, "mt5", "EURUSD", "ticks")

    # Halt policy should fail/halt feed
    res = handle_feed_overflow(feed_id, "halt")
    assert res["state"] == "failed"

    # drop_and_reconcile should increment dropped/gap counts
    # and move state to reconciling
    res = handle_feed_overflow(feed_id, "drop_and_reconcile")
    assert res["state"] == "reconciling"
    assert res["dropped_count"] == 1
    assert res["gap_count"] == 1

    # backpressure policy keeps connected
    res = handle_feed_overflow(feed_id, "backpressure")
    assert res["state"] == "connected"


def test_get_feed_status_observability() -> None:
    """Test get_feed_status tool lookup."""
    feed_id = "feed_obs_id"
    register_mock_feed(feed_id, "ctrader", "GBPUSD", "bars")

    res = get_feed_status(feed_id=feed_id)
    assert isinstance(res, dict)
    assert res["feed_id"] == feed_id
    assert res["source"] == "ctrader"


def test_scheduler_jobs_lifecycle() -> None:
    """Test scheduler job creation, deduplication, start, stop, status."""
    job_name = "EURUSD_M5_Ingestion"

    # Create job
    res = create_data_update_job(
        name=job_name,
        source="csv",
        symbols=["EURUSD"],
        timeframes=["M5"],
        data_kind="bars",
        storage_format="csv",
        storage_path="data/raw",
        schedule="* * * * *",
    )
    assert res["name"] == job_name
    assert res["state"] == "created"

    # Attempt duplicate creation should fail
    with pytest.raises(ValidationError):
        create_data_update_job(
            name=job_name,
            source="csv",
            symbols=["EURUSD"],
            timeframes=["M5"],
            data_kind="bars",
            storage_format="csv",
            storage_path="data/raw",
            schedule="* * * * *",
        )

    # Start job
    start_res = start_data_update_job(job_name)
    assert start_res["state"] == "running"

    # Check status
    status_res = get_data_update_job_status(job_name)
    assert status_res["state"] == "running"

    # Stop job
    stop_res = stop_data_update_job(job_name)
    assert stop_res["state"] == "stopped"


def test_run_job_once_behavior() -> None:
    """Verify run-once does not schedule background loop but executes immediately."""
    job_name = "Run_Once_Job"
    create_data_update_job(
        name=job_name,
        source="synthetic",
        symbols=["GBPUSD"],
        timeframes=["M15"],
        data_kind="bars",
        storage_format="parquet",
        storage_path="data/processed",
        schedule=None,  # No schedule
    )

    # Start recurring should fail due to no schedule
    with pytest.raises(ValidationError):
        start_data_update_job(job_name)

    # Run once
    run_res = run_data_update_job_once(job_name)
    assert run_res["state"] == "running"


def test_crash_recovery_sequence() -> None:
    """Verify crashed job (running in DB) recovers to 'recovering' state."""
    job_name = "Crashed_Job"
    create_data_update_job(
        name=job_name,
        source="csv",
        symbols=["EURUSD"],
        timeframes=["M1"],
        data_kind="bars",
        storage_format="csv",
        storage_path="data/raw",
        schedule="* * * * *",
    )

    # Force database state to running
    with db_helper.get_connection() as conn:
        conn.execute(
            "UPDATE data_jobs SET state = 'running' WHERE name = ?;", (job_name,)
        )

    # Trigger recovery
    recovered = recover_crashed_jobs()
    assert recovered >= 1

    # Check state
    status = get_data_update_job_status(job_name)
    assert status["state"] == "recovering"
    assert status["last_error"] == "SYSTEM_CRASH_DETECTION"
