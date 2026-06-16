"""Indicators service package.

Provides a registry and convenience wrappers for trend, volatility, and momentum
indicator calculations, conforming to standard quantitative replay requirements.
"""

from app.services.indicators.calculations import execute_indicator_composition
from app.services.indicators.errors import IndicatorError
from app.services.indicators.protocols import (
    IndicatorConfig,
    IndicatorContext,
    IndicatorManifest,
    IndicatorProtocol,
    IndicatorResult,
    IndicatorState,
    WarmupRequirement,
)
from app.services.indicators.registry import (
    adr,
    adx,
    atr,
    ema,
    get_indicator,
    list_indicators,
    register_indicator,
    rolling_volatility,
    rsi,
    sma,
    unregister_indicator,
    validate_indicator,
    williams_r,
)

__all__ = [
    "IndicatorConfig",
    "IndicatorContext",
    "IndicatorError",
    "IndicatorManifest",
    "IndicatorProtocol",
    "IndicatorResult",
    "IndicatorState",
    "WarmupRequirement",
    "adr",
    "adx",
    "atr",
    "ema",
    "execute_indicator_composition",
    "get_indicator",
    "list_indicators",
    "register_indicator",
    "rolling_volatility",
    "rsi",
    "sma",
    "unregister_indicator",
    "validate_indicator",
    "williams_r",
]
