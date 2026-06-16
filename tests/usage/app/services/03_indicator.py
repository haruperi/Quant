"""Usage examples for the HaruQuantAI indicator service.

Demonstrates executing calculations, checking manifests, joining columns,
preventing lookahead via available_at, validation checks, and error modes.
"""

# ruff: noqa: E501, E402, BLE001, NPY002, PD011, C901, RUF012, ARG002
import sys
from pathlib import Path

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[4])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from app.services.data import get_data
from app.services.indicators import (
    IndicatorConfig,
    IndicatorContext,
    IndicatorError,
    IndicatorManifest,
    IndicatorResult,
    IndicatorState,
    WarmupRequirement,
    ema,
    get_indicator,
    list_indicators,
    register_indicator,
    sma,
    validate_indicator,
)


def generate_ohlcv_sample(rows: int = 30) -> pd.DataFrame:
    """Fetch real EURUSD H1 bars from MT5, falling back to synthetic data if MT5 is unavailable."""
    try:
        print("Attempting to fetch real EURUSD H1 bars from MT5...")
        records = get_data(
            symbol="EURUSD",
            timeframe="H1",
            data_kind="ohlcv",
            source="mt5",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-06T00:00:00Z",
        )
        if len(records) >= rows:
            df = pd.DataFrame(records)
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.set_index("timestamp")
            df = df.sort_index()

            if "quality" not in df.columns:
                df["quality"] = "good"

            df = df.iloc[:rows].copy()
            print(f"Successfully loaded {len(df)} real bars from MT5.")
            return df
        print(
            f"MT5 returned only {len(records)} bars (needed {rows}). Falling back to synthetic."
        )
    except Exception as e:
        print(f"Failed to fetch data from MT5: {e}. Falling back to synthetic.")

    start_time = datetime(2026, 6, 16, 10, 0, 0, tzinfo=UTC)
    timestamps = [start_time + timedelta(minutes=5 * i) for i in range(rows)]

    np.random.seed(100)
    close_prices = np.cumprod(1.0 + np.random.normal(0, 0.002, rows)) * 1.1200
    high_prices = close_prices * 1.002
    low_prices = close_prices * 0.998
    open_prices = close_prices * 0.999
    volume = np.random.randint(100, 500, rows).astype(float)

    df = pd.DataFrame(
        {
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": volume,
            "quality": ["good"] * rows,
            "symbol": ["EURUSD"] * rows,
            "timeframe": ["M5"] * rows,
        },
        index=pd.DatetimeIndex(timestamps, name="timestamp"),
    )
    return df


def demo_calculations_and_manifests() -> None:
    """Demonstrate basic calculation execution and inspecting output manifest metadata."""
    print("\n--- 1. Calculations & Manifests Demo ---")
    data = generate_ohlcv_sample(25)

    # Calculate 10-period SMA
    result = sma(data, period=10)
    print(f"Computed Output Columns: {result.output_columns}")

    # Inspect manifest details
    manifest = result.manifest
    print(f"Manifest Version:    {manifest.manifest_version}")
    print(f"Indicator ID:        {manifest.indicator_id}")
    print(f"Parameter Hash:      {manifest.parameter_hash}")
    print(f"Input Checksum:      {manifest.input_checksum}")
    print(f"Output Checksum:     {manifest.output_checksum}")
    print(f"Calculation Timing:  {manifest.timing}")


def demo_joining_results() -> None:
    """Demonstrate alignment and joining of values back to original dataframe."""
    print("\n--- 2. Result Joining Demo ---")
    data = generate_ohlcv_sample(25)

    # Calculate 10-period EMA
    res_ema = ema(data, period=10)

    # Join results to original input dataset
    joined = res_ema.join_to(data, mode="copy")
    print(f"Original Columns: {list(data.columns)}")
    print(f"Joined Columns:   {list(joined.columns)}")

    # Verify rows matches exactly
    assert len(data) == len(joined)
    print("Alignment checked: joined row sizes match input exactly.")

    # Print the DataFrame showing open, high, low, close, calculated EMA, and available_at timestamp
    print("\nJoined Dataframe Output (Last 10 rows):")
    print(joined[["open", "high", "low", "close", "ema_10", "available_at"]].tail(10))


def demo_lookahead_prevention() -> None:
    """Demonstrate strategy consumption filter using available_at timestamps."""
    print("\n--- 3. Lookahead Prevention Demo ---")
    data = generate_ohlcv_sample(10)

    res_sma = sma(data, period=5)
    values = res_sma.values

    # Say the strategy is making decisions at the open of the 4th bar
    decision_time = data.index[3].to_pydatetime()

    # Filter values available at or before decision time
    available_data = values[values["available_at"] <= decision_time]
    print(f"Decision Time:             {decision_time}")
    print(f"Total computed rows:       {len(values)}")
    print(f"Strategy-accessible rows:  {len(available_data)}")

    # Accessible rows must not contain timestamps >= 10:15 (i.e. indices >= 3)
    inaccessible = available_data[available_data["timestamp"] >= decision_time]
    assert inaccessible.empty
    print(
        "Lookahead checked: Strategy only accessed bars fully closed before decision time."
    )


def demo_error_modes() -> None:
    """Demonstrate differences in exception vs result error handling modes."""
    print("\n--- 4. Error Modes Demo ---")
    data = generate_ohlcv_sample(5)  # too short for period=10

    # Mode A: exception (default)
    try:
        sma(data, period=10, error_mode="exception")
    except IndicatorError as exc:
        print(f"Caught expected exception (code={exc.code}): {exc}")

    # Mode B: result (does not raise, populates error structures)
    res = sma(data, period=10, error_mode="result")
    print(f"Result returned with success flag: {res.values.empty}")
    print(
        f"Result Errors:                     {res.errors[0].code} - {res.errors[0].message}"
    )


def demo_custom_indicator_registration() -> None:
    """Demonstrate dynamic registration and conformance checks of custom indicators."""
    print("\n--- 5. Custom Indicator Registration Demo ---")

    class CustomMomentum:
        indicator_id = "custom_mom"
        name = "Custom Momentum"
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
            return ["custom_mom_out"]

        def warmup_requirement(
            self,
            parameters: dict[str, Any],
            timeframe: str,
            calendar: str | None = None,
        ) -> WarmupRequirement:
            return WarmupRequirement("*", timeframe, 1)

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
            res_df["custom_mom_out"] = data["close"] * 2.0
            return IndicatorResult(
                values=res_df,
                output_columns=["custom_mom_out"],
                manifest=IndicatorManifest(indicator_id="custom_mom"),
            )

        def update(
            self,
            bar: dict[str, Any],
            state: IndicatorState,
            config: IndicatorConfig,
            context: IndicatorContext | None = None,
        ) -> tuple[IndicatorResult, IndicatorState]:
            raise NotImplementedError

        def serialize_state(self, state: IndicatorState) -> str:
            raise NotImplementedError

        def deserialize_state(
            self, payload: str, expected_parameter_hash: str | None = None
        ) -> IndicatorState:
            raise NotImplementedError

    # Validate conformance
    val = validate_indicator(CustomMomentum)
    print(f"Custom indicator is valid: {val.valid} ({val.message})")

    if val.valid:
        register_indicator(CustomMomentum)
        print("Indicator registered.")
        print(f"Currently registered: {list_indicators(None)}")

        # Fetch and compute
        data = generate_ohlcv_sample(5)
        constructor = get_indicator("custom_mom")
        inst = constructor()
        res = inst.calculate(data, IndicatorConfig(indicator_id="custom_mom"))
        print(f"Custom indicator output:\n{res.values[['custom_mom_out']]}")


if __name__ == "__main__":
    print("==================================================")
    print("STARTING INDICATOR SERVICE USAGE DEMO (03_indicator.py)")
    print("==================================================")

    demo_calculations_and_manifests()
    demo_joining_results()
    demo_lookahead_prevention()
    demo_error_modes()
    demo_custom_indicator_registration()

    print("==================================================")
    print("DEMO SCRIPT EXECUTED SUCCESSFULLY")
    print("==================================================")
