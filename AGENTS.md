# Instructions

**Purpose**: Single AI/Builder operating guide for HaruQuantAI.

## 1. Core Operating Directive

- **Durable Memory**: Memory, decisions, and progress live in repository files, **never in chat**.
- **Active Project Documentation**: Set is `AGENTS.md`, `docs/ARCHITECTURE.md`, and `CHANGELOG.md`.
- **Authority Order** Current direct owner instruction -> `AGENTS.md` -> `docs/ARCHITECTURE.md` -> `CHANGELOG.md`.
- **Required Before Action**: Read `AGENTS.md`, `docs/ARCHITECTURE.md`, `CHANGELOG.md` and relevant existing code/tests before planning, editing, or recommending changes.

---

## 2. AI Working & Research Principles

* **Correctness > Speed**: Verify via tools. Never generate code from memory if current docs are a tool call away.
* **State Assumptions & Uncertainty**: Explicitly state inferred versions, frameworks, or scopes. Say "I don't know" rather than guessing. Ask clarifying questions for ambiguous requests.
* **Documentation Tool Strategy** (Use together; mention which informed your answer):
  * **WebSearch**: Community consensus, modern best practices, real-world patterns, known footguns/critiques.
  * **Context7**: Official docs, exact API signatures, version-specific features, deprecation checks.
  * **DeepWiki**: Internal design intent, canonical usage (tests/examples), architectural "why".
* **Research Workflow**: **1. WebSearch** (landscape) → **2. Context7** (verify syntax/deprecations) → **3. DeepWiki** (design intent).
* **Handle Disagreements**: If sources diverge (e.g., official docs vs. test suite reality), explicitly call out the divergence and explain the tradeoff. Do not silently pick a side.
* **Version Handling**: Always confirm library versions before coding. Default to **`pyproject.toml` pinned version or latest stable. Verify against Context7 to avoid deprecated APIs. Explicitly state the version used in your output.

## 3. Builder Role & Execution Rules

- **Dry Run Required**: Before editing, report: files read/changed, commands/tests planned, scope boundaries, blockers/risks, and rollback path.
- **Approval Gate**: Wait for the exact phrase `APPROVED: EXECUTE` before modifying files.
- **Scope Control**: Work only in approved scope. Do not invent requirements, risk limits, or trading rules. Do not perform broad refactors without approval.
- **No Guessing**: If info is missing, check active docs. If still missing, stop and report as `Pending`, `Assumption`, or `Proposed Decision`.
- **Final Report**: After any task, report files changed, decisions/risks updated, commands run, validation results, and rollback path. Use positive checklist wording (e.g., `[X] Scope followed`) Also if a checklist exist for the task, update it with a [X] or [ ] before the response.

---

## 4. Code Quality Standard

- **Pre-commit Order**: `trailing-whitespace` → `end-of-file-fixer` → `check-yaml/toml` → `check-added-large-files` → `detect-secrets` → `ruff` (lint/auto-fix) → `ruff-format` → `mypy --strict` (strict static types) → `pytest`.
- **Python Code Layout Checklist**:
  - File-level docstring (purpose, exports, side effects).
  - Small focused functions.
  - Separation of business logic from I/O.
  - Deterministic behavior.
  - Public functions/classes have Google-style docstrings (what, when, args, returns, errors).
  - Explicit type hints on all function arguments and return values.
  - Input and output validation enforced.
  - Logging standard: Use `from tools.utils import logger` (use `print()` in examples only never in production). Use logging for important events, warnings, validation failures and recoverable errors.
  - Explicit error handling: No silent failures. No bare `except:`. Catch, log, and return structured errors.
  - Testing: `pytest` required. **80% minimum coverage gate** at both individual file and package level. Test normal usage, edge cases, invalid input, and error paths.
  - Security: Never commit secrets. Redact sensitive values in logs/errors. `.env.example` only.

---

## 5. Tool Function Standard

- **Core Principle**: Only functions exposed in `tools/<domain>/__init__.py` (`__all__`) are Official AI Tools. Internal helpers (`_name`) are exempt from full standard but must be typed/documented.
- **Imports Rule**: Agents must import from the domain, never deep:

  - ✅ `from tools.data import get_market_data`
  - ❌ `from tools.data.market_data import get_market_data`
- **Mandatory Structure - Tool Template & Schema**:

  1. **Metadata**: `TOOL_NAME`, `TOOL_VERSION`, `TOOL_CATEGORY`, `TOOL_RISK_LEVEL` (low/medium/high/critical), `REQUIRES_APPROVAL`, `READS`, `WRITES`, `TRADES`, `REQUIRES_NETWORK`.
  2. **Signature**: Outward-facing tools must accept `request_id: str | None = None` for traceability.
  3. **Validation**: Validate inputs first. Return `INVALID_INPUT` schema if failed.
  4. **Execution**: `try/except` block. Log `called`, `success`, or `exception` via `from tools.utils import logger`. Include `request_id`.
  5. **Standard Return Schema** Tools must **never** return `None` or raw exceptions. Always return this exact dictionary structure:

  ```json
  {
    "status": "success" | "error",
    "message": "Human/AI-readable summary string",
    "data": <Any valid payload or null>,
    "error": null | {"code": "ERROR_CODE", "details": "Specific explanation"},
    "metadata": {
      "tool_name": str, "tool_version": str, "tool_category": str, "tool_risk_level": "low" | "medium" | "high" | "critical",
      "request_id": str | null, "execution_ms": float,
      "reads": bool, "writes": bool, "updates": bool, "deletes": bool, "trades": bool, "requires_network": bool
    }
  }
  ```

  6. **Allowed Tool Error Codes**: `INVALID_INPUT`, `PERMISSION_DENIED`, `DATA_NOT_FOUND`, `EMPTY_RESULT`, `SERVICE_UNAVAILABLE`, `BROKER_UNAVAILABLE`, `DATABASE_ERROR`, `NETWORK_ERROR`, `TIMEOUT`, `VALIDATION_FAILED`, `TOOL_EXECUTION_FAILED`, `UNKNOWN_ERROR`.
  7. **Testing**: Unit tests (`tests/unit/tools/<domain>/test_<file>.py`) and real-world usage examples (`tests/usage/...`) required for all exported tools.

---

## 6. Agent Design Standard

- **Core Principle**: Few agents, many tools, strict contracts, deterministic gates. Registry at `haruquant/agentic/registry.py`. Flat-first structure (`agentic/agents/{department}.py`). Folders only when complexity earns them.
- **Agent vs Tool**: If it fetches, calculates, validates, or executes → **Tool**. If it decides, interprets, plans, delegates, or recommends → **Agent**.
- **Mandatory Metadata**: `AGENT_NAME`, `AGENT_VERSION`, `AGENT_DEPARTMENT`, `AGENT_DESCRIPTION`, `AGENT_RISK_LEVEL`, `AGENT_REQUIRES_APPROVAL`, `AGENT_INPUT_CONTRACT`, `AGENT_OUTPUT_CONTRACT`, permissions (`CAN_PLACE_TRADES`, `CAN_APPROVE_RISK`), `ALLOWED_TOOLS`, `BLOCKED_TOOL_NAMES`, and a builder function `build_{name}_agent() -> Agent` returning a Google ADK Agent.  Must log construction. Must not execute tools or mutate state during build.
- **Standard Instruction Structure**: Agent instruction must contain these 10 sections: `Role`, `Responsibilities`, `Non-Goals`, `Allowed Tools`, `Blocked Actions`, `Required Evidence`, `Output Contract`, `Safety Rules`, `Uncertainty Behavior`, and `Escalation Rules`.
- **Standard Agent Response Schema**: Agent runtimes must normalize all agent outputs to this structure:
  ```json
  {
    "status": "success" | "error" | "blocked" | "needs_approval" | "needs_clarification",
    "message": "Human/AI-readable summary",
    "data": <Payload or null>,
    "decision": <Decision payload or null>,
    "evidence": ["Cited sources / tool results"],
    "tool_calls": ["Tool call records"],
    "error": null | {"code": "ERROR_CODE", "details": "..."},
    "metadata": {
      "agent_name": str, "agent_version": str, "agent_department": str, "agent_risk_level": str,
      "request_id": str, "workflow_id": str, "execution_ms": float,
      "input_contract": str, "output_contract": str, "approval_required": bool
    }
  }
  ```
- **Allowed Agent Error Codes**: `INVALID_INPUT`, `MISSING_EVIDENCE`, `STALE_EVIDENCE`, `CONFLICTING_EVIDENCE`, `TOOL_FAILURE`, `POLICY_BLOCKED`, `PERMISSION_DENIED`, `APPROVAL_REQUIRED`, `OUTPUT_CONTRACT_FAILED`, `AGENT_EXECUTION_FAILED`.
- **Traceability**: `request_id` and `workflow_id` are mandatory and must propagate through runtime, tools, policy, and audit logs.
- **Evidence Discipline**: Agents must never invent backtest results, live performance, or broker fills. Missing/stale evidence must be explicitly disclosed.
- **Testing**: Unit tests (builder, metadata, instructions, blocked tools), Usage examples (`tests/usage/agentic/...`), and Evaluation scenarios (missing evidence, unsafe requests).

---

## 7. Non-Negotiable Safety & Governance

1. **Fail-Closed**: If policy is uncertain or evidence is missing, block the action.
2. **No Live Action by Default**: Live trading, risk changes, and execution state mutations require explicit, deterministic approval.
3. **Kill Switch**: Deterministic. An LLM **cannot** override or bypass a kill switch.
4. **No Invented Data**: Agents must never invent backtest results, live performance, or broker fills.
5. **Deterministic Policy**: LLMs explain policy; Python code (`agentic/policy.py`) must enforce it.
6. **Conversation Boundary**: AI can draft/explain/plan, but **cannot** directly execute governed/broker actions.

## 8. Project Documentation Update Rules

Update active docs whenever project meaning changes:

- Architecture, API, data models, security, testing, observability → `docs/ARCHITECTURE.md`
- Sprint state, decisions, risks, blockers, added features, pending decisions → `CHANGELOG.md`
- AI/Builder workflow rules → `AGENTS.md`

## 9. Command Rules

- **Safe**: `pwd`, `ls`, `cat`, `grep`, `git status`, `git diff`, `pytest`, `ruff check .`, `mypy .`
- **Restricted (Requires Explicit Approval)**: `rm -rf`, `git reset`, `git clean`, `pip install`, `npm install`, `docker compose`, live broker calls, real email/Telegram sends, destructive SQL.

## 10. Final Checklist (Must be satisfied before finishing)

- [ ] Scope was strictly followed.
- [ ] Required docs were read; no requirements/rules were invented.
- [ ] Code quality standards (types, docstrings, logging, error handling) applied.
- [ ] Tools/Agents follow their respective compressed standards (schemas, metadata, imports).
- [ ] No secrets or live side effects introduced.
- [ ] Affected active docs (`ARCHITECTURE.md`, `CHANGELOG.md`) updated.
- [ ] Validation/tests and usage examples run and passed.
- [ ] Rollback path identified and reported.
