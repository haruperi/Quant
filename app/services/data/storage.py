"""Storage, persistence, and local caching utilities.

Manages SQLite database connections, schema migrations, local file dataset (CSV/Parquet)
read/write operations under approved storage roots, atomic file operations, quarantine
writes, and database-backed cache operations.
"""

import hashlib
import json
import os
import sqlite3
import tempfile
from collections.abc import Generator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from app.utils.errors import DataError, ValidationError
from app.utils.logger import logger
from app.utils.paths import ensure_parent_dir, normalize_path

APPROVED_STORAGE_ROOTS: list[str] = [
    "data/raw",
    "data/processed",
    "data/cache",
    "artifacts/data",
]

QUARANTINE_DIR: str = "data/quarantine"
DB_FILE_PATH: str = "data/data_service.db"

DEFAULT_SCHEMA_VERSION: str = "v1"
DEFAULT_NORMALIZATION_VERSION: str = "v1"


def validate_storage_path(path_str: str) -> Path:
    """Validate that the path is secure and falls within approved storage roots.

    Args:
        path_str: The target file path string.

    Returns:
        Path: Resolved absolute path object.

    Raises:
        ValidationError: If the path is unsafe, outside approved roots, or uses
                         unsupported extensions.
    """
    if not path_str:
        raise ValidationError("Path cannot be empty.")

    if ".." in path_str:
        raise ValidationError("Parent traversal using '..' is forbidden.")

    parts = Path(path_str).parts
    for part in parts:
        if part.startswith(".") and part != ".":
            raise ValidationError("Hidden files or directories are forbidden.")

    try:
        norm_path_str = normalize_path(path_str)
        resolved_path = Path(norm_path_str).resolve()
    except Exception as e:
        logger.error(f"Path normalization failure for {path_str}: {e}")
        err_path = f"Invalid path: {path_str}"
        raise ValidationError(err_path) from e

    workspace_root = Path.cwd().resolve()
    is_inside_root = False
    for root_rel in APPROVED_STORAGE_ROOTS:
        root_abs = (workspace_root / root_rel).resolve()
        try:
            resolved_path.relative_to(root_abs)
            is_inside_root = True
            break
        except ValueError:
            continue

    if not is_inside_root:
        err_msg = f"Path {path_str} is outside approved storage roots."
        logger.error(err_msg)
        raise ValidationError(err_msg)

    ext = resolved_path.suffix.lower()
    if ext not in (".csv", ".parquet"):
        err_ext = f"Unsupported storage file extension: {ext}"
        raise ValidationError(err_ext)

    return resolved_path


class DatabaseHelper:
    """Manages SQLite connection configurations, table schemas, and migrations."""

    def __init__(self, db_path: str = DB_FILE_PATH) -> None:
        """Initialize and ensure database file exists."""
        self.db_path = db_path
        db_parent = Path(self.db_path).parent
        db_parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection]:
        """Context manager providing a configured SQLite connection.

        Applies WAL journaling mode, foreign keys, and busy timeout rules.
        """
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failure: {e}")
            err_db = f"Database error: {e}"
            raise DataError(err_db) from e
        finally:
            conn.close()

    def init_database(self) -> None:
        """Ensure core tables and migrations are initialized."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sys_migrations (
                    migration_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    applied_at TEXT NOT NULL
                );
                """
            )

            cursor = conn.execute("SELECT MAX(version) as current FROM sys_migrations")
            row = cursor.fetchone()
            current_version = (
                row["current"] if row and row["current"] is not None else 0
            )

            self._apply_migrations(conn, current_version)

    def _apply_migrations(self, conn: sqlite3.Connection, current: int) -> None:
        """Apply incremental schema upgrades to the database."""
        if current < 1:
            logger.info("Applying migration version 1: Creating core tables.")
            # Table: data_cache
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_cache (
                    key TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    normalization_version TEXT NOT NULL,
                    raw_hash TEXT,
                    records_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """
            )
            # Table: data_jobs
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_jobs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL,
                    symbols TEXT NOT NULL,
                    timeframes TEXT NOT NULL,
                    data_kind TEXT NOT NULL,
                    storage_format TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    schedule TEXT,
                    enabled INTEGER DEFAULT 1,
                    state TEXT NOT NULL,
                    last_run_status TEXT,
                    last_checkpoint TEXT,
                    last_error TEXT,
                    next_run TEXT,
                    lease_owner TEXT,
                    lease_expires TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            # Table: feed_state
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feed_state (
                    feed_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    data_kind TEXT NOT NULL,
                    state TEXT NOT NULL,
                    last_heartbeat TEXT,
                    last_event TEXT,
                    buffer_depth INTEGER DEFAULT 0,
                    dropped_count INTEGER DEFAULT 0,
                    gap_count INTEGER DEFAULT 0,
                    reconnect_count INTEGER DEFAULT 0,
                    circuit_breaker_state TEXT,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            # Table: circuit_breakers
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS circuit_breakers (
                    source TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    last_state_change TEXT NOT NULL,
                    failures_count INTEGER DEFAULT 0,
                    cooldown_expires TEXT
                );
                """
            )

            conn.execute(
                "INSERT INTO sys_migrations VALUES (?, ?, ?);",
                ("mig_001_core", 1, datetime.now(UTC).isoformat()),
            )


db_helper = DatabaseHelper()


# --- Caching Operations ---
def generate_cache_key(
    source: str,
    symbol: str,
    timeframe: str,
    start_time: str,
    end_time: str,
    schema_version: str = DEFAULT_SCHEMA_VERSION,
    normalization_version: str = DEFAULT_NORMALIZATION_VERSION,
    raw_hash: str | None = None,
) -> str:
    """Generate a unique deterministic SHA256 cache key."""
    key_str = (
        f"{source}:{symbol}:{timeframe}:{start_time}:{end_time}:"
        f"{schema_version}:{normalization_version}:{raw_hash or ''}"
    )
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()


def get_cached_data(
    key: str, stale_data_behavior: str, request_id: str | None = None
) -> dict[str, Any] | None:
    """Retrieve data records from cache, evaluating TTL."""
    logger.debug(f"Querying cache for key: {key}", extra={"request_id": request_id})

    row = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM data_cache WHERE key = ?;", (key,))
            row = cursor.fetchone()
    except Exception as e:  # noqa: BLE001
        logger.error(
            f"Failed to retrieve cache records: {e}",
            extra={"request_id": request_id},
        )
        return None

    if not row:
        logger.debug("Cache miss.")
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])
    is_expired = datetime.now(UTC) > expires_at

    try:
        records = json.loads(row["records_json"])
    except json.JSONDecodeError as je:
        logger.error(f"Failed to decode cache JSON: {je}")
        return None

    meta = {
        "source": row["source"],
        "symbol": row["symbol"],
        "timeframe": row["timeframe"],
        "schema_version": row["schema_version"],
        "normalization_version": row["normalization_version"],
        "raw_hash": row["raw_hash"],
        "cached_at": row["created_at"],
        "stale": is_expired,
    }

    if is_expired:
        err_msg = (
            f"Cache expired for key {key}. stale_data_behavior={stale_data_behavior}"
        )
        logger.warning(err_msg)
        if stale_data_behavior in ("refresh_and_return", "fail"):
            return None
        meta["warning"] = "Data returned is stale from cache."

    return {"records": records, "metadata": meta}


def set_cached_data(
    key: str,
    source: str,
    symbol: str,
    timeframe: str,
    start_time: str,
    end_time: str,
    records: list[dict[str, Any]],
    ttl_seconds: int,
    schema_version: str = DEFAULT_SCHEMA_VERSION,
    normalization_version: str = DEFAULT_NORMALIZATION_VERSION,
    raw_hash: str | None = None,
    request_id: str | None = None,
) -> None:
    """Store data records into cache."""
    logger.debug(
        f"Storing data in cache: key={key}, TTL={ttl_seconds}s",
        extra={"request_id": request_id},
    )

    created_at = datetime.now(UTC)
    expires_at = created_at + timedelta(seconds=ttl_seconds)

    try:
        records_json = json.dumps(records)
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_cache (
                    key, source, symbol, timeframe, start_time, end_time,
                    schema_version, normalization_version, raw_hash,
                    records_json, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    key,
                    source,
                    symbol,
                    timeframe,
                    start_time,
                    end_time,
                    schema_version,
                    normalization_version,
                    raw_hash,
                    records_json,
                    created_at.isoformat(),
                    expires_at.isoformat(),
                ),
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(
            f"Cache write failed. Cache operation bypassed safely: {e}",
            extra={"request_id": request_id},
        )


def clear_data_cache(
    namespace: str,
    source_filter: str | None = None,
    symbol_filter: str | None = None,
    *,
    dry_run: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Inspect or delete cache records."""
    logger.info(
        f"clear_data_cache namespace={namespace}, dry_run={dry_run}",
        extra={"request_id": request_id},
    )

    if namespace != "data_cache":
        raise ValidationError("Only 'data_cache' namespace can be cleared.")

    query = "SELECT key, source, symbol FROM data_cache WHERE 1=1"
    params = []

    if source_filter:
        query += " AND source = ?"
        params.append(source_filter)
    if symbol_filter:
        query += " AND symbol = ?"
        params.append(symbol_filter)

    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            matched_keys = [row["key"] for row in rows]

            if not dry_run and matched_keys:
                ph = ",".join(["?"] * len(matched_keys))
                delete_query = f"DELETE FROM data_cache WHERE key IN ({ph})"  # noqa: S608
                conn.execute(delete_query, matched_keys)
                logger.info(f"Cleared {len(matched_keys)} cache entries.")

        return {
            "dry_run": dry_run,
            "cleared_count": 0 if dry_run else len(matched_keys),
            "matched_count": len(matched_keys),
            "matched_keys": matched_keys,
        }

    except Exception as e:
        logger.error(
            f"Failed cache clear operation: {e}",
            extra={"request_id": request_id},
        )
        err_msg = f"Failed to clear cache: {e}"
        raise ValidationError(err_msg) from e


# --- Local Dataset File I/O ---
def save_market_data(
    records: list[dict[str, Any]],
    path_str: str,
    format_str: str = "parquet",
    *,
    overwrite: bool = False,
    include_metadata: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Atomically writes normalized market data to file."""
    logger.info(
        f"Initiating save_market_data: path={path_str}, format={format_str}",
        extra={"request_id": request_id},
    )

    _ = include_metadata

    if not records:
        raise ValidationError("No data records supplied to save.")

    resolved_path = validate_storage_path(path_str)

    if resolved_path.exists() and not overwrite:
        err_exist = f"File already exists: {resolved_path}"
        logger.error(err_exist)
        raise ValidationError(err_exist)

    fmt = format_str.lower()
    if fmt not in ("csv", "parquet"):
        err_fmt = f"Format {format_str} unsupported."
        raise ValidationError(err_fmt)

    ensure_parent_dir(str(resolved_path))

    df = pd.DataFrame(records)

    temp_fd, temp_path_str = tempfile.mkstemp(
        dir=str(resolved_path.parent), suffix=".tmp"
    )
    os.close(temp_fd)
    temp_path = Path(temp_path_str)

    try:
        if fmt == "csv":
            df.to_csv(temp_path, index=False)
        else:
            df.to_parquet(temp_path, index=False)

        if resolved_path.exists():
            temp_path.replace(resolved_path)
        else:
            temp_path.rename(resolved_path)

        logger.info(f"Market data saved successfully to {resolved_path}")
        return {"path": str(resolved_path), "record_count": len(records)}
    except Exception as e:
        logger.error(f"Failed to write market data: {e}")
        if temp_path.exists():
            quarantine_path = Path(QUARANTINE_DIR)
            quarantine_path.mkdir(parents=True, exist_ok=True)
            quar_file = (
                quarantine_path
                / f"{resolved_path.name}_{datetime.now(UTC).timestamp()}.quarantine"
            )
            try:
                temp_path.rename(quar_file)
                logger.warning(f"Corrupt or partial file quarantined at: {quar_file}")
            except OSError as q_err:
                logger.error(f"Failed to quarantine file {temp_path}: {q_err}")
                with suppress(Exception):
                    temp_path.unlink()
        err_save = f"File system save operation failed: {e}"
        raise DataError(err_save) from e


def load_local_dataset(
    path_str: str, request_id: str | None = None
) -> list[dict[str, Any]]:
    """Loads CSV or Parquet file dataset from local roots."""
    logger.info(
        f"Initiating load_local_dataset: path={path_str}",
        extra={"request_id": request_id},
    )

    resolved_path = validate_storage_path(path_str)

    if not resolved_path.exists():
        err_msg = f"Local file not found: {resolved_path}"
        logger.error(err_msg)
        raise ValidationError(err_msg)

    ext = resolved_path.suffix.lower()
    if ext not in (".csv", ".parquet"):
        err_ext = f"Extension {ext} is not supported."
        raise ValidationError(err_ext)

    try:
        if ext == ".csv":
            with resolved_path.open(encoding="utf-8", errors="ignore") as f:
                first_line = f.readline()
            sep = "\t" if "\t" in first_line else ","
            df = pd.read_csv(resolved_path, sep=sep)
        else:
            df = pd.read_parquet(resolved_path)

        df = df.where(df.notna(), None)
        return df.to_dict(orient="records")  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Failed to load local dataset from {resolved_path}: {e}")
        err_load = f"Failed to load dataset: {e}"
        raise DataError(err_load) from e
