# Shared Utilities (`app/utils`)

## Overview

`app/utils` is the **foundational infrastructure layer** of the HaruQuantAI system. It provides every primitive that upper-layer
domains (live runtime, simulation, risk, strategy, research) depend on for identity generation, envelope formatting, secret
handling, datetime normalization, observability, and authorization — without pulling in domain business logic. Every module is
**import-safe and side-effect-free**: importing a utility file never configures logging, reads environment variables, opens
network connections, or mutates shared state. This guarantee is enforced by design and verified on every CI run.

All 16 modules share a single public contract: other services throughout the application import exclusively from `app.utils`
(e.g. `from app.utils import logger, success_response`) rather than from sub-files directly. Heavy optional dependencies such
as `pandas`, `pydantic-settings`, and `argon2-cffi` are either lazy-loaded on first use or gated behind the `__getattr__`
mechanism in `__init__.py`, keeping the package lightweight. It enforces a deny-by-default authorization model, a UTC-first
timestamp policy, and a deterministic approved error-code registry — all three apply uniformly across every tool boundary.

---

## Design Philosophy & Non-Negotiable Rules

All modules within `app/utils` must adhere strictly to these principles:

1. **Import Safety & Side-Effect Free**: Importing any utility file must never trigger side effects. No logging initialization,
   no database queries, no automatic environment variable reads, and no external network operations.
2. **Standard Library + Safe Imports**: Keep dependency requirements minimal. Heavy third-party imports (like `pandas`) must be
   lazy-loaded or used only in specific dedicated modules (such as `dataframe_tools.py`).
3. **No Domain Business Logic**: Utilities must provide generic infrastructure support (ID generation, schema checking, date
   formatting, structure envelopes). They must **never** contain broker, portfolio, risk management, strategy, or live-trading
   logic.
4. **Unified Entry Point**: All public interfaces must be registered and re-exported in `app/utils/__init__.py`. Other services
   must import from `app/utils` directly, not from sub-files (e.g. `from app.utils import logger`, not
   `from app.utils.logger import logger`).

---

## Features

### [`auth.py`](auth.py) — Authentication & Authorization

Deny-by-default access control and context tracking. Validates `principal_id`, `principal_type`, roles, permissions, and scopes
against immutable `AuthContext` objects. `authorize_action` returns a structured decision without raising;
`require_authorization` raises `SecurityError` on denial.

**Key exports:** `AuthContext`, `AuthorizationDecision`, `PrincipalType`, `DecisionStatus`,
`build_auth_context`, `authorize_action`, `require_authorization`, `validate_auth_context`

---

### [`data_quality.py`](data_quality.py) — OHLCV Data Quality

Non-persisted OHLCV diagnostics for pricing bounds, volume, timestamps, and bar structure. Applies a penalty scoring model
(`critical×40 + error×20 + warning×5 + info×1`). Detects NaN, Infinity, negative prices, flatline candles, zero volume,
OHLC inversion, and symbol mismatches. Pass/fail gate is controlled by configurable `quality_pass_threshold`.

**Key exports:** `QualityProfile`, `QualityIssue`, `prepare_ohlcv_data`, `inspect_ohlcv_quality`, `validate_ohlcv_quality`

---

### [`dataframe_tools.py`](dataframe_tools.py) — DataFrame Utilities

Lazy-loaded pandas utilities for alignment, serialization, grid combinatorics, and bar conversion. All pandas imports are
deferred until first call. Contract aliases (`align_dataframe_time_index`, `chunk_sequence`, `generate_parameter_combinations`,
`bars_to_records`) match the public specification.

**Key exports:** `OHLC_COLUMNS`, `OHLCV_COLUMNS`, `align_dataframe_datetime`, `align_dataframe_time_index`, `bar_to_record`,
`bars_to_records`, `chunk_sequence`, `chunked`, `compare_dataframes`, `compare_ohlc`, `compare_ohlcv`, `dataframe_columns`,
`generate_parameter_combinations`, `iter_dataframe_records`, `parameter_combinations`, `serialize_dataframe_records`

---

### [`errors.py`](errors.py) — Exception Hierarchy & Error Registry

Application-wide deterministic exception hierarchy and approved error-code registry. Covers base utility errors, indicator
domain errors (`IND_*`), strategy domain errors (`STRATEGY_*`), risk errors, simulation errors (`SIM_*`), and live runtime
errors (`LIVE_*`). Includes broker error classification and exponential-backoff retry helpers.

**Key exports:** `APPROVED_ERROR_CODES`, `ERROR_MESSAGES`, `Error`, `ValidationError`, `ConfigurationError`, `SecurityError`,
`DataError`, `ExternalServiceError`, `TradingError`, `TradingTimeoutError`, `UnknownOutcomeError`, `IndicatorError`,
`StrategyError`, `ErrorPayload`, `ErrorRouteResult`, `ErrorRouter`, `normalize_error_code`, `raise_for_invalid_code`,
`error_name`, `message_for`, `code_for_exception`, `details_for_exception`, `exception_to_error_payload`,
`validate_error_payload`, `route_error`, `classify_broker_error`, `trading_retry_delay`, `map_exception_to_strategy_error`

---

### [`event_bus.py`](event_bus.py) — In-Memory Event Bus

Thread-safe bounded in-memory pub/sub bus. Supports idempotency keys, back-pressure (fail-fast or drop-oldest), event
deduplication, and subscriber fan-out. No external message broker dependency. All state lives inside caller-owned instances.

**Key exports:** `EventEnvelope`, `PublishResult`, `InMemoryEventBus`, `build_event_envelope`, `publish_event`

---

### [`identity.py`](identity.py) — Identifier Generation & Validation

Prefix-validated, collision-resistant ULID/UUID identifiers. Validates prefix format, ID structure, and version strings
against compiled regex patterns. Every ID type has a dedicated generator and a matching validator.

**Key exports:** `DEFAULT_VERSION`, `ID_PREFIXES`, `generate_id`, `generate_prefixed_id`, `generate_request_id`,
`generate_workflow_id`, `generate_correlation_id`, `generate_causation_id`, `generate_event_id`, `generate_idempotency_id`,
`validate_id`, `validate_request_id`, `validate_workflow_id`, `ensure_version`

---

### [`logger.py`](logger.py) — Structured Logging

Production-grade structured logging with colorized local output and JSON production format. Supports file rotation,
log-level configuration, and thread-local trace context injection (`request_id`, `workflow_id`, `correlation_id`).

Output format: `timestamp | level | module.submodule.function:line | message`

**Key exports:** `logger`, `configure_logging`, `get_logger`, `set_trace_context`, `clear_trace_context`

---

### [`normalization.py`](normalization.py) — Datetime & UTC Normalization

UTC-first datetime normalization, staleness checks, clock-drift detection, and timestamp sequence validation. All outputs are
UTC-aware `datetime` objects. Naive inputs are assumed UTC. Includes `format_timestamp` alias for cross-module compatibility.

**Key exports:** `UTC`, `DEFAULT_TIMEZONE`, `ClockDriftStatus`, `TimestampIssue`, `utc_now`, `parse_datetime`,
`normalize_timestamp`, `to_utc_datetime`, `to_naive_utc`, `format_utc_timestamp`, `format_timestamp`, `is_stale`,
`check_clock_drift`, `normalize_timestamp_column`, `normalize_timestamp_sequence`, `validate_timestamp_sequence`

---

### [`notifications.py`](notifications.py) — Notification Routing

Throttled, deduplicated notification routing to caller-supplied adapters. Redacts secrets from titles, bodies, and metadata
before dispatch. Supports per-channel throttle windows and deduplication keys. Includes `FakeNotificationAdapter` for tests.

**Key exports:** `NotificationMessage`, `NotificationResult`, `NotificationAdapter`, `FakeNotificationAdapter`,
`NotificationRouter`, `render_notification`, `route_notification`, `broadcast_notification`

---

### [`observability.py`](observability.py) — Metrics & Circuit Breaker

In-memory metric registry, Prometheus text export, clock-drift health checks, and a thread-safe circuit breaker with
`closed`/`open`/`half_open` states. All state is caller-owned with no module globals. Circuit breaker internal state is
private and accessible only through read-only properties. Sensitive keys are filtered from health snapshots via
`SENSITIVE_KEY_PATTERN`.

**Key exports:** `GRAFANA_DASHBOARD_EXPECTATIONS`, `MetricRecord`, `HealthSnapshot`, `MetricRegistry`, `CircuitBreaker`,
`record_metric`, `record_tool_call_metric`, `build_health_snapshot`, `check_clock_drift_health`, `export_prometheus_metrics`

---

### [`paths.py`](paths.py) — Safe Path Utilities

Path normalization, directory creation, and path-traversal protection. All path operations resolve candidates and validate
that results remain inside the declared root boundary before returning.

**Key exports:** `ensure_dir`, `ensure_parent_dir`, `normalize_path`, `safe_join`, `validate_path_within_root`

---

### [`security.py`](security.py) — Cryptography & Secret Redaction

Cryptographic utilities and secret redaction tools. Password hashing attempts Argon2id first and falls back to
PBKDF2-HMAC-SHA256. Fernet symmetric encryption with `InvalidToken` guard. Regex-based sensitive key filtering via
`SENSITIVE_KEY_PATTERN`. Multi-version secret selection with conflict detection.

**Key exports:** `SENSITIVE_KEY_PATTERN`, `MAX_REDACTION_DEPTH`, `SECRET_VERSION_NOT_FOUND`, `RedactionDiagnostics`,
`SecretVersion`, `hash_password`, `verify_password`, `encrypt_text`, `decrypt_text`, `encrypt_value`, `decrypt_value`,
`generate_encryption_key`, `load_encryption_key`, `redact_payload`, `redact_mapping`, `redact_mapping_with_diagnostics`,
`redact_text`, `redact_value`, `classify_secret_key`, `select_active_secret_version`

---

### [`settings.py`](settings.py) — Application Configuration

Pydantic-settings application configuration loaded from environment variables and `.env`. Lazy-loaded via `__getattr__` to
prevent eager dotenv scanning on import. `validate_config` returns a `ValidationResult`-compatible dict rather than raising.

**Key exports:** `Settings`, `settings`, `load_config`, `validate_config`, `HARUQUANT_HOME`, `CONFIGURATION_ERROR`,
`HaruQuantConfigurationError`

---

### [`standard.py`](standard.py) — Standard Envelopes

Standard `{status, message, data, error, metadata}` envelope builders for all official AI tools. Provides deterministic JSON
serialization, metadata construction, OHLCV record validation, metric label validation, alert deduplication, error event
building, and circuit-open responses.

**Key exports:** `StandardResponse`, `StandardEnvelope`, `StandardMetadata`, `ToolMetadata`, `ToolError`, `DataQualityIssue`,
`ErrorEvent`, `AlertDeduplicator`, `build_metadata`, `success_response`, `build_success_response`, `error_response`,
`build_error_response`, `response_from_exception`, `circuit_open_response`, `validate_standard_response`, `canonical_json`,
`stable_identifier`, `get_execution_ms`, `build_data_quality_issue`, `validate_ohlcv_records`, `build_error_event`,
`validate_metric_labels`, `is_official_tool_allowed`

---

### [`validations.py`](validations.py) — Schema & Range Validation

Non-strict JSON schema and numeric range checking. Validates structured packets (evidence packs, approval packets, registry
entries, handoff payloads). Returns `ValidationResult` TypedDicts rather than raising, enabling caller-controlled error
handling.

**Key exports:** `VALIDATION_FAILED`, `VALID_RISK_LEVELS`, `VALID_ENVIRONMENT_MODES`, `ValidationResult`,
`validate_input_schema`, `validate_output_schema`, `validate_numeric_range`, `validate_required_fields`,
`validate_mapping_schema`, `validate_schema_version`, `validate_data_freshness`, `validate_evidence_pack`,
`validate_approval_packet`, `validate_registry_entry`, `validate_handoff_payload`, `validation_failed_paths`

---

## Installation

### Prerequisites

Ensure the parent project dependencies are installed. This package requires:

**Standard library** (no installation needed):
- `hashlib`, `hmac`, `secrets`, `uuid`, `re`, `json`, `math`, `time`, `threading`, `collections`, `dataclasses`, `typing`,
  `importlib`

**Required third-party packages** (installed with the project):
```
cryptography       # Fernet symmetric encryption (encrypt_text / decrypt_text)
pydantic           # TypedDict and model validation
pydantic-settings  # Settings / load_config — lazy-loaded on first access only
```

**Optional third-party packages** (graceful fallback if absent):
```
argon2-cffi   # Argon2id password hashing — falls back to PBKDF2-HMAC-SHA256
pandas        # DataFrame utilities in dataframe_tools.py — lazy-imported
```

Install all project dependencies:

```bash
pip install -r requirements.txt
```

### Integration

Import exclusively from the `app.utils` package, never from sub-files:

```python
# Correct — unified public registry
from app.utils import logger, success_response, build_metadata, ValidationError

# Incorrect — bypasses the registry and violates the design contract
from app.utils.logger import logger             # Do not do this
from app.utils.standard import success_response  # Do not do this
```

---

## Usage Examples

For fully-runnable end-to-end scripts that exercise all feature groups, see:

**[`tests/usage/app/services/01_utils.py`](../../tests/usage/app/services/01_utils.py)**

Run it directly:

```bash
python tests/usage/app/services/01_utils.py
```

The examples below demonstrate each feature group concisely. They match the patterns used in the usage script above.

### Basic Usage

Emit a structured log message and wrap a result in the standard envelope:

```python
from app.utils import logger, build_metadata, success_response

logger.info("Service started", extra={"component": "market_data"})

metadata = build_metadata(tool_name="get_rates_tool")
response = success_response(
    message="Rates loaded.",
    data={"EURUSD": 1.1023},
    metadata=metadata,
)
print(response["status"])   # "success"
print(response["data"])     # {"EURUSD": 1.1023}
```

### Feature Usage

#### Trace Context & Logging

```python
from app.utils import (
    logger, configure_logging, set_trace_context, clear_trace_context,
    generate_request_id, generate_workflow_id, generate_correlation_id,
)

configure_logging(level="INFO")
set_trace_context(
    request_id=generate_request_id(),
    workflow_id=generate_workflow_id(),
    correlation_id=generate_correlation_id(),
)
logger.info("Processing request", extra={"symbol": "EURUSD"})
# 2026-06-21T10:30:00.123Z | INFO | app.service.run:42 | Processing request
clear_trace_context()
```

#### Standard Envelopes

```python
from app.utils import build_metadata, success_response, error_response, response_from_exception

meta = build_metadata(tool_name="fetch_bars", reads=True)

resp = success_response(message="Bars fetched.", data={"count": 100}, metadata=meta)

err = error_response(
    code="VALIDATION_FAILED",
    message="Timeframe M10 is not supported.",
    details="Supported timeframes: M1, M5, M15, H1, H4, D1.",
    metadata=meta,
)

try:
    raise RuntimeError("broker disconnected")
except Exception as exc:
    fail = response_from_exception(exception=exc, metadata=meta)
```

#### Identifiers

```python
from app.utils import (
    generate_request_id, generate_workflow_id, generate_prefixed_id,
    validate_id, validate_request_id,
)

req_id = generate_request_id()          # "req_01j2k..."
wf_id  = generate_workflow_id()         # "wf_01j2k..."
custom = generate_prefixed_id("hedge")  # "hedge_01j2k..."

assert validate_request_id(req_id) == req_id
assert validate_id(custom, expected_prefix="hedge") == custom
```

#### Datetime Normalization

```python
from datetime import timedelta
from app.utils import utc_now, parse_datetime, to_naive_utc, to_utc_datetime, is_stale, format_utc_timestamp

now    = utc_now()
fmt    = format_utc_timestamp(now)   # "2026-06-21T10:30:00.000000Z"
parsed = parse_datetime("2026-06-21T10:00:00Z")
naive  = to_naive_utc(parsed)
aware  = to_utc_datetime(naive)
assert parsed == aware

old_ts = utc_now() - timedelta(minutes=10)
assert is_stale(old_ts, max_age_seconds=300) is True
```

#### Security & Redaction

```python
from app.utils import hash_password, verify_password, generate_encryption_key, encrypt_text, decrypt_text, redact_payload

# Argon2id preferred, PBKDF2-HMAC-SHA256 fallback
h = hash_password("MyPassword123")
assert verify_password("MyPassword123", h) is True

key    = generate_encryption_key()
cipher = encrypt_text("strategy_params_v3", key=key)
plain  = decrypt_text(cipher, key=key)
assert plain == "strategy_params_v3"

safe = redact_payload({"api_key": "sk-abc123", "symbol": "EURUSD"})
# {"api_key": "[REDACTED]", "symbol": "EURUSD"}
```

#### Authorization

```python
from app.utils import (
    build_auth_context, authorize_action, require_authorization,
    generate_request_id, generate_workflow_id,
)

ctx = build_auth_context(
    principal_id="agent-001",
    principal_type="agent",
    roles={"trader"},
    permissions={"market_data:read", "orders:write"},
    scopes={"live"},
    request_id=generate_request_id(),
    workflow_id=generate_workflow_id(),
)

decision = authorize_action(ctx, required_permissions={"orders:write"})
print(decision.allowed)   # True
print(decision.status)    # "allowed"

# Raises SecurityError(AUTHORIZATION_FAILED) when denied
require_authorization(ctx, required_permissions={"admin:delete"})
```

#### Data Quality

```python
import pandas as pd
from app.utils import inspect_ohlcv_quality, validate_ohlcv_quality

df = pd.DataFrame([
    {"timestamp": "2026-06-21T10:00:00Z", "open": 1.10, "high": 1.11, "low": 1.09, "close": 1.105, "volume": 100},
    {"timestamp": "2026-06-21T10:01:00Z", "open": 1.105, "high": 1.12, "low": 1.08, "close": 1.11, "volume": 200},
])

profile = inspect_ohlcv_quality(df, quality_pass_threshold=90.0)
print(profile["passed"])  # True
print(profile["score"])   # 100.0

resp = validate_ohlcv_quality(df, expected_symbol="EURUSD", timeframe="M1")
print(resp["status"])     # "success"
```

#### Event Bus

```python
from app.utils import InMemoryEventBus, build_event_envelope, publish_event

bus = InMemoryEventBus(max_queue_size=500)

def on_signal(envelope):
    print(f"Signal: {envelope['payload']}")

bus.subscribe("strategy.signal", on_signal)
event  = build_event_envelope(
    event_type="strategy.signal",
    source="strategy_runner",
    payload={"action": "BUY", "symbol": "EURUSD", "size": 0.1},
)
result = publish_event(bus, event)
print(result.status)           # "delivered"
print(result.delivered_count)  # 1
```

#### Circuit Breaker & Observability

```python
from app.utils import CircuitBreaker, MetricRegistry, record_tool_call_metric, export_prometheus_metrics

registry = MetricRegistry()
cb = CircuitBreaker(name="broker_feed", failure_threshold=3, cooldown_seconds=30.0, registry=registry)

if cb.allow_request():
    try:
        pass  # broker call
        cb.record_success()
    except Exception:
        cb.record_failure()

record_tool_call_metric(registry, tool_name="get_ticks", status="success", latency_ms=12.4)
print(export_prometheus_metrics(registry))
```

#### Notifications

```python
from app.utils import FakeNotificationAdapter, NotificationRouter, route_notification

adapters = {"desktop": FakeNotificationAdapter(channel="desktop")}
router   = NotificationRouter(adapters=adapters, throttle_seconds=5.0)

result = route_notification(
    router, channel="desktop",
    title="Feed Heartbeat Missed",
    body="EURUSD feed has not ticked in 60 seconds.",
    severity="warning",
    dedupe_key="feed.heartbeat.EURUSD",
)
print(result.status)     # "sent"
print(result.latency_ms)
```

#### Schema Validation

```python
from app.utils import validate_input_schema, validate_numeric_range, ValidationError

schema = {
    "type": "object",
    "properties": {
        "symbol":   {"type": "string", "minLength": 3},
        "quantity": {"type": "number", "minimum": 0.01},
    },
    "required": ["symbol", "quantity"],
}

validate_input_schema({"symbol": "EURUSD", "quantity": 1.5}, schema)  # OK

try:
    validate_input_schema({"symbol": "EU", "quantity": -1}, schema)
except ValidationError as exc:
    print(exc)

validate_numeric_range(0.05, min_value=0.01, max_value=1.0, field_name="lot_size")
```

#### Safe Paths

```python
from pathlib import Path
from app.utils import ensure_parent_dir, safe_join, validate_path_within_root

base      = Path("/data/haruquant")
safe_path = safe_join(base, "raw", "EURUSD", "2026.csv")

ensure_parent_dir(safe_path)   # creates parent directories if absent

try:
    safe_join(base, "../../etc/passwd")
except ValueError:
    print("traversal blocked")
```

### Advanced Usage / Edge Cases

#### Lazy Settings Access

`settings.py` is never imported eagerly. Dotenv scanning triggers only on first attribute access:

```python
import os
os.environ["HARUQUANT_HOME"] = "/opt/haruquant"

from app.utils import settings, validate_config

cfg    = settings   # triggers dotenv scan once; subsequent accesses are cached
result = validate_config(cfg)
if not result["valid"]:
    print(result["details"])   # {"errors": ["..."]}
```

#### Argon2id → PBKDF2 Hash Format Detection

`verify_password` automatically routes by hash prefix:

```python
from app.utils import hash_password, verify_password

h = hash_password("secret")
# "$argon2id$..." if argon2-cffi is installed, else "pbkdf2_sha256$..."
assert verify_password("secret", h) is True
assert verify_password("wrong",  h) is False
```

#### Error Router with Deduplication Window

```python
from app.utils import InMemoryEventBus, ErrorRouter

bus    = InMemoryEventBus()
router = ErrorRouter(bus=bus, dedupe_window_seconds=60.0)

exc = ValueError("DB write failed")
r1  = router.route_error(error=exc, source="data_writer")  # "routed"
r2  = router.route_error(error=exc, source="data_writer")  # "suppressed"
```

#### Circuit Breaker Half-Open Probe

```python
import time
from app.utils import CircuitBreaker

cb = CircuitBreaker(name="test", failure_threshold=2, cooldown_seconds=0.1)
cb.record_failure()
cb.record_failure()
assert cb.state == "open"

time.sleep(0.15)
allowed = cb.allow_request()   # True — transitions to "half_open"
assert cb.state == "half_open"

cb.record_success()            # closes the circuit
assert cb.state == "closed"
```

#### Broadcast to Multiple Notification Channels

```python
from app.utils import FakeNotificationAdapter, NotificationRouter, broadcast_notification

adapters = {
    "desktop": FakeNotificationAdapter(channel="desktop"),
    "email":   FakeNotificationAdapter(channel="email"),
}
router  = NotificationRouter(adapters=adapters)
results = broadcast_notification(
    router,
    channels=["desktop", "email"],
    title="Kill Switch Triggered",
    body="All live positions have been closed.",
    severity="critical",
)
for r in results:
    print(r.channel, r.status)
```

#### Alert Deduplication

```python
from app.utils import AlertDeduplicator

dedup = AlertDeduplicator(window_seconds=30.0, max_entries=64)
assert dedup.allow("feed.stale.EURUSD") is True
assert dedup.allow("feed.stale.EURUSD") is False   # suppressed within window
```

---

## API Reference

### StandardResponse Schema

Every official tool response wraps its payload in this five-key envelope:

```python
{
    "status":   "success" | "error",
    "message":  str,
    "data":     object | None,                        # None on error
    "error":    {"code": str, "details": str} | None, # None on success
    "metadata": {
        "tool_name":         str,
        "tool_version":      str,
        "tool_category":     str,
        "tool_risk_level":   "low" | "medium" | "high" | "critical",
        "request_id":        str | None,
        "execution_ms":      float,
        "reads":             bool,
        "writes":            bool,
        "updates":           bool,
        "deletes":           bool,
        "trades":            bool,
        "requires_network":  bool,
        "read_only":         bool,
        "writes_file":       bool,
        "modifies_database": bool,
        "places_trade":      bool,
    },
}
```

### Error Hierarchy

```
Error
├── ValidationError          (VALIDATION_FAILED)
│   ├── ToolError            (TOOL_EXECUTION_FAILED)
│   ├── IndicatorError       (IND_* codes)
│   ├── StrategyError        (STRATEGY_* codes)
│   └── RiskError            (risk-specific codes)
├── ConfigurationError       (SERVICE_UNAVAILABLE)
├── SecurityError            (PERMISSION_DENIED)
├── DataError                (DATA_NOT_FOUND)
└── ExternalServiceError     (SERVICE_UNAVAILABLE)
    └── TradingError         (BROKER_UNAVAILABLE)
        ├── TradingTimeoutError   (TIMEOUT)
        └── UnknownOutcomeError   (CIRCUIT_OPEN)
```

### Key Envelope Builders (`standard.py`)

| Function | Returns | Description |
| :--- | :--- | :--- |
| `build_metadata(tool_name, ...)` | `StandardMetadata` | Build required tool metadata |
| `success_response(message, data, metadata)` | `StandardResponse` | Wrap a successful result |
| `error_response(code, message, details, metadata)` | `StandardResponse` | Wrap a known validation or execution error |
| `response_from_exception(exception, metadata)` | `StandardResponse` | Map a caught exception to an error envelope |
| `circuit_open_response(metadata, ...)` | `StandardResponse` | Fail-fast circuit-open error envelope |
| `validate_standard_response(response)` | `None` | Assert envelope structure and metadata are valid |
| `canonical_json(payload)` | `str` | Deterministic JSON with sorted keys and compact separators |
| `stable_identifier(payload, prefix)` | `str` | Reproducible SHA-256 fingerprint identifier |

### Secret Redaction Policy

Production code must **never** log or expose the following in any envelope, log line, or event payload:

- Passwords or password hashes
- API keys, broker credentials, or authorization headers
- Encryption keys or Fernet tokens
- Raw approval packets or private evidence payloads
- Telegram bot tokens or notification provider credentials

Use `redact_payload(mapping)` or `redact_text(string)` at every system boundary where external data enters.

---

## Testing

### Usage / Integration Script

The full end-to-end demonstration covering all 12 feature groups is at:

```
tests/usage/app/services/01_utils.py
```

Run it directly:

```bash
python tests/usage/app/services/01_utils.py
```

Expected output ends with:

```
==================================================
DEMO SCRIPT EXECUTED SUCCESSFULLY
==================================================
```

### Unit Tests

Run the dedicated unit test suite for this module:

```bash
# Run all utils unit tests
pytest tests/unit/app/utils/ -v

# Run a specific module
pytest tests/unit/app/utils/test_standard.py -v
pytest tests/unit/app/utils/test_errors.py -v
pytest tests/unit/app/utils/test_security.py -v
```

### Import Safety Verification

Confirm the package produces no side effects on import:

```bash
python -c "import app.utils; print('import-safe: OK')"
```
