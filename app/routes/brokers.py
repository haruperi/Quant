# ruff: noqa: ANN401, PLC0415
"""Active broker router/resolver.

This module resolves, routes and returns the active broker module based on settings.
"""

from typing import Any

from app.core.config import settings


def get_broker_module() -> Any:
    """Resolve and return the active broker module based on settings.

    Returns:
        Any: The active broker module (mt5, ctrader, or simulator).
    """
    active = getattr(settings, "active_broker", "mt5").lower()
    if active == "ctrader":
        from app.services.brokers import ctrader

        return ctrader

    if active == "simulator":
        from app.services import simulator

        return simulator

    from app.services.brokers import mt5

    return mt5
