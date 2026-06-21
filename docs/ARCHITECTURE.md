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

### 8.3 Simulator Service Contracts
- **Sprint-pack boundary**: Phase 8 is split into approved sprint packs. Completed 08A covers models/config/journal, deterministic result scaffolding, report string builders, request validation, arbitrary-code rejection, and an in-memory execution-provider-compatible adapter. Replay clock/data feed, order lifecycle/fill engine, portfolio/account/equity, analytics integration, and high-realism spread/slippage/latency remain later sprint packs.
- **Official public surface**: `app.services.simulator.run_backtest` is the user-facing simulator tool boundary. Internal engine services remain separate from the tool wrapper and are not agent-callable unless explicitly wrapped.
- **No live side effects**: Simulator execution must not call live broker execution code. The compatibility `SimulatorClient` is in-memory and preserves existing MT5-style tests, while `SimulatorExecutionProvider` uses canonical trade contracts for simulated execution.
- **Traceability and evidence**: Simulator requests carry `request_id`, actor context, strategy references, model ids, broker profile refs, data authority refs, and realism labels. Results include run/config/data hashes, journal manifest metadata, metrics, cost summaries, realism disclosure, and data-quality summary.
- **Run lifecycle envelopes**: `run_backtest` preserves the standard tool envelope at the top level and reports simulator lifecycle state inside `data.status`. Supported local states include `success`, `queued`, `cancelled`, and `diagnostic_failed`; validation and checkpoint incompatibility fail closed through deterministic standard error envelopes.
- **Journal boundary**: 08A supports in-memory and explicit JSONL journals with hash-chain replay metadata and an async append boundary. Production optimization, walk-forward, and Monte Carlo runs must stream journals with bounded buffers before they are enabled.
- **Pending and advanced-order contracts**: The simulator engine owns pending-order placement and trigger evaluation for buy/sell limit, buy/sell stop, and buy/sell stop-limit orders; supports deterministic stop-limit activation, SL/TP trigger evaluation, configured trailing-stop repricing, configured pegged-price resolution, and broker maximum-pending-order enforcement.
- **Sizing and broker-risk gates**: The engine records raw and normalized order volume, defaults volume rounding to floor-to-step, validates symbol min/max/step constraints, validates stop-loss/take-profit direction, enforces broker max-position limits, and blocks new simulated orders when account margin level reaches the configured stop-out threshold.

### 8.4 Risk Service Contracts
- **Modular Governance Engines**: The risk system is divided into modular, decoupled engine components (`PortfolioVaREngine`, `ExpectedShortfallEngine`, `MarginRiskEngine`, `DrawdownGovernor`) and structured result schemas (`VaRResult`, `ExpectedShortfallResult`, `MarginRequirement`, `LeverageSnapshot`, `LiquiditySnapshot`, `DrawdownState`, `RiskStepDownState`).
- **Institutional Configuration**: Supports both flat parameters and nested configuration blocks (`RiskSubConfig`, `DrawdownSubConfig`, `CorrelationSubConfig`, `TailRiskSubConfig`, `ExecutionSubConfig`) synchronized bi-directionally via model validation.
- **Mathematical Decoupling**: Standalone analytical and empirical functions (`calculate_parametric_var`, `calculate_historical_var`, `calculate_risk_contribution`, `calculate_margin_requirement`, `calculate_free_margin_after_trade`, `check_margin_usage`, `check_leverage_limit`, `check_exit_liquidity`, `calculate_daily_drawdown`, `calculate_total_drawdown`, `calculate_strategy_drawdown`, `apply_drawdown_throttle`) are exposed alongside the class-based engines for direct client calls.
- **Pre-Trade Risk Governance Gate**: `RiskGovernor.review_trade_risk` integrates all pre-trade limits, regime filters, margin stress, correlation limits, and drawdown throttles, ensuring fail-closed safety and audit traceability for all proposals.
- **Traceability**: All risk calculations and decision packages carry mandatory `request_id`, `correlation_id`, and `workflow_id` fields to maintain audit-trail continuity.
- **Strategy Lifecycle Governance**: Enforces stage progression gates (`research`, `simulation`, `paper`, `shadow`, `live-read-only`, `micro-live`, `full-live`) through structured review contracts (`StrategyAdmissionReview`, `LiveReadinessReview`, `ModePromotionReview`). Rejects live modes if key security requirements (e.g. audit persistence, kill switch, reconciliation, idempotency, broker metadata, risk config, policy enforcement) are missing, and requires signed `RiskApprovalToken` authorization for high-risk promotions.
- **Storage and Persistence Ports**: Defines decoupled repository interfaces (`RiskStateStore`, `RiskAuditSink`, `RiskPolicyStore`, `RiskDecisionStore`) with PEP 484 signatures. Enforces fail-closed behavior when persistence is unavailable, validates contract schema versions (expects major version `"1"`), and supports idempotent decision tracking using a compound key of `(request_id, workflow_id, signal_id, decision_material_hash)`.
- **Cryptographic Audit Chaining & Token Hardening**: Ensures audit integrity using a SHA-256 hash chain with a defined genesis rule for the first block. Enforces recursive redaction of sensitive credentials, keys, and tokens in audit payloads to prevent leaks. Validates approval tokens using `RiskDecisionTokenSigner` with active `policy_hash` bindings to guarantee cryptographic and policy compatibility.

### 8.5 Optimization Service Contracts
- **Exhaustive & Heuristic Search Engines**: Implements grid search (iterator-bound with parallel ThreadPool execution), random search (pseudo-random space sampling with explicit Sobol/Latin Hypercube fallbacks), genetic algorithms (crossover, mutation, elitism, tournament selection), and Bayesian optimization (GP fallback to random search when Optuna/scikit-optimize are absent, unless strict-mode is enabled).
- **Time-Series Splitting Boundaries**: Enforces chronological rolling and expanding splits with configurable purging and embargo windows to prevent overlaps and information leakage between training and out-of-sample segments.
- **Robustness & Monte Carlo Stress Testing**: Simulates spreads, slippage, and commission shocks, alongside Monte Carlo estimators for trade skips, trade shuffling, and ruin probability (estimated drawdowns, losers streaks, profit targets, and prop-firm breach indicators).
- **Safe Persistence & Checkpointing**: Persists state incrementally at configured candidate intervals. Saves use atomic writes (writing to a tempfile then swapping via `os.replace` to prevent corruption) and safe path checks to guard against directory traversal.
- **JSON Serialization Formatting**: Ensures all public returned payloads are JSON-safe (UTC ISO-8601 strings for `datetime`, string-based coercion for `Decimal`, and converting float `NaN` or `Infinity` to `null` with metadata warnings).

### 8.6 Live Service Contracts
- **Live Gating and Mutation Boundary**: The live runtime service acts as a safety gateway middleware. It governs live-route requests and enforces that live mutations (broker-routed order execution) are disabled by default (`live_enabled=False` and `live_mode="package_only"`) unless explicitly authorized.
- **Deterministic Gate Chain**: All requests must sequentially pass 11 deterministic gates: live enablement, request schema validation, approval validation, risk check, broker readiness, stale-context check, idempotency validation, reconciliation authority, kill switch validation, audit pre-recording, and broker permission. Fails closed immediately on the first blocking gate.
- **Session Lifecycle and Single-Session Guard**: Manages start, pause, stop, and recovery lifecycles. Restricts runtime execution to a single active session singleton. Recovery diagnostics place the session into a `paused` state pending operator review if any unknown outcomes or pending reconciliations are detected.
- **Reconciliation Authority**: Compares internal runtime state against authoritative broker snapshots. Detects missing, extra, and mismatched position/order items. Live mutation is blocked (returning `retry_after_reconciliation`) if any mismatch is found.
- **Monitoring, Health, and Cost Limits**: Tracks live tool latency, failures, and cost budgets. Ingestion failures, tool failure rates (5x failures fails a tool, 3x degrades it), or exceeding the cost budget automatically blocks live readiness.

### 8.7 Research Edge Lab Contracts
- **Read-Only / Advisory Gating**: The Research Edge Lab is strictly read-only with respect to live broker accounts and live trading states. All recommendation outcomes are marked as `"advisory_only"` to prevent interference with live risk profile engines.
- **Data Cleaning and Quality Reports**: Provides timezone normalization, missing-bar strategies (forward fill, linear interpolation, drop), and spread anomaly capping. Validation findings and transformations are recorded in a structured `DataQualityReportModel`.
- **Lookahead Bias & Leakage Gating**: Enforces chronological splits with safety buffer gaps and scans feature columns to reject lookahead bias with a `"critical"` leakage severity indicator.
- **Statistical Sign-Off**: Expectancy measurements are validated using non-parametric block bootstrapping, permutation tests, and multiple comparison corrections (Benjamini-Hochberg and Holm-Bonferroni) to control the False Discovery Rate.
- **Resource Constraints**: Validates dataset sizes against configured resource boundaries, raising a `ValidationError` when row counts exceed limits.
- **Graceful Optional Shims**: Optional dependencies (such as `scikit-learn` for unsupervised PCA and clustering) are shimmed to raise a `ValidationError` (code `SERVICE_UNAVAILABLE`) when missing, allowing the rest of the research workflows to execute cleanly.
- **Atomic Serialization**: Persists results to JSON and Markdown via safe temporary-file write-and-replace swaps to prevent corruption.

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
- **Completed utility primitives**: Utilities provide standard envelopes, typed errors, identity, UTC normalization, safe paths, lazy dataframe helpers, OHLCV diagnostics, schema validation, redaction/security, auth context checks, in-memory Event Bus, sanitized error routing, fake/local and real (Desktop, Telegram, Email) notification routing, and no-op/local observability primitives. These helpers remain support infrastructure and do not own strategy, portfolio, broker, risk, or live trading decisions.

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
