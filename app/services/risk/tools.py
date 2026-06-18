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
from app.services.risk.governor import RiskGovernor
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
from app.services.risk.regime import assess_risk_regime
from app.services.risk.sizing import calculate_position_size
from app.services.risk.storage import InMemoryRiskStateStore
from app.services.risk.stress import build_default_scenario_registry
from app.services.risk.var_es import calculate_var_es_snapshots
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
    "build_portfolio_risk_snapshot_tool": lambda _: (
        "Successfully compiled portfolio risk snapshot."
    ),
    "review_trade_risk_tool": lambda d: (
        f"Trade risk review completed with status: {d.get('status')}."
    ),
    "calculate_position_size_tool": lambda d: (
        f"Position size calculation complete: {d.get('calculated_volume')} lots."
    ),
    "assess_risk_regime_tool": lambda d: (
        f"Market regime assessment complete: {d.get('regime')}."
    ),
    "review_strategy_admission_tool": lambda d: (
        f"Strategy admission review completed with status: {d.get('status')}."
    ),
    "review_allocation_proposal_tool": lambda d: (
        f"Allocation proposal review completed with status: {d.get('status')}."
    ),
    "run_portfolio_risk_governor_tool": lambda d: (
        f"Portfolio risk governor run completed with status: {d.get('status')}."
    ),
    "validate_risk_approval_token_tool": lambda _: "Token validation check completed.",
    "check_risk_kill_switch_tool": lambda _: "Kill switch status check completed.",
    "run_risk_scenario_analysis_tool": lambda d: (
        f"Scenario analysis complete. Executed {len(d)} scenarios."
    ),
    "generate_risk_report_tool": lambda _: "Risk report generated successfully.",
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


@risk_tool(name="build_portfolio_risk_snapshot_tool", risk_level="low", reads=True)
def build_portfolio_risk_snapshot_tool(
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

    Args:
        portfolio_state: Account balance, equity, and position lists.
        market_context: Active market quotes and returns databases.
        config_profile: Configuration profile name.
        request_id: Track ID.

    Returns:
        dict: Serialized PortfolioRiskSnapshot metadata dict.
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


@risk_tool(name="review_trade_risk_tool", risk_level="high", reads=True, writes=True)
def review_trade_risk_tool(
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

    Args:
        proposed_trade: Proposed trade dictionary.
        portfolio_state: Current portfolio state.
        market_context: Injected runtime flags and evidence.
        config_profile: Active policy configuration profile name.
        request_id: Track ID.
        workflow_id: Workflow execution ID.
        operator_role: Role of the executing operator.
        approval_token: Optional override approval token.

    Returns:
        dict: Serialized decision outcome.
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


@risk_tool(name="calculate_position_size_tool", risk_level="low", reads=True)
def calculate_position_size_tool(
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

    Args:
        portfolio_state: Account balance and equity state.
        proposed_trade: Proposed trade request.
        market_context: Market quotes and sizing options dictionary.
        config_profile: Config profile name.
        request_id: Track ID.

    Returns:
        dict: Sizing options.
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
    res = calculate_position_size(sizing_request, p_state, market_context, config)
    return res.model_dump()


@risk_tool(name="assess_risk_regime_tool", risk_level="low", reads=True)
def assess_risk_regime_tool(
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

    Args:
        symbol: Target trading symbol.
        market_context: Dict containing spreads, volatility, and session flags.
        config_profile: Active policy configuration profile name.
        request_id: Track ID.

    Returns:
        dict: Calculated regime indicators.
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
    res = assess_risk_regime(
        market_snapshot=market_snapshot,
        calendar_evidence=calendar_evidence,
        risk_config=config,
        market_context=market_context,
    )
    return res.model_dump()


@risk_tool(
    name="review_strategy_admission_tool", risk_level="medium", reads=True, writes=True
)
def review_strategy_admission_tool(
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

    Args:
        strategy_admission_request: Candidate strategy performance metrics.
        market_context: Injected runtime flags for live-sensitive validation.
        config_profile: Active policy configuration profile name.
        request_id: Track ID.
        operator_role: Role of the executing operator.

    Returns:
        dict: Decision status and feedback.
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


@risk_tool(
    name="review_allocation_proposal_tool", risk_level="medium", reads=True, writes=True
)
def review_allocation_proposal_tool(
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

    Args:
        proposed_allocation: Strategy allocation request mapping.
        portfolio_state: Consolidated account balance state.
        market_context: Injected runtime flags for live-sensitive validation.
        config_profile: Active policy configuration profile name.
        request_id: Track ID.
        operator_role: Role of the executing operator.

    Returns:
        dict: Sizing budget decision outcome.
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
    )
    req.request_id = request_id
    gov = get_shared_governor()
    decision = gov.review_allocation_proposal(req)
    return decision.model_dump()


@risk_tool(
    name="run_portfolio_risk_governor_tool", risk_level="high", reads=True, writes=True
)
def run_portfolio_risk_governor_tool(
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

    Args:
        portfolio_state: Current consolidated account details.
        market_context: Active quotes and returns history.
        config_profile: Configuration profile name.
        request_id: Track ID.
        operator_role: Role of the executing operator.

    Returns:
        dict: Checked consolidated outcome.
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


@risk_tool(name="validate_risk_approval_token_tool", risk_level="low", reads=True)
def validate_risk_approval_token_tool(
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

    Args:
        token: Cryptographically signed token dict.
        expected_scope: Expected scope constraints.
        config_profile: Configuration profile name.
        request_id: Track ID.

    Returns:
        dict: Cryptographic check result.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    t = RiskApprovalToken.model_validate(token)
    from app.services.risk.audit import validate_risk_approval_token

    is_valid = validate_risk_approval_token(
        token=t,
        expected_scope=expected_scope,
        active_config_hash=config.contract_hash(),
        active_policy_hash="",
        state_store=get_shared_store(),
    )
    return {"is_valid": is_valid, "token_id": t.token_id}


@risk_tool(name="check_risk_kill_switch_tool", risk_level="low", reads=True)
def check_risk_kill_switch_tool(
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

    Args:
        scope: Scope to check (e.g. 'global', 'strategy').
        target: Target identifier (e.g. '*' or strategy_id).
        request_id: Track ID.

    Returns:
        dict: Halted states.
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


@risk_tool(name="run_risk_scenario_analysis_tool", risk_level="low", reads=True)
def run_risk_scenario_analysis_tool(
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

    Args:
        portfolio_state: Account balance details.
        proposed_trade: Candidate proposed trade dictionary.
        market_context: Quotes and pricing context.
        config_profile: Configuration profile name.
        request_id: Track ID.

    Returns:
        list: Shock scenario metrics.
    """
    _ = request_id
    config = load_risk_config(config_profile)
    p_state = PortfolioState.model_validate(portfolio_state)
    trade = ProposedTrade.model_validate(proposed_trade) if proposed_trade else None

    registry = build_default_scenario_registry()
    results = registry.evaluate_portfolio(p_state, trade, market_context, config)
    return [r.model_dump() for r in results]


@risk_tool(name="generate_risk_report_tool", risk_level="low", reads=True, writes=True)
def generate_risk_report_tool(
    request_id: str | None = None,
    write_to_path: str | None = None,
) -> dict[str, Any]:
    """Compile compiled decision scores, breach statistics, and details from memory.

    When agents should use:
        Use when compiling a comprehensive historical summary report of
        pre-trade decisions, breach flags, and risk metrics.

    What it cannot do:
        Cannot submit order intents or modify active limit settings.

    Args:
        request_id: Track ID.
        write_to_path: Optional path to write JSON report to.

    Returns:
        dict: Generated report fields.
    """
    from app.services.risk.reports import generate_risk_report

    store = get_shared_store()

    try:
        report = generate_risk_report(
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
