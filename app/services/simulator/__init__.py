"""In-memory broker simulator service package.

This service package offers a fully mockable in-memory trading broker environment.
"""

from app.services.simulator.engine import (
    SimulatorClient,
    get_account_info,
    get_ctrader_client,
    get_history_deal_info,
    get_history_order_info,
    get_mt5_client,
    get_order_info,
    get_position_info,
    get_simulator_client,
    get_symbol_info,
    get_terminal_info,
    trade,
)
from app.services.simulator.models import (
    SimulatorAccountInfo,
    SimulatorDealInfo,
    SimulatorOrderInfo,
    SimulatorPositionInfo,
    SimulatorSymbolInfo,
    SimulatorTerminalInfo,
    SimulatorTradeResult,
)

__all__ = [
    "SimulatorAccountInfo",
    "SimulatorClient",
    "SimulatorDealInfo",
    "SimulatorOrderInfo",
    "SimulatorPositionInfo",
    "SimulatorSymbolInfo",
    "SimulatorTerminalInfo",
    "SimulatorTradeResult",
    "get_account_info",
    "get_ctrader_client",
    "get_history_deal_info",
    "get_history_order_info",
    "get_mt5_client",
    "get_order_info",
    "get_position_info",
    "get_simulator_client",
    "get_symbol_info",
    "get_terminal_info",
    "trade",
]
