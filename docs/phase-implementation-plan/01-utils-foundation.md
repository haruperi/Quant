## Phase 1 Utils Foundation

### Goal

Implement the Utils Foundation requirements under `app/utils/` while preserving the phase module boundaries and governance rules.

Task inventory: 1186 checkbox tasks (1186 checked, 0 unchecked).

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

app/core/security.py (re-exported by app.utils)

app/utils/settings.py

app/utils/auth.py

app/utils/event_bus.py

app/utils/errors.py (ErrorRouter / route_error)

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

- [X] Implement `app/__init__.py` first to establish a clean side-effect-free package. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] `app/__init__.py` exists and is side-effect free. *tests/unit/app/utils/test_utils_registry.py:28*

#### `app/utils/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] The implementation is expected to be fresh and clean, with no backward-compatibility shims. *app/utils/__init__.py:224*
- [X] `app/utils/__init__.py` must act as the public registry for the utility domain. *app/utils/__init__.py:224*
- [X] Only intentionally imported names listed in `__all__` may be public. *app/utils/__init__.py:224*
- [X] Support helpers may return native Python values when they are not agent-callable tools. *app/utils/__init__.py:224*
- [X] Internal helpers must remain private unless explicitly intended for public import. *app/utils/__init__.py:224*
- [X] No accidental public exports may exist. *app/utils/__init__.py:224*
- [X] No compatibility shims, aliases, fallback import modules, or duplicate wrapper modules may exist. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] New public exports must be justified by real cross-domain reuse. *app/utils/__init__.py:224*
- [X] Public exports may not be renamed or removed after v8 acceptance without a new versioned specification and registry review. *app/utils/__init__.py:224*
- [X] Implement `app/utils/__init__.py` only after modules exist and public names are finalized. *app/utils/__init__.py:224*
- [X] `app/utils/__init__.py` exposes only approved public names. *app/utils/__init__.py:224*
- [X] `app/utils/__init__.py` must not eagerly import pandas, cryptography, dotenv, broker SDKs, network clients, notification clients, Prometheus exporters, or other heavy optional dependencies unless absolutely necessary. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Documentation must maintain compatibility review notes for future public API changes. *app/utils/__init__.py:224*
- [X] Internal helpers are not accidentally exported. *app/utils/__init__.py:224*
- [X] No compatibility shims, aliases, fallback import modules, or duplicate wrapper modules exist. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/logger.py`

Functions/classes:

- `get_logger()`
- `configure_logging()`

Requirements:

- [X] The logger must be exported as a support object and must not be treated as an official AI tool. *app/utils/logger.py:263*
- [X] Official AI tools must use structured logging. *app/utils/logger.py:266*
- [X] The module must expose a project-wide `logger`. *app/utils/logger.py:263*
- [X] The module must expose `get_logger(name: str | None = None)`. *app/utils/logger.py:250*
- [X] The module must expose `configure_logging(level: str | int = "INFO")`. *app/utils/logger.py:266*
- [X] Logging must use Python `logging`. *app/utils/logger.py:266*
- [X] Logging must use structured JSON-compatible output for production runtime events. *app/utils/logger.py:266*
- [X] Production logging must use a JSON-compatible structured formatter. *app/utils/logger.py:266*
- [X] Local development console logging must support colorized human-readable output. *tests/unit/app/utils/test_logger.py:92*
- [X] Human-readable console log lines must use the format `datetime | level | module.submodule.filename:function:line | message`. *app/utils/logger.py:266*
- [X] Human-readable console timestamps must use the format `YYYY-MM-DD HH:MM:SS`. *app/utils/logger.py:266*
- [X] Logging must include `timestamp`, `level`, `logger_name`, `message`, `event_name`, `module`, `function`, `request_id`, `workflow_id`, `correlation_id`, and `error_code` where available. *app/utils/logger.py:263*
- [X] Human-readable console logging must include source line numbers where available. *app/utils/logger.py:266*
- [X] Logging must support child loggers per module while preserving a stable root logger name. *app/utils/logger.py:263*
- [X] Logging configuration must avoid duplicate handlers. *tests/unit/app/utils/test_event_bus.py:13*
- [X] Logging configuration must happen only through an explicit configuration function. *app/utils/logger.py:266*
- [X] Importing logger utilities must not force application-level logging configuration. *app/utils/logger.py:263*
- [X] File logging must be opt-in and configured explicitly through runtime settings or `configure_logging`. *app/utils/logger.py:266*
- [X] File logging must write only to configured log directories that are normalized through safe path handling. *app/utils/logger.py:266*
- [X] File logging must use rotating log files when enabled. *app/utils/logger.py:266*
- [X] Log rotation must support configurable maximum file size and maximum retained file count. *tests/unit/app/utils/test_logger.py:111*
- [X] Log retention must support configurable deletion of old rotated log files. *app/utils/logger.py:266*
- [X] Log retention deletion must be bounded to configured log directories and must not delete arbitrary files. *app/utils/logger.py:266*
- [X] Log file writes, rotation, and retention deletion must degrade safely if the filesystem or logging sink fails. *tests/unit/app/utils/test_logger.py:111*
- [X] Logging must avoid writing secrets. *app/utils/logger.py:266*
- [X] Log-level configuration must be controlled by runtime settings. *app/utils/logger.py:266*
- [X] Production files must log function/tool calls, validation failures, successful completions, recoverable warnings, and execution failures where applicable. *tests/unit/app/utils/test_validations.py:95*
- [X] Official AI tool logs must distinguish start, completion, validation failure, recoverable warning, and execution failure lifecycle events. *tests/unit/app/utils/test_validations.py:95*
- [X] Official AI tool logs must include request and workflow trace identifiers where available. *app/utils/logger.py:266*
- [X] Event Bus logs must include publish, subscribe, delivery failure, retry, dead-letter, queue-full, and dropped-event events. *tests/unit/app/utils/test_validations.py:95*
- [X] Notification logs must include routing decisions and delivery outcomes without exposing sensitive message bodies. *app/utils/logger.py:266*
- [X] Auth logs must include sanitized auth validation and authorization decisions. *app/utils/logger.py:266*
- [X] Observability logs must include metrics/export/health-check failures where detectable. *tests/unit/app/utils/test_validations.py:95*
- [X] Production files must never log passwords, API keys, broker credentials, encryption keys, tokens, raw private payloads, full approval packets, notification provider credentials, authorization headers, or Telegram bot tokens. *app/utils/logger.py:266*
- [X] Implement `app/utils/logger.py` before modules that need production logging. *app/utils/logger.py:263*
- [X] Important events and recoverable failures must use structured logging. *tests/unit/app/utils/test_validations.py:95*
- [X] Immutable constants and logger objects are allowed. *app/utils/logger.py:263*
- [X] Logging must be thread-safe under concurrent tool execution. *tests/unit/app/utils/test_logger.py:136*
- [X] Logging overhead must be minimal for normal tool execution. *app/utils/logger.py:266*
- [X] Logging must degrade safely if a logging sink fails. *tests/unit/app/utils/test_validations.py:95*
- [X] Documentation must describe required log fields and optional trace fields. *app/utils/logger.py:266*
- [X] Local development logging supports colorized human-readable console output in the approved format. *tests/unit/app/utils/test_logger.py:92*
- [X] Logging output must be deterministic enough for unit testing where log fields are asserted. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Logger tests must verify colorized console output can be enabled and disabled deterministically. *tests/unit/app/utils/test_utils_registry.py:6*

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

- [X] The utilities module must not own trading strategy logic. *app/utils/standard.py:106*
- [X] The utilities module must not own broker execution logic. *app/utils/standard.py:106*
- [X] The utilities module must not own risk-governor decisions. *app/utils/standard.py:106*
- [X] The utilities module must not own portfolio allocation decisions. *app/utils/standard.py:106*
- [X] The utilities module must not own application orchestration. *app/utils/standard.py:106*
- [X] The utilities module must not become a dumping ground for unrelated helpers. *app/utils/standard.py:106*
- [X] The utilities module must not export every internal helper as a public agent tool. *app/utils/standard.py:106*
- [X] The utilities module must not hide external dependency behavior behind unclear convenience functions. *app/utils/standard.py:106*
- [X] The utilities module must not perform live trading or live account mutation. *app/utils/standard.py:106*
- [X] The utilities module must not make trading, risk, allocation, execution, or strategy acceptance decisions. *app/utils/standard.py:106*
- [X] Utilities must not approve or reject trades. *tests/unit/app/utils/test_validations.py:21*
- [X] Utilities must not recommend allocations. *app/utils/standard.py:106*
- [X] Utilities must not decide strategy promotion. *app/utils/standard.py:106*
- [X] Utilities must not approve risk changes. *app/utils/standard.py:106*
- [X] Utilities must not place, close, modify, or cancel orders. *app/utils/standard.py:106*
- [X] Utilities must not activate live systems. *app/utils/standard.py:106*
- [X] Utilities must not override kill switches. *app/utils/standard.py:106*
- [X] Modules requiring financial decisions must call the appropriate risk, portfolio, execution, strategy, or governance domain. *app/utils/standard.py:106*
- [X] This is a domain-level requirements document for `docs/planning/DOMAIN.md`, not a sprint-specific requirements document. *app/utils/standard.py:106*
- [X] Support helpers remain native unless explicitly classified as official AI tools. *app/utils/standard.py:106*
- [X] Conditional AI tools remain support helpers unless direct agent use is approved. *app/utils/standard.py:106*
- [X] `app.services.data` will own repair, resampling, enrichment, persistence, and cleaning workflows for market data. *app/utils/standard.py:106*
- [X] Optional dependencies may or may not be installed; importability must remain intact either way. *app/utils/standard.py:106*
- [X] No UI, broker runtime, database repository, or LLM framework dependency is required inside `app.utils`. *app/utils/standard.py:106*
- [X] Public names must be classified as either official AI tools or support objects/helpers. *app/utils/standard.py:106*
- [X] Official AI tools must return the standard HaruQuant tool envelope. *app/utils/standard.py:106*
- [X] Official AI tools must include tool metadata. *app/utils/standard.py:106*
- [X] Official AI tools must include risk and side-effect flags. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Official AI tools must validate inputs. *app/utils/standard.py:106*
- [X] Official AI tools must not fail silently. *tests/unit/app/utils/test_validations.py:95*
- [X] Agents may call only approved official AI tools through approved tool attachment. *app/utils/standard.py:106*
- [X] Every official AI tool must return the top-level keys `status`, `message`, `data`, `error`, and `metadata`. *app/utils/standard.py:106*
- [X] `status` must be either `success` or `error`. *app/utils/standard.py:106*
- [X] `message` must be a string. *app/utils/standard.py:106*
- [X] `error` must be either `None` or a mapping with `code` and `details`. *app/utils/standard.py:106*
- [X] Standard response validation must reject missing top-level keys. *tests/unit/app/utils/test_validations.py:21*
- [X] Standard response validation must reject missing metadata keys. *tests/unit/app/utils/test_validations.py:21*
- [X] Standard response validation must reject malformed errors. *tests/unit/app/utils/test_validations.py:21*
- [X] `get_execution_ms(start_time)` must calculate execution duration consistently for official tools. *app/utils/standard.py:255*
- [X] `get_execution_ms(start_time)` must return milliseconds rounded to three decimals. *app/utils/standard.py:255*
- [X] Official tools must not return unstructured `None`. *app/utils/standard.py:106*
- [X] Official AI tools must return standard HaruQuant tool envelopes. *app/utils/standard.py:106*
- [X] Official success responses must include `status="success"`, message, data, `error=None`, and metadata. *app/utils/standard.py:106*
- [X] Data-quality issues must include code, severity, message, column, row count, and samples. *app/utils/standard.py:106*
- [X] Canonical JSON serialization must return deterministic JSON strings. *app/utils/standard.py:106*
- [X] Error helpers must return deterministic names and fallback messages. *app/utils/errors.py:533*
- [X] Official AI tools must return standard error envelopes for expected validation failures. *tests/unit/app/utils/test_validations.py:95*
- [X] Circuit-open failures must return `CIRCUIT_OPEN` or provider-specific deterministic details. *tests/unit/app/utils/test_validations.py:95*
- [X] Error events must include sanitized details only. *app/utils/errors.py:533*
- [X] Every public function must document return value. *app/utils/standard.py:106*
- [X] Documentation must include an operational runbook for critical utility-layer failures. *tests/unit/app/utils/test_validations.py:95*
- [X] Implement `app/utils/standard.py` before official AI tools. *app/utils/standard.py:106*
- [X] Implement usage examples for official AI tools and production primitives. *app/utils/standard.py:106*
- [X] Run CI quality gates before accepting the implementation. *app/utils/standard.py:106*
- [X] The target folder structure exists. *app/utils/standard.py:106*
- [X] Public registry documentation classifies every official AI tool and support helper. *app/utils/standard.py:106*
- [X] Official tools return standard envelopes. *app/utils/standard.py:106*
- [X] Official tools include metadata constants. *app/utils/standard.py:106*
- [X] Official tools include side-effect flags. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Official tools include `execution_ms`. *app/utils/standard.py:106*
- [X] Every Python file must have a file-level docstring. *app/utils/standard.py:106*
- [X] Every public function and class must have a useful docstring. *app/utils/standard.py:106*
- [X] All public functions and methods must be typed. *app/utils/standard.py:106*
- [X] Inputs must be validated where appropriate. *app/utils/standard.py:106*
- [X] Output shapes must be explicit where applicable. *app/utils/standard.py:106*
- [X] Error behavior must be deterministic. *app/utils/errors.py:533*
- [X] Production logic must not use `print()`. *app/utils/standard.py:106*
- [X] Utility functions must be safe for concurrent use unless explicitly documented otherwise. *tests/unit/app/utils/test_logger.py:136*
- [X] Mutable module-level state must be avoided. *app/utils/standard.py:106*
- [X] Caller-owned inputs must not be mutated unless documented in the function name and docstring. *app/utils/standard.py:106*
- [X] Concurrency guarantees and limitations must be documented per component. *app/utils/standard.py:106*
- [X] Optional dependencies must not break importability. *app/utils/standard.py:106*
- [X] Missing optional dependencies must fail only when the relevant feature is used. *tests/unit/app/utils/test_validations.py:95*
- [X] Missing optional dependency failures must be explicit. *tests/unit/app/utils/test_validations.py:95*
- [X] Optional dependency error messages must identify the missing dependency and required feature. *app/utils/standard.py:106*
- [X] Official AI tools must not raise expected validation errors to callers. *app/utils/standard.py:106*
- [X] Domain-specific errors must be mappable through `Error` inheritance or a compatible `code` attribute. *app/utils/errors.py:533*
- [X] Error helpers must not raise for unknown codes unless explicitly requested. *app/utils/errors.py:533*
- [X] Error messages must be human-readable and actionable. *app/utils/errors.py:533*
- [X] Event validation failures must map to `INVALID_EVENT`. *tests/unit/app/utils/test_validations.py:95*
- [X] Every Python file must start with a file-level docstring. *app/utils/standard.py:106*
- [X] File-level docstrings must state purpose. *app/utils/standard.py:106*
- [X] File-level docstrings must state whether the file contains official AI tools or support helpers. *app/utils/standard.py:106*
- [X] File-level docstrings must list exported public functions/classes. *app/utils/standard.py:106*
- [X] File-level docstrings must describe side effects, if any. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Every public function must document what it does. *app/utils/standard.py:106*
- [X] Every public function must document when to use it. *app/utils/standard.py:106*
- [X] Every public function must document arguments. *app/utils/standard.py:106*
- [X] Every public function must document side effects, if any. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Official AI tool docstrings must be agent-facing. *app/utils/standard.py:106*
- [X] Official AI tool docstrings must explain when an agent should use the tool. *app/utils/standard.py:106*
- [X] Official AI tool docstrings must explain what the tool does not do. *app/utils/standard.py:106*
- [X] Usage examples must demonstrate success and error handling. *app/utils/standard.py:106*
- [X] Usage examples must use realistic inputs. *app/utils/standard.py:106*
- [X] Documentation must describe safe metric-label rules and examples of rejected labels. *tests/unit/app/utils/test_validations.py:21*
- [X] Documentation must describe which features are support helpers and which are official AI tools. *app/utils/standard.py:106*
- [X] Documentation must describe which adapters are optional and lazy-loaded. *app/utils/standard.py:106*
- [X] Every Python file has a file-level docstring. *app/utils/standard.py:106*
- [X] Every public function/class has a useful docstring. *app/utils/standard.py:106*
- [X] Public functions and methods are typed. *app/utils/standard.py:106*
- [X] Inputs are validated where appropriate. *app/utils/standard.py:106*
- [X] Errors are explicit and deterministic. *app/utils/errors.py:533*
- [X] No production `print()` calls exist. *app/utils/standard.py:106*
- [X] Data repair and cleaning workflows are explicitly excluded from `app.utils` and reserved for `app.services.data`. *app/utils/standard.py:106*
- [X] Future domain-specific errors inherit from `Error` or expose a compatible `code` attribute. *app/utils/errors.py:533*
- [X] Standard response builders can map `Error` subclasses generically without hardcoding every future domain error. *app/utils/errors.py:533*
- [X] Usage examples exist for official AI tools. *app/utils/standard.py:106*
- [X] Usage examples use realistic inputs. *app/utils/standard.py:106*
- [X] Usage examples show success and error handling. *app/utils/standard.py:106*
- [X] Full-project quality gate passes. *app/utils/standard.py:106*
- [X] No unresolved open questions remain for the baseline production-ready utils module. *app/utils/standard.py:106*
- [X] The implementation must be compatible with Ruff format, Ruff check, mypy strict, pytest, and coverage. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Shared caches are allowed only when explicitly specified, bounded, and tested. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Time-dependent helpers must support deterministic testing where practical. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] ID-dependent and randomness-dependent helpers must support deterministic testing where practical. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] The utilities module must not implement UI, database repositories, or backtest engines. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Negative prices must be reported. *app/utils/standard.py:106*
- [X] Zero prices must be reported. *app/utils/standard.py:106*
- [X] OHLC values outside high/low range must be reported. *app/utils/standard.py:106*
- [X] NaN and infinity values must be detected. *app/utils/standard.py:106*
- [X] Symbol verification must be marked `not_available` when no symbol column exists. *app/utils/standard.py:106*
- [X] Issue lists and issue samples must truncate when limits are reached. *app/utils/standard.py:106*
- [X] Repeated identical alerts must be deduplicated or throttled. *tests/unit/app/utils/test_event_bus.py:13*
- [X] High-cardinality metric labels must be rejected or normalized. *tests/unit/app/utils/test_validations.py:21*
- [X] Open circuit state must fail fast. *tests/unit/app/utils/test_validations.py:95*
- [X] Unit tests must exist for every utility module. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Usage examples must exist for official AI tools. *app/utils/standard.py:106*
- [X] Minimum line coverage must be at least 80% for `app.utils`. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Tests must cover edge cases. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Official AI tool tests must verify metadata correctness. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Official AI tool tests must verify `execution_ms` existence. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Data-quality tests must cover at least 15 distinct data-quality cases. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] CI must pass Ruff format, Ruff check, mypy strict, pytest, and the coverage gate. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Implement unit tests for every module. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Unit tests exist for every module. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Official tools have metadata tests. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Edge case tests exist. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Coverage is at least 80%. *app/utils/standard.py:106*
- [X] Ruff format passes. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Ruff import sorting passes through Ruff check/format. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Ruff check passes. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] mypy passes. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] pytest passes. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Coverage gate passes. *app/utils/standard.py:106*

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

- [X] Official AI tools must use deterministic error codes. *app/utils/errors.py:67*
- [X] Standard response validation should validate error codes against the approved error-code set where practical. *app/utils/errors.py:67*
- [X] The module must define `Error`. *app/utils/errors.py:533*
- [X] The module must define `ValidationError`. *app/utils/errors.py:533*
- [X] The module must define `ConfigurationError`. *app/utils/errors.py:533*
- [X] The module must define `SecurityError`. *app/utils/errors.py:533*
- [X] The module must define `DataError`. *app/utils/errors.py:533*
- [X] The module must define `ExternalServiceError`. *app/utils/errors.py:533*
- [X] Every shared exception must carry a deterministic `code` attribute. *app/utils/errors.py:67*
- [X] Error messages must be human-readable. *app/utils/errors.py:533*
- [X] `error_name(code)` must return deterministic names. *app/utils/errors.py:1445*
- [X] `message_for(code, default)` must return useful fallback messages. *app/utils/errors.py:1464*
- [X] Unknown codes must resolve safely to `UNKNOWN_ERROR` or a provided default. *app/utils/errors.py:67*
- [X] Future domain-specific errors must inherit from `Error` or expose a compatible `code: str` attribute. *app/utils/errors.py:533*
- [X] Standard response builders must map `Error` subclasses generically without requiring every future domain error to be hardcoded. *app/utils/errors.py:533*
- [X] Unknown non-HaruQuant exceptions must map safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED` at controlled tool boundaries. *app/utils/errors.py:67*
- [X] Official error responses must include `status="error"`, message, `data=None`, error code/details, and metadata. *app/utils/errors.py:67*
- [X] Support helpers may return native Python values or raise typed exceptions. *app/utils/errors.py:67*
- [X] Unexpected execution failures must return `TOOL_EXECUTION_FAILED` or another safe deterministic error code. *tests/unit/app/utils/test_validations.py:95*
- [X] Implement `app/utils/errors.py` before deterministic failure behavior is needed. *tests/unit/app/utils/test_validations.py:95*
- [X] Support helpers return clear native values or raise typed exceptions. *app/utils/errors.py:67*
- [X] Support helpers may raise typed HaruQuant exceptions for programmer or validation errors. *app/utils/errors.py:67*
- [X] Expected validation failures should use deterministic codes such as `INVALID_INPUT` or `VALIDATION_FAILED`. *tests/unit/app/utils/test_validations.py:95*
- [X] Raw exception objects must never be returned in `data`. *app/utils/errors.py:67*
- [X] Raw exception objects must never be returned in `error`. *app/utils/errors.py:67*
- [X] Unknown non-HaruQuant exceptions must map safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED`. *app/utils/errors.py:67*
- [X] `INVALID_AUTH_CONTEXT` *app/utils/errors.py:67*
- [X] `AUTHORIZATION_FAILED` *app/utils/errors.py:67*
- [X] `INVALID_EVENT` *app/utils/errors.py:67*
- [X] `EVENT_PUBLISH_FAILED` *app/utils/errors.py:67*
- [X] `EVENT_HANDLER_FAILED` *app/utils/errors.py:67*
- [X] `EVENT_DEAD_LETTER_FAILED` *app/utils/errors.py:67*
- [X] `QUEUE_FULL` *app/utils/errors.py:67*
- [X] `BACKPRESSURE_EXCEEDED` *app/utils/errors.py:67*
- [X] `NOTIFICATION_FAILED` *app/utils/errors.py:67*
- [X] `NOTIFICATION_SUPPRESSED` *app/utils/errors.py:67*
- [X] `NOTIFICATION_THROTTLED` *app/utils/errors.py:67*
- [X] `OBSERVABILITY_ERROR` *app/utils/errors.py:67*
- [X] `METRICS_EXPORT_FAILED` *app/utils/errors.py:67*
- [X] `CLOCK_DRIFT_DETECTED` *app/utils/errors.py:67*
- [X] `CIRCUIT_OPEN` *app/utils/errors.py:67*
- [X] `SECRET_VERSION_CONFLICT` *app/utils/errors.py:98*
- [X] Every public function must document raised exceptions or structured error behavior. *app/utils/errors.py:67*
- [X] Official AI tool docstrings must explain what error codes may be returned. *app/utils/errors.py:67*
- [X] Official tools use deterministic error codes. *app/utils/errors.py:67*
- [X] Missing mandatory OHLC columns must return structured `INVALID_INPUT`. *app/utils/errors.py:67*
- [X] Unknown error codes must resolve safely. *app/utils/errors.py:67*
- [X] Unknown non-HaruQuant exceptions must map safely at controlled tool boundaries. *app/utils/errors.py:67*
- [X] Official AI tool tests must verify deterministic error codes. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Error tests must verify exception attributes, known codes, unknown codes, and fallback messages. *app/utils/errors.py:533*

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

- [X] Official AI tools must include `request_id: str | None = None`. *app/utils/identity.py:65*
- [X] `metadata` must include `tool_name`, `tool_version`, `tool_category`, `tool_risk_level`, `request_id`, `execution_ms`, `read_only`, `writes_file`, `modifies_database`, `places_trade`, and `requires_network`. *app/utils/identity.py:65*
- [X] Standard response validation must reject invalid statuses. *tests/unit/app/utils/test_validations.py:21*
- [X] The module must provide `generate_id`. *app/utils/identity.py:65*
- [X] The module must provide `generate_prefixed_id`. *app/utils/identity.py:65*
- [X] The module must provide `generate_request_id`. *app/utils/identity.py:99*
- [X] The module must provide `generate_workflow_id`. *app/utils/identity.py:104*
- [X] The module must provide `generate_correlation_id` or equivalent correlation ID support. *app/utils/identity.py:109*
- [X] The module must provide `generate_event_id` or equivalent event ID support. *app/utils/identity.py:119*
- [X] The module must provide `validate_request_id`. *app/utils/identity.py:163*
- [X] The module must provide `validate_workflow_id`. *app/utils/identity.py:181*
- [X] The module must provide `ensure_version`. *app/utils/identity.py:199*
- [X] IDs must be string-safe. *app/utils/identity.py:65*
- [X] IDs must be safe for logs, filenames where practical, audit records, tool metadata, events, notifications, and metrics after cardinality controls. *app/utils/identity.py:65*
- [X] IDs must not contain secrets or raw user-provided text. *app/utils/identity.py:65*
- [X] Prefix validation must reject empty or unsafe prefixes. *tests/unit/app/utils/test_validations.py:21*
- [X] Generated IDs must be collision-resistant. *app/utils/identity.py:65*
- [X] Generated IDs must use UUID4, ULID-like generation, or an equivalently collision-resistant approach unless deterministic IDs are explicitly required. *app/utils/identity.py:65*
- [X] Request IDs and workflow IDs must be suitable for logs, audit records, tool responses, and agent handoffs. *app/utils/identity.py:65*
- [X] ID validation must be deterministic and must not perform external lookups. *app/utils/identity.py:65*
- [X] `ensure_version(None)` must return the configured default. *app/utils/identity.py:199*
- [X] Official AI tools must accept optional `request_id`. *app/utils/identity.py:65*
- [X] Identity helpers must accept prefixes and version strings. *app/utils/identity.py:65*
- [X] Implement `app/utils/identity.py` before request/workflow/event trace helpers are needed. *app/utils/identity.py:65*
- [X] Official tools accept `request_id`. *app/utils/identity.py:65*
- [X] The implementation must avoid avoidable circular imports. *app/utils/identity.py:65*
- [X] Large data-quality validations must avoid unnecessary deep copies. *app/utils/identity.py:65*
- [X] Usage examples must use `request_id` where applicable. *app/utils/identity.py:65*
- [X] Usage examples use `request_id` where applicable. *app/utils/identity.py:65*
- [X] Empty or unsafe ID prefixes must fail validation. *tests/unit/app/utils/test_validations.py:95*
- [X] `ensure_version(None)` must return the default. *app/utils/identity.py:199*
- [X] Invalid datetime inputs must fail clearly. *tests/unit/app/utils/test_validations.py:21*
- [X] Invalid high-low relationships must be reported. *tests/unit/app/utils/test_validations.py:21*
- [X] Tests must cover invalid inputs. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Official AI tool tests must verify request ID propagation. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Identity tests must verify ID uniqueness, prefix validation, and version defaulting. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Invalid input tests exist. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/normalization.py`

Functions/classes:

- `DEFAULT_TIMEZONE`
- `parse_datetime`
- `normalize_timestamp`
- `format_timestamp`
- `is_stale`
- `get_execution_ms(start_time)`

Requirements:

- [X] Official AI tools must measure execution timing. *app/utils/normalization.py:109*
- [X] `get_execution_ms(start_time)` must use a monotonic clock source such as `time.perf_counter()`. *app/utils/standard.py:255*
- [X] The module must define `DEFAULT_TIMEZONE = "UTC"`. *app/utils/normalization.py:109*
- [X] The module must provide datetime parsing. *app/utils/normalization.py:109*
- [X] The module must provide timestamp normalization. *app/utils/normalization.py:109*
- [X] The module must provide UTC conversion. *app/utils/normalization.py:109*
- [X] The module must provide naive UTC conversion. *app/utils/normalization.py:109*
- [X] The module must provide UTC timestamp formatting with trailing `Z`. *app/utils/normalization.py:109*
- [X] The module must provide timezone normalization for pandas-like series or timestamp columns. *app/utils/normalization.py:109*
- [X] The module must provide stale-data checks. *app/utils/normalization.py:109*
- [X] Timezone behavior must be explicit. *app/utils/normalization.py:109*
- [X] Naive datetimes must be handled deterministically using an explicit assumed timezone. *app/utils/normalization.py:109*
- [X] ISO strings must parse consistently. *app/utils/normalization.py:109*
- [X] Time-dependent helpers must support injected `now` values or injected clock objects where practical. *app/utils/normalization.py:109*
- [X] Invalid datetimes must fail clearly. *tests/unit/app/utils/test_validations.py:21*
- [X] Helpers must not use the local machine timezone implicitly. *app/utils/normalization.py:109*
- [X] Wall-clock timestamps must be UTC-aware. *app/utils/normalization.py:109*
- [X] Execution timing must use monotonic timers. *app/utils/normalization.py:109*
- [X] The system must distinguish wall-clock timestamps from monotonic durations. *app/utils/normalization.py:109*
- [X] Distributed workflow timestamp validation must surface clock-drift risk where relevant. *app/utils/normalization.py:109*
- [X] Event envelopes must include event creation time and event processing time where applicable. *app/utils/normalization.py:109*
- [X] Notification diagnostics must include created, routed, sent, and failed timestamps where applicable. *tests/unit/app/utils/test_validations.py:95*
- [X] Health checks should include clock-drift status where supported by runtime environment. *app/utils/normalization.py:109*
- [X] Timestamp helpers must accept datetime-like values and explicit timezone assumptions. *app/utils/normalization.py:109*
- [X] Timestamp formatting must return UTC ISO strings ending in `Z`. *app/utils/normalization.py:109*
- [X] Implement `app/utils/normalization.py` before data quality, settings, freshness checks, and event timestamp validation. *app/utils/normalization.py:109*
- [X] Importing `app.utils` must be lightweight. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Heavy dependencies must be imported inside the specific submodule or function that needs them. *app/utils/normalization.py:109*
- [X] Importing any `app.utils` module must not open network connections. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Importing any `app.utils` module must not initialize broker clients. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Importing any `app.utils` module must not run validation jobs. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Documentation must describe UTC-first time policy. *app/utils/normalization.py:109*
- [X] Documentation must describe monotonic execution timing policy. *app/utils/normalization.py:109*
- [X] Importing `app.utils` must be safe in tests, CLI scripts, FastAPI startup, and agent runtime initialization. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Naive datetimes must be normalized using the explicit assumed timezone. *app/utils/normalization.py:109*
- [X] Stale checks must be deterministic when `now` is injected. *app/utils/normalization.py:109*
- [X] Unparseable datetimes must be reported. *app/utils/normalization.py:109*
- [X] Non-monotonic timestamps must be reported. *app/utils/normalization.py:109*
- [X] Duplicate timestamps must be reported. *app/utils/normalization.py:109*
- [X] Stale data must fail deterministically. *tests/unit/app/utils/test_validations.py:95*
- [X] Normalization tests must verify ISO parsing, naive timezone assumptions, UTC conversion, and stale checks. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/paths.py`

Functions/classes:

- `normalize_path`
- `ensure_dir`
- `ensure_parent_dir`
- `safe_join`
- `validate_path_within_root`

Requirements:

- [X] The module must provide `normalize_path`. *app/utils/paths.py:92*
- [X] The module must provide `ensure_dir`. *app/utils/paths.py:126*
- [X] The module must provide `ensure_parent_dir`. *app/utils/paths.py:159*
- [X] Path inputs must be validated. *app/utils/paths.py:92*
- [X] Directory creation helpers must be explicit side-effect helpers. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] `normalize_path` must have no side effects. *app/utils/paths.py:92*
- [X] `ensure_dir` must create a directory when missing. *app/utils/paths.py:126*
- [X] `ensure_parent_dir` must create a parent directory when missing. *app/utils/paths.py:159*
- [X] Path traversal outside `base_dir` must be rejected when a base directory is supplied. *tests/unit/app/utils/test_validations.py:21*
- [X] Path helpers must return `Path` objects. *app/utils/paths.py:92*
- [X] File and directory permissions must use platform-safe defaults. *app/utils/paths.py:92*
- [X] Path helpers must accept string or `Path` values and optional `base_dir`. *app/utils/paths.py:92*
- [X] Path helpers must return `Path` objects. *app/utils/paths.py:92*
- [X] Implement `app/utils/paths.py` before settings and artifact helpers. *app/utils/paths.py:92*
- [X] Importing any `app.utils` module must not create files or directories. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Empty paths must fail validation. *tests/unit/app/utils/test_validations.py:95*
- [X] Unsafe path traversal outside `base_dir` must be rejected. *tests/unit/app/utils/test_validations.py:21*
- [X] Tests must cover success paths. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Tests must cover failure paths. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Logger tests must verify human-readable console formatting includes datetime, level, module path, function name, line number, and message. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Path tests must verify safe normalization, unsafe traversal, directory creation, and parent creation. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] A concurrency stress test suite must exist outside the fast unit-test path. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/dataframe_tools.py`

Functions/classes:

- `align_dataframe_time_index`
- `bars_to_records`
- `chunk_sequence`
- `generate_parameter_combinations`
- `compare_dataframes`

Requirements:

- [X] The module must provide datetime alignment for dataframes. *app/utils/dataframe_tools.py:58*
- [X] The module must provide bar-to-record conversion. *app/utils/dataframe_tools.py:58*
- [X] The module must provide chunking for sequences. *app/utils/dataframe_tools.py:58*
- [X] The module must provide parameter-combination helpers. *app/utils/dataframe_tools.py:58*
- [X] The module must provide dataframe comparison helpers. *app/utils/dataframe_tools.py:58*
- [X] The module must provide OHLC and OHLCV comparison helpers. *app/utils/dataframe_tools.py:58*
- [X] The module must provide dataframe-record serialization. *app/utils/dataframe_tools.py:58*
- [X] Dataframe helpers may return native Python objects. *app/utils/dataframe_tools.py:58*
- [X] Dataframe columns must be validated where required. *app/utils/dataframe_tools.py:58*
- [X] Dataframe helpers must not mutate caller-owned dataframes unless explicitly documented. *app/utils/dataframe_tools.py:58*
- [X] Dataframe helpers must document copy, view, or transformed-data behavior. *app/utils/dataframe_tools.py:58*
- [X] Serialization must handle timestamps safely. *app/utils/dataframe_tools.py:58*
- [X] `serialize_dataframe_records` must emit UTC ISO timestamp strings ending in `Z`. *app/utils/dataframe_tools.py:118*
- [X] `compare_dataframes` must align by comparable indexes or fail with a clear validation error when deterministic alignment is impossible. *app/utils/dataframe_tools.py:194*
- [X] `chunked` must reject `size <= 0` with a clear validation error. *app/utils/dataframe_tools.py:170*
- [X] Comparisons must support tolerance. *app/utils/dataframe_tools.py:58*
- [X] Empty dataframes must be handled deterministically. *app/utils/dataframe_tools.py:58*
- [X] Importing `app.utils` must not eagerly import pandas. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Missing pandas must fail only when a dataframe helper is called. *tests/unit/app/utils/test_validations.py:95*
- [X] Dataframe serialization must return JSON-safe records where practical. *app/utils/dataframe_tools.py:58*
- [X] Implement `app/utils/dataframe_tools.py` after normalization and errors. *app/utils/dataframe_tools.py:58*
- [X] Dataframe helpers must use lazy pandas imports or `TYPE_CHECKING` guards. *app/utils/dataframe_tools.py:58*
- [X] Importing any `app.utils` module must not execute expensive dataframe operations. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Dataframe helpers must avoid repeated full-dataframe scans where possible. *app/utils/dataframe_tools.py:58*
- [X] Dataframe helpers use lazy pandas imports or `TYPE_CHECKING` guards. *app/utils/dataframe_tools.py:58*
- [X] Missing pandas must fail only when dataframe helpers are called. *tests/unit/app/utils/test_validations.py:95*
- [X] Missing required dataframe columns must fail clearly. *tests/unit/app/utils/test_validations.py:95*
- [X] Empty dataframes must be handled deterministically. *app/utils/dataframe_tools.py:58*
- [X] Dataframe index mismatch must fail clearly when deterministic alignment is impossible. *tests/unit/app/utils/test_validations.py:95*
- [X] `chunked(size <= 0)` must fail clearly. *app/utils/dataframe_tools.py:170*
- [X] Dataframe tests must verify alignment, serialization, UTC timestamp output, comparison, index mismatch behavior, missing columns, chunk-size validation, and no input mutation. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/data_quality.py`

Functions/classes:

- `validate_ohlcv_quality`

Requirements:

- [X] Data-quality market-calendar gap handling depends on session rules being supplied by a caller or future domain module. *app/utils/data_quality.py:354*
- [X] The default OHLCV scoring model applies unless a later module-specific specification replaces it. *app/utils/data_quality.py:354*
- [X] `validate_ohlcv_quality` must be implemented as a low-risk, read-only official AI tool. *app/utils/data_quality.py:354*
- [X] The module must provide `prepare_ohlcv_data`. *app/utils/data_quality.py:106*
- [X] The module must provide `validate_ohlcv_quality`. *app/utils/data_quality.py:354*
- [X] `validate_ohlcv_quality` must be stateless and diagnostic-only. *app/utils/data_quality.py:354*
- [X] `validate_ohlcv_quality` must not repair, enrich, persist, resample, clean, or mutate input data. *app/utils/data_quality.py:354*
- [X] `validate_ohlcv_quality` may inspect, profile, score, report issues, and provide descriptive remediation recommendations. *app/utils/data_quality.py:354*
- [X] Data repair, resampling, enrichment, persistence, and cleaning workflows must be reserved for `app.services.data`. *app/utils/data_quality.py:354*
- [X] Caller-owned dataframes must not be mutated. *app/utils/data_quality.py:354*
- [X] Validation must verify the input is a pandas DataFrame. *app/utils/data_quality.py:354*
- [X] Validation must verify mandatory OHLC columns exist. *app/utils/data_quality.py:354*
- [X] Missing mandatory columns must produce structured `INVALID_INPUT` details. *app/utils/data_quality.py:354*
- [X] Extra columns must be ignored by default and must not fail validation unless they create ambiguity. *tests/unit/app/utils/test_validations.py:95*
- [X] Validation must verify datetime column or datetime-compatible index availability. *app/utils/data_quality.py:354*
- [X] Validation must verify datetimes are parseable. *app/utils/data_quality.py:354*
- [X] Validation must report timestamp monotonicity. *app/utils/data_quality.py:354*
- [X] Validation must detect duplicate timestamps. *tests/unit/app/utils/test_event_bus.py:13*
- [X] Validation must detect duplicate OHLC/OHLCV rows. *tests/unit/app/utils/test_event_bus.py:13*
- [X] Validation must detect missing timestamps or inferred gaps when timeframe is known. *app/utils/data_quality.py:354*
- [X] Validation must distinguish market-calendar gaps from unexpected gaps where session rules are supplied. *app/utils/data_quality.py:354*
- [X] Validation must verify OHLC values are numeric. *app/utils/data_quality.py:354*
- [X] Validation must flag negative prices. *app/utils/data_quality.py:354*
- [X] Validation must flag zero prices. *app/utils/data_quality.py:354*
- [X] Validation must validate high-low relationships. *app/utils/data_quality.py:354*
- [X] Validation must verify OHLC values are within candle high/low range. *app/utils/data_quality.py:354*
- [X] Validation must flag zero volume when volume is supplied. *app/utils/data_quality.py:354*
- [X] Validation must flag negative volume when volume is supplied. *app/utils/data_quality.py:354*
- [X] Validation must verify spread is numeric and non-negative when supplied. *app/utils/data_quality.py:354*
- [X] Validation must detect extreme spikes using configurable thresholds. *app/utils/data_quality.py:354*
- [X] Validation must detect flatline candles. *app/utils/data_quality.py:354*
- [X] Validation must detect numeric infinities and NaN values. *app/utils/data_quality.py:354*
- [X] Validation must report timezone awareness. *app/utils/data_quality.py:354*
- [X] Validation must produce session-level statistics where possible. *app/utils/data_quality.py:354*
- [X] Validation must calculate a deterministic quality score. *app/utils/data_quality.py:354*
- [X] Validation must assign severity levels consistently. *app/utils/data_quality.py:354*
- [X] Validation must bound issue samples by `max_issue_samples`. *app/utils/data_quality.py:354*
- [X] Validation must bound issue list length by `max_issues_returned`. *app/utils/data_quality.py:354*
- [X] Validation must avoid oversized tool responses for large datasets. *app/utils/data_quality.py:354*
- [X] Validation must report symbol mismatches as `SYMBOL_MISMATCH` when `symbol` is provided and a dataframe `symbol` column exists. *app/utils/data_quality.py:354*
- [X] Validation must mark symbol verification as `not_available` in summary when `symbol` is provided and no dataframe `symbol` column exists. *app/utils/data_quality.py:354*
- [X] Validation must report timeframe mismatches as `TIMEFRAME_MISMATCH` or `UNEXPECTED_TIME_GAP` when timeframe checks fail. *tests/unit/app/utils/test_validations.py:95*
- [X] Successful validation responses must include `symbol`, `timeframe`, `rows_checked`, `quality_score`, `passed`, `severity`, `issues`, `summary`, `profile`, and `remediation`. *app/utils/data_quality.py:354*
- [X] Each issue must include `code`, `severity`, `message`, `column`, `row_count`, and `sample`. *app/utils/data_quality.py:354*
- [X] The default quality score penalty model must be: critical `-40`, error `-20`, warning `-5`, info `-1`, bounded from `0` to `100`. *app/utils/data_quality.py:354*
- [X] OHLCV validation must use a default quality pass threshold of `90.0`. *app/utils/data_quality.py:354*
- [X] OHLCV `passed=True` must require no critical issues, no error issues, and `quality_score >= quality_pass_threshold`. *app/utils/data_quality.py:354*
- [X] Warning and info issues may still produce `passed=True` only when the quality score remains above threshold. *app/utils/data_quality.py:354*
- [X] Overall severity must aggregate deterministically: any critical issue means `critical`; otherwise any error means `error`; otherwise any warning means `warning`; otherwise `info`. *app/utils/data_quality.py:354*
- [X] Issue truncation must be explicit through `summary["issues_truncated"]` and `summary["samples_truncated"]` when limits are reached. *app/utils/data_quality.py:354*
- [X] OHLCV validation must accept a pandas DataFrame. *app/utils/data_quality.py:354*
- [X] OHLCV validation must accept optional symbol and timeframe context. *app/utils/data_quality.py:354*
- [X] `validate_ohlcv_quality` success data must include symbol, timeframe, rows checked, quality score, pass/fail state, severity, issues, summary, profile, and remediation. *app/utils/data_quality.py:354*
- [X] Implement `app/utils/data_quality.py` after standard, errors, normalization, dataframe tools, and schema validation. *app/utils/data_quality.py:354*
- [X] `validate_ohlcv_quality` should handle 1,000 rows quickly for normal agent workflows. *app/utils/data_quality.py:354*
- [X] `validate_ohlcv_quality` should handle 100,000 rows within a practical local validation budget. *app/utils/data_quality.py:354*
- [X] `validate_ohlcv_quality` is stateless, diagnostic-only, and does not repair, resample, persist, enrich, or mutate input data. *app/utils/data_quality.py:354*
- [X] Invalid OHLCV input type must return `INVALID_INPUT`. *tests/unit/app/utils/test_validations.py:21*
- [X] Extra OHLCV columns must not fail validation unless they create ambiguity. *tests/unit/app/utils/test_validations.py:95*
- [X] Duplicate OHLC/OHLCV rows must be reported. *app/utils/data_quality.py:354*
- [X] Missing timestamps or inferred gaps must be reported when timeframe is known. *app/utils/data_quality.py:354*
- [X] Market-calendar gaps must be distinguished from unexpected gaps where session rules are supplied. *app/utils/data_quality.py:354*
- [X] Zero volume must be reported when volume is supplied. *app/utils/data_quality.py:354*
- [X] Negative volume must be reported when volume is supplied. *app/utils/data_quality.py:354*
- [X] Flatline candles must be detected. *app/utils/data_quality.py:354*
- [X] Symbol mismatches must be reported when symbol verification is available. *app/utils/data_quality.py:354*
- [X] Timeframe mismatches must be reported when timeframe is supplied. *app/utils/data_quality.py:354*
- [X] Data-quality tests cover realistic OHLCV defects. *tests/unit/app/utils/test_utils_registry.py:6*

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

- [X] Strict schema-version enforcement occurs only when a caller or schema requires a version. *app/utils/validations.py:374*
- [X] `validate_input_schema` must be implemented as a low-risk, read-only official AI tool. *app/utils/validations.py:374*
- [X] `validate_output_schema` must be implemented as a low-risk, read-only official AI tool. *app/utils/validations.py:410*
- [X] `validate_handoff_payload` must be implemented as a low-risk, read-only official AI tool. *app/utils/validations.py:446*
- [X] `validate_evidence_pack` must be implemented as a low-risk, read-only official AI tool. *app/utils/validations.py:478*
- [X] `validate_approval_packet` must be implemented as a low-risk, read-only official AI tool. *app/utils/validations.py:510*
- [X] `validate_registry_entry` must be implemented as a low-risk, read-only official AI tool. *app/utils/validations.py:542*
- [X] `validate_data_freshness` must be implemented as a low-risk, read-only official AI tool. *app/utils/validations.py:574*
- [X] Official AI tools must return the standard response schema. *app/utils/validations.py:374*
- [X] The module must provide reusable validation helpers for agent, workflow, tool, registry, evidence, approval, freshness, artifact, and payload contracts. *app/utils/validations.py:374*
- [X] `validate_numeric_range` must be a support helper returning a native validation result. *app/utils/validations.py:68*
- [X] `validate_required_fields` must be a support helper returning a native validation result. *app/utils/validations.py:104*
- [X] Native validation results must include at minimum `valid`, `message`, `code`, and `details`. *app/utils/validations.py:374*
- [X] Official validators may wrap native validation results in standard tool envelopes. *app/utils/validations.py:374*
- [X] Numeric validation must support risk values, prices, volumes, spreads, scores, thresholds, and allocation limits. *app/utils/validations.py:374*
- [X] Numeric validation must reject non-numeric values with deterministic details. *tests/unit/app/utils/test_validations.py:21*
- [X] Numeric validation must reject `NaN`, positive infinity, and negative infinity unless a future specialized function explicitly allows them. *tests/unit/app/utils/test_validations.py:21*
- [X] Numeric validation bounds must be inclusive unless documented otherwise. *app/utils/validations.py:374*
- [X] Numeric validation messages must include the logical field name. *app/utils/validations.py:374*
- [X] Missing required fields must be explicit. *app/utils/validations.py:374*
- [X] Unknown extra fields must be rejected by default for official schema validators. *tests/unit/app/utils/test_validations.py:21*
- [X] Schemas may explicitly allow extra fields through a documented schema policy. *app/utils/validations.py:374*
- [X] Input and output schema validators must support optional schema-version checks. *app/utils/validations.py:374*
- [X] Version mismatches must return `VALIDATION_FAILED` with a clear compatibility message. *app/utils/validations.py:374*
- [X] Schema compatibility must follow semantic-version rules. *app/utils/validations.py:374*
- [X] Schema compatibility must require the same major version. *app/utils/validations.py:374*
- [X] Schema compatibility may accept payload minor versions less than or equal to the schema minor version when no breaking change is declared. *app/utils/validations.py:374*
- [X] Schema compatibility may be overridden by an explicit compatible-version allowlist in the schema. *app/utils/validations.py:374*
- [X] Schema validation errors must return the specific path to the invalid field. *tests/unit/app/utils/test_validations.py:21*
- [X] Official schema validator errors must include `invalid_fields` as a bounded list of `{path, code, message}` objects where practical. *tests/unit/app/utils/test_validations.py:21*
- [X] Invalid-field paths must use a deterministic format such as JSON Pointer. *tests/unit/app/utils/test_validations.py:21*
- [X] Dot-path strings may be allowed for human-readable display when documented. *app/utils/validations.py:374*
- [X] Nested validation errors must include the nearest valid parent path when the exact path cannot be determined. *app/utils/validations.py:374*
- [X] Schema validation error details must remain bounded and redacted. *app/utils/validations.py:374*
- [X] Evidence validation must require source, timestamp, and evidence type. *app/utils/validations.py:374*
- [X] Approval packet validation must require action, reason, evidence, risk class, and approval status. *app/utils/validations.py:374*
- [X] Registry entry validation must require name, version, category or domain, risk level, and status. *app/utils/validations.py:374*
- [X] Risk-level validation must use the central `VALID_RISK_LEVELS` model. *app/utils/validations.py:374*
- [X] Environment validation must use the central `VALID_ENVIRONMENT_MODES` model unless a stricter allowlist is supplied. *app/utils/validations.py:374*
- [X] Blocked action validation must require an `action` field. *app/utils/validations.py:374*
- [X] Blocked action validation must fail closed when `payload["action"]` appears in `blocked_actions`. *tests/unit/app/utils/test_validations.py:95*
- [X] Freshness validation must require a timestamp field with default `as_of`. *app/utils/validations.py:374*
- [X] Freshness validation must support a configurable timestamp field. *app/utils/validations.py:374*
- [X] Freshness validation must compare against injected timestamps where supported. *app/utils/validations.py:374*
- [X] Artifact reference validation must require `artifact_id`, `version`, and at least one location field such as `storage_path`, `uri`, or `content_hash`. *app/utils/validations.py:374*
- [X] Schema validation helpers must enforce configured maximum depth, maximum field count, maximum issue count, maximum sample count, and maximum payload size. *app/utils/validations.py:374*
- [X] Resource-limit failures must return bounded diagnostics. *tests/unit/app/utils/test_validations.py:95*
- [X] Resource-limit failures must include the relevant path or validation area where available. *tests/unit/app/utils/test_validations.py:95*
- [X] Schema validation helpers must avoid dumping entire payloads in errors. *app/utils/validations.py:374*
- [X] Schema validation must accept payload mappings. *app/utils/validations.py:374*
- [X] Input/output schema validation must accept schema mappings. *app/utils/validations.py:374*
- [X] Schema validators must accept optional `schema_version`. *app/utils/validations.py:374*
- [X] Numeric-range validation must accept a value, logical field name, optional minimum, optional maximum, and `allow_none`. *app/utils/validations.py:374*
- [X] Blocked-action validation must accept payload and blocked-action list. *app/utils/validations.py:374*
- [X] Artifact-reference validation must accept artifact identity, version, and location/hash fields. *app/utils/validations.py:374*
- [X] Native validation helpers must return validation-result dictionaries containing at least `valid`, `message`, `code`, and `details`. *app/utils/validations.py:374*
- [X] Schema validation failures must include bounded invalid-field diagnostics with deterministic field paths. *tests/unit/app/utils/test_validations.py:21*
- [X] Schema validation errors must include invalid-field path, error code, sanitized message, and bounded details. *tests/unit/app/utils/test_validations.py:21*
- [X] Documentation must include schema examples for evidence packs, approval packets, registry entries, freshness metadata, and artifact references. *app/utils/validations.py:374*
- [X] Implement `app/utils/validations.py` after standard, errors, normalization, security, auth, and observability foundations. *app/utils/validations.py:374*
- [X] Validators accept supported enum values and strings where practical, then normalize to canonical JSON-safe strings. *app/utils/validations.py:374*
- [X] Schema validation errors include deterministic invalid-field paths. *tests/unit/app/utils/test_validations.py:21*
- [X] Official schema validation errors include bounded `invalid_fields` diagnostics where practical. *tests/unit/app/utils/test_validations.py:21*
- [X] Canonical JSON output must be deterministic across equivalent payloads. *app/utils/validations.py:374*
- [X] Schema validation helpers must be optimized for low latency. *tests/unit/app/utils/test_validations.py:122*
- [X] Schema validation helpers must not perform blocking I/O. *app/utils/validations.py:374*
- [X] Schema validation helpers must not perform network calls. *app/utils/validations.py:374*
- [X] Schema validation helpers must not introduce unbounded CPU spikes during normal market-data processing. *app/utils/validations.py:374*
- [X] Official AI tool docstrings must explain what evidence the tool produces. *app/utils/validations.py:374*
- [X] Documentation must describe the structured logging schema. *app/utils/validations.py:374*
- [X] Documentation must define schema-validation invalid-field path format. *tests/unit/app/utils/test_validations.py:21*
- [X] Documentation must define schema-validation resource limits and performance expectations. *tests/unit/app/utils/test_validations.py:122*
- [X] Official tools pass `validate_tool_response_schema`. *app/utils/validations.py:374*
- [X] Public responses, metadata, audit records, logs, and serialized payloads never expose enum objects directly. *app/utils/validations.py:374*
- [X] Schema validation resource limits prevent unbounded CPU, memory, and response sizes. *app/utils/validations.py:374*
- [X] Non-numeric OHLC values must be reported. *app/utils/validations.py:374*
- [X] Non-numeric or negative spread must be reported when spread is supplied. *app/utils/validations.py:374*
- [X] Missing required payload fields must fail explicitly. *tests/unit/app/utils/test_validations.py:95*
- [X] Schema version mismatches must fail with `VALIDATION_FAILED`. *tests/unit/app/utils/test_validations.py:95*
- [X] Schema validation of oversized payloads must fail with bounded diagnostics. *tests/unit/app/utils/test_validations.py:95*
- [X] Schema validation errors for nested fields must include deterministic field paths. *app/utils/validations.py:374*
- [X] Blocked-action payloads without `action` must fail clearly. *tests/unit/app/utils/test_validations.py:95*
- [X] Blocked actions must fail closed. *tests/unit/app/utils/test_validations.py:95*
- [X] Missing freshness metadata must fail. *tests/unit/app/utils/test_validations.py:95*
- [X] Artifact references missing identity, version, or location/hash must fail. *tests/unit/app/utils/test_validations.py:95*
- [X] Official AI tool tests must verify standard return schema compliance. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Standard response tests must verify success envelope, error envelope, metadata, invalid schema, missing keys, execution timing, schema constants, and error code validation. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Data-quality tests must verify clean OHLCV data, missing columns, extra columns, symbol mismatch, timeframe mismatch, duplicates, gaps, bad OHLC, zero/negative values, spread, volume, spikes, flatlines, truncation limits, and schema compliance. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Schema-validation tests must verify native helper results, required fields, input/output schemas, schema versioning, handoffs, evidence, approvals, registry entries, blocked actions, freshness, and artifact references. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Schema-validation tests must verify invalid-field paths for flat and nested payloads. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Schema-validation tests must verify payload-size, depth, field-count, issue-count, and sample-count limits. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Schema-validation tests must verify low-latency behavior with representative market-data payloads. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Schema-validation tests must verify no blocking I/O or network access occurs. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Official tools have schema compliance tests. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/core/security.py (re-exported by app.utils)`

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

- [X] Agents must not call low-level helpers such as `normalize_timestamp`, `ensure_dir`, or `hash_password` unless a workflow explicitly approves that capability. *app/core/security.py:228*
- [X] Sensitive runtime settings and provider credentials are supplied through secure environment/configuration mechanisms. *app/core/security.py:58*
- [X] `redact_text` must be classified as a low-risk, read-only official AI tool only for approved audit/log-redaction workflows. *app/core/security.py:58*
- [X] `redact_mapping` must be classified as a low-risk, read-only official AI tool only for approved audit/log-redaction workflows. *app/core/security.py:68*
- [X] `encrypt_data` must remain a restricted support helper and must not be attached to agents by default. *app/core/security.py:58*
- [X] `decrypt_data` must remain a restricted support helper and must not be attached to agents by default. *app/core/security.py:58*
- [X] The module must provide sensitive-key detection. *app/core/security.py:58*
- [X] The module must provide scalar redaction. *tests/unit/app/core/test_security.py:37*
- [X] The module must provide text redaction. *tests/unit/app/core/test_security.py:37*
- [X] The module must provide mapping redaction. *tests/unit/app/core/test_security.py:37*
- [X] The module must provide password hashing. *app/core/security.py:58*
- [X] The module must provide password verification. *app/core/security.py:58*
- [X] The module must provide encryption key loading. *app/core/security.py:58*
- [X] The module must provide encryption. *app/core/security.py:58*
- [X] The module must provide decryption. *app/core/security.py:58*
- [X] The module must provide active secret-version selection. *app/core/security.py:58*
- [X] Secret-like keys must be detected case-insensitively. *app/core/security.py:58*
- [X] Redaction must use a denylist-first strategy. *tests/unit/app/core/test_security.py:37*
- [X] The denylist must include password, passwd, token, secret, key, credential, authorization, auth, API key, private key, access key, login, session, cookie, bearer, broker, and encryption-related patterns. *app/core/security.py:58*
- [X] Denylist matching must be case-insensitive. *app/core/security.py:58*
- [X] Denylist matching must support partial-key matching for common sensitive names. *app/core/security.py:58*
- [X] Redaction helpers must provide an explicit allowlist mechanism for fields that are safe to log despite matching denylist patterns. *tests/unit/app/core/test_security.py:37*
- [X] Redaction allowlist decisions must be narrow and field-specific. *tests/unit/app/core/test_security.py:37*
- [X] Redaction allowlist decisions must not allow broad wildcard exposure of secrets. *tests/unit/app/core/test_security.py:37*
- [X] Redaction helpers must expose diagnostics showing which fields were redacted without exposing redacted values. *tests/unit/app/core/test_security.py:37*
- [X] Redaction must preserve non-sensitive fields. *tests/unit/app/core/test_security.py:37*
- [X] Redaction must handle nested dictionaries and lists. *tests/unit/app/core/test_security.py:37*
- [X] Redaction must stop safely at `MAX_REDACTION_DEPTH` and mark truncated structures. *app/core/security.py:31*
- [X] Redaction must be applied before sensitive values appear in logs, error responses, metadata, remediation text, tool responses, events, notifications, metrics, health checks, dead-letter diagnostics, or canonical JSON payloads. *tests/unit/app/core/test_security.py:37*
- [X] Canonical JSON serialization must redact sensitive values by default unless a caller explicitly disables redaction in a trusted internal context. *tests/unit/app/core/test_security.py:37*
- [X] Canonical JSON serialization must expose redaction configuration through documented options. *tests/unit/app/core/test_security.py:37*
- [X] Password hashing must use Argon2id as the preferred production algorithm. *app/core/security.py:58*
- [X] If Argon2id is unavailable, the implementation must fail clearly unless a separately approved fallback is configured. *tests/unit/app/utils/test_validations.py:95*
- [X] Password verification must use constant-time comparison where relevant. *app/core/security.py:58*
- [X] Encryption features must use `cryptography.fernet.Fernet` for phase 1 symmetric encryption when encryption is enabled. *app/core/security.py:58*
- [X] Missing `cryptography` must not break module import, but encryption/decryption calls must fail with a clear configuration error. *tests/unit/app/utils/test_validations.py:95*
- [X] Encryption key loading must never log key material. *app/core/security.py:58*
- [X] Environment-based encryption keys must use `ENCRYPTION_KEY`. *app/core/security.py:58*
- [X] `ENCRYPTION_KEY` must be a 32-byte URL-safe base64-encoded Fernet key when environment-based key loading is used. *app/core/security.py:58*
- [X] Encryption and decryption failures must not expose plaintext or key material. *tests/unit/app/utils/test_validations.py:95*
- [X] Secret version selection must choose the active item with the highest numeric version. *app/core/security.py:58*
- [X] If no active secret version exists, the function must raise `SecurityError` or return a structured `SECRET_VERSION_NOT_FOUND` error at the tool boundary. *app/core/security.py:32*
- [X] Duplicate active secret versions with the same numeric version must fail closed with `SECRET_VERSION_CONFLICT`. *app/utils/errors.py:98*
- [X] Security helpers must accept text, scalars, mappings, passwords, hashed passwords, encryption keys, encrypted tokens, and secret-version mappings. *app/core/security.py:58*
- [X] Event metadata must not include secrets. *app/core/security.py:58*
- [X] Documentation must include safe examples that do not contain real secrets. *app/core/security.py:58*
- [X] Implement `app/core/security.py (re-exported by app.utils)` before logging, settings, events, notifications, and audit-safe behavior are finalized. *app/core/security.py:58*
- [X] Security helpers must avoid expensive redaction recursion loops. *tests/unit/app/core/test_security.py:37*
- [X] Security helpers must use recursion depth protection for nested structures. *app/core/security.py:58*
- [X] Security helpers must avoid logging sensitive payloads during failure. *tests/unit/app/utils/test_validations.py:95*
- [X] Error details must not expose secrets. *app/utils/errors.py:533*
- [X] Sensitive values must be redacted before logging. *app/core/security.py:58*
- [X] Sensitive values must be redacted before appearing in error responses. *app/core/security.py:58*
- [X] Sensitive values must be redacted before appearing in metadata. *app/core/security.py:58*
- [X] Sensitive values must be redacted before appearing in remediation messages. *app/core/security.py:58*
- [X] Sensitive values must be redacted before canonical JSON serialization where configured. *app/core/security.py:58*
- [X] Sensitive values must be redacted before appearing in exception text exposed to callers. *app/core/security.py:58*
- [X] Encryption keys must never be logged. *app/core/security.py:58*
- [X] Password hashes must never be treated as plaintext. *app/core/security.py:58*
- [X] Approval packets must not leak secrets through error messages. *app/core/security.py:58*
- [X] Path helpers must defend against unsafe traversal when `base_dir` is supplied. *app/core/security.py:58*
- [X] Official AI tools must declare side effects correctly. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Side-effecting utilities must not be attached to agents without explicit approval. *app/core/security.py:58*
- [X] Validation tools must fail closed when blocked actions are detected. *tests/unit/app/utils/test_validations.py:95*
- [X] Unknown environment modes must fail validation. *tests/unit/app/utils/test_validations.py:95*
- [X] Invalid freshness evidence must be surfaced, not ignored. *tests/unit/app/utils/test_validations.py:21*
- [X] Redaction must handle nested mappings, lists, string payloads, exception messages, metadata, and returned error details. *tests/unit/app/core/test_security.py:37*
- [X] Encryption and decryption failures must not expose plaintext or key material. *tests/unit/app/utils/test_validations.py:95*
- [X] Secret selection must be deterministic. *app/core/security.py:58*
- [X] No secrets are logged. *app/core/security.py:58*
- [X] Redaction allowlist entries must be audited through configuration, tests, or documented approval. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Sensitive nested mappings and lists must be redacted without mutating input. *app/core/security.py:58*
- [X] Excessively deep redaction structures must stop at `MAX_REDACTION_DEPTH`. *app/core/security.py:31*
- [X] Invalid encryption input must fail safely. *tests/unit/app/utils/test_validations.py:21*
- [X] Missing or malformed encryption keys must fail without leaking key material. *tests/unit/app/utils/test_validations.py:95*
- [X] Missing active secret versions must fail with `SecurityError` or `SECRET_VERSION_NOT_FOUND`. *app/core/security.py:32*
- [X] Duplicate active secret versions with the same numeric version must fail with `SECRET_VERSION_CONFLICT`. *app/utils/errors.py:98*
- [X] Security regression tests must prove common secret patterns do not leak. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Branch coverage must be meaningful for validators and security helpers. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Official AI tool tests must verify no secret leakage where relevant. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Security tests must verify redaction, nested redaction, password hashing, password verification, Fernet key behavior, encryption round trip, invalid tokens, secret selection, and `SECRET_VERSION_NOT_FOUND`. *app/core/security.py:32*
- [X] Security tests must verify metric labels reject sensitive or high-cardinality values. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Security tests verify redaction and no secret leakage. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/settings.py`

Functions/classes:

- `HARUQUANT_HOME`
- `RuntimeSettings`
- `HaruQuantConfigurationError`
- `CONFIGURATION_ERROR`

Requirements:

- [X] `load_runtime_settings` must remain a support helper and must not be attached to agents by default. *app/utils/settings.py:204*
- [X] The module must define immutable typed runtime settings. *app/utils/settings.py:204*
- [X] Runtime settings must include environment, log level, data directory, cache directory, audit directory, timezone, and strict validation. *app/utils/settings.py:204*
- [X] Runtime settings must include logging configuration. *app/utils/settings.py:204*
- [X] Logging configuration must include optional log directory, file logging enablement, rotation maximum size, retained file count, and retention deletion policy. *tests/unit/app/utils/test_logger.py:111*
- [X] Logging configuration must include human-readable console format selection and color enablement or disablement. *app/utils/settings.py:204*
- [X] Runtime settings must include auth configuration. *app/utils/settings.py:204*
- [X] Runtime settings must include Event Bus configuration. *app/utils/settings.py:204*
- [X] Runtime settings must include notification configuration. *app/utils/settings.py:204*
- [X] Runtime settings must include observability configuration. *app/utils/settings.py:204*
- [X] The module must load runtime settings from explicit calls only. *app/utils/settings.py:204*
- [X] The module must load runtime settings from mappings. *app/utils/settings.py:204*
- [X] The module must inject runtime settings into an explicitly supplied mutable target mapping. *app/utils/settings.py:204*
- [X] Required settings must have deterministic defaults where safe. *app/utils/settings.py:204*
- [X] Sensitive settings must not be logged. *app/utils/settings.py:204*
- [X] Environment names must be validated. *app/utils/settings.py:204*
- [X] Path settings must use `Path` objects. *app/utils/settings.py:204*
- [X] `.env` loading must be optional and dependency-aware. *app/utils/settings.py:204*
- [X] Settings source precedence must be explicit mapping/function arguments, then environment variables, then `.env` file, then safe defaults. *app/utils/settings.py:204*
- [X] Importing `app.utils` must not read `.env`. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Optional dependency absence must not break import. *app/utils/settings.py:204*
- [X] Optional dependency absence must fail only when the requested feature requires the dependency. *tests/unit/app/utils/test_validations.py:95*
- [X] Invalid settings must fail clearly with configuration errors. *tests/unit/app/utils/test_validations.py:21*
- [X] `strict_validation=True` must escalate non-critical validation warnings to failures where the caller asks settings to enforce strict behavior. *tests/unit/app/utils/test_validations.py:95*
- [X] `strict_validation=False` must allow warnings to be returned or logged without failing settings load. *tests/unit/app/utils/test_validations.py:95*
- [X] `inject_runtime_settings` must mutate only the provided target mapping and return that mapping. *app/utils/settings.py:403*
- [X] Default runtime paths must resolve under `HARUQUANT_HOME` when configured. *app/utils/settings.py:27*
- [X] Production deployments must configure `HARUQUANT_HOME` explicitly. *app/utils/settings.py:27*
- [X] Default directories must be `data`, `cache`, and `audit` under the resolved HaruQuant home directory. *app/utils/settings.py:204*
- [X] OHLCV validation must accept configurable datetime, open, high, low, close, volume, and spread column names. *app/utils/settings.py:204*
- [X] OHLCV validation must accept configurable gap multiplier, spike threshold, issue-sample limit, and returned-issue limit. *app/utils/settings.py:204*
- [X] Schema validators must accept resource-limit configuration where applicable. *app/utils/settings.py:204*
- [X] Freshness validation must accept timestamp metadata, configurable timestamp field, injected `now`, and `max_age_seconds`. *app/utils/settings.py:204*
- [X] Settings loaders must accept mappings and optional `.env` file paths. *app/utils/settings.py:204*
- [X] Settings loaders must return `RuntimeSettings`. *app/utils/settings.py:62*
- [X] Settings injection must return the same target mapping it mutates. *app/utils/settings.py:204*
- [X] Implement `app/utils/settings.py` before adapters and runtime configuration consumers. *app/utils/settings.py:204*
- [X] Importing any `app.utils` module must not read `.env` files. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Importing any `app.utils` module must not mutate environment variables. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Time handling must be deterministic and timezone-safe across supported runtime environments. *app/utils/settings.py:204*
- [X] Missing optional dependency failures must use `HaruQuantConfigurationError`, `CONFIGURATION_ERROR`, or the standard tool error envelope where applicable. *app/utils/settings.py:28*
- [X] Missing pandas fails only when dataframe helpers are called, with a clear configuration/dependency error. *tests/unit/app/utils/test_validations.py:95*
- [X] When `HARUQUANT_HOME` is not configured, local/test defaults must resolve under a deterministic `.haruquant` directory beneath the current working directory. *app/utils/settings.py:27*
- [X] Spikes must be detected using configurable thresholds. *app/utils/settings.py:204*
- [X] Schema validation of deeply nested payloads must stop at configured depth. *app/utils/settings.py:204*
- [X] Invalid environment modes must fail. *tests/unit/app/utils/test_validations.py:21*
- [X] Logger tests must verify file logging writes only to configured safe log directories. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Logger tests must verify log rotation by maximum file size or equivalent configured policy. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Logger tests must verify old rotated log files are deleted according to configured retention limits without deleting unrelated files. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Data-quality tests must verify 10,000 bad rows return no more than configured issue and sample limits. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Settings tests must verify defaults, mapping load, invalid environments, `strict_validation`, path normalization, and injection. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/auth.py`

Functions/classes:

- `Error`
- `SECURITY_ERROR`

Requirements:

- [X] The system must implement `app/utils/` as the shared utility foundation for HaruQuantAI. *app/utils/auth.py:50*
- [X] The module must support higher-level domains including data, research, simulation, risk, portfolio, execution, analytics, governance, and agentic workflows. *app/utils/auth.py:50*
- [X] The module must provide project-wide structured logging. *app/utils/auth.py:50*
- [X] The module must provide standard HaruQuant tool response envelopes. *app/utils/auth.py:50*
- [X] The module must provide deterministic error codes and exception mapping. *app/utils/auth.py:50*
- [X] The module must provide timestamp and timezone normalization using a UTC-first policy. *app/utils/auth.py:50*
- [X] The module must provide safe path handling. *app/utils/auth.py:50*
- [X] The module must provide dataframe and OHLCV helper utilities. *app/utils/auth.py:50*
- [X] The module must provide OHLCV data-quality validation with bounded diagnostics and deterministic scoring. *app/utils/auth.py:50*
- [X] The module must provide schema, payload, risk-level, numeric-range, and contract validation. *app/utils/auth.py:50*
- [X] The module must provide security helpers for redaction, hashing, encryption, decryption, and secret-version selection. *tests/unit/app/core/test_security.py:37*
- [X] The module must provide runtime settings loading and injection with deterministic source precedence. *app/utils/auth.py:50*
- [X] The module must provide standard execution timing helpers for consistent `execution_ms` values. *app/utils/auth.py:50*
- [X] The module must provide explicit tool-response schema validation constants. *app/utils/auth.py:50*
- [X] The module must provide schema-version compatibility checks for validation contracts. *app/utils/auth.py:50*
- [X] The module must provide resource-limit controls for large validation workloads. *app/utils/auth.py:50*
- [X] The module must support lazy loading for pandas and other heavy optional dependencies. *app/utils/auth.py:50*
- [X] The module must preserve a stateless, diagnostic-only data-quality boundary. *app/utils/auth.py:50*
- [X] The module must support string-serializable constants and enum-friendly canonicalization. *app/utils/auth.py:50*
- [X] The module must support extensible domain error mapping through `Error` and compatible `code` attributes. *app/utils/errors.py:533*
- [X] The module must provide auth context validation and authorization support helpers. *app/utils/auth.py:50*
- [X] Auth helpers may validate identity context, roles, scopes, and permissions, but must not become the identity provider. *app/utils/auth.py:50*
- [X] Authorization checks must deny access by default when context is missing or malformed. *app/utils/auth.py:50*
- [X] Agent access to official tools must be allowlisted. *app/utils/auth.py:50*
- [X] Agent/tool caller:** Calls approved official AI tools and receives standard envelopes. *app/utils/auth.py:50*
- [X] Authorized tool caller:** A caller with explicit permission to invoke an official AI tool. *app/utils/auth.py:50*
- [X] Authenticated principal:** A user, service, workflow, or agent identity represented in auth context. *app/utils/auth.py:50*
- [X] Workflow caller:** Uses validation, tracing, metadata, event, alert, and handoff utilities in automated workflows. *app/utils/auth.py:50*
- [X] Production module developer:** Imports support helpers from `app.utils` and uses typed native helper APIs. *app/utils/auth.py:50*
- [X] Higher-level domain module:** Data, research, simulation, risk, portfolio, execution, analytics, governance, and agentic workflow modules consume utility functionality. *app/utils/auth.py:50*
- [X] Human approver:** Uses or is represented by approval packets requiring action, reason, evidence, risk class, and approval status. *app/utils/auth.py:50*
- [X] Maintainer/reviewer:** Governs public API changes, CI gates, quality checks, and acceptance criteria. *app/utils/auth.py:50*
- [X] Security reviewer:** A maintainer responsible for auth, secret redaction, encrypted payload handling, and no-leak guarantees. *tests/unit/app/core/test_security.py:37*
- [X] The utils module will provide auth primitives and validation helpers, but the application or infrastructure layer will own external identity-provider integration. *app/utils/auth.py:50*
- [X] Agent access to encryption or decryption must require explicit security approval, permission checks, and audit logging. *app/utils/auth.py:50*
- [X] The module must define a shared authentication context model for internal tools, agents, workflows, and services. *app/utils/auth.py:50*
- [X] The auth context must support principal ID, principal type, roles, permissions, scopes, tenant or environment context where applicable, request ID, workflow ID, and correlation ID. *app/utils/auth.py:50*
- [X] The module must provide validation helpers for authenticated principal context. *app/utils/auth.py:50*
- [X] The module must provide authorization helper checks for required roles, permissions, scopes, and tool names. *app/utils/auth.py:50*
- [X] Authorization helpers must deny by default when identity, permission, role, scope, or tool context is missing. *app/utils/auth.py:50*
- [X] Agents must be authorized through an explicit tool allowlist before accessing official AI tools. *app/utils/auth.py:50*
- [X] Side-effecting or sensitive utilities must require explicit permission checks before execution. *app/utils/auth.py:50*
- [X] Auth helpers must return deterministic validation results or standard tool error envelopes at official tool boundaries. *app/utils/auth.py:50*
- [X] Auth helpers must not validate external identity-provider tokens unless an explicit adapter is supplied by the application layer. *app/utils/auth.py:50*
- [X] Auth helpers must not contact external identity providers at import time. *app/utils/auth.py:50*
- [X] Auth context must be redacted before logging, events, metrics, or error reporting. *app/utils/auth.py:50*
- [X] Auth failures must use deterministic error codes such as `PERMISSION_DENIED`, `INVALID_AUTH_CONTEXT`, or `AUTHORIZATION_FAILED`. *tests/unit/app/utils/test_validations.py:95*
- [X] Authentication and authorization events must be observable through logs, metrics, and sanitized audit events. *app/utils/auth.py:50*
- [X] Auth helpers must accept sanitized auth context mappings or typed auth context objects. *app/utils/auth.py:50*
- [X] Auth helpers must accept required permissions, roles, scopes, and tool names. *app/utils/auth.py:50*
- [X] Auth helpers must return allow/deny decisions with sanitized reason details. *app/utils/auth.py:50*
- [X] Redaction allowlist misuse must return `SECURITY_ERROR` or a more specific deterministic security code. *tests/unit/app/core/test_security.py:37*
- [X] Documentation must include examples of safe redaction allowlist use. *tests/unit/app/core/test_security.py:37*
- [X] Implement `app/utils/auth.py` before tool allowlists and side-effect permission checks. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Auth helpers must avoid hidden global mutable state. *app/utils/auth.py:50*
- [X] Auth failures must map to `PERMISSION_DENIED`, `INVALID_AUTH_CONTEXT`, or `AUTHORIZATION_FAILED`. *tests/unit/app/utils/test_validations.py:95*
- [X] Auth context must be redacted before logging. *app/utils/auth.py:50*
- [X] Agent tool authorization must use explicit allowlists. *app/utils/auth.py:50*
- [X] Redaction allowlist entries must be narrow and auditable. *tests/unit/app/core/test_security.py:37*
- [X] Documentation must describe auth context fields. *app/utils/auth.py:50*
- [X] Documentation must describe authorization deny-by-default behavior. *app/utils/auth.py:50*
- [X] Documentation must describe redaction denylist defaults. *tests/unit/app/core/test_security.py:37*
- [X] Documentation must describe audited redaction allowlist configuration. *tests/unit/app/core/test_security.py:37*
- [X] Documentation must warn against broad redaction allowlist rules. *tests/unit/app/core/test_security.py:37*
- [X] File logging is explicit, safely scoped, rotating, and retention-limited when enabled. *app/utils/auth.py:50*
- [X] Auth helpers deny by default and enforce tool allowlists. *app/utils/auth.py:50*
- [X] The module must provide canonical JSON serialization for audit, hashing, caching, reproducible tests, and comparison workflows. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Missing auth context must deny access. *app/utils/auth.py:50*
- [X] Malformed auth context must deny access with a deterministic error. *app/utils/auth.py:50*
- [X] Missing required role, permission, or scope must deny access. *app/utils/auth.py:50*
- [X] Unknown tool name in authorization checks must deny access. *app/utils/auth.py:50*
- [X] Redaction allowlist conflicts with denylist must fail closed unless explicitly approved. *tests/unit/app/core/test_security.py:37*
- [X] Redaction allowlist configuration must be reviewed and tested. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Security tests must verify redaction denylist matching. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Security tests must verify audited allowlist exceptions. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Security tests must verify denylist/allowlist conflict behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Auth tests must cover valid auth context. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Auth tests must cover missing auth context. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Auth tests must cover malformed auth context. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Auth tests must cover missing role, permission, and scope. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Auth tests must cover denied-by-default behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Auth tests must verify no token or credential leakage. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Redaction denylist and audited allowlist behavior is implemented and tested. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/event_bus.py`

Functions/classes:

- `event_id`
- `causation_id`
- `BACKPRESSURE_EXCEEDED`
- `QUEUE_FULL`

Requirements:

- [X] The module must provide request, workflow, generic ID, version, correlation ID, causation ID, and idempotency helpers. *app/utils/event_bus.py:51*
- [X] The module must provide Event Bus and pub/sub primitives. *app/utils/event_bus.py:51*
- [X] Event Bus utilities may route events, but must not own application orchestration. *app/utils/event_bus.py:51*
- [X] Event Bus utilities must not place trades, approve trades, modify orders, activate live systems, or override kill switches. *app/utils/event_bus.py:51*
- [X] Event publisher:** A module or workflow that emits validated events. *app/utils/event_bus.py:51*
- [X] Event subscriber:** A handler that receives events by topic or event type. *app/utils/event_bus.py:51*
- [X] The utils module will provide Event Bus contracts and an in-process implementation, while production broker-backed adapters may live in infrastructure modules or optional adapters. *app/utils/event_bus.py:51*
- [X] The system must provide a shared Event Bus abstraction for internal utility, workflow, alert, and error-routing events. *app/utils/event_bus.py:51*
- [X] The system must define a standard event envelope. *app/utils/event_bus.py:51*
- [X] The standard event envelope must include `event_id`, `event_type`, `event_version`, `source`, `severity`, `timestamp`, `request_id`, `workflow_id`, `correlation_id`, `causation_id`, `idempotency_key`, `payload`, and `metadata`. *app/utils/event_bus.py:51*
- [X] Event payloads must be JSON-serializable or fail validation clearly. *tests/unit/app/utils/test_validations.py:95*
- [X] Event payloads must be redacted before logging, metrics labeling, notification routing, audit serialization, or dead-letter forwarding. *app/utils/event_bus.py:51*
- [X] The Event Bus must support publish and subscribe operations. *app/utils/event_bus.py:51*
- [X] The Event Bus must support topic or event-type subscriptions. *app/utils/event_bus.py:51*
- [X] The Event Bus must support handler registration and unregistration. *app/utils/event_bus.py:51*
- [X] Distributed broker adapters are not required to guarantee global ordering unless the adapter explicitly documents that guarantee. *app/utils/event_bus.py:51*
- [X] The Event Bus must support error isolation so one failing subscriber does not silently prevent other subscribers from receiving the event. *tests/unit/app/utils/test_validations.py:95*
- [X] The Event Bus must route subscriber failures to the error-routing mechanism. *tests/unit/app/utils/test_validations.py:95*
- [X] The Event Bus must support retry policy metadata for delivery failures. *tests/unit/app/utils/test_validations.py:95*
- [X] The Event Bus must support dead-letter routing for events that exceed retry limits. *app/utils/event_bus.py:51*
- [X] The Event Bus must support idempotency keys to reduce duplicate event processing. *tests/unit/app/utils/test_event_bus.py:13*
- [X] Idempotency keys must have both a configurable TTL and a configurable maximum cache size. *app/utils/event_bus.py:51*
- [X] The default idempotency TTL must be short enough to prevent memory growth but long enough to cover expected retry windows. *app/utils/event_bus.py:51*
- [X] Idempotency entries must store compact metadata rather than full event payloads by default. *app/utils/event_bus.py:51*
- [X] Idempotency duplicate detection may use hashes of sanitized canonical event payloads and must not retain full sensitive payloads. *tests/unit/app/utils/test_event_bus.py:13*
- [X] Idempotency-key storage must not grow without bound in long-running processes. *app/utils/event_bus.py:51*
- [X] Expired idempotency keys must be evicted deterministically. *app/utils/event_bus.py:51*
- [X] The default idempotency cache eviction policy must evict expired entries first, then oldest entries. *app/utils/event_bus.py:51*
- [X] Idempotency cache eviction must be observable through logs and metrics. *app/utils/event_bus.py:51*
- [X] Idempotency cache state must not expose sensitive payloads, raw event bodies, tokens, credentials, approval packets, or private data. *app/utils/event_bus.py:51*
- [X] Duplicate idempotency keys with different payload hashes must fail safely or emit deterministic conflict diagnostics. *tests/unit/app/utils/test_validations.py:95*
- [X] The Event Bus must support correlation IDs across tool calls, logs, notifications, and metrics. *app/utils/event_bus.py:51*
- [X] The Event Bus must expose bounded queue depth or handler backlog diagnostics. *app/utils/event_bus.py:51*
- [X] Event Bus delivery diagnostics must include delivered, failed, retried, dead-lettered, dropped counts, and queue depth where applicable. *tests/unit/app/utils/test_validations.py:95*
- [X] When the Event Bus queue is full, publish operations must immediately return a deterministic `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` error code. *tests/unit/app/utils/test_event_bus.py:36*
- [X] Queue-full behavior must return `BACKPRESSURE_EXCEEDED` when the caller can retry later. *app/utils/event_bus.py:51*
- [X] Queue-full behavior may return `QUEUE_FULL` for lower-level queue diagnostics. *app/utils/event_bus.py:51*
- [X] Event publishers must receive enough structured queue-full detail to implement retry, degradation, or fail-closed behavior. *tests/unit/app/utils/test_validations.py:95*
- [X] Event Bus queue policies must be explicit modes such as fail-fast, bounded wait, or lossy-drop. *tests/unit/app/utils/test_validations.py:95*
- [X] Production Event Bus queue policy must default to fail-fast for critical workflows. *tests/unit/app/utils/test_validations.py:95*
- [X] Queue-full behavior must not silently drop events unless the caller explicitly selected a lossy policy. *app/utils/event_bus.py:51*
- [X] Lossy-drop behavior must be allowed only for explicitly configured low-severity telemetry events. *app/utils/event_bus.py:51*
- [X] Dropped events must be counted in metrics. *app/utils/event_bus.py:51*
- [X] Dropped events must be logged with sanitized metadata. *app/utils/event_bus.py:51*
- [X] Queue-full diagnostics must include event type, source, severity, queue name or topic, queue depth, configured queue limit, request ID, workflow ID, and correlation ID where available. *app/utils/event_bus.py:51*
- [X] Queue-full diagnostics must not include raw event payloads by default. *app/utils/event_bus.py:51*
- [X] The Event Bus must not open network connections during module import. *app/utils/event_bus.py:51*
- [X] Production external broker adapters must be dependency-aware and lazy-loaded. *app/utils/event_bus.py:51*
- [X] Production external broker adapters must fail clearly when required optional dependencies are missing. *tests/unit/app/utils/test_validations.py:95*
- [X] Production external broker adapters must implement circuit breakers. *tests/unit/app/utils/test_observability.py:36*
- [X] Event Bus support must not approve trades, place orders, mutate broker state, or make risk decisions. *app/utils/event_bus.py:51*
- [X] External pub/sub adapters must implement a circuit-breaker pattern. *tests/unit/app/utils/test_observability.py:36*
- [X] Official AI tool responses must not return whole dataframes. *app/utils/event_bus.py:51*
- [X] Event Bus publishing must accept an event type, source, severity, payload, metadata, request ID, workflow ID, correlation ID, and idempotency key. *app/utils/event_bus.py:51*
- [X] Event Bus subscription must accept topic or event-type filters and handler references. *app/utils/event_bus.py:51*
- [X] Event Bus publish operations must return deterministic delivery or enqueue results. *app/utils/event_bus.py:51*
- [X] Event Bus delivery diagnostics must include delivered, failed, retried, dead-lettered, dropped counts, and queue depth where applicable. *tests/unit/app/utils/test_validations.py:95*
- [X] Queue-full errors must include sanitized queue diagnostics. *app/utils/event_bus.py:51*
- [X] Queue diagnostics must not include raw payloads. *app/utils/event_bus.py:51*
- [X] Circuit-breaker diagnostics must not include credentials, provider tokens, message bodies, or raw event payloads. *tests/unit/app/utils/test_observability.py:36*
- [X] Implement `app/utils/event_bus.py` before error routing and notification routing. *app/utils/event_bus.py:51*
- [X] Queue-full publishing returns deterministic `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` diagnostics. *app/utils/event_bus.py:51*
- [X] Importing any `app.utils` module must not configure global logging handlers unexpectedly. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Importing any `app.utils` module must not initialize external pub/sub clients. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Event Bus handler registration, unregistration, publishing, retry, dead-letter handling, and idempotency tracking must be thread-safe and/or async-safe. *tests/unit/app/utils/test_logger.py:136*
- [X] Event Bus handlers must not share mutable event payloads unless payloads are explicitly copied or treated as immutable by contract. *app/utils/event_bus.py:51*
- [X] Event Bus event versioning must support forward compatibility for event consumers. *app/utils/event_bus.py:51*
- [X] Event Bus delivery diagnostics must remain consistent under concurrent publishing. *tests/unit/app/utils/test_logger.py:136*
- [X] Optional Event Bus broker dependencies must be lazy-loaded. *app/utils/event_bus.py:51*
- [X] Utilities must be safe with large datasets. *app/utils/event_bus.py:51*
- [X] Utilities must avoid unnecessary deep copies. *app/utils/event_bus.py:51*
- [X] Dataframe helpers must document copy, view, and transformed-data behavior. *app/utils/event_bus.py:51*
- [X] Agent-facing diagnostics must prefer summaries, counts, and compact samples. *app/utils/event_bus.py:51*
- [X] Returned issue lists and samples must be bounded. *app/utils/event_bus.py:51*
- [X] Event Bus diagnostics must remain bounded to avoid oversized logs and metrics. *app/utils/event_bus.py:51*
- [X] Event Bus idempotency storage must be bounded by TTL and maximum cache size. *app/utils/event_bus.py:51*
- [X] Event Bus queues must have explicit limits. *app/utils/event_bus.py:51*
- [X] Queue-full behavior must fail fast or follow a documented bounded policy. *tests/unit/app/utils/test_validations.py:95*
- [X] Lossy-drop behavior may be allowed only when explicitly configured for low-severity telemetry events. *app/utils/event_bus.py:51*
- [X] Backpressure diagnostics must be bounded and redacted. *app/utils/event_bus.py:51*
- [X] External Event Bus broker outages must be isolated through circuit breakers and deterministic error codes. *tests/unit/app/utils/test_observability.py:36*
- [X] Event publish failures must map to `EVENT_PUBLISH_FAILED`. *tests/unit/app/utils/test_validations.py:95*
- [X] Event subscriber failures must map to `EVENT_HANDLER_FAILED`. *tests/unit/app/utils/test_validations.py:95*
- [X] Dead-letter routing failures must map to `EVENT_DEAD_LETTER_FAILED`. *tests/unit/app/utils/test_validations.py:95*
- [X] Queue-full errors must be returned immediately to publishers. *app/utils/event_bus.py:51*
- [X] Backpressure errors must be distinct from subscriber execution errors. *app/utils/event_bus.py:51*
- [X] Subscriber execution errors must not be misclassified as publish failures unless publish requires synchronous all-handler success. *tests/unit/app/utils/test_validations.py:95*
- [X] Sensitive values must be redacted before appearing in Event Bus payload logs. *app/utils/event_bus.py:51*
- [X] Event payloads must be redacted before publication when they contain sensitive fields. *app/utils/event_bus.py:51*
- [X] Dead-letter event storage, if configured outside utils, must receive redacted payloads by default. *app/utils/event_bus.py:51*
- [X] Idempotency keys must not encode raw secrets or raw payloads. *app/utils/event_bus.py:51*
- [X] Event IDs, request IDs, workflow IDs, and correlation IDs must be safe for logs and metrics. *app/utils/event_bus.py:51*
- [X] Event payload hashes, if used for idempotency conflict detection, must not allow reconstruction of sensitive payloads. *app/utils/event_bus.py:51*
- [X] Dead-letter payloads must be redacted by default before storage or forwarding. *app/utils/event_bus.py:51*
- [X] Documentation must describe Event Bus event envelope fields. *app/utils/event_bus.py:51*
- [X] Documentation must define Event Bus idempotency TTL behavior. *app/utils/event_bus.py:51*
- [X] Documentation must define Event Bus idempotency maximum cache-size behavior. *app/utils/event_bus.py:51*
- [X] Documentation must define Event Bus queue-full and backpressure behavior. *tests/unit/app/utils/test_event_bus.py:36*
- [X] Documentation must define Event Bus delivery, retry, and dead-letter behavior. *app/utils/event_bus.py:51*
- [X] Documentation must define Event Bus concurrency guarantees. *app/utils/event_bus.py:51*
- [X] Documentation must define whether the Event Bus implementation is synchronous, asynchronous, or dual-mode. *app/utils/event_bus.py:51*
- [X] Documentation must state that deterministic ordered delivery applies to the in-process Event Bus per event type, not necessarily to distributed broker adapters. *app/utils/event_bus.py:51*
- [X] Documentation must describe circuit-breaker configuration for external pub/sub adapters. *tests/unit/app/utils/test_observability.py:36*
- [X] Documentation must document each event type's ordering, durability, retry, and loss-tolerance expectations. *app/utils/event_bus.py:51*
- [X] Event Bus idempotency storage is bounded by TTL and maximum cache size. *app/utils/event_bus.py:51*
- [X] Event Bus idempotency storage uses compact metadata rather than full event payloads by default. *app/utils/event_bus.py:51*
- [X] Event Bus queue policies are explicit and production critical workflows default to fail-fast behavior. *tests/unit/app/utils/test_validations.py:95*
- [X] Event Bus publish, subscribe, unsubscribe, retry, and dead-letter paths are thread-safe and/or async-safe. *tests/unit/app/utils/test_logger.py:136*
- [X] External pub/sub adapters have circuit breakers. *tests/unit/app/utils/test_observability.py:36*
- [X] Documentation covers Event Bus backpressure, idempotency, circuit breakers, clock drift, schema field paths, and redaction allowlist governance. *tests/unit/app/core/test_security.py:37*
- [X] The system must provide an in-process pub/sub mechanism suitable for local development, unit tests, and deterministic workflow tests. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] The Event Bus must support disabled or no-op adapter behavior for tests and local development where event delivery is intentionally suppressed. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] The in-process Event Bus must guarantee deterministic, ordered handler execution per event type to ensure reproducible test outcomes. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Idempotency tracking must be testable with injected clocks or deterministic time controls. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event publishing with missing event type must fail validation. *tests/unit/app/utils/test_validations.py:95*
- [X] Event publishing with unserializable payload must fail validation. *tests/unit/app/utils/test_validations.py:95*
- [X] Duplicate event IDs must be handled idempotently where idempotency keys are supplied. *app/utils/event_bus.py:51*
- [X] Idempotency cache TTL expiration must not break valid future event processing. *app/utils/event_bus.py:51*
- [X] Idempotency cache eviction must not expose old event payloads. *app/utils/event_bus.py:51*
- [X] Concurrent publish calls for the same idempotency key must not double-deliver an event. *tests/unit/app/utils/test_logger.py:136*
- [X] Subscriber failure must not prevent other subscribers from receiving the event. *tests/unit/app/utils/test_validations.py:95*
- [X] Concurrent subscriber registration and publishing must not corrupt handler lists. *tests/unit/app/utils/test_logger.py:136*
- [X] Concurrent subscriber unregistration during publishing must have deterministic behavior. *tests/unit/app/utils/test_logger.py:136*
- [X] Repeated subscriber failures must route to dead-letter handling after configured retry limits. *tests/unit/app/utils/test_validations.py:95*
- [X] Event Bus queue overflow must return `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` and must not block indefinitely. *app/utils/event_bus.py:51*
- [X] External pub/sub adapter outage must open the circuit after the configured threshold. *tests/unit/app/utils/test_observability.py:36*
- [X] Half-open circuit recovery must not create duplicate event delivery. *tests/unit/app/utils/test_event_bus.py:13*
- [X] Logger tests must verify duplicate handler prevention. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must cover publish success. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must cover subscription and unsubscription. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify deterministic ordered handler execution per event type for the in-process bus. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must cover subscriber failure isolation. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must cover retry and dead-letter behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must cover idempotency keys. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify idempotency TTL expiration. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify maximum idempotency cache size enforcement. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify duplicate idempotency key handling. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify concurrent publish behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify concurrent subscribe and unsubscribe behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify concurrent retry and dead-letter behavior where supported. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must cover payload serialization failure. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify queue-full behavior returns `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED`. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must cover deterministic backpressure behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify dropped-event metrics. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must cover queue limit or backlog diagnostics. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify external adapter circuit-breaker closed, open, and half-open states with fake adapters. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must verify no secret leakage in event logs. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must use fake clock and fake queue implementations where needed for deterministic time and queue behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event Bus tests must cover disabled or no-op adapter behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must cover Event Bus metrics. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must verify queue-depth metrics. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/errors.py (ErrorRouter / route_error)`

Functions/classes:

- `ErrorRoute`
- `AlertRoute`
- `route_error`
- `route_alert`
- `build_error_event`
- `sanitize_error_payload`

Requirements:

- [X] The module must provide early alert routing and error routing so the rest of the system can report issues consistently. *app/utils/errors.py:1301*
- [X] Alert routing must fail safely and must not expose sensitive information. *tests/unit/app/utils/test_validations.py:95*
- [X] The Event Bus is intended for utility, workflow, alert, and error-routing events, not direct trading execution. *app/utils/errors.py:1301*
- [X] The system must provide a standard error event model. *app/utils/errors.py:1301*
- [X] The error event model must include error code, severity, source module, source function or tool, request ID, workflow ID, correlation ID, sanitized message, sanitized details, and timestamp. *app/utils/errors.py:1301*
- [X] Expected validation failures must be routable as warning or error events depending on severity. *tests/unit/app/utils/test_validations.py:95*
- [X] Unexpected execution failures must be routable as error or critical events. *tests/unit/app/utils/test_validations.py:95*
- [X] Critical system failures must be routable to notifications. *tests/unit/app/utils/test_validations.py:95*
- [X] Error routing must deduplicate repeated identical errors within a configurable time window. *app/utils/errors.py:533*
- [X] Error routing must prevent recursive alert storms. *app/utils/errors.py:533*
- [X] Error routing must redact secrets before publishing events, logging, metrics, or notifications. *app/utils/errors.py:533*
- [X] Error routing must preserve enough diagnostic context for troubleshooting without exposing sensitive payloads. *app/utils/errors.py:533*
- [X] Error routing must support severity-based routing rules. *app/utils/errors.py:533*
- [X] Error routing must support environment-specific routing rules. *app/utils/errors.py:533*
- [X] Error routing must support suppression rules for known noisy non-critical errors. *app/utils/errors.py:533*
- [X] Error routing must expose metrics for routed, suppressed, retried, failed, and dead-lettered error events. *app/utils/errors.py:533*
- [X] Error routing failures must not recursively trigger infinite error routing. *app/utils/errors.py:533*
- [X] Error routing must preserve the original error code and attach routing failure code separately when both exist. *app/utils/errors.py:533*
- [X] Error routing must accept sanitized exception context, deterministic error code, severity, request ID, workflow ID, and correlation ID. *app/utils/errors.py:533*
- [X] Error routing must return routed, suppressed, deduplicated, throttled, or failed status. *app/utils/errors.py:533*
- [X] Documentation must include a production readiness checklist for secrets, auth, alert routing, and metrics before enabling live workflows. *app/utils/errors.py:1301*
- [X] Implement `app/utils/errors.py (ErrorRouter / route_error)` before notification routing. *app/utils/errors.py:1301*
- [X] Error routing failures must not recursively trigger infinite error routing. *app/utils/errors.py:533*
- [X] Alert failures must be logged and measured without exposing secrets. *tests/unit/app/utils/test_validations.py:95*
- [X] Error routing must preserve original error code and attach routing failure code separately when both exist. *app/utils/errors.py:533*
- [X] Error routing must sanitize exception text before alerting. *app/utils/errors.py:533*
- [X] Documentation must describe error routing behavior and severity rules. *app/utils/errors.py:1301*
- [X] Documentation must describe how alerts and error routing are initialized early in the system lifecycle. *app/utils/errors.py:1301*
- [X] Recursive error routing must be detected and suppressed. *app/utils/errors.py:1301*
- [X] Error-routing tests must cover validation error routing. *app/utils/errors.py:533*
- [X] Error-routing tests must cover unexpected exception routing. *app/utils/errors.py:533*
- [X] Error-routing tests must cover deduplication and throttling. *app/utils/errors.py:533*
- [X] Error-routing tests must cover recursive error suppression. *app/utils/errors.py:533*
- [X] Error-routing tests must verify recursive alert suppression under circuit-open and notification-failure scenarios. *app/utils/errors.py:533*

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

- [X] The module must provide shared status, severity, risk-level, environment-mode, auth, event, notification, and health-state constants. *app/utils/notifications.py:78*
- [X] The module must provide notification routing primitives for email, Telegram, and desktop channels. *app/utils/notifications.py:78*
- [X] Utilities may validate, normalize, redact, serialize, route events, emit notifications, record metrics, and report issues. *app/utils/notifications.py:78*
- [X] Notification utilities may alert humans or systems, but must not make trading, portfolio, risk, or strategy decisions. *app/utils/notifications.py:78*
- [X] Email, Telegram, and desktop notifications must be disabled unless configured for the current environment. *app/utils/notifications.py:78*
- [X] Production desktop notifications must be disabled by default. *app/utils/notifications.py:78*
- [X] Notification recipients must be configured explicitly. *app/utils/notifications.py:78*
- [X] Notification recipient:** A configured email, Telegram, or desktop recipient for alerts. *app/utils/notifications.py:78*
- [X] Security/audit consumer:** Relies on redacted logs, metadata, tool responses, canonical JSON, events, notifications, and secret-safe error handling. *app/utils/notifications.py:78*
- [X] Notification helpers will provide routing contracts and adapter boundaries, not hard-coded provider credentials. *app/utils/notifications.py:78*
- [X] Email, Telegram, and desktop notification providers will be configured explicitly per environment. *app/utils/notifications.py:78*
- [X] No notification channel is enabled in production without explicit configuration. *app/utils/notifications.py:78*
- [X] Auth, Event Bus, notification, and observability primitives must be support helpers by default unless explicitly promoted to official AI tools. *app/utils/notifications.py:78*
- [X] The system must provide notification routing primitives for email, Telegram, and desktop channels. *app/utils/notifications.py:78*
- [X] Notification routing must support severity-based routing. *app/utils/notifications.py:78*
- [X] Notification routing must support environment-specific routing. *app/utils/notifications.py:78*
- [X] Notification routing must support channel enablement and disablement through runtime settings. *app/utils/notifications.py:78*
- [X] Notification routing must support per-channel recipient configuration. *app/utils/notifications.py:78*
- [X] Notification routing must support safe templates for alert title, summary, severity, source, timestamp, request ID, workflow ID, and correlation ID. *app/utils/notifications.py:78*
- [X] Notification templates must render from sanitized data transfer objects rather than raw event payloads. *app/utils/notifications.py:78*
- [X] Notification templates must support markdown and plain-text fallbacks to ensure readability across email, Telegram, and desktop clients. *app/utils/notifications.py:78*
- [X] Notification rendering must degrade to plain text when a channel does not support markdown. *app/utils/notifications.py:78*
- [X] Notification template rendering failures must return deterministic notification failure diagnostics without exposing raw payloads. *tests/unit/app/utils/test_validations.py:95*
- [X] Notification routing must not include raw sensitive payloads. *app/utils/notifications.py:78*
- [X] Notification routing must redact secrets before message construction. *app/utils/notifications.py:78*
- [X] Notification markdown rendering must escape or sanitize unsafe user-controlled content where applicable. *app/utils/notifications.py:78*
- [X] Notification routing must support rate limiting or throttling to avoid alert storms. *app/utils/notifications.py:78*
- [X] Notification routing must support deduplication of repeated alerts. *app/utils/notifications.py:78*
- [X] Notification routing must produce delivery status results. *app/utils/notifications.py:78*
- [X] Notification routing must publish notification success and failure events to the Event Bus. *tests/unit/app/utils/test_validations.py:95*
- [X] Notification routing must expose metrics for sent, failed, suppressed, throttled, and deduplicated notifications. *tests/unit/app/utils/test_validations.py:95*
- [X] Email notifications must support configurable SMTP or provider adapter settings without logging credentials. *app/utils/notifications.py:78*
- [X] Telegram notifications must support bot-token and chat-recipient configuration without logging credentials. *app/utils/notifications.py:78*
- [X] Desktop notifications must be disabled by default in production unless explicitly enabled. *app/utils/notifications.py:78*
- [X] Notification adapters must be lazy-loaded and must not initialize network clients at import time. *app/utils/notifications.py:78*
- [X] External notification adapters must implement circuit breakers. *tests/unit/app/utils/test_observability.py:36*
- [X] Notification delivery failures must not fail the original business operation unless the caller explicitly requires fail-closed alerting. *tests/unit/app/utils/test_validations.py:95*
- [X] External notification adapters must implement a circuit-breaker pattern. *tests/unit/app/utils/test_observability.py:36*
- [X] Notification routing must accept alert severity, channel preferences, sanitized message template data, and routing policy. *app/utils/notifications.py:78*
- [X] Runtime settings must accept logging, notification, Event Bus, auth, and observability configuration. *app/utils/notifications.py:78*
- [X] Notification routing must return sent, suppressed, throttled, deduplicated, failed, or disabled status. *tests/unit/app/utils/test_validations.py:95*
- [X] Desktop notification content must not include secrets. *app/utils/notifications.py:78*
- [X] Documentation must include runbook sections for Event Bus backpressure incidents, notification outage incidents, clock-drift incidents, and schema-validation performance regressions. *tests/unit/app/utils/test_validations.py:122*
- [X] Implement `app/utils/notifications.py` before alert delivery is attached to workflows. *app/utils/notifications.py:78*
- [X] Prometheus-compatible metrics include circuit-breaker state, queue depth, idempotency cache size, backpressure count, notification failures, and clock drift. *tests/unit/app/utils/test_validations.py:95*
- [X] Production code must not leak secrets in logs, errors, events, notifications, metrics, or health snapshots. *app/utils/notifications.py:78*
- [X] Importing any `app.utils` module must not initialize notification clients. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Wall-clock timestamp serialization must be UTC-first and safe for logs, events, notifications, metrics, health snapshots, and audit metadata. *app/utils/notifications.py:78*
- [X] Notification routing, deduplication, throttling, rate-limit counters, and circuit-breaker state must be thread-safe and/or async-safe. *tests/unit/app/utils/test_logger.py:136*
- [X] Notification delivery diagnostics must remain consistent under concurrent alert bursts. *tests/unit/app/utils/test_logger.py:136*
- [X] Optional notification provider dependencies must be lazy-loaded. *app/utils/notifications.py:78*
- [X] Notification delivery failures must be isolated from core utility functions unless explicitly configured otherwise. *tests/unit/app/utils/test_validations.py:95*
- [X] Notification routing must remain safe under repeated error bursts. *app/utils/notifications.py:78*
- [X] Notification messages must be concise and actionable. *app/utils/notifications.py:78*
- [X] External notification provider outages must be isolated through circuit breakers and deterministic error codes. *tests/unit/app/utils/test_observability.py:36*
- [X] Notification delivery must be observable through logs, metrics, or sanitized events. *app/utils/notifications.py:78*
- [X] Notification routing failures must map to `NOTIFICATION_FAILED`. *tests/unit/app/utils/test_validations.py:95*
- [X] Notification configuration failures must map to `CONFIGURATION_ERROR`. *app/utils/settings.py:28*
- [X] Notification failures must distinguish configuration failure, provider timeout, provider rejection, circuit-open state, throttling, and suppression. *tests/unit/app/utils/test_validations.py:21*
- [X] Unknown Event Bus or notification provider errors must map safely to deterministic error codes. *app/utils/notifications.py:78*
- [X] Sensitive values must be redacted before appearing in notification templates. *app/utils/notifications.py:78*
- [X] Authorization headers must never appear in logs, metrics, events, or notifications. *app/utils/notifications.py:78*
- [X] Notification recipient lists must be treated as sensitive configuration. *app/utils/notifications.py:78*
- [X] Email credentials must never appear in logs, metrics, events, or notifications. *app/utils/notifications.py:78*
- [X] Telegram bot tokens must never appear in logs, metrics, events, or notifications. *app/utils/notifications.py:78*
- [X] Side-effecting notification and event adapter actions must require explicit configuration. *app/utils/notifications.py:78*
- [X] External notification and pub/sub adapters must be lazy-loaded. *app/utils/notifications.py:78*
- [X] External notification and pub/sub adapters must fail closed when credentials are missing or malformed. *tests/unit/app/utils/test_validations.py:95*
- [X] Metric labels must reject raw IDs, arbitrary user strings, exception strings, notification recipients, provider tokens, and event payload values. *tests/unit/app/utils/test_validations.py:21*
- [X] Notification markdown rendering must escape or sanitize unsafe user-controlled content where applicable. *app/utils/notifications.py:78*
- [X] Auth and notification provider credentials must be excluded from Event Bus payloads by default. *app/utils/notifications.py:78*
- [X] Documentation must describe notification routing rules for email, Telegram, and desktop channels. *app/utils/notifications.py:78*
- [X] Documentation must define notification routing concurrency guarantees. *app/utils/notifications.py:78*
- [X] Documentation must define whether each notification adapter is synchronous, asynchronous, or dual-mode. *app/utils/notifications.py:78*
- [X] Documentation must describe notification throttling and deduplication behavior. *app/utils/notifications.py:78*
- [X] Documentation must describe notification markdown and plain-text template fallback behavior. *app/utils/notifications.py:78*
- [X] Documentation must describe circuit-breaker configuration for notification adapters. *tests/unit/app/utils/test_observability.py:36*
- [X] Importing `app.utils` does not import pandas, cryptography, dotenv, broker SDKs, notification clients, pub/sub clients, Prometheus exporters, or network clients unless the specific feature is used. *tests/unit/app/utils/test_utils_registry.py:28*
- [X] Notification routing, throttling, deduplication, and circuit-breaker state are thread-safe and/or async-safe. *tests/unit/app/utils/test_logger.py:136*
- [X] External notification adapters have circuit breakers. *tests/unit/app/utils/test_observability.py:36*
- [X] Notification templates support markdown and plain-text fallback rendering. *app/utils/notifications.py:78*
- [X] Notification templates render from sanitized data transfer objects rather than raw event payloads. *app/utils/notifications.py:78*
- [X] Notification routing must support test mode with fake adapters. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Event publishing with sensitive payload must redact before logging or notification routing. *app/utils/notifications.py:78*
- [X] Notification channel disabled must return disabled or suppressed status without error. *app/utils/notifications.py:78*
- [X] Notification credentials missing must fail safely without leaking configuration details. *tests/unit/app/utils/test_validations.py:95*
- [X] Notification provider timeout must return failed status and emit metrics. *tests/unit/app/utils/test_validations.py:95*
- [X] Notification markdown rendering failure must fall back to plain text. *tests/unit/app/utils/test_validations.py:95*
- [X] Unsupported notification formatting must not fail the original operation unless fail-closed alerting is explicitly configured. *tests/unit/app/utils/test_validations.py:95*
- [X] Notification adapter outage must open the circuit after the configured threshold. *tests/unit/app/utils/test_observability.py:36*
- [X] Logger tests must verify log emission does not leak passwords, tokens, API keys, broker credentials, encryption keys, private payloads, full approval packets, notification provider credentials, authorization headers, or Telegram bot tokens. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must cover email routing with fake adapter. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must cover Telegram routing with fake adapter. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must cover desktop routing with fake adapter. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must cover disabled channel behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must cover missing credentials. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must cover provider failure and timeout behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must verify throttling and deduplication. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must verify concurrent routing behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must verify concurrent suppression, throttling, deduplication, and adapter-failure behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must verify thread-safe or async-safe throttling and deduplication state. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must verify markdown rendering. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must verify plain-text fallback rendering. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must verify provider circuit-breaker closed, open, and half-open states with fake adapters. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Notification tests must verify notification content does not leak secrets after template rendering. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must cover notification metrics. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Grafana documentation tests or review checks must confirm dashboards cover system health, tool health, Event Bus, notifications, errors, and auth failures. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] A chaos-test profile must cover notification provider failures and pub/sub adapter outages. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Tests prove no sensitive values leak through logs, events, notifications, metrics, dead-letter diagnostics, schema errors, or health checks. *tests/unit/app/utils/test_utils_registry.py:6*

#### `app/utils/observability.py`

Functions/classes:

- `CLOCK_DRIFT_DETECTED`

Requirements:

- [X] The module must provide observability primitives for logs, metrics, health snapshots, and trace correlation. *app/utils/observability.py:61*
- [X] The module must provide Prometheus-compatible system-health metrics. *tests/unit/app/utils/test_observability.py:14*
- [X] The module must define Grafana dashboard expectations for operational health. *app/utils/observability.py:61*
- [X] Observability utilities may report system health, but must not decide operational actions without governance approval. *app/utils/observability.py:61*
- [X] Prometheus/Grafana metrics must include system-health visibility and must not be limited to business alerts. *tests/unit/app/utils/test_observability.py:14*
- [X] System operator:** A maintainer who monitors logs, alerts, metrics, dashboards, and health status. *app/utils/observability.py:61*
- [X] Observability consumer:** A developer, operator, or automated monitor that uses Prometheus/Grafana metrics. *tests/unit/app/utils/test_observability.py:14*
- [X] Prometheus metrics export may be provided by application runtime, while utils provides metric registration and recording helpers. *tests/unit/app/utils/test_observability.py:14*
- [X] Grafana dashboards may be maintained as documentation or version-controlled dashboard definitions. *app/utils/observability.py:61*
- [X] Metrics and logs are operational telemetry and must not contain raw market payloads, secrets, or approval-packet contents. *app/utils/observability.py:61*
- [X] The system must provide observability helpers for logs, metrics, health checks, and trace correlation. *app/utils/observability.py:61*
- [X] The system must expose Prometheus-compatible metrics for system health. *tests/unit/app/utils/test_observability.py:14*
- [X] The system must support Grafana dashboards for operational visibility. *app/utils/observability.py:61*
- [X] Metrics must cover official AI tool call counts. *app/utils/observability.py:61*
- [X] Metrics must cover official AI tool success and error counts. *app/utils/observability.py:61*
- [X] Metrics must cover tool execution latency. *tests/unit/app/utils/test_validations.py:122*
- [X] Metrics must cover validation failure counts by error code and source. *tests/unit/app/utils/test_validations.py:95*
- [X] Metrics must cover Event Bus events published, delivered, failed, retried, dead-lettered, dropped, and backpressured. *tests/unit/app/utils/test_validations.py:95*
- [X] Metrics must cover Event Bus queue depth or backlog where applicable. *app/utils/observability.py:61*
- [X] Metrics must cover Event Bus idempotency cache size, eviction count, duplicate count, and conflict count. *tests/unit/app/utils/test_event_bus.py:13*
- [X] Metrics must cover notification sent, failed, suppressed, throttled, and deduplicated counts. *tests/unit/app/utils/test_validations.py:95*
- [X] Metrics must cover notification delivery latency. *tests/unit/app/utils/test_validations.py:122*
- [X] Metrics must cover logging error counts where detectable. *app/utils/observability.py:61*
- [X] Metrics must cover settings load failures. *tests/unit/app/utils/test_validations.py:95*
- [X] Metrics must cover security redaction failures. *tests/unit/app/core/test_security.py:37*
- [X] Metrics must cover encryption and decryption failures without exposing plaintext or key material. *tests/unit/app/utils/test_validations.py:95*
- [X] Metrics must cover auth validation and authorization failures. *tests/unit/app/utils/test_validations.py:95*
- [X] Metrics must cover circuit-breaker state transitions and current state. *tests/unit/app/utils/test_observability.py:36*
- [X] Metrics must cover clock-drift status where available. *app/utils/observability.py:61*
- [X] Metrics must include system-health metrics, not only business alerts. *app/utils/observability.py:61*
- [X] Prometheus-compatible alerts must cover circuit-open state, queue saturation, dead-letter growth, notification failure rate, and clock drift where alerting is implemented. *tests/unit/app/utils/test_validations.py:95*
- [X] Grafana dashboards must include panels for idempotency cache size, backpressure count, retry count, circuit-breaker state, and clock drift where dashboards are implemented. *tests/unit/app/utils/test_observability.py:36*
- [X] Metrics labels must be bounded and must not include high-cardinality raw IDs unless explicitly approved. *tests/unit/app/utils/test_standard.py:341*
- [X] Metrics labels must not include secrets, raw payloads, tokens, API keys, personal data, notification recipients, or approval packet contents. *app/utils/observability.py:61*
- [X] Observability helpers must support no-op operation when Prometheus dependencies are not installed. *tests/unit/app/utils/test_observability.py:14*
- [X] Missing Prometheus dependencies must fail only when Prometheus-specific export features are used. *tests/unit/app/utils/test_validations.py:95*
- [X] Grafana dashboard documentation must include panels for system health, tool health, Event Bus health, notification health, error routing, auth failures, and data-quality validation health. *tests/unit/app/utils/test_validations.py:95*
- [X] Health snapshots must include component status, last error timestamp, last successful event timestamp, degraded status, and critical status where applicable. *app/utils/observability.py:61*
- [X] Health checks should include wall-clock drift monitoring. *tests/unit/app/utils/test_observability.py:36*
- [X] Clock drift monitoring should detect significant NTP or system-clock offset beyond a configured threshold. *app/utils/observability.py:61*
- [X] Clock drift thresholds must be configurable by environment. *app/utils/observability.py:61*
- [X] Clock drift warnings must be emitted as observability events. *app/utils/observability.py:61*
- [X] Critical clock drift must produce degraded or critical health status depending on threshold. *tests/unit/app/utils/test_observability.py:36*
- [X] Clock drift diagnostics must include measured offset, threshold, timestamp, source, and component status where available. *app/utils/observability.py:61*
- [X] Clock drift monitoring may be no-op when the runtime environment cannot provide an offset source. *app/utils/observability.py:61*
- [X] Clock drift no-op behavior must be explicit and observable as unsupported or not configured. *app/utils/observability.py:61*
- [X] Circuit breakers must open after a configurable threshold of consecutive failures, timeouts, or provider errors. *tests/unit/app/utils/test_validations.py:95*
- [X] Open circuits must fail fast without repeatedly consuming threads, sockets, or connection-pool capacity. *tests/unit/app/utils/test_logger.py:136*
- [X] Circuit breakers must support half-open recovery attempts after a configurable cooldown interval. *tests/unit/app/utils/test_observability.py:36*
- [X] Circuit breakers must close after successful recovery attempts. *tests/unit/app/utils/test_observability.py:36*
- [X] Circuit-breaker state transitions must be logged with sanitized metadata. *tests/unit/app/utils/test_observability.py:36*
- [X] Circuit-breaker state transitions must be exposed through Prometheus-compatible metrics. *tests/unit/app/utils/test_observability.py:36*
- [X] Circuit-breaker state must be included in component health snapshots. *tests/unit/app/utils/test_observability.py:36*
- [X] Circuit-breaker failures must not expose credentials, tokens, message bodies, or sensitive payloads. *tests/unit/app/utils/test_validations.py:95*
- [X] Observability helpers must accept metric names, bounded labels, numeric values, durations, and component health states. *app/utils/observability.py:61*
- [X] Observability helpers must return metric registration or recording status where applicable. *app/utils/observability.py:61*
- [X] Health checks must return healthy, degraded, critical, unsupported, or not-configured status with sanitized details. *app/utils/observability.py:61*
- [X] Clock-drift health failures must return `CLOCK_DRIFT_DETECTED` where the error boundary requires a deterministic code. *tests/unit/app/utils/test_validations.py:95*
- [X] Metrics labels must not include secrets, tokens, raw payloads, full exception strings, or user-provided arbitrary values. *app/utils/observability.py:61*
- [X] Documentation must include a dashboard review checklist to ensure Grafana panels cover system health, not only trading or business outcomes. *app/utils/observability.py:61*
- [X] Implement `app/utils/observability.py` before production health gates are accepted. *app/utils/observability.py:61*
- [X] Health checks include clock-drift monitoring or explicit no-op status. *app/utils/observability.py:61*
- [X] Optional Prometheus dependencies must be lazy-loaded. *tests/unit/app/utils/test_observability.py:14*
- [X] Metrics collection must add low overhead. *app/utils/observability.py:61*
- [X] Health checks must be deterministic and fast. *app/utils/observability.py:61*
- [X] Metrics recording failures must not fail the original operation unless explicitly configured to fail closed. *tests/unit/app/utils/test_validations.py:95*
- [X] Component health checks must distinguish healthy, degraded, critical, unsupported, and not-configured states. *app/utils/observability.py:61*
- [X] Metrics labels must be bounded-cardinality. *app/utils/observability.py:61*
- [X] Metrics must be safe to expose to Prometheus without leaking secrets. *tests/unit/app/utils/test_observability.py:14*
- [X] Observability helpers must be import-safe without Prometheus dependencies. *tests/unit/app/utils/test_observability.py:14*
- [X] Logging output must be machine-parseable in production and human-readable enough for local development. *app/utils/observability.py:61*
- [X] Grafana dashboard definitions must be version-controlled if implemented as files. *app/utils/observability.py:61*
- [X] Health checks must distinguish healthy, degraded, and critical states. *app/utils/observability.py:61*
- [X] System-health observability must not be limited to trading or business alerts. *app/utils/observability.py:61*
- [X] Observability export failures must map to `OBSERVABILITY_ERROR` or `CONFIGURATION_ERROR`. *app/utils/settings.py:28*
- [X] Metrics recording failures must not fail the original operation unless explicitly configured to fail closed. *tests/unit/app/utils/test_validations.py:95*
- [X] Circuit-open failures must be observable through logs and metrics. *tests/unit/app/utils/test_validations.py:95*
- [X] Sensitive values must be redacted before appearing in Prometheus metrics or Grafana variables. *tests/unit/app/utils/test_observability.py:14*
- [X] Prometheus metrics must avoid high-cardinality sensitive identifiers. *tests/unit/app/utils/test_observability.py:14*
- [X] Grafana dashboard variables must not expose secrets. *app/utils/observability.py:61*
- [X] Clock-drift diagnostics must not expose infrastructure secrets. *app/utils/observability.py:61*
- [X] Documentation must describe circuit-breaker metrics and health states. *tests/unit/app/utils/test_observability.py:36*
- [X] Documentation must describe clock-drift monitoring and environment-specific thresholds. *app/utils/observability.py:61*
- [X] Documentation must describe Prometheus metrics names, labels, and cardinality limits. *tests/unit/app/utils/test_observability.py:14*
- [X] Documentation must describe Grafana dashboard expectations. *app/utils/observability.py:61*
- [X] Documentation includes production readiness checklists, operational runbooks, dashboard review checklists, and compatibility review notes. *app/utils/observability.py:61*
- [X] Observability must support local/test no-op behavior. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Prometheus dependency missing must not break module import. *tests/unit/app/utils/test_observability.py:14*
- [X] Prometheus exporter unavailable must degrade to no-op metrics or explicit configuration error depending on caller mode. *tests/unit/app/utils/test_observability.py:14*
- [X] Health check failures must not expose secrets. *tests/unit/app/utils/test_validations.py:95*
- [X] Clock drift unavailable must be reported as unsupported, not healthy. *app/utils/observability.py:61*
- [X] Clock drift above warning threshold must produce degraded health. *app/utils/observability.py:61*
- [X] Clock drift above critical threshold must produce critical health. *app/utils/observability.py:61*
- [X] Sensitive metric labels must be rejected before metrics emission. *tests/unit/app/utils/test_validations.py:21*
- [X] Observability tests must cover metrics registration. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must cover tool-call counters and latency histograms. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must cover auth failure metrics. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must cover no-op behavior when Prometheus dependencies are unavailable. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must use fake Prometheus exporters where exporter behavior must be exercised without external services. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must reject high-cardinality or sensitive metric labels. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must verify clock-drift healthy, degraded, critical, unsupported, and not-configured states. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Observability tests must verify circuit-breaker metrics. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Health-check tests must cover healthy, degraded, critical, unsupported, and not-configured states. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Documentation must describe how to run observability in no-op/local/test mode. *tests/unit/app/utils/test_utils_registry.py:6*


### Hardening Amendments

#### Sprint-pack execution boundary

Requirements:

- [X] Split Phase 1 implementation into approved sprint packs before editing code: 01A package/errors/standard, 01B logging/time/identity/paths, 01C settings/security/auth, 01D event bus/error routing/notifications, 01E observability/metrics, and 01F dataframe/data-quality/validators. *docs/phase-implementation-plan/01-utils-foundation.md:1486*
- [X] Each Phase 1 sprint pack must have its own dry run, approval, tests, rollback plan, and implementation report. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Replace any remaining Black, isort, or Flake8 acceptance wording with Ruff format, Ruff check, mypy strict, pytest, coverage, and pre-commit wording. *tests/unit/app/utils/test_utils_registry.py:6*
- [X] Ensure Utils imports do not depend on contracts that would create circular imports with Phase 1.5. *docs/phase-implementation-plan/01-utils-foundation.md:1486*
- [X] Document which Utils functions are allowed to be used by Core Contracts without importing heavy optional dependencies. *tests/unit/app/utils/test_utils_registry.py:28*

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

- [X] `example_01_logging_and_tracing`: Demonstrate `configure_logging`, logger usage, and trace context propagation. *tests/usage/app/services/01_utils.py:74*
- [X] `example_02_standard_responses`: Demonstrate standardized success, error, validation, and exception response envelopes. *tests/usage/app/services/01_utils.py:96*
- [X] `example_03_identities`: Demonstrate request, workflow, correlation, event, idempotency, and custom prefixed IDs. *tests/usage/app/services/01_utils.py:129*
- [X] `example_04_datetimes_and_normalization`: Demonstrate UTC parsing, formatting, staleness checks, timestamp sequence validation, and execution timing. *tests/usage/app/services/01_utils.py:151*
- [X] `example_05_security_and_redaction`: Demonstrate payload redaction, password hashing, verification, encryption, and decryption without leaking secrets. *tests/usage/app/services/01_utils.py:180*
- [X] `example_06_dataframe_and_combinations`: Demonstrate dataframe alignment, record serialization, chunking, and parameter-combination helpers. *tests/usage/app/services/01_utils.py:207*
- [X] `example_07_data_quality`: Demonstrate OHLCV diagnostics and standard-envelope quality validation for valid and invalid records. *tests/usage/app/services/01_utils.py:230*
- [X] `example_08_validations`: Demonstrate input/output schema validation, evidence validation, registry validation, and failure envelopes. *tests/usage/app/services/01_utils.py:260*
- [X] `example_09_event_bus`: Demonstrate event envelope creation, publish/subscribe behavior, idempotency handling, and queue failure behavior. *tests/usage/app/services/01_utils.py:285*
- [X] `example_10_circuit_breakers_and_observability`: Demonstrate circuit-breaker states, health snapshots, metric recording, and Prometheus text export. *tests/usage/app/services/01_utils.py:307*
- [X] `example_11_notifications`: Demonstrate fake/local notification routing, throttling, disabled channels, and redacted alert payloads. *tests/usage/app/services/01_utils.py:329*
- [X] `example_12_paths`: Demonstrate safe path normalization, parent directory creation, traversal rejection, and approved-root checks. *tests/usage/app/services/01_utils.py:349*
- [X] The single usage file must be runnable as a script and organize separate examples as focused functions. *tests/usage/app/services/01_utils.py:366*
- [X] Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable. *tests/usage/app/services/01_utils.py:74*

### Documentation and Logging Requirements

- [X] Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects. *app/utils/settings.py:1*
- [X] Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors. *app/utils/settings.py:204*
- [X] Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only. *tests/unit/app/utils/test_logger.py:53*
- [X] Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes. *app/utils/README.md:34*

### Acceptance Checklist

- Done criterion: All 1186 checkbox tasks are implemented or explicitly deferred with a documented reason.
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
