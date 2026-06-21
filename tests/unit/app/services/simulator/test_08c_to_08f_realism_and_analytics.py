"""Unit tests for realism models and simulator reporting/analytics."""

import pytest
from app.services.simulator.analytics import build_scorecard_from_simulator_result
from app.services.simulator.models.liquidity import (
    OrderBookLevel,
    OrderBookLiquidityModel,
)
from app.services.simulator.models.slippage import (
    VolatilitySlippageModel,
    VolumeSlippageModel,
)
from app.services.simulator.models.spread import VariableSpreadModel
from app.services.simulator.report import build_json_report, build_markdown_report
from app.utils.errors import ValidationError


def test_variable_spread_model_validation() -> None:
    """Verify that VariableSpreadModel validates bounds and point size correctly."""
    # Invalid bounds
    with pytest.raises(ValidationError):
        VariableSpreadModel(min_spread_points=-1.0)
    with pytest.raises(ValidationError):
        VariableSpreadModel(min_spread_points=10.0, max_spread_points=5.0)
    # Invalid point
    with pytest.raises(ValidationError):
        VariableSpreadModel(point=0.0)


def test_variable_spread_model_build_tick() -> None:
    """Verify that VariableSpreadModel generates ticks with seeded randomness."""
    model = VariableSpreadModel(
        min_spread_points=10.0,
        max_spread_points=20.0,
        point=0.0001,
        seed=100,
    )

    # Invalid mid price
    with pytest.raises(ValidationError):
        model.build_tick(
            timestamp="2026-01-01T00:00:00Z", symbol="EURUSD", mid_price=-1.0
        )

    tick = model.build_tick(
        timestamp="2026-01-01T00:00:00Z",
        symbol="EURUSD",
        mid_price=1.1000,
        tick_index=1,
    )
    assert tick.symbol == "EURUSD"
    assert tick.bid < 1.1000
    assert tick.ask > 1.1000
    assert tick.spread_points is not None
    assert 10.0 <= tick.spread_points <= 20.0


def test_volatility_slippage_model_validation_and_apply() -> None:
    """Verify volatility-based slippage model constraints and calculations."""
    # Validation checks
    with pytest.raises(ValidationError):
        VolatilitySlippageModel(base_slippage_points=-1.0)
    with pytest.raises(ValidationError):
        VolatilitySlippageModel(volatility_multiplier=-0.5)
    with pytest.raises(ValidationError):
        VolatilitySlippageModel(point=0)

    model = VolatilitySlippageModel(
        base_slippage_points=2.0,
        volatility_multiplier=1.5,
        point=0.0001,
    )

    # Invalid apply inputs
    with pytest.raises(ValidationError):
        model.apply(
            side="invalid",  # type: ignore[arg-type]
            expected_price=1.1,
            executable_price=1.1,
            filled_volume=1.0,
        )
    with pytest.raises(ValidationError):
        model.apply(
            side="buy", expected_price=-1.0, executable_price=1.1, filled_volume=1.0
        )
    with pytest.raises(ValidationError):
        model.apply(
            side="buy",
            expected_price=1.1,
            executable_price=1.1,
            filled_volume=1.0,
            volatility=-0.0001,
        )

    # Executing apply
    res_buy = model.apply(
        side="buy",
        expected_price=1.1000,
        executable_price=1.1000,
        filled_volume=1.0,
        volatility=0.0002,
    )
    assert res_buy.slippage_points == 2.0 + 1.5 * (0.0002 / 0.0001)
    assert res_buy.final_price > 1.1000

    # Zero volume receives no slippage
    res_zero = model.apply(
        side="buy",
        expected_price=1.1000,
        executable_price=1.1000,
        filled_volume=0.0,
    )
    assert res_zero.slippage_points == 0.0
    assert res_zero.final_price == 1.1000


def test_volume_slippage_model_validation_and_apply() -> None:
    """Verify volume-dependent slippage model constraints and calculations."""
    with pytest.raises(ValidationError):
        VolumeSlippageModel(base_slippage_points=-1.0)
    with pytest.raises(ValidationError):
        VolumeSlippageModel(point=-0.0001)

    model = VolumeSlippageModel(
        base_slippage_points=1.0,
        volume_multiplier=0.5,
        point=0.0001,
    )

    with pytest.raises(ValidationError):
        model.apply(
            side="invalid",  # type: ignore[arg-type]
            expected_price=1.1,
            executable_price=1.1,
            filled_volume=1.0,
        )

    res_buy = model.apply(
        side="buy",
        expected_price=1.1000,
        executable_price=1.1000,
        filled_volume=2.0,
    )
    # 1.0 + 0.5 * 2.0 = 2.0 slippage points
    assert res_buy.slippage_points == 2.0
    assert res_buy.final_price == round(1.1000 + 2.0 * 0.0001, 10)


def test_order_book_liquidity_model() -> None:
    """Verify OrderBookLevel and OrderBookLiquidityModel validation."""
    # Level validation
    with pytest.raises(ValidationError):
        OrderBookLevel(price=-1.0, volume=10.0)
    with pytest.raises(ValidationError):
        OrderBookLevel(price=1.1, volume=-5.0)

    # Empty book validation
    with pytest.raises(ValidationError):
        OrderBookLiquidityModel(bids=(), asks=())

    bids = (
        OrderBookLevel(price=1.0990, volume=1.5),
        OrderBookLevel(price=1.0980, volume=3.0),
    )
    asks = (
        OrderBookLevel(price=1.1010, volume=1.0),
        OrderBookLevel(price=1.1020, volume=2.5),
    )
    model = OrderBookLiquidityModel(bids=bids, asks=asks)

    # Invalid fill arguments
    with pytest.raises(ValidationError):
        model.fill(requested_volume=-1.0, side="buy")
    with pytest.raises(ValidationError):
        model.fill(requested_volume=1.0, side="invalid")

    # Walk buy side (asks)
    fill_buy = model.fill(requested_volume=2.0, side="buy")
    assert fill_buy.requested_volume == 2.0
    # Available volume is 1.0 @ 1.1010, 2.5 @ 1.1020. So 2.0 is fully filled.
    assert fill_buy.filled_volume == 2.0
    assert fill_buy.remainder_volume == 0.0

    # Walk sell side (bids) with IOC policy
    fill_sell = model.fill(requested_volume=5.0, side="sell", time_in_force="IOC")
    assert fill_sell.requested_volume == 5.0
    # Available bids total volume: 1.5 + 3.0 = 4.5. Remainder is 0.5.
    assert fill_sell.filled_volume == 4.5
    assert fill_sell.remainder_volume == 0.5
    assert fill_sell.diagnostic_code == "SIM_IOC_REMAINDER_CANCELLED"


def test_reports_and_scorecard() -> None:
    """Verify JSON/Markdown reports and scorecard mapping."""
    result = {
        "run_id": "test_run_123",
        "classification": "backtest",
        "realism_disclosure": "simulated",
        "summary_metrics": {"sharpe": 1.5, "win_rate": 0.6},
    }

    json_rep = build_json_report(result)
    assert "test_run_123" in json_rep
    assert '"sharpe": 1.5' in json_rep

    md_rep = build_markdown_report(result)
    assert "# Simulator Report test_run_123" in md_rep
    assert "- `sharpe`: 1.5" in md_rep

    # Mock scorecards mapping
    scorecard = build_scorecard_from_simulator_result(
        trades=[],
        equity_curve=[{"timestamp": "2026-01-01T00:00:00Z", "equity": 1000.0}],
        run_id="test_run_123",
    )
    assert isinstance(scorecard, dict)
