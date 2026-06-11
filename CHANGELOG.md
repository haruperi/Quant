# Changelog

All notable HaruQuantAI project changes should be recorded here.

## [Unreleased]

| ID       | Functionality | Notes                                     |
| -------- | ------------- | ----------------------------------------- |
| TODO-002 | Utils Registry | Public registry for utility domain, side-effect free. |
| TODO-003 | Utils Standard Envelope | Standard tool response builders, metadata, validation, canonical JSON, and timing helpers. |
| TODO-004 | Utils Standard Diagnostics | Diagnostic issue schemas, circuit-open envelopes, sanitized error events, metric-label checks, and bounded dedupe helpers. |
| TODO-005 | Utils Errors | Typed HaruQuant exceptions, deterministic error-code registry, and safe exception-to-envelope mapping. |
| TODO-006 | Utils Identity | Collision-resistant trace IDs, prefix validation, version defaulting, and request propagation helpers. |
| TODO-007 | Utils Normalization | UTC-first timestamp parsing, formatting, stale checks, sequence diagnostics, and clock-drift helpers. |
| TODO-008 | Utils Paths | Safe path normalization, base-directory traversal protection, and explicit directory creation helpers. |
| TODO-009 | Utils Dataframe Tools | Lazy-pandas dataframe alignment, serialization, OHLC/OHLCV comparison, chunking, and parameter-grid helpers. |
| TODO-010 | Utils Data Quality | Bounded OHLCV quality diagnostics and standard-envelope validation wrapper without repair or persistence ownership. |
| TODO-011 | Utils Schema Validation | Deterministic schema, range, handoff, evidence, approval, registry, and freshness validation helpers. |
| TODO-012 | Utils Security | Secret redaction, password hashing, lazy optional encryption helpers, and redaction tool wrapper. |
| TODO-013 | Utils Settings | Immutable runtime settings loader with explicit side-effect boundaries and safe path normalization. |
| TODO-014 | Utils Auth | Immutable auth contexts, deny-by-default authorization decisions, and auth validation envelope helper. |
| TODO-015 | Utils Event Bus | Bounded in-memory event envelopes, pub/sub, idempotency handling, queue-full behavior, and sanitized payloads. |
| TODO-016 | Utils Error Routing | Sanitized error routing with deduplication and caller-owned Event Bus integration. |
| TODO-017 | Utils Notifications | Fake/local notification routing, redaction, disabled-channel handling, throttling, deduplication, and provider failure reporting. |
| TODO-018 | Utils Observability | In-memory metrics, Prometheus-compatible text export, health snapshots, clock-drift status, and circuit-breaker primitives. |

## Added

| ID       | Functionality                | Notes                                    |
| -------- | ---------------------------- | ---------------------------------------- |
| DONE-001 | Implementation Documentation | Documentation bootstrap for HaruQuantAI. |
| DONE-002 | Logger                       | Structured JSON production logs, color console logs, rotating file safety. |

## Fixed

| ID       | Functionality | Notes                                                   |
| -------- | ------------- | ------------------------------------------------------- |
| FIX-001  | Logger        | Keep ANSI color formatting on terminal logs only, not file logs. |
| FIX-002  | Logger        | Correct path resolution in tests/usage/tools/utils.py and export trace context functions from tools.utils. |
| FIX-003  | Test Coverage | Point pytest, coverage, Ruff, and mypy configuration at `tools.utils` after removing `src/app`. |

## Decisions

| ID      | Decision       | Notes                                                                                                                            |
| ------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| DEC-001 | Project Name   | project name is HaruQuantAI                                                                                                      |
| DEC-002 | Project Memory | project memory lives in durable files, not chat                                                                                  |
| DEC-003 | Rebuild Style  | HaruQuantAI is a clean-room rebuild that preserves important functionality and safety behavior while adding new product behavior |
| DEC-004 | Product Scope  | product scope includes tools, API, UI, data, live, research, and conversation surfaces                                           |

## Pending Decisions

| ID       | Proposed decision                             | Why pending                                              |
| -------- | --------------------------------------------- | -------------------------------------------------------- |
| PDEC-001 | Chat and regulated artifact retention policy. | Compliance impact.                                       |
| PDEC-002 | Risk threshold defaults.                      | Numeric trading policy must be approved before live use. |
| PDEC-003 | Event bus implementation phases.              | Needs reliability and deployment input.                  |
| PDEC-004 | New service-tool catalog format.              | Needs implementation repo structure.                     |
| PDEC-005 | SQLite production duration.                   | Depends on concurrency and deployment targets.           |
