"""Deterministic simulator journal persistence.

Exports append-only journal records, in-memory journals, and JSONL journal
writers with manifest generation. JSONL writers write only when explicitly
constructed by a caller.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.utils.errors import SimPersistenceFailedError, ValidationError
from app.utils.normalization import utc_now
from app.utils.standard import canonical_json, stable_identifier


@dataclass(frozen=True, slots=True)
class JournalRecord:
    """Single deterministic journal event.

    Args:
        sequence: Monotonic sequence number.
        event_type: Event category.
        payload: Redacted event payload.
        previous_hash: Previous record hash.
        record_hash: Current record hash.
        created_at: UTC timestamp.
    """

    sequence: int
    event_type: str
    payload: dict[str, Any]
    previous_hash: str
    record_hash: str
    created_at: str


@dataclass(frozen=True, slots=True)
class JournalManifest:
    """Journal manifest with replay verification metadata.

    Args:
        run_id: Simulator run id.
        config_hash: Configuration hash.
        data_manifest_hash: Data manifest hash.
        engine_version: Engine version.
        schema_version: Journal schema version.
        artifact_checksums: Artifact checksum map.
        retention_tier: Retention tier label.
        last_sequence: Last committed sequence.
        last_record_hash: Last committed record hash.
    """

    run_id: str
    config_hash: str
    data_manifest_hash: str
    engine_version: str
    schema_version: str
    artifact_checksums: dict[str, str]
    retention_tier: str
    last_sequence: int
    last_record_hash: str


class DeterministicJournal:
    """Append-only hash-chain journal.

    Args:
        run_id: Simulator run id.
        config_hash: Configuration hash.
        data_manifest_hash: Data manifest hash.
        engine_version: Engine version.
        retention_tier: Retention tier label.

    Raises:
        ValidationError: If required identifiers are missing.
    """

    def __init__(
        self,
        *,
        run_id: str,
        config_hash: str,
        data_manifest_hash: str,
        engine_version: str,
        retention_tier: str = "local_research",
    ) -> None:
        """Initialize an empty deterministic journal."""
        for name, value in {
            "run_id": run_id,
            "config_hash": config_hash,
            "data_manifest_hash": data_manifest_hash,
            "engine_version": engine_version,
        }.items():
            if not value.strip():
                message = f"{name} must be non-empty."
                raise ValidationError(message)
        self.run_id = run_id
        self.config_hash = config_hash
        self.data_manifest_hash = data_manifest_hash
        self.engine_version = engine_version
        self.retention_tier = retention_tier
        self._records: list[JournalRecord] = []

    @property
    def records(self) -> tuple[JournalRecord, ...]:
        """Return immutable journal records.

        Returns:
            tuple[JournalRecord, ...]: Journal records.
        """
        return tuple(self._records)

    def append(self, event_type: str, payload: dict[str, Any]) -> JournalRecord:
        """Append a deterministic journal event.

        Args:
            event_type: Non-empty event type.
            payload: JSON-compatible redacted payload.

        Returns:
            JournalRecord: Appended record.

        Raises:
            ValidationError: If event type or payload are invalid.
        """
        if not event_type.strip():
            raise ValidationError("event_type must be non-empty.")
        previous_hash = self._records[-1].record_hash if self._records else "GENESIS"
        sequence = len(self._records) + 1
        created_at = utc_now().isoformat()
        hash_payload = {
            "sequence": sequence,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
            "run_id": self.run_id,
        }
        record_hash = stable_identifier(hash_payload, prefix="id")
        record = JournalRecord(
            sequence=sequence,
            event_type=event_type,
            payload=payload,
            previous_hash=previous_hash,
            record_hash=record_hash,
            created_at=created_at,
        )
        self._records.append(record)
        return record

    async def append_async(
        self, event_type: str, payload: dict[str, Any]
    ) -> JournalRecord:
        """Append through an asynchronous boundary.

        Args:
            event_type: Non-empty event type.
            payload: JSON-compatible redacted payload.

        Returns:
            JournalRecord: Appended record.

        Raises:
            ValidationError: If event type or payload are invalid.
        """
        return self.append(event_type, payload)

    def manifest(self) -> JournalManifest:
        """Build a journal manifest.

        Returns:
            JournalManifest: Manifest for replay and artifact verification.
        """
        last = self._records[-1] if self._records else None
        return JournalManifest(
            run_id=self.run_id,
            config_hash=self.config_hash,
            data_manifest_hash=self.data_manifest_hash,
            engine_version=self.engine_version,
            schema_version="1.0.0",
            artifact_checksums={},
            retention_tier=self.retention_tier,
            last_sequence=last.sequence if last else 0,
            last_record_hash=last.record_hash if last else "GENESIS",
        )

    def replay_payload(self) -> list[dict[str, Any]]:
        """Return JSON-compatible records for replay.

        Returns:
            list[dict[str, Any]]: Serialized journal records.
        """
        return [asdict(record) for record in self._records]


class JsonlJournal(DeterministicJournal):
    """Append-only JSONL journal persisted to an explicit artifact directory.

    Args:
        artifact_root: Directory where journal files are written.
        run_id: Simulator run id.
        config_hash: Configuration hash.
        data_manifest_hash: Data manifest hash.
        engine_version: Engine version.
        retention_tier: Retention tier label.

    Raises:
        SimPersistenceFailedError: If the artifact path cannot be initialized.
    """

    def __init__(
        self,
        *,
        artifact_root: Path,
        run_id: str,
        config_hash: str,
        data_manifest_hash: str,
        engine_version: str,
        retention_tier: str = "local_research",
    ) -> None:
        """Initialize a JSONL journal."""
        super().__init__(
            run_id=run_id,
            config_hash=config_hash,
            data_manifest_hash=data_manifest_hash,
            engine_version=engine_version,
            retention_tier=retention_tier,
        )
        try:
            self.artifact_root = artifact_root.resolve()
            self.artifact_root.mkdir(parents=True, exist_ok=True)
            self.journal_path = self.artifact_root / "journal.jsonl"
            self.manifest_path = self.artifact_root / "journal_manifest.json"
        except OSError as exc:
            message = f"Failed to initialize journal storage: {exc}"
            raise SimPersistenceFailedError(
                message,
                code="SIM_PERSISTENCE_FAILED",
            ) from exc

    def append(self, event_type: str, payload: dict[str, Any]) -> JournalRecord:
        """Append and persist a JSONL journal event.

        Args:
            event_type: Non-empty event type.
            payload: JSON-compatible redacted payload.

        Returns:
            JournalRecord: Appended record.

        Raises:
            SimPersistenceFailedError: If the write fails.
        """
        record = super().append(event_type, payload)
        try:
            with self.journal_path.open("a", encoding="utf-8") as handle:
                handle.write(canonical_json(asdict(record)) + "\n")
        except OSError as exc:
            message = f"Failed to append simulator journal: {exc}"
            raise SimPersistenceFailedError(
                message,
                code="SIM_PERSISTENCE_FAILED",
            ) from exc
        return record

    def write_manifest(self) -> JournalManifest:
        """Write and return the current journal manifest.

        Returns:
            JournalManifest: Persisted manifest.

        Raises:
            SimPersistenceFailedError: If the manifest write fails.
        """
        manifest = self.manifest()
        try:
            self.manifest_path.write_text(
                json.dumps(asdict(manifest), indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as exc:
            message = f"Failed to write simulator journal manifest: {exc}"
            raise SimPersistenceFailedError(
                message,
                code="SIM_PERSISTENCE_FAILED",
            ) from exc
        return manifest
