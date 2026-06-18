# ruff: noqa: ANN401
"""Compatibility wrapper for the service-level broker router.

Routes should not own broker adapter selection policy. New code should import
``get_broker_module`` from ``app.services.brokers.router`` directly.
"""

from typing import Any

from app.services.brokers.router import get_broker_module as _get_broker_module


def get_broker_module() -> Any:
    """Resolve and return the active broker module.

    Returns:
        Any: The active broker module selected by the service router.
    """
    return _get_broker_module()
