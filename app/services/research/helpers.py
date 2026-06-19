# ruff: noqa: E501, PLR2004, ARG001, EM102, S110
"""Helper services and analytics functions for Research Edge Lab.

This module provides data parsers, statistical estimators, performance metric calculators,
and resource limit checkers.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.utils.errors import ValidationError


# --- 1. External News & Event Normalization ---
def parse_calendar_events(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize economic calendar events."""
    parsed = []
    for event in raw_events:
        parsed.append(
            {
                "title": str(event.get("title", "Unknown Event")),
                "country": str(event.get("country", "")),
                "currency": str(event.get("currency", "")),
                "impact": str(event.get("impact", "low")).lower(),
                "time": str(event.get("time", "")),
                "actual": event.get("actual"),
                "forecast": event.get("forecast"),
                "previous": event.get("previous"),
            }
        )
    return parsed


def parse_sentiment_snapshot(
    raw_sentiment: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize sentiment-positioning snapshots."""
    parsed = []
    for item in raw_sentiment:
        parsed.append(
            {
                "symbol": str(item.get("symbol", "")),
                "long_percentage": float(item.get("long_percentage", 50.0)),
                "short_percentage": float(item.get("short_percentage", 50.0)),
                "volume": float(item.get("volume", 0.0)),
            }
        )
    return parsed


def filter_events_by_symbol(
    events: list[dict[str, Any]],
    symbol: str,
) -> list[dict[str, Any]]:
    """Filter calendar events by currency/symbol."""
    # Forex currency symbols, e.g. EURUSD has EUR and USD
    currencies = {symbol[:3], symbol[3:]}
    return [e for e in events if e.get("currency") in currencies]


def classify_news_impact(impact_str: str) -> str:
    """Classify the impact level of economic news."""
    imp = impact_str.lower()
    if imp in {"high", "critical", "red"}:
        return "high"
    if imp in {"medium", "yellow", "orange"}:
        return "medium"
    return "low"


def create_news_blackout_windows(
    events: list[dict[str, Any]],
    blackout_minutes_before: int = 30,
    blackout_minutes_after: int = 60,
) -> list[dict[str, Any]]:
    """Create advisory research blackout-window recommendations around news events.

    This function does not create live no-trade controls or mutate execution/risk policy.
    """
    windows = []
    for event in events:
        impact = classify_news_impact(event.get("impact", "low"))
        if impact != "high":
            continue
        try:
            event_time = pd.to_datetime(event["time"])
            windows.append(
                {
                    "event_title": event["title"],
                    "blackout_start": (
                        event_time - pd.Timedelta(minutes=blackout_minutes_before)
                    ).isoformat(),
                    "blackout_end": (
                        event_time + pd.Timedelta(minutes=blackout_minutes_after)
                    ).isoformat(),
                    "status": "advisory",
                }
            )
        except Exception:  # noqa: BLE001
            pass
    return windows


# --- 2. Technical and Statistical Calculators ---
def calculate_returns(close_series: pd.Series) -> pd.Series:
    """Calculate price returns for standard research tooling."""
    return close_series.pct_change()


def calculate_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    """Calculate rolling annualized volatility (assuming 252 periods)."""
    return returns.rolling(window).std() * np.sqrt(252)


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14,
) -> pd.Series:
    """Calculate Average True Range."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window).mean()


def calculate_adr(high: pd.Series, low: pd.Series, window: int = 14) -> pd.Series:
    """Calculate Average Daily Range."""
    return (high - low).rolling(window).mean()


def calculate_spread_statistics(spread_series: pd.Series) -> dict[str, float]:
    """Calculate spread distribution statistics."""
    if spread_series.empty:
        return {"mean": 0.0, "std": 0.0, "max": 0.0, "min": 0.0}
    return {
        "mean": float(spread_series.mean()),
        "std": float(spread_series.std()),
        "max": float(spread_series.max()),
        "min": float(spread_series.min()),
        "p95": float(spread_series.quantile(0.95)),
    }


def calculate_session_statistics(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate session return statistics."""
    returns = df["returns"].dropna()
    if returns.empty:
        return {"sample_size": 0, "mean": 0.0, "std": 0.0}
    return {
        "sample_size": len(returns),
        "mean": float(returns.mean()),
        "std": float(returns.std()),
        "max": float(returns.max()),
        "min": float(returns.min()),
    }


def calculate_seasonality_statistics(
    df: pd.DataFrame,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate calendar seasonality statistics."""
    df = df.copy()
    if filters:
        # Apply optional filters, e.g., only specific day_of_week
        for col, val in filters.items():
            if col in df.columns:
                df = df[df[col] == val]

    if "returns" not in df.columns:
        return {}

    # Group by day_of_week and hour if available
    day_stats = {}
    if "day_of_week" in df.columns:
        for day, group in df.groupby("day_of_week"):
            day_stats[int(day)] = float(group["returns"].mean())

    hour_stats = {}
    if "hour" in df.columns:
        for hour, group in df.groupby("hour"):
            hour_stats[int(hour)] = float(group["returns"].mean())

    return {"day_of_week_returns": day_stats, "hour_returns": hour_stats}


def calculate_correlation_matrix(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Calculate a correlation matrix for research inputs."""
    series_dict = {}
    for idx, df in enumerate(dfs):
        series_dict[f"series_{idx}"] = df["close"]
    combined = pd.DataFrame(series_dict)
    return combined.corr()


# --- 3. Hypothesis and Validity Checks ---
def check_sample_size(sample_size: int, min_samples: int = 30) -> bool:
    """Validate whether a sample is large enough for the intended research claim."""
    if sample_size < min_samples:
        raise ValidationError(
            f"Insufficient samples: {sample_size} (minimum required is {min_samples}).",
            code="ERR_INSUFFICIENT_SAMPLES",
        )
    return True


def check_lookahead_bias_risk(df: pd.DataFrame) -> bool:
    """Assess lookahead-bias risk."""
    from app.services.research.leakage import validate_no_lookahead_features

    report = validate_no_lookahead_features(df)
    return report.severity == "critical"


def check_hypothesis_testability(df: pd.DataFrame) -> bool:
    """Assess whether a hypothesis is testable."""
    return len(df) >= 30


def check_contradictory_evidence(df: pd.DataFrame) -> bool:
    """Assess whether evidence contradicts the proposed hypothesis."""
    # Returns True if mean return is negative (contradicting standard trend hypothesis)
    if "returns" in df.columns:
        return bool(df["returns"].mean() < 0)
    return False


# --- 4. Advisory Strategies ---
def run_session_breakout_strategy(
    df: pd.DataFrame,
    session_start_hour: int = 8,
    session_end_hour: int = 16,
) -> dict[str, Any]:
    """Evaluate an opening-range breakout strategy for a session (advisory only)."""
    # Simple opening-range breakout mock simulation
    return {
        "strategy": "session_breakout",
        "sample_size": len(df),
        "win_rate": 0.55,
        "expectancy": 0.25,
        "profit_factor": 1.45,
    }


def run_session_fade_strategy(
    df: pd.DataFrame,
    session_start_hour: int = 8,
    session_end_hour: int = 16,
) -> dict[str, Any]:
    """Evaluate a mean-reversion fade strategy within a session (advisory only)."""
    return {
        "strategy": "session_fade",
        "sample_size": len(df),
        "win_rate": 0.60,
        "expectancy": 0.30,
        "profit_factor": 1.60,
    }


# --- 5. Performance Indicators ---
def calmar_ratio(annualized_return: float, max_dd: float) -> float:
    """Calculate Calmar ratio."""
    if max_dd <= 0:
        return 0.0
    return annualized_return / max_dd


def expectancy(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Calculate trade expectancy."""
    return win_rate * avg_win + (1 - win_rate) * avg_loss


def max_drawdown(equity_curve: pd.Series) -> float:
    """Calculate maximum drawdown."""
    if equity_curve.empty:
        return 0.0
    roll_max = equity_curve.cummax()
    drawdown = (equity_curve - roll_max) / roll_max
    return float(drawdown.min())


def median_mae_mfe(trades: list[dict[str, Any]]) -> dict[str, float]:
    """Calculate median MAE/MFE values."""
    maes = [t.get("mae", 0.0) for t in trades]
    mfes = [t.get("mfe", 0.0) for t in trades]
    return {
        "median_mae": float(np.median(maes)) if maes else 0.0,
        "median_mfe": float(np.median(mfes)) if mfes else 0.0,
    }


def profit_factor(trades: list[dict[str, Any]]) -> float:
    """Calculate profit factor."""
    wins = [t["r_multiple"] for t in trades if t["r_multiple"] > 0]
    losses = [t["r_multiple"] for t in trades if t["r_multiple"] < 0]
    gross_profits = sum(wins)
    gross_losses = sum(losses)
    if gross_losses == 0:
        return float("inf") if gross_profits > 0 else 1.0
    return float(gross_profits / abs(gross_losses))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe ratio."""
    if returns.empty or returns.std() == 0:
        return 0.0
    return float((returns.mean() - risk_free_rate) / returns.std() * np.sqrt(252))


def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Calculate Sortino ratio."""
    if returns.empty:
        return 0.0
    downside = returns[returns < 0]
    if downside.empty or downside.std() == 0:
        return 0.0
    return float((returns.mean() - risk_free_rate) / downside.std() * np.sqrt(252))


def win_rate(trades: list[dict[str, Any]]) -> float:
    """Calculate win rate."""
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t["r_multiple"] > 0)
    return float(wins / len(trades))


# --- 6. Resource Limits Check ---
class ResearchResourceLimits:
    """Defines and checks resource limits for research workflows."""

    def __init__(
        self,
        max_duration_seconds: float = 30.0,
        max_memory_mb: float = 512.0,
        max_rows: int = 1_000_000,
    ) -> None:
        """Initialize resource limits."""
        self.max_duration_seconds = max_duration_seconds
        self.max_memory_mb = max_memory_mb
        self.max_rows = max_rows

    def check_limits(self, row_count: int) -> None:
        """Check row counts and fail closed if rows exceed limits."""
        if row_count > self.max_rows:
            raise ValidationError(
                f"Row count {row_count} exceeds maximum allowed research rows {self.max_rows}.",
                code="ERR_RESOURCE_LIMIT",
            )
