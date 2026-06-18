"""Brokers service package.

Broker adapters are loaded lazily so optional provider SDKs are only required
when their adapter is actually used.
"""

__all__ = [
    "BinanceClient",
    "CTraderClient",
    "DukascopyClient",
    "MT5Client",
    "YahooClient",
    "get_binance_client",
    "get_ctrader_client",
    "get_dukascopy_client",
    "get_mt5_client",
    "get_yahoo_client",
]

_EXPORT_MODULES = {
    "BinanceClient": "app.services.brokers.binance",
    "get_binance_client": "app.services.brokers.binance",
    "CTraderClient": "app.services.brokers.ctrader",
    "get_ctrader_client": "app.services.brokers.ctrader",
    "DukascopyClient": "app.services.brokers.dukascopy",
    "get_dukascopy_client": "app.services.brokers.dukascopy",
    "MT5Client": "app.services.brokers.mt5",
    "get_mt5_client": "app.services.brokers.mt5",
    "YahooClient": "app.services.brokers.yahoo",
    "get_yahoo_client": "app.services.brokers.yahoo",
}


def __getattr__(name: str) -> object:
    """Lazily import broker adapter exports.

    Args:
        name: Exported broker symbol.

    Returns:
        Any: The requested broker class or factory.

    Raises:
        AttributeError: If ``name`` is not an exported broker symbol.
    """
    if name not in _EXPORT_MODULES:
        raise AttributeError(name)

    from importlib import import_module

    module = import_module(_EXPORT_MODULES[name])
    value = getattr(module, name)
    globals()[name] = value
    return value
