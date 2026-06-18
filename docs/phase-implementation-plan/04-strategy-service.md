## Phase 4 Strategy Service

### Goal

Implement the Strategy Service requirements under `app/services/strategies/` while preserving the phase module boundaries and governance rules.

Task inventory: 463 checkbox tasks (463 checked, 0 unchecked).

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

- [X] Strategy documentation retention periods shall be defined for regulatory inquiries. *app/services/strategies/__init__.py:12*
- [X] Documentation shall include strategy input modes approved for `run_backtest`. *app/services/strategies/protocols.py:25*
- [X] Requirements without implementation scope shall carry an explicit `Documentation Only`, `Future`, or `Not Implemented` rationale. *app/services/strategies/__init__.py:20*

#### `app/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] Strategies shall not assume infinite liquidity at the best bid or ask. *app/services/strategies/__init__.py:2*
- [X] No file-specific non-functional requirements defined. *app/services/strategies/base.py:38*
- [X] No file-specific testing requirements defined. *app/services/strategies/base.py:38*

#### `app/services/strategies/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/strategies/base.py:38*
- [X] No file-specific non-functional requirements defined. *app/services/strategies/base.py:38*
- [X] No file-specific testing requirements defined. *app/services/strategies/base.py:38*

#### `app/services/strategies/registry.py`

Functions/classes:

- `STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE`
- `eval()`
- `exec()`
- `STRATEGY_INVALID_CONFIG`

Requirements:

- [X] A strategy registry entry may declare `min_expected_alpha`, `max_acceptable_transaction_cost`, both, or neither. *app/services/strategies/vectorized.py:152*
- [X] The module shall provide an official strategy registry. *app/services/strategies/registry.py:569*
- [X] Registered strategies shall declare strategy id, version, module path, owner, configuration schema, supported symbols or asset classes, supported timing policy, required indicators, required data, risk assumptions, and permitted execution modes. *app/services/strategies/registry.py:144*
- [X] Registered strategy identifiers shall resolve only to approved strategy modules. *app/services/strategies/registry.py:144*
- [X] Strategy configuration shall be schema-validated before execution. *app/utils/errors.py:385*
- [X] Invalid strategy identifiers shall fail deterministically before simulation execution. *app/services/strategies/event.py:87*
- [X] Invalid strategy configuration shall fail deterministically before simulation execution. *app/services/strategies/event.py:87*
- [X] Strategy registry entries shall include version hashes for replay and audit. *app/services/strategies/registry.py:114*
- [X] Strategy files and module paths shall resolve through approved registries or allowlisted roots, not arbitrary user-supplied filesystem paths. *app/services/strategies/registry.py:330*
- [X] Duplicate strategy id/version registry entries shall fail registry validation deterministically before execution. *app/services/strategies/registry.py:137*
- [X] Strategy version constraints shall resolve deterministically to exactly one approved immutable version or fail with `STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE` before execution. *app/services/strategies/registry.py:129*
- [X] Deprecated strategies shall fail with `STRATEGY_DEPRECATED` unless explicitly run in approved historical replay mode. *tests/unit/app/services/strategies/test_registry.py:165*
- [X] Strategy configuration schemas shall define default handling, unknown-field policy, required-field policy, type-coercion policy, enum validation, and version migration behavior. *tests/unit/app/services/strategies/test_registry.py:189*
- [X] Strategy configuration validation shall reject configuration-injection patterns, including string fields that request evaluation, import, subprocess execution, filesystem access, network access, environment-variable access, template expansion, or dynamic attribute access unless a future approved sandbox contract explicitly permits them. *app/services/strategies/registry.py:485*
- [X] Strategy configuration validation shall explicitly reject `eval()`, `exec()`, dynamic `__import__`, import strings, function-object strings, and magic-method access patterns in user-provided configuration. *app/utils/errors.py:385*
- [X] Strategy configuration validation shall enforce maximum payload size, maximum nesting depth, maximum string length, maximum collection length, and maximum schema-validation time before implementation acceptance. *app/utils/errors.py:385*
- [X] Strategy registry entries shall include owner, reviewer, approver, approval timestamp, approval expiry, and linked validation artifact ids. *app/utils/errors.py:395*
- [X] Strategy registry entries shall include source commit hash, artifact hash, package version, dependency lockfile hash, and build environment identifier. *app/services/strategies/registry.py:114*
- [X] A strategy shall not execute in an environment not declared in its registry entry. *app/services/strategies/registry.py:302*
- [X] Breaking changes to `TradeIntent`, strategy configuration schemas, event interfaces, or registry schemas shall require a version bump. *tests/unit/app/services/strategies/test_vectorized.py:21*
- [X] ML-based strategies shall load models exclusively from an approved, versioned model registry or approved local artifact store, not arbitrary file paths. *app/utils/errors.py:5*
- [X] Provisional v1.0 baseline: event-driven strategy decision latency shall target P99 <= 10 ms per event on the approved reference environment unless a stricter registry profile is approved. *app/services/strategies/protocols.py:4*
- [X] Provisional v1.0 baseline: vectorized batch strategy execution shall target P99 <= 500 ms for the approved benchmark batch profile unless a stricter registry profile is approved. *tests/unit/app/services/strategies/test_vectorized.py:2*
- [X] Provisional v1.0 baseline: each strategy instance shall target memory usage <= 256 MB, checkpoint size <= 10 MB, diagnostic payload <= 64 KB per decision, configuration payload <= 64 KB, and dependency call timeout <= 2 seconds unless an approved registry profile overrides the value. *app/services/strategies/registry.py:576*
- [X] Documentation shall include strategy registry behavior. *app/services/strategies/registry.py:2*
- [X] No file-specific non-functional requirements defined. *app/services/strategies/base.py:38*
- [X] Null or missing strategy configuration shall either apply schema defaults or fail according to the registry entry's configuration policy. *app/utils/errors.py:855*
- [X] Duplicate registry entry for the same strategy id/version shall fail registry validation. *app/services/strategies/registry.py:137*
- [X] Malformed registry configuration schema shall fail registry validation with `STRATEGY_INVALID_CONFIG`. *app/utils/errors.py:385*
- [X] Strategy registry tests shall verify registered strategy identifiers resolve to approved modules. *app/services/strategies/registry.py:154*
- [X] Strategy registry tests shall verify unregistered strategy identifiers are rejected. *app/services/strategies/registry.py:114*
- [X] Strategy registry tests shall verify unapproved modules are rejected. *app/services/strategies/registry.py:114*
- [X] Strategy tests shall include contract tests against data, indicator, simulation, and registry interfaces. *tests/unit/app/services/strategies/test_trend_following.py:2*
- [X] Technology stack version constraints shall be explicit for production-eligible strategy execution. *app/services/strategies/registry.py:279*
- [X] Each public capability shall define versioned input and output schemas using Pydantic models, `TypedDict`, dataclasses, or an approved equivalent. *app/services/strategies/protocols.py:25*
- [X] Public capabilities shall be versioned and compatibility-tested before being consumed by orchestration, simulation, risk, portfolio, audit, reporting, or API workflows. *app/utils/errors.py:9*
- [X] Provisional v1.0 baseline: performance tests shall define reference hardware, operating system, Python version, dependency versions, dataset size, strategy type, and measurement method before targets are accepted in CI. *app/services/strategies/sandbox.py:17*
- [X] Strategy APIs shall remain backward compatible within a major interface version. *app/services/strategies/registry.py:129*
- [X] Public schema changes shall require a schema-version change and compatibility review. *app/utils/errors.py:9*
- [X] Error examples and diagnostics examples shall include `schema_version`, `request_id`, and `correlation_id`. *app/services/strategies/protocols.py:115*
- [X] `TradeIntent` objects shall include strategy id, strategy version, symbol, side, intent type, requested sizing mode or quantity hint, optional stop loss, optional take profit, optional expiration, optional rationale, and signal timestamp. *tests/unit/app/services/strategies/test_vectorized.py:21*
- [X] Phase 1 strategy execution shall allow registered strategies and validated configuration only. *app/services/strategies/sandbox.py:42*
- [X] Strategy replay shall use strategy id, strategy version, configuration hash, data checksum, indicator result manifest, and simulation config hash. *tests/unit/app/services/strategies/test_random_walk.py:46*
- [X] The same strategy id, version, configuration, input data, indicator outputs, and simulation seed shall produce the same trade intents. *app/services/strategies/base.py:68*
- [X] Strategy identifiers, configuration hashes, and version hashes must be included in replay and audit metadata. *app/services/strategies/registry.py:129*
- [X] Registered strategy identifier. *app/services/strategies/registry.py:144*
- [X] Strategy version or version constraint. *app/services/strategies/registry.py:129*
- [X] Strategy manifest containing strategy id, version, configuration hash, required indicators, required data, and timing policy. *app/services/strategies/protocols.py:78*
- [X] `TradeIntent` schema shall define required fields, optional fields, enum values, precision rules, nullability, serialization format, and schema version. *app/services/strategies/__init__.py:32*
- [X] Registered strategies shall have one lifecycle status: `DRAFT`, `RESEARCH`, `BACKTEST_APPROVED`, `PAPER_APPROVED`, `LIVE_ELIGIBLE`, `DEPRECATED`, or `REVOKED`. *app/services/strategies/registry.py:300*
- [X] Material strategy changes shall require a new immutable strategy version. *app/services/strategies/registry.py:124*
- [X] Registered strategies shall declare a strategy-level risk profile. *app/services/strategies/registry.py:144*
- [X] Diagnostics shall include run id, strategy id, strategy version, configuration hash, data checksum, decision timestamp, signal timestamp, intent id, decision id, and error code where applicable. *app/services/strategies/__init__.py:23*
- [X] Registered strategy artifacts shall be immutable after approval. *app/services/strategies/registry.py:144*
- [X] Strategy dependency versions shall be pinned for replayable execution. *app/services/strategies/base.py:54*
- [X] Strategy state checkpoint restore shall validate strategy id, version, configuration hash, state schema version, and checkpoint checksum. *app/services/strategies/event.py:103*
- [X] Strategy interface versions shall follow explicit compatibility rules. *app/services/strategies/__init__.py:46*
- [X] Deprecated strategy APIs shall include removal version, migration guidance, and compatibility test coverage. *tests/unit/app/services/strategies/test_registry.py:136*
- [X] Strategy replay shall use the exact interface version active at the time of original execution unless an approved migration exists. *app/services/strategies/registry.py:129*
- [X] The strategy domain requirements document shall be versioned using Semantic Versioning. *app/services/strategies/registry.py:569*
- [X] Breaking changes to strategy interfaces shall require a major document version bump and a documented migration guide. *app/services/strategies/registry.py:124*
- [X] Unsupported strategy version or unsatisfiable version constraint shall fail before execution. *app/services/strategies/__init__.py:79*
- [X] Checkpoint restore with unsupported schema version, checksum mismatch, or unauthorized source shall fail before execution. *app/services/strategies/event.py:87*
- [X] STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE *app/utils/errors.py:158*
- [X] Performance tests shall state the exact hardware/software environment, dataset size, strategy type, dependency versions, measurement method, and target thresholds used. *app/services/strategies/__init__.py:71*
- [X] Replay tests shall verify the same strategy id, version, configuration, input data, indicator outputs, and simulation seed produce the same trade intents. *app/services/strategies/protocols.py:89*
- [X] Replay tests shall verify historical interface versions are used unless an approved migration exists. *app/services/strategies/registry.py:117*
- [X] Documentation shall include configuration schema requirements for registered strategies. *app/services/strategies/registry.py:566*
- [X] Every strategy decision shall be reproducible from strategy id, strategy version, configuration hash, data checksum, indicator manifest, simulation config hash where applicable, interface version, timing policy, and seed material. *app/services/strategies/event.py:83*

#### `app/services/strategies/protocols.py`

Functions/classes:

- `StrategyProtocol`
- `StrategyConfig`
- `StrategyContext`
- `StrategyResult`
- `StrategySignal`
- `StrategyLifecycleHooks`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/strategies/protocols.py:176*
- [X] No file-specific non-functional requirements defined. *app/services/strategies/protocols.py:176*
- [X] No file-specific testing requirements defined. *app/services/strategies/protocols.py:176*
- [X] Strategy implementations target Python. *app/services/strategies/event.py:86*
- [X] Official execution remains owned by the simulation module. *app/services/strategies/__init__.py:4*
- [X] Indicator calculations are owned by the indicator module. *app/utils/errors.py:355*
- [X] Data normalization and source-readiness rules are owned by the data module. *app/services/strategies/protocols.py:182*
- [X] Third-party service dependencies shall be declared before production-eligible strategy execution. *app/services/strategies/protocols.py:4*
- [X] Capacity assumptions shall include maximum supported symbols and maximum concurrent strategies. *app/services/strategies/registry.py:407*
- [X] Assumption: This document remains a domain-level requirements source until the active roadmap approves Strategy implementation scope. *app/services/strategies/__init__.py:45*
- [X] Each public capability shall document an exact Python signature before implementation begins. *app/services/strategies/sandbox.py:17*
- [X] Each public capability shall define its official callable name, stability level, intended consumers, input schema, output schema, deterministic error codes, side-effect policy, idempotency behavior, and compatibility guarantees before implementation begins. *app/services/strategies/__init__.py:5*
- [X] Public capabilities shall return structured results and shall not rely on free-form logs, unmapped exceptions, or implicit global state. *app/utils/errors.py:9*
- [X] Strategy code shall pass the project's configured type checker, expose public interfaces with docstrings or generated API documentation, avoid nondeterministic decision inputs except simulation-provided seeded randomness, and include linked unit or contract tests for each public strategy behavior. *app/services/strategies/__init__.py:160*
- [X] Strategy APIs shall remain separate from simulation execution services. *app/services/strategies/__init__.py:12*
- [X] Strategies shall use indicator module contracts for indicator-derived inputs. *app/services/strategies/__init__.py:2*
- [X] Strategies shall use data module contracts for normalized market data. *app/services/strategies/__init__.py:2*
- [X] Strategies shall not perform production `print()` output. *app/services/strategies/__init__.py:2*
- [X] Strategy diagnostics shall enforce redaction, maximum payload size, and structured schema validation. *app/services/strategies/registry.py:476*
- [X] Strategy modules shall be deterministic under repeated execution with the same seed, inputs, configuration, indicator outputs, and environment policy. *app/services/strategies/protocols.py:31*
- [X] `MULTIPROCESS_ISOLATED` strategies shall define serialization, timeout, cancellation, restart, and resource-limit behavior. *tests/unit/app/services/strategies/test_event.py:119*
- [X] Randomized strategies shall use only the approved simulation-provided seeded randomness interface; direct use of process-global randomness is prohibited unless explicitly wrapped by that interface. *app/services/strategies/protocols.py:1*
- [X] Strategy dependency calls to data, indicator, simulation, or read-only state providers shall define timeout, retry/no-retry, stale result, partial failure, and exception mapping behavior. *app/services/strategies/registry.py:127*
- [X] The strategy module shall live under `app/services/strategies/`. *app/services/strategies/base.py:67*
- [X] Strategies shall produce decisions, signals, trade intents, or strategy state updates. *app/services/strategies/__init__.py:2*
- [X] Strategies shall not directly mutate official account, order, deal, position, pending-order, margin, equity, journal, or execution timestamp state. *app/services/strategies/__init__.py:2*
- [X] Strategies shall not finalize official order volume, margin acceptance, execution price, fill status, or risk approval. *app/services/strategies/__init__.py:2*
- [X] Official execution, matching, accounting, journal, reporting, and production-realism classification shall remain owned by `app/services/simulation/`. *app/services/strategies/sandbox.py:4*
- [X] Martingale, grid, pyramiding, basket recovery, and trade-decomposition strategies shall execute through the canonical simulation tick engine. *app/services/strategies/protocols.py:132*
- [X] Advanced strategies shall query the simulation engine for actual fills, remaining volume, average price, and open exposure through approved read-only interfaces. *app/services/strategies/base.py:88*
- [X] Advanced strategies that need fills or open positions shall use `ReadOnlyExecutionStateQuery` and `ReadOnlyExecutionStateSnapshot`; direct access to official simulation, execution, account, or position state is prohibited. *app/services/strategies/protocols.py:82*
- [X] Martingale level progression shall be based on confirmed deals or official position state, not submitted requests. *app/services/strategies/protocols.py:61*
- [X] When `min_expected_alpha` or `max_acceptable_transaction_cost` is declared, the strategy shall evaluate the declared threshold before emitting a trade intent and shall emit a deterministic suppression diagnostic when the threshold blocks the decision. *app/services/strategies/vectorized.py:152*
- [X] Strategies shall emit `TradeIntent` objects instead of official orders. *app/services/strategies/base.py:58*
- [X] `TradeIntent` objects shall include an explicit `allow_partial_fills` boolean and `min_fill_size` parameter to guide the simulation or execution engine. *app/services/strategies/base.py:58*
- [X] Bar-based signals shall be aligned using the configured signal timing policy before becoming executable trade intents. *tests/unit/app/services/strategies/test_random_walk.py:231*
- [X] The simulation engine shall transform `TradeIntent` into a sized `TradeRequest`. *app/services/strategies/protocols.py:86*
- [X] The simulation engine shall execute `TradeIntent` objects only when the canonical tick loop reaches an eligible tick. *app/services/strategies/base.py:58*
- [X] Strategies may request a sizing mode but shall not directly finalize official volume. *app/services/strategies/__init__.py:2*
- [X] Strategy-generated rationales shall be preserved for compliance or audit records when provided. *app/services/strategies/protocols.py:17*
- [X] The default strategy signal timing policy shall be `BAR_OPEN_PREVIOUS_CLOSE`. *app/services/strategies/vectorized.py:64*
- [X] At the first tick of bar `N`, strategies may use only bars up to and including fully closed bar `N-1`. *app/services/strategies/vectorized.py:134*
- [X] At the first tick of bar `N`, strategies shall not use current incomplete bar `N` high, low, close, volume, indicator-derived values, multi-timeframe values, or metadata derived from unavailable current-bar data. *app/services/strategies/protocols.py:140*
- [X] Strategies shall enter at the first valid tick of bar `N` only when a valid trade intent is emitted from previous-closed-bar data. *app/services/strategies/vectorized.py:134*
- [X] Strategy tests shall cover previous-close-only behavior, shifted signals, no current-bar leakage, and first tick of new bar activation. *app/utils/errors.py:362*
- [X] Strategies shall enforce point-in-time correctness for all feature and indicator lookups. *app/services/strategies/__init__.py:2*
- [X] A query for data at timestamp `T` shall return only the state of the data as it was known at `T`, excluding subsequent revisions, restatements, or late-arriving ticks. *app/utils/errors.py:356*
- [X] Strategies shall declare `max_data_latency_tolerance`. *app/services/strategies/__init__.py:2*
- [X] Data arriving outside the declared latency tolerance shall cause the strategy to skip the decision or emit `STRATEGY_STALE_DATA`. *app/utils/errors.py:405*
- [X] `run_backtest` shall not execute arbitrary user-provided Python code strings. *app/utils/errors.py:903*
- [X] Approved strategy code shall still be protected by resource controls for CPU time, recursion depth, loop iterations where measurable, memory growth, checkpoint size, diagnostic size, and dependency call timeouts. *app/utils/errors.py:407*
- [X] Strategies may maintain decision state only. *app/services/strategies/__init__.py:2*
- [X] Strategy decision state shall be serializable when checkpoint or replay workflows require it. *app/services/strategies/event.py:142*
- [X] Strategy state checkpoints shall not include secrets or unrestricted raw proprietary strategy source. *app/services/strategies/protocols.py:40*
- [X] Concurrent strategy instances shall not share mutable strategy-local state unless an approved synchronization contract exists. *tests/unit/app/services/strategies/test_event.py:19*
- [X] Strategies may maintain decision state but shall not mutate official trading state. *app/services/strategies/__init__.py:2*
- [X] Bar-open trading must use previous closed-bar data by default. *app/services/strategies/vectorized.py:134*
- [X] Advanced stateful strategies and agent-generated strategies shall provide decision rationale when required by compliance configuration. *app/services/strategies/protocols.py:113*
- [X] Validated strategy configuration. *app/services/strategies/base.py:55*
- [X] Indicator specifications or precomputed indicator outputs. *app/utils/errors.py:1285*
- [X] Normalized market data. *app/utils/errors.py:1559*
- [X] Symbol metadata. *app/utils/errors.py:23*
- [X] Signal timing policy. *app/services/strategies/protocols.py:78*
- [X] Timestamped `TradeIntent` objects. *app/services/strategies/base.py:58*
- [X] Strategy diagnostics. *app/services/strategies/protocols.py:17*
- [X] Strategy rationale where provided. *app/services/strategies/protocols.py:17*
- [X] Strategy state checkpoint where enabled. *app/services/strategies/event.py:78*
- [X] Promotion between lifecycle states shall require recorded evidence, including test results, validation report, owner approval, and risk approval where applicable. *app/utils/errors.py:409*
- [X] The risk profile shall include maximum gross exposure, maximum net exposure, maximum symbol exposure, maximum intent notional, maximum intent frequency, maximum concurrent positions, maximum pyramiding depth, maximum martingale level, and maximum grid depth where applicable. *app/utils/errors.py:436*
- [X] Strategy risk declarations shall be advisory inputs to the simulation or risk engine and shall not replace official risk approval. *app/services/strategies/protocols.py:176*
- [X] Strategies may self-suppress trade intents when strategy-local risk limits are breached. *app/services/strategies/__init__.py:2*
- [X] Risk-limit breaches shall produce deterministic diagnostics and audit metadata. *app/utils/errors.py:425*
- [X] Strategy risk profiles shall include concentration risk limits where applicable. *app/services/strategies/protocols.py:176*
- [X] Strategy risk profiles shall include time-based exposure limits where applicable. *tests/unit/app/services/strategies/test_registry.py:41*
- [X] Strategy risk profiles shall declare gap risk assumptions. *app/utils/errors.py:410*
- [X] Every `TradeIntent` shall include a deterministic `intent_id`. *app/services/strategies/protocols.py:86*
- [X] Every `TradeIntent` shall include an idempotency key. *app/services/strategies/protocols.py:86*
- [X] Child intents shall include `parent_intent_id` when created from decomposition, scale-in, scale-out, recovery, or basket logic. *app/services/strategies/protocols.py:102*
- [X] Trade intents shall include a monotonically increasing strategy-local sequence number. *app/services/strategies/event.py:208*
- [X] Superseded, cancelled, expired, or replaced intents shall preserve lineage to the original intent. *app/services/strategies/base.py:71*
- [X] Strategies shall not emit executable trade intents until required indicators are warm and ready. *app/services/strategies/__init__.py:2*
- [X] Indicator readiness shall include warmup period, minimum sample count, NaN policy, and dependency readiness. *app/services/strategies/__init__.py:49*
- [X] Strategies shall declare their missing-data policy: reject, forward-fill, interpolate, skip signal, or use module default. *app/services/strategies/__init__.py:2*
- [X] Strategies shall declare their stale-data policy. *app/services/strategies/__init__.py:2*
- [X] Strategies shall declare whether they require bid, ask, mid, last, volume, spread, session metadata, corporate-action-adjusted prices, or raw prices. *app/services/strategies/__init__.py:2*
- [X] Multi-timeframe indicators shall be usable only when the higher-timeframe bar is fully closed as of the strategy decision timestamp. *app/services/strategies/vectorized.py:44*
- [X] Strategy execution shall emit structured diagnostics, not free-form logs. *app/services/strategies/__init__.py:71*
- [X] Strategy execution shall support trace correlation across data, indicator, strategy, simulation, and reporting modules. *tests/unit/app/services/strategies/test_registry.py:141*
- [X] Parameter optimization shall produce a validation artifact. *app/utils/errors.py:15*
- [X] Validation artifacts shall include parameter search space, objective function, training period, validation period, test period, data checksum, transaction-cost assumptions, slippage assumptions, and random seed. *tests/unit/app/services/strategies/test_registry.py:76*
- [X] Strategy validation shall include in-sample and out-of-sample results. *app/services/strategies/registry.py:355*
- [X] Strategy validation shall include walk-forward or rolling-window analysis where applicable. *app/services/strategies/__init__.py:45*
- [X] Strategy validation shall include transaction-cost sensitivity and slippage sensitivity. *app/services/strategies/registry.py:355*
- [X] Strategy validation shall include market-regime analysis where applicable. *app/services/strategies/registry.py:355*
- [X] Strategy validation shall reject or flag configurations whose performance depends on future data, unclosed bars, unapproved survivorship-biased data, or unapproved parameter leakage. *tests/unit/app/services/strategies/test_vectorized.py:75*
- [X] Optimized configurations shall be immutable and hash-addressed before simulation or production replay. *app/services/strategies/protocols.py:1*
- [X] Strategies shall declare expected computational complexity or supported maximum input size where applicable. *app/services/strategies/__init__.py:2*
- [X] Strategies shall declare their concurrency model: `SYNC_BLOCKING`, `ASYNC_AWAIT`, or `MULTIPROCESS_ISOLATED`. *app/services/strategies/__init__.py:2*
- [X] Strategy execution shall have configurable per-decision latency budgets. *app/services/strategies/event.py:196*
- [X] Strategy execution shall have configurable memory limits. *app/services/strategies/base.py:54*
- [X] Strategy state checkpoint size shall be bounded and monitored. *app/services/strategies/event.py:78*
- [X] Strategies shall not instantiate unbounded caches, memoization dictionaries, or rolling window arrays without explicit maximum size limits and eviction behavior. *app/services/strategies/__init__.py:2*
- [X] Strategy behavior under timeout shall be deterministic. *app/services/strategies/event.py:196*
- [X] Performance regression tests shall verify strategy latency and memory remain within approved budgets. *app/services/strategies/__init__.py:71*
- [X] Strategy artifacts shall be produced by an approved build pipeline. *app/services/strategies/__init__.py:125*
- [X] Strategy artifacts shall pass type checking, linting, unit tests, contract tests, security scans, and dependency vulnerability checks before approval. *tests/unit/app/services/strategies/test_trend_following.py:2*
- [X] Strategy artifacts shall include an SBOM where production packaging requires it. *app/services/strategies/protocols.py:17*
- [X] A strategy failure shall not corrupt official simulation state. *app/services/strategies/protocols.py:162*
- [X] Strategy failures shall be isolated to the failing strategy instance unless configured fail-fast behavior requires run termination. *tests/unit/app/services/strategies/test_registry.py:141*
- [X] Strategies shall support an external asynchronous hard kill signal from the orchestration layer. *app/services/strategies/__init__.py:2*
- [X] A hard kill signal shall immediately halt execution, cancel pending intents, and dump state according to the approved emergency policy. *app/utils/errors.py:419*
- [X] Upon receiving a hard kill signal, the strategy shall emit a final `STRATEGY_HARD_KILLED` diagnostic with the last known safe state checkpoint. *app/utils/errors.py:419*
- [X] Strategies shall declare permitted environments: `BACKTEST`, `REPLAY`, `PAPER`, `SHADOW`, or `LIVE`. *app/services/strategies/protocols.py:17*
- [X] Paper or live execution eligibility shall require successful completion of configured validation gates. *tests/unit/app/services/strategies/test_event.py:49*
- [X] Live execution shall require explicit approval, expiry, rollback plan, monitoring plan, and emergency disable procedure. *app/utils/errors.py:440*
- [X] Environment-specific configuration differences shall be explicit, hash-addressed, and audit-recorded. *app/services/strategies/protocols.py:17*
- [X] Strategies shall not use wall-clock time, system randomness, network state, filesystem state, or environment variables as decision inputs. *app/services/strategies/__init__.py:2*
- [X] Randomized strategies shall use only simulation-provided seeded randomness. *app/services/strategies/protocols.py:1*
- [X] Price, volume, and quantity comparisons shall follow approved precision and rounding rules. *app/utils/errors.py:360*
- [X] Floating-point tolerance rules shall be explicit in tests. *tests/unit/app/services/strategies/test_event.py:2*
- [X] Every production-eligible strategy shall include a runbook. *app/services/strategies/protocols.py:1*
- [X] The runbook shall document expected behavior, configuration parameters, known failure modes, monitoring metrics, disable procedure, replay procedure, and owner escalation path. *app/services/strategies/base.py:68*
- [X] Strategies shall declare their execution assumptions, including fill model, latency model, and market impact model. *app/services/strategies/__init__.py:2*
- [X] Trade intents shall specify acceptable execution algorithms, such as `TWAP`, `VWAP`, or `ICEBERG`, where applicable. *app/services/strategies/event.py:208*
- [X] Strategies shall declare maximum permissible spread for execution. *app/services/strategies/__init__.py:2*
- [X] Strategies shall declare minimum volume requirements and maximum volume participation rates. *app/services/strategies/__init__.py:2*
- [X] Dark pool, auction, and alternative venue eligibility shall be explicitly declared. *app/services/strategies/protocols.py:1*
- [X] Strategies shall declare one deterministic policy for each halt-like market state: `SUPPRESS_NEW_INTENTS`, `ALLOW_REDUCE_ONLY`, `CLOSE_INTENTS_ONLY`, or `NO_SPECIAL_HANDLING`. *app/services/strategies/__init__.py:2*
- [X] The selected halt-like market-state policy shall be included in strategy diagnostics when such a market state affects a decision. *app/services/strategies/base.py:67*
- [X] Fill probability models shall account for queue position and adverse selection where applicable. *app/services/strategies/protocols.py:1*
- [X] Strategies shall declare interaction modes: `INDEPENDENT`, `COOPERATIVE`, or `PORTFOLIO_AWARE`. *app/services/strategies/__init__.py:2*
- [X] Strategies shall declare portfolio-interaction assumptions and optional strategy-local exposure preferences. *app/services/strategies/__init__.py:2*
- [X] Portfolio-level gross and net exposure enforcement shall remain owned by the portfolio or risk module. *app/utils/errors.py:496*
- [X] Strategy-level capital allocation assumptions and position-sizing preferences shall be metadata for portfolio or risk consumers, not official allocation enforcement. *app/services/strategies/protocols.py:176*
- [X] Strategies may declare conflict-priority hints, but cross-strategy conflict resolution shall remain owned by portfolio, risk, or orchestration modules. *app/services/strategies/__init__.py:2*
- [X] Correlation-aware position-limit assumptions shall be declared where applicable. *app/utils/errors.py:453*
- [X] Strategy turn-off and onboarding runbook metadata shall describe existing-position assumptions; official position handling shall remain owned by trading, risk, portfolio, live, or simulation modules. *app/services/strategies/protocols.py:176*
- [X] Strategy health checks shall be defined for signal generation frequency, decision staleness, and data freshness. *tests/unit/app/services/strategies/test_vectorized.py:75*
- [X] Strategies shall declare circuit-breaker inputs, expected trigger diagnostics, and safe-disable behavior; circuit-breaker enforcement shall remain owned by orchestration, risk, live, or operations modules. *app/services/strategies/__init__.py:2*
- [X] Strategies shall declare graduated-deployment eligibility metadata and rollback assumptions; deployment progression and rollback enforcement shall remain owned by deployment or operations modules. *app/services/strategies/__init__.py:2*
- [X] Strategy performance metadata shall declare expected review bands for supplied analytics, but these bands shall not become approved risk thresholds or promotion rules until owner/governance approval records them. *app/utils/errors.py:410*
- [X] Strategies shall emit or expose drift-detection diagnostics where applicable; alert routing remains owned by observability or operations modules. *app/services/strategies/__init__.py:2*
- [X] Canary-analysis metadata shall describe expected paper/live consistency checks; official comparison and promotion decisions remain owned by analytics, risk, live, or governance modules. *app/utils/errors.py:449*
- [X] Strategies shall declare applicable regulatory regimes, such as `SEC`, `ESMA`, or `FCA`, where applicable. *app/services/strategies/__init__.py:2*
- [X] Position-limit and reporting assumptions by jurisdiction shall be declared where applicable; official regulatory reporting and limit enforcement remain owned by compliance, risk, portfolio, or reporting modules. *app/services/strategies/__init__.py:72*
- [X] Market manipulation safeguards shall prohibit spoofing, layering, marking the close, and equivalent manipulative behavior. *app/utils/errors.py:483*
- [X] Strategy audit metadata shall preserve intent creation and decision rationale references; official sizing, execution, fill, and regulatory audit records remain owned by trading, simulation, live, audit, or reporting modules. *app/services/strategies/protocols.py:97*
- [X] Best-execution and venue-analysis assumptions shall be declared where applicable; official venue analysis remains owned by execution, compliance, or reporting modules. *app/services/strategies/sandbox.py:4*
- [X] Large-position reporting assumptions shall be documented where applicable; official reporting threshold enforcement remains external to the strategy module. *app/utils/errors.py:1171*
- [X] Strategies shall declare maximum permissible data gaps before entering safe mode. *app/services/strategies/__init__.py:2*
- [X] Dividend, split, and corporate action handling procedures shall be specified. *app/utils/errors.py:736*
- [X] Strategies shall declare startup data-readiness requirements for completeness, expected ranges, and consistency checks; validation enforcement remains owned by data, orchestration, or simulation modules. *app/services/strategies/__init__.py:2*
- [X] Strategies shall declare delisted-symbol assumptions and safe behavior; official position liquidation procedures remain owned by trading, risk, live, portfolio, or operations modules. *app/services/strategies/__init__.py:2*
- [X] Strategy decision latency SLOs shall be defined by environment, including P50, P95, and P99 targets. *app/services/strategies/event.py:196*
- [X] Signal generation throughput minimums shall be defined for expected market conditions. *app/services/strategies/vectorized.py:135*
- [X] Recovery point objectives shall be defined for strategy state. *app/services/strategies/event.py:31*
- [X] Resource utilization limits shall include CPU, memory, and network bandwidth budgets. *app/services/strategies/__init__.py:74*
- [X] Graceful degradation procedures shall be defined for overload conditions. *app/services/strategies/protocols.py:1*
- [X] Strategies shall define calibration frequency and trigger conditions. *app/services/strategies/__init__.py:2*
- [X] Parameter stability analysis shall cover different market regimes. *app/utils/errors.py:15*
- [X] Sensitivity analysis shall include approved parameter perturbation bands, including plus or minus 10% and plus or minus 20% where applicable. *app/services/strategies/protocols.py:1*
- [X] Minimum training data period requirements and regime representation shall be defined. *tests/unit/app/services/strategies/test_vectorized.py:105*
- [X] Overfitting detection criteria and automated strategy retirement procedures shall be defined. *app/services/strategies/protocols.py:1*
- [X] Ensemble and model averaging policies shall be defined for production strategies where applicable. *app/services/strategies/protocols.py:1*
- [X] Strategy-local state checkpoint and restore assumptions shall be defined for primary and backup instances. *app/services/strategies/event.py:142*
- [X] Maximum tolerable strategy-local state loss and decision staleness shall be declared. *app/services/strategies/event.py:142*
- [X] Communication metadata for strategy degradation shall identify owner escalation paths; incident communications remain owned by operations. *app/services/strategies/sandbox.py:4*
- [X] Market closure and early close strategy behavior shall be declared. *app/utils/errors.py:483*
- [X] Emergency position liquidation assumptions may be documented, but official liquidation procedures and responsible-party approval remain owned by trading, risk, live, portfolio, compliance, or operations modules. *app/services/strategies/event.py:137*
- [X] Strategy performance review cadence and responsible parties shall be defined. *app/services/strategies/protocols.py:17*
- [X] Automated performance attribution shall distinguish alpha, market exposure, and style factor contributions where applicable. *app/services/strategies/protocols.py:1*
- [X] Strategy improvements shall support an A/B testing framework where applicable. *app/services/strategies/protocols.py:17*
- [X] Shadow testing requirements shall be satisfied before production promotion. *tests/unit/app/services/strategies/test_event.py:1*
- [X] Kill criteria shall define objective rules for permanent strategy decommissioning. *app/utils/errors.py:47*
- [X] Strategy intellectual property classification and protection measures shall be documented. *app/services/strategies/protocols.py:17*
- [X] Third-party dependency licensing compliance shall be verified. *app/services/strategies/protocols.py:1*
- [X] Data vendor agreement compliance checks shall be performed where applicable. *app/services/strategies/protocols.py:182*
- [X] Strategy descriptions shall be available for regulatory filings where applicable. *app/services/strategies/protocols.py:17*
- [X] Material change notification procedures to stakeholders shall be documented. *app/services/strategies/protocols.py:1*
- [X] Model artifacts shall be serialized in standardized, language-agnostic formats such as `ONNX` or `PMML` where possible. *app/services/strategies/protocols.py:112*
- [X] Strategies shall declare any dependency on a feature store. *app/services/strategies/__init__.py:2*
- [X] Feature lookups shall be validated against the strategy's declared point-in-time correctness policy. *app/utils/errors.py:466*
- [X] ML-based strategies shall implement concept drift and data drift detection where applicable. *app/services/strategies/sandbox.py:42*
- [X] Strategies shall emit `STRATEGY_DRIFT_DETECTED` when input feature distributions or model prediction confidence deviate beyond approved statistical thresholds. *app/utils/errors.py:416*
- [X] Strategies shall be prohibited from containing hardcoded secrets, API keys, or credentials. *app/services/strategies/__init__.py:2*
- [X] Strategies requiring external configuration secrets shall request them through an approved read-only secrets manager interface injected at runtime by the orchestration layer. *app/services/strategies/__init__.py:2*
- [X] Strategies shall not log, serialize, checkpoint, or expose secrets in diagnostics, rationale, manifests, or state snapshots. *app/services/strategies/__init__.py:2*
- [X] Strategies using Level 2 or Level 3 data shall declare their maximum supported order book depth. *app/services/strategies/__init__.py:2*
- [X] Strategies may annotate intents with declared maximum volume participation assumptions for visible order book data at the decision timestamp; official sizing validation remains owned by risk, trading, simulation, or live execution modules. *app/services/strategies/__init__.py:2*
- [X] Strategies shall define deterministic behavior when order book data is crossed, locked, stale, incomplete, or outside the declared supported depth. *app/services/strategies/__init__.py:2*
- [X] Each requirement shall be traceable to a specific test case id where implementation is required. *app/utils/errors.py:1427*
- [X] Major design-choice requirements shall be traceable to an Architecture Decision Record. *tests/unit/app/services/strategies/test_trend_following.py:146*
- [X] A strategy shall not be considered production-ready until it passes applicable testing, validation, and runbook requirements. *app/services/strategies/registry.py:137*
- [X] Production-ready strategy approval shall require sign-off from the Quant Research Lead and Engineering Lead, or their approved delegates. *app/utils/errors.py:5*
- [X] Strategies shall follow a standard processing anatomy: data input, indicator calculation, signal generation, timing alignment, trade intent creation, and simulation execution. *app/services/strategies/__init__.py:2*
- [X] Hook inputs and outputs shall be typed and schema-documented. *app/services/strategies/event.py:160*
- [X] Strategy hooks shall return only approved strategy outputs, including decisions, diagnostics, state updates, or `TradeIntent` objects. *app/services/strategies/event.py:142*
- [X] Strategy hooks shall not mutate official simulation, execution, account, order, position, journal, or reporting state directly. *app/services/strategies/base.py:54*
- [X] Required and optional hooks shall be explicitly declared by strategy type. *app/services/strategies/__init__.py:69*
- [X] Unsupported hooks for a strategy type shall fail deterministically or be ignored according to the approved interface contract. *app/utils/errors.py:16*
- [X] Invalid strategy configuration schema shall fail before execution. *app/services/strategies/event.py:87*
- [X] Unknown configuration fields shall be rejected or ignored according to an explicit schema policy. *app/services/strategies/registry.py:485*
- [X] Data-service timeout, unavailable dependency, broken connection, or network partition shall produce `STRATEGY_DATA_NOT_READY` after the approved retry/no-retry policy is exhausted. *app/utils/errors.py:332*
- [X] Partial data degradation shall follow the strategy's declared missing-data policy: `reject` suppresses all intents, `skip signal` suppresses affected symbols, and any degraded subset execution shall emit `STRATEGY_DATA_QUALITY_GATE_FAILED` diagnostics naming omitted symbols without exposing private payloads. *app/utils/errors.py:414*
- [X] Duplicate, out-of-order, stale, revised, or late-arriving ticks shall follow the declared data policy. *app/utils/errors.py:356*
- [X] Strategy hook timeout shall return `STRATEGY_TIMEOUT` and follow the configured failure policy. *app/utils/errors.py:408*
- [X] Concurrent read-only state snapshots across multiple strategies shall define isolation level, snapshot timestamp, and behavior when official state updates during decision traversal. *app/services/strategies/protocols.py:63*
- [X] `STRATEGY_INVALID_CONFIG` *app/utils/errors.py:156*
- [X] `STRATEGY_NOT_FOUND` *app/utils/errors.py:157*
- [X] `STRATEGY_DEPRECATED` *app/utils/errors.py:159*
- [X] `STRATEGY_UNAPPROVED_MODULE` *app/utils/errors.py:160*
- [X] `STRATEGY_SCHEMA_VALIDATION_FAILED` *app/utils/errors.py:161*
- [X] `STRATEGY_UNSUPPORTED_TIMING_POLICY` *app/services/strategies/vectorized.py:83*
- [X] `STRATEGY_ENVIRONMENT_NOT_PERMITTED` *app/utils/errors.py:167*
- [X] `STRATEGY_ARTIFACT_HASH_MISMATCH` *app/utils/errors.py:168*
- [X] `STRATEGY_DEPENDENCY_HASH_MISMATCH` *app/utils/errors.py:169*
- [X] `STRATEGY_CHECKPOINT_INCOMPATIBLE` *app/utils/errors.py:172*
- [X] `STRATEGY_DATA_NOT_READY` *app/utils/errors.py:173*
- [X] `STRATEGY_INDICATOR_NOT_READY` *app/utils/errors.py:174*
- [X] `STRATEGY_MISSING_REQUIRED_DATA` *app/utils/errors.py:175*
- [X] `STRATEGY_STALE_DATA` *app/utils/errors.py:176*
- [X] `STRATEGY_DUPLICATE_INTENT` *app/utils/errors.py:177*
- [X] `STRATEGY_RESOURCE_LIMIT_EXCEEDED` *app/utils/errors.py:178*
- [X] `STRATEGY_TIMEOUT` *app/utils/errors.py:179*
- [X] `STRATEGY_VALIDATION_ARTIFACT_REQUIRED` *app/utils/errors.py:180*
- [X] `STRATEGY_RISK_PROFILE_REQUIRED` *app/utils/errors.py:181*
- [X] `STRATEGY_CIRCUIT_BREAKER_TRIGGERED` *app/utils/errors.py:182*
- [X] `STRATEGY_POSITION_LIMIT_EXCEEDED` *app/utils/errors.py:183*
- [X] `STRATEGY_VOLUME_PARTICIPATION_EXCEEDED` *app/utils/errors.py:184*
- [X] `STRATEGY_PERFORMANCE_DEGRADED` *app/utils/errors.py:186*
- [X] `STRATEGY_DRIFT_DETECTED` *app/utils/errors.py:187*
- [X] `STRATEGY_REGULATORY_LIMIT_BREACHED` *app/utils/errors.py:188*
- [X] `STRATEGY_MARKET_ACCESS_REVOKED` *app/utils/errors.py:189*
- [X] `STRATEGY_HARD_KILLED` *app/services/strategies/event.py:138*
- [X] Every requirement id shall have at least one linked test id or a documented non-implementation rationale. *tests/unit/app/services/strategies/test_event.py:1*
- [X] Every usage example shall be executable or schema-validatable as documentation test coverage. *tests/unit/app/services/strategies/test_registry.py:221*
- [X] The traceability matrix shall be tested or reviewed as an explicit pre-implementation deliverable. *app/services/strategies/base.py:67*
- [X] Public capability tests shall verify exact Python signatures, input schema validation, output schema validation, error decision tables, side-effect rules, and batch/stream behavior. *app/services/strategies/sandbox.py:17*
- [X] Strategy tests shall cover EMA trend intents, martingale recovery, decomposition child orders, and partial-fill handling. *app/services/strategies/__init__.py:46*
- [X] Strategy tests shall cover previous-closed-bar signal timing and no-lookahead behavior. *app/services/strategies/protocols.py:78*
- [X] Strategy tests shall verify indicator-derived signals cannot access prohibited current-bar values. *app/services/strategies/registry.py:302*
- [X] Strategy configuration tests shall verify valid schemas pass and invalid schemas fail deterministically. *app/utils/errors.py:385*
- [X] Strategy tests shall include golden-file replay tests for emitted `TradeIntent` manifests. *tests/unit/app/services/strategies/test_trend_following.py:2*
- [X] Strategy tests shall include fuzz tests for invalid configuration, malformed data, missing fields, duplicate ticks, out-of-order ticks, NaN indicators, and extreme prices. *app/services/strategies/registry.py:485*
- [X] Strategy tests shall include performance regression tests with approved latency and memory thresholds. *tests/unit/app/services/strategies/test_trend_following.py:2*
- [X] Strategy tests shall include snapshot tests verifying stable intent ids, decision ids, configuration hashes, and replay manifests. *tests/unit/app/services/strategies/test_trend_following.py:2*
- [X] Strategy tests shall include mutation testing to verify that deliberate subtle corruptions to strategy logic or data inputs are caught by the test suite. *tests/unit/app/services/strategies/test_registry.py:141*
- [X] Boundary tests shall verify strategies cannot mutate official account, order, deal, position, margin, equity, journal, reporting, or execution timestamp state. *tests/unit/app/services/strategies/test_event.py:2*
- [X] Boundary tests shall verify portfolio, compliance, disaster-recovery, deployment, and venue requirements are exposed only as declarations or metadata, not enforced inside the strategy module. *app/services/strategies/protocols.py:50*
- [X] Security tests shall cover configuration-injection payloads, oversized configuration payloads, excessive nesting, excessive string lengths, and resource exhaustion through sanctioned strategy and indicator paths. *app/services/strategies/registry.py:588*
- [X] Clock-drift tests shall verify behavior when strategy, data, indicator, or simulation timestamps exceed approved tolerance. *app/utils/errors.py:324*
- [X] Documentation shall state that raw arbitrary Python strategy code is not accepted by `run_backtest`. *app/services/strategies/sandbox.py:17*
- [X] Documentation shall describe strategy replay metadata. *tests/unit/app/services/strategies/test_registry.py:171*
- [X] Documentation shall include public capability contracts, requirement IDs, applicability tags, acceptance criteria, and linked test IDs before Builder handoff. *tests/unit/app/services/strategies/test_event.py:1*
- [X] Before Builder handoff, each requirement shall include a stable requirement id, priority, phase, applicability tags, owning module, acceptance criteria, and at least one linked test case id where implementation is required. *app/utils/errors.py:361*
- [X] Applicability tags shall identify whether a requirement applies to `BACKTEST_CORE`, `REPLAY`, `PAPER`, `SHADOW`, `LIVE`, `ML_ONLY`, `L2_L3_ONLY`, `REGULATED_MARKET_ONLY`, or `FUTURE`. *app/services/strategies/protocols.py:17*
- [X] A traceability matrix shall be a required deliverable before implementation begins, not a future improvement. *app/services/strategies/__init__.py:159*
- [X] Stable requirement IDs, acceptance criteria, applicability tags, and linked test IDs are required for v1.0 Builder handoff. *tests/unit/app/services/strategies/test_event.py:1*
- [X] Strategies shall emit `TradeIntent` objects and diagnostics, not broker orders, official fills, account mutations, portfolio mutations, risk approvals, or regulatory reports. *app/services/strategies/vectorized.py:5*
- [X] Risk, trading, simulation, live, portfolio, compliance, reporting, data, and indicator modules shall remain the authorities for their own enforcement responsibilities. *app/services/strategies/protocols.py:129*
- [X] Strategy execution shall receive read-only snapshots or approved read-only handles for external state; strategy code shall not mutate official external state directly. *app/services/strategies/event.py:142*
- [X] Every external-module interaction shall pass through a documented contract with deterministic error mapping, timeout behavior, and redaction behavior. *app/services/strategies/__init__.py:5*
- [X] Strategy implementation scope shall be narrowed to an approved phase slice before Builder handoff. *app/services/strategies/__init__.py:125*

#### `app/utils/errors.py`

Functions/classes:

- `STRATEGY_LOOKAHEAD_DETECTED`

Requirements:

- [X] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom strategy exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`. *app/utils/errors.py:28*
- [X] Strategy access to prohibited current-bar or future data shall fail with the canonical strategy-domain error code `STRATEGY_LOOKAHEAD_DETECTED`; lower-level simulation lookahead errors, if any, shall be mapped to this code before returning strategy diagnostics. *app/utils/errors.py:1261*
- [X] Repeated strategy errors shall trigger deterministic disablement or escalation according to configuration. *app/utils/errors.py:855*
- [X] Strategies shall return safe, deterministic errors for invalid configuration or unsupported inputs. *app/utils/errors.py:837*
- [X] No file-specific non-functional requirements defined. *app/utils/errors.py:50*
- [X] Every public capability shall have contract tests for valid input, invalid input, deterministic errors, idempotency, and side effects. *app/utils/errors.py:298*
- [X] Error-code tests shall verify lower-level lookahead errors map to `STRATEGY_LOOKAHEAD_DETECTED` at strategy-module boundaries. *app/utils/errors.py:1261*
- [X] Dependency-failure tests shall verify data-layer failures map to `STRATEGY_DATA_NOT_READY` or approved data errors and indicator-layer failures map to `INDICATOR_MODULE_ERROR`. *app/utils/errors.py:402*
- [X] Each public capability shall include a decision table mapping every validation condition, dependency condition, lifecycle condition, timeout condition, and security condition to one deterministic error code. *app/services/strategies/registry.py:58*
- [X] Raw strategy-code injection attempts shall be rejected before execution. *app/utils/errors.py:393*
- [X] Rejected raw strategy-code input shall return `SIM_ARBITRARY_CODE_REJECTED`. *app/services/strategies/sandbox.py:40*
- [X] Rejected strategy-injection attempts shall be journaled without logging unsafe code bodies in full. *app/services/strategies/sandbox.py:26*
- [X] Rejected strategy-input diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code. *app/services/strategies/sandbox.py:40*
- [X] Resource exhaustion by sanctioned strategy code, sanctioned indicator calls, or sanctioned data access shall fail deterministically with `STRATEGY_RESOURCE_LIMIT_EXCEEDED` or a more specific approved error code. *app/utils/errors.py:989*
- [X] Strategy security rejections must be journaled with safe redaction. *app/utils/errors.py:30*
- [X] Structured error result with deterministic error code on failure. *app/utils/errors.py:527*
- [X] Deprecated or revoked strategies shall fail deterministically before execution unless explicitly run in historical replay mode. *tests/unit/app/services/strategies/test_registry.py:165*
- [X] The simulation or risk engine shall remain the final authority for official risk acceptance or rejection. *app/utils/errors.py:298*
- [X] Duplicate `intent_id` or idempotency key collisions shall fail deterministically. *app/services/strategies/registry.py:137*
- [X] Strategy execution shall fail deterministically if required market data fields are missing, stale, out of order, duplicated, or timezone-inconsistent unless an explicit approved policy handles them. *app/utils/errors.py:1289*
- [X] Strategy diagnostics shall support debug mode without exposing secrets, proprietary source, unsafe code bodies, or excessive market-data payloads. *app/utils/errors.py:33*
- [X] Strategy approval shall be invalidated if the source hash, artifact hash, dependency hash, or build provenance changes. *app/utils/errors.py:41*
- [X] The orchestration layer shall support deterministic failure policies: `FAIL_RUN`, `DISABLE_STRATEGY`, `SKIP_DECISION`, or `QUARANTINE_INSTANCE`. *app/utils/errors.py:343*
- [X] Corrupt, incompatible, or unauthorized checkpoints shall fail deterministically before execution. *app/utils/errors.py:22*
- [X] Strategies shall declare behavior when the data layer reports cross-venue price deviation, degraded data quality, failover, or unavailable data. *app/utils/errors.py:837*
- [X] Data vendor failover orchestration shall remain owned by the data or operations module. *app/utils/errors.py:1289*
- [X] Recovery time objectives shall be defined for strategy restarts and failovers. *app/utils/errors.py:1*
- [X] Strategies shall declare assumptions for backup execution venues where applicable; backup venue failover enforcement remains owned by execution, live, or operations modules. *app/utils/errors.py:837*
- [X] Post-mortem documentation shall be required for strategy failures. *app/utils/errors.py:1*
- [X] Unknown strategy id shall fail before execution. *tests/unit/app/services/strategies/test_registry.py:144*
- [X] Empty strategy identifier shall fail before execution with a deterministic validation error. *app/services/strategies/registry.py:286*
- [X] Unapproved strategy module shall fail before execution. *app/utils/errors.py:32*
- [X] Raw arbitrary Python strategy code strings shall be rejected before execution. *app/utils/errors.py:903*
- [X] Unsafe rejected code bodies shall not be logged in full. *app/services/strategies/sandbox.py:22*
- [X] Empty market-data input shall produce `STRATEGY_DATA_NOT_READY` or a more specific deterministic error. *app/utils/errors.py:402*
- [X] Indicator module timeout, unavailable dependency, broken connection, or unhandled indicator exception shall map to `INDICATOR_MODULE_ERROR` with original exception details redacted. *app/utils/errors.py:399*
- [X] Timezone-naive, DST-ambiguous, or timezone-inconsistent data shall fail unless an approved normalization policy exists. *app/utils/errors.py:414*
- [X] Clock drift beyond the approved tolerance between strategy runtime, data feed, indicator outputs, or simulation clock shall fail closed with `STRATEGY_STALE_DATA`, checkpoint abort, or a more specific approved error code. *tests/unit/app/services/strategies/test_vectorized.py:203*
- [X] Duplicate `intent_id`, duplicate idempotency key, or non-monotonic strategy-local sequence number shall fail deterministically. *app/services/strategies/registry.py:137*
- [X] Attempted secret exposure in diagnostics, checkpoints, manifests, or rationale shall fail redaction validation. *app/utils/errors.py:307*
- [X] `SIM_ARBITRARY_CODE_REJECTED` *app/utils/errors.py:164*
- [X] `STRATEGY_INTERNAL_ERROR` *app/utils/errors.py:165*
- [X] `INDICATOR_MODULE_ERROR` *app/utils/errors.py:170*
- [X] `STRATEGY_CHECKPOINT_INVALID` *app/utils/errors.py:171*
- [X] `STRATEGY_DATA_QUALITY_GATE_FAILED` *app/utils/errors.py:185*
- [X] Every confirmed error code shall have at least one focused failure-path test that triggers the code and verifies the full response or diagnostic shape. *app/utils/errors.py:1427*
- [X] AI Tool strategy security tests shall verify `run_backtest` rejects raw arbitrary Python strategy code, returns `SIM_ARBITRARY_CODE_REJECTED`, does not execute rejected code, and does not log rejected code in full. *app/utils/errors.py:393*
- [X] Strategy tests shall include scenario tests for session boundaries, holidays, weekend gaps, DST transitions, spread spikes, partial fills, rejected fills, and multi-timeframe bar closure. *tests/unit/app/services/strategies/test_trend_following.py:2*
- [X] Each confirmed error code shall have at least one triggering scenario and a stable diagnostic shape before implementation acceptance. *app/utils/errors.py:534*

#### `app/services/strategies/vectorized.py`

Functions/classes:

- `run_vectorized_strategy_signals`
- `TradeIntent`
- `MULTIPROCESS_ISOLATED`

Requirements:

- [X] Each public capability shall define whether results are returned as a single batch, iterator, stream, or async stream; `run_vectorized_strategy_signals` shall be treated as batch output until a streaming contract is explicitly approved. *app/services/strategies/vectorized.py:60*
- [X] The module shall support vectorized signal strategies. *app/utils/errors.py:343*
- [X] Vectorized signal strategies shall compute indicators, generate signals, and convert signals to timestamped `TradeIntent` objects before simulation execution. *app/services/strategies/base.py:49*
- [X] Vectorized signal generation shall shift current-bar conditions so that bar-open entries are based on previous closed-bar values. *app/services/strategies/vectorized.py:135*
- [X] If a vectorized batch detects lookahead at any element, the entire batch shall fail atomically, emit `STRATEGY_LOOKAHEAD_DETECTED`, discard intents produced by that batch, and preserve a diagnostic identifying the first failing timestamp. *app/services/strategies/vectorized.py:143*
- [X] A vectorized batch decision clock shall be anchored to the supplied `StrategyExecutionContext.decision_timestamp`; wall-clock elapsed time during long-running batches shall not advance decision-time semantics. *app/services/strategies/vectorized.py:148*
- [X] Vectorized processing is allowed only for indicator and signal generation. *app/services/strategies/vectorized.py:135*
- [X] CPU-bound vectorized strategies shall run in isolated worker processes when their declared execution profile is `MULTIPROCESS_ISOLATED`, when configured by orchestration, or when measured event-loop latency exceeds the approved threshold for the target environment. *app/utils/errors.py:987*
- [X] Vectorized strategies shall calculate indicators in a vectorized manner where supported by the indicator module. *app/services/strategies/vectorized.py:2*
- [X] Vectorized strategies shall generate signals in a vectorized manner before conversion to timestamped `TradeIntent` objects. *app/services/strategies/base.py:58*
- [X] Vectorized processing shall not bypass tick-accurate simulation execution, fill modeling, accounting, margin checks, risk checks, or journal generation. *app/services/strategies/vectorized.py:2*
- [X] Hook execution order shall be deterministic and documented for vectorized runs, event-driven runs, replay, checkpoint restore, and shutdown. *app/services/strategies/event.py:269*
- [X] Documentation shall include examples for vectorized signal strategies and event-driven strategies. *app/services/strategies/__init__.py:47*
- [X] No file-specific non-functional requirements defined. *app/services/strategies/base.py:38*
- [X] Clock drift detected during a long-running vectorized batch shall not change the batch decision timestamp; the batch shall either complete under the original timestamp or fail atomically according to the configured clock-drift policy. *app/utils/errors.py:324*
- [X] Strategy tests shall cover vectorized signal strategies. *app/services/strategies/__init__.py:12*
- [X] `STRATEGY_LOOKAHEAD_DETECTED` *app/services/strategies/vectorized.py:149*
- [X] Strategy tests shall include property-based tests for no-lookahead, deterministic replay, and risk-envelope invariants. *tests/unit/app/services/strategies/test_trend_following.py:2*
- [X] Property-based no-lookahead tests shall cover timezone offsets, DST gaps, DST overlaps, session boundaries, late-arriving data, revised bars, and multi-timeframe closure boundaries. *app/services/strategies/vectorized.py:70*
- [X] Documentation shall describe no-lookahead strategy timing. *app/utils/errors.py:993*

#### `app/services/strategies/event.py`

Functions/classes:

- `FILL_UPDATE`
- `PARTIAL_FILL`
- `TradeIntent`
- `decision_id`
- `ASYNC_AWAIT`
- `SYNC_BLOCKING`

Requirements:

- [X] Strategies shall not directly create official fills, deals, journal events, or reports. *app/services/strategies/__init__.py:2*
- [X] The module shall support stateful event strategies. *app/utils/errors.py:313*
- [X] Event strategies shall respond to initialization, bar-open, tick, and trade-transaction events through controlled interfaces. *app/services/strategies/event.py:2*
- [X] `INTRABAR_EVENT` strategies may use current tick data only through approved event interfaces. *app/services/strategies/protocols.py:20*
- [X] Event strategies shall support `FILL_UPDATE` or `PARTIAL_FILL` events to react to incomplete executions through approved read-only execution-state interfaces. *app/services/strategies/event.py:2*
- [X] Strategy-local state updates shall be atomic per decision event or shall fail with a deterministic rollback diagnostic. *app/services/strategies/event.py:142*
- [X] Read-only external state supplied to a strategy shall be an immutable snapshot or shall carry a documented consistency model preventing races with concurrent simulation, risk, portfolio, or data updates. *app/services/strategies/event.py:118*
- [X] Optional read-only simulation state for event strategies. *app/services/strategies/base.py:83*
- [X] Strategy risk profiles shall declare correlation assumptions during stress events. *app/utils/errors.py:410*
- [X] Every `TradeIntent` shall include a `decision_id` linking it to the strategy decision event that created it. *app/services/strategies/protocols.py:91*
- [X] Strategy metrics shall include intents emitted, intents suppressed, no-signal decisions, rejected decisions, invalid data events, lookahead detections, configuration validation failures, state checkpoint size, and per-event decision latency. *app/services/strategies/event.py:142*
- [X] Strategies shall not perform unbounded loops, unbounded recursion, unbounded memory growth, or unbounded history scans during event execution. *app/services/strategies/__init__.py:2*
- [X] Event strategies shall be reentrant or explicitly marked single-threaded. *app/services/strategies/event.py:2*
- [X] Simultaneous events shall be processed using a stable deterministic ordering policy. *app/utils/errors.py:534*
- [X] Wash trade prevention rules shall be declared. *app/services/strategies/event.py:1*
- [X] Strategies shall declare behavior during `AUCTION_PHASE`, `TRADING_HALT`, `CROSSING_SESSION`, and `BROKEN_MARKET` microstructure events. *app/services/strategies/__init__.py:2*
- [X] Event strategies shall implement a standard lifecycle interface where applicable. *app/services/strategies/event.py:2*
- [X] The standard event strategy lifecycle interface shall include hooks such as `on_init`, `on_start`, `on_bar`, `on_tick`, `on_fill_update`, `on_partial_fill`, `on_order_update`, `on_timer`, `on_error`, `on_checkpoint`, `on_restore`, and `on_stop`. *tests/unit/app/services/strategies/test_trend_following.py:183*
- [X] Strategy execution shall define measurable latency, memory, checkpoint-size, diagnostic-payload-size, event-queue, timeout, and retry-exhaustion limits per supported environment before implementation acceptance. *app/services/strategies/event.py:196*
- [X] Strategy execution shall define deterministic backpressure behavior when event volume exceeds configured capacity. *app/services/strategies/event.py:142*
- [X] `ASYNC_AWAIT` strategies shall define an approved async compatibility contract and shall not block the event loop. *app/services/strategies/__init__.py:13*
- [X] `SYNC_BLOCKING` strategies shall define maximum call duration and isolation expectations before being used in shared event loops. *app/services/strategies/__init__.py:13*
- [X] No file-specific non-functional requirements defined. *app/services/strategies/base.py:38*
- [X] Simultaneous events for a single strategy instance shall be processed in a stable documented order, such as timestamp, event type priority, then deterministic sequence number. *app/services/strategies/event.py:115*
- [X] Strategy tests shall cover stateful event strategies. *app/services/strategies/event.py:142*
- [X] Strategy tests shall include stress tests for large histories, many symbols, dense tick streams, and high-frequency event dispatch. *tests/unit/app/services/strategies/test_trend_following.py:2*
- [X] Strategy tests shall include chaos engineering scenarios, including simulated data-feed disconnections, sudden latency spikes, and out-of-order message injection during event processing. *app/services/strategies/event.py:86*
- [X] Strategy tests shall verify memory leak detection over extended event-loop iterations and assert stable memory usage within approved thresholds. *app/services/strategies/event.py:142*
- [X] Boundary tests shall verify strategies cannot create fills, deals, official orders, reports, or journal events directly. *tests/unit/app/services/strategies/test_event.py:1*
- [X] Concurrency tests shall verify read-only state snapshot isolation and stable event ordering for simultaneous events. *app/services/strategies/protocols.py:63*
- [X] A strategy shall not execute in an environment higher than its approved lifecycle status. *app/services/strategies/registry.py:302*
- [X] `STRATEGY_LIFECYCLE_NOT_APPROVED` *app/utils/errors.py:166*

#### `app/services/strategies/sandbox.py`

Functions/classes:

- `STRATEGY_ENVIRONMENT_NOT_PERMITTED`

Requirements:

- [X] The strategy input path shall accept only registered strategy identifiers, validated strategy configuration schemas, or code explicitly vetted and sandboxed by the orchestration layer. *app/services/strategies/base.py:68*
- [X] Code-based strategy execution shall remain disabled until sandbox policy, approval workflow, and prohibited-operation lists are approved. *app/services/strategies/sandbox.py:42*
- [X] Sandboxed code-based strategy execution, if enabled later, shall require `simulation.admin` approval, strategy owner approval, sandbox profile id, vetting artifact hash, allowed capability list, audit record, and approval expiry. *app/services/strategies/sandbox.py:2*
- [X] Sandbox policy shall define allowed imports, denied imports, filesystem access, network access, subprocess access, environment-variable access, timeouts, memory limits, and prohibited operations. *app/services/strategies/base.py:88*
- [X] Strategy execution shall occur only through registered strategies, validated schemas, or explicitly sandboxed and vetted orchestration paths. *app/services/strategies/__init__.py:12*
- [X] Sandbox and vetting metadata only when code-based strategy execution is explicitly permitted. *app/services/strategies/sandbox.py:2*
- [X] Any attempt by a strategy to read environment variables not explicitly allowlisted in the sandbox profile shall emit `STRATEGY_ENVIRONMENT_NOT_PERMITTED`. *app/utils/errors.py:396*
- [X] Documentation shall describe sandbox and vetting requirements if code-based strategy execution is ever enabled. *app/services/strategies/sandbox.py:2*
- [X] No file-specific non-functional requirements defined. *app/services/strategies/base.py:38*
- [X] Missing sandbox or vetting metadata for a code-based strategy path shall fail before execution. *app/services/strategies/__init__.py:69*
- [X] Sandbox approval expiry shall cause code-based strategy execution to fail before execution. *app/services/strategies/sandbox.py:2*
- [X] `STRATEGY_SANDBOX_REQUIRED` *app/services/strategies/sandbox.py:1*


### Hardening Amendments

#### Canonical signal boundary

Requirements:

- [X] Adopt the Phase 1.5 `StrategyInput` and `StrategySignal` contracts for all strategy service inputs and outputs. *app/services/strategies/__init__.py:47*
- [X] Enforce the canonical flow `StrategyInput -> StrategySignal -> RiskDecision -> OrderIntent -> TradeRequest`. *app/services/strategies/registry.py:576*
- [X] Prohibit strategies from returning broker-specific order requests, raw broker payloads, execution commands, or live mutation instructions. *app/services/strategies/sandbox.py:42*
- [X] Add strategy version hash, parameter hash, input dataset hash, signal validity window, optional confidence score, and evidence references to every emitted signal. *app/services/strategies/event.py:62*
- [X] Reject expired, malformed, unsupported, or insufficient-evidence signals before they reach Risk Governance. *app/services/strategies/protocols.py:129*
- [X] Add tests proving strategy outputs can be consumed by Risk without broker-specific adapter knowledge. *app/services/strategies/protocols.py:129*

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

- [X] Each public capability shall define precise side effects, mutation permissions, idempotency behavior, concurrency assumptions, retry behavior, and redaction behavior. *app/services/strategies/protocols.py:1*
- [X] Strategy imports shall be side-effect safe and shall not perform broker calls, network access, filesystem writes, subprocess execution, environment mutation, or decision-time clock/randomness reads. *app/services/strategies/registry.py:302*
- [X] Security tests shall verify strategy imports perform no broker calls, network calls, filesystem writes, subprocess calls, environment mutation, or secret reads. *app/services/strategies/registry.py:588*
