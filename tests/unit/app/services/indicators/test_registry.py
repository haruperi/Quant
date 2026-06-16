# ruff: noqa: E501, PD011, PT018, NPY002, DTZ001, ARG002, RUF012, RUF100
"""Unit tests for the indicator registry and convenience wrappers."""

from typing import Any

import pandas as pd
import pytest
from app.services.indicators import (
    IndicatorConfig,
    IndicatorContext,
    IndicatorError,
    IndicatorManifest,
    IndicatorResult,
    WarmupRequirement,
    adr,
    atr,
    ema,
    get_indicator,
    list_indicators,
    register_indicator,
    rolling_volatility,
    rsi,
    sma,
    unregister_indicator,
    validate_indicator,
    williams_r,
)
from app.services.indicators.errors import (
    InsufficientDataError,
    MissingRequiredColumnError,
    UnsupportedIndicatorError,
)
from app.utils.errors import ValidationError

from tests.unit.app.services.indicators.test_trend import generate_mock_ohlcv


class DummyIndicator:
    """Mock custom indicator class conforming to structural typing protocols."""

    indicator_id = "dummy"
    name = "Dummy Custom Indicator"
    version = "1.0.0"
    formula_version = "1.0.0"
    status = "official"
    dependencies = ["numpy", "pandas"]

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        pass

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        return ["close"]

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        return ["dummy_output"]

    def warmup_requirement(
        self,
        parameters: dict[str, Any],
        timeframe: str,
        calendar: str | None = None,
    ) -> WarmupRequirement:
        return WarmupRequirement("symbol", timeframe, 0)

    def validate_input(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> None:
        pass

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        res_df = pd.DataFrame(index=data.index)
        res_df["dummy_output"] = 42.0
        return IndicatorResult(
            values=res_df,
            output_columns=["dummy_output"],
            manifest=IndicatorManifest(indicator_id="dummy"),
        )


def test_custom_indicator_registration_lifecycle():
    """Verify custom indicators can be validated, registered, run, and unregistered."""
    # Step 1: Validate conformance
    val = validate_indicator(DummyIndicator)
    assert val.valid

    # Step 2: Register
    register_indicator(DummyIndicator)
    assert "dummy" in list_indicators(None)

    # Step 3: Fetch constructor and calculate
    df = generate_mock_ohlcv(5)
    constructor = get_indicator("dummy")
    inst = constructor()
    res = inst.calculate(df, IndicatorConfig(indicator_id="dummy"))
    assert (res.values["dummy_output"] == 42.0).all()

    # Step 4: Unregister
    unregister_indicator("dummy")
    assert "dummy" not in list_indicators(None)

    with pytest.raises(UnsupportedIndicatorError):
        get_indicator("dummy")


def test_convenience_wrappers():
    """Verify built-in convenience wrappers call calculations correctly."""
    df = generate_mock_ohlcv(20, constant_price=1.2000)

    # test sma
    res_sma = sma(df, period=5)
    assert "sma_5" in res_sma.output_columns
    assert (res_sma.values["sma_5"].dropna() == 1.2000).all()

    # test ema
    res_ema = ema(df, period=5)
    assert "ema_5" in res_ema.output_columns
    assert (res_ema.values["ema_5"].dropna() == 1.2000).all()

    # test rsi
    res_rsi = rsi(df, period=5)
    assert "rsi_close_5" in res_rsi.output_columns
    assert (res_rsi.values["rsi_close_5"].dropna() == 50.0).all()

    # test atr
    res_atr = atr(df, period=5)
    assert "atr_5" in res_atr.output_columns

    # test adr
    res_adr = adr(df, period=5)
    assert "adr_5" in res_adr.output_columns

    # test volatility
    res_vol = rolling_volatility(df, period=5)
    assert "rolling_volatility_close_5" in res_vol.output_columns

    # test williams_r
    res_wr = williams_r(df, period=5)
    assert "williams_r_5" in res_wr.output_columns


def test_error_mode_result():
    """Verify calculation failures map to results instead of exceptions when error_mode='result'."""
    df = generate_mock_ohlcv(5)  # too short for period=10

    # Under 'exception' mode, raises error
    with pytest.raises(IndicatorError) as exc_info:
        sma(df, period=10, error_mode="exception")
    assert exc_info.value.code == "IND_INSUFFICIENT_DATA"

    # Under 'result' mode, returns IndicatorResult with errors
    res = sma(df, period=10, error_mode="result")
    assert len(res.errors) == 1
    assert res.errors[0].code == "IND_INSUFFICIENT_DATA"
    assert res.values.empty


def test_join_to_validation_and_features():
    """Verify join_to functionality, collision checks, values_only, and fallback modes."""
    df = generate_mock_ohlcv(20)
    res = sma(df, period=5)

    # 1. Normal join with DatetimeIndex
    joined = res.join_to(df, mode="copy")
    assert len(joined) == 20
    assert "sma_5" in joined.columns
    assert (joined.index == df.index).all()

    # 2. values_only property
    v_only = res.values_only
    assert list(v_only.columns) == [
        "timestamp",
        "symbol",
        "sma_5",
        "available_at",
        "quality",
    ]

    # 3. Input validations
    with pytest.raises(ValidationError) as exc:
        res.join_to("not a dataframe")
    assert exc.value.code == "INVALID_INPUT"

    with pytest.raises(ValidationError) as exc:
        res.join_to(df, mode="invalid")
    assert exc.value.code == "INVALID_INPUT"

    # 4. Column collision
    df_collision = df.copy()
    df_collision["sma_5"] = 1.0
    with pytest.raises(ValidationError) as exc:
        res.join_to(df_collision)
    assert exc.value.code == "IND_OUTPUT_COLUMN_CONFLICT"

    # 5. Positional index fallback alignment (when symbol and timestamp are missing)
    df_no_meta = df.drop(columns=["symbol"])
    df_no_meta.index.name = None

    res_no_meta = IndicatorResult(
        values=res.values.drop(columns=["symbol", "timestamp"]),
        output_columns=res.output_columns,
        manifest=res.manifest,
    )
    joined_pos = res_no_meta.join_to(df_no_meta)
    assert "sma_5" in joined_pos.columns
    assert len(joined_pos) == 20

    # Collision in positional fallback
    df_collision_pos = df_no_meta.copy()
    df_collision_pos["sma_5"] = 2.0
    with pytest.raises(ValidationError) as exc:
        res_no_meta.join_to(df_collision_pos)
    assert exc.value.code == "IND_OUTPUT_COLUMN_CONFLICT"


def test_calculations_input_validations():
    """Verify input validation edge cases and structure checks in the calculations engine."""
    # 1. Empty dataset check
    with pytest.raises(InsufficientDataError):
        sma(pd.DataFrame(), period=5)

    # 2. Missing source column
    df = generate_mock_ohlcv(20)
    with pytest.raises(MissingRequiredColumnError):
        sma(df, period=5, source="non_existent")

    # 3. Naive timezone index
    df_naive = df.copy()
    df_naive.index = df_naive.index.tz_localize(None)
    with pytest.raises(ValidationError):
        sma(df_naive, period=5)

    # 4. Non-DatetimeIndex
    df_no_dt = df.copy()
    df_no_dt.index = range(len(df_no_dt))
    with pytest.raises(ValidationError):
        sma(df_no_dt, period=5)

    # 5. MultiIndex missing levels
    df_bad_mi = df.copy()
    df_bad_mi.index = pd.MultiIndex.from_tuples(
        [(i, i) for i in range(len(df_bad_mi))], names=["a", "b"]
    )
    with pytest.raises(ValidationError):
        sma(df_bad_mi, period=5)

    # 6. Valid MultiIndex execution
    df_mi = df.copy()
    df_mi = df_mi.set_index(["symbol", df_mi.index])
    res_mi = sma(df_mi, period=5)
    assert "sma_5" in res_mi.output_columns
    assert len(res_mi.values) == 20


def test_calculations_input_validations_expanded():
    """Verify other validation failures inside validate_input_data."""
    df = generate_mock_ohlcv(20)

    # 7. Duplicate timestamps
    df_dup = df.copy()
    df_dup.index = [df.index[0]] * len(df)
    with pytest.raises(ValidationError):
        sma(df_dup, period=5)

    # 8. Non-monotonic timestamps
    df_non_mono = df.copy()
    new_idx = list(df.index)
    new_idx[0], new_idx[1] = new_idx[1], new_idx[0]
    df_non_mono.index = new_idx
    with pytest.raises(ValidationError):
        sma(df_non_mono, period=5)

    # 9. Invalid OHLC
    df_bad_ohlc = df.copy()
    df_bad_ohlc.loc[df.index[0], "low"] = df_bad_ohlc.loc[df.index[0], "high"] + 10.0
    with pytest.raises(ValidationError):
        sma(df_bad_ohlc, period=5)


def test_calculation_helpers():
    """Verify helpers in calculations.py to cover edge cases and reach 80% coverage."""
    from datetime import datetime

    import numpy as np
    from app.services.indicators.calculations import (
        calculate_wilder_smoothing,
        normalize_to_utc,
        parse_timeframe_to_timedelta,
    )
    from app.services.indicators.errors import IndicatorParameterError
    from app.utils.errors import ValidationError

    # 1. parse_timeframe_to_timedelta
    assert parse_timeframe_to_timedelta("H1") == pd.Timedelta(hours=1)
    assert parse_timeframe_to_timedelta("D1") == pd.Timedelta(days=1)
    assert parse_timeframe_to_timedelta("W1") == pd.Timedelta(weeks=1)
    assert parse_timeframe_to_timedelta("MN") == pd.Timedelta(days=30)
    assert parse_timeframe_to_timedelta("MN2") == pd.Timedelta(days=60)

    with pytest.raises(IndicatorParameterError):
        parse_timeframe_to_timedelta("invalid")
    with pytest.raises(IndicatorParameterError):
        parse_timeframe_to_timedelta("M")

    # 2. normalize_to_utc
    naive = datetime(2026, 6, 16, 10, 0, 0)
    assert normalize_to_utc(naive).tzinfo is not None
    assert normalize_to_utc("2026-06-16T10:00:00").tzinfo is not None

    with pytest.raises(ValidationError):
        normalize_to_utc(12345)
    with pytest.raises(ValidationError):
        normalize_to_utc("invalid date")

    # 3. calculate_wilder_smoothing edge cases
    s = pd.Series([1.0, 2.0, np.nan, 4.0])
    res_s = calculate_wilder_smoothing(s, 2)
    assert len(res_s) == 4

    # short series
    s_short = pd.Series([1.0])
    res_short = calculate_wilder_smoothing(s_short, 5)
    assert res_short.isna().all()
