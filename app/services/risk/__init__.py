# ruff: noqa: F401
"""Risk service entry point.

This module exposes the official AI tools, deterministic services, public python
contracts, and custom exceptions for the HaruQuantAI risk service.
"""

from __future__ import annotations

from app.services.risk.governor import RiskGovernor, run_portfolio_risk_governor
from app.services.risk.kill_switch import (
    KillSwitchService,
    check_risk_kill_switch,
    classify_drawdown_regime,
)
from app.services.risk.lifecycle import (
    AllocationService,
    CostService,
    IncidentService,
    LifecycleService,
    PortfolioAuditService,
    PortfolioKillSwitch,
    ReportingService,
    normalize_lifecycle_state,
)
from app.services.risk.limits import (
    LimitCheckResult,
    check_daily_loss_limit,
    check_max_drawdown_limit,
    run_risk_governor_checks,
)
from app.services.risk.models import (
    OrderState,
    PortfolioState,
    PositionSizingRequest,
    PositionSizingResult,
    PositionState,
    ProposedAllocation,
    ProposedTrade,
    RegimeAssessment,
    RiskApprovalToken,
    RiskConfig,
    RiskDecisionPackage,
    RiskReport,
    RiskSnapshot,
    ScenarioResult,
)
from app.services.risk.scenarios import (
    StressScenario,
    evaluate_scenarios,
)
from app.services.risk.tools import (
    assess_risk_regime,
    build_portfolio_risk_snapshot,
    calculate_position_size,
    create_risk_decision_package,
    generate_risk_report,
    review_allocation_proposal,
    review_strategy_admission,
    review_trade_risk,
    run_risk_scenario_analysis,
    validate_risk_approval_token,
)

__all__ = [
    # Facades & Deterministic Services
    "AllocationService",
    "CostService",
    "IncidentService",
    "LifecycleService",
    "OrderState",
    "PortfolioAuditService",
    "PortfolioKillSwitch",
    "PortfolioState",
    "PositionSizingRequest",
    "PositionSizingResult",
    "PositionState",
    "ProposedAllocation",
    "ProposedTrade",
    "RegimeAssessment",
    "ReportingService",
    "RiskApprovalToken",
    "RiskAuditRecord",
    # Contracts & Models
    "RiskConfig",
    "RiskDecisionPackage",
    "RiskReport",
    "RiskSnapshot",
    "ScenarioResult",
    "StressScenario",
    "assess_risk_regime",
    # Official AI Tools
    "build_portfolio_risk_snapshot",
    "calculate_position_size",
    "check_daily_loss_limit",
    "check_max_drawdown_limit",
    "check_risk_kill_switch",
    "classify_drawdown_regime",
    "create_risk_decision_package",
    "generate_risk_report",
    "normalize_lifecycle_state",
    "review_allocation_proposal",
    "review_strategy_admission",
    "review_trade_risk",
    # Verification & Limit Functions
    "run_portfolio_risk_governor",
    "run_risk_governor_checks",
    "run_risk_scenario_analysis",
    "validate_risk_approval_token",
]
