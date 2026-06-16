# ruff: noqa: E501, ARG002, PLR2004
"""Volatility indicators: ATR, ADR, and Rolling Volatility.

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


class AverageTrueRange:
    """Average True Range (ATR) volatility indicator."""

    indicator_id = "atr"
    name = "Average True Range"
    version = "1.0.0"
    formula_version = "1.0.0"

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate period >= 1."""
        period = parameters.get("period", 14)
        if not isinstance(period, int) or isinstance(period, bool) or period < 1:
            raise IndicatorParameterError("period must be an integer >= 1.")

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        """ATR requires high, low, close columns."""
        return ["high", "low", "close"]

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        """Return atr_<period>."""
        return [generate_output_column_name(self.indicator_id, parameters, "")]

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
        validate_input_data(data, config, self.required_columns(config.parameters))
        if len(data) < period:
            msg = f"Required {period} rows for ATR calculations, got {len(data)}."
            raise InsufficientDataError(msg)

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        """Compute vectorized ATR."""
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
        # Seed first element
        tr.iloc[0] = high.iloc[0] - low.iloc[0]

        # Smooth using Wilder's smoothing
        atr_series = calculate_wilder_smoothing(tr, period)

        # Build output dataframe
        output_col = self.output_columns(config.parameters)[0]
        res_df = pd.DataFrame(index=data.index)
        res_df["timestamp"] = (
            data.index.get_level_values("timestamp")
            if isinstance(data.index, pd.MultiIndex)
            else data.index
        )
        res_df["symbol"] = symbol
        res_df[output_col] = atr_series

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
        """Execute incremental ATR updates."""
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


class AverageDailyRange:
    """Average Daily Range (ADR) volatility indicator."""

    indicator_id = "adr"
    name = "Average Daily Range"
    version = "1.0.0"
    formula_version = "1.0.0"

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate period >= 1."""
        period = parameters.get("period", 20)
        if not isinstance(period, int) or isinstance(period, bool) or period < 1:
            raise IndicatorParameterError("period must be an integer >= 1.")

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        """ADR requires high, low columns."""
        return ["high", "low"]

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        """Return adr_<period>."""
        return [generate_output_column_name(self.indicator_id, parameters, "")]

    def warmup_requirement(
        self,
        parameters: dict[str, Any],
        timeframe: str,
        calendar: str | None = None,
    ) -> WarmupRequirement:
        """Warmup bars = period - 1."""
        period = parameters.get("period", 20)
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
        period = config.parameters.get("period", 20)
        validate_input_data(data, config, self.required_columns(config.parameters))
        if len(data) < period:
            msg = f"Required {period} rows for ADR calculations, got {len(data)}."
            raise InsufficientDataError(msg)

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        """Compute vectorized ADR."""
        start_time = time.perf_counter()
        self.validate_parameters(config.parameters)
        self.validate_input(data, config, context)

        period = config.parameters.get("period", 20)

        # Read and validate symbol/timeframe metadata
        symbol, timeframe, tf_duration = validate_input_data(
            data, config, self.required_columns(config.parameters)
        )

        daily_range = data["high"] - data["low"]
        adr_series = daily_range.rolling(period).mean()

        # Build output dataframe
        output_col = self.output_columns(config.parameters)[0]
        res_df = pd.DataFrame(index=data.index)
        res_df["timestamp"] = (
            data.index.get_level_values("timestamp")
            if isinstance(data.index, pd.MultiIndex)
            else data.index
        )
        res_df["symbol"] = symbol
        res_df[output_col] = adr_series

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
        """Execute incremental ADR updates."""
        from app.services.indicators.calculations import update_sliding_window_state

        return update_sliding_window_state(
            self, bar, state, config, context, lookback_multiplier=2
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


class RollingVolatility:
    """Rolling Volatility indicator."""

    indicator_id = "rolling_volatility"
    name = "Rolling Volatility"
    version = "1.0.0"
    formula_version = "1.0.0"

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate period >= 2 and return_type."""
        period = parameters.get("period", 20)
        if not isinstance(period, int) or isinstance(period, bool) or period < 2:
            raise IndicatorParameterError("period must be an integer >= 2.")

        ret_type = parameters.get("return_type", "log")
        if ret_type not in ("log", "simple"):
            raise IndicatorParameterError(
                "return_type must be either 'log' or 'simple'."
            )

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        """Rolling volatility requires configured source column."""
        return []

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        """Return rolling_volatility_<period>."""
        src = source or "close"
        return [generate_output_column_name(self.indicator_id, parameters, src)]

    def warmup_requirement(
        self,
        parameters: dict[str, Any],
        timeframe: str,
        calendar: str | None = None,
    ) -> WarmupRequirement:
        """Warmup bars = period."""
        period = parameters.get("period", 20)
        return WarmupRequirement(symbol="*", timeframe=timeframe, lookback_bars=period)

    def validate_input(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> None:
        """Verify quality and data sufficiency."""
        period = config.parameters.get("period", 20)
        validate_input_data(data, config, [])
        # We need period + 1 prices to compute period returns
        if len(data) < period + 1:
            msg = f"Required {period + 1} rows for Volatility calculations, got {len(data)}."
            raise InsufficientDataError(msg)

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        """Compute rolling standard deviation of simple/log returns."""
        start_time = time.perf_counter()
        self.validate_parameters(config.parameters)
        self.validate_input(data, config, context)

        period = config.parameters.get("period", 20)
        src_col = config.source_column

        # Read config options
        ret_type = config.parameters.get("return_type", "log")
        ddof = config.parameters.get("ddof", 1)
        ann_factor = config.parameters.get("ann_factor", 1.0)

        # Validate symbol/timeframe metadata
        symbol, timeframe, tf_duration = validate_input_data(data, config, [])

        series = data[src_col]

        # Calculate returns
        if ret_type == "log":
            returns = np.log(series / series.shift(1))
        else:
            returns = (series - series.shift(1)) / series.shift(1)

        # Calculate standard deviation
        vol_series = returns.rolling(window=period).std(ddof=ddof) * ann_factor

        # Build output dataframe
        output_col = self.output_columns(config.parameters, src_col)[0]
        res_df = pd.DataFrame(index=data.index)
        res_df["timestamp"] = (
            data.index.get_level_values("timestamp")
            if isinstance(data.index, pd.MultiIndex)
            else data.index
        )
        res_df["symbol"] = symbol
        res_df[output_col] = vol_series

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
        """Execute incremental Volatility updates."""
        from app.services.indicators.calculations import update_sliding_window_state

        return update_sliding_window_state(
            self, bar, state, config, context, lookback_multiplier=2
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
