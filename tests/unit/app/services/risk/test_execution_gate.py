"""Unit tests for the Execution Feasibility Gate module.

Verifies spread/slippage to sigma, stop compliance, volume steps,
sessions, and frequency limits.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    ExecutionRiskGate,
    PortfolioState,
    PositionState,
    ProposedTrade,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
    SlippagePolicy,
    SpreadPolicy,
    check_lot_step_validity,
    check_slippage_limit,
    check_spread_limit,
    check_stop_distance_validity,
)
from app.services.risk.execution_gate import (
    check_holding_time_limit,
    check_slippage_to_sigma,
    check_spread_to_sigma,
    check_stop_freeze_level,
    check_trade_frequency,
    check_volume_feasibility,
    verify_execution_limits,
)


@pytest.fixture
def base_portfolio() -> PortfolioState:
    """Fixture for baseline PortfolioState."""
    return PortfolioState(
        account_id="acc-exec",
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
    )


@pytest.fixture
def base_config() -> RiskConfig:
    """Fixture for baseline RiskConfig."""
    return RiskConfig(profile_name="default")


@pytest.fixture
def market_context() -> dict[str, Any]:
    """Fixture for market context."""
    return {
        "EURUSD_spread": 0.0002,
        "EURUSD_pip_size": 0.0001,
        "EURUSD_volatility": Decimal("0.0001"),  # sigma = 1 pip
        "EURUSD_slippage_limit": 3.0,
        "EURUSD_stop_level": 5.0,  # 5 pips
        "EURUSD_freeze_level": 2.0,  # 2 pips
        "EURUSD_volume_min": Decimal("0.01"),
        "EURUSD_volume_max": Decimal("100.0"),
        "EURUSD_volume_step": Decimal("0.01"),
        "session": "OPEN",
        "spread_sigma_multiplier": 3.0,
        "slippage_sigma_multiplier": 3.0,
    }


def test_spread_and_slippage_to_sigma() -> None:
    """Verify spread and slippage checks against standard deviations."""
    # Volatility sigma = 0.0001 (1 pip). Max multiplier = 3.0 -> limit = 0.0003
    # Spread = 0.0002 -> passes
    assert check_spread_to_sigma(Decimal("0.0002"), Decimal("0.0001"), Decimal("3.0"))
    # Spread = 0.0004 -> fails
    assert not check_spread_to_sigma(
        Decimal("0.0004"), Decimal("0.0001"), Decimal("3.0")
    )

    # Slippage = 2 pips (0.0002) <= 2.0 * sigma -> passes
    assert check_slippage_to_sigma(Decimal("0.0002"), Decimal("0.0001"), Decimal("2.0"))
    # Slippage = 3 pips (0.0003) > 2.0 * sigma -> fails
    assert not check_slippage_to_sigma(
        Decimal("0.0003"), Decimal("0.0001"), Decimal("2.0")
    )


def test_stop_freeze_level_compliance() -> None:
    """Verify stop loss distance complies with broker minimum thresholds."""
    pip_size = Decimal("0.0001")

    # Proposed trade sl = 1.0900 (distance = 100 pips > stop_level 5 pips)
    trade_ok = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
    )
    passed, msg = check_stop_freeze_level(
        trade_ok, Decimal("5.0"), Decimal("2.0"), pip_size
    )
    assert passed
    assert msg == ""

    # Proposed trade sl = 1.0997 (distance = 3 pips < stop_level 5 pips) -> fails
    trade_bad = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0997"),
    )
    failed, msg_fail = check_stop_freeze_level(
        trade_bad, Decimal("5.0"), Decimal("2.0"), pip_size
    )
    assert not failed
    assert "below broker stop_level threshold" in msg_fail


def test_volume_feasibility_step_granularities() -> None:
    """Verify proposed lot volume size checks against broker constraints."""
    min_vol = Decimal("0.01")
    max_vol = Decimal("100.0")
    step = Decimal("0.01")

    # Volume = 0.05 -> passes
    passed, msg = check_volume_feasibility(Decimal("0.05"), min_vol, max_vol, step)
    assert passed
    assert msg == ""

    # Volume = 0.005 -> fails min
    failed_min, msg_min = check_volume_feasibility(
        Decimal("0.005"), min_vol, max_vol, step
    )
    assert not failed_min
    assert "below broker minimum" in msg_min

    # Volume = 0.055 -> fails lot step (0.01 step)
    failed_step, msg_step = check_volume_feasibility(
        Decimal("0.055"), min_vol, max_vol, step
    )
    assert not failed_step
    assert "does not align with broker lot step" in msg_step


def test_trade_frequency_gate(base_portfolio: PortfolioState) -> None:
    """Verify trade frequency protection gates prevent runaway trade spikes."""
    now = datetime.now(UTC)
    base_portfolio.positions = [
        PositionState(
            position_id=f"pos-{i}",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("0.10"),
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1000"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("100.00"),
            strategy_id="TF-01",
            open_time=now
            - timedelta(seconds=i * 10),  # positions opened in last 0, 10, 20, 30, 40s
        )
        for i in range(5)
    ]

    # Limit = 5 trades/minute -> passes
    passed, msg = check_trade_frequency(base_portfolio, "TF-01", max_trades_per_min=6)
    assert passed
    assert msg == ""

    # Limit = 4 trades/minute -> fails
    failed, msg_fail = check_trade_frequency(
        base_portfolio, "TF-01", max_trades_per_min=4
    )
    assert not failed
    assert "Trade frequency limit breached" in msg_fail


def test_verify_execution_limits(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
    market_context: dict[str, Any],
) -> None:
    """Verify execution limits for spread, slippage, stop level, and volume gates."""
    # Pass path
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
    )
    res = verify_execution_limits(base_portfolio, trade, market_context, base_config)
    assert res.status == RiskDecisionStatus.APPROVE
    assert not res.breached

    # Market closed check
    market_context["session"] = "CLOSED"
    res_closed = verify_execution_limits(
        base_portfolio, trade, market_context, base_config
    )
    assert res_closed.status == RiskDecisionStatus.REJECT
    assert res_closed.reason_code == RiskReasonCode.SPREAD_BREACH
    assert "market is closed" in res_closed.message
    market_context["session"] = "OPEN"

    # Spread to sigma breach (spread 2 pips, limit = 1.5 * 1 pip = 1.5 pips)
    market_context["spread_sigma_multiplier"] = 1.5
    res_spread = verify_execution_limits(
        base_portfolio, trade, market_context, base_config
    )
    assert res_spread.status == RiskDecisionStatus.REJECT
    assert res_spread.reason_code == RiskReasonCode.SPREAD_BREACH


def test_execution_feasibility_gate_helpers() -> None:
    """Verify helpers check_spread_limit, check_slippage_limit, etc."""
    # check_spread_limit
    policy = SpreadPolicy(
        max_spread=Decimal("0.0050"), spread_sigma_multiplier=Decimal("3.0")
    )
    passed, msg = check_spread_limit(Decimal("0.0020"), Decimal("0.0010"), policy)
    assert passed
    assert msg == ""

    passed, msg = check_spread_limit(Decimal("0.0060"), Decimal("0.0010"), policy)
    assert not passed
    assert "exceeds absolute max spread" in msg

    # check_slippage_limit
    slip_policy = SlippagePolicy(
        max_slippage=Decimal("0.0020"), slippage_sigma_multiplier=Decimal("2.0")
    )
    passed, msg = check_slippage_limit(
        Decimal("0.0010"), Decimal("0.0010"), slip_policy
    )
    assert passed

    passed, msg = check_slippage_limit(
        Decimal("0.0030"), Decimal("0.0010"), slip_policy
    )
    assert not passed

    # check_stop_distance_validity
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
    )
    passed, msg = check_stop_distance_validity(
        trade, Decimal("5.0"), Decimal("2.0"), Decimal("0.0001")
    )
    assert passed

    # Representability: Stop loss not aligning with pip size
    # (e.g. 1.09005 with pip size 0.0001)
    trade_bad = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.09005"),
    )
    passed, msg = check_stop_distance_validity(
        trade_bad, Decimal("5.0"), Decimal("2.0"), Decimal("0.0001")
    )
    assert not passed
    assert "cannot be represented" in msg

    # Target price representability check
    trade_tp_bad = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
        intended_target=Decimal("1.11005"),
    )
    passed, msg = check_stop_distance_validity(
        trade_tp_bad, Decimal("5.0"), Decimal("2.0"), Decimal("0.0001")
    )
    assert not passed
    assert "cannot be represented" in msg

    # check_lot_step_validity
    passed, msg, reduced = check_lot_step_validity(
        Decimal("1.51"), Decimal("0.01"), Decimal("100.0"), Decimal("0.1")
    )
    assert passed

    passed, msg, reduced = check_lot_step_validity(
        Decimal("1.55"), Decimal("0.01"), Decimal("100.0"), Decimal("0.1")
    )
    assert not passed
    assert reduced == Decimal("1.51")  # volume_min (0.01) + 15 * 0.1 = 1.51

    passed, msg, reduced = check_lot_step_validity(
        Decimal("150.0"), Decimal("0.01"), Decimal("100.0"), Decimal("0.01")
    )
    assert not passed
    assert reduced == Decimal("100.0")

    # check_holding_time_limit
    trade_hold = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        expected_holding_period=3600.0,
    )
    passed, msg = check_holding_time_limit(trade_hold, {"max_holding_time": 7200.0})
    assert passed

    passed, msg = check_holding_time_limit(trade_hold, {"max_holding_time": 1800.0})
    assert not passed
    assert "exceeds maximum allowed duration" in msg


def test_execution_risk_gate_orchestrator_success(
    base_portfolio: PortfolioState,
) -> None:
    """Verify ExecutionRiskGate success and modification checks."""
    config = RiskConfig(profile_name="default")
    gate = ExecutionRiskGate(config)

    # Injected broker constraint metadata
    ctx = {
        "EURUSD_stop_level": 5.0,
        "EURUSD_freeze_level": 2.0,
        "EURUSD_volume_min": Decimal("0.01"),
        "EURUSD_volume_max": Decimal("100.0"),
        "EURUSD_volume_step": Decimal("0.01"),
        "EURUSD_pip_size": Decimal("0.0001"),
        "EURUSD_spread": 0.0002,
        "EURUSD_volatility": Decimal("0.0001"),
        "EURUSD_freshness": datetime.now(UTC).isoformat(),
        "session": "OPEN",
        "EURUSD_slippage_limit": Decimal("3.0"),
        "slippage_sigma_multiplier": Decimal("3.0"),
    }

    # Pass trade
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
    )
    res = gate.check_execution_feasibility(base_portfolio, trade, ctx)
    assert res.status == RiskDecisionStatus.APPROVE, (
        f"Failed: {res.message} (Reason: {res.reason_code})"
    )
    assert not res.breached

    # Size reduction suggestion
    trade_large = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("150.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
    )
    res_large = gate.check_execution_feasibility(base_portfolio, trade_large, ctx)
    assert res_large.status == RiskDecisionStatus.REDUCE_SIZE
    assert res_large.reduced_volume == Decimal("100.0")


def test_execution_risk_gate_orchestrator_failures(
    base_portfolio: PortfolioState,
) -> None:
    """Verify ExecutionRiskGate checks that trigger rejections."""
    from datetime import timedelta

    config = RiskConfig(profile_name="default")
    gate = ExecutionRiskGate(config)

    # Injected broker constraint metadata
    ctx = {
        "EURUSD_stop_level": 5.0,
        "EURUSD_freeze_level": 2.0,
        "EURUSD_volume_min": Decimal("0.01"),
        "EURUSD_volume_max": Decimal("100.0"),
        "EURUSD_volume_step": Decimal("0.01"),
        "EURUSD_pip_size": Decimal("0.0001"),
        "EURUSD_spread": 0.0002,
        "EURUSD_volatility": Decimal("0.0001"),
        "EURUSD_freshness": datetime.now(UTC).isoformat(),
        "session": "OPEN",
        "EURUSD_slippage_limit": Decimal("3.0"),
        "slippage_sigma_multiplier": Decimal("3.0"),
    }

    # Pass trade
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        stop_loss=Decimal("1.0900"),
    )

    # Stale metadata check in live
    ctx_live = dict(ctx)
    ctx_live["mode"] = "micro_live"
    ctx_live["EURUSD_freshness"] = (
        datetime.now(UTC) - timedelta(seconds=120)
    ).isoformat()
    res_stale = gate.check_execution_feasibility(base_portfolio, trade, ctx_live)
    assert res_stale.status == RiskDecisionStatus.REJECT
    assert res_stale.reason_code == RiskReasonCode.STALE_EVIDENCE

    # Missing metadata check
    ctx_missing = dict(ctx)
    ctx_missing["mode"] = "micro_live"
    del ctx_missing["EURUSD_stop_level"]
    res_missing = gate.check_execution_feasibility(base_portfolio, trade, ctx_missing)
    assert res_missing.status == RiskDecisionStatus.REJECT
    assert "missing fields" in res_missing.message

    # Inconsistent metadata check
    ctx_inconsistent = dict(ctx)
    ctx_inconsistent["EURUSD_volume_min"] = Decimal("10.0")
    ctx_inconsistent["EURUSD_volume_max"] = Decimal("5.0")
    res_inconsistent = gate.check_execution_feasibility(
        base_portfolio, trade, ctx_inconsistent
    )
    assert res_inconsistent.status == RiskDecisionStatus.REJECT
    assert "volume_min 10.0 > volume_max 5.0" in res_inconsistent.message

    # Spread limit breach
    ctx_spread = dict(ctx)
    ctx_spread["EURUSD_spread"] = 0.0006
    res_spread = gate.check_execution_feasibility(base_portfolio, trade, ctx_spread)
    assert res_spread.status == RiskDecisionStatus.REJECT
    assert res_spread.reason_code == RiskReasonCode.SPREAD_BREACH

    # M1 micro-scalping profile spread check
    ctx_m1 = dict(ctx)
    ctx_m1["timeframe"] = "M1"
    # Volatility is 1 pip. Multiplier for M1 is 1.5 -> limit = 1.5 pips = 0.00015
    # Spread is 0.0002 (2 pips) -> fails
    res_m1 = gate.check_execution_feasibility(base_portfolio, trade, ctx_m1)
    assert res_m1.status == RiskDecisionStatus.REJECT
    assert "exceeds volatility limit" in res_m1.message

    # Filling mode compatibility
    ctx_filling = dict(ctx)
    ctx_filling["EURUSD_filling_mode"] = "FOK, IOC"
    trade_filling_bad = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
        price=Decimal("1.1000"),
        order_type="buy_limit",
    )
    res_filling = gate.check_execution_feasibility(
        base_portfolio, trade_filling_bad, ctx_filling
    )
    assert res_filling.status == RiskDecisionStatus.REJECT
    assert "not authorized by broker" in res_filling.message

    # Multi-dimension trade frequency
    ctx_freq = dict(ctx)
    ctx_freq["max_trades_per_min_symbol"] = 2
    base_portfolio.positions = [
        PositionState(
            position_id=f"pos-{i}",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("0.10"),
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1000"),
            floating_pnl=Decimal("0.00"),
            margin_required=Decimal("100.00"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
        for i in range(2)
    ]
    res_freq = gate.check_execution_feasibility(base_portfolio, trade, ctx_freq)
    assert res_freq.status == RiskDecisionStatus.REJECT
    assert res_freq.reason_code == RiskReasonCode.FREQUENCY_BREACH
    assert "Trade frequency limit breached for symbol" in res_freq.message
