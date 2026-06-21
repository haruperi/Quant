"""Simulator report helpers.

Exports JSON-compatible and Markdown report builders over SimulatorResult
payloads. The module performs no filesystem writes unless callers persist the
returned strings themselves.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


def build_json_report(result: Mapping[str, Any]) -> str:
    """Build the canonical JSON report string.

    Args:
        result: Simulator result mapping.

    Returns:
        str: Deterministic JSON report.

    Raises:
        TypeError: If result is not JSON serializable.
    """
    return json.dumps(result, indent=2, sort_keys=True)


def build_markdown_report(result: Mapping[str, Any]) -> str:
    """Build a human-readable Markdown report.

    Args:
        result: Simulator result mapping.

    Returns:
        str: Markdown report text.

    Raises:
        No explicit exceptions are raised.
    """
    run_id = str(result.get("run_id", "unknown"))
    classification = str(result.get("classification", "unknown"))
    metrics = result.get("summary_metrics", {})
    metric_lines = []
    if isinstance(metrics, Mapping):
        metric_lines = [f"- `{key}`: {value}" for key, value in sorted(metrics.items())]
    return "\n".join(
        [
            f"# Simulator Report {run_id}",
            "",
            f"- Classification: `{classification}`",
            f"- Realism disclosure: {result.get('realism_disclosure', 'not provided')}",
            "",
            "## Summary Metrics",
            *metric_lines,
            "",
        ]
    )
