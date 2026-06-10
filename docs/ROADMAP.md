# HaruQuantAI Roadmap

Purpose: this file records current project status, sprint scope, tasks, acceptance checklist, decisions, risks, blockers, next actions, and completed work.

## Current Project Status

Status: documentation refactor in progress after Sprint 000 documentation bootstrap.

Production code is not being changed by this documentation refactor. Existing implementation code in `api/`, `tools/`, `agentic/`, `data/`, `ui/`, `tests/`, and `scripts/` remains reference/current repository material until the owner decides how it should be treated for Sprint 001.

## Current Sprint: DOC-LEAN Lean Documentation Refactor

### Goal

Replace the enterprise-style documentation structure with four active documents and one root AI/Builder guide:

- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `AGENTS.md`

### Scope

- Consolidate useful old documentation into the lean active docs and root AI guide.
- Update root AI/onboarding files to point to the lean documentation model.
- Remove or archive old docs after migration.
- Preserve decisions, risks, open questions, safety rules, architecture contracts, module requirements, and Builder workflow rules.

### Out Of Scope

- Production source code changes.
- Application behavior changes.
- New dependencies.
- Live broker calls or live trading actions.
- New business rules, risk limits, or unapproved architecture decisions.

### Tasks

- [x] Perform dry run and receive approval.
- [x] Create lean active docs.
- [x] Update `README.md` and `AGENTS.md`.
- [x] Remove old active docs after content migration.
- [x] Check for old references.
- [ ] Report final docs tree and validation results.

### Acceptance Criteria

- [x] The active docs and root AI guide exist and are useful without chat history.
- [x] No active documentation file still says the old planning folder is the main source of truth.
- [x] No active documentation file still requires four-file sprint packs.
- [x] Root AI/onboarding files point to the active docs.
- [x] Old useful content is migrated, summarized, or intentionally archived.
- [x] Final active docs under `docs/` are reduced to the lean documentation model unless archive exceptions are reported.

### Files Expected To Change

- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `README.md`
- `AGENTS.md`
- old docs and folders under `docs/` removed after migration

### Risks

- Losing detailed Utils requirements during consolidation.
- Leaving old prompt-library files as competing sources of truth.
- Breaking existing docs validator if it expects the old structure.

### Done Log

- Dry run completed and approved with exact phrase `APPROVED: EXECUTE`.
- Five active docs were created and old active docs were removed after consolidation.
- Root onboarding/AI files were updated for the lean documentation model.
- Module-order details were removed from `AGENTS.md`; product/module sequencing now lives in the active product docs.
- Mixed Utils requirements were split across active docs while preserving detailed `[ ]` implementation checklists for Sprint 001 tracking.
- Utils requirements were integrated into the new document structure by removing copied legacy numbering and duplicate summary headings while preserving tickable implementation items.
- Strategy source requirements were revised from the external audit to mark the document revision-required before Builder handoff, add draft public capability contracts, clarify external-module ownership boundaries, resolve the canonical strategy lookahead error code, and record traceability/readiness blockers.
- Strategy source requirements were revised from the follow-up audit to tighten purpose and ownership boundaries, add a boundary diagram, require exact public API signatures, versioned schemas, error decision tables, measurable SLO approvals, dependency/concurrency/clock-drift failure modes, missing strategy error codes, stronger tests, and active module summary synchronization.
- Strategy source requirements were revised from the production-readiness audit to generate stable `REQ-STRAT-*` IDs, add public Pydantic-style schema baselines, define read-only execution-state query/snapshot contracts, add provisional v1.0 NFR baselines, clarify atomic vectorized-batch failure semantics, add partial-data and long-batch clock-drift edge cases, require property-based no-lookahead tests, schema-align usage examples, add a family-level traceability matrix, and synchronize the active module summary.
- Data source-requirements handoff audit was integrated as a documentation refinement: per-tool contract expectations, phase slices, source promotion criteria, optional dependency behavior, scheduler ambiguity fixes, response-contract anchors, and active module summary synchronization.
- Data source-requirements second handoff audit was integrated as a documentation refinement: precision policy contract, response schema version lock, symbol pagination, historical volume modes, internal scheduler scope, already-running job behavior, cache race handling, database pool defaults, feed backpressure and clock drift, resilience edge cases, performance/load/soak/chaos tests, load-test sign-off reporting, and active module summary synchronization.
- Data source-requirements production-grade audit was integrated as a documentation refinement: concrete Data engineering benchmark profile, concurrent storage path write locking, checkpoint granularity, backfill chunk limit, ownership mapping, no-lookahead alignment mechanism, inline manifest/schema-linking contracts, fallback metadata disclosure, pending-RFC guardrail, additional error codes, scheduler chaos test, storage concurrency test, and active module summary synchronization.
- Analytics source-requirements handoff audit was integrated as a documentation refinement: official tool catalog, metric definition catalog, report criticality, adapter mappings, dashboard payload classification, FX/schema blockers, warning/quality-flag catalog, requirement-to-test traceability, and active module summary synchronization.
- Analytics architecture audit was integrated as a documentation refinement: official versus internal surface separation, reference-only low-level metric inventory, metric ownership blocker, request-ID validation, file-loading boundary, monetary precision blocker, measurable NFR placeholders, additional edge cases/tests, usage example labeling, and Builder handoff Definition of Done.
- Analytics follow-up architecture audit was integrated as a documentation refinement: non-binding evidence wording, private canonical metric-kernel mandate, fail-closed adapters, canonical error envelope, deterministic numeric/non-finite policy, cache boundary and concurrency requirements, monetary precision mandate, named ADR handoff gates, partial-report example, and active module summary synchronization.
- Trading source-requirements handoff audit was integrated as a documentation refinement: ownership boundaries, public tool contract matrix requirements, standard envelope expectations, live mutation semantics, measurable NFRs, edge cases, test coverage gaps, and active module summary synchronization.
- Trading source-requirements second refinement was integrated: exact API contract appendix requirements, live credential/session boundary, redaction interface expectations, default timeout/freshness/payload/readiness limits, readiness and concurrency error behavior, credential-expiry edge cases, broker-simulator failure-injection tests, concrete failure-path envelopes, and active module summary synchronization.
- Trading source-requirements third refinement was integrated: Decimal precision and rounding policy, canonical idempotency serialization and hashing requirements, timezone-aware broker-time handling, persistence dependency direction, rate-limit boundary wording, reconciliation snapshot default, proposed readiness SLO pending approval, DST/network-partition/resource-exhaustion edge cases, property-based test requirements, unknown-outcome reconciliation example, shadow-trading read-only guarantee, and active module summary synchronization.
- UI/API source-requirements handoff audit was integrated as a documentation refinement: route contract requirements, public/internal/stability classification, operator event stream auth clarification, domain delegation wording, standard envelope and streaming contract requirements, pagination/filtering/versioning promotion to required handoff scope, measurable NFRs, edge cases, test gaps, usage examples, and active module summary synchronization.
- UI/API follow-up audit was integrated as a documentation refinement: pre-implementation draft status, contract-definition checklist, pre-handoff blockers, glossary, request-flow sequence diagram, route group contract placeholders, service-client delegation protocol requirements, standard error code catalog, baseline versioning/pagination/idempotency/NFR proposals, health-only operator stream restrictions, contract definition tests, negative preflight and idempotency replay examples, and active module summary synchronization.
- Live source-requirements handoff audit was integrated as a documentation refinement: public live tool contract requirements, canonical live gate order, package-only versus broker-mutation semantics, side-effect modes, approval-context requirements, measurable NFRs, edge cases, missing tests, pre-production required decisions, and active module summary synchronization.
- Live source-requirements follow-up audit was integrated as a documentation refinement: terminology/data definitions, retry-safety taxonomy, explicit policy-matrix requirements, removal of audit-write emergency bypass wording, diagnostic-only gate constraints, broker adapter contract requirements, proposed NFR targets marked pending approval, malformed broker response handling, concurrency contract requirements, pending-decision acceptance table, and active module summary synchronization.
- Live source-requirements security/rate-limit audit was integrated as a documentation refinement: strict middleware/gateway wording, testable metadata propagation wording, `retry_after_seconds`, route-gated kill-switch example, mandatory broker communication security gate, rate-limit/backoff requirements, partial-network-partition edge cases, chaos/security/rate-limit tests, UI/dashboard/websocket out-of-scope clarification, and active module summary synchronization.
- Optimization source-requirements handoff audit was integrated as a documentation refinement: scope tiers, public tool contract expectations, repository ownership boundaries, canonical final-decision enum guidance, production-blocking decision matrix, usage/error examples, missing tests, and active module summary synchronization.
- Optimization source-requirements follow-up audit was integrated as a documentation refinement: public/internal capability separation, dry-run semantics by capability type, `BacktestExecutionAdapter` interface ownership, explicit reproducibility fields, `search_method` requirements, provisional NFR baselines, remote repository failure handling, dry-run/network-failure tests, usage examples, pending decision matrix, and active module summary synchronization.
- Optimization source-requirements architectural audit was integrated as a documentation refinement: repository `Protocol`/ABC and DI boundaries, concrete repository implementation exclusions, JSON serialization policy, omitted `dry_run=True` default, testable `OPT_*` failure outcomes, public API compatibility rules, monotonic timeout enforcement, cache-stampede and sampler-unavailable handling, chaos/DST tests, cache-hit and execution-handoff examples, owner-assigned decision matrix, canonical enum/error-code appendix, and active module summary synchronization.
- Simulation source-requirements handoff audit was integrated as a documentation refinement: revision-required status, Phase 1 FX slice guardrails, public capability contract requirements, traceability gates, external interface blockers, request/security edge cases, import-safety tests, executable usage-example expectations, and active module summary synchronization.
- Simulation source-requirements follow-up refinement was integrated: document version table, Phase 1 out-of-scope clause, draft `run_backtest` and `SimTrader` contract scaffolds, Deferred Scope Register, decision log, limit-order queue/gap/FX precedence clarifications, provisional performance-target wording, Phase 1 edge/error matrix, Phase 1 test suite, executable usage-example requirements, and active module summary synchronization.
- Simulation strict architect audit was integrated: pending/draft contract blocker wording, live-adapter import boundary, OS-resource ownership exclusion, versioned `SimTrader` candidate method names, feature-store disabled-by-default behavior, encryption-at-rest requirements, production-realistic checklist gate, deterministic unhandled-error mapping, memory-limit approval blocker, DST/session ambiguity handling, concurrent manifest-read edge cases, fault-injection tests, queued/diagnostic-failed example requirements, and active module summary synchronization.
- Risk source-requirements handoff audit was integrated as a documentation refinement: revision-required status, export classification requirements, official tool contract requirements, portfolio-under-risk adapter boundaries, kill-switch non-mutation wording, missing validation/test requirements, pending production decision matrix, and active module summary synchronization.
- Risk source-requirements second refinement was integrated: deterministic policy-engine boundary, transitional compatibility/facade wording, private-surface expectations, benchmark scenario table, default payload-size limit, missing-config edge case, response-envelope examples, and safe fallback requirements for unresolved `RISK-PEND-*` decisions.
- Risk source-requirements third architectural audit was integrated: `BLOCKED: NOT READY FOR HANDOFF` status, fail-closed axiom, document change log, long-term market-data exclusion, strict `__all__` export registry, transitional facade v2.0 migration/reapproval requirement, time injection, strict Decimal/Pydantic serialization, non-PSD correlation handling, payload depth/list limits, trace propagation, timezone/payload edge cases, time/payload parsing tests, and active module summary synchronization.
- Conversation source-requirements handoff audit was integrated as a documentation refinement: revision-required status, public capability contract expectations, stream event schema requirements, repository/persistence contracts, retention configuration blockers, read-only tool permission requirements, concurrency/idempotency requirements, measurable NFRs, missing tests, and active module summary synchronization.
- Conversation source-requirements second refinement was integrated: formal handoff blocker checklist, `ConversationRepository` contract requirements, stream event contract appendix requirements, configuration reference requirements, machine-readable error-code requirements, auth context clarification, request-id/concurrency/lifecycle race requirements, glossary, usage-example gaps, and active module summary synchronization.
- Conversation source-requirements third refinement was integrated: prerequisites/external-dependencies posture, provisional baseline policy, capability contract table scaffold, external permission authority clarification, `user_id` trust boundary, fallback response schema requirements, proposed concurrency/title/follow-up/backpressure baselines, rate-limit/database-pressure edge cases, property-based redaction tests, mid-stream provider chaos tests, cancellation/backpressure examples, no-hardcoded-configuration directive, and active module summary synchronization.
- Research source-requirements handoff audit was integrated as a documentation refinement: revision-required status, advisory-only boundaries, public API contract requirements, model schema requirements, canonical error behavior, reproducibility metadata, network-helper behavior, report persistence rules, duplicate API clarifications, missing tests, and active module summary synchronization.
- Research source-requirements second refinement was integrated: standard research envelope schema requirements, per-callable error-pattern selection, cleaning strategy enums, leakage report fields, seed propagation, optional provider classification, atomic report writes, measurable resource-limit placeholders, usage failure examples, glossary/checklist requirements, and active module summary synchronization.
- Research source-requirements third refinement was integrated: unresolved API overlap blockers, inline standard research envelope shape, behavior/error table requirements, provisional insufficient-sample error guidance, market-data adapter ownership clarification, internal/compatibility export stability wording, cleaning default approval blocker, SHA-256 artifact/config hash requirements, HTTP 429 and clock-drift edge cases, property-based or generated rolling-window tests, nested masking robustness tests, robust envelope usage example, and active module summary synchronization.
- Indicator source-requirements handoff audit was integrated as a documentation refinement: formula-table blockers, cache ownership boundaries, machine-readable capability matrix requirements, explicit no-lookahead metadata, benchmark/SLO alignment, deprecation timelines, numeric edge semantics, usage error examples, audit-integrity approval blockers, and active module summary synchronization.
- Indicator source-requirements follow-up audit was integrated as a documentation refinement: implementation pre-requisites moved to the top of the requirement, strict type-contract expectations, injected adapter I/O boundaries, proposed default resource limits, cache backend degradation policy, timezone database boundary behavior, release-signing ownership clarification, and active module summary synchronization.

## Next Planned Sprint: 01 Utils/Foundation

Status: implementation started.

### Goal

Build the Utils foundation first: settings, logging, redaction, time helpers, identity/traceability, error helpers, event bus, notifications, health, metrics, and common safety utilities.

### Scope

Expected scope includes:

- Standard response envelope.
- Public registry and API control.
- Official low-risk validation tools and approved redaction tools.
- Error object helpers and deterministic error-code mapping.
- Request/workflow/correlation/causation/event/idempotency IDs.
- UTC clock helpers and monotonic execution timing.
- Safe path helpers.
- Lazy dataframe helpers.
- Diagnostic-only OHLCV data-quality validation.
- Schema/contract validation.
- Redaction, hashing, and restricted encryption/decryption support helpers.
- Runtime settings with deterministic source precedence.
- Auth context and deny-by-default authorization helpers.
- Runtime settings.
- Event bus/pub-sub foundation.
- Error routing and alert routing.
- Email/Telegram notification abstraction.
- Desktop notification routing contract if approved for scope.
- Observability, metrics, health snapshots, clock-drift diagnostics, and circuit-breaker helpers.
- Tests for documented behavior.

### Out Of Scope

- Production trading logic.
- Data module implementation.
- Strategy/risk/trading/live implementation.
- Live broker calls.
- New dependencies without approval.

### Readiness Issues

- Decide whether existing implementation code is reference-only, partially adopted, or authoritative for Sprint 001.
- Confirm minimal API/data model contract depth for Sprint 001/002.
- Confirm any dependency additions or avoid them.

### Implementation Priority

- [ ] Implement `tools/__init__.py` first to establish a clean side-effect-free package.
- [ ] Implement `tools/utils/logger.py` before modules that need production logging.
- [ ] Implement `tools/utils/standard.py` before official AI tools.
- [ ] Implement `tools/utils/errors.py` before deterministic failure behavior is needed.
- [ ] Implement `tools/utils/identity.py` before request/workflow/event trace helpers are needed.
- [ ] Implement `tools/utils/normalization.py` before data quality, settings, freshness checks, and event timestamp validation.
- [ ] Implement `tools/utils/paths.py` before settings and artifact helpers.
- [ ] Implement `tools/utils/security.py` before logging, settings, events, notifications, and audit-safe behavior are finalized.
- [ ] Implement `tools/utils/settings.py` before adapters and runtime configuration consumers.
- [ ] Implement `tools/utils/auth.py` before tool allowlists and side-effect permission checks.
- [ ] Implement `tools/utils/event_bus.py` before error routing and notification routing.
- [ ] Implement `tools/utils/error_routing.py` before notification routing.
- [ ] Implement `tools/utils/notifications.py` before alert delivery is attached to workflows.
- [ ] Implement `tools/utils/observability.py` before production health gates are accepted.
- [ ] Implement `tools/utils/dataframe_tools.py` after normalization and errors.
- [ ] Implement `tools/utils/schema_validation.py` after standard, errors, normalization, security, auth, and observability foundations.
- [ ] Implement `tools/utils/data_quality.py` after standard, errors, normalization, dataframe tools, and schema validation.
- [ ] Implement `tools/utils/__init__.py` only after modules exist and public names are finalized.
- [ ] Implement unit tests for every module.
- [ ] Implement usage examples for official AI tools and production primitives.
- [ ] Run CI quality gates before accepting the implementation.

---

### Sprint 001 Implementation Roadmap

1. Complete the lightweight public registry and official AI validation tools.
2. Split legacy mixed utility modules into the target module names from `01-utils.md`.
3. Keep external providers disabled by default and use in-process/no-op adapters only.
4. Add focused tests for every new target module.
5. Align coverage configuration so the Utils coverage gate measures `tools.utils` only.
6. Remove or formally approve remaining compatibility imports from `common.py` and `validators.py`.
7. Checkmark `docs/source-requirements/01-utils.md` only when implementation and validation evidence exists.
8. Re-run docs, unit, usage, lint, and coverage gates before Sprint 001 acceptance.

### Sprint 001 Current Progress

- [X] Added target module files for paths, dataframe tools, data quality, schema validation, auth, event bus, error routing, notifications, and observability.
- [X] Moved official schema validation registry entries to lightweight `tools.utils.schema_validation`.
- [X] Moved official OHLCV quality registry entry to lazy `tools.utils.data_quality`.
- [X] Added distinct native redaction helpers and official redaction tool wrappers.
- [X] Made logger file sinks opt-in through `configure_logging`.
- [X] Added `validate_tool_response_schema`.
- [ ] Add focused unit tests for every new target module.
- [ ] Resolve full coverage gate.
- [ ] Decide whether legacy `common.py` and `validators.py` compatibility imports are approved for Sprint 001.
- [ ] Finish production-required Event Bus retry/backpressure/concurrency tests.
- [ ] Finish production observability and notification readiness tests.

### Sprint 001 Done Log

- Created `TOOL_FUNCTION_STANDARDIZATION_AUDIT.md` for the Utils standardization slice.
- Added target Utils modules and wired the public registry to the new official tool paths.
- Verified behavior with `pytest tests/unit/tools/utils tests/usage/tools/utils.py --no-cov` on 2026-06-08: 130 passed.
- Recorded coverage gate as still failing because the current coverage run reports the full repository total at 2.43% despite the focused tests passing.

---

### Acceptance And Definition Of Done

- [ ] The target folder structure exists.
- [ ] `tools/__init__.py` exists and is side-effect free.
- [ ] `tools/utils/__init__.py` exposes only approved public names.
- [ ] Public registry documentation classifies every official AI tool and support helper.
- [ ] Internal helpers are not accidentally exported.
- [ ] No compatibility shims, aliases, fallback import modules, or duplicate wrapper modules exist.
- [ ] Every Python file has a file-level docstring.
- [ ] Every public function/class has a useful docstring.
- [ ] Public functions and methods are typed.
- [ ] Inputs are validated where appropriate.
- [ ] Errors are explicit and deterministic.
- [ ] Official tools return standard envelopes.
- [ ] Support helpers return clear native values or raise typed exceptions.
- [ ] No production `print()` calls exist.
- [ ] No secrets are logged.
- [ ] File logging is explicit, safely scoped, rotating, and retention-limited when enabled.
- [ ] Local development logging supports colorized human-readable console output in the approved format.
- [ ] Official tools include metadata constants.
- [ ] Official tools include side-effect flags.
- [ ] Official tools accept `request_id`.
- [ ] Official tools include `execution_ms`.
- [ ] Official tools use deterministic error codes.
- [ ] Official tools pass `validate_tool_response_schema`.
- [ ] Importing `tools.utils` does not import pandas, cryptography, dotenv, broker SDKs, notification clients, pub/sub clients, Prometheus exporters, or network clients unless the specific feature is used.
- [ ] Dataframe helpers use lazy pandas imports or `TYPE_CHECKING` guards.
- [ ] Missing pandas fails only when dataframe helpers are called, with a clear configuration/dependency error.
- [ ] `validate_ohlcv_quality` is stateless, diagnostic-only, and does not repair, resample, persist, enrich, or mutate input data.
- [ ] Data repair and cleaning workflows are explicitly excluded from `tools.utils` and reserved for `tools.data`.
- [ ] Validators accept supported enum values and strings where practical, then normalize to canonical JSON-safe strings.
- [ ] Public responses, metadata, audit records, logs, and serialized payloads never expose enum objects directly.
- [ ] Future domain-specific errors inherit from `HaruQuantError` or expose a compatible `code` attribute.
- [ ] Standard response builders can map `HaruQuantError` subclasses generically without hardcoding every future domain error.
- [ ] Auth helpers deny by default and enforce tool allowlists.
- [ ] Event Bus idempotency storage is bounded by TTL and maximum cache size.
- [ ] Event Bus idempotency storage uses compact metadata rather than full event payloads by default.
- [ ] Event Bus queue policies are explicit and production critical workflows default to fail-fast behavior.
- [ ] Event Bus publish, subscribe, unsubscribe, retry, and dead-letter paths are thread-safe and/or async-safe.
- [ ] Notification routing, throttling, deduplication, and circuit-breaker state are thread-safe and/or async-safe.
- [ ] Queue-full publishing returns deterministic `QUEUE_FULL` or `BACKPRESSURE_EXCEEDED` diagnostics.
- [ ] External notification adapters have circuit breakers.
- [ ] External pub/sub adapters have circuit breakers.
- [ ] Prometheus-compatible metrics include circuit-breaker state, queue depth, idempotency cache size, backpressure count, notification failures, and clock drift.
- [ ] Health checks include clock-drift monitoring or explicit no-op status.
- [ ] Schema validation errors include deterministic invalid-field paths.
- [ ] Official schema validation errors include bounded `invalid_fields` diagnostics where practical.
- [ ] Schema validation resource limits prevent unbounded CPU, memory, and response sizes.
- [ ] Redaction denylist and audited allowlist behavior is implemented and tested.
- [ ] Notification templates support markdown and plain-text fallback rendering.
- [ ] Notification templates render from sanitized data transfer objects rather than raw event payloads.
- [ ] Tests prove no sensitive values leak through logs, events, notifications, metrics, dead-letter diagnostics, schema errors, or health checks.
- [ ] Unit tests exist for every module.
- [ ] Official tools have schema compliance tests.
- [ ] Official tools have metadata tests.
- [ ] Invalid input tests exist.
- [ ] Edge case tests exist.
- [ ] Security tests verify redaction and no secret leakage.
- [ ] Data-quality tests cover realistic OHLCV defects.
- [ ] Coverage is at least 80%.
- [ ] Usage examples exist for official AI tools.
- [ ] Usage examples use realistic inputs.
- [ ] Usage examples show success and error handling.
- [ ] Usage examples use `request_id` where applicable.
- [ ] Black passes.
- [ ] isort passes.
- [ ] Flake8 passes.
- [ ] mypy passes.
- [ ] pytest passes.
- [ ] Coverage gate passes.
- [ ] Full-project quality gate passes.
- [ ] Documentation covers Event Bus backpressure, idempotency, circuit breakers, clock drift, schema field paths, and redaction allowlist governance.
- [ ] Documentation includes production readiness checklists, operational runbooks, dashboard review checklists, and compatibility review notes.
- [ ] No unresolved open questions remain for the baseline production-ready utils module.

---

### Planned Quality Gates

```bash
black tools tests
isort tools tests
flake8 tools tests
mypy tools tests
pytest tests/unit/tools/utils tests/usage/tools/utils --cov=tools.utils --cov-fail-under=80
```

Required full-project gate:

```bash
black .
isort .
flake8 .
mypy tools tests
pytest --cov=tools --cov-fail-under=80
```

---

### Final Implementation Guidance

Build the module in small slices. Keep low-level helpers native, typed, deterministic, documented, and easy to test. Use official AI tool envelopes only where agent/workflow calls need standardized responses and metadata. Keep external dependencies lazy and adapter-based. Treat auth, redaction, event routing, notifications, metrics, and health snapshots as production infrastructure that must fail safely, expose bounded diagnostics, and never leak secrets.

Do not check off completion boxes in `docs/source-requirements/01-utils.md` until implementation and validation evidence exists.

## Decisions Log

### DEC-001 Project Name

Decision: project name is **HaruQuantAI**.

### DEC-002 Project Memory

Decision: project memory lives in durable files, not chat.

### DEC-003 Rebuild Style

Decision: HaruQuantAI is a clean-room rebuild that preserves important functionality and safety behavior while adding new product behavior.

### DEC-004 Product Scope

Decision: product scope includes tools, API, UI, data, live, research, and conversation surfaces.

### DEC-005 Old Material Authority

Decision: old catalog, docs, tests, and examples are reference material only unless explicitly adopted later.

### DEC-006 Module Build Order

Decision: build order is Utils, Data, Indicator, Strategy, Risk, Analytics, Trading, Simulation, Optimization, Live, UI/API Gateway, Research, Conversation.

### DEC-007 Launch-Critical Integrations

Decision: MT5 and SQLite are launch-critical integrations.

### DEC-008 Launch Notification Channels

Decision: email and Telegram are launch notification channels.

### DEC-009 Deferred Currency Strength Endpoint

Decision: `/api/dashboard/currency-strength` is deferred.

### DEC-010 Backend Entry Point

Decision: backend canonical entry point is `api.main:app`.

### DEC-011 Chat Draft Governance

Decision: chat action drafts use governance separate from execution approvals.

### DEC-012 Idempotency

Decision: deterministic idempotency is required from the beginning where financial side effects are possible.

### DEC-013 Sprint 000 Documentation Only

Decision: Sprint 000 was documentation-only.

### DEC-014 Auth Baseline

Decision: auth baseline is API-gateway-enforced authentication plus RBAC/action-level authorization, with service accounts for internal calls and human approval for governed actions.

### DEC-015 CI Baseline

Decision: CI baseline should include docs checks, Markdown quality checks, Python format/lint/type/security/unit gates, UI lint/build gates when UI exists, secret scanning, and contract tests as soon as contracts exist.

### DEC-016 Performance Targets

Decision: initial performance targets are engineering baselines, not business SLAs.

### DEC-017 Dependency Management

Decision: dependency management uses Python packaging metadata in `pyproject.toml`, Python environment pins in `requirements.txt` with `uv.lock`, and npm workspaces/lockfile for `ui/`.

### DEC-018 Lean Documentation Model

Decision: active project documentation is consolidated into three files under `docs/`: `PROJECT.md`, `ARCHITECTURE.md`, and `ROADMAP.md`.

Reason: owner requested a lean one-person-project documentation model.

### DEC-019 Single AI/Builder Guide

Decision: merge redundant Codex-specific and Builder-specific guidance into root `AGENTS.md`.

Reason: the files duplicated agent, Codex, and Builder operating rules. A single root instruction file reduces drift.

### DEC-020 Analytics Metric Kernel Ownership

Decision: Analytics owns canonical metric kernels as private/internal implementation details consumed through stable, versioned official tools and report interfaces.

Reason: owner-directed Analytics audit required one definitive metric ownership model and removed ambiguity between public tools, internal kernels, compatibility aliases, deprecated exports, and reference-only historical names.

### DEC-021 Analytics Monetary Precision

Decision: canonical Analytics monetary sums, cost aggregation, and base-currency aggregation use `Decimal`; derived ratios may use deterministic `float64` arithmetic only where exact decimal arithmetic is not appropriate, with documented tolerance in configuration, tests, and report metadata.

Reason: owner-directed Analytics audit required a definitive monetary precision mandate for report hashes, monetary sums, base-currency conversion, portfolio aggregation, and derived ratios.

### DEC-022 Risk Default Limit Values

Decision: the named default limit fractions `var_cap_frac = 0.10`, `es_cap_frac = 0.15`, `delta_var_cap_frac = 0.02`, `delta_es_cap_frac = 0.03`, `max_margin_used_frac = 0.50`, `warning_utilization_frac = 0.90`, `max_currency_exposure_frac = 0.20`, and `max_single_rc_frac = 0.10` are promoted to named, overridable requirements in `05-risk.md`. These are documentation requirements; they remain **Pending live-use approval** per `PDEC-002`.

Reason: audit revealed these values were present in implementation but absent from requirements documentation.

### DEC-023 Canonical Hard-Limit Rule Keys

Decision: the canonical rule key identifiers `invalid_equity`, `portfolio_var_cap`, `portfolio_es_cap`, `delta_var_cap`, `delta_es_cap`, `margin_cap`, `currency_weight_cap`, `single_rc_cap`, `cluster_var_cap`, `cluster_es_cap`, `breach_count_halt`, and `drawdown_halt` are recorded in `05-risk.md` with their default-active status and trigger conditions. Every `LimitEvent` shall carry the exact canonical `rule_key` string.

Reason: audit found the mechanisms were covered but rule key names and the default-active table were absent, making it impossible for Builders to wire deterministic error events.

### DEC-024 Simulation Risk Integration Hook Contracts

Decision: `08-simulation.md` §1.16.1 defines the mandatory simulation risk integration hooks: per-frame `PortfolioState` build and `RiskSnapshot` generation, pre-trade `GovernanceEngine.pre_trade_review` gate, and post-trade `GovernanceEngine.post_trade_review` re-evaluation. §1.16.2 defines the optional simulator-only tiered-margin policy ($500k at 1:1000, excess at 1:500, FX and XAUUSD only). `11_ui_api.md` Simulator API section defines the `risk_snapshot.summary` eight-field compact schema exposed on the `/advance` and `/positions` endpoints.

Reason: audit found the hook call sites, post-trade re-evaluation, tiered-margin policy, and `risk_snapshot.summary` field list were absent from the docs, blocking clean Builder implementation without re-specifying risk math in the simulation engine.

## Proposed Decisions Pending Approval

| ID | Proposed decision | Why pending |
|---|---|---|
| PDEC-001 | Chat and regulated artifact retention policy. | Compliance impact. |
| PDEC-002 | Risk threshold defaults. | Numeric trading policy must be approved before live use. |
| PDEC-003 | Event bus implementation phases. | Needs reliability and deployment input. |
| PDEC-004 | New service-tool catalog format. | Needs implementation repo structure. |
| PDEC-005 | SQLite production duration. | Depends on concurrency and deployment targets. |

## Blockers

| ID | Blocker | Impact | Owner |
|---|---|---|---|
| BLK-001 | First milestone depth for all 13 modules is not defined. | Blocks sprint/release scope. | Owner/Architect |
| BLK-002 | First-release instruments, symbols, timeframes, and account modes are not defined. | Blocks Data, Risk, Simulation, Trading tests. | Owner |
| BLK-003 | Action-level mutation/governance matrix is not finalized. | Blocks safe API/data write implementation. | Owner/Architect |
| BLK-004 | First release phase is not selected. | Blocks Live, Risk, deployment, security gates. | Owner |
| BLK-005 | Minimum API/data model contract for Sprint 001/002 is not approved. | Blocks contract tests and early implementation acceptance. | Architect |
| BLK-006 | Existing repo adoption status is not decided. | Blocks clean Sprint 001 ownership. | Owner/Architect |
| BLK-007 | Live execution schema, idempotency store, reconciliation persistence, approval action matrix/quorum, kill-switch policy, broker adapter contracts, stale thresholds, timeout limits, concrete NFR targets, rate-limit/backoff behavior, queue/concurrency behavior, audit durability, mandatory broker communication security profile, and restart/recovery objectives are not approved. | Blocks Live Builder handoff and production live broker mutation. | Owner/Architect |
| BLK-008 | Conversation public capability contracts, machine-readable error codes, stream event schemas, fallback response schema, `ConversationRepository`/persistence behavior, production retention policy, configuration reference values, read-only tool permission authority, auth context flow, concurrency/idempotency behavior, concrete NFR targets, focused tests, and traceability matrix are not approved. | Blocks Conversation Builder handoff and production reliance on chat as a safety boundary. | Owner/Architect |
| BLK-009 | Risk export classifications, official tool contracts, stable requirement IDs, portfolio-under-risk ownership, private/public export mapping, transitional facade v2.0 migration/reapproval, benchmark acceptance, time-provider policy, strict Decimal/Pydantic serialization behavior, payload depth/list limits, non-PSD correlation handling, double-spend owner, fractional Kelly multiplier, stressed lookback policy, crisis reference source, first heavy-tailed VaR distribution, and Gaussian VaR waiver policy are not approved. | Blocks Risk Builder handoff and production live risk implementation. | Owner/Architect |
| BLK-010 | Research public API overlaps, public API contracts, model schemas, standard envelope schema/status/error enums, exact behavior/error tables, canonical error taxonomy, cleaning strategy enums/defaults, leakage report schema, seed propagation rules, SHA-256 reproducibility metadata, optional provider behavior, report persistence rules, measurable resource limits/reference hardware, usage failure paths, advisory-only boundaries, duplicate API clarifications, and requirement-to-test traceability are not approved. | Blocks Research Builder handoff and production reliance on research artifacts. | Owner/Architect |
| BLK-011 | Indicator formula tables, public callable signatures and type contracts, error-mode defaults, cache/checksum and degradation policy, default resource limits, stable requirement IDs, traceability matrix, timezone conversion policy, and production audit integrity policy are not approved. | Blocks Indicator Builder handoff and deterministic Core MVP implementation. | Owner/Architect |

## Next Planned Sprint: 01 Utils/Foundation

| BLK-012 | Strategy public API signatures, error decision tables, final quantitative SLOs, reference performance environment, reviewed applicability tags and acceptance criteria, concrete test-case expansion from the family-level traceability matrix, sandbox policy, lifecycle promotion gates, dependency failure mapping, read-only state consistency model approval, and governance/operations extraction decision are not approved. | Blocks Strategy Builder handoff and external-module integration. | Owner/Architect |
| BLK-013 | Analytics official tool surface, public/internal export classification ADR, metric catalog formulas, concrete limits, FX/schema compatibility, dashboard payload classes, warning/quality-flag catalog, local cache behavior if implemented, and requirement-to-test traceability are not approved. | Blocks Analytics Builder handoff and production reliance on analytics reports. | Owner/Architect |
| BLK-014 | Optimization public/internal capability classification, public tool contracts, dry-run semantics, `BacktestExecutionAdapter` ownership, repository Protocol/ABC and DI policy, JSON serialization policy, canonical enum/error catalog, reproducibility fields, production resource limits, repository backend policy, remote repository retry policy, cache-stampede policy, artifact root, report schema version, optional dependency policy, and requirement-to-test traceability are not approved. | Blocks Optimization Builder handoff and production reliance on optimization evidence. | Owner/Architect |
| BLK-014 | Trading public API signatures, public tool contract matrix, `StandardTradingEnvelope v1`, Decimal policy, canonical serialization and hashing policy, credential/session interface, redaction interface, persistence interface direction, threshold defaults/overrides, reconciliation snapshot limits, property-based test tooling, concurrency scopes, route mutation semantics, broker-simulator failure injection, and requirement-to-test traceability are not approved. | Blocks Trading Builder handoff and production reliance on route-aware trading tools. | Owner/Architect |
| BLK-015 | Simulation Phase 1 FX slice, `run_backtest` public schema, `SimTrader` protocol contracts, `SimulationResult` schema, artifact/journal schemas, deferred-scope register, decision log, benchmark profile, memory limits, encryption-at-rest policy, production-realistic checklist, edge/error matrix, and requirement-to-test traceability are not approved. | Blocks Simulation Builder handoff and production reliance on simulation evidence. | Owner/Architect |

## Risks And Mitigations

| ID | Risk | Severity | Status | Mitigation |
|---|---|---|---|---|
| RISK-001 | Scope explosion from "all 13 modules work." | Critical | Open | Define first milestone depth; keep Sprint 001 scoped to Utils. |
| RISK-002 | Docs drift. | High | Open | Keep project memory in active docs and update with changes. |
| RISK-003 | Preserved safety behavior gets lost. | High | Monitoring | Preserve fail-closed, envelope, approval, idempotency, redaction, validation, audit, live-disabled defaults. |
| RISK-004 | Premature live trading side effects. | Critical | Open | Default live mutations disabled; require full safety gates. |
| RISK-005 | Auth model under-specified. | High | Monitoring | Use API gateway auth plus RBAC/action baseline; provider pending. |
| RISK-006 | MT5 runtime constraints. | High | Open | Isolate MT5 behind adapters and provide mocks. |
| RISK-007 | SQLite concurrency limits. | Medium | Monitoring | Keep repositories abstracted and revisit before multi-user production. |
| RISK-008 | Ambiguous mutation rules. | Critical | Open | Create action-level mutation/governance matrix before state-changing modules. |
| RISK-009 | Event loss or missing correlation. | High | Open | Start simple, add durable event/audit persistence before financial workflows. |
| RISK-010 | Idempotency misunderstood as exactly-once. | Critical | Open | Document keys as necessary but not sufficient; add reconciliation. |
| RISK-011 | UI/API contract drift. | High | Open | Maintain contracts and tests before frontend build-out. |
| RISK-012 | Unapproved risk threshold defaults. | Critical | Open | Keep numeric thresholds proposed; block live use until approved. |
| RISK-013 | Chat action drafts create unauthorized side effects. | High | Monitoring | Keep drafts separate from execution approval. |
| RISK-014 | Secret leakage. | Critical | Open | Redaction, no secrets in docs, secret scanning, tests, placeholders only. |
| RISK-015 | Notification alert fatigue or throttling. | Medium | Open | Use levels, routing, rate limits, retries, summaries. |
| RISK-016 | Simulation and live path divergence. | High | Open | Use shared Trading order-intent path with separated side effects. |
| RISK-017 | Reconciliation gaps. | Critical | Open | Block risky actions on unknown or mismatched state. |
| RISK-018 | Optimization overload or overfitting. | Medium | Open | Add run limits, metadata, robustness scoring, warnings. |
| RISK-019 | Performance targets lack workload context. | Medium | Monitoring | Treat as engineering baselines until benchmarks. |
| RISK-020 | Retention policy guessed. | High | Open | Require owner/compliance approval. |
| RISK-021 | Existing repo adoption ambiguity. | High | Open | Decide adoption status before Sprint 001. |
| RISK-022 | Conversation implementation relies on inferred contracts for streaming, fallback behavior, persistence, retention, permissions, concurrency, configuration limits, or machine-readable errors. | High | Open | Require explicit conversation contracts, event schemas, fallback schemas, permission authority, repository behavior, configuration references, concrete NFR targets, failure behavior, and mapped tests before Builder handoff. |
| RISK-023 | Research implementation could infer statistical contracts, artifact schemas, error/envelope behavior, API overlap resolutions, cleaning semantics/defaults, seed determinism, external-feed behavior, resource limits, or advisory boundaries from broad inventory wording. | High | Open | Require public contracts, envelope schema and enums, behavior/error tables, canonical errors, cleaning strategy defaults, seed propagation, SHA-256 reproducibility metadata, provider failure behavior, measurable limits, advisory-only wording, usage failure examples, and mapped tests before Builder handoff. |
| RISK-024 | Indicator implementation could infer formulas, public data types, resource limits, numeric edge behavior, cache semantics, timezone behavior, or no-lookahead behavior from broad requirements. | High | Open | Require approved formula tables, type contracts, numeric policy, capability matrix, resource defaults, cache/checksum and degradation policy, timezone boundary policy, and mapped tests before Builder handoff. |
| RISK-025 | Strategy implementation could infer API signatures, final SLOs, dependency failure behavior, or governance boundaries from draft placeholders. | High | Open | Use the documented schema baselines, provisional NFRs, stable requirement IDs, read-only state contracts, and family-level traceability matrix as planning baselines; still require exact public signatures, error decision tables, owner-approved quantitative targets, dependency mappings, concurrency model, and concrete test-case expansion before Builder handoff. |
| RISK-026 | Analytics low-level metric aliases could be mistaken for stable agent/API tools. | High | Open | Require official/internal classification, keep historical metric inventory reference-only, gate exposure through the Official Analytics Tool Catalog, and keep canonical metric kernels private/internal by default. |
| RISK-027 | Analytics reports could be non-reproducible if performance limits, schema compatibility, numeric tolerances, non-finite handling, or cache behavior remain unresolved. | High | Open | Require approved metric catalog, concrete NFR limits, schema matrix, Decimal monetary sums, deterministic ratio tolerances, cache-concurrency rules, and golden-file/traceability tests before Builder handoff. |
| RISK-033 | Live implementation could treat proposed NFR targets, emergency fail-safe labels, retry/rate-limit behavior, broker communication security, broker adapter contracts, or reconciliation authority transitions as approved. | Critical | Open | Keep proposed targets and policy/state-machine items pending until owner/architect approval; block production live broker mutation until `LIVE-PEND-*` items and mandatory security gates are resolved. |
| RISK-028 | Trading implementation could infer live credential handling, API signatures, Decimal precision, canonical hashing, timeout/freshness defaults, reconciliation snapshot limits, persistence direction, concurrency locking, or failure-envelope behavior from incomplete contracts. | Critical | Open | Require Interface Definition Appendix, Decimal/canonical serialization approval, credential/session boundary approval, persistence interface direction, concrete defaults or approved overrides, generated/property-based contract tests, and broker-simulator failure-path tests before Builder handoff. |
| RISK-040 | Simulation's broad multi-asset baseline could obscure the buildable Phase 1 FX slice or lead Builders to infer API/contracts, live-adapter behavior, security-at-rest behavior, or NFR gates from placeholders. | High | Open | Require approved contract scaffolds, deferred-scope register, edge/error matrix, encryption-at-rest policy, benchmark profile, executable examples, fault-injection tests, and traceability matrix before Builder handoff. |

## Next Actions

1. Finish lean documentation migration and verify old references.
2. Decide existing code adoption status for Sprint 001.
3. Resolve blocking questions that affect Utils and the early API/data contract.
4. Approve a single current-sprint block for Sprint 001 in this file.
5. Build Utils/Foundation only after dry run and `APPROVED: EXECUTE`.
6. Before Data implementation begins, approve a phase slice from the Data handoff requirements and confirm exact per-tool contracts.
7. Before Data production handoff, approve or revise the Data engineering benchmark profile, response schema version, precision policy, database pool defaults, backfill checkpoint/chunk policy, concurrent path write-lock policy, manifest/schema paths, load-test report, and real-time feed soak-test requirements.
7. Before Analytics implementation begins, approve the required Analytics ADRs for official tool surface, public/internal export classification, metric formulas, report section criticality, thresholds, FX authority, schema compatibility, dashboard limits, local cache behavior if implemented, warning/quality-flag catalog, measurable NFR limits, and requirement-to-test traceability matrix.
8. Before Trading implementation begins, approve a narrowed Trading slice, public tool contract matrix, Interface Definition Appendix, `StandardTradingEnvelope v1`, Decimal precision policy, canonical serialization and hashing policy, credential/session interface, redaction interface, persistence interface direction, default thresholds or overrides, reconciliation snapshot limits, property-based testing tool decision, concurrency scopes, route-specific mutation semantics, broker-simulator failure-injection plan, and requirement-to-test traceability matrix.
9. Before Live implementation begins, approve the live public tool contract matrix, terminology/enumerations, canonical live gate contract, diagnostic-only gate list, package-only and mutation-enabled modes, approval action matrix/quorum, side-effect modes, retry-safety taxonomy, `retry_after_seconds` behavior, idempotency and reconciliation persistence, broker adapter contracts, concrete NFR targets, stale/timeout/rate-limit/queue/concurrency limits, mandatory broker communication security profile, and restart/recovery behavior.
9. Before Optimization implementation begins, approve a narrowed Optimization slice, public/internal capability matrix, public tool contract matrix, dry-run semantics/defaults, `BacktestExecutionAdapter` ownership, repository Protocol/ABC and DI policy, JSON serialization policy, canonical enum/error catalog, reproducibility fields, production resource limits, repository backend/retry/cache-stampede policy, artifact root, report schema version, optional dependency policy, and requirement-to-test traceability matrix.
9. Before Simulation implementation begins, approve the Phase 1 FX canonical backtest slice, `run_backtest` public schemas, `SimTrader` protocol contracts, `SimulationResult` and artifact/journal schemas, external interface contracts, deferred-scope register, decision log, benchmark profile, memory limits, encryption-at-rest policy, production-realistic checklist, edge/error matrix, fault-injection plan, executable queued/diagnostic-failed examples, acceptance criteria, and requirement-to-test traceability matrix.
9. Before Risk implementation begins, approve export classifications, official risk tool contracts, stable requirement IDs, portfolio-under-risk adapter ownership, private/public export mapping, transitional facade v2.0 migration/reapproval plan, benchmark acceptance, time-provider policy, strict Decimal/Pydantic serialization behavior, payload depth/list limits, non-PSD correlation handling, double-spend prevention ownership, fractional Kelly multiplier, stressed lookback policy, crisis reference source, first heavy-tailed VaR distribution, Gaussian VaR waiver behavior, and requirement-to-test traceability matrix.
9. Before Conversation implementation begins, approve the public capability contract matrix, machine-readable error taxonomy, stream event schemas, fallback response schema, `ConversationRepository`/persistence contracts, production retention policy, configuration reference values and provisional-baseline disposition, read-only tool permission authority, auth context flow, concurrency/idempotency behavior, concrete NFR targets, focused safety tests, and requirement-to-test traceability matrix.
9. Before Research implementation begins, approve the public API overlap resolutions, public API contract matrix, core model/report schemas, standard research envelope schema/status/error enums, canonical research error taxonomy, per-callable behavior/error table and error-pattern map, cleaning strategy enums/defaults, leakage report schema, seed propagation policy, SHA-256 reproducibility metadata requirements, network-helper timeout/retry/cache/stale-data/rate-limit and optional-provider policy, report persistence and atomic-write policy, measurable resource limits with reference hardware, advisory-only promotion boundaries, usage failure examples, glossary/checklist requirements, and requirement-to-test traceability matrix.
9. Before Indicator implementation begins, approve the implementation pre-requisites in `docs/source-requirements/03-indicator.md`, including formula tables for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R; public callable signatures and type contracts; error-mode defaults; cache/checksum and degradation policy; default resource limits; stable requirement IDs; requirement-to-test traceability matrix; capability matrix fields; timezone conversion policy; and production audit integrity policy.
9. Before Strategy implementation begins, approve public API signatures, error decision tables, final quantitative SLOs and reference performance environment, reviewed applicability tags and acceptance criteria, concrete test cases expanded from the family-level traceability matrix, sandbox policy, lifecycle promotion gates, dependency failure mapping, read-only state consistency model, and governance/operations extraction scope.

## Completed Work

- Sprint 000 created a documentation baseline with product, architecture, planning, domain, risk, questions, decisions, testing, security, observability, deployment, and sprint files.
- Documentation refactor migrated the old baseline into the lean documentation model.
- Risk integration audit promoted 9 named default limit values, 12 canonical hard-limit rule key names, the two-stage RC governance formula, timeframe-aware lookback defaults, `RecommendationEngine` advisory output types, simulation risk integration hook requirements (§1.16.1), simulator-only margin tier policy (§1.16.2), `margin_level` formula, and `risk_snapshot.summary` API field list into the active requirements docs without duplicating logic across doc boundaries. Decisions recorded as DEC-022, DEC-023, DEC-024.
