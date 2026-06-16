"""Data update scheduler, job lifecycle, and feeds tracking manager.

Provides persisted job tracking, lease concurrency controls, background job loops,
and active feeds monitoring/heartbeat status checks.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any, Literal

from app.services.data.storage import db_helper
from app.services.data.validation import (
    MAX_SYMBOLS_PER_JOB,
    MAX_TIMEFRAMES_PER_JOB,
    validate_license,
)
from app.utils.errors import DataError, ValidationError
from app.utils.logger import logger

# In-memory maps
ACTIVE_JOB_TASKS: dict[str, asyncio.Task[None]] = {}
ACTIVE_FEEDS: dict[str, dict[str, Any]] = {}
BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """Helper to get running event loop or create a new one safely."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        try:
            return asyncio.get_event_loop_policy().get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop


def recover_crashed_jobs() -> int:
    """Recover jobs that were left in the 'running' state after a system crash."""
    logger.info("Executing scheduler crash recovery sequence...")
    now_str = datetime.now(UTC).isoformat()
    count = 0
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, state FROM data_jobs WHERE state = 'running';"
            )
            rows = cursor.fetchall()
            for r in rows:
                job_id = r["id"]
                logger.warning(
                    f"Crashed job detected: name={r['name']}. "
                    "Transitioning to recovering state."
                )
                conn.execute(
                    """
                    UPDATE data_jobs
                    SET state = 'recovering',
                        last_error = 'SYSTEM_CRASH_DETECTION',
                        lease_owner = NULL,
                        lease_expires = NULL,
                        updated_at = ?
                    WHERE id = ?;
                    """,
                    (now_str, job_id),
                )
                count += 1
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to perform database crash recovery: {e}")
    return count


# Execute recovery on module load
recover_crashed_jobs()


# --- Scheduler Jobs Business Logic ---
def _validate_job_creation_args(
    name: str,
    source: str,
    symbols: list[str],
    timeframes: list[str],
    request_id: str | None = None,
) -> None:
    """Validate job creation parameters (licensing, lengths, non-emptiness)."""
    if not name or not name.strip():
        raise ValidationError("Job name cannot be empty.", code="INVALID_INPUT")
    if not source:
        raise ValidationError(
            "Source identifier cannot be empty.", code="INVALID_INPUT"
        )
    if not symbols:
        raise ValidationError("Symbols list cannot be empty.", code="INVALID_INPUT")
    if not timeframes:
        raise ValidationError("Timeframes list cannot be empty.", code="INVALID_INPUT")

    if len(symbols) > MAX_SYMBOLS_PER_JOB:
        raise ValidationError("Max symbols limit exceeded.", code="INVALID_INPUT")
    if len(timeframes) > MAX_TIMEFRAMES_PER_JOB:
        raise ValidationError("Max timeframes limit exceeded.", code="INVALID_INPUT")

    for sym in symbols:
        try:
            validate_license(
                source,
                sym,
                workflow_context="research",
                request_id=request_id,
            )
        except ValidationError as e:
            logger.error(f"License check failed for {source}:{sym}: {e}")
            err_msg = f"License check failed: {e}"
            raise ValidationError(err_msg, code="LICENSE_RESTRICTION") from e


def create_data_update_job(
    name: str,
    source: str,
    symbols: list[str],
    timeframes: list[str],
    data_kind: str,
    storage_format: str,
    storage_path: str,
    start_time: str | None = None,
    end_time: str | None = None,
    schedule: str | None = None,
    enabled: bool = True,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a persisted job definition in the database."""
    logger.info(
        f"Creating data update job: name={name}, source={source}",
        extra={"request_id": request_id},
    )

    _validate_job_creation_args(
        name=name,
        source=source,
        symbols=symbols,
        timeframes=timeframes,
        request_id=request_id,
    )

    exists = False
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT id FROM data_jobs WHERE name = ?;", (name,))
            if cursor.fetchone():
                exists = True
    except Exception as e:
        err_msg = f"Database error checking duplicate jobs: {e}"
        raise DataError(err_msg) from e

    if exists:
        err_msg = f"Job with name '{name}' already exists."
        raise ValidationError(err_msg, code="INVALID_INPUT")

    job_id = f"job_{name.lower().replace(' ', '_')}"
    now_str = datetime.now(UTC).isoformat()
    symbols_str = ",".join(symbols)
    timeframes_str = ",".join(timeframes)

    job_data = {
        "id": job_id,
        "name": name,
        "source": source,
        "symbols": symbols_str,
        "timeframes": timeframes_str,
        "data_kind": data_kind,
        "storage_format": storage_format,
        "storage_path": storage_path,
        "start_time": start_time,
        "end_time": end_time,
        "schedule": schedule,
        "enabled": 1 if enabled else 0,
        "state": "created",
        "last_run_status": None,
        "last_checkpoint": None,
        "last_error": None,
        "next_run": None,
        "lease_owner": None,
        "lease_expires": None,
        "created_at": now_str,
        "updated_at": now_str,
    }

    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO data_jobs (
                    id, name, source, symbols, timeframes, data_kind, storage_format,
                    storage_path, start_time, end_time, schedule, enabled, state,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    job_id,
                    name,
                    source,
                    symbols_str,
                    timeframes_str,
                    data_kind,
                    storage_format,
                    storage_path,
                    start_time,
                    end_time,
                    schedule,
                    1 if enabled else 0,
                    "created",
                    now_str,
                    now_str,
                ),
            )
    except Exception as e:
        logger.error(f"Failed to create job {name} in DB: {e}")
        err_msg = f"Database error writing job definition: {e}"
        raise DataError(err_msg) from e

    return job_data


async def _run_job_loop(job_name: str) -> None:
    """Internal task loop representing a running scheduled job."""
    logger.info(f"Background worker loop started for job '{job_name}'.")
    while True:
        try:
            # Check enabled status and lease
            job = None
            with db_helper.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM data_jobs WHERE name = ?;", (job_name,)
                )
                row = cursor.fetchone()
                if row:
                    job = dict(row)

            if not job or not job["enabled"]:
                logger.info(f"Job '{job_name}' disabled. Stopping worker loop.")
                break

            # Process database updates simulated steps
            now_str = datetime.now(UTC).isoformat()
            with db_helper.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE data_jobs
                    SET state = 'running',
                        last_run_status = 'success',
                        last_checkpoint = ?,
                        updated_at = ?
                    WHERE name = ?;
                    """,
                    (now_str, now_str, job_name),
                )

            # Rest briefly
            await asyncio.sleep(60.0)

        except asyncio.CancelledError:
            logger.info(f"Worker task for '{job_name}' was cancelled.")
            break
        except Exception as e:  # noqa: BLE001
            logger.error(f"Scheduler worker loop error on job '{job_name}': {e}")
            await asyncio.sleep(10.0)


def start_data_update_job(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Start recurring background execution for a job."""
    logger.info(
        f"Starting scheduled job: name={name}",
        extra={"request_id": request_id},
    )

    job = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_jobs WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
    except Exception as e:
        err_msg = f"Database lookup failure: {e}"
        raise DataError(err_msg) from e

    if not job:
        err_msg = f"Job with name '{name}' not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    if not job["schedule"]:
        err_msg = f"Job '{name}' cannot start recurringly because schedule is omitted."
        raise ValidationError(
            err_msg,
            code="INVALID_INPUT",
        )

    if name in ACTIVE_JOB_TASKS and not ACTIVE_JOB_TASKS[name].done():
        return {"job_id": job["id"], "state": "running"}

    now_str = datetime.now(UTC).isoformat()
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                "UPDATE data_jobs SET enabled = 1, state = 'running', "
                "updated_at = ? WHERE name = ?;",
                (now_str, name),
            )
    except Exception as e:
        err_msg = f"Failed to enable job '{name}': {e}"
        raise DataError(err_msg) from e

    loop = _get_or_create_event_loop()
    task = loop.create_task(_run_job_loop(name))
    ACTIVE_JOB_TASKS[name] = task

    return {"job_id": job["id"], "state": "running"}


def stop_data_update_job(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Stop or disable scheduled background execution for a job."""
    logger.info(f"Stopping job: name={name}", extra={"request_id": request_id})

    job = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_jobs WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
    except Exception as e:
        err_msg = f"Database lookup error: {e}"
        raise DataError(err_msg) from e

    if not job:
        err_msg = f"Job '{name}' not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    task = ACTIVE_JOB_TASKS.get(name)
    if task and not task.done():
        task.cancel()

    now_str = datetime.now(UTC).isoformat()
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                UPDATE data_jobs
                SET enabled = 0,
                    state = 'stopped',
                    lease_owner = NULL,
                    lease_expires = NULL,
                    updated_at = ?
                WHERE name = ?;
                """,
                (now_str, name),
            )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to update database on stop for {name}: {e}")

    return {"job_id": job["id"], "state": "stopped"}


async def _execute_single_run(name: str) -> None:
    """Internal implementation for run_once execution."""
    logger.info(f"Starting one-time execution run for job '{name}'...")
    now_str = datetime.now(UTC).isoformat()
    try:
        await asyncio.sleep(0.2)
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                UPDATE data_jobs
                SET state = 'completed',
                    last_run_status = 'success',
                    last_checkpoint = 'run_once_success',
                    last_error = NULL,
                    updated_at = ?
                WHERE name = ?;
                """,
                (now_str, name),
            )
    except Exception as ex:  # noqa: BLE001
        logger.error(f"One-off execution failed for '{name}': {ex}")
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                UPDATE data_jobs
                SET state = 'failed',
                    last_run_status = 'failed',
                    last_error = ?,
                    updated_at = ?
                WHERE name = ?;
                """,
                (str(ex), now_str, name),
            )


def run_data_update_job_once(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Execute one immediate update run of a job definition."""
    logger.info(
        f"Triggering immediate run: name={name}",
        extra={"request_id": request_id},
    )

    job = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_jobs WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
    except Exception as e:
        err_msg = f"Database lookup error: {e}"
        raise DataError(err_msg) from e

    if not job:
        err_msg = f"Job '{name}' not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    now_str = datetime.now(UTC).isoformat()
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                "UPDATE data_jobs SET state = 'running', "
                "updated_at = ? WHERE name = ?;",
                (now_str, name),
            )
    except Exception as e:
        err_msg = f"Database update failure: {e}"
        raise DataError(err_msg) from e

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(_execute_single_run(name))
        BACKGROUND_TASKS.add(task)
        task.add_done_callback(BACKGROUND_TASKS.discard)
    except RuntimeError:
        asyncio.run(_execute_single_run(name))

    return {"job_id": job["id"], "state": "running"}


def get_data_update_job_status(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Inspect the status details of a job definition."""
    logger.info(
        f"Retrieving status for job: name={name}",
        extra={"request_id": request_id},
    )

    job = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_jobs WHERE name = ?;", (name,))
            row = cursor.fetchone()
            if row:
                job = dict(row)
    except Exception as e:
        err_msg = f"Database query error: {e}"
        raise DataError(err_msg) from e

    if not job:
        err_msg = f"Job '{name}' not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    return {
        "job_id": job["id"],
        "name": job["name"],
        "source": job["source"],
        "symbols": job["symbols"].split(",") if job["symbols"] else [],
        "timeframes": job["timeframes"].split(",") if job["timeframes"] else [],
        "data_kind": job["data_kind"],
        "state": job["state"],
        "enabled": bool(job["enabled"]),
        "last_run_status": job["last_run_status"],
        "last_checkpoint": job["last_checkpoint"],
        "last_error": job["last_error"],
        "next_run": job["next_run"],
        "lease_owner": job["lease_owner"],
        "lease_expires": job["lease_expires"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
    }


# --- Active Feeds State Management ---
def register_mock_feed(
    feed_id: str,
    source: str,
    symbol: str,
    data_kind: str,
    state: str = "connected",
    buffer_depth: int = 0,
    dropped_count: int = 0,
    gap_count: int = 0,
    reconnect_count: int = 0,
    circuit_breaker_state: str = "closed",
    last_error: str | None = None,
) -> None:
    """Register/update active feed in-memory and SQLite DB."""
    now_str = datetime.now(UTC).isoformat()
    feed_data = {
        "feed_id": feed_id,
        "source": source,
        "symbol": symbol,
        "data_kind": data_kind,
        "state": state,
        "last_heartbeat": now_str,
        "last_event": now_str,
        "buffer_depth": buffer_depth,
        "dropped_count": dropped_count,
        "gap_count": gap_count,
        "reconnect_count": reconnect_count,
        "circuit_breaker_state": circuit_breaker_state,
        "last_error": last_error,
        "created_at": now_str,
        "updated_at": now_str,
    }
    ACTIVE_FEEDS[feed_id] = feed_data

    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO feed_state (
                    feed_id, source, symbol, data_kind, state, last_heartbeat,
                    last_event, buffer_depth, dropped_count, gap_count,
                    reconnect_count, circuit_breaker_state, last_error,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    feed_id,
                    source,
                    symbol,
                    data_kind,
                    state,
                    now_str,
                    now_str,
                    buffer_depth,
                    dropped_count,
                    gap_count,
                    reconnect_count,
                    circuit_breaker_state,
                    last_error,
                    now_str,
                    now_str,
                ),
            )
    except Exception as e:
        logger.error(f"Failed to persist feed state for {feed_id}: {e}")
        err_msg = f"Database sync failure: {e}"
        raise DataError(err_msg) from e


def handle_feed_overflow(
    feed_id: str,
    policy: Literal["halt", "drop_and_reconcile", "backpressure"],
) -> dict[str, Any]:
    """Handle a buffer overflow event on an active feed."""
    feed = ACTIVE_FEEDS.get(feed_id)
    if not feed:
        try:
            with db_helper.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM feed_state WHERE feed_id = ?;", (feed_id,)
                )
                row = cursor.fetchone()
                if row:
                    feed = dict(row)
        except Exception as e:
            err_msg = f"Database query error: {e}"
            raise DataError(err_msg) from e

    if not feed:
        err_msg = f"Feed {feed_id} not found."
        raise ValidationError(err_msg, code="JOB_NOT_FOUND")

    now_str = datetime.now(UTC).isoformat()
    if policy == "halt":
        feed["state"] = "failed"
        feed["last_error"] = "BUFFER_OVERFLOW"
        msg = f"Feed {feed_id} halted due to buffer overflow."
        logger.error(msg)
    elif policy == "drop_and_reconcile":
        feed["dropped_count"] += 1
        feed["gap_count"] += 1
        feed["state"] = "reconciling"
        feed["last_error"] = "BUFFER_OVERFLOW"
        msg = f"Feed {feed_id} overflow: dropping records and entering reconciliation."
        logger.warning(msg)
    elif policy == "backpressure":
        feed["state"] = "connected"
        msg = f"Feed {feed_id} applying backpressure."
        logger.info(msg)
    else:
        err_msg = f"Unsupported overflow policy: {policy}"
        raise ValidationError(err_msg)

    feed["updated_at"] = now_str
    ACTIVE_FEEDS[feed_id] = feed

    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                UPDATE feed_state
                SET state = ?, dropped_count = ?, gap_count = ?,
                    last_error = ?, updated_at = ?
                WHERE feed_id = ?;
                """,
                (
                    feed["state"],
                    feed["dropped_count"],
                    feed["gap_count"],
                    feed["last_error"],
                    now_str,
                    feed_id,
                ),
            )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to update database for feed {feed_id} overflow: {e}")

    return {
        "feed_id": feed_id,
        "action": policy,
        "state": feed["state"],
        "dropped_count": feed["dropped_count"],
        "gap_count": feed["gap_count"],
    }


def _filter_in_memory_feeds(
    feed_id: str | None = None,
    source: str | None = None,
    symbol: str | None = None,
    data_kind: str | None = None,
) -> list[dict[str, Any]]:
    """Filter active in-memory feeds based on criteria."""
    matching_feeds = []
    if feed_id:
        if feed_id in ACTIVE_FEEDS:
            matching_feeds.append(ACTIVE_FEEDS[feed_id])
    else:
        for f in ACTIVE_FEEDS.values():
            if source and f["source"].lower() != source.lower():
                continue
            if symbol and f["symbol"].upper() != symbol.upper():
                continue
            if data_kind and f["data_kind"].lower() != data_kind.lower():
                continue
            matching_feeds.append(f)
    return matching_feeds


def _get_feeds_from_db(
    feed_id: str | None = None,
    source: str | None = None,
    symbol: str | None = None,
    data_kind: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve feeds from database matching the given criteria."""
    matching_feeds = []
    try:
        with db_helper.get_connection() as conn:
            if feed_id:
                cursor = conn.execute(
                    "SELECT * FROM feed_state WHERE feed_id = ?;", (feed_id,)
                )
            else:
                query = "SELECT * FROM feed_state WHERE 1=1"
                params = []
                if source:
                    query += " AND LOWER(source) = LOWER(?)"
                    params.append(source)
                if symbol:
                    query += " AND UPPER(symbol) = UPPER(?)"
                    params.append(symbol)
                if data_kind:
                    query += " AND LOWER(data_kind) = LOWER(?)"
                    params.append(data_kind)
                cursor = conn.execute(query, params)

            rows = cursor.fetchall()
            for r in rows:
                matching_feeds.append(
                    {
                        "feed_id": r["feed_id"],
                        "source": r["source"],
                        "symbol": r["symbol"],
                        "data_kind": r["data_kind"],
                        "state": r["state"],
                        "last_heartbeat": r["last_heartbeat"],
                        "last_event": r["last_event"],
                        "buffer_depth": int(r["buffer_depth"]),
                        "dropped_count": int(r["dropped_count"]),
                        "gap_count": int(r["gap_count"]),
                        "reconnect_count": int(r["reconnect_count"]),
                        "circuit_breaker_state": r["circuit_breaker_state"],
                        "last_error": r["last_error"],
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                    }
                )
    except Exception as e:
        logger.error(f"Database error during feed lookup: {e}")
        err_msg = f"Database error checking feeds: {e}"
        raise DataError(err_msg) from e
    return matching_feeds


def get_feed_status(
    feed_id: str | None = None,
    source: str | None = None,
    symbol: str | None = None,
    data_kind: str | None = None,
    *,
    request_id: str | None = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Inspect real-time feed health, heartbeats, buffer depth, and circuit states."""
    logger.info(
        f"Retrieving feed status: id={feed_id}, source={source}, symbol={symbol}",
        extra={"request_id": request_id},
    )

    matching_feeds = _filter_in_memory_feeds(
        feed_id=feed_id, source=source, symbol=symbol, data_kind=data_kind
    )

    if not matching_feeds:
        matching_feeds = _get_feeds_from_db(
            feed_id=feed_id, source=source, symbol=symbol, data_kind=data_kind
        )

    if not matching_feeds:
        err_msg = "No matching real-time feeds found."
        logger.error(err_msg, extra={"request_id": request_id})
        raise ValidationError(err_msg, code="DATA_NOT_FOUND")

    if feed_id:
        return matching_feeds[0]

    return matching_feeds
