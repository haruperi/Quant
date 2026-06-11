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
