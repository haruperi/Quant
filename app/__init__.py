"""
This is the heart of the project.

Isolate application code inside an app directory.

Because it:
- Keeps root clean.
- Prevents import issues.
- Makes packaging easier.
- Works great with tools like pytest, Docker, and CI/CD.
Inside app/, everything has a purpose.
"""

from __future__ import annotations

from importlib import import_module

from app.services.analytics import (
    MetricDefinitionCatalog,
    return_on_initial_capital,
    total_return,
)

__all__ = [
    "OPT_JSON_SERIALIZATION_FAILED",
    "Infinity",
    "MetricDefinitionCatalog",
    "parameter_space_hash",
    "parametric_simulation",
    "return_on_initial_capital",
    "strategy_id",
    "total_return",
]

_LAZY_OPTIMIZATION_EXPORTS = frozenset(
    {
        "Infinity",
        "OPT_JSON_SERIALIZATION_FAILED",
        "parametric_simulation",
        "parameter_space_hash",
        "strategy_id",
    }
)


def __getattr__(name: str) -> object:
    """Lazily expose optional optimization exports.

    Args:
        name: Export name.

    Returns:
        object: Requested optimization export.

    Raises:
        AttributeError: If the name is not exported by this package.
    """
    if name in _LAZY_OPTIMIZATION_EXPORTS:
        optimization = import_module("app.services.optimization")
        value: object = getattr(optimization, name)
        return value
    message = f"module 'app' has no attribute {name!r}"
    raise AttributeError(message)
