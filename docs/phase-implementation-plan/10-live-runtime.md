## Phase 10 Live Runtime

### Goal

Implement the Live Runtime requirements under `app/services/live/` while preserving the phase module boundaries and governance rules.

Task inventory: 234 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

Required files:

```text

app/utils/__init__.py

app/utils/errors.py

app/services/trader/__init__.py

app/services/risk/__init__.py

app/services/risk/kill_switch.py

app/services/optimization/__init__.py

```

Required functionality:

- Unified trader service directs orders to live broker targets.
- Global kill switch blocks orders when triggered.
- MT5 and cTrader live execution connections are authenticated.

### Files to Create

```text

app/services/live/

app/services/live/__init__.py

app/utils/settings.py

app/services/live/session.py

app/services/live/gates.py

app/services/live/executor.py

app/services/live/reconciliation.py

app/services/live/monitoring.py

app/utils/errors.py

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

#### `app/utils/settings.py`

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

#### `app/utils/errors.py`

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


### Hardening Amendments

#### Mandatory live-promotion ladder

Requirements:

- [ ] Enforce the live-promotion ladder: offline test, simulation, replay, read-only broker connection, paper trading, shadow trading, micro-live, and full-live.
- [ ] Require explicit operator approval before moving from read-only to paper, paper to shadow, shadow to micro-live, and micro-live to full-live.
- [ ] Implement read-only live mode where broker account, positions, orders, symbols, and market data can be inspected but no orders can be placed.
- [ ] Implement paper trading mode using live-like market data and canonical execution contracts without touching a real broker account.
- [ ] Implement shadow trading mode that records intended orders and compares them against market conditions without broker mutation.
- [ ] Implement micro-live controls with reduced size, strict daily loss limits, strict trade count limits, and enhanced monitoring.
- [ ] Require startup reconciliation, pre-trade reconciliation, periodic reconciliation, shutdown reconciliation, and operator-visible reconciliation status.
- [ ] Define emergency flatten policy, broker-disconnection behavior, stale-data behavior, news/session gate behavior, and daily-loss guard behavior.
- [ ] Add tests proving full-live cannot activate directly from simulation, optimization, UI/API, or conversation commands.

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

feat(live-runtime): implement live broker sessions and execution safety gates



- Build live execution executor to map order intents to broker actions

- Setup pre-execution safety gates (price stale, feed status, terminal connection)

- Implement continuous position/order reconciliation and database state synchronization

- Create active live monitoring checks, clock drift detectors, and fail-closed alerts

```

- [ ] Secrets redaction tests shall inject fake values such as `password: secret123` and prove no log line, error message, notification, metric, report, or chat response contains `secret123`.
