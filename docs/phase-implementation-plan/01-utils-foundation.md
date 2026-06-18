## Phase 1 Utils Foundation

### Goal

Implement the Utils Foundation requirements under `app/utils/` while preserving the phase module boundaries and governance rules.

Task inventory: 1,163 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

Required files:

```text

None

```

Required functionality:

- JSON structured logging and console log configuration.
- Standard tool response envelope construction.
- Domain exception types and error registration mapping.
- Timestamp UTC normalization and ISO string formatting.
- Monotonic clock duration timing.
- Collision-resistant trace ID generation and prefix checks.
- Safe traversal directory normalization and creation.
- Thread-safe Event Bus subscription and publishing.
- Metrics registry and Prometheus text format output.
- Secret payload redaction and settings loading.

### Files to Create

```text

app/__init__.py

app/utils/__init__.py

app/utils/logger.py

app/utils/standard.py

app/utils/errors.py

app/utils/identity.py

app/utils/normalization.py

app/utils/paths.py

app/utils/dataframe_tools.py

app/utils/data_quality.py

app/utils/validations.py

app/utils/security.py

app/utils/settings.py

app/utils/auth.py

app/utils/event_bus.py

app/utils/error_routing.py

app/utils/notifications.py

app/utils/observability.py

docs/planning/DOMAIN.md

app/utils/

```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [ ] Implement `app/__init__.py` first to establish a clean side-effect-free package.
- [ ] `app/__init__.py` exists and is side-effect free.

#### `app/utils/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [ ] The implementation is expected to be fresh and clean, with no backward-compatibility shims.
- [ ] `app/utils/__init__.py` must act as the public registry for the utility domain.
- [ ] Only intentionally imported names listed in `__all__` may be public.
- [ ] Support helpers may return native Python values when they are not agent-callable tools.
- [ ] Internal helpers must remain private unless explicitly intended for public import.
- [ ] No accidental public exports may exist.
- [ ] No compatibility shims, aliases, fallback import modules, or duplicate wrapper modules may exist.
- [ ] New public exports must be justified by real cross-domain reuse.
- [ ] Public exports may not be renamed or removed after v8 acceptance without a new versioned specification and registry review.
- [ ] Implement `app/utils/__init__.py` only after modules exist and public names are finalized.
- [ ] `app/utils/__init__.py` exposes only approved public names.
- [ ] `app/utils/__init__.py` must not eagerly import pandas, cryptography, dotenv, broker SDKs, network clients, notification clients, Prometheus exporters, or other heavy optional dependencies unless absolutely necessary.
- [ ] Documentation must maintain compatibility review notes for future public API changes.
- [ ] Internal helpers are not accidentally exported.
- [ ] No compatibility shims, aliases, fallback import modules, or duplicate wrapper modules exist.

#### `app/utils/logger.py`

Functions/classes:

- `get_logger()`
- `configure_logging()`

Requirements:

- [ ] The logger must be exported as a support object and must not be treated as an official AI tool.
- [ ] Official AI tools must use structured logging.
- [ ] The module must expose a project-wide `logger`.
- [ ] The module must expose `get_logger(name: str | None = None)`.
- [ ] The module must expose `configure_logging(level: str | int = "INFO")`.
- [ ] Logging must use Python `logging`.
- [ ] Logging must use structured JSON-compatible output for production runtime events.
- [ ] Production logging must use a JSON-compatible structured formatter.
- [ ] Local development console logging must support colorized human-readable output.
- [ ] Human-readable console log lines must use the format `datetime | level | module.submodule.filename:function:line | message`.
- [ ] Human-readable console timestamps must use the format `YYYY-MM-DD HH:MM:SS`.
- [ ] Logging must include `timestamp`, `level`, `logger_name`, `message`, `event_name`, `module`, `function`, `request_id`, `workflow_id`, `correlation_id`, and `error_code` where available.
- [ ] Human-readable console logging must include source line numbers where available.
- [ ] Logging must support child loggers per module while preserving a stable root logger name.
- [ ] Logging configuration must avoid duplicate handlers.
- [ ] Logging configuration must happen only through an explicit configuration function.
- [ ] Importing logger utilities must not force application-level logging configuration.
- [ ] File logging must be opt-in and configured explicitly through runtime settings or `configure_logging`.
- [ ] File logging must write only to configured log directories that are normalized through safe path handling.
- [ ] File logging must use rotating log files when enabled.
- [ ] Log rotation must support configurable maximum file size and maximum retained file count.
- [ ] Log retention must support configurable deletion of old rotated log files.
- [ ] Log retention deletion must be bounded to configured log directories and must not delete arbitrary files.
- [ ] Log file writes, rotation, and retention deletion must degrade safely if the filesystem or logging sink fails.
- [ ] Logging must avoid writing secrets.
- [ ] Log-level configuration must be controlled by runtime settings.
- [ ] Production files must log function/tool calls, validation failures, successful completions, recoverable warnings, and execution failures where applicable.
- [ ] Official AI tool logs must distinguish start, completion, validation failure, recoverable warning, and execution failure lifecycle events.
- [ ] Official AI tool logs must include request and workflow trace identifiers where available.
- [ ] Event Bus logs must include publish, subscribe, delivery failure, retry, dead-letter, queue-full, and dropped-event events.
- [ ] Notification logs must include routing decisions and delivery outcomes without exposing sensitive message bodies.
- [ ] Auth logs must include sanitized auth validation and authorization decisions.
- [ ] Observability logs must include metrics/export/health-check failures where detectable.
- [ ] Production files must never log passwords, API keys, broker credentials, encryption keys, tokens, raw private payloads, full approval packets, notification provider credentials, authorization headers, or Telegram bot tokens.
- [ ] Implement `app/utils/logger.py` before modules that need production logging.
- [ ] Important events and recoverable failures must use structured logging.
- [ ] Immutable constants and logger objects are allowed.
- [ ] Logging must be thread-safe under concurrent tool execution.
- [ ] Logging overhead must be minimal for normal tool execution.
- [ ] Logging must degrade safely if a logging sink fails.
- [ ] Documentation must describe required log fields and optional trace fields.
- [ ] Local development logging supports colorized human-readable console output in the approved format.
- [ ] Logging output must be deterministic enough for unit testing where log fields are asserted.
- [ ] Logger tests must verify colorized console output can be enabled and disabled deterministically.

#### `app/utils/standard.py`

Functions/classes:

- `StandardResponse`
- `ToolMetadata`
- `ToolError`
- `build_success_response`
- `build_error_response`
- `validate_standard_response`
- `get_execution_ms(start_time)`

Requirements:

- [ ] The utilities module must not own trading strategy logic.
- [ ] The utilities module must not own broker execution logic.
- [ ] The utilities module must not own risk-governor decisions.
- [ ] The utilities module must not own portfolio allocation decisions.
- [ ] The utilities module must not own application orchestration.
- [ ] The utilities module must not become a dumping ground for unrelated helpers.
- [ ] The utilities module must not export every internal helper as a public agent tool.
- [ ] The utilities module must not hide external dependency behavior behind unclear convenience functions.
- [ ] The utilities module must not perform live trading or live account mutation.
- [ ] The utilities module must not make trading, risk, allocation, execution, or strategy acceptance decisions.
- [ ] Utilities must not approve or reject trades.
- [ ] Utilities must not recommend allocations.
- [ ] Utilities must not decide strategy promotion.
- [ ] Utilities must not approve risk changes.
- [ ] Utilities must not place, close, modify, or cancel orders.
- [ ] Utilities must not activate live systems.
- [ ] Utilities must not override kill switches.
- [ ] Modules requiring financial decisions must call the appropriate risk, portfolio, execution, strategy, or governance domain.
- [ ] This is a domain-level requirements document for `docs/planning/DOMAIN.md`, not a sprint-specific requirements document.
- [ ] Support helpers remain native unless explicitly classified as official AI tools.
- [ ] Conditional AI tools remain support helpers unless direct agent use is approved.
- [ ] `app.services.data` will own repair, resampling, enrichment, persistence, and cleaning workflows for market data.
- [ ] Optional dependencies may or may not be installed; importability must remain intact either way.
- [ ] No UI, broker runtime, database repository, or LLM framework dependency is required inside `app.utils`.
- [ ] Public names must be classified as either official AI tools or support objects/helpers.
- [ ] Official AI tools must return the standard HaruQuant tool envelope.
- [ ] Official AI tools must include tool metadata.
- [ ] Official AI tools must include risk and side-effect flags.
- [ ] Official AI tools must validate inputs.
- [ ] Official AI tools must not fail silently.
- [ ] Agents may call only approved official AI tools through approved tool attachment.
- [ ] Every official AI tool must return the top-level keys `status`, `message`, `data`, `error`, and `metadata`.
- [ ] `status` must be either `success` or `error`.
- [ ] `message` must be a string.
- [ ] `error` must be either `None` or a mapping with `code` and `details`.
- [ ] Standard response validation must reject missing top-level keys.
- [ ] Standard response validation must reject missing metadata keys.
- [ ] Standard response validation must reject malformed errors.
- [ ] `get_execution_ms(start_time)` must calculate execution duration consistently for official tools.
- [ ] `get_execution_ms(start_time)` must return milliseconds rounded to three decimals.
- [ ] Official tools must not return unstructured `None`.
- [ ] Official AI tools must return standard HaruQuant tool envelopes.
- [ ] Official success responses must include `status="success"`, message, data, `error=None`, and metadata.
- [ ] Data-quality issues must include code, severity, message, column, row count, and samples.
- [ ] Canonical JSON serialization must return deterministic JSON strings.
- [ ] Error helpers must return deterministic names and fallback messages.
- [ ] Official AI tools must return standard error envelopes for expected validation failures.
- [ ] Circuit-open failures must return `CIRCUIT_OPEN` or provider-specific deterministic details.
- [ ] Error events must include sanitized details only.
- [ ] Every public function must document return value.
- [ ] Documentation must include an operational runbook for critical utility-layer failures.
- [ ] Implement `app/utils/standard.py` before official AI tools.
- [ ] Implement usage examples for official AI tools and production primitives.
- [ ] Run CI quality gates before accepting the implementation.
- [ ] The target folder structure exists.
- [ ] Public registry documentation classifies every official AI tool and support helper.
- [ ] Official tools return standard envelopes.
- [ ] Official tools include metadata constants.
- [ ] Official tools include side-effect flags.
- [ ] Official tools include `execution_ms`.
- [ ] Every Python file must have a file-level docstring.
- [ ] Every public function and class must have a useful docstring.
- [ ] All public functions and methods must be typed.
- [ ] Inputs must be validated where appropriate.
- [ ] Output shapes must be explicit where applicable.
- [ ] Error behavior must be deterministic.
- [ ] Production logic must not use `print()`.
- [ ] Utility functions must be safe for concurrent use unless explicitly documented otherwise.
- [ ] Mutable module-level state must be avoided.
- [ ] Caller-owned inputs must not be mutated unless documented in the function name and docstring.
- [ ] Concurrency guarantees and limitations must be documented per component.
- [ ] Optional dependencies must not break importability.
- [ ] Missing optional dependencies must fail only when the relevant feature is used.
- [ ] Missing optional dependency failures must be explicit.
- [ ] Optional dependency error messages must identify the missing dependency and required feature.
- [ ] Official AI tools must not raise expected validation errors to callers.
- [ ] Domain-specific errors must be mappable through `Error` inheritance or a compatible `code` attribute.
- [ ] Error helpers must not raise for unknown codes unless explicitly requested.
- [ ] Error messages must be human-readable and actionable.
- [ ] Event validation failures must map to `INVALID_EVENT`.
- [ ] Every Python file must start with a file-level docstring.
- [ ] File-level docstrings must state purpose.
- [ ] File-level docstrings must state whether the file contains official AI tools or support helpers.
- [ ] File-level docstrings must list exported public functions/classes.
- [ ] File-level docstrings must describe side effects, if any.
- [ ] Every public function must document what it does.
- [ ] Every public function must document when to use it.
- [ ] Every public function must document arguments.
- [ ] Every public function must document side effects, if any.
- [ ] Official AI tool docstrings must be agent-facing.
- [ ] Official AI tool docstrings must explain when an agent should use the tool.
- [ ] Official AI tool docstrings must explain what the tool does not do.
- [ ] Usage examples must demonstrate success and error handling.
- [ ] Usage examples must use realistic inputs.
- [ ] Documentation must describe safe metric-label rules and examples of rejected labels.
- [ ] Documentation must describe which features are support helpers and which are official AI tools.
- [ ] Documentation must describe which adapters are optional and lazy-loaded.
- [ ] Every Python file has a file-level docstring.
- [ ] Every public function/class has a useful docstring.
- [ ] Public functions and methods are typed.
- [ ] Inputs are validated where appropriate.
- [ ] Errors are explicit and deterministic.
- [ ] No production `print()` calls exist.
- [ ] Data repair and cleaning workflows are explicitly excluded from `app.utils` and reserved for `app.services.data`.
- [ ] Future domain-specific errors inherit from `Error` or expose a compatible `code` attribute.
- [ ] Standard response builders can map `Error` subclasses generically without hardcoding every future domain error.
- [ ] Usage examples exist for official AI tools.
- [ ] Usage examples use realistic inputs.
- [ ] Usage examples show success and error handling.
- [ ] Full-project quality gate passes.
- [ ] No unresolved open questions remain for the baseline production-ready utils module.
- [ ] The implementation must be compatible with Ruff format, Ruff check, mypy strict, pytest, and coverage.
- [ ] Shared caches are allowed only when explicitly specified, bounded, and tested.
- [ ] Time-dependent helpers must support deterministic testing where practical.
- [ ] ID-dependent and randomness-dependent helpers must support deterministic testing where practical.
- [ ] The utilities module must not implement UI, database repositories, or backtest engines.
- [ ] Negative prices must be reported.
- [ ] Zero prices must be reported.
- [ ] OHLC values outside high/low range must be reported.
- [ ] NaN and infinity values must be detected.
- [ ] Symbol verification must be marked `not_available` when no symbol column exists.
- [ ] Issue lists and issue samples must truncate when limits are reached.
- [ ] Repeated identical alerts must be deduplicated or throttled.
- [ ] High-cardinality metric labels must be rejected or normalized.
- [ ] Open circuit state must fail fast.
- [ ] Unit tests must exist for every utility module.
- [ ] Usage examples must exist for official AI tools.
- [ ] Minimum line coverage must be at least 80% for `app.utils`.
- [ ] Tests must cover edge cases.
- [ ] Official AI tool tests must verify metadata correctness.
- [ ] Official AI tool tests must verify `execution_ms` existence.
- [ ] Data-quality tests must cover at least 15 distinct data-quality cases.
- [ ] CI must pass Ruff format, Ruff check, mypy strict, pytest, and the coverage gate.
- [ ] Implement unit tests for every module.
- [ ] Unit tests exist for every module.
- [ ] Official tools have metadata tests.
- [ ] Edge case tests exist.
- [ ] Coverage is at least 80%.
- [ ] Ruff format passes.
- [ ] Ruff import sorting passes through Ruff check/format.
- [ ] Ruff check passes.
- [ ] mypy passes.
- [ ] pytest passes.
- [ ] Coverage gate passes.

#### `app/utils/errors.py`

Functions/classes:

- `Error`
- `ValidationError`
- `ConfigurationError`
- `SecurityError`
- `DataError`
- `ExternalServiceError`
- `error_name(code)`
- `message_for(code, default)`
- `message_for()`
- `UNKNOWN_ERROR`
- `TOOL_EXECUTION_FAILED`

Requirements:

- [ ] Official AI tools must use deterministic error codes.
- [ ] Standard response validation should validate error codes against the approved error-code set where practical.
- [ ] The module must define `Error`.
- [ ] The module must define `ValidationError`.
- [ ] The module must define `ConfigurationError`.
- [ ] The module must define `SecurityError`.
- [ ] The module must define `DataError`.
- [ ] The module must define `ExternalServiceError`.
- [ ] Every shared exception must carry a deterministic `code` attribute.
- [ ] Error messages must be human-readable.
- [ ] `error_name(code)` must return deterministic names.
- [ ] `message_for(code, default)` must return useful fallback messages.
- [ ] Unknown codes must resolve safely to `UNKNOWN_ERROR` or a provided default.
- [ ] Future domain-specific errors must inherit from `Error` or expose a compatible `code: str` attribute.
- [ ] Standard response builders must map `Error` subclasses generically without requiring every future domain error to be hardcoded.
- [ ] Unknown non-HaruQuant exceptions must map safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED` at controlled tool boundaries.
- [ ] Official error responses must include `status="error"`, message, `data=None`, error code/details, and metadata.
- [ ] Support helpers may return native Python values or raise typed exceptions.
- [ ] Unexpected execution failures must return `TOOL_EXECUTION_FAILED` or another safe deterministic error code.
- [ ] Implement `app/utils/errors.py` before deterministic failure behavior is needed.
- [ ] Support helpers return clear native values or raise typed exceptions.
- [ ] Support helpers may raise typed HaruQuant exceptions for programmer or validation errors.
- [ ] Expected validation failures should use deterministic codes such as `INVALID_INPUT` or `VALIDATION_FAILED`.
- [ ] Raw exception objects must never be returned in `data`.
- [ ] Raw exception objects must never be returned in `error`.
- [ ] Unknown non-HaruQuant exceptions must map safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED`.
- [ ] `INVALID_AUTH_CONTEXT`
- [ ] `AUTHORIZATION_FAILED`
- [ ] `INVALID_EVENT`
- [ ] `EVENT_PUBLISH_FAILED`
- [ ] `EVENT_HANDLER_FAILED`
- [ ] `EVENT_DEAD_LETTER_FAILED`
- [ ] `QUEUE_FULL`
- [ ] `BACKPRESSURE_EXCEEDED`
- [ ] `NOTIFICATION_FAILED`
- [ ] `NOTIFICATION_SUPPRESSED`
- [ ] `NOTIFICATION_THROTTLED`
- [ ] `OBSERVABILITY_ERROR`
- [ ] `METRICS_EXPORT_FAILED`
- [ ] `CLOCK_DRIFT_DETECTED`
- [ ] `CIRCUIT_OPEN`
- [ ] `SECRET_VERSION_CONFLICT`
- [ ] Every public function must document raised exceptions or structured error behavior.
- [ ] Official AI tool docstrings must explain what error codes may be returned.
- [ ] Official tools use deterministic error codes.
- [ ] Missing mandatory OHLC columns must return structured `INVALID_INPUT`.
- [ ] Unknown error codes must resolve safely.
- [ ] Unknown non-HaruQuant exceptions must map safely at controlled tool boundaries.
- [ ] Official AI tool tests must verify deterministic error codes.
- [ ] Error tests must verify exception attributes, known codes, unknown codes, and fallback messages.

#### `app/utils/identity.py`

Functions/classes:

- `generate_id`
- `generate_prefixed_id`
- `generate_request_id`
- `generate_workflow_id`
- `generate_correlation_id`
- `generate_event_id`
- `validate_request_id`
- `validate_workflow_id`
- `ensure_version`
- `ensure_version(None)`
- `ensure_version()`

Requirements:

- [ ] Official AI tools must include `request_id: str | None = None`.
- [ ] `metadata` must include `tool_name`, `tool_version`, `tool_category`, `tool_risk_level`, `request_id`, `execution_ms`, `read_only`, `writes_file`, `modifies_database`, `places_trade`, and `requires_network`.
- [ ] Standard response validation must reject invalid statuses.
- [ ] The module must provide `generate_id`.
- [ ] The module must provide `generate_prefixed_id`.
- [ ] The module must provide `generate_request_id`.
- [ ] The module must provide `generate_workflow_id`.
- [ ] The module must provide `generate_correlation_id` or equivalent correlation ID support.
- [ ] The module must provide `generate_event_id` or equivalent event ID support.
- [ ] The module must provide `validate_request_id`.
- [ ] The module must provide `validate_workflow_id`.
- [ ] The module must provide `ensure_version`.
- [ ] IDs must be string-safe.
- [ ] IDs must be safe for logs, filenames where practical, audit records, tool metadata, events, notifications, and metrics after cardinality controls.
- [ ] IDs must not contain secrets or raw user-provided text.
- [ ] Prefix validation must reject empty or unsafe prefixes.
- [ ] Generated IDs must be collision-resistant.
- [ ] Generated IDs must use UUID4, ULID-like generation, or an equivalently collision-resistant approach unless deterministic IDs are explicitly required.
- [ ] Request IDs and workflow IDs must be suitable for logs, audit records, tool responses, and agent handoffs.
- [ ] ID validation must be deterministic and must not perform external lookups.
- [ ] `ensure_version(None)` must return the configured default.
- [ ] Official AI tools must accept optional `request_id`.
- [ ] Identity helpers must accept prefixes and version strings.
- [ ] Implement `app/utils/identity.py` before request/workflow/event trace helpers are needed.
- [ ] Official tools accept `request_id`.
- [ ] The implementation must avoid avoidable circular imports.
- [ ] Large data-quality validations must avoid unnecessary deep copies.
- [ ] Usage examples must use `request_id` where applicable.
- [ ] Usage examples use `request_id` where applicable.
- [ ] Empty or unsafe ID prefixes must fail validation.
- [ ] `ensure_version(None)` must return the default.
- [ ] Invalid datetime inputs must fail clearly.
- [ ] Invalid high-low relationships must be reported.
- [ ] Tests must cover invalid inputs.
- [ ] Official AI tool tests must verify request ID propagation.
- [ ] Identity tests must verify ID uniqueness, prefix validation, and version defaulting.
- [ ] Invalid input tests exist.

#### `app/utils/normalization.py`

Functions/classes:

- `DEFAULT_TIMEZONE`
- `parse_datetime`
- `normalize_timestamp`
- `format_timestamp`
- `is_stale`
- `get_execution_ms(start_time)`

Requirements:

- [ ] Official AI tools must measure execution timing.
- [ ] `get_execution_ms(start_time)` must use a monotonic clock source such as `time.perf_counter()`.
- [ ] The module must define `DEFAULT_TIMEZONE = "UTC"`.
- [ ] The module must provide datetime parsing.
- [ ] The module must provide timestamp normalization.
- [ ] The module must provide UTC conversion.
- [ ] The module must provide naive UTC conversion.
- [ ] The module must provide UTC timestamp formatting with trailing `Z`.
- [ ] The module must provide timezone normalization for pandas-like series or timestamp columns.
- [ ] The module must provide stale-data checks.
- [ ] Timezone behavior must be explicit.
- [ ] Naive datetimes must be handled deterministically using an explicit assumed timezone.
- [ ] ISO strings must parse consistently.
- [ ] Time-dependent helpers must support injected `now` values or injected clock objects where practical.
- [ ] Invalid datetimes must fail clearly.
- [ ] Helpers must not use the local machine timezone implicitly.
- [ ] Wall-clock timestamps must be UTC-aware.
- [ ] Execution timing must use monotonic timers.
- [ ] The system must distinguish wall-clock timestamps from monotonic durations.
- [ ] Distributed workflow timestamp validation must surface clock-drift risk where relevant.
- [ ] Event envelopes must include event creation time and event processing time where applicable.
- [ ] Notification diagnostics must include created, routed, sent, and failed timestamps where applicable.
- [ ] Health checks should include clock-drift status where supported by runtime environment.
- [ ] Timestamp helpers must accept datetime-like values and explicit timezone assumptions.
- [ ] Timestamp formatting must return UTC ISO strings ending in `Z`.
- [ ] Implement `app/utils/normalization.py` before data quality, settings, freshness checks, and event timestamp validation.
- [ ] Importing `app.utils` must be lightweight.
- [ ] Heavy dependencies must be imported inside the specific submodule or function that needs them.
- [ ] Importing any `app.utils` module must not open network connections.
- [ ] Importing any `app.utils` module must not initialize broker clients.
- [ ] Importing any `app.utils` module must not run validation jobs.
- [ ] Documentation must describe UTC-first time policy.
- [ ] Documentation must describe monotonic execution timing policy.
- [ ] Importing `app.utils` must be safe in tests, CLI scripts, FastAPI startup, and agent runtime initialization.
- [ ] Naive datetimes must be normalized using the explicit assumed timezone.
- [ ] Stale checks must be deterministic when `now` is injected.
- [ ] Unparseable datetimes must be reported.
- [ ] Non-monotonic timestamps must be reported.
- [ ] Duplicate timestamps must be reported.
- [ ] Stale data must fail deterministically.
- [ ] Normalization tests must verify ISO parsing, naive timezone assumptions, UTC conversion, and stale checks.

#### `app/utils/paths.py`

Functions/classes:

- `normalize_path`
- `ensure_dir`
- `ensure_parent_dir`
- `safe_join`
- `validate_path_within_root`

Requirements:

- [ ] The module must provide `normalize_path`.
- [ ] The module must provide `ensure_dir`.
- [ ] The module must provide `ensure_parent_dir`.
- [ ] Path inputs must be validated.
- [ ] Directory creation helpers must be explicit side-effect helpers.
- [ ] `normalize_path` must have no side effects.
- [ ] `ensure_dir` must create a directory when missing.
- [ ] `ensure_parent_dir` must create a parent directory when missing.
- [ ] Path traversal outside `base_dir` must be rejected when a base directory is supplied.
- [ ] Path helpers must return `Path` objects.
- [ ] File and directory permissions must use platform-safe defaults.
- [ ] Path helpers must accept string or `Path` values and optional `base_dir`.
- [ ] Path helpers must return `Path` objects.
- [ ] Implement `app/utils/paths.py` before settings and artifact helpers.
- [ ] Importing any `app.utils` module must not create files or directories.
- [ ] Empty paths must fail validation.
- [ ] Unsafe path traversal outside `base_dir` must be rejected.
- [ ] Tests must cover success paths.
- [ ] Tests must cover failure paths.
- [ ] Logger tests must verify human-readable console formatting includes datetime, level, module path, function name, line number, and message.
- [ ] Path tests must verify safe normalization, unsafe traversal, directory creation, and parent creation.
- [ ] A concurrency stress test suite must exist outside the fast unit-test path.

#### `app/utils/dataframe_tools.py`

Functions/classes:

- `align_dataframe_time_index`
- `bars_to_records`
- `chunk_sequence`
- `generate_parameter_combinations`
- `compare_dataframes`

Requirements:

- [ ] The module must provide datetime alignment for dataframes.
- [ ] The module must provide bar-to-record conversion.
- [ ] The module must provide chunking for sequences.
- [ ] The module must provide parameter-combination helpers.
- [ ] The module must provide dataframe comparison helpers.
- [ ] The module must provide OHLC and OHLCV comparison helpers.
- [ ] The module must provide dataframe-record serialization.
- [ ] Dataframe helpers may return native Python objects.
- [ ] Dataframe columns must be validated where required.
- [ ] Dataframe helpers must not mutate caller-owned dataframes unless explicitly documented.
- [ ] Dataframe helpers must document copy, view, or transformed-data behavior.
- [ ] Serialization must handle timestamps safely.
- [ ] `serialize_dataframe_records` must emit UTC ISO timestamp strings ending in `Z`.
- [ ] `compare_dataframes` must align by comparable indexes or fail with a clear validation error when deterministic alignment is impossible.
- [ ] `chunked` must reject `size <= 0` with a clear validation error.
- [ ] Comparisons must support tolerance.
- [ ] Empty dataframes must be handled deterministically.
- [ ] Importing `app.utils` must not eagerly import pandas.
- [ ] Missing pandas must fail only when a dataframe helper is called.
- [ ] Dataframe serialization must return JSON-safe records where practical.
- [ ] Implement `app/utils/dataframe_tools.py` after normalization and errors.
- [ ] Dataframe helpers must use lazy pandas imports or `TYPE_CHECKING` guards.
- [ ] Importing any `app.utils` module must not execute expensive dataframe operations.
- [ ] Dataframe helpers must avoid repeated full-dataframe scans where possible.
- [ ] Dataframe helpers use lazy pandas imports or `TYPE_CHECKING` guards.
- [ ] Missing pandas must fail only when dataframe helpers are called.
- [ ] Missing required dataframe columns must fail clearly.
- [ ] Empty dataframes must be handled deterministically.
- [ ] Dataframe index mismatch must fail clearly when deterministic alignment is impossible.
- [ ] `chunked(size <= 0)` must fail clearly.
- [ ] Dataframe tests must verify alignment, serialization, UTC timestamp output, comparison, index mismatch behavior, missing columns, chunk-size validation, and no input mutation.

#### `app/utils/data_quality.py`

Functions/classes:

- `validate_ohlcv_quality`

Requirements:

- [ ] Data-quality market-calendar gap handling depends on session rules being supplied by a caller or future domain module.
- [ ] The default OHLCV scoring model applies unless a later module-specific specification replaces it.
- [ ] `validate_ohlcv_quality` must be implemented as a low-risk, read-only official AI tool.
- [ ] The module must provide `prepare_ohlcv_data`.
- [ ] The module must provide `validate_ohlcv_quality`.
- [ ] `validate_ohlcv_quality` must be stateless and diagnostic-only.
- [ ] `validate_ohlcv_quality` must not repair, enrich, persist, resample, clean, or mutate input data.
- [ ] `validate_ohlcv_quality` may inspect, profile, score, report issues, and provide descriptive remediation recommendations.
- [ ] Data repair, resampling, enrichment, persistence, and cleaning workflows must be reserved for `app.services.data`.
- [ ] Caller-owned dataframes must not be mutated.
- [ ] Validation must verify the input is a pandas DataFrame.
- [ ] Validation must verify mandatory OHLC columns exist.
- [ ] Missing mandatory columns must produce structured `INVALID_INPUT` details.
- [ ] Extra columns must be ignored by default and must not fail validation unless they create ambiguity.
- [ ] Validation must verify datetime column or datetime-compatible index availability.
- [ ] Validation must verify datetimes are parseable.
- [ ] Validation must report timestamp monotonicity.
- [ ] Validation must detect duplicate timestamps.
- [ ] Validation must detect duplicate OHLC/OHLCV rows.
- [ ] Validation must detect missing timestamps or inferred gaps when timeframe is known.
- [ ] Validation must distinguish market-calendar gaps from unexpected gaps where session rules are supplied.
- [ ] Validation must verify OHLC values are numeric.
- [ ] Validation must flag negative prices.
- [ ] Validation must flag zero prices.
- [ ] Validation must validate high-low relationships.
- [ ] Validation must verify OHLC values are within candle high/low range.
- [ ] Validation must flag zero volume when volume is supplied.
- [ ] Validation must flag negative volume when volume is supplied.
- [ ] Validation must verify spread is numeric and non-negative when supplied.
- [ ] Validation must detect extreme spikes using configurable thresholds.
- [ ] Validation must detect flatline candles.
- [ ] Validation must detect numeric infinities and NaN values.
- [ ] Validation must report timezone awareness.
- [ ] Validation must produce session-level statistics where possible.
- [ ] Validation must calculate a deterministic quality score.
- [ ] Validation must assign severity levels consistently.
- [ ] Validation must bound issue samples by `max_issue_samples`.
- [ ] Validation must bound issue list length by `max_issues_returned`.
- [ ] Validation must avoid oversized tool responses for large datasets.
- [ ] Validation must report symbol mismatches as `SYMBOL_MISMATCH` when `symbol` is provided and a dataframe `symbol` column exists.
- [ ] Validation must mark symbol verification as `not_available` in summary when `symbol` is provided and no dataframe `symbol` column exists.
- [ ] Validation must report timeframe mismatches as `TIMEFRAME_MISMATCH` or `UNEXPECTED_TIME_GAP` when timeframe checks fail.
- [ ] Successful validation responses must include `symbol`, `timeframe`, `rows_checked`, `quality_score`, `passed`, `severity`, `issues`, `summary`, `profile`, and `remediation`.
- [ ] Each issue must include `code`, `severity`, `message`, `column`, `row_count`, and `sample`.
- [ ] The default quality score penalty model must be: critical `-40`, error `-20`, warning `-5`, info `-1`, bounded from `0` to `100`.
- [ ] OHLCV validation must use a default quality pass threshold of `90.0`.
- [ ] OHLCV `passed=True` must require no critical issues, no error issues, and `quality_score >= quality_pass_threshold`.
- [ ] Warning and info issues may still produce `passed=True` only when the quality score remains above threshold.
- [ ] Overall severity must aggregate deterministically: any critical issue means `critical`; otherwise any error means `error`; otherwise any warning means `warning`; otherwise `info`.
- [ ] Issue truncation must be explicit through `summary["issues_truncated"]` and `summary["samples_truncated"]` when limits are reached.
- [ ] OHLCV validation must accept a pandas DataFrame.
- [ ] OHLCV validation must accept optional symbol and timeframe context.
- [ ] `validate_ohlcv_quality` success data must include symbol, timeframe, rows checked, quality score, pass/fail state, severity, issues, summary, profile, and remediation.
- [ ] Implement `app/utils/data_quality.py` after standard, errors, normalization, dataframe tools, and schema validation.
- [ ] `validate_ohlcv_quality` should handle 1,000 rows quickly for normal agent workflows.
- [ ] `validate_ohlcv_quality` should handle 100,000 rows within a practical local validation budget.
- [ ] `validate_ohlcv_quality` is stateless, diagnostic-only, and does not repair, resample, persist, enrich, or mutate input data.
- [ ] Invalid OHLCV input type must return `INVALID_INPUT`.
- [ ] Extra OHLCV columns must not fail validation unless they create ambiguity.
- [ ] Duplicate OHLC/OHLCV rows must be reported.
- [ ] Missing timestamps or inferred gaps must be reported when timeframe is known.
- [ ] Market-calendar gaps must be distinguished from unexpected gaps where session rules are supplied.
- [ ] Zero volume must be reported when volume is supplied.
- [ ] Negative volume must be reported when volume is supplied.
- [ ] Flatline candles must be detected.
- [ ] Symbol mismatches must be reported when symbol verification is available.
- [ ] Timeframe mismatches must be reported when timeframe is supplied.
- [ ] Data-quality tests cover realistic OHLCV defects.

#### `app/utils/validations.py`

Functions/classes:

- `validate_input_schema`
- `validate_output_schema`
- `validate_handoff_payload`
- `validate_evidence_pack`
- `validate_approval_packet`
- `validate_registry_entry`
- `validate_data_freshness`
- `VALIDATION_FAILED`
- `VALID_RISK_LEVELS`
- `VALID_ENVIRONMENT_MODES`

Requirements:

- [ ] Strict schema-version enforcement occurs only when a caller or schema requires a version.
- [ ] `validate_input_schema` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_output_schema` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_handoff_payload` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_evidence_pack` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_approval_packet` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_registry_entry` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_data_freshness` must be implemented as a low-risk, read-only official AI tool.
- [ ] Official AI tools must return the standard response schema.
- [ ] The module must provide reusable validation helpers for agent, workflow, tool, registry, evidence, approval, freshness, artifact, and payload contracts.
- [ ] `validate_numeric_range` must be a support helper returning a native validation result.
- [ ] `validate_required_fields` must be a support helper returning a native validation result.
- [ ] Native validation results must include at minimum `valid`, `message`, `code`, and `details`.
- [ ] Official validators may wrap native validation results in standard tool envelopes.
- [ ] Numeric validation must support risk values, prices, volumes, spreads, scores, thresholds, and allocation limits.
- [ ] Numeric validation must reject non-numeric values with deterministic details.
- [ ] Numeric validation must reject `NaN`, positive infinity, and negative infinity unless a future specialized function explicitly allows them.
- [ ] Numeric validation bounds must be inclusive unless documented otherwise.
- [ ] Numeric validation messages must include the logical field name.
- [ ] Missing required fields must be explicit.
- [ ] Unknown extra fields must be rejected by default for official schema validators.
- [ ] Schemas may explicitly allow extra fields through a documented schema policy.
- [ ] Input and output schema validators must support optional schema-version checks.
- [ ] Version mismatches must return `VALIDATION_FAILED` with a clear compatibility message.
- [ ] Schema compatibility must follow semantic-version rules.
- [ ] Schema compatibility must require the same major version.
- [ ] Schema compatibility may accept payload minor versions less than or equal to the schema minor version when no breaking change is declared.
- [ ] Schema compatibility may be overridden by an explicit compatible-version allowlist in the schema.
- [ ] Schema validation errors must return the specific path to the invalid field.
- [ ] Official schema validator errors must include `invalid_fields` as a bounded list of `{path, code, message}` objects where practical.
- [ ] Invalid-field paths must use a deterministic format such as JSON Pointer.
- [ ] Dot-path strings may be allowed for human-readable display when documented.
- [ ] Nested validation errors must include the nearest valid parent path when the exact path cannot be determined.
- [ ] Schema validation error details must remain bounded and redacted.
- [ ] Evidence validation must require source, timestamp, and evidence type.
- [ ] Approval packet validation must require action, reason, evidence, risk class, and approval status.
- [ ] Registry entry validation must require name, version, category or domain, risk level, and status.
- [ ] Risk-level validation must use the central `VALID_RISK_LEVELS` model.
- [ ] Environment validation must use the central `VALID_ENVIRONMENT_MODES` model unless a stricter allowlist is supplied.
- [ ] Blocked action validation must require an `action` field.
- [ ] Blocked action validation must fail closed when `payload["action"]` appears in `blocked_actions`.
- [ ] Freshness validation must require a timestamp field with default `as_of`.
- [ ] Freshness validation must support a configurable timestamp field.
- [ ] Freshness validation must compare against injected timestamps where supported.
- [ ] Artifact reference validation must require `artifact_id`, `version`, and at least one location field such as `storage_path`, `uri`, or `content_hash`.
- [ ] Schema validation helpers must enforce configured maximum depth, maximum field count, maximum issue count, maximum sample count, and maximum payload size.
- [ ] Resource-limit failures must return bounded diagnostics.
- [ ] Resource-limit failures must include the relevant path or validation area where available.
- [ ] Schema validation helpers must avoid dumping entire payloads in errors.
- [ ] Schema validation must accept payload mappings.
- [ ] Input/output schema validation must accept schema mappings.
- [ ] Schema validators must accept optional `schema_version`.
- [ ] Numeric-range validation must accept a value, logical field name, optional minimum, optional maximum, and `allow_none`.
- [ ] Blocked-action validation must accept payload and blocked-action list.
- [ ] Artifact-reference validation must accept artifact identity, version, and location/hash fields.
- [ ] Native validation helpers must return validation-result dictionaries containing at least `valid`, `message`, `code`, and `details`.
- [ ] Schema validation failures must include bounded invalid-field diagnostics with deterministic field paths.
- [ ] Schema validation errors must include invalid-field path, error code, sanitized message, and bounded details.
- [ ] Documentation must include schema examples for evidence packs, approval packets, registry entries, freshness metadata, and artifact references.
- [ ] Implement `app/utils/validations.py` after standard, errors, normalization, security, auth, and observability foundations.
- [ ] Validators accept supported enum values and strings where practical, then normalize to canonical JSON-safe strings.
- [ ] Schema validation errors include deterministic invalid-field paths.
- [ ] Official schema validation errors include bounded `invalid_fields` diagnostics where practical.
- [ ] Canonical JSON output must be deterministic across equivalent payloads.
- [ ] Schema validation helpers must be optimized for low latency.
- [ ] Schema validation helpers must not perform blocking I/O.
- [ ] Schema validation helpers must not perform network calls.
- [ ] Schema validation helpers must not introduce unbounded CPU spikes during normal market-data processing.
- [ ] Official AI tool docstrings must explain what evidence the tool produces.
- [ ] Documentation must describe the structured logging schema.
- [ ] Documentation must define schema-validation invalid-field path format.
- [ ] Documentation must define schema-validation resource limits and performance expectations.
- [ ] Official tools pass `validate_tool_response_schema`.
- [ ] Public responses, metadata, audit records, logs, and serialized payloads never expose enum objects directly.
- [ ] Schema validation resource limits prevent unbounded CPU, memory, and response sizes.
- [ ] Non-numeric OHLC values must be reported.
- [ ] Non-numeric or negative spread must be reported when spread is supplied.
- [ ] Missing required payload fields must fail explicitly.
- [ ] Schema version mismatches must fail with `VALIDATION_FAILED`.
- [ ] Schema validation of oversized payloads must fail with bounded diagnostics.
- [ ] Schema validation errors for nested fields must include deterministic field paths.
- [ ] Blocked-action payloads without `action` must fail clearly.
- [ ] Blocked actions must fail closed.
- [ ] Missing freshness metadata must fail.
- [ ] Artifact references missing identity, version, or location/hash must fail.
- [ ] Official AI tool tests must verify standard return schema compliance.
- [ ] Standard response tests must verify success envelope, error envelope, metadata, invalid schema, missing keys, execution timing, schema constants, and error code validation.
- [ ] Data-quality tests must verify clean OHLCV data, missing columns, extra columns, symbol mismatch, timeframe mismatch, duplicates, gaps, bad OHLC, zero/negative values, spread, volume, spikes, flatlines, truncation limits, and schema compliance.
- [ ] Schema-validation tests must verify native helper results, required fields, input/output schemas, schema versioning, handoffs, evidence, approvals, registry entries, blocked actions, freshness, and artifact references.
- [ ] Schema-validation tests must verify invalid-field paths for flat and nested payloads.
- [ ] Schema-validation tests must verify payload-size, depth, field-count, issue-count, and sample-count limits.
- [ ] Schema-validation tests must verify low-latency behavior with representative market-data payloads.
- [ ] Schema-validation tests must verify no blocking I/O or network access occurs.
- [ ] Official tools have schema compliance tests.

#### `app/utils/security.py`

Functions/classes:

- `redact_text`
- `redact_mapping`
- `hash_password`
- `verify_password`
- `encrypt_value`
- `decrypt_value`
- `SecurityError`
- `SECRET_VERSION_NOT_FOUND`

Requirements:

- [ ] Agents must not call low-level helpers such as `normalize_timestamp`, `ensure_dir`, or `hash_password` unless a workflow explicitly approves that capability.
- [ ] Sensitive runtime settings and provider credentials are supplied through secure environment/configuration mechanisms.
- [ ] `redact_text` must be classified as a low-risk, read-only official AI tool only for approved audit/log-redaction workflows.
- [ ] `redact_mapping` must be classified as a low-risk, read-only official AI tool only for approved audit/log-redaction workflows.
- [ ] `encrypt_data` must remain a restricted support helper and must not be attached to agents by default.
- [ ] `decrypt_data` must remain a restricted support helper and must not be attached to agents by default.
- [ ] The module must provide sensitive-key detection.
- [ ] The module must provide scalar redaction.
- [ ] The module must provide text redaction.
- [ ] The module must provide mapping redaction.
- [ ] The module must provide password hashing.
- [ ] The module must provide password verification.
- [ ] The module must provide encryption key loading.
- [ ] The module must provide encryption.
- [ ] The module must provide decryption.
- [ ] The module must provide active secret-version selection.
- [ ] Secret-like keys must be detected case-insensitively.
- [ ] Redaction must use a denylist-first strategy.
- [ ] The denylist must include password, passwd, token, secret, key, credential, authorization, auth, API key, private key, access key, login, session, cookie, bearer, broker, and encryption-related patterns.
- [ ] Denylist matching must be case-insensitive.
- [ ] Denylist matching must support partial-key matching for common sensitive names.
- [ ] Redaction helpers must provide an explicit allowlist mechanism for fields that are safe to log despite matching denylist patterns.
- [ ] Redaction allowlist decisions must be narrow and field-specific.
- [ ] Redaction allowlist decisions must not allow broad wildcard exposure of secrets.
- [ ] Redaction helpers must expose diagnostics showing which fields were redacted without exposing redacted values.
- [ ] Redaction must preserve non-sensitive fields.
- [ ] Redaction must handle nested dictionaries and lists.
- [ ] Redaction must stop safely at `MAX_REDACTION_DEPTH` and mark truncated structures.
- [ ] Redaction must be applied before sensitive values appear in logs, error responses, metadata, remediation text, tool responses, events, notifications, metrics, health checks, dead-letter diagnostics, or canonical JSON payloads.
- [ ] Canonical JSON serialization must redact sensitive values by default unless a caller explicitly disables redaction in a trusted internal context.
- [ ] Canonical JSON serialization must expose redaction configuration through documented options.
- [ ] Password hashing must use Argon2id as the preferred production algorithm.
- [ ] If Argon2id is unavailable, the implementation must fail clearly unless a separately approved fallback is configured.
- [ ] Password verification must use constant-time comparison where relevant.
- [ ] Encryption features must use `cryptography.fernet.Fernet` for phase 1 symmetric encryption when encryption is enabled.
- [ ] Missing `cryptography` must not break module import, but encryption/decryption calls must fail with a clear configuration error.
- [ ] Encryption key loading must never log key material.
- [ ] Environment-based encryption keys must use `ENCRYPTION_KEY`.
- [ ] `ENCRYPTION_KEY` must be a 32-byte URL-safe base64-encoded Fernet key when environment-based key loading is used.
- [ ] Encryption and decryption failures must not expose plaintext or key material.
- [ ] Secret version selection must choose the active item with the highest numeric version.
- [ ] If no active secret version exists, the function must raise `SecurityError` or return a structured `SECRET_VERSION_NOT_FOUND` error at the tool boundary.
- [ ] Duplicate active secret versions with the same numeric version must fail closed with `SECRET_VERSION_CONFLICT`.
- [ ] Security helpers must accept text, scalars, mappings, passwords, hashed passwords, encryption keys, encrypted tokens, and secret-version mappings.
- [ ] Event metadata must not include secrets.
- [ ] Documentation must include safe examples that do not contain real secrets.
- [ ] Implement `app/utils/security.py` before logging, settings, events, notifications, and audit-safe behavior are finalized.
- [ ] Security helpers must avoid expensive redaction recursion loops.
- [ ] Security helpers must use recursion depth protection for nested structures.
- [ ] Security helpers must avoid logging sensitive payloads during failure.
- [ ] Error details must not expose secrets.
- [ ] Sensitive values must be redacted before logging.
- [ ] Sensitive values must be redacted before appearing in error responses.
- [ ] Sensitive values must be redacted before appearing in metadata.
- [ ] Sensitive values must be redacted before appearing in remediation messages.
- [ ] Sensitive values must be redacted before canonical JSON serialization where configured.
- [ ] Sensitive values must be redacted before appearing in exception text exposed to callers.
- [ ] Encryption keys must never be logged.
- [ ] Password hashes must never be treated as plaintext.
- [ ] Approval packets must not leak secrets through error messages.
- [ ] Path helpers must defend against unsafe traversal when `base_dir` is supplied.
- [ ] Official AI tools must declare side effects correctly.
- [ ] Side-effecting utilities must not be attached to agents without explicit approval.
- [ ] Validation tools must fail closed when blocked actions are detected.
- [ ] Unknown environment modes must fail validation.
- [ ] Invalid freshness evidence must be surfaced, not ignored.
- [ ] Redaction must handle nested mappings, lists, string payloads, exception messages, metadata, and returned error details.
- [ ] Encryption and decryption failures must not expose plaintext or key material.
- [ ] Secret selection must be deterministic.
- [ ] No secrets are logged.
- [ ] Redaction allowlist entries must be audited through configuration, tests, or documented approval.
- [ ] Sensitive nested mappings and lists must be redacted without mutating input.
- [ ] Excessively deep redaction structures must stop at `MAX_REDACTION_DEPTH`.
- [ ] Invalid encryption input must fail safely.
- [ ] Missing or malformed encryption keys must fail without leaking key material.
- [ ] Missing active secret versions must fail with `SecurityError` or `SECRET_VERSION_NOT_FOUND`.
- [ ] Duplicate active secret versions with the same numeric version must fail with `SECRET_VERSION_CONFLICT`.
- [ ] Security regression tests must prove common secret patterns do not leak.
- [ ] Branch coverage must be meaningful for validators and security helpers.
- [ ] Official AI tool tests must verify no secret leakage where relevant.
- [ ] Security tests must verify redaction, nested redaction, password hashing, password verification, Fernet key behavior, encryption round trip, invalid tokens, secret selection, and `SECRET_VERSION_NOT_FOUND`.
- [ ] Security tests must verify metric labels reject sensitive or high-cardinality values.
- [ ] Security tests verify redaction and no secret leakage.

#### `app/utils/settings.py`

Functions/classes:

- `HARUQUANT_HOME`
- `RuntimeSettings`
- `HaruQuantConfigurationError`
- `CONFIGURATION_ERROR`

Requirements:

- [ ] `load_runtime_settings` must remain a support helper and must not be attached to agents by default.
- [ ] The module must define immutable typed runtime settings.
- [ ] Runtime settings must include environment, log level, data directory, cache directory, audit directory, timezone, and strict validation.
- [ ] Runtime settings must include logging configuration.
- [ ] Logging configuration must include optional log directory, file logging enablement, rotation maximum size, retained file count, and retention deletion policy.
- [ ] Logging configuration must include human-readable console format selection and color enablement or disablement.
- [ ] Runtime settings must include auth configuration.
- [ ] Runtime settings must include Event Bus configuration.
- [ ] Runtime settings must include notification configuration.
- [ ] Runtime settings must include observability configuration.
- [ ] The module must load runtime settings from explicit calls only.
- [ ] The module must load runtime settings from mappings.
- [ ] The module must inject runtime settings into an explicitly supplied mutable target mapping.
- [ ] Required settings must have deterministic defaults where safe.
- [ ] Sensitive settings must not be logged.
- [ ] Environment names must be validated.
- [ ] Path settings must use `Path` objects.
- [ ] `.env` loading must be optional and dependency-aware.
- [ ] Settings source precedence must be explicit mapping/function arguments, then environment variables, then `.env` file, then safe defaults.
- [ ] Importing `app.utils` must not read `.env`.
- [ ] Optional dependency absence must not break import.
- [ ] Optional dependency absence must fail only when the requested feature requires the dependency.
- [ ] Invalid settings must fail clearly with configuration errors.
- [ ] `strict_validation=True` must escalate non-critical validation warnings to failures where the caller asks settings to enforce strict behavior.
- [ ] `strict_validation=False` must allow warnings to be returned or logged without failing settings load.
- [ ] `inject_runtime_settings` must mutate only the provided target mapping and return that mapping.
- [ ] Default runtime paths must resolve under `HARUQUANT_HOME` when configured.
- [ ] Production deployments must configure `HARUQUANT_HOME` explicitly.
- [ ] Default directories must be `data`, `cache`, and `audit` under the resolved HaruQuant home directory.
- [ ] OHLCV validation must accept configurable datetime, open, high, low, close, volume, and spread column names.
- [ ] OHLCV validation must accept configurable gap multiplier, spike threshold, issue-sample limit, and returned-issue limit.
- [ ] Schema validators must accept resource-limit configuration where applicable.
- [ ] Freshness validation must accept timestamp metadata, configurable timestamp field, injected `now`, and `max_age_seconds`.
- [ ] Settings loaders must accept mappings and optional `.env` file paths.
- [ ] Settings loaders must return `RuntimeSettings`.
- [ ] Settings injection must return the same target mapping it mutates.
- [ ] Implement `app/utils/settings.py` before adapters and runtime configuration consumers.
- [ ] Importing any `app.utils` module must not read `.env` files.
- [ ] Importing any `app.utils` module must not mutate environment variables.
- [ ] Time handling must be deterministic and timezone-safe across supported runtime environments.
- [ ] Missing optional dependency failures must use `HaruQuantConfigurationError`, `CONFIGURATION_ERROR`, or the standard tool error envelope where applicable.
- [ ] Missing pandas fails only when dataframe helpers are called, with a clear configuration/dependency error.
- [ ] When `HARUQUANT_HOME` is not configured, local/test defaults must resolve under a deterministic `.haruquant` directory beneath the current working directory.
- [ ] Spikes must be detected using configurable thresholds.
- [ ] Schema validation of deeply nested payloads must stop at configured depth.
- [ ] Invalid environment modes must fail.
- [ ] Logger tests must verify file logging writes only to configured safe log directories.
- [ ] Logger tests must verify log rotation by maximum file size or equivalent configured policy.
- [ ] Logger tests must verify old rotated log files are deleted according to configured retention limits without deleting unrelated files.
- [ ] Data-quality tests must verify 10,000 bad rows return no more than configured issue and sample limits.
- [ ] Settings tests must verify defaults, mapping load, invalid environments, `strict_validation`, path normalization, and injection.

#### `app/utils/auth.py`

Functions/classes:

- `Error`
- `SECURITY_ERROR`

Requirements:

- [ ] The system must implement `app/utils/` as the shared utility foundation for HaruQuantAI.
- [ ] The module must support higher-level domains including data, research, simulation, risk, portfolio, execution, analytics, governance, and agentic workflows.
- [ ] The module must provide project-wide structured logging.
- [ ] The module must provide standard HaruQuant tool response envelopes.
- [ ] The module must provide deterministic error codes and exception mapping.
- [ ] The module must provide timestamp and timezone normalization using a UTC-first policy.
- [ ] The module must provide safe path handling.
- [ ] The module must provide dataframe and OHLCV helper utilities.
- [ ] The module must provide OHLCV data-quality validation with bounded diagnostics and deterministic scoring.
- [ ] The module must provide schema, payload, risk-level, numeric-range, and contract validation.
- [ ] The module must provide security helpers for redaction, hashing, encryption, decryption, and secret-version selection.
- [ ] The module must provide runtime settings loading and injection with deterministic source precedence.
- [ ] The module must provide standard execution timing helpers for consistent `execution_ms` values.
- [ ] The module must provide explicit tool-response schema validation constants.
- [ ] The module must provide schema-version compatibility checks for validation contracts.
- [ ] The module must provide resource-limit controls for large validation workloads.
- [ ] The module must support lazy loading for pandas and other heavy optional dependencies.
- [ ] The module must preserve a stateless, diagnostic-only data-quality boundary.
- [ ] The module must support string-serializable constants and enum-friendly canonicalization.
- [ ] The module must support extensible domain error mapping through `Error` and compatible `code` attributes.
- [ ] The module must provide auth context validation and authorization support helpers.
- [ ] Auth helpers may validate identity context, roles, scopes, and permissions, but must not become the identity provider.
- [ ] Authorization checks must deny access by default when context is missing or malformed.
- [ ] Agent access to official tools must be allowlisted.
- [ ] Agent/tool caller:** Calls approved official AI tools and receives standard envelopes.
- [ ] Authorized tool caller:** A caller with explicit permission to invoke an official AI tool.
- [ ] Authenticated principal:** A user, service, workflow, or agent identity represented in auth context.
- [ ] Workflow caller:** Uses validation, tracing, metadata, event, alert, and handoff utilities in automated workflows.
- [ ] Production module developer:** Imports support helpers from `app.utils` and uses typed native helper APIs.
- [ ] Higher-level domain module:** Data, research, simulation, risk, portfolio, execution, analytics, governance, and agentic workflow modules consume utility functionality.
- [ ] Human approver:** Uses or is represented by approval packets requiring action, reason, evidence, risk class, and approval status.
- [ ] Maintainer/reviewer:** Governs public API changes, CI gates, quality checks, and acceptance criteria.
- [ ] Security reviewer:** A maintainer responsible for auth, secret redaction, encrypted payload handling, and no-leak guarantees.
- [ ] The utils module will provide auth primitives and validation helpers, but the application or infrastructure layer will own external identity-provider integration.
- [ ] Agent access to encryption or decryption must require explicit security approval, permission checks, and audit logging.
- [ ] The module must define a shared authentication context model for internal tools, agents, workflows, and services.
- [ ] The auth context must support principal ID, principal type, roles, permissions, scopes, tenant or environment context where applicable, request ID, workflow ID, and correlation ID.
- [ ] The module must provide validation helpers for authenticated principal context.
- [ ] The module must provide authorization helper checks for required roles, permissions, scopes, and tool names.
- [ ] Authorization helpers must deny by default when identity, permission, role, scope, or tool context is missing.
- [ ] Agents must be authorized through an explicit tool allowlist before accessing official AI tools.
- [ ] Side-effecting or sensitive utilities must require explicit permission checks before execution.
- [ ] Auth helpers must return deterministic validation results or standard tool error envelopes at official tool boundaries.
- [ ] Auth helpers must not validate external identity-provider tokens unless an explicit adapter is supplied by the application layer.
- [ ] Auth helpers must not contact external identity providers at import time.
- [ ] Auth context must be redacted before logging, events, metrics, or error reporting.
- [ ] Auth failures must use deterministic error codes such as `PERMISSION_DENIED`, `INVALID_AUTH_CONTEXT`, or `AUTHORIZATION_FAILED`.
- [ ] Authentication and authorization events must be observable through logs, metrics, and sanitized audit events.
- [ ] Auth helpers must accept sanitized auth context mappings or typed auth context objects.
- [ ] Auth helpers must accept required permissions, roles, scopes, and tool names.
- [ ] Auth helpers must return allow/deny decisions with sanitized reason details.
- [ ] Redaction allowlist misuse must return `SECURITY_ERROR` or a more specific deterministic security code.
- [ ] Documentation must include examples of safe redaction allowlist use.
- [ ] Implement `app/utils/auth.py` before tool allowlists and side-effect permission checks.
- [ ] Auth helpers must avoid hidden global mutable state.
- [ ] Auth failures must map to `PERMISSION_DENIED`, `INVALID_AUTH_CONTEXT`, or `AUTHORIZATION_FAILED`.
- [ ] Auth context must be redacted before logging.
- [ ] Agent tool authorization must use explicit allowlists.
- [ ] Redaction allowlist entries must be narrow and auditable.
- [ ] Documentation must describe auth context fields.
- [ ] Documentation must describe authorization deny-by-default behavior.
- [ ] Documentation must describe redaction denylist defaults.
- [ ] Documentation must describe audited redaction allowlist configuration.
- [ ] Documentation must warn against broad redaction allowlist rules.
- [ ] File logging is explicit, safely scoped, rotating, and retention-limited when enabled.
- [ ] Auth helpers deny by default and enforce tool allowlists.
- [ ] The module must provide canonical JSON serialization for audit, hashing, caching, reproducible tests, and comparison workflows.
- [ ] Missing auth context must deny access.
- [ ] Malformed auth context must deny access with a deterministic error.
- [ ] Missing required role, permission, or scope must deny access.
- [ ] Unknown tool name in authorization checks must deny access.
- [ ] Redaction allowlist conflicts with denylist must fail closed unless explicitly approved.
- [ ] Redaction allowlist configuration must be reviewed and tested.
- [ ] Security tests must verify redaction denylist matching.
- [ ] Security tests must verify audited allowlist exceptions.
- [ ] Security tests must verify denylist/allowlist conflict behavior.
- [ ] Auth tests must cover valid auth context.
- [ ] Auth tests must cover missing auth context.
- [ ] Auth tests must cover malformed auth context.
- [ ] Auth tests must cover missing role, permission, and scope.
- [ ] Auth tests must cover denied-by-default behavior.
- [ ] Auth tests must verify no token or credential leakage.
- [ ] Redaction denylist and audited allowlist behavior is implemented and tested.

#### `app/utils/event_bus.py`

Functions/classes:

- `event_id`
- `causation_id`
- `BACKPRESSURE_EXCEEDED`
- `QUEUE_FULL`

Requirements:

- [ ] The module must provide request, workflow, generic ID, version, correlation ID, causation ID, and idempotency helpers.
- [ ] The module must provide Event Bus and pub/sub primitives.
- [ ] Event Bus utilities may route events, but must not own application orchestration.
- [ ] Event Bus utilities must not place trades, approve trades, modify orders, activate live systems, or override kill switches.
- [ ] Event publisher:** A module or workflow that emits validated events.
- [ ] Event subscriber:** A handler that receives events by topic or event type.
- [ ] The utils module will provide Event Bus contracts and an in-process implementation, while production broker-backed adapters may live in infrastructure modules or optional adapters.
- [ ] The system must provide a shared Event Bus abstraction for internal utility, workflow, alert, and error-routing events.
- [ ] The system must define a standard event envelope.
- [ ] The standard event envelope must include `event_id`, `event_type`, `event_version`, `source`, `severity`, `timestamp`, `request_id`, `workflow_id`, `correlation_id`, `causation_id`, `idempotency_key`, `payload`, and `metadata`.
- [ ] Event payloads must be JSON-serializable or fail validation clearly.
- [ ] Event payloads must be redacted before logging, metrics labeling, notification routing, audit serialization, or dead-letter forwarding.
- [ ] The Event Bus must support publish and subscribe operations.
- [ ] The Event Bus must support topic or event-type subscriptions.
- [ ] The Event Bus must support handler registration and unregistration.
- [ ] Distributed broker adapters are not required to guarantee global ordering unless the adapter explicitly documents that guarantee.
- [ ] The Event Bus must support error isolation so one failing subscriber does not silently prevent other subscribers from receiving the event.
- [ ] The Event Bus must route subscriber failures to the error-routing mechanism.
- [ ] The Event Bus must support retry policy metadata for delivery failures.
- [ ] The Event Bus must support dead-letter routing for events that exceed retry limits.
- [ ] The Event Bus must support idempotency keys to reduce duplicate event processing.
- [ ] Idempotency keys must have both a configurable TTL and a configurable maximum cache size.
- [ ] The default idempotency TTL must be short enough to prevent memory growth but long enough to cover expected retry windows.
- [ ] Idempotency entries must store compact metadata rather than full event payloads by default.
- [ ] Idempotency duplicate detection may use hashes of sanitized canonical event payloads and must not retain full sensitive payloads.
- [ ] Idempotency-key storage must not grow without bound in long-running processes.
- [ ] Expired idempotency keys must be evicted deterministically.
- [ ] The default idempotency cache eviction policy must evict expired entries first, then oldest entries.
- [ ] Idempotency cache eviction must be observable through logs and metrics.
- [ ] Idempotency cache state must not expose sensitive payloads, raw event bodies, tokens, credentials, approval packets, or private data.
- [ ] Duplicate idempotency keys with different payload hashes must fail safely or emit deterministic conflict diagnostics.
- [ ] The Event Bus must support correlation IDs across tool calls, logs, notifications, and metrics.
- [ ] The Event Bus must expose bounded queue depth or handler backlog diagnostics.
- [ ] Event Bus delivery diagnostics must include delivered, failed, retried, dead-lettered, dropped counts, and queue depth where applicable.
- [ ] When the Event Bus queue is full, publish operations must immediately return a deterministic `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` error code.
- [ ] Queue-full behavior must return `BACKPRESSURE_EXCEEDED` when the caller can retry later.
- [ ] Queue-full behavior may return `QUEUE_FULL` for lower-level queue diagnostics.
- [ ] Event publishers must receive enough structured queue-full detail to implement retry, degradation, or fail-closed behavior.
- [ ] Event Bus queue policies must be explicit modes such as fail-fast, bounded wait, or lossy-drop.
- [ ] Production Event Bus queue policy must default to fail-fast for critical workflows.
- [ ] Queue-full behavior must not silently drop events unless the caller explicitly selected a lossy policy.
- [ ] Lossy-drop behavior must be allowed only for explicitly configured low-severity telemetry events.
- [ ] Dropped events must be counted in metrics.
- [ ] Dropped events must be logged with sanitized metadata.
- [ ] Queue-full diagnostics must include event type, source, severity, queue name or topic, queue depth, configured queue limit, request ID, workflow ID, and correlation ID where available.
- [ ] Queue-full diagnostics must not include raw event payloads by default.
- [ ] The Event Bus must not open network connections during module import.
- [ ] Production external broker adapters must be dependency-aware and lazy-loaded.
- [ ] Production external broker adapters must fail clearly when required optional dependencies are missing.
- [ ] Production external broker adapters must implement circuit breakers.
- [ ] Event Bus support must not approve trades, place orders, mutate broker state, or make risk decisions.
- [ ] External pub/sub adapters must implement a circuit-breaker pattern.
- [ ] Official AI tool responses must not return whole dataframes.
- [ ] Event Bus publishing must accept an event type, source, severity, payload, metadata, request ID, workflow ID, correlation ID, and idempotency key.
- [ ] Event Bus subscription must accept topic or event-type filters and handler references.
- [ ] Event Bus publish operations must return deterministic delivery or enqueue results.
- [ ] Event Bus delivery diagnostics must include delivered, failed, retried, dead-lettered, dropped counts, and queue depth where applicable.
- [ ] Queue-full errors must include sanitized queue diagnostics.
- [ ] Queue diagnostics must not include raw payloads.
- [ ] Circuit-breaker diagnostics must not include credentials, provider tokens, message bodies, or raw event payloads.
- [ ] Implement `app/utils/event_bus.py` before error routing and notification routing.
- [ ] Queue-full publishing returns deterministic `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` diagnostics.
- [ ] Importing any `app.utils` module must not configure global logging handlers unexpectedly.
- [ ] Importing any `app.utils` module must not initialize external pub/sub clients.
- [ ] Event Bus handler registration, unregistration, publishing, retry, dead-letter handling, and idempotency tracking must be thread-safe and/or async-safe.
- [ ] Event Bus handlers must not share mutable event payloads unless payloads are explicitly copied or treated as immutable by contract.
- [ ] Event Bus event versioning must support forward compatibility for event consumers.
- [ ] Event Bus delivery diagnostics must remain consistent under concurrent publishing.
- [ ] Optional Event Bus broker dependencies must be lazy-loaded.
- [ ] Utilities must be safe with large datasets.
- [ ] Utilities must avoid unnecessary deep copies.
- [ ] Dataframe helpers must document copy, view, and transformed-data behavior.
- [ ] Agent-facing diagnostics must prefer summaries, counts, and compact samples.
- [ ] Returned issue lists and samples must be bounded.
- [ ] Event Bus diagnostics must remain bounded to avoid oversized logs and metrics.
- [ ] Event Bus idempotency storage must be bounded by TTL and maximum cache size.
- [ ] Event Bus queues must have explicit limits.
- [ ] Queue-full behavior must fail fast or follow a documented bounded policy.
- [ ] Lossy-drop behavior may be allowed only when explicitly configured for low-severity telemetry events.
- [ ] Backpressure diagnostics must be bounded and redacted.
- [ ] External Event Bus broker outages must be isolated through circuit breakers and deterministic error codes.
- [ ] Event publish failures must map to `EVENT_PUBLISH_FAILED`.
- [ ] Event subscriber failures must map to `EVENT_HANDLER_FAILED`.
- [ ] Dead-letter routing failures must map to `EVENT_DEAD_LETTER_FAILED`.
- [ ] Queue-full errors must be returned immediately to publishers.
- [ ] Backpressure errors must be distinct from subscriber execution errors.
- [ ] Subscriber execution errors must not be misclassified as publish failures unless publish requires synchronous all-handler success.
- [ ] Sensitive values must be redacted before appearing in Event Bus payload logs.
- [ ] Event payloads must be redacted before publication when they contain sensitive fields.
- [ ] Dead-letter event storage, if configured outside utils, must receive redacted payloads by default.
- [ ] Idempotency keys must not encode raw secrets or raw payloads.
- [ ] Event IDs, request IDs, workflow IDs, and correlation IDs must be safe for logs and metrics.
- [ ] Event payload hashes, if used for idempotency conflict detection, must not allow reconstruction of sensitive payloads.
- [ ] Dead-letter payloads must be redacted by default before storage or forwarding.
- [ ] Documentation must describe Event Bus event envelope fields.
- [ ] Documentation must define Event Bus idempotency TTL behavior.
- [ ] Documentation must define Event Bus idempotency maximum cache-size behavior.
- [ ] Documentation must define Event Bus queue-full and backpressure behavior.
- [ ] Documentation must define Event Bus delivery, retry, and dead-letter behavior.
- [ ] Documentation must define Event Bus concurrency guarantees.
- [ ] Documentation must define whether the Event Bus implementation is synchronous, asynchronous, or dual-mode.
- [ ] Documentation must state that deterministic ordered delivery applies to the in-process Event Bus per event type, not necessarily to distributed broker adapters.
- [ ] Documentation must describe circuit-breaker configuration for external pub/sub adapters.
- [ ] Documentation must document each event type's ordering, durability, retry, and loss-tolerance expectations.
- [ ] Event Bus idempotency storage is bounded by TTL and maximum cache size.
- [ ] Event Bus idempotency storage uses compact metadata rather than full event payloads by default.
- [ ] Event Bus queue policies are explicit and production critical workflows default to fail-fast behavior.
- [ ] Event Bus publish, subscribe, unsubscribe, retry, and dead-letter paths are thread-safe and/or async-safe.
- [ ] External pub/sub adapters have circuit breakers.
- [ ] Documentation covers Event Bus backpressure, idempotency, circuit breakers, clock drift, schema field paths, and redaction allowlist governance.
- [ ] The system must provide an in-process pub/sub mechanism suitable for local development, unit tests, and deterministic workflow tests.
- [ ] The Event Bus must support disabled or no-op adapter behavior for tests and local development where event delivery is intentionally suppressed.
- [ ] The in-process Event Bus must guarantee deterministic, ordered handler execution per event type to ensure reproducible test outcomes.
- [ ] Idempotency tracking must be testable with injected clocks or deterministic time controls.
- [ ] Event publishing with missing event type must fail validation.
- [ ] Event publishing with unserializable payload must fail validation.
- [ ] Duplicate event IDs must be handled idempotently where idempotency keys are supplied.
- [ ] Idempotency cache TTL expiration must not break valid future event processing.
- [ ] Idempotency cache eviction must not expose old event payloads.
- [ ] Concurrent publish calls for the same idempotency key must not double-deliver an event.
- [ ] Subscriber failure must not prevent other subscribers from receiving the event.
- [ ] Concurrent subscriber registration and publishing must not corrupt handler lists.
- [ ] Concurrent subscriber unregistration during publishing must have deterministic behavior.
- [ ] Repeated subscriber failures must route to dead-letter handling after configured retry limits.
- [ ] Event Bus queue overflow must return `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` and must not block indefinitely.
- [ ] External pub/sub adapter outage must open the circuit after the configured threshold.
- [ ] Half-open circuit recovery must not create duplicate event delivery.
- [ ] Logger tests must verify duplicate handler prevention.
- [ ] Event Bus tests must cover publish success.
- [ ] Event Bus tests must cover subscription and unsubscription.
- [ ] Event Bus tests must verify deterministic ordered handler execution per event type for the in-process bus.
- [ ] Event Bus tests must cover subscriber failure isolation.
- [ ] Event Bus tests must cover retry and dead-letter behavior.
- [ ] Event Bus tests must cover idempotency keys.
- [ ] Event Bus tests must verify idempotency TTL expiration.
- [ ] Event Bus tests must verify maximum idempotency cache size enforcement.
- [ ] Event Bus tests must verify duplicate idempotency key handling.
- [ ] Event Bus tests must verify concurrent publish behavior.
- [ ] Event Bus tests must verify concurrent subscribe and unsubscribe behavior.
- [ ] Event Bus tests must verify concurrent retry and dead-letter behavior where supported.
- [ ] Event Bus tests must cover payload serialization failure.
- [ ] Event Bus tests must verify queue-full behavior returns `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED`.
- [ ] Event Bus tests must cover deterministic backpressure behavior.
- [ ] Event Bus tests must verify dropped-event metrics.
- [ ] Event Bus tests must cover queue limit or backlog diagnostics.
- [ ] Event Bus tests must verify external adapter circuit-breaker closed, open, and half-open states with fake adapters.
- [ ] Event Bus tests must verify no secret leakage in event logs.
- [ ] Event Bus tests must use fake clock and fake queue implementations where needed for deterministic time and queue behavior.
- [ ] Event Bus tests must cover disabled or no-op adapter behavior.
- [ ] Observability tests must cover Event Bus metrics.
- [ ] Observability tests must verify queue-depth metrics.

#### `app/utils/error_routing.py`

Functions/classes:

- `ErrorRoute`
- `AlertRoute`
- `route_error`
- `route_alert`
- `build_error_event`
- `sanitize_error_payload`

Requirements:

- [ ] The module must provide early alert routing and error routing so the rest of the system can report issues consistently.
- [ ] Alert routing must fail safely and must not expose sensitive information.
- [ ] The Event Bus is intended for utility, workflow, alert, and error-routing events, not direct trading execution.
- [ ] The system must provide a standard error event model.
- [ ] The error event model must include error code, severity, source module, source function or tool, request ID, workflow ID, correlation ID, sanitized message, sanitized details, and timestamp.
- [ ] Expected validation failures must be routable as warning or error events depending on severity.
- [ ] Unexpected execution failures must be routable as error or critical events.
- [ ] Critical system failures must be routable to notifications.
- [ ] Error routing must deduplicate repeated identical errors within a configurable time window.
- [ ] Error routing must prevent recursive alert storms.
- [ ] Error routing must redact secrets before publishing events, logging, metrics, or notifications.
- [ ] Error routing must preserve enough diagnostic context for troubleshooting without exposing sensitive payloads.
- [ ] Error routing must support severity-based routing rules.
- [ ] Error routing must support environment-specific routing rules.
- [ ] Error routing must support suppression rules for known noisy non-critical errors.
- [ ] Error routing must expose metrics for routed, suppressed, retried, failed, and dead-lettered error events.
- [ ] Error routing failures must not recursively trigger infinite error routing.
- [ ] Error routing must preserve the original error code and attach routing failure code separately when both exist.
- [ ] Error routing must accept sanitized exception context, deterministic error code, severity, request ID, workflow ID, and correlation ID.
- [ ] Error routing must return routed, suppressed, deduplicated, throttled, or failed status.
- [ ] Documentation must include a production readiness checklist for secrets, auth, alert routing, and metrics before enabling live workflows.
- [ ] Implement `app/utils/error_routing.py` before notification routing.
- [ ] Error routing failures must not recursively trigger infinite error routing.
- [ ] Alert failures must be logged and measured without exposing secrets.
- [ ] Error routing must preserve original error code and attach routing failure code separately when both exist.
- [ ] Error routing must sanitize exception text before alerting.
- [ ] Documentation must describe error routing behavior and severity rules.
- [ ] Documentation must describe how alerts and error routing are initialized early in the system lifecycle.
- [ ] Recursive error routing must be detected and suppressed.
- [ ] Error-routing tests must cover validation error routing.
- [ ] Error-routing tests must cover unexpected exception routing.
- [ ] Error-routing tests must cover deduplication and throttling.
- [ ] Error-routing tests must cover recursive error suppression.
- [ ] Error-routing tests must verify recursive alert suppression under circuit-open and notification-failure scenarios.

#### `app/utils/notifications.py`

Functions/classes:

- `NotificationChannel`
- `NotificationMessage`
- `NotificationResult`
- `NotificationRouter`
- `route_notification`
- `send_email_notification`
- `send_telegram_notification`
- `send_desktop_notification`
- `redact_notification_payload`

Requirements:

- [ ] The module must provide shared status, severity, risk-level, environment-mode, auth, event, notification, and health-state constants.
- [ ] The module must provide notification routing primitives for email, Telegram, and desktop channels.
- [ ] Utilities may validate, normalize, redact, serialize, route events, emit notifications, record metrics, and report issues.
- [ ] Notification utilities may alert humans or systems, but must not make trading, portfolio, risk, or strategy decisions.
- [ ] Email, Telegram, and desktop notifications must be disabled unless configured for the current environment.
- [ ] Production desktop notifications must be disabled by default.
- [ ] Notification recipients must be configured explicitly.
- [ ] Notification recipient:** A configured email, Telegram, or desktop recipient for alerts.
- [ ] Security/audit consumer:** Relies on redacted logs, metadata, tool responses, canonical JSON, events, notifications, and secret-safe error handling.
- [ ] Notification helpers will provide routing contracts and adapter boundaries, not hard-coded provider credentials.
- [ ] Email, Telegram, and desktop notification providers will be configured explicitly per environment.
- [ ] No notification channel is enabled in production without explicit configuration.
- [ ] Auth, Event Bus, notification, and observability primitives must be support helpers by default unless explicitly promoted to official AI tools.
- [ ] The system must provide notification routing primitives for email, Telegram, and desktop channels.
- [ ] Notification routing must support severity-based routing.
- [ ] Notification routing must support environment-specific routing.
- [ ] Notification routing must support channel enablement and disablement through runtime settings.
- [ ] Notification routing must support per-channel recipient configuration.
- [ ] Notification routing must support safe templates for alert title, summary, severity, source, timestamp, request ID, workflow ID, and correlation ID.
- [ ] Notification templates must render from sanitized data transfer objects rather than raw event payloads.
- [ ] Notification templates must support markdown and plain-text fallbacks to ensure readability across email, Telegram, and desktop clients.
- [ ] Notification rendering must degrade to plain text when a channel does not support markdown.
- [ ] Notification template rendering failures must return deterministic notification failure diagnostics without exposing raw payloads.
- [ ] Notification routing must not include raw sensitive payloads.
- [ ] Notification routing must redact secrets before message construction.
- [ ] Notification markdown rendering must escape or sanitize unsafe user-controlled content where applicable.
- [ ] Notification routing must support rate limiting or throttling to avoid alert storms.
- [ ] Notification routing must support deduplication of repeated alerts.
- [ ] Notification routing must produce delivery status results.
- [ ] Notification routing must publish notification success and failure events to the Event Bus.
- [ ] Notification routing must expose metrics for sent, failed, suppressed, throttled, and deduplicated notifications.
- [ ] Email notifications must support configurable SMTP or provider adapter settings without logging credentials.
- [ ] Telegram notifications must support bot-token and chat-recipient configuration without logging credentials.
- [ ] Desktop notifications must be disabled by default in production unless explicitly enabled.
- [ ] Notification adapters must be lazy-loaded and must not initialize network clients at import time.
- [ ] External notification adapters must implement circuit breakers.
- [ ] Notification delivery failures must not fail the original business operation unless the caller explicitly requires fail-closed alerting.
- [ ] External notification adapters must implement a circuit-breaker pattern.
- [ ] Notification routing must accept alert severity, channel preferences, sanitized message template data, and routing policy.
- [ ] Runtime settings must accept logging, notification, Event Bus, auth, and observability configuration.
- [ ] Notification routing must return sent, suppressed, throttled, deduplicated, failed, or disabled status.
- [ ] Desktop notification content must not include secrets.
- [ ] Documentation must include runbook sections for Event Bus backpressure incidents, notification outage incidents, clock-drift incidents, and schema-validation performance regressions.
- [ ] Implement `app/utils/notifications.py` before alert delivery is attached to workflows.
- [ ] Prometheus-compatible metrics include circuit-breaker state, queue depth, idempotency cache size, backpressure count, notification failures, and clock drift.
- [ ] Production code must not leak secrets in logs, errors, events, notifications, metrics, or health snapshots.
- [ ] Importing any `app.utils` module must not initialize notification clients.
- [ ] Wall-clock timestamp serialization must be UTC-first and safe for logs, events, notifications, metrics, health snapshots, and audit metadata.
- [ ] Notification routing, deduplication, throttling, rate-limit counters, and circuit-breaker state must be thread-safe and/or async-safe.
- [ ] Notification delivery diagnostics must remain consistent under concurrent alert bursts.
- [ ] Optional notification provider dependencies must be lazy-loaded.
- [ ] Notification delivery failures must be isolated from core utility functions unless explicitly configured otherwise.
- [ ] Notification routing must remain safe under repeated error bursts.
- [ ] Notification messages must be concise and actionable.
- [ ] External notification provider outages must be isolated through circuit breakers and deterministic error codes.
- [ ] Notification delivery must be observable through logs, metrics, or sanitized events.
- [ ] Notification routing failures must map to `NOTIFICATION_FAILED`.
- [ ] Notification configuration failures must map to `CONFIGURATION_ERROR`.
- [ ] Notification failures must distinguish configuration failure, provider timeout, provider rejection, circuit-open state, throttling, and suppression.
- [ ] Unknown Event Bus or notification provider errors must map safely to deterministic error codes.
- [ ] Sensitive values must be redacted before appearing in notification templates.
- [ ] Authorization headers must never appear in logs, metrics, events, or notifications.
- [ ] Notification recipient lists must be treated as sensitive configuration.
- [ ] Email credentials must never appear in logs, metrics, events, or notifications.
- [ ] Telegram bot tokens must never appear in logs, metrics, events, or notifications.
- [ ] Side-effecting notification and event adapter actions must require explicit configuration.
- [ ] External notification and pub/sub adapters must be lazy-loaded.
- [ ] External notification and pub/sub adapters must fail closed when credentials are missing or malformed.
- [ ] Metric labels must reject raw IDs, arbitrary user strings, exception strings, notification recipients, provider tokens, and event payload values.
- [ ] Notification markdown rendering must escape or sanitize unsafe user-controlled content where applicable.
- [ ] Auth and notification provider credentials must be excluded from Event Bus payloads by default.
- [ ] Documentation must describe notification routing rules for email, Telegram, and desktop channels.
- [ ] Documentation must define notification routing concurrency guarantees.
- [ ] Documentation must define whether each notification adapter is synchronous, asynchronous, or dual-mode.
- [ ] Documentation must describe notification throttling and deduplication behavior.
- [ ] Documentation must describe notification markdown and plain-text template fallback behavior.
- [ ] Documentation must describe circuit-breaker configuration for notification adapters.
- [ ] Importing `app.utils` does not import pandas, cryptography, dotenv, broker SDKs, notification clients, pub/sub clients, Prometheus exporters, or network clients unless the specific feature is used.
- [ ] Notification routing, throttling, deduplication, and circuit-breaker state are thread-safe and/or async-safe.
- [ ] External notification adapters have circuit breakers.
- [ ] Notification templates support markdown and plain-text fallback rendering.
- [ ] Notification templates render from sanitized data transfer objects rather than raw event payloads.
- [ ] Notification routing must support test mode with fake adapters.
- [ ] Event publishing with sensitive payload must redact before logging or notification routing.
- [ ] Notification channel disabled must return disabled or suppressed status without error.
- [ ] Notification credentials missing must fail safely without leaking configuration details.
- [ ] Notification provider timeout must return failed status and emit metrics.
- [ ] Notification markdown rendering failure must fall back to plain text.
- [ ] Unsupported notification formatting must not fail the original operation unless fail-closed alerting is explicitly configured.
- [ ] Notification adapter outage must open the circuit after the configured threshold.
- [ ] Logger tests must verify log emission does not leak passwords, tokens, API keys, broker credentials, encryption keys, private payloads, full approval packets, notification provider credentials, authorization headers, or Telegram bot tokens.
- [ ] Notification tests must cover email routing with fake adapter.
- [ ] Notification tests must cover Telegram routing with fake adapter.
- [ ] Notification tests must cover desktop routing with fake adapter.
- [ ] Notification tests must cover disabled channel behavior.
- [ ] Notification tests must cover missing credentials.
- [ ] Notification tests must cover provider failure and timeout behavior.
- [ ] Notification tests must verify throttling and deduplication.
- [ ] Notification tests must verify concurrent routing behavior.
- [ ] Notification tests must verify concurrent suppression, throttling, deduplication, and adapter-failure behavior.
- [ ] Notification tests must verify thread-safe or async-safe throttling and deduplication state.
- [ ] Notification tests must verify markdown rendering.
- [ ] Notification tests must verify plain-text fallback rendering.
- [ ] Notification tests must verify provider circuit-breaker closed, open, and half-open states with fake adapters.
- [ ] Notification tests must verify notification content does not leak secrets after template rendering.
- [ ] Observability tests must cover notification metrics.
- [ ] Grafana documentation tests or review checks must confirm dashboards cover system health, tool health, Event Bus, notifications, errors, and auth failures.
- [ ] A chaos-test profile must cover notification provider failures and pub/sub adapter outages.
- [ ] Tests prove no sensitive values leak through logs, events, notifications, metrics, dead-letter diagnostics, schema errors, or health checks.

#### `app/utils/observability.py`

Functions/classes:

- `CLOCK_DRIFT_DETECTED`

Requirements:

- [ ] The module must provide observability primitives for logs, metrics, health snapshots, and trace correlation.
- [ ] The module must provide Prometheus-compatible system-health metrics.
- [ ] The module must define Grafana dashboard expectations for operational health.
- [ ] Observability utilities may report system health, but must not decide operational actions without governance approval.
- [ ] Prometheus/Grafana metrics must include system-health visibility and must not be limited to business alerts.
- [ ] System operator:** A maintainer who monitors logs, alerts, metrics, dashboards, and health status.
- [ ] Observability consumer:** A developer, operator, or automated monitor that uses Prometheus/Grafana metrics.
- [ ] Prometheus metrics export may be provided by application runtime, while utils provides metric registration and recording helpers.
- [ ] Grafana dashboards may be maintained as documentation or version-controlled dashboard definitions.
- [ ] Metrics and logs are operational telemetry and must not contain raw market payloads, secrets, or approval-packet contents.
- [ ] The system must provide observability helpers for logs, metrics, health checks, and trace correlation.
- [ ] The system must expose Prometheus-compatible metrics for system health.
- [ ] The system must support Grafana dashboards for operational visibility.
- [ ] Metrics must cover official AI tool call counts.
- [ ] Metrics must cover official AI tool success and error counts.
- [ ] Metrics must cover tool execution latency.
- [ ] Metrics must cover validation failure counts by error code and source.
- [ ] Metrics must cover Event Bus events published, delivered, failed, retried, dead-lettered, dropped, and backpressured.
- [ ] Metrics must cover Event Bus queue depth or backlog where applicable.
- [ ] Metrics must cover Event Bus idempotency cache size, eviction count, duplicate count, and conflict count.
- [ ] Metrics must cover notification sent, failed, suppressed, throttled, and deduplicated counts.
- [ ] Metrics must cover notification delivery latency.
- [ ] Metrics must cover logging error counts where detectable.
- [ ] Metrics must cover settings load failures.
- [ ] Metrics must cover security redaction failures.
- [ ] Metrics must cover encryption and decryption failures without exposing plaintext or key material.
- [ ] Metrics must cover auth validation and authorization failures.
- [ ] Metrics must cover circuit-breaker state transitions and current state.
- [ ] Metrics must cover clock-drift status where available.
- [ ] Metrics must include system-health metrics, not only business alerts.
- [ ] Prometheus-compatible alerts must cover circuit-open state, queue saturation, dead-letter growth, notification failure rate, and clock drift where alerting is implemented.
- [ ] Grafana dashboards must include panels for idempotency cache size, backpressure count, retry count, circuit-breaker state, and clock drift where dashboards are implemented.
- [ ] Metrics labels must be bounded and must not include high-cardinality raw IDs unless explicitly approved.
- [ ] Metrics labels must not include secrets, raw payloads, tokens, API keys, personal data, notification recipients, or approval packet contents.
- [ ] Observability helpers must support no-op operation when Prometheus dependencies are not installed.
- [ ] Missing Prometheus dependencies must fail only when Prometheus-specific export features are used.
- [ ] Grafana dashboard documentation must include panels for system health, tool health, Event Bus health, notification health, error routing, auth failures, and data-quality validation health.
- [ ] Health snapshots must include component status, last error timestamp, last successful event timestamp, degraded status, and critical status where applicable.
- [ ] Health checks should include wall-clock drift monitoring.
- [ ] Clock drift monitoring should detect significant NTP or system-clock offset beyond a configured threshold.
- [ ] Clock drift thresholds must be configurable by environment.
- [ ] Clock drift warnings must be emitted as observability events.
- [ ] Critical clock drift must produce degraded or critical health status depending on threshold.
- [ ] Clock drift diagnostics must include measured offset, threshold, timestamp, source, and component status where available.
- [ ] Clock drift monitoring may be no-op when the runtime environment cannot provide an offset source.
- [ ] Clock drift no-op behavior must be explicit and observable as unsupported or not configured.
- [ ] Circuit breakers must open after a configurable threshold of consecutive failures, timeouts, or provider errors.
- [ ] Open circuits must fail fast without repeatedly consuming threads, sockets, or connection-pool capacity.
- [ ] Circuit breakers must support half-open recovery attempts after a configurable cooldown interval.
- [ ] Circuit breakers must close after successful recovery attempts.
- [ ] Circuit-breaker state transitions must be logged with sanitized metadata.
- [ ] Circuit-breaker state transitions must be exposed through Prometheus-compatible metrics.
- [ ] Circuit-breaker state must be included in component health snapshots.
- [ ] Circuit-breaker failures must not expose credentials, tokens, message bodies, or sensitive payloads.
- [ ] Observability helpers must accept metric names, bounded labels, numeric values, durations, and component health states.
- [ ] Observability helpers must return metric registration or recording status where applicable.
- [ ] Health checks must return healthy, degraded, critical, unsupported, or not-configured status with sanitized details.
- [ ] Clock-drift health failures must return `CLOCK_DRIFT_DETECTED` where the error boundary requires a deterministic code.
- [ ] Metrics labels must not include secrets, tokens, raw payloads, full exception strings, or user-provided arbitrary values.
- [ ] Documentation must include a dashboard review checklist to ensure Grafana panels cover system health, not only trading or business outcomes.
- [ ] Implement `app/utils/observability.py` before production health gates are accepted.
- [ ] Health checks include clock-drift monitoring or explicit no-op status.
- [ ] Optional Prometheus dependencies must be lazy-loaded.
- [ ] Metrics collection must add low overhead.
- [ ] Health checks must be deterministic and fast.
- [ ] Metrics recording failures must not fail the original operation unless explicitly configured to fail closed.
- [ ] Component health checks must distinguish healthy, degraded, critical, unsupported, and not-configured states.
- [ ] Metrics labels must be bounded-cardinality.
- [ ] Metrics must be safe to expose to Prometheus without leaking secrets.
- [ ] Observability helpers must be import-safe without Prometheus dependencies.
- [ ] Logging output must be machine-parseable in production and human-readable enough for local development.
- [ ] Grafana dashboard definitions must be version-controlled if implemented as files.
- [ ] Health checks must distinguish healthy, degraded, and critical states.
- [ ] System-health observability must not be limited to trading or business alerts.
- [ ] Observability export failures must map to `OBSERVABILITY_ERROR` or `CONFIGURATION_ERROR`.
- [ ] Metrics recording failures must not fail the original operation unless explicitly configured to fail closed.
- [ ] Circuit-open failures must be observable through logs and metrics.
- [ ] Sensitive values must be redacted before appearing in Prometheus metrics or Grafana variables.
- [ ] Prometheus metrics must avoid high-cardinality sensitive identifiers.
- [ ] Grafana dashboard variables must not expose secrets.
- [ ] Clock-drift diagnostics must not expose infrastructure secrets.
- [ ] Documentation must describe circuit-breaker metrics and health states.
- [ ] Documentation must describe clock-drift monitoring and environment-specific thresholds.
- [ ] Documentation must describe Prometheus metrics names, labels, and cardinality limits.
- [ ] Documentation must describe Grafana dashboard expectations.
- [ ] Documentation includes production readiness checklists, operational runbooks, dashboard review checklists, and compatibility review notes.
- [ ] Observability must support local/test no-op behavior.
- [ ] Prometheus dependency missing must not break module import.
- [ ] Prometheus exporter unavailable must degrade to no-op metrics or explicit configuration error depending on caller mode.
- [ ] Health check failures must not expose secrets.
- [ ] Clock drift unavailable must be reported as unsupported, not healthy.
- [ ] Clock drift above warning threshold must produce degraded health.
- [ ] Clock drift above critical threshold must produce critical health.
- [ ] Sensitive metric labels must be rejected before metrics emission.
- [ ] Observability tests must cover metrics registration.
- [ ] Observability tests must cover tool-call counters and latency histograms.
- [ ] Observability tests must cover auth failure metrics.
- [ ] Observability tests must cover no-op behavior when Prometheus dependencies are unavailable.
- [ ] Observability tests must use fake Prometheus exporters where exporter behavior must be exercised without external services.
- [ ] Observability tests must reject high-cardinality or sensitive metric labels.
- [ ] Observability tests must verify clock-drift healthy, degraded, critical, unsupported, and not-configured states.
- [ ] Observability tests must verify circuit-breaker metrics.
- [ ] Health-check tests must cover healthy, degraded, critical, unsupported, and not-configured states.
- [ ] Documentation must describe how to run observability in no-op/local/test mode.


### Hardening Amendments

#### Sprint-pack execution boundary

Requirements:

- [ ] Split Phase 1 implementation into approved sprint packs before editing code: 01A package/errors/standard, 01B logging/time/identity/paths, 01C settings/security/auth, 01D event bus/error routing/notifications, 01E observability/metrics, and 01F dataframe/data-quality/validators.
- [ ] Each Phase 1 sprint pack must have its own dry run, approval, tests, rollback plan, and implementation report.
- [ ] Replace any remaining Black, isort, or Flake8 acceptance wording with Ruff format, Ruff check, mypy strict, pytest, coverage, and pre-commit wording.
- [ ] Ensure Utils imports do not depend on contracts that would create circular imports with Phase 1.5.
- [ ] Document which Utils functions are allowed to be used by Core Contracts without importing heavy optional dependencies.

### Unit Tests Required

```text

tests/unit/app/test_package_imports.py

tests/unit/app/utils/test_utils_registry.py

tests/unit/app/utils/test_logger.py

tests/unit/app/utils/test_standard.py

tests/unit/app/utils/test_errors.py

tests/unit/app/utils/test_identity.py

tests/unit/app/utils/test_normalization.py

tests/unit/app/utils/test_paths.py

tests/unit/app/utils/test_dataframe_tools.py

tests/unit/app/utils/test_data_quality.py

tests/unit/app/utils/test_validations.py

tests/unit/app/utils/test_security.py

tests/unit/app/utils/test_settings.py

tests/unit/app/utils/test_auth.py

tests/unit/app/utils/test_event_bus.py

tests/unit/app/utils/test_error_routing.py

tests/unit/app/utils/test_notifications.py

tests/unit/app/utils/test_observability.py

tests/unit/app/utils

```

Test coverage:

- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/01_utils.py

```

Usage examples must show:

- `example_01_logging_and_tracing`: Demonstrate `configure_logging`, logger usage, and trace context propagation.
- `example_02_standard_responses`: Demonstrate standardized success, error, validation, and exception response envelopes.
- `example_03_identities`: Demonstrate request, workflow, correlation, event, idempotency, and custom prefixed IDs.
- `example_04_datetimes_and_normalization`: Demonstrate UTC parsing, formatting, staleness checks, timestamp sequence validation, and execution timing.
- `example_05_security_and_redaction`: Demonstrate payload redaction, password hashing, verification, encryption, and decryption without leaking secrets.
- `example_06_dataframe_and_combinations`: Demonstrate dataframe alignment, record serialization, chunking, and parameter-combination helpers.
- `example_07_data_quality`: Demonstrate OHLCV diagnostics and standard-envelope quality validation for valid and invalid records.
- `example_08_validations`: Demonstrate input/output schema validation, evidence validation, registry validation, and failure envelopes.
- `example_09_event_bus`: Demonstrate event envelope creation, publish/subscribe behavior, idempotency handling, and queue failure behavior.
- `example_10_circuit_breakers_and_observability`: Demonstrate circuit-breaker states, health snapshots, metric recording, and Prometheus text export.
- `example_11_notifications`: Demonstrate fake/local notification routing, throttling, disabled channels, and redacted alert payloads.
- `example_12_paths`: Demonstrate safe path normalization, parent directory creation, traversal rejection, and approved-root checks.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 1,163 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text

feat(utils-foundation): implement core utility modules and safety envelopes



- Setup project logging under `app/utils/logger.py` with structured JSON format

- Implement StandardResponse and ToolMetadata schemas in `app/utils/standard.py`

- Define central domain exceptions and error code maps in `app/utils/errors.py`

- Create trace-identity, path-traversal validation, and datetime parsing utilities

- Implement Event Bus, fake notification channels, and Prometheus exporter

```
