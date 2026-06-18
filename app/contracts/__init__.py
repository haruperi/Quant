"""Public registry for canonical contracts.

This module re-exports approved cross-domain model contracts and provider protocols.
It is import-safe and side-effect free: importing it does not open databases,
configure logging, initiate network requests, or import optional heavy broker libraries.
"""

from __future__ import annotations

from app.contracts.analytics import AnalyticsReport, PerformanceScorecard
from app.contracts.audit import AuditEvent
from app.contracts.base import Contract
from app.contracts.indicators import IndicatorResult
from app.contracts.live import KillSwitchState, LiveSessionState
from app.contracts.market import (
    ERR_MALFORMED_PAYLOAD,
    ERR_PROVIDER_ERROR,
    ERR_STALE_DATA,
    ERR_SYMBOL_UNAVAILABLE,
    ERR_UNSUPPORTED_TIMEFRAME,
    Bar,
    DataSlice,
    Spread,
    Symbol,
    Tick,
    Timeframe,
)
from app.contracts.optimization import OptimizationCandidate
from app.contracts.portfolio import AccountSnapshot, PortfolioSnapshot, Position
from app.contracts.providers import (
    AccountProvider,
    BrokerErrorMapper,
    ExecutionJournal,
    ExecutionProvider,
    MarketDataProvider,
    OrderProvider,
    PositionProvider,
    SymbolInfoProvider,
    TradeStore,
)
from app.contracts.risk import (
    PositionSizingResult,
    RiskAuditEvent,
    RiskDecision,
    RiskRejection,
)
from app.contracts.simulation import BacktestConfig, BacktestResult
from app.contracts.strategies import StrategyInput, StrategySignal
from app.contracts.trading import (
    BrokerCapabilities,
    ExecutionReport,
    Fill,
    OrderIntent,
    TradeRequest,
    TradeResult,
)

__all__ = [
    "ERR_MALFORMED_PAYLOAD",
    "ERR_PROVIDER_ERROR",
    "ERR_STALE_DATA",
    "ERR_SYMBOL_UNAVAILABLE",
    "ERR_UNSUPPORTED_TIMEFRAME",
    "AccountProvider",
    "AccountSnapshot",
    "AnalyticsReport",
    "AuditEvent",
    "BacktestConfig",
    "BacktestResult",
    "Bar",
    "BrokerCapabilities",
    "BrokerErrorMapper",
    "Contract",
    "DataSlice",
    "ExecutionJournal",
    "ExecutionProvider",
    "ExecutionReport",
    "Fill",
    "IndicatorResult",
    "KillSwitchState",
    "LiveSessionState",
    "MarketDataProvider",
    "OptimizationCandidate",
    "OrderIntent",
    "OrderProvider",
    "PerformanceScorecard",
    "PortfolioSnapshot",
    "Position",
    "PositionProvider",
    "PositionSizingResult",
    "RiskAuditEvent",
    "RiskDecision",
    "RiskRejection",
    "Spread",
    "StrategyInput",
    "StrategySignal",
    "Symbol",
    "SymbolInfoProvider",
    "Tick",
    "Timeframe",
    "TradeRequest",
    "TradeResult",
    "TradeStore",
]
