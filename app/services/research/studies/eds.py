# ruff: noqa: E501, TC001
"""Edge Discovery Studies (EDS) service for Research Edge Lab.

Evaluates mean-reversion and trend-persistence rules against historical data and
establishes null-model baselines.
"""

from __future__ import annotations

import datetime
from typing import Any

import numpy as np

from app.services.research.data import PreparedDataset
from app.utils.settings import (
    EdgeLabConfig,
    EdgeResult,
    EdgeStats,
    TradeSample,
)


def run_eds_null_baseline(
    dataset: PreparedDataset,
    config: EdgeLabConfig,
) -> dict[str, Any]:
    """Establish null-model baselines for edge-discovery studies."""
    df = dataset.data
    from app.services.research.helpers import check_sample_size

    check_sample_size(len(df), config.null_models_config.min_samples)

    # Establish baseline return statistics under random shuffle
    from app.services.research.studies.null_models import (
        shuffle_returns_null,
    )

    seed = config.bootstrap_config.seed or 42
    null_dist = shuffle_returns_null(df, n_shuffles=500, seed=seed)

    return {
        "study": "null_baseline",
        "sample_size": len(df),
        "mean_null": float(np.mean(null_dist)),
        "std_null": float(np.std(null_dist)),
        "p95_null": float(np.percentile(null_dist, 95)),
        "p05_null": float(np.percentile(null_dist, 5)),
        "seed": seed,
    }


def _calculate_stats(trades: list[TradeSample]) -> EdgeStats:
    """Calculate summary statistics for a list of trade samples."""
    if not trades:
        return EdgeStats(
            sample_size=0,
            win_rate=0.0,
            profit_factor=0.0,
            expectancy=0.0,
            sharpe_ratio=0.0,
        )

    r_multiples = [t.r_multiple for t in trades]
    wins = [r for r in r_multiples if r > 0]
    losses = [r for r in r_multiples if r < 0]

    win_rate = len(wins) / len(trades)
    gross_profits = sum(wins)
    gross_losses = sum(losses)
    profit_factor = (
        gross_profits / abs(gross_losses)
        if gross_losses != 0
        else (float("inf") if gross_profits > 0 else 1.0)
    )
    expectancy = sum(r_multiples) / len(trades)

    # Calculate t-stat and p-value relative to zero
    std_dev = np.std(r_multiples) if len(r_multiples) > 1 else 0.0
    t_stat = None
    p_val = None
    if std_dev > 0:
        t_stat = (expectancy / std_dev) * np.sqrt(len(trades))
        # Simple normal approximation p-value
        import math

        p_val = float(1.0 - math.erf(abs(t_stat) / math.sqrt(2.0)))

    # Sharpe ratio proxy
    sharpe = (expectancy / std_dev) * np.sqrt(252) if std_dev > 0 else 0.0

    return EdgeStats(
        sample_size=len(trades),
        win_rate=win_rate,
        profit_factor=float(profit_factor),
        expectancy=expectancy,
        sharpe_ratio=float(sharpe),
        p_value=p_val,
        t_statistic=t_stat,
    )


def run_eds_mean_reversion(
    dataset: PreparedDataset,
    config: EdgeLabConfig,
) -> EdgeResult:
    """Evaluate a mean-reversion detector based on compression and z-score fade behavior."""
    mr_config = config.mean_reversion_config
    df = dataset.data
    from app.services.research.features import zscore
    from app.services.research.helpers import check_sample_size

    # Validate sample size
    check_sample_size(len(df), config.null_models_config.min_samples)

    zs = zscore(df["close"], mr_config.compression_window)
    trades: list[TradeSample] = []
    warnings: list[str] = []

    for idx in range(len(df)):
        if idx + mr_config.fade_horizon >= len(df):
            continue
        z_val = zs.iloc[idx]
        if np.isnan(z_val):
            continue

        direction = 0
        if z_val > mr_config.zscore_threshold:
            direction = -1  # Short
        elif z_val < -mr_config.zscore_threshold:
            direction = 1  # Long

        if direction != 0:
            entry_price = df["close"].iloc[idx]
            exit_price = df["close"].iloc[idx + mr_config.fade_horizon]
            ret = ((exit_price - entry_price) / entry_price) * direction

            # Calculate MFE and MAE
            window_prices = df["close"].iloc[idx + 1 : idx + mr_config.fade_horizon + 1]
            mfe = float(((window_prices - entry_price) / entry_price * direction).max())
            mae = float(((window_prices - entry_price) / entry_price * direction).min())

            trades.append(
                TradeSample(
                    entry_time=df.index[idx].to_pydatetime(),
                    exit_time=df.index[idx + mr_config.fade_horizon].to_pydatetime(),
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    r_multiple=ret,
                    mae=mae,
                    mfe=mfe,
                )
            )

    stats = _calculate_stats(trades)
    if stats.sample_size < config.null_models_config.min_samples:
        warnings.append("Evaluated trades sample size is below recommended threshold.")

    return EdgeResult(
        study_name="mean_reversion_fade",
        config=config,
        stats=stats,
        trades=trades,
        warnings=warnings,
        audit_metadata={
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "rule": f"fade zscore > {mr_config.zscore_threshold}",
        },
    )


def run_eds_trend_persistence(
    dataset: PreparedDataset,
    config: EdgeLabConfig,
) -> EdgeResult:
    """Evaluate a trend-persistence detector based on high-ATR breakout follow-through behavior."""
    tp_config = config.trend_persistence_config
    df = dataset.data
    from app.services.research.features import atr
    from app.services.research.helpers import check_sample_size

    # Validate sample size
    check_sample_size(len(df), config.null_models_config.min_samples)

    atr_vals = atr(df["high"], df["low"], df["close"], tp_config.atr_window)
    trades: list[TradeSample] = []
    warnings: list[str] = []

    for idx in range(1, len(df)):
        if idx + tp_config.follow_through_horizon >= len(df):
            continue
        atr_val = atr_vals.iloc[idx]
        if np.isnan(atr_val) or atr_val <= 0:
            continue

        prev_close = df["close"].iloc[idx - 1]
        close = df["close"].iloc[idx]

        direction = 0
        if close > prev_close + tp_config.breakout_multiplier * atr_val:
            direction = 1  # Long breakout
        elif close < prev_close - tp_config.breakout_multiplier * atr_val:
            direction = -1  # Short breakout

        if direction != 0:
            entry_price = close
            exit_price = df["close"].iloc[idx + tp_config.follow_through_horizon]
            ret = ((exit_price - entry_price) / entry_price) * direction

            window_prices = df["close"].iloc[
                idx + 1 : idx + tp_config.follow_through_horizon + 1
            ]
            mfe = float(((window_prices - entry_price) / entry_price * direction).max())
            mae = float(((window_prices - entry_price) / entry_price * direction).min())

            trades.append(
                TradeSample(
                    entry_time=df.index[idx].to_pydatetime(),
                    exit_time=df.index[
                        idx + tp_config.follow_through_horizon
                    ].to_pydatetime(),
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    r_multiple=ret,
                    mae=mae,
                    mfe=mfe,
                )
            )

    stats = _calculate_stats(trades)
    if stats.sample_size < config.null_models_config.min_samples:
        warnings.append("Evaluated trades sample size is below recommended threshold.")

    return EdgeResult(
        study_name="trend_persistence_breakout",
        config=config,
        stats=stats,
        trades=trades,
        warnings=warnings,
        audit_metadata={
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "rule": f"breakout > {tp_config.breakout_multiplier} * ATR",
        },
    )
