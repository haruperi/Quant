# Tool Function Standard

## 1. Core Principle

Any function exposed in a domain’s `__init__.py` (`__all__`) is an **Official AI Tool** and **must** follow this standard. Internal helpers (not in `__all__`, preferably prefixed with `_`) do not need the full standard but must remain documented, clean and typed.

## 2. Directory & Import Structure

- **Structure**: `tools/<domain_name>/<file>.py`
- **Registry**: `tools/<domain_name>/__init__.py` is the **only** official registry.
- **Import Rule**: Agents must import from the domain, never deep.
  - ✅ `from tools.data import get_market_data`
  - ❌ `from tools.data.market_data import get_market_data`
- **`__init__.py` Rules**: Contains **only** imports and `__all__`. No business logic, calculations, or validation. Group imports by source file with comments.

## 3. Standard Function Template

All outward-facing tools must follow this exact structure to ensure AI compatibility and generic usability:

```python
from __future__ import annotations
import time
from typing import Any, Dict, Optional
from tools.utils import logger

# 1. Metadata & Side-Effect Declarations
TOOL_NAME = "get_market_data"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"  # low, medium, high, critical
READS = True
WRITES = False
UPDATES = False
DELETES = False
TRADES = False
REQUIRES_NETWORK = True
REQUIRES_APPROVAL = False

# 2. Function Definition
def get_market_data(symbol: str, timeframe: str = "H1", request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    [Agent-Facing Docstring]
    Fetches OHLCV market data. Use when an agent needs historical price data.

    Args:
        symbol (str): Trading symbol (e.g., "EURUSD").
        timeframe (str, optional): Candle timeframe. Defaults to "H1".
        request_id (Optional[str], optional): Workflow trace ID.

    Returns:
        Dict[str, Any]: Standard tool response (status, message, data, error, metadata).
    """
    started_at = time.perf_counter()
    logger.info(f"{TOOL_NAME} called | request_id={request_id} | symbol={symbol}")

    # 3. Input Validation
    if not symbol:
        return _build_error("INVALID_INPUT", "symbol cannot be empty.", started_at, request_id)

    try:
        # 4. Core Execution (Generic/AI logic here)
        result_data = {"candles": []} # Replace with actual logic

        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info(f"{TOOL_NAME} success | request_id={request_id} | execution_ms={execution_ms}")

        # 5. Structured Success Return
        return {
            "status": "success",
            "message": "Tool executed successfully.",
            "data": result_data,
            "error": None,
            "metadata": _get_metadata(started_at, request_id)
        }
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception(f"{TOOL_NAME} failed | request_id={request_id} | execution_ms={execution_ms}")
        return _build_error("TOOL_EXECUTION_FAILED", str(e), started_at, request_id)

# 6. Helper functions for standard returns (keep DRY)
def _get_metadata(started_at: float, request_id: Optional[str]) -> Dict[str, Any]:
    """ Gets and returns the metadata for a tool execution. """
    return {
        "tool_name": TOOL_NAME, "tool_version": TOOL_VERSION, "tool_category": TOOL_CATEGORY,
        "tool_risk_level": TOOL_RISK_LEVEL, "request_id": request_id,
        "execution_ms": round((time.perf_counter() - started_at) * 1000, 3),
        "reads": READS, "writes": WRITES, "updates": UPDATES, "deletes": DELETES,
        "trades": TRADES, "requires_network": REQUIRES_NETWORK
    }

def _build_error(code: str, details: str, started_at: float, request_id: Optional[str]) -> Dict[str, Any]:
    """ Builds and returns the error schema for a tool execution. """
    return {
        "status": "error", "message": "Tool execution failed.", "data": None,
        "error": {"code": code, "details": details},
        "metadata": _get_metadata(started_at, request_id)
    }
```

## 4. Standard Return Schema (Mandatory)

Tools must **never** return `None` or raw exceptions. Always return this exact dictionary structure:

```json
{
  "status": "success" | "error",
  "message": "Human/AI-readable summary string",
  "data": <Any valid payload or null>,
  "error": null | {"code": "ERROR_CODE", "details": "Specific explanation"},
  "metadata": {
    "tool_name": str, "tool_version": str, "tool_category": str, "tool_risk_level": str,
    "request_id": str | null, "execution_ms": float,
    "reads": bool, "writes": bool, "updates": bool, "deletes": bool, "trades": bool, "requires_network": bool
  }
}
```

**Allowed Error Codes**: `INVALID_INPUT`, `PERMISSION_DENIED`, `DATA_NOT_FOUND`, `EMPTY_RESULT`, `SERVICE_UNAVAILABLE`, `BROKER_UNAVAILABLE`, `DATABASE_ERROR`, `NETWORK_ERROR`, `TIMEOUT`, `VALIDATION_FAILED`, `TOOL_EXECUTION_FAILED`, `UNKNOWN_ERROR`.

## 5. Mandatory Rules Checklist

- [ ] **Docstrings**: File-level (purpose, exports, helpers) + Function-level (agent-facing: what, when, args, returns, errors).
- [ ] **Validation**: Validate all external inputs first. Return `INVALID_INPUT` schema if failed.
- [ ] **Logging**: Import `logger`. Log: `called`, `validation failed` (if any), `success`, `exception`. Include `request_id`. Never log secrets.
- [ ] **Traceability**: Every tool must accept `request_id: Optional[str] = None`.
- [ ] **No Silent Failures**: Catch exceptions, log them, and return the standard error schema.
- [ ] **Risk & Permissions**: If `TOOL_RISK_LEVEL` is `critical` (trades, deletes, modifies live state), `REQUIRES_APPROVAL` must be `True`, and explicit permission checks must precede execution.
- [ ] **Testing**: Exported tools require unit tests (`tests/unit/tools/<domain>/test_<file>.py`) covering success, invalid input, and error paths.
- [ ] **Usage Examples**: Real-world execution examples required in `tests/usage/tools/<domain>/<file>.py` (no mocks).

---
