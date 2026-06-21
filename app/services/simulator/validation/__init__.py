"""Simulator validation public facade.

Exports schema and data-quality gates used by simulator entry points. Importing
this module has no side effects.
"""

from app.services.simulator.validation.quality import validate_tick_records
from app.services.simulator.validation.schema import (
    parse_backtest_request,
    reject_arbitrary_strategy_code,
)

__all__ = [
    "parse_backtest_request",
    "reject_arbitrary_strategy_code",
    "validate_tick_records",
]
