"""Optimization scoring and metrics assessment.

Implements Sharpe, Sortino, Calmar, profit factor, total return, and custom composite
scoring functions. Also implements Deflated Sharpe Ratio (DSR) and Multiple Testing
adjustments.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any, Protocol

import numpy as np


# Scoring Function Type Protocol
class ScoringFunction(Protocol):
    """Protocol for scoring functions."""

    def __call__(self, trades: list[dict[str, Any]], initial_balance: float) -> float:
        """Calculate score from trades list."""
        ...


def get_daily_returns(
    trades: list[dict[str, Any]], initial_balance: float
) -> list[float]:
    """Helper to group trade profits by day and compute returns.

    Args:
        trades: List of executed trades.
        initial_balance: Starting account balance.

    Returns:
        list[float]: Daily returns.
    """
    if not trades:
        return []
    daily_profits: dict[str, float] = {}
    for t in trades:
        close_time = t.get("close_time") or t.get("close_timestamp")
        if not close_time:
            continue
        if isinstance(close_time, str):
            try:
                dt = datetime.fromisoformat(close_time)
            except ValueError:
                dt = datetime.now(UTC)
        else:
            dt = close_time
        day = dt.date().isoformat()
        daily_profits[day] = daily_profits.get(day, 0.0) + float(t.get("profit", 0.0))
    return [p / initial_balance for p in daily_profits.values()]


def calculate_max_drawdown(
    trades: list[dict[str, Any]], initial_balance: float
) -> float:
    """Calculate maximum peak-to-trough drawdown from trade profit sequences.

    Args:
        trades: List of trades.
        initial_balance: Starting balance.

    Returns:
        float: Max drawdown fraction (0-1).
    """
    balance = initial_balance
    peak = balance
    max_dd = 0.0
    for t in trades:
        balance += float(t.get("profit", 0.0))
        peak = max(peak, balance)
        dd = (peak - balance) / peak if peak > 0.0 else 0.0
        max_dd = max(max_dd, dd)
    return max_dd


def total_return_score(trades: list[dict[str, Any]], initial_balance: float) -> float:
    """Calculate total return ratio.

    Args:
        trades: List of trades.
        initial_balance: Starting balance.

    Returns:
        float: Total return percentage.
    """
    if not initial_balance:
        return 0.0
    net_profit = sum(float(t.get("profit", 0.0)) for t in trades)
    return float(net_profit / initial_balance)


def profit_factor_score(
    trades: list[dict[str, Any]],
    initial_balance: float,  # noqa: ARG001
) -> float:
    """Calculate profit factor (gross win profit divided by gross loss).

    Args:
        trades: List of trades.
        initial_balance: Starting balance.

    Returns:
        float: Profit factor score.
    """
    wins = [
        float(t.get("profit", 0.0)) for t in trades if float(t.get("profit", 0.0)) > 0.0
    ]
    losses = [
        float(t.get("profit", 0.0)) for t in trades if float(t.get("profit", 0.0)) < 0.0
    ]
    if not losses:
        return float(sum(wins)) if wins else 0.0
    return float(sum(wins) / abs(sum(losses)))


def sharpe_score(trades: list[dict[str, Any]], initial_balance: float) -> float:
    """Calculate annualized daily returns Sharpe ratio.

    Args:
        trades: List of trades.
        initial_balance: Starting balance.

    Returns:
        float: Annualized Sharpe ratio.
    """
    returns = get_daily_returns(trades, initial_balance)
    if len(returns) < 2:  # noqa: PLR2004
        return 0.0
    ret_std = np.std(returns, ddof=1)
    if ret_std == 0.0:
        return 0.0
    return float((np.mean(returns) / ret_std) * np.sqrt(252))


def sortino_score(trades: list[dict[str, Any]], initial_balance: float) -> float:
    """Calculate annualized daily returns Sortino ratio.

    Args:
        trades: List of trades.
        initial_balance: Starting balance.

    Returns:
        float: Annualized Sortino ratio.
    """
    returns = get_daily_returns(trades, initial_balance)
    if len(returns) < 2:  # noqa: PLR2004
        return 0.0
    downside_returns = [r for r in returns if r < 0.0]
    if not downside_returns:
        return 0.0
    downside_std = np.sqrt(np.sum([r**2 for r in returns if r < 0.0]) / len(returns))
    if downside_std == 0.0:
        return 0.0
    return float((np.mean(returns) / downside_std) * np.sqrt(252))


def calmar_score(trades: list[dict[str, Any]], initial_balance: float) -> float:
    """Calculate Calmar ratio (annualized return divided by max drawdown).

    Args:
        trades: List of trades.
        initial_balance: Starting balance.

    Returns:
        float: Calmar ratio.
    """
    max_dd = calculate_max_drawdown(trades, initial_balance)
    if max_dd <= 0.0:
        return 0.0
    ret = total_return_score(trades, initial_balance)
    return float(ret / max_dd)


def custom_score(trades: list[dict[str, Any]], initial_balance: float) -> float:
    """Calculate a weighted composite score.

    Args:
        trades: List of trades.
        initial_balance: Starting balance.

    Returns:
        float: Weighted composite score.
    """
    ret = total_return_score(trades, initial_balance)
    sharpe = sharpe_score(trades, initial_balance)
    max_dd = calculate_max_drawdown(trades, initial_balance)
    return float(0.4 * ret + 0.4 * sharpe - 0.2 * max_dd)


def optimization_get_scoring_func(name: str) -> ScoringFunction:
    """Resolve supported objective name to a scoring function.

    Args:
        name: Objective name string.

    Returns:
        ScoringFunction: Metric evaluator callback.
    """
    funcs = {
        "sharpe": sharpe_score,
        "sortino": sortino_score,
        "calmar": calmar_score,
        "profit_factor": profit_factor_score,
        "total_return": total_return_score,
        "custom": custom_score,
    }
    return funcs.get(name.strip().lower(), total_return_score)


def norm_inv(p: float) -> float:
    """Calculate inverse standard normal CDF Beasley-Springer-Moro approximation.

    Args:
        p: Target probability value (0-1).

    Returns:
        float: Standard normal quantile Z-score.
    """
    try:
        from scipy.stats import norm  # type: ignore[import-untyped,unused-ignore]  # fmt: skip # noqa: I001

        return float(norm.ppf(p))
    except ImportError:
        if p <= 0.0 or p >= 1.0:
            return 0.0
        y = p - 0.5
        if abs(y) < 0.42:  # noqa: PLR2004
            r = y * y
            a = [2.50662823884, -18.61500062529, 41.39119773534, -28.47609504908]
            b = [1.0, -8.47351093090, 23.08336743743, -21.06224101826, 3.13082909833]
            num = a[0] + r * (a[1] + r * (a[2] + r * a[3]))
            den = b[0] + r * (b[1] + r * (b[2] + r * (b[3] + r * b[4])))
            return y * num / den
        r = p if y < 0 else 1.0 - p
        s = math.log(-math.log(r))
        c = [2.92246467, 1.85957931, -0.08962697, -0.02244095]
        x = c[0] + s * (c[1] + s * (c[2] + s * c[3]))
        return -x if y < 0 else x


def calculate_dsr(
    sharpe: float,
    trial_count: int,
    skew: float = 0.0,
    kurtosis: float = 3.0,
    t_samples: int = 100,
) -> float:
    """Calculate Deflated Sharpe Ratio (DSR) using normal CDF approximation.

    Args:
        sharpe: Calculated annualized Sharpe ratio.
        trial_count: Number of optimization trials/tests executed.
        skew: Skewness of daily return distribution.
        kurtosis: Kurtosis of daily return distribution.
        t_samples: Number of daily return samples.

    Returns:
        float: Deflated Sharpe Ratio probability fraction (0-1).
    """
    if trial_count <= 1:
        return 1.0 if sharpe > 0.0 else 0.0

    euler_mascheroni = 0.57721566490153286
    z_inv = norm_inv(1.0 - 1.0 / trial_count)
    z_inv_e = norm_inv(1.0 - 1.0 / (trial_count * math.e))
    e_max = (1.0 - euler_mascheroni) * z_inv + euler_mascheroni * z_inv_e
    sr0 = e_max / math.sqrt(t_samples) if t_samples > 0 else 0.0

    var_sr = (
        (1.0 - skew * sharpe + ((kurtosis - 1.0) / 4.0) * (sharpe**2)) / (t_samples - 1)
        if t_samples > 1
        else 1.0
    )
    if var_sr <= 0.0:
        return 0.0

    stat = (sharpe - sr0) / math.sqrt(var_sr)
    # normal CDF approximation using error function
    return 0.5 * (1.0 + math.erf(stat / math.sqrt(2.0)))


def evaluate_candidate_score(
    trades: list[dict[str, Any]],
    initial_balance: float,
    objective: str = "sharpe",
    trial_count: int = 1,
) -> dict[str, Any]:
    """Evaluate performance score and anti-overfitting metrics for a candidate.

    Args:
        trades: Evaluated candidate trades.
        initial_balance: Starting balance.
        objective: Main optimization objective name.
        trial_count: Number of unique candidate trials in search space.

    Returns:
        dict[str, Any]: Score and metrics dictionary.
    """
    func = optimization_get_scoring_func(objective)
    score = func(trades, initial_balance)

    # Compute raw Sharpe and DSR
    raw_sr = sharpe_score(trades, initial_balance)
    returns = get_daily_returns(trades, initial_balance)

    # Simple skewness/kurtosis calculation
    skew = 0.0
    kurtosis = 3.0
    n = len(returns)
    if n >= 3:  # noqa: PLR2004
        returns_arr = np.array(returns)
        mean = np.mean(returns_arr)
        std = np.std(returns_arr, ddof=1)
        if std > 0.0:
            skew = float(np.mean((returns_arr - mean) ** 3) / (std**3))
            kurtosis = float(np.mean((returns_arr - mean) ** 4) / (std**4))

    t_samples = max(n, 2)
    dsr = calculate_dsr(raw_sr, trial_count, skew, kurtosis, t_samples)

    # Return standard metrics mapping
    return {
        "score": score,
        "raw_sharpe": raw_sr,
        "deflated_sharpe": dsr,
        "skewness": skew,
        "kurtosis": kurtosis,
        "trade_count": len(trades),
        "ending_balance": initial_balance
        + sum(float(t.get("profit", 0.0)) for t in trades),
        "net_profit": sum(float(t.get("profit", 0.0)) for t in trades),
        "max_drawdown": calculate_max_drawdown(trades, initial_balance),
        "multiple_testing_method": "deflated_sharpe_ratio",
        "mtb_pass_status": bool(dsr >= 0.95),  # noqa: PLR2004
        "mtb_rejection_reason": None
        if dsr >= 0.95  # noqa: PLR2004
        else "deflated_sharpe_ratio_below_95_percent",
    }


def rank_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sort optimization parameter sets deterministically.

    Sorts by score descending, then by trade_count descending, then by
    candidate_hash ascending.

    Args:
        candidates: List of candidate results dictionary blocks.

    Returns:
        list[dict[str, Any]]: Deterministically ranked candidate blocks.
    """

    def sort_key(c: dict[str, Any]) -> tuple[float, float, str]:
        score = float(c.get("score", 0.0))
        trade_count = float(c.get("trade_count", 0.0))
        cand_hash = str(c.get("candidate_hash", ""))
        return (score, trade_count, cand_hash)

    # Sort descending for score and trade_count, but ascending for candidate_hash.
    # To do this cleanly, we can sort with custom keys or reverse sort and adjust keys.
    # Let's sort by: score (descending), trade_count (descending),
    # then candidate_hash (ascending).
    # Since Python's sort is stable, we can sort multiple times or map strings/floats.
    # Let's sort in multiple passes:
    # Pass 1: candidate_hash ascending (reverse=False)
    sorted_cands = sorted(candidates, key=lambda c: str(c.get("candidate_hash", "")))
    # Pass 2: trade_count descending (reverse=True)
    sorted_cands.sort(key=lambda c: float(c.get("trade_count", 0.0)), reverse=True)
    # Pass 3: score descending (reverse=True)
    sorted_cands.sort(key=lambda c: float(c.get("score", 0.0)), reverse=True)

    return sorted_cands


def pareto_select(
    candidates: list[dict[str, Any]],
    objectives: list[str],
    initial_balance: float = 10000.0,
) -> list[dict[str, Any]]:
    """Perform deterministic Pareto front selection.

    Args:
        candidates: Candidates evaluated.
        objectives: Multi-objective metric names.
        initial_balance: Starting balance.

    Returns:
        list[dict[str, Any]]: Pareto optimal front candidates.
    """
    if not candidates:
        return []
    if len(objectives) <= 1:
        # Sort by primary objective
        ranked = rank_candidates(candidates)
        return [ranked[0]] if ranked else []

    # Extract objective scores for each candidate
    candidate_scores = []
    for c in candidates:
        scores = []
        for obj in objectives:
            func = optimization_get_scoring_func(obj)
            trades = c.get("trades", [])
            scores.append(func(trades, initial_balance))
        candidate_scores.append((c, np.array(scores)))

    pareto_front = []
    for i, (c1, s1) in enumerate(candidate_scores):
        dominated = False
        for j, (_c2, s2) in enumerate(candidate_scores):
            if i == j:
                continue
            # c2 dominates c1 if s2 >= s1 for all, and s2 > s1 for at least one
            if np.all(s2 >= s1) and np.any(s2 > s1):
                dominated = True
                break
        if not dominated:
            pareto_front.append(c1)

    return pareto_front
