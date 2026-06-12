# HaruQuant Tool Function Auditing Checklist

> Production-ready audit checklist for HaruQuantAI-callable tool functions.

## Purpose

This checklist verifies whether a HaruQuantAI tool function is agent-safe, production-ready, testable, auditable, and compliant with the HaruQuantAI Tool Function Standard.

It applies to tools under the tools folder:

```text
    tools/
        data/
            __init__.py
            market_data.py
            validators.py

        execution/
            __init__.py
            orders.py
            positions.py

        risk/
            __init__.py
            governor.py
            exposure.py

        analytics/
            __init__.py
            metrics.py
            ratios.py
```

---

## 1. Core Rule

Any function exposed through a tool domain `__init__.py` is an official AI Tool.

Any official AI Tool must follow the HaruQuantAI Tool Function Standard.

A function is an AI Tool if it is imported and listed in `__all__`.

A function not exposed through `__init__.py` is considered internal.

---

## 2. Audit Scoring Guide

Each checklist item should be scored from `0` to `3`.

| Score | Meaning                                             |
| ----: | --------------------------------------------------- |
|     0 | Missing completely                                  |
|     1 | Mentioned but vague, informal, or incomplete        |
|     2 | Present, usable, and documented                     |
|     3 | Production-grade, implemented, tested, and enforced |

The master score is normalized out of exactly `1000`.

Critical fail conditions override numeric score.

---

## 3. Critical Fail Conditions

A tool fails immediately if any item below is true.

| Critical Fail Condition                                                                 | Pass/Fail | Evidence / Notes |
| --------------------------------------------------------------------------------------- | --------- | ---------------- |
| Tool can place/close/modify live trades without approval metadata and permission checks |           |                  |
| Tool can modify risk, policy, or safety settings without approval metadata and checks   |           |                  |
| Tool silently fails or returns `None`                                                 |           |                  |
| Tool returns inconsistent/unstructured outputs                                          |           |                  |
| Tool exposes secrets, broker credentials, API keys, or tokens in logs or returns        |           |                  |
| Tool has no input validation                                                            |           |                  |
| Tool has no error handling                                                              |           |                  |
| Tool catches exceptions but hides the failure                                           |           |                  |
| Tool mutates state but declares `READ_ONLY = True`                                    |           |                  |
| Tool places trades but declares `PLACES_TRADE = False`                                |           |                  |
| Tool is exported in `__all__` but cannot be imported                                  |           |                  |
| Tool is attached to agents but is not listed in any domain `__all__`                  |           |                  |
| High-risk or critical tool has no tests                                                 |           |                  |
| High-risk or critical tool has no audit/logging footprint                               |           |                  |
| Live execution tool does not fail closed                                                |           |                  |

---

## 4. Tool Domain Structure Checklist

| Check                                                             | Yes/No | Score | Evidence / Notes |
| ----------------------------------------------------------------- | -----: | ----: | ---------------- |
| Tool lives under `tools/{domain}/`                              |        |       |                  |
| Domain folder has `__init__.py`                                 |        |       |                  |
| Implementation lives in a normal module file, not `__init__.py` |        |       |                  |
| Domain has clear responsibility                                   |        |       |                  |
| Domain is not a mixed god tool folder                             |        |       |                  |
| Tools are grouped by source file logically                        |        |       |                  |
| Internal helpers are not accidentally exported                    |        |       |                  |
| Agents import from domain package, not deep implementation files  |        |       |                  |

---

## 5. `__init__.py` Registry Checklist

| Check                                                 | Yes/No | Score | Evidence / Notes |
| ----------------------------------------------------- | -----: | ----: | ---------------- |
| `__init__.py` has file-level docstring              |        |       |                  |
| `__init__.py` contains no implementation logic      |        |       |                  |
| `__init__.py` imports approved tools only           |        |       |                  |
| `__all__` exists                                    |        |       |                  |
| Every imported public tool is listed in `__all__`   |        |       |                  |
| Every item in `__all__` imports successfully        |        |       |                  |
| `__all__` is organized by source file comments      |        |       |                  |
| Empty line separates tool groups                      |        |       |                  |
| No private helper is listed in `__all__`            |        |       |                  |
| No deprecated or unsafe tool is exported accidentally |        |       |                  |

Expected pattern:

```python
# market_data.py tools
from tools.data.market_data import get_market_data

# validators.py tools
from tools.data.validators import validate_ohlcv_quality

__all__ = [
    "get_market_data",
    "validate_ohlcv_quality",
]
```

---

## 6. Tool Classification and Metadata Checklist

Required constants:

```python
TOOL_NAME = "get_market_data"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = True
```

| Check                                   | Yes/No | Score | Evidence / Notes |
| --------------------------------------- | -----: | ----: | ---------------- |
| Tool name is declared                   |        |       |                  |
| Tool version is declared                |        |       |                  |
| Tool category is declared               |        |       |                  |
| Tool risk level is declared             |        |       |                  |
| Approval requirement is declared        |        |       |                  |
| Read/write behavior is declared         |        |       |                  |
| Database mutation behavior is declared  |        |       |                  |
| File-writing behavior is declared       |        |       |                  |
| Trading behavior is declared            |        |       |                  |
| Network requirement is declared         |        |       |                  |
| Declared metadata matches real behavior |        |       |                  |

---

## 7. File and Entity Docstring Checklist

| Check                                        | Yes/No | Score | Evidence / Notes |
| -------------------------------------------- | -----: | ----: | ---------------- |
| Python file starts with file-level docstring |        |       |                  |
| Docstring states file purpose                |        |       |                  |
| Docstring lists exported AI Tools            |        |       |                  |
| Docstring lists internal helpers             |        |       |                  |
| Every exported tool has detailed docstring   |        |       |                  |
| Tool docstring is agent-facing               |        |       |                  |
| Tool docstring states when to use tool       |        |       |                  |
| Tool docstring states arguments              |        |       |                  |
| Tool docstring states return schema          |        |       |                  |
| Tool docstring states possible errors        |        |       |                  |
| Tool docstring states side effects           |        |       |                  |

---

## 8. Function Signature Checklist

| Check                                                                           | Yes/No | Score | Evidence / Notes |
| ------------------------------------------------------------------------------- | -----: | ----: | ---------------- |
| Tool has type hints for all parameters                                          |        |       |                  |
| Tool has standard response return type                                          |        |       |                  |
| Tool supports `request_id: Optional[str] = None` where applicable             |        |       |                  |
| Required parameters do not have unsafe defaults                                 |        |       |                  |
| Optional parameters have safe defaults                                          |        |       |                  |
| Parameter names are agent-readable                                              |        |       |                  |
| No raw ambiguous `*args`/`**kwargs` for agent-facing tools unless justified |        |       |                  |

---

## 9. Standard Tool Response Schema Checklist

Every AI Tool must return:

```python
{
    "status": "success" | "error",
    "message": str,
    "data": Any,
    "error": None | {
        "code": str,
        "details": str,
    },
    "metadata": {
        "tool_name": str,
        "tool_version": str,
        "tool_category": str,
        "tool_risk_level": str,
        "request_id": str | None,
        "execution_ms": float,
        "read_only": bool,
        "writes_file": bool,
        "modifies_database": bool,
        "places_trade": bool,
        "requires_network": bool,
    },
}
```

| Check                                            | Yes/No | Score | Evidence / Notes |
| ------------------------------------------------ | -----: | ----: | ---------------- |
| Return always includes `status`                |        |       |                  |
| Return always includes `message`               |        |       |                  |
| Return always includes `data`                  |        |       |                  |
| Return always includes `error`                 |        |       |                  |
| Return always includes `metadata`              |        |       |                  |
| Success response sets `error = None`           |        |       |                  |
| Error response includes deterministic error code |        |       |                  |
| Metadata includes tool identity                  |        |       |                  |
| Metadata includes execution time                 |        |       |                  |
| Metadata includes side-effect declarations       |        |       |                  |
| Tool never returns `None`                      |        |       |                  |
| Tool never returns raw exception object          |        |       |                  |

---

## 10. Error Code Checklist

Allowed common error codes:

```text
INVALID_INPUT
PERMISSION_DENIED
DATA_NOT_FOUND
EMPTY_RESULT
SERVICE_UNAVAILABLE
BROKER_UNAVAILABLE
DATABASE_ERROR
NETWORK_ERROR
TIMEOUT
VALIDATION_FAILED
TOOL_EXECUTION_FAILED
UNKNOWN_ERROR
```

| Check                                                                       | Yes/No | Score | Evidence / Notes |
| --------------------------------------------------------------------------- | -----: | ----: | ---------------- |
| Tool uses deterministic error codes                                         |        |       |                  |
| Invalid input returns `INVALID_INPUT`                                     |        |       |                  |
| Permission failure returns `PERMISSION_DENIED`                            |        |       |                  |
| Empty result is distinguished from execution failure                        |        |       |                  |
| Broker failure is distinguished from generic failure                        |        |       |                  |
| Network failure is distinguished where applicable                           |        |       |                  |
| Unexpected exception returns `TOOL_EXECUTION_FAILED` or `UNKNOWN_ERROR` |        |       |                  |
| Error details do not leak secrets                                           |        |       |                  |

---

## 11. Input Validation Checklist

| Check                                                    | Yes/No | Score | Evidence / Notes |
| -------------------------------------------------------- | -----: | ----: | ---------------- |
| Required inputs are validated                            |        |       |                  |
| Type assumptions are validated                           |        |       |                  |
| Enum/string choices are validated                        |        |       |                  |
| Numeric ranges are validated                             |        |       |                  |
| Date ranges are validated where applicable               |        |       |                  |
| Timeframes are validated where applicable                |        |       |                  |
| Symbols/assets are validated where applicable            |        |       |                  |
| File paths are sanitized where applicable                |        |       |                  |
| Order sizes/risk values are validated where applicable   |        |       |                  |
| Invalid input returns standard error response            |        |       |                  |
| Tool does not execute core logic after failed validation |        |       |                  |

---

## 12. Core Execution and Dependency Checklist

| Check                                                          | Yes/No | Score | Evidence / Notes |
| -------------------------------------------------------------- | -----: | ----: | ---------------- |
| Core logic is clear and bounded                                |        |       |                  |
| Tool does one coherent job                                     |        |       |                  |
| Tool is not a large hidden workflow unless explicitly intended |        |       |                  |
| External calls have timeout/retry handling where applicable    |        |       |                  |
| Broker/API/database clients are handled safely                 |        |       |                  |
| Expensive operations are bounded                               |        |       |                  |
| Empty results are handled intentionally                        |        |       |                  |
| Tool avoids hidden state mutation                              |        |       |                  |
| Tool avoids global mutable state unless justified              |        |       |                  |
| Tool handles dependencies unavailable                          |        |       |                  |

---

## 13. Permission and Approval Checklist

Mandatory for high-risk and critical tools.

| Check                                                    | Yes/No | Score | Evidence / Notes |
| -------------------------------------------------------- | -----: | ----: | ---------------- |
| Tool has conservative risk level                         |        |       |                  |
| `REQUIRES_APPROVAL` matches risk                       |        |       |                  |
| Critical tools require explicit approval input/check     |        |       |                  |
| Permission denial returns standard error                 |        |       |                  |
| Live trading tools fail closed                           |        |       |                  |
| Risk-changing tools fail closed                          |        |       |                  |
| Tool cannot disable safeguards without approval          |        |       |                  |
| Tool cannot bypass kill switch                           |        |       |                  |
| Approval result is logged                                |        |       |                  |
| Approval result is included in metadata where applicable |        |       |                  |

---

## 14. Logging and Traceability Checklist

| Check                                                 | Yes/No | Score | Evidence / Notes |
| ----------------------------------------------------- | -----: | ----: | ---------------- |
| File imports `logger`                              |        |       |                  |
| Tool logs when called                                 |        |       |                  |
| Tool logs `request_id` where provided               |        |       |                  |
| Tool logs validation failure                          |        |       |                  |
| Tool logs successful completion                       |        |       |                  |
| Tool logs execution failure with `logger.exception` |        |       |                  |
| Tool logs execution time                              |        |       |                  |
| Tool does not log credentials/secrets                 |        |       |                  |
| Tool includes `request_id` in metadata              |        |       |                  |
| Tool call can be traced from agent run to tool result |        |       |                  |

---

## 15. No Silent Failure Checklist

| Check                                                         | Yes/No | Score | Evidence / Notes |
| ------------------------------------------------------------- | -----: | ----: | ---------------- |
| Tool never returns `None`                                   |        |       |                  |
| Tool never silently swallows exceptions                       |        |       |                  |
| Tool never prints error instead of returning structured error |        |       |                  |
| Tool never returns ambiguous mixed formats                    |        |       |                  |
| Tool distinguishes success with empty result from failure     |        |       |                  |
| Tool gives clear failure message                              |        |       |                  |
| Tool gives deterministic error code                           |        |       |                  |
| Failed result cannot be mistaken for success                  |        |       |                  |

---

## 16. Import Boundary Checklist

| Check                                                                 | Yes/No | Score | Evidence / Notes |
| --------------------------------------------------------------------- | -----: | ----: | ---------------- |
| Agents import tool from domain package                                |        |       |                  |
| Tool implementation avoids circular imports                           |        |       |                  |
| Tool does not import from another domain's deep file unless justified |        |       |                  |
| Shared helpers are placed in appropriate shared utilities             |        |       |                  |
| `__init__.py` remains a registry only                               |        |       |                  |
| Tool dependencies are clear                                           |        |       |                  |
| Tool does not depend on agent internals                               |        |       |                  |

---

## 17. Unit Testing Checklist

Recommended location:

```text
tests/unit/tools/{domain}/test_{source_file}.py
```

| Check                                                       | Yes/No | Score | Evidence / Notes |
| ----------------------------------------------------------- | -----: | ----: | ---------------- |
| Unit test file exists                                       |        |       |                  |
| Every function in domain `__all__` is tested              |        |       |                  |
| Successful call test exists                                 |        |       |                  |
| Invalid input test exists                                   |        |       |                  |
| Empty result test exists where applicable                   |        |       |                  |
| Service/dependency failure test exists where applicable     |        |       |                  |
| Standard return schema test exists                          |        |       |                  |
| Metadata correctness test exists                            |        |       |                  |
| Error code correctness test exists                          |        |       |                  |
| Logging footprint test exists                               |        |       |                  |
| Permission denial test exists for high-risk tools           |        |       |                  |
| Critical/live tool fail-closed test exists where applicable |        |       |                  |

---

## 18. Usage Example Checklist

Recommended location:

```text
tests/usage/tools/{domain}/{source_file}.py
```

| Check                                                  | Yes/No | Score | Evidence / Notes |
| ------------------------------------------------------ | -----: | ----: | ---------------- |
| Usage example file exists                              |        |       |                  |
| Every exported function has a usage example            |        |       |                  |
| Usage imports from domain package                      |        |       |                  |
| Usage uses realistic inputs                            |        |       |                  |
| Usage includes `request_id` where applicable         |        |       |                  |
| Usage demonstrates success handling                    |        |       |                  |
| Usage demonstrates error handling                      |        |       |                  |
| Usage avoids mocks                                     |        |       |                  |
| Usage shows how an agent/workflow would consume result |        |       |                  |

---

## 19. Documentation and Security Checklist

| Check                                               | Yes/No | Score | Evidence / Notes |
| --------------------------------------------------- | -----: | ----: | ---------------- |
| Tool is documented in file docstring                |        |       |                  |
| Domain `__init__.py` documents exported tools     |        |       |                  |
| Usage example exists                                |        |       |                  |
| Risk/side effects are documented                    |        |       |                  |
| Error behavior is documented                        |        |       |                  |
| Approval requirement is documented where applicable |        |       |                  |
| Tool does not expose secrets in return values       |        |       |                  |
| Tool does not expose secrets in logs                |        |       |                  |
| Tool validates external/untrusted data              |        |       |                  |
| Tool enforces least privilege                       |        |       |                  |

---

## 20. Trading and Broker Safety Checklist

Mandatory for execution, risk, and portfolio tools.

| Check                                                              | Yes/No | Score | Evidence / Notes |
| ------------------------------------------------------------------ | -----: | ----: | ---------------- |
| Broker/account-changing behavior is explicitly declared            |        |       |                  |
| Live order tools have `TOOL_RISK_LEVEL = "critical"`             |        |       |                  |
| Live order tools have `REQUIRES_APPROVAL = True`                 |        |       |                  |
| Live order tools have `PLACES_TRADE = True`                      |        |       |                  |
| Live order tools validate symbol                                   |        |       |                  |
| Live order tools validate volume/lot size                          |        |       |                  |
| Live order tools validate order type                               |        |       |                  |
| Live order tools validate stop loss / take profit where applicable |        |       |                  |
| Live order tools check kill switch state                           |        |       |                  |
| Live order tools check risk approval                               |        |       |                  |
| Live order tools fail closed on broker uncertainty                 |        |       |                  |
| Live order tools return broker action reference safely             |        |       |                  |
| Live order tools are tested with permission denial                 |        |       |                  |
| Live order tools are tested with broker unavailable                |        |       |                  |

---

## 21. Master Tool Audit Summary

| Area                                    | Includes Sections   |      Max Score | Actual Score | Pass/Fail | Evidence / Notes |
| --------------------------------------- | ------------------- | -------------: | -----------: | --------- | ---------------- |
| Critical Fail Conditions                | Section 4           |       Required |              |           |                  |
| Domain and Registry Structure           | Sections 5–6       |            130 |              |           |                  |
| Classification, Docstrings, Signature   | Sections 7–9       |            150 |              |           |                  |
| Return Schema and Error Handling        | Sections 10–12, 16 |            190 |              |           |                  |
| Execution, Permission, Approval         | Sections 13–14     |            150 |              |           |                  |
| Logging, Traceability, Imports          | Sections 15, 17     |            140 |              |           |                  |
| Testing and Usage                       | Sections 18–19     |            160 |              |           |                  |
| Documentation, Security, Trading Safety | Sections 20–21     |             80 |              |           |                  |
| **Total**                         |                     | **1000** |              |           |                  |

---

## 22. Audit Decision Rule

A tool is production-ready only if:

1. It passes all critical fail checks.
2. It is correctly exported through domain `__init__.py`.
3. It scores at least 90%.
4. It has standard return schema.
5. It has input validation.
6. It has error handling.
7. It has logging footprint.
8. It has unit tests.
9. It has usage examples.
10. It has correct risk and side-effect metadata.
11. It passes relevant CI/quality gates.

For high-risk and critical tools, also require:

1. Approval enforcement.
2. Permission denial tests.
3. Fail-closed behavior.
4. Audit/logging of high-risk events.
5. Trading/broker safety tests where applicable.

---

## 23. Recommended Tool Audit Workflow

1. Inspect `tools/{domain}/__init__.py`.
2. Use `__all__` as the source of truth.
3. List every exported tool.
4. Verify each function exists and imports correctly.
5. Run critical fail review.
6. Score checklist sections.
7. Run unit tests:

```bash
pytest tests/unit/tools -q
```

1. Run usage examples:

```bash
python tests/usage/tools/{domain}/{source_file}.py
```

1. Record final decision:

```text
Approved
Approved with minor fixes
Needs refactor
Rejected / redesign required
```

---

## 24. Tool Audit Report Template

```markdown
# Tool Function Audit Report: <domain>/<source_file.py>

## 1. Domain Summary
## 2. Registry Review
## 3. Exported Tool List
## 4. Critical Fail Review
## 5. File-Level Review
## 6. Tool-by-Tool Compliance Review
## 7. Return Schema Review
## 8. Input Validation Review
## 9. Error Handling Review
## 10. Logging and Traceability Review
## 11. Risk and Side-Effect Review
## 12. Unit Test Review
## 13. Usage Example Review
## 14. Security Review
## 15. Trading/Broker Safety Review where applicable
## 16. Master Score
## 17. Decision
## 18. Required Remediation
```

Compliance table:

```markdown
| Domain | File | Tool | Exported in __all__ | Return Schema | Metadata | Logging | Tests | Usage | Risk | Status |
|---|---|---|---|---|---|---|---|---|---|---|
```

---

## 25. Definition of Done

A tool audit is complete only when:

```text
[ ] Domain __init__.py reviewed
[ ] __all__ reviewed
[ ] Every exported tool identified
[ ] Critical fail conditions reviewed
[ ] Full checklist scored
[ ] Evidence recorded
[ ] Unit tests checked
[ ] Usage examples checked
[ ] Risk metadata checked
[ ] Logging footprint checked
[ ] Security checked
[ ] Trading/broker safety checked where applicable
[ ] Final decision recorded
[ ] Remediation tasks created if needed
```
