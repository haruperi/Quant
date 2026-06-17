# ruff: noqa: E501
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.models import (
    PortfolioState,
    PositionSizingRequest,
    ProposedAllocation,
    RiskConfig,
)
from app.services.risk.sizing import AllocationService, calculate_position_size
from app.utils.errors import (
    InsufficientVolatilityEvidenceError,
    InvalidPortfolioStateError,
    MissingStopLossError,
)


@pytest.fixture
def base_config():
    return RiskConfig(
        max_daily_loss_pct=Decimal("0.05"),
        default_kelly_fraction=Decimal("0.25"),
        min_kelly_trades=3,
    )


@pytest.fixture
def base_portfolio():
    return PortfolioState(
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


@pytest.fixture(autouse=True)
def mock_mt5_symbol_info(mocker):
    # This fixture mocks get_symbol_info for all sizing tests so they succeed by default
    def get_mock_info(symbol):
        mock_info = mocker.MagicMock()
        symbol_upper = symbol.upper()
        if "JPY" in symbol_upper:
            mock_info.point = 0.001
            mock_info.digits = 3
        elif "OIL" in symbol_upper or "CFD" in symbol_upper:
            mock_info.point = 0.01
            mock_info.digits = 2
        else:
            mock_info.point = 0.00001
            mock_info.digits = 5
        mock_info.trade_contract_size = 100000.0
        return mock_info

    return mocker.patch(
        "app.services.brokers.mt5.get_symbol_info", side_effect=get_mock_info
    )


def test_fixed_lot_sizing():
    req = PositionSizingRequest(
        symbol="EURUSD", method="fixed_lot", fixed_volume=Decimal("0.5")
    )
    res = calculate_position_size(req, None, None)
    assert res.calculated_volume == Decimal("0.5")


def test_fixed_risk_sizing(base_portfolio, base_config):
    # standard fixed risk sizing
    req = PositionSizingRequest(
        symbol="EURUSD",
        method="fixed_risk",
        risk_percent=Decimal("1.0"),  # 1% of 10,000 = 100 USD
        stop_loss_pips=Decimal("20.0"),  # 20 pips
    )
    # EURUSD contract size = 100,000, pip scale = 0.0001 -> pip value = 10 USD per lot
    # volume = 100 USD / (20 pips * 10 USD) = 0.50 lot
    res = calculate_position_size(req, base_portfolio, base_config)
    assert res.calculated_volume == Decimal("0.5")
    assert res.stop_distance_pips == Decimal("20.0")

    # Missing stop loss raises MissingStopLossError
    bad_req = PositionSizingRequest(
        symbol="EURUSD", method="fixed_risk", risk_percent=Decimal("1.0")
    )
    with pytest.raises(MissingStopLossError):
        calculate_position_size(bad_req, base_portfolio, base_config)

    # Zero equity raises InvalidPortfolioStateError
    zero_portfolio = base_portfolio.model_copy(update={"equity": Decimal(0)})
    with pytest.raises(InvalidPortfolioStateError):
        calculate_position_size(req, zero_portfolio, base_config)


def test_kelly_sizing(base_portfolio, base_config):
    samples = [
        {"profit": 150.0},
        {"profit": 100.0},
        {"profit": -80.0},
        {"profit": 200.0},
    ]
    # win_rate = 3/4 = 0.75, average win = 150, average loss = 80 -> payoff = 1.875
    # kelly f = w - (1 - w)/R = 0.75 - 0.25 / 1.875 = 0.75 - 0.1333 = 0.6167
    req = PositionSizingRequest(symbol="EURUSD", method="kelly_criterion")

    # Fractional Kelly (default 0.25)
    res = calculate_position_size(
        req, base_portfolio, base_config, trade_samples=samples, has_waiver=False
    )
    assert res.kelly_fraction_applied is not None
    assert res.kelly_fraction_applied < Decimal("0.2")  # 0.6167 * 0.25 = 0.154

    # Full Kelly with waiver
    res_full = calculate_position_size(
        req, base_portfolio, base_config, trade_samples=samples, has_waiver=True
    )
    assert res_full.kelly_fraction_applied is not None
    assert res_full.kelly_fraction_applied > Decimal("0.6")


def test_volatility_sizing(base_portfolio, base_config):
    req = PositionSizingRequest(
        symbol="EURUSD", method="volatility", atr_value=Decimal("0.0020")
    )
    # stop = 0.0020 / 0.0001 = 20 pips. Multiplier 1.5 -> 30 pips.
    # risk = 1% = 100 USD. volume = 100 / (30 * 10) = 0.33 lots
    res = calculate_position_size(req, base_portfolio, base_config)
    assert res.calculated_volume == Decimal("0.33")
    assert res.stop_distance_pips == Decimal("30.0")

    # Missing ATR value raises error
    bad_req = PositionSizingRequest(symbol="EURUSD", method="volatility")
    with pytest.raises(InsufficientVolatilityEvidenceError):
        calculate_position_size(bad_req, base_portfolio, base_config)


def test_allocation_proposals(base_portfolio, base_config):
    # Propose allocation exceeding equity
    proposal = ProposedAllocation(
        allocations={"strat_A": Decimal(6000), "strat_B": Decimal(5000)},
        as_of=datetime.now(UTC),
    )
    res = AllocationService.propose(proposal, base_portfolio, base_config)
    assert res["status"] == "rejected"

    # Propose strategy allocation exceeding 50% cap
    bad_proposal = ProposedAllocation(
        allocations={"strat_A": Decimal(6000)}, as_of=datetime.now(UTC)
    )
    res2 = AllocationService.propose(bad_proposal, base_portfolio, base_config)
    assert res2["status"] == "rejected"

    # Healthy allocation
    good_proposal = ProposedAllocation(
        allocations={"strat_A": Decimal(4000), "strat_B": Decimal(4000)},
        as_of=datetime.now(UTC),
    )
    res3 = AllocationService.propose(good_proposal, base_portfolio, base_config)
    assert res3["status"] == "accepted"


def test_allocation_generators():
    # Equal capital
    proposal = AllocationService.equal_capital(["A", "B", "C"], Decimal(9000))
    assert proposal.allocations == {
        "A": Decimal(3000),
        "B": Decimal(3000),
        "C": Decimal(3000),
    }

    # Empty strategy list
    proposal_empty = AllocationService.equal_capital([], Decimal(9000))
    assert proposal_empty.allocations == {}

    # Confidence weighted
    confidences = {"A": Decimal("1.5"), "B": Decimal("0.5"), "C": Decimal("0.0")}
    proposal_weighted = AllocationService.confidence_weighted(
        confidences, Decimal(1000)
    )
    # total = 2.0. A get 750, B gets 250, C gets 0.
    assert proposal_weighted.allocations == {
        "A": Decimal("750.00"),
        "B": Decimal("250.00"),
    }


def test_sizing_edge_cases(base_portfolio, base_config):
    # 1. Fixed lot fallback
    req = PositionSizingRequest(symbol="EURUSD", method="fixed_lot")
    res = calculate_position_size(req, base_portfolio, base_config)
    assert res.calculated_volume == Decimal("0.10")

    # 2. Fixed risk with specific risk_amount
    req_amount = PositionSizingRequest(
        symbol="EURUSD",
        method="fixed_risk",
        risk_amount=Decimal(150),
        stop_loss_pips=Decimal(30),
    )
    res_amount = calculate_position_size(req_amount, base_portfolio, base_config)
    assert res_amount.calculated_volume == Decimal("0.50")

    # 3. Fixed risk with fallback to config default
    req_fallback = PositionSizingRequest(
        symbol="EURUSD", method="fixed_risk", stop_loss_pips=Decimal(50)
    )
    res_fallback = calculate_position_size(req_fallback, base_portfolio, base_config)
    # default daily loss pct is 5% of 10,000 = 500 USD. 50 pips stop -> volume = 500 / 500 = 1.00 lot
    assert res_fallback.calculated_volume == Decimal("1.00")

    # 4. Milestone sizing cases
    req_milestone = PositionSizingRequest(symbol="EURUSD", method="milestone")

    portfolio_low = base_portfolio.model_copy(update={"equity": Decimal(5000)})
    assert calculate_position_size(
        req_milestone, portfolio_low, base_config
    ).calculated_volume == Decimal("0.10")

    portfolio_mid = base_portfolio.model_copy(update={"equity": Decimal(30000)})
    assert calculate_position_size(
        req_milestone, portfolio_mid, base_config
    ).calculated_volume == Decimal("0.50")

    portfolio_high = base_portfolio.model_copy(update={"equity": Decimal(75000)})
    assert calculate_position_size(
        req_milestone, portfolio_high, base_config
    ).calculated_volume == Decimal("1.00")

    portfolio_max = base_portfolio.model_copy(update={"equity": Decimal(120000)})
    assert calculate_position_size(
        req_milestone, portfolio_max, base_config
    ).calculated_volume == Decimal("2.00")

    # 5. Volatility adjusted with multiplier
    req_vol = PositionSizingRequest(
        symbol="EURUSD",
        method="volatility",
        atr_value=Decimal("0.0020"),
        multiplier=Decimal("2.0"),
    )
    res_vol = calculate_position_size(req_vol, base_portfolio, base_config)
    # stop = 20 * 2.0 = 40 pips. risk = 1% = 100 USD. volume = 100 / (40 * 10) = 0.25 lot
    assert res_vol.calculated_volume == Decimal("0.25")

    # 6. Fixed fractional size
    req_frac = PositionSizingRequest(
        symbol="EURUSD", method="fixed_fractional", risk_percent=Decimal("2.0")
    )
    res_frac = calculate_position_size(req_frac, base_portfolio, base_config)
    # allocated capital = 2% of 10000 = 200. Default 30 pips stop -> volume = 200 / 300 = 0.67
    assert res_frac.calculated_volume == Decimal("0.67")

    # 7. Kelly edge cases (no losing trades -> payoff_ratio 2.0)
    req_kelly = PositionSizingRequest(symbol="EURUSD", method="kelly_criterion")
    winning_samples = [{"profit": 100.0}] * 5
    res_win = calculate_position_size(
        req_kelly, base_portfolio, base_config, trade_samples=winning_samples
    )
    assert res_win.kelly_fraction_applied is not None

    # 8. Kelly negative fraction edge case
    losing_samples = [{"profit": -100.0}] * 5
    res_lose = calculate_position_size(
        req_kelly, base_portfolio, base_config, trade_samples=losing_samples
    )
    assert res_lose.calculated_volume == Decimal("0.01")  # clamped fallback

    # 9. Confidence weighted allocation with all-zero/negative confidence
    empty_allocation = AllocationService.confidence_weighted(
        {"A": Decimal("-1.0"), "B": Decimal("0.0")}, Decimal(1000)
    )
    assert empty_allocation.allocations == {}


def test_dynamic_mt5_symbol_info_pip_scale(mocker):
    # Mock get_symbol_info to return EURUSD properties
    mock_info = mocker.MagicMock()
    mock_info.point = 0.00001
    mock_info.digits = 5
    mocker.patch("app.services.brokers.mt5.get_symbol_info", return_value=mock_info)

    from app.services.risk.sizing import get_pip_scale

    assert get_pip_scale("EURUSD") == Decimal("0.0001")


def test_dynamic_mt5_symbol_info_pip_scale_3_digits(mocker):
    # Mock get_symbol_info to return USDJPY properties
    mock_info = mocker.MagicMock()
    mock_info.point = 0.001
    mock_info.digits = 3
    mocker.patch("app.services.brokers.mt5.get_symbol_info", return_value=mock_info)

    from app.services.risk.sizing import get_pip_scale

    assert get_pip_scale("USDJPY") == Decimal("0.01")


def test_dynamic_mt5_symbol_info_pip_scale_2_digits(mocker):
    # Mock get_symbol_info to return 2-digit instrument (e.g. USOIL) properties
    mock_info = mocker.MagicMock()
    mock_info.point = 0.01
    mock_info.digits = 2
    mocker.patch("app.services.brokers.mt5.get_symbol_info", return_value=mock_info)

    from app.services.risk.sizing import get_pip_scale

    assert get_pip_scale("USOIL") == Decimal("0.01")


def test_dynamic_mt5_symbol_info_contract_size(mocker):
    # Mock get_symbol_info to return contract size
    mock_info = mocker.MagicMock()
    mock_info.trade_contract_size = 100000.0
    mocker.patch("app.services.brokers.mt5.get_symbol_info", return_value=mock_info)

    from app.services.risk.sizing import get_contract_size

    assert get_contract_size("EURUSD") == Decimal(100000)


def test_dynamic_mt5_symbol_info_fallback(mocker):
    # Mock get_symbol_info to raise Exception or return None to trigger ValidationError
    mocker.patch(
        "app.services.brokers.mt5.get_symbol_info", side_effect=Exception("Offline")
    )

    from app.services.risk.sizing import get_contract_size, get_pip_scale
    from app.utils.errors import ValidationError

    with pytest.raises(ValidationError):
        get_pip_scale("EURUSD")
    with pytest.raises(ValidationError):
        get_contract_size("EURUSD")
