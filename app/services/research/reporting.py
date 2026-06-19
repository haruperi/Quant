# ruff: noqa: E501, TC001
"""Reporting and serialization service for Research Edge Lab.

This module converts edge discovery results and profile snapshots to markdown,
summary dicts, scorecards, and persists them safely to files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.utils.errors import ValidationError
from app.utils.logger import logger
from app.utils.security import redact_mapping
from app.utils.settings import EdgeResult


def result_to_markdown(result: EdgeResult) -> str:
    """Convert an edge result into a Markdown report."""
    config_dict = redact_mapping(result.config.model_dump(mode="json"))
    stats = result.stats

    md = []
    md.append(f"# Edge Discovery Report: {result.study_name}")
    md.append(f"**Generated At**: {result.audit_metadata.get('created_at', 'N/A')}")
    md.append("## Summary Statistics")
    md.append(f"- **Sample Size**: {stats.sample_size}")
    md.append(f"- **Win Rate**: {stats.win_rate:.2%}")
    md.append(f"- **Profit Factor**: {stats.profit_factor:.2f}")
    md.append(f"- **Expectancy (R)**: {stats.expectancy:.2f}")
    md.append(f"- **Sharpe Ratio**: {stats.sharpe_ratio:.2f}")
    if stats.p_value is not None:
        md.append(f"- **P-Value**: {stats.p_value:.4f}")
    if stats.t_statistic is not None:
        md.append(f"- **T-Statistic**: {stats.t_statistic:.2f}")

    if result.warnings:
        md.append("## Warnings")
        for warning in result.warnings:
            md.append(f"- [⚠️] {warning}")

    md.append("## Configuration Used")
    md.append("```json")
    md.append(json.dumps(config_dict, indent=2))
    md.append("```")

    md.append("## Audit Evidence & Metadata")
    md.append("```json")
    md.append(json.dumps(redact_mapping(result.audit_metadata), indent=2))
    md.append("```")

    md.append("\n*Disclaimer: This report is advisory-only for research purposes.*")

    return "\n".join(md)


def result_to_summary(result: EdgeResult) -> dict[str, Any]:
    """Generate a concise summary dictionary from an edge result."""
    return {
        "study_name": result.study_name,
        "sample_size": result.stats.sample_size,
        "win_rate": result.stats.win_rate,
        "profit_factor": result.stats.profit_factor,
        "expectancy": result.stats.expectancy,
        "sharpe_ratio": result.stats.sharpe_ratio,
        "p_value": result.stats.p_value,
        "warnings_count": len(result.warnings),
    }


def _safe_write(content: str, filepath: str, overwrite: bool) -> bool:
    """Safely write content to filepath with atomic replace and path verification."""
    path = Path(filepath)
    # Prevent path traversal
    if ".." in path.parts:
        raise ValidationError("Directory traversal detected.", code="PERMISSION_DENIED")

    if path.exists() and not overwrite:
        logger.warning(f"File {filepath} already exists and overwrite is False.")
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_file = path.with_suffix(".tmp")
    try:
        temp_file.write_text(content, encoding="utf-8")
        # Atomic rename
        temp_file.replace(path)
        return True
    except Exception as e:
        logger.error(f"Failed to write report to {filepath}: {e}")
        if temp_file.exists():
            temp_file.unlink()
        raise


def save_markdown(
    result: EdgeResult,
    filepath: str,
    overwrite: bool = True,
) -> bool:
    """Persist an edge result report as Markdown."""
    content = result_to_markdown(result)
    return _safe_write(content, filepath, overwrite)


def save_json(result: EdgeResult, filepath: str, overwrite: bool = True) -> bool:
    """Persist an edge result report as JSON."""
    content = json.dumps(redact_mapping(result.model_dump(mode="json")), indent=2)
    return _safe_write(content, filepath, overwrite)


def generate_multi_symbol_report(results: list[EdgeResult]) -> str:
    """Generate a combined Markdown report for multiple symbols."""
    md = ["# Multi-Symbol Edge Comparison Report\n"]
    md.append("| Study | Size | Win Rate | Profit Factor | Expectancy | Sharpe |")
    md.append("|---|---|---|---|---|---|")
    for r in results:
        stats = r.stats
        md.append(
            f"| {r.study_name} | {stats.sample_size} | {stats.win_rate:.1%} "
            f"| {stats.profit_factor:.2f} | {stats.expectancy:.2f} | {stats.sharpe_ratio:.2f} |"
        )
    md.append("\n*Disclaimer: Advisory-only comparison report.*")
    return "\n".join(md)


def build_edge_profile_snapshot(
    symbol: str,
    timeframe: str,
    results: list[EdgeResult],
) -> dict[str, Any]:
    """Build a normalized snapshot payload from progressive Edge Lab tab results."""
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "schema_version": "1.0.0",
        "snapshots": [result_to_summary(r) for r in results],
        "audit_metadata": {
            "symbol": symbol,
            "timeframe": timeframe,
            "created_at": "2026-06-19T16:44:44Z",
        },
    }


def build_profile_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Build a concise dashboard-ready summary from one profile snapshot."""
    snapshots = snapshot.get("snapshots", [])
    if not snapshots:
        return {"symbol": snapshot.get("symbol"), "status": "empty"}

    avg_win_rate = sum(s["win_rate"] for s in snapshots) / len(snapshots)
    avg_expectancy = sum(s["expectancy"] for s in snapshots) / len(snapshots)
    return {
        "symbol": snapshot.get("symbol"),
        "timeframe": snapshot.get("timeframe"),
        "studies_count": len(snapshots),
        "avg_win_rate": avg_win_rate,
        "avg_expectancy": avg_expectancy,
    }


def build_dashboard_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Build a UI or dashboard summary block from one profile snapshot."""
    summary = build_profile_summary(snapshot)
    summary["ui_display_type"] = "research_profile"
    return summary


def save_json_report(
    snapshot: dict[str, Any],
    filepath: str,
    overwrite: bool = True,
) -> bool:
    """Save one complete JSON profile report."""
    content = json.dumps(redact_mapping(snapshot), indent=2)
    return _safe_write(content, filepath, overwrite)


def save_markdown_report(
    snapshot: dict[str, Any],
    filepath: str,
    overwrite: bool = True,
) -> bool:
    """Save one complete Markdown profile report."""
    md = [
        f"# Edge Profile Snapshot: {snapshot.get('symbol')} "
        f"({snapshot.get('timeframe')})"
    ]
    md.append(f"**Schema Version**: {snapshot.get('schema_version')}\n")
    md.append("## Studies Evaluated")
    for s in snapshot.get("snapshots", []):
        md.append(f"### {s['study_name']}")
        md.append(f"- **Sample Size**: {s['sample_size']}")
        md.append(f"- **Win Rate**: {s['win_rate']:.1%}")
        md.append(f"- **Expectancy**: {s['expectancy']:.2f}")

    content = "\n".join(md)
    return _safe_write(content, filepath, overwrite)


def build_edge_lab_scorecard_report(
    symbol: str,
    timeframe: str,
    results: list[EdgeResult],
) -> dict[str, Any]:
    """Build a deterministic backend scorecard report from progressive Edge Lab outputs."""
    snapshot = build_edge_profile_snapshot(symbol, timeframe, results)
    summary = build_profile_summary(snapshot)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "scorecard": summary,
        "advisory_disclaimer": "This scorecard is for research purposes only.",
    }
