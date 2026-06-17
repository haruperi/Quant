# HaruQuantAI Implementation Plan

**Purpose:** Provide the standalone phased Builder implementation plan for HaruQuantAI.

Each phase is a standalone implementation phase. A task is any unchecked Markdown checkbox in this file.

**Execution rule:** This document is a plan, not approval to implement all phases at once. Each phase still requires the repository approval workflow and a dry run before edits.

## Task Inventory

| Phase | Area | Target area | Tasks | Checked | Unchecked |
|---:|---|---|---:|---:|---:|
| 1 | Utils Foundation | `app/utils/` | 1,163 | 0 | 1,163 |
| 2 | Data Foundation | `app/services/data/` | 701 | 0 | 701 |
| 3 | Indicator Library | `app/services/indicators/` | 737 | 0 | 737 |
| 4 | Strategy Service | `app/services/strategies/` | 457 | 0 | 457 |
| 5 | Risk Governance | `app/services/risk/` | 678 | 0 | 678 |
| 6 | Analytics Service | `app/services/analytics/` | 460 | 0 | 460 |
| 7 | Trading Service | `app/services/trader/` | 84 | 0 | 84 |
| 8 | Simulation Engine | `app/services/simulation/` | 1,662 | 0 | 1,662 |
| 9 | Optimization Service | `app/services/optimization/` | 278 | 0 | 278 |
| 10 | Live Runtime | `app/services/live/` | 234 | 0 | 234 |
| 11 | UI and API Gateway | `api/ and ui/` | 365 | 0 | 365 |
| 12 | Research Edge Lab | `app/services/research/` | 290 | 0 | 290 |
| 13 | Conversation AI Layer | `app/services/conversation/` | 249 | 0 | 249 |
| **Total** |  |  | **7,358** | **0** | **7,358** |

## Global Builder Rules

- Done criterion: Read `AGENTS.md`, `docs/ARCHITECTURE.md`, `CHANGELOG.md`, this implementation plan and relevant existing code/tests before planning or editing.
- Done criterion: Perform a dry run before edits: files read/changed, commands/tests planned, scope boundaries, blockers/risks, and rollback path.
- Done criterion: Wait for `APPROVED: EXECUTE` before modifying files.
- Done criterion: Implement one approved scope at a time; do not use this plan as blanket approval for broad refactors.
- Done criterion: Preserve module ownership boundaries and fail-closed safety behavior.
- Done criterion: Update active docs and `CHANGELOG.md` whenever project meaning changes.
- Done criterion: Run validation in the required order: pre-commit hooks, Ruff, Ruff format, mypy strict, and pytest as applicable.

## Recommended Dependency Order

```text
01 Utils -> 02 Data -> 03 Indicators -> 04 Strategies -> 05 Risk
05 Risk -> 07 Trading -> 08 Simulation -> 06 Analytics -> 09 Optimization
09 Optimization -> 10 Live -> 11 UI/API -> 12 Research -> 13 Conversation
```

## Phase 1 Utils Foundation

### Goal

Implement the Utils Foundation requirements under `app/utils/` while preserving the phase module boundaries and governance rules.

Task inventory: 1,163 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/utils/`.
- Trading strategy logic.
- Broker execution logic or live account mutation.
- Risk-governor decisions, portfolio allocation decisions, strategy promotion, or live activation approvals.
- Application orchestration, UI behavior, database repositories, broker SDK ownership, or backtest engines.
- External identity-provider token validation unless an explicit application-layer adapter is supplied.

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
app/utils/schema_validation.py
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
- [ ] The implementation must be compatible with Black, isort, Flake8, mypy, pytest, and coverage.
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
- [ ] CI must pass Black, isort, Flake8, mypy, pytest, and the coverage gate.
- [ ] Implement unit tests for every module.
- [ ] Unit tests exist for every module.
- [ ] Official tools have metadata tests.
- [ ] Edge case tests exist.
- [ ] Coverage is at least 80%.
- [ ] Black passes.
- [ ] isort passes.
- [ ] Flake8 passes.
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

#### `app/utils/schema_validation.py`

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
- [ ] Implement `app/utils/schema_validation.py` after standard, errors, normalization, security, auth, and observability foundations.
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
tests/unit/app/utils/test_schema_validation.py
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
- `example_08_schema_validation`: Demonstrate input/output schema validation, evidence validation, registry validation, and failure envelopes.
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
feat(utils-foundation): implement phase 1 utils foundation requirements
```

## Phase 2 Data Foundation

### Goal

Implement the Data Foundation requirements under `app/services/data/` while preserving the phase module boundaries and governance rules.

Task inventory: 701 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/data/`.
- Requires Phase 1 Utils Foundation contracts to be available where referenced by `02-data.md`.
- The data module remains a clean, greenfield rebuild.
- Data is a thin domain layer over `app.utils`; it must not duplicate shared utility primitives.
- Phase 1 keeps public streaming subscription tools out of scope while retaining internal feed support and feed status inspection.
- SQLite is the default single-node persistence backend, while the persistence abstraction remains TSDB-ready.
- Local and synthetic sources can be production-ready first; external/broker sources remain staging until evidence promotes them.

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
app/services/data/validation.py
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
- [ ] CI gates shall pass before production sign-off: `black`, `isort`, `flake8`, `mypy`, `pytest`, and coverage above 80%.
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

#### `app/services/data/errors.py`

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

#### `app/services/data/validation.py`

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
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(data-foundation): implement phase 2 data foundation requirements
```

## Phase 3 Indicator Library

### Goal

Implement the Indicator Library requirements under `app/services/indicators/` while preserving the phase module boundaries and governance rules.

Task inventory: 737 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/indicators/`.
- Requires Phase 2 Data Foundation contracts to be available where referenced by `03-indicator.md`.

### Files to Create

```text
app/__init__.py
app/services/indicators/__init__.py
app/services/indicators/registry.py
app/services/indicators/protocols.py
app/services/indicators/errors.py
app/services/indicators/calculations.py
app/services/indicators/batch/__init__.py
app/services/indicators/batch/trend.py
app/services/indicators/batch/volatility.py
app/services/indicators/batch/momentum.py
app/services/indicators/incremental/__init__.py
app/services/indicators/incremental/state.py
app/services/indicators/incremental/accumulators.py
app/services/indicators/adapters/__init__.py
app/services/indicators/adapters/cache.py
app/services/indicators/adapters/audit.py
app/services/indicators/
app/services/simulation/
app/utils/errors.py
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/indicators/README.md`

Functions/classes:
- No runtime functions/classes; documentation artifact only.

Requirements:
- [ ] Documentation shall warn against using unshifted current-bar values for bar-open decisions.
- [ ] Promotion of custom indicators to official status shall require documentation, golden fixtures, conformance tests, no-lookahead tests, determinism tests, and benchmark coverage.
- [ ] Documentation shall include the Production Scope Tiers classification for every requirement before implementation begins.
- [ ] Documentation shall describe no-lookahead behavior for indicator-derived signals.
- [ ] Documentation shall describe multi-timeframe indicator alignment.
- [ ] Documentation shall describe output column naming, default source naming, non-default source naming, multi-output naming, custom output names, output column conflict policy, and generated `output_columns`.
- [ ] Documentation shall describe debug-mode strict typing and runtime validation behavior.
- [ ] Documentation shall describe golden fixtures and reference output approval workflow.
- [ ] Documentation shall describe the `available_at` contract, `label_time`, `bar_open_time`, `bar_close_time`, `computed_from_start`, `computed_from_end`, and strategy-facing filtering.
- [ ] Documentation shall describe custom indicator conformance, status values, prohibited operations, dependency declarations, and promotion review.
- [ ] Documentation shall describe mandatory cross-validation against industry-standard libraries, third-party formula convention differences, golden fixture approval, mutation fuzz testing, and survivorship bias testing.
- [ ] Public usage examples shall be executable documentation examples once implementation begins.

#### `app/__init__.py`

Functions/classes:
- `IndicatorProtocol`

Requirements:
- [ ] Every smoothed indicator shall define smoothing method, alpha convention, and initial seed behavior.
- [ ] Documentation shall describe numeric dtype policy, NaN, infinity, negative zero, overflow, underflow, divide-by-zero, and floating-point tolerance behavior.
- [ ] `IndicatorProtocol.calculate(data, config, context)` shall use approved type hints before implementation begins.
- [ ] `data` shall be a `pandas.DataFrame` for Core MVP batch execution unless a formula table explicitly approves an alternate typed input.
- [ ] Core MVP `data` shall contain UTC-normalized timestamp information as either a UTC `DatetimeIndex` for single-symbol input or a `MultiIndex` containing `symbol` and UTC `timestamp` levels for multi-symbol input.
- [ ] Core MVP `data` shall expose required OHLCV columns through stable lowercase column names and shall reject ambiguous duplicate columns.
- [ ] `IndicatorResult.values` shall be a `pandas.DataFrame` aligned to the accepted input timestamp/symbol keys and containing generated indicator columns plus required availability and quality metadata.
- [ ] `IndicatorConfig` and `IndicatorContext` shall be typed as dataclasses, `TypedDict`, Pydantic models, or equivalent approved Python contracts before Builder handoff.
- [ ] Any future array-native input such as `numpy.ndarray` shall be an Optional Extension with explicit schema, shape, dtype, symbol/timestamp alignment, and conversion rules.
- [ ] No file-specific non-functional requirements defined.
- [ ] Numeric tests shall cover dtype preservation, NaN, infinity, negative zero, overflow, underflow, divide-by-zero, absolute tolerance, and relative tolerance.
- [ ] Numeric tests shall verify NaN propagation, infinity rejection in official workflows, division-by-zero unavailable outputs, negative-zero normalization, and overflow/underflow deterministic handling.
- [ ] Property-based mutation fuzz tests shall inject NaN, infinity, extreme outliers, zero volume, flat prices, negative values, malformed timestamps, duplicate timestamps, and random missing intervals.
#### `app/services/indicators/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/indicators/registry.py`

Functions/classes:
- `register_indicator(...)`
- `get_indicator(...)`
- `list_indicators(...)`
- `validate_indicator(...)`
- `unregister_indicator(...)`
- `register_indicator()`
- `get_indicator()`
- `list_indicators()`
- `validate_indicator()`
- `unregister_indicator()`
- `IndicatorResult`

Requirements:
- [ ] The module shall provide an indicator registry for approved indicator implementations.
- [ ] Registered indicators shall declare id, name, version, parameter schema, input schema, output schema, warmup policy, and deterministic behavior.
- [ ] Custom indicators shall be registered through approved extension points before use in official workflows.
- [ ] Custom indicator registration shall not bypass input validation, no-lookahead metadata, schema validation, or deterministic replay requirements.
- [ ] Public APIs shall include stable import paths, function and class signatures, parameter schemas, result schemas, error schemas, and registry contracts.
- [ ] The deprecation phase for each indicator, parameter, schema, or API shall be machine-readable through the registry.
- [ ] The public package shall expose registry operations for `register_indicator(...)`, `get_indicator(...)`, `list_indicators(...)`, `validate_indicator(...)`, and `unregister_indicator(...)` where unregistering is allowed outside official production registries.
- [ ] Convenience functions shall return `IndicatorResult` and shall use the same validation, naming, manifest, cache, availability, and no-lookahead rules as registry-driven execution.
- [ ] Public module layout shall separate core protocols, result types, registry code, built-in indicator implementations, error definitions, and test fixtures.
- [ ] Documentation shall declare the public API surface, stable import paths, `typing.Protocol` contracts, registry contracts, schema versions, and deprecation policy.
- [ ] Documentation shall describe indicator anatomy, required public types, required protocol attributes, required protocol methods, registry operations, built-in convenience functions, result objects, manifests, and state objects.
- [ ] Documentation shall describe the deprecation lifecycle, machine-readable registry phase, changelog entries, migration guide, and `IND_DEPRECATED`.
- [ ] Indicator anatomy, required interfaces, registry operations, built-in convenience functions, and result object methods are documented and tested.
- [ ] The public API contract table shall cover registry operations, built-in convenience functions, result object methods, protocol methods, state serialization functions, and manifest serialization functions.
- [ ] The machine-readable capability matrix shall be generated from the registry and shall include indicator id, version, tier, supported modes, optional dependencies, unsupported-mode error codes, and official-workflow eligibility.
- [ ] No file-specific non-functional requirements defined.
- [ ] Registry API tests shall verify `register_indicator`, `get_indicator`, `list_indicators`, `validate_indicator`, and allowed `unregister_indicator` behavior.
- [ ] Built-in convenience function tests shall verify `ema`, `sma`, `adx`, `atr`, `adr`, `rolling_volatility`, `rsi`, and `williams_r` return `IndicatorResult` and follow the same validation, naming, manifest, cache, availability, and no-lookahead rules as registry execution.
- [ ] Deprecation lifecycle tests shall verify deprecation warning phase, deprecation error with opt-in phase, removal phase, registry machine-readable phase, `IND_DEPRECATED`, and migration-guide coverage.
- [ ] Capability-matrix tests shall verify every built-in indicator against its machine-readable capability matrix.
- [ ] Custom indicator conformance suite passes for every registered custom indicator.
- [ ] Every official indicator shall publish a machine-readable capability matrix covering batch, vectorized, incremental, streaming, out-of-core, acceleration, composition, multi-symbol, and multi-timeframe support.
#### `app/services/indicators/protocols.py`

Functions/classes:
- `IndicatorProtocol`
- `IndicatorConfig`
- `IndicatorContext`
- `IndicatorResult`
- `IndicatorState`
- `IndicatorManifest`
- `IndicatorMetadata`
- `WarmupPolicy`
- `PrecisionPolicy`
- `IndicatorDependency`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] The module shall be packageable through standard Python packaging metadata.
- [ ] Build-system and project metadata shall be declared in `pyproject.toml`.
- [ ] Logs shall include indicator id, implementation version, parameter hash, input checksum, symbol count, timeframe, and request id when available.
- [ ] Canary execution shall allow a configured subset of actors, workflows, symbols, or requests to receive a new implementation while comparing outputs against the baseline implementation.
- [ ] Distributed tracing, feature-flagged execution, canary routing, SLO alert routing, and rollback metadata shall be classified as Optional Extension unless a later approved decision promotes them.
- [ ] Indicator requests shall support configurable maximum rows, maximum symbols, maximum columns, memory budget, and execution timeout.
- [ ] Resource-limit defaults shall live in an approved configuration schema before Builder handoff and shall be overrideable only through validated configuration.
- [ ] Unless an indicator formula specification explicitly overrides this policy, NaN input values shall propagate to NaN outputs for affected rows or windows and shall be represented as unavailable values with quality metadata.
- [ ] Unless an indicator formula specification explicitly overrides this policy, division by zero shall produce NaN unavailable outputs with deterministic warning metadata rather than silently clipping or filling values.
- [ ] Production non-transient indicator error rate shall target less than 0.1 percent over the configured measurement window, excluding deterministic user input validation failures.
- [ ] Production indicator timeout rate shall target less than 0.05 percent over the configured measurement window.
- [ ] SLO thresholds, measurement windows, included workflows, excluded error categories, and alert routing shall be configurable.
- [ ] Indicator outputs shall be treated as decision inputs only; official execution remains owned by `app/services/simulation/`.
- [ ] Indicator implementations shall define required input columns, output column names, parameter schema, warmup length, and missing-data behavior.
- [ ] Indicators shall accept OHLCV inputs with explicit timestamp, symbol, timeframe, and timezone metadata.
- [ ] Indicators shall support multi-symbol input only when output grouping preserves symbol identity.
- [ ] Indicators shall preserve input row order after deterministic timestamp and symbol validation.
- [ ] Indicator outputs shall include timestamp and symbol alignment metadata.
- [ ] Indicator outputs shall expose warmup or unavailable regions explicitly rather than silently filling values.
- [ ] Indicator outputs shall distinguish computed values, warmup nulls, missing-input nulls, and rejected rows.
- [ ] Indicator outputs used by official backtests shall be serializable in the precision policy required by the downstream workflow.
- [ ] Indicator calculation shall not mutate the input dataframe by default.
- [ ] Official workflows shall treat in-place input mutation as prohibited unless an explicitly configured internal optimization proves copy-equivalent output and records the optimization in the manifest.
- [ ] The default batch result shall be an `IndicatorResult` containing an aligned `values` dataframe with timestamp, symbol, generated indicator columns, availability metadata, and quality metadata.
- [ ] The result object shall expose a `join_to(input_data, mode="copy")` helper that returns a copy of the source dataframe with generated indicator columns appended.
- [ ] Output column collisions with existing input columns shall fail with a deterministic error by default.
- [ ] Explicit overwrite, suffix, prefix, or namespace behavior for output column collisions shall require configuration and shall be recorded in the manifest.
- [ ] Joined output shall preserve original input columns, row count, row ordering, timestamp alignment, symbol grouping, and index policy.
- [ ] Warmup and unavailable rows shall remain present in joined output with nullable indicator values and explicit metadata rather than being dropped.
- [ ] Vectorized output alignment shall be verified by timestamp and symbol keys rather than by positional row number alone when the input dataframe has an external index.
- [ ] The same indicator input data, parameter set, implementation version, and precision policy shall produce the same output.
- [ ] Indicator implementations shall define numeric precision behavior.
- [ ] Indicator result manifests shall include input data checksum, parameter hash, implementation version, output schema version, and calculation timestamp.
- [ ] Chunked indicator output shall match full-run output within the documented precision policy.
- [ ] Performance benchmarks shall define warmup iterations before measurement.
- [ ] Out-of-core outputs shall match in-memory full-run outputs within the documented precision policy.
- [ ] Accelerated and fallback paths shall produce outputs that match within the documented precision policy and shall record backend metadata in the result manifest.
- [ ] Public indicator interfaces shall use `typing.Protocol` or equivalent structural typing contracts so custom indicators can integrate without inheriting from framework base classes.
- [ ] Indicator result objects shall implement rich notebook inspection methods, including `_repr_html_` and `_repr_pretty_`, with summary statistics, warmup visualization, unavailable-region visibility, and manifest summary.
- [ ] `IndicatorProtocol` shall define required attributes for `indicator_id`, `name`, `version`, `formula_version`, `input_schema`, `parameter_schema`, `output_schema`, `warmup_policy`, `capabilities`, and `status`.
- [ ] `IndicatorProtocol` shall define `validate_parameters(parameters)`.
- [ ] `IndicatorProtocol` shall define `required_columns(parameters)`.
- [ ] `IndicatorProtocol` shall define `output_columns(parameters, source=None, naming_policy=None)`.
- [ ] `IndicatorProtocol` shall define `warmup_requirement(parameters, timeframe, calendar=None)`.
- [ ] `IndicatorProtocol` shall define `validate_input(data, config, context)`.
- [ ] `IndicatorProtocol` shall define `calculate(data, config, context)`.
- [ ] `IndicatorProtocol` shall define `calculate_vectorized(data, config, context)` when the indicator supports vectorized batch execution separately from generic calculation.
- [ ] `IndicatorContext` shall contain request id, correlation id, actor, workflow, environment, entitlement context, tracing context, observability context, and SLO context where applicable.
- [ ] Every built-in indicator shall define default parameters, allowed parameter ranges, default source columns, required input columns, warmup length, output columns, null behavior, and degenerate-window behavior.
- [ ] Indicator formulas shall be documented with enough precision that an independent implementation can reproduce the same output.
- [ ] Each official built-in indicator shall include a formula specification table defining indicator id, required columns, default source column, parameters, default parameter values, valid parameter ranges, formula, smoothing convention, seed behavior, warmup length, window inclusivity, null handling, degenerate-window behavior, output columns, and precision tolerance.
- [ ] Any formula, seed, warmup, tolerance, or default-parameter change shall require an implementation version update, golden fixture review, and documented migration or changelog note.
- [ ] Indicator output rows shall include `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable.
- [ ] Higher-timeframe indicator values shall set `available_at` no earlier than the close of the higher-timeframe source bar plus configured data latency.
- [ ] If a strategy-facing consumer attempts to read a value with `available_at > decision_time`, the retrieval shall raise `IND_LOOKAHEAD_RISK` or return a masked/unavailable result according to the configured error mode.
- [ ] Local time or exchange time conversion shall occur only at input, output, display, or external integration boundaries.
- [ ] Historical indicator calculation shall not depend on host timezone database changes after inputs are normalized to UTC.
- [ ] Indicator inputs shall declare price adjustment status: raw, split-adjusted, dividend-adjusted, total-return-adjusted, back-adjusted, or synthetic.
- [ ] Indicator inputs shall declare price source: trade, bid, ask, mid, mark, settlement, or vendor-derived.
- [ ] Indicator inputs shall declare venue, exchange, data vendor, symbol normalization version, and corporate-action adjustment version when available.
- [ ] Indicator manifests shall include data provenance fields required to reproduce the calculation.
- [ ] Official workflows shall reject inputs with unknown adjustment status unless explicitly configured to allow them.
- [ ] Official workflows shall reject bars affected by intra-bar corporate-action adjustments unless a deterministic intra-bar adjustment policy is configured before calculation.
- [ ] Official workflows shall reject stub quotes or spreads greater than the configured threshold, with a default rejection threshold of 50 percent of mid price, unless an explicit fallback policy is configured.
- [ ] Mid-price indicators shall deterministically reject missing or inverted bid/ask inputs unless configured to fall back to last valid mid, trade price, mark price, or unavailable output.
- [ ] Incremental updates shall be idempotent for the same input bar.
- [ ] Incremental and batch outputs shall match within the documented precision policy.
- [ ] Indicator functions shall validate all inputs at call time before any calculation begins.
- [ ] The module shall support indicator composition where one indicator output serves as another indicator input.
- [ ] Composed indicator chains shall preserve provenance metadata through the chain.
- [ ] Indicator inputs may include per-row data quality flags from the data module.
- [ ] Configured inclusion of flagged rows shall be recorded in the indicator manifest.
- [ ] Indicator output rows derived from flagged inputs shall propagate the highest-severity quality flag present in the source data for that calculation window.
- [ ] Strategy-facing outputs shall expose quality metadata so strategies can require a minimum data quality level for consumption.
- [ ] The indicator module shall define a protocol to request minimum required warmup data from the data module before calculation.
- [ ] Warmup requests shall include requested symbol, timeframe, and lookback period.
- [ ] Warmup requests shall include indicator id and parameter set to determine exact warmup length.
- [ ] Warmup requests shall declare whether warmup data must be closed-bar only or may include the current incomplete bar.
- [ ] The indicator module shall request warmup data through the data module contract and shall validate that returned warmup data conforms to the same schema and provenance requirements as the primary input before using it.
- [ ] When an indicator is configured with a higher-timeframe source, the module shall request higher-timeframe bars through the data module contract alongside the primary timeframe.
- [ ] Higher-timeframe indicator values may be forward-filled onto the primary timeframe only after the higher-timeframe source bar is fully closed plus configured data latency.
- [ ] The module shall set `available_at` for each primary-timeframe row to the higher-timeframe bar close time plus configured data latency.
- [ ] Weekend and holiday gaps in higher-timeframe data shall not cause forward-fill of stale values across session boundaries unless explicitly configured.
- [ ] Proprietary indicator result manifests shall record non-sensitive access-control decision metadata, including decision id, entitlement policy version, and authorized workflow.
- [ ] Symbol metadata.
- [ ] Timeframe metadata.
- [ ] Output mode: values-only result, joined copy result, or explicitly configured internal optimization.
- [ ] Precision policy.
- [ ] Timezone metadata with unambiguous timestamp handling.
- [ ] Optional microstructure quality policy containing stub quote, inverted market, missing bid/ask, spread threshold, and mid-price fallback configuration.
- [ ] Data latency configuration for availability-time calculation.
- [ ] Optional out-of-core processing configuration containing memory budget, chunk size, storage backend, and spill directory.
- [ ] Optional acceleration backend configuration containing backend id, feature flag, worker pool, worker count, and fallback policy.
- [ ] Optional feature flag and canary routing configuration for indicator implementation rollout.
- [ ] Optional proprietary indicator access context containing actor, workflow, entitlement, environment, and intended use.
- [ ] Optional warmup data request configuration.
- [ ] Resource limit configuration.
- [ ] Optional observability context containing request id and correlation id.
- [ ] Optional tracing context containing trace id, parent span id, baggage, and sampling decision.
- [ ] Indicator values dataframe containing timestamp, symbol, indicator columns, availability metadata, and quality metadata.
- [ ] Original input dataframe preserved without default mutation.
- [ ] `available_at` timestamp or deterministic availability metadata for every output row.
- [ ] `label_time`, `bar_open_time`, `bar_close_time`, `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable.
- [ ] Warmup and missing-data metadata.
- [ ] Indicator result manifest.
- [ ] Input checksum.
- [ ] Dtype metadata.
- [ ] Data provenance metadata required to reproduce the calculation.
- [ ] Out-of-core execution metadata when out-of-core processing is enabled.
- [ ] Acceleration backend metadata when an accelerated or fallback backend is used.
- [ ] Feature flag, canary route, baseline implementation, selected implementation, and canary comparison metadata when rollout controls are enabled.
- [ ] Non-sensitive proprietary access-control decision metadata when proprietary indicator execution is requested.
- [ ] Propagated data quality metadata.
- [ ] Every indicator result shall include a machine-readable manifest as a standalone serializable object.
- [ ] The manifest shall include `manifest_version`.
- [ ] The manifest shall include `indicator_id`.
- [ ] The manifest shall include `indicator_version`.
- [ ] The manifest shall include `formula_version`.
- [ ] The manifest shall include `output_schema_version`.
- [ ] The manifest shall include `parameter_hash` derived from a canonical parameter representation.
- [ ] The manifest shall include `input_checksum` derived from input data including timestamps, symbols, and OHLCV values in canonical order.
- [ ] The manifest shall include `output_checksum`.
- [ ] The module shall define the exact input and output checksum policy, including included columns, dtype normalization, timestamp normalization, symbol ordering, row ordering, float handling, null representation, precision policy, and excluded metadata.
- [ ] The manifest shall include `data_provenance` with adjustment status, price source, vendor, venue, symbol normalization version, corporate-action version, and continuous contract roll method when applicable.
- [ ] The manifest shall include `output_contract` with generated column names, source column, output mode, naming policy, column conflict policy, join mode, input mutation flag, and index alignment policy.
- [ ] The manifest shall include `execution_backend` with in-memory, out-of-core, accelerated, fallback, parallelism, worker count, and backend version fields where applicable.
- [ ] The manifest shall include `rollout` with feature flag, canary route, selected implementation, baseline implementation, and tolerance status where applicable.
- [ ] The manifest shall include `access_control` with non-sensitive decision metadata for proprietary indicator requests where applicable.
- [ ] The manifest shall include `timing` with calculation start, calculation end, and wall-clock duration.
- [ ] The manifest shall include `output_shape` with row count, symbol count, column list, and dtypes.
- [ ] The manifest shall include `environment` with Python version, key dependency versions, operating system, and optional host identifier for debugging.
- [ ] The manifest shall include composition lineage when the result depends on upstream indicator outputs.
- [ ] The manifest shall include quality-flag policy and propagated quality summary when data quality flags are present.
- [ ] Every invalid input schema shall return a deterministic error code.
- [ ] Unexpected input mutation during official calculation shall return a deterministic error code.
- [ ] Every insufficient-data condition shall return a deterministic error code or explicit unavailable output according to configuration.
- [ ] Lookahead-sensitive indicator access shall provide metadata required for `SIM_LOOKAHEAD_DETECTED`.
- [ ] Intra-bar corporate-action adjustment inputs without a configured deterministic policy shall return a deterministic error code.
- [ ] Stub quotes, inverted markets, missing bid or ask values, and spread-threshold violations shall return deterministic error codes unless an explicit fallback policy is configured.
- [ ] Deprecated indicator, parameter, schema, or API use in the deprecation error phase shall return a deterministic error code unless an explicit opt-in flag is configured.
- [ ] `IND_INVALID_CONFIG`
- [ ] `IND_INVALID_INPUT_SCHEMA`
- [ ] `IND_INPUT_MUTATION_DETECTED`
- [ ] Input validation tests shall cover missing columns, duplicate timestamps, non-monotonic timestamps, invalid OHLC, empty data, insufficient warmup, and invalid parameters.
- [ ] Input validation tests shall cover malformed config payloads and invalid configuration combinations, including valid parameters that are incompatible when combined.
- [ ] Input validation tests shall verify simultaneous conflicting options, such as `values_only=True` with `output_mode="join"`, fail with `IND_INVALID_CONFIG`.
- [ ] Public API tests shall verify `typing.Protocol` compatibility for custom indicators that do not inherit from framework base classes.
- [ ] Notebook representation tests shall verify indicator result `_repr_html_` and `_repr_pretty_` output includes summary statistics, warmup visualization, unavailable-region visibility, and manifest summary without exposing full market data payloads.
- [ ] Join helper tests shall verify `IndicatorResult.join_to(input_data, mode="copy")` appends generated indicator columns while preserving original columns, row count, row order, timestamp alignment, symbol grouping, index policy, warmup rows, and unavailable rows.
- [ ] Availability tests shall verify higher-timeframe values are unavailable until the higher-timeframe source bar is fully closed plus configured latency.
- [ ] Timezone database tests shall verify historical outputs remain stable after UTC-normalized inputs are supplied and that timezone-database-dependent conversions occur only at I/O boundaries.
- [ ] Determinism tests shall verify identical inputs and parameters produce identical outputs and manifests.
- [ ] Chunking tests shall verify chunked output matches full-run output within documented precision policy.
- [ ] Out-of-core tests shall verify datasets exceeding memory budget produce the same output as full in-memory runs within documented precision policy.
- [ ] Out-of-core tests shall verify deterministic rejection for indicators that require full in-memory context and cannot be safely chunked.
- [ ] Acceleration backend tests shall verify feature-flag isolation, fallback behavior, backend metadata, and parity between accelerated and fallback paths within documented precision policy.
- [ ] Batch and incremental tests shall verify incremental output matches batch output within the documented precision policy.
- [ ] Market data quality tests shall verify default exclusion of flagged rows, explicit inclusion configuration, quality-flag propagation, highest-severity quality summarization, and strategy-facing quality metadata.
- [ ] Manifest tests shall verify every required manifest field, nested data provenance, calculation config, timing, output shape, environment, composition lineage, and quality summary.
- [ ] Manifest tests shall verify output contract fields for generated column names, source column, output mode, naming policy, column conflict policy, join mode, input mutation flag, and index alignment policy.
- [ ] Manifest tests shall verify parameter hash canonicalization and input/output checksum policies are stable and documented.
- [ ] Provenance tests shall cover raw, split-adjusted, dividend-adjusted, total-return-adjusted, back-adjusted, synthetic, bid, ask, mid, mark, settlement, vendor-derived, continuous futures, and unknown adjustment status inputs.
- [ ] Microstructure tests shall cover stub quotes, inverted markets, missing bid or ask values, spreads above the configured threshold, and mid-price fallback policies.
- [ ] Survivorship bias tests shall verify indicators do not silently produce misleading signals for delisted, bankrupt, merged, or inactive symbols without data-quality flags and provenance metadata.
- [ ] Observability tests shall verify metrics, logs, traces, canary comparison metadata, and SLO measurement fields include required fields and do not change calculation semantics.
- [ ] Feature flag and canary tests shall verify routed execution, baseline comparison, output delta recording, tolerance status, rollback metadata, and unchanged official outputs when canary route is not selected.
- [ ] Warmup protocol tests shall verify requested symbol, timeframe, lookback, indicator id, parameter set, closed-bar policy, returned provenance, data-module contract integration through a fake data-module provider, and warmup output marking.
- [ ] Proprietary indicator tests shall verify entitlement context and protected-package metadata do not leak secrets into logs, traces, manifests, or error messages.
- [ ] Property-based tests shall cover valid and invalid OHLCV inputs.
- [ ] Property-based tests shall verify SMA over constant price input equals the constant price after warmup.
- [ ] Property-based tests shall verify EMA over constant price input converges deterministically according to its seed policy.
- [ ] Property-based tests shall verify RSI remains within documented bounds for valid inputs.
- [ ] Property-based tests shall verify ATR is non-negative for valid OHLC inputs.
- [ ] Documentation tests shall execute usage examples, invalid-input examples, manifest-inspection examples, multi-symbol examples, multi-timeframe examples, and incremental examples where supported.
- [ ] Usage examples shall include normal output, invalid parameter handling, missing-column handling, manifest inspection, availability filtering, multi-symbol input, multi-timeframe input, and incremental update behavior where supported.
- [ ] Documentation shall include a configuration reference for every supported indicator.
- [ ] Documentation shall include input schema, output schema, parameter schema, warmup policy, and missing-data behavior for every supported indicator.
- [ ] Documentation shall describe vectorized calculation requirements, values-only output, joined-copy output, default input immutability, official in-place mutation restrictions, and internal optimization manifest requirements.
- [ ] Documentation shall describe notebook result representations, including `_repr_html_`, `_repr_pretty_`, summary statistics, warmup visualization, unavailable-region visibility, and manifest summaries.
- [ ] Documentation shall describe optional acceleration backends, feature flags, pure fallback behavior, backend metadata, GIL-release behavior, and parallel symbol execution configuration.
- [ ] Documentation shall describe input validation timing and fail-fast behavior.
- [ ] Documentation shall describe indicator result manifest structure and every required manifest field.
- [ ] Documentation shall describe data quality flags, default exclusion policy, explicit inclusion policy, output quality propagation, and strategy-facing quality metadata.
- [ ] Documentation shall describe warmup data request protocol and warmup output marking.
- [ ] Documentation shall describe observability metrics, log fields, request ids, correlation ids, distributed tracing, OpenTelemetry-compatible propagation, feature flags, canary routing, output delta comparison, and rollback metadata.
- [ ] Documentation shall describe packaging metadata, `pyproject.toml`, dependency categories, `py.typed`, and typed package behavior.
- [ ] Documentation shall describe proprietary indicator access control, entitlement checks, authorized workflows, non-sensitive manifest metadata, source protection, and protected-package determinism.
- [ ] `typing.Protocol` contracts and notebook result representations are implemented and tested.
- [ ] `ema(data, period=10, source="close")` produces `ema_10`, and `IndicatorResult.join_to(data)` appends `ema_10` to a copied dataframe without mutating the input by default.
- [ ] `pyproject.toml` metadata is present and valid.
- [ ] Availability-time metadata is implemented and tested.
- [ ] Acceleration backend parity, feature flag, fallback, and backend metadata tests pass.
- [ ] Performance benchmark metadata and regression gate are implemented.
- [ ] Machine-readable manifest structure is implemented and tested.
- [ ] Manifest output-contract fields are implemented and tested.
- [ ] Warmup data request protocol is documented and tested.
- [ ] Multi-timeframe alignment protocol is documented and tested.
- [ ] Official Backtest Required shall include no-lookahead alignment, reproducible fixtures, manifest/checksum behavior, data-quality propagation, and strategy/simulation integration contracts.
- [ ] Rich notebook HTML representations may be added after stable result and manifest schemas exist.
#### `app/services/indicators/errors.py`

Functions/classes:
- `IndicatorResult(errors=...)`
- `IndicatorResult`

Requirements:
- [ ] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom indicator exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.
- [ ] Indicator implementations shall return deterministic errors for invalid input schema, invalid parameter values, insufficient data, non-monotonic timestamps, duplicate timestamps, or impossible OHLCV values.
- [ ] The module shall provide metadata required for downstream layers to raise their own lookahead errors while keeping simulation-layer errors outside indicator ownership.
- [ ] Out-of-core processing shall expose deterministic errors when an indicator requires full in-memory context and cannot be safely chunked.
- [ ] Type mismatch failures in debug mode shall fail fast with deterministic errors before any output, state mutation, cache read, or cache write occurs.
- [ ] `IndicatorResult` shall contain `values`, `output_columns`, `manifest`, `availability`, `quality`, `state`, `errors`, `metrics`, and `join_to(...)`.
- [ ] Division-by-zero, all-null windows, constant-price windows, zero-volume windows, flat-market windows, NaN inputs, infinite values, overflow, underflow, and negative zero shall produce deterministic outputs or deterministic errors.
- [ ] Composition shall reject cycles, missing upstream outputs, incompatible source timeframes, unavailable upstream values, and output column collisions with deterministic errors before calculation.
- [ ] The module shall document whether deterministic errors are raised as exceptions, returned inside `IndicatorResult.errors`, or both, and shall document the default mode.
- [ ] Indicator errors shall be safe, deterministic, and machine-readable.
- [ ] Requests exceeding configured resource limits shall fail with deterministic machine-readable errors.
- [ ] Missing optional acceleration, proprietary, tracing, or audit dependencies shall produce deterministic unsupported-backend or not-configured errors without changing default built-in indicator semantics.
- [ ] Unless an indicator formula specification explicitly overrides this policy, positive and negative infinity inputs shall be rejected with deterministic numeric errors in official workflows before calculation.
- [ ] Overflow and underflow shall return deterministic errors or unavailable outputs according to the indicator formula specification and shall be recorded in result errors or warning metadata.
- [ ] Core MVP shall include deterministic batch calculation for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R; input validation; output naming; no-lookahead availability metadata; manifests; deterministic errors; and golden tests.
- [ ] Public contracts shall define whether invalid requests raise exceptions, return `IndicatorResult(errors=...)`, or support both modes, and shall document the default mode.
- [ ] Unsupported modes, unsupported backends, unsupported indicators, unavailable optional dependencies, and unsupported composition requests shall fail before calculation with deterministic errors.
- [ ] No file-specific non-functional requirements defined.
- [ ] Error-mode tests shall verify deterministic exception mode and deterministic `IndicatorResult.errors` mode if both are supported.
- [ ] Error-mode tests shall verify that result-error mode does not raise exceptions and instead populates `IndicatorResult.errors` with deterministic codes.
- [ ] Output contract tests shall verify custom output names, invalid output names, output naming policies, output modes, column conflict policies, and deterministic collision errors.
- [ ] Simulation integration tests shall verify simulation-layer lookahead detection uses indicator-provided availability metadata without making the indicator module own simulation errors.
- [ ] Floating-point warning and error handling shall be deterministic within official workflows.
- [ ] The benchmark suite shall fail CI when performance regresses by more than 20 percent without explicit approval.
- [ ] The deprecation error with opt-in phase shall last at least two minor releases, raise `IND_DEPRECATED` by default, and support an explicit opt-in flag to restore behavior with a warning.
- [ ] The removal phase shall occur only in a major version and shall return `IND_UNSUPPORTED_INDICATOR` or the closest deterministic unsupported-API error.
- [ ] Unsupported incremental mode requests shall fail deterministically.
- [ ] Parameter validation, schema validation, and data sufficiency checks shall be performed as the first operation and shall fail fast with deterministic error codes.
- [ ] Calculation mode: batch, incremental, streaming, or explicitly unsupported.
- [ ] Structured error result with deterministic error code on failure.
- [ ] Every invalid indicator request shall return a deterministic error code.
- [ ] Every invalid parameter set shall return a deterministic error code.
- [ ] Invalid output names, invalid output modes, invalid naming policies, and output column collisions shall return deterministic error codes.
- [ ] Unsupported indicator ids shall return a deterministic error code.
- [ ] Unsupported timeframes shall return a deterministic error code.
- [ ] Unsupported dtypes shall return a deterministic error code.
- [ ] Ambiguous, nonexistent, or timezone-naive timestamps shall return deterministic error codes in official workflows.
- [ ] Unknown adjustment status shall return a deterministic error code unless explicitly allowed.
- [ ] Missing or incompatible symbol mapping for symbol changes, mergers, ticker replacements, or vendor remaps shall return a deterministic error code.
- [ ] Formula version mismatches shall return a deterministic error code.
- [ ] Custom indicators rejected by conformance, status, dependency, or governance checks shall return deterministic error codes.
- [ ] Unauthorized proprietary indicator requests shall return deterministic access-control error codes.
- [ ] SLO violations detected during production monitoring shall emit deterministic metric events and shall return deterministic error codes when the request policy requires synchronous enforcement.
- [ ] `IND_INVALID_PARAMETER`
- [ ] `IND_UNSUPPORTED_INDICATOR`
- [ ] `IND_UNSUPPORTED_TIMEFRAME`
- [ ] `IND_UNSUPPORTED_DTYPE`
- [ ] `IND_INVALID_OUTPUT_COLUMN`
- [ ] `IND_INVALID_OUTPUT_MODE`
- [ ] `IND_INVALID_TIMEZONE`
- [ ] `IND_INVALID_OHLC`
- [ ] `IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED`
- [ ] `IND_UNSUPPORTED_OUT_OF_CORE`
- [ ] `IND_UNSUPPORTED_INCREMENTAL_MODE`
- [ ] `IND_INTERNAL_ERROR`
- [ ] Composition tests shall verify cyclic graphs, missing upstream columns, incompatible source timeframes, unavailable upstream values, and output column collisions fail deterministically.
- [ ] Performance benchmark tests shall prove the CI regression gate fails the build when the greater-than-20-percent regression threshold is triggered without explicit approval.
- [ ] Custom indicator tests shall verify import failure, dependency conflict, unsupported Python version, and side-effect enforcement failure handling.
- [ ] Usage examples shall show deterministic structured error behavior rather than relying only on successful calls.
- [ ] Documentation shall describe out-of-core processing, memory budgets, chunk sizes, spill storage, unsupported out-of-core rejection, and in-memory parity requirements.
- [ ] Out-of-core parity and unsupported out-of-core rejection tests pass.
#### `app/services/indicators/calculations.py`

Functions/classes:
- `calculate_sma`
- `calculate_ema`
- `calculate_adx`
- `calculate_atr`
- `calculate_adr`
- `calculate_rolling_volatility`
- `calculate_rsi`
- `calculate_williams_r`

Requirements:
- [ ] Indicator calculations shall not use current incomplete bar high, low, close, volume, or derived values for previous-closed-bar decisions.
- [ ] Indicator calculations may be cached by indicator id, parameter hash, input data checksum, implementation version, schema version, and precision policy.
- [ ] Indicator calculations shall support chunked processing where mathematically valid and shall preserve warmup continuity across chunks.
- [ ] Indicator calculations shall support out-of-core processing for datasets that exceed configured memory budgets when the indicator formula permits bounded-state or chunked computation.
- [ ] Indicator calculations shall define whether windows operate over rows, elapsed time, trading sessions, or calendar time.
- [ ] For batch calculations, full input validation shall complete before any output rows are computed.
- [ ] For incremental calculations, state deserialization validation and new-bar validation shall complete before incremental state is updated.
- [ ] Flagged rows shall be excluded from official calculations by default unless explicitly configured otherwise.
- [ ] Optional incremental state for incremental calculations.
- [ ] Indicator calculations shall emit structured operational metrics where enabled.
- [ ] No file-specific non-functional requirements defined.
- [ ] Input immutability tests shall verify indicator calculations do not mutate the input dataframe by default and raise `IND_INPUT_MUTATION_DETECTED` when official calculation detects unexpected mutation.
- [ ] Indicator implementations target Python.
- [ ] Indicator outputs are decision support artifacts, not official execution artifacts.
- [ ] Data normalization and source-readiness rules are owned by the data module.
- [ ] Indicator code shall be typed, documented, deterministic, and testable.
- [ ] Runtime dependencies, optional acceleration dependencies, development dependencies, and test dependencies shall be separated.
- [ ] Distributed typed packages shall include `py.typed` when public inline type annotations are intended for downstream type checking.
- [ ] Public type information shall be maintained for downstream users when the package is published as typed.
- [ ] Logs shall not include full market data payloads by default.
- [ ] Indicator execution shall support correlation ids for strategy and simulation workflow tracing.
- [ ] Indicator execution shall support distributed tracing across data fetch, indicator calculation, strategy consumption, and simulation integration boundaries when tracing is enabled.
- [ ] The module shall support OpenTelemetry-compatible trace propagation or an equivalent vendor-neutral tracing contract.
- [ ] Indicator implementations shall support feature-flagged and canary-routed execution for controlled rollout of new implementations.
- [ ] Canary comparison shall record output deltas, tolerance status, performance deltas, and rollback decisions without changing official outputs unless the canary route is explicitly selected.
- [ ] The module shall define default resource limits for maximum rows, symbols, columns, memory budget, chunk size, and timeout before production use.
- [ ] Proposed Core MVP default resource limits are `default_max_rows=10_000_000`, `default_max_symbols=1_000`, `default_max_columns=256`, `default_memory_budget_bytes=4_294_967_296`, `default_chunk_rows=1_000_000`, and `default_timeout_seconds=60`, pending owner/architect approval.
- [ ] Partial outputs shall not be returned as successful official results unless explicitly marked partial.
- [ ] Chunked, parallel, and out-of-core processing shall define backpressure behavior before implementation.
- [ ] Optional acceleration dependencies shall be isolated behind extras or feature flags.
- [ ] The project shall maintain a lockfile or equivalent reproducible dependency mechanism for official workflows.
- [ ] The project shall generate or support generating a software bill of materials for production releases.
- [ ] Distributed Python wheels, source distributions, and production packages shall be cryptographically signed by the approved CI/CD release pipeline using Sigstore, PEP 740-compatible attestations, or an equivalent approved signing mechanism.
- [ ] Dependency licenses shall be compatible with the intended deployment and distribution model.
- [ ] Known vulnerable dependencies shall not be allowed in production releases unless explicitly waived.
- [ ] Official indicator workflows shall declare supported numeric dtypes.
- [ ] Indicator implementations shall define whether outputs use `float64`, nullable floats, decimals, fixed-point integers, or another representation.
- [ ] Negative zero shall be normalized to zero for hashing, checksums, output comparison, and display.
- [ ] Indicator comparisons in tests shall use documented absolute and relative tolerances.
- [ ] Indicator implementations shall document thread-safety guarantees.
- [ ] SLO measurements shall be emitted through observability metrics and summarized in production readiness reports.
- [ ] The indicator module shall live under `app/services/indicators/` (relocated and approved per DEC-029/DONE-037).
- [ ] The indicator module shall provide reusable indicator calculation primitives for strategy, research, and simulation workflows.
- [ ] The indicator module shall not determine final official position size, margin acceptance, risk approval, or order matching.
- [ ] The indicator module shall expose typed, deterministic functions or classes that can be consumed by strategies and simulation orchestration.
- [ ] Indicator implementations shall validate parameter ranges before calculation.
- [ ] Indicators shall accept normalized historical market data from the data module contract.
- [ ] Batch indicators shall calculate outputs through vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation.
- [ ] The result object shall expose generated column names through `output_columns`.
- [ ] The result object shall expose `values_only` output for workflows that require indicator columns without the original OHLCV columns.
- [ ] Output column naming shall use stable lowercase snake_case names derived from indicator id, source column, period, and named parameters in canonical parameter order.
- [ ] Indicator-derived trade signals shall obey no-lookahead timing.
- [ ] Indicators used for bar-open strategies shall expose only fully closed-bar values available before the first tick of the next bar.
- [ ] At the first tick of bar `N`, indicator-derived data with timestamp greater than or equal to bar `N` open time shall be masked, dropped, or rejected before strategy access.
- [ ] Multi-timeframe indicator alignment shall not expose higher-timeframe values until the higher-timeframe bar is fully closed.
- [ ] The module shall provide `available_at`, source `bar_close_time`, source `bar_open_time` when available, `computed_from_start`, `computed_from_end`, `source_timeframe`, and a `lookahead_prohibited` flag for downstream lookahead enforcement.
- [ ] Vectorized indicator generation shall provide explicit utilities to shift outputs, such as `.shift(1)`, to align with bar-open execution logic.
- [ ] Core MVP numeric behavior shall use IEEE 754 `float64` outputs with default relative tolerance `1e-9` and default absolute tolerance `1e-12` for golden and cross-validation tests unless an approved formula table overrides the tolerance.
- [ ] Floating-point arithmetic may be used for research indicators when outputs are not directly used for official accounting or official fill prices.
- [ ] Indicator outputs that feed official simulation decisions shall be reproducible across replay runs.
- [ ] Performance benchmarks shall specify hardware profile, including CPU model, core count, RAM, and disk type when caching is disk-backed.
- [ ] Performance benchmarks shall define measurement methodology, including wall-clock timing and min, median, and p99 over a documented run count.
- [ ] Per-indicator benchmarks shall be maintained and tracked over releases.
- [ ] Optional hardware acceleration backends, including Numba, CuPy, SIMD, or equivalent backends, shall be isolated behind explicit feature flags or extras.
- [ ] Every accelerated indicator path shall provide a pure NumPy, pandas, or standard Python fallback with identical public API behavior.
- [ ] The module shall document whether each accelerated or parallel backend releases the GIL, uses multiprocessing, or requires single-threaded execution.
- [ ] The indicator module shall explicitly declare its public API surface.
- [ ] Internal modules shall be clearly marked as private and shall not be consumed directly by strategy or simulation code.
- [ ] The deprecation warning phase shall last at least two minor releases, emit structured warnings on every use, and continue full support.
- [ ] Deprecation timelines shall be documented in the changelog and migration guide.
- [ ] The indicator module shall expose a documented anatomy for every official and custom indicator.
- [ ] Private helper modules shall not be required for downstream strategy, simulation, notebook, or custom-indicator integration.
- [ ] Every built-in indicator shall provide a concrete formula specification before implementation begins.
- [ ] Every rolling-window indicator shall define whether windows are left-closed, right-closed, and whether the current row is included.
- [ ] Formula tables must be approved before any Core MVP implementation begins; their absence shall halt coding for `app/services/indicators/`.
- [ ] Formula specification tables shall use this minimum template:
- [ ] Every indicator output row shall include or derive a deterministic `available_at` timestamp.
- [ ] `available_at` shall represent the earliest time at which the value may be consumed by a strategy without lookahead.
- [ ] Strategy-facing APIs shall filter by `available_at <= decision_time`, not merely by indicator timestamp.
- [ ] Indicator outputs shall expose `label_time`, `bar_open_time`, `bar_close_time`, and `available_at` when these differ.
- [ ] Session-aware indicators shall use an explicit trading calendar.
- [ ] The module shall define behavior for weekends, exchange holidays, half-days, daylight-saving transitions, and missing session opens or closes.
- [ ] Multi-session rolling windows shall define whether overnight gaps are included.
- [ ] Indicators shall define whether pre-market, regular-session, post-market, and 24/7 market data are treated separately or continuously.
- [ ] Session resets shall be explicit for indicators that require them.
- [ ] Official workflows shall reject timezone-naive, ambiguous, or nonexistent local timestamps.
- [ ] Internal processing shall use UTC-aware timestamps or documented naive UTC representations only.
- [ ] Continuous futures or synthetic instruments shall declare roll method and adjustment method.
- [ ] Bid, ask, and mid-price indicators shall define behavior for stub quotes, inverted markets, missing bid or ask values, and extreme spreads.
- [ ] Late-arriving, corrected, or revised bars shall trigger deterministic recomputation or deterministic rejection.
- [ ] Custom indicators shall pass a conformance test suite before registration in official workflows.
- [ ] Custom indicators shall declare status: official, experimental, deprecated, or research-only.
- [ ] Experimental indicators shall not be used in official simulation workflows unless explicitly allowed.
- [ ] Custom indicators shall not perform network I/O, broker calls, filesystem writes, account mutations, or nondeterministic random operations during calculation.
- [ ] Custom indicators shall declare all external dependencies.
- [ ] Custom indicator conformance shall verify prohibited side effects through a documented enforcement mechanism before registration in official workflows.
- [ ] Official workflows shall reject custom indicators whose prohibited-operation checks cannot be executed, cannot be trusted, or return an inconclusive result.
- [ ] Custom indicator enforcement shall document whether validation uses static analysis, sandbox execution, runtime guards, process isolation, conformance tests, policy review, or a combination of these mechanisms.
- [ ] Custom indicators shall be reviewed before promotion to official status.
- [ ] When composition is enabled, the module shall accept only validated acyclic indicator graphs.
- [ ] Composed indicator chains shall preserve `available_at` correctly.
- [ ] No composed indicator shall consume a value before it is available.
- [ ] Supported quality flags shall include interpolated, backfilled, suspect, corrected, synthetic, auction, and vendor-specific flags when provided by the data module.
- [ ] Indicator implementations shall document how each quality flag affects calculation.
- [ ] The indicator module shall not directly own market-data fetching, source readiness, vendor adapters, or normalization logic.
- [ ] Higher-timeframe bars shall be validated before calculation and shall not make the indicator module responsible for market-data fetching, provider readiness, or normalization.
- [ ] Higher-timeframe bars shall be aligned using left-closed, right-closed boundaries matching the primary timeframe bar edges.
- [ ] The module shall support multiple higher-timeframe sources simultaneously with independent availability timestamps.
- [ ] Proprietary or licensed indicator implementations shall require an access-control decision before execution.
- [ ] Proprietary indicator execution shall be supported only through approved protected packaging mechanisms.
- [ ] Normalized OHLCV market data.
- [ ] Optional normalized tick or lower-timeframe data when an indicator explicitly requires it.
- [ ] Indicator id.
- [ ] Indicator parameter set.
- [ ] Source column selection for indicators that operate on a specific price or value column.
- [ ] Output naming policy.
- [ ] Output column conflict policy.
- [ ] Trading calendar or session policy when an indicator is session-aware.
- [ ] Price adjustment status.
- [ ] Price source.
- [ ] Optional intra-bar corporate-action adjustment policy.
- [ ] Optional indicator composition graph.
- [ ] Optional per-row data quality flags from the data module.
- [ ] Indicator result data aligned to timestamp and symbol.
- [ ] Generated indicator column names.
- [ ] Joined dataframe copy when join output mode is requested.
- [ ] Parameter hash.
- [ ] Output checksum.
- [ ] Indicator composition lineage where applicable.
- [ ] Observability metrics when enabled.
- [ ] Trace ids and span ids when distributed tracing is enabled.
- [ ] SLO measurement fields when SLO tracking is enabled.
- [ ] `IND_MISSING_REQUIRED_COLUMN`
- [ ] `IND_OUTPUT_COLUMN_CONFLICT`
- [ ] `IND_DUPLICATE_TIMESTAMP`
- [ ] `IND_NON_MONOTONIC_TIME`
- [ ] `IND_AMBIGUOUS_TIMESTAMP`
- [ ] `IND_INSUFFICIENT_DATA`
- [ ] `IND_LOOKAHEAD_RISK`
- [ ] `IND_UNKNOWN_ADJUSTMENT_STATUS`
- [ ] `IND_SYMBOL_MAPPING_REQUIRED`
- [ ] `IND_STUB_QUOTE_REJECTED`
- [ ] `IND_INVERTED_MARKET`
- [ ] `IND_SPREAD_THRESHOLD_EXCEEDED`
- [ ] `IND_DEPRECATED`
- [ ] `IND_ACCELERATION_BACKEND_UNAVAILABLE`
- [ ] `IND_RESOURCE_LIMIT_EXCEEDED`
- [ ] `IND_TIMEOUT`
- [ ] `IND_CANCELLED`
- [ ] `IND_PARTIAL_RESULT`
- [ ] `IND_CUSTOM_INDICATOR_REJECTED`
- [ ] `IND_ACCESS_DENIED`
- [ ] `IND_PROPRIETARY_UNAUTHORIZED`
- [ ] `IND_SLO_VIOLATION`
- [ ] Every functional and non-functional requirement shall have a stable requirement id before implementation begins.
- [ ] Default-parameter tests shall verify default parameter values and valid parameter ranges for every built-in indicator.
- [ ] Public API contract tests shall verify every public callable against the documented API contract table.
- [ ] Vectorized output tests shall verify batch indicators use vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation.
- [ ] No-lookahead tests shall cover previous-closed-bar availability, current-bar masking, multi-timeframe alignment, and vectorized signal shifting.
- [ ] Availability tests shall verify strategy-facing APIs filter by `available_at <= decision_time`.
- [ ] Changes to golden outputs shall require explicit approval and changelog entry.
- [ ] Calendar and session tests shall cover weekends, exchange holidays, half-days, daylight-saving transitions, session gaps, missing opens, missing closes, pre-market, regular-session, post-market, and 24/7 market data.
- [ ] Resource-limit tests shall cover maximum rows, symbols, columns, memory budget, execution timeout, cancellation, and partial-result handling.
- [ ] Multi-timeframe alignment tests shall verify higher-timeframe data requests through a fake data-module contract, forward-fill only after availability, independent availability timestamps for multiple higher-timeframe sources, boundary alignment, and stale gap prevention across weekends and holidays.
- [ ] Custom indicator conformance tests shall verify status, dependency declarations, no network I/O, no broker calls, no filesystem writes, no account mutations, no nondeterministic random operations, and promotion requirements.
- [ ] Custom indicator conformance tests shall verify rejection when prohibited-operation enforcement cannot run, cannot be trusted, or returns an inconclusive result.
- [ ] Property-based tests shall verify indicator output row count and symbol grouping match the documented output policy.
- [ ] Property-based tests shall verify adding future rows does not change previously available closed-bar outputs except when explicitly documented for revision-aware modes.
- [ ] Strategy integration tests shall verify indicator outputs can feed trade-signal generation without exposing prohibited current-bar data.
- [ ] Simulation integration tests shall verify indicator-derived signals are converted to trade intents before tick execution.
- [ ] Public API surface is documented.
- [ ] Production Scope Tiers are assigned and approved for every requirement.
- [ ] Public API contract tables are complete for every public callable.
- [ ] Vectorized dataframe output, deterministic indicator column naming, values-only output, joined-copy output, and output column conflict behavior are implemented and tested.
- [ ] Typed distribution includes `py.typed` when public inline type annotations are exported.
- [ ] Formula specifications exist for every official indicator.
- [ ] Golden fixtures exist for every official indicator.
- [ ] Calendar and session behavior is documented and tested.
- [ ] Indicator composition tests pass where composition is supported.
- [ ] Data-quality flag handling is implemented and tested.
- [ ] Deprecation lifecycle and `IND_DEPRECATED` behavior are implemented.
- [ ] Proprietary indicator access control and protected-source determinism tests pass for every proprietary indicator.
- [ ] Property-based and invariant tests pass.
- [ ] Mutation fuzz and survivorship bias tests pass.
- [ ] Distributed tracing, feature flag, canary routing, and SLO measurement tests pass.
- [ ] Dependency lockfile or equivalent reproducibility mechanism is present for official workflows.
- [ ] Dependency license and vulnerability checks pass or have explicit waivers.
- [ ] Software bill of materials generation is supported for production releases.
- [ ] Core MVP coding shall halt until `IND-PREQ-001`, `IND-PREQ-002`, `IND-PREQ-003`, `IND-PREQ-004`, `IND-PREQ-005`, and `IND-PREQ-006` are resolved or explicitly deferred.
- [ ] Optional Extension shall include streaming, out-of-core processing, acceleration backends, proprietary indicator execution, distributed tracing, SLO alert routing, and canary routing unless a later approved decision promotes any item.
- [ ] Future Improvement shall include capabilities that are useful but not required for the current approved implementation phase.
- [ ] Core MVP shall be implementable without optional acceleration backends, proprietary indicator controls, out-of-core execution, distributed tracing, SLO enforcement, or release-signing infrastructure.
- [ ] Every public callable shall be classified as stable, experimental, internal, optional, or future before implementation begins.
- [ ] GPU/SIMD acceleration may be added as an Optional Extension after Core MVP formula and fixture behavior is stable.
#### `app/services/indicators/batch/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/indicators/batch/trend.py`

Functions/classes:
- `SMAIndicator`
- `EMAIndicator`
- `ADXIndicator`
- `calculate_sma`
- `calculate_ema`
- `calculate_adx`

Requirements:
- [ ] The module shall support trend indicators including EMA, SMA, and ADX.
- [ ] Documentation shall include examples for EMA/SMA trend signals, ATR volatility sizing inputs, RSI momentum signals, vectorized dataframe output, joined indicator columns, and multi-timeframe alignment.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Indicator APIs shall remain separate from strategy execution and simulation execution services.
- [ ] Indicator implementations shall be reusable by notebook, CLI, agentic, and simulation workflows without changing semantics.
- [ ] Observability shall be optional and shall not change calculation semantics.
- [ ] A call equivalent to `ema(data, period=10, source="close")` shall generate an indicator column named `ema_10` when `close` is the default source.
- [ ] When the source column is not the default source or when naming ambiguity exists, output column names shall include the source column, such as `ema_open_10` or `ema_close_10`.
- [ ] Multi-output indicators shall expose deterministic output column names for each component, such as `adx_14`, `plus_di_14`, and `minus_di_14`.
- [ ] Custom output column names shall be accepted only when they pass schema validation, collision checks, and deterministic naming policy checks.
- [ ] Public API changes shall follow semantic versioning.
- [ ] Backward-incompatible public API, schema, formula, or behavior changes shall require a major version bump or documented migration path.
- [ ] Deprecated APIs, indicators, parameters, or schemas shall emit deterministic deprecation warnings and remain supported for a documented compatibility window.
- [ ] Indicator result schema versions shall be independently versioned from implementation versions.
- [ ] Debug-mode APIs shall enforce strict typing and runtime validation before calculation begins, using validated schemas or equivalent runtime guards.
- [ ] Deprecated indicators, parameters, schemas, or APIs shall follow a three-phase lifecycle.
- [ ] Every indicator shall define its exact mathematical formula.
- [ ] The HaruQuant formula specification shall remain the source of truth when third-party library conventions differ.
- [ ] Symbol changes, mergers, ticker replacements, and vendor remaps shall use an explicit symbol mapping contract.
- [ ] Optional symbol mapping contract for symbol changes, mergers, ticker replacements, and vendor remaps.
- [ ] Output schema version.
- [ ] `IND_FORMULA_VERSION_MISMATCH`
- [ ] Vectorized output tests shall verify `ema(data, period=10, source="close")` produces `ema_10` when `close` is the default source.
- [ ] Vectorized output tests shall verify non-default source naming such as `ema_open_10` and deterministic multi-output names such as `adx_14`, `plus_di_14`, and `minus_di_14`.
- [ ] EMA, SMA, RSI, ATR, and ADX outputs shall be cross-validated against at least two industry-standard libraries, including TA-Lib and pandas-ta, tulipy, or equivalent libraries, on fixed golden fixtures.
- [ ] Property-based tests shall verify Williams %R remains within documented bounds for valid non-degenerate windows.
- [ ] Usage examples shall remain executable documentation examples once implementation begins.
- [ ] Documentation shall include API examples showing `ema(data, period=10, source="close")` returning an `IndicatorResult` with `ema_10` and `result.join_to(data)` returning a copied dataframe with `ema_10` appended.
- [ ] Documentation shall describe semantic versioning policy and migration requirements for backward-incompatible changes.
- [ ] Documentation shall include exact mathematical formula, smoothing convention, alpha convention, seed behavior, rolling-window inclusivity, and edge-case behavior for every supported indicator.
- [ ] Documentation shall describe RSI, ATR, and ADX smoothing conventions.
- [ ] Documentation shall describe calendar, session, weekend, holiday, half-day, daylight-saving, missing-session, pre-market, regular-session, post-market, and 24/7 market semantics.
- [ ] Documentation shall describe intra-bar corporate-action adjustment rejection, deterministic intra-bar adjustment policies, symbol mapping continuity, mergers, ticker replacements, vendor remaps, stub quote handling, inverted market handling, spread thresholds, and mid-price fallback behavior.
- [ ] Documentation shall describe detailed multi-timeframe alignment, boundary semantics, independent availability timestamps, and stale gap prevention.
- [ ] Cross-library validation passes for EMA, SMA, RSI, ATR, and ADX against at least two industry-standard libraries.
- [ ] Proprietary source protection may be added through approved packaging/security controls without changing public indicator semantics.
#### `app/services/indicators/batch/volatility.py`

Functions/classes:
- `ema(...)`
- `sma(...)`
- `adx(...)`
- `atr(...)`
- `adr(...)`
- `rolling_volatility(...)`
- `rsi(...)`
- `williams_r(...)`

Requirements:
- [ ] The module shall support volatility indicators including ATR, ADR, and rolling volatility.
- [ ] Official indicator convenience functions shall expose typed wrappers for supported built-ins, including `ema(...)`, `sma(...)`, `adx(...)`, `atr(...)`, `adr(...)`, `rolling_volatility(...)`, `rsi(...)`, and `williams_r(...)`.
- [ ] Rolling volatility shall define return type, log-return versus simple-return behavior, sample versus population standard deviation, degrees of freedom, and annualization factor.
- [ ] Formula specification tables shall be completed for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R before implementation begins.
- [ ] Documentation shall describe rolling volatility return type, log/simple return policy, standard-deviation convention, degrees of freedom, and annualization factor.
- [ ] No file-specific non-functional requirements defined.
- [ ] Indicator tests shall cover EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R.
- [ ] Formula golden tests shall verify exact formula conventions, seed behavior, warmup length, rolling-window inclusivity, null handling, and degenerate-window behavior for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R.
- [ ] Golden fixtures shall cover normal data, flat markets, gaps, missing bars, duplicated timestamps, extreme volatility, zero volume, all-null windows, and insufficient warmup.
- [ ] Property-based tests shall verify rolling volatility is non-negative.
- [ ] ADR shall define whether it uses high-low range, close-to-close range, session range, calendar-day range, or trading-day range.
- [ ] The test plan shall include a requirement-to-test traceability matrix mapping each requirement id to one or more unit, contract, integration, performance, security, or documentation tests.
- [ ] Documentation shall include a requirement-to-test traceability matrix.
- [ ] Documentation shall describe ADR range convention and Williams %R degenerate-window behavior.
- [ ] Requirement-to-test traceability matrix exists and maps every requirement id to tests or approved deferral.
#### `app/services/indicators/batch/momentum.py`

Functions/classes:
- `RSIIndicator`
- `WilliamsRIndicator`
- `calculate_rsi`
- `calculate_williams_r`

Requirements:
- [ ] The module shall support momentum indicators including RSI and Williams %R.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Runtime dependencies shall be explicitly declared and version-constrained.
- [ ] Performance benchmarks shall specify Python version and key dependency versions, including NumPy, pandas, and any optional acceleration dependencies.
- [ ] Williams %R shall define behavior when highest high equals lowest low.
- [ ] Timezone database dependent conversions shall be confined to I/O boundaries and shall record timezone database version or conversion policy when available.
- [ ] Access-control checks shall validate actor, workflow, entitlement, environment, indicator id, indicator version, and intended use before calculation begins.
- [ ] Venue, exchange, data vendor, symbol normalization version, and corporate-action adjustment version where available.
- [ ] Implementation version.
- [ ] Formula version.
- [ ] The module shall define the exact canonical representation used for parameter hashing, including key ordering, defaults, omitted optional values, numeric formatting, null representation, string normalization, and version material.
- [ ] Reference outputs shall be reviewed and pinned by implementation version.
- [ ] Cross-validation deviations beyond documented tolerance shall require formula justification, implementation-version pinning, golden fixture approval, and changelog entry.
#### `app/services/indicators/incremental/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/indicators/incremental/state.py`

Functions/classes:
- `IndicatorProtocol`
- `IndicatorConfig`
- `IndicatorContext`
- `IndicatorResult`
- `IndicatorManifest`
- `IndicatorState`
- `WarmupRequirement`
- `IndicatorRegistration`
- `IndicatorError`
- `update(bar, state, config, context)`
- `update()`
- `serialize_state(state)`
- `deserialize_state(payload)`
- `serialize_state()`
- `deserialize_state()`
- `IND_STATE_INCOMPATIBLE`
- `IND_STATE_CORRUPTED`

Requirements:
- [ ] Official fills, orders, account state, journals, and reports are produced by the simulation module.
- [ ] The indicator module shall not execute trades, create fills, mutate account state, mutate simulation journals, or perform broker-state operations.
- [ ] Official production batch indicators shall not rely on per-row Python loops except for formulas with documented stateful dependencies that cannot be vectorized safely.
- [ ] Indicator implementations shall avoid hidden global mutable state.
- [ ] Performance benchmarks shall state whether cached or uncached performance is being measured.
- [ ] The public package shall expose `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError` with exact approved type contracts.
- [ ] `IndicatorProtocol` shall define `update(bar, state, config, context)` when the indicator supports incremental or streaming execution.
- [ ] `IndicatorProtocol` shall define `serialize_state(state)` and `deserialize_state(payload)` when the indicator supports incremental or streaming execution.
- [ ] `IndicatorState` shall contain serializable incremental accumulators, last processed timestamp, last processed symbol, warmup completion status, input checksum, and state schema version.
- [ ] RSI, ATR, and ADX implementations shall explicitly state whether they use Wilder smoothing or another smoothing convention.
- [ ] Formula specification tables shall state whether each indicator is Core MVP, Official Backtest Required, Production Required, Optional Extension, or Future Improvement.
- [ ] Symbol mapping shall preserve indicator state continuity across equivalent instrument identities without resetting warmup unless the mapping policy marks the instrument as discontinuous.
- [ ] Incremental indicators shall expose serializable state.
- [ ] Incremental state shall include enough information to resume calculation without recomputing the full history.
- [ ] Serialized incremental state shall use a documented binary or text serialization format.
- [ ] Serialized incremental state shall include indicator id.
- [ ] Serialized incremental state shall include implementation version.
- [ ] Serialized incremental state shall include incremental state schema version.
- [ ] Serialized incremental state shall include parameter hash.
- [ ] Serialized incremental state shall include input checksum of all data processed so far.
- [ ] Serialized incremental state shall include internal accumulator values sufficient to resume without recomputation.
- [ ] Serialized incremental state shall include last-processed timestamp and symbol.
- [ ] Serialized incremental state shall include warmup completion flag.
- [ ] Deserialization shall validate that provided state matches current indicator id, implementation version, schema version, and parameter set.
- [ ] Deserialization of state from a different indicator version, schema version, or parameter set shall return `IND_STATE_INCOMPATIBLE`.
- [ ] Corrupted or unreadable serialized state shall return `IND_STATE_CORRUPTED`.
- [ ] Incremental state size shall be bounded and shall not grow proportionally to the total number of bars processed.
- [ ] Indicators shall consume warmup data for calculation state but shall not emit output rows for the warmup period unless those rows are explicitly marked as warmup.
- [ ] Unauthorized proprietary indicator requests shall fail before input data is read, state is deserialized, cache entries are read, or calculation begins.
- [ ] Serializable incremental state when incremental calculation is enabled.
- [ ] Incompatible incremental state shall return a deterministic error code before state is updated.
- [ ] Corrupted incremental state shall return a deterministic error code before state is updated.
- [ ] `IND_STATE_INCOMPATIBLE`
- [ ] `IND_STATE_CORRUPTED`
- [ ] Stateless indicator functions shall be thread-safe by default.
- [ ] Stateful incremental indicators shall be single-owner or lock-free according to their documented state model.
- [ ] Single-owner incremental state objects shall not be safe for concurrent mutation.
- [ ] Lock-free incremental state objects shall be safe for concurrent reads with immutable state snapshots.
- [ ] Documentation shall describe incremental state serialization, idempotency, late-arriving data, corrected data, revised data, and out-of-order update behavior.
- [ ] Documentation shall describe incremental state format, state compatibility validation, state corruption handling, and bounded state size.
- [ ] Documentation shall describe thread-safety guarantees, incremental state ownership, immutable state snapshots, cache concurrency, parallel symbol execution, worker pools, worker counts, chunk sizes, and cache synchronization.
- [ ] Debug-mode strict typing and runtime validation fail before calculation or state mutation.
- [ ] Incremental state compatibility and corruption tests pass.
- [ ] `IndicatorManifest`, `IndicatorState`, and `IndicatorError` shall have exact serialized field contracts before implementation begins.
- [ ] No file-specific non-functional requirements defined.
- [ ] Input validation timing tests shall verify parameter validation, schema validation, data sufficiency checks, state deserialization validation, and new-bar validation fail before calculation or state mutation.
- [ ] Indicator anatomy tests shall verify `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError` contracts.
- [ ] Indicator anatomy tests shall verify required methods for `validate_parameters`, `required_columns`, `output_columns`, `warmup_requirement`, `validate_input`, `calculate`, `calculate_vectorized`, `update`, `serialize_state`, and `deserialize_state` where applicable.
- [ ] Debug-mode validation tests shall verify type mismatches fail before calculation, state mutation, cache reads, cache writes, or output generation.
- [ ] Incremental tests shall verify state serialization, resume behavior, idempotent repeated input bars, late-arriving bars, corrected bars, revised bars, and out-of-order updates.
- [ ] Incremental state tests shall verify state format, indicator id, implementation version, schema version, parameter hash, processed input checksum, accumulator values, last-processed timestamp, last-processed symbol, warmup completion flag, bounded state size, `IND_STATE_INCOMPATIBLE`, and `IND_STATE_CORRUPTED`.
- [ ] Symbol mapping tests shall cover symbol changes, mergers, ticker replacements, vendor remaps, state continuity, discontinuity markers, and warmup reset behavior.
- [ ] Concurrency tests shall verify stateless function thread safety, single-owner incremental-state behavior, immutable snapshot reads, parallel symbol execution, cache concurrent reads, and atomic synchronized cache writes.
- [ ] Fuzz tests shall verify graceful unavailable outputs or deterministic rejection for invalid mutated inputs without crashes, nondeterminism, cache corruption, or state corruption.
- [ ] Indicators shall define whether they support batch calculation, incremental calculation, streaming calculation, or a subset of these modes.
- [ ] The module shall define whether out-of-order incremental updates are supported.
- [ ] Documentation shall describe batch, incremental, and streaming calculation modes.
- [ ] Batch and incremental parity tests pass for indicators that support incremental mode.
#### `app/services/indicators/incremental/accumulators.py`

Functions/classes:
- `IndicatorAccumulator`
- `EMAAccumulator`
- `ATRAccumulator`
- `RSIAccumulator`
- `update_incremental_indicator`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/indicators/adapters/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/indicators/adapters/cache.py`

Functions/classes:
- `IndicatorCacheAdapter`
- `IndicatorCacheKey`
- `get_cached_indicator_result`
- `set_cached_indicator_result`
- `invalidate_indicator_cache`

Requirements:
- [ ] Cache hits shall be deterministic and shall never reuse results across incompatible input data, parameter sets, implementation versions, or schema versions.
- [ ] If an optional cache adapter is unreachable and `cache_policy="best_effort"`, the module shall degrade to uncached calculation with warning metadata rather than raising an unhandled exception.
- [ ] If an optional cache adapter is unreachable and `cache_policy="strict"`, the request shall fail before calculation with deterministic cache-unavailable diagnostics.
- [ ] Uncached first-run batch calculation for each official built-in indicator over 10 symbols and 10 years of M1 bars shall target p99 less than or equal to 5 seconds on the documented benchmark hardware profile.
- [ ] Warm-cache batch calculation for official indicator workloads shall target p99 less than or equal to 250 milliseconds for up to 10 symbols and 100,000 input rows, aligned with the service-level objective section.
- [ ] Performance benchmark specifications shall be the source for the p99 uncached and warm-cache targets defined in the service-level objective section.
- [ ] Out-of-core processing shall preserve warmup continuity, symbol grouping, timestamp ordering, provenance metadata, and cache-key determinism across chunks.
- [ ] Parallel execution across symbols shall be configurable by thread pool, process pool, worker count, chunk size, and cache synchronization mode.
- [ ] `IndicatorConfig` shall contain indicator id, parameters, source column, output naming policy, output mode, column conflict policy, precision policy, cache policy, calendar policy, availability policy, and execution backend configuration.
- [ ] All internal timestamp arithmetic and cache keys shall be normalized to UTC.
- [ ] Deterministic intra-bar adjustment policies shall be recorded in the indicator manifest and shall not differ across batch, incremental, streaming, or cached execution.
- [ ] The cache layer shall support composition.
- [ ] The indicator module shall own cache-key derivation and downstream invalidation triggers for composition when upstream inputs, upstream parameters, upstream formulas, or upstream implementation versions change.
- [ ] External cache storage backends shall own eviction, physical invalidation, consistency, and synchronization mechanisms through documented adapter contracts.
- [ ] The selected protection mechanism shall be outside the public API contract and shall not change deterministic outputs, error behavior, manifest content, cache keys, or test expectations.
- [ ] Optional cache policy.
- [ ] Optional SLO configuration containing latency target, cache-hit target, error-rate target, timeout-rate target, measurement window, and alert routing.
- [ ] Optional benchmark context containing hardware profile, Python version, dependency versions, cache mode, warmup iterations, and measurement methodology.
- [ ] The manifest shall include `calculation_config` with precision policy, session calendar identifier, data latency config, calculation mode, resource limits, and cache policy.
- [ ] The manifest shall include `slo` with configured thresholds and observed latency, cache status, error classification, and timeout status where applicable.
- [ ] Resource-limit, timeout, cancellation, partial-result, cache-write, unsupported out-of-core, unavailable acceleration backend, and unsupported incremental mode conditions shall return deterministic error codes.
- [ ] `IND_CACHE_INVALID`
- [ ] `IND_CACHE_WRITE_FAILED`
- [ ] Importing `app.services.indicators` shall not perform network I/O, filesystem writes, cache writes, plugin execution, long-running computation, environment mutation, or registration from untrusted plugins.
- [ ] Metrics shall include calculation duration, input row count, output row count, symbol count, cache hit or miss, memory usage estimate, rejected row count, warmup row count, and error code counts.
- [ ] Trace spans shall carry request id, correlation id, indicator id, implementation version, parameter hash, input checksum, cache status, backend id, and error code when available.
- [ ] Cache writes shall be atomic and shall not corrupt existing valid cache entries on failure.
- [ ] The module shall define behavior under memory pressure, cancellation, timeout, and interrupted cache writes.
- [ ] Cancellation, timeout, and memory-pressure handling shall clean up partial cache writes, audit writes, and out-of-core spill artifacts according to a documented cleanup policy.
- [ ] Dependency upgrades shall run the full indicator correctness, determinism, no-lookahead, cache, and benchmark suite.
- [ ] Cached outputs shall preserve dtype metadata.
- [ ] The cache layer shall be thread-safe for concurrent reads and atomic writes.
- [ ] Cache implementations shall support multiple concurrent readers.
- [ ] Cache implementations shall support single-writer or multi-writer operation with documented synchronization.
- [ ] The module shall document whether parallel symbol execution is supported and how it interacts with the cache.
- [ ] Production indicator workflows shall define service level objectives for calculation latency, cache hit ratio, non-transient error rate, and timeout rate.
- [ ] Default warm-cache calculation latency for official indicator workloads shall target p99 less than or equal to 250 milliseconds per indicator request for up to 10 symbols and 100,000 input rows.
- [ ] Default uncached first-run calculation latency for official indicator workloads shall target p99 less than or equal to 5 seconds for 10 years by 10 symbols of M1 bars on the documented benchmark hardware profile.
- [ ] Repeated research and simulation runs with stable inputs shall target cache hit ratio of at least 95 percent after cache warmup.
- [ ] Documentation shall include public API contract tables covering import paths, signatures, defaults, input schemas, output schemas, error behavior, side effects, cache behavior, stability level, and official-workflow eligibility.
- [ ] Documentation shall describe cache keys and invalidation behavior.
- [ ] Documentation shall describe UTC normalization for internal timestamp arithmetic and cache keys, and shall define local and exchange time handling at I/O boundaries.
- [ ] Documentation shall describe performance benchmark hardware profile, dependency versions, cached and uncached modes, warmup iterations, measurement methodology, and regression threshold.
- [ ] Documentation shall describe indicator composition, `available_at` preservation, provenance propagation, and downstream cache invalidation.
- [ ] Documentation shall describe service level objectives, latency thresholds, cache-hit thresholds, error-rate thresholds, timeout-rate thresholds, measurement windows, excluded error categories, and alert routing.
- [ ] Documentation shall describe resource limits, timeout behavior, cancellation behavior, memory-pressure behavior, interrupted cache-write behavior, and partial-result policy.
- [ ] UTC normalization for internal timestamp arithmetic and cache keys is implemented and tested.
- [ ] Thread-safety and cache-concurrency tests pass.
- [ ] Parallel symbol execution configuration and cache synchronization tests pass.
- [ ] Resource-limit, timeout, cancellation, and cache-write failure tests pass.
- [ ] Indicator documentation is complete for formulas, APIs, schemas, dtypes, cache behavior, observability, and release controls.
- [ ] Production Required shall include resource limits, redacted structured diagnostics, documented cache behavior if caching is enabled, public API compatibility rules, and acceptance gates for official workflows.
- [ ] Every public callable shall define its stable import path, function signature, required parameters, optional parameters and defaults, accepted input schema, returned object type, deterministic error behavior, side effects, cache behavior, stability level, and official-workflow eligibility.
- [ ] Out-of-core processing may be added as an Optional Extension after chunking parity and cache integrity requirements are approved.
- [ ] Canary routing, distributed tracing, SLO alerting, cryptographic package signing, release attestations, SBOM generation, and multi-writer cache synchronization may be added through platform or release-engineering integrations after ownership is approved.
- [ ] No file-specific non-functional requirements defined.
- [ ] Import-time tests shall verify importing `app.services.indicators` performs no network I/O, filesystem writes, cache writes, plugin execution, long-running computation, environment mutation, or registration from untrusted plugins.
- [ ] UTC normalization tests shall verify internal timestamp arithmetic and cache keys are UTC-normalized while local and exchange time conversions occur only at I/O boundaries.
- [ ] Cache tests shall cover cache hits, cache misses, schema-version changes, implementation-version changes, parameter changes, and input checksum changes.
- [ ] Cache tests shall verify atomic cache writes and failure behavior for interrupted cache writes.
- [ ] Cache degradation tests shall verify cache adapter connection failures fall back to uncached calculation with warning metadata under `cache_policy="best_effort"` and fail before calculation under `cache_policy="strict"`.
- [ ] Cache tests shall verify corrupt manifest rejection, stale cache rejection when dependency versions or schema versions change, output checksum mismatch detection, and canonical parameter hash stability across equivalent parameter ordering.
- [ ] Composition tests shall verify `available_at` preservation, provenance propagation, downstream cache invalidation, and rejection of unavailable upstream values.
- [ ] Performance benchmark tests shall verify benchmark metadata, cached and uncached modes, warmup iterations, min/median/p99 measurement, per-indicator tracking, and CI failure on unapproved regressions above 20 percent.
- [ ] Corporate-action tests shall cover intra-bar adjustment rejection, deterministic intra-bar adjustment policies, manifest recording, and parity across batch, incremental, streaming, and cached execution.
- [ ] SLO tests shall verify latency, cache-hit ratio, non-transient error rate, timeout rate, measurement windows, excluded error categories, alert routing metadata, and synchronous enforcement behavior when configured.
- [ ] Proprietary indicator tests shall verify access checks before execution, unauthorized request rejection before data or cache access, non-sensitive access-control manifest metadata, and deterministic parity for protected-source packages.
#### `app/services/indicators/adapters/audit.py`

Functions/classes:
- `IndicatorManifest`

Requirements:
- [ ] `IndicatorManifest` shall contain calculation identity, formula identity, input checksum, output checksum, parameter hash, output schema version, output column contract, data provenance, execution backend, timing, environment, and audit metadata.
- [ ] Official simulation and production workflows may require indicator calculation audit entries.
- [ ] When audit mode is enabled, the indicator module shall produce an immutable audit log entry.
- [ ] When `audit_mode=true` or the workflow policy requires audit, the module shall emit an immutable audit entry containing the full indicator manifest, request metadata, input checksum, output checksum, and tamper-evident integrity metadata.
- [ ] The module shall emit audit payloads through a documented audit sink interface rather than owning external audit storage unless a later approved architecture decision assigns that responsibility.
- [ ] Audit entries shall include the full indicator manifest.
- [ ] Audit entries shall include request metadata containing actor, workflow, correlation id, request id, and timestamp when available.
- [ ] Audit entries shall include input data checksum.
- [ ] Audit entries shall include output data checksum.
- [ ] Audit entries shall be append-only and tamper-evident through the approved Audit Policy appendix, which must define either chained SHA-256 HMAC with managed signing-key handling or a tamper-evident Merkle-tree policy before production use.
- [ ] Pending: Audit integrity mechanism selection, signing-key custody, rotation, and verification rules require owner/security approval before production audit mode is accepted.
- [ ] Audit mode shall not change indicator outputs except for additional audit metadata.
- [ ] Optional audit mode.
- [ ] Audit log entry when audit mode is enabled.
- [ ] Documentation shall describe audit mode, audit entry structure, tamper-evident integrity, and audit metadata.
- [ ] Audit mode entries are append-only, tamper-evident, and tested when audit mode is enabled.
- [ ] Production audit mode shall halt until `IND-PREQ-007` is resolved.
- [ ] No file-specific non-functional requirements defined.
- [ ] Audit tests shall verify audit entries include full manifest, request metadata, input checksum, output checksum, append-only behavior, tamper-evident integrity, and unchanged calculation semantics.
### Unit Tests Required

```text
tests/unit/app/services/indicators/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/03_indicators.py
```

Usage examples must show:
- `example_01_registry_and_capabilities`: Demonstrate indicator registration, lookup, listing, capability metadata, and unsupported-capability failures.
- `example_02_trend_indicators`: Demonstrate SMA, EMA, and ADX calculations with warmup and availability metadata.
- `example_03_volatility_indicators`: Demonstrate ATR, ADR, and rolling volatility calculations with precision policy metadata.
- `example_04_momentum_indicators`: Demonstrate RSI and Williams %R calculations with deterministic outputs and invalid-input handling.
- `example_05_incremental_state`: Demonstrate accumulator state serialization, compatibility checks, and incremental updates.
- `example_06_composition_and_dependency_graph`: Demonstrate DAG validation, composed indicator execution, dependency ordering, and cycle rejection.
- `example_07_caching_and_provenance`: Demonstrate cache keys, parameter hashes, implementation versions, source checksums, and provenance metadata.
- `example_08_no_lookahead_guards`: Demonstrate incomplete-bar rejection, previous-closed-bar decisions, and lookahead diagnostics.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 737 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(indicator-library): implement phase 3 indicator library requirements
```


- [ ] Indicator functions shall avoid production `print()` output and shall use structured logging only through approved utility logging contracts where logging is required.
- [ ] SBOM generation, cryptographic package signing, vulnerability checks, license gates, and release provenance attestations shall be CI/CD and release-engineering responsibilities, not Python indicator module runtime responsibilities, unless explicitly assigned by a later approved architecture decision.
- [ ] Release artifacts shall include provenance attestations that identify source revision, build workflow, build environment, package hash, and signing identity.
- [ ] Supply-chain tests shall verify dependency declarations, lockfile or equivalent reproducibility mechanism, license compatibility checks, vulnerability checks, SBOM generation support, cryptographic package signing, and release provenance attestations.
- [ ] Documentation shall describe market-data provenance, price adjustment status, price source, venue, vendor, symbol normalization version, corporate-action adjustment version, and continuous-instrument adjustment policy.
- [ ] Documentation shall describe dependency pinning, lockfile or equivalent reproducibility mechanism, SBOM generation, license checks, vulnerability checks, cryptographic package signing, release provenance attestations, and waiver process.
- [ ] Market-data provenance, adjustment status, intra-bar corporate actions, symbol mapping, and microstructure rules are validated.
- [ ] Cryptographic package signing and release provenance attestation are present for production packages.
## Phase 4 Strategy Service

### Goal

Implement the Strategy Service requirements under `app/services/strategies/` while preserving the phase module boundaries and governance rules.

Task inventory: 457 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/strategies/`.
- Requires Phase 3 Indicator Library contracts to be available where referenced by `04-strategy.md`.

### Files to Create

```text
app/__init__.py
app/services/strategies/__init__.py
app/services/strategies/registry.py
app/services/strategies/protocols.py
app/services/strategies/errors.py
app/services/strategies/vectorized.py
app/services/strategies/event.py
app/services/strategies/sandbox.py
app/services/strategies/
app/services/simulation/
app/utils/errors.py
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/strategies/README.md`

Functions/classes:
- No runtime functions/classes; documentation artifact only.

Requirements:
- [ ] [REQ-STRAT-269] Strategy documentation retention periods shall be defined for regulatory inquiries.
- [ ] [REQ-STRAT-428] Documentation shall include strategy input modes approved for `run_backtest`.
- [ ] [REQ-STRAT-013] Requirements without implementation scope shall carry an explicit `Documentation Only`, `Future`, or `Not Implemented` rationale.

#### `app/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] [REQ-STRAT-281] Strategies shall not assume infinite liquidity at the best bid or ask.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/strategies/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/strategies/registry.py`

Functions/classes:
- `STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE`
- `eval()`
- `exec()`
- `STRATEGY_INVALID_CONFIG`

Requirements:
- [ ] [REQ-STRAT-038] A strategy registry entry may declare `min_expected_alpha`, `max_acceptable_transaction_cost`, both, or neither.
- [ ] [REQ-STRAT-062] The module shall provide an official strategy registry.
- [ ] [REQ-STRAT-063] Registered strategies shall declare strategy id, version, module path, owner, configuration schema, supported symbols or asset classes, supported timing policy, required indicators, required data, risk assumptions, and permitted execution modes.
- [ ] [REQ-STRAT-064] Registered strategy identifiers shall resolve only to approved strategy modules.
- [ ] [REQ-STRAT-065] Strategy configuration shall be schema-validated before execution.
- [ ] [REQ-STRAT-066] Invalid strategy identifiers shall fail deterministically before simulation execution.
- [ ] [REQ-STRAT-067] Invalid strategy configuration shall fail deterministically before simulation execution.
- [ ] [REQ-STRAT-068] Strategy registry entries shall include version hashes for replay and audit.
- [ ] [REQ-STRAT-069] Strategy files and module paths shall resolve through approved registries or allowlisted roots, not arbitrary user-supplied filesystem paths.
- [ ] [REQ-STRAT-070] Duplicate strategy id/version registry entries shall fail registry validation deterministically before execution.
- [ ] [REQ-STRAT-071] Strategy version constraints shall resolve deterministically to exactly one approved immutable version or fail with `STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE` before execution.
- [ ] [REQ-STRAT-072] Deprecated strategies shall fail with `STRATEGY_DEPRECATED` unless explicitly run in approved historical replay mode.
- [ ] [REQ-STRAT-073] Strategy configuration schemas shall define default handling, unknown-field policy, required-field policy, type-coercion policy, enum validation, and version migration behavior.
- [ ] [REQ-STRAT-074] Strategy configuration validation shall reject configuration-injection patterns, including string fields that request evaluation, import, subprocess execution, filesystem access, network access, environment-variable access, template expansion, or dynamic attribute access unless a future approved sandbox contract explicitly permits them.
- [ ] [REQ-STRAT-075] Strategy configuration validation shall explicitly reject `eval()`, `exec()`, dynamic `__import__`, import strings, function-object strings, and magic-method access patterns in user-provided configuration.
- [ ] [REQ-STRAT-076] Strategy configuration validation shall enforce maximum payload size, maximum nesting depth, maximum string length, maximum collection length, and maximum schema-validation time before implementation acceptance.
- [ ] [REQ-STRAT-125] Strategy registry entries shall include owner, reviewer, approver, approval timestamp, approval expiry, and linked validation artifact ids.
- [ ] [REQ-STRAT-175] Strategy registry entries shall include source commit hash, artifact hash, package version, dependency lockfile hash, and build environment identifier.
- [ ] [REQ-STRAT-191] A strategy shall not execute in an environment not declared in its registry entry.
- [ ] [REQ-STRAT-196] Breaking changes to `TradeIntent`, strategy configuration schemas, event interfaces, or registry schemas shall require a version bump.
- [ ] [REQ-STRAT-270] ML-based strategies shall load models exclusively from an approved, versioned model registry or approved local artifact store, not arbitrary file paths.
- [ ] [REQ-STRAT-311] Provisional v1.0 baseline: event-driven strategy decision latency shall target P99 <= 10 ms per event on the approved reference environment unless a stricter registry profile is approved.
- [ ] [REQ-STRAT-312] Provisional v1.0 baseline: vectorized batch strategy execution shall target P99 <= 500 ms for the approved benchmark batch profile unless a stricter registry profile is approved.
- [ ] [REQ-STRAT-313] Provisional v1.0 baseline: each strategy instance shall target memory usage <= 256 MB, checkpoint size <= 10 MB, diagnostic payload <= 64 KB per decision, configuration payload <= 64 KB, and dependency call timeout <= 2 seconds unless an approved registry profile overrides the value.
- [ ] [REQ-STRAT-427] Documentation shall include strategy registry behavior.
- [ ] No file-specific non-functional requirements defined.
- [ ] [REQ-STRAT-328] Null or missing strategy configuration shall either apply schema defaults or fail according to the registry entry's configuration policy.
- [ ] [REQ-STRAT-331] Duplicate registry entry for the same strategy id/version shall fail registry validation.
- [ ] [REQ-STRAT-332] Malformed registry configuration schema shall fail registry validation with `STRATEGY_INVALID_CONFIG`.
- [ ] [REQ-STRAT-399] Strategy registry tests shall verify registered strategy identifiers resolve to approved modules.
- [ ] [REQ-STRAT-400] Strategy registry tests shall verify unregistered strategy identifiers are rejected.
- [ ] [REQ-STRAT-401] Strategy registry tests shall verify unapproved modules are rejected.
- [ ] [REQ-STRAT-411] Strategy tests shall include contract tests against data, indicator, simulation, and registry interfaces.
- [ ] [REQ-STRAT-440] Technology stack version constraints shall be explicit for production-eligible strategy execution.
- [ ] [REQ-STRAT-002] Each public capability shall define versioned input and output schemas using Pydantic models, `TypedDict`, dataclasses, or an approved equivalent.
- [ ] [REQ-STRAT-007] Public capabilities shall be versioned and compatibility-tested before being consumed by orchestration, simulation, risk, portfolio, audit, reporting, or API workflows.
- [ ] [REQ-STRAT-314] Provisional v1.0 baseline: performance tests shall define reference hardware, operating system, Python version, dependency versions, dataset size, strategy type, and measurement method before targets are accepted in CI.
- [ ] [REQ-STRAT-317] Strategy APIs shall remain backward compatible within a major interface version.
- [ ] [REQ-STRAT-009] Public schema changes shall require a schema-version change and compatibility review.
- [ ] [REQ-STRAT-010] Error examples and diagnostics examples shall include `schema_version`, `request_id`, and `correlation_id`.
- [ ] [REQ-STRAT-042] `TradeIntent` objects shall include strategy id, strategy version, symbol, side, intent type, requested sizing mode or quantity hint, optional stop loss, optional take profit, optional expiration, optional rationale, and signal timestamp.
- [ ] [REQ-STRAT-079] Phase 1 strategy execution shall allow registered strategies and validated configuration only.
- [ ] [REQ-STRAT-092] Strategy replay shall use strategy id, strategy version, configuration hash, data checksum, indicator result manifest, and simulation config hash.
- [ ] [REQ-STRAT-093] The same strategy id, version, configuration, input data, indicator outputs, and simulation seed shall produce the same trade intents.
- [ ] [REQ-STRAT-103] Strategy identifiers, configuration hashes, and version hashes must be included in replay and audit metadata.
- [ ] [REQ-STRAT-104] Registered strategy identifier.
- [ ] [REQ-STRAT-105] Strategy version or version constraint.
- [ ] [REQ-STRAT-117] Strategy manifest containing strategy id, version, configuration hash, required indicators, required data, and timing policy.
- [ ] [REQ-STRAT-119] `TradeIntent` schema shall define required fields, optional fields, enum values, precision rules, nullability, serialization format, and schema version.
- [ ] [REQ-STRAT-120] Registered strategies shall have one lifecycle status: `DRAFT`, `RESEARCH`, `BACKTEST_APPROVED`, `PAPER_APPROVED`, `LIVE_ELIGIBLE`, `DEPRECATED`, or `REVOKED`.
- [ ] [REQ-STRAT-123] Material strategy changes shall require a new immutable strategy version.
- [ ] [REQ-STRAT-126] Registered strategies shall declare a strategy-level risk profile.
- [ ] [REQ-STRAT-151] Diagnostics shall include run id, strategy id, strategy version, configuration hash, data checksum, decision timestamp, signal timestamp, intent id, decision id, and error code where applicable.
- [ ] [REQ-STRAT-174] Registered strategy artifacts shall be immutable after approval.
- [ ] [REQ-STRAT-179] Strategy dependency versions shall be pinned for replayable execution.
- [ ] [REQ-STRAT-184] Strategy state checkpoint restore shall validate strategy id, version, configuration hash, state schema version, and checkpoint checksum.
- [ ] [REQ-STRAT-195] Strategy interface versions shall follow explicit compatibility rules.
- [ ] [REQ-STRAT-197] Deprecated strategy APIs shall include removal version, migration guidance, and compatibility test coverage.
- [ ] [REQ-STRAT-198] Strategy replay shall use the exact interface version active at the time of original execution unless an approved migration exists.
- [ ] [REQ-STRAT-287] The strategy domain requirements document shall be versioned using Semantic Versioning.
- [ ] [REQ-STRAT-288] Breaking changes to strategy interfaces shall require a major document version bump and a documented migration guide.
- [ ] [REQ-STRAT-330] Unsupported strategy version or unsatisfiable version constraint shall fail before execution.
- [ ] [REQ-STRAT-345] Checkpoint restore with unsupported schema version, checksum mismatch, or unauthorized source shall fail before execution.
- [ ] [REQ-STRAT-353] `STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE`
- [ ] [REQ-STRAT-393] Performance tests shall state the exact hardware/software environment, dataset size, strategy type, dependency versions, measurement method, and target thresholds used.
- [ ] [REQ-STRAT-404] Replay tests shall verify the same strategy id, version, configuration, input data, indicator outputs, and simulation seed produce the same trade intents.
- [ ] [REQ-STRAT-426] Replay tests shall verify historical interface versions are used unless an approved migration exists.
- [ ] [REQ-STRAT-430] Documentation shall include configuration schema requirements for registered strategies.
- [ ] [REQ-STRAT-021] Every strategy decision shall be reproducible from strategy id, strategy version, configuration hash, data checksum, indicator manifest, simulation config hash where applicable, interface version, timing policy, and seed material.
#### `app/services/strategies/protocols.py`

Functions/classes:
- `StrategyProtocol`
- `StrategyConfig`
- `StrategyContext`
- `StrategyResult`
- `StrategySignal`
- `StrategyLifecycleHooks`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] [REQ-STRAT-436] Strategy implementations target Python.
- [ ] [REQ-STRAT-437] Official execution remains owned by the simulation module.
- [ ] [REQ-STRAT-438] Indicator calculations are owned by the indicator module.
- [ ] [REQ-STRAT-439] Data normalization and source-readiness rules are owned by the data module.
- [ ] [REQ-STRAT-441] Third-party service dependencies shall be declared before production-eligible strategy execution.
- [ ] [REQ-STRAT-442] Capacity assumptions shall include maximum supported symbols and maximum concurrent strategies.
- [ ] [REQ-STRAT-443] Assumption: This document remains a domain-level requirements source until the active roadmap approves Strategy implementation scope.
- [ ] [REQ-STRAT-001] Each public capability shall document an exact Python signature before implementation begins.
- [ ] [REQ-STRAT-006] Each public capability shall define its official callable name, stability level, intended consumers, input schema, output schema, deterministic error codes, side-effect policy, idempotency behavior, and compatibility guarantees before implementation begins.
- [ ] [REQ-STRAT-008] Public capabilities shall return structured results and shall not rely on free-form logs, unmapped exceptions, or implicit global state.
- [ ] [REQ-STRAT-303] Strategy code shall pass the project's configured type checker, expose public interfaces with docstrings or generated API documentation, avoid nondeterministic decision inputs except simulation-provided seeded randomness, and include linked unit or contract tests for each public strategy behavior.
- [ ] [REQ-STRAT-304] Strategy APIs shall remain separate from simulation execution services.
- [ ] [REQ-STRAT-305] Strategies shall use indicator module contracts for indicator-derived inputs.
- [ ] [REQ-STRAT-306] Strategies shall use data module contracts for normalized market data.
- [ ] [REQ-STRAT-308] Strategies shall not perform production `print()` output.
- [ ] [REQ-STRAT-316] Strategy diagnostics shall enforce redaction, maximum payload size, and structured schema validation.
- [ ] [REQ-STRAT-318] Strategy modules shall be deterministic under repeated execution with the same seed, inputs, configuration, indicator outputs, and environment policy.
- [ ] [REQ-STRAT-321] `MULTIPROCESS_ISOLATED` strategies shall define serialization, timeout, cancellation, restart, and resource-limit behavior.
- [ ] [REQ-STRAT-322] Randomized strategies shall use only the approved simulation-provided seeded randomness interface; direct use of process-global randomness is prohibited unless explicitly wrapped by that interface.
- [ ] [REQ-STRAT-323] Strategy dependency calls to data, indicator, simulation, or read-only state providers shall define timeout, retry/no-retry, stale result, partial failure, and exception mapping behavior.
- [ ] [REQ-STRAT-023] The strategy module shall live under `app/services/strategies/`.
- [ ] [REQ-STRAT-024] Strategies shall produce decisions, signals, trade intents, or strategy state updates.
- [ ] [REQ-STRAT-025] Strategies shall not directly mutate official account, order, deal, position, pending-order, margin, equity, journal, or execution timestamp state.
- [ ] [REQ-STRAT-027] Strategies shall not finalize official order volume, margin acceptance, execution price, fill status, or risk approval.
- [ ] [REQ-STRAT-028] Official execution, matching, accounting, journal, reporting, and production-realism classification shall remain owned by `app/services/simulation/`.
- [ ] [REQ-STRAT-034] Martingale, grid, pyramiding, basket recovery, and trade-decomposition strategies shall execute through the canonical simulation tick engine.
- [ ] [REQ-STRAT-035] Advanced strategies shall query the simulation engine for actual fills, remaining volume, average price, and open exposure through approved read-only interfaces.
- [ ] [REQ-STRAT-036] Advanced strategies that need fills or open positions shall use `ReadOnlyExecutionStateQuery` and `ReadOnlyExecutionStateSnapshot`; direct access to official simulation, execution, account, or position state is prohibited.
- [ ] [REQ-STRAT-037] Martingale level progression shall be based on confirmed deals or official position state, not submitted requests.
- [ ] [REQ-STRAT-039] When `min_expected_alpha` or `max_acceptable_transaction_cost` is declared, the strategy shall evaluate the declared threshold before emitting a trade intent and shall emit a deterministic suppression diagnostic when the threshold blocks the decision.
- [ ] [REQ-STRAT-041] Strategies shall emit `TradeIntent` objects instead of official orders.
- [ ] [REQ-STRAT-043] `TradeIntent` objects shall include an explicit `allow_partial_fills` boolean and `min_fill_size` parameter to guide the simulation or execution engine.
- [ ] [REQ-STRAT-044] Bar-based signals shall be aligned using the configured signal timing policy before becoming executable trade intents.
- [ ] [REQ-STRAT-045] The simulation engine shall transform `TradeIntent` into a sized `TradeRequest`.
- [ ] [REQ-STRAT-046] The simulation engine shall execute `TradeIntent` objects only when the canonical tick loop reaches an eligible tick.
- [ ] [REQ-STRAT-047] Strategies may request a sizing mode but shall not directly finalize official volume.
- [ ] [REQ-STRAT-048] Strategy-generated rationales shall be preserved for compliance or audit records when provided.
- [ ] [REQ-STRAT-049] The default strategy signal timing policy shall be `BAR_OPEN_PREVIOUS_CLOSE`.
- [ ] [REQ-STRAT-050] At the first tick of bar `N`, strategies may use only bars up to and including fully closed bar `N-1`.
- [ ] [REQ-STRAT-051] At the first tick of bar `N`, strategies shall not use current incomplete bar `N` high, low, close, volume, indicator-derived values, multi-timeframe values, or metadata derived from unavailable current-bar data.
- [ ] [REQ-STRAT-052] Strategies shall enter at the first valid tick of bar `N` only when a valid trade intent is emitted from previous-closed-bar data.
- [ ] [REQ-STRAT-055] Strategy tests shall cover previous-close-only behavior, shifted signals, no current-bar leakage, and first tick of new bar activation.
- [ ] [REQ-STRAT-056] Strategies shall enforce point-in-time correctness for all feature and indicator lookups.
- [ ] [REQ-STRAT-057] A query for data at timestamp `T` shall return only the state of the data as it was known at `T`, excluding subsequent revisions, restatements, or late-arriving ticks.
- [ ] [REQ-STRAT-058] Strategies shall declare `max_data_latency_tolerance`.
- [ ] [REQ-STRAT-059] Data arriving outside the declared latency tolerance shall cause the strategy to skip the decision or emit `STRATEGY_STALE_DATA`.
- [ ] [REQ-STRAT-077] `run_backtest` shall not execute arbitrary user-provided Python code strings.
- [ ] [REQ-STRAT-087] Approved strategy code shall still be protected by resource controls for CPU time, recursion depth, loop iterations where measurable, memory growth, checkpoint size, diagnostic size, and dependency call timeouts.
- [ ] [REQ-STRAT-089] Strategies may maintain decision state only.
- [ ] [REQ-STRAT-090] Strategy decision state shall be serializable when checkpoint or replay workflows require it.
- [ ] [REQ-STRAT-091] Strategy state checkpoints shall not include secrets or unrestricted raw proprietary strategy source.
- [ ] [REQ-STRAT-096] Concurrent strategy instances shall not share mutable strategy-local state unless an approved synchronization contract exists.
- [ ] [REQ-STRAT-097] Strategies may maintain decision state but shall not mutate official trading state.
- [ ] [REQ-STRAT-099] Bar-open trading must use previous closed-bar data by default.
- [ ] [REQ-STRAT-101] Advanced stateful strategies and agent-generated strategies shall provide decision rationale when required by compliance configuration.
- [ ] [REQ-STRAT-106] Validated strategy configuration.
- [ ] [REQ-STRAT-107] Indicator specifications or precomputed indicator outputs.
- [ ] [REQ-STRAT-108] Normalized market data.
- [ ] [REQ-STRAT-109] Symbol metadata.
- [ ] [REQ-STRAT-110] Signal timing policy.
- [ ] [REQ-STRAT-113] Timestamped `TradeIntent` objects.
- [ ] [REQ-STRAT-114] Strategy diagnostics.
- [ ] [REQ-STRAT-115] Strategy rationale where provided.
- [ ] [REQ-STRAT-116] Strategy state checkpoint where enabled.
- [ ] [REQ-STRAT-122] Promotion between lifecycle states shall require recorded evidence, including test results, validation report, owner approval, and risk approval where applicable.
- [ ] [REQ-STRAT-127] The risk profile shall include maximum gross exposure, maximum net exposure, maximum symbol exposure, maximum intent notional, maximum intent frequency, maximum concurrent positions, maximum pyramiding depth, maximum martingale level, and maximum grid depth where applicable.
- [ ] [REQ-STRAT-128] Strategy risk declarations shall be advisory inputs to the simulation or risk engine and shall not replace official risk approval.
- [ ] [REQ-STRAT-129] Strategies may self-suppress trade intents when strategy-local risk limits are breached.
- [ ] [REQ-STRAT-131] Risk-limit breaches shall produce deterministic diagnostics and audit metadata.
- [ ] [REQ-STRAT-132] Strategy risk profiles shall include concentration risk limits where applicable.
- [ ] [REQ-STRAT-133] Strategy risk profiles shall include time-based exposure limits where applicable.
- [ ] [REQ-STRAT-134] Strategy risk profiles shall declare gap risk assumptions.
- [ ] [REQ-STRAT-136] Every `TradeIntent` shall include a deterministic `intent_id`.
- [ ] [REQ-STRAT-138] Every `TradeIntent` shall include an idempotency key.
- [ ] [REQ-STRAT-139] Child intents shall include `parent_intent_id` when created from decomposition, scale-in, scale-out, recovery, or basket logic.
- [ ] [REQ-STRAT-140] Trade intents shall include a monotonically increasing strategy-local sequence number.
- [ ] [REQ-STRAT-142] Superseded, cancelled, expired, or replaced intents shall preserve lineage to the original intent.
- [ ] [REQ-STRAT-143] Strategies shall not emit executable trade intents until required indicators are warm and ready.
- [ ] [REQ-STRAT-144] Indicator readiness shall include warmup period, minimum sample count, NaN policy, and dependency readiness.
- [ ] [REQ-STRAT-145] Strategies shall declare their missing-data policy: reject, forward-fill, interpolate, skip signal, or use module default.
- [ ] [REQ-STRAT-146] Strategies shall declare their stale-data policy.
- [ ] [REQ-STRAT-147] Strategies shall declare whether they require bid, ask, mid, last, volume, spread, session metadata, corporate-action-adjusted prices, or raw prices.
- [ ] [REQ-STRAT-148] Multi-timeframe indicators shall be usable only when the higher-timeframe bar is fully closed as of the strategy decision timestamp.
- [ ] [REQ-STRAT-150] Strategy execution shall emit structured diagnostics, not free-form logs.
- [ ] [REQ-STRAT-154] Strategy execution shall support trace correlation across data, indicator, strategy, simulation, and reporting modules.
- [ ] [REQ-STRAT-155] Parameter optimization shall produce a validation artifact.
- [ ] [REQ-STRAT-156] Validation artifacts shall include parameter search space, objective function, training period, validation period, test period, data checksum, transaction-cost assumptions, slippage assumptions, and random seed.
- [ ] [REQ-STRAT-157] Strategy validation shall include in-sample and out-of-sample results.
- [ ] [REQ-STRAT-158] Strategy validation shall include walk-forward or rolling-window analysis where applicable.
- [ ] [REQ-STRAT-159] Strategy validation shall include transaction-cost sensitivity and slippage sensitivity.
- [ ] [REQ-STRAT-160] Strategy validation shall include market-regime analysis where applicable.
- [ ] [REQ-STRAT-161] Strategy validation shall reject or flag configurations whose performance depends on future data, unclosed bars, unapproved survivorship-biased data, or unapproved parameter leakage.
- [ ] [REQ-STRAT-162] Optimized configurations shall be immutable and hash-addressed before simulation or production replay.
- [ ] [REQ-STRAT-163] Strategies shall declare expected computational complexity or supported maximum input size where applicable.
- [ ] [REQ-STRAT-164] Strategies shall declare their concurrency model: `SYNC_BLOCKING`, `ASYNC_AWAIT`, or `MULTIPROCESS_ISOLATED`.
- [ ] [REQ-STRAT-165] Strategy execution shall have configurable per-decision latency budgets.
- [ ] [REQ-STRAT-166] Strategy execution shall have configurable memory limits.
- [ ] [REQ-STRAT-167] Strategy state checkpoint size shall be bounded and monitored.
- [ ] [REQ-STRAT-169] Strategies shall not instantiate unbounded caches, memoization dictionaries, or rolling window arrays without explicit maximum size limits and eviction behavior.
- [ ] [REQ-STRAT-172] Strategy behavior under timeout shall be deterministic.
- [ ] [REQ-STRAT-173] Performance regression tests shall verify strategy latency and memory remain within approved budgets.
- [ ] [REQ-STRAT-176] Strategy artifacts shall be produced by an approved build pipeline.
- [ ] [REQ-STRAT-177] Strategy artifacts shall pass type checking, linting, unit tests, contract tests, security scans, and dependency vulnerability checks before approval.
- [ ] [REQ-STRAT-178] Strategy artifacts shall include an SBOM where production packaging requires it.
- [ ] [REQ-STRAT-181] A strategy failure shall not corrupt official simulation state.
- [ ] [REQ-STRAT-182] Strategy failures shall be isolated to the failing strategy instance unless configured fail-fast behavior requires run termination.
- [ ] [REQ-STRAT-187] Strategies shall support an external asynchronous hard kill signal from the orchestration layer.
- [ ] [REQ-STRAT-188] A hard kill signal shall immediately halt execution, cancel pending intents, and dump state according to the approved emergency policy.
- [ ] [REQ-STRAT-189] Upon receiving a hard kill signal, the strategy shall emit a final `STRATEGY_HARD_KILLED` diagnostic with the last known safe state checkpoint.
- [ ] [REQ-STRAT-190] Strategies shall declare permitted environments: `BACKTEST`, `REPLAY`, `PAPER`, `SHADOW`, or `LIVE`.
- [ ] [REQ-STRAT-192] Paper or live execution eligibility shall require successful completion of configured validation gates.
- [ ] [REQ-STRAT-193] Live execution shall require explicit approval, expiry, rollback plan, monitoring plan, and emergency disable procedure.
- [ ] [REQ-STRAT-194] Environment-specific configuration differences shall be explicit, hash-addressed, and audit-recorded.
- [ ] [REQ-STRAT-199] Strategies shall not use wall-clock time, system randomness, network state, filesystem state, or environment variables as decision inputs.
- [ ] [REQ-STRAT-200] Randomized strategies shall use only simulation-provided seeded randomness.
- [ ] [REQ-STRAT-202] Price, volume, and quantity comparisons shall follow approved precision and rounding rules.
- [ ] [REQ-STRAT-203] Floating-point tolerance rules shall be explicit in tests.
- [ ] [REQ-STRAT-204] Every production-eligible strategy shall include a runbook.
- [ ] [REQ-STRAT-205] The runbook shall document expected behavior, configuration parameters, known failure modes, monitoring metrics, disable procedure, replay procedure, and owner escalation path.
- [ ] [REQ-STRAT-206] Strategies shall declare their execution assumptions, including fill model, latency model, and market impact model.
- [ ] [REQ-STRAT-207] Trade intents shall specify acceptable execution algorithms, such as `TWAP`, `VWAP`, or `ICEBERG`, where applicable.
- [ ] [REQ-STRAT-208] Strategies shall declare maximum permissible spread for execution.
- [ ] [REQ-STRAT-209] Strategies shall declare minimum volume requirements and maximum volume participation rates.
- [ ] [REQ-STRAT-210] Dark pool, auction, and alternative venue eligibility shall be explicitly declared.
- [ ] [REQ-STRAT-211] Strategies shall declare one deterministic policy for each halt-like market state: `SUPPRESS_NEW_INTENTS`, `ALLOW_REDUCE_ONLY`, `CLOSE_INTENTS_ONLY`, or `NO_SPECIAL_HANDLING`.
- [ ] [REQ-STRAT-212] The selected halt-like market-state policy shall be included in strategy diagnostics when such a market state affects a decision.
- [ ] [REQ-STRAT-213] Fill probability models shall account for queue position and adverse selection where applicable.
- [ ] [REQ-STRAT-214] Strategies shall declare interaction modes: `INDEPENDENT`, `COOPERATIVE`, or `PORTFOLIO_AWARE`.
- [ ] [REQ-STRAT-215] Strategies shall declare portfolio-interaction assumptions and optional strategy-local exposure preferences.
- [ ] [REQ-STRAT-216] Portfolio-level gross and net exposure enforcement shall remain owned by the portfolio or risk module.
- [ ] [REQ-STRAT-217] Strategy-level capital allocation assumptions and position-sizing preferences shall be metadata for portfolio or risk consumers, not official allocation enforcement.
- [ ] [REQ-STRAT-218] Strategies may declare conflict-priority hints, but cross-strategy conflict resolution shall remain owned by portfolio, risk, or orchestration modules.
- [ ] [REQ-STRAT-219] Correlation-aware position-limit assumptions shall be declared where applicable.
- [ ] [REQ-STRAT-220] Strategy turn-off and onboarding runbook metadata shall describe existing-position assumptions; official position handling shall remain owned by trading, risk, portfolio, live, or simulation modules.
- [ ] [REQ-STRAT-221] Strategy health checks shall be defined for signal generation frequency, decision staleness, and data freshness.
- [ ] [REQ-STRAT-222] Strategies shall declare circuit-breaker inputs, expected trigger diagnostics, and safe-disable behavior; circuit-breaker enforcement shall remain owned by orchestration, risk, live, or operations modules.
- [ ] [REQ-STRAT-223] Strategies shall declare graduated-deployment eligibility metadata and rollback assumptions; deployment progression and rollback enforcement shall remain owned by deployment or operations modules.
- [ ] [REQ-STRAT-224] Strategy performance metadata shall declare expected review bands for supplied analytics, but these bands shall not become approved risk thresholds or promotion rules until owner/governance approval records them.
- [ ] [REQ-STRAT-225] Strategies shall emit or expose drift-detection diagnostics where applicable; alert routing remains owned by observability or operations modules.
- [ ] [REQ-STRAT-226] Canary-analysis metadata shall describe expected paper/live consistency checks; official comparison and promotion decisions remain owned by analytics, risk, live, or governance modules.
- [ ] [REQ-STRAT-227] Strategies shall declare applicable regulatory regimes, such as `SEC`, `ESMA`, or `FCA`, where applicable.
- [ ] [REQ-STRAT-228] Position-limit and reporting assumptions by jurisdiction shall be declared where applicable; official regulatory reporting and limit enforcement remain owned by compliance, risk, portfolio, or reporting modules.
- [ ] [REQ-STRAT-230] Market manipulation safeguards shall prohibit spoofing, layering, marking the close, and equivalent manipulative behavior.
- [ ] [REQ-STRAT-231] Strategy audit metadata shall preserve intent creation and decision rationale references; official sizing, execution, fill, and regulatory audit records remain owned by trading, simulation, live, audit, or reporting modules.
- [ ] [REQ-STRAT-232] Best-execution and venue-analysis assumptions shall be declared where applicable; official venue analysis remains owned by execution, compliance, or reporting modules.
- [ ] [REQ-STRAT-233] Large-position reporting assumptions shall be documented where applicable; official reporting threshold enforcement remains external to the strategy module.
- [ ] [REQ-STRAT-234] Strategies shall declare maximum permissible data gaps before entering safe mode.
- [ ] [REQ-STRAT-235] Dividend, split, and corporate action handling procedures shall be specified.
- [ ] [REQ-STRAT-236] Strategies shall declare startup data-readiness requirements for completeness, expected ranges, and consistency checks; validation enforcement remains owned by data, orchestration, or simulation modules.
- [ ] [REQ-STRAT-238] Strategies shall declare delisted-symbol assumptions and safe behavior; official position liquidation procedures remain owned by trading, risk, live, portfolio, or operations modules.
- [ ] [REQ-STRAT-240] Strategy decision latency SLOs shall be defined by environment, including P50, P95, and P99 targets.
- [ ] [REQ-STRAT-241] Signal generation throughput minimums shall be defined for expected market conditions.
- [ ] [REQ-STRAT-243] Recovery point objectives shall be defined for strategy state.
- [ ] [REQ-STRAT-244] Resource utilization limits shall include CPU, memory, and network bandwidth budgets.
- [ ] [REQ-STRAT-245] Graceful degradation procedures shall be defined for overload conditions.
- [ ] [REQ-STRAT-246] Strategies shall define calibration frequency and trigger conditions.
- [ ] [REQ-STRAT-247] Parameter stability analysis shall cover different market regimes.
- [ ] [REQ-STRAT-248] Sensitivity analysis shall include approved parameter perturbation bands, including plus or minus 10% and plus or minus 20% where applicable.
- [ ] [REQ-STRAT-249] Minimum training data period requirements and regime representation shall be defined.
- [ ] [REQ-STRAT-250] Overfitting detection criteria and automated strategy retirement procedures shall be defined.
- [ ] [REQ-STRAT-251] Ensemble and model averaging policies shall be defined for production strategies where applicable.
- [ ] [REQ-STRAT-253] Strategy-local state checkpoint and restore assumptions shall be defined for primary and backup instances.
- [ ] [REQ-STRAT-254] Maximum tolerable strategy-local state loss and decision staleness shall be declared.
- [ ] [REQ-STRAT-255] Communication metadata for strategy degradation shall identify owner escalation paths; incident communications remain owned by operations.
- [ ] [REQ-STRAT-256] Market closure and early close strategy behavior shall be declared.
- [ ] [REQ-STRAT-257] Emergency position liquidation assumptions may be documented, but official liquidation procedures and responsible-party approval remain owned by trading, risk, live, portfolio, compliance, or operations modules.
- [ ] [REQ-STRAT-258] Strategy performance review cadence and responsible parties shall be defined.
- [ ] [REQ-STRAT-259] Automated performance attribution shall distinguish alpha, market exposure, and style factor contributions where applicable.
- [ ] [REQ-STRAT-260] Strategy improvements shall support an A/B testing framework where applicable.
- [ ] [REQ-STRAT-261] Shadow testing requirements shall be satisfied before production promotion.
- [ ] [REQ-STRAT-262] Kill criteria shall define objective rules for permanent strategy decommissioning.
- [ ] [REQ-STRAT-264] Strategy intellectual property classification and protection measures shall be documented.
- [ ] [REQ-STRAT-265] Third-party dependency licensing compliance shall be verified.
- [ ] [REQ-STRAT-266] Data vendor agreement compliance checks shall be performed where applicable.
- [ ] [REQ-STRAT-267] Strategy descriptions shall be available for regulatory filings where applicable.
- [ ] [REQ-STRAT-268] Material change notification procedures to stakeholders shall be documented.
- [ ] [REQ-STRAT-271] Model artifacts shall be serialized in standardized, language-agnostic formats such as `ONNX` or `PMML` where possible.
- [ ] [REQ-STRAT-272] Strategies shall declare any dependency on a feature store.
- [ ] [REQ-STRAT-273] Feature lookups shall be validated against the strategy's declared point-in-time correctness policy.
- [ ] [REQ-STRAT-274] ML-based strategies shall implement concept drift and data drift detection where applicable.
- [ ] [REQ-STRAT-275] Strategies shall emit `STRATEGY_DRIFT_DETECTED` when input feature distributions or model prediction confidence deviate beyond approved statistical thresholds.
- [ ] [REQ-STRAT-276] Strategies shall be prohibited from containing hardcoded secrets, API keys, or credentials.
- [ ] [REQ-STRAT-277] Strategies requiring external configuration secrets shall request them through an approved read-only secrets manager interface injected at runtime by the orchestration layer.
- [ ] [REQ-STRAT-278] Strategies shall not log, serialize, checkpoint, or expose secrets in diagnostics, rationale, manifests, or state snapshots.
- [ ] [REQ-STRAT-280] Strategies using Level 2 or Level 3 data shall declare their maximum supported order book depth.
- [ ] [REQ-STRAT-282] Strategies may annotate intents with declared maximum volume participation assumptions for visible order book data at the decision timestamp; official sizing validation remains owned by risk, trading, simulation, or live execution modules.
- [ ] [REQ-STRAT-284] Strategies shall define deterministic behavior when order book data is crossed, locked, stale, incomplete, or outside the declared supported depth.
- [ ] [REQ-STRAT-285] Each requirement shall be traceable to a specific test case id where implementation is required.
- [ ] [REQ-STRAT-286] Major design-choice requirements shall be traceable to an Architecture Decision Record.
- [ ] [REQ-STRAT-289] A strategy shall not be considered production-ready until it passes applicable testing, validation, and runbook requirements.
- [ ] [REQ-STRAT-290] Production-ready strategy approval shall require sign-off from the Quant Research Lead and Engineering Lead, or their approved delegates.
- [ ] [REQ-STRAT-291] Strategies shall follow a standard processing anatomy: data input, indicator calculation, signal generation, timing alignment, trade intent creation, and simulation execution.
- [ ] [REQ-STRAT-297] Hook inputs and outputs shall be typed and schema-documented.
- [ ] [REQ-STRAT-298] Strategy hooks shall return only approved strategy outputs, including decisions, diagnostics, state updates, or `TradeIntent` objects.
- [ ] [REQ-STRAT-299] Strategy hooks shall not mutate official simulation, execution, account, order, position, journal, or reporting state directly.
- [ ] [REQ-STRAT-301] Required and optional hooks shall be explicitly declared by strategy type.
- [ ] [REQ-STRAT-302] Unsupported hooks for a strategy type shall fail deterministically or be ignored according to the approved interface contract.
- [ ] [REQ-STRAT-327] Invalid strategy configuration schema shall fail before execution.
- [ ] [REQ-STRAT-329] Unknown configuration fields shall be rejected or ignored according to an explicit schema policy.
- [ ] [REQ-STRAT-337] Data-service timeout, unavailable dependency, broken connection, or network partition shall produce `STRATEGY_DATA_NOT_READY` after the approved retry/no-retry policy is exhausted.
- [ ] [REQ-STRAT-339] Partial data degradation shall follow the strategy's declared missing-data policy: `reject` suppresses all intents, `skip signal` suppresses affected symbols, and any degraded subset execution shall emit `STRATEGY_DATA_QUALITY_GATE_FAILED` diagnostics naming omitted symbols without exposing private payloads.
- [ ] [REQ-STRAT-343] Duplicate, out-of-order, stale, revised, or late-arriving ticks shall follow the declared data policy.
- [ ] [REQ-STRAT-344] Strategy hook timeout shall return `STRATEGY_TIMEOUT` and follow the configured failure policy.
- [ ] [REQ-STRAT-350] Concurrent read-only state snapshots across multiple strategies shall define isolation level, snapshot timestamp, and behavior when official state updates during decision traversal.
- [ ] [REQ-STRAT-351] `STRATEGY_INVALID_CONFIG`
- [ ] [REQ-STRAT-352] `STRATEGY_NOT_FOUND`
- [ ] [REQ-STRAT-354] `STRATEGY_DEPRECATED`
- [ ] [REQ-STRAT-355] `STRATEGY_UNAPPROVED_MODULE`
- [ ] [REQ-STRAT-356] `STRATEGY_SCHEMA_VALIDATION_FAILED`
- [ ] [REQ-STRAT-357] `STRATEGY_UNSUPPORTED_TIMING_POLICY`
- [ ] [REQ-STRAT-363] `STRATEGY_ENVIRONMENT_NOT_PERMITTED`
- [ ] [REQ-STRAT-364] `STRATEGY_ARTIFACT_HASH_MISMATCH`
- [ ] [REQ-STRAT-365] `STRATEGY_DEPENDENCY_HASH_MISMATCH`
- [ ] [REQ-STRAT-368] `STRATEGY_CHECKPOINT_INCOMPATIBLE`
- [ ] [REQ-STRAT-369] `STRATEGY_DATA_NOT_READY`
- [ ] [REQ-STRAT-370] `STRATEGY_INDICATOR_NOT_READY`
- [ ] [REQ-STRAT-371] `STRATEGY_MISSING_REQUIRED_DATA`
- [ ] [REQ-STRAT-372] `STRATEGY_STALE_DATA`
- [ ] [REQ-STRAT-373] `STRATEGY_DUPLICATE_INTENT`
- [ ] [REQ-STRAT-374] `STRATEGY_RESOURCE_LIMIT_EXCEEDED`
- [ ] [REQ-STRAT-375] `STRATEGY_TIMEOUT`
- [ ] [REQ-STRAT-376] `STRATEGY_VALIDATION_ARTIFACT_REQUIRED`
- [ ] [REQ-STRAT-377] `STRATEGY_RISK_PROFILE_REQUIRED`
- [ ] [REQ-STRAT-378] `STRATEGY_CIRCUIT_BREAKER_TRIGGERED`
- [ ] [REQ-STRAT-379] `STRATEGY_POSITION_LIMIT_EXCEEDED`
- [ ] [REQ-STRAT-380] `STRATEGY_VOLUME_PARTICIPATION_EXCEEDED`
- [ ] [REQ-STRAT-382] `STRATEGY_PERFORMANCE_DEGRADED`
- [ ] [REQ-STRAT-383] `STRATEGY_DRIFT_DETECTED`
- [ ] [REQ-STRAT-384] `STRATEGY_REGULATORY_LIMIT_BREACHED`
- [ ] [REQ-STRAT-385] `STRATEGY_MARKET_ACCESS_REVOKED`
- [ ] [REQ-STRAT-386] `STRATEGY_HARD_KILLED`
- [ ] [REQ-STRAT-387] Every requirement id shall have at least one linked test id or a documented non-implementation rationale.
- [ ] [REQ-STRAT-390] Every usage example shall be executable or schema-validatable as documentation test coverage.
- [ ] [REQ-STRAT-391] The traceability matrix shall be tested or reviewed as an explicit pre-implementation deliverable.
- [ ] [REQ-STRAT-392] Public capability tests shall verify exact Python signatures, input schema validation, output schema validation, error decision tables, side-effect rules, and batch/stream behavior.
- [ ] [REQ-STRAT-396] Strategy tests shall cover EMA trend intents, martingale recovery, decomposition child orders, and partial-fill handling.
- [ ] [REQ-STRAT-397] Strategy tests shall cover previous-closed-bar signal timing and no-lookahead behavior.
- [ ] [REQ-STRAT-398] Strategy tests shall verify indicator-derived signals cannot access prohibited current-bar values.
- [ ] [REQ-STRAT-402] Strategy configuration tests shall verify valid schemas pass and invalid schemas fail deterministically.
- [ ] [REQ-STRAT-405] Strategy tests shall include golden-file replay tests for emitted `TradeIntent` manifests.
- [ ] [REQ-STRAT-408] Strategy tests shall include fuzz tests for invalid configuration, malformed data, missing fields, duplicate ticks, out-of-order ticks, NaN indicators, and extreme prices.
- [ ] [REQ-STRAT-410] Strategy tests shall include performance regression tests with approved latency and memory thresholds.
- [ ] [REQ-STRAT-412] Strategy tests shall include snapshot tests verifying stable intent ids, decision ids, configuration hashes, and replay manifests.
- [ ] [REQ-STRAT-414] Strategy tests shall include mutation testing to verify that deliberate subtle corruptions to strategy logic or data inputs are caught by the test suite.
- [ ] [REQ-STRAT-417] Boundary tests shall verify strategies cannot mutate official account, order, deal, position, margin, equity, journal, reporting, or execution timestamp state.
- [ ] [REQ-STRAT-419] Boundary tests shall verify portfolio, compliance, disaster-recovery, deployment, and venue requirements are exposed only as declarations or metadata, not enforced inside the strategy module.
- [ ] [REQ-STRAT-421] Security tests shall cover configuration-injection payloads, oversized configuration payloads, excessive nesting, excessive string lengths, and resource exhaustion through sanctioned strategy and indicator paths.
- [ ] [REQ-STRAT-424] Clock-drift tests shall verify behavior when strategy, data, indicator, or simulation timestamps exceed approved tolerance.
- [ ] [REQ-STRAT-429] Documentation shall state that raw arbitrary Python strategy code is not accepted by `run_backtest`.
- [ ] [REQ-STRAT-434] Documentation shall describe strategy replay metadata.
- [ ] [REQ-STRAT-435] Documentation shall include public capability contracts, requirement IDs, applicability tags, acceptance criteria, and linked test IDs before Builder handoff.
- [ ] [REQ-STRAT-011] Before Builder handoff, each requirement shall include a stable requirement id, priority, phase, applicability tags, owning module, acceptance criteria, and at least one linked test case id where implementation is required.
- [ ] [REQ-STRAT-012] Applicability tags shall identify whether a requirement applies to `BACKTEST_CORE`, `REPLAY`, `PAPER`, `SHADOW`, `LIVE`, `ML_ONLY`, `L2_L3_ONLY`, `REGULATED_MARKET_ONLY`, or `FUTURE`.
- [ ] [REQ-STRAT-015] A traceability matrix shall be a required deliverable before implementation begins, not a future improvement.
- [ ] [REQ-STRAT-016] Stable requirement IDs, acceptance criteria, applicability tags, and linked test IDs are required for v1.0 Builder handoff.
- [ ] [REQ-STRAT-017] Strategies shall emit `TradeIntent` objects and diagnostics, not broker orders, official fills, account mutations, portfolio mutations, risk approvals, or regulatory reports.
- [ ] [REQ-STRAT-018] Risk, trading, simulation, live, portfolio, compliance, reporting, data, and indicator modules shall remain the authorities for their own enforcement responsibilities.
- [ ] [REQ-STRAT-019] Strategy execution shall receive read-only snapshots or approved read-only handles for external state; strategy code shall not mutate official external state directly.
- [ ] [REQ-STRAT-020] Every external-module interaction shall pass through a documented contract with deterministic error mapping, timeout behavior, and redaction behavior.
- [ ] [REQ-STRAT-022] Strategy implementation scope shall be narrowed to an approved phase slice before Builder handoff.
#### `app/services/strategies/errors.py`

Functions/classes:
- `STRATEGY_LOOKAHEAD_DETECTED`

Requirements:
- [ ] [REQ-STRAT-DRY-01] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom strategy exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.
- [ ] [REQ-STRAT-054] Strategy access to prohibited current-bar or future data shall fail with the canonical strategy-domain error code `STRATEGY_LOOKAHEAD_DETECTED`; lower-level simulation lookahead errors, if any, shall be mapped to this code before returning strategy diagnostics.
- [ ] [REQ-STRAT-186] Repeated strategy errors shall trigger deterministic disablement or escalation according to configuration.
- [ ] [REQ-STRAT-307] Strategies shall return safe, deterministic errors for invalid configuration or unsupported inputs.
- [ ] No file-specific non-functional requirements defined.
- [ ] [REQ-STRAT-388] Every public capability shall have contract tests for valid input, invalid input, deterministic errors, idempotency, and side effects.
- [ ] [REQ-STRAT-422] Error-code tests shall verify lower-level lookahead errors map to `STRATEGY_LOOKAHEAD_DETECTED` at strategy-module boundaries.
- [ ] [REQ-STRAT-423] Dependency-failure tests shall verify data-layer failures map to `STRATEGY_DATA_NOT_READY` or approved data errors and indicator-layer failures map to `INDICATOR_MODULE_ERROR`.
- [ ] [REQ-STRAT-003] Each public capability shall include a decision table mapping every validation condition, dependency condition, lifecycle condition, timeout condition, and security condition to one deterministic error code.
- [ ] [REQ-STRAT-083] Raw strategy-code injection attempts shall be rejected before execution.
- [ ] [REQ-STRAT-084] Rejected raw strategy-code input shall return `SIM_ARBITRARY_CODE_REJECTED`.
- [ ] [REQ-STRAT-085] Rejected strategy-injection attempts shall be journaled without logging unsafe code bodies in full.
- [ ] [REQ-STRAT-086] Rejected strategy-input diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code.
- [ ] [REQ-STRAT-088] Resource exhaustion by sanctioned strategy code, sanctioned indicator calls, or sanctioned data access shall fail deterministically with `STRATEGY_RESOURCE_LIMIT_EXCEEDED` or a more specific approved error code.
- [ ] [REQ-STRAT-102] Strategy security rejections must be journaled with safe redaction.
- [ ] [REQ-STRAT-118] Structured error result with deterministic error code on failure.
- [ ] [REQ-STRAT-124] Deprecated or revoked strategies shall fail deterministically before execution unless explicitly run in historical replay mode.
- [ ] [REQ-STRAT-130] The simulation or risk engine shall remain the final authority for official risk acceptance or rejection.
- [ ] [REQ-STRAT-141] Duplicate `intent_id` or idempotency key collisions shall fail deterministically.
- [ ] [REQ-STRAT-149] Strategy execution shall fail deterministically if required market data fields are missing, stale, out of order, duplicated, or timezone-inconsistent unless an explicit approved policy handles them.
- [ ] [REQ-STRAT-153] Strategy diagnostics shall support debug mode without exposing secrets, proprietary source, unsafe code bodies, or excessive market-data payloads.
- [ ] [REQ-STRAT-180] Strategy approval shall be invalidated if the source hash, artifact hash, dependency hash, or build provenance changes.
- [ ] [REQ-STRAT-183] The orchestration layer shall support deterministic failure policies: `FAIL_RUN`, `DISABLE_STRATEGY`, `SKIP_DECISION`, or `QUARANTINE_INSTANCE`.
- [ ] [REQ-STRAT-185] Corrupt, incompatible, or unauthorized checkpoints shall fail deterministically before execution.
- [ ] [REQ-STRAT-237] Strategies shall declare behavior when the data layer reports cross-venue price deviation, degraded data quality, failover, or unavailable data.
- [ ] [REQ-STRAT-239] Data vendor failover orchestration shall remain owned by the data or operations module.
- [ ] [REQ-STRAT-242] Recovery time objectives shall be defined for strategy restarts and failovers.
- [ ] [REQ-STRAT-252] Strategies shall declare assumptions for backup execution venues where applicable; backup venue failover enforcement remains owned by execution, live, or operations modules.
- [ ] [REQ-STRAT-263] Post-mortem documentation shall be required for strategy failures.
- [ ] [REQ-STRAT-324] Unknown strategy id shall fail before execution.
- [ ] [REQ-STRAT-325] Empty strategy identifier shall fail before execution with a deterministic validation error.
- [ ] [REQ-STRAT-326] Unapproved strategy module shall fail before execution.
- [ ] [REQ-STRAT-333] Raw arbitrary Python strategy code strings shall be rejected before execution.
- [ ] [REQ-STRAT-335] Unsafe rejected code bodies shall not be logged in full.
- [ ] [REQ-STRAT-336] Empty market-data input shall produce `STRATEGY_DATA_NOT_READY` or a more specific deterministic error.
- [ ] [REQ-STRAT-338] Indicator module timeout, unavailable dependency, broken connection, or unhandled indicator exception shall map to `INDICATOR_MODULE_ERROR` with original exception details redacted.
- [ ] [REQ-STRAT-340] Timezone-naive, DST-ambiguous, or timezone-inconsistent data shall fail unless an approved normalization policy exists.
- [ ] [REQ-STRAT-341] Clock drift beyond the approved tolerance between strategy runtime, data feed, indicator outputs, or simulation clock shall fail closed with `STRATEGY_STALE_DATA`, checkpoint abort, or a more specific approved error code.
- [ ] [REQ-STRAT-346] Duplicate `intent_id`, duplicate idempotency key, or non-monotonic strategy-local sequence number shall fail deterministically.
- [ ] [REQ-STRAT-348] Attempted secret exposure in diagnostics, checkpoints, manifests, or rationale shall fail redaction validation.
- [ ] [REQ-STRAT-359] `SIM_ARBITRARY_CODE_REJECTED`
- [ ] [REQ-STRAT-361] `STRATEGY_INTERNAL_ERROR`
- [ ] [REQ-STRAT-366] `INDICATOR_MODULE_ERROR`
- [ ] [REQ-STRAT-367] `STRATEGY_CHECKPOINT_INVALID`
- [ ] [REQ-STRAT-381] `STRATEGY_DATA_QUALITY_GATE_FAILED`
- [ ] [REQ-STRAT-389] Every confirmed error code shall have at least one focused failure-path test that triggers the code and verifies the full response or diagnostic shape.
- [ ] [REQ-STRAT-403] AI Tool strategy security tests shall verify `run_backtest` rejects raw arbitrary Python strategy code, returns `SIM_ARBITRARY_CODE_REJECTED`, does not execute rejected code, and does not log rejected code in full.
- [ ] [REQ-STRAT-413] Strategy tests shall include scenario tests for session boundaries, holidays, weekend gaps, DST transitions, spread spikes, partial fills, rejected fills, and multi-timeframe bar closure.
- [ ] [REQ-STRAT-014] Each confirmed error code shall have at least one triggering scenario and a stable diagnostic shape before implementation acceptance.
#### `app/services/strategies/vectorized.py`

Functions/classes:
- `run_vectorized_strategy_signals`
- `TradeIntent`
- `MULTIPROCESS_ISOLATED`

Requirements:
- [ ] [REQ-STRAT-004] Each public capability shall define whether results are returned as a single batch, iterator, stream, or async stream; `run_vectorized_strategy_signals` shall be treated as batch output until a streaming contract is explicitly approved.
- [ ] [REQ-STRAT-029] The module shall support vectorized signal strategies.
- [ ] [REQ-STRAT-031] Vectorized signal strategies shall compute indicators, generate signals, and convert signals to timestamped `TradeIntent` objects before simulation execution.
- [ ] [REQ-STRAT-053] Vectorized signal generation shall shift current-bar conditions so that bar-open entries are based on previous closed-bar values.
- [ ] [REQ-STRAT-060] If a vectorized batch detects lookahead at any element, the entire batch shall fail atomically, emit `STRATEGY_LOOKAHEAD_DETECTED`, discard intents produced by that batch, and preserve a diagnostic identifying the first failing timestamp.
- [ ] [REQ-STRAT-061] A vectorized batch decision clock shall be anchored to the supplied `StrategyExecutionContext.decision_timestamp`; wall-clock elapsed time during long-running batches shall not advance decision-time semantics.
- [ ] [REQ-STRAT-098] Vectorized processing is allowed only for indicator and signal generation.
- [ ] [REQ-STRAT-170] CPU-bound vectorized strategies shall run in isolated worker processes when their declared execution profile is `MULTIPROCESS_ISOLATED`, when configured by orchestration, or when measured event-loop latency exceeds the approved threshold for the target environment.
- [ ] [REQ-STRAT-292] Vectorized strategies shall calculate indicators in a vectorized manner where supported by the indicator module.
- [ ] [REQ-STRAT-293] Vectorized strategies shall generate signals in a vectorized manner before conversion to timestamped `TradeIntent` objects.
- [ ] [REQ-STRAT-294] Vectorized processing shall not bypass tick-accurate simulation execution, fill modeling, accounting, margin checks, risk checks, or journal generation.
- [ ] [REQ-STRAT-300] Hook execution order shall be deterministic and documented for vectorized runs, event-driven runs, replay, checkpoint restore, and shutdown.
- [ ] [REQ-STRAT-433] Documentation shall include examples for vectorized signal strategies and event-driven strategies.
- [ ] No file-specific non-functional requirements defined.
- [ ] [REQ-STRAT-342] Clock drift detected during a long-running vectorized batch shall not change the batch decision timestamp; the batch shall either complete under the original timestamp or fail atomically according to the configured clock-drift policy.
- [ ] [REQ-STRAT-394] Strategy tests shall cover vectorized signal strategies.
- [ ] [REQ-STRAT-358] `STRATEGY_LOOKAHEAD_DETECTED`
- [ ] [REQ-STRAT-406] Strategy tests shall include property-based tests for no-lookahead, deterministic replay, and risk-envelope invariants.
- [ ] [REQ-STRAT-407] Property-based no-lookahead tests shall cover timezone offsets, DST gaps, DST overlaps, session boundaries, late-arriving data, revised bars, and multi-timeframe closure boundaries.
- [ ] [REQ-STRAT-432] Documentation shall describe no-lookahead strategy timing.
#### `app/services/strategies/event.py`

Functions/classes:
- `FILL_UPDATE`
- `PARTIAL_FILL`
- `TradeIntent`
- `decision_id`
- `ASYNC_AWAIT`
- `SYNC_BLOCKING`

Requirements:
- [ ] [REQ-STRAT-026] Strategies shall not directly create official fills, deals, journal events, or reports.
- [ ] [REQ-STRAT-030] The module shall support stateful event strategies.
- [ ] [REQ-STRAT-032] Event strategies shall respond to initialization, bar-open, tick, and trade-transaction events through controlled interfaces.
- [ ] [REQ-STRAT-033] `INTRABAR_EVENT` strategies may use current tick data only through approved event interfaces.
- [ ] [REQ-STRAT-040] Event strategies shall support `FILL_UPDATE` or `PARTIAL_FILL` events to react to incomplete executions through approved read-only execution-state interfaces.
- [ ] [REQ-STRAT-094] Strategy-local state updates shall be atomic per decision event or shall fail with a deterministic rollback diagnostic.
- [ ] [REQ-STRAT-095] Read-only external state supplied to a strategy shall be an immutable snapshot or shall carry a documented consistency model preventing races with concurrent simulation, risk, portfolio, or data updates.
- [ ] [REQ-STRAT-111] Optional read-only simulation state for event strategies.
- [ ] [REQ-STRAT-135] Strategy risk profiles shall declare correlation assumptions during stress events.
- [ ] [REQ-STRAT-137] Every `TradeIntent` shall include a `decision_id` linking it to the strategy decision event that created it.
- [ ] [REQ-STRAT-152] Strategy metrics shall include intents emitted, intents suppressed, no-signal decisions, rejected decisions, invalid data events, lookahead detections, configuration validation failures, state checkpoint size, and per-event decision latency.
- [ ] [REQ-STRAT-168] Strategies shall not perform unbounded loops, unbounded recursion, unbounded memory growth, or unbounded history scans during event execution.
- [ ] [REQ-STRAT-171] Event strategies shall be reentrant or explicitly marked single-threaded.
- [ ] [REQ-STRAT-201] Simultaneous events shall be processed using a stable deterministic ordering policy.
- [ ] [REQ-STRAT-229] Wash trade prevention rules shall be declared.
- [ ] [REQ-STRAT-283] Strategies shall declare behavior during `AUCTION_PHASE`, `TRADING_HALT`, `CROSSING_SESSION`, and `BROKEN_MARKET` microstructure events.
- [ ] [REQ-STRAT-295] Event strategies shall implement a standard lifecycle interface where applicable.
- [ ] [REQ-STRAT-296] The standard event strategy lifecycle interface shall include hooks such as `on_init`, `on_start`, `on_bar`, `on_tick`, `on_fill_update`, `on_partial_fill`, `on_order_update`, `on_timer`, `on_error`, `on_checkpoint`, `on_restore`, and `on_stop`.
- [ ] [REQ-STRAT-310] Strategy execution shall define measurable latency, memory, checkpoint-size, diagnostic-payload-size, event-queue, timeout, and retry-exhaustion limits per supported environment before implementation acceptance.
- [ ] [REQ-STRAT-315] Strategy execution shall define deterministic backpressure behavior when event volume exceeds configured capacity.
- [ ] [REQ-STRAT-319] `ASYNC_AWAIT` strategies shall define an approved async compatibility contract and shall not block the event loop.
- [ ] [REQ-STRAT-320] `SYNC_BLOCKING` strategies shall define maximum call duration and isolation expectations before being used in shared event loops.
- [ ] No file-specific non-functional requirements defined.
- [ ] [REQ-STRAT-349] Simultaneous events for a single strategy instance shall be processed in a stable documented order, such as timestamp, event type priority, then deterministic sequence number.
- [ ] [REQ-STRAT-395] Strategy tests shall cover stateful event strategies.
- [ ] [REQ-STRAT-409] Strategy tests shall include stress tests for large histories, many symbols, dense tick streams, and high-frequency event dispatch.
- [ ] [REQ-STRAT-415] Strategy tests shall include chaos engineering scenarios, including simulated data-feed disconnections, sudden latency spikes, and out-of-order message injection during event processing.
- [ ] [REQ-STRAT-416] Strategy tests shall verify memory leak detection over extended event-loop iterations and assert stable memory usage within approved thresholds.
- [ ] [REQ-STRAT-418] Boundary tests shall verify strategies cannot create fills, deals, official orders, reports, or journal events directly.
- [ ] [REQ-STRAT-425] Concurrency tests shall verify read-only state snapshot isolation and stable event ordering for simultaneous events.
- [ ] [REQ-STRAT-121] A strategy shall not execute in an environment higher than its approved lifecycle status.
- [ ] [REQ-STRAT-362] `STRATEGY_LIFECYCLE_NOT_APPROVED`
#### `app/services/strategies/sandbox.py`

Functions/classes:
- `STRATEGY_ENVIRONMENT_NOT_PERMITTED`

Requirements:
- [ ] [REQ-STRAT-078] The strategy input path shall accept only registered strategy identifiers, validated strategy configuration schemas, or code explicitly vetted and sandboxed by the orchestration layer.
- [ ] [REQ-STRAT-080] Code-based strategy execution shall remain disabled until sandbox policy, approval workflow, and prohibited-operation lists are approved.
- [ ] [REQ-STRAT-081] Sandboxed code-based strategy execution, if enabled later, shall require `simulation.admin` approval, strategy owner approval, sandbox profile id, vetting artifact hash, allowed capability list, audit record, and approval expiry.
- [ ] [REQ-STRAT-082] Sandbox policy shall define allowed imports, denied imports, filesystem access, network access, subprocess access, environment-variable access, timeouts, memory limits, and prohibited operations.
- [ ] [REQ-STRAT-100] Strategy execution shall occur only through registered strategies, validated schemas, or explicitly sandboxed and vetted orchestration paths.
- [ ] [REQ-STRAT-112] Sandbox and vetting metadata only when code-based strategy execution is explicitly permitted.
- [ ] [REQ-STRAT-279] Any attempt by a strategy to read environment variables not explicitly allowlisted in the sandbox profile shall emit `STRATEGY_ENVIRONMENT_NOT_PERMITTED`.
- [ ] [REQ-STRAT-431] Documentation shall describe sandbox and vetting requirements if code-based strategy execution is ever enabled.
- [ ] No file-specific non-functional requirements defined.
- [ ] [REQ-STRAT-334] Missing sandbox or vetting metadata for a code-based strategy path shall fail before execution.
- [ ] [REQ-STRAT-347] Sandbox approval expiry shall cause code-based strategy execution to fail before execution.
- [ ] [REQ-STRAT-360] `STRATEGY_SANDBOX_REQUIRED`
### Unit Tests Required

```text
tests/unit/app/services/strategies/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/04_strategies.py
```

Usage examples must show:
- `example_01_registry_and_templates`: Demonstrate strategy registration, template discovery, version constraints, and capability metadata.
- `example_02_config_validation`: Demonstrate JSON Schema config validation, invalid config errors, and safe defaults.
- `example_03_vectorized_signal_generation`: Demonstrate lookahead-free vectorized signal generation and signal metadata.
- `example_04_event_driven_lifecycle`: Demonstrate `on_init`, `on_bar`, `on_tick`, and state transition hooks without side effects.
- `example_05_strategy_state_and_provenance`: Demonstrate state serialization, parameter hashes, input checksums, and reproducibility metadata.
- `example_06_builtin_trend_following`: Demonstrate built-in trend-following strategy outputs and quality diagnostics.
- `example_07_builtin_random_walk`: Demonstrate RandomWalk strategy grids, scaling logic, and validation failures.
- `example_08_blocked_actions`: Demonstrate that strategies emit signals only and cannot place broker orders or approve risk.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 457 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(strategy-service): implement phase 4 strategy service requirements
```


- [ ] [REQ-STRAT-005] Each public capability shall define precise side effects, mutation permissions, idempotency behavior, concurrency assumptions, retry behavior, and redaction behavior.
- [ ] [REQ-STRAT-309] Strategy imports shall be side-effect safe and shall not perform broker calls, network access, filesystem writes, subprocess execution, environment mutation, or decision-time clock/randomness reads.
- [ ] [REQ-STRAT-420] Security tests shall verify strategy imports perform no broker calls, network calls, filesystem writes, subprocess calls, environment mutation, or secret reads.
## Phase 5 Risk Governance

### Goal

Implement the Risk Governance requirements under `app/services/risk/` while preserving the phase module boundaries and governance rules.

Task inventory: 678 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/risk/`.
- Requires Phase 4 Strategy Service contracts to be available where referenced by `05-risk.md`.

### Files to Create

```text
app/__init__.py
app/services/risk/__init__.py
app/services/risk/models.py
app/services/risk/governor.py
app/services/risk/limits.py
app/services/risk/sizing.py
app/services/risk/lifecycle.py
app/services/risk/kill_switch.py
app/services/risk/scenarios.py
app/services/risk/
app/services/governance
app/services/portfolio
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/risk/errors.py`

Functions/classes:
- `Error`
- `ValidationError`
- `ServiceError`

Requirements:
- [ ] Each portfolio-under-risk compatibility adapter shall document its owning external domain, side effects, storage boundary, and failure behavior.
- [ ] Portfolio-under-risk lazy service resolution shall raise `AttributeError` for unknown lazy service names.
- [ ] Audit write failure behavior shall be configurable.
- [ ] Live-readiness workflows shall fail closed when audit persistence is mandatory and unavailable.
- [ ] Exceptions shall be mapped to deterministic error codes, which must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
- [ ] Failures shall not be swallowed.
- [ ] The module shall prevent stale, revoked, tampered, or expired approval tokens from validating.
- [ ] Live-sensitive workflows shall hard-fail when audit chain integrity is required and verification fails.
- [ ] Timezone conversion failure shall fail closed for live workflows.
- [ ] Approval tokens shall expire deterministically and fail validation after expiry.
- [ ] Approval tokens shall support revocation and fail validation after revocation.
- [ ] Approval-token compatibility across config changes shall fail closed unless an explicit governed compatibility policy authorizes the exact old config hash, new config hash, action scope, and expiry.
- [ ] `PortfolioAuditService.audit` shall mark critical audit failure as disabling live trading when findings exist and severity is critical, and shall write an audit artifact.
- [ ] `CostService.report` shall aggregate cost by period, agent, provider, model, task, workflow, strategy, token usage, failed call cost, and backtest compute cost.
- [ ] Missing risk configuration entirely shall return `INVALID_RISK_CONFIG` immediately.
- [ ] Wrong type shall trigger invalid input handling.
- [ ] Zero account equity shall be invalid for percentage risk calculations.
- [ ] Inconsistent account currency shall trigger data-quality failure.
- [ ] Unsupported symbol or asset class shall trigger data-quality failure.
- [ ] Duplicate position identifiers shall trigger data-quality failure.
- [ ] Inconsistent position direction, quantity, or sign shall trigger data-quality failure.
- [ ] Invalid approval-token scope shall fail token validation.
- [ ] Missing or ambiguous pending-order execution policy when pending orders exist shall trigger configured failure behavior.
- [ ] Allocation confidence inputs that are missing or all zero shall not divide by zero.
- [ ] Portfolio service lazy lookup for an unknown service name shall raise `AttributeError`.
- [ ] Malformed JSON-like payloads shall return `INVALID_INPUT` through official AI tools.
- [ ] Oversized payloads shall return `PAYLOAD_TOO_LARGE` or `INVALID_INPUT` before expensive calculation begins.
- [ ] Audit persistence partial write shall fail closed when audit persistence is mandatory.
- [ ] Permission-denied responses from governance, audit, or token backends shall fail closed for live-sensitive workflows.
- [ ] The risk module shall use deterministic error codes, including:
- [ ] `INVALID_INPUT`
- [ ] `INVALID_RISK_CONFIG`
- [ ] `APPROVAL_TOKEN_INVALID`
- [ ] `MISSING_STOP_LOSS`
- [ ] `CALCULATION_FAILED`
- [ ] `SNAPSHOT_BUILD_FAILED`
- [ ] `REPORT_GENERATION_FAILED`
- [ ] `STORAGE_ERROR`
- [ ] `TOOL_EXECUTION_FAILED`
- [ ] `UNKNOWN_ERROR`
- [ ] Unknown exceptions shall be logged and converted into `TOOL_EXECUTION_FAILED` or `UNKNOWN_ERROR`.
- [ ] External dependency failures shall not result in silent success.
- [ ] Approval tests shall prove clock-skewed token expiry fails closed according to configured tolerance.
- [ ] Tool-standard tests shall verify every official AI tool has one success example and one failure example.
- [ ] Error code documentation shall exist.
- [ ] Portfolio workflow artifacts should have explicit retention, redaction, and artifact-write failure behavior before production use.
- [ ] Approval tokens shall fail closed across config changes unless an explicit compatibility policy marks the old and new config hashes as equivalent for the same action scope.

#### `app/services/risk/README.md`

Functions/classes:
- No runtime functions/classes; documentation artifact only.

Requirements:
- [ ] Documentation tests shall verify each risk file and top-level public member has a module or member docstring.
- [ ] Before Builder handoff, the current checkbox inventory shall be converted into a numbered requirements catalogue with stable `RISK-FR-*`, `RISK-NFR-*`, `RISK-SEC-*`, `RISK-EDGE-*`, `RISK-TEST-*`, `RISK-DOC-*`, and `RISK-COMPAT-*` identifiers.
- [ ] `README.md` shall explain risk module responsibilities.
- [ ] Tool catalog shall document official tools.
- [ ] Config documentation shall explain thresholds.
- [ ] Workflow documentation shall explain risk gates.
- [ ] A traceability table shall map each business rule to its owning FR, NFR, security, test, or documentation requirement.
- [ ] Documentation review shall be complete before production promotion.
- [ ] A requirements traceability table shall map each business rule to its owning FR, NFR, security, test, or documentation requirement before production promotion.

#### `app/__init__.py`

Functions/classes:
- `trace_id`

Requirements:
- [ ] `app/services/risk/__init__.py` shall expose only symbols intentionally classified as `official_ai_tool`, `public_python_contract`, `deterministic_service`, or `legacy_compatibility_export`.
- [ ] `app/services/risk/__init__.py` shall use `__all__` as the strict public export registry.
- [ ] Portfolio-under-risk compatibility shall preserve package-level traceability for `app.services.portfolio.__init__`, `app.services.portfolio.__all__`, and `app.services.portfolio.standard_tools` when portfolio remains exposed as a workflow-facing package under risk governance.
- [ ] `ScenarioDefinition`
- [ ] The risk module shall reject NaN, Infinity, non-finite Decimal values, and values outside configured numeric bounds for all public contracts.
- [ ] Non-positive-semidefinite correlation matrices shall be detected and either sanitized through a documented deterministic method or rejected as a data-quality failure according to profile configuration.
- [ ] The risk domain shall expose only approved official AI tools through `app/services/risk/__init__.py`.
- [ ] Structured logs, metrics, and audit records shall include a `correlation_id` or `trace_id` propagated from the initial agent or API request through the risk decision and audit chain.
- [ ] The root package initializer shall remain limited to import/export exposure and shall not contain business implementation.
- [ ] No file-specific non-functional requirements defined.
- [ ] NaN, Infinity, and non-finite Decimal values shall be rejected.
- [ ] Contract tests shall prove public contracts reject NaN, Infinity, malformed payloads, unknown enum values, and out-of-range numeric values.
- [ ] Correlation tests shall cover non-positive-semidefinite matrix handling, including deterministic sanitization or configured data-quality rejection.
- [ ] Package-initializer tests shall verify `app.services.risk.__init__` has no business implementation beyond import/export exposure.
- [ ] Portfolio-under-risk tests shall verify `app.services.portfolio.__init__` has no business implementation beyond package exposure, `app.services.portfolio.__all__` remains unique and aligned with the expected exported tool surface, and `app.services.portfolio.standard_tools` carries required tool documentation and envelope behavior.
#### `app/services/risk/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/risk/models.py`

Functions/classes:
- `Request`
- `Response`
- `Result`
- `Config`

Requirements:
- [ ] The risk module shall not train models.
- [ ] `CostService.report` shall flag budget exceeded and protected decision types routed to non-deterministic models, require high-cost workflow approval when budget is exceeded, and write a cost audit artifact.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Public contracts use Pydantic V2; frozen dataclasses are limited to internal immutable calculation helpers.
- [ ] Risk thresholds and profiles are config-driven and stored under `configs/risk/*.yaml`.
- [ ] Risk module production readiness is requirement-first: requirement -> contract -> deterministic implementation -> unit test -> workflow test -> audit evidence -> acceptance gate.
- [ ] The production benchmark environment is `RISK_BENCHMARK_PROFILE_V1`.
- [ ] If `RISK-PEND-001` is unresolved, live-sensitive pre-trade approval shall fail closed with `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED` unless refreshed `PortfolioState` evidence includes pending orders or pending approvals.
- [ ] If `RISK-PEND-003` is unresolved, live-sensitive `high_volatility` or `crisis` regime decisions that require stressed correlation, VaR, or CVaR shall return `needs_more_evidence` or `block` rather than falling back to ordinary lookbacks.
- [ ] If `RISK-PEND-004` is unresolved, crisis-reference-dependent live decisions shall fail closed as missing evidence.
- [ ] If `RISK-PEND-005` is unresolved, historical VaR shall remain the only production-live default and non-historical parametric VaR shall require explicit profile configuration plus approval.
- [ ] If `RISK-PEND-006` is unresolved, Gaussian parametric VaR in production-live workflows shall return `needs_approval` or `block` according to profile and shall emit `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
- [ ] Recommendations remain non-mandatory until promoted by owner or architecture decision.
- [ ] Future ambiguity shall be added as a new requirements decision item with owner, target section, and production-readiness impact instead of as an open-ended question.
- [ ] Pending: confirm whether crisis-period references are configured profiles, evidence-pack inputs, or implementation fixtures.
- [ ] Every exported symbol shall be classified as one of `official_ai_tool`, `public_python_contract`, `deterministic_service`, `internal_helper`, or `legacy_compatibility_export`.
- [ ] Every official AI tool shall accept `request_id: Optional[str] = None`.
- [ ] Every official AI tool shall return the standard HaruQuant tool response schema.
- [ ] `review_allocation_proposal`
- [ ] `create_risk_decision_package`
- [ ] The current implementation support surface shall include risk request assembly through `RiskRequestAssemblyContext` and `assemble_risk_assessment_request`.
- [ ] The current implementation support surface shall include threshold/config helpers through `load_risk_thresholds`, `config_version_hash`, `validate_threshold_schema`, and `validate_config_hash`.
- [ ] The current implementation support surface shall include metric and scorecard contracts through `MetricRow`, `MetricContext`, `MetricFamily`, `RiskSnapshot`, `MetricRegistry`, `ScoreRow`, `ScoreContext`, `ScoreFamily`, `RiskScorecard`, `ScoreRegistry`, `RiskSnapshotEngine`, `RiskScorecardEngine`, and `RecommendationEngine`.
- [ ] The current implementation support surface shall include decision, signature, approval, validity, and audit helpers through `compose_risk_decision`, `pack_risk_decision_rationale_and_provenance`, `create_approval_token`, `validate_approval_token`, `stable_hash`, `sign_payload`, `invalidate_for_material_proposal_change`, `enforce_risk_decision_expiry`, and `write_risk_audit`.
- [ ] The current implementation support surface shall include reporting and persistence contracts for risk snapshots, scenario results, replay outputs, Markdown reports, JSON reports, decisions, snapshot bundles, and scenario stores.
- [ ] Portfolio-under-risk compatibility is transitional; the long-term target is a separate `app/services/portfolio` domain where Risk consumes read-only portfolio evidence and emits risk decisions through stable interfaces.
- [ ] Transitional compatibility facades shall emit deprecation warnings or deprecation metadata in public docs, tool metadata, or runtime diagnostics where applicable.
- [ ] `RiskDecisionPackage`
- [ ] The risk module shall define a canonical decision-state enum containing `approve`, `warn`, `needs_approval`, `needs_more_evidence`, `reject`, `block`, and `error`.
- [ ] The risk module shall define a canonical limit-status enum containing `pass`, `warn`, `needs_more_evidence`, `fail`, and `blocked`.
- [ ] Public Pydantic V2 model configuration shall set `allow_inf_nan=False` for public request, response, config, snapshot, decision, approval-token, audit, and tool contracts.
- [ ] The risk module shall expose a deterministic schema/version identifier for every public request and response contract.
- [ ] Time-sensitive contracts and services shall accept an injected time provider or explicit `now` datetime for deterministic tests, scenario replay, and audit reproduction.
- [ ] The risk module shall produce the same `RiskDecisionPackage` for the same inputs, configuration hash, and dependency versions.
- [ ] All material decisions shall include enough metadata to reproduce the decision later.
- [ ] Config changes shall create a new config hash visible in snapshots, decisions, approvals, and reports.
- [ ] Markdown report generation from a completed decision package shall complete within 1 second p95.
- [ ] The module shall define maximum accepted payload sizes for public tools and return `PAYLOAD_TOO_LARGE` or `INVALID_INPUT` for oversized requests before expensive calculation begins.
- [ ] Public official Risk tools shall reject payloads larger than 1 MiB by default unless an owner-approved profile sets a lower limit.
- [ ] Non-critical reporting failures shall not silently hide risk decisions.
- [ ] External dependency failure shall be represented as `needs_more_evidence`, `reject`, or `block`, never as silent success.
- [ ] The module shall define timeout behavior for governance, audit storage, token state backend, config loading, and evidence-provider calls.
- [ ] Risk tools shall declare accurate risk metadata and side-effect flags.
- [ ] Every material risk decision shall emit structured logs with request id, workflow id, decision status, reason codes, and execution time.
- [ ] Every material risk decision shall be serializable as an audit record.
- [ ] Audit records shall include evidence references, config hash, input summary, limit results, approval state, and final decision.
- [ ] Observability metrics shall include decision count, block count, reject count, approval-required count, latency, calculation failures, and missing-evidence events.
- [ ] Audit hash-chain verification shall complete before live-sensitive decisions when configured as mandatory.
- [ ] The module shall use Pydantic V2 for all public request, response, config, snapshot, decision, approval-token, audit, and tool contracts.
- [ ] Frozen dataclasses may be used only for internal immutable calculation structures and shall not replace public Pydantic contracts.
- [ ] Public contracts shall be versioned when downstream workflows depend on them.
- [ ] Official AI tools shall not be added without tests, usage examples, metadata, and registry review.
- [ ] Concurrent risk decisions shall not share mutable request state, cached intermediate values, approval-token state, or audit buffers unless explicitly synchronized and tested.
- [ ] Any cache used by the risk module shall be keyed by input evidence version, config hash, and dependency version and shall be safe for concurrent reads/writes.
- [ ] The module shall use HMAC or stronger signing for approval-token tamper evidence.
- [ ] The risk module shall enforce least privilege: readiness decisions only, no execution.
- [ ] The risk module shall own portfolio-level risk decisions.
- [ ] The risk module shall emit execution-blocking decisions and risk-owned block state, but it shall not directly disable broker orders, cancel orders, close positions, or mutate execution controls.
- [ ] The risk module shall not own or cache long-term historical market data; it shall consume point-in-time snapshots and bounded evidence packs from external evidence providers.
- [ ] The risk module shall explicitly mark unavailable snapshot fields as missing evidence rather than inventing defaults.
- [ ] The risk module shall include `request_id`, `workflow_id`, `as_of`, `config_hash`, and evidence references in every material snapshot or decision package.
- [ ] The risk module shall verify stored config hash compatibility before applying a previous decision or approval token; mismatches shall return `CONFIG_VERSION_MISMATCH` and require a new decision.
- [ ] The risk module shall block or request evidence when required FX conversion rates are unavailable for material decisions.
- [ ] Conversion assumptions shall appear in snapshot metadata and audit records.
- [ ] Missing material conversion rates shall fail closed for live-readiness decisions.
- [ ] Maximum daily loss percentage shall define its equity base explicitly in each risk profile; if the base is missing for live profiles, config validation shall return `INVALID_RISK_CONFIG`.
- [ ] The risk module shall calculate margin required for current positions and proposed trades when contract size, leverage, price, and currency data are available.
- [ ] The risk module shall fail closed when required broker symbol metadata is missing for live-readiness or pre-trade decisions.
- [ ] Historical VaR shall be the default VaR method for production live workflows unless an explicitly approved profile config selects another method.
- [ ] If Gaussian parametric VaR is used, the decision or calculation result shall emit `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
- [ ] The risk module shall reject or request more evidence when return history is insufficient for configured VaR/CVaR requirements.
- [ ] The minimum data points for VaR/CVaR sufficiency shall be explicit in each risk profile; missing production-live values shall return `INVALID_RISK_CONFIG`.
- [ ] The risk module shall expose calculation assumptions in snapshot metadata, including lookback, confidence level, method, and data coverage.
- [ ] The risk module shall handle missing or insufficient correlation data explicitly as missing evidence.
- [ ] The risk module shall accept spread, slippage, session, liquidity, and economic-calendar context as external evidence.
- [ ] The risk module shall enforce high-impact-news blackout windows when calendar evidence is supplied; the default baseline is 10 minutes before and 10 minutes after high-impact events.
- [ ] The risk module shall treat missing required news/calendar evidence according to configured mode: `ignore`, `warn`, `needs_more_evidence`, or `block`.
- [ ] Weekend, overnight, restricted-session, and news-blackout rules shall have a concrete configuration schema before Builder implementation.
- [ ] The risk module shall create tamper-evident approval tokens for approval-required decisions.
- [ ] Approval tokens shall include request id, workflow id, approved action, approver, expiry, config hash, decision hash, scope, and nonce or single-use identifier.
- [ ] Approval tokens shall be bound to the decision, account, strategy, symbol/action scope, and config hash they were created for.
- [ ] Token validation shall verify schema, signature, expiry, revocation, action type, scope, decision hash, config hash or approved config compatibility, nonce or single-use state, authorized approver, and required audit write.
- [ ] The risk module shall generate human-readable Markdown risk reports from snapshots, decisions, and scenario outputs.
- [ ] Risk reports shall separate evidence, calculations, assumptions, warnings, decisions, and recommendations.
- [ ] Risk reports shall not claim live approval unless a valid approval token and risk decision exist.
- [ ] The risk module shall support deterministic regime transitions with timestamp, previous regime, new regime, reason, and evidence references.
- [ ] The risk module shall expose regime state in snapshots, risk reports, audit records, and decision packages.
- [ ] The regime layer shall fail closed for live-sensitive workflows when required regime evidence is missing and policy requires it.
- [ ] For live pre-trade review in `high_volatility` or `crisis` regimes, correlation calculations shall use stressed lookback evidence or configured stressed assumptions instead of the standard recent lookback.
- [ ] For live pre-trade review in `high_volatility` or `crisis` regimes, VaR and CVaR calculations shall use stressed assumptions, stressed lookback evidence, or explicit crisis-period evidence.
- [ ] Stressed lookback policy shall support configurable crisis references or maximum-observed-correlation style evidence over an approved historical window.
- [ ] `ReportingService.generate` shall generate portfolio performance reports, mark reports incomplete when required fields or execution evidence are missing, include critical audit or risk findings in decision-required output, and write a performance report artifact.
- [ ] The risk module shall validate live portfolio-state freshness for production live workflows and return `needs_more_evidence` or `block` when state is stale beyond configured tolerance.
- [ ] The risk module shall disclose `in_flight_tolerance_used` in decision metadata when used.
- [ ] Missing required field shall trigger invalid input, evidence request, warning, reject, or block according to workflow policy.
- [ ] Stale `as_of` timestamps shall trigger stale-evidence handling.
- [ ] Insufficient return history shall reject or request more evidence for VaR/CVaR.
- [ ] Insufficient correlation overlap shall be handled explicitly as missing evidence or configured fallback.
- [ ] Missing symbol metadata shall fail closed for live-readiness or pre-trade decisions.
- [ ] Missing FX conversion rates shall fail closed for material live-readiness decisions.
- [ ] Insufficient ATR/volatility evidence shall emit `INSUFFICIENT_VOLATILITY_EVIDENCE`.
- [ ] Insufficient Kelly trade sample evidence shall emit `INSUFFICIENT_K_EVIDENCE`.
- [ ] Live pre-trade review in `high_volatility` or `crisis` regimes shall not silently use ordinary correlation, VaR, or CVaR lookbacks when stressed evidence is required.
- [ ] Protected decision task routed to a non-deterministic model shall be flagged as a cost governance anomaly.
- [ ] Performance report missing portfolio PnL, drawdown, trade count, audit evidence, or execution logs shall be marked incomplete.
- [ ] Unreadable or corrupted persisted step-down state shall return `needs_more_evidence` or `block` for live-sensitive workflows according to config.
- [ ] In-flight reconciliation grace-period expiry shall emit `IN_FLIGHT_RECONCILIATION_EXPIRED` and require forced portfolio-state refresh before live-sensitive decision.
- [ ] Clock skew beyond configured tolerance shall trigger stale-evidence or token-validation failure.
- [ ] `MISSING_EVIDENCE`
- [ ] `STALE_EVIDENCE`
- [ ] `INSUFFICIENT_VOLATILITY_EVIDENCE`
- [ ] `INSUFFICIENT_K_EVIDENCE`
- [ ] Contract tests shall validate all public contracts and invalid payloads.
- [ ] Contract tests shall prove every official AI tool returns the standard envelope with `status`, `message`, `data`, `error`, and `metadata` on success.
- [ ] Contract tests shall prove every official AI tool returns deterministic error envelopes for invalid input, missing evidence, hard block, approval required, domain exceptions, and tool execution failure.
- [ ] Contract tests shall prove public contracts preserve Decimal precision during validation and JSON serialization without implicit float conversion.
- [ ] Regime tests shall cover classification, transitions, missing evidence, and limit multipliers.
- [ ] Failure tests shall cover missing evidence, stale evidence, dependency failure, and audit failure.
- [ ] Portfolio-under-risk tests shall cover `PortfolioAuditService.audit`, `IncidentService.create_incident`, `CostService.report`, and `ReportingService.generate`, including artifact references and missing-evidence behavior.
- [ ] Profile fixture tests shall cover `prop_firm_default`, `paper`, and `live_conservative` default thresholds and documented overrides.
- [ ] Concurrency tests shall prove concurrent pre-trade requests cannot double-spend in-flight tolerance or pending approval capacity.
- [ ] Integration tests shall cover governance service unavailable during approval-required decisions.
- [ ] VaR/CVaR tests shall prove parametric VaR defaults to a heavy-tailed distribution when used in production-live profiles.
- [ ] All FR and NFR requirements shall have test evidence or explicit deferral notes.
- [ ] Performance benchmarks shall be measured with hardware/reference-environment metadata.
- [ ] Usage examples shall include one happy-path response envelope for a normal approved or warning-only advisory decision.
- [ ] Usage examples shall include response examples for `approve`, `reject`, `block`, `needs_more_evidence`, `needs_approval`, and `error` states.
- [ ] Before Builder handoff, every official Risk tool shall have a public contract covering purpose, classification, stability, required inputs, optional inputs, output `data` schema, status values, error codes, warning codes, side-effect metadata, network behavior, persistence behavior, and success/failure examples.
- [ ] Before Builder handoff, every pending production decision shall be resolved, explicitly deferred, or assigned an owner-approved safe default.
- [ ] No live-production Risk workflow shall depend on an unresolved `Pending:` production decision.
- [ ] Config documentation shall identify `configs/risk/*.yaml` as the canonical risk config path and document `prop_firm_default`, `paper`, and `live_conservative` profiles.
- [ ] Workflow documentation shall explain concurrent pre-trade request behavior and the owner of double-spend prevention.
- [ ] Benchmark documentation shall define `RISK_BENCHMARK_PROFILE_V1` and required benchmark manifest fields.
- [ ] Risk reports shall separate observed evidence, calculated metrics, limit results, assumptions, warnings, decisions, and approval requirements.
- [ ] Risk decision reports shall include plain-language explanations for primary `reject` or `block` reasons.
- [ ] Risk thresholds and profiles shall be stored under `configs/risk/*.yaml`.
- [ ] Production profile examples shall include `configs/risk/prop_firm_default.yaml`, `configs/risk/paper.yaml`, and `configs/risk/live_conservative.yaml`.
- [ ] Pydantic V2 shall be the standard implementation for public contracts.
- [ ] Frozen dataclasses may be used internally for immutable performance-critical calculation steps when they do not replace public Pydantic contracts.
- [ ] Default baselines such as 5% maximum daily loss, 10% maximum total loss, 10% monthly profit target tracking, 95% VaR, and 0.50 FX correlation threshold shall apply to `prop_firm_default` and `live_conservative` profiles.
- [ ] The `paper` profile shall keep the same default thresholds unless a documented paper-only override is configured.
- [ ] The `research` profile may relax, warn, or disable selected production baselines, but relaxed settings shall never be inherited by live workflows.
- [ ] Acceptance fixtures shall exist for `prop_firm_default`, `paper`, and `live_conservative` profiles.
- [ ] Governance ownership shall remain in an external `app/services/governance` domain or governance service accessed through stable public interfaces; the risk module shall consume governance decisions and persist risk-owned audit facts through those interfaces without owning enterprise governance policy.
- [ ] The production benchmark profile shall be `RISK_BENCHMARK_PROFILE_V1`: Python 3.12+, 8 vCPU minimum, 32 GB RAM minimum, NVMe SSD, release build settings, no debugger, and no unrelated heavy background workload.
- [ ] Benchmark manifests shall record OS, CPU model, logical CPU count, RAM, storage type, Python version, dependency lock hash, git commit, dataset hash, warm/cold cache state, and benchmark profile id.
- [ ] Approval-token compatibility exceptions shall require authorized governance approval, bounded expiry, audit evidence, and deterministic compatibility metadata.
- [ ] Final risk gates shall be deterministic code decisions; LLM agents may explain, summarize, or recommend but shall not make final safety-critical decisions.
- [ ] The module shall produce one canonical `RiskDecisionPackage` for approvals, rejections, warnings, and approval-required states.
- [ ] Missing evidence, invalid state, missing approval, unclear policy, or calculation failure shall block or reject instead of guessing.
- [ ] Limit aggregation shall follow: `blocked > fail > needs_more_evidence > warn > pass`.
- [ ] Approval shall be required for live trading requests, promotion to live candidate, risk budget increases, allocation increases beyond threshold, configured warning overrides, and high-risk or critical state transitions.
- [ ] Either Risk shall reserve pending approval capacity, or Execution/Governance shall serialize requests or update state before subsequent checks.
- [ ] Strategy/Research workflow user: may request advisory risk reviews and strategy admission checks.
- [ ] Simulation/Paper/Live workflow caller: may request mode-specific risk decisions.
- [ ] Execution/Governance layer: shall serialize pre-trade requests or update `PortfolioState` with pending orders when Risk does not own a pending-approval reservation cache.
- [ ] Governance/audit service: may provide approval state, audit persistence, and policy metadata through stable public interfaces.
- [ ] Risk Agent shall not invent missing evidence.
#### `app/services/risk/governor.py`

Functions/classes:
- `check_max_drawdown_limit`
- `check_daily_loss_limit`
- `check_strategy_loss_limit`
- `check_portfolio_exposure_limit`
- `check_symbol_exposure_limit`
- `check_currency_exposure_limit`
- `check_correlation_limit`
- `check_var_limit`
- `check_cvar_limit`
- `check_leverage_limit`
- `check_margin_limit`
- `check_news_blackout`
- `check_spread_limit`
- `check_slippage_limit`
- `check_trade_frequency_limit`
- `check_kill_switch_state`
- `run_risk_governor_checks`
- `RiskProposal`
- `RiskApprovalToken`
- `RiskGovernorDecision`
- `RiskMemo`
- `RiskAssessmentRequest`
- `AccountState`
- `MarketState`
- `SymbolState`
- `PositionState`
- `PortfolioState`
- `MarketSnapshot`
- `AccountSnapshot`
- `PortfolioSnapshot`
- `RiskPolicy`
- `CorrelationPreference`
- `OverrideRecord`
- `CircuitBreakerState`
- `BudgetUtilization`
- `GovernanceState`
- `PolicyEngine`
- `PolicyScope`
- `PolicyVersion`
- `PolicyBundle`
- `PolicyEnforcementResult`
- `PolicyResolutionQuery`
- `PolicyResolver`
- `RiskGovernor`
- `GovernanceEngine`
- `ProposedTrade`
- `RiskDecisionPackage`

Requirements:
- [ ] `run_portfolio_risk_governor`
- [ ] Current governor-check exports shall include `check_max_drawdown_limit`, `check_daily_loss_limit`, `check_strategy_loss_limit`, `check_portfolio_exposure_limit`, `check_symbol_exposure_limit`, `check_currency_exposure_limit`, `check_correlation_limit`, `check_var_limit`, `check_cvar_limit`, `check_leverage_limit`, `check_margin_limit`, `check_news_blackout`, `check_spread_limit`, `check_slippage_limit`, `check_trade_frequency_limit`, `check_kill_switch_state`, and `run_risk_governor_checks`.
- [ ] The current implementation support surface shall include domain contracts for `RiskProposal`, `RiskApprovalToken`, `RiskGovernorDecision`, `RiskMemo`, `RiskAssessmentRequest`, `AccountState`, `MarketState`, `SymbolState`, `PositionState`, `PortfolioState`, `MarketSnapshot`, `AccountSnapshot`, and `PortfolioSnapshot`.
- [ ] The current implementation support surface shall include policy and governance contracts through `RiskPolicy`, `CorrelationPreference`, `OverrideRecord`, `CircuitBreakerState`, `BudgetUtilization`, `GovernanceState`, `PolicyEngine`, `PolicyScope`, `PolicyVersion`, `PolicyBundle`, `PolicyEnforcementResult`, `PolicyResolutionQuery`, `PolicyResolver`, `RiskGovernor`, and `GovernanceEngine`.
- [ ] The risk module shall review every proposed trade through a canonical `ProposedTrade` contract before execution.
- [ ] The risk module shall return one canonical `RiskDecisionPackage` for each pre-trade review.
- [ ] The risk module shall calculate projected exposure, margin, drawdown, VaR/CVaR, concentration, and correlation impact when evidence is available.
- [ ] The risk module shall return `approve` only when all required hard limits pass and no unresolved blocking evidence exists.
- [ ] The risk module shall return `reject` or `block` for hard-limit breaches, active kill-switch states, invalid input, or missing mandatory live-readiness evidence.
- [ ] The risk module shall return `needs_more_evidence` when configured mandatory evidence is missing but the action is not automatically prohibited.
- [ ] The risk module shall return `needs_approval` when a deterministic policy permits exception handling but requires approval.
- [ ] The risk governor shall validate request, portfolio state, and risk configuration before evaluating risk.
- [ ] The risk governor shall check kill switch before final approval.
- [ ] The risk governor shall run required limit checks and missing/stale evidence checks.
- [ ] The risk governor shall determine approval requirements and attach approval tokens only when policy permits.
- [ ] The risk governor shall emit audit event metadata for material decisions.
- [ ] The pre-trade risk workflow shall prevent concurrent double-spending of in-flight tolerance buffers when simultaneous requests use the same portfolio state.
- [ ] The production architecture shall choose exactly one double-spend prevention owner before Builder handoff: Risk-owned pending-approval reservation cache or external Execution/Governance serialization.
- [ ] The selected double-spend prevention owner shall be recorded in configuration and documentation.
- [ ] If no double-spend prevention owner is configured for live workflows, pre-trade approval shall fail closed with `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`.
- [ ] If double-spend prevention is externalized, Execution/Governance shall update `PortfolioState` with pending orders or pending approvals before later risk checks.
- [ ] The risk module shall reject or block simultaneous approvals that would collectively breach configured limits while relying on the same stale `PortfolioState`.
- [ ] Pre-trade review output shall disclose whether pending approval capacity, in-flight tolerance, or external serialization evidence was used.
- [ ] `LifecycleService.transition` shall require board approval and risk-governor compatibility for micro-live and live transitions.
- [ ] Position sizing shall not approve trades; the governor shall review sized trades before they are approved, rejected, blocked, or marked approval-required.
- [ ] `PortfolioKillSwitch.evaluate` shall trigger when critical audit failure, unavailable risk governor, unavailable audit logging, failed broker heartbeat, daily or weekly loss breach, account or strategy drawdown breach, spread spike, slippage spike, or repeated order failures are detected.
- [ ] Scenario outputs shall be advisory unless passed through the canonical governor.
- [ ] The Risk Governor shall consume `RegimeAssessment` before approving, warning, rejecting, or blocking proposed risk-increasing actions.
- [ ] `PortfolioAuditService.audit` shall flag missing risk-governor approval, approval token/order mismatch, unauthorized risk threshold changes, skipped lifecycle stages, missing live strategy board approval, missing evidence refs, missing execution logs, missing broker responses, and hidden failed tool calls.
- [ ] The risk governor shall downgrade decisions to `needs_approval`, `reject`, or `block` when portfolio exit-liquidity stress breaches configured limits.
- [ ] The governor shall populate `primary_failure_limit` and `composite_breach_flags` in every material `RiskDecisionPackage`.
- [ ] `run_portfolio_risk_governor`
- [ ] Governor decision generation shall complete within 50 ms p95 after snapshot inputs are prepared.
- [ ] Complex orchestration shall belong in services or the governor, not calculators.
- [ ] Risk calculators, limit checks, sizing calculations, regime checks, and governor logic shall be stateless and thread-safe.
- [ ] The governor shall not rely on unordered dictionaries, sets, filesystem discovery order, dynamic import order, or plugin discovery order for safety-critical limit sequencing.
- [ ] Governor decision precedence shall follow: `block > error > reject > needs_more_evidence > needs_approval > warn > approve`.
- [ ] Scenario outputs shall remain advisory unless passed through the governor.
- [ ] Risk Agent: may request snapshots, ask for governor decisions, explain findings, summarize approval requirements, and package evidence for human review.
- [ ] Risk Agent shall not override deterministic governor decisions.
- [ ] No file-specific non-functional requirements defined.
- [ ] `GOVERNOR_DECISION_FAILED`
- [ ] Governor tests shall cover decision truth tables.
- [ ] Portfolio-under-risk tests shall cover `LifecycleService.transition` across allowed transitions, invalid transitions, missing board approval, risk-governor incompatibility, missing strategy review evidence, and accepted transitions.
- [ ] Governor truth-table tests shall pass.
- [ ] The target module path is `app/services/risk/`.
- [ ] The source document is the production requirements baseline v8.0.
- [ ] The implementation language is Python.
- [ ] The module targets Python 3.12 or newer.
- [ ] Integration dependencies are accessed through stable public interfaces.
- [ ] `app.services.execution` may provide read-only open orders/positions but shall not be mutated by risk.
- [ ] JSONL storage is permitted for local development and deterministic tests.
- [ ] Performance targets are measured in local deterministic mode with no remote broker/network calls unless otherwise specified.
- [ ] Governance remains externally owned by `app/services/governance` or an equivalent governance service exposed through stable public interfaces.
- [ ] No safe fallback for a `RISK-PEND-*` item shall remain the permanent default for more than two sprint cycles without owner/architect review and a roadmap entry.
- [ ] Source-confirmed production requirements are captured in this document unless explicitly marked Pending or Recommendation.
- [ ] Pending: confirm whether double-spend prevention is implemented inside Risk through a pending-approvals cache or enforced externally by Execution/Governance serialization.
- [ ] Recommendation: approval tokens should include a cryptographic nonce or single-use flag for all governed workflows, not only live-sensitive workflows.
- [ ] Recommendation: token validation should record approval tokens as consumed in audit storage and reject consumed tokens on replay.
- [ ] Symbols not listed in `app.services.risk.__all__` shall be private implementation details and may change without compatibility guarantees.
- [ ] Only symbols classified as `official_ai_tool` shall be agent-callable official risk tools.
- [ ] Internal helpers shall not be agent-callable and shall not be included in the official AI tool registry.
- [ ] Legacy compatibility exports shall document replacement guidance, stability, and deprecation status when they differ from canonical tool names.
- [ ] Every official AI tool shall follow the HaruQuant AI Tool Function Standard.
- [ ] Official AI tools shall call deterministic services rather than implementing risk logic inline.
- [ ] Required official tool surface shall include:
- [ ] `build_portfolio_risk_snapshot`
- [ ] `review_trade_risk`
- [ ] `calculate_position_size`
- [ ] `assess_risk_regime`
- [ ] `review_strategy_admission`
- [ ] `validate_risk_approval_token`
- [ ] `generate_risk_report`
- [ ] Current implementation traceability shall map the canonical official tool groups above to the present `app.services.risk.__all__` export surface without treating differently named but equivalent legacy requirements as separate behavior.
- [ ] Portfolio-under-risk compatibility shall treat `app.services.portfolio` and the `portfolio` tool category as compatibility adapters unless explicitly classified as risk-owned services.
- [ ] Transitional portfolio-under-risk facades shall be fully migrated to `app/services/portfolio` or explicitly reapproved by the owner/architect no later than v2.0.
- [ ] Safe fallback compatibility facades shall not be treated as permanent architecture without owner/architect review.
- [ ] `RiskConfig` / `RiskThresholds`
- [ ] `PortfolioRiskSnapshot`
- [ ] `ProposedTrade`
- [ ] `ProposedAllocation`
- [ ] `RegimeAssessment`
- [ ] `RiskApprovalToken`
- [ ] `RiskAuditRecord`
- [ ] `RiskReport`
- [ ] Private service internals shall not appear in `app.services.risk.__all__` unless they are intentionally classified, documented, tested, and reviewed for public import.
- [ ] Public JSON serialization shall preserve Decimal precision through string or another documented exact JSON-safe representation and shall not silently convert Decimal values to binary floats.
- [ ] Official Risk tools shall not read local system time directly except through the approved time provider or shared Utils clock helper.
- [ ] Pre-trade risk review latency for a normal portfolio shall complete within 100 ms p95 in local deterministic mode.
- [ ] Snapshot generation for up to 500 open positions shall complete within 250 ms p95.
- [ ] Audit chain verification of 10,000 audit records shall complete within 2 seconds p95.
- [ ] The module shall support at least 500 open positions in portfolio-level calculations.
- [ ] The module shall avoid O(n³) algorithms in normal pre-trade paths unless explicitly justified.
- [ ] Public official Risk tools shall reject JSON payload nesting deeper than 10 levels by default before expensive validation or calculation begins.
- [ ] Public official Risk tools shall reject arrays or lists with more than 10,000 items by default before expensive validation or calculation begins.
- [ ] Normal pre-trade paths shall not exceed O(n^2) complexity over open positions and correlated symbols under supported portfolio sizes.
- [ ] The module shall define retry and retry-exhaustion behavior for idempotent persistence and validation operations.
- [ ] Approval-token signing keys, secrets, broker credentials, and private account identifiers shall never be logged.
- [ ] Approval tokens shall be tamper-evident using HMAC or stronger signing.
- [ ] Internal helpers shall not be exposed as official AI tools unless intentionally promoted through `__all__`.
- [ ] The module shall enforce least privilege: risk can approve or block readiness but cannot execute trades.
- [ ] Logs and audit records shall redact secrets and sensitive account data.
- [ ] Hash-chain generation shall use canonical serialization and a documented hash algorithm.
- [ ] The module shall support Python 3.12 or newer.
- [ ] The module shall use project logging and result conventions.
- [ ] The module shall avoid unnecessary heavy dependencies in deterministic pre-trade paths.
- [ ] Each production file shall have a clear module-level docstring and public function/class docstrings.
- [ ] Public functions shall have type hints.
- [ ] Core functions shall remain small, focused, and testable.
- [ ] Public interface changes shall be versioned, documented, and reviewed before downstream workflows depend on them.
- [ ] `app.services.risk.__all__` shall remain the explicit current agent-facing export registry and shall be reviewed whenever current implementation exports diverge from canonical future tool names.
- [ ] Portfolio-under-risk service classes shall be lazy-loaded so optional portfolio workflow dependencies do not break risk importability.
- [ ] Portfolio-under-risk artifacts shall not contain secrets, credentials, broker passwords, API keys, or unredacted private data.
- [ ] Portfolio-under-risk reports shall distinguish complete, incomplete, accepted, rejected, blocked, triggered, and approval-required states.
- [ ] Any pending-approval reservation cache used by the risk module shall be keyed by `workflow_id`, bounded by expiry, and synchronized for concurrent reads and writes.
- [ ] Risk calculations for production live workflows shall prefer methods that reduce tail-risk underestimation.
- [ ] The module shall prevent LLM agents from approving live trading.
- [ ] The module shall prevent approval tokens from authorizing mismatched subject/action scopes.
- [ ] The module shall prevent consumed approval tokens from validating for live-sensitive actions.
- [ ] The module shall require nonce or single-use validation for live-sensitive approval tokens.
- [ ] The module shall redact broker passwords, API keys, account passwords, private tokens, token signing keys, full account credentials, and raw private approval secrets from logs and audit records.
- [ ] Audit hash chaining shall use SHA-256 or stronger and deterministic canonical JSON serialization.
- [ ] The first audit-chain record shall use a documented genesis value; the default is 64 zeroes unless deployment config defines a different constant.
- [ ] Risk tools shall never set `places_trade=True`.
- [ ] The risk module shall own strategy admission checks.
- [ ] The risk module shall own pre-trade risk review.
- [ ] The risk module shall own allocation review.
- [ ] The risk module shall own approval-token creation and validation.
- [ ] The risk module shall own risk audit records.
- [ ] The risk module shall own risk report summaries.
- [ ] The risk module shall expose agent-safe risk tools.
- [ ] The risk module shall not acquire market data directly.
- [ ] The risk module shall not generate strategy signals.
- [ ] The risk module shall not execute backtests.
- [ ] The risk module shall not place broker orders.
- [ ] The risk module shall not close positions.
- [ ] The risk module shall not render UI.
- [ ] The risk module shall not allow LLM-based final approval.
- [ ] The risk module shall not own database infrastructure outside its storage boundary.
- [ ] The risk module shall calculate account equity, balance, open risk, floating PnL, realized PnL, margin usage, free margin, and leverage when inputs are available.
- [ ] The risk module shall support account-base-currency conversion when conversion rates are available.
- [ ] All monetary account-level risk metrics shall be expressed in account base currency.
- [ ] The risk module shall enforce configurable maximum total loss, with default baseline of 10%.
- [ ] The risk module shall support configurable monthly profit target tracking, with default baseline of 10%.
- [ ] Monthly profit target tracking shall define the reset calendar, account timezone, equity/balance base, inclusion of open PnL, and handling of deposits/withdrawals before production handoff.
- [ ] The risk module shall detect best-day or consistency-rule risk when configured.
- [ ] The risk module shall calculate projected margin usage after a proposed trade.
- [ ] The risk module shall evaluate proposed trades against the existing portfolio, not only against individual positions.
- [ ] The risk module shall reject or warn when a proposed trade increases portfolio correlation above the configured threshold; the default FX baseline is 0.50.
- [ ] The risk module shall calculate incremental risk contribution when enough data exists.
- [ ] The risk module shall support weekend, overnight, and restricted-session rules when enabled.
- [ ] The risk module shall use explicit timezone configuration for all session and calendar rules.
- [ ] The risk module shall not compare naive and aware datetimes.
- [ ] The risk module shall reject approval reuse for materially different actions.
- [ ] The risk module shall reject consumed approval tokens for live-sensitive actions, even if they are otherwise unexpired, correctly signed, and correctly scoped.
- [ ] Emergency revocation shall be logged as a material governance event.
- [ ] The risk module shall calculate `RegimeAssessment` for portfolio snapshots when regime assessment is enabled.
- [ ] `IncidentService.create_incident` shall create portfolio incident reports from supplied incident fields and write an incident audit artifact.
- [ ] The risk module shall apply graduated risk step-down controls before hard circuit breakers for production live workflows and when otherwise enabled.
- [ ] The risk module shall support in-flight order tolerance buffers during live reconciliation for production live workflows and when otherwise enabled.
- [ ] The audit layer shall support cryptographic hash chaining with `previous_hash` and `record_hash` for tamper-evident audit records, and production live workflows shall require audit-chain persistence.
- [ ] Negative price, equity, margin, volatility, or quantity shall be rejected where invalid.
- [ ] Impossible timestamps shall be rejected or blocked according to workflow policy.
- [ ] Concurrent approval attempts that would overspend in-flight tolerance shall block or fail deterministically.
- [ ] Empty allocation strategy list shall return empty equal-capital allocation instead of dividing by zero.
- [ ] Audit-chain tamper detection shall emit `AUDIT_CHAIN_TAMPER_DETECTED`.
- [ ] Maliciously deep JSON payloads or excessively large arrays, including more than 10,000 items in a single list, shall be rejected with `PAYLOAD_TOO_LARGE` before parsing or expensive validation.
- [ ] `POLICY_BLOCKED`
- [ ] `APPROVAL_REQUIRED`
- [ ] `APPROVAL_TOKEN_EXPIRED`
- [ ] `APPROVAL_TOKEN_REVOKED`
- [ ] `APPROVAL_TOKEN_CONSUMED`
- [ ] `CONFIG_VERSION_MISMATCH`
- [ ] `CONFIG_COMPATIBILITY_NOT_APPROVED`
- [ ] `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`
- [ ] `PAYLOAD_TOO_LARGE`
- [ ] `IN_FLIGHT_TOLERANCE_EXCEEDED`
- [ ] Internal services may raise domain exceptions.
- [ ] Official AI tools shall catch domain exceptions and return standard tool responses.
- [ ] Double-spend detection shall not silently approve concurrent risk-increasing actions.
- [ ] Zero-equity percentage-risk calculations shall not silently compute or default.
- [ ] Unit tests shall exist for every non-trivial risk module file.
- [ ] Config tests shall cover loading, validation, hash stability, and config mismatch.
- [ ] Limit tests shall cover pass, warn, fail, and block paths for every configured limit.
- [ ] Approval tests shall cover nonce or single-use validation, consumed-token rejection, and config-compatibility rejection by default.
- [ ] Approval tests shall prove unauthorized approvers cannot create or validate governed approval tokens.
- [ ] Approval tests shall prove token-consumption write failure blocks live-sensitive validation.
- [ ] Tool-standard tests shall cover every exported AI tool.
- [ ] Export-registry tests shall verify `app.services.risk.__all__` exactly matches the expected current agent-facing tool surface until a versioned registry change is approved.
- [ ] Usage tests shall verify every exported risk tool has a usage example or an explicit approved skip.
- [ ] Security tests shall cover prompt override, token replay, secret logging, and permission bypass.
- [ ] Portfolio-under-risk tests shall cover lazy service loading, unknown lazy service names, and package import behavior.
- [ ] Traceability tests or review artifacts shall verify every business rule maps to an owning requirement before production promotion.
- [ ] Performance tests shall prove oversized payload rejection happens before expensive calculations.
- [ ] Payload parsing tests shall prove deeply nested, malformed, and excessively large JSON/list payloads are rejected efficiently without CPU exhaustion.
- [ ] Concurrency tests shall prove pending-approval cache behavior is deterministic if implemented inside risk.
- [ ] Integration tests shall cover audit persistence partial write when mandatory audit is enabled.
- [ ] Integration tests shall cover the Execution/Governance serialization path when Risk does not own pending-approval reservations.
- [ ] Error-code tests shall prove `PARAMETRIC_VAR_GAUSSIAN_WARNING` and `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED` are included in deterministic error or warning handling.
- [ ] Coverage shall remain above 80%, with higher practical coverage for core risk gates.
- [ ] All FR and NFR requirements shall have implementation owners.
- [ ] All official AI tools shall comply with the HaruQuant Tool Function Standard.
- [ ] Audit persistence behavior shall be verified.
- [ ] Live execution shall remain outside the risk module.
- [ ] Before Builder handoff, every mandatory Risk requirement shall have a stable unique identifier.
- [ ] Builder handoff shall remain blocked while any `RISK-PEND-*` item is unresolved or not explicitly deferred by owner/architect approval.
- [ ] Forward references to source-only IDs such as `FR-096` through `FR-100` shall remain migration notes only until equivalent active `RISK-*` identifiers are assigned.
- [ ] Error code documentation shall explain `PARAMETRIC_VAR_GAUSSIAN_WARNING` and `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`.
- [ ] Component map shall document which file owns each risk capability.
- [ ] Approval-token documentation shall define config-hash compatibility, default fail-closed behavior, nonce or single-use handling, token consumption, revocation, and replay rejection.
- [ ] Risk reports shall be available in Markdown and JSON-compatible dict formats.
- [ ] Institutional hardening requirements shall be canonically treated as `FR-096` through `FR-100`.
- [ ] Duplicate source references to `FR-086` through `FR-091` shall be normalized during implementation planning and traceability review.
- [ ] The official AI tool requirements shall use their own canonical tool-surface requirement group and shall not reuse institutional hardening IDs.
- [ ] The module shall target Python 3.12 or newer.
- [ ] JSONL storage shall be permitted for local development and deterministic tests.
- [ ] Approval tokens shall include a cryptographic nonce or single-use identifier.
- [ ] Risk may decide whether an action is allowed, blocked, or approval-required, but shall not place trades, close positions, mutate broker state, or override execution tools.
- [ ] Risk shall advise and gate; Execution shall act.
- [ ] Agents shall call official risk tools only; internal calculators and helpers shall remain private unless intentionally promoted.
- [ ] Allocation recommendations shall not be execution instructions.
- [ ] Pre-trade approvals shall not be allowed to double-spend in-flight order tolerance.
- [ ] LLM Agent: may explain, summarize, or recommend, but shall not enforce final safety-critical gates.
- [ ] Authorized Approver: may approve eligible approval-required actions through deterministic approval-token workflow.
- [ ] Execution layer: may consume readiness output from the risk module but must handle actual execution outside risk.
- [ ] Risk Agent shall not approve live trading by itself.
- [ ] Risk Agent shall not bypass approval tokens.
- [ ] Agents shall not import internal calculators unless intentionally exposed as official tools.
#### `app/services/risk/limits.py`

Functions/classes:
- `ValidationIssue`
- `ValidationSummary`
- `validate_account_state`
- `validate_market_states`
- `validate_symbol_states`
- `validate_position_states`
- `validate_risk_limits`

Requirements:
- [ ] Recommendation: `RegimeAssessment` should output a configurable `risk_multiplier` that can scale position sizing and exposure limits when promoted by owner decision.
- [ ] The current implementation support surface shall include validation contracts and validators through `ValidationIssue`, `ValidationSummary`, `validate_account_state`, `validate_market_states`, `validate_symbol_states`, `validate_position_states`, and `validate_risk_limits`.
- [ ] The risk module shall detect symbol concentration breaches using configurable limits.
- [ ] The risk module shall detect strategy concentration breaches using configurable limits.
- [ ] The risk module shall enforce maximum margin utilization limits.
- [ ] The risk module shall enforce maximum effective leverage limits.
- [ ] The risk module shall enforce configurable maximum spread limits for pre-trade review.
- [ ] The risk module shall enforce demotion, suspension, and retirement rules for strategies breaching risk limits.
- [ ] The risk module shall clamp or reject position sizes that exceed broker constraints, configured risk, margin, leverage, concentration, or symbol limits.
- [ ] The risk module shall validate allocation proposals against portfolio-level risk limits before approval.
- [ ] The risk module shall apply stricter configured risk limits during high-risk regimes.
- [ ] Agent-provided text shall never override deterministic policy, approvals, kill-switch state, or configured risk limits.
- [ ] The module shall prevent LLM and agent prompt text from overriding deterministic policy, approvals, kill-switch state, or configured risk limits.
- [ ] Composite breach tracking shall include all breached limits, but primary failure shall be selected from deterministic order after precedence is applied.
- [ ] No file-specific non-functional requirements defined.
- [ ] Concurrent pre-trade requests using the same stale `PortfolioState` shall not receive approvals that collectively breach configured risk limits.
- [ ] Pending: confirm the exact stressed-lookback policy for crisis correlation, VaR, and CVaR calculations.
- [ ] Pending: confirm which heavy-tailed parametric VaR distribution is supported first.
- [ ] Pending: confirm whether Gaussian parametric VaR is allowed in production-live workflows after warning or requires explicit waiver.
- [ ] Current portfolio-state and portfolio-risk exports shall include `get_open_positions`, `get_open_orders`, `get_strategy_allocations`, `get_portfolio_equity_curve`, `calculate_portfolio_returns`, `calculate_portfolio_volatility`, `calculate_portfolio_correlation`, `calculate_portfolio_var`, `calculate_portfolio_cvar`, `calculate_risk_contribution`, `calculate_margin_usage`, `calculate_currency_exposure`, `detect_strategy_overlap`, `detect_symbol_cluster_risk`, and `build_portfolio_risk_snapshot`.
- [ ] Current shared risk tool helpers shall include `risk_tool_result`, `risk_tool_context`, `risk_business_payload`, `risk_limit_check`, `risk_policy_module`, `risk_portfolio_module`, `risk_safety_module`, and `risk_live_module`, and shall remain support helpers rather than independent trading authority.
- [ ] Shared helpers such as `risk_tool_result`, `risk_tool_context`, `risk_business_payload`, `risk_limit_check`, `risk_policy_module`, `risk_portfolio_module`, `risk_safety_module`, and `risk_live_module` shall remain support helpers and shall not be official AI tools.
- [ ] The risk module shall define Decimal precision and rounding behavior for money, volume, lot size, pips, percentages, VaR, CVaR, margin, leverage, exposure, and allocation calculations.
- [ ] The module shall support at least 100 strategies in allocation and concentration review.
- [ ] The module shall support at least 5,000 historical return points for VaR/CVaR calculations.
- [ ] VaR, CVaR, and correlation methods shall account for non-stationarity during high-volatility and crisis regimes.
- [ ] Production live VaR behavior shall avoid Gaussian assumptions unless explicitly overridden and warning-tagged.
- [ ] The risk module shall own portfolio exposure analysis.
- [ ] The risk module shall own risk limit checks.
- [ ] Pending orders shall be included in exposure, margin, leverage, concentration, and cluster-risk calculations according to the configured pending-order exposure policy.
- [ ] Near-market pending orders shall be treated as potential exposure unless explicitly configured otherwise.
- [ ] The risk module shall calculate exposure by symbol, strategy, currency, asset class, direction, and account-level aggregate.
- [ ] The risk module shall calculate net and gross exposure separately.
- [ ] The risk module shall detect currency-cluster and correlated-cluster exposure risks for FX portfolios.
- [ ] The risk module shall calculate daily drawdown, total drawdown, peak-to-valley drawdown, and current drawdown state.
- [ ] The risk module shall enforce configurable maximum daily loss, with default baseline of 5%.
- [ ] The risk module shall calculate VaR at configurable confidence levels, with default baseline of 95%.
- [ ] The risk module shall calculate CVaR / expected shortfall at configurable confidence levels.
- [ ] The risk module shall support historical and parametric VaR methods when configured.
- [ ] If parametric VaR is used for production live workflows, it shall default to a heavy-tailed distribution.
- [ ] The risk module shall calculate pairwise and portfolio-level correlation exposure for active positions and proposed trades.
- [ ] The regime layer shall classify volatility, liquidity, correlation, drawdown, crisis, news, and session regimes.
- [ ] The risk module shall calculate portfolio exit-liquidity stress for production live workflows and when otherwise enabled, including stressed VaR, stressed CVaR where available, stressed max drawdown, and market-impact assumptions.
- [ ] Risk reports shall highlight `primary_failure_limit` first and list composite breach flags separately.
- [ ] Parametric VaR configured with Gaussian assumptions shall emit `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
- [ ] `LIMIT_FAILED`
- [ ] `PARAMETRIC_VAR_GAUSSIAN_WARNING`
- [ ] Gaussian parametric VaR shall not silently pass as normal production-live VaR behavior.
- [ ] Calculator tests shall cover exposure, margin, drawdown, VaR, CVaR, volatility, and correlation.
- [ ] Regime tests shall prove stressed correlation lookback behavior is used in `high_volatility` or `crisis` regimes when required.
- [ ] Regime tests shall prove stressed VaR/CVaR behavior is used in `high_volatility` or `crisis` regimes when required.
- [ ] Edge-case hardening tests shall cover step-down startup/restore/reset, audit genesis, correlation fallback, deterministic limit order, and in-flight grace expiry.
- [ ] VaR/CVaR tests shall prove historical VaR is the production-live default.
- [ ] VaR/CVaR tests shall prove Gaussian parametric VaR emits `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
- [ ] VaR documentation shall explain production-live VaR method defaults and parametric distribution assumptions.
- [ ] Portfolio service exposure should be reviewed whenever `app.services.portfolio.__all__` changes so lazy service exports and formal package exports remain intentionally aligned.
- [ ] Limit checks shall execute in a documented deterministic order.
- [ ] Historical VaR shall be the production-live default.
- [ ] Gaussian parametric VaR shall be warning-gated with `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
#### `app/services/risk/sizing.py`

Functions/classes:
- `INVALID_RISK_CONFIG`
- `calculate_fixed_fractional_size`
- `calculate_volatility_adjusted_size`
- `calculate_risk_parity_weights`
- `calculate_correlation_adjusted_size`
- `calculate_margin_aware_size`
- `calculate_cost_adjusted_size`
- `calculate_max_safe_position_size`
- `validate_allocation_proposal`
- `INSUFFICIENT_K_EVIDENCE`
- `PositionSizingResult`
- `AllocationService`
- `MISSING_STOP_LOSS`

Requirements:
- [ ] Institutional hardening blocks may be feature-flagged during implementation, but production live workflows require exit-liquidity stress, correlation-adjusted sizing, graduated step-down controls, live portfolio-state freshness checks, in-flight order tolerance enforcement, audit hash chaining, and composite breach reporting.
- [ ] If `RISK-PEND-002` is unresolved, production Kelly sizing shall require `kelly_fraction_multiplier` in the active risk profile and shall return `INVALID_RISK_CONFIG` when it is missing.
- [ ] The risk module shall own position sizing recommendations.
- [ ] Current allocation and sizing exports shall include `calculate_fixed_fractional_size`, `calculate_volatility_adjusted_size`, `calculate_risk_parity_weights`, `calculate_correlation_adjusted_size`, `calculate_margin_aware_size`, `calculate_cost_adjusted_size`, `calculate_max_safe_position_size`, `propose_strategy_allocation`, `rebalance_strategy_allocations`, and `validate_allocation_proposal`.
- [ ] The current implementation support surface shall include reusable calculation helpers for stop distance, pip value, proposed trade risk, notional exposure, risk/reward, VaR, CVaR, drawdown, exposure, concentration, margin, correlation, and position sizing.
- [ ] `PositionSizingRequest`
- [ ] `PositionSizingResult`
- [ ] Raw calculators for stop distance, pip value, proposed trade risk, notional exposure, risk/reward, VaR, CVaR, drawdown, exposure, concentration, margin, correlation, and position sizing shall remain private or deterministic-service internals unless explicitly promoted.
- [ ] Monetary and sizing calculations shall use `ROUND_HALF_EVEN` unless an approved risk profile explicitly documents a different deterministic rounding mode.
- [ ] Public Pydantic V2 contracts shall use strict `Decimal` typing for monetary, sizing, margin, leverage, exposure, VaR, CVaR, and allocation fields and shall forbid implicit float casting for those fields.
- [ ] The risk module shall calculate `fixed_lot` sizing using a configured lot size.
- [ ] The risk module shall calculate `fixed_risk` sizing using fixed account risk percentage or fixed account risk amount.
- [ ] The risk module shall calculate `milestone` sizing using deterministic account balance/equity milestone tables.
- [ ] The risk module shall calculate conservative `kelly_criterion` sizing using validated win-rate/payoff evidence, configured caps, and a configurable minimum trade sample requirement.
- [ ] Kelly sizing shall use default baseline `min_kelly_trades = 30`; insufficient samples shall emit `INSUFFICIENT_K_EVIDENCE`.
- [ ] Production Kelly sizing shall apply fractional Kelly by default to account for estimation error in historical win-rate and payoff-ratio evidence.
- [ ] Full Kelly sizing shall be prohibited by default and allowed only when an explicit documented risk waiver is supplied.
- [ ] Kelly sizing output shall disclose the fractional Kelly multiplier applied and whether full Kelly was rejected, downgraded, or allowed by waiver.
- [ ] The risk module shall calculate `volatility` sizing using ATR or volatility-adjusted stop distance.
- [ ] The risk module shall calculate `fixed_fractional` sizing using configured capital fraction or notional allocation.
- [ ] The `fixed_risk` sizing method shall calculate risk from distance to the provided stop-loss.
- [ ] `ProposedTrade.stop_loss` shall be required and valid for `fixed_risk` sizing unless an approved sizing policy explicitly uses another stop-distance evidence field.
- [ ] The risk module shall return a canonical `PositionSizingResult` for every sizing request.
- [ ] The risk module shall support risk-parity-style allocation proposals for strategy baskets.
- [ ] `AllocationService.propose` shall evaluate portfolio allocation proposals against available capital, stale allocation data, eligible lifecycle states, maximum strategy allocation, maximum symbol allocation, and maximum cluster allocation.
- [ ] `AllocationService.propose` shall reject allocations that exceed capital, use ineligible lifecycle states, exceed strategy caps, exceed symbol concentration, exceed cluster concentration, or rely on stale allocation data.
- [ ] `AllocationService.propose` shall accept valid allocations with a constraint report and board approval flag, and shall write an allocation audit artifact.
- [ ] `AllocationService.equal_capital` shall split available capital equally across supplied strategy ids and return an empty allocation when no strategy ids are supplied.
- [ ] `AllocationService.confidence_weighted` shall allocate capital in proportion to non-negative strategy confidence scores and avoid division by zero when confidence inputs are absent or all zero.
- [ ] The position sizing engine shall support correlation-adjusted sizing for production live workflows and when otherwise enabled, using marginal correlation to open positions and configured penalty method.
- [ ] Kelly sizing shall either reject insufficient evidence with `INSUFFICIENT_K_EVIDENCE` or, when configured, fall back to `fixed_risk` and emit `SIZING_FALLBACK_TO_FIXED_RISK`.
- [ ] Position sizing for one standard sizing request with broker constraints shall complete within 25 ms p95.
- [ ] Correlation-adjusted sizing for one request plus 100-symbol correlation context shall complete within 50 ms p95.
- [ ] Sizing documentation shall explain the default fractional Kelly policy and risk-waiver requirement for full Kelly.
- [ ] Production live workflows shall enable exit-liquidity stress, correlation-adjusted sizing, graduated step-down controls, live portfolio-state freshness checks, in-flight order tolerance enforcement, audit hash chaining, and composite breach reporting.
- [ ] Per-trade sizing shall call `sizing.py`; allocation shall not duplicate sizing formulas.
- [ ] Valid `PositionSizingResult` shall mean only that sizing calculated successfully, not that the trade is approved.
- [ ] Production Kelly sizing shall be fractional by default.
- [ ] Full Kelly sizing shall require an explicit documented risk waiver.
- [ ] No file-specific non-functional requirements defined.
- [ ] Missing stop-loss for fixed-risk sizing shall emit `MISSING_STOP_LOSS` when required.
- [ ] Full Kelly sizing requested without a documented waiver shall be rejected or downgraded to fractional Kelly according to policy.
- [ ] Stop-loss-dependent sizing shall not silently infer stop-loss distance when required evidence is absent.
- [ ] Position sizing tests shall cover `fixed_lot`, `fixed_risk`, `milestone`, Kelly, volatility, and `fixed_fractional`.
- [ ] Position sizing tests shall prove production Kelly sizing applies fractional Kelly by default.
- [ ] Position sizing tests shall prove full Kelly requires a documented risk waiver.
- [ ] Position sizing tests shall prove missing or invalid stop-loss for `fixed_risk` returns `MISSING_STOP_LOSS`.
- [ ] Position sizing tests shall prove zero account equity returns `INVALID_PORTFOLIO_STATE` for percentage-risk calculations.
- [ ] Workflow tests shall cover pre-trade, position sizing, regime assessment, strategy admission, allocation, and live-readiness.
- [ ] Institutional hardening tests shall cover exit-liquidity stress, correlation-adjusted sizing, step-down state, live freshness, in-flight tolerance, audit chain, and composite failure.
- [ ] Concurrency tests shall cover simultaneous risk decisions, simultaneous sizing calls, and cached read/write paths.
- [ ] Position sizing methods shall have expected-value fixtures.
- [ ] Pending: confirm the exact default fractional Kelly multiplier value.
- [ ] The risk module shall calculate portfolio volatility using a deterministic method and documented lookback window.
- [ ] Regime documentation shall explain stressed lookback behavior for `high_volatility` and `crisis` regimes.
#### `app/services/risk/lifecycle.py`

Functions/classes:
- `build_risk_decision_package`
- `AllocationService`
- `CostService`
- `IncidentService`
- `PortfolioAuditService`
- `PortfolioKillSwitch`
- `LifecycleService`
- `ReportingService`

Requirements:
- [ ] The risk module shall not own portfolio management, cost aggregation, incident management, lifecycle execution logic, or broad reporting workflows.
- [ ] Current strategy lifecycle and decision-package exports shall include `admit_strategy_to_portfolio`, `promote_strategy_to_paper`, `promote_strategy_to_live_candidate`, `suspend_strategy`, `retire_strategy`, `demote_strategy_to_paper`, `update_strategy_status`, and `build_risk_decision_package`.
- [ ] `AllocationService`, `CostService`, `IncidentService`, `LifecycleService`, `PortfolioKillSwitch`, `PortfolioAuditService`, and `ReportingService` shall be documented as external compatibility facades and not core Risk-owned services unless a later owner decision explicitly reclassifies them.
- [ ] Portfolio-under-risk compatibility shall include lazy service exposure through `__getattr__` for `AllocationService`, `CostService`, `IncidentService`, `PortfolioAuditService`, `PortfolioKillSwitch`, `LifecycleService`, and `ReportingService`.
- [ ] The risk module shall review strategy admission using a canonical validation evidence package.
- [ ] The risk module shall support the canonical lifecycle states `research`, `validated`, `paper_candidate`, `paper_active`, `live_candidate`, `live_active`, `suspended`, `retired`, and `rejected`.
- [ ] The risk module shall normalize legacy lifecycle aliases to canonical lifecycle states only when the mapping is deterministic.
- [ ] The risk module shall reject ambiguous lifecycle aliases with a deterministic data-quality failure.
- [ ] The risk module shall enforce promotion gates before a strategy moves into paper or live eligibility.
- [ ] The risk module shall not mark a strategy live-ready without evidence, risk decision, approval state, and kill-switch status.
- [ ] `LifecycleService.transition` shall evaluate governed strategy lifecycle transitions against the allowed transition map.
- [ ] `LifecycleService.transition` shall reject transitions that are not allowed by the lifecycle transition map.
- [ ] `LifecycleService.transition` shall require strategy review evidence when transitioning to paper-live.
- [ ] `LifecycleService.transition` shall write a lifecycle audit artifact.
- [ ] A canonical glossary shall document decision states, lifecycle states, evidence states, workflow modes, and limit statuses.
- [ ] Strategy lifecycle state names and board approval semantics should remain aligned between portfolio-under-risk workflows and the canonical risk governance glossary.
- [ ] The canonical strategy lifecycle states shall be `research`, `validated`, `paper_candidate`, `paper_active`, `live_candidate`, `live_active`, `suspended`, `retired`, and `rejected`.
- [ ] Legacy or source-only lifecycle aliases such as `draft`, `candidate`, `backtested`, `robustness_passed`, `paper`, `approved_for_live`, `live_approved`, and `live` shall be normalized to canonical lifecycle states or rejected when ambiguous.
- [ ] The risk module documentation shall include a canonical glossary for decision states, lifecycle states, evidence states, workflow modes, and limit statuses.
- [ ] Any important risk decision, approval token, kill-switch check, live-readiness decision, or strategy lifecycle change shall produce audit data.
- [ ] No file-specific non-functional requirements defined.
- [ ] Invalid strategy lifecycle state shall trigger data-quality failure.
- [ ] Portfolio-under-risk tests shall cover `AllocationService.propose`, `AllocationService.equal_capital`, and `AllocationService.confidence_weighted` across accepted, rejected, stale, over-capital, ineligible lifecycle, strategy cap, symbol cap, cluster cap, empty strategy list, and zero-confidence cases.
- [ ] Market data, portfolio state, execution state, governance state, and utility services are external domains.
- [ ] PostgreSQL is required for production live audit chains, approval-token state, token revocation state, and token consumption state.
- [ ] No official risk tool shall place trades, close trades, mutate broker state, or override execution controls.
- [ ] Portfolio-under-risk compatibility adapters shall not own source-of-truth portfolio, execution, cost, incident, governance, or broad reporting state.
- [ ] Portfolio-under-risk compatibility shall preserve the method-level service surface for `propose`, `equal_capital`, `confidence_weighted`, `evaluate`, `trigger`, `resume`, `transition`, `audit`, `create_incident`, `report`, and `generate`.
- [ ] `PortfolioState`
- [ ] Storage repositories, token-state backend clients, audit-chain internals, policy-resolution internals, and lazy service loaders shall not be agent-callable.
- [ ] Benchmark results shall report hardware, Python version, dependency versions, dataset size, and warm/cold cache state.
- [ ] Audit-chain genesis behavior shall be deterministic and documented; genesis value shall not depend on random runtime state.
- [ ] Pre-trade risk review shall remain safe under concurrent strategy submissions using the same portfolio state.
- [ ] The risk module shall own portfolio risk state construction.
- [ ] The risk module shall not mutate live account state.
- [ ] The risk module shall normalize raw account, equity, position, order, strategy, and symbol inputs into a canonical `PortfolioState`.
- [ ] The risk module shall build a reproducible `RiskSnapshot` from `PortfolioState` and `RiskConfig` without mutating source inputs.
- [ ] Approval-token consumption shall be persisted through the production token-state backend before a live-sensitive approval is treated as valid.
- [ ] The risk module shall run deterministic scenario and what-if analysis without changing live state.
- [ ] Timezone mismatch between broker-provided timestamps and the system-configured timezone shall trigger `INVALID_PORTFOLIO_STATE`.
- [ ] Unknown regime state shall fail closed for live-sensitive workflows when configured.
- [ ] Token-state backend unavailable during live-sensitive token validation shall fail closed.
- [ ] `INVALID_PORTFOLIO_STATE`
- [ ] `LIVE_STATE_STALE`
- [ ] Performance tests shall cover cold-cache and warm-cache p95 latency when both cache states are supported.
- [ ] Workflow tests shall prove Execution/Governance serialization or state-refresh requirements are enforced if pending approval reservation is externalized.
- [ ] Integration tests shall cover token-state backend unavailable during live-sensitive approval-token validation.
- [ ] Integration tests shall cover the current pipeline from portfolio state to risk snapshot, scorecard, recommendations, storage, and risk/scenario report generation.
- [ ] Regime assessment and transition tests shall pass.
- [ ] Workflow documentation shall state whether double-spend prevention is handled by an internal pending-approvals cache or by Execution/Governance serialization.
- [ ] PostgreSQL shall be the mandatory durable production backend for live audit chains, approval-token state, token revocation state, and token consumption state.
- [ ] Validated approval tokens for live-sensitive actions shall be marked consumed through the production token-state backend and shall not validate a second time.
#### `app/services/risk/kill_switch.py`

Functions/classes:
- `KillSwitchStateMachine`
- `KillSwitchService`

Requirements:
- [ ] The risk module shall own kill-switch state checks.
- [ ] `check_risk_kill_switch`
- [ ] The current implementation support surface shall include kill-switch contracts through `KillSwitchStateMachine`, `KillSwitchService`, `evaluate_new_entry_block`, and `require_hard_trigger_recovery_dual_auth`.
- [ ] `KillSwitchState`
- [ ] Token expiry, stale evidence detection, kill-switch timeout handling, step-down expiry, audit ordering, and clock-skew checks shall use the injected time source where available.
- [ ] The risk module shall classify portfolio drawdown state as normal, caution, restricted, blocked, or kill-switch-required according to configured thresholds.
- [ ] Kill-switch activation shall revoke or invalidate outstanding approval tokens for affected global, account, strategy, or symbol scope.
- [ ] The risk module shall check kill-switch state for live-readiness and execution-sensitive workflows.
- [ ] Active kill switch shall force `block` for live-related decisions.
- [ ] Unknown kill-switch state shall fail closed for live-related decisions.
- [ ] LLM agents shall not be able to override kill-switch state through prompt text, tool arguments, or approval tokens.
- [ ] The module shall support graduated risk step-down controls when enabled.
- [ ] Step-down controls shall apply before hard circuit breakers.
- [ ] Step-down controls shall never authorize a trade that would breach a hard risk limit.
- [ ] Step-down state shall support deterministic initialization, restoration, reset, expiry, and corruption handling.
- [ ] Live-sensitive workflows shall treat unreadable or corrupted persisted step-down state as `needs_more_evidence` or `block` according to config.
- [ ] `PortfolioKillSwitch.evaluate` shall return current state when no trigger is active.
- [ ] `PortfolioKillSwitch.trigger` shall set risk-owned kill-switch state to triggered, emit a deterministic block decision for new orders, require approval before resume, create incident details, and write a kill-switch audit artifact.
- [ ] Any execution-control mutation required to disable new orders shall be performed only by Execution/Governance through its own authorized interface after consuming the risk-owned block state.
- [ ] `PortfolioKillSwitch.resume` shall block resume without approval id and restore healthy state only when approval id is supplied.
- [ ] Every risk decision report shall include a plain-language explanation for `reject` or `block`, referencing the specific limit, rule, missing evidence, approval failure, or kill-switch state.
- [ ] `check_risk_kill_switch`
- [ ] Safety-critical decisions shall fail closed on invalid input, missing mandatory evidence, unknown approval state, unknown kill-switch state, or calculation failure.
- [ ] The module shall prevent LLM agents from overriding kill switch.
- [ ] The module shall invalidate outstanding approvals affected by kill-switch activation.
- [ ] Approval shall never be allowed for LLM kill-switch override, hidden live execution, broker action without execution gate, missing portfolio evidence, stale approval token, or mismatched subject/action token.
- [ ] Active kill switch shall always block risk-increasing and live-related action.
- [ ] Unknown kill switch shall fail closed for live-related actions.
- [ ] Tolerance buffers shall never override kill-switch, max-total-loss, or prohibited-action rules.
- [ ] Risk Agent shall not override kill switch.
- [ ] No file-specific non-functional requirements defined.
- [ ] `KILL_SWITCH_ACTIVE`
- [ ] `KILL_SWITCH_UNKNOWN`
- [ ] Safety-critical workflows shall fail closed on invalid input, missing evidence, unknown approval state, unknown kill-switch state, or calculation failure.
- [ ] Approval tests shall cover creation, validation, expiry, revocation, emergency kill-switch revocation, mismatch, and tamper.
- [ ] Time manipulation tests shall prove token expiry, stale evidence detection, kill-switch timeouts, step-down expiry, and clock-skew behavior remain deterministic with mocked or injected clocks.
- [ ] Kill-switch tests shall cover active, inactive, unknown, and attempted override.
- [ ] Portfolio-under-risk tests shall cover `PortfolioKillSwitch.evaluate`, `PortfolioKillSwitch.trigger`, and `PortfolioKillSwitch.resume` across each trigger condition and approval-required resume behavior.
- [ ] Approval and kill-switch security tests shall pass.
- [ ] Usage examples shall include failure response envelopes for missing evidence, active kill switch, and invalid approval token.
#### `app/services/risk/scenarios.py`

Functions/classes:
- `StressScenario`
- `ScenarioResult`
- `ScenarioRegistry`
- `build_default_scenario_registry`

Requirements:
- [ ] The current implementation support surface shall include scenario and replay contracts through `StressScenario`, `ScenarioResult`, `ScenarioRegistry`, `build_default_scenario_registry`, and `evaluate_scenarios`.
- [ ] Scenario analysis with up to 100 scenarios and 500 positions shall complete within 5 seconds p95.
- [ ] The module shall support at least 100 stress scenarios per scenario-analysis run.
- [ ] Benchmark scenarios `PERF-001` through `PERF-012` shall define dataset size, portfolio shape, strategy count, historical return count, scenario count, cache state, expected p95 latency, and acceptable variance.
- [ ] No file-specific non-functional requirements defined.
- [ ] Performance tests shall cover benchmark scenarios `PERF-001` through `PERF-012`.
### Unit Tests Required

```text
tests/unit/app/services/risk/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/05_risk.py
```

Usage examples must show:
- `example_01_risk_profile_validation`: Demonstrate risk profile loading, schema validation, and invalid profile failures.
- `example_02_limit_checks`: Demonstrate exposure, drawdown, loss, concentration, and stale-evidence limit checks.
- `example_03_position_sizing`: Demonstrate fixed-risk, fixed-fractional, volatility, Kelly, and milestone sizing calculators.
- `example_04_kill_switch`: Demonstrate kill-switch activation, status lookup, deterministic blocking, and non-bypass behavior.
- `example_05_risk_governor_decisions`: Demonstrate approve, reduce, reject, block, and needs-approval decisions with evidence metadata.
- `example_06_stress_scenarios`: Demonstrate stress scenario evaluation, scenario summaries, and fail-closed warnings.
- `example_07_official_risk_tools`: Demonstrate standard-envelope outputs for exported risk tools and error code correctness.
- `example_08_governed_action_boundaries`: Demonstrate that risk cannot execute trades and live mutations remain blocked.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 678 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(risk-governance): implement phase 5 risk governance requirements
```


- [ ] Recommendation: scenario analysis should include broker margin-call and stop-out stress tests using adverse price moves of two to three standard deviations.
- [ ] `run_risk_scenario_analysis`
- [ ] `ScenarioResult`
- [ ] Randomized scenario tests, if added, shall require explicit seeds and shall report the seed used.
- [ ] The risk module shall own scenario and what-if analysis for risk review.
## Phase 6 Analytics Service

### Goal

Implement the Analytics Service requirements under `app/services/analytics/` while preserving the phase module boundaries and governance rules.

Task inventory: 460 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/analytics/`.
- Requires Phase 5 Risk Governance contracts to be available where referenced by `06_analytics.md`.

### Files to Create

```text
app/services/analytics/
app/__init__.py
app/services/analytics/__init__.py
app/services/analytics/adapters.py
app/services/analytics/trade.py
app/services/analytics/equity.py
app/services/analytics/drawdown.py
app/services/analytics/risk.py
app/services/analytics/ratios.py
app/services/analytics/distributions.py
app/services/analytics/benchmark.py
app/services/analytics/efficiency.py
app/services/analytics/scorecard.py
app/services/analytics/report.py
app/services/analytics/dashboard.py
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/analytics/models.py`

Functions/classes:
- `Request`
- `Result`
- `Config`
- `Metadata`

Requirements:
- [ ] Analytics functions must be read-only and side-effect free at the domain level.
- [ ] Importing the analytics registry should not perform live broker calls, network calls, database mutations, or trading side effects.
- [ ] Official tools must be stateless, retry-safe, and safe for parallel optimization or portfolio workflows.
- [ ] Metric kernels must not depend on mutable global calculation state.
- [ ] Local/read-through caches, if implemented, must define TTL, maximum size, eviction behavior, invalidation keys, lock timeout, stale-read behavior, and single-flight or equivalent thundering-herd prevention before Builder handoff.
- [ ] Distributed caching, distributed invalidation services, message queues, and async background workers must not be implemented inside Analytics.
- [ ] Portfolio aggregation must fail closed when required base-currency conversion is unavailable.
- [ ] The analytics registry must expose only intentional public analytics tools and must not hide colliding function names; duplicate concepts must use module-qualified aliases where needed.
- [ ] Every official exported analytics tool must be callable, documented, and accept a `request_id` parameter for traceability.
- [ ] Each official public capability must be labeled as stable, approved experimental, deprecated, or internal-support-only.
- [ ] Each official public capability must document whether it is safe for agent/API use.
- [ ] The analytics registry must distinguish official tools, internal metric kernels, compatibility aliases, and deprecated exports.
- [ ] Agentic workflows must import analytics capabilities from `app.services.analytics` rather than deep module files.
- [ ] Strategy-version mismatch must be handled explicitly during degradation pairing and must not be hidden inside aggregate scores.
- [ ] Low-sample explainability drivers must not appear in ranked driver lists.
- [ ] `common_avg_loss` shall expose the common-module average-loss function without colliding with metrics exports.
- [ ] `common_get_r_multiples` shall expose the common-module R-multiple function without colliding with metrics exports.
- [ ] `max_gross_size_held` shall calculate the maximum absolute total size held across positions.
- [ ] `percent_time_in_market` shall calculate percent of the trading period spent in the market.
- [ ] `metrics_get_r_multiples` shall expose metrics-module R-multiple behavior without colliding with common exports.
- [ ] `win_rate_fraction` shall calculate win rate on a 0-to-1 scale.
- [ ] `avg_win_loss` shall calculate mean winning and losing outcomes.
- [ ] `consecutive_wins_losses` shall calculate maximum consecutive wins and losses from numeric outcomes.
- [ ] `t_statistic` shall calculate the t-statistic for mean outcome.
- [ ] `open_position_pnl` shall calculate total unrealized PnL from open positions.
- [ ] `slippage_paid` shall calculate total absolute slippage costs paid.
- [ ] `commission_paid` shall calculate total absolute commission costs paid.
- [ ] `swap_paid` shall calculate total absolute swap costs paid.
- [ ] `metrics_avg_loss` shall expose metrics-module average-loss behavior without colliding with common exports.
- [ ] `expectancy_r` shall calculate R-expectancy.
- [ ] `max_size_held` shall calculate maximum total contracts held.
- [ ] `max_net_size_held` shall calculate maximum net directional size held.
- [ ] `max_long_size_held` shall calculate maximum total long contracts held.
- [ ] `max_short_size_held` shall calculate maximum total short contracts held.
- [ ] `avg_r_multiple` shall calculate average R-multiple.
- [ ] `median_r_multiple` shall calculate median R-multiple.
- [ ] `r_expectancy` shall calculate R-space expectancy.
- [ ] `max_r_multiple` shall calculate maximum R-multiple.
- [ ] `min_r_multiple` shall calculate minimum R-multiple.
- [ ] `avg_consecutive_wins` shall calculate average length of winning streaks.
- [ ] `avg_consecutive_losses` shall calculate average length of losing streaks.
- [ ] `r_signal_to_noise` shall calculate mean R relative to R volatility.
- [ ] `rolling_expectancy_stability` shall calculate expectancy stability over a rolling window.
- [ ] `win_after_win_probability` shall calculate probability that a win follows a win.
- [ ] `runs_test_zscore` shall calculate Wald-Wolfowitz runs-test z-score.
- [ ] `get_analytics_overview` shall calculate comprehensive analytics across all, long, and short subsets.
- [ ] `calculate_spread_cost_impact` shall calculate spread cost drag.
- [ ] `calculate_slippage_impact` shall calculate slippage cost drag.
- [ ] `calculate_commission_impact` shall calculate commission cost drag.
- [ ] `cagr` shall calculate compound annual growth rate.
- [ ] `compound_monthly_growth_rate` shall calculate compound monthly growth rate.
- [ ] `buy_and_hold_cagr` shall calculate buy-and-hold CAGR from price data.
- [ ] `adjusted_gross_profit` shall calculate adjusted gross profit.
- [ ] `adjusted_gross_loss` shall calculate adjusted gross loss.
- [ ] `adjusted_net_profit` shall calculate adjusted net profit.
- [ ] `select_net_profit` shall calculate net profit after outlier selection.
- [ ] `select_gross_profit` shall calculate gross profit after outlier selection.
- [ ] `select_gross_loss` shall calculate gross loss after outlier selection.
- [ ] `max_runup` shall calculate maximum gain from valley to peak.
- [ ] `max_runup_date` shall identify the timestamp of maximum runup peak.
- [ ] `calculate_period_analysis` shall calculate performance by timestamp bucket.
- [ ] `calculate_long_short_split` shall calculate long-versus-short profit split.
- [ ] `calculate_session_performance` shall calculate session performance from timestamped records.
- [ ] `whites_reality_check` shall assess data-snooping bias with White's Reality Check.
- [ ] `probability_of_backtest_overfitting` shall estimate probability of backtest overfitting.
- [ ] `walk_forward_degradation_score` shall measure performance decay from in-sample to out-of-sample scores.
- [ ] `bonferroni_correction` shall apply Bonferroni correction for multiple hypothesis testing.
- [ ] `benjamini_hochberg_correction` shall apply Benjamini-Hochberg false-discovery-rate control.
- [ ] `stability_score` shall calculate performance consistency across walk-forward windows.
- [ ] `whites_reality_check_backtests` shall run White's Reality Check against backtest result objects.
- [ ] Documentation must include success examples for each approved official high-level tool.
- [ ] Documentation must include validation-failure examples showing the standard error envelope.
- [ ] Low-level metric examples must be labeled as internal/developer examples when they are not official agent/API tools.

#### `app/__init__.py`

Functions/classes:
- `total_return`
- `return_on_initial_capital`
- `MetricDefinitionCatalog`

Requirements:
- [ ] Undefined or unsupported metric values must be represented as omitted fields or `None` according to the output schema plus structured warnings or skipped-section metadata; they must not be serialized as `NaN`, infinity, fabricated zero, or display-only caps.
- [ ] R-multiple fallback proxies must be listed in the Metric Definition Catalog before use; fallback-derived R-multiple values must include warning metadata and mark the affected metric confidence as degraded.
- [ ] Every official metric must define formula, units, required inputs, optional inputs, accepted aliases, return scale, annualization basis, sample/population convention, minimum sample size, undefined-result behavior, and golden-fixture expectations.
- [ ] `total_return` shall calculate total return as a percentage of initial capital.
- [ ] `return_on_initial_capital` shall calculate net profit as a percentage of initial capital.
- [ ] Numeric outputs must avoid misleading precision and must handle empty, missing, non-finite, zero-denominator, and insufficient-sample scenarios consistently.
- [ ] Documentation must include the Metric Definition Catalog.
- [ ] Official Analytics Tool Catalog is approved and maps every official tool to schemas, errors, metadata, side effects, stability, and tests.
- [ ] Metric Definition Catalog is approved and no official schema references uncataloged metrics.
- [ ] Public/internal export classification is approved, including compatibility aliases and deprecated exports.
- [ ] Analytics-owned private canonical metric-kernel model is documented and enforced through public/internal export classification tests.
- [ ] Schema compatibility matrix defines accepted, deprecated, legacy-adapted, rejected, and unsupported future versions.
- [ ] Decimal monetary precision mandate and deterministic derived-ratio tolerance policy are documented in schemas, metadata, and tests.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/analytics/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/analytics/adapters.py`

Functions/classes:
- `BacktestResult`
- `PaperTradingResult`
- `LiveTradingResult`
- `TradingResult`

Requirements:
- [ ] Backtest, paper, live, portfolio, and normalized trading results must either inherit from a canonical `TradingResult` contract or be converted into it through deterministic adapters.
- [ ] Deterministic adapters must preserve schema version, result ID, phase/environment, timestamps, account base currency, strategy identifiers, symbols, timeframe, trades, equity curve, optional balance curve, benchmark data, upstream quality metadata, and source metadata without silent field loss.
- [ ] Deterministic adapters must define source-to-canonical field mappings, required fields, optional fields, defaulting behavior, unsupported-field behavior, lossless metadata preservation rules, and warning/error behavior for missing or incompatible fields.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Documentation must include adapter field-mapping tables for every supported upstream result type.
#### `app/services/analytics/trade.py`

Functions/classes:
- `AnalyticsReport`
- `build_analytics_report`
- `build_portfolio_analytics_report`
- `calculate_trade_metrics`
- `calculate_equity_metrics`
- `calculate_drawdown_metrics`
- `calculate_risk_metrics`
- `calculate_benchmark_metrics`
- `calculate_statistical_validation`
- `calculate_prop_firm_compliance`
- `get_r_multiples`
- `calculate_efficiency_metrics`
- `compute_r_trade_metrics`
- `compute_trade_metrics`
- `calculate_analytics_for_subset`

Requirements:
- [ ] Official analytics tools must not write files, modify databases, place trades, or require network access.
- [ ] Analytics input conversion must support common developer inputs such as pandas dataframes, pandas series, lists of trade records, and lists of numeric values where the public capability expects them.
- [ ] Trade-oriented tools must use closed-trade semantics when a metric is defined over realized results.
- [ ] Closed-trade filtering must exclude records explicitly marked as still open or end-of-data placeholders and must ignore records without close timestamps when close timestamps are required.
- [ ] Trade classification must distinguish wins, losses, and breakevens using a configured `breakeven_epsilon` from the Metric Definition Catalog or numeric policy ADR so near-zero PnL does not become a false win or loss.
- [ ] Exposure and time-in-market analytics must merge overlapping trade intervals so simultaneous positions are measured as market presence once for duration metrics.
- [ ] Long/short split analytics must classify direction using the supplied trade direction/type fields and must not infer trade direction from PnL.
- [ ] Cost-impact analytics must quantify spread, slippage, and commission drag from supplied cost and gross-profit inputs without mutating the source trades.
- [ ] Aggregated analytics must preserve source context enough for downstream consumers to know whether inputs came from all trades, long trades, short trades, benchmark comparisons, cost analysis, or statistical validation.
- [ ] `AnalyticsReport` output must include summary, trade metrics, equity metrics, return metrics, drawdown metrics, risk metrics, ratio metrics, distribution metrics, benchmark metrics, efficiency metrics, statistical validation, cost breakdown, warnings, quality flags, dashboard payloads, lineage, and metadata when those sections are applicable.
- [ ] Report hashes must include deterministic input hash, config hash, report hash, trade ledger hash, equity curve hash, and optional benchmark hash where the source material exists.
- [ ] ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must approve the initial official high-level tool surface before Builder implementation; candidate tools include `build_analytics_report`, `build_portfolio_analytics_report`, `evaluate_strategy_quality`, `compare_analytics_reports`, `calculate_trade_metrics`, `calculate_equity_metrics`, `calculate_drawdown_metrics`, `calculate_risk_metrics`, `calculate_benchmark_metrics`, `calculate_statistical_validation`, and `calculate_prop_firm_compliance`.
- [ ] Candidate dashboard payloads include summary cards, equity curve chart, drawdown curve chart, monthly returns heatmap, rolling ratio charts, rolling drawdown chart, trade distribution chart, cost breakdown chart, symbol contribution chart, warning table, and quality flag table when source sections exist.
- [ ] `get_closed_trades` shall filter trade records to realized closed trades.
- [ ] `classify_trades` shall classify trades into wins, losses, and breakevens using a consistent threshold.
- [ ] `avg_loss` shall calculate the mean loss of losing trades.
- [ ] `get_r_multiples` shall calculate R-multiples for trades.
- [ ] `trade_pnl_distribution` shall calculate a statistical summary of realized trade PnL.
- [ ] `trade_level_drawdowns` shall calculate cumulative PnL drawdowns at trade close points.
- [ ] `max_close_to_close_drawdown` shall calculate maximum trade-level peak-to-valley decline including excursion context where available.
- [ ] `avg_trade_drawdown` shall calculate mean trade-level close-to-close drawdown depth.
- [ ] `max_consecutive_drawdown_trades` shall calculate maximum number of consecutive trades inside a strategy drawdown.
- [ ] `max_close_to_close_drawdown_date` shall identify the timestamp of deepest trade-level valley.
- [ ] `avg_trade_notional_efficiency` shall provide the capital-efficiency metric under a clearer average-trade-notional name.
- [ ] `avg_return_per_risk_unit` shall calculate average R-multiple per closed trade.
- [ ] `return_per_trade_hour` shall calculate net profit per hour spent in active trades.
- [ ] `return_per_market_hour` shall calculate net profit per hour where at least one trade was open.
- [ ] `trades_per_day` shall calculate average number of closed trades per calendar day in the test period.
- [ ] `profit_per_trade_per_day` shall calculate net profit normalized by both number of trades and calendar days.
- [ ] `mfe_efficiency` shall calculate average percentage of MFE captured by winning trades.
- [ ] `aggregate_mfe_capture_ratio` shall calculate aggregate MFE capture ratio for winning trades.
- [ ] `mae_efficiency` shall calculate realized-loss-to-MAE efficiency for losing trades.
- [ ] `aggregate_loss_containment_efficiency` shall calculate aggregate loss containment for losing trades.
- [ ] `position_size_efficiency` shall calculate relationship between position size and normalized trade outcome.
- [ ] `calculate_efficiency_metrics` shall calculate aggregate MAE/MFE efficiency context from trades.
- [ ] `get_ordered_closed_trades` shall filter closed trades and sort them for sequence-dependent metrics.
- [ ] `total_trades` shall count closed trades.
- [ ] `winning_trades` shall count closed winning trades.
- [ ] `losing_trades` shall count closed losing trades.
- [ ] `breakeven_trades` shall count closed breakeven trades.
- [ ] `long_trades` shall count closed long trades.
- [ ] `short_trades` shall count closed short trades.
- [ ] `count_open_trades` shall count currently open trades.
- [ ] `win_rate` shall calculate percentage of winning trades.
- [ ] `loss_rate` shall calculate percentage of losing trades.
- [ ] `avg_win` shall calculate mean profit of winning trades.
- [ ] `largest_win` shall calculate maximum single-trade profit.
- [ ] `largest_loss` shall calculate maximum single-trade loss.
- [ ] `median_win` shall calculate median PnL of winning trades.
- [ ] `median_loss` shall calculate median PnL of losing trades.
- [ ] `expectancy` shall calculate trade expectancy.
- [ ] `max_consecutive_wins` shall calculate maximum consecutive winning trades.
- [ ] `max_consecutive_losses` shall calculate maximum consecutive losing trades.
- [ ] `avg_time_in_trade` shall calculate average trade duration.
- [ ] `median_time_in_trade` shall calculate median trade duration.
- [ ] `max_time_in_trade` shall calculate maximum trade duration.
- [ ] `min_time_in_trade` shall calculate minimum trade duration.
- [ ] `compute_r_trade_metrics` shall calculate trade metrics from R-multiple inputs.
- [ ] `compute_trade_metrics` shall calculate trade metrics from numeric R values and optional MAE/MFE arrays.
- [ ] `trade_efficiency` shall calculate realized outcome relative to maximum favorable excursion.
- [ ] `trade_outcome_entropy` shall calculate Shannon entropy of trade outcomes.
- [ ] `longest_flat_period_duration` shall calculate longest period without an active trade.
- [ ] `calculate_trade_metrics` shall calculate aggregate core trade metrics from normalized trade records.
- [ ] `calculate_analytics_for_subset` shall calculate all analytics categories for a supplied trade subset.
- [ ] `return_over_drawdown` shall calculate total return relative to maximum trade drawdown.
- [ ] `net_profit_as_percent_of_max_trade_drawdown` shall calculate net profit as a percentage of max trade drawdown.
- [ ] `select_net_profit_as_percent_of_max_trade_drawdown` shall calculate selected net profit as a percentage of max trade drawdown.
- [ ] `adjusted_net_profit_as_percent_of_max_trade_drawdown` shall calculate adjusted net profit as a percentage of max trade drawdown.
- [ ] `net_profit` shall calculate total realized profit or loss from closed trades.
- [ ] `gross_profit` shall sum winning closed-trade profit.
- [ ] `gross_loss` shall sum losing closed-trade loss.
- [ ] `balance_curve_from_closed_trades` shall generate a realized balance curve from closed trades.
- [ ] `balance_curve` shall expose balance-curve behavior as an alias of closed-trade balance curve generation.
- [ ] `equity_curve` shall expose equity-curve behavior for common orchestration using the closed-trade curve.
- [ ] `max_loss_probability` shall calculate probability of a single trade loss exceeding a threshold.
- [ ] `risk_of_ruin` shall estimate ruin probability through Monte Carlo simulation of trade outcomes.
- [ ] `avg_trade_nominal_exposure` shall calculate average nominal exposure per trade.
- [ ] `max_single_trade_margin_utilization` shall calculate maximum margin used by a single trade as a percentage of equity.
- [ ] `avg_single_trade_margin_utilization` shall calculate average margin used per trade as a percentage of equity.
- [ ] `risk_of_ruin_with_custom_horizon` shall estimate ruin probability over a fixed future trade horizon.
- [ ] The module must define concrete maximum accepted input sizes for trades, equity points, benchmark points, portfolio components, dashboard payloads, and statistical observations before production handoff.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/analytics/equity.py`

Functions/classes:
- `NaT`
- `Infinity`
- `VALIDATION_FAILED`
- `calculate_drawdown_metrics`
- `compute_equity_metrics`
- `calculate_return_metrics`

Requirements:
- [ ] Equity and return analytics must sort and normalize supplied series deterministically; optional `NaN`/`NaT` observations may be filtered only with recorded warning metadata, required `NaN`/`NaT` fields must fail validation unless the Metric Definition Catalog marks them skippable, and `Infinity`/`-Infinity` at official boundaries must return `VALIDATION_FAILED`.
- [ ] Dashboard truncation/downsampling must be deterministic and must preserve first point, last point, local extrema where practical, drawdown troughs, equity highs, and timestamps associated with major, critical, or blocker warnings.
- [ ] `benchmark_returns` shall generate a return series from benchmark equity or price values.
- [ ] `relative_drawdown_series` shall generate relative underperformance between strategy and benchmark equity.
- [ ] `drawdown_series` shall calculate drawdown values from an equity curve.
- [ ] `drawdown_duration_series` shall calculate drawdown duration values from an equity curve.
- [ ] `max_drawdown_duration_from_equity` shall calculate maximum drawdown duration from equity values.
- [ ] `max_strategy_drawdown_date` shall identify the timestamp of deepest strategy equity valley.
- [ ] `avg_underwater_drawdown_percent` shall calculate average drawdown depth while equity is below peak.
- [ ] `calculate_drawdown_metrics` shall calculate aggregate drawdown metrics from an equity curve.
- [ ] `compute_equity_metrics` shall calculate equity metrics from return inputs.
- [ ] `total_return_usd` shall calculate total return in currency units from an equity curve.
- [ ] `returns_series` shall calculate percentage returns between equity points.
- [ ] `log_returns_series` shall calculate logarithmic returns between equity points.
- [ ] `daily_returns` shall calculate daily percentage returns from an equity curve.
- [ ] `weekly_returns` shall calculate weekly percentage returns from an equity curve.
- [ ] `monthly_returns` shall calculate monthly percentage returns from an equity curve.
- [ ] `annual_returns` shall calculate annual percentage returns from an equity curve.
- [ ] `calculate_return_metrics` shall calculate aggregate cumulative and average returns from an equity curve.
- [ ] No file-specific non-functional requirements defined.
- [ ] Official analytics tools must validate `request_id`; missing, empty, malformed, or unsafe request IDs must return a structured validation error envelope.
- [ ] Official analytics tools must return the standard tool envelope on success and on controlled validation failure.
- [ ] Date/time analytics must parse supplied open/close timestamps, support both datetime-like and numeric timestamp inputs where implemented, and return JSON-safe values for durations and timestamps.
- [ ] Live-vs-backtest and paper-vs-backtest degradation comparisons must validate strategy ID, strategy version, symbols, timeframe or return frequency, evaluation window, account base currency, and comparable cost/slippage model metadata before pairing.
- [ ] `win_loss_streaks` shall return winning and losing streak sequences.
- [ ] `kelly_criterion` shall calculate Kelly criterion percentage from R-multiples or returns.
- [ ] `avg_monthly_return` shall calculate arithmetic average monthly return.
- [ ] `monthly_return_stddev` shall calculate monthly return volatility.
- [ ] `annualized_return` shall calculate geometric annualized return.
- [ ] `geometric_mean_return` shall calculate geometric mean return.
- [ ] `best_return` shall calculate best single-period return.
- [ ] `worst_return` shall calculate worst single-period return.
- [ ] `buy_and_hold_return` shall calculate total buy-and-hold return from price data.
- [ ] `return_volatility` shall calculate return standard deviation.
- [ ] `downside_return_volatility` shall calculate volatility of returns below target.
- [ ] `return_skewness` shall calculate return-distribution skewness.
- [ ] `return_kurtosis` shall calculate return-distribution excess kurtosis.
- [ ] `return_on_account` shall calculate return on required account size.
#### `app/services/analytics/drawdown.py`

Functions/classes:
- `calculate_drawdown_series`
- `max_drawdown`
- `drawdown_duration`
- `drawdown_recovery`
- `underwater_curve`

Requirements:
- [ ] Strategy-quality evaluation must rely only on the supplied report payload and must surface warnings for weak profitability, high drawdown, overfitting risk, small sample size, or other observable quality concerns.
- [ ] Optional sections such as TCA metrics, attribution, prop-firm compliance evidence, drawdown distribution, tail-risk metrics, dynamic correlation, walk-forward analytics, metric comparisons, live degradation, and explainability must be represented as calculated, skipped, or failed.
- [ ] Formula definitions must be explicit for Sharpe, Sortino, Calmar, Jensen alpha, beta, tracking error, information ratio, VaR, CVaR, expected shortfall, SQN, Kelly, drawdown duration, CAGR, profit factor, expectancy, and R-multiple metrics before those metrics are locked as official contracts.
- [ ] `max_relative_drawdown_percent` shall calculate maximum relative underperformance as a positive percentage.
- [ ] `max_strategy_drawdown` shall calculate deepest peak-to-valley decline in currency units.
- [ ] `max_strategy_drawdown_percent` shall calculate deepest percentage decline relative to running peak.
- [ ] `max_drawdown` shall calculate maximum drawdown from returns.
- [ ] `avg_drawdown` shall calculate average drawdown depth.
- [ ] `drawdown_distribution` shall calculate detailed drawdown distribution statistics.
- [ ] `max_drawdown_duration_from_returns` shall calculate maximum drawdown duration from return values.
- [ ] `max_drawdown_duration` shall calculate maximum drawdown duration from the selected input type.
- [ ] `avg_drawdown_duration` shall calculate average duration of drawdown episodes.
- [ ] `time_to_recovery` shall calculate recovery periods for unique drawdowns.
- [ ] `recovery_factor` shall calculate net profit relative to maximum drawdown.
- [ ] `max_close_to_close_drawdown_percent` shall calculate close-to-close drawdown as a percentage.
- [ ] `account_size_required` shall estimate capital required to withstand max close-to-close dips.
- [ ] `avg_yearly_max_drawdown` shall average the maximum drawdown observed in each year.
- [ ] `ulcer_index` shall calculate squared-drawdown-based ulcer index.
- [ ] `pain_index` shall calculate mean absolute percentage drawdown.
- [ ] `pain_ratio` shall calculate return relative to pain index.
- [ ] `calmar_ratio` shall calculate annualized return relative to maximum drawdown.
- [ ] `fouse_ratio` shall calculate Fouse drawdown-index-style ratio.
- [ ] `sterling_ratio` shall calculate CAGR relative to adjusted average yearly maximum drawdown.
- [ ] `rina_index` shall calculate select net profit relative to average drawdown and time in market.
- [ ] `net_profit_as_percent_of_max_strategy_drawdown` shall calculate net profit as a percentage of max strategy drawdown.
- [ ] `select_net_profit_as_percent_of_max_strategy_drawdown` shall calculate selected net profit as a percentage of max strategy drawdown.
- [ ] `adjusted_net_profit_as_percent_of_max_strategy_drawdown` shall calculate adjusted net profit as a percentage of max strategy drawdown.
- [ ] `return_on_max_strategy_drawdown` shall calculate total return relative to maximum strategy drawdown.
- [ ] `return_on_max_close_to_close_drawdown` shall calculate net profit relative to maximum close-to-close drawdown.
- [ ] `drawdown_probability` shall calculate probability of drawdown exceeding a threshold.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/analytics/risk.py`

Functions/classes:
- `calculate_risk_metrics`

Requirements:
- [ ] Official analytics tools must be low-risk, read-only operations.
- [ ] Metadata must include tool name, tool version, tool category, tool risk level, request ID, execution time, and side-effect flags.
- [ ] R-multiple analytics must prefer explicit initial-risk fields when available and fall back only to documented analytics proxies when risk fields are absent.
- [ ] Official analytics tool responses must include metadata, side-effect flags, risk flags, execution timing, and structured errors.
- [ ] Metric definitions must document default configuration sources for annualization, risk-free rate, breakeven tolerance, minimum sample size, bootstrap count limits, dashboard limits, FX stale-rate limits, and confidence/alpha levels when those defaults are approved.
- [ ] Strategy-quality scorecards must not make final live approval, promotion, prop-firm enforcement, or risk-governor decisions.
- [ ] Strategy-quality outputs must not claim final approval, promotion, live-readiness, prop-firm compliance enforcement, risk-limit approval, or portfolio allocation authority.
- [ ] `risk_adjusted_efficiency` shall calculate return relative to total defined initial risk.
- [ ] `profit_per_pip_risk` shall calculate reward-to-risk based on profit pips relative to MAE pips.
- [ ] `upside_potential_ratio` shall calculate upside potential relative to downside risk.
- [ ] `volatility` shall calculate return standard deviation as a positive percentage.
- [ ] `annualized_volatility` shall calculate annualized volatility as a positive percentage.
- [ ] `downside_volatility` shall calculate downside deviation as a positive percentage.
- [ ] `value_at_risk` shall calculate value-at-risk as a positive percentage.
- [ ] `conditional_var` shall calculate conditional value-at-risk as a positive percentage.
- [ ] `expected_shortfall` shall calculate expected shortfall.
- [ ] `max_nominal_exposure_simple` shall calculate maximum nominal exposure held at one time.
- [ ] `max_gross_exposure` shall calculate maximum gross nominal exposure.
- [ ] `exposure_time_ratio` shall calculate percentage of total period spent in market.
- [ ] `time_weighted_avg_exposure` shall calculate time-weighted average notional exposure.
- [ ] `portfolio_margin_utilization_curve` shall generate portfolio margin-utilization curve over time.
- [ ] `compounding_risk_of_ruin` shall estimate ruin probability with dynamic compounding risk.
- [ ] `historical_var_by_symbol` shall calculate historical value-at-risk by symbol.
- [ ] `portfolio_var_from_covariance` shall calculate portfolio value-at-risk from covariance and weights.
- [ ] `calculate_risk_metrics` shall calculate aggregate risk metrics such as VaR, CVaR, and volatility.
- [ ] Tool metadata must consistently identify the category as `analytics` and risk level as `low`.
- [ ] Analytics input and output contracts must remain aligned with Simulation, Optimization, Risk, Portfolio, Trading receipt, and UI/API contracts.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Redaction rules must apply to sensitive keys and sensitive-looking values in inputs, warnings, errors, logs, metadata, and diagnostic details.
- [ ] Low-level metric helpers such as individual average, skewness, kurtosis, tail-ratio, tracking-error, ulcer-index, omega-ratio, payoff-ratio, and date helper functions must remain internal/support-only unless explicitly promoted by the Official Analytics Tool Catalog.
- [ ] Warnings and quality flags must include code, severity, affected section, source context, and enough bounded detail for downstream review.
- [ ] Warning and quality-flag catalogs must define code, severity, affected section, source-backed status, whether the flag blocks promotion, bounded detail rules, and linked test fixtures.
- [ ] Explainability outputs must distinguish explained PnL, unexplained PnL, explained variance percentage, sample count, and driver stability when those inputs are supplied.
#### `app/services/analytics/ratios.py`

Functions/classes:
- `calculate_ratio_metrics`

Requirements:
- [ ] `benchmark_information_ratio` shall expose benchmark information ratio without colliding with the ratios module export.
- [ ] `up_down_capture` shall calculate up-capture and down-capture ratios.
- [ ] `metrics_win_rate_fraction` shall expose metrics-module win-rate fraction behavior without colliding with ratios exports.
- [ ] `metrics_expectancy` shall expose metrics-module expectancy behavior without colliding with ratios exports.
- [ ] `metrics_expectancy_r` shall expose metrics-module R-expectancy behavior without colliding with ratios exports.
- [ ] `ratios_win_rate_fraction` shall expose ratios-module win-rate fraction behavior without colliding with metrics exports.
- [ ] `sharpe_ratio` shall calculate excess return per unit of volatility.
- [ ] `annualized_sharpe_ratio` shall calculate annualized Sharpe ratio from monthly inputs.
- [ ] `sortino_ratio` shall calculate excess return per unit of downside volatility.
- [ ] `ratios_information_ratio` shall expose ratios-module information ratio without colliding with benchmark exports.
- [ ] `omega_ratio` shall calculate probability-weighted gains relative to losses.
- [ ] `gain_to_pain_ratio` shall calculate gains relative to absolute negative returns.
- [ ] `kappa_ratio` shall calculate generalized Sortino-style Kappa ratio.
- [ ] `profit_factor` shall calculate gross profit relative to gross loss.
- [ ] `payoff_ratio` shall calculate average win relative to average loss.
- [ ] `edge_ratio` shall calculate payoff edge adjusted by win rate.
- [ ] `profit_to_mae_ratio` shall calculate profit capture relative to adverse excursion.
- [ ] `mfe_to_mae_ratio` shall calculate favorable excursion relative to adverse excursion.
- [ ] `expectancy_over_std` shall calculate expectancy stability relative to standard deviation.
- [ ] `net_profit_as_percent_of_largest_loss` shall calculate net profit as a percentage of largest loss.
- [ ] `select_net_profit_as_percent_of_largest_loss` shall calculate selected net profit as a percentage of largest loss.
- [ ] `adjusted_net_profit_as_percent_of_largest_loss` shall calculate adjusted net profit as a percentage of largest loss.
- [ ] `adjusted_profit_factor` shall calculate adjusted gross profit relative to adjusted gross loss.
- [ ] `select_profit_factor` shall calculate selected gross profit relative to selected gross loss.
- [ ] `ratios_expectancy` shall expose ratios-module expectancy behavior without colliding with metrics exports.
- [ ] `ratios_expectancy_r` shall expose ratios-module R-expectancy behavior without colliding with metrics exports.
- [ ] `calculate_ratio_metrics` shall calculate aggregate ratio metrics from return values.
- [ ] Architectural Mandate: derived ratios may use deterministic `float64` arithmetic only where exact decimal arithmetic is not appropriate, with documented tolerance stored in configuration, tests, and report metadata.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] The module must degrade safely when optional acceleration libraries are unavailable.
- [ ] Calculations over large datasets must use vectorized operations where feasible and must degrade to bounded chunked processing with warnings when vectorization or memory limits are exceeded.
- [ ] Shared caches, if implemented, must be concurrency-safe or read-through and keyed by input hash, configuration hash, and analytics engine version.
- [ ] Long-series cumulative operations must use numerically stable methods where feasible and must document any approximation or chunking behavior.
- [ ] Duplicate timestamps must be rejected or resolved deterministically according to configuration and recorded in diagnostics.
- [ ] Invalid or missing required inputs must fail with a structured error envelope, not an uncaught exception. Custom analytics exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
- [ ] `time_in_market_duration` shall calculate total duration where at least one position was open.
- [ ] `trading_period_duration` shall calculate total duration of the trading period.
- [ ] `deflated_sharpe_ratio` shall adjust Sharpe ratio diagnostics for multiple testing and non-normality.
#### `app/services/analytics/distributions.py`

Functions/classes:
- `calculate_distribution_metrics`

Requirements:
- [ ] `return_distribution` shall calculate a statistical summary of returns.
- [ ] `r_multiple_distribution` shall calculate a statistical summary of R-multiple values.
- [ ] `distributions_r_multiple_distribution` shall expose distribution-module R-multiple distribution behavior without colliding with metrics exports.
- [ ] `percentile_summary` shall return selected percentile values.
- [ ] `upside_downside_summary` shall summarize positive and negative outcome distributions.
- [ ] `skewness` shall calculate return or value skewness.
- [ ] `kurtosis` shall calculate excess kurtosis.
- [ ] `higher_moments` shall calculate detailed skewness and kurtosis context.
- [ ] `fat_tail_score` shall estimate tail heaviness relative to normal behavior.
- [ ] `tail_ratio` shall calculate the ratio between upper-tail and lower-tail percentile magnitudes.
- [ ] `jarque_bera_test` shall run a Jarque-Bera normality diagnostic.
- [ ] `shapiro_wilk_test` shall run a Shapiro-Wilk normality diagnostic.
- [ ] `qq_plot_data` shall generate theoretical and actual quantile data for Q-Q plotting.
- [ ] `fit_distribution` shall fit a theoretical distribution and return fit parameters.
- [ ] `distribution_fit_quality` shall return fit-quality diagnostics such as likelihood and information criteria.
- [ ] `histogram_data` shall generate histogram bin data for plotting.
- [ ] `detect_outliers` shall identify outliers with the requested method and threshold.
- [ ] `outlier_ratio` shall calculate the percentage of data points flagged as outliers.
- [ ] `calculate_distribution_metrics` shall calculate aggregate distribution metrics from numeric values.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Analytics behavior must be deterministic for the same inputs except where Monte Carlo, bootstrap, or permutation features intentionally use randomness; those features should support explicit seeds.
- [ ] Statistical validation tools must expose deterministic options such as seeds, bootstrap/permutation counts, block sizes, confidence levels, alpha levels, and sample-size thresholds where supported.
- [ ] `metrics_r_multiple_distribution` shall calculate R-multiple distribution statistics.
- [ ] `permutation_test` shall run significance testing through random reshuffling or sign-flipping.
- [ ] `bootstrap_confidence_intervals` shall estimate metric uncertainty with non-parametric bootstrap.
- [ ] `bootstrap_probability_above_threshold` shall estimate probability that a bootstrapped metric exceeds a threshold.
- [ ] `permutation_test_backtest` shall run permutation testing against a backtest result object.
- [ ] `bootstrap_confidence_intervals_backtest` shall estimate bootstrap confidence intervals from a backtest result object.
#### `app/services/analytics/benchmark.py`

Functions/classes:
- `calculate_benchmark_metrics`

Requirements:
- [ ] Benchmark analytics must align strategy and benchmark return streams before comparison and must handle missing or non-overlapping periods safely.
- [ ] Benchmark metrics must only be calculated after deterministic alignment of strategy and benchmark series.
- [ ] Strategy and benchmark timestamps must be normalized to UTC before alignment.
- [ ] Benchmark data must be restricted to the strategy analytics window unless explicit lookback is configured and recorded.
- [ ] Missing benchmark currency metadata must emit a warning and restrict calculations to currency-neutral metrics unless a validated currency policy exists.
- [ ] Portfolio analytics must not sum raw PnL across different profit currencies.
- [ ] Portfolio, TCA, and base-currency analytics must require validated FX conversion data when source money values are in different currencies.
- [ ] Missing required FX conversion data must produce blocker-level quality evidence for affected multi-currency portfolio or TCA sections.
- [ ] Stale FX rates must be identified when FX age limits are configured, and affected converted values must be marked as estimated when stale data is used.
- [ ] All money fields must include explicit currency or inherit a validated account base currency with lineage explaining the inheritance.
- [ ] `beta` shall calculate the strategy beta coefficient relative to benchmark returns.
- [ ] `alpha` shall calculate annualized Jensen-style alpha relative to benchmark returns.
- [ ] `r_squared` shall calculate coefficient of determination between strategy and benchmark returns.
- [ ] `tracking_error` shall calculate annualized tracking error between strategy and benchmark returns.
- [ ] `information_ratio` shall calculate relative Sharpe-style information ratio.
- [ ] `batting_average` shall calculate the percentage of periods where the strategy outperformed the benchmark.
- [ ] `calculate_benchmark_metrics` shall calculate combined benchmark-relative metrics such as alpha and beta.
- [ ] The module must not overstate strategy quality, robustness, or live readiness; report outputs should expose caveats where sample size, overfitting, missing benchmark, or partial data weaken confidence.
- [ ] All timestamps must be timezone-aware or explicitly normalized to UTC before metric calculation, benchmark alignment, report hashing, or dashboard payload generation.
- [ ] ADR Required: `ADR-ANALYTICS-LIMITS` must record exact maximum input sizes, response payload limits, runtime budgets, memory budgets, statistical iteration limits, dashboard point limits, reference hardware, and benchmark method before Builder handoff.
- [ ] Performance benchmark tests must fail the handoff gate until `ADR-ANALYTICS-LIMITS` supplies exact dataset sizes, hardware profile, benchmark method, runtime thresholds, memory thresholds, and statistical-validation iteration limits.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/analytics/efficiency.py`

Functions/classes:
- `capital_efficiency`
- `return_per_unit_mae`
- `return_per_unit_mfe`
- `exposure_efficiency`

Requirements:
- [ ] `capital_efficiency` shall calculate return per unit of nominal capital deployed.
- [ ] `return_per_unit_mae` shall calculate total return relative to adverse excursion experienced.
- [ ] `return_per_calendar_day` shall calculate net profit per calendar day in the test period.
- [ ] `exit_efficiency` shall calculate combined win-capture and loss-containment efficiency.
- [ ] `loss_containment_efficiency` shall calculate how well realized losses stayed above their adverse excursion.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] `median_mae_mfe` shall calculate median MAE and MFE values.
- [ ] `get_mae_mfe_r` shall calculate MAE and MFE normalized to R-space.
- [ ] `median_mae_r` shall calculate median MAE in R-multiple terms.
- [ ] `median_mfe_r` shall calculate median MFE in R-multiple terms.
#### `app/services/analytics/scorecard.py`

Functions/classes:
- `MetricDefinition`
- `ScorecardRule`
- `ScorecardResult`
- `evaluate_scorecard`
- `validate_metric_catalog`

Requirements:
- [ ] No metric may be referenced in an official tool schema, report schema, dashboard payload, scorecard rule, warning rule, or quality-flag rule until its Metric Definition Catalog entry is approved.
- [ ] Metric definitions must document whether outputs are calculated facts, diagnostic estimates, warning evidence, scorecard inputs, or non-binding review context.
- [ ] `evaluate_strategy_quality` shall evaluate a supplied analytics report and return strategy-quality decision context, score, strengths, warnings, and recommended action.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Public registry changes must remain auditable through tests and catalog updates.
- [ ] The module must separate calculated facts from warnings, caveats, decisions, and recommended actions.
- [ ] Official agent/API-facing analytics tools must be high-level, documented, typed, schema-compliant, traceable, and listed in the Official Analytics Tool Catalog.
- [ ] Every official analytics tool must have a documented input schema and output schema, including required fields, optional fields, default values, accepted aliases, units, validation errors, warning codes, and JSON-safe serialization behavior.
- [ ] Low-level metric kernels must not be exposed as official agent/API tools unless explicitly approved in the Official Analytics Tool Catalog.
- [ ] Official analytics tools must log call start, validation failure, successful completion, controlled warning, and execution failure without logging secrets or full raw private payloads.
- [ ] Warning severity must support at least informational, warning, major, critical, and blocker-level meanings.
- [ ] Quality flags must separate raw metrics, normalized score inputs, penalty flags, hard blockers, recommendation evidence, and final governance decisions.
- [ ] Strategy-quality and prop-firm outputs must be labeled as non-binding analytics evidence or decision context only.
- [ ] `sqn` shall calculate system quality number.
- [ ] `sample_size_warning` shall assess metric reliability based on sample size.
- [ ] Documentation must include the Official Analytics Tool Catalog.
- [ ] Documentation must include the warning-code and quality-flag catalog.
#### `app/services/analytics/report.py`

Functions/classes:
- `AnalyticsReport`
- `PortfolioAnalyticsReport`

Requirements:
- [ ] Overview/report tools must combine lower-level analytics into grouped payloads that remain serializable for API and dashboard consumers.
- [ ] The module must generate a complete, versioned `AnalyticsReport` from a valid backtest, optimization candidate, out-of-sample, walk-forward, paper, live, or normalized trading result when required inputs are available.
- [ ] Report building must validate inputs, normalize result data, run required metric groups, run optional metric groups, collect warnings and quality flags, build dashboard payloads, validate output, compute hashes, and return a standard tool response.
- [ ] Missing optional inputs must produce warnings or skipped-section metadata rather than fabricated metric values.
- [ ] Critical metric group failures must return an error unless diagnostic partial mode is explicitly configured.
- [ ] Partial reports must include `report_status = "partial"`, affected sections, skipped/failed/degraded section metadata, warnings, quality flags, lineage, and JSON-safe values.
- [ ] Report generation must define section criticality as required, optional, diagnostic-only, disabled, skipped, failed, or degraded.
- [ ] Required-section failure must return an error unless diagnostic partial mode is explicitly enabled.
- [ ] Optional-section failure must produce skipped or failed section metadata without fabricating the missing section.
- [ ] Partial reports must be marked non-promotable and must not be consumed as final approval evidence.
- [ ] Report metadata must preserve `request_id`, optional `workflow_id`, run IDs, strategy identifiers, strategy version, schema version, analytics engine version, annualization settings, optional-section status, source context, and creation time.
- [ ] Hashing rules must exclude non-deterministic fields such as generation timestamps unless explicitly documented.
- [ ] Hashes must be computed from canonical JSON serialization with deterministic key ordering, documented numeric normalization, and documented exclusion rules for non-deterministic fields.
- [ ] Analytics must propagate upstream data-quality and bias evidence into report warnings and quality flags.
- [ ] Dashboard payload builders must consume validated `AnalyticsReport` sections and must not recompute core metrics.
- [ ] `format_summary_as_rows` shall format raw summary data into report/display rows.
- [ ] `build_backtest_report` shall build a structured backtest analytics report payload.
- [ ] `print_statistical_validation_report` shall package a comprehensive statistical validation report.
- [ ] Report generation must be idempotent for the same input, configuration, and analytics engine version.
- [ ] Reports must include reproducibility metadata, input hashes, configuration hashes, report hashes, and lineage.
- [ ] Annualized metrics must use explicit annualization settings stored in configuration and report metadata; the module must not silently guess annualization when frequency cannot be inferred safely.
- [ ] Cache hits, misses, evictions, and concurrent duplicate requests must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes.
- [ ] Sequential and parallel execution over the same report inputs must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes.
- [ ] Warning and quality-flag ordering must be deterministic where output hashes, dashboard payloads, report comparison, or tests depend on order.
- [ ] Architectural Mandate: canonical monetary sums, cost aggregation, and base-currency aggregation must use `Decimal` normalization for hashing and report contracts.
- [ ] Report metadata must identify the monetary precision mode used, such as `decimal` or `float64_with_tolerance`.
- [ ] The module must define concrete runtime limits for bootstrap, permutation, Monte Carlo, distribution fitting, dashboard downsampling, and report generation before production handoff.
- [ ] `build_analytics_report` latency, statistical-validation runtime, throughput, memory, and payload-size targets must be measurable before Builder handoff.
- [ ] Documentation must include report section criticality and partial-report behavior.
- [ ] Documentation must include schema compatibility policy for accepted, deprecated, legacy-adapted, and unsupported report/result versions.
- [ ] Documentation must include partial-report examples showing skipped, failed, and degraded section metadata.
- [ ] `TradingResult`, `AnalyticsReport`, `PortfolioAnalyticsReport`, dashboard payloads, warning objects, quality flags, and error envelopes have versioned schemas.
- [ ] Report section criticality and partial-report non-promotable behavior are approved.
- [ ] Requirement-to-test traceability matrix maps every official tool, report contract, adapter mapping, warning/quality flag, and failure envelope to tests.
- [ ] Usage examples cover success, validation failure, partial report, dashboard truncation, and request-ID traceability.
- [ ] No file-specific non-functional requirements defined.
- [ ] Final analytics responses must not contain `NaN`, `inf`, `-inf`, invalid JSON values, pandas objects, NumPy objects, raw dataframes, raw series, or other unserializable values.
#### `app/services/analytics/dashboard.py`

Functions/classes:
- `build_overview_payload`

Requirements:
- [ ] Dashboard payloads must include chart/table data, finite numeric values, ISO-8601 timestamps, units, warnings, and metadata sufficient for UI/API consumers.
- [ ] If a required source section is missing, failed, skipped, or degraded, the dashboard payload must include section-status metadata and warnings rather than recomputing or fabricating chart/table values.
- [ ] Dashboard/UI consumers must not need to recalculate core metrics.
- [ ] Dashboard payload support must be classified by chart/table type as required, optional, or future before Builder implementation.
- [ ] Truncated payload metadata must include whether truncation occurred, original point count, returned point count, truncation method or algorithm, and truncation reason.
- [ ] `build_overview_payload` shall build the API/dashboard analytics overview payload.
- [ ] Result payloads must be JSON-safe or convertible to JSON-safe structures for API and dashboard consumers.
- [ ] Dashboard payloads must obey configured size limits and deterministic truncation policies when limits are defined.
- [ ] The module must define concrete maximum response payload size and deterministic truncation behavior for dashboard and API payloads before production handoff.
- [ ] Documentation must include required, optional, and future dashboard payload classes.
- [ ] Documentation must include dashboard truncation examples showing truncation metadata.
- [ ] Concrete input-size, runtime, memory, response-size, dashboard truncation, statistical iteration, and performance targets are approved with a hardware/profile context.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
### Unit Tests Required

```text
tests/unit/app/services/analytics/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/06_analytics.py
```

Usage examples must show:
- `example_01_trade_and_equity_metrics`: Demonstrate trade summaries, equity curves, returns, and canonical metric definitions.
- `example_02_drawdown_and_risk_metrics`: Demonstrate drawdown series, max drawdown, recovery, risk ratios, and undefined-result behavior.
- `example_03_distribution_and_benchmark_metrics`: Demonstrate distribution stats, benchmark comparisons, and missing benchmark handling.
- `example_04_efficiency_metrics`: Demonstrate capital efficiency, return per MAE/MFE, exposure efficiency, and warning metadata.
- `example_05_scorecard_evaluation`: Demonstrate scorecard rules, warning flags, metric catalog validation, and failed/skipped sections.
- `example_06_report_generation`: Demonstrate report payload generation, markdown/json serialization, provenance, and reproducibility hashes.
- `example_07_dashboard_payloads`: Demonstrate dashboard-ready payloads, chart/table data, and schema-versioned outputs.
- `example_08_read_only_boundaries`: Demonstrate analytics read-only behavior and lack of trading/risk approval authority.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 460 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(analytics-service): implement phase 6 analytics service requirements
```


- [ ] Analytics output must not include secrets, credentials, broker tokens, authorization headers, or private raw provider payloads.
- [ ] Analytics outputs used by UI/API must remain backward-compatible or be versioned when payload structure changes.
## Phase 7 Trading Service

### Goal

The Trader service layer provides the dedicated trading boundary for HaruQuantAI.
The module exposes a unified trading interface supporting MT5, cTrader, and Simulator providers through `app/routes/brokers.py`.
The Trader services own broker-compatible trading operations, validation, execution readiness checks, reconciliation support, and trading state retrieval while maintaining MQL5-compatible behavior where applicable.


Task inventory: 84 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/trader/`.
- Requires Phase 6 Analytics Service contracts to be available where referenced by `07_trading.md`.

### Files to Create

```text
app/services/trader/
app/routes/brokers.py
data/persistence
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/trader/executor.py`

Functions/classes:
- `TradeExecutor`
- `submit_market_order`
- `submit_pending_order`
- `modify_pending_order`
- `cancel_pending_order`
- `close_position`
- `modify_stops`

Requirements:
- [ ] Submit market orders.
- [ ] Submit pending orders.
- [ ] Modify pending orders.
- [ ] Cancel pending orders.
- [ ] Close positions fully or partially.
- [ ] Kill-Switch Behavior**: Under active kill-switch status, block all new trade requests, cancel all active pending orders immediately, and support a configurable option to flatten all open positions.
- [ ] Align order types precisely: Market, Limit, and Stop orders.
- [ ] Align trade request field naming to mirror MQL5 `MqlTradeRequest` structure.
- [ ] Implement fill policies (Fill or Kill, Immediate or Cancel, Return) mirroring MQL5's `CTrade` and `OrderSend` contracts.
- [ ] Correlation IDs**: All requests, responses, and events must propagate structural correlation, trace, and request IDs.
- [ ] Stop accepting new trade requests immediately.
- [ ] Cancel any locally tracked pending orders that have not been acknowledged by the broker.

#### `app/services/trader/validation.py`

Functions/classes:
- `TradeValidationResult`
- `validate_trade_request`
- `validate_symbol`
- `validate_volume`
- `validate_price`
- `validate_slippage`
- `validate_market_session`

Requirements:
- [ ] Modify stop-loss and take-profit levels.
- [ ] Return execution/fill details (filled volume, average price, remaining volume) in the result envelope.
- [ ] Validate slippage against a configurable tolerance, rejecting/warning if exceeded.
- [ ] Retrieve account dealing mode (Netting vs. Hedging) and cache it.
- [ ] Retrieve symbol information.
- [ ] Validate symbols.
- [ ] Validate trade volumes.
- [ ] Validate prices.
- [ ] Validate stop-loss and take-profit geometry.
- [ ] Validate margin requirements.
- [ ] Validate order requests against malicious payloads and out-of-bound arguments.
- [ ] Validate expiration values.
- [ ] Validate broker constraints.
- [ ] Dealing Mode Check**: Validate that position modification and closure requests are compatible with the cached account dealing mode (Netting vs. Hedging).
- [ ] Market Session Check**: Validate that the requested action is allowed during current active market sessions (e.g., prevent new positions during weekend rollover, even if connected).
- [ ] Decimal & Precision Normalization**: Ensure that all financial values (price, volume, SL/TP) are parsed into high-precision decimal objects and rounded/truncated according to the broker's specific digits and volume step parameters before routing.
- [ ] Validate broker connectivity.
- [ ] Validate market availability.
- [ ] Validate account permissions.
- [ ] Validate account readiness.
- [ ] Validate margin availability.
- [ ] Aggregate readiness checks before execution.
- [ ] Idempotency Key Scope**: Compute idempotency keys using a hash of specific request attributes: `(account_id, symbol, action_type, volume, price, slippage, timestamp_window)`.
- [ ] Verify rate limit health as part of the execution readiness checks.
- [ ] Fail-Closed**: Trading operations shall fail closed on invalid readiness conditions, active kill-switch status, or if the startup reconciliation gate is blocked.
- [ ] Serialized Execution**: Trading requests within the same `(account, symbol)` scope must be executed sequentially (e.g., serialized via an async lock or queue) to prevent interleaved state modification.
- [ ] Parameter Sanitization**: All broker-bound parameters must be strictly typed, sanitized, and validated before leaving the trading boundary.
- [ ] Contract Tests**: Validate the broker adapter interface against actual broker API behaviors to catch breaking upstream changes.

#### `app/services/trader/reporting.py`

Functions/classes:
- `ExecutionQualityReport`
- `TradingReport`
- `record_trading_metric`
- `emit_trading_alert`

Requirements:
- [ ] Partial Fill Strategy**: Return partial fill details directly to the Strategy/Risk caller rather than auto-chasing, with configurable behavior support.
- [ ] Generate trading reports.
- [ ] Include validation warnings.
- [ ] Alerting Rules**:
- [ ] Telemetry**: Propagate trace context through broker calls if supported by the provider SDK.
- [ ] Redaction**: Secrets, credentials, and API tokens must be redacted and never leaked to logs, error messages, or telemetry.

#### `app/services/trader/reconciliation.py`

Functions/classes:
- `ReconciliationResult`
- `compare_trade_state`
- `reconcile_orders`
- `reconcile_positions`
- `startup_reconciliation_gate`

Requirements:
- [ ] Retrieve account information.
- [ ] Retrieve position information.
- [ ] Retrieve pending order information.
- [ ] Retrieve historical order information.
- [ ] Retrieve historical deal information.
- [ ] Retrieve terminal information.
- [ ] Detect missing records.
- [ ] Detect mismatched records.
- [ ] Prevent unsafe retries after "unknown outcome" errors.
- [ ] Run scheduled reconciliation at configurable intervals (e.g., every N minutes).
- [ ] Trigger reconciliation on startup and immediately following any "unknown outcome" broker error.
- [ ] Support a flag that blocks trading execution until the initial reconciliation pass completes successfully.
- [ ] Include reconciliation summaries.
- [ ] Startup Reconciliation Gate**: Trading execution must be blocked at startup until the initial reconciliation pass completes successfully.
- [ ] Explicit Timeout Definition**: Synchronous broker calls must enforce explicit timeout thresholds (e.g., 5 seconds). Any request exceeding this threshold must be classified as an Unknown Outcome, disable automatic retries, and trigger forced reconciliation.
- [ ] Trigger a P1 critical alert if reconciliation drift exceeds a configurable monetary amount or a percentage of account equity.
- [ ] Chaos Engineering**: Inject random broker disconnections and delayed adapter responses during E2E testing to verify circuit breaker and reconciliation resilience.

#### `app/services/trader/throttling.py`

Functions/classes:
- `ProviderRateLimiter`
- `ConcurrencyQueue`
- `check_rate_limit_health`
- `shutdown_trade_queue`

Requirements:
- [ ] Verify that the provider rate-limiting threshold has not been exceeded.
- [ ] Configure and enforce a per-provider rate limiter (token bucket algorithm) for each broker instance.
- [ ] Apply rate limits to all outbound API calls to prevent bans or IP blocking.
- [ ] Trigger warning logs and flags if rate limit capacity utilization exceeds 80% for more than 5 consecutive minutes.
- [ ] Shutdown Sequence**: When the service is shutting down or redeploying, it must:
- [ ] Allow in-flight requests to resolve within a configurable timeout window.

#### `app/services/trader/store.py`

Functions/classes:
- `TradeStore`
- `IdempotencyRecord`
- `generate_trade_request_id`
- `compute_idempotency_key`
- `detect_duplicate_request`

Requirements:
- [ ] Generate deterministic request identifiers.
- [ ] Detect duplicate requests using idempotency records.
- [ ] Reject conflicting duplicate requests.
- [ ] Enforce TTL (Time-To-Live) and lifecycle stages on idempotency keys.
- [ ] Handle concurrency collisions with "already in progress" responses to avoid race conditions.
- [ ] Compare internal state (via `TradeStore`) against broker state.
- [ ] Collision Protection**: Attempts to submit duplicate request IDs before the original is finalized must be rejected immediately.
- [ ] Metrics**: Track latency, failure rates, reconciliation drift, rate limit utilization, and idempotency hits.
- [ ] Flush final reconciliation states and active idempotency logs to the `TradeStore`.
- [ ] E2E Reconciliation & Idempotency Testing**: Implement specific test suites that inject network drops, simulate unknown outcomes, and verify correct recovery, deduplication, and reconciliation.

#### `app/services/trader/errors.py`

Functions/classes:
- `TradingError`
- `TradingTimeoutError`
- `UnknownOutcomeError`
- `classify_broker_error`

Requirements:
- [ ] Map error codes to standard codes that match MQL5 retcode behaviors (e.g., `TRADE_RETCODE_REQUOTE`, `TRADE_RETCODE_PRICE_OFF`).
- [ ] Error Classification**: Errors must be classified into transient vs. permanent types, mapped from broker-specific codes to a common internal set.
- [ ] Retry Policy**: Idempotent operations shall use a retry policy with exponential backoff and randomized jitter.
- [ ] Circuit Breaker**: Connections to broker adapters must be protected by circuit breakers to prevent cascading failures.

#### `app/services/trader/README.md`

Functions/classes:
- No runtime functions/classes; documentation artifact only.

Requirements:
- [ ] Simulator Integration**: Maintain high-fidelity integration tests using the local simulator adapter for deterministic regression validation.

### Unit Tests Required

```text
tests/unit/app/services/trader/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/07_trading.py
```

Usage examples must show:
- `example_01_order_intent_creation`: Demonstrate deterministic order-intent creation from approved risk decisions.
- `example_02_order_validation`: Demonstrate symbol, price, volume, stop, freeze-level, and MQL5 compatibility validation.
- `example_03_idempotency_and_store`: Demonstrate idempotency keys, request packaging, duplicate handling, and store persistence.
- `example_04_simulator_route`: Demonstrate paper/simulation route behavior without live broker mutation.
- `example_05_reconciliation`: Demonstrate order, position, and receipt reconciliation plus mismatch reporting.
- `example_06_rate_limits_and_shutdown`: Demonstrate throttling, ordered queues, graceful shutdown, and recoverable errors.
- `example_07_execution_quality_reporting`: Demonstrate fill quality, slippage, partial-fill metadata, and structured receipts.
- `example_08_live_boundary`: Demonstrate that live mutation is blocked unless Live phase gates approve it.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 84 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(trading-service): implement phase 7 trading service requirements
```

## Phase 8 Simulation Engine

### Goal

Implement the Simulation Engine requirements under `app/services/simulation/` while preserving the phase module boundaries and governance rules.

Task inventory: 1,662 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/simulation/`.
- Requires Phase 7 Trading Service contracts to be available where referenced by `08-simulation.md`.

### Files to Create

```text
app/__init__.py
app/services/simulation/__init__.py
app/services/simulation/orchestrator.py
app/services/simulation/engine.py
app/services/simulation/trader.py
app/services/simulation/models/__init__.py
app/services/simulation/models/tick.py
app/services/simulation/models/spread.py
app/services/simulation/models/slippage.py
app/services/simulation/models/liquidity.py
app/services/simulation/models/fee.py
app/services/simulation/models/swap.py
app/services/simulation/models/margin.py
app/services/simulation/validation/__init__.py
app/services/simulation/validation/quality.py
app/services/simulation/validation/schema.py
app/services/simulation/journal.py
app/services/simulation/report.py
app/services/simulation/
docs/source-requirements/03-indicator.md
docs/source-requirements/04-strategy.md
app/services/data/
app/services/strategies/
app/services/indicators/
data/broker
docs/source-requirements/
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/simulation/README.md`

Functions/classes:
- No runtime functions/classes; documentation artifact only.

Requirements:
- [ ] Usage examples shall run as executable documentation tests and assert exact success or failure envelope shape.
- [ ] Documentation shall include a formal user guide for interpreting realism labels.
- [ ] Documentation shall include a configuration reference for every config class and enum.
- [ ] Documentation shall include a migration guide if earlier simulator versions exist.
- [ ] Documentation shall describe memory-safety constraints for optimization, walk-forward, and Monte Carlo runs.
- [ ] Documentation shall describe FX cross-rate synthesis rejection behavior and `max_cross_rate_skew_bps`.
- [ ] Documentation shall describe added error and diagnostic codes.
- [ ] Documentation shall include research-integrity, optimization, and overfitting-control operating procedures.
- [ ] Documentation shall include immutable run-configuration, environment drift detection, and benchmark-profile certification procedures.
- [ ] Documentation shall include warm data cache behavior, TTL rules, `DataManifestHash` keys, and checksum validation requirements.
- [ ] Documentation shall include feature-store point-in-time retrieval, alternative-data as-of alignment, publication lag, ingestion lag, and no-lookahead rules.
- [ ] Documentation shall include FX `production_realistic` V1 non-goals and scope limitations.
- [ ] Documentation shall include third-party data and vendor-governance procedures.

#### `app/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] The module may simulate configured simulation risk-rule effects for replay and evidence, but external policy definition, live approval authority, and human governance decisions live outside Simulation.
- [ ] Initial MT5 parity tests shall use a versioned broker profile named `mt5_demo_reference_fx_v1`.
- [ ] Poison-pill detection shall quarantine the work unit, stop infinite requeue loops, emit an alert, and preserve failure artifacts for diagnosis.
- [ ] Anything exported from a domain `__init__.py` and listed in `__all__` shall be treated as an official AI Tool.
- [ ] Documentation shall include execution latency modelling, latency component definitions, and latency diagnostic interpretation.
- [ ] Optional enterprise features may be disabled initially, but their contracts should be defined to avoid breaking redesign.
- [ ] No file-specific non-functional requirements defined.
- [ ] Import-time tests shall verify public module import performs no filesystem writes, network access, worker startup, secret reads, market-data access, broker access, or long-running initialization.
#### `app/services/simulation/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/simulation/orchestrator.py`

Functions/classes:
- `BacktestOrchestrator`
- `run_backtest`
- `EventDrivenExecutionEngine`

Requirements:
- [ ] Simulation orchestration through `BacktestOrchestrator`.
- [ ] The system shall provide a `BacktestOrchestrator` that validates configuration and data dependencies before executing a simulation.
- [ ] Phase 1 shall implement `run_backtest`, `BacktestOrchestrator`, `EventDrivenExecutionEngine`, FX symbol metadata, tick generation, spread/slippage/commission/swap models, broker-profile fixtures, data-quality gates, deterministic journal storage, JSON and Markdown reports, schema validation, and replay tests.
- [ ] The `BacktestOrchestrator` shall coordinate validation, data quality, signal construction, tick construction, execution, metrics, and reporting.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Expose the official AI tool boundary for `run_backtest`.
- [ ] MT5 parity comparisons shall require exact match for order count, deal count, position lifecycle count, side, symbol, order type, fill policy, and deterministic event order.
- [ ] Production service mode shall queue `run_backtest` requests when workers are saturated and return a run id with `queued` status.
- [ ] Queueing shall enforce maximum queue length, maximum queue age, cancellation support, and deterministic rejection when limits are exceeded.
- [ ] The scheduler shall persist queued, running, completed, failed, and cancelled states outside worker memory.
- [ ] Any network, multi-user, agent-orchestrated, or externally accessible `run_backtest` surface shall require authenticated actor identity.
- [ ] The `run_backtest` AI Tool shall reject raw arbitrary Python strategy code strings before execution.
- [ ] The orchestration layer shall explicitly vet and sandbox any code-based strategy path before it can be executed.
- [ ] The system shall return `SIM_ARBITRARY_CODE_REJECTED` when raw arbitrary strategy code is passed to `run_backtest`.
- [ ] `SIM_IOC_REMAINDER_CANCELLED` shall be classified as a non-fatal diagnostic code.
- [ ] The system shall return `SIM_CHECKPOINT_INCOMPATIBLE` when a resumed run fails checkpoint compatibility validation.
- [ ] `SIM_IOC_REMAINDER_CANCELLED`
- [ ] The module does not own strategy logic, strategy lifecycle approval, or strategy-generated signal logic; those belong to `app/services/strategies/`.
- [ ] The module does not execute arbitrary user-provided Python strategy code through `run_backtest`.
- [ ] `run_backtest` shall define required fields, optional fields, defaults, enum values, unknown-field behavior, malformed-payload behavior, size limits, path resolution rules, validation order, authorization behavior, and artifact-root behavior before implementation.
- [ ] `run_backtest` shall define response envelopes for `success`, `failed`, `queued`, `cancelled`, and `diagnostic_failed` statuses before implementation.
- [ ] Optimization, walk-forward, Monte Carlo, visual replay export, production-promotion manifests, and service-mode lifecycle operations shall be implemented only when their requirements are explicitly tagged for the active release phase.
- [ ] `actor_context` shall define authenticated actor identity and roles for any networked, multi-user, or agent-orchestrated invocation.
- [ ] `status` values shall include `success`, `failed`, `queued`, `cancelled`, and `diagnostic_failed` before implementation.
- [ ] The system shall fill available volume and cancel the remainder for `IOC` orders.
- [ ] When an `IOC` order is partially filled, the unfilled remainder shall be cancelled.
- [ ] `SIM_IOC_REMAINDER_CANCELLED` shall not be treated as a fatal simulation error when the partial fill itself is valid.
- [ ] The `run_backtest` AI Tool shall enforce the strategy registry and sandbox rules defined in `docs/source-requirements/04-strategy.md`.
- [ ] Long-running optimization, walk-forward, and Monte Carlo jobs shall periodically checkpoint progress to disk in a restartable format.
- [ ] A `ResumePolicy` shall define maximum checkpoint age, checkpoint compatibility rules, automatic resume eligibility, and restart-from-scratch behavior.
- [ ] Pending orders, SL, TP, and limit prices shall be adjusted or cancelled according to broker/config policy.
- [ ] The `run_backtest` AI Tool shall not accept raw arbitrary Python strategy code as a string input.
- [ ] The `run_backtest` AI Tool shall reject raw strategy-code injection attempts before execution.
- [ ] The `run_backtest` AI Tool shall return `SIM_ARBITRARY_CODE_REJECTED` when raw arbitrary strategy code is rejected.
- [ ] Raw Python strategy code is supplied to `run_backtest`.
- [ ] IOC order partially fills and cancels remainder.
- [ ] `run_backtest` contract tests for success, failed, cancelled, queued where supported, and diagnostic-failed envelopes.
- [ ] Contract tests shall verify failed, queued, cancelled, and diagnostic-failed responses preserve the same envelope shape and include deterministic `SIM_*` error codes where applicable.
- [ ] Security tests shall verify unauthenticated network or agent-orchestrated access is rejected, each RBAC role is enforced, secrets in payloads are rejected and redacted, and rejected raw strategy code is not executed or logged in full.
- [ ] Market-halt tests shall cover market-wide halts, symbol halts, limit-up/limit-down states, halted order rejection or deferral, and resumed trading.
- [ ] Advanced-order tests shall cover trailing stops, pegged orders, cancel-replace behavior, queue-priority effects, and deterministic repricing.
- [ ] Checkpoint and resume tests shall cover checkpoint age limits, checkpoint compatibility, OOM-style restart, worker loss, requeue behavior, and duplicate artifact prevention.
- [ ] Service-operations tests shall cover resource quotas, queue backpressure, queued run status, queue limit rejection, cancellation, environment drift warnings, synthetic transaction probes, and canary divergence handling.
- [ ] AI Tool strategy security tests shall verify `run_backtest` rejects raw arbitrary Python strategy code, returns `SIM_ARBITRARY_CODE_REJECTED`, does not execute rejected code, and does not log rejected code in full.
- [ ] Model-governance, research-integrity, run-lifecycle, vendor-governance, and promotion-manifest tests shall pass before production promotion workflows are enabled.
- [ ] Service-mode CI shall include resource-quota, queue, tracing, business-metric, synthetic-probe, canary, data-lineage, checkpoint-resume, and distributed-worker tests before production service deployment.
- [ ] `queued` envelope example showing run id, queue position or bounded queue metadata where available, retry/cancellation metadata, warnings, and no completed result.
- [ ] `run_backtest` shall not execute arbitrary user-provided Python code strings.
- [ ] `ResumePolicy` for checkpoint age, checkpoint compatibility, automatic resume eligibility, and restart behavior.
- [ ] Scheduler configuration for queue backend, queue limits, worker heartbeat timeout, retry policy, cancellation behavior, and preemptible-worker handling.
- [ ] Code-based strategy execution metadata only when referenced by an approved registry entry with sandbox profile id, vetting artifact hash, approval metadata, and explicit orchestration-layer permission.
- [ ] Registered strategy identifier or validated strategy configuration for `run_backtest`.
- [ ] Sandbox and vetting metadata only when code-based strategy execution is explicitly permitted by the orchestration layer.
- [ ] Position lifecycle history.
- [ ] IOC remainder cancellation diagnostics.
- [ ] User, agent, CLI, or notebook shall be able to invoke the `run_backtest` tool wrapper.
- [ ] The `run_backtest` tool wrapper shall be the official user-facing tool boundary.
- [ ] Documentation shall state that raw arbitrary Python strategy code is not accepted by `run_backtest`.
- [ ] Documentation shall describe IOC remainder cancellation diagnostics.
- [ ] Documentation shall include run lifecycle, idempotency, cancellation, checkpoint, and resume behavior.
- [ ] Documentation shall include resource quota, scheduler queue, worker heartbeat, checkpoint/resume, preemptible-worker, and backpressure operating procedures.
- [ ] Documentation shall include market-halt, limit-up/limit-down, portfolio kill-switch, trailing-stop, pegged-order, and cancel-replace semantics.
#### `app/services/simulation/engine.py`

Functions/classes:
- `EventDrivenExecutionEngine`
- `SimulationResult`
- `run_id`
- `broker_profile_id`

Requirements:
- [ ] Canonical tick-based execution through `EventDrivenExecutionEngine`.
- [ ] `metadata` shall include module, operation, tool risk level, side-effect classification, actor/audit references where authorized, engine version, config hash, data manifest hash, execution timing, and created timestamp.
- [ ] The system shall execute official backtests through the tick-based `EventDrivenExecutionEngine`.
- [ ] At the first tick of bar `N`, the engine shall mask, drop, or reject any raw OHLCV data point with timestamp greater than or equal to bar `N` open time.
- [ ] At the first tick of bar `N`, the engine shall mask, drop, or reject any indicator-derived data point with timestamp greater than or equal to bar `N` open time.
- [ ] At the first tick of bar `N`, the engine shall mask, drop, or reject any multi-timeframe aligned data point with timestamp greater than or equal to bar `N` open time.
- [ ] At the first tick of bar `N`, the engine shall mask, drop, or reject strategy metadata used for sizing or trade decisions when that metadata depends on data with timestamp greater than or equal to bar `N` open time.
- [ ] The engine shall raise `SIM_LOOKAHEAD_DETECTED` when a strategy attempts to access prohibited current-bar or future data during first-tick processing for bar `N`.
- [ ] The system shall support configurable execution latency models covering strategy computation delay, broker or network routing delay, venue or exchange gateway delay, and matching-engine delay.
- [ ] The default `ambiguous_sl_tp_policy` shall be `conservative_worst_outcome`, meaning the engine selects the lower resulting account equity after applying valid SL-first and TP-first interpretations under the same first-available-tick and cost model.
- [ ] The system shall centralize final position sizing in the engine.
- [ ] The engine shall maintain an authoritative positions container for open positions.
- [ ] The engine shall maintain an authoritative orders container for active pending orders.
- [ ] The engine shall maintain an authoritative deals container for executed deal records.
- [ ] State containers shall be mutated only by the execution engine and shall be exposed to strategies through read-only snapshots.
- [ ] The matching engine shall determine fillable volume from liquidity constraints before applying slippage to filled volume.
- [ ] Every journal shall include a `journal_manifest.json` containing configuration hash, data manifest hash, engine version, schema version, artifact checksums, and retention tier.
- [ ] Optimization shall use the same canonical tick execution engine as normal backtests.
- [ ] Large optimization jobs shall be split into deterministic work units keyed by strategy id, parameter hash, config hash, data hash, engine version, and schema version.
- [ ] Parallel optimization workers shall run isolated engine instances and shall not share mutable account, order, journal, or strategy state.
- [ ] The roll engine shall decide whether to close/reopen, adjust the price series, or simulate calendar-spread execution.
- [ ] The accounting engine shall track native-currency and base-currency realized PnL.
- [ ] The accounting engine shall track native-currency and base-currency unrealized PnL.
- [ ] The accounting engine shall track native-currency and base-currency commissions and fees.
- [ ] The accounting engine shall track native-currency and base-currency swap.
- [ ] The accounting engine shall track native-currency and base-currency borrow fees.
- [ ] The accounting engine shall track native-currency and base-currency dividend cashflows.
- [ ] The accounting engine shall track native-currency and base-currency futures roll PnL.
- [ ] The accounting engine shall track native-currency and base-currency perpetual funding.
- [ ] The accounting engine shall track native-currency and base-currency margin.
- [ ] The accounting engine shall track native-currency and base-currency cash balances.
- [ ] The accounting engine shall track portfolio NAV in base currency.
- [ ] The first regulatory engine scope shall be US equities and ETFs.
- [ ] The regulatory engine may support optional wash-sale detection and tax-awareness diagnostics for taxable account scenarios.
- [ ] FX production-realistic promotion shall not require the regulatory engine, but reports shall disclose that regulatory checks were disabled or not applicable.
- [ ] Internal engine services shall not be exported as agent-callable tools unless a deliberate wrapper is created.
- [ ] `SimulationResult` shall include `schema_version`, `run_id`, `classification`, `started_at`, `completed_at`, `engine_version`, `config_hash`, `data_manifest_hash`, `broker_profile_id`, `artifact_manifest`, `summary_metrics`, `risk_metrics`, `cost_summary`, `realism_disclosure`, and `data_quality_summary`.
- [ ] Resumed runs shall verify config hash, data manifest hash, engine version, journal sequence continuity, random-seed state, and checkpoint compatibility before continuing.
- [ ] The numeric performance values in this section are provisional engineering targets until a Phase 1 benchmark profile and pass/fail gates are approved.
- [ ] Internal engine services shall remain separate from official AI Tool wrappers.
- [ ] Optional enterprise features shall have extension points without forcing a breaking redesign of the core engine.
- [ ] The immutable run-configuration artifact shall include data authority manifest versions, broker profile versions, strategy version, engine version, dependency lock hash, resource policy, and effective runtime flags.
- [ ] Trace and log context shall propagate run id, request id, strategy id, config hash, data manifest hash, and engine version.
- [ ] Major engine releases shall support canary analysis by running a controlled subset of production requests through old and new engine versions and comparing results for configured statistical equivalence.
- [ ] Internal engine services shall not be agent-callable unless wrapped deliberately.
- [ ] Phase 1 shall exclude equity/ETF corporate actions, borrow-fee production realism, forced buy-ins, delisting, US regulatory engines, futures rollover production realism, perpetual funding production realism, feature-store integration, alternative-data integration, distributed workers, poison-pill work-unit quarantine, canary analysis, synthetic transaction monitoring, external report distribution, and production promotion workflows unless separately approved.
- [ ] `Future Extensions Annex`: future asset classes, enterprise service mode, distributed workers, regulatory engines, feature-store/alternative-data integrations, canary/synthetic monitoring, external report distribution, and production-promotion automation.
- [ ] The engine is the single source of truth for orders, deals, positions, pending orders, account state, balance, equity, margin, free margin, margin level, realized PnL, floating PnL, commission, swap, trade history, audit journal, and execution timestamps.
- [ ] Optimization must use the canonical tick-execution engine.
- [ ] Tick batching shall be allowed only where the engine can prove no state transition or compliance event can occur before the next boundary.
- [ ] The `EventDrivenExecutionEngine` shall own canonical execution.
- [ ] Internal engines shall provide data quality, tick generation, spread, market calendar, gaps, event priority, liquidity, slippage, matching, fees, swap, broker rules, portfolio, accounting, compliance, metrics, optimization, Monte Carlo, and performance services.
- [ ] Deferred enterprise and future-scope areas include non-FX production-realistic asset-class expansion, regulatory engines, feature-store integration, alternative-data integration, distributed workers, canary analysis, synthetic transaction monitoring, external-report distribution workflows, and production-promotion automation unless explicitly approved for the active release phase.
- [ ] No file-specific non-functional requirements defined.
- [ ] Optimization uses the same canonical tick execution engine as normal backtests.
- [ ] The attached Hardened Draft v1.6 specification is the active source of truth.
- [ ] The simulator is intended for Python implementation.
- [ ] The simulation module is intended to live under `app/services/simulation/`.
- [ ] Indicator implementation requirements live in `docs/source-requirements/03-indicator.md`.
- [ ] The simulator targets deterministic backtesting and simulation, not live order execution against a broker.
- [ ] Vectorized processing is acceptable only for indicators and signal generation.
- [ ] Future improvements shall contain only deferred optional enhancements and shall not contain mandatory business rules, required inputs, required outputs, or production gates.
- [ ] Each future improvement shall include rationale, non-goal status for the current phase, promotion trigger, affected requirement sections, and required owner decision before promotion.
- [ ] The Deferred Scope Register in the Phase 1 Builder Slice section shall be the single source of truth for Simulation deferred-scope status during Phase 1 handoff preparation.
- [ ] Validate simulation configuration, strategy references, data dependencies, broker profiles, market-data authority manifests, realism requirements, and run permissions before execution.
- [ ] The same configuration, data, and seed shall produce the same trade intents.
- [ ] The same configuration, data, and seed shall produce the same event-priority order.
- [ ] The same configuration, data, and seed shall produce the same orders, deals, and positions.
- [ ] The same configuration, data, and seed shall produce the same portfolio state.
- [ ] Event ordering shall be replayable.
- [ ] Parent-child order lineage shall be auditable when order chaining is enabled.
- [ ] The system shall not silently fail.
- [ ] The system shall return deterministic error codes for rejections, skipped trades, invalid config, invalid data, validation failures, sizing failures, and execution failures.
- [ ] The system shall log all failures.
- [ ] Indicator and signal calculation for 10 years by 10 symbols of M1 bars should target less than 5 seconds after caching or preprocessing.
- [ ] Optimization batch of 10,000 parameter sets should target less than 30 minutes after parallel execution is enabled.
- [ ] Common 10-symbol research runs should target less than 2 GB memory after chunking and caching.
- [ ] Production benchmark gates shall define benchmark dataset, hardware profile, dependency lock hash, measurement command, warmup behavior, sample count, pass/fail threshold, allowed variance, median runtime, and p95 runtime before the targets above are used as acceptance gates.
- [ ] Phase 1 Builder handoff shall either replace provisional `should target` values with approved `MUST meet` thresholds or explicitly mark them non-blocking until production promotion.
- [ ] Phase 1 memory limits shall remain pending owner approval until the benchmark profile defines maximum resident memory, measurement command, reference hardware, dataset shape, and failure behavior.
- [ ] Once approved, memory-limit breaches shall fail deterministically with `SIM_RESOURCE_QUOTA_EXCEEDED` before the run can claim production-realistic classification.
- [ ] The system shall follow a domain-driven architecture.
- [ ] Simulation, indicators, and strategies shall remain in their target domains.
- [ ] This domain document may be split into smaller requirement files after Phase 1 boundaries are implemented, provided traceability to this baseline is preserved.
- [ ] Any split requirements file shall preserve requirement ids, release phase, acceptance criteria, and verification mapping.
- [ ] The simulator shall reproduce important MT5 Strategy Tester execution semantics.
- [ ] Data checks shall be deterministic.
- [ ] Data checks shall include survivorship-bias flags where relevant.
- [ ] Floating-point types may be used for vectorized indicator research only when the result is not used directly for official accounting or official fill prices.
- [ ] Fractional shares and fractional contract quantities shall be allowed only when symbol metadata declares a valid fractional volume step.
- [ ] Position sizing shall default to floor-to-step volume rounding, while final fill prices and account cashflows shall follow the execution and accounting rounding rules above.
- [ ] The simulator shall emit run-level telemetry for every official run.
- [ ] Resource quotas shall include maximum concurrent runs, maximum wall-clock seconds per run, maximum temporary storage bytes, maximum queued runs, and maximum worker count where applicable.
- [ ] Quota violations shall fail fast with `SIM_RESOURCE_QUOTA_EXCEEDED`.
- [ ] Before a production run starts, the system shall compute and record an environment diagnostic hash covering dependency versions, selected system libraries, relevant environment variables, container image digest where applicable, and benchmark profile id.
- [ ] The system shall raise `SIM_ENVIRONMENT_DRIFT_WARNING` when the environment diagnostic hash differs from the certified benchmark profile environment.
- [ ] Alerting shall include trend or predictive rules for persistence failures, data-provider failures, queue saturation, and SLO burn rate where the monitoring platform supports them.
- [ ] Production service mode shall support synthetic transaction monitoring through a scheduled canonical simulation probe.
- [ ] Optional service failures such as warm-cache outage or SQLite sidecar index outage may degrade to slower fallback behavior for non-production runs when configured.
- [ ] SQLite sidecar fallback shall use a full canonical JSONL scan and shall disclose the slower degraded mode in diagnostics.
- [ ] Official AI Tool exports shall require metadata.
- [ ] Official AI Tool exports shall use structured logging.
- [ ] Official AI Tool exports shall return deterministic error codes.
- [ ] Official AI Tool exports shall avoid silent failures.
- [ ] Official AI Tool exports shall provide safe errors.
- [ ] Parent-child order lineage shall be preserved where enabled for auditability.
- [ ] Local trusted CLI or notebook usage may run without interactive authentication only when the process uses local filesystem permissions and does not expose a network listener.
- [ ] External tool access shall enforce role-based authorization with at least `simulation.viewer`, `simulation.runner`, and `simulation.admin` roles.
- [ ] `simulation.admin` may manage approved broker profiles, data-authority manifests, retention policies, and benchmark baselines.
- [ ] The tool wrapper shall prevent arbitrary code execution through strategy input.
- [ ] Code-based strategy execution approval shall require `simulation.admin` approval, strategy owner approval, sandbox profile id, vetting artifact hash, and recorded approval expiry.
- [ ] Rejected code-injection attempts shall be logged with safe redaction.
- [ ] Security-relevant rejections shall include deterministic error codes.
- [ ] Research runs shall default to a 180-day retention tier.
- [ ] Diagnostic failure logs shall default to a 90-day retention tier unless linked to a production-candidate incident.
- [ ] Benchmark metadata attached to a release shall be retained for at least three years or the lifetime of the release line, whichever is longer.
- [ ] Encryption-at-rest requirements shall define owning module, approved key source, key rotation expectations, failure behavior when encryption is unavailable, metadata redaction, and compatibility with checksum/signature verification.
- [ ] Production releases shall require pinned dependency lockfiles.
- [ ] Production releases shall generate an SBOM.
- [ ] Production releases shall pass dependency vulnerability scanning.
- [ ] Production releases shall pass secret scanning.
- [ ] Production releases shall pass static security analysis for public modules and official AI Tool wrappers.
- [ ] Third-party market-data adapters, broker-profile loaders, and optimization plugins shall be treated as supply-chain dependencies with approval status and version hashes.
- [ ] Every rejection shall return a deterministic error code.
- [ ] Every skipped trade shall return a deterministic error code.
- [ ] Every validation failure shall return a deterministic error code.
- [ ] Every sizing failure shall return a deterministic error code.
- [ ] Every execution failure shall return a deterministic error code.
- [ ] Every failure shall be logged.
- [ ] Unsupported fill policies shall be rejected before matching.
- [ ] Safe errors shall be provided by the exported tool wrapper.
- [ ] The system shall support the documented `SIM_*` error-code taxonomy.
- [ ] The system shall stop production runs on `SIM_PERSISTENCE_FAILED`.
- [ ] The system shall return `SIM_CALIBRATION_REQUIRED` when calibrated execution evidence is required but missing, expired, or invalid.
- [ ] The system shall return `SIM_VENDOR_DATA_POLICY_VIOLATION` when data license, retention, revision, or point-in-time requirements are violated.
- [ ] The system shall return `SIM_QUEUE_LIMIT_EXCEEDED` when scheduler queue limits are exceeded.
- [ ] The system shall return `SIM_WORKER_LOST_REQUEUED` as a non-fatal diagnostic when a lost worker causes a work unit to be requeued.
- [ ] The system shall return `SIM_CANARY_DIVERGENCE` when canary comparison exceeds configured divergence tolerance.
- [ ] The system shall return `SIM_FEATURE_LOOKAHEAD_DETECTED` when feature-store or alternative-data availability violates point-in-time rules.
- [ ] `SIM_DATA_EMPTY`
- [ ] `SIM_DATA_DUPLICATE_TIMESTAMP`
- [ ] `SIM_DATA_NON_MONOTONIC_TIME`
- [ ] `SIM_DATA_PRICE_OUTLIER`
- [ ] `SIM_LOOKAHEAD_DETECTED`
- [ ] `SIM_VOLUME_BELOW_MIN`
- [ ] `SIM_VOLUME_ABOVE_MAX`
- [ ] `SIM_VOLUME_STEP_MISMATCH`
- [ ] `SIM_FREEZE_LEVEL_VIOLATION`
- [ ] `SIM_CORRELATION_LIMIT_EXCEEDED`
- [ ] `SIM_CONCENTRATION_LIMIT_EXCEEDED`
- [ ] `SIM_MARKET_CLOSED`
- [ ] `SIM_GAP_HANDLING_REJECTED`
- [ ] `SIM_PARTIAL_FILL_REMAINDER`
- [ ] `SIM_UNSUPPORTED_FILL_POLICY`
- [ ] `SIM_LIMIT_QUEUE_NOT_FILLED`
- [ ] `SIM_PENDING_ORDER_EXPIRED`
- [ ] `SIM_ORDER_NOT_FOUND`
- [ ] `SIM_SIZING_FAILED`
- [ ] `SIM_SIZING_REQUIRES_STOP_LOSS`
- [ ] `SIM_PERSISTENCE_FAILED`
- [ ] `SIM_ARBITRARY_CODE_REJECTED`
- [ ] `SIM_COMMISSION_CALCULATION_FAILED`
- [ ] `SIM_FX_CROSS_RATE_REJECTED`
- [ ] `SIM_DATA_PARTIAL`
- [ ] `SIM_RESOURCE_QUOTA_EXCEEDED`
- [ ] `SIM_QUEUE_LIMIT_EXCEEDED`
- [ ] `SIM_ENVIRONMENT_DRIFT_WARNING`
- [ ] `SIM_WORKER_LOST_REQUEUED`
- [ ] `SIM_CANARY_DIVERGENCE`
- [ ] `SIM_FEATURE_LOOKAHEAD_DETECTED`
- [ ] `SIM_MARKET_HALT_ACTIVE`
- [ ] `SIM_KILL_SWITCH_TRIGGERED`
- [ ] `SIM_POISON_WORK_UNIT_QUARANTINED`
- [ ] `SIM_OPTIONAL_SERVICE_DEGRADED`
- [ ] `SIM_RUN_ID_CONFLICT`
- [ ] `SIM_CHECKPOINT_INCOMPATIBLE`
- [ ] `SIM_CALIBRATION_REQUIRED`
- [ ] `SIM_VENDOR_DATA_POLICY_VIOLATION`
- [ ] `SIM_PERFORMANCE_GATE_FAILED`
- [ ] `SIM_MONTE_CARLO_FAILED`
- [ ] `SIM_OPTIMIZATION_FAILED`
- [ ] `SIM_INTERNAL_ERROR`
- [ ] The module does not own raw market-data acquisition, source readiness, external source adapters, or normalized data contracts; those belong to `app/services/data/`.
- [ ] The module does not own final live broker execution against real accounts.
- [ ] The module does not own live adapter implementation, live broker session management, live broker credentials, or imports of live execution modules; those must remain in Live/Trading/execution adapter ownership.
- [ ] `error` shall include deterministic `SIM_*` code, safe message, field path where applicable, severity, retryability, and redacted details.
- [ ] The system shall build indicator and signal data before constructing the executable signal timeline.
- [ ] The system shall align bar-based signals using the configured signal timing policy.
- [ ] The system shall use `BAR_OPEN_PREVIOUS_CLOSE` as the default signal timing policy.
- [ ] The system shall reject or flag lookahead usage in bar-open strategies.
- [ ] The system shall require vectorized signal generation to shift current-bar conditions so that bar-open entries are based on previous closed-bar values.
- [ ] The system shall allow simplified realism modes only when explicitly configured.
- [ ] Latency diagnostics shall record signal timestamp, request timestamp, eligible execution timestamp, latency components, and latency model id.
- [ ] The system shall support `FOK`.
- [ ] The system shall support `IOC`.
- [ ] The system shall support `RETURN`.
- [ ] The system shall support explicit partial-fill behavior.
- [ ] The system shall reject `FOK` orders when full requested volume is unavailable.
- [ ] The system shall keep unfilled `RETURN` remainders pending only when the broker or symbol supports it.
- [ ] The system shall create a separate deal record for every partial fill.
- [ ] The system shall recalculate position average price from actual filled volumes and prices.
- [ ] The system shall support configurable limit-order queue behavior.
- [ ] The system shall reduce available fill volume by estimated or configured queue-ahead volume.
- [ ] The system shall resolve FIFO and pro-rata behavior deterministically.
- [ ] The system may document hidden-order and iceberg support while keeping them disabled until order-book data is available.
- [ ] Before Phase 1 Builder handoff, limit-order queue configuration shall explicitly define valid values for `queue_model`, `touch_fill_enabled`, `queue_ahead_volume`, `queue_ahead_estimation_method`, `fill_allocation_method`, `minimum_fill_volume`, and `partial_fill_policy`.
- [ ] Phase 1 queue behavior shall be limited to deterministic `touch_fill_enabled=false` rejection or deterministic configured queue-ahead reduction unless the owner approves richer order-book queue realism.
- [ ] Hidden-order and iceberg reservation behavior shall be `[PHASE2]` and must return deterministic unsupported-scope diagnostics if requested during Phase 1.
- [ ] The system shall support market-hours configuration including session start, session end, timezone, weekend closure, holiday calendar, and 24/7 asset flag.
- [ ] The system shall detect market open and closed state.
- [ ] The system shall detect session breaks, weekends, holidays, and rollover boundaries.
- [ ] The system shall detect market-wide halts, exchange halts, symbol halts, and limit-up/limit-down states when halt data is available.
- [ ] The system shall prevent market orders outside allowed sessions unless explicitly configured for 24/7 assets.
- [ ] The system shall support gap handling by rejection.
- [ ] The system shall support gap handling by fill at open.
- [ ] The system shall use the conservative worse outcome by default when both SL and TP are crossed in the same ambiguous gap.
- [ ] The system shall enforce stop-out percentage.
- [ ] The system shall enforce maximum pending orders.
- [ ] The system shall reject unsupported fill policies with deterministic error codes.
- [ ] The system shall support fixed-lot sizing.
- [ ] The system shall support milestone sizing.
- [ ] The system shall support Kelly-criterion sizing.
- [ ] The system shall support volatility-based sizing.
- [ ] The system shall support fixed-fractional sizing.
- [ ] The system shall reject zero or negative stop distance.
- [ ] The system shall normalize volume using symbol minimum, maximum, and step constraints.
- [ ] The system shall support explicit volume rounding policies.
- [ ] The system shall default to floor-to-step rounding.
- [ ] The system shall record raw and normalized volume and shall not silently adjust volume.
- [ ] Pending-order records shall include all applicable position record fields plus order price, stop-limit price, expiry date, and expiration mode.
- [ ] Deal records shall include all applicable position record fields plus deal reason, deal direction, order id, position id, fill price, filled volume, and execution timestamp.
- [ ] The system shall validate broker maximum orders and positions.
- [ ] The system shall validate fill-policy compatibility.
- [ ] The system shall execute market orders.
- [ ] The system shall trigger pending orders.
- [ ] The system shall support buy limit pending orders.
- [ ] The system shall support buy stop pending orders.
- [ ] The system shall support sell limit pending orders.
- [ ] The system shall support sell stop pending orders.
- [ ] The system shall support buy stop-limit pending orders.
- [ ] The system shall support sell stop-limit pending orders.
- [ ] The system shall support trailing stops when configured.
- [ ] The system shall support pegged orders when configured, including orders pegged to best bid, best ask, mid price, or another approved reference.
- [ ] The system shall activate stop-limit orders.
- [ ] The system shall trigger SL/TP.
- [ ] The system shall handle gap execution.
- [ ] The system shall enforce fill policies.
- [ ] The system shall simulate partial fills.
- [ ] The system shall produce orders, deals, position events, and execution diagnostics.
- [ ] Compliance records shall include timestamp.
- [ ] Compliance records shall include decision rationale.
- [ ] Compliance records shall include pre-trade checks.
- [ ] Compliance records shall include optional compliance tag.
- [ ] Advanced stateful strategies and agent-generated strategies shall provide decision rationale.
- [ ] The simulation module shall provide approved read-only execution state to advanced strategies when required.
- [ ] The simulation module shall consume indicator outputs through the indicator module contract defined in `docs/source-requirements/03-indicator.md`.
- [ ] The simulation module shall reject, mask, or downgrade runs when indicator-derived data violates the configured no-lookahead policy.
- [ ] The simulation module shall convert indicator-derived signals into timestamped trade intents before official execution.
- [ ] The system shall support grid-search optimization.
- [ ] The system shall support random-search optimization.
- [ ] The system shall support Bayesian optimization.
- [ ] The system shall support genetic optimization.
- [ ] Optimization shall reject parameter sets that fail minimum trade count.
- [ ] Optimization shall reject parameter sets that fail robustness checks.
- [ ] Optimization outputs shall include config hash, data hash, parameter hash, random seed, and objective function.
- [ ] Failed or diagnostic work units shall not poison the optimization cache.
- [ ] Optimization jobs shall support resumable execution from persisted work-unit manifests.
- [ ] Optimization and walk-forward jobs shall decompose into independent deterministic work units executable on ephemeral stateless workers.
- [ ] Worker loss, heartbeat expiry, or preemptible-instance termination shall requeue the affected work unit without marking the entire job `SIM_INTERNAL_ERROR`.
- [ ] Distributed schedulers shall detect poison-pill work units that repeatedly fail for the same work-unit hash.
- [ ] Monte Carlo outputs shall include confidence bands for drawdown.
- [ ] Monte Carlo outputs shall include confidence bands for net profit.
- [ ] Monte Carlo outputs shall include confidence bands for profit factor.
- [ ] Monte Carlo outputs shall include worst-case streaks.
- [ ] The system shall benchmark memory usage.
- [ ] The system shall benchmark optimization throughput when optimization is enabled.
- [ ] The production benchmark profile shall be `SIM_BENCHMARK_PROFILE_V1`: Python 3.12, 8 vCPU minimum, 32 GB RAM minimum, NVMe SSD, release build settings, no debugger, and no unrelated heavy background workload.
- [ ] The performance gate shall fail when median runtime regresses by more than 10 percent against the approved baseline and the absolute target is missed.
- [ ] The memory gate shall fail when peak memory regresses by more than 15 percent against the approved baseline and the absolute memory target is missed.
- [ ] If active orders or open positions exist, batching shall proceed only up to the nearest known trigger boundary.
- [ ] The system shall represent asset class in symbol metadata.
- [ ] The system shall support FX.
- [ ] The system shall support CFD.
- [ ] The system shall support ETF.
- [ ] The system shall support future.
- [ ] The system shall support spot crypto.
- [ ] The system shall support index instruments.
- [ ] The system shall derive required realism modules from symbol metadata and simulation config.
- [ ] FX shall be the first asset class eligible for `production_realistic` promotion.
- [ ] The system shall support dividends.
- [ ] The system shall support stock splits.
- [ ] The system shall support reverse splits.
- [ ] The system shall support mergers.
- [ ] The system shall support spinoffs.
- [ ] The system shall support delistings.
- [ ] Dividends shall be applied on ex-date according to selected data policy.
- [ ] Reverse-split fractional handling shall be explicitly configured.
- [ ] Delisting handling shall explicitly realize the configured final economic outcome instead of silently dropping the symbol.
- [ ] Delisting outcomes shall support final exchange price, final OTC or pink-sheet price, cash merger consideration, liquidation value, or conservative total-loss treatment where appropriate.
- [ ] Mergers, delistings, spinoffs, rights issues, symbol changes, and special distributions shall block production-realistic equity or ETF labels when they intersect the requested date range, holdings, or pending orders unless explicitly supported.
- [ ] Research-mode handling of unsupported corporate actions shall disclose the unsupported action and the selected conservative approximation.
- [ ] The system shall support futures contract metadata.
- [ ] The system shall support no futures rollover.
- [ ] The system shall support continuous-adjusted rollover.
- [ ] The system shall support physical close-and-reopen rollover.
- [ ] Futures roll dates shall be deterministic and derived from contract metadata.
- [ ] Continuous-adjusted data may support indicator continuity, but execution shall reference tradeable contract prices.
- [ ] The system shall support disabled funding mode.
- [ ] The system shall support fixed funding rate mode.
- [ ] The system shall support historical funding rate mode.
- [ ] Funding shall apply at exchange-defined funding timestamps.
- [ ] Funding payment direction shall follow the configured exchange sign convention.
- [ ] The system shall support fixed-rate conversion.
- [ ] The system shall support spot-at-bar-close conversion.
- [ ] Currency conversion rates shall come from a deterministic FX rate provider.
- [ ] Direct currency pairs shall be preferred where available.
- [ ] Inverse pairs may be used when enabled.
- [ ] Cross-rate synthesis may be used when enabled and all legs are available.
- [ ] FX conversion configuration shall expose `max_fx_rate_age_seconds` as the canonical maximum-rate-age field.
- [ ] Intraday conversion shall default to a stricter maximum FX rate age than daily-bar conversion.
- [ ] Cross-rate synthesis shall detect triangular arbitrage loops and circular paths in the FX provider graph.
- [ ] Cross-rate synthesis shall reject highly skewed conversion paths when the synthesized rate differs from an available direct or inverse reference by more than the configured `max_cross_rate_skew_bps`.
- [ ] Phase 1 shall default `max_cross_rate_skew_bps` to 25 basis points for validation fixtures and production-candidate runs.
- [ ] The system shall calculate alpha when benchmark data is provided.
- [ ] The system shall calculate beta when benchmark data is provided.
- [ ] The system shall calculate information ratio when benchmark data is provided.
- [ ] The system shall calculate tracking error when benchmark data is provided.
- [ ] The system shall calculate benchmark-relative drawdown when benchmark data is provided.
- [ ] The system shall preserve parent-child order lineage for trade decomposition.
- [ ] The system shall preserve parent-child order lineage for partial fills.
- [ ] The system shall preserve parent-child order lineage for bracket orders.
- [ ] The system shall preserve parent-child order lineage for execution algorithms.
- [ ] The system shall store parent order id, child order ids, fill ids, and linkage metadata when order chaining is enabled.
- [ ] The system shall provide optional deterministic regulatory checks.
- [ ] Regulatory checks may include short-sale locate checks.
- [ ] Official AI Tools shall follow HaruQuant tool standards.
- [ ] Official AI Tools shall include metadata.
- [ ] Official AI Tools shall perform input validation.
- [ ] Official AI Tools shall use structured logging.
- [ ] Official AI Tools shall return deterministic error codes.
- [ ] Official AI Tools shall avoid silent failures.
- [ ] The first implementation slice shall be the Phase 1 FX canonical backtest slice.
- [ ] Unsupported option or option-like instruments shall fail deterministically or run only in explicitly labelled research mode when a future research adapter exists.
- [ ] Validation shall cover conceptual soundness, implementation correctness, input-data suitability, outcome analysis, stress behavior, monitoring approach, and known limitations.
- [ ] A dynamic materiality upgrade shall require the stricter validation evidence and sign-off associated with the upgraded tier before production promotion.
- [ ] The research protocol manifest shall include hypothesis, parameter search space, train/validation/test split, benchmark, objective function, minimum trade count, and promotion criteria.
- [ ] Time-series validation shall support walk-forward, anchored walk-forward, rolling walk-forward, purged cross-validation, embargo windows, and out-of-time validation.
- [ ] Production promotion shall require configured out-of-sample degradation thresholds.
- [ ] Production promotion shall require sensitivity analysis around selected parameters.
- [ ] Post-hoc selected strategies shall not be labelled production-realistic without explicit research-integrity approval.
- [ ] Calibration artifacts shall include symbol, venue or broker profile, date range, account type, order type, order size distribution, data checksum, calibration version, and calibration timestamp.
- [ ] Production-realistic execution models shall define acceptable error bands against observed historical, paper, or live execution data where available.
- [ ] Uncalibrated execution models shall downgrade realism classification or require explicit approval.
- [ ] Capacity diagnostics shall estimate performance degradation across configured capital, order-size, and participation-rate levels.
- [ ] Production promotion shall define maximum approved capital, maximum order size, maximum participation rate, and approved instrument universe.
- [ ] Strategies that exceed approved capacity limits shall be blocked from production promotion or explicitly downgraded.
- [ ] Every external data source shall have a vendor or source inventory record.
- [ ] Vendor records shall include provider, dataset, license scope, redistribution rights, retention rights, adjustment policy, timezone policy, revision policy, and support contact.
- [ ] Production-realistic runs shall require point-in-time data snapshots or an explicit data-revision policy.
- [ ] Data manifests shall record whether data is raw, adjusted, back-adjusted, survivorship-bias-free, point-in-time, revised, or vendor-restated.
- [ ] Every production promotion shall produce a `simulation_promotion_manifest.json`.
- [ ] Promotion shall require explicit classification: `research_only`, `mt5_parity_candidate`, `production_fx_candidate`, or asset-class-specific production candidate.
- [ ] Empty data.
- [ ] Duplicate timestamps.
- [ ] Non-monotonic timestamps.
- [ ] Zero or negative prices.
- [ ] Price outliers.
- [ ] Current-bar lookahead detected.
- [ ] Volume below minimum.
- [ ] Volume above maximum.
- [ ] Volume step mismatch.
- [ ] Stops-level violation.
- [ ] Freeze-level violation.
- [ ] Correlation limit exceeded.
- [ ] Concentration limit exceeded.
- [ ] Market closed.
- [ ] Market order submitted outside session.
- [ ] Weekend or session gap.
- [ ] Gap through stop loss.
- [ ] Gap through take profit.
- [ ] Ambiguous same-gap SL/TP hit.
- [ ] Unsupported fill policy.
- [ ] Partial-fill remainder.
- [ ] Limit order touched but queue not filled.
- [ ] Order not found.
- [ ] Sizing requires stop loss.
- [ ] Commission calculation failure.
- [ ] Monte Carlo failure.
- [ ] Optimization failure.
- [ ] Unsupported merger, spinoff, or delisting behavior.
- [ ] Reverse split fractional quantity handling.
- [ ] Continuous-adjusted indicator values used for non-tradeable execution prices.
- [ ] SQLite sidecar index transaction fails.
- [ ] Sandbox or vetting metadata is missing for code-based strategy execution.
- [ ] FX cross-rate synthesis creates a circular path.
- [ ] Timezone-naive timestamp.
- [ ] Date range crosses a DST or session-boundary ambiguity.
- [ ] Spring-forward local session time gap cannot be mapped to UTC.
- [ ] Fall-back local session duplicate maps to multiple possible UTC instants.
- [ ] Unauthorized actor attempts to launch a run.
- [ ] Data manifest checksum mismatch.
- [ ] Broker profile manifest is unavailable or checksum-mismatched.
- [ ] Market-data authority manifest is unavailable, expired, or checksum-mismatched.
- [ ] Concurrent read of `MarketDataAuthorityManifest` by multiple optimization workers.
- [ ] Registered strategy reference tests proving raw Python strategy-code strings are rejected before import or execution.
- [ ] Data authority tests proving `MarketDataAuthorityManifest` presence, checksum, point-in-time status, and authorization are validated before execution.
- [ ] Timezone/DST tests proving broker-profile timezone rules map local sessions to UTC and reject unresolved spring-forward gaps or fall-back duplicate ambiguity before execution.
- [ ] Concurrent manifest-read tests proving immutable `MarketDataAuthorityManifest` reads are thread-safe for multiple workers and conflicting manifest versions are rejected deterministically.
- [ ] No-live-side-effect tests proving Simulation cannot call live broker mutation paths.
- [ ] Import-time safety tests proving public Simulation imports perform no network, broker, filesystem write, worker, scheduler, or secret-read side effects.
- [ ] Traceability tests shall verify every accepted implementation requirement has `requirement_id`, `phase`, `priority`, `acceptance_criteria`, `verification_method`, and at least one mapped verification gate.
- [ ] Traceability tests shall verify no `future`, `enterprise`, or asset-class-expansion requirement is marked blocking for Phase 1 without owner approval.
- [ ] Boundary tests shall verify Simulation does not call live broker execution paths and does not mutate strategy-owned state except through approved callbacks or returned diagnostics.
- [ ] Market-calendar and gap tests shall cover market-closed rejection, session open, weekend gap, gap-through SL, gap-through TP, and SL/TP ambiguity.
- [ ] Broker-rule tests shall cover supported fill policies, max pending orders, max positions, hedging/netting rules, and stopout thresholds.
- [ ] Latency tests shall cover fixed latency, distribution latency, component latency, delayed eligibility, and latency interaction with missed fills.
- [ ] Matching tests shall cover market order, pending trigger, stop-limit, SL/TP, gap, partial fill, and order-book fill.
- [ ] Strategy tests shall cover EMA trend intents, martingale recovery, decomposition child orders, and partial-fill handling.
- [ ] Execution-calibration tests shall cover missing calibration artifacts, stale calibration artifacts, calibration error-band failures, and uncalibrated realism downgrades.
- [ ] Capacity tests shall cover capital scaling diagnostics, participation-rate limits, approved-capacity violations, and capacity disclosure.
- [ ] Monte Carlo tests shall cover bootstrap reproducibility, confidence interval outputs, and failure handling.
- [ ] Optimization tests shall cover grid/random runs, walk-forward IS/OOS split, overfit rejection, and deterministic parameter ranking.
- [ ] Optimization-cache tests shall cover provenance hash hits, provenance hash misses, failed work-unit exclusion, resumable manifests, and isolated worker state.
- [ ] Performance-gate tests shall cover runtime regression threshold, memory regression threshold, benchmark manifest fields, and benchmark-profile validation.
- [ ] Benchmark tests shall cover benchmark alignment, currency conversion, alpha, beta, information ratio, tracking error, and benchmark-relative drawdown.
- [ ] Order-chaining tests shall cover parent-child lineage, partial-fill child links, decomposition remainder, and bracket/OCO chain integrity.
- [ ] Replay tests shall verify same seed, config, and data produce identical output.
- [ ] Distributed-worker tests shall cover deterministic work-unit decomposition, stateless worker execution, shared artifact-store usage, cache checksum validation, worker heartbeat expiry, and preemptible-worker requeue.
- [ ] Optional-service degradation tests shall cover warm-cache failure, SQLite sidecar outage, JSONL scan fallback, non-production degraded diagnostics, and production fail-closed behavior.
- [ ] Feature-store tests shall cover point-in-time retrieval, availability timestamps, publication lag, microsecond decision timestamps, and feature lookahead rejection.
- [ ] Determinism gate shall pass.
- [ ] Execution realism gate shall pass.
- [ ] MT5 parity gate shall pass within documented tolerance for supported semantics.
- [ ] Performance gate shall pass before production promotion.
- [ ] Research-integrity gate shall pass before production promotion.
- [ ] Execution-calibration gate shall pass before production-realistic promotion when calibrated execution models are required.
- [ ] Supply-chain gate shall pass before production release.
- [ ] CI gate shall pass before production merge.
- [ ] `ruff` shall pass.
- [ ] `black` shall pass.
- [ ] `mypy` shall pass for public modules.
- [ ] `pytest` shall pass.
- [ ] Test coverage shall be at least 80%.
- [ ] Deterministic replay tests shall pass.
- [ ] Broker-profile fixture tests shall pass.
- [ ] Rounding and precision tests shall pass.
- [ ] Security, redaction, and retention tests shall pass.
- [ ] Optimization cache and resumability tests shall pass when optimization is enabled.
- [ ] IOC remainder diagnostic tests shall pass.
- [ ] Failed request that validates `SIM_ARBITRARY_CODE_REJECTED` before strategy import or execution.
- [ ] Signals are converted to timestamped `TradeIntent` objects.
- [ ] Before Builder handoff, every accepted requirement shall include `requirement_id`, `release_phase`, `priority`, `owner`, `status`, `acceptance_criteria`, `dependencies`, and `verification_method`.
- [ ] Requirement IDs shall use stable prefixes such as `SIM-FR`, `SIM-NFR`, `SIM-SEC`, `SIM-EDGE`, `SIM-TEST`, `SIM-BR`, and `SIM-DOC`.
- [ ] The test plan shall include a requirements-to-tests traceability matrix mapping every accepted requirement ID to one or more unit, integration, contract, replay, security, performance, CI, benchmark, or documented manual verification gates.
- [ ] The first Builder-ready implementation scope shall be limited to the FX canonical backtest slice unless another phase slice is explicitly approved in `CHANGELOG.md`.
- [ ] Phase 1 may preserve future enum values or metadata fields only when they are inert, documented as non-goals, and covered by deterministic unsupported-scope behavior.
- [ ] `Phase 1 Specification`: FX canonical backtest requirements, exact API contracts, exact acceptance criteria, Phase 1 edge/error matrix, Phase 1 test suite, and Phase 1 traceability matrix.
- [ ] Shared requirement IDs may appear in both tiers only when the Phase 1 requirement has a precise in-scope behavior and the annex references deferred extensions without changing the Phase 1 contract.
- [ ] Strategies may maintain decision state but shall not mutate official trading state.
- [ ] Vectorized processing is allowed only for indicator and signal generation.
- [ ] Bar-open trading must use previous closed-bar data by default.
- [ ] Production realism shortcuts must be explicitly configured.
- [ ] A shortcut shall never be silently assumed.
- [ ] A simulation must declare asset-class realism requirements for selected instruments.
- [ ] Equities and ETFs require corporate-action treatment for production-realistic classification.
- [ ] Production merge requires CI gates to pass with coverage at least 80%.
- [ ] A batched range shall never skip a possible execution, risk, accounting, session, rollover, or compliance event.
- [ ] FX conversion shall fail closed when rate age exceeds the configured maximum unless diagnostic override is explicitly enabled.
- [ ] Feature-store configuration for point-in-time feature retrieval when machine-learning features are used.
- [ ] Alternative-data configuration for source timing, publication delay, ingestion delay, as-of alignment, lag policy, and embargo policy when non-price data is used.
- [ ] Resource quota configuration for concurrent runs, wall-clock time, temporary storage, queued runs, and worker limits.
- [ ] Market data from a provider.
- [ ] OHLCV bar data.
- [ ] Indicator specifications.
- [ ] Optional order-book depth data.
- [ ] Optional feature-store data and point-in-time feature manifests.
- [ ] Optional alternative data such as sentiment, fundamentals, news, options flow, and external signals.
- [ ] Optional market-halt and limit-up/limit-down data.
- [ ] Optional corporate-action data.
- [ ] Optional futures contract-chain data.
- [ ] Optional perpetual funding-rate data.
- [ ] Optional FX conversion-rate data.
- [ ] Optional benchmark data.
- [ ] Optional optimization configuration.
- [ ] Optional Monte Carlo configuration.
- [ ] Required `MarketDataAuthorityManifest` for production-realistic runs.
- [ ] Required broker profile manifest for MT5-parity and production-realistic FX runs.
- [ ] `max_cross_rate_skew_bps` for cross-rate synthesis validation.
- [ ] Orders history.
- [ ] Deals history.
- [ ] Trade list.
- [ ] Partial-fill history.
- [ ] Exposure curve.
- [ ] Monte Carlo confidence bands when enabled.
- [ ] Environment diagnostic hash and environment drift warning when applicable.
- [ ] Queue, scheduler, worker, quota, and checkpoint metadata for service-mode runs.
- [ ] Latency diagnostics when execution latency modelling is enabled.
- [ ] Feature-store and alternative-data alignment diagnostics when ML or non-price data is used.
- [ ] Step-through replay metadata when debugger mode is used.
- [ ] Rejected FX cross-rate synthesis diagnostics.
- [ ] Usage examples shall run end-to-end.
- [ ] Optional enterprise feature contracts shall be defined early to avoid breaking redesign.
- [ ] Release notes shall reference the applicable `simulation_promotion_manifest.json`.
- [ ] Documentation shall describe approved strategy input modes, strategy registry behavior, and sandbox/vetting requirements if code-based strategy execution is ever enabled.
#### `app/services/simulation/trader.py`

Functions/classes:
- `SimTrader`
- `TradeIntent`
- `TradeRequest`

Requirements:
- [ ] Conversion of timestamped `TradeIntent` objects into sized `TradeRequest` objects.
- [ ] Simulation-only trader interface and MT5-style simulated order/query semantics.
- [ ] Provide simulation-compatible MT5-style accessors and trader methods for controlled strategy integration, including historical tick/bar accessors, symbol/account accessors, order submission/modification/deletion, position queries, order queries, deal/order history, margin/profit calculation, and terminal-style simulation status.
- [ ] Every MT5-style `SimTrader` method exposed to strategies shall define request fields, return fields, mutable-state effects, deterministic rejection codes, and read-only snapshot guarantees before implementation.
- [ ] The system shall transform `TradeIntent` into a sized `TradeRequest`.
- [ ] The system shall support MT5-style `order_send`.
- [ ] `order_send` shall accept action, magic, order, symbol, volume, price, stop-limit price, stop loss, take profit, deviation, order type, fill policy, time policy, expiration, comment, position id, and opposite position id where supported by account mode.
- [ ] The system shall support position modification.
- [ ] The system shall expose MT5-style `position_modify` for stop-loss, take-profit, and supported mutable position fields.
- [ ] The system shall support position close.
- [ ] The system shall expose MT5-style `position_close`.
- [ ] The system shall support order modification.
- [ ] The system shall expose MT5-style `order_modify` for pending-order price, stop-limit price, stop loss, take profit, expiration mode, and expiration timestamp.
- [ ] The system shall support order deletion.
- [ ] The system shall expose MT5-style `order_delete`.
- [ ] The system shall support atomic cancel-replace operations for pending orders where broker or venue semantics allow them.
- [ ] Cancel-replace operations shall preserve, reset, or recompute queue priority according to configured venue rules and shall journal the chosen behavior.
- [ ] The system shall support querying open positions.
- [ ] The system shall expose MT5-style `positions_get` and `positions_total`.
- [ ] The system shall support querying open orders.
- [ ] The system shall expose MT5-style `orders_get` and `orders_total`.
- [ ] The system shall support querying historical deals.
- [ ] The system shall expose MT5-style `history_deals_get` and `deals_total`.
- [ ] The system shall support querying historical orders.
- [ ] The system shall expose MT5-style `history_orders_get` and `history_orders_total`.
- [ ] The system shall support querying account info.
- [ ] The system shall expose MT5-style `account_info`.
- [ ] The system shall expose MT5-style `order_calc_margin` for pre-trade margin estimation.
- [ ] The system shall expose MT5-style `order_calc_profit` for mark-to-market or hypothetical trade profit estimation.
- [ ] The same Trader protocol shall support both simulation and live adapters where live trading is enabled outside the simulator.
- [ ] The simulated Trader protocol shall preserve the same request, response, and query semantics as the live adapter for shared strategy code.
- [ ] Shared Trader protocol definitions may be shared across Simulation and Live/Trading, but Simulation shall implement only simulated behavior and shall not import, instantiate, or call live adapter implementation code.
- [ ] The system shall support `on_tick` callbacks for event-driven strategy execution.
- [ ] The system shall support `on_bar` callbacks for bar-boundary strategy execution.
- [ ] The system shall provide a terminal-style interface for simulation status, account state, open positions, pending orders, and trade events.
- [ ] Terminal-style output shall be controlled by an explicit `verbose` configuration flag.
- [ ] Visual simulation mode shall be supported only as a diagnostic or research view and shall not alter canonical execution results.
- [ ] Progress reporting shall be available for long-running official simulations, optimizations, walk-forward runs, and Monte Carlo runs.
- [ ] The system shall support deterministic step-through replay for debugging.
- [ ] Step-through replay shall allow pausing at a configured timestamp, journal sequence, order event, deal event, bar boundary, strategy callback, or error condition.
- [ ] Debugger hooks shall expose read-only snapshots of tick state, order book where available, orders, deals, positions, account state, strategy-visible inputs, and selected strategy diagnostics.
- [ ] Resuming from a debugger pause shall preserve deterministic replay and shall not alter official results unless a diagnostic mutation mode is explicitly enabled.
- [ ] The simulation module shall accept timestamped `TradeIntent` objects from approved strategies and shall convert them into sized `TradeRequest` objects before execution.
- [ ] Regulatory checks may include pattern day trader checks.
- [ ] Initial US regulatory checks shall include pattern day trader disclosure, short-sale locate configuration, short-sale restriction support where data exists, and position-limit checks where configured.
- [ ] The simulator shall support live/simulation parity through an MT5-style `SimTrader` protocol.
- [ ] The `SimTrader` shall expose MT5-style trading methods to strategies through controlled interfaces.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Pending: the referenced Hardened Draft v1.6 specification, strategy contracts, indicator contracts, data contracts, broker-profile manifests, and market-data authority manifests must be attached or summarized before Builder handoff.
- [ ] Strategy implementation requirements live in `docs/source-requirements/04-strategy.md`.
- [ ] MT5 Strategy Tester semantics are an inspiration and parity target for selected controlled cases, not necessarily a guarantee of exact MT5 behavior for every broker-specific case.
- [ ] Compliance records shall provide evidence of pre-trade checks and risk decisions.
- [ ] Unhandled exceptions at controlled tool boundaries MUST be mapped to `SIM_INTERNAL_ERROR`, logged at `ERROR` level with redacted context, and must not expose secrets, raw strategy code, credentials, or private payloads.
- [ ] MT5-parity tests shall compare supported behavior against controlled MT5 Strategy Tester scenarios.
- [ ] Pre-trade checks and risk-check evidence shall be recorded.
- [ ] `simulation.runner` may launch runs only for authorized strategy ids, data scopes, and artifact roots.
- [ ] Strategy files, market data paths, broker profiles, and artifact destinations shall be resolved through approved registries or allowlisted roots, not arbitrary user-supplied filesystem paths.
- [ ] The tool wrapper shall prevent unregistered or unapproved strategy modules from being invoked.
- [ ] Sandbox policy shall define allowed imports, denied imports, filesystem access, network access, subprocess access, environment-variable access, timeouts, memory limits, and prohibited operations before any code-based strategy path is enabled.
- [ ] The system shall return `SIM_RESEARCH_PROTOCOL_MISSING` when a production-candidate optimized strategy lacks the required research protocol manifest.
- [ ] The system shall not log unsafe raw strategy code bodies in full when rejecting arbitrary-code input.
- [ ] Strategy-input rejection diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code.
- [ ] `SIM_PORTFOLIO_RISK_REJECTED`
- [ ] Mandatory inbound-contract validation for `MarketDataAuthorityManifest` supplied by `app/services/data/` and strategy registry references supplied by `app/services/strategies/` before official runs.
- [ ] The module does not own production risk-governor policy, external governance policy, or human approval workflows.
- [ ] `strategy_ref` shall be a registered strategy identifier plus version or hash; raw Python code strings are invalid.
- [ ] The system shall support fixed-risk sizing.
- [ ] The system shall reject fixed-risk sizing when stop loss is missing.
- [ ] The system shall validate portfolio risk availability.
- [ ] Compliance records shall include risk-check result.
- [ ] Compliance records shall include optional strategy name and version.
- [ ] The simulation module shall consume strategy outputs through the strategy module contract defined in `docs/source-requirements/04-strategy.md`.
- [ ] Monte Carlo outputs shall include risk of ruin.
- [ ] The system shall align benchmark data to the same clock and currency as the strategy.
- [ ] Internal-only fields, secrets, raw credentials, and proprietary strategy source shall not appear in official AI Tool responses.
- [ ] Rejected strategy-input diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code.
- [ ] Strategy research runs shall record a research protocol manifest before optimization begins.
- [ ] Portfolio-risk rejection.
- [ ] Strategy identifier does not exist in registry.
- [ ] Strategy identifier resolves to an unapproved module.
- [ ] Security tests shall cover local trusted mode, external authentication requirement, RBAC authorization, allowlisted strategy/data/artifact roots, secret rejection, and safe errors.
- [ ] Portfolio risk gate shall pass for multi-symbol runs.
- [ ] Portfolio-risk tests shall pass.
- [ ] AI Tool strategy-injection rejection tests shall pass.
- [ ] Successful canonical FX backtest using a registered strategy id and approved data/broker manifests.
- [ ] External contracts required for implementation shall be attached or summarized in this file before Builder handoff, including strategy outputs, indicator manifests, data manifests, broker profiles, market-data authority manifests, and the active source-of-truth baseline.
- [ ] Registered strategy identifier and validated strategy configuration.
- [ ] Portfolio-risk summary.
- [ ] Rejected strategy-injection diagnostics.
- [ ] Strategy developer shall provide vectorized or event-driven strategy logic.
- [ ] Vectorized signal strategy shall compute indicators, generate signals, and convert signals to trade intents.
- [ ] Documentation shall include strategy-capacity diagnostics and production capacity approval procedures.
#### `app/services/simulation/models/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Asset-class production realism depends on enabled models and available data.
- [ ] When Python minor version, dependency lock hash, platform, or decimal/numeric backend differs from the certified profile, official results shall record an environment drift diagnostic and shall not be used for production promotion without compatibility evidence.
- [ ] The system shall stop the simulation on accounting invariant violations unless diagnostic mode is configured.
- [ ] Diagnostic mode shall mark results `diagnostic_failed`, prevent optimization ranking, prevent benchmark promotion, and exclude the run from canonical performance comparisons.
- [ ] Production promotion shall require recorded benchmark results.
- [ ] FX conversions shall store source rate precision, conversion timestamp, and converted cashflow rounded to the account currency precision at the accounting boundary.
- [ ] Production service mode shall enforce per-user, per-tenant, or per-request resource quotas.
- [ ] The complete resolved configuration for a production run shall be serialized into an immutable run-configuration artifact stored alongside results.
- [ ] Production service mode shall define maximum request payload size, maximum resolved configuration size, maximum artifact path length, maximum diagnostic payload size, maximum run duration, maximum queue wait, and maximum retry count before implementation.
- [ ] Canary divergence shall block promotion or trigger rollback without changing the primary user-facing result for the request.
- [ ] Official AI Tool exports shall require or create request id.
- [ ] Compliance records shall be created for accepted and rejected trade requests.
- [ ] Every official run shall record actor id, auth context, role, request id, and authorization decision in audit metadata.
- [ ] External data-provider or broker credentials shall be read only from approved secrets providers or environment bindings and shall never be accepted as plain request payload fields.
- [ ] Externally accessible simulator tools shall not be enabled until threat model, data-governance review, RBAC configuration, redaction policy, retention policy, and protected-artifact policy are approved.
- [ ] Accounting invariant violation shall stop the simulation unless diagnostic mode is explicitly enabled.
- [ ] Missing required model data shall fail fast or be explicitly recorded as an approximation.
- [ ] The system shall return `SIM_RUN_ID_CONFLICT` when a run id or request id conflicts with an existing incompatible run.
- [ ] The system shall return `SIM_MODEL_GOVERNANCE_EXPIRED` when a required model inventory record or approval is expired.
- [ ] The system shall return `SIM_RESOURCE_QUOTA_EXCEEDED` when a request exceeds configured resource quotas.
- [ ] `SIM_UNSUPPORTED_COMMISSION_MODEL`
- [ ] `SIM_POSITION_NOT_FOUND`
- [ ] `SIM_MODEL_GOVERNANCE_EXPIRED`
- [ ] `SIM_ACCOUNT_INVARIANT_BROKEN`
- [ ] The module does not own indicator formula implementation or indicator result contracts; those belong to `app/services/indicators/`.
- [ ] The system shall produce a structured `SimulationResult`.
- [ ] Latency models shall support fixed, distribution-based, venue-profile-based, and disabled modes.
- [ ] The system shall enforce maximum total positions when configured.
- [ ] The system shall enforce maximum positions per symbol when configured.
- [ ] The system shall support hedging account behavior when configured.
- [ ] The system shall support netting account behavior when configured.
- [ ] The system shall support negative-balance-protection configuration.
- [ ] The system shall liquidate deterministically during stopout, defaulting to largest losing position first.
- [ ] MT5 parity evidence shall record broker profile id, broker server label, account type, MT5 build, capture timestamp, symbol specification hash, and fixture data hash.
- [ ] No external broker brand or live account shall be globally authoritative; production parity applies only to approved broker profiles and fixtures.
- [ ] The system shall allow strategies to request a sizing mode but not directly finalize official volume.
- [ ] The system shall apply deals to positions and account state.
- [ ] The system shall recalculate account state.
- [ ] The system shall enforce `Equity = Balance + FloatingPnL`.
- [ ] The system shall create a compliance or audit record for every accepted trade request.
- [ ] The system shall create a compliance or audit record for every rejected trade request.
- [ ] Compliance records shall include request id.
- [ ] Walk-forward results shall separate in-sample and out-of-sample metrics.
- [ ] Optimization caching shall reuse only completed work units whose provenance hash exactly matches the requested run.
- [ ] Optimization result ranking shall be deterministic when objective scores tie.
- [ ] Monte Carlo analysis shall not replace the official backtest result.
- [ ] Benchmark results shall be required before production promotion.
- [ ] Benchmark results shall be stored with release notes.
- [ ] Benchmark manifests shall record OS, CPU model, logical CPU count, RAM, storage type, Python version, dependency lock hash, git commit, and benchmark dataset hash.
- [ ] The system shall support equity.
- [ ] The system shall downgrade realism labels when required asset-class models are disabled.
- [ ] The system shall support corporate-action treatment for production-realistic equity and ETF backtests.
- [ ] Long positions shall receive eligible dividend cashflows.
- [ ] Short positions shall pay applicable dividend cashflows.
- [ ] Dividend cashflows shall be converted to account base currency.
- [ ] Cash dividends, stock splits, and reverse splits shall be the first supported corporate-action treatments for equity and ETF production realism.
- [ ] The system shall support optional short-locate recall and forced buy-in modelling for equity and ETF short positions.
- [ ] Recall models shall support deterministic configured recall events and seeded probabilistic recall rates by symbol, borrow status, and date.
- [ ] Funding shall convert to account base currency.
- [ ] Regulatory checks may include position-limit checks.
- [ ] Wash-sale diagnostics shall flag loss sales followed by repurchases of substantially identical instruments within the configured window and shall disclose after-tax PnL impact only when tax modelling is enabled.
- [ ] Official AI Tools shall require or create request id.
- [ ] Equity, futures, perpetual, and multi-currency examples shall be required before those asset classes are promoted to production-realistic status.
- [ ] Every production-candidate simulator model shall have a model inventory record.
- [ ] Model inventory records shall include model id, owner, purpose, approved use cases, prohibited use cases, asset-class scope, version, dependencies, validation status, materiality tier, known limitations, and review expiry.
- [ ] Production promotion shall require independent validation or documented second-party review for material models.
- [ ] Every model exception, override, accepted limitation, and temporary approval shall require owner, approver, rationale, expiry date, and audit record.
- [ ] Production models shall require periodic re-validation after material code, data, broker-profile, dependency, or calibration changes.
- [ ] Expired, unapproved, or materially changed model inventory records shall block production-realistic classification unless an explicit governance override is present.
- [ ] Retrying the same request id shall be idempotent unless explicitly configured to create a new run id.
- [ ] Unsupported commission model.
- [ ] Position not found.
- [ ] Accounting invariant violation.
- [ ] Malformed request payload.
- [ ] Unknown request field.
- [ ] Missing required request field.
- [ ] Request payload exceeds configured size limit.
- [ ] Secrets, tokens, broker credentials, authorization headers, or provider credentials are supplied in request payload fields.
- [ ] Duplicate request id is submitted concurrently.
- [ ] Duplicate request id is replayed with incompatible material fields.
- [ ] Request validation tests for required fields, unknown fields, malformed payloads, invalid enum casing, invalid date range, missing symbol, oversized payload, path traversal, and secrets in payload fields.
- [ ] Model-governance tests shall cover model inventory validation, expired approvals, missing validation evidence, and accepted model exceptions.
- [ ] Regulatory-constraint tests shall cover PDT rule, short-sale locate, position limits, and disabled-regulatory disclosure.
- [ ] Wash-sale tests shall cover optional taxable-account diagnostics, configured windows, substantially identical instrument mapping, and after-tax disclosure when enabled.
- [ ] Accounting gate shall pass.
- [ ] Model-governance gate shall pass before production promotion.
- [ ] Accounting invariant tests shall pass.
- [ ] Failed request that validates `SIM_INVALID_DATE_RANGE` before data access.
- [ ] A run shall not be labelled production-realistic unless required asset-class models are enabled or proven unnecessary.
- [ ] Monte Carlo analysis must not replace the official backtest result.
- [ ] Structured `SimulationResult`.
- [ ] Account snapshots.
- [ ] Equity curve.
- [ ] Balance curve.
- [ ] Optimization result set with hashes, random seed, and objective function.
- [ ] Structured error result with deterministic error code on failure.
- [ ] Canary comparison results and synthetic transaction probe results when production monitoring is enabled.
- [ ] Visual trade replay export artifact when requested.
- [ ] Benchmark results shall be stored with release notes before production promotion.
- [ ] Release documentation shall include model-validation, research-integrity, calibration, security, and benchmark evidence links for production promotions.
- [ ] Documentation shall include a threat model and data-governance guide before any externally accessible simulator tool is enabled.
- [ ] Documentation shall include model-governance and model-inventory operating procedures.
- [ ] Documentation shall include dynamic model materiality assessment rules and evidence requirements.
#### `app/services/simulation/models/tick.py`

Functions/classes:
- `TradeIntent`
- `FAST_RESEARCH`
- `INTRABAR_EVENT`
- `TIMEFRAME_TICKS`
- `M1_TICKS`
- `REAL_TICKS`
- `SYNTHETIC_TICKS`
- `run_backtest`
- `SimulationConfig`

Requirements:
- [ ] Tick generation, tick stream construction, spread modelling, slippage modelling, liquidity modelling, matching, partial-fill handling, same-tick event priority, gap handling, commission/fee/swap/funding/borrow-fee accounting, and portfolio-level simulation state.
- [ ] Run official tick-based backtests and return standard official tool envelopes.
- [ ] `SimulationBacktestRequestV1` fields: `schema_version`, `request_id`, `actor_context`, `strategy_ref`, `strategy_config`, `symbols`, `timeframe`, `start`, `end`, `initial_balance`, `account_currency`, `tick_model`, `spread_model`, `slippage_model`, `commission_model`, `swap_model`, `broker_profile_ref`, `market_data_authority_ref`, `journal_persistence`, `artifact_root_ref`, `realism_profile`, and `metadata`.
- [ ] The system shall run data-quality checks before indicator calculation, signal generation, or tick generation.
- [ ] The system shall build a canonical bid/ask tick stream before official execution.
- [ ] The system shall use tick execution as the only official production execution mode.
- [ ] The system shall use the canonical bid/ask tick stream as the official execution clock.
- [ ] The system shall convert bar-level or vectorized signals into timestamped `TradeIntent` objects before execution.
- [ ] The system shall execute `TradeIntent` objects only when the tick loop reaches an eligible tick.
- [ ] The system shall prevent vectorized execution from producing official fills, account state, trade journals, or reports.
- [ ] The system shall support an optional approximate `FAST_RESEARCH` mode only when the result is clearly marked as non-canonical, non-MT5-parity, and non-production-realistic.
- [ ] At the first tick of bar `N`, the system shall allow strategies to use only bars up to and including fully closed bar `N-1`.
- [ ] At the first tick of bar `N`, the system shall prohibit use of current incomplete bar `N` high, low, close, or volume.
- [ ] The system shall enter at the first valid tick of bar `N` when a valid trade intent is emitted from previous-closed-bar data.
- [ ] The system shall support `INTRABAR_EVENT` strategies only for event strategies using current tick data.
- [ ] The system shall support `TIMEFRAME_TICKS`.
- [ ] The system shall support `M1_TICKS`.
- [ ] The system shall support `REAL_TICKS`.
- [ ] The system shall support `SYNTHETIC_TICKS`.
- [ ] The system shall represent every execution tick with time, symbol, bid, ask, optional last price, optional volume, source, optional bar time, sequence-in-bar, and bar-open flag.
- [ ] The system shall open buy positions at ask.
- [ ] The system shall close buy positions at bid.
- [ ] The system shall open sell positions at bid.
- [ ] The system shall close sell positions at ask.
- [ ] The system shall convert strategy-timeframe OHLC bars into four-tick paths when using `TIMEFRAME_TICKS`.
- [ ] The system shall convert M1 OHLC bars into four-tick paths when using `M1_TICKS`.
- [ ] The system shall pass broker real ticks through in `REAL_TICKS` mode when bid/ask data is available.
- [ ] The system shall merge bar-based signal timelines into the real tick stream in `REAL_TICKS` mode.
- [ ] The system shall generate `SYNTHETIC_TICKS` from M1 OHLCV bars using an MQL5 Article #75-style support-point algorithm, not a simple four-price path.
- [ ] The system shall treat generated OHLC-derived synthetic prices as bid prices and derive ask prices through the spread model.
- [ ] The system shall produce deterministic synthetic ticks for identical M1 data, symbol spec, spread config, and random seed.
- [ ] Synthetic tick generation shall derive a deterministic per-bar seed instead of relying only on a single mutable global random sequence.
- [ ] The per-bar synthetic-tick seed shall be derived with SHA-256 from schema version, `global_seed`, `symbol_hash`, UTC `bar_open_timestamp`, and synthetic tick algorithm version.
- [ ] `symbol_hash` shall be derived from the canonical JSON representation of the full `SymbolSpec`, including normalized symbol, broker profile id, point, tick size, tick value, contract size, currencies, sessions, and volume constraints.
- [ ] Synthetic tick generation shall remain reproducible when bars are processed out of chronological order.
- [ ] Synthetic tick generation shall remain reproducible when bars are processed in date chunks or parallelized by symbol.
- [ ] Synthetic tick generation shall remain reproducible when a run resumes from a checkpoint.
- [ ] Synthetic tick generation shall journal or expose per-bar seed derivation metadata sufficient to replay a generated bar's tick path.
- [ ] The simulator shall support data modelling modes equivalent to real ticks, simulated ticks, M1 OHLC, trading-timeframe OHLC, and calculation-only research data where explicitly labelled.
- [ ] The simulator shall expose MT5-style historical tick accessors `copy_ticks_from` and `copy_ticks_range` for simulation-compatible data providers.
- [ ] The simulator shall expose MT5-style historical bar accessors `copy_rates_from`, `copy_rates_from_pos`, and `copy_rates_range` for simulation-compatible data providers.
- [ ] The simulator shall expose MT5-style `symbol_info_tick` and `symbol_info` accessors for simulation-compatible symbol metadata and latest tick state.
- [ ] The system shall calculate ask for generated ticks as bid plus spread points multiplied by symbol point.
- [ ] The system shall record spread source and spread points per tick or journal checkpoint.
- [ ] Trade intents shall become eligible for matching only after the configured latency delay has elapsed on the canonical tick clock.
- [ ] The system shall estimate available volume from tick volume, M1 volume, or configured symbol liquidity when using volume-dependent liquidity.
- [ ] The system shall make liquidity decisions deterministically for the same tick, configuration, seed, and order request.
- [ ] The system shall mark the first tick after a session break or weekend as a gap tick.
- [ ] The system shall support treating gap-crossed stop losses as market orders at the first available tick.
- [ ] Gap ambiguity handling shall journal candidate outcomes, selected outcome, rejected alternative, first available tick, affected order ids, and the deterministic reason code.
- [ ] The system shall process same-tick events through a deterministic priority queue.
- [ ] The system shall order same-tick events by tick time, explicit priority, and monotonic sequence number.
- [ ] The system shall process stopout before other same-tick events by default.
- [ ] The system shall process expiration before new triggers for the same timestamp.
- [ ] The system shall process existing position exits before new signal intents by default.
- [ ] The system shall use conservative SL/TP tie-breaking by default unless another mode is explicitly configured.
- [ ] The system shall journal priority decisions for replay.
- [ ] The system shall support daily end-of-day, tick-by-tick, and on-close-only swap calculation modes.
- [ ] The system shall validate OHLCV and tick schemas.
- [ ] The `MarketDataAuthorityManifest` shall declare authoritative sources for bars, real ticks, spreads, corporate actions, futures chains, funding rates, FX conversion rates, and benchmark series.
- [ ] Data lineage shall form a directed acyclic graph tracing from journaled deal or account event to generated tick, support point, M1 bar, normalized source row, raw vendor data file, source manifest, and checksum where applicable.
- [ ] Alternative data shall align to the canonical tick clock without lookahead, using explicit as-of joins and configured lag or embargo policies.
- [ ] The system shall reject missing tick value or point value when required for sizing.
- [ ] Trailing stops shall update deterministically from eligible tick data and shall never use future bar high, low, close, or volume.
- [ ] Pegged-order repricing shall follow explicit tick-size, latency, queue-priority, and market-data availability rules.
- [ ] The system shall mark open positions to market on ticks.
- [ ] The journal shall record tick model.
- [ ] The simulation module shall execute strategy-generated trade intents only when the canonical tick loop reaches an eligible tick.
- [ ] The simulation module shall run data-quality checks before indicator calculation, signal generation, or tick generation.
- [ ] The system shall report ticks processed.
- [ ] Visual replay exports shall include candles or tick references, strategy signals, order events, fills, position state, equity or balance overlays, drawdown overlays, and annotations for rejections or halts.
- [ ] The system shall benchmark tick generation speed.
- [ ] The system shall benchmark tick loop speed.
- [ ] Tick batching may accelerate pure mark-to-market updates.
- [ ] Tick batching shall stop immediately at any tick that may trigger state transitions or compliance events.
- [ ] Tick batching shall never reorder ticks.
- [ ] Tick batching shall never suppress per-event accounting invariants.
- [ ] Tick batching shall be permitted only between known pre-calculated boundary events.
- [ ] Tick batching shall use active pending-order trigger prices, stop-loss prices, take-profit prices, expiration times, stopout thresholds, bar-open times, session boundaries, gap boundaries, swap rollover times, scheduled intent activations, strategy callback boundaries, and compliance boundaries to determine safe batch ranges.
- [ ] Tick batching shall stop before the nearest active boundary that may cause a state transition.
- [ ] Tick batching shall not evaluate or skip past a tick that may trigger a state change.
- [ ] Tick batching shall never infer safety from future bar high, low, close, or volume values unavailable at the current tick.
- [ ] Tick-batching safety diagnostics shall be emitted when batching is enabled.
- [ ] Phase 1 tick batching shall use a conservative boundary-interval proof model that batches only across intervals where all active trigger, session, rollover, strategy, and compliance boundaries are known before the batch starts.
- [ ] FX `production_realistic` V1 classification shall require a documented checklist before Builder handoff. At minimum, the checklist shall evaluate data-quality pass status, approved broker profile, approved market-data authority manifest, tick model, spread model, slippage model, commission model, swap model, margin model, currency-conversion model, no-lookahead status, journal persistence status, replayability, and explicit realism downgrades.
- [ ] The first production FX slice shall cover deterministic tick execution, spreads, slippage, commission, swap, margin, market hours, multi-currency conversion, portfolio checks, journal integrity, and report schemas.
- [ ] Borrow fees shall be applied daily or tick-by-tick according to configuration.
- [ ] Forced buy-ins shall close affected short positions at the first eligible market tick subject to configured latency, liquidity, fees, and market-halt rules.
- [ ] Futures contract metadata shall include root symbol, contract symbol, expiry, first notice date, last trade date, contract size, tick size, tick value, margin currency, and settlement currency.
- [ ] The system shall support real-time tick funding rate mode.
- [ ] The system shall support real-time-tick conversion.
- [ ] Maximum FX rate age shall be configurable by conversion context, including intraday tick conversion, bar-close conversion, daily-bar conversion, margin conversion, fee conversion, dividend conversion, funding conversion, and report-only conversion.
- [ ] Initial US regulatory checks shall explicitly support SEC Rule 201 alternative uptick-rule restrictions where required data is available.
- [ ] Release readiness examples shall include one FX MT5-parity fixture run, one FX production-realistic single-symbol run, one FX multi-symbol portfolio run, one synthetic-tick research approximation run, one severe-data-quality blocked run, one deterministic replay run, and one JSON plus Markdown report pair.
- [ ] Implementation tickets and release manifests shall assign traceability ids such as `SIM-FR-001`, `SIM-NFR-001`, and `SIM-BR-001` to accepted requirements before implementation begins.
- [ ] Implementation tickets and release manifests shall include priority, release phase, owner, acceptance criteria, and verification method for each accepted requirement.
- [ ] Every official run shall use a deterministic lifecycle state machine: `created`, `validated`, `data_prepared`, `signals_built`, `ticks_built`, `executing`, `reporting`, `completed`, `failed`, and `cancelled`.
- [ ] The promotion manifest shall include requirement ids, implementation tickets, test evidence, benchmark evidence, replay evidence, model-validation evidence, security evidence, known exceptions, approvers, approval timestamp, expiry, and release artifact hashes.
- [ ] The same configuration, data, and seed shall produce the same tick stream.
- [ ] Python tick loop with no trade events should target at least 10,000 ticks per second.
- [ ] Synthetic tick generation should target at least 100,000 generated ticks per second where possible.
- [ ] Simple four-tick OHLC generation shall remain separate from MQL5-style synthetic tick generation.
- [ ] MT5 parity comparisons shall require execution timestamps to match the fixture tick timestamp for the same eligible tick.
- [ ] MT5 parity price comparisons shall tolerate at most one half of the symbol tick size, unless the approved broker fixture documents a stricter tolerance.
- [ ] Tradable prices shall be normalized to the symbol tick size.
- [ ] Conservative price rounding shall default to adverse rounding: buy-side executable prices round up to the next valid tick and sell-side executable prices round down to the next valid tick when exact normalization is required.
- [ ] Telemetry shall include stage duration, tick generation rate, tick loop rate, memory high-water mark, journal flush latency, journal backlog, data-quality failure counts, rejection counts, fill counts, and report-generation duration.
- [ ] Every major pipeline stage shall emit an OpenTelemetry-compatible trace span, including validation, data preparation, signal generation, tick generation, execution, reporting, and artifact persistence.
- [ ] `SIM_UNSUPPORTED_TICK_MODEL`
- [ ] `SIM_SYNTHETIC_TICK_GENERATION_FAILED`
- [ ] Phase 1 shall include only `run_backtest`, deterministic tick execution, approved FX symbol metadata, broker-profile fixtures, registered strategy references with validated configuration, data-quality gates, tick generation, spread/slippage/commission/swap models, journal persistence, JSON reports, Markdown reports, schema validation, replay tests, and no-live-side-effect guarantees.
- [ ] All official backtests must execute through a tick loop.
- [ ] A global random seed alone shall not be sufficient for synthetic tick generation in production mode.
- [ ] Synthetic tick randomness shall be locally reproducible per symbol and per bar.
- [ ] `SimulationConfig` with strategy settings, symbols, timeframe, start date, end date, execution mode, tick model, data modelling mode, spread model, signal timing, sizing mode, initial deposit, leverage, margin mode, slippage configuration, optimization configuration, visual mode, progress reporting, terminal verbosity, and random seed.
- [ ] M1 OHLCV data when M1 or synthetic tick generation is used.
- [ ] Real bid/ask tick data when real-tick mode is used.
- [ ] Symbol specifications including point, tick size, tick value, contract size, volume min/max/step, asset class, currencies, sessions, and broker constraints.
- [ ] Required `global_seed` for deterministic synthetic tick generation.
- [ ] Derived `symbol_hash` for per-symbol synthetic tick seed derivation.
- [ ] `bar_open_timestamp` for per-bar synthetic tick seed derivation.
- [ ] Tick-batching boundary metadata derived from active orders, positions, session boundaries, gap boundaries, rollover boundaries, compliance boundaries, and scheduled strategy events.
- [ ] Per-bar synthetic tick seed derivation metadata or replay metadata.
- [ ] Market-halt, limit-up/limit-down, kill-switch, trailing-stop, pegged-order, cancel-replace, recall, forced-buy-in, wash-sale, and alternative-uptick-rule diagnostics when applicable.
- [ ] Tick-batching safety diagnostics when batching is enabled.
- [ ] Event strategy shall respond to initialization, bar-open, tick, and trade-transaction events.
- [ ] Every report shall disclose tick model.
- [ ] Reports shall disclose tick-batching safety diagnostics when batching is enabled.
- [ ] The journal shall document per-bar synthetic tick seed derivation metadata when generated ticks are used.
- [ ] External synthetic tick algorithm reference shall be documented as MQL5 Article #75.
- [ ] Documentation shall describe per-bar synthetic tick seed derivation, including SHA-256 inputs, `global_seed`, `symbol_hash`, UTC `bar_open_timestamp`, and replay metadata.
- [ ] Documentation shall describe checkpoint and replay behavior for synthetic tick generation.
- [ ] Documentation shall describe tick-batching safety boundaries and the Phase 1 boundary-interval proof model.
- [ ] The requirements are domain-wide supporting requirements under `docs/source-requirements/`, not a sprint-specific implementation ticket.
- [ ] Tick execution is the canonical production mode.
- [ ] No file-specific non-functional requirements defined.
- [ ] Unsupported tick model.
- [ ] Tick volume less than or equal to zero.
- [ ] Synthetic tick generation with tick volume equal to 1.
- [ ] Synthetic tick generation with tick volume equal to 2.
- [ ] Synthetic tick generation with tick volume equal to 3.
- [ ] Synthetic tick generation with tick volume greater than 3.
- [ ] Generated ticks exceeding OHLC bounds.
- [ ] Same-tick SL/TP conflict.
- [ ] Stopout and strategy intent on same tick.
- [ ] Pending order expiration and trigger on same tick.
- [ ] Synthetic tick generation resumes from checkpoint mid-run.
- [ ] Synthetic tick generation is parallelized by symbol.
- [ ] Synthetic tick generation is parallelized by date chunk.
- [ ] Synthetic tick generation processes bars out of chronological order.
- [ ] Tick batching approaches active stop loss.
- [ ] Tick batching approaches active take profit.
- [ ] Tick batching approaches pending-order trigger.
- [ ] Tick batching approaches order expiration.
- [ ] Tick batching approaches stopout threshold.
- [ ] Tick batching approaches bar-open signal boundary.
- [ ] Tick batching approaches session boundary.
- [ ] Tick batching approaches gap boundary.
- [ ] Tick batching approaches swap rollover.
- [ ] Tick batching approaches scheduled strategy callback.
- [ ] Tick batching approaches compliance boundary.
- [ ] Tick execution tests for canonical bid/ask tick order, signal timing, previous-closed-bar behavior, and no vectorized official fills.
- [ ] Synthetic tick determinism tests for per-bar seed derivation under sequential, chunked, out-of-order, and checkpoint-resumed processing.
- [ ] Config tests shall cover invalid dates, invalid tick model, invalid spread model, invalid liquidity model, invalid fee/swap config, and missing symbol.
- [ ] Signal-timing tests shall cover previous-close-only behavior, shifted signals, no current-bar leakage, and first tick of new bar activation.
- [ ] Tick-factory tests shall cover timeframe ticks, M1 ticks, real ticks, synthetic ticks, sequence order, and bar-open flags.
- [ ] Synthetic-tick tests shall cover volume 1, volume 2, volume 3, volume greater than 3, support points, determinism, bounds, and MQL5-style behavior.
- [ ] Synthetic-tick tests shall verify that per-bar seed derivation produces identical ticks for full sequential runs, chunked runs, out-of-order bar processing, and checkpoint-resumed runs.
- [ ] Synthetic-tick tests shall verify that different symbols and different bar-open timestamps produce independent deterministic synthetic tick streams.
- [ ] Event-priority tests shall cover same-tick SL/TP conflict, stopout priority, expiration before trigger, and deterministic ordering.
- [ ] Performance tests shall cover tick generation benchmark, tick loop benchmark, memory benchmark, and optimization benchmark.
- [ ] Tick-batching tests shall verify batching stops before active stop loss, active take profit, pending-order trigger, order expiration, stopout threshold, bar-open signal boundary, scheduled strategy callback, market session boundary, gap boundary, swap rollover boundary, and compliance boundary.
- [ ] Tick-batching tests shall verify batching does not use future bar high, low, close, or volume to prove safety.
- [ ] Regulatory-constraint tests shall cover SEC Rule 201 alternative uptick-rule restrictions when required data is available.
- [ ] Rounding tests shall cover tick-size price normalization, adverse rounding, currency cashflow rounding, FX conversion rounding, point precision, and fractional volume steps.
- [ ] Data-lineage tests shall verify lineage from deal and PnL events back to generated ticks, support points, M1 bars, normalized rows, raw vendor files, source manifests, and checksums where applicable.
- [ ] Borrow-fee tests shall verify equity and ETF short borrow fees accrue daily and tick-by-tick when configured, remain distinct from swap and dividends, convert to account base currency, and appear in reports.
- [ ] Synthetic tick tests shall pass.
- [ ] Per-bar synthetic tick seed tests shall pass.
- [ ] Tick-batching boundary proof tests shall pass when tick batching is enabled.
- [ ] Official fills are produced only by the canonical tick loop.
#### `app/services/simulation/models/spread.py`

Functions/classes:
- `NATIVE_SPREAD`
- `FIXED_SPREAD`
- `VARIABLE_SPREAD`

Requirements:
- [ ] The system shall support `NATIVE_SPREAD`.
- [ ] The system shall support `FIXED_SPREAD`.
- [ ] The system shall support `VARIABLE_SPREAD`.
- [ ] The system shall validate that spreads are non-negative.
- [ ] The system shall reject or explicitly repair missing spread data according to configuration.
- [ ] The system shall generate variable spreads deterministically using configured min/max spread and random seed.
- [ ] The system shall support spread-relative slippage.
- [ ] The system shall apply slippage after spread and before final fill-price acceptance.
- [ ] The system shall include spread, slippage, commission, fees, swap, borrow fees, dividends, funding, and configured cashflows in net PnL.
- [ ] The system shall detect negative spreads.
- [ ] The journal shall record spread model.
- [ ] The system shall support calendar-spread rollover.
- [ ] Simulator models shall include execution models, slippage models, liquidity models, spread models, sizing models, risk models, calibration models, strategy models, benchmark models, and data-adjustment models.
- [ ] Production promotion shall require performance to remain acceptable under increased spread, increased slippage, reduced liquidity, delayed execution, missing-data, and gap-stress scenarios.
- [ ] Slippage, spread, market-impact, and liquidity models shall declare calibration data sources.
- [ ] The same configuration, data, and seed shall produce the same spread values.
- [ ] `SIM_UNSUPPORTED_SPREAD_MODEL`
- [ ] `SIM_DATA_NEGATIVE_SPREAD`
- [ ] `SIM_SPREAD_MISSING`
- [ ] Spread data when native spread mode is used.
- [ ] Every report shall disclose spread model.
- [ ] No file-specific non-functional requirements defined.
- [ ] Unsupported spread model.
- [ ] Negative spread.
- [ ] Missing spread.
- [ ] Broker profile fixture tests for approved FX symbol metadata, precision, volume constraints, spread, swap, margin, sessions, and hash stability.
- [ ] Spread, slippage, commission, swap, margin, and accounting golden tests for the approved FX fixture set.
- [ ] Data-quality tests shall cover missing columns, invalid OHLC, duplicate timestamps, non-monotonic time, negative spreads, price outliers, and missing bars.
- [ ] Spread tests shall cover native, fixed, variable, missing spread, negative spread, and deterministic random spread.
- [ ] Slippage tests shall cover fixed, spread-relative, volatility-based, volume-dependent, cap exceeded, and deterministic random slippage.
- [ ] Futures-rollover tests shall cover contract expiry, roll date selection, continuous adjustment, calendar-spread roll, roll PnL attribution, and missing contract-chain failure.
- [ ] Severe missing bars, duplicate timestamps, negative spreads, invalid OHLC bars, or lookahead-sensitive feature data block production runs.
#### `app/services/simulation/models/slippage.py`

Functions/classes:
- `ExecutionRealismConfig`

Requirements:
- [ ] The system shall provide an `ExecutionRealismConfig` containing liquidity, slippage, latency, commission, swap, borrow-fee, market-hours, gap-handling, broker-rules, portfolio-risk, data-quality, corporate-action, futures-rollover, perpetual-funding, and currency-conversion configuration.
- [ ] The system shall prevent production-realistic labelling when infinite liquidity, no slippage, no commission, no swap, or disabled portfolio checks are used without appropriate disclosure.
- [ ] The system shall support fixed-slippage liquidity mode.
- [ ] The system shall produce diagnostics for requested volume, filled volume, unfilled volume, VWAP, slippage points, and market impact.
- [ ] When volume-dependent liquidity and slippage models are both active, liquidity constraints shall be evaluated before slippage.
- [ ] Partial-fill diagnostics shall separately record requested volume, filled volume, unfilled volume, liquidity impact, slippage impact, and cancelled or pending remainder.
- [ ] Execution-quality metrics shall distinguish liquidity shortfall from slippage cost.
- [ ] The system shall support no slippage.
- [ ] The system shall support fixed-point slippage.
- [ ] The system shall support volatility-based slippage.
- [ ] The system shall support volume-dependent slippage.
- [ ] The system shall support queue-position slippage.
- [ ] The system shall apply slippage directionally so that it worsens execution price according to order direction.
- [ ] The system shall cap slippage when a maximum slippage is configured.
- [ ] The system shall use deterministic seeded randomness when randomized slippage is enabled.
- [ ] The system shall journal expected price, executable bid/ask, slippage points, and final fill price.
- [ ] Slippage shall apply only to actually filled volume after liquidity constraints determine fillable quantity.
- [ ] Slippage shall not be charged, journaled as cost, or attributed to an unfilled remainder.
- [ ] The system shall support gap handling by fill with slippage.
- [ ] Before Phase 1 Builder handoff, gap configuration shall explicitly define `gap_policy`, `ambiguous_sl_tp_policy`, `fill_price_source`, `gap_slippage_model`, `max_gap_fill_slippage_points`, and `session_calendar_ref`.
- [ ] The system shall validate slippage and deviation rules.
- [ ] The system shall apply liquidity and slippage results.
- [ ] The journal shall record slippage model.
- [ ] The system shall produce liquidity and slippage diagnostics.
- [ ] FX `production_realistic` V1 shall explicitly exclude broker last-look behavior, broker bias, asymmetric slippage manipulation, news-event volatility-surface expansion, counterparty default risk, and broker solvency modelling.
- [ ] Roll events shall be journaled with old contract, new contract, roll price, adjustment amount, realized roll PnL where applicable, and slippage/fees when simulated.
- [ ] Dynamic materiality reassessment shall be able to upgrade slippage, liquidity, sizing, risk, benchmark, and data-adjustment models to a stricter validation tier for a specific run.
- [ ] Execution-model validation shall compare expected fill price, realized fill price, slippage distribution, rejection rate, partial-fill rate, and latency assumptions.
- [ ] Capacity reports shall include turnover, average participation rate, maximum participation rate, liquidity utilization, slippage sensitivity, and market-impact sensitivity.
- [ ] The same configuration, data, and seed shall produce the same slippage values.
- [ ] Every trade path shall be journaled from validation through sizing, liquidity, slippage, fills, fees, swap, accounting, and compliance checks.
- [ ] `SIM_UNSUPPORTED_SLIPPAGE_MODEL`
- [ ] `SIM_SLIPPAGE_EXCEEDED`
- [ ] Execution-realism configuration for liquidity, slippage, latency, commission, pass-through fees, swap, borrow fees, recall risk, market hours, market halts, gap handling, broker rules, portfolio risk, kill switches, data quality, corporate actions, futures rollover, perpetual funding, currency conversion, benchmark, and regulatory checks.
- [ ] Slippage diagnostics.
- [ ] Every report shall disclose slippage model.
- [ ] No file-specific non-functional requirements defined.
- [ ] Unsupported slippage model.
- [ ] Slippage cap exceeded.
- [ ] Gap-handling tests for rejection, fill-at-open, fill-with-slippage, and ambiguous SL/TP conservative outcome.
- [ ] Liquidity and slippage tests shall verify that liquidity constraints are evaluated before slippage and that slippage applies only to actually filled volume.
- [ ] Execution-quality tests shall verify that liquidity shortfall is distinguished from slippage cost.
#### `app/services/simulation/models/liquidity.py`

Functions/classes:
- `Request`
- `Response`
- `Result`
- `Config`

Requirements:
- [ ] The system shall support infinite liquidity for MT5-parity or early research use only.
- [ ] The system shall support volume-dependent liquidity mode.
- [ ] The system shall support order-book liquidity mode where depth data is available.
- [ ] The system shall walk order-book levels and calculate VWAP execution price when using order-book liquidity.
- [ ] The system shall not guarantee a limit-order fill merely because price touches the limit unless touch-fill is enabled and liquidity is available.
- [ ] The system shall validate liquidity-model compatibility.
- [ ] The journal shall record liquidity model.
- [ ] The system shall calculate liquidity metrics.
- [ ] Model materiality shall be reassessed dynamically per run based on configured exposure, capital, instrument universe, strategy criticality, liquidity usage, and report distribution mode.
- [ ] Reports shall include capacity diagnostics when liquidity or market-impact models are enabled.
- [ ] The same configuration, data, and seed shall produce the same liquidity decisions.
- [ ] `SIM_UNSUPPORTED_LIQUIDITY_MODEL`
- [ ] `SIM_LIQUIDITY_UNAVAILABLE`
- [ ] Liquidity diagnostics.
- [ ] Every report shall disclose liquidity model.
- [ ] Reports shall disclose capacity diagnostics and approved capacity limits when liquidity or market-impact models are enabled.
- [ ] No file-specific non-functional requirements defined.
- [ ] Unsupported liquidity model.
- [ ] Insufficient liquidity.
- [ ] Liquidity tests shall cover infinite liquidity, volume-dependent liquidity, order-book walking, insufficient liquidity, partial fills, and market impact.
- [ ] Dynamic-materiality tests shall cover run-level materiality upgrades from exposure, capital, liquidity usage, instrument universe, and external distribution mode.
- [ ] Short-recall tests shall cover deterministic recall events, seeded probabilistic recall, forced buy-ins, market-halt interaction, liquidity, fees, and journal attribution.
- [ ] Liquidity and partial-fill tests shall pass.
#### `app/services/simulation/models/fee.py`

Functions/classes:
- `Request`
- `Response`
- `Result`
- `Config`

Requirements:
- [ ] The system shall support no commission.
- [ ] The system shall support per-lot commission.
- [ ] The system shall support per-trade commission.
- [ ] The system shall support percent-notional commission.
- [ ] The system shall support tiered commission.
- [ ] The system shall support maker/taker commission.
- [ ] The system shall support pass-through regulatory, exchange, clearing, transaction, activity, and rebate fee models when configured.
- [ ] US equity and ETF fee models may include SEC Section 31 fees, FINRA TAF, exchange-specific maker/taker fees or rebates, and payment-for-order-flow disclosure where relevant.
- [ ] The system shall apply minimum and maximum commission limits when configured.
- [ ] The system shall calculate commission per actual fill, not only per requested order.
- [ ] The system shall support commission currency conversion when account currency differs.
- [ ] The system shall report gross PnL, total costs, and net PnL.
- [ ] Broker profiles shall capture symbol rules, sessions, swap rules, margin rules, fee rules, fill policies, precision, and supported order types.
- [ ] The system shall record queryable data lineage for every data point used in fill-price, mark-to-market, margin, fee, swap, funding, dividend, benchmark, and PnL calculations.
- [ ] Position records shall include time, id, magic, symbol, side or type, volume, open price, current price, stop loss, take profit, commission, margin required, fee, swap, profit, and comment.
- [ ] Trade-info snapshots shall include time, id, magic, symbol, side or type, volume, price, stop loss, take profit, commission, fee, swap, profit, comment, and margin required.
- [ ] The system shall apply borrow-fee events for equity and ETF short positions when configured.
- [ ] The system shall change balance only from closed realized PnL, commission, fee, swap, borrow-fee, dividend, funding, and configured cashflow events.
- [ ] The journal shall record fee and commission model.
- [ ] The system shall produce commission, fee, and swap summaries.
- [ ] Splits shall adjust open position volume and average price without changing economic value before fees or taxes.
- [ ] The system shall support configurable hard-to-borrow borrow fee rates for equity and ETF short positions.
- [ ] Borrow fees shall be distinct from standard swap, dividends, commission, and trade PnL.
- [ ] Borrow-fee cashflows shall be journaled separately from dividends, swap, commission, and trade PnL.
- [ ] Borrow-fee cashflows shall convert to account base currency when the borrow-fee currency differs from account currency.
- [ ] Reports shall disclose total borrow fees paid and the borrow-fee model status.
- [ ] Production-realistic equity or ETF short backtests shall require borrow-fee treatment or shall disclose a realism downgrade or approximation.
- [ ] The system shall support instruments whose profit currency, margin currency, commission currency, dividend currency, borrow-fee currency, funding currency, and account base currency differ.
- [ ] Internal simulation math shall use `Decimal` or equivalent fixed-precision decimal arithmetic for prices, points, fees, FX conversions, margins, cashflows, and account balances.
- [ ] Commission, fees, swap, dividends, funding, realized PnL, and cash ledger entries shall round at each cashflow boundary to the relevant currency precision using the broker profile rule or `ROUND_HALF_UP` when no broker-specific rule exists.
- [ ] Perpetual swaps require funding-rate treatment, funding timestamps, funding currency, and exchange-fee model for production-realistic classification.
- [ ] Balance may change only from closed realized PnL, commission, fee, swap, borrow-fee, dividend, funding, and configured cashflow events.
- [ ] Equity and ETF short production-realistic runs shall include borrow-fee treatment or disclose downgrade or approximation.
- [ ] Equity and ETF borrow-fee configuration for short-selling runs.
- [ ] Commission, fee, swap, and borrow-fee summary.
- [ ] Borrow-fee totals and borrow-fee cashflow history for equity and ETF short runs.
- [ ] Reports shall disclose total borrow fees paid for equity and ETF short runs.
- [ ] Reports shall disclose pass-through regulatory and exchange fees separately from broker commission when configured.
- [ ] External reports shall disclose major assumptions, limitations, model simplifications, data limitations, fees and costs treatment, optimization status, and whether live trading evidence exists.
- [ ] The journal shall document borrow-fee accruals separately from dividends, swap, commission, and trade PnL.
- [ ] The journal shall document delisting outcomes, recall events, forced buy-ins, pass-through regulatory fees, exchange fees, SEC Rule 201 checks, and wash-sale diagnostics when applicable.
- [ ] Documentation shall describe equity and ETF short borrow-fee behavior.
- [ ] Documentation shall include pass-through regulatory and exchange fee models, including US equity examples for SEC Section 31 and FINRA TAF where supported.
- [ ] Documentation shall include delisting, survivorship-bias, recall-risk, forced-buy-in, borrow-fee, SEC Rule 201, and optional wash-sale diagnostic behavior.
- [ ] No file-specific non-functional requirements defined.
- [ ] Equity short position spans a borrow-fee accrual boundary.
- [ ] Borrow-fee data is missing for hard-to-borrow equity.
- [ ] Borrow-fee currency differs from account currency.
- [ ] Fee and commission tests shall cover per-lot, per-trade, percent-notional, tiered, maker/taker, min/max commission, and currency conversion.
- [ ] Pass-through fee tests shall cover regulatory, exchange, clearing, transaction, activity, rebate, SEC Section 31, FINRA TAF, and maker/taker fee attribution where configured.
- [ ] Multi-currency-accounting tests shall cover realized PnL conversion, floating PnL conversion, margin conversion, fee/swap/dividend/funding conversion, and stale FX-rate rejection.
- [ ] Borrow-fee tests shall pass before equity or ETF short-selling runs are production-promoted.
#### `app/services/simulation/models/swap.py`

Functions/classes:
- `Request`
- `Response`
- `Result`
- `Config`

Requirements:
- [ ] The system shall support swap types in points, money, percent, and interest.
- [ ] The system shall apply swap only to positions open across the configured rollover boundary.
- [ ] The system shall support configurable triple-swap day per symbol.
- [ ] The system shall journal swap charges and credits.
- [ ] The system shall reflect swap in account balance and equity.
- [ ] The system shall label overnight backtests with disabled swap as cost-incomplete.
- [ ] The system shall apply swap events.
- [ ] The journal shall record swap model.
- [ ] The journal shall record every swap event.
- [ ] Distributed locks or compare-and-swap commits shall prevent duplicate journal sequences or duplicate checkpoint commits when workers restart mid-batch.
- [ ] If no active orders or open positions exist, batching may proceed only up to the next bar open, session boundary, gap boundary, swap rollover boundary, scheduled intent activation, or strategy callback boundary.
- [ ] The system shall support perpetual swap.
- [ ] Equity, ETF, futures, perpetual swap, spot crypto, CFD, and index instruments shall remain `research_approximation` or explicitly downgraded until their asset-class-specific data, cost, margin, and corporate-action or lifecycle models pass production gates.
- [ ] Funding cashflows shall remain distinct from swap and commission.
- [ ] Phase 1 shall exclude production-realistic labels for equity, ETF, futures, perpetual swap, spot crypto, CFD, index, option, and option-like instruments.
- [ ] The same configuration, data, and seed shall produce the same commission and swap events.
- [ ] MT5 parity money comparisons shall tolerate at most the larger of one account-currency cent or 0.01 percent of the compared value for realized PnL, balance, equity, margin, commission, and swap.
- [ ] `SIM_UNSUPPORTED_SWAP_MODEL`
- [ ] `SIM_SWAP_CALCULATION_FAILED`
- [ ] Multi-currency strategies require base-currency conversion for realized PnL, floating PnL, margin, commission, swap, dividends, funding, and cash balances.
- [ ] Funding summary for perpetual swap runs.
- [ ] Every report shall disclose swap model.
- [ ] The journal shall document poison-pill work-unit quarantine, idempotent write decisions, distributed-lock ownership, compare-and-swap commit outcomes, and optional service degradation events.
- [ ] Documentation shall include poison-pill work-unit quarantine, idempotent queue semantics, distributed locks, compare-and-swap commits, and optional-service degradation behavior.
- [ ] No file-specific non-functional requirements defined.
- [ ] Unsupported swap model.
- [ ] Swap calculation failure.
- [ ] Swap tests shall cover daily rollover, triple-swap day, long/short swap, and disabled-swap disclosure.
- [ ] Accounting tests shall cover equity, margin, free margin, margin level, realized/floating PnL, commission, swap, and stopout.
- [ ] Broker-profile tests shall cover `mt5_demo_reference_fx_v1` metadata, symbol spec hashes, session rules, swap rules, margin rules, and fixture provenance.
- [ ] Distributed-worker tests shall cover poison-pill work-unit quarantine, idempotent journal writes, distributed-lock or compare-and-swap commits, and duplicate checkpoint prevention.
- [ ] Swap and gap tests shall pass.
#### `app/services/simulation/models/margin.py`

Functions/classes:
- `Request`
- `Response`
- `Result`
- `Config`

Requirements:
- [ ] Official simulated orders, deals, positions, pending orders, account state, balance, equity, margin, free margin, margin level, realized PnL, floating PnL, execution timestamps, and immutable simulation journal.
- [ ] The system shall update margin, exposure, commission, and risk immediately after partial fills.
- [ ] The system shall enforce margin-call percentage.
- [ ] The system shall maintain portfolio-level state for multi-symbol backtests.
- [ ] The system shall calculate gross exposure.
- [ ] The system shall calculate net exposure.
- [ ] The system shall calculate currency exposure.
- [ ] The system shall calculate margin contribution by symbol.
- [ ] The system shall calculate concentration.
- [ ] The system shall support optional VaR values.
- [ ] The system shall validate portfolio risk after sizing and before matching.
- [ ] The system shall support independent-symbol margin.
- [ ] The system shall support netted FX margin.
- [ ] The system shall support cross-margin.
- [ ] The system shall support SPAN-like margin mode.
- [ ] The system shall enforce correlation limits when enabled.
- [ ] The system shall enforce concentration limits when enabled.
- [ ] The system shall enforce gross, symbol, and cluster exposure limits when enabled.
- [ ] The system shall evaluate pair, basket, grid, and martingale strategies at portfolio level.
- [ ] The system shall support portfolio-level kill switches that halt new trading when configured drawdown, loss, exposure, margin, volatility, or error thresholds are breached.
- [ ] Kill-switch events shall liquidate, block new orders, cancel pending orders, or enter monitor-only mode according to configuration.
- [ ] Kill-switch decisions shall be journaled with threshold, observed value, action, and actor or policy id.
- [ ] The system shall validate margin availability.
- [ ] The system shall enforce `FreeMargin = Equity - Margin`.
- [ ] The system shall enforce `MarginLevel = Equity / Margin * 100` when margin is greater than zero.
- [ ] The journal shall record every margin event.
- [ ] The simulation module shall enforce that strategies cannot mutate official account, order, deal, position, margin, equity, journal, or execution timestamp state.
- [ ] The system shall produce equity, balance, margin, and exposure curves.
- [ ] Options and option-like contracts shall remain out of scope beyond reserved enum or metadata mentions until an options-specific requirements document defines contract specs, Greeks, exercise/assignment, expiry, corporate actions, margin, pricing, and settlement.
- [ ] Strategies shall not directly mutate official account, order, deal, position, margin, equity, or journal state.
- [ ] `SIM_INSUFFICIENT_MARGIN`
- [ ] Futures require contract metadata, expiry, rollover policy, margin model, and roll-adjustment disclosure for production-realistic classification.
- [ ] Margin curve.
- [ ] Every report shall disclose margin model.
- [ ] No file-specific non-functional requirements defined.
- [ ] Insufficient margin.
- [ ] Position-sizing tests shall cover all sizing modes, invalid inputs, volume normalization, and margin failure.
- [ ] Portfolio-risk tests shall cover exposure, concentration, correlation, portfolio margin, and multi-symbol margin aggregation.
- [ ] Kill-switch tests shall cover drawdown, loss, exposure, margin, volatility, and error-triggered trading halt behavior.
- [ ] Validation tests shall cover volume, stops, freeze, price, margin, portfolio, max positions/orders, and unsupported fill policy.
#### `app/services/simulation/validation/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/simulation/validation/quality.py`

Functions/classes:
- `MarketDataAuthorityManifest`
- `PartialDataPolicy`
- `SIM_DATA_PARTIAL`
- `SIM_DATA_STALE`
- `DataManifestHash`
- `SIM_FEATURE_LOOKAHEAD_DETECTED`

Requirements:
- [ ] Simulation-specific data-quality gating, realism classification, asset-class realism disclosures, benchmark manifests, model-governance evidence, research-integrity evidence, and execution-calibration evidence.
- [ ] Reports shall include IOC remainder cancellations in execution-quality diagnostics.
- [ ] The system shall detect missing required columns.
- [ ] The system shall detect missing bars.
- [ ] The system shall detect duplicate timestamps.
- [ ] The system shall detect non-monotonic timestamps.
- [ ] The system shall detect zero or negative prices.
- [ ] The system shall detect price outliers.
- [ ] The system shall detect impossible OHLC bars.
- [ ] The system shall produce a `DataQualityReport`.
- [ ] The system shall block production runs when severe data-quality thresholds fail unless diagnostic mode is explicitly enabled.
- [ ] The system shall include the data-quality report in the final report.
- [ ] Production simulations shall consume normalized data through the data module contract and an approved `MarketDataAuthorityManifest`.
- [ ] Missing or staging-only authoritative data shall block a production-realistic label unless the affected model is proven unnecessary for the selected instruments.
- [ ] The system shall define a `PartialDataPolicy` for incomplete provider files or partial symbol-day data.
- [ ] `PartialDataPolicy` shall support quarantining the affected symbol and date with `SIM_DATA_PARTIAL`, using stale prior data with `SIM_DATA_STALE` and a configurable staleness limit, or failing the entire run.
- [ ] Stale-data recovery shall be unavailable for production-realistic classification unless explicitly approved and disclosed.
- [ ] Data lineage shall be queryable for audit, replay, model validation, and production-promotion evidence.
- [ ] The market-data authority client shall support a warm cache for frequently read immutable or rarely changed datasets.
- [ ] Warm data cache keys shall include `DataManifestHash`, provider id, dataset id, symbol, timeframe, date range, adjustment mode, and schema version.
- [ ] Cache hits shall skip network transfer only after validating the cached artifact checksum against the authoritative manifest.
- [ ] Cache entries shall expire according to a configured TTL and shall never override point-in-time data snapshot requirements.
- [ ] The simulator shall support optional feature-store integration for machine-learning features.
- [ ] Feature-store integration shall default to disabled in Phase 1. If enabled in a later approved phase, it MUST enforce point-in-time correctness, feature availability timestamps, publication lag, ingestion lag, and deterministic `SIM_FEATURE_LOOKAHEAD_DETECTED` rejection before any feature can influence a decision.
- [ ] Feature-store retrieval shall enforce point-in-time correctness at the canonical decision timestamp, including sub-second or microsecond availability timestamps where provided.
- [ ] Feature-store retrieval shall reject or mask any feature whose computation or publication time is later than the strategy decision time.
- [ ] Alternative data inputs such as sentiment, fundamentals, news, options flow, and external signals shall include event time, ingestion time, publication time, source id, and availability timestamp.
- [ ] The journal shall record data-quality report.
- [ ] The system shall produce data-quality summary.
- [ ] The system shall calculate data-quality metrics.
- [ ] The system shall calculate MT5-style history quality.
- [ ] Production-realistic reports shall attach confidence intervals to every material performance, risk, drawdown, cost, and execution-quality metric when Monte Carlo or bootstrap evidence is available.
- [ ] The system shall calculate execution-quality metrics.
- [ ] Optimization shall reject parameter sets that fail data-quality checks.
- [ ] Equity and ETF runs shall include a corporate-action quality report.
- [ ] Severe data-quality failures shall block production runs unless diagnostic mode is configured.
- [ ] Diagnostic mode shall never produce a `production_realistic` or `mt5_parity_oriented` classification after severe data-quality failure or accounting invariant violation.
- [ ] Public simulation modules shall expose only approved AI Tool wrappers and stable protocol types; internal execution, accounting, journal, data-quality, and reporting services shall remain non-agent-callable and shall be protected by import-boundary tests.
- [ ] Required data-quality gates shall run before calculations and execution.
- [ ] History-quality metadata shall be exposed.
- [ ] The simulator shall emit business-level time-series metrics suitable for dashboards, including run status counts, lookahead violation counts, execution latency, data-quality failure counts, persistence failure counts, queue depth, and quota rejection counts.
- [ ] Severe data-quality failure shall block production runs unless diagnostic mode is explicitly enabled.
- [ ] `SIM_DATA_QUALITY_FAILED`
- [ ] Data-quality report.
- [ ] Corporate-action quality report for equity/ETF runs.
- [ ] Every report shall disclose data-quality status.
- [ ] No file-specific non-functional requirements defined.
- [ ] Report tests for canonical JSON report, required Markdown report, realism disclosure, data-quality summary, cost summary, and artifact manifest.
- [ ] Usage examples shall include canonical FX backtest, severe data-quality blocked run, optimization with streaming journal persistence, and raw Python strategy-code rejection.
- [ ] IOC remainder tests shall verify partial-fill remainder cancellation journals `SIM_IOC_REMAINDER_CANCELLED`, does not fail a valid partial-fill simulation, and appears in execution-quality diagnostics.
- [ ] Data-quality tests shall pass.
- [ ] Severe data-quality blocked run that returns `diagnostic_failed` and does not claim `production_realistic` or `mt5_parity_oriented`.
- [ ] The tool validates config, data quality, strategy registry, broker profile, and market-data authority requirements.
- [ ] The response returns a deterministic `SIM_*` error code, bounded diagnostics, and any safe partial artifacts.
- [ ] The run is not labelled `production_realistic` or `mt5_parity_oriented` after severe data-quality failure.
#### `app/services/simulation/validation/schema.py`

Functions/classes:
- `SimulationResult`
- `run_backtest`

Requirements:
- [ ] Before Builder handoff, each public simulator capability shall define name, purpose, caller type, stability level, official/internal status, request schema, response schema, deterministic error codes, side effects, required permissions, artifact behavior, network behavior, persistence behavior, compatibility guarantees, and at least one success and one deterministic-error example.
- [ ] `SimulationResult`, official tool envelopes, artifact manifests, journal events, report JSON, broker profiles, and market-data authority manifests shall have schema references before Builder handoff.
- [ ] `SimulationToolEnvelopeV1` fields: `schema_version`, `request_id`, `status`, `result`, `error`, `warnings`, `metadata`, and `artifacts`.
- [ ] Every journal event shall include schema version, run id, monotonic sequence number, event timestamp, event type, payload, previous event hash, and event hash.
- [ ] The simulation module shall consume indicator result manifests containing input checksum, parameter hash, implementation version, output schema version, and timing metadata.
- [ ] Visual replay exports shall use a documented JSON schema suitable for charting libraries without becoming the canonical report artifact.
- [ ] Report schema validation shall run before a report is marked complete.
- [ ] Official AI Tools shall use a standard return schema.
- [ ] Official AI Tool responses shall use an envelope containing `schema_version`, `request_id`, `status`, `result`, `error`, `warnings`, `metadata`, and `artifacts`.
- [ ] Official response schemas shall be versioned and backward-compatible within a major schema version.
- [ ] The `run_backtest` AI Tool shall accept only registered strategy identifiers, validated strategy configuration schemas, or code explicitly vetted and sandboxed by the orchestration layer.
- [ ] Determinism guarantees shall be evaluated under the same pinned `requirements.txt` or lockfile, same approved dependency versions, same simulation schema version, and same Python minor version unless a cross-version reproducibility profile is explicitly certified.
- [ ] Public response schemas shall remain backward-compatible within a major schema version, and breaking changes shall require a new major schema version.
- [ ] Alerting shall cover journal persistence failures, schema validation failures, repeated accounting invariant failures, abnormal rejection spikes, data-provider failures, and performance regressions.
- [ ] Official AI Tool exports shall use a standard return schema.
- [ ] The `run_backtest` AI Tool shall require registered strategy identifiers or validated strategy configuration schemas.
- [ ] The strategy registry shall be an explicit allowlist of approved strategy ids, module paths, version hashes, configuration schemas, and permitted execution modes.
- [ ] Any Phase 1 code or schema introduced to accommodate future scope shall be inert by default, guarded by an explicit feature flag or scope tag, and fully tested for deterministic unsupported-scope rejection.
- [ ] Strategy execution shall occur only through registered strategies, validated schemas, or explicitly sandboxed and vetted orchestration paths.
- [ ] Artifact manifest containing paths, media types, schema versions, hashes, sizes, retention tier, and created timestamps.
- [ ] Documentation shall include a schema reference for `SimulationResult`, official AI Tool envelopes, journal events, report JSON, artifact manifests, broker profiles, and market-data authority manifests.
- [ ] Documentation shall include execution-model calibration requirements and calibration artifact schemas.
- [ ] Documentation shall include end-to-end data-lineage graph schema and audit query examples.
- [ ] Documentation shall include deterministic step-through replay and visual trade replay export schema.
- [ ] Documentation shall include the schema and approval workflow for `simulation_promotion_manifest.json`.
- [ ] No file-specific non-functional requirements defined.
- [ ] Contract tests shall verify `run_backtest` success envelopes include `schema_version`, `request_id`, `status`, `result`, `error`, `warnings`, `metadata`, and `artifacts`.
- [ ] Contract tests shall verify public schema backward compatibility within a major schema version.
- [ ] Schema tests shall cover `SimulationResult`, official AI Tool response envelopes, report JSON, report Markdown metadata, artifact manifests, and backward-compatible schema versioning.
- [ ] Visual-replay-export tests shall cover schema validation, signals, fills, order events, equity overlays, drawdown overlays, halt annotations, and derivation from canonical journal artifacts.
- [ ] AI Tool strategy security tests shall verify registered strategy identifiers succeed when schemas are valid, unregistered strategy identifiers are rejected, unapproved modules are rejected, and invalid strategy configuration schemas are rejected.
- [ ] No official tool shall be exported without metadata/schema tests.
- [ ] Response schema and artifact manifest tests shall pass.
- [ ] MT5 parity shall fail when a difference is explained only by an undocumented broker rule, missing symbol metadata, or non-deterministic rounding.
- [ ] Official AI Tool exports shall validate inputs.
- [ ] Every invalid configuration shall return a deterministic error code.
- [ ] Every invalid data condition shall return a deterministic error code.
- [ ] Stale FX conversion rates shall fail or be explicitly recorded according to configuration.
- [ ] The system shall return `SIM_FX_RATE_STALE` when a required FX conversion rate exceeds configured maximum age.
- [ ] The system shall return `SIM_PROMOTION_EVIDENCE_MISSING` when a production promotion manifest lacks required evidence.
- [ ] `SIM_INVALID_CONFIG`
- [ ] `SIM_INVALID_DATE_RANGE`
- [ ] `SIM_MISSING_SYMBOL`
- [ ] `SIM_DATA_MISSING_COLUMN`
- [ ] `SIM_DATA_INVALID_OHLC`
- [ ] `SIM_INVALID_VOLUME`
- [ ] `SIM_INVALID_STOPS_LEVEL`
- [ ] `SIM_INVALID_PRICE`
- [ ] `SIM_SIZING_INVALID_ATR`
- [ ] `SIM_SIZING_INVALID_KELLY_INPUTS`
- [ ] `SIM_FX_RATE_STALE`
- [ ] `SIM_DATA_STALE`
- [ ] `SIM_RESEARCH_PROTOCOL_MISSING`
- [ ] `SIM_PROMOTION_EVIDENCE_MISSING`
- [ ] `market_data_authority_ref` shall reference an approved `MarketDataAuthorityManifest`; inline raw provider credentials are invalid.
- [ ] `broker_profile_ref` shall reference an approved broker profile manifest; inline broker credentials are invalid.
- [ ] The system shall reject missing or invalid Kelly inputs.
- [ ] The system shall reject missing, zero, negative, or misaligned ATR values for volatility sizing.
- [ ] The system shall validate symbol availability.
- [ ] The system shall validate market session availability.
- [ ] The system shall validate volume minimum, maximum, and step.
- [ ] The system shall validate price correctness.
- [ ] The system shall validate stop-loss and take-profit direction.
- [ ] The system shall validate stops level.
- [ ] The system shall validate freeze level.
- [ ] The system shall validate expiration and time policy.
- [ ] The system shall fail fast or explicitly record an approximation when required asset-class data is missing.
- [ ] FX conversion precedence shall be direct pair first, inverse pair second when inverse conversion is enabled, and cross-rate synthesis third when cross-rate synthesis is enabled and all legs pass skew/staleness validation.
- [ ] Phase 1 shall document the exact fallback-chain setting and default before implementation; the default shall fail closed when no approved non-stale direct or enabled inverse rate is available unless the owner approves cross-rate synthesis for the active fixture.
- [ ] Stale FX rates shall fail or be explicitly recorded according to configuration.
- [ ] `stale_rate_tolerance_seconds` may be accepted only as a backward-compatible alias for `max_fx_rate_age_seconds`.
- [ ] If a required conversion rate exceeds the configured maximum age, conversion shall fail closed with `SIM_FX_RATE_STALE` unless diagnostic mode explicitly overrides it.
- [ ] Cross-rate synthesis shall reject mathematically invalid conversion paths.
- [ ] Stale, duplicated, or conflicting run ids shall fail with deterministic error codes.
- [ ] Promotion shall fail when any required evidence artifact is missing, expired, unverifiable, or hash-mismatched.
- [ ] Invalid date range.
- [ ] Missing symbol.
- [ ] Missing required data columns.
- [ ] Invalid OHLC bars.
- [ ] Missing bars beyond threshold.
- [ ] Invalid volume.
- [ ] Invalid stop-loss or take-profit direction.
- [ ] Invalid ATR sizing input.
- [ ] Invalid Kelly sizing input.
- [ ] Missing corporate-action data when required.
- [ ] Missing futures contract chain when required.
- [ ] Missing perpetual funding rate when required.
- [ ] Missing, stale, or unusable FX conversion rate.
- [ ] FX rate is present but stale.
- [ ] FX stale-rate diagnostic override is enabled.
- [ ] FX cross-rate synthesis produces a skewed or invalid conversion rate.
- [ ] Invalid enum casing.
- [ ] Broker-profile timezone rules are missing for a local session calendar.
- [ ] FX conversion tests for direct, inverse, stale, and rejected cross-rate paths according to approved Phase 1 settings.
- [ ] Contract tests shall verify unknown fields, malformed payloads, invalid enum casing, missing required fields, timezone-naive dates, oversized payloads, and path traversal attempts.
- [ ] Partial-data tests shall cover symbol-day quarantine, stale-data fallback, stale-data age limits, whole-run failure, and production-realism downgrade behavior.
- [ ] Research-integrity tests shall cover missing protocol manifests, post-hoc selection disclosure, out-of-sample degradation thresholds, and parameter-sensitivity evidence.
- [ ] Perpetual-funding tests shall cover funding interval, long/short funding direction, funding currency conversion, and missing funding-rate behavior.
- [ ] Promotion-manifest tests shall cover required evidence artifacts, expired approvals, hash mismatches, missing classification, and manifest retention.
- [ ] FX staleness and cross-rate rejection tests shall pass.
- [ ] `PartialDataPolicy` for incomplete provider files, partial symbol-day data, stale-data fallback, quarantine behavior, and fail-fast behavior.
- [ ] `max_fx_rate_age_seconds` or equivalent context-specific FX stale-rate tolerance configuration.
- [ ] FX stale-rate override disclosures.
#### `app/services/simulation/journal.py`

Functions/classes:
- `JournalPersistenceConfig`
- `SIM_FX_CROSS_RATE_REJECTED`
- `run_backtest`
- `SIM_PERSISTENCE_FAILED`
- `SIM_DATA_PARTIAL`
- `PartialDataPolicy`
- `SIM_DATA_STALE`
- `SIM_MARKET_HALT_ACTIVE`
- `SIM_KILL_SWITCH_TRIGGERED`
- `SIM_POISON_WORK_UNIT_QUARANTINED`
- `SIM_OPTIONAL_SERVICE_DEGRADED`
- `SimulationResult`

Requirements:
- [ ] Simulation reports, metrics, artifact manifests, replay metadata, journal persistence, run lifecycle, run idempotency, optimization/walk-forward/Monte Carlo execution evidence, and production-promotion evidence.
- [ ] Produce `SimulationResult`, immutable journal artifacts, canonical JSON reports, required Markdown reports, derived CSV/HTML/visual replay artifacts where configured, and structured error responses.
- [ ] The system shall produce a report from the immutable journal and computed metrics.
- [ ] When an `IOC` order remainder is cancelled, the system shall journal `SIM_IOC_REMAINDER_CANCELLED` as a non-fatal diagnostic event.
- [ ] The system shall maintain an immutable trade journal.
- [ ] The journal shall record config hash.
- [ ] The journal shall record data checksum.
- [ ] The journal shall record sizing model.
- [ ] The journal shall record signal timing policy.
- [ ] The journal shall record every event priority decision.
- [ ] The journal shall record every order state transition.
- [ ] The journal shall record every deal and partial fill.
- [ ] The journal shall record every position update.
- [ ] The journal shall record every account snapshot.
- [ ] The journal shall record every rejection and error.
- [ ] The journal shall record every compliance record.
- [ ] The canonical journal storage format shall be append-only JSON Lines with one event per line.
- [ ] Optional Parquet and CSV journal exports may be generated for analysis, but they shall be derived artifacts and not the canonical replay source.
- [ ] Artifact integrity checks shall fail when journal hashes, manifest checksums, or sequence continuity are invalid.
- [ ] The immutable journal shall support streaming append-to-disk persistence.
- [ ] Append-only journal storage shall support long optimization, walk-forward, and Monte Carlo runs without materializing every run journal in process memory.
- [ ] Holding all optimization, walk-forward, or Monte Carlo journals in memory shall be forbidden for production runs.
- [ ] Journal persistence failures shall fail closed with `SIM_PERSISTENCE_FAILED`.
- [ ] Streaming journal writes shall preserve event ordering, replayability, config hash, data checksum, parameter hash, random seed, and objective metadata for each run.
- [ ] The report shall disclose the journal storage backend and durability mode used for the run.
- [ ] `JournalPersistenceConfig` shall include backend selection, durability mode, flush batch size, maximum in-memory buffer size, and sidecar index configuration.
- [ ] Phase 1 shall use append-only JSON Lines as the mandatory canonical streaming journal backend.
- [ ] Phase 1 shall use a SQLite sidecar index as the initial random-access journal query format for report generation and diagnostics.
- [ ] Phase 1 journal durability shall default to fsync per batch, with a maximum batch of 1,000 events, five seconds, or 16 MB before flush, whichever occurs first.
- [ ] Production journal persistence shall fsync before marking a run complete or before emitting final reports.
- [ ] If a journal write, flush, fsync, sidecar transaction, or commit fails, the run shall stop in production mode and return `SIM_PERSISTENCE_FAILED`.
- [ ] After persistence failure, diagnostics shall include journal backend, run id, failed operation, and last committed sequence number.
- [ ] The simulation module shall journal strategy id, strategy version, configuration hash, rationale where provided, and strategy-input rejection diagnostics.
- [ ] The simulation module shall prevent vectorized indicator or signal generation from producing official fills, account state, trade journals, or reports.
- [ ] Visual trade replay export shall be supported as a derived artifact from the canonical journal and report JSON.
- [ ] If JSON and human-readable report artifacts disagree, the run shall fail report validation until the derived artifact is regenerated from canonical JSON and journal data.
- [ ] Requeued work units shall preserve deterministic provenance hashes and shall not duplicate completed journal or report artifacts.
- [ ] Task queues and worker leases shall provide exactly-once effects or idempotent execution for journal writes, checkpoint commits, sidecar index updates, and artifact publication.
- [ ] The system shall support Monte Carlo analysis after a canonical journal exists.
- [ ] The system shall support bootstrap robustness analysis from the immutable journal.
- [ ] The system shall include asset-class realism decisions in the immutable journal and final report header.
- [ ] Split adjustment events shall be journaled with before/after volume, price, SL, TP, and pending-order state.
- [ ] Recall and forced-buy-in events shall be journaled separately from strategy-initiated exits.
- [ ] If a higher-precedence rate exists but is stale, invalid, or checksum-mismatched, the fallback chain shall follow explicit configuration: either fail closed immediately or continue to the next enabled source with a journaled diagnostic.
- [ ] Every conversion shall be journaled with rate, source, timestamp, and age.
- [ ] FX stale-rate diagnostic overrides shall be journaled and disclosed in the report.
- [ ] Rejected cross-rate paths shall return or journal `SIM_FX_CROSS_RATE_REJECTED`.
- [ ] Rejected cross-rate paths shall be journaled with failed currency graph, requested conversion pair, candidate path, computed rate, reference rate when available, skew, and rejection reason.
- [ ] Regulatory checks shall be fully journaled when enabled.
- [ ] The `run_backtest` AI Tool shall journal rejected strategy-injection attempts without logging unsafe code bodies in full.
- [ ] Capacity assumptions shall be journaled and included in the realism disclosure.
- [ ] A cancelled run shall produce a structured cancelled result, partial artifact manifest, final journal flush attempt, and cancellation diagnostic.
- [ ] Run lifecycle transitions shall be journaled with actor, request id, timestamp, previous state, next state, and transition reason.
- [ ] The same configuration, data, and seed shall produce the same journal.
- [ ] Every shortcut shall be recorded in configuration, journal, and final report.
- [ ] Production service mode shall expose health checks for data access, artifact storage, journal backend, sidecar index, secrets provider, and worker capacity.
- [ ] Production service mode shall define SLOs for run startup latency, successful completion rate, journal durability, artifact availability, and report-generation latency.
- [ ] Operational runbooks shall cover failed runs, corrupted sidecar index, journal replay recovery, data-source outage, artifact restore, stuck worker, and rollback after bad release.
- [ ] The immutable journal shall preserve audit evidence.
- [ ] `simulation.viewer` may read authorized reports and metadata but shall not launch runs or read protected journals.
- [ ] Logs, reports, and journals may include run id, request id, actor id or pseudonymous actor id, strategy id, strategy version, symbol, timeframe, non-secret configuration, checksums, aggregate metrics, diagnostics, and artifact references.
- [ ] Logs, reports, and journals shall not include API keys, tokens, passwords, private keys, full broker credentials, raw personal identifiers, payment data, unrestricted account identifiers, proprietary strategy source code, or raw proprietary market data payloads unless an explicit protected-artifact policy allows it.
- [ ] Production-candidate and validation journals, reports, and benchmark metadata shall default to a seven-year retention tier.
- [ ] Artifact export shall include checksums for reports, journals, tables, and benchmark files.
- [ ] Protected journals, artifact manifests, report bundles, and replay evidence shall define encryption-at-rest requirements before any externally accessible or production-candidate simulator surface is enabled.
- [ ] The system shall return `SIM_PERSISTENCE_FAILED` when the journal cannot be written, flushed, fsynced, committed, indexed, or otherwise persisted.
- [ ] The system shall journal `SIM_IOC_REMAINDER_CANCELLED` when an IOC order remainder is cancelled after a valid partial fill.
- [ ] The system shall return or journal `SIM_FX_CROSS_RATE_REJECTED` when FX cross-rate synthesis is rejected due to invalid, circular, or skewed conversion paths.
- [ ] The system shall return or journal `SIM_DATA_PARTIAL` when partial data is quarantined according to `PartialDataPolicy`.
- [ ] The system shall return or journal `SIM_DATA_STALE` when stale data is used under an explicit stale-data policy.
- [ ] The system shall journal `SIM_ENVIRONMENT_DRIFT_WARNING` when runtime environment differs from the certified benchmark profile.
- [ ] The system shall return or journal `SIM_MARKET_HALT_ACTIVE` when trading is blocked or deferred by a halt or limit-up/limit-down state.
- [ ] The system shall return or journal `SIM_KILL_SWITCH_TRIGGERED` when portfolio kill-switch policy blocks or alters trading.
- [ ] The system shall return or journal `SIM_POISON_WORK_UNIT_QUARANTINED` when a repeated-failure work unit is quarantined.
- [ ] The system shall return or journal `SIM_OPTIONAL_SERVICE_DEGRADED` when a non-production run falls back after optional cache or sidecar service failure.
- [ ] Persistence-failure diagnostics shall include journal backend, run id, failed operation, and last committed sequence number.
- [ ] Risk rejections must be journaled.
- [ ] Streaming journal persistence shall be mandatory for optimization, walk-forward, and Monte Carlo production runs.
- [ ] Production runs shall fail closed when journal persistence fails.
- [ ] `IOC` remainder cancellation shall be a journaled diagnostic, not a silent side effect.
- [ ] Journal persistence configuration for streaming append-to-disk storage.
- [ ] Journal backend selection with Phase 1 support for canonical JSONL and SQLite sidecar index.
- [ ] Immutable journal.
- [ ] Journal persistence backend and durability metadata.
- [ ] Persistence-failure diagnostics when journal writes, flushes, fsyncs, sidecar transactions, or commits fail.
- [ ] The immutable journal shall act as the audit and replay source.
- [ ] Reports shall disclose journal storage backend, durability mode, and sidecar index usage.
- [ ] The journal shall document configuration hash and data checksum.
- [ ] The journal shall document model choices used in the run.
- [ ] The journal shall document every state transition and rejection.
- [ ] The journal shall document every compliance record.
- [ ] The journal shall document currency conversion rate, source, timestamp, and age for every conversion.
- [ ] The journal shall document asset-class realism decisions.
- [ ] The journal shall document persistence backend, durability mode, flush policy, sidecar index configuration, and last committed sequence.
- [ ] The journal shall document strategy-input rejection attempts without logging unsafe code bodies in full.
- [ ] The journal shall document IOC remainder cancellations as non-fatal diagnostics.
- [ ] The journal shall document FX stale-rate overrides and rejected cross-rate synthesis paths.
- [ ] The journal shall document model inventory ids, model validation evidence ids, governance overrides, and model exception expiry.
- [ ] The journal shall document research protocol manifest id, selected-parameter lineage, and out-of-sample validation evidence.
- [ ] The journal shall document execution-calibration artifact ids and calibration status for execution realism models.
- [ ] The journal shall document latency model id, latency components, delayed eligibility time, and latency-affected fill decisions.
- [ ] The journal shall document capacity assumptions, approved limits, and capacity-limit violations.
- [ ] The journal shall document market halts, limit-up/limit-down states, kill-switch triggers, trailing-stop updates, pegged-order repricing, and cancel-replace operations.
- [ ] The journal shall document feature-store retrieval timestamps, feature availability timestamps, alternative-data as-of alignment, and rejected feature lookahead events.
- [ ] The journal shall document run lifecycle transitions, idempotency decisions, cancellations, and checkpoint compatibility checks.
- [ ] The journal shall document vendor/source inventory ids, point-in-time snapshot ids, and material vendor-data limitations.
- [ ] The journal shall document immutable run-configuration artifact id, environment diagnostic hash, and environment drift warnings.
- [ ] The journal shall document resource quota checks, queue transitions, worker assignment, worker heartbeat loss, requeue decisions, retry attempts, and resume checkpoints.
- [ ] The journal shall document partial-data policy decisions, quarantined symbol-date ranges, stale-data use, and stale-data age.
- [ ] The journal shall document data-lineage artifact ids for fill-price, mark-to-market, and PnL events.
- [ ] The journal shall document trace ids, span ids, synthetic transaction probe ids, and canary comparison ids when applicable.
- [ ] Documentation shall describe streaming journal persistence requirements, supported journal storage backends, SQLite sidecar indexing, fsync-per-batch durability, and maximum in-memory journal buffer limits.
- [ ] Documentation shall describe Phase 1 defaults for MT5 parity tolerance, JSONL journal storage, SQLite sidecar indexing, canonical JSON report format, and required Markdown report format.
- [ ] Reports and journals are required artifacts, not optional diagnostics.
- [ ] No file-specific non-functional requirements defined.
- [ ] Optimization run produces too many journal events for memory.
- [ ] Walk-forward run produces too many journal events for memory.
- [ ] Monte Carlo run attempts to materialize all journals in memory.
- [ ] Journal append-to-disk write fails.
- [ ] Journal backend becomes unavailable mid-run.
- [ ] Journal write succeeds but flush or commit fails.
- [ ] Authorized actor lacks access to requested strategy id, data scope, broker profile, journal, or artifact root.
- [ ] Filesystem permission is denied for journal, sidecar index, report, or artifact root.
- [ ] Disk becomes full during journal append, report generation, sidecar index write, or artifact manifest write.
- [ ] Canonical journal exists but the SQLite sidecar index is corrupted.
- [ ] Canonical journal hash chain or sequence validation fails.
- [ ] Protected journal access is denied to a viewer or unauthorized service account.
- [ ] Journal persistence tests for append-only JSONL, SQLite sidecar indexing, hash-chain/sequence validation, replay, and fail-closed persistence errors.
- [ ] Fault-injection tests for disk-full during journal append, disk-full during report generation, flush failure, fsync failure, SQLite sidecar transaction failure, and artifact manifest write failure.
- [ ] Run-lifecycle tests shall cover idempotent retries, duplicate run ids, cancellation artifacts, checkpoint compatibility, and lifecycle transition journaling.
- [ ] Reporting tests shall verify metrics are reproducible from the journal and include realism disclosure, cost diagnostics, and portfolio diagnostics.
- [ ] Journal persistence tests shall cover streaming append behavior, journal replay from append-only storage, SQLite sidecar indexing, and report generation from persisted journals.
- [ ] Journal persistence tests shall verify optimization, walk-forward, and Monte Carlo runs do not retain all journals in memory.
- [ ] Journal persistence tests shall verify journal write, flush, fsync, sidecar transaction, and commit failures return `SIM_PERSISTENCE_FAILED`.
- [ ] Journal persistence tests shall verify last committed journal sequence is recoverable after persistence failure.
- [ ] Performance tests shall include memory profiles for optimization, walk-forward, and Monte Carlo runs with streaming journal persistence enabled.
- [ ] Corporate-action tests shall cover dividend cashflow, split adjustment, reverse split, merger/delisting policy, adjusted/unadjusted price modes, and journal disclosure.
- [ ] FX staleness tests shall verify stale rates return `SIM_FX_RATE_STALE`, diagnostic overrides require explicit configuration, and stale-rate overrides are journaled and disclosed.
- [ ] FX cross-rate tests shall verify circular paths, mathematically invalid rates, and skewed rates outside configured tolerance return or journal `SIM_FX_CROSS_RATE_REJECTED`.
- [ ] Chaos and fault-injection tests shall simulate disk-full, permission-denied, journal flush failure, sidecar transaction failure, artifact-store outage, and worker heartbeat loss with deterministic error envelopes and no silent artifact promotion.
- [ ] Debug-replay tests shall cover pause by timestamp, journal sequence, event, bar boundary, strategy callback, and error condition with deterministic resume.
- [ ] Streaming journal persistence and failure tests shall pass.
- [ ] The result includes a `SimulationResult`, journal artifact, JSON report, Markdown report, artifact manifest, metrics, and realism disclosure.
- [ ] Work units are deterministic and resumable.
- [ ] Journals are streamed to disk instead of held fully in memory.
- [ ] Ranking is deterministic when objective scores tie.
- [ ] Controlled tool boundaries MUST return a deterministic `SIM_*` error code and safe redacted error envelope for all handled failures. Custom simulation exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
- [ ] Diagnostic mode shall require an explicit configuration flag, actor id, rationale, and audit record.
- [ ] `SIM_EVENT_PRIORITY_CONFLICT`
- [ ] The system shall prevent or defer trading during market halts and limit-up/limit-down states according to exchange and broker policy.
- [ ] The system shall apply commission events.
- [ ] Dividend events shall be recorded separately from trade PnL.
- [ ] The system shall support spot-at-event-time conversion.
- [ ] Event-priority conflict.
- [ ] Delisting tests shall cover final exchange price, OTC price, cash consideration, liquidation value, total-loss treatment, and prevention of silent symbol dropping.
- [ ] Alternative-data tests shall cover irregular event times, delayed publication, ingestion timestamps, as-of alignment, lag policy, embargo policy, and no-lookahead behavior.
- [ ] Event-priority tests shall pass.
- [ ] Futures roll events and roll PnL attribution for futures runs.
- [ ] Data-lineage graph or lineage artifact references for audited data points.
#### `app/services/simulation/report.py`

Functions/classes:
- `SimulationReport`
- `SimulationSummary`
- `generate_simulation_report`
- `serialize_simulation_report`

Requirements:
- [ ] The module does not treat research approximation, visual mode, notebook objects, or derived exports as canonical execution or reporting artifacts.
- [ ] The module does not own OS-level resource management such as process pools, thread-pool orchestration, global memory management, or platform scheduler policy beyond enforcing configured Simulation resource quotas and reporting quota diagnostics.
- [ ] Support optimization, walk-forward, Monte Carlo, bootstrap, deterministic replay, step-through replay, visual replay export, benchmark reporting, production-promotion manifests, and service-mode run lifecycle operations where enabled.
- [ ] The system shall disclose every enabled, disabled, or simplified realism model in the final report.
- [ ] The system shall record gap-handling rules in the report.
- [ ] The system shall produce a trades list.
- [ ] The system shall produce orders history.
- [ ] The system shall produce deals history.
- [ ] The system shall produce partial-fill history.
- [ ] The system shall produce position lifecycle history.
- [ ] The system shall produce portfolio-risk summary.
- [ ] The system shall produce realism-disclosure summary.
- [ ] The system shall calculate PnL metrics.
- [ ] The system shall calculate cost metrics.
- [ ] The system shall calculate trade statistics.
- [ ] The system shall calculate streak statistics.
- [ ] The system shall calculate regression metrics.
- [ ] The system shall calculate return metrics.
- [ ] The system shall calculate drawdown metrics.
- [ ] The system shall report bars processed.
- [ ] The system shall report symbols involved.
- [ ] The system shall calculate total net profit, gross profit, gross loss, profit factor, expected payoff, recovery factor, and Sharpe ratio.
- [ ] The system shall calculate Z-score for win/loss sequence randomness.
- [ ] The system shall calculate AHPR and GHPR when return series and trade count are sufficient.
- [ ] The system shall calculate linear-regression correlation and linear-regression standard error for the equity curve.
- [ ] The system shall calculate total trades, total deals, short trades and win percentage, long trades and win percentage, profit trades and percentage, and loss trades and percentage.
- [ ] The system shall calculate largest profit trade, largest loss trade, average profit trade, and average loss trade.
- [ ] The system shall calculate maximum consecutive wins, maximum consecutive losses, maximal consecutive profit, maximal consecutive loss, average consecutive wins, and average consecutive losses.
- [ ] The system shall calculate balance drawdown absolute, equity drawdown absolute, balance drawdown maximal, equity drawdown maximal, balance drawdown relative, and equity drawdown relative.
- [ ] Metrics without confidence intervals in production-realistic reports shall disclose why interval evidence is unavailable and whether the omission downgrades the result.
- [ ] The system shall calculate portfolio metrics.
- [ ] The system shall include robustness metrics when Monte Carlo or walk-forward analysis is enabled.
- [ ] Every report shall state whether the run used full production realism, MT5-parity settings, or research approximation settings.
- [ ] The official report formats shall be JSON and Markdown.
- [ ] HTML reports may be generated from the official JSON and Markdown artifacts.
- [ ] CSV exports shall be supported for tabular report sections such as orders, deals, trades, positions, account snapshots, and diagnostics.
- [ ] Notebook objects may consume official artifacts but shall not be a required production report format.
- [ ] The official JSON report shall be the canonical machine-readable report artifact.
- [ ] The official Markdown report shall be the required human-review report artifact for Phase 1 CI and release evidence.
- [ ] A run shall not receive `production_realistic` classification unless every required checklist item is true or explicitly marked not applicable by an approved owner decision recorded in the report.
- [ ] Reports using FX `production_realistic` V1 shall disclose these non-goals when they are material to interpretation.
- [ ] Reports shall disclose when dividend income is ignored.
- [ ] Delisting losses, including possible negative 100 percent returns for equity holdings, shall be reflected in realized PnL, equity curve, drawdown, and reports.
- [ ] Production-equity reports shall disclose unsupported corporate-action behavior.
- [ ] Reports shall separate trade PnL from roll yield where possible.
- [ ] Reports shall disclose total funding paid or received.
- [ ] Reports shall disclose net trading PnL excluding funding.
- [ ] Portfolio reports shall include currency exposure and currency PnL attribution.
- [ ] The system shall support optional benchmark-relative reports.
- [ ] Reports shall clearly omit benchmark metrics when benchmark data is not provided.
- [ ] Disabled regulatory checks shall be disclosed for regulated asset-class reports.
- [ ] Optimization reports shall disclose total parameter combinations tested, rejected combinations, failed combinations, and final selected parameter lineage.
- [ ] Reports shall disclose whether a result is single-run, optimized, walk-forward selected, or post-hoc selected.
- [ ] Reports shall warn when the same dataset was used for strategy discovery, parameter selection, and final evaluation.
- [ ] Reports shall disclose whether execution models are broker-calibrated, venue-calibrated, generic, synthetic, or uncalibrated.
- [ ] Reports shall disclose material vendor-data limitations.
- [ ] Data-source license or retention conflicts shall block external report export unless explicitly approved.
- [ ] Point calculations shall preserve decimal precision internally and shall be rounded only at configured reporting or validation boundaries.
- [ ] Production runs shall fail closed or require explicit diagnostic override when optional service degradation would weaken durability, replayability, auditability, or report correctness.
- [ ] Sensitive identifiers shall be redacted, hashed, or pseudonymized before appearing in standard logs or reports.
- [ ] A generated traceability report shall fail CI when an accepted implementation requirement lacks mapped verification or when a future requirement is marked blocking for Phase 1 without owner approval.
- [ ] Production realism shortcuts must be disclosed in the report.
- [ ] Benchmark-relative reports require benchmark data aligned to the same clock and currency as the strategy.
- [ ] A required model may be disabled only if the report records the disablement and downgrades the realism label where relevant.
- [ ] Multi-currency cash ledgers and currency exposure report.
- [ ] Every report shall disclose commission model.
- [ ] Every report shall disclose market-hours and gap policy.
- [ ] Every report shall disclose portfolio-risk model.
- [ ] Every report shall disclose corporate-action model.
- [ ] Every report shall disclose futures-rollover model.
- [ ] Every report shall disclose perpetual-funding model.
- [ ] Every report shall disclose currency-conversion model.
- [ ] Every report shall disclose benchmark model.
- [ ] Every report shall disclose regulatory-constraint model.
- [ ] Every report shall disclose the run classification: `production_realistic`, asset-class-specific production-realistic label, `mt5_parity_oriented`, or `research_approximation`.
- [ ] Every report shall disclose disabled required models and any realism-label downgrade.
- [ ] Equity reports shall disclose corporate-action adjustment method.
- [ ] Futures reports shall disclose rollover policy and roll PnL attribution where possible.
- [ ] Perpetual reports shall disclose total funding paid/received and net trading PnL excluding funding.
- [ ] Multi-currency reports shall reconcile native and base-currency ledgers.
- [ ] Reports shall disclose IOC remainder cancellation diagnostics.
- [ ] Reports shall disclose FX stale-rate diagnostic overrides.
- [ ] Reports shall disclose rejected FX cross-rate synthesis diagnostics when they affect a run.
- [ ] Reports shall disclose model inventory ids, validation status, material model exceptions, and approval expiry for production-candidate runs.
- [ ] Reports shall disclose research protocol id, selection method, optimization status, out-of-sample degradation, and parameter-sensitivity status when strategy research or optimization influenced the result.
- [ ] Reports shall disclose execution-model calibration status and whether execution models are broker-calibrated, venue-calibrated, generic, synthetic, or uncalibrated.
- [ ] Reports shall disclose execution latency model, latency assumptions, and latency diagnostics when latency modelling is enabled.
- [ ] Reports shall disclose market-halt, limit-up/limit-down, portfolio kill-switch, trailing-stop, pegged-order, and cancel-replace behavior when encountered.
- [ ] Equity and ETF reports shall disclose delisting treatment, recall-risk model, forced buy-ins, and borrow availability assumptions when applicable.
- [ ] Regulated asset reports shall disclose SEC Rule 201, wash-sale diagnostics, and disabled tax-aware or regulatory modules where applicable.
- [ ] ML or alternative-data reports shall disclose feature-store point-in-time status, alternative-data alignment policies, lag assumptions, and rejected feature lookahead diagnostics.
- [ ] Reports shall disclose vendor-data limitations, data revision policy, and point-in-time snapshot status when external data sources are used.
- [ ] Reports shall disclose partial-data handling decisions, quarantined symbol-date ranges, stale-data fallback usage, and any resulting realism downgrade.
- [ ] Reports shall disclose metric confidence intervals for material production-realistic metrics or explicitly disclose why intervals are unavailable.
- [ ] Reports shall disclose immutable run-configuration artifact id, environment diagnostic hash, and environment drift warnings when applicable.
- [ ] Reports shall disclose queue wait time, execution worker id, retry count, resume source, and checkpoint id for service-mode runs.
- [ ] Reports shall disclose canary comparison and synthetic transaction probe evidence when used for release or service-health validation.
- [ ] Reports shall disclose FX `production_realistic` V1 non-goals where material.
- [ ] Reports shall declare distribution mode: `internal_research`, `internal_production_review`, `client_facing`, `investor_facing`, or `public`.
- [ ] Client-facing, investor-facing, or public reports shall include hypothetical-performance disclosures when results are simulated.
- [ ] External report generation shall support a compliance approval workflow before export.
- [ ] External reports shall prevent unsupported performance claims and shall include configured legal or compliance disclaimers.
- [ ] Documentation shall include report examples for FX, equity, futures, perpetual, and multi-currency portfolios before those scopes are production-promoted.
- [ ] Documentation shall describe FX stale-rate behavior, `max_fx_rate_age_seconds`, diagnostic overrides, and report disclosures.
- [ ] Documentation shall include confidence interval methodology for reported metrics and downgrade behavior when intervals are unavailable.
- [ ] Documentation shall include external-report distribution modes, hypothetical-performance disclosures, compliance approval workflow, and unsupported-claim controls.
- [ ] No file-specific non-functional requirements defined.
- [ ] Disabled regulatory checks for regulated asset-class reports.
- [ ] Corrupted artifact manifest is encountered during replay or report generation.
- [ ] Requirement-to-test traceability report for all accepted Phase 1 requirements.
- [ ] Report-confidence-interval tests shall verify material production-realistic metrics include confidence intervals or explicit omission disclosure and downgrade behavior.
### Unit Tests Required

```text
tests/unit/app/services/simulation/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/08_simulation.py
```

Usage examples must show:
- `example_01_run_backtest`: Demonstrate canonical backtest request, run lifecycle, standard result, and reproducible run IDs.
- `example_02_tick_engine_and_orders`: Demonstrate market, limit, stop, stop-limit, trailing-stop, and pegged order behavior.
- `example_03_execution_costs_and_slippage`: Demonstrate spreads, commissions, swaps, slippage caps, and liquidity walk behavior.
- `example_04_positions_and_accounting`: Demonstrate hedging/netting positions, margin, PnL, equity, and balance accounting.
- `example_05_journal_and_event_log`: Demonstrate deterministic journals, event logs, receipts, and audit metadata.
- `example_06_strategy_adapter`: Demonstrate strategy signal ingestion, risk/trading boundaries, and blocked broker mutation.
- `example_07_metrics_and_reports`: Demonstrate simulation summary, equity curve, drawdown, trade stats, and artifact references.
- `example_08_resume_cancel_and_resource_limits`: Demonstrate progress, cancellation, resume safety, quotas, and fail-closed invalid input paths.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 1,662 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(simulation-engine): implement phase 8 simulation engine requirements
```


- [ ] The same configuration, data, and seed shall produce the same metrics.
- [ ] Diagnostic mode may continue only far enough to emit bounded diagnostics, partial artifacts, failed invariant details, and safe remediation hints.
- [ ] Importing public simulation modules shall not start workers, open network connections, read secrets, write artifacts, register global mutable state, access market data, contact brokers, or launch background schedulers.
- [ ] Production run-configuration artifacts shall be signed or checksum-verified and shall be the single source of truth for replay.
- [ ] Synthetic transaction probes shall alert when the canonical simulation fails, produces non-deterministic output, violates expected metrics tolerance, or cannot produce required artifacts.
- [ ] Retention tier, deletion eligibility, and legal-hold status shall be stored in the artifact manifest.
- [ ] Protected artifacts shall be readable only by authorized roles and approved service identities.
- [ ] Phase 1 local-only research artifacts may remain unencrypted only when explicitly classified as local research, stored outside protected artifact roots, and excluded from production-candidate evidence.
- [ ] Production artifacts shall record git commit, dependency lock hash, container image digest when applicable, build timestamp, builder identity, and release signature.
- [ ] Official release artifacts shall be signed or checksum-verified before deployment.
- [ ] `artifact_root_ref` shall resolve through an allowlisted root or registry entry, not an arbitrary filesystem path.
- [ ] Distributed work units shall pull inputs from and write outputs to a shared versioned artifact store; local worker disk shall never be the sole source of truth for shared artifacts.
- [ ] Failed runs shall return the same envelope with `status=failed`, deterministic error code, safe error message, and any completed diagnostic artifacts.
- [ ] Calibration artifacts shall be immutable once attached to a production-candidate run.
- [ ] Vendor data changes after a completed production run shall not mutate historical run artifacts.
- [ ] Promotion manifests shall be retained with the release artifacts they approve.
- [ ] Artifact path attempts directory traversal or resolves outside allowlisted roots.
- [ ] Artifact store is unavailable before run start.
- [ ] External dependency timeout occurs during data manifest, broker profile, artifact store, secrets-provider, scheduler, worker heartbeat, or optional service access.
- [ ] Fault-injection tests shall verify `SIM_PERSISTENCE_FAILED` is returned, the run halts cleanly, the last committed JSONL sequence remains recoverable, and corrupted partial artifacts are not promoted.
- [ ] Secure-SDLC tests shall cover dependency lock validation, SBOM generation, vulnerability scan evidence, secret scan evidence, release artifact checksums, and release signatures where enabled.
- [ ] Observability tests shall cover trace context propagation, required pipeline spans, business metrics export, SLO burn-rate alert inputs, and predictive alert rule configuration where supported.
- [ ] Vendor-governance tests shall cover vendor inventory records, license conflicts, point-in-time snapshot requirements, vendor restatement policy, and immutable historical artifacts.
- [ ] Retention and redaction tests shall cover retention tiers, legal-hold metadata, artifact checksums, disallowed secret fields, pseudonymized actors, and protected artifact access.
- [ ] Dependency lock, SBOM, vulnerability scan, secret scan, static security analysis, and artifact checksum checks shall pass before production release workflows are enabled.
- [ ] `diagnostic_failed` envelope example showing bounded diagnostics, warnings, safe error details, artifacts, and non-promotable classification.
- [ ] Poison-pill policy for repeated work-unit failure thresholds, quarantine behavior, alert routing, and diagnostic artifact retention.
- [ ] Observability configuration for tracing, metrics export, SLO thresholds, synthetic probes, canary analysis, and alert routing.
- [ ] Immutable run-configuration artifact for production runs.
- [ ] Required artifact retention tier for every official run.
- [ ] Realism-disclosure summary.
- [ ] Benchmark-relative metrics when benchmark data is provided.
- [ ] Walk-forward in-sample and out-of-sample metrics when enabled.
- [ ] Immutable run-configuration artifact and checksum or signature.
- [ ] OpenTelemetry trace identifiers and business-metric export metadata when observability is enabled.
- [ ] Documentation shall include retention, redaction, and protected-artifact operating procedures.
- [ ] Documentation shall include observability metrics, alerting expectations, SLOs, and operational runbooks.
- [ ] Documentation shall include OpenTelemetry tracing, business metrics, predictive alerting, synthetic transaction monitoring, and canary analysis procedures.
- [ ] Documentation shall include secure-SDLC and software supply-chain procedures, including SBOM, dependency scanning, secret scanning, release signing, and artifact checksum verification.
## Phase 9 Optimization Service

### Goal

Implement the Optimization Service requirements under `app/services/optimization/` while preserving the phase module boundaries and governance rules.

Task inventory: 278 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/optimization/`.
- Requires Phase 8 Simulation Engine contracts to be available where referenced by `09_optimization.md`.

### Files to Create

```text
app/services/optimization/
app/__init__.py
app/services/optimization/__init__.py
app/services/optimization/sweeps.py
app/services/optimization/robustness.py
app/services/optimization/splitting.py
app/services/optimization/scoring.py
app/services/optimization/algorithms/__init__.py
app/services/optimization/algorithms/grid.py
app/services/optimization/algorithms/random.py
app/services/optimization/algorithms/bayesian.py
app/services/optimization/algorithms/genetic.py
app/services/optimization/persistence/__init__.py
app/services/optimization/persistence/checkpoint.py
app/services/optimization/persistence/repository.py
app/services/optimization/helpers.py
app/services/optimization/models.py
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/__init__.py`

Functions/classes:
- `strategy_id`
- `Infinity`
- `OPT_JSON_SERIALIZATION_FAILED`

Requirements:
- [ ] Optimization workflows shall record reproducibility context including `strategy_id`, parameter-space definition including constraints, objective, data window start/end, engine type, engine version, seed, cost model hash, simulator realism profile hash, module version, parameter-space hash, candidate hashes, and all candidate results required to reproduce ranking and report outputs.
- [ ] The module shall validate optimization requests, strategy compatibility, market data quality, parameter spaces, objective definitions, and evidence-package shape before running expensive work or persisting artifacts.
- [ ] `parametric_simulation` shall simulate outcomes from win rate, reward/risk ratio, risk per trade, trade count, simulation count, and initial balance.
- [ ] `parameter_space_hash` shall be order-invariant, shall sort dictionary keys, shall canonicalize parameter definitions, and shall include constraints after canonical sorting and normalization.
- [ ] The module shall perform no broker, database, network, multiprocessing, or heavy dependency initialization at import time.
- [ ] Timeout enforcement shall use a monotonic clock source such as `time.monotonic()` or `time.perf_counter()` so NTP adjustments or wall-clock changes cannot cause premature timeout or infinite hangs.
- [ ] Public result payloads shall be JSON-safe before envelope return. `NaN`, `Infinity`, and `-Infinity` shall serialize as `null` with a warning; `datetime` values shall serialize as UTC ISO-8601 strings; `Decimal` values shall serialize as normalized strings unless a schema declares a numeric representation; unsupported objects shall fail closed with `OPT_JSON_SERIALIZATION_FAILED`.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/optimization/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/optimization/sweeps.py`

Functions/classes:
- `ParameterSpace`
- `ParameterCandidate`
- `SweepResult`
- `grid_search`
- `random_search`
- `run_parameter_sweep`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Parameter spaces, iteration counts, population sizes, bootstrap counts, simulation counts, and worker counts must be bounded before production use.
- [ ] Optimization outputs shall include objective, executable parameters, candidate score, data slice, algorithm name and version, seed, engine type and version, cost model hash, simulator realism profile hash, parameter-space hash, candidate hash, warnings, and caveats.
- [ ] Metrics shall include request count, validation failures, runtime failures, resource-cap rejections, execution duration, queue time, candidate count, and cancellation count.
- [ ] Repeated deterministic runs with the same inputs shall produce the same candidate ordering, same candidate hashes, same parameter-space hash, and same evidence when backtest execution is deterministic.
- [ ] Request-packaging tools shall not trigger candidate execution, persistence writes, external network calls, or background jobs unless explicitly documented and approved.
- [ ] The module shall support float, integer, categorical, boolean, fixed, conditional, and constrained parameter spaces.
- [ ] Parameter constraints shall be evaluated before candidate execution, and unsafe constraint expressions shall be blocked.
- [ ] Final optimization output states shall use the canonical enum `ready_for_risk_review`, `validation_needed`, `research_only`, `rejected`, `failed`, or `cancelled`; all requirements, schemas, tests, examples, and reports shall use these exact values.
- [ ] `compare_optimization_runs` shall package candidate optimization run IDs or result payloads for comparison.
- [ ] `calculate_parameter_stability` shall calculate standard-deviation-style stability by parameter across selected candidates.
- [ ] `detect_overfit_parameters` shall detect overfit risk from the gap between in-sample and out-of-sample scores.
- [ ] `rank_parameter_sets` shall rank optimization parameter candidates deterministically from highest score to lowest score.
- [ ] `rank_parameter_sets` tie-breaking shall sort tied scores by `trade_count` descending when available, then by `candidate_hash` ascending; missing `trade_count` shall sort after present `trade_count` for the same score.
- [ ] Search methods shall return optimization summaries containing candidate results, best parameters, best score, objective, runtime, and total-run metadata.
- [ ] `walk_forward` shall optimize parameters on rolling training windows and test them on out-of-sample windows.
- [ ] `optimization_walk_forward` shall expose a user-facing wrapper around walk-forward parameter optimization.
- [ ] `print_optimization_report` shall print or format a top-candidate optimization report for inspection.
- [ ] Walk-forward results shall preserve train window, test window, selected parameters, train score, test score, and degradation context.
- [ ] Walk-forward evidence shall include fold results, best parameters per fold, OOS results per fold, fold pass rate, parameter drift score, OOS retention score, walk-forward score, Walk-Forward Efficiency, and walk-forward status.
- [ ] `parallel_walk_forward` shall run walk-forward optimization across windows and/or candidates in parallel.
- [ ] Pruned candidates shall remain persisted with partial evidence, including prune reason, prune phase, intermediate metric snapshot, backend name, and retryable flag.
- [ ] `run_optimization_task` shall coordinate a background parameter optimization run and report progress.
- [ ] Candidate cache entries shall be invalidated automatically when strategy hash, data hash, cost model hash, simulator realism profile hash, objective hash, engine type, module version, or parameter-space hash changes.
- [ ] `candidate_hash` shall be the source of truth for candidate deduplication and shall deterministically combine strategy hash, data hash, cost model hash, simulator realism profile hash, objective hash, engine type, module version, and canonicalized sorted executable parameter values.
- [ ] `candidate_hash` shall exclude inactive conditional parameters and shall use canonical JSON with sorted keys and normalized decimals.
#### `app/services/optimization/robustness.py`

Functions/classes:
- `calculate_robustness_score`
- `RobustnessRequest`
- `RobustnessStats`
- `RobustnessResponse`

Requirements:
- [ ] Optimization workflows must warn about overfitting, parameter instability, and robustness weaknesses instead of presenting candidate scores as live readiness.
- [ ] Risk Governor handoff packages shall include the full evidence package, final decision, best candidate, top candidates, rejected-candidate summary, production gates, walk-forward evidence, robustness evidence, Monte Carlo evidence, prop-firm compliance evidence, warnings, audit references, and institutional evidence fields.
- [ ] `run_spread_stress_test` shall package wider-spread stress-test inputs.
- [ ] `run_slippage_stress_test` shall package slippage stress-test inputs.
- [ ] `run_commission_stress_test` shall package commission stress-test inputs.
- [ ] `run_randomize_trade_order_mc` shall package shuffled-trade-order Monte Carlo inputs.
- [ ] `run_resample_trades_mc` shall package resampled-trade Monte Carlo inputs.
- [ ] `run_skip_trades_mc` shall package skipped-trade Monte Carlo inputs.
- [ ] `run_randomize_parameters_mc` shall package randomized-parameter Monte Carlo inputs.
- [ ] `run_randomize_history_mc` shall package randomized-history Monte Carlo inputs.
- [ ] `run_combined_monte_carlo` shall package combined Monte Carlo stress inputs.
- [ ] `run_cross_market_test` shall package cross-market robustness-test inputs.
- [ ] `run_cross_timeframe_test` shall package cross-timeframe robustness-test inputs.
- [ ] `run_second_oos_test` shall package second out-of-sample validation inputs.
- [ ] `run_third_oos_test` shall package third out-of-sample validation inputs.
- [ ] `calculate_robustness_score` shall calculate a deterministic robustness percentage from pass/fail checks.
- [ ] `build_robustness_report` shall package robustness report creation inputs.
- [ ] `assess_strategy_robustness` shall produce a comprehensive Monte Carlo robustness assessment.
- [ ] `robustness_simulation` shall simulate robustness with skipped trades, deterioration, and selected Monte Carlo mode.
- [ ] `optimization_monte_carlo` shall expose a user-facing wrapper around Monte Carlo robustness simulation over trade results.
- [ ] Candidate scoring shall support return, net profit, Sharpe, Sortino, Calmar, profit factor, expectancy, win rate, drawdown, trade count, exposure, turnover, cost-adjusted return, OOS retention, fold consistency, robustness survival, Monte Carlo p5 outcome, and prop-firm breach probability.
- [ ] `RobustnessRequest`, `RobustnessStats`, and `RobustnessResponse` shall model robustness simulation inputs and outputs.
- [ ] Evidence packages shall include best candidate, top candidates, rejected candidate summary, optimization summary, walk-forward evidence, parameter stability evidence, robustness evidence, Monte Carlo evidence, prop-firm compliance evidence, production gates, final decision, warnings, audit references, and visualization data.
- [ ] Chart-ready data shall support equity curves, drawdown curves, candidate scatter plots, parameter heatmaps, Pareto front, walk-forward fold results, Monte Carlo cone, final equity distribution, drawdown distribution, regime performance, robustness degradation, DSR versus raw Sharpe, topology visualization, capacity ladder, embargo table, and execution-realism stress table.
- [ ] The module shall support checkpointing after configured candidate intervals, state transitions, before long robustness or Monte Carlo phases, on cancellation, and on recoverable errors.
- [ ] Metrics and reports must not overstate live readiness or hide sample-size, out-of-sample, robustness, or overfit caveats.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] `bootstrap_simulation` shall use block bootstrap to preserve short-term temporal structure.
- [ ] `compare_simulation_methods` shall run multiple Monte Carlo methods and compare their results.
- [ ] `MonteCarloResult` shall hold Monte Carlo simulation outputs and provide summary/statistics behavior.
- [ ] Monte Carlo evidence shall include ruin probability, daily-loss breach probability, total-loss breach probability, profit-target probability, equity percentiles, drawdown percentiles, losing-streak distribution, and return distribution.
- [ ] `run_monte_carlo_task` shall coordinate a background Monte Carlo simulation run.
#### `app/services/optimization/splitting.py`

Functions/classes:
- `WalkForwardSplit`
- `chronological_split`
- `expanding_window_split`
- `rolling_window_split`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] `run_walk_forward_optimization` shall package rolling train/test walk-forward optimization details.
- [ ] `run_walk_forward_matrix` shall package a matrix of walk-forward train/test combinations.
- [ ] `splitter_from_rolling` shall create deterministic rolling time-series train/test windows.
- [ ] `splitter_from_expanding` shall create deterministic expanding time-series train/test windows.
- [ ] `splitter_rolling_split` shall split tabular data into rolling train/test or train/validation/test slices.
- [ ] `SplitterResult` shall hold split windows and support plotting/inspection behavior.
- [ ] Walk-forward validation shall support rolling, anchored, expanding, and custom fold modes.
- [ ] Walk-forward and cross-validation splits shall enforce configurable purging and embargo periods between training and validation sets when required.
- [ ] Evidence shall include embargo configuration, effective embargo bars, and leakage-prevention status for walk-forward and CPCV runs.
- [ ] `analyze_walk_forward_results` shall summarize walk-forward optimization results.
- [ ] `run_walk_forward_task` shall coordinate a background walk-forward analysis run and report progress.
#### `app/services/optimization/scoring.py`

Functions/classes:
- `OptimizationScore`
- `ScoringFunction`
- `evaluate_candidate_score`
- `rank_candidates`

Requirements:
- [ ] Inactive conditional parameters shall be excluded from executable candidate parameters, candidate hashes, backtest adapter payloads, scoring, and strategy invocation, while remaining available only in metadata or audit records.
- [ ] Search methods shall support objective/scoring functions, initial balance, symbol, engine type, max workers, verbosity, progress callbacks, and reproducibility controls where implemented.
- [ ] `sharpe_score` shall score results using Sharpe ratio.
- [ ] `sortino_score` shall score results using Sortino ratio.
- [ ] `calmar_score` shall score results using Calmar ratio.
- [ ] `profit_factor_score` shall score results using profit factor.
- [ ] `total_return_score` shall score results using total return percentage.
- [ ] `custom_score` shall calculate a weighted composite from return, Sharpe, and drawdown components.
- [ ] `optimization_get_scoring_func` shall resolve supported objective names to scoring functions.
- [ ] Scoring helpers shall handle missing metrics with deterministic fallback behavior.
- [ ] Candidate scoring shall support single-objective, weighted multi-objective, constraint-based, and Pareto-ready scoring.
- [ ] Pareto selection shall be deterministic and shall record fallback behavior for knee-point selection when used.
- [ ] Anti-overfitting gates shall evaluate in-sample versus out-of-sample degradation, walk-forward consistency, parameter neighborhood smoothness, top-candidate clustering, profit concentration, trade count adequacy, cost sensitivity, Monte Carlo survival, regime dependency, Deflated Sharpe Ratio, multiple-testing correction, topology stability, leakage prevention, and capacity degradation.
- [ ] Every scored candidate shall include raw Sharpe, deflated Sharpe, multiple-testing method, nominal or effective trial count metadata, Sharpe variance estimate, MTB pass status, and MTB rejection reason.
- [ ] `nominal_trial_count` shall be calculated from unique executable candidate hashes after canonical normalization, inactive conditional exclusion, constraint rejection, and cache deduplication.
- [ ] If topology-adjusted or effective-trial estimation is enabled, evidence shall include `effective_trial_count`, `trial_count_method`, and any required method metadata.
- [ ] Evidence shall include `trial_count_independence_warning` when nominal counts may overstate independence in highly correlated, Bayesian, exploitative, or highly constrained parameter spaces.
- [ ] `nominal_trial_count` shall not be presented as a statistically independent trial count unless the configured method explicitly supports that interpretation.
- [ ] PBO threshold enforcement shall remain blocked until the designated risk owner approves production, strict-capital, research-only, and exploratory-validation thresholds.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/optimization/algorithms/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/optimization/algorithms/grid.py`

Functions/classes:
- `run_parameter_sweep`

Requirements:
- [ ] `run_parameter_sweep` shall package a grid or random parameter search request for downstream optimization execution.
- [ ] `run_parameter_sweep` shall require `search_method` with approved values `grid`, `random`, `latin_hypercube`, or `sobol`; distribution-based methods shall include validated distribution definitions instead of grid-only parameter lists.
- [ ] `grid_search` shall evaluate an exhaustive parameter grid over a supplied strategy/backtest context.
- [ ] `optimization_grid_search` shall expose a user-facing wrapper for exhaustive parameter grid search.
- [ ] Grid expansion shall support `100,000+` combinations through strict iterator mode that yields one candidate at a time and never materializes the full Cartesian product in memory.
- [ ] Strict iterator mode shall stay within an owner-approved memory budget regardless of grid size; the budget value remains pending owner/architect approval.
- [ ] `parallel_grid_search` shall run parameter-grid candidate evaluations across multiple workers.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/optimization/algorithms/random.py`

Functions/classes:
- `ManualPairInput`
- `RandomWinRateRequest`
- `RandomWinRatePair`
- `DistributionStats`
- `RandomWinRateResult`
- `RandomWinRateResponse`

Requirements:
- [ ] `random_search` shall sample parameter combinations from distributions and evaluate candidates.
- [ ] `optimization_random_search` shall expose a user-facing wrapper for randomized parameter search.
- [ ] Seeded random search shall support pseudo-random, Sobol sequence, and Latin Hypercube sampling contracts.
- [ ] Pseudo-random sampling shall be the always-available deterministic fallback.
- [ ] `monte_carlo_analysis` shall run Monte Carlo analysis against a backtest result with selected simulation type and random seed.
- [ ] `shuffle_trades_simulation` shall randomize trade order while preserving individual trade outcomes.
- [ ] `random_win_rate_simulation` shall simulate trading with random win-rate/reward-risk pairs.
- [ ] Monte Carlo and scenario simulations shall support reproducibility controls and must not claim certainty from randomized outputs.
- [ ] Monte Carlo random number generation shall derive deterministic seeds from run seed, candidate ID, and phase-specific offsets.
- [ ] `parallel_random_search` shall run sampled parameter candidate evaluations across multiple workers.
- [ ] `ManualPairInput`, `RandomWinRateRequest`, `RandomWinRatePair`, `DistributionStats`, `RandomWinRateResult`, and `RandomWinRateResponse` shall model random win-rate simulation inputs and outputs.
- [ ] Random, Monte Carlo, Bayesian, and genetic workflows must support seed or random-state controls where practical.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/optimization/algorithms/bayesian.py`

Functions/classes:
- `bayesian_optimization`
- `optimization_bayesian`
- `BayesianOptimizationResult`

Requirements:
- [ ] `bayesian_optimization` shall run Gaussian-process-style Bayesian optimization over a parameter space.
- [ ] `optimization_bayesian` shall expose a user-facing wrapper for Bayesian parameter optimization.
- [ ] No file-specific non-functional requirements defined.
#### `app/services/optimization/algorithms/genetic.py`

Functions/classes:
- `genetic_algorithm`
- `optimization_genetic`
- `GeneticAlgorithmResult`

Requirements:
- [ ] `genetic_algorithm` shall evolve parameter candidates through population, selection, crossover, mutation, and elitism behavior.
- [ ] `optimization_genetic` shall expose a user-facing wrapper for genetic algorithm parameter optimization.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/optimization/persistence/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/optimization/persistence/checkpoint.py`

Functions/classes:
- `OPT_ATOMIC_WRITE_FAILED`
- `OPT_CHECKPOINT_CORRUPTED`
- `OPT_INTRADAY_RULE_DATA_UNAVAILABLE`
- `OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED`
- `OPT_TRIAL_COUNT_METHOD_UNSUPPORTED`
- `OPT_PRUNED_BY_HARD_GATE`
- `OPT_PBO_THRESHOLD_FAILED`
- `OPT_NOISY_OBJECTIVE_NOT_ALLOWED`
- `STOCHASTIC_REALISM_CONFLICT`

Requirements:
- [ ] The module shall write optimization runs, candidates, candidate results, checkpoints, evidence packages, and audit records only through an approved repository interface.
- [ ] Resume logic shall reject corrupted, partial, or schema-invalid checkpoint artifacts rather than silently resuming.
- [ ] If the latest checkpoint is corrupted but an earlier valid checkpoint exists, the run may resume from the earlier checkpoint with an audit warning.
- [ ] File-backed checkpoint and candidate-result writes shall use atomic rename semantics by writing to a uniquely named temporary file, flushing and fsyncing where supported, then replacing the target artifact.
- [ ] Atomic write failure shall produce a structured repository or checkpoint error with artifact type, temporary path reference, target path reference, run ID, and phase.
- [ ] Atomic write temporary files shall be created only under approved artifact directories and shall not be treated as valid evidence packages or checkpoints.
- [ ] File-backed checkpoint writes shall prevent path traversal through both temporary and final artifact paths.
- [ ] The module shall include `OPT_ATOMIC_WRITE_FAILED`, `OPT_CHECKPOINT_CORRUPTED`, `OPT_INTRADAY_RULE_DATA_UNAVAILABLE`, `OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED`, `OPT_TRIAL_COUNT_METHOD_UNSUPPORTED`, `OPT_PRUNED_BY_HARD_GATE`, `OPT_PBO_THRESHOLD_FAILED`, and `OPT_NOISY_OBJECTIVE_NOT_ALLOWED` with subtype `STOCHASTIC_REALISM_CONFLICT` where applicable.
- [ ] No file-specific non-functional requirements defined.
#### `app/services/optimization/persistence/repository.py`

Functions/classes:
- `OptimizationRepository`
- `OptimizationRunRecord`
- `save_optimization_run`
- `load_optimization_run`
- `update_optimization_progress`

Requirements:
- [ ] Execution-capable workflows shall require an approved execution profile with resource caps, timeout policy, repository policy, and safety gates.
- [ ] Repository-backed workflows shall be idempotent for repeated resume, cancel, and progress requests.
- [ ] Production implementation shall be blocked until owner-approved limits exist for max candidates, max parameter-space expansion, max runtime, max worker count, max Monte Carlo simulations, objective whitelist, repository backend, artifact root, report schema version, and resource override approver.
- [ ] Optional Optuna and scikit-optimize backends shall sit behind a stable optimizer backend interface and shall require dependency approval, version pinning, repository policy approval, and contract tests before production use.
- [ ] Future Ray, Dask, or Celery adapters shall remain deferred until repository idempotency, retry behavior, and resource accounting are production-mature.
- [ ] The module shall own repository contracts and payload schemas, but shall not own production database provisioning, migrations, credentials, or operations unless explicitly assigned by architecture decision.
- [ ] Concrete repository adapters shall be owned by the approved persistence layer unless explicitly assigned to this module by architecture decision.
- [ ] Repository implementations shall be passed into execution-capable workflows through Dependency Injection rather than imported or constructed by optimization core code.
- [ ] Repository backend support for in-memory fixtures, JSONL fixtures, SQLite, DuckDB/Parquet, PostgreSQL, or managed PostgreSQL-compatible databases shall require deployment-tier approval before production use.
- [ ] Proposed engineering baseline: repository writes over network-backed repositories should retry safe transient failures with exponential backoff up to `3` attempts before surfacing a persistent structured error.
- [ ] Candidate hash generation shall benchmark at `10,000 candidates/sec` locally for simple parameters, parameter validation shall benchmark at `5,000 candidates/sec` for simple numeric parameters, repository write throughput shall benchmark `1,000` candidate records, and resume scan shall benchmark `10,000` candidate hash checks.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Each execution-capable workflow shall enforce configured timeout, retry, cancellation, and backpressure policies.
- [ ] Parallel workflows must avoid race conditions in progress tracking and result aggregation.
- [ ] Persist/package tools must distinguish request packaging from actual durable storage.
- [ ] Dry-run behavior shall be defined per capability type: packaging tools return a validated request envelope without execution, background jobs, persistence writes, or external calls; lightweight calculation tools still perform the deterministic calculation but skip any logging, persistence, or external side-effect writes.
- [ ] Constraint violations shall be persisted or represented in audit-ready evidence and shall not be sent to the backtest adapter for execution.
- [ ] `ProgressTracker` shall track progress for parallel optimization work in a thread-safe manner.
- [ ] Background task entry points shall return a `task_id` and polling/progress reference, not block the calling thread until optimization completion.
#### `app/services/optimization/helpers.py`

Functions/classes:
- `load_strategy_from_path`
- `normalize_engine_type`
- `run_strategy_backtest`
- `run_strategy_backtest_from_path`
- `EngineOptimizationResult`
- `OptimizationExecutionError`
- `OPT_EXECUTION_FAILED`
- `OPT_STRATEGY_LOAD_FAILED`
- `OPT_ENGINE_CREATION_FAILED`
- `OPT_SYMBOL_SETUP_FAILED`
- `OPT_CANDIDATE_EXECUTION_FAILED`
- `OPT_NOISY_OBJECTIVE_NOT_ALLOWED`
- `STOCHASTIC_REALISM_CONFLICT`

Requirements:
- [ ] `service_strategy_class` shall normalize either a concrete strategy class or a callable strategy-class factory.
- [ ] `optimization_tool_result` shall build the standard HaruQuant optimization result envelope.
- [ ] `optimization_tool_context` shall extract request ID, agent name, environment, and dry-run context from tool keyword arguments.
- [ ] `optimization_business_payload` shall remove standard context fields and retain only business request fields.
- [ ] `package_optimization_request` shall create deterministic request packages without running compute-heavy optimization jobs.
- [ ] Lazy attribute resolution shall resolve lower-level optimization service attributes without putting business logic in the package initializer.
- [ ] `load_strategy_from_path` shall dynamically load a strategy class from a file path and class name.
- [ ] `normalize_engine_type` shall normalize legacy engine labels to supported execution engine names.
- [ ] `run_strategy_backtest` shall run one optimization candidate through the trading/backtest engine with supplied strategy, data, symbol, parameters, balance, engine type, and position size.
- [ ] `run_strategy_backtest_from_path` shall load a strategy class from disk and run one optimization candidate through the backtest path.
- [ ] `EngineOptimizationResult` shall expose a small optimization-facing result contract built from engine outputs.
- [ ] Execution helpers shall convert engine trades, equity points, processed tick counts, and analytics into optimization-ready result objects.
- [ ] Execution helpers shall return or raise structured `OptimizationExecutionError` results with deterministic `OPT_EXECUTION_FAILED`, `OPT_STRATEGY_LOAD_FAILED`, `OPT_ENGINE_CREATION_FAILED`, `OPT_SYMBOL_SETUP_FAILED`, or `OPT_CANDIDATE_EXECUTION_FAILED` codes when strategy loading, engine creation, symbol setup, or candidate execution fails.
- [ ] Candidate execution shall occur only through a versioned `BacktestExecutionAdapter`.
- [ ] The backtest adapter shall validate required data columns, strategy compatibility, cost model, engine type, deterministic seed behavior, and adapter version before execution.
- [ ] Backtest adapter version mismatch shall fail closed before execution.
- [ ] Unsupported simulator realism shocks shall return structured unsupported-feature errors and shall not be silently ignored.
- [ ] Deterministic-only noisy-objective mode shall fail closed with `OPT_NOISY_OBJECTIVE_NOT_ALLOWED` when stochastic simulator realism is active, and failure details shall include conflict subtype `STOCHASTIC_REALISM_CONFLICT`.
- [ ] Background tasks shall isolate database/progress-manager side effects from low-level deterministic optimization helpers.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Optimization behavior must be reproducible for the same inputs where deterministic algorithms are used.
- [ ] Proposed engineering baseline: public packaging responses should complete in `<= 200 ms` under owner-approved payload-size limits, subject to owner finalization and benchmark validation.
- [ ] Optimization must control compute load and warn about overfitting risks.
- [ ] Optimization must not mutate production strategy state without governance.
- [ ] Optimization must not place trades, call live brokers, or bypass risk/trading/live safety gates.
- [ ] Error responses must be structured, traceable, and safe for API/agent consumption.
- [ ] Optional lower-level dependencies shall either use a documented fallback or return a structured dependency error such as `OPT_SAMPLER_UNAVAILABLE`, `OPT_OPTIMIZER_BACKEND_UNAVAILABLE`, or `OPT_DEPENDENCY_UNAVAILABLE`; unhandled `ImportError` or backend-specific exceptions shall not cross public tool boundaries.
- [ ] Logs, traces, reports, and errors shall redact secrets, credentials, authorization headers, private trade payloads, sensitive file paths, and environment variables.
- [ ] Registry changes must remain covered by tests and catalog updates.
- [ ] Hashing shall use SHA-256 over canonical JSON with sorted keys and normalized decimals, with decimals quantized to eight decimal places by default unless field-specific precision is declared.
- [ ] Resource caps shall fail closed by default unless an explicitly approved override is present.
- [ ] Official optimization tools shall not possess live broker credentials, live broker gateway network access, or permission to place or close trades.
- [ ] Error codes shall use deterministic enum-style values and optimization-specific errors shall use the `OPT_` prefix. Custom optimization exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
- [ ] Each requirement shall include a stable requirement ID, priority, scope tier, owner, acceptance criteria, and one or more mapped tests before Builder handoff.
- [ ] Requirement priorities shall distinguish `P0 safety`, `P0 contract`, `P1 current public tool`, `P2 internal rebuild`, and `P3 future`.
- [ ] Confirmed requirements, assumptions, proposed decisions, pending decisions, and future improvements shall remain separated.
- [ ] The optimization registry must expose only intentional public service tools through `app.services.optimization.__all__`.
- [ ] The optimization registry must keep exports unique, callable, documented, and synchronized with tests and catalog entries.
- [ ] Public service tools that package work must not execute live broker actions or mutate production strategy state.
- [ ] When a caller omits `dry_run`, public optimization tools shall default to `dry_run=True`.
- [ ] Official optimization tools shall never place trades, close broker positions, access live broker gateways, or return `approved_for_live_trading`.
- [ ] Official optimization tools shall include side-effect metadata with `places_trade=False`.
- [ ] Portfolio Manager handoff packages shall include capacity estimates, exposure assumptions, cross-symbol validation, cross-timeframe validation, regime evidence, intended deployment AUM, estimated capacity in deployment base currency, and portfolio-impact warnings.
- [ ] UI/reporting handoff packages shall provide chart-ready data without requiring recomputation and shall not render charts inside this module.
- [ ] `build_optimization_report` shall package optimization report creation inputs for downstream reporting.
- [ ] Optional backend-specific objects shall not leak into official tool responses.
- [ ] CPCV validation shall support deterministic path generation when enabled and shall enforce purging and embargo on every path.
- [ ] `resample_returns_simulation` shall sample returns with replacement from the empirical return distribution.
- [ ] `calculate_confidence_intervals` shall calculate confidence intervals for selected metrics.
- [ ] `position_sizing_simulation` shall compare linear and compounding position-sizing equity curves.
- [ ] `consecutive_losing_simulation` shall simulate maximum consecutive losses for win-rate and reward/risk pairs.
- [ ] `profit_target_simulation` shall estimate probability of reaching a target balance.
- [ ] `multi_entry_simulation` shall simulate multi-entry strategy scenarios.
- [ ] Prop-firm compliance gates shall support max daily loss, max total loss, monthly target, best-day consistency, news restrictions, weekend restrictions, overnight restrictions, exposure limits, correlated exposure limits, and forbidden behavior flags.
- [ ] End-of-day-only prop-firm evaluation shall be allowed only when the specific versioned prop-firm profile explicitly permits it.
- [ ] `compare_parallel_speedup` shall compare optimization runtime across different worker counts.
- [ ] `get_optimal_n_jobs` shall recommend a worker count based on available CPU capacity.
- [ ] `estimate_completion_time` shall estimate total execution time from single-run time, run count, and worker count.
- [ ] The service layer shall depend on an `ExecutionOrchestrator` abstraction rather than direct multiprocessing.
- [ ] Local sequential and local multiprocessing orchestration shall preserve deterministic aggregation order and equivalent failure isolation.
- [ ] The `ExecutionOrchestrator` shall support backend-neutral early-stopping and pruning hooks.
- [ ] `pfo_from_optimize_func` shall periodically optimize portfolio allocation weights from a deterministic callback.
- [ ] `pfo_plot` shall package periodic allocation-weight data for inspection and may provide non-UI diagnostic serialization; UI chart rendering shall remain outside the Optimization module.
#### `app/services/optimization/models.py`

Functions/classes:
- `OptimizationResult`
- `UnsupervisedConfigRequest`
- `UnsupervisedRunSummary`
- `UnsupervisedAnalysisRequest`
- `ParameterRange`
- `OptimizationRequest`
- `OptimizationResponse`
- `OptimizationRunDetails`
- `OptimizationResultItem`
- `PositionSizingRequest`
- `WalkForwardRequest`
- `WalkForwardWindow`
- `WalkForwardResponse`
- `MonteCarloRequest`
- `ParametricMonteCarloRequest`
- `MonteCarloResponse`
- `ConsecutiveLosingRequest`
- `ConsecutiveLosingScenario`
- `ConsecutiveLosingResponse`
- `ProfitTargetRequest`
- `ProfitTargetResult`
- `ProfitTargetResponse`
- `MultiEntryRequest`
- `MultiEntryScenarioResult`
- `MultiEntryResponse`

Requirements:
- [ ] `OptimizationResult` shall represent one candidate optimization result with parameters, score, metrics, and metadata.
- [ ] `OptimizationSummary` shall represent an optimization run summary and expose top-N and dataframe conversion behavior.
- [ ] `UnsupervisedConfigRequest`, `UnsupervisedRunSummary`, and `UnsupervisedAnalysisRequest` shall model unsupervised-analysis configuration and output attached to optimization flows.
- [ ] `ParameterRange` shall model a named parameter range for optimization requests.
- [ ] `OptimizationRequest`, `OptimizationResponse`, `OptimizationRunDetails`, and `OptimizationResultItem` shall model optimization request, response, run detail, and result item payloads.
- [ ] `PositionSizingRequest` shall model position-sizing simulation requests.
- [ ] `WalkForwardRequest`, `WalkForwardWindow`, and `WalkForwardResponse` shall model walk-forward analysis inputs and outputs.
- [ ] `MonteCarloRequest`, `ParametricMonteCarloRequest`, and `MonteCarloResponse` shall model Monte Carlo inputs and outputs.
- [ ] `ConsecutiveLosingRequest`, `ConsecutiveLosingScenario`, and `ConsecutiveLosingResponse` shall model consecutive-loss simulation inputs and outputs.
- [ ] `ProfitTargetRequest`, `ProfitTargetResult`, and `ProfitTargetResponse` shall model profit-target simulation inputs and outputs.
- [ ] `MultiEntryRequest`, `MultiEntryScenarioResult`, and `MultiEntryResponse` shall model multi-entry simulation inputs and outputs.
- [ ] Evidence packages shall include institutional fields for raw Sharpe, Deflated Sharpe Ratio, multiple-testing method, purging and embargo data, leakage prevention status, parameter plateau score, isolation penalty, estimated capacity, simulator realism profiles, orchestrator backend, and resource quota.
- [ ] Evidence packages shall include advanced research fields for PBO, CPCV, sensitivity, noisy-objective handling, repeated score statistics, and compute cost when applicable.
- [ ] Capacity evidence shall include `deployment_base_currency`, `intended_deployment_aum`, and `estimated_capacity_in_base_currency`.
- [ ] Reports shall be generated from evidence without recomputation and shall include constraint violations, WFE summary, sampler policy, Pareto selection method, PBO when enabled, pruning/partial-evidence behavior, and production/research threshold context.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
### Unit Tests Required

```text
tests/unit/app/services/optimization/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/09_optimization.py
```

Usage examples must show:
- `example_01_parameter_space`: Demonstrate parameter definitions, conditional parameters, validation, and candidate hashing.
- `example_02_grid_and_random_search`: Demonstrate grid/random sweeps, scoring functions, reproducibility, and progress callbacks.
- `example_03_bayesian_optimization`: Demonstrate Bayesian search wrapper, candidate ranking, and failure metadata.
- `example_04_genetic_algorithm`: Demonstrate population initialization, selection, crossover, mutation, elitism, and result ranking.
- `example_05_walk_forward_splits`: Demonstrate chronological, rolling, and expanding splits without leakage.
- `example_06_robustness_and_monte_carlo`: Demonstrate robustness checks, Monte Carlo runs, sensitivity summaries, and uncertainty metadata.
- `example_07_repository_and_resume`: Demonstrate optimization run persistence, resume, cancel, and idempotent progress lookup.
- `example_08_evidence_package`: Demonstrate reproducible optimization evidence packages and advisory-only boundaries.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 278 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(optimization-service): implement phase 9 optimization service requirements
```


- [ ] Public service tools must not perform unbounded compute directly when their documented behavior is request packaging.
- [ ] Public request-packaging API responses shall complete within an approved latency budget.
- [ ] Proposed engineering baseline: execution-capable workflows should use a configurable default timeout of `30 minutes`, with overrides allowed only through approved resource profiles.
- [ ] Large request payloads shall be rejected before expensive validation or execution with `OPT_PAYLOAD_TOO_LARGE` when they exceed configured size limits.
- [ ] Generated reports, saved results, and logs must not expose secrets, credentials, broker tokens, private trade payloads, or authorization headers.
- [ ] Resource overrides shall include approver, reason, requested cap, approved cap, timestamp, request ID, and workflow trust context in audit metadata.
- [ ] Production signoff shall be blocked when required institutional evidence fields are missing or when performance benchmarks exceed configured limits without approved exception.
- [ ] Public service tools shall return the documented standard optimization envelope containing `tool_name`, `status`, `request_id`, `data`, `errors`, `warnings`, `audit`, and `side_effects`; unit tests shall verify conformance to this contract.
- [ ] Public service tools must include request/audit context including request ID, tool name, risk level, and approval requirement.
- [ ] Public service tools must preserve business request payloads separately from standard context fields.
- [ ] `dry_run` requested on a calculation-only public tool shall follow that tool contract and shall not change the calculation result except for side-effect metadata and audit context.
- [ ] Public service tools must surface validation and runtime errors in structured result fields rather than uncaught exceptions.
- [ ] Evidence package schemas shall be versioned and backward-compatible according to a documented compatibility policy.
- [ ] `save_optimization_result` shall package optimization result metadata for downstream storage.
- [ ] Sobol or Latin Hypercube unavailability shall be explicit and shall either return `OPT_SAMPLER_UNAVAILABLE` or use an approved configured fallback with sampler method, seed, scramble setting, fallback usage, and fallback reason recorded in evidence.
- [ ] If average trade duration is known, effective embargo shall be at least the average trade duration in bars unless a stricter value is configured.
- [ ] PBO shall be calculated when CPCV is enabled, and PBO above the configured threshold shall flag or reject overfit risk according to the workflow profile.
- [ ] `calculate_probability_of_ruin` shall estimate probability that drawdown exceeds the configured ruin threshold.
- [ ] `ParametricSimulationResult`, `PositionSizingResult`, `ConsecutiveLosingScenarioResult`, and `ProfitTargetScenarioResult` shall hold scenario-specific simulation results.
- [ ] Prop-firm profiles shall be versioned configuration profiles and shall define rule-evaluation frequency as one of `per_tick`, `per_bar_close`, `per_trade_event`, `session_close`, or `end_of_day`.
- [ ] Prop-firm compliance checks shall evaluate max daily loss, max exposure, and max correlated exposure at the configured intraday frequency when the selected profile requires intraday evidence.
- [ ] `analyze_parallel_results` shall convert parallel optimization results into tabular analysis output.
- [ ] Parallel processing must keep worker inputs serializable and preserve deterministic aggregation of results.
- [ ] `PortfolioOptimizerResult` shall hold periodic portfolio weights and non-UI inspection metadata.
## Phase 10 Live Runtime

### Goal

Implement the Live Runtime requirements under `app/services/live/` while preserving the phase module boundaries and governance rules.

Task inventory: 234 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/live/`.
- Requires Phase 9 Optimization Service contracts to be available where referenced by `10_live.md`.

### Files to Create

```text
app/services/live/
app/services/live/__init__.py
app/services/live/config.py
app/services/live/session.py
app/services/live/gates.py
app/services/live/executor.py
app/services/live/reconciliation.py
app/services/live/monitoring.py
app/services/live/errors.py
app/utils/errors.py
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/live/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] The module does not own broker adapter implementation or interface definition; it owns live readiness validation, response classification, and error-mapping requirements for approved broker adapters before live use.
- [ ] Each exported live tool contract shall reference the shared side-effect mode and retry-safety enumerations from Terminology And Data Definitions rather than redefining them.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Expose a registry of callable live tools through the live tool registry, with each callable live tool accepting a standard request envelope and returning a standard response envelope.
- [ ] Each exported live tool shall document whether it is public API, internal helper, or official callable tool.
- [ ] Live outputs shall be structured, traceable, redacted, and JSON-safe.
- [ ] Public registry changes shall remain covered by tests and catalog updates.
- [ ] The module does not own market-data ingestion, provider data normalization, or historical data storage.
- [ ] The module does not own durable database schema/migration ownership, but it shall define required persistence ports such as `LiveStateStore`, `AuditSink`, and `IdempotencyStore`, including exact method signatures, required fields, failure behavior, and schema-version compatibility expectations before Builder handoff.
- [ ] The module does not own the live action policy matrix unless a later governance decision assigns it to Live; until then, Live shall consume the approved matrix from the owning governance module.
- [ ] The module does not own API authentication, UI rendering, websocket connection management, or frontend workflow policy.
- [ ] The module does not provide financial advice, trading recommendations, or owner-approved live threshold decisions.
- [ ] The live action policy matrix shall define every action mentioned in this file before Builder handoff.
- [ ] Emergency fail-safe classification shall come only from the approved live action policy matrix.
- [ ] `build_trading_report(route="live")` shall package a live execution result report request without recomputing or fabricating execution evidence.
- [ ] Position manager shall maintain live position views used by trading decisions.
- [ ] Performance tests shall use approved values from this table or later owner-approved replacements.
- [ ] Shadow data feeds shall package production-like account, portfolio, market, and environment snapshots.
- [ ] Shadow comparison reports shall compare expected and realized fill/PnL outcomes.
- [ ] Callable/docstring tests shall cover every exported live service tool.
- [ ] Idempotency tests shall cover duplicate same-material, duplicate different-material, and simultaneous duplicate live requests.
- [ ] Requirement traceability tests shall map every functional `shall` requirement to at least one named test or explicitly approved deferral.
- [ ] Optional shadow expected-versus-realized PnL reporting can remain future work unless required before live launch.
- [ ] Proposed Decision: shadow expected-versus-realized PnL reporting should be accepted for production only after an owner-approved paper-trading validation window and correlation threshold are defined.
- [ ] UI/dashboard rendering and websocket connection management are strictly out of scope for Live. Live may emit structured JSON events for approved consumers; rendering, websocket transport, and dashboard orchestration belong to API/UI or other consumer modules.
- [ ] Snapshot cache behavior can remain future work unless required for live readiness or audit.
- [ ] Public registry and catalog updates shall be mandatory when live tools are added, renamed, or removed.
#### `app/services/live/config.py`

Functions/classes:
- `Config`
- `load_config`
- `validate_config`

Requirements:
- [ ] Live runtime configuration, including trading enablement flags, safety settings, notification settings, logging settings, state settings, and secret-reference resolution.
- [ ] Live notifications through configured safe channels without leaking secrets or private broker data.
- [ ] `retry_after_seconds` shall be present for `retry_after_reconciliation`, broker rate-limit, and configured retry-delay scenarios, and shall be `null` or omitted only when no retry delay is applicable.
- [ ] Validate live runtime configuration and resolve secret references without exposing secret values.
- [ ] Live runtime shall fail closed unless live mode is explicitly enabled by approved runtime configuration.
- [ ] The runtime must verify that its internal position/order view matches broker truth within configured `max_staleness_seconds` or narrower approved context-specific staleness thresholds before any broker mutation.
- [ ] Live configuration shall be validated at startup. Any invalid configured broker provider, strategy reference, trading setting, safety setting, notification route, logging setting, state setting, or secret reference shall prevent live trading until corrected.
- [ ] Live config parsing shall resolve only approved secret references, reject raw secret values where prohibited, and return structured validation errors without exposing secret values.
- [ ] Live secrets helpers shall resolve configured secret references without logging secret values.
- [ ] Notification adapter shall send live execution success/failure notifications through configured safe channels.
- [ ] Workflows exceeding configured `live_workflow_timeout_seconds` shall trigger a `WORKFLOW_TIMEOUT` incident.
- [ ] Live readiness stale thresholds shall be configurable per context type and shall be enforced deterministically.
- [ ] Live broker adapter calls shall have configured timeout limits and shall classify timeout as unknown outcome unless broker truth proves otherwise.
- [ ] No file-specific non-functional requirements defined.
- [ ] Live runtime tests with mocks shall cover config parsing, secret resolution, state manager, signal processor, trade executor, position manager, notifications, startup, shutdown, and safe recovery.
- [ ] Package kill-switch trigger, condition check, order-disable, mass-cancel, mass-close, event-record, re-enable-approval, and approval-cleared recovery requests.
- [ ] Broker communication security shall be enforced through an owner/architect-approved security profile before production broker mutation can be enabled.
- [ ] The approved broker communication security profile shall define minimum encrypted transport version, certificate validation or pinning requirements where supported, credential handling, adapter compliance evidence, and failure behavior.
- [ ] Live kill-switch enforcement, live order disablement, live mass-cancel/mass-close request packaging, re-enable approval, and approval-cleared recovery.
- [ ] Live runtime shall keep live broker mutations disabled by default unless explicitly enabled and governed.
- [ ] Live runtime shall run in package-only mode unless live broker mutation is explicitly enabled.
- [ ] `submit_order(route="live")` shall return a blocked result unless the canonical live route gate passes. If the gate passes and live mutation is disabled, it shall return a packaged-only submit request. If the gate passes and live mutation is enabled, it may call an approved broker adapter and shall record the resulting side-effect state.
- [ ] `require_reenable_approval` shall require approval before trading can be re-enabled.
- [ ] Broker communication security is a mandatory pre-production gate. Live shall not allow production broker mutation until the approved security profile defines encrypted transport, certificate validation requirements, credential handling, logging restrictions, and adapter compliance tests.
- [ ] Kill-switch tests shall cover global, strategy, symbol, disable orders, cancel all, close all, record event, require re-enable approval, and clear after approval.
- [ ] Broker communication security tests shall prove production mutation is blocked when the approved transport/security profile is missing, unsupported, or failed.
- [ ] Broker communication security is not a deferrable pending decision for production; production broker mutation shall remain disabled until the mandatory broker communication security profile is approved and enforced.
#### `app/services/live/session.py`

Functions/classes:
- `LiveSession`
- `LiveSessionStatus`
- `start_live_session`
- `stop_live_session`
- `recover_live_session`
- `get_live_session_status`

Requirements:
- [ ] Live session, live run, startup, shutdown, signal handling, recovery diagnostics, and runtime status/event emission for approved consumers.
- [ ] Start and stop live sessions safely.
- [ ] Live engine/session/run helpers shall orchestrate live runtime startup, shutdown, signal handling, and structured runtime status/event emission.
- [ ] Cost enforcement shall enforce per-request, workflow, and session cost budgets and record cost entries.
- [ ] Importing live modules shall not start broker sessions, start background workers, mutate state, or resolve raw secret values.
- [ ] Importing live modules shall not resolve secrets, open sockets, spawn threads, start async tasks, or initialize broker SDK sessions.
- [ ] No file-specific non-functional requirements defined.
- [ ] Cost enforcement tests shall cover per-request, workflow, session budget, before-send failure, and after-send incident behavior.
- [ ] Gate shared trading functions such as `submit_order`, `modify_order`, `cancel_order`, `close_position`, `modify_position`, `reduce_exposure`, `pause_strategy`, `resume_strategy`, `sync_positions`, `reconcile_state`, and `build_trading_report` when called with `route="live"`.
- [ ] Live runtime components shall support safe startup, safe shutdown, signal handling, and recovery diagnostics.
- [ ] Live runtime shall enforce bounded queue sizes or explicit rejection behavior under request overload.
- [ ] Live runtime shall serialize or otherwise safely coordinate conflicting actions for the same account, strategy, symbol, order, or position.
- [ ] Live runtime shall not overstate readiness or safety when context is partial or stale.
- [ ] Live runtime shall treat shared trading functions as the only live trading action surface.
- [ ] Live runtime shall classify unknown broker outcomes separately from broker rejections, validation rejections, and successful broker acknowledgements.
- [ ] A failed mandatory gate shall stop evaluation before any downstream gate that could mutate broker state, mutate durable state beyond audit-safe diagnostics, or consume external broker capacity.
- [ ] Live runtime shall enforce the live action policy matrix and shall return `LIVE_POLICY_UNDEFINED` for any live action missing from the matrix.
- [ ] `disable_new_orders` behavior shall be dictated by the live action policy matrix. The functional requirement is enforcement of the matrix, not self-classification by the runtime.
- [ ] Live runtime shall require valid approval context for each action classified as approval-required in the live action policy matrix.
- [ ] Live runtime shall reject approval context that is expired, revoked, not approved, outside action scope, outside account scope, outside strategy or symbol scope, or missing required audit metadata.
- [ ] `modify_position(route="live")` shall follow the canonical live route gate and shall preserve stop-loss or take-profit mutation scope, broker constraints, idempotency material, and side-effect mode.
- [ ] `pause_strategy(route="live")` and `resume_strategy(route="live")` shall be operational live controls only and shall not replace strategy lifecycle promotion or approval.
- [ ] Live shutdown shall stop accepting new live mutation requests before preserving state, flushing audit evidence, and reporting unresolved live work.
- [ ] Signal processor shall transform strategy signals into live trading candidates only through approved runtime checks.
- [ ] Live runtime shall define a concurrency coordination contract before Builder handoff.
- [ ] The coordination contract shall define lock acquisition timeout, stale lock recovery, conflict error code, idempotency interaction, and audit evidence.
- [ ] Live registry tests shall prove the approved live runtime and governance surface is exported intentionally.
- [ ] Live gate tests shall prove each gate returns deterministic pass/block/error results and that gate failures stop unsafe downstream actions.
- [ ] Concurrency tests shall cover simultaneous submit/cancel, close/reduce exposure, pause/resume, duplicate idempotency keys, and kill-switch racing with live submit.
- [ ] Import-time safety tests shall prove importing live modules performs no broker connection, mutation, background start, or raw secret logging.
- [ ] Live is an operational runtime around `route="live"` trading functions, not a separate implementation of order and position behavior.
- [ ] Dashboard/runtime helper orchestration can remain future work if the runtime can operate safely without dashboard hints.
#### `app/services/live/gates.py`

Functions/classes:
- `LiveGateDecision`
- `LiveGateResult`
- `evaluate_live_gate`
- `require_live_approval`
- `enforce_kill_switch_gate`

Requirements:
- [ ] Live-only approval gates for broker mutation, kill-switch action, pause, resume, exposure reduction, mass cancel, mass close, and recovery.
- [ ] Live runtime shall reject any direct live broker mutation that bypasses shared trading, risk, approval, idempotency, reconciliation, audit, or kill-switch gates.
- [ ] Live route gating shall evaluate gates in a deterministic order: live enablement, request schema validation, approval validation, risk decision validation, broker readiness, stale-context validation, idempotency validation, reconciliation authority validation, kill-switch validation, audit pre-recording, and broker adapter permission.
- [ ] Diagnostic-only gates may run after a mandatory gate failure only when the gate contract marks `diagnostic_after_failure=true`, `mutates_state=false`, `calls_broker=false`, and `requires_network=false`.
- [ ] Initially approved diagnostic-only gates are limited to local tool-contract metadata validation and local redaction validation; every other gate is mandatory until explicitly approved otherwise.
- [ ] When live broker mutation is enabled, live trading actions may call an approved broker adapter only after all mandatory live gates pass.
- [ ] `trigger_global_kill_switch` shall package global trading kill-switch activation only after approval gates unless explicitly classified as an emergency fail-safe action.
- [ ] `trigger_strategy_kill_switch` shall package strategy-level kill-switch activation only after approval gates unless explicitly classified as an emergency fail-safe action.
- [ ] `trigger_symbol_kill_switch` shall package symbol-level kill-switch activation only after approval gates unless explicitly classified as an emergency fail-safe action.
- [ ] `cancel_all_orders` shall package cancellation of all pending orders only after approval gates.
- [ ] `close_all_positions` shall package closing all positions only after approval gates.
- [ ] `clear_kill_switch_after_approval` shall package kill-switch clearing only after approval gates.
- [ ] No file-specific non-functional requirements defined.
- [ ] Diagnostic-only gate tests shall prove only approved local diagnostic gates run after mandatory gate failure and that they do not mutate state, call broker adapters, or require network access.
- [ ] Mutation-enabled tests with mocks shall prove adapter calls occur only after all mandatory gates pass.
- [ ] Each exported live tool shall define a stable public contract including tool name, purpose, input schema, output schema, approval requirement, side-effect classification, risk level, error codes, warning codes, audit metadata, idempotency behavior, and stability status.
- [ ] Monitor live stale state, ingestion, tool health, workflow timeout, operational status, incidents, cost, latency, and notification outcomes.
- [ ] Critical live and kill-switch actions shall require explicit approval context unless classified as emergency fail-safe actions by the approved live action policy matrix.
- [ ] Live tools shall preserve clear side-effect flags and approval requirements.
- [ ] Compensation behavior shall be allowed only for approved compensation action classes. Each compensation action shall define preconditions, maximum scope, approval requirement, timeout, audit evidence, retry policy, and terminal failure behavior.
- [ ] The Live module shall act as a strict middleware/gateway for live-route requests and shall not implement strategy, risk, approval, broker, UI, or business-policy logic.
- [ ] Live gate decision records for every live-route request, including gate inputs, gate outcomes, final decision, side-effect mode, and audit reference.
- [ ] The module does not own strategy signal generation, strategy lifecycle promotion, or strategy approval.
- [ ] The module does not own risk policy, position sizing approval, exposure limits, portfolio allocation policy, or kill-switch policy ownership outside live enforcement.
- [ ] The module does not own strategy selection, financial advice, risk-policy creation, approval-policy creation, or broker-adapter policy decisions.
- [ ] The module does not own approval policy creation, but it shall validate approval context against the approved approval-policy contract.
- [ ] Each gate failure shall return a standard error code, human-readable operator message, request ID, correlation ID, failed gate name, retry-safety classification, and audit metadata.
- [ ] Live gate decision records shall persist the requested action, gate order, gate inputs by reference, gate outcomes, final decision, side-effect mode, and audit reference when persistence is available.
- [ ] Package-only success shall not be treated as broker acceptance, live readiness, risk approval, or execution evidence.
- [ ] Each live action policy entry shall define action name, owning module, required permissions, approval requirement, emergency fail-safe eligibility, idempotency requirement, required audit events, side-effect ceiling, retry-safety default, and operator-review requirement.
- [ ] Approval context shall include approval ID, approved action type, approved account scope, strategy scope where applicable, symbol scope where applicable, risk decision reference where applicable, approver identity reference, approval timestamp, expiration timestamp, approval state, and audit metadata.
- [ ] Approval expiry between gate evaluation and broker send shall block mutation or produce an unknown/incident state only if a broker send already occurred.
- [ ] `modify_order(route="live")` shall follow the canonical live route gate and shall preserve order identity, approved mutation scope, idempotency material, and side-effect mode.
- [ ] `cancel_order(route="live")` shall follow the canonical live route gate and shall preserve order identity, cancel reason, idempotency material, and side-effect mode.
- [ ] `close_position(route="live")` shall follow the canonical live route gate and shall preserve position identity, close scope, risk/approval references, idempotency material, and side-effect mode.
- [ ] `reduce_exposure(route="live")` shall follow the canonical live route gate and shall preserve the approved reduction scope, position/symbol/account scope, idempotency material, and side-effect mode.
- [ ] Kill-switch trigger tools shall consume emergency fail-safe classification only from the approved live action policy matrix and shall not infer emergency status from request text, user role, chat instruction, UI input, or API route.
- [ ] `check_kill_switch_conditions` shall package kill-switch trigger-condition evaluation.
- [ ] `record_kill_switch_event` shall package durable kill-switch event recording.
- [ ] Active kill switch shall block live trading requests regardless of route request text, UI input, API input, or chat instruction.
- [ ] Broker adapter readiness shall fail closed on unsupported API version, deprecated endpoint use, missing capability declaration, stale symbol metadata, missing account snapshot, or incompatible response schema version.
- [ ] Shadow execution shall not be treated as live broker approval or live readiness by itself.
- [ ] Contract tests shall cover every exported public tool input schema, result-envelope schema, risk level, approval requirement, side-effect flag, stability, and documentation reference.
- [ ] Critical live-route tests shall prove shared trading functions block without approval ID when approval is required.
- [ ] Policy matrix consistency tests shall prove every action mentioned in functional requirements has a defined matrix entry with approval class, emergency flag, idempotency requirement, side-effect ceiling, and audit requirement.
- [ ] Approval context tests shall reject expired, revoked, out-of-scope, malformed, missing-audit, and wrong-action approvals.
- [ ] Approval packet completeness, state-machine, creation, voting, override, and distinct-approver tests shall cover live governance only after ownership is approved by the governance module.
- [ ] Usage-example tests shall prove examples remain executable against documented signatures and include blocked live mode, missing approval, active kill switch, package-only mode, and unknown outcome.
#### `app/services/live/executor.py`

Functions/classes:
- `LiveTradeExecutor`
- `execute_live_order_intent`
- `validate_live_execution_request`

Requirements:
- [ ] Trade executor shall enforce live execution safety checks before broker mutation.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Evaluate live readiness before `route="live"` trading functions can mutate broker state.
- [ ] Support shadow execution and expected-versus-realized reporting without real broker mutation.
- [ ] Live mutations shall be disabled by default.
- [ ] Broker calls shall be isolated behind approved adapters or bridges.
- [ ] Raw broker payloads shall be stored only as redacted evidence references unless explicitly classified safe.
- [ ] Idempotency shall prevent unsafe duplicate live execution and shall not be mistaken for exactly-once broker semantics.
- [ ] Paper, simulation, and shadow trading shall remain separate from live broker mutation.
- [ ] Live side-effect state classification for each request: no side effect, packaged only, broker mutation attempted, broker mutation accepted, broker mutation rejected, unknown outcome, reconciled, or incident.
- [ ] Live broker readiness and broker-truth synchronization before live mutation.
- [ ] Live performance reports, live execution reports, broker-truth snapshots, and live audit evidence.
- [ ] Live-compatible shadow execution and production-like comparison reports when real broker mutation is disabled.
- [ ] The module does not grant AI chat, UI, API, backtest, or optimization workflows authority to execute live broker mutations.
- [ ] Audit pre-event evidence shall be recorded before broker mutation and audit post-event evidence after broker response, rejection, timeout, or unknown outcome.
- [ ] Audit-write failure before broker mutation shall always block broker mutation.
- [ ] Broker readiness shall include broker API/version compatibility checks once the broker adapter contract is approved.
- [ ] When live broker mutation is disabled, live trading actions shall only package validated broker-mutation requests or return structured blocks and shall not call any broker adapter.
- [ ] Every live result envelope shall include `side_effect_mode` with one of `none`, `packaged_only`, `broker_mutation_attempted`, `broker_mutation_confirmed`, `broker_mutation_rejected`, `unknown_outcome`, or `incident`.
- [ ] `sync_positions(route="live")` shall package live position synchronization from broker state and shall not mutate broker orders or positions.
- [ ] `disable_new_orders` shall package or perform disabling new order submission according to the live action policy matrix.
- [ ] Each approved broker adapter shall expose a documented capability contract before Live can use it for broker mutation.
- [ ] Broker adapter contracts shall define provider ID, API/version compatibility, supported actions, symbol metadata access, account/order/position snapshot access, readiness checks, request schema, response schema, timeout behavior, rate-limit behavior, malformed-response handling, error mapping, retry-safety classification, and redaction rules.
- [ ] Broker-side rate limiting, including HTTP 429 or provider-equivalent rate-limit responses, shall not be retried blindly.
- [ ] Broker rate-limit responses shall include `retry_after_seconds` when the provider supplies or the approved rate-limit policy derives a retry delay.
- [ ] Broker rate-limit backoff policy shall be approved before production live mutation. Proposed Decision: exponential backoff with jitter and at most three attempts before incident escalation.
- [ ] The concurrency coordination contract shall specify whether coordination uses per-account locks, per-symbol locks, per-order/position locks, optimistic version checks, or another approved mechanism.
- [ ] Conflicting actions for the same account, strategy, symbol, order, or position shall be serialized, rejected with a deterministic conflict error, or coordinated through an approved optimistic concurrency rule.
- [ ] Production live broker mutation is strictly blocked until all `Proposed Decision` statuses in this table are updated to `Decision: Approved` by the owner/architect or replaced by approved values.
- [ ] Shadow execution shall execute production-like workflows without real broker mutation.
- [ ] Shadow execution shall fail closed if it receives a live account reference or live broker adapter reference.
- [ ] Standard-envelope snapshot tests shall cover success, blocked, rejected, packaged-only, mutation-attempted, mutation-confirmed, unknown-outcome, and incident states.
- [ ] Package-only tests shall prove no broker adapter call occurs when live mutation is disabled.
- [ ] Broker bridge tests shall cover approved broker adapters, response classification, error mapping, timeout mapping, and fail-closed live behavior.
- [ ] Broker adapter contract tests shall cover capability discovery, readiness, API/version compatibility, malformed success responses, response schema validation, error mapping, and retry-safety classification.
- [ ] Broker rate-limit tests shall cover HTTP 429 or provider-equivalent responses, `retry_after_seconds`, retry-safety classification, approved backoff limits, and incident escalation after backoff exhaustion.
- [ ] Shadow execution tests shall cover feed building, no-live-mutation execution, live-reference rejection, and expected-versus-realized reporting.
- [ ] Compensation tests shall cover order, position, registry, validation, execution, missing-plan, and audit-log behavior after compensation ownership is approved.
- [ ] Production live broker mutation shall remain disabled until the decisions above are approved and referenced by version.
#### `app/services/live/reconciliation.py`

Functions/classes:
- `reconcile_state(route="live")`
- `reconcile_state()`

Requirements:
- [ ] The Live module shall be consumed only by approved shared trading tools, live runtime orchestration, operator workflows, monitoring, reconciliation, audit, and reporting consumers.
- [ ] Live reconciliation authority state, startup reconciliation, retry guard, unknown-outcome handling, and live discrepancy incidents.
- [ ] Live state management for positions, orders, broker receipts, reconciliation status, run status, incidents, and recovery context.
- [ ] The module does not own shared order, position, validation, route, bridge, receipt, simulator, or reconciliation function contracts; those belong to `07_trading.md`.
- [ ] Package live submit, cancel, modify, close, pause, resume, reduce exposure, position sync, broker reconciliation, and live report requests through shared trading contracts.
- [ ] Produce live execution, reconciliation, incident, and performance reports with audit evidence.
- [ ] Live runtime shall propagate, log, and persist request ID, correlation ID, approval ID, risk decision reference, idempotency material, broker provider, route, account, strategy, symbol, and audit metadata through every gate, package, broker-attempt, reconciliation, and report boundary.
- [ ] Live runtime shall return structured rejections or blocks for invalid orders, disabled live mode, unsupported broker, failed readiness checks, stale context, active kill switch, reconciliation mismatch, missing approval, or unsafe live conditions.
- [ ] `reconcile_state(route="live")` shall package reconciliation of internal state against broker truth and shall record mismatch, unknown-outcome, and incident states.
- [ ] Live startup shall run broker readiness and startup reconciliation before live recovery or live mutation workflows.
- [ ] Live startup shall not permit live mutation until startup reconciliation completes successfully or produces an approved operator-cleared recovery state.
- [ ] Broker-truth snapshots shall normalize broker positions, orders, account, and timestamp evidence.
- [ ] Live reconciliation comparison shall detect missing, extra, mismatched, and stale broker/internal records.
- [ ] Live reconciliation persistence shall preserve reconciliation runs, mismatches, incidents, and evidence references through the approved persistence interface.
- [ ] Live authority-state transitions shall remain pending until the reconciliation state machine is approved; until then, production live broker mutation shall remain disabled.
- [ ] Startup reconciliation shall run before live recovery or live mutation workflows.
- [ ] Retry guard behavior shall prevent unsafe blind retries after unknown broker outcomes.
- [ ] Unknown broker outcomes shall block blind retry until broker truth resolves the live authority state.
- [ ] Live reconciliation incidents shall package discrepancy severity, evidence, action requirement, and audit context.
- [ ] Reconciliation shall prefer broker truth when determining live authority state.
- [ ] Live runtime shall persist idempotency records before any broker mutation attempt where persistence is available and shall fail closed if required idempotency persistence cannot be written.
- [ ] Malformed broker success responses, including HTTP 200 or equivalent success status with missing required fields or invalid data types, shall be classified as `unknown_outcome`, shall trigger reconciliation, and shall not be treated as confirmed broker mutation.
- [ ] Broker rate-limit responses shall return `retry_safety="safe_to_retry"` only when the adapter contract proves no broker mutation occurred; otherwise they shall return `retry_safety="retry_after_reconciliation"` or `do_not_retry`.
- [ ] Live runtime shall record an incident when cost budget is exceeded after broker send but before reconciliation completion.
- [ ] Live reports shall include approvals, risk decisions, route, broker evidence, receipts, reconciliation state, incidents, warnings, and unresolved actions.
- [ ] Live shall fail closed on missing approval, missing risk context, stale broker/account state, active kill switch, reconciliation mismatch, idempotency conflict, disabled live flag, or unknown broker result.
- [ ] Unknown broker outcomes shall block blind retries until reconciliation resolves state.
- [ ] Reconciliation shall prefer broker truth when determining live authority state.
- [ ] No file-specific non-functional requirements defined.
- [ ] Live execution tests with mocks shall prove submit, modify, cancel, close, pause, resume, exposure reduction, sync, reconciliation, and reports require approval and fail closed when context is missing.
- [ ] Reconciliation tests shall cover matched, missing, extra, mismatched, stale, unknown-outcome, startup, persistence, retry guard, restart recovery, and incident paths.
- [ ] Restart tests shall cover persisted unknown outcomes, in-flight approvals, in-flight reconciliation, pending compensation, and startup mismatch blocking.
- [ ] Performance and reliability tests shall cover readiness latency budget, reconciliation timeout, broker adapter timeout, bounded queue behavior, shutdown audit flush, and monitoring signal emission.
- [ ] Performance tests shall include approved concrete targets, including readiness latency, gate latency, reconciliation loop interval, adapter timeout, request throughput, queue-depth rejection, and shutdown audit flush once the owner approves those values.
- [ ] Chaos/network partition tests shall prove the runtime fails closed and records incidents when broker connection, audit sink, receipt read, or reconciliation persistence fails mid-mutation.
- [ ] Unknown-outcome retry tests shall prove clients receive `retry_after_reconciliation` and cannot blindly retry before reconciliation.
#### `app/services/live/monitoring.py`

Functions/classes:
- `LiveMonitor`
- `LiveHealthSnapshot`
- `check_live_readiness`
- `record_live_incident`
- `emit_live_monitoring_event`

Requirements:
- [ ] Live monitoring for stale state, ingestion health, tool health, workflow timeout, operational incidents, latency, cost, notification failures, and live readiness.
- [ ] Live state manager shall preserve runtime state needed for live execution recovery and monitoring.
- [ ] Tool health monitoring shall track last successful call time, last failure time, consecutive failure count, timeout count, dependency status, and current health state for each exported live tool.
- [ ] Workflow timeout monitoring shall detect stale or overdue live workflows.
- [ ] Stale-state monitoring shall identify stale market, account, broker, approval, or risk state.
- [ ] Stale-state monitoring shall tie broker/account/order/position freshness checks to approved market-data freshness thresholds where broker mutation depends on current market state.
- [ ] Ingestion monitoring shall track whether required live inputs are arriving.
- [ ] Incident classification shall classify live incidents by severity and action need.
- [ ] Latency helpers shall record live trading timing and latency diagnostics.
- [ ] Snapshot caches shall preserve recent live performance snapshots.
- [ ] Live runtime shall prevent broker mutation when cost budget is exceeded before broker send.
- [ ] If cost budget is exceeded after gate approval but before broker send, the runtime shall block mutation and record a cost-budget incident.
- [ ] Monitoring shall expose stale state, timeouts, health failures, incidents, latency, and cost-budget conditions.
- [ ] No file-specific non-functional requirements defined.
- [ ] Monitoring tests shall cover stale state, ingestion health, workflow timeout, tool health, incident classification, latency, and snapshot cache behavior.
#### `app/services/live/errors.py`

Functions/classes:
- `Error`
- `ValidationError`
- `ConfigurationError`

Requirements:
- [ ] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom live exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.
- [ ] Each exported live tool shall return a standard envelope containing tool name, status, request ID, correlation ID, side-effect mode, data, errors, warnings, audit metadata, incident reference, and `retry_after_seconds` where applicable.
- [ ] Live errors shall use documented error codes from a finite taxonomy and shall include request ID, correlation ID, failed gate where applicable, retry-safety classification, operator action hint, and audit reference when available.
- [ ] Secrets, credentials, tokens, authorization headers, private broker payloads, and raw approval packets shall not leak through logs, errors, notifications, metrics, reports, or chat.
- [ ] Loggers and redaction helpers shall recursively scrub fields whose names contain `secret`, `token`, `key`, `authorization`, `password`, `credential`, or `api_key`, case-insensitively, before logs, errors, reports, notifications, metrics, or chat output are emitted.
- [ ] No file-specific non-functional requirements defined.
- [ ] Security tests shall prove secrets, private broker payloads, and raw approval packets are redacted from errors, logs, reports, notifications, metrics, and chat.
### Unit Tests Required

```text
tests/unit/app/services/live/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/10_live.py
```

Usage examples must show:
- `example_01_live_config_and_readiness`: Demonstrate live config validation, readiness status, and disabled-by-default mutation policy.
- `example_02_session_lifecycle`: Demonstrate start, pause, resume, stop, recovery diagnostics, and runtime status events.
- `example_03_live_gates`: Demonstrate approval gates, kill-switch gates, stale-state gates, and fail-closed decisions.
- `example_04_shadow_and_dry_run_execution`: Demonstrate dry-run/shadow execution paths without broker mutation.
- `example_05_live_executor_boundary`: Demonstrate executor safety checks and rejection of direct broker mutation bypasses.
- `example_06_reconciliation_and_incidents`: Demonstrate startup reconciliation, mismatch handling, incident records, and alerts.
- `example_07_monitoring_and_health`: Demonstrate latency, ingestion health, tool health, cost, notification, and readiness monitoring.
- `example_08_emergency_actions`: Demonstrate governed pause, mass cancel, mass close, exposure reduction, and audit requirements.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 234 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(live-runtime): implement phase 10 live runtime requirements
```


- [ ] Secrets redaction tests shall inject fake values such as `password: secret123` and prove no log line, error message, notification, metric, report, or chat response contains `secret123`.
## Phase 11 UI and API Gateway

### Goal

Implement the UI and API Gateway requirements under `api/ and ui/` while preserving the phase module boundaries and governance rules.

Task inventory: 365 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `api/ and ui/`.
- Requires Phase 10 Live Runtime contracts to be available where referenced by `11_ui_api.md`.

### Files to Create

```text
api/ and ui/
api/__init__.py
api/main.py
api/app.py
api/dependencies.py
api/middleware/__init__.py
api/middleware/redaction.py
api/middleware/intent.py
api/middleware/auth.py
api/routes/__init__.py
api/routes/auth.py
api/routes/settings.py
api/routes/chat.py
api/routes/strategies.py
api/routes/simulation.py
api/routes/risk.py
api/routes/live.py
api/routes/operator.py
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `ui/src/lib/api/clients.ts`

Functions/classes:
- Planned file-local functions/classes listed by this section's requirements.

Requirements:
- [ ] API and UI shall prevent contract drift through typed DTOs, validators, and contract tests.
- [ ] Frontend API clients shall attach request and trace identifiers for observability.
- [ ] UI workflows shall display stale or unavailable data clearly and shall not use stale data for governed decisions without refresh.
- [ ] Mutating endpoints shall define retry eligibility, idempotency policy, audit-log requirement, and expected 4xx/5xx failure behavior.
- [ ] Frontend primary workflows shall meet a declared accessibility target, preferably WCAG 2.1 AA for core workflows, before production handoff.
- [ ] Build, lint, typecheck, contract validation, and security test gates shall be runnable in CI once implementation begins.
- [ ] Requirement IDs shall be added before production handoff for all functional and non-functional requirements, and each requirement shall map to at least one test case or an explicit manual-verification note.
- [ ] The canonical API shall configure CORS for local frontend origins and allow credentials.
- [ ] `GET /api/dashboard/equity-curve` shall return dashboard equity curve data.
- [ ] `backtestApi` shall expose frontend backtest operations.
- [ ] `marketDataApi` shall expose frontend market-data operations.
- [ ] `edgeLabApi` shall expose frontend Edge Lab operations.
- [ ] `optimizationApi` shall expose frontend optimization operations.
- [ ] `simulatorApi` shall expose frontend simulator operations.
- [ ] `strategyApi` shall expose frontend strategy operations.
- [ ] `tradesApi` shall expose frontend trade-data operations.
- [ ] Frontend contract validators shall validate agentic and generic API contracts before data is trusted by UI workflows.
- [ ] Strategy components shall support strategy listing, strategy cards, strategy creation, metadata editing, code editing, version history, diff viewing, and config preview.
- [ ] Edge Lab components shall support prerequisite state, navigation, dataset summary, collection state, controls, scorecard evidence, indicator charting, core metric unsupervised views, and EDS evidence.
- [ ] Performance components shall support trade detail, trade chart, statistics, calendars, comparative charts, metric grids, distributions, scatter charts, series charts, and page-level actions.

#### `api/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] Every pending policy in the Pre-handoff Blockers table is resolved or explicitly deferred by owner decision.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/main.py`

Functions/classes:
- `create_app`
- `main`

Requirements:
- [ ] Each public HTTP route shall define method, path, auth requirement, role or permission requirement, request schema, response schema, status codes, standard error envelope, side effects, idempotency behavior, audit requirement where applicable, rate-limit class, observability fields, and owning backend/domain service.
- [ ] UI/API requirements define boundary contracts, not domain-service implementation.
- [ ] API route handlers shall validate path, query, header, and body inputs using boundary schemas before calling domain services.
- [ ] API route handlers shall translate domain blocks, idempotency conflicts, dependency failures, and internal failures into documented standard envelopes with route-appropriate status codes.
- [ ] Domain-facing route handlers shall validate and authorize requests, call the approved owning domain service, translate service results into boundary DTOs, and shall not implement trading, risk, broker, simulation, optimization, research, or persistence algorithms inline.
- [ ] Domain-facing route handlers shall use an approved service-client interface with explicit service discovery, timeout, auth context forwarding, service-account fallback rules, request/correlation ID propagation, and typed error translation before implementation.
- [ ] Idempotency keys shall be non-empty, string-safe, bounded-length values supplied through a documented header or request field; exact key format remains blocked by UIAPI-BLK-004.
- [ ] Requirement ID ranges shall use `UIAPI-CAP-*`, `UIAPI-FR-*`, `UIAPI-NFR-*`, `UIAPI-EDGE-*`, `UIAPI-TEST-*`, and `UIAPI-EX-*`. Existing unnumbered checkboxes remain provisional and are not Builder-ready until IDs are assigned.
- [ ] `api.main:app` shall be the canonical backend FastAPI entry point.
- [ ] `POST /api/risk/position-sizing` shall validate and authorize the request, delegate risk-based position sizing to the approved risk-domain service, and return the service result through the documented API response schema without implementing risk calculation logic in the UI/API layer.
- [ ] `POST /api/risk/regime-detection` shall validate and authorize the request, delegate regime detection to the approved risk-domain service, and return the service result through the documented API response schema.
- [ ] `POST /api/risk/allocation` shall validate and authorize the request, delegate risk allocation to the approved risk-domain service, and return the service result through the documented API response schema.
- [ ] `POST /api/risk/governance` shall validate and authorize the request, delegate risk governance evaluation to the approved risk-domain service, and return the service result through the documented API response schema.
- [ ] `GET /api/dashboard/currency-strength` shall remain optional/deferred until its schema, source service, stale-data behavior, and frontend contract are finalized.
- [ ] Frontend API clients shall expose typed access for AI chat, backtest, data, docs, Edge Lab, live, optimization, risk, simulator, strategies, trades, audit, board, cost, evidence, execution, portfolio, research, settings, and workflow domains.
- [ ] Live trading mutations shall remain disabled unless explicit live flags, risk approval, broker readiness, reconciliation, idempotency, audit, and kill-switch requirements are satisfied by backend services.
- [ ] Primary UI workflow controls shall remain visible or reachable without horizontal scrolling at documented supported viewport widths, shall not overlap critical content, shall provide accessible labels, and shall satisfy the declared accessibility target.
- [ ] Frontend build, lint, and agentic-firm contract tests shall remain runnable through package scripts.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/app.py`

Functions/classes:
- `create_app`
- `configure_routes`
- `configure_middleware`

Requirements:
- [ ] The gateway shall not call unknown internal service APIs directly from route handlers. Every delegated call shall go through an approved client or orchestrator abstraction.
- [ ] Delegation shall be serial by default: validate request, authorize actor, call one approved service client, translate result. Multi-service workflows require an approved orchestrator abstraction and must not accumulate business rules in route handlers.
- [ ] Error envelopes shall include deterministic code, human-readable message, bounded details, request id, trace or correlation id, and retryability where applicable.
- [ ] Streaming endpoints shall use a documented stream event envelope containing event name or type, data, request id, trace or correlation id, sequence, timestamp, and terminal-error fields where applicable.
- [ ] Proposed Decision: Backward compatibility shall be preserved within an approved stable major API version. Deprecations require documentation, frontend migration notes, and an owner-approved removal window before stable-route removal.
- [ ] Mutating governed endpoints shall require request id, trace or correlation id, actor identity, required permission, approval context where applicable, audit event type, and an idempotency key for governed or financial mutations.
- [ ] `lifespan` shall initialize the database, apply pending migrations, clean stale simulator leases when simulator routes are available, start the scheduler, and shut the scheduler down on application shutdown.
- [ ] `api.app.create_app` shall build the migration-era operator API with dependency injection, CORS, operator auth middleware, operator metadata routes, health routes, approval routes, and event-stream routes.
- [ ] Public operator routes shall be limited to documentation and health endpoints and shall never expose approval, policy, actor, live-execution, broker, incident, or private system data.
- [ ] A redacted public health-only stream shall not exist unless approved by owner/security decision. If approved, it may expose only static service name, coarse health state, heartbeat timestamp, and public schema version, and must not reuse the protected operator event stream path unless explicitly documented.
- [ ] Operator roles shall be limited to `operator`, `approver`, and `admin`.
- [ ] `GET /api/operator/health` shall return aggregate app, database, Redis, and schema-registry health.
- [ ] `POST /api/operator/live-execution` shall create a live-execution approval request.
- [ ] `POST /api/operator/policy-change` shall create a policy-change approval request.
- [ ] `POST /api/operator/override` shall create an override approval request.
- [ ] `POST /api/operator/kill-switch-recovery` shall create a kill-switch recovery approval request.
- [ ] `POST /api/operator/live-execution/{approval_id}/votes` shall record a vote on a live-execution approval.
- [ ] `GET /api/operator/events/stream` shall stream operator events only through the approved operator stream contract, auth policy, redaction policy, heartbeat policy, and disconnect cleanup policy.
- [ ] `POST /api/ai-chat/threads/{thread_id}/action-drafts/{draft_id}/request-approval` shall request approval for an action draft.
- [ ] `POST /api/ai-chat/threads/{thread_id}/action-drafts/{draft_id}/paper-execute` shall execute an action draft only in the approved paper path.
- [ ] `POST /api/sqx/calculate-scores` shall validate and authorize the request, delegate SQX score calculation to the approved strategy or analytics service, and return the service result.
- [ ] `POST /api/backtest/run/{strategy_id}` shall validate and authorize the request, delegate backtest execution to the approved simulation service, and return the service result.
- [ ] `POST /api/backtest/portfolio/run/{strategy_id}` shall validate and authorize the request, delegate portfolio backtest execution to the approved simulation or analytics service, and return the service result.
- [ ] `POST /api/optimization/runs` shall validate and authorize the request, delegate bounded run creation to the approved optimization service, and return the run contract without implementing optimization algorithms in the UI/API layer.
- [ ] `POST /api/optimization/walk-forward` shall validate and authorize the request, delegate walk-forward analysis to the approved optimization service, and return the service result.
- [ ] `POST /api/optimization/unsupervised-analysis` shall validate and authorize the request, delegate unsupervised analysis to the approved optimization or research service, and return the service result.
- [ ] `POST /api/optimization/monte-carlo` shall validate and authorize the request, delegate Monte Carlo simulation to the approved optimization service, and return the service result.
- [ ] `POST /api/optimization/monte-carlo/parametric` shall validate and authorize the request, delegate parametric Monte Carlo to the approved optimization service, and return the service result.
- [ ] `POST /api/optimization/monte-carlo/position-sizing` shall validate and authorize the request, delegate position-sizing simulation to the approved optimization or risk service, and return the service result.
- [ ] `POST /api/optimization/monte-carlo/consecutive-losing` shall validate and authorize the request, delegate consecutive-losing simulation to the approved optimization service, and return the service result.
- [ ] `POST /api/optimization/monte-carlo/profit-target` shall validate and authorize the request, delegate profit-target simulation to the approved optimization service, and return the service result.
- [ ] `POST /api/optimization/monte-carlo/random-win-rate` shall validate and authorize the request, delegate random-win-rate simulation to the approved optimization service, and return the service result.
- [ ] `POST /api/optimization/monte-carlo/robustness` shall validate and authorize the request, delegate robustness simulation to the approved optimization service, and return the service result.
- [ ] `POST /api/optimization/monte-carlo/multi-entry` shall validate and authorize the request, delegate multi-entry simulation to the approved optimization service, and return the service result.
- [ ] `POST /api/data/dataset/prepare` shall validate and authorize the request, delegate generic dataset preparation to the approved data or research service, and return the service result.
- [ ] `POST /api/edge-lab/run` shall validate and authorize the request, delegate Edge Lab analysis to approved Edge Lab or research services, and return the service result without implementing research algorithms in the UI/API layer.
- [ ] `POST /api/edge-lab/dataset/prepare` shall validate and authorize the request, delegate Edge Lab-specific dataset preparation to the approved Edge Lab or data service, and return the service result.
- [ ] `POST /api/edge-lab/seasonality` shall validate and authorize the request, delegate seasonality analysis to the approved research service, and return the service result.
- [ ] `POST /api/edge-lab/core-metrics/run` shall validate and authorize the request, delegate core metric calculation to the approved research or analytics service, and return the service result.
- [ ] `POST /api/edge-lab/market-structure/run` shall validate and authorize the request, delegate market-structure analysis to the approved research service, and return the service result.
- [ ] `POST /api/edge-lab/unsupervised-structure/run` shall validate and authorize the request, delegate unsupervised-structure analysis to the approved research service, and return the service result.
- [ ] `POST /api/edge-lab/market-structure/stability` shall validate and authorize the request, delegate stability analysis to the approved research service, and return the service result.
- [ ] `POST /api/edge-lab/market-structure/robustness` shall validate and authorize the request, delegate robustness analysis to the approved research service, and return the service result.
- [ ] `POST /api/edge-lab/automation/run` shall validate and authorize the request, delegate Edge Lab automation to the approved orchestration service, and return the service result.
- [ ] `POST /api/edge-lab/automation/batch` shall validate and authorize the request, delegate Edge Lab automation batch work to the approved orchestration service, and return the service result.
- [ ] `governedWriteContext` shall construct governed write options with workflow id, approval id, required permission, audit event type, and optional board or critical-incident approval ids.
- [ ] Governed frontend writes shall be blocked before request when required request id, workflow id, approval id, server permission check, CSRF token, audit intent, or required approval context is missing.
- [ ] Layout components shall provide app shell, sidebar, navbar, offline banner, theme provider, error boundary, and shared UI primitives.
- [ ] Documentation components shall support navigation, table of contents, Markdown rendering, document wrapping, and document editing.
- [ ] Protected API endpoints shall require authenticated user or service-account context where applicable.
- [ ] API responses shall use standard envelopes unless streaming has a documented approved event format.
- [ ] Proposed Decision: Default request body size limit shall be 1 MB for standard JSON endpoints, 10 MB for approved import endpoints, and route-specific for explicitly approved artifact uploads. Oversized payloads return HTTP 413 with `PAYLOAD_TOO_LARGE`.
- [ ] Proposed Decision: Default maximum streaming connections shall be 5 per authenticated actor/session per stream class and 50 process-wide per stream class until production capacity tests approve higher limits.
- [ ] Every public route group has a concrete route contract table with method, path, auth, schema refs, status codes, error codes, idempotency behavior, pagination behavior where applicable, rate-limit class, observability fields, side effects, stability, and owning service.
- [ ] Every functional and non-functional requirement has a requirement ID and mapped test type.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Each public HTTP route, WebSocket/SSE stream, frontend client, and official callable capability shall identify whether it is public API, protected API, internal helper, migration-compatibility surface, official frontend client capability, or optional/deferred capability.
- [ ] Each frontend API client capability shall map to a documented backend route contract or be marked as frontend-only, mocked, optional/deferred, or migration-only.
- [ ] Optional backend route import failures shall degrade route availability without blocking unrelated API startup.
- [ ] API startup shall not require unavailable optional providers for unrelated routes.
- [ ] Proposed Decision: All API endpoints shall complete or return a structured error within 30 seconds unless the route contract documents a longer-running job, streaming flow, or accepted async run model.
- [ ] Proposed Decision: Default response size limit shall be 2 MB for standard JSON endpoints unless the route contract defines pagination, streaming, artifact download, or truncation behavior.
- [ ] API routes shall define timeout behavior and retry eligibility.
- [ ] Proposed Decision: WebSocket/SSE routes shall use a 15-second client-to-server ping interval where supported, a 30-second server expectation window, and terminal cleanup after missed heartbeat policy is triggered.
- [ ] API and UI compatibility shall be tested through OpenAPI or equivalent route snapshots and TypeScript DTO/validator drift checks before production handoff.
- [ ] Proposed Decision: Rate-limit responses shall return HTTP 429 with `RATE_LIMITED`, retry metadata where safe, request id, and trace or correlation id.
- [ ] Proposed Decision: Backend non-JSON upstream responses shall be translated to HTTP 502 with `UPSTREAM_NON_JSON_RESPONSE`, bounded sanitized details, request id, and trace or correlation id.
- [ ] API route handlers shall translate validation failures into the standard validation error envelope with HTTP 422.
- [ ] Non-streaming API responses shall use a standard response envelope with `status`, `message`, `data`, `error`, and `metadata` fields. Metadata shall include request id, correlation or trace id, API version, route group or module, operation, side-effect class, execution time, and creation timestamp where available. This standard response envelope must be imported and reused from `app.utils.standard` or `app.utils.errors` to prevent duplicate declaration.
- [ ] HTTP 204 responses shall never carry a body. Endpoints that need metadata, warnings, or audit details shall return a standard envelope with a non-204 status.
- [ ] Proposed Decision: List endpoints shall use cursor-based pagination by default, with `limit` defaulting to 50, maximum `limit` 200, opaque cursor strings, stable deterministic ordering, and empty results returned as an empty list plus null next cursor unless a route contract states otherwise.
- [ ] Proposed Decision: API versioning shall default to `v0-draft` during pre-implementation work. Frontend clients shall send the expected API version when a route contract requires it. Version mismatch shall return `409` with `CONTRACT_VERSION_MISMATCH` for incompatible contracts or a documented warning metadata field for compatible minor changes.
- [ ] Governed and financial mutation endpoints shall store idempotency material, request hash, response status, response headers, response body, actor, route, operation, created timestamp, expiry timestamp, and terminal state where storage is available.
- [ ] Proposed Decision: Duplicate idempotency keys with different material shall return HTTP 409 with `IDEMPOTENCY_CONFLICT`.
- [ ] Proposed Decision: Duplicate idempotency keys for an unknown, in-progress, or terminal-failed previous attempt shall return HTTP 409 with `DUPLICATE_IDEMPOTENCY_KEY` unless the route contract defines a safer reconciliation response.
- [ ] Proposed Decision: Idempotency storage unavailable shall fail closed by default with HTTP 503 and `DEPENDENCY_UNAVAILABLE` for governed and financial mutations.
- [ ] Frontend stale-warning threshold shall default to 30 seconds for dashboard/governed-decision context unless the route contract defines a stricter or looser threshold.
- [ ] Governed frontend write preflight shall emit a warning telemetry event when it blocks a request, including sanitized route, required permission, missing context type, request id, trace id, and actor/session metadata where available.
- [ ] `_optional_import` shall load optional route modules and log startup warnings instead of failing the whole API when an optional route cannot import.
- [ ] `_include_optional_router` shall include a router only when its module was imported successfully.
- [ ] `WEBSOCKET /api/backtest/ws/{backtest_id}/logs` shall stream backtest logs.
- [ ] `WEBSOCKET /api/optimization/ws/{optimization_id}` shall stream optimization progress.
- [ ] The frontend shall provide documentation routes under `/documentation`, `/documentation/manage`, `/documentation/fundamentals/*`, `/documentation/development/*`, and `/documentation/robustness/*`.
- [ ] The frontend shall provide Edge Lab routes under `/edge-lab`, including automation, core metric, discovery, edge profile, market structure, Monte Carlo lab, scorecard, seasonality, SQX import, and unsupervised structure.
- [ ] The frontend shall provide performance routes under `/performance`, including overview, metaparams, chart analysis, strategy analysis, trade analysis, trades calendar, and periodical analysis pages.
#### `api/dependencies.py`

Functions/classes:
- `get_operator_api_dependencies`

Requirements:
- [ ] `get_operator_api_dependencies` shall expose the operator dependency container to route handlers.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Each public capability shall declare stability as stable, experimental, deprecated, migration-only, or optional/deferred.
- [ ] Import and documentation endpoints shall define allowed content types, cleanup behavior, and path-safety behavior.
- [ ] Proposed Decision: Duplicate idempotency keys for completed successful operations shall return the stored original response, including status, headers, body, and metadata, with `metadata.retryable=false` and `metadata.idempotency_replay=true`.
- [ ] Documentation save/delete endpoints shall enforce a configured documentation root, normalize paths, reject traversal, reject symlink escape outside the root, and return explicit validation errors.
- [ ] Import endpoints shall define accepted file or content types, maximum size, parse-error behavior, duplicate import behavior, and cleanup behavior after partial failure.
- [ ] API request logs shall include sanitized method, path, headers, and query metadata.
- [ ] `GET /api/backtest/{backtest_id}` shall return a backtest.
- [ ] `GET /api/backtest/{backtest_id}/overview` shall return a backtest overview.
- [ ] `GET /api/backtest/` shall list all backtests.
- [ ] `PUT /api/backtest/{backtest_id}` shall update backtest metadata.
- [ ] `DELETE /api/backtest/{backtest_id}` shall delete a backtest.
- [ ] `GET /api/optimization/runs/{optimization_id}` shall return optimization run detail.
- [ ] `GET /api/optimization/runs/{optimization_id}/results` shall return optimization results.
- [ ] `DELETE /api/optimization/runs/{optimization_id}` shall cancel an optimization run.
- [ ] `GET /api/optimization/runs/{optimization_id}/unsupervised-report` shall return an unsupervised report.
- [ ] `GET /api/dashboard/broker` shall return broker status.
- [ ] `GET /api/dashboard/summary` shall return dashboard summary data.
- [ ] `GET /api/dashboard/system/status` shall return system status.
- [ ] `GET /api/dashboard/system/resources` shall return resource usage.
- [ ] `GET /api/dashboard/market-hours` shall return market-hours data.
- [ ] `GET /api/dashboard/forex-calendar` shall return forex-calendar data.
- [ ] `GET /api/docs/files` shall return documentation file tree data.
- [ ] `GET /api/docs/content` shall return documentation file content.
- [ ] `POST /api/docs/save` shall save documentation content.
- [ ] `DELETE /api/docs/delete` shall delete documentation content.
- [ ] `GET /api/data/symbols` shall return available market-data symbols.
- [ ] `GET /api/edge-lab/runs` shall list Edge Lab runs.
- [ ] `GET /api/edge-lab/runs/count` shall count Edge Lab runs.
- [ ] `GET /api/edge-lab/runs/summary` shall return Edge Lab run summary.
- [ ] `GET /api/edge-lab/runs/{run_id}` shall return an Edge Lab run.
- [ ] `GET /api/edge-lab/runs/{run_id}/stats` shall return Edge Lab run statistics.
- [ ] `GET /api/edge-lab/runs/{run_id}/trades` shall return Edge Lab run trades.
- [ ] `DELETE /api/edge-lab/runs/{run_id}` shall delete an Edge Lab run.
- [ ] `GET /api/edge-lab/core-metrics/runs` shall list core metric runs.
- [ ] `GET /api/edge-lab/core-metrics/runs/{run_id}` shall return a core metric run.
- [ ] `DELETE /api/edge-lab/core-metrics/runs/{run_id}` shall delete a core metric run.
- [ ] `GET /api/edge-lab/market-structure/runs` shall list market-structure runs.
- [ ] `GET /api/edge-lab/market-structure/runs/{run_id}` shall return a market-structure run.
- [ ] `DELETE /api/edge-lab/market-structure/runs/{run_id}` shall delete a market-structure run.
- [ ] `GET /api/edge-lab/market-structure/validation` shall return market-structure validation.
- [ ] `GET /api/edge-lab/market-structure/evaluations` shall list market-structure evaluations.
- [ ] `POST /api/edge-lab/market-structure/evaluations/refresh` shall refresh market-structure evaluations.
- [ ] `GET /api/edge-lab/market-structure/calibration` shall return market-structure calibration.
- [ ] `GET /api/edge-lab/market-structure/profile-calibration` shall return profile calibration.
- [ ] `GET /api/edge-lab/market-structure/metric-calibration` shall return metric calibration.
- [ ] `POST /api/edge-lab/automation/refresh` shall refresh Edge Lab automation schedule.
- [ ] `POST /api/edge-lab/scorecard/snapshots` shall save a scorecard snapshot.
- [ ] `GET /api/edge-lab/scorecard/snapshots` shall list scorecard snapshots.
- [ ] `GET /api/edge-lab/scorecard/snapshots/{snapshot_id}` shall return a scorecard snapshot.
- [ ] `GET /api/edge-lab/scorecard/snapshots/compare` shall compare scorecard snapshots.
- [ ] `POST /api/edge-lab/scorecard/snapshots/{snapshot_id}/export-parquet` shall export a scorecard snapshot to Parquet.
- [ ] `GET /api/edge-lab/scorecard/snapshots/{snapshot_id}/report` shall return a scorecard snapshot report.
- [ ] `POST /api/edge-lab/scorecard/snapshots/{snapshot_id}/export-report` shall export a scorecard snapshot report.
- [ ] `POST /api/edge-lab/scorecard/snapshots/compare/export-markdown` shall export scorecard snapshot comparison Markdown.
- [ ] `agenticApiRequest` shall create request and trace ids, attach headers, validate governed writes before sending, execute the fetch, parse payloads, validate contracts when a schema is supplied, track telemetry, and return an envelope with data, request id, trace id, stale flag, and stale warning.
- [ ] `agenticApiData` shall return only the data portion of `agenticApiRequest`.
- [ ] `AgenticApiError` shall carry message, request id, trace id, and status for failed API calls.
- [ ] Read-only GET requests may retry once when enabled and not governed.
- [ ] Stale API responses shall emit telemetry and include a stale warning.
#### `api/middleware/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/middleware/redaction.py`

Functions/classes:
- `SecretRedactionMiddleware`

Requirements:
- [ ] The canonical API shall install `SecretRedactionMiddleware`.
- [ ] `SecretRedactionMiddleware` shall redact request headers and query parameters before debug logging.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] API errors and logs shall redact secrets and avoid exposing credentials or private broker data.
#### `api/middleware/intent.py`

Functions/classes:
- `IntentClassificationMiddleware`
- `IntentClassifier`
- `classify_intent`

Requirements:
- [ ] `IntentClassificationMiddleware` shall classify every request path and attach intent, priority, session id, and user id metadata to request state.
- [ ] `IntentClassifier` shall classify request intent from the URL path and optional session header.
- [ ] Routing metadata shall include intent, priority, session id, and user id fields.
- [ ] API logs, traces, and telemetry shall include request id, trace or correlation id, route group, route intent, actor id where available, session id where available, status code, duration, and sanitized error code.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/middleware/auth.py`

Functions/classes:
- `VALIDATION_FAILED`
- `AUTHENTICATION_REQUIRED`
- `AUTHORIZATION_FAILED`
- `CSRF_REQUIRED`
- `CSRF_INVALID`
- `RATE_LIMITED`
- `IDEMPOTENCY_KEY_REQUIRED`
- `DUPLICATE_IDEMPOTENCY_KEY`
- `IDEMPOTENCY_CONFLICT`
- `GOVERNANCE_REQUIRED`
- `STALE_DATA`
- `UPSTREAM_UNAVAILABLE`
- `UPSTREAM_NON_JSON_RESPONSE`
- `UPSTREAM_TIMEOUT`
- `CONTRACT_VERSION_MISMATCH`
- `PAYLOAD_TOO_LARGE`
- `UNSUPPORTED_MEDIA_TYPE`
- `OPERATOR_STREAM_FORBIDDEN`
- `DEPENDENCY_UNAVAILABLE`
- `INTERNAL_ERROR`
- `NOT_IMPLEMENTED`
- `get_operator_principal`

Requirements:
- [ ] Each WebSocket, SSE, or streaming capability shall define auth, event schema, heartbeat interval, reconnect behavior, disconnect cleanup, backpressure behavior, terminal error event, sequence behavior, and maximum connection policy.
- [ ] API route handlers shall translate authentication failures into the standard 401 error envelope.
- [ ] API route handlers shall translate authorization failures into the standard 403 error envelope.
- [ ] Standard error codes shall include `VALIDATION_FAILED`, `AUTHENTICATION_REQUIRED`, `AUTHORIZATION_FAILED`, `CSRF_REQUIRED`, `CSRF_INVALID`, `RATE_LIMITED`, `IDEMPOTENCY_KEY_REQUIRED`, `DUPLICATE_IDEMPOTENCY_KEY`, `IDEMPOTENCY_CONFLICT`, `GOVERNANCE_REQUIRED`, `STALE_DATA`, `UPSTREAM_UNAVAILABLE`, `UPSTREAM_NON_JSON_RESPONSE`, `UPSTREAM_TIMEOUT`, `CONTRACT_VERSION_MISMATCH`, `PAYLOAD_TOO_LARGE`, `UNSUPPORTED_MEDIA_TYPE`, `OPERATOR_STREAM_FORBIDDEN`, `DEPENDENCY_UNAVAILABLE`, `INTERNAL_ERROR`, and `NOT_IMPLEMENTED`. Custom API gateway exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
- [ ] `GET /api/health` shall be unauthenticated and shall return HTTP 200 with a minimal service status payload when the API process is accepting requests. It shall not expose secrets, credentials, broker account data, or private dependency details.
- [ ] `authenticate_user` shall authenticate username/password, reject invalid or inactive users, distinguish unverified users, update last login for verified users, and return user metadata.
- [ ] `get_user_id_from_token` shall require an Authorization header, accept optional Bearer prefix, verify the token, and raise 401 for missing, invalid, or expired tokens.
- [ ] `OperatorAuthMiddleware` shall protect all `/api/operator` routes except explicitly public documentation and health routes.
- [ ] `GET /api/operator/events/stream` shall require an authenticated operator principal with an allowed operator role unless a separately documented redacted public health-only stream is explicitly configured.
- [ ] `get_operator_principal` shall return the authenticated operator principal or raise 401.
- [ ] `require_operator_role` shall enforce allowed operator roles and raise 403 when unauthorized.
- [ ] `POST /api/auth/register` shall register a user account.
- [ ] `POST /api/auth/login` shall authenticate a user and return an auth response.
- [ ] `POST /api/auth/logout` shall invalidate the caller's session token.
- [ ] `GET /api/settings/` shall return settings for the authenticated user.
- [ ] `PUT /api/settings/` shall update settings for the authenticated user.
- [ ] The frontend shall provide authentication routes `/login` and `/register`.
- [ ] `request` shall call the configured API URL, attach JSON content type, attach the local auth bearer token when present, parse JSON error details, support 204 responses, and return parsed JSON data.
- [ ] Protected dashboard layouts shall prevent unauthenticated use of protected workflows.
- [ ] Auth components shall support login and registration flows.
- [ ] Governed and financial endpoints shall require backend safety gates and audit; frontend checks are preflight only and shall not be treated as final authorization.
- [ ] WebSocket and streaming routes shall detect client disconnects, stop per-client delivery work, release per-client resources, preserve authoritative session state, emit no further events to the disconnected client, and record sanitized disconnect metadata.
- [ ] Authentication tokens shall be treated as secrets and shall not be logged or exposed in telemetry.
- [ ] API logs, traces, telemetry, and frontend telemetry shall not include auth tokens, broker credentials, API provider credentials, passwords, raw secrets, authorization headers, CSRF tokens, or private broker account data.
- [ ] Proposed Decision: Non-streaming authenticated read endpoints shall target p95 latency under 200 ms in lab/local contract tests and under 500 ms in production-like tests, excluding explicitly documented long-running analysis endpoints.
- [ ] Proposed Decision: Initial rate-limit classes shall include `health` 120/minute, `standard-read` 300/minute, `standard-write` 60/minute, `auth` 10/minute, `ai-chat` 50/minute, `operator` 30/minute, `live-mutation` 5/minute, `import` 10/minute, and `analysis` 20/minute per actor/session or stricter route-specific scope.
- [ ] Every streaming surface has a concrete event contract with auth, event envelope, heartbeat, reconnect, backpressure, disconnect cleanup, terminal-error behavior, and maximum connection policy.
- [ ] Every governed mutation has a concrete idempotency, audit, authorization, CSRF, duplicate-submit, and stale-data policy.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Mutating endpoints shall require role/action checks and governed write context where financial or operational side effects are possible.
- [ ] `generate_token` shall create a single active user session token, invalidate existing sessions for that user, and set a 24-hour duration.
- [ ] `verify_token` shall validate stored sessions, parse expiration timestamps, delete expired sessions, and return the user id only for valid sessions.
- [ ] `invalidate_token` shall delete a stored session token.
#### `api/routes/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/routes/auth.py`

Functions/classes:
- `login`
- `logout`
- `refresh_token`
- `get_current_operator`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/routes/settings.py`

Functions/classes:
- `Config`
- `load_config`
- `validate_config`

Requirements:
- [ ] `GET /api/settings` shall return settings without requiring a trailing slash.
- [ ] The frontend shall provide dashboard-level routes for `/`, `/agents`, `/ai-ceo`, `/audit`, `/backtests`, `/board-room`, `/chart/[[...slug]]`, `/costs`, `/execution`, `/live`, `/optimization`, `/portfolio`, `/research`, `/risk-center`, `/settings`, `/strategies`, `/strategies/[id]`, `/strategy-lab`, `/tools`, and `/tools/currency-strength`.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/routes/chat.py`

Functions/classes:
- `listAiChatThreads`
- `streamAiChatResponse`

Requirements:
- [ ] Frontend page context providers shall redact secrets and bound context payload size before sending context to AI chat or route-aware workflows.
- [ ] `GET /api/ai-chat/threads` shall list AI chat threads.
- [ ] `POST /api/ai-chat/threads` shall create an AI chat thread.
- [ ] `GET /api/ai-chat/threads/{thread_id}` shall return thread detail.
- [ ] `PATCH /api/ai-chat/threads/{thread_id}` shall rename a thread.
- [ ] `PATCH /api/ai-chat/threads/{thread_id}/context` shall update thread page context.
- [ ] `DELETE /api/ai-chat/threads/{thread_id}` shall delete a thread.
- [ ] `POST /api/ai-chat/threads/{thread_id}/archive` shall archive a thread.
- [ ] `POST /api/ai-chat/threads/{thread_id}/restore` shall restore a thread.
- [ ] `POST /api/ai-chat/threads/{thread_id}/purge` shall purge a thread where allowed.
- [ ] `GET /api/ai-chat/threads/{thread_id}/retention` shall return thread retention detail.
- [ ] `PATCH /api/ai-chat/threads/{thread_id}/retention` shall update thread retention class.
- [ ] `POST /api/ai-chat/retention/lifecycle-run` shall run retention lifecycle processing.
- [ ] `GET /api/ai-chat/threads/{thread_id}/export` shall export a thread.
- [ ] `POST /api/ai-chat/threads/{thread_id}/messages` shall create a chat message.
- [ ] `GET /api/ai-chat/tools` shall list AI chat tools.
- [ ] `POST /api/ai-chat/context/resolve` shall resolve page context.
- [ ] `GET /api/ai-chat/threads/{thread_id}/signal-proposals` shall list signal proposals linked to a thread.
- [ ] `POST /api/ai-chat/threads/{thread_id}/signal-proposals/{proposal_id}/watchlist` shall save a signal proposal to the watchlist.
- [ ] `POST /api/ai-chat/threads/{thread_id}/signal-proposals/{proposal_id}/review-queue` shall queue a signal proposal for review.
- [ ] `GET /api/ai-chat/threads/{thread_id}/action-drafts` shall list action drafts linked to a thread.
- [ ] `POST /api/ai-chat/threads/{thread_id}/responses/stream` shall stream an AI chat response.
- [ ] `POST /api/ai-chat/threads/{thread_id}/responses/regenerate` shall regenerate an AI chat response.
- [ ] The frontend shall provide live, simulation, risk, strategy, Edge Lab, dashboard, documentation, AI chat, and performance components that render backend data without owning backend business rules.
- [ ] `listAiChatThreads` shall list AI chat threads through the frontend AI chat client.
- [ ] `streamAiChatResponse` shall stream AI chat responses through the frontend AI chat client.
- [ ] Page context providers and hooks shall register current page context and actions for AI chat and route-aware workflows.
- [ ] AI chat UI shall include launcher, panel, header, input, message list, action-plan preview, CEO status badge, route labels, page-intelligence blocks, and semantic snapshot support.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/routes/strategies.py`

Functions/classes:
- `get_strategy_template`
- `create_strategy`
- `list_strategies`
- `get_strategy`
- `update_strategy`
- `delete_strategy`

Requirements:
- [ ] `GET /api/strategies/templates/{template_name}` shall return a strategy template.
- [ ] `POST /api/strategies/` shall create a strategy.
- [ ] `GET /api/strategies/` shall list strategies.
- [ ] `GET /api/strategies/{strategy_id}` shall return one strategy.
- [ ] `PUT /api/strategies/{strategy_id}` shall update a strategy.
- [ ] `DELETE /api/strategies/{strategy_id}` shall delete a strategy.
- [ ] `GET /api/strategies/{strategy_id}/versions` shall list strategy versions.
- [ ] `GET /api/strategies/{strategy_id}/versions/{version_id}/code` shall return version code.
- [ ] `POST /api/strategies/{strategy_id}/versions/{version_id}/rollback` shall roll a strategy back to a version.
- [ ] `POST /api/strategies/{strategy_id}/export` shall export a strategy.
- [ ] `POST /api/strategies/{strategy_id}/import` shall import a strategy.
- [ ] `POST /api/sqx/import` shall import SQX strategies.
- [ ] `GET /api/sqx/strategies` shall list imported SQX strategies.
- [ ] `POST /api/live/sessions/{session_id}/strategies` shall add a strategy to a live session.
- [ ] `DELETE /api/live/sessions/{session_id}/strategies/{strategy_config_id}` shall remove a strategy from a live session.
- [ ] `GET /api/live/sessions/{session_id}/strategies` shall list live session strategies.
- [ ] Dashboard components shall render system status, broker status, market hours, resource usage, recent activity, quick actions, active strategies, equity curve, daily PnL, win rate, and currency-strength views.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] `GET /api/backtest/strategy/{strategy_id}` shall list backtests for a strategy.
#### `api/routes/simulation.py`

Functions/classes:
- `start_simulation`
- `list_simulation_sessions`
- `get_simulation_session`
- `cancel_simulation_session`

Requirements:
- [ ] `POST /api/simulator/start` shall start a simulation session.
- [ ] `GET /api/simulator/sessions` shall list simulation sessions.
- [ ] `GET /api/simulator/paused` shall list paused simulation sessions.
- [ ] `GET /api/simulator/{session_id}` shall return one simulation session.
- [ ] `PUT /api/simulator/{session_id}` shall update a simulation session.
- [ ] `GET /api/simulator/{session_id}/bar/{bar_index}` shall return one bar from a simulation session.
- [ ] `POST /api/simulator/{session_id}/advance` shall advance a simulation by bars.
- [ ] `POST /api/simulator/{session_id}/what-if` shall evaluate a simulation what-if action.
- [ ] `POST /api/simulator/{session_id}/resume` shall resume a simulation session.
- [ ] `POST /api/simulator/{session_id}/seek` shall seek a simulation session.
- [ ] `GET /api/simulator/{session_id}/trades` shall list simulation trades.
- [ ] `DELETE /api/simulator/{session_id}` shall delete a simulation session.
- [ ] `POST /api/simulator/{session_id}/stop-and-save` shall stop and save a simulation session.
- [ ] `GET /api/optimization/monte-carlo/{simulation_id}` shall return a Monte Carlo result.
- [ ] The frontend shall provide simulation routes under `/simulation`, including batch auto, manual, replay, visual auto, replay backtest detail, and replay trade detail.
- [ ] Backtest and simulation components shall support configuration, execution view, results, charts, trade lists, sessions, positions, orders, risk panels, speed/skip controls, and trading dialogs.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] `GET /api/simulator/{session_id}/positions` shall return session positions.
- [ ] `POST /api/simulator/{session_id}/trade` shall execute a simulated trade.
- [ ] `POST /api/simulator/{session_id}/trade/preview` shall preview a simulated trade.
- [ ] `POST /api/simulator/{session_id}/order/pending` shall place a simulated pending order.
- [ ] `PATCH /api/simulator/{session_id}/positions/{position_id}` shall modify a simulated position.
- [ ] `DELETE /api/simulator/{session_id}/positions/{position_id}` shall close a simulated position.
- [ ] `POST /api/simulator/{session_id}/positions/{position_id}/partial` shall partially close a simulated position.
- [ ] `PATCH /api/simulator/{session_id}/orders/{order_id}` shall modify a simulated order.
- [ ] `DELETE /api/simulator/{session_id}/orders/{order_id}` shall delete a simulated order.
- [ ] `POST /api/simulator/{session_id}/seek-trade` shall seek to a trade.
#### `api/routes/risk.py`

Functions/classes:
- `riskApi`

Requirements:
- [ ] `riskApi` shall expose frontend risk operations.
- [ ] Live components shall support live status, sessions, strategy runner, session strategy manager, positions, orders, manual order controls, risk monitoring, candle charts, and logs.
- [ ] Frontend code shall not embed backend business logic for trading, risk, broker execution, research algorithms, or persistence rules.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/routes/live.py`

Functions/classes:
- `LiveTradingAPI`

Requirements:
- [ ] `POST /api/live/sessions` shall create a live session.
- [ ] `GET /api/live/sessions` shall list live sessions.
- [ ] `GET /api/live/sessions/{session_id}` shall return one live session.
- [ ] `PUT /api/live/sessions/{session_id}` shall update a live session.
- [ ] `DELETE /api/live/sessions/{session_id}` shall delete a live session.
- [ ] `POST /api/live/sessions/{session_id}/start` shall start a live session only through live-session controls.
- [ ] `POST /api/live/sessions/{session_id}/stop` shall stop a live session.
- [ ] `POST /api/live/sessions/{session_id}/pause` shall pause a live session.
- [ ] `POST /api/live/sessions/{session_id}/resume` shall resume a live session.
- [ ] `GET /api/live/sessions/{session_id}/status` shall return live session status.
- [ ] `GET /api/live/sessions/{session_id}/statistics` shall return live session statistics.
- [ ] `GET /api/live/sessions/{session_id}/market-data` shall return live session market data.
- [ ] `GET /api/live/sessions/{session_id}/signals` shall return live session signals.
- [ ] `GET /api/live/sessions/{session_id}/positions` shall return live session positions.
- [ ] `GET /api/live/sessions/{session_id}/logs` shall return live session logs.
- [ ] `PUT /api/live/sessions/{session_id}/positions/{position_id}` shall request live position modification through the live route.
- [ ] `POST /api/live/sessions/{session_id}/orders` shall request manual live order creation through the live route.
- [ ] `GET /api/live/sessions/{session_id}/orders` shall return live session orders.
- [ ] `DELETE /api/live/sessions/{session_id}/orders/{ticket}` shall request live order cancellation through the live route.
- [ ] `POST /api/live/sessions/{session_id}/orders/pending` shall request pending live order creation through the live route.
- [ ] `DELETE /api/live/sessions/{session_id}/positions/{position_id}` shall request live position closure through the live route.
- [ ] `POST /api/live/sessions/{session_id}/positions/close-all` shall request closing all live positions through the live route.
- [ ] `WEBSOCKET /api/live/sessions/{session_id}/ws` shall stream live session events.
- [ ] `LiveTradingAPI` shall expose frontend live-trading operations.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `api/routes/operator.py`

Functions/classes:
- `OperatorPrincipal`
- `get_operator_metadata`
- `list_operator_events`

Requirements:
- [ ] `OperatorPrincipal` shall represent token, actor id, and role extracted from operator request headers.
- [ ] `GET /api/operator` shall return operator API metadata, environment, schema registry contract count, policy bundle count, actor id, and role.
- [ ] `GET /api/operator/health/db` shall return database health.
- [ ] `GET /api/operator/health/redis` shall return Redis health.
- [ ] `GET /api/operator/health/schema-registry` shall return schema-registry health.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
### Unit Tests Required

```text
tests/unit/api/ and ui/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/11_ui_api.py
```

Usage examples must show:
- `example_01_api_health_and_metadata`: Demonstrate health, readiness, metadata, schema registry, and versioned response envelopes.
- `example_02_auth_and_operator_context`: Demonstrate token validation, operator principal extraction, role checks, and denial responses.
- `example_03_route_validation`: Demonstrate request DTO validation, response DTO validation, pagination, filters, and error translation.
- `example_04_guarded_write_preflight`: Demonstrate governed write preflight checks while backend remains authoritative.
- `example_05_streaming`: Demonstrate WebSocket/SSE heartbeat, reconnect, backpressure, terminal errors, and cleanup.
- `example_06_frontend_api_clients`: Demonstrate typed clients, trace headers, stale-response warnings, and telemetry hooks.
- `example_07_ui_workflows`: Demonstrate dashboard, data, strategy, simulation, risk, live, operator, and chat workflows through clients.
- `example_08_no_domain_logic_boundary`: Demonstrate route handlers delegate to services and do not embed trading, risk, or simulation algorithms.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 365 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(ui-api): implement phase 11 ui and api gateway requirements
```

## Phase 12 Research Edge Lab

### Goal

Implement the Research Edge Lab requirements under `app/services/research/` while preserving the phase module boundaries and governance rules.

Task inventory: 290 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/research/`.
- Requires Phase 11 UI and API Gateway contracts to be available where referenced by `12_research.md`.

### Files to Create

```text
app/services/research/
app/services/research/__init__.py
app/services/research/config.py
app/services/research/data.py
app/services/research/features.py
app/services/research/leakage.py
app/services/research/metrics.py
app/services/research/studies/__init__.py
app/services/research/studies/eds.py
app/services/research/studies/null_models.py
app/services/research/studies/structure.py
app/services/research/studies/unsupervised.py
app/services/research/helpers.py
app/services/research/reporting.py
app/services/research/errors.py
app/utils/errors.py
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/research/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] Importing `app.services.research` shall not perform network calls, disk writes, provider initialization, credential reads, live trading state access, or heavy model execution.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/research/config.py`

Functions/classes:
- `CleaningConfig`

Requirements:
- [ ] `create_config` shall create an Edge Lab configuration object with common defaults for research workflows.
- [ ] `DataConfig` shall describe source, symbol, timeframe, and date-range data inputs for research workflows.
- [ ] `SessionConfig` shall describe trading-session windows and related session settings.
- [ ] `BootstrapConfig` shall describe bootstrap resampling settings.
- [ ] `PermutationConfig` shall describe permutation-test settings.
- [ ] `NullModelsConfig` shall describe null-model settings and acceptance criteria.
- [ ] `MeanReversionConfig` shall describe mean-reversion edge-discovery settings.
- [ ] `TrendPersistenceConfig` shall describe trend-persistence edge-discovery settings.
- [ ] `MarketStructureConfig` shall describe market-structure research settings.
- [ ] `SessionEdgeConfig` shall describe session-edge research settings.
- [ ] `EdgeLabConfig` shall aggregate the module's research configuration sections into one workflow-level configuration.
- [ ] `TradeSample` shall represent a normalized trade sample for edge-result reporting.
- [ ] `EdgeStats` shall represent summary statistics for an edge result.
- [ ] `EdgeResult` shall represent a complete edge-study result suitable for summaries and reports.
- [ ] `research_modeling_module` shall return the research modeling service module through the shared lazy-resolution utility.
- [ ] Each public export in `app.services.research.__all__` shall have a documented contract specifying API status, input types, required fields, output type, error behavior, side effects, determinism guarantees, network/heavy dependency status, and stability level.
- [ ] Core model contracts shall define required fields, optional fields, schema versions, validation behavior, serialization behavior, and example payloads for `PreparedDataset`, `DataQualityReportModel`, `EdgeResult`, `CoreMetricProfile`, `MarketStructureProfile`, `UnsupervisedResearchResult`, `UnsupervisedInsightReport`, and report payloads.
- [ ] The module shall define a canonical research error taxonomy covering validation errors, configuration errors, insufficient-data errors, statistical-invalidity errors, external-provider errors, serialization errors, resource-limit errors, and permission errors.
- [ ] Public library functions shall either raise typed research exceptions or return structured result objects with warnings according to their documented contract; standard research tools shall return errors through the standard HaruQuant envelope.
- [ ] Each public callable contract shall explicitly choose one failure pattern: typed exception, structured result with warnings/errors, or standard research envelope. Mixed behavior is not allowed unless every branch is documented.
- [ ] The standard research envelope shall define at least `status`, `data`, `errors`, `warnings`, `audit`, `side_effect`, `approval_required`, `dry_run`, `environment`, `risk_level`, and `timing`.
- [ ] Standard research envelope `errors` and `warnings` shall use machine-readable codes, human-readable messages, optional field paths, severity, retryability, and bounded details.
- [ ] Standard research envelope `audit` shall include request ID, correlation ID where available, tool/capability name, schema version, source references where applicable, created-at timestamp, and redaction/provenance metadata.
- [ ] Standard research envelope schema must be frozen for the approved first implementation slice before any network-backed, standard helper, evidence-pack, or agent-facing research helper is implemented.
- [ ] Each public callable in the approved implementation slice shall have a behavior/error table that maps invalid input, insufficient data, unsupported config, provider unavailable, rate limit, serialization failure, resource limit, and permission failure to one exact typed exception, structured result warning/error, or standard envelope error.
- [ ] Provisional insufficient-sample behavior: research calculations should fail with a typed validation error or standard-envelope error code such as `ERR_INSUFFICIENT_SAMPLES` when the approved minimum sample size is not met; final code names and thresholds remain pending owner/architect approval.
- [ ] The first implementation slice shall be explicitly approved before Builder handoff; proposed initial slice is data preparation plus core metrics unless the owner approves a different slice.
- [ ] A contract-first checklist shall block coding until every public callable in the approved slice has input/output types, error model, determinism guarantee, side-effect classification, envelope/result shape, examples, and mapped tests.
- [ ] The module glossary shall define `Edge Lab`, `null baseline`, `profile snapshot`, `research envelope`, `advisory evidence`, `leakage report`, and `research artifact`.
- [ ] `CleaningConfig` shall describe data-cleaning behavior for timezone normalization, missing bars, non-trading periods, and spread anomalies.
- [ ] `CleaningConfig` shall define `missing_bar_strategy` with approved values such as `drop`, `forward_fill`, `interpolate`, and `none`, with deterministic behavior documented for each value.
- [ ] `CleaningConfig.missing_bar_strategy` default must be owner-approved before implementation. No Builder may infer a default or silently fill/drop bars without an approved default and explicit quality-report action.
- [ ] `CleaningConfig` shall define `non_trading_period_strategy` with approved values and shall document weekend, holiday, synthetic-bar, and provider-gap behavior.
- [ ] `clean_dataset` shall normalize timestamps to the configured timezone, resolve duplicate or non-monotonic timestamps according to `CleaningConfig`, apply configured missing-bar and non-trading-period handling, detect spread anomalies, and return both cleaned data and a `DataQualityReportModel` containing machine-readable cleaning actions and unresolved warnings.
- [ ] `EnrichmentConfig` shall describe enrichment settings for pip metadata, bar geometry, returns, labels, calendar fields, and sessions.
- [ ] `prepare_research_dataset` shall accept either in-memory raw OHLCV/OHLCVS data or a configured research data source, apply cleaning, validation, and enrichment in deterministic order, and return a `PreparedDataset` containing prepared data, metadata, and a quality report. It shall fail with a typed validation or configuration error when fatal issues prevent safe research use.
- [ ] `sma` shall compute simple moving averages over a configured window.
- [ ] `ema` shall compute exponential moving averages over a configured span.
- [ ] `std` shall compute rolling standard deviation over a configured window.
- [ ] `validate_no_lookahead_features` shall inspect declared feature metadata, column naming conventions, target/horizon columns, and configured allowed-forward columns, then return a structured leakage report identifying suspected lookahead fields, severity, evidence, and recommended action without mutating the input frame.
- [ ] `compute_session_statistics` shall calculate detailed statistics for a configured trading session.
- [ ] `run_eds_session` shall run session-edge discovery across configured session studies.
- [ ] Edge-discovery results shall include sample size, evaluated rule/config, source dataset identity, split identifiers, uncertainty metadata, warnings, and an advisory-only disclaimer.
- [ ] `exceeds_null_threshold` shall determine whether an observed value exceeds a configured null-distribution threshold.
- [ ] Bootstrap, permutation, and null-generation functions shall accept an explicit `seed` parameter or source one from a documented configuration object; returned results shall record the effective seed.
- [ ] `build_market_structure_research_profile` shall build a `MarketStructureProfile` plus configured research-only validation layers, including calibration evidence, stability summary, robustness summary, warnings, runtime metadata, and quality-adjusted confidence fields.
- [ ] `UnsupervisedResearchConfig` shall describe unsupervised research settings.
- [ ] `UnsupervisedResearchConfig` shall include a `seed` field used by non-deterministic algorithms.
- [ ] `cluster_feature_space` shall consume `UnsupervisedResearchConfig.seed` or an explicit seed parameter so K-Means output is reproducible for fixed inputs and dependency versions.
- [ ] `session_hours_payload` shall return a machine-readable payload describing configured session hours.
- [ ] `fetch_forexfactory_news` shall retrieve ForexFactory news data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, and offline-test behavior, then return a standard research envelope containing status, normalized data, provider metadata, source timestamp, warnings, errors, and audit metadata.
- [ ] `fetch_forexfactory_calendar` shall retrieve ForexFactory economic calendar data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope.
- [ ] `fetch_forexfactory_sentiment` shall retrieve ForexFactory sentiment data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope.
- [ ] `fetch_forexfactory_instrument_page` shall retrieve a symbol-specific ForexFactory page through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope.
- [ ] ForexFactory and other external-feed helpers shall be optional-provider capabilities. Missing provider adapters shall return a deterministic provider-unavailable envelope or documented typed configuration error without breaking import or unrelated research workflows.
- [ ] Persisted research artifacts shall include artifact schema version, module version, config hash, dataset identity or data hash, random seed, generated-at timestamp, timezone, source references, and dependency/version metadata required to reproduce the result.
- [ ] Persisted research artifacts shall include SHA-256 hashes of the input dataset identity or canonical data snapshot and the effective configuration used to generate the artifact.
- [ ] Network-backed research helpers shall enforce configured timeout, retry, rate-limit, cache, stale-data, and provider-layout-change behavior and shall return partial or failed results only through the standard research envelope with warnings and audit metadata.
- [ ] Seeded research workflows shall produce equivalent outputs for fixed input data, configuration, random seed, dependency versions, and artifact schema version.
- [ ] Report and artifact serialization shall prevent path traversal, accidental overwrite unless configured, and leakage of masked fields.
- [ ] Long-running workflows shall expose duration metadata and shall support configured resource limits or fail with a typed resource-limit error.
- [ ] No file-specific non-functional requirements defined.
#### `app/services/research/data.py`

Functions/classes:
- `CanonicalOHLCVSSchema`
- `validate_dataset`
- `OHLCVSchema`
- `LeakageReport`
- `MetricContext`
- `build_core_metric_profile`
- `build_market_structure_profile`
- `run_seasonality`

Requirements:
- [ ] `CanonicalOHLCVSSchema` shall define the canonical research dataset schema for OHLCV data with spread support.
- [ ] `DatasetIssue` shall represent a detected dataset quality issue.
- [ ] `CleaningAction` shall represent a cleaning action applied to research data.
- [ ] `DataQualityReportModel` shall summarize validation issues and cleaning actions for a dataset.
- [ ] `PreparedDataset` shall carry cleaned, validated, enriched data with its quality report and metadata.
- [ ] `enrich_dataset` shall add research features such as pip metadata, bar geometry, return labels, calendar fields, and session fields.
- [ ] `validate_dataset` shall validate schema, continuity, OHLC consistency, duplicate timestamps, spread quality, and volume fields while distinguishing fatal validation errors from warnings through machine-readable issue codes.
- [ ] `DataSource` shall represent the shared data-source descriptor used by research dataset validation.
- [ ] `OHLCVSchema` shall represent the shared OHLCV schema descriptor used by research dataset validation.
- [ ] `LeakageReport` shall define `suspected_columns`, `severity`, `evidence`, `recommendation`, `allowed_forward_columns`, `target_column`, and request/source metadata.
- [ ] `MetricValue` shall represent one normalized metric value with metadata.
- [ ] `MetricContext` shall provide the dataset and metadata needed by metric calculators.
- [ ] `CoreMetricProfile` shall represent a normalized profile of core dataset metrics.
- [ ] `build_core_metric_profile` shall build a normalized core metric profile from a prepared dataset.
- [ ] Metric profile output shall define units, sample size, source dataset identity, warnings, undefined-value behavior, and reproducibility metadata.
- [ ] `build_market_structure_profile` shall build a directional market-structure profile from a prepared dataset.
- [ ] `build_market_structure_robustness_report` shall report robustness of market-structure behavior across parameter or data variations.
- [ ] `ClusterModelResult` shall represent clustering labels and cluster metadata.
- [ ] `InvestmentDataSummary` shall represent descriptive statistics for investment data.
- [ ] `summarize_investment_data` shall return key descriptive statistics for investment data.
- [ ] Unsupervised modeling outputs shall include preprocessing metadata, selected feature columns, dropped columns, scaler behavior, seed, model parameters, and cluster/component diagnostics.
- [ ] `tag_sessions` shall tag each market-data row with its trading session.
- [ ] `run_seasonality` shall calculate seasonality statistics for the provided dataset and filters.
- [ ] External-feed helpers shall handle HTTP 429 responses, including missing or invalid `Retry-After` headers, through deterministic rate-limit errors or warnings with bounded retry metadata.
- [ ] `check_data_snooping_risk` shall assess data-snooping risk.
- [ ] Report persistence functions shall write to a temporary file and atomically rename where the platform supports it; unsupported atomic behavior shall be disclosed in the result metadata or typed error.
- [ ] Research artifacts shall preserve source references, assumptions, warnings, and enough metadata to reproduce the result.
- [ ] Data preparation and feature pipelines shall avoid lookahead bias and shall support explicit chronological split validation.
- [ ] Statistical results shall expose uncertainty where applicable, including p-values, confidence intervals, null percentiles, or comparable validation metadata.
- [ ] Public standard tools shall return the standard HaruQuant envelope containing status, tool metadata, request metadata, data, errors, warnings, and audit metadata.
- [ ] The module shall avoid storing real secrets, credentials, private broker data, or unredacted private artifacts.
- [ ] Proposed benchmark placeholder: `prepare_research_dataset` should process up to 1,000,000 rows in no more than 30 seconds on approved reference hardware; this remains pending until owner approval.
- [ ] No file-specific non-functional requirements defined.
#### `app/services/research/features.py`

Functions/classes:
- `build_market_regime_feature_frame`
- `calculate_regime_features`

Requirements:
- [ ] `log_returns` shall compute log returns from close prices.
- [ ] `simple_returns` shall compute arithmetic returns from close prices.
- [ ] `zscore` shall compute a close-price z-score relative to a moving average and standard deviation.
- [ ] `percent_rank` shall compute rolling percentile rank values.
- [ ] `atr` shall compute Average True Range.
- [ ] `atr_percent` shall compute ATR as a percentage of close price.
- [ ] `bollinger_bands` shall compute Bollinger-style upper, middle, and lower bands.
- [ ] `bb_width` shall compute Bollinger Band width.
- [ ] `bb_percent_b` shall compute Bollinger Band percent-B.
- [ ] `rolling_percentile_rank` shall compute rolling percentile rank for a supplied series.
- [ ] `rsi` shall compute Relative Strength Index.
- [ ] `rate_of_change` shall compute rate of change as a momentum measure.
- [ ] `momentum` shall compute simple price-difference momentum.
- [ ] `donchian_channel` shall compute Donchian breakout levels.
- [ ] `hurst_exponent` shall estimate Hurst exponent for mean-reversion versus trend detection.
- [ ] `rolling_hurst` shall compute Hurst exponent over rolling windows.
- [ ] `pivot_points` shall compute pivot, support, and resistance levels.
- [ ] `adr` shall compute Average Daily Range.
- [ ] `forward_returns` shall compute horizon-aligned forward log returns.
- [ ] `forward_max_favorable_excursion` shall compute maximum favorable price excursion over a forward horizon.
- [ ] `forward_max_adverse_excursion` shall compute maximum adverse price excursion over a forward horizon.
- [ ] `detect_volatility_regime` shall classify volatility regime using ATR percentile or equivalent volatility evidence.
- [ ] `detect_trend_regime` shall classify trend regime from moving-average relationships.
- [ ] `build_market_regime_feature_frame` shall build timestamp-aligned feature rows for PCA and clustering regime research.
- [ ] Feature functions shall define warm-up-period behavior, NaN handling, minimum window behavior, numeric precision expectations, and input mutation behavior.
- [ ] Forward-looking feature functions shall clearly label forward columns as research-only and shall be detectable by leakage checks.
- [ ] `FeatureSetFrame` shall represent the feature frame used by unsupervised modeling.
- [ ] `calculate_regime_features` shall calculate regime feature rows.
- [ ] `detect_market_regime` shall classify market regime from supplied research features.
- [ ] No file-specific non-functional requirements defined.
- [ ] `active_sessions_for_hour` shall return the active trading sessions for a given hour.
- [ ] `session_label_for_hour` shall return the session label for a given hour.
#### `app/services/research/leakage.py`

Functions/classes:
- `LeakageCheckResult`
- `validate_no_lookahead`
- `detect_feature_leakage`
- `mask_forward_columns`

Requirements:
- [ ] `TimeSplitResult` shall represent deterministic chronological train, validation, and test partitions.
- [ ] `enforce_time_split` shall enforce deterministic chronological train, validation, and test splits.
- [ ] `mask_research_artifact` shall remove or redact sensitive fields from research artifacts before persistence or sharing.
- [ ] `dump_masked_research_json` shall serialize a masked research artifact to JSON.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/research/metrics.py`

Functions/classes:
- `MetricCalculator`
- `MetricRegistry`
- `ReturnsCalculator`
- `RocCalculator`
- `CandlesCalculator`
- `RangesCalculator`
- `VolatilityCalculator`
- `SpreadCalculator`
- `VolumeActivityCalculator`
- `build_default_registry`

Requirements:
- [ ] `MetricCalculator` shall define the calculator interface for research core metrics.
- [ ] `MetricRegistry` shall register and resolve named metric calculators.
- [ ] `ReturnsCalculator` shall calculate return-related core metrics.
- [ ] `RocCalculator` shall calculate rate-of-change core metrics.
- [ ] `CandlesCalculator` shall calculate candle-geometry core metrics.
- [ ] `RangesCalculator` shall calculate range-related core metrics.
- [ ] `VolatilityCalculator` shall calculate volatility core metrics.
- [ ] `SpreadCalculator` shall calculate spread-quality core metrics.
- [ ] `VolumeActivityCalculator` shall calculate volume or activity core metrics.
- [ ] `build_default_registry` shall build the default registry of research metric calculators.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/research/studies/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/research/studies/eds.py`

Functions/classes:
- `run_eds_null_baseline`
- `run_eds_mean_reversion`
- `run_eds_trend_persistence`

Requirements:
- [ ] `run_eds_null_baseline` shall establish null-model baselines for edge-discovery studies.
- [ ] `run_eds_mean_reversion` shall evaluate a mean-reversion detector based on compression and z-score fade behavior.
- [ ] `run_eds_trend_persistence` shall evaluate a trend-persistence detector based on high-ATR breakout follow-through behavior.
- [ ] Null-model functions shall define behavior for invalid sample sizes, non-finite statistics, empty distributions, random seeds, replacement/block settings, and multiple-comparison correction applicability.
- [ ] Null-model behavior/error tables shall dictate exact outcomes for invalid sample sizes, non-finite statistics, empty distributions, invalid random seeds, invalid replacement/block settings, and inapplicable multiple-comparison corrections; these cases may not be left to Builder interpretation.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/research/studies/null_models.py`

Functions/classes:
- `compute_null_percentile`

Requirements:
- [ ] `compare_to_null` shall compare observed expectancy or performance against a null distribution.
- [ ] `get_acceptance_criteria` shall extract acceptance criteria from a null baseline.
- [ ] `block_bootstrap_ci` shall compute a confidence interval using block bootstrap resampling.
- [ ] `block_bootstrap_distribution` shall generate a bootstrap distribution for a statistic.
- [ ] `permutation_test` shall compute a permutation-test p-value.
- [ ] `random_entry_null` shall generate a null distribution from random entries in log-return space.
- [ ] `r_space_null` shall generate a null distribution in R-multiple space.
- [ ] `session_randomized_null` shall generate a null distribution by shuffling entries within the same session.
- [ ] `shuffle_returns_null` shall generate a null distribution by shuffling return blocks.
- [ ] `benjamini_hochberg` shall apply Benjamini-Hochberg false-discovery-rate correction.
- [ ] `holm_bonferroni` shall apply Holm-Bonferroni multiple-comparison correction.
- [ ] `compute_null_percentile` shall compute the percentile of an observed value within a null distribution.
- [ ] `null_distribution_stats` shall compute summary statistics for a null distribution.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Multiple-comparison checks shall be available when evaluating many hypotheses or candidates.
#### `app/services/research/studies/structure.py`

Functions/classes:
- `build_calibration_grid`
- `build_metric_calibration_grid`
- `resolve_market_structure_profile`
- `resolve_market_structure_profile_overrides`
- `parse_news_items`
- `generate_research_hypothesis`
- `build_research_evidence_pack`

Requirements:
- [ ] `TrendSwingPoint` shall represent a detected swing point used in market-structure analysis.
- [ ] `TrendLeg` shall represent a directional leg between swing points.
- [ ] `TrendScoreRow` shall represent one market-structure score row.
- [ ] `MarketStructureProfile` shall represent a reproducible directional structure profile.
- [ ] `MarketStructureCalibrationCandidate` shall represent one calibration candidate for market-structure classification.
- [ ] `classify_with_candidate` shall classify market structure using one calibration candidate.
- [ ] `build_calibration_grid` shall build candidate parameter grids for market-structure calibration.
- [ ] `evaluate_calibration_candidates` shall evaluate market-structure calibration candidates against realized evidence.
- [ ] `MarketStructureMetricCalibrationCandidate` shall represent one metric-calibration candidate.
- [ ] `build_metric_calibration_grid` shall build candidate grids for market-structure metric calibration.
- [ ] `evaluate_metric_calibration_candidates` shall evaluate metric-calibration candidates against target behavior.
- [ ] `evaluate_profile_calibration` shall evaluate profile-level calibration behavior.
- [ ] `timeframe_bucket` shall map a timeframe into a market-structure profile bucket.
- [ ] `symbol_class` shall map a symbol into a market-structure symbol class.
- [ ] `resolve_market_structure_profile` shall resolve the applicable market-structure profile for a symbol and timeframe.
- [ ] `resolve_market_structure_profile_overrides` shall resolve profile overrides for a symbol, timeframe, or profile class.
- [ ] `confidence_bucket` shall convert validation evidence into a confidence bucket.
- [ ] `label_realized_market_behavior` shall classify realized future behavior as trend, reversion, or mixed.
- [ ] `build_validation_summary` shall summarize market-structure validation evidence.
- [ ] `build_market_structure_stability_report` shall report stability of market-structure behavior across samples or windows.
- [ ] `build_strategy_fit` shall assess advisory strategy-fit evidence from market-structure research and shall not approve strategy promotion, mutate strategy runtime state, or authorize execution changes.
- [ ] Market-structure calibration outputs shall include candidate parameters, ranking criteria, validation window, stability evidence, and warnings for unstable rankings.
- [ ] `parse_news_items` shall normalize raw news items into structured research records.
- [ ] `generate_research_hypothesis` shall generate a structured research hypothesis from inputs and evidence.
- [ ] `build_research_evidence_pack` shall build a structured research evidence pack containing source references, assumptions, warnings, and validation notes.
- [ ] The module shall emit structured warnings or logs for validation failures, dropped rows, masking actions, provider failures, statistical insufficiency, and partial report generation.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] `ClassificationResult` shall represent the result of classifying a symbol's edge profile.
#### `app/services/research/studies/unsupervised.py`

Functions/classes:
- `UnsupervisedResearchRequest`
- `UnsupervisedResearchResult`
- `run_pca`
- `compute_forward_returns`
- `build_unsupervised_insight_report`

Requirements:
- [ ] `UnsupervisedResearchRequest` shall represent one unsupervised research request.
- [ ] `UnsupervisedResearchResult` shall represent a complete unsupervised research result.
- [ ] `UnsupervisedResearchService` shall orchestrate unsupervised research workflows.
- [ ] `PcaModelResult` shall represent PCA scores, loadings, and explained variance.
- [ ] `run_pca` shall run PCA on numeric feature columns and return component scores and loadings.
- [ ] `cluster_feature_space` shall cluster numeric feature rows using deterministic K-Means labels.
- [ ] `attach_cluster_labels` shall attach cluster labels to a feature frame without mutating the input.
- [ ] `PcaRiskFactor` shall represent an interpreted PCA loading or risk factor.
- [ ] `ClusterOutperformance` shall represent forward-return evidence by cluster.
- [ ] `SignalAdaptationResult` shall represent signal-suppression or signal-adaptation recommendations by cluster.
- [ ] `UnsupervisedInsightReport` shall represent a complete unsupervised insight report for trading workflows.
- [ ] `identify_pca_risk_factors` shall extract the largest PCA loadings as interpretable risk factors.
- [ ] `compute_forward_returns` shall compute horizon-aligned forward returns from a price column.
- [ ] `analyze_cluster_outperformance` shall score clusters by future returns and assign semantic regime names.
- [ ] `adapt_signals_by_cluster` shall produce advisory signal-adaptation recommendations identifying clusters where forward-return evidence is weak; it shall not mutate strategy runtime state, block live entries, or authorize execution changes.
- [ ] `build_unsupervised_insight_report` shall build a complete unsupervised insight report for trading workflows.
- [ ] No file-specific non-functional requirements defined.
#### `app/services/research/helpers.py`

Functions/classes:
- `parse_calendar_events`
- `parse_sentiment_snapshot`
- `create_news_blackout_windows`
- `calculate_returns`
- `calculate_volatility`
- `calculate_atr`
- `calculate_adr`
- `calculate_spread_statistics`
- `calculate_session_statistics`
- `calculate_seasonality_statistics`
- `calculate_correlation_matrix`
- `check_sample_size`

Requirements:
- [ ] `parse_calendar_events` shall normalize economic calendar events.
- [ ] `parse_sentiment_snapshot` shall normalize sentiment-positioning snapshots.
- [ ] `filter_events_by_symbol` shall filter calendar events by the currencies or instruments relevant to a symbol.
- [ ] `classify_news_impact` shall classify the impact level of economic news.
- [ ] `create_news_blackout_windows` shall create advisory research blackout-window recommendations around news events and shall not create live no-trade controls or mutate risk/execution policy.
- [ ] `calculate_returns` shall calculate price returns for standard research tooling.
- [ ] `calculate_volatility` shall calculate rolling annualized volatility.
- [ ] `calculate_atr` shall calculate Average True Range.
- [ ] `calculate_adr` shall calculate Average Daily Range.
- [ ] `calculate_spread_statistics` shall calculate spread distribution statistics.
- [ ] `calculate_session_statistics` shall calculate session return statistics.
- [ ] `calculate_seasonality_statistics` shall calculate calendar seasonality statistics.
- [ ] `calculate_correlation_matrix` shall calculate a correlation matrix for research inputs.
- [ ] `detect_trend_strength` shall detect trend strength from moving-average evidence.
- [ ] `detect_mean_reversion_conditions` shall detect mean-reversion conditions.
- [ ] `detect_breakout_conditions` shall detect breakout conditions.
- [ ] `score_research_hypothesis` shall score research evidence quality.
- [ ] `check_sample_size` shall validate whether a sample is large enough for the intended research claim.
- [ ] `check_lookahead_bias_risk` shall assess lookahead-bias risk.
- [ ] `check_hypothesis_testability` shall assess whether a hypothesis is testable.
- [ ] `check_contradictory_evidence` shall assess whether evidence contradicts the proposed hypothesis.
- [ ] Network-backed research helpers shall be isolated from core deterministic calculations and shall be skippable in offline or heavy-environment tests.
- [ ] Serialization helpers shall support masked JSON or Markdown output without leaking sensitive source details.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] The module shall be sandboxed and shall not place, modify, cancel, or route live orders.
- [ ] Research outputs shall clearly distinguish observations, assumptions, warnings, and validation evidence from approved trading decisions.
- [ ] Standard tool envelopes shall include side-effect, approval-required, dry-run, environment, risk-level, and timing audit fields.
- [ ] The standard research envelope schema shall be versioned and referenced by every network-backed helper, standard helper, evidence-pack helper, and future agent-facing research tool.
- [ ] Public exports shall remain unique and resolvable through the lazy namespace.
- [ ] The module shall remain interoperable with analytics, optimization, risk, and execution modules only through documented public contracts.
- [ ] `ResearchResourceLimits` shall define `max_duration_seconds`, `max_memory_mb`, `max_rows`, and behavior when a limit is exceeded.
- [ ] Before production Builder handoff, the owner shall approve measurable resource targets for the first implementation slice, including maximum rows, runtime budget, memory budget, and reference hardware.
- [ ] `run_session_breakout_strategy` shall evaluate an opening-range breakout strategy for a session.
- [ ] `run_session_fade_strategy` shall evaluate a mean-reversion fade strategy within a session.
- [ ] `EdgeClass` shall represent the classification category assigned to an edge.
- [ ] `EdgeSummary` shall summarize mean-reversion and trend-persistence evidence for a symbol.
- [ ] `classify_symbol` shall classify a symbol based on mean-reversion and trend-persistence evidence.
- [ ] `SeasonalityFilters` shall describe calendar, session, or symbol filters for seasonality analysis.
- [ ] `calmar_ratio` shall expose the analytics Calmar ratio for research workflows.
- [ ] `expectancy` shall expose the analytics expectancy calculation for research workflows.
- [ ] `max_drawdown` shall expose the analytics maximum drawdown calculation for research workflows.
- [ ] `median_mae_mfe` shall expose the analytics median MAE/MFE calculation for research workflows.
- [ ] `profit_factor` shall expose the analytics profit-factor calculation for research workflows.
- [ ] `sharpe_ratio` shall expose the analytics Sharpe ratio calculation for research workflows.
- [ ] `sortino_ratio` shall expose the analytics Sortino ratio calculation for research workflows.
- [ ] `win_rate` shall expose the analytics win-rate calculation for research workflows.
#### `app/services/research/reporting.py`

Functions/classes:
- `save_markdown`
- `save_json`
- `generate_multi_symbol_report`
- `build_edge_profile_snapshot`
- `build_profile_summary`
- `build_dashboard_summary`
- `save_json_report`
- `save_markdown_report`
- `build_edge_lab_scorecard_report`

Requirements:
- [ ] `result_to_markdown` shall convert an edge result into a Markdown report.
- [ ] `result_to_summary` shall generate a concise summary dictionary from an edge result.
- [ ] `save_markdown` shall persist an edge result report as Markdown and shall expose an `overwrite: bool` contract.
- [ ] `save_json` shall persist an edge result report as JSON and shall expose an `overwrite: bool` contract.
- [ ] `generate_multi_symbol_report` shall generate a combined report for multiple symbols.
- [ ] `print_result_summary` shall print a concise result summary to console.
- [ ] `build_edge_profile_snapshot` shall build a normalized snapshot payload from progressive Edge Lab tab results.
- [ ] `build_profile_summary` shall build a concise dashboard-ready summary from one profile snapshot.
- [ ] `build_dashboard_summary` shall build a UI or dashboard summary block from one profile snapshot.
- [ ] `snapshot_report_json` shall build a machine-readable profile snapshot report.
- [ ] `snapshot_report_markdown` shall render a human-readable profile snapshot report.
- [ ] `comparison_report_markdown` shall render a Markdown comparison report from two profile snapshots.
- [ ] `save_json_report` shall save one complete JSON profile report.
- [ ] `save_markdown_report` shall save one complete Markdown profile report.
- [ ] `build_edge_lab_scorecard_report` shall build a deterministic backend scorecard report from progressive Edge Lab outputs.
- [ ] Report persistence functions shall define allowed output paths, overwrite behavior, atomic write behavior, encoding, masking behavior, permission-failure behavior, and return value.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/research/errors.py`

Functions/classes:
- `Error`
- `ValidationError`
- `ConfigurationError`

Requirements:
- [ ] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom research exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
### Unit Tests Required

```text
tests/unit/app/services/research/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/12_research.py
```

Usage examples must show:
- `example_01_research_config_and_data_prep`: Demonstrate research config validation, data preparation, cleaning, and quality reports.
- `example_02_feature_engineering`: Demonstrate returns, volatility, range, momentum, Bollinger-style stats, Hurst, pivots, and regimes.
- `example_03_leakage_controls`: Demonstrate chronological splits, no-lookahead checks, forward-column masking, and leakage failures.
- `example_04_edge_studies`: Demonstrate mean reversion, trend persistence, session behavior, and null baseline studies.
- `example_05_statistical_validation`: Demonstrate bootstrap, permutation tests, null models, multiple-comparison correction, and thresholds.
- `example_06_market_structure`: Demonstrate market-structure profiles, calibration candidates, overrides, and stability summaries.
- `example_07_unsupervised_analysis`: Demonstrate PCA, clustering, labels, outperformance analysis, and risk-factor summaries.
- `example_08_research_reports`: Demonstrate markdown/json reports, profile snapshots, dashboard summaries, and advisory-only boundaries.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 290 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(research-edge-lab): implement phase 12 research edge lab requirements
```


- [ ] The module shall fail closed when a workflow attempts to mutate live trading state or bypass governance.
- [ ] Until resource limits and reference hardware are approved, Research may not claim production-grade performance; oversized or long-running workflows must fail with a typed resource-limit error or standard-envelope resource-limit error instead of attempting unbounded work.
## Phase 13 Conversation AI Layer

### Goal

Implement the Conversation AI Layer requirements under `app/services/conversation/` while preserving the phase module boundaries and governance rules.

Task inventory: 249 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

- Target implementation area: `app/services/conversation/`.
- Requires Phase 12 Research Edge Lab contracts to be available where referenced by `13_conversation.md`.

### Files to Create

```text
app/services/conversation/
app/services/conversation/__init__.py
app/services/conversation/service.py
app/services/conversation/config.py
app/services/conversation/retention.py
app/services/conversation/prompt_builder.py
app/services/conversation/ceo_gateway.py
app/services/conversation/memory.py
app/services/conversation/context/__init__.py
app/services/conversation/context/service.py
app/services/conversation/context/builders.py
app/services/conversation/providers/__init__.py
app/services/conversation/providers/stream.py
app/services/conversation/errors.py
app/utils/errors.py
```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/conversation/__init__.py`

Functions/classes:
- `list_ceo_chat_tools`

Requirements:
- [ ] Package initialization shall standardize conversation domain export metadata with tool category `conversation`.
- [ ] `list_ceo_chat_tools` shall list chat tool definitions available to the CEO chat workflow.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/conversation/service.py`

Functions/classes:
- `ConversationService`
- `PageContextService`

Requirements:
- [ ] `ConversationService` public methods shall document whether they mutate persistent state, emit audit events, require user ownership checks, or trigger retention escalation.
- [ ] Package initialization shall make `ConversationService` importable from `app.services.conversation`.
- [ ] `ConversationService` shall provide durable chat operations used by the UI API and CEO gateway.
- [ ] `ConversationService` shall provide the durable conversation API for UI API and CEO gateway callers, including thread lifecycle, redacted message persistence, retention detail, context metadata update, export, memory summary retrieval, pinned fact retrieval, and governed action draft operations.
- [ ] Request IDs shall be generated by the API/UI gateway or service caller using the approved Utils identity helper once available; missing request IDs may be generated by `stream_turn`, but malformed, oversized, or unsafe request IDs shall return a documented validation error.
- [ ] `ConversationRetentionService` shall apply lifecycle, archival, legal-hold, and purge rules through the repository.
- [ ] `ConversationMemoryService` shall keep durable memory separate from ephemeral page context.
- [ ] `PageContextService` shall build compact page context without persisting it as durable memory.
- [ ] `PageContextService.from_chat_request` shall expose `from_chat_request` behavior that builds page context from a chat request's route, page title, session id, symbol, timeframe, DOM snapshot, and page intelligence.
- [ ] Tool plans shall be read-only unless routed through separate governed services outside the conversation module.
- [ ] The API/UI Gateway or an approved authorization service shall own authentication, identity validation, and final permission authority for read-only tool evidence. Conversation owns only permission result consumption, evidence inclusion rules, and prompt/audit handling.
- [ ] The repository contract shall define how SQLite launch persistence maps thread IDs, user IDs, request IDs, lifecycle events, JSON metadata, booleans, timestamps, and version fields without exposing raw database rows at public service boundaries.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Each public capability shall document whether it is a stable public API, internal helper, official callable tool, or experimental export.
- [ ] Conversation persistence shall redact secrets before storing user or assistant message content.
- [ ] Standard and regulated inactive conversations shall be archived rather than immediately purged.
- [ ] Security-sensitive logs shall never include unredacted message text, secrets, provider keys, action draft payload secrets, or raw tool evidence containing credentials.
- [ ] The package-level domain registry shall remain explicit about no exposed conversation function tools when `__all__` is empty.
- [ ] `app.services.conversation.__all__` shall remain the package-level exposed function-tool registry for the conversation domain.
- [ ] `app.services.conversation.__all__` shall be allowed to be empty when no conversation functions are registered as external tools.
- [ ] Duplicate chat turn requests shall be idempotent by `(user_id, thread_id, request_id)` and shall not create duplicate user messages, duplicate assistant messages, duplicate action drafts, or duplicate lifecycle events.
- [ ] `list_threads` shall list a user's threads, optionally include archived threads, apply a limit, and filter by case-insensitive title query when supplied.
- [ ] `rename_thread` shall trim a supplied title, fall back to the default title when the result is empty, persist the title, and return updated thread detail.
- [ ] `delete_thread` shall soft-delete a user's thread and return whether the operation succeeded.
- [ ] `archive_thread` shall archive a user's thread with a lifecycle reason and return updated thread detail.
- [ ] `restore_thread` shall restore an archived thread with a lifecycle reason and return updated thread detail.
- [ ] `update_context` shall persist the current route, page type, and active context revision for a thread.
- [ ] `add_message` shall persist a redacted chat message with role, request id, context revision, tool calls, linked signal proposal, linked action draft, metadata, and latency.
- [ ] `add_message` on archived or deleted threads shall return a documented machine-readable error or exception shape before implementation.
- [ ] `add_message` shall mark a thread regulated when a message links to a signal proposal or action draft.
- [ ] `export_thread` shall export a thread as JSON when requested and record an export lifecycle event.
- [ ] `export_thread` shall export a thread as Markdown by default and record an export lifecycle event.
- [ ] `export_thread` shall include CEO workflow metadata for assistant messages when response metadata is available.
- [ ] `create_action_draft` shall create a governed action draft with generated draft id, request id, draft type, title, description, payload, risk precheck status, risk notes, and required human approval.
- [ ] `create_action_draft` shall validate payloads against a versioned schema for each supported draft type before persistence.
- [ ] `create_action_draft` shall mark the conversation regulated because action drafts are governed artifacts.
- [ ] `list_action_drafts` shall list a user's action drafts, optionally filtered by thread id and status.
- [ ] `ActionDraftRecord` shall represent draft id, thread id, user id, request id, draft type, title, description, payload, risk precheck status, approval id, status, human approval requirement, side-effect status, governed workflow id, execution intent id, execution receipt id, and timestamps.
- [ ] `utc_now` shall return the current UTC timestamp.
- [ ] `to_sqlite_timestamp` shall convert datetimes to UTC SQLite-compatible timestamp strings without microseconds.
- [ ] `apply_legal_hold` shall place a thread on legal hold, clear expiry and purge dates, and store legal-hold reason and optional end date.
- [ ] `run_lifecycle` shall skip legal-hold threads, purge deleted threads past purge date, purge expired ephemeral threads, and archive inactive standard or regulated threads past the archive threshold.
- [ ] `maybe_refresh_summary` shall return the latest existing summary until the message-count cadence is reached.
- [ ] `maybe_refresh_summary` shall create a new deterministic rolling summary when the cadence threshold is met.
- [ ] `list_pinned_facts` shall return pinned facts for a user's thread.
- [ ] `build_rolling_summary` shall create a compact deterministic summary from recent user and assistant turns without requiring an LLM provider.
- [ ] `compact_dom_snapshot` shall compact DOM title, headings, text excerpt, tables, semantic blocks, and actionable elements within fixed limits.
- [ ] `entity_refs_from_state` shall create entity references for session, symbol, timeframe, and selected UI entities.
- [ ] `build_compact_context` shall create a bounded `PageContext` with schema version, route, page type, page title, entity refs, context revision, freshness, authority, summary, and payload.
- [ ] Conversation shall not present unsupported live market conditions, strategy suitability, volatility, regime, or price-action claims as facts.
- [ ] Conversation shall not claim to execute trades or irreversible actions from chat.
- [ ] Usage examples shall include expected return shape or representative output for each public capability shown.
- [ ] Repository behavior shall define transactional boundaries, isolation expectations, conflict detection, optimistic version or per-thread lock behavior, idempotency lookup/write behavior, partial-failure handling, retryability, and machine-readable persistence error codes.
- [ ] Concrete non-functional targets shall be approved or explicitly deferred from release scope before production-readiness claims are made.
- [ ] `ConversationRepository` shall be defined as a Python protocol, abstract base class, or companion persistence contract before implementation.
- [ ] Deterministic fallback responses shall use a documented schema, not free-form implicit text.
#### `app/services/conversation/config.py`

Functions/classes:
- `list_threads`
- `get_thread`
- `redact_sensitive_text`
- `PromptBuilder`
- `ModelConfigurationError`
- `OpenAICompatibleStreamClient`
- `is_configured`
- `is_configured_for`
- `thread_id`

Requirements:
- [ ] Each public capability shall document machine-readable error codes for validation, authorization, idempotency, concurrency, provider, persistence, configuration, cancellation, and internal failure paths.
- [ ] `list_threads` and `get_thread` shall define default limits, maximum limits, and behavior when requested limits exceed configured maximums.
- [ ] `add_message` shall refresh durable memory summaries on the configured cadence.
- [ ] `redact_sensitive_text` shall redact configured secret patterns, email addresses, and long numeric identifiers from persisted text.
- [ ] Retention durations, archive thresholds, purge delays, and legal-hold release behavior shall be loaded from a validated retention policy configuration with documented local-development defaults and explicit production overrides.
- [ ] The retention policy configuration schema and local-development defaults shall be committed with this specification or a referenced companion specification before lifecycle tests are accepted.
- [ ] `normalize_text` shall collapse whitespace and truncate text to a configured limit.
- [ ] `PromptBuilder.build` shall include only the configured maximum number of recent user/assistant messages.
- [ ] `ModelConfigurationError` shall represent missing or invalid model runtime configuration.
- [ ] `ModelRuntimeError` shall represent configured provider runtime failure.
- [ ] `OpenAICompatibleStreamClient` shall select providers based on model names and configured environment variables.
- [ ] `OpenAICompatibleStreamClient.is_configured` shall expose `is_configured` behavior that reports whether any supported provider credentials are available.
- [ ] `OpenAICompatibleStreamClient.is_configured_for` shall expose `is_configured_for` behavior that reports whether a specific model can be served by its inferred provider.
- [ ] OpenAI streaming shall require a configured API key and stream chat-completion deltas.
- [ ] Google/Gemini streaming shall require a configured API key and installed provider SDK.
- [ ] Ollama streaming shall use the configured local Ollama base URL and report configuration/runtime errors when unreachable or failing.
- [ ] Provider failure after partial token streaming shall emit a documented degraded terminal event and shall not replace already-streamed content with deterministic fallback text unless explicitly configured.
- [ ] `stream_turn` shall use model streaming only when chat is enabled, a model is selected, and the provider is configured.
- [ ] `stream_turn` shall degrade to fallback responses when the model is disabled, not configured, blocked, or unavailable before tokens are produced.
- [ ] Import-time behavior shall not configure providers, open databases, run migrations, load `.env`, contact networks, start background tasks, or register live side-effecting tools.
- [ ] Provider streaming shall fail over to deterministic fallback text when model configuration or provider runtime fails before output is produced.
- [ ] All retention lifecycle decisions shall be deterministic for a supplied clock and retention policy configuration.
- [ ] Deleted conversations shall only purge after the configured purge delay unless retention class blocks purging.
- [ ] Model-provider configuration shall be environment-driven and shall not require hardcoded secrets.
- [ ] The retention policy configuration schema shall be approved before lifecycle implementation. The schema shall define retention classes, durations, archive thresholds, purge delays, legal-hold release behavior, local-development defaults, production override requirements, and validation errors.
- [ ] The Conversation configuration reference shall be approved before implementation. The reference shall enumerate prompt budgets, context budgets, provider timeouts, stream buffering limits, active-stream memory limits, import-time expectations, lifecycle batch limits, summary cadence, and fallback behavior.
- [ ] Requirement-to-test traceability shall map every accepted public contract, configuration value, event type, error code, concurrency rule, and retention rule to tests.
- [ ] Fallback metadata shall include `generation_source`, `fallback_reason`, `model_requested`, `provider_label`, `provider_configured`, `tokens_started`, `request_id`, `thread_id`, and redacted tool/evidence availability state.
- [ ] Fallback text shall be bounded by configuration and shall not invent market data, risk approval, backtest results, owner decisions, or provider behavior.
- [ ] Conversation configuration shall define names, types, default values, validation rules, environment override behavior, and failure behavior for every runtime-configurable value.
- [ ] Retention configuration values shall include standard retention duration, ephemeral retention duration, regulated retention duration or no-expiry behavior, archive inactivity thresholds, deleted-thread purge delay, legal-hold release behavior, lifecycle batch size, and lifecycle time budget. Concrete values are Pending owner approval.
- [ ] Prompt and context configuration values shall include maximum page-context characters, DOM snapshot characters, page-intelligence characters, tool-evidence characters, memory summary characters, pinned fact count, recent message count, per-message characters, total prompt budget, and truncation strategy. Concrete values are Pending owner approval.
- [ ] Streaming configuration values shall include provider timeout, retry count, no-retry conditions, fallback chunk size, fallback delay, outgoing event buffer limit, backpressure policy, active-stream memory budget, and cancellation persistence behavior. Concrete values are Pending owner approval.
- [ ] Import-time configuration expectations shall define the maximum allowed side effects and optional dependency behavior; concrete timing targets are Pending benchmark approval.
- [ ] Observability configuration values shall include telemetry field names, audit sink expectations, redaction-before-log requirements, prompt composition log sampling or retention, provider degradation metadata, and security-sensitive log exclusions.
- [ ] Developers MUST NOT implement retention durations, prompt budgets, stream buffer limits, provider timeouts, or lifecycle limits as hardcoded constants; they MUST be loaded from the approved configuration schema with injectable test overrides.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Importing `app.services.conversation` shall not require provider credentials, network access, database access, optional provider SDKs, or model availability.
- [ ] Chat shall remain usable when LLM providers are disabled or unavailable.
- [ ] `ActionDraftRecord.model_dump` shall expose `model_dump` behavior that returns a dictionary copy suitable for API serialization.
- [ ] Provider calls shall use documented timeout, retry, and no-retry conditions.
- [ ] Short follow-up detection and pending research context merge rules shall be explicitly defined before implementation, including token/sentence limits, accepted answer shapes, and conflict behavior when the follow-up is ambiguous.
- [ ] Conversation shall describe unavailable evidence as pending instead of inventing market data, backtest results, risk approvals, owner decisions, or provider behavior.
- [ ] Usage examples shall include at least one invalid-input example and one provider-disabled fallback example.
- [ ] Provider-disabled fallback shall emit a metadata event before token events and a terminal `done` event with `generation_source="deterministic_fallback"`.
#### `app/services/conversation/retention.py`

Functions/classes:
- `create_thread`
- `set_thread_retention_class`
- `ConversationRepository`

Requirements:
- [ ] Conversation mutations shall enforce user ownership before reading, writing, exporting, deleting, archiving, restoring, updating retention, creating action drafts, or listing action drafts.
- [ ] Conversation mutations that affect thread state, message state, action draft state, retention state, or lifecycle audit state shall be atomic where consistency is required.
- [ ] Repository operations used by thread creation, message persistence, action draft creation, retention escalation, export audit logging, and lifecycle updates shall return explicit failure results or raise documented exceptions on partial failure.
- [ ] Concurrent conversation mutations shall preserve consistent thread, message, retention, and audit state or return a documented conflict/failure result.
- [ ] `create_thread` shall create a thread for a user, assign a generated thread id, default the title when absent, persist route/page/context metadata, initialize retention policy, and return full thread detail.
- [ ] Archived thread behavior shall be explicitly defined for message addition, context update, export, retention changes, and action draft creation.
- [ ] Deleted thread behavior shall be explicitly defined for read, restore, export, retention detail, message addition, action draft creation, and lifecycle purge.
- [ ] `retention_detail` shall return retention policy detail and lifecycle audit events for a user's thread, including deleted threads, and shall raise a lookup error when missing.
- [ ] `set_thread_retention_class` shall support `ephemeral`, `regulated`, `legal_hold`, and `standard` retention classes.
- [ ] `set_thread_retention_class` shall define whether changing to the current retention class is a no-op, lifecycle event, or validation error before implementation.
- [ ] `set_thread_retention_class` shall reject unsupported retention classes with a value error.
- [ ] `RetentionDecision` shall represent one retention lifecycle decision with action, thread id, and reason.
- [ ] `retention_expiry_for` shall calculate expiration timestamps only for supported retention classes and shall either reject unknown retention classes with a documented error or treat them according to an explicitly documented fail-closed default.
- [ ] `purge_after_for` shall return no purge date for regulated or legal-hold threads and otherwise align purge timing with retention expiry.
- [ ] `initialize_thread_policy` shall initialize thread retention with class, expiry, purge date, and lifecycle reason.
- [ ] `mark_regulated` shall upgrade non-regulated threads to regulated retention and preserve already regulated or legal-hold threads.
- [ ] `set_ephemeral` shall set ephemeral retention for eligible threads and shall not downgrade regulated or legal-hold threads.
- [ ] `release_legal_hold` shall return a legal-hold thread to regulated retention and clear legal-hold fields.
- [ ] Regulated chat artifacts shall trigger regulated retention handling.
- [ ] Conversation shall preserve user ownership boundaries for threads, messages, retention detail, pinned facts, and action drafts.
- [ ] Retention lifecycle actions shall be auditable and shall respect legal hold before archive, delete, or purge behavior.
- [ ] Regulated and legal-hold retention classes shall not be downgraded by ephemeral retention requests.
- [ ] A `ConversationRepository` contract or companion persistence specification shall be approved before implementation. The contract shall define thread, message, memory summary, pinned fact, action draft, retention policy, lifecycle audit, export audit, idempotency, and locking/version operations.
- [ ] The repository contract shall define method signatures or operation records for creating, reading, listing, renaming, archiving, restoring, soft-deleting, exporting, and retention-updating threads.
- [ ] The repository contract shall define transaction scopes for operations that must update multiple records, including thread creation with retention policy, message persistence with title update or retention escalation, action draft creation with retention escalation, export with lifecycle audit event, and legal-hold changes.
- [ ] The repository contract shall define conflict signals for version mismatch, active-turn lock conflict, duplicate request replay, duplicate request material mismatch, retention race, lifecycle race, and partial persistence failure.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/conversation/prompt_builder.py`

Functions/classes:
- `generate_thread_title`
- `get_context_builder`
- `build_page_context`
- `PromptBuilder`
- `CEOChatGateway`

Requirements:
- [ ] Public conversation exports shall be documented in a capability contract table before Builder handoff.
- [ ] `add_message` shall auto-title default conversation threads from the first user prompt.
- [ ] `add_message` shall define the fallback title format for empty, whitespace-only, redacted-empty, or too-short first prompts before implementation.
- [ ] `generate_thread_title` shall generate a compact thread title from the prompt and use a fallback when the prompt is empty.
- [ ] `get_context_builder` shall resolve the context builder for a page type or route.
- [ ] `build_page_context` shall route page-context creation to the appropriate specialized builder.
- [ ] `PromptBuildResult` shall contain the composed chat messages and prompt-composition audit log.
- [ ] `PromptBuilder.build` shall expose `build` behavior that includes the highest-authority governance system prompt first.
- [ ] `PromptBuilder.build` shall include user-attached read-only tool hints when supplied.
- [ ] `PromptBuilder.build` shall include read-only tool evidence when supplied and instruct the model not to guess when tools are unavailable.
- [ ] Prompt building shall reject or quarantine tool evidence that lacks required provenance, permission status, freshness metadata, retrieval timestamp, or read-only classification.
- [ ] `PromptBuilder.build` shall append the current user prompt last.
- [ ] `PromptBuilder.build` shall return a composition log with layer authority, inclusion state, character counts, token estimates, message count, route, and truncation state.
- [ ] Prompt composition shall compact oversized page context to a bounded representation.
- [ ] `CEOChatGateway` shall run chat turns through context assembly, planner routing, read-only evidence tools, CEO memo creation, prompt building, model/fallback response generation, metadata creation, and message persistence.
- [ ] Read-only tool attachment and evidence inclusion shall require an explicit permission check for the requesting user, thread, route, and target data scope before tool hints or evidence are included in prompt composition.
- [ ] Conversation context shall be compacted to bounded payload sizes before prompt inclusion.
- [ ] Prompt composition shall complete within a documented latency budget for normal bounded inputs.
- [ ] Prompt composition shall produce auditable layer metadata for governance and debugging.
- [ ] Authorization context and read-only evidence permission contracts shall be approved before tool evidence can be included in prompts. The contract shall define how principal identity, roles, permissions, scopes, route, thread, and target data scope are passed and denied.
- [ ] Public capability contracts shall be approved before Builder handoff, including machine-readable error codes rather than only exception class names.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/conversation/ceo_gateway.py`

Functions/classes:
- `CEOChatGateway`

Requirements:
- [ ] `CEOChatGateway` shall record telemetry, usage/cost metadata when available, deterministic-decision metadata, planner metadata, CEO memo metadata, page context, attached tools, tool results, generation source, and provider name.
- [ ] CEO gateway events shall support streaming UI consumption through progress, metadata, token, and completion events.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Read-only tool evidence shall include provenance where available and shall not silently become authority for side effects.
- [ ] `get_action_draft` shall return one action draft for a user and shall raise a lookup error when missing.
- [ ] Action drafts shall remain proposals and shall not execute directly from the conversation module.
- [ ] Tool evidence rejection or quarantine shall have a documented result shape, excluded-layer composition log entry, and security/audit metadata before implementation.
- [ ] Action drafts shall require human approval and shall preserve side-effect status as draft-only unless external governance changes it.
- [ ] Usage examples shall include an action draft creation example that demonstrates draft-only side-effect status and human approval requirement.
#### `app/services/conversation/memory.py`

Functions/classes:
- `get_thread`
- `PromptBuilder`

Requirements:
- [ ] `get_thread` shall return a user's thread detail with thread fields, messages, latest memory summary, and pinned facts, and shall raise a lookup error when the thread is missing.
- [ ] `PromptBuilder` shall build layered, auditable prompts from thread, memory, pinned facts, page context, route decision, tool evidence, recent messages, and the current user prompt.
- [ ] `PromptBuilder.build` shall include memory summary and pinned facts only when available.
- [ ] `PromptBuilder.build` shall always include current page context and shall prefer it over stale thread memory for page-specific questions.
- [ ] Page context, tool evidence, memory summary, pinned facts, and recent-message layers shall each have documented maximum character or token budgets.
- [ ] Concrete NFR targets for prompt composition latency, import-time latency, stream startup latency, active-stream memory, event buffer limits, lifecycle batch duration, and export size shall be approved before production-readiness claims.
- [ ] Streaming shall support backpressure or bounded buffering so slow UI consumers do not cause unbounded memory growth.
- [ ] Page context shall remain ephemeral and shall not become durable memory unless explicitly persisted through thread context metadata.
- [ ] The repository contract shall define method signatures or operation records for adding messages, reading messages, detecting duplicate request IDs, storing message metadata, storing action drafts, reading action drafts, listing action drafts, storing memory summaries, listing pinned facts, and writing lifecycle audit events.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/conversation/context/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/conversation/context/service.py`

Functions/classes:
- `ConversationContextService`
- `get_page_context`
- `assemble_conversation_context`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] `update_context` shall record a lifecycle audit event when the active context revision changes.
- [ ] `ContextAssembler` shall act as the canonical page-context assembler alias for routes and chat tools.
- [ ] `infer_page_type` shall infer page type from explicit hint or route text.
- [ ] `compact_page_intelligence` shall compact page identity, selected entities, visible metrics, visible tables, visible charts, filters, user selection, action affordances, and freshness metadata.
- [ ] `freshness_payload` shall describe the freshness and source of context data.
- [ ] `build_dashboard_context` shall build context for dashboard pages.
- [ ] `build_data_workspace_context` shall build context for data workspace pages.
- [ ] `build_strategy_detail_context` shall build context for strategy detail pages.
- [ ] `build_backtest_detail_context` shall build context for backtest or simulation detail pages.
- [ ] `build_optimization_context` shall build context for optimization pages.
- [ ] `build_portfolio_risk_context` shall build context for portfolio risk pages.
- [ ] `build_live_trading_context` shall build context for live trading pages.
- [ ] `build_operator_workflow_context` shall build context for operator workflow pages.
- [ ] `build_generic_context` shall build fallback context for unrecognized pages.
#### `app/services/conversation/context/builders.py`

Functions/classes:
- `PageContextBuilder`
- `DashboardContextBuilder`
- `StrategyContextBuilder`
- `BacktestContextBuilder`
- `LiveTradingContextBuilder`
- `build_page_context`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/conversation/providers/__init__.py`

Functions/classes:
- `__all__`

Requirements:
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/conversation/providers/stream.py`

Functions/classes:
- `OpenAICompatibleStreamClient`
- `StreamManager`
- `thread_id`
- `user_id`

Requirements:
- [ ] `CEOChatGateway.stream_turn` shall document stable event names, event ordering, required payload fields, terminal event behavior, cancellation behavior, degraded-provider behavior, and error event behavior.
- [ ] Concurrent `stream_turn` calls for the same `(user_id, thread_id)` shall use an approved serialization mechanism, optimistic version check, or documented conflict event such as `concurrent_turn_in_progress`; the final mechanism is Pending.
- [ ] `StreamCancelled` shall represent a cancelled response stream.
- [ ] `OpenAICompatibleStreamClient.provider_for_model` shall expose `provider_for_model` behavior that infers `ollama`, `openai`, or `google` from model prefixes or names.
- [ ] `OpenAICompatibleStreamClient.provider_label_for_model` shall expose `provider_label_for_model` behavior that returns a user-facing provider label.
- [ ] `OpenAICompatibleStreamClient.stream_chat` shall expose `stream_chat` behavior that streams chat tokens through Ollama, Google/Gemini, or OpenAI-compatible APIs according to provider selection.
- [ ] Streaming shall collect provider usage metadata when available.
- [ ] Stream cancellation shall stop provider streaming, persist cancellation metadata when appropriate, and emit a documented terminal cancellation event.
- [ ] `StreamManager.text_tokens` shall expose `text_tokens` behavior that splits fallback text into deterministic chunks and optionally delays between chunks.
- [ ] `handle_turn` shall consume the streaming workflow and return the final chat turn result from the completed event.
- [ ] `handle_turn` shall raise a runtime error if the streaming workflow never completes.
- [ ] `stream_turn` shall emit progress events for request receipt, context assembly, planner route selection, tool planning, evidence completion, response composition, streaming, and completion.
- [ ] `stream_turn` shall generate a request id when the request does not provide one.
- [ ] `stream_turn` shall update thread page context before reading thread state.
- [ ] `stream_turn` shall avoid duplicate user-message persistence when a request id already exists in the thread.
- [ ] `stream_turn` shall merge pending research context when a short follow-up appears to answer a prior data-window clarification.
- [ ] `stream_turn` shall route through the planner and derive CEO route decisions from the plan, request, and page context.
- [ ] `stream_turn` shall execute only planned read-only tool calls through the read-only tool executor.
- [ ] `stream_turn` shall return deterministic needs-input progress when required clarification or market evidence is missing.
- [ ] `stream_turn` shall run the research workflow only when the planner intent is research and successful market-data evidence is available.
- [ ] `stream_turn` shall run direct news sentiment specialist handling only through approved routing conditions.
- [ ] `stream_turn` shall block deterministic direct specialist or live-execution requests instead of invoking live mutations.
- [ ] `stream_turn` shall persist assistant responses with metadata, latency, context revision, and tool-call metadata.
- [ ] `stream_turn` shall emit `meta`, `token`, progress, and `done` events for UI consumption.
- [ ] `stream_turn` shall emit events using a documented schema with stable event names, required payload fields, ordering guarantees, terminal event rules, cancellation event rules, error event rules, degraded-provider event rules, and backward-compatibility expectations for UI consumers.
- [ ] `stream_turn` shall emit a documented conflict/error event when a same-thread concurrent turn cannot be serialized safely.
- [ ] Redaction shall occur before persistence, audit logging, telemetry, stream metadata, dead-letter diagnostics, and security-sensitive logs.
- [ ] The stream event contract shall be approved before UI integration or gateway implementation. The contract shall define event names, payload fields, ordering, heartbeats if applicable, terminal events, cancellation, provider-degraded events, backpressure events, and error events.
- [ ] The repository contract shall define whether conflict and failure behavior is surfaced as typed exceptions, standard result objects, or gateway stream events at each boundary.
- [ ] The stream contract shall define canonical event names for request receipt, context assembly, planner route selection, tool planning, evidence completion, needs-input, response composition, metadata, token, provider-degraded, cancellation, error, backpressure, conflict, and done.
- [ ] Every stream event payload shall include `event_type`, `schema_version`, `request_id`, `thread_id`, `user_id` or redacted actor reference, `timestamp`, `correlation_id` where available, and event-specific payload fields.
- [ ] Token events shall define text chunk field names, ordering index behavior, provider/fallback source metadata, and whether empty chunks are allowed.
- [ ] Metadata events shall define planner metadata, CEO memo metadata, model/provider metadata, tool evidence status, prompt composition summary, usage metadata, latency metadata, and redaction status.
- [ ] Terminal events shall be mutually exclusive and shall include success, needs-input, cancelled, provider-degraded-complete, failed, and conflict terminal states.
- [ ] Error events shall include a machine-readable error code, severity, retryability, user-safe message, redacted details, and persistence state where available.
- [ ] Cancellation events shall define behavior before first token, after partial tokens, and during final persistence.
- [ ] Backpressure events shall define whether events are buffered, dropped, coalesced, or fail-fast; exact limits are Pending until NFR targets are approved.
- [ ] Provider failure before first token may use deterministic fallback text; provider failure after partial tokens shall emit a degraded terminal event and shall not replace already-streamed content unless an approved policy explicitly permits replacement.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
#### `app/services/conversation/errors.py`

Functions/classes:
- `Error`
- `ValidationError`
- `ConfigurationError`

Requirements:
- [ ] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom conversation exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.
- [ ] Each public capability shall document intended consumers, input schema, output schema, documented errors, side effects, authorization expectations, idempotency behavior, risk level, network behavior, persistence behavior, and stability.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
### Unit Tests Required

```text
tests/unit/app/services/conversation/
```

Test coverage:
- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text
tests/usage/app/services/13_conversation.py
```

Usage examples must show:
- `example_01_thread_lifecycle`: Demonstrate create, list, read, rename, archive, restore, soft delete, export, and context updates.
- `example_02_memory_and_retention`: Demonstrate rolling summaries, pinned facts, retention classes, archival, purge, and legal hold behavior.
- `example_03_redaction`: Demonstrate secret, email, long-number, broker-like payload, and persisted-text redaction.
- `example_04_page_context`: Demonstrate route-aware context builders for dashboard, data, strategy, backtest, optimization, risk, live, and operator pages.
- `example_05_prompt_builder`: Demonstrate governance instructions, memory, page context, evidence, recent messages, and token-budget handling.
- `example_06_provider_streaming`: Demonstrate OpenAI-compatible, Gemini, local-provider, fallback, cancellation, and provider-error streaming paths.
- `example_07_ceo_gateway`: Demonstrate planner routing, read-only tool evidence, model selection, persistence, metadata, and streaming coordination.
- `example_08_action_drafts_and_boundaries`: Demonstrate governed action draft persistence while blocking trades, approvals, backtests, optimizations, and broker-affecting actions.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 249 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text
feat(conversation-ai-layer): implement phase 13 conversation ai layer requirements
```

## Final Platform Acceptance Checklist

- Done criterion: All 7,358 source checkbox tasks are implemented, tested, or explicitly deferred with owner-approved rationale.
- Done criterion: Every module imports without optional provider dependencies installed.
- Done criterion: All official registries expose only approved public functions/classes/tools.
- Done criterion: Standard envelopes are consistent across all phases.
- Done criterion: No module leaks secrets, credentials, private broker payloads, or approval packet internals into logs, metrics, reports, or conversation memory.
- Done criterion: Risk, live trading, execution, approval, idempotency, reconciliation, and kill-switch controls fail closed.
- Done criterion: UI/API and Conversation delegate domain logic instead of bypassing governed services.
- Done criterion: Active documentation, changelog, tests, and usage examples are synchronized with implemented behavior.

End of plan.
