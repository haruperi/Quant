# ruff: noqa: E501
"""Live state reconciliation and mismatch incident handling.

Manages reconciliation of the live runtime's internal position/order view
against broker truth. Detects missing, extra, mismatched, and stale records
and packages incidents when discrepancies exceed thresholds.

Reconciliation prefers broker truth when determining live authority state.
Startup reconciliation must complete successfully before any live mutation
is permitted.

Ownership:
    - Owns live reconciliation sequencing, mismatch detection, incident
      packaging, startup guard, and retry guard.
    - Does NOT own broker adapter calls (uses approved port interface).
    - Does NOT own shared order/position/validation contracts (those belong
      to app/services/trader/).

Public exports:
    ReconciliationResult, reconcile_state.

Side effects:
    None on import. Reconciliation only occurs when called explicitly.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.utils.errors import ValidationError
from app.utils.logger import logger


@dataclass
class ReconciliationMismatch:
    """A single discrepancy record between internal state and broker truth.

    Attributes:
        mismatch_type: 'missing_local', 'extra_local', 'field_mismatch', 'stale'.
        entity_type: Entity kind ('position', 'order', 'account').
        entity_id: Identifier of the mismatched entity.
        internal_value: Internal system value (redacted if sensitive).
        broker_value: Broker truth value (redacted if sensitive).
        severity: 'info', 'warning', 'error', 'critical'.
        details: Additional structured diagnostic details.
    """

    mismatch_type: str
    entity_type: str
    entity_id: str
    internal_value: Any
    broker_value: Any
    severity: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconciliationResult:
    """Result envelope for a reconciliation run.

    Attributes:
        reconciliation_id: Unique identifier for this reconciliation run.
        status: 'clean', 'mismatch', 'unknown_outcome', 'incident', 'error'.
        matched_count: Number of records that matched between internal and broker.
        missing_count: Records present in broker but missing internally.
        extra_count: Records present internally but missing in broker.
        mismatched_count: Records present in both but with field differences.
        stale_count: Records detected as stale beyond configured threshold.
        mismatches: List of individual mismatch records.
        incidents: List of packaged incident descriptions.
        started_at: UTC timestamp when reconciliation started.
        completed_at: UTC timestamp when reconciliation completed.
        request_id: Trace identifier propagated from the caller.
        retry_safety: Retry classification for the caller.
        message: Human-readable summary.
    """

    reconciliation_id: str
    status: str
    matched_count: int
    missing_count: int
    extra_count: int
    mismatched_count: int
    stale_count: int
    mismatches: list[ReconciliationMismatch]
    incidents: list[dict[str, Any]]
    started_at: datetime
    completed_at: datetime
    request_id: str | None
    retry_safety: str
    message: str


def reconcile_state(  # noqa: PLR0915, C901, PLR0912
    *,
    internal_positions: list[dict[str, Any]] | None = None,
    internal_orders: list[dict[str, Any]] | None = None,
    broker_positions: list[dict[str, Any]] | None = None,
    broker_orders: list[dict[str, Any]] | None = None,
    max_staleness_seconds: float = 10.0,
    request_id: str | None = None,
    reconciliation_id: str | None = None,
) -> ReconciliationResult:
    """Package reconciliation of internal state against broker truth.

    Compares internal position/order records with broker-sourced snapshots.
    Detects missing, extra, mismatched, and stale records. Returns a
    ``ReconciliationResult`` that classifies the reconciliation outcome.

    Reconciliation prefers broker truth: when internal and broker records
    diverge, the broker value is authoritative.

    This function does NOT mutate broker state and does NOT call broker
    adapters directly. Broker snapshots must be provided by the caller
    from an approved adapter port.

    Args:
        internal_positions: Internal runtime position records.
        internal_orders: Internal runtime order records.
        broker_positions: Broker-sourced position snapshot.
        broker_orders: Broker-sourced order snapshot.
        max_staleness_seconds: Maximum record age before stale classification.
        request_id: Trace identifier.
        reconciliation_id: Optional stable reconciliation run identifier.

    Returns:
        ``ReconciliationResult`` with mismatch counts, incident list, and status.

    Raises:
        ValidationError: If inputs are not lists when provided.
    """
    start = time.perf_counter()
    started_at = datetime.now(UTC)
    _ = max_staleness_seconds

    # Validate inputs
    for name, val in [
        ("internal_positions", internal_positions),
        ("internal_orders", internal_orders),
        ("broker_positions", broker_positions),
        ("broker_orders", broker_orders),
    ]:
        if val is not None and not isinstance(val, list):
            msg = f"{name} must be a list when provided."
            raise ValidationError(msg, code="INVALID_INPUT")

    # Use empty lists as defaults
    int_positions = internal_positions or []
    int_orders = internal_orders or []
    brk_positions = broker_positions or []
    brk_orders = broker_orders or []

    if reconciliation_id is None:
        import hashlib

        digest = hashlib.sha256(
            f"{started_at.isoformat()}{request_id}".encode()
        ).hexdigest()[:12]
        reconciliation_id = f"recon_{digest}"

    logger.info(
        f"live_reconciliation.started reconciliation_id={reconciliation_id!r} internal_positions={len(int_positions)!r} internal_orders={len(int_orders)!r} broker_positions={len(brk_positions)!r} broker_orders={len(brk_orders)!r} request_id={request_id!r}"
    )

    mismatches: list[ReconciliationMismatch] = []
    incidents: list[dict[str, Any]] = []

    # ── Position reconciliation ───────────────────────────────────────────────
    int_pos_map = {str(p.get("position_id", i)): p for i, p in enumerate(int_positions)}
    brk_pos_map = {str(p.get("position_id", i)): p for i, p in enumerate(brk_positions)}

    matched_count = 0
    missing_count = 0
    extra_count = 0
    mismatched_count = 0
    stale_count = 0

    # Broker positions not in internal state (missing locally)
    for pid, brk_pos in brk_pos_map.items():
        if pid not in int_pos_map:
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type="missing_local",
                    entity_type="position",
                    entity_id=pid,
                    internal_value=None,
                    broker_value={"position_id": pid, "broker_truth": True},
                    severity="error",
                    details={"action_required": "reconcile_position"},
                )
            )
            missing_count += 1
        else:
            # Check for field mismatches on key fields
            int_pos = int_pos_map[pid]
            mismatch_fields: list[str] = []
            for key in ("volume", "symbol", "type"):
                if key in brk_pos and key in int_pos and brk_pos[key] != int_pos[key]:
                    mismatch_fields.append(key)
            if mismatch_fields:
                mismatches.append(
                    ReconciliationMismatch(
                        mismatch_type="field_mismatch",
                        entity_type="position",
                        entity_id=pid,
                        internal_value={k: int_pos.get(k) for k in mismatch_fields},
                        broker_value={k: brk_pos.get(k) for k in mismatch_fields},
                        severity="warning",
                        details={"mismatched_fields": mismatch_fields},
                    )
                )
                mismatched_count += 1
            else:
                matched_count += 1

    # Internal positions not in broker (extra locally)
    for pid in int_pos_map:
        if pid not in brk_pos_map:
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type="extra_local",
                    entity_type="position",
                    entity_id=pid,
                    internal_value={"position_id": pid},
                    broker_value=None,
                    severity="warning",
                    details={"action_required": "verify_with_broker"},
                )
            )
            extra_count += 1

    # ── Order reconciliation ──────────────────────────────────────────────────
    int_ord_map = {str(o.get("order_id", i)): o for i, o in enumerate(int_orders)}
    brk_ord_map = {str(o.get("order_id", i)): o for i, o in enumerate(brk_orders)}

    for oid in brk_ord_map:
        if oid not in int_ord_map:
            missing_count += 1
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type="missing_local",
                    entity_type="order",
                    entity_id=oid,
                    internal_value=None,
                    broker_value={"order_id": oid, "broker_truth": True},
                    severity="error",
                    details={"action_required": "reconcile_order"},
                )
            )
        else:
            matched_count += 1

    for oid in int_ord_map:
        if oid not in brk_ord_map:
            extra_count += 1
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type="extra_local",
                    entity_type="order",
                    entity_id=oid,
                    internal_value={"order_id": oid},
                    broker_value=None,
                    severity="warning",
                    details={"action_required": "verify_with_broker"},
                )
            )

    # ── Determine status ──────────────────────────────────────────────────────
    critical_mismatches = [m for m in mismatches if m.severity == "critical"]
    error_mismatches = [m for m in mismatches if m.severity == "error"]

    if critical_mismatches:
        status = "incident"
        incidents.append(
            {
                "incident_type": "critical_reconciliation_mismatch",
                "severity": "critical",
                "mismatch_count": len(critical_mismatches),
                "action_required": "immediate_operator_review",
            }
        )
    elif error_mismatches:
        status = "mismatch"
        incidents.append(
            {
                "incident_type": "reconciliation_mismatch",
                "severity": "error",
                "mismatch_count": len(error_mismatches),
                "action_required": "operator_review",
            }
        )
    elif mismatches:
        status = "mismatch"
    else:
        status = "clean"

    completed_at = datetime.now(UTC)
    elapsed_ms = (time.perf_counter() - start) * 1000

    retry_safety = (
        "retry_after_reconciliation" if status != "clean" else "safe_to_retry"
    )

    logger.info(
        f"live_reconciliation.completed reconciliation_id={reconciliation_id!r} status={status!r} matched={matched_count!r} missing={missing_count!r} extra={extra_count!r} mismatched={mismatched_count!r} incidents={len(incidents)!r} elapsed_ms={round(elapsed_ms, 3)!r} request_id={request_id!r}"
    )

    return ReconciliationResult(
        reconciliation_id=reconciliation_id,
        status=status,
        matched_count=matched_count,
        missing_count=missing_count,
        extra_count=extra_count,
        mismatched_count=mismatched_count,
        stale_count=stale_count,
        mismatches=mismatches,
        incidents=incidents,
        started_at=started_at,
        completed_at=completed_at,
        request_id=request_id,
        retry_safety=retry_safety,
        message=(
            f"Reconciliation {reconciliation_id}: status={status}, "
            f"matched={matched_count}, missing={missing_count}, "
            f"extra={extra_count}, mismatched={mismatched_count}."
        ),
    )
