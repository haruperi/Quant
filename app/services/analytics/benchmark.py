"""Benchmark comparison metrics for Analytics.

Implements Beta, Alpha, R-Squared, Tracking Error,
and Information Ratios against benchmark inputs.
"""

from __future__ import annotations

import math
from typing import Any, cast

from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError


def _validate_request_id(request_id: str | None) -> None:
    """Helper to validate request_id strictly."""
    if request_id is not None and (
        not isinstance(request_id, str) or not request_id.strip()
    ):
        raise ValidationError("request_id must be a non-empty string.")


def _to_float_list(series: Any) -> list[float]:
    if series is None:
        return []
    if hasattr(series, "tolist"):
        return cast("list[float]", series.tolist())
    if isinstance(series, list):
        return [float(x) for x in series]
    return []


def _align_series(
    strategy_returns: Any, benchmark_returns: Any
) -> tuple[list[float], list[float]]:
    """Align strategy and benchmark returns chronologically, truncating if necessary."""
    s_list = _to_float_list(strategy_returns)
    b_list = _to_float_list(benchmark_returns)

    # Try using pandas alignment if they are pandas objects
    if hasattr(strategy_returns, "align") and hasattr(benchmark_returns, "align"):
        import pandas as pd

        s_ser = pd.Series(strategy_returns)
        b_ser = pd.Series(benchmark_returns)
        s_aligned, b_aligned = s_ser.align(b_ser, join="inner")
        return [float(x) for x in s_aligned.tolist()], [
            float(x) for x in b_aligned.tolist()
        ]

    n = min(len(s_list), len(b_list))
    return s_list[:n], b_list[:n]


# --- Core Kernels ---


def beta(strategy_returns: list[float], benchmark_returns: list[float]) -> float:
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n < 2:
        return 1.0
    mean_s = sum(s_aligned) / n
    mean_b = sum(b_aligned) / n
    cov = sum((s_aligned[i] - mean_s) * (b_aligned[i] - mean_b) for i in range(n)) / (
        n - 1
    )
    var_b = sum((b_aligned[i] - mean_b) ** 2 for i in range(n)) / (n - 1)
    if var_b == 0:
        return 1.0
    return cov / var_b


def alpha(
    strategy_returns: list[float],
    benchmark_returns: list[float],
    risk_free_rate: float = 0.0,
) -> float:
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n == 0:
        return 0.0
    b_coef = beta(s_aligned, b_aligned)
    mean_s = sum(s_aligned) / n
    mean_b = sum(b_aligned) / n
    # Annualize Jensen's Alpha assuming daily returns
    # Alpha = E(R_s) - [R_f + Beta * (E(R_b) - R_f)]
    # Daily alpha:
    daily_alpha = mean_s - (
        risk_free_rate / 252.0 + b_coef * (mean_b - risk_free_rate / 252.0)
    )
    return daily_alpha * 252.0 * 100.0  # Annualized %


def r_squared(strategy_returns: list[float], benchmark_returns: list[float]) -> float:
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n < 2:
        return 0.0
    mean_s = sum(s_aligned) / n
    mean_b = sum(b_aligned) / n
    cov = sum((s_aligned[i] - mean_s) * (b_aligned[i] - mean_b) for i in range(n)) / (
        n - 1
    )
    var_s = sum((s_aligned[i] - mean_s) ** 2 for i in range(n)) / (n - 1)
    var_b = sum((b_aligned[i] - mean_b) ** 2 for i in range(n)) / (n - 1)
    if var_s == 0 or var_b == 0:
        return 0.0
    r = cov / (math.sqrt(var_s) * math.sqrt(var_b))
    return r**2


def tracking_error(
    strategy_returns: list[float], benchmark_returns: list[float]
) -> float:
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n < 2:
        return 0.0
    diff = [s_aligned[i] - b_aligned[i] for i in range(n)]
    mean_diff = sum(diff) / n
    var_diff = sum((x - mean_diff) ** 2 for x in diff) / (n - 1)
    # Annualized tracking error
    return math.sqrt(var_diff) * math.sqrt(252) * 100.0  # Annualized %


def information_ratio(
    strategy_returns: list[float], benchmark_returns: list[float]
) -> float:
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n < 2:
        return 0.0
    diff = [s_aligned[i] - b_aligned[i] for i in range(n)]
    mean_diff = sum(diff) / n
    var_diff = sum((x - mean_diff) ** 2 for x in diff) / (n - 1)
    std_diff = math.sqrt(var_diff)
    if std_diff == 0:
        return 0.0
    # Annualized Information Ratio
    return (mean_diff / std_diff) * math.sqrt(252)


def batting_average(
    strategy_returns: list[float], benchmark_returns: list[float]
) -> float:
    s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
    n = len(s_aligned)
    if n == 0:
        return 0.0
    wins = sum(1 for i in range(n) if s_aligned[i] > b_aligned[i])
    return wins / n


# --- Official AI Tools ---


def calculate_benchmark_metrics(
    strategy_returns: Any,
    benchmark_returns: Any,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate combined benchmark-relative metrics such as alpha, beta, and information ratio."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="calculate_benchmark_metrics",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        s_aligned, b_aligned = _align_series(strategy_returns, benchmark_returns)
        if not s_aligned:
            raise ValidationError(
                "Aligned returns series must contain at least one valid data point."
            )

        data = {
            "beta": beta(s_aligned, b_aligned),
            "alpha_percent": alpha(s_aligned, b_aligned),
            "r_squared": r_squared(s_aligned, b_aligned),
            "tracking_error_percent": tracking_error(s_aligned, b_aligned),
            "information_ratio": information_ratio(s_aligned, b_aligned),
            "batting_average": batting_average(s_aligned, b_aligned),
        }
        return success_response(
            message="Successfully calculated benchmark metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)
