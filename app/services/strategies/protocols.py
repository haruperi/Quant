"""Type declarations and interfaces for the strategies service.

This module defines standard protocols, configs, contexts, results, and manifest
structures that unify all batch and event-driven strategy execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Protocol, runtime_checkable

import pandas as pd
from pydantic import BaseModel, Field

StrategyEnvironment = Literal["BACKTEST", "REPLAY", "PAPER", "SHADOW", "LIVE"]
StrategySide = Literal["BUY", "SELL", "HOLD"]
StrategyIntentType = Literal["OPEN", "CLOSE", "REDUCE", "INCREASE", "NO_ACTION"]
StrategyTimingPolicy = Literal["BAR_OPEN_PREVIOUS_CLOSE", "INTRABAR_EVENT"]
ConfigUnknownFieldPolicy = Literal["REJECT", "IGNORE"]


class StrategyRefInput(BaseModel):
    """Pydantic schema representing strategy registration locator input."""

    schema_version: str = "strategy.ref.v1"
    strategy_id: str
    version: str | None = None
    version_constraint: str | None = None
    environment: StrategyEnvironment
    request_id: str | None = None
    correlation_id: str | None = None


class StrategyConfigInput(BaseModel):
    """Pydantic schema representing configuration inputs validation envelope."""

    schema_version: str = "strategy.config.v1"
    strategy_ref: StrategyRefInput
    config: dict[str, Any]
    registry_schema_version: str
    unknown_field_policy: ConfigUnknownFieldPolicy = "REJECT"
    max_payload_bytes: int = 65536


class ReadOnlyExecutionStateQuery(BaseModel):
    """Execution state query filters request schema."""

    schema_version: str = "strategy.read_only_state_query.v1"
    strategy_id: str
    symbol: str | None = None
    include_fills: bool = True
    include_open_positions: bool = True
    snapshot_at: datetime
    request_id: str | None = None
    correlation_id: str | None = None


class ReadOnlyExecutionStateSnapshot(BaseModel):
    """Immutable snapshot payload representing fills and open positions state."""

    schema_version: str = "strategy.read_only_state_snapshot.v1"
    snapshot_id: str
    snapshot_at: datetime
    source_module: str
    fills: list[dict[str, Any]] = Field(default_factory=list)
    open_positions: list[dict[str, Any]] = Field(default_factory=list)
    consistency_model: Literal["IMMUTABLE_SNAPSHOT"] = "IMMUTABLE_SNAPSHOT"


class StrategyExecutionContext(BaseModel):
    """Operational context passed during decision-time calculations."""

    schema_version: str = "strategy.execution_context.v1"
    environment: StrategyEnvironment
    decision_timestamp: datetime
    timing_policy: StrategyTimingPolicy
    seed_material: str
    request_id: str
    correlation_id: str
    read_only_state: ReadOnlyExecutionStateSnapshot | None = None
    resource_budget_ref: str | None = None


class TradeIntent(BaseModel):
    """Strategic trade intent emitted by a strategy decision."""

    schema_version: str = "strategy.trade_intent.v1"
    intent_id: str
    decision_id: str
    idempotency_key: str
    strategy_id: str
    strategy_version: str
    symbol: str
    side: StrategySide
    intent_type: StrategyIntentType
    requested_sizing_mode: str | None = None
    quantity_hint: Decimal | None = None
    signal_timestamp: datetime
    decision_timestamp: datetime
    parent_intent_id: str | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    expiration: datetime | None = None
    allow_partial_fills: bool = False
    min_fill_size: Decimal | None = None
    rationale_ref: str | None = None
    lineage: dict[str, str] = Field(default_factory=dict)


class StrategyDiagnostics(BaseModel):
    """Structured decision diagnostics returned by strategies or orchestrators."""

    schema_version: str = "strategy.diagnostics.v1"
    strategy_id: str
    strategy_version: str | None = None
    request_id: str
    correlation_id: str
    decision_timestamp: datetime | None = None
    status: Literal["success", "error", "degraded", "suppressed"]
    error_code: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    redaction_status: Literal["redacted", "not_required"] = "not_required"
    dependency_health: dict[str, str] = Field(default_factory=dict)


@dataclass(frozen=True)
class StrategyRiskProfile:
    """Declared strategy risk assumptions and advisories.

    Used by simulation/risk engine during validation checks.
    """

    max_gross_exposure: Decimal | None = None
    max_net_exposure: Decimal | None = None
    max_symbol_exposure: Decimal | None = None
    max_intent_notional: Decimal | None = None
    max_intent_frequency: int | None = None
    max_concurrent_positions: int | None = None
    max_pyramiding_depth: int | None = None
    max_martingale_level: int | None = None
    max_grid_depth: int | None = None


@runtime_checkable
class StrategyProtocol(Protocol):
    """Typing protocol representing the structural contract for all strategies."""

    @property
    def strategy_id(self) -> str:
        """Unique key mapping this strategy definition."""
        ...

    @property
    def version(self) -> str:
        """Version of this strategy code."""
        ...

    @property
    def lifecycle_status(self) -> str:
        """Lifecycle status of the strategy (e.g. DRAFT, RESEARCH)."""
        ...

    @property
    def permitted_environments(self) -> list[StrategyEnvironment]:
        """Allowed environments for execution."""
        ...

    @property
    def config_schema(self) -> dict[str, Any] | None:
        """JSON schema or dictionary descriptor for config validation."""
        ...

    @property
    def risk_profile(self) -> StrategyRiskProfile | None:
        """Advisory risk limits declared by strategy."""
        ...

    def run_vectorized_signals(
        self,
        data: pd.DataFrame,
        indicators: pd.DataFrame,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> list[TradeIntent]:
        """Compute signals across a batch DataFrame and return TradeIntent list."""
        ...

    # Optional lifecycle event hooks
    def on_init(
        self,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on initialization."""
        ...

    def on_bar(
        self,
        bar: dict[str, Any],
        indicators: dict[str, Any],
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on closed bar events."""
        ...

    def on_tick(
        self,
        tick: dict[str, Any],
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on new price ticks."""
        ...

    def on_fill_update(
        self,
        fill_event: dict[str, Any],
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on deal fills/partial fills."""
        ...
