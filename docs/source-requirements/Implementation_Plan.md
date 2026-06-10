# HaruQuantAI Huge Implementation Plan v1

**Purpose:** Convert the 13 source requirements documents into one phased Builder checklist. Each source requirements file becomes one implementation phase.

**Execution rule:** This is an implementation plan, not permission to implement everything in one sprint. Each phase should be split into small Builder-approved sprint packs when work starts.

**Generated from uploaded source requirements:**

| Phase | Source file | Module path | Phase focus |
|---|---|---|---|
| 01 | `01-utils(3).md` | `tools/utils/` | Core platform primitives: logging, standard envelopes, errors, identity, time, paths, schemas, security, settings, auth, event bus, notifications, observability. |
| 02 | `02-data(2).md` | `tools/data/` | Contract-driven historical, real-time, local, synthetic, broker, and external market-data gateway. |
| 03 | `03-indicator(1).md` | `tools/indicators/` | Pure deterministic indicator calculation library with no direct I/O and explicit no-lookahead metadata. |
| 04 | `04-strategy(1).md` | `tools/strategies/` | Side-effect-free decision layer converting market data, indicators, config, and read-only state into TradeIntent objects. |
| 05 | `05-risk(1).md` | `tools/risk/` | Deterministic risk governance and safety gate between strategy intent and execution-sensitive workflows. |
| 06 | `06_analytics(1).md` | `tools/analytics/` | Read-only performance, robustness, dashboard, and reporting evidence layer. |
| 07 | `07_trading(1).md` | `tools/trading/` | Shared route-aware trading surface for simulation and live workflows. |
| 08 | `08-simulation(1).md` | `tools/simulation/` | Canonical deterministic tick-based backtesting and simulated execution engine. |
| 09 | `09_optimization(1).md` | `tools/optimization/` | Parameter search, walk-forward, robustness, Monte Carlo, scoring, and optimization evidence packaging. |
| 10 | `10_live(1).md` | `tools/live/` | Governed live-mutation boundary, live session runtime, gates, reconciliation, monitoring, and incident handling. |
| 11 | `11_ui_api(1).md` | `api/ + ui/` | FastAPI gateway and Next.js frontend surface for validated, governed access to backend capabilities. |
| 12 | `12_research(1).md` | `tools/research/` | Sandboxed market research, edge discovery, statistical validation, market structure, feature engineering, and reports. |
| 13 | `13_conversation(1).md` | `tools/conversation/` | Governed AI chat layer with durable threads, memory, page context, CEO/planner routing, read-only evidence, and action drafts. |

---

## Global Builder Rules

- [ ] Do not implement all phases at once. Treat each phase as a parent epic that must be decomposed into sprint-sized implementation slices.
- [ ] Before coding a phase, create or update that phase's `requirements.md`, `blueprint.md`, `acceptance.md`, and `handoff-prompt.md` sprint pack.
- [ ] No Builder may invent missing public API signatures, schema fields, route contracts, persistence behavior, or live trading authority.
- [ ] Any source requirement marked as blocked, pending, optional, future, staging, experimental, or not approved must remain disabled, stubbed, or fail-safe until explicitly approved.
- [ ] Every public function must have a standard response envelope, typed input/output schemas, deterministic error codes, side-effect classification, authorization expectations where applicable, tests, and usage examples.
- [ ] Every phase must preserve ownership boundaries. A module may consume evidence from another module but must not silently take over that module's authority.
- [ ] No chat, UI, research, analytics, optimization, simulation, or strategy workflow may bypass risk, approval, live, idempotency, audit, reconciliation, or kill-switch controls.
- [ ] Live broker mutation is forbidden until Trading, Risk, Live, API authorization, audit, idempotency, reconciliation, operator approval, and kill-switch gates all exist and pass.
- [ ] All artifacts, reports, manifests, and outputs must be reproducible, hashable where relevant, redacted where sensitive, and JSON-safe at official tool boundaries.
- [ ] Use fresh clean implementation. Do not add legacy compatibility aliases unless a later approved architecture decision explicitly requests them.

---

## Recommended Build Order and Dependency Gates

```text
01 Utils
  -> 02 Data
      -> 03 Indicators
          -> 04 Strategies
              -> 05 Risk
              -> 07 Trading
                  -> 08 Simulation
                      -> 06 Analytics
                      -> 09 Optimization
                          -> 10 Live
                              -> 11 UI/API
                                  -> 12 Research
                                      -> 13 Conversation
```

**Note:** The numbered phase order follows the source files. The dependency graph shows practical implementation dependencies. Analytics can begin after Simulation has stable canonical result shapes, but metric kernels may be developed earlier behind internal fixtures. Research can begin after Data and Analytics foundations exist, but public research tooling should wait for standard envelopes and artifact rules. Conversation should come last because it composes page context, read-only tool evidence, CEO/planner routing, and governed action drafts across the rest of the platform.

---

## Cross-Phase Architecture Deliverables

- [ ] Create `docs/PROJECT.md` updates that describe this phased implementation approach without duplicating every requirement.
- [ ] Create `docs/ARCHITECTURE.md` module-boundary diagram showing ownership and forbidden ownership for every module.
- [ ] Create `docs/PROJECT.md` with one concise module entry per phase: owns, does not own, public surface, dependencies, and readiness status.
- [ ] Create `docs/ROADMAP.md` with phase gates and deferred scope register.
- [ ] Create `docs/BUILDER.md` with common Builder dry-run rules and acceptance checklist.
- [ ] Maintain a central error-code catalog or per-module error catalogs linked from module docs.
- [ ] Maintain an official tool catalog per module before exposing anything to agents or API routes.
- [ ] Maintain a test traceability matrix mapping requirements to tests for every phase.
- [ ] Maintain a deferred decisions register for pending, staging, experimental, and future items.

---

## Phase 01 — Utils Foundation

**Source:** `01-utils(3).md`
**Target path:** `tools/utils/`
**Phase objective:** Create the shared HaruQuantAI utility foundation before any domain module depends on envelopes, errors, IDs, timestamps, schema validation, settings, security, events, notifications, or observability.

### Phase prerequisites

- [ ] Approved baseline project structure exists.
- [ ] Python package/test layout is available.
- [ ] No domain module depends on incomplete utility behavior.

### Implementation checklist

#### Contracts and registry

- [ ] Create the `tools.utils` package and explicit `__all__` export registry.
- [ ] Define standard response envelopes with `status`, `message`, `data`, `error`, and `metadata` fields.
- [ ] Define deterministic error classes, error codes, and exception-to-envelope mapping.
- [ ] Define module metadata, version metadata, timing metadata, and correlation/causation metadata helpers.
- [ ] Add contract tests proving all official utilities return JSON-safe outputs.

#### Logging, identity, and time

- [ ] Implement structured logger configuration with secret-safe metadata.
- [ ] Add request ID, workflow ID, event ID, version ID, and idempotency key helpers.
- [ ] Implement UTC-first timestamp normalization, freshness checks, stale-data checks, and monotonic timers.
- [ ] Ensure logs never contain raw secrets, raw approval packets, or raw market payloads by default.

#### Validation, normalization, and paths

- [ ] Implement deterministic canonical JSON serialization and canonical hashing helpers.
- [ ] Implement safe path handling using approved roots and traversal protection.
- [ ] Implement input/output schema validation helpers.
- [ ] Implement numeric range, freshness, artifact reference, evidence, approval, registry, and handoff validation helpers.
- [ ] Implement diagnostic-only OHLCV quality validation without market-data repair ownership.

#### Security, auth, and settings

- [ ] Implement redaction helpers for secrets, tokens, credentials, emails, and long identifiers.
- [ ] Implement password hashing/verification helpers where required.
- [ ] Implement encryption/decryption boundaries without hard-coded secrets.
- [ ] Implement runtime settings loading with deterministic precedence.
- [ ] Implement auth-context validation, deny-by-default authorization helpers, and tool allowlists.

#### Event bus, notifications, and observability

- [ ] Implement in-process Event Bus contracts and fake/test adapters.
- [ ] Implement error-routing and alert-routing primitives.
- [ ] Implement notification routing contracts for email, Telegram, and desktop without provider credentials.
- [ ] Implement metric registration and recording helpers.
- [ ] Implement Prometheus-compatible metrics helpers and Grafana dashboard expectations.
- [ ] Implement health snapshot and trace-correlation helpers.

#### Tests and acceptance

- [ ] Add unit tests for every utility file.
- [ ] Add usage tests showing domain modules can consume envelopes, validation, event bus, and observability.
- [ ] Add security tests for redaction, path traversal, auth denial, and optional dependency behavior.
- [ ] Add import tests proving optional adapters do not break package import.
- [ ] Accept only when utilities remain side-effect safe at import time.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/__init__.py` (Root package initializer)
2. `tools/utils/errors.py` (Registry of system exception types and codes)
3. `tools/utils/standard.py` (Standard response envelopes)
4. `tools/utils/identity.py` (Request and trace IDs)
5. `tools/utils/normalization.py` (Timestamp and numeric formatting helpers)
6. `tools/utils/logger.py` (Configured structured logger)
7. `tools/utils/paths.py` (Protected path helpers and traversal checks)
8. `tools/utils/security.py` (Redaction and hash engines)
9. `tools/utils/settings.py` (Runtime configuration loader)
10. `tools/utils/auth.py` (Deny-by-default allowlist checks)
11. `tools/utils/dataframe_tools.py` (Safe lazy DataFrame wrappers)
12. `tools/utils/schema_validation.py` (JSON schema and contract validation)
13. `tools/utils/data_quality.py` (Diagnostic-only OHLCV validator)
14. `tools/utils/event_bus.py` (In-process pub/sub foundation)
15. `tools/utils/error_routing.py` (Error-to-event router)
16. `tools/utils/notifications.py` (Email/Telegram routing interfaces)
17. `tools/utils/observability.py` (Prometheus metrics and health snapshots)
18. `tools/utils/__init__.py` (Exposes final public utilities)

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 02 — Data Service

**Source:** `02-data(2).md`
**Target path:** `tools/data/`
**Phase objective:** Build the canonical data access layer and gateway used by research, indicators, strategy, simulation, optimization, analytics, risk, trading-preparation, and agentic workflows.

### Phase prerequisites

- [ ] Phase 01 standard envelopes, errors, settings, paths, validation, logging, and observability primitives are available.
- [ ] Data source readiness policy is approved for local/synthetic/staging providers.

### Implementation checklist

#### Contracts and official surface

- [ ] Define official data tool names and `tools.data.__all__` exports.
- [ ] Define standard data envelopes aligned with Utils.
- [ ] Define deterministic `DATA_*` error codes including validation failure, buffer overflow, and data dropped.
- [ ] Define data-kind, source, timeframe, readiness, and capability enums.
- [ ] Add manifest schemas for data authority, source metadata, quality metadata, and normalized payload references.

#### Local and synthetic sources

- [ ] Implement CSV adapter with safe paths and schema validation.
- [ ] Implement Parquet adapter with safe paths and schema validation.
- [ ] Implement deterministic GBM synthetic generation for bars and ticks.
- [ ] Implement synthetic source manifests and reproducibility seeds.
- [ ] Ensure local/synthetic sources can be marked production-ready while external sources start conservative.

#### Normalization and transforms

- [ ] Normalize OHLCV, tick, spread, and volume records into stable contracts.
- [ ] Implement timeframe parsing and canonical timestamp handling.
- [ ] Implement resampling, tick aggregation, multi-timeframe alignment, and labeling.
- [ ] Enforce no-lookahead defaults in transformation outputs.
- [ ] Propagate data-quality flags and source-readiness metadata downstream.

#### Cache, storage, and persistence

- [ ] Implement approved cache roots, TTLs, invalidation rules, atomic writes, and manifests.
- [ ] Implement safe cache clear with scope limits.
- [ ] Implement SQLite persistence for local scheduler state and crash recovery.
- [ ] Keep persistence abstraction TSDB-ready for future high-frequency tick/spread storage.
- [ ] Represent large payloads with artifact references where needed instead of leaking raw objects.

#### Scheduler, jobs, and recovery

- [ ] Define update-job, backfill, chunk, checkpoint, lease, retry, and recovery contracts.
- [ ] Implement canonical `get_data_update_job_status` status inspection.
- [ ] Implement idempotent job definitions and chunk checkpointing.
- [ ] Implement crash recovery behavior for interrupted jobs.
- [ ] Reject unofficial scheduler exports unless approved.

#### Gateway and adapters

- [ ] Implement source registry and gateway routing from one internal contract to many adapters.
- [ ] Implement readiness checks and capability declarations.
- [ ] Implement fake adapters and optional dependency fail-safe behavior.
- [ ] Stub or stage MT5, cTrader, Dukascopy, Binance symbol discovery, and live feed gateway adapters until promotion evidence exists.
- [ ] Implement canonical `get_feed_status` for real-time feed observability.

#### Tests and acceptance

- [ ] Add contract tests for exports, errors, envelopes, manifests, and normalized records.
- [ ] Add adapter tests for CSV, Parquet, synthetic, and staging adapters.
- [ ] Add cache/storage/persistence crash-recovery tests.
- [ ] Add scheduler idempotency and checkpoint tests.
- [ ] Add feed status, bounded buffer, heartbeat, gap, and circuit-breaker tests.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/data/errors.py` (Reuses `tools.utils.errors` + custom data exceptions)
2. `tools/data/validation.py` (Market data and record schemas)
3. `tools/data/transforms.py` (Timeframe alignments, resampling, and lookahead checks)
4. `tools/data/cache.py` (Cache storage path and manifest files)
5. `tools/data/storage.py` (Local CSV and Parquet read/write helpers)
6. `tools/data/persistence.py` (SQLite scheduler/job persistence)
7. `tools/data/adapters/__init__.py`
8. `tools/data/adapters/csv.py`, `tools/data/adapters/parquet.py`, `tools/data/adapters/synthetic.py`
9. `tools/data/adapters/mt5.py`, `tools/data/adapters/ctrader.py`, `tools/data/adapters/dukascopy.py` (Staged integrations)
10. `tools/data/scheduler.py` (Idempotent job runner and checkpoint manager)
11. `tools/data/gateway.py` (The main router interfacing all data adapters)
12. `tools/data/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 03 — Indicator Library

**Source:** `03-indicator(1).md`
**Target path:** `tools/indicators/`
**Phase objective:** Implement deterministic indicator calculations as pure decision-support artifacts with explicit warmup, availability, quality, provenance, and no-lookahead metadata.

### Phase prerequisites

- [ ] Phase 01 utility primitives are available.
- [ ] Phase 02 normalized data contracts and quality metadata are stable enough for indicator input fixtures.

### Implementation checklist

#### Core contracts

- [ ] Create indicator protocols, config, context, result, manifest, state, warmup, registration, and error types.
- [ ] Define registry operations for register, get, list, validate, and allowed unregister.
- [ ] Publish a machine-readable capability matrix from registry metadata.
- [ ] Fail unsupported capability requests before calculation with deterministic `IND_UNSUPPORTED_*` errors.

#### Built-in calculations

- [ ] Implement trend indicators such as SMA, EMA, and ADX.
- [ ] Implement volatility indicators such as ATR, ADR, and rolling volatility.
- [ ] Implement momentum indicators such as RSI and Williams %R.
- [ ] Return generated column names, values-only option, manifests, availability metadata, and quality metadata.
- [ ] Implement `join_to(input_data, mode="copy")` without mutating input by default.

#### No-lookahead and data safety

- [ ] Calculate and expose `available_at`, `computed_from_start`, `computed_from_end`, and source timeframe metadata.
- [ ] Respect warmup and closed-bar availability rules.
- [ ] Reject missing, unsorted, duplicate, or non-UTC timestamp data as configured.
- [ ] Propagate upstream data-quality flags without repairing market data.
- [ ] Keep calculation paths free of filesystem, network, cache, clock, and telemetry side effects.

#### Optional capability boundaries

- [ ] Define incremental state protocol but keep optional if not in first slice.
- [ ] Define streaming/out-of-core/accelerated/composed/proprietary/canary capabilities as disabled unless explicitly enabled.
- [ ] Allow cache, audit, and observability only through injected mockable adapters.
- [ ] Document all optional features in the capability matrix.

#### Tests and acceptance

- [ ] Add golden fixtures for each built-in indicator and tolerance policy.
- [ ] Add no-lookahead tests for `available_at` and warmup behavior.
- [ ] Add registry and capability-matrix tests.
- [ ] Add custom indicator conformance tests.
- [ ] Add import and side-effect tests proving calculations do not perform direct I/O.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/indicators/protocols.py` (Indicator execution interfaces)
2. `tools/indicators/errors.py` (Custom indicator errors inheriting from utils)
3. `tools/indicators/calculations.py` (Mathematical calculation helper functions)
4. `tools/indicators/batch/__init__.py`
5. `tools/indicators/batch/trend.py`, `tools/indicators/batch/volatility.py`, `tools/indicators/batch/momentum.py`
6. `tools/indicators/incremental/__init__.py`
7. `tools/indicators/incremental/state.py`, `tools/indicators/incremental/accumulators.py` (Optional streaming)
8. `tools/indicators/adapters/__init__.py`
9. `tools/indicators/adapters/cache.py`, `tools/indicators/adapters/audit.py`
10. `tools/indicators/registry.py` (Dynamic capability registry and catalog exporter)
11. `tools/indicators/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 04 — Strategy Engine

**Source:** `04-strategy(1).md`
**Target path:** `tools/strategies/`
**Phase objective:** Create the side-effect-free strategy decision layer that emits schema-valid, deterministic, auditable `TradeIntent` objects but never executes or authorizes trades.

### Phase prerequisites

- [ ] Phase 03 indicator result contracts are available.
- [ ] Phase 02 data readiness and manifest contracts are available.
- [ ] Strategy public API signatures are approved before Builder handoff.

### Implementation checklist

#### Contracts and API completion

- [ ] Approve exact Python signatures for each public capability before implementation.
- [ ] Implement `validate_strategy_ref` against immutable registry entries and lifecycle status.
- [ ] Implement `validate_strategy_config` with schema versions, normalized defaults, and config hashes.
- [ ] Implement `run_vectorized_strategy_signals` for batch signal generation.
- [ ] Implement `run_event_strategy_hook` for event-driven strategy hooks.
- [ ] Implement `build_trade_intent` with deterministic `intent_id`, `decision_id`, idempotency key, and lineage.
- [ ] Implement `create_strategy_replay_manifest` and `export_strategy_diagnostics`.

#### Registry and lifecycle

- [ ] Create strategy registry with versions, hashes, lifecycle status, approvals, deprecations, and config policy.
- [ ] Reject missing, deprecated, unapproved, or version-incompatible strategies.
- [ ] Require explicit technology stack and third-party dependency declarations for production-eligible execution.
- [ ] Track capacity assumptions such as max symbols and max concurrent strategies.

#### Decision semantics

- [ ] Enforce pure function semantics over market data, indicators, config, and read-only state.
- [ ] Generate ordered timestamped signals and TradeIntent objects.
- [ ] Prevent duplicate intents with idempotency and lineage checks.
- [ ] Support strategy-local state checkpoint requests only when declared.
- [ ] Keep strategy outputs as declarations, metadata, diagnostics, and intent annotations, not enforcement.

#### Safety and governance

- [ ] Reject arbitrary user-provided Python unless future sandbox policy is approved.
- [ ] Enforce data, indicator, and feature readiness before decisions.
- [ ] Detect lookahead and fail with deterministic strategy errors.
- [ ] Apply resource limits and timeout handling.
- [ ] Redact diagnostics and safe rationales.

#### Tests and acceptance

- [ ] Add registry, config, vectorized, event, intent, manifest, and diagnostics tests.
- [ ] Add lookahead rejection, duplicate-intent, invalid-config, timeout, and checkpoint-restore failure tests.
- [ ] Add usage tests for registered vectorized strategy and event strategy lifecycle.
- [ ] Add replay determinism tests using config/data/indicator hashes.
- [ ] Accept only when strategy module cannot mutate broker, account, risk, portfolio, or live state.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/strategies/protocols.py` (Strategy runner interfaces)
2. `tools/strategies/errors.py` (Lookahead & missing strategy errors)
3. `tools/strategies/sandbox.py` (Isolated python runtime runner)
4. `tools/strategies/vectorized.py` (Vectorized batch signal runtime)
5. `tools/strategies/event.py` (Event-driven strategy signal runtime)
6. `tools/strategies/registry.py` (Immutable strategy registration and version compiler)
7. `tools/strategies/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 05 — Risk Governor

**Source:** `05-risk(1).md`
**Target path:** `tools/risk/`
**Phase objective:** Implement deterministic risk governance as the safety gate between strategy intent and trading/simulation/live workflows, treating ambiguity as a hard failure.

### Phase prerequisites

- [ ] Phase 01 utilities are available.
- [ ] Strategy TradeIntent schema is stable enough for risk admission review.
- [ ] Risk profile configuration location and fail-closed behavior are approved.

### Implementation checklist

#### Contracts and configuration

- [ ] Create Pydantic V2 public contracts and internal immutable calculation helpers.
- [ ] Load config-driven thresholds and profiles from `configs/risk/*.yaml`.
- [ ] Define `RiskDecisionPackage` schema with approve, reject, block, needs-more-evidence, and needs-approval states.
- [ ] Define deterministic `RISK_*` and pending-decision fallback errors.
- [ ] Require live workflows to define production profiles and audit settings.

#### Risk calculations

- [ ] Implement exposure limits, max daily loss, max total loss, drawdown state, and portfolio drawdown gating.
- [ ] Implement position sizing including fixed fractional and configured Kelly where approved.
- [ ] Implement VaR/CVaR, correlation, concentration, margin, and portfolio contribution checks.
- [ ] Implement regime, crisis/high-volatility, and stressed-evidence behavior with fail-closed fallbacks.
- [ ] Implement exit-liquidity stress and correlation-adjusted sizing for production-live readiness.

#### Governance and approvals

- [ ] Implement approval-token validation, consumption, revocation, and audit-state interfaces.
- [ ] Implement pre-trade admission review from portfolio, market, strategy, approval, and policy evidence.
- [ ] Implement kill-switch checks and breach classification.
- [ ] Prevent double-spend approval ambiguity using pending-approval evidence or fail-closed fallback.
- [ ] Never place trades or mutate broker/execution state.

#### Audit and persistence ports

- [ ] Define JSONL local deterministic storage for development and tests.
- [ ] Define PostgreSQL-required production audit-chain, approval-token, token revocation, and token consumption persistence ports.
- [ ] Implement audit hash chaining where required for production-live.
- [ ] Emit safe evidence packages and decision metadata.

#### Tests and acceptance

- [ ] Add unit tests for limits, sizing, governor, kill switch, scenarios, and lifecycle.
- [ ] Add property tests around threshold edges and fail-closed behavior.
- [ ] Add concurrency tests for double-spend/pending approvals.
- [ ] Add scenario tests for USD crash, JPY spike, high volatility, crisis regime, stale portfolio, and missing evidence.
- [ ] Accept only when ambiguous live-sensitive inputs block rather than pass.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/risk/models.py` (Pydantic models for RiskDecisionPackage)
2. `tools/risk/limits.py` (Max daily loss, drawdown, and correlation checks)
3. `tools/risk/sizing.py` (Kelly/fixed fractional math calculators)
4. `tools/risk/scenarios.py` (Stressed regime-specific risk checks)
5. `tools/risk/kill_switch.py` (System-wide fail-closed checks)
6. `tools/risk/lifecycle.py` (Approval token registry and consumption checks)
7. `tools/risk/governor.py` (Admission engine reviewing TradeIntents)
8. `tools/risk/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 06 — Analytics Evidence

**Source:** `06_analytics(1).md`
**Target path:** `tools/analytics/`
**Phase objective:** Implement read-only analytics evidence for trades, equity curves, returns, benchmarks, drawdowns, ratios, distributions, dashboard payloads, and strategy-quality scorecards.

### Phase prerequisites

- [ ] Phase 01 utilities are available.
- [ ] Canonical trade/equity/result fixtures exist from Simulation or approved test fixtures.
- [ ] Analytics official catalog and metric definitions are approved.

### Implementation checklist

#### Official catalog and contracts

- [ ] Create Official Analytics Tool Catalog with tool names, callable paths, stability, schemas, errors, side effects, risk levels, and support status.
- [ ] Create Metric Definition Catalog for every official metric.
- [ ] Create warning-code and quality-flag catalogs.
- [ ] Expose only approved high-level tools through `tools.analytics.__all__`.
- [ ] Return standard envelopes with safe metadata.

#### Input adapters and schemas

- [ ] Implement canonical `TradingResult` adapters for backtest, paper, live, portfolio, and normalized caller outputs.
- [ ] Fail closed when required fields, schema versions, or compatibility mappings are missing.
- [ ] Normalize trade dictionaries, numeric return lists, equity curves, and benchmark series.
- [ ] Filter closed trades and classify trades deterministically.
- [ ] Extract R-multiple, exposure, and time-in-market primitives.

#### Metric implementation

- [ ] Implement trade metrics, equity metrics, drawdowns, risk statistics, ratios, distributions, benchmark-relative metrics, and efficiency metrics.
- [ ] Implement statistical validation diagnostics and caveats.
- [ ] Implement prop-firm evidence groups when contracts are approved.
- [ ] Compute reports without mutating source reports or upstream artifacts.
- [ ] Never emit a live-ready, promotable, or final approval verdict.

#### Reports and dashboard payloads

- [ ] Build `AnalyticsReport` and `PortfolioAnalyticsReport` schemas.
- [ ] Build dashboard-ready and report-ready payloads from validated report sections.
- [ ] Build non-binding strategy-quality evidence from supplied analytics report material.
- [ ] Compare supplied analytics reports without recomputing or fabricating core metrics.
- [ ] Include lineage, reproducibility hashes, warnings, and quality flags.

#### Tests and acceptance

- [ ] Add unit tests for metrics, adapters, reports, scorecards, and dashboard payloads.
- [ ] Add fixtures for empty trades, missing equity, benchmark mismatch, all winners, all losers, flat equity, and NaN/inf inputs.
- [ ] Add determinism tests for hashes and output ordering.
- [ ] Add tests ensuring analytics cannot approve, promote, allocate, or execute.
- [ ] Accept only when outputs are read-only advisory evidence.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/analytics/metrics/__init__.py`
2. `tools/analytics/metrics/trade.py`, `tools/analytics/metrics/equity.py`, `tools/analytics/metrics/drawdown.py`, `tools/analytics/metrics/ratios.py`, `tools/analytics/metrics/distributions.py`, `tools/analytics/metrics/benchmark.py`, `tools/analytics/metrics/efficiency.py`
3. `tools/analytics/adapters.py` (Input conversion wrappers for backtest/live inputs)
4. `tools/analytics/scorecard.py` (Strategy quality evaluation scorecard)
5. `tools/analytics/report.py` (Aggregates stats into file-persisted documents)
6. `tools/analytics/dashboard.py` (Minified frontend payload extractor)
7. `tools/analytics/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 07 — Trading Contract Boundary

**Source:** `07_trading(1).md`
**Target path:** `tools/trading/`
**Phase objective:** Build the shared route-aware trading contract used by both simulation and live, with one request/result shape and explicit `route="sim"` or `route="live"` behavior.

### Phase prerequisites

- [ ] Phase 01 utilities are available.
- [ ] Risk decision package and TradeIntent/TradeRequest boundaries are stable enough for integration.
- [ ] Route authority rules for `sim` and `live` are approved.

### Implementation checklist

#### Registry and route contract

- [ ] Create `tools.trading.__all__` public registry.
- [ ] Define canonical trading route contract for `sim` and `live` routes.
- [ ] Define standard trading envelopes with validation errors, idempotency metadata, route metadata, and audit references.
- [ ] Classify every trading function by side effect, authority requirement, route support, and persistence behavior.

#### Validation and request packaging

- [ ] Implement symbol, volume, price, order type, magic/expert ID, slippage, expiration, timeframe, date range, stop loss, take profit, credentials, margin, ticket, max-order, and symbol-volume validation.
- [ ] Implement broker readiness request packaging for account, symbol, quote, spread, market, margin, lot, stop-distance, permission, and broker-time checks.
- [ ] Implement execution plan construction and pre-send validation.
- [ ] Consume risk, approval, kill-switch, authorization, and live-runtime verdicts from owning modules.

#### Simulation-compatible behavior

- [ ] Implement simulator-state mutation for `route="sim"` only.
- [ ] Implement simulated order placement, pending-order processing, fill records, account snapshots, equity points, trade records, and JSON-safe result containers.
- [ ] Preserve same public request shapes and envelopes as live-compatible packaging.

#### Live-compatible boundaries

- [ ] Package live requests but do not independently authorize broker mutation.
- [ ] Propagate authority state, idempotency material, send-attempt evidence, receipts, compensation plans, and retry-guard inputs.
- [ ] Define broker bridge boundaries for MT5, cTrader, paper broker, simulator, and approved adapters.
- [ ] Do not perform live credential discovery or secret lookup outside Live.

#### Reconciliation and monitoring

- [ ] Implement reconciliation request packages and evidence schemas.
- [ ] Implement compensation package construction without unsafe execution.
- [ ] Implement monitoring inputs for stale state, ingestion health, tool health, workflow timeout, incidents, latency, cost, and operational status.
- [ ] Implement shadow-trading expected-versus-realized reports when no live mutation occurs.

#### Tests and acceptance

- [ ] Add bridge, validation, reconciliation, simulator, monitoring, and compensation tests.
- [ ] Add route parity tests proving sim/live share schemas and differ only by explicit route behavior.
- [ ] Add idempotency, duplicate request, stale evidence, and missing authority tests.
- [ ] Accept only when trading cannot bypass risk, approval, idempotency, reconciliation, audit, or kill switches.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/trading/validation.py` (Lot size, order type, and pricing validation)
2. `tools/trading/bridge/base.py` (Abstract broker interface wrapper)
3. `tools/trading/bridge/mt5.py`, `tools/trading/bridge/ctrader.py` (Live route handlers)
4. `tools/trading/simulator/broker.py`, `tools/trading/simulator/state.py` (Simulation route handlers)
5. `tools/trading/reconciliation.py` (Receipt mapping and compensation)
6. `tools/trading/monitoring.py` (Stale feeds and connection telemetry checker)
7. `tools/trading/compensation.py` (Failure state rollback and correction packager)
8. `tools/trading/registry.py` (Allowed trading capabilities directory)
9. `tools/trading/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 08 — Simulation / Backtest Engine

**Source:** `08-simulation(1).md`
**Target path:** `tools/simulation/`
**Phase objective:** Implement the canonical deterministic FX Phase 1 backtest engine that converts approved strategy outputs into tick-accurate simulated execution, accounting, journals, metrics, reports, and replayable evidence.

### Phase prerequisites

- [ ] Data, Indicators, Strategy, Risk, and Trading contracts needed for canonical FX simulation are stable.
- [ ] `run_backtest` request/response schemas are approved before implementation.
- [ ] Out-of-scope asset classes remain deferred.

### Implementation checklist

#### Specification gate before code

- [ ] Complete the approved `run_backtest` contract with request schema, response schema, status values, deterministic errors, artifact behavior, and authorization behavior.
- [ ] Complete `SimulationResult`, journal event, report JSON, broker profile, and market-data authority manifest schemas.
- [ ] Complete every exposed `SimTrader` method contract before implementation.
- [ ] Keep Phase 1 limited to canonical FX unless roadmap explicitly expands scope.

#### Orchestration and validation

- [ ] Implement `BacktestOrchestrator` lifecycle.
- [ ] Validate simulation config, strategy refs, data dependencies, broker profiles, market-data authority manifests, realism requirements, and run permissions before execution.
- [ ] Reject raw Python strategy code through `run_backtest`.
- [ ] Validate inbound contracts from Data and Strategy before official runs.
- [ ] Implement run idempotency and run lifecycle status.

#### Execution engine

- [ ] Implement `EventDrivenExecutionEngine` canonical tick loop.
- [ ] Convert timestamped `TradeIntent` objects into sized `TradeRequest` objects.
- [ ] Implement MT5-style simulation-only trader interface and query semantics.
- [ ] Own official simulated orders, deals, positions, pending orders, account state, balance, equity, margin, free margin, margin level, realized/floating PnL, and timestamps.
- [ ] Implement same-tick event priority, gap handling, spread, slippage, liquidity, matching, partial fills, commissions, fees, swaps, funding/borrow fees where in scope.

#### Journal and reports

- [ ] Persist immutable simulation journal events.
- [ ] Create canonical JSON reports, required Markdown reports, artifact manifests, replay metadata, and derived artifacts where configured.
- [ ] Produce data-quality gating, realism classification, asset-class realism disclosures, benchmark manifests, and model-governance evidence.
- [ ] Emit report artifacts without calling live modules or live broker adapters.

#### Optimization and replay support

- [ ] Implement deterministic replay and step-through replay where in Phase 1.
- [ ] Define hooks for optimization, walk-forward, Monte Carlo, visual replay export, and service-mode lifecycle only when explicitly tagged.
- [ ] Provide simulation evidence to Analytics and Optimization without granting promotion authority.

#### Tests and acceptance

- [ ] Add unit tests for orchestrator, engine, models, validation, journal, and report.
- [ ] Add integration test for canonical FX backtest.
- [ ] Add severe data-quality blocked-run tests.
- [ ] Add deterministic replay and artifact hash tests.
- [ ] Add no-lookahead, fill priority, gap, slippage, spread, partial-fill, margin, swap, and cost edge tests.
- [ ] Accept only when official fills pass through the tick execution loop.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/simulation/models.py` (Backtest result and request model definitions)
2. `tools/simulation/validation.py` (Prerequisite validation check routines)
3. `tools/simulation/simtrader.py` (Implements target broker protocols)
4. `tools/simulation/engine.py` (The main event-driven queue runner)
5. `tools/simulation/journal.py` (Writes intermediate ticks/fills to file)
6. `tools/simulation/fx.py` (Currency conversion and rate matcher)
7. `tools/simulation/adapters.py` (Loads inputs from Phase 02 Data)
8. `tools/simulation/orchestrator.py` (Controls backtest lifecycles)
9. `tools/simulation/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 09 — Optimization Framework

**Source:** `09_optimization(1).md`
**Target path:** `tools/optimization/`
**Phase objective:** Implement optimization request packaging, lower-level search contracts, robustness checks, scoring, checkpointing, and evidence packages without becoming a live approval authority.

### Phase prerequisites

- [ ] Simulation execution adapter contract is stable.
- [ ] Analytics report/evidence contracts are available.
- [ ] Optimization run limits, objective names, and persistence policy are approved for the active slice.

### Implementation checklist

#### Public service surface

- [ ] Expose approved optimization service tools through `tools.optimization.__all__`.
- [ ] Return standard optimization envelopes with tool name, status, request ID, data, errors, warnings, and audit metadata.
- [ ] Package parameter sweep, walk-forward, matrix, comparison, robustness, and report requests.
- [ ] Classify public service tools by experimental/stable and packaging/execution behavior.

#### Search and splitting

- [ ] Implement parameter ranges, candidate hashing, parameter-space hashing, and cache-reuse rules.
- [ ] Implement grid search and random search first where approved.
- [ ] Define Bayesian and genetic algorithms as optional/later unless explicitly approved.
- [ ] Implement train/test split and walk-forward analysis helpers.
- [ ] Implement walk-forward matrix and parameter stability helpers.

#### Robustness and Monte Carlo

- [ ] Implement spread, slippage, commission, cross-market, cross-timeframe, and out-of-sample robustness request packages.
- [ ] Implement Monte Carlo helpers for trade-order shuffling, return resampling, bootstrap, ruin probability, confidence intervals, parametric simulations, position sizing, consecutive-loss, profit-target, random win-rate, robustness, and multi-entry simulations.
- [ ] Implement overfit detection and multiple-testing correction support.
- [ ] Implement robustness score and report package.

#### Scoring and evidence

- [ ] Implement objective-name resolution and scoring functions.
- [ ] Implement Deflated Sharpe, Probability of Backtest Overfitting, Walk-Forward Efficiency, parameter topology stability, Monte Carlo survival, and prop-firm compliance evidence where approved.
- [ ] Create optimization evidence packages, final decision states, rejected-candidate summaries, production-gate results, audit references, and chart-ready handoff data.
- [ ] Ensure optimization success never equals live approval.

#### Persistence contracts

- [ ] Define repository interfaces as Protocol/ABC only.
- [ ] Define checkpoint metadata, resume metadata, cancel/progress workflows, and repository payload schemas.
- [ ] Inject concrete repositories from infrastructure when approved; do not own migrations or database sessions.

#### Tests and acceptance

- [ ] Add tests for sweeps, robustness, splitting, scoring, models, checkpointing, and request packaging.
- [ ] Add determinism tests for candidate hashes and resume behavior.
- [ ] Add overfit/robustness gates on known fixtures.
- [ ] Add tests proving no strategy mutation, live approval, or broker execution authority exists.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/optimization/models.py` (Candidate inputs and result Pydantic schemas)
2. `tools/optimization/helpers.py` (Strategy loader and result wrapper)
3. `tools/optimization/scoring.py` (Objective calculators like Sharpe and Calmar)
4. `tools/optimization/splitting.py` (Walk-forward rolling and anchored fold splitters)
5. `tools/optimization/algorithms/__init__.py`
6. `tools/optimization/algorithms/grid.py`, `tools/optimization/algorithms/random.py`, `tools/optimization/algorithms/bayesian.py`, `tools/optimization/algorithms/genetic.py`
7. `tools/optimization/robustness.py` (Slippage and Monte Carlo stress engines)
8. `tools/optimization/persistence/__init__.py`
9. `tools/optimization/persistence/checkpoint.py` (Saves intermediate candidate state)
10. `tools/optimization/persistence/repository.py` (Database resume adapter)
11. `tools/optimization/sweeps.py` (Runs parallel parameter sweeps)
12. `tools/optimization/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 10 — Live Runtime

**Source:** `10_live(1).md`
**Target path:** `tools/live/`
**Phase objective:** Implement the live trading runtime as a strict middleware/gateway around shared trading functions so live-route requests cannot bypass enablement, approval, risk, reconciliation, audit, idempotency, kill switch, or operator controls.

### Phase prerequisites

- [ ] Trading route-aware contracts are available.
- [ ] Risk decisions, approval evidence, kill-switch state, idempotency, audit, and reconciliation interfaces are available.
- [ ] Live enablement and broker-readiness policy are approved.

### Implementation checklist

#### Configuration and enablement

- [ ] Implement live runtime configuration for enablement flags, safety settings, notifications, logging, state, and secret-reference resolution.
- [ ] Validate that no notification, broker, or mutation channel is active without explicit configuration.
- [ ] Define live action matrix input contract from governance/policy owner.
- [ ] Fail closed when actor context, approval context, risk verdict, kill-switch state, or live enablement is missing.

#### Session lifecycle

- [ ] Implement live session, live run, startup, shutdown, signal handling, recovery diagnostics, and runtime status/event emission.
- [ ] Implement safe startup reconciliation before mutation.
- [ ] Implement safe shutdown and exposure-reduction request packaging.
- [ ] Emit live runtime events for approved consumers.

#### Live gates

- [ ] Implement mandatory live-only gates for broker mutation, kill switch, pause, resume, exposure reduction, mass cancel, mass close, and recovery.
- [ ] Record every gate input, outcome, final decision, side-effect mode, and audit reference.
- [ ] Classify side-effect state as no side effect, packaged only, attempted, accepted, rejected, unknown, reconciled, or incident.
- [ ] Prevent chat, UI, API, backtest, and optimization workflows from bypassing live gates.

#### Reconciliation and incidents

- [ ] Implement broker-truth synchronization before live mutation.
- [ ] Implement reconciliation authority state transition machine.
- [ ] Implement retry guards and unknown-outcome handling.
- [ ] Create live discrepancy incidents and recovery context.
- [ ] Implement approval-cleared re-enable workflow.

#### Monitoring and reporting

- [ ] Monitor stale state, ingestion health, tool health, workflow timeout, incidents, latency, cost, notification failures, and live readiness.
- [ ] Generate live performance reports, execution reports, broker-truth snapshots, and audit evidence.
- [ ] Send live notifications through safe configured channels without secrets or private broker payload leakage.
- [ ] Support shadow execution and production-like comparison when real mutation is disabled.

#### Tests and acceptance

- [ ] Add config, session, gates, executor, reconciliation, monitoring, and error tests.
- [ ] Add fail-closed tests for missing enablement, approval, risk, kill switch, actor, and broker readiness.
- [ ] Add unknown outcome, retry guard, reconciliation discrepancy, incident, and re-enable tests.
- [ ] Accept only when Live is the only allowed route to broker mutation.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/live/configs.py` (Live configuration and environment loaders)
2. `tools/live/status.py` (Durable status and diagnostic snapshot structures)
3. `tools/live/gates.py` (Strict operator permission gate checks)
4. `tools/live/reconciliation.py` (Audits live positions against broker logs)
5. `tools/live/monitoring.py` (Real-time telemetry feeds analyzer)
6. `tools/live/actions.py` (Manual emergency override execution triggers)
7. `tools/live/recovery.py` (Failed network recover routines)
8. `tools/live/runtime.py` (The core session startup and shutdown manager)
9. `tools/live/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 11 — UI / API Gateway

**Source:** `11_ui_api(1).md`
**Target path:** `api/ + ui/`
**Phase objective:** Build the secure FastAPI gateway and Next.js UI surface after backend contracts are clear, exposing approved capabilities through validation, auth, typed clients, protected routes, streaming contracts, and governed write controls.

### Phase prerequisites

- [ ] Backend module public surfaces are contract-stable for the routes being exposed.
- [ ] Auth/authorization, route contracts, stream contracts, idempotency, pagination, and DTO rules are documented.

### Implementation checklist

#### Pre-handoff contract completion

- [ ] Complete route contracts, response envelopes, auth rules, idempotency behavior, pagination/filtering policy, measurable NFRs, and requirement-to-test traceability before broad implementation.
- [ ] Classify every route as public, protected, internal, migration-only, experimental, deprecated, optional, or deferred.
- [ ] Document HTTP, WebSocket, and SSE contract behavior.

#### FastAPI backend

- [ ] Create canonical entry point `api.main:app`.
- [ ] Implement app composition, route registration, middleware, lifecycle startup/shutdown, CORS, and health endpoint.
- [ ] Implement route groups for auth, settings, AI chat, strategies, SQX, backtest/simulator, risk, live, optimization, dashboard, docs, Edge Lab, data, and operator workflows.
- [ ] Implement Pydantic request/response models at the HTTP boundary.
- [ ] Route handlers may validate, authorize, delegate, and translate errors, but must not implement domain algorithms.

#### Auth, middleware, and safety

- [ ] Implement token verification, invalidation, operator principal extraction, and role enforcement.
- [ ] Implement secret-safe request metadata logging.
- [ ] Implement intent classification middleware where needed.
- [ ] Implement guarded-write preflight checks in the frontend as UX only; backend remains authoritative.
- [ ] Prevent direct frontend database writes or broker calls.

#### Streaming and clients

- [ ] Implement WebSocket/SSE managers for backtest logs, live sessions, optimization progress, AI chat, and operator events only after schemas are defined.
- [ ] Define auth, event schema, heartbeat, reconnect, backpressure, terminal error, and cleanup behavior for each stream.
- [ ] Implement typed frontend API clients, DTO validators, request helpers, trace headers, stale-response warnings, and telemetry hooks.

#### Next.js frontend

- [ ] Implement protected layouts, authentication pages, dashboard pages, workflow pages, and documentation screens.
- [ ] Build shared components, charts, forms, workflow panels, tables, settings screens, and chat UI.
- [ ] Render domain outputs without embedding trading, risk, simulation, optimization, research, or persistence algorithms.
- [ ] Add frontend contract drift detection through validators, snapshots, and tests.

#### Tests and acceptance

- [ ] Add route contract tests, auth tests, middleware tests, stream tests, DTO tests, and frontend tests.
- [ ] Add idempotency, pagination/filtering, authorization denial, stale response, and error translation tests.
- [ ] Accept only when gateway delegates domain logic and enforces governed write controls.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

**API (FastAPI):**
1. `api/dependencies.py` (DI containers and middleware injectors)
2. `api/middleware/__init__.py`
3. `api/middleware/redaction.py`, `api/middleware/intent.py`, `api/middleware/auth.py`
4. `api/routes/__init__.py`
5. `api/routes/auth.py`, `api/routes/settings.py`, `api/routes/chat.py`, `api/routes/strategies.py`, `api/routes/simulation.py`, `api/routes/risk.py`, `api/routes/live.py`, `api/routes/operator.py`
6. `api/app.py` (FastAPI app factory loader)
7. `api/main.py` (Production entry-point runner)

**UI (Next.js):**
1. `ui/src/lib/validators/` (DTO validation schemas matching backend types)
2. `ui/src/lib/api/` (Guarded-write preflight typed API fetch clients)
3. `ui/src/components/` (RADIX UI page components)
4. `ui/src/app/` (Next.js app layouts and routers)
      api/               # Typed API client wrappers
      validators/        # Client contract validation schemas
```

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 12 — Research / Edge Lab

**Source:** `12_research(1).md`
**Target path:** `tools/research/`
**Phase objective:** Implement sandboxed research and Edge Lab evidence generation for market behavior, edge discovery, feature engineering, leakage checks, statistical validation, market structure, and reports without granting execution authority.

### Phase prerequisites

- [ ] Data contracts are stable.
- [ ] Analytics functions required by Research are stable.
- [ ] Research first-slice public API contracts and resource limits are approved.

### Implementation checklist

#### Pre-handoff cleanup

- [ ] Resolve public API overlaps and exact public API contracts for first implementation slice.
- [ ] Define model schemas, standard envelope schemas, exact behavior/error tables, reproducibility metadata, artifact persistence rules, resource limits, and requirement-to-test traceability.
- [ ] Disable optional external-feed helpers when provider adapters are absent without breaking import.

#### Configuration and data prep

- [ ] Implement research configuration models for data prep, bootstrap/permutation/null models, market structure, mean reversion, trend persistence, session edge, and Edge Lab settings.
- [ ] Implement research-only data cleaning, enrichment, validation, preparation, and quality report models.
- [ ] Respect Data module ownership for production ingestion/provider contracts.

#### Features and leakage controls

- [ ] Implement returns, moving averages, volatility, range, momentum, Bollinger-style statistics, Hurst statistics, pivots, forward returns, MAE/MFE, and simple regime labels.
- [ ] Implement chronological splits, lookahead validation, and artifact masking before persistence.
- [ ] Implement core metric registry and normalized core metric profile creation.

#### Edge discovery and validation

- [ ] Implement mean reversion, trend persistence, session behavior, and null baseline studies.
- [ ] Implement null-model generation, bootstrap distributions, permutation testing, multiple-comparison corrections, percentiles, and thresholds.
- [ ] Implement market-structure profiles, calibration candidates, overrides, validation summaries, stability, robustness, and strategy-fit reports.

#### Unsupervised and reporting

- [ ] Implement PCA, clustering, cluster labels, cluster outperformance analysis, PCA risk-factor summaries, signal adaptation, and unsupervised insight reports where approved.
- [ ] Implement seasonality filters and result generation.
- [ ] Implement profile snapshots, dashboard summaries, scorecards, Markdown/JSON serialization, and multi-symbol reports.
- [ ] Expose analytics compatibility exports without taking analytics ownership.

#### Tests and acceptance

- [ ] Add config, data, features, leakage, metrics, studies, null models, structure, unsupervised, helpers, and reporting tests.
- [ ] Add leakage, multiple-comparison, small sample, missing data, non-stationary, outlier, and reproducibility tests.
- [ ] Accept only when research evidence remains advisory and cannot authorize execution, risk approval, or live signal policy.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/research/models.py` (Research report envelope definition schemas)
2. `tools/research/errors.py` (Exceptions for sample sizes and pipeline leaks)
3. `tools/research/features.py` (Mathematical feature engineering calculators)
4. `tools/research/leakage.py` (Checks features for future leakages)
5. `tools/research/stats.py` (Bootstraps, null models, and statistical significance)
6. `tools/research/seasonality.py` (Identifies time-of-day/day-of-week trends)
7. `tools/research/unsupervised.py` (Market regime clustering helpers)
8. `tools/research/reports.py` (SHA-256 validated PDF/Markdown compiler)
9. `tools/research/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Phase 13 — Conversation / AI Chat

**Source:** `13_conversation(1).md`
**Target path:** `tools/conversation/`
**Phase objective:** Implement governed AI conversation as a read-only evidence and draft-proposal layer with durable threads, memory, page context, prompt composition, provider streaming, CEO/planner routing, and strict no-execution boundaries.

### Phase prerequisites

- [ ] UI/API actor context and page context are available.
- [ ] Read-only tool evidence contracts are available.
- [ ] Provider configuration and no-mutation policy are approved.

### Implementation checklist

#### Capability contracts

- [ ] Document every public conversation capability before handoff.
- [ ] Classify each export as stable public API, internal helper, official callable tool, or experimental export.
- [ ] Define intended consumers, schemas, errors, side effects, authorization, idempotency, risk level, network behavior, persistence behavior, and stability.
- [ ] Define machine-readable error codes for validation, authorization, idempotency, concurrency, provider, persistence, configuration, cancellation, and internal failures.

#### Durable conversation services

- [ ] Implement thread lifecycle operations: create, list, read, rename, archive, restore, soft delete, export, and context updates.
- [ ] Persist redacted chat messages and schema mappings.
- [ ] Implement durable memory summaries and pinned-fact retrieval.
- [ ] Implement title generation and deterministic rolling summaries.
- [ ] Implement retention classes, expiration, archival, purge, legal hold, lifecycle audit, and policy detail.

#### Redaction and context

- [ ] Implement secret, email, and long-number redaction for persisted text.
- [ ] Implement page-context assembly from route, title, session, symbol, timeframe, DOM snapshot, and page intelligence inputs.
- [ ] Implement route-aware context builders for dashboard, data workspace, strategy detail, backtest detail, optimization, portfolio risk, live trading, operator workflow, and generic pages.
- [ ] Fail closed when authenticated actor context is missing or invalid.

#### Prompting and streaming

- [ ] Compose prompts from governance instructions, memory, pinned facts, page context, read-only tools, tool evidence, recent messages, and user prompt.
- [ ] Implement provider-aware streaming for OpenAI-compatible APIs, Google/Gemini, and local Ollama.
- [ ] Implement fallback token streaming when model execution is disabled, unavailable, blocked, or degraded.
- [ ] Implement cancellation and provider error handling.

#### CEO gateway and drafts

- [ ] Implement CEOChatGateway orchestration across planner, CEO memo generation, page context, read-only tool execution, optional research workflow routing, prompt building, model selection, streaming, metadata, and persistence.
- [ ] Implement read-only tool evidence inclusion and schema validation.
- [ ] Implement governed action draft records, persistence, lookup, listing, and retention classification.
- [ ] Do not allow conversation to execute live trades, risk approvals, strategy execution, backtests, optimization runs, or broker-affecting actions.

#### Tests and acceptance

- [ ] Add tests for service, config, retention, memory, context builders, prompt builder, stream manager, CEO gateway, and errors.
- [ ] Add redaction tests for secrets, email, long numbers, and private broker-like payloads.
- [ ] Add fail-closed tests for missing actor context, missing auth, provider failure, cancellation, persistence errors, and unsafe action requests.
- [ ] Accept only when conversation can produce evidence-backed answers and drafts but cannot mutate governed trading state.

### Target folder structure & creation order

The following structure is the expected implementation layout. Files must be created in this recommended sequential order to resolve internal imports cleanly:

#### Recommended File Creation Order

1. `tools/conversation/protocols.py` (AI Provider and model adapters definition)
2. `tools/conversation/errors.py` (Token limits and service degradation codes)
3. `tools/conversation/models.py` (Durable thread and message schemas)
4. `tools/conversation/persistence.py` (Session database repositories)
5. `tools/conversation/context.py` (Retrieves runtime context from other 12 modules)
6. `tools/conversation/prompt_builder.py` (Compiles prompts with user permissions)
7. `tools/conversation/providers/__init__.py`
8. `tools/conversation/providers/openai.py`, `tools/conversation/providers/gemini.py`
9. `tools/conversation/planner.py` (Planner routing and agent capability resolver)
10. `tools/conversation/gateway.py` (The streaming coordinator interface)
11. `tools/conversation/__init__.py`

### Phase acceptance gate

- [ ] All approved public contracts for this phase are documented before coding begins.
- [ ] All implemented public functions have typed schemas, deterministic errors, standard envelopes, and usage tests.
- [ ] All ownership boundaries from the source document are preserved.
- [ ] All pending/future/optional capabilities are disabled, staged, or fail-safe unless explicitly approved.
- [ ] Unit tests, integration tests where applicable, usage tests, import tests, and security/safety tests pass.
- [ ] The phase produces a short implementation report listing changed files, tests run, deferred items, and unresolved risks.

---

## Final Platform Acceptance Checklist

- [ ] All modules import without optional provider dependencies installed.
- [ ] All official tool registries expose only approved public functions.
- [ ] All standard envelopes are consistent across Utils, Data, Indicators, Strategy, Risk, Analytics, Trading, Simulation, Optimization, Live, UI/API, Research, and Conversation.
- [ ] All modules have deterministic error-code catalogs.
- [ ] All modules include usage tests that demonstrate correct caller behavior.
- [ ] All reports, manifests, journals, evidence packages, and artifacts are schema-versioned and reproducible.
- [ ] No module leaks secrets, credentials, private broker payloads, or approval packet internals into logs, metrics, reports, or chat memory.
- [ ] No module takes over another module's ownership silently.
- [ ] Risk fails closed when evidence is stale, missing, ambiguous, or unsafe.
- [ ] Live broker mutation is impossible unless all required live gates pass.
- [ ] Conversation can summarize, explain, route, and draft proposals, but cannot execute broker-affecting or approval-affecting actions.
- [ ] UI/API validates, authorizes, delegates, and translates errors without embedding domain algorithms.
- [ ] The project has a versioned roadmap marking each module as not started, contract drafting, implementation, test hardening, staging, or production-ready.

## Suggested Sprint Packaging

For each phase, split work into these sprint file packs:

```text
docs/planning/sprints/phase-XX-slice-YY/
  requirements.md      # WHAT and WHY
  blueprint.md         # HOW: files, steps, flows, functions, tests
  acceptance.md        # Definition of Done: specific and testable
  handoff-prompt.md    # Exact prompt to paste into the Builder
```

Recommended first slices:

- [ ] Phase 01 Slice 01: standard envelopes, errors, identity, time, paths, and logging.
- [ ] Phase 01 Slice 02: schema validation, settings, security, auth, event bus, notifications, observability.
- [ ] Phase 02 Slice 01: data contracts, normalized records, CSV/Parquet local sources, synthetic source, and manifests.
- [ ] Phase 02 Slice 02: cache/storage, SQLite scheduler state, update jobs, feed status, and staging adapters.
- [ ] Phase 03 Slice 01: indicator protocols, registry, capability matrix, SMA/EMA/ATR/ADR/RSI/Williams %R fixtures.
- [ ] Phase 04 Slice 01: strategy registry, config validation, TradeIntent contract, vectorized strategy runner.
- [ ] Phase 05 Slice 01: risk models, profiles, limits, sizing, admission review, fail-closed evidence behavior.
- [ ] Phase 07 Slice 01: trading route contract, validation, simulator route, request packaging, idempotency metadata.
- [ ] Phase 08 Slice 01: `run_backtest` contract, orchestrator, tick engine skeleton, journal, canonical FX happy path.
- [ ] Phase 06 Slice 01: canonical analytics reports and core metrics from simulation fixtures.
- [ ] Phase 09 Slice 01: parameter sweep packaging, grid/random search adapter contract, robustness request packaging.
- [ ] Phase 10 Slice 01: live config, session status, gates, no-mutation dry-run/shadow runtime.
- [ ] Phase 11 Slice 01: API health, auth skeleton, typed DTOs, and one read-only route group.
- [ ] Phase 12 Slice 01: research config, data prep, leakage checks, core metrics, and one edge study.
- [ ] Phase 13 Slice 01: conversation service, redaction, memory summaries, prompt builder, streaming fallback.

## Source Traceability Notes

This plan intentionally preserves the following source-level boundaries:

- Phase 01 comes from `01-utils(3).md` and targets `tools/utils/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 02 comes from `02-data(2).md` and targets `tools/data/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 03 comes from `03-indicator(1).md` and targets `tools/indicators/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 04 comes from `04-strategy(1).md` and targets `tools/strategies/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 05 comes from `05-risk(1).md` and targets `tools/risk/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 06 comes from `06_analytics(1).md` and targets `tools/analytics/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 07 comes from `07_trading(1).md` and targets `tools/trading/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 08 comes from `08-simulation(1).md` and targets `tools/simulation/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 09 comes from `09_optimization(1).md` and targets `tools/optimization/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 10 comes from `10_live(1).md` and targets `tools/live/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 11 comes from `11_ui_api(1).md` and targets `api/ + ui/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 12 comes from `12_research(1).md` and targets `tools/research/`. Its implementation checklist summarizes the source requirements without copying the full source document.
- Phase 13 comes from `13_conversation(1).md` and targets `tools/conversation/`. Its implementation checklist summarizes the source requirements without copying the full source document.

End of plan.
