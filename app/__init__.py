"""HaruQuant application package.

Exposes a curated, side-effect-free public surface. All exports are
resolved lazily on first access so that ``import app`` does not trigger
pandas, numpy, or any other heavy transitive dependency.

Public names
------------
Analytics (lazy):
    MetricDefinitionCatalog, return_on_initial_capital, total_return
Optimisation (lazy):
    Infinity, OPT_JSON_SERIALIZATION_FAILED, parameter_space_hash,
    parametric_simulation, strategy_id
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

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

_LAZY_ANALYTICS_EXPORTS: frozenset[str] = frozenset(
    {
        "MetricDefinitionCatalog",
        "return_on_initial_capital",
        "total_return",
    }
)

_LAZY_OPTIMIZATION_EXPORTS: frozenset[str] = frozenset(
    {
        "Infinity",
        "OPT_JSON_SERIALIZATION_FAILED",
        "parameter_space_hash",
        "parametric_simulation",
        "strategy_id",
    }
)


def __getattr__(name: str) -> Any:  # noqa: ANN401
    """Lazily resolve analytics and optimisation exports on first access.

    Resolved values are cached in the module's global namespace so that
    subsequent attribute accesses bypass this function entirely.

    Args:
        name: The attribute name being accessed on this package.

    Returns:
        The requested symbol resolved from its source module.

    Raises:
        AttributeError: If ``name`` is not an approved public export.
    """
    if name in _LAZY_ANALYTICS_EXPORTS:
        module = import_module("app.services.analytics")
        value: object = getattr(module, name)
        globals()[name] = value
        return value
    if name in _LAZY_OPTIMIZATION_EXPORTS:
        module = import_module("app.services.optimization")
        value = getattr(module, name)
        globals()[name] = value
        return value
    message = f"module 'app' has no attribute {name!r}"
    raise AttributeError(message)
