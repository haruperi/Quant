# ruff: noqa: E501, ANN401, PLR2004
"""Vetting layer for code-based strategy execution.

Ensures arbitrary code-based strategy string execution remains disabled until
specifically approved by operations, throwing a SIM_ARBITRARY_CODE_REJECTED error.
"""

from __future__ import annotations

from typing import Any

from app.utils.errors import SimArbitraryCodeRejectedError
from app.utils.logger import logger


def vet_and_sandbox_code(code_str: str, request_id: str | None = None) -> Any:
    """Vet and reject arbitrary Python code string inputs.

    Always disabled by default, throwing SimArbitraryCodeRejectedError.

    Args:
        code_str: Unsafe Python source code candidate string.
        request_id: Request identification tracing token.

    Raises:
        SimArbitraryCodeRejectedError: Always raised to prevent code injection.
    """
    # Safe snippet truncation for safe logging without full unsafe payload logs
    snippet = code_str[:120] + "..." if len(code_str) > 120 else code_str

    logger.warning(
        "Arbitrary strategy code input was rejected",
        extra={
            "event_name": "arbitrary_code_injection_rejected",
            "request_id": request_id,
            "snippet": snippet,
        },
    )

    # REQ-STRAT-084: Rejected raw strategy-code input shall return SIM_ARBITRARY_CODE_REJECTED
    raise SimArbitraryCodeRejectedError(
        "Code-based strategy execution is disabled. Only registered strategies are allowed.",
        code="SIM_ARBITRARY_CODE_REJECTED",
    )
