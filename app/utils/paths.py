"""Safe path normalization and explicit directory creation helpers.

This module provides support helpers, not official AI tools. It exports
side-effect-free path normalization plus explicit directory creation helpers
with base-directory traversal protection.

Public exports:
    normalize_path, ensure_dir, ensure_parent_dir,
    safe_join, validate_path_within_root.

Side effects:
    ``normalize_path``, ``safe_join``, and ``validate_path_within_root`` have
    none. ``ensure_dir`` and ``ensure_parent_dir`` create directories only when
    explicitly called.
"""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

from app.utils.errors import SecurityError, ValidationError
from app.utils.logger import logger


def _raise_validation(message: str, *, field_name: str) -> NoReturn:
    """Log and raise a deterministic path validation error."""
    logger.warning(
        "path validation failed",
        extra={
            "event_name": "path_validation_failed",
            "field_name": field_name,
            "error_code": "INVALID_INPUT",
        },
    )
    raise ValidationError(message, code="INVALID_INPUT")


def _coerce_path(value: str | Path, *, field_name: str) -> Path:
    """Return a ``Path`` from a string or Path input."""
    if isinstance(value, str):
        if not value.strip():
            _raise_validation(
                f"{field_name} must be a non-empty path.",
                field_name=field_name,
            )
        return Path(value.strip()).expanduser()
    if isinstance(value, Path):
        if not str(value):
            _raise_validation(
                f"{field_name} must be a non-empty path.",
                field_name=field_name,
            )
        return value.expanduser()
    _raise_validation(
        f"{field_name} must be a string or pathlib.Path.",
        field_name=field_name,
    )


def _resolve_path(path: Path) -> Path:
    """Resolve a path without requiring the final target to exist."""
    return path.resolve(strict=False)


def _strip_windows_extended_prefix(path: Path) -> Path:
    """Return a comparable path without a Windows extended-length prefix."""
    text = str(path)
    if text.startswith("\\\\?\\UNC\\"):
        return Path(f"\\\\{text[8:]}")
    if text.startswith("\\\\?\\"):
        return Path(text[4:])
    return path


def _ensure_within_base(path: Path, base_dir: Path) -> None:
    """Raise when ``path`` is outside ``base_dir``."""
    comparable_path = _strip_windows_extended_prefix(path)
    comparable_base = _strip_windows_extended_prefix(base_dir)
    try:
        comparable_path.relative_to(comparable_base)
    except ValueError as exc:
        logger.warning(
            "path traversal rejected",
            extra={
                "event_name": "path_traversal_rejected",
                "error_code": "PERMISSION_DENIED",
            },
        )
        message = "path traversal outside base_dir is not allowed."
        raise SecurityError(message) from exc


def normalize_path(
    path: str | Path,
    *,
    base_dir: str | Path | None = None,
) -> Path:
    """Normalize a path with optional base-directory traversal protection.

    Use this for deterministic path handling before reading, writing, or
    creating filesystem resources. This helper does not create files or
    directories.

    Args:
        path: String or ``Path`` value to normalize.
        base_dir: Optional base directory. Relative paths are resolved
            under this directory, and absolute/relative paths outside it
            are rejected.

    Returns:
        Normalized absolute ``Path`` object.

    Raises:
        ValidationError: If ``path`` or ``base_dir`` is empty or malformed.
        SecurityError: If the normalized path escapes ``base_dir``.

    Side effects:
        None.
    """
    raw_path = _coerce_path(path, field_name="path")
    if base_dir is None:
        return _resolve_path(raw_path)

    raw_base = _coerce_path(base_dir, field_name="base_dir")
    normalized_base = _resolve_path(raw_base)
    candidate = raw_path if raw_path.is_absolute() else normalized_base / raw_path
    normalized = _resolve_path(candidate)
    _ensure_within_base(normalized, normalized_base)
    return normalized


def safe_join(base_dir: str | Path, *parts: str | Path) -> Path:
    """Join path parts relative to base_dir with traversal protection.

    All resolved path components must remain inside ``base_dir``. This
    function is the approved replacement for unsafe ``os.path.join`` calls
    in security-sensitive contexts.

    Args:
        base_dir: Root directory that all resolved paths must stay inside.
        *parts: Path components to join under ``base_dir``.

    Returns:
        Resolved absolute ``Path`` guaranteed to be inside ``base_dir``.

    Raises:
        ValidationError: If any part is empty or malformed.
        SecurityError: If the joined path escapes ``base_dir``.

    Side effects:
        None.
    """
    raw_base = _coerce_path(base_dir, field_name="base_dir")
    normalized_base = _resolve_path(raw_base)
    candidate = normalized_base
    for index, part in enumerate(parts):
        raw_part = _coerce_path(part, field_name=f"parts[{index}]")
        candidate = candidate / raw_part
    normalized = _resolve_path(candidate)
    _ensure_within_base(normalized, normalized_base)
    return normalized


def validate_path_within_root(
    path: str | Path,
    root: str | Path,
) -> Path:
    """Validate that ``path`` is inside ``root`` and return the resolved path.

    Use this to gate filesystem operations on caller-supplied paths before
    they reach ``open()``, ``shutil``, or any other I/O helper.

    Args:
        path: Path to validate.
        root: Required root directory boundary.

    Returns:
        Resolved absolute ``Path``.

    Raises:
        ValidationError: If either ``path`` or ``root`` is empty or malformed.
        SecurityError: If ``path`` escapes ``root``.

    Side effects:
        None.
    """
    raw_path = _coerce_path(path, field_name="path")
    raw_root = _coerce_path(root, field_name="root")
    normalized_root = _resolve_path(raw_root)
    candidate = raw_path if raw_path.is_absolute() else normalized_root / raw_path
    normalized = _resolve_path(candidate)
    _ensure_within_base(normalized, normalized_root)
    return normalized


def ensure_dir(
    path: str | Path,
    *,
    base_dir: str | Path | None = None,
) -> Path:
    """Normalize and create a directory if it is missing.

    Args:
        path: Directory path to normalize and create.
        base_dir: Optional base directory traversal boundary.

    Returns:
        Normalized directory ``Path``.

    Raises:
        ValidationError: If path input is invalid or directory creation
            fails due to a filesystem error.
        SecurityError: If the normalized path escapes ``base_dir``.

    Side effects:
        Creates the normalized directory using platform-safe defaults.
    """
    directory = normalize_path(path, base_dir=base_dir)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        message = f"failed to create directory: {directory}"
        raise ValidationError(message, code="INVALID_INPUT") from exc
    logger.info(
        "directory ensured",
        extra={
            "event_name": "directory_ensured",
            "path": str(directory),
        },
    )
    return directory


def ensure_parent_dir(
    path: str | Path,
    *,
    base_dir: str | Path | None = None,
) -> Path:
    """Normalize a file path and create its parent directory if missing.

    Args:
        path: File path whose parent directory should exist.
        base_dir: Optional base directory traversal boundary.

    Returns:
        Normalized file ``Path``.

    Raises:
        ValidationError: If path input is invalid or parent creation fails
            due to a filesystem error.
        SecurityError: If the normalized path escapes ``base_dir``.

    Side effects:
        Creates the normalized parent directory using platform-safe defaults.
    """
    file_path = normalize_path(path, base_dir=base_dir)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        message = f"failed to create parent directory: {file_path.parent}"
        raise ValidationError(message, code="INVALID_INPUT") from exc
    logger.info(
        "parent directory ensured",
        extra={
            "event_name": "parent_directory_ensured",
            "path": str(file_path.parent),
        },
    )
    return file_path
