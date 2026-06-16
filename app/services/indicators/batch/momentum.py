# ruff: noqa: E501, ARG002
"""Momentum indicators: RSI and Williams %R.

All implementations conform to the IndicatorProtocol contract.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd

from app.services.indicators.calculations import (
    build_result_manifest,
    calculate_wilder_smoothing,
    generate_output_column_name,
    validate_input_data,
)
from app.services.indicators.protocols import (
    IndicatorConfig,
    IndicatorContext,
    IndicatorResult,
    IndicatorState,
    WarmupRequirement,
)
from app.utils.errors import (
    IndicatorParameterError,
    InsufficientDataError,
)


class RelativeStrengthIndex:
    """Relative Strength Index (RSI) momentum indicator."""

    indicator_id = "rsi"
    name = "Relative Strength Index"
    version = "1.0.0"
    formula_version = "1.0.0"

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate period >= 1."""
        period = parameters.get("period", 14)
        if not isinstance(period, int) or isinstance(period, bool) or period < 1:
            raise IndicatorParameterError("period must be an integer >= 1.")

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        """RSI requires configured source column."""
        return []

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        """Return rsi_<period>."""
        src = source or "close"
        return [generate_output_column_name(self.indicator_id, parameters, src)]

    def warmup_requirement(
        self,
        parameters: dict[str, Any],
        timeframe: str,
        calendar: str | None = None,
    ) -> WarmupRequirement:
        """Warmup bars = period."""
        period = parameters.get("period", 14)
        return WarmupRequirement(symbol="*", timeframe=timeframe, lookback_bars=period)

    def validate_input(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> None:
        """Verify quality and data sufficiency."""
        period = config.parameters.get("period", 14)
        validate_input_data(data, config, [])
        if len(data) < period + 1:
            msg = f"Required {period + 1} rows for RSI calculations (price diff needs 1 extra row), got {len(data)}."
            raise InsufficientDataError(msg)

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        """Compute vectorized RSI with Wilder smoothing."""
        start_time = time.perf_counter()
        self.validate_parameters(config.parameters)
        self.validate_input(data, config, context)

        period = config.parameters.get("period", 14)
        src_col = config.source_column

        # Read and validate symbol/timeframe metadata
        symbol, timeframe, tf_duration = validate_input_data(data, config, [])

        series = data[src_col]
        diff = series.diff()

        gain = diff.clip(lower=0.0)
        loss = (-diff).clip(lower=0.0)

        # Skip the first NaN row for smoothing calculations
        avg_gain = calculate_wilder_smoothing(gain.iloc[1:], period)
        avg_loss = calculate_wilder_smoothing(loss.iloc[1:], period)

        # Align series back to index
        avg_gain = avg_gain.reindex(data.index)
        avg_loss = avg_loss.reindex(data.index)

        # Compute RSI
        is_nan = avg_gain.isna() | avg_loss.isna()
        rsi_vals = np.where(
            (avg_loss == 0.0) & (avg_gain == 0.0),
            50.0,
            np.where(
                avg_loss == 0.0,
                100.0,
                100.0 - (100.0 / (1.0 + (avg_gain / avg_loss))),
            ),
        )
        rsi_series = pd.Series(np.where(is_nan, np.nan, rsi_vals), index=data.index)

        # Build output dataframe
        output_col = self.output_columns(config.parameters, src_col)[0]
        res_df = pd.DataFrame(index=data.index)
        res_df["timestamp"] = (
            data.index.get_level_values("timestamp")
            if isinstance(data.index, pd.MultiIndex)
            else data.index
        )
        res_df["symbol"] = symbol
        res_df[output_col] = rsi_series

        # Set available_at metadata
        res_df["available_at"] = res_df["timestamp"] + tf_duration
        res_df["quality"] = data["quality"] if "quality" in data.columns else "good"

        # Manifest
        manifest = build_result_manifest(
            self.indicator_id,
            self.version,
            self.formula_version,
            config,
            data,
            res_df,
            [output_col],
            symbol,
            timeframe,
            start_time,
        )

        return IndicatorResult(
            values=res_df,
            output_columns=[output_col],
            manifest=manifest,
        )

    def update(
        self,
        bar: dict[str, Any],
        state: IndicatorState,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> tuple[IndicatorResult, IndicatorState]:
        """Execute incremental RSI updates."""
        from app.services.indicators.calculations import update_sliding_window_state

        return update_sliding_window_state(
            self, bar, state, config, context, lookback_multiplier=3
        )

    def serialize_state(self, state: IndicatorState) -> str:
        """Serialize state object to string."""
        from app.services.indicators.calculations import serialize_indicator_state

        return serialize_indicator_state(state)

    def deserialize_state(
        self, payload: str, expected_parameter_hash: str | None = None
    ) -> IndicatorState:
        """Restore state object from string."""
        from app.services.indicators.calculations import deserialize_indicator_state

        return deserialize_indicator_state(
            payload,
            self.indicator_id,
            self.version,
            expected_parameter_hash=expected_parameter_hash,
        )


class WilliamsR:
    """Williams %R momentum indicator."""

    indicator_id = "williams_r"
    name = "Williams %R"
    version = "1.0.0"
    formula_version = "1.0.0"

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate period >= 1."""
        period = parameters.get("period", 14)
        if not isinstance(period, int) or isinstance(period, bool) or period < 1:
            raise IndicatorParameterError("period must be an integer >= 1.")

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        """Williams %R requires high, low, close columns."""
        return ["high", "low", "close"]

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        """Return williams_r_<period>."""
        return [generate_output_column_name(self.indicator_id, parameters, "")]

    def warmup_requirement(
        self,
        parameters: dict[str, Any],
        timeframe: str,
        calendar: str | None = None,
    ) -> WarmupRequirement:
        """Warmup bars = period - 1."""
        period = parameters.get("period", 14)
        return WarmupRequirement(
            symbol="*", timeframe=timeframe, lookback_bars=period - 1
        )

    def validate_input(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> None:
        """Verify quality and data sufficiency."""
        period = config.parameters.get("period", 14)
        validate_input_data(data, config, self.required_columns(config.parameters))
        if len(data) < period:
            msg = (
                f"Required {period} rows for Williams %R calculations, got {len(data)}."
            )
            raise InsufficientDataError(msg)

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        """Compute vectorized Williams %R."""
        start_time = time.perf_counter()
        self.validate_parameters(config.parameters)
        self.validate_input(data, config, context)

        period = config.parameters.get("period", 14)

        # Read and validate symbol/timeframe metadata
        symbol, timeframe, tf_duration = validate_input_data(
            data, config, self.required_columns(config.parameters)
        )

        high = data["high"]
        low = data["low"]
        close = data["close"]

        hh = high.rolling(period).max()
        ll = low.rolling(period).min()

        # Williams %R formula: -100 * (HighestHigh - Close) / (HighestHigh - LowestLow)
        # Handle division by zero when hh == ll: output NaN
        range_diff = hh - ll
        williams_series = np.where(
            range_diff > 0.0, -100.0 * (hh - close) / range_diff, np.nan
        )
        williams_series = pd.Series(williams_series, index=data.index)

        # Build output dataframe
        output_col = self.output_columns(config.parameters)[0]
        res_df = pd.DataFrame(index=data.index)
        res_df["timestamp"] = (
            data.index.get_level_values("timestamp")
            if isinstance(data.index, pd.MultiIndex)
            else data.index
        )
        res_df["symbol"] = symbol
        res_df[output_col] = williams_series

        # Set available_at metadata
        res_df["available_at"] = res_df["timestamp"] + tf_duration
        res_df["quality"] = data["quality"] if "quality" in data.columns else "good"

        # Manifest
        manifest = build_result_manifest(
            self.indicator_id,
            self.version,
            self.formula_version,
            config,
            data,
            res_df,
            [output_col],
            symbol,
            timeframe,
            start_time,
        )

        return IndicatorResult(
            values=res_df,
            output_columns=[output_col],
            manifest=manifest,
        )

    def update(
        self,
        bar: dict[str, Any],
        state: IndicatorState,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> tuple[IndicatorResult, IndicatorState]:
        """Execute incremental Williams %R updates."""
        from app.services.indicators.calculations import update_sliding_window_state

        return update_sliding_window_state(
            self, bar, state, config, context, lookback_multiplier=1
        )

    def serialize_state(self, state: IndicatorState) -> str:
        """Serialize state object to string."""
        from app.services.indicators.calculations import serialize_indicator_state

        return serialize_indicator_state(state)

    def deserialize_state(
        self, payload: str, expected_parameter_hash: str | None = None
    ) -> IndicatorState:
        """Restore state object from string."""
        from app.services.indicators.calculations import deserialize_indicator_state

        return deserialize_indicator_state(
            payload,
            self.indicator_id,
            self.version,
            expected_parameter_hash=expected_parameter_hash,
        )
