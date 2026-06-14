# ruff: noqa: ANN401, PLC0415
"""Active broker resolver for generic trade classes.

This module resolves and returns the active broker module based on settings.
"""

from typing import Any

from app.core.config import settings


def get_broker_module() -> Any:
    """Resolve and return the active broker module based on settings.

    Returns:
        Any: The active broker module (mt5 or ctrader).
    """
    active = getattr(settings, "active_broker", "mt5").lower()
    if active == "ctrader":
        from app.services.brokers import ctrader

        return ctrader

    from app.services.brokers import mt5

    return mt5
