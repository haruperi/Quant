# ruff: noqa: ARG002, PD011
"""Trend indicators: SMA, EMA, and ADX.

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


class SimpleMovingAverage:
    """Simple Moving Average (SMA) indicator."""

    indicator_id = "sma"
    name = "Simple Moving Average"
    version = "1.0.0"
    formula_version = "1.0.0"

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate period >= 1."""
        period = parameters.get("period", 10)
        if not isinstance(period, int) or isinstance(period, bool) or period < 1:
            raise IndicatorParameterError("period must be an integer >= 1.")

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        """SMA requires configured source column."""
        return []

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        """Return sma_<period> or sma_<source>_<period>."""
        src = source or "close"
        return [generate_output_column_name(self.indicator_id, parameters, src)]

    def warmup_requirement(
        self,
        parameters: dict[str, Any],
        timeframe: str,
        calendar: str | None = None,
    ) -> WarmupRequirement:
        """Warmup bars = period - 1."""
        period = parameters.get("period", 10)
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
        period = config.parameters.get("period", 10)
        validate_input_data(data, config, [])
        if len(data) < period:
            msg = f"Required {period} rows for SMA calculations, got {len(data)}."
            raise InsufficientDataError(msg)

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        """Compute vectorized SMA."""
        start_time = time.perf_counter()
        self.validate_parameters(config.parameters)
        self.validate_input(data, config, context)

        period = config.parameters.get("period", 10)
        src_col = config.source_column

        # Read and validate symbol/timeframe metadata
        symbol, timeframe, tf_duration = validate_input_data(data, config, [])

        # Vectorized calculation
        series = data[src_col]
        sma_series = series.rolling(period).mean()

        # Build output dataframe
        output_col = self.output_columns(config.parameters, src_col)[0]
        res_df = pd.DataFrame(index=data.index)
        res_df["timestamp"] = (
            data.index.get_level_values("timestamp")
            if isinstance(data.index, pd.MultiIndex)
            else data.index
        )
        res_df["symbol"] = symbol
        res_df[output_col] = sma_series

        # Set available_at metadata: close time of the bar
        res_df["available_at"] = res_df["timestamp"] + tf_duration

        # Data quality propagation
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
        """Execute incremental SMA updates."""
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


class ExponentialMovingAverage:
    """Exponential Moving Average (EMA) indicator."""

    indicator_id = "ema"
    name = "Exponential Moving Average"
    version = "1.0.0"
    formula_version = "1.0.0"

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate period >= 1."""
        period = parameters.get("period", 10)
        if not isinstance(period, int) or isinstance(period, bool) or period < 1:
            raise IndicatorParameterError("period must be an integer >= 1.")

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        """EMA requires configured source column."""
        return []

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        """Return ema_<period> or ema_<source>_<period>."""
        src = source or "close"
        return [generate_output_column_name(self.indicator_id, parameters, src)]

    def warmup_requirement(
        self,
        parameters: dict[str, Any],
        timeframe: str,
        calendar: str | None = None,
    ) -> WarmupRequirement:
        """Warmup bars = period - 1."""
        period = parameters.get("period", 10)
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
        period = config.parameters.get("period", 10)
        validate_input_data(data, config, [])
        if len(data) < period:
            msg = f"Required {period} rows for EMA calculations, got {len(data)}."
            raise InsufficientDataError(msg)

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        """Compute vectorized EMA with SMA seeding."""
        start_time = time.perf_counter()
        self.validate_parameters(config.parameters)
        self.validate_input(data, config, context)

        period = config.parameters.get("period", 10)
        src_col = config.source_column

        # Read and validate symbol/timeframe metadata
        symbol, timeframe, tf_duration = validate_input_data(data, config, [])

        series = data[src_col]
        vals = series.values
        ema_vals = np.full(len(series), np.nan)

        if len(series) >= period:
            # Seed with SMA of the first period elements
            sma_val = series.iloc[:period].mean()
            ema_vals[period - 1] = sma_val
            alpha = 2.0 / (period + 1)

            for i in range(period, len(series)):
                if np.isnan(vals[i]):
                    ema_vals[i] = np.nan
                elif np.isnan(ema_vals[i - 1]):
                    # Re-seed if previous value was NaN
                    sub = vals[max(0, i - period + 1) : i + 1]
                    valid = sub[~np.isnan(sub)]
                    if len(valid) >= period:
                        ema_vals[i] = valid.mean()
                else:
                    ema_vals[i] = vals[i] * alpha + ema_vals[i - 1] * (1.0 - alpha)

        ema_series = pd.Series(ema_vals, index=series.index)

        # Build output dataframe
        output_col = self.output_columns(config.parameters, src_col)[0]
        res_df = pd.DataFrame(index=data.index)
        res_df["timestamp"] = (
            data.index.get_level_values("timestamp")
            if isinstance(data.index, pd.MultiIndex)
            else data.index
        )
        res_df["symbol"] = symbol
        res_df[output_col] = ema_series

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
        """Execute incremental EMA updates."""
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


class AverageDirectionalIndex:
    """Average Directional Index (ADX) indicator."""

    indicator_id = "adx"
    name = "Average Directional Index"
    version = "1.0.0"
    formula_version = "1.0.0"

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate period >= 1."""
        period = parameters.get("period", 14)
        if not isinstance(period, int) or isinstance(period, bool) or period < 1:
            raise IndicatorParameterError("period must be an integer >= 1.")

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        """ADX requires high, low, close columns."""
        return ["high", "low", "close"]

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        """Return adx_<period>, plus_di_<period>, minus_di_<period>."""
        period = parameters.get("period", 14)
        return [f"adx_{period}", f"plus_di_{period}", f"minus_di_{period}"]

    def warmup_requirement(
        self,
        parameters: dict[str, Any],
        timeframe: str,
        calendar: str | None = None,
    ) -> WarmupRequirement:
        """Warmup bars = 2 * period - 1."""
        period = parameters.get("period", 14)
        return WarmupRequirement(
            symbol="*", timeframe=timeframe, lookback_bars=2 * period - 1
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
        # ADX requires 2 * period to compute
        min_bars = 2 * period - 1
        if len(data) < min_bars:
            msg = f"Required {min_bars} rows for ADX calculations, got {len(data)}."
            raise InsufficientDataError(msg)

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        """Compute vectorized ADX."""
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

        # Compute True Range (TR)
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        # First row high - low
        tr.iloc[0] = high.iloc[0] - low.iloc[0]

        # Compute DM+ and DM-
        high_diff = high - high.shift(1)
        low_diff = low.shift(1) - low

        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)

        # Convert to series and set first element to NaN as diff is undefined
        plus_dm = pd.Series(plus_dm, index=data.index)
        minus_dm = pd.Series(minus_dm, index=data.index)
        plus_dm.iloc[0] = np.nan
        minus_dm.iloc[0] = np.nan

        # Smooth TR, +DM, -DM using Wilder smoothing
        str_series = calculate_wilder_smoothing(tr, period)
        s_plus_dm = calculate_wilder_smoothing(plus_dm, period)
        s_minus_dm = calculate_wilder_smoothing(minus_dm, period)

        # Compute +DI and -DI
        # Avoid division by zero: if STR is zero or NaN, DI is NaN
        # Use np.where
        plus_di = np.where(str_series > 0, 100.0 * (s_plus_dm / str_series), np.nan)
        minus_di = np.where(str_series > 0, 100.0 * (s_minus_dm / str_series), np.nan)

        # Compute DX
        di_sum = plus_di + minus_di
        di_diff = np.abs(plus_di - minus_di)
        dx = np.where(
            np.isnan(di_sum),
            np.nan,
            np.where(di_sum > 0, 100.0 * (di_diff / di_sum), 0.0),
        )
        dx_series = pd.Series(dx, index=data.index)

        # Compute ADX as Wilder smoothing of DX
        adx_series = calculate_wilder_smoothing(dx_series, period)

        # Build output dataframe
        output_cols = self.output_columns(config.parameters)
        res_df = pd.DataFrame(index=data.index)
        res_df["timestamp"] = (
            data.index.get_level_values("timestamp")
            if isinstance(data.index, pd.MultiIndex)
            else data.index
        )
        res_df["symbol"] = symbol
        res_df[output_cols[0]] = adx_series
        res_df[output_cols[1]] = plus_di
        res_df[output_cols[2]] = minus_di

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
            output_cols,
            symbol,
            timeframe,
            start_time,
        )

        return IndicatorResult(
            values=res_df,
            output_columns=output_cols,
            manifest=manifest,
        )

    def update(
        self,
        bar: dict[str, Any],
        state: IndicatorState,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> tuple[IndicatorResult, IndicatorState]:
        """Execute incremental ADX updates."""
        from app.services.indicators.calculations import update_sliding_window_state

        return update_sliding_window_state(
            self, bar, state, config, context, lookback_multiplier=5
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
