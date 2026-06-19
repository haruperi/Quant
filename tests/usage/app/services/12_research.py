# ruff: noqa: E501, NPY002, E402
"""Usage examples for Research Edge Lab.

Demonstrates data preparation, feature engineering, leakage controls,
edge studies, statistical validation, market structure calibration,
unsupervised analysis, and reporting.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path to support direct execution
project_root = str(Path(__file__).resolve().parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import numpy as np
import pandas as pd
from app.services.research import (
    EdgeLabConfig,
    adapt_signals_by_cluster,
    analyze_cluster_outperformance,
    attach_cluster_labels,
    benjamini_hochberg,
    block_bootstrap_ci,
    build_calibration_grid,
    build_dashboard_summary,
    build_edge_profile_snapshot,
    build_market_regime_feature_frame,
    build_strategy_fit,
    cluster_feature_space,
    detect_swing_points,
    detect_trend_regime,
    detect_volatility_regime,
    enforce_time_split,
    evaluate_calibration_candidates,
    forward_max_adverse_excursion,
    forward_max_favorable_excursion,
    forward_returns,
    holm_bonferroni,
    hurst_exponent,
    log_returns,
    mask_forward_columns,
    permutation_test,
    prepare_research_dataset,
    result_to_markdown,
    result_to_summary,
    run_eds_mean_reversion,
    run_eds_null_baseline,
    run_eds_trend_persistence,
    run_pca,
    save_json,
    save_markdown,
    session_label_for_hour,
    validate_no_lookahead_features,
)
from app.utils.errors import ValidationError


def _generate_synthetic_ohlcv(n_bars: int = 150) -> pd.DataFrame:
    """Helper to generate synthetic OHLCV data."""
    dates = pd.date_range(start="2026-06-01", periods=n_bars, freq="h")
    np.random.seed(42)
    # Generate prices with mean reversion trend
    prices = 1.1000 + np.cumsum(np.random.normal(0, 0.001, n_bars))
    df = pd.DataFrame(
        {
            "open": prices - 0.0005,
            "high": prices + 0.0010,
            "low": prices - 0.0015,
            "close": prices,
            "volume": np.random.randint(100, 1000, n_bars).astype(float),
            "spread": np.random.uniform(0.1, 2.0, n_bars),
        },
        index=dates,
    )
    return df


def example_01_research_config_and_data_prep() -> None:
    """Demonstrate research config validation, data preparation, cleaning, and quality reports."""
    print("\n--- Example 1: Research Config & Data Preparation ---")
    df = _generate_synthetic_ohlcv()
    config = EdgeLabConfig()
    config.cleaning_config.missing_bar_strategy = "forward_fill"

    dataset = prepare_research_dataset(df, config)
    print(f"Data columns: {list(dataset.data.columns)}")
    print(f"Metadata: {dataset.metadata}")
    print(f"Quality report issues count: {len(dataset.quality_report.issues)}")
    print(
        f"Quality report actions applied: {[a.action_type for a in dataset.quality_report.actions]}"
    )


def example_02_feature_engineering() -> None:
    """Demonstrate returns, volatility, range, momentum, Bollinger-style stats, Hurst, pivots, and regimes."""
    print("\n--- Example 2: Feature Engineering ---")
    df = _generate_synthetic_ohlcv()
    close = df["close"]

    # Basic returns
    df["log_returns"] = log_returns(close)

    # Volatility and range
    df["vol_regime"] = detect_volatility_regime(df, window=10)
    df["trend_regime"] = detect_trend_regime(df, fast_window=5, slow_window=15)

    # Hurst exponent
    h_exp = hurst_exponent(close)
    print(f"Estimated Hurst exponent: {h_exp:.4f}")

    # Sessions
    df["session_label"] = [session_label_for_hour(h) for h in df.index.hour]
    print(f"Session distribution:\n{df['session_label'].value_counts()}")


def example_03_leakage_controls() -> None:
    """Demonstrate chronological splits, no-lookahead checks, forward-column masking, and leakage failures."""
    print("\n--- Example 3: Leakage Controls ---")
    df = _generate_synthetic_ohlcv()

    # Append forward/future targets
    df["research_fwd_ret"] = forward_returns(df["close"], 5)
    df["research_mfe"] = forward_max_favorable_excursion(df["close"], df["high"], 5)
    df["research_mae"] = forward_max_adverse_excursion(df["close"], df["low"], 5)

    # Run check
    report = validate_no_lookahead_features(df)
    print(f"Leakage check severity: {report.severity}")
    print(f"Suspected columns: {report.suspected_columns}")

    # Masking columns
    masked = mask_forward_columns(df, report)
    print(
        f"Masked columns present: {[c for c in report.suspected_columns if c in masked.columns]}"
    )

    # Splits
    split = enforce_time_split(masked, 0.6, 0.2, 0.2)
    print(
        f"Chronological split sizes: Train={split.train_records}, Val={split.val_records}, Test={split.test_records}"
    )


def example_04_edge_studies() -> None:
    """Demonstrate mean reversion, trend persistence, session behavior, and null baseline studies."""
    print("\n--- Example 4: Edge Discovery Studies ---")
    df = _generate_synthetic_ohlcv()
    config = EdgeLabConfig()
    dataset = prepare_research_dataset(df, config)

    # Baseline
    baseline = run_eds_null_baseline(dataset, config)
    print(f"Baseline Null expectancy mean: {baseline['mean_null']:.6f}")

    # Studies
    mr_res = run_eds_mean_reversion(dataset, config)
    print(
        f"Mean Reversion Win Rate: {mr_res.stats.win_rate:.2%}, Expectancy: {mr_res.stats.expectancy:.4f}"
    )

    tp_res = run_eds_trend_persistence(dataset, config)
    print(
        f"Trend Breakout Win Rate: {tp_res.stats.win_rate:.2%}, Expectancy: {tp_res.stats.expectancy:.4f}"
    )


def example_05_statistical_validation() -> None:
    """Demonstrate bootstrap, permutation tests, null models, multiple-comparison correction, and thresholds."""
    print("\n--- Example 5: Statistical Validation ---")
    df = _generate_synthetic_ohlcv()
    returns = df["close"].pct_change().dropna().to_numpy()

    # Block Bootstrap
    low, high = block_bootstrap_ci(
        returns, n_iterations=200, block_size=5, confidence_level=0.95
    )
    print(f"95% Block Bootstrap Confidence Interval: [{low:.6f}, {high:.6f}]")

    # Permutation test
    p_val = permutation_test(returns[:50], returns[50:], n_permutations=200)
    print(f"Permutation test p-value: {p_val:.4f}")

    # Multiple comparisons corrections
    p_values = [0.005, 0.02, 0.045, 0.08, 0.12]
    bh_reject = benjamini_hochberg(p_values, alpha=0.05)
    hb_reject = holm_bonferroni(p_values, alpha=0.05)
    print(f"BH Reject array: {bh_reject}")
    print(f"Holm-Bonferroni Reject array: {hb_reject}")


def example_06_market_structure() -> None:
    """Demonstrate market-structure profiles, calibration candidates, overrides, and stability summaries."""
    print("\n--- Example 6: Market Structure Studies ---")
    df = _generate_synthetic_ohlcv()
    swings = detect_swing_points(df, window=3)
    print(f"Detected {len(swings)} swing highs/lows in dataset.")

    # Grid calibration
    grid = build_calibration_grid([3, 5], [0.5, 0.6])
    best_params = evaluate_calibration_candidates(df, grid)
    print(f"Best Calibration Parameter Score: {best_params[0].score}")

    # Strategy fit (advisory)
    fit = build_strategy_fit(df)
    print(f"Advisory Strategy Fit: {fit}")


def example_07_unsupervised_analysis() -> None:
    """Demonstrate PCA, clustering, labels, outperformance analysis, and risk-factor summaries."""
    print("\n--- Example 7: Unsupervised Analysis ---")
    df = _generate_synthetic_ohlcv()
    feature_frame = build_market_regime_feature_frame(df)

    try:
        # PCA
        pca_res = run_pca(feature_frame, n_components=2)
        print(f"PCA Explained Variance: {pca_res['explained_variance']}")

        # K-Means clustering
        cluster_res = cluster_feature_space(feature_frame, n_clusters=3)
        labeled = attach_cluster_labels(feature_frame, cluster_res["labels"])

        # Attach forward returns and score
        labeled["research_forward_returns"] = np.random.normal(0, 0.001, len(labeled))
        cluster_perf = analyze_cluster_outperformance(labeled, cluster_res["labels"])
        for cid, stats in cluster_perf.items():
            print(
                f"Cluster {cid} ({stats['regime_name']}): mean returns={stats['mean_forward_return']:.6f}"
            )

        # Signal adaptation recommendations (advisory)
        adapt = adapt_signals_by_cluster(cluster_perf)
        print(f"Advisory recommendations: {adapt['recommendations']}")
    except ValidationError as exc:
        print(f"Skipping unsupervised analysis example: {exc}")


def example_08_research_reports() -> None:
    """Demonstrate markdown/json reports, profile snapshots, dashboard summaries, and advisory-only boundaries."""
    print("\n--- Example 8: Research Reporting ---")
    df = _generate_synthetic_ohlcv()
    config = EdgeLabConfig()
    dataset = prepare_research_dataset(df, config)
    res = run_eds_mean_reversion(dataset, config)

    # Serialization
    md_content = result_to_markdown(res)
    print(f"MD report length: {len(md_content)}")
    summary = result_to_summary(res)
    print(f"Concise summary dict: {summary}")

    # File persistence to scratch path
    scratch_dir = Path("cache")
    scratch_dir.mkdir(exist_ok=True)
    save_markdown(res, str(scratch_dir / "eds_report.md"), overwrite=True)
    save_json(res, str(scratch_dir / "eds_report.json"), overwrite=True)
    print("Persisted reports to cache directory.")

    # Snapshot and Scorecard
    snapshot = build_edge_profile_snapshot("EURUSD", "H1", [res])
    dashboard = build_dashboard_summary(snapshot)
    print(f"Dashboard summary payload: {dashboard}")


def main() -> None:
    """Run all examples sequentially."""
    print("Running Research Edge Lab usage examples...")
    example_01_research_config_and_data_prep()
    example_02_feature_engineering()
    example_03_leakage_controls()
    example_04_edge_studies()
    example_05_statistical_validation()
    example_06_market_structure()
    example_07_unsupervised_analysis()
    example_08_research_reports()
    print("\nAll usage examples completed successfully.")


if __name__ == "__main__":
    main()
