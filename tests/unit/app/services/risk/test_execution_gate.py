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
    PortfolioState,
    PositionState,
    ProposedTrade,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
)
from app.services.risk.execution_gate import (
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
