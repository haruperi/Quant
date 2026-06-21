# ruff: noqa
"""Official AI tools implementation for the Simulation Service.

Exposes the run_backtest tool wrapper for AI agents and orchestrators.
"""

from __future__ import annotations

from typing import Any

from app.services.simulator.orchestrator import run_backtest as _run_backtest
from app.utils.standard import StandardResponse


def run_backtest(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    strategy_config: dict[str, Any] | None = None,
    initial_balance: float = 10000.0,
    account_currency: str = "USD",
    tick_model: str = "M1_TICKS",
    spread_model: str = "NATIVE_SPREAD",
    slippage_model: str = "NO_SLIPPAGE",
    commission_model: str = "NO_COMMISSION",
    swap_model: str = "NO_SWAP",
    broker_profile_ref: str = "mt5_demo_reference_fx_v1",
    journal_persistence: dict[str, Any] | None = None,
    request_id: str | None = None,
    **kwargs: Any,
) -> StandardResponse:
    """Run a deterministic, tick-accurate strategy backtest and simulation.

    Args:
        strategy_ref: Registered identifier of the trading strategy to execute.
        symbols: List of symbol tickers to trade (e.g. ['EURUSD']).
        timeframe: Historic bar resolution (e.g. 'H1').
        start: Start date-time string in ISO format.
        end: End date-time string in ISO format.
        strategy_config: Configuration dictionary passed to the strategy parameters.
        initial_balance: Starting account balance cash deposit.
        account_currency: Base account accounting currency (e.g. 'USD').
        tick_model: Pricing tick stream mode ('M1_TICKS', 'TIMEFRAME_TICKS', 'REAL_TICKS', 'SYNTHETIC_TICKS').
        spread_model: Spread behavior model ('NATIVE_SPREAD', 'FIXED_SPREAD', 'VARIABLE_SPREAD').
        slippage_model: Slippage cost model ('NO_SLIPPAGE', 'FIXED_SLIPPAGE', etc.).
        commission_model: Commission cost model ('NO_COMMISSION', 'FIXED_COMMISSION', etc.).
        swap_model: Overnight rollover swap cost model ('NO_SWAP', etc.).
        broker_profile_ref: Identifier mapping to symbol precision, leverage, and volume constraints.
        journal_persistence: Configuration for streaming append-only JSONL files and SQLite sidecars.
        request_id: Optional tracking identifier for request correlation.
    """
    payload = {
        "strategy_ref": strategy_ref,
        "symbols": symbols,
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "strategy_config": strategy_config or {},
        "initial_balance": initial_balance,
        "account_currency": account_currency,
        "tick_model": tick_model,
        "spread_model": spread_model,
        "slippage_model": slippage_model,
        "commission_model": commission_model,
        "swap_model": swap_model,
        "broker_profile_ref": broker_profile_ref,
        "journal_persistence": journal_persistence or {},
        "request_id": request_id,
        **kwargs,
    }
    return _run_backtest(payload)
