## Phase 0 Project Scaffold and CI Foundation

### Goal

Create the repository execution foundation before domain implementation begins, so every later phase uses the same project structure, dependency policy, quality gates, environment conventions, and release workflow.

Task inventory: calculated from the checkbox tasks in this section.

### Dependency Files and Functionality

Required files:

```text
None
```

Required functionality:

- Project scaffold and Python package baseline.
- Ruff, mypy, pytest, coverage, and pre-commit quality gates.
- Environment template and secure configuration conventions.
- CI workflow or equivalent local CI command runner.
- Migration, backup, restore, and release checklist ownership.

### Files to Create

```text
pyproject.toml
.pre-commit-config.yaml
.gitignore
.env.example
README.md
AGENTS.md
CHANGELOG.md
docs/PROJECT.md
docs/ARCHITECTURE.md
docs/MODULES.md
docs/ROADMAP.md
docs/BUILDER.md
scripts/ci_check.py
scripts/release_check.py
scripts/backup_check.py
.github/workflows/ci.yml
```

### Functionality to Implement

#### Project scaffold and package baseline

Requirements:

- [ ] Create the approved minimal repository scaffold before domain phase work begins.
- [ ] Configure Python project metadata in `pyproject.toml` using the approved Python version policy.
- [ ] Configure package discovery so `app` imports reliably in tests, scripts, API runtime, and agent runtime.
- [ ] Create `.gitignore` entries for virtual environments, caches, local data, secrets, logs, reports, and generated artifacts.
- [ ] Create `.env.example` with safe placeholder values only.
- [ ] Ensure no real credentials, broker tokens, API keys, private payloads, account numbers, or trading secrets appear in scaffold files.
- [ ] Create the lean documentation set: `PROJECT.md`, `ARCHITECTURE.md`, `MODULES.md`, `ROADMAP.md`, and `BUILDER.md`.
- [ ] Preserve the Builder approval workflow in `AGENTS.md` and `docs/BUILDER.md`.
- [ ] Document that this implementation plan is not blanket approval for repository edits.

#### Quality gates and CI

Requirements:

- [ ] Configure Ruff format as the canonical formatter.
- [ ] Configure Ruff check as the canonical lint and import-order gate.
- [ ] Configure mypy strict as the canonical static typing gate.
- [ ] Configure pytest as the canonical unit and usage-test runner.
- [ ] Configure coverage to enforce at least 80% per affected package and project where applicable.
- [ ] Configure pre-commit to run formatting, linting, type, and test-adjacent safety checks appropriate for local development.
- [ ] Create a single local CI command or script that runs Ruff format check, Ruff check, mypy strict, pytest, and coverage in the approved order.
- [ ] Create a GitHub Actions workflow or documented local equivalent that runs the same quality gates.
- [ ] Ensure quality gates can run without optional broker SDKs, notification clients, LLM providers, or UI dependencies installed.
- [ ] Document how to run fast tests, full tests, usage examples, and CI checks locally.

#### Migrations, backups, releases, and deployment modes

Requirements:

- [ ] Define which phase owns database migrations and schema versioning before persistence code is implemented.
- [ ] Define a migration naming convention and rollback expectation for future database-backed phases.
- [ ] Define local backup and restore expectations for data, audit, reports, optimization artifacts, and trade journals.
- [ ] Define deployment modes: local development, test, simulation, paper, shadow, live-read-only, micro-live, and full-live.
- [ ] Ensure production/live deployment modes require explicit configuration and never activate from safe defaults.
- [ ] Create a release checklist covering tests, docs, changelog, migration notes, rollback path, and operator risk review.
- [ ] Create a dependency policy documenting required, optional, broker-specific, UI-specific, and LLM-provider-specific dependencies.
- [ ] Document optional dependency behavior: imports must remain safe and missing optional dependencies fail only when a feature is used.

#### Documentation and governance baseline

Requirements:

- [ ] Create a changelog discipline requiring every project-meaning change to be recorded.
- [ ] Document the final phase dependency order and sprint-pack execution rule.
- [ ] Document the Core Contracts phase as mandatory before cross-domain model duplication begins.
- [ ] Document the fail-closed principle for risk, live, trading, auth, event, and approval workflows.
- [ ] Document that API routes, UI screens, and conversation flows must delegate to governed services and must not own domain decisions.
- [ ] Document that live trading requires staged promotion through read-only, paper, shadow, micro-live, and full-live modes.
- [ ] Define the Sprint-Pack Execution Boundary as mandatory: only one approved sprint pack or explicitly approved phase slice may be implemented at a time.
- [ ] Define that the next sprint pack or phase may not start until the current approved scope has green pre-commit, Ruff check, Ruff format, mypy strict, pytest, and coverage gates.
- [ ] Define that the next sprint pack or phase may not start until the current approved scope has at least 80 percent coverage for each affected file and package, unless an owner-approved documented exception exists.
- [ ] Define that Phase 3 Indicator implementation may not start until Phase 2 Data has green CI, at least 80 percent affected-file/package coverage, passing usage examples, synchronized docs, and an implementation report.
- [ ] Define that Live, UI/API, Research, and Conversation phases may not start to implement governed mutation behavior until their upstream Data, Indicator, Strategy, Risk, Trading, Simulation, Analytics, and Optimization readiness gates are satisfied or explicitly deferred with owner approval.
- [ ] Define that phase advancement is blocked by unresolved safety blockers, stale active documentation, missing changelog entries, skipped usage examples, failing import-safety checks, or unreviewed public contract changes.
- [ ] Define that checklist completion must include evidence references such as command summaries, coverage results, usage example status, docs updated, risk decisions, and rollback path; unchecked boxes may not be marked complete from intent alone.
- [ ] Define that velocity pressure, checklist fatigue, or partial completion may not be used as rationale to bypass safety gates, coverage gates, approval gates, or live-trading promotion gates.

### Unit Tests Required

```text
tests/unit/scaffold/
tests/unit/scripts/
```

Test coverage:

- [ ] Tests verify project imports are side-effect free before optional dependencies are installed.
- [ ] Tests verify the local CI script exposes the approved quality-gate order.
- [ ] Tests verify `.env.example` contains placeholders only and no obvious secret values.
- [ ] Tests verify documentation files required by the lean documentation model exist.
- [ ] Tests verify release and backup check scripts fail clearly when required inputs are missing.

### Usage Examples Required

```text
tests/usage/00_project_scaffold.py
```

Usage examples must show:

- [ ] Example demonstrates running the local validation command in dry-run/report mode.
- [ ] Example demonstrates loading safe environment defaults without broker or network dependencies.
- [ ] Example demonstrates reading the release checklist and producing a bounded readiness summary.

### Acceptance Checklist

- Done criterion: All Phase 0 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Repository scaffold, CI gates, docs baseline, environment template, and release checklist are ready before Phase 1 implementation.
- Done criterion: The project can be imported and tested without optional live-provider dependencies installed.
