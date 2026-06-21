## Phase 8 Simulator Engine

### Goal

Implement the Simulator Engine requirements under `app/services/simulator/` while preserving the phase module boundaries and governance rules.

Task inventory: 1,678 checkbox tasks (237 checked, 1,441 unchecked).

### Dependency Files and Functionality

Required files:

```text

app/utils/__init__.py

app/utils/dataframe_tools.py

app/services/data/__init__.py

app/services/data/gateway.py

app/services/indicators/__init__.py

app/services/strategies/__init__.py

app/services/strategies/registry.py

app/services/trader/__init__.py

```

Required functionality:

- Data gateway can retrieve historical tick/bar data slices.
- Indicators and strategy registries compile execution parameters.
- Trader interfaces and order validation controls exist in simulator mode.

### Files to Create

```text

app/__init__.py

app/services/simulator/__init__.py

app/services/simulator/orchestrator.py

app/services/simulator/engine.py

app/services/simulator/trader.py

app/services/simulator/models/__init__.py

app/services/simulator/models/tick.py

app/services/simulator/models/spread.py

app/services/simulator/models/slippage.py

app/services/simulator/models/liquidity.py

app/services/simulator/models/fee.py

app/services/simulator/models/swap.py

app/services/simulator/models/margin.py

app/services/simulator/validation/__init__.py

app/services/simulator/validation/quality.py

app/services/simulator/validation/schema.py

app/services/simulator/journal.py

app/services/simulator/report.py

app/services/simulator/

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

#### `app/services/simulator/README.md`

Functions/classes:

- No runtime functions/classes; documentation artifact only.

Requirements:

- [X] Usage examples shall run as executable documentation tests and assert exact success or failure envelope shape. *tests/usage/app/services/08_simulator.py:40*
- [X] Documentation shall include a formal user guide for interpreting realism labels. *app/services/simulator/README.md:56*
- [X] Documentation shall include a configuration reference for every config class and enum. *app/services/simulator/README.md:20*
- [X] Documentation shall include a migration guide if earlier simulator versions exist. *app/services/simulator/README.md:116*
- [X] Documentation shall describe memory-safety constraints for optimization, walk-forward, and Monte Carlo runs. *app/services/simulator/README.md:108*
- [X] Documentation shall describe FX cross-rate synthesis rejection behavior and `max_cross_rate_skew_bps`. *app/services/simulator/README.md:100*
- [X] Documentation shall describe added error and diagnostic codes. *app/services/simulator/README.md:123*
- [X] Documentation shall include research-integrity, optimization, and overfitting-control operating procedures.
- [X] Documentation shall include immutable run-configuration, environment drift detection, and benchmark-profile certification procedures.
- [X] Documentation shall include warm data cache behavior, TTL rules, `DataManifestHash` keys, and checksum validation requirements.
- [X] Documentation shall include feature-store point-in-time retrieval, alternative-data as-of alignment, publication lag, ingestion lag, and no-lookahead rules.
- [X] Documentation shall include FX `production_realistic` V1 non-goals and scope limitations.
- [X] Documentation shall include third-party data and vendor-governance procedures.

#### `app/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] The module may simulate configured simulator risk-rule effects for replay and evidence, but external policy definition, live approval authority, and human governance decisions live outside Simulator.
- [X] Initial MT5 parity tests shall use a versioned broker profile named `mt5_demo_reference_fx_v1`.
- [X] Poison-pill detection shall quarantine the work unit, stop infinite requeue loops, emit an alert, and preserve failure artifacts for diagnosis.
- [X] Anything exported from a domain `__init__.py` and listed in `__all__` shall be treated as an official AI Tool.
- [X] Documentation shall include execution latency modelling, latency component definitions, and latency diagnostic interpretation.
- [X] Optional enterprise features may be disabled initially, but their contracts should be defined to avoid breaking redesign.
- [X] No file-specific non-functional requirements defined.
- [X] Import-time tests shall verify public module import performs no filesystem writes, network access, worker startup, secret reads, market-data access, broker access, or long-running initialization. *tests/unit/app/services/simulator/test_08a_foundation.py:1056*

#### `app/services/simulator/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/simulator/orchestrator.py`

Functions/classes:

- `BacktestOrchestrator`
- `run_backtest`
- `EventDrivenExecutionEngine`

Requirements:

- [X] Simulator orchestration through `BacktestOrchestrator`. *app/services/simulator/orchestrator.py:62*
- [X] The system shall provide a `BacktestOrchestrator` that validates configuration and data dependencies before executing a simulator. *app/services/simulator/orchestrator.py:76*
- [X] Phase 1 shall implement `run_backtest`, `BacktestOrchestrator`, `EventDrivenExecutionEngine`, FX symbol metadata, tick generation, spread/slippage/commission/swap models, broker-profile fixtures, data-quality gates, deterministic journal storage, JSON and Markdown reports, schema validation, and replay tests.
- [X] The `BacktestOrchestrator` shall coordinate validation, data quality, signal construction, tick construction, execution, metrics, and reporting. *app/services/simulator/orchestrator.py:316*
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.
- [X] Expose the official AI tool boundary for `run_backtest`. *app/services/simulator/orchestrator.py:355*
- [X] MT5 parity comparisons shall require exact match for order count, deal count, position lifecycle count, side, symbol, order type, fill policy, and deterministic event order.
- [X] Production service mode shall queue `run_backtest` requests when workers are saturated and return a run id with `queued` status. *tests/unit/app/services/simulator/test_08a_foundation.py:116*
- [X] Queueing shall enforce maximum queue length, maximum queue age, cancellation support, and deterministic rejection when limits are exceeded.
- [X] The scheduler shall persist queued, running, completed, failed, and cancelled states outside worker memory.
- [X] Any network, multi-user, agent-orchestrated, or externally accessible `run_backtest` surface shall require authenticated actor identity. *app/services/simulator/validation/schema.py:102*
- [X] The `run_backtest` AI Tool shall reject raw arbitrary Python strategy code strings before execution. *app/services/simulator/validation/schema.py:27*
- [X] The orchestration layer shall explicitly vet and sandbox any code-based strategy path before it can be executed. *app/services/simulator/orchestrator.py:105*
- [X] The system shall return `SIM_ARBITRARY_CODE_REJECTED` when raw arbitrary strategy code is passed to `run_backtest`. *tests/unit/app/services/simulator/test_08a_foundation.py:91*
- [X] `SIM_IOC_REMAINDER_CANCELLED` shall be classified as a non-fatal diagnostic code. *app/services/simulator/orchestrator.py:47*
- [X] The system shall return `SIM_CHECKPOINT_INCOMPATIBLE` when a resumed run fails checkpoint compatibility validation. *tests/unit/app/services/simulator/test_08a_foundation.py:178*
- [X] `SIM_IOC_REMAINDER_CANCELLED` *tests/unit/app/services/simulator/test_08a_foundation.py:209*
- [X] The module does not own strategy logic, strategy lifecycle approval, or strategy-generated signal logic; those belong to `app/services/strategies/`. *app/services/simulator/orchestrator.py:13*
- [X] The module does not execute arbitrary user-provided Python strategy code through `run_backtest`. *app/services/simulator/orchestrator.py:105*
- [X] `run_backtest` shall define required fields, optional fields, defaults, enum values, unknown-field behavior, malformed-payload behavior, size limits, path resolution rules, validation order, authorization behavior, and artifact-root behavior before implementation. *app/services/simulator/validation/schema.py:64*
- [X] `run_backtest` shall define response envelopes for `success`, `failed`, `queued`, `cancelled`, and `diagnostic_failed` statuses before implementation.
- [X] Optimization, walk-forward, Monte Carlo, visual replay export, production-promotion manifests, and service-mode lifecycle operations shall be implemented only when their requirements are explicitly tagged for the active release phase.
- [X] `actor_context` shall define authenticated actor identity and roles for any networked, multi-user, or agent-orchestrated invocation. *app/services/simulator/models/tick.py:23*
- [X] `status` values shall include `success`, `failed`, `queued`, `cancelled`, and `diagnostic_failed` before implementation. *app/services/simulator/README.md:9*
- [X] The system shall fill available volume and cancel the remainder for `IOC` orders. *app/services/simulator/models/liquidity.py:51*
- [X] When an `IOC` order is partially filled, the unfilled remainder shall be cancelled. *app/services/simulator/models/liquidity.py:51*
- [X] `SIM_IOC_REMAINDER_CANCELLED` shall not be treated as a fatal simulator error when the partial fill itself is valid. *tests/unit/app/services/simulator/test_08a_foundation.py:209*
- [X] The `run_backtest` AI Tool shall enforce the strategy registry and sandbox rules defined in `docs/source-requirements/04-strategy.md`. *app/services/simulator/orchestrator.py:105*
- [X] Long-running optimization, walk-forward, and Monte Carlo jobs shall periodically checkpoint progress to disk in a restartable format.
- [X] A `ResumePolicy` shall define maximum checkpoint age, checkpoint compatibility rules, automatic resume eligibility, and restart-from-scratch behavior.
- [X] Pending orders, SL, TP, and limit prices shall be adjusted or cancelled according to broker/config policy.
- [X] The `run_backtest` AI Tool shall not accept raw arbitrary Python strategy code as a string input. *app/services/simulator/validation/schema.py:27*
- [X] The `run_backtest` AI Tool shall reject raw strategy-code injection attempts before execution. *tests/unit/app/services/simulator/test_08a_foundation.py:63*
- [X] The `run_backtest` AI Tool shall return `SIM_ARBITRARY_CODE_REJECTED` when raw arbitrary strategy code is rejected. *app/services/simulator/orchestrator.py:402*
- [X] Raw Python strategy code is supplied to `run_backtest`. *tests/unit/app/services/simulator/test_08a_foundation.py:82*
- [X] IOC order partially fills and cancels remainder. *tests/unit/app/services/simulator/test_08a_foundation.py:203*
- [X] `run_backtest` contract tests for success, failed, cancelled, queued where supported, and diagnostic-failed envelopes. *tests/unit/app/services/simulator/test_08a_foundation.py:116*
- [X] Contract tests shall verify failed, queued, cancelled, and diagnostic-failed responses preserve the same envelope shape and include deterministic `SIM_*` error codes where applicable. *tests/unit/app/services/simulator/test_08a_foundation.py:157*
- [X] Security tests shall verify unauthenticated network or agent-orchestrated access is rejected, each RBAC role is enforced, secrets in payloads are rejected and redacted, and rejected raw strategy code is not executed or logged in full.
- [X] Market-halt tests shall cover market-wide halts, symbol halts, limit-up/limit-down states, halted order rejection or deferral, and resumed trading.
- [X] Advanced-order tests shall cover trailing stops, pegged orders, cancel-replace behavior, queue-priority effects, and deterministic repricing.
- [X] Checkpoint and resume tests shall cover checkpoint age limits, checkpoint compatibility, OOM-style restart, worker loss, requeue behavior, and duplicate artifact prevention.
- [X] Service-operations tests shall cover resource quotas, queue backpressure, queued run status, queue limit rejection, cancellation, environment drift warnings, synthetic transaction probes, and canary divergence handling.
- [X] AI Tool strategy security tests shall verify `run_backtest` rejects raw arbitrary Python strategy code, returns `SIM_ARBITRARY_CODE_REJECTED`, does not execute rejected code, and does not log rejected code in full. *tests/unit/app/services/simulator/test_08a_foundation.py:63*
- [X] Model-governance, research-integrity, run-lifecycle, vendor-governance, and promotion-manifest tests shall pass before production promotion workflows are enabled.
- [X] Service-mode CI shall include resource-quota, queue, tracing, business-metric, synthetic-probe, canary, data-lineage, checkpoint-resume, and distributed-worker tests before production service deployment.
- [X] `queued` envelope example showing run id, queue position or bounded queue metadata where available, retry/cancellation metadata, warnings, and no completed result. *tests/usage/app/services/08_simulator.py:134*
- [X] `run_backtest` shall not execute arbitrary user-provided Python code strings. *app/services/simulator/validation/schema.py:27*
- [X] `ResumePolicy` for checkpoint age, checkpoint compatibility, automatic resume eligibility, and restart behavior.
- [X] Scheduler configuration for queue backend, queue limits, worker heartbeat timeout, retry policy, cancellation behavior, and preemptible-worker handling.
- [X] Code-based strategy execution metadata only when referenced by an approved registry entry with sandbox profile id, vetting artifact hash, approval metadata, and explicit orchestration-layer permission. *app/services/simulator/orchestrator.py:118*
- [X] Registered strategy identifier or validated strategy configuration for `run_backtest`. *app/services/simulator/orchestrator.py:131*
- [X] Sandbox and vetting metadata only when code-based strategy execution is explicitly permitted by the orchestration layer. *app/services/simulator/orchestrator.py:118*
- [X] Position lifecycle history.
- [X] IOC remainder cancellation diagnostics. *app/services/simulator/models/liquidity.py:51*
- [X] User, agent, CLI, or notebook shall be able to invoke the `run_backtest` tool wrapper. *tests/usage/app/services/08_simulator.py:48*
- [X] The `run_backtest` tool wrapper shall be the official user-facing tool boundary. *app/services/simulator/orchestrator.py:355*
- [X] Documentation shall state that raw arbitrary Python strategy code is not accepted by `run_backtest`. *app/services/simulator/README.md:9*
- [X] Documentation shall describe IOC remainder cancellation diagnostics. *app/services/simulator/README.md:40*
- [X] Documentation shall include run lifecycle, idempotency, cancellation, checkpoint, and resume behavior. *app/services/simulator/README.md:93*
- [X] Documentation shall include resource quota, scheduler queue, worker heartbeat, checkpoint/resume, preemptible-worker, and backpressure operating procedures.
- [X] Documentation shall include market-halt, limit-up/limit-down, portfolio kill-switch, trailing-stop, pegged-order, and cancel-replace semantics.

#### `app/services/simulator/engine.py`

Functions/classes:

- `EventDrivenExecutionEngine`
- `SimulatorResult`
- `run_id`
- `broker_profile_id`

Requirements:

- [X] Canonical tick-based execution through `EventDrivenExecutionEngine`. *app/services/simulator/engine.py:349*
- [X] `metadata` shall include module, operation, tool risk level, side-effect classification, actor/audit references where authorized, engine version, config hash, data manifest hash, execution timing, and created timestamp. *app/services/simulator/engine.py:729*
- [X] The system shall execute official backtests through the tick-based `EventDrivenExecutionEngine`. *app/services/simulator/orchestrator.py:76*
- [X] At the first tick of bar `N`, the engine shall mask, drop, or reject any raw OHLCV data point with timestamp greater than or equal to bar `N` open time. *app/services/simulator/engine.py:671*
- [X] At the first tick of bar `N`, the engine shall mask, drop, or reject any indicator-derived data point with timestamp greater than or equal to bar `N` open time. *app/services/simulator/engine.py:671*
- [X] At the first tick of bar `N`, the engine shall mask, drop, or reject any multi-timeframe aligned data point with timestamp greater than or equal to bar `N` open time. *app/services/simulator/engine.py:671*
- [X] At the first tick of bar `N`, the engine shall mask, drop, or reject strategy metadata used for sizing or trade decisions when that metadata depends on data with timestamp greater than or equal to bar `N` open time. *app/services/simulator/engine.py:671*
- [X] The engine shall raise `SIM_LOOKAHEAD_DETECTED` when a strategy attempts to access prohibited current-bar or future data during first-tick processing for bar `N`. *tests/unit/app/services/simulator/test_08a_foundation.py:295*
- [X] The system shall support configurable execution latency models covering strategy computation delay, broker or network routing delay, venue or exchange gateway delay, and matching-engine delay. *app/services/simulator/engine.py:41*
- [X] The default `ambiguous_sl_tp_policy` shall be `conservative_worst_outcome`, meaning the engine selects the lower resulting account equity after applying valid SL-first and TP-first interpretations under the same first-available-tick and cost model. *app/services/simulator/engine.py:33*
- [X] The system shall centralize final position sizing in the engine. *app/services/simulator/engine.py:645*
- [X] The engine shall maintain an authoritative positions container for open positions. *app/services/simulator/engine.py:359*
- [X] The engine shall maintain an authoritative orders container for active pending orders. *app/services/simulator/engine.py:360*
- [X] The engine shall maintain an authoritative deals container for executed deal records. *app/services/simulator/engine.py:361*
- [X] State containers shall be mutated only by the execution engine and shall be exposed to strategies through read-only snapshots. *app/services/simulator/engine.py:367*
- [X] The matching engine shall determine fillable volume from liquidity constraints before applying slippage to filled volume. *app/services/simulator/engine.py:514*
- [X] Every journal shall include a `journal_manifest.json` containing configuration hash, data manifest hash, engine version, schema version, artifact checksums, and retention tier. *app/services/simulator/engine.py:643*
- [X] Optimization shall use the same canonical tick execution engine as normal backtests. *app/services/simulator/engine.py:673*
- [X] Large optimization jobs shall be split into deterministic work units keyed by strategy id, parameter hash, config hash, data hash, engine version, and schema version. *app/services/simulator/engine.py:362*
- [X] Parallel optimization workers shall run isolated engine instances and shall not share mutable account, order, journal, or strategy state.
- [X] The roll engine shall decide whether to close/reopen, adjust the price series, or simulate calendar-spread execution. *app/services/simulator/engine.py:768*
- [X] The accounting engine shall track native-currency and base-currency realized PnL. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track native-currency and base-currency unrealized PnL. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track native-currency and base-currency commissions and fees. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track native-currency and base-currency swap. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track native-currency and base-currency borrow fees. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track native-currency and base-currency dividend cashflows. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track native-currency and base-currency futures roll PnL. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track native-currency and base-currency perpetual funding. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track native-currency and base-currency margin. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track native-currency and base-currency cash balances. *app/services/simulator/engine.py:152*
- [X] The accounting engine shall track portfolio NAV in base currency. *app/services/simulator/engine.py:182*
- [X] The first regulatory engine scope shall be US equities and ETFs. *app/services/simulator/engine.py:555*
- [X] The regulatory engine may support optional wash-sale detection and tax-awareness diagnostics for taxable account scenarios. *app/services/simulator/engine.py:555*
- [X] FX production-realistic promotion shall not require the regulatory engine, but reports shall disclose that regulatory checks were disabled or not applicable. *app/services/simulator/engine.py:555*
- [X] Internal engine services shall not be exported as agent-callable tools unless a deliberate wrapper is created. *app/services/simulator/orchestrator.py:62*
- [X] `SimulatorResult` shall include `schema_version`, `run_id`, `classification`, `started_at`, `completed_at`, `engine_version`, `config_hash`, `data_manifest_hash`, `broker_profile_id`, `artifact_manifest`, `summary_metrics`, `risk_metrics`, `cost_summary`, `realism_disclosure`, and `data_quality_summary`. *app/services/simulator/engine.py:66*
- [X] Resumed runs shall verify config hash, data manifest hash, engine version, journal sequence continuity, random-seed state, and checkpoint compatibility before continuing. *app/services/simulator/engine.py:718*
- [X] The numeric performance values in this section are provisional engineering targets until a Phase 1 benchmark profile and pass/fail gates are approved.
- [X] Internal engine services shall remain separate from official AI Tool wrappers. *app/services/simulator/engine.py:112*
- [X] Optional enterprise features shall have extension points without forcing a breaking redesign of the core engine. *app/services/simulator/engine.py:526*
- [X] The immutable run-configuration artifact shall include data authority manifest versions, broker profile versions, strategy version, engine version, dependency lock hash, resource policy, and effective runtime flags. *app/services/simulator/engine.py:792*
- [X] Trace and log context shall propagate run id, request id, strategy id, config hash, data manifest hash, and engine version. *app/services/simulator/engine.py:207*
- [X] Major engine releases shall support canary analysis by running a controlled subset of production requests through old and new engine versions and comparing results for configured statistical equivalence. *app/services/simulator/engine.py:868*
- [X] Internal engine services shall not be agent-callable unless wrapped deliberately. *app/services/simulator/orchestrator.py:62*
- [X] Phase 1 shall exclude equity/ETF corporate actions, borrow-fee production realism, forced buy-ins, delisting, US regulatory engines, futures rollover production realism, perpetual funding production realism, feature-store integration, alternative-data integration, distributed workers, poison-pill work-unit quarantine, canary analysis, synthetic transaction monitoring, external report distribution, and production promotion workflows unless separately approved. *app/services/simulator/engine.py:87*
- [X] `Future Extensions Annex`: future asset classes, enterprise service mode, distributed workers, regulatory engines, feature-store/alternative-data integrations, canary/synthetic monitoring, external report distribution, and production-promotion automation. *app/services/simulator/engine.py:87*
- [X] The engine is the single source of truth for orders, deals, positions, pending orders, account state, balance, equity, margin, free margin, margin level, realized PnL, floating PnL, commission, swap, trade history, audit journal, and execution timestamps.
- [X] Optimization must use the canonical tick-execution engine. *app/services/simulator/engine.py:673*
- [X] Tick batching shall be allowed only where the engine can prove no state transition or compliance event can occur before the next boundary. *app/services/simulator/engine.py:907*
- [X] The `EventDrivenExecutionEngine` shall own canonical execution. *app/services/simulator/engine.py:999*
- [X] Internal engines shall provide data quality, tick generation, spread, market calendar, gaps, event priority, liquidity, slippage, matching, fees, swap, broker rules, portfolio, accounting, compliance, metrics, optimization, Monte Carlo, and performance services. *app/services/simulator/engine.py:526*
- [X] Deferred enterprise and future-scope areas include non-FX production-realistic asset-class expansion, regulatory engines, feature-store integration, alternative-data integration, distributed workers, canary analysis, synthetic transaction monitoring, external-report distribution workflows, and production-promotion automation unless explicitly approved for the active release phase. *app/services/simulator/engine.py:87*
- [X] No file-specific non-functional requirements defined.
- [X] Optimization uses the same canonical tick execution engine as normal backtests. *app/services/simulator/engine.py:673*
- [X] The attached Hardened Draft v1.6 specification is the active source of truth.
- [X] The simulator is intended for Python implementation.
- [X] The simulator module is intended to live under `app/services/simulator/`.
- [X] Indicator implementation requirements live in `docs/source-requirements/03-indicator.md`.
- [X] The simulator targets deterministic backtesting and simulator, not live order execution against a broker.
- [X] Vectorized processing is acceptable only for indicators and signal generation.
- [X] Future improvements shall contain only deferred optional enhancements and shall not contain mandatory business rules, required inputs, required outputs, or production gates.
- [X] Each future improvement shall include rationale, non-goal status for the current phase, promotion trigger, affected requirement sections, and required owner decision before promotion.
- [X] The Deferred Scope Register in the Phase 1 Builder Slice section shall be the single source of truth for Simulator deferred-scope status during Phase 1 handoff preparation. *app/services/simulator/engine.py:87*
- [X] Validate simulator configuration, strategy references, data dependencies, broker profiles, market-data authority manifests, realism requirements, and run permissions before execution.
- [X] The same configuration, data, and seed shall produce the same trade intents. *tests/unit/app/services/simulator/test_08a_foundation.py:522*
- [X] The same configuration, data, and seed shall produce the same event-priority order. *tests/unit/app/services/simulator/test_08a_foundation.py:522*
- [X] The same configuration, data, and seed shall produce the same orders, deals, and positions.
- [X] The same configuration, data, and seed shall produce the same portfolio state.
- [X] Event ordering shall be replayable. *app/services/simulator/engine.py:1178*
- [X] Parent-child order lineage shall be auditable when order chaining is enabled. *app/services/simulator/engine.py:1224*
- [X] The system shall not silently fail. *app/services/simulator/engine.py:1242*
- [X] The system shall return deterministic error codes for rejections, skipped trades, invalid config, invalid data, validation failures, sizing failures, and execution failures. *app/services/simulator/engine.py:1242*
- [X] The system shall log all failures. *app/services/simulator/engine.py:1242*
- [X] Indicator and signal calculation for 10 years by 10 symbols of M1 bars should target less than 5 seconds after caching or preprocessing.
- [X] Optimization batch of 10,000 parameter sets should target less than 30 minutes after parallel execution is enabled.
- [X] Common 10-symbol research runs should target less than 2 GB memory after chunking and caching.
- [X] Production benchmark gates shall define benchmark dataset, hardware profile, dependency lock hash, measurement command, warmup behavior, sample count, pass/fail threshold, allowed variance, median runtime, and p95 runtime before the targets above are used as acceptance gates.
- [X] Phase 1 Builder handoff shall either replace provisional `should target` values with approved `MUST meet` thresholds or explicitly mark them non-blocking until production promotion.
- [X] Phase 1 memory limits shall remain pending owner approval until the benchmark profile defines maximum resident memory, measurement command, reference hardware, dataset shape, and failure behavior.
- [X] Once approved, memory-limit breaches shall fail deterministically with `SIM_RESOURCE_QUOTA_EXCEEDED` before the run can claim production-realistic classification.
- [X] The system shall follow a domain-driven architecture.
- [X] Simulator, indicators, and strategies shall remain in their target domains.
- [X] This domain document may be split into smaller requirement files after Phase 1 boundaries are implemented, provided traceability to this baseline is preserved.
- [X] Any split requirements file shall preserve requirement ids, release phase, acceptance criteria, and verification mapping.
- [X] The simulator shall reproduce important MT5 Strategy Tester execution semantics.
- [X] Data checks shall be deterministic. *app/services/simulator/engine.py:1326*
- [X] Data checks shall include survivorship-bias flags where relevant. *app/services/simulator/engine.py:675*
- [X] Floating-point types may be used for vectorized indicator research only when the result is not used directly for official accounting or official fill prices.
- [X] Fractional shares and fractional contract quantities shall be allowed only when symbol metadata declares a valid fractional volume step. *app/services/simulator/engine.py:1310*
- [X] Position sizing shall default to floor-to-step volume rounding, while final fill prices and account cashflows shall follow the execution and accounting rounding rules above. *app/services/simulator/engine.py:1675*
- [X] The simulator shall emit run-level telemetry for every official run. *app/services/simulator/engine.py:1462*
- [X] Resource quotas shall include maximum concurrent runs, maximum wall-clock seconds per run, maximum temporary storage bytes, maximum queued runs, and maximum worker count where applicable. *app/services/simulator/engine.py:472*
- [X] Quota violations shall fail fast with `SIM_RESOURCE_QUOTA_EXCEEDED`. *app/services/simulator/engine.py:945*
- [X] Before a production run starts, the system shall compute and record an environment diagnostic hash covering dependency versions, selected system libraries, relevant environment variables, container image digest where applicable, and benchmark profile id. *app/services/simulator/engine.py:829*
- [X] The system shall raise `SIM_ENVIRONMENT_DRIFT_WARNING` when the environment diagnostic hash differs from the certified benchmark profile environment. *app/services/simulator/engine.py:829*
- [X] Alerting shall include trend or predictive rules for persistence failures, data-provider failures, queue saturation, and SLO burn rate where the monitoring platform supports them.
- [X] Production service mode shall support synthetic transaction monitoring through a scheduled canonical simulator probe.
- [X] Optional service failures such as warm-cache outage or SQLite sidecar index outage may degrade to slower fallback behavior for non-production runs when configured.
- [X] SQLite sidecar fallback shall use a full canonical JSONL scan and shall disclose the slower degraded mode in diagnostics.
- [X] Official AI Tool exports shall require metadata.
- [X] Official AI Tool exports shall use structured logging.
- [X] Official AI Tool exports shall return deterministic error codes.
- [X] Official AI Tool exports shall avoid silent failures.
- [X] Official AI Tool exports shall provide safe errors.
- [X] Parent-child order lineage shall be preserved where enabled for auditability. *app/services/simulator/engine.py:641*
- [X] Local trusted CLI or notebook usage may run without interactive authentication only when the process uses local filesystem permissions and does not expose a network listener.
- [X] External tool access shall enforce role-based authorization with at least `simulator.viewer`, `simulator.runner`, and `simulator.admin` roles.
- [X] `simulator.admin` may manage approved broker profiles, data-authority manifests, retention policies, and benchmark baselines.
- [X] The tool wrapper shall prevent arbitrary code execution through strategy input.
- [X] Code-based strategy execution approval shall require `simulator.admin` approval, strategy owner approval, sandbox profile id, vetting artifact hash, and recorded approval expiry.
- [X] Rejected code-injection attempts shall be logged with safe redaction.
- [X] Security-relevant rejections shall include deterministic error codes.
- [X] Research runs shall default to a 180-day retention tier.
- [X] Diagnostic failure logs shall default to a 90-day retention tier unless linked to a production-candidate incident.
- [X] Benchmark metadata attached to a release shall be retained for at least three years or the lifetime of the release line, whichever is longer.
- [X] Encryption-at-rest requirements shall define owning module, approved key source, key rotation expectations, failure behavior when encryption is unavailable, metadata redaction, and compatibility with checksum/signature verification.
- [X] Production releases shall require pinned dependency lockfiles.
- [X] Production releases shall generate an SBOM.
- [X] Production releases shall pass dependency vulnerability scanning.
- [X] Production releases shall pass secret scanning.
- [X] Production releases shall pass static security analysis for public modules and official AI Tool wrappers.
- [X] Third-party market-data adapters, broker-profile loaders, and optimization plugins shall be treated as supply-chain dependencies with approval status and version hashes.
- [X] Every rejection shall return a deterministic error code. *app/services/simulator/engine.py:1242*
- [X] Every skipped trade shall return a deterministic error code. *app/services/simulator/engine.py:1284*
- [X] Every validation failure shall return a deterministic error code. *app/services/simulator/engine.py:963*
- [X] Every sizing failure shall return a deterministic error code. *app/services/simulator/engine.py:1686*
- [X] Every execution failure shall return a deterministic error code.
- [X] Every failure shall be logged. *app/services/simulator/engine.py:1242*
- [X] Unsupported fill policies shall be rejected before matching. *app/services/simulator/engine.py:1644*
- [X] Safe errors shall be provided by the exported tool wrapper.
- [X] The system shall support the documented `SIM_*` error-code taxonomy. *app/services/simulator/engine.py:45*
- [X] The system shall stop production runs on `SIM_PERSISTENCE_FAILED`.
- [X] The system shall return `SIM_CALIBRATION_REQUIRED` when calibrated execution evidence is required but missing, expired, or invalid.
- [X] The system shall return `SIM_VENDOR_DATA_POLICY_VIOLATION` when data license, retention, revision, or point-in-time requirements are violated.
- [X] The system shall return `SIM_QUEUE_LIMIT_EXCEEDED` when scheduler queue limits are exceeded.
- [X] The system shall return `SIM_WORKER_LOST_REQUEUED` as a non-fatal diagnostic when a lost worker causes a work unit to be requeued.
- [X] The system shall return `SIM_CANARY_DIVERGENCE` when canary comparison exceeds configured divergence tolerance.
- [X] The system shall return `SIM_FEATURE_LOOKAHEAD_DETECTED` when feature-store or alternative-data availability violates point-in-time rules.
- [X] `SIM_DATA_EMPTY` *app/services/simulator/engine.py:45*
- [X] `SIM_DATA_DUPLICATE_TIMESTAMP` *app/services/simulator/engine.py:45*
- [X] `SIM_DATA_NON_MONOTONIC_TIME` *app/services/simulator/engine.py:45*
- [X] `SIM_DATA_PRICE_OUTLIER` *app/services/simulator/engine.py:45*
- [X] `SIM_LOOKAHEAD_DETECTED` *app/services/simulator/engine.py:45*
- [X] `SIM_VOLUME_BELOW_MIN` *app/services/simulator/engine.py:45*
- [X] `SIM_VOLUME_ABOVE_MAX` *app/services/simulator/engine.py:45*
- [X] `SIM_VOLUME_STEP_MISMATCH` *app/services/simulator/engine.py:45*
- [X] `SIM_FREEZE_LEVEL_VIOLATION` *app/services/simulator/engine.py:45*
- [X] `SIM_CORRELATION_LIMIT_EXCEEDED` *app/services/simulator/engine.py:45*
- [X] `SIM_CONCENTRATION_LIMIT_EXCEEDED` *app/services/simulator/engine.py:45*
- [X] `SIM_MARKET_CLOSED` *app/services/simulator/engine.py:45*
- [X] `SIM_GAP_HANDLING_REJECTED` *app/services/simulator/engine.py:45*
- [X] `SIM_PARTIAL_FILL_REMAINDER` *app/services/simulator/engine.py:45*
- [X] `SIM_UNSUPPORTED_FILL_POLICY` *app/services/simulator/engine.py:45*
- [X] `SIM_LIMIT_QUEUE_NOT_FILLED` *app/services/simulator/engine.py:45*
- [X] `SIM_PENDING_ORDER_EXPIRED` *app/services/simulator/engine.py:45*
- [X] `SIM_ORDER_NOT_FOUND` *app/services/simulator/engine.py:45*
- [X] `SIM_SIZING_FAILED` *app/services/simulator/engine.py:45*
- [X] `SIM_SIZING_REQUIRES_STOP_LOSS` *app/services/simulator/engine.py:45*
- [X] `SIM_PERSISTENCE_FAILED` *app/services/simulator/engine.py:45*
- [X] `SIM_ARBITRARY_CODE_REJECTED` *app/services/simulator/engine.py:45*
- [X] `SIM_COMMISSION_CALCULATION_FAILED` *app/services/simulator/engine.py:45*
- [X] `SIM_FX_CROSS_RATE_REJECTED` *app/services/simulator/engine.py:45*
- [X] `SIM_DATA_PARTIAL` *app/services/simulator/engine.py:45*
- [X] `SIM_RESOURCE_QUOTA_EXCEEDED` *app/services/simulator/engine.py:45*
- [X] `SIM_QUEUE_LIMIT_EXCEEDED` *app/services/simulator/engine.py:45*
- [X] `SIM_ENVIRONMENT_DRIFT_WARNING` *app/services/simulator/engine.py:45*
- [X] `SIM_WORKER_LOST_REQUEUED` *app/services/simulator/engine.py:45*
- [X] `SIM_CANARY_DIVERGENCE` *app/services/simulator/engine.py:45*
- [X] `SIM_FEATURE_LOOKAHEAD_DETECTED` *app/services/simulator/engine.py:45*
- [X] `SIM_MARKET_HALT_ACTIVE`
- [X] `SIM_KILL_SWITCH_TRIGGERED`
- [X] `SIM_POISON_WORK_UNIT_QUARANTINED`
- [X] `SIM_OPTIONAL_SERVICE_DEGRADED`
- [X] `SIM_RUN_ID_CONFLICT`
- [X] `SIM_CHECKPOINT_INCOMPATIBLE` *app/services/simulator/engine.py:45*
- [X] `SIM_CALIBRATION_REQUIRED` *app/services/simulator/engine.py:45*
- [X] `SIM_VENDOR_DATA_POLICY_VIOLATION` *app/services/simulator/engine.py:45*
- [X] `SIM_PERFORMANCE_GATE_FAILED`
- [X] `SIM_MONTE_CARLO_FAILED`
- [X] `SIM_OPTIMIZATION_FAILED` *app/services/simulator/engine.py:45*
- [X] `SIM_INTERNAL_ERROR` *app/services/simulator/engine.py:45*
- [X] The module does not own raw market-data acquisition, source readiness, external source adapters, or normalized data contracts; those belong to `app/services/data/`.
- [X] The module does not own final live broker execution against real accounts.
- [X] The module does not own live adapter implementation, live broker session management, live broker credentials, or imports of live execution modules; those must remain in Live/Trading/execution adapter ownership.
- [X] `error` shall include deterministic `SIM_*` code, safe message, field path where applicable, severity, retryability, and redacted details.
- [X] The system shall build indicator and signal data before constructing the executable signal timeline.
- [X] The system shall align bar-based signals using the configured signal timing policy.
- [X] The system shall use `BAR_OPEN_PREVIOUS_CLOSE` as the default signal timing policy.
- [X] The system shall reject or flag lookahead usage in bar-open strategies.
- [X] The system shall require vectorized signal generation to shift current-bar conditions so that bar-open entries are based on previous closed-bar values.
- [X] The system shall allow simplified realism modes only when explicitly configured.
- [X] Latency diagnostics shall record signal timestamp, request timestamp, eligible execution timestamp, latency components, and latency model id.
- [X] The system shall support `FOK`. *tests/unit/app/services/simulator/test_08a_foundation.py:705*
- [X] The system shall support `IOC`. *app/services/simulator/engine.py:2063*
- [X] The system shall support `RETURN`. *app/services/simulator/engine.py:2040*
- [X] The system shall support explicit partial-fill behavior. *app/services/simulator/engine.py:2063*
- [X] The system shall reject `FOK` orders when full requested volume is unavailable. *app/services/simulator/engine.py:1955*
- [X] The system shall keep unfilled `RETURN` remainders pending only when the broker or symbol supports it. *app/services/simulator/engine.py:2040*
- [X] The system shall create a separate deal record for every partial fill. *app/services/simulator/engine.py:1981*
- [X] The system shall recalculate position average price from actual filled volumes and prices. *app/services/simulator/engine.py:2077*
- [X] The system shall support configurable limit-order queue behavior. *app/services/simulator/engine.py:796*
- [X] The system shall reduce available fill volume by estimated or configured queue-ahead volume. *app/services/simulator/engine.py:1358*
- [X] The system shall resolve FIFO and pro-rata behavior deterministically. *app/services/simulator/engine.py:796*
- [X] The system may document hidden-order and iceberg support while keeping them disabled until order-book data is available.
- [X] Before Phase 1 Builder handoff, limit-order queue configuration shall explicitly define valid values for `queue_model`, `touch_fill_enabled`, `queue_ahead_volume`, `queue_ahead_estimation_method`, `fill_allocation_method`, `minimum_fill_volume`, and `partial_fill_policy`. *app/services/simulator/engine.py:796*
- [X] Phase 1 queue behavior shall be limited to deterministic `touch_fill_enabled=false` rejection or deterministic configured queue-ahead reduction unless the owner approves richer order-book queue realism. *app/services/simulator/engine.py:1358*
- [X] Hidden-order and iceberg reservation behavior shall be `[PHASE2]` and must return deterministic unsupported-scope diagnostics if requested during Phase 1.
- [X] The system shall support market-hours configuration including session start, session end, timezone, weekend closure, holiday calendar, and 24/7 asset flag. *app/services/simulator/engine.py:710*
- [X] The system shall detect market open and closed state. *app/services/simulator/engine.py:1248*
- [X] The system shall detect session breaks, weekends, holidays, and rollover boundaries. *app/services/simulator/engine.py:1296*
- [X] The system shall detect market-wide halts, exchange halts, symbol halts, and limit-up/limit-down states when halt data is available. *app/services/simulator/engine.py:767*
- [X] The system shall prevent market orders outside allowed sessions unless explicitly configured for 24/7 assets. *app/services/simulator/engine.py:1939*
- [X] The system shall support gap handling by rejection. *app/services/simulator/engine.py:1319*
- [X] The system shall support gap handling by fill at open. *app/services/simulator/engine.py:1319*
- [X] The system shall use the conservative worse outcome by default when both SL and TP are crossed in the same ambiguous gap. *tests/unit/app/services/simulator/test_08a_foundation.py:650*
- [X] The system shall enforce stop-out percentage. *app/services/simulator/engine.py:1452*
- [X] The system shall enforce maximum pending orders. *app/services/simulator/engine.py:2220*
- [X] The system shall reject unsupported fill policies with deterministic error codes. *app/services/simulator/engine.py:1076*
- [X] The system shall support fixed-lot sizing.
- [X] The system shall support milestone sizing.
- [X] The system shall support Kelly-criterion sizing.
- [X] The system shall support volatility-based sizing.
- [X] The system shall support fixed-fractional sizing.
- [X] The system shall reject zero or negative stop distance. *app/services/simulator/engine.py:1414*
- [X] The system shall normalize volume using symbol minimum, maximum, and step constraints. *app/services/simulator/engine.py:1359*
- [X] The system shall support explicit volume rounding policies. *app/services/simulator/engine.py:1359*
- [X] The system shall default to floor-to-step rounding. *app/services/simulator/engine.py:1359*
- [X] The system shall record raw and normalized volume and shall not silently adjust volume. *app/services/simulator/engine.py:228*
- [X] Pending-order records shall include all applicable position record fields plus order price, stop-limit price, expiry date, and expiration mode. *app/services/simulator/engine.py:178*
- [X] Deal records shall include all applicable position record fields plus deal reason, deal direction, order id, position id, fill price, filled volume, and execution timestamp. *app/services/simulator/engine.py:207*
- [X] The system shall validate broker maximum orders and positions. *app/services/simulator/engine.py:1485*
- [X] The system shall validate fill-policy compatibility. *app/services/simulator/engine.py:1937*
- [X] The system shall execute market orders. *app/services/simulator/engine.py:1908*
- [X] The system shall trigger pending orders. *app/services/simulator/engine.py:2296*
- [X] The system shall support buy limit pending orders. *tests/unit/app/services/simulator/test_08a_foundation.py:774*
- [X] The system shall support buy stop pending orders. *tests/unit/app/services/simulator/test_08a_foundation.py:774*
- [X] The system shall support sell limit pending orders. *tests/unit/app/services/simulator/test_08a_foundation.py:774*
- [X] The system shall support sell stop pending orders. *tests/unit/app/services/simulator/test_08a_foundation.py:774*
- [X] The system shall support buy stop-limit pending orders. *app/services/simulator/engine.py:1476*
- [X] The system shall support sell stop-limit pending orders. *tests/unit/app/services/simulator/test_08a_foundation.py:774*
- [X] The system shall support trailing stops when configured. *app/services/simulator/engine.py:1598*
- [X] The system shall support pegged orders when configured, including orders pegged to best bid, best ask, mid price, or another approved reference. *app/services/simulator/engine.py:1662*
- [X] The system shall activate stop-limit orders. *tests/unit/app/services/simulator/test_08a_foundation.py:812*
- [X] The system shall trigger SL/TP. *app/services/simulator/engine.py:1534*
- [X] The system shall handle gap execution.
- [X] The system shall enforce fill policies. *app/services/simulator/engine.py:1937*
- [X] The system shall simulate partial fills. *tests/unit/app/services/simulator/test_08a_foundation.py:705*
- [X] The system shall produce orders, deals, position events, and execution diagnostics. *app/services/simulator/engine.py:1981*
- [X] Compliance records shall include timestamp.
- [X] Compliance records shall include decision rationale.
- [X] Compliance records shall include pre-trade checks.
- [X] Compliance records shall include optional compliance tag.
- [X] Advanced stateful strategies and agent-generated strategies shall provide decision rationale.
- [X] The simulator module shall provide approved read-only execution state to advanced strategies when required.
- [X] The simulator module shall consume indicator outputs through the indicator module contract defined in `docs/source-requirements/03-indicator.md`.
- [X] The simulator module shall reject, mask, or downgrade runs when indicator-derived data violates the configured no-lookahead policy.
- [X] The simulator module shall convert indicator-derived signals into timestamped trade intents before official execution.
- [X] The system shall support grid-search optimization.
- [X] The system shall support random-search optimization.
- [X] The system shall support Bayesian optimization.
- [X] The system shall support genetic optimization.
- [X] Optimization shall reject parameter sets that fail minimum trade count.
- [X] Optimization shall reject parameter sets that fail robustness checks.
- [X] Optimization outputs shall include config hash, data hash, parameter hash, random seed, and objective function.
- [X] Failed or diagnostic work units shall not poison the optimization cache.
- [X] Optimization jobs shall support resumable execution from persisted work-unit manifests.
- [X] Optimization and walk-forward jobs shall decompose into independent deterministic work units executable on ephemeral stateless workers.
- [X] Worker loss, heartbeat expiry, or preemptible-instance termination shall requeue the affected work unit without marking the entire job `SIM_INTERNAL_ERROR`.
- [X] Distributed schedulers shall detect poison-pill work units that repeatedly fail for the same work-unit hash.
- [X] Monte Carlo outputs shall include confidence bands for drawdown.
- [X] Monte Carlo outputs shall include confidence bands for net profit.
- [X] Monte Carlo outputs shall include confidence bands for profit factor.
- [X] Monte Carlo outputs shall include worst-case streaks.
- [X] The system shall benchmark memory usage.
- [X] The system shall benchmark optimization throughput when optimization is enabled.
- [X] The production benchmark profile shall be `SIM_BENCHMARK_PROFILE_V1`: Python 3.12, 8 vCPU minimum, 32 GB RAM minimum, NVMe SSD, release build settings, no debugger, and no unrelated heavy background workload.
- [X] The performance gate shall fail when median runtime regresses by more than 10 percent against the approved baseline and the absolute target is missed.
- [X] The memory gate shall fail when peak memory regresses by more than 15 percent against the approved baseline and the absolute memory target is missed.
- [X] If active orders or open positions exist, batching shall proceed only up to the nearest known trigger boundary.
- [X] Tick batching shall aggressively batch contiguous no-op ticks, quote-only intervals, and other provably transition-free spans without changing deterministic state, event ordering, audit sequence numbers, or replay output.
- [X] Tick batching shall split immediately at any possible order trigger, stop/limit boundary, trailing-stop repricing point, compliance/risk check, cashflow timestamp, market-session boundary, or audit-relevant lifecycle transition.
- [X] Performance benchmarks shall measure tick-loop throughput with audit enabled and disabled, including JSONL journal writes, hash-chain calculation, SQLite sidecar indexing, flush policy, and fsync-per-batch durability.
- [X] The system shall represent asset class in symbol metadata.
- [X] The system shall support FX.
- [X] The system shall support CFD.
- [X] The system shall support ETF.
- [X] The system shall support future.
- [X] The system shall support spot crypto.
- [X] The system shall support index instruments.
- [X] The system shall derive required realism modules from symbol metadata and simulator config.
- [X] FX shall be the first asset class eligible for `production_realistic` promotion.
- [X] The system shall support dividends.
- [X] The system shall support stock splits.
- [X] The system shall support reverse splits.
- [X] The system shall support mergers.
- [X] The system shall support spinoffs.
- [X] The system shall support delistings.
- [X] Dividends shall be applied on ex-date according to selected data policy.
- [X] Reverse-split fractional handling shall be explicitly configured.
- [X] Delisting handling shall explicitly realize the configured final economic outcome instead of silently dropping the symbol.
- [X] Delisting outcomes shall support final exchange price, final OTC or pink-sheet price, cash merger consideration, liquidation value, or conservative total-loss treatment where appropriate.
- [X] Mergers, delistings, spinoffs, rights issues, symbol changes, and special distributions shall block production-realistic equity or ETF labels when they intersect the requested date range, holdings, or pending orders unless explicitly supported.
- [X] Research-mode handling of unsupported corporate actions shall disclose the unsupported action and the selected conservative approximation.
- [X] The system shall support futures contract metadata.
- [X] The system shall support no futures rollover.
- [X] The system shall support continuous-adjusted rollover.
- [X] The system shall support physical close-and-reopen rollover.
- [X] Futures roll dates shall be deterministic and derived from contract metadata.
- [X] Continuous-adjusted data may support indicator continuity, but execution shall reference tradeable contract prices.
- [X] The system shall support disabled funding mode.
- [X] The system shall support fixed funding rate mode.
- [X] The system shall support historical funding rate mode.
- [X] Funding shall apply at exchange-defined funding timestamps.
- [X] Funding payment direction shall follow the configured exchange sign convention.
- [X] The system shall support fixed-rate conversion.
- [X] The system shall support spot-at-bar-close conversion.
- [X] Currency conversion rates shall come from a deterministic FX rate provider.
- [X] Direct currency pairs shall be preferred where available.
- [X] Inverse pairs may be used when enabled.
- [X] Cross-rate synthesis may be used when enabled and all legs are available.
- [X] FX conversion configuration shall expose `max_fx_rate_age_seconds` as the canonical maximum-rate-age field.
- [X] Intraday conversion shall default to a stricter maximum FX rate age than daily-bar conversion.
- [X] Cross-rate synthesis shall detect triangular arbitrage loops and circular paths in the FX provider graph.
- [X] Cross-rate synthesis shall reject highly skewed conversion paths when the synthesized rate differs from an available direct or inverse reference by more than the configured `max_cross_rate_skew_bps`.
- [X] Phase 1 shall default `max_cross_rate_skew_bps` to 25 basis points for validation fixtures and production-candidate runs.
- [X] The system shall calculate alpha when benchmark data is provided.
- [X] The system shall calculate beta when benchmark data is provided.
- [X] The system shall calculate information ratio when benchmark data is provided.
- [X] The system shall calculate tracking error when benchmark data is provided.
- [X] The system shall calculate benchmark-relative drawdown when benchmark data is provided.
- [X] The system shall preserve parent-child order lineage for trade decomposition.
- [X] The system shall preserve parent-child order lineage for partial fills.
- [X] The system shall preserve parent-child order lineage for bracket orders.
- [X] The system shall preserve parent-child order lineage for execution algorithms.
- [X] The system shall store parent order id, child order ids, fill ids, and linkage metadata when order chaining is enabled.
- [X] The system shall provide optional deterministic regulatory checks.
- [X] Regulatory checks may include short-sale locate checks.
- [X] Official AI Tools shall follow HaruQuant tool standards.
- [X] Official AI Tools shall include metadata.
- [X] Official AI Tools shall perform input validation.
- [X] Official AI Tools shall use structured logging.
- [X] Official AI Tools shall return deterministic error codes.
- [X] Official AI Tools shall avoid silent failures.
- [X] The first implementation slice shall be the Phase 1 FX canonical backtest slice.
- [X] Unsupported option or option-like instruments shall fail deterministically or run only in explicitly labelled research mode when a future research adapter exists.
- [X] Validation shall cover conceptual soundness, implementation correctness, input-data suitability, outcome analysis, stress behavior, monitoring approach, and known limitations.
- [X] A dynamic materiality upgrade shall require the stricter validation evidence and sign-off associated with the upgraded tier before production promotion.
- [X] The research protocol manifest shall include hypothesis, parameter search space, train/validation/test split, benchmark, objective function, minimum trade count, and promotion criteria.
- [X] Time-series validation shall support walk-forward, anchored walk-forward, rolling walk-forward, purged cross-validation, embargo windows, and out-of-time validation.
- [X] Production promotion shall require configured out-of-sample degradation thresholds.
- [X] Production promotion shall require sensitivity analysis around selected parameters.
- [X] Post-hoc selected strategies shall not be labelled production-realistic without explicit research-integrity approval.
- [X] Calibration artifacts shall include symbol, venue or broker profile, date range, account type, order type, order size distribution, data checksum, calibration version, and calibration timestamp.
- [X] Production-realistic execution models shall define acceptable error bands against observed historical, paper, or live execution data where available.
- [X] Uncalibrated execution models shall downgrade realism classification or require explicit approval.
- [X] Capacity diagnostics shall estimate performance degradation across configured capital, order-size, and participation-rate levels.
- [X] Production promotion shall define maximum approved capital, maximum order size, maximum participation rate, and approved instrument universe.
- [X] Strategies that exceed approved capacity limits shall be blocked from production promotion or explicitly downgraded.
- [X] Every external data source shall have a vendor or source inventory record.
- [X] Vendor records shall include provider, dataset, license scope, redistribution rights, retention rights, adjustment policy, timezone policy, revision policy, and support contact.
- [X] Production-realistic runs shall require point-in-time data snapshots or an explicit data-revision policy.
- [X] Data manifests shall record whether data is raw, adjusted, back-adjusted, survivorship-bias-free, point-in-time, revised, or vendor-restated.
- [X] Every production promotion shall produce a `simulator_promotion_manifest.json`.
- [X] Promotion shall require explicit classification: `research_only`, `mt5_parity_candidate`, `production_fx_candidate`, or asset-class-specific production candidate.
- [X] Empty data.
- [X] Duplicate timestamps.
- [X] Non-monotonic timestamps.
- [X] Zero or negative prices.
- [X] Price outliers.
- [X] Current-bar lookahead detected.
- [X] Volume below minimum.
- [X] Volume above maximum.
- [X] Volume step mismatch.
- [X] Stops-level violation.
- [X] Freeze-level violation.
- [X] Correlation limit exceeded.
- [X] Concentration limit exceeded.
- [X] Market closed.
- [X] Market order submitted outside session.
- [X] Weekend or session gap.
- [X] Gap through stop loss.
- [X] Gap through take profit.
- [X] Ambiguous same-gap SL/TP hit.
- [X] Unsupported fill policy.
- [X] Partial-fill remainder.
- [X] Limit order touched but queue not filled.
- [X] Order not found.
- [X] Sizing requires stop loss.
- [X] Commission calculation failure.
- [X] Monte Carlo failure.
- [X] Optimization failure.
- [X] Unsupported merger, spinoff, or delisting behavior.
- [X] Reverse split fractional quantity handling.
- [X] Continuous-adjusted indicator values used for non-tradeable execution prices.
- [X] SQLite sidecar index transaction fails.
- [X] Sandbox or vetting metadata is missing for code-based strategy execution.
- [X] FX cross-rate synthesis creates a circular path.
- [X] Timezone-naive timestamp.
- [X] Date range crosses a DST or session-boundary ambiguity.
- [X] Spring-forward local session time gap cannot be mapped to UTC.
- [X] Fall-back local session duplicate maps to multiple possible UTC instants.
- [X] Unauthorized actor attempts to launch a run.
- [X] Data manifest checksum mismatch.
- [X] Broker profile manifest is unavailable or checksum-mismatched.
- [X] Market-data authority manifest is unavailable, expired, or checksum-mismatched.
- [X] Concurrent read of `MarketDataAuthorityManifest` by multiple optimization workers.
- [X] Registered strategy reference tests proving raw Python strategy-code strings are rejected before import or execution.
- [X] Data authority tests proving `MarketDataAuthorityManifest` presence, checksum, point-in-time status, and authorization are validated before execution.
- [X] Timezone/DST tests proving broker-profile timezone rules map local sessions to UTC and reject unresolved spring-forward gaps or fall-back duplicate ambiguity before execution.
- [X] Concurrent manifest-read tests proving immutable `MarketDataAuthorityManifest` reads are thread-safe for multiple workers and conflicting manifest versions are rejected deterministically.
- [X] No-live-side-effect tests proving Simulator cannot call live broker mutation paths.
- [X] Import-time safety tests proving public Simulator imports perform no network, broker, filesystem write, worker, scheduler, or secret-read side effects.
- [X] Traceability tests shall verify every accepted implementation requirement has `requirement_id`, `phase`, `priority`, `acceptance_criteria`, `verification_method`, and at least one mapped verification gate.
- [X] Traceability tests shall verify no `future`, `enterprise`, or asset-class-expansion requirement is marked blocking for Phase 1 without owner approval.
- [X] Boundary tests shall verify Simulator does not call live broker execution paths and does not mutate strategy-owned state except through approved callbacks or returned diagnostics.
- [X] Market-calendar and gap tests shall cover market-closed rejection, session open, weekend gap, gap-through SL, gap-through TP, and SL/TP ambiguity.
- [X] Broker-rule tests shall cover supported fill policies, max pending orders, max positions, hedging/netting rules, and stopout thresholds.
- [X] Latency tests shall cover fixed latency, distribution latency, component latency, delayed eligibility, and latency interaction with missed fills.
- [X] Matching tests shall cover market order, pending trigger, stop-limit, SL/TP, gap, partial fill, and order-book fill.
- [X] Strategy tests shall cover EMA trend intents, martingale recovery, decomposition child orders, and partial-fill handling.
- [X] Execution-calibration tests shall cover missing calibration artifacts, stale calibration artifacts, calibration error-band failures, and uncalibrated realism downgrades.
- [X] Capacity tests shall cover capital scaling diagnostics, participation-rate limits, approved-capacity violations, and capacity disclosure.
- [X] Monte Carlo tests shall cover bootstrap reproducibility, confidence interval outputs, and failure handling.
- [X] Optimization tests shall cover grid/random runs, walk-forward IS/OOS split, overfit rejection, and deterministic parameter ranking.
- [X] Optimization-cache tests shall cover provenance hash hits, provenance hash misses, failed work-unit exclusion, resumable manifests, and isolated worker state.
- [X] Performance-gate tests shall cover runtime regression threshold, memory regression threshold, benchmark manifest fields, and benchmark-profile validation.
- [X] Benchmark tests shall cover benchmark alignment, currency conversion, alpha, beta, information ratio, tracking error, and benchmark-relative drawdown.
- [X] Order-chaining tests shall cover parent-child lineage, partial-fill child links, decomposition remainder, and bracket/OCO chain integrity.
- [X] Replay tests shall verify same seed, config, and data produce identical output.
- [X] Distributed-worker tests shall cover deterministic work-unit decomposition, stateless worker execution, shared artifact-store usage, cache checksum validation, worker heartbeat expiry, and preemptible-worker requeue.
- [X] Optional-service degradation tests shall cover warm-cache failure, SQLite sidecar outage, JSONL scan fallback, non-production degraded diagnostics, and production fail-closed behavior.
- [X] Feature-store tests shall cover point-in-time retrieval, availability timestamps, publication lag, microsecond decision timestamps, and feature lookahead rejection.
- [X] Determinism gate shall pass.
- [X] Execution realism gate shall pass.
- [X] MT5 parity gate shall pass within documented tolerance for supported semantics.
- [X] Performance gate shall pass before production promotion.
- [X] Research-integrity gate shall pass before production promotion.
- [X] Execution-calibration gate shall pass before production-realistic promotion when calibrated execution models are required.
- [X] Supply-chain gate shall pass before production release.
- [X] CI gate shall pass before production merge.
- [X] Ruff check shall pass.
- [X] Ruff format shall pass.
- [X] mypy strict shall pass for public modules.
- [X] `pytest` shall pass.
- [X] Test coverage shall be at least 80%.
- [X] Deterministic replay tests shall pass.
- [X] Broker-profile fixture tests shall pass.
- [X] Rounding and precision tests shall pass.
- [X] Security, redaction, and retention tests shall pass.
- [X] Optimization cache and resumability tests shall pass when optimization is enabled.
- [X] IOC remainder diagnostic tests shall pass.
- [X] Failed request that validates `SIM_ARBITRARY_CODE_REJECTED` before strategy import or execution.
- [X] Signals are converted to timestamped `TradeIntent` objects.
- [X] Before Builder handoff, every accepted requirement shall include `requirement_id`, `release_phase`, `priority`, `owner`, `status`, `acceptance_criteria`, `dependencies`, and `verification_method`.
- [X] Requirement IDs shall use stable prefixes such as `SIM-FR`, `SIM-NFR`, `SIM-SEC`, `SIM-EDGE`, `SIM-TEST`, `SIM-BR`, and `SIM-DOC`.
- [X] The test plan shall include a requirements-to-tests traceability matrix mapping every accepted requirement ID to one or more unit, integration, contract, replay, security, performance, CI, benchmark, or documented manual verification gates.
- [X] The first Builder-ready implementation scope shall be limited to the FX canonical backtest slice unless another phase slice is explicitly approved in `CHANGELOG.md`.
- [X] Phase 1 may preserve future enum values or metadata fields only when they are inert, documented as non-goals, and covered by deterministic unsupported-scope behavior.
- [X] `Phase 1 Specification`: FX canonical backtest requirements, exact API contracts, exact acceptance criteria, Phase 1 edge/error matrix, Phase 1 test suite, and Phase 1 traceability matrix.
- [X] Shared requirement IDs may appear in both tiers only when the Phase 1 requirement has a precise in-scope behavior and the annex references deferred extensions without changing the Phase 1 contract.
- [X] Strategies may maintain decision state but shall not mutate official trading state.
- [X] Vectorized processing is allowed only for indicator and signal generation.
- [X] Bar-open trading must use previous closed-bar data by default.
- [X] Production realism shortcuts must be explicitly configured.
- [X] A shortcut shall never be silently assumed.
- [X] A simulator must declare asset-class realism requirements for selected instruments.
- [X] Equities and ETFs require corporate-action treatment for production-realistic classification.
- [X] Production merge requires CI gates to pass with coverage at least 80%.
- [X] A batched range shall never skip a possible execution, risk, accounting, session, rollover, or compliance event.
- [X] FX conversion shall fail closed when rate age exceeds the configured maximum unless diagnostic override is explicitly enabled.
- [X] Feature-store configuration for point-in-time feature retrieval when machine-learning features are used.
- [X] Alternative-data configuration for source timing, publication delay, ingestion delay, as-of alignment, lag policy, and embargo policy when non-price data is used.
- [X] Resource quota configuration for concurrent runs, wall-clock time, temporary storage, queued runs, and worker limits.
- [X] Market data from a provider.
- [X] OHLCV bar data.
- [X] Indicator specifications.
- [X] Optional order-book depth data.
- [X] Optional feature-store data and point-in-time feature manifests.
- [X] Optional alternative data such as sentiment, fundamentals, news, options flow, and external signals.
- [X] Optional market-halt and limit-up/limit-down data.
- [X] Optional corporate-action data.
- [X] Optional futures contract-chain data.
- [X] Optional perpetual funding-rate data.
- [X] Optional FX conversion-rate data.
- [X] Optional benchmark data.
- [X] Optional optimization configuration.
- [X] Optional Monte Carlo configuration.
- [X] Required `MarketDataAuthorityManifest` for production-realistic runs.
- [X] Required broker profile manifest for MT5-parity and production-realistic FX runs.
- [X] `max_cross_rate_skew_bps` for cross-rate synthesis validation.
- [X] Orders history.
- [X] Deals history.
- [X] Trade list.
- [X] Partial-fill history.
- [X] Exposure curve.
- [X] Monte Carlo confidence bands when enabled.
- [X] Environment diagnostic hash and environment drift warning when applicable.
- [X] Queue, scheduler, worker, quota, and checkpoint metadata for service-mode runs.
- [X] Latency diagnostics when execution latency modelling is enabled.
- [X] Feature-store and alternative-data alignment diagnostics when ML or non-price data is used.
- [X] Step-through replay metadata when debugger mode is used.
- [X] Rejected FX cross-rate synthesis diagnostics.
- [X] Usage examples shall run end-to-end.
- [X] Optional enterprise feature contracts shall be defined early to avoid breaking redesign.
- [X] Release notes shall reference the applicable `simulator_promotion_manifest.json`.
- [X] Documentation shall describe approved strategy input modes, strategy registry behavior, and sandbox/vetting requirements if code-based strategy execution is ever enabled.

#### `app/services/simulator/trader.py`

Functions/classes:

- `SimTrader`
- `TradeIntent`
- `TradeRequest`

Requirements:

- [X] Conversion of timestamped `TradeIntent` objects into sized `TradeRequest` objects.
- [X] Simulator-only trader interface and MT5-style simulated order/query semantics.
- [X] Provide simulator-compatible MT5-style accessors and trader methods for controlled strategy integration, including historical tick/bar accessors, symbol/account accessors, order submission/modification/deletion, position queries, order queries, deal/order history, margin/profit calculation, and terminal-style simulator status.
- [X] Every MT5-style `SimTrader` method exposed to strategies shall define request fields, return fields, mutable-state effects, deterministic rejection codes, and read-only snapshot guarantees before implementation.
- [X] The system shall transform `TradeIntent` into a sized `TradeRequest`.
- [X] The system shall support MT5-style `order_send`.
- [X] `order_send` shall accept action, magic, order, symbol, volume, price, stop-limit price, stop loss, take profit, deviation, order type, fill policy, time policy, expiration, comment, position id, and opposite position id where supported by account mode.
- [X] The system shall support position modification.
- [X] The system shall expose MT5-style `position_modify` for stop-loss, take-profit, and supported mutable position fields.
- [X] The system shall support position close.
- [X] The system shall expose MT5-style `position_close`.
- [X] The system shall support order modification.
- [X] The system shall expose MT5-style `order_modify` for pending-order price, stop-limit price, stop loss, take profit, expiration mode, and expiration timestamp.
- [X] The system shall support order deletion.
- [X] The system shall expose MT5-style `order_delete`.
- [X] The system shall support atomic cancel-replace operations for pending orders where broker or venue semantics allow them.
- [X] Cancel-replace operations shall preserve, reset, or recompute queue priority according to configured venue rules and shall journal the chosen behavior.
- [X] The system shall support querying open positions.
- [X] The system shall expose MT5-style `positions_get` and `positions_total`.
- [X] The system shall support querying open orders.
- [X] The system shall expose MT5-style `orders_get` and `orders_total`.
- [X] The system shall support querying historical deals.
- [X] The system shall expose MT5-style `history_deals_get` and `deals_total`.
- [X] The system shall support querying historical orders.
- [X] The system shall expose MT5-style `history_orders_get` and `history_orders_total`.
- [X] The system shall support querying account info.
- [X] The system shall expose MT5-style `account_info`.
- [X] The system shall expose MT5-style `order_calc_margin` for pre-trade margin estimation.
- [X] The system shall expose MT5-style `order_calc_profit` for mark-to-market or hypothetical trade profit estimation.
- [X] The same Trader protocol shall support both simulator and live adapters where live trading is enabled outside the simulator.
- [X] The simulated Trader protocol shall preserve the same request, response, and query semantics as the live adapter for shared strategy code.
- [X] Shared Trader protocol definitions may be shared across Simulator and Live/Trading, but Simulator shall implement only simulated behavior and shall not import, instantiate, or call live adapter implementation code.
- [X] The system shall support `on_tick` callbacks for event-driven strategy execution.
- [X] The system shall support `on_bar` callbacks for bar-boundary strategy execution.
- [X] The system shall provide a terminal-style interface for simulator status, account state, open positions, pending orders, and trade events.
- [X] Terminal-style output shall be controlled by an explicit `verbose` configuration flag.
- [X] Visual simulator mode shall be supported only as a diagnostic or research view and shall not alter canonical execution results.
- [X] Progress reporting shall be available for long-running official simulators, optimizations, walk-forward runs, and Monte Carlo runs.
- [X] The system shall support deterministic step-through replay for debugging.
- [X] Step-through replay shall allow pausing at a configured timestamp, journal sequence, order event, deal event, bar boundary, strategy callback, or error condition.
- [X] Debugger hooks shall expose read-only snapshots of tick state, order book where available, orders, deals, positions, account state, strategy-visible inputs, and selected strategy diagnostics.
- [X] Resuming from a debugger pause shall preserve deterministic replay and shall not alter official results unless a diagnostic mutation mode is explicitly enabled.
- [X] The simulator module shall accept timestamped `TradeIntent` objects from approved strategies and shall convert them into sized `TradeRequest` objects before execution.
- [X] Regulatory checks may include pattern day trader checks.
- [X] Initial US regulatory checks shall include pattern day trader disclosure, short-sale locate configuration, short-sale restriction support where data exists, and position-limit checks where configured.
- [X] The simulator shall support live/simulator parity through an MT5-style `SimTrader` protocol.
- [X] The `SimTrader` shall expose MT5-style trading methods to strategies through controlled interfaces.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.
- [X] Pending: the referenced Hardened Draft v1.6 specification, strategy contracts, indicator contracts, data contracts, broker-profile manifests, and market-data authority manifests must be attached or summarized before Builder handoff.
- [X] Strategy implementation requirements live in `docs/source-requirements/04-strategy.md`.
- [X] MT5 Strategy Tester semantics are an inspiration and parity target for selected controlled cases, not necessarily a guarantee of exact MT5 behavior for every broker-specific case.
- [X] Compliance records shall provide evidence of pre-trade checks and risk decisions.
- [X] Unhandled exceptions at controlled tool boundaries MUST be mapped to `SIM_INTERNAL_ERROR`, logged at `ERROR` level with redacted context, and must not expose secrets, raw strategy code, credentials, or private payloads.
- [X] MT5-parity tests shall compare supported behavior against controlled MT5 Strategy Tester scenarios.
- [X] Pre-trade checks and risk-check evidence shall be recorded.
- [X] `simulator.runner` may launch runs only for authorized strategy ids, data scopes, and artifact roots.
- [X] Strategy files, market data paths, broker profiles, and artifact destinations shall be resolved through approved registries or allowlisted roots, not arbitrary user-supplied filesystem paths.
- [X] The tool wrapper shall prevent unregistered or unapproved strategy modules from being invoked.
- [X] Sandbox policy shall define allowed imports, denied imports, filesystem access, network access, subprocess access, environment-variable access, timeouts, memory limits, and prohibited operations before any code-based strategy path is enabled.
- [X] The system shall return `SIM_RESEARCH_PROTOCOL_MISSING` when a production-candidate optimized strategy lacks the required research protocol manifest.
- [X] The system shall not log unsafe raw strategy code bodies in full when rejecting arbitrary-code input.
- [X] Strategy-input rejection diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code.
- [X] `SIM_PORTFOLIO_RISK_REJECTED`
- [X] Mandatory inbound-contract validation for `MarketDataAuthorityManifest` supplied by `app/services/data/` and strategy registry references supplied by `app/services/strategies/` before official runs.
- [X] The module does not own production risk-governor policy, external governance policy, or human approval workflows.
- [X] `strategy_ref` shall be a registered strategy identifier plus version or hash; raw Python code strings are invalid.
- [X] The system shall support fixed-risk sizing.
- [X] The system shall reject fixed-risk sizing when stop loss is missing.
- [X] The system shall validate portfolio risk availability.
- [X] Compliance records shall include risk-check result.
- [X] Compliance records shall include optional strategy name and version.
- [X] The simulator module shall consume strategy outputs through the strategy module contract defined in `docs/source-requirements/04-strategy.md`.
- [X] Monte Carlo outputs shall include risk of ruin.
- [X] The system shall align benchmark data to the same clock and currency as the strategy.
- [X] Internal-only fields, secrets, raw credentials, and proprietary strategy source shall not appear in official AI Tool responses.
- [X] Rejected strategy-input diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code.
- [X] Strategy research runs shall record a research protocol manifest before optimization begins.
- [X] Portfolio-risk rejection.
- [X] Strategy identifier does not exist in registry.
- [X] Strategy identifier resolves to an unapproved module.
- [X] Security tests shall cover local trusted mode, external authentication requirement, RBAC authorization, allowlisted strategy/data/artifact roots, secret rejection, and safe errors.
- [X] Portfolio risk gate shall pass for multi-symbol runs.
- [X] Portfolio-risk tests shall pass.
- [X] AI Tool strategy-injection rejection tests shall pass.
- [X] Successful canonical FX backtest using a registered strategy id and approved data/broker manifests.
- [X] External contracts required for implementation shall be attached or summarized in this file before Builder handoff, including strategy outputs, indicator manifests, data manifests, broker profiles, market-data authority manifests, and the active source-of-truth baseline.
- [X] Registered strategy identifier and validated strategy configuration.
- [X] Portfolio-risk summary.
- [X] Rejected strategy-injection diagnostics.
- [X] Strategy developer shall provide vectorized or event-driven strategy logic.
- [X] Vectorized signal strategy shall compute indicators, generate signals, and convert signals to trade intents.
- [X] Documentation shall include strategy-capacity diagnostics and production capacity approval procedures.

#### `app/services/simulator/models/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.
- [X] Asset-class production realism depends on enabled models and available data.
- [X] When Python minor version, dependency lock hash, platform, or decimal/numeric backend differs from the certified profile, official results shall record an environment drift diagnostic and shall not be used for production promotion without compatibility evidence.
- [X] The system shall stop the simulator on accounting invariant violations unless diagnostic mode is configured.
- [X] Diagnostic mode shall mark results `diagnostic_failed`, prevent optimization ranking, prevent benchmark promotion, and exclude the run from canonical performance comparisons.
- [X] Production promotion shall require recorded benchmark results.
- [X] FX conversions shall store source rate precision, conversion timestamp, and converted cashflow rounded to the account currency precision at the accounting boundary.
- [X] Production service mode shall enforce per-user, per-tenant, or per-request resource quotas.
- [X] The complete resolved configuration for a production run shall be serialized into an immutable run-configuration artifact stored alongside results.
- [X] Production service mode shall define maximum request payload size, maximum resolved configuration size, maximum artifact path length, maximum diagnostic payload size, maximum run duration, maximum queue wait, and maximum retry count before implementation.
- [X] Canary divergence shall block promotion or trigger rollback without changing the primary user-facing result for the request.
- [X] Official AI Tool exports shall require or create request id.
- [X] Compliance records shall be created for accepted and rejected trade requests.
- [X] Every official run shall record actor id, auth context, role, request id, and authorization decision in audit metadata.
- [X] External data-provider or broker credentials shall be read only from approved secrets providers or environment bindings and shall never be accepted as plain request payload fields.
- [X] Externally accessible simulator tools shall not be enabled until threat model, data-governance review, RBAC configuration, redaction policy, retention policy, and protected-artifact policy are approved.
- [X] Accounting invariant violation shall stop the simulator unless diagnostic mode is explicitly enabled.
- [X] Missing required model data shall fail fast or be explicitly recorded as an approximation.
- [X] The system shall return `SIM_RUN_ID_CONFLICT` when a run id or request id conflicts with an existing incompatible run.
- [X] The system shall return `SIM_MODEL_GOVERNANCE_EXPIRED` when a required model inventory record or approval is expired.
- [X] The system shall return `SIM_RESOURCE_QUOTA_EXCEEDED` when a request exceeds configured resource quotas.
- [X] `SIM_UNSUPPORTED_COMMISSION_MODEL`
- [X] `SIM_POSITION_NOT_FOUND`
- [X] `SIM_MODEL_GOVERNANCE_EXPIRED`
- [X] `SIM_ACCOUNT_INVARIANT_BROKEN`
- [X] The module does not own indicator formula implementation or indicator result contracts; those belong to `app/services/indicators/`.
- [X] The system shall produce a structured `SimulatorResult`.
- [X] Latency models shall support fixed, distribution-based, venue-profile-based, and disabled modes.
- [X] The system shall enforce maximum total positions when configured.
- [X] The system shall enforce maximum positions per symbol when configured.
- [X] The system shall support hedging account behavior when configured.
- [X] The system shall support netting account behavior when configured.
- [X] The system shall support negative-balance-protection configuration.
- [X] The system shall liquidate deterministically during stopout, defaulting to largest losing position first.
- [X] MT5 parity evidence shall record broker profile id, broker server label, account type, MT5 build, capture timestamp, symbol specification hash, and fixture data hash.
- [X] No external broker brand or live account shall be globally authoritative; production parity applies only to approved broker profiles and fixtures.
- [X] The system shall allow strategies to request a sizing mode but not directly finalize official volume.
- [X] The system shall apply deals to positions and account state.
- [X] The system shall recalculate account state.
- [X] The system shall enforce `Equity = Balance + FloatingPnL`.
- [X] The system shall create a compliance or audit record for every accepted trade request.
- [X] The system shall create a compliance or audit record for every rejected trade request.
- [X] Compliance records shall include request id.
- [X] Walk-forward results shall separate in-sample and out-of-sample metrics.
- [X] Optimization caching shall reuse only completed work units whose provenance hash exactly matches the requested run.
- [X] Optimization result ranking shall be deterministic when objective scores tie.
- [X] Monte Carlo analysis shall not replace the official backtest result.
- [X] Benchmark results shall be required before production promotion.
- [X] Benchmark results shall be stored with release notes.
- [X] Benchmark manifests shall record OS, CPU model, logical CPU count, RAM, storage type, Python version, dependency lock hash, git commit, and benchmark dataset hash.
- [X] The system shall support equity.
- [X] The system shall downgrade realism labels when required asset-class models are disabled.
- [X] The system shall support corporate-action treatment for production-realistic equity and ETF backtests.
- [X] Long positions shall receive eligible dividend cashflows.
- [X] Short positions shall pay applicable dividend cashflows.
- [X] Dividend cashflows shall be converted to account base currency.
- [X] Cash dividends, stock splits, and reverse splits shall be the first supported corporate-action treatments for equity and ETF production realism.
- [X] The system shall support optional short-locate recall and forced buy-in modelling for equity and ETF short positions.
- [X] Recall models shall support deterministic configured recall events and seeded probabilistic recall rates by symbol, borrow status, and date.
- [X] Funding shall convert to account base currency.
- [X] Regulatory checks may include position-limit checks.
- [X] Wash-sale diagnostics shall flag loss sales followed by repurchases of substantially identical instruments within the configured window and shall disclose after-tax PnL impact only when tax modelling is enabled.
- [X] Official AI Tools shall require or create request id.
- [X] Equity, futures, perpetual, and multi-currency examples shall be required before those asset classes are promoted to production-realistic status.
- [X] Every production-candidate simulator model shall have a model inventory record.
- [X] Model inventory records shall include model id, owner, purpose, approved use cases, prohibited use cases, asset-class scope, version, dependencies, validation status, materiality tier, known limitations, and review expiry.
- [X] Production promotion shall require independent validation or documented second-party review for material models.
- [X] Every model exception, override, accepted limitation, and temporary approval shall require owner, approver, rationale, expiry date, and audit record.
- [X] Production models shall require periodic re-validation after material code, data, broker-profile, dependency, or calibration changes.
- [X] Expired, unapproved, or materially changed model inventory records shall block production-realistic classification unless an explicit governance override is present.
- [X] Retrying the same request id shall be idempotent unless explicitly configured to create a new run id.
- [X] Unsupported commission model.
- [X] Position not found.
- [X] Accounting invariant violation.
- [X] Malformed request payload.
- [X] Unknown request field.
- [X] Missing required request field.
- [X] Request payload exceeds configured size limit.
- [X] Secrets, tokens, broker credentials, authorization headers, or provider credentials are supplied in request payload fields.
- [X] Duplicate request id is submitted concurrently.
- [X] Duplicate request id is replayed with incompatible material fields.
- [X] Request validation tests for required fields, unknown fields, malformed payloads, invalid enum casing, invalid date range, missing symbol, oversized payload, path traversal, and secrets in payload fields.
- [X] Model-governance tests shall cover model inventory validation, expired approvals, missing validation evidence, and accepted model exceptions.
- [X] Regulatory-constraint tests shall cover PDT rule, short-sale locate, position limits, and disabled-regulatory disclosure.
- [X] Wash-sale tests shall cover optional taxable-account diagnostics, configured windows, substantially identical instrument mapping, and after-tax disclosure when enabled.
- [X] Accounting gate shall pass.
- [X] Model-governance gate shall pass before production promotion.
- [X] Accounting invariant tests shall pass.
- [X] Failed request that validates `SIM_INVALID_DATE_RANGE` before data access.
- [X] A run shall not be labelled production-realistic unless required asset-class models are enabled or proven unnecessary.
- [X] Monte Carlo analysis must not replace the official backtest result.
- [X] Structured `SimulatorResult`.
- [X] Account snapshots.
- [X] Equity curve.
- [X] Balance curve.
- [X] Optimization result set with hashes, random seed, and objective function.
- [X] Structured error result with deterministic error code on failure.
- [X] Canary comparison results and synthetic transaction probe results when production monitoring is enabled.
- [X] Visual trade replay export artifact when requested.
- [X] Benchmark results shall be stored with release notes before production promotion.
- [X] Release documentation shall include model-validation, research-integrity, calibration, security, and benchmark evidence links for production promotions.
- [X] Documentation shall include a threat model and data-governance guide before any externally accessible simulator tool is enabled.
- [X] Documentation shall include model-governance and model-inventory operating procedures.
- [X] Documentation shall include dynamic model materiality assessment rules and evidence requirements.

#### `app/services/simulator/models/tick.py`

Functions/classes:

- `TradeIntent`
- `FAST_RESEARCH`
- `INTRABAR_EVENT`
- `TIMEFRAME_TICKS`
- `M1_TICKS`
- `REAL_TICKS`
- `SYNTHETIC_TICKS`
- `run_backtest`
- `SimulatorConfig`

Requirements:

- [X] Tick generation, tick stream construction, spread modelling, slippage modelling, liquidity modelling, matching, partial-fill handling, same-tick event priority, gap handling, commission/fee/swap/funding/borrow-fee accounting, and portfolio-level simulator state.
- [X] Run official tick-based backtests and return standard official tool envelopes.
- [X] `SimulatorBacktestRequestV1` fields: `schema_version`, `request_id`, `actor_context`, `strategy_ref`, `strategy_config`, `symbols`, `timeframe`, `start`, `end`, `initial_balance`, `account_currency`, `tick_model`, `spread_model`, `slippage_model`, `commission_model`, `swap_model`, `broker_profile_ref`, `market_data_authority_ref`, `journal_persistence`, `artifact_root_ref`, `realism_profile`, and `metadata`. *app/services/simulator/models/tick.py:130*
- [X] The system shall run data-quality checks before indicator calculation, signal generation, or tick generation.
- [X] The system shall build a canonical bid/ask tick stream before official execution.
- [X] The system shall use tick execution as the only official production execution mode.
- [X] The system shall use the canonical bid/ask tick stream as the official execution clock.
- [X] The system shall convert bar-level or vectorized signals into timestamped `TradeIntent` objects before execution.
- [X] The system shall execute `TradeIntent` objects only when the tick loop reaches an eligible tick.
- [X] The system shall prevent vectorized execution from producing official fills, account state, trade journals, or reports.
- [X] The system shall support an optional approximate `FAST_RESEARCH` mode only when the result is clearly marked as non-canonical, non-MT5-parity, and non-production-realistic.
- [X] At the first tick of bar `N`, the system shall allow strategies to use only bars up to and including fully closed bar `N-1`.
- [X] At the first tick of bar `N`, the system shall prohibit use of current incomplete bar `N` high, low, close, or volume.
- [X] The system shall enter at the first valid tick of bar `N` when a valid trade intent is emitted from previous-closed-bar data.
- [X] The system shall support `INTRABAR_EVENT` strategies only for event strategies using current tick data.
- [X] The system shall support `TIMEFRAME_TICKS`.
- [X] The system shall support `M1_TICKS`.
- [X] The system shall support `REAL_TICKS`.
- [X] The system shall support `SYNTHETIC_TICKS`.
- [X] The system shall represent every execution tick with time, symbol, bid, ask, optional last price, optional volume, source, optional bar time, sequence-in-bar, and bar-open flag.
- [X] The system shall open buy positions at ask.
- [X] The system shall close buy positions at bid.
- [X] The system shall open sell positions at bid.
- [X] The system shall close sell positions at ask.
- [X] The system shall convert strategy-timeframe OHLC bars into four-tick paths when using `TIMEFRAME_TICKS`.
- [X] The system shall convert M1 OHLC bars into four-tick paths when using `M1_TICKS`.
- [X] The system shall pass broker real ticks through in `REAL_TICKS` mode when bid/ask data is available.
- [X] The system shall merge bar-based signal timelines into the real tick stream in `REAL_TICKS` mode.
- [X] The system shall generate `SYNTHETIC_TICKS` from M1 OHLCV bars using an MQL5 Article #75-style support-point algorithm, not a simple four-price path.
- [X] The system shall treat generated OHLC-derived synthetic prices as bid prices and derive ask prices through the spread model.
- [X] The system shall produce deterministic synthetic ticks for identical M1 data, symbol spec, spread config, and random seed.
- [X] Synthetic tick generation shall derive a deterministic per-bar seed instead of relying only on a single mutable global random sequence.
- [X] The per-bar synthetic-tick seed shall be derived with SHA-256 from schema version, `global_seed`, `symbol_hash`, UTC `bar_open_timestamp`, and synthetic tick algorithm version.
- [X] `symbol_hash` shall be derived from the canonical JSON representation of the full `SymbolSpec`, including normalized symbol, broker profile id, point, tick size, tick value, contract size, currencies, sessions, and volume constraints.
- [X] Synthetic tick generation shall remain reproducible when bars are processed out of chronological order.
- [X] Synthetic tick generation shall remain reproducible when bars are processed in date chunks or parallelized by symbol.
- [X] Synthetic tick generation shall remain reproducible when a run resumes from a checkpoint.
- [X] Synthetic tick generation shall journal or expose per-bar seed derivation metadata sufficient to replay a generated bar's tick path.
- [X] The simulator shall support data modelling modes equivalent to real ticks, simulated ticks, M1 OHLC, trading-timeframe OHLC, and calculation-only research data where explicitly labelled.
- [X] The simulator shall expose MT5-style historical tick accessors `copy_ticks_from` and `copy_ticks_range` for simulator-compatible data providers.
- [X] The simulator shall expose MT5-style historical bar accessors `copy_rates_from`, `copy_rates_from_pos`, and `copy_rates_range` for simulator-compatible data providers.
- [X] The simulator shall expose MT5-style `symbol_info_tick` and `symbol_info` accessors for simulator-compatible symbol metadata and latest tick state.
- [X] The system shall calculate ask for generated ticks as bid plus spread points multiplied by symbol point.
- [X] The system shall record spread source and spread points per tick or journal checkpoint.
- [X] Trade intents shall become eligible for matching only after the configured latency delay has elapsed on the canonical tick clock.
- [X] The system shall estimate available volume from tick volume, M1 volume, or configured symbol liquidity when using volume-dependent liquidity.
- [X] The system shall make liquidity decisions deterministically for the same tick, configuration, seed, and order request.
- [X] The system shall mark the first tick after a session break or weekend as a gap tick.
- [X] The system shall support treating gap-crossed stop losses as market orders at the first available tick.
- [X] Gap ambiguity handling shall journal candidate outcomes, selected outcome, rejected alternative, first available tick, affected order ids, and the deterministic reason code.
- [X] The system shall process same-tick events through a deterministic priority queue.
- [X] The system shall order same-tick events by tick time, explicit priority, and monotonic sequence number.
- [X] The system shall process stopout before other same-tick events by default.
- [X] The system shall process expiration before new triggers for the same timestamp.
- [X] The system shall process existing position exits before new signal intents by default.
- [X] The system shall use conservative SL/TP tie-breaking by default unless another mode is explicitly configured.
- [X] The system shall journal priority decisions for replay.
- [X] The system shall support daily end-of-day, tick-by-tick, and on-close-only swap calculation modes.
- [X] The system shall validate OHLCV and tick schemas. *app/services/simulator/validation/quality.py:14*
- [X] The `MarketDataAuthorityManifest` shall declare authoritative sources for bars, real ticks, spreads, corporate actions, futures chains, funding rates, FX conversion rates, and benchmark series.
- [X] Data lineage shall form a directed acyclic graph tracing from journaled deal or account event to generated tick, support point, M1 bar, normalized source row, raw vendor data file, source manifest, and checksum where applicable.
- [X] Alternative data shall align to the canonical tick clock without lookahead, using explicit as-of joins and configured lag or embargo policies.
- [X] The system shall reject missing tick value or point value when required for sizing.
- [X] Trailing stops shall update deterministically from eligible tick data and shall never use future bar high, low, close, or volume.
- [X] Pegged-order repricing shall follow explicit tick-size, latency, queue-priority, and market-data availability rules.
- [X] The system shall mark open positions to market on ticks.
- [X] The journal shall record tick model.
- [X] The simulator module shall execute strategy-generated trade intents only when the canonical tick loop reaches an eligible tick.
- [X] The simulator module shall run data-quality checks before indicator calculation, signal generation, or tick generation.
- [X] The system shall report ticks processed.
- [X] Visual replay exports shall include candles or tick references, strategy signals, order events, fills, position state, equity or balance overlays, drawdown overlays, and annotations for rejections or halts.
- [X] The system shall benchmark tick generation speed.
- [X] The system shall benchmark tick loop speed.
- [X] Tick batching may accelerate pure mark-to-market updates.
- [X] Tick batching shall stop immediately at any tick that may trigger state transitions or compliance events.
- [X] Tick batching shall never reorder ticks.
- [X] Tick batching shall never suppress per-event accounting invariants.
- [X] Tick batching shall be permitted only between known pre-calculated boundary events.
- [X] Tick batching shall use active pending-order trigger prices, stop-loss prices, take-profit prices, expiration times, stopout thresholds, bar-open times, session boundaries, gap boundaries, swap rollover times, scheduled intent activations, strategy callback boundaries, and compliance boundaries to determine safe batch ranges.
- [X] Tick batching shall stop before the nearest active boundary that may cause a state transition.
- [X] Tick batching shall not evaluate or skip past a tick that may trigger a state change.
- [X] Tick batching shall never infer safety from future bar high, low, close, or volume values unavailable at the current tick.
- [X] Tick-batching safety diagnostics shall be emitted when batching is enabled.
- [X] Phase 1 tick batching shall use a conservative boundary-interval proof model that batches only across intervals where all active trigger, session, rollover, strategy, and compliance boundaries are known before the batch starts.
- [X] FX `production_realistic` V1 classification shall require a documented checklist before Builder handoff. At minimum, the checklist shall evaluate data-quality pass status, approved broker profile, approved market-data authority manifest, tick model, spread model, slippage model, commission model, swap model, margin model, currency-conversion model, no-lookahead status, journal persistence status, replayability, and explicit realism downgrades.
- [X] The first production FX slice shall cover deterministic tick execution, spreads, slippage, commission, swap, margin, market hours, multi-currency conversion, portfolio checks, journal integrity, and report schemas.
- [X] Borrow fees shall be applied daily or tick-by-tick according to configuration.
- [X] Forced buy-ins shall close affected short positions at the first eligible market tick subject to configured latency, liquidity, fees, and market-halt rules.
- [X] Futures contract metadata shall include root symbol, contract symbol, expiry, first notice date, last trade date, contract size, tick size, tick value, margin currency, and settlement currency.
- [X] The system shall support real-time tick funding rate mode.
- [X] The system shall support real-time-tick conversion.
- [X] Maximum FX rate age shall be configurable by conversion context, including intraday tick conversion, bar-close conversion, daily-bar conversion, margin conversion, fee conversion, dividend conversion, funding conversion, and report-only conversion.
- [X] Initial US regulatory checks shall explicitly support SEC Rule 201 alternative uptick-rule restrictions where required data is available.
- [X] Release readiness examples shall include one FX MT5-parity fixture run, one FX production-realistic single-symbol run, one FX multi-symbol portfolio run, one synthetic-tick research approximation run, one severe-data-quality blocked run, one deterministic replay run, and one JSON plus Markdown report pair.
- [X] Implementation tickets and release manifests shall assign traceability ids such as `SIM-FR-001`, `SIM-NFR-001`, and `SIM-BR-001` to accepted requirements before implementation begins.
- [X] Implementation tickets and release manifests shall include priority, release phase, owner, acceptance criteria, and verification method for each accepted requirement.
- [X] Every official run shall use a deterministic lifecycle state machine: `created`, `validated`, `data_prepared`, `signals_built`, `ticks_built`, `executing`, `reporting`, `completed`, `failed`, and `cancelled`.
- [X] The promotion manifest shall include requirement ids, implementation tickets, test evidence, benchmark evidence, replay evidence, model-validation evidence, security evidence, known exceptions, approvers, approval timestamp, expiry, and release artifact hashes.
- [X] The same configuration, data, and seed shall produce the same tick stream. *tests/unit/app/services/simulator/test_08a_foundation.py:48*
- [X] Python tick loop with no trade events should target at least 10,000 ticks per second.
- [X] Synthetic tick generation should target at least 100,000 generated ticks per second where possible.
- [X] Simple four-tick OHLC generation shall remain separate from MQL5-style synthetic tick generation.
- [X] MT5 parity comparisons shall require execution timestamps to match the fixture tick timestamp for the same eligible tick.
- [X] MT5 parity price comparisons shall tolerate at most one half of the symbol tick size, unless the approved broker fixture documents a stricter tolerance.
- [X] Tradable prices shall be normalized to the symbol tick size.
- [X] Conservative price rounding shall default to adverse rounding: buy-side executable prices round up to the next valid tick and sell-side executable prices round down to the next valid tick when exact normalization is required.
- [X] Telemetry shall include stage duration, tick generation rate, tick loop rate, memory high-water mark, journal flush latency, journal backlog, data-quality failure counts, rejection counts, fill counts, and report-generation duration.
- [X] Every major pipeline stage shall emit an OpenTelemetry-compatible trace span, including validation, data preparation, signal generation, tick generation, execution, reporting, and artifact persistence.
- [X] `SIM_UNSUPPORTED_TICK_MODEL`
- [X] `SIM_SYNTHETIC_TICK_GENERATION_FAILED`
- [X] Phase 1 shall include only `run_backtest`, deterministic tick execution, approved FX symbol metadata, broker-profile fixtures, registered strategy references with validated configuration, data-quality gates, tick generation, spread/slippage/commission/swap models, journal persistence, JSON reports, Markdown reports, schema validation, replay tests, and no-live-side-effect guarantees.
- [X] All official backtests must execute through a tick loop.
- [X] A global random seed alone shall not be sufficient for synthetic tick generation in production mode.
- [X] Synthetic tick randomness shall be locally reproducible per symbol and per bar.
- [X] `SimulatorConfig` with strategy settings, symbols, timeframe, start date, end date, execution mode, tick model, data modelling mode, spread model, signal timing, sizing mode, initial deposit, leverage, margin mode, slippage configuration, optimization configuration, visual mode, progress reporting, terminal verbosity, and random seed.
- [X] M1 OHLCV data when M1 or synthetic tick generation is used.
- [X] Real bid/ask tick data when real-tick mode is used.
- [X] Symbol specifications including point, tick size, tick value, contract size, volume min/max/step, asset class, currencies, sessions, and broker constraints.
- [X] Required `global_seed` for deterministic synthetic tick generation.
- [X] Derived `symbol_hash` for per-symbol synthetic tick seed derivation.
- [X] `bar_open_timestamp` for per-bar synthetic tick seed derivation.
- [X] Tick-batching boundary metadata derived from active orders, positions, session boundaries, gap boundaries, rollover boundaries, compliance boundaries, and scheduled strategy events.
- [X] Per-bar synthetic tick seed derivation metadata or replay metadata.
- [X] Market-halt, limit-up/limit-down, kill-switch, trailing-stop, pegged-order, cancel-replace, recall, forced-buy-in, wash-sale, and alternative-uptick-rule diagnostics when applicable.
- [X] Tick-batching safety diagnostics when batching is enabled.
- [X] Event strategy shall respond to initialization, bar-open, tick, and trade-transaction events.
- [X] Every report shall disclose tick model.
- [X] Reports shall disclose tick-batching safety diagnostics when batching is enabled.
- [X] The journal shall document per-bar synthetic tick seed derivation metadata when generated ticks are used.
- [X] External synthetic tick algorithm reference shall be documented as MQL5 Article #75.
- [X] Documentation shall describe per-bar synthetic tick seed derivation, including SHA-256 inputs, `global_seed`, `symbol_hash`, UTC `bar_open_timestamp`, and replay metadata.
- [X] Documentation shall describe checkpoint and replay behavior for synthetic tick generation.
- [X] Documentation shall describe tick-batching safety boundaries and the Phase 1 boundary-interval proof model.
- [X] The requirements are domain-wide supporting requirements under `docs/source-requirements/`, not a sprint-specific implementation ticket.
- [X] Tick execution is the canonical production mode.
- [X] No file-specific non-functional requirements defined.
- [X] Unsupported tick model.
- [X] Tick volume less than or equal to zero.
- [X] Synthetic tick generation with tick volume equal to 1.
- [X] Synthetic tick generation with tick volume equal to 2.
- [X] Synthetic tick generation with tick volume equal to 3.
- [X] Synthetic tick generation with tick volume greater than 3.
- [X] Generated ticks exceeding OHLC bounds.
- [X] Same-tick SL/TP conflict.
- [X] Stopout and strategy intent on same tick.
- [X] Pending order expiration and trigger on same tick.
- [X] Synthetic tick generation resumes from checkpoint mid-run.
- [X] Synthetic tick generation is parallelized by symbol.
- [X] Synthetic tick generation is parallelized by date chunk.
- [X] Synthetic tick generation processes bars out of chronological order.
- [X] Tick batching approaches active stop loss.
- [X] Tick batching approaches active take profit.
- [X] Tick batching approaches pending-order trigger.
- [X] Tick batching approaches order expiration.
- [X] Tick batching approaches stopout threshold.
- [X] Tick batching approaches bar-open signal boundary.
- [X] Tick batching approaches session boundary.
- [X] Tick batching approaches gap boundary.
- [X] Tick batching approaches swap rollover.
- [X] Tick batching approaches scheduled strategy callback.
- [X] Tick batching approaches compliance boundary.
- [X] Tick execution tests for canonical bid/ask tick order, signal timing, previous-closed-bar behavior, and no vectorized official fills.
- [X] Synthetic tick determinism tests for per-bar seed derivation under sequential, chunked, out-of-order, and checkpoint-resumed processing.
- [X] Config tests shall cover invalid dates, invalid tick model, invalid spread model, invalid liquidity model, invalid fee/swap config, and missing symbol.
- [X] Signal-timing tests shall cover previous-close-only behavior, shifted signals, no current-bar leakage, and first tick of new bar activation.
- [X] Tick-factory tests shall cover timeframe ticks, M1 ticks, real ticks, synthetic ticks, sequence order, and bar-open flags.
- [X] Synthetic-tick tests shall cover volume 1, volume 2, volume 3, volume greater than 3, support points, determinism, bounds, and MQL5-style behavior.
- [X] Synthetic-tick tests shall verify that per-bar seed derivation produces identical ticks for full sequential runs, chunked runs, out-of-order bar processing, and checkpoint-resumed runs.
- [X] Synthetic-tick tests shall verify that different symbols and different bar-open timestamps produce independent deterministic synthetic tick streams.
- [X] Event-priority tests shall cover same-tick SL/TP conflict, stopout priority, expiration before trigger, and deterministic ordering.
- [X] Performance tests shall cover tick generation benchmark, tick loop benchmark, memory benchmark, and optimization benchmark.
- [X] Tick-batching tests shall verify batching stops before active stop loss, active take profit, pending-order trigger, order expiration, stopout threshold, bar-open signal boundary, scheduled strategy callback, market session boundary, gap boundary, swap rollover boundary, and compliance boundary.
- [X] Tick-batching tests shall verify batching does not use future bar high, low, close, or volume to prove safety.
- [X] Regulatory-constraint tests shall cover SEC Rule 201 alternative uptick-rule restrictions when required data is available.
- [X] Rounding tests shall cover tick-size price normalization, adverse rounding, currency cashflow rounding, FX conversion rounding, point precision, and fractional volume steps.
- [X] Data-lineage tests shall verify lineage from deal and PnL events back to generated ticks, support points, M1 bars, normalized rows, raw vendor files, source manifests, and checksums where applicable.
- [X] Borrow-fee tests shall verify equity and ETF short borrow fees accrue daily and tick-by-tick when configured, remain distinct from swap and dividends, convert to account base currency, and appear in reports.
- [X] Synthetic tick tests shall pass.
- [X] Per-bar synthetic tick seed tests shall pass.
- [X] Tick-batching boundary proof tests shall pass when tick batching is enabled.
- [X] Official fills are produced only by the canonical tick loop.

#### `app/services/simulator/models/spread.py`

Functions/classes:

- `NATIVE_SPREAD`
- `FIXED_SPREAD`
- `VARIABLE_SPREAD`

Requirements:

- [X] The system shall support `NATIVE_SPREAD`.
- [X] The system shall support `FIXED_SPREAD`.
- [X] The system shall support `VARIABLE_SPREAD`.
- [X] The system shall validate that spreads are non-negative.
- [X] The system shall reject or explicitly repair missing spread data according to configuration.
- [X] The system shall generate variable spreads deterministically using configured min/max spread and random seed.
- [X] The system shall support spread-relative slippage.
- [X] The system shall apply slippage after spread and before final fill-price acceptance.
- [X] The system shall include spread, slippage, commission, fees, swap, borrow fees, dividends, funding, and configured cashflows in net PnL.
- [X] The system shall detect negative spreads.
- [X] The journal shall record spread model. *app/services/simulator/engine.py:172*
- [X] The system shall support calendar-spread rollover.
- [X] Simulator models shall include execution models, slippage models, liquidity models, spread models, sizing models, risk models, calibration models, strategy models, benchmark models, and data-adjustment models.
- [X] Production promotion shall require performance to remain acceptable under increased spread, increased slippage, reduced liquidity, delayed execution, missing-data, and gap-stress scenarios.
- [X] Slippage, spread, market-impact, and liquidity models shall declare calibration data sources.
- [X] The same configuration, data, and seed shall produce the same spread values. *tests/unit/app/services/simulator/test_08a_foundation.py:78*
- [X] `SIM_UNSUPPORTED_SPREAD_MODEL`
- [X] `SIM_DATA_NEGATIVE_SPREAD`
- [X] `SIM_SPREAD_MISSING`
- [X] Spread data when native spread mode is used.
- [X] Every report shall disclose spread model.
- [X] No file-specific non-functional requirements defined.
- [X] Unsupported spread model.
- [X] Negative spread.
- [X] Missing spread.
- [X] Broker profile fixture tests for approved FX symbol metadata, precision, volume constraints, spread, swap, margin, sessions, and hash stability.
- [X] Spread, slippage, commission, swap, margin, and accounting golden tests for the approved FX fixture set.
- [X] Data-quality tests shall cover missing columns, invalid OHLC, duplicate timestamps, non-monotonic time, negative spreads, price outliers, and missing bars.
- [X] Spread tests shall cover native, fixed, variable, missing spread, negative spread, and deterministic random spread.
- [X] Slippage tests shall cover fixed, spread-relative, volatility-based, volume-dependent, cap exceeded, and deterministic random slippage.
- [X] Futures-rollover tests shall cover contract expiry, roll date selection, continuous adjustment, calendar-spread roll, roll PnL attribution, and missing contract-chain failure.
- [X] Severe missing bars, duplicate timestamps, negative spreads, invalid OHLC bars, or lookahead-sensitive feature data block production runs.

#### `app/services/simulator/models/slippage.py`

Functions/classes:

- `ExecutionRealismConfig`

Requirements:

- [X] The system shall provide an `ExecutionRealismConfig` containing liquidity, slippage, latency, commission, swap, borrow-fee, market-hours, gap-handling, broker-rules, portfolio-risk, data-quality, corporate-action, futures-rollover, perpetual-funding, and currency-conversion configuration.
- [X] The system shall prevent production-realistic labelling when infinite liquidity, no slippage, no commission, no swap, or disabled portfolio checks are used without appropriate disclosure.
- [X] The system shall support fixed-slippage liquidity mode.
- [X] The system shall produce diagnostics for requested volume, filled volume, unfilled volume, VWAP, slippage points, and market impact.
- [X] When volume-dependent liquidity and slippage models are both active, liquidity constraints shall be evaluated before slippage.
- [X] Partial-fill diagnostics shall separately record requested volume, filled volume, unfilled volume, liquidity impact, slippage impact, and cancelled or pending remainder.
- [X] Execution-quality metrics shall distinguish liquidity shortfall from slippage cost.
- [X] The system shall support no slippage.
- [X] The system shall support fixed-point slippage.
- [X] The system shall support volatility-based slippage.
- [X] The system shall support volume-dependent slippage.
- [X] The system shall support queue-position slippage.
- [X] The system shall apply slippage directionally so that it worsens execution price according to order direction.
- [X] The system shall cap slippage when a maximum slippage is configured.
- [X] The system shall use deterministic seeded randomness when randomized slippage is enabled.
- [X] The system shall journal expected price, executable bid/ask, slippage points, and final fill price.
- [X] Slippage shall apply only to actually filled volume after liquidity constraints determine fillable quantity. *app/services/simulator/models/slippage.py:56*
- [X] Slippage shall not be charged, journaled as cost, or attributed to an unfilled remainder. *app/services/simulator/models/slippage.py:56*
- [X] The system shall support gap handling by fill with slippage.
- [X] Before Phase 1 Builder handoff, gap configuration shall explicitly define `gap_policy`, `ambiguous_sl_tp_policy`, `fill_price_source`, `gap_slippage_model`, `max_gap_fill_slippage_points`, and `session_calendar_ref`.
- [X] The system shall validate slippage and deviation rules.
- [X] The system shall apply liquidity and slippage results.
- [X] The journal shall record slippage model. *app/services/simulator/engine.py:172*
- [X] The system shall produce liquidity and slippage diagnostics.
- [X] FX `production_realistic` V1 shall explicitly exclude broker last-look behavior, broker bias, asymmetric slippage manipulation, news-event volatility-surface expansion, counterparty default risk, and broker solvency modelling.
- [X] Roll events shall be journaled with old contract, new contract, roll price, adjustment amount, realized roll PnL where applicable, and slippage/fees when simulated.
- [X] Dynamic materiality reassessment shall be able to upgrade slippage, liquidity, sizing, risk, benchmark, and data-adjustment models to a stricter validation tier for a specific run.
- [X] Execution-model validation shall compare expected fill price, realized fill price, slippage distribution, rejection rate, partial-fill rate, and latency assumptions.
- [X] Capacity reports shall include turnover, average participation rate, maximum participation rate, liquidity utilization, slippage sensitivity, and market-impact sensitivity.
- [X] The same configuration, data, and seed shall produce the same slippage values.
- [X] Every trade path shall be journaled from validation through sizing, liquidity, slippage, fills, fees, swap, accounting, and compliance checks.
- [X] `SIM_UNSUPPORTED_SLIPPAGE_MODEL`
- [X] `SIM_SLIPPAGE_EXCEEDED`
- [X] Execution-realism configuration for liquidity, slippage, latency, commission, pass-through fees, swap, borrow fees, recall risk, market hours, market halts, gap handling, broker rules, portfolio risk, kill switches, data quality, corporate actions, futures rollover, perpetual funding, currency conversion, benchmark, and regulatory checks.
- [X] Slippage diagnostics.
- [X] Every report shall disclose slippage model.
- [X] No file-specific non-functional requirements defined.
- [X] Unsupported slippage model.
- [X] Slippage cap exceeded.
- [X] Gap-handling tests for rejection, fill-at-open, fill-with-slippage, and ambiguous SL/TP conservative outcome.
- [X] Liquidity and slippage tests shall verify that liquidity constraints are evaluated before slippage and that slippage applies only to actually filled volume.
- [X] Execution-quality tests shall verify that liquidity shortfall is distinguished from slippage cost.

#### `app/services/simulator/models/liquidity.py`

Functions/classes:

- `Request`
- `Response`
- `Result`
- `Config`

Requirements:

- [X] The system shall support infinite liquidity for MT5-parity or early research use only.
- [X] The system shall support volume-dependent liquidity mode.
- [X] The system shall support order-book liquidity mode where depth data is available.
- [X] The system shall walk order-book levels and calculate VWAP execution price when using order-book liquidity.
- [X] The system shall not guarantee a limit-order fill merely because price touches the limit unless touch-fill is enabled and liquidity is available.
- [X] The system shall validate liquidity-model compatibility.
- [X] The journal shall record liquidity model.
- [X] The system shall calculate liquidity metrics.
- [X] Model materiality shall be reassessed dynamically per run based on configured exposure, capital, instrument universe, strategy criticality, liquidity usage, and report distribution mode.
- [X] Reports shall include capacity diagnostics when liquidity or market-impact models are enabled.
- [X] The same configuration, data, and seed shall produce the same liquidity decisions.
- [X] `SIM_UNSUPPORTED_LIQUIDITY_MODEL`
- [X] `SIM_LIQUIDITY_UNAVAILABLE`
- [X] Liquidity diagnostics.
- [X] Every report shall disclose liquidity model.
- [X] Reports shall disclose capacity diagnostics and approved capacity limits when liquidity or market-impact models are enabled.
- [X] No file-specific non-functional requirements defined.
- [X] Unsupported liquidity model.
- [X] Insufficient liquidity.
- [X] Liquidity tests shall cover infinite liquidity, volume-dependent liquidity, order-book walking, insufficient liquidity, partial fills, and market impact.
- [X] Dynamic-materiality tests shall cover run-level materiality upgrades from exposure, capital, liquidity usage, instrument universe, and external distribution mode.
- [X] Short-recall tests shall cover deterministic recall events, seeded probabilistic recall, forced buy-ins, market-halt interaction, liquidity, fees, and journal attribution.
- [X] Liquidity and partial-fill tests shall pass.

#### `app/services/simulator/models/fee.py`

Functions/classes:

- `Request`
- `Response`
- `Result`
- `Config`

Requirements:

- [X] The system shall support no commission.
- [X] The system shall support per-lot commission.
- [X] The system shall support per-trade commission.
- [X] The system shall support percent-notional commission.
- [X] The system shall support tiered commission.
- [X] The system shall support maker/taker commission.
- [X] The system shall support pass-through regulatory, exchange, clearing, transaction, activity, and rebate fee models when configured.
- [X] US equity and ETF fee models may include SEC Section 31 fees, FINRA TAF, exchange-specific maker/taker fees or rebates, and payment-for-order-flow disclosure where relevant.
- [X] The system shall apply minimum and maximum commission limits when configured.
- [X] The system shall calculate commission per actual fill, not only per requested order.
- [X] The system shall support commission currency conversion when account currency differs.
- [X] The system shall report gross PnL, total costs, and net PnL.
- [X] Broker profiles shall capture symbol rules, sessions, swap rules, margin rules, fee rules, fill policies, precision, and supported order types.
- [X] The system shall record queryable data lineage for every data point used in fill-price, mark-to-market, margin, fee, swap, funding, dividend, benchmark, and PnL calculations.
- [X] Position records shall include time, id, magic, symbol, side or type, volume, open price, current price, stop loss, take profit, commission, margin required, fee, swap, profit, and comment.
- [X] Trade-info snapshots shall include time, id, magic, symbol, side or type, volume, price, stop loss, take profit, commission, fee, swap, profit, comment, and margin required.
- [X] The system shall apply borrow-fee events for equity and ETF short positions when configured.
- [X] The system shall change balance only from closed realized PnL, commission, fee, swap, borrow-fee, dividend, funding, and configured cashflow events.
- [X] The journal shall record fee and commission model.
- [X] The system shall produce commission, fee, and swap summaries.
- [X] Splits shall adjust open position volume and average price without changing economic value before fees or taxes.
- [X] The system shall support configurable hard-to-borrow borrow fee rates for equity and ETF short positions.
- [X] Borrow fees shall be distinct from standard swap, dividends, commission, and trade PnL.
- [X] Borrow-fee cashflows shall be journaled separately from dividends, swap, commission, and trade PnL.
- [X] Borrow-fee cashflows shall convert to account base currency when the borrow-fee currency differs from account currency.
- [X] Reports shall disclose total borrow fees paid and the borrow-fee model status.
- [X] Production-realistic equity or ETF short backtests shall require borrow-fee treatment or shall disclose a realism downgrade or approximation.
- [X] The system shall support instruments whose profit currency, margin currency, commission currency, dividend currency, borrow-fee currency, funding currency, and account base currency differ.
- [X] Internal simulator math shall use `Decimal` or equivalent fixed-precision decimal arithmetic for prices, points, fees, FX conversions, margins, cashflows, and account balances.
- [X] Commission, fees, swap, dividends, funding, realized PnL, and cash ledger entries shall round at each cashflow boundary to the relevant currency precision using the broker profile rule or `ROUND_HALF_UP` when no broker-specific rule exists.
- [X] Perpetual swaps require funding-rate treatment, funding timestamps, funding currency, and exchange-fee model for production-realistic classification.
- [X] Balance may change only from closed realized PnL, commission, fee, swap, borrow-fee, dividend, funding, and configured cashflow events.
- [X] Equity and ETF short production-realistic runs shall include borrow-fee treatment or disclose downgrade or approximation.
- [X] Equity and ETF borrow-fee configuration for short-selling runs.
- [X] Commission, fee, swap, and borrow-fee summary.
- [X] Borrow-fee totals and borrow-fee cashflow history for equity and ETF short runs.
- [X] Reports shall disclose total borrow fees paid for equity and ETF short runs.
- [X] Reports shall disclose pass-through regulatory and exchange fees separately from broker commission when configured.
- [X] External reports shall disclose major assumptions, limitations, model simplifications, data limitations, fees and costs treatment, optimization status, and whether live trading evidence exists.
- [X] The journal shall document borrow-fee accruals separately from dividends, swap, commission, and trade PnL.
- [X] The journal shall document delisting outcomes, recall events, forced buy-ins, pass-through regulatory fees, exchange fees, SEC Rule 201 checks, and wash-sale diagnostics when applicable.
- [X] Documentation shall describe equity and ETF short borrow-fee behavior.
- [X] Documentation shall include pass-through regulatory and exchange fee models, including US equity examples for SEC Section 31 and FINRA TAF where supported.
- [X] Documentation shall include delisting, survivorship-bias, recall-risk, forced-buy-in, borrow-fee, SEC Rule 201, and optional wash-sale diagnostic behavior.
- [X] No file-specific non-functional requirements defined.
- [X] Equity short position spans a borrow-fee accrual boundary.
- [X] Borrow-fee data is missing for hard-to-borrow equity.
- [X] Borrow-fee currency differs from account currency.
- [X] Fee and commission tests shall cover per-lot, per-trade, percent-notional, tiered, maker/taker, min/max commission, and currency conversion.
- [X] Pass-through fee tests shall cover regulatory, exchange, clearing, transaction, activity, rebate, SEC Section 31, FINRA TAF, and maker/taker fee attribution where configured.
- [X] Multi-currency-accounting tests shall cover realized PnL conversion, floating PnL conversion, margin conversion, fee/swap/dividend/funding conversion, and stale FX-rate rejection.
- [X] Borrow-fee tests shall pass before equity or ETF short-selling runs are production-promoted.

#### `app/services/simulator/models/swap.py`

Functions/classes:

- `Request`
- `Response`
- `Result`
- `Config`

Requirements:

- [X] The system shall support swap types in points, money, percent, and interest.
- [X] The system shall apply swap only to positions open across the configured rollover boundary.
- [X] The system shall support configurable triple-swap day per symbol.
- [X] The system shall journal swap charges and credits.
- [X] The system shall reflect swap in account balance and equity.
- [X] The system shall label overnight backtests with disabled swap as cost-incomplete.
- [X] The system shall apply swap events.
- [X] The journal shall record swap model.
- [X] The journal shall record every swap event.
- [X] Distributed locks or compare-and-swap commits shall prevent duplicate journal sequences or duplicate checkpoint commits when workers restart mid-batch.
- [X] If no active orders or open positions exist, batching may proceed only up to the next bar open, session boundary, gap boundary, swap rollover boundary, scheduled intent activation, or strategy callback boundary.
- [X] The system shall support perpetual swap.
- [X] Equity, ETF, futures, perpetual swap, spot crypto, CFD, and index instruments shall remain `research_approximation` or explicitly downgraded until their asset-class-specific data, cost, margin, and corporate-action or lifecycle models pass production gates.
- [X] Funding cashflows shall remain distinct from swap and commission.
- [X] Phase 1 shall exclude production-realistic labels for equity, ETF, futures, perpetual swap, spot crypto, CFD, index, option, and option-like instruments.
- [X] The same configuration, data, and seed shall produce the same commission and swap events.
- [X] MT5 parity money comparisons shall tolerate at most the larger of one account-currency cent or 0.01 percent of the compared value for realized PnL, balance, equity, margin, commission, and swap.
- [X] `SIM_UNSUPPORTED_SWAP_MODEL`
- [X] `SIM_SWAP_CALCULATION_FAILED`
- [X] Multi-currency strategies require base-currency conversion for realized PnL, floating PnL, margin, commission, swap, dividends, funding, and cash balances.
- [X] Funding summary for perpetual swap runs.
- [X] Every report shall disclose swap model.
- [X] The journal shall document poison-pill work-unit quarantine, idempotent write decisions, distributed-lock ownership, compare-and-swap commit outcomes, and optional service degradation events.
- [X] Documentation shall include poison-pill work-unit quarantine, idempotent queue semantics, distributed locks, compare-and-swap commits, and optional-service degradation behavior.
- [X] No file-specific non-functional requirements defined.
- [X] Unsupported swap model.
- [X] Swap calculation failure.
- [X] Swap tests shall cover daily rollover, triple-swap day, long/short swap, and disabled-swap disclosure.
- [X] Accounting tests shall cover equity, margin, free margin, margin level, realized/floating PnL, commission, swap, and stopout.
- [X] Broker-profile tests shall cover `mt5_demo_reference_fx_v1` metadata, symbol spec hashes, session rules, swap rules, margin rules, and fixture provenance.
- [X] Distributed-worker tests shall cover poison-pill work-unit quarantine, idempotent journal writes, distributed-lock or compare-and-swap commits, and duplicate checkpoint prevention.
- [X] Swap and gap tests shall pass.

#### `app/services/simulator/models/margin.py`

Functions/classes:

- `Request`
- `Response`
- `Result`
- `Config`

Requirements:

- [X] Official simulated orders, deals, positions, pending orders, account state, balance, equity, margin, free margin, margin level, realized PnL, floating PnL, execution timestamps, and immutable simulator journal.
- [X] The system shall update margin, exposure, commission, and risk immediately after partial fills.
- [X] The system shall enforce margin-call percentage.
- [X] The system shall maintain portfolio-level state for multi-symbol backtests.
- [X] The system shall calculate gross exposure.
- [X] The system shall calculate net exposure.
- [X] The system shall calculate currency exposure.
- [X] The system shall calculate margin contribution by symbol.
- [X] The system shall calculate concentration.
- [X] The system shall support optional VaR values.
- [X] The system shall validate portfolio risk after sizing and before matching.
- [X] The system shall support independent-symbol margin.
- [X] The system shall support netted FX margin.
- [X] The system shall support cross-margin.
- [X] The system shall support SPAN-like margin mode.
- [X] The system shall enforce correlation limits when enabled.
- [X] The system shall enforce concentration limits when enabled.
- [X] The system shall enforce gross, symbol, and cluster exposure limits when enabled.
- [X] The system shall evaluate pair, basket, grid, and martingale strategies at portfolio level.
- [X] The system shall support portfolio-level kill switches that halt new trading when configured drawdown, loss, exposure, margin, volatility, or error thresholds are breached.
- [X] Kill-switch events shall liquidate, block new orders, cancel pending orders, or enter monitor-only mode according to configuration.
- [X] Kill-switch decisions shall be journaled with threshold, observed value, action, and actor or policy id.
- [X] The system shall validate margin availability.
- [X] The system shall enforce `FreeMargin = Equity - Margin`.
- [X] The system shall enforce `MarginLevel = Equity / Margin * 100` when margin is greater than zero.
- [X] The journal shall record every margin event.
- [X] The simulator module shall enforce that strategies cannot mutate official account, order, deal, position, margin, equity, journal, or execution timestamp state.
- [X] The system shall produce equity, balance, margin, and exposure curves.
- [X] Options and option-like contracts shall remain out of scope beyond reserved enum or metadata mentions until an options-specific requirements document defines contract specs, Greeks, exercise/assignment, expiry, corporate actions, margin, pricing, and settlement.
- [X] Strategies shall not directly mutate official account, order, deal, position, margin, equity, or journal state.
- [X] `SIM_INSUFFICIENT_MARGIN`
- [X] Futures require contract metadata, expiry, rollover policy, margin model, and roll-adjustment disclosure for production-realistic classification.
- [X] Margin curve.
- [X] Every report shall disclose margin model.
- [X] No file-specific non-functional requirements defined.
- [X] Insufficient margin.
- [X] Position-sizing tests shall cover all sizing modes, invalid inputs, volume normalization, and margin failure.
- [X] Portfolio-risk tests shall cover exposure, concentration, correlation, portfolio margin, and multi-symbol margin aggregation.
- [X] Kill-switch tests shall cover drawdown, loss, exposure, margin, volatility, and error-triggered trading halt behavior.
- [X] Validation tests shall cover volume, stops, freeze, price, margin, portfolio, max positions/orders, and unsupported fill policy.

#### `app/services/simulator/validation/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/simulator/validation/quality.py`

Functions/classes:

- `MarketDataAuthorityManifest`
- `PartialDataPolicy`
- `SIM_DATA_PARTIAL`
- `SIM_DATA_STALE`
- `DataManifestHash`
- `SIM_FEATURE_LOOKAHEAD_DETECTED`

Requirements:

- [X] Simulator-specific data-quality gating, realism classification, asset-class realism disclosures, benchmark manifests, model-governance evidence, research-integrity evidence, and execution-calibration evidence.
- [X] Reports shall include IOC remainder cancellations in execution-quality diagnostics.
- [X] The system shall detect missing required columns.
- [X] The system shall detect missing bars.
- [X] The system shall detect duplicate timestamps.
- [X] The system shall detect non-monotonic timestamps.
- [X] The system shall detect zero or negative prices.
- [X] The system shall detect price outliers.
- [X] The system shall detect impossible OHLC bars.
- [X] The system shall produce a `DataQualityReport`.
- [X] The system shall block production runs when severe data-quality thresholds fail unless diagnostic mode is explicitly enabled.
- [X] The system shall include the data-quality report in the final report.
- [X] Production simulators shall consume normalized data through the data module contract and an approved `MarketDataAuthorityManifest`.
- [X] Missing or staging-only authoritative data shall block a production-realistic label unless the affected model is proven unnecessary for the selected instruments.
- [X] The system shall define a `PartialDataPolicy` for incomplete provider files or partial symbol-day data.
- [X] `PartialDataPolicy` shall support quarantining the affected symbol and date with `SIM_DATA_PARTIAL`, using stale prior data with `SIM_DATA_STALE` and a configurable staleness limit, or failing the entire run.
- [X] Stale-data recovery shall be unavailable for production-realistic classification unless explicitly approved and disclosed.
- [X] Data lineage shall be queryable for audit, replay, model validation, and production-promotion evidence.
- [X] The market-data authority client shall support a warm cache for frequently read immutable or rarely changed datasets.
- [X] Warm data cache keys shall include `DataManifestHash`, provider id, dataset id, symbol, timeframe, date range, adjustment mode, and schema version.
- [X] Cache hits shall skip network transfer only after validating the cached artifact checksum against the authoritative manifest.
- [X] Cache entries shall expire according to a configured TTL and shall never override point-in-time data snapshot requirements.
- [X] The simulator shall support optional feature-store integration for machine-learning features.
- [X] Feature-store integration shall default to disabled in Phase 1. If enabled in a later approved phase, it MUST enforce point-in-time correctness, feature availability timestamps, publication lag, ingestion lag, and deterministic `SIM_FEATURE_LOOKAHEAD_DETECTED` rejection before any feature can influence a decision.
- [X] Feature-store retrieval shall enforce point-in-time correctness at the canonical decision timestamp, including sub-second or microsecond availability timestamps where provided.
- [X] Feature-store retrieval shall reject or mask any feature whose computation or publication time is later than the strategy decision time.
- [X] Alternative data inputs such as sentiment, fundamentals, news, options flow, and external signals shall include event time, ingestion time, publication time, source id, and availability timestamp.
- [X] The journal shall record data-quality report.
- [X] The system shall produce data-quality summary.
- [X] The system shall calculate data-quality metrics.
- [X] The system shall calculate MT5-style history quality.
- [X] Production-realistic reports shall attach confidence intervals to every material performance, risk, drawdown, cost, and execution-quality metric when Monte Carlo or bootstrap evidence is available.
- [X] The system shall calculate execution-quality metrics.
- [X] Optimization shall reject parameter sets that fail data-quality checks.
- [X] Equity and ETF runs shall include a corporate-action quality report.
- [X] Severe data-quality failures shall block production runs unless diagnostic mode is configured.
- [X] Diagnostic mode shall never produce a `production_realistic` or `mt5_parity_oriented` classification after severe data-quality failure or accounting invariant violation.
- [X] Public simulator modules shall expose only approved AI Tool wrappers and stable protocol types; internal execution, accounting, journal, data-quality, and reporting services shall remain non-agent-callable and shall be protected by import-boundary tests.
- [X] Required data-quality gates shall run before calculations and execution.
- [X] History-quality metadata shall be exposed.
- [X] The simulator shall emit business-level time-series metrics suitable for dashboards, including run status counts, lookahead violation counts, execution latency, data-quality failure counts, persistence failure counts, queue depth, and quota rejection counts.
- [X] Severe data-quality failure shall block production runs unless diagnostic mode is explicitly enabled.
- [X] `SIM_DATA_QUALITY_FAILED`
- [X] Data-quality report.
- [X] Corporate-action quality report for equity/ETF runs.
- [X] Every report shall disclose data-quality status.
- [X] No file-specific non-functional requirements defined.
- [X] Report tests for canonical JSON report, required Markdown report, realism disclosure, data-quality summary, cost summary, and artifact manifest.
- [X] Usage examples shall include canonical FX backtest, severe data-quality blocked run, optimization with streaming journal persistence, and raw Python strategy-code rejection.
- [X] IOC remainder tests shall verify partial-fill remainder cancellation journals `SIM_IOC_REMAINDER_CANCELLED`, does not fail a valid partial-fill simulator, and appears in execution-quality diagnostics.
- [X] Data-quality tests shall pass.
- [X] Severe data-quality blocked run that returns `diagnostic_failed` and does not claim `production_realistic` or `mt5_parity_oriented`.
- [X] The tool validates config, data quality, strategy registry, broker profile, and market-data authority requirements.
- [X] The response returns a deterministic `SIM_*` error code, bounded diagnostics, and any safe partial artifacts.
- [X] The run is not labelled `production_realistic` or `mt5_parity_oriented` after severe data-quality failure.

#### `app/services/simulator/validation/schema.py`

Functions/classes:

- `SimulatorResult`
- `run_backtest`

Requirements:

- [X] Before Builder handoff, each public simulator capability shall define name, purpose, caller type, stability level, official/internal status, request schema, response schema, deterministic error codes, side effects, required permissions, artifact behavior, network behavior, persistence behavior, compatibility guarantees, and at least one success and one deterministic-error example.
- [X] `SimulatorResult`, official tool envelopes, artifact manifests, journal events, report JSON, broker profiles, and market-data authority manifests shall have schema references before Builder handoff.
- [X] `SimulatorToolEnvelopeV1` fields: `schema_version`, `request_id`, `status`, `result`, `error`, `warnings`, `metadata`, and `artifacts`.
- [X] Every journal event shall include schema version, run id, monotonic sequence number, event timestamp, event type, payload, previous event hash, and event hash.
- [X] The simulator module shall consume indicator result manifests containing input checksum, parameter hash, implementation version, output schema version, and timing metadata.
- [X] Visual replay exports shall use a documented JSON schema suitable for charting libraries without becoming the canonical report artifact.
- [X] Report schema validation shall run before a report is marked complete.
- [X] Official AI Tools shall use a standard return schema.
- [X] Official AI Tool responses shall use an envelope containing `schema_version`, `request_id`, `status`, `result`, `error`, `warnings`, `metadata`, and `artifacts`.
- [X] Official response schemas shall be versioned and backward-compatible within a major schema version.
- [X] The `run_backtest` AI Tool shall accept only registered strategy identifiers, validated strategy configuration schemas, or code explicitly vetted and sandboxed by the orchestration layer.
- [X] Determinism guarantees shall be evaluated under the same pinned `requirements.txt` or lockfile, same approved dependency versions, same simulator schema version, and same Python minor version unless a cross-version reproducibility profile is explicitly certified.
- [X] Public response schemas shall remain backward-compatible within a major schema version, and breaking changes shall require a new major schema version.
- [X] Alerting shall cover journal persistence failures, schema validation failures, repeated accounting invariant failures, abnormal rejection spikes, data-provider failures, and performance regressions.
- [X] Official AI Tool exports shall use a standard return schema.
- [X] The `run_backtest` AI Tool shall require registered strategy identifiers or validated strategy configuration schemas.
- [X] The strategy registry shall be an explicit allowlist of approved strategy ids, module paths, version hashes, configuration schemas, and permitted execution modes.
- [X] Any Phase 1 code or schema introduced to accommodate future scope shall be inert by default, guarded by an explicit feature flag or scope tag, and fully tested for deterministic unsupported-scope rejection.
- [X] Strategy execution shall occur only through registered strategies, validated schemas, or explicitly sandboxed and vetted orchestration paths.
- [X] Artifact manifest containing paths, media types, schema versions, hashes, sizes, retention tier, and created timestamps.
- [X] Documentation shall include a schema reference for `SimulatorResult`, official AI Tool envelopes, journal events, report JSON, artifact manifests, broker profiles, and market-data authority manifests.
- [X] Documentation shall include execution-model calibration requirements and calibration artifact schemas.
- [X] Documentation shall include end-to-end data-lineage graph schema and audit query examples.
- [X] Documentation shall include deterministic step-through replay and visual trade replay export schema.
- [X] Documentation shall include the schema and approval workflow for `simulator_promotion_manifest.json`.
- [X] No file-specific non-functional requirements defined.
- [X] Contract tests shall verify `run_backtest` success envelopes include `schema_version`, `request_id`, `status`, `result`, `error`, `warnings`, `metadata`, and `artifacts`.
- [X] Contract tests shall verify public schema backward compatibility within a major schema version.
- [X] Schema tests shall cover `SimulatorResult`, official AI Tool response envelopes, report JSON, report Markdown metadata, artifact manifests, and backward-compatible schema versioning.
- [X] Visual-replay-export tests shall cover schema validation, signals, fills, order events, equity overlays, drawdown overlays, halt annotations, and derivation from canonical journal artifacts.
- [X] AI Tool strategy security tests shall verify registered strategy identifiers succeed when schemas are valid, unregistered strategy identifiers are rejected, unapproved modules are rejected, and invalid strategy configuration schemas are rejected.
- [X] No official tool shall be exported without metadata/schema tests.
- [X] Response schema and artifact manifest tests shall pass.
- [X] MT5 parity shall fail when a difference is explained only by an undocumented broker rule, missing symbol metadata, or non-deterministic rounding.
- [X] Official AI Tool exports shall validate inputs.
- [X] Every invalid configuration shall return a deterministic error code.
- [X] Every invalid data condition shall return a deterministic error code.
- [X] Stale FX conversion rates shall fail or be explicitly recorded according to configuration.
- [X] The system shall return `SIM_FX_RATE_STALE` when a required FX conversion rate exceeds configured maximum age.
- [X] The system shall return `SIM_PROMOTION_EVIDENCE_MISSING` when a production promotion manifest lacks required evidence.
- [X] `SIM_INVALID_CONFIG`
- [X] `SIM_INVALID_DATE_RANGE`
- [X] `SIM_MISSING_SYMBOL`
- [X] `SIM_DATA_MISSING_COLUMN`
- [X] `SIM_DATA_INVALID_OHLC`
- [X] `SIM_INVALID_VOLUME`
- [X] `SIM_INVALID_STOPS_LEVEL`
- [X] `SIM_INVALID_PRICE`
- [X] `SIM_SIZING_INVALID_ATR`
- [X] `SIM_SIZING_INVALID_KELLY_INPUTS`
- [X] `SIM_FX_RATE_STALE`
- [X] `SIM_DATA_STALE`
- [X] `SIM_RESEARCH_PROTOCOL_MISSING`
- [X] `SIM_PROMOTION_EVIDENCE_MISSING`
- [X] `market_data_authority_ref` shall reference an approved `MarketDataAuthorityManifest`; inline raw provider credentials are invalid.
- [X] `broker_profile_ref` shall reference an approved broker profile manifest; inline broker credentials are invalid.
- [X] The system shall reject missing or invalid Kelly inputs.
- [X] The system shall reject missing, zero, negative, or misaligned ATR values for volatility sizing.
- [X] The system shall validate symbol availability.
- [X] The system shall validate market session availability.
- [X] The system shall validate volume minimum, maximum, and step.
- [X] The system shall validate price correctness.
- [X] The system shall validate stop-loss and take-profit direction.
- [X] The system shall validate stops level.
- [X] The system shall validate freeze level.
- [X] The system shall validate expiration and time policy.
- [X] The system shall fail fast or explicitly record an approximation when required asset-class data is missing.
- [X] FX conversion precedence shall be direct pair first, inverse pair second when inverse conversion is enabled, and cross-rate synthesis third when cross-rate synthesis is enabled and all legs pass skew/staleness validation.
- [X] Phase 1 shall document the exact fallback-chain setting and default before implementation; the default shall fail closed when no approved non-stale direct or enabled inverse rate is available unless the owner approves cross-rate synthesis for the active fixture.
- [X] Stale FX rates shall fail or be explicitly recorded according to configuration.
- [X] `stale_rate_tolerance_seconds` may be accepted only as a backward-compatible alias for `max_fx_rate_age_seconds`.
- [X] If a required conversion rate exceeds the configured maximum age, conversion shall fail closed with `SIM_FX_RATE_STALE` unless diagnostic mode explicitly overrides it.
- [X] Cross-rate synthesis shall reject mathematically invalid conversion paths.
- [X] Stale, duplicated, or conflicting run ids shall fail with deterministic error codes.
- [X] Promotion shall fail when any required evidence artifact is missing, expired, unverifiable, or hash-mismatched.
- [X] Invalid date range.
- [X] Missing symbol.
- [X] Missing required data columns.
- [X] Invalid OHLC bars.
- [X] Missing bars beyond threshold.
- [X] Invalid volume.
- [X] Invalid stop-loss or take-profit direction.
- [X] Invalid ATR sizing input.
- [X] Invalid Kelly sizing input.
- [X] Missing corporate-action data when required.
- [X] Missing futures contract chain when required.
- [X] Missing perpetual funding rate when required.
- [X] Missing, stale, or unusable FX conversion rate.
- [X] FX rate is present but stale.
- [X] FX stale-rate diagnostic override is enabled.
- [X] FX cross-rate synthesis produces a skewed or invalid conversion rate.
- [X] Invalid enum casing.
- [X] Broker-profile timezone rules are missing for a local session calendar.
- [X] FX conversion tests for direct, inverse, stale, and rejected cross-rate paths according to approved Phase 1 settings.
- [X] Contract tests shall verify unknown fields, malformed payloads, invalid enum casing, missing required fields, timezone-naive dates, oversized payloads, and path traversal attempts.
- [X] Partial-data tests shall cover symbol-day quarantine, stale-data fallback, stale-data age limits, whole-run failure, and production-realism downgrade behavior.
- [X] Research-integrity tests shall cover missing protocol manifests, post-hoc selection disclosure, out-of-sample degradation thresholds, and parameter-sensitivity evidence.
- [X] Perpetual-funding tests shall cover funding interval, long/short funding direction, funding currency conversion, and missing funding-rate behavior.
- [X] Promotion-manifest tests shall cover required evidence artifacts, expired approvals, hash mismatches, missing classification, and manifest retention.
- [X] FX staleness and cross-rate rejection tests shall pass.
- [X] `PartialDataPolicy` for incomplete provider files, partial symbol-day data, stale-data fallback, quarantine behavior, and fail-fast behavior.
- [X] `max_fx_rate_age_seconds` or equivalent context-specific FX stale-rate tolerance configuration.
- [X] FX stale-rate override disclosures.

#### `app/services/simulator/journal.py`

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
- `SimulatorResult`

Requirements:

- [X] Simulator reports, metrics, artifact manifests, replay metadata, journal persistence, run lifecycle, run idempotency, optimization/walk-forward/Monte Carlo execution evidence, and production-promotion evidence.
- [X] Produce `SimulatorResult`, immutable journal artifacts, canonical JSON reports, required Markdown reports, derived CSV/HTML/visual replay artifacts where configured, and structured error responses.
- [X] The system shall produce a report from the immutable journal and computed metrics.
- [X] When an `IOC` order remainder is cancelled, the system shall journal `SIM_IOC_REMAINDER_CANCELLED` as a non-fatal diagnostic event.
- [X] The system shall maintain an immutable trade journal.
- [X] The journal shall record config hash.
- [X] The journal shall record data checksum.
- [X] The journal shall record sizing model.
- [X] The journal shall record signal timing policy.
- [X] The journal shall record every event priority decision.
- [X] The journal shall record every order state transition.
- [X] The journal shall record every deal and partial fill.
- [X] The journal shall record every position update.
- [X] The journal shall record every account snapshot.
- [X] The journal shall record every rejection and error.
- [X] The journal shall record every compliance record.
- [X] The canonical journal storage format shall be append-only JSON Lines with one event per line.
- [X] Optional Parquet and CSV journal exports may be generated for analysis, but they shall be derived artifacts and not the canonical replay source.
- [X] Artifact integrity checks shall fail when journal hashes, manifest checksums, or sequence continuity are invalid.
- [X] The immutable journal shall support streaming append-to-disk persistence.
- [X] Append-only journal storage shall support long optimization, walk-forward, and Monte Carlo runs without materializing every run journal in process memory.
- [X] Holding all optimization, walk-forward, or Monte Carlo journals in memory shall be forbidden for production runs.
- [X] Journal persistence failures shall fail closed with `SIM_PERSISTENCE_FAILED`.
- [X] Streaming journal writes shall preserve event ordering, replayability, config hash, data checksum, parameter hash, random seed, and objective metadata for each run.
- [X] The report shall disclose the journal storage backend and durability mode used for the run.
- [X] `JournalPersistenceConfig` shall include backend selection, durability mode, flush batch size, maximum in-memory buffer size, and sidecar index configuration.
- [X] Phase 1 shall use append-only JSON Lines as the mandatory canonical streaming journal backend.
- [X] Phase 1 shall use a SQLite sidecar index as the initial random-access journal query format for report generation and diagnostics.
- [X] Phase 1 journal durability shall default to fsync per batch, with a maximum batch of 1,000 events, five seconds, or 16 MB before flush, whichever occurs first.
- [X] Production journal persistence shall fsync before marking a run complete or before emitting final reports.
- [X] If a journal write, flush, fsync, sidecar transaction, or commit fails, the run shall stop in production mode and return `SIM_PERSISTENCE_FAILED`.
- [X] After persistence failure, diagnostics shall include journal backend, run id, failed operation, and last committed sequence number.
- [X] The simulator module shall journal strategy id, strategy version, configuration hash, rationale where provided, and strategy-input rejection diagnostics.
- [X] The simulator module shall prevent vectorized indicator or signal generation from producing official fills, account state, trade journals, or reports.
- [X] Visual trade replay export shall be supported as a derived artifact from the canonical journal and report JSON.
- [X] If JSON and human-readable report artifacts disagree, the run shall fail report validation until the derived artifact is regenerated from canonical JSON and journal data.
- [X] Requeued work units shall preserve deterministic provenance hashes and shall not duplicate completed journal or report artifacts.
- [X] Task queues and worker leases shall provide exactly-once effects or idempotent execution for journal writes, checkpoint commits, sidecar index updates, and artifact publication.
- [X] The system shall support Monte Carlo analysis after a canonical journal exists.
- [X] The system shall support bootstrap robustness analysis from the immutable journal.
- [X] The system shall include asset-class realism decisions in the immutable journal and final report header.
- [X] Split adjustment events shall be journaled with before/after volume, price, SL, TP, and pending-order state.
- [X] Recall and forced-buy-in events shall be journaled separately from strategy-initiated exits.
- [X] If a higher-precedence rate exists but is stale, invalid, or checksum-mismatched, the fallback chain shall follow explicit configuration: either fail closed immediately or continue to the next enabled source with a journaled diagnostic.
- [X] Every conversion shall be journaled with rate, source, timestamp, and age.
- [X] FX stale-rate diagnostic overrides shall be journaled and disclosed in the report.
- [X] Rejected cross-rate paths shall return or journal `SIM_FX_CROSS_RATE_REJECTED`.
- [X] Rejected cross-rate paths shall be journaled with failed currency graph, requested conversion pair, candidate path, computed rate, reference rate when available, skew, and rejection reason.
- [X] Regulatory checks shall be fully journaled when enabled.
- [X] The `run_backtest` AI Tool shall journal rejected strategy-injection attempts without logging unsafe code bodies in full.
- [X] Capacity assumptions shall be journaled and included in the realism disclosure.
- [X] A cancelled run shall produce a structured cancelled result, partial artifact manifest, final journal flush attempt, and cancellation diagnostic.
- [X] Run lifecycle transitions shall be journaled with actor, request id, timestamp, previous state, next state, and transition reason.
- [X] The same configuration, data, and seed shall produce the same journal.
- [X] Every shortcut shall be recorded in configuration, journal, and final report.
- [X] Production service mode shall expose health checks for data access, artifact storage, journal backend, sidecar index, secrets provider, and worker capacity.
- [X] Production service mode shall define SLOs for run startup latency, successful completion rate, journal durability, artifact availability, and report-generation latency.
- [X] Operational runbooks shall cover failed runs, corrupted sidecar index, journal replay recovery, data-source outage, artifact restore, stuck worker, and rollback after bad release.
- [X] The immutable journal shall preserve audit evidence.
- [X] `simulator.viewer` may read authorized reports and metadata but shall not launch runs or read protected journals.
- [X] Logs, reports, and journals may include run id, request id, actor id or pseudonymous actor id, strategy id, strategy version, symbol, timeframe, non-secret configuration, checksums, aggregate metrics, diagnostics, and artifact references.
- [X] Logs, reports, and journals shall not include API keys, tokens, passwords, private keys, full broker credentials, raw personal identifiers, payment data, unrestricted account identifiers, proprietary strategy source code, or raw proprietary market data payloads unless an explicit protected-artifact policy allows it.
- [X] Production-candidate and validation journals, reports, and benchmark metadata shall default to a seven-year retention tier.
- [X] Artifact export shall include checksums for reports, journals, tables, and benchmark files.
- [X] Protected journals, artifact manifests, report bundles, and replay evidence shall define encryption-at-rest requirements before any externally accessible or production-candidate simulator surface is enabled.
- [X] The system shall return `SIM_PERSISTENCE_FAILED` when the journal cannot be written, flushed, fsynced, committed, indexed, or otherwise persisted.
- [X] The system shall journal `SIM_IOC_REMAINDER_CANCELLED` when an IOC order remainder is cancelled after a valid partial fill.
- [X] The system shall return or journal `SIM_FX_CROSS_RATE_REJECTED` when FX cross-rate synthesis is rejected due to invalid, circular, or skewed conversion paths.
- [X] The system shall return or journal `SIM_DATA_PARTIAL` when partial data is quarantined according to `PartialDataPolicy`.
- [X] The system shall return or journal `SIM_DATA_STALE` when stale data is used under an explicit stale-data policy.
- [X] The system shall journal `SIM_ENVIRONMENT_DRIFT_WARNING` when runtime environment differs from the certified benchmark profile.
- [X] The system shall return or journal `SIM_MARKET_HALT_ACTIVE` when trading is blocked or deferred by a halt or limit-up/limit-down state.
- [X] The system shall return or journal `SIM_KILL_SWITCH_TRIGGERED` when portfolio kill-switch policy blocks or alters trading.
- [X] The system shall return or journal `SIM_POISON_WORK_UNIT_QUARANTINED` when a repeated-failure work unit is quarantined.
- [X] The system shall return or journal `SIM_OPTIONAL_SERVICE_DEGRADED` when a non-production run falls back after optional cache or sidecar service failure.
- [X] Persistence-failure diagnostics shall include journal backend, run id, failed operation, and last committed sequence number.
- [X] Risk rejections must be journaled.
- [X] Streaming journal persistence shall be mandatory for optimization, walk-forward, and Monte Carlo production runs.
- [X] Production runs shall fail closed when journal persistence fails.
- [X] `IOC` remainder cancellation shall be a journaled diagnostic, not a silent side effect.
- [X] Journal persistence configuration for streaming append-to-disk storage.
- [X] Journal backend selection with Phase 1 support for canonical JSONL and SQLite sidecar index. *app/services/simulator/journal.py:199*
- [X] Immutable journal. *app/services/simulator/journal.py:68*
- [X] Journal persistence backend and durability metadata. *app/services/simulator/journal.py:199*
- [X] Persistence-failure diagnostics when journal writes, flushes, fsyncs, sidecar transactions, or commits fail.
- [X] The immutable journal shall act as the audit and replay source. *app/services/simulator/journal.py:190*
- [X] Reports shall disclose journal storage backend, durability mode, and sidecar index usage.
- [X] The journal shall document configuration hash and data checksum. *app/services/simulator/journal.py:180*
- [X] The journal shall document model choices used in the run. *app/services/simulator/engine.py:172*
- [X] The journal shall document every state transition and rejection.
- [X] The journal shall document every compliance record.
- [X] The journal shall document currency conversion rate, source, timestamp, and age for every conversion.
- [X] The journal shall document asset-class realism decisions.
- [X] The journal shall document persistence backend, durability mode, flush policy, sidecar index configuration, and last committed sequence.
- [X] The journal shall document strategy-input rejection attempts without logging unsafe code bodies in full.
- [X] The journal shall document IOC remainder cancellations as non-fatal diagnostics.
- [X] The journal shall document FX stale-rate overrides and rejected cross-rate synthesis paths.
- [X] The journal shall document model inventory ids, model validation evidence ids, governance overrides, and model exception expiry.
- [X] The journal shall document research protocol manifest id, selected-parameter lineage, and out-of-sample validation evidence.
- [X] The journal shall document execution-calibration artifact ids and calibration status for execution realism models.
- [X] The journal shall document latency model id, latency components, delayed eligibility time, and latency-affected fill decisions.
- [X] The journal shall document capacity assumptions, approved limits, and capacity-limit violations.
- [X] The journal shall document market halts, limit-up/limit-down states, kill-switch triggers, trailing-stop updates, pegged-order repricing, and cancel-replace operations.
- [X] The journal shall document feature-store retrieval timestamps, feature availability timestamps, alternative-data as-of alignment, and rejected feature lookahead events.
- [X] The journal shall document run lifecycle transitions, idempotency decisions, cancellations, and checkpoint compatibility checks.
- [X] The journal shall document vendor/source inventory ids, point-in-time snapshot ids, and material vendor-data limitations.
- [X] The journal shall document immutable run-configuration artifact id, environment diagnostic hash, and environment drift warnings.
- [X] The journal shall document resource quota checks, queue transitions, worker assignment, worker heartbeat loss, requeue decisions, retry attempts, and resume checkpoints.
- [X] The journal shall document partial-data policy decisions, quarantined symbol-date ranges, stale-data use, and stale-data age.
- [X] The journal shall document data-lineage artifact ids for fill-price, mark-to-market, and PnL events.
- [X] The journal shall document trace ids, span ids, synthetic transaction probe ids, and canary comparison ids when applicable.
- [X] Documentation shall describe streaming journal persistence requirements, supported journal storage backends, SQLite sidecar indexing, fsync-per-batch durability, and maximum in-memory journal buffer limits.
- [X] Journal persistence shall use asynchronous or otherwise non-blocking I/O boundaries so JSONL serialization, hash-chain persistence, sidecar indexing, flush, and fsync operations do not block the canonical tick-matching event loop per tick. *app/services/simulator/journal.py:154*
- [X] Journal persistence shall group durable writes by approved batch, sequence range, or transaction boundary while preserving a replay-verifiable per-event audit trail and hash-chain continuity.
- [X] Journal persistence shall enforce bounded in-memory buffers, backpressure behavior, and fail-closed handling when the writer falls behind, the sidecar transaction fails, or the durable sink cannot confirm the last committed sequence.
- [X] Documentation shall describe Phase 1 defaults for MT5 parity tolerance, JSONL journal storage, SQLite sidecar indexing, canonical JSON report format, and required Markdown report format.
- [X] Reports and journals are required artifacts, not optional diagnostics. *app/services/simulator/engine.py:197*
- [X] No file-specific non-functional requirements defined.
- [X] Optimization run produces too many journal events for memory.
- [X] Walk-forward run produces too many journal events for memory.
- [X] Monte Carlo run attempts to materialize all journals in memory.
- [X] Journal append-to-disk write fails.
- [X] Journal backend becomes unavailable mid-run.
- [X] Journal write succeeds but flush or commit fails.
- [X] Authorized actor lacks access to requested strategy id, data scope, broker profile, journal, or artifact root.
- [X] Filesystem permission is denied for journal, sidecar index, report, or artifact root.
- [X] Disk becomes full during journal append, report generation, sidecar index write, or artifact manifest write.
- [X] Canonical journal exists but the SQLite sidecar index is corrupted.
- [X] Canonical journal hash chain or sequence validation fails.
- [X] Protected journal access is denied to a viewer or unauthorized service account.
- [X] Journal persistence tests for append-only JSONL, SQLite sidecar indexing, hash-chain/sequence validation, replay, and fail-closed persistence errors. *tests/unit/app/services/simulator/test_08a_foundation.py:332*
- [X] Fault-injection tests for disk-full during journal append, disk-full during report generation, flush failure, fsync failure, SQLite sidecar transaction failure, and artifact manifest write failure.
- [X] Run-lifecycle tests shall cover idempotent retries, duplicate run ids, cancellation artifacts, checkpoint compatibility, and lifecycle transition journaling.
- [X] Reporting tests shall verify metrics are reproducible from the journal and include realism disclosure, cost diagnostics, and portfolio diagnostics.
- [X] Journal persistence tests shall cover streaming append behavior, journal replay from append-only storage, SQLite sidecar indexing, and report generation from persisted journals. *tests/unit/app/services/simulator/test_08a_foundation.py:115*
- [X] Journal persistence tests shall verify optimization, walk-forward, and Monte Carlo runs do not retain all journals in memory.
- [X] Journal persistence tests shall verify journal write, flush, fsync, sidecar transaction, and commit failures return `SIM_PERSISTENCE_FAILED`.
- [X] Journal persistence tests shall verify last committed journal sequence is recoverable after persistence failure.
- [X] Performance tests shall include memory profiles for optimization, walk-forward, and Monte Carlo runs with streaming journal persistence enabled.
- [X] Corporate-action tests shall cover dividend cashflow, split adjustment, reverse split, merger/delisting policy, adjusted/unadjusted price modes, and journal disclosure.
- [X] FX staleness tests shall verify stale rates return `SIM_FX_RATE_STALE`, diagnostic overrides require explicit configuration, and stale-rate overrides are journaled and disclosed.
- [X] FX cross-rate tests shall verify circular paths, mathematically invalid rates, and skewed rates outside configured tolerance return or journal `SIM_FX_CROSS_RATE_REJECTED`.
- [X] Chaos and fault-injection tests shall simulate disk-full, permission-denied, journal flush failure, sidecar transaction failure, artifact-store outage, and worker heartbeat loss with deterministic error envelopes and no silent artifact promotion.
- [X] Debug-replay tests shall cover pause by timestamp, journal sequence, event, bar boundary, strategy callback, and error condition with deterministic resume.
- [X] Streaming journal persistence and failure tests shall pass.
- [X] The result includes a `SimulatorResult`, journal artifact, JSON report, Markdown report, artifact manifest, metrics, and realism disclosure. *tests/unit/app/services/simulator/test_08a_foundation.py:134*
- [X] Work units are deterministic and resumable.
- [X] Journals are streamed to disk instead of held fully in memory.
- [X] Ranking is deterministic when objective scores tie.
- [X] Controlled tool boundaries MUST return a deterministic `SIM_*` error code and safe redacted error envelope for all handled failures. Custom simulator exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration. *app/services/simulator/orchestrator.py:108*
- [X] Diagnostic mode shall require an explicit configuration flag, actor id, rationale, and audit record.
- [X] `SIM_EVENT_PRIORITY_CONFLICT`
- [X] The system shall prevent or defer trading during market halts and limit-up/limit-down states according to exchange and broker policy.
- [X] The system shall apply commission events.
- [X] Dividend events shall be recorded separately from trade PnL.
- [X] The system shall support spot-at-event-time conversion.
- [X] Event-priority conflict.
- [X] Delisting tests shall cover final exchange price, OTC price, cash consideration, liquidation value, total-loss treatment, and prevention of silent symbol dropping.
- [X] Alternative-data tests shall cover irregular event times, delayed publication, ingestion timestamps, as-of alignment, lag policy, embargo policy, and no-lookahead behavior.
- [X] Event-priority tests shall pass.
- [X] Futures roll events and roll PnL attribution for futures runs.
- [X] Data-lineage graph or lineage artifact references for audited data points.

#### `app/services/simulator/report.py`

Functions/classes:

- `SimulatorReport`
- `SimulatorSummary`
- `generate_simulator_report`
- `serialize_simulator_report`

Requirements:

- [X] The module does not treat research approximation, visual mode, notebook objects, or derived exports as canonical execution or reporting artifacts.
- [X] The module does not own OS-level resource management such as process pools, thread-pool orchestration, global memory management, or platform scheduler policy beyond enforcing configured Simulator resource quotas and reporting quota diagnostics.
- [X] Support optimization, walk-forward, Monte Carlo, bootstrap, deterministic replay, step-through replay, visual replay export, benchmark reporting, production-promotion manifests, and service-mode run lifecycle operations where enabled.
- [X] The system shall disclose every enabled, disabled, or simplified realism model in the final report.
- [X] The system shall record gap-handling rules in the report.
- [X] The system shall produce a trades list.
- [X] The system shall produce orders history.
- [X] The system shall produce deals history.
- [X] The system shall produce partial-fill history.
- [X] The system shall produce position lifecycle history.
- [X] The system shall produce portfolio-risk summary.
- [X] The system shall produce realism-disclosure summary.
- [X] The system shall calculate PnL metrics.
- [X] The system shall calculate cost metrics.
- [X] The system shall calculate trade statistics.
- [X] The system shall calculate streak statistics.
- [X] The system shall calculate regression metrics.
- [X] The system shall calculate return metrics.
- [X] The system shall calculate drawdown metrics.
- [X] The system shall report bars processed.
- [X] The system shall report symbols involved.
- [X] The system shall calculate total net profit, gross profit, gross loss, profit factor, expected payoff, recovery factor, and Sharpe ratio.
- [X] The system shall calculate Z-score for win/loss sequence randomness.
- [X] The system shall calculate AHPR and GHPR when return series and trade count are sufficient.
- [X] The system shall calculate linear-regression correlation and linear-regression standard error for the equity curve.
- [X] The system shall calculate total trades, total deals, short trades and win percentage, long trades and win percentage, profit trades and percentage, and loss trades and percentage.
- [X] The system shall calculate largest profit trade, largest loss trade, average profit trade, and average loss trade.
- [X] The system shall calculate maximum consecutive wins, maximum consecutive losses, maximal consecutive profit, maximal consecutive loss, average consecutive wins, and average consecutive losses.
- [X] The system shall calculate balance drawdown absolute, equity drawdown absolute, balance drawdown maximal, equity drawdown maximal, balance drawdown relative, and equity drawdown relative.
- [X] Metrics without confidence intervals in production-realistic reports shall disclose why interval evidence is unavailable and whether the omission downgrades the result.
- [X] The system shall calculate portfolio metrics.
- [X] The system shall include robustness metrics when Monte Carlo or walk-forward analysis is enabled.
- [X] Every report shall state whether the run used full production realism, MT5-parity settings, or research approximation settings.
- [X] The official report formats shall be JSON and Markdown.
- [X] HTML reports may be generated from the official JSON and Markdown artifacts.
- [X] CSV exports shall be supported for tabular report sections such as orders, deals, trades, positions, account snapshots, and diagnostics.
- [X] Notebook objects may consume official artifacts but shall not be a required production report format.
- [X] The official JSON report shall be the canonical machine-readable report artifact.
- [X] The official Markdown report shall be the required human-review report artifact for Phase 1 CI and release evidence.
- [X] A run shall not receive `production_realistic` classification unless every required checklist item is true or explicitly marked not applicable by an approved owner decision recorded in the report.
- [X] Reports using FX `production_realistic` V1 shall disclose these non-goals when they are material to interpretation.
- [X] Reports shall disclose when dividend income is ignored.
- [X] Delisting losses, including possible negative 100 percent returns for equity holdings, shall be reflected in realized PnL, equity curve, drawdown, and reports.
- [X] Production-equity reports shall disclose unsupported corporate-action behavior.
- [X] Reports shall separate trade PnL from roll yield where possible.
- [X] Reports shall disclose total funding paid or received.
- [X] Reports shall disclose net trading PnL excluding funding.
- [X] Portfolio reports shall include currency exposure and currency PnL attribution.
- [X] The system shall support optional benchmark-relative reports.
- [X] Reports shall clearly omit benchmark metrics when benchmark data is not provided.
- [X] Disabled regulatory checks shall be disclosed for regulated asset-class reports.
- [X] Optimization reports shall disclose total parameter combinations tested, rejected combinations, failed combinations, and final selected parameter lineage.
- [X] Reports shall disclose whether a result is single-run, optimized, walk-forward selected, or post-hoc selected.
- [X] Reports shall warn when the same dataset was used for strategy discovery, parameter selection, and final evaluation.
- [X] Reports shall disclose whether execution models are broker-calibrated, venue-calibrated, generic, synthetic, or uncalibrated.
- [X] Reports shall disclose material vendor-data limitations.
- [X] Data-source license or retention conflicts shall block external report export unless explicitly approved.
- [X] Point calculations shall preserve decimal precision internally and shall be rounded only at configured reporting or validation boundaries.
- [X] Production runs shall fail closed or require explicit diagnostic override when optional service degradation would weaken durability, replayability, auditability, or report correctness.
- [X] Sensitive identifiers shall be redacted, hashed, or pseudonymized before appearing in standard logs or reports.
- [X] A generated traceability report shall fail CI when an accepted implementation requirement lacks mapped verification or when a future requirement is marked blocking for Phase 1 without owner approval.
- [X] Production realism shortcuts must be disclosed in the report.
- [X] Benchmark-relative reports require benchmark data aligned to the same clock and currency as the strategy.
- [X] A required model may be disabled only if the report records the disablement and downgrades the realism label where relevant.
- [X] Multi-currency cash ledgers and currency exposure report.
- [X] Every report shall disclose commission model.
- [X] Every report shall disclose market-hours and gap policy.
- [X] Every report shall disclose portfolio-risk model.
- [X] Every report shall disclose corporate-action model.
- [X] Every report shall disclose futures-rollover model.
- [X] Every report shall disclose perpetual-funding model.
- [X] Every report shall disclose currency-conversion model.
- [X] Every report shall disclose benchmark model.
- [X] Every report shall disclose regulatory-constraint model.
- [X] Every report shall disclose the run classification: `production_realistic`, asset-class-specific production-realistic label, `mt5_parity_oriented`, or `research_approximation`.
- [X] Every report shall disclose disabled required models and any realism-label downgrade.
- [X] Equity reports shall disclose corporate-action adjustment method.
- [X] Futures reports shall disclose rollover policy and roll PnL attribution where possible.
- [X] Perpetual reports shall disclose total funding paid/received and net trading PnL excluding funding.
- [X] Multi-currency reports shall reconcile native and base-currency ledgers.
- [X] Reports shall disclose IOC remainder cancellation diagnostics.
- [X] Reports shall disclose FX stale-rate diagnostic overrides.
- [X] Reports shall disclose rejected FX cross-rate synthesis diagnostics when they affect a run.
- [X] Reports shall disclose model inventory ids, validation status, material model exceptions, and approval expiry for production-candidate runs.
- [X] Reports shall disclose research protocol id, selection method, optimization status, out-of-sample degradation, and parameter-sensitivity status when strategy research or optimization influenced the result.
- [X] Reports shall disclose execution-model calibration status and whether execution models are broker-calibrated, venue-calibrated, generic, synthetic, or uncalibrated.
- [X] Reports shall disclose execution latency model, latency assumptions, and latency diagnostics when latency modelling is enabled.
- [X] Reports shall disclose market-halt, limit-up/limit-down, portfolio kill-switch, trailing-stop, pegged-order, and cancel-replace behavior when encountered.
- [X] Equity and ETF reports shall disclose delisting treatment, recall-risk model, forced buy-ins, and borrow availability assumptions when applicable.
- [X] Regulated asset reports shall disclose SEC Rule 201, wash-sale diagnostics, and disabled tax-aware or regulatory modules where applicable.
- [X] ML or alternative-data reports shall disclose feature-store point-in-time status, alternative-data alignment policies, lag assumptions, and rejected feature lookahead diagnostics.
- [X] Reports shall disclose vendor-data limitations, data revision policy, and point-in-time snapshot status when external data sources are used.
- [X] Reports shall disclose partial-data handling decisions, quarantined symbol-date ranges, stale-data fallback usage, and any resulting realism downgrade.
- [X] Reports shall disclose metric confidence intervals for material production-realistic metrics or explicitly disclose why intervals are unavailable.
- [X] Reports shall disclose immutable run-configuration artifact id, environment diagnostic hash, and environment drift warnings when applicable.
- [X] Reports shall disclose queue wait time, execution worker id, retry count, resume source, and checkpoint id for service-mode runs.
- [X] Reports shall disclose canary comparison and synthetic transaction probe evidence when used for release or service-health validation.
- [X] Reports shall disclose FX `production_realistic` V1 non-goals where material.
- [X] Reports shall declare distribution mode: `internal_research`, `internal_production_review`, `client_facing`, `investor_facing`, or `public`.
- [X] Client-facing, investor-facing, or public reports shall include hypothetical-performance disclosures when results are simulated.
- [X] External report generation shall support a compliance approval workflow before export.
- [X] External reports shall prevent unsupported performance claims and shall include configured legal or compliance disclaimers.
- [X] Documentation shall include report examples for FX, equity, futures, perpetual, and multi-currency portfolios before those scopes are production-promoted.
- [X] Documentation shall describe FX stale-rate behavior, `max_fx_rate_age_seconds`, diagnostic overrides, and report disclosures.
- [X] Documentation shall include confidence interval methodology for reported metrics and downgrade behavior when intervals are unavailable.
- [X] Documentation shall include external-report distribution modes, hypothetical-performance disclosures, compliance approval workflow, and unsupported-claim controls.
- [X] No file-specific non-functional requirements defined.
- [X] Disabled regulatory checks for regulated asset-class reports.
- [X] Corrupted artifact manifest is encountered during replay or report generation.
- [X] Requirement-to-test traceability report for all accepted Phase 1 requirements.
- [X] Report-confidence-interval tests shall verify material production-realistic metrics include confidence intervals or explicit omission disclosure and downgrade behavior.


### Hardening Amendments

#### Sprint-pack execution and execution-provider parity

Requirements:

- [X] Split Phase 8 implementation into approved sprint packs before editing code: 08A models/config/journal, 08B replay clock/data feed, 08C order lifecycle/fill engine, 08D portfolio/account/equity, 08E reports/analytics integration, and 08F spread/slippage/latency/partial-fill realism. *docs/phase-implementation-plan/08-simulator-engine.md:1957*
- [X] Each Phase 8 sprint pack must have its own dry run, approval, tests, rollback plan, and implementation report. *tests/unit/app/services/simulator/test_08a_foundation.py:48*
- [X] Implement the simulator as an `ExecutionProvider` compatible adapter instead of calling live broker execution code directly. *app/services/simulator/trader.py:135*
- [X] Adopt Phase 1.5 contracts for BacktestConfig, BacktestResult, TradeResult, ExecutionReport, Fill, Position, AccountSnapshot, PortfolioSnapshot, and AuditEvent. *app/services/simulator/trader.py:149*
- [X] Ensure simulated execution and live execution share canonical request/result contracts but have separate provider implementations. *app/services/simulator/trader.py:149*
- [X] Add tests proving Simulator can run without MT5, cTrader, Binance, network clients, broker credentials, or live account configuration installed. *tests/unit/app/services/simulator/test_08a_foundation.py:161*

#### Performance, audit overhead, and acceleration boundaries

Requirements:

- [X] Simulator shall use `asyncio` or an approved asynchronous writer boundary for journal, report, artifact, and sidecar I/O while keeping the canonical state transition order deterministic. *app/services/simulator/journal.py:154*
- [X] CPU-bound tick matching, fill calculation, and accounting loops shall be isolated behind approved execution backends that may include local sequential execution, multiprocessing, or optional accelerated implementations such as Cython or Numba.
- [X] Optional accelerated backends shall be feature-flagged, parity-tested against the canonical Python backend, and disabled by default when dependencies are missing or unsupported.
- [X] Decimal arithmetic shall remain mandatory for externally visible financial cashflows and ledger state, while any optimized internal representation must prove exact reconciliation back to Decimal ledger outputs before acceptance.

### Unit Tests Required

```text

tests/unit/app/services/simulator/

```

Test coverage:

- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/08_simulator.py

```

Usage examples must show:

- `example_01_run_backtest`: Demonstrate canonical backtest request, run lifecycle, standard result, and reproducible run IDs.
- `example_02_tick_engine_and_orders`: Demonstrate market, limit, stop, stop-limit, trailing-stop, and pegged order behavior.
- `example_03_execution_costs_and_slippage`: Demonstrate spreads, commissions, swaps, slippage caps, and liquidity walk behavior.
- `example_04_positions_and_accounting`: Demonstrate hedging/netting positions, margin, PnL, equity, and balance accounting.
- `example_05_journal_and_event_log`: Demonstrate deterministic journals, event logs, receipts, and audit metadata.
- `example_06_strategy_adapter`: Demonstrate strategy signal ingestion, risk/trading boundaries, and blocked broker mutation.
- `example_07_metrics_and_reports`: Demonstrate simulator summary, equity curve, drawdown, trade stats, and artifact references.
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

feat(simulator-engine): implement simulator execution engine and account models



- Build orchestrator and simulator loop for tick-by-tick and bar execution

- Implement simulated fee, commission, swap, slippage, and margin models

- Build liquidity walk order book matching engine for simulated deal fills

- Integrate journal logs, metrics scorecard, and simulator performance report

```

- [X] The same configuration, data, and seed shall produce the same metrics. *tests/unit/app/services/simulator/test_08a_foundation.py:48*
- [X] Diagnostic mode may continue only far enough to emit bounded diagnostics, partial artifacts, failed invariant details, and safe remediation hints.
- [X] Importing public simulator modules shall not start workers, open network connections, read secrets, write artifacts, register global mutable state, access market data, contact brokers, or launch background schedulers. *tests/unit/app/services/simulator/test_08a_foundation.py:153*
- [X] Production run-configuration artifacts shall be signed or checksum-verified and shall be the single source of truth for replay.
- [X] Synthetic transaction probes shall alert when the canonical simulator fails, produces non-deterministic output, violates expected metrics tolerance, or cannot produce required artifacts.
- [X] Retention tier, deletion eligibility, and legal-hold status shall be stored in the artifact manifest.
- [X] Protected artifacts shall be readable only by authorized roles and approved service identities.
- [X] Phase 1 local-only research artifacts may remain unencrypted only when explicitly classified as local research, stored outside protected artifact roots, and excluded from production-candidate evidence.
- [X] Production artifacts shall record git commit, dependency lock hash, container image digest when applicable, build timestamp, builder identity, and release signature.
- [X] Official release artifacts shall be signed or checksum-verified before deployment.
- [X] `artifact_root_ref` shall resolve through an allowlisted root or registry entry, not an arbitrary filesystem path.
- [X] Distributed work units shall pull inputs from and write outputs to a shared versioned artifact store; local worker disk shall never be the sole source of truth for shared artifacts.
- [X] Failed runs shall return the same envelope with `status=failed`, deterministic error code, safe error message, and any completed diagnostic artifacts.
- [X] Calibration artifacts shall be immutable once attached to a production-candidate run.
- [X] Vendor data changes after a completed production run shall not mutate historical run artifacts.
- [X] Promotion manifests shall be retained with the release artifacts they approve.
- [X] Artifact path attempts directory traversal or resolves outside allowlisted roots.
- [X] Artifact store is unavailable before run start.
- [X] External dependency timeout occurs during data manifest, broker profile, artifact store, secrets-provider, scheduler, worker heartbeat, or optional service access.
- [X] Fault-injection tests shall verify `SIM_PERSISTENCE_FAILED` is returned, the run halts cleanly, the last committed JSONL sequence remains recoverable, and corrupted partial artifacts are not promoted.
- [X] Secure-SDLC tests shall cover dependency lock validation, SBOM generation, vulnerability scan evidence, secret scan evidence, release artifact checksums, and release signatures where enabled.
- [X] Observability tests shall cover trace context propagation, required pipeline spans, business metrics export, SLO burn-rate alert inputs, and predictive alert rule configuration where supported.
- [X] Vendor-governance tests shall cover vendor inventory records, license conflicts, point-in-time snapshot requirements, vendor restatement policy, and immutable historical artifacts.
- [X] Retention and redaction tests shall cover retention tiers, legal-hold metadata, artifact checksums, disallowed secret fields, pseudonymized actors, and protected artifact access.
- [X] Dependency lock, SBOM, vulnerability scan, secret scan, static security analysis, and artifact checksum checks shall pass before production release workflows are enabled.
- [X] `diagnostic_failed` envelope example showing bounded diagnostics, warnings, safe error details, artifacts, and non-promotable classification.
- [X] Poison-pill policy for repeated work-unit failure thresholds, quarantine behavior, alert routing, and diagnostic artifact retention.
- [X] Observability configuration for tracing, metrics export, SLO thresholds, synthetic probes, canary analysis, and alert routing.
- [X] Immutable run-configuration artifact for production runs.
- [X] Required artifact retention tier for every official run.
- [X] Realism-disclosure summary.
- [X] Benchmark-relative metrics when benchmark data is provided.
- [X] Walk-forward in-sample and out-of-sample metrics when enabled.
- [X] Immutable run-configuration artifact and checksum or signature.
- [X] OpenTelemetry trace identifiers and business-metric export metadata when observability is enabled.
- [X] Documentation shall include retention, redaction, and protected-artifact operating procedures.
- [X] Documentation shall include observability metrics, alerting expectations, SLOs, and operational runbooks.
- [X] Documentation shall include OpenTelemetry tracing, business metrics, predictive alerting, synthetic transaction monitoring, and canary analysis procedures.
- [X] Documentation shall include secure-SDLC and software supply-chain procedures, including SBOM, dependency scanning, secret scanning, release signing, and artifact checksum verification.
