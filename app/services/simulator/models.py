# ruff: noqa: ANN401, FBT001
"""Wrapper specifications classes matching MT5 for the simulator service."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.simulator.engine import SimulatorClient


class SimulatorTerminalInfo:
    """Wrapper matching MT5 terminal info specifications."""

    def __init__(self, connected: bool) -> None:
        """Initialize terminal info.

        Args:
            connected: Connection status flag.
        """
        self.build = 5833
        self.connected = connected
        self.trade_allowed = True
        self.dlls_allowed = True
        self.ping_last = 500
        self.language = "English"
        self.company = "HaruQuant AI"
        self.name = "HaruQuant Broker Simulator"
        self.path = "In-Memory"
        self.data_path = "In-Memory"
        self.commondata_path = "In-Memory"


class SimulatorAccountInfo:
    """Wrapper matching MT5 account info specifications."""

    def __init__(self, client: "SimulatorClient") -> None:
        """Initialize account info.

        Args:
            client: The SimulatorClient instance.
        """
        self.login = client.login
        self.name = "Simulator User"
        self.server = client.server
        self.company = client.company
        self.currency = client.currency
        self.leverage = client.leverage

        self.trade_mode = 0  # Demo
        self.margin_mode = 0  # Hedging
        self.trade_allowed = True
        self.trade_expert = True
        self.limit_orders = 1000

        # Compute dynamic balance/equity/profit/margin values
        self.balance = client.balance
        self.credit = client.credit
        self.profit = client.calculate_total_profit()
        self.equity = self.balance + self.profit
        self.margin = client.calculate_total_margin()
        self.margin_free = self.equity - self.margin
        self.margin_level = (
            (self.equity / self.margin) * 100.0 if self.margin > 0 else 100000.0
        )
        self.margin_so_call = 80
        self.margin_so_so = 50


class SimulatorSymbolInfo:
    """Wrapper matching MT5 symbol info specifications."""

    def __init__(self, sym_data: Any) -> None:
        """Initialize symbol info from dict specs or MT5 SymbolInfo object.

        Args:
            sym_data: Preconfigured symbol specs dict or MT5 SymbolInfo.
        """
        if isinstance(sym_data, dict):
            self.name = sym_data["name"]
            self.description = sym_data["description"]
            self.path = sym_data["path"]
            self.digits = sym_data["digits"]
            self.point = sym_data["point"]
            self.trade_tick_size = sym_data["trade_tick_size"]
            self.trade_contract_size = sym_data["trade_contract_size"]
            self.volume_min = sym_data["volume_min"]
            self.volume_max = sym_data["volume_max"]
            self.volume_step = sym_data["volume_step"]
            self.swap_mode = sym_data["swap_mode"]
            self.swap_long = sym_data["swap_long"]
            self.swap_short = sym_data["swap_short"]
            self.bid = sym_data["bid"]
            self.ask = sym_data["ask"]
            self.last = sym_data["last"]
            self.spread = sym_data["spread"]
            self.trade_mode = sym_data["trade_mode"]
        else:
            self.name = sym_data.name
            self.description = sym_data.description
            self.path = sym_data.path
            self.digits = sym_data.digits
            self.point = sym_data.point
            self.trade_tick_size = sym_data.trade_tick_size
            self.trade_contract_size = sym_data.trade_contract_size
            self.volume_min = sym_data.volume_min
            self.volume_max = sym_data.volume_max
            self.volume_step = sym_data.volume_step
            self.swap_mode = sym_data.swap_mode
            self.swap_long = sym_data.swap_long
            self.swap_short = sym_data.swap_short
            self.bid = sym_data.bid
            self.ask = sym_data.ask
            self.last = sym_data.last
            self.spread = sym_data.spread
            self.trade_mode = sym_data.trade_mode


class SimulatorPositionInfo:
    """Wrapper matching MT5 position info specifications."""

    def __init__(self, pos_data: dict[str, Any]) -> None:
        """Initialize position info.

        Args:
            pos_data: Position data dict.
        """
        self.ticket = pos_data["ticket"]
        self.symbol = pos_data["symbol"]
        self.type = pos_data["type"]
        self.volume = pos_data["volume"]
        self.price_open = pos_data["price_open"]
        self.sl = pos_data["sl"]
        self.tp = pos_data["tp"]
        self.price_current = pos_data["price_current"]
        self.swap = pos_data["swap"]
        self.profit = pos_data["profit"]
        self.magic = pos_data["magic"]
        self.time = pos_data["time"]
        self.time_msc = pos_data["time_msc"]
        self.time_update = pos_data["time_update"]
        self.time_update_msc = pos_data["time_update_msc"]
        self.identifier = pos_data["identifier"]
        self.comment = pos_data["comment"]


class SimulatorOrderInfo:
    """Wrapper matching MT5 pending order info specifications."""

    def __init__(self, ord_data: dict[str, Any]) -> None:
        """Initialize pending order info.

        Args:
            ord_data: Pending order data dict.
        """
        self.ticket = ord_data["ticket"]
        self.symbol = ord_data["symbol"]
        self.type = ord_data["type"]
        self.volume_initial = ord_data["volume_initial"]
        self.volume_current = ord_data["volume_current"]
        self.price_open = ord_data["price_open"]
        self.sl = ord_data["sl"]
        self.tp = ord_data["tp"]
        self.price_current = ord_data["price_current"]
        self.price_stoplimit = ord_data["price_stoplimit"]
        self.magic = ord_data["magic"]
        self.time_setup = ord_data["time_setup"]
        self.time_setup_msc = ord_data["time_setup_msc"]
        self.time_expiration = ord_data["time_expiration"]
        self.time_done = ord_data["time_done"]
        self.time_done_msc = ord_data["time_done_msc"]
        self.state = ord_data["state"]
        self.position_id = ord_data["position_id"]
        self.position_by_id = ord_data["position_by_id"]
        self.comment = ord_data["comment"]


class SimulatorDealInfo:
    """Wrapper matching MT5 deal info specifications."""

    def __init__(self, deal_data: dict[str, Any]) -> None:
        """Initialize deal info.

        Args:
            deal_data: Deal data dict.
        """
        self.ticket = deal_data["ticket"]
        self.order = deal_data["order"]
        self.position_id = deal_data["position_id"]
        self.symbol = deal_data["symbol"]
        self.volume = deal_data["volume"]
        self.price = deal_data["price"]
        self.type = deal_data["type"]
        self.entry = deal_data["entry"]
        self.time = deal_data["time"]
        self.time_msc = deal_data["time_msc"]
        self.commission = deal_data["commission"]
        self.profit = deal_data["profit"]
        self.swap = deal_data["swap"]
        self.magic = deal_data["magic"]
        self.comment = deal_data["comment"]


class SimulatorTradeResult:
    """Wrapper matching MT5 trade execution result."""

    def __init__(
        self, order_id: int, deal_id: int, comment: str = "Request executed"
    ) -> None:
        """Initialize trade result.

        Args:
            order_id: The ticket ID of the execution order.
            deal_id: The ticket ID of the associated deal.
            comment: Descriptive execution comment.
        """
        self.order = order_id
        self.deal = deal_id
        self.retcode = 10009  # TRADE_RETCODE_DONE
        self.comment = comment
        self.price = 0.0
        self.volume = 0.0
        self.bid = 0.0
        self.ask = 0.0
