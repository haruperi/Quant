"""Unit tests for simulator 08B replay clock and data feed."""

import hashlib
import json
from typing import Any, cast

import pytest
from app.services.simulator import ChronologicalDataFeed, SimulatorTick
from app.services.simulator.validation.quality import (
    align_record_timezones,
    apply_partial_data_policy,
    detect_data_gaps,
)
from app.utils.errors import SimulationError
from pytest_mock import MockerFixture


def test_align_record_timezones() -> None:
    """Verify raw timestamps are normalized to UTC ISO strings."""
    records = [
        {"timestamp": "2026-01-01T05:00:00+05:00", "price": 1.1},
        {"timestamp": "2026-01-01T00:00:00Z", "price": 1.2},
    ]
    aligned = align_record_timezones(records)
    assert aligned[0]["timestamp"] == "2026-01-01T00:00:00+00:00"
    assert aligned[1]["timestamp"] == "2026-01-01T00:00:00+00:00"


def test_detect_data_gaps() -> None:
    """Verify gap detection works and weekend gaps are ignored."""
    # 1. Active hour gap (> 1 hour)
    records = [
        {"timestamp": "2026-01-01T00:00:00Z"},
        {"timestamp": "2026-01-01T02:00:01Z"},
    ]
    issues = detect_data_gaps(records, max_gap_seconds=3600.0)
    assert len(issues) == 1
    assert issues[0]["code"] == "SIM_GAP_HANDLING_REJECTED"

    # 2. Weekend gap (Friday night to Sunday night)
    # 2026-01-02 is Friday, 2026-01-05 is Monday
    records_weekend = [
        {"timestamp": "2026-01-02T22:00:00Z"},
        {"timestamp": "2026-01-05T00:00:00Z"},
    ]
    issues_weekend = detect_data_gaps(records_weekend, max_gap_seconds=3600.0)
    assert len(issues_weekend) == 0

    # 3. Small gap (< 1 hour)
    records_small = [
        {"timestamp": "2026-01-01T00:00:00Z"},
        {"timestamp": "2026-01-01T00:30:00Z"},
    ]
    issues_small = detect_data_gaps(records_small, max_gap_seconds=3600.0)
    assert len(issues_small) == 0


def test_apply_partial_data_policy_fail_fast() -> None:
    """Verify fail_fast raises SimulationError on missing symbol-days."""
    symbol_records = {
        "EURUSD": [
            {"timestamp": "2026-01-01T12:00:00Z"},
            {"timestamp": "2026-01-02T12:00:00Z"},
        ],
        "GBPUSD": [
            {"timestamp": "2026-01-01T12:00:00Z"},
        ],
    }
    with pytest.raises(SimulationError) as exc_info:
        apply_partial_data_policy(symbol_records, policy="fail_fast")
    assert exc_info.value.code == "SIM_DATA_PARTIAL"


def test_apply_partial_data_policy_quarantine() -> None:
    """Verify quarantine filters out missing trading days for all symbols."""
    symbol_records = {
        "EURUSD": [
            {"timestamp": "2026-01-01T12:00:00Z"},
            {"timestamp": "2026-01-02T12:00:00Z"},
        ],
        "GBPUSD": [
            {"timestamp": "2026-01-01T12:00:00Z"},
        ],
    }
    filtered = apply_partial_data_policy(symbol_records, policy="quarantine")
    # 2026-01-02 is missing for GBPUSD, so it should be
    # quarantined (removed) for EURUSD too.
    assert len(filtered["EURUSD"]) == 1
    assert filtered["EURUSD"][0]["timestamp"] == "2026-01-01T12:00:00Z"
    assert len(filtered["GBPUSD"]) == 1


def test_apply_partial_data_policy_allow() -> None:
    """Verify allow policy leaves records unchanged."""
    symbol_records = {
        "EURUSD": [
            {"timestamp": "2026-01-01T12:00:00Z"},
            {"timestamp": "2026-01-02T12:00:00Z"},
        ],
        "GBPUSD": [
            {"timestamp": "2026-01-01T12:00:00Z"},
        ],
    }
    result = apply_partial_data_policy(symbol_records, policy="allow")
    assert len(result["EURUSD"]) == 2
    assert len(result["GBPUSD"]) == 1


def test_chronological_data_feed_merging(mocker: MockerFixture) -> None:
    """Verify multi-symbol ticks are merged in strictly chronological order."""
    eur_ticks = [
        {"timestamp": "2026-01-01T00:00:00Z", "bid": 1.1000, "ask": 1.1002},
        {"timestamp": "2026-01-01T00:00:02Z", "bid": 1.1001, "ask": 1.1003},
    ]
    gbp_ticks = [
        {"timestamp": "2026-01-01T00:00:01Z", "bid": 1.4000, "ask": 1.4002},
        {"timestamp": "2026-01-01T00:00:03Z", "bid": 1.4001, "ask": 1.4003},
    ]

    def mock_get_data(symbol: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        if symbol == "EURUSD":
            return eur_ticks
        return gbp_ticks

    mocker.patch("app.services.simulator.data_feed.get_data", side_effect=mock_get_data)

    feed = ChronologicalDataFeed(
        symbols=("EURUSD", "GBPUSD"),
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        data_kind="ticks",
        partial_data_policy="allow",
    )

    replayed = cast(list[SimulatorTick], list(feed))
    assert len(replayed) == 4
    # Merged order: EUR0, GBP0, EUR1, GBP1
    assert isinstance(replayed[0], SimulatorTick)
    assert replayed[0].symbol == "EURUSD"
    assert replayed[1].symbol == "GBPUSD"
    assert replayed[2].symbol == "EURUSD"
    assert replayed[3].symbol == "GBPUSD"

    # Confirm timestamps are strictly increasing
    assert replayed[0].timestamp < replayed[1].timestamp
    assert replayed[1].timestamp < replayed[2].timestamp
    assert replayed[2].timestamp < replayed[3].timestamp


def test_chronological_data_feed_caching_and_checksum(mocker: MockerFixture) -> None:
    """Verify cache hits, manifest checksum verification, and cache saving."""
    eur_ticks = [
        {"timestamp": "2026-01-01T00:00:00Z", "bid": 1.1000, "ask": 1.1002},
    ]
    expected_checksum = hashlib.sha256(
        json.dumps(eur_ticks).encode("utf-8")
    ).hexdigest()

    mock_get_cached = mocker.patch(
        "app.services.simulator.data_feed.get_cached_data",
        return_value={"records": eur_ticks},
    )
    mock_set_cached = mocker.patch("app.services.simulator.data_feed.set_cached_data")
    mock_get_data = mocker.patch("app.services.simulator.data_feed.get_data")

    # 1. Valid checksum cache hit
    feed_hit = ChronologicalDataFeed(
        symbols=("EURUSD",),
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        data_kind="ticks",
        data_manifest_hash="test_manifest_hash",
        manifest_checksums={"EURUSD": expected_checksum},
    )
    replayed = list(feed_hit)
    assert len(replayed) == 1
    assert mock_get_cached.call_count == 1
    assert mock_get_data.call_count == 0

    # 2. Checksum mismatch causes reload
    feed_mismatch = ChronologicalDataFeed(
        symbols=("EURUSD",),
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        data_kind="ticks",
        data_manifest_hash="test_manifest_hash",
        manifest_checksums={"EURUSD": "invalid_checksum"},
    )
    mock_get_data.return_value = eur_ticks
    replayed_mismatch = list(feed_mismatch)
    assert len(replayed_mismatch) == 1
    assert mock_get_data.call_count == 1
    assert mock_set_cached.call_count == 1
