"""MQL5-compatible DealInfo class wrapping history deal properties.

Provides easy access to the history deal properties.
"""

from typing import Any

from app.services.trader.resolver import get_broker_module


class DealInfo:
    """Provides access to properties of a historical deal."""

    def __init__(self, ticket: int | None = None) -> None:
        """Initialize the DealInfo helper.

        Args:
            ticket: Optional deal ticket to select automatically.
        """
        self._data: Any = None
        if ticket is not None:
            self.select(ticket)

    def select(self, ticket: int) -> bool:
        """Select a history deal by ticket.

        Args:
            ticket: History deal ticket.

        Returns:
            bool: True if selected successfully, False otherwise.
        """
        broker = get_broker_module()
        deals = broker.get_history_deal_info(ticket=ticket)
        if deals:
            self._data = deals[0]
            return True
        self._data = None
        return False

    def ticket(self) -> int:
        """Get the ticket of the deal.

        Returns:
            int: Ticket number.
        """
        return int(getattr(self._data, "ticket", 0))

    def order(self) -> int:
        """Get the ticket of the order that initiated the deal.

        Returns:
            int: Order ticket.
        """
        return int(getattr(self._data, "order", 0))

    def time(self) -> int:
        """Get the deal execution time.

        Returns:
            int: Time in seconds.
        """
        return int(getattr(self._data, "time", 0))

    def time_msc(self) -> int:
        """Get the deal execution time in milliseconds.

        Returns:
            int: Time.
        """
        return int(getattr(self._data, "time_msc", 0))

    def type(self) -> int:
        """Get the deal type (0=Buy, 1=Sell).

        Returns:
            int: Deal type.
        """
        return int(getattr(self._data, "type", 0))

    def type_description(self) -> str:
        """Get description of the deal type.

        Returns:
            str: Description.
        """
        t = self.type()
        mapping = {
            0: "Buy",
            1: "Sell",
        }
        return mapping.get(t, f"Unknown ({t})")

    def entry(self) -> int:
        """Get the deal entry type (0=In, 1=Out, 2=InOut, 3=OutBy).

        Returns:
            int: Entry type.
        """
        return int(getattr(self._data, "entry", 0))

    def entry_description(self) -> str:
        """Get description of the deal entry type.

        Returns:
            str: Description.
        """
        e = self.entry()
        mapping = {
            0: "Entry In",
            1: "Entry Out",
            2: "Entry In/Out",
            3: "Entry Out By",
        }
        return mapping.get(e, f"Unknown ({e})")

    def magic(self) -> int:
        """Get the magic number of the deal.

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

    def volume(self) -> float:
        """Get the volume of the deal.

        Returns:
            float: Volume.
        """
        return float(getattr(self._data, "volume", 0.0))

    def price(self) -> float:
        """Get the price of the deal.

        Returns:
            float: Execution price.
        """
        return float(getattr(self._data, "price", 0.0))

    def commission(self) -> float:
        """Get the commission of the deal.

        Returns:
            float: Commission.
        """
        return float(getattr(self._data, "commission", 0.0))

    def swap(self) -> float:
        """Get the swap of the deal.

        Returns:
            float: Swap.
        """
        return float(getattr(self._data, "swap", 0.0))

    def profit(self) -> float:
        """Get the gross profit of the deal.

        Returns:
            float: Profit.
        """
        return float(getattr(self._data, "profit", 0.0))

    def symbol(self) -> str:
        """Get the symbol of the deal.

        Returns:
            str: Symbol name.
        """
        return str(getattr(self._data, "symbol", ""))

    def comment(self) -> str:
        """Get the comment of the deal.

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
            1: self.order(),
            2: self.time(),
            3: self.type(),
            4: self.entry(),
            5: self.magic(),
            6: self.position_id(),
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
            0: self.volume(),
            1: self.price(),
            2: self.commission(),
            3: self.swap(),
            4: self.profit(),
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
