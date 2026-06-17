"""Risk domain models and public schemas.

This module provides public Pydantic V2 contracts for the risk service.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.utils.errors import InvalidRiskConfigError, ValidationError


class RiskBaseModel(BaseModel):
    """Base model enforcing common Pydantic V2 configurations."""

    model_config = {
        "allow_inf_nan": False,
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
    }


class RiskConfig(RiskBaseModel):
    """Configuration profile containing risk limits and parameters."""

    profile_name: str = Field(default="prop_firm_default")
    config_version: str = Field(default="1.0.0")
    config_hash: str = Field(default="genesis_hash")

    # Loss & Drawdown limits
    max_daily_loss_pct: Decimal = Field(default=Decimal("0.05"))
    max_total_loss_pct: Decimal = Field(default=Decimal("0.10"))
    profit_target_pct: Decimal = Field(default=Decimal("0.10"))

    # Leverage, Margin & Exposure limits
    max_margin_utilization_pct: Decimal = Field(default=Decimal("0.80"))
    max_effective_leverage: Decimal = Field(default=Decimal("30.0"))
    correlation_threshold: Decimal = Field(default=Decimal("0.50"))

    # News Blackout
    news_blackout_minutes: int = Field(default=10)
    timezone: str = Field(default="UTC")

    # Sizing parameters
    default_kelly_fraction: Decimal = Field(default=Decimal("0.25"))
    min_kelly_trades: int = Field(default=30)
    require_stop_loss: bool = Field(default=True)

    # VaR / CVaR parameters
    var_confidence: Decimal = Field(default=Decimal("0.95"))
    var_lookback_days: int = Field(default=250)
    var_method: Literal["historical", "parametric"] = Field(default="historical")
    parametric_distribution: Literal["heavy_tailed", "gaussian"] = Field(
        default="heavy_tailed"
    )

    # Flow & Governance flags
    exit_liquidity_stress_enabled: bool = Field(default=True)
    correlation_adjusted_sizing_enabled: bool = Field(default=True)
    step_down_controls_enabled: bool = Field(default=True)
    freshness_tolerance_seconds: int = Field(default=60)
    in_flight_tolerance_pct: Decimal = Field(default=Decimal("0.01"))
    audit_hash_chaining_enabled: bool = Field(default=True)
    double_spend_prevention_owner: Literal["risk_cache", "external"] = Field(
        default="risk_cache"
    )

    @field_validator(
        "max_daily_loss_pct",
        "max_total_loss_pct",
        "profit_target_pct",
        "max_margin_utilization_pct",
        "max_effective_leverage",
        "correlation_threshold",
        "default_kelly_fraction",
        "var_confidence",
        "in_flight_tolerance_pct",
    )
    @classmethod
    def validate_non_negative_decimal(cls, val: Decimal) -> Decimal:
        """Validate decimal values are non-negative and finite."""
        if val < 0:
            raise InvalidRiskConfigError("Decimal values must be non-negative.")
        return val

    @field_serializer(
        "max_daily_loss_pct",
        "max_total_loss_pct",
        "profit_target_pct",
        "max_margin_utilization_pct",
        "max_effective_leverage",
        "correlation_threshold",
        "default_kelly_fraction",
        "var_confidence",
        "in_flight_tolerance_pct",
    )
    def serialize_decimal(self, val: Decimal) -> str:
        """Serialize Decimals to string representation to preserve precision."""
        return str(val)


class PositionState(RiskBaseModel):
    """State profile of a single open position."""

    position_id: str
    symbol: str
    direction: Literal["long", "short"]
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    floating_pnl: Decimal
    margin_required: Decimal
    strategy_id: str
    open_time: datetime

    @field_validator("quantity", "entry_price", "current_price", "margin_required")
    @classmethod
    def validate_positive_decimal(cls, val: Decimal) -> Decimal:
        """Enforce positive values."""
        if val <= 0:
            raise ValidationError(
                "Price, quantity and margin must be greater than zero."
            )
        return val

    @field_serializer(
        "quantity",
        "entry_price",
        "current_price",
        "stop_loss",
        "take_profit",
        "floating_pnl",
        "margin_required",
    )
    def serialize_decimal(self, val: Decimal | None) -> str | None:
        """Serialize Decimals to string."""
        return str(val) if val is not None else None


class OrderState(RiskBaseModel):
    """State profile of a pending order."""

    order_id: str
    symbol: str
    direction: Literal["buy", "sell"]
    order_type: Literal["limit", "stop", "market"]
    quantity: Decimal
    price: Decimal
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    strategy_id: str
    expiry_time: datetime | None = None

    @field_validator("quantity", "price")
    @classmethod
    def validate_positive_decimal(cls, val: Decimal) -> Decimal:
        """Enforce positive values."""
        if val <= 0:
            raise ValidationError("Quantity and price must be greater than zero.")
        return val

    @field_serializer("quantity", "price", "stop_loss", "take_profit")
    def serialize_decimal(self, val: Decimal | None) -> str | None:
        """Serialize Decimals to string."""
        return str(val) if val is not None else None


class PortfolioState(RiskBaseModel):
    """Durable state representation of a complete trading account portfolio."""

    account_id: str
    balance: Decimal
    equity: Decimal
    margin_used: Decimal
    free_margin: Decimal
    floating_pnl: Decimal
    realized_pnl: Decimal
    currency: str = "USD"
    positions: list[PositionState] = Field(default_factory=list)
    orders: list[OrderState] = Field(default_factory=list)
    strategy_allocations: dict[str, Decimal] = Field(default_factory=dict)
    historical_returns: list[Decimal] = Field(default_factory=list)
    as_of: datetime

    @field_validator("balance", "equity", "margin_used", "free_margin")
    @classmethod
    def validate_non_negative(cls, val: Decimal) -> Decimal:
        """Enforce non-negative values for core account states."""
        if val < 0:
            raise ValidationError("Account values must be non-negative.")
        return val

    @field_serializer(
        "balance",
        "equity",
        "margin_used",
        "free_margin",
        "floating_pnl",
        "realized_pnl",
    )
    def serialize_decimal(self, val: Decimal) -> str:
        """Serialize Decimals to string."""
        return str(val)

    @field_serializer("strategy_allocations")
    def serialize_strategy_allocations(self, val: dict[str, Decimal]) -> dict[str, str]:
        """Serialize strategy allocations dictionary Decimals."""
        return {k: str(v) for k, v in val.items()}

    @field_serializer("historical_returns")
    def serialize_historical_returns(self, val: list[Decimal]) -> list[str]:
        """Serialize returns list Decimals."""
        return [str(v) for v in val]


class RiskSnapshot(RiskBaseModel):
    """Snapshot representation of analyzed portfolio risk metrics."""

    account_id: str
    as_of: datetime
    config_hash: str

    # Portfolio level indicators
    balance: Decimal
    equity: Decimal
    total_drawdown_pct: Decimal
    daily_drawdown_pct: Decimal
    margin_utilization_pct: Decimal
    effective_leverage: Decimal

    # Exposure metrics
    net_exposure: Decimal
    gross_exposure: Decimal
    exposure_by_symbol: dict[str, Decimal]
    exposure_by_strategy: dict[str, Decimal]
    exposure_by_currency: dict[str, Decimal]

    # Volatility / Tail risk metrics
    portfolio_volatility: Decimal
    var_value: Decimal
    cvar_value: Decimal

    # Diagnostic flags
    missing_evidence_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_serializer(
        "balance",
        "equity",
        "total_drawdown_pct",
        "daily_drawdown_pct",
        "margin_utilization_pct",
        "effective_leverage",
        "net_exposure",
        "gross_exposure",
        "portfolio_volatility",
        "var_value",
        "cvar_value",
    )
    def serialize_decimal(self, val: Decimal) -> str:
        """Serialize Decimals to string."""
        return str(val)

    @field_serializer(
        "exposure_by_symbol", "exposure_by_strategy", "exposure_by_currency"
    )
    def serialize_exposure_dict(self, val: dict[str, Decimal]) -> dict[str, str]:
        """Serialize Decimals inside exposure maps."""
        return {k: str(v) for k, v in val.items()}


class ProposedTrade(RiskBaseModel):
    """Representation of a trade proposed by a strategy."""

    strategy_id: str
    symbol: str
    side: Literal["buy", "sell"]
    volume: Decimal
    price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    requires_live_execution: bool = False

    @field_validator("volume")
    @classmethod
    def validate_positive_volume(cls, val: Decimal) -> Decimal:
        """Enforce positive volume."""
        if val <= 0:
            raise ValidationError("Trade volume must be greater than zero.")
        return val

    @field_serializer("volume", "price", "stop_loss", "take_profit")
    def serialize_decimal(self, val: Decimal | None) -> str | None:
        """Serialize Decimals to string."""
        return str(val) if val is not None else None


class PositionSizingRequest(RiskBaseModel):
    """Request schema for sizing calculator."""

    symbol: str
    method: Literal[
        "fixed_lot",
        "fixed_risk",
        "milestone",
        "kelly_criterion",
        "volatility",
        "fixed_fractional",
    ]
    risk_percent: Decimal | None = None
    risk_amount: Decimal | None = None
    stop_loss_pips: Decimal | None = None
    fixed_volume: Decimal | None = None
    atr_value: Decimal | None = None
    multiplier: Decimal | None = None

    @field_serializer(
        "risk_percent",
        "risk_amount",
        "stop_loss_pips",
        "fixed_volume",
        "atr_value",
        "multiplier",
    )
    def serialize_decimal(self, val: Decimal | None) -> str | None:
        """Serialize Decimals."""
        return str(val) if val is not None else None


class PositionSizingResult(RiskBaseModel):
    """Result response from sizing calculator."""

    calculated_volume: Decimal
    method_applied: str
    stop_distance_pips: Decimal | None = None
    kelly_fraction_applied: Decimal | None = None
    notes: list[str] = Field(default_factory=list)

    @field_serializer(
        "calculated_volume", "stop_distance_pips", "kelly_fraction_applied"
    )
    def serialize_decimal(self, val: Decimal | None) -> str | None:
        """Serialize Decimals."""
        return str(val) if val is not None else None


class ProposedAllocation(RiskBaseModel):
    """Proposal of portfolio capital allocations to strategies."""

    allocations: dict[str, Decimal]
    as_of: datetime

    @field_serializer("allocations")
    def serialize_allocations(self, val: dict[str, Decimal]) -> dict[str, str]:
        """Serialize allocations Dict."""
        return {k: str(v) for k, v in val.items()}


class RegimeAssessment(RiskBaseModel):
    """Regime classification output of the portfolio."""

    volatility_regime: Literal["normal", "high", "extreme"]
    liquidity_regime: Literal["normal", "thin", "crisis"]
    correlation_regime: Literal["normal", "stressed"]
    drawdown_regime: Literal[
        "normal", "caution", "restricted", "blocked", "kill_switch_required"
    ]
    is_crisis: bool = False
    risk_multiplier: Decimal = Field(default=Decimal("1.0"))
    transition_timestamp: datetime
    previous_regime: str | None = None
    reason: str

    @field_serializer("risk_multiplier")
    def serialize_decimal(self, val: Decimal) -> str:
        """Serialize Decimals."""
        return str(val)


class ScenarioResult(RiskBaseModel):
    """Advisory result of a what-if stress scenario test."""

    scenario_name: str
    impact_pct: Decimal
    projected_equity: Decimal
    projected_drawdown_pct: Decimal
    margin_utilization_pct: Decimal
    is_margin_call: bool
    is_stop_out: bool

    @field_serializer(
        "impact_pct",
        "projected_equity",
        "projected_drawdown_pct",
        "margin_utilization_pct",
    )
    def serialize_decimal(self, val: Decimal) -> str:
        """Serialize Decimals."""
        return str(val)


class RiskApprovalToken(RiskBaseModel):
    """Cryptographically verifiable approval token for risk limit overrides."""

    token_id: str
    request_id: str
    workflow_id: str
    approved_action: str
    approver: str
    expiry_time: datetime
    config_hash: str
    decision_hash: str
    scope: dict[str, str]
    nonce: str
    signature: str


class RiskDecisionPackage(RiskBaseModel):
    """Canonical packaging wrapper for risk governor decisions."""

    decision_id: str
    request_id: str
    workflow_id: str
    status: Literal[
        "approve",
        "warn",
        "needs_approval",
        "needs_more_evidence",
        "reject",
        "block",
        "error",
    ]
    rule_key: str
    primary_failure_limit: str | None = None
    composite_breach_flags: list[str] = Field(default_factory=list)
    approval_required: bool = False
    approval_token: RiskApprovalToken | None = None
    snapshot_as_of: datetime
    config_hash: str
    reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskAuditRecord(RiskBaseModel):
    """Durable cryptographically chained audit record of risk events."""

    record_id: str
    timestamp: datetime
    request_id: str
    workflow_id: str
    event_type: str
    config_hash: str
    input_summary: dict[str, Any]
    limit_results: list[dict[str, Any]]
    final_decision: str
    previous_hash: str
    record_hash: str


class RiskReport(RiskBaseModel):
    """Standardized report generation wrapper for risk outputs."""

    report_id: str
    timestamp: datetime
    format: Literal["markdown", "json"]
    content: str
