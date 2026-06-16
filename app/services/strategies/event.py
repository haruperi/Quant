# ruff: noqa: E501, EM101, EM102, TRY301, TRY300, BLE001, C901, PLR0912, PLR0915, RUF012, ANN401, DTZ003, RUF100
"""Event-driven and stateful strategy execution engine."""

from __future__ import annotations

import copy
import hashlib
import json
import time
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.services.strategies.protocols import (
    ReadOnlyExecutionStateSnapshot,
    StrategyExecutionContext,
    TradeIntent,
)
from app.utils.errors import (
    StrategyCheckpointIncompatibleError,
    StrategyCheckpointInvalidError,
    StrategyHardKilledError,
    StrategyTimeoutError,
    map_exception_to_strategy_error,
)
from app.utils.logger import logger


class StrategyStateCheckpoint(BaseModel):
    """Standardized representation of a stateful strategy checkpoint."""

    schema_version: str = "strategy.state_checkpoint.v1"
    strategy_id: str
    version: str
    configuration_hash: str
    state_schema_version: str = "1.0.0"
    checksum: str
    payload: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


def compute_hash(data: Any) -> str:
    """Generate a deterministic SHA256 hex digest for a JSON-serializable object."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def create_state_checkpoint(
    strategy_id: str,
    version: str,
    config: dict[str, Any],
    payload: dict[str, Any],
    state_schema_version: str = "1.0.0",
) -> StrategyStateCheckpoint:
    """Helper function to create a validated strategy state checkpoint with checksums."""
    config_hash = compute_hash(config)
    payload_hash = compute_hash(payload)

    # Calculate unique checksum of state content + config hash
    combined = (
        f"{strategy_id}:{version}:{config_hash}:{payload_hash}:{state_schema_version}"
    )
    checksum = hashlib.sha256(combined.encode("utf-8")).hexdigest()

    return StrategyStateCheckpoint(
        strategy_id=strategy_id,
        version=version,
        configuration_hash=config_hash,
        state_schema_version=state_schema_version,
        checksum=checksum,
        payload=payload,
        updated_at=datetime.utcnow(),
    )


def validate_and_restore_checkpoint(
    checkpoint: StrategyStateCheckpoint,
    strategy_id: str,
    version: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Verify strategy ID, version, config hash, state schema, and checksum consistency.

    Raises:
        StrategyCheckpointIncompatibleError: If metadata does not match target run.
        StrategyCheckpointInvalidError: If checksum verification fails.
    """
    if checkpoint.strategy_id != strategy_id:
        raise StrategyCheckpointIncompatibleError("Checkpoint strategy_id mismatch.")
    if checkpoint.version != version:
        raise StrategyCheckpointIncompatibleError(
            "Checkpoint strategy version mismatch."
        )

    config_hash = compute_hash(config)
    if checkpoint.configuration_hash != config_hash:
        raise StrategyCheckpointIncompatibleError(
            "Checkpoint configuration hash mismatch."
        )

    payload_hash = compute_hash(checkpoint.payload)
    combined = f"{strategy_id}:{version}:{config_hash}:{payload_hash}:{checkpoint.state_schema_version}"
    expected_checksum = hashlib.sha256(combined.encode("utf-8")).hexdigest()

    if checkpoint.checksum != expected_checksum:
        raise StrategyCheckpointInvalidError(
            "Checkpoint checksum verification failed (data corruption)."
        )

    return checkpoint.payload


def run_strategy_hook(
    strategy_instance: Any,
    hook_name: str,
    payload: dict[str, Any],
    read_only_state: ReadOnlyExecutionStateSnapshot | None,
    context: StrategyExecutionContext,
    config: dict[str, Any],
    timeout_seconds: float = 2.0,
) -> dict[str, Any]:
    """Execute a lifecycle hook on a stateful strategy instance.

    Ensures state updates are atomic per decision event, reverting changes if
    exceptions occur, and validates timeouts and hard kills.

    Returns:
        Standard envelope dictionary containing status, data (intents), and errors.
    """
    request_id = context.request_id
    correlation_id = context.correlation_id

    # Check for hard kill signal before run
    if getattr(context, "resource_budget_ref", None) == "HARD_KILL":
        raise StrategyHardKilledError(
            "Emergency hard kill signal received.",
            code="STRATEGY_HARD_KILLED",
        )

    # Capture state for atomic rollback (deep copy self.__dict__)
    # REQ-STRAT-094: Strategy-local state updates shall be atomic per decision event
    backup_dict = None
    try:
        backup_dict = copy.deepcopy(strategy_instance.__dict__)
    except Exception as exc:
        logger.warning(
            f"Failed to deepcopy strategy state for rollback: {exc}. Falling back to shallow copy.",
            extra={"strategy_id": strategy_instance.strategy_id},
        )
        backup_dict = copy.copy(strategy_instance.__dict__)

    start_time = time.perf_counter()
    try:
        hook_method = getattr(strategy_instance, hook_name, None)
        if hook_method is None:
            # If hook is not implemented but optional, ignore or return empty
            return {
                "status": "success",
                "message": f"Hook '{hook_name}' not implemented, skipped.",
                "data": {"trade_intents": [], "state_updates": {}},
                "error": None,
            }

        # Invoke hook method
        # Standardize argument counts depending on hook signature
        import inspect

        sig = inspect.signature(hook_method)
        params = list(sig.parameters.keys())

        # Construct arguments
        kwargs: dict[str, Any] = {}
        if "context" in params:
            kwargs["context"] = context
        if "config" in params:
            kwargs["config"] = config
        if "read_only_state" in params:
            kwargs["read_only_state"] = read_only_state
        if "payload" in params:
            kwargs["payload"] = payload
        elif "bar" in params:
            kwargs["bar"] = payload
        elif "tick" in params:
            kwargs["tick"] = payload
        elif "fill_event" in params:
            kwargs["fill_event"] = payload

        # Execute hook
        result = hook_method(**kwargs)
        duration = time.perf_counter() - start_time

        # REQ-STRAT-344: Timeout check
        if duration > timeout_seconds:
            raise StrategyTimeoutError(
                f"Strategy hook '{hook_name}' exceeded decision latency budget of {timeout_seconds} seconds."
            )

        # Ensure result is formatted correctly
        if not isinstance(result, dict):
            result = {"trade_intents": getattr(strategy_instance, "trade_intents", [])}

        trade_intents = result.get("trade_intents", [])
        # Coerce dicts to TradeIntent Pydantic models
        coerced_intents = []
        for ti in trade_intents:
            if isinstance(ti, dict):
                coerced_intents.append(TradeIntent(**ti))
            elif isinstance(ti, TradeIntent):
                coerced_intents.append(ti)

        # Log completion
        logger.info(
            f"Executed hook '{hook_name}' on strategy '{strategy_instance.strategy_id}'",
            extra={
                "strategy_id": strategy_instance.strategy_id,
                "hook_name": hook_name,
                "execution_ms": duration * 1000.0,
            },
        )

        return {
            "status": "success",
            "message": f"Hook '{hook_name}' executed successfully.",
            "data": {
                "trade_intents": coerced_intents,
                "diagnostics": {
                    "strategy_id": strategy_instance.strategy_id,
                    "strategy_version": strategy_instance.version,
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "decision_timestamp": context.decision_timestamp,
                    "status": "success",
                    "details": {},
                    "redaction_status": "not_required",
                },
                "state_updates": result.get("state_updates", {}),
            },
            "error": None,
            "metadata": {
                "request_id": request_id,
                "correlation_id": correlation_id,
                "execution_ms": duration * 1000.0,
            },
        }

    except Exception as exc:
        # Atomic rollback on exception
        if backup_dict is not None:
            strategy_instance.__dict__.clear()
            strategy_instance.__dict__.update(backup_dict)
            logger.info(
                f"Rolled back state changes for strategy '{strategy_instance.strategy_id}' "
                f"after hook '{hook_name}' failure."
            )

        mapped = map_exception_to_strategy_error(exc)
        logger.error(
            f"Stateful strategy hook '{hook_name}' failed: {exc}",
            extra={
                "strategy_id": getattr(strategy_instance, "strategy_id", "unknown"),
                "hook_name": hook_name,
                "error_code": mapped.code,
            },
        )

        return {
            "status": "error",
            "message": f"Hook execution failed: {exc}",
            "data": None,
            "error": {
                "code": mapped.code,
                "details": str(exc),
            },
            "metadata": {
                "request_id": request_id,
                "correlation_id": correlation_id,
            },
        }
