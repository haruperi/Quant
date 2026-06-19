"""Official AI tools facade for the Risk Governance Service.

Provides the standardized tool interface and wrappers for risk calculations,
reviews, overrides, reports, and controls.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from app.services.risk.config import load_risk_config
from app.services.risk.correlation import (
    calculate_correlation_matrix as _calculate_correlation_matrix,
)
from app.services.risk.exposure import (
    calculate_currency_exposure as _calculate_currency_exposure,
)
from app.services.risk.governor import RiskGovernor
from app.services.risk.lifecycle import review_live_readiness as _review_live_readiness
from app.services.risk.limits import check_risk_limits as _check_risk_limits
from app.services.risk.models import (
    PortfolioRiskSnapshot,
    PortfolioState,
    PositionSizingRequest,
    ProposedAllocation,
    ProposedTrade,
    RiskApprovalToken,
    RiskAssessmentRequest,
    StrategyAdmissionRequest,
)
from app.services.risk.models import (
    create_risk_decision_package as _create_risk_decision_package,
)

# Service Underlyer Imports
from app.services.risk.policy import (
    load_risk_policy as _load_risk_policy,
)
from app.services.risk.policy import (
    validate_risk_policy as _validate_risk_policy,
)
from app.services.risk.regime import assess_risk_regime as _assess_risk_regime
from app.services.risk.sizing import calculate_position_size as _calculate_position_size
from app.services.risk.storage import InMemoryRiskStateStore
from app.services.risk.stress import build_default_scenario_registry
from app.services.risk.var_es import (
    calculate_expected_shortfall as _calculate_expected_shortfall,
)
from app.services.risk.var_es import (
    calculate_portfolio_var as _calculate_portfolio_var,
)
from app.services.risk.var_es import (
    calculate_var_es_snapshots,
)
from app.utils.errors import exception_to_error_payload
from app.utils.logger import logger
from app.utils.standard import build_metadata, error_response, success_response

# Shared persistence registry for tool invocations
_shared_store = InMemoryRiskStateStore()
_shared_governor = RiskGovernor(
    state_store=_shared_store,
    audit_sink=_shared_store,
    policy_store=_shared_store,
    decision_store=_shared_store,
)


def get_shared_store() -> InMemoryRiskStateStore:
    """Retrieve the shared InMemoryRiskStateStore instance."""
    return _shared_store


def get_shared_governor() -> RiskGovernor:
    """Retrieve the shared RiskGovernor instance."""
    return _shared_governor


_SUCCESS_MSG_TEMPLATES: dict[str, Callable[[Any], str]] = {
    "build_portfolio_risk_snapshot": lambda _: (
        "Successfully compiled portfolio risk snapshot."
    ),
    "review_trade_risk": lambda d: (
        f"Trade risk review completed with status: {d.get('status')}."
    ),
    "calculate_position_size": lambda d: (
        f"Position size calculation complete: {d.get('calculated_volume')} lots."
    ),
    "assess_risk_regime": lambda d: (
        f"Market regime assessment complete: {d.get('regime')}."
    ),
    "review_strategy_admission": lambda d: (
        f"Strategy admission review completed with status: {d.get('status')}."
    ),
    "review_allocation_proposal": lambda d: (
        f"Allocation proposal review completed with status: {d.get('status')}."
    ),
    "run_portfolio_risk_governor": lambda d: (
        f"Portfolio risk governor run completed with status: {d.get('status')}."
    ),
    "validate_risk_approval_token": lambda _: "Token validation check completed.",
    "check_risk_kill_switch": lambda _: "Kill switch status check completed.",
    "run_stress_scenario_analysis": lambda d: (
        f"Scenario analysis complete. Executed {len(d)} scenarios."
    ),
    "generate_risk_report": lambda _: "Risk report generated successfully.",
    "load_risk_policy": lambda _: "Successfully loaded risk policy.",
    "validate_risk_policy": lambda _: "Policy validation completed.",
    "calculate_currency_exposure": lambda _: "Currency exposure calculation complete.",
    "calculate_correlation_matrix": lambda _: (
        "Correlation matrix calculation complete."
    ),
    "calculate_portfolio_var": lambda _: "Value-at-Risk calculation complete.",
    "calculate_expected_shortfall": lambda _: (
        "Expected Shortfall calculation complete."
    ),
    "check_risk_limits": lambda _: "Risk limits check complete.",
    "review_live_readiness": lambda _: "Live readiness review complete.",
    "create_risk_decision_package": lambda _: "Risk decision package created.",
}


def risk_tool(
    name: str,
    version: str = "1.0.0",
    category: str = "risk",
    risk_level: Literal["low", "medium", "high", "critical"] = "low",
    *,
    reads: bool = False,
    writes: bool = False,
    updates: bool = False,
    deletes: bool = False,
    requires_network: bool = False,
) -> Callable[..., Callable[..., dict[str, Any]]]:
    """Decorator standardizing risk tool metadata and error handling envelopes.

    Ensures trades=False is strictly enforced on all risk governance tools.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
            request_id = kwargs.get("request_id")
            t_start = time.perf_counter()
            try:
                data = func(*args, **kwargs)
                meta = build_metadata(
                    tool_name=name,
                    tool_version=version,
                    tool_category=category,
                    tool_risk_level=risk_level,
                    request_id=request_id,
                    reads=reads,
                    writes=writes,
                    updates=updates,
                    deletes=deletes,
                    trades=False,  # Enforce places_trade=False
                    requires_network=requires_network,
                    start_time=t_start,
                )
                msg = _SUCCESS_MSG_TEMPLATES.get(
                    name, lambda _: f"Successfully executed tool {name}."
                )(data)
                return success_response(  # type: ignore[return-value]
                    message=msg,
                    data=data,
                    metadata=meta,
                )
            except Exception as e:  # noqa: BLE001
                logger.error(
                    f"Risk tool {name} error: {e}",
                    extra={"request_id": request_id},
                )
                meta = build_metadata(
                    tool_name=name,
                    tool_version=version,
                    tool_category=category,
                    tool_risk_level=risk_level,
                    request_id=request_id,
                    reads=reads,
                    writes=writes,
                    updates=updates,
                    deletes=deletes,
                    trades=False,
                    requires_network=requires_network,
                    start_time=t_start,
                )
                payload = exception_to_error_payload(
                    e, default_code="TOOL_EXECUTION_FAILED"
                )
                return error_response(  # type: ignore[return-value]
                    message=f"Failed to execute {name}.",
                    code=payload["code"],
                    details=payload["details"],
                    metadata=meta,
                )

        return wrapper

    return decorator


def _validate_live_sensitive_tool_context(
    market_context: dict[str, Any],
    config_profile: str,
    operator_role: str | None = None,
) -> None:
    """Validate live-sensitive requests.

    Ensures they supply valid mode, policy profile, operator authority,
    and freshness evidence.

    Args:
        market_context: Injected runtime flags and metrics.
        config_profile: Active configuration profile name.
        operator_role: Operator role string.

    Raises:
        ValidationError: If validation fails.
    """
    from app.utils.errors import ValidationError

    mode = market_context.get("mode", "paper")
    env = market_context.get("environment", "local")
    is_live = mode in {"micro_live", "full_live"} or env in {"production", "live"}
    if is_live:
        if mode not in {"micro_live", "full_live"}:
            msg = f"Invalid live execution mode: '{mode}'."
            raise ValidationError(msg)
        if not config_profile or not isinstance(config_profile, str):
            msg = "A valid policy profile name is required in live execution mode."
            raise ValidationError(msg)
        if not operator_role or str(operator_role).lower() not in {
            "operator",
            "risk_manager",
            "admin",
            "compliance_officer",
        }:
            msg = "Missing or unauthorized operator role for live execution mode."
            raise ValidationError(msg)
        if not market_context.get("freshness"):
            msg = "Missing freshness evidence for live execution mode."
            raise ValidationError(msg)


# --- 1. load_risk_policy ---
@risk_tool(name="load_risk_policy", risk_level="low", reads=True)
def load_risk_policy(
    profile_name: str = "default",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Load active policy configuration.

    When agents should use:
        Use to fetch configuration settings, limits, and parameters for a profile.

    What it cannot do:
        Cannot modify configuration rules or write to the state store.
    """
    _ = request_id
    config = _load_risk_policy(profile_name)
    return config.model_dump()


# --- 2. validate_risk_policy ---
@risk_tool(name="validate_risk_policy", risk_level="low", reads=True)
def validate_risk_policy(
    policy_data: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate policy configuration dictionary against schema.

    When agents should use:
        Use before applying or saving policy configurations
        to verify schema conformance.

    What it cannot do:
        Cannot save or persist policy config.
    """
    _ = request_id
    from app.services.risk.models import RiskConfig

    config = RiskConfig.model_validate(policy_data)
    _validate_risk_policy(config)
    return {"status": "valid"}


# --- 3. build_portfolio_risk_snapshot ---
@risk_tool(name="build_portfolio_risk_snapshot", risk_level="low", reads=True)
def build_portfolio_risk_snapshot(
    portfolio_state: dict[str, Any],
    market_context: dict[str, Any],
    config_profile: str = "default",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Compile a complete portfolio risk snapshot.

    When agents should use:
        Use when compiling a complete read-only summary of the portfolio risk state
        (exposure, VaR, stress metrics, drawdown) for auditing or UI display.

    What it cannot do:
        Cannot execute trades, modify the database, or approve override requests.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    p_state = PortfolioState.model_validate(portfolio_state)

    # 1. Calculate VaR and ES
    try:
        var_snap, _es_snap = calculate_var_es_snapshots(
            portfolio_state=p_state,
            proposed_trade=None,
            market_context=market_context,
            config=config,
            min_samples=2,
        )
        var_val = var_snap.result
    except Exception:  # noqa: BLE001
        var_val = Decimal("0.0")

    # 2. Stress tests
    try:
        registry = build_default_scenario_registry()
        stress_results = registry.evaluate_portfolio(
            portfolio_state=p_state,
            proposed_trade=None,
            market_context=market_context,
            config=config,
        )
        max_stress = max(
            (sr.impact_pct for sr in stress_results), default=Decimal("0.0")
        )
    except Exception:  # noqa: BLE001
        max_stress = Decimal("0.0")

    # 3. Drawdown calculation
    drawdown_pct = Decimal("0.0")
    if p_state.balance > 0:
        drawdown_pct = max(
            (p_state.balance - p_state.equity) / p_state.balance, Decimal("0.0")
        )

    # 4. Total exposure
    total_exposure = sum(
        (abs(pos.quantity * pos.current_price) for pos in p_state.positions),
        Decimal("0.0"),
    )

    snap = PortfolioRiskSnapshot(
        positions=p_state.positions,
        pending_orders=[],
        in_flight_orders=[],
        exposure=total_exposure,
        var_es=var_val,
        stress_loss=max_stress,
        drawdown=drawdown_pct,
    )
    return snap.model_dump()


# --- 4. calculate_position_size ---
@risk_tool(name="calculate_position_size", risk_level="low", reads=True)
def calculate_position_size(
    portfolio_state: dict[str, Any],
    proposed_trade: dict[str, Any],
    market_context: dict[str, Any],
    config_profile: str = "default",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Compute volatility-adjusted lot position sizing options.

    When agents should use:
        Use when computing the recommended trade volume (lot sizing) based on
        account equity, risk percent parameters, volatility (ATR),
        and stop-loss distance.

    What it cannot do:
        Cannot validate overall portfolio exposure limits or approve overrides.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    p_state = PortfolioState.model_validate(portfolio_state)
    trade = ProposedTrade.model_validate(proposed_trade)
    sizing_req_data = market_context.get("sizing_request") or {}
    sizing_request = PositionSizingRequest(
        symbol=trade.symbol,
        method=sizing_req_data.get("method", "fixed_lot"),
        fixed_volume=Decimal(str(sizing_req_data.get("fixed_volume")))
        if sizing_req_data.get("fixed_volume") is not None
        else trade.volume,
        risk_percent=Decimal(str(sizing_req_data.get("risk_percent")))
        if sizing_req_data.get("risk_percent") is not None
        else None,
        stop_loss_pips=Decimal(str(sizing_req_data.get("stop_loss_pips")))
        if sizing_req_data.get("stop_loss_pips") is not None
        else None,
        atr_value=Decimal(str(sizing_req_data.get("atr_value")))
        if sizing_req_data.get("atr_value") is not None
        else None,
        multiplier=Decimal(str(sizing_req_data.get("multiplier")))
        if sizing_req_data.get("multiplier") is not None
        else None,
        risk_amount=Decimal(str(sizing_req_data.get("risk_amount")))
        if sizing_req_data.get("risk_amount") is not None
        else None,
    )
    res = _calculate_position_size(sizing_request, p_state, market_context, config)
    return res.model_dump()


# --- 5. calculate_currency_exposure ---
@risk_tool(name="calculate_currency_exposure", risk_level="low", reads=True)
def calculate_currency_exposure(
    portfolio_state: dict[str, Any],
    proposed_trade: dict[str, Any] | None = None,
    market_context: dict[str, Any] | None = None,
    config_profile: str = "default",
    strategy_id: str | None = None,
    symbol: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate gross and net exposure per currency.

    When agents should use:
        Use when decomposing a portfolio and potential trade to examine exposure
        concentrations per currency.

    What it cannot do:
        Cannot place trades or run limit checks.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    p_state = PortfolioState.model_validate(portfolio_state)
    trade = ProposedTrade.model_validate(proposed_trade) if proposed_trade else None
    ctx = market_context or {}
    res = _calculate_currency_exposure(
        portfolio_state=p_state,
        proposed_trade=trade,
        config=config,
        market_context=ctx,
        strategy_id=strategy_id,
        symbol=symbol,
    )
    return {k: v.model_dump() for k, v in res.items()}


# --- 6. calculate_correlation_matrix ---
@risk_tool(name="calculate_correlation_matrix", risk_level="low", reads=True)
def calculate_correlation_matrix(
    market_data: dict[str, list[Any]],
    lookback: int = 50,
    timeframe: str = "M1",
    method: str = "pearson",
    return_type: str = "close_to_close",
    min_samples: int = 20,
    fallback_correlation: float | None = None,
    exclude_last: bool = True,
    request_id: str | None = None,
) -> dict[str, dict[str, str]]:
    """Compute rolling correlation matrix for multiple symbol price series.

    When agents should use:
        Use to determine historical asset correlations to adjust
        sizing or check cluster limits.

    What it cannot do:
        Cannot size positions or check limits.
    """
    _ = request_id
    fallback_dec = (
        Decimal(str(fallback_correlation)) if fallback_correlation is not None else None
    )
    res = _calculate_correlation_matrix(
        market_data=market_data,
        lookback=lookback,
        timeframe=timeframe,
        method=method,
        return_type=return_type,
        min_samples=min_samples,
        fallback_correlation=fallback_dec,
        exclude_last=exclude_last,
    )
    return {
        k: {sk: str(sv) for sk, sv in sv_dict.items()} for k, sv_dict in res.items()
    }


# --- 7. calculate_portfolio_var ---
@risk_tool(name="calculate_portfolio_var", risk_level="low", reads=True)
def calculate_portfolio_var(
    portfolio_state: dict[str, Any],
    market_context: dict[str, Any],
    config_profile: str = "default",
    proposed_trade: dict[str, Any] | None = None,
    lookback: int = 50,
    confidence: float = 0.95,
    method: str = "parametric",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate portfolio Value-at-Risk (VaR).

    When agents should use:
        Use to calculate maximum expected portfolio loss at a given confidence level.

    What it cannot do:
        Cannot place trades or adjust limits.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    p_state = PortfolioState.model_validate(portfolio_state)
    trade = ProposedTrade.model_validate(proposed_trade) if proposed_trade else None
    res = _calculate_portfolio_var(
        portfolio_state=p_state,
        market_context=market_context,
        config=config,
        proposed_trade=trade,
        lookback=lookback,
        confidence=Decimal(str(confidence)),
        method=method,
    )
    return {"var_value": str(res)}


# --- 8. calculate_expected_shortfall ---
@risk_tool(name="calculate_expected_shortfall", risk_level="low", reads=True)
def calculate_expected_shortfall(
    portfolio_state: dict[str, Any],
    market_context: dict[str, Any],
    config_profile: str = "default",
    proposed_trade: dict[str, Any] | None = None,
    lookback: int = 50,
    confidence: float = 0.95,
    method: str = "parametric",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate portfolio Expected Shortfall (ES).

    When agents should use:
        Use to calculate average expected loss exceeding the VaR threshold.

    What it cannot do:
        Cannot place trades.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    p_state = PortfolioState.model_validate(portfolio_state)
    trade = ProposedTrade.model_validate(proposed_trade) if proposed_trade else None
    res = _calculate_expected_shortfall(
        portfolio_state=p_state,
        market_context=market_context,
        config=config,
        proposed_trade=trade,
        lookback=lookback,
        confidence=Decimal(str(confidence)),
        method=method,
    )
    return {"expected_shortfall_value": str(res)}


# --- 9. run_stress_scenario_analysis ---
@risk_tool(name="run_stress_scenario_analysis", risk_level="low", reads=True)
def run_stress_scenario_analysis(
    portfolio_state: dict[str, Any],
    proposed_trade: dict[str, Any] | None,
    market_context: dict[str, Any],
    config_profile: str = "default",
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Evaluate portfolio shock resilience under registered stress test scenarios.

    When agents should use:
        Use when executing macro shock scenario stress tests (e.g. currency spikes,
        market crashes) on current positions.

    What it cannot do:
        Cannot calculate rolling return correlations or approve overrides.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    p_state = PortfolioState.model_validate(portfolio_state)
    trade = ProposedTrade.model_validate(proposed_trade) if proposed_trade else None

    registry = build_default_scenario_registry()
    results = registry.evaluate_portfolio(p_state, trade, market_context, config)
    return [r.model_dump() for r in results]


# --- 10. check_risk_limits ---
@risk_tool(name="check_risk_limits", risk_level="medium", reads=True)
def check_risk_limits(
    proposed_trade: dict[str, Any],
    portfolio_state: dict[str, Any],
    market_context: dict[str, Any] | None = None,
    config_profile: str = "default",
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Evaluate pre-trade limits sequentially.

    When agents should use:
        Use to test if a trade breaches configured limits without recording a decision.

    What it cannot do:
        Cannot persist a trade decision or execute trades.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    trade = ProposedTrade.model_validate(proposed_trade)
    p_state = PortfolioState.model_validate(portfolio_state)
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=p_state,
        risk_config=config,
        market_context=market_context or {},
    )
    res = _check_risk_limits(req, config)
    return [r.model_dump() for r in res]


# --- 11. check_risk_kill_switch ---
@risk_tool(name="check_risk_kill_switch", risk_level="low", reads=True)
def check_risk_kill_switch(
    scope: str,
    target: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Check active kill switch triggers for the target scope.

    When agents should use:
        Use when querying if a particular scope (global, portfolio, strategy,
        symbol, or currency) is currently blocked due to active kill switches.

    What it cannot do:
        Cannot trigger or reset kill switches (read-only query).
    """
    _ = request_id
    from app.services.risk.kill_switch import get_kill_switch_manager

    manager = get_kill_switch_manager()
    is_blocked = manager.is_blocked(scope, target)
    state = (
        manager.states.get(scope, {}).get("state", "inactive")
        if scope in manager.states
        else "inactive"
    )
    reason = (
        manager.states.get(scope, {}).get("reason", "")
        if scope in manager.states
        else ""
    )
    return {
        "is_blocked": is_blocked,
        "scope": scope,
        "target": target,
        "state": state,
        "reason": reason,
    }


# --- 12. review_trade_risk ---
@risk_tool(name="review_trade_risk", risk_level="high", reads=True, writes=True)
def review_trade_risk(
    proposed_trade: dict[str, Any],
    portfolio_state: dict[str, Any],
    market_context: dict[str, Any],
    config_profile: str = "default",
    request_id: str | None = None,
    workflow_id: str | None = None,
    operator_role: str | None = None,
    approval_token: str | None = None,
) -> dict[str, Any]:
    """Execute pre-trade risk checks for a candidate ProposedTrade.

    When agents should use:
        Use when performing pre-trade validation checks for a proposed order intent.
        Evaluates limits, kill switch, drawdown, news, rollover,
        spread, and correlation.

    What it cannot do:
        Cannot place live trades directly with the broker or
        mutate the broker account state.
    """
    _validate_live_sensitive_tool_context(market_context, config_profile, operator_role)
    config = load_risk_config(config_profile)
    req = RiskAssessmentRequest(
        proposed_action=ProposedTrade.model_validate(proposed_trade),
        portfolio_state=PortfolioState.model_validate(portfolio_state),
        risk_config=config,
        calendar_evidence=market_context.get("calendar_evidence", []),
        market_context=market_context,
    )
    req.request_id = request_id
    req.workflow_id = workflow_id or "wf-tool"

    gov = get_shared_governor()
    decision = gov.review_trade_risk(
        request=req,
        operator_role=operator_role,
        approval_token=approval_token,
    )
    return decision.model_dump()


# --- 13. review_allocation_proposal ---
@risk_tool(
    name="review_allocation_proposal", risk_level="medium", reads=True, writes=True
)
def review_allocation_proposal(
    proposed_allocation: dict[str, Any],
    portfolio_state: dict[str, Any],
    market_context: dict[str, Any] | None = None,
    config_profile: str = "default",
    request_id: str | None = None,
    operator_role: str | None = None,
) -> dict[str, Any]:
    """Evaluate budget allocation proposal changes across multiple strategies.

    When agents should use:
        Use when evaluating capital allocation adjustments across active strategies.

    What it cannot do:
        Cannot place orders or bypass strategy lifecycle skip-gates.
    """
    if market_context:
        _validate_live_sensitive_tool_context(
            market_context, config_profile, operator_role
        )
    config = load_risk_config(config_profile)
    req = RiskAssessmentRequest(
        proposed_action=ProposedAllocation.model_validate(proposed_allocation),
        portfolio_state=PortfolioState.model_validate(portfolio_state),
        risk_config=config,
        market_context=market_context or {},
    )
    req.request_id = request_id
    gov = get_shared_governor()
    decision = gov.review_allocation_proposal(req)
    return decision.model_dump()


# --- 14. review_strategy_admission ---
@risk_tool(
    name="review_strategy_admission", risk_level="medium", reads=True, writes=True
)
def review_strategy_admission(
    strategy_admission_request: dict[str, Any],
    market_context: dict[str, Any] | None = None,
    config_profile: str = "default",
    request_id: str | None = None,
    operator_role: str | None = None,
) -> dict[str, Any]:
    """Review metrics walk-forward and promotion checks for strategy admission.

    When agents should use:
        Use when validating strategy backtest or walk-forward performance metrics
        before admitting it to simulation or shadow phases.

    What it cannot do:
        Cannot size positions or assess individual trade risk.
    """
    if market_context:
        _validate_live_sensitive_tool_context(
            market_context, config_profile, operator_role
        )
    config = load_risk_config(config_profile)
    req = RiskAssessmentRequest(
        proposed_action=StrategyAdmissionRequest.model_validate(
            strategy_admission_request
        ),
        portfolio_state=PortfolioState(
            account_id="acc-admit",
            balance=Decimal("1.0"),
            equity=Decimal("1.0"),
            margin_used=Decimal("0.0"),
            free_margin=Decimal("1.0"),
            floating_pnl=Decimal("0.0"),
            realized_pnl=Decimal("0.0"),
            currency="USD",
            as_of=datetime.now(UTC),
        ),
        risk_config=config,
    )
    req.request_id = request_id
    gov = get_shared_governor()
    decision = gov.review_strategy_admission(req)
    return decision.model_dump()


# --- 15. review_live_readiness ---
@risk_tool(name="review_live_readiness", risk_level="low", reads=True)
def review_live_readiness(
    strategy_id: str,
    proposed_stage: str,
    market_context: dict[str, Any],
    config_profile: str = "default",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Review live readiness parameters for strategy promotion.

    When agents should use:
        Use before promoting strategy to paper, shadow or live execution stages.

    What it cannot do:
        Cannot change strategy stages directly.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    res = _review_live_readiness(strategy_id, proposed_stage, market_context, config)
    return res.model_dump()


# --- 16. run_portfolio_risk_governor ---
@risk_tool(
    name="run_portfolio_risk_governor", risk_level="high", reads=True, writes=True
)
def run_portfolio_risk_governor(
    portfolio_state: dict[str, Any],
    market_context: dict[str, Any],
    config_profile: str = "default",
    request_id: str | None = None,
    operator_role: str | None = None,
) -> dict[str, Any]:
    """Run sequential checkpoints across consolidated portfolio states.

    When agents should use:
        Use when executing consolidated, periodic portfolio checkpoints
        (drawdown, correlation clusters, margin utility checks).

    What it cannot do:
        Cannot alter raw broker executions or place trades.
    """
    _validate_live_sensitive_tool_context(market_context, config_profile, operator_role)
    config = load_risk_config(config_profile)
    req = RiskAssessmentRequest(
        proposed_action=ProposedTrade(
            strategy_id="portfolio-check",
            symbol="EURUSD",
            side="buy",
            volume=Decimal("0.0"),
        ),
        portfolio_state=PortfolioState.model_validate(portfolio_state),
        risk_config=config,
        market_context=market_context,
    )
    req.request_id = request_id
    gov = get_shared_governor()
    decision = gov.run_portfolio_risk_governor(req)
    return decision.model_dump()


# --- 17. create_risk_decision_package ---
@risk_tool(name="create_risk_decision_package", risk_level="low", reads=True)
def create_risk_decision_package(
    decision_id: str,
    request_id: str,
    workflow_id: str,
    status: str,
    rule_key: str,
    config_hash: str,
    reason: str,
    composite_breach_flags: list[str],
    calculated_volume: float,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a canonical RiskDecisionPackage representation.

    When agents should use:
        Use to format standard risk decisions for logging or transmission.

    What it cannot do:
        Cannot store or persist decision package.
    """
    from app.services.risk.models import RiskDecisionStatus

    res = _create_risk_decision_package(
        decision_id=decision_id,
        request_id=request_id,
        workflow_id=workflow_id,
        status=RiskDecisionStatus(status),
        rule_key=rule_key,
        config_hash=config_hash,
        reason=reason,
        composite_breach_flags=composite_breach_flags,
        calculated_volume=Decimal(str(calculated_volume)),
        details=details,
    )
    return res.model_dump()


# --- 18. validate_risk_approval_token ---
@risk_tool(name="validate_risk_approval_token", risk_level="low", reads=True)
def validate_risk_approval_token(
    token: dict[str, Any],
    expected_scope: dict[str, Any],
    config_profile: str = "default",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Check cryptographic token signatures and expirations.

    When agents should use:
        Use when checking the cryptographic validity, expiry, and environment
        scope compatibility of a risk override approval token.

    What it cannot do:
        Cannot generate a new approval token.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    t = RiskApprovalToken.model_validate(token)
    from app.services.risk.audit import validate_risk_approval_token as _validate_token

    is_valid = _validate_token(
        token=t,
        expected_scope=expected_scope,
        active_config_hash=config.contract_hash(),
        active_policy_hash="",
        state_store=get_shared_store(),
    )
    return {"is_valid": is_valid, "token_id": t.token_id}


# --- 19. generate_risk_report ---
@risk_tool(name="generate_risk_report", risk_level="low", reads=True, writes=True)
def generate_risk_report(
    request_id: str | None = None,
    write_to_path: str | None = None,
) -> dict[str, Any]:
    """Compile compiled decision scores, breach statistics, and details from memory.

    When agents should use:
        Use when compiling a comprehensive historical summary report of
        pre-trade decisions, breach flags, and risk metrics.

    What it cannot do:
        Cannot submit order intents or modify active limit settings.
    """
    from app.services.risk.reports import generate_risk_report as _gen_report

    store = get_shared_store()

    try:
        report = _gen_report(
            state_store=store,
            audit_sink=store,
            decision_store=store,
            request_id=request_id,
            write_to_path=write_to_path,
        )
        report_dict = report.model_dump()

        # Add backward-compatible summary statistics
        report_dict["total_decisions_logged"] = len(store._decisions)  # noqa: SLF001
        report_dict["total_audit_events"] = len(store._audit_events)  # noqa: SLF001

        status_counts: dict[str, int] = {}
        breaches_count: dict[str, int] = {}
        for d in store._decisions.values():  # noqa: SLF001
            status_counts[d.status] = status_counts.get(d.status, 0) + 1
            for b in d.composite_breach_flags:
                breaches_count[b] = breaches_count.get(b, 0) + 1

        report_dict["status_distribution"] = status_counts
        report_dict["breaches_summary"] = breaches_count

        if write_to_path:
            report_dict["file_written"] = True
            report_dict["output_path"] = str(write_to_path)

        return report_dict
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error generating risk report in tool: {e}")
        return {
            "status": "error",
            "message": f"Failed to generate risk report: {e}",
            "file_written": False,
        }


# --- Optional regime tool (retained for backward compatibility) ---
@risk_tool(name="assess_risk_regime", risk_level="low", reads=True)
def assess_risk_regime(
    symbol: str,
    market_context: dict[str, Any],
    config_profile: str = "default",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Determine volatility and spread regimes for the target symbol.

    When agents should use:
        Use when assessing the current market regime (volatility, spread,
        trading session, news impact) to adjust strategy behaviors.

    What it cannot do:
        Cannot calculate portfolio-level VaR/ES or modify limit configurations.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    from app.services.risk.models import MarketRiskSnapshot
    from app.utils.normalization import parse_datetime, utc_now

    spreads_list = market_context.get("spreads", {}).get(symbol, [])
    current_spread = (
        Decimal(str(spreads_list[-1])) if spreads_list else Decimal("0.0001")
    )
    volatility = Decimal(str(market_context.get("volatility", "0.001")))
    session = market_context.get("session", "active")

    rollover_time = market_context.get("rollover_time")
    if isinstance(rollover_time, str):
        rollover_time = parse_datetime(rollover_time)

    freshness = market_context.get("freshness")
    if isinstance(freshness, str):
        freshness = parse_datetime(freshness)
    if not freshness:
        freshness = utc_now()

    market_snapshot = MarketRiskSnapshot(
        spread=current_spread,
        volatility=volatility,
        session=session,
        rollover_time=rollover_time,
        news_impact=market_context.get("news_impact"),
        freshness=freshness,
    )
    calendar_evidence = market_context.get("calendar_evidence", [])
    res = _assess_risk_regime(
        market_snapshot=market_snapshot,
        calendar_evidence=calendar_evidence,
        risk_config=config,
        market_context=market_context,
    )
    return res.model_dump()


__all__ = [
    "assess_risk_regime",
    "build_portfolio_risk_snapshot",
    "calculate_correlation_matrix",
    "calculate_currency_exposure",
    "calculate_expected_shortfall",
    "calculate_portfolio_var",
    "calculate_position_size",
    "check_risk_kill_switch",
    "check_risk_limits",
    "create_risk_decision_package",
    "generate_risk_report",
    "get_shared_governor",
    "get_shared_store",
    "load_risk_policy",
    "review_allocation_proposal",
    "review_live_readiness",
    "review_strategy_admission",
    "review_trade_risk",
    "run_portfolio_risk_governor",
    "run_stress_scenario_analysis",
    "validate_risk_approval_token",
    "validate_risk_policy",
]
