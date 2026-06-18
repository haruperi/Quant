# HaruQuantAI Architecture Specification

## 1. Vision & System Overview
- **Purpose**: Modular, AI-assisted quantitative trading platform. Clean-room rebuild prioritizing safe service-tool boundaries, governed trading, reproducible research, and strict kill-switch controls.
- **Architecture**: Modular monolith with service-oriented boundaries.
  - **Layer 1**: Conversation / Research / UI
  - **Layer 2**: API Gateway / Auth / Tool Access Control
  - **Layer 3**: Optimization / Simulation / Analytics
  - **Layer 4**: Trading / Risk / Strategy / Indicator
  - **Layer 5**: Data / Broker Adapters / State Persistence
  - **Layer 6**: Utils (settings, logging, event bus, security, observability)

## 2. Target Actors
`Owner/Admin`, `Operator`, `Researcher`, `Strategy Developer`, `Risk Manager`, `Compliance Approver`, `Read-only Viewer`, `Service Account`, `AI Agent` (bounded by tools/policy), `Broker Adapter` (external boundary, no internal risk authority).

## 3. Core Workflows
1. **Research → Strategy**: Load data → Explore hypothesis → Create versioned spec → Simulate → Review artifacts → Promote via governance.
2. **Signal → Paper Trade**: Data → Indicator → Strategy emits **signal** → Risk evaluates → Trading creates **order intent** → Paper execution records receipt → Analytics/audit consume.
3. **Signal → Live Trade**: Authenticated initiation → Strategy signal → Risk validates (state, thresholds, kill switch) → Trading creates idempotent order intent → Live checks readiness → Submits to broker *only if live mutations explicitly enabled* → Receipt/reconciliation/audit.
4. **Conversation Action Draft**: User prompt → AI drafts redacted action/explanation → Governance determines approval route → Backend executes *only* if separately approved and valid.

## 4. Runtime Model & Environments
- **Stack**: FastAPI/Pydantic/Uvicorn (Backend), Next.js/React/TS (Frontend), SQLite (Launch persistence), MetaTrader5 (Broker baseline).
- **Execution Modes**:
  - `Research`: No live broker mutation.
  - `Simulation`: Simulated side effects only.
  - `Paper`: Demo/paper side effects only.
  - `Live`: **Disabled by default**. Requires full safety gates, explicit approval, and reconciliation.
- **Key Config**: `ALLOW_LIVE_MUTATIONS=false` (default), `ENVIRONMENT`, `DATABASE_URL`, `LOG_LEVEL` (JSON prod, color local).

## 5. Folder Structure
`app/` (routes, core services, utilities), `agentic/` (runtime, policy, registry, contracts), `data/` (SQLite, migrations, cache), `ui/` (Next.js workspace), `tests/`, `scripts/`, `docs/`, `.github/`.

## 6. Non-Negotiable Business Rules
- **Build Order**: Utils → Data → Indicator → Strategy → Risk → Analytics → Trading → Simulation → Optimization → Live → UI/API → Research → Conversation.
- **Signal Boundary**: Strategies emit *signals*, **never** broker orders.
- **Risk Interception**: Risk intercepts all signals before trading/live execution.
- **Trading Boundary**: Trading creates deterministic *order intents* from approved risk decisions.
- **Fail-Closed**: Live trading fails closed by default. Missing/stale context blocks execution.
- **Conversation Boundary**: AI can draft/explain/plan, but **cannot** directly execute governed/broker actions.
- **Utils Foundation**: Shared foundation only. Must not own strategy, broker, portfolio, risk, or live trading logic.

## 7. Glossary (Key Terms)
- **Signal**: Strategy output expressing market intent (not an order).
- **Proposal**: Candidate trade action prepared for risk review.
- **Risk Decision**: Approval, reduction, rejection, or block based on policy.
- **Order Intent**: Internal deterministic order request after risk gating.
- **Execution Receipt**: Broker/paper/simulation result for an order intent.
- **Kill Switch**: Safety control that absolutely blocks trading actions.
- **Action Draft**: Conversation-created proposal requiring governance.

## 8. Module I/O Boundaries
| Module | Inputs | Outputs |
|---|---|---|
| **Data** | Provider feeds, broker reads, local files | Normalized bars/ticks, snapshots, state records |
| **Indicator** | Normalized data, definitions, params | Indicator result columns/values |
| **Strategy** | Data, indicators, params, lifecycle | Signals, strategy metadata |
| **Risk** | Proposals, portfolio/broker state, policies | Risk decisions, constraints, kill-switch state |
| **Analytics** | Trade logs, equity curves, returns, benchmark data | Canonical reports, portfolio reports, scorecard evaluations, dashboard payloads |
| **Trading** | Risk decisions, proposal material | Order intents, idempotency records |
| **Simulation** | Historical data, strategy, order intents | Simulated trades, equity curve, metrics |
| **Live** | Order intents, broker readiness, reconciliation | Execution attempts, receipts, live audit events |

### 8.1 Analytics Service Contracts
- **Read-only boundary**: Analytics is downstream evidence generation only. It must not write files, mutate databases, call brokers/networks, place trades, or approve risk/trading actions.
- **Public surface**: Official agent/API-safe Analytics tools are cataloged in `app.services.analytics.models.OFFICIAL_ANALYTICS_TOOL_CATALOG` and approved by `docs/adr/ADR-ANALYTICS-PUBLIC-SURFACE.md`.
- **Metric definitions**: Approved formulas, units, aliases, undefined-result behavior, and confidence labels are cataloged in `METRIC_DEFINITION_CATALOG`.
- **Schema compatibility**: Analytics report/result compatibility is governed by `SCHEMA_COMPATIBILITY_MATRIX`; current accepted schema is `1.3.1`.
- **Runtime limits**: Input, payload, dashboard truncation, statistical-iteration, runtime, and memory limits are approved in `docs/adr/ADR-ANALYTICS-LIMITS.md`.
- **Portfolio currency safety**: Multi-currency portfolio analytics fail closed unless validated FX conversion data is supplied.

### 8.2 Trading Service Contracts
- **Broker routing ownership**: Broker module selection is owned by `app.services.brokers.router`; `app.routes.brokers` is a compatibility wrapper and must not own adapter policy.
- **Execution boundary**: `app.services.trader.trade.Trade` is the current executor/orchestrator. Phase plans that mention a separate `executor.py` map to this existing service unless a future refactor is explicitly approved.
- **Traceability**: Normalized trade results carry `request_id`, `correlation_id`, and `trace_id` alongside fill details so downstream risk, analytics, and reconciliation flows can cite the same execution context.
- **Rate limiting and readiness**: Trading checks provider rate-limit health during readiness and consumes provider rate-limit capacity before outbound broker execution.
- **Known pending hardening**: Partial close volume support, cached netting/hedging compatibility enforcement, scheduled reconciliation, broker circuit breakers, high-fidelity simulator E2E tests, and canonical provider metadata separation remain open Phase 7 follow-up items.

## 9. Data Models & Schema Rules
- **IDs**: Durable cross-module IDs must be `TEXT` (UUID4/ULID).
- **Timestamps**: UTC `created_at` and `updated_at`.
- **Types**: JSON fields use `*_json` suffix. SQLite booleans constrained to `0`/`1`. No casual floats for price/size precision.
- **Traceability**: Cross-module actions must carry `request_id`, `correlation_id`, and `workflow_id`.
- **Idempotency**: Financial side-effect paths must store/derive idempotency material.
- **Namespaces**: Table prefixes required (`core_`, `risk_`, `gov_`, `audit_`, `research_`, `ref_`, `ai_chat_`, `agent_`).

## 10. Interface Contracts
**API Response Envelope** (Mandatory):
```json
{
  "status": "success" | "error",
  "message": "Human-readable summary",
  "data": {},
  "error": null | {"code": "ERR_CODE", "details": "..."},
  "metadata": {
    "request_id": "req_...", "correlation_id": "corr_...",
    "api_version": "v0-draft", "module": "risk", "operation": "evaluate",
    "risk_level": "governed", "side_effects": "none",
    "execution_time_ms": 42, "created_at": "2026-06-04T00:00:00Z"
  }
}
```
**Event Bus Envelope**: `event_id`, `event_type`, `schema_version`, `source_module`, `timestamp`, `request_id`, `correlation_id`, `causation_id`, `payload_json` (redacted), `audit_level`.

## 11. Implementation & Safety Standards
- **Validation**: Validate *before* side effects. Fail closed if context is incomplete for risk/live/security. Return structured, redacted errors. Reject unknown fields for sensitive mutations.
- **Error/Retry**: Retry *only* known safe transient failures. Do not blindly retry unknown broker results; reconcile first. Fail-closed on: missing auth/approval, stale price, reconciliation mismatch, idempotency conflict, active kill switch.
- **Security**: No committed secrets. Redact sensitive values in logs, errors, chat, and telemetry. Protected API/tool access requires auth. Governed actions require role/action authorization.
- **Testing**: Coverage scales with risk. Utils/Data/Indicator (deterministic) → Strategy/Risk/Trading (contracts & fail-closed) → Sim/Live (safety-gated) → UI/Conv (safety, redaction, drafts).
- **Observability**: Cross-module request/correlation IDs mandatory. Structured JSON logs. Health monitoring (readiness, DB, feed status, clock drift). Audit trails for token logs and action approvals.

### 11.1 Utility Standard Contracts
- **Public registry classification**: `app.utils.__all__` is the utility-domain registry. Standard envelope builders, validators, diagnostic issue helpers, deterministic identifiers, metric-label validators, and bounded deduplication helpers are support helpers unless a future tool module explicitly wraps them as official AI tools.
- **Official tool attachment**: Agents may attach only names approved by the relevant registry/policy check. Standard helpers can verify an approved name set, but they do not execute tools or grant trading, broker, risk, portfolio, or strategy authority.
- **Safe metric labels**: Metric labels must be bounded-cardinality and secret-free. Sensitive keys such as password, token, credential, secret, authorization, or API key are rejected. High-cardinality labels such as request IDs, user/account IDs, emails, UUIDs, session IDs, and long unbounded values are rejected unless explicitly normalized to deterministic fingerprints.
- **Optional adapters**: Utility standard helpers are stdlib-only. Optional adapters for metrics exporters, notification transports, event buses, encryption providers, broker SDKs, or external services must be lazy-loaded by their owning modules and must fail only when that feature is used.
- **Critical utility-layer failure runbook**: Fail closed, return a standard error envelope when possible, emit sanitized error events only, avoid retries for unknown side-effect state, check circuit-open state before provider calls, preserve request/workflow/correlation IDs, and escalate to the owning domain when the failure requires risk, trading, broker, portfolio, strategy, or governance judgment.
- **Completed utility primitives**: Utilities provide standard envelopes, typed errors, identity, UTC normalization, safe paths, lazy dataframe helpers, OHLCV diagnostics, schema validation, redaction/security, auth context checks, in-memory Event Bus, sanitized error routing, fake/local notification routing, and no-op/local observability primitives. These helpers remain support infrastructure and do not own strategy, portfolio, broker, risk, or live trading decisions.

## 12. Pending Architecture Decisions
1. Event bus durability phases.
2. Exact API schema/versioning format.
3. Deployment topology.
4. SQLite migration path.
5. AI provider interface details.
6. Risk threshold signing and approval process.
7. Worker/job execution model for heavy simulation/optimization.
8. Final identity provider.
9. Retention windows for chat, audit, market data, and regulated artifacts.
