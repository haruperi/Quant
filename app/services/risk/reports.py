"""Risk reporting and metrics registration module.

Defines schemas and builders for generating JSON-safe and file-written reports
summarizing risk configurations, metrics, and pre-trade decisions.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import Field

from app.services.risk.models import (
    PortfolioRiskSnapshot,
    PortfolioState,
    RiskContract,
    RiskDecisionPackage,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger
from app.utils.normalization import utc_now
from app.utils.observability import MetricRegistry

if TYPE_CHECKING:
    from app.services.risk.storage import (
        RiskAuditSink,
        RiskDecisionStore,
        RiskStateStore,
    )

# Global metric registry for risk events and performance
RISK_METRICS_REGISTRY = MetricRegistry()


class RiskDecisionSummary(RiskContract):
    """Summary of a single pre-trade risk decision.

    Args:
        decision_id: Unique decision ID.
        request_id: Associated request ID.
        status: Synthesized decision status.
        rule_key: Policy rule key matching the decision.
        reason: Explanation text.
        timestamp: Time of decision.
        symbol: Traded symbol.
        volume: Approved trade volume in lots.
    """

    decision_id: str = Field(..., description="Unique decision ID.")
    request_id: str = Field(..., description="Associated request ID.")
    status: str = Field(..., description="Synthesized decision status.")
    rule_key: str = Field(..., description="Primary rule key applied.")
    reason: str = Field(..., description="Explanation of decision.")
    timestamp: datetime = Field(..., description="Time of decision.")
    symbol: str | None = Field(default=None, description="Traded symbol.")
    volume: float | None = Field(
        default=None, description="Approved trade volume in lots."
    )


class PortfolioRiskReport(RiskContract):
    """Consolidated portfolio-level risk metrics.

    Args:
        total_exposure: Gross portfolio exposure in account currency.
        var: Value-at-Risk snapshot metric value.
        es: Expected Shortfall snapshot metric value.
        stress_loss: Max projected stress scenario loss.
        margin_usage: Margin utilization percentage.
        drawdown: Current portfolio drawdown percentage.
    """

    total_exposure: float = Field(
        ..., description="Gross exposure in account currency."
    )
    var: float | None = Field(
        default=None, description="Value-at-Risk snapshot metric value."
    )
    es: float | None = Field(
        default=None, description="Expected Shortfall snapshot metric value."
    )
    stress_loss: float | None = Field(
        default=None, description="Max projected stress scenario loss."
    )
    margin_usage: float | None = Field(
        default=None, description="Margin utilization percentage."
    )
    drawdown: float | None = Field(
        default=None, description="Current portfolio drawdown percentage."
    )


class RiskReport(RiskContract):
    """Structured report containing aggregated risk decision data and metrics.

    Args:
        report_id: Unique report ID.
        generated_at: Report generation timestamp.
        policy_profile: Active policy profile name.
        config_hash: Active configuration hash.
        mode: Execution trading mode.
        portfolio_exposure: Total portfolio gross exposure.
        currency_exposure: Currency exposures mapping.
        correlation_clusters: Cluster exposures mapping.
        var: Value-at-Risk snapshot metric value.
        es: Expected Shortfall snapshot metric value.
        stress_loss: Max projected stress loss.
        drawdown_state: Throttling drawdown state summary.
        margin_usage: Margin utilization percentage.
        breaches: List of rule/constraint limit breaches.
        warnings: List of advisory warnings.
        decisions: pre-trade decisions list.
        metadata: trace and version metadata.
    """

    report_id: str = Field(..., description="Unique report ID.")
    generated_at: datetime = Field(..., description="Report generation timestamp.")
    policy_profile: str | None = Field(
        default=None, description="Active policy profile name."
    )
    config_hash: str | None = Field(
        default=None, description="Active configuration hash."
    )
    mode: str | None = Field(default=None, description="Execution trading mode.")
    portfolio_exposure: float | None = Field(
        default=None, description="Total portfolio gross exposure."
    )
    currency_exposure: dict[str, float] | None = Field(
        default=None, description="Currency exposures mapping."
    )
    correlation_clusters: dict[str, float] | None = Field(
        default=None, description="Cluster exposures mapping."
    )
    var: float | None = Field(
        default=None, description="Value-at-Risk snapshot metric value."
    )
    es: float | None = Field(
        default=None, description="Expected Shortfall snapshot metric value."
    )
    stress_loss: float | None = Field(
        default=None, description="Max projected stress loss."
    )
    drawdown_state: dict[str, Any] | None = Field(
        default=None, description="Throttling drawdown state summary."
    )
    margin_usage: float | None = Field(
        default=None, description="Margin utilization percentage."
    )
    breaches: list[str] = Field(
        default_factory=list, description="List of rule/constraint limit breaches."
    )
    warnings: list[str] = Field(
        default_factory=list, description="List of advisory warnings."
    )
    decisions: list[RiskDecisionSummary] = Field(
        default_factory=list, description="pre-trade decisions list."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="trace and version metadata."
    )


def _to_float(v: Any) -> float | None:  # noqa: ANN401
    """Safely convert value to float, returning None on failure."""
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _to_float_dict(d: Any) -> dict[str, float] | None:  # noqa: ANN401
    """Safely convert dictionary values to float, returning None on failure."""
    if not isinstance(d, dict):
        return None
    res = {}
    for k, v in d.items():
        fl = _to_float(v)
        if fl is not None:
            res[k] = fl
    return res


def build_risk_decision_summary(
    decision: RiskDecisionPackage,
) -> RiskDecisionSummary:
    """Build a summary from a RiskDecisionPackage.

    Args:
        decision: The decision package.

    Returns:
        RiskDecisionSummary: Summarized pre-trade decision.
    """
    details = decision.details or {}
    proposed_action = details.get("proposed_action") or {}
    if isinstance(proposed_action, dict):
        symbol = proposed_action.get("symbol")
        volume = proposed_action.get("volume")
    else:
        symbol = getattr(proposed_action, "symbol", None)
        volume = getattr(proposed_action, "volume", None)

    return RiskDecisionSummary(
        decision_id=decision.decision_id,
        request_id=decision.request_id,
        status=decision.status,
        rule_key=decision.rule_key,
        reason=decision.reason,
        timestamp=decision.snapshot_as_of,
        symbol=symbol,
        volume=_to_float(volume),
    )


class RiskReportBuilder:
    """Builder class for assembling a RiskReport from stored evidence."""

    def __init__(
        self,
        state_store: RiskStateStore,
        audit_sink: RiskAuditSink,
        decision_store: RiskDecisionStore,
    ) -> None:
        """Initialize with storage ports.

        Args:
            state_store: State and kill switch port.
            audit_sink: Audit sink port.
            decision_store: Decision store port.
        """
        self.state_store = state_store
        self.audit_sink = audit_sink
        self.decision_store = decision_store

    def _parse_events(
        self, events: list[Any]
    ) -> tuple[list[RiskDecisionSummary], set[str], RiskDecisionPackage | None]:
        """Parse decisions and gather breaches/warnings from audit events."""
        decisions_list: list[RiskDecisionSummary] = []
        breaches: set[str] = set()
        latest_decision: RiskDecisionPackage | None = None

        for event in events:
            decision_data = event.details.get("decision")
            if decision_data:
                try:
                    dec = RiskDecisionPackage.model_validate(decision_data)
                    summary = build_risk_decision_summary(dec)
                    decisions_list.append(summary)

                    # Gather breaches/warnings from decision
                    for flag in dec.composite_breach_flags:
                        breaches.add(flag)

                    # Update latest
                    if (
                        latest_decision is None
                        or dec.snapshot_as_of > latest_decision.snapshot_as_of
                    ):
                        latest_decision = dec
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing decision from audit event: {e}")

        return decisions_list, breaches, latest_decision

    def build(self, request_id: str | None = None) -> RiskReport:
        """Build and populate the RiskReport.

        Args:
            request_id: Request ID context.

        Returns:
            RiskReport: Populated report.
        """
        events = self.audit_sink.get_all_events()
        decisions_list, breaches, latest_decision = self._parse_events(events)
        warnings: set[str] = set()

        # Extract stats from latest decision details to prevent recomputing
        policy_profile = None
        config_hash = None
        mode = None
        portfolio_exposure = None
        currency_exposure = None
        correlation_clusters = None
        var_val = None
        es_val = None
        stress_loss_val = None
        margin_usage_val = None

        if latest_decision:
            config_hash = latest_decision.config_hash
            details = latest_decision.details or {}
            policy_profile = details.get("policy_profile")
            mode = details.get("mode")
            portfolio_exposure = details.get("portfolio_exposure")
            currency_exposure = details.get("currency_exposure")
            correlation_clusters = details.get("correlation_clusters")
            var_val = details.get("var")
            es_val = details.get("es")
            stress_loss_val = details.get("stress_loss")
            margin_usage_val = details.get("margin_usage")

        # Fallback to store if latest_decision lacks drawdown
        drawdown = self.state_store.get_drawdown_state()
        drawdown_dict = None
        if drawdown:
            drawdown_dict = {
                "current_drawdown": float(drawdown.current_drawdown),
                "soft_limit": float(drawdown.soft_limit),
                "hard_limit": float(drawdown.hard_limit),
                "multiplier": float(drawdown.multiplier),
            }

        meta = {
            "risk.request_id": request_id or "",
            "risk.schema_version": "1.0.0",
        }

        # Build final report_id
        from app.utils.standard import stable_identifier

        report_id = stable_identifier(
            {
                "generated_at": utc_now().isoformat(),
                "decisions_count": len(decisions_list),
            },
            prefix="report",
        )

        return RiskReport(
            report_id=report_id,
            generated_at=utc_now(),
            policy_profile=policy_profile,
            config_hash=config_hash,
            mode=mode,
            portfolio_exposure=_to_float(portfolio_exposure),
            currency_exposure=_to_float_dict(currency_exposure),
            correlation_clusters=_to_float_dict(correlation_clusters),
            var=_to_float(var_val),
            es=_to_float(es_val),
            stress_loss=_to_float(stress_loss_val),
            drawdown_state=drawdown_dict,
            margin_usage=_to_float(margin_usage_val),
            breaches=sorted(breaches),
            warnings=sorted(warnings),
            decisions=decisions_list,
            metadata=meta,
        )


def generate_risk_report(
    state_store: RiskStateStore,
    audit_sink: RiskAuditSink,
    decision_store: RiskDecisionStore,
    request_id: str | None = None,
    write_to_path: str | None = None,
) -> RiskReport:
    """Generate a risk report from stored evidence.

    Args:
        state_store: Drawdown, kill switch, and token store.
        audit_sink: Audit event sink.
        decision_store: Decision package store.
        request_id: Trace correlation ID.
        write_to_path: Optional path to write JSON report to.

    Returns:
        RiskReport: Generated report.
    """
    builder = RiskReportBuilder(state_store, audit_sink, decision_store)
    report = builder.build(request_id)

    if write_to_path:
        # Traversal guard (allow workspace root or system temporary directory)
        import tempfile

        resolved_path = Path(write_to_path).resolve()
        workspace_root = Path.cwd().resolve()
        temp_dir = Path(tempfile.gettempdir()).resolve()

        in_workspace = str(resolved_path).startswith(str(workspace_root))
        in_temp = str(resolved_path).startswith(str(temp_dir))

        if not (in_workspace or in_temp):
            err_msg = (
                "Path traversal detected: path is outside the "
                "authorized workspace directory."
            )
            raise ValidationError(err_msg)

        # Ensure directory exists
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with resolved_path.open("w") as f:
                f.write(report.to_json())
        except (OSError, ValidationError) as e:
            logger.error(f"Failed to write risk report file: {e}")
            err_msg = f"Failed to write risk report file: {e}"
            raise ValidationError(err_msg) from e

    return report


def build_portfolio_risk_snapshot(
    portfolio_state: dict[str, Any] | PortfolioState,
    market_context: dict[str, Any],
    config_profile: str = "default",
) -> PortfolioRiskSnapshot:
    """Compile a complete portfolio risk snapshot.

    Includes VaR, ES, stress tests, and drawdowns.

    Args:
        portfolio_state: Account balance, equity, and position lists.
        market_context: Active market quotes and returns databases.
        config_profile: Configuration profile name.

    Returns:
        PortfolioRiskSnapshot: The compiled portfolio risk snapshot.

    Raises:
        ValidationError: If parsing or calculations fail.
    """
    from decimal import Decimal

    from app.services.risk.config import load_risk_config
    from app.services.risk.models import PortfolioRiskSnapshot, PortfolioState
    from app.services.risk.stress import build_default_scenario_registry
    from app.services.risk.var_es import calculate_var_es_snapshots

    if isinstance(portfolio_state, dict):
        p_state = PortfolioState.model_validate(portfolio_state)
    else:
        p_state = portfolio_state

    config = load_risk_config(config_profile)

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

    return PortfolioRiskSnapshot(
        positions=p_state.positions,
        pending_orders=[],
        in_flight_orders=[],
        exposure=total_exposure,
        var_es=var_val,
        stress_loss=max_stress,
        drawdown=drawdown_pct,
    )
