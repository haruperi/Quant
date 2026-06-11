# HaruQuant Agentic AI Playbook

## 1. Core Philosophy & Mental Model

- **The Core Loop**: Reason → Plan → **Policy Check** → Act → Observe → Evaluate → Refine / Compensate / Finish.
- **Golden Rule 1**: The **Host/Orchestrator is the brain** (owns routing, planning, memory, state, policy, approvals, synthesis).
- **Golden Rule 2**: The **Capability Layer is the action/integration bus** (owns standardized access to tools, resources, prompts, and external systems).
- **Golden Rule 3**: Host plans. Adapter connects. Provider executes. Memory stays in the host.

## 2. Layered Architecture

1. **Interface & Routing**: Entry points, intent classification, dispatch, first-pass policy.
2. **Orchestration & Workflow**: Session/context management, task decomposition, conflict sync, conditional routing.
3. **Agent Layer (Workers)**: Persona-defined, tool-augmented LLMs with structured I/O and short/long-term memory.
4. **Capability Bus**: Adapter wrappers connecting to domain-specific Capability Providers (Tools=Do, Resources=Read, Prompts=Guide).
5. **Data & External Systems**: Vector DBs, SQL/NoSQL, APIs, Files.
6. **Evaluation & Observability**: LLM-as-judge, trajectory logs, cost/latency metrics, audit trails.

## 3. Capability Design Standard

- **Tool**: Performs an action (`verb_noun`).
- **Resource**: Exposes read-only state/data (`domain://path`).
- **Prompt**: Reusable instruction template (`*_prompt`).
- **Adapter Pattern**: Encapsulate client logic. Host routes → Adapter calls → Provider executes → Host synthesizes. Never push conversation state into capability providers.

## 4. Agent Anatomy & Governance

Every agent must explicitly declare:

- **Identity**: Persona, Brain (model), Department, Version.
- **Boundaries**: Allowed Tools, Blocked Tools, Input/Output Contracts.
- **Governance**: Policy Profile, Approval Profile, Risk Class, Ownership, Audit Scope.
- **Execution Mode**: Deterministic, LLM-driven, or Hybrid (with explicit boundaries).

## 5. Workflow Orchestration Patterns

- **Sequential**: Linear dependencies with validation gates.
- **Routing**: Heterogeneous requests dispatched to specialists.
- **Parallel**: Independent subtasks gathered by a synthesizer.
- **Evaluator-Optimizer**: Creator → Evaluator → Refine loop until threshold met.
- **Orchestrator-Workers**: Dynamic planning and delegation.
  *Rule*: Document approval checkpoints, compensation design, and escalation triggers for every workflow.

## 6. Memory, State & Context Engineering

- **Memory Types**: Short-term (session), Long-term (vector/DB), Procedural (FSM/policies).
- **State Machine**: Explicit transitions (IDLE → PLANNING → EXECUTING → OBSERVING → EVALUATING → COMPLETE/ERROR). Loops must have max iterations.
- **Context Precedence**: System Policy > Workflow Policy > Session State > Approved User Input > Trusted Resources > Retrieved Docs > Raw Tool Output.
- **Rule**: Validate and sanitize all tool output before reusing it as model context.

## 7. Security, Policy & Approvals

- **Policy Enforcement Layers**: UI/Gateway → Routing → Host/Orchestrator → Tool Wrapper → Capability Provider → Downstream System.
- **Action Risk Classes**:
  - **A**: Read-only (Auto-allowed).
  - **B**: Low-risk write (Policy gate).
  - **C**: Material write (Requires human approval).
  - **D**: High-risk/Financially material (Strict approval + audit).
  - **E**: Irreversible/Prohibited (Deny or special process).
- **Kill Switch**: Deterministic. An LLM **cannot** override or bypass a kill switch. Fail-closed by default.

## 8. Failure Recovery & Idempotency

- Assume retries, partial failures, duplicates, and downstream timeouts will happen.
- **Required**: Idempotency keys, duplicate detection, retry semantics, compensation actions (rollback/mitigation), and clear commit boundaries (Saga pattern).

## 9. Observability & Auditability

- **Mandatory Trace Fields**: `trace_id`, `session_id`, `request_id`, `workflow_id`, `agent_name`, `tool_call_id`, `latency`, `cost`, `status`.
- **Audit Log**: Must capture who requested, who approved, policy applied, evidence used, action taken, timestamp, and compensation (if any).
- **Redaction**: Never log secrets, API keys, or raw sensitive credentials.

## 10. Evaluation & Testing Strategy

- **Evaluation Levels**: Response (output quality), Step (tool/schema validation), Trajectory (end-to-end success, latency, cost).
- **Test Types**: Unit (tools/schemas), Integration (workflows/handoffs), Failure-path (timeouts/malformed output), Contract (schema compatibility), Security (prompt injection), Compensation (rollback behavior).

## 11. HaruQuant Implementation Rules (Non-Negotiable)

- **Structure**: Flat-first. Folders only when complexity earns them.
- **Ratio**: Few agents, many reliable tools.
- **Framework**: Google ADK via standard builder functions.
- **Registry**: `tools/{domain}/__init__.py` is the sole source of truth for tool exports (`__all__`).
- **Traceability**: `request_id` and `workflow_id` must propagate through runtime, agents, tools, policy, and audit logs.
- **Safety**: Deterministic policy gates. LLMs explain policy; Python code enforces it.

## 12. System Design Sequence (10 Steps)

Before coding, define:

1. **Host**: Where orchestration, approvals, and memory live.
2. **Goals**: Primary user, business, and non-functional constraints.
3. **Domains**: Coherent capability boundaries (no "god" servers).
4. **Workflows**: Sequential, routing, parallel, or evaluator-optimizer.
5. **Capabilities**: Classify every domain capability as Tool, Resource, or Prompt.
6. **Trust Boundaries**: Read-only vs. side-effecting, auth requirements.
7. **Transport**: STDIO (local) vs. HTTP/RPC (remote/shared).
8. **Lifecycle**: Initialize → Discover → Operate → Shutdown.
9. **Approvals**: Auto-approved vs. human-required, evidence needed, escalation paths.
10. **Observability**: Trace IDs, prompt versions, redaction rules.

---
