"""Generic Trade Classes module.

Provides unified, cross-platform wrappers matching the MQL5 Trade Classes
interface for account info, symbol info, terminal info, position/order details,
and trade execution.
"""

from app.services.trader.account_info import AccountInfo
from app.services.trader.deal_info import DealInfo
from app.services.trader.history_order_info import HistoryOrderInfo
from app.services.trader.order_info import OrderInfo
from app.services.trader.position_info import PositionInfo
from app.services.trader.symbol_info import SymbolInfo
from app.services.trader.terminal_info import TerminalInfo
from app.services.trader.trade import Trade

__all__ = [
    "AccountInfo",
    "DealInfo",
    "HistoryOrderInfo",
    "OrderInfo",
    "PositionInfo",
    "SymbolInfo",
    "TerminalInfo",
    "Trade",
]
