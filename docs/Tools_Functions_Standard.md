# HaruQuantAI Tool Function Standard

## Role

You are an expert AI Systems Architect and Senior Python Developer working on the HaruQuantAI Agentic AI framework.

## Task

Audit, create, or refactor tool functions inside the `tools/` directory so that every agent-callable tool follows the HaruQuantAI Tool Function Standard.

This standard applies to the following structure:

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

Each folder inside `tools/` is a **tool domain**.

Examples:

```text
tools/data/
tools/execution/
tools/risk/
tools/backtesting/
tools/analytics/
tools/strategies/
```

The actual tool implementations live inside normal Python files such as:

```text
market_data.py
validators.py
orders.py
positions.py
governor.py
metrics.py
```

The domain-level `__init__.py` file is the official **tool registry** for that domain.

Agents must import tools from the domain package, not from deep implementation files.

Correct:

```python
from tools.data import get_market_data
from tools.execution import place_order
```

Avoid:

```python
from tools.data.market_data import get_market_data
from tools.execution.orders import place_order
```

---

## Core Rule

Any function exposed through a tool domain `__init__.py` is considered an official AI Tool.

Any official AI Tool must follow this standard.

Any function not exposed through `__init__.py` is considered an internal helper or private implementation detail.

Internal helpers do not need the full AI Tool standard, but they must still be clean, typed, documented, and tested where necessary.

---

## 1. Tool Domain Structure

Each tool domain must follow this structure:

```text
    tools/
        domain_name/
            __init__.py
            file_a.py
            file_b.py
            file_c.py
```

Example:

```text
    tools/
        data/
            __init__.py
            market_data.py
            validators.py
```

The implementation files contain the actual functions.

The `__init__.py` file only exposes approved AI tools.

---

## 2. `__init__.py` Tool Registry Rule

The `__init__.py` file must only be used for routing and exposing approved tools.

It must not contain business logic, calculations, broker logic, database logic, API calls, validation logic, or implementation logic.

Good:

```python
"""
Data tools exposed to HaruQuantAI agents.

Only approved AI-callable data tools should be exported here.
"""

from tools.data.market_data import get_market_data
from tools.data.validators import validate_ohlcv_quality


__all__ = [
    "get_market_data",
    "validate_ohlcv_quality",
]
```

Bad:

```python
def get_market_data(symbol):
    # implementation logic here
    ...
```

---

## 3. Readable `__init__.py` Formatting

The `__init__.py` file must be organized by source file.

Leave an empty line between tool groups.

Add a comment showing the source file.

Example:

```python
"""
Execution tools exposed to HaruQuantAI agents.

This package exposes approved execution-related AI tools.
"""

# orders.py tools
from tools.execution.orders import place_order
from tools.execution.orders import cancel_order

# positions.py tools
from tools.execution.positions import close_position
from tools.execution.positions import get_open_positions


__all__ = [
    # orders.py tools
    "place_order",
    "cancel_order",

    # positions.py tools
    "close_position",
    "get_open_positions",
]
```

---

## 4. Tool Classification Rule

A function is an AI Tool if it is imported and listed in the `__all__` list of a tool domain `__init__.py`.

Example:

```python
__all__ = [
    "get_market_data",
    "validate_ohlcv_quality",
]
```

This means both functions must follow the AI Tool Function Standard.

A function is internal if it is not exposed through `__init__.py`.

Example:

```python
def _normalize_symbol(symbol: str) -> str:
    ...
```

Internal helper functions should usually start with `_`.

---

## 5. File-Level Docstring Rule

Every Python file must start with a file-level docstring.

The docstring must explain:

- purpose of the file
- whether the file contains AI tools or helpers
- list of classes in the file
- list of functions in the file
- which functions are intended to be exported as AI tools

Example:

```python
"""
market_data.py

Provides market data retrieval tools for HaruQuantAI agents.

This file contains AI-callable tools for fetching OHLCV data, tick data,
and symbol metadata.

Exported AI Tools:
    - get_market_data: Fetches OHLCV market data for a symbol and timeframe.

Internal Helpers:
    - _normalize_symbol: Normalizes broker-specific symbol names.
    - _validate_timeframe: Validates supported timeframe values.

Classes:
    None
"""
```

---

## 6. Entity-Level Docstring Rule

Every class and function must have a detailed docstring directly below its definition.

For AI Tools, the docstring must be agent-facing.

It must clearly explain:

- what the tool does
- when an agent should use it
- arguments
- return value
- possible error cases
- side effects, if any

Example:

```python
def get_market_data(symbol: str, timeframe: str = "H1", bars: int = 500) -> Dict[str, Any]:
    """
    Fetches OHLCV market data for a symbol and timeframe.

    Use this tool when an agent needs historical price data for analysis,
    signal generation, backtesting preparation, validation, or charting.

    Args:
        symbol (str): Trading symbol to fetch data for, for example "EURUSD".
        timeframe (str, optional): Candle timeframe, for example "M1", "M5", "H1", or "D1".
            Defaults to "H1".
        bars (int, optional): Number of bars to fetch. Defaults to 500.

    Returns:
        Dict[str, Any]: Standard tool response containing status, message,
        data, error, and metadata.
    """
```

---

## 7. Standard AI Tool Function Template

All functions exposed through `__init__.py` must follow this structure.

```python
from __future__ import annotations

import time
from typing import Any, Dict, Optional


from tools.utils import logger


TOOL_NAME = "standard_tool_template"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "template"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


# @adk.tool  # Uncomment or adjust based on ADK usage.
def standard_tool_template(
    target_asset: str,
    timeframe: str = "H1",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes a standard AI tool operation.

    Use this tool as the reference structure for all HaruQuantAI tools.
    This function demonstrates input validation, logging, structured returns,
    error handling, metadata, timing, and traceability.

    Args:
        target_asset (str): Trading asset, symbol, strategy, or target item
            the tool should operate on.
        timeframe (str, optional): Timeframe used for the operation.
            Defaults to "H1".
        request_id (Optional[str], optional): Optional workflow/request ID used
            to trace the tool call across an agent workflow.

    Returns:
        Dict[str, Any]: Standard tool response with status, message, data,
        error, and metadata.
    """

    started_at = time.perf_counter()

    logger.info(
        "%s called | request_id=%s | target_asset=%s | timeframe=%s",
        TOOL_NAME,
        request_id,
        target_asset,
        timeframe,
    )

    # 1. Input Validation
    if not target_asset:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.warning(
            "%s failed validation | request_id=%s | reason=missing_target_asset",
            TOOL_NAME,
            request_id,
        )

        return {
            "status": "error",
            "message": "Target asset is required.",
            "data": None,
            "error": {
                "code": "INVALID_INPUT",
                "details": "target_asset cannot be empty.",
            },
            "metadata": {
                "tool_name": TOOL_NAME,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        # Replace this block with actual tool logic.
        simulated_result = {
            "metric": 105.4,
            "condition": "stable",
            "target_asset": target_asset,
            "timeframe": timeframe,
        }

        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info(
            "%s completed successfully | request_id=%s | execution_ms=%s",
            TOOL_NAME,
            request_id,
            execution_ms,
        )

        # 3. Structured Return
        return {
            "status": "success",
            "message": "Tool executed successfully.",
            "data": simulated_result,
            "error": None,
            "metadata": {
                "tool_name": TOOL_NAME,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.exception(
            "%s failed | request_id=%s | execution_ms=%s",
            TOOL_NAME,
            request_id,
            execution_ms,
        )

        # 4. Graceful Error Handling
        return {
            "status": "error",
            "message": "Tool execution failed.",
            "data": None,
            "error": {
                "code": "TOOL_EXECUTION_FAILED",
                "details": str(error),
            },
            "metadata": {
                "tool_name": TOOL_NAME,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }
```

---

## 8. Standard Return Schema

Every AI Tool must return a dictionary with this exact top-level structure:

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

A tool must never return `None`.

A tool must never silently fail.

A tool must always return either:

```text
success with data
success with empty data and a clear message
error with a clear reason
```

---

## 9. Standard Error Codes

Use deterministic error codes so agents can reason about failures.

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

Examples:

```python
"error": {
    "code": "INVALID_INPUT",
    "details": "symbol cannot be empty."
}
```

```python
"error": {
    "code": "DATA_NOT_FOUND",
    "details": "No OHLCV data found for EURUSD H1."
}
```

---

## 10. Tool Identity Metadata

Every AI Tool file should define metadata constants near the top of the file or near the tool function.

Required metadata:

```python
TOOL_NAME = "get_market_data"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
```

Risk levels:

```text
low       = read-only, safe, no state mutation
medium    = creates files, runs expensive jobs, writes reports, modifies local artifacts
high      = modifies strategy/risk settings, updates database state, changes configurations
critical  = places trades, closes trades, changes live account state, activates live systems
```

---

## 11. Side-Effect Declaration

Every AI Tool must clearly declare side effects using metadata constants.

Required declarations:

```python
CREATES = False
READS = True
UPDATES = False
DELETES = False
TRADES = False
REQUIRES_NETWORK = False
```

These values must match the real behavior of the tool.

Examples:

Data read tool:

```python
READS = True
CREATES = False
UPDATES = False
TRADES = False
REQUIRES_NETWORK = True
```

Backtest report generation tool:

```python
READ_ONLY = False
CREATES = True
UPDATES = False
TRADES = False
REQUIRES_NETWORK = False
```

Live order tool:

```python
READ_ONLY = False
CREATES = False
UPDATES = True
TRADES = True
REQUIRES_NETWORK = True
TOOL_RISK_LEVEL = "critical"
REQUIRES_APPROVAL = True
```

---

## 12. Permission and Risk Rule

Any tool with one or more of the following must be treated as high-risk or critical:

```text
places trades
closes trades
modifies live broker state
changes risk settings
changes strategy parameters
writes to production database
deletes files
overwrites files
activates live trading
disables risk controls
```

Critical tools must include:

```python
TOOL_RISK_LEVEL = "critical"
REQUIRES_APPROVAL = True
```

Critical tools must also perform explicit permission checks before execution.

Example:

```python
if not approved:
    return {
        "status": "error",
        "message": "Approval is required before this tool can run.",
        "data": None,
        "error": {
            "code": "PERMISSION_DENIED",
            "details": "This tool requires approval because it can affect live trading.",
        },
        "metadata": {...},
    }
```

---

## 13. Input Validation Rule

Every AI Tool must validate all external inputs before execution.

Validation should check:

- missing required values
- wrong type
- invalid enum/string choices
- invalid numeric ranges
- unsafe paths
- unsupported symbols
- unsupported timeframes
- invalid date ranges
- invalid risk values
- invalid order sizes

Invalid input must return:

```python
{
    "status": "error",
    "message": "Invalid input.",
    "data": None,
    "error": {
        "code": "INVALID_INPUT",
        "details": "Clear explanation of the invalid input."
    },
    "metadata": {...}
}
```

---

## 14. Logging Rule

Every Python file must import logger:

```python
from tools.utils import logger
```

Every AI Tool must leave a logging footprint.

At minimum, each AI Tool must log:

```text
tool called
validation failure, if any
successful completion
execution failure, if any
```

Example:

```python
logger.info("%s called | request_id=%s", TOOL_NAME, request_id)
logger.warning("%s validation failed | request_id=%s", TOOL_NAME, request_id)
logger.info("%s completed successfully | request_id=%s", TOOL_NAME, request_id)
logger.exception("%s failed | request_id=%s", TOOL_NAME, request_id)
```

Do not log secrets, account passwords, API keys, broker tokens, or sensitive credentials.

---

## 15. Request ID and Traceability Rule

Every AI Tool should accept:

```python
request_id: Optional[str] = None
```

This allows one user request or agent workflow to be traced across multiple tools.

Example workflow:

```text
planner -> data tool -> strategy tool -> backtest tool -> risk tool -> report tool
```

The same `request_id` should appear in logs and metadata.

---

## 16. No Silent Failure Rule

AI Tools must not:

- return `None`
- swallow exceptions silently
- return raw exceptions
- print errors instead of returning structured errors
- hide validation failures
- return unstructured mixed formats

Every failure must return a standard error response.

---

## 17. Import Boundary Rule

Agents should import tools from domain packages only.

Correct:

```python
from tools.data import get_market_data
```

Avoid:

```python
from tools.data.market_data import get_market_data
```

Inside implementation files, keep imports clean.

Preferred dependency direction:

```text
tool implementation -> helper functions / clients / repositories / utilities
```

Avoid circular imports between tool domains.

Avoid importing from another domain’s deep implementation file unless absolutely necessary.

If one tool needs another domain’s official tool, import from the domain package:

```python
from tools.data import get_market_data
```

---

## 18. Unit Testing Rule

Every function listed in a tool domain `__all__` must have unit tests.

Tests must exist under:

```text
tests/unit/tools/{domain}/test_{source_file}.py
```

Example:

```text
tests/unit/tools/data/test_market_data.py
tests/unit/tools/data/test_validators.py
```

Each exported AI Tool must test:

- successful call
- invalid input
- empty result where applicable
- service/tool failure where applicable
- standard return schema compliance
- metadata correctness
- error code correctness
- logging footprint
- permission denial for high-risk tools

---

## 19. Real-World Usage Example Rule

Every exported AI Tool must have a usage example.

Usage files must exist under:

```text
tests/usage/tools/{domain}/{source_file}.py
```

Example:

```text
tests/usage/tools/data/market_data.py
tests/usage/tools/data/validators.py
```

Usage examples must demonstrate real execution of every exported function using actual calls.

Avoid mocks in usage files.

Usage examples should show how an agent or workflow would consume the result.

Example:

```python
from tools.data import get_market_data


result = get_market_data(
    symbol="EURUSD",
    timeframe="H1",
    bars=500,
    request_id="usage-example-001",
)

if result["status"] == "success":
    candles = result["data"]
    print(f"Fetched {len(candles)} candles.")
else:
    print(result["error"])
```

---

## 20. Tool Registry Audit Rule

When auditing a tool domain, inspect the domain `__init__.py` first.

The `__all__` list is the source of truth.

For every function in `__all__`, verify:

- function exists
- function imports correctly
- function has type hints
- function has an agent-facing docstring
- function returns the standard schema
- function validates inputs
- function handles errors
- function logs important events
- function includes metadata
- function has unit tests
- function has usage examples

If a function is implemented but not listed in `__all__`, mark it as:

```text
Internal or unexported function.
```

If a function is listed in `__all__` but cannot be imported, mark it as:

```text
Broken tool export.
```

---

## 21. Tool File Audit Checklist

For every file inside `tools/`, check:

```text
[ ] File starts with file-level docstring
[ ] File imports logger
[ ] File contains no unused heavy logic in __init__.py
[ ] Every class has a docstring
[ ] Every function has a docstring
[ ] Every exported function follows AI Tool return schema
[ ] Every exported function has type hints
[ ] Every exported function validates input
[ ] Every exported function handles exceptions gracefully
[ ] Every exported function logs call/completion/failure
[ ] Every exported function includes tool metadata
[ ] Every exported function includes execution_ms
[ ] Every exported function supports request_id
[ ] Every exported function avoids silent failures
[ ] Every exported function has unit tests
[ ] Every exported function has usage examples
[ ] Internal helpers are not exposed accidentally
[ ] __all__ only includes approved AI Tools
```

---

## 22. Final Output Required When Auditing

When auditing or refactoring tools, produce a markdown report named:

```text
TOOL_FUNCTION_STANDARDIZATION_AUDIT.md
```

The report must include:

```markdown
# Tool Function Standardization Audit

## 1. Executive Summary

## 2. Tool Domains Audited

## 3. Domain Registry Review

## 4. Exported Tool List

## 5. File-by-File Audit

## 6. Tool-by-Tool Compliance Table

| Domain | File | Tool | Exported in __all__ | Standard Return | Logging | Tests | Usage Example | Status |
|---|---|---|---|---|---|---|---|---|

## 7. Broken Exports

## 8. Missing Exports

## 9. Non-Compliant Tools

## 10. Missing Tests

## 11. Missing Usage Examples

## 12. Risk and Permission Issues

## 13. Refactoring Summary

## 14. Recommended Next Actions
```

---

## 23. Final Instruction

When creating or refactoring HaruQuantAI tools:

1. Put the implementation in a normal module file.
2. Expose approved AI Tools through the domain `__init__.py`.
3. Treat anything in `__all__` as an official AI Tool.
4. Make every official AI Tool follow this standard.
5. Do not put implementation logic in `__init__.py`.
6. Do not create duplicate wrapper functions unless the original function is too low-level, unsafe, or not agent-friendly.
7. Keep agents importing from the domain package.

Correct final pattern:

```python
from tools.data import get_market_data
```

Not:

```python
from tools.data.market_data import get_market_data
```
