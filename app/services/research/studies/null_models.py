# ruff: noqa: E501, PLR2004
"""Null models, resampling, and hypothesis testing for Research Edge Lab.

Provides block bootstrap, permutation tests, multiple comparisons correction,
and null distribution generators.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_null_percentile(
    observed: float, null_distribution: list[float] | np.ndarray
) -> float:
    """Compute the percentile of an observed value within a null distribution."""
    arr = np.asarray(null_distribution)
    if len(arr) == 0:
        return 50.0
    return float((arr <= observed).mean() * 100.0)


def compare_to_null(
    observed: float, null_distribution: list[float] | np.ndarray
) -> dict[str, Any]:
    """Compare observed expectancy or performance against a null distribution."""
    arr = np.asarray(null_distribution)
    p_val = float((arr >= observed).mean())
    pct = compute_null_percentile(observed, arr)
    return {
        "observed": observed,
        "null_mean": float(np.mean(arr)),
        "null_std": float(np.std(arr)),
        "p_value": p_val,
        "percentile": pct,
        "significant": p_val < 0.05,
    }


def get_acceptance_criteria(
    null_distribution: list[float] | np.ndarray,
    alpha: float = 0.05,
) -> dict[str, float]:
    """Extract acceptance criteria from a null baseline."""
    arr = np.asarray(null_distribution)
    return {
        "critical_value_high": float(np.percentile(arr, (1.0 - alpha) * 100.0)),
        "critical_value_low": float(np.percentile(arr, alpha * 100.0)),
    }


def block_bootstrap_distribution(
    data: np.ndarray | pd.Series,
    n_iterations: int = 1000,
    block_size: int = 10,
    seed: int | None = None,
) -> np.ndarray:
    """Generate a bootstrap distribution for a statistic (default: mean) using block bootstrap resampling."""
    arr = np.asarray(data)
    n = len(arr)
    if n < block_size or block_size <= 0:
        return np.zeros(n_iterations)

    rng = np.random.default_rng(seed)
    # Determine the number of blocks to sample
    num_blocks = int(np.ceil(n / block_size))
    bootstrap_stats = np.zeros(n_iterations)

    for i in range(n_iterations):
        # Choose starting indices for blocks
        start_indices = rng.integers(0, n - block_size + 1, size=num_blocks)
        sample = np.concatenate([arr[idx : idx + block_size] for idx in start_indices])
        # Trim to original length
        sample = sample[:n]
        bootstrap_stats[i] = np.mean(sample)

    return bootstrap_stats


def block_bootstrap_ci(
    data: np.ndarray | pd.Series,
    n_iterations: int = 1000,
    block_size: int = 10,
    confidence_level: float = 0.95,
    seed: int | None = None,
) -> tuple[float, float]:
    """Compute a confidence interval using block bootstrap resampling."""
    dist = block_bootstrap_distribution(data, n_iterations, block_size, seed)
    alpha = 1.0 - confidence_level
    low = float(np.percentile(dist, (alpha / 2.0) * 100.0))
    high = float(np.percentile(dist, (1.0 - alpha / 2.0) * 100.0))
    return low, high


def permutation_test(
    group1: np.ndarray | pd.Series,
    group2: np.ndarray | pd.Series,
    n_permutations: int = 1000,
    seed: int | None = None,
) -> float:
    """Compute a permutation-test p-value."""
    arr1 = np.asarray(group1)
    arr2 = np.asarray(group2)
    obs_diff = np.mean(arr1) - np.mean(arr2)

    pool = np.concatenate([arr1, arr2])
    n1 = len(arr1)
    rng = np.random.default_rng(seed)

    diffs = np.zeros(n_permutations)
    for i in range(n_permutations):
        shuffled = rng.permutation(pool)
        perm_g1 = shuffled[:n1]
        perm_g2 = shuffled[n1:]
        diffs[i] = np.mean(perm_g1) - np.mean(perm_g2)

    p_val = float((np.abs(diffs) >= np.abs(obs_diff)).mean())
    return p_val


def random_entry_null(
    df: pd.DataFrame,
    horizon: int = 5,
    n_samples: int = 1000,
    seed: int | None = None,
) -> np.ndarray:
    """Generate a null distribution from random entries in log-return space."""
    if "returns" not in df.columns:
        return np.zeros(n_samples)
    returns = df["returns"].dropna().to_numpy()
    if len(returns) < horizon:
        return np.zeros(n_samples)

    rng = np.random.default_rng(seed)
    null_expectancies = np.zeros(n_samples)

    for i in range(n_samples):
        # Sample random entry points
        indices = rng.integers(0, len(returns) - horizon, size=30)
        # Calculate mean forward returns for these 30 random entries
        fwd_returns = [np.sum(returns[idx : idx + horizon]) for idx in indices]
        null_expectancies[i] = np.mean(fwd_returns)

    return null_expectancies


def r_space_null(
    n_trades: int = 30,
    n_samples: int = 1000,
    seed: int | None = None,
) -> np.ndarray:
    """Generate a null distribution in R-multiple space (assuming standard coin-flip model)."""
    rng = np.random.default_rng(seed)
    null_expectancies = np.zeros(n_samples)
    for i in range(n_samples):
        # 50/50 win/loss of +1R and -1R
        trades = rng.choice([1.0, -1.0], size=n_trades)
        null_expectancies[i] = np.mean(trades)
    return null_expectancies


def session_randomized_null(
    df: pd.DataFrame,
    n_shuffles: int = 500,
    seed: int | None = None,
) -> np.ndarray:
    """Generate a null distribution by shuffling entries within the same session."""
    rng = np.random.default_rng(seed)
    if "hour" not in df.columns or "returns" not in df.columns:
        return np.zeros(n_shuffles)

    df = df.copy()
    null_means = np.zeros(n_shuffles)

    for i in range(n_shuffles):
        shuffled_returns = df["returns"].copy()
        # Shuffle returns within each hour session group
        for _hour, group in df.groupby("hour"):
            indices = group.index
            shuffled_vals = rng.permutation(group["returns"].to_numpy())
            shuffled_returns.loc[indices] = shuffled_vals
        null_means[i] = shuffled_returns.mean()

    return null_means


def shuffle_returns_null(
    df: pd.DataFrame,
    n_shuffles: int = 500,
    seed: int | None = None,
) -> np.ndarray:
    """Generate a null distribution by shuffling return blocks."""
    if "returns" not in df.columns:
        return np.zeros(n_shuffles)
    returns = df["returns"].dropna().to_numpy()
    if len(returns) == 0:
        return np.zeros(n_shuffles)

    rng = np.random.default_rng(seed)
    null_means = np.zeros(n_shuffles)
    for i in range(n_shuffles):
        shuffled = rng.permutation(returns)
        null_means[i] = np.mean(shuffled)
    return null_means


def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Apply Benjamini-Hochberg false-discovery-rate correction."""
    m = len(p_values)
    if m == 0:
        return []

    # Sort p-values and keep track of original indices
    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    reject = [False] * m

    max_i = -1
    for rank, (_orig_idx, p) in enumerate(indexed_p):
        i = rank + 1  # 1-based rank
        if p <= (i / m) * alpha:
            max_i = rank

    if max_i != -1:
        for r in range(max_i + 1):
            orig_idx = indexed_p[r][0]
            reject[orig_idx] = True

    return reject


def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Apply Holm-Bonferroni multiple-comparison correction."""
    m = len(p_values)
    if m == 0:
        return []

    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    reject = [False] * m

    for rank, (orig_idx, p) in enumerate(indexed_p):
        i = rank + 1
        denominator = m - i + 1
        if p <= alpha / denominator:
            reject[orig_idx] = True
        else:
            # Stop at the first non-significant p-value
            break

    return reject


def null_distribution_stats(
    null_distribution: list[float] | np.ndarray,
) -> dict[str, float]:
    """Compute summary statistics for a null distribution."""
    arr = np.asarray(null_distribution)
    if len(arr) == 0:
        return {"mean": 0.0, "std": 0.0}
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
    }
