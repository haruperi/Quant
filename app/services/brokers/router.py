"""Service-level broker resolver.

Centralizes active broker module selection so API routes do not own broker
adapter policy. The legacy ``app.routes.brokers`` module delegates here for
backward compatibility.
"""

from types import ModuleType


def get_active_broker_name() -> str:
    """Return the configured broker name with compatibility fallbacks.

    Returns:
        str: Lowercase broker name.
    """
    settings_obj: object | None = None
    try:
        from app.utils import settings as settings_module

        settings_obj = getattr(settings_module, "settings", None)
    except ImportError:
        settings_obj = None

    if settings_obj is None:
        try:
            from app.core.config import settings as core_settings

            settings_obj = core_settings
        except ImportError:
            settings_obj = None

    return str(getattr(settings_obj, "active_broker", "mt5")).lower()


def get_broker_module() -> ModuleType:
    """Resolve and return the active broker module from runtime settings.

    Returns:
        ModuleType: The configured broker service module.
    """
    active = get_active_broker_name()
    if active == "ctrader":
        from app.services.brokers import ctrader

        return ctrader

    if active == "simulator":
        from app.services import simulator

        return simulator

    from app.services.brokers import mt5

    return mt5
