# Indicators Service

The Indicators Service is a contract-driven, auditable, and type-safe module designed for quantitative trading research and execution. It provides robust calculations for trend, momentum, and volatility indicators, featuring built-in caching, execution tracing, canary routing, lookahead prevention, and dynamic indicator registration.

---

## 1. Directory Structure

```text
app/services/indicators/
├── __init__.py             # Public module interface exports
├── calculations.py         # Topological sorting and composition execution
├── errors.py               # Indicator-specific typed exceptions
├── protocols.py            # Interfaces, metadata classes, and schemas
├── py.typed                # PEP 561 typing marker
├── registry.py             # Global indicator registration and execution gateway
├── adapters/               # Core execution adapters
│   ├── __init__.py
│   ├── audit.py            # Calculation audit trails and logs
│   ├── cache.py            # Thread-safe calculation caching
│   ├── canary.py           # Feature-flagged and canary routing comparisons
│   ├── observability.py    # SLO tracking, latencies, and alerts metrics
│   └── tracing.py          # Distributed W3C trace propagation
├── batch/                  # Concrete batch calculations
│   ├── __init__.py
│   ├── momentum.py         # RSI, Williams %R, ADX
│   ├── trend.py            # SMA, EMA
│   └── volatility.py       # ATR, ADR, Rolling Volatility
└── incremental/            # Dynamic/streaming calculations stubs
    ├── __init__.py
    ├── accumulators.py
    └── state.py
```

---

## 2. Core Concepts & Abstractions

### `IndicatorProtocol`
All indicators (built-in and custom) must implement the `IndicatorProtocol` interface. This ensures strict conformance for calculation signatures, dynamic validation, schema verification, and state serialization.

```python
class IndicatorProtocol(Protocol):
    indicator_id: str
    name: str
    version: str
    formula_version: str
    status: str
    dependencies: list[str]

    def validate_parameters(self, parameters: dict[str, Any]) -> None: ...
    def required_columns(self, parameters: dict[str, Any]) -> list[str]: ...
    def output_columns(self, parameters: dict[str, Any], source: str | None = None, naming_policy: str | None = None) -> list[str]: ...
    def warmup_requirement(self, parameters: dict[str, Any], timeframe: str, calendar: str | None = None) -> WarmupRequirement: ...
    def validate_input(self, data: pd.DataFrame, config: IndicatorConfig, context: IndicatorContext | None = None) -> None: ...
    def calculate(self, data: pd.DataFrame, config: IndicatorConfig, context: IndicatorContext | None = None) -> IndicatorResult: ...
    def update(self, bar: dict[str, Any], state: IndicatorState, config: IndicatorConfig, context: IndicatorContext | None = None) -> tuple[IndicatorResult, IndicatorState]: ...
    def serialize_state(self, state: IndicatorState) -> str: ...
    def deserialize_state(self, payload: str, expected_parameter_hash: str | None = None) -> IndicatorState: ...
```

### `IndicatorConfig`
Configuration schema defining indicator-specific inputs, execution modes, conflict resolutions, and feature flags.

* **`indicator_id`**: The unique identifier of the indicator to run.
* **`parameters`**: Key-value pairs configured for the calculations.
* **`source_column`**: Override standard inputs (e.g., run SMA on `high` instead of `close`).
* **`column_conflict_policy`**: Strategy when output column exists in the dataset (`fail`, `overwrite`, or `suffix`).
* **`is_partial`**: Flag indicating if lookahead checks should adapt to incomplete bars.
* **`allow_deprecated`**: Feature flag allowing the execution of deprecated indicators.

### `IndicatorResult`
The envelope returned by calculations. It encapsulates:
* **`values`**: The output `pd.DataFrame` containing computed columns and the lookahead-prevention `available_at` column.
* **`output_columns`**: Lists of names of the generated columns.
* **`manifest`**: Detailed metadata including input/output checksums, timing statistics, and parameter hashes.
* **`errors`**: Handled diagnostic errors (when `error_mode="result"` is selected).

---

## 3. Built-In Indicators

| Indicator | ID | Category | Parameters | Description |
|---|---|---|---|---|
| **Simple Moving Average** | `sma` | Trend | `period` (default: 10) | Basic average of the last $N$ close prices. |
| **Exponential Moving Average** | `ema` | Trend | `period` (default: 10) | Weighted moving average giving more weight to recent prices. |
| **Average True Range** | `atr` | Volatility | `period` (default: 14) | Measure of market volatility calculated from High/Low/Close. |
| **Average Daily Range** | `adr` | Volatility | `period` (default: 14) | Volatility metric based on daily High/Low spans. |
| **Rolling Volatility** | `rolling_volatility` | Volatility | `period` (default: 20) | Standard deviation of close percent changes. |
| **Relative Strength Index** | `rsi` | Momentum | `period` (default: 14) | Momentum oscillator measuring speed and change of price movements. |
| **Williams %R** | `williams_r` | Momentum | `period` (default: 14) | Momentum indicator measuring overbought and oversold levels. |
| **Average Directional Index** | `adx` | Momentum | `period` (default: 14) | Trend strength indicator combining +DI and -DI. |

---

## 4. Execution Adapters

The registry wraps all calculations in a resilient pipeline populated by adapters:

1. **Caching (`cache.py`)**: Stores calculated datasets in an in-memory thread-safe structure, keyed by input data hashes and parameter configurations.
2. **Auditing (`audit.py`)**: Emits structured log entries detailing calculation boundaries, duration, and data checksums for strict audit trails.
3. **Tracing (`tracing.py`)**: Supports W3C distributed tracing context propagation to track executions across data fetching and strategy consumption boundaries.
4. **Canary Routing (`canary.py`)**: Safely routes workflows, symbols, or users to alternative "candidate" implementations. Compares precision outputs and latency benchmarks side-by-side, suggesting rollbacks without altering production values unless explicitly opted in.
5. **SLO Metrics (`observability.py`)**: Collects latency metrics and failure rates to route alerts when calculation durations exceed service-level objective limits.

---

## 5. Usage Examples

Complete examples are available in the integration script [03_indicator.py](file:///c:/Users/rharu/Documents/MyApplications/Quant/tests/usage/app/services/03_indicator.py).

### 5.1 Simple Calculation & Joining
```python
import pandas as pd
from app.services.indicators import ema

# Sample dataframe containing OHLCV
data = pd.DataFrame({
    "open": [1.12, 1.13, 1.12, 1.14, 1.15],
    "high": [1.13, 1.14, 1.13, 1.15, 1.16],
    "low": [1.11, 1.12, 1.11, 1.13, 1.14],
    "close": [1.12, 1.13, 1.12, 1.14, 1.15],
    "volume": [100.0, 150.0, 120.0, 200.0, 180.0]
}, index=pd.date_range("2026-06-16T10:00:00Z", periods=5, freq="5min"))

# Calculate EMA
result = ema(data, period=3)

# Join results back to original data safely
joined_df = result.join_to(data, mode="copy")
print(joined_df[["close", "ema_3", "available_at"]])
```

### 5.2 Composed DAG Execution
For complex multi-stage indicator systems, `execute_indicator_composition` evaluates execution dependencies, orders calculations topologically, and propagates the strict lookahead `available_at` timestamp.

```python
from app.services.indicators import execute_indicator_composition, IndicatorConfig

configs = [
    IndicatorConfig(indicator_id="sma", parameters={"period": 3}),
    IndicatorConfig(indicator_id="rsi", parameters={"period": 3})
]

# Run topological composition
results = execute_indicator_composition(data, configs)
print("Computed columns:", list(results.columns))
```

### 5.3 Lookahead Prevention
Calculations automatically construct an `available_at` timestamp for each row representing the exact time that bar closed. Strategies can filter data dynamically using this timestamp to avoid indexing future information:

```python
# Say the strategy evaluates decisions at 10:10:00
decision_time = pd.Timestamp("2026-06-16T10:10:00Z")

# Filter only accessible data
accessible_data = joined_df[joined_df["available_at"] <= decision_time]
```

### 5.4 Custom Indicator Registration
New custom indicators can be dynamically registered after passing conformance audits:

```python
from app.services.indicators import register_indicator, validate_indicator, IndicatorProtocol

class CustomMomentum(IndicatorProtocol):
    indicator_id = "custom_mom"
    name = "Custom Momentum"
    version = "1.0.0"
    formula_version = "1.0.0"
    status = "official"
    dependencies = ["numpy", "pandas"]

    # Implement all protocol validate, required_columns, calculate, and state methods...

# Verify conformance
validation = validate_indicator(CustomMomentum)
if validation.valid:
    register_indicator(CustomMomentum)
    print("Custom indicator registered successfully!")
```

---

## 6. Verification and Testing

To run the unit test suite and verify coverage gates:
```powershell
.venv\Scripts\pytest
```

To run lint checks and static type analysis:
```powershell
.venv\Scripts\python -m ruff check app/services/indicators/
.venv\Scripts\python -m mypy app/services/indicators/
```
