## Phase 2 Data Foundation

### Goal

Implement the Data Foundation requirements under `app/services/data/` while preserving the phase module boundaries and governance rules.

Task inventory: 701 checkbox tasks (0 checked, all unchecked).

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

app/services/data/logger.py

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

- [ ] Backward compatibility remains out of scope.
- [ ] The module shall preserve current data-domain capabilities at the capability level, not by preserving old function names.
- [ ] The v8 specification remains the authoritative baseline, with this final document acting as the production-hardening closure layer.
- [ ] Public streaming subscription tools remain out of Phase 1.
- [ ] Historical market-hours reconstruction is deferred until a market-calendar provider is approved.
- [ ] Pending: define any future public streaming subscription tool surface before export.
- [ ] Pending: track future-phase decisions as implementation planning issues rather than treating them as Phase 1 blockers.
- [ ] `app/services/data/__init__.py` contains only imports and `__all__`.
- [ ] Official exports match this requirements document.
- [ ] Every official tool supports `request_id`.
- [ ] Every official tool logs structured events.
- [ ] Every official tool has unit tests.
- [ ] Every official tool has usage examples where applicable.
- [ ] Downstream modules import only through `app.services.data`.
- [ ] The module shall be implemented as a greenfield professional production module.
- [ ] CI gates shall pass before production sign-off: pre-commit hooks, Ruff check, Ruff format, mypy strict, pytest, and coverage above 80%.
- [ ] Official exports shall match this requirements document.
- [ ] Credentials are not exposed or logged.
- [ ] Test coverage is above 80%.
- [ ] `app/services/data/__init__.py` shall export only the approved official tool surface in Section 1.2 unless a future specification explicitly adds more.
- [ ] The module shall expose only safe, intentional, agent-callable tools from `app/services/data/__init__.py`.
- [ ] `app/services/data/__init__.py` shall export only the following official tools:
- [ ] `get_data`
- [ ] `list_symbols`
- [ ] `get_market_hours`
- [ ] `app/services/data/__init__.py` shall contain only imports and `__all__`.
- [ ] Parent traversal with `..` shall be rejected.
- [ ] Any future official tool addition shall require an explicit specification update.
- [ ] All timestamps crossing the official AI-tool boundary shall be UTC ISO 8601 strings.
- [ ] `get_market_hours` Phase 1 may return current configured hours only.
- [ ] The primary volume value shall be disclosed through `volume_kind`.
- [ ] Every official tool shall support `request_id`.
- [ ] Resampling 100,000 M1 bars to H1 should target under 3 seconds.
- [ ] Official tools shall be typed.
- [ ] Every official tool shall accept `request_id`.
- [ ] Start and end timestamps shall be UTC ISO 8601 when provided.
- [ ] Parent traversal using `..` shall be rejected.
- [ ] Hidden/system directories shall be rejected unless explicitly allowed.
- [ ] Authentication failure shall return `AUTHENTICATION_FAILED`.
- [ ] Open circuit breaker shall return `CIRCUIT_BREAKER_OPEN`.
- [ ] Official tools shall not expose raw exceptions.
- [ ] Unsupported timeframe shall return `UNSUPPORTED_TIMEFRAME`.
- [ ] Permission failure shall return `PERMISSION_DENIED`.
- [ ] Hidden or system directories shall be rejected unless explicitly allowed by configuration.
- [ ] Historical market-hour reconstruction shall return `UNSUPPORTED_OPERATION` unless an approved calendar provider supports it.
- [ ] Allowed `workflow_context` values shall be exhaustive: `research`, `backtest`, `validation`, `risk`, and `execution_bound`.
- [ ] `workflow_context` shall accept only `research`, `backtest`, `validation`, `risk`, and `execution_bound`.
- [ ] Start shall be before end.
- [ ] Timestamp overlap with no safe policy shall return `TIMESTAMP_OVERLAP`.
- [ ] Exploratory backtests may opt into `float` only when explicitly marked non-validation.
- [ ] State writes shall be atomic.
- [ ] Unsupported extensions shall be rejected.
- [ ] Stale lock recovery shall be auditable.
- [ ] Crash recovery shall be idempotent and auditable.
- [ ] Failed crash recovery shall return `STATE_RECOVERY_FAILED`.
- [ ] The gateway shall enforce no-silent-fallback behavior.
- [ ] Circuit breaker transitions shall be auditable.
- [ ] Production logic shall not use `print()`.
- [ ] Credentials shall be resolved internally from approved configuration or environment variables.
- [ ] Official AI tools shall not accept raw passwords unless a future explicit security design approves it.
- [ ] Official AI tools shall not expose credential loaders.
- [ ] Missing credentials shall return `CREDENTIALS_MISSING`.
- [ ] Public streaming subscription tools shall remain out of Phase 1.
- [ ] Public streaming subscription tools shall remain out of Phase 1.
- [ ] Unsupported public streaming operations shall fail closed with `UNSUPPORTED_OPERATION`.
- [ ] Labels shall align to input timestamps.
- [ ] Connection leak detection shall be tested.
- [ ] Conflicting ingestion key behavior shall be tested.
- [ ] Every official tool shall test invalid input.
- [ ] Recovery from stale locks shall be tested.
- [ ] No-silent-fallback behavior shall be tested.
- [ ] Circuit breaker open, half-open, and closed transitions shall be tested.
- [ ] Test coverage shall remain above 80%.
- [ ] Every official tool shall test successful call.
- [ ] Every official tool shall test unsupported timeframe where applicable.
- [ ] Every official tool shall test empty result.
- [ ] Every official tool shall test request ID propagation.
- [ ] Every official tool shall test logging footprint.
- [ ] Every official tool shall test side-effect flags and read-only classification where applicable.
- [ ] Production tests shall cover raw data hash propagation.
- [ ] Production tests shall cover rejection or logging of interpolation and forward-fill outside research workflows.
- [ ] Production sign-off commands shall pass.
- [ ] Coverage shall remain above 80%.

#### `app/services/data/feeds.py`

Functions/classes:

- `FeedStatus`
- `start_feed`
- `stop_feed`
- `get_feed_status`

Requirements:

- [ ] Internal real-time feed support, feed state, and feed status are in scope for production readiness.
- [ ] Documentation shall include real-time feed limitations for Phase 1.
- [ ] `get_feed_status` is the canonical feed observability tool.
- [ ] `VALIDATION_FAILED`, `BUFFER_OVERFLOW`, and `DATA_DROPPED` are included in the deterministic error-code list.
- [ ] Pending: define the promotion process and evidence package for moving MT5, cTrader, Dukascopy, Binance symbol discovery, or real-time feed gateway from `staging` to `production`.
- [ ] Feed inspection shall be added through `get_feed_status`.
- [ ] `BUFFER_OVERFLOW` and `DATA_DROPPED` shall be added to deterministic error codes.
- [ ] Reconnect and retry logic shall use exponential backoff with randomized jitter.
- [ ] Real-time feed state is observable and resilient.
- [ ] `get_feed_status`
- [ ] `get_feed_status` shall be read-only and shall not expose raw stream handles, sockets, clients, credentials, or connection strings.
- [ ] The deterministic error-code list shall include `DATA_DROPPED`.
- [ ] Real-time records shall normalize to the same OHLCV, tick, and spread contracts used by historical data.
- [ ] Real-time timestamps shall normalize to UTC before crossing any official boundary.
- [ ] Missing, stale, partial, conflicting, dropped, revised, or license-restricted data shall be flagged.
- [ ] Internal real-time feed support shall be in scope for Phase 1 hardening where a source declares live or streaming capability.
- [ ] The module shall expose one low-risk, read-only real-time feed observability tool named `get_feed_status`.
- [ ] Internal feed state shall be observable through `get_feed_status` so operators can monitor heartbeat, buffer health, dropped data, gap reconciliation, reconnects, and circuit-breaker state.
- [ ] The deterministic error-code list shall include `BUFFER_OVERFLOW`.
- [ ] The deterministic error-code list shall include `FEED_HEARTBEAT_TIMEOUT`.
- [ ] The deterministic error-code list shall include `FEED_RECONCILIATION_FAILED`.
- [ ] Initial source readiness shall be `staging` for `real_time_feed_gateway` until buffer, heartbeat, recovery, gap reconciliation, and circuit-breaker tests pass.
- [ ] The module shall support an internal real-time feed layer for live tick, spread, and bar-oriented data where source adapters declare live or streaming capability.
- [ ] Real-time feed state shall be observable through `get_feed_status`.
- [ ] `get_feed_status` shall report source, symbol, data kind, connection state, feed readiness, last heartbeat timestamp, last event timestamp, buffer depth, configured buffer capacity, dropped event count, gap count, reconnect count, circuit breaker state, and last error code.
- [ ] Real-time feeds shall maintain heartbeat tracking.
- [ ] Real-time feeds shall detect heartbeat timeouts and return or log `FEED_HEARTBEAT_TIMEOUT`.
- [ ] Real-time buffer overflow shall follow an explicit policy: `halt`, `drop_and_reconcile`, or `backpressure`.
- [ ] Real-time feed gaps shall be visible to downstream consumers.
- [ ] Real-time feed gaps shall not be hidden by synthetic fills.
- [ ] Real-time reconnection shall use exponential backoff with randomized jitter.
- [ ] Real-time feeds shall use bounded buffers.
- [ ] Feed status shall expose heartbeat health, buffer health, gap health, reconnect health, circuit breaker state, and last error.
- [ ] Real-time feed ingestion shall use bounded queues and shall not allow unbounded memory growth.
- [ ] Retry and reconnection shall use exponential backoff with randomized jitter.
- [ ] Oversized source adapters shall be split into focused client, instrument, normalization, and live-feed modules where needed.
- [ ] Overflow policy shall accept only `halt`, `drop_and_reconcile`, or `backpressure`.
- [ ] Reconnect policy shall include maximum retries, exponential backoff, jitter, maximum backoff, and circuit breaker cooldown.
- [ ] Feed status requests shall accept feed ID, source, symbol, data kind, and request ID.
- [ ] Feed status outputs shall include feed ID, state, heartbeat timestamp, last event timestamp, buffer depth, dropped count, gap count, reconnect count, circuit breaker state, and last error.
- [ ] Reconnection shall use exponential backoff with randomized jitter.
- [ ] Feed overflow with `backpressure` shall slow ingestion without unbounded memory growth.
- [ ] Feed status shall not expose raw connection handles, socket details, client objects, or credential-bearing connection strings.
- [ ] Feed heartbeat timeout shall return or log `FEED_HEARTBEAT_TIMEOUT`.
- [ ] Feed buffer overflow shall return or log `BUFFER_OVERFLOW`.
- [ ] Dropped feed records shall return or log `DATA_DROPPED`.
- [ ] Failed feed gap reconciliation shall return `FEED_RECONCILIATION_FAILED`.
- [ ] The module shall provide reliable, normalized, auditable access to historical, real-time, local, synthetic, broker, and external market data.
- [ ] Dropped data gap creation shall be tested.
- [ ] Feed heartbeat tracking shall be tested.
- [ ] Feed heartbeat timeout shall be tested.
- [ ] Feed buffer limit behavior shall be tested.
- [ ] Feed overflow with `halt` shall be tested.
- [ ] Feed overflow with `drop_and_reconcile` shall be tested.
- [ ] Feed overflow with `backpressure` shall be tested.
- [ ] Feed reconnect with exponential backoff and jitter shall be tested.
- [ ] `get_feed_status` schema shall be tested.

#### `app/services/data/persistence.py`

Functions/classes:

- `Repository`
- `save_state`
- `load_state`

Requirements:

- [ ] The module shall persist source circuit breaker state.
- [ ] Documentation shall include database migration procedure.
- [ ] SQLite is sufficient for single-node local state persistence.
- [ ] The persistence abstraction must be TSDB-ready for future high-frequency tick and spread storage.
- [ ] Pending: select the future high-frequency tick/spread TSDB backend after the TSDB-ready persistence interface is validated.
- [ ] Idempotency keys shall be deterministically derived from source, symbol, data kind, timeframe, start, end, schema version, and normalization version.
- [ ] Database persistence shall enforce connection limits, timeouts, and leak detection.
- [ ] Circuit breaker state shall persist across restarts.
- [ ] Persistence shall support a future append-optimized TSDB backend.
- [ ] No DataFrame, NumPy array, SDK object, stream handle, socket, or database client crosses the official tool boundary.
- [ ] Database persistence is transactional, bounded, idempotent, and recovery-aware.
- [ ] Production sign-off shall include implemented spec version, test command output summary, coverage percentage, exported tool list, known limitations, enabled source adapters, required environment variables, source readiness manifest, license manifest, persistence backend, and downstream modules validated.
- [ ] On restart, a source with a persisted open circuit breaker shall remain open or half-open for the configured cooldown period and shall not immediately hammer the failing external source.
- [ ] Circuit breaker open state shall persist across restarts.
- [ ] The module shall persist source revision and raw hash metadata.
- [ ] Large historical datasets shall be persisted and referenced by metadata instead of returned inline when response limits are exceeded.
- [ ] Persisted data requested with an older `schema_version` than the current canonical version shall either be safely migrated on read or rejected with `DATA_SCHEMA_DRIFT` and re-fetch guidance.
- [ ] Parquet shall remain the preferred local file format for large persisted datasets in Phase 1.
- [ ] The deterministic error-code list shall include `DATABASE_ERROR`.
- [ ] The deterministic error-code list shall include `DB_CONNECTION_ERROR`.
- [ ] The deterministic error-code list shall include `DB_WRITE_FAILED`.
- [ ] The persistence interface shall be append-optimized and TSDB-ready.
- [ ] TimescaleDB shall be the preferred future relational time-series backend for high-frequency tick and spread persistence when multi-node or high-throughput persistence becomes required.
- [ ] InfluxDB or equivalent metrics-oriented TSDBs may be considered later for telemetry or high-frequency observational data, but they shall not replace the canonical persistence abstraction.
- [ ] Internal adapters may use pandas, NumPy, broker SDKs, HTTP clients, MCP clients, sockets, database clients, and file-system objects, but those objects shall not cross the official AI-tool boundary.
- [ ] Schema migrations shall enforce backward compatibility checks.
- [ ] If a requested `schema_version` is older than the current canonical version, the system shall either perform an on-the-fly safe migration or return `DATA_SCHEMA_DRIFT` with a recommendation to re-fetch.
- [ ] SQLite shall be the default single-node ACID-capable persistence backend.
- [ ] The persistence abstraction shall support append-optimized TSDB backends in future phases without rewriting gateway routing logic.
- [ ] The persistence abstraction shall support append-only ingestion metadata.
- [ ] Persistence writes shall use transactions for atomic state changes.
- [ ] Database writes shall include deterministic idempotency keys.
- [ ] Data ingestion idempotency keys shall be derived from a hash of source, symbol, data kind, timeframe, start time, end time, schema version, and normalization version.
- [ ] Database writes shall be idempotent under retry.
- [ ] Database writes shall distinguish insert, update, no-op duplicate, and conflict.
- [ ] Database conflicts shall return deterministic errors and shall not silently overwrite committed data.
- [ ] The persistence layer shall enforce connection pool limits, connection timeouts, and automatic leak detection.
- [ ] Database migrations shall be versioned, auditable, and reversible where practical.
- [ ] Schema migrations shall enforce backward compatibility or mandatory invalidation and re-ingestion.
- [ ] The module shall persist ingestion idempotency keys.
- [ ] Response metadata shall include tool name, tool version, tool category, risk level, request ID, execution time, read-only flag, writes-file flag, modifies-database flag, places-trade flag, and requires-network flag.
- [ ] Tools that mutate persisted state shall set `modifies_database=True` when persistence state changes.
- [ ] Retrieval tools that only read local state shall keep `modifies_database=False`.
- [ ] Database connection pools shall use strict limits and timeouts.
- [ ] Backward compatibility aliases shall not be included unless a future implementation phase explicitly approves a temporary migration shim.
- [ ] Database persistence requests shall include entity type, idempotency key, schema version, normalization version, transaction metadata, and request ID where applicable.
- [ ] Database migrations shall include migration ID, source schema version, target schema version, compatibility result, and rollback policy.
- [ ] Metadata shall include tool identity, category, risk level, request ID, execution time, side-effect flags, trade flag, network flag, source readiness where applicable, precision policy where applicable, and persistence flags where applicable.
- [ ] Database state shall not store plaintext secrets.
- [ ] Database connection failure shall return `DB_CONNECTION_ERROR`.
- [ ] Database write failure shall return `DB_WRITE_FAILED`.
- [ ] Persistence failure shall return `DATABASE_ERROR`.
- [ ] The module shall persist data license and attribution metadata.
- [ ] The module shall normalize all source-specific market data into canonical internal contracts before returning or persisting records.
- [ ] If an adapter trips a circuit breaker, the degraded state shall be persisted.
- [ ] Every source adapter shall avoid returning raw SDK, client, stream, socket, or database objects.
- [ ] Long-running real-time feed ingestion shall not exhaust database connection pools.
- [ ] The module shall persist feed state.
- [ ] Official tools shall never return raw pandas objects, NumPy arrays, raw SDK objects, sockets, stream handles, database clients, `None`, or unstructured exceptions.
- [ ] The maximum persisted synthetic generation size shall be 1,000,000 records unless explicitly raised by configuration and covered by performance tests.
- [ ] Connection pool limit behavior shall be tested.
- [ ] Every official tool shall test that raw DataFrame, NumPy, SDK, stream, socket, client, and database objects do not cross the official boundary.
- [ ] SQLite or default persistence backend initialization shall be tested.
- [ ] Persistence transactions shall be tested.
- [ ] Database connection timeout handling shall be tested.
- [ ] Database idempotency keys shall be tested.
- [ ] Schema migration compatibility checks shall be tested.
- [ ] No raw SDK, stream, socket, client, or database object leakage shall be tested.
- [ ] Circuit breaker state persistence across restart shall be tested.

#### `app/services/data/README.md`

Functions/classes:

- No runtime functions/classes; documentation artifact only.

Requirements:

- [ ] Documentation shall include a data module README or docs section.
- [ ] Documentation shall include the official tool catalog.
- [ ] Documentation shall include the final `__all__` export list.
- [ ] Documentation shall include environment variable reference.
- [ ] Documentation shall include crash recovery runbook.
- [ ] Documentation shall include circuit breaker behavior and recovery procedure.
- [ ] Documentation shall include production sign-off template.
- [ ] This requirements document belongs in `docs/planning/DOMAIN.md` because it covers the full data module rather than one sprint.
- [ ] Public functions and classes shall contain useful docstrings.

#### `app/services/data/scheduler.py`

Functions/classes:

- `create_job`
- `start_job`
- `stop_job`
- `get_job_status`

Requirements:

- [ ] Documentation shall explain why `get_data_update_job_status` and `get_feed_status` are included.
- [ ] Documentation shall include usage examples for market data, local storage, symbols, synthetic generation, labeling, scheduler, job status, and feed status.
- [ ] Documentation shall include troubleshooting for MT5, cTrader, Dukascopy, Binance symbol discovery, local storage, cache, database persistence, scheduler, crash recovery, and feed health.
- [ ] `get_data_update_job_status` is the canonical scheduler status tool.
- [ ] `get_update_job_status`, `create_update_job`, `start_update_job`, and `stop_update_job` are not official exports.
- [ ] The scheduler naming conflict shall be resolved by exporting only `create_data_update_job`, `start_data_update_job`, `stop_data_update_job`, `run_data_update_job_once`, and `get_data_update_job_status` for scheduler lifecycle/status.
- [ ] Status inspection shall be added through `get_data_update_job_status`.
- [ ] A central limits manifest shall define maximum records, maximum date range, maximum cache TTL, maximum synthetic generation size, maximum backfill chunk size, maximum feed buffer depth, and maximum scheduler frequency.
- [ ] Response examples shall be documented for OHLCV, tick, spread, market hours, trading sessions, availability, historical volume, scheduler status, feed status, and error responses.
- [ ] Real-time buffer overflow shall flag gaps and trigger backfill when configured and supported.
- [ ] Scheduler lifecycle is explicit, idempotent, and crash-recoverable.
- [ ] Production sign-off artifact is created before release.
- [ ] The names `create_update_job`, `start_update_job`, and `stop_update_job` shall not be exported as official tools.
- [ ] The name `get_update_job_status` shall not be exported as an official tool.
- [ ] External or vendor data sources shall include license metadata before data is stored, exported, scheduled, or used in validation, risk, or execution-bound workflows.
- [ ] `get_data_update_job_status`
- [ ] `get_data_update_job_status` shall be read-only and shall not mutate scheduler state.
- [ ] `get_data_update_job_status` shall be non-networked unless job metadata requires source health lookup.
- [ ] License metadata shall be enforced before storage, scheduler export, or artifact generation.
- [ ] Missing license metadata shall fail closed with `LICENSE_RESTRICTION` for storage, scheduler, export, validation, risk, and execution-bound workflows.
- [ ] The default backfill chunk size for OHLCV bars shall be 100,000 records or 30 calendar days, whichever is reached first.
- [ ] The default backfill chunk size for ticks and spreads shall be 1,000,000 records or 1 calendar day, whichever is reached first.
- [ ] Real-time gaps shall be reconciled through historical backfill where supported and configured.
- [ ] Historical backfills shall be resumable and idempotent.
- [ ] Historical requests shall support chunk size, backfill mode, gap resolution policy, overlap policy, data version policy, precision policy, workflow context, and persistence target where applicable.
- [ ] Backfill idempotency keys shall be derived from source, symbol, data kind, timeframe, start time, end time, schema version, and normalization version.
- [ ] The deterministic error-code list shall include `CHECKPOINT_CORRUPTED`.
- [ ] The module shall persist backfill checkpoints.
- [ ] Crash recovery shall log the lease-expiration reason.
- [ ] Recovery shall resume from the last committed checkpoint, not the last attempted record.
- [ ] Stale locks shall expire according to configured lease timeout.
- [ ] Backfill and recovery events shall be auditable.
- [ ] Corrupted state shall return `STATE_RECOVERY_FAILED` or `CHECKPOINT_CORRUPTED`.
- [ ] Corrupted checkpoint shall return `CHECKPOINT_CORRUPTED`.
- [ ] Scheduler frequency shall not be more frequent than once per minute unless a dedicated live-feed ingestion mechanism is used.
- [ ] SQLite shall be the default ACID-capable single-node persistence backend for scheduler state, feed state, cache metadata, checkpoints, idempotency keys, and audit state.
- [ ] The module shall include internal layers for contracts, responses, validation, normalization, quality, timeframes, cache, registry, gateway routing, source adapters, storage, persistence, transforms, generators, labeling, scheduler, feed state, versioning, precision, rate limits, licensing, and audit logging.
- [ ] If the overflow policy is `drop_and_reconcile`, the system shall immediately flag a data gap, update feed gap-count metadata, emit `DATA_DROPPED` or `BUFFER_OVERFLOW`, and trigger historical backfill for the missing time window when supported by the source.
- [ ] Real-time feed state shall persist feed leases, heartbeat state, buffer metadata, last processed timestamp, last committed checkpoint, gap windows, reconnect count, and circuit breaker state.
- [ ] Live data shall be persisted only through explicit persistence, scheduler, feed-ingestion, or storage workflows.
- [ ] The module shall define a persistence abstraction for scheduler state, feed state, cache metadata, source revisions, license metadata, data manifests, checkpoints, idempotency keys, circuit breaker state, and audit events.
- [ ] The module shall explicitly define its concurrency model: `asyncio` for real-time feed ingestion and network I/O, and `multiprocessing` or chunked batch processing for heavy synthetic generation and large historical backfills to prevent event-loop blocking and GIL contention.
- [ ] The gateway shall maintain a global, thread/async-safe rate-limit token bucket or counter per source to prevent concurrent scheduler jobs, feeds, and agent requests from collectively breaching external API rate limits.
- [ ] The same `request_id` shall appear in logs, response metadata, adapter logs, cache logs, scheduler logs, feed logs, and persistence audit records where feasible.
- [ ] Feed configuration shall include source, symbol, data kind, optional timeframe, buffer capacity, overflow policy, heartbeat timeout, reconnect policy, backfill-on-gap flag, persistence target, and request ID.
- [ ] Official tools shall convert adapter, gateway, cache, persistence, scheduler, and feed exceptions into standard error responses.
- [ ] Feed overflow with `drop_and_reconcile` shall record a gap and attempt historical backfill if supported.
- [ ] Feed overflow with `halt` shall stop feed ingestion and require operator or scheduler recovery policy.
- [ ] Quality reports shall be included for fetched, loaded, generated, resampled, aggregated, and backfilled data.
- [ ] The authoritative scheduler lifecycle tool names shall be `create_data_update_job`, `start_data_update_job`, `stop_data_update_job`, and `run_data_update_job_once`.
- [ ] The module shall expose one low-risk, read-only scheduler status tool named `get_data_update_job_status`.
- [ ] The deterministic error-code list shall include `JOB_NOT_FOUND`.
- [ ] The deterministic error-code list shall include `SCHEDULER_ERROR`.
- [ ] Scheduler jobs shall default to a maximum of 500 symbols per job and 20 timeframes per job unless configuration and tests approve larger workloads.
- [ ] `create_data_update_job`
- [ ] `start_data_update_job`
- [ ] `stop_data_update_job`
- [ ] `run_data_update_job_once`
- [ ] Historical backfill jobs shall be chunked, resumable, checkpointed, idempotent, and safe to retry.
- [ ] Historical backfill jobs shall persist progress by source, symbol, data kind, timeframe, start time, end time, schema version, normalization version, chunk ID, and idempotency key.
- [ ] Historical backfill jobs shall not mark a chunk complete until records, metadata, quality report, source revision metadata, license metadata, and persistence manifest are committed.
- [ ] Historical backfill jobs shall detect gaps before and after ingestion.
- [ ] The module shall persist scheduler job state.
- [ ] Jobs left in `running` state after a crash shall idempotently transition to `recovering` or `failed` according to recovery policy.
- [ ] Recovery shall not mark incomplete jobs as completed.
- [ ] `create_data_update_job` shall create persisted update job definitions.
- [ ] `start_data_update_job` shall start recurring execution for a valid existing job or valid schedule.
- [ ] `start_data_update_job` shall not behave as a one-time run when schedule is omitted.
- [ ] `run_data_update_job_once` shall execute one immediate update run and shall not create a recurring schedule.
- [ ] `stop_data_update_job` shall stop or disable scheduled execution.
- [ ] `get_data_update_job_status` shall inspect job state without mutating scheduler state.
- [ ] Scheduler state shall include `created`, `running`, `stopped`, `failed`, `completed`, and `recovering`.
- [ ] Scheduler job requests shall include job name, source, symbol or symbols, optional timeframe or timeframes, schedule, storage target, data kind, and request ID.
- [ ] Data update job definitions shall include job ID, job name, source, symbols, timeframes, data kind, storage format, storage path, optional start/end, optional schedule, enabled flag, created timestamp, and updated timestamp.
- [ ] Job names shall be stable, non-empty, and safe for file and database keys.
- [ ] Duplicate job creation shall be idempotent or return a deterministic duplicate-job error.
- [ ] Starting an already running job shall not create duplicate workers silently.
- [ ] Scheduler jobs shall use checkpointing, idempotency, lease-based locks, retry policy, cache policy, path policy, license policy, and crash recovery policy.
- [ ] Scheduler tools shall be medium-risk except `get_data_update_job_status`, which shall be low-risk and read-only.
- [ ] Schedules shall be parseable and bounded.
- [ ] Scheduler and cache tools shall include side-effect metadata.
- [ ] Backfill jobs shall include source, symbols, timeframes, data kinds, start, end, chunk policy, destination, schedule or one-time mode, recovery policy, request ID, and metadata options.
- [ ] Job status outputs shall include job ID, state, enabled flag, last run status, last checkpoint, last error, next scheduled run, lease status, recovery state, and request ID.
- [ ] Persistence errors shall not mark jobs or chunks as complete.
- [ ] Missing source license metadata shall return `LICENSE_RESTRICTION` for storage, scheduler, validation, risk, and execution-bound workflows.
- [ ] Missing scheduler job shall return `JOB_NOT_FOUND`.
- [ ] Scheduler errors shall return `SCHEDULER_ERROR`.
- [ ] A running job found after crash shall transition idempotently to `recovering` or `failed`, not remain indefinitely `running`.
- [ ] Backfill chunking shall be tested.
- [ ] Backfill idempotency shall be tested.
- [ ] Backfill source revision handling shall be tested.
- [ ] Automatic historical backfill after dropped data shall be tested where source supports backfill.
- [ ] Backfill checkpoint resume shall be tested.
- [ ] Backfill cache invalidation shall be tested.
- [ ] Recovery from corrupted checkpoints shall be tested.
- [ ] Every official tool shall test dry-run behavior for cache, scheduler, and file operations where applicable.
- [ ] License restriction enforcement shall be tested for storage and scheduler exports.
- [ ] Scheduler tests shall cover create job, start job, stop job, and run once.
- [ ] Scheduler tests shall cover duplicate start behavior.
- [ ] Scheduler tests shall cover duplicate job creation behavior.
- [ ] Scheduler tests shall cover missing job behavior.
- [ ] Scheduler tests shall cover invalid source, symbol, timeframe, and schedule.
- [ ] Scheduler tests shall cover state persistence.
- [ ] Backfill license enforcement shall be tested.

#### `app/services/data/sources.py`

Functions/classes:

- `SourceAdapter`
- `SourceRegistry`
- `get_source_adapter`

Requirements:

- [ ] Documentation shall include a source adapter catalog.
- [ ] Documentation shall include the source readiness manifest.
- [ ] Documentation shall include the source license manifest.
- [ ] The HaruQuantAI Tool Function Standard, Code Quality Standard, Agent Standard, and Agentic AI Playbook exist outside this source-requirements document and may define cross-cutting details not repeated in the data module specification.
- [ ] The broker/data gateway is internal and routes one internal contract to many external APIs.
- [ ] Phase 1 may proceed without complete external source adapter implementations when disabled or unavailable adapters fail safely and deterministically and contracts, responses, validation, timeframes, registry, exports, and tests meet Phase 1 acceptance.
- [ ] No blocking open questions remain for Phase 1 implementation based on the current source material.
- [ ] A source readiness manifest shall be maintained.
- [ ] A source license manifest shall be maintained.
- [ ] cTrader and Dukascopy clients are internal.
- [ ] Broker adapters never place trades.
- [ ] The source registry shall not be exported as an official AI tool unless a future requirement explicitly approves it.
- [ ] When a source provides both tick volume and real volume, both shall be preserved.
- [ ] Disabled or unconfigured source shall return `SOURCE_NOT_CONFIGURED`.
- [ ] Historical data shall preserve source revision metadata where available.
- [ ] Network retry exhaustion shall return deterministic error codes and include retry metadata.
- [ ] Unsupported source shall return `UNSUPPORTED_SOURCE`.
- [ ] Unsupported valid-source capability shall return `UNSUPPORTED_OPERATION`.
- [ ] Empty source result shall return `EMPTY_RESULT` or `DATA_NOT_FOUND` according to context.
- [ ] Network timeout shall return `TIMEOUT`.
- [ ] Network failure shall return `NETWORK_ERROR`.
- [ ] Broker unavailable shall return `BROKER_UNAVAILABLE`.
- [ ] A central limits manifest shall define default and maximum values by data kind, source, workflow context, and response mode.
- [ ] Symbol metadata shall normalize asset class, base currency, quote currency, contract size, tick size, tick value, point, digits, lot limits, lot step, margin currency, profit currency, trading hours, and source metadata.
- [ ] Either date range or limit shall be provided unless the source has a safe default.
- [ ] External source calls shall use explicit timeouts, bounded retries, rate limits, and circuit breakers.
- [ ] The module shall not place trades, close positions, modify broker account state, modify terminal settings, modify risk settings, or perform execution actions.
- [ ] OHLCV records shall normalize timestamp, open, high, low, close, volume, tick volume, real volume, spread, source, symbol, and timeframe.
- [ ] `get_historical_volume` may derive volume from OHLCV, tick records, or source-native volume data if the public response contract remains stable and tested.
- [ ] Tick records shall normalize timestamp, bid, ask, last, volume, spread, source, and symbol.
- [ ] Spread records shall normalize timestamp, symbol, bid, ask, spread points, spread pips, and source.
- [ ] `fallback_sources` shall be represented as an explicit optional list in data retrieval requests.
- [ ] `fallback_sources` shall default to an empty list.
- [ ] Fallback shall never occur unless `fallback_sources` is supplied by the caller.
- [ ] Fallback metadata shall include requested source, actual source, fallback used, fallback reason, and attempted fallback chain.
- [ ] The module shall provide one internal broker/data gateway interface that routes one internal request contract to many external source APIs.
- [ ] The gateway shall use adapter capability declarations before execution.
- [ ] `fallback_sources` shall be optional and shall default to empty.
- [ ] Broker/data gateway errors shall preserve requested source, actual source where known, adapter readiness, capability declaration, and circuit breaker state.
- [ ] Source readiness shall be declared in a central source readiness manifest.
- [ ] Source readiness shall be included in source-specific response metadata.
- [ ] The gateway shall enforce source readiness before execution.
- [ ] The source registry shall provide internal adapter lookup and registration.
- [ ] Availability outputs shall include available ranges, gaps, completeness, record count, source readiness, and source metadata.
- [ ] Fallback shall validate source readiness, capability declarations, license policy, and workflow context before use.
- [ ] Historical data shall expose gaps, overlaps, completeness, quality status, source readiness, license metadata, and precision policy in metadata.
- [ ] The gateway shall enforce credential policy, source readiness, rate limits, retry policy, circuit breaker policy, license policy, source revision policy, normalization policy, quality policy, and precision policy consistently across adapters.
- [ ] `fallback_sources` shall be validated against source readiness, capability declarations, and license policy before use.
- [ ] Spread outputs shall include records or summaries, record count, symbol, source, start, end, quality report, source metadata, license metadata, and precision metadata.
- [ ] Source revision mismatch shall return or log `DATA_SOURCE_REVISION_DETECTED`.
- [ ] Passwords, access tokens, API keys, account secrets, broker secrets, and raw credential payloads shall never be logged or returned.
- [ ] Official tools shall remain thin orchestration functions that validate inputs, call internal services/adapters, and return standard responses.
- [ ] Naive timestamps shall exist only inside source adapters before normalization.
- [ ] Every source adapter shall implement a common internal source protocol.
- [ ] Every source adapter shall validate source-specific requirements.
- [ ] Every source adapter shall fetch or load raw source data.
- [ ] Every source adapter shall convert raw fields into normalized records.
- [ ] Every source adapter shall preserve source metadata.
- [ ] Every source adapter shall map source errors to deterministic internal errors.
- [ ] Source adapters shall expose no direct official AI tool functions.
- [ ] Source adapters shall support circuit breaker state.
- [ ] Broker adapters shall remain read-only in the data module.
- [ ] Broker adapters shall never place trades, close positions, modify account state, or change terminal settings.
- [ ] Every source adapter shall avoid logging secrets.
- [ ] Source adapters may be marked `production`, `staging`, `experimental`, or `not_available`, but unavailable adapters shall fail safely and deterministically.
- [ ] Adapter errors shall preserve safe source context and request ID.
- [ ] Broker adapters shall never place trades, close positions, modify account state, or change terminal settings.
- [ ] MT5 adapter shall remain read-only and shall not place orders or modify broker state.
- [ ] Initial source readiness shall be `staging` for `mt5` until live credential, broker, timeout, and data validation tests pass.
- [ ] MT5 source shall support secure credential resolution from environment/config.
- [ ] MT5 credential resolution shall remain inside the adapter/client layer.
- [ ] Initial source readiness shall be `staging` for `ctrader` until client-boundary, network, and normalization tests pass.
- [ ] cTrader source shall use the approved cTrader adapter/MCP boundary.
- [ ] cTrader source shall support symbol listing, bar loading, cTrader bar normalization, timeframe mapping, source metadata preservation, and deterministic network/client errors.
- [ ] Raw cTrader client construction shall remain internal.
- [ ] cTrader client construction shall remain internal.
- [ ] Public Dukascopy streaming subscription tools shall remain deferred until a later specification explicitly approves public streaming tools.
- [ ] Initial source readiness shall be `staging` for `dukascopy` until historical/live capability, rate-limit, and normalization tests pass.
- [ ] Dukascopy live or stream-oriented access shall be represented as an internal adapter capability where supported.
- [ ] Dukascopy source shall support instrument discovery, internal instrument metadata lookup, historical OHLCV or tick fetch where implemented, source interval mapping, live or stream-oriented fetch where supported, normalization, HTTP/network handling, retry/timeouts, and source metadata preservation.
- [ ] Dukascopy implementation shall be split into smaller client, instruments, normalization, source, and live modules if it becomes oversized.
- [ ] Dukascopy client internals shall remain internal.
- [ ] Initial source readiness shall be `staging` for `binance` symbol discovery only.
- [ ] Binance or equivalent exchange support shall be symbol-discovery oriented through `list_symbols(source="binance")`.
- [ ] Binance support shall not become a trading or execution adapter inside the data module.
- [ ] Data quality tests shall cover adversarial market conditions, including zero-volume bars, extreme spread widening such as `>1000` pips, NaN/Inf values from source APIs, and flash-crash price anomalies.
- [ ] The internal gateway shall route one internal request format to many source adapters.
- [ ] Adapter capability declarations shall be tested.
- [ ] Adapter readiness levels shall be tested.
- [ ] Source registry lookup and registration behavior shall be tested.
- [ ] Source registry non-export as an official AI tool shall be tested.
- [ ] Every source adapter shall test source-specific normalization.
- [ ] Every source adapter shall test source-specific deterministic error mapping.
- [ ] Every source adapter shall test missing optional dependency behavior.
- [ ] Every source adapter shall test mocked network or client failure behavior where applicable.
- [ ] Every source adapter shall test no secret leakage.
- [ ] Explicit fallback source behavior shall be tested.
- [ ] MT5 credential redaction shall be tested.
- [ ] cTrader client-boundary behavior shall be tested.
- [ ] Dukascopy historical/live capability representation shall be tested.
- [ ] Binance symbol-discovery-only behavior shall be tested.
- [ ] Production tests shall cover rate-limit tracking, HTTP 429 handling, and no-immediate-retry behavior.
- [ ] Network timeout, HTTP 429, retry, and circuit breaker behavior shall be tested with mocks.
- [ ] Every official tool shall test unsupported source where applicable.
- [ ] Every official tool shall test source failure.
- [ ] Production tests shall cover license restriction enforcement.

#### `app/services/data/storage.py`

Functions/classes:

- `save_record`
- `load_record`
- `validate_storage_path`

Requirements:

- [ ] Documentation shall include approved storage roots.
- [ ] Package path is `app/services/data/`.
- [ ] Local paths are validated against approved storage roots.
- [ ] The module shall not be marked production-ready until a production sign-off artifact is produced.
- [ ] Redistribution-restricted data shall not be exported outside approved internal paths.
- [ ] Storage writes shall include metadata manifests when `include_metadata=True`.
- [ ] Optional source metadata may include source version, source update timestamp, raw data hash, vendor response time, remaining rate-limit quota, terminal path, and adapter version.
- [ ] Local immutable datasets shall have no time-based expiry when their file hash and modified timestamp remain unchanged.
- [ ] Approved storage roots shall be configurable only through HaruQuant settings.
- [ ] Absolute paths outside approved roots shall be rejected.
- [ ] `save_market_data`
- [ ] `load_local_dataset`
- [ ] Source adapters shall implement the common internal source protocol in `app/services/data/sources/base.py` or a future explicitly versioned replacement path.
- [ ] Storage requests shall validate path safety and default to `overwrite=False`.
- [ ] Storage writes shall use temp artifact plus atomic final commit/rename semantics.
- [ ] Storage writes shall quarantine partial artifacts from failed writes.
- [ ] File writes shall use temp files plus atomic rename or equivalent safe commit semantics.
- [ ] Partial artifacts created during failed writes shall be quarantined.
- [ ] Production files shall contain module-level docstrings.
- [ ] Implementation files shall remain small and single-responsibility.
- [ ] The package path shall be `app/services/data/`.
- [ ] Storage requests shall include path, format, overwrite flag, create-parents flag, include-metadata flag, and request ID.
- [ ] Storage paths shall resolve under approved storage roots.
- [ ] Local file operations shall enforce approved storage roots and path validation.
- [ ] Absolute paths outside approved roots shall be rejected.
- [ ] Overwrite operations shall require explicit `overwrite=True`.
- [ ] Existing local file with `overwrite=False` shall return `FILE_ALREADY_EXISTS`.
- [ ] Unsafe path shall return `PATH_NOT_ALLOWED`.
- [ ] Missing local file shall return `FILE_NOT_FOUND`.
- [ ] Initial source readiness shall be `production` for `csv`.
- [ ] Naive local CSV/Parquet timestamps shall require source timezone detection or request-level `source_timezone` override.
- [ ] CSV source shall support loading OHLCV records.
- [ ] CSV source shall support loading tick records when columns allow.
- [ ] CSV source shall support saving normalized records through the storage layer.
- [ ] CSV source shall support configurable timestamp column, delimiter, column alias mapping, strict path safety, date filtering, and validation after load.
- [ ] `save_market_data` shall save validated normalized records to CSV or Parquet.
- [ ] `load_local_dataset` shall load CSV or Parquet datasets into normalized records.
- [ ] Initial source readiness shall be `production` for `parquet`.
- [ ] Parquet source shall support loading OHLCV and tick records.
- [ ] Parquet source shall support saving normalized records.
- [ ] Parquet source shall preserve schema metadata where possible.
- [ ] Parquet source shall support date filtering, safe path validation, and validation after load.
- [ ] Parquet shall be the preferred local storage format for larger datasets.
- [ ] Loading 100,000 local Parquet records should target under 2 seconds.
- [ ] The gateway shall route requests to adapters for CSV, Parquet, MT5, cTrader, Dukascopy, Binance symbol discovery, synthetic generation, real-time feed providers, and future approved providers.
- [ ] MT5 source shall support terminal path handling, connection lifecycle management, symbol listing, OHLCV bars, tick data where available, symbol metadata/details, timeframe mapping, UTC timestamp normalization, broker timezone metadata, and broker-unavailable errors.
- [ ] `workflow_context` shall be an explicit input wherever precision, validation strictness, storage, or downstream risk differs.
- [ ] Quarantine of partial artifacts shall be tested.
- [ ] Storage tests shall cover valid save and load.
- [ ] Storage tests shall cover overwrite blocked by default.
- [ ] Storage tests shall cover unsafe path rejection.
- [ ] Storage tests shall cover unsupported extension rejection.
- [ ] Storage tests shall cover metadata preservation.
- [ ] Every official tool shall test path safety where applicable.

#### `app/utils/errors.py`

Functions/classes:

- `Error`
- `ValidationError`
- `ServiceError`

Requirements:

- [ ] Documentation shall include an error-code reference with all deterministic error codes.
- [ ] `VALIDATION_FAILED` shall be added to deterministic error codes.
- [ ] Every official tool handles errors deterministically.
- [ ] `status` shall be `success` or `error`.
- [ ] `error` shall be null on success or contain deterministic code and details on failure.
- [ ] All standard system exceptions and error codes (including `VALIDATION_FAILED`, `AUTHENTICATION_FAILED`, `PERMISSION_DENIED`, `CIRCUIT_BREAKER_OPEN`, `UNKNOWN_ERROR`) shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom data exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.
- [ ] The deterministic error-code list shall include `VALIDATION_FAILED`.
- [ ] The deterministic error-code list shall include `CIRCUIT_BREAKER_OPEN`.
- [ ] The deterministic error-code list shall include `AUTHENTICATION_FAILED`.
- [ ] The deterministic error-code list shall include `PERMISSION_DENIED`.
- [ ] `UNKNOWN_ERROR` shall be reserved only for unexpected failures after deterministic error mapping has been exhausted.
- [ ] Official data tools shall use deterministic error codes.
- [ ] Any unsupported `workflow_context` shall return `INVALID_INPUT`.
- [ ] Invalid workflow context shall return `INVALID_INPUT`.
- [ ] Input validation failure shall return `VALIDATION_FAILED` or `INVALID_INPUT` according to context.
- [ ] Official tools shall not use `UNKNOWN_ERROR` for expected unsupported capabilities.
- [ ] Bad data shall not be silently normalized without visible warnings or errors.
- [ ] The deterministic error-code list shall include `STATE_RECOVERY_FAILED`.
- [ ] The deterministic error-code list shall include `CREDENTIALS_MISSING`.
- [ ] Errors and logs shall redact secret-like values.
- [ ] Every official tool shall test deterministic error code mapping.
- [ ] Usage examples shall show realistic workflows and handle both success and error responses.

#### `app/services/data/cache.py`

Functions/classes:

- `CacheKey`
- `read_cache`
- `write_cache`
- `invalidate_cache`

Requirements:

- [ ] Documentation shall include cache TTL and invalidation policy.
- [ ] Documentation shall state that schema version, normalization version, and raw data hash changes invalidate matching cache entries regardless of TTL.
- [ ] Approved storage roots shall be fixed to `data/raw/`, `data/processed/`, `data/cache/`, and `artifacts/data/` for Phase 1.
- [ ] Changing schema version, normalization version, or raw data hash shall invalidate matching cache entries regardless of TTL.
- [ ] Cache keys include schema version, normalization version, and raw data hash where available.
- [ ] Stale cache is not returned silently.
- [ ] The maximum request-level cache TTL override shall be 7 days unless a source declares a stricter maximum.
- [ ] Historical daily-or-higher data shall default to a cache TTL of 86,400 seconds.
- [ ] Intraday bar data shall default to a cache TTL of 3,600 seconds.
- [ ] Tick data shall default to a cache TTL of 900 seconds unless the source declares a stricter freshness policy.
- [ ] Cache entries shall automatically invalidate when `schema_version`, `normalization_version`, or `raw_data_hash` changes, regardless of TTL.
- [ ] Stale cache shall not be returned silently.
- [ ] Stale cache behavior shall be governed by the `stale_data_behavior` input parameter, defaulting to `refresh_and_return` for execution-bound workflows and `return_with_warning` for research workflows.
- [ ] The approved Phase 1 storage roots shall be `data/raw/`, `data/processed/`, `data/cache/`, and `artifacts/data/`.
- [ ] `clear_data_cache`
- [ ] Historical requests shall support source, symbol, data kind, timeframe where applicable, start, end, limit, cache policy, source timezone, workflow context, fallback sources, and request ID.
- [ ] Historical data shall include raw data hash in cache identity when available.
- [ ] Historical data shall never silently use stale cache entries.
- [ ] Live data shall not use persistent cache by default.
- [ ] A new `schema_version` shall read data written by the previous minor version or trigger mandatory cache invalidation and re-ingestion.
- [ ] The cache shall support key creation, reads, writes, stale detection, source revision detection, and safe clearing.
- [ ] Cache keys shall include source, data kind, symbol, timeframe, start, end, schema version, normalization version, request flags, source revision metadata, and raw data hash where available.
- [ ] Stale cache shall not be returned silently.
- [ ] Stale cache behavior shall be governed by `stale_data_behavior`, with `refresh_and_return` forcing a source refresh before return and `return_with_warning` returning stale data only with explicit warning metadata.
- [ ] Cache reads, writes, misses, stale decisions, invalidation, and clear operations shall propagate request ID in logs.
- [ ] Cache write failures shall not corrupt successful source fetches.
- [ ] If source fetch succeeds but cache write fails, the response shall return source data with a warning and log the cache failure.
- [ ] `clear_data_cache` shall default to dry-run.
- [ ] `clear_data_cache` shall validate namespace, source filter, symbol filter, dry-run option, and allowed cache root.
- [ ] Generated artifacts, local credentials, notebooks, temp files, `__pycache__`, and `.pyc` files shall not be committed.
- [ ] Data retrieval tools shall accept source, symbol, data kind, timeframe where applicable, date range, limit, cache controls, source timezone override, stale-data behavior, quality failure behavior, workflow context, fallback sources, and request ID.
- [ ] Cache TTL override shall be non-negative and within configured maximum TTL.
- [ ] Cache errors shall not corrupt successful source fetches.
- [ ] HTTP 429 or source throttling shall return or log `RATE_LIMIT_EXCEEDED`.
- [ ] Immediate retry after throttling shall be forbidden.
- [ ] Historical data providers that revise old data shall trigger cache invalidation or strict failure according to `DataVersionPolicy`.
- [ ] Missing cache entries shall be treated as cache misses that trigger source fetch or deterministic failure; stale-cache behavior shall not be applied to missing entries.
- [ ] Source revisions shall invalidate cache or fail according to `DataVersionPolicy`.
- [ ] Cache miss shall return or log `CACHE_MISS`.
- [ ] Cache stale shall return or log `CACHE_STALE`.
- [ ] Cache write failure shall return data with warning if source fetch succeeded.
- [ ] Data validation, normalization, quality scoring, timestamp handling, cache handling, source metadata, and persistence behavior shall be deterministic and documented.
- [ ] Every official tool shall log call start, validation failure, source failure, cache hit/miss/stale status, persistence failure, successful completion, execution time, and error code on failure.
- [ ] Schema migration and cache invalidation events shall be auditable.
- [ ] Crash recovery shall never bypass validation, path policy, license policy, cache policy, source readiness policy, precision policy, or gateway policy.
- [ ] Streaming and live data shall default to cache TTL `0` and shall not be persistently cached unless explicitly stored through a persistence workflow.
- [ ] Real-time reconnection shall avoid thundering-herd behavior after crashes, restarts, network partitions, and source throttling.
- [ ] Every official tool shall test cache hit, miss, stale, and invalidation behavior where applicable.
- [ ] Cache invalidation on schema version change shall be tested.
- [ ] Cache invalidation on normalization version change shall be tested.
- [ ] Production tests shall cover source revision detection and cache invalidation.

#### `app/services/data/models.py`

Functions/classes:

- `Request`
- `Result`
- `Config`
- `Metadata`

Requirements:

- [ ] Documentation shall include precision and numeric serialization policy by workflow context.
- [ ] `get_historical_volume` may be direct or derived if its response contract remains stable and tested.
- [ ] Downstream modules shall adapt to the new contracts rather than relying on aliases.
- [ ] Precision serialization shall be workflow-aware.
- [ ] Schema evolution shall enforce backward compatibility or explicit invalidation and re-ingestion.
- [ ] Every official tool returns the standard response schema.
- [ ] Every official tool has metadata and side-effect flags.
- [ ] Downstream contract alignment tests pass.
- [ ] `get_symbol_metadata`
- [ ] `get_data_availability`
- [ ] The data module shall be rebuilt as a clean, contract-driven, agent-safe, testable, maintainable domain under `app/services/data/`.
- [ ] `get_historical_volume` shall return volume-specific historical records or summaries.
- [ ] Converting 100,000 DataFrame rows to records should target under 3 seconds.
- [ ] Missing required asset-specific metadata shall return or emit `MISSING_ASSET_METADATA` when the asset class and workflow require those fields.
- [ ] Every official AI tool shall return the standard HaruQuantAI response schema.
- [ ] All market data crossing the official AI-tool boundary shall be JSON-serializable and contract-compliant.
- [ ] Large historical data shall be stored locally and referenced through metadata where direct response payloads would be unsafe.
- [ ] Every official tool shall return status, message, data, error, and metadata.
- [ ] Missing required asset metadata shall return `MISSING_ASSET_METADATA`.
- [ ] The deterministic error-code list shall include `MISSING_ASSET_METADATA`.
- [ ] Error responses shall include status, message, error code, details, request ID, and metadata.
- [ ] Schema drift shall return `DATA_SCHEMA_DRIFT`.
- [ ] The default direct-response limit for OHLCV bars shall be 5,000 records.
- [ ] The maximum direct-response limit for OHLCV bars shall be 50,000 records.
- [ ] The default direct-response limit for ticks shall be 10,000 records.
- [ ] The maximum direct-response limit for ticks shall be 250,000 records.
- [ ] The default direct-response limit for spread records shall be 10,000 records.
- [ ] The maximum direct-response limit for spread records shall be 250,000 records.
- [ ] Data availability tools shall not materialize more than 1,000,000 records solely for counts unless an operator explicitly enables a bounded audit mode.
- [ ] Historical tick retrieval shall require explicit date ranges or bounded limits.
- [ ] Until a historical calendar provider is approved, historical market-hour reconstruction shall return `UNSUPPORTED_OPERATION` and disclose `historical_hours_supported=false` in metadata.
- [ ] `VALIDATION_FAILED` shall be used for input, contract, or request validation failures.
- [ ] `get_market_data` shall fetch normalized historical OHLCV bar data.
- [ ] Normalization decisions, gap decisions, overlap decisions, and precision policy shall appear in metadata or the quality report.
- [ ] Validation of 10,000 OHLCV records should target under 500 ms.
- [ ] `get_tick_data` shall fetch normalized historical tick data.
- [ ] `get_spread_data` shall fetch or derive normalized historical spread data.
- [ ] Tick records shall validate that at least one of bid, ask, or last exists.
- [ ] Tick records shall validate `ask >= bid` when both bid and ask are present.
- [ ] Precision quantization shall run before records cross official boundaries when symbol metadata provides required precision.
- [ ] Numeric output shall default to `decimal_string` for `backtest`, `validation`, `risk`, and `execution_bound` workflows.
- [ ] Numeric output may use `float` only for `research` workflows and only when metadata discloses the precision policy.
- [ ] Execution-bound workflows shall fail closed on precision mismatch.
- [ ] Numeric serialization policy shall be disclosed in metadata.
- [ ] Precision policy shall be disclosed in metadata.
- [ ] Precision mismatches shall fail closed for risk and execution-bound workflows.
- [ ] Precision mismatch shall return `PRECISION_MISMATCH`.
- [ ] Execution-bound precision mismatch shall fail closed.
- [ ] Duplicate timestamps, out-of-order records, missing timestamps, OHLC inconsistencies, negative volume, negative spread, stale data, partial data, and tick ask-bid violations shall be detected by quality validation.
- [ ] Symbol metadata shall support asset-specific extensions for futures, options, bonds, and crypto where required by the asset class or workflow.
- [ ] The default `spread_policy` shall be `average`.
- [ ] Tick aggregation shall reject invalid or unsorted ticks unless repair is explicitly enabled.
- [ ] Labeling metadata shall describe the label method and parameters.
- [ ] Historical tick retrieval shall be tested.
- [ ] Historical data availability and gap detection shall be tested.
- [ ] Data quality tests shall cover valid OHLCV pass.
- [ ] Data quality tests shall cover negative spread.
- [ ] Data quality tests shall cover tick ask-bid violations.
- [ ] Historical OHLCV retrieval shall be tested.
- [ ] Historical spread retrieval or derivation shall be tested.
- [ ] Precision behavior shall be tested for research, backtest, validation, risk, and execution-bound workflows.
- [ ] Production tests shall cover asset-specific metadata validation.
- [ ] Every official tool shall test standard return schema.
- [ ] Every official tool shall test metadata correctness.
- [ ] Downstream contract alignment shall be tested for strategy, simulation, optimization, analytics, risk, portfolio, execution, and agentic workflows.
- [ ] Numeric serialization shall be tested for `decimal_string` and `float` policy.
- [ ] Production tests shall cover precision quantization.
- [ ] Production tests shall cover execution-bound precision mismatch failure behavior.
- [ ] Production tests shall cover downstream contract alignment.

#### `app/services/data/adapters/synthetic.py`

Functions/classes:

- `generate_synthetic_bars`
- `generate_synthetic_ticks`

Requirements:

- [ ] Source readiness starts conservative: local and synthetic sources may be production; external/broker sources are staging until mocked and live validation passes.
- [ ] GBM synthetic generation is enough for Phase 1.
- [ ] Synthetic generation is deterministic when seed is supplied.
- [ ] `mean_reverting`, `trend`, and `seasonal` synthetic processes shall be Phase 2 extensions.
- [ ] The maximum direct-response limit for synthetic bars shall be 100,000 records.
- [ ] The maximum direct-response limit for synthetic ticks shall be 250,000 records.
- [ ] Initial source readiness shall be `production` for `synthetic`.
- [ ] `generate_synthetic_ticks`
- [ ] `generate_synthetic_bars`
- [ ] Synthetic generation shall use dedicated official tools rather than a normal external adapter unless future design requires source-like behavior.
- [ ] Synthetic tick and bar generation shall be deterministic when a seed is supplied.
- [ ] `generate_synthetic_ticks` shall support symbol, start timestamp, number of ticks, start price, average spread, volatility, volume behavior, and seed.
- [ ] `generate_synthetic_bars` shall support symbol, timeframe, start timestamp, number of bars, start price, drift, volatility, spread behavior, volume behavior, method, and seed.
- [ ] `generate_synthetic_bars` shall support GBM in Phase 1.
- [ ] Generating 100,000 synthetic ticks should target under 3 seconds.

#### `app/services/data/transforms.py`

Functions/classes:

- `resample_ohlcv`
- `align_multitimeframe_data`
- `aggregate_ticks_to_bars`

Requirements:

- [ ] Pending: select the future `MarketCalendarProvider` implementation for historical holidays, daylight-saving, and broker-session reconstruction.
- [ ] OHLCV, tick, spread, metadata, sessions, availability, and volume outputs use normalized contracts.
- [ ] Timezone normalization uses UTC at the official boundary.
- [ ] Source timezone and broker timezone metadata are preserved.
- [ ] Multi-timeframe alignment prevents lookahead by default.
- [ ] `get_trading_sessions`
- [ ] Phase 1 may return current configured market hours only.
- [ ] Historical holiday, daylight-saving, and broker-session reconstruction shall be provided through a future `MarketCalendarProvider` abstraction.
- [ ] The future market-calendar implementation shall use IANA timezones and exchange/broker calendar datasets behind an internal provider interface.
- [ ] `get_market_hours` shall return timezone-aware market hours.
- [ ] Session start and end values shall be UTC ISO 8601 strings.
- [ ] Source timezone override shall be a valid IANA timezone.
- [ ] Source timezone and broker timezone shall be included when known.
- [ ] Source timezone and broker timezone shall be preserved in metadata when known.
- [ ] Original source timezone or broker timezone shall be preserved in metadata.
- [ ] Required source metadata shall include source, requested source, actual source, source readiness, source capability declaration, schema version, normalization version, timestamp timezone, request ID, and license metadata where applicable.
- [ ] OHLCV outputs shall include records, record count, symbol, timeframe, source, start, end, timestamp timezone, source timezone, schema version, normalization version, quality report, source metadata, license metadata, and precision metadata.
- [ ] Tick outputs shall include records, record count, symbol, source, start, end, timestamp timezone, source timezone, schema version, normalization version, quality report, source metadata, license metadata, and precision metadata.
- [ ] Adapters shall resolve DST ambiguities using explicit broker timezone mapping or the Python `fold` attribute before normalization to UTC.
- [ ] Source adapters shall declare capabilities for OHLCV, ticks, spread, symbol metadata, market hours, streaming, writes, credentials, and network requirements.
- [ ] `resample_ohlcv`
- [ ] `align_multitimeframe_data`
- [ ] `aggregate_ticks_to_bars`
- [ ] `resample_ohlcv` shall accept normalized OHLCV records.
- [ ] `resample_ohlcv` shall validate source timeframe and target timeframe.
- [ ] `resample_ohlcv` shall aggregate open as first open, high as max high, low as min low, close as last close, and volume as sum.
- [ ] `resample_ohlcv` shall aggregate spread according to explicit `spread_policy`.
- [ ] `align_multitimeframe_data` shall prevent lookahead leakage by default with `allow_lookahead=False` and `alignment_method="last_known_closed_bar"`.
- [ ] `aggregate_ticks_to_bars` shall convert normalized tick records into OHLCV bars.
- [ ] `label_market_data`
- [ ] `get_trading_sessions` shall return normalized trading session windows and labels.
- [ ] `label_market_data` shall generate deterministic historical labels.
- [ ] `label_market_data` shall support LEXLB-style labels or an equivalent current deterministic labeling method.
- [ ] `label_market_data` shall support configurable lookahead horizon and configurable threshold.
- [ ] `label_market_data` shall validate horizon and threshold inputs.
- [ ] Labeling shall prevent lookahead leakage beyond the declared horizon.
- [ ] `label_market_data` shall not claim predictive value.

#### `app/utils/validations.py`

Functions/classes:

- `validate_request`
- `validate_payload`

Requirements:

- [ ] Every official tool validates inputs.
- [ ] Data quality validation runs before returning market data.
- [ ] CI quality gates pass.
- [ ] Data content validation failure shall return `DATA_QUALITY_FAILED`.
- [ ] Direct official-tool responses shall use safe default limits to avoid large agent payloads.
- [ ] Official tool payload sizes shall be configurable and bounded.
- [ ] For responses approaching maximum limits, the module shall support generator/yield patterns or chunked iteration to prevent Out-Of-Memory conditions during serialization and agent payload construction.
- [ ] Limit shall be positive and within configured maximums.
- [ ] Any request exceeding configured limits shall return `LIMIT_EXCEEDED`.
- [ ] Excessive request limit shall return `LIMIT_EXCEEDED`.
- [ ] Rate limit shall return or log `RATE_LIMIT_EXCEEDED`.
- [ ] `DATA_QUALITY_FAILED` shall be used for data-content validation failures.
- [ ] Historical data shall not silently interpolate, forward-fill, or repair gaps for backtest, validation, risk, or execution-bound workflows.
- [ ] Recovery shall not duplicate committed chunks.
- [ ] Data quality validation shall run after normalization and before return to downstream workflows.
- [ ] Duplicate ingestion no-op behavior shall be tested.
- [ ] Every official tool shall test quality failure.
- [ ] Data quality tests shall cover duplicate timestamps as warning or failure according to configured policy.
- [ ] Data quality tests shall cover out-of-order timestamps.
- [ ] Data quality tests shall cover missing timestamps and inferred gaps.
- [ ] Data quality tests shall cover OHLC inconsistency.
- [ ] Data quality tests shall cover negative volume.
- [ ] Data quality tests shall cover stale data.
- [ ] Data quality tests shall cover partial data.
- [ ] Production tests shall cover timestamp gap and overlap defaults.


### Hardening Amendments

#### Persistence, lineage, calendars, and provider contracts

Requirements:

- [ ] Adopt the Phase 1.5 canonical market data contracts instead of defining duplicate Bar, Tick, Symbol, Timeframe, or DataSlice models.
- [ ] Define database migration ownership, migration naming, forward migration, rollback expectation, and schema-version recording for all persisted data stores.
- [ ] Implement data lineage metadata for provider, provider request ID, retrieved timestamp, normalized timestamp, raw source hash, transformation hash, and quality-check result reference.
- [ ] Define raw provider payload retention rules separately from canonical normalized market-data retention rules.
- [ ] Define symbol master ownership for canonical symbols, broker symbols, precision, lot size, tick size, asset class, sessions, and provider availability.
- [ ] Define market/session calendar ownership and how Data distinguishes expected session gaps from unexpected missing data.
- [ ] Define backup and restore policy for historical data, cache data, normalized datasets, data-quality reports, and provider metadata.
- [ ] Create golden dataset fixtures used by Data, Indicators, Strategies, Simulation, Analytics, Optimization, and Research regression tests.
- [ ] Implement a canonical `MarketDataProvider` interface boundary for MT5, cTrader, Binance, file, database, and simulator-backed data sources.
- [ ] Ensure provider adapters return canonical contracts and never leak raw provider SDK objects across the service boundary.

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

- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/02_data.py

```

Usage examples must show:

- `example_01_metadata_and_discovery`: Demonstrate symbol discovery, source capabilities, metadata lookup, and data availability checks.
- `example_02_historical_data_retrieval`: Demonstrate OHLCV retrieval across approved sources with standard failure handling for unavailable providers.
- `example_03_local_file_sources`: Demonstrate CSV and Parquet loading through safe paths and normalized contracts.
- `example_04_synthetic_generation`: Demonstrate reproducible synthetic bars and ticks with seeds and source manifests.
- `example_05_timeframes_sessions_and_market_hours`: Demonstrate timeframe parsing, market-hour lookup, trading sessions, and UTC normalization.
- `example_06_transformations_and_alignment`: Demonstrate resampling, tick aggregation, labeling, and lookahead-free multi-timeframe alignment.
- `example_07_cache_and_storage`: Demonstrate cache hits/misses, TTL behavior, manifests, and scoped cache clearing.
- `example_08_scheduler_jobs`: Demonstrate update-job creation, status inspection, start/stop behavior, checkpointing, and recovery surfaces.
- `example_09_feed_status_and_readiness`: Demonstrate feed heartbeat, gap/staleness status, readiness metadata, and circuit-breaker reporting.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 701 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Phase 2 has green CI, at least 80 percent affected-file/package coverage, passing usage examples, synchronized docs, and no unresolved safety blockers before Phase 3 work begins.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text

feat(data-foundation): implement market data gateway and client connections



- Implement MT5, cTrader, Dukascopy, Yahoo Finance, and Binance connection clients

- Build a resilient market data gateway in `app/services/data/gateway.py`

- Setup SQLite persistence cache for bars and ticks data in `data/persistence`

- Add support for raw CSV/Parquet file ingestion and directory normalization

- Expose 24 official market data retrieval and ingestion AI tools

```
