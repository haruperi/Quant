# ruff: noqa
"""Validation schemas and metadata structures for simulation backtesting.

Defines Pydantic models for incoming simulation requests, symbol specifications,
results, persistence/realism configuration, and the official tool response envelope.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class SymbolSpec(BaseModel):
    """Normalized specification details for a financial symbol."""

    symbol: str
    point: Decimal = Field(default=Decimal("0.00001"))
    tick_size: Decimal = Field(default=Decimal("0.00001"))
    tick_value: Decimal = Field(default=Decimal("1.0"))
    contract_size: Decimal = Field(default=Decimal("100000.0"))
    volume_min: Decimal = Field(default=Decimal("0.01"))
    volume_max: Decimal = Field(default=Decimal("100.0"))
    volume_step: Decimal = Field(default=Decimal("0.01"))
    asset_class: str = Field(default="FX")
    profit_currency: str = Field(default="USD")
    margin_currency: str = Field(default="USD")
    commission_currency: str = Field(default="USD")
    swap_long: Decimal = Field(default=Decimal("0.0"))
    swap_short: Decimal = Field(default=Decimal("0.0"))
    swap_mode: str = Field(default="points")  # points, money, percent, interest
    swap_rollover_day: int = Field(default=3)  # Triple swap day (Wednesday = 3)
    stops_level: Decimal = Field(default=Decimal("0.0"))
    freeze_level: Decimal = Field(default=Decimal("0.0"))
    sessions: list[dict[str, str]] = Field(default_factory=list)


class SimulationBacktestRequestV1(BaseModel):
    """Pydantic model representing standard Simulation tool input arguments."""

    schema_version: str = Field(default="simulation.backtest_request.v1")
    request_id: str | None = Field(default=None)
    actor_context: dict[str, Any] | None = Field(default=None)
    strategy_ref: str
    strategy_config: dict[str, Any] = Field(default_factory=dict)
    symbols: list[str]
    timeframe: str
    start: str
    end: str
    initial_balance: Decimal = Field(default=Decimal("10000.0"))
    account_currency: str = Field(default="USD")
    tick_model: str = Field(
        default="M1_TICKS"
    )  # TIMEFRAME_TICKS, M1_TICKS, REAL_TICKS, SYNTHETIC_TICKS
    spread_model: str = Field(
        default="NATIVE_SPREAD"
    )  # NATIVE_SPREAD, FIXED_SPREAD, VARIABLE_SPREAD
    slippage_model: str = Field(
        default="NO_SLIPPAGE"
    )  # NO_SLIPPAGE, FIXED_SLIPPAGE, etc.
    commission_model: str = Field(
        default="NO_COMMISSION"
    )  # NO_COMMISSION, FIXED_COMMISSION, etc.
    swap_model: str = Field(default="NO_SWAP")  # NO_SWAP, etc.
    broker_profile_ref: str = Field(default="mt5_demo_reference_fx_v1")
    market_data_authority_ref: str | None = Field(default=None)
    journal_persistence: dict[str, Any] = Field(default_factory=dict)
    artifact_root_ref: str | None = Field(default=None)
    realism_profile: str = Field(default="research_approximation")
    metadata: dict[str, Any] = Field(default_factory=dict)


class SimulationToolEnvelopeV1(BaseModel):
    """Detailed response envelope specified by the simulation requirements."""

    schema_version: str = Field(default="simulation.tool_envelope.v1")
    request_id: str | None = Field(default=None)
    status: str
    result: dict[str, Any] | None = Field(default=None)
    error: dict[str, Any] | None = Field(default=None)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, str] = Field(default_factory=dict)
