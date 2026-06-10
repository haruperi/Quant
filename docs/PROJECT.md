# HaruQuantAI Project

Purpose: this file is the product truth for HaruQuantAI. It records the project purpose, product scope, domain language, workflows, business rules, assumptions, open questions, and source/reference notes.

## Project Purpose

HaruQuantAI is a clean-room rebuild and upgrade of HaruQuant. The project is intended to become a modular AI-assisted quantitative trading platform with documented requirements, safe service-tool boundaries, governed trading actions, reproducible research, simulation/backtesting, live-readiness controls, and AI-assisted workflows.

Project memory lives in repository files, not chat. Important facts, assumptions, decisions, risks, questions, and scope changes must be recorded in the active docs or `AGENTS.md` as appropriate.

## Product Vision

HaruQuantAI should provide one coherent system for research, data ingestion, indicators, strategy signals, risk gates, trading order intents, simulation, optimization, live readiness, analytics, secure API/UI access, and conversation AI.

The product should keep research, simulation, paper trading, and live trading aligned without allowing user-facing or AI-facing surfaces to bypass authorization, risk, reconciliation, idempotency, audit, or kill-switch controls.

## Target Users And Actors

| Actor | Description |
|---|---|
| Owner/Admin | Controls project direction, configuration, and high-level policy approval. |
| Operator | Runs the system, monitors health, and handles incidents under authorization. |
| Researcher | Explores data, indicators, analytics, simulations, and artifacts without live side effects. |
| Strategy Developer | Builds and tests strategy definitions and versions. |
| Risk Manager | Reviews risk decisions, thresholds, drawdown, exposure, reconciliation, and kill switch. |
| Compliance Approver | Reviews regulated or governed artifacts and live recovery actions. |
| Read-only Viewer | Views approved dashboards and reports. |
| Service Account | Internal non-human actor with scoped service permissions. |
| AI Agent | Uses approved tool plans only; cannot bypass auth, governance, or risk. |
| Broker Adapter | External broker/data boundary; never owns internal risk authority. |

## Core Workflows

### Research To Strategy

1. Load normalized historical data.
2. Explore a hypothesis with indicators and analytics.
3. Create a versioned strategy specification.
4. Run simulation on approved data.
5. Review performance, risk, caveats, and artifacts.
6. Promote only through the approved governance path.

### Signal To Paper Trade

1. Data emits normalized market/account state.
2. Indicator calculates required features.
3. Strategy emits a canonical signal.
4. Risk evaluates the proposal and portfolio state.
5. Trading creates a deterministic order intent after approval or reduction.
6. Paper execution records a receipt.
7. Analytics and audit consume results.

### Signal To Live Trade

1. Authenticated actor or service initiates or approves the flow.
2. Strategy emits a signal and proposal.
3. Risk validates strategy, account, portfolio, broker state, thresholds, and kill switch.
4. Trading creates an order intent with deterministic idempotency material.
5. Live checks broker readiness and reconciliation.
6. Live submits to broker only if live mutations are explicitly enabled.
7. Execution receipt, reconciliation, audit, metrics, and alerts update.

### Conversation Action Draft

1. User asks chat to prepare an action or explanation.
2. Conversation creates a redacted action draft or read-only response.
3. Governance determines the required approval route.
4. Backend execution occurs only if separately approved and still valid.

## Business Rules

- Build modules in this approved order: Utils, Data, Indicator, Strategy, Risk, Analytics, Trading, Simulation, Optimization, Live, UI/API Gateway, Research, Conversation.
- Old HaruQuant code, docs, tests, examples, and catalogs are reference material only unless explicitly adopted by a decision in `docs/ROADMAP.md`.
- Strategies emit signals, not broker orders.
- Risk intercepts signals before trading or live execution.
- Trading creates deterministic order intents from approved/reduced risk decisions or simulation context.
- Simulation and live share order-intent semantics but never share live side effects.
- Conversation can draft, explain, summarize, and plan, but cannot directly execute governed or broker-affecting actions.
- Live trading fails closed by default.
- Live broker mutations are disabled unless explicitly approved, configured, risk-gated, reconciled, idempotent, and audited.
- Missing or stale broker/risk/security context blocks live execution.
- Secrets must never be committed, logged, returned, persisted in chat, or sent in notifications.
- Utils is a shared foundation for validation, normalization, redaction, serialization, event routing, diagnostics, telemetry, settings, and notification routing.
- Utils must not own strategy logic, broker execution, portfolio allocation, risk-governor decisions, application orchestration, database repositories, UI behavior, or live trading decisions.
- Agent-facing Utils tools are low-risk and read-only unless a later approved decision explicitly changes their classification.
- Encryption, decryption, external identity-provider validation, production notification delivery, and production pub/sub adapters require explicit approval before agent or production workflow attachment.

## Glossary

| Term | Meaning |
|---|---|
| Symbol | Internal normalized instrument identifier such as `EURUSD`. |
| Timeframe | Candle/bar interval such as `M5`, `H1`, or `D1`. |
| OHLCV bar | Open, high, low, close, volume market data record. |
| Tick | Bid/ask/last market data point. |
| Indicator | Derived value computed from normalized market data. |
| Strategy | Versioned trading logic that emits signals. |
| Signal | Strategy output expressing market intent, not an order. |
| Proposal | Candidate trade action prepared for risk review. |
| Risk decision | Approval, reduction, rejection, or block based on policy and state. |
| Order intent | Internal deterministic order request after risk gating. |
| Execution receipt | Broker, paper, or simulation result for an order intent. |
| Portfolio state | Internal account, equity, margin, position, and exposure view. |
| Reconciliation | Comparison between internal state and broker truth. |
| Kill switch | Safety control that blocks trading actions. |
| Action draft | Conversation-created proposal that still needs governance. |
| Audit event | Durable record of important system activity. |

## Inputs And Outputs

| Module | Inputs | Outputs |
|---|---|---|
| Data | Provider feeds, broker reads, local files, SQLite state. | Normalized bars/ticks, broker snapshots, state records. |
| Indicator | Normalized data, indicator definitions, parameters. | Indicator result columns and values. |
| Strategy | Data, indicators, parameters, lifecycle state. | Signals and strategy metadata. |
| Risk | Proposals, portfolio/broker state, thresholds, policies. | Risk decisions, constraints, kill-switch state. |
| Trading | Risk decisions and proposal material. | Order intents and idempotency records. |
| Simulation | Historical data, strategy, order intents, config. | Simulated trades, equity curve, metrics, artifacts. |
| Optimization | Parameter spaces, simulation config, objective. | Candidate rankings, best result, robustness output. |
| Live | Order intents, broker readiness, reconciliation. | Execution attempts, receipts, live audit events. |
| API/UI | User requests and auth context. | Response envelopes, dashboards, controls. |
| Research | Data, metrics, hypotheses. | Research artifacts and evidence references. |
| Conversation | User messages, context, tool plans. | Messages, summaries, action drafts. |

## Utils

### Purpose

Provide the shared production-grade utility foundation for HaruQuantAI. Utils provides stable, typed, documented, deterministic, logged, testable, and secure primitives used by higher-level domains including data, research, simulation, risk, portfolio, execution, analytics, governance, UI/API, and agentic workflows.

Utils may validate, normalize, redact, serialize, route events, report diagnostics, emit telemetry, and provide safe adapter boundaries. It remains a foundation layer, not a business-decision layer.

### Owns

Settings, configuration loading, standard response helpers, request/workflow/correlation/causation/event/idempotency IDs, UTC time helpers, safe path helpers, canonical JSON serialization, dataframe helpers, diagnostic-only OHLCV quality checks, schema validation, security/redaction helpers, auth context helpers, event bus/pub/sub primitives, error routing, notification routing, circuit breakers, observability helpers, health snapshots, common errors, and shared constants.

### Does Not Own

Strategy logic, broker execution, portfolio allocation, risk-governor decisions, application orchestration, database repositories, UI behavior, data repair/resampling/enrichment/persistence, or live trading decisions.

### Requirement Source / Classification

#### Confirmed Requirements

Confirmed requirements are derived from the uploaded v8 utility specification and the user-approved production-readiness additions in this conversation.

#### User-Directed Production Requirements

The following areas are included as required baseline capabilities because they were explicitly requested for production readiness:

- Logging expansion.
- Time and clock policy expansion.
- Auth and authorization helpers.
- Pub/sub and Event Bus primitives.
- Error routing and alert routing.
- Notifications through email, Telegram, and desktop adapters.
- Observability with Prometheus/Grafana system-health metrics.
- Circuit breakers, clock-drift monitoring, bounded idempotency, and backpressure behavior.

#### Promoted Production Hardening Requirements

Former optional hardening items have been promoted into the baseline requirements, implementation plan, testing requirements, documentation requirements, CI gates, and Definition of Done.

### Functional Requirements

#### Foundation And Scope

- [ ] The system must implement `tools/utils/` as the shared utility foundation for HaruQuantAI.
- [ ] The module must support higher-level domains including data, research, simulation, risk, portfolio, execution, analytics, governance, and agentic workflows.
- [ ] The module must provide project-wide structured logging.
- [ ] The module must provide standard HaruQuant tool response envelopes.
- [ ] The module must provide deterministic error codes and exception mapping.
- [ ] The module must provide request, workflow, generic ID, version, correlation ID, causation ID, and idempotency helpers.
- [ ] The module must provide shared status, severity, risk-level, environment-mode, auth, event, notification, and health-state constants.
- [ ] The module must provide timestamp and timezone normalization using a UTC-first policy.
- [ ] The module must provide safe path handling.
- [ ] The module must provide canonical JSON serialization for audit, hashing, caching, reproducible tests, and comparison workflows.
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
- [ ] The module must support extensible domain error mapping through `HaruQuantError` and compatible `code` attributes.
- [ ] The module must provide auth context validation and authorization support helpers.
- [ ] The module must provide Event Bus and pub/sub primitives.
- [ ] The module must provide early alert routing and error routing so the rest of the system can report issues consistently.
- [ ] The module must provide notification routing primitives for email, Telegram, and desktop channels.
- [ ] The module must provide observability primitives for logs, metrics, health snapshots, and trace correlation.
- [ ] The module must provide Prometheus-compatible system-health metrics.
- [ ] The module must define Grafana dashboard expectations for operational health.

#### Public Registry And API Control

- [ ] `tools/utils/__init__.py` must act as the public registry for the utility domain.
- [ ] Only intentionally imported names listed in `__all__` may be public.
- [ ] Public names must be classified as either official AI tools or support objects/helpers.
- [ ] Official AI tools must return the standard HaruQuant tool envelope.
- [ ] Support helpers may return native Python values when they are not agent-callable tools.
- [ ] The logger must be exported as a support object and must not be treated as an official AI tool.
- [ ] Auth, Event Bus, notification, and observability primitives must be support helpers by default unless explicitly promoted to official AI tools.
- [ ] Internal helpers must remain private unless explicitly intended for public import.
- [ ] No accidental public exports may exist.
- [ ] No compatibility shims, aliases, fallback import modules, or duplicate wrapper modules may exist.
- [ ] New public exports must be justified by real cross-domain reuse.
- [ ] Public exports may not be renamed or removed after v8 acceptance without a new versioned specification and registry review.

#### Official AI Tools

- [ ] `validate_ohlcv_quality` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_input_schema` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_output_schema` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_handoff_payload` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_evidence_pack` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_approval_packet` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_registry_entry` must be implemented as a low-risk, read-only official AI tool.
- [ ] `validate_data_freshness` must be implemented as a low-risk, read-only official AI tool.
- [ ] `redact_text` must be classified as a low-risk, read-only official AI tool only for approved audit/log-redaction workflows.
- [ ] `redact_mapping` must be classified as a low-risk, read-only official AI tool only for approved audit/log-redaction workflows.
- [ ] `load_runtime_settings` must remain a support helper and must not be attached to agents by default.
- [ ] `encrypt_data` must remain a restricted support helper and must not be attached to agents by default.
- [ ] `decrypt_data` must remain a restricted support helper and must not be attached to agents by default.
- [ ] Agent access to encryption or decryption must require explicit security approval, permission checks, and audit logging.
- [ ] Official AI tools must include `request_id: str | None = None`.
- [ ] Official AI tools must include tool metadata.
- [ ] Official AI tools must include risk and side-effect flags.
- [ ] Official AI tools must validate inputs.
- [ ] Official AI tools must measure execution timing.
- [ ] Official AI tools must use structured logging.
- [ ] Official AI tools must return the standard response schema.
- [ ] Official AI tools must use deterministic error codes.
- [ ] Official AI tools must not fail silently.
- [ ] Agents may call only approved official AI tools through approved tool attachment.

#### Standard Tool Response

- [ ] Every official AI tool must return the top-level keys `status`, `message`, `data`, `error`, and `metadata`.
- [ ] `status` must be either `success` or `error`.
- [ ] `message` must be a string.
- [ ] `error` must be either `None` or a mapping with `code` and `details`.
- [ ] `metadata` must include `tool_name`, `tool_version`, `tool_category`, `tool_risk_level`, `request_id`, `execution_ms`, `read_only`, `writes_file`, `modifies_database`, `places_trade`, and `requires_network`.
- [ ] Standard response validation must reject missing top-level keys.
- [ ] Standard response validation must reject missing metadata keys.
- [ ] Standard response validation must reject invalid statuses.
- [ ] Standard response validation must reject malformed errors.
- [ ] Standard response validation should validate error codes against the approved error-code set where practical.
- [ ] `get_execution_ms(start_time)` must calculate execution duration consistently for official tools.
- [ ] `get_execution_ms(start_time)` must use a monotonic clock source such as `time.perf_counter()`.
- [ ] `get_execution_ms(start_time)` must return milliseconds rounded to three decimals.

#### Logging

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

#### Time And Clock Handling

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

#### Authentication And Authorization

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

#### Error Utilities

- [ ] The module must define `HaruQuantError`.
- [ ] The module must define `HaruQuantValidationError`.
- [ ] The module must define `HaruQuantConfigurationError`.
- [ ] The module must define `HaruQuantSecurityError`.
- [ ] The module must define `HaruQuantDataError`.
- [ ] The module must define `HaruQuantExternalServiceError`.
- [ ] Every shared exception must carry a deterministic `code` attribute.
- [ ] Error messages must be human-readable.
- [ ] `error_name(code)` must return deterministic names.
- [ ] `message_for(code, default)` must return useful fallback messages.
- [ ] Unknown codes must resolve safely to `UNKNOWN_ERROR` or a provided default.
- [ ] Future domain-specific errors must inherit from `HaruQuantError` or expose a compatible `code: str` attribute.
- [ ] Standard response builders must map `HaruQuantError` subclasses generically without requiring every future domain error to be hardcoded.
- [ ] Unknown non-HaruQuant exceptions must map safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED` at controlled tool boundaries.

#### Identity And Traceability

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

#### Path Utilities

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

#### Dataframe Utilities

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
- [ ] Importing `tools.utils` must not eagerly import pandas.
- [ ] Missing pandas must fail only when a dataframe helper is called.

#### OHLCV Data Quality

- [ ] The module must provide `prepare_ohlcv_data`.
- [ ] The module must provide `validate_ohlcv_quality`.
- [ ] `validate_ohlcv_quality` must be stateless and diagnostic-only.
- [ ] `validate_ohlcv_quality` must not repair, enrich, persist, resample, clean, or mutate input data.
- [ ] `validate_ohlcv_quality` may inspect, profile, score, report issues, and provide descriptive remediation recommendations.
- [ ] Data repair, resampling, enrichment, persistence, and cleaning workflows must be reserved for `tools.data`.
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

#### Schema Validation

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

#### Security Utilities

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
- [ ] Redaction allowlist entries must be audited through configuration, tests, or documented approval.
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
- [ ] Environment-based encryption keys must use `HARUQUANT_ENCRYPTION_KEY`.
- [ ] `HARUQUANT_ENCRYPTION_KEY` must be a 32-byte URL-safe base64-encoded Fernet key when environment-based key loading is used.
- [ ] Encryption and decryption failures must not expose plaintext or key material.
- [ ] Secret version selection must choose the active item with the highest numeric version.
- [ ] If no active secret version exists, the function must raise `HaruQuantSecurityError` or return a structured `SECRET_VERSION_NOT_FOUND` error at the tool boundary.
- [ ] Duplicate active secret versions with the same numeric version must fail closed with `SECRET_VERSION_CONFLICT`.

#### Runtime Settings

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
- [ ] Importing `tools.utils` must not read `.env`.
- [ ] Optional dependency absence must not break import.
- [ ] Optional dependency absence must fail only when the requested feature requires the dependency.
- [ ] Invalid settings must fail clearly with configuration errors.
- [ ] `strict_validation=True` must escalate non-critical validation warnings to failures where the caller asks settings to enforce strict behavior.
- [ ] `strict_validation=False` must allow warnings to be returned or logged without failing settings load.
- [ ] `inject_runtime_settings` must mutate only the provided target mapping and return that mapping.
- [ ] Default runtime paths must resolve under `HARUQUANT_HOME` when configured.
- [ ] When `HARUQUANT_HOME` is not configured, local/test defaults must resolve under a deterministic `.haruquant` directory beneath the current working directory.
- [ ] Production deployments must configure `HARUQUANT_HOME` explicitly.
- [ ] Default directories must be `data`, `cache`, and `audit` under the resolved HaruQuant home directory.

#### Event Bus And Pub/Sub

- [ ] The system must provide a shared Event Bus abstraction for internal utility, workflow, alert, and error-routing events.
- [ ] The system must provide an in-process pub/sub mechanism suitable for local development, unit tests, and deterministic workflow tests.
- [ ] The Event Bus must support disabled or no-op adapter behavior for tests and local development where event delivery is intentionally suppressed.
- [ ] The system must define a standard event envelope.
- [ ] The standard event envelope must include `event_id`, `event_type`, `event_version`, `source`, `severity`, `timestamp`, `request_id`, `workflow_id`, `correlation_id`, `causation_id`, `idempotency_key`, `payload`, and `metadata`.
- [ ] Event payloads must be JSON-serializable or fail validation clearly.
- [ ] Event payloads must be redacted before logging, metrics labeling, notification routing, audit serialization, or dead-letter forwarding.
- [ ] The Event Bus must support publish and subscribe operations.
- [ ] The Event Bus must support topic or event-type subscriptions.
- [ ] The Event Bus must support handler registration and unregistration.
- [ ] The in-process Event Bus must guarantee deterministic, ordered handler execution per event type to ensure reproducible test outcomes.
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
- [ ] Idempotency tracking must be testable with injected clocks or deterministic time controls.
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

#### Error Routing And Alerts

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

#### Notifications

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
- [ ] Notification routing must support test mode with fake adapters.
- [ ] Notification routing must produce delivery status results.
- [ ] Notification routing must publish notification success and failure events to the Event Bus.
- [ ] Notification routing must expose metrics for sent, failed, suppressed, throttled, and deduplicated notifications.
- [ ] Email notifications must support configurable SMTP or provider adapter settings without logging credentials.
- [ ] Telegram notifications must support bot-token and chat-recipient configuration without logging credentials.
- [ ] Desktop notifications must be disabled by default in production unless explicitly enabled.
- [ ] Notification adapters must be lazy-loaded and must not initialize network clients at import time.
- [ ] External notification adapters must implement circuit breakers.
- [ ] Notification delivery failures must not fail the original business operation unless the caller explicitly requires fail-closed alerting.

#### Observability, Metrics, And Health

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

#### Circuit Breakers

- [ ] External notification adapters must implement a circuit-breaker pattern.
- [ ] External pub/sub adapters must implement a circuit-breaker pattern.
- [ ] Circuit breakers must open after a configurable threshold of consecutive failures, timeouts, or provider errors.
- [ ] Open circuits must fail fast without repeatedly consuming threads, sockets, or connection-pool capacity.
- [ ] Circuit breakers must support half-open recovery attempts after a configurable cooldown interval.
- [ ] Circuit breakers must close after successful recovery attempts.
- [ ] Circuit-breaker state transitions must be logged with sanitized metadata.
- [ ] Circuit-breaker state transitions must be exposed through Prometheus-compatible metrics.
- [ ] Circuit-breaker state must be included in component health snapshots.
- [ ] Circuit-breaker failures must not expose credentials, tokens, message bodies, or sensitive payloads.


### Non-Functional Requirements
#### Code Quality

- [ ] Every Python file must have a file-level docstring.
- [ ] Every public function and class must have a useful docstring.
- [ ] All public functions and methods must be typed.
- [ ] Inputs must be validated where appropriate.
- [ ] Output shapes must be explicit where applicable.
- [ ] Error behavior must be deterministic.
- [ ] Important events and recoverable failures must use structured logging.
- [ ] Production logic must not use `print()`.
- [ ] Official tools must not return unstructured `None`.
- [ ] Production code must not leak secrets in logs, errors, events, notifications, metrics, or health snapshots.
- [ ] The implementation must avoid avoidable circular imports.
- [ ] The implementation must be compatible with Black, isort, Flake8, mypy, pytest, and coverage.

#### Import-Time Performance And Side Effects

- [ ] Importing `tools.utils` must be lightweight.
- [ ] `tools/utils/__init__.py` must not eagerly import pandas, cryptography, dotenv, broker SDKs, network clients, notification clients, Prometheus exporters, or other heavy optional dependencies unless absolutely necessary.
- [ ] Heavy dependencies must be imported inside the specific submodule or function that needs them.
- [ ] Dataframe helpers must use lazy pandas imports or `TYPE_CHECKING` guards.
- [ ] Importing `tools.utils` must be safe in tests, CLI scripts, FastAPI startup, and agent runtime initialization.
- [ ] Importing any `tools.utils` module must not create files or directories.
- [ ] Importing any `tools.utils` module must not read `.env` files.
- [ ] Importing any `tools.utils` module must not configure global logging handlers unexpectedly.
- [ ] Importing any `tools.utils` module must not open network connections.
- [ ] Importing any `tools.utils` module must not initialize broker clients.
- [ ] Importing any `tools.utils` module must not initialize notification clients.
- [ ] Importing any `tools.utils` module must not initialize external pub/sub clients.
- [ ] Importing any `tools.utils` module must not mutate environment variables.
- [ ] Importing any `tools.utils` module must not run validation jobs.
- [ ] Importing any `tools.utils` module must not execute expensive dataframe operations.

#### Determinism, Concurrency, And Shared State

- [ ] Utility functions must be safe for concurrent use unless explicitly documented otherwise.
- [ ] Mutable module-level state must be avoided.
- [ ] Immutable constants and logger objects are allowed.
- [ ] Caller-owned inputs must not be mutated unless documented in the function name and docstring.
- [ ] Shared caches are allowed only when explicitly specified, bounded, and tested.
- [ ] Time-dependent helpers must support deterministic testing where practical.
- [ ] Time handling must be deterministic and timezone-safe across supported runtime environments.
- [ ] Wall-clock timestamp serialization must be UTC-first and safe for logs, events, notifications, metrics, health snapshots, and audit metadata.
- [ ] ID-dependent and randomness-dependent helpers must support deterministic testing where practical.
- [ ] Canonical JSON output must be deterministic across equivalent payloads.
- [ ] Logging output must be deterministic enough for unit testing where log fields are asserted.
- [ ] Auth helpers must avoid hidden global mutable state.
- [ ] Event Bus handler registration, unregistration, publishing, retry, dead-letter handling, and idempotency tracking must be thread-safe and/or async-safe.
- [ ] Event Bus handlers must not share mutable event payloads unless payloads are explicitly copied or treated as immutable by contract.
- [ ] Event Bus event versioning must support forward compatibility for event consumers.
- [ ] Event Bus delivery diagnostics must remain consistent under concurrent publishing.
- [ ] Notification routing, deduplication, throttling, rate-limit counters, and circuit-breaker state must be thread-safe and/or async-safe.
- [ ] Notification delivery diagnostics must remain consistent under concurrent alert bursts.
- [ ] Logging must be thread-safe under concurrent tool execution.
- [ ] Concurrency guarantees and limitations must be documented per component.

#### Optional Dependencies

- [ ] Optional dependencies must not break importability.
- [ ] Missing optional dependencies must fail only when the relevant feature is used.
- [ ] Missing optional dependency failures must be explicit.
- [ ] Missing optional dependency failures must use `HaruQuantConfigurationError`, `CONFIGURATION_ERROR`, or the standard tool error envelope where applicable.
- [ ] Optional dependency error messages must identify the missing dependency and required feature.
- [ ] Optional Event Bus broker dependencies must be lazy-loaded.
- [ ] Optional notification provider dependencies must be lazy-loaded.
- [ ] Optional Prometheus dependencies must be lazy-loaded.

#### Memory, Response Size, And Backpressure

- [ ] Utilities must be safe with large datasets.
- [ ] Utilities must avoid unnecessary deep copies.
- [ ] Dataframe helpers must document copy, view, and transformed-data behavior.
- [ ] Official AI tool responses must not return whole dataframes.
- [ ] Agent-facing diagnostics must prefer summaries, counts, and compact samples.
- [ ] Returned issue lists and samples must be bounded.
- [ ] Event Bus diagnostics must remain bounded to avoid oversized logs and metrics.
- [ ] Event Bus idempotency storage must be bounded by TTL and maximum cache size.
- [ ] Event Bus queues must have explicit limits.
- [ ] Queue-full behavior must fail fast or follow a documented bounded policy.
- [ ] Lossy-drop behavior may be allowed only when explicitly configured for low-severity telemetry events.
- [ ] Backpressure diagnostics must be bounded and redacted.

#### Performance

- [ ] `validate_ohlcv_quality` should handle 1,000 rows quickly for normal agent workflows.
- [ ] `validate_ohlcv_quality` should handle 100,000 rows within a practical local validation budget.
- [ ] Large data-quality validations must avoid unnecessary deep copies.
- [ ] Dataframe helpers must avoid repeated full-dataframe scans where possible.
- [ ] Schema validation helpers must be optimized for low latency.
- [ ] Schema validation helpers must not perform blocking I/O.
- [ ] Schema validation helpers must not perform network calls.
- [ ] Schema validation helpers must not introduce unbounded CPU spikes during normal market-data processing.
- [ ] Security helpers must avoid expensive redaction recursion loops.
- [ ] Security helpers must use recursion depth protection for nested structures.
- [ ] Security helpers must avoid logging sensitive payloads during failure.
- [ ] Logging overhead must be minimal for normal tool execution.
- [ ] Metrics collection must add low overhead.
- [ ] Health checks must be deterministic and fast.

#### Reliability And Degradation

- [ ] Logging must degrade safely if a logging sink fails.
- [ ] Metrics recording failures must not fail the original operation unless explicitly configured to fail closed.
- [ ] Notification delivery failures must be isolated from core utility functions unless explicitly configured otherwise.
- [ ] Notification routing must remain safe under repeated error bursts.
- [ ] Notification messages must be concise and actionable.
- [ ] External Event Bus broker outages must be isolated through circuit breakers and deterministic error codes.
- [ ] External notification provider outages must be isolated through circuit breakers and deterministic error codes.
- [ ] Component health checks must distinguish healthy, degraded, critical, unsupported, and not-configured states.

#### Observability Non-Functional Requirements

- [ ] Metrics labels must be bounded-cardinality.
- [ ] Metrics must be safe to expose to Prometheus without leaking secrets.
- [ ] Observability helpers must be import-safe without Prometheus dependencies.
- [ ] Logging output must be machine-parseable in production and human-readable enough for local development.
- [ ] Notification delivery must be observable through logs, metrics, or sanitized events.
- [ ] Grafana dashboard definitions must be version-controlled if implemented as files.
- [ ] Observability must support local/test no-op behavior.
- [ ] Health checks must distinguish healthy, degraded, and critical states.
- [ ] System-health observability must not be limited to trading or business alerts.


### Business Rules
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
- [ ] The utilities module must not implement UI, database repositories, or backtest engines.
- [ ] Utilities may validate, normalize, redact, serialize, route events, emit notifications, record metrics, and report issues.
- [ ] Utilities must not approve or reject trades.
- [ ] Utilities must not recommend allocations.
- [ ] Utilities must not decide strategy promotion.
- [ ] Utilities must not approve risk changes.
- [ ] Utilities must not place, close, modify, or cancel orders.
- [ ] Utilities must not activate live systems.
- [ ] Utilities must not override kill switches.
- [ ] Modules requiring financial decisions must call the appropriate risk, portfolio, execution, strategy, or governance domain.
- [ ] Agents must not call low-level helpers such as `normalize_timestamp`, `ensure_dir`, or `hash_password` unless a workflow explicitly approves that capability.
- [ ] Auth helpers may validate identity context, roles, scopes, and permissions, but must not become the identity provider.
- [ ] Event Bus utilities may route events, but must not own application orchestration.
- [ ] Event Bus utilities must not place trades, approve trades, modify orders, activate live systems, or override kill switches.
- [ ] Notification utilities may alert humans or systems, but must not make trading, portfolio, risk, or strategy decisions.
- [ ] Observability utilities may report system health, but must not decide operational actions without governance approval.
- [ ] Prometheus/Grafana metrics must include system-health visibility and must not be limited to business alerts.
- [ ] Email, Telegram, and desktop notifications must be disabled unless configured for the current environment.
- [ ] Production desktop notifications must be disabled by default.
- [ ] Notification recipients must be configured explicitly.
- [ ] Alert routing must fail safely and must not expose sensitive information.
- [ ] Authorization checks must deny access by default when context is missing or malformed.
- [ ] Agent access to official tools must be allowlisted.


### Inputs and Outputs
#### Inputs

- [ ] Official AI tools must accept optional `request_id`.
- [ ] OHLCV validation must accept a pandas DataFrame.
- [ ] OHLCV validation must accept optional symbol and timeframe context.
- [ ] OHLCV validation must accept configurable datetime, open, high, low, close, volume, and spread column names.
- [ ] OHLCV validation must accept configurable gap multiplier, spike threshold, issue-sample limit, and returned-issue limit.
- [ ] Schema validation must accept payload mappings.
- [ ] Input/output schema validation must accept schema mappings.
- [ ] Schema validators must accept optional `schema_version`.
- [ ] Schema validators must accept resource-limit configuration where applicable.
- [ ] Numeric-range validation must accept a value, logical field name, optional minimum, optional maximum, and `allow_none`.
- [ ] Freshness validation must accept timestamp metadata, configurable timestamp field, injected `now`, and `max_age_seconds`.
- [ ] Blocked-action validation must accept payload and blocked-action list.
- [ ] Artifact-reference validation must accept artifact identity, version, and location/hash fields.
- [ ] Identity helpers must accept prefixes and version strings.
- [ ] Timestamp helpers must accept datetime-like values and explicit timezone assumptions.
- [ ] Path helpers must accept string or `Path` values and optional `base_dir`.
- [ ] Security helpers must accept text, scalars, mappings, passwords, hashed passwords, encryption keys, encrypted tokens, and secret-version mappings.
- [ ] Settings loaders must accept mappings and optional `.env` file paths.
- [ ] Auth helpers must accept sanitized auth context mappings or typed auth context objects.
- [ ] Auth helpers must accept required permissions, roles, scopes, and tool names.
- [ ] Event Bus publishing must accept an event type, source, severity, payload, metadata, request ID, workflow ID, correlation ID, and idempotency key.
- [ ] Event Bus subscription must accept topic or event-type filters and handler references.
- [ ] Error routing must accept sanitized exception context, deterministic error code, severity, request ID, workflow ID, and correlation ID.
- [ ] Notification routing must accept alert severity, channel preferences, sanitized message template data, and routing policy.
- [ ] Observability helpers must accept metric names, bounded labels, numeric values, durations, and component health states.
- [ ] Runtime settings must accept logging, notification, Event Bus, auth, and observability configuration.

#### Outputs

- [ ] Official AI tools must return standard HaruQuant tool envelopes.
- [ ] Official success responses must include `status="success"`, message, data, `error=None`, and metadata.
- [ ] Official error responses must include `status="error"`, message, `data=None`, error code/details, and metadata.
- [ ] `validate_ohlcv_quality` success data must include symbol, timeframe, rows checked, quality score, pass/fail state, severity, issues, summary, profile, and remediation.
- [ ] Data-quality issues must include code, severity, message, column, row count, and samples.
- [ ] Native validation helpers must return validation-result dictionaries containing at least `valid`, `message`, `code`, and `details`.
- [ ] Schema validation failures must include bounded invalid-field diagnostics with deterministic field paths.
- [ ] Path helpers must return `Path` objects.
- [ ] Settings loaders must return `RuntimeSettings`.
- [ ] Settings injection must return the same target mapping it mutates.
- [ ] Dataframe serialization must return JSON-safe records where practical.
- [ ] Canonical JSON serialization must return deterministic JSON strings.
- [ ] Timestamp formatting must return UTC ISO strings ending in `Z`.
- [ ] Error helpers must return deterministic names and fallback messages.
- [ ] Support helpers may return native Python values or raise typed exceptions.
- [ ] Auth helpers must return allow/deny decisions with sanitized reason details.
- [ ] Event Bus publish operations must return deterministic delivery or enqueue results.
- [ ] Event Bus delivery diagnostics must include delivered, failed, retried, dead-lettered, dropped counts, and queue depth where applicable.
- [ ] Error routing must return routed, suppressed, deduplicated, throttled, or failed status.
- [ ] Notification routing must return sent, suppressed, throttled, deduplicated, failed, or disabled status.
- [ ] Observability helpers must return metric registration or recording status where applicable.
- [ ] Health checks must return healthy, degraded, critical, unsupported, or not-configured status with sanitized details.


### User Roles
- [ ] **Agent/tool caller:** Calls approved official AI tools and receives standard envelopes.
- [ ] **Authorized tool caller:** A caller with explicit permission to invoke an official AI tool.
- [ ] **Authenticated principal:** A user, service, workflow, or agent identity represented in auth context.
- [ ] **Workflow caller:** Uses validation, tracing, metadata, event, alert, and handoff utilities in automated workflows.
- [ ] **Production module developer:** Imports support helpers from `tools.utils` and uses typed native helper APIs.
- [ ] **Higher-level domain module:** Data, research, simulation, risk, portfolio, execution, analytics, governance, and agentic workflow modules consume utility functionality.
- [ ] **Human approver:** Uses or is represented by approval packets requiring action, reason, evidence, risk class, and approval status.
- [ ] **Event publisher:** A module or workflow that emits validated events.
- [ ] **Event subscriber:** A handler that receives events by topic or event type.
- [ ] **Notification recipient:** A configured email, Telegram, or desktop recipient for alerts.
- [ ] **System operator:** A maintainer who monitors logs, alerts, metrics, dashboards, and health status.
- [ ] **Observability consumer:** A developer, operator, or automated monitor that uses Prometheus/Grafana metrics.
- [ ] **Maintainer/reviewer:** Governs public API changes, CI gates, quality checks, and acceptance criteria.
- [ ] **Security reviewer:** A maintainer responsible for auth, secret redaction, encrypted payload handling, and no-leak guarantees.
- [ ] **Security/audit consumer:** Relies on redacted logs, metadata, tool responses, canonical JSON, events, notifications, and secret-safe error handling.


### Edge Cases
- [ ] Empty or unsafe ID prefixes must fail validation.
- [ ] `ensure_version(None)` must return the default.
- [ ] Invalid datetime inputs must fail clearly.
- [ ] Naive datetimes must be normalized using the explicit assumed timezone.
- [ ] Stale checks must be deterministic when `now` is injected.
- [ ] Empty paths must fail validation.
- [ ] Unsafe path traversal outside `base_dir` must be rejected.
- [ ] Missing pandas must fail only when dataframe helpers are called.
- [ ] Missing required dataframe columns must fail clearly.
- [ ] Empty dataframes must be handled deterministically.
- [ ] Dataframe index mismatch must fail clearly when deterministic alignment is impossible.
- [ ] `chunked(size <= 0)` must fail clearly.
- [ ] Invalid OHLCV input type must return `INVALID_INPUT`.
- [ ] Missing mandatory OHLC columns must return structured `INVALID_INPUT`.
- [ ] Extra OHLCV columns must not fail validation unless they create ambiguity.
- [ ] Unparseable datetimes must be reported.
- [ ] Non-monotonic timestamps must be reported.
- [ ] Duplicate timestamps must be reported.
- [ ] Duplicate OHLC/OHLCV rows must be reported.
- [ ] Missing timestamps or inferred gaps must be reported when timeframe is known.
- [ ] Market-calendar gaps must be distinguished from unexpected gaps where session rules are supplied.
- [ ] Non-numeric OHLC values must be reported.
- [ ] Negative prices must be reported.
- [ ] Zero prices must be reported.
- [ ] Invalid high-low relationships must be reported.
- [ ] OHLC values outside high/low range must be reported.
- [ ] Zero volume must be reported when volume is supplied.
- [ ] Negative volume must be reported when volume is supplied.
- [ ] Non-numeric or negative spread must be reported when spread is supplied.
- [ ] Spikes must be detected using configurable thresholds.
- [ ] Flatline candles must be detected.
- [ ] NaN and infinity values must be detected.
- [ ] Symbol mismatches must be reported when symbol verification is available.
- [ ] Symbol verification must be marked `not_available` when no symbol column exists.
- [ ] Timeframe mismatches must be reported when timeframe is supplied.
- [ ] Issue lists and issue samples must truncate when limits are reached.
- [ ] Missing required payload fields must fail explicitly.
- [ ] Schema version mismatches must fail with `VALIDATION_FAILED`.
- [ ] Schema validation of deeply nested payloads must stop at configured depth.
- [ ] Schema validation of oversized payloads must fail with bounded diagnostics.
- [ ] Schema validation errors for nested fields must include deterministic field paths.
- [ ] Blocked-action payloads without `action` must fail clearly.
- [ ] Blocked actions must fail closed.
- [ ] Missing freshness metadata must fail.
- [ ] Stale data must fail deterministically.
- [ ] Invalid environment modes must fail.
- [ ] Artifact references missing identity, version, or location/hash must fail.
- [ ] Sensitive nested mappings and lists must be redacted without mutating input.
- [ ] Excessively deep redaction structures must stop at `MAX_REDACTION_DEPTH`.
- [ ] Invalid encryption input must fail safely.
- [ ] Missing or malformed encryption keys must fail without leaking key material.
- [ ] Missing active secret versions must fail with `HaruQuantSecurityError` or `SECRET_VERSION_NOT_FOUND`.
- [ ] Duplicate active secret versions with the same numeric version must fail with `SECRET_VERSION_CONFLICT`.
- [ ] Unknown error codes must resolve safely.
- [ ] Unknown non-HaruQuant exceptions must map safely at controlled tool boundaries.
- [ ] Missing auth context must deny access.
- [ ] Malformed auth context must deny access with a deterministic error.
- [ ] Missing required role, permission, or scope must deny access.
- [ ] Unknown tool name in authorization checks must deny access.
- [ ] Event publishing with missing event type must fail validation.
- [ ] Event publishing with unserializable payload must fail validation.
- [ ] Event publishing with sensitive payload must redact before logging or notification routing.
- [ ] Duplicate event IDs must be handled idempotently where idempotency keys are supplied.
- [ ] Idempotency cache TTL expiration must not break valid future event processing.
- [ ] Idempotency cache eviction must not expose old event payloads.
- [ ] Concurrent publish calls for the same idempotency key must not double-deliver an event.
- [ ] Subscriber failure must not prevent other subscribers from receiving the event.
- [ ] Concurrent subscriber registration and publishing must not corrupt handler lists.
- [ ] Concurrent subscriber unregistration during publishing must have deterministic behavior.
- [ ] Repeated subscriber failures must route to dead-letter handling after configured retry limits.
- [ ] Event Bus queue overflow must return `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` and must not block indefinitely.
- [ ] Notification channel disabled must return disabled or suppressed status without error.
- [ ] Notification credentials missing must fail safely without leaking configuration details.
- [ ] Notification provider timeout must return failed status and emit metrics.
- [ ] Repeated identical alerts must be deduplicated or throttled.
- [ ] Notification markdown rendering failure must fall back to plain text.
- [ ] Unsupported notification formatting must not fail the original operation unless fail-closed alerting is explicitly configured.
- [ ] Prometheus dependency missing must not break module import.
- [ ] Prometheus exporter unavailable must degrade to no-op metrics or explicit configuration error depending on caller mode.
- [ ] High-cardinality metric labels must be rejected or normalized.
- [ ] Health check failures must not expose secrets.
- [ ] Recursive error routing must be detected and suppressed.
- [ ] External pub/sub adapter outage must open the circuit after the configured threshold.
- [ ] Notification adapter outage must open the circuit after the configured threshold.
- [ ] Open circuit state must fail fast.
- [ ] Half-open circuit recovery must not create duplicate event delivery.
- [ ] Clock drift unavailable must be reported as unsupported, not healthy.
- [ ] Clock drift above warning threshold must produce degraded health.
- [ ] Clock drift above critical threshold must produce critical health.
- [ ] Redaction allowlist conflicts with denylist must fail closed unless explicitly approved.
- [ ] Sensitive metric labels must be rejected before metrics emission.


### Error Handling Expectations
- [ ] Support helpers may raise typed HaruQuant exceptions for programmer or validation errors.
- [ ] Official AI tools must not raise expected validation errors to callers.
- [ ] Official AI tools must return standard error envelopes for expected validation failures.
- [ ] Expected validation failures should use deterministic codes such as `INVALID_INPUT` or `VALIDATION_FAILED`.
- [ ] Unexpected execution failures must return `TOOL_EXECUTION_FAILED` or another safe deterministic error code.
- [ ] Raw exception objects must never be returned in `data`.
- [ ] Raw exception objects must never be returned in `error`.
- [ ] Error details must not expose secrets.
- [ ] Unknown non-HaruQuant exceptions must map safely to `UNKNOWN_ERROR` or `TOOL_EXECUTION_FAILED`.
- [ ] Domain-specific errors must be mappable through `HaruQuantError` inheritance or a compatible `code` attribute.
- [ ] Error helpers must not raise for unknown codes unless explicitly requested.
- [ ] Error messages must be human-readable and actionable.
- [ ] Auth failures must map to `PERMISSION_DENIED`, `INVALID_AUTH_CONTEXT`, or `AUTHORIZATION_FAILED`.
- [ ] Event validation failures must map to `INVALID_EVENT`.
- [ ] Event publish failures must map to `EVENT_PUBLISH_FAILED`.
- [ ] Event subscriber failures must map to `EVENT_HANDLER_FAILED`.
- [ ] Dead-letter routing failures must map to `EVENT_DEAD_LETTER_FAILED`.
- [ ] Queue-full errors must be returned immediately to publishers.
- [ ] Queue-full errors must include sanitized queue diagnostics.
- [ ] Backpressure errors must be distinct from subscriber execution errors.
- [ ] Subscriber execution errors must not be misclassified as publish failures unless publish requires synchronous all-handler success.
- [ ] Notification routing failures must map to `NOTIFICATION_FAILED`.
- [ ] Notification configuration failures must map to `CONFIGURATION_ERROR`.
- [ ] Notification failures must distinguish configuration failure, provider timeout, provider rejection, circuit-open state, throttling, and suppression.
- [ ] Observability export failures must map to `OBSERVABILITY_ERROR` or `CONFIGURATION_ERROR`.
- [ ] Metrics recording failures must not fail the original operation unless explicitly configured to fail closed.
- [ ] Circuit-open failures must return `CIRCUIT_OPEN` or provider-specific deterministic details.
- [ ] Circuit-open failures must be observable through logs and metrics.
- [ ] Clock-drift health failures must return `CLOCK_DRIFT_DETECTED` where the error boundary requires a deterministic code.
- [ ] Schema validation errors must include invalid-field path, error code, sanitized message, and bounded details.
- [ ] Redaction allowlist misuse must return `SECURITY_ERROR` or a more specific deterministic security code.
- [ ] Error routing failures must not recursively trigger infinite error routing.
- [ ] Error events must include sanitized details only.
- [ ] Alert failures must be logged and measured without exposing secrets.
- [ ] Unknown Event Bus or notification provider errors must map safely to deterministic error codes.
- [ ] Error routing must preserve original error code and attach routing failure code separately when both exist.

#### Approved Error-Code Registry Additions

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


### Security Requirements
- [ ] Sensitive values must be redacted before logging.
- [ ] Sensitive values must be redacted before appearing in error responses.
- [ ] Sensitive values must be redacted before appearing in metadata.
- [ ] Sensitive values must be redacted before appearing in remediation messages.
- [ ] Sensitive values must be redacted before canonical JSON serialization where configured.
- [ ] Sensitive values must be redacted before appearing in exception text exposed to callers.
- [ ] Sensitive values must be redacted before appearing in Event Bus payload logs.
- [ ] Sensitive values must be redacted before appearing in notification templates.
- [ ] Sensitive values must be redacted before appearing in Prometheus metrics or Grafana variables.
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
- [ ] Security regression tests must prove common secret patterns do not leak.
- [ ] Encryption and decryption failures must not expose plaintext or key material.
- [ ] Secret selection must be deterministic.
- [ ] Auth context must be redacted before logging.
- [ ] Authorization headers must never appear in logs, metrics, events, or notifications.
- [ ] Notification recipient lists must be treated as sensitive configuration.
- [ ] Email credentials must never appear in logs, metrics, events, or notifications.
- [ ] Telegram bot tokens must never appear in logs, metrics, events, or notifications.
- [ ] Desktop notification content must not include secrets.
- [ ] Event payloads must be redacted before publication when they contain sensitive fields.
- [ ] Event metadata must not include secrets.
- [ ] Metrics labels must not include secrets, tokens, raw payloads, full exception strings, or user-provided arbitrary values.
- [ ] Prometheus metrics must avoid high-cardinality sensitive identifiers.
- [ ] Grafana dashboard variables must not expose secrets.
- [ ] Error routing must sanitize exception text before alerting.
- [ ] Dead-letter event storage, if configured outside utils, must receive redacted payloads by default.
- [ ] Agent tool authorization must use explicit allowlists.
- [ ] Side-effecting notification and event adapter actions must require explicit configuration.
- [ ] External notification and pub/sub adapters must be lazy-loaded.
- [ ] External notification and pub/sub adapters must fail closed when credentials are missing or malformed.
- [ ] Idempotency keys must not encode raw secrets or raw payloads.
- [ ] Event IDs, request IDs, workflow IDs, and correlation IDs must be safe for logs and metrics.
- [ ] Event payload hashes, if used for idempotency conflict detection, must not allow reconstruction of sensitive payloads.
- [ ] Queue diagnostics must not include raw payloads.
- [ ] Circuit-breaker diagnostics must not include credentials, provider tokens, message bodies, or raw event payloads.
- [ ] Clock-drift diagnostics must not expose infrastructure secrets.
- [ ] Redaction allowlist configuration must be reviewed and tested.
- [ ] Redaction allowlist entries must be narrow and auditable.
- [ ] Metric labels must reject raw IDs, arbitrary user strings, exception strings, notification recipients, provider tokens, and event payload values.
- [ ] Dead-letter payloads must be redacted by default before storage or forwarding.
- [ ] Notification markdown rendering must escape or sanitize unsafe user-controlled content where applicable.
- [ ] Auth and notification provider credentials must be excluded from Event Bus payloads by default.


### Tests Required
- [ ] Unit tests must exist for every utility module.
- [ ] Usage examples must exist for official AI tools.
- [ ] Minimum line coverage must be at least 80% for `tools.utils`.
- [ ] Branch coverage must be meaningful for validators and security helpers.
- [ ] Tests must cover success paths.
- [ ] Tests must cover invalid inputs.
- [ ] Tests must cover edge cases.
- [ ] Tests must cover failure paths.
- [ ] Official AI tool tests must verify standard return schema compliance.
- [ ] Official AI tool tests must verify metadata correctness.
- [ ] Official AI tool tests must verify request ID propagation.
- [ ] Official AI tool tests must verify `execution_ms` existence.
- [ ] Official AI tool tests must verify deterministic error codes.
- [ ] Official AI tool tests must verify no secret leakage where relevant.
- [ ] Logger tests must verify duplicate handler prevention.
- [ ] Logger tests must verify log emission does not leak passwords, tokens, API keys, broker credentials, encryption keys, private payloads, full approval packets, notification provider credentials, authorization headers, or Telegram bot tokens.
- [ ] Logger tests must verify file logging writes only to configured safe log directories.
- [ ] Logger tests must verify log rotation by maximum file size or equivalent configured policy.
- [ ] Logger tests must verify old rotated log files are deleted according to configured retention limits without deleting unrelated files.
- [ ] Logger tests must verify human-readable console formatting includes datetime, level, module path, function name, line number, and message.
- [ ] Logger tests must verify colorized console output can be enabled and disabled deterministically.
- [ ] Standard response tests must verify success envelope, error envelope, metadata, invalid schema, missing keys, execution timing, schema constants, and error code validation.
- [ ] Error tests must verify exception attributes, known codes, unknown codes, and fallback messages.
- [ ] Identity tests must verify ID uniqueness, prefix validation, and version defaulting.
- [ ] Normalization tests must verify ISO parsing, naive timezone assumptions, UTC conversion, and stale checks.
- [ ] Path tests must verify safe normalization, unsafe traversal, directory creation, and parent creation.
- [ ] Dataframe tests must verify alignment, serialization, UTC timestamp output, comparison, index mismatch behavior, missing columns, chunk-size validation, and no input mutation.
- [ ] Data-quality tests must verify clean OHLCV data, missing columns, extra columns, symbol mismatch, timeframe mismatch, duplicates, gaps, bad OHLC, zero/negative values, spread, volume, spikes, flatlines, truncation limits, and schema compliance.
- [ ] Data-quality tests must cover at least 15 distinct data-quality cases.
- [ ] Data-quality tests must verify 10,000 bad rows return no more than configured issue and sample limits.
- [ ] Schema-validation tests must verify native helper results, required fields, input/output schemas, schema versioning, handoffs, evidence, approvals, registry entries, blocked actions, freshness, and artifact references.
- [ ] Schema-validation tests must verify invalid-field paths for flat and nested payloads.
- [ ] Schema-validation tests must verify payload-size, depth, field-count, issue-count, and sample-count limits.
- [ ] Schema-validation tests must verify low-latency behavior with representative market-data payloads.
- [ ] Schema-validation tests must verify no blocking I/O or network access occurs.
- [ ] Security tests must verify redaction, nested redaction, password hashing, password verification, Fernet key behavior, encryption round trip, invalid tokens, secret selection, and `SECRET_VERSION_NOT_FOUND`.
- [ ] Security tests must verify redaction denylist matching.
- [ ] Security tests must verify audited allowlist exceptions.
- [ ] Security tests must verify denylist/allowlist conflict behavior.
- [ ] Security tests must verify metric labels reject sensitive or high-cardinality values.
- [ ] Settings tests must verify defaults, mapping load, invalid environments, `strict_validation`, path normalization, and injection.
- [ ] Auth tests must cover valid auth context.
- [ ] Auth tests must cover missing auth context.
- [ ] Auth tests must cover malformed auth context.
- [ ] Auth tests must cover missing role, permission, and scope.
- [ ] Auth tests must cover denied-by-default behavior.
- [ ] Auth tests must verify no token or credential leakage.
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
- [ ] Error-routing tests must cover validation error routing.
- [ ] Error-routing tests must cover unexpected exception routing.
- [ ] Error-routing tests must cover deduplication and throttling.
- [ ] Error-routing tests must cover recursive error suppression.
- [ ] Error-routing tests must verify recursive alert suppression under circuit-open and notification-failure scenarios.
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
- [ ] Observability tests must cover metrics registration.
- [ ] Observability tests must cover tool-call counters and latency histograms.
- [ ] Observability tests must cover Event Bus metrics.
- [ ] Observability tests must cover notification metrics.
- [ ] Observability tests must cover auth failure metrics.
- [ ] Observability tests must cover no-op behavior when Prometheus dependencies are unavailable.
- [ ] Observability tests must use fake Prometheus exporters where exporter behavior must be exercised without external services.
- [ ] Observability tests must reject high-cardinality or sensitive metric labels.
- [ ] Observability tests must verify clock-drift healthy, degraded, critical, unsupported, and not-configured states.
- [ ] Observability tests must verify circuit-breaker metrics.
- [ ] Observability tests must verify queue-depth metrics.
- [ ] Health-check tests must cover healthy, degraded, critical, unsupported, and not-configured states.
- [ ] Grafana documentation tests or review checks must confirm dashboards cover system health, tool health, Event Bus, notifications, errors, and auth failures.
- [ ] A concurrency stress test suite must exist outside the fast unit-test path.
- [ ] A chaos-test profile must cover notification provider failures and pub/sub adapter outages.
- [ ] CI must pass Black, isort, Flake8, mypy, pytest, and the coverage gate.


### Documentation Requirements
- [ ] Every Python file must start with a file-level docstring.
- [ ] File-level docstrings must state purpose.
- [ ] File-level docstrings must state whether the file contains official AI tools or support helpers.
- [ ] File-level docstrings must list exported public functions/classes.
- [ ] File-level docstrings must describe side effects, if any.
- [ ] Every public function must document what it does.
- [ ] Every public function must document when to use it.
- [ ] Every public function must document arguments.
- [ ] Every public function must document return value.
- [ ] Every public function must document raised exceptions or structured error behavior.
- [ ] Every public function must document side effects, if any.
- [ ] Official AI tool docstrings must be agent-facing.
- [ ] Official AI tool docstrings must explain when an agent should use the tool.
- [ ] Official AI tool docstrings must explain what evidence the tool produces.
- [ ] Official AI tool docstrings must explain what the tool does not do.
- [ ] Official AI tool docstrings must explain what error codes may be returned.
- [ ] Usage examples must demonstrate success and error handling.
- [ ] Usage examples must use realistic inputs.
- [ ] Usage examples must use `request_id` where applicable.
- [ ] Documentation must describe the structured logging schema.
- [ ] Documentation must describe required log fields and optional trace fields.
- [ ] Documentation must describe UTC-first time policy.
- [ ] Documentation must describe monotonic execution timing policy.
- [ ] Documentation must describe auth context fields.
- [ ] Documentation must describe authorization deny-by-default behavior.
- [ ] Documentation must describe Event Bus event envelope fields.
- [ ] Documentation must define Event Bus idempotency TTL behavior.
- [ ] Documentation must define Event Bus idempotency maximum cache-size behavior.
- [ ] Documentation must define Event Bus queue-full and backpressure behavior.
- [ ] Documentation must define Event Bus delivery, retry, and dead-letter behavior.
- [ ] Documentation must define Event Bus concurrency guarantees.
- [ ] Documentation must define whether the Event Bus implementation is synchronous, asynchronous, or dual-mode.
- [ ] Documentation must state that deterministic ordered delivery applies to the in-process Event Bus per event type, not necessarily to distributed broker adapters.
- [ ] Documentation must describe error routing behavior and severity rules.
- [ ] Documentation must describe notification routing rules for email, Telegram, and desktop channels.
- [ ] Documentation must define notification routing concurrency guarantees.
- [ ] Documentation must define whether each notification adapter is synchronous, asynchronous, or dual-mode.
- [ ] Documentation must describe notification throttling and deduplication behavior.
- [ ] Documentation must describe notification markdown and plain-text template fallback behavior.
- [ ] Documentation must describe circuit-breaker configuration for notification adapters.
- [ ] Documentation must describe circuit-breaker configuration for external pub/sub adapters.
- [ ] Documentation must describe circuit-breaker metrics and health states.
- [ ] Documentation must describe clock-drift monitoring and environment-specific thresholds.
- [ ] Documentation must describe Prometheus metrics names, labels, and cardinality limits.
- [ ] Documentation must describe Grafana dashboard expectations.
- [ ] Documentation must describe how to run observability in no-op/local/test mode.
- [ ] Documentation must define schema-validation invalid-field path format.
- [ ] Documentation must define schema-validation resource limits and performance expectations.
- [ ] Documentation must describe redaction denylist defaults.
- [ ] Documentation must describe audited redaction allowlist configuration.
- [ ] Documentation must include examples of safe redaction allowlist use.
- [ ] Documentation must warn against broad redaction allowlist rules.
- [ ] Documentation must describe safe metric-label rules and examples of rejected labels.
- [ ] Documentation must include safe examples that do not contain real secrets.
- [ ] Documentation must describe which features are support helpers and which are official AI tools.
- [ ] Documentation must include schema examples for evidence packs, approval packets, registry entries, freshness metadata, and artifact references.
- [ ] Documentation must maintain compatibility review notes for future public API changes.
- [ ] Documentation must describe which adapters are optional and lazy-loaded.
- [ ] Documentation must describe how alerts and error routing are initialized early in the system lifecycle.
- [ ] Documentation must include a production readiness checklist for secrets, auth, alert routing, and metrics before enabling live workflows.
- [ ] Documentation must include an operational runbook for critical utility-layer failures.
- [ ] Documentation must include runbook sections for Event Bus backpressure incidents, notification outage incidents, clock-drift incidents, and schema-validation performance regressions.
- [ ] Documentation must include a dashboard review checklist to ensure Grafana panels cover system health, not only trading or business outcomes.
- [ ] Documentation must document each event type's ordering, durability, retry, and loss-tolerance expectations.


### Assumptions
- [ ] This is a domain-level requirements document for `docs/planning/DOMAIN.md`, not a sprint-specific requirements document.
- [ ] The implementation is expected to be fresh and clean, with no backward-compatibility shims.
- [ ] Support helpers remain native unless explicitly classified as official AI tools.
- [ ] Conditional AI tools remain support helpers unless direct agent use is approved.
- [ ] `tools.data` will own repair, resampling, enrichment, persistence, and cleaning workflows for market data.
- [ ] Data-quality market-calendar gap handling depends on session rules being supplied by a caller or future domain module.
- [ ] Optional dependencies may or may not be installed; importability must remain intact either way.
- [ ] The default OHLCV scoring model applies unless a later module-specific specification replaces it.
- [ ] Strict schema-version enforcement occurs only when a caller or schema requires a version.
- [ ] No UI, broker runtime, database repository, or LLM framework dependency is required inside `tools.utils`.
- [ ] The utils module will provide auth primitives and validation helpers, but the application or infrastructure layer will own external identity-provider integration.
- [ ] The utils module will provide Event Bus contracts and an in-process implementation, while production broker-backed adapters may live in infrastructure modules or optional adapters.
- [ ] The Event Bus is intended for utility, workflow, alert, and error-routing events, not direct trading execution.
- [ ] Notification helpers will provide routing contracts and adapter boundaries, not hard-coded provider credentials.
- [ ] Email, Telegram, and desktop notification providers will be configured explicitly per environment.
- [ ] Prometheus metrics export may be provided by application runtime, while utils provides metric registration and recording helpers.
- [ ] Grafana dashboards may be maintained as documentation or version-controlled dashboard definitions.
- [ ] Sensitive runtime settings and provider credentials are supplied through secure environment/configuration mechanisms.
- [ ] No notification channel is enabled in production without explicit configuration.
- [ ] Metrics and logs are operational telemetry and must not contain raw market payloads, secrets, or approval-packet contents.


### Notes / Future Improvements
Sprint 001 is expected to build Utils/Foundation first. Exact adoption of existing implementation code is pending owner decision. Production-backed event bus adapters, provider-specific notification clients, Grafana dashboard definitions, and external identity-provider token validation are later integration decisions unless explicitly approved for the sprint.

## Data

### Purpose

Provide normalized data access, launch-critical MT5 integration, SQLite persistence, provider adapters, broker state reads, and crash-recovery state.

### Owns

Historical data, real-time feeds, normalization, market data bars/ticks, provider aliases, SQLite repositories, migrations, data cache/state, broker read adapters, and provider status.

### Does Not Own

Strategy logic owned by `tools/strategies/`, simulation/backtesting engine logic owned by `tools/simulation/`, analytics scoring, risk approval, portfolio allocation, trading order intent creation, live activation, governance approval, UI display policy, or conversation memory.

### Public Capabilities

- Load normalized bars/ticks.
- Read broker/account state through adapters.
- Persist state and market data through repositories.
- Expose provider status and data quality flags.
- Support mock/simulated providers for tests.

### Functional Requirements

- Normalize provider data before downstream use.
- Validate OHLCV geometry, timestamps, duplicates, gaps, and provider/source metadata.
- Isolate MT5 behind adapters.
- Use migrations for durable schema changes.
- Keep broker raw payloads redacted where persisted.
- Define per-tool contracts before Builder handoff, including required inputs, optional inputs, enum values, output schema, metadata additions, side-effect flags, deterministic errors, network behavior, and success/error examples.
- Keep source readiness explicit in a central manifest; local CSV, Parquet, and synthetic sources may start production-ready, while MT5 and other external/broker sources remain staging until promotion evidence is approved.
- Require source promotion evidence before staging sources become production-ready, including mocked tests, live validation where applicable, normalization evidence, quality-validation evidence, timeout/rate-limit behavior, license review, credential redaction, no-secret-leakage tests, and operator sign-off.
- Keep optional adapter dependencies lazy so missing broker/vendor SDKs do not break local CSV, Parquet, synthetic, transform, scheduler-status, cache-status, or read-only status tools.
- Make scheduler status local and read-only by default; any source-health lookup must be explicitly requested and disclosed in metadata.
- Make duplicate scheduler job behavior deterministic: identical normalized job definitions with the same idempotency key replay the existing job, while conflicting duplicates return `DUPLICATE_JOB_CONFLICT`.
- Treat the Data scheduler as an internal data-module component, not a cross-cutting platform scheduler.
- Define precision policy, versioned schema identifiers, response-envelope version lock, symbol pagination, historical volume modes, cache race behavior, database pool defaults, feed backpressure, feed clock-drift handling, file-corruption behavior, concurrent path write locking, schema-migration failure behavior, and resilience error codes before Builder handoff.
- Keep Data enum manifests, source readiness, source license, limits, schema identifiers, planned schema paths, and the Data engineering benchmark profile in `docs/source-requirements/02-data.md`.
- Keep backfill chunks no larger than 10,000 normalized records or 1 calendar day of source time, whichever is smaller, unless a later owner-approved benchmark profile raises the limit with tests.
- Commit backfill checkpoints per source, symbol, data kind, timeframe, chunk start/end, schema version, normalization version, source revision, chunk ID, and idempotency key.
- Use exclusive path-scoped locks for storage writes; concurrent writes to the same final path must return deterministic `CONCURRENT_WRITE_LOCKED` behavior rather than corrupting data.
- `align_multitimeframe_data` must use no-lookahead defaults based on last closed higher-timeframe bars and disclose the availability mechanism in metadata.

### Non-Functional Requirements

Provider failures must be structured and safe. Missing MT5 must not crash unrelated workflows. SQLite access must remain behind repositories. Data tools must not leak raw DataFrames, NumPy arrays, SDK objects, sockets, stream handles, clients, credentials, or database objects across official tool boundaries. Performance, throughput, memory, soak, and load-test thresholds are engineering baselines measured against the Data engineering benchmark profile in `docs/source-requirements/02-data.md` until validated by accepted benchmark reports.

### Edge Cases

Missing MT5 terminal, provider timeout, duplicate timestamps, DST/timezone boundary bars, malformed OHLCV, missing volume/spread, provider alias collisions, migration partial apply, schema migration failure, corrupted local CSV/Parquet files, SQLite concurrency limits, disk-full writes, concurrent writes to the same path, cache clear/read races, missing timezone data, feed clock drift, memory pressure, and already-running scheduler jobs.

### Tests Required

Adapter boundary tests, normalization fixtures, repository tests, migration checks, data quality tests, provider-unavailable tests, contract snapshot tests, import/export surface tests, deterministic error-response tests, optional dependency tests, source promotion review checks, performance/load/stress tests, feed soak tests, scheduler chaos tests for mid-backfill termination and exact checkpoint resume, cache race tests, storage failure tests, same-path write concurrency tests, and documentation example tests.

### Notes / Future Improvements

First-release symbols, timeframes, and account modes are pending. Detailed supporting Data handoff requirements live in `docs/source-requirements/02-data.md`, subordinate to this active module summary.

## Indicator

### Purpose

Compute standard and custom indicators over normalized, validated data as a pure, deterministic calculation library. Indicator outputs are decision-support artifacts only and do not own trade, order, fill, risk, or final strategy decisions.

### Owns

Indicator registry, indicator definitions, formula specifications, parameter validation, calculation outputs, availability metadata, capability-matrix metadata, cache-key material, injected calculation adapters, public type contracts, and indicator result schemas.

### Does Not Own

Broker calls, order creation, strategy lifecycle, risk decisions, simulation errors, external cache storage mechanisms, telemetry collectors, audit storage, system clock synchronization, timezone database maintenance, or persistence ownership outside approved result storage.

### Public Capabilities

- List available indicators.
- Validate indicator parameters.
- Run indicators over normalized bars.
- Return deterministic indicator outputs.
- Expose machine-readable capability matrix metadata generated from the registry.
- Return structured indicator errors through the approved exception/result-error mode.

### Functional Requirements

- Inputs must be normalized and non-empty.
- Required columns must exist.
- Periods and parameters must be valid.
- Unknown indicators are rejected.
- Output columns must not silently overwrite unrelated user columns.
- Exact formula tables for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R must be approved before Core MVP implementation begins.
- Public type contracts for `data`, config, context, result, manifest, state, and errors must be approved before Builder handoff.
- Default resource limits, cache degradation behavior, checksum policy, and cache policy defaults must be approved before deterministic implementation begins.
- No-lookahead metadata must include `available_at`, source close timing, and downstream-readable lookahead-prohibition metadata.

### Non-Functional Requirements

Indicator calculations must be deterministic, import-time safe, free of calculation-path I/O except through injected mockable adapters, and efficient on approved benchmark datasets. Uncached and warm-cache p99 targets, numeric edge behavior, default resource limits, and deprecation timelines must be documented before Builder handoff.

### Edge Cases

Empty windows, insufficient lookback, invalid period, missing column, NaN/inf values, duplicate output names, conflicting output modes, lookahead access, cache backend unavailability, timezone database changes after UTC normalization, stale/compatible cache entries, and multi-timeframe weight mismatch.

### Tests Required

Deterministic fixtures, formula golden tests, parameter validation, edge-case data tests, registry contract tests, capability-matrix tests, public type contract tests, no-lookahead tests, numeric policy tests, cache-compatibility and cache-degradation tests, timezone-boundary tests, usage-example tests, and requirement-to-test traceability tests.

### Notes / Future Improvements

Detailed supporting Indicator handoff requirements live in `docs/source-requirements/03-indicator.md`, subordinate to this active module summary. Indicator Builder handoff is blocked until implementation pre-requisites are approved or explicitly deferred, including formula tables, public callable signatures and type contracts, error-mode defaults, cache/checksum and degradation policy, default resource limits, stable requirement IDs, requirement-to-test traceability, and production audit integrity policy. Optional acceleration, out-of-core, streaming, proprietary, canary, and distributed tracing behavior remain deferred unless explicitly promoted.

## Strategy

### Purpose

Compute strategy decisions from validated market data, indicators, configuration, strategy-local state, and approved read-only execution-state snapshots, then emit canonical signals, `TradeIntent` objects, diagnostics, checkpoints, and replay metadata. Strategy does not execute orders, manage accounts, mutate broker or portfolio state, or enforce official portfolio/risk/compliance rules.

### Owns

Strategy registry, strategy versions, lifecycle state, parameter schemas, canonical signal and `TradeIntent` creation, strategy-local decision state, checkpoints, replay metadata, diagnostics, read-only execution-state query declarations, and declarations consumed by external modules.

### Does Not Own

Risk approval, broker order placement, official fills, account state, portfolio mutation, official sizing, compliance enforcement, deployment rollout, disaster recovery, data normalization, indicator calculation internals, or UI business policy.

### Public Capabilities

- Register/list strategies only through approved registry contracts.
- Validate strategy references, version constraints, lifecycle status, and parameters.
- Generate canonical signals and `TradeIntent` objects.
- Emit diagnostics, replay manifests, checkpoints where enabled, and trace metadata.
- Provide exact Python signatures, versioned schemas, error decision tables, side-effect rules, batch/stream behavior, and contract tests before Builder handoff.

### Functional Requirements

- Strategy name and version/hash must be present before promotion.
- Parameters must match the strategy schema.
- Signals must use canonical fields.
- Neutral/no-action signals must not produce order intents.
- Lifecycle state must allow the requested environment.
- Strategy version constraints must resolve to one approved immutable version or fail deterministically.
- Strategy execution must use immutable read-only snapshots or documented consistency models for external state.
- Strategy must map data and indicator dependency failures into approved deterministic strategy-domain errors.
- Strategy configuration validation must reject code/configuration injection and bounded-resource abuse.
- Vectorized batches must fail atomically on lookahead or configured clock-drift violations and preserve diagnostics identifying the first failing decision timestamp.
- Partial data degradation must follow the declared missing-data policy and emit structured data-quality diagnostics when any degraded subset proceeds.

### Non-Functional Requirements

Strategies must be reproducible, versioned, auditable, import-time safe, deterministic under the same inputs/seed, bounded by approved resource limits, and covered by measurable latency/memory/checkpoint/diagnostic targets before implementation acceptance. Provisional v1.0 baselines in the supporting requirement source are event-driven P99 decision latency <= 10 ms, vectorized batch P99 <= 500 ms, per-instance memory <= 256 MB, checkpoint size <= 10 MB, diagnostic payload <= 64 KB per decision, configuration payload <= 64 KB, and dependency call timeout <= 2 seconds, subject to approved benchmark profile and owner/architecture tuning.

### Edge Cases

Invalid lifecycle state, missing version hash, unsatisfiable version constraint, deprecated strategy, parameter drift, stale input data, data/indicator dependency failure, clock drift, configuration-injection payload, oversized configuration, no-action signal, duplicated strategy version, concurrent read-only state updates, and strategy promotion without governance.

### Tests Required

Lifecycle tests, parameter schema tests, signal and `TradeIntent` contract tests, no-action behavior tests, strategy registry tests, error-code tests, dependency-failure tests, clock-drift tests, concurrency/snapshot tests, security/resource-abuse tests, property-based no-lookahead tests across timezone and DST cases, replay tests, performance tests with approved reference environment, and requirement-to-test traceability tests.

### Notes / Future Improvements

Detailed supporting Strategy handoff requirements live in `docs/source-requirements/04-strategy.md`, subordinate to this active module summary. Strategy now has stable requirement IDs, public schema-contract baselines, provisional NFR baselines, read-only execution-state contracts, and a family-level traceability matrix in the supporting source. Strategy Builder handoff remains blocked until public API signatures, error decision tables, final quantitative SLO/reference performance environment, reviewed applicability tags and acceptance criteria, concrete test-case expansion, sandbox policy, lifecycle promotion gates, and governance/operations extraction decisions are approved.

## Risk

### Purpose

Intercept proposals/signals and produce approved, warning, approval-required, more-evidence, rejected, or blocked decisions based on deterministic policy, sizing, limits, portfolio state, broker state, reconciliation, approval state, and kill-switch controls.

Risk follows the architectural axiom that ambiguity is a hard failure: if the system cannot prove an action is safe, it must block it.

### Owns

Risk requests, decisions, constraints, sizing, exposure, drawdown, safety limits, portfolio-state checks, reconciliation gates, approval-token checks, risk-owned kill-switch state, scenario analysis, risk reports, audit metadata for risk decisions, and deterministic policy-engine behavior.

### Does Not Own

Market-data ingestion, long-term historical market-data ownership or caching, strategy signal creation, frontend details, broker submission, broker/account mutation, execution-control mutation, portfolio management, cost aggregation, incident management, lifecycle execution logic, broad portfolio source-of-truth state, governance policy ownership, broad reporting ownership, or LLM-based final approval.

### Public Capabilities

- Evaluate proposals through official risk tools only after tool contracts are approved.
- Produce risk decisions, constraint explanations, approval requirements, and risk-owned block states.
- Expose risk snapshots, sizing outputs, admission reviews, allocation reviews, scenario analysis, approval-token validation, kill-switch checks, and reports.
- Classify exports as official AI tools, public Python contracts, deterministic services, internal helpers, or legacy compatibility exports before Builder handoff.
- Use `tools/risk/__init__.py` and `tools.risk.__all__` as the strict public export registry; names outside `__all__` are private implementation details.
- Treat portfolio-under-risk surfaces as transitional compatibility facades targeting separate `tools/portfolio` ownership unless explicitly classified as risk-owned services.
- Emit deprecation warnings or metadata for transitional facades and migrate them to `tools/portfolio` or reapprove them no later than v2.0.

### Functional Requirements

- Live decisions require current broker/account state.
- Missing risk thresholds fail closed for live.
- Active kill switch blocks new entries.
- Risk decisions must expire or be revalidated when freshness windows close.
- Approved/reduced decisions are required before live order intent creation.
- Every official Risk tool must have a contract covering classification, inputs, output schema, status values, deterministic errors, side effects, network behavior, persistence behavior, and success/failure examples before Builder implementation.
- Canonical decision states are `approve`, `warn`, `needs_approval`, `needs_more_evidence`, `reject`, `block`, and `error`.
- Risk may emit execution-blocking decisions, but Execution/Governance must perform any broker or execution-control mutation.
- Public tool payloads default to a 1 MiB maximum unless an owner-approved profile sets a lower limit.
- Public tool payloads default to maximum JSON nesting depth 10 and maximum single-list length 10,000 before expensive validation or calculation.
- Time-sensitive services must accept injected time providers or explicit `now` values for deterministic expiry, stale-evidence, kill-switch timeout, step-down, and replay behavior.
- Public Pydantic V2 contracts must use strict Decimal handling, `allow_inf_nan=False`, deterministic `ROUND_HALF_EVEN` rounding unless explicitly overridden, and JSON serialization that does not silently convert Decimal values to floats.
- Non-positive-semidefinite correlation matrices must be detected and deterministically sanitized or rejected according to profile configuration.
- Structured logs, metrics, and audit records must carry propagated `correlation_id` or `trace_id`.
- Risk handoff requires a numbered requirements catalogue, transition/export mapping, private-helper list, benchmark definitions, and response-envelope examples.
- Production implementation is blocked until owner-approved decisions exist for double-spend prevention ownership, fractional Kelly multiplier, stressed lookbacks, crisis references, first heavy-tailed VaR distribution, and Gaussian VaR waiver behavior.

### Non-Functional Requirements

Risk behavior must be fail-closed, auditable, deterministic where needed, redacted, import-time safe, explicit about missing evidence, strict about Decimal serialization, bounded against payload abuse, and never guess live thresholds or unresolved production policy.

### Edge Cases

Missing thresholds, missing risk config, stale portfolio state, reconciliation mismatch, expired risk decision, unknown broker state, broker/system timezone mismatch, permission loss, active kill switch, unapproved overrides, malformed, deeply nested, or oversized payload, single arrays larger than 10,000 items, NaN/Infinity values, non-PSD correlation matrices, missing FX conversion, unavailable token-state backend, partial audit write, permission-denied governance/audit backend, clock skew, and concurrent approval double-spend.

### Tests Required

Fail-closed tests, sizing/limit tests, reconciliation gate tests, expiration tests, time-manipulation tests with injected clocks, kill-switch tests, audit tests, official-tool contract tests, export-classification tests, private-surface tests, Decimal/numeric validation and serialization tests, payload parsing abuse tests, non-PSD correlation tests, approval-token security tests, double-spend concurrency tests, persistence-failure tests, performance benchmark tests, response-envelope usage-example tests, and requirement-to-test traceability tests.

### Notes / Future Improvements

Detailed supporting Risk handoff requirements live in `docs/source-requirements/05-risk.md`, subordinate to this active module summary. Risk Builder handoff status is `BLOCKED: NOT READY FOR HANDOFF` until stable IDs, resolved or explicitly deferred `RISK-PEND-*` decisions, public contracts for official tools, export classification, portfolio-under-risk adapter ownership and v2.0 migration/reapproval plan, benchmark specifications, response-envelope examples, time/Decimal/payload guardrails, and requirement-to-test traceability are complete.

## Analytics

### Purpose

Compute performance, risk, statistical, trade, backtest, live/historic, and dashboard-ready metrics as non-binding evidence. Analytics outputs must not auto-approve, auto-promote, auto-allocate, or auto-execute strategies without separate governance/human approval.

### Owns

Analytics result schemas, approved official high-level tools, private canonical metric-kernel contracts, report-ready outputs, dashboard payload contracts, official tool catalog, metric definition catalog, warning/quality-flag catalogs, deterministic fail-closed adapters, lineage, reproducibility hashes, and caveat/warning metadata.

### Does Not Own

Live state mutation, broker submission, risk approval, strategy promotion, prop-firm enforcement, final portfolio allocation, benchmark/FX source authority, execution evidence generation, arbitrary file loading inside analytics core, distributed state management, distributed cache invalidation, message queues, async/background job orchestration, or public exposure of low-level metric kernels without catalog approval.

### Public Capabilities

- Calculate metrics from trades, equity curves, portfolio state, and simulations.
- Produce dashboard/report payloads.
- Compare performance across strategies, regimes, and runs.
- Build canonical analytics reports, portfolio reports, report comparisons, and non-binding strategy-quality evidence from validated supplied inputs.

### Functional Requirements

- Inputs must be validated and traceable.
- Results must include metadata, warnings, and source context.
- Metrics must distinguish simulated, paper, live, and historic data.
- Official tools must be listed in an approved Official Analytics Tool Catalog before Builder implementation; exports absent from that catalog are not public.
- Official metrics must be listed in a Metric Definition Catalog with formulas, units, annualization assumptions, undefined-result behavior, and golden-fixture expectations.
- Low-level metrics and aliases must remain internal/support/reference-only unless explicitly promoted through the Official Analytics Tool Catalog.
- Analytics owns canonical metric kernels as private/internal implementation details consumed through stable, versioned official tools and report interfaces.
- Trade classification must use a configured `breakeven_epsilon`; optional `NaN`/`NaT` observations may be filtered only with warnings, required `NaN`/`NaT` fields must fail unless cataloged as skippable, and `Infinity`/`-Infinity` must return structured validation errors.
- Deterministic adapters must fail closed with structured errors when required fields, schema versions, or compatibility mappings are missing or incompatible.
- Report generation must define required, optional, diagnostic-only, disabled, skipped, failed, and degraded section states.
- Official tools must validate `request_id` and return structured validation errors for missing, empty, malformed, duplicate-in-context, or unsafe IDs.
- Partial reports must be JSON-safe, explicitly non-promotable, and must not be treated as final approval evidence.
- Dashboard payload builders must consume validated report sections and must not recompute or fabricate core metrics.
- Multi-currency portfolio, TCA, and base-currency analytics must fail closed when required FX conversion is missing.
- Strategy-quality, prop-firm, and governance-adjacent outputs must be labeled as non-binding analytics evidence only.

### Non-Functional Requirements

Metrics must be reproducible and not overstate live readiness. Canonical monetary sums, cost aggregation, and base-currency aggregation must use `Decimal`; derived ratios may use deterministic `float64` with documented tolerance. Analytics must define payload, runtime, memory, statistical iteration, redaction, warning-ordering, dashboard truncation, local cache behavior, and schema compatibility policies before production handoff.

### Edge Cases

Empty trades, partial data, mixed environments, missing benchmark, divide-by-zero metrics, inconsistent timestamps, clock drift or timezone mismatches between strategy and benchmark/equity sources, duplicate trade IDs, conflicting PnL fields, invalid currency codes, ambiguous local timestamps, stale or missing FX rates, unsupported schema versions, oversized payloads, missing live/paper execution evidence, invalid request IDs, unsupported dataframe indexes, flat benchmark series, mixed cost sign conventions, and cache stampede/thundering-herd scenarios for identical report or input hashes.

### Tests Required

Metric fixtures, formula golden tests, official-tool catalog tests, public/internal boundary tests, standard-envelope snapshot tests, golden-file output-schema tests, request-ID validation tests, deterministic numeric/non-finite validation tests, empty/partial data tests, environment separation tests, adapter mapping tests, partial-report tests, dashboard payload contract tests, FX/currency tests, schema compatibility tests, warning/quality-flag tests, redaction tests, concurrency/cache determinism tests, performance benchmark tests from the approved Analytics limits ADR, and requirement-to-test traceability tests.

### Notes / Future Improvements

Detailed supporting Analytics handoff requirements live in `docs/source-requirements/06_analytics.md`, subordinate to this active module summary. Production handoff is blocked until the required Analytics ADRs approve the official tool surface, public/internal export classification, metric formulas, report criticality, thresholds, FX authority, schema compatibility, dashboard limits, performance limits, warning/quality-flag catalog, local cache behavior if implemented, and traceability matrix.

## Trading

### Purpose

Format deterministic order intents and orchestrate order lifecycle semantics shared by simulation, paper, and live paths.

### Owns

Order intents, idempotency material validation, canonical payload serialization contracts, Decimal/time normalization contracts, client order IDs, route-aware trading request packages, simulator-state mutation for simulation routes, execution lifecycle semantics, execution adapter contracts, credential/session interface consumption, redaction interface consumption, and persistence event payloads or repository interfaces for execution evidence.

### Does Not Own

Strategy generation, risk decisions, approval voting/state authority, rate-limiting policy enforcement, live broker readiness, live runtime authorization, broker secret resolution, live credential lifecycle, concrete persistence backend ownership, durable database schema/migration ownership, or direct bypass of approval, risk, idempotency, reconciliation, audit, kill-switch, or live-runtime gates.

### Public Capabilities

- Create order intents from approved/reduced risk decisions or simulation context.
- Validate order type, side, size, price, stop-loss, and take-profit logic.
- Preserve deterministic idempotency material.
- Expose route-aware trading contracts for `sim` and `live` while keeping simulation mutation, live request packaging, and live broker mutation clearly separated.
- Return `StandardTradingEnvelope v1` for public agent-facing trading tools.

### Functional Requirements

- Live order intents require approved/reduced risk decision.
- Idempotency keys must be deterministic from material fields.
- Live orders must not exceed approved volume.
- Buy/sell stop-loss and take-profit geometry must validate.
- Before Builder handoff, every exported trading tool must have a public contract covering classification, stability, supported routes, required and optional inputs, output schema, status values, error codes, side-effect class, approval requirement, idempotency behavior, audit metadata, network behavior, and persistence behavior.
- Before Builder handoff, Trading must include an Interface Definition Appendix with exact public callable signatures, parameter types, defaults, constraints, enum values, versioned schemas, `data` schemas, failure behavior, and usage examples.
- Trading must consume approval, risk, kill-switch, authorization, and live-runtime verdicts from owning modules instead of creating final policy decisions or independently authorizing live broker mutation.
- Live `trading_connect` must consume a pre-authorized Live-owned connection/session handle or injected credential provider interface and must not independently resolve secrets or initiate live broker login outside the Live-owned session boundary.
- `submit_order` and other route-aware actions may mutate simulator state for `route="sim"` but must only package live-compatible requests for `route="live"` unless an external live-runtime authority explicitly authorizes mutation and all safety gates pass.
- Trading rejection envelopes must include machine-readable error codes, field paths where applicable, retryability, severity, route, provider, request ID, and correlation ID.
- Readiness failure must return a rejected envelope with `READINESS_FAILED`, and concurrent mutation rejection must return `TRADING_CONCURRENCY_CONFLICT` with the documented concurrency scope.
- Prices, volumes, costs, margin, PnL, equity, and balance must use Python `decimal.Decimal`, default `ROUND_HALF_EVEN`, at least 28 digits of working precision, and a minimum 8-decimal quantization scale before validation, hashing, reporting, or persistence unless a stricter provider/instrument contract applies.
- Idempotency material must use UTF-8 canonical JSON with sorted keys, no insignificant whitespace, UTC timestamp strings, canonical Decimal strings, no floats in broker-critical material, and an approved cryptographic hash such as SHA-256.
- Broker-time evidence must be parsed and stored as timezone-aware UTC before validation, hashing, reporting, or persistence.
- Trading defines repository/interface contracts and persistence event payload schemas; Infrastructure, Data, Live, or another approved owner provides concrete implementations through dependency injection.

### Non-Functional Requirements

Trading paths must be deterministic, auditable, redacted, import-time safe, and safe to retry only under idempotency and reconciliation rules. Trading must reject stale context, enforce documented timeout and payload limits, serialize or reject conflicting concurrent mutations, and report readiness as successful only when all required checks pass. Default broker operation timeout is 10 seconds, broker check timeout is 5 seconds, market data freshness threshold is 5 seconds, maximum request payload size is 1 MiB, maximum readiness check count is 20, and maximum reconciliation snapshot size is 10,000 records or 5 MiB unless approved module-specific contracts override them. Proposed readiness aggregation p99 under 50 ms remains Pending benchmark/profile approval.

### Edge Cases

Idempotency key conflict, same key with different material fields, concurrent duplicate submissions, concurrent live connection attempts, expired live credential/session token, partial fills, stale risk decision, stale broker/account/risk context, invalid payload type or oversized payload, invalid price geometry, broker timeout after possible acceptance, network partition between send-attempt persistence and broker transmission, persistence failure after response, receipt without matching send attempt, DST/timezone skew, Decimal rounding changes, simulator resource exhaustion, redaction failure, and unknown provider result.

### Tests Required

Order intent contract tests, generated or mechanically checked public tool contract matrix tests, API signature tests, `StandardTradingEnvelope v1` tests, import-time safety tests, live credential/session boundary tests, idempotency tests, canonical serialization tests, Decimal-safe validation tests, property-based tests for idempotency/rounding/serialization/concurrency if approved tooling is available, route mutation-semantics tests, rejection-envelope tests, concurrency tests, broker-simulator failure injection tests, timeout/retry tests, persistence-failure tests, validation tests, retry/conflict tests, redaction tests, usage-example tests, and simulation/live separation tests.

### Notes / Future Improvements

Exact order intent schema, public tool matrix, Decimal policy, canonical serialization policy, credential/session interface, persistence interface direction, threshold overrides, property-based testing tool approval, requirement-to-test ID map, and first Trading implementation slice are pending final contract approval. Detailed supporting Trading handoff requirements live in `docs/source-requirements/07_trading.md`, subordinate to this active module summary.

## Simulation

### Purpose

Run historical data through the same Trading order-intent path used by live workflows without live broker side effects.

### Owns

Backtest runtime, canonical tick-based execution, replay, simulated fills, simulation run metadata, warnings, equity curves, immutable journals, JSON/Markdown reports, artifact manifests, and simulated trade records.

### Does Not Own

Live broker submission, real account mutation, production strategy promotion, strategy logic, indicator formulas, raw market-data acquisition, production risk-governor policy, external governance approvals, live adapter implementation/imports, OS-level scheduler/thread-pool/global-memory management beyond configured quotas, or arbitrary Python strategy-code execution through `run_backtest`.

### Public Capabilities

- Start simulation runs.
- Replay historical data.
- Produce simulated trades, equity, metrics, warnings, and artifacts.
- Expose `run_backtest` only after public request/response contracts, deterministic error codes, authorization behavior, artifact behavior, and schema compatibility rules are approved.
- Provide controlled simulation-compatible MT5-style accessors and `SimTrader` methods only through documented contracts.

### Functional Requirements

- Initial balance must be positive.
- Date ranges and symbols must be valid.
- Simulation cannot invoke live broker submission.
- Results must include run metadata, metrics, warnings, and trace IDs.
- Builder handoff must be limited to an approved Phase 1 FX canonical backtest slice unless a broader phase is explicitly approved.
- Every accepted implementation requirement must have a stable requirement ID, release phase, priority, owner, dependencies, acceptance criteria, and verification method.
- `run_backtest` must reject raw arbitrary Python strategy code and accept only registered strategy identifiers, validated strategy configuration, or separately approved sandboxed/vetted registry references.
- Public response envelopes must cover success, failed, queued, cancelled, and diagnostic-failed statuses before implementation.
- The Phase 1 Simulation specification must define a version table, deferred scope register, decision log, `run_backtest` contract scaffold, `SimTrader` protocol scaffold, Phase 1 edge/error matrix, and Phase 1 test suite before Builder handoff.
- Limit-order queue behavior, gap ambiguity behavior, and FX conversion precedence must use explicit configuration fields and deterministic defaults before Phase 1 implementation.
- Shared Trader protocol definitions may be reused for compatibility, but Simulation must not import, instantiate, or call live adapter implementation code.
- Future-scope schema or code included in Phase 1 must remain inert by default, feature-flagged or scope-tagged, and tested for deterministic unsupported-scope rejection.
- Protected production-candidate journals, artifact manifests, report bundles, and replay evidence must define encryption-at-rest requirements before externally accessible or production-candidate use.
- FX `production_realistic` classification requires an approved checklist covering data quality, broker/data manifests, execution/cost/margin/currency models, no-lookahead, journal persistence, replayability, and downgrades.

### Non-Functional Requirements

Runs must be reproducible with recorded inputs, seeds, versions, and data references. Simulation must be import-time safe, deterministic, auditable, redacted, backward-compatible within major schema versions, and explicit about production-realism downgrades. Controlled tool boundaries must return deterministic `SIM_*` errors, and unhandled boundary exceptions must map to `SIM_INTERNAL_ERROR` with redacted logging.
Performance numbers remain provisional engineering targets until the owner approves a Phase 1 benchmark profile and pass/fail gates.

### Edge Cases

Empty data window, invalid date range, missing local file, spread/slippage mismatch, no trades, long run cancellation, data gaps, malformed payload, unknown fields, timezone-naive timestamps, DST/session ambiguity, unauthorized actor, artifact path traversal, secrets in payloads, manifest checksum mismatch, concurrent manifest reads, disk-full journal writes, corrupted sidecar index, duplicate request IDs, and external dependency timeouts.

### Tests Required

Determinism tests, replay tests, simulated-fill tests, no-live-side-effect tests, result schema tests, public contract snapshot tests, import-time safety tests, arbitrary-code rejection tests, RBAC/path-security tests, journal persistence failure tests, fault-injection tests, DST/timezone tests, concurrent manifest-read tests, queued/diagnostic-failed executable usage-example tests, Phase 1 edge/error matrix tests, performance benchmark gates, and requirement-to-test traceability tests.

### Notes / Future Improvements

Detailed supporting Simulation handoff requirements live in `docs/source-requirements/08-simulation.md`, subordinate to this active module summary. Production handoff is blocked until the owner approves the Phase 1 FX slice, public API schemas, `SimTrader` protocol contracts, external interface contracts, artifact/journal schemas, deferred-scope register, decision log, acceptance criteria, and requirement-to-test traceability matrix.

## Optimization

### Purpose

Run bounded parameter-search, walk-forward, robustness, Monte Carlo, scoring, and optimization-result packaging workflows for research and simulation review without live-trading authority.

### Owns

Optimization request/response contracts, public service-tool packaging, objective selection, candidate ranking, stability and overfit diagnostics, robustness metadata, evidence-package contracts, candidate and parameter-space hashing, checkpoint/resume contracts, repository `Protocol` or abstract interface contracts, `BacktestExecutionAdapter` interface contracts, JSON serialization policy, canonical enums/error codes, and chart-ready handoff data.

### Does Not Own

Live execution, broker calls, automatic production promotion, final Risk Governor or Portfolio Manager approval, production database provisioning, database migrations, credential management, concrete repository implementations, database drivers, object-store clients, or UI chart rendering.

### Public Capabilities

- Package parameter sweep, walk-forward, comparison, persistence, report, and robustness requests.
- Rank candidates and calculate lightweight stability, overfit, and robustness summaries.
- Generate versioned optimization evidence packages for downstream review.
- Report metadata that always keeps `places_trade=False` and never returns live-trading approval.
- Keep lower-level search, execution, orchestration, repository-backed run control, and portfolio-optimization helpers internal until explicitly promoted through registry review.

### Functional Requirements

- Parameter ranges must be valid and bounded.
- Objective must be specified.
- Maximum run count must be enforced.
- Random seed or reproducibility material must be recorded when applicable.
- Optimization cannot mutate production strategy state without governance.
- Before Builder handoff, every Optimization requirement must have an ID, priority, scope tier, owner, acceptance criteria, and mapped tests.
- Before Builder handoff, every public optimization tool must define required inputs, optional inputs, output envelope schema, status values, error codes, warning codes, audit fields, side-effect metadata, network behavior, persistence behavior, and examples.
- Final optimization output states must use one canonical enum shared by requirements, schemas, tests, examples, and reports.
- Repository-backed workflows must use approved repository interfaces only; Optimization owns contracts and payload schemas, not production database operations unless separately assigned.
- Dry-run behavior must distinguish packaging tools from lightweight calculation tools.
- Omitted `dry_run` must default to `True`.
- Optimization workflows must record explicit reproducibility fields, including strategy ID, parameter-space definition, objective, data window, engine type/version, seed, cost model hash, simulator realism profile hash, module version, parameter-space hash, candidate hashes, and candidate results.
- `run_parameter_sweep` must require an approved `search_method` before implementation.
- Public outputs must serialize non-JSON-native values deterministically and fail closed with `OPT_JSON_SERIALIZATION_FAILED` for unsupported objects.
- `rank_parameter_sets` ties must be deterministic using trade count and candidate hash.
- Background task entry points must return task/progress references rather than blocking the caller.
- Production implementation is blocked until owner-approved limits exist for candidates, parameter-space expansion, runtime, workers, Monte Carlo simulations, objective whitelist, repository backend, artifact root, report schema version, and resource override approver.

### Non-Functional Requirements

Optimization must control compute load, remain import-time safe, reject oversized payloads before expensive work with `OPT_PAYLOAD_TOO_LARGE`, redact secrets and sensitive paths, enforce configured timeout/cancellation/backpressure policies for execution-capable workflows using monotonic clocks, and warn about overfitting risks. Proposed engineering baselines such as `<= 200 ms` packaging latency, `30 minute` execution timeout, and `3` network repository retry attempts remain subject to owner finalization.

### Edge Cases

Invalid search space, runaway run count, failed candidate, identical rankings, overfit result, missing reproducibility seed, DST/session-boundary split errors, duplicate or out-of-order market data, dry-run requests on calculation-only tools, cancellation during repository/checkpoint/report phases, corrupted checkpoints, repository permission or disk failures, network repository timeouts or connection-pool exhaustion, unavailable advanced sampler dependencies, candidate cache stampede, abrupt worker termination, non-JSON-native output values, artifact checksum mismatch, and incompatible optional dependencies.

### Tests Required

Bound enforcement tests, deterministic seed tests, ranking tests, failure-handling tests, no-production-mutation tests, public tool contract tests, golden-envelope tests, enum consistency tests, dry-run contract tests, JSON serialization tests, import-time safety tests, requirement-to-test traceability tests, repository/checkpoint/network-failure tests, chaos/resilience tests, DST/timezone tests, sampler dependency tests, cache-stampede tests, redaction tests, usage-example tests, and observability tests.

### Notes / Future Improvements

Detailed supporting Optimization handoff requirements live in `docs/source-requirements/09_optimization.md`, subordinate to this active module summary. Production handoff is blocked until scope tiers, public contracts, production limits, dry-run semantics, repository ownership/DI policy, `BacktestExecutionAdapter` ownership, JSON serialization policy, canonical enum/error values, requirement traceability, and pending owner decisions are resolved.

## Live

### Purpose

Provide the live trading runtime and governed live-mutation boundary around shared `route="live"` Trading functions. Live is a strict middleware/gateway for live-route requests, connects Trading to real broker APIs only after all live-readiness gates pass, and must not become a separate order, position, strategy, risk, approval, broker-policy, UI, or business-logic implementation.

### Owns

Live runtime orchestration, live enablement, broker readiness checks, live gate decision records, package-only versus broker-mutation side-effect classification, live execution adapter calls after all gates pass, live execution attempts, live receipts, live reconciliation authority state, kill-switch enforcement, live action policy-matrix enforcement, rate-limit response classification, incident records, notifications, structured JSON runtime events, and live audit events.

### Does Not Own

Strategy signals, strategy selection, financial advice, risk policy creation, approval policy creation, auth policy, broker adapter implementation or interface definition, durable database schema ownership, UI/dashboard rendering, websocket management, shared Trading order/position contracts, or bypassing reconciliation. Unless later assigned by governance decision, Live consumes rather than owns the live action policy matrix.

### Public Capabilities

- Report live readiness and live gate decisions.
- Package live-compatible Trading requests when live mutation is disabled.
- Submit approved live execution requests only when live mutation is explicitly enabled and every live gate passes.
- Record receipts, reconciliation evidence, side-effect state, incidents, and audit references.
- Provide a public tool contract table before Builder handoff, including tool name, schema, approval requirement, side-effect class, risk level, error/warning codes, `retry_after_seconds`, idempotency behavior, and stability.
- Define shared Live terminology and enumerations for side-effect modes and retry-safety classifications before exported tools are implemented.

### Functional Requirements

- Live mutations default disabled and package-only mode must not call broker adapters.
- Broker submission requires auth, authorization, request validation, approval validation, risk decision validation, broker readiness, stale-context validation, idempotency validation, reconciliation authority validation, kill-switch validation, audit pre-recording, broker adapter permission, and explicit live flag.
- Every live result must identify side-effect mode: no side effect, packaged only, broker mutation attempted, broker mutation confirmed, broker mutation rejected, unknown outcome, or incident.
- Live must propagate, log, and persist request, correlation, approval, risk, idempotency, broker, route, account, strategy, symbol, and audit metadata across every live boundary.
- Unknown broker results block blind retry until reconciliation resolves broker truth.
- Broker rate-limit responses must expose retry safety and `retry_after_seconds` when applicable and must not be retried blindly.
- Approval context must include approved action scope, account scope, strategy/symbol scope where applicable, risk decision reference where applicable, approver reference, timestamps, state, and audit metadata.
- Audit-write failure before broker mutation always blocks broker mutation.
- Malformed broker success responses must be classified as unknown outcomes and trigger reconciliation.
- Production live broker mutation remains blocked until live execution schema, idempotency storage, reconciliation persistence, approval quorum, kill-switch policy, broker adapter contracts, live action policy matrix, concrete NFR targets, concurrency coordination, mandatory broker communication security profile, and operational thresholds are approved.

### Non-Functional Requirements

Live must fail closed on uncertainty, preserve deterministic redacted errors, remain import-time safe, avoid overclaiming readiness, coordinate conflicting account/order/position actions, enforce approved broker communication security before production mutation, expose bounded monitoring for stale state, rate limits, timeouts, incidents, latency, queue pressure, cost budget failures, and health, and keep numeric performance targets proposed/pending until owner approval.

### Edge Cases

Broker disconnected, stale account snapshot, reconciliation mismatch, provider timeout after possible acceptance, broker rate limit, malformed broker success response, broker API version skew, partial network partition, partial fill, duplicate idempotency material, disabled live flag, active or racing kill switch, approval expiry during execution, audit/idempotency persistence failure, runtime restart with unknown outcome, concurrent submit/cancel, shadow workflow receiving live references, clock drift beyond approved thresholds, config parse errors containing secret-like text, and secret-reference failure.

### Tests Required

Public tool contract tests, standard-envelope snapshots, gate-order tests, diagnostic-only gate tests, policy-matrix consistency tests, package-only no-broker-call tests, mutation-enabled mocked adapter tests, broker adapter contract tests, broker rate-limit/backoff tests, broker communication security gate tests, approval-context tests, disabled-live tests, reconciliation tests, idempotency tests, unknown-result tests, chaos/network-partition tests, import-time safety tests, concurrency tests, restart/recovery tests, timeout/backpressure tests with approved targets, usage-example tests, traceability tests, and secret-redaction tests.

### Notes / Future Improvements

Whether first release includes live execution is pending. Detailed supporting Live handoff requirements live in `docs/source-requirements/10_live.md`, subordinate to this active module summary. Production handoff is blocked until the owner approves the exact live execution schema, idempotency store, reconciliation persistence, approval action matrix/quorum, kill-switch policy, broker adapter contracts, stale thresholds, timeout limits, rate-limit behavior, queue/concurrency behavior, audit durability, mandatory broker communication security profile, concrete NFR targets, and restart/recovery objectives.

## UI / API Gateway

### Purpose

Expose a unified, secure UI/API entry point for approved project surfaces. The UI/API Gateway handles authentication, contract validation, delegation to backend services, response translation, and the frontend application without embedding domain logic.

### Owns

FastAPI routes, authentication enforcement, authorization checks, request/response contracts, stream contracts, error mapping, route-level contract documentation, frontend/API drift detection, frontend screens, clients, stores, validators, user interaction, and guarded-write preflight as a user-experience safeguard.

### Does Not Own

Trading/risk algorithms, simulation or optimization algorithms, research algorithms, broker calls, persistence business rules, complex orchestration beyond approved serial delegation, direct database writes from UI, direct broker calls from UI, or lifecycle ownership of domain services it calls. Route handlers may validate, authorize, delegate to approved service clients, and translate DTOs, but must not implement domain algorithms inline.

### Public Capabilities

- Health/readiness and protected dashboards.
- Data, indicator, strategy, risk, trading, simulation, optimization, live-readiness, analytics, research, conversation, and notification endpoints.
- Frontend views for approved workflows.
- Public HTTP, WebSocket/SSE, frontend client, and official callable capabilities classified as public, protected, internal, migration-only, experimental, deprecated, or optional/deferred.
- Route contracts covering auth, roles/permissions, schemas, status codes, error envelopes, side effects, idempotency, audit, rate limits, observability fields, and owning services before production handoff.
- Route group contract tables for health, auth, settings, AI chat, strategy/SQX, backtest/simulator, risk, live, optimization, dashboard/data/docs, Edge Lab/research, operator, and streams before Builder handoff.

### Functional Requirements

- Protected endpoints require authenticated user or service account.
- Mutations require role/action checks.
- Governed and financial endpoints require safety gates and audit.
- Responses use standard envelopes unless streaming has a documented approved event format.
- Domain-facing route handlers validate and authorize requests, delegate calculations and workflow execution to approved owning services, and return boundary DTOs.
- List endpoints require documented pagination, filtering, sorting, default limit, maximum limit, and empty-result behavior before production handoff.
- Streaming endpoints require documented auth, event schemas, heartbeat, reconnect, disconnect cleanup, backpressure, terminal-error behavior, and maximum connection policy before production handoff.
- Governed and financial mutations require request/trace metadata, actor identity, permission, approval context where applicable, audit event type, and idempotency behavior.
- Operator event streams require operator auth and role authorization unless a separate redacted public health-only stream is explicitly approved.
- A public health-only stream may expose only static service name, coarse health state, heartbeat timestamp, and public schema version after owner/security approval.
- Default pre-handoff baseline proposals include `v0-draft` API versioning, cursor pagination with default limit 50 and max 200, 30-second stale warning for governed context, 30-second endpoint timeout unless documented otherwise, and fail-closed idempotency storage behavior for governed mutations.
- `/api/dashboard/currency-strength` remains optional/deferred until its schema, source service, stale-data behavior, and frontend contract are finalized.

### Non-Functional Requirements

API/UI must prevent contract drift, redact errors, avoid embedding backend business logic in frontend code, preserve secret-safe observability across backend logs and frontend telemetry, and approve measurable pre-handoff baselines for p95 latency, request/response sizes, rate limits, stream heartbeat and connection limits, and accessibility.

### Edge Cases

Unauthenticated access, admin deactivation after token issue, permission change mid-workflow, rate limit, streaming disconnect/reconnect/backpressure, malformed payload, non-JSON upstream response, stale frontend contract, direct mutation attempt, duplicate or missing idempotency key, idempotency storage unavailable, CSRF failure, oversized payload, localStorage unavailability, CORS denial, partial backend dependency failure, path traversal, missing service-client registration, missing orchestrator abstraction for complex workflows, and deferred currency-strength behavior.

### Tests Required

Contract definition tests, API contract tests, route metadata tests, auth/authz tests, response envelope tests, stream contract tests, operator event stream security tests, idempotency tests, CSRF tests, rate-limit tests, path-safety tests, redaction tests, frontend DTO/validator drift tests, frontend integration tests, protected-route tests, accessibility/responsive tests, and requirement-to-test traceability tests.

### Notes / Future Improvements

Detailed supporting UI/API handoff requirements live in `docs/source-requirements/11_ui_api.md`, subordinate to this active module summary. Production handoff is blocked until route contracts, standard response and error envelopes, stream event envelopes, versioning, pagination/filtering/sorting policy, service-client delegation protocol, operator event stream auth, measurable NFRs, governed mutation idempotency/audit/CSRF behavior, usage examples, and requirement-to-test traceability are approved. Automatic contract documentation generation may remain future work only if manual contracts are complete.

## Research

### Purpose

Provide sandboxed market research, edge discovery, feature engineering, statistical validation, market-structure analysis, unsupervised insight generation, evidence packaging, and AI-assisted analysis using lower modules without bypassing safety gates. Research outputs are advisory evidence only and cannot authorize execution, risk approval, live signal control, or strategy promotion by themselves.

### Owns

Research runs, artifacts, hypotheses, evidence references, research reports, sandbox boundaries, research-ready data preparation contracts, feature/leakage helpers, null-model and edge-discovery contracts, market-structure research profiles, unsupervised research results, seasonality analysis, standard research envelopes for external helper tools, and lazy public export metadata.

### Does Not Own

Live state mutation, execution approval, direct broker actions, portfolio risk enforcement, final trade approval, production signal execution, backtest engine ownership, production optimization orchestration, analytics module ownership for reused analytics ratios, broad market-data provider ownership, secrets, AI provider governance, or durable roadmap/product decisions.

### Public Capabilities

- Analyze research-ready market data, indicators, features, edge evidence, null models, market structure, and unsupervised regimes.
- Draft hypotheses and evidence-backed artifacts.
- Generate advisory research reports, scorecards, profile snapshots, and evidence packs.
- Expose public research capabilities only after each export is classified as stable public API, internal-support contract, compatibility re-export, experimental capability, or network-backed helper.
- Document per-capability contracts covering input type, required fields, output type, errors, side effects, determinism, dependency behavior, network/disk behavior, and stability before Builder handoff.
- Mark optional external-provider exports in the lazy registry and define deterministic provider-unavailable behavior without breaking `tools.research` imports.
- Keep `internal-support` and `compatibility-re-export` items out of stable agent-facing catalogs unless explicitly promoted through versioned contracts.

### Functional Requirements

- Research artifacts must reference source data and assumptions.
- Research cannot mutate live state.
- AI-assisted research must be bounded and auditable.
- Data preparation, feature, leakage, edge-discovery, null-model, market-structure, unsupervised, network-helper, and reporting functions must define input/output schemas, mutation behavior, warning/error behavior, and acceptance criteria.
- Public model contracts must define schema versions and examples for `PreparedDataset`, `DataQualityReportModel`, `EdgeResult`, `CoreMetricProfile`, `MarketStructureProfile`, `UnsupervisedResearchResult`, `UnsupervisedInsightReport`, and report payloads.
- The standard research envelope must define versioned `status`, `data`, `errors`, `warnings`, `audit`, `side_effect`, `approval_required`, `dry_run`, `environment`, `risk_level`, and `timing` fields before network-backed or agent-facing tools are implemented.
- Each public callable must choose a single documented failure pattern: typed exception, structured result with warnings/errors, or standard research envelope.
- Each public callable in the approved slice must have a behavior/error table with exact outcomes and codes for invalid input, insufficient data, unsupported config, provider unavailable, rate limit, serialization failure, resource limit, and permission failure.
- `CleaningConfig` must define approved missing-bar and non-trading-period strategies before data-preparation implementation.
- `CleaningConfig` defaults must be approved; Builders may not infer a missing-bar default or silently fill/drop bars.
- Non-deterministic bootstrap, permutation, null-model, clustering, and unsupervised workflows must accept or source a seed and record the effective seed in outputs.
- Report persistence helpers must define overwrite parameters and atomic-write behavior.
- Persisted artifacts must include SHA-256 hashes of canonical data/source identity and effective configuration.
- Advisory signal adaptation, news blackout windows, and strategy-fit outputs must not mutate runtime controls, block live entries, approve promotion, or authorize execution.
- Re-exported analytics functions must preserve upstream analytics contracts and have compatibility tests.
- Duplicate or overlapping APIs such as `forward_returns`/`compute_forward_returns`, `atr`/`calculate_atr`, `adr`/`calculate_adr`, and session/regime helper variants must be clarified before implementation.

### Non-Functional Requirements

Research must be reproducible, import-time safe, redacted, bounded, traceable, clear about uncertainty, and explicit about advisory-only status. Persisted artifacts must include schema version, module version, config hash, dataset/source identity, generated-at timestamp, timezone, seed, dependency metadata, SHA-256 artifact/input/config hashes, warnings, and provenance. Network-backed helpers must be isolated, cache-aware, timeout/rate-limit/retry bounded, optional-provider classified, and skippable in offline tests. Resource limits must define maximum rows, runtime, memory, reference hardware, and limit-exceeded behavior before production-grade claims; proposed performance targets remain pending until owner approval.

### Edge Cases

Missing source data, hallucinated result risk, unapproved provider access, oversized artifact, attempt to bypass governance, malformed configuration, unsupported symbol/timeframe/date range, invalid OHLCV/OHLCVS data, duplicate/mixed timezone timestamps, clock drift, out-of-order merged-source timestamps, NaT timestamps, NaN/Infinity values, columns entirely NaN after cleaning, all-identical PCA/clustering features, too-small samples, non-finite null distributions, overlapping sessions, unstable calibration rankings, missing optional provider adapter, external provider timeout/rate-limit/layout change, HTTP 429 with invalid or missing `Retry-After`, path traversal, unwritable report paths, concurrent report writes, stale or corrupted cached feed data, missing masking rules, and incompatible artifact schema versions.

### Tests Required

Sandbox tests, artifact schema tests, source-reference tests, no-live-mutation tests, public export contract tests, standard-envelope tests for network helpers, model schema tests, behavior/error table tests, requirement-to-test traceability tests, data validation tests, cleaning strategy tests, feature and leakage tests, property-based or generated-case rolling-window tests, null-model seed tests, edge-discovery tests, market-structure tests, unsupervised modeling determinism tests, report golden and atomic-write tests, security/redaction tests, nested masking robustness tests, import-time safety tests, concurrency tests, performance/resource tests, provider failure and missing-adapter tests, observability tests, and executable success/failure usage-example tests.

### Notes / Future Improvements

Detailed supporting Research handoff requirements live in `docs/source-requirements/12_research.md`, subordinate to this active module summary. Research Builder handoff is blocked until public API overlaps are resolved, public API contracts, model schemas, canonical error behavior, standard research envelope schema/status/error enums, exact behavior/error tables, cleaning strategy defaults, seed propagation rules, SHA-256 reproducibility metadata, optional external-helper behavior, persistence rules, measurable resource limits, usage failure paths, advisory-only boundary wording, duplicate API clarifications, and requirement-to-test traceability are resolved or explicitly deferred.

## Conversation

### Purpose

Provide the governed AI chat layer for HaruQuantAI: durable chat threads, redacted messages, memory, retention, page-context assembly, prompt composition, provider streaming, CEO/planner routing, read-only tool evidence, and governed action drafts without allowing chat to execute broker-affecting actions.

### Owns

Chat threads, redacted messages, memory summaries, pinned facts, action drafts, provider routing, read-only tool plans, read-only evidence inclusion rules, evidence schema validation, page-context assembly, prompt-building contracts, retention metadata, lifecycle audit events, stream events, and conversation telemetry.

### Does Not Own

Direct execution of trades, live order mutation, broker reconciliation, execution receipts, risk approvals, portfolio risk decisions, kill-switch state, strategy signals, trading order intents, backtests, optimizations, research model ownership, read-only tool execution ownership, final permission authority, user authentication, identity provisioning, `user_id` validation, provider credentials, provider key lifecycle, authentication source-of-truth, persistent storage engine ownership, or final governance authorization.

### Public Capabilities

- Chat with the system.
- Summarize runs, docs, and system state.
- Draft governed action proposals.
- Use approved read-only or governed tool plans.
- Expose `ConversationService`, `CEOChatGateway`, context builders, prompt builders, stream clients, retention helpers, memory helpers, and title/summary helpers only through documented capability contracts.
- Keep `tools.conversation.__all__` allowed to be empty when no standardized conversation function tools are approved.

### Functional Requirements

- Threads must belong to the user.
- Messages must be redacted before persistence.
- Tool plans are read-only unless explicitly governed.
- Action drafts cannot execute directly.
- Regulated action drafts require retention and audit metadata.
- Before Builder handoff, every public conversation capability must document callable status, stability, intended consumers, input schema, output schema, error behavior, side effects, authorization expectations, idempotency behavior, risk level, network behavior, and persistence behavior.
- A capability contract table must classify `ConversationService`, `PromptBuilder`, `CEOChatGateway`, provider stream clients, and action draft operations with input schema, output schema, machine-readable error codes, side effects, authorization, and idempotency guarantees.
- `CEOChatGateway.stream_turn` must define stable event names, required payload fields, ordering guarantees, terminal event behavior, cancellation behavior, degraded-provider behavior, and error event behavior.
- `ConversationRepository` or a companion persistence specification must define operations, transactional boundaries, conflict signals, idempotency storage, locking/versioning behavior, partial-failure behavior, and machine-readable persistence error codes.
- Duplicate chat turn requests must be idempotent by `(user_id, thread_id, request_id)` and concurrent mutations must use approved serialization, optimistic version checks, or documented conflict events.
- Archived and deleted thread behavior must be explicitly defined for reads, writes, export, retention changes, action draft creation, restore, and lifecycle purge.
- Action draft payloads must be validated against versioned schemas before persistence and must remain proposal-only until external governance changes side-effect status.
- Read-only tool evidence requires explicit auth context, permission result from API/UI or an approved authorization service, provenance, freshness, retrieval timestamp, and read-only classification before prompt inclusion.
- Provider fallback must use a documented schema before any model token is emitted; partial-token failures, rate limits, stream cancellation, and backpressure require documented terminal or telemetry events.
- Conversation configuration must enumerate retention policy, prompt/context budgets, provider timeouts, stream buffer limits, active-stream memory limits, lifecycle batch limits, summary cadence, observability fields, and validation rules. Provisional baseline values may be documented for planning but are not production-approved until promoted by owner decision.

### Non-Functional Requirements

Conversation must not invent market data, backtest results, risk approvals, owner decisions, or provider behavior. It must remain import-time safe without provider credentials, network access, database access, optional provider SDKs, model availability, `.env` loading, migrations, background tasks, or provider registration side effects. Page context, tool evidence, memory, pinned facts, recent messages, prompt composition, streaming buffers, provider calls, and retention lifecycle decisions must have documented bounds, timeouts, retry/no-retry rules, deterministic clock behavior, redaction-before-log behavior, and redacted observability. Retention durations, prompt budgets, provider timeouts, stream buffer limits, active-stream memory limits, and lifecycle limits must be injected through configuration, not hardcoded. Concrete NFR targets remain pending owner approval.

### Edge Cases

Secret in prompt, user asks for live trade, stale context, provider unavailable, provider HTTP 429/rate limiting, partial-token provider failure, stream cancellation, backpressure, malformed request ID, clock skew between application and database, database connection pool exhaustion or SQLite busy/locked response, tool-plan permission mismatch, unauthorized or adversarial tool evidence, cross-user export, concurrent `stream_turn` calls, duplicate request IDs across same or different threads, lifecycle/archive/purge races, repository partial write failures, action draft pending when kill switch activates, and retention/legal-hold ambiguity.

### Tests Required

AI safety tests, redaction tests, retention tests, action-draft separation tests, permission tests, provider-unavailable tests, public capability contract tests, stream event contract tests, repository contract and failure-path tests, empty `__all__` tool-discovery tests, configured retention/prompt-limit tests, configuration-injection/no-hardcoded-limit tests, property-based redaction tests, provider rate-limit and mid-stream degradation chaos tests, cross-user security tests, prompt-injection tests, read-only evidence provenance tests, concurrency/idempotency tests, performance/boundedness tests, observability tests, import-time safety tests, and usage-example tests for archived-thread errors, provider-disabled fallback, stream cancellation/backpressure, and action-draft validation failure.

### Notes / Future Improvements

Detailed supporting Conversation handoff requirements live in `docs/source-requirements/13_conversation.md`, subordinate to this active module summary. Production handoff is blocked until public capability contracts, machine-readable error codes, stream event schemas, fallback response schema, repository/persistence contracts, production retention policy, configuration reference values, read-only tool permission authority, auth context flow, concurrency/idempotency behavior, measurable NFR targets, focused tests, and requirement-to-test traceability are resolved or explicitly deferred from release scope.


## Current Assumptions

- Launch-critical integrations are MT5 and SQLite.
- Launch notification channels are email and Telegram.
- Backend canonical entry point is `api.main:app`.
- SQLite is acceptable as a bootstrap/local launch store until concurrency and production targets are decided.
- Event bus can start in memory for early Utils work but must become durable before critical financial workflows rely on replay or audit.
- The first build sprint should focus on Utils/Foundation.
- Existing implementation code is not automatically authoritative until the owner decides whether it is reference-only, partially adopted, or authoritative for a sprint.
- Email, Telegram, and desktop notification routing are planned Utils capabilities; provider credentials and channel enablement remain explicit environment configuration.
- Prometheus/Grafana-compatible observability is planned through Utils primitives; exact dashboard definitions remain pending until implementation scope is approved.
- Detailed Utils implementation checklists live in `docs/PROJECT.md` and Sprint 001 execution tracking lives in `docs/ROADMAP.md`; product assumptions remain here.

## Open Questions

### Blocking

- What does "all 13 modules work" mean for the first product milestone: skeleton, happy-path MVP, or production-ready workflows?
- What are the first-release instruments, symbols, timeframes, and broker account types?
- Which actions may directly mutate durable state, and which must only package governed requests?
- What new product behaviors beyond the 13-module architecture are required first?
- Is the first release research/backtest only, paper trading, live-preparation, or controlled live execution?
- What is the minimum accepted API/data model contract for Sprint 001 and Sprint 002?
- Should existing implementation code be treated as reference-only, partially adopted, or authoritative for Sprint 001?

### Important But Not Blocking

- Which AI provider should Conversation use first?
- What are the exact simulation and optimization result fields required by UI/API?
- What numeric risk thresholds should be used for initial paper/live gates?
- What production retention policy applies to chat, audit, simulation, execution, and regulated artifacts?
- What deployment target is first: local workstation, VPS, container, cloud, or hybrid?
- Should the event bus start in-memory, SQLite-backed, or external?
- Should catalog generation be mandatory in CI from Sprint 001?
- Should desktop notifications be launch-critical or only a local/operator convenience?
- Which Utils capabilities, if any, may be attached directly to agents beyond read-only validation and approved redaction?

### Later Decisions

- Exact `/api/dashboard/currency-strength` endpoint schema.
- Providers after MT5.
- Whether SQLite remains acceptable for multi-user production.
- Whether Docker/Compose is required before first deploy.
- Whether optimization starts with grid/random only or includes Bayesian/genetic early.

## Source And Reference Notes

- Durable project truth is now the active docs set under `docs/`, with AI/Builder instructions centralized in root `AGENTS.md`.
- Historical planning files, sprint packs, prompt libraries, and durable docs were consolidated into this lean structure in the documentation refactor.
- Uploaded HaruQuant service-tool requirements and existing repository material remain reference sources only unless a decision in `docs/ROADMAP.md` promotes specific behavior.
- Chat is not durable memory unless its decision, risk, question, or requirement is recorded in the active docs.
