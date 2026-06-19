# ruff: noqa: E501, PLR2004
"""Feature engineering service for Research Edge Lab.

Calculates technical indicators, forward returns, excursions, and regime
classifications for quant studies.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.utils.errors import ValidationError


def log_returns(close: pd.Series) -> pd.Series:
    """Compute log returns from close prices."""
    return np.log(close / close.shift(1))


def simple_returns(close: pd.Series) -> pd.Series:
    """Compute arithmetic returns from close prices."""
    return close.pct_change()


def zscore(close: pd.Series, window: int = 20) -> pd.Series:
    """Compute a close-price z-score relative to a moving average and standard deviation."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")
    ma = close.rolling(window).mean()
    sd = close.rolling(window).std()
    return (close - ma) / sd


def percent_rank(series: pd.Series, window: int = 20) -> pd.Series:
    """Compute rolling percentile rank values."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")

    def _rank(x: np.ndarray) -> float:
        if len(x) == 0:
            return float(np.nan)
        val = x[-1]
        if np.isnan(val):
            return float(np.nan)
        valid_x = x[~np.isnan(x)]
        if len(valid_x) <= 1:
            return 0.5
        return float((valid_x <= val).sum() / len(valid_x))

    return series.rolling(window).apply(_rank, raw=True)


def rolling_percentile_rank(series: pd.Series, window: int = 20) -> pd.Series:
    """Compute rolling percentile rank for a supplied series."""
    return percent_rank(series, window)


def atr(
    high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14
) -> pd.Series:
    """Compute Average True Range (ATR)."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window).mean()


def atr_percent(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14,
) -> pd.Series:
    """Compute ATR as a percentage of close price."""
    atr_val = atr(high, low, close, window)
    return atr_val / close


def bollinger_bands(
    close: pd.Series,
    window: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Compute Bollinger-style upper, middle, and lower bands."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")
    middle = close.rolling(window).mean()
    sd = close.rolling(window).std()
    upper = middle + num_std * sd
    lower = middle - num_std * sd
    return upper, middle, lower


def bb_width(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series:
    """Compute Bollinger Band width."""
    upper, middle, lower = bollinger_bands(close, window, num_std)
    return (upper - lower) / middle


def bb_percent_b(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series:
    """Compute Bollinger Band percent-B."""
    upper, _, lower = bollinger_bands(close, window, num_std)
    return (close - lower) / (upper - lower)


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Compute Relative Strength Index."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def rate_of_change(close: pd.Series, window: int = 14) -> pd.Series:
    """Compute rate of change as a momentum measure."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")
    return (close - close.shift(window)) / close.shift(window)


def momentum(close: pd.Series, window: int = 14) -> pd.Series:
    """Compute simple price-difference momentum."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")
    return close - close.shift(window)


def donchian_channel(
    high: pd.Series,
    low: pd.Series,
    window: int = 20,
) -> tuple[pd.Series, pd.Series]:
    """Compute Donchian breakout levels (upper and lower)."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")
    upper = high.rolling(window).max()
    lower = low.rolling(window).min()
    return upper, lower


def hurst_exponent(series: pd.Series) -> float:
    """Estimate Hurst exponent for mean-reversion versus trend detection."""
    vals = series.dropna().to_numpy()
    if len(vals) < 50:
        return 0.5
    returns = np.diff(np.log(vals))
    n_vals = len(returns)
    if n_vals < 20:
        return 0.5

    max_chunk = n_vals
    min_chunk = 10
    chunks = np.unique(np.geomspace(min_chunk, max_chunk, num=10).astype(int))

    rs_vals = []
    chunk_sizes = []

    for n in chunks:
        num_chunks = n_vals // n
        if num_chunks == 0:
            continue
        rs_list = []
        for i in range(num_chunks):
            chunk = returns[i * n : (i + 1) * n]
            mean = np.mean(chunk)
            y = np.cumsum(chunk - mean)
            r = np.max(y) - np.min(y)
            s = np.std(chunk)
            if s > 0:
                rs_list.append(r / s)
        if rs_list:
            rs_vals.append(np.mean(rs_list))
            chunk_sizes.append(n)

    if len(chunk_sizes) < 2:
        return 0.5

    poly = np.polyfit(np.log(chunk_sizes), np.log(rs_vals), 1)
    h = float(poly[0])
    return float(np.clip(h, 0.0, 1.0))


def rolling_hurst(series: pd.Series, window: int = 100) -> pd.Series:
    """Compute Hurst exponent over rolling windows."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")

    def _hurst(x: np.ndarray) -> float:
        return hurst_exponent(pd.Series(x))

    return series.rolling(window).apply(_hurst, raw=True)


def pivot_points(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> dict[str, pd.Series]:
    """Compute pivot, support, and resistance levels (Standard Pivot Points)."""
    p = (high + low + close) / 3.0
    r1 = 2.0 * p - low
    s1 = 2.0 * p - high
    r2 = p + (high - low)
    s2 = p - (high - low)
    r3 = high + 2.0 * (p - low)
    s3 = low - 2.0 * (high - p)
    return {"pivot": p, "r1": r1, "s1": s1, "r2": r2, "s2": s2, "r3": r3, "s3": s3}


def adr(high: pd.Series, low: pd.Series, window: int = 14) -> pd.Series:
    """Compute Average Daily Range."""
    if window <= 0:
        raise ValidationError("Window must be positive.", code="INVALID_INPUT")
    return (high - low).rolling(window).mean()


def forward_returns(close: pd.Series, horizon: int = 5) -> pd.Series:
    """Compute horizon-aligned forward log returns (labeled with research_ prefix)."""
    if horizon <= 0:
        raise ValidationError("Horizon must be positive.", code="INVALID_INPUT")
    ret = np.log(close.shift(-horizon) / close)
    ret.name = "research_forward_returns"
    return ret


def forward_max_favorable_excursion(
    close: pd.Series,
    high: pd.Series,
    horizon: int = 5,
) -> pd.Series:
    """Compute maximum favorable price excursion over a forward horizon (labeled with research_ prefix)."""
    if horizon <= 0:
        raise ValidationError("Horizon must be positive.", code="INVALID_INPUT")
    # Shift high back
    mfe = pd.Series(index=close.index, dtype=float)
    for idx in range(len(close)):
        if idx + horizon >= len(close):
            continue
        max_high = high.iloc[idx + 1 : idx + horizon + 1].max()
        mfe.iloc[idx] = (max_high - close.iloc[idx]) / close.iloc[idx]
    mfe.name = "research_mfe"
    return mfe


def forward_max_adverse_excursion(
    close: pd.Series,
    low: pd.Series,
    horizon: int = 5,
) -> pd.Series:
    """Compute maximum adverse price excursion over a forward horizon (labeled with research_ prefix)."""
    if horizon <= 0:
        raise ValidationError("Horizon must be positive.", code="INVALID_INPUT")
    mae = pd.Series(index=close.index, dtype=float)
    for idx in range(len(close)):
        if idx + horizon >= len(close):
            continue
        min_low = low.iloc[idx + 1 : idx + horizon + 1].min()
        mae.iloc[idx] = (min_low - close.iloc[idx]) / close.iloc[idx]
    mae.name = "research_mae"
    return mae


def detect_volatility_regime(
    df: pd.DataFrame,
    window: int = 14,
    threshold_pct: float = 0.7,
) -> pd.Series:
    """Classify volatility regime using ATR percentile or equivalent volatility evidence."""
    df = df.copy()
    atr_val = atr(df["high"], df["low"], df["close"], window)
    atr_rank = percent_rank(atr_val, window=window * 5)
    regime = pd.Series("low", index=df.index)
    regime[atr_rank > threshold_pct] = "high"
    return regime


def detect_trend_regime(
    df: pd.DataFrame,
    fast_window: int = 20,
    slow_window: int = 50,
) -> pd.Series:
    """Classify trend regime from moving-average relationships."""
    df = df.copy()
    fast_ma = df["close"].rolling(fast_window).mean()
    slow_ma = df["close"].rolling(slow_window).mean()
    regime = pd.Series("sideways", index=df.index)
    regime[fast_ma > slow_ma] = "bullish"
    regime[fast_ma < slow_ma] = "bearish"
    return regime


def active_sessions_for_hour(hour: int) -> list[str]:
    """Return the active trading sessions for a given hour."""
    sessions = []
    # London: 08:00 - 16:00
    if 8 <= hour < 16:
        sessions.append("London")
    # New York: 13:00 - 21:00
    if 13 <= hour < 21:
        sessions.append("NewYork")
    # Tokyo: 00:00 - 08:00
    if 0 <= hour < 8:
        sessions.append("Tokyo")
    return sessions


def session_label_for_hour(hour: int) -> str:
    """Return the session label for a given hour."""
    sessions = active_sessions_for_hour(hour)
    if not sessions:
        return "Asian_Quiet"
    return "_".join(sessions)


def calculate_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate regime feature rows.

    Args:
        df: Prepared market data.

    Returns:
        pd.DataFrame: DataFrame containing regime features.
    """
    df = df.copy()
    df["atr_pct"] = atr_percent(df["high"], df["low"], df["close"], 14)
    df["rsi_14"] = rsi(df["close"], 14)
    df["zscore_20"] = zscore(df["close"], 20)
    df["roc_10"] = rate_of_change(df["close"], 10)
    return df


def build_market_regime_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Build timestamp-aligned feature rows for PCA and clustering regime research."""
    feature_df = calculate_regime_features(df)
    cols = ["atr_pct", "rsi_14", "zscore_20", "roc_10"]
    return feature_df[cols].dropna()


def detect_market_regime(df: pd.DataFrame) -> pd.Series:
    """Classify market regime from supplied research features."""
    feature_df = calculate_regime_features(df)
    # Simple rule-based regime detection for demonstration
    regime = pd.Series("normal", index=df.index)
    regime[feature_df["rsi_14"] > 70] = "overbought"
    regime[feature_df["rsi_14"] < 30] = "oversold"
    return regime
