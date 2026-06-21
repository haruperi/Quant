"""Simulator tick and request models.

Exports immutable request, actor, symbol, and tick structures used by the
simulator engine and tool boundary. The module has no side effects on import.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.utils.errors import ValidationError
from app.utils.normalization import normalize_timestamp

RealismProfile = Literal[
    "research_approximation", "mt5_parity_oriented", "production_realistic"
]
JournalPersistenceMode = Literal["memory", "jsonl"]


@dataclass(frozen=True, slots=True)
class SimulatorActorContext:
    """Authenticated actor context for simulator requests.

    Args:
        actor_id: Stable actor identifier.
        roles: Actor role names.
        auth_source: Authentication source label.

    Raises:
        ValidationError: If actor identity or roles are malformed.
    """

    actor_id: str
    roles: tuple[str, ...] = ("researcher",)
    auth_source: str = "local"

    def __post_init__(self) -> None:
        """Validate actor fields after dataclass construction."""
        if not self.actor_id.strip():
            raise ValidationError("actor_id must be non-empty.", code="INVALID_INPUT")
        if not self.roles or any(not role.strip() for role in self.roles):
            raise ValidationError("roles must contain non-empty values.")


@dataclass(frozen=True, slots=True)
class SimulatorSymbolSpec:
    """FX-oriented simulator symbol metadata.

    Args:
        symbol: Canonical symbol.
        digits: Price precision.
        point: Point size.
        contract_size: Units per lot.
        lot_min: Minimum lot size.
        lot_max: Maximum lot size.
        lot_step: Supported lot increment.
        base_currency: Base currency.
        quote_currency: Quote currency.

    Raises:
        ValidationError: If numeric limits are inconsistent.
    """

    symbol: str
    digits: int = 5
    point: float = 0.00001
    contract_size: float = 100000.0
    lot_min: float = 0.01
    lot_max: float = 100.0
    lot_step: float = 0.01
    base_currency: str = "EUR"
    quote_currency: str = "USD"

    def __post_init__(self) -> None:
        """Validate symbol metadata."""
        if not self.symbol.strip():
            raise ValidationError("symbol must be non-empty.")
        if self.digits < 0 or self.point <= 0 or self.contract_size <= 0:
            raise ValidationError("symbol precision and contract values must be valid.")
        if self.lot_min <= 0 or self.lot_max < self.lot_min or self.lot_step <= 0:
            raise ValidationError("symbol lot limits are invalid.")


@dataclass(frozen=True, slots=True)
class SimulatorTick:
    """Canonical bid/ask tick for simulator execution.

    Args:
        timestamp: UTC ISO timestamp.
        symbol: Symbol name.
        bid: Bid price.
        ask: Ask price.
        last: Optional last price.
        volume: Optional available volume proxy.
        spread_points: Optional spread in points.
        source: Data source label.

    Raises:
        ValidationError: If timestamp or price relationships are invalid.
    """

    timestamp: str
    symbol: str
    bid: float
    ask: float
    last: float | None = None
    volume: float | None = None
    spread_points: float | None = None
    source: str = "simulator"

    def __post_init__(self) -> None:
        """Validate tick fields and normalize timestamp."""
        normalized = normalize_timestamp(self.timestamp).isoformat()
        object.__setattr__(self, "timestamp", normalized)
        if not self.symbol.strip():
            raise ValidationError("symbol must be non-empty.")
        if self.bid <= 0 or self.ask <= 0 or self.ask < self.bid:
            raise ValidationError("tick bid/ask prices are invalid.")
        if self.volume is not None and self.volume < 0:
            raise ValidationError("tick volume must be non-negative.")
        if self.spread_points is not None and self.spread_points < 0:
            raise ValidationError(
                "tick spread_points must be non-negative.",
                code="SIM_DATA_NEGATIVE_SPREAD",
            )


@dataclass(frozen=True, slots=True)
class SimulatorBacktestRequestV1:
    """Validated public backtest request payload.

    Args:
        schema_version: Request schema version.
        request_id: Trace request identifier.
        actor_context: Authenticated actor context.
        strategy_ref: Registered strategy identifier.
        strategy_config: Strategy configuration payload.
        symbols: Symbols included in the run.
        timeframe: Requested timeframe.
        start: UTC start time.
        end: UTC end time.
        initial_balance: Initial account balance.
        account_currency: Account currency.
        tick_model: Tick model id.
        spread_model: Spread model id.
        slippage_model: Slippage model id.
        commission_model: Commission model id.
        swap_model: Swap model id.
        broker_profile_ref: Broker profile reference.
        market_data_authority_ref: Market data authority reference.
        journal_persistence: Journal persistence mode.
        artifact_root_ref: Allowlisted artifact root reference.
        realism_profile: Realism profile label.
        metadata: Namespaced metadata.

    Raises:
        ValidationError: If required fields are missing or inconsistent.
    """

    request_id: str
    actor_context: SimulatorActorContext
    strategy_ref: str
    symbols: tuple[str, ...]
    timeframe: str
    start: str
    end: str
    schema_version: str = "1.0.0"
    strategy_config: dict[str, object] = field(default_factory=dict)
    initial_balance: float = 100000.0
    account_currency: str = "USD"
    tick_model: str = "deterministic_midpoint_v1"
    spread_model: str = "fixed_points_v1"
    slippage_model: str = "none_v1"
    commission_model: str = "none_v1"
    swap_model: str = "none_v1"
    broker_profile_ref: str = "mt5_demo_reference_fx_v1"
    market_data_authority_ref: str = "local_synthetic_v1"
    journal_persistence: JournalPersistenceMode = "memory"
    artifact_root_ref: str | None = None
    realism_profile: RealismProfile = "research_approximation"
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate request boundary fields."""
        if not self.request_id.strip():
            raise ValidationError("request_id must be non-empty.")
        if not self.strategy_ref.strip():
            raise ValidationError("strategy_ref must be non-empty.")
        if not self.symbols or any(not symbol.strip() for symbol in self.symbols):
            raise ValidationError("symbols must contain non-empty values.")
        if self.initial_balance <= 0:
            raise ValidationError("initial_balance must be greater than zero.")
        start = normalize_timestamp(self.start)
        end = normalize_timestamp(self.end)
        if start >= end:
            raise ValidationError(
                "start must be before end.",
                code="SIM_INVALID_DATE_RANGE",
            )
        object.__setattr__(self, "start", start.isoformat())
        object.__setattr__(self, "end", end.isoformat())
        if self.journal_persistence not in {"memory", "jsonl"}:
            raise ValidationError("journal_persistence is unsupported.")
        if self.realism_profile not in {
            "research_approximation",
            "mt5_parity_oriented",
            "production_realistic",
        }:
            raise ValidationError("realism_profile is unsupported.")
