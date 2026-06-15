"""MQL5-compatible HistoryOrderInfo class wrapping history order properties.

Provides easy access to the history order properties.
"""

from typing import Any

from app.routes.brokers import get_broker_module


class HistoryOrderInfo:
    """Provides access to properties of a historical order."""

    def __init__(self, ticket: int | None = None) -> None:
        """Initialize the HistoryOrderInfo helper.

        Args:
            ticket: Optional order ticket to select automatically.
        """
        self._data: Any = None
        if ticket is not None:
            self.select(ticket)

    def select(self, ticket: int) -> bool:
        """Select a history order by ticket.

        Args:
            ticket: History order ticket.

        Returns:
            bool: True if selected successfully, False otherwise.
        """
        broker = get_broker_module()
        orders = broker.get_history_order_info(ticket=ticket)
        if orders:
            self._data = orders[0]
            return True
        self._data = None
        return False

    def ticket(self) -> int:
        """Get the ticket of the history order.

        Returns:
            int: Ticket number.
        """
        return int(getattr(self._data, "ticket", 0))

    def time_setup(self) -> int:
        """Get the setup time of the history order.

        Returns:
            int: Setup time in seconds.
        """
        return int(getattr(self._data, "time_setup", 0))

    def time_setup_msc(self) -> int:
        """Get the setup time in milliseconds.

        Returns:
            int: Setup time.
        """
        return int(getattr(self._data, "time_setup_msc", 0))

    def time_expiration(self) -> int:
        """Get the expiration time of the history order.

        Returns:
            int: Expiration time in seconds.
        """
        return int(getattr(self._data, "time_expiration", 0))

    def time_done(self) -> int:
        """Get the execution/cancellation time of the history order.

        Returns:
            int: Done time in seconds.
        """
        return int(getattr(self._data, "time_done", 0))

    def time_done_msc(self) -> int:
        """Get the done time in milliseconds.

        Returns:
            int: Done time.
        """
        return int(getattr(self._data, "time_done_msc", 0))

    def type(self) -> int:
        """Get the type of the history order.

        Returns:
            int: Order type.
        """
        return int(getattr(self._data, "type", 0))

    def type_description(self) -> str:
        """Get the description of the order type.

        Returns:
            str: Description (e.g., "Buy Limit").
        """
        t = self.type()
        mapping = {
            0: "Buy",
            1: "Sell",
            2: "Buy Limit",
            3: "Sell Limit",
            4: "Buy Stop",
            5: "Sell Stop",
            6: "Buy Stop Limit",
            7: "Sell Stop Limit",
        }
        return mapping.get(t, f"Unknown ({t})")

    def type_time(self) -> int:
        """Get the expiration type of the history order.

        Returns:
            int: Expiration type.
        """
        return int(getattr(self._data, "type_time", 0))

    def type_time_description(self) -> str:
        """Get description of the expiration type.

        Returns:
            str: Description.
        """
        t = self.type_time()
        mapping = {
            0: "GTC",
            1: "Day",
            2: "Specified",
            3: "Specified Day",
        }
        return mapping.get(t, f"Unknown ({t})")

    def type_filling(self) -> int:
        """Get execution type of the history order.

        Returns:
            int: Filling type.
        """
        return int(getattr(self._data, "type_filling", 0))

    def type_filling_description(self) -> str:
        """Get description of execution type.

        Returns:
            str: Description.
        """
        t = self.type_filling()
        mapping = {
            0: "FOK",
            1: "IOC",
            2: "Return",
        }
        return mapping.get(t, f"Unknown ({t})")

    def state(self) -> int:
        """Get status of the history order.

        Returns:
            int: Order state.
        """
        return int(getattr(self._data, "state", 0))

    def state_description(self) -> str:
        """Get description of the order status.

        Returns:
            str: Description.
        """
        s = self.state()
        mapping = {
            0: "Started",
            1: "Placed",
            2: "Canceled",
            3: "Partial",
            4: "Filled",
            5: "Rejected",
            6: "Expired",
            7: "Request Sent",
            8: "Request Cancelled",
        }
        return mapping.get(s, f"Unknown ({s})")

    def magic(self) -> int:
        """Get the magic number of the history order.

        Returns:
            int: Magic number.
        """
        return int(getattr(self._data, "magic", 0))

    def position_id(self) -> int:
        """Get the associated position ID.

        Returns:
            int: Position ID.
        """
        return int(getattr(self._data, "position_id", 0))

    def position_by_id(self) -> int:
        """Get the associated position ID by which order was placed.

        Returns:
            int: Position ID.
        """
        return int(getattr(self._data, "position_by_id", 0))

    def volume_initial(self) -> float:
        """Get the initial volume of the history order.

        Returns:
            float: Volume.
        """
        return float(getattr(self._data, "volume_initial", 0.0))

    def volume_current(self) -> float:
        """Get the current volume of the history order.

        Returns:
            float: Volume.
        """
        return float(getattr(self._data, "volume_current", 0.0))

    def price_open(self) -> float:
        """Get the price level of the history order.

        Returns:
            float: Open price.
        """
        return float(getattr(self._data, "price_open", 0.0))

    def stop_loss(self) -> float:
        """Get the Stop Loss level.

        Returns:
            float: SL price.
        """
        return float(getattr(self._data, "sl", 0.0))

    def take_profit(self) -> float:
        """Get the Take Profit level.

        Returns:
            float: TP price.
        """
        return float(getattr(self._data, "tp", 0.0))

    def price_current(self) -> float:
        """Get the current price of the symbol.

        Returns:
            float: Current price.
        """
        return float(getattr(self._data, "price_current", 0.0))

    def price_stop_limit(self) -> float:
        """Get the stop limit price.

        Returns:
            float: Price stop limit.
        """
        return float(getattr(self._data, "price_stoplimit", 0.0))

    def symbol(self) -> str:
        """Get the symbol of the history order.

        Returns:
            str: Symbol name.
        """
        return str(getattr(self._data, "symbol", ""))

    def comment(self) -> str:
        """Get the comment of the history order.

        Returns:
            str: Comment string.
        """
        return str(getattr(self._data, "comment", ""))

    def info_integer(self, prop_id: int) -> int:
        """Get generic integer property.

        Args:
            prop_id: Property ID identifier.

        Returns:
            int: Property value.
        """
        prop_map = {
            0: self.ticket(),
            1: self.time_setup(),
            2: self.type(),
            3: self.state(),
            4: self.magic(),
            5: self.position_id(),
            6: self.time_expiration(),
        }
        return prop_map.get(prop_id, 0)

    def info_double(self, prop_id: int) -> float:
        """Get generic double property.

        Args:
            prop_id: Property ID identifier.

        Returns:
            float: Property value.
        """
        prop_map = {
            0: self.volume_initial(),
            1: self.volume_current(),
            2: self.price_open(),
            3: self.stop_loss(),
            4: self.take_profit(),
            5: self.price_current(),
        }
        return prop_map.get(prop_id, 0.0)

    def info_string(self, prop_id: int) -> str:
        """Get generic string property.

        Args:
            prop_id: Property ID identifier.

        Returns:
            str: Property value.
        """
        prop_map = {
            0: self.symbol(),
            1: self.comment(),
        }
        return prop_map.get(prop_id, "")
