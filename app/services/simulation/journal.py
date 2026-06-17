# ruff: noqa
"""Journal persistence and audit trail for simulation.

Implements append-only JSONL streaming persistence with a SQLite transactional sidecar index,
calculating sequential audit hashes (previous hash -> current hash chain).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sqlite3
from datetime import UTC, datetime
from typing import Any

from app.utils.errors import SimPersistenceFailedError


class Journal:
    """Manages immutable backtest execution logs and transactional sidecar indexing."""

    def __init__(
        self,
        run_id: str,
        artifact_dir: str | None = None,
        use_sqlite_sidecar: bool = True,
        schema_version: str = "simulation.journal.v1",
    ) -> None:
        """Initialize simulation journal persistence."""
        self.run_id = run_id
        self.schema_version = schema_version
        self.sequence_number = 0
        self.last_hash = "0" * 64
        self.use_sqlite_sidecar = use_sqlite_sidecar

        self.jsonl_path = None
        self.sqlite_path = None
        self.db_conn = None

        if artifact_dir:
            try:
                os.makedirs(artifact_dir, exist_ok=True)
                self.jsonl_path = os.path.join(artifact_dir, f"journal_{run_id}.jsonl")
                self.sqlite_path = os.path.join(artifact_dir, f"journal_{run_id}.db")

                if self.use_sqlite_sidecar:
                    self.db_conn = sqlite3.connect(self.sqlite_path)
                    self._create_tables()
            except Exception as e:
                msg = f"Failed to initialize journal storage: {e}"
                raise SimPersistenceFailedError(msg)

    def _create_tables(self) -> None:
        """Create tables in the SQLite sidecar database."""
        if not self.db_conn:
            return
        cursor = self.db_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_events (
                sequence INTEGER PRIMARY KEY,
                run_id TEXT,
                timestamp TEXT,
                event_type TEXT,
                payload_json TEXT,
                previous_hash TEXT,
                event_hash TEXT
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_event_type ON journal_events(event_type)"
        )
        self.db_conn.commit()

    def append_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Append a new event, computing chain hashes, and persist to JSONL/SQLite."""
        from decimal import Decimal

        def decimal_to_float(obj: Any) -> Any:
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [decimal_to_float(x) for x in obj]
            if isinstance(obj, tuple):
                return tuple(decimal_to_float(x) for x in obj)
            return obj

        payload = decimal_to_float(payload)
        self.sequence_number += 1
        timestamp = datetime.now(UTC).isoformat()

        # Build basic event envelope for hashing
        envelope_to_hash = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "sequence_number": self.sequence_number,
            "timestamp": timestamp,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": self.last_hash,
        }

        # Calculate hash
        serialized = json.dumps(envelope_to_hash, sort_keys=True)
        event_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.last_hash = event_hash

        # Store hash on envelope
        envelope = envelope_to_hash.copy()
        envelope["event_hash"] = event_hash

        # Persist to JSONL file
        if self.jsonl_path:
            try:
                with open(self.jsonl_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(envelope) + "\n")
            except Exception as e:
                msg = f"JSONL journal append failed: {e}"
                raise SimPersistenceFailedError(msg)

        # Persist to SQLite
        if self.use_sqlite_sidecar and self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO journal_events (sequence, run_id, timestamp, event_type, payload_json, previous_hash, event_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.sequence_number,
                        self.run_id,
                        timestamp,
                        event_type,
                        json.dumps(payload),
                        envelope["previous_hash"],
                        event_hash,
                    ),
                )
                self.db_conn.commit()
            except Exception as e:
                msg = f"SQLite journal sidecar append failed: {e}"
                raise SimPersistenceFailedError(msg)

        return envelope

    def replay(self) -> list[dict[str, Any]]:
        """Replay all journaled events chronologically."""
        events = []
        if self.use_sqlite_sidecar and self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "SELECT sequence, timestamp, event_type, payload_json, previous_hash, event_hash FROM journal_events ORDER BY sequence"
                )
                for row in cursor.fetchall():
                    events.append(
                        {
                            "schema_version": self.schema_version,
                            "run_id": self.run_id,
                            "sequence_number": row[0],
                            "timestamp": row[1],
                            "event_type": row[2],
                            "payload": json.loads(row[3]),
                            "previous_hash": row[4],
                            "event_hash": row[5],
                        }
                    )
                return events
            except Exception:
                # Fallback to JSONL scan if SQLite query fails
                pass

        if self.jsonl_path and os.path.exists(self.jsonl_path):
            try:
                with open(self.jsonl_path, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            events.append(json.loads(line))
            except Exception as e:
                msg = f"Failed to replay JSONL journal: {e}"
                raise SimPersistenceFailedError(msg)

        return events

    def query_events_by_type(self, event_type: str) -> list[dict[str, Any]]:
        """Query specific types of events from SQLite or fallback JSONL scan."""
        events = []
        if self.use_sqlite_sidecar and self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "SELECT sequence, timestamp, event_type, payload_json, previous_hash, event_hash FROM journal_events WHERE event_type = ? ORDER BY sequence",
                    (event_type,),
                )
                for row in cursor.fetchall():
                    events.append(
                        {
                            "schema_version": self.schema_version,
                            "run_id": self.run_id,
                            "sequence_number": row[0],
                            "timestamp": row[1],
                            "event_type": row[2],
                            "payload": json.loads(row[3]),
                            "previous_hash": row[4],
                            "event_hash": row[5],
                        }
                    )
                return events
            except Exception:
                pass

        # Fallback JSONL scan
        all_events = self.replay()
        return [e for e in all_events if e["event_type"] == event_type]

    def close(self) -> None:
        """Close SQLite database connection cleanly."""
        if self.db_conn:
            with contextlib.suppress(Exception):
                self.db_conn.close()
            self.db_conn = None
