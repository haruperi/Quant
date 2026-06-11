"""Unit tests for tools.utils.paths."""

from pathlib import Path

import pytest
from tools.utils.errors import SecurityError, ValidationError
from tools.utils.paths import ensure_dir, ensure_parent_dir, normalize_path


def test_normalize_path_returns_path_without_creating_target(tmp_path: Path) -> None:
    target = normalize_path("nested/file.txt", base_dir=tmp_path)

    assert isinstance(target, Path)
    assert target == (tmp_path / "nested" / "file.txt").resolve(strict=False)
    assert not target.exists()
    assert not target.parent.exists()


def test_normalize_path_accepts_absolute_path_inside_base(tmp_path: Path) -> None:
    target = tmp_path / "child" / "file.txt"

    normalized = normalize_path(target, base_dir=tmp_path)

    assert normalized == target.resolve(strict=False)


def test_normalize_path_rejects_empty_or_invalid_inputs(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="path"):
        normalize_path("", base_dir=tmp_path)

    with pytest.raises(ValidationError, match="base_dir"):
        normalize_path("file.txt", base_dir="")

    with pytest.raises(ValidationError, match="path"):
        normalize_path(object())  # type: ignore[arg-type]


def test_normalize_path_rejects_traversal_outside_base(tmp_path: Path) -> None:
    with pytest.raises(SecurityError, match="base_dir"):
        normalize_path("../outside.txt", base_dir=tmp_path)

    outside = tmp_path.parent / "outside.txt"
    with pytest.raises(SecurityError, match="base_dir"):
        normalize_path(outside, base_dir=tmp_path)


def test_ensure_dir_creates_missing_directory(tmp_path: Path) -> None:
    directory = ensure_dir("cache/items", base_dir=tmp_path)

    assert directory == (tmp_path / "cache" / "items").resolve(strict=False)
    assert directory.is_dir()


def test_ensure_dir_rejects_traversal_before_creation(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        ensure_dir("../escape", base_dir=tmp_path)

    assert not (tmp_path.parent / "escape").exists()


def test_ensure_parent_dir_creates_parent_and_returns_file_path(tmp_path: Path) -> None:
    file_path = ensure_parent_dir("audit/events/event.json", base_dir=tmp_path)

    assert file_path == (tmp_path / "audit" / "events" / "event.json").resolve(
        strict=False,
    )
    assert file_path.parent.is_dir()
    assert not file_path.exists()


def test_ensure_parent_dir_rejects_traversal_before_creation(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        ensure_parent_dir("../escape/file.txt", base_dir=tmp_path)

    assert not (tmp_path.parent / "escape").exists()
