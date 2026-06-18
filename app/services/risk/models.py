"""Risk governance models and enums module.

Defines all Pydantic models for inputs, intermediate calculations, snapshots,
and decision packages used by the RiskGovernor.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field

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


class RiskEvidenceRef(RiskContract):
    """Reference tracking data source or external snapshot proof."""

    source: str = Field(..., description="Source system or category.")
    reference_id: str = Field(..., description="Source unique identifier.")
    timestamp: datetime = Field(..., description="Source creation timestamp.")


class AccountRiskSnapshot(RiskContract):
    """Sub-snapshot focused on account equity limits."""

    equity: Decimal = Field(..., description="Net asset equity.")
    balance: Decimal = Field(..., description="Cash balance.")
    free_margin: Decimal = Field(..., description="Available free margin.")
    margin_used: Decimal = Field(..., description="Total used margin.")
    leverage: Decimal = Field(..., description="Account leverage.")
    base_currency: str = Field(..., description="Base currency.")
    timestamp: datetime = Field(..., description="Calculation timestamp.")


class MarketRiskSnapshot(RiskContract):
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


class PortfolioRiskSnapshot(RiskContract):
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


class PositionRiskSnapshot(RiskContract):
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


class PendingOrderRiskSnapshot(RiskContract):
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


class CorrelationSnapshot(RiskContract):
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


class VaRSnapshot(RiskContract):
    """Calculated Value-at-Risk parameters."""

    method: str = Field(..., description="Method used (e.g. parametric, historical).")
    confidence: Decimal = Field(..., description="Confidence level (e.g. 0.95).")
    portfolio_volatility: Decimal = Field(..., description="Portfolio volatility.")
    exposure: Decimal = Field(..., description="Evaluated exposure size.")
    result: Decimal = Field(..., description="VaR value.")
    assumptions: dict[str, Any] = Field(
        default_factory=dict, description="Underlying model assumptions."
    )


class ExpectedShortfallSnapshot(RiskContract):
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


class MarginRiskSnapshot(RiskContract):
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


class ExecutionRiskSnapshot(RiskContract):
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


class KillSwitchStateEnum(StrEnum):
    """Safety kill-switch states."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    LOCKED = "locked"


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
