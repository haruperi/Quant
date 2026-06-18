# HaruQuantAI Implementation Plan

**Purpose:** Provide the standalone phased Builder implementation plan for HaruQuantAI.

Each phase is a standalone implementation phase. A task is any unchecked Markdown checkbox in this file.

**Execution rule:** This document is a plan, not approval to implement all phases at once. Each phase still requires the repository approval workflow and a dry run before edits.

## Task Inventory

|           Phase | Area                               | Target area                                    |           Tasks |     Checked |       Unchecked |
| --------------: | ---------------------------------- | ---------------------------------------------- | --------------: | ----------: | --------------: |
|               0 | Project Scaffold and CI Foundation | Repository scaffold / CI / docs                |              49 |           0 |              49 |
|               1 | Utils Foundation                   | `app/utils/`                                 |           1,168 |           0 |           1,168 |
|             1.5 | Core Domain Contracts              | `app/contracts/`                             |              73 |           0 |              73 |
|               2 | Data Foundation                    | `app/services/data/`                         |             711 |           0 |             711 |
|               3 | Indicator Library                  | `app/services/indicators/`                   |             743 |           0 |             743 |
|               4 | Strategy Service                   | `app/services/strategies/`                   |             463 |           0 |             463 |
|               5 | Risk Governance                    | `app/services/risk/`                         |             876 |           0 |             876 |
|               6 | Analytics Service                  | `app/services/analytics/`                    |             465 |           0 |             465 |
|               7 | Trading Service                    | `app/services/trader/` + broker integrations |              91 |           0 |              91 |
|               8 | Simulation Engine                  | `app/services/simulation/`                   |           1,678 |           0 |           1,678 |
|               9 | Optimization Service               | `app/services/optimization/`                 |             285 |           0 |             285 |
|              10 | Live Runtime                       | `app/services/live/`                         |             243 |           0 |             243 |
|              11 | UI and API Gateway                 | `api/ and ui/`                               |             381 |           0 |             381 |
|              12 | Research Edge Lab                  | `app/services/research/`                     |             297 |           0 |             297 |
|              13 | Conversation AI Layer              | `app/services/conversation/`                 |             263 |           0 |             263 |
| **Total** |                                    |                                                | **7,786** | **0** | **7,786** |

**Hardening amendment delta:** 428 additional unchecked tasks were added to the original 7,358 unchecked tasks, bringing the total to 7,786 unchecked tasks.

## Global Builder Rules

- Done criterion: Read `AGENTS.md`, `docs/ARCHITECTURE.md`, `CHANGELOG.md`, this implementation plan and relevant existing code/tests before planning or editing.
- Done criterion: Perform a dry run before edits: files read/changed, commands/tests planned, scope boundaries, blockers/risks, and rollback path.
- Done criterion: Wait for `APPROVED: EXECUTE` before modifying files.
- Done criterion: Implement one approved scope at a time; do not use this plan as blanket approval for broad refactors.
- Done criterion: Preserve module ownership boundaries and fail-closed safety behavior.
- Done criterion: Update active docs and `CHANGELOG.md` whenever project meaning changes.
- Done criterion: Run validation in the required order: pre-commit hooks, Ruff check, Ruff format, mypy strict, pytest, and coverage as applicable.

## Final Hardening Amendments Incorporated

The following amendments are now part of the implementation plan and are counted as checkbox tasks where applicable:

- Phase 0 Project Scaffold and CI Foundation was added before domain implementation.
- Phase 1.5 Core Domain Contracts was added to prevent duplicated cross-domain models.
- Large phases must be split into approved sprint packs before implementation.
- Sprint-pack execution boundaries now block phase advancement until the prior approved scope has green CI, coverage evidence, synchronized docs, usage examples, and resolved safety blockers.
- Old Black/isort/Flake8 wording was replaced with Ruff format, Ruff check, mypy strict, pytest, coverage, and pre-commit gates.
- Broker routing ownership was moved out of API routes and into broker service/integration boundaries.
- Data persistence, migrations, lineage, calendars, backups, and golden datasets were added.
- Paper, shadow, read-only, micro-live, and full-live promotion gates were added before live trading.
- Lightweight Research Core was added before strategy and optimization promotion workflows depend on research evidence.
- Conversation tool permissions, prompt-injection defense, and retrieval boundaries were added.

## Recommended Dependency Order

```text

00 Scaffold/CI -> 01 Utils -> 01.5 Core Contracts -> 02 Data -> 03 Indicators

02 Data + 03 Indicators + 12A Research Core -> 04 Strategies -> 05 Risk

05 Risk -> 07 Trading -> 08 Simulation -> 06 Analytics -> 09 Optimization

09 Optimization -> 10 Live -> 11 UI/API -> 12 Research Edge Lab -> 13 Conversation

Mandatory live promotion: offline test -> simulation -> replay -> read-only -> paper -> shadow -> micro-live -> full-live

```

## Phase Files

Each implementation phase now lives in its own file for sprint-pack execution, review, and maintenance. The task inventory above remains the canonical cross-phase count.

- [Phase 0 Project Scaffold and CI Foundation](implementation-plan/00-project-scaffold-and-ci-foundation.md)
- [Phase 1 Utils Foundation](implementation-plan/01-utils-foundation.md)
- [Phase 1.5 Core Domain Contracts](implementation-plan/01_5-core-domain-contracts.md)
- [Phase 2 Data Foundation](implementation-plan/02-data-foundation.md)
- [Phase 3 Indicator Library](implementation-plan/03-indicator-library.md)
- [Phase 4 Strategy Service](implementation-plan/04-strategy-service.md)
- [Phase 5 Risk Governance â€” Institutional RiskGovernor Rewrite](implementation-plan/05-risk-governance.md)
- [Phase 6 Analytics Service](implementation-plan/06-analytics-service.md)
- [Phase 7 Trading Service](implementation-plan/07-trading-service.md)
- [Phase 8 Simulation Engine](implementation-plan/08-simulation-engine.md)
- [Phase 9 Optimization Service](implementation-plan/09-optimization-service.md)
- [Phase 10 Live Runtime](implementation-plan/10-live-runtime.md)
- [Phase 11 UI and API Gateway](implementation-plan/11-ui-and-api-gateway.md)
- [Phase 12 Research Edge Lab](implementation-plan/12-research-edge-lab.md)
- [Phase 13 Conversation AI Layer](implementation-plan/13-conversation-ai-layer.md)

## Final Platform Acceptance Checklist

- Done criterion: All 7,786 source checkbox tasks are implemented, tested, or explicitly deferred with owner-approved rationale.
- Done criterion: Every module imports without optional provider dependencies installed.
- Done criterion: All official registries expose only approved public functions/classes/tools.
- Done criterion: Standard envelopes are consistent across all phases.
- Done criterion: No module leaks secrets, credentials, private broker payloads, or approval packet internals into logs, metrics, reports, or conversation memory.
- Done criterion: Risk, live trading, execution, approval, idempotency, reconciliation, and kill-switch controls fail closed.
- Done criterion: UI/API and Conversation delegate domain logic instead of bypassing governed services.
- Done criterion: Active documentation, changelog, tests, and usage examples are synchronized with implemented behavior.

### Final Hardening Acceptance Additions

- Done criterion: Phase 0 scaffold/CI and Phase 1.5 Core Contracts are complete or explicitly deferred with owner-approved rationale before dependent domain implementation proceeds.
- Done criterion: Sprint-pack execution boundaries are enforced before phase advancement; no downstream phase begins while upstream CI, coverage, usage examples, active docs, changelog, or safety gates are failing.
- Done criterion: Data and Indicator foundations are preferred as complete, audited, green-gated modules over any partially implemented Live Trading, UI/API, Research, or Conversation capability.
- Done criterion: All old Black/isort/Flake8 validation references have been replaced with Ruff format, Ruff check, mypy strict, pytest, coverage, and pre-commit gates.
- Done criterion: Broker routing is owned by broker services/integrations, not API route modules.
- Done criterion: Live trading cannot progress to full-live without read-only, paper, shadow, and micro-live gates.
- Done criterion: Canonical contracts are used across domain boundaries and raw provider SDK objects do not leak past integration adapters.
- Done criterion: Research evidence, optimization candidates, UI actions, and conversation requests cannot bypass risk, approval, execution, reconciliation, or kill-switch governance.

### Institutional Risk Governance Acceptance Additions

- Done criterion: Phase 5 Risk Governance implements a layered institutional RiskGovernor rather than a single risk formula.
- Done criterion: VaR is supported but does not act as the only portfolio-risk method.
- Done criterion: Expected Shortfall/CVaR and stress loss act as live-profile tail-risk approval gates.
- Done criterion: FX trades are decomposed into currency-leg exposure before approval.
- Done criterion: Correlation, cluster exposure, margin, drawdown, lifecycle, execution feasibility, and kill-switch controls are all evaluated before final approval.
- Done criterion: Risk decisions are deterministic, auditable, replayable, and tokenized.
- Done criterion: LLM agents may explain or summarize risk outcomes but cannot approve, reject, override, or bypass deterministic safety gates.
- Done criterion: Trading and Live services reject broker mutation without a fresh, scoped, config-compatible risk approval token.

End of plan.
