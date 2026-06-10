# HaruQuantAI Architecture

Purpose: this file records the system design, stack, runtime model, folder structure, data models, API/interface contracts, validation, error handling, security, observability, testing, deployment, and dependency rules.

## System Overview

HaruQuantAI is a modular monolith by default, with service-oriented module boundaries. Lower modules provide shared infrastructure, normalized data, and durable state. Middle modules produce indicators, signals, risk decisions, analytics, simulations, and deterministic order intents. Higher modules expose API, UI, research, live runtime, and conversation workflows.

The architecture must keep research, simulation, paper trading, and live trading aligned while blocking any path that bypasses auth, authorization, risk, idempotency, reconciliation, audit, or kill-switch controls.

## Tech Stack

| Area | Baseline |
|---|---|
| Backend | Python 3.9+, FastAPI, Pydantic, Uvicorn |
| Frontend | Next.js, React, TypeScript, Tailwind CSS, Radix UI |
| Persistence | SQLite launch baseline, SQL migrations under `data/database/migrations/` |
| Data/science | pandas, numpy, scipy, scikit-learn, numba, pyarrow/fastparquet where approved |
| Charts/reporting | Plotly, Bokeh, and UI chart libraries where approved |
| Broker/data launch integration | MetaTrader5 |
| AI/agents | Provider abstractions; configured AI providers cannot bypass governance |
| Testing | pytest, pytest-cov, selected Node/UI contract tests |
| Quality | black, isort, flake8, mypy, pylint, bandit, pre-commit, ESLint where configured |
| Dependency management | Python: `pyproject.toml`, `requirements.txt`, `uv.lock`; UI: npm workspace and lockfile |

## Runtime Model

- Backend canonical entry point: `api.main:app`.
- Frontend workspace: `ui/`.
- SQLite provides local durable persistence for launch.
- Scheduler/background jobs may start inside the backend process until a worker/deployment decision changes this.
- Event bus may start simple but must become durable before critical live trading paths rely on replay or audit.
- Live mutations remain disabled unless explicitly enabled by configuration and governance.

Runtime modes:

| Mode | Purpose | Side-effect policy |
|---|---|---|
| Research | Explore data, features, strategies, and hypotheses. | No live broker mutation. |
| Simulation | Backtest over historical data through the trading path. | Simulated side effects only. |
| Paper | Exercise execution path without real capital. | Demo/paper side effects only. |
| Live | Real broker execution. | Disabled by default; requires full safety gates. |

Expected future commands must not be claimed working unless verified:

```text
uvicorn api.main:app --reload
npm --prefix ui run dev
python scripts/tools/initialize_database.py
pytest
ruff check .
mypy .
```

## Folder Structure

| Path | Responsibility |
|---|---|
| `api/` | FastAPI apps, routes, middleware, auth, websocket/session services, API composition. |
| `tools/` | Core domain modules and utilities. |
| `agentic/` | Agent runtime, permissions, safety, workflow schemas, provider configuration. |
| `data/` | SQLite repositories, migrations, cache/state/log directories, market data, research data, saved strategies. |
| `ui/` | Next.js frontend workspace, app routes, components, clients, stores, types, validators. |
| `tests/` | Python unit, integration, usage, and contract tests. |
| `scripts/` | Operational tools, database initialization, docs validation, migrations/helpers, examples. |
| `docs/` | Five active project documents. |
| `.github/` | CI workflows. |

Generated logs, caches, databases, virtual environments, screenshots, and local artifacts are not source of truth unless explicitly curated.

## Module Boundaries

Dependencies should flow downward or through explicit contracts:

```text
Conversation / Research / UI
        |
API Gateway / Auth / Tool Access Control
        |
Optimization / Simulation / Analytics
        |
Trading / Risk / Strategy / Indicator
        |
Data / Broker Adapters / State Persistence
        |
Utils: settings, logging, event bus, security, notifications, observability
```

Core boundary rules:

- UI and Conversation must not own trading, risk, broker, or persistence business logic.
- Strategy must emit signals, not broker orders.
- Risk must evaluate before Trading creates financial order intents.
- Live must not submit to a broker unless auth, authorization, risk, idempotency, broker readiness, reconciliation, audit, and live-enable checks pass.
- Providers are adapters; HaruQuantAI owns internal schemas.

## Utils Foundation Architecture

The Utils module is the first build foundation. It supplies shared contracts and primitives used by all higher modules, but it must not become an application orchestration layer.

### Target Files

Planned Utils implementation files:

```text
tools/
  __init__.py
  utils/
    __init__.py
    logger.py
    standard.py
    errors.py
    identity.py
    normalization.py
    paths.py
    dataframe_tools.py
    data_quality.py
    schema_validation.py
    security.py
    settings.py
    auth.py
    event_bus.py
    error_routing.py
    notifications.py
    observability.py
```

Planned fast tests and usage examples:

```text
tests/unit/tools/utils/
tests/usage/tools/utils/
```

The final file list for Sprint 001 may be narrowed by the approved sprint plan.

Detailed tickable Utils implementation requirements live in `docs/PROJECT.md`; Sprint priority, Definition of Done, and CI gate checklists live in `docs/ROADMAP.md`.

### Public Registry Contract

- `tools/utils/__init__.py` owns the public utility registry.
- Public names must be intentional and listed in `__all__`.
- Public exports are classified as official AI tools or support helpers.
- Official AI tools return standard envelopes.
- Support helpers may return native values or raise typed exceptions.
- Sensitive helpers such as settings loading, encryption, and decryption are not agent-callable by default.
- No compatibility aliases, duplicate wrapper modules, fallback import paths, or accidental exports should be added.

### Tool Response Contract

Official AI tools must return:

```text
status
message
data
error
metadata
```

Metadata for official tools must include:

```text
tool_name
tool_version
tool_category
tool_risk_level
request_id
execution_ms
read_only
writes_file
modifies_database
places_trade
requires_network
```

Execution timing must use monotonic timers and report milliseconds consistently.

### Logging Contract

- Logging configuration must be explicit and avoid duplicate handlers.
- Production logs should be structured and JSON-compatible.
- Local development may use human-readable console logs.
- Importing logger utilities must not configure application-level logging.
- File logging is opt-in, path-safe, rotating, and retention-limited.
- Logs must include request/workflow/correlation/error context where available.
- Logs must not contain secrets, credentials, raw private payloads, full approval packets, notification credentials, authorization headers, or Telegram bot tokens.

### Time And Identity Contract

- Wall-clock timestamps are UTC-aware.
- Naive datetimes require an explicit assumed timezone.
- Durations use monotonic timers.
- Request, workflow, correlation, causation, event, and idempotency IDs must be string-safe and traceable.
- IDs must not include secrets or raw user-provided text.

### Auth Context Contract

Utils may define auth context primitives and deny-by-default authorization helpers. External identity-provider token validation belongs to application or infrastructure adapters unless explicitly approved.

Auth context should support:

```text
principal_id
principal_type
roles
permissions
scopes
tenant_or_environment
request_id
workflow_id
correlation_id
```

Auth context must be redacted before logging, events, metrics, errors, or audit output.

### Event Bus Contract

Utils owns the in-process event bus contract and early implementation. Production broker-backed adapters may be added later behind explicit adapter boundaries.

Event bus requirements:

- Event envelope fields must include event ID, type, schema version, source, timestamps, trace IDs, payload, and audit level.
- Delivery should be deterministic per event type for the in-process implementation.
- Distributed broker adapters are not assumed to preserve the same ordering without documented guarantees.
- Idempotency storage must be bounded by TTL and maximum cache size.
- Queue-full behavior must return deterministic `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` diagnostics.
- Retry, dead-letter, dropped-event metrics, and backpressure behavior must be observable.
- Shared state must be thread-safe or async-safe where applicable.

### Notification Contract

Utils owns notification routing contracts and adapter boundaries, not hard-coded provider credentials.

- Email, Telegram, and desktop routes must be explicitly configured.
- Disabled/missing channels must fail with structured diagnostics.
- Notifications must be redacted, throttled, deduplicated, observable, and protected by circuit breakers for external providers.
- Templates should support markdown and plain-text fallback.
- Templates render from sanitized DTOs, not raw event payloads.

### Observability Contract

Utils should provide metric registration and no-op behavior when Prometheus/exporter dependencies are unavailable.

Metric and health coverage should include:

- Tool calls and latency.
- Errors and validation failures.
- Event bus publish/delivery/retry/dead-letter/backpressure.
- Queue depth and idempotency cache size.
- Notification routing and failures.
- Auth failures.
- Circuit-breaker state.
- Clock-drift state.
- Health states: healthy, degraded, critical, unsupported, not configured.

Metric labels must avoid high cardinality and sensitive values. Grafana dashboard expectations belong in docs or version-controlled dashboard definitions once approved.

### Settings Contract

Runtime settings must load deterministically and support injection for tests. Importing settings utilities must not read `.env`, mutate environment variables, or contact providers.

Settings diagnostics must redact sensitive values.

### Utils Quality Gates

Expected Utils quality commands once the implementation exists:

```text
black tools tests
isort tools tests
flake8 tools tests
mypy tools tests
pytest tests/unit/tools/utils tests/usage/tools/utils --cov=tools.utils --cov-fail-under=80
```

These commands are planned gates, not verified current commands.

## Data Models And Schemas

Common conventions:

- Durable cross-module IDs should be `TEXT`; local legacy rows may use integer IDs.
- UTC timestamps should include `created_at` and, where mutable, `updated_at`.
- JSON fields should use a `*_json` suffix and be validated where possible.
- Booleans in SQLite should be constrained to `0` or `1`.
- Broker-critical price/size precision must not rely casually on floating point.
- Cross-module actions should carry `request_id`, `correlation_id`, and where applicable `workflow_id`.
- Financial side-effect paths must store or deterministically derive idempotency material.
- Secrets must not be stored as plain fields.

Logical namespaces use table prefixes such as `core_`, `risk_`, `gov_`, `audit_`, `research_`, `ref_`, `ai_chat_`, and `agent_`.

Important entities:

- User, session, service account.
- Workflow, workflow step, workflow transition.
- Trade hypothesis, trade proposal.
- Risk assessment request, risk decision, risk constraint.
- Execution intent, send attempt, receipt.
- Reconciliation run, broker position.
- Strategy, strategy version, strategy lifecycle.
- Market data bar/tick.
- Indicator definition/result.
- Portfolio state/position.
- Simulation run, optimization run/result.
- Analytics result.
- Notification.
- Approval, policy, compliance profile.
- Chat thread/message/action draft.
- Agent task/tool call/decision/evidence ref.
- Audit log.

Schema rules:

- Use migrations for durable schema changes.
- Prefer additive migrations.
- Do not edit applied migrations without an approved reset/rebaseline.
- Preserve idempotency, audit, and reconciliation history.
- Keep docs, migrations, repositories, API schemas, and tests synchronized.

## API And Interface Contracts

API Gateway owns authentication, authorization, validation, response envelopes, error mapping, and access to module services.

Standard response envelope:

```json
{
  "status": "success",
  "message": "Operation completed.",
  "data": {},
  "error": null,
  "metadata": {
    "request_id": "req_...",
    "correlation_id": "corr_...",
    "api_version": "v0-draft",
    "module": "risk",
    "operation": "evaluate_proposal",
    "risk_level": "governed",
    "side_effects": "none",
    "execution_time_ms": 42,
    "created_at": "2026-06-04T00:00:00Z"
  }
}
```

Minimum event envelope:

- `event_id`
- `event_type`
- `schema_version`
- `source_module`
- `timestamp`
- `request_id`
- `correlation_id`
- `causation_id`
- `payload_json`
- `audit_level`

Endpoint groups are draft until reconciled with implementation: health, auth, settings, catalog/docs, data, indicator, strategy, risk, portfolio, trading, simulation, optimization, live, analytics, research, conversation, notifications.

`/api/dashboard/currency-strength` is deferred and should not block early sprints.

## Validation Approach

- Validate before side effects.
- Fail closed when validation context is incomplete for risk, live, security, or governed actions.
- Return structured, redacted errors at service/API boundaries.
- Preserve request/correlation IDs in validation failures.
- Bound diagnostic payloads.
- Reject unknown fields for sensitive mutations unless explicitly documented.
- Never coerce security-sensitive values in surprising ways.

Examples of validation requirements:

- Market data must have valid timestamp, OHLC geometry, finite values, provider/source consistency, and stage-appropriate quality checks.
- Risk requests need proposal, strategy, symbol, side, requested volume, policy context, portfolio state, and live broker/account state when applicable.
- Order intents require approved/reduced risk decision or simulation context, deterministic idempotency material, valid side/order/price/size, and live volume within approved limits.
- Conversation messages must be redacted before persistence; action drafts cannot execute directly.

## Error Handling Approach

Errors must be structured, redacted, and traceable. Error categories include invalid input, auth/authz failure, governance/risk block, data quality failure, idempotency conflict, provider/network failure, dependency unavailable, persistence failure, configuration failure, and internal error.

Retry rules:

- Retry only known safe transient failures.
- Do not blindly retry unknown broker results; reconcile first.
- Idempotent retry must preserve material fields.
- Auth, risk, governance, validation, and idempotency conflicts are not retried automatically.

Fail-closed conditions include missing auth, missing approval, missing broker state, stale price, reconciliation mismatch, idempotency conflict, invalid strategy state, active kill switch, or disabled live mutations.

## Security Rules

- Never commit real secrets.
- `.env.example` may contain placeholders only.
- Real `.env` files, credentials, local databases, logs, generated reports, and private artifacts must stay out of source control.
- API keys, broker credentials, Telegram tokens, email passwords, signing keys, database passwords, and AI provider keys are secrets.
- Load secrets from environment variables or approved secret storage.
- Redact sensitive values in logs, errors, docs, tests, chat output, notifications, and telemetry.
- Protected API/tool access requires authentication.
- Governed actions require role/action authorization.
- AI tools may draft or explain but must not execute governed actions directly.

## Testing Strategy

Test coverage scales with risk:

- Sprint 000/docs: documentation presence and consistency.
- Utils: settings, logging, time, security, events, notifications, observability.
- Data: SQLite, MT5 adapter boundary, normalization, persistence.
- Indicator: deterministic indicator fixtures.
- Strategy: signal contract and lifecycle.
- Risk: fail-closed policy and sizing.
- Trading: order intent and idempotency.
- Simulation: determinism and replay.
- Live: safety-gated integration only.
- UI/API: API contract, auth, frontend integration.
- Research: sandbox and artifact tests.
- Conversation: AI safety, retention, redaction, action drafts.

Do not write tests for invented behavior. Do not weaken tests to pass code. Do not claim tests passed unless run.

## Observability, Metrics, And Audit Trail

Every cross-module request should carry request/correlation IDs. Safety-critical flows need logs, metrics, audit events, and alert routes.

Minimum observability areas:

- Structured logs with redaction.
- Health and readiness checks.
- Metrics for requests, errors, latency, event bus behavior, provider status, notifications, risk blocks, simulation/optimization runs, and live-readiness gates.
- Audit records for governed actions, risk decisions, execution attempts, reconciliation, kill switch, approvals, and AI action drafts.
- Email/Telegram notifications for approved operational and safety events, with rate limits and redaction.

## Deployment And Environment Notes

Deployment target is pending. Local development is the baseline until owner decisions define staging and production topology.

Expected configuration areas:

- Application/API.
- SQLite paths.
- MT5.
- Email.
- Telegram.
- Observability.
- Event bus.
- Security/signing.
- AI provider.

Known configuration keys from the previous documentation baseline:

| Area | Keys |
|---|---|
| Application | `APP_NAME`, `ENVIRONMENT`, `API_HOST`, `API_PORT`, `UI_ORIGIN` |
| Persistence | `DATABASE_URL`, `DATA_DIR`, `ARTIFACT_DIR`, `DATA_CACHE_PATH` |
| Safety | `ALLOW_LIVE_MUTATIONS`, `PROFILE` |
| Observability | `LOG_LEVEL`, `LOG_RENDER`, `EVENT_BUS_BACKEND`, `METRICS_ENABLED`, `METRICS_PORT` |
| MT5 | `MT5_ENABLED`, `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`, `MT5_TERMINAL_PATH` |
| Email | `NOTIFICATION_EMAIL_ENABLED` and SMTP host/port/user/password/from/to settings |
| Telegram | `NOTIFICATION_TELEGRAM_ENABLED`, `NOTIFICATION_TELEGRAM_BOT_TOKEN`, `NOTIFICATION_TELEGRAM_CHAT_IDS` |
| Conversation AI | `HARUQUANTAI_CHAT_ENABLED`, provider, model, API key, and base URL settings |

Default live safety:

```text
ALLOW_LIVE_MUTATIONS=false
```

Release readiness requires environment variables, migrations, rollback plan, monitoring checks, secret handling, auth, and live safety controls to be complete for the selected environment.

## Dependency Rules

- Do not add dependencies without documented approval.
- Document purpose, owning module, runtime/dev scope, required/optional status, security considerations, and failure behavior.
- Prefer standard library and approved dependencies.
- Optional dependencies must degrade gracefully.
- Heavy compute, broker, AI, notification, cloud, and database dependencies require explicit documentation.
- Update the relevant manifest and lockfile together when dependencies change.

## Pending Architecture Decisions

- Event bus durability phases.
- Exact API schema/versioning format.
- Deployment topology.
- SQLite migration path.
- AI provider interface details.
- Risk threshold signing and approval process.
- Worker/job execution model for heavy simulation and optimization.
- Final identity provider.
- Retention windows for chat, audit, market data, and regulated execution artifacts.
