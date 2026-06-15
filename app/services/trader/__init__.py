"""Generic Trade Classes module.

Provides unified, cross-platform wrappers matching the MQL5 Trade Classes
interface for account info, symbol info, terminal info, position/order details,
and trade execution.
"""

from app.services.trader.account_info import AccountInfo
from app.services.trader.concurrency import ConcurrencyQueue
from app.services.trader.deal_info import DealInfo
from app.services.trader.history_order_info import HistoryOrderInfo
from app.services.trader.idempotency import IdempotencyService
from app.services.trader.order_info import OrderInfo
from app.services.trader.position_info import PositionInfo
from app.services.trader.rate_limiter import RateLimiter, get_rate_limiter
from app.services.trader.readiness import ReadinessService
from app.services.trader.reconciliation import ReconciliationService
from app.services.trader.reporting import ReportingService
from app.services.trader.result import (
    BrokerResponseNormalizer,
    NormalizedTradeResult,
    ResultBuilder,
)
from app.services.trader.store import InMemoryTradeStore, TradeStore, get_default_store
from app.services.trader.symbol_info import SymbolInfo
from app.services.trader.terminal_info import TerminalInfo
from app.services.trader.trade import Trade
from app.services.trader.validation import ValidationService

__all__ = [
    "AccountInfo",
    "BrokerResponseNormalizer",
    "ConcurrencyQueue",
    "DealInfo",
    "HistoryOrderInfo",
    "IdempotencyService",
    "InMemoryTradeStore",
    "NormalizedTradeResult",
    "OrderInfo",
    "PositionInfo",
    "RateLimiter",
    "ReadinessService",
    "ReconciliationService",
    "ReportingService",
    "ResultBuilder",
    "SymbolInfo",
    "TerminalInfo",
    "Trade",
    "TradeStore",
    "ValidationService",
    "get_default_store",
    "get_rate_limiter",
]
