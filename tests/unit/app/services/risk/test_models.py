"""Unit tests for risk governance data models."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.models import (
    PortfolioState,
    ProposedTrade,
    RiskConfig,
)
from pydantic import ValidationError


def test_risk_config_defaults():
    cfg = RiskConfig()
    assert cfg.max_daily_loss_pct == Decimal("0.05")
    assert cfg.max_total_loss_pct == Decimal("0.10")
    assert cfg.double_spend_prevention_owner == "risk_cache"
    assert cfg.schema_version == "1.0.0"


def test_proposed_trade_validation():
    # Success path
    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
        stop_loss=Decimal("0.99"),
    )
    assert trade.symbol == "EURUSD"
    assert trade.volume == Decimal("0.1")

    # Invalid side
    with pytest.raises(ValidationError):
        ProposedTrade(
            strategy_id="strat_1",
            symbol="EURUSD",
            side="invalid",
            volume=Decimal("0.1"),
        )


def test_portfolio_state_validation():
    # Success path
    portfolio = PortfolioState(
        account_id="acc_123",
        balance=Decimal(10000),
        equity=Decimal(10000),
        margin_used=Decimal(0),
        free_margin=Decimal(10000),
        floating_pnl=Decimal(0),
        realized_pnl=Decimal(0),
        currency="USD",
        as_of=datetime.now(UTC),
    )
    assert portfolio.account_id == "acc_123"
    assert portfolio.balance == Decimal(10000)

    # Missing field
    with pytest.raises(ValidationError):
        PortfolioState(
            account_id="acc_123",
            balance=Decimal(10000),
        )


def test_canonical_json_round_trip():
    trade = ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    json_str = trade.to_json()
    assert "EURUSD" in json_str
    assert "buy" in json_str

    # Reload from json
    reloaded = ProposedTrade.model_validate_json(json_str)
    assert reloaded.symbol == trade.symbol
    assert reloaded.volume == trade.volume


def test_canonical_json_coercion_types():
    now = datetime.now(UTC)
    portfolio = PortfolioState(
        account_id="acc_123",
        balance=Decimal(10000),
        equity=Decimal(10000),
        margin_used=Decimal(0),
        free_margin=Decimal(10000),
        floating_pnl=Decimal(0),
        realized_pnl=Decimal(0),
        currency="USD",
        historical_returns=[Decimal("0.01"), Decimal("-0.02")],
        as_of=now,
    )
    json_str = portfolio.to_json()
    assert now.isoformat() in json_str
    assert "0.01" in json_str or "0.01" in json_str.lower()

    # Verify it decodes correctly
    decoded = PortfolioState.model_validate_json(json_str)
    assert decoded.historical_returns == [Decimal("0.01"), Decimal("-0.02")]


def test_canonical_json_serialization_failure():
    class ErrorTrade(ProposedTrade):
        def model_dump(self, *_args, **_kwargs):
            raise ValueError("Simulated model dump error")

    trade = ErrorTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.1"),
    )
    from app.utils.errors import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        trade.to_json()
    assert "Failed to serialize contract" in str(exc_info.value)
