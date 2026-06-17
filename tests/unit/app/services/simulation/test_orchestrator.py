# ruff: noqa: E501
"""Unit tests for backtest orchestrator coordinating data, strategies, matching engines, and reports."""

from __future__ import annotations

import shutil
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from app.services.simulation.orchestrator import run_backtest
from app.utils.errors import SimulationError


@pytest.fixture(autouse=True)
def cleanup_artifacts() -> Generator[None]:
    """Fixture to clean up generated test artifacts after run."""
    yield
    art_dir = "artifacts/simulation_test"
    if Path(art_dir).exists():
        shutil.rmtree(art_dir)


def test_run_backtest_success() -> None:
    """Test full coordinates orchestrator run pipeline using synthetic mock data."""
    # Build request mapping
    req = {
        "strategy_ref": "trend_following",
        "strategy_config": {
            "symbol": "EURUSD",
            "fast_period": 10,
            "slow_period": 20,
            "filter_period": 50,
        },
        "symbols": ["EURUSD"],
        "timeframe": "M1",
        "start": "2026-06-01T00:00:00Z",
        "end": "2026-06-01T01:00:00Z",
        "initial_balance": 10000.0,
        "account_currency": "USD",
        "tick_model": "M1_TICKS",
        "spread_model": "FIXED_SPREAD",
        "slippage_model": "FIXED_SLIPPAGE",
        "commission_model": "PERCENT_NOTIONAL_COMMISSION",
        "swap_model": "NO_SWAP",
        "broker_profile_ref": "synthetic_demo_v1",
        "journal_persistence": {
            "artifact_dir": "artifacts/simulation_test",
            "use_sqlite_sidecar": True,
        },
    }

    res = run_backtest(req)

    assert res["status"] == "success"
    data = res["data"]
    assert isinstance(data, dict)
    assert data["status"] == "success"
    assert "result" in data
    result = data["result"]
    assert isinstance(result, dict)
    assert "metrics" in result

    # Verify that JSON/Markdown reports and journal files were written to disk
    art = data["artifacts"]
    assert isinstance(art, dict)
    assert Path(art["report_md"]).exists()
    assert Path(art["report_json"]).exists()
    assert Path(art["journal_jsonl"]).exists()


def test_calculate_sized_volume() -> None:
    """Test calculate_sized_volume position sizing configurations and exceptions."""
    from decimal import Decimal

    from app.services.simulation.orchestrator import calculate_sized_volume
    from app.services.simulation.validation.schema import SymbolSpec

    spec = SymbolSpec(
        symbol="EURUSD",
        point=Decimal("0.00001"),
        tick_size=Decimal("0.00001"),
        tick_value=Decimal("1.0"),
        contract_size=Decimal("100000.0"),
        volume_min=Decimal("0.01"),
        volume_max=Decimal("100.0"),
        volume_step=Decimal("0.01"),
    )

    # FIXED_LOT mode
    vol_fixed = calculate_sized_volume(
        "FIXED_LOT", Decimal("10000.0"), Decimal("1.10"), None, spec, Decimal("0.5")
    )
    assert vol_fixed == Decimal("0.5")

    # FIXED_RISK mode normal
    vol_risk = calculate_sized_volume(
        "FIXED_RISK",
        Decimal("10000.0"),
        Decimal("1.10000"),
        Decimal("1.09000"),
        spec,
        None,
    )
    # Risk = 100 USD (1% of 10000). Distance = 0.01000. Contract size = 100000.
    # Expected volume = 100 / (0.01 * 100000) = 0.1
    assert vol_risk == Decimal("0.1")

    # FIXED_RISK missing SL
    with pytest.raises(SimulationError, match="Stop loss is required"):
        calculate_sized_volume(
            "FIXED_RISK", Decimal("10000.0"), Decimal("1.10"), None, spec
        )

    # FIXED_RISK invalid distance
    with pytest.raises(
        SimulationError, match="Stop distance must be greater than zero"
    ):
        calculate_sized_volume(
            "FIXED_RISK", Decimal("10000.0"), Decimal("1.10"), Decimal("1.10"), spec
        )


def test_run_backtest_missing_symbols() -> None:
    """Test run_backtest behavior when symbol list is empty."""
    req = {
        "strategy_ref": "trend_following",
        "strategy_config": {},
        "symbols": [],
        "timeframe": "M1",
        "start": "2026-06-01T00:00:00Z",
        "end": "2026-06-01T01:00:00Z",
    }
    res = run_backtest(req)
    assert res["status"] == "error"
    error = res["error"]
    assert error is not None
    assert error["code"] == "SIM_MISSING_SYMBOL"


def test_run_backtest_strategy_error(mocker: Any) -> None:
    """Test run_backtest when strategy signal generation returns an error."""
    # Mock run_vectorized_strategy_signals to return an error response
    mocker.patch(
        "app.services.simulation.orchestrator.run_vectorized_strategy_signals",
        return_value={
            "status": "error",
            "error": {
                "code": "SIM_INTERNAL_ERROR",
                "details": "Simulated strategy failure",
            },
        },
    )
    req = {
        "strategy_ref": "trend_following",
        "strategy_config": {},
        "symbols": ["EURUSD"],
        "timeframe": "M1",
        "start": "2026-06-01T00:00:00Z",
        "end": "2026-06-01T01:00:00Z",
        "broker_profile_ref": "synthetic_demo_v1",
    }
    res = run_backtest(req)
    assert res["status"] == "error"
    error = res["error"]
    assert error is not None
    assert error["code"] == "SIM_INTERNAL_ERROR"


def test_journal_persistence_and_replay() -> None:
    """Test Journal operations, SQLite sidecar indexing, queries, fallback scan, and exceptions."""
    from decimal import Decimal

    from app.services.simulation.journal import Journal

    art_dir = "artifacts/journal_unit_test"
    run_id = "test_run_123"

    # Clean previous run if exists
    if Path(art_dir).exists():
        shutil.rmtree(art_dir)

    # Initialize journal with sidecar
    journal = Journal(run_id=run_id, artifact_dir=art_dir, use_sqlite_sidecar=True)

    # Append test events (one with Decimal to test conversion)
    event1 = journal.append_event(
        "order_placed", {"price": Decimal("1.10000"), "volume": Decimal("0.5")}
    )
    event2 = journal.append_event(
        "position_closed", {"price": 1.10050, "pnl": Decimal("25.00")}
    )

    assert event1["sequence_number"] == 1
    assert event1["previous_hash"] == "0" * 64
    assert event1["event_hash"] != "0" * 64
    assert isinstance(event1["payload"]["price"], float)
    assert event2["previous_hash"] == event1["event_hash"]

    # Replay events
    events = journal.replay()
    assert len(events) == 2
    assert events[0]["event_type"] == "order_placed"
    assert events[1]["event_type"] == "position_closed"

    # Query events by type
    orders = journal.query_events_by_type("order_placed")
    assert len(orders) == 1
    assert orders[0]["sequence_number"] == 1

    # Close the journal
    journal.close()

    # Replay fallback from JSONL (when SQLite db is not connected/failed)
    # We create a new journal pointing to same directory with SQLite disabled
    journal_jsonl = Journal(
        run_id=run_id, artifact_dir=art_dir, use_sqlite_sidecar=False
    )
    events_jsonl = journal_jsonl.replay()
    assert len(events_jsonl) == 2

    # Query by type fallback JSONL
    orders_jsonl = journal_jsonl.query_events_by_type("order_placed")
    assert len(orders_jsonl) == 1

    # Cleanup test files
    if Path(art_dir).exists():
        shutil.rmtree(art_dir)


def test_journal_initialization_exceptions() -> None:
    """Test Journal raises SimPersistenceFailedError on connection/path errors."""
    from app.services.simulation.journal import Journal
    from app.utils.errors import SimPersistenceFailedError

    # Passing invalid filesystem characters in path to force database initialization error
    with pytest.raises(SimPersistenceFailedError):
        Journal(
            run_id="test", artifact_dir="/invalid_dir/\\:\x00", use_sqlite_sidecar=True
        )
