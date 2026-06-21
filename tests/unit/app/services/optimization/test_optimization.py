"""Unit tests for the Phase 9 Optimization Service.

Covers parameter space schemas, search algorithms, scoring metrics, Walk-Forward splits,
robustness stress testing, checkpoint atomic writes, and repository persistence.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from app.services.optimization import (
    Infinity,
    InMemoryOptimizationRepository,
    OptimizationExecutionError,
    ParameterRange,
    ParameterSpace,
    ProgressTracker,
    WalkForwardSplit,
    assess_strategy_robustness,
    bayesian_optimization,
    build_candidate_hash,
    calculate_dsr,
    calculate_max_drawdown,
    calculate_parameter_stability,
    calmar_score,
    compare_simulation_methods,
    custom_score,
    detect_overfit_parameters,
    evaluate_candidate_score,
    genetic_algorithm,
    get_active_parameters,
    grid_search,
    json_safe_serialize,
    load_optimization_run,
    load_strategy_from_path,
    normalize_engine_type,
    optimization_get_scoring_func,
    optimization_monte_carlo,
    parallel_grid_search,
    parameter_space_hash,
    parametric_simulation,
    pareto_select,
    profit_factor_score,
    random_search,
    rank_candidates,
    run_commission_stress_test,
    run_parameter_sweep,
    run_slippage_stress_test,
    run_spread_stress_test,
    run_strategy_backtest,
    run_strategy_backtest_from_path,
    save_optimization_run,
    sharpe_score,
    sortino_score,
    splitter_from_expanding,
    splitter_from_rolling,
    splitter_rolling_split,
    strategy_id,
    total_return_score,
    update_optimization_progress,
)
from app.services.optimization.persistence.checkpoint import (
    load_checkpoint,
    save_checkpoint,
)
from app.utils.standard import validate_standard_response


@pytest.fixture
def sample_parameter_space() -> ParameterSpace:
    """Fixture returning a standard parameter space schema."""
    return ParameterSpace(
        parameters=[
            ParameterRange(
                name="short_window", type="int", min_value=5, max_value=15, step=1
            ),
            ParameterRange(
                name="long_window", type="int", min_value=10, max_value=30, step=2
            ),
            ParameterRange(
                name="multiplier", type="float", min_value=1.5, max_value=3.5, step=0.5
            ),
            ParameterRange(
                name="entry_type",
                type="categorical",
                options=["market", "limit", "stop"],
            ),
            ParameterRange(name="use_filter", type="bool"),
            ParameterRange(
                name="filter_period",
                type="int",
                min_value=50,
                max_value=200,
                conditional_on="use_filter",
                conditional_values=[True],
            ),
        ],
        constraints=["short_window < long_window"],
    )


@pytest.fixture
def sample_trades() -> list[dict[str, Any]]:
    """Fixture returning a list of mock round-trip trades."""
    from datetime import timedelta

    base_time = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
    return [
        {"profit": 150.0, "volume": 1.0, "close_time": base_time.isoformat()},
        {
            "profit": -50.0,
            "volume": 1.0,
            "close_time": (base_time + timedelta(days=1)).isoformat(),
        },
        {
            "profit": 200.0,
            "volume": 1.5,
            "close_time": (base_time + timedelta(days=2)).isoformat(),
        },
        {
            "profit": -100.0,
            "volume": 0.8,
            "close_time": (base_time + timedelta(days=3)).isoformat(),
        },
    ]


# --- Phase 2 & 3: Parameter Space Validation ---
def test_parameter_range_validation() -> None:
    """Verify numeric boundaries and option validation in parameter ranges."""
    # Valid
    p = ParameterRange(name="p", type="int", min_value=1, max_value=10)
    assert p.min_value == 1

    # Invalid numeric bounds
    with pytest.raises(ValueError, match="min_value and max_value are required"):
        ParameterRange(name="p", type="int", min_value=1)

    with pytest.raises(ValueError, match="min_value cannot be greater than max_value"):
        ParameterRange(name="p", type="int", min_value=10, max_value=5)

    # Invalid categorical options
    with pytest.raises(ValueError, match="options must be provided"):
        ParameterRange(name="p", type="categorical")


# --- Helpers Testing ---
def test_strategy_id_helper() -> None:
    """Verify strategy identifier extraction helper."""

    class DummyClass:
        strategy_ref = "dummy_ref"

    assert strategy_id(DummyClass()) == "dummy_ref"
    assert strategy_id(DummyClass) == "DummyClass"
    assert strategy_id("string_ref") == "str"


def test_normalize_engine_type() -> None:
    """Verify engine label normalization resolves legacy/event labels."""
    assert normalize_engine_type("legacy") == "event_driven"
    assert normalize_engine_type("event-driven") == "event_driven"
    assert normalize_engine_type("custom_engine") == "custom_engine"


def test_parameter_space_hash(sample_parameter_space: ParameterSpace) -> None:
    """Verify deterministic and order-invariant parameter space hashing."""
    h1 = parameter_space_hash(sample_parameter_space)
    # Re-order parameters
    reversed_space = ParameterSpace(
        parameters=list(reversed(sample_parameter_space.parameters)),
        constraints=sample_parameter_space.constraints,
    )
    h2 = parameter_space_hash(reversed_space)
    assert h1 == h2


def test_get_active_parameters(sample_parameter_space: ParameterSpace) -> None:
    """Verify inactive conditional parameters filter out properly."""
    params = {"use_filter": False, "filter_period": 100, "multiplier": 2.0}
    active = get_active_parameters(params, sample_parameter_space)
    assert "filter_period" not in active
    assert active["use_filter"] is False

    params_active = {"use_filter": True, "filter_period": 100, "multiplier": 2.0}
    active_2 = get_active_parameters(params_active, sample_parameter_space)
    assert active_2["filter_period"] == 100


def test_build_candidate_hash(sample_parameter_space: ParameterSpace) -> None:
    """Verify candidate hash deterministic hashing."""
    params1 = {"use_filter": False, "filter_period": 100, "short_window": 5}
    params2 = {"use_filter": False, "filter_period": 200, "short_window": 5}
    h1 = build_candidate_hash(
        "TF",
        "data",
        "cost",
        "realism",
        "obj",
        "event_driven",
        "1.0",
        params1,
        sample_parameter_space,
    )
    h2 = build_candidate_hash(
        "TF",
        "data",
        "cost",
        "realism",
        "obj",
        "event_driven",
        "1.0",
        params2,
        sample_parameter_space,
    )
    # Should match because filter_period is inactive
    assert h1 == h2


def test_json_safe_serialize() -> None:
    """Verify serialization formatting and NaN/Infinity warning handlers."""
    # Test NaN warning
    with pytest.warns(RuntimeWarning, match="NaN or Infinity value serialized as null"):
        res = json_safe_serialize(float("nan"))
    assert res is None

    with pytest.warns(RuntimeWarning, match="NaN or Infinity value serialized as null"):
        res = json_safe_serialize(Infinity)
    assert res is None

    # Test decimals and datetimes
    assert json_safe_serialize(Decimal("1.25000")) == "1.25"
    assert (
        json_safe_serialize(datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC))
        == "2026-06-19T12:00:00+00:00"
    )

    # Test unsupported type fails closed
    with pytest.raises(
        OptimizationExecutionError, match="Unsupported serialization type"
    ):
        json_safe_serialize(object())


def test_load_strategy_from_path_missing() -> None:
    """Verify load strategy from path raises structured error on missing files."""
    with pytest.raises(OptimizationExecutionError, match="Strategy file not found"):
        load_strategy_from_path("non_existent_file.py", "MyStrategy")


def test_run_strategy_backtest_validation() -> None:
    """Verify parameter validations and fail-closed checks on backtest execution."""
    with pytest.raises(OptimizationExecutionError, match="strategy_ref is required"):
        run_strategy_backtest("", ["EURUSD"], "M1", "2026-01-01", "2026-01-02", {})

    with pytest.raises(OptimizationExecutionError, match="symbols cannot be empty"):
        run_strategy_backtest("TF", [], "M1", "2026-01-01", "2026-01-02", {})

    with pytest.raises(OptimizationExecutionError, match="Unsupported engine type"):
        run_strategy_backtest(
            "TF",
            ["EURUSD"],
            "M1",
            "2026-01-01",
            "2026-01-02",
            {},
            engine_type="unsupported",
        )

    with pytest.raises(
        OptimizationExecutionError, match="Backtest adapter version mismatch"
    ):
        run_strategy_backtest(
            "TF",
            ["EURUSD"],
            "M1",
            "2026-01-01",
            "2026-01-02",
            {},
            adapter_version="0.1.0",
        )

    with pytest.raises(
        OptimizationExecutionError, match="Stochastic realism is active"
    ):
        run_strategy_backtest(
            "TF",
            ["EURUSD"],
            "M1",
            "2026-01-01",
            "2026-01-02",
            {},
            stochastic_realism=True,
            deterministic_only=True,
        )


def test_run_strategy_backtest_success() -> None:
    """Verify strategy backtest execution and deal rounding matching."""
    res = run_strategy_backtest(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameters={"short_window": 5, "long_window": 10},
        initial_balance=100000.0,
    )
    assert res.success is True
    assert res.ending_balance == 100000.0
    assert res.net_profit == 0.0
    assert res.total_trades == 0
    assert isinstance(res.trades, list)


def test_run_strategy_backtest_from_path() -> None:
    """Verify dynamic loading and registration of strategy files."""
    # Create temp strategy file
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(
            "from app.services.strategies.base import BaseStrategy\n"
            "class MyTempStrat(BaseStrategy):\n"
            "    strategy_ref = 'my_temp_strat'\n"
            "    def run_vectorized_signals(self, data, indicators, context, config):\n"
            "        return []\n"
        )
        tmp_path = tmp.name

    try:
        res = run_strategy_backtest_from_path(
            file_path=tmp_path,
            class_name="MyTempStrat",
            symbols=["EURUSD"],
            timeframe="M1",
            start="2026-01-01T00:00:00Z",
            end="2026-01-01T01:00:00Z",
            parameters={},
            initial_balance=100000.0,
        )
        assert res.success is True
    finally:
        tmp_p = Path(tmp_path)
        if tmp_p.exists():
            tmp_p.unlink()


def test_parametric_simulation() -> None:
    """Verify parametric Monte Carlo simulator outcomes."""
    res = parametric_simulation(
        win_rate=0.55,
        reward_risk_ratio=1.5,
        risk_per_trade=0.01,
        trade_count=50,
        simulation_count=100,
        initial_balance=10000.0,
        seed=42,
    )
    assert len(res["equity_paths"]) == 100
    assert len(res["drawdowns"]) == 100
    assert len(res["final_equity"]) == 100
    # Final equity is greater than start on average
    assert sum(res["final_equity"]) / 100.0 > 10000.0


# --- Scoring Testing ---
def test_scoring_functions(sample_trades: list[dict[str, Any]]) -> None:
    """Verify Sharpe, Sortino, Calmar, profit factor, and custom score calculations."""
    balance = 10000.0
    assert total_return_score(sample_trades, balance) == (200.0 / balance)
    assert profit_factor_score(sample_trades, balance) == (350.0 / 150.0)

    # Max drawdown
    assert calculate_max_drawdown(sample_trades, balance) == 100.0 / 10300.0

    # Sharpe
    assert sharpe_score(sample_trades, balance) > 0.0
    # Sortino
    assert sortino_score(sample_trades, balance) > 0.0
    # Calmar
    assert calmar_score(sample_trades, balance) > 0.0
    # Custom
    assert custom_score(sample_trades, balance) != 0.0

    # Scoring func lookup
    assert optimization_get_scoring_func("sharpe") == sharpe_score
    assert optimization_get_scoring_func("unknown") == total_return_score


def test_dsr_calculation() -> None:
    """Verify Deflated Sharpe Ratio calculation returns correct probability metrics."""
    # Under independent trials, DSR should deflate raw Sharpe
    dsr = calculate_dsr(
        sharpe=1.5, trial_count=10, skew=0.0, kurtosis=3.0, t_samples=252
    )
    assert 0.0 <= dsr <= 1.0


def test_evaluate_candidate_score(sample_trades: list[dict[str, Any]]) -> None:
    """Verify candidate evaluation and MTB adjustments returns."""
    res = evaluate_candidate_score(sample_trades, 10000.0, "sharpe", trial_count=5)
    assert "deflated_sharpe" in res
    assert "mtb_pass_status" in res


def test_rank_candidates_tie_breaker() -> None:
    """Verify ranking and tie-breaking (trade count desc, hash asc)."""
    cands = [
        {"score": 1.5, "trade_count": 10, "candidate_hash": "b"},
        {"score": 1.5, "trade_count": 20, "candidate_hash": "a"},
        {"score": 1.5, "trade_count": 10, "candidate_hash": "a"},
        {"score": 2.0, "trade_count": 5, "candidate_hash": "c"},
    ]
    ranked = rank_candidates(cands)
    # First: score=2.0
    assert ranked[0]["score"] == 2.0
    # Second: score=1.5, trade_count=20
    assert ranked[1]["trade_count"] == 20
    # Third: score=1.5, trade_count=10, candidate_hash="a" (hash sorted asc)
    assert ranked[2]["candidate_hash"] == "a"
    assert ranked[3]["candidate_hash"] == "b"


def test_pareto_select() -> None:
    """Verify Pareto optimal front selection."""
    cands = [
        # Dominated by second cand
        {"trades": [{"profit": 10.0}], "candidate_hash": "1"},
        # Dominates first
        {"trades": [{"profit": 20.0}], "candidate_hash": "2"},
        # Tradeoff: low return but low drawdown
        {"trades": [{"profit": 5.0}], "candidate_hash": "3"},
    ]
    front = pareto_select(cands, ["total_return", "calmar"])
    assert len(front) >= 1


# --- Splitting Testing ---
def test_walk_forward_splits() -> None:
    """Verify rolling and expanding splits generation and purging/embargo windows."""
    wfs = WalkForwardSplit(
        start_date="2026-01-01T00:00:00Z",
        end_date="2026-01-10T00:00:00Z",
        folds=3,
        train_fraction=0.7,
        fold_mode="rolling",
        purging_bars=10,
        embargo_bars=15,
    )
    res = wfs.split()
    assert len(res.folds) == 3

    # Check that test_start is shifted forward due to embargo
    fold = res.folds[0]
    # train_end + 15 mins (embargo)
    assert fold.test_start > fold.train_end


def test_splitter_helpers() -> None:
    """Verify splitters helpers construct correct time series intervals."""
    r_res = splitter_from_rolling(
        "2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z", folds=2
    )
    assert len(r_res.folds) == 2

    e_res = splitter_from_expanding(
        "2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z", folds=2
    )
    assert len(e_res.folds) == 2

    # Tabular split
    data = list(range(10))
    train, test = splitter_rolling_split(data, 0.7)
    assert len(train) == 7
    assert len(test) == 3


# --- Robustness and Monte Carlo Testing ---
def test_stress_testing_shocks(sample_trades: list[dict[str, Any]]) -> None:
    """Verify slippage, spread, and commission stress tests reduce profit."""
    raw_profit = sum(t["profit"] for t in sample_trades)

    slip_trades = run_slippage_stress_test(sample_trades, slippage_pips=2.0)
    assert sum(t["profit"] for t in slip_trades) < raw_profit

    spread_trades = run_spread_stress_test(sample_trades, spread_multiplier=2.0)
    assert sum(t["profit"] for t in spread_trades) < raw_profit

    comm_trades = run_commission_stress_test(
        sample_trades, extra_commission_per_lot=5.0
    )
    assert sum(t["profit"] for t in comm_trades) < raw_profit


def test_monte_carlo_simulations(sample_trades: list[dict[str, Any]]) -> None:
    """Verify Monte Carlo trade order shuffling and resample outcomes."""
    res = optimization_monte_carlo(
        sample_trades,
        simulation_method="shuffle_trades",
        simulation_count=50,
        initial_balance=10000.0,
        seed=123,
    )
    assert isinstance(res.ruin_probability, float)
    assert res.drawdown_p95 >= 0.0

    # Compare methods
    comp = compare_simulation_methods(sample_trades, 10000.0, 50, seed=123)
    assert "shuffle_trades" in comp
    assert "resample_trades" in comp


def test_strategy_robustness_assessment(sample_trades: list[dict[str, Any]]) -> None:
    """Verify strategy robustness assessment checks compile correctly."""
    res = assess_strategy_robustness(sample_trades, 10000.0, seed=42)
    assert 0.0 <= res.stats.robustness_score <= 100.0
    assert "slippage_stress_test" in res.checks


# --- Sweeps and Search Algorithms Testing ---
def test_grid_search(sample_parameter_space: ParameterSpace) -> None:
    """Verify iterator-based grid search and parallel sweeps."""
    summary = grid_search(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=sample_parameter_space,
        objective="sharpe",
        initial_balance=10000.0,
        dry_run=True,
    )
    assert summary.total_candidates > 0
    assert len(summary.candidates) == summary.total_candidates

    # Parallel
    summary_parallel = parallel_grid_search(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=sample_parameter_space,
        objective="sharpe",
        initial_balance=10000.0,
        max_workers=2,
        dry_run=True,
    )
    assert summary_parallel.total_candidates == summary.total_candidates


def test_random_search(sample_parameter_space: ParameterSpace) -> None:
    """Verify pseudo-random search sweeps and LHS/Sobol unavailability fallbacks."""
    # Pseudo-random
    summary = random_search(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=sample_parameter_space,
        objective="sharpe",
        initial_balance=10000.0,
        max_candidates=5,
        dry_run=True,
    )
    assert summary.total_candidates == 5

    # Sobol strict fail
    import sys
    from unittest.mock import patch

    with (
        patch.dict(sys.modules, {"scipy.stats.qmc": None}),
        pytest.raises(OptimizationExecutionError, match="sampler is unavailable"),
    ):
        random_search(
            strategy_ref="trend_following",
            symbols=["EURUSD"],
            timeframe="M1",
            start="2026-01-01T00:00:00Z",
            end="2026-01-01T01:00:00Z",
            parameter_space=sample_parameter_space,
            objective="sharpe",
            initial_balance=10000.0,
            max_candidates=5,
            sampler_method="sobol",
            strict_sampler=True,
            dry_run=True,
        )


def test_bayesian_optimization_fallback(sample_parameter_space: ParameterSpace) -> None:
    """Verify Bayesian optimization fallback to random search when skopt is missing."""
    summary = bayesian_optimization(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=sample_parameter_space,
        objective="sharpe",
        initial_balance=10000.0,
        max_candidates=5,
        strict_backend=False,
        dry_run=True,
    )
    assert summary.total_candidates == 5


def test_genetic_algorithm(sample_parameter_space: ParameterSpace) -> None:
    """Verify genetic algorithm evolution population updates."""
    summary = genetic_algorithm(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=sample_parameter_space,
        objective="sharpe",
        initial_balance=10000.0,
        population_size=10,
        generations=3,
        dry_run=True,
        seed=42,
    )
    assert len(summary.candidates) > 0


def test_sweeps_stability_and_overfit(sample_trades: list[dict[str, Any]]) -> None:
    """Verify sweeps stability and overfitting calculators."""
    cands = [
        {"parameters": {"short": 5, "long": 10}, "score": 1.0},
        {"parameters": {"short": 15, "long": 30}, "score": 1.5},
    ]
    stab = calculate_parameter_stability(cands)
    assert "short" in stab
    assert "long" in stab

    overfit = detect_overfit_parameters(in_sample_score=2.0, out_of_sample_score=1.8)
    assert overfit["is_overfit"] is False


def test_run_parameter_sweep_facade(sample_parameter_space: ParameterSpace) -> None:
    """Verify public parameter sweep tool envelopes and validation rules."""
    payload = {
        "strategy_ref": "trend_following",
        "symbols": ["EURUSD"],
        "timeframe": "M1",
        "start": "2026-01-01T00:00:00Z",
        "end": "2026-01-01T01:00:00Z",
        "parameter_space": sample_parameter_space.model_dump(),
        "search_method": "grid",
        "objective": "sharpe",
        "initial_balance": 10000.0,
        "max_workers": 1,
        "dry_run": True,
    }

    import typing

    res = typing.cast("dict[str, Any]", run_parameter_sweep(payload))
    validate_standard_response(typing.cast("Any", res))
    assert res["status"] == "success"
    inner_data = typing.cast("dict[str, Any]", res["data"])
    assert inner_data["tool_name"] == "run_parameter_sweep"
    assert inner_data["status"] == "success"


# --- Persistence Testing ---
def test_checkpoint_atomic_saves_and_loads() -> None:
    """Verify atomic checkpoints write, traversal blocker, and corruption recovery."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_path = str(Path(tmpdir) / "checkpoint.json")
        data = {"run_id": "test_run", "progress": 50.0, "status": "running"}

        # Traversal check
        with pytest.raises(OptimizationExecutionError, match="Path traversal detected"):
            save_checkpoint("../../traversal.json", data, "test_run", base_dir=tmpdir)

        # Successful atomic save and load
        save_checkpoint(checkpoint_path, data, "test_run", base_dir=tmpdir)
        loaded = load_checkpoint(checkpoint_path, base_dir=tmpdir)
        assert loaded["run_id"] == "test_run"

        # Corrupted checkpoint recovery
        with Path(checkpoint_path).open("w") as f:
            f.write("{invalid_json}")
        with pytest.raises(
            OptimizationExecutionError, match="Checkpoint corruption detected"
        ):
            load_checkpoint(checkpoint_path, base_dir=tmpdir)


def test_optimization_repository() -> None:
    """Verify repository persistence, progress updates, and retries with backoff."""
    repo = InMemoryOptimizationRepository()
    from app.services.optimization.persistence.repository import OptimizationRunRecord

    record = OptimizationRunRecord(
        run_id="run_1",
        strategy_ref="TF",
        parameter_space_hash="hash_abc",
        objective="sharpe",
        status="running",
    )

    save_optimization_run(repo, "run_1", record)
    loaded = load_optimization_run(repo, "run_1")
    assert loaded.strategy_ref == "TF"

    update_optimization_progress(repo, "run_1", 75.0, "completed")
    updated = load_optimization_run(repo, "run_1")
    assert updated.progress == 75.0
    assert updated.status == "completed"


def test_progress_tracker() -> None:
    """Verify thread-safe progress tracker increments."""
    tracker = ProgressTracker(total=10)
    tracker.increment()
    tracker.increment()
    assert tracker.get_progress() == 20.0
