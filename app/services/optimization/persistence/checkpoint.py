"""Optimization checkpointing and atomic persistence.

Provides file-backed checkpoint saves and loads with atomic rename semantics,
corruption recovery, and path traversal protection.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, cast

from app.services.optimization.helpers import OptimizationExecutionError

# Error Code Constants
OPT_ATOMIC_WRITE_FAILED = "OPT_ATOMIC_WRITE_FAILED"
OPT_CHECKPOINT_CORRUPTED = "OPT_CHECKPOINT_CORRUPTED"
OPT_INTRADAY_RULE_DATA_UNAVAILABLE = "OPT_INTRADAY_RULE_DATA_UNAVAILABLE"
OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED = (
    "OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED"
)
OPT_TRIAL_COUNT_METHOD_UNSUPPORTED = "OPT_TRIAL_COUNT_METHOD_UNSUPPORTED"
OPT_PRUNED_BY_HARD_GATE = "OPT_PRUNED_BY_HARD_GATE"
OPT_PBO_THRESHOLD_FAILED = "OPT_PBO_THRESHOLD_FAILED"
OPT_NOISY_OBJECTIVE_NOT_ALLOWED = "OPT_NOISY_OBJECTIVE_NOT_ALLOWED"
STOCHASTIC_REALISM_CONFLICT = "STOCHASTIC_REALISM_CONFLICT"


def validate_safe_path(target_path: str, base_dir: str | None = None) -> str:
    """Resolve and validate target path to prevent directory traversal.

    Args:
        target_path: Path to resolve.
        base_dir: Approved root directory. Defaults to current working directory.

    Returns:
        str: Absolute verified target path.

    Raises:
        OptimizationExecutionError: If validation fails.
    """
    abs_target = Path(target_path).resolve()
    root_dir = Path(base_dir or Path.cwd()).resolve()
    if not abs_target.is_relative_to(root_dir):
        msg = f"Path traversal detected: {target_path} is outside {root_dir}"
        raise OptimizationExecutionError(
            msg,
            code="PERMISSION_DENIED",
        )
    return str(abs_target)


def save_checkpoint(
    file_path: str,
    data: dict[str, Any],
    run_id: str,
    base_dir: str | None = None,
) -> None:
    """Save checkpoint atomically.

    Writes to a temporary file in the same directory, flushes, fsyncs, and
    replaces target.

    Args:
        file_path: Target save location.
        data: Dict state data.
        run_id: Optimization run identifier.
        base_dir: Base directory limit.

    Raises:
        OptimizationExecutionError: If atomic write fails.
    """
    try:
        abs_path = Path(validate_safe_path(file_path, base_dir))
    except Exception as exc:
        msg = f"Path traversal validation failed: {exc}"
        raise OptimizationExecutionError(
            msg,
            code="PERMISSION_DENIED",
        ) from exc

    dir_name = abs_path.parent
    dir_name.mkdir(parents=True, exist_ok=True)

    fd, temp_path_str = tempfile.mkstemp(
        dir=str(dir_name), prefix="checkpoint_", suffix=".tmp"
    )
    temp_path = Path(temp_path_str)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
            f.flush()
            with contextlib.suppress(OSError):
                os.fsync(f.fileno())
        # Atomic rename
        temp_path.replace(abs_path)
    except Exception as exc:
        if temp_path.exists():
            with contextlib.suppress(OSError):
                temp_path.unlink()
        msg = f"Atomic write failed for {file_path} in run {run_id}: {exc}"
        raise OptimizationExecutionError(
            msg,
            code=OPT_ATOMIC_WRITE_FAILED,
        ) from exc


def validate_checkpoint_schema(data: Any) -> None:  # noqa: ANN401
    """Validate that the loaded checkpoint conforms to the schema.

    Args:
        data: Checkpoint payload structure.

    Raises:
        ValueError: If schema constraints are violated.
    """
    if not isinstance(data, dict):
        raise TypeError("Checkpoint must be a JSON object dictionary.")
    if "run_id" not in data:
        raise ValueError("Missing run_id key in checkpoint schema.")


def load_checkpoint(
    file_path: str,
    base_dir: str | None = None,
) -> dict[str, Any]:
    """Load and parse checkpoint state, rejecting corrupted or schema-invalid outputs.

    Args:
        file_path: Save location.
        base_dir: Base directory limit.

    Returns:
        dict[str, Any]: Decoded checkpoint dictionary.

    Raises:
        OptimizationExecutionError: If file is missing or corrupted.
    """
    try:
        abs_path = Path(validate_safe_path(file_path, base_dir))
    except Exception as exc:
        msg = f"Path traversal validation failed: {exc}"
        raise OptimizationExecutionError(
            msg,
            code="PERMISSION_DENIED",
        ) from exc

    if not abs_path.exists():
        msg = f"Checkpoint file does not exist: {file_path}"
        raise OptimizationExecutionError(
            msg,
            code="DATA_NOT_FOUND",
        )

    try:
        with abs_path.open() as f:
            data = json.load(f)

        validate_checkpoint_schema(data)
        return cast("dict[str, Any]", data)
    except Exception as exc:
        msg = f"Checkpoint corruption detected for {file_path}: {exc}"
        raise OptimizationExecutionError(
            msg,
            code=OPT_CHECKPOINT_CORRUPTED,
        ) from exc
