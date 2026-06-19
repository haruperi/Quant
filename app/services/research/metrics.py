# ruff: noqa: PLR2004
"""Core metric calculators for Research Edge Lab.

Defines the metric calculator interface and standard calculators for returns,
volatility, range, geometry, volume, and spread.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    import pandas as pd

    from app.utils.settings import EdgeLabConfig


class MetricValue:
    """Represents one normalized metric value with metadata."""

    def __init__(self, value: float, metadata: dict[str, Any] | None = None) -> None:
        """Initialize a metric value."""
        self.value = value
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert metric value to a dict."""
        return {"value": self.value, "metadata": self.metadata}


class MetricContext:
    """Provides the dataset and metadata needed by metric calculators."""

    def __init__(self, df: pd.DataFrame, config: EdgeLabConfig) -> None:
        """Initialize metric context."""
        self.df = df
        self.config = config


class MetricCalculator:
    """Calculator interface for research core metrics."""

    def calculate(self, context: MetricContext) -> MetricValue:
        """Calculate the metric from the context."""
        raise NotImplementedError


class ReturnsCalculator(MetricCalculator):
    """Calculates return-related core metrics."""

    def calculate(self, context: MetricContext) -> MetricValue:
        """Calculate mean return and return metrics."""
        returns = context.df["returns"].dropna()
        if returns.empty:
            return MetricValue(0.0, {"status": "empty"})
        return MetricValue(
            float(returns.mean()),
            {
                "std": float(returns.std()),
                "skew": float(returns.skew()) if len(returns) > 2 else 0.0,
                "kurt": float(returns.kurt()) if len(returns) > 3 else 0.0,
                "count": len(returns),
            },
        )


class RocCalculator(MetricCalculator):
    """Calculates rate-of-change core metrics."""

    def calculate(self, context: MetricContext) -> MetricValue:
        """Calculate rate of change."""
        close = context.df["close"]
        if len(close) < 11:
            return MetricValue(0.0, {"status": "insufficient_data"})
        roc = (close - close.shift(10)) / close.shift(10)
        roc = roc.dropna()
        return MetricValue(
            float(roc.mean()),
            {"std": float(roc.std()), "count": len(roc)},
        )


class CandlesCalculator(MetricCalculator):
    """Calculates candle-geometry core metrics."""

    def calculate(self, context: MetricContext) -> MetricValue:
        """Calculate candle body and shadows."""
        df = context.df
        if "candle_body" not in df.columns:
            return MetricValue(0.0, {"status": "missing_features"})
        return MetricValue(
            float(df["candle_body"].mean()),
            {
                "mean_upper_shadow": float(df["upper_shadow"].mean()),
                "mean_lower_shadow": float(df["lower_shadow"].mean()),
            },
        )


class RangesCalculator(MetricCalculator):
    """Calculates range-related core metrics."""

    def calculate(self, context: MetricContext) -> MetricValue:
        """Calculate high-low ranges."""
        df = context.df
        hl_range = df["high"] - df["low"]
        return MetricValue(
            float(hl_range.mean()),
            {"max": float(hl_range.max()), "min": float(hl_range.min())},
        )


class VolatilityCalculator(MetricCalculator):
    """Calculates volatility core metrics."""

    def calculate(self, context: MetricContext) -> MetricValue:
        """Calculate annualized volatility."""
        returns = context.df["returns"].dropna()
        if returns.empty:
            return MetricValue(0.0, {"status": "empty"})
        # Daily scaling factor approximation
        ann_vol = float(returns.std() * np.sqrt(252))
        return MetricValue(ann_vol, {"scaling_factor": 252})


class SpreadCalculator(MetricCalculator):
    """Calculates spread-quality core metrics."""

    def calculate(self, context: MetricContext) -> MetricValue:
        """Calculate spread statistics."""
        df = context.df
        if "spread" not in df.columns:
            return MetricValue(0.0, {"status": "missing_spread"})
        spread = df["spread"].dropna()
        return MetricValue(
            float(spread.mean()),
            {"max": float(spread.max()), "min": float(spread.min())},
        )


class VolumeActivityCalculator(MetricCalculator):
    """Calculates volume or activity core metrics."""

    def calculate(self, context: MetricContext) -> MetricValue:
        """Calculate volume statistics."""
        df = context.df
        if "volume" not in df.columns:
            return MetricValue(0.0, {"status": "missing_volume"})
        volume = df["volume"].dropna()
        return MetricValue(
            float(volume.mean()),
            {"max": float(volume.max()), "min": float(volume.min())},
        )


class MetricRegistry:
    """Registers and resolves named metric calculators."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._calculators: dict[str, MetricCalculator] = {}

    def register(self, name: str, calculator: MetricCalculator) -> None:
        """Register a calculator."""
        self._calculators[name] = calculator

    def calculate_all(self, context: MetricContext) -> dict[str, MetricValue]:
        """Calculate all registered metrics."""
        return {
            name: calc.calculate(context) for name, calc in self._calculators.items()
        }


def build_default_registry() -> MetricRegistry:
    """Build the default registry of research metric calculators."""
    registry = MetricRegistry()
    registry.register("returns", ReturnsCalculator())
    registry.register("roc", RocCalculator())
    registry.register("candles", CandlesCalculator())
    registry.register("ranges", RangesCalculator())
    registry.register("volatility", VolatilityCalculator())
    registry.register("spread", SpreadCalculator())
    registry.register("volume", VolumeActivityCalculator())
    return registry
