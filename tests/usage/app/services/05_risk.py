# ruff: noqa: E501, E402
"""Usage example script for app/services/risk.

Demonstrates typical workflows using the official risk contracts, profiles, and policy engine.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[4])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from agentic.tools.risk import build_portfolio_risk_snapshot
from app.services.risk import (
    STAGE_SEQUENCE,
    AccountRiskSnapshot,
    ExpectedShortfallMethod,
    KillSwitchStateEnum,
    MarketRiskSnapshot,
    PolicyRule,
    PolicyScope,
    PortfolioState,
    PositionSizingRequest,
    PositionState,
    ProposedAllocation,
    ProposedTrade,
    ReturnType,
    RiskAction,
    RiskApprovalToken,
    RiskAssessmentRequest,
    RiskConfig,
    RiskDecisionPackage,
    RiskDecisionStatus,
    RiskMode,
    RiskReasonCode,
    SizingMethod,
    VaRMethod,
    build_default_scenario_registry,
    calculate_cluster_exposures,
    calculate_correlation_snapshot,
    calculate_daily_drawdown,
    calculate_position_size,
    calculate_returns,
    calculate_total_drawdown,
    calculate_var_es_snapshots,
    correlation_adjusted_risk_parity_allocation,
    detect_correlation_spikes,
    determine_drawdown_throttling,
    equal_risk_allocation,
    evaluate_execution_feasibility,
    evaluate_lifecycle_promotion,
    evaluate_live_readiness,
    evaluate_margin_governance,
    evaluate_proposed_trade_correlation,
    exit_liquidity_stress_check,
    get_kill_switch_manager,
    run_limit_checks,
    validate_custom_scenario,
    verify_allocation_limits,
    verify_drawdown_limits,
    verify_execution_limits,
    verify_margin_limits,
    volatility_parity_allocation,
)
from app.services.risk.config import load_risk_config
from app.services.risk.policy import resolve_policy, validate_override_token
from app.services.risk.stress import PriceShockScenario
from app.utils.errors import ValidationError as AppValidationError
from pydantic import ValidationError


def example_01_contracts_and_models() -> None:
    """Demonstrate creation, validation, and serialization of core risk contracts (Sprint 5.1)."""
    print("\n" + "=" * 100)
    print("--- Example 1: Contracts and Models (Sprint 5.1) ---")
    print("=" * 100)

    # 1. Enums
    print(f"Risk Decision Statuses: {list(RiskDecisionStatus)}")
    print(f"Risk Modes: {list(RiskMode)}")
    print(f"Risk Actions: {list(RiskAction)}")
    print(f"Risk Reason Codes: {list(RiskReasonCode)}")

    # 2. RiskConfig instantiation and JSON serialization
    config = RiskConfig(
        profile_name="test_profile",
        allow_live_execution=False,
        max_daily_loss_pct=Decimal("0.05"),
        max_effective_leverage=Decimal("30.0"),
    )
    print(f"\nSerialized RiskConfig:\n{config.to_json()[:120]}...")

    # 3. ProposedTrade validation
    trade = ProposedTrade(
        strategy_id="trend-following-v1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.10"),
    )
    print(
        f"\nProposedTrade instantiated successfully: {trade.symbol} {trade.side} {trade.volume}"
    )
    trade_json = trade.to_json()
    print(f"Serialized ProposedTrade:\n{trade_json[:120]}...")

    deserialized_trade = ProposedTrade.model_validate_json(trade_json)
    print(f"Deserialized successfully. Volume: {deserialized_trade.volume}")

    # 4. PortfolioState snapshot
    position = PositionState(
        position_id="pos-001",
        symbol="EURUSD",
        direction="long",
        quantity=Decimal("0.10"),
        entry_price=Decimal("1.0850"),
        current_price=Decimal("1.0870"),
        floating_pnl=Decimal("20.00"),
        margin_required=Decimal("100.00"),
        strategy_id="trend-following-v1",
        open_time=datetime.now(UTC),
    )
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("10000.00"),
        equity=Decimal("10020.00"),
        margin_used=Decimal("100.00"),
        free_margin=Decimal("9920.00"),
        floating_pnl=Decimal("20.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[position],
    )
    print(
        f"\nPortfolioState instantiated successfully: Balance={portfolio.balance}, Positions={len(portfolio.positions)}"
    )
    print(f"PortfolioState JSON sample: {portfolio.to_json()[:120]}...")

    # 5. Snapshots and Packages
    account_snap = AccountRiskSnapshot(
        equity=portfolio.equity,
        balance=portfolio.balance,
        free_margin=portfolio.free_margin,
        margin_used=portfolio.margin_used,
        leverage=Decimal("30.0"),
        base_currency="USD",
        timestamp=datetime.now(UTC),
    )
    market_snap = MarketRiskSnapshot(
        spread=Decimal("0.0001"),
        volatility=Decimal("0.0050"),
        session="NY",
        freshness=datetime.now(UTC),
    )
    decision = RiskDecisionPackage(
        decision_id="dec-001",
        request_id="req-001",
        workflow_id="wf-001",
        status=RiskDecisionStatus.APPROVE,
        rule_key="rule-001",
        snapshot_as_of=datetime.now(UTC),
        config_hash="config-hash-001",
        reason="Limits cleared",
        composite_breach_flags=[],
        calculated_volume=Decimal("0.10"),
    )
    print("\nSnapshots created successfully:")
    print(f"  Account snapshot currency: {account_snap.base_currency}")
    print(f"  Market snapshot freshness: {market_snap.freshness}")
    print(f"  Decision Status: {decision.status}")
    print(f"  Decision Package JSON:\n{decision.to_json()[:120]}...")


def example_02_configs_and_policies() -> None:
    """Demonstrate configuration loading, ceiling constraints, and policy resolution (Sprint 5.2)."""
    print("\n" + "=" * 100)
    print("--- Example 2: Config Profiles & Policy Resolution (Sprint 5.2) ---")
    print("=" * 100)

    default_config = load_risk_config("default")
    print(
        f"Loaded 'default' profile. Daily loss limit: {default_config.max_daily_loss_pct}"
    )
    print(f"Default config hash: {default_config.contract_hash()}")

    prop_firm_config = load_risk_config("prop_firm_default")
    print(
        f"Loaded 'prop_firm_default' profile. Daily loss limit: {prop_firm_config.max_daily_loss_pct}"
    )

    live_config = load_risk_config("live_conservative")
    print(
        f"Loaded 'live_conservative' profile. Allow live: {live_config.allow_live_execution}"
    )

    # 2. Ceiling check
    print("\nCeiling Validation Demonstration:")
    try:
        # Re-verify that loading an unsafe value manually throws ValidationError or breaches ceiling
        RiskConfig(
            profile_name="unsafe",
            max_daily_loss_pct=Decimal("0.25"),  # Hard ceiling is 0.20
        )
        context = {"environment": "local", "symbol": "EURUSD"}
        rules = [
            PolicyRule(
                rule_id="unsafe_rule",
                scope=PolicyScope(symbol="EURUSD"),
                overrides={"max_daily_loss_pct": 0.25},
            )
        ]
        result = resolve_policy(default_config, rules, context)
        print(
            f"Unsafe policy resolution result status: {result.status} (expected REJECT)"
        )
        print(f"Unsafe policy resolution breaches: {result.breaches}")
    except ValidationError as e:
        print(f"Validation caught unsafe config: {e}")

    # 3. Policy-as-Code & Precedence
    print("\nPolicy-as-Code Resolution & Precedence:")
    now = datetime.now(UTC)
    rules = [
        PolicyRule(
            rule_id="rule-global-account",
            scope=PolicyScope(account_id="acc-001"),
            overrides={"max_daily_loss_pct": 0.04},
        ),
        PolicyRule(
            rule_id="rule-strategy-override",
            scope=PolicyScope(strategy_id="mean-reversion-v1"),
            overrides={"max_daily_loss_pct": 0.06},
        ),
        PolicyRule(
            rule_id="rule-symbol-specific",
            scope=PolicyScope(symbol="EURUSD"),
            overrides={"max_daily_loss_pct": 0.08, "max_effective_leverage": 25.0},
        ),
    ]

    context = {
        "account_id": "acc-001",
        "strategy_id": "mean-reversion-v1",
        "symbol": "EURUSD",
        "environment": "local",
    }
    enforcement = resolve_policy(default_config, rules, context)
    print(f"Resolved Status: {enforcement.status}")
    print(f"Policy Hash: {enforcement.policy_hash}")
    print(
        f"Resolved Daily Loss Limit: {enforcement.resolved_config.max_daily_loss_pct} (expected 0.08)"
    )
    print(
        f"Resolved Effective Leverage: {enforcement.resolved_config.max_effective_leverage} (expected 25.0)"
    )

    # 4. Override Token Verification
    print("\nOverride Token Verification:")
    token = RiskApprovalToken(
        token_id="tok-999",
        request_id="req-999",
        workflow_id="wf-999",
        approved_action="override_limits",
        approver="risk_manager",
        expiry_time=now + timedelta(hours=1),
        config_hash=default_config.contract_hash(),
        decision_hash="dec-999",
        scope={"symbol": "EURUSD"},
        nonce="nonce-999",
        signature="sig-999",
    )

    is_valid = validate_override_token(
        token=token,
        expected_scope={"symbol": "EURUSD"},
        active_config_hash=default_config.contract_hash(),
    )
    print(f"Approval Token validation check: {is_valid} (expected True)")

    # 5. Live Mode Safeguard
    print("\nLive Sensitive Mode Gate Safeguard:")
    live_context = {
        "environment": "production",
        "mode": RiskMode.FULL_LIVE,
    }
    live_enforcement = resolve_policy(default_config, [], live_context)
    print(f"Production resolve status: {live_enforcement.status} (expected BLOCK)")
    print(f"Production resolve reason: {live_enforcement.reason}")

    live_enforcement_ok = resolve_policy(live_config, [], live_context)
    print(
        f"Production resolve with live config status: {live_enforcement_ok.status} (expected APPROVE)"
    )


def example_03_market_regime_gate() -> None:
    """Demonstrate market regime classification and gates (Sprint 5.3)."""
    print("\n" + "=" * 100)
    print("--- Example 3: Market Regime Gate (Sprint 5.3) ---")
    print("=" * 100)

    from app.services.risk import (
        assess_risk_regime,
    )

    base_config = load_risk_config("default")
    live_config = load_risk_config("live_conservative")

    # 1. Normal Snapshot & Normal Context
    normal_snap = MarketRiskSnapshot(
        spread=Decimal("0.0002"),
        volatility=Decimal("0.0150"),
        session="NY",
        freshness=datetime.now(UTC),
    )
    context_normal = {
        "spread_mean": 0.0002,
        "spread_std": 0.0001,
        "vol_short": 0.015,
        "vol_med": 0.015,
        "vol_long": 0.015,
        "tick_frequency": 30,
        "missing_bars": 0,
        "stale_seconds": 2,
    }
    result_normal = assess_risk_regime(normal_snap, [], base_config, context_normal)
    print(f"Normal Case status: {result_normal.status} (expected APPROVE)")
    print(f"  Regime: {result_normal.regime}")
    print(f"  Spread Regime: {result_normal.spread_regime}")
    print(f"  Volatility Regime: {result_normal.volatility_regime}")
    print(f"  Liquidity Regime: {result_normal.liquidity_regime}")

    # 2. Stale Snapshot
    stale_snap = normal_snap.model_copy(
        update={"freshness": datetime.now(UTC) - timedelta(seconds=120)}
    )
    result_stale = assess_risk_regime(
        stale_snap, [], base_config, {"max_stale_seconds": 60}
    )
    print(f"\nStale Data Case status: {result_stale.status} (expected BLOCK)")
    print(f"  Regime: {result_stale.regime}")
    print(f"  Reason: {result_stale.reason}")

    # 3. Volatility Spike
    # Short-term volatility (0.025) is more than 2.0x long-term volatility (0.010)
    context_spike = {"vol_short": 0.025, "vol_med": 0.010, "vol_long": 0.010}
    result_spike = assess_risk_regime(normal_snap, [], base_config, context_spike)
    print(f"\nVolatility Spike Case status: {result_spike.status} (expected REJECT)")
    print(f"  Volatility Regime: {result_spike.volatility_regime}")
    print(f"  Regime: {result_spike.regime}")
    print(f"  Reason: {result_spike.reason}")

    # 4. News Blackout Schedule
    now = datetime.now(UTC)
    calendar_news = [
        {"time": now + timedelta(minutes=2), "symbol": "EURUSD", "impact": "HIGH"},
    ]
    context_news = {"symbol": "EURUSD", "news_blackout_mins": 5.0}
    result_news = assess_risk_regime(
        normal_snap, calendar_news, base_config, context_news
    )
    print(f"\nNews Blackout Case status: {result_news.status} (expected REJECT)")
    print(f"  News Regime: {result_news.news_regime}")
    print(f"  Regime: {result_news.regime}")
    print(f"  Reason: {result_news.reason}")

    # 5. Rollover Blackout Schedule
    # Rollover scheduled in 2 minutes
    rollover_time = now + timedelta(minutes=2)
    rollover_snap = normal_snap.model_copy(update={"rollover_time": rollover_time})
    context_rollover = {"rollover_blackout_before_mins": 5.0}
    result_rollover = assess_risk_regime(
        rollover_snap, [], base_config, context_rollover
    )
    print(
        f"\nRollover Blackout Case status: {result_rollover.status} (expected REJECT)"
    )
    print(f"  Rollover Regime: {result_rollover.rollover_regime}")
    print(f"  Regime: {result_rollover.regime}")
    print(f"  Reason: {result_rollover.reason}")

    # 6. Live Profile Missing News Calendar (Fail-Closed)
    context_live = {"require_news_calendar": True}
    result_live_fail = assess_risk_regime(normal_snap, [], live_config, context_live)
    print(
        f"\nLive Stale Calendar Case status: {result_live_fail.status} (expected BLOCK)"
    )
    print(f"  Regime: {result_live_fail.regime}")
    print(f"  Reason: {result_live_fail.reason}")


def example_04_deterministic_limits() -> None:
    """Demonstrate pre-trade limit checks and sequential aggregation (Sprint 5.4)."""
    print("\n" + "=" * 100)
    print("--- Example 4: Deterministic Limits & Aggregation (Sprint 5.4) ---")
    print("=" * 100)

    # 1. Base components Setup
    base_config = load_risk_config("default")
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("1000.00"),
        free_margin=Decimal("99000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[],
    )
    trade = ProposedTrade(
        strategy_id="strategy-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.10"),
    )

    # Context with no breaches
    request = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=base_config,
        calendar_evidence=[],
        market_context={
            "kill_switch_active": False,
            "freshness": datetime.now(UTC),
            "daily_loss_pct": 0.0,
            "mode": RiskMode.PAPER,
            "portfolio_gross_exposure": 100000.0,
            "max_portfolio_exposure": 5.0,
        },
    )

    # A. Run passing limits check
    status, code, msg, flags, primary, _results = run_limit_checks(request, base_config)
    print("A. Normal Pass Check:")
    print(f"  Decision Status: {status} (expected APPROVE)")
    print(f"  Reason Code: {code}")
    print(f"  Message: {msg}")
    print(f"  Breach Flags: {flags}")
    print(f"  Primary Failure: {primary!r}")

    # B. Single Limit Breach (exposure limit)
    # Portfolio exposure = 600,000 + 10,000 = 610,000 (exceeds 5.0x of 100,000 equity)
    request.market_context["portfolio_gross_exposure"] = 600000.0
    status, code, msg, flags, primary, _results = run_limit_checks(request, base_config)
    print("\nB. Single Limit Breach Check:")
    print(f"  Decision Status: {status} (expected REJECT)")
    print(f"  Reason Code: {code}")
    print(f"  Message: {msg}")
    print(f"  Breach Flags: {flags}")
    print(f"  Primary Failure: {primary!r}")

    # C. Composite/Multiple Breaches
    # Trigger exposure breach (REJECT), daily loss breach (REJECT), and kill switch (BLOCK)
    # The aggregated status should be BLOCK (highest precedence)
    # The primary failure limit should be "kill_switch_state" as it runs first in sequence order among highest severity
    request.market_context["daily_loss_pct"] = 0.06
    request.market_context["kill_switch_active"] = True
    status, code, msg, flags, primary, _results = run_limit_checks(request, base_config)
    print("\nC. Composite Breaches Check (Kill Switch + Daily Loss + Exposure):")
    print(f"  Decision Status: {status} (expected BLOCK)")
    print(f"  Reason Code: {code}")
    print(f"  Message: {msg}")
    print(f"  Breach Flags: {flags}")
    print(f"  Primary Failure: {primary!r}")


def example_05_position_sizing() -> None:
    """Demonstrate position sizing methods and constraints verification (Sprint 5.5)."""
    print("\n" + "=" * 100)
    print("--- Example 5: Position Sizing & Constraints (Sprint 5.5) ---")
    print("=" * 100)

    # 1. Setup base structures
    base_config = load_risk_config("default")
    base_config.max_risk_per_trade = Decimal("0.05")
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[],
    )

    # EURUSD market context with standard broker constraints
    eurusd_context = {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "contract_size": 100000.0,
        "digits": 5,
        "tick_size": 0.00001,
        "tick_value": 1.0,
        "conversion_rate": 1.0,
    }

    # A. Fixed Risk Sizing (2% risk on 20 pips stop distance)
    # Risk per standard lot = 200 points * $1 = $200.
    # Risk amount = 100,000 * 2% = $2,000.
    # Expected Volume = 2000 / 200 = 10.0 lots.
    req_fixed = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("20.0"),
        risk_percent=Decimal("0.02"),
    )
    res_fixed = calculate_position_size(
        req_fixed, portfolio, eurusd_context, base_config
    )
    print("A. Fixed Risk Position Sizing (2%):")
    print(f"  Calculated Volume: {res_fixed.calculated_volume} lots (expected 10.0)")
    print(f"  Risk Contribution: {res_fixed.risk_contribution} USD")
    print(f"  Constraints Applied: {res_fixed.constraints_applied}")

    # B. Volatility Sizing (ATR-based stop loss)
    # ATR = 0.00100 (10 pips). Multiplier = 2.0 -> stop distance = 20 pips.
    # Expected Volume = 10.0 lots.
    req_vol = PositionSizingRequest(
        symbol="EURUSD",
        method=SizingMethod.VOLATILITY_ADJUSTED,
        atr_value=Decimal("0.00100"),
        multiplier=Decimal("2.0"),
        risk_percent=Decimal("0.02"),
    )
    res_vol = calculate_position_size(req_vol, portfolio, eurusd_context, base_config)
    print("\nB. Volatility-Adjusted Sizing:")
    print(f"  Calculated Volume: {res_vol.calculated_volume} lots (expected 10.0)")
    print(f"  Stop Distance (pips): {res_vol.stop_distance_pips}")
    print(f"  Constraints Applied: {res_vol.constraints_applied}")

    # C. Sizing with Downward Reductions
    # Step-down = 0.5 (from milestone), currency reduction = 0.8, cluster reduction = 0.9.
    # Expected Volume = 10.0 * 0.5 * 0.8 * 0.9 = 3.6 lots.
    reduced_context = eurusd_context.copy()
    reduced_context["drawdown_step_down_multiplier"] = 0.5
    reduced_context["currency_exposure_reduction"] = 0.8
    reduced_context["correlation_cluster_reduction"] = 0.9
    res_reduced = calculate_position_size(
        req_fixed, portfolio, reduced_context, base_config
    )
    print("\nC. Sizing with Downward Multipliers (Milestone + Currency + Cluster):")
    print(f"  Calculated Volume: {res_reduced.calculated_volume} lots (expected 3.60)")
    print(f"  Constraints Applied: {res_reduced.constraints_applied}")

    # D. JPY Pair Conversion
    # Digits = 3. Point size = 0.001. Stop distance = 50 pips (500 points).
    # Conversion rate is USDJPY rate (0.0091). Tick value = $0.91.
    # Risk = 1,000 USD (1%). Risk per lot = 500 * $0.91 = $455.
    # Expected volume = 1000 / 455 = 2.1978 -> 2.19 lots.
    jpy_context = {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "contract_size": 100000.0,
        "digits": 3,
        "tick_size": 0.001,
        "tick_value": 0.91,
        "conversion_rate": 0.0091,
    }
    req_jpy = PositionSizingRequest(
        symbol="USDJPY",
        method=SizingMethod.FIXED_RISK,
        stop_loss_pips=Decimal("50.0"),
        risk_percent=Decimal("0.01"),
    )
    res_jpy = calculate_position_size(req_jpy, portfolio, jpy_context, base_config)
    print("\nD. JPY Pair Sizing & Conversion:")
    print(f"  Calculated Volume: {res_jpy.calculated_volume} lots (expected 2.19)")
    print(f"  Risk Contribution: {res_jpy.risk_contribution} USD")


def example_06_fx_currency_exposure() -> None:
    """Demonstrate currency leg decomposition and exposure policies (Sprint 5.6)."""
    print("\n" + "=" * 100)
    print("--- Example 6: FX Currency Exposure & Policies (Sprint 5.6) ---")
    print("=" * 100)

    from app.services.risk import (
        calculate_currency_exposure,
        decompose_position,
    )

    base_config = load_risk_config("default")
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            # Long 1.0 lot EURUSD open position
            PositionState(
                position_id="pos-101",
                symbol="EURUSD",
                direction="long",
                quantity=Decimal("1.0"),
                entry_price=Decimal("1.10"),
                current_price=Decimal("1.10"),
                floating_pnl=Decimal("0.00"),
                margin_required=Decimal("1000.00"),
                strategy_id="strat-1",
                open_time=datetime.now(UTC),
            )
        ],
        orders=[
            # Pending Order: Buy Limit 1.0 EURUSD at 1.09 (distance = 100 pips)
            {
                "symbol": "EURUSD",
                "side": "buy",
                "quantity": 1.0,
                "price": 1.09,
                "distance_pips": 100.0,
                "probability": 0.3,
                "status": "active",
            }
        ],
    )

    market_context = {
        "EURUSD_contract_size": 100000.0,
        "EURUSD_price": 1.10,
        "mode": RiskMode.PAPER,
        "conversion_rates": {
            "EUR": 1.10,
        },
    }

    # A. Leg Decomposition
    legs = decompose_position(
        symbol="EURUSD",
        side="buy",
        quantity=Decimal("1.0"),
        price=Decimal("1.10"),
        contract_size=Decimal("100000.0"),
        base_ccy="EUR",
        quote_ccy="USD",
    )
    print("A. Position Leg Decomposition (EURUSD Buy 1.0 lot):")
    for leg in legs:
        print(f"  Leg Currency: {leg.currency}, Signed Amount: {leg.signed_amount}")

    # B. Pending Order Policy: Ignore (default)
    base_config.pending_order_policy = "ignore"
    exposures_ignore = calculate_currency_exposure(
        portfolio, None, base_config, market_context
    )
    print("\nB. Currency Exposures (Policy: Ignore pending orders):")
    print(
        f"  EUR Gross: {exposures_ignore['EUR'].gross} USD, Net: {exposures_ignore['EUR'].net} USD"
    )
    print(
        f"  USD Gross: {exposures_ignore['USD'].gross} USD, Net: {exposures_ignore['USD'].net} USD"
    )

    # C. Pending Order Policy: Full Potential
    base_config.pending_order_policy = "full-potential"
    exposures_full = calculate_currency_exposure(
        portfolio, None, base_config, market_context
    )
    print("\nC. Currency Exposures (Policy: Full Potential):")
    print(f"  EUR Net: {exposures_full['EUR'].net} USD (expected 220000.0)")

    # D. Proposed Trade Addition
    proposed = ProposedTrade(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="sell",  # Opposing trade to reduce EUR long exposure
        volume=Decimal("0.5"),
        price=Decimal("1.10"),
    )
    exposures_proposed = calculate_currency_exposure(
        portfolio, proposed, base_config, market_context
    )
    print("\nD. Currency Exposures with Proposed Opposing Trade (0.5 lot Sell):")
    print(f"  EUR Net: {exposures_proposed['EUR'].net} USD (expected 165000.0)")


def example_07_correlation_and_cluster_risk() -> None:
    """Demonstrate returns calculation, alignment, correlation matrix, spikes, clusters, and sizing multipliers."""
    print("\n" + "=" * 50)
    print("EXAMPLE 07: CORRELATION AND CLUSTER RISK")
    print("=" * 50)

    # 1. Setup mock bar series
    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    bars_a = [
        {"time": base_time + timedelta(minutes=i), "open": 100 + i, "close": 101 + i}
        for i in range(10)
    ]
    bars_b = [
        {
            "time": base_time + timedelta(minutes=i),
            "open": 200 + 2 * i,
            "close": 202 + 2 * i,
        }
        for i in range(10)
    ]

    # Calculate returns
    rets_a = calculate_returns(bars_a, ReturnType.CLOSE_TO_CLOSE, exclude_last=False)
    rets_b = calculate_returns(bars_b, ReturnType.CLOSE_TO_CLOSE, exclude_last=False)
    print(f"Calculated {len(rets_a)} returns for A and {len(rets_b)} returns for B.")

    # 2. Build snapshot
    snapshot = calculate_correlation_snapshot(
        {"EURUSD": bars_a, "GBPUSD": bars_b},
        min_samples=2,
        exclude_last=False,
    )
    print("\nCorrelation Matrix Snapshot:")
    for sym1, row in snapshot.matrix.items():
        for sym2, val in row.items():
            print(f"  Corr({sym1}, {sym2}): {val:.4f}")

    # 3. Detect spikes
    spikes = detect_correlation_spikes(snapshot, Decimal("0.80"))
    print(f"\nSpikes Detected (threshold 0.80): {spikes}")

    # 4. Connected cluster exposures
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            PositionState(
                position_id="pos-1",
                symbol="EURUSD",
                direction="long",
                quantity=Decimal("1.0"),
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1000"),
                floating_pnl=Decimal("0.0"),
                margin_required=Decimal("1000.0"),
                strategy_id="strat-1",
                open_time=datetime.now(UTC),
            )
        ],
    )

    market_context = {
        "EURUSD_contract_size": 100000.0,
        "GBPUSD_contract_size": 100000.0,
        "conversion_rates": {
            "EUR": 1.10,
            "GBP": 1.25,
            "USD": 1.0,
        },
        "market_data": {
            "EURUSD": bars_a,
            "GBPUSD": bars_b,
        },
        "GBPUSD_volume_step": 0.01,
    }

    clusters = calculate_cluster_exposures(
        portfolio_state=portfolio,
        proposed_trade=None,
        snapshot=snapshot,
        threshold=Decimal("0.50"),
        market_context=market_context,
    )
    print("\nConnected Cluster Exposures:")
    for name, val in clusters.items():
        print(f"  {name}: {val:.2f} USD")

    # 5. Sizing multiplier & marginal trade resolution
    proposed = ProposedTrade(
        strategy_id="strat-1",
        symbol="GBPUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.2500"),
    )
    config = RiskConfig(
        profile_name="usage_profile",
        correlation_threshold=Decimal("0.50"),
    )

    status, vol, msg = evaluate_proposed_trade_correlation(
        proposed_trade=proposed,
        portfolio_state=portfolio,
        snapshot=snapshot,
        config=config,
        market_context=market_context,
    )
    print("\nProposed Trade Resolution (Buy GBPUSD 1.0 lot):")
    print(f"  Decision Status: {status}")
    print(f"  Adjusted Volume: {vol:.2f}")
    print(f"  Reason: {msg}")


def example_08_var_and_expected_shortfall() -> None:
    """Demonstrate Parametric & Historical VaR and Expected Shortfall calculations (Sprint 5.8)."""
    print("\n" + "=" * 50)
    print("EXAMPLE 08: VALUE-AT-RISK AND EXPECTED SHORTFALL")
    print("=" * 50)

    # 1. Setup mock bar series with alternating walk to have actual gains & losses
    base_time = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
    bars_a = []
    price_a = 100.0
    for i in range(25):
        change = 1.0 if i % 2 == 0 else -1.5
        price_a += change
        bars_a.append(
            {
                "time": base_time + timedelta(minutes=i),
                "open": price_a - change,
                "close": price_a,
            }
        )

    bars_b = []
    price_b = 200.0
    for i in range(25):
        change = 2.0 if i % 2 == 0 else -3.0
        price_b += change
        bars_b.append(
            {
                "time": base_time + timedelta(minutes=i),
                "open": price_b - change,
                "close": price_b,
            }
        )

    # 2. Setup portfolio state
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("100000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            PositionState(
                position_id="pos-1",
                symbol="EURUSD",
                direction="long",
                quantity=Decimal("1.0"),
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1000"),
                floating_pnl=Decimal("0.0"),
                margin_required=Decimal("1000.0"),
                strategy_id="TF-01",
                open_time=datetime.now(UTC),
            )
        ],
    )

    market_context = {
        "EURUSD_contract_size": 100000.0,
        "GBPUSD_contract_size": 100000.0,
        "conversion_rates": {
            "EUR": 1.10,
            "GBP": 1.25,
            "USD": 1.0,
        },
        "market_data": {
            "EURUSD": bars_a,
            "GBPUSD": bars_b,
        },
    }

    config = RiskConfig(
        profile_name="usage_profile",
        correlation_threshold=Decimal("0.50"),
    )

    # Parametric Calculation
    var_snap, es_snap = calculate_var_es_snapshots(
        portfolio_state=portfolio,
        proposed_trade=None,
        market_context=market_context,
        config=config,
        var_confidence=Decimal("0.95"),
        es_confidence=Decimal("0.95"),
        var_method=VaRMethod.PARAMETRIC,
        es_method=ExpectedShortfallMethod.PARAMETRIC,
        min_samples=10,
        exclude_last=False,
    )

    print(f"Total Gross Exposure: {var_snap.exposure:.2f} USD")
    print(f"Portfolio Volatility: {var_snap.portfolio_volatility:.6f}")
    print(f"Parametric VaR (95%): {var_snap.result:.2f} USD")
    print(f"Parametric Expected Shortfall (95%): {es_snap.average_tail_loss:.2f} USD")

    # Historical Calculation
    var_hist, es_hist = calculate_var_es_snapshots(
        portfolio_state=portfolio,
        proposed_trade=None,
        market_context=market_context,
        config=config,
        var_confidence=Decimal("0.95"),
        es_confidence=Decimal("0.95"),
        var_method=VaRMethod.HISTORICAL,
        es_method=ExpectedShortfallMethod.HISTORICAL,
        min_samples=10,
        exclude_last=False,
    )
    print(f"\nHistorical VaR (95%): {var_hist.result:.2f} USD")
    print(f"Historical Expected Shortfall (95%): {es_hist.average_tail_loss:.2f} USD")

    # Risk Contributions
    contr = var_snap.assumptions.get("component_contributions", {})
    m_contr = var_snap.assumptions.get("marginal_contributions", {})
    print("\nEuler Risk Contributions:")
    for sym in contr:
        print(
            f"  {sym} - Component VaR: {contr[sym]:.2f} USD, Marginal Risk Contribution: {m_contr[sym]:.6f}"
        )


def example_09_stress_testing() -> None:
    """Demonstrate portfolio stress testing under default and custom scenarios (Sprint 5.9)."""
    print("\n" + "=" * 50)
    print("EXAMPLE 09: PORTFOLIO STRESS TESTING")
    print("=" * 50)

    # 1. Load the default scenario registry
    registry = build_default_scenario_registry()
    print(f"Loaded default scenario registry with {len(registry.scenarios)} scenarios.")

    # 2. Setup portfolio state with a EURUSD position and JPY position
    portfolio = PortfolioState(
        account_id="acc-001",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("2000.00"),
        free_margin=Decimal("8000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            PositionState(
                position_id="pos-eur",
                symbol="EURUSD",
                direction="long",
                quantity=Decimal("1.0"),
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1000"),
                floating_pnl=Decimal("0.00"),
                margin_required=Decimal("1000.00"),
                strategy_id="TF-01",
                open_time=datetime.now(UTC),
            ),
            PositionState(
                position_id="pos-jpy",
                symbol="USDJPY",
                direction="long",
                quantity=Decimal("1.0"),
                entry_price=Decimal("110.00"),
                current_price=Decimal("110.00"),
                floating_pnl=Decimal("0.00"),
                margin_required=Decimal("1000.00"),
                strategy_id="TF-01",
                open_time=datetime.now(UTC),
            ),
        ],
        orders=[],
    )

    market_context = {
        "EURUSD_contract_size": 100000.0,
        "USDJPY_contract_size": 100000.0,
        "EURUSD_pip_size": 0.0001,
        "USDJPY_pip_size": 0.01,
        "EURUSD_spread": 0.0002,
        "USDJPY_spread": 0.02,
        "EURUSD_volatility": Decimal("0.015"),
        "USDJPY_volatility": Decimal("0.012"),
        "conversion_rates": {
            "EUR": 1.10,
            "JPY": 0.009,
            "USD": 1.0,
        },
        "quote_age_stale": False,
    }

    config = RiskConfig(
        profile_name="usage_profile",
        max_daily_loss_pct=Decimal("0.05"),
        max_total_loss_pct=Decimal("0.10"),
        max_total_loss_pct_advisory=Decimal("0.08"),
        max_effective_leverage=Decimal("30.0"),
    )

    # 3. Evaluate portfolio under default scenarios
    results = registry.evaluate_portfolio(portfolio, None, market_context, config)
    print("\nDefault Stress Scenario Evaluation Results:")
    for res in results:
        status_str = "PASS" if res.pass_status else "FAIL"
        print(
            f"  Scenario: {res.scenario_name:<30} | Status: {status_str:<4} | "
            f"Loss Impact: {res.impact_pct * 100:>6.2f}% | Projected Equity: {res.projected_equity:>9.2f} USD"
        )
        if res.reason_codes:
            print(f"    Reason Codes: {res.reason_codes}")

    # 4. Demonstrate Custom Scenario creation & validation without code execution
    print("\nCustom Scenario Validation & Execution:")
    custom_config = {
        "name": "Custom European Meltdown",
        "price_shocks": {
            "EURUSD": -0.07,  # EURUSD drops 7%
            "USDJPY": 0.03,  # USDJPY rises 3%
        },
    }

    try:
        custom_scenario = validate_custom_scenario(custom_config)
        print(f"  Validated custom scenario: {custom_scenario.name}")

        # Register custom scenario
        # Wrap it in a PriceShockScenario class
        registry.register_scenario(
            custom_scenario.name,
            PriceShockScenario(custom_scenario.name, custom_scenario.price_shocks),
        )
        print(f"  Registered scenario '{custom_scenario.name}' to registry.")

        # Re-evaluate
        single_result = registry.scenarios[custom_scenario.name].evaluate(
            portfolio, None, market_context, config
        )
        status_str = "PASS" if single_result.pass_status else "FAIL"
        print(f"  Evaluation of '{custom_scenario.name}':")
        print(
            f"    Status: {status_str} | Loss Impact: {single_result.impact_pct * 100:.2f}% | "
            f"Projected Equity: {single_result.projected_equity:.2f} USD"
        )
    except AppValidationError as e:
        print(f"  Validation failed: {e}")


def example_10_margin_drawdown_execution() -> None:
    """Demonstrate margin, drawdown governors, and execution feasibility limits (Sprint 5.10)."""
    print("\n" + "=" * 50)
    print("EXAMPLE 10: MARGIN, DRAWDOWN, AND EXECUTION FEASIBILITY")
    print("=" * 50)

    # 1. Setup Portfolio & proposed trade
    portfolio = PortfolioState(
        account_id="acc-usage-10",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("1000.00"),
        free_margin=Decimal("9000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[
            PositionState(
                position_id="pos-eur-10",
                symbol="EURUSD",
                direction="long",
                quantity=Decimal("1.0"),
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1000"),
                floating_pnl=Decimal("0.00"),
                margin_required=Decimal("1000.00"),
                strategy_id="TF-01",
                open_time=datetime.now(UTC),
            )
        ],
        orders=[],
        strategy_allocations={"TF-01": Decimal("5000.00")},
    )

    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
    )

    market_context = {
        "EURUSD_contract_size": 100000.0,
        "EURUSD_pip_size": 0.0001,
        "EURUSD_spread": 0.0002,
        "EURUSD_volatility": Decimal("0.0001"),
        "EURUSD_slippage_limit": 3.0,
        "EURUSD_stop_level": 5.0,
        "EURUSD_freeze_level": 2.0,
        "EURUSD_volume_min": Decimal("0.01"),
        "EURUSD_volume_max": Decimal("100.0"),
        "EURUSD_volume_step": Decimal("0.01"),
        "conversion_rates": {
            "EUR": 1.10,
            "USD": 1.0,
        },
        "session": "OPEN",
        "historical_avg_volume": 2.0,
        "peak_balance": 10500.00,
        "spread_sigma_multiplier": 3.0,
        "slippage_sigma_multiplier": 3.0,
    }

    config = RiskConfig(
        profile_name="usage_profile",
        max_margin_utilization_pct=Decimal("0.80"),
        max_effective_leverage=Decimal("30.0"),
        max_risk_per_trade=Decimal("0.02"),
        max_total_loss_pct=Decimal("0.10"),
        max_total_loss_pct_advisory=Decimal("0.05"),
    )

    # --- A. Margin Governance ---
    print("\nA. Margin Governance Evaluation:")
    margin_snap = evaluate_margin_governance(portfolio, trade, market_context, config)
    print(f"  Projected Margin: {margin_snap.projected_margin:.2f} USD")
    print(f"  Projected Free Margin: {margin_snap.free_margin:.2f} USD")
    print(f"  Margin Usage: {margin_snap.margin_usage:.2%}")
    print(f"  Effective Leverage: {margin_snap.leverage:.2f}")

    margin_limits_res = verify_margin_limits(portfolio, trade, market_context, config)
    print(
        f"  Margin Limits Result: Status={margin_limits_res.status}, Breached={margin_limits_res.breached}"
    )

    # Exit liquidity stress check under extreme volatility
    exit_pass, exit_loss = exit_liquidity_stress_check(
        portfolio, trade, market_context, config, spread_multiplier=Decimal("5.0")
    )
    print(
        f"  Exit Liquidity Stress (5x spread): Pass={exit_pass}, Loss Impact={exit_loss:.2f} USD"
    )

    # --- B. Drawdown governor ---
    print("\nB. Drawdown Governor Evaluation:")
    daily_dd = calculate_daily_drawdown(portfolio, Decimal("10000.00"))
    total_dd = calculate_total_drawdown(portfolio, Decimal("10500.00"))
    print(f"  Daily Drawdown: {daily_dd:.2%}")
    print(f"  Total Drawdown: {total_dd:.2%}")

    # Verify throttling transition
    throttling_state, scale_mult = determine_drawdown_throttling(
        total_dd, config.max_total_loss_pct_advisory, config.max_total_loss_pct
    )
    print(
        f"  Throttling State: {throttling_state.value}, Multiplier Enforced: {scale_mult}"
    )

    drawdown_limits_res = verify_drawdown_limits(
        portfolio, trade, market_context, config
    )
    print(
        f"  Drawdown Limits Result: Status={drawdown_limits_res.status}, Reason={drawdown_limits_res.reason_code}"
    )

    # --- C. Execution Gate ---
    print("\nC. Execution Feasibility Gate Evaluation:")
    exec_snap = evaluate_execution_feasibility(portfolio, trade, market_context, config)
    print(f"  Marketability Check (Open session): {exec_snap.marketability}")
    print(f"  Slippage allowance: {exec_snap.slippage:.5f} (Quote currency)")

    exec_limits_res = verify_execution_limits(portfolio, trade, market_context, config)
    print(
        f"  Execution Limits Result: Status={exec_limits_res.status}, Reason={exec_limits_res.reason_code}"
    )


def example_11_allocation_and_lifecycle_governance() -> None:
    """Demonstrate capital allocation parity algorithms and lifecycle stage gates (Sprint 5.11)."""
    print("\n" + "=" * 100)
    print("--- Example 11: Allocation and Lifecycle Governance (Sprint 5.11) ---")
    print("=" * 100)

    strategies = ["strat1", "strat2", "strat3"]
    vols = {
        "strat1": Decimal("0.015"),
        "strat2": Decimal("0.025"),
        "strat3": Decimal("0.020"),
    }
    correlation_matrix = {
        "strat1": {"strat2": Decimal("0.50"), "strat3": Decimal("0.30")},
        "strat2": {"strat1": Decimal("0.50"), "strat3": Decimal("0.40")},
        "strat3": {"strat1": Decimal("0.30"), "strat2": Decimal("0.40")},
    }
    total_budget = Decimal("10000.00")

    # 1. Parity calculations
    equal_allocs = equal_risk_allocation(strategies, total_budget)
    vol_parity_allocs = volatility_parity_allocation(strategies, vols, total_budget)
    corr_parity_allocs = correlation_adjusted_risk_parity_allocation(
        strategies, vols, correlation_matrix, total_budget
    )

    print("\nStrategy Allocation Parity Calculations:")
    print("  Equal Risk Allocation:")
    for s, amt in equal_allocs.items():
        print(f"    {s}: {amt:.2f} USD")
    print("  Volatility Parity Allocation:")
    for s, amt in vol_parity_allocs.items():
        print(f"    {s}: {amt:.2f} USD")
    print("  Correlation-Adjusted Parity Allocation:")
    for s, amt in corr_parity_allocs.items():
        print(f"    {s}: {amt:.2f} USD")

    # 2. Allocation verify limits
    portfolio = PortfolioState(
        account_id="acc-alloc-demo",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[],
        orders=[],
        strategy_allocations={
            "strat1": Decimal("3000.00"),
            "strat2": Decimal("3000.00"),
        },
    )

    config = RiskConfig(
        profile_name="usage_profile",
        max_allocation_increase_pct=Decimal("0.20"),
        max_strategy_allocation_pct=Decimal("0.50"),
        min_backtest_trades=100,
        min_backtest_sharpe=Decimal("1.5"),
    )

    # Allocation increase proposal (strat1 from 3000 to 4500 is +50% increase)
    proposal = ProposedAllocation(
        allocations={"strat1": Decimal("4500.00"), "strat2": Decimal("3000.00")},
        as_of=datetime.now(UTC),
    )

    # Proposed allocation evaluation with missing performance evidence
    alloc_res_missing = verify_allocation_limits(portfolio, proposal, {}, config)
    print("\nAllocation Increase Gate - Missing Evidence:")
    print(f"  Status: {alloc_res_missing.status}")
    print(f"  Reason: {alloc_res_missing.message}")

    # Evaluation with valid stats but requires governed approval token
    market_context: dict[str, Any] = {
        "strategy_evidence": {
            "strat1": {
                "trade_count": 150,
                "sharpe_ratio": Decimal("1.8"),
            }
        }
    }
    alloc_res_need_approval = verify_allocation_limits(
        portfolio, proposal, market_context, config
    )
    print("\nAllocation Increase Gate - Requires Approval Token:")
    print(f"  Status: {alloc_res_need_approval.status}")
    print(f"  Reason: {alloc_res_need_approval.message}")

    # Evaluation with approval token validated
    market_context["approval_token_valid"] = True
    alloc_res_approved = verify_allocation_limits(
        portfolio, proposal, market_context, config
    )
    print("\nAllocation Increase Gate - Approved with Token:")
    print(f"  Status: {alloc_res_approved.status}")
    print(f"  Reason: {alloc_res_approved.message}")

    # 3. Lifecycle Gates Promotion Checks
    print("\nStrategy Promotion Gate Checks:")
    print(f"  Staging Sequence: {STAGE_SEQUENCE}")

    promotion_pass = evaluate_lifecycle_promotion(
        "strat1",
        "backtest",
        "walk-forward",
        {
            "trade_count": 120,
            "sharpe_ratio": Decimal("1.7"),
            "max_drawdown": Decimal("0.10"),
        },
        config,
    )
    print(f"  Backtest to Walk-Forward (Pass): Status={promotion_pass.status}")

    promotion_fail_skip = evaluate_lifecycle_promotion(
        "strat1",
        "backtest",
        "simulation",
        {},
        config,
    )
    print(
        f"  Backtest to Simulation (Fail Skip Gate): Status={promotion_fail_skip.status}, Message={promotion_fail_skip.message}"
    )

    # 4. Live Readiness gate
    print("\nLive Readiness Reviews:")
    readiness_res = evaluate_live_readiness(
        "strat1",
        "shadow",
        {
            "audit_persistence_active": True,
            "kill_switch_configured": True,
            "portfolio_reconciliation_active": True,
            "idempotency_evidence_present": True,
        },
        config,
    )
    print(
        f"  Live shadow stage readiness check: Status={readiness_res.status}, Message={readiness_res.message}"
    )


def example_12_kill_switches() -> None:
    """Demonstrate kill switch manager operations and automated triggers (Sprint 5.12)."""
    print("\n" + "=" * 100)
    print("--- Example 12: Kill Switches and Trigger Governance (Sprint 5.12) ---")
    print("=" * 100)

    # 1. Initialize manager using a temp file for persistence
    import tempfile

    from app.services.risk import (
        LimitResult,
        RiskDecisionStatus,
        RiskReasonCode,
        RiskSeverity,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        persistence_path = Path(tmpdir) / "kill_switch_state_example.json"
        manager = get_kill_switch_manager(persistence_path=persistence_path)

        # Reset any active switches for clean run
        with manager._lock:
            manager.states = {
                "global": {
                    "state": KillSwitchStateEnum.INACTIVE,
                    "reason": None,
                    "triggered_at": None,
                    "triggered_by": None,
                },
                "portfolio": {
                    "state": KillSwitchStateEnum.INACTIVE,
                    "reason": None,
                    "triggered_at": None,
                    "triggered_by": None,
                },
                "strategies": {},
                "symbols": {},
                "currencies": {},
            }
            manager.save()

        # 2. Check initial state
        print("Initial state check:")
        print(f"  Is global blocked? {manager.is_blocked('global', '*')}")
        print(f"  Is EURUSD symbol blocked? {manager.is_blocked('symbol', 'EURUSD')}")

        # 3. Trigger global halt manually
        print("\nTriggering global kill switch manually...")
        manager.trigger(
            scope="global",
            target="*",
            reason="Manual operator emergency halt",
            triggered_by="operator_01",
        )
        print(f"  Is global blocked? {manager.is_blocked('global', '*')}")
        print(
            f"  Is EURUSD symbol blocked (hierarchical check)? {manager.is_blocked('symbol', 'EURUSD')}"
        )

        # 4. Attempt to resume without token/role -> expect ValidationError
        print("\nAttempting to resume global halt without authorization...")
        try:
            manager.resume(scope="global", target="*")
        except AppValidationError as e:
            print(f"  ValidationError correctly caught: {e}")

        # 5. Resume with admin role
        print("\nResuming global halt with 'admin' operator role...")
        manager.resume(scope="global", target="*", operator_role="admin")
        print(f"  Is global blocked? {manager.is_blocked('global', '*')}")

        # 6. Auto-evaluate triggers on breach
        print(
            "\nSimulating pre-trade risk evaluation with a critical drawdown breach..."
        )
        req = RiskAssessmentRequest(
            proposed_action=ProposedTrade(
                strategy_id="strat1",
                symbol="EURUSD",
                side="buy",
                volume=Decimal("1.0"),
            ),
            portfolio_state=PortfolioState(
                account_id="acc-123",
                balance=Decimal("10000.00"),
                equity=Decimal("10000.00"),
                margin_used=Decimal("0.00"),
                free_margin=Decimal("10000.00"),
                floating_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                currency="USD",
                as_of=datetime.now(UTC),
                positions=[],
            ),
            risk_config=load_risk_config("default"),
            calendar_evidence=[],
            market_context={
                "kill_switch_active": False,
                "freshness": datetime.now(UTC),
                "daily_loss_pct": 0.0,
                "mode": "paper",
            },
        )

        drawdown_breach = LimitResult(
            limit_name="drawdown_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.DRAWDOWN_BREACH,
            message="Total drawdown threshold exceeded 10%",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

        triggered = manager.evaluate_triggers(req, [drawdown_breach])
        print(f"  Triggered scopes on drawdown breach: {triggered}")
        print(
            f"  Is EURUSD symbol blocked now? {manager.is_blocked('symbol', 'EURUSD')}"
        )

        # Clean up global singleton after demo to not pollute other tests
        with manager._lock:
            manager.states = {
                "global": {
                    "state": KillSwitchStateEnum.INACTIVE,
                    "reason": None,
                    "triggered_at": None,
                    "triggered_by": None,
                },
                "portfolio": {
                    "state": KillSwitchStateEnum.INACTIVE,
                    "reason": None,
                    "triggered_at": None,
                    "triggered_by": None,
                },
                "strategies": {},
                "symbols": {},
                "currencies": {},
            }
            manager.save()


def example_13_governor_orchestration() -> None:
    """Demonstrate governor orchestration and checks pipeline (Sprint 5.13)."""
    print("\n" + "=" * 100)
    print("--- Example 13: Risk Governor Orchestration (Sprint 5.13) ---")
    print("=" * 100)

    from app.services.risk import (
        InMemoryRiskStateStore,
        PortfolioState,
        ProposedTrade,
        RiskAssessmentRequest,
        RiskConfig,
        RiskGovernor,
    )

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={"mode": "paper", "environment": "local"},
    )
    req.request_id = "req_gov_demo"

    decision = gov.review_trade_risk(req)
    print(f"Governor Decision Status: {decision.status}")
    print(f"Governor Decision Reason: {decision.reason}")
    print(f"Calculated approved volume: {decision.calculated_volume}")


def example_14_audit_token_storage() -> None:
    """Demonstrate audit chaining, token signatures, and fail-closed storage (Sprint 5.14)."""
    print("\n" + "=" * 100)
    print("--- Example 14: Audit Chaining & Token boundaries (Sprint 5.14) ---")
    print("=" * 100)

    from app.services.risk import (
        InMemoryRiskStateStore,
        RiskGovernor,
        verify_risk_audit_chain,
    )

    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

    # 1. Verification of empty chain
    print(f"Initial empty audit chain verify: {verify_risk_audit_chain(store)}")

    # 2. Trigger check that generates chain
    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    portfolio = PortfolioState(
        account_id="acc_1",
        balance=Decimal("10000.00"),
        equity=Decimal("10000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("10000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={"mode": "paper", "environment": "local"},
    )
    req.request_id = "req_audit_demo"

    decision = gov.review_trade_risk(req)
    print(f"Chained audit log count: {len(store.get_all_events())}")
    print(f"Verify audit chain: {verify_risk_audit_chain(store)}")

    # 3. Token signing & validation
    details = decision.details or {}
    token_sig = details.get("decision_token")
    token_sig_str = str(token_sig) if token_sig else ""
    print(f"Signed token signature: {token_sig_str[:30]}...")


def example_15_official_risk_tools() -> None:
    """Demonstrate official AI-callable tools usage and envelopes (Sprint 5.15)."""
    print("\n" + "=" * 100)
    print("--- Example 15: Official AI Tools Registry (Sprint 5.15) ---")
    print("=" * 100)

    portfolio = {
        "account_id": "acc_1",
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_used": 0.0,
        "free_margin": 10000.0,
        "floating_pnl": 0.0,
        "realized_pnl": 0.0,
        "currency": "USD",
        "as_of": datetime.now(UTC).isoformat(),
        "positions": [],
    }
    market_context = {"mode": "paper"}

    res = build_portfolio_risk_snapshot(
        portfolio_state=portfolio,
        market_context=market_context,
        request_id="req_tool_demo",
    )
    print(f"Tool status: {res.get('status')}")
    print(f"Tool message: {res.get('message')}")
    metadata = res.get("metadata")
    trades = metadata.get("trades") if isinstance(metadata, dict) else None
    print(f"Tool metadata (trades=False): {trades}")


def example_16_reporting_and_observability() -> None:
    """Demonstrate report compilation, file output safety, and Prometheus metrics export (Sprint 5.16)."""
    print("\n" + "=" * 100)
    print("--- Example 16: Reports and Observability (Sprint 5.16) ---")
    print("=" * 100)

    from app.services.risk import (
        InMemoryRiskStateStore,
        PortfolioState,
        ProposedTrade,
        RiskAssessmentRequest,
        RiskConfig,
        RiskGovernor,
        generate_risk_report,
    )
    from app.services.risk.reports import RISK_METRICS_REGISTRY

    # 1. Initialize governor with in-memory stores
    store = InMemoryRiskStateStore()
    gov = RiskGovernor(store, store, store, store)

    # 2. Add some mock decisions to the storage by reviewing trade risk
    trade = ProposedTrade(
        strategy_id="strat_reporting",
        symbol="GBPUSD",
        side="buy",
        volume=Decimal("0.5"),
    )
    portfolio = PortfolioState(
        account_id="acc_reporting",
        balance=Decimal("20000.00"),
        equity=Decimal("20000.00"),
        margin_used=Decimal("0.00"),
        free_margin=Decimal("20000.00"),
        floating_pnl=Decimal("0.00"),
        realized_pnl=Decimal("0.00"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[],
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=RiskConfig(profile_name="default"),
        calendar_evidence=[],
        market_context={"mode": "paper", "environment": "local"},
    )
    req.request_id = "req_reporting_demo"

    # Make decisions to record metrics
    decision = gov.review_trade_risk(req)
    print(f"Reviewed trade risk. Status: {decision.status}")

    # 3. Generate risk report
    report = generate_risk_report(
        state_store=store,
        audit_sink=store,
        decision_store=store,
        request_id="trace_reporting_demo",
    )
    print("\nGenerated Risk Report:")
    print(f"  Report ID: {report.report_id}")
    print(f"  Generated At: {report.generated_at}")
    print(f"  Policy Profile: {report.policy_profile}")
    print(f"  Decisions Count: {len(report.decisions)}")
    if report.decisions:
        print(
            f"  First Decision Status: {report.decisions[0].status} on {report.decisions[0].symbol}"
        )

    # 4. Demonstrate optional file output and path traversal guard
    report_file_path = "risk_report_demo.json"
    print(f"\nWriting report to file: {report_file_path}")
    generate_risk_report(
        state_store=store,
        audit_sink=store,
        decision_store=store,
        request_id="trace_reporting_demo",
        write_to_path=report_file_path,
    )
    print(f"  File successfully written: {Path(report_file_path).exists()}")
    # Clean up the demo file
    if Path(report_file_path).exists():
        Path(report_file_path).unlink()

    # 5. Export metrics from RISK_METRICS_REGISTRY
    prometheus_metrics = RISK_METRICS_REGISTRY.export_prometheus_text()
    print("\nRISK_METRICS_REGISTRY Prometheus Export (sample):")
    # Print the lines of Prometheus output containing risk metrics
    lines = [
        line for line in prometheus_metrics.split("\n") if "haruquant_risk" in line
    ]
    for line in lines[:15]:
        print(f"  {line}")


if __name__ == "__main__":
    """Execute all risk governance usage examples."""
    print("==================================================")
    print("STARTING RISK GOVERNANCE USAGE EXAMPLES")
    print("==================================================")

    example_01_contracts_and_models()
    example_02_configs_and_policies()
    example_03_market_regime_gate()
    example_04_deterministic_limits()
    example_05_position_sizing()
    example_06_fx_currency_exposure()
    example_07_correlation_and_cluster_risk()
    example_08_var_and_expected_shortfall()
    example_09_stress_testing()
    example_10_margin_drawdown_execution()
    example_11_allocation_and_lifecycle_governance()
    example_12_kill_switches()
    example_13_governor_orchestration()
    example_14_audit_token_storage()
    example_15_official_risk_tools()
    example_16_reporting_and_observability()

    print("==================================================")
    print("ALL RISK GOVERNANCE USAGE EXAMPLES COMPLETED")
    print("==================================================")
