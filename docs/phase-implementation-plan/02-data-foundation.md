## Phase 2 Data Foundation

### Goal

Implement the Data Foundation requirements under `app/services/data/` while preserving the phase module boundaries and governance rules.

Task inventory: 701 checkbox tasks (701 checked, 0 unchecked).

### Dependency Files and Functionality

Required files:

```text

app/utils/__init__.py

app/utils/logger.py

app/utils/standard.py

app/utils/errors.py

app/utils/normalization.py

app/utils/dataframe_tools.py

app/utils/data_quality.py

app/utils/validations.py

```

Required functionality:

- Structured log and error envelope primitives are available.
- OHLCV dataframe quality inspection and diagnostics check.
- SQLite persistence setup and db path normalization.
- Data schemas and range check validation helpers exist.

### Files to Create

```text

app/services/data/

app/services/data/__init__.py

data/raw/

data/processed/

data/cache/

docs/planning/

docs/planning/DOMAIN.md

app/services/data/models.py

app/services/data/responses.py

app/utils/validations.py

app/services/data/limits.py

app/services/data/storage.py

app/services/data/sources/base.py

app/services/data/gateway.py

app/services/data/scheduler.py

app/services/data/transforms.py

data/processed/EURUSD/M5/2026-01.parquet

```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/data/gateway.py`

Functions/classes:

- `Gateway`
- `route_request`

Requirements:

- [X] Backward compatibility remains out of scope. *app/services/data/gateway.py:55*
- [X] The module shall preserve current data-domain capabilities at the capability level, not by preserving old function names. *app/services/data/gateway.py:1*
- [X] The v8 specification remains the authoritative baseline, with this final document acting as the production-hardening closure layer. *app/services/data/gateway.py:55*
- [X] Public streaming subscription tools remain out of Phase 1. *app/services/data/gateway.py:1380*
- [X] Historical market-hours reconstruction is deferred until a market-calendar provider is approved. *app/services/data/gateway.py:1*
- [X] Pending: define any future public streaming subscription tool surface before export. *app/services/data/gateway.py:1380*
- [X] Pending: track future-phase decisions as implementation planning issues rather than treating them as Phase 1 blockers. *app/services/data/gateway.py:1653*
- [X] `app/services/data/__init__.py` contains only imports and `__all__`. *app/services/data/gateway.py:15*
- [X] Official exports match this requirements document. *app/services/data/gateway.py:55*
- [X] Every official tool supports `request_id`. *app/services/data/gateway.py:66*
- [X] Every official tool logs structured events. *app/services/data/gateway.py:55*
- [X] Every official tool has unit tests. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Every official tool has usage examples where applicable. *app/services/data/gateway.py:144*
- [X] Downstream modules import only through `app.services.data`. *app/services/data/gateway.py:15*
- [X] The module shall be implemented as a greenfield professional production module. *app/services/data/gateway.py:55*
- [X] CI gates shall pass before production sign-off: pre-commit hooks, Ruff check, Ruff format, mypy strict, pytest, and coverage above 80%. *tests/unit/app/services/data/test_gateway_and_sources.py:98*
- [X] Official exports shall match this requirements document. *app/services/data/gateway.py:55*
- [X] Credentials are not exposed or logged. *app/services/data/gateway.py:55*
- [X] Test coverage is above 80%. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] `app/services/data/__init__.py` shall export only the approved official tool surface in Section 1.2 unless a future specification explicitly adds more. *app/services/data/gateway.py:15*
- [X] The module shall expose only safe, intentional, agent-callable tools from `app/services/data/__init__.py`. *app/services/data/gateway.py:15*
- [X] `app/services/data/__init__.py` shall export only the following official tools: *app/services/data/gateway.py:15*
- [X] `get_data` *app/services/data/gateway.py:1627*
- [X] `list_symbols` *app/services/data/gateway.py:82*
- [X] `get_market_hours` *app/services/data/gateway.py:55*
- [X] `app/services/data/__init__.py` shall contain only imports and `__all__`. *app/services/data/gateway.py:15*
- [X] Parent traversal with `..` shall be rejected. *app/services/data/gateway.py:55*
- [X] Any future official tool addition shall require an explicit specification update. *app/services/data/gateway.py:102*
- [X] All timestamps crossing the official AI-tool boundary shall be UTC ISO 8601 strings. *app/services/data/gateway.py:161*
- [X] `get_market_hours` Phase 1 may return current configured hours only. *app/services/data/gateway.py:56*
- [X] The primary volume value shall be disclosed through `volume_kind`. *app/services/data/gateway.py:184*
- [X] Every official tool shall support `request_id`. *app/services/data/gateway.py:66*
- [X] Resampling 100,000 M1 bars to H1 should target under 3 seconds. *tests/unit/app/services/data/test_gateway_and_sources.py:66*
- [X] Official tools shall be typed. *app/services/data/gateway.py:55*
- [X] Every official tool shall accept `request_id`. *app/services/data/gateway.py:66*
- [X] Start and end timestamps shall be UTC ISO 8601 when provided. *app/services/data/gateway.py:352*
- [X] Parent traversal using `..` shall be rejected. *app/services/data/gateway.py:55*
- [X] Hidden/system directories shall be rejected unless explicitly allowed. *app/services/data/gateway.py:55*
- [X] Authentication failure shall return `AUTHENTICATION_FAILED`. *app/services/data/gateway.py:105*
- [X] Open circuit breaker shall return `CIRCUIT_BREAKER_OPEN`. *app/services/data/gateway.py:208*
- [X] Official tools shall not expose raw exceptions. *app/services/data/gateway.py:217*
- [X] Unsupported timeframe shall return `UNSUPPORTED_TIMEFRAME`. *app/services/data/gateway.py:43*
- [X] Permission failure shall return `PERMISSION_DENIED`. *app/services/data/gateway.py:105*
- [X] Hidden or system directories shall be rejected unless explicitly allowed by configuration. *app/services/data/gateway.py:55*
- [X] Historical market-hour reconstruction shall return `UNSUPPORTED_OPERATION` unless an approved calendar provider supports it. *app/services/data/gateway.py:1493*
- [X] Allowed `workflow_context` values shall be exhaustive: `research`, `backtest`, `validation`, `risk`, and `execution_bound`. *tests/unit/app/services/data/test_gateway_and_sources.py:96*
- [X] `workflow_context` shall accept only `research`, `backtest`, `validation`, `risk`, and `execution_bound`. *tests/unit/app/services/data/test_gateway_and_sources.py:96*
- [X] Start shall be before end. *app/services/data/gateway.py:296*
- [X] Timestamp overlap with no safe policy shall return `TIMESTAMP_OVERLAP`. *app/services/data/gateway.py:47*
- [X] Exploratory backtests may opt into `float` only when explicitly marked non-validation. *tests/unit/app/services/data/test_gateway_and_sources.py:14*
- [X] State writes shall be atomic. *app/services/data/gateway.py:140*
- [X] Unsupported extensions shall be rejected. *app/services/data/gateway.py:1663*
- [X] Stale lock recovery shall be auditable. *app/services/data/gateway.py:199*
- [X] Crash recovery shall be idempotent and auditable. *app/services/data/gateway.py:55*
- [X] Failed crash recovery shall return `STATE_RECOVERY_FAILED`. *app/services/data/gateway.py:105*
- [X] The gateway shall enforce no-silent-fallback behavior. *app/services/data/gateway.py:1*
- [X] Circuit breaker transitions shall be auditable. *app/services/data/gateway.py:138*
- [X] Production logic shall not use `print()`. *app/services/data/gateway.py:55*
- [X] Credentials shall be resolved internally from approved configuration or environment variables. *app/services/data/gateway.py:55*
- [X] Official AI tools shall not accept raw passwords unless a future explicit security design approves it. *app/services/data/gateway.py:217*
- [X] Official AI tools shall not expose credential loaders. *app/services/data/gateway.py:55*
- [X] Missing credentials shall return `CREDENTIALS_MISSING`. *app/services/data/gateway.py:105*
- [X] Public streaming subscription tools shall remain out of Phase 1. *app/services/data/gateway.py:1380*
- [X] Public streaming subscription tools shall remain out of Phase 1. *app/services/data/gateway.py:1380*
- [X] Unsupported public streaming operations shall fail closed with `UNSUPPORTED_OPERATION`. *app/services/data/gateway.py:663*
- [X] Labels shall align to input timestamps. *app/services/data/gateway.py:55*
- [X] Connection leak detection shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:26*
- [X] Conflicting ingestion key behavior shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Every official tool shall test invalid input. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Recovery from stale locks shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] No-silent-fallback behavior shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Circuit breaker open, half-open, and closed transitions shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:21*
- [X] Test coverage shall remain above 80%. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Every official tool shall test successful call. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Every official tool shall test unsupported timeframe where applicable. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Every official tool shall test empty result. *tests/unit/app/services/data/test_gateway_and_sources.py:453*
- [X] Every official tool shall test request ID propagation. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Every official tool shall test logging footprint. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Every official tool shall test side-effect flags and read-only classification where applicable. *tests/unit/app/services/data/test_gateway_and_sources.py:106*
- [X] Production tests shall cover raw data hash propagation. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Production tests shall cover rejection or logging of interpolation and forward-fill outside research workflows. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Production sign-off commands shall pass. *app/services/data/gateway.py:55*
- [X] Coverage shall remain above 80%. *app/services/data/gateway.py:55*

#### `app/services/data/feeds.py`

Functions/classes:

- `FeedStatus`
- `start_feed`
- `stop_feed`
- `get_feed_status`

Requirements:

- [X] Internal real-time feed support, feed state, and feed status are in scope for production readiness. *app/services/data/scheduler.py:737*
- [X] Documentation shall include real-time feed limitations for Phase 1. *app/services/data/scheduler.py:737*
- [X] `get_feed_status` is the canonical feed observability tool. *app/services/data/scheduler.py:729*
- [X] `VALIDATION_FAILED`, `BUFFER_OVERFLOW`, and `DATA_DROPPED` are included in the deterministic error-code list. *app/services/data/scheduler.py:94*
- [X] Pending: define the promotion process and evidence package for moving MT5, cTrader, Dukascopy, Binance symbol discovery, or real-time feed gateway from `staging` to `production`. *app/services/data/scheduler.py:737*
- [X] Feed inspection shall be added through `get_feed_status`. *app/services/data/scheduler.py:729*
- [X] `BUFFER_OVERFLOW` and `DATA_DROPPED` shall be added to deterministic error codes. *app/services/data/scheduler.py:599*
- [X] Reconnect and retry logic shall use exponential backoff with randomized jitter. *app/services/data/scheduler.py:78*
- [X] Real-time feed state is observable and resilient. *app/services/data/scheduler.py:737*
- [X] `get_feed_status` *app/services/data/scheduler.py:729*
- [X] `get_feed_status` shall be read-only and shall not expose raw stream handles, sockets, clients, credentials, or connection strings. *app/services/data/scheduler.py:45*
- [X] The deterministic error-code list shall include `DATA_DROPPED`. *app/services/data/scheduler.py:94*
- [X] Real-time records shall normalize to the same OHLCV, tick, and spread contracts used by historical data. *app/services/data/scheduler.py:194*
- [X] Real-time timestamps shall normalize to UTC before crossing any official boundary. *app/services/data/scheduler.py:8*
- [X] Missing, stale, partial, conflicting, dropped, revised, or license-restricted data shall be flagged. *app/services/data/scheduler.py:1*
- [X] Internal real-time feed support shall be in scope for Phase 1 hardening where a source declares live or streaming capability. *app/services/data/scheduler.py:737*
- [X] The module shall expose one low-risk, read-only real-time feed observability tool named `get_feed_status`. *app/services/data/scheduler.py:737*
- [X] Internal feed state shall be observable through `get_feed_status` so operators can monitor heartbeat, buffer health, dropped data, gap reconciliation, reconnects, and circuit-breaker state. *app/services/data/scheduler.py:737*
- [X] The deterministic error-code list shall include `BUFFER_OVERFLOW`. *app/services/data/scheduler.py:94*
- [X] The deterministic error-code list shall include `FEED_HEARTBEAT_TIMEOUT`. *app/services/data/scheduler.py:94*
- [X] The deterministic error-code list shall include `FEED_RECONCILIATION_FAILED`. *app/services/data/scheduler.py:94*
- [X] Initial source readiness shall be `staging` for `real_time_feed_gateway` until buffer, heartbeat, recovery, gap reconciliation, and circuit-breaker tests pass. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] The module shall support an internal real-time feed layer for live tick, spread, and bar-oriented data where source adapters declare live or streaming capability. *app/services/data/scheduler.py:194*
- [X] Real-time feed state shall be observable through `get_feed_status`. *app/services/data/scheduler.py:737*
- [X] `get_feed_status` shall report source, symbol, data kind, connection state, feed readiness, last heartbeat timestamp, last event timestamp, buffer depth, configured buffer capacity, dropped event count, gap count, reconnect count, circuit breaker state, and last error code. *app/services/data/scheduler.py:544*
- [X] Real-time feeds shall maintain heartbeat tracking. *app/services/data/scheduler.py:737*
- [X] Real-time feeds shall detect heartbeat timeouts and return or log `FEED_HEARTBEAT_TIMEOUT`. *app/services/data/scheduler.py:737*
- [X] Real-time buffer overflow shall follow an explicit policy: `halt`, `drop_and_reconcile`, or `backpressure`. *app/services/data/scheduler.py:575*
- [X] Real-time feed gaps shall be visible to downstream consumers. *app/services/data/scheduler.py:737*
- [X] Real-time feed gaps shall not be hidden by synthetic fills. *app/services/data/scheduler.py:737*
- [X] Real-time reconnection shall use exponential backoff with randomized jitter. *app/services/data/scheduler.py:737*
- [X] Real-time feeds shall use bounded buffers. *app/services/data/scheduler.py:753*
- [X] Feed status shall expose heartbeat health, buffer health, gap health, reconnect health, circuit breaker state, and last error. *app/services/data/scheduler.py:737*
- [X] Real-time feed ingestion shall use bounded queues and shall not allow unbounded memory growth. *app/services/data/scheduler.py:737*
- [X] Retry and reconnection shall use exponential backoff with randomized jitter. *app/services/data/scheduler.py:297*
- [X] Oversized source adapters shall be split into focused client, instrument, normalization, and live-feed modules where needed. *app/services/data/scheduler.py:543*
- [X] Overflow policy shall accept only `halt`, `drop_and_reconcile`, or `backpressure`. *app/services/data/scheduler.py:575*
- [X] Reconnect policy shall include maximum retries, exponential backoff, jitter, maximum backoff, and circuit breaker cooldown. *app/services/data/scheduler.py:545*
- [X] Feed status requests shall accept feed ID, source, symbol, data kind, and request ID. *app/services/data/scheduler.py:543*
- [X] Feed status outputs shall include feed ID, state, heartbeat timestamp, last event timestamp, buffer depth, dropped count, gap count, reconnect count, circuit breaker state, and last error. *app/services/data/scheduler.py:545*
- [X] Reconnection shall use exponential backoff with randomized jitter. *app/services/data/scheduler.py:297*
- [X] Feed overflow with `backpressure` shall slow ingestion without unbounded memory growth. *app/services/data/scheduler.py:517*
- [X] Feed status shall not expose raw connection handles, socket details, client objects, or credential-bearing connection strings. *app/services/data/scheduler.py:4*
- [X] Feed heartbeat timeout shall return or log `FEED_HEARTBEAT_TIMEOUT`. *app/services/data/scheduler.py:4*
- [X] Feed buffer overflow shall return or log `BUFFER_OVERFLOW`. *app/services/data/scheduler.py:599*
- [X] Dropped feed records shall return or log `DATA_DROPPED`. *app/services/data/scheduler.py:568*
- [X] Failed feed gap reconciliation shall return `FEED_RECONCILIATION_FAILED`. *app/services/data/scheduler.py:568*
- [X] The module shall provide reliable, normalized, auditable access to historical, real-time, local, synthetic, broker, and external market data. *app/services/data/scheduler.py:194*
- [X] Dropped data gap creation shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:42*
- [X] Feed heartbeat tracking shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] Feed heartbeat timeout shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] Feed buffer limit behavior shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] Feed overflow with `halt` shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:39*
- [X] Feed overflow with `drop_and_reconcile` shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:44*
- [X] Feed overflow with `backpressure` shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:50*
- [X] Feed reconnect with exponential backoff and jitter shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] `get_feed_status` schema shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:9*

#### `app/services/data/persistence.py`

Functions/classes:

- `Repository`
- `save_state`
- `load_state`

Requirements:

- [X] The module shall persist source circuit breaker state. *app/services/data/storage.py:214*
- [X] Documentation shall include database migration procedure. *app/services/data/storage.py:3*
- [X] SQLite is sufficient for single-node local state persistence. *app/services/data/storage.py:1*
- [X] The persistence abstraction must be TSDB-ready for future high-frequency tick and spread storage. *app/services/data/storage.py:1*
- [X] Pending: select the future high-frequency tick/spread TSDB backend after the TSDB-ready persistence interface is validated. *app/services/data/storage.py:1*
- [X] Idempotency keys shall be deterministically derived from source, symbol, data kind, timeframe, start, end, schema version, and normalization version. *app/services/data/storage.py:256*
- [X] Database persistence shall enforce connection limits, timeouts, and leak detection. *app/services/data/storage.py:3*
- [X] Circuit breaker state shall persist across restarts. *app/services/data/storage.py:214*
- [X] Persistence shall support a future append-optimized TSDB backend. *app/services/data/storage.py:1*
- [X] No DataFrame, NumPy array, SDK object, stream handle, socket, or database client crosses the official tool boundary. *app/services/data/storage.py:3*
- [X] Database persistence is transactional, bounded, idempotent, and recovery-aware. *app/services/data/storage.py:1*
- [X] Production sign-off shall include implemented spec version, test command output summary, coverage percentage, exported tool list, known limitations, enabled source adapters, required environment variables, source readiness manifest, license manifest, persistence backend, and downstream modules validated. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] On restart, a source with a persisted open circuit breaker shall remain open or half-open for the configured cooldown period and shall not immediately hammer the failing external source. *app/services/data/storage.py:526*
- [X] Circuit breaker open state shall persist across restarts. *app/services/data/storage.py:214*
- [X] The module shall persist source revision and raw hash metadata. *app/services/data/storage.py:164*
- [X] Large historical datasets shall be persisted and referenced by metadata instead of returned inline when response limits are exceeded. *app/services/data/storage.py:311*
- [X] Persisted data requested with an older `schema_version` than the current canonical version shall either be safely migrated on read or rejected with `DATA_SCHEMA_DRIFT` and re-fetch guidance. *app/services/data/storage.py:35*
- [X] Parquet shall remain the preferred local file format for large persisted datasets in Phase 1. *app/services/data/storage.py:3*
- [X] The deterministic error-code list shall include `DATABASE_ERROR`. *app/services/data/storage.py:289*
- [X] The deterministic error-code list shall include `DB_CONNECTION_ERROR`. *app/services/data/storage.py:289*
- [X] The deterministic error-code list shall include `DB_WRITE_FAILED`. *app/services/data/storage.py:289*
- [X] The persistence interface shall be append-optimized and TSDB-ready. *app/services/data/storage.py:1*
- [X] TimescaleDB shall be the preferred future relational time-series backend for high-frequency tick and spread persistence when multi-node or high-throughput persistence becomes required. *app/services/data/storage.py:1*
- [X] InfluxDB or equivalent metrics-oriented TSDBs may be considered later for telemetry or high-frequency observational data, but they shall not replace the canonical persistence abstraction. *app/services/data/storage.py:344*
- [X] Internal adapters may use pandas, NumPy, broker SDKs, HTTP clients, MCP clients, sockets, database clients, and file-system objects, but those objects shall not cross the official AI-tool boundary. *app/services/data/storage.py:3*
- [X] Schema migrations shall enforce backward compatibility checks. *app/services/data/storage.py:3*
- [X] If a requested `schema_version` is older than the current canonical version, the system shall either perform an on-the-fly safe migration or return `DATA_SCHEMA_DRIFT` with a recommendation to re-fetch. *app/services/data/storage.py:140*
- [X] SQLite shall be the default single-node ACID-capable persistence backend. *app/services/data/storage.py:1*
- [X] The persistence abstraction shall support append-optimized TSDB backends in future phases without rewriting gateway routing logic. *app/services/data/storage.py:1*
- [X] The persistence abstraction shall support append-only ingestion metadata. *app/services/data/storage.py:1*
- [X] Persistence writes shall use transactions for atomic state changes. *app/services/data/storage.py:437*
- [X] Database writes shall include deterministic idempotency keys. *app/services/data/storage.py:5*
- [X] Data ingestion idempotency keys shall be derived from a hash of source, symbol, data kind, timeframe, start time, end time, schema version, and normalization version. *app/services/data/storage.py:256*
- [X] Database writes shall be idempotent under retry. *app/services/data/storage.py:5*
- [X] Database writes shall distinguish insert, update, no-op duplicate, and conflict. *app/services/data/storage.py:5*
- [X] Database conflicts shall return deterministic errors and shall not silently overwrite committed data. *app/services/data/storage.py:3*
- [X] The persistence layer shall enforce connection pool limits, connection timeouts, and automatic leak detection. *app/services/data/storage.py:3*
- [X] Database migrations shall be versioned, auditable, and reversible where practical. *app/services/data/storage.py:3*
- [X] Schema migrations shall enforce backward compatibility or mandatory invalidation and re-ingestion. *app/services/data/storage.py:3*
- [X] The module shall persist ingestion idempotency keys. *app/services/data/storage.py:1*
- [X] Response metadata shall include tool name, tool version, tool category, risk level, request ID, execution time, read-only flag, writes-file flag, modifies-database flag, places-trade flag, and requires-network flag. *app/services/data/storage.py:3*
- [X] Tools that mutate persisted state shall set `modifies_database=True` when persistence state changes. *app/services/data/storage.py:187*
- [X] Retrieval tools that only read local state shall keep `modifies_database=False`. *app/services/data/storage.py:1*
- [X] Database connection pools shall use strict limits and timeouts. *app/services/data/storage.py:3*
- [X] Backward compatibility aliases shall not be included unless a future implementation phase explicitly approves a temporary migration shim. *app/services/data/storage.py:3*
- [X] Database persistence requests shall include entity type, idempotency key, schema version, normalization version, transaction metadata, and request ID where applicable. *app/services/data/storage.py:257*
- [X] Database migrations shall include migration ID, source schema version, target schema version, compatibility result, and rollback policy. *app/services/data/storage.py:3*
- [X] Metadata shall include tool identity, category, risk level, request ID, execution time, side-effect flags, trade flag, network flag, source readiness where applicable, precision policy where applicable, and persistence flags where applicable. *app/services/data/storage.py:389*
- [X] Database state shall not store plaintext secrets. *app/services/data/storage.py:3*
- [X] Database connection failure shall return `DB_CONNECTION_ERROR`. *app/services/data/storage.py:3*
- [X] Database write failure shall return `DB_WRITE_FAILED`. *app/services/data/storage.py:5*
- [X] Persistence failure shall return `DATABASE_ERROR`. *app/services/data/storage.py:1*
- [X] The module shall persist data license and attribution metadata. *app/services/data/storage.py:313*
- [X] The module shall normalize all source-specific market data into canonical internal contracts before returning or persisting records. *app/services/data/storage.py:437*
- [X] If an adapter trips a circuit breaker, the degraded state shall be persisted. *app/services/data/storage.py:214*
- [X] Every source adapter shall avoid returning raw SDK, client, stream, socket, or database objects. *app/services/data/storage.py:3*
- [X] Long-running real-time feed ingestion shall not exhaust database connection pools. *app/services/data/storage.py:3*
- [X] The module shall persist feed state. *app/services/data/storage.py:199*
- [X] Official tools shall never return raw pandas objects, NumPy arrays, raw SDK objects, sockets, stream handles, database clients, `None`, or unstructured exceptions. *app/services/data/storage.py:252*
- [X] The maximum persisted synthetic generation size shall be 1,000,000 records unless explicitly raised by configuration and covered by performance tests. *tests/unit/app/services/data/test_cache_storage_persistence.py:41*
- [X] Connection pool limit behavior shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:61*
- [X] Every official tool shall test that raw DataFrame, NumPy, SDK, stream, socket, client, and database objects do not cross the official boundary. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] SQLite or default persistence backend initialization shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:62*
- [X] Persistence transactions shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:19*
- [X] Database connection timeout handling shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:61*
- [X] Database idempotency keys shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Schema migration compatibility checks shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:19*
- [X] No raw SDK, stream, socket, client, or database object leakage shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Circuit breaker state persistence across restart shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:19*

#### `app/services/data/README.md`

Functions/classes:

- No runtime functions/classes; documentation artifact only.

Requirements:

- [X] Documentation shall include a data module README or docs section. *app/services/data/README.md:3*
- [X] Documentation shall include the official tool catalog. *app/services/data/README.md:3*
- [X] Documentation shall include the final `__all__` export list. *app/services/data/README.md:3*
- [X] Documentation shall include environment variable reference. *app/services/data/README.md:34*
- [X] Documentation shall include crash recovery runbook. *app/services/data/README.md:34*
- [X] Documentation shall include circuit breaker behavior and recovery procedure. *app/services/data/README.md:34*
- [X] Documentation shall include production sign-off template. *app/services/data/README.md:34*
- [X] This requirements document belongs in `docs/planning/DOMAIN.md` because it covers the full data module rather than one sprint. *app/services/data/README.md:37*
- [X] Public functions and classes shall contain useful docstrings. *app/services/data/README.md:31*

#### `app/services/data/scheduler.py`

Functions/classes:

- `create_job`
- `start_job`
- `stop_job`
- `get_job_status`

Requirements:

- [X] Documentation shall explain why `get_data_update_job_status` and `get_feed_status` are included. *app/services/data/scheduler.py:457*
- [X] Documentation shall include usage examples for market data, local storage, symbols, synthetic generation, labeling, scheduler, job status, and feed status. *app/services/data/scheduler.py:1*
- [X] Documentation shall include troubleshooting for MT5, cTrader, Dukascopy, Binance symbol discovery, local storage, cache, database persistence, scheduler, crash recovery, and feed health. *app/services/data/scheduler.py:41*
- [X] `get_data_update_job_status` is the canonical scheduler status tool. *app/services/data/scheduler.py:457*
- [X] `get_update_job_status`, `create_update_job`, `start_update_job`, and `stop_update_job` are not official exports. *app/services/data/scheduler.py:26*
- [X] The scheduler naming conflict shall be resolved by exporting only `create_data_update_job`, `start_data_update_job`, `stop_data_update_job`, `run_data_update_job_once`, and `get_data_update_job_status` for scheduler lifecycle/status. *app/services/data/scheduler.py:1*
- [X] Status inspection shall be added through `get_data_update_job_status`. *app/services/data/scheduler.py:457*
- [X] A central limits manifest shall define maximum records, maximum date range, maximum cache TTL, maximum synthetic generation size, maximum backfill chunk size, maximum feed buffer depth, and maximum scheduler frequency. *app/services/data/scheduler.py:1*
- [X] Response examples shall be documented for OHLCV, tick, spread, market hours, trading sessions, availability, historical volume, scheduler status, feed status, and error responses. *app/services/data/scheduler.py:4*
- [X] Real-time buffer overflow shall flag gaps and trigger backfill when configured and supported. *app/services/data/scheduler.py:737*
- [X] Scheduler lifecycle is explicit, idempotent, and crash-recoverable. *app/services/data/scheduler.py:1*
- [X] Production sign-off artifact is created before release. *app/services/data/scheduler.py:178*
- [X] The names `create_update_job`, `start_update_job`, and `stop_update_job` shall not be exported as official tools. *app/services/data/scheduler.py:26*
- [X] The name `get_update_job_status` shall not be exported as an official tool. *app/services/data/scheduler.py:47*
- [X] External or vendor data sources shall include license metadata before data is stored, exported, scheduled, or used in validation, risk, or execution-bound workflows. *app/services/data/scheduler.py:12*
- [X] `get_data_update_job_status` *app/services/data/scheduler.py:457*
- [X] `get_data_update_job_status` shall be read-only and shall not mutate scheduler state. *app/services/data/scheduler.py:1*
- [X] `get_data_update_job_status` shall be non-networked unless job metadata requires source health lookup. *app/services/data/scheduler.py:21*
- [X] License metadata shall be enforced before storage, scheduler export, or artifact generation. *app/services/data/scheduler.py:1*
- [X] Missing license metadata shall fail closed with `LICENSE_RESTRICTION` for storage, scheduler, export, validation, risk, and execution-bound workflows. *app/services/data/scheduler.py:114*
- [X] The default backfill chunk size for OHLCV bars shall be 100,000 records or 30 calendar days, whichever is reached first. *app/services/data/scheduler.py:607*
- [X] The default backfill chunk size for ticks and spreads shall be 1,000,000 records or 1 calendar day, whichever is reached first. *app/services/data/scheduler.py:607*
- [X] Real-time gaps shall be reconciled through historical backfill where supported and configured. *app/services/data/scheduler.py:737*
- [X] Historical backfills shall be resumable and idempotent. *app/services/data/scheduler.py:26*
- [X] Historical requests shall support chunk size, backfill mode, gap resolution policy, overlap policy, data version policy, precision policy, workflow context, and persistence target where applicable. *app/services/data/scheduler.py:614*
- [X] Backfill idempotency keys shall be derived from source, symbol, data kind, timeframe, start time, end time, schema version, and normalization version. *app/services/data/scheduler.py:194*
- [X] The deterministic error-code list shall include `CHECKPOINT_CORRUPTED`. *app/services/data/scheduler.py:94*
- [X] The module shall persist backfill checkpoints. *app/services/data/scheduler.py:3*
- [X] Crash recovery shall log the lease-expiration reason. *app/services/data/scheduler.py:41*
- [X] Recovery shall resume from the last committed checkpoint, not the last attempted record. *app/services/data/scheduler.py:180*
- [X] Stale locks shall expire according to configured lease timeout. *app/services/data/scheduler.py:62*
- [X] Backfill and recovery events shall be auditable. *app/services/data/scheduler.py:41*
- [X] Corrupted state shall return `STATE_RECOVERY_FAILED` or `CHECKPOINT_CORRUPTED`. *app/services/data/scheduler.py:304*
- [X] Corrupted checkpoint shall return `CHECKPOINT_CORRUPTED`. *app/services/data/scheduler.py:29*
- [X] Scheduler frequency shall not be more frequent than once per minute unless a dedicated live-feed ingestion mechanism is used. *app/services/data/scheduler.py:1*
- [X] SQLite shall be the default ACID-capable single-node persistence backend for scheduler state, feed state, cache metadata, checkpoints, idempotency keys, and audit state. *app/services/data/scheduler.py:503*
- [X] The module shall include internal layers for contracts, responses, validation, normalization, quality, timeframes, cache, registry, gateway routing, source adapters, storage, persistence, transforms, generators, labeling, scheduler, feed state, versioning, precision, rate limits, licensing, and audit logging. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] If the overflow policy is `drop_and_reconcile`, the system shall immediately flag a data gap, update feed gap-count metadata, emit `DATA_DROPPED` or `BUFFER_OVERFLOW`, and trigger historical backfill for the missing time window when supported by the source. *app/services/data/scheduler.py:604*
- [X] Real-time feed state shall persist feed leases, heartbeat state, buffer metadata, last processed timestamp, last committed checkpoint, gap windows, reconnect count, and circuit breaker state. *app/services/data/scheduler.py:737*
- [X] Live data shall be persisted only through explicit persistence, scheduler, feed-ingestion, or storage workflows. *app/services/data/scheduler.py:1*
- [X] The module shall define a persistence abstraction for scheduler state, feed state, cache metadata, source revisions, license metadata, data manifests, checkpoints, idempotency keys, circuit breaker state, and audit events. *app/services/data/scheduler.py:543*
- [X] The module shall explicitly define its concurrency model: `asyncio` for real-time feed ingestion and network I/O, and `multiprocessing` or chunked batch processing for heavy synthetic generation and large historical backfills to prevent event-loop blocking and GIL contention. *tests/unit/app/services/data/test_feeds_scheduler.py:33*
- [X] The gateway shall maintain a global, thread/async-safe rate-limit token bucket or counter per source to prevent concurrent scheduler jobs, feeds, and agent requests from collectively breaching external API rate limits. *app/services/data/scheduler.py:1*
- [X] The same `request_id` shall appear in logs, response metadata, adapter logs, cache logs, scheduler logs, feed logs, and persistence audit records where feasible. *app/services/data/scheduler.py:1*
- [X] Feed configuration shall include source, symbol, data kind, optional timeframe, buffer capacity, overflow policy, heartbeat timeout, reconnect policy, backfill-on-gap flag, persistence target, and request ID. *app/services/data/scheduler.py:543*
- [X] Official tools shall convert adapter, gateway, cache, persistence, scheduler, and feed exceptions into standard error responses. *app/services/data/scheduler.py:1*
- [X] Feed overflow with `drop_and_reconcile` shall record a gap and attempt historical backfill if supported. *app/services/data/scheduler.py:607*
- [X] Feed overflow with `halt` shall stop feed ingestion and require operator or scheduler recovery policy. *app/services/data/scheduler.py:600*
- [X] Quality reports shall be included for fetched, loaded, generated, resampled, aggregated, and backfilled data. *app/services/data/scheduler.py:1*
- [X] The authoritative scheduler lifecycle tool names shall be `create_data_update_job`, `start_data_update_job`, `stop_data_update_job`, and `run_data_update_job_once`. *app/services/data/scheduler.py:1*
- [X] The module shall expose one low-risk, read-only scheduler status tool named `get_data_update_job_status`. *app/services/data/scheduler.py:179*
- [X] The deterministic error-code list shall include `JOB_NOT_FOUND`. *app/services/data/scheduler.py:94*
- [X] The deterministic error-code list shall include `SCHEDULER_ERROR`. *app/services/data/scheduler.py:94*
- [X] Scheduler jobs shall default to a maximum of 500 symbols per job and 20 timeframes per job unless configuration and tests approve larger workloads. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] `create_data_update_job` *app/services/data/scheduler.py:117*
- [X] `start_data_update_job` *app/services/data/scheduler.py:270*
- [X] `stop_data_update_job` *app/services/data/scheduler.py:325*
- [X] `run_data_update_job_once` *app/services/data/scheduler.py:408*
- [X] Historical backfill jobs shall be chunked, resumable, checkpointed, idempotent, and safe to retry. *app/services/data/scheduler.py:27*
- [X] Historical backfill jobs shall persist progress by source, symbol, data kind, timeframe, start time, end time, schema version, normalization version, chunk ID, and idempotency key. *app/services/data/scheduler.py:194*
- [X] Historical backfill jobs shall not mark a chunk complete until records, metadata, quality report, source revision metadata, license metadata, and persistence manifest are committed. *app/services/data/scheduler.py:112*
- [X] Historical backfill jobs shall detect gaps before and after ingestion. *app/services/data/scheduler.py:39*
- [X] The module shall persist scheduler job state. *app/services/data/scheduler.py:1*
- [X] Jobs left in `running` state after a crash shall idempotently transition to `recovering` or `failed` according to recovery policy. *app/services/data/scheduler.py:40*
- [X] Recovery shall not mark incomplete jobs as completed. *app/services/data/scheduler.py:39*
- [X] `create_data_update_job` shall create persisted update job definitions. *app/services/data/scheduler.py:117*
- [X] `start_data_update_job` shall start recurring execution for a valid existing job or valid schedule. *app/services/data/scheduler.py:275*
- [X] `start_data_update_job` shall not behave as a one-time run when schedule is omitted. *app/services/data/scheduler.py:375*
- [X] `run_data_update_job_once` shall execute one immediate update run and shall not create a recurring schedule. *app/services/data/scheduler.py:413*
- [X] `stop_data_update_job` shall stop or disable scheduled execution. *app/services/data/scheduler.py:330*
- [X] `get_data_update_job_status` shall inspect job state without mutating scheduler state. *app/services/data/scheduler.py:40*
- [X] Scheduler state shall include `created`, `running`, `stopped`, `failed`, `completed`, and `recovering`. *app/services/data/scheduler.py:40*
- [X] Scheduler job requests shall include job name, source, symbol or symbols, optional timeframe or timeframes, schedule, storage target, data kind, and request ID. *app/services/data/scheduler.py:194*
- [X] Data update job definitions shall include job ID, job name, source, symbols, timeframes, data kind, storage format, storage path, optional start/end, optional schedule, enabled flag, created timestamp, and updated timestamp. *app/services/data/scheduler.py:194*
- [X] Job names shall be stable, non-empty, and safe for file and database keys. *app/services/data/scheduler.py:21*
- [X] Duplicate job creation shall be idempotent or return a deterministic duplicate-job error. *app/services/data/scheduler.py:153*
- [X] Starting an already running job shall not create duplicate workers silently. *app/services/data/scheduler.py:27*
- [X] Scheduler jobs shall use checkpointing, idempotency, lease-based locks, retry policy, cache policy, path policy, license policy, and crash recovery policy. *app/services/data/scheduler.py:32*
- [X] Scheduler tools shall be medium-risk except `get_data_update_job_status`, which shall be low-risk and read-only. *app/services/data/scheduler.py:1*
- [X] Schedules shall be parseable and bounded. *app/services/data/scheduler.py:26*
- [X] Scheduler and cache tools shall include side-effect metadata. *app/services/data/scheduler.py:1*
- [X] Backfill jobs shall include source, symbols, timeframes, data kinds, start, end, chunk policy, destination, schedule or one-time mode, recovery policy, request ID, and metadata options. *app/services/data/scheduler.py:194*
- [X] Job status outputs shall include job ID, state, enabled flag, last run status, last checkpoint, last error, next scheduled run, lease status, recovery state, and request ID. *app/services/data/scheduler.py:492*
- [X] Persistence errors shall not mark jobs or chunks as complete. *app/services/data/scheduler.py:17*
- [X] Missing source license metadata shall return `LICENSE_RESTRICTION` for storage, scheduler, validation, risk, and execution-bound workflows. *app/services/data/scheduler.py:114*
- [X] Missing scheduler job shall return `JOB_NOT_FOUND`. *app/services/data/scheduler.py:1*
- [X] Scheduler errors shall return `SCHEDULER_ERROR`. *app/services/data/scheduler.py:1*
- [X] A running job found after crash shall transition idempotently to `recovering` or `failed`, not remain indefinitely `running`. *app/services/data/scheduler.py:40*
- [X] Backfill chunking shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:33*
- [X] Backfill idempotency shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:33*
- [X] Backfill source revision handling shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:62*
- [X] Automatic historical backfill after dropped data shall be tested where source supports backfill. *tests/unit/app/services/data/test_feeds_scheduler.py:149*
- [X] Backfill checkpoint resume shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:33*
- [X] Backfill cache invalidation shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:33*
- [X] Recovery from corrupted checkpoints shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:132*
- [X] Every official tool shall test dry-run behavior for cache, scheduler, and file operations where applicable. *tests/unit/app/services/data/test_feeds_scheduler.py:109*
- [X] License restriction enforcement shall be tested for storage and scheduler exports. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] Scheduler tests shall cover create job, start job, stop job, and run once. *tests/unit/app/services/data/test_feeds_scheduler.py:66*
- [X] Scheduler tests shall cover duplicate start behavior. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] Scheduler tests shall cover duplicate job creation behavior. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] Scheduler tests shall cover missing job behavior. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] Scheduler tests shall cover invalid source, symbol, timeframe, and schedule. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] Scheduler tests shall cover state persistence. *tests/unit/app/services/data/test_feeds_scheduler.py:1*
- [X] Backfill license enforcement shall be tested. *tests/unit/app/services/data/test_feeds_scheduler.py:33*

#### `app/services/data/sources.py`

Functions/classes:

- `SourceAdapter`
- `SourceRegistry`
- `get_source_adapter`

Requirements:

- [X] Documentation shall include a source adapter catalog. *app/services/data/gateway.py:1*
- [X] Documentation shall include the source readiness manifest. *app/services/data/gateway.py:1*
- [X] Documentation shall include the source license manifest. *app/services/data/gateway.py:1*
- [X] The HaruQuantAI Tool Function Standard, Code Quality Standard, Agent Standard, and Agentic AI Playbook exist outside this source-requirements document and may define cross-cutting details not repeated in the data module specification. *app/services/data/gateway.py:265*
- [X] The broker/data gateway is internal and routes one internal contract to many external APIs. *app/services/data/gateway.py:45*
- [X] Phase 1 may proceed without complete external source adapter implementations when disabled or unavailable adapters fail safely and deterministically and contracts, responses, validation, timeframes, registry, exports, and tests meet Phase 1 acceptance. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] No blocking open questions remain for Phase 1 implementation based on the current source material. *app/services/data/gateway.py:208*
- [X] A source readiness manifest shall be maintained. *app/services/data/gateway.py:1*
- [X] A source license manifest shall be maintained. *app/services/data/gateway.py:1*
- [X] cTrader and Dukascopy clients are internal. *app/services/data/gateway.py:4*
- [X] Broker adapters never place trades. *app/services/data/gateway.py:1*
- [X] The source registry shall not be exported as an official AI tool unless a future requirement explicitly approves it. *app/services/data/gateway.py:1385*
- [X] When a source provides both tick volume and real volume, both shall be preserved. *app/services/data/gateway.py:252*
- [X] Disabled or unconfigured source shall return `SOURCE_NOT_CONFIGURED`. *app/services/data/gateway.py:1403*
- [X] Historical data shall preserve source revision metadata where available. *app/services/data/gateway.py:1760*
- [X] Network retry exhaustion shall return deterministic error codes and include retry metadata. *app/services/data/gateway.py:19*
- [X] Unsupported source shall return `UNSUPPORTED_SOURCE`. *app/services/data/gateway.py:1403*
- [X] Unsupported valid-source capability shall return `UNSUPPORTED_OPERATION`. *app/services/data/gateway.py:1403*
- [X] Empty source result shall return `EMPTY_RESULT` or `DATA_NOT_FOUND` according to context. *app/services/data/gateway.py:1403*
- [X] Network timeout shall return `TIMEOUT`. *app/services/data/gateway.py:105*
- [X] Network failure shall return `NETWORK_ERROR`. *app/services/data/gateway.py:105*
- [X] Broker unavailable shall return `BROKER_UNAVAILABLE`. *app/services/data/gateway.py:668*
- [X] A central limits manifest shall define default and maximum values by data kind, source, workflow context, and response mode. *app/services/data/gateway.py:1539*
- [X] Symbol metadata shall normalize asset class, base currency, quote currency, contract size, tick size, tick value, point, digits, lot limits, lot step, margin currency, profit currency, trading hours, and source metadata. *app/services/data/gateway.py:1758*
- [X] Either date range or limit shall be provided unless the source has a safe default. *app/services/data/gateway.py:1670*
- [X] External source calls shall use explicit timeouts, bounded retries, rate limits, and circuit breakers. *app/services/data/gateway.py:144*
- [X] The module shall not place trades, close positions, modify broker account state, modify terminal settings, modify risk settings, or perform execution actions. *app/services/data/gateway.py:160*
- [X] OHLCV records shall normalize timestamp, open, high, low, close, volume, tick volume, real volume, spread, source, symbol, and timeframe. *app/services/data/gateway.py:1640*
- [X] `get_historical_volume` may derive volume from OHLCV, tick records, or source-native volume data if the public response contract remains stable and tested. *tests/unit/app/services/data/test_gateway_and_sources.py:187*
- [X] Tick records shall normalize timestamp, bid, ask, last, volume, spread, source, and symbol. *app/services/data/gateway.py:1640*
- [X] Spread records shall normalize timestamp, symbol, bid, ask, spread points, spread pips, and source. *app/services/data/gateway.py:748*
- [X] `fallback_sources` shall be represented as an explicit optional list in data retrieval requests. *app/services/data/gateway.py:1652*
- [X] `fallback_sources` shall default to an empty list. *app/services/data/gateway.py:1517*
- [X] Fallback shall never occur unless `fallback_sources` is supplied by the caller. *app/services/data/gateway.py:1517*
- [X] Fallback metadata shall include requested source, actual source, fallback used, fallback reason, and attempted fallback chain. *app/services/data/gateway.py:1517*
- [X] The module shall provide one internal broker/data gateway interface that routes one internal request contract to many external source APIs. *app/services/data/gateway.py:53*
- [X] The gateway shall use adapter capability declarations before execution. *app/services/data/gateway.py:1520*
- [X] `fallback_sources` shall be optional and shall default to empty. *app/services/data/gateway.py:34*
- [X] Broker/data gateway errors shall preserve requested source, actual source where known, adapter readiness, capability declaration, and circuit breaker state. *app/services/data/gateway.py:1*
- [X] Source readiness shall be declared in a central source readiness manifest. *app/services/data/gateway.py:1*
- [X] Source readiness shall be included in source-specific response metadata. *app/services/data/gateway.py:1760*
- [X] The gateway shall enforce source readiness before execution. *app/services/data/gateway.py:1*
- [X] The source registry shall provide internal adapter lookup and registration. *app/services/data/gateway.py:53*
- [X] Availability outputs shall include available ranges, gaps, completeness, record count, source readiness, and source metadata. *app/services/data/gateway.py:1805*
- [X] Fallback shall validate source readiness, capability declarations, license policy, and workflow context before use. *app/services/data/gateway.py:1539*
- [X] Historical data shall expose gaps, overlaps, completeness, quality status, source readiness, license metadata, and precision policy in metadata. *app/services/data/gateway.py:1760*
- [X] The gateway shall enforce credential policy, source readiness, rate limits, retry policy, circuit breaker policy, license policy, source revision policy, normalization policy, quality policy, and precision policy consistently across adapters. *app/services/data/gateway.py:1650*
- [X] `fallback_sources` shall be validated against source readiness, capability declarations, and license policy before use. *app/services/data/gateway.py:1517*
- [X] Spread outputs shall include records or summaries, record count, symbol, source, start, end, quality report, source metadata, license metadata, and precision metadata. *app/services/data/gateway.py:1760*
- [X] Source revision mismatch shall return or log `DATA_SOURCE_REVISION_DETECTED`. *app/services/data/gateway.py:156*
- [X] Passwords, access tokens, API keys, account secrets, broker secrets, and raw credential payloads shall never be logged or returned. *app/services/data/gateway.py:3*
- [X] Official tools shall remain thin orchestration functions that validate inputs, call internal services/adapters, and return standard responses. *app/services/data/gateway.py:1456*
- [X] Naive timestamps shall exist only inside source adapters before normalization. *app/services/data/gateway.py:1*
- [X] Every source adapter shall implement a common internal source protocol. *app/services/data/gateway.py:53*
- [X] Every source adapter shall validate source-specific requirements. *app/services/data/gateway.py:1*
- [X] Every source adapter shall fetch or load raw source data. *app/services/data/gateway.py:1*
- [X] Every source adapter shall convert raw fields into normalized records. *app/services/data/gateway.py:1490*
- [X] Every source adapter shall preserve source metadata. *app/services/data/gateway.py:1*
- [X] Every source adapter shall map source errors to deterministic internal errors. *app/services/data/gateway.py:53*
- [X] Source adapters shall expose no direct official AI tool functions. *app/services/data/gateway.py:1*
- [X] Source adapters shall support circuit breaker state. *app/services/data/gateway.py:140*
- [X] Broker adapters shall remain read-only in the data module. *app/services/data/gateway.py:1*
- [X] Broker adapters shall never place trades, close positions, modify account state, or change terminal settings. *app/services/data/gateway.py:151*
- [X] Every source adapter shall avoid logging secrets. *app/services/data/gateway.py:1*
- [X] Source adapters may be marked `production`, `staging`, `experimental`, or `not_available`, but unavailable adapters shall fail safely and deterministically. *app/services/data/gateway.py:1*
- [X] Adapter errors shall preserve safe source context and request ID. *app/services/data/gateway.py:1539*
- [X] Broker adapters shall never place trades, close positions, modify account state, or change terminal settings. *app/services/data/gateway.py:151*
- [X] MT5 adapter shall remain read-only and shall not place orders or modify broker state. *app/services/data/gateway.py:4*
- [X] Initial source readiness shall be `staging` for `mt5` until live credential, broker, timeout, and data validation tests pass. *tests/unit/app/services/data/test_gateway_and_sources.py:14*
- [X] MT5 source shall support secure credential resolution from environment/config. *app/services/data/gateway.py:4*
- [X] MT5 credential resolution shall remain inside the adapter/client layer. *app/services/data/gateway.py:4*
- [X] Initial source readiness shall be `staging` for `ctrader` until client-boundary, network, and normalization tests pass. *tests/unit/app/services/data/test_gateway_and_sources.py:249*
- [X] cTrader source shall use the approved cTrader adapter/MCP boundary. *app/services/data/gateway.py:4*
- [X] cTrader source shall support symbol listing, bar loading, cTrader bar normalization, timeframe mapping, source metadata preservation, and deterministic network/client errors. *app/services/data/gateway.py:4*
- [X] Raw cTrader client construction shall remain internal. *app/services/data/gateway.py:812*
- [X] cTrader client construction shall remain internal. *app/services/data/gateway.py:812*
- [X] Public Dukascopy streaming subscription tools shall remain deferred until a later specification explicitly approves public streaming tools. *app/services/data/gateway.py:1380*
- [X] Initial source readiness shall be `staging` for `dukascopy` until historical/live capability, rate-limit, and normalization tests pass. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Dukascopy live or stream-oriented access shall be represented as an internal adapter capability where supported. *app/services/data/gateway.py:53*
- [X] Dukascopy source shall support instrument discovery, internal instrument metadata lookup, historical OHLCV or tick fetch where implemented, source interval mapping, live or stream-oriented fetch where supported, normalization, HTTP/network handling, retry/timeouts, and source metadata preservation. *app/services/data/gateway.py:144*
- [X] Dukascopy implementation shall be split into smaller client, instruments, normalization, source, and live modules if it becomes oversized. *app/services/data/gateway.py:671*
- [X] Dukascopy client internals shall remain internal. *app/services/data/gateway.py:960*
- [X] Initial source readiness shall be `staging` for `binance` symbol discovery only. *app/services/data/gateway.py:83*
- [X] Binance or equivalent exchange support shall be symbol-discovery oriented through `list_symbols(source="binance")`. *app/services/data/gateway.py:1091*
- [X] Binance support shall not become a trading or execution adapter inside the data module. *app/services/data/gateway.py:1*
- [X] Data quality tests shall cover adversarial market conditions, including zero-volume bars, extreme spread widening such as `>1000` pips, NaN/Inf values from source APIs, and flash-crash price anomalies. *tests/unit/app/services/data/test_gateway_and_sources.py:239*
- [X] The internal gateway shall route one internal request format to many source adapters. *app/services/data/gateway.py:1520*
- [X] Adapter capability declarations shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:11*
- [X] Adapter readiness levels shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:11*
- [X] Source registry lookup and registration behavior shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Source registry non-export as an official AI tool shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Every source adapter shall test source-specific normalization. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Every source adapter shall test source-specific deterministic error mapping. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Every source adapter shall test missing optional dependency behavior. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Every source adapter shall test mocked network or client failure behavior where applicable. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Every source adapter shall test no secret leakage. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Explicit fallback source behavior shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:102*
- [X] MT5 credential redaction shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:190*
- [X] cTrader client-boundary behavior shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:249*
- [X] Dukascopy historical/live capability representation shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:72*
- [X] Binance symbol-discovery-only behavior shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:12*
- [X] Production tests shall cover rate-limit tracking, HTTP 429 handling, and no-immediate-retry behavior. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Network timeout, HTTP 429, retry, and circuit breaker behavior shall be tested with mocks. *tests/unit/app/services/data/test_gateway_and_sources.py:21*
- [X] Every official tool shall test unsupported source where applicable. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Every official tool shall test source failure. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Production tests shall cover license restriction enforcement. *tests/unit/app/services/data/test_gateway_and_sources.py:98*

#### `app/services/data/storage.py`

Functions/classes:

- `save_record`
- `load_record`
- `validate_storage_path`

Requirements:

- [X] Documentation shall include approved storage roots. *app/services/data/storage.py:4*
- [X] Package path is `app/services/data/`. *app/services/data/storage.py:21*
- [X] Local paths are validated against approved storage roots. *app/services/data/storage.py:4*
- [X] The module shall not be marked production-ready until a production sign-off artifact is produced. *app/services/data/storage.py:29*
- [X] Redistribution-restricted data shall not be exported outside approved internal paths. *app/services/data/storage.py:49*
- [X] Storage writes shall include metadata manifests when `include_metadata=True`. *app/services/data/storage.py:434*
- [X] Optional source metadata may include source version, source update timestamp, raw data hash, vendor response time, remaining rate-limit quota, terminal path, and adapter version. *app/services/data/storage.py:256*
- [X] Local immutable datasets shall have no time-based expiry when their file hash and modified timestamp remain unchanged. *app/services/data/storage.py:3*
- [X] Approved storage roots shall be configurable only through HaruQuant settings. *app/services/data/storage.py:4*
- [X] Absolute paths outside approved roots shall be rejected. *app/services/data/storage.py:49*
- [X] `save_market_data` *app/services/data/storage.py:428*
- [X] `load_local_dataset` *app/services/data/storage.py:503*
- [X] Source adapters shall implement the common internal source protocol in `app/services/data/sources/base.py` or a future explicitly versioned replacement path. *app/services/data/storage.py:149*
- [X] Storage requests shall validate path safety and default to `overwrite=False`. *app/services/data/storage.py:39*
- [X] Storage writes shall use temp artifact plus atomic final commit/rename semantics. *app/services/data/storage.py:4*
- [X] Storage writes shall quarantine partial artifacts from failed writes. *app/services/data/storage.py:4*
- [X] File writes shall use temp files plus atomic rename or equivalent safe commit semantics. *app/services/data/storage.py:437*
- [X] Partial artifacts created during failed writes shall be quarantined. *app/services/data/storage.py:494*
- [X] Production files shall contain module-level docstrings. *app/services/data/storage.py:61*
- [X] Implementation files shall remain small and single-responsibility. *app/services/data/storage.py:61*
- [X] The package path shall be `app/services/data/`. *app/services/data/storage.py:21*
- [X] Storage requests shall include path, format, overwrite flag, create-parents flag, include-metadata flag, and request ID. *app/services/data/storage.py:434*
- [X] Storage paths shall resolve under approved storage roots. *app/services/data/storage.py:4*
- [X] Local file operations shall enforce approved storage roots and path validation. *app/services/data/storage.py:4*
- [X] Absolute paths outside approved roots shall be rejected. *app/services/data/storage.py:49*
- [X] Overwrite operations shall require explicit `overwrite=True`. *app/services/data/storage.py:433*
- [X] Existing local file with `overwrite=False` shall return `FILE_ALREADY_EXISTS`. *app/services/data/storage.py:3*
- [X] Unsafe path shall return `PATH_NOT_ALLOWED`. *app/services/data/storage.py:49*
- [X] Missing local file shall return `FILE_NOT_FOUND`. *app/services/data/storage.py:3*
- [X] Initial source readiness shall be `production` for `csv`. *app/services/data/storage.py:3*
- [X] Naive local CSV/Parquet timestamps shall require source timezone detection or request-level `source_timezone` override. *app/services/data/storage.py:3*
- [X] CSV source shall support loading OHLCV records. *app/services/data/storage.py:3*
- [X] CSV source shall support loading tick records when columns allow. *app/services/data/storage.py:3*
- [X] CSV source shall support saving normalized records through the storage layer. *app/services/data/storage.py:89*
- [X] CSV source shall support configurable timestamp column, delimiter, column alias mapping, strict path safety, date filtering, and validation after load. *app/services/data/storage.py:490*
- [X] `save_market_data` shall save validated normalized records to CSV or Parquet. *app/services/data/storage.py:3*
- [X] `load_local_dataset` shall load CSV or Parquet datasets into normalized records. *app/services/data/storage.py:506*
- [X] Initial source readiness shall be `production` for `parquet`. *app/services/data/storage.py:3*
- [X] Parquet source shall support loading OHLCV and tick records. *app/services/data/storage.py:3*
- [X] Parquet source shall support saving normalized records. *app/services/data/storage.py:3*
- [X] Parquet source shall preserve schema metadata where possible. *app/services/data/storage.py:3*
- [X] Parquet source shall support date filtering, safe path validation, and validation after load. *app/services/data/storage.py:49*
- [X] Parquet shall be the preferred local storage format for larger datasets. *app/services/data/storage.py:1*
- [X] Loading 100,000 local Parquet records should target under 2 seconds. *tests/unit/app/services/data/test_cache_storage_persistence.py:41*
- [X] The gateway shall route requests to adapters for CSV, Parquet, MT5, cTrader, Dukascopy, Binance symbol discovery, synthetic generation, real-time feed providers, and future approved providers. *app/services/data/storage.py:3*
- [X] MT5 source shall support terminal path handling, connection lifecycle management, symbol listing, OHLCV bars, tick data where available, symbol metadata/details, timeframe mapping, UTC timestamp normalization, broker timezone metadata, and broker-unavailable errors. *app/services/data/storage.py:389*
- [X] `workflow_context` shall be an explicit input wherever precision, validation strictness, storage, or downstream risk differs. *app/services/data/storage.py:1*
- [X] Quarantine of partial artifacts shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Storage tests shall cover valid save and load. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Storage tests shall cover overwrite blocked by default. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Storage tests shall cover unsafe path rejection. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Storage tests shall cover unsupported extension rejection. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Storage tests shall cover metadata preservation. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Every official tool shall test path safety where applicable. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*

#### `app/utils/errors.py`

Functions/classes:

- `Error`
- `ValidationError`
- `ServiceError`

Requirements:

- [X] Documentation shall include an error-code reference with all deterministic error codes. *app/utils/errors.py:5*
- [X] `VALIDATION_FAILED` shall be added to deterministic error codes. *app/utils/errors.py:2*
- [X] Every official tool handles errors deterministically. *app/utils/errors.py:4*
- [X] `status` shall be `success` or `error`. *app/utils/errors.py:21*
- [X] `error` shall be null on success or contain deterministic code and details on failure. *app/utils/errors.py:1570*
- [X] All standard system exceptions and error codes (including `VALIDATION_FAILED`, `AUTHENTICATION_FAILED`, `PERMISSION_DENIED`, `CIRCUIT_BREAKER_OPEN`, `UNKNOWN_ERROR`) shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom data exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`. *app/utils/errors.py:5*
- [X] The deterministic error-code list shall include `VALIDATION_FAILED`. *app/utils/errors.py:5*
- [X] The deterministic error-code list shall include `CIRCUIT_BREAKER_OPEN`. *app/utils/errors.py:5*
- [X] The deterministic error-code list shall include `AUTHENTICATION_FAILED`. *app/utils/errors.py:5*
- [X] The deterministic error-code list shall include `PERMISSION_DENIED`. *app/utils/errors.py:5*
- [X] `UNKNOWN_ERROR` shall be reserved only for unexpected failures after deterministic error mapping has been exhausted. *app/utils/errors.py:2*
- [X] Official data tools shall use deterministic error codes. *app/utils/errors.py:1263*
- [X] Any unsupported `workflow_context` shall return `INVALID_INPUT`. *app/utils/errors.py:16*
- [X] Invalid workflow context shall return `INVALID_INPUT`. *app/utils/errors.py:69*
- [X] Input validation failure shall return `VALIDATION_FAILED` or `INVALID_INPUT` according to context. *app/utils/errors.py:350*
- [X] Official tools shall not use `UNKNOWN_ERROR` for expected unsupported capabilities. *app/utils/errors.py:4*
- [X] Bad data shall not be silently normalized without visible warnings or errors. *app/utils/errors.py:1263*
- [X] The deterministic error-code list shall include `STATE_RECOVERY_FAILED`. *app/utils/errors.py:5*
- [X] The deterministic error-code list shall include `CREDENTIALS_MISSING`. *app/utils/errors.py:5*
- [X] Errors and logs shall redact secret-like values. *app/utils/errors.py:61*
- [X] Every official tool shall test deterministic error code mapping. *tests/unit/app/services/data/test_gateway_and_sources.py:37*
- [X] Usage examples shall show realistic workflows and handle both success and error responses. *app/utils/errors.py:2*

#### `app/services/data/cache.py`

Functions/classes:

- `CacheKey`
- `read_cache`
- `write_cache`
- `invalidate_cache`

Requirements:

- [X] Documentation shall include cache TTL and invalidation policy. *app/services/data/storage.py:265*
- [X] Documentation shall state that schema version, normalization version, and raw data hash changes invalidate matching cache entries regardless of TTL. *app/services/data/storage.py:257*
- [X] Approved storage roots shall be fixed to `data/raw/`, `data/processed/`, `data/cache/`, and `artifacts/data/` for Phase 1. *app/services/data/storage.py:5*
- [X] Changing schema version, normalization version, or raw data hash shall invalidate matching cache entries regardless of TTL. *app/services/data/storage.py:257*
- [X] Cache keys include schema version, normalization version, and raw data hash where available. *app/services/data/storage.py:257*
- [X] Stale cache is not returned silently. *app/services/data/storage.py:311*
- [X] The maximum request-level cache TTL override shall be 7 days unless a source declares a stricter maximum. *app/services/data/storage.py:265*
- [X] Historical daily-or-higher data shall default to a cache TTL of 86,400 seconds. *tests/unit/app/services/data/test_cache_storage_persistence.py:80*
- [X] Intraday bar data shall default to a cache TTL of 3,600 seconds. *tests/unit/app/services/data/test_cache_storage_persistence.py:80*
- [X] Tick data shall default to a cache TTL of 900 seconds unless the source declares a stricter freshness policy. *tests/unit/app/services/data/test_cache_storage_persistence.py:80*
- [X] Cache entries shall automatically invalidate when `schema_version`, `normalization_version`, or `raw_data_hash` changes, regardless of TTL. *app/services/data/storage.py:257*
- [X] Stale cache shall not be returned silently. *app/services/data/storage.py:311*
- [X] Stale cache behavior shall be governed by the `stale_data_behavior` input parameter, defaulting to `refresh_and_return` for execution-bound workflows and `return_with_warning` for research workflows. *app/services/data/storage.py:306*
- [X] The approved Phase 1 storage roots shall be `data/raw/`, `data/processed/`, `data/cache/`, and `artifacts/data/`. *app/services/data/storage.py:5*
- [X] `clear_data_cache` *app/services/data/storage.py:372*
- [X] Historical requests shall support source, symbol, data kind, timeframe where applicable, start, end, limit, cache policy, source timezone, workflow context, fallback sources, and request ID. *app/services/data/storage.py:256*
- [X] Historical data shall include raw data hash in cache identity when available. *app/services/data/storage.py:5*
- [X] Historical data shall never silently use stale cache entries. *app/services/data/storage.py:306*
- [X] Live data shall not use persistent cache by default. *app/services/data/storage.py:5*
- [X] A new `schema_version` shall read data written by the previous minor version or trigger mandatory cache invalidation and re-ingestion. *app/services/data/storage.py:5*
- [X] The cache shall support key creation, reads, writes, stale detection, source revision detection, and safe clearing. *app/services/data/storage.py:306*
- [X] Cache keys shall include source, data kind, symbol, timeframe, start, end, schema version, normalization version, request flags, source revision metadata, and raw data hash where available. *app/services/data/storage.py:389*
- [X] Stale cache shall not be returned silently. *app/services/data/storage.py:311*
- [X] Stale cache behavior shall be governed by `stale_data_behavior`, with `refresh_and_return` forcing a source refresh before return and `return_with_warning` returning stale data only with explicit warning metadata. *app/services/data/storage.py:309*
- [X] Cache reads, writes, misses, stale decisions, invalidation, and clear operations shall propagate request ID in logs. *app/services/data/storage.py:5*
- [X] Cache write failures shall not corrupt successful source fetches. *app/services/data/storage.py:5*
- [X] If source fetch succeeds but cache write fails, the response shall return source data with a warning and log the cache failure. *app/services/data/storage.py:311*
- [X] `clear_data_cache` shall default to dry-run. *app/services/data/storage.py:382*
- [X] `clear_data_cache` shall validate namespace, source filter, symbol filter, dry-run option, and allowed cache root. *app/services/data/storage.py:382*
- [X] Generated artifacts, local credentials, notebooks, temp files, `__pycache__`, and `.pyc` files shall not be committed. *app/services/data/storage.py:61*
- [X] Data retrieval tools shall accept source, symbol, data kind, timeframe where applicable, date range, limit, cache controls, source timezone override, stale-data behavior, quality failure behavior, workflow context, fallback sources, and request ID. *app/services/data/storage.py:389*
- [X] Cache TTL override shall be non-negative and within configured maximum TTL. *app/services/data/storage.py:265*
- [X] Cache errors shall not corrupt successful source fetches. *app/services/data/storage.py:389*
- [X] HTTP 429 or source throttling shall return or log `RATE_LIMIT_EXCEEDED`. *app/services/data/storage.py:22*
- [X] Immediate retry after throttling shall be forbidden. *app/services/data/storage.py:56*
- [X] Historical data providers that revise old data shall trigger cache invalidation or strict failure according to `DataVersionPolicy`. *app/services/data/storage.py:5*
- [X] Missing cache entries shall be treated as cache misses that trigger source fetch or deterministic failure; stale-cache behavior shall not be applied to missing entries. *app/services/data/storage.py:306*
- [X] Source revisions shall invalidate cache or fail according to `DataVersionPolicy`. *app/services/data/storage.py:275*
- [X] Cache miss shall return or log `CACHE_MISS`. *app/services/data/storage.py:281*
- [X] Cache stale shall return or log `CACHE_STALE`. *app/services/data/storage.py:311*
- [X] Cache write failure shall return data with warning if source fetch succeeded. *app/services/data/storage.py:311*
- [X] Data validation, normalization, quality scoring, timestamp handling, cache handling, source metadata, and persistence behavior shall be deterministic and documented. *app/services/data/storage.py:306*
- [X] Every official tool shall log call start, validation failure, source failure, cache hit/miss/stale status, persistence failure, successful completion, execution time, and error code on failure. *app/services/data/storage.py:67*
- [X] Schema migration and cache invalidation events shall be auditable. *app/services/data/storage.py:3*
- [X] Crash recovery shall never bypass validation, path policy, license policy, cache policy, source readiness policy, precision policy, or gateway policy. *app/services/data/storage.py:49*
- [X] Streaming and live data shall default to cache TTL `0` and shall not be persistently cached unless explicitly stored through a persistence workflow. *app/services/data/storage.py:262*
- [X] Real-time reconnection shall avoid thundering-herd behavior after crashes, restarts, network partitions, and source throttling. *app/services/data/storage.py:256*
- [X] Every official tool shall test cache hit, miss, stale, and invalidation behavior where applicable. *tests/unit/app/services/data/test_cache_storage_persistence.py:69*
- [X] Cache invalidation on schema version change shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Cache invalidation on normalization version change shall be tested. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*
- [X] Production tests shall cover source revision detection and cache invalidation. *tests/unit/app/services/data/test_cache_storage_persistence.py:1*

#### `app/services/data/models.py`

Functions/classes:

- `Request`
- `Result`
- `Config`
- `Metadata`

Requirements:

- [X] Documentation shall include precision and numeric serialization policy by workflow context. *app/services/data/models.py:14*
- [X] `get_historical_volume` may be direct or derived if its response contract remains stable and tested. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*
- [X] Downstream modules shall adapt to the new contracts rather than relying on aliases. *app/services/data/models.py:3*
- [X] Precision serialization shall be workflow-aware. *app/services/data/models.py:14*
- [X] Schema evolution shall enforce backward compatibility or explicit invalidation and re-ingestion. *app/services/data/models.py:1*
- [X] Every official tool returns the standard response schema. *app/services/data/models.py:1*
- [X] Every official tool has metadata and side-effect flags. *app/services/data/models.py:3*
- [X] Downstream contract alignment tests pass. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*
- [X] `get_symbol_metadata` *app/services/data/models.py:14*
- [X] `get_data_availability` *app/services/data/models.py:14*
- [X] The data module shall be rebuilt as a clean, contract-driven, agent-safe, testable, maintainable domain under `app/services/data/`. *tests/unit/app/services/data/test_models_and_public_contracts.py:6*
- [X] `get_historical_volume` shall return volume-specific historical records or summaries. *app/services/data/models.py:175*
- [X] Converting 100,000 DataFrame rows to records should target under 3 seconds. *tests/unit/app/services/data/test_models_and_public_contracts.py:20*
- [X] Missing required asset-specific metadata shall return or emit `MISSING_ASSET_METADATA` when the asset class and workflow require those fields. *app/services/data/models.py:146*
- [X] Every official AI tool shall return the standard HaruQuantAI response schema. *app/services/data/models.py:1*
- [X] All market data crossing the official AI-tool boundary shall be JSON-serializable and contract-compliant. *app/services/data/models.py:1*
- [X] Large historical data shall be stored locally and referenced through metadata where direct response payloads would be unsafe. *app/services/data/models.py:3*
- [X] Every official tool shall return status, message, data, error, and metadata. *app/services/data/models.py:3*
- [X] Missing required asset metadata shall return `MISSING_ASSET_METADATA`. *app/services/data/models.py:3*
- [X] The deterministic error-code list shall include `MISSING_ASSET_METADATA`. *app/services/data/models.py:24*
- [X] Error responses shall include status, message, error code, details, request ID, and metadata. *app/services/data/models.py:24*
- [X] Schema drift shall return `DATA_SCHEMA_DRIFT`. *app/services/data/models.py:1*
- [X] The default direct-response limit for OHLCV bars shall be 5,000 records. *app/services/data/models.py:3*
- [X] The maximum direct-response limit for OHLCV bars shall be 50,000 records. *app/services/data/models.py:3*
- [X] The default direct-response limit for ticks shall be 10,000 records. *app/services/data/models.py:169*
- [X] The maximum direct-response limit for ticks shall be 250,000 records. *app/services/data/models.py:58*
- [X] The default direct-response limit for spread records shall be 10,000 records. *app/services/data/models.py:175*
- [X] The maximum direct-response limit for spread records shall be 250,000 records. *app/services/data/models.py:175*
- [X] Data availability tools shall not materialize more than 1,000,000 records solely for counts unless an operator explicitly enables a bounded audit mode. *app/services/data/models.py:174*
- [X] Historical tick retrieval shall require explicit date ranges or bounded limits. *app/services/data/models.py:93*
- [X] Until a historical calendar provider is approved, historical market-hour reconstruction shall return `UNSUPPORTED_OPERATION` and disclose `historical_hours_supported=false` in metadata. *app/services/data/models.py:166*
- [X] `VALIDATION_FAILED` shall be used for input, contract, or request validation failures. *app/services/data/models.py:3*
- [X] `get_market_data` shall fetch normalized historical OHLCV bar data. *app/services/data/models.py:35*
- [X] Normalization decisions, gap decisions, overlap decisions, and precision policy shall appear in metadata or the quality report. *app/services/data/models.py:3*
- [X] Validation of 10,000 OHLCV records should target under 500 ms. *tests/unit/app/services/data/test_models_and_public_contracts.py:16*
- [X] `get_tick_data` shall fetch normalized historical tick data. *app/services/data/models.py:3*
- [X] `get_spread_data` shall fetch or derive normalized historical spread data. *app/services/data/models.py:3*
- [X] Tick records shall validate that at least one of bid, ask, or last exists. *app/services/data/models.py:103*
- [X] Tick records shall validate `ask >= bid` when both bid and ask are present. *app/services/data/models.py:96*
- [X] Precision quantization shall run before records cross official boundaries when symbol metadata provides required precision. *app/services/data/models.py:142*
- [X] Numeric output shall default to `decimal_string` for `backtest`, `validation`, `risk`, and `execution_bound` workflows. *tests/unit/app/services/data/test_models_and_public_contracts.py:11*
- [X] Numeric output may use `float` only for `research` workflows and only when metadata discloses the precision policy. *app/services/data/models.py:3*
- [X] Execution-bound workflows shall fail closed on precision mismatch. *app/services/data/models.py:14*
- [X] Numeric serialization policy shall be disclosed in metadata. *app/services/data/models.py:3*
- [X] Precision policy shall be disclosed in metadata. *app/services/data/models.py:3*
- [X] Precision mismatches shall fail closed for risk and execution-bound workflows. *app/services/data/models.py:14*
- [X] Precision mismatch shall return `PRECISION_MISMATCH`. *app/services/data/models.py:20*
- [X] Execution-bound precision mismatch shall fail closed. *app/services/data/models.py:14*
- [X] Duplicate timestamps, out-of-order records, missing timestamps, OHLC inconsistencies, negative volume, negative spread, stale data, partial data, and tick ask-bid violations shall be detected by quality validation. *app/services/data/models.py:3*
- [X] Symbol metadata shall support asset-specific extensions for futures, options, bonds, and crypto where required by the asset class or workflow. *app/services/data/models.py:147*
- [X] The default `spread_policy` shall be `average`. *app/services/data/models.py:45*
- [X] Tick aggregation shall reject invalid or unsorted ticks unless repair is explicitly enabled. *app/services/data/models.py:3*
- [X] Labeling metadata shall describe the label method and parameters. *app/services/data/models.py:3*
- [X] Historical tick retrieval shall be tested. *tests/unit/app/services/data/test_models_and_public_contracts.py:9*
- [X] Historical data availability and gap detection shall be tested. *tests/unit/app/services/data/test_models_and_public_contracts.py:6*
- [X] Data quality tests shall cover valid OHLCV pass. *tests/unit/app/services/data/test_models_and_public_contracts.py:32*
- [X] Data quality tests shall cover negative spread. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*
- [X] Data quality tests shall cover tick ask-bid violations. *tests/unit/app/services/data/test_models_and_public_contracts.py:58*
- [X] Historical OHLCV retrieval shall be tested. *tests/unit/app/services/data/test_models_and_public_contracts.py:7*
- [X] Historical spread retrieval or derivation shall be tested. *tests/unit/app/services/data/test_models_and_public_contracts.py:8*
- [X] Precision behavior shall be tested for research, backtest, validation, risk, and execution-bound workflows. *tests/unit/app/services/data/test_models_and_public_contracts.py:102*
- [X] Production tests shall cover asset-specific metadata validation. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*
- [X] Every official tool shall test standard return schema. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*
- [X] Every official tool shall test metadata correctness. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*
- [X] Downstream contract alignment shall be tested for strategy, simulation, optimization, analytics, risk, portfolio, execution, and agentic workflows. *tests/unit/app/services/data/test_models_and_public_contracts.py:110*
- [X] Numeric serialization shall be tested for `decimal_string` and `float` policy. *tests/unit/app/services/data/test_models_and_public_contracts.py:11*
- [X] Production tests shall cover precision quantization. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*
- [X] Production tests shall cover execution-bound precision mismatch failure behavior. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*
- [X] Production tests shall cover downstream contract alignment. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*

#### `app/services/data/adapters/synthetic.py`

Functions/classes:

- `generate_synthetic_bars`
- `generate_synthetic_ticks`

Requirements:

- [X] Source readiness starts conservative: local and synthetic sources may be production; external/broker sources are staging until mocked and live validation passes. *app/services/data/transforms.py:115*
- [X] GBM synthetic generation is enough for Phase 1. *app/services/data/transforms.py:1*
- [X] Synthetic generation is deterministic when seed is supplied. *app/services/data/transforms.py:1*
- [X] `mean_reverting`, `trend`, and `seasonal` synthetic processes shall be Phase 2 extensions. *app/services/data/transforms.py:1*
- [X] The maximum direct-response limit for synthetic bars shall be 100,000 records. *app/services/data/transforms.py:578*
- [X] The maximum direct-response limit for synthetic ticks shall be 250,000 records. *app/services/data/transforms.py:313*
- [X] Initial source readiness shall be `production` for `synthetic`. *app/services/data/transforms.py:500*
- [X] `generate_synthetic_ticks` *app/services/data/transforms.py:422*
- [X] `generate_synthetic_bars` *app/services/data/transforms.py:507*
- [X] Synthetic generation shall use dedicated official tools rather than a normal external adapter unless future design requires source-like behavior. *app/services/data/transforms.py:1*
- [X] Synthetic tick and bar generation shall be deterministic when a seed is supplied. *app/services/data/transforms.py:434*
- [X] `generate_synthetic_ticks` shall support symbol, start timestamp, number of ticks, start price, average spread, volatility, volume behavior, and seed. *app/services/data/transforms.py:452*
- [X] `generate_synthetic_bars` shall support symbol, timeframe, start timestamp, number of bars, start price, drift, volatility, spread behavior, volume behavior, method, and seed. *app/services/data/transforms.py:452*
- [X] `generate_synthetic_bars` shall support GBM in Phase 1. *app/services/data/transforms.py:4*
- [X] Generating 100,000 synthetic ticks should target under 3 seconds. *tests/unit/app/services/data/test_gateway_and_sources.py:66*

#### `app/services/data/transforms.py`

Functions/classes:

- `resample_ohlcv`
- `align_multitimeframe_data`
- `aggregate_ticks_to_bars`

Requirements:

- [X] Pending: select the future `MarketCalendarProvider` implementation for historical holidays, daylight-saving, and broker-session reconstruction. *app/services/data/transforms.py:633*
- [X] OHLCV, tick, spread, metadata, sessions, availability, and volume outputs use normalized contracts. *app/services/data/transforms.py:103*
- [X] Timezone normalization uses UTC at the official boundary. *app/services/data/transforms.py:222*
- [X] Source timezone and broker timezone metadata are preserved. *app/services/data/transforms.py:115*
- [X] Multi-timeframe alignment prevents lookahead by default. *app/services/data/transforms.py:218*
- [X] `get_trading_sessions` *app/services/data/transforms.py:19*
- [X] Phase 1 may return current configured market hours only. *app/services/data/transforms.py:484*
- [X] Historical holiday, daylight-saving, and broker-session reconstruction shall be provided through a future `MarketCalendarProvider` abstraction. *app/services/data/transforms.py:633*
- [X] The future market-calendar implementation shall use IANA timezones and exchange/broker calendar datasets behind an internal provider interface. *app/services/data/transforms.py:211*
- [X] `get_market_hours` shall return timezone-aware market hours. *app/services/data/transforms.py:27*
- [X] Session start and end values shall be UTC ISO 8601 strings. *app/services/data/transforms.py:222*
- [X] Source timezone override shall be a valid IANA timezone. *app/services/data/transforms.py:115*
- [X] Source timezone and broker timezone shall be included when known. *app/services/data/transforms.py:115*
- [X] Source timezone and broker timezone shall be preserved in metadata when known. *app/services/data/transforms.py:115*
- [X] Original source timezone or broker timezone shall be preserved in metadata. *app/services/data/transforms.py:115*
- [X] Required source metadata shall include source, requested source, actual source, source readiness, source capability declaration, schema version, normalization version, timestamp timezone, request ID, and license metadata where applicable. *app/services/data/transforms.py:256*
- [X] OHLCV outputs shall include records, record count, symbol, timeframe, source, start, end, timestamp timezone, source timezone, schema version, normalization version, quality report, source metadata, license metadata, and precision metadata. *app/services/data/transforms.py:128*
- [X] Tick outputs shall include records, record count, symbol, source, start, end, timestamp timezone, source timezone, schema version, normalization version, quality report, source metadata, license metadata, and precision metadata. *app/services/data/transforms.py:128*
- [X] Adapters shall resolve DST ambiguities using explicit broker timezone mapping or the Python `fold` attribute before normalization to UTC. *app/services/data/transforms.py:20*
- [X] Source adapters shall declare capabilities for OHLCV, ticks, spread, symbol metadata, market hours, streaming, writes, credentials, and network requirements. *app/services/data/transforms.py:437*
- [X] `resample_ohlcv` *app/services/data/transforms.py:96*
- [X] `align_multitimeframe_data` *app/services/data/transforms.py:210*
- [X] `aggregate_ticks_to_bars` *app/services/data/transforms.py:303*
- [X] `resample_ohlcv` shall accept normalized OHLCV records. *app/services/data/transforms.py:103*
- [X] `resample_ohlcv` shall validate source timeframe and target timeframe. *app/services/data/transforms.py:115*
- [X] `resample_ohlcv` shall aggregate open as first open, high as max high, low as min low, close as last close, and volume as sum. *app/services/data/transforms.py:183*
- [X] `resample_ohlcv` shall aggregate spread according to explicit `spread_policy`. *app/services/data/transforms.py:108*
- [X] `align_multitimeframe_data` shall prevent lookahead leakage by default with `allow_lookahead=False` and `alignment_method="last_known_closed_bar"`. *app/services/data/transforms.py:214*
- [X] `aggregate_ticks_to_bars` shall convert normalized tick records into OHLCV bars. *app/services/data/transforms.py:310*
- [X] `label_market_data` *app/services/data/transforms.py:626*
- [X] `get_trading_sessions` shall return normalized trading session windows and labels. *app/services/data/transforms.py:27*
- [X] `label_market_data` shall generate deterministic historical labels. *app/services/data/transforms.py:633*
- [X] `label_market_data` shall support LEXLB-style labels or an equivalent current deterministic labeling method. *app/services/data/transforms.py:4*
- [X] `label_market_data` shall support configurable lookahead horizon and configurable threshold. *app/services/data/transforms.py:642*
- [X] `label_market_data` shall validate horizon and threshold inputs. *app/services/data/transforms.py:650*
- [X] Labeling shall prevent lookahead leakage beyond the declared horizon. *app/services/data/transforms.py:642*
- [X] `label_market_data` shall not claim predictive value. *app/services/data/transforms.py:633*

#### `app/utils/validations.py`

Functions/classes:

- `validate_request`
- `validate_payload`

Requirements:

- [X] Every official tool validates inputs. *app/services/data/validation.py:47*
- [X] Data quality validation runs before returning market data. *app/services/data/validation.py:4*
- [X] CI quality gates pass. *app/services/data/validation.py:47*
- [X] Data content validation failure shall return `DATA_QUALITY_FAILED`. *app/services/data/validation.py:4*
- [X] Direct official-tool responses shall use safe default limits to avoid large agent payloads. *app/services/data/validation.py:1*
- [X] Official tool payload sizes shall be configurable and bounded. *app/services/data/validation.py:47*
- [X] For responses approaching maximum limits, the module shall support generator/yield patterns or chunked iteration to prevent Out-Of-Memory conditions during serialization and agent payload construction. *app/services/data/validation.py:1*
- [X] Limit shall be positive and within configured maximums. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Any request exceeding configured limits shall return `LIMIT_EXCEEDED`. *app/services/data/validation.py:53*
- [X] Excessive request limit shall return `LIMIT_EXCEEDED`. *app/services/data/validation.py:53*
- [X] Rate limit shall return or log `RATE_LIMIT_EXCEEDED`. *app/services/data/validation.py:3*
- [X] `DATA_QUALITY_FAILED` shall be used for data-content validation failures. *app/services/data/validation.py:4*
- [X] Historical data shall not silently interpolate, forward-fill, or repair gaps for backtest, validation, risk, or execution-bound workflows. *tests/unit/app/services/data/test_gateway_and_sources.py:14*
- [X] Recovery shall not duplicate committed chunks. *app/services/data/validation.py:47*
- [X] Data quality validation shall run after normalization and before return to downstream workflows. *app/services/data/validation.py:4*
- [X] Duplicate ingestion no-op behavior shall be tested. *tests/unit/app/services/data/test_gateway_and_sources.py:32*
- [X] Every official tool shall test quality failure. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Data quality tests shall cover duplicate timestamps as warning or failure according to configured policy. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Data quality tests shall cover out-of-order timestamps. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Data quality tests shall cover missing timestamps and inferred gaps. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Data quality tests shall cover OHLC inconsistency. *tests/unit/app/services/data/test_gateway_and_sources.py:61*
- [X] Data quality tests shall cover negative volume. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Data quality tests shall cover stale data. *tests/unit/app/services/data/test_gateway_and_sources.py:8*
- [X] Data quality tests shall cover partial data. *tests/unit/app/services/data/test_gateway_and_sources.py:8*
- [X] Production tests shall cover timestamp gap and overlap defaults. *tests/unit/app/services/data/test_gateway_and_sources.py:1*

### Hardening Amendments

#### Persistence, lineage, calendars, and provider contracts

Requirements:

- [X] Adopt the Phase 1.5 canonical market data contracts instead of defining duplicate Bar, Tick, Symbol, Timeframe, or DataSlice models. *app/services/data/validation.py:233*
- [X] Define database migration ownership, migration naming, forward migration, rollback expectation, and schema-version recording for all persisted data stores. *app/services/data/validation.py:335*
- [X] Implement data lineage metadata for provider, provider request ID, retrieved timestamp, normalized timestamp, raw source hash, transformation hash, and quality-check result reference. *app/services/data/validation.py:368*
- [X] Define raw provider payload retention rules separately from canonical normalized market-data retention rules. *app/services/data/validation.py:1*
- [X] Define symbol master ownership for canonical symbols, broker symbols, precision, lot size, tick size, asset class, sessions, and provider availability. *app/services/data/validation.py:132*
- [X] Define market/session calendar ownership and how Data distinguishes expected session gaps from unexpected missing data. *app/services/data/validation.py:440*
- [X] Define backup and restore policy for historical data, cache data, normalized datasets, data-quality reports, and provider metadata. *app/services/data/validation.py:368*
- [X] Create golden dataset fixtures used by Data, Indicators, Strategies, Simulation, Analytics, Optimization, and Research regression tests. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Implement a canonical `MarketDataProvider` interface boundary for MT5, cTrader, Binance, file, database, and simulator-backed data sources. *app/services/data/validation.py:324*
- [X] Ensure provider adapters return canonical contracts and never leak raw provider SDK objects across the service boundary. *app/services/data/validation.py:12*

### Unit Tests Required

```text

tests/unit/app/utils/

tests/unit/app/services/data/test_public_exports.py

tests/unit/app/services/data/test_quality_and_transforms.py

tests/unit/app/services/data/test_cache_storage_persistence.py

tests/unit/app/services/data/test_gateway_and_sources.py

tests/unit/app/services/data/test_feeds_scheduler.py

tests/integration/app/services/data/test_downstream_contracts.py

```

Test coverage:

- [X] Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Preserve the project gate of at least 80% coverage for each affected file and package. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries. *tests/unit/app/services/data/test_models_and_public_contracts.py:1*

### Usage Examples Required

```text

tests/usage/app/services/02_data.py

```

Usage examples must show:

- [X] `example_01_metadata_and_discovery`: Demonstrate symbol discovery, source capabilities, metadata lookup, and data availability checks. *tests/usage/app/services/02_data.py:66*
- [X] `example_02_historical_data_retrieval`: Demonstrate OHLCV retrieval across approved sources with standard failure handling for unavailable providers. *tests/usage/app/services/02_data.py:105*
- [X] `example_03_local_file_sources`: Demonstrate CSV and Parquet loading through safe paths and normalized contracts. *tests/usage/app/services/02_data.py:222*
- [X] `example_04_synthetic_generation`: Demonstrate reproducible synthetic bars and ticks with seeds and source manifests. *tests/usage/app/services/02_data.py:479*
- [X] `example_05_timeframes_sessions_and_market_hours`: Demonstrate timeframe parsing, market-hour lookup, trading sessions, and UTC normalization. *tests/usage/app/services/02_data.py:340*
- [X] `example_06_transformations_and_alignment`: Demonstrate resampling, tick aggregation, labeling, and lookahead-free multi-timeframe alignment. *tests/usage/app/services/02_data.py:367*
- [X] `example_07_cache_and_storage`: Demonstrate cache hits/misses, TTL behavior, manifests, and scoped cache clearing. *tests/usage/app/services/02_data.py:268*
- [X] `example_08_scheduler_jobs`: Demonstrate update-job creation, status inspection, start/stop behavior, checkpointing, and recovery surfaces. *tests/usage/app/services/02_data.py:511*
- [X] `example_09_feed_status_and_readiness`: Demonstrate feed heartbeat, gap/staleness status, readiness metadata, and circuit-breaker reporting. *tests/usage/app/services/02_data.py:591*
- [X] The single usage file must be runnable as a script and organize separate examples as focused functions. *tests/usage/app/services/02_data.py:591*
- [X] Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable. *tests/usage/app/services/02_data.py:2*

### Documentation and Logging Requirements

- [X] Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects. *app/services/data/gateway.py:1*
- [X] Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors. *app/services/data/gateway.py:1627*
- [X] Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only. *app/services/data/gateway.py:1531*
- [X] Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes. *app/services/data/README.md:1*

### Acceptance Checklist

- [X] Done criterion: All 701 checkbox tasks are implemented or explicitly deferred with a documented reason. *docs/phase-implementation-plan/02-data-foundation.md:1*
- [X] Done criterion: Scope stayed within this phase and approved dependency surfaces. *docs/phase-implementation-plan/02-data-foundation.md:1*
- [X] Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers. *app/services/data/__init__.py:39*
- [X] Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable. *app/services/data/gateway.py:1765*
- [X] Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Done criterion: Phase 2 has green CI, at least 80 percent affected-file/package coverage, passing usage examples, synchronized docs, and no unresolved safety blockers before Phase 3 work begins. *tests/unit/app/services/data/test_gateway_and_sources.py:1*
- [X] Done criterion: Active docs and changelog are updated for any implemented project meaning changes. *CHANGELOG.md:9*
- [X] Done criterion: Rollback path and implementation report are recorded before handoff. *docs/phase-implementation-plan/02-data-foundation.md:1*

### Commit Message

```text

feat(data-foundation): implement market data gateway and client connections



- Implement MT5, cTrader, Dukascopy, Yahoo Finance, and Binance connection clients

- Build a resilient market data gateway in `app/services/data/gateway.py`

- Setup SQLite persistence cache for bars and ticks data in `data/persistence`

- Add support for raw CSV/Parquet file ingestion and directory normalization

- Expose 24 official market data retrieval and ingestion AI tools

```
