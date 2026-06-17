# ruff: noqa
"""Simulation Service.

Provides deterministic tick-accurate execution, broker models, and
journal/reporting persistence.
"""

from app.services.simulation.engine import EventDrivenExecutionEngine
from app.services.simulation.journal import Journal
from app.services.simulation.orchestrator import run_backtest
from app.services.simulation.report import (
    calculate_metrics,
    generate_json_report,
    generate_markdown_report,
)
from app.services.simulation.trader import SimTrader

__all__ = [
    "EventDrivenExecutionEngine",
    "Journal",
    "SimTrader",
    "calculate_metrics",
    "generate_json_report",
    "generate_markdown_report",
    "run_backtest",
]
