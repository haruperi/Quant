# Shared Utilities (`app/utils`)

A collection of import-safe, side-effect-free utility primitives that form the foundational layer of the **HaruQuantAI** system.

---

## 1. Design Philosophy & Non-Negotiable Rules

All modules within `app/utils` must adhere strictly to these principles:

1. **Import Safety & Side-Effect Free**: Importing any utility file must never trigger side effects. This means **no** logging configuration initialization, **no** database queries, **no** automatic environment variable reads, and **no** external network operations.
2. **Standard library + Safe Imports**: Keep dependency requirements minimal. Heavy third-party imports (like `pandas`) must be lazy-loaded or used only in specific dedicated modules (such as `dataframe_tools.py`).
3. **No Domain Business Logic**: Utilities must provide generic infrastructure support (such as ID generation, schema checking, date formatting, and structure envelopes). They must **never** contain broker, portfolio, risk management, strategy, or live-trading business logic.
4. **Unified Entry Point**: All public interfaces must be registered and re-exported in `app/utils/__init__.py`. Other services inside the application must import from `app/utils` directly, rather than referencing sub-files (e.g., use `from app.utils import logger`, not `from app.utils.logger import logger`).

---

## 2. Module Directory

| Module | Primary Purpose & Features | Key Primitives & Functions |
| :--- | :--- | :--- |
| [`auth.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/auth.py) | Deny-by-default access control and context context tracking. | `AuthContext`, `AuthorizationDecision`, `authorize_action`, `require_authorization` |
| [`data_quality.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/data_quality.py) | Non-persisted diagnostics for data shapes, pricing bounds, and volumes. | `QualityProfile`, `QualityIssue`, `inspect_ohlcv_quality`, `validate_ohlcv_quality` |
| [`dataframe_tools.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/dataframe_tools.py) | Lazy-loaded utilities for Pandas DataFrames, grid parameters, and alignment. | `align_dataframe_datetime`, `compare_ohlcv`, `chunked`, `parameter_combinations` |
| [`error_routing.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/error_routing.py) | Routing sanitized exceptions to event tracks with caller-owned buses. | `ErrorRouter`, `ErrorRouteResult`, `route_error` |
| [`errors.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/errors.py) | Application-wide exception hierarchy and deterministic error-code registry. | `Error`, `ValidationError`, `DataError`, `SecurityError`, `exception_to_error_payload` |
| [`event_bus.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/event_bus.py) | Thread-safe, bounded, in-memory publisher-subscriber event bus. | `InMemoryEventBus`, `EventEnvelope`, `build_event_envelope`, `publish_event` |
| [`identity.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/identity.py) | Prefix-validated, collision-resistant ULID/UUID identifiers. | `generate_request_id`, `generate_workflow_id`, `generate_causation_id`, `validate_id` |
| [`logger.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/logger.py) | Production JSON/local colorized logging, rotation, and trace propagation. | `logger`, `configure_logging`, `set_trace_context`, `clear_trace_context` |
| [`normalization.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/normalization.py) | Timezone-aware UTC-first conversions, staleness checks, and sequence checks. | `UTC`, `ClockDriftStatus`, `normalize_timestamp`, `is_stale`, `check_clock_drift` |
| [`notifications.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/notifications.py) | Throttled, deduplicated alert routing to simulated notification channels. | `NotificationRouter`, `NotificationMessage`, `broadcast_notification` |
| [`observability.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/observability.py) | Circuit breakers, in-memory metrics counters, and Prometheus exporters. | `CircuitBreaker`, `MetricRegistry`, `record_metric`, `export_prometheus_metrics` |
| [`paths.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/paths.py) | Directory validation, path normalization, and path traversal protections. | `ensure_dir`, `ensure_parent_dir`, `normalize_path` |
| [`settings.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/settings.py) | Explicit, immutable runtime settings loading with deterministic precedence. | `RuntimeSettings`, `LoggingSettings`, `load_runtime_settings`, `inject_runtime_settings` |
| [`security.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/core/security.py) | Public utility security helpers implemented in `app.core.security` and re-exported through `app.utils`. | `redact_payload`, `redact_mapping_with_diagnostics`, `hash_password`, `encrypt_value`, `select_active_secret_version` |
| [`validations.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/validations.py) | Non-strict JSON Schema / Pydantic constraints checking and numeric ranges. | `validate_input_schema`, `validate_output_schema`, `validate_numeric_range` |
| [`standard.py`](file:///c:/Users/rharu/Documents/MyApplications/Quant/app/utils/standard.py) | Standard envelope formatting builders for tools, API calls, and errors. | `StandardEnvelope`, `success_response`, `error_response`, `response_from_exception` |

---

## 3. Key Design Patterns & Usage Examples

### 3.1 Trace-Context & Logging (`logger.py`)

Always use the re-exported `logger` for telemetry. To associate logs across module boundaries, configure trace contexts using `set_trace_context`.

```python
from app.utils import logger, set_trace_context, clear_trace_context

# Initialize context at gateway entry
set_trace_context(
    request_id="req_1234abcd",
    workflow_id="wf_5678efgh",
    correlation_id="corr_9012ijkl"
)

logger.info("Processing gateway request", extra={"symbol": "EURUSD"})
# Output (JSON in production, colorized string locally):
# {"message": "Processing gateway request", "request_id": "req_1234abcd", "symbol": "EURUSD", ...}

# Clear context when exiting execution thread
clear_trace_context()
```

### 3.2 Standard Responses & Envelopes (`standard.py`)

All official AI tools and APIs wrap their payloads in a `StandardEnvelope` structure. Use envelope builders to normalize success and error states:

```python
from app.utils import success_response, error_response, response_from_exception

# Success envelope
response = success_response(
    data={"bars": [{"timestamp": "2026-06-16T10:00:00Z", "close": 1.1023}]},
    message="Successfully fetched bars",
    tool_name="get_market_data",
    execution_time_ms=12.4
)

# Error envelope
fail_response = error_response(
    code="VALIDATION_FAILED",
    message="Timeframe M10 is not supported",
    tool_name="get_market_data"
)

# Automatically build envelope from caught exception
try:
    raise ValueError("DB disk full")
except Exception as e:
    err_envelope = response_from_exception(e, tool_name="save_market_data")
```

### 3.3 Structured Error Registry & Checks (`errors.py`)

Ensure exceptions use a code registered in `APPROVED_ERROR_CODES`:

```python
from app.utils import ValidationError, raise_for_invalid_code

# Raise standard exceptions
if not symbol:
    raise ValidationError("Symbol must not be empty", code="INVALID_INPUT")

# Verify code eligibility
raise_for_invalid_code("DB_CONNECTION_ERROR")  # OK
# raise_for_invalid_code("BAD_SOMETHING")      # Raises ValidationError
```

### 3.4 Bounded Event Bus Pub/Sub (`event_bus.py`)

An in-memory event bus useful for routing internal diagnostics, clock checks, or telemetry updates asynchronously:

```python
from app.utils import InMemoryEventBus, build_event_envelope, publish_event

bus = InMemoryEventBus(max_queue_size=1000)

# Register a subscriber
@bus.subscribe("data.heartbeat")
def handle_heartbeat(envelope):
    print(f"Received heartbeat event: {envelope.event_id}")

# Publish an event
event = build_event_envelope(
    event_type="data.heartbeat",
    source_module="scheduler",
    payload={"status": "running"}
)
publish_event(bus, event)
```

### 3.5 Circuit Breakers & Observability (`observability.py`)

Implement circuit breaking to defend adapters against transient connection storms:

```python
from app.utils import CircuitBreaker, record_metric

cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=10)

def fetch_data():
    if not cb.allow_request():
        # Circuit is open
        record_metric("gateway.requests.circuit_blocked", 1)
        return None

    try:
        # Call external broker API
        result = broker_client.get_ticks()
        cb.record_success()
        return result
    except Exception as e:
        cb.record_failure()
        raise e
```
