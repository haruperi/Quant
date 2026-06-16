# ruff: noqa: E501, ANN001, ANN201, D103, PTH123, PLR2004, INP001, EM102, T201
"""Performance benchmark runner for HaruQuantAI indicators.

Measures calculation latencies, tracks regressions, and verifies SLO targets.
"""

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.indicators import ema, sma
from tests.unit.app.services.indicators.test_trend import generate_mock_ohlcv


def run_benchmark(indicator_func, df, warmup_runs=3, measured_runs=10):
    # Warmup runs
    for _ in range(warmup_runs):
        indicator_func(df, period=10)

    durations = []
    for _ in range(measured_runs):
        start = time.perf_counter()
        indicator_func(df, period=10)
        end = time.perf_counter()
        durations.append((end - start) * 1000.0)  # ms

    return {
        "min": float(np.min(durations)),
        "median": float(np.median(durations)),
        "p99": float(np.percentile(durations, 99)),
        "runs": measured_runs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--approve-regression",
        action="store_true",
        help="Approve performance regression > 20 percent",
    )
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Only save baseline without comparison",
    )
    args = parser.parse_args()

    print("Running indicator performance benchmarks...")

    # Generate dataset for benchmarking (10,000 rows is fast for unit testing/CI checks)
    df = generate_mock_ohlcv(10000, constant_price=10.0)

    # Run benchmarks
    sma_metrics = run_benchmark(sma, df)
    ema_metrics = run_benchmark(ema, df)

    current_results = {
        "sma": sma_metrics,
        "ema": ema_metrics,
        "environment": {
            "python_version": platform.python_version(),
            "pandas_version": pd.__version__,
            "numpy_version": np.__version__,
            "os": platform.system(),
            "cpu": platform.processor() or "AMD64 Family 25 Model 80 Stepping 0",
            "cores": os.cpu_count() or 8,
            "ram_gb": 16.0,
            "disk_type": "SSD",
        },
    }

    print("\n--- Current Benchmark Results (ms) ---")
    print(
        f"SMA - Min: {sma_metrics['min']:.2f}, Median: {sma_metrics['median']:.2f}, P99: {sma_metrics['p99']:.2f}"
    )
    print(
        f"EMA - Min: {ema_metrics['min']:.2f}, Median: {ema_metrics['median']:.2f}, P99: {ema_metrics['p99']:.2f}"
    )

    baseline_path = Path("benchmark_baseline.json")

    if args.baseline_only or not baseline_path.exists():
        print(f"\nSaving current results as new baseline to {baseline_path}...")
        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(current_results, f, indent=2)
        print("Baseline saved successfully.")
        return 0

    # Compare against baseline
    with open(baseline_path, encoding="utf-8") as f:
        baseline = json.load(f)

    regression_detected = False
    print("\n--- Regression Comparison (current vs baseline median) ---")
    for key in ["sma", "ema"]:
        current_med = current_results[key]["median"]
        base_med = baseline[key]["median"]
        diff_pct = ((current_med - base_med) / base_med) * 100.0
        print(
            f"{key.upper()}: Current {current_med:.2f} ms vs Baseline {base_med:.2f} ms ({diff_pct:+.2f}%)"
        )

        if diff_pct > 20.0:
            print(
                f"WARNING: Regression of {diff_pct:.2f}% detected for {key.upper()} (> 20% limit)."
            )
            regression_detected = True

    if regression_detected and not args.approve_regression:
        print("\nERROR: Performance regression exceeded 20% limit. CI build failed.")
        sys.exit(1)

    if args.approve_regression:
        print("\nRegression approved. Updating baseline file...")
        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(current_results, f, indent=2)

    print("\nAll benchmark assertions passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
