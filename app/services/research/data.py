# ruff: noqa: E501, ANN401, C901
"""Data preparation and validation service for Research Edge Lab.

This module provides data cleaning, schema validation, data quality reporting,
and feature enrichment for historical market data.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.utils.errors import ValidationError
from app.utils.logger import logger
from app.utils.settings import EdgeLabConfig

CanonicalOHLCVSSchema = {"open", "high", "low", "close", "volume", "spread"}


class DatasetIssue(BaseModel):
    """Represents a detected dataset quality issue."""

    code: str
    message: str
    severity: str  # "warning" or "error"
    column: str | None = None


class CleaningAction(BaseModel):
    """Represents a cleaning action applied to research data."""

    action_type: str
    description: str
    column: str | None = None


class DataQualityReportModel(BaseModel):
    """Summarizes validation issues and cleaning actions for a dataset."""

    issues: list[DatasetIssue] = Field(default_factory=list)
    actions: list[CleaningAction] = Field(default_factory=list)


class PreparedDataset:
    """Carries cleaned, validated, enriched data with its quality report and metadata."""

    def __init__(
        self,
        data: pd.DataFrame,
        quality_report: DataQualityReportModel,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize the prepared dataset."""
        self.data = data
        self.quality_report = quality_report
        self.metadata = metadata


def validate_dataset(df: pd.DataFrame) -> DataQualityReportModel:
    """Validate schema, continuity, OHLC consistency, duplicate timestamps, spread quality, and volume fields.

    Args:
        df: Pandas DataFrame containing OHLCV(S) data.

    Returns:
        DataQualityReportModel: Summarized validation report containing warnings and errors.

    Raises:
        ValidationError: If fatal validation errors occur (e.g. missing core OHLC columns).
    """
    report = DataQualityReportModel()

    # 1. Schema Validation (Fatal)
    required = {"open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        msg = f"Missing core OHLC columns: {missing}"
        report.issues.append(
            DatasetIssue(
                code="ERR_MISSING_COLUMNS",
                message=msg,
                severity="error",
            )
        )
        logger.error(msg)
        raise ValidationError(msg, code="VALIDATION_FAILED")

    # 2. Duplicate / Non-monotonic Timestamps
    if not df.index.is_monotonic_increasing:
        report.issues.append(
            DatasetIssue(
                code="ERR_NON_MONOTONIC_INDEX",
                message="Index timestamps are not monotonically increasing.",
                severity="error",
            )
        )
        logger.error("Non-monotonic index detected.")
        raise ValidationError("Index must be monotonic.", code="VALIDATION_FAILED")

    if df.index.duplicated().any():
        report.issues.append(
            DatasetIssue(
                code="ERR_DUPLICATE_TIMESTAMPS",
                message="Duplicate timestamps detected in index.",
                severity="error",
            )
        )
        logger.error("Duplicate timestamps detected.")
        raise ValidationError(
            "Index contains duplicate timestamps.", code="VALIDATION_FAILED"
        )

    # 3. OHLC Consistency Check (Warnings)
    inconsistent_high = df["high"] < df[["open", "close"]].max(axis=1)
    if inconsistent_high.any():
        count = inconsistent_high.sum()
        report.issues.append(
            DatasetIssue(
                code="WARN_INCONSISTENT_HIGH",
                message=f"High price is lower than open or close in {count} rows.",
                severity="warning",
                column="high",
            )
        )

    inconsistent_low = df["low"] > df[["open", "close"]].min(axis=1)
    if inconsistent_low.any():
        count = inconsistent_low.sum()
        report.issues.append(
            DatasetIssue(
                code="WARN_INCONSISTENT_LOW",
                message=f"Low price is higher than open or close in {count} rows.",
                severity="warning",
                column="low",
            )
        )

    # 4. Volume Validation (Warnings)
    if "volume" in df.columns:
        neg_volume = df["volume"] < 0
        if neg_volume.any():
            count = neg_volume.sum()
            report.issues.append(
                DatasetIssue(
                    code="WARN_NEGATIVE_VOLUME",
                    message=f"Negative volume values detected in {count} rows.",
                    severity="warning",
                    column="volume",
                )
            )

    # 5. Spread Quality (Warnings)
    if "spread" in df.columns:
        neg_spread = df["spread"] < 0
        if neg_spread.any():
            count = neg_spread.sum()
            report.issues.append(
                DatasetIssue(
                    code="WARN_NEGATIVE_SPREAD",
                    message=f"Negative spread values detected in {count} rows.",
                    severity="warning",
                    column="spread",
                )
            )

    return report


def enrich_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Add research features such as returns, calendar fields, and candle geometry.

    Args:
        df: Pandas DataFrame containing cleaned OHLCV data.

    Returns:
        pd.DataFrame: A copy of the DataFrame with added features.
    """
    df = df.copy()

    # Returns
    df["returns"] = df["close"].pct_change()
    df["log_returns"] = np.log(df["close"] / df["close"].shift(1))

    # Calendar Fields
    if isinstance(df.index, pd.DatetimeIndex):
        df["day_of_week"] = df.index.dayofweek
        df["hour"] = df.index.hour
        df["month"] = df.index.month
        df["year"] = df.index.year

    # Candle Geometry
    df["candle_body"] = (df["close"] - df["open"]).abs()
    df["upper_shadow"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["lower_shadow"] = df[["open", "close"]].min(axis=1) - df["low"]

    return df


def prepare_research_dataset(
    data: pd.DataFrame,
    config: EdgeLabConfig | None = None,
) -> PreparedDataset:
    """Clean, validate, and enrich OHLCV data.

    Args:
        data: In-memory raw OHLCV DataFrame.
        config: Research configuration. If omitted, default configuration is used.

    Returns:
        PreparedDataset: Cleaned, validated, and enriched dataset.
    """
    if config is None:
        config = EdgeLabConfig()

    df = data.copy()
    report = DataQualityReportModel()

    # 1. Clean Timezones
    if isinstance(df.index, pd.DatetimeIndex):
        target_tz = config.cleaning_config.timezone
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
            report.actions.append(
                CleaningAction(
                    action_type="timezone_localize",
                    description="Localized naive timestamps to UTC.",
                )
            )
        if str(df.index.tz) != target_tz:
            df.index = df.index.tz_convert(target_tz)
            report.actions.append(
                CleaningAction(
                    action_type="timezone_convert",
                    description=f"Converted timestamps timezone to {target_tz}.",
                )
            )

    # 2. Handle missing bars strategy
    strategy = config.cleaning_config.missing_bar_strategy
    if strategy == "drop":
        before_len = len(df)
        df = df.dropna(subset=["open", "high", "low", "close"])
        after_len = len(df)
        if before_len != after_len:
            report.actions.append(
                CleaningAction(
                    action_type="drop_na",
                    description=f"Dropped {before_len - after_len} rows containing missing OHLC values.",
                )
            )
    elif strategy == "forward_fill":
        missing_count = df["close"].isna().sum()
        if missing_count > 0:
            df = df.ffill()
            report.actions.append(
                CleaningAction(
                    action_type="forward_fill",
                    description=f"Forward-filled {missing_count} missing rows.",
                )
            )
    elif strategy == "interpolate":
        missing_count = df["close"].isna().sum()
        if missing_count > 0:
            df = df.interpolate(method="linear")
            report.actions.append(
                CleaningAction(
                    action_type="interpolate",
                    description=f"Interpolated {missing_count} missing rows.",
                )
            )

    # 3. Spread anomalies cleaning
    if "spread" in df.columns:
        anomaly_threshold = config.cleaning_config.spread_anomaly_threshold
        anomalies = df["spread"] > anomaly_threshold
        if anomalies.any():
            count = anomalies.sum()
            df.loc[anomalies, "spread"] = anomaly_threshold
            report.actions.append(
                CleaningAction(
                    action_type="cap_spread",
                    description=f"Capped {count} spread values exceeding threshold {anomaly_threshold}.",
                    column="spread",
                )
            )

    # 4. Validate
    validation_report = validate_dataset(df)
    report.issues.extend(validation_report.issues)

    # 5. Enrich
    enriched_df = enrich_dataset(df)

    metadata = {
        "symbol": config.data_config.symbol,
        "timeframe": config.data_config.timeframe,
        "rows": len(enriched_df),
    }

    return PreparedDataset(
        data=enriched_df,
        quality_report=report,
        metadata=metadata,
    )


class CoreMetricProfile(BaseModel):
    """Core dataset metrics profile."""

    metrics: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def build_core_metric_profile(dataset: PreparedDataset) -> CoreMetricProfile:
    """Build a normalized core metric profile from a prepared dataset."""
    from app.services.research.metrics import MetricContext, build_default_registry

    registry = build_default_registry()
    context = MetricContext(dataset.data, EdgeLabConfig())
    results = registry.calculate_all(context)

    metrics_dict = {name: val.to_dict() for name, val in results.items()}
    return CoreMetricProfile(
        metrics=metrics_dict,
        warnings=[],
        metadata=dataset.metadata,
    )


def build_market_structure_profile(dataset: PreparedDataset) -> Any:
    """Build a directional market-structure profile from a prepared dataset."""
    from app.services.research.studies.structure import (
        resolve_market_structure_profile,
    )

    symbol = dataset.metadata.get("symbol", "EURUSD")
    timeframe = dataset.metadata.get("timeframe", "H1")
    return resolve_market_structure_profile(symbol, timeframe)


def run_seasonality(
    df: pd.DataFrame,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate seasonality statistics for the provided dataset and filters."""
    from app.services.research.helpers import calculate_seasonality_statistics

    return calculate_seasonality_statistics(df, filters)
