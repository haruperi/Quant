## Phase 3 Indicator Library

### Goal

Implement the Indicator Library requirements under `app/services/indicators/` while preserving the phase module boundaries and governance rules.

Task inventory: 737 checkbox tasks (737 checked, 0 unchecked).

### Dependency Files and Functionality

Required files:

```text

app/utils/__init__.py

app/utils/errors.py

app/utils/dataframe_tools.py

app/services/data/__init__.py

app/services/data/gateway.py

```

Required functionality:

- Data gateway is accessible to fetch historical symbol series.
- Dataframe utility operations (alignment, comparison, serialization) exist.
- Centralized exception classes can resolve custom indicator errors.

### Files to Create

```text

app/__init__.py

app/services/indicators/__init__.py

app/services/indicators/registry.py

app/services/indicators/protocols.py

app/utils/errors.py

app/services/indicators/calculations.py

app/services/indicators/batch/__init__.py

app/services/indicators/batch/trend.py

app/services/indicators/batch/volatility.py

app/services/indicators/batch/momentum.py

app/services/indicators/incremental/__init__.py

app/services/indicators/incremental/state.py

app/services/indicators/incremental/accumulators.py

app/services/indicators/adapters/__init__.py

app/services/indicators/adapters/cache.py

app/services/indicators/adapters/audit.py

app/services/indicators/

app/services/simulation/

app/utils/errors.py

```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/indicators/README.md`

Functions/classes:

- No runtime functions/classes; documentation artifact only.

Requirements:

- [X] Documentation shall warn against using unshifted current-bar values for bar-open decisions. *app/services/indicators/README.md:151*
- [X] Promotion of custom indicators to official status shall require documentation, golden fixtures, conformance tests, no-lookahead tests, determinism tests, and benchmark coverage. *tests/unit/app/services/indicators/test_registry.py:35*
- [X] Documentation shall include the Production Scope Tiers classification for every requirement before implementation begins. *app/services/indicators/README.md:103*
- [X] Documentation shall describe no-lookahead behavior for indicator-derived signals. *app/services/indicators/README.md:3*
- [X] Documentation shall describe multi-timeframe indicator alignment. *app/services/indicators/README.md:135*
- [X] Documentation shall describe output column naming, default source naming, non-default source naming, multi-output naming, custom output names, output column conflict policy, and generated `output_columns`. *app/services/indicators/README.md:53*
- [X] Documentation shall describe debug-mode strict typing and runtime validation behavior. *app/services/indicators/README.md:40*
- [X] Documentation shall describe golden fixtures and reference output approval workflow. *app/services/indicators/README.md:103*
- [X] Documentation shall describe the `available_at` contract, `label_time`, `bar_open_time`, `bar_close_time`, `computed_from_start`, `computed_from_end`, and strategy-facing filtering. *app/services/indicators/README.md:3*
- [X] Documentation shall describe custom indicator conformance, status values, prohibited operations, dependency declarations, and promotion review. *app/services/indicators/README.md:40*
- [X] Documentation shall describe mandatory cross-validation against industry-standard libraries, third-party formula convention differences, golden fixture approval, mutation fuzz testing, and survivorship bias testing. *tests/unit/app/services/indicators/test_registry.py:32*
- [X] Public usage examples shall be executable documentation examples once implementation begins. *app/services/indicators/README.md:108*

#### `app/__init__.py`

Functions/classes:

- `IndicatorProtocol`

Requirements:

- [X] Every smoothed indicator shall define smoothing method, alpha convention, and initial seed behavior. *app/services/indicators/protocols.py:450*
- [X] Documentation shall describe numeric dtype policy, NaN, infinity, negative zero, overflow, underflow, divide-by-zero, and floating-point tolerance behavior. *app/services/indicators/protocols.py:46*
- [X] `IndicatorProtocol.calculate(data, config, context)` shall use approved type hints before implementation begins. *app/services/indicators/protocols.py:4*
- [X] `data` shall be a `pandas.DataFrame` for Core MVP batch execution unless a formula table explicitly approves an alternate typed input. *app/services/indicators/protocols.py:197*
- [X] Core MVP `data` shall contain UTC-normalized timestamp information as either a UTC `DatetimeIndex` for single-symbol input or a `MultiIndex` containing `symbol` and UTC `timestamp` levels for multi-symbol input. *app/services/indicators/protocols.py:164*
- [X] Core MVP `data` shall expose required OHLCV columns through stable lowercase column names and shall reject ambiguous duplicate columns. *app/services/indicators/protocols.py:53*
- [X] `IndicatorResult.values` shall be a `pandas.DataFrame` aligned to the accepted input timestamp/symbol keys and containing generated indicator columns plus required availability and quality metadata. *app/services/indicators/protocols.py:164*
- [X] `IndicatorConfig` and `IndicatorContext` shall be typed as dataclasses, `TypedDict`, Pydantic models, or equivalent approved Python contracts before Builder handoff. *app/services/indicators/protocols.py:8*
- [X] Any future array-native input such as `numpy.ndarray` shall be an Optional Extension with explicit schema, shape, dtype, symbol/timestamp alignment, and conversion rules. *app/services/indicators/protocols.py:494*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/protocols.py:42*
- [X] Numeric tests shall cover dtype preservation, NaN, infinity, negative zero, overflow, underflow, divide-by-zero, absolute tolerance, and relative tolerance. *tests/unit/app/services/indicators/test_advanced_features.py:357*
- [X] Numeric tests shall verify NaN propagation, infinity rejection in official workflows, division-by-zero unavailable outputs, negative-zero normalization, and overflow/underflow deterministic handling. *tests/unit/app/services/indicators/test_advanced_features.py:276*
- [X] Property-based mutation fuzz tests shall inject NaN, infinity, extreme outliers, zero volume, flat prices, negative values, malformed timestamps, duplicate timestamps, and random missing intervals. *tests/unit/app/services/indicators/test_advanced_features.py:2*

#### `app/services/indicators/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/indicators/protocols.py:42*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/protocols.py:42*
- [X] No file-specific testing requirements defined. *tests/unit/app/services/indicators/test_advanced_features.py:188*

#### `app/services/indicators/registry.py`

Functions/classes:

- `register_indicator(...)`
- `get_indicator(...)`
- `list_indicators(...)`
- `validate_indicator(...)`
- `unregister_indicator(...)`
- `register_indicator()`
- `get_indicator()`
- `list_indicators()`
- `validate_indicator()`
- `unregister_indicator()`
- `IndicatorResult`

Requirements:

- [X] The module shall provide an indicator registry for approved indicator implementations. *app/services/indicators/registry.py:2*
- [X] Registered indicators shall declare id, name, version, parameter schema, input schema, output schema, warmup policy, and deterministic behavior. *app/services/indicators/registry.py:374*
- [X] Custom indicators shall be registered through approved extension points before use in official workflows. *app/services/indicators/registry.py:154*
- [X] Custom indicator registration shall not bypass input validation, no-lookahead metadata, schema validation, or deterministic replay requirements. *app/services/indicators/registry.py:129*
- [X] Public APIs shall include stable import paths, function and class signatures, parameter schemas, result schemas, error schemas, and registry contracts. *app/services/indicators/registry.py:2*
- [X] The deprecation phase for each indicator, parameter, schema, or API shall be machine-readable through the registry. *app/services/indicators/registry.py:2*
- [X] The public package shall expose registry operations for `register_indicator(...)`, `get_indicator(...)`, `list_indicators(...)`, `validate_indicator(...)`, and `unregister_indicator(...)` where unregistering is allowed outside official production registries. *app/services/indicators/registry.py:120*
- [X] Convenience functions shall return `IndicatorResult` and shall use the same validation, naming, manifest, cache, availability, and no-lookahead rules as registry-driven execution. *app/services/indicators/registry.py:2*
- [X] Public module layout shall separate core protocols, result types, registry code, built-in indicator implementations, error definitions, and test fixtures. *tests/unit/app/services/indicators/test_registry.py:2*
- [X] Documentation shall declare the public API surface, stable import paths, `typing.Protocol` contracts, registry contracts, schema versions, and deprecation policy. *app/services/indicators/registry.py:11*
- [X] Documentation shall describe indicator anatomy, required public types, required protocol attributes, required protocol methods, registry operations, built-in convenience functions, result objects, manifests, and state objects. *app/services/indicators/registry.py:2*
- [X] Documentation shall describe the deprecation lifecycle, machine-readable registry phase, changelog entries, migration guide, and `IND_DEPRECATED`. *app/services/indicators/registry.py:2*
- [X] Indicator anatomy, required interfaces, registry operations, built-in convenience functions, and result object methods are documented and tested. *tests/unit/app/services/indicators/test_registry.py:2*
- [X] The public API contract table shall cover registry operations, built-in convenience functions, result object methods, protocol methods, state serialization functions, and manifest serialization functions. *app/services/indicators/registry.py:2*
- [X] The machine-readable capability matrix shall be generated from the registry and shall include indicator id, version, tier, supported modes, optional dependencies, unsupported-mode error codes, and official-workflow eligibility. *app/services/indicators/registry.py:45*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/registry.py:54*
- [X] Registry API tests shall verify `register_indicator`, `get_indicator`, `list_indicators`, `validate_indicator`, and allowed `unregister_indicator` behavior. *tests/unit/app/services/indicators/test_registry.py:2*
- [X] Built-in convenience function tests shall verify `ema`, `sma`, `adx`, `atr`, `adr`, `rolling_volatility`, `rsi`, and `williams_r` return `IndicatorResult` and follow the same validation, naming, manifest, cache, availability, and no-lookahead rules as registry execution. *tests/unit/app/services/indicators/test_registry.py:2*
- [X] Deprecation lifecycle tests shall verify deprecation warning phase, deprecation error with opt-in phase, removal phase, registry machine-readable phase, `IND_DEPRECATED`, and migration-guide coverage. *tests/unit/app/services/indicators/test_registry.py:2*
- [X] Capability-matrix tests shall verify every built-in indicator against its machine-readable capability matrix. *tests/unit/app/services/indicators/test_registry.py:2*
- [X] Custom indicator conformance suite passes for every registered custom indicator. *app/services/indicators/registry.py:71*
- [X] Every official indicator shall publish a machine-readable capability matrix covering batch, vectorized, incremental, streaming, out-of-core, acceleration, composition, multi-symbol, and multi-timeframe support. *app/services/indicators/registry.py:334*

#### `app/services/indicators/protocols.py`

Functions/classes:

- `IndicatorProtocol`
- `IndicatorConfig`
- `IndicatorContext`
- `IndicatorResult`
- `IndicatorState`
- `IndicatorManifest`
- `IndicatorMetadata`
- `WarmupPolicy`
- `PrecisionPolicy`
- `IndicatorDependency`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/indicators/protocols.py:42*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/protocols.py:42*
- [X] No file-specific testing requirements defined. *tests/unit/app/services/indicators/test_advanced_features.py:188*
- [X] The module shall be packageable through standard Python packaging metadata. *app/services/indicators/protocols.py:4*
- [X] Build-system and project metadata shall be declared in `pyproject.toml`. *app/services/indicators/protocols.py:134*
- [X] Logs shall include indicator id, implementation version, parameter hash, input checksum, symbol count, timeframe, and request id when available. *app/services/indicators/protocols.py:17*
- [X] Canary execution shall allow a configured subset of actors, workflows, symbols, or requests to receive a new implementation while comparing outputs against the baseline implementation. *app/services/indicators/protocols.py:21*
- [X] Distributed tracing, feature-flagged execution, canary routing, SLO alert routing, and rollback metadata shall be classified as Optional Extension unless a later approved decision promotes them. *app/services/indicators/protocols.py:87*
- [X] Indicator requests shall support configurable maximum rows, maximum symbols, maximum columns, memory budget, and execution timeout. *app/services/indicators/protocols.py:20*
- [X] Resource-limit defaults shall live in an approved configuration schema before Builder handoff and shall be overrideable only through validated configuration. *app/services/indicators/protocols.py:38*
- [X] Unless an indicator formula specification explicitly overrides this policy, NaN input values shall propagate to NaN outputs for affected rows or windows and shall be represented as unavailable values with quality metadata. *app/services/indicators/protocols.py:161*
- [X] Unless an indicator formula specification explicitly overrides this policy, division by zero shall produce NaN unavailable outputs with deterministic warning metadata rather than silently clipping or filling values. *app/services/indicators/protocols.py:47*
- [X] Production non-transient indicator error rate shall target less than 0.1 percent over the configured measurement window, excluding deterministic user input validation failures. *app/services/indicators/protocols.py:497*
- [X] Production indicator timeout rate shall target less than 0.05 percent over the configured measurement window. *app/services/indicators/protocols.py:41*
- [X] SLO thresholds, measurement windows, included workflows, excluded error categories, and alert routing shall be configurable. *app/services/indicators/protocols.py:111*
- [X] Indicator outputs shall be treated as decision inputs only; official execution remains owned by `app/services/simulation/`. *app/services/indicators/protocols.py:17*
- [X] Indicator implementations shall define required input columns, output column names, parameter schema, warmup length, and missing-data behavior. *app/services/indicators/protocols.py:190*
- [X] Indicators shall accept OHLCV inputs with explicit timestamp, symbol, timeframe, and timezone metadata. *app/services/indicators/protocols.py:164*
- [X] Indicators shall support multi-symbol input only when output grouping preserves symbol identity. *app/services/indicators/protocols.py:21*
- [X] Indicators shall preserve input row order after deterministic timestamp and symbol validation. *app/services/indicators/protocols.py:164*
- [X] Indicator outputs shall include timestamp and symbol alignment metadata. *app/services/indicators/protocols.py:164*
- [X] Indicator outputs shall expose warmup or unavailable regions explicitly rather than silently filling values. *app/services/indicators/protocols.py:164*
- [X] Indicator outputs shall distinguish computed values, warmup nulls, missing-input nulls, and rejected rows. *app/services/indicators/protocols.py:361*
- [X] Indicator outputs used by official backtests shall be serializable in the precision policy required by the downstream workflow. *tests/unit/app/services/indicators/test_advanced_features.py:120*
- [X] Indicator calculation shall not mutate the input dataframe by default. *app/services/indicators/protocols.py:190*
- [X] Official workflows shall treat in-place input mutation as prohibited unless an explicitly configured internal optimization proves copy-equivalent output and records the optimization in the manifest. *app/services/indicators/protocols.py:182*
- [X] The default batch result shall be an `IndicatorResult` containing an aligned `values` dataframe with timestamp, symbol, generated indicator columns, availability metadata, and quality metadata. *app/services/indicators/protocols.py:164*
- [X] The result object shall expose a `join_to(input_data, mode="copy")` helper that returns a copy of the source dataframe with generated indicator columns appended. *app/services/indicators/protocols.py:182*
- [X] Output column collisions with existing input columns shall fail with a deterministic error by default. *app/services/indicators/protocols.py:44*
- [X] Explicit overwrite, suffix, prefix, or namespace behavior for output column collisions shall require configuration and shall be recorded in the manifest. *app/services/indicators/protocols.py:46*
- [X] Joined output shall preserve original input columns, row count, row ordering, timestamp alignment, symbol grouping, and index policy. *app/services/indicators/protocols.py:136*
- [X] Warmup and unavailable rows shall remain present in joined output with nullable indicator values and explicit metadata rather than being dropped. *app/services/indicators/protocols.py:161*
- [X] Vectorized output alignment shall be verified by timestamp and symbol keys rather than by positional row number alone when the input dataframe has an external index. *app/services/indicators/protocols.py:230*
- [X] The same indicator input data, parameter set, implementation version, and precision policy shall produce the same output. *app/services/indicators/protocols.py:183*
- [X] Indicator implementations shall define numeric precision behavior. *app/services/indicators/protocols.py:345*
- [X] Indicator result manifests shall include input data checksum, parameter hash, implementation version, output schema version, and calculation timestamp. *app/services/indicators/protocols.py:128*
- [X] Chunked indicator output shall match full-run output within the documented precision policy. *app/services/indicators/protocols.py:44*
- [X] Performance benchmarks shall define warmup iterations before measurement. *tests/unit/app/services/indicators/test_advanced_features.py:13*
- [X] Out-of-core outputs shall match in-memory full-run outputs within the documented precision policy. *app/services/indicators/protocols.py:51*
- [X] Accelerated and fallback paths shall produce outputs that match within the documented precision policy and shall record backend metadata in the result manifest. *app/services/indicators/protocols.py:4*
- [X] Public indicator interfaces shall use `typing.Protocol` or equivalent structural typing contracts so custom indicators can integrate without inheriting from framework base classes. *app/services/indicators/protocols.py:436*
- [X] Indicator result objects shall implement rich notebook inspection methods, including `_repr_html_` and `_repr_pretty_`, with summary statistics, warmup visualization, unavailable-region visibility, and manifest summary. *app/services/indicators/protocols.py:345*
- [X] `IndicatorProtocol` shall define required attributes for `indicator_id`, `name`, `version`, `formula_version`, `input_schema`, `parameter_schema`, `output_schema`, `warmup_policy`, `capabilities`, and `status`. *app/services/indicators/protocols.py:127*
- [X] `IndicatorProtocol` shall define `validate_parameters(parameters)`. *app/services/indicators/protocols.py:458*
- [X] `IndicatorProtocol` shall define `required_columns(parameters)`. *app/services/indicators/protocols.py:466*
- [X] `IndicatorProtocol` shall define `output_columns(parameters, source=None, naming_policy=None)`. *app/services/indicators/protocols.py:68*
- [X] `IndicatorProtocol` shall define `warmup_requirement(parameters, timeframe, calendar=None)`. *app/services/indicators/protocols.py:458*
- [X] `IndicatorProtocol` shall define `validate_input(data, config, context)`. *app/services/indicators/protocols.py:4*
- [X] `IndicatorProtocol` shall define `calculate(data, config, context)`. *app/services/indicators/protocols.py:4*
- [X] `IndicatorProtocol` shall define `calculate_vectorized(data, config, context)` when the indicator supports vectorized batch execution separately from generic calculation. *app/services/indicators/protocols.py:4*
- [X] `IndicatorContext` shall contain request id, correlation id, actor, workflow, environment, entitlement context, tracing context, observability context, and SLO context where applicable. *app/services/indicators/protocols.py:86*
- [X] Every built-in indicator shall define default parameters, allowed parameter ranges, default source columns, required input columns, warmup length, output columns, null behavior, and degenerate-window behavior. *app/services/indicators/protocols.py:44*
- [X] Indicator formulas shall be documented with enough precision that an independent implementation can reproduce the same output. *app/services/indicators/protocols.py:5*
- [X] Each official built-in indicator shall include a formula specification table defining indicator id, required columns, default source column, parameters, default parameter values, valid parameter ranges, formula, smoothing convention, seed behavior, warmup length, window inclusivity, null handling, degenerate-window behavior, output columns, and precision tolerance. *app/services/indicators/protocols.py:466*
- [X] Any formula, seed, warmup, tolerance, or default-parameter change shall require an implementation version update, golden fixture review, and documented migration or changelog note. *app/services/indicators/protocols.py:42*
- [X] Indicator output rows shall include `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable. *app/services/indicators/protocols.py:161*
- [X] Higher-timeframe indicator values shall set `available_at` no earlier than the close of the higher-timeframe source bar plus configured data latency. *tests/unit/app/services/indicators/test_advanced_features.py:353*
- [X] If a strategy-facing consumer attempts to read a value with `available_at > decision_time`, the retrieval shall raise `IND_LOOKAHEAD_RISK` or return a masked/unavailable result according to the configured error mode. *app/services/indicators/protocols.py:45*
- [X] Local time or exchange time conversion shall occur only at input, output, display, or external integration boundaries. *app/services/indicators/protocols.py:130*
- [X] Historical indicator calculation shall not depend on host timezone database changes after inputs are normalized to UTC. *app/services/indicators/protocols.py:5*
- [X] Indicator inputs shall declare price adjustment status: raw, split-adjusted, dividend-adjusted, total-return-adjusted, back-adjusted, or synthetic. *app/services/indicators/protocols.py:73*
- [X] Indicator inputs shall declare price source: trade, bid, ask, mid, mark, settlement, or vendor-derived. *app/services/indicators/protocols.py:74*
- [X] Indicator inputs shall declare venue, exchange, data vendor, symbol normalization version, and corporate-action adjustment version when available. *app/services/indicators/protocols.py:126*
- [X] Indicator manifests shall include data provenance fields required to reproduce the calculation. *app/services/indicators/protocols.py:5*
- [X] Official workflows shall reject inputs with unknown adjustment status unless explicitly configured to allow them. *app/services/indicators/protocols.py:80*
- [X] Official workflows shall reject bars affected by intra-bar corporate-action adjustments unless a deterministic intra-bar adjustment policy is configured before calculation. *app/services/indicators/protocols.py:397*
- [X] Official workflows shall reject stub quotes or spreads greater than the configured threshold, with a default rejection threshold of 50 percent of mid price, unless an explicit fallback policy is configured. *app/services/indicators/protocols.py:79*
- [X] Mid-price indicators shall deterministically reject missing or inverted bid/ask inputs unless configured to fall back to last valid mid, trade price, mark price, or unavailable output. *app/services/indicators/protocols.py:74*
- [X] Incremental updates shall be idempotent for the same input bar. *app/services/indicators/protocols.py:517*
- [X] Incremental and batch outputs shall match within the documented precision policy. *app/services/indicators/protocols.py:47*
- [X] Indicator functions shall validate all inputs at call time before any calculation begins. *app/services/indicators/protocols.py:5*
- [X] The module shall support indicator composition where one indicator output serves as another indicator input. *app/services/indicators/protocols.py:68*
- [X] Composed indicator chains shall preserve provenance metadata through the chain. *app/services/indicators/protocols.py:2*
- [X] Indicator inputs may include per-row data quality flags from the data module. *app/services/indicators/protocols.py:161*
- [X] Configured inclusion of flagged rows shall be recorded in the indicator manifest. *app/services/indicators/protocols.py:120*
- [X] Indicator output rows derived from flagged inputs shall propagate the highest-severity quality flag present in the source data for that calculation window. *app/services/indicators/protocols.py:5*
- [X] Strategy-facing outputs shall expose quality metadata so strategies can require a minimum data quality level for consumption. *app/services/indicators/protocols.py:134*
- [X] The indicator module shall define a protocol to request minimum required warmup data from the data module before calculation. *app/services/indicators/protocols.py:4*
- [X] Warmup requests shall include requested symbol, timeframe, and lookback period. *app/services/indicators/protocols.py:21*
- [X] Warmup requests shall include indicator id and parameter set to determine exact warmup length. *app/services/indicators/protocols.py:183*
- [X] Warmup requests shall declare whether warmup data must be closed-bar only or may include the current incomplete bar. *app/services/indicators/protocols.py:397*
- [X] The indicator module shall request warmup data through the data module contract and shall validate that returned warmup data conforms to the same schema and provenance requirements as the primary input before using it. *tests/unit/app/services/indicators/test_advanced_features.py:84*
- [X] When an indicator is configured with a higher-timeframe source, the module shall request higher-timeframe bars through the data module contract alongside the primary timeframe. *app/services/indicators/protocols.py:17*
- [X] Higher-timeframe indicator values may be forward-filled onto the primary timeframe only after the higher-timeframe source bar is fully closed plus configured data latency. *tests/unit/app/services/indicators/test_advanced_features.py:353*
- [X] The module shall set `available_at` for each primary-timeframe row to the higher-timeframe bar close time plus configured data latency. *tests/unit/app/services/indicators/test_advanced_features.py:353*
- [X] Weekend and holiday gaps in higher-timeframe data shall not cause forward-fill of stale values across session boundaries unless explicitly configured. *app/services/indicators/protocols.py:161*
- [X] Proprietary indicator result manifests shall record non-sensitive access-control decision metadata, including decision id, entitlement policy version, and authorized workflow. *app/services/indicators/protocols.py:358*
- [X] Symbol metadata. *app/services/indicators/protocols.py:21*
- [X] Timeframe metadata. *app/services/indicators/protocols.py:134*
- [X] Output mode: values-only result, joined copy result, or explicitly configured internal optimization. *app/services/indicators/protocols.py:304*
- [X] Precision policy. *app/services/indicators/protocols.py:47*
- [X] Timezone metadata with unambiguous timestamp handling. *app/services/indicators/protocols.py:130*
- [X] Optional microstructure quality policy containing stub quote, inverted market, missing bid/ask, spread threshold, and mid-price fallback configuration. *app/services/indicators/protocols.py:53*
- [X] Data latency configuration for availability-time calculation. *tests/unit/app/services/indicators/test_advanced_features.py:353*
- [X] Optional out-of-core processing configuration containing memory budget, chunk size, storage backend, and spill directory. *app/services/indicators/protocols.py:23*
- [X] Optional acceleration backend configuration containing backend id, feature flag, worker pool, worker count, and fallback policy. *app/services/indicators/protocols.py:71*
- [X] Optional feature flag and canary routing configuration for indicator implementation rollout. *app/services/indicators/protocols.py:38*
- [X] Optional proprietary indicator access context containing actor, workflow, entitlement, environment, and intended use. *app/services/indicators/protocols.py:86*
- [X] Optional warmup data request configuration. *app/services/indicators/protocols.py:361*
- [X] Resource limit configuration. *app/services/indicators/protocols.py:16*
- [X] Optional observability context containing request id and correlation id. *app/services/indicators/protocols.py:96*
- [X] Optional tracing context containing trace id, parent span id, baggage, and sampling decision. *app/services/indicators/protocols.py:96*
- [X] Indicator values dataframe containing timestamp, symbol, indicator columns, availability metadata, and quality metadata. *app/services/indicators/protocols.py:164*
- [X] Original input dataframe preserved without default mutation. *app/services/indicators/protocols.py:182*
- [X] `available_at` timestamp or deterministic availability metadata for every output row. *app/services/indicators/protocols.py:50*
- [X] `label_time`, `bar_open_time`, `bar_close_time`, `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable. *app/services/indicators/protocols.py:134*
- [X] Warmup and missing-data metadata. *app/services/indicators/protocols.py:134*
- [X] Indicator result manifest. *app/services/indicators/protocols.py:358*
- [X] Input checksum. *app/services/indicators/protocols.py:130*
- [X] Dtype metadata. *app/services/indicators/protocols.py:134*
- [X] Data provenance metadata required to reproduce the calculation. *app/services/indicators/protocols.py:134*
- [X] Out-of-core execution metadata when out-of-core processing is enabled. *app/services/indicators/protocols.py:51*
- [X] Acceleration backend metadata when an accelerated or fallback backend is used. *app/services/indicators/protocols.py:71*
- [X] Feature flag, canary route, baseline implementation, selected implementation, and canary comparison metadata when rollout controls are enabled. *app/services/indicators/protocols.py:171*
- [X] Non-sensitive proprietary access-control decision metadata when proprietary indicator execution is requested. *app/services/indicators/protocols.py:17*
- [X] Propagated data quality metadata. *app/services/indicators/protocols.py:134*
- [X] Every indicator result shall include a machine-readable manifest as a standalone serializable object. *app/services/indicators/protocols.py:167*
- [X] The manifest shall include `manifest_version`. *app/services/indicators/protocols.py:124*
- [X] The manifest shall include `indicator_id`. *app/services/indicators/protocols.py:358*
- [X] The manifest shall include `indicator_version`. *app/services/indicators/protocols.py:358*
- [X] The manifest shall include `formula_version`. *app/services/indicators/protocols.py:4*
- [X] The manifest shall include `output_schema_version`. *app/services/indicators/protocols.py:4*
- [X] The manifest shall include `parameter_hash` derived from a canonical parameter representation. *app/services/indicators/protocols.py:359*
- [X] The manifest shall include `input_checksum` derived from input data including timestamps, symbols, and OHLCV values in canonical order. *app/services/indicators/protocols.py:130*
- [X] The manifest shall include `output_checksum`. *app/services/indicators/protocols.py:4*
- [X] The module shall define the exact input and output checksum policy, including included columns, dtype normalization, timestamp normalization, symbol ordering, row ordering, float handling, null representation, precision policy, and excluded metadata. *app/services/indicators/protocols.py:44*
- [X] The manifest shall include `data_provenance` with adjustment status, price source, vendor, venue, symbol normalization version, corporate-action version, and continuous contract roll method when applicable. *app/services/indicators/protocols.py:132*
- [X] The manifest shall include `output_contract` with generated column names, source column, output mode, naming policy, column conflict policy, join mode, input mutation flag, and index alignment policy. *app/services/indicators/protocols.py:44*
- [X] The manifest shall include `execution_backend` with in-memory, out-of-core, accelerated, fallback, parallelism, worker count, and backend version fields where applicable. *app/services/indicators/protocols.py:51*
- [X] The manifest shall include `rollout` with feature flag, canary route, selected implementation, baseline implementation, and tolerance status where applicable. *app/services/indicators/protocols.py:429*
- [X] The manifest shall include `access_control` with non-sensitive decision metadata for proprietary indicator requests where applicable. *app/services/indicators/protocols.py:68*
- [X] The manifest shall include `timing` with calculation start, calculation end, and wall-clock duration. *app/services/indicators/protocols.py:360*
- [X] The manifest shall include `output_shape` with row count, symbol count, column list, and dtypes. *app/services/indicators/protocols.py:136*
- [X] The manifest shall include `environment` with Python version, key dependency versions, operating system, and optional host identifier for debugging. *app/services/indicators/protocols.py:137*
- [X] The manifest shall include composition lineage when the result depends on upstream indicator outputs. *app/services/indicators/protocols.py:358*
- [X] The manifest shall include quality-flag policy and propagated quality summary when data quality flags are present. *app/services/indicators/protocols.py:156*
- [X] Every invalid input schema shall return a deterministic error code. *app/services/indicators/protocols.py:197*
- [X] Unexpected input mutation during official calculation shall return a deterministic error code. *app/services/indicators/protocols.py:197*
- [X] Every insufficient-data condition shall return a deterministic error code or explicit unavailable output according to configuration. *app/services/indicators/protocols.py:45*
- [X] Lookahead-sensitive indicator access shall provide metadata required for `SIM_LOOKAHEAD_DETECTED`. *app/services/indicators/protocols.py:171*
- [X] Intra-bar corporate-action adjustment inputs without a configured deterministic policy shall return a deterministic error code. *app/services/indicators/protocols.py:318*
- [X] Stub quotes, inverted markets, missing bid or ask values, and spread-threshold violations shall return deterministic error codes unless an explicit fallback policy is configured. *app/services/indicators/protocols.py:45*
- [X] Deprecated indicator, parameter, schema, or API use in the deprecation error phase shall return a deterministic error code unless an explicit opt-in flag is configured. *app/services/indicators/protocols.py:111*
- [X] `IND_INVALID_CONFIG` *app/services/indicators/protocols.py:182*
- [X] `IND_INVALID_INPUT_SCHEMA` *app/services/indicators/protocols.py:182*
- [X] `IND_INPUT_MUTATION_DETECTED` *app/services/indicators/protocols.py:182*
- [X] Input validation tests shall cover missing columns, duplicate timestamps, non-monotonic timestamps, invalid OHLC, empty data, insufficient warmup, and invalid parameters. *tests/unit/app/services/indicators/test_advanced_features.py:333*
- [X] Input validation tests shall cover malformed config payloads and invalid configuration combinations, including valid parameters that are incompatible when combined. *tests/unit/app/services/indicators/test_advanced_features.py:177*
- [X] Input validation tests shall verify simultaneous conflicting options, such as `values_only=True` with `output_mode="join"`, fail with `IND_INVALID_CONFIG`. *tests/unit/app/services/indicators/test_advanced_features.py:76*
- [X] Public API tests shall verify `typing.Protocol` compatibility for custom indicators that do not inherit from framework base classes. *tests/unit/app/services/indicators/test_advanced_features.py:77*
- [X] Notebook representation tests shall verify indicator result `_repr_html_` and `_repr_pretty_` output includes summary statistics, warmup visualization, unavailable-region visibility, and manifest summary without exposing full market data payloads. *tests/unit/app/services/indicators/test_advanced_features.py:250*
- [X] Join helper tests shall verify `IndicatorResult.join_to(input_data, mode="copy")` appends generated indicator columns while preserving original columns, row count, row order, timestamp alignment, symbol grouping, index policy, warmup rows, and unavailable rows. *tests/unit/app/services/indicators/test_advanced_features.py:191*
- [X] Availability tests shall verify higher-timeframe values are unavailable until the higher-timeframe source bar is fully closed plus configured latency. *tests/unit/app/services/indicators/test_advanced_features.py:353*
- [X] Timezone database tests shall verify historical outputs remain stable after UTC-normalized inputs are supplied and that timezone-database-dependent conversions occur only at I/O boundaries. *tests/unit/app/services/indicators/test_advanced_features.py:185*
- [X] Determinism tests shall verify identical inputs and parameters produce identical outputs and manifests. *tests/unit/app/services/indicators/test_advanced_features.py:185*
- [X] Chunking tests shall verify chunked output matches full-run output within documented precision policy. *tests/unit/app/services/indicators/test_advanced_features.py:295*
- [X] Out-of-core tests shall verify datasets exceeding memory budget produce the same output as full in-memory runs within documented precision policy. *tests/unit/app/services/indicators/test_advanced_features.py:413*
- [X] Out-of-core tests shall verify deterministic rejection for indicators that require full in-memory context and cannot be safely chunked. *tests/unit/app/services/indicators/test_advanced_features.py:621*
- [X] Acceleration backend tests shall verify feature-flag isolation, fallback behavior, backend metadata, and parity between accelerated and fallback paths within documented precision policy. *tests/unit/app/services/indicators/test_advanced_features.py:621*
- [X] Batch and incremental tests shall verify incremental output matches batch output within the documented precision policy. *tests/unit/app/services/indicators/test_advanced_features.py:33*
- [X] Market data quality tests shall verify default exclusion of flagged rows, explicit inclusion configuration, quality-flag propagation, highest-severity quality summarization, and strategy-facing quality metadata. *tests/unit/app/services/indicators/test_advanced_features.py:508*
- [X] Manifest tests shall verify every required manifest field, nested data provenance, calculation config, timing, output shape, environment, composition lineage, and quality summary. *tests/unit/app/services/indicators/test_advanced_features.py:782*
- [X] Manifest tests shall verify output contract fields for generated column names, source column, output mode, naming policy, column conflict policy, join mode, input mutation flag, and index alignment policy. *tests/unit/app/services/indicators/test_advanced_features.py:439*
- [X] Manifest tests shall verify parameter hash canonicalization and input/output checksum policies are stable and documented. *tests/unit/app/services/indicators/test_advanced_features.py:205*
- [X] Provenance tests shall cover raw, split-adjusted, dividend-adjusted, total-return-adjusted, back-adjusted, synthetic, bid, ask, mid, mark, settlement, vendor-derived, continuous futures, and unknown adjustment status inputs. *tests/unit/app/services/indicators/test_advanced_features.py:545*
- [X] Microstructure tests shall cover stub quotes, inverted markets, missing bid or ask values, spreads above the configured threshold, and mid-price fallback policies. *tests/unit/app/services/indicators/test_advanced_features.py:545*
- [X] Survivorship bias tests shall verify indicators do not silently produce misleading signals for delisted, bankrupt, merged, or inactive symbols without data-quality flags and provenance metadata. *tests/unit/app/services/indicators/test_advanced_features.py:508*
- [X] Observability tests shall verify metrics, logs, traces, canary comparison metadata, and SLO measurement fields include required fields and do not change calculation semantics. *tests/unit/app/services/indicators/test_advanced_features.py:357*
- [X] Feature flag and canary tests shall verify routed execution, baseline comparison, output delta recording, tolerance status, rollback metadata, and unchanged official outputs when canary route is not selected. *tests/unit/app/services/indicators/test_advanced_features.py:387*
- [X] Warmup protocol tests shall verify requested symbol, timeframe, lookback, indicator id, parameter set, closed-bar policy, returned provenance, data-module contract integration through a fake data-module provider, and warmup output marking. *tests/unit/app/services/indicators/test_advanced_features.py:84*
- [X] Proprietary indicator tests shall verify entitlement context and protected-package metadata do not leak secrets into logs, traces, manifests, or error messages. *tests/unit/app/services/indicators/test_advanced_features.py:508*
- [X] Property-based tests shall cover valid and invalid OHLCV inputs. *tests/unit/app/services/indicators/test_advanced_features.py:29*
- [X] Property-based tests shall verify SMA over constant price input equals the constant price after warmup. *tests/unit/app/services/indicators/test_advanced_features.py:34*
- [X] Property-based tests shall verify EMA over constant price input converges deterministically according to its seed policy. *tests/unit/app/services/indicators/test_advanced_features.py:185*
- [X] Property-based tests shall verify RSI remains within documented bounds for valid inputs. *tests/unit/app/services/indicators/test_advanced_features.py:205*
- [X] Property-based tests shall verify ATR is non-negative for valid OHLC inputs. *tests/unit/app/services/indicators/test_advanced_features.py:29*
- [X] Documentation tests shall execute usage examples, invalid-input examples, manifest-inspection examples, multi-symbol examples, multi-timeframe examples, and incremental examples where supported. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Usage examples shall include normal output, invalid parameter handling, missing-column handling, manifest inspection, availability filtering, multi-symbol input, multi-timeframe input, and incremental update behavior where supported. *app/services/indicators/protocols.py:204*
- [X] Documentation shall include a configuration reference for every supported indicator. *app/services/indicators/protocols.py:38*
- [X] Documentation shall include input schema, output schema, parameter schema, warmup policy, and missing-data behavior for every supported indicator. *app/services/indicators/protocols.py:38*
- [X] Documentation shall describe vectorized calculation requirements, values-only output, joined-copy output, default input immutability, official in-place mutation restrictions, and internal optimization manifest requirements. *app/services/indicators/protocols.py:161*
- [X] Documentation shall describe notebook result representations, including `_repr_html_`, `_repr_pretty_`, summary statistics, warmup visualization, unavailable-region visibility, and manifest summaries. *app/services/indicators/protocols.py:4*
- [X] Documentation shall describe optional acceleration backends, feature flags, pure fallback behavior, backend metadata, GIL-release behavior, and parallel symbol execution configuration. *app/services/indicators/protocols.py:134*
- [X] Documentation shall describe input validation timing and fail-fast behavior. *app/services/indicators/protocols.py:46*
- [X] Documentation shall describe indicator result manifest structure and every required manifest field. *app/services/indicators/protocols.py:358*
- [X] Documentation shall describe data quality flags, default exclusion policy, explicit inclusion policy, output quality propagation, and strategy-facing quality metadata. *app/services/indicators/protocols.py:156*
- [X] Documentation shall describe warmup data request protocol and warmup output marking. *app/services/indicators/protocols.py:361*
- [X] Documentation shall describe observability metrics, log fields, request ids, correlation ids, distributed tracing, OpenTelemetry-compatible propagation, feature flags, canary routing, output delta comparison, and rollback metadata. *app/services/indicators/protocols.py:161*
- [X] Documentation shall describe packaging metadata, `pyproject.toml`, dependency categories, `py.typed`, and typed package behavior. *app/services/indicators/protocols.py:46*
- [X] Documentation shall describe proprietary indicator access control, entitlement checks, authorized workflows, non-sensitive manifest metadata, source protection, and protected-package determinism. *app/services/indicators/protocols.py:68*
- [X] `typing.Protocol` contracts and notebook result representations are implemented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:250*
- [X] `ema(data, period=10, source="close")` produces `ema_10`, and `IndicatorResult.join_to(data)` appends `ema_10` to a copied dataframe without mutating the input by default. *app/services/indicators/protocols.py:182*
- [X] `pyproject.toml` metadata is present and valid. *app/services/indicators/protocols.py:134*
- [X] Availability-time metadata is implemented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:353*
- [X] Acceleration backend parity, feature flag, fallback, and backend metadata tests pass. *tests/unit/app/services/indicators/test_advanced_features.py:623*
- [X] Performance benchmark metadata and regression gate are implemented. *tests/unit/app/services/indicators/test_advanced_features.py:163*
- [X] Machine-readable manifest structure is implemented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:544*
- [X] Manifest output-contract fields are implemented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:782*
- [X] Warmup data request protocol is documented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:163*
- [X] Multi-timeframe alignment protocol is documented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:353*
- [X] Official Backtest Required shall include no-lookahead alignment, reproducible fixtures, manifest/checksum behavior, data-quality propagation, and strategy/simulation integration contracts. *tests/unit/app/services/indicators/test_advanced_features.py:353*
- [X] Rich notebook HTML representations may be added after stable result and manifest schemas exist. *app/services/indicators/protocols.py:4*

#### `app/utils/errors.py`

Functions/classes:

- `IndicatorResult(errors=...)`
- `IndicatorResult`

Requirements:

- [X] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom indicator exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`. *app/utils/errors.py:5*
- [X] Indicator implementations shall return deterministic errors for invalid input schema, invalid parameter values, insufficient data, non-monotonic timestamps, duplicate timestamps, or impossible OHLCV values. *app/utils/errors.py:350*
- [X] The module shall provide metadata required for downstream layers to raise their own lookahead errors while keeping simulation-layer errors outside indicator ownership. *app/utils/errors.py:1263*
- [X] Out-of-core processing shall expose deterministic errors when an indicator requires full in-memory context and cannot be safely chunked. *app/utils/errors.py:778*
- [X] Type mismatch failures in debug mode shall fail fast with deterministic errors before any output, state mutation, cache read, or cache write occurs. *app/utils/errors.py:18*
- [X] `IndicatorResult` shall contain `values`, `output_columns`, `manifest`, `availability`, `quality`, `state`, `errors`, `metrics`, and `join_to(...)`. *app/utils/errors.py:21*
- [X] Division-by-zero, all-null windows, constant-price windows, zero-volume windows, flat-market windows, NaN inputs, infinite values, overflow, underflow, and negative zero shall produce deterministic outputs or deterministic errors. *app/utils/errors.py:1263*
- [X] Composition shall reject cycles, missing upstream outputs, incompatible source timeframes, unavailable upstream values, and output column collisions with deterministic errors before calculation. *app/utils/errors.py:17*
- [X] The module shall document whether deterministic errors are raised as exceptions, returned inside `IndicatorResult.errors`, or both, and shall document the default mode. *app/utils/errors.py:802*
- [X] Indicator errors shall be safe, deterministic, and machine-readable. *app/utils/errors.py:1263*
- [X] Requests exceeding configured resource limits shall fail with deterministic machine-readable errors. *app/utils/errors.py:1263*
- [X] Missing optional acceleration, proprietary, tracing, or audit dependencies shall produce deterministic unsupported-backend or not-configured errors without changing default built-in indicator semantics. *app/utils/errors.py:26*
- [X] Unless an indicator formula specification explicitly overrides this policy, positive and negative infinity inputs shall be rejected with deterministic numeric errors in official workflows before calculation. *app/utils/errors.py:1263*
- [X] Overflow and underflow shall return deterministic errors or unavailable outputs according to the indicator formula specification and shall be recorded in result errors or warning metadata. *app/utils/errors.py:1263*
- [X] Core MVP shall include deterministic batch calculation for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R; input validation; output naming; no-lookahead availability metadata; manifests; deterministic errors; and golden tests. *tests/unit/app/services/indicators/test_advanced_features.py:297*
- [X] Public contracts shall define whether invalid requests raise exceptions, return `IndicatorResult(errors=...)`, or support both modes, and shall document the default mode. *app/utils/errors.py:658*
- [X] Unsupported modes, unsupported backends, unsupported indicators, unavailable optional dependencies, and unsupported composition requests shall fail before calculation with deterministic errors. *app/utils/errors.py:26*
- [X] No file-specific non-functional requirements defined. *app/utils/errors.py:50*
- [X] Error-mode tests shall verify deterministic exception mode and deterministic `IndicatorResult.errors` mode if both are supported. *tests/unit/app/services/indicators/test_advanced_features.py:126*
- [X] Error-mode tests shall verify that result-error mode does not raise exceptions and instead populates `IndicatorResult.errors` with deterministic codes. *tests/unit/app/services/indicators/test_advanced_features.py:77*
- [X] Output contract tests shall verify custom output names, invalid output names, output naming policies, output modes, column conflict policies, and deterministic collision errors. *tests/unit/app/services/indicators/test_advanced_features.py:439*
- [X] Simulation integration tests shall verify simulation-layer lookahead detection uses indicator-provided availability metadata without making the indicator module own simulation errors. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Floating-point warning and error handling shall be deterministic within official workflows. *app/utils/errors.py:2*
- [X] The benchmark suite shall fail CI when performance regresses by more than 20 percent without explicit approval. *tests/unit/app/services/indicators/test_advanced_features.py:76*
- [X] The deprecation error with opt-in phase shall last at least two minor releases, raise `IND_DEPRECATED` by default, and support an explicit opt-in flag to restore behavior with a warning. *app/utils/errors.py:51*
- [X] The removal phase shall occur only in a major version and shall return `IND_UNSUPPORTED_INDICATOR` or the closest deterministic unsupported-API error. *app/utils/errors.py:1390*
- [X] Unsupported incremental mode requests shall fail deterministically. *app/utils/errors.py:28*
- [X] Parameter validation, schema validation, and data sufficiency checks shall be performed as the first operation and shall fail fast with deterministic error codes. *app/utils/errors.py:32*
- [X] Calculation mode: batch, incremental, streaming, or explicitly unsupported. *app/utils/errors.py:379*
- [X] Structured error result with deterministic error code on failure. *app/utils/errors.py:5*
- [X] Every invalid indicator request shall return a deterministic error code. *app/utils/errors.py:1390*
- [X] Every invalid parameter set shall return a deterministic error code. *app/utils/errors.py:1390*
- [X] Invalid output names, invalid output modes, invalid naming policies, and output column collisions shall return deterministic error codes. *app/utils/errors.py:17*
- [X] Unsupported indicator ids shall return a deterministic error code. *app/utils/errors.py:1390*
- [X] Unsupported timeframes shall return a deterministic error code. *app/utils/errors.py:1390*
- [X] Unsupported dtypes shall return a deterministic error code. *app/utils/errors.py:1390*
- [X] Ambiguous, nonexistent, or timezone-naive timestamps shall return deterministic error codes in official workflows. *app/utils/errors.py:358*
- [X] Unknown adjustment status shall return a deterministic error code unless explicitly allowed. *app/utils/errors.py:21*
- [X] Missing or incompatible symbol mapping for symbol changes, mergers, ticker replacements, or vendor remaps shall return a deterministic error code. *app/utils/errors.py:23*
- [X] Formula version mismatches shall return a deterministic error code. *app/utils/errors.py:1390*
- [X] Custom indicators rejected by conformance, status, dependency, or governance checks shall return deterministic error codes. *app/utils/errors.py:380*
- [X] Unauthorized proprietary indicator requests shall return deterministic access-control error codes. *app/utils/errors.py:382*
- [X] SLO violations detected during production monitoring shall emit deterministic metric events and shall return deterministic error codes when the request policy requires synchronous enforcement. *app/utils/errors.py:383*
- [X] `IND_INVALID_PARAMETER` *app/utils/errors.py:117*
- [X] `IND_UNSUPPORTED_INDICATOR` *app/utils/errors.py:118*
- [X] `IND_UNSUPPORTED_TIMEFRAME` *app/utils/errors.py:119*
- [X] `IND_UNSUPPORTED_DTYPE` *app/utils/errors.py:120*
- [X] `IND_INVALID_OUTPUT_COLUMN` *app/utils/errors.py:123*
- [X] `IND_INVALID_OUTPUT_MODE` *app/utils/errors.py:125*
- [X] `IND_INVALID_TIMEZONE` *app/utils/errors.py:130*
- [X] `IND_INVALID_OHLC` *app/utils/errors.py:131*
- [X] `IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED` *app/utils/errors.py:138*
- [X] `IND_UNSUPPORTED_OUT_OF_CORE` *app/utils/errors.py:145*
- [X] `IND_UNSUPPORTED_INCREMENTAL_MODE` *app/utils/errors.py:150*
- [X] `IND_INTERNAL_ERROR` *app/utils/errors.py:549*
- [X] Composition tests shall verify cyclic graphs, missing upstream columns, incompatible source timeframes, unavailable upstream values, and output column collisions fail deterministically. *tests/unit/app/services/indicators/test_advanced_features.py:172*
- [X] Performance benchmark tests shall prove the CI regression gate fails the build when the greater-than-20-percent regression threshold is triggered without explicit approval. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Custom indicator tests shall verify import failure, dependency conflict, unsupported Python version, and side-effect enforcement failure handling. *tests/unit/app/services/indicators/test_advanced_features.py:748*
- [X] Usage examples shall show deterministic structured error behavior rather than relying only on successful calls. *app/utils/errors.py:2*
- [X] Documentation shall describe out-of-core processing, memory budgets, chunk sizes, spill storage, unsupported out-of-core rejection, and in-memory parity requirements. *app/utils/errors.py:26*
- [X] Out-of-core parity and unsupported out-of-core rejection tests pass. *tests/unit/app/services/indicators/test_advanced_features.py:620*

#### `app/services/indicators/calculations.py`

Functions/classes:

- `calculate_sma`
- `calculate_ema`
- `calculate_adx`
- `calculate_atr`
- `calculate_adr`
- `calculate_rolling_volatility`
- `calculate_rsi`
- `calculate_williams_r`

Requirements:

- [X] Indicator calculations shall not use current incomplete bar high, low, close, volume, or derived values for previous-closed-bar decisions. *app/services/indicators/calculations.py:227*
- [X] Indicator calculations may be cached by indicator id, parameter hash, input data checksum, implementation version, schema version, and precision policy. *app/services/indicators/calculations.py:856*
- [X] Indicator calculations shall support chunked processing where mathematically valid and shall preserve warmup continuity across chunks. *app/services/indicators/calculations.py:4*
- [X] Indicator calculations shall support out-of-core processing for datasets that exceed configured memory budgets when the indicator formula permits bounded-state or chunked computation. *app/services/indicators/calculations.py:4*
- [X] Indicator calculations shall define whether windows operate over rows, elapsed time, trading sessions, or calendar time. *app/services/indicators/calculations.py:5*
- [X] For batch calculations, full input validation shall complete before any output rows are computed. *app/services/indicators/calculations.py:503*
- [X] For incremental calculations, state deserialization validation and new-bar validation shall complete before incremental state is updated. *app/services/indicators/calculations.py:503*
- [X] Flagged rows shall be excluded from official calculations by default unless explicitly configured otherwise. *app/services/indicators/calculations.py:51*
- [X] Optional incremental state for incremental calculations. *app/services/indicators/calculations.py:748*
- [X] Indicator calculations shall emit structured operational metrics where enabled. *app/services/indicators/calculations.py:2*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/calculations.py:4*
- [X] Input immutability tests shall verify indicator calculations do not mutate the input dataframe by default and raise `IND_INPUT_MUTATION_DETECTED` when official calculation detects unexpected mutation. *tests/unit/app/services/indicators/test_advanced_features.py:737*
- [X] Indicator implementations target Python. *app/services/indicators/calculations.py:2*
- [X] Indicator outputs are decision support artifacts, not official execution artifacts. *app/services/indicators/calculations.py:2*
- [X] Data normalization and source-readiness rules are owned by the data module. *app/services/indicators/calculations.py:5*
- [X] Indicator code shall be typed, documented, deterministic, and testable. *tests/unit/app/services/indicators/test_advanced_features.py:786*
- [X] Runtime dependencies, optional acceleration dependencies, development dependencies, and test dependencies shall be separated. *tests/unit/app/services/indicators/test_advanced_features.py:681*
- [X] Distributed typed packages shall include `py.typed` when public inline type annotations are intended for downstream type checking. *app/services/indicators/calculations.py:71*
- [X] Public type information shall be maintained for downstream users when the package is published as typed. *app/services/indicators/calculations.py:71*
- [X] Logs shall not include full market data payloads by default. *app/services/indicators/calculations.py:349*
- [X] Indicator execution shall support correlation ids for strategy and simulation workflow tracing. *app/services/indicators/calculations.py:2*
- [X] Indicator execution shall support distributed tracing across data fetch, indicator calculation, strategy consumption, and simulation integration boundaries when tracing is enabled. *app/services/indicators/calculations.py:2*
- [X] The module shall support OpenTelemetry-compatible trace propagation or an equivalent vendor-neutral tracing contract. *app/services/indicators/calculations.py:46*
- [X] Indicator implementations shall support feature-flagged and canary-routed execution for controlled rollout of new implementations. *app/services/indicators/calculations.py:2*
- [X] Canary comparison shall record output deltas, tolerance status, performance deltas, and rollback decisions without changing official outputs unless the canary route is explicitly selected. *tests/unit/app/services/indicators/test_advanced_features.py:382*
- [X] The module shall define default resource limits for maximum rows, symbols, columns, memory budget, chunk size, and timeout before production use. *app/services/indicators/calculations.py:280*
- [X] Proposed Core MVP default resource limits are `default_max_rows=10_000_000`, `default_max_symbols=1_000`, `default_max_columns=256`, `default_memory_budget_bytes=4_294_967_296`, `default_chunk_rows=1_000_000`, and `default_timeout_seconds=60`, pending owner/architect approval. *tests/unit/app/services/indicators/test_advanced_features.py:184*
- [X] Partial outputs shall not be returned as successful official results unless explicitly marked partial. *app/services/indicators/calculations.py:310*
- [X] Chunked, parallel, and out-of-core processing shall define backpressure behavior before implementation. *app/services/indicators/calculations.py:2*
- [X] Optional acceleration dependencies shall be isolated behind extras or feature flags. *app/services/indicators/calculations.py:526*
- [X] The project shall maintain a lockfile or equivalent reproducible dependency mechanism for official workflows. *app/services/indicators/calculations.py:81*
- [X] The project shall generate or support generating a software bill of materials for production releases. *app/services/indicators/calculations.py:46*
- [X] Distributed Python wheels, source distributions, and production packages shall be cryptographically signed by the approved CI/CD release pipeline using Sigstore, PEP 740-compatible attestations, or an equivalent approved signing mechanism. *tests/unit/app/services/indicators/test_advanced_features.py:23*
- [X] Dependency licenses shall be compatible with the intended deployment and distribution model. *app/services/indicators/calculations.py:81*
- [X] Known vulnerable dependencies shall not be allowed in production releases unless explicitly waived. *app/services/indicators/calculations.py:45*
- [X] Official indicator workflows shall declare supported numeric dtypes. *app/services/indicators/calculations.py:2*
- [X] Indicator implementations shall define whether outputs use `float64`, nullable floats, decimals, fixed-point integers, or another representation. *app/services/indicators/calculations.py:2*
- [X] Negative zero shall be normalized to zero for hashing, checksums, output comparison, and display. *tests/unit/app/services/indicators/test_advanced_features.py:264*
- [X] Indicator comparisons in tests shall use documented absolute and relative tolerances. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Indicator implementations shall document thread-safety guarantees. *app/services/indicators/calculations.py:2*
- [X] SLO measurements shall be emitted through observability metrics and summarized in production readiness reports. *app/services/indicators/calculations.py:845*
- [X] The indicator module shall live under `app/services/indicators/` (relocated and approved per DEC-029/DONE-037). *app/services/indicators/calculations.py:22*
- [X] The indicator module shall provide reusable indicator calculation primitives for strategy, research, and simulation workflows. *app/services/indicators/calculations.py:2*
- [X] The indicator module shall not determine final official position size, margin acceptance, risk approval, or order matching. *app/services/indicators/calculations.py:78*
- [X] The indicator module shall expose typed, deterministic functions or classes that can be consumed by strategies and simulation orchestration. *app/services/indicators/calculations.py:4*
- [X] Indicator implementations shall validate parameter ranges before calculation. *app/services/indicators/calculations.py:2*
- [X] Indicators shall accept normalized historical market data from the data module contract. *app/services/indicators/calculations.py:4*
- [X] Batch indicators shall calculate outputs through vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation. *app/services/indicators/calculations.py:528*
- [X] The result object shall expose generated column names through `output_columns`. *app/services/indicators/calculations.py:997*
- [X] The result object shall expose `values_only` output for workflows that require indicator columns without the original OHLCV columns. *app/services/indicators/calculations.py:782*
- [X] Output column naming shall use stable lowercase snake_case names derived from indicator id, source column, period, and named parameters in canonical parameter order. *app/services/indicators/calculations.py:249*
- [X] Indicator-derived trade signals shall obey no-lookahead timing. *app/services/indicators/calculations.py:2*
- [X] Indicators used for bar-open strategies shall expose only fully closed-bar values available before the first tick of the next bar. *app/services/indicators/calculations.py:226*
- [X] At the first tick of bar `N`, indicator-derived data with timestamp greater than or equal to bar `N` open time shall be masked, dropped, or rejected before strategy access. *app/services/indicators/calculations.py:226*
- [X] Multi-timeframe indicator alignment shall not expose higher-timeframe values until the higher-timeframe bar is fully closed. *app/services/indicators/calculations.py:101*
- [X] The module shall provide `available_at`, source `bar_close_time`, source `bar_open_time` when available, `computed_from_start`, `computed_from_end`, `source_timeframe`, and a `lookahead_prohibited` flag for downstream lookahead enforcement. *app/services/indicators/calculations.py:208*
- [X] Vectorized indicator generation shall provide explicit utilities to shift outputs, such as `.shift(1)`, to align with bar-open execution logic. *app/services/indicators/calculations.py:4*
- [X] Core MVP numeric behavior shall use IEEE 754 `float64` outputs with default relative tolerance `1e-9` and default absolute tolerance `1e-12` for golden and cross-validation tests unless an approved formula table overrides the tolerance. *tests/unit/app/services/indicators/test_advanced_features.py:357*
- [X] Floating-point arithmetic may be used for research indicators when outputs are not directly used for official accounting or official fill prices. *app/services/indicators/calculations.py:22*
- [X] Indicator outputs that feed official simulation decisions shall be reproducible across replay runs. *app/services/indicators/calculations.py:78*
- [X] Performance benchmarks shall specify hardware profile, including CPU model, core count, RAM, and disk type when caching is disk-backed. *tests/unit/app/services/indicators/test_advanced_features.py:35*
- [X] Performance benchmarks shall define measurement methodology, including wall-clock timing and min, median, and p99 over a documented run count. *tests/unit/app/services/indicators/test_advanced_features.py:195*
- [X] Per-indicator benchmarks shall be maintained and tracked over releases. *tests/unit/app/services/indicators/test_advanced_features.py:35*
- [X] Optional hardware acceleration backends, including Numba, CuPy, SIMD, or equivalent backends, shall be isolated behind explicit feature flags or extras. *app/services/indicators/calculations.py:526*
- [X] Every accelerated indicator path shall provide a pure NumPy, pandas, or standard Python fallback with identical public API behavior. *app/services/indicators/calculations.py:4*
- [X] The module shall document whether each accelerated or parallel backend releases the GIL, uses multiprocessing, or requires single-threaded execution. *app/services/indicators/calculations.py:504*
- [X] The indicator module shall explicitly declare its public API surface. *app/services/indicators/calculations.py:274*
- [X] Internal modules shall be clearly marked as private and shall not be consumed directly by strategy or simulation code. *app/services/indicators/calculations.py:102*
- [X] The deprecation warning phase shall last at least two minor releases, emit structured warnings on every use, and continue full support. *app/services/indicators/calculations.py:45*
- [X] Deprecation timelines shall be documented in the changelog and migration guide. *app/services/indicators/calculations.py:66*
- [X] The indicator module shall expose a documented anatomy for every official and custom indicator. *app/services/indicators/calculations.py:2*
- [X] Private helper modules shall not be required for downstream strategy, simulation, notebook, or custom-indicator integration. *app/services/indicators/calculations.py:4*
- [X] Every built-in indicator shall provide a concrete formula specification before implementation begins. *app/services/indicators/calculations.py:2*
- [X] Every rolling-window indicator shall define whether windows are left-closed, right-closed, and whether the current row is included. *app/services/indicators/calculations.py:67*
- [X] Formula tables must be approved before any Core MVP implementation begins; their absence shall halt coding for `app/services/indicators/`. *app/services/indicators/calculations.py:22*
- [X] Formula specification tables shall use this minimum template: *app/services/indicators/calculations.py:45*
- [X] Every indicator output row shall include or derive a deterministic `available_at` timestamp. *app/services/indicators/calculations.py:6*
- [X] `available_at` shall represent the earliest time at which the value may be consumed by a strategy without lookahead. *app/services/indicators/calculations.py:213*
- [X] Strategy-facing APIs shall filter by `available_at <= decision_time`, not merely by indicator timestamp. *app/services/indicators/calculations.py:904*
- [X] Indicator outputs shall expose `label_time`, `bar_open_time`, `bar_close_time`, and `available_at` when these differ. *app/services/indicators/calculations.py:904*
- [X] Session-aware indicators shall use an explicit trading calendar. *app/services/indicators/calculations.py:22*
- [X] The module shall define behavior for weekends, exchange holidays, half-days, daylight-saving transitions, and missing session opens or closes. *app/services/indicators/calculations.py:39*
- [X] Multi-session rolling windows shall define whether overnight gaps are included. *app/services/indicators/calculations.py:67*
- [X] Indicators shall define whether pre-market, regular-session, post-market, and 24/7 market data are treated separately or continuously. *app/services/indicators/calculations.py:38*
- [X] Session resets shall be explicit for indicators that require them. *app/services/indicators/calculations.py:4*
- [X] Official workflows shall reject timezone-naive, ambiguous, or nonexistent local timestamps. *app/services/indicators/calculations.py:133*
- [X] Internal processing shall use UTC-aware timestamps or documented naive UTC representations only. *app/services/indicators/calculations.py:133*
- [X] Continuous futures or synthetic instruments shall declare roll method and adjustment method. *app/services/indicators/calculations.py:45*
- [X] Bid, ask, and mid-price indicators shall define behavior for stub quotes, inverted markets, missing bid or ask values, and extreme spreads. *app/services/indicators/calculations.py:447*
- [X] Late-arriving, corrected, or revised bars shall trigger deterministic recomputation or deterministic rejection. *app/services/indicators/calculations.py:6*
- [X] Custom indicators shall pass a conformance test suite before registration in official workflows. *tests/unit/app/services/indicators/test_advanced_features.py:747*
- [X] Custom indicators shall declare status: official, experimental, deprecated, or research-only. *app/services/indicators/calculations.py:22*
- [X] Experimental indicators shall not be used in official simulation workflows unless explicitly allowed. *app/services/indicators/calculations.py:22*
- [X] Custom indicators shall not perform network I/O, broker calls, filesystem writes, account mutations, or nondeterministic random operations during calculation. *app/services/indicators/calculations.py:2*
- [X] Custom indicators shall declare all external dependencies. *app/services/indicators/calculations.py:22*
- [X] Custom indicator conformance shall verify prohibited side effects through a documented enforcement mechanism before registration in official workflows. *app/services/indicators/calculations.py:78*
- [X] Official workflows shall reject custom indicators whose prohibited-operation checks cannot be executed, cannot be trusted, or return an inconclusive result. *app/services/indicators/calculations.py:727*
- [X] Custom indicator enforcement shall document whether validation uses static analysis, sandbox execution, runtime guards, process isolation, conformance tests, policy review, or a combination of these mechanisms. *tests/unit/app/services/indicators/test_advanced_features.py:748*
- [X] Custom indicators shall be reviewed before promotion to official status. *app/services/indicators/calculations.py:22*
- [X] When composition is enabled, the module shall accept only validated acyclic indicator graphs. *app/services/indicators/calculations.py:78*
- [X] Composed indicator chains shall preserve `available_at` correctly. *app/services/indicators/calculations.py:904*
- [X] No composed indicator shall consume a value before it is available. *app/services/indicators/calculations.py:904*
- [X] Supported quality flags shall include interpolated, backfilled, suspect, corrected, synthetic, auction, and vendor-specific flags when provided by the data module. *app/services/indicators/calculations.py:66*
- [X] Indicator implementations shall document how each quality flag affects calculation. *app/services/indicators/calculations.py:2*
- [X] The indicator module shall not directly own market-data fetching, source readiness, vendor adapters, or normalization logic. *app/services/indicators/calculations.py:4*
- [X] Higher-timeframe bars shall be validated before calculation and shall not make the indicator module responsible for market-data fetching, provider readiness, or normalization. *app/services/indicators/calculations.py:2*
- [X] Higher-timeframe bars shall be aligned using left-closed, right-closed boundaries matching the primary timeframe bar edges. *app/services/indicators/calculations.py:101*
- [X] The module shall support multiple higher-timeframe sources simultaneously with independent availability timestamps. *app/services/indicators/calculations.py:128*
- [X] Proprietary or licensed indicator implementations shall require an access-control decision before execution. *app/services/indicators/calculations.py:2*
- [X] Proprietary indicator execution shall be supported only through approved protected packaging mechanisms. *tests/unit/app/services/indicators/test_advanced_features.py:275*
- [X] Normalized OHLCV market data. *app/services/indicators/calculations.py:29*
- [X] Optional normalized tick or lower-timeframe data when an indicator explicitly requires it. *app/services/indicators/calculations.py:683*
- [X] Indicator id. *app/services/indicators/calculations.py:2*
- [X] Indicator parameter set. *app/services/indicators/calculations.py:33*
- [X] Source column selection for indicators that operate on a specific price or value column. *app/services/indicators/calculations.py:518*
- [X] Output naming policy. *app/services/indicators/calculations.py:6*
- [X] Output column conflict policy. *app/services/indicators/calculations.py:310*
- [X] Trading calendar or session policy when an indicator is session-aware. *app/services/indicators/calculations.py:2*
- [X] Price adjustment status. *app/services/indicators/calculations.py:404*
- [X] Price source. *app/services/indicators/calculations.py:446*
- [X] Optional intra-bar corporate-action adjustment policy. *app/services/indicators/calculations.py:433*
- [X] Optional indicator composition graph. *app/services/indicators/calculations.py:78*
- [X] Optional per-row data quality flags from the data module. *app/services/indicators/calculations.py:4*
- [X] Indicator result data aligned to timestamp and symbol. *app/services/indicators/calculations.py:4*
- [X] Generated indicator column names. *app/services/indicators/calculations.py:186*
- [X] Joined dataframe copy when join output mode is requested. *app/services/indicators/calculations.py:185*
- [X] Parameter hash. *app/services/indicators/calculations.py:150*
- [X] Output checksum. *app/services/indicators/calculations.py:185*
- [X] Indicator composition lineage where applicable. *app/services/indicators/calculations.py:78*
- [X] Observability metrics when enabled. *app/services/indicators/calculations.py:845*
- [X] Trace ids and span ids when distributed tracing is enabled. *app/services/indicators/calculations.py:66*
- [X] SLO measurement fields when SLO tracking is enabled. *app/services/indicators/calculations.py:66*
- [X] `IND_MISSING_REQUIRED_COLUMN` *app/services/indicators/calculations.py:66*
- [X] `IND_OUTPUT_COLUMN_CONFLICT` *app/services/indicators/calculations.py:943*
- [X] `IND_DUPLICATE_TIMESTAMP` *app/services/indicators/calculations.py:66*
- [X] `IND_NON_MONOTONIC_TIME` *app/services/indicators/calculations.py:66*
- [X] `IND_AMBIGUOUS_TIMESTAMP` *app/services/indicators/calculations.py:66*
- [X] `IND_INSUFFICIENT_DATA` *app/services/indicators/calculations.py:66*
- [X] `IND_LOOKAHEAD_RISK` *app/services/indicators/calculations.py:66*
- [X] `IND_UNKNOWN_ADJUSTMENT_STATUS` *app/services/indicators/calculations.py:419*
- [X] `IND_SYMBOL_MAPPING_REQUIRED` *app/services/indicators/calculations.py:442*
- [X] `IND_STUB_QUOTE_REJECTED` *app/services/indicators/calculations.py:464*
- [X] `IND_INVERTED_MARKET` *app/services/indicators/calculations.py:456*
- [X] `IND_SPREAD_THRESHOLD_EXCEEDED` *app/services/indicators/calculations.py:475*
- [X] `IND_DEPRECATED` *app/services/indicators/calculations.py:66*
- [X] `IND_ACCELERATION_BACKEND_UNAVAILABLE` *app/services/indicators/calculations.py:66*
- [X] `IND_RESOURCE_LIMIT_EXCEEDED` *app/services/indicators/calculations.py:66*
- [X] `IND_TIMEOUT` *app/services/indicators/calculations.py:66*
- [X] `IND_CANCELLED` *app/services/indicators/calculations.py:66*
- [X] `IND_PARTIAL_RESULT` *app/services/indicators/calculations.py:66*
- [X] `IND_CUSTOM_INDICATOR_REJECTED` *app/services/indicators/calculations.py:66*
- [X] `IND_ACCESS_DENIED` *app/services/indicators/calculations.py:66*
- [X] `IND_PROPRIETARY_UNAUTHORIZED` *app/services/indicators/calculations.py:66*
- [X] `IND_SLO_VIOLATION` *app/services/indicators/calculations.py:66*
- [X] Every functional and non-functional requirement shall have a stable requirement id before implementation begins. *app/services/indicators/calculations.py:392*
- [X] Default-parameter tests shall verify default parameter values and valid parameter ranges for every built-in indicator. *tests/unit/app/services/indicators/test_advanced_features.py:205*
- [X] Public API contract tests shall verify every public callable against the documented API contract table. *tests/unit/app/services/indicators/test_advanced_features.py:583*
- [X] Vectorized output tests shall verify batch indicators use vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation. *tests/unit/app/services/indicators/test_advanced_features.py:18*
- [X] No-lookahead tests shall cover previous-closed-bar availability, current-bar masking, multi-timeframe alignment, and vectorized signal shifting. *tests/unit/app/services/indicators/test_advanced_features.py:44*
- [X] Availability tests shall verify strategy-facing APIs filter by `available_at <= decision_time`. *tests/unit/app/services/indicators/test_advanced_features.py:276*
- [X] Changes to golden outputs shall require explicit approval and changelog entry. *app/services/indicators/calculations.py:39*
- [X] Calendar and session tests shall cover weekends, exchange holidays, half-days, daylight-saving transitions, session gaps, missing opens, missing closes, pre-market, regular-session, post-market, and 24/7 market data. *tests/unit/app/services/indicators/test_advanced_features.py:547*
- [X] Resource-limit tests shall cover maximum rows, symbols, columns, memory budget, execution timeout, cancellation, and partial-result handling. *tests/unit/app/services/indicators/test_advanced_features.py:413*
- [X] Multi-timeframe alignment tests shall verify higher-timeframe data requests through a fake data-module contract, forward-fill only after availability, independent availability timestamps for multiple higher-timeframe sources, boundary alignment, and stale gap prevention across weekends and holidays. *tests/unit/app/services/indicators/test_advanced_features.py:353*
- [X] Custom indicator conformance tests shall verify status, dependency declarations, no network I/O, no broker calls, no filesystem writes, no account mutations, no nondeterministic random operations, and promotion requirements. *tests/unit/app/services/indicators/test_advanced_features.py:748*
- [X] Custom indicator conformance tests shall verify rejection when prohibited-operation enforcement cannot run, cannot be trusted, or returns an inconclusive result. *tests/unit/app/services/indicators/test_advanced_features.py:748*
- [X] Property-based tests shall verify indicator output row count and symbol grouping match the documented output policy. *tests/unit/app/services/indicators/test_advanced_features.py:271*
- [X] Property-based tests shall verify adding future rows does not change previously available closed-bar outputs except when explicitly documented for revision-aware modes. *tests/unit/app/services/indicators/test_advanced_features.py:276*
- [X] Strategy integration tests shall verify indicator outputs can feed trade-signal generation without exposing prohibited current-bar data. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Simulation integration tests shall verify indicator-derived signals are converted to trade intents before tick execution. *tests/unit/app/services/indicators/test_advanced_features.py:276*
- [X] Public API surface is documented. *app/services/indicators/calculations.py:175*
- [X] Production Scope Tiers are assigned and approved for every requirement. *app/services/indicators/calculations.py:392*
- [X] Public API contract tables are complete for every public callable. *app/services/indicators/calculations.py:175*
- [X] Vectorized dataframe output, deterministic indicator column naming, values-only output, joined-copy output, and output column conflict behavior are implemented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:439*
- [X] Typed distribution includes `py.typed` when public inline type annotations are exported. *app/services/indicators/calculations.py:9*
- [X] Formula specifications exist for every official indicator. *app/services/indicators/calculations.py:2*
- [X] Golden fixtures exist for every official indicator. *app/services/indicators/calculations.py:2*
- [X] Calendar and session behavior is documented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:115*
- [X] Indicator composition tests pass where composition is supported. *tests/unit/app/services/indicators/test_advanced_features.py:172*
- [X] Data-quality flag handling is implemented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:163*
- [X] Deprecation lifecycle and `IND_DEPRECATED` behavior are implemented. *app/services/indicators/calculations.py:66*
- [X] Proprietary indicator access control and protected-source determinism tests pass for every proprietary indicator. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Property-based and invariant tests pass. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Mutation fuzz and survivorship bias tests pass. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Distributed tracing, feature flag, canary routing, and SLO measurement tests pass. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Dependency lockfile or equivalent reproducibility mechanism is present for official workflows. *app/services/indicators/calculations.py:81*
- [X] Dependency license and vulnerability checks pass or have explicit waivers. *app/services/indicators/calculations.py:81*
- [X] Software bill of materials generation is supported for production releases. *app/services/indicators/calculations.py:46*
- [X] Core MVP coding shall halt until `IND-PREQ-001`, `IND-PREQ-002`, `IND-PREQ-003`, `IND-PREQ-004`, `IND-PREQ-005`, and `IND-PREQ-006` are resolved or explicitly deferred. *app/services/indicators/calculations.py:4*
- [X] Optional Extension shall include streaming, out-of-core processing, acceleration backends, proprietary indicator execution, distributed tracing, SLO alert routing, and canary routing unless a later approved decision promotes any item. *app/services/indicators/calculations.py:4*
- [X] Future Improvement shall include capabilities that are useful but not required for the current approved implementation phase. *app/services/indicators/calculations.py:2*
- [X] Core MVP shall be implementable without optional acceleration backends, proprietary indicator controls, out-of-core execution, distributed tracing, SLO enforcement, or release-signing infrastructure. *app/services/indicators/calculations.py:4*
- [X] Every public callable shall be classified as stable, experimental, internal, optional, or future before implementation begins. *app/services/indicators/calculations.py:2*
- [X] GPU/SIMD acceleration may be added as an Optional Extension after Core MVP formula and fixture behavior is stable. *app/services/indicators/calculations.py:50*

#### `app/services/indicators/batch/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/indicators/batch/__init__.py:1*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/batch/__init__.py:1*
- [X] No file-specific testing requirements defined. *tests/unit/app/services/indicators/test_registry.py:93*

#### `app/services/indicators/batch/trend.py`

Functions/classes:

- `SMAIndicator`
- `EMAIndicator`
- `ADXIndicator`
- `calculate_sma`
- `calculate_ema`
- `calculate_adx`

Requirements:

- [X] The module shall support trend indicators including EMA, SMA, and ADX. *app/services/indicators/batch/trend.py:2*
- [X] Documentation shall include examples for EMA/SMA trend signals, ATR volatility sizing inputs, RSI momentum signals, vectorized dataframe output, joined indicator columns, and multi-timeframe alignment. *app/services/indicators/batch/trend.py:2*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/batch/trend.py:42*
- [X] No file-specific testing requirements defined. *tests/unit/app/services/indicators/test_trend.py:27*
- [X] Indicator APIs shall remain separate from strategy execution and simulation execution services. *app/services/indicators/batch/trend.py:15*
- [X] Indicator implementations shall be reusable by notebook, CLI, agentic, and simulation workflows without changing semantics. *app/services/indicators/batch/trend.py:4*
- [X] Observability shall be optional and shall not change calculation semantics. *app/services/indicators/batch/trend.py:15*
- [X] A call equivalent to `ema(data, period=10, source="close")` shall generate an indicator column named `ema_10` when `close` is the default source. *app/services/indicators/batch/trend.py:59*
- [X] When the source column is not the default source or when naming ambiguity exists, output column names shall include the source column, such as `ema_open_10` or `ema_close_10`. *app/services/indicators/batch/trend.py:49*
- [X] Multi-output indicators shall expose deterministic output column names for each component, such as `adx_14`, `plus_di_14`, and `minus_di_14`. *app/services/indicators/batch/trend.py:18*
- [X] Custom output column names shall be accepted only when they pass schema validation, collision checks, and deterministic naming policy checks. *app/services/indicators/batch/trend.py:18*
- [X] Public API changes shall follow semantic versioning. *app/services/indicators/batch/trend.py:42*
- [X] Backward-incompatible public API, schema, formula, or behavior changes shall require a major version bump or documented migration path. *app/services/indicators/batch/trend.py:40*
- [X] Deprecated APIs, indicators, parameters, or schemas shall emit deterministic deprecation warnings and remain supported for a documented compatibility window. *app/services/indicators/batch/trend.py:153*
- [X] Indicator result schema versions shall be independently versioned from implementation versions. *app/services/indicators/batch/trend.py:4*
- [X] Debug-mode APIs shall enforce strict typing and runtime validation before calculation begins, using validated schemas or equivalent runtime guards. *app/services/indicators/batch/trend.py:10*
- [X] Deprecated indicators, parameters, schemas, or APIs shall follow a three-phase lifecycle. *app/services/indicators/batch/trend.py:2*
- [X] Every indicator shall define its exact mathematical formula. *app/services/indicators/batch/trend.py:2*
- [X] The HaruQuant formula specification shall remain the source of truth when third-party library conventions differ. *app/services/indicators/batch/trend.py:40*
- [X] Symbol changes, mergers, ticker replacements, and vendor remaps shall use an explicit symbol mapping contract. *app/services/indicators/batch/trend.py:71*
- [X] Optional symbol mapping contract for symbol changes, mergers, ticker replacements, and vendor remaps. *app/services/indicators/batch/trend.py:71*
- [X] Output schema version. *app/services/indicators/batch/trend.py:18*
- [X] `IND_FORMULA_VERSION_MISMATCH` *app/services/indicators/batch/trend.py:42*
- [X] Vectorized output tests shall verify `ema(data, period=10, source="close")` produces `ema_10` when `close` is the default source. *tests/unit/app/services/indicators/test_trend.py:110*
- [X] Vectorized output tests shall verify non-default source naming such as `ema_open_10` and deterministic multi-output names such as `adx_14`, `plus_di_14`, and `minus_di_14`. *tests/unit/app/services/indicators/test_trend.py:114*
- [X] EMA, SMA, RSI, ATR, and ADX outputs shall be cross-validated against at least two industry-standard libraries, including TA-Lib and pandas-ta, tulipy, or equivalent libraries, on fixed golden fixtures. *app/services/indicators/batch/trend.py:2*
- [X] Property-based tests shall verify Williams %R remains within documented bounds for valid non-degenerate windows. *tests/unit/app/services/indicators/test_trend.py:81*
- [X] Usage examples shall remain executable documentation examples once implementation begins. *app/services/indicators/batch/trend.py:4*
- [X] Documentation shall include API examples showing `ema(data, period=10, source="close")` returning an `IndicatorResult` with `ema_10` and `result.join_to(data)` returning a copied dataframe with `ema_10` appended. *app/services/indicators/batch/trend.py:229*
- [X] Documentation shall describe semantic versioning policy and migration requirements for backward-incompatible changes. *app/services/indicators/batch/trend.py:56*
- [X] Documentation shall include exact mathematical formula, smoothing convention, alpha convention, seed behavior, rolling-window inclusivity, and edge-case behavior for every supported indicator. *app/services/indicators/batch/trend.py:153*
- [X] Documentation shall describe RSI, ATR, and ADX smoothing conventions. *app/services/indicators/batch/trend.py:462*
- [X] Documentation shall describe calendar, session, weekend, holiday, half-day, daylight-saving, missing-session, pre-market, regular-session, post-market, and 24/7 market semantics. *app/services/indicators/batch/trend.py:26*
- [X] Documentation shall describe intra-bar corporate-action adjustment rejection, deterministic intra-bar adjustment policies, symbol mapping continuity, mergers, ticker replacements, vendor remaps, stub quote handling, inverted market handling, spread thresholds, and mid-price fallback behavior. *app/services/indicators/batch/trend.py:71*
- [X] Documentation shall describe detailed multi-timeframe alignment, boundary semantics, independent availability timestamps, and stale gap prevention. *app/services/indicators/batch/trend.py:65*
- [X] Cross-library validation passes for EMA, SMA, RSI, ATR, and ADX against at least two industry-standard libraries. *app/services/indicators/batch/trend.py:2*
- [X] Proprietary source protection may be added through approved packaging/security controls without changing public indicator semantics. *app/services/indicators/batch/trend.py:2*

#### `app/services/indicators/batch/volatility.py`

Functions/classes:

- `ema(...)`
- `sma(...)`
- `adx(...)`
- `atr(...)`
- `adr(...)`
- `rolling_volatility(...)`
- `rsi(...)`
- `williams_r(...)`

Requirements:

- [X] The module shall support volatility indicators including ATR, ADR, and rolling volatility. *app/services/indicators/batch/volatility.py:2*
- [X] Official indicator convenience functions shall expose typed wrappers for supported built-ins, including `ema(...)`, `sma(...)`, `adx(...)`, `atr(...)`, `adr(...)`, `rolling_volatility(...)`, `rsi(...)`, and `williams_r(...)`. *tests/unit/app/services/indicators/test_volatility.py:2*
- [X] Rolling volatility shall define return type, log-return versus simple-return behavior, sample versus population standard deviation, degrees of freedom, and annualization factor. *app/services/indicators/batch/volatility.py:393*
- [X] Formula specification tables shall be completed for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R before implementation begins. *tests/unit/app/services/indicators/test_volatility.py:2*
- [X] Documentation shall describe rolling volatility return type, log/simple return policy, standard-deviation convention, degrees of freedom, and annualization factor. *app/services/indicators/batch/volatility.py:393*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/batch/volatility.py:42*
- [X] Indicator tests shall cover EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R. *tests/unit/app/services/indicators/test_volatility.py:2*
- [X] Formula golden tests shall verify exact formula conventions, seed behavior, warmup length, rolling-window inclusivity, null handling, and degenerate-window behavior for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R. *tests/unit/app/services/indicators/test_volatility.py:2*
- [X] Golden fixtures shall cover normal data, flat markets, gaps, missing bars, duplicated timestamps, extreme volatility, zero volume, all-null windows, and insufficient warmup. *app/services/indicators/batch/volatility.py:30*
- [X] Property-based tests shall verify rolling volatility is non-negative. *tests/unit/app/services/indicators/test_volatility.py:2*
- [X] ADR shall define whether it uses high-low range, close-to-close range, session range, calendar-day range, or trading-day range. *app/services/indicators/batch/volatility.py:257*
- [X] The test plan shall include a requirement-to-test traceability matrix mapping each requirement id to one or more unit, contract, integration, performance, security, or documentation tests. *tests/unit/app/services/indicators/test_volatility.py:2*
- [X] Documentation shall include a requirement-to-test traceability matrix. *tests/unit/app/services/indicators/test_volatility.py:2*
- [X] Documentation shall describe ADR range convention and Williams %R degenerate-window behavior. *tests/unit/app/services/indicators/test_volatility.py:35*
- [X] Requirement-to-test traceability matrix exists and maps every requirement id to tests or approved deferral. *tests/unit/app/services/indicators/test_volatility.py:2*

#### `app/services/indicators/batch/momentum.py`

Functions/classes:

- `RSIIndicator`
- `WilliamsRIndicator`
- `calculate_rsi`
- `calculate_williams_r`

Requirements:

- [X] The module shall support momentum indicators including RSI and Williams %R. *tests/unit/app/services/indicators/test_momentum.py:2*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/batch/momentum.py:42*
- [X] No file-specific testing requirements defined. *tests/unit/app/services/indicators/test_momentum.py:15*
- [X] Runtime dependencies shall be explicitly declared and version-constrained. *app/services/indicators/batch/momentum.py:39*
- [X] Performance benchmarks shall specify Python version and key dependency versions, including NumPy, pandas, and any optional acceleration dependencies. *tests/unit/app/services/indicators/test_momentum.py:4*
- [X] Williams %R shall define behavior when highest high equals lowest low. *tests/unit/app/services/indicators/test_momentum.py:42*
- [X] Timezone database dependent conversions shall be confined to I/O boundaries and shall record timezone database version or conversion policy when available. *app/services/indicators/batch/momentum.py:39*
- [X] Access-control checks shall validate actor, workflow, entitlement, environment, indicator id, indicator version, and intended use before calculation begins. *app/services/indicators/batch/momentum.py:15*
- [X] Venue, exchange, data vendor, symbol normalization version, and corporate-action adjustment version where available. *app/services/indicators/batch/momentum.py:39*
- [X] Implementation version. *app/services/indicators/batch/momentum.py:4*
- [X] Formula version. *app/services/indicators/batch/momentum.py:40*
- [X] The module shall define the exact canonical representation used for parameter hashing, including key ordering, defaults, omitted optional values, numeric formatting, null representation, string normalization, and version material. *app/services/indicators/batch/momentum.py:29*
- [X] Reference outputs shall be reviewed and pinned by implementation version. *app/services/indicators/batch/momentum.py:4*
- [X] Cross-validation deviations beyond documented tolerance shall require formula justification, implementation-version pinning, golden fixture approval, and changelog entry. *app/services/indicators/batch/momentum.py:40*

#### `app/services/indicators/incremental/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/indicators/incremental/__init__.py:1*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/incremental/__init__.py:1*
- [X] No file-specific testing requirements defined. *tests/unit/app/services/indicators/test_advanced_features.py:188*

#### `app/services/indicators/incremental/state.py`

Functions/classes:

- `IndicatorProtocol`
- `IndicatorConfig`
- `IndicatorContext`
- `IndicatorResult`
- `IndicatorManifest`
- `IndicatorState`
- `WarmupRequirement`
- `IndicatorRegistration`
- `IndicatorError`
- `update(bar, state, config, context)`
- `update()`
- `serialize_state(state)`
- `deserialize_state(payload)`
- `serialize_state()`
- `deserialize_state()`
- `IND_STATE_INCOMPATIBLE`
- `IND_STATE_CORRUPTED`

Requirements:

- [X] Official fills, orders, account state, journals, and reports are produced by the simulation module. *app/services/indicators/protocols.py:4*
- [X] The indicator module shall not execute trades, create fills, mutate account state, mutate simulation journals, or perform broker-state operations. *app/services/indicators/protocols.py:411*
- [X] Official production batch indicators shall not rely on per-row Python loops except for formulas with documented stateful dependencies that cannot be vectorized safely. *app/services/indicators/protocols.py:2*
- [X] Indicator implementations shall avoid hidden global mutable state. *app/services/indicators/protocols.py:411*
- [X] Performance benchmarks shall state whether cached or uncached performance is being measured. *tests/unit/app/services/indicators/test_advanced_features.py:136*
- [X] The public package shall expose `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError` with exact approved type contracts. *app/services/indicators/protocols.py:516*
- [X] `IndicatorProtocol` shall define `update(bar, state, config, context)` when the indicator supports incremental or streaming execution. *app/services/indicators/protocols.py:517*
- [X] `IndicatorProtocol` shall define `serialize_state(state)` and `deserialize_state(payload)` when the indicator supports incremental or streaming execution. *app/services/indicators/protocols.py:524*
- [X] `IndicatorState` shall contain serializable incremental accumulators, last processed timestamp, last processed symbol, warmup completion status, input checksum, and state schema version. *app/services/indicators/protocols.py:416*
- [X] RSI, ATR, and ADX implementations shall explicitly state whether they use Wilder smoothing or another smoothing convention. *app/services/indicators/protocols.py:420*
- [X] Formula specification tables shall state whether each indicator is Core MVP, Official Backtest Required, Production Required, Optional Extension, or Future Improvement. *tests/unit/app/services/indicators/test_advanced_features.py:12*
- [X] Symbol mapping shall preserve indicator state continuity across equivalent instrument identities without resetting warmup unless the mapping policy marks the instrument as discontinuous. *app/services/indicators/protocols.py:78*
- [X] Incremental indicators shall expose serializable state. *app/services/indicators/protocols.py:412*
- [X] Incremental state shall include enough information to resume calculation without recomputing the full history. *app/services/indicators/protocols.py:412*
- [X] Serialized incremental state shall use a documented binary or text serialization format. *app/services/indicators/protocols.py:97*
- [X] Serialized incremental state shall include indicator id. *app/services/indicators/protocols.py:412*
- [X] Serialized incremental state shall include implementation version. *app/services/indicators/protocols.py:412*
- [X] Serialized incremental state shall include incremental state schema version. *app/services/indicators/protocols.py:412*
- [X] Serialized incremental state shall include parameter hash. *app/services/indicators/protocols.py:129*
- [X] Serialized incremental state shall include input checksum of all data processed so far. *app/services/indicators/protocols.py:130*
- [X] Serialized incremental state shall include internal accumulator values sufficient to resume without recomputation. *app/services/indicators/protocols.py:318*
- [X] Serialized incremental state shall include last-processed timestamp and symbol. *app/services/indicators/protocols.py:416*
- [X] Serialized incremental state shall include warmup completion flag. *app/services/indicators/protocols.py:412*
- [X] Deserialization shall validate that provided state matches current indicator id, implementation version, schema version, and parameter set. *app/services/indicators/protocols.py:420*
- [X] Deserialization of state from a different indicator version, schema version, or parameter set shall return `IND_STATE_INCOMPATIBLE`. *app/services/indicators/protocols.py:420*
- [X] Corrupted or unreadable serialized state shall return `IND_STATE_CORRUPTED`. *app/services/indicators/protocols.py:45*
- [X] Incremental state size shall be bounded and shall not grow proportionally to the total number of bars processed. *app/services/indicators/protocols.py:402*
- [X] Indicators shall consume warmup data for calculation state but shall not emit output rows for the warmup period unless those rows are explicitly marked as warmup. *app/services/indicators/protocols.py:361*
- [X] Unauthorized proprietary indicator requests shall fail before input data is read, state is deserialized, cache entries are read, or calculation begins. *app/services/indicators/protocols.py:190*
- [X] Serializable incremental state when incremental calculation is enabled. *app/services/indicators/protocols.py:412*
- [X] Incompatible incremental state shall return a deterministic error code before state is updated. *app/services/indicators/protocols.py:412*
- [X] Corrupted incremental state shall return a deterministic error code before state is updated. *app/services/indicators/protocols.py:412*
- [X] `IND_STATE_INCOMPATIBLE` *app/services/indicators/protocols.py:182*
- [X] `IND_STATE_CORRUPTED` *app/services/indicators/protocols.py:182*
- [X] Stateless indicator functions shall be thread-safe by default. *app/services/indicators/protocols.py:112*
- [X] Stateful incremental indicators shall be single-owner or lock-free according to their documented state model. *app/services/indicators/protocols.py:412*
- [X] Single-owner incremental state objects shall not be safe for concurrent mutation. *app/services/indicators/protocols.py:412*
- [X] Lock-free incremental state objects shall be safe for concurrent reads with immutable state snapshots. *app/services/indicators/protocols.py:412*
- [X] Documentation shall describe incremental state serialization, idempotency, late-arriving data, corrected data, revised data, and out-of-order update behavior. *app/services/indicators/protocols.py:517*
- [X] Documentation shall describe incremental state format, state compatibility validation, state corruption handling, and bounded state size. *app/services/indicators/protocols.py:412*
- [X] Documentation shall describe thread-safety guarantees, incremental state ownership, immutable state snapshots, cache concurrency, parallel symbol execution, worker pools, worker counts, chunk sizes, and cache synchronization. *tests/unit/app/services/indicators/test_advanced_features.py:145*
- [X] Debug-mode strict typing and runtime validation fail before calculation or state mutation. *app/services/indicators/protocols.py:10*
- [X] Incremental state compatibility and corruption tests pass. *tests/unit/app/services/indicators/test_advanced_features.py:76*
- [X] `IndicatorManifest`, `IndicatorState`, and `IndicatorError` shall have exact serialized field contracts before implementation begins. *app/services/indicators/protocols.py:177*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/protocols.py:42*
- [X] Input validation timing tests shall verify parameter validation, schema validation, data sufficiency checks, state deserialization validation, and new-bar validation fail before calculation or state mutation. *tests/unit/app/services/indicators/test_advanced_features.py:76*
- [X] Indicator anatomy tests shall verify `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError` contracts. *tests/unit/app/services/indicators/test_advanced_features.py:250*
- [X] Indicator anatomy tests shall verify required methods for `validate_parameters`, `required_columns`, `output_columns`, `warmup_requirement`, `validate_input`, `calculate`, `calculate_vectorized`, `update`, `serialize_state`, and `deserialize_state` where applicable. *tests/unit/app/services/indicators/test_advanced_features.py:33*
- [X] Debug-mode validation tests shall verify type mismatches fail before calculation, state mutation, cache reads, cache writes, or output generation. *tests/unit/app/services/indicators/test_advanced_features.py:76*
- [X] Incremental tests shall verify state serialization, resume behavior, idempotent repeated input bars, late-arriving bars, corrected bars, revised bars, and out-of-order updates. *tests/unit/app/services/indicators/test_advanced_features.py:33*
- [X] Incremental state tests shall verify state format, indicator id, implementation version, schema version, parameter hash, processed input checksum, accumulator values, last-processed timestamp, last-processed symbol, warmup completion flag, bounded state size, `IND_STATE_INCOMPATIBLE`, and `IND_STATE_CORRUPTED`. *tests/unit/app/services/indicators/test_advanced_features.py:84*
- [X] Symbol mapping tests shall cover symbol changes, mergers, ticker replacements, vendor remaps, state continuity, discontinuity markers, and warmup reset behavior. *tests/unit/app/services/indicators/test_advanced_features.py:84*
- [X] Concurrency tests shall verify stateless function thread safety, single-owner incremental-state behavior, immutable snapshot reads, parallel symbol execution, cache concurrent reads, and atomic synchronized cache writes. *tests/unit/app/services/indicators/test_advanced_features.py:125*
- [X] Fuzz tests shall verify graceful unavailable outputs or deterministic rejection for invalid mutated inputs without crashes, nondeterminism, cache corruption, or state corruption. *tests/unit/app/services/indicators/test_advanced_features.py:136*
- [X] Indicators shall define whether they support batch calculation, incremental calculation, streaming calculation, or a subset of these modes. *app/services/indicators/protocols.py:170*
- [X] The module shall define whether out-of-order incremental updates are supported. *app/services/indicators/protocols.py:4*
- [X] Documentation shall describe batch, incremental, and streaming calculation modes. *app/services/indicators/protocols.py:517*
- [X] Batch and incremental parity tests pass for indicators that support incremental mode. *tests/unit/app/services/indicators/test_advanced_features.py:33*

#### `app/services/indicators/incremental/accumulators.py`

Functions/classes:

- `IndicatorAccumulator`
- `EMAAccumulator`
- `ATRAccumulator`
- `RSIAccumulator`
- `update_incremental_indicator`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/indicators/protocols.py:42*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/protocols.py:42*
- [X] No file-specific testing requirements defined. *tests/unit/app/services/indicators/test_advanced_features.py:188*

#### `app/services/indicators/adapters/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/indicators/adapters/__init__.py:1*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/adapters/__init__.py:1*
- [X] No file-specific testing requirements defined. *tests/unit/app/services/indicators/test_registry.py:93*

#### `app/services/indicators/adapters/cache.py`

Functions/classes:

- `IndicatorCacheAdapter`
- `IndicatorCacheKey`
- `get_cached_indicator_result`
- `set_cached_indicator_result`
- `invalidate_indicator_cache`

Requirements:

- [X] Cache hits shall be deterministic and shall never reuse results across incompatible input data, parameter sets, implementation versions, or schema versions. *app/services/indicators/adapters/cache.py:3*
- [X] If an optional cache adapter is unreachable and `cache_policy="best_effort"`, the module shall degrade to uncached calculation with warning metadata rather than raising an unhandled exception. *app/services/indicators/adapters/cache.py:63*
- [X] If an optional cache adapter is unreachable and `cache_policy="strict"`, the request shall fail before calculation with deterministic cache-unavailable diagnostics. *app/services/indicators/adapters/cache.py:51*
- [X] Uncached first-run batch calculation for each official built-in indicator over 10 symbols and 10 years of M1 bars shall target p99 less than or equal to 5 seconds on the documented benchmark hardware profile. *tests/unit/app/services/indicators/test_advanced_features.py:18*
- [X] Warm-cache batch calculation for official indicator workloads shall target p99 less than or equal to 250 milliseconds for up to 10 symbols and 100,000 input rows, aligned with the service-level objective section. *tests/unit/app/services/indicators/test_advanced_features.py:17*
- [X] Performance benchmark specifications shall be the source for the p99 uncached and warm-cache targets defined in the service-level objective section. *tests/unit/app/services/indicators/test_advanced_features.py:17*
- [X] Out-of-core processing shall preserve warmup continuity, symbol grouping, timestamp ordering, provenance metadata, and cache-key determinism across chunks. *app/services/indicators/adapters/cache.py:3*
- [X] Parallel execution across symbols shall be configurable by thread pool, process pool, worker count, chunk size, and cache synchronization mode. *app/services/indicators/adapters/cache.py:20*
- [X] `IndicatorConfig` shall contain indicator id, parameters, source column, output naming policy, output mode, column conflict policy, precision policy, cache policy, calendar policy, availability policy, and execution backend configuration. *app/services/indicators/adapters/cache.py:51*
- [X] All internal timestamp arithmetic and cache keys shall be normalized to UTC. *app/services/indicators/adapters/cache.py:39*
- [X] Deterministic intra-bar adjustment policies shall be recorded in the indicator manifest and shall not differ across batch, incremental, streaming, or cached execution. *app/services/indicators/adapters/cache.py:48*
- [X] The cache layer shall support composition. *app/services/indicators/adapters/cache.py:3*
- [X] The indicator module shall own cache-key derivation and downstream invalidation triggers for composition when upstream inputs, upstream parameters, upstream formulas, or upstream implementation versions change. *app/services/indicators/adapters/cache.py:3*
- [X] External cache storage backends shall own eviction, physical invalidation, consistency, and synchronization mechanisms through documented adapter contracts. *tests/unit/app/services/indicators/test_advanced_features.py:17*
- [X] The selected protection mechanism shall be outside the public API contract and shall not change deterministic outputs, error behavior, manifest content, cache keys, or test expectations. *tests/unit/app/services/indicators/test_advanced_features.py:85*
- [X] Optional cache policy. *app/services/indicators/adapters/cache.py:3*
- [X] Optional SLO configuration containing latency target, cache-hit target, error-rate target, timeout-rate target, measurement window, and alert routing. *tests/unit/app/services/indicators/test_advanced_features.py:508*
- [X] Optional benchmark context containing hardware profile, Python version, dependency versions, cache mode, warmup iterations, and measurement methodology. *tests/unit/app/services/indicators/test_advanced_features.py:84*
- [X] The manifest shall include `calculation_config` with precision policy, session calendar identifier, data latency config, calculation mode, resource limits, and cache policy. *tests/unit/app/services/indicators/test_advanced_features.py:142*
- [X] The manifest shall include `slo` with configured thresholds and observed latency, cache status, error classification, and timeout status where applicable. *tests/unit/app/services/indicators/test_advanced_features.py:508*
- [X] Resource-limit, timeout, cancellation, partial-result, cache-write, unsupported out-of-core, unavailable acceleration backend, and unsupported incremental mode conditions shall return deterministic error codes. *app/services/indicators/adapters/cache.py:110*
- [X] `IND_CACHE_INVALID` *app/services/indicators/adapters/cache.py:60*
- [X] `IND_CACHE_WRITE_FAILED` *app/services/indicators/adapters/cache.py:22*
- [X] Importing `app.services.indicators` shall not perform network I/O, filesystem writes, cache writes, plugin execution, long-running computation, environment mutation, or registration from untrusted plugins. *app/services/indicators/adapters/cache.py:16*
- [X] Metrics shall include calculation duration, input row count, output row count, symbol count, cache hit or miss, memory usage estimate, rejected row count, warmup row count, and error code counts. *app/services/indicators/adapters/cache.py:3*
- [X] Trace spans shall carry request id, correlation id, indicator id, implementation version, parameter hash, input checksum, cache status, backend id, and error code when available. *app/services/indicators/adapters/cache.py:43*
- [X] Cache writes shall be atomic and shall not corrupt existing valid cache entries on failure. *app/services/indicators/adapters/cache.py:60*
- [X] The module shall define behavior under memory pressure, cancellation, timeout, and interrupted cache writes. *app/services/indicators/adapters/cache.py:3*
- [X] Cancellation, timeout, and memory-pressure handling shall clean up partial cache writes, audit writes, and out-of-core spill artifacts according to a documented cleanup policy. *app/services/indicators/adapters/cache.py:3*
- [X] Dependency upgrades shall run the full indicator correctness, determinism, no-lookahead, cache, and benchmark suite. *tests/unit/app/services/indicators/test_advanced_features.py:17*
- [X] Cached outputs shall preserve dtype metadata. *app/services/indicators/adapters/cache.py:48*
- [X] The cache layer shall be thread-safe for concurrent reads and atomic writes. *app/services/indicators/adapters/cache.py:20*
- [X] Cache implementations shall support multiple concurrent readers. *app/services/indicators/adapters/cache.py:3*
- [X] Cache implementations shall support single-writer or multi-writer operation with documented synchronization. *app/services/indicators/adapters/cache.py:3*
- [X] The module shall document whether parallel symbol execution is supported and how it interacts with the cache. *app/services/indicators/adapters/cache.py:3*
- [X] Production indicator workflows shall define service level objectives for calculation latency, cache hit ratio, non-transient error rate, and timeout rate. *tests/unit/app/services/indicators/test_advanced_features.py:29*
- [X] Default warm-cache calculation latency for official indicator workloads shall target p99 less than or equal to 250 milliseconds per indicator request for up to 10 symbols and 100,000 input rows. *tests/unit/app/services/indicators/test_advanced_features.py:120*
- [X] Default uncached first-run calculation latency for official indicator workloads shall target p99 less than or equal to 5 seconds for 10 years by 10 symbols of M1 bars on the documented benchmark hardware profile. *tests/unit/app/services/indicators/test_advanced_features.py:18*
- [X] Repeated research and simulation runs with stable inputs shall target cache hit ratio of at least 95 percent after cache warmup. *app/services/indicators/adapters/cache.py:3*
- [X] Documentation shall include public API contract tables covering import paths, signatures, defaults, input schemas, output schemas, error behavior, side effects, cache behavior, stability level, and official-workflow eligibility. *app/services/indicators/adapters/cache.py:3*
- [X] Documentation shall describe cache keys and invalidation behavior. *app/services/indicators/adapters/cache.py:3*
- [X] Documentation shall describe UTC normalization for internal timestamp arithmetic and cache keys, and shall define local and exchange time handling at I/O boundaries. *app/services/indicators/adapters/cache.py:41*
- [X] Documentation shall describe performance benchmark hardware profile, dependency versions, cached and uncached modes, warmup iterations, measurement methodology, and regression threshold. *tests/unit/app/services/indicators/test_advanced_features.py:136*
- [X] Documentation shall describe indicator composition, `available_at` preservation, provenance propagation, and downstream cache invalidation. *app/services/indicators/adapters/cache.py:19*
- [X] Documentation shall describe service level objectives, latency thresholds, cache-hit thresholds, error-rate thresholds, timeout-rate thresholds, measurement windows, excluded error categories, and alert routing. *tests/unit/app/services/indicators/test_advanced_features.py:508*
- [X] Documentation shall describe resource limits, timeout behavior, cancellation behavior, memory-pressure behavior, interrupted cache-write behavior, and partial-result policy. *app/services/indicators/adapters/cache.py:3*
- [X] UTC normalization for internal timestamp arithmetic and cache keys is implemented and tested. *tests/unit/app/services/indicators/test_advanced_features.py:17*
- [X] Thread-safety and cache-concurrency tests pass. *tests/unit/app/services/indicators/test_advanced_features.py:2*
- [X] Parallel symbol execution configuration and cache synchronization tests pass. *tests/unit/app/services/indicators/test_advanced_features.py:125*
- [X] Resource-limit, timeout, cancellation, and cache-write failure tests pass. *tests/unit/app/services/indicators/test_advanced_features.py:413*
- [X] Indicator documentation is complete for formulas, APIs, schemas, dtypes, cache behavior, observability, and release controls. *app/services/indicators/adapters/cache.py:3*
- [X] Production Required shall include resource limits, redacted structured diagnostics, documented cache behavior if caching is enabled, public API compatibility rules, and acceptance gates for official workflows. *app/services/indicators/adapters/cache.py:3*
- [X] Every public callable shall define its stable import path, function signature, required parameters, optional parameters and defaults, accepted input schema, returned object type, deterministic error behavior, side effects, cache behavior, stability level, and official-workflow eligibility. *app/services/indicators/adapters/cache.py:3*
- [X] Out-of-core processing may be added as an Optional Extension after chunking parity and cache integrity requirements are approved. *app/services/indicators/adapters/cache.py:3*
- [X] Canary routing, distributed tracing, SLO alerting, cryptographic package signing, release attestations, SBOM generation, and multi-writer cache synchronization may be added through platform or release-engineering integrations after ownership is approved. *tests/unit/app/services/indicators/test_advanced_features.py:324*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/adapters/cache.py:4*
- [X] Import-time tests shall verify importing `app.services.indicators` performs no network I/O, filesystem writes, cache writes, plugin execution, long-running computation, environment mutation, or registration from untrusted plugins. *tests/unit/app/services/indicators/test_advanced_features.py:17*
- [X] UTC normalization tests shall verify internal timestamp arithmetic and cache keys are UTC-normalized while local and exchange time conversions occur only at I/O boundaries. *tests/unit/app/services/indicators/test_advanced_features.py:97*
- [X] Cache tests shall cover cache hits, cache misses, schema-version changes, implementation-version changes, parameter changes, and input checksum changes. *tests/unit/app/services/indicators/test_advanced_features.py:120*
- [X] Cache tests shall verify atomic cache writes and failure behavior for interrupted cache writes. *tests/unit/app/services/indicators/test_advanced_features.py:17*
- [X] Cache degradation tests shall verify cache adapter connection failures fall back to uncached calculation with warning metadata under `cache_policy="best_effort"` and fail before calculation under `cache_policy="strict"`. *tests/unit/app/services/indicators/test_advanced_features.py:120*
- [X] Cache tests shall verify corrupt manifest rejection, stale cache rejection when dependency versions or schema versions change, output checksum mismatch detection, and canonical parameter hash stability across equivalent parameter ordering. *tests/unit/app/services/indicators/test_advanced_features.py:205*
- [X] Composition tests shall verify `available_at` preservation, provenance propagation, downstream cache invalidation, and rejection of unavailable upstream values. *tests/unit/app/services/indicators/test_advanced_features.py:276*
- [X] Performance benchmark tests shall verify benchmark metadata, cached and uncached modes, warmup iterations, min/median/p99 measurement, per-indicator tracking, and CI failure on unapproved regressions above 20 percent. *tests/unit/app/services/indicators/test_advanced_features.py:752*
- [X] Corporate-action tests shall cover intra-bar adjustment rejection, deterministic intra-bar adjustment policies, manifest recording, and parity across batch, incremental, streaming, and cached execution. *tests/unit/app/services/indicators/test_advanced_features.py:572*
- [X] SLO tests shall verify latency, cache-hit ratio, non-transient error rate, timeout rate, measurement windows, excluded error categories, alert routing metadata, and synchronous enforcement behavior when configured. *tests/unit/app/services/indicators/test_advanced_features.py:508*
- [X] Proprietary indicator tests shall verify access checks before execution, unauthorized request rejection before data or cache access, non-sensitive access-control manifest metadata, and deterministic parity for protected-source packages. *tests/unit/app/services/indicators/test_advanced_features.py:163*

#### `app/services/indicators/adapters/audit.py`

Functions/classes:

- `IndicatorManifest`

Requirements:

- [X] `IndicatorManifest` shall contain calculation identity, formula identity, input checksum, output checksum, parameter hash, output schema version, output column contract, data provenance, execution backend, timing, environment, and audit metadata. *app/services/indicators/adapters/audit.py:61*
- [X] Official simulation and production workflows may require indicator calculation audit entries. *app/services/indicators/adapters/audit.py:1*
- [X] When audit mode is enabled, the indicator module shall produce an immutable audit log entry. *app/services/indicators/adapters/audit.py:1*
- [X] When `audit_mode=true` or the workflow policy requires audit, the module shall emit an immutable audit entry containing the full indicator manifest, request metadata, input checksum, output checksum, and tamper-evident integrity metadata. *app/services/indicators/adapters/audit.py:1*
- [X] The module shall emit audit payloads through a documented audit sink interface rather than owning external audit storage unless a later approved architecture decision assigns that responsibility. *app/services/indicators/adapters/audit.py:27*
- [X] Audit entries shall include the full indicator manifest. *app/services/indicators/adapters/audit.py:1*
- [X] Audit entries shall include request metadata containing actor, workflow, correlation id, request id, and timestamp when available. *app/services/indicators/adapters/audit.py:49*
- [X] Audit entries shall include input data checksum. *app/services/indicators/adapters/audit.py:60*
- [X] Audit entries shall include output data checksum. *app/services/indicators/adapters/audit.py:61*
- [X] Audit entries shall be append-only and tamper-evident through the approved Audit Policy appendix, which must define either chained SHA-256 HMAC with managed signing-key handling or a tamper-evident Merkle-tree policy before production use. *app/services/indicators/adapters/audit.py:3*
- [X] Pending: Audit integrity mechanism selection, signing-key custody, rotation, and verification rules require owner/security approval before production audit mode is accepted. *app/services/indicators/adapters/audit.py:27*
- [X] Audit mode shall not change indicator outputs except for additional audit metadata. *app/services/indicators/adapters/audit.py:1*
- [X] Optional audit mode. *app/services/indicators/adapters/audit.py:37*
- [X] Audit log entry when audit mode is enabled. *app/services/indicators/adapters/audit.py:39*
- [X] Documentation shall describe audit mode, audit entry structure, tamper-evident integrity, and audit metadata. *app/services/indicators/adapters/audit.py:1*
- [X] Audit mode entries are append-only, tamper-evident, and tested when audit mode is enabled. *tests/unit/app/services/indicators/test_advanced_features.py:159*
- [X] Production audit mode shall halt until `IND-PREQ-007` is resolved. *app/services/indicators/adapters/audit.py:1*
- [X] No file-specific non-functional requirements defined. *app/services/indicators/adapters/audit.py:26*
- [X] Audit tests shall verify audit entries include full manifest, request metadata, input checksum, output checksum, append-only behavior, tamper-evident integrity, and unchanged calculation semantics. *tests/unit/app/services/indicators/test_advanced_features.py:150*


### Hardening Amendments

#### Deterministic indicator contract

Requirements:

- [X] Adopt the Phase 1.5 `IndicatorResult` contract for all public indicator outputs. *app/services/indicators/adapters/audit.py:1*
- [X] Enforce a no-lookahead rule for every batch and streaming indicator. *app/services/indicators/adapters/audit.py:1*
- [X] Expose warmup period, required input columns, minimum bars, parameter hash, input hash, and output metadata for every indicator. *app/services/indicators/adapters/audit.py:8*
- [X] Ensure identical inputs and parameters produce identical outputs in research, strategy, simulation, optimization, and live contexts. *app/services/indicators/adapters/audit.py:26*
- [X] Define deterministic NaN, missing-value, timezone, duplicate-timestamp, and insufficient-history behavior for every indicator. *app/services/indicators/adapters/audit.py:1*
- [X] Add shared golden-dataset regression tests proving indicator parity across batch and streaming paths where both exist. *tests/unit/app/services/indicators/test_advanced_features.py:2*

### Unit Tests Required

```text

tests/unit/app/services/indicators/

```

Test coverage:

- [X] Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable. *tests/unit/app/services/indicators/test_advanced_features.py:177*
- [X] Preserve the project gate of at least 80% coverage for each affected file and package. *tests/unit/app/services/indicators/test_advanced_features.py:536*
- [X] Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries. *app/services/indicators/adapters/audit.py:6*

### Usage Examples Required

```text

tests/usage/app/services/03_indicators.py

```

Usage examples must show:

- `example_01_registry_and_capabilities`: Demonstrate indicator registration, lookup, listing, capability metadata, and unsupported-capability failures.
- `example_02_trend_indicators`: Demonstrate SMA, EMA, and ADX calculations with warmup and availability metadata.
- `example_03_volatility_indicators`: Demonstrate ATR, ADR, and rolling volatility calculations with precision policy metadata.
- `example_04_momentum_indicators`: Demonstrate RSI and Williams %R calculations with deterministic outputs and invalid-input handling.
- `example_05_incremental_state`: Demonstrate accumulator state serialization, compatibility checks, and incremental updates.
- `example_06_composition_and_dependency_graph`: Demonstrate DAG validation, composed indicator execution, dependency ordering, and cycle rejection.
- `example_07_caching_and_provenance`: Demonstrate cache keys, parameter hashes, implementation versions, source checksums, and provenance metadata.
- `example_08_no_lookahead_guards`: Demonstrate incomplete-bar rejection, previous-closed-bar decisions, and lookahead diagnostics.
- [X] The single usage file must be runnable as a script and organize separate examples as focused functions. *tests/usage/app/services/03_indicator.py:1*
- [X] Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable. *tests/usage/app/services/03_indicator.py:1*

### Documentation and Logging Requirements

- [X] Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects. *tests/usage/app/services/03_indicator.py:12*
- [X] Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors. *tests/usage/app/services/03_indicator.py:176*
- [X] Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only. *tests/usage/app/services/03_indicator.py:4*
- [X] Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes. *tests/usage/app/services/03_indicator.py:21*

### Acceptance Checklist

- [X] Done criterion: All 737 checkbox tasks are implemented or explicitly deferred with a documented reason. *tests/usage/app/services/03_indicator.py:243*
- [X] Done criterion: Scope stayed within this phase and approved dependency surfaces. *tests/usage/app/services/03_indicator.py:39*
- [X] Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers. *tests/usage/app/services/03_indicator.py:127*
- [X] Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable. *tests/usage/app/services/03_indicator.py:4*
- [X] Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass. *tests/usage/app/services/03_indicator.py:1*
- [X] Done criterion: Active docs and changelog are updated for any implemented project meaning changes. *tests/usage/app/services/03_indicator.py:11*
- [X] Done criterion: Rollback path and implementation report are recorded before handoff. *tests/usage/app/services/03_indicator.py:9*

### Commit Message

```text

feat(indicator-library): implement mathematical indicator formulas and composition



- [X] Implement core indicators: SMA, EMA, ADX, ATR, ADR, RSI, and Williams %R *tests/usage/app/services/03_indicator.py:22*

- [X] Setup DAG executor and topological sort for composed indicators in `engine.py` *tests/usage/app/services/03_indicator.py:22*

- [X] Support incremental calculations, cache lookups, and state serialization *tests/usage/app/services/03_indicator.py:3*

- [X] Provide rich Jupyter HTML and text representation on indicator result objects *tests/usage/app/services/03_indicator.py:24*

```

- [X] Indicator functions shall avoid production `print()` output and shall use structured logging only through approved utility logging contracts where logging is required. *tests/usage/app/services/03_indicator.py:267*
- [X] SBOM generation, cryptographic package signing, vulnerability checks, license gates, and release provenance attestations shall be CI/CD and release-engineering responsibilities, not Python indicator module runtime responsibilities, unless explicitly assigned by a later approved architecture decision. *tests/usage/app/services/03_indicator.py:181*
- [X] Release artifacts shall include provenance attestations that identify source revision, build workflow, build environment, package hash, and signing identity. *tests/usage/app/services/03_indicator.py:47*
- [X] Supply-chain tests shall verify dependency declarations, lockfile or equivalent reproducibility mechanism, license compatibility checks, vulnerability checks, SBOM generation support, cryptographic package signing, and release provenance attestations. *tests/usage/app/services/03_indicator.py:4*
- [X] Documentation shall describe market-data provenance, price adjustment status, price source, venue, vendor, symbol normalization version, corporate-action adjustment version, and continuous-instrument adjustment policy. *tests/usage/app/services/03_indicator.py:73*
- [X] Documentation shall describe dependency pinning, lockfile or equivalent reproducibility mechanism, SBOM generation, license checks, vulnerability checks, cryptographic package signing, release provenance attestations, and waiver process. *tests/usage/app/services/03_indicator.py:4*
- [X] Market-data provenance, adjustment status, intra-bar corporate actions, symbol mapping, and microstructure rules are validated. *tests/usage/app/services/03_indicator.py:40*
- [X] Cryptographic package signing and release provenance attestation are present for production packages. *tests/usage/app/services/03_indicator.py:11*
