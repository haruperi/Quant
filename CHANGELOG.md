# Changelog

All notable HaruQuantAI project changes should be recorded here.

## [Unreleased]

| ID       | Functionality              | Notes                                                                                                                             |
| -------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| DONE-020 | MT5Client Broker Adapter   | Created MT5Client class to manage initialization, login, symbol selection, status connection checks, and connection shutdown.     |
| DONE-021 | Dynamic Pip Calculations   | Updated MT5 usage examples to dynamically compute pip values and round prices based on symbol specifications.                     |
| DONE-022 | cTrader Open API Client    | Integrated CTraderClient broker adapter using ctrader-open-api over Twisted/TCP with mock test infrastructure.                     |
| DONE-023 | Generic Trade Classes      | Created generic, unified, MQL5-compatible trade classes and active broker resolver inside app/services/trader.                    |
| DONE-024 | Broker Simulator Adapter   | Implemented an in-memory broker simulator (`simulator.py`) under `app/services/brokers` and registered it in `resolver.py`. Integrated live MT5 specifications and calculations (margin & profit) with offline fallbacks. |
| DONE-025 | Standalone Simulator Service | Refactored simulator adapter into a standalone package `app/services/simulator` with separate `models.py` and `engine.py`. |
| DONE-026 | Broker Resolver Relocation | Relocated active broker resolver from `app/services/trader/resolver.py` to `app/routes/brokers.py` and refactored reference imports across the trader sub-modules, tests, and scripts. |



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


## Pending Decisions

| ID       | Proposed decision                             | Why pending                                              |
| -------- | --------------------------------------------- | -------------------------------------------------------- |
| PDEC-001 | Chat and regulated artifact retention policy. | Compliance impact.                                       |
| PDEC-002 | Risk threshold defaults.                      | Numeric trading policy must be approved before live use. |
| PDEC-003 | Event bus implementation phases.              | Needs reliability and deployment input.                  |
| PDEC-004 | New service-tool catalog format.              | Needs implementation repo structure.                     |
| PDEC-005 | SQLite production duration.                   | Depends on concurrency and deployment targets.           |
