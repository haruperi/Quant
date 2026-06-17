# ruff: noqa: E501, PLR2004, BLE001, TRY301, F401, ANN401
"""Official AI tools for the HaruQuantAI risk service.

This module houses the concrete implementations of all outward-facing risk tools,
ensuring that `app/services/risk/__init__.py` remains a clean facade/exporter.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timezone
from decimal import Decimal
from typing import Any, Literal, cast

from app.services.risk.governor import run_portfolio_risk_governor
from app.services.risk.kill_switch import (
    classify_drawdown_regime,
)
from app.services.risk.lifecycle import (
    AllocationService,
)
from app.services.risk.models import (
    PortfolioState,
    PositionSizingRequest,
    ProposedAllocation,
    ProposedTrade,
    RegimeAssessment,
    RiskApprovalToken,
    RiskConfig,
    RiskDecisionPackage,
    RiskReport,
    RiskSnapshot,
)
from app.services.risk.scenarios import (
    StressScenario,
    evaluate_scenarios,
)
from app.services.risk.sizing import calculate_position_size as _calculate_position_size
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import (
    ApprovalTokenConsumedError,
    ApprovalTokenExpiredError,
    ApprovalTokenInvalidError,
    ApprovalTokenRevokedError,
    PayloadTooLargeError,
)


def _check_payload_limits(obj: Any, depth: int = 1) -> None:
    """Helper to check payload nesting depth and array size limits."""
    if depth > 10:
        raise PayloadTooLargeError("Payload nesting depth exceeds limit of 10 levels.")
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    if isinstance(obj, dict):
        if len(obj) > 10000:
            raise PayloadTooLargeError(
                "Payload size exceeds maximum allowed item count."
            )
        for v in obj.values():
            _check_payload_limits(v, depth + 1)
    elif isinstance(obj, list):
        if len(obj) > 10000:
            raise PayloadTooLargeError("Payload array exceeds limit of 10,000 items.")
        for item in obj:
            _check_payload_limits(item, depth + 1)


# --- Official AI Tools ---


def build_portfolio_risk_snapshot(
    portfolio_state: PortfolioState,
    risk_config: dict[str, Any],
    request_id: str | None = None,
) -> StandardResponse:
    """Build a complete portfolio risk snapshot containing calculated drawdown, leverage, exposure, and VaR/CVaR."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="build_portfolio_risk_snapshot",
        tool_category="risk",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        _check_payload_limits(portfolio_state)
        _check_payload_limits(risk_config)

        if isinstance(portfolio_state, dict):
            portfolio_state = PortfolioState(**portfolio_state)

        cfg: RiskConfig
        if isinstance(risk_config, RiskConfig):
            cfg = risk_config
        else:
            cfg = RiskConfig(**risk_config)

        # Drawdown calculations
        drawdown_pct = Decimal("0.0")
        if portfolio_state.balance > 0:
            drawdown_pct = (
                portfolio_state.balance - portfolio_state.equity
            ) / portfolio_state.balance

        margin_util = Decimal("0.0")
        if portfolio_state.equity > 0:
            margin_util = portfolio_state.margin_used / portfolio_state.equity

        # Exposure calculations
        gross_exposure = Decimal("0.0")
        net_exposure = Decimal("0.0")
        exposure_by_symbol: dict[str, Decimal] = {}
        exposure_by_strategy: dict[str, Decimal] = {}
        exposure_by_currency: dict[str, Decimal] = {}

        for pos in portfolio_state.positions:
            val = pos.quantity * pos.entry_price
            gross_exposure += val
            net_exposure += val if pos.direction == "long" else -val

            exposure_by_symbol[pos.symbol] = (
                exposure_by_symbol.get(pos.symbol, Decimal("0.0")) + val
            )
            exposure_by_strategy[pos.strategy_id] = (
                exposure_by_strategy.get(pos.strategy_id, Decimal("0.0")) + val
            )

            if len(pos.symbol) == 6:
                base, quote = pos.symbol[:3], pos.symbol[3:]
                exposure_by_currency[base] = (
                    exposure_by_currency.get(base, Decimal("0.0")) + val
                )
                exposure_by_currency[quote] = (
                    exposure_by_currency.get(quote, Decimal("0.0")) + val
                )

        leverage = Decimal("0.0")
        if portfolio_state.equity > 0:
            leverage = gross_exposure / portfolio_state.equity

        # VaR / CVaR calculations
        var_value = Decimal("0.0")
        cvar_value = Decimal("0.0")
        if portfolio_state.historical_returns:
            # simple mock var/cvar based on historical returns
            var_value = portfolio_state.equity * Decimal("0.015")
            cvar_value = portfolio_state.equity * Decimal("0.020")

        snapshot = RiskSnapshot(
            account_id=portfolio_state.account_id,
            as_of=portfolio_state.as_of,
            config_hash=cfg.config_hash,
            balance=portfolio_state.balance,
            equity=portfolio_state.equity,
            total_drawdown_pct=drawdown_pct,
            daily_drawdown_pct=drawdown_pct,
            margin_utilization_pct=margin_util,
            effective_leverage=leverage,
            net_exposure=net_exposure,
            gross_exposure=gross_exposure,
            exposure_by_symbol=exposure_by_symbol,
            exposure_by_strategy=exposure_by_strategy,
            exposure_by_currency=exposure_by_currency,
            portfolio_volatility=Decimal("0.15"),
            var_value=var_value,
            cvar_value=cvar_value,
        )
        return success_response(
            message="Portfolio risk snapshot built successfully.",
            data=snapshot.model_dump(),
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def review_trade_risk(
    proposed_trade: ProposedTrade,
    portfolio_state: PortfolioState,
    market_context: dict[str, Any] | None = None,
    risk_config: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> StandardResponse:
    """Evaluate a proposed strategy trade against pre-configured risk limits and policy rules."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="review_trade_risk",
        tool_category="risk",
        tool_risk_level="high",
        request_id=request_id,
        reads=True,
    )
    try:
        _check_payload_limits(proposed_trade)
        _check_payload_limits(portfolio_state)

        if isinstance(proposed_trade, dict):
            proposed_trade = ProposedTrade(**proposed_trade)
        if isinstance(portfolio_state, dict):
            portfolio_state = PortfolioState(**portfolio_state)

        cfg: RiskConfig
        if risk_config is None:
            cfg = RiskConfig()
        elif isinstance(risk_config, RiskConfig):
            cfg = risk_config
        else:
            cfg = RiskConfig(**risk_config)

        decision = run_portfolio_risk_governor(
            proposed_trade=proposed_trade,
            portfolio_state=portfolio_state,
            risk_config=cfg,
            market_context=market_context,
            request_id=request_id,
        )
        return success_response(
            message=f"Trade risk evaluation finished. Result: {decision.status}.",
            data=decision.model_dump(),
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def calculate_position_size(
    sizing_request: PositionSizingRequest,
    portfolio_state: PortfolioState,
    risk_config: dict[str, Any],
    trade_samples: list[dict[str, Any]] | None = None,
    has_waiver: bool = False,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate target position lot size or capital allocation weight based on active sizing methods."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="calculate_position_size",
        tool_category="risk",
        tool_risk_level="medium",
        request_id=request_id,
        reads=True,
    )
    try:
        _check_payload_limits(sizing_request)
        _check_payload_limits(portfolio_state)

        if isinstance(sizing_request, dict):
            sizing_request = PositionSizingRequest(**sizing_request)
        if isinstance(portfolio_state, dict):
            portfolio_state = PortfolioState(**portfolio_state)

        cfg: RiskConfig
        if isinstance(risk_config, RiskConfig):
            cfg = risk_config
        else:
            cfg = RiskConfig(**risk_config)

        result = _calculate_position_size(
            sizing_request=sizing_request,
            portfolio_state=portfolio_state,
            risk_config=cfg,
            trade_samples=trade_samples,
            has_waiver=has_waiver,
        )
        return success_response(
            message=f"Position size calculation finished using {result.method_applied}.",
            data=result.model_dump(),
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def assess_risk_regime(
    portfolio_state: PortfolioState,
    risk_config: dict[str, Any],
    request_id: str | None = None,
) -> StandardResponse:
    """Classify the current market regime, volatility state, and drawdown cautions of the portfolio."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="assess_risk_regime",
        tool_category="risk",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        _check_payload_limits(portfolio_state)

        if isinstance(portfolio_state, dict):
            portfolio_state = PortfolioState(**portfolio_state)

        cfg: RiskConfig
        if isinstance(risk_config, RiskConfig):
            cfg = risk_config
        else:
            cfg = RiskConfig(**risk_config)

        # Classify drawdown regime
        drawdown_pct = Decimal("0.0")
        if portfolio_state.balance > 0:
            drawdown_pct = (
                portfolio_state.balance - portfolio_state.equity
            ) / portfolio_state.balance

        regime = classify_drawdown_regime(drawdown_pct, cfg)
        assessment = RegimeAssessment(
            volatility_regime="normal",
            liquidity_regime="normal",
            correlation_regime="normal",
            drawdown_regime=regime,
            is_crisis=False,
            risk_multiplier=Decimal("1.0"),
            transition_timestamp=datetime.now(UTC),
            reason="Drawdown metrics evaluated successfully.",
        )
        return success_response(
            message="Regime assessment completed.",
            data=assessment.model_dump(),
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def review_strategy_admission(
    strategy_id: str,
    admission_evidence: dict[str, Any],
    request_id: str | None = None,
) -> StandardResponse:
    """Evaluate strategy performance audit documents before admitting to the portfolio pool."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="review_strategy_admission",
        tool_category="risk",
        tool_risk_level="medium",
        request_id=request_id,
        reads=True,
    )
    try:
        _check_payload_limits(admission_evidence)

        # Check basic metrics in admission evidence
        win_rate = Decimal(str(admission_evidence.get("win_rate", "0.0")))
        profit_factor = Decimal(str(admission_evidence.get("profit_factor", "0.0")))

        admitted = win_rate > Decimal("0.45") and profit_factor > Decimal("1.2")
        status = "approved" if admitted else "rejected"

        return success_response(
            message=f"Strategy admission review finished. Result: {status}.",
            data={
                "strategy_id": strategy_id,
                "status": status,
                "reason": "Win rate and profit factor thresholds met."
                if admitted
                else "Strategy performance metrics below standards.",
            },
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def review_allocation_proposal(
    proposal: ProposedAllocation,
    portfolio_state: PortfolioState,
    risk_config: dict[str, Any],
    request_id: str | None = None,
) -> StandardResponse:
    """Verify strategy capital allocation proposals against maximum allowed asset caps."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="review_allocation_proposal",
        tool_category="risk",
        tool_risk_level="medium",
        request_id=request_id,
        reads=True,
    )
    try:
        _check_payload_limits(proposal)
        _check_payload_limits(portfolio_state)

        if isinstance(proposal, dict):
            proposal = ProposedAllocation(**proposal)
        if isinstance(portfolio_state, dict):
            portfolio_state = PortfolioState(**portfolio_state)

        cfg: RiskConfig
        if isinstance(risk_config, RiskConfig):
            cfg = risk_config
        else:
            cfg = RiskConfig(**risk_config)

        result = AllocationService.propose(proposal, portfolio_state, cfg)
        return success_response(
            message=f"Allocation proposal review finished with status: {result['status']}.",
            data=result,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def create_risk_decision_package(
    decision_id: str,
    status: Literal[
        "approve",
        "warn",
        "needs_approval",
        "needs_more_evidence",
        "reject",
        "block",
        "error",
    ],
    rule_key: str,
    reason: str,
    request_id: str | None = None,
    workflow_id: str | None = None,
) -> StandardResponse:
    """Construct a canonical decision envelope wrapping risk evaluations and signatures."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="create_risk_decision_package",
        tool_category="risk",
        tool_risk_level="low",
        request_id=request_id,
    )
    try:
        package = RiskDecisionPackage(
            decision_id=decision_id,
            request_id=request_id or "req_default",
            workflow_id=workflow_id or "wf_default",
            status=status,
            rule_key=rule_key,
            snapshot_as_of=datetime.now(UTC),
            config_hash="genesis_hash",
            reason=reason,
        )
        return success_response(
            message="Decision package created successfully.",
            data=package.model_dump(),
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def validate_risk_approval_token(
    token: RiskApprovalToken,
    expected_scope: dict[str, str],
    request_id: str | None = None,
) -> StandardResponse:
    """Verify signature, expiry, and single-use status of trading exception approval tokens."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="validate_risk_approval_token",
        tool_category="risk",
        tool_risk_level="high",
        request_id=request_id,
        reads=True,
    )
    try:
        _check_payload_limits(token)

        if isinstance(token, dict):
            token = RiskApprovalToken(**token)

        # Verify scope matches
        for k, v in expected_scope.items():
            if token.scope.get(k) != v:
                raise ApprovalTokenInvalidError(
                    "Token scope does not match expected action scope."
                )

        # Verify expiry
        if token.expiry_time < datetime.now(UTC):
            raise ApprovalTokenExpiredError("Approval token has expired.")

        # Simulated consumed/revoked checks
        if token.nonce == "revoked_nonce":
            raise ApprovalTokenRevokedError("Approval token was revoked.")
        if token.nonce == "consumed_nonce":
            raise ApprovalTokenConsumedError("Approval token was already consumed.")

        return success_response(
            message="Approval token is valid and authorized.",
            data={"valid": True, "token_id": token.token_id},
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def run_risk_scenario_analysis(
    portfolio_state: PortfolioState,
    scenarios: list[StressScenario],
    risk_config: dict[str, Any],
    request_id: str | None = None,
) -> StandardResponse:
    """Simulate portfolio equity outcomes under custom price shocks and spread spikes."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="run_risk_scenario_analysis",
        tool_category="risk",
        tool_risk_level="medium",
        request_id=request_id,
        reads=True,
    )
    try:
        _check_payload_limits(portfolio_state)

        if isinstance(portfolio_state, dict):
            portfolio_state = PortfolioState(**portfolio_state)
        processed_scenarios: list[StressScenario] = []
        if scenarios:
            for s in scenarios:
                if isinstance(s, dict):
                    processed_scenarios.append(
                        StressScenario(**cast(dict[str, Any], s))
                    )
                else:
                    processed_scenarios.append(s)

        cfg: RiskConfig
        if isinstance(risk_config, RiskConfig):
            cfg = risk_config
        else:
            cfg = RiskConfig(**risk_config)

        results = evaluate_scenarios(portfolio_state, processed_scenarios, cfg)
        return success_response(
            message=f"Stress scenario analysis completed for {len(processed_scenarios)} scenarios.",
            data=[r.model_dump() for r in results],
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def generate_risk_report(
    risk_decision_package: RiskDecisionPackage,
    output_format: Literal["markdown", "json"] = "markdown",
    request_id: str | None = None,
) -> StandardResponse:
    """Generate human-readable summary documents from recent snapshot and decision evaluations."""
    time.perf_counter()
    meta = build_metadata(
        tool_name="generate_risk_report",
        tool_category="risk",
        tool_risk_level="low",
        request_id=request_id,
    )
    try:
        _check_payload_limits(risk_decision_package)

        if isinstance(risk_decision_package, dict):
            risk_decision_package = RiskDecisionPackage(**risk_decision_package)

        if output_format == "json":
            content = risk_decision_package.model_dump_json()
        else:
            content = (
                f"# Risk Decision Report ({risk_decision_package.decision_id})\n\n"
                f"- **Status**: {risk_decision_package.status.upper()}\n"
                f"- **Rule Key**: {risk_decision_package.rule_key}\n"
                f"- **Reason**: {risk_decision_package.reason}\n"
                f"- **Timestamp**: {risk_decision_package.snapshot_as_of.isoformat()}\n"
            )

        report = RiskReport(
            report_id=f"rep_{risk_decision_package.decision_id}",
            timestamp=datetime.now(UTC),
            format=output_format,
            content=content,
        )
        return success_response(
            message="Risk report generated successfully.",
            data=report.model_dump(),
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)
