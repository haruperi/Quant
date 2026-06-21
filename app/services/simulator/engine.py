"""Simulator execution engine foundation.

Exports the deterministic EventDrivenExecutionEngine and SimulatorResult used
by the public backtest orchestrator. Importing this module does not start
workers, read secrets, access market data, or contact brokers.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from datetime import time as datetime_time
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, cast

from app.services.simulator.data_feed import ChronologicalDataFeed
from app.services.simulator.journal import DeterministicJournal
from app.services.simulator.models import (
    CommissionModel,
    FixedLiquidityModel,
    FixedSlippageModel,
    FixedSpreadModel,
    MarginModel,
    SimulatorSymbolSpec,
    SimulatorTick,
    SwapModel,
    VariableSpreadModel,
    VolatilitySlippageModel,
    VolumeSlippageModel,
)
from app.services.strategies import (
    ReadOnlyExecutionStateSnapshot,
    StrategyExecutionContext,
    get_strategy,
    run_strategy_hook,
)
from app.utils.errors import SimLookaheadDetectedError, ValidationError
from app.utils.logger import logger
from app.utils.normalization import normalize_timestamp, utc_now
from app.utils.standard import canonical_json, stable_identifier

if TYPE_CHECKING:
    from app.services.simulator.models import SimulatorBacktestRequestV1

ENGINE_VERSION = "0.8.0-08A"
DEFAULT_AMBIGUOUS_SL_TP_POLICY = "conservative_worst_outcome"
TOOL_RISK_LEVEL = "medium"
SIDE_EFFECT_CLASSIFICATION = "simulated_only"
RESULT_SCHEMA_VERSION = "1.0.0"
DEFAULT_RETENTION_TIER = "research_180_days"
PHASE1_ASSET_CLASS = "FX"
VOLUME_STEP_EPSILON = 1e-9
WEEKEND_START_DAY = 5
SESSION_RANGE_PARTS = 2

OrderSide = Literal["buy", "sell"]
RollPolicy = Literal["none", "close_reopen", "adjust_price_series", "calendar_spread"]
DeferredScopeStatus = Literal["deferred", "unsupported", "not_applicable"]
FillPolicy = Literal["FOK", "IOC", "RETURN"]
GapPolicy = Literal["reject", "fill_at_open"]
QueueModel = Literal["none", "configured_queue_ahead"]
VolumeRoundingPolicy = Literal["floor_to_step"]
PendingOrderType = Literal[
    "buy_limit",
    "sell_limit",
    "buy_stop",
    "sell_stop",
    "buy_stop_limit",
    "sell_stop_limit",
]
StopTakeProfitTriggerType = Literal["sl", "tp", "none"]

SIM_ENGINE_ERROR_TAXONOMY = frozenset(
    {
        "SIM_ARBITRARY_CODE_REJECTED",
        "SIM_CALIBRATION_REQUIRED",
        "SIM_CANARY_DIVERGENCE",
        "SIM_CHECKPOINT_INCOMPATIBLE",
        "SIM_COMMISSION_CALCULATION_FAILED",
        "SIM_CONCENTRATION_LIMIT_EXCEEDED",
        "SIM_CORRELATION_LIMIT_EXCEEDED",
        "SIM_DATA_DUPLICATE_TIMESTAMP",
        "SIM_DATA_EMPTY",
        "SIM_DATA_NON_MONOTONIC_TIME",
        "SIM_DATA_PARTIAL",
        "SIM_DATA_PRICE_OUTLIER",
        "SIM_FEATURE_LOOKAHEAD_DETECTED",
        "SIM_FREEZE_LEVEL_VIOLATION",
        "SIM_FX_CROSS_RATE_REJECTED",
        "SIM_GAP_HANDLING_REJECTED",
        "SIM_INTERNAL_ERROR",
        "SIM_INVALID_CONFIG",
        "SIM_INVALID_VOLUME",
        "SIM_IOC_REMAINDER_CANCELLED",
        "SIM_LIQUIDITY_UNAVAILABLE",
        "SIM_LIMIT_QUEUE_NOT_FILLED",
        "SIM_LOOKAHEAD_DETECTED",
        "SIM_MARKET_CLOSED",
        "SIM_MAX_POSITIONS_EXCEEDED",
        "SIM_MARGIN_STOP_OUT",
        "SIM_ORDER_NOT_FOUND",
        "SIM_PARTIAL_FILL_REMAINDER",
        "SIM_PENDING_ORDER_EXPIRED",
        "SIM_PERSISTENCE_FAILED",
        "SIM_QUEUE_LIMIT_EXCEEDED",
        "SIM_RESOURCE_QUOTA_EXCEEDED",
        "SIM_SIZING_FAILED",
        "SIM_SIZING_REQUIRES_STOP_LOSS",
        "SIM_UNSUPPORTED_FILL_POLICY",
        "SIM_UNSUPPORTED_ORDER_TYPE",
        "SIM_VENDOR_DATA_POLICY_VIOLATION",
        "SIM_VOLUME_ABOVE_MAX",
        "SIM_VOLUME_BELOW_MIN",
        "SIM_VOLUME_STEP_MISMATCH",
        "SIM_WORKER_LOST_REQUEUED",
    }
)

DEFERRED_PHASE1_SCOPE: dict[str, DeferredScopeStatus] = {
    "alternative_data": "deferred",
    "canary_infrastructure": "deferred",
    "distributed_workers": "deferred",
    "equity_corporate_actions": "deferred",
    "external_report_distribution": "deferred",
    "feature_store": "deferred",
    "futures_rollover_production_realism": "deferred",
    "non_fx_production_realism": "deferred",
    "perpetual_funding_production_realism": "deferred",
    "production_promotion_automation": "deferred",
    "regulatory_tax_engine": "deferred",
    "synthetic_transaction_monitoring": "deferred",
}


@dataclass(frozen=True, slots=True)
class ExecutionLatencyModel:
    """Configurable execution latency model.

    Args:
        strategy_compute_ms: Strategy computation delay.
        broker_routing_ms: Broker or network routing delay.
        venue_gateway_ms: Venue or exchange gateway delay.
        matching_engine_ms: Matching-engine delay.

    Raises:
        ValidationError: If any latency component is negative.
    """

    strategy_compute_ms: float = 0.0
    broker_routing_ms: float = 0.0
    venue_gateway_ms: float = 0.0
    matching_engine_ms: float = 0.0

    def __post_init__(self) -> None:
        """Validate latency components."""
        components = (
            self.strategy_compute_ms,
            self.broker_routing_ms,
            self.venue_gateway_ms,
            self.matching_engine_ms,
        )
        if any(component < 0 for component in components):
            raise ValidationError(
                "execution latency components must be non-negative.",
                code="SIM_INVALID_CONFIG",
            )

    @property
    def total_ms(self) -> float:
        """Return total configured latency.

        Returns:
            float: Sum of all latency components.
        """
        return round(
            self.strategy_compute_ms
            + self.broker_routing_ms
            + self.venue_gateway_ms
            + self.matching_engine_ms,
            6,
        )

    def to_dict(self) -> dict[str, float]:
        """Serialize latency model as JSON-compatible data.

        Returns:
            dict[str, float]: Latency model payload.
        """
        return {**asdict(self), "total_ms": self.total_ms}


@dataclass(frozen=True, slots=True)
class EngineOrder:
    """Engine-owned order record.

    Args:
        order_id: Deterministic order id.
        symbol: Symbol name.
        side: Buy or sell side.
        requested_volume: Requested volume in lots.
        filled_volume: Filled volume in lots.
        status: Order lifecycle status.
        created_at: UTC creation timestamp.
        time_in_force: Time-in-force policy.
        order_price: Optional pending order price.
        stop_limit_price: Optional stop-limit activation price.
        expiry: Optional expiry timestamp.
        expiration_mode: Expiration mode label.
        parent_order_id: Optional parent order id.
        order_type: Order type label.
        sl: Optional stop-loss price.
        tp: Optional take-profit price.
        trailing_stop_points: Optional configured trailing stop distance.
        pegged_reference: Optional configured pegged-order reference.
        raw_requested_volume: Raw requested volume before normalization.
        volume_rounding_policy: Volume rounding policy used.
        volume_adjusted: Whether requested volume was adjusted.
    """

    order_id: str
    symbol: str
    side: OrderSide
    requested_volume: float
    filled_volume: float
    status: str
    created_at: str
    time_in_force: str = "GTC"
    order_price: float | None = None
    stop_limit_price: float | None = None
    expiry: str | None = None
    expiration_mode: str = "GTC"
    parent_order_id: str | None = None
    order_type: str = "market"
    sl: float | None = None
    tp: float | None = None
    trailing_stop_points: float | None = None
    pegged_reference: str | None = None
    raw_requested_volume: float | None = None
    volume_rounding_policy: str = "floor_to_step"
    volume_adjusted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert order to dict."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PendingOrderTriggerResult:
    """Deterministic pending-order trigger evaluation."""

    order_id: str
    order_type: str
    triggered: bool
    activated: bool
    reference_price: float
    fill_price: float | None
    reason: str
    code: str | None = None


@dataclass(frozen=True, slots=True)
class StopTakeProfitTrigger:
    """Deterministic SL/TP trigger evaluation for an open position."""

    position_id: str
    trigger_type: StopTakeProfitTriggerType
    triggered: bool
    price: float | None
    reason: str
    code: str | None = None


@dataclass(frozen=True, slots=True)
class TrailingStopUpdate:
    """Deterministic trailing-stop repricing decision."""

    position_id: str
    updated: bool
    previous_sl: float | None
    new_sl: float | None
    reason: str


@dataclass(frozen=True, slots=True)
class PeggedOrderPrice:
    """Deterministic pegged-order price resolution."""

    pegged_reference: str
    price: float
    reason: str


@dataclass(frozen=True, slots=True)
class VolumeNormalizationResult:
    """Deterministic volume normalization record."""

    raw_volume: float
    normalized_volume: float
    rounding_policy: VolumeRoundingPolicy
    adjusted: bool
    symbol: str


@dataclass(frozen=True, slots=True)
class StopOutEvaluation:
    """Deterministic account stop-out gate result."""

    status: Literal["pass", "blocked"]
    margin_level_percent: float | None
    stopout_level_percent: float
    code: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class EngineDeal:
    """Engine-owned deal record."""

    deal_id: str
    order_id: str
    symbol: str
    side: OrderSide
    volume: float
    price: float
    commission: float
    margin: float
    executed_at: str
    position_id: str
    deal_reason: str = "market_order"
    deal_direction: str = "entry"
    diagnostic_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert deal to dict."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EnginePosition:
    """Engine-owned open position record."""

    position_id: str
    symbol: str
    side: OrderSide
    volume: float
    average_price: float
    margin: float
    opened_at: str
    sl: float | None = None
    tp: float | None = None
    trailing_stop_points: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert position to dict."""
        return asdict(self)


@dataclass(slots=True)
class AccountLedger:
    """Base and native-currency accounting state owned by the engine.

    Args:
        base_currency: Account base currency.
        balance_base: Cash balance in base currency.

    Raises:
        No exceptions are raised during construction.
    """

    base_currency: str
    balance_base: float
    realized_pnl_base: float = 0.0
    unrealized_pnl_base: float = 0.0
    commission_base: float = 0.0
    swap_base: float = 0.0
    borrow_fee_base: float = 0.0
    dividend_cashflow_base: float = 0.0
    futures_roll_pnl_base: float = 0.0
    perpetual_funding_base: float = 0.0
    margin_base: float = 0.0
    native_cash_balances: dict[str, float] = field(default_factory=dict)
    native_realized_pnl: dict[str, float] = field(default_factory=dict)
    native_unrealized_pnl: dict[str, float] = field(default_factory=dict)
    native_commissions: dict[str, float] = field(default_factory=dict)
    native_swap: dict[str, float] = field(default_factory=dict)
    native_borrow_fees: dict[str, float] = field(default_factory=dict)
    native_dividend_cashflows: dict[str, float] = field(default_factory=dict)
    native_futures_roll_pnl: dict[str, float] = field(default_factory=dict)
    native_perpetual_funding: dict[str, float] = field(default_factory=dict)
    native_margin: dict[str, float] = field(default_factory=dict)

    @property
    def nav_base(self) -> float:
        """Return portfolio NAV in base currency.

        Returns:
            float: Balance plus unrealized PnL minus accrued costs.
        """
        return round(
            self.balance_base
            + self.unrealized_pnl_base
            + self.realized_pnl_base
            - self.commission_base
            + self.swap_base
            - self.borrow_fee_base
            + self.dividend_cashflow_base
            + self.futures_roll_pnl_base
            + self.perpetual_funding_base,
            10,
        )

    @property
    def free_margin_base(self) -> float:
        """Return base-currency free margin."""
        return round(self.nav_base - self.margin_base, 10)

    @property
    def margin_level_percent(self) -> float | None:
        """Return margin level percentage, or None without used margin."""
        if self.margin_base <= 0:
            return None
        return round((self.nav_base / self.margin_base) * 100, 10)

    def apply_deal(
        self,
        *,
        currency: str,
        commission: float,
        margin: float,
    ) -> None:
        """Apply an executed deal's immediate cashflow effects.

        Args:
            currency: Native cashflow currency.
            commission: Commission amount.
            margin: Required margin amount.

        Returns:
            None.
        """
        self.commission_base = round(self.commission_base + commission, 10)
        self.margin_base = round(self.margin_base + margin, 10)
        self.balance_base = round(self.balance_base - commission, 10)
        self.native_commissions[currency] = round(
            self.native_commissions.get(currency, 0.0) + commission,
            10,
        )
        self.native_margin[currency] = round(
            self.native_margin.get(currency, 0.0) + margin,
            10,
        )
        self.native_cash_balances[currency] = round(
            self.native_cash_balances.get(currency, 0.0) - commission,
            10,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize account state as JSON-compatible data.

        Returns:
            dict[str, Any]: Account ledger payload.
        """
        payload = asdict(self)
        payload["nav_base"] = self.nav_base
        payload["free_margin_base"] = self.free_margin_base
        payload["margin_level_percent"] = self.margin_level_percent
        return payload


@dataclass(frozen=True, slots=True)
class EngineStateSnapshot:
    """Read-only snapshot of engine-owned containers."""

    positions: MappingProxyType[str, EnginePosition]
    orders: MappingProxyType[str, EngineOrder]
    deals: MappingProxyType[str, EngineDeal]
    account: dict[str, Any]


@dataclass(frozen=True, slots=True)
class JournalArtifactManifest:
    """Canonical journal manifest sidecar payload.

    Args:
        filename: Expected manifest filename.
        config_hash: Configuration hash.
        data_manifest_hash: Data manifest hash.
        engine_version: Engine version.
        schema_version: Manifest schema version.
        artifact_checksums: Checksums for produced artifacts.
        retention_tier: Retention tier label.

    Raises:
        ValidationError: If required hash or retention fields are missing.
    """

    filename: str
    config_hash: str
    data_manifest_hash: str
    engine_version: str
    schema_version: str = RESULT_SCHEMA_VERSION
    artifact_checksums: dict[str, str] = field(default_factory=dict)
    retention_tier: str = DEFAULT_RETENTION_TIER

    def __post_init__(self) -> None:
        """Validate manifest identifiers."""
        if self.filename != "journal_manifest.json":
            raise ValidationError("journal manifest filename is invalid.")
        if not self.config_hash or not self.data_manifest_hash:
            raise ValidationError("journal manifest hashes are required.")
        if not self.engine_version or not self.retention_tier:
            raise ValidationError("journal manifest metadata is incomplete.")

    def to_dict(self) -> dict[str, Any]:
        """Serialize manifest as JSON-compatible data."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OptimizationWorkUnit:
    """Deterministic optimization work-unit key.

    Args:
        work_unit_id: Stable work-unit id.
        strategy_id: Strategy identifier.
        parameter_hash: Parameter hash.
        config_hash: Config hash.
        data_hash: Data hash.
        engine_version: Engine version.
        schema_version: Schema version.

    Raises:
        ValidationError: If any key field is empty.
    """

    work_unit_id: str
    strategy_id: str
    parameter_hash: str
    config_hash: str
    data_hash: str
    engine_version: str
    schema_version: str = RESULT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate work-unit key fields."""
        fields = (
            self.work_unit_id,
            self.strategy_id,
            self.parameter_hash,
            self.config_hash,
            self.data_hash,
            self.engine_version,
            self.schema_version,
        )
        if any(not value for value in fields):
            raise ValidationError("optimization work-unit keys must be complete.")

    def to_dict(self) -> dict[str, str]:
        """Serialize work unit as JSON-compatible data."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResumeCheckpoint:
    """Checkpoint compatibility material for resumed runs."""

    config_hash: str
    data_manifest_hash: str
    engine_version: str
    last_journal_sequence: int
    random_seed_state: str
    checkpoint_compatible: bool = True


@dataclass(frozen=True, slots=True)
class ResumePolicy:
    """Fail-closed resume compatibility policy."""

    maximum_checkpoint_age_seconds: int = 86400
    require_sequence_continuity: bool = True
    automatic_resume_enabled: bool = False
    restart_from_scratch_on_incompatible: bool = True


@dataclass(frozen=True, slots=True)
class ResumeVerification:
    """Result of checkpoint compatibility verification."""

    status: Literal["compatible", "incompatible"]
    code: str | None
    details: str

    def to_dict(self) -> dict[str, str | None]:
        """Serialize resume verification."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RollDecision:
    """Futures-roll decision result."""

    policy: RollPolicy
    action: str
    details: str

    def to_dict(self) -> dict[str, str]:
        """Serialize roll decision."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RunConfigurationArtifact:
    """Immutable run-configuration artifact payload."""

    config_hash: str
    data_authority_manifest_version: str
    broker_profile_version: str
    strategy_version: str
    engine_version: str
    dependency_lock_hash: str
    resource_policy: dict[str, object]
    runtime_flags: dict[str, object]

    def to_dict(self) -> dict[str, Any]:
        """Serialize artifact as JSON-compatible data."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResourceQuota:
    """Simulator resource quota configuration."""

    max_concurrent_runs: int = 1
    max_wall_clock_seconds: int = 300
    max_temporary_storage_bytes: int = 100_000_000
    max_queued_runs: int = 1
    max_worker_count: int = 1

    def __post_init__(self) -> None:
        """Validate quota values."""
        if any(value <= 0 for value in asdict(self).values()):
            raise ValidationError("resource quota values must be positive.")

    def to_dict(self) -> dict[str, int]:
        """Serialize quota configuration."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EnvironmentDiagnostic:
    """Deterministic environment diagnostic summary."""

    dependency_versions: dict[str, str]
    selected_system_libraries: dict[str, str]
    relevant_environment: dict[str, str]
    container_image_digest: str | None
    benchmark_profile_id: str
    environment_hash: str
    drift_warning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize environment diagnostic."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EngineTelemetry:
    """Run-level business telemetry emitted by the engine."""

    run_status: str
    lookahead_violation_count: int
    execution_latency_ms: float
    data_quality_failure_count: int
    persistence_failure_count: int
    queue_depth: int
    quota_rejection_count: int

    def to_dict(self) -> dict[str, int | float | str]:
        """Serialize telemetry metrics."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EngineExtensionPoints:
    """Named internal simulator service extension points."""

    data_quality: str = "deterministic_local"
    tick_generation: str = "deterministic_midpoint"
    spread: str = "fixed_points"
    market_calendar: str = "local_session"
    gaps: str = "policy_gate"
    event_priority: str = "stable_sequence"
    liquidity: str = "fixed_volume"
    slippage: str = "fixed_points"
    matching: str = "market_order"
    fees: str = "per_lot"
    swap: str = "fixed_daily"
    broker_rules: str = "profile_metadata"
    portfolio: str = "engine_owned"
    accounting: str = "engine_ledger"
    compliance: str = "deterministic_gates"
    metrics: str = "summary_metrics"
    optimization: str = "isolated_work_units"
    monte_carlo: str = "future_extension"
    performance: str = "local_quota_checks"

    def to_dict(self) -> dict[str, str]:
        """Serialize extension point names."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RegulatoryScope:
    """Deterministic regulatory engine scope disclosure."""

    first_scope: str = "US equities and ETFs"
    wash_sale_detection: str = "optional_diagnostic"
    tax_awareness: str = "optional_diagnostic"
    fx_production_realistic_requirement: str = "not_applicable"

    def to_dict(self) -> dict[str, str]:
        """Serialize regulatory scope."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CanaryAnalysisResult:
    """Controlled old/new engine comparison result."""

    status: Literal["pass", "fail"]
    code: str | None
    compared_metrics: dict[str, float]
    tolerance: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize canary analysis result."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BrokerRuleProfile:
    """Deterministic broker-rule profile for matching validation."""

    supported_fill_policies: tuple[FillPolicy, ...] = ("FOK", "IOC", "RETURN")
    max_pending_orders: int = 100
    max_positions: int = 100
    hedging_mode: Literal["hedging", "netting"] = "hedging"
    stopout_level_percent: float = 50.0

    def __post_init__(self) -> None:
        """Validate broker-rule settings."""
        if not self.supported_fill_policies:
            raise ValidationError("supported fill policies are required.")
        if self.max_pending_orders <= 0 or self.max_positions <= 0:
            raise ValidationError("broker limits must be positive.")
        if self.stopout_level_percent < 0:
            raise ValidationError("stopout level must be non-negative.")

    def to_dict(self) -> dict[str, Any]:
        """Serialize broker rules."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TradeIntent:
    """Timestamped deterministic trade intent."""

    intent_id: str
    signal_id: str
    timestamp: str
    symbol: str
    side: OrderSide
    requested_volume: float
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize trade intent."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EventPriorityRecord:
    """Replayable event-priority record."""

    event_id: str
    timestamp: str
    priority: int
    sequence: int
    event_type: str

    def to_dict(self) -> dict[str, int | str]:
        """Serialize priority record."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ParentChildLineage:
    """Auditable parent-child order lineage."""

    parent_order_id: str
    child_order_ids: tuple[str, ...]
    fill_ids: tuple[str, ...]
    linkage_metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize order lineage."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EngineDiagnostic:
    """Structured deterministic simulator diagnostic."""

    code: str
    message: str
    field_path: str | None
    severity: Literal["info", "warning", "error"]
    retryable: bool
    details: str

    def __post_init__(self) -> None:
        """Validate diagnostic code."""
        validate_engine_error_code(self.code)

    def to_dict(self) -> dict[str, object]:
        """Serialize diagnostic."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DataQualityDiagnostic:
    """Deterministic market-data quality diagnostic."""

    code: str
    symbol: str | None
    timestamp: str | None
    survivorship_bias_flag: bool
    details: str

    def to_dict(self) -> dict[str, object | None]:
        """Serialize data-quality diagnostic."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MarketHoursConfig:
    """Deterministic market-hours configuration.

    Args:
        session_start: UTC session start as HH:MM.
        session_end: UTC session end as HH:MM.
        timezone: Timezone label; Phase 1 supports UTC-only evaluation.
        weekend_closed: Whether Saturday/Sunday are closed.
        holiday_dates: Closed holiday dates in YYYY-MM-DD.
        is_24_7: Whether the asset trades continuously.
        session_breaks: Closed intraday break ranges as HH:MM-HH:MM.

    Raises:
        ValidationError: If time fields are malformed.
    """

    session_start: str = "00:00"
    session_end: str = "23:59"
    timezone: str = "UTC"
    weekend_closed: bool = True
    holiday_dates: tuple[str, ...] = ()
    is_24_7: bool = False
    session_breaks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate market-hours values."""
        _parse_hhmm(self.session_start)
        _parse_hhmm(self.session_end)
        for session_break in self.session_breaks:
            start, end = _split_session_range(session_break)
            _parse_hhmm(start)
            _parse_hhmm(end)
        if self.timezone != "UTC":
            raise ValidationError(
                "Phase 1 market-hours evaluation supports UTC only.",
                code="SIM_INVALID_CONFIG",
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize market-hours configuration."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MarketSessionState:
    """Market session state at a timestamp."""

    is_open: bool
    reason: str
    code: str | None = None

    def to_dict(self) -> dict[str, str | bool | None]:
        """Serialize session state."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MarketHaltState:
    """Market, exchange, symbol, or limit-state halt indicator."""

    active: bool
    halt_type: Literal[
        "none", "market", "exchange", "symbol", "limit_up", "limit_down"
    ] = "none"
    reason: str = ""

    def to_dict(self) -> dict[str, str | bool]:
        """Serialize halt state."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GapHandlingDecision:
    """Deterministic gap-handling decision."""

    policy: GapPolicy
    action: str
    code: str | None
    details: str

    def to_dict(self) -> dict[str, str | None]:
        """Serialize gap decision."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class LimitOrderQueueConfig:
    """Deterministic limit-order queue configuration."""

    queue_model: QueueModel = "none"
    touch_fill_enabled: bool = False
    queue_ahead_volume: float = 0.0
    queue_ahead_estimation_method: str = "configured"
    fill_allocation_method: Literal["fifo", "pro_rata"] = "fifo"
    minimum_fill_volume: float = 0.0
    partial_fill_policy: Literal["cancel_remainder", "keep_pending"] = (
        "cancel_remainder"
    )

    def __post_init__(self) -> None:
        """Validate queue configuration."""
        if self.queue_ahead_volume < 0 or self.minimum_fill_volume < 0:
            raise ValidationError(
                "queue volume settings must be non-negative.",
                code="SIM_INVALID_CONFIG",
            )

    def to_dict(self) -> dict[str, object]:
        """Serialize queue configuration."""
        return asdict(self)


def build_run_id(request: SimulatorBacktestRequestV1) -> str:
    """Build a deterministic simulator run id.

    Args:
        request: Validated simulator request.

    Returns:
        str: Stable run id for the same configuration and seed inputs.
    """
    material = {
        "schema_version": request.schema_version,
        "strategy_ref": request.strategy_ref,
        "strategy_config": request.strategy_config,
        "symbols": request.symbols,
        "timeframe": request.timeframe,
        "start": request.start,
        "end": request.end,
        "initial_balance": request.initial_balance,
        "models": [
            request.tick_model,
            request.spread_model,
            request.slippage_model,
            request.commission_model,
            request.swap_model,
        ],
    }
    return stable_identifier(material, prefix="simrun")


def build_config_hash(request: SimulatorBacktestRequestV1) -> str:
    """Build a deterministic configuration hash.

    Args:
        request: Validated simulator request.

    Returns:
        str: Stable configuration hash.
    """
    return stable_identifier(asdict(request), prefix="id")


def build_data_manifest_hash(request: SimulatorBacktestRequestV1) -> str:
    """Build a deterministic data manifest hash.

    Args:
        request: Validated simulator request.

    Returns:
        str: Stable data manifest hash.
    """
    return stable_identifier(
        {
            "symbols": request.symbols,
            "start": request.start,
            "end": request.end,
            "authority": request.market_data_authority_ref,
        },
        prefix="id",
    )


def build_journal_artifact_manifest(
    *,
    config_hash: str,
    data_manifest_hash: str,
    engine_version: str,
    journal_checksum: str,
    retention_tier: str = DEFAULT_RETENTION_TIER,
) -> JournalArtifactManifest:
    """Build a canonical journal manifest sidecar.

    Args:
        config_hash: Configuration hash.
        data_manifest_hash: Data manifest hash.
        engine_version: Engine version.
        journal_checksum: Journal payload checksum.
        retention_tier: Retention tier label.

    Returns:
        JournalArtifactManifest: Manifest sidecar payload.
    """
    return JournalArtifactManifest(
        filename="journal_manifest.json",
        config_hash=config_hash,
        data_manifest_hash=data_manifest_hash,
        engine_version=engine_version,
        artifact_checksums={"journal.jsonl": journal_checksum},
        retention_tier=retention_tier,
    )


def build_optimization_work_units(
    request: SimulatorBacktestRequestV1,
    parameter_sets: list[dict[str, object]],
    *,
    engine_version: str = ENGINE_VERSION,
) -> list[OptimizationWorkUnit]:
    """Split optimization parameters into deterministic work units.

    Args:
        request: Validated simulator request.
        parameter_sets: Parameter combinations.
        engine_version: Engine version.

    Returns:
        list[OptimizationWorkUnit]: Deterministic work-unit keys.
    """
    config_hash = build_config_hash(request)
    data_hash = build_data_manifest_hash(request)
    units = []
    for parameters in parameter_sets:
        parameter_hash = stable_identifier(parameters, prefix="id")
        work_unit_id = stable_identifier(
            {
                "strategy_id": request.strategy_ref,
                "parameter_hash": parameter_hash,
                "config_hash": config_hash,
                "data_hash": data_hash,
                "engine_version": engine_version,
                "schema_version": RESULT_SCHEMA_VERSION,
            },
            prefix="simwu",
        )
        units.append(
            OptimizationWorkUnit(
                work_unit_id=work_unit_id,
                strategy_id=request.strategy_ref,
                parameter_hash=parameter_hash,
                config_hash=config_hash,
                data_hash=data_hash,
                engine_version=engine_version,
            )
        )
    return units


def verify_resume_checkpoint(
    checkpoint: ResumeCheckpoint,
    *,
    expected_config_hash: str,
    expected_data_manifest_hash: str,
    expected_engine_version: str,
    expected_next_sequence: int,
    policy: ResumePolicy | None = None,
) -> ResumeVerification:
    """Verify resumed-run compatibility.

    Args:
        checkpoint: Checkpoint material.
        expected_config_hash: Expected config hash.
        expected_data_manifest_hash: Expected data hash.
        expected_engine_version: Expected engine version.
        expected_next_sequence: Expected next journal sequence.
        policy: Optional resume policy.

    Returns:
        ResumeVerification: Compatibility result.
    """
    active_policy = policy or ResumePolicy()
    checks = {
        "config_hash": checkpoint.config_hash == expected_config_hash,
        "data_manifest_hash": (
            checkpoint.data_manifest_hash == expected_data_manifest_hash
        ),
        "engine_version": checkpoint.engine_version == expected_engine_version,
        "checkpoint_compatible": checkpoint.checkpoint_compatible,
        "random_seed_state": bool(checkpoint.random_seed_state),
    }
    if active_policy.require_sequence_continuity:
        checks["journal_sequence"] = (
            checkpoint.last_journal_sequence + 1 == expected_next_sequence
        )
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return ResumeVerification(
            status="incompatible",
            code="SIM_CHECKPOINT_INCOMPATIBLE",
            details=", ".join(failed),
        )
    return ResumeVerification(
        status="compatible",
        code=None,
        details="checkpoint is compatible",
    )


def decide_roll_action(policy: RollPolicy) -> RollDecision:
    """Resolve a deterministic futures-roll policy.

    Args:
        policy: Roll policy.

    Returns:
        RollDecision: Roll action and disclosure.

    Raises:
        ValidationError: If policy is unsupported.
    """
    actions = {
        "none": ("none", "roll engine disabled"),
        "close_reopen": ("close_reopen", "close expiring and reopen next contract"),
        "adjust_price_series": ("adjust_price_series", "adjust historical prices"),
        "calendar_spread": ("calendar_spread", "simulate calendar-spread execution"),
    }
    if policy not in actions:
        raise ValidationError("roll policy is unsupported.", code="SIM_INVALID_CONFIG")
    action, details = actions[policy]
    return RollDecision(policy=policy, action=action, details=details)


def build_run_configuration_artifact(
    request: SimulatorBacktestRequestV1,
    *,
    config_hash: str,
    engine_version: str = ENGINE_VERSION,
) -> RunConfigurationArtifact:
    """Build immutable run-configuration material.

    Args:
        request: Validated simulator request.
        config_hash: Configuration hash.
        engine_version: Engine version.

    Returns:
        RunConfigurationArtifact: Immutable configuration payload.
    """
    metadata = request.metadata
    return RunConfigurationArtifact(
        config_hash=config_hash,
        data_authority_manifest_version=str(
            metadata.get("data_authority_manifest_version", "local_synthetic_v1")
        ),
        broker_profile_version=str(
            metadata.get("broker_profile_version", request.broker_profile_ref)
        ),
        strategy_version=str(metadata.get("strategy_version", request.strategy_ref)),
        engine_version=engine_version,
        dependency_lock_hash=str(metadata.get("dependency_lock_hash", "unlocked")),
        resource_policy=dict(ResourceQuota().to_dict()),
        runtime_flags={
            "journal_persistence": request.journal_persistence,
            "realism_profile": request.realism_profile,
            "asset_class": str(metadata.get("asset_class", PHASE1_ASSET_CLASS)),
        },
    )


def build_environment_diagnostic(
    *,
    benchmark_profile_id: str = "local_unverified",
    certified_environment_hash: str | None = None,
) -> EnvironmentDiagnostic:
    """Build deterministic local environment diagnostic metadata.

    Args:
        benchmark_profile_id: Benchmark profile id.
        certified_environment_hash: Optional certified hash for drift checking.

    Returns:
        EnvironmentDiagnostic: Environment diagnostic payload.
    """
    dependency_versions = {"python": sys.version.split()[0]}
    selected_system_libraries = {"platform": sys.platform}
    relevant_environment: dict[str, str] = {}
    material = {
        "dependency_versions": dependency_versions,
        "selected_system_libraries": selected_system_libraries,
        "benchmark_profile_id": benchmark_profile_id,
    }
    environment_hash = stable_identifier(material, prefix="env")
    drift = (
        "SIM_ENVIRONMENT_DRIFT_WARNING"
        if certified_environment_hash not in {None, environment_hash}
        else None
    )
    return EnvironmentDiagnostic(
        dependency_versions=dependency_versions,
        selected_system_libraries=selected_system_libraries,
        relevant_environment=relevant_environment,
        container_image_digest=None,
        benchmark_profile_id=benchmark_profile_id,
        environment_hash=environment_hash,
        drift_warning=drift,
    )


def compare_canary_metrics(
    old_metrics: dict[str, float],
    new_metrics: dict[str, float],
    *,
    tolerance: float,
) -> CanaryAnalysisResult:
    """Compare old/new engine metrics for canary equivalence.

    Args:
        old_metrics: Baseline metric values.
        new_metrics: Candidate metric values.
        tolerance: Maximum absolute divergence.

    Returns:
        CanaryAnalysisResult: Pass/fail comparison result.

    Raises:
        ValidationError: If tolerance is negative.
    """
    if tolerance < 0:
        raise ValidationError("canary tolerance must be non-negative.")
    compared = {}
    status: Literal["pass", "fail"] = "pass"
    for name, old_value in old_metrics.items():
        new_value = new_metrics.get(name)
        if new_value is None:
            continue
        delta = abs(new_value - old_value)
        compared[name] = round(delta, 10)
        if delta > tolerance:
            status = "fail"
    return CanaryAnalysisResult(
        status=status,
        code=None if status == "pass" else "SIM_CANARY_DIVERGENCE",
        compared_metrics=compared,
        tolerance=tolerance,
    )


def can_batch_ticks(*, possible_events_before_next_boundary: bool) -> bool:
    """Return whether tick batching can preserve event semantics.

    Args:
        possible_events_before_next_boundary: Whether execution, risk,
            accounting, session, rollover, or compliance events can occur.

    Returns:
        bool: True when batching is safe.
    """
    return not possible_events_before_next_boundary


def validate_phase1_scope(metadata: dict[str, object]) -> None:
    """Fail closed for unsupported future-scope features.

    Args:
        metadata: Request metadata.

    Returns:
        None.

    Raises:
        ValidationError: If a deferred scope is explicitly requested.
    """
    requested = metadata.get("requested_future_scope", ())
    if not isinstance(requested, list | tuple | set):
        return
    unsupported = [
        str(item) for item in requested if str(item) in DEFERRED_PHASE1_SCOPE
    ]
    if unsupported:
        raise ValidationError(
            "requested simulator scope is deferred for Phase 1.",
            code="SIM_INVALID_CONFIG",
        )


def validate_resource_quota(
    *,
    wall_clock_seconds: float,
    temporary_storage_bytes: int,
    quota: ResourceQuota | None = None,
) -> None:
    """Validate local resource usage against deterministic quotas."""
    active_quota = quota or ResourceQuota()
    if (
        wall_clock_seconds > active_quota.max_wall_clock_seconds
        or temporary_storage_bytes > active_quota.max_temporary_storage_bytes
    ):
        raise ValidationError(
            "simulator resource quota exceeded.",
            code="SIM_RESOURCE_QUOTA_EXCEEDED",
        )


def validate_engine_error_code(code: str) -> None:
    """Validate a simulator engine error-code taxonomy entry."""
    if code not in SIM_ENGINE_ERROR_TAXONOMY:
        raise ValidationError("simulator error code is unsupported.")


def validate_fill_policy(
    fill_policy: str,
    *,
    broker_profile: BrokerRuleProfile | None = None,
) -> FillPolicy:
    """Validate fill policy before matching.

    Args:
        fill_policy: Requested fill policy.
        broker_profile: Optional broker-rule profile.

    Returns:
        FillPolicy: Normalized supported fill policy.

    Raises:
        ValidationError: If the policy is unsupported.
    """
    normalized = fill_policy.upper()
    active_profile = broker_profile or BrokerRuleProfile()
    if normalized not in active_profile.supported_fill_policies:
        logger.warning(
            "simulator unsupported fill policy",
            extra={
                "event_name": "simulator_unsupported_fill_policy",
                "fill_policy": normalized,
                "error_code": "SIM_UNSUPPORTED_FILL_POLICY",
            },
        )
        raise ValidationError(
            "fill policy is unsupported.",
            code="SIM_UNSUPPORTED_FILL_POLICY",
        )
    if normalized == "FOK":
        return "FOK"
    if normalized == "IOC":
        return "IOC"
    return "RETURN"


def normalize_order_volume(
    requested_volume: float,
    symbol_spec: SimulatorSymbolSpec,
    *,
    rounding_policy: VolumeRoundingPolicy = "floor_to_step",
) -> VolumeNormalizationResult:
    """Normalize requested volume using symbol min, max, and step limits.

    Args:
        requested_volume: Raw requested lot volume.
        symbol_spec: Symbol volume metadata.
        rounding_policy: Supported deterministic rounding policy.

    Returns:
        VolumeNormalizationResult: Raw and normalized volume record.

    Raises:
        ValidationError: If volume is outside symbol limits.
    """
    if rounding_policy != "floor_to_step":
        raise ValidationError(
            "volume rounding policy is unsupported.",
            code="SIM_INVALID_CONFIG",
        )
    if requested_volume <= 0:
        raise ValidationError(
            "requested_volume must be greater than zero.",
            code="SIM_INVALID_VOLUME",
        )
    if requested_volume < symbol_spec.lot_min:
        raise ValidationError(
            "requested_volume is below symbol minimum.",
            code="SIM_VOLUME_BELOW_MIN",
        )
    if requested_volume > symbol_spec.lot_max:
        raise ValidationError(
            "requested_volume is above symbol maximum.",
            code="SIM_VOLUME_ABOVE_MAX",
        )
    steps = int(
        (requested_volume - symbol_spec.lot_min + VOLUME_STEP_EPSILON)
        / symbol_spec.lot_step
    )
    normalized_volume = round(symbol_spec.lot_min + steps * symbol_spec.lot_step, 10)
    if normalized_volume <= 0:
        raise ValidationError("final size is invalid.", code="SIM_SIZING_FAILED")
    return VolumeNormalizationResult(
        raw_volume=requested_volume,
        normalized_volume=normalized_volume,
        rounding_policy=rounding_policy,
        adjusted=abs(normalized_volume - requested_volume) > VOLUME_STEP_EPSILON,
        symbol=symbol_spec.symbol,
    )


def validate_stop_prices(
    *,
    side: OrderSide,
    entry_price: float,
    sl: float | None = None,
    tp: float | None = None,
) -> None:
    """Validate stop-loss and take-profit direction against entry price."""
    if side not in {"buy", "sell"} or entry_price <= 0:
        raise ValidationError("stop validation inputs are invalid.")
    if sl is not None and sl <= 0:
        raise ValidationError(
            "stop-loss price must be positive.",
            code="SIM_SIZING_REQUIRES_STOP_LOSS",
        )
    if tp is not None and tp <= 0:
        raise ValidationError(
            "take-profit price must be positive.",
            code="SIM_INVALID_CONFIG",
        )
    if side == "buy":
        invalid_sl = sl is not None and sl >= entry_price
        invalid_tp = tp is not None and tp <= entry_price
    else:
        invalid_sl = sl is not None and sl <= entry_price
        invalid_tp = tp is not None and tp >= entry_price
    if invalid_sl:
        raise ValidationError(
            "stop-loss direction is invalid.",
            code="SIM_SIZING_REQUIRES_STOP_LOSS",
        )
    if invalid_tp:
        raise ValidationError(
            "take-profit direction is invalid.",
            code="SIM_INVALID_CONFIG",
        )


def evaluate_stopout(
    account: AccountLedger,
    *,
    broker_profile: BrokerRuleProfile | None = None,
) -> StopOutEvaluation:
    """Evaluate account margin level against the broker stop-out threshold."""
    active_profile = broker_profile or BrokerRuleProfile()
    margin_level = account.margin_level_percent
    if margin_level is None:
        return StopOutEvaluation(
            status="pass",
            margin_level_percent=None,
            stopout_level_percent=active_profile.stopout_level_percent,
            code=None,
            reason="no_used_margin",
        )
    if margin_level <= active_profile.stopout_level_percent:
        return StopOutEvaluation(
            status="blocked",
            margin_level_percent=margin_level,
            stopout_level_percent=active_profile.stopout_level_percent,
            code="SIM_MARGIN_STOP_OUT",
            reason="margin_level_at_or_below_stopout",
        )
    return StopOutEvaluation(
        status="pass",
        margin_level_percent=margin_level,
        stopout_level_percent=active_profile.stopout_level_percent,
        code=None,
        reason="margin_level_above_stopout",
    )


def validate_position_limit(
    positions: dict[str, EnginePosition],
    *,
    symbol: str,
    side: OrderSide,
    broker_profile: BrokerRuleProfile | None = None,
) -> None:
    """Validate broker maximum-position count before opening a new position."""
    active_profile = broker_profile or BrokerRuleProfile()
    position_id = stable_identifier({"symbol": symbol, "side": side}, prefix="simpos")
    if position_id in positions:
        return
    if len(positions) >= active_profile.max_positions:
        raise ValidationError(
            "maximum position count exceeded.",
            code="SIM_MAX_POSITIONS_EXCEEDED",
        )


def evaluate_market_session(
    timestamp: str,
    *,
    config: MarketHoursConfig | None = None,
    halt_state: MarketHaltState | None = None,
) -> MarketSessionState:
    """Evaluate deterministic market open/closed state.

    Args:
        timestamp: UTC timestamp.
        config: Market-hours configuration.
        halt_state: Optional halt state.

    Returns:
        MarketSessionState: Open/closed state and reason.
    """
    active_config = config or MarketHoursConfig()
    active_halt = halt_state or MarketHaltState(active=False)
    state = MarketSessionState(is_open=True, reason="regular_session")
    if active_halt.active:
        state = MarketSessionState(
            is_open=False,
            reason=active_halt.reason or active_halt.halt_type,
            code="SIM_MARKET_HALT_ACTIVE",
        )
    elif active_config.is_24_7:
        state = MarketSessionState(is_open=True, reason="24_7")
    else:
        moment = normalize_timestamp(timestamp)
        if active_config.weekend_closed and moment.weekday() >= WEEKEND_START_DAY:
            state = MarketSessionState(
                is_open=False,
                reason="weekend",
                code="SIM_MARKET_CLOSED",
            )
        elif moment.date().isoformat() in active_config.holiday_dates:
            state = MarketSessionState(
                is_open=False,
                reason="holiday",
                code="SIM_MARKET_CLOSED",
            )
        elif not _time_in_range(
            moment.time(),
            _parse_hhmm(active_config.session_start),
            _parse_hhmm(active_config.session_end),
        ):
            state = MarketSessionState(
                is_open=False,
                reason="outside_session",
                code="SIM_MARKET_CLOSED",
            )
        else:
            state = _session_break_state(moment, active_config)
    return state


def _session_break_state(
    moment: datetime,
    config: MarketHoursConfig,
) -> MarketSessionState:
    for session_break in config.session_breaks:
        start, end = _split_session_range(session_break)
        if _time_in_range(moment.time(), _parse_hhmm(start), _parse_hhmm(end)):
            return MarketSessionState(
                is_open=False,
                reason="session_break",
                code="SIM_MARKET_CLOSED",
            )
    return MarketSessionState(is_open=True, reason="regular_session")


def decide_gap_handling(
    *,
    policy: GapPolicy,
    ambiguous_sl_tp: bool = False,
) -> GapHandlingDecision:
    """Resolve deterministic gap handling.

    Args:
        policy: Gap policy.
        ambiguous_sl_tp: Whether SL/TP are both crossed in the same gap.

    Returns:
        GapHandlingDecision: Gap action.

    Raises:
        ValidationError: If policy is unsupported.
    """
    if policy == "reject":
        return GapHandlingDecision(
            policy=policy,
            action="reject",
            code="SIM_GAP_HANDLING_REJECTED",
            details="gap execution rejected by policy",
        )
    if policy == "fill_at_open":
        details = (
            "fill at open using conservative_worst_outcome"
            if ambiguous_sl_tp
            else "fill at open"
        )
        return GapHandlingDecision(
            policy=policy,
            action="fill_at_open",
            code=None,
            details=details,
        )
    raise ValidationError("gap policy is unsupported.", code="SIM_INVALID_CONFIG")


def apply_limit_queue(
    requested_volume: float,
    available_volume: float,
    *,
    config: LimitOrderQueueConfig | None = None,
) -> float:
    """Apply deterministic queue-ahead reduction to available volume."""
    active_config = config or LimitOrderQueueConfig()
    if requested_volume <= 0 or available_volume < 0:
        raise ValidationError("queue volume inputs are invalid.")
    if active_config.queue_model == "none" and not active_config.touch_fill_enabled:
        raise ValidationError(
            "limit order touched but queue fill is disabled.",
            code="SIM_LIMIT_QUEUE_NOT_FILLED",
        )
    reduced_available = max(available_volume - active_config.queue_ahead_volume, 0.0)
    fillable = min(requested_volume, reduced_available)
    if fillable < active_config.minimum_fill_volume:
        return 0.0
    return round(fillable, 10)


def validate_pending_order_type(order_type: str) -> PendingOrderType:
    """Validate a pending-order type.

    Args:
        order_type: Pending-order type label.

    Returns:
        PendingOrderType: Supported pending-order type.

    Raises:
        ValidationError: If the order type is unsupported.
    """
    if order_type == "buy_limit":
        return "buy_limit"
    if order_type == "sell_limit":
        return "sell_limit"
    if order_type == "buy_stop":
        return "buy_stop"
    if order_type == "sell_stop":
        return "sell_stop"
    if order_type == "buy_stop_limit":
        return "buy_stop_limit"
    if order_type == "sell_stop_limit":
        return "sell_stop_limit"
    raise ValidationError(
        "pending order type is unsupported.",
        code="SIM_UNSUPPORTED_ORDER_TYPE",
    )


def evaluate_pending_order_trigger(
    order: EngineOrder,
    tick: SimulatorTick,
) -> PendingOrderTriggerResult:
    """Evaluate whether a pending order triggers at the supplied tick.

    Args:
        order: Engine-owned pending order.
        tick: Current bid/ask tick.

    Returns:
        PendingOrderTriggerResult: Deterministic trigger decision.

    Raises:
        ValidationError: If order price inputs are incomplete.
    """
    order_type = validate_pending_order_type(order.order_type)
    price = _require_order_price(order)
    reference_price = tick.ask if order_type.startswith("buy") else tick.bid

    triggered = False
    activated = False
    fill_price: float | None = None
    reason = "not_triggered"
    if order_type == "buy_limit" and reference_price <= price:
        triggered = True
        fill_price = min(reference_price, price)
        reason = "buy_limit_touched"
    elif order_type == "sell_limit" and reference_price >= price:
        triggered = True
        fill_price = max(reference_price, price)
        reason = "sell_limit_touched"
    elif order_type == "buy_stop" and reference_price >= price:
        triggered = True
        fill_price = reference_price
        reason = "buy_stop_touched"
    elif order_type == "sell_stop" and reference_price <= price:
        triggered = True
        fill_price = reference_price
        reason = "sell_stop_touched"
    elif order_type in {"buy_stop_limit", "sell_stop_limit"}:
        return _evaluate_stop_limit_trigger(
            order=order,
            order_type=order_type,
            reference_price=reference_price,
        )

    return PendingOrderTriggerResult(
        order_id=order.order_id,
        order_type=order_type,
        triggered=triggered,
        activated=activated,
        reference_price=reference_price,
        fill_price=fill_price,
        reason=reason,
    )


def evaluate_sl_tp_trigger(
    position: EnginePosition,
    tick: SimulatorTick,
    *,
    sl: float | None = None,
    tp: float | None = None,
    ambiguous_policy: str = DEFAULT_AMBIGUOUS_SL_TP_POLICY,
) -> StopTakeProfitTrigger:
    """Evaluate stop-loss and take-profit trigger state for a position.

    Args:
        position: Engine-owned open position.
        tick: Current bid/ask tick.
        sl: Optional stop-loss price.
        tp: Optional take-profit price.
        ambiguous_policy: Same-tick SL/TP tie-break policy.

    Returns:
        StopTakeProfitTrigger: Trigger decision.

    Raises:
        ValidationError: If an unsupported ambiguity policy is supplied.
    """
    if ambiguous_policy != DEFAULT_AMBIGUOUS_SL_TP_POLICY:
        raise ValidationError(
            "ambiguous SL/TP policy is unsupported.",
            code="SIM_INVALID_CONFIG",
        )
    exit_price = tick.bid if position.side == "buy" else tick.ask
    sl_triggered = sl is not None and (
        exit_price <= sl if position.side == "buy" else exit_price >= sl
    )
    tp_triggered = tp is not None and (
        exit_price >= tp if position.side == "buy" else exit_price <= tp
    )
    if sl_triggered:
        return StopTakeProfitTrigger(
            position_id=position.position_id,
            trigger_type="sl",
            triggered=True,
            price=sl,
            reason=(
                "conservative_sl_selected" if tp_triggered else "stop_loss_touched"
            ),
        )
    if tp_triggered:
        return StopTakeProfitTrigger(
            position_id=position.position_id,
            trigger_type="tp",
            triggered=True,
            price=tp,
            reason="take_profit_touched",
        )
    return StopTakeProfitTrigger(
        position_id=position.position_id,
        trigger_type="none",
        triggered=False,
        price=None,
        reason="not_triggered",
    )


def update_trailing_stop(
    position: EnginePosition,
    tick: SimulatorTick,
    *,
    current_sl: float | None,
    trailing_stop_points: float,
    symbol_spec: SimulatorSymbolSpec | None = None,
) -> TrailingStopUpdate:
    """Compute a deterministic configured trailing-stop update.

    Args:
        position: Engine-owned open position.
        tick: Current bid/ask tick.
        current_sl: Current stop-loss price.
        trailing_stop_points: Trailing distance in points.
        symbol_spec: Optional symbol metadata for point size.

    Returns:
        TrailingStopUpdate: Repricing decision.

    Raises:
        ValidationError: If the trailing stop distance is invalid.
    """
    if trailing_stop_points <= 0:
        raise ValidationError(
            "trailing_stop_points must be positive.",
            code="SIM_INVALID_CONFIG",
        )
    point = (symbol_spec or SimulatorSymbolSpec(symbol=tick.symbol)).point
    distance = trailing_stop_points * point
    candidate = tick.bid - distance if position.side == "buy" else tick.ask + distance
    if current_sl is None:
        return TrailingStopUpdate(
            position_id=position.position_id,
            updated=True,
            previous_sl=None,
            new_sl=round(candidate, 10),
            reason="trailing_stop_initialized",
        )
    if position.side == "buy" and candidate > current_sl:
        return TrailingStopUpdate(
            position_id=position.position_id,
            updated=True,
            previous_sl=current_sl,
            new_sl=round(candidate, 10),
            reason="trailing_stop_raised",
        )
    if position.side == "sell" and candidate < current_sl:
        return TrailingStopUpdate(
            position_id=position.position_id,
            updated=True,
            previous_sl=current_sl,
            new_sl=round(candidate, 10),
            reason="trailing_stop_lowered",
        )
    return TrailingStopUpdate(
        position_id=position.position_id,
        updated=False,
        previous_sl=current_sl,
        new_sl=current_sl,
        reason="trailing_stop_unchanged",
    )


def resolve_pegged_order_price(
    tick: SimulatorTick,
    *,
    pegged_reference: str,
    approved_reference_price: float | None = None,
) -> PeggedOrderPrice:
    """Resolve a configured pegged-order reference to a deterministic price."""
    validate_pegged_order_configuration(
        pegged_reference=pegged_reference,
        configured=True,
    )
    if pegged_reference == "best_bid":
        return PeggedOrderPrice(
            pegged_reference=pegged_reference,
            price=tick.bid,
            reason="pegged_to_best_bid",
        )
    if pegged_reference == "best_ask":
        return PeggedOrderPrice(
            pegged_reference=pegged_reference,
            price=tick.ask,
            reason="pegged_to_best_ask",
        )
    if pegged_reference == "mid":
        return PeggedOrderPrice(
            pegged_reference=pegged_reference,
            price=round((tick.bid + tick.ask) / 2, 10),
            reason="pegged_to_mid",
        )
    if approved_reference_price is None or approved_reference_price <= 0:
        raise ValidationError(
            "approved pegged reference price is required.",
            code="SIM_INVALID_CONFIG",
        )
    return PeggedOrderPrice(
        pegged_reference=pegged_reference,
        price=approved_reference_price,
        reason="pegged_to_approved_reference",
    )


def validate_trailing_stop_configuration(
    *,
    trailing_stop_points: float | None,
    configured: bool,
) -> EngineDiagnostic:
    """Validate whether trailing-stop behavior is configured for simulation."""
    if trailing_stop_points is None:
        return EngineDiagnostic(
            code="SIM_INVALID_CONFIG",
            message="trailing stop not requested",
            field_path="trailing_stop_points",
            severity="info",
            retryable=False,
            details=f"configured={configured}",
        )
    if trailing_stop_points <= 0 or not configured:
        raise ValidationError(
            "trailing stops require an explicit configured model.",
            code="SIM_INVALID_CONFIG",
        )
    return EngineDiagnostic(
        code="SIM_INVALID_CONFIG",
        message="trailing stop configuration accepted",
        field_path="trailing_stop_points",
        severity="info",
        retryable=False,
        details=(
            f"configured={configured}; trailing_stop_points={trailing_stop_points}"
        ),
    )


def validate_pegged_order_configuration(
    *,
    pegged_reference: str | None,
    configured: bool,
) -> EngineDiagnostic:
    """Validate configured pegged-order references."""
    if pegged_reference is None:
        return EngineDiagnostic(
            code="SIM_INVALID_CONFIG",
            message="pegged order not requested",
            field_path="pegged_reference",
            severity="info",
            retryable=False,
            details=f"configured={configured}",
        )
    if pegged_reference not in {"best_bid", "best_ask", "mid", "approved_reference"}:
        raise ValidationError(
            "pegged order reference is unsupported.",
            code="SIM_UNSUPPORTED_ORDER_TYPE",
        )
    if not configured:
        raise ValidationError(
            "pegged orders require an explicit configured model.",
            code="SIM_INVALID_CONFIG",
        )
    return EngineDiagnostic(
        code="SIM_INVALID_CONFIG",
        message="pegged order configuration accepted",
        field_path="pegged_reference",
        severity="info",
        retryable=False,
        details=f"configured={configured}; pegged_reference={pegged_reference}",
    )


def _require_order_price(order: EngineOrder) -> float:
    if order.order_price is None:
        raise ValidationError(
            "pending order price is required.",
            code="SIM_INVALID_CONFIG",
        )
    return order.order_price


def _evaluate_stop_limit_trigger(
    *,
    order: EngineOrder,
    order_type: PendingOrderType,
    reference_price: float,
) -> PendingOrderTriggerResult:
    activation_price = _require_order_price(order)
    if order.stop_limit_price is None:
        raise ValidationError(
            "stop-limit price is required.",
            code="SIM_INVALID_CONFIG",
        )
    if order_type == "buy_stop_limit":
        activated = reference_price >= activation_price
        triggered = activated and reference_price <= order.stop_limit_price
    else:
        activated = reference_price <= activation_price
        triggered = activated and reference_price >= order.stop_limit_price
    return PendingOrderTriggerResult(
        order_id=order.order_id,
        order_type=order_type,
        triggered=triggered,
        activated=activated,
        reference_price=reference_price,
        fill_price=order.stop_limit_price if triggered else None,
        reason=(
            f"{order_type}_filled"
            if triggered
            else f"{order_type}_activated"
            if activated
            else "not_triggered"
        ),
    )


def _parse_hhmm(value: str) -> datetime_time:
    try:
        return datetime.strptime(value, "%H:%M").replace(tzinfo=UTC).time()
    except ValueError as exc:
        raise ValidationError("time must use HH:MM format.") from exc


def _split_session_range(value: str) -> tuple[str, str]:
    parts = value.split("-", maxsplit=1)
    if len(parts) != SESSION_RANGE_PARTS:
        raise ValidationError("session range must use HH:MM-HH:MM format.")
    return parts[0], parts[1]


def _time_in_range(
    current_time: datetime_time,
    start_time: datetime_time,
    end_time: datetime_time,
) -> bool:
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    return current_time >= start_time or current_time <= end_time


def build_trade_intents(
    signals: list[dict[str, object]],
    *,
    seed_material: dict[str, object],
) -> list[TradeIntent]:
    """Convert strategy signals into deterministic timestamped trade intents.

    Args:
        signals: Signal dictionaries with timestamp, symbol, side, and volume.
        seed_material: Deterministic run material.

    Returns:
        list[TradeIntent]: Stable trade intents.

    Raises:
        ValidationError: If any signal is malformed.
    """
    intents = []
    for index, signal in enumerate(signals, start=1):
        timestamp = normalize_timestamp(str(signal.get("timestamp", ""))).isoformat()
        symbol = str(signal.get("symbol", "")).strip()
        side = str(signal.get("side", "")).lower()
        raw_volume = signal.get("volume", 0.0)
        if not isinstance(raw_volume, int | float):
            raise ValidationError(
                "signal volume is invalid.",
                code="SIM_INVALID_CONFIG",
            )
        volume = float(raw_volume)
        if not symbol or side not in {"buy", "sell"} or volume <= 0:
            raise ValidationError("signal is invalid.", code="SIM_INVALID_CONFIG")
        signal_id = str(
            signal.get(
                "signal_id",
                stable_identifier({"signal": signal, "index": index}, prefix="simsig"),
            )
        )
        intent_id = stable_identifier(
            {
                "seed": seed_material,
                "signal_id": signal_id,
                "timestamp": timestamp,
                "symbol": symbol,
                "side": side,
                "volume": volume,
                "index": index,
            },
            prefix="simintent",
        )
        intents.append(
            TradeIntent(
                intent_id=intent_id,
                signal_id=signal_id,
                timestamp=timestamp,
                symbol=symbol,
                side="buy" if side == "buy" else "sell",
                requested_volume=volume,
                metadata={"source": "strategy_signal"},
            )
        )
    return intents


def build_event_priority_order(
    events: list[dict[str, object]],
) -> list[EventPriorityRecord]:
    """Build replayable deterministic event-priority records.

    Args:
        events: Event dictionaries with timestamp, priority, and type.

    Returns:
        list[EventPriorityRecord]: Stable event order.
    """
    records = []
    for index, event in enumerate(events, start=1):
        timestamp = normalize_timestamp(str(event.get("timestamp", ""))).isoformat()
        raw_priority = event.get("priority", 100)
        if not isinstance(raw_priority, int):
            raise ValidationError(
                "event priority is invalid.",
                code="SIM_INVALID_CONFIG",
            )
        priority = raw_priority
        event_type = str(event.get("event_type", "unknown"))
        event_id = stable_identifier(
            {
                "timestamp": timestamp,
                "priority": priority,
                "event_type": event_type,
                "sequence": index,
            },
            prefix="simevent",
        )
        records.append(
            EventPriorityRecord(
                event_id=event_id,
                timestamp=timestamp,
                priority=priority,
                sequence=index,
                event_type=event_type,
            )
        )
    return sorted(
        records,
        key=lambda record: (record.timestamp, record.priority, record.sequence),
    )


def build_parent_child_lineage(
    *,
    parent_order_id: str,
    child_order_ids: tuple[str, ...],
    fill_ids: tuple[str, ...],
    metadata: dict[str, object] | None = None,
) -> ParentChildLineage:
    """Build auditable parent-child order lineage."""
    if not parent_order_id or any(not child for child in child_order_ids):
        raise ValidationError("order lineage ids must be non-empty.")
    return ParentChildLineage(
        parent_order_id=parent_order_id,
        child_order_ids=child_order_ids,
        fill_ids=fill_ids,
        linkage_metadata=metadata or {},
    )


def build_engine_diagnostic(
    *,
    code: str,
    message: str,
    field_path: str | None = None,
    severity: Literal["info", "warning", "error"] = "error",
    retryable: bool = False,
    details: str = "",
) -> EngineDiagnostic:
    """Build and log a deterministic engine diagnostic.

    Args:
        code: SIM error code.
        message: Safe message.
        field_path: Optional field path.
        severity: Diagnostic severity.
        retryable: Whether retry can be attempted safely.
        details: Redacted safe details.

    Returns:
        EngineDiagnostic: Structured diagnostic.
    """
    diagnostic = EngineDiagnostic(
        code=code,
        message=message,
        field_path=field_path,
        severity=severity,
        retryable=retryable,
        details=details,
    )
    logger.warning(
        "simulator diagnostic emitted",
        extra={
            "event_name": "simulator_diagnostic_emitted",
            "error_code": diagnostic.code,
            "severity": diagnostic.severity,
            "field_path": diagnostic.field_path,
        },
    )
    return diagnostic


def build_skipped_trade_diagnostic(
    *,
    code: str,
    reason: str,
    field_path: str | None = None,
) -> EngineDiagnostic:
    """Build a deterministic skipped-trade diagnostic."""
    return build_engine_diagnostic(
        code=code,
        message="Simulator skipped trade.",
        field_path=field_path,
        severity="warning",
        retryable=False,
        details=reason,
    )


def validate_asset_class_scope(asset_class: str) -> None:
    """Validate Phase 1 asset-class scope."""
    if asset_class.upper() != PHASE1_ASSET_CLASS:
        raise ValidationError(
            "asset class is unsupported for Phase 1 production realism.",
            code="SIM_INVALID_CONFIG",
        )


def validate_fractional_volume(
    *,
    quantity: float,
    volume_step: float,
) -> None:
    """Validate fractional quantity support from symbol metadata."""
    if quantity <= 0 or volume_step <= 0:
        raise ValidationError("quantity and volume_step must be positive.")
    rounded_steps = round(quantity / volume_step)
    if abs(quantity - rounded_steps * volume_step) > VOLUME_STEP_EPSILON:
        raise ValidationError(
            "quantity does not match symbol volume step.",
            code="SIM_VOLUME_STEP_MISMATCH",
        )


def deterministic_data_quality_checks(
    ticks: list[SimulatorTick],
    *,
    survivorship_bias_flag: bool = False,
) -> list[DataQualityDiagnostic]:
    """Run deterministic data-quality checks over ticks."""
    if not ticks:
        return [
            DataQualityDiagnostic(
                code="SIM_DATA_EMPTY",
                symbol=None,
                timestamp=None,
                survivorship_bias_flag=survivorship_bias_flag,
                details="no ticks supplied",
            )
        ]
    diagnostics = []
    previous_ts = None
    seen: set[tuple[str, str]] = set()
    for tick in ticks:
        key = (tick.symbol, tick.timestamp)
        if key in seen:
            diagnostics.append(
                DataQualityDiagnostic(
                    code="SIM_DATA_DUPLICATE_TIMESTAMP",
                    symbol=tick.symbol,
                    timestamp=tick.timestamp,
                    survivorship_bias_flag=survivorship_bias_flag,
                    details="duplicate symbol timestamp",
                )
            )
        seen.add(key)
        current_ts = normalize_timestamp(tick.timestamp)
        if previous_ts is not None and current_ts < previous_ts:
            diagnostics.append(
                DataQualityDiagnostic(
                    code="SIM_DATA_NON_MONOTONIC_TIME",
                    symbol=tick.symbol,
                    timestamp=tick.timestamp,
                    survivorship_bias_flag=survivorship_bias_flag,
                    details="timestamps are not monotonic",
                )
            )
        previous_ts = current_ts
    return diagnostics


@dataclass(frozen=True, slots=True)
class SimulatorResult:
    """Canonical simulator result summary.

    Args:
        schema_version: Result schema version.
        run_id: Simulator run id.
        classification: Realism classification.
        started_at: UTC start timestamp.
        completed_at: UTC completion timestamp.
        engine_version: Engine version.
        config_hash: Request configuration hash.
        data_manifest_hash: Data manifest hash.
        broker_profile_id: Broker profile id.
        artifact_manifest: Artifact manifest payload.
        summary_metrics: Summary metrics.
        risk_metrics: Risk metrics.
        cost_summary: Cost summary.
        realism_disclosure: Realism disclosure text.
        data_quality_summary: Data-quality summary.
        metadata: Engine execution metadata.
    """

    schema_version: str
    run_id: str
    classification: str
    started_at: str
    completed_at: str
    engine_version: str
    config_hash: str
    data_manifest_hash: str
    broker_profile_id: str
    artifact_manifest: dict[str, Any]
    summary_metrics: dict[str, float]
    risk_metrics: dict[str, float]
    cost_summary: dict[str, float]
    realism_disclosure: str
    data_quality_summary: dict[str, Any]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize result as JSON-compatible data.

        Returns:
            dict[str, Any]: Result payload.
        """
        return asdict(self)


def _get_float_metadata(metadata: dict[str, object], key: str, default: float) -> float:
    val = metadata.get(key)
    if val is None:
        return default
    try:
        return float(str(val))
    except (ValueError, TypeError):
        return default


def _get_int_metadata(metadata: dict[str, object], key: str, default: int) -> int:
    val = metadata.get(key)
    if val is None:
        return default
    try:
        return int(str(val))
    except (ValueError, TypeError):
        return default


def _get_str_metadata(metadata: dict[str, object], key: str, default: str) -> str:
    val = metadata.get(key)
    if val is None:
        return default
    return str(val)


class EventDrivenExecutionEngine:
    """Deterministic tick-engine foundation for official simulator runs.

    Args:
        engine_version: Engine version label.

    Raises:
        No exceptions are raised during construction.
    """

    def __init__(self, *, engine_version: str = ENGINE_VERSION) -> None:
        """Initialize the engine without stateful external resources."""
        self.engine_version = engine_version
        self.positions: dict[str, EnginePosition] = {}
        self.orders: dict[str, EngineOrder] = {}
        self.deals: dict[str, EngineDeal] = {}
        self.latest_prices: dict[str, SimulatorTick] = {}
        self.symbol_specs: dict[str, SimulatorSymbolSpec] = {}
        self.request_metadata: dict[str, Any] = {}
        self.pending_intents: list[Any] = []
        self.equity_curve: list[dict[str, Any]] = []
        self.closed_trades: list[dict[str, Any]] = []
        self.account = AccountLedger(base_currency="USD", balance_base=0.0)

    def snapshot(self) -> EngineStateSnapshot:
        """Return a read-only snapshot of engine-owned state.

        Returns:
            EngineStateSnapshot: Immutable container views for strategy reads.

        Raises:
            No exceptions are raised.
        """
        return EngineStateSnapshot(
            positions=MappingProxyType(dict(self.positions)),
            orders=MappingProxyType(dict(self.orders)),
            deals=MappingProxyType(dict(self.deals)),
            account=self.account.to_dict(),
        )

    def _build_read_only_state(
        self, current_time: datetime
    ) -> ReadOnlyExecutionStateSnapshot:
        """Construct read-only state snapshot for strategy hook consumption."""
        open_positions = []
        for pos in self.positions.values():
            side_str = "BUY" if pos.side == "buy" else "SELL"
            type_int = 0 if pos.side == "buy" else 1
            try:
                ticket_int = int(pos.position_id)
            except ValueError:
                ticket_int = abs(hash(pos.position_id)) % 100000000

            open_positions.append(
                {
                    "position_id": pos.position_id,
                    "symbol": pos.symbol,
                    "side": side_str,
                    "type": type_int,
                    "ticket": ticket_int,
                    "volume": pos.volume,
                    "average_price": pos.average_price,
                    "margin": pos.margin,
                    "opened_at": pos.opened_at,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "trailing_stop_points": pos.trailing_stop_points,
                    "magic": None,
                }
            )

        fills = []
        for deal in self.deals.values():
            side_str = "BUY" if deal.side == "buy" else "SELL"
            type_int = 0 if deal.side == "buy" else 1
            try:
                ticket_int = int(deal.deal_id)
            except ValueError:
                ticket_int = abs(hash(deal.deal_id)) % 100000000

            fills.append(
                {
                    "deal_id": deal.deal_id,
                    "order_id": deal.order_id,
                    "symbol": deal.symbol,
                    "side": side_str,
                    "type": type_int,
                    "ticket": ticket_int,
                    "volume": deal.volume,
                    "price": deal.price,
                    "commission": deal.commission,
                    "margin": deal.margin,
                    "executed_at": deal.executed_at,
                    "position_id": deal.position_id,
                    "deal_reason": deal.deal_reason,
                    "deal_direction": deal.deal_direction,
                }
            )

        snap_id = stable_identifier(
            f"{current_time.isoformat()}-{len(self.positions)}", prefix="snap"
        )
        return ReadOnlyExecutionStateSnapshot(
            snapshot_id=snap_id,
            snapshot_at=current_time,
            source_module="simulation",
            fills=fills,
            open_positions=open_positions,
        )

    def _find_cross_rates(
        self,
        from_currency: str,
        to_currency: str,
        currencies: set[str],
        get_mid: Callable[[str], float | None],
    ) -> list[float]:
        """Find synthesized cross rates from other active currencies."""
        synthesized_rates = []
        for x in currencies:
            if x in (from_currency, to_currency):
                continue
            r1_dir = get_mid(f"{from_currency}{x}")
            r1_inv = get_mid(f"{x}{from_currency}")
            r1 = (
                r1_dir
                if r1_dir is not None
                else (1.0 / r1_inv if r1_inv is not None else None)
            )
            if r1 is None:
                continue

            r2_dir = get_mid(f"{x}{to_currency}")
            r2_inv = get_mid(f"{to_currency}{x}")
            r2 = (
                r2_dir
                if r2_dir is not None
                else (1.0 / r2_inv if r2_inv is not None else None)
            )
            if r2 is None:
                continue

            synthesized_rates.append(r1 * r2)
        return synthesized_rates

    def _resolve_conversion_rate(self, from_currency: str, to_currency: str) -> float:  # noqa: C901
        if from_currency == to_currency:
            return 1.0

        def get_mid(symbol: str) -> float | None:
            tick = self.latest_prices.get(symbol)
            if tick is not None:
                return (tick.bid + tick.ask) / 2.0
            return None

        direct_symbol = f"{from_currency}{to_currency}"
        direct_rate = get_mid(direct_symbol)

        inverse_symbol = f"{to_currency}{from_currency}"
        inverse_rate = get_mid(inverse_symbol)
        if inverse_rate is not None:
            inverse_rate = 1.0 / inverse_rate

        reference_rate = direct_rate if direct_rate is not None else inverse_rate

        currencies = set()
        fx_symbol_length = 6
        for symbol in self.latest_prices:
            if len(symbol) == fx_symbol_length:
                currencies.add(symbol[:3])
                currencies.add(symbol[3:])

        synthesized_rates = self._find_cross_rates(
            from_currency, to_currency, currencies, get_mid
        )

        if not synthesized_rates and reference_rate is None:
            err_msg = f"No conversion path from {from_currency} to {to_currency}"
            raise ValidationError(
                err_msg,
                code="SIM_FX_CROSS_RATE_REJECTED",
            )

        synthesized_rate = synthesized_rates[0] if synthesized_rates else None

        if reference_rate is not None:
            if synthesized_rate is not None:
                max_skew_bps = float(
                    self.request_metadata.get("max_cross_rate_skew_bps", 25.0)
                )
                skew = abs(synthesized_rate - reference_rate) / reference_rate
                if skew > max_skew_bps * 0.0001:
                    err_msg = (
                        f"Cross-rate skew limit exceeded for conversion from "
                        f"{from_currency} to {to_currency}."
                    )
                    raise ValidationError(
                        err_msg,
                        code="SIM_FX_CROSS_RATE_REJECTED",
                    )
            return reference_rate

        if synthesized_rate is None:
            raise ValidationError(
                "No conversion path found",
                code="SIM_FX_CROSS_RATE_REJECTED",
            )
        return synthesized_rate

    def _recalculate_account_ledger(self) -> None:
        self.account.unrealized_pnl_base = 0.0
        self.account.native_unrealized_pnl.clear()
        self.account.margin_base = 0.0
        self.account.native_margin.clear()

        native_margin_sums: dict[str, float] = {}
        native_pnl_sums: dict[str, float] = {}

        for pos in self.positions.values():
            spec = self.symbol_specs.get(pos.symbol) or SimulatorSymbolSpec(
                symbol=pos.symbol
            )
            tick = self.latest_prices.get(pos.symbol)
            if tick is None:
                tick = SimulatorTick(
                    timestamp=pos.opened_at,
                    symbol=pos.symbol,
                    bid=pos.average_price,
                    ask=pos.average_price,
                )

            direction = 1.0 if pos.side == "buy" else -1.0
            current_price = tick.bid if pos.side == "buy" else tick.ask
            floating_pnl_quote = round(
                (current_price - pos.average_price)
                * pos.volume
                * spec.contract_size
                * direction,
                10,
            )

            qc = spec.quote_currency
            native_pnl_sums[qc] = round(
                native_pnl_sums.get(qc, 0.0) + floating_pnl_quote, 10
            )
            native_margin_sums[qc] = round(
                native_margin_sums.get(qc, 0.0) + pos.margin, 10
            )

            rate = self._resolve_conversion_rate(qc, self.account.base_currency)
            self.account.unrealized_pnl_base = round(
                self.account.unrealized_pnl_base + floating_pnl_quote * rate, 10
            )
            self.account.margin_base = round(
                self.account.margin_base + pos.margin * rate, 10
            )

        for qc, pnl in native_pnl_sums.items():
            self.account.native_unrealized_pnl[qc] = pnl
        for qc, marg in native_margin_sums.items():
            self.account.native_margin[qc] = marg

    def place_pending_order(
        self,
        *,
        tick: SimulatorTick,
        order_type: str,
        requested_volume: float,
        order_price: float,
        stop_limit_price: float | None = None,
        time_in_force: str = "GTC",
        expiry: str | None = None,
        expiration_mode: str = "GTC",
        sl: float | None = None,
        tp: float | None = None,
        trailing_stop_points: float | None = None,
        pegged_reference: str | None = None,
        broker_profile: BrokerRuleProfile | None = None,
    ) -> EngineOrder:
        """Create an engine-owned pending order.

        Args:
            tick: Current tick used for deterministic order timestamping.
            order_type: Supported pending-order type.
            requested_volume: Requested volume in lots.
            order_price: Limit, stop, or stop-limit activation price.
            stop_limit_price: Stop-limit limit price when applicable.
            time_in_force: Fill policy used when the order executes.
            expiry: Optional order expiry timestamp.
            expiration_mode: Expiration mode label.
            sl: Optional stop-loss price.
            tp: Optional take-profit price.
            trailing_stop_points: Optional trailing-stop distance.
            pegged_reference: Optional pegged-order reference.
            broker_profile: Optional broker-rule profile.

        Returns:
            EngineOrder: Pending order stored in engine state.

        Raises:
            ValidationError: If inputs or broker limits are invalid.
        """
        pending_type = validate_pending_order_type(order_type)
        if requested_volume <= 0:
            raise ValidationError(
                "requested_volume must be greater than zero.",
                code="SIM_INVALID_VOLUME",
            )
        if order_price <= 0:
            raise ValidationError(
                "pending order price must be positive.",
                code="SIM_INVALID_CONFIG",
            )
        if pending_type.endswith("stop_limit") and (
            stop_limit_price is None or stop_limit_price <= 0
        ):
            raise ValidationError(
                "stop-limit orders require a positive stop_limit_price.",
                code="SIM_INVALID_CONFIG",
            )
        validate_fill_policy(time_in_force, broker_profile=broker_profile)
        active_profile = broker_profile or BrokerRuleProfile()
        pending_count = sum(
            1 for order in self.orders.values() if order.status == "pending"
        )
        if pending_count >= active_profile.max_pending_orders:
            raise ValidationError(
                "maximum pending-order count exceeded.",
                code="SIM_QUEUE_LIMIT_EXCEEDED",
            )
        side: OrderSide = "buy" if pending_type.startswith("buy") else "sell"
        created_at = normalize_timestamp(tick.timestamp).isoformat()
        order_id = stable_identifier(
            {
                "symbol": tick.symbol,
                "order_type": pending_type,
                "side": side,
                "requested_volume": requested_volume,
                "order_price": order_price,
                "stop_limit_price": stop_limit_price,
                "timestamp": created_at,
                "order_index": len(self.orders) + 1,
            },
            prefix="simord",
        )
        order = EngineOrder(
            order_id=order_id,
            symbol=tick.symbol,
            side=side,
            requested_volume=round(requested_volume, 10),
            filled_volume=0.0,
            status="pending",
            created_at=created_at,
            time_in_force=validate_fill_policy(
                time_in_force,
                broker_profile=broker_profile,
            ),
            order_price=order_price,
            stop_limit_price=stop_limit_price,
            expiry=normalize_timestamp(expiry).isoformat() if expiry else None,
            expiration_mode=expiration_mode,
            order_type=pending_type,
            sl=sl,
            tp=tp,
            trailing_stop_points=trailing_stop_points,
            pegged_reference=pegged_reference,
            raw_requested_volume=requested_volume,
            volume_adjusted=False,
        )
        self.orders[order_id] = order
        logger.info(
            "simulator pending order placed",
            extra={
                "event_name": "simulator_pending_order_placed",
                "order_id": order_id,
                "order_type": pending_type,
                "symbol": tick.symbol,
            },
        )
        return order

    def trigger_pending_orders(
        self,
        *,
        tick: SimulatorTick,
        symbol_spec: SimulatorSymbolSpec | None = None,
        liquidity_model: FixedLiquidityModel | None = None,
        slippage_model: (
            FixedSlippageModel | VolatilitySlippageModel | VolumeSlippageModel | None
        ) = None,
        commission_model: CommissionModel | None = None,
        margin_model: MarginModel | None = None,
        market_hours: MarketHoursConfig | None = None,
        halt_state: MarketHaltState | None = None,
    ) -> list[EngineDeal]:
        """Trigger pending orders touched by the current tick.

        Args:
            tick: Current executable bid/ask tick.
            symbol_spec: Optional symbol metadata.
            liquidity_model: Optional liquidity model.
            slippage_model: Optional slippage model.
            commission_model: Optional commission model.
            margin_model: Optional margin model.
            market_hours: Optional market-hours configuration.
            halt_state: Optional halt state.

        Returns:
            list[EngineDeal]: Deals created from triggered pending orders.
        """
        deals: list[EngineDeal] = []
        pending_orders = [
            order
            for order in self.orders.values()
            if order.status in {"pending", "activated"} and order.symbol == tick.symbol
        ]
        for order in pending_orders:
            result = evaluate_pending_order_trigger(order, tick)
            if (
                result.activated
                and not result.triggered
                and order.status != "activated"
            ):
                self.orders[order.order_id] = replace(order, status="activated")
                continue
            if not result.triggered:
                continue
            remaining_volume = round(order.requested_volume - order.filled_volume, 10)
            deal = self.execute_market_order(
                tick=tick,
                side=order.side,
                requested_volume=remaining_volume,
                symbol_spec=symbol_spec,
                liquidity_model=liquidity_model,
                slippage_model=slippage_model,
                commission_model=commission_model,
                margin_model=margin_model,
                time_in_force=order.time_in_force,
                market_hours=market_hours,
                halt_state=halt_state,
            )
            deals.append(deal)
            self.orders[order.order_id] = replace(
                order,
                filled_volume=round(order.filled_volume + deal.volume, 10),
                status=(
                    "filled"
                    if deal.volume >= remaining_volume
                    else "partially_filled_remainder_pending"
                ),
            )
        return deals

    def run(  # noqa: C901, PLR0912, PLR0915
        self,
        request: SimulatorBacktestRequestV1,
        *,
        journal: DeterministicJournal | None = None,
    ) -> SimulatorResult:
        """Run a deterministic tick-based 08A simulator pass.

        Args:
            request: Validated backtest request.
            journal: Optional caller-owned journal.

        Returns:
            SimulatorResult: Deterministic foundation result.

        Raises:
            SimLookaheadDetectedError: If request metadata violates
                first-tick no-lookahead boundaries.
            ValidationError: Propagated from lower-level validated models.
        """
        execution_start = time.perf_counter()
        started_at = utc_now().isoformat()
        self._reset_state(request)
        validate_phase1_scope(request.metadata)
        self._validate_first_tick_lookahead(request)
        run_id = build_run_id(request)
        config_hash = build_config_hash(request)
        data_manifest_hash = build_data_manifest_hash(request)
        latency_model = self._latency_model_from_metadata(request.metadata)
        ambiguous_policy = str(
            request.metadata.get(
                "ambiguous_sl_tp_policy",
                DEFAULT_AMBIGUOUS_SL_TP_POLICY,
            )
        )
        if ambiguous_policy != DEFAULT_AMBIGUOUS_SL_TP_POLICY:
            raise ValidationError(
                "ambiguous_sl_tp_policy is unsupported.",
                code="SIM_INVALID_CONFIG",
            )
        active_journal = journal or DeterministicJournal(
            run_id=run_id,
            config_hash=config_hash,
            data_manifest_hash=data_manifest_hash,
            engine_version=self.engine_version,
        )
        active_journal.append(
            "simulator.run_started",
            {
                "request_id": request.request_id,
                "strategy_ref": request.strategy_ref,
                "symbols": list(request.symbols),
                "engine_version": self.engine_version,
            },
        )
        active_journal.append(
            "simulator.models_selected",
            {
                "tick_model": request.tick_model,
                "spread_model": request.spread_model,
                "slippage_model": request.slippage_model,
                "commission_model": request.commission_model,
                "swap_model": request.swap_model,
                "latency_model": latency_model.to_dict(),
                "ambiguous_sl_tp_policy": ambiguous_policy,
            },
        )

        # Resolve models
        spread_type = request.spread_model
        if spread_type == "variable_v1":
            spread_seed = _get_int_metadata(request.metadata, "spread_seed", 42)
            _spread_model: FixedSpreadModel | VariableSpreadModel = VariableSpreadModel(
                seed=spread_seed
            )
        else:
            sp_points = _get_float_metadata(request.metadata, "spread_points", 1.0)
            _spread_model = FixedSpreadModel(spread_points=sp_points)

        slippage_type = request.slippage_model
        slippage_model: (
            FixedSlippageModel | VolatilitySlippageModel | VolumeSlippageModel
        )
        if slippage_type == "volatility_v1":
            base_pts = _get_float_metadata(
                request.metadata, "base_slippage_points", 2.0
            )
            vol_mult = _get_float_metadata(
                request.metadata, "volatility_multiplier", 1.5
            )
            slippage_model = VolatilitySlippageModel(
                base_slippage_points=base_pts,
                volatility_multiplier=vol_mult,
            )
        elif slippage_type == "volume_v1":
            base_pts = _get_float_metadata(
                request.metadata, "base_slippage_points", 1.0
            )
            vol_mult = _get_float_metadata(request.metadata, "volume_multiplier", 0.5)
            slippage_model = VolumeSlippageModel(
                base_slippage_points=base_pts,
                volume_multiplier=vol_mult,
            )
        elif slippage_type == "none_v1":
            slippage_model = FixedSlippageModel(slippage_points=0.0)
        else:
            slip_pts = _get_float_metadata(request.metadata, "slippage_points", 0.0)
            slippage_model = FixedSlippageModel(slippage_points=slip_pts)

        commission_type = request.commission_model
        if commission_type == "none_v1":
            commission_model = CommissionModel(amount_per_lot=0.0)
        else:
            commission_model = CommissionModel(
                amount_per_lot=_get_float_metadata(
                    request.metadata, "commission_amount_per_lot", 4.0
                )
            )

        swap_type = request.swap_model
        if swap_type == "none_v1":
            swap_model = SwapModel(long_per_lot_per_day=0.0, short_per_lot_per_day=0.0)
        else:
            s_long = _get_float_metadata(request.metadata, "swap_long", -2.0)
            s_short = _get_float_metadata(request.metadata, "swap_short", -1.0)
            swap_model = SwapModel(
                long_per_lot_per_day=s_long,
                short_per_lot_per_day=s_short,
            )

        leverage = _get_int_metadata(request.metadata, "leverage", 100)
        margin_model = MarginModel(leverage=leverage)

        # Ingest multi-symbol tick/ohlcv data
        data_kind = str(request.metadata.get("data_kind", ""))
        if data_kind not in {"ticks", "ohlcv"}:
            data_kind = "ticks" if request.timeframe.upper() == "TICKS" else "ohlcv"
        data_kind_lit: Literal["ticks", "ohlcv"] = (
            "ticks" if data_kind == "ticks" else "ohlcv"
        )

        feed = ChronologicalDataFeed(
            symbols=request.symbols,
            start=request.start,
            end=request.end,
            data_kind=data_kind_lit,
            timeframe=request.timeframe,
            partial_data_policy=_get_str_metadata(
                request.metadata, "partial_data_policy", "fail_fast"
            ),
            max_gap_seconds=_get_float_metadata(
                request.metadata, "max_gap_seconds", 3600.0
            ),
            data_manifest_hash=data_manifest_hash,
            manifest_checksums=cast(
                "dict[str, str] | None",
                request.metadata.get("manifest_checksums"),
            ),
            request_id=request.request_id,
        )

        # Instantiate strategy
        strategy_class = get_strategy(request.strategy_ref)
        strategy_instance = strategy_class()

        timing_policy_str = _get_str_metadata(
            request.metadata, "timing_policy", "BAR_OPEN_PREVIOUS_CLOSE"
        )
        timing_policy: Literal["BAR_OPEN_PREVIOUS_CLOSE", "INTRABAR_EVENT"] = (
            "INTRABAR_EVENT"
            if timing_policy_str == "INTRABAR_EVENT"
            else "BAR_OPEN_PREVIOUS_CLOSE"
        )
        ctx = StrategyExecutionContext(
            environment="BACKTEST",
            decision_timestamp=normalize_timestamp(request.start),
            timing_policy=timing_policy,
            seed_material=request.request_id,
            request_id=request.request_id,
            correlation_id=request.request_id,
            read_only_state=self._build_read_only_state(
                normalize_timestamp(request.start)
            ),
        )

        init_res = run_strategy_hook(
            strategy_instance=strategy_instance,
            hook_name="on_init",
            payload={},
            read_only_state=self._build_read_only_state(
                normalize_timestamp(request.start)
            ),
            context=ctx,
            config=request.strategy_config,
        )
        if init_res["status"] == "error":
            raise ValidationError(
                init_res.get("message", "Strategy initialization failed."),
                code="SIM_INTERNAL_ERROR",
            )

        prev_timestamp = None

        # Replay Clock Tick/Bar Loop
        for event in feed:
            if isinstance(event, SimulatorTick):
                ticks_to_process = [event]
                is_bar_event = False
                bar_dict = {}
            else:
                bar_dict = dict(event)
                symbol = bar_dict["symbol"]
                ts = bar_dict["timestamp"]
                ticks_to_process = [
                    SimulatorTick(
                        timestamp=ts,
                        symbol=symbol,
                        bid=float(bar_dict["open"]),
                        ask=float(bar_dict["open"]),
                    ),
                    SimulatorTick(
                        timestamp=ts,
                        symbol=symbol,
                        bid=float(bar_dict["high"]),
                        ask=float(bar_dict["high"]),
                    ),
                    SimulatorTick(
                        timestamp=ts,
                        symbol=symbol,
                        bid=float(bar_dict["low"]),
                        ask=float(bar_dict["low"]),
                    ),
                    SimulatorTick(
                        timestamp=ts,
                        symbol=symbol,
                        bid=float(bar_dict["close"]),
                        ask=float(bar_dict["close"]),
                    ),
                ]
                is_bar_event = True

            for tick in ticks_to_process:
                self.latest_prices[tick.symbol] = tick
                spec = self.symbol_specs.get(tick.symbol)
                if spec is None:
                    spec = SimulatorSymbolSpec(symbol=tick.symbol)
                    self.symbol_specs[tick.symbol] = spec

                current_ts = normalize_timestamp(tick.timestamp)
                if (
                    prev_timestamp is not None
                    and current_ts.date() > prev_timestamp.date()
                ):
                    days_elapsed = (current_ts.date() - prev_timestamp.date()).days
                    for pos in list(self.positions.values()):
                        pos_spec = self.symbol_specs.get(
                            pos.symbol
                        ) or SimulatorSymbolSpec(symbol=pos.symbol)
                        swap_val = swap_model.calculate(
                            side=pos.side, volume=pos.volume, days_held=days_elapsed
                        )
                        rate = self._resolve_conversion_rate(
                            pos_spec.quote_currency, self.account.base_currency
                        )
                        swap_base = swap_val * rate
                        self.account.swap_base = round(
                            self.account.swap_base + swap_base, 10
                        )
                        self.account.balance_base = round(
                            self.account.balance_base + swap_base, 10
                        )
                        self.account.native_swap[pos_spec.quote_currency] = round(
                            self.account.native_swap.get(pos_spec.quote_currency, 0.0)
                            + swap_val,
                            10,
                        )
                        self.account.native_cash_balances[pos_spec.quote_currency] = (
                            round(
                                self.account.native_cash_balances.get(
                                    pos_spec.quote_currency, 0.0
                                )
                                + swap_val,
                                10,
                            )
                        )
                        active_journal.append(
                            "simulator.swap_applied",
                            {
                                "position_id": pos.position_id,
                                "symbol": pos.symbol,
                                "swap_amount": swap_val,
                                "swap_amount_base": swap_base,
                                "timestamp": tick.timestamp,
                            },
                        )
                prev_timestamp = current_ts

                # Reprice Trailing stops
                for pos_id, pos in list(self.positions.items()):
                    if (
                        pos.symbol == tick.symbol
                        and pos.trailing_stop_points is not None
                    ):
                        trailing_update = update_trailing_stop(
                            pos,
                            tick,
                            current_sl=pos.sl,
                            trailing_stop_points=pos.trailing_stop_points,
                            symbol_spec=spec,
                        )
                        if trailing_update.updated:
                            self.positions[pos_id] = replace(
                                pos, sl=trailing_update.new_sl
                            )
                            active_journal.append(
                                "simulator.position_sl_updated",
                                {
                                    "position_id": pos_id,
                                    "symbol": pos.symbol,
                                    "previous_sl": trailing_update.previous_sl,
                                    "new_sl": trailing_update.new_sl,
                                    "timestamp": tick.timestamp,
                                },
                            )

                # Trigger pending orders
                triggered_deals = self.trigger_pending_orders(
                    tick=tick,
                    symbol_spec=spec,
                    liquidity_model=FixedLiquidityModel(
                        max_volume_per_tick=_get_float_metadata(
                            request.metadata, "max_volume_per_tick", 100.0
                        )
                    ),
                    slippage_model=slippage_model,
                    commission_model=commission_model,
                    margin_model=margin_model,
                )
                for deal in triggered_deals:
                    active_journal.append("simulator.deal_executed", deal.to_dict())

                # SL/TP evaluation
                for pos_id, pos in list(self.positions.items()):
                    if pos.symbol == tick.symbol:
                        sl_tp_eval = evaluate_sl_tp_trigger(
                            pos,
                            tick,
                            sl=pos.sl,
                            tp=pos.tp,
                            ambiguous_policy=ambiguous_policy,
                        )
                        if sl_tp_eval.triggered:
                            close_side: OrderSide = (
                                "sell" if pos.side == "buy" else "buy"
                            )
                            close_deal = self.execute_market_order(
                                tick=tick,
                                side=close_side,
                                requested_volume=pos.volume,
                                symbol_spec=spec,
                                liquidity_model=FixedLiquidityModel(
                                    max_volume_per_tick=pos.volume
                                ),
                                slippage_model=slippage_model,
                                commission_model=commission_model,
                                margin_model=margin_model,
                                target_position_id=pos_id,
                            )
                            active_journal.append(
                                "simulator.position_liquidated",
                                {
                                    "position_id": pos_id,
                                    "symbol": pos.symbol,
                                    "reason": sl_tp_eval.trigger_type,
                                    "deal_id": close_deal.deal_id,
                                    "price": sl_tp_eval.price,
                                    "timestamp": tick.timestamp,
                                },
                            )

                # Margin stop-out evaluation
                stopout = evaluate_stopout(
                    self.account, broker_profile=BrokerRuleProfile()
                )
                if stopout.status == "blocked":
                    losing_positions = []
                    for p_id, p in self.positions.items():
                        p_spec = self.symbol_specs.get(p.symbol) or SimulatorSymbolSpec(
                            symbol=p.symbol
                        )
                        p_tick = self.latest_prices.get(p.symbol)
                        if p_tick is not None:
                            dir_val = 1.0 if p.side == "buy" else -1.0
                            curr_pr = p_tick.bid if p.side == "buy" else p_tick.ask
                            pnl_q = (
                                (curr_pr - p.average_price)
                                * p.volume
                                * p_spec.contract_size
                                * dir_val
                            )
                            rate = self._resolve_conversion_rate(
                                p_spec.quote_currency, self.account.base_currency
                            )
                            pnl_b = pnl_q * rate
                            losing_positions.append((p_id, p, pnl_b))
                    losing_positions.sort(key=lambda item: item[2])
                    if losing_positions:
                        target_id, target_pos, target_pnl = losing_positions[0]
                        c_side: OrderSide = (
                            "sell" if target_pos.side == "buy" else "buy"
                        )
                        t_spec = self.symbol_specs.get(
                            target_pos.symbol
                        ) or SimulatorSymbolSpec(symbol=target_pos.symbol)
                        t_tick = self.latest_prices.get(target_pos.symbol)
                        if t_tick is not None:
                            close_deal = self.execute_market_order(
                                tick=t_tick,
                                side=c_side,
                                requested_volume=target_pos.volume,
                                symbol_spec=t_spec,
                                liquidity_model=FixedLiquidityModel(
                                    max_volume_per_tick=target_pos.volume
                                ),
                                slippage_model=slippage_model,
                                commission_model=commission_model,
                                margin_model=margin_model,
                                target_position_id=target_id,
                            )
                            active_journal.append(
                                "simulator.margin_stopout_executed",
                                {
                                    "position_id": target_id,
                                    "symbol": target_pos.symbol,
                                    "pnl_base": target_pnl,
                                    "deal_id": close_deal.deal_id,
                                    "timestamp": t_tick.timestamp,
                                },
                            )

            # Strategy decision point
            dt_ts = normalize_timestamp(ticks_to_process[-1].timestamp)
            ctx = replace(
                ctx,
                decision_timestamp=dt_ts,
                read_only_state=self._build_read_only_state(dt_ts),
            )

            if not is_bar_event and isinstance(event, SimulatorTick):
                tick_dict = {
                    "timestamp": event.timestamp,
                    "symbol": event.symbol,
                    "bid": event.bid,
                    "ask": event.ask,
                    "last": event.last,
                    "volume": event.volume,
                    "spread_points": event.spread_points,
                }
                strategy_res = run_strategy_hook(
                    strategy_instance=strategy_instance,
                    hook_name="on_tick",
                    payload=tick_dict,
                    read_only_state=self._build_read_only_state(dt_ts),
                    context=ctx,
                    config=request.strategy_config,
                )
            else:
                strategy_res = run_strategy_hook(
                    strategy_instance=strategy_instance,
                    hook_name="on_bar",
                    payload=bar_dict,
                    read_only_state=self._build_read_only_state(dt_ts),
                    context=ctx,
                    config=request.strategy_config,
                )

            if strategy_res["status"] == "success":
                intents_list = strategy_res["data"].get("trade_intents", [])
                for raw_intent in intents_list:
                    intent_dict = (
                        raw_intent.model_dump()
                        if hasattr(raw_intent, "model_dump")
                        else dict(raw_intent)
                    )
                    intent_symbol = intent_dict.get(
                        "symbol", ticks_to_process[-1].symbol
                    )
                    intent_side: OrderSide = (
                        "buy"
                        if str(intent_dict.get("side", "buy")).lower() == "buy"
                        else "sell"
                    )
                    intent_qty = float(
                        intent_dict.get("quantity_hint", 0.0)
                        or intent_dict.get("volume", 0.0)
                    )
                    intent_type = str(intent_dict.get("intent_type", "market")).lower()

                    if intent_qty <= 0:
                        continue

                    t_pos_id = intent_dict.get("parent_intent_id")
                    t_spec = self.symbol_specs.get(
                        intent_symbol
                    ) or SimulatorSymbolSpec(symbol=intent_symbol)

                    if intent_type == "market":
                        try:
                            intent_deal = self.execute_market_order(
                                tick=ticks_to_process[-1],
                                side=intent_side,
                                requested_volume=intent_qty,
                                symbol_spec=t_spec,
                                liquidity_model=FixedLiquidityModel(
                                    max_volume_per_tick=intent_qty
                                ),
                                slippage_model=slippage_model,
                                commission_model=commission_model,
                                margin_model=margin_model,
                                sl=intent_dict.get("stop_loss"),
                                tp=intent_dict.get("take_profit"),
                                target_position_id=t_pos_id,
                            )
                            active_journal.append(
                                "simulator.deal_executed", intent_deal.to_dict()
                            )
                        except ValidationError as ve:
                            skipped_diag = build_skipped_trade_diagnostic(
                                code=ve.code or "SIM_SIZING_FAILED",
                                reason=str(ve),
                                field_path="volume",
                            )
                            active_journal.append(
                                "simulator.skipped_trade", skipped_diag.to_dict()
                            )
                    elif intent_type in {
                        "buy_limit",
                        "sell_limit",
                        "buy_stop",
                        "sell_stop",
                        "buy_stop_limit",
                        "sell_stop_limit",
                    }:
                        try:
                            intent_order = self.place_pending_order(
                                tick=ticks_to_process[-1],
                                order_type=intent_type,
                                requested_volume=intent_qty,
                                order_price=float(
                                    intent_dict.get("price", 0.0)
                                    or intent_dict.get("order_price", 0.0)
                                ),
                                stop_limit_price=intent_dict.get("stop_limit_price"),
                                sl=intent_dict.get("stop_loss"),
                                tp=intent_dict.get("take_profit"),
                                trailing_stop_points=intent_dict.get(
                                    "trailing_stop_points"
                                ),
                                pegged_reference=intent_dict.get("pegged_reference"),
                            )
                            active_journal.append(
                                "simulator.order_placed", intent_order.to_dict()
                            )
                        except ValidationError as ve:
                            skipped_diag = build_skipped_trade_diagnostic(
                                code=ve.code or "SIM_INVALID_CONFIG",
                                reason=str(ve),
                                field_path="price",
                            )
                            active_journal.append(
                                "simulator.skipped_trade", skipped_diag.to_dict()
                            )

            # Recalculate account ledger & snapshot equity curve
            self._recalculate_account_ledger()
            self.equity_curve.append(
                {
                    "timestamp": ticks_to_process[-1].timestamp,
                    "balance": self.account.balance_base,
                    "equity": self.account.nav_base,
                    "margin": self.account.margin_base,
                    "free_margin": self.account.free_margin_base,
                }
            )

        # Scorecard compilation integration
        from app.services.simulator.analytics import (
            build_scorecard_from_simulator_result,
        )

        scorecard = build_scorecard_from_simulator_result(
            trades=self.closed_trades,
            equity_curve=self.equity_curve,
            run_id=run_id,
        )

        max_drawdown = float(
            scorecard.get("drawdown_metrics", {}).get("max_drawdown", 0.0)
        )
        if max_drawdown == 0.0 and self.equity_curve:
            peak = -1e9
            for pt in self.equity_curve:
                eq = pt["equity"]
                peak = max(peak, eq)
                if peak > 0:
                    dd = (peak - eq) / peak
                    max_drawdown = max(max_drawdown, dd)

        journal_checksum = stable_identifier(
            active_journal.replay_payload(),
            prefix="id",
        )
        journal_artifact_manifest = build_journal_artifact_manifest(
            config_hash=config_hash,
            data_manifest_hash=data_manifest_hash,
            engine_version=self.engine_version,
            journal_checksum=journal_checksum,
        )
        run_config_artifact = build_run_configuration_artifact(
            request,
            config_hash=config_hash,
            engine_version=self.engine_version,
        )
        environment_diagnostic = build_environment_diagnostic()
        completed_at = utc_now().isoformat()
        execution_ms = round((time.perf_counter() - execution_start) * 1000, 3)
        validate_resource_quota(
            wall_clock_seconds=execution_ms / 1000,
            temporary_storage_bytes=0,
        )
        metrics = {
            "total_trades": float(len(self.closed_trades)),
            "ending_balance": float(self.account.balance_base),
            "net_profit": float(self.account.realized_pnl_base),
            "open_positions": float(len(self.positions)),
            "orders": float(len(self.orders)),
            "deals": float(len(self.deals)),
        }
        metadata = self._result_metadata(
            request=request,
            config_hash=config_hash,
            data_manifest_hash=data_manifest_hash,
            execution_ms=execution_ms,
            created_at=completed_at,
            latency_model=latency_model,
            ambiguous_sl_tp_policy=ambiguous_policy,
            run_config_artifact=run_config_artifact,
            journal_artifact_manifest=journal_artifact_manifest,
            environment_diagnostic=environment_diagnostic,
        )
        result = SimulatorResult(
            schema_version=RESULT_SCHEMA_VERSION,
            run_id=run_id,
            classification=request.realism_profile,
            started_at=started_at,
            completed_at=completed_at,
            engine_version=self.engine_version,
            config_hash=config_hash,
            data_manifest_hash=data_manifest_hash,
            broker_profile_id=request.broker_profile_ref,
            artifact_manifest={
                "journal": asdict(active_journal.manifest()),
                "journal_manifest": journal_artifact_manifest.to_dict(),
                "run_configuration": run_config_artifact.to_dict(),
            },
            summary_metrics=metrics,
            risk_metrics={"max_drawdown": max_drawdown},
            cost_summary={
                "commission": self.account.commission_base,
                "swap": self.account.swap_base,
                "slippage": 0.0,
            },
            realism_disclosure=(
                "08A canonical tick-engine foundation; synthetic matching "
                "primitives are available but orchestrated strategy fills are "
                "not yet produced."
            ),
            data_quality_summary={"status": "not_evaluated", "issues": 0},
            metadata=metadata,
        )
        logger.info(
            "simulator engine run completed",
            extra={
                "event_name": "simulator_engine_run_completed",
                "request_id": request.request_id,
                "run_id": run_id,
                "config_hash": config_hash,
            },
        )
        canonical_json(result.to_dict())
        return result

    def execute_market_order(
        self,
        *,
        tick: SimulatorTick,
        side: OrderSide,
        requested_volume: float,
        symbol_spec: SimulatorSymbolSpec | None = None,
        liquidity_model: FixedLiquidityModel | None = None,
        slippage_model: (
            FixedSlippageModel | VolatilitySlippageModel | VolumeSlippageModel | None
        ) = None,
        commission_model: CommissionModel | None = None,
        margin_model: MarginModel | None = None,
        time_in_force: str = "GTC",
        market_hours: MarketHoursConfig | None = None,
        halt_state: MarketHaltState | None = None,
        broker_profile: BrokerRuleProfile | None = None,
        volume_rounding_policy: VolumeRoundingPolicy = "floor_to_step",
        sl: float | None = None,
        tp: float | None = None,
        trailing_stop_points: float | None = None,
        target_position_id: str | None = None,
    ) -> EngineDeal:
        """Match a market order through engine-owned state.

        Args:
            tick: Current executable bid/ask tick.
            side: Buy or sell side.
            requested_volume: Requested volume in lots.
            symbol_spec: Optional symbol metadata.
            liquidity_model: Optional liquidity model.
            slippage_model: Optional slippage model.
            commission_model: Optional commission model.
            margin_model: Optional margin model.
            time_in_force: Time-in-force policy.
            market_hours: Optional market-hours configuration.
            halt_state: Optional halt state.
            broker_profile: Optional broker-rule profile.
            volume_rounding_policy: Deterministic volume rounding policy.
            sl: Optional stop-loss price.
            tp: Optional take-profit price.
            trailing_stop_points: Optional trailing stop points in points.
            target_position_id: Optional ID of the position to target/close.

        Returns:
            EngineDeal: Executed deal record.

        Raises:
            ValidationError: If side, volume, or model inputs are invalid.
        """
        if side not in {"buy", "sell"}:
            raise ValidationError(
                "side must be buy or sell.",
                code="SIM_INVALID_CONFIG",
            )
        fill_policy = validate_fill_policy(time_in_force, broker_profile=broker_profile)
        session = evaluate_market_session(
            tick.timestamp,
            config=market_hours,
            halt_state=halt_state,
        )
        if not session.is_open:
            message = f"market is closed: {session.reason}"
            raise ValidationError(
                message,
                code=session.code or "SIM_MARKET_CLOSED",
            )
        spec = symbol_spec or SimulatorSymbolSpec(symbol=tick.symbol)
        validate_position_limit(
            self.positions,
            symbol=tick.symbol,
            side=side,
            broker_profile=broker_profile,
        )
        stopout = evaluate_stopout(self.account, broker_profile=broker_profile)
        if stopout.status == "blocked":
            raise ValidationError(stopout.reason, code=stopout.code)
        normalization = self._final_position_size(
            requested_volume,
            spec,
            rounding_policy=volume_rounding_policy,
        )
        volume = normalization.normalized_volume
        liquidity = liquidity_model or FixedLiquidityModel()
        fill = liquidity.fill(volume, time_in_force=fill_policy)
        if fill_policy == "FOK" and fill.filled_volume < volume:
            raise ValidationError(
                "FOK order cannot be fully filled.",
                code="SIM_LIQUIDITY_UNAVAILABLE",
            )
        executable_price = tick.ask if side == "buy" else tick.bid
        validate_stop_prices(side=side, entry_price=executable_price, sl=sl, tp=tp)
        slippage = slippage_model or FixedSlippageModel(point=spec.point)
        price = slippage.apply(
            side=side,
            expected_price=executable_price,
            executable_price=executable_price,
            filled_volume=fill.filled_volume,
        ).final_price
        commission = (commission_model or CommissionModel()).calculate(
            fill.filled_volume
        )
        margin = (margin_model or MarginModel()).calculate(
            contract_size=spec.contract_size,
            volume=fill.filled_volume,
            price=price,
        )
        created_at = normalize_timestamp(tick.timestamp).isoformat()
        order_id = stable_identifier(
            {
                "symbol": tick.symbol,
                "side": side,
                "raw_requested_volume": normalization.raw_volume,
                "requested_volume": volume,
                "volume_rounding_policy": normalization.rounding_policy,
                "volume_adjusted": normalization.adjusted,
                "timestamp": created_at,
                "order_index": len(self.orders) + 1,
            },
            prefix="simord",
        )
        deal_id = stable_identifier(
            {
                "order_id": order_id,
                "volume": fill.filled_volume,
                "price": price,
                "deal_index": len(self.deals) + 1,
            },
            prefix="simdeal",
        )
        status = self._order_status_for_fill(
            fill_policy=fill_policy,
            remainder_volume=fill.remainder_volume,
        )
        order = EngineOrder(
            order_id=order_id,
            symbol=tick.symbol,
            side=side,
            requested_volume=volume,
            filled_volume=fill.filled_volume,
            status=status,
            created_at=created_at,
            time_in_force=fill_policy,
            sl=sl,
            tp=tp,
            raw_requested_volume=normalization.raw_volume,
            volume_rounding_policy=normalization.rounding_policy,
            volume_adjusted=normalization.adjusted,
        )
        position_id = stable_identifier(
            {
                "symbol": tick.symbol,
                "side": side,
            },
            prefix="simpos",
        )
        deal = EngineDeal(
            deal_id=deal_id,
            order_id=order_id,
            symbol=tick.symbol,
            side=side,
            volume=fill.filled_volume,
            price=price,
            commission=commission,
            margin=margin,
            executed_at=created_at,
            position_id=position_id,
            diagnostic_code=fill.diagnostic_code,
        )
        self.orders[order_id] = order
        self.deals[deal_id] = deal
        self.symbol_specs[tick.symbol] = spec
        self._upsert_position(
            position_id=position_id,
            symbol=tick.symbol,
            side=side,
            filled_volume=fill.filled_volume,
            fill_price=price,
            margin=margin,
            opened_at=created_at,
            sl=sl,
            tp=tp,
            trailing_stop_points=trailing_stop_points,
            broker_profile=broker_profile,
            target_position_id=target_position_id,
        )
        if fill_policy == "RETURN" and fill.remainder_volume > 0:
            remainder_order = EngineOrder(
                order_id=stable_identifier(
                    {"parent": order_id, "remainder": fill.remainder_volume},
                    prefix="simord",
                ),
                symbol=tick.symbol,
                side=side,
                requested_volume=fill.remainder_volume,
                filled_volume=0.0,
                status="pending",
                created_at=created_at,
                time_in_force=fill_policy,
                order_price=executable_price,
                parent_order_id=order_id,
                raw_requested_volume=fill.remainder_volume,
            )
            self.orders[remainder_order.order_id] = remainder_order
        self.account.apply_deal(
            currency=spec.quote_currency,
            commission=commission,
            margin=margin,
        )
        self._recalculate_account_ledger()
        return deal

    def _order_status_for_fill(
        self,
        *,
        fill_policy: FillPolicy,
        remainder_volume: float,
    ) -> str:
        if remainder_volume == 0:
            return "filled"
        if fill_policy == "IOC":
            return "partially_filled_remainder_cancelled"
        if fill_policy == "RETURN":
            return "partially_filled_remainder_pending"
        return "rejected"

    def _upsert_position(  # noqa: C901, PLR0912, PLR0915
        self,
        *,
        position_id: str,
        symbol: str,
        side: OrderSide,
        filled_volume: float,
        fill_price: float,
        margin: float,
        opened_at: str,
        sl: float | None = None,
        tp: float | None = None,
        trailing_stop_points: float | None = None,
        broker_profile: BrokerRuleProfile | None = None,
        target_position_id: str | None = None,
    ) -> None:
        active_profile = broker_profile or BrokerRuleProfile()
        spec = self.symbol_specs.get(symbol) or SimulatorSymbolSpec(symbol=symbol)
        use_netting = active_profile.hedging_mode == "netting"

        if use_netting or target_position_id is not None:
            if target_position_id is not None:
                existing_pos_id = target_position_id
                existing_pos = self.positions.get(existing_pos_id)
            else:
                existing_pos_id = None
                existing_pos = None
                for pid, pos in self.positions.items():
                    if pos.symbol == symbol:
                        existing_pos_id = pid
                        existing_pos = pos
                        break

            if existing_pos is None:
                self.positions[position_id] = EnginePosition(
                    position_id=position_id,
                    symbol=symbol,
                    side=side,
                    volume=filled_volume,
                    average_price=fill_price,
                    margin=margin,
                    opened_at=opened_at,
                    sl=sl,
                    tp=tp,
                    trailing_stop_points=trailing_stop_points,
                )
                return

            if existing_pos_id is None:
                return
            if existing_pos.side == side:
                total_volume = round(existing_pos.volume + filled_volume, 10)
                average_price = round(
                    (
                        existing_pos.average_price * existing_pos.volume
                        + fill_price * filled_volume
                    )
                    / total_volume,
                    10,
                )
                self.positions[existing_pos_id] = EnginePosition(
                    position_id=existing_pos_id,
                    symbol=symbol,
                    side=side,
                    volume=total_volume,
                    average_price=average_price,
                    margin=round(existing_pos.margin + margin, 10),
                    opened_at=existing_pos.opened_at,
                    sl=sl if sl is not None else existing_pos.sl,
                    tp=tp if tp is not None else existing_pos.tp,
                    trailing_stop_points=trailing_stop_points
                    if trailing_stop_points is not None
                    else existing_pos.trailing_stop_points,
                )
            else:
                diff = round(existing_pos.volume - filled_volume, 10)
                closed_volume = min(existing_pos.volume, filled_volume)
                direction = 1 if existing_pos.side == "buy" else -1
                realized_pnl_quote = (
                    (fill_price - existing_pos.average_price)
                    * closed_volume
                    * spec.contract_size
                    * direction
                )
                rate = self._resolve_conversion_rate(
                    spec.quote_currency, self.account.base_currency
                )
                realized_pnl_base = realized_pnl_quote * rate

                self.account.realized_pnl_base = round(
                    self.account.realized_pnl_base + realized_pnl_base, 10
                )
                self.account.balance_base = round(
                    self.account.balance_base + realized_pnl_base, 10
                )
                self.account.native_realized_pnl[spec.quote_currency] = round(
                    self.account.native_realized_pnl.get(spec.quote_currency, 0.0)
                    + realized_pnl_quote,
                    10,
                )
                self.account.native_cash_balances[spec.quote_currency] = round(
                    self.account.native_cash_balances.get(spec.quote_currency, 0.0)
                    + realized_pnl_quote,
                    10,
                )
                self.closed_trades.append(
                    {
                        "symbol": symbol,
                        "direction": existing_pos.side,
                        "volume": closed_volume,
                        "open_price": existing_pos.average_price,
                        "close_price": fill_price,
                        "open_time": existing_pos.opened_at,
                        "close_time": opened_at,
                        "net_pnl": realized_pnl_base,
                        "profit": realized_pnl_base,
                        "is_open": False,
                    }
                )

                if diff > 0:
                    new_margin = round(
                        existing_pos.margin * (diff / existing_pos.volume), 10
                    )
                    self.positions[existing_pos_id] = EnginePosition(
                        position_id=existing_pos_id,
                        symbol=symbol,
                        side=existing_pos.side,
                        volume=diff,
                        average_price=existing_pos.average_price,
                        margin=new_margin,
                        opened_at=existing_pos.opened_at,
                        sl=existing_pos.sl,
                        tp=existing_pos.tp,
                        trailing_stop_points=existing_pos.trailing_stop_points,
                    )
                elif diff == 0:
                    del self.positions[existing_pos_id]
                else:
                    del self.positions[existing_pos_id]
                    remainder_volume = abs(diff)
                    new_margin = round(margin * (remainder_volume / filled_volume), 10)
                    new_id = stable_identifier(
                        {
                            "symbol": symbol,
                            "side": side,
                        },
                        prefix="simpos",
                    )
                    self.positions[new_id] = EnginePosition(
                        position_id=new_id,
                        symbol=symbol,
                        side=side,
                        volume=remainder_volume,
                        average_price=fill_price,
                        margin=new_margin,
                        opened_at=opened_at,
                        sl=sl,
                        tp=tp,
                        trailing_stop_points=trailing_stop_points,
                    )
        else:
            existing = self.positions.get(position_id)
            if existing is None:
                self.positions[position_id] = EnginePosition(
                    position_id=position_id,
                    symbol=symbol,
                    side=side,
                    volume=filled_volume,
                    average_price=fill_price,
                    margin=margin,
                    opened_at=opened_at,
                    sl=sl,
                    tp=tp,
                    trailing_stop_points=trailing_stop_points,
                )
                return
            total_volume = round(existing.volume + filled_volume, 10)
            average_price = round(
                (existing.average_price * existing.volume + fill_price * filled_volume)
                / total_volume,
                10,
            )
            self.positions[position_id] = EnginePosition(
                position_id=position_id,
                symbol=symbol,
                side=side,
                volume=total_volume,
                average_price=average_price,
                margin=round(existing.margin + margin, 10),
                opened_at=existing.opened_at,
                sl=sl if sl is not None else existing.sl,
                tp=tp if tp is not None else existing.tp,
                trailing_stop_points=trailing_stop_points
                if trailing_stop_points is not None
                else existing.trailing_stop_points,
            )

    def _reset_state(self, request: SimulatorBacktestRequestV1) -> None:
        self.positions.clear()
        self.orders.clear()
        self.deals.clear()
        self.latest_prices.clear()
        self.symbol_specs.clear()
        self.pending_intents.clear()
        self.equity_curve.clear()
        self.closed_trades.clear()
        self.request_metadata = dict(request.metadata)
        self.account = AccountLedger(
            base_currency=request.account_currency,
            balance_base=float(request.initial_balance),
            native_cash_balances={
                request.account_currency: float(request.initial_balance),
            },
        )

    def _final_position_size(
        self,
        requested_volume: float,
        symbol_spec: SimulatorSymbolSpec,
        *,
        rounding_policy: VolumeRoundingPolicy = "floor_to_step",
    ) -> VolumeNormalizationResult:
        return normalize_order_volume(
            requested_volume,
            symbol_spec,
            rounding_policy=rounding_policy,
        )

    def _validate_first_tick_lookahead(
        self,
        request: SimulatorBacktestRequestV1,
    ) -> None:
        bar_open = request.metadata.get("first_tick_bar_open")
        if bar_open is None:
            return
        bar_open_ts = normalize_timestamp(str(bar_open))
        sources = (
            "raw_ohlcv_points",
            "indicator_points",
            "multi_timeframe_points",
            "strategy_metadata_dependencies",
        )
        for source in sources:
            points = request.metadata.get(source, ())
            if not isinstance(points, list | tuple):
                continue
            for point in points:
                if not isinstance(point, dict):
                    continue
                timestamp = point.get("timestamp", point.get("available_at"))
                if timestamp is None:
                    timestamp = point.get("data_timestamp")
                if timestamp is None:
                    continue
                if normalize_timestamp(str(timestamp)) >= bar_open_ts:
                    logger.warning(
                        "simulator lookahead detected",
                        extra={
                            "event_name": "simulator_lookahead_detected",
                            "request_id": request.request_id,
                            "source": source,
                        },
                    )
                    message = f"{source} contains current-bar or future data."
                    raise SimLookaheadDetectedError(
                        message,
                        code="SIM_LOOKAHEAD_DETECTED",
                    )

    def _latency_model_from_metadata(
        self,
        metadata: dict[str, object],
    ) -> ExecutionLatencyModel:
        raw = metadata.get("execution_latency_model", {})
        if not isinstance(raw, dict):
            raise ValidationError(
                "execution_latency_model must be a mapping.",
                code="SIM_INVALID_CONFIG",
            )
        return ExecutionLatencyModel(
            strategy_compute_ms=float(raw.get("strategy_compute_ms", 0.0)),
            broker_routing_ms=float(raw.get("broker_routing_ms", 0.0)),
            venue_gateway_ms=float(raw.get("venue_gateway_ms", 0.0)),
            matching_engine_ms=float(raw.get("matching_engine_ms", 0.0)),
        )

    def _result_metadata(
        self,
        *,
        request: SimulatorBacktestRequestV1,
        config_hash: str,
        data_manifest_hash: str,
        execution_ms: float,
        created_at: str,
        latency_model: ExecutionLatencyModel,
        ambiguous_sl_tp_policy: str,
        run_config_artifact: RunConfigurationArtifact,
        journal_artifact_manifest: JournalArtifactManifest,
        environment_diagnostic: EnvironmentDiagnostic,
    ) -> dict[str, Any]:
        actor_metadata: dict[str, object] = {
            "actor_id": request.actor_context.actor_id,
            "roles": list(request.actor_context.roles),
            "auth_source": request.actor_context.auth_source,
        }
        return {
            "module": "simulator",
            "operation": "event_driven_execution",
            "tool_risk_level": TOOL_RISK_LEVEL,
            "side_effects": SIDE_EFFECT_CLASSIFICATION,
            "actor": actor_metadata,
            "audit": {
                "request_id": request.request_id,
                "broker_profile_id": request.broker_profile_ref,
                "market_data_authority_ref": request.market_data_authority_ref,
            },
            "engine_version": self.engine_version,
            "config_hash": config_hash,
            "data_manifest_hash": data_manifest_hash,
            "execution_ms": execution_ms,
            "created_at": created_at,
            "execution_latency_model": latency_model.to_dict(),
            "ambiguous_sl_tp_policy": ambiguous_sl_tp_policy,
            "state_authority": "engine_owned",
            "extension_points": EngineExtensionPoints().to_dict(),
            "regulatory_scope": RegulatoryScope().to_dict(),
            "deferred_scope": dict(DEFERRED_PHASE1_SCOPE),
            "run_configuration": run_config_artifact.to_dict(),
            "journal_manifest": journal_artifact_manifest.to_dict(),
            "environment_diagnostic": environment_diagnostic.to_dict(),
            "telemetry": EngineTelemetry(
                run_status="success",
                lookahead_violation_count=0,
                execution_latency_ms=latency_model.total_ms,
                data_quality_failure_count=0,
                persistence_failure_count=0,
                queue_depth=0,
                quota_rejection_count=0,
            ).to_dict(),
            "phase1_asset_class": PHASE1_ASSET_CLASS,
        }
