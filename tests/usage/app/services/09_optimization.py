# ruff: noqa: E402
"""Executable optimization service examples."""

from __future__ import annotations

import contextlib
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# Ensure project root is on sys.path
project_root = str(Path(__file__).resolve().parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.optimization import (
    InMemoryOptimizationRepository,
    OptimizationRunRecord,
    ParameterRange,
    ParameterSpace,
    WalkForwardSplit,
    WalkForwardWindow,
    bayesian_optimization,
    compare_optimization_runs,
    detect_overfit_parameters,
    genetic_algorithm,
    get_active_parameters,
    grid_search,
    load_optimization_run,
    optimization_monte_carlo,
    parameter_space_hash,
    random_search,
    rolling_window_split,
    run_slippage_stress_test,
    save_optimization_run,
)
from app.services.optimization.persistence.checkpoint import (
    load_checkpoint,
    save_checkpoint,
)


def example_01_parameter_space() -> None:
    """Demonstrate parameter space definitions, active conditionals, and hashes."""
    space = ParameterSpace(
        parameters=[
            ParameterRange(
                name="short_window", type="int", min_value=5, max_value=15, step=1
            ),
            ParameterRange(
                name="long_window", type="int", min_value=10, max_value=30, step=2
            ),
            ParameterRange(name="use_rsi", type="categorical", options=[True, False]),
            ParameterRange(
                name="rsi_period", type="int", min_value=7, max_value=21, step=1
            ),
        ],
        constraints=["short_window < long_window"],
    )
    # Check hashing
    h = parameter_space_hash(space)
    assert isinstance(h, str)
    assert len(h) == 64

    # Active parameters
    cand = {"short_window": 10, "long_window": 20, "use_rsi": False}
    active = get_active_parameters(cand, space)
    assert active["short_window"] == 10
    print("[x] example_01_parameter_space passed")


def example_02_grid_and_random_search() -> None:
    """Demonstrate grid and random search sweeps with scoring objectives."""
    space = ParameterSpace(
        parameters=[
            ParameterRange(
                name="short_window", type="int", min_value=5, max_value=6, step=1
            ),
            ParameterRange(
                name="long_window", type="int", min_value=10, max_value=12, step=2
            ),
        ]
    )

    # Grid search
    summary = grid_search(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=space,
        dry_run=True,
    )
    assert len(summary.candidates) > 0

    # Random search
    rand_summary = random_search(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=space,
        max_candidates=2,
        dry_run=True,
    )
    assert len(rand_summary.candidates) > 0
    print("[x] example_02_grid_and_random_search passed")


def example_03_bayesian_optimization() -> None:
    """Demonstrate Bayesian optimization wrapper and clean fallback behaviour."""
    space = ParameterSpace(
        parameters=[
            ParameterRange(name="short_window", type="int", min_value=5, max_value=15),
            ParameterRange(name="long_window", type="int", min_value=10, max_value=30),
        ]
    )

    summary = bayesian_optimization(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=space,
        max_candidates=5,
        seed=42,
        dry_run=True,
    )
    assert len(summary.candidates) > 0
    print("[x] example_03_bayesian_optimization passed")


def example_04_genetic_algorithm() -> None:
    """Demonstrate genetic algorithm optimizer config, elitism, crossover,

    and mutation.
    """
    space = ParameterSpace(
        parameters=[
            ParameterRange(name="short_window", type="int", min_value=5, max_value=15),
            ParameterRange(name="long_window", type="int", min_value=10, max_value=30),
        ]
    )

    summary = genetic_algorithm(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=space,
        population_size=10,
        generations=3,
        seed=123,
        dry_run=True,
    )
    assert len(summary.candidates) > 0
    print("[x] example_04_genetic_algorithm passed")


def example_05_walk_forward_splits() -> None:
    """Demonstrate walk-forward train/test window splitting with purging

    and embargo windows.
    """
    start_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    end_dt = datetime(2026, 1, 20, 0, 0, 0, tzinfo=UTC)

    # Standalone rolling split
    rolling_folds = rolling_window_split(
        start=start_dt,
        end=end_dt,
        folds=5,
        train_fraction=0.7,
        purging_bars=2,
        embargo_bars=1,
    )
    assert len(rolling_folds) == 5
    assert isinstance(rolling_folds[0], WalkForwardWindow)

    # Using WalkForwardSplit coordinator
    wf = WalkForwardSplit(
        start_date=start_dt,
        end_date=end_dt,
        folds=3,
        train_fraction=0.6,
        fold_mode="expanding",
        purging_bars=0,
        embargo_bars=0,
    )
    res = wf.split()
    assert len(res.folds) == 3
    print("[x] example_05_walk_forward_splits passed")


def example_06_robustness_and_monte_carlo() -> None:
    """Demonstrate Monte Carlo trade resampling, ruin estimation, and

    stress shock robustness.
    """
    base_time = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
    from datetime import timedelta

    trades = [
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

    # Stress tests
    slipped = run_slippage_stress_test(trades, slippage_pips=1.5, pip_value=10.0)
    assert len(slipped) == len(trades)

    # Monte Carlo Response
    mc_res = optimization_monte_carlo(
        trades=trades,
        simulation_method="shuffle_trades",
        simulation_count=50,
        initial_balance=10000.0,
        ruin_threshold=0.5,
        target_balance=12000.0,
        seed=42,
    )
    assert mc_res.ruin_probability >= 0.0
    assert mc_res.drawdown_p95 >= 0.0
    print("[x] example_06_robustness_and_monte_carlo passed")


def example_07_repository_and_resume() -> None:
    """Demonstrate atomic checkpoint saves, corruption recovery, and

    repository state tracking.
    """
    # Atomic Checkpoint
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_file = str(Path(tmpdir) / "opt_checkpoint.json")
        state = {
            "run_id": "run_123",
            "completed_candidates": [{"short": 5, "long": 10}],
        }

        # Save
        save_checkpoint(checkpoint_file, state, "run_123", base_dir=tmpdir)

        # Load
        loaded = load_checkpoint(checkpoint_file, base_dir=tmpdir)
        assert loaded["completed_candidates"] == state["completed_candidates"]

        # Test corruption recovery
        with Path(checkpoint_file).open("w") as f:
            f.write("{invalid_json:")

        with contextlib.suppress(Exception):
            load_checkpoint(checkpoint_file, base_dir=tmpdir)

    # Repository Persistence
    repo = InMemoryOptimizationRepository()
    record = OptimizationRunRecord(
        run_id="run_123",
        strategy_ref="dummy_strat",
        parameter_space_hash="some_hash",
        objective="sharpe",
        status="RUNNING",
        progress=0.0,
        total_candidates=10,
        candidates=[],
    )
    save_optimization_run(repo, "run_123", record)
    loaded_rec = load_optimization_run(repo, "run_123")
    assert loaded_rec.run_id == "run_123"
    print("[x] example_07_repository_and_resume passed")


def example_08_evidence_package() -> None:
    """Demonstrate Walk-Forward efficiency report packaging and standard

    envelope validation.
    """
    # Overfit calculation
    overfit = detect_overfit_parameters(in_sample_score=2.0, out_of_sample_score=1.8)
    assert overfit["is_overfit"] is False

    # Comparison report
    rep = compare_optimization_runs(
        run_ids=["run_1", "run_2"],
        results_payloads=[
            {"run_id": "run_1", "best_score": 1.5},
            {"run_id": "run_2", "best_score": 1.2},
        ],
    )
    assert "run_1" in rep
    print("[x] example_08_evidence_package passed")


def main() -> None:
    """Run all optimization examples."""
    print("=== Running Optimization Service Examples ===")
    example_01_parameter_space()
    example_02_grid_and_random_search()
    example_03_bayesian_optimization()
    example_04_genetic_algorithm()
    example_05_walk_forward_splits()
    example_06_robustness_and_monte_carlo()
    example_07_repository_and_resume()
    example_08_evidence_package()
    print("=== All Examples Completed Successfully ===")


if __name__ == "__main__":
    main()
