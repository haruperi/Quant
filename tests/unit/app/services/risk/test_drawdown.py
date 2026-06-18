"""Unit tests for the Drawdown Governor module.

Verifies daily/total drawdowns, state transitions, JSON state
persistence, and revenge trading.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.risk import (
    DrawdownState,
    PortfolioState,
    PositionState,
    ProposedTrade,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
)
from app.services.risk.drawdown import (
    DrawdownThrottlingState,
    calculate_daily_drawdown,
    calculate_strategy_drawdown,
    calculate_total_drawdown,
    check_revenge_trading,
    determine_drawdown_throttling,
    persist_drawdown_state,
    restore_drawdown_state,
    verify_drawdown_limits,
)


@pytest.fixture
def base_portfolio() -> PortfolioState:
    """Fixture for baseline PortfolioState."""
    return PortfolioState(
        account_id="acc-drawdown",
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
        strategy_allocations={"TF-01": Decimal("5000.00")},
    )


@pytest.fixture
def base_config() -> RiskConfig:
    """Fixture for baseline RiskConfig."""
    return RiskConfig(
        profile_name="default",
        max_total_loss_pct=Decimal("0.10"),
        max_total_loss_pct_advisory=Decimal("0.05"),
    )


def test_drawdown_calculations(base_portfolio: PortfolioState) -> None:
    """Verify daily and total drawdown calculation."""
    # 1. Total drawdown: peak balance = 11000. equity = 9900.
    # drawdown = (11k - 9.9k) / 11k = 10%
    base_portfolio.equity = Decimal("9900.00")
    drawdown = calculate_total_drawdown(base_portfolio, Decimal("11000.00"))
    assert drawdown == Decimal("0.10")

    # 2. Daily drawdown: daily starting = 10500. equity = 9975.
    # daily drawdown = (10500 - 9975) / 10500 = 5%
    base_portfolio.equity = Decimal("9975.00")
    daily = calculate_daily_drawdown(base_portfolio, Decimal("10500.00"))
    assert daily == Decimal("0.05")


def test_strategy_drawdown(base_portfolio: PortfolioState) -> None:
    """Verify strategy-specific drawdown calculation."""
    # Strategy TF-01 allocated = 5000. Floating PnL of its positions = -500.
    # strat_equity = 4500. Peak = 5000. Drawdown = 10%
    base_portfolio.positions = [
        PositionState(
            position_id="pos-1",
            symbol="EURUSD",
            direction="long",
            quantity=Decimal("1.0"),
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.0950"),
            floating_pnl=Decimal("-500.00"),
            margin_required=Decimal("1000.0"),
            strategy_id="TF-01",
            open_time=datetime.now(UTC),
        )
    ]

    strat_drawdown = calculate_strategy_drawdown(
        "TF-01", base_portfolio, Decimal("5000.00")
    )
    assert strat_drawdown == Decimal("0.10")


def test_drawdown_throttling_state_mapping() -> None:
    """Verify mapping of drawdown level to throttling category and multipliers."""
    soft = Decimal("0.05")
    hard = Decimal("0.10")

    # 1. Normal state: drawdown = 1% (< 2.5%)
    state, mult = determine_drawdown_throttling(Decimal("0.01"), soft, hard)
    assert state == DrawdownThrottlingState.NORMAL
    assert mult == Decimal("1.0")

    # 2. Caution state: drawdown = 3% (>= 2.5%, < 5%)
    state, mult = determine_drawdown_throttling(Decimal("0.03"), soft, hard)
    assert state == DrawdownThrottlingState.CAUTION
    assert mult == Decimal("0.8")

    # 3. Defensive state: drawdown = 6% (>= 5%, < 8%)
    state, mult = determine_drawdown_throttling(Decimal("0.06"), soft, hard)
    assert state == DrawdownThrottlingState.DEFENSIVE
    assert mult == Decimal("0.5")

    # 4. Recovery-only state: drawdown = 9% (>= 8%, < 10%)
    state, mult = determine_drawdown_throttling(Decimal("0.09"), soft, hard)
    assert state == DrawdownThrottlingState.RECOVERY_ONLY
    assert mult == Decimal("0.2")

    # 5. Halted state: drawdown = 11% (>= 10%)
    state, mult = determine_drawdown_throttling(Decimal("0.11"), soft, hard)
    assert state == DrawdownThrottlingState.HALTED
    assert mult == Decimal("0.0")


def test_drawdown_persistence(tmp_path: Any) -> None:
    """Verify drawdown state JSON persistence and restoration.

    Includes testing of corruption handling.
    """
    state_file = tmp_path / "drawdown_state.json"
    state = DrawdownState(
        current_drawdown=Decimal("0.04"),
        soft_limit=Decimal("0.05"),
        hard_limit=Decimal("0.10"),
        multiplier=Decimal("0.8"),
    )

    # Persist and restore
    persist_drawdown_state(state, state_file)
    assert state_file.exists()

    restored = restore_drawdown_state(state_file)
    assert restored is not None
    assert restored.current_drawdown == Decimal("0.04")
    assert restored.multiplier == Decimal("0.8")

    # Test file corruption handling
    with state_file.open("w", encoding="utf-8") as f:
        f.write("{invalid_json: true")  # corrupt JSON syntax

    corrupt_state = restore_drawdown_state(state_file)
    assert corrupt_state is None

    # Test missing keys
    with state_file.open("w", encoding="utf-8") as f:
        json.dump({"current_drawdown": 0.05, "multiplier": 0.5}, f)

    missing_keys_state = restore_drawdown_state(state_file)
    assert missing_keys_state is None


def test_revenge_trading_checks() -> None:
    """Verify that revenge trading check catches out-of-bounds trade sizes."""
    state = DrawdownState(
        current_drawdown=Decimal("0.06"),
        soft_limit=Decimal("0.05"),
        hard_limit=Decimal("0.10"),
        multiplier=Decimal("0.5"),  # defensive state multiplier
    )

    market_context = {"EURUSD_historical_avg_volume": Decimal("1.0")}

    # Proposed trade: volume = 0.4 lots (under 1.0 * 0.5 = 0.5 limit)
    trade_ok = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.4"),
    )
    is_revenge, msg = check_revenge_trading(trade_ok, state, market_context)
    assert not is_revenge
    assert msg == ""

    # Proposed trade: volume = 0.8 lots (exceeds 1.0 * 0.5 = 0.5 limit) -> REJECT
    trade_large = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.8"),
    )
    is_revenge_fail, msg_fail = check_revenge_trading(
        trade_large, state, market_context
    )
    assert is_revenge_fail
    assert "Revenge trading detected" in msg_fail


def test_verify_drawdown_limits(
    base_portfolio: PortfolioState,
    base_config: RiskConfig,
) -> None:
    """Verify verify_drawdown_limits checks for pass, warnings, and halt breaches."""
    # Pass path
    trade = ProposedTrade(
        strategy_id="TF-01",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
    )
    # Peak = 10000. Current equity = 10000 -> 0% drawdown -> passes
    res = verify_drawdown_limits(
        base_portfolio,
        trade,
        {"peak_balance": 10000.0, "historical_avg_volume": 1.0},
        base_config,
    )
    assert res.status == RiskDecisionStatus.APPROVE
    assert not res.breached

    # Multiplier reduction (Defensive state: drawdown = 6% > soft_limit 5%)
    base_portfolio.equity = Decimal("9400.00")
    res_def = verify_drawdown_limits(
        base_portfolio,
        trade,
        {"peak_balance": 10000.0, "historical_avg_volume": 2.0},
        base_config,
    )
    assert res_def.status == RiskDecisionStatus.REDUCE_SIZE
    assert not res_def.breached
    assert res_def.details["multiplier"] == 0.5

    # Revenge trading trigger
    # Under defensive mult=0.5, max volume allowed = 1.0 * 0.5 = 0.5.
    # Proposed is 1.0 lot -> REJECT
    res_revenge = verify_drawdown_limits(
        base_portfolio,
        trade,
        {"peak_balance": 10000.0, "historical_avg_volume": 1.0},
        base_config,
    )
    assert res_revenge.status == RiskDecisionStatus.REJECT
    assert res_revenge.breached

    # Hard drawdown halt (Halted state: drawdown = 12% > hard_limit 10%)
    base_portfolio.equity = Decimal("8800.00")
    res_halt = verify_drawdown_limits(
        base_portfolio,
        trade,
        {"peak_balance": 10000.0, "historical_avg_volume": 1.0},
        base_config,
    )
    assert res_halt.status == RiskDecisionStatus.BLOCK
    assert res_halt.breached
    assert res_halt.reason_code == RiskReasonCode.DRAWDOWN_BREACH
