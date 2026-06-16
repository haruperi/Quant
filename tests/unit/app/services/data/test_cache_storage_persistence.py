"""Unit tests for cache, storage paths, database setup, and quarantine."""

from pathlib import Path

import pytest
from app.services.data.storage import (
    clear_data_cache,
    db_helper,
    generate_cache_key,
    get_cached_data,
    load_local_dataset,
    save_market_data,
    set_cached_data,
    validate_storage_path,
)
from app.utils.errors import ValidationError


def test_path_validation_locks() -> None:
    """Verify that path check prevents outside root writes and traversal."""
    # Approved root
    valid_path = "data/raw/EURUSD_M1.csv"
    validate_storage_path(valid_path)

    # Traversal check
    with pytest.raises(ValidationError):
        validate_storage_path("data/raw/../../secret.env")

    # Outside approved root check
    with pytest.raises(ValidationError):
        validate_storage_path("tmp/data.csv")

    # Unsupported extension
    with pytest.raises(ValidationError):
        validate_storage_path("data/raw/EURUSD_M1.txt")


def test_atomic_file_write_and_quarantine() -> None:
    """Test save_market_data atomic creation and loading."""
    records = [
        {"timestamp": "2026-06-01T00:00:00Z", "symbol": "EURUSD", "close": 1.1000}
    ]
    target_file = "data/raw/temp_test_write.csv"

    # Save
    res = save_market_data(records, target_file, "csv", overwrite=True)
    assert res["record_count"] == 1
    assert "path" in res

    # Load
    loaded = load_local_dataset(target_file)
    assert len(loaded) == 1
    assert loaded[0]["symbol"] == "EURUSD"

    # Cleanup
    file_path = Path(target_file)
    if file_path.exists():
        file_path.unlink()


def test_database_helper_connection() -> None:
    """Test SQLite connection provider and WAL journaling status."""
    with db_helper.get_connection() as conn:
        cursor = conn.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.lower() == "wal"


def test_cache_hits_and_misses() -> None:
    """Verify caching controls."""
    key = generate_cache_key("csv", "EURUSD", "M1", "2026-06-01", "2026-06-02")
    records = [
        {"timestamp": "2026-06-01T00:00:00Z", "symbol": "EURUSD", "close": 1.1000}
    ]

    # Initially cache miss
    cached = get_cached_data(key, "refresh_and_return")
    assert cached is None

    # Set cache with 10 seconds TTL
    set_cached_data(key, "csv", "EURUSD", "M1", "2026-06-01", "2026-06-02", records, 10)

    # Cache hit
    cached = get_cached_data(key, "refresh_and_return")
    assert cached is not None
    assert cached["records"][0]["symbol"] == "EURUSD"

    # Dry-run clearing
    clear_res = clear_data_cache("data_cache", dry_run=True)
    assert clear_res["matched_count"] > 0
    assert clear_res["cleared_count"] == 0

    # Delete clearing
    clear_res = clear_data_cache("data_cache", dry_run=False)
    assert clear_res["cleared_count"] > 0

    # Confirm cache is cleared
    cached_post = get_cached_data(key, "refresh_and_return")
    assert cached_post is None
