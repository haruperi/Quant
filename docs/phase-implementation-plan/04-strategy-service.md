## Phase 4 Strategy Service

### Goal

Implement the Strategy Service requirements under `app/services/strategies/` while preserving the phase module boundaries and governance rules.

Task inventory: 457 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

Required files:

```text

app/utils/__init__.py

app/utils/errors.py

app/services/indicators/__init__.py

app/services/indicators/registry.py

app/services/data/__init__.py

```

Required functionality:

- Indicators (SMA, EMA, ATR, RSI) can be calculated and cached.
- Data gateway can retrieve OHLCV historical sequences.
- Domain registry, validation, and standard exceptions exist.

### Files to Create

```text

app/__init__.py

app/services/strategies/__init__.py

app/services/strategies/registry.py

app/services/strategies/protocols.py

app/utils/errors.py

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

- [ ] Strategy documentation retention periods shall be defined for regulatory inquiries.
- [ ] Documentation shall include strategy input modes approved for `run_backtest`.
- [ ] Requirements without implementation scope shall carry an explicit `Documentation Only`, `Future`, or `Not Implemented` rationale.

#### `app/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [ ] Strategies shall not assume infinite liquidity at the best bid or ask.
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

- [ ] A strategy registry entry may declare `min_expected_alpha`, `max_acceptable_transaction_cost`, both, or neither.
- [ ] The module shall provide an official strategy registry.
- [ ] Registered strategies shall declare strategy id, version, module path, owner, configuration schema, supported symbols or asset classes, supported timing policy, required indicators, required data, risk assumptions, and permitted execution modes.
- [ ] Registered strategy identifiers shall resolve only to approved strategy modules.
- [ ] Strategy configuration shall be schema-validated before execution.
- [ ] Invalid strategy identifiers shall fail deterministically before simulation execution.
- [ ] Invalid strategy configuration shall fail deterministically before simulation execution.
- [ ] Strategy registry entries shall include version hashes for replay and audit.
- [ ] Strategy files and module paths shall resolve through approved registries or allowlisted roots, not arbitrary user-supplied filesystem paths.
- [ ] Duplicate strategy id/version registry entries shall fail registry validation deterministically before execution.
- [ ] Strategy version constraints shall resolve deterministically to exactly one approved immutable version or fail with `STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE` before execution.
- [ ] Deprecated strategies shall fail with `STRATEGY_DEPRECATED` unless explicitly run in approved historical replay mode.
- [ ] Strategy configuration schemas shall define default handling, unknown-field policy, required-field policy, type-coercion policy, enum validation, and version migration behavior.
- [ ] Strategy configuration validation shall reject configuration-injection patterns, including string fields that request evaluation, import, subprocess execution, filesystem access, network access, environment-variable access, template expansion, or dynamic attribute access unless a future approved sandbox contract explicitly permits them.
- [ ] Strategy configuration validation shall explicitly reject `eval()`, `exec()`, dynamic `__import__`, import strings, function-object strings, and magic-method access patterns in user-provided configuration.
- [ ] Strategy configuration validation shall enforce maximum payload size, maximum nesting depth, maximum string length, maximum collection length, and maximum schema-validation time before implementation acceptance.
- [ ] Strategy registry entries shall include owner, reviewer, approver, approval timestamp, approval expiry, and linked validation artifact ids.
- [ ] Strategy registry entries shall include source commit hash, artifact hash, package version, dependency lockfile hash, and build environment identifier.
- [ ] A strategy shall not execute in an environment not declared in its registry entry.
- [ ] Breaking changes to `TradeIntent`, strategy configuration schemas, event interfaces, or registry schemas shall require a version bump.
- [ ] ML-based strategies shall load models exclusively from an approved, versioned model registry or approved local artifact store, not arbitrary file paths.
- [ ] Provisional v1.0 baseline: event-driven strategy decision latency shall target P99 <= 10 ms per event on the approved reference environment unless a stricter registry profile is approved.
- [ ] Provisional v1.0 baseline: vectorized batch strategy execution shall target P99 <= 500 ms for the approved benchmark batch profile unless a stricter registry profile is approved.
- [ ] Provisional v1.0 baseline: each strategy instance shall target memory usage <= 256 MB, checkpoint size <= 10 MB, diagnostic payload <= 64 KB per decision, configuration payload <= 64 KB, and dependency call timeout <= 2 seconds unless an approved registry profile overrides the value.
- [ ] Documentation shall include strategy registry behavior.
- [ ] No file-specific non-functional requirements defined.
- [ ] Null or missing strategy configuration shall either apply schema defaults or fail according to the registry entry's configuration policy.
- [ ] Duplicate registry entry for the same strategy id/version shall fail registry validation.
- [ ] Malformed registry configuration schema shall fail registry validation with `STRATEGY_INVALID_CONFIG`.
- [ ] Strategy registry tests shall verify registered strategy identifiers resolve to approved modules.
- [ ] Strategy registry tests shall verify unregistered strategy identifiers are rejected.
- [ ] Strategy registry tests shall verify unapproved modules are rejected.
- [ ] Strategy tests shall include contract tests against data, indicator, simulation, and registry interfaces.
- [ ] Technology stack version constraints shall be explicit for production-eligible strategy execution.
- [ ] Each public capability shall define versioned input and output schemas using Pydantic models, `TypedDict`, dataclasses, or an approved equivalent.
- [ ] Public capabilities shall be versioned and compatibility-tested before being consumed by orchestration, simulation, risk, portfolio, audit, reporting, or API workflows.
- [ ] Provisional v1.0 baseline: performance tests shall define reference hardware, operating system, Python version, dependency versions, dataset size, strategy type, and measurement method before targets are accepted in CI.
- [ ] Strategy APIs shall remain backward compatible within a major interface version.
- [ ] Public schema changes shall require a schema-version change and compatibility review.
- [ ] Error examples and diagnostics examples shall include `schema_version`, `request_id`, and `correlation_id`.
- [ ] `TradeIntent` objects shall include strategy id, strategy version, symbol, side, intent type, requested sizing mode or quantity hint, optional stop loss, optional take profit, optional expiration, optional rationale, and signal timestamp.
- [ ] Phase 1 strategy execution shall allow registered strategies and validated configuration only.
- [ ] Strategy replay shall use strategy id, strategy version, configuration hash, data checksum, indicator result manifest, and simulation config hash.
- [ ] The same strategy id, version, configuration, input data, indicator outputs, and simulation seed shall produce the same trade intents.
- [ ] Strategy identifiers, configuration hashes, and version hashes must be included in replay and audit metadata.
- [ ] Registered strategy identifier.
- [ ] Strategy version or version constraint.
- [ ] Strategy manifest containing strategy id, version, configuration hash, required indicators, required data, and timing policy.
- [ ] `TradeIntent` schema shall define required fields, optional fields, enum values, precision rules, nullability, serialization format, and schema version.
- [ ] Registered strategies shall have one lifecycle status: `DRAFT`, `RESEARCH`, `BACKTEST_APPROVED`, `PAPER_APPROVED`, `LIVE_ELIGIBLE`, `DEPRECATED`, or `REVOKED`.
- [ ] Material strategy changes shall require a new immutable strategy version.
- [ ] Registered strategies shall declare a strategy-level risk profile.
- [ ] Diagnostics shall include run id, strategy id, strategy version, configuration hash, data checksum, decision timestamp, signal timestamp, intent id, decision id, and error code where applicable.
- [ ] Registered strategy artifacts shall be immutable after approval.
- [ ] Strategy dependency versions shall be pinned for replayable execution.
- [ ] Strategy state checkpoint restore shall validate strategy id, version, configuration hash, state schema version, and checkpoint checksum.
- [ ] Strategy interface versions shall follow explicit compatibility rules.
- [ ] Deprecated strategy APIs shall include removal version, migration guidance, and compatibility test coverage.
- [ ] Strategy replay shall use the exact interface version active at the time of original execution unless an approved migration exists.
- [ ] The strategy domain requirements document shall be versioned using Semantic Versioning.
- [ ] Breaking changes to strategy interfaces shall require a major document version bump and a documented migration guide.
- [ ] Unsupported strategy version or unsatisfiable version constraint shall fail before execution.
- [ ] Checkpoint restore with unsupported schema version, checksum mismatch, or unauthorized source shall fail before execution.
- [ ] STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE
- [ ] Performance tests shall state the exact hardware/software environment, dataset size, strategy type, dependency versions, measurement method, and target thresholds used.
- [ ] Replay tests shall verify the same strategy id, version, configuration, input data, indicator outputs, and simulation seed produce the same trade intents.
- [ ] Replay tests shall verify historical interface versions are used unless an approved migration exists.
- [ ] Documentation shall include configuration schema requirements for registered strategies.
- [ ] Every strategy decision shall be reproducible from strategy id, strategy version, configuration hash, data checksum, indicator manifest, simulation config hash where applicable, interface version, timing policy, and seed material.

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
- [ ] Strategy implementations target Python.
- [ ] Official execution remains owned by the simulation module.
- [ ] Indicator calculations are owned by the indicator module.
- [ ] Data normalization and source-readiness rules are owned by the data module.
- [ ] Third-party service dependencies shall be declared before production-eligible strategy execution.
- [ ] Capacity assumptions shall include maximum supported symbols and maximum concurrent strategies.
- [ ] Assumption: This document remains a domain-level requirements source until the active roadmap approves Strategy implementation scope.
- [ ] Each public capability shall document an exact Python signature before implementation begins.
- [ ] Each public capability shall define its official callable name, stability level, intended consumers, input schema, output schema, deterministic error codes, side-effect policy, idempotency behavior, and compatibility guarantees before implementation begins.
- [ ] Public capabilities shall return structured results and shall not rely on free-form logs, unmapped exceptions, or implicit global state.
- [ ] Strategy code shall pass the project's configured type checker, expose public interfaces with docstrings or generated API documentation, avoid nondeterministic decision inputs except simulation-provided seeded randomness, and include linked unit or contract tests for each public strategy behavior.
- [ ] Strategy APIs shall remain separate from simulation execution services.
- [ ] Strategies shall use indicator module contracts for indicator-derived inputs.
- [ ] Strategies shall use data module contracts for normalized market data.
- [ ] Strategies shall not perform production `print()` output.
- [ ] Strategy diagnostics shall enforce redaction, maximum payload size, and structured schema validation.
- [ ] Strategy modules shall be deterministic under repeated execution with the same seed, inputs, configuration, indicator outputs, and environment policy.
- [ ] `MULTIPROCESS_ISOLATED` strategies shall define serialization, timeout, cancellation, restart, and resource-limit behavior.
- [ ] Randomized strategies shall use only the approved simulation-provided seeded randomness interface; direct use of process-global randomness is prohibited unless explicitly wrapped by that interface.
- [ ] Strategy dependency calls to data, indicator, simulation, or read-only state providers shall define timeout, retry/no-retry, stale result, partial failure, and exception mapping behavior.
- [ ] The strategy module shall live under `app/services/strategies/`.
- [ ] Strategies shall produce decisions, signals, trade intents, or strategy state updates.
- [ ] Strategies shall not directly mutate official account, order, deal, position, pending-order, margin, equity, journal, or execution timestamp state.
- [ ] Strategies shall not finalize official order volume, margin acceptance, execution price, fill status, or risk approval.
- [ ] Official execution, matching, accounting, journal, reporting, and production-realism classification shall remain owned by `app/services/simulation/`.
- [ ] Martingale, grid, pyramiding, basket recovery, and trade-decomposition strategies shall execute through the canonical simulation tick engine.
- [ ] Advanced strategies shall query the simulation engine for actual fills, remaining volume, average price, and open exposure through approved read-only interfaces.
- [ ] Advanced strategies that need fills or open positions shall use `ReadOnlyExecutionStateQuery` and `ReadOnlyExecutionStateSnapshot`; direct access to official simulation, execution, account, or position state is prohibited.
- [ ] Martingale level progression shall be based on confirmed deals or official position state, not submitted requests.
- [ ] When `min_expected_alpha` or `max_acceptable_transaction_cost` is declared, the strategy shall evaluate the declared threshold before emitting a trade intent and shall emit a deterministic suppression diagnostic when the threshold blocks the decision.
- [ ] Strategies shall emit `TradeIntent` objects instead of official orders.
- [ ] `TradeIntent` objects shall include an explicit `allow_partial_fills` boolean and `min_fill_size` parameter to guide the simulation or execution engine.
- [ ] Bar-based signals shall be aligned using the configured signal timing policy before becoming executable trade intents.
- [ ] The simulation engine shall transform `TradeIntent` into a sized `TradeRequest`.
- [ ] The simulation engine shall execute `TradeIntent` objects only when the canonical tick loop reaches an eligible tick.
- [ ] Strategies may request a sizing mode but shall not directly finalize official volume.
- [ ] Strategy-generated rationales shall be preserved for compliance or audit records when provided.
- [ ] The default strategy signal timing policy shall be `BAR_OPEN_PREVIOUS_CLOSE`.
- [ ] At the first tick of bar `N`, strategies may use only bars up to and including fully closed bar `N-1`.
- [ ] At the first tick of bar `N`, strategies shall not use current incomplete bar `N` high, low, close, volume, indicator-derived values, multi-timeframe values, or metadata derived from unavailable current-bar data.
- [ ] Strategies shall enter at the first valid tick of bar `N` only when a valid trade intent is emitted from previous-closed-bar data.
- [ ] Strategy tests shall cover previous-close-only behavior, shifted signals, no current-bar leakage, and first tick of new bar activation.
- [ ] Strategies shall enforce point-in-time correctness for all feature and indicator lookups.
- [ ] A query for data at timestamp `T` shall return only the state of the data as it was known at `T`, excluding subsequent revisions, restatements, or late-arriving ticks.
- [ ] Strategies shall declare `max_data_latency_tolerance`.
- [ ] Data arriving outside the declared latency tolerance shall cause the strategy to skip the decision or emit `STRATEGY_STALE_DATA`.
- [ ] `run_backtest` shall not execute arbitrary user-provided Python code strings.
- [ ] Approved strategy code shall still be protected by resource controls for CPU time, recursion depth, loop iterations where measurable, memory growth, checkpoint size, diagnostic size, and dependency call timeouts.
- [ ] Strategies may maintain decision state only.
- [ ] Strategy decision state shall be serializable when checkpoint or replay workflows require it.
- [ ] Strategy state checkpoints shall not include secrets or unrestricted raw proprietary strategy source.
- [ ] Concurrent strategy instances shall not share mutable strategy-local state unless an approved synchronization contract exists.
- [ ] Strategies may maintain decision state but shall not mutate official trading state.
- [ ] Bar-open trading must use previous closed-bar data by default.
- [ ] Advanced stateful strategies and agent-generated strategies shall provide decision rationale when required by compliance configuration.
- [ ] Validated strategy configuration.
- [ ] Indicator specifications or precomputed indicator outputs.
- [ ] Normalized market data.
- [ ] Symbol metadata.
- [ ] Signal timing policy.
- [ ] Timestamped `TradeIntent` objects.
- [ ] Strategy diagnostics.
- [ ] Strategy rationale where provided.
- [ ] Strategy state checkpoint where enabled.
- [ ] Promotion between lifecycle states shall require recorded evidence, including test results, validation report, owner approval, and risk approval where applicable.
- [ ] The risk profile shall include maximum gross exposure, maximum net exposure, maximum symbol exposure, maximum intent notional, maximum intent frequency, maximum concurrent positions, maximum pyramiding depth, maximum martingale level, and maximum grid depth where applicable.
- [ ] Strategy risk declarations shall be advisory inputs to the simulation or risk engine and shall not replace official risk approval.
- [ ] Strategies may self-suppress trade intents when strategy-local risk limits are breached.
- [ ] Risk-limit breaches shall produce deterministic diagnostics and audit metadata.
- [ ] Strategy risk profiles shall include concentration risk limits where applicable.
- [ ] Strategy risk profiles shall include time-based exposure limits where applicable.
- [ ] Strategy risk profiles shall declare gap risk assumptions.
- [ ] Every `TradeIntent` shall include a deterministic `intent_id`.
- [ ] Every `TradeIntent` shall include an idempotency key.
- [ ] Child intents shall include `parent_intent_id` when created from decomposition, scale-in, scale-out, recovery, or basket logic.
- [ ] Trade intents shall include a monotonically increasing strategy-local sequence number.
- [ ] Superseded, cancelled, expired, or replaced intents shall preserve lineage to the original intent.
- [ ] Strategies shall not emit executable trade intents until required indicators are warm and ready.
- [ ] Indicator readiness shall include warmup period, minimum sample count, NaN policy, and dependency readiness.
- [ ] Strategies shall declare their missing-data policy: reject, forward-fill, interpolate, skip signal, or use module default.
- [ ] Strategies shall declare their stale-data policy.
- [ ] Strategies shall declare whether they require bid, ask, mid, last, volume, spread, session metadata, corporate-action-adjusted prices, or raw prices.
- [ ] Multi-timeframe indicators shall be usable only when the higher-timeframe bar is fully closed as of the strategy decision timestamp.
- [ ] Strategy execution shall emit structured diagnostics, not free-form logs.
- [ ] Strategy execution shall support trace correlation across data, indicator, strategy, simulation, and reporting modules.
- [ ] Parameter optimization shall produce a validation artifact.
- [ ] Validation artifacts shall include parameter search space, objective function, training period, validation period, test period, data checksum, transaction-cost assumptions, slippage assumptions, and random seed.
- [ ] Strategy validation shall include in-sample and out-of-sample results.
- [ ] Strategy validation shall include walk-forward or rolling-window analysis where applicable.
- [ ] Strategy validation shall include transaction-cost sensitivity and slippage sensitivity.
- [ ] Strategy validation shall include market-regime analysis where applicable.
- [ ] Strategy validation shall reject or flag configurations whose performance depends on future data, unclosed bars, unapproved survivorship-biased data, or unapproved parameter leakage.
- [ ] Optimized configurations shall be immutable and hash-addressed before simulation or production replay.
- [ ] Strategies shall declare expected computational complexity or supported maximum input size where applicable.
- [ ] Strategies shall declare their concurrency model: `SYNC_BLOCKING`, `ASYNC_AWAIT`, or `MULTIPROCESS_ISOLATED`.
- [ ] Strategy execution shall have configurable per-decision latency budgets.
- [ ] Strategy execution shall have configurable memory limits.
- [ ] Strategy state checkpoint size shall be bounded and monitored.
- [ ] Strategies shall not instantiate unbounded caches, memoization dictionaries, or rolling window arrays without explicit maximum size limits and eviction behavior.
- [ ] Strategy behavior under timeout shall be deterministic.
- [ ] Performance regression tests shall verify strategy latency and memory remain within approved budgets.
- [ ] Strategy artifacts shall be produced by an approved build pipeline.
- [ ] Strategy artifacts shall pass type checking, linting, unit tests, contract tests, security scans, and dependency vulnerability checks before approval.
- [ ] Strategy artifacts shall include an SBOM where production packaging requires it.
- [ ] A strategy failure shall not corrupt official simulation state.
- [ ] Strategy failures shall be isolated to the failing strategy instance unless configured fail-fast behavior requires run termination.
- [ ] Strategies shall support an external asynchronous hard kill signal from the orchestration layer.
- [ ] A hard kill signal shall immediately halt execution, cancel pending intents, and dump state according to the approved emergency policy.
- [ ] Upon receiving a hard kill signal, the strategy shall emit a final `STRATEGY_HARD_KILLED` diagnostic with the last known safe state checkpoint.
- [ ] Strategies shall declare permitted environments: `BACKTEST`, `REPLAY`, `PAPER`, `SHADOW`, or `LIVE`.
- [ ] Paper or live execution eligibility shall require successful completion of configured validation gates.
- [ ] Live execution shall require explicit approval, expiry, rollback plan, monitoring plan, and emergency disable procedure.
- [ ] Environment-specific configuration differences shall be explicit, hash-addressed, and audit-recorded.
- [ ] Strategies shall not use wall-clock time, system randomness, network state, filesystem state, or environment variables as decision inputs.
- [ ] Randomized strategies shall use only simulation-provided seeded randomness.
- [ ] Price, volume, and quantity comparisons shall follow approved precision and rounding rules.
- [ ] Floating-point tolerance rules shall be explicit in tests.
- [ ] Every production-eligible strategy shall include a runbook.
- [ ] The runbook shall document expected behavior, configuration parameters, known failure modes, monitoring metrics, disable procedure, replay procedure, and owner escalation path.
- [ ] Strategies shall declare their execution assumptions, including fill model, latency model, and market impact model.
- [ ] Trade intents shall specify acceptable execution algorithms, such as `TWAP`, `VWAP`, or `ICEBERG`, where applicable.
- [ ] Strategies shall declare maximum permissible spread for execution.
- [ ] Strategies shall declare minimum volume requirements and maximum volume participation rates.
- [ ] Dark pool, auction, and alternative venue eligibility shall be explicitly declared.
- [ ] Strategies shall declare one deterministic policy for each halt-like market state: `SUPPRESS_NEW_INTENTS`, `ALLOW_REDUCE_ONLY`, `CLOSE_INTENTS_ONLY`, or `NO_SPECIAL_HANDLING`.
- [ ] The selected halt-like market-state policy shall be included in strategy diagnostics when such a market state affects a decision.
- [ ] Fill probability models shall account for queue position and adverse selection where applicable.
- [ ] Strategies shall declare interaction modes: `INDEPENDENT`, `COOPERATIVE`, or `PORTFOLIO_AWARE`.
- [ ] Strategies shall declare portfolio-interaction assumptions and optional strategy-local exposure preferences.
- [ ] Portfolio-level gross and net exposure enforcement shall remain owned by the portfolio or risk module.
- [ ] Strategy-level capital allocation assumptions and position-sizing preferences shall be metadata for portfolio or risk consumers, not official allocation enforcement.
- [ ] Strategies may declare conflict-priority hints, but cross-strategy conflict resolution shall remain owned by portfolio, risk, or orchestration modules.
- [ ] Correlation-aware position-limit assumptions shall be declared where applicable.
- [ ] Strategy turn-off and onboarding runbook metadata shall describe existing-position assumptions; official position handling shall remain owned by trading, risk, portfolio, live, or simulation modules.
- [ ] Strategy health checks shall be defined for signal generation frequency, decision staleness, and data freshness.
- [ ] Strategies shall declare circuit-breaker inputs, expected trigger diagnostics, and safe-disable behavior; circuit-breaker enforcement shall remain owned by orchestration, risk, live, or operations modules.
- [ ] Strategies shall declare graduated-deployment eligibility metadata and rollback assumptions; deployment progression and rollback enforcement shall remain owned by deployment or operations modules.
- [ ] Strategy performance metadata shall declare expected review bands for supplied analytics, but these bands shall not become approved risk thresholds or promotion rules until owner/governance approval records them.
- [ ] Strategies shall emit or expose drift-detection diagnostics where applicable; alert routing remains owned by observability or operations modules.
- [ ] Canary-analysis metadata shall describe expected paper/live consistency checks; official comparison and promotion decisions remain owned by analytics, risk, live, or governance modules.
- [ ] Strategies shall declare applicable regulatory regimes, such as `SEC`, `ESMA`, or `FCA`, where applicable.
- [ ] Position-limit and reporting assumptions by jurisdiction shall be declared where applicable; official regulatory reporting and limit enforcement remain owned by compliance, risk, portfolio, or reporting modules.
- [ ] Market manipulation safeguards shall prohibit spoofing, layering, marking the close, and equivalent manipulative behavior.
- [ ] Strategy audit metadata shall preserve intent creation and decision rationale references; official sizing, execution, fill, and regulatory audit records remain owned by trading, simulation, live, audit, or reporting modules.
- [ ] Best-execution and venue-analysis assumptions shall be declared where applicable; official venue analysis remains owned by execution, compliance, or reporting modules.
- [ ] Large-position reporting assumptions shall be documented where applicable; official reporting threshold enforcement remains external to the strategy module.
- [ ] Strategies shall declare maximum permissible data gaps before entering safe mode.
- [ ] Dividend, split, and corporate action handling procedures shall be specified.
- [ ] Strategies shall declare startup data-readiness requirements for completeness, expected ranges, and consistency checks; validation enforcement remains owned by data, orchestration, or simulation modules.
- [ ] Strategies shall declare delisted-symbol assumptions and safe behavior; official position liquidation procedures remain owned by trading, risk, live, portfolio, or operations modules.
- [ ] Strategy decision latency SLOs shall be defined by environment, including P50, P95, and P99 targets.
- [ ] Signal generation throughput minimums shall be defined for expected market conditions.
- [ ] Recovery point objectives shall be defined for strategy state.
- [ ] Resource utilization limits shall include CPU, memory, and network bandwidth budgets.
- [ ] Graceful degradation procedures shall be defined for overload conditions.
- [ ] Strategies shall define calibration frequency and trigger conditions.
- [ ] Parameter stability analysis shall cover different market regimes.
- [ ] Sensitivity analysis shall include approved parameter perturbation bands, including plus or minus 10% and plus or minus 20% where applicable.
- [ ] Minimum training data period requirements and regime representation shall be defined.
- [ ] Overfitting detection criteria and automated strategy retirement procedures shall be defined.
- [ ] Ensemble and model averaging policies shall be defined for production strategies where applicable.
- [ ] Strategy-local state checkpoint and restore assumptions shall be defined for primary and backup instances.
- [ ] Maximum tolerable strategy-local state loss and decision staleness shall be declared.
- [ ] Communication metadata for strategy degradation shall identify owner escalation paths; incident communications remain owned by operations.
- [ ] Market closure and early close strategy behavior shall be declared.
- [ ] Emergency position liquidation assumptions may be documented, but official liquidation procedures and responsible-party approval remain owned by trading, risk, live, portfolio, compliance, or operations modules.
- [ ] Strategy performance review cadence and responsible parties shall be defined.
- [ ] Automated performance attribution shall distinguish alpha, market exposure, and style factor contributions where applicable.
- [ ] Strategy improvements shall support an A/B testing framework where applicable.
- [ ] Shadow testing requirements shall be satisfied before production promotion.
- [ ] Kill criteria shall define objective rules for permanent strategy decommissioning.
- [ ] Strategy intellectual property classification and protection measures shall be documented.
- [ ] Third-party dependency licensing compliance shall be verified.
- [ ] Data vendor agreement compliance checks shall be performed where applicable.
- [ ] Strategy descriptions shall be available for regulatory filings where applicable.
- [ ] Material change notification procedures to stakeholders shall be documented.
- [ ] Model artifacts shall be serialized in standardized, language-agnostic formats such as `ONNX` or `PMML` where possible.
- [ ] Strategies shall declare any dependency on a feature store.
- [ ] Feature lookups shall be validated against the strategy's declared point-in-time correctness policy.
- [ ] ML-based strategies shall implement concept drift and data drift detection where applicable.
- [ ] Strategies shall emit `STRATEGY_DRIFT_DETECTED` when input feature distributions or model prediction confidence deviate beyond approved statistical thresholds.
- [ ] Strategies shall be prohibited from containing hardcoded secrets, API keys, or credentials.
- [ ] Strategies requiring external configuration secrets shall request them through an approved read-only secrets manager interface injected at runtime by the orchestration layer.
- [ ] Strategies shall not log, serialize, checkpoint, or expose secrets in diagnostics, rationale, manifests, or state snapshots.
- [ ] Strategies using Level 2 or Level 3 data shall declare their maximum supported order book depth.
- [ ] Strategies may annotate intents with declared maximum volume participation assumptions for visible order book data at the decision timestamp; official sizing validation remains owned by risk, trading, simulation, or live execution modules.
- [ ] Strategies shall define deterministic behavior when order book data is crossed, locked, stale, incomplete, or outside the declared supported depth.
- [ ] Each requirement shall be traceable to a specific test case id where implementation is required.
- [ ] Major design-choice requirements shall be traceable to an Architecture Decision Record.
- [ ] A strategy shall not be considered production-ready until it passes applicable testing, validation, and runbook requirements.
- [ ] Production-ready strategy approval shall require sign-off from the Quant Research Lead and Engineering Lead, or their approved delegates.
- [ ] Strategies shall follow a standard processing anatomy: data input, indicator calculation, signal generation, timing alignment, trade intent creation, and simulation execution.
- [ ] Hook inputs and outputs shall be typed and schema-documented.
- [ ] Strategy hooks shall return only approved strategy outputs, including decisions, diagnostics, state updates, or `TradeIntent` objects.
- [ ] Strategy hooks shall not mutate official simulation, execution, account, order, position, journal, or reporting state directly.
- [ ] Required and optional hooks shall be explicitly declared by strategy type.
- [ ] Unsupported hooks for a strategy type shall fail deterministically or be ignored according to the approved interface contract.
- [ ] Invalid strategy configuration schema shall fail before execution.
- [ ] Unknown configuration fields shall be rejected or ignored according to an explicit schema policy.
- [ ] Data-service timeout, unavailable dependency, broken connection, or network partition shall produce `STRATEGY_DATA_NOT_READY` after the approved retry/no-retry policy is exhausted.
- [ ] Partial data degradation shall follow the strategy's declared missing-data policy: `reject` suppresses all intents, `skip signal` suppresses affected symbols, and any degraded subset execution shall emit `STRATEGY_DATA_QUALITY_GATE_FAILED` diagnostics naming omitted symbols without exposing private payloads.
- [ ] Duplicate, out-of-order, stale, revised, or late-arriving ticks shall follow the declared data policy.
- [ ] Strategy hook timeout shall return `STRATEGY_TIMEOUT` and follow the configured failure policy.
- [ ] Concurrent read-only state snapshots across multiple strategies shall define isolation level, snapshot timestamp, and behavior when official state updates during decision traversal.
- [ ] `STRATEGY_INVALID_CONFIG`
- [ ] `STRATEGY_NOT_FOUND`
- [ ] `STRATEGY_DEPRECATED`
- [ ] `STRATEGY_UNAPPROVED_MODULE`
- [ ] `STRATEGY_SCHEMA_VALIDATION_FAILED`
- [ ] `STRATEGY_UNSUPPORTED_TIMING_POLICY`
- [ ] `STRATEGY_ENVIRONMENT_NOT_PERMITTED`
- [ ] `STRATEGY_ARTIFACT_HASH_MISMATCH`
- [ ] `STRATEGY_DEPENDENCY_HASH_MISMATCH`
- [ ] `STRATEGY_CHECKPOINT_INCOMPATIBLE`
- [ ] `STRATEGY_DATA_NOT_READY`
- [ ] `STRATEGY_INDICATOR_NOT_READY`
- [ ] `STRATEGY_MISSING_REQUIRED_DATA`
- [ ] `STRATEGY_STALE_DATA`
- [ ] `STRATEGY_DUPLICATE_INTENT`
- [ ] `STRATEGY_RESOURCE_LIMIT_EXCEEDED`
- [ ] `STRATEGY_TIMEOUT`
- [ ] `STRATEGY_VALIDATION_ARTIFACT_REQUIRED`
- [ ] `STRATEGY_RISK_PROFILE_REQUIRED`
- [ ] `STRATEGY_CIRCUIT_BREAKER_TRIGGERED`
- [ ] `STRATEGY_POSITION_LIMIT_EXCEEDED`
- [ ] `STRATEGY_VOLUME_PARTICIPATION_EXCEEDED`
- [ ] `STRATEGY_PERFORMANCE_DEGRADED`
- [ ] `STRATEGY_DRIFT_DETECTED`
- [ ] `STRATEGY_REGULATORY_LIMIT_BREACHED`
- [ ] `STRATEGY_MARKET_ACCESS_REVOKED`
- [ ] `STRATEGY_HARD_KILLED`
- [ ] Every requirement id shall have at least one linked test id or a documented non-implementation rationale.
- [ ] Every usage example shall be executable or schema-validatable as documentation test coverage.
- [ ] The traceability matrix shall be tested or reviewed as an explicit pre-implementation deliverable.
- [ ] Public capability tests shall verify exact Python signatures, input schema validation, output schema validation, error decision tables, side-effect rules, and batch/stream behavior.
- [ ] Strategy tests shall cover EMA trend intents, martingale recovery, decomposition child orders, and partial-fill handling.
- [ ] Strategy tests shall cover previous-closed-bar signal timing and no-lookahead behavior.
- [ ] Strategy tests shall verify indicator-derived signals cannot access prohibited current-bar values.
- [ ] Strategy configuration tests shall verify valid schemas pass and invalid schemas fail deterministically.
- [ ] Strategy tests shall include golden-file replay tests for emitted `TradeIntent` manifests.
- [ ] Strategy tests shall include fuzz tests for invalid configuration, malformed data, missing fields, duplicate ticks, out-of-order ticks, NaN indicators, and extreme prices.
- [ ] Strategy tests shall include performance regression tests with approved latency and memory thresholds.
- [ ] Strategy tests shall include snapshot tests verifying stable intent ids, decision ids, configuration hashes, and replay manifests.
- [ ] Strategy tests shall include mutation testing to verify that deliberate subtle corruptions to strategy logic or data inputs are caught by the test suite.
- [ ] Boundary tests shall verify strategies cannot mutate official account, order, deal, position, margin, equity, journal, reporting, or execution timestamp state.
- [ ] Boundary tests shall verify portfolio, compliance, disaster-recovery, deployment, and venue requirements are exposed only as declarations or metadata, not enforced inside the strategy module.
- [ ] Security tests shall cover configuration-injection payloads, oversized configuration payloads, excessive nesting, excessive string lengths, and resource exhaustion through sanctioned strategy and indicator paths.
- [ ] Clock-drift tests shall verify behavior when strategy, data, indicator, or simulation timestamps exceed approved tolerance.
- [ ] Documentation shall state that raw arbitrary Python strategy code is not accepted by `run_backtest`.
- [ ] Documentation shall describe strategy replay metadata.
- [ ] Documentation shall include public capability contracts, requirement IDs, applicability tags, acceptance criteria, and linked test IDs before Builder handoff.
- [ ] Before Builder handoff, each requirement shall include a stable requirement id, priority, phase, applicability tags, owning module, acceptance criteria, and at least one linked test case id where implementation is required.
- [ ] Applicability tags shall identify whether a requirement applies to `BACKTEST_CORE`, `REPLAY`, `PAPER`, `SHADOW`, `LIVE`, `ML_ONLY`, `L2_L3_ONLY`, `REGULATED_MARKET_ONLY`, or `FUTURE`.
- [ ] A traceability matrix shall be a required deliverable before implementation begins, not a future improvement.
- [ ] Stable requirement IDs, acceptance criteria, applicability tags, and linked test IDs are required for v1.0 Builder handoff.
- [ ] Strategies shall emit `TradeIntent` objects and diagnostics, not broker orders, official fills, account mutations, portfolio mutations, risk approvals, or regulatory reports.
- [ ] Risk, trading, simulation, live, portfolio, compliance, reporting, data, and indicator modules shall remain the authorities for their own enforcement responsibilities.
- [ ] Strategy execution shall receive read-only snapshots or approved read-only handles for external state; strategy code shall not mutate official external state directly.
- [ ] Every external-module interaction shall pass through a documented contract with deterministic error mapping, timeout behavior, and redaction behavior.
- [ ] Strategy implementation scope shall be narrowed to an approved phase slice before Builder handoff.

#### `app/utils/errors.py`

Functions/classes:

- `STRATEGY_LOOKAHEAD_DETECTED`

Requirements:

- [ ] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom strategy exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.
- [ ] Strategy access to prohibited current-bar or future data shall fail with the canonical strategy-domain error code `STRATEGY_LOOKAHEAD_DETECTED`; lower-level simulation lookahead errors, if any, shall be mapped to this code before returning strategy diagnostics.
- [ ] Repeated strategy errors shall trigger deterministic disablement or escalation according to configuration.
- [ ] Strategies shall return safe, deterministic errors for invalid configuration or unsupported inputs.
- [ ] No file-specific non-functional requirements defined.
- [ ] Every public capability shall have contract tests for valid input, invalid input, deterministic errors, idempotency, and side effects.
- [ ] Error-code tests shall verify lower-level lookahead errors map to `STRATEGY_LOOKAHEAD_DETECTED` at strategy-module boundaries.
- [ ] Dependency-failure tests shall verify data-layer failures map to `STRATEGY_DATA_NOT_READY` or approved data errors and indicator-layer failures map to `INDICATOR_MODULE_ERROR`.
- [ ] Each public capability shall include a decision table mapping every validation condition, dependency condition, lifecycle condition, timeout condition, and security condition to one deterministic error code.
- [ ] Raw strategy-code injection attempts shall be rejected before execution.
- [ ] Rejected raw strategy-code input shall return `SIM_ARBITRARY_CODE_REJECTED`.
- [ ] Rejected strategy-injection attempts shall be journaled without logging unsafe code bodies in full.
- [ ] Rejected strategy-input diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code.
- [ ] Resource exhaustion by sanctioned strategy code, sanctioned indicator calls, or sanctioned data access shall fail deterministically with `STRATEGY_RESOURCE_LIMIT_EXCEEDED` or a more specific approved error code.
- [ ] Strategy security rejections must be journaled with safe redaction.
- [ ] Structured error result with deterministic error code on failure.
- [ ] Deprecated or revoked strategies shall fail deterministically before execution unless explicitly run in historical replay mode.
- [ ] The simulation or risk engine shall remain the final authority for official risk acceptance or rejection.
- [ ] Duplicate `intent_id` or idempotency key collisions shall fail deterministically.
- [ ] Strategy execution shall fail deterministically if required market data fields are missing, stale, out of order, duplicated, or timezone-inconsistent unless an explicit approved policy handles them.
- [ ] Strategy diagnostics shall support debug mode without exposing secrets, proprietary source, unsafe code bodies, or excessive market-data payloads.
- [ ] Strategy approval shall be invalidated if the source hash, artifact hash, dependency hash, or build provenance changes.
- [ ] The orchestration layer shall support deterministic failure policies: `FAIL_RUN`, `DISABLE_STRATEGY`, `SKIP_DECISION`, or `QUARANTINE_INSTANCE`.
- [ ] Corrupt, incompatible, or unauthorized checkpoints shall fail deterministically before execution.
- [ ] Strategies shall declare behavior when the data layer reports cross-venue price deviation, degraded data quality, failover, or unavailable data.
- [ ] Data vendor failover orchestration shall remain owned by the data or operations module.
- [ ] Recovery time objectives shall be defined for strategy restarts and failovers.
- [ ] Strategies shall declare assumptions for backup execution venues where applicable; backup venue failover enforcement remains owned by execution, live, or operations modules.
- [ ] Post-mortem documentation shall be required for strategy failures.
- [ ] Unknown strategy id shall fail before execution.
- [ ] Empty strategy identifier shall fail before execution with a deterministic validation error.
- [ ] Unapproved strategy module shall fail before execution.
- [ ] Raw arbitrary Python strategy code strings shall be rejected before execution.
- [ ] Unsafe rejected code bodies shall not be logged in full.
- [ ] Empty market-data input shall produce `STRATEGY_DATA_NOT_READY` or a more specific deterministic error.
- [ ] Indicator module timeout, unavailable dependency, broken connection, or unhandled indicator exception shall map to `INDICATOR_MODULE_ERROR` with original exception details redacted.
- [ ] Timezone-naive, DST-ambiguous, or timezone-inconsistent data shall fail unless an approved normalization policy exists.
- [ ] Clock drift beyond the approved tolerance between strategy runtime, data feed, indicator outputs, or simulation clock shall fail closed with `STRATEGY_STALE_DATA`, checkpoint abort, or a more specific approved error code.
- [ ] Duplicate `intent_id`, duplicate idempotency key, or non-monotonic strategy-local sequence number shall fail deterministically.
- [ ] Attempted secret exposure in diagnostics, checkpoints, manifests, or rationale shall fail redaction validation.
- [ ] `SIM_ARBITRARY_CODE_REJECTED`
- [ ] `STRATEGY_INTERNAL_ERROR`
- [ ] `INDICATOR_MODULE_ERROR`
- [ ] `STRATEGY_CHECKPOINT_INVALID`
- [ ] `STRATEGY_DATA_QUALITY_GATE_FAILED`
- [ ] Every confirmed error code shall have at least one focused failure-path test that triggers the code and verifies the full response or diagnostic shape.
- [ ] AI Tool strategy security tests shall verify `run_backtest` rejects raw arbitrary Python strategy code, returns `SIM_ARBITRARY_CODE_REJECTED`, does not execute rejected code, and does not log rejected code in full.
- [ ] Strategy tests shall include scenario tests for session boundaries, holidays, weekend gaps, DST transitions, spread spikes, partial fills, rejected fills, and multi-timeframe bar closure.
- [ ] Each confirmed error code shall have at least one triggering scenario and a stable diagnostic shape before implementation acceptance.

#### `app/services/strategies/vectorized.py`

Functions/classes:

- `run_vectorized_strategy_signals`
- `TradeIntent`
- `MULTIPROCESS_ISOLATED`

Requirements:

- [ ] Each public capability shall define whether results are returned as a single batch, iterator, stream, or async stream; `run_vectorized_strategy_signals` shall be treated as batch output until a streaming contract is explicitly approved.
- [ ] The module shall support vectorized signal strategies.
- [ ] Vectorized signal strategies shall compute indicators, generate signals, and convert signals to timestamped `TradeIntent` objects before simulation execution.
- [ ] Vectorized signal generation shall shift current-bar conditions so that bar-open entries are based on previous closed-bar values.
- [ ] If a vectorized batch detects lookahead at any element, the entire batch shall fail atomically, emit `STRATEGY_LOOKAHEAD_DETECTED`, discard intents produced by that batch, and preserve a diagnostic identifying the first failing timestamp.
- [ ] A vectorized batch decision clock shall be anchored to the supplied `StrategyExecutionContext.decision_timestamp`; wall-clock elapsed time during long-running batches shall not advance decision-time semantics.
- [ ] Vectorized processing is allowed only for indicator and signal generation.
- [ ] CPU-bound vectorized strategies shall run in isolated worker processes when their declared execution profile is `MULTIPROCESS_ISOLATED`, when configured by orchestration, or when measured event-loop latency exceeds the approved threshold for the target environment.
- [ ] Vectorized strategies shall calculate indicators in a vectorized manner where supported by the indicator module.
- [ ] Vectorized strategies shall generate signals in a vectorized manner before conversion to timestamped `TradeIntent` objects.
- [ ] Vectorized processing shall not bypass tick-accurate simulation execution, fill modeling, accounting, margin checks, risk checks, or journal generation.
- [ ] Hook execution order shall be deterministic and documented for vectorized runs, event-driven runs, replay, checkpoint restore, and shutdown.
- [ ] Documentation shall include examples for vectorized signal strategies and event-driven strategies.
- [ ] No file-specific non-functional requirements defined.
- [ ] Clock drift detected during a long-running vectorized batch shall not change the batch decision timestamp; the batch shall either complete under the original timestamp or fail atomically according to the configured clock-drift policy.
- [ ] Strategy tests shall cover vectorized signal strategies.
- [ ] `STRATEGY_LOOKAHEAD_DETECTED`
- [ ] Strategy tests shall include property-based tests for no-lookahead, deterministic replay, and risk-envelope invariants.
- [ ] Property-based no-lookahead tests shall cover timezone offsets, DST gaps, DST overlaps, session boundaries, late-arriving data, revised bars, and multi-timeframe closure boundaries.
- [ ] Documentation shall describe no-lookahead strategy timing.

#### `app/services/strategies/event.py`

Functions/classes:

- `FILL_UPDATE`
- `PARTIAL_FILL`
- `TradeIntent`
- `decision_id`
- `ASYNC_AWAIT`
- `SYNC_BLOCKING`

Requirements:

- [ ] Strategies shall not directly create official fills, deals, journal events, or reports.
- [ ] The module shall support stateful event strategies.
- [ ] Event strategies shall respond to initialization, bar-open, tick, and trade-transaction events through controlled interfaces.
- [ ] `INTRABAR_EVENT` strategies may use current tick data only through approved event interfaces.
- [ ] Event strategies shall support `FILL_UPDATE` or `PARTIAL_FILL` events to react to incomplete executions through approved read-only execution-state interfaces.
- [ ] Strategy-local state updates shall be atomic per decision event or shall fail with a deterministic rollback diagnostic.
- [ ] Read-only external state supplied to a strategy shall be an immutable snapshot or shall carry a documented consistency model preventing races with concurrent simulation, risk, portfolio, or data updates.
- [ ] Optional read-only simulation state for event strategies.
- [ ] Strategy risk profiles shall declare correlation assumptions during stress events.
- [ ] Every `TradeIntent` shall include a `decision_id` linking it to the strategy decision event that created it.
- [ ] Strategy metrics shall include intents emitted, intents suppressed, no-signal decisions, rejected decisions, invalid data events, lookahead detections, configuration validation failures, state checkpoint size, and per-event decision latency.
- [ ] Strategies shall not perform unbounded loops, unbounded recursion, unbounded memory growth, or unbounded history scans during event execution.
- [ ] Event strategies shall be reentrant or explicitly marked single-threaded.
- [ ] Simultaneous events shall be processed using a stable deterministic ordering policy.
- [ ] Wash trade prevention rules shall be declared.
- [ ] Strategies shall declare behavior during `AUCTION_PHASE`, `TRADING_HALT`, `CROSSING_SESSION`, and `BROKEN_MARKET` microstructure events.
- [ ] Event strategies shall implement a standard lifecycle interface where applicable.
- [ ] The standard event strategy lifecycle interface shall include hooks such as `on_init`, `on_start`, `on_bar`, `on_tick`, `on_fill_update`, `on_partial_fill`, `on_order_update`, `on_timer`, `on_error`, `on_checkpoint`, `on_restore`, and `on_stop`.
- [ ] Strategy execution shall define measurable latency, memory, checkpoint-size, diagnostic-payload-size, event-queue, timeout, and retry-exhaustion limits per supported environment before implementation acceptance.
- [ ] Strategy execution shall define deterministic backpressure behavior when event volume exceeds configured capacity.
- [ ] `ASYNC_AWAIT` strategies shall define an approved async compatibility contract and shall not block the event loop.
- [ ] `SYNC_BLOCKING` strategies shall define maximum call duration and isolation expectations before being used in shared event loops.
- [ ] No file-specific non-functional requirements defined.
- [ ] Simultaneous events for a single strategy instance shall be processed in a stable documented order, such as timestamp, event type priority, then deterministic sequence number.
- [ ] Strategy tests shall cover stateful event strategies.
- [ ] Strategy tests shall include stress tests for large histories, many symbols, dense tick streams, and high-frequency event dispatch.
- [ ] Strategy tests shall include chaos engineering scenarios, including simulated data-feed disconnections, sudden latency spikes, and out-of-order message injection during event processing.
- [ ] Strategy tests shall verify memory leak detection over extended event-loop iterations and assert stable memory usage within approved thresholds.
- [ ] Boundary tests shall verify strategies cannot create fills, deals, official orders, reports, or journal events directly.
- [ ] Concurrency tests shall verify read-only state snapshot isolation and stable event ordering for simultaneous events.
- [ ] A strategy shall not execute in an environment higher than its approved lifecycle status.
- [ ] `STRATEGY_LIFECYCLE_NOT_APPROVED`

#### `app/services/strategies/sandbox.py`

Functions/classes:

- `STRATEGY_ENVIRONMENT_NOT_PERMITTED`

Requirements:

- [ ] The strategy input path shall accept only registered strategy identifiers, validated strategy configuration schemas, or code explicitly vetted and sandboxed by the orchestration layer.
- [ ] Code-based strategy execution shall remain disabled until sandbox policy, approval workflow, and prohibited-operation lists are approved.
- [ ] Sandboxed code-based strategy execution, if enabled later, shall require `simulation.admin` approval, strategy owner approval, sandbox profile id, vetting artifact hash, allowed capability list, audit record, and approval expiry.
- [ ] Sandbox policy shall define allowed imports, denied imports, filesystem access, network access, subprocess access, environment-variable access, timeouts, memory limits, and prohibited operations.
- [ ] Strategy execution shall occur only through registered strategies, validated schemas, or explicitly sandboxed and vetted orchestration paths.
- [ ] Sandbox and vetting metadata only when code-based strategy execution is explicitly permitted.
- [ ] Any attempt by a strategy to read environment variables not explicitly allowlisted in the sandbox profile shall emit `STRATEGY_ENVIRONMENT_NOT_PERMITTED`.
- [ ] Documentation shall describe sandbox and vetting requirements if code-based strategy execution is ever enabled.
- [ ] No file-specific non-functional requirements defined.
- [ ] Missing sandbox or vetting metadata for a code-based strategy path shall fail before execution.
- [ ] Sandbox approval expiry shall cause code-based strategy execution to fail before execution.
- [ ] `STRATEGY_SANDBOX_REQUIRED`


### Hardening Amendments

#### Canonical signal boundary

Requirements:

- [ ] Adopt the Phase 1.5 `StrategyInput` and `StrategySignal` contracts for all strategy service inputs and outputs.
- [ ] Enforce the canonical flow `StrategyInput -> StrategySignal -> RiskDecision -> OrderIntent -> TradeRequest`.
- [ ] Prohibit strategies from returning broker-specific order requests, raw broker payloads, execution commands, or live mutation instructions.
- [ ] Add strategy version hash, parameter hash, input dataset hash, signal validity window, optional confidence score, and evidence references to every emitted signal.
- [ ] Reject expired, malformed, unsupported, or insufficient-evidence signals before they reach Risk Governance.
- [ ] Add tests proving strategy outputs can be consumed by Risk without broker-specific adapter knowledge.

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

feat(strategy-service): implement Strategy base class, protocol, and TrendFollowing



- Implement `BaseStrategy` and class-based strategy registration hooks

- Build thread-safe global Strategy Registry with version constraints

- Implement `TrendFollowingStrategy` with crossover and trend filter logic

- Support vectorized signal processing and event-driven update lifecycle hooks

```

- [ ] Each public capability shall define precise side effects, mutation permissions, idempotency behavior, concurrency assumptions, retry behavior, and redaction behavior.
- [ ] Strategy imports shall be side-effect safe and shall not perform broker calls, network access, filesystem writes, subprocess execution, environment mutation, or decision-time clock/randomness reads.
- [ ] Security tests shall verify strategy imports perform no broker calls, network calls, filesystem writes, subprocess calls, environment mutation, or secret reads.
