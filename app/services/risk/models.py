"""Risk governance models and enums module.

Defines all Pydantic models for inputs, intermediate calculations, snapshots,
and decision packages used by the RiskGovernor.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, model_validator

from app.contracts.base import Contract


class RiskDecisionStatus(StrEnum):
    """Canonical outcomes of the risk review process."""

    APPROVE = "approve"
    REDUCE_SIZE = "reduce_size"
    REJECT = "reject"
    BLOCK = "block"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    NEEDS_APPROVAL = "needs_approval"
    HALT_STRATEGY = "halt_strategy"
    HALT_ALL = "halt_all"


class RiskMode(StrEnum):
    """Execution mode of the trading system."""

    OFFLINE = "offline"
    SIMULATION = "simulation"
    PAPER = "paper"
    SHADOW = "shadow"
    LIVE_READONLY = "live_readonly"
    MICRO_LIVE = "micro_live"
    FULL_LIVE = "full_live"


class RiskAction(StrEnum):
    """Governed actions requiring risk approval."""

    EXECUTE_TRADE = "execute_trade"
    ALLOCATE_CAPITAL = "allocate_capital"
    ADMIT_STRATEGY = "admit_strategy"
    PROMOTE_MODE = "promote_mode"


class RiskSeverity(StrEnum):
    """Severity levels for violations or events."""

    INFO = "info"
    WARNING = "warning"
    SOFT_BREACH = "soft_breach"
    HARD_BREACH = "hard_breach"
    CRITICAL_BREACH = "critical_breach"
    EMERGENCY_HALT = "emergency_halt"


class RiskReasonCode(StrEnum):
    """Deterministic reasons for decisions."""

    OK = "OK"
    NEWS_BLACKOUT = "NEWS_BLACKOUT"
    ROLLOVER_BLACKOUT = "ROLLOVER_BLACKOUT"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    DRAWDOWN_BREACH = "DRAWDOWN_BREACH"
    DAILY_LOSS_BREACH = "DAILY_LOSS_BREACH"
    LEVERAGE_BREACH = "LEVERAGE_BREACH"
    MARGIN_BREACH = "MARGIN_BREACH"
    CONCENTRATION_BREACH = "CONCENTRATION_BREACH"
    CURRENCY_BREACH = "CURRENCY_BREACH"
    CORRELATION_BREACH = "CORRELATION_BREACH"
    VAR_BREACH = "VAR_BREACH"
    ES_BREACH = "ES_BREACH"
    STRESS_BREACH = "STRESS_BREACH"
    SLIPPAGE_BREACH = "SLIPPAGE_BREACH"
    SPREAD_BREACH = "SPREAD_BREACH"
    FREQUENCY_BREACH = "FREQUENCY_BREACH"
    INVALID_INPUT = "INVALID_INPUT"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED = "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED"
    ALLOCATION_LIMIT_BREACH = "ALLOCATION_LIMIT_BREACH"
    LIFECYCLE_GATES_BREACH = "LIFECYCLE_GATES_BREACH"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class RiskContract(Contract):
    """Base model for risk contracts.

    Supports Decimal serialization to float in JSON.
    """

    def to_json(self) -> str:
        """Serialize contract to deterministic canonical JSON string."""
        from app.utils.errors import ValidationError
        from app.utils.standard import canonical_json

        try:
            dump = self.model_dump()

            # Helper to recursively convert Decimal and datetime objects
            def _coerce_types(v: Any) -> Any:  # noqa: ANN401
                if isinstance(v, Decimal):
                    return float(v)
                if isinstance(v, datetime):
                    return v.isoformat()
                if isinstance(v, dict):
                    return {k: _coerce_types(val) for k, val in v.items()}
                if isinstance(v, list):
                    return [_coerce_types(val) for val in v]
                return v

            return canonical_json(_coerce_types(dump))
        except Exception as e:
            msg = f"Failed to serialize contract: {e}"
            raise ValidationError(msg) from e


class RiskSubConfig(RiskContract):
    """Sub-configuration for general risk caps."""

    max_risk_per_trade: Decimal = Field(
        default=Decimal("0.0025"), description="Max risk per trade."
    )
    max_total_open_risk: Decimal = Field(
        default=Decimal("0.0150"), description="Max total open risk."
    )
    max_symbol_open_risk: Decimal = Field(
        default=Decimal("0.0050"), description="Max symbol open risk."
    )
    max_currency_bucket_risk: Decimal = Field(
        default=Decimal("0.0075"), description="Max currency bucket risk."
    )
    max_correlated_cluster_risk: Decimal = Field(
        default=Decimal("0.0075"), description="Max correlated cluster risk."
    )
    max_margin_usage: Decimal = Field(
        default=Decimal("0.30"), description="Max margin utilization."
    )


class DrawdownSubConfig(RiskContract):
    """Sub-configuration for drawdown/loss thresholds."""

    daily_loss_soft_limit: Decimal = Field(
        default=Decimal("0.02"), description="Daily loss soft drawdown limit."
    )
    daily_loss_hard_limit: Decimal = Field(
        default=Decimal("0.04"), description="Daily loss hard drawdown limit."
    )
    total_drawdown_soft_limit: Decimal = Field(
        default=Decimal("0.06"), description="Total drawdown soft limit."
    )
    total_drawdown_hard_limit: Decimal = Field(
        default=Decimal("0.09"), description="Total drawdown hard limit."
    )


class CorrelationSubConfig(RiskContract):
    """Sub-configuration for correlation window parameters."""

    lookback_m5: int = Field(
        default=96, description="Lookback window bars for M5 charts."
    )
    lookback_h1: int = Field(
        default=24, description="Lookback window bars for H1 charts."
    )
    lookback_d1: int = Field(
        default=10, description="Lookback window bars for D1 charts."
    )
    reject_threshold: Decimal = Field(
        default=Decimal("0.70"), description="Correlation threshold to reject."
    )
    reduce_threshold: Decimal = Field(
        default=Decimal("0.50"), description="Correlation threshold to reduce."
    )


class TailRiskSubConfig(RiskContract):
    """Sub-configuration for tail-risk limits."""

    var_confidence: Decimal = Field(
        default=Decimal("0.95"), description="VaR confidence level."
    )
    es_confidence: Decimal = Field(
        default=Decimal("0.95"), description="ES confidence level."
    )
    max_portfolio_var: Decimal = Field(
        default=Decimal("0.0100"), description="Max portfolio Value-at-Risk."
    )
    max_portfolio_es: Decimal = Field(
        default=Decimal("0.0150"), description="Max portfolio Expected Shortfall."
    )
    stress_loss_limit: Decimal = Field(
        default=Decimal("0.0200"), description="Max portfolio stress loss limit."
    )


class ExecutionSubConfig(RiskContract):
    """Sub-configuration for execution blackout and spread controls."""

    max_spread_to_sigma: Decimal = Field(
        default=Decimal("0.25"), description="Max spread spike to sigma ratio."
    )
    max_slippage_to_sigma: Decimal = Field(
        default=Decimal("0.20"), description="Max slippage to sigma ratio."
    )
    rollover_blackout_hours_before: int = Field(
        default=2, description="Hours to block trading before rollover."
    )
    rollover_blackout_hours_after: int = Field(
        default=2, description="Hours to block trading after rollover."
    )


class RiskConfig(RiskContract):
    """Configuration profile containing policy rules and risk limits."""

    profile_name: str = Field(
        default="default", description="Configuration profile name."
    )
    allow_live_execution: bool = Field(
        default=False, description="True if live execution is authorized."
    )
    max_daily_loss_pct: Decimal = Field(default=Decimal("0.05"))
    max_total_loss_pct: Decimal = Field(default=Decimal("0.10"))
    double_spend_prevention_owner: str = Field(default="risk_cache")
    max_margin_utilization_pct: Decimal = Field(default=Decimal("0.80"))
    max_effective_leverage: Decimal = Field(default=Decimal("30.0"))
    correlation_threshold: Decimal = Field(default=Decimal("0.50"))
    default_kelly_fraction: Decimal = Field(default=Decimal("0.25"))
    min_kelly_trades: int = Field(default=3)
    max_risk_per_trade: Decimal = Field(default=Decimal("0.01"))
    max_total_loss_pct_advisory: Decimal = Field(default=Decimal("0.08"))
    pending_order_policy: str = Field(
        default="ignore",
        description=(
            "Policy for pending orders: ignore, near_market_only, "
            "probability_weighted, full_potential"
        ),
    )
    currency_clusters: dict[str, list[str]] = Field(
        default_factory=dict, description="Currency leg cluster definitions."
    )
    allocation_method: str = Field(
        default="correlation_adjusted_parity",
        description="Method for dynamic capital allocations.",
    )
    max_allocation_increase_pct: Decimal = Field(
        default=Decimal("0.20"),
        description=(
            "Threshold for requiring governed approval for allocation increases."
        ),
    )
    max_strategy_allocation_pct: Decimal = Field(
        default=Decimal("0.50"),
        description="Maximum allocation percentage for a single strategy.",
    )
    min_backtest_trades: int = Field(
        default=100, description="Minimum trades required in backtest."
    )
    min_backtest_sharpe: Decimal = Field(
        default=Decimal("1.5"), description="Minimum Sharpe ratio in backtest."
    )
    max_backtest_drawdown: Decimal = Field(
        default=Decimal("0.20"), description="Maximum drawdown in backtest."
    )
    min_wf_trades: int = Field(
        default=50, description="Minimum trades in walk-forward."
    )
    min_wf_sharpe: Decimal = Field(
        default=Decimal("1.2"), description="Minimum Sharpe in walk-forward."
    )
    min_sim_trades: int = Field(default=30, description="Minimum trades in simulation.")
    min_sim_profit_factor: Decimal = Field(
        default=Decimal("1.1"), description="Minimum profit factor in simulation."
    )
    min_paper_trades: int = Field(
        default=20, description="Minimum trades in paper trading."
    )
    min_paper_sharpe: Decimal = Field(
        default=Decimal("1.0"), description="Minimum Sharpe in paper trading."
    )
    max_shadow_tracking_error: Decimal = Field(
        default=Decimal("0.05"), description="Maximum tracking error in shadow mode."
    )
    min_shadow_days: int = Field(
        default=14, description="Minimum duration in shadow mode in days."
    )
    min_live_days: int = Field(
        default=30, description="Minimum duration in micro-live in days."
    )
    min_live_sharpe: Decimal = Field(
        default=Decimal("1.0"), description="Minimum Sharpe in micro-live."
    )
    var_method: str = Field(
        default="historical", description="Default Value-at-Risk calculation method."
    )
    var_confidence: Decimal = Field(
        default=Decimal("0.95"), description="Default VaR confidence level."
    )
    var_lookback_days: int = Field(
        default=250, description="Default lookback window in trading days for VaR/ES."
    )
    es_confidence: Decimal = Field(
        default=Decimal("0.95"),
        description="Default Expected Shortfall confidence level.",
    )
    max_stress_loss_pct: Decimal = Field(
        default=Decimal("0.15"),
        description="Max estimated stress loss threshold before rejection.",
    )
    min_correlation_samples: int = Field(
        default=20,
        description="Minimum data samples required for correlation calculation.",
    )
    currency_leg_limits: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Exposure limits per currency leg in account currency.",
    )
    drawdown_stepdown_thresholds: list[Decimal] = Field(
        default_factory=list,
        description="List of drawdown thresholds for risk reduction scaling.",
    )
    drawdown_stepdown_multipliers: list[Decimal] = Field(
        default_factory=list,
        description="Risk scaling step-down multipliers matching thresholds.",
    )
    maintenance_margin_pct: Decimal = Field(
        default=Decimal("0.50"), description="Maintenance margin ratio threshold."
    )
    max_spread_multiplier: Decimal = Field(
        default=Decimal("3.0"),
        description="Allowed spread spike multiplier above typical.",
    )
    max_slippage_pips: Decimal = Field(
        default=Decimal("5.0"),
        description="Maximum tolerable execution slippage in pips.",
    )
    rollover_blackout_start_utc: str = Field(
        default="21:55", description="Rollover blackout window start time (HH:MM UTC)."
    )
    rollover_blackout_end_utc: str = Field(
        default="22:05", description="Rollover blackout window end time (HH:MM UTC)."
    )
    m1_volatility_adaptive_sizing: bool = Field(
        default=True,
        description="Enable M1 micro-scalping volatility sizing adjustment.",
    )
    m1_spread_to_sigma_ratio_filter: Decimal = Field(
        default=Decimal("1.5"),
        description="Maximum ratio of spread to standard deviation on M1.",
    )
    m1_broker_midnight_blackout_minutes: int = Field(
        default=15, description="Minutes to block trading around midnight on M1."
    )
    operator_approval_fields: dict[str, Any] | None = Field(
        default=None,
        description="Approval signatures/metadata required for live execution.",
    )
    experimental_features: dict[str, Any] = Field(
        default_factory=dict,
        description="Namespaced dictionary for experimental features.",
    )
    risk: RiskSubConfig = Field(
        default_factory=RiskSubConfig, description="General risk sub-configuration."
    )
    drawdown: DrawdownSubConfig = Field(
        default_factory=DrawdownSubConfig, description="Drawdown/loss thresholds."
    )
    correlation: CorrelationSubConfig = Field(
        default_factory=CorrelationSubConfig, description="Correlation parameters."
    )
    tail_risk: TailRiskSubConfig = Field(
        default_factory=TailRiskSubConfig, description="Tail-risk limits."
    )
    execution: ExecutionSubConfig = Field(
        default_factory=ExecutionSubConfig, description="Execution parameters."
    )

    @model_validator(mode="after")
    def _sync_flat_and_nested_configs(self) -> RiskConfig:
        """Synchronize flat and nested configuration fields bi-directionally."""
        import os

        # (Flat field name, Nested config name, Nested field name)
        sync_map = [
            ("max_risk_per_trade", "risk", "max_risk_per_trade"),
            ("max_margin_utilization_pct", "risk", "max_margin_usage"),
            ("max_daily_loss_pct", "drawdown", "daily_loss_hard_limit"),
            ("max_total_loss_pct", "drawdown", "total_drawdown_hard_limit"),
            ("correlation_threshold", "correlation", "reject_threshold"),
            ("var_confidence", "tail_risk", "var_confidence"),
            ("es_confidence", "tail_risk", "es_confidence"),
            ("max_stress_loss_pct", "tail_risk", "stress_loss_limit"),
            ("m1_spread_to_sigma_ratio_filter", "execution", "max_spread_to_sigma"),
        ]

        for flat_name, nested_name, nested_sub_name in sync_map:
            nested_obj = getattr(self, nested_name)

            # Check if environment override is present for the flat field
            env_override = os.getenv(f"HARUQUANT_RISK_{flat_name.upper()}") is not None

            if env_override:
                # Flat field was overridden by environment, so copy from flat to nested
                setattr(nested_obj, nested_sub_name, getattr(self, flat_name))
            elif nested_name in self.model_fields_set:
                # Nested configuration was explicitly set (e.g. from JSON config),
                # so copy from nested to flat
                setattr(self, flat_name, getattr(nested_obj, nested_sub_name))
            elif flat_name in self.model_fields_set:
                # Flat configuration was explicitly set, but nested was not,
                # so copy from flat to nested
                setattr(nested_obj, nested_sub_name, getattr(self, flat_name))
            else:
                # Neither was explicitly set, so copy from flat default
                # to nested default to preserve backward compatibility.
                setattr(nested_obj, nested_sub_name, getattr(self, flat_name))

        return self


class PositionState(RiskContract):
    """Current state snapshot of an open position."""

    position_id: str = Field(..., description="Unique position identifier.")
    symbol: str = Field(..., description="Symbol being traded.")
    direction: Literal["long", "short"] = Field(..., description="Position direction.")
    quantity: Decimal = Field(..., description="Position size in lots.")
    entry_price: Decimal = Field(..., description="Average position entry price.")
    current_price: Decimal = Field(..., description="Current market price.")
    floating_pnl: Decimal = Field(..., description="Current unrealized PnL.")
    margin_required: Decimal = Field(..., description="Margin requirement.")
    strategy_id: str = Field(
        ..., description="ID of the strategy owning this position."
    )
    open_time: datetime = Field(
        ..., description="Timestamp of when the position opened."
    )


class PortfolioState(RiskContract):
    """Consolidated state snapshot of the trading account and positions."""

    account_id: str = Field(..., description="Unique account identifier.")
    balance: Decimal = Field(..., description="Current cash balance.")
    equity: Decimal = Field(..., description="Current net equity.")
    margin_used: Decimal = Field(..., description="Total margin utilized.")
    free_margin: Decimal = Field(..., description="Available free margin.")
    floating_pnl: Decimal = Field(..., description="Total floating unrealized PnL.")
    realized_pnl: Decimal = Field(..., description="Total realized transaction PnL.")
    currency: str = Field(..., description="Account base currency.")
    historical_returns: list[Decimal] = Field(
        default_factory=list, description="Historical portfolio returns for VaR."
    )
    as_of: datetime = Field(..., description="Snapshot calculation timestamp.")
    positions: list[PositionState] = Field(
        default_factory=list, description="List of currently active positions."
    )
    orders: list[Any] = Field(
        default_factory=list, description="List of pending/active orders."
    )
    strategy_allocations: dict[str, Decimal] = Field(
        default_factory=dict, description="Capital allocation details by strategy."
    )


class ProposedTrade(RiskContract):
    """Details of a candidate trade proposed for risk validation."""

    strategy_id: str = Field(..., description="Target strategy.")
    symbol: str = Field(..., description="Trade symbol.")
    side: Literal["buy", "sell"] = Field(..., description="Order side.")
    volume: Decimal = Field(..., description="Requested volume in lots.")
    price: Decimal = Field(
        default=Decimal("0.0"), description="Intended entry execution price."
    )
    stop_loss: Decimal | None = Field(
        default=None, description="Intended stop loss price."
    )
    requires_live_execution: bool = Field(
        default=False, description="True if evaluating live execution environment."
    )

    # Added to fully meet checklist requirements
    requested_size: Decimal | None = Field(
        default=None, description="Requested trade volume size in lots."
    )
    order_type: str | None = Field(
        default=None, description="Order type (e.g. buy_limit, sell_stop)."
    )
    intended_stop: Decimal | None = Field(
        default=None, description="Intended stop loss price."
    )
    intended_target: Decimal | None = Field(
        default=None, description="Intended take profit target price."
    )
    signal_id: str | None = Field(
        default=None, description="Associated signal identifier."
    )
    timestamp: datetime | None = Field(
        default=None, description="Proposed trade creation timestamp."
    )
    expected_holding_period: float | None = Field(
        default=None, description="Expected holding duration in seconds."
    )
    evidence_references: list[RiskEvidenceRef] | None = Field(
        default=None, description="Associated evidence references."
    )

    @model_validator(mode="after")
    def sync_trade_fields(self) -> ProposedTrade:
        """Synchronize alias fields for ProposedTrade."""
        if self.requested_size is None:
            self.requested_size = self.volume
        if self.intended_stop is None:
            self.intended_stop = self.stop_loss
        return self


class ProposedAllocation(RiskContract):
    """Candidate strategy capital allocation budgets."""

    allocations: dict[str, Decimal] = Field(
        ..., description="Desired strategy-to-capital mapping."
    )
    as_of: datetime = Field(..., description="Calculation timestamp.")


class PositionSizingRequest(RiskContract):
    """Details needed to calculate position size options."""

    symbol: str = Field(..., description="Symbol for the trade.")
    method: str = Field(..., description="Sizing method to evaluate.")
    fixed_volume: Decimal | None = Field(
        default=None, description="Static size for fixed_lot."
    )
    risk_percent: Decimal | None = Field(
        default=None, description="Risk budget allocation percent."
    )
    stop_loss_pips: Decimal | None = Field(
        default=None, description="Stop loss distance in pips."
    )
    atr_value: Decimal | None = Field(
        default=None, description="Current ATR value for volatility sizing."
    )
    multiplier: Decimal | None = Field(
        default=None, description="ATR multiplier factor."
    )
    risk_amount: Decimal | None = Field(
        default=None, description="Fixed dollar risk amount."
    )


class PositionSizingResult(RiskContract):
    """Output calculated by the position sizing engine."""

    calculated_volume: Decimal = Field(..., description="Calculated lot volume.")
    stop_distance_pips: Decimal | None = Field(
        default=None, description="Evaluated pip stop distance."
    )
    kelly_fraction_applied: Decimal | None = Field(
        default=None, description="Applied Kelly fraction modifier."
    )
    sizing_method: str = Field(
        default="fixed_lot", description="Applied calculator type."
    )
    constraints_applied: list[str] = Field(
        default_factory=list, description="Names of constraints evaluated."
    )
    risk_contribution: Decimal = Field(
        default=Decimal("0.0"), description="Portfolio risk or margin contribution."
    )


class RiskApprovalToken(RiskContract):
    """Cryptographically signed approval token allowing order routing."""

    token_id: str = Field(..., description="Unique token ID.")
    request_id: str = Field(..., description="Associated request ID.")
    workflow_id: str = Field(..., description="Associated workflow run identifier.")
    approved_action: str = Field(..., description="Approved action payload reference.")
    approver: str = Field(..., description="Authorized approver name/system.")
    expiry_time: datetime = Field(..., description="Expiration timestamp.")
    config_hash: str = Field(..., description="Evaluated risk configuration hash.")
    decision_hash: str = Field(..., description="Evaluated decision payload hash.")
    policy_hash: str | None = Field(
        default=None, description="Active policy signature hash."
    )
    scope: dict[str, Any] = Field(
        default_factory=dict, description="Scope restriction parameters."
    )
    nonce: str = Field(..., description="Anti-replay nonce.")
    signature: str = Field(..., description="Crypto approval signature.")


class RiskDecisionPackage(RiskContract):
    """Canonical output envelope for all Risk Governor reviews."""

    decision_id: str = Field(..., description="Unique decision ID.")
    request_id: str = Field(..., description="Associated request ID.")
    workflow_id: str = Field(..., description="Associated workflow ID.")
    status: str = Field(..., description="Status (approve, reject, block, etc.).")
    rule_key: str = Field(..., description="Key of the primary limiting policy rule.")
    snapshot_as_of: datetime = Field(..., description="Data snapshot timestamp.")
    config_hash: str = Field(..., description="Active configuration hash.")
    reason: str = Field(..., description="Explanation of decision.")
    composite_breach_flags: list[str] = Field(
        default_factory=list, description="Identifiers of all breached constraints."
    )
    calculated_volume: Decimal | None = Field(
        default=None, description="Optionally approved sized volume."
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary decision details."
    )

    # Added to fully meet checklist requirements
    requested_size: Decimal | None = Field(
        default=None, description="Requested lot volume."
    )
    approved_size: Decimal | None = Field(
        default=None, description="Optionally approved lot volume."
    )
    max_allowed_size: Decimal | None = Field(
        default=None, description="Maximum allowed volume."
    )
    action: str | None = Field(default=None, description="Evaluation action category.")
    reason_codes: list[str] | None = Field(
        default=None, description="Breached constraint codes."
    )
    risk_snapshot: PortfolioRiskSnapshot | None = Field(
        default=None, description="Summarized risk snapshot parameters."
    )
    policy_hash: str | None = Field(
        default=None, description="Active policy signature hash."
    )
    decision_token: RiskDecisionToken | None = Field(
        default=None, description="Cryptographically signed approval token."
    )
    expiry: datetime | None = Field(
        default=None, description="Decision validity expiration timestamp."
    )
    audit_hash_reference: str | None = Field(
        default=None, description="Audit trail link reference hash."
    )
    policy_version: str | None = Field(
        default=None, description="Active policy version identifier."
    )
    policy_scope: dict[str, Any] | None = Field(
        default=None, description="Active policy scope attributes."
    )

    @model_validator(mode="after")
    def sync_package_fields(self) -> RiskDecisionPackage:  # noqa: C901, PLR0912
        """Synchronize alias fields for RiskDecisionPackage."""
        if self.approved_size is None:
            self.approved_size = self.calculated_volume
        if self.reason_codes is None:
            self.reason_codes = list(self.composite_breach_flags)
        if self.requested_size is None and self.details:
            vol = self.details.get("requested_volume") or self.details.get("volume")
            if vol is not None:
                self.requested_size = Decimal(str(vol))
        if self.max_allowed_size is None and self.details:
            max_vol = self.details.get("max_volume") or self.details.get(
                "max_allowed_volume"
            )
            if max_vol is not None:
                self.max_allowed_size = Decimal(str(max_vol))
        if self.action is None and self.details:
            self.action = self.details.get("action")
        if self.policy_hash is None and self.details:
            self.policy_hash = self.details.get("policy_hash")
        if self.decision_token is None and self.details:
            token_dict = self.details.get("decision_token") or self.details.get("token")
            if isinstance(token_dict, dict):
                with contextlib.suppress(Exception):
                    self.decision_token = RiskDecisionToken.model_validate(token_dict)
        if self.expiry is None and self.details:
            exp = self.details.get("expiry_time") or self.details.get("expiry")
            if isinstance(exp, str):
                from app.utils.normalization import parse_datetime

                with contextlib.suppress(Exception):
                    self.expiry = parse_datetime(exp)
            elif isinstance(exp, datetime):
                self.expiry = exp
        if self.audit_hash_reference is None and self.details:
            self.audit_hash_reference = self.details.get(
                "audit_hash"
            ) or self.details.get("hash")
        if self.policy_version is None and self.details:
            self.policy_version = self.details.get("policy_version")
        if self.policy_scope is None and self.details:
            self.policy_scope = self.details.get("policy_scope") or self.details.get(
                "scope"
            )
        return self


class StressScenario(RiskContract):
    """Hypothetical macro market shock parameter sets."""

    name: str = Field(..., description="Scenario identifier name.")
    price_shocks: dict[str, Decimal] = Field(
        default_factory=dict, description="Symbol-to-pct price shift map."
    )


class StrategyAdmissionRequest(RiskContract):
    """Request to admit a new strategy to the system registry."""

    strategy_id: str = Field(..., description="Strategy identifier.")
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Performance and validation metrics."
    )


class RiskAssessmentRequest(RiskContract):
    """Input encapsulation for a complete governor evaluation run."""

    proposed_action: ProposedTrade | ProposedAllocation | StrategyAdmissionRequest = (
        Field(..., description="Candidate action under evaluation.")
    )
    portfolio_state: PortfolioState = Field(
        ..., description="Current portfolio snapshot."
    )
    risk_config: RiskConfig = Field(..., description="Target risk configuration.")
    calendar_evidence: list[dict[str, Any]] = Field(
        default_factory=list, description="Calendar news event details."
    )
    market_context: dict[str, Any] = Field(
        default_factory=dict, description="Live market spreads, slippage, volatility."
    )

    # Added to fully meet checklist requirements
    account_state: dict[str, Any] | None = Field(
        default=None, description="Consolidated account balance and parameters."
    )
    market_state: dict[str, Any] | None = Field(
        default=None, description="Underlying active market parameters."
    )
    pending_orders: list[Any] | None = Field(
        default=None, description="Active pending orders."
    )
    open_positions: list[Any] | None = Field(
        default=None, description="Active open positions."
    )
    policy_profile: str | None = Field(
        default=None, description="Associated policy profile name."
    )
    mode: RiskMode | None = Field(
        default=None, description="Evaluation execution mode."
    )
    freshness: datetime | None = Field(
        default=None, description="Market data freshness timestamp."
    )

    @model_validator(mode="after")
    def sync_request_fields(self) -> RiskAssessmentRequest:  # noqa: C901
        """Synchronize alias fields for RiskAssessmentRequest."""
        if self.account_state is None:
            self.account_state = {
                "balance": float(self.portfolio_state.balance),
                "equity": float(self.portfolio_state.equity),
                "margin_used": float(self.portfolio_state.margin_used),
                "free_margin": float(self.portfolio_state.free_margin),
                "currency": self.portfolio_state.currency,
            }
        if self.pending_orders is None:
            self.pending_orders = list(self.portfolio_state.orders)
        if self.open_positions is None:
            self.open_positions = [
                p.model_dump() for p in self.portfolio_state.positions
            ]
        if self.policy_profile is None:
            self.policy_profile = self.risk_config.profile_name
        if self.market_state is None:
            self.market_state = dict(self.market_context)
        if self.freshness is None:
            from app.utils.normalization import parse_datetime, utc_now

            f = self.market_context.get("freshness")
            if isinstance(f, str):
                with contextlib.suppress(Exception):
                    self.freshness = parse_datetime(f)
            elif isinstance(f, datetime):
                self.freshness = f
            else:
                self.freshness = utc_now()
        if self.mode is None:
            mode_str = self.market_context.get("mode")
            allowed_modes = {
                "offline",
                "simulation",
                "paper",
                "shadow",
                "live_readonly",
                "micro_live",
                "full_live",
            }
            if mode_str in allowed_modes:
                self.mode = RiskMode(mode_str)
            else:
                self.mode = RiskMode.PAPER
        return self


class RiskPolicyProfile(RiskContract):
    """Policy profile metadata wrapping config parameters."""

    profile_name: str = Field(..., description="Configuration profile name.")
    description: str | None = Field(
        default=None, description="Optional profile description."
    )
    config: RiskConfig = Field(
        ..., description="Associated risk limits config parameters."
    )


class RiskSnapshot(RiskContract):
    """Base class for all risk governance snapshots."""


class RiskEvidenceRef(RiskContract):
    """Reference tracking data source or external snapshot proof."""

    source: str = Field(..., description="Source system or category.")
    reference_id: str = Field(..., description="Source unique identifier.")
    timestamp: datetime = Field(..., description="Source creation timestamp.")


class AccountRiskSnapshot(RiskSnapshot):
    """Sub-snapshot focused on account equity limits."""

    equity: Decimal = Field(..., description="Net asset equity.")
    balance: Decimal = Field(..., description="Cash balance.")
    free_margin: Decimal = Field(..., description="Available free margin.")
    margin_used: Decimal = Field(..., description="Total used margin.")
    leverage: Decimal = Field(..., description="Account leverage.")
    base_currency: str = Field(..., description="Base currency.")
    timestamp: datetime = Field(..., description="Calculation timestamp.")


class MarketRiskSnapshot(RiskSnapshot):
    """Sub-snapshot capturing market regime parameters."""

    spread: Decimal = Field(..., description="Current symbol spread.")
    volatility: Decimal = Field(..., description="Current volatility metric.")
    session: str = Field(..., description="Market session name.")
    rollover_time: datetime | None = Field(
        default=None, description="Expected next rollover time."
    )
    news_impact: str | None = Field(
        default=None, description="Current near news event impact level."
    )
    freshness: datetime = Field(..., description="Timestamp of quotes freshness.")


class PortfolioRiskSnapshot(RiskSnapshot):
    """Composite snapshot summarizing risk concentrations and metrics."""

    positions: list[PositionState] = Field(
        default_factory=list, description="Open positions snapshot."
    )
    pending_orders: list[Any] = Field(
        default_factory=list, description="Pending orders snapshot."
    )
    in_flight_orders: list[Any] = Field(
        default_factory=list, description="Currently executing orders."
    )
    exposure: Decimal = Field(..., description="Total gross exposure.")
    var_es: Decimal = Field(..., description="Portfolio Value-at-Risk.")
    stress_loss: Decimal = Field(..., description="Max projected stress test loss.")
    drawdown: Decimal = Field(..., description="Current drawdown percentage.")


class PositionRiskSnapshot(RiskSnapshot):
    """Risk breakdown of a single open position."""

    position_id: str = Field(..., description="Position ID.")
    signed_size: Decimal = Field(
        ..., description="Position size (positive long, negative short)."
    )
    entry_price: Decimal = Field(..., description="Entry price level.")
    current_price: Decimal = Field(..., description="Current market price.")
    pnl: Decimal = Field(..., description="Floating unrealized PnL.")
    risk: Decimal = Field(..., description="Stop loss risk amount.")
    margin: Decimal = Field(..., description="Margin requirement.")
    strategy_id: str = Field(..., description="Strategy identifier.")
    timestamp: datetime = Field(..., description="As-of timestamp.")


class PendingOrderRiskSnapshot(RiskSnapshot):
    """Exposure details of a pending order."""

    order_id: str = Field(..., description="Order identifier.")
    exposure: Decimal = Field(..., description="Order potential exposure.")


class CurrencyLegExposure(RiskContract):
    """Currency breakdown for a single leg of a trade."""

    currency: str = Field(..., description="Target currency.")
    signed_amount: Decimal = Field(..., description="Signed position amount.")


class CurrencyExposure(RiskContract):
    """Portfolio currency leg exposure breakdown."""

    gross: Decimal = Field(..., description="Gross exposure amount.")
    net: Decimal = Field(..., description="Net exposure amount.")
    account_currency_equivalent: Decimal = Field(
        ..., description="Exposure in account currency."
    )


class SymbolExposure(RiskContract):
    """Portfolio symbol exposure breakdown."""

    symbol: str = Field(..., description="Target symbol.")
    signed_amount: Decimal = Field(..., description="Signed symbol amount.")
    gross: Decimal = Field(..., description="Gross exposure amount.")
    net: Decimal = Field(..., description="Net exposure amount.")
    account_currency_equivalent: Decimal = Field(
        ..., description="Exposure in account currency."
    )


class CorrelationSnapshot(RiskSnapshot):
    """Rolling correlation matrix output details."""

    matrix: dict[str, dict[str, Decimal]] = Field(
        default_factory=dict, description="Correlation values table."
    )
    lookback: int = Field(..., description="Lookback window length.")
    timeframe: str = Field(..., description="Bar timeframe evaluated.")
    method: str = Field(..., description="Correlation formula method.")
    sample_count: int = Field(..., description="Total samples aligned.")
    fallback_status: bool = Field(
        ..., description="True if default fallback was applied."
    )


class CorrelationMatrix(RiskContract):
    """Calculated pairwise correlation matrix for symbols."""

    symbols: list[str] = Field(..., description="Ordered list of symbol names.")
    matrix: dict[str, dict[str, Decimal]] = Field(
        ..., description="Symbol to symbol pairwise correlation coefficients."
    )


class CorrelationCluster(RiskContract):
    """Cluster of correlated symbols and their aggregated risk exposure."""

    cluster_id: str = Field(..., description="Unique identifier for the cluster.")
    symbols: list[str] = Field(..., description="Symbols included in this cluster.")
    exposure: Decimal = Field(
        ..., description="Aggregated gross exposure in account currency."
    )


class VaRSnapshot(RiskSnapshot):
    """Calculated Value-at-Risk parameters."""

    method: str = Field(..., description="Method used (e.g. parametric, historical).")
    confidence: Decimal = Field(..., description="Confidence level (e.g. 0.95).")
    portfolio_volatility: Decimal = Field(..., description="Portfolio volatility.")
    exposure: Decimal = Field(..., description="Evaluated exposure size.")
    result: Decimal = Field(..., description="VaR value.")
    assumptions: dict[str, Any] = Field(
        default_factory=dict, description="Underlying model assumptions."
    )


class ExpectedShortfallSnapshot(RiskSnapshot):
    """Calculated Expected Shortfall metrics."""

    confidence: Decimal = Field(..., description="Confidence level (e.g. 0.95).")
    threshold_loss: Decimal = Field(..., description="Threshold loss level.")
    average_tail_loss: Decimal = Field(..., description="Average loss in tail.")
    sample_count: int = Field(..., description="Return samples evaluated.")
    method: str = Field(..., description="Expected shortfall method name.")


class StressScenarioResult(RiskContract):
    """Outcome of a single stress scenario simulation."""

    scenario_name: str = Field(..., description="Name of the stress scenario.")
    impact_pct: Decimal = Field(
        ..., description="Projected portfolio loss/gain percentage."
    )
    projected_equity: Decimal = Field(
        ..., description="Estimated portfolio equity after shock."
    )
    pass_status: bool = Field(
        default=True, description="True if projected loss is within limits."
    )
    reason_codes: list[str] = Field(
        default_factory=list, description="Reason codes for failure status."
    )


class MarginRiskSnapshot(RiskSnapshot):
    """Margin metrics snapshot."""

    projected_margin: Decimal = Field(
        ..., description="Projected total margin after trade."
    )
    free_margin: Decimal = Field(..., description="Free margin available.")
    margin_usage: Decimal = Field(..., description="Margin usage percentage.")
    leverage: Decimal = Field(..., description="Active leverage multiplier.")


class DrawdownState(RiskContract):
    """Drawdown throttling status metrics."""

    current_drawdown: Decimal = Field(..., description="Current drawdown percentage.")
    soft_limit: Decimal = Field(..., description="Advisory soft limit percentage.")
    hard_limit: Decimal = Field(..., description="Hard blocking limit percentage.")
    multiplier: Decimal = Field(..., description="Applied risk scale step-down factor.")


class ExecutionRiskSnapshot(RiskSnapshot):
    """Execution feasibility conditions."""

    spread: Decimal = Field(..., description="Active spread.")
    slippage: Decimal = Field(..., description="Active slippage.")
    stop_level: Decimal = Field(..., description="Broker minimum stop level.")
    freeze_level: Decimal = Field(..., description="Broker order modify freeze level.")
    lot_step: Decimal = Field(..., description="Lot size minimum step granularity.")
    marketability: bool = Field(
        ..., description="True if conditions permit order entries."
    )


class RiskRejection(RiskContract):
    """Rejection outcome reasons."""

    code: str = Field(..., description="Reason code identifier.")
    severity: str = Field(..., description="Outcome severity.")
    reason: str = Field(..., description="Explanation string.")
    violated_limit: str | None = Field(
        default=None, description="Name of limit violated."
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Associated proof references."
    )


class RiskWarning(RiskContract):
    """Warning messages produced during evaluation."""

    code: str = Field(..., description="Reason code identifier.")
    severity: str = Field(..., description="Outcome severity.")
    reason: str = Field(..., description="Explanation string.")


class RiskReduction(RiskContract):
    """Details of a volume scale-down suggestion."""

    reduced_volume: Decimal = Field(..., description="Target scaled lot size.")
    reason: str = Field(..., description="Reason for reduction.")


class RiskMemo(RiskContract):
    """Generic description or comment metadata."""

    content: str = Field(..., description="Comment content.")


class RiskBudget(RiskContract):
    """Strategy allocation limit limits."""

    strategy_id: str = Field(..., description="Strategy identifier.")
    limit_pct: Decimal = Field(..., description="Allocation ceiling percentage.")


class RiskBudgetUtilization(RiskContract):
    """Strategy budget utilization snapshot."""

    strategy_id: str = Field(..., description="Strategy identifier.")
    utilized_pct: Decimal = Field(..., description="Allocation usage percentage.")


class RiskAuditEvent(RiskContract):
    """Tamper-evident record of a single governor request."""

    event_id: str = Field(..., description="Unique event ID.")
    decision_id: str = Field(..., description="Associated decision ID.")
    policy_name: str = Field(..., description="Target policy rule category name.")
    action_taken: str = Field(..., description="Synthesized outcome action.")
    payload_hash: str = Field(..., description="Hash of target inputs evaluated.")
    severity: str = Field(..., description="Outcome severity level.")
    previous_hash: str = Field(
        default="", description="SHA256 of the previous audit event."
    )
    hash: str = Field(default="", description="SHA256 of the current audit event.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Event creation timestamp.",
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed request/outcome payload context."
    )


class RiskDecisionToken(RiskContract):
    """Token representing risk decision."""

    token_id: str = Field(..., description="Unique token ID.")
    expiry: datetime = Field(..., description="Expiration timestamp.")
    policy_hash: str = Field(..., description="Policy hash.")
    config_hash: str = Field(..., description="Active configuration hash.")
    signature: str = Field(..., description="Approval signature.")
    revoked: bool = Field(default=False, description="True if token is revoked.")
    scope: dict[str, Any] = Field(
        default_factory=dict, description="Scope restriction parameters."
    )


class PolicyScope(RiskContract):
    """Scope criteria for selecting matching policy rules."""

    environment: str | None = Field(
        default=None, description="Scope execution environment filter."
    )
    mode: RiskMode | None = Field(
        default=None, description="Scope execution mode filter."
    )
    account_id: str | None = Field(
        default=None, description="Scope account identifier filter."
    )
    strategy_id: str | None = Field(
        default=None, description="Scope strategy identifier filter."
    )
    symbol: str | None = Field(default=None, description="Scope symbol filter.")
    currency: str | None = Field(default=None, description="Scope currency filter.")
    workflow_id: str | None = Field(
        default=None, description="Scope workflow ID filter."
    )
    operator_role: str | None = Field(
        default=None, description="Scope operator role filter."
    )


class PolicyRule(RiskContract):
    """Scoped override rules for risk config profiles."""

    rule_id: str = Field(..., description="Unique identifier for the policy rule.")
    scope: PolicyScope = Field(
        ..., description="Evaluation scope for this policy rule."
    )
    overrides: dict[str, Any] = Field(
        default_factory=dict, description="Config limit values to override."
    )
    expiry_time: datetime | None = Field(
        default=None, description="Timestamp after which rule is ignored."
    )
    requires_approval: bool = Field(
        default=False, description="True if rule requires approval token."
    )
    min_approver_role: str | None = Field(
        default=None, description="Minimum role allowed to sign off on overrides."
    )


class PolicyEnforcementResult(RiskContract):
    """Result of running policy engine resolution."""

    status: RiskDecisionStatus = Field(
        ..., description="Resulting status outcome (approve, reject, block)."
    )
    reason: str = Field(..., description="Result reason description.")
    policy_hash: str = Field(..., description="Calculated SHA256 of the policy rules.")
    resolved_config: RiskConfig = Field(
        ..., description="RiskConfig resolved after merging scope overrides."
    )
    breaches: list[str] = Field(
        default_factory=list, description="List of rule/constraint breach details."
    )
    policy_version: str | None = Field(
        default=None, description="Active policy version identifier."
    )
    policy_scope: dict[str, Any] | None = Field(
        default=None, description="Active policy scope attributes."
    )


class KillSwitchStateEnum(StrEnum):
    """Safety kill-switch states.

    States progress: INACTIVE → TRIGGERED → ACTIVE → PENDING_RESUME → INACTIVE.
    LOCKED is a special terminal state requiring admin/compliance intervention.
    UNKNOWN signals an indeterminate state and must always fail closed.
    """

    INACTIVE = "inactive"
    ACTIVE = "active"
    LOCKED = "locked"
    UNKNOWN = "unknown"  # state cannot be determined → always fail closed
    TRIGGERED = "triggered"  # halt signalled, not yet fully propagated
    PENDING_RESUME = "pending_resume"  # awaiting governed approval to deactivate


class KillSwitchReason(StrEnum):
    """Reason codes explaining why a kill switch was triggered."""

    MANUAL_HALT = "manual_halt"
    DAILY_LOSS_BREACH = "daily_loss_breach"
    DRAWDOWN_BREACH = "drawdown_breach"
    AUDIT_FAILURE = "audit_failure"
    EXTREME_SPREAD = "extreme_spread"
    PORTFOLIO_UNRECONCILED = "portfolio_unreconciled"
    BROKER_DISCONNECT = "broker_disconnect"
    MARGIN_EMERGENCY = "margin_emergency"


def create_risk_decision_package(
    decision_id: str,
    request_id: str,
    workflow_id: str,
    status: RiskDecisionStatus,
    rule_key: str,
    config_hash: str,
    reason: str,
    composite_breach_flags: list[str],
    calculated_volume: Decimal,
    details: dict[str, Any] | None = None,
) -> RiskDecisionPackage:
    """Factory function to build a canonical RiskDecisionPackage.

    Args:
        decision_id: Unique decision ID.
        request_id: Associated request ID.
        workflow_id: Workflow execution ID.
        status: Synthesized decision outcome.
        rule_key: Triggering rules matched.
        config_hash: Reference config SHA hash.
        reason: Explanation message.
        composite_breach_flags: Active breach names list.
        calculated_volume: Sized volume value.
        details: Custom context dictionaries.

    Returns:
        RiskDecisionPackage: Populated decision package instance.
    """
    from app.utils.normalization import utc_now

    return RiskDecisionPackage(
        decision_id=decision_id,
        request_id=request_id,
        workflow_id=workflow_id,
        status=status,
        rule_key=rule_key,
        snapshot_as_of=utc_now(),
        config_hash=config_hash,
        reason=reason,
        composite_breach_flags=composite_breach_flags,
        calculated_volume=calculated_volume,
        details=details or {},
    )


ProposedTrade.model_rebuild()
RiskAssessmentRequest.model_rebuild()
RiskDecisionPackage.model_rebuild()
