# HaruQuant Agent Standard

## 1. Core Principle

**Few agents, many tools, strict contracts, deterministic gates.**
An agent exists *only* to decide, interpret, review, plan, delegate, or recommend. If it only fetches, calculates, validates, or executes, it must be a **Tool**, not an Agent.

## 2. Directory & Import Structure

- **Structure**: Flat-first. `haruquant/agentic/agents/{department}.py` (e.g., `research.py`, `execution.py`). Split into folders *only* when complexity demands it.
- **Registry**: `haruquant/agentic/registry.py` is the single source of truth for agent discovery.
- **Import Rule**: Agents must import tools from domain packages, never deep.
  - ✅ `from haruquant.tools.data import get_market_data`
  - ❌ `from haruquant.tools.data.market_data import get_market_data`

## 3. Standard Agent File Template

Every agent file must follow this exact structure to ensure safety, traceability, and ADK compatibility:

```python
from __future__ import annotations
import logging
from google.adk.agents import Agent
from agentic.config.agent_model import AGENT_MODEL
from tools.data import get_market_data # Import from domain

from tools.utils import logger

# 1. Metadata
AGENT_NAME = "research_lead"
AGENT_VERSION = "1.0.0"
AGENT_DEPARTMENT = "research"
AGENT_DESCRIPTION = "Coordinates market research and produces evidence packs."
AGENT_RISK_LEVEL = "medium" # low, medium, high, critical
AGENT_REQUIRES_APPROVAL = False
AGENT_INPUT_CONTRACT = "AgentRequest"
AGENT_OUTPUT_CONTRACT = "ResearchEvidencePack"

# 2. Permissions & Tool Boundaries
CAN_PLACE_TRADES = False
CAN_APPROVE_RISK = False
ALLOWED_TOOLS = [get_market_data]
BLOCKED_TOOL_NAMES = ["place_order", "close_position", "activate_live_trading"]

# 3. Agent Instruction (Must contain all 10 required sections)
RESEARCH_LEAD_INSTRUCTION = """
# Role
You are the HaruQuant Research Lead Agent.
# Responsibilities
- Understand requests, gather evidence via approved tools, produce ResearchEvidencePack.
# Non-Goals
- Do not place trades, approve risk, or invent data.
# Allowed Tools
Use only tools attached to this agent.
# Blocked Actions
Live trading, broker execution, risk approval.
# Required Evidence
Conclusions must cite tool results or clearly marked assumptions.
# Output Contract
Return a ResearchEvidencePack-compatible response.
# Safety Rules
Disclose missing, stale, or conflicting evidence. Escalate if approval is needed.
# Uncertainty Behavior
Ask for clarification when the request cannot be safely completed.
# Escalation Rules
Escalate strategy design to Strategy agents, risk to Risk agents.
"""

# 4. Builder Function
def build_research_lead_agent() -> Agent:
    """
    Builds the Research Lead Agent.
    Returns: Configured Google ADK Agent instance.
    """
    logger.info(f"Building agent | name={AGENT_NAME} | version={AGENT_VERSION} | risk={AGENT_RISK_LEVEL}")

    return Agent(
        name=AGENT_NAME,
        model=AGENT_MODEL,
        description=AGENT_DESCRIPTION,
        instruction=RESEARCH_LEAD_INSTRUCTION,
        tools=ALLOWED_TOOLS,
    )
```

## 4. Standard Agent Return Schema (Mandatory)

Agent runtimes must normalize all outputs into this exact structure. Never return raw, unstructured LLM output to a workflow.

```json
{
  "status": "success" | "error" | "blocked" | "needs_approval" | "needs_clarification",
  "message": "Human/AI-readable summary string",
  "data": <Normalized payload or null>,
  "decision": <Any decision object or null>,
  "evidence": ["List of evidence sources or tool results"],
  "tool_calls": ["List of tool call records"],
  "error": null | {"code": "ERROR_CODE", "details": "Specific explanation"},
  "metadata": {
    "agent_name": str, "agent_version": str, "agent_department": str, "agent_risk_level": str,
    "request_id": str, "workflow_id": str, "execution_ms": float,
    "input_contract": str, "output_contract": str, "approval_required": bool
  }
}
```

**Allowed Error Codes**: `INVALID_INPUT`, `MISSING_EVIDENCE`, `STALE_EVIDENCE`, `CONFLICTING_EVIDENCE`, `TOOL_FAILURE`, `POLICY_BLOCKED`, `PERMISSION_DENIED`, `APPROVAL_REQUIRED`, `OUTPUT_CONTRACT_FAILED`, `AGENT_EXECUTION_FAILED`.

## 5. Mandatory Rules Checklist

- [ ] **Docstrings**: File-level (purpose, agents, builders, tools, contracts, risk, safety) + Builder-level.
- [ ] **Metadata**: All 8 metadata constants defined at the top of the file.
- [ ] **Permissions**: Explicit boolean declarations matching the agent's real scope.
- [ ] **Tool Boundaries**: Explicit `ALLOWED_TOOLS` list and `BLOCKED_TOOL_NAMES` list.
- [ ] **Instruction Completeness**: Must contain all 10 sections: Role, Responsibilities, Non-Goals, Allowed Tools, Blocked Actions, Required Evidence, Output Contract, Safety Rules, Uncertainty Behavior, Escalation Rules.
- [ ] **Traceability**: Runtime must enforce and propagate `request_id` and `workflow_id` across all logs, audits, and tool calls.
- [ ] **Logging**: Log agent build, run started, tool calls, policy checks, run completed/failed/blocked, and `execution_ms`. Never log secrets.
- [ ] **Audit Footprint**: High/medium risk runs must emit an append-friendly audit record (timestamp, IDs, agent info, tools called, evidence, decision, policy result).
- [ ] **Testing**: Unit tests (builder, metadata, instructions, blocked tools), Usage examples (real execution via runtime), and Evaluation scenarios (missing evidence, unsafe requests).

## 6. Non-Negotiable Safety Rules

1. **Fail-Closed**: If policy is uncertain or evidence is missing, block the action. Do not guess.
2. **No Live Action by Default**: Live trading, risk increases, and execution state changes require explicit, deterministic approval.
3. **Kill Switch**: An LLM cannot override or bypass a kill switch.
4. **No Invented Data**: Agents must never invent backtest results, live performance, or broker fills. Stale/missing evidence must be explicitly disclosed.
5. **Deterministic Policy**: LLMs may explain policy, but Python code (`agentic/policy.py`) must enforce it.

---
