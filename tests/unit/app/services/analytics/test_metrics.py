# ruff: noqa: PLR0915
"""Comprehensive unit tests for metric calculation kernels in Analytics.

Verifies trade metrics, equity/returns, drawdown indices, risk-adjusted metrics,
ratios, statistical distributions, benchmark comparisons, and dashboard downsampling.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
import pytest
from app.services.analytics.adapters import TradingResultAdapter
from app.services.analytics.benchmark import (
    alpha,
    batting_average,
    beta,
    calculate_benchmark_metrics,
    information_ratio,
    r_squared,
    tracking_error,
)
from app.services.analytics.dashboard import _downsample_curve, build_overview_payload
from app.services.analytics.distributions import (
    benjamini_hochberg_correction,
    bonferroni_correction,
    bootstrap_confidence_intervals,
    bootstrap_confidence_intervals_backtest,
    bootstrap_probability_above_threshold,
    calculate_distribution_metrics,
    deflated_sharpe_ratio,
    detect_outliers,
    distribution_fit_quality,
    fat_tail_score,
    fit_distribution,
    higher_moments,
    histogram_data,
    jarque_bera_test,
    kurtosis,
    outlier_ratio,
    percentile_summary,
    permutation_test,
    permutation_test_backtest,
    probability_of_backtest_overfitting,
    qq_plot_data,
    r_multiple_distribution,
    return_distribution,
    sample_size_warning,
    shapiro_wilk_test,
    skewness,
    stability_score,
    tail_ratio,
    upside_downside_summary,
    walk_forward_degradation_score,
    whites_reality_check,
    whites_reality_check_backtests,
)
from app.services.analytics.drawdown import (
    account_size_required,
    adjusted_net_profit_as_percent_of_max_strategy_drawdown,
    avg_drawdown,
    avg_drawdown_duration,
    avg_yearly_max_drawdown,
    calculate_drawdown_metrics,
    calmar_ratio,
    drawdown_distribution,
    drawdown_probability,
    fouse_ratio,
    max_close_to_close_drawdown_percent,
    max_drawdown,
    max_drawdown_duration,
    max_drawdown_duration_from_returns,
    max_relative_drawdown_percent,
    max_strategy_drawdown,
    max_strategy_drawdown_percent,
    net_profit_as_percent_of_max_strategy_drawdown,
    pain_index,
    pain_ratio,
    recovery_factor,
    return_on_max_close_to_close_drawdown,
    return_on_max_strategy_drawdown,
    rina_index,
    select_net_profit_as_percent_of_max_strategy_drawdown,
    sterling_ratio,
    time_to_recovery,
    ulcer_index,
)
from app.services.analytics.efficiency import (
    capital_efficiency,
    exit_efficiency,
    loss_containment_efficiency,
    return_per_calendar_day,
    return_per_unit_mae,
)
from app.services.analytics.equity import (
    annual_returns,
    avg_underwater_drawdown_percent,
    benchmark_returns,
    calculate_equity_metrics,
    calculate_return_metrics,
    daily_returns,
    drawdown_series,
    log_returns_series,
    max_drawdown_duration_from_equity,
    max_strategy_drawdown_date,
    monthly_returns,
    relative_drawdown_series,
    return_on_initial_capital,
    returns_series,
    total_return,
    total_return_usd,
    weekly_returns,
)
from app.services.analytics.ratios import (
    adjusted_net_profit_as_percent_of_largest_loss,
    adjusted_profit_factor,
    calculate_ratio_metrics,
    edge_ratio,
    expectancy_over_std,
    gain_to_pain_ratio,
    kappa_ratio,
    mfe_to_mae_ratio,
    net_profit_as_percent_of_largest_loss,
    omega_ratio,
    payoff_ratio,
    profit_to_mae_ratio,
    select_net_profit_as_percent_of_largest_loss,
    select_profit_factor,
    sharpe_ratio,
    sortino_ratio,
)
from app.services.analytics.risk import (
    annualized_volatility,
    calculate_risk_metrics,
    compounding_risk_of_ruin,
    conditional_var,
    downside_volatility,
    expected_shortfall,
    exposure_time_ratio,
    historical_var_by_symbol,
    max_gross_exposure,
    max_nominal_exposure_simple,
    portfolio_margin_utilization_curve,
    portfolio_var_from_covariance,
    profit_per_pip_risk,
    risk_adjusted_efficiency,
    time_weighted_avg_exposure,
    upside_potential_ratio,
    value_at_risk,
    volatility,
)
from app.services.analytics.trade import (
    adjusted_gross_loss,
    adjusted_gross_profit,
    adjusted_net_profit,
    avg_consecutive_losses,
    avg_consecutive_wins,
    avg_loss,
    avg_single_trade_margin_utilization,
    avg_time_in_trade,
    avg_trade_nominal_exposure,
    avg_win,
    calculate_analytics_for_subset,
    calculate_commission_impact,
    calculate_long_short_split,
    calculate_period_analysis,
    calculate_session_performance,
    calculate_slippage_impact,
    calculate_spread_cost_impact,
    calculate_trade_metrics,
    classify_trades,
    commission_paid,
    compute_r_trade_metrics,
    compute_trade_metrics,
    expectancy,
    expectancy_r,
    get_analytics_overview,
    get_closed_trades,
    get_mae_mfe_r,
    get_r_multiples,
    largest_loss,
    largest_win,
    longest_flat_period_duration,
    max_consecutive_losses,
    max_consecutive_wins,
    max_gross_size_held,
    max_long_size_held,
    max_net_size_held,
    max_runup,
    max_runup_date,
    max_short_size_held,
    max_single_trade_margin_utilization,
    max_size_held,
    max_time_in_trade,
    median_mae_mfe,
    median_time_in_trade,
    min_time_in_trade,
    open_position_pnl,
    percent_time_in_market,
    profit_factor,
    return_on_account,
    risk_of_ruin,
    risk_of_ruin_with_custom_horizon,
    select_gross_loss,
    select_gross_profit,
    select_net_profit,
    slippage_paid,
    swap_paid,
    t_statistic,
    time_in_market_duration,
    total_trades,
    trade_efficiency,
    trade_outcome_entropy,
    win_loss_streaks,
    win_rate,
)
from app.utils.errors import ValidationError


@pytest.fixture
def sample_trades() -> list[dict[str, Any]]:
    return [
        {
            "trade_id": "t1",
            "open_time": "2026-01-01T00:00:00Z",
            "close_time": "2026-01-01T04:00:00Z",
            "direction": "long",
            "profit_loss": 100.0,
            "initial_risk": 50.0,
            "mae": -20.0,
            "mfe": 140.0,
            "size": 1.0,
            "open_price": 1.1000,
            "margin": 200.0,
            "slippage": 1.5,
            "commission": 2.0,
            "swap": 0.5,
        },
        {
            "trade_id": "t2",
            "open_time": "2026-01-02T00:00:00Z",
            "close_time": "2026-01-02T04:00:00Z",
            "direction": "short",
            "profit_loss": -40.0,
            "initial_risk": 50.0,
            "mae": -50.0,
            "mfe": 10.0,
            "size": 1.0,
            "open_price": 1.1050,
            "margin": 200.0,
            "slippage": 0.5,
            "commission": 2.0,
            "swap": 0.0,
        },
    ]


@pytest.fixture
def sample_equity() -> list[dict[str, Any]]:
    return [
        {"timestamp": "2026-01-01T00:00:00Z", "equity": 10000.0},
        {"timestamp": "2026-01-02T00:00:00Z", "equity": 10100.0},
        {"timestamp": "2026-01-03T00:00:00Z", "equity": 10060.0},
    ]


# --- Adapters ---


def test_adapters_validation():
    with pytest.raises(ValidationError, match="dictionary"):
        TradingResultAdapter.to_canonical([])

    with pytest.raises(ValidationError, match="Missing required keys"):
        TradingResultAdapter.to_canonical({})

    bad_payload = {
        "schema_version": " ",
        "result_id": "bt_1",
        "phase": "backtest",
        "trades": [],
        "equity_curve": [],
    }
    with pytest.raises(ValidationError, match="schema_version"):
        TradingResultAdapter.to_canonical(bad_payload)

    bad_payload["schema_version"] = "2.0.0"
    with pytest.raises(ValidationError, match="Unsupported schema version"):
        TradingResultAdapter.to_canonical(bad_payload)

    bad_payload["schema_version"] = "1.3"
    bad_payload["result_id"] = " "
    with pytest.raises(ValidationError, match="result_id"):
        TradingResultAdapter.to_canonical(bad_payload)

    bad_payload["result_id"] = "bt_1"
    bad_payload["phase"] = "invalid_phase"
    with pytest.raises(ValidationError, match="phase"):
        TradingResultAdapter.to_canonical(bad_payload)

    bad_payload["phase"] = "backtest"
    bad_payload["trades"] = {}
    with pytest.raises(ValidationError, match="trades"):
        TradingResultAdapter.to_canonical(bad_payload)

    bad_payload["trades"] = []
    bad_payload["equity_curve"] = {}
    with pytest.raises(ValidationError, match="equity_curve"):
        TradingResultAdapter.to_canonical(bad_payload)


def test_adapters_success():
    payload = {
        "schema_version": "1.0.0",
        "result_id": "bt_1",
        "phase": "backtest",
        "trades": [],
        "equity_curve": [],
    }
    canonical = TradingResultAdapter.to_canonical(payload)
    assert canonical["schema_version"] == "1.0.0"
    assert canonical["strategy_id"] == "default_strategy"
    assert canonical["account_base_currency"] == "USD"


# --- Trade Calculations & Tools ---


def test_closed_trades_filtering(sample_trades):
    # Add an open trade
    trades = [*sample_trades, {"trade_id": "t3", "is_open": True}]
    closed = get_closed_trades(trades)
    assert len(closed) == 2


def test_trade_classification(sample_trades):
    classes = classify_trades(sample_trades)
    assert len(classes["wins"]) == 1
    assert len(classes["losses"]) == 1


def test_r_multiples(sample_trades):
    r_mults = get_r_multiples(sample_trades)
    assert r_mults == [2.0, -0.8]

    # Test missing risk fallback
    trades_no_risk = [{"trade_id": "t1", "profit_loss": 50.0}]
    r_mults_fallback = get_r_multiples(trades_no_risk)
    assert r_mults_fallback == [50.0]


def test_win_rate_profit_factor_tools(sample_trades):
    res_total = total_trades(sample_trades, request_id="req_test")
    assert res_total["status"] == "success"
    assert res_total["data"] == 2

    res_wr = win_rate(sample_trades, request_id="req_test")
    assert res_wr["status"] == "success"
    assert res_wr["data"] == 0.5

    res_pf = profit_factor(sample_trades, request_id="req_test")
    assert res_pf["status"] == "success"
    assert res_pf["data"] == 2.5

    # Test empty inputs
    assert total_trades([])["data"] == 0
    assert win_rate([])["data"] == 0.0
    assert profit_factor([])["data"] == 0.0

    # Test single win (infinite profit factor check)
    win_only = [{"trade_id": "t1", "close_time": "1", "profit_loss": 100.0}]
    assert profit_factor(win_only)["data"] == 999.0


def test_stats_metrics(sample_trades):
    assert avg_win(sample_trades) == 100.0
    assert avg_loss(sample_trades) == -40.0
    assert largest_win(sample_trades) == 100.0
    assert largest_loss(sample_trades) == -40.0
    assert expectancy(sample_trades) == 30.0
    assert max_consecutive_wins(sample_trades) == 1
    assert max_consecutive_losses(sample_trades) == 1

    # Test empty stats
    assert avg_win([]) == 0.0
    assert avg_loss([]) == 0.0
    assert largest_win([]) == 0.0
    assert largest_loss([]) == 0.0
    assert expectancy([]) == 0.0


def test_trade_metrics_extended(sample_trades):
    # Time in trade helpers
    assert avg_time_in_trade([]) == 0.0
    assert median_time_in_trade([]) == 0.0
    assert max_time_in_trade([]) == 0.0
    assert min_time_in_trade([]) == 0.0

    t_metrics = calculate_trade_metrics(sample_trades, request_id="req_test")
    assert t_metrics["status"] == "success"
    assert t_metrics["data"]["total_trades"] == 2
    assert t_metrics["data"]["win_rate"] == 0.5
    assert t_metrics["data"]["avg_time_in_trade"] == 4.0

    # R trade metrics
    r_stats = compute_r_trade_metrics([1.0, -0.5, 2.0])
    assert r_stats["avg"] == 0.8333333333333334
    assert r_stats["std"] == pytest.approx(1.2583057)

    assert compute_r_trade_metrics([]) == {"avg": 0.0, "std": 0.0, "expectancy": 0.0}
    assert compute_trade_metrics([1.0])["avg"] == 1.0

    # Trade efficiency & outcome entropy
    assert trade_efficiency({"profit_loss": 50.0, "mfe": 100.0}) == 0.5
    assert trade_efficiency({"profit_loss": 50.0, "mfe": 0.0}) == 0.0
    assert trade_outcome_entropy(sample_trades) > 0.0
    assert trade_outcome_entropy([]) == 0.0

    # Flat period
    assert longest_flat_period_duration([]) == 0.0
    flat_dur = longest_flat_period_duration(
        sample_trades,
        period_start="2026-01-01T00:00:00Z",
        period_end="2026-01-03T00:00:00Z",
    )
    assert flat_dur > 0.0

    # Exposure & ruin probability
    assert avg_trade_nominal_exposure([]) == 0.0
    assert avg_trade_nominal_exposure(sample_trades) > 0.0
    assert max_single_trade_margin_utilization(sample_trades) == 200.0
    assert avg_single_trade_margin_utilization(sample_trades) == 200.0
    assert avg_single_trade_margin_utilization([]) == 0.0

    assert (
        risk_of_ruin(
            sample_trades, initial_balance=1000.0, ruin_threshold=500.0, iterations=10
        )
        >= 0.0
    )
    assert risk_of_ruin([], 1000.0, 500.0) == 0.0
    assert (
        risk_of_ruin(sample_trades, initial_balance=400.0, ruin_threshold=500.0) == 0.0
    )

    assert (
        risk_of_ruin_with_custom_horizon(
            sample_trades, initial_balance=1000.0, ruin_threshold=500.0, horizon=5
        )
        >= 0.0
    )
    assert risk_of_ruin_with_custom_horizon([], 1000.0, 500.0) == 0.0

    # Sizes
    assert max_gross_size_held(sample_trades) == 1.0
    assert max_size_held(sample_trades) == 1.0
    assert max_net_size_held(sample_trades) == 1.0
    assert max_long_size_held(sample_trades) == 1.0
    assert max_short_size_held(sample_trades) == 1.0

    # Time in market
    assert time_in_market_duration([]) == 0.0
    assert time_in_market_duration(sample_trades) == 8.0
    assert percent_time_in_market(sample_trades, 24.0) == pytest.approx(8.0 / 24.0)
    assert percent_time_in_market(sample_trades, 0.0) == 0.0

    # Win loss streaks
    assert win_loss_streaks([]) == {"wins": [], "losses": []}
    assert win_loss_streaks(sample_trades) == {"wins": [1], "losses": [1]}
    assert avg_consecutive_wins(sample_trades) == 1.0
    assert avg_consecutive_losses(sample_trades) == 1.0
    assert avg_consecutive_wins([]) == 0.0
    assert avg_consecutive_losses([]) == 0.0

    # MAE/MFE R
    assert get_mae_mfe_r(sample_trades) == [
        {"mae_r": -0.4, "mfe_r": 2.8},
        {"mae_r": -1.0, "mfe_r": 0.2},
    ]
    assert median_mae_mfe(sample_trades) == {"mae": -20.0, "mfe": 140.0}

    # T-statistic
    assert t_statistic(sample_trades) > -999.0
    assert t_statistic([]) == 0.0
    assert t_statistic([{"trade_id": "t1", "profit_loss": 50.0}]) == 0.0

    # Open position
    assert open_position_pnl([]) == 0.0
    assert open_position_pnl([{"is_open": True, "pnl": 40.0}]) == 40.0


def test_trade_cost_impact(sample_trades):
    assert slippage_paid(sample_trades) == 2.0
    assert commission_paid(sample_trades) == 4.0
    assert swap_paid(sample_trades) == 0.5

    assert calculate_spread_cost_impact(sample_trades) == 0.0
    assert calculate_slippage_impact(sample_trades) == 2.0
    assert calculate_commission_impact(sample_trades) == 4.0

    # Expectancy R
    assert expectancy_r(sample_trades) == 0.6
    assert expectancy_r([]) == 0.0


def test_trade_adjusted_metrics(sample_trades):
    # Adjusted Profit / Loss
    assert adjusted_gross_profit([]) == 0.0
    assert adjusted_gross_loss([]) == 0.0
    assert adjusted_net_profit([]) == 0.0
    assert select_net_profit([]) == 0.0
    assert select_gross_profit([]) == 0.0
    assert select_gross_loss([]) == 0.0

    assert adjusted_gross_profit(sample_trades) > 0.0
    assert adjusted_gross_loss(sample_trades) < 0.0
    assert adjusted_net_profit(sample_trades) != 0.0

    # Return on account / drawdown ratios
    assert return_on_account(100.0, 10000.0) == 1.0
    assert max_runup(sample_trades) == 100.0
    assert max_runup([]) == 0.0
    assert (
        max_runup_date([{"timestamp": "2026-01-01", "equity": 100.0}])
        == "1970-01-01T00:00:00Z"
    )

    # Subset & periods
    long_trades_list = [t for t in sample_trades if t.get("direction") == "long"]
    assert calculate_analytics_for_subset(long_trades_list)["total_trades"] == 1
    assert calculate_period_analysis(sample_trades) == {"2026-01": 60.0}
    assert calculate_long_short_split(sample_trades) == {
        "long_pnl": 100.0,
        "short_pnl": -40.0,
    }
    assert calculate_session_performance(sample_trades) == {
        "asian": 60.0,
        "london": 0.0,
        "newyork": 0.0,
    }


# --- Equity & Returns ---


def test_returns_and_drawdowns(sample_equity):
    eq_vals = [x["equity"] for x in sample_equity]
    rets = returns_series(eq_vals)
    assert rets == pytest.approx([0.01, -0.00396039603960396])

    l_rets = log_returns_series(eq_vals)
    assert math.isclose(l_rets[0], math.log(1.01))

    dds = drawdown_series(eq_vals)
    assert dds[0] == 0.0
    assert dds[1] == 0.0
    assert dds[2] == (10100.0 - 10060.0) / 10100.0


def test_equity_returns_extended(sample_equity):
    eq_vals = [x["equity"] for x in sample_equity]
    assert total_return_usd(sample_equity) == 60.0
    assert total_return(sample_equity) == 0.6
    assert return_on_initial_capital(sample_equity) == 0.6

    # Returns arrays
    rets_approx = pytest.approx([0.01, -0.00396039603960396])
    assert daily_returns(sample_equity) == rets_approx
    assert weekly_returns(sample_equity) == []
    assert monthly_returns(sample_equity) == []
    assert annual_returns(sample_equity) == []

    # Alignment & benchmark returns
    bench = [10000.0, 10050.0, 10030.0]
    b_rets = benchmark_returns(bench)
    assert b_rets == pytest.approx([0.005, -0.00199004975])

    rel_dds = relative_drawdown_series(eq_vals, bench)
    assert len(rel_dds) == 3

    # Drawdown durations
    assert max_drawdown_duration_from_equity(sample_equity) >= 0.0
    assert max_strategy_drawdown_date(sample_equity) != ""
    assert avg_underwater_drawdown_percent(sample_equity) >= 0.0

    # Aggregators
    metrics_ret = calculate_return_metrics(sample_equity)
    assert metrics_ret["total_return_percent"] == 0.6

    metrics_dd = calculate_drawdown_metrics(sample_equity, request_id="req_test")
    assert metrics_dd["status"] == "success"
    assert metrics_dd["data"]["max_drawdown_percent"] > 0.0

    # Validation errors
    with pytest.raises(ValidationError):
        calculate_equity_metrics(None, request_id=" ")

    err_res = calculate_equity_metrics(None, request_id="req_1")
    assert err_res["status"] == "error"


# --- Drawdown Indices & Ratios ---


def test_drawdown_indices(sample_equity):
    max_dd = max_strategy_drawdown(sample_equity)
    assert max_dd == 40.0

    max_dd_pct = max_strategy_drawdown_percent(sample_equity)
    assert math.isclose(max_dd_pct, 40.0 / 10100.0 * 100.0)

    avg_dd_val = avg_drawdown(sample_equity)
    assert avg_dd_val > 0

    assert ulcer_index(sample_equity) > 0
    assert pain_index(sample_equity) > 0


def test_drawdown_ratios_extended(sample_equity, sample_trades):
    eq_vals = [x["equity"] for x in sample_equity]
    returns = [0.01, -0.005, 0.02, -0.01]

    # Drawdown distributions & properties
    assert max_relative_drawdown_percent(eq_vals, eq_vals) == 0.0
    assert max_drawdown(returns) >= 0.0
    assert drawdown_distribution(sample_equity) != {}

    assert max_drawdown_duration_from_returns(returns) >= 0.0
    assert max_drawdown_duration(sample_equity) >= 0.0
    assert avg_drawdown_duration(sample_equity) >= 0.0
    assert time_to_recovery(sample_equity) == []
    assert recovery_factor(100.0, 50.0) == 2.0

    assert max_close_to_close_drawdown_percent(sample_trades) > 0.0
    assert account_size_required(sample_trades, initial_balance=10000.0) == 10040.0
    assert avg_yearly_max_drawdown(sample_equity) > 0.0

    # Pain & Calmar
    assert pain_ratio(0.10, 5.0) == 0.02
    assert calmar_ratio(0.10, 5.0) == 0.02
    assert fouse_ratio(0.10, 5.0) == 0.02
    assert sterling_ratio(0.10, 5.0) == pytest.approx(0.10 / 15.0)
    assert rina_index(100.0, 5.0, 10.0) == 2.0

    # Net profits vs drawdowns
    assert net_profit_as_percent_of_max_strategy_drawdown(100.0, 50.0) == 200.0
    assert select_net_profit_as_percent_of_max_strategy_drawdown(100.0, 50.0) == 200.0
    assert adjusted_net_profit_as_percent_of_max_strategy_drawdown(100.0, 50.0) == 200.0
    assert return_on_max_strategy_drawdown(0.10, 5.0) == 0.02
    assert return_on_max_close_to_close_drawdown(100.0, 50.0) == 2.0
    assert drawdown_probability(sample_equity, 0.02) >= 0.0


# --- Risk ---


def test_risk_metrics():
    returns = [0.01, -0.005, 0.02, -0.01, 0.005]
    vol = volatility(returns)
    assert vol > 0

    ann_vol = annualized_volatility(returns, periods=252)
    assert ann_vol == vol * math.sqrt(252)

    down_vol = downside_volatility(returns)
    assert down_vol > 0

    var_95 = value_at_risk(returns, 0.95)
    cvar_95 = conditional_var(returns, 0.95)
    assert var_95 >= 0
    assert cvar_95 >= 0


def test_risk_metrics_extended():
    returns = [0.01, -0.005, 0.02, -0.01]

    assert risk_adjusted_efficiency(100.0, 50.0) == 2.0
    assert profit_per_pip_risk([{"profit_loss": 10.0, "mae": -5.0}]) == 2.0
    assert profit_per_pip_risk([]) == 0.0

    assert upside_potential_ratio(returns) >= 0.0
    assert expected_shortfall(returns) >= 0.0
    assert max_nominal_exposure_simple([]) == 0.0
    assert max_gross_exposure([]) == 0.0
    assert exposure_time_ratio([], 24.0) == 0.0
    assert time_weighted_avg_exposure([], 24.0) == 0.0
    assert portfolio_margin_utilization_curve([]) == []

    dummy_trades = [
        {"profit_loss": 10.0, "close_time": "2026-01-01T04:00:00Z"},
        {"profit_loss": -5.0, "close_time": "2026-01-02T04:00:00Z"},
    ]
    assert compounding_risk_of_ruin(dummy_trades, 1000.0, 500.0) >= 0.0

    assert historical_var_by_symbol({"EURUSD": [{"profit_loss": 10.0}]}) == {
        "EURUSD": 10.0
    }
    assert (
        portfolio_var_from_covariance([0.5, 0.5], [[0.01, 0.002], [0.002, 0.015]]) > 0.0
    )

    # calculate tool
    res = calculate_risk_metrics(returns, request_id="req_test")
    assert res["status"] == "success"
    assert res["data"]["volatility"] > 0.0


# --- Ratios ---


def test_ratios():
    returns = [0.01, -0.005, 0.02, -0.01, 0.005]
    sr = sharpe_ratio(returns)
    sortino = sortino_ratio(returns)
    omega = omega_ratio(returns)
    assert isinstance(sr, float)
    assert isinstance(sortino, float)
    assert isinstance(omega, float)


def test_ratios_extended(sample_trades):
    returns = [0.01, -0.005, 0.02, -0.01]
    assert gain_to_pain_ratio(returns) > 0.0
    assert gain_to_pain_ratio([-0.01]) == 0.0
    assert gain_to_pain_ratio([0.01]) == 999.0

    assert kappa_ratio(returns) != 0.0
    assert kappa_ratio([]) == 0.0
    assert payoff_ratio(sample_trades) > 0.0
    assert edge_ratio(sample_trades) != 0.0
    assert profit_to_mae_ratio(sample_trades) > 0.0
    assert mfe_to_mae_ratio(sample_trades) == pytest.approx(150.0 / 70.0)
    assert mfe_to_mae_ratio([]) == 0.0

    assert expectancy_over_std(sample_trades) > 0.0
    assert expectancy_over_std([]) == 0.0
    assert expectancy_over_std([{"trade_id": "t1", "profit_loss": 50.0}]) == 0.0

    assert net_profit_as_percent_of_largest_loss(100.0, -20.0) == 500.0
    assert net_profit_as_percent_of_largest_loss(100.0, 0.0) == 0.0
    assert select_net_profit_as_percent_of_largest_loss(100.0, -20.0) == 500.0
    assert adjusted_net_profit_as_percent_of_largest_loss(100.0, -20.0) == 500.0

    assert adjusted_profit_factor(sample_trades) > 0.0
    assert select_profit_factor(sample_trades) > 0.0

    # calculate tool
    res = calculate_ratio_metrics(returns, request_id="req_test")
    assert res["status"] == "success"
    assert res["data"]["sharpe_ratio"] > 0.0


# --- Distributions ---


def test_distributions():
    returns = [0.01, -0.005, 0.02, -0.01, 0.005]
    skew = skewness(returns)
    kurt = kurtosis(returns)
    jb = jarque_bera_test(returns)
    assert isinstance(skew, float)
    assert isinstance(kurt, float)
    assert "jb_stat" in jb


def test_distributions_extended():
    returns = [0.01, -0.002, 0.025, -0.015, 0.005]

    # Moment/Summary structures
    assert skewness([1.0, 1.0]) == 0.0
    assert kurtosis([1.0, 1.0, 1.0]) == 0.0
    assert higher_moments([]) == {}
    assert percentile_summary([]) == {}

    up_down = upside_downside_summary(returns)
    assert up_down["upside_count"] == 3

    assert fat_tail_score(returns) == kurtosis(returns)
    assert tail_ratio([]) == 0.0
    assert tail_ratio(returns) >= 0.0

    assert jarque_bera_test([1.0, 1.0]) == {"jb_stat": 0.0, "p_value": 1.0}
    assert shapiro_wilk_test([1.0, 1.0]) == {"w_stat": 0.0, "p_value": 1.0}
    assert shapiro_wilk_test(returns)["w_stat"] > 0.0

    assert qq_plot_data([]) == []
    assert len(qq_plot_data(returns)) == 5
    assert qq_plot_data([1.0, 1.0]) != []

    assert fit_distribution([]) == {}
    assert "mean" in fit_distribution(returns)

    assert distribution_fit_quality([]) == {}
    assert "log_likelihood" in distribution_fit_quality(returns)
    assert distribution_fit_quality([1.0, 1.0]) == {"log_likelihood": 0.0, "aic": 0.0}

    # Histogram & Outliers
    assert histogram_data([]) == {"bins": [], "counts": []}
    hist = histogram_data(returns, bins=3)
    assert len(hist["bins"]) == 4

    assert detect_outliers([1.0, 2.0, 3.0]) == []
    assert outlier_ratio([]) == 0.0

    # Bootstrapping & Permutations
    assert bootstrap_confidence_intervals([]) == (0.0, 0.0)
    lower, upper = bootstrap_confidence_intervals(returns, iterations=10)
    assert lower <= upper

    assert whites_reality_check([[0.01], [0.02]], [0.01]) == 0.25
    assert permutation_test([], [1.0]) == 1.0
    assert permutation_test(returns, returns, iterations=10) >= 0.0

    assert deflated_sharpe_ratio(1.5, returns) == 1.35
    assert probability_of_backtest_overfitting([returns]) == 0.15

    # degradation
    degrad = walk_forward_degradation_score(
        {"profit_factor": 2.0}, {"profit_factor": 1.0}
    )
    assert degrad == 0.5
    assert walk_forward_degradation_score({"profit_factor": 0.0}, {}) == 0.0

    # Corrections
    assert bonferroni_correction([0.01, 0.05]) == [0.02, 0.10]
    assert benjamini_hochberg_correction([0.05, 0.01]) == [0.05, 0.02]

    # Stability
    assert stability_score([]) == 0.0
    assert stability_score([{"profit_factor": 1.5}, {"profit_factor": 1.5}]) == 1.0
    assert stability_score([{"profit_factor": 0.0}]) == 0.0

    # Backtest tests
    assert whites_reality_check_backtests([]) == 0.25
    assert permutation_test_backtest({}, {}) == 0.05
    assert bootstrap_confidence_intervals_backtest({}) == (1.2, 1.8)


# --- Benchmark ---


def test_benchmark():
    strat_ret = [0.01, -0.005, 0.02, -0.01, 0.005]
    bench_ret = [0.008, -0.004, 0.015, -0.008, 0.004]

    b_coef = beta(strat_ret, bench_ret)
    a_coef = alpha(strat_ret, bench_ret)
    te = tracking_error(strat_ret, bench_ret)
    ir = information_ratio(strat_ret, bench_ret)

    assert isinstance(b_coef, float)
    assert isinstance(a_coef, float)
    assert isinstance(te, float)
    assert isinstance(ir, float)


def test_benchmark_extended():
    returns = [0.01, -0.005, 0.02, -0.01]
    bench = [0.005, -0.002, 0.01, -0.005]

    assert r_squared([1.0], [1.0]) == 0.0
    assert r_squared([1.0, 1.0], [2.0, 2.0]) == 0.0
    assert r_squared(returns, bench) >= 0.0

    assert batting_average([], [1.0]) == 0.0
    assert batting_average(returns, bench) == 0.5

    # Alignment using pandas series
    s_ser = pd.Series(returns)
    b_ser = pd.Series(bench)
    res_tool = calculate_benchmark_metrics(s_ser, b_ser, request_id="req_test")
    assert res_tool["status"] == "success"
    assert res_tool["data"]["beta"] > 0.0


# --- Efficiency ---


def test_efficiency(sample_trades):
    eff = loss_containment_efficiency(sample_trades)
    assert 0.0 <= eff <= 1.0


def test_efficiency_extended(sample_trades):
    assert capital_efficiency(100.0, 10000.0) == 0.01
    assert return_per_unit_mae(sample_trades) >= 0.0
    assert return_per_calendar_day(100.0, 10) == 10.0
    assert exit_efficiency(sample_trades) >= 0.0


# --- Dashboard overview & Downsampling ---


def test_dashboard(sample_equity):
    # build summary report
    report = {
        "sections": {
            "trade_metrics": {"win_rate": 0.5, "total_trades": 2},
            "ratio_metrics": {"profit_factor": 1.5, "sharpe_ratio": 1.2},
            "drawdown_metrics": {"max_drawdown_percent": 5.0},
            "equity_metrics": {"total_return_usd": 150.0},
        },
        "equity_curve": sample_equity,
        "warnings": [],
        "quality_flags": [],
    }

    # test downsampling curve
    curve_large = [{"timestamp": str(i), "equity": float(i)} for i in range(500)]
    downsampled = _downsample_curve(curve_large, max_points=100)
    assert downsampled["truncated"] is True
    assert downsampled["returned_count"] <= 104

    # test payload builder
    resp = build_overview_payload(report, request_id="req_test")
    assert resp["status"] == "success"
    assert resp["data"]["summary_cards"]["net_profit"] == 150.0
    assert resp["data"]["summary_cards"]["win_rate"] == 0.5


def test_analytics_coverage_expansion(mocker):
    from app.services.analytics.distributions import (
        detect_outliers,
        kurtosis,
        outlier_ratio,
        skewness,
    )
    from app.services.analytics.drawdown import (
        drawdown_probability,
    )
    from app.services.analytics.equity import (
        _parse_equity_curve,
        _to_float_list,
    )
    from app.services.analytics.equity import (
        _parse_time as equity_parse_time,
    )
    from app.services.analytics.risk import (
        calculate_risk_metrics,
        compounding_risk_of_ruin,
        historical_var_by_symbol,
        portfolio_var_from_covariance,
    )
    from app.services.analytics.trade import (
        avg_return_per_risk_unit,
        avg_trade_notional_efficiency,
        calculate_trade_metrics,
        max_close_to_close_drawdown_date,
        max_consecutive_drawdown_trades,
        mfe_efficiency,
        position_size_efficiency,
        profit_per_trade_per_day,
        return_per_market_hour,
        return_per_trade_hour,
        trades_per_day,
    )

    # 1. distributions.py edge cases
    assert skewness([1.0, 1.0, 1.0]) == 0.0
    assert kurtosis([1.0, 1.0, 1.0, 1.0]) == 0.0
    assert detect_outliers([1.0, 2.0, 3.0, 4.0, 100.0]) == [4]
    assert outlier_ratio([1.0, 2.0, 3.0, 4.0, 100.0]) == 0.2
    assert return_distribution([1.0, 2.0, 3.0, 4.0]) is not None
    assert r_multiple_distribution([1.0, 2.0, 3.0, 4.0]) is not None

    # tool checks
    with pytest.raises(ValidationError):
        sample_size_warning(30, request_id=" ")
    assert sample_size_warning(10, min_recommended=30)["data"]["is_weak"] is True
    assert sample_size_warning(50, min_recommended=30)["data"]["is_weak"] is False
    assert sample_size_warning(10, min_recommended=30)["status"] == "success"

    with pytest.raises(ValidationError):
        bootstrap_probability_above_threshold([1.0], request_id=" ")
    assert bootstrap_probability_above_threshold([])["status"] == "error"
    assert (
        bootstrap_probability_above_threshold([1.0, 2.0, 3.0], threshold=1.5)["status"]
        == "success"
    )

    with pytest.raises(ValidationError):
        calculate_distribution_metrics([], request_id=" ")
    assert calculate_distribution_metrics([])["status"] == "error"
    assert calculate_distribution_metrics([1.0, 2.0, 3.0])["status"] == "success"
    # trigger exception in calculate_distribution_metrics
    assert calculate_distribution_metrics("invalid")["status"] == "error"

    # 2. equity.py and drawdown.py edge cases
    assert equity_parse_time(1700000000) is not None
    assert equity_parse_time(1700000000.0) is not None
    assert equity_parse_time("invalid-date-format") is None
    assert equity_parse_time(None) is None

    df = pd.DataFrame([{"timestamp": "2026-01-01T00:00:00Z", "equity": 10000.0}])
    assert len(_parse_equity_curve(df)) == 1
    assert _parse_equity_curve(None) == []
    assert _parse_equity_curve("invalid") == []
    assert len(_parse_equity_curve([["2026-01-01T00:00:00Z", 10000.0]])) == 1

    assert _to_float_list(pd.Series([1.0, 2.0])) == [1.0, 2.0]
    assert _to_float_list(None) == []
    assert _to_float_list("not-a-list") == []

    # mock drawdown_series to return []
    mocker.patch("app.services.analytics.drawdown.drawdown_series", return_value=[])
    assert (
        drawdown_probability([{"timestamp": "2026-01-01", "equity": 10000.0}], 5.0)
        == 0.0
    )

    # 3. risk.py edge cases
    assert compounding_risk_of_ruin([], 1000.0, 500.0) == 0.0
    assert historical_var_by_symbol({"EURUSD": []}) == {"EURUSD": 0.0}
    assert portfolio_var_from_covariance([], []) == 0.0
    assert calculate_risk_metrics([])["status"] == "error"
    assert calculate_risk_metrics("invalid")["status"] == "error"

    # 4. trade.py edge cases
    trades_data = [
        {
            "trade_id": "t1",
            "open_time": "2026-01-01T00:00:00Z",
            "close_time": "2026-01-01T04:00:00Z",
            "direction": "long",
            "profit_loss": 100.0,
            "initial_risk": 50.0,
            "size": 1.0,
            "open_price": 1.1000,
            "commission": 2.0,
        },
        {
            "trade_id": "t2",
            "open_time": "2026-01-02T00:00:00Z",
            "close_time": "2026-01-02T04:00:00Z",
            "direction": "short",
            "profit_loss": -40.0,
            "initial_risk": 50.0,
            "size": 2.0,
            "open_price": 1.1050,
            "commission": 2.0,
        },
    ]

    assert max_consecutive_drawdown_trades([]) == 0
    assert max_consecutive_drawdown_trades(trades_data) >= 0

    assert max_close_to_close_drawdown_date([]) == "1970-01-01T00:00:00Z"
    assert max_close_to_close_drawdown_date(trades_data) != ""

    assert avg_trade_notional_efficiency([]) == 0.0
    assert avg_trade_notional_efficiency(trades_data) > 0.0

    assert avg_return_per_risk_unit([]) == 0.0
    assert avg_return_per_risk_unit(trades_data) != 0.0

    assert return_per_trade_hour([]) == 0.0
    assert return_per_trade_hour(trades_data) != 0.0

    assert return_per_market_hour([]) == 0.0
    assert return_per_market_hour(trades_data) != 0.0

    assert trades_per_day(trades_data, duration_days=0.0) == 0.0
    assert trades_per_day(trades_data, duration_days=5.0) == 0.4

    assert profit_per_trade_per_day(trades_data, duration_days=0.0) == 0.0
    assert profit_per_trade_per_day(trades_data, duration_days=5.0) != 0.0

    assert mfe_efficiency([]) == 1.0
    assert mfe_efficiency(trades_data) > 0.0

    assert position_size_efficiency([]) == 0.0
    assert position_size_efficiency(trades_data) != 0.0

    # calculate_trade_metrics error handling
    assert calculate_trade_metrics([1.0])["status"] == "error"

    # get_analytics_overview filtering
    overview_filtered = get_analytics_overview(
        trades_data,
        start_time="2026-01-01T02:00:00Z",
        end_time="2026-01-01T06:00:00Z",
    )
    assert overview_filtered["status"] == "success"
    assert overview_filtered["data"]["all"]["total_trades"] == 1

    overview_err = get_analytics_overview([1.0])
    assert overview_err["status"] == "error"
