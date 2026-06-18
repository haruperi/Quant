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

from app.services.analytics import (
    MetricDefinitionCatalog,
    return_on_initial_capital,
    total_return,
)

__all__ = [
    "MetricDefinitionCatalog",
    "return_on_initial_capital",
    "total_return",
]
