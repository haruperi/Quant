"""Concurrency stress suite for utility path helpers.

This module is intentionally outside ``tests/unit`` and is not named
``test_*.py``, so it does not run in the fast unit-test path. Run it manually
when validating path helper behavior under concurrent callers.
"""

# ruff: noqa: E402

import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

project_root = str(Path(__file__).resolve().parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.paths import ensure_dir, ensure_parent_dir, normalize_path


def _run_single_iteration(base_dir: Path, index: int) -> None:
    """Run one concurrent path-helper iteration."""
    normalize_path(f"normalized/{index}/item.txt", base_dir=base_dir)
    ensure_dir(f"cache/{index}", base_dir=base_dir)
    ensure_parent_dir(f"artifacts/{index}/result.json", base_dir=base_dir)


def run_path_concurrency_stress(
    *,
    workers: int = 8,
    iterations: int = 100,
) -> dict[str, int]:
    """Run a bounded concurrency stress scenario for path helpers.

    Args:
        workers: Number of worker threads.
        iterations: Number of concurrent iterations.

    Returns:
        Summary counts for attempted iterations and workers.

    Raises:
        ValueError: If worker or iteration counts are not positive.

    Side effects:
        Creates temporary directories under the platform temporary directory.
    """
    if workers <= 0:
        raise ValueError("workers must be greater than zero.")
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero.")

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(_run_single_iteration, base_dir, index)
                for index in range(iterations)
            ]
            for future in futures:
                future.result()

    return {"workers": workers, "iterations": iterations}


if __name__ == "__main__":
    print(run_path_concurrency_stress())
