# Changelog

All notable HaruQuantAI project changes should be recorded here.

## [Unreleased]

| ID       | Functionality              | Notes                                                                                                                             |
| -------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| DONE-049 | Relocate Requirements & Document Risk Service | Migrated and updated all references across 12 requirements markdown files in `docs/source-requirements/` to reflect the package namespace shift from `tools/*` to `app/services/*` (and `tools/utils` to `app/utils`), and created a detailed `README.md` for `app/services/risk/` detailing the architecture, limits, sizing calculators, scenarios, and official AI tools. |
| DONE-048 | Decoupled Risk API Configuration Schema | Decoupled the official AI risk tool parameter definitions from strict Pydantic structures by updating the signature of the `risk_config` parameter to JSON-compatible types (`dict[str, Any]`), and relocated all actual tool implementations from `__init__.py` into a new `tools.py` module to keep the entry point as a pure exporter facade, resolving all mypy static type errors and complying with architectural rules. |
| DONE-047 | Pre-Trade Risk Governance Module | Implemented complete pre-trade risk module under `app/services/risk/` with stateless limit checks, position sizing (fixed risk, Kelly, milestone, volatility, fixed fractional), stress scenario evaluation, kill switch service, and lifecycle transition map. Exposed 10 official AI tools with StandardResponse envelopes supporting both object and dict-like input deserialization. Verified 100% of the 39 unit tests pass and code coverage is above 80% on every module. |
| DONE-046 | Error Service Consolidation | Consolidated all custom indicators, strategies, and utilities errors into `app/utils/errors.py`. Cleaned up imports and deleted `app/utils/error_routing.py`, `app/services/indicators/errors.py`, and `app/services/strategies/errors.py`. |
| DONE-045 | RandomWalk EA Grid Strategy Implementation | Implemented concrete `RandomWalkStrategy` and `RandomWalkConfig` under `app/services/strategies/source/random_walk.py` with scaling order grids, decimal precision point size calculations, and chronological position life check simulation. Verified clean static typing, formatting, and unit tests passing with overall coverage above 81%. |
| DONE-044 | Strategy Method and Helpers Renaming | Renamed the strategy vectorized execution method from `run_vectorized` to `run_vectorized_signals` across the base class, protocol, registry cap checks, test mocks, and usage scripts. Prefixed internal helper functions (`calculate_indicators`, `shift_features`, `ensure_signal_columns`, `generate_simple_signals`) in `TrendFollowingStrategy` with underscores (`_`) to mark them private. Verified clean static typing and formatting, and passed the test suite with 81.49% coverage. |
| DONE-043 | Base Strategy Implementation | Created abstract base class `BaseStrategy` defining static defaults, interface contract (`run_vectorized`), and standard no-op lifecycle hooks (`on_init`, `on_bar`, `on_tick`, etc.). Refactored `TrendFollowingStrategy` to inherit from `BaseStrategy`, renamed its vectorized bar helper to `run_on_bar` to avoid signature conflicts, and verified subclass conformance in unit tests. |
| DONE-042 | Trend Following Strategy | Created app/services/strategies/source folder and implemented TrendFollowingStrategy with double EMA crossovers and long-term trend filter confirmation, conforming strictly to StrategyProtocol and auto-registering to the global registry catalog. Added unit tests with 87% coverage. |
| DONE-041 | Strategy Service Implementation | Implemented a side-effect-free decision layer under app/services/strategies, supporting vectorized signal calculators, event-driven hooks with atomic state updates, thread-safe registry with version constraints, and validation security checks. Passed 100% of 16 tests with 81.34% total codebase coverage. |
| DONE-040 | Indicators Requirements Verification & Finalization | Resolved 3 advanced indicator unit test failures (added `allow_deprecated` to `IndicatorConfig`, fixed `IndicatorResult` `NameError` in mutating indicator tests, and added `status` and `dependencies` attributes to `DummyIndicator`), addressed typing errors in calculations and registry files to ensure 100% clean mypy static type checking, formatted indicators package with ruff, and checked in all completed checkboxes in the requirements file. Passed 100% of 318 tests with 81.42% code coverage. |
| DONE-039 | Indicators Advanced Requirements Verification | Fixed advanced indicator unit tests (canary routing price variance and py.typed parents path resolution), generated SBOM generator script, documented CI/CD cryptographic release process & thread-safety guarantees, and fully completed requirements audit checklists. Passed 100% of 314 tests with 81.23% codebase coverage. |
| DONE-038 | Indicators Requirements Audit & Remediations | Audited `03-indicator.md` requirements. Implemented state compatibility validations (version, parameter hash, and schema version checking) during deserialization, added rich HTML and text notebook representations (`_repr_html_`, `_repr_pretty_`) on `IndicatorResult`, and created topological sort and composition runner (`execute_indicator_composition`) with `available_at` maximum propagation. Passed 100% of 32 unit tests with 83.60% code coverage. |
| DONE-037 | Indicators Service Implementation | Fully implemented contract-driven, auditable, and type-safe Indicators Service under `app/services/indicators/`, supporting SMA, EMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R. Completed thread-safe caching, audit logging verification, DAG verification for composed indicators, resource limits enforcement, and incremental updates. Passed 100% of the 29 unit tests with 83.08% code coverage. |
| DONE-036 | Shared Utilities Documentation and Renames | Added app/utils/README.md, created tests/usage/app/services/01_utils.py as a complete usage script, and renamed usage scripts to 02_data.py and 07_trading.py. |
| DONE-035 | Requirements Specification Synchronization | Updated docs/source-requirements/02-data.md to align all architecture diagrams, tables, and section headings with the active consolidated data service file layout. |
| DONE-034 | Market Data Documentation & Test Fix | Documented all options and parameters of the get_data() function in app/services/data/README.md, and added a circuit-breaker reset fixture in gateway tests to resolve state contamination issues. |
| DONE-033 | Broker Data Retrieval Integration | Implemented actual broker data retrieval (`get_bars` and `get_ticks`) across MT5, cTrader, Dukascopy, Yahoo Finance, and Binance clients. Integrated active adapters in `app/services/data/gateway.py`. Added comprehensive tests, achieving 80.58% total package coverage. |
| DONE-032 | Raw CSV/Parquet Path Support & MT5 Headers | Added support for subdirectories (data/raw/csv, data/raw/parquet), auto-detection of tab delimiter in CSVs, normalization of raw MT5 bracket columns to standard OHLCV fields, and tabular tail printing for retrieved data. |
| DONE-031 | Split Data Retrieval & Connection Clients | Added connection manager client stubs for Dukascopy, Binance, and Yahoo Finance in app/services/brokers; integrated Yahoo Finance in data gateway and validation registries; updated concrete adapters to manage broker client connection status; and refactored the unified usage examples script to demonstrate metadata class-based filtering, split data retrieval, multi-timeframe merging, and symbol concatenation. |
| DONE-030 | App Data Service Rebuild   | Fully implemented the contract-driven, auditable, and resilient Market Data Service under the namespace `app/services/data/`, exposing the 24 official AI tools wrapped in standard `app.utils.standard` JSON-serializable envelopes, with SQLite storage/caching, concurrent scheduler jobs, and 100% test coverage passing (81.73% overall package coverage). |
| DONE-028 | Trading Plan Implementation | Implemented the updated trading requirements document, including TradeStore contract integration, validation enrichment, graceful shutdown, and global kill switch, with 100% unit tests passing and >85% test coverage. |
| DONE-029 | Data Requirements Shift | Updated data requirements document (`02-data.md`) to reflect relocation from `tools/data` to `app/services/data` and imports from `tools.utils` to `app.utils`. |
| DONE-020 | MT5Client Broker Adapter   | Created MT5Client class to manage initialization, login, symbol selection, status connection checks, and connection shutdown.     |
| DONE-021 | Dynamic Pip Calculations   | Updated MT5 usage examples to dynamically compute pip values and round prices based on symbol specifications.                     |
| DONE-022 | cTrader Open API Client    | Integrated CTraderClient broker adapter using ctrader-open-api over Twisted/TCP with mock test infrastructure.                     |
| DONE-023 | Generic Trade Classes      | Created generic, unified, MQL5-compatible trade classes and active broker resolver inside app/services/trader.                    |
| DONE-024 | Broker Simulator Adapter   | Implemented an in-memory broker simulator (`simulator.py`) under `app/services/brokers` and registered it in `resolver.py`. Integrated live MT5 specifications and calculations (margin & profit) with offline fallbacks. |
| DONE-025 | Standalone Simulator Service | Refactored simulator adapter into a standalone package `app/services/simulator` with separate `models.py` and `engine.py`. |
| DONE-026 | Broker Resolver Relocation | Relocated active broker resolver from `app/services/trader/resolver.py` to `app/routes/brokers.py` and refactored reference imports across the trader sub-modules, tests, and scripts. |
| DONE-027 | Trading Plan Update        | Updated trading requirements specification (`07_trading_revised.md`) to integrate state management, error handling resilience, execution quality, rate limiting, observability, concurrency guarantees (including `ConcurrencyQueue`), reconciliation triggers (including Startup Reconciliation Gate), MQL5 specifics, expanded testing, security hardening, Netting/Hedging mode compatibility, Decimal normalization, explicit timeouts, partial fill strategy, graceful shutdown sequence, alerting thresholds, and chaos testing. |




## Added

| ID       | Functionality                | Notes                                                                                                                         |
| -------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| DONE-001 | Implementation Documentation | Documentation bootstrap for HaruQuantAI.                                                                                      |
| DONE-002 | Logger                       | Structured JSON production logs, color console logs, rotating file safety. safe file logging, and logger lifecycle behavior. |
| DONE-003 | Utils Registry               | Public registry for utility domain, side-effect free.                                                                             |
| DONE-004 | Utils Standard Envelope      | Standard tool response builders, metadata, validation, canonical JSON, and timing helpers.                                        |
| DONE-005 | Utils Standard Diagnostics   | Diagnostic issue schemas, circuit-open envelopes, sanitized error events, metric-label checks, and bounded dedupe helpers.        |
| DONE-006 | Utils Errors                 | Typed HaruQuant exceptions, deterministic error-code registry, and safe exception-to-envelope mapping.                            |
| DONE-007 | Utils Identity               | Collision-resistant trace IDs, prefix validation, version defaulting, and request propagation helpers.                            |
| DONE-008 | Utils Normalization          | UTC-first timestamp parsing, formatting, stale checks, sequence diagnostics, and clock-drift helpers.                             |
| DONE-009 | Utils Paths                  | Safe path normalization, base-directory traversal protection, and explicit directory creation helpers.                            |
| DONE-010 | Utils Dataframe Tools        | Lazy-pandas dataframe alignment, serialization, OHLC/OHLCV comparison, chunking, and parameter-grid helpers.                      |
| DONE-011 | Utils Data Quality           | Bounded OHLCV quality diagnostics and standard-envelope validation wrapper without repair or persistence ownership.               |
| DONE-012 | Utils Schema Validation      | Deterministic schema, range, handoff, evidence, approval, registry, and freshness validation helpers.                             |
| DONE-013 | Utils Security               | Secret redaction, password hashing, lazy optional encryption helpers, and redaction tool wrapper.                                 |
| DONE-014 | Utils Settings               | Immutable runtime settings loader with explicit side-effect boundaries and safe path normalization.                               |
| DONE-015 | Utils Auth                   | Immutable auth contexts, deny-by-default authorization decisions, and auth validation envelope helper.                            |
| DONE-016 | Utils Event Bus              | Bounded in-memory event envelopes, pub/sub, idempotency handling, queue-full behavior, and sanitized payloads.                    |
| DONE-017 | Utils Error Routing          | Sanitized error routing with deduplication and caller-owned Event Bus integration.                                                |
| DONE-018 | Utils Notifications          | Fake/local notification routing, redaction, disabled-channel handling, throttling, deduplication, and provider failure reporting. |
| DONE-019 | Utils Observability          | In-memory metrics, Prometheus-compatible text export, health snapshots, clock-drift status, and circuit-breaker primitives.       |

## Fixed

| ID      | Functionality | Notes                                                                                                      |
| ------- | ------------- | ---------------------------------------------------------------------------------------------------------- |
| FIX-001 | Logger        | Keep ANSI color formatting on terminal logs only, not file logs.                                           |
| FIX-002 | Logger        | Correct path resolution in tests/usage/tools/utils.py and export trace context functions from tools.utils. |
| FIX-003 | Test Coverage | Point pytest, coverage, Ruff, and mypy configuration at `tools.utils` after removing `src/app`.        |
| FIX-004 | Utils Tool Standard Audit | Added `TOOL_FUNCTION_STANDARDIZATION_AUDIT.md`, fixed `redact_payload` invalid input handling, and expanded utility test coverage. |
| FIX-005 | Utils Function Audit Remediation | Tightened official utils wrappers to fail closed with standard envelopes, added registry source grouping, and expanded wrapper usage/tests. |
| FIX-006 | Logger Migration | Fully migrated logger implementation to `app/utils/logger.py` and deleted the deprecated `tools/utils/logger.py` shim. |
| FIX-007 | Security Migration | Moved security helper logic to `app/core/security.py`, resolved circular imports using `TYPE_CHECKING` guards, and relocated unit tests. |
| FIX-008 | Utilities Relocation | Relocated standard utility modules to `app/utils/`, deleted the deprecated settings module (`tools/utils/settings.py`), and removed the deprecated `tools/` folder. |
| FIX-009 | cTrader Account Currency | Fetch and cache dynamic asset list from cTrader Open API to correctly resolve trading account base currency. |
| FIX-010 | MT5 History Queries | Pass date parameters positionally to `history_orders_get` and `history_deals_get` to fix silent failures under MT5 python module. |

## Decisions

| ID      | Decision       | Notes                                                                                                                            |
| ------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| DEC-001 | Project Name   | project name is HaruQuantAI                                                                                                      |
| DEC-002 | Project Memory | project memory lives in durable files, not chat                                                                                  |
| DEC-003 | Rebuild Style  | HaruQuantAI is a clean-room rebuild that preserves important functionality and safety behavior while adding new product behavior |
| DEC-004 | Product Scope  | product scope includes tools, API, UI, data, live, research, and conversation surfaces                                           |
| DEC-005 | No Direct MT5 Import | No file should import MetaTrader5 directly. The client/connection should be resolved via app/services/brokers/mt5.py module/functions to maintain a single point of control over terminal state. |
| DEC-006 | Standalone Simulator Service | Standalone simulator service is created to separate simulation state from external live broker adapter definitions. |
| DEC-007 | Strategy Config JSON Schema | All strategy configurations must be declared as JSON Schema dictionaries (`config_schema`), setting `config_model = None`. |
| DEC-008 | Private Helper Naming | Strategy internal helper functions must begin with a leading underscore (`_`) to clearly identify them as private. |
| DEC-009 | Domain Error Consolidation | All domain and module-specific errors are consolidated into the single namespace `app/utils/errors.py` to prevent code duplication and simplify exception handling. |
| DEC-010 | Config JSON Schema | All official AI risk tools or functions must accept JSON-compatible dictionary payloads (`dict[str, Any]`) for configuration parameters to decouple parameters from internal Pydantic schemas. |
| DEC-011 | Dynamic Symbol Info Lookup | Sizing calculators must never hardcode symbol information values (such as point sizes and contract sizes) and must instead fetch actual values dynamically via the MT5 broker client, using robust offline fallback dictionary maps. |


## Pending Decisions

| ID       | Proposed decision                             | Why pending                                              |
| -------- | --------------------------------------------- | -------------------------------------------------------- |
| PDEC-001 | Chat and regulated artifact retention policy. | Compliance impact.                                       |
| PDEC-002 | Risk threshold defaults.                      | Numeric trading policy must be approved before live use. |
| PDEC-003 | Event bus implementation phases.              | Needs reliability and deployment input.                  |
| PDEC-004 | New service-tool catalog format.              | Needs implementation repo structure.                     |
| PDEC-005 | SQLite production duration.                   | Depends on concurrency and deployment targets.           |
