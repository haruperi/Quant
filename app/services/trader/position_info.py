"""MQL5-compatible PositionInfo class wrapping open position properties.

Provides easy access to the open position properties.
"""

from typing import Any

from app.services.trader.resolver import get_broker_module


class PositionInfo:
    """Provides access to properties of an open position."""

    def __init__(self, ticket: int | None = None) -> None:
        """Initialize the PositionInfo helper.

        Args:
            ticket: Optional position ticket to select automatically.
        """
        self._data: Any = None
        if ticket is not None:
            self.select_by_ticket(ticket)

    def select(self, symbol: str) -> bool:
        """Select an open position by symbol.

        Args:
            symbol: Symbol name.

        Returns:
            bool: True if selected successfully, False otherwise.
        """
        broker = get_broker_module()
        positions = broker.get_position_info(symbol=symbol)
        if positions:
            self._data = positions[0]
            return True
        self._data = None
        return False

    def select_by_ticket(self, ticket: int) -> bool:
        """Select an open position by ticket.

        Args:
            ticket: Position ticket.

        Returns:
            bool: True if selected successfully, False otherwise.
        """
        broker = get_broker_module()
        positions = broker.get_position_info(ticket=ticket)
        if positions:
            self._data = positions[0]
            return True
        self._data = None
        return False

    def ticket(self) -> int:
        """Get the ticket of the open position.

        Returns:
            int: Ticket number.
        """
        return int(getattr(self._data, "ticket", 0))

    def time(self) -> int:
        """Get the open time of the position.

        Returns:
            int: Time in seconds.
        """
        return int(getattr(self._data, "time", 0))

    def time_msc(self) -> int:
        """Get the open time in milliseconds.

        Returns:
            int: Time.
        """
        return int(getattr(self._data, "time_msc", 0))

    def time_update(self) -> int:
        """Get the update time of the position.

        Returns:
            int: Update time in seconds.
        """
        return int(getattr(self._data, "time_update", 0))

    def time_update_msc(self) -> int:
        """Get the update time in milliseconds.

        Returns:
            int: Update time.
        """
        return int(getattr(self._data, "time_update_msc", 0))

    def type(self) -> int:
        """Get the type of the position (0=Buy, 1=Sell).

        Returns:
            int: Position type.
        """
        return int(getattr(self._data, "type", 0))

    def type_description(self) -> str:
        """Get the description of the position type.

        Returns:
            str: Description (e.g., "Buy").
        """
        t = self.type()
        mapping = {
            0: "Buy",
            1: "Sell",
        }
        return mapping.get(t, f"Unknown ({t})")

    def magic(self) -> int:
        """Get the magic number of the position.

        Returns:
            int: Magic number.
        """
        return int(getattr(self._data, "magic", 0))

    def identifier(self) -> int:
        """Get the position identifier.

        Returns:
            int: Identifier.
        """
        return int(getattr(self._data, "identifier", getattr(self._data, "ticket", 0)))

    def volume(self) -> float:
        """Get the current volume of the position.

        Returns:
            float: Volume.
        """
        return float(getattr(self._data, "volume", 0.0))

    def price_open(self) -> float:
        """Get the open price of the position.

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

    def swap(self) -> float:
        """Get the accumulated swap of the position.

        Returns:
            float: Swap.
        """
        return float(getattr(self._data, "swap", 0.0))

    def profit(self) -> float:
        """Get the current floating profit of the position.

        Returns:
            float: Profit.
        """
        return float(getattr(self._data, "profit", 0.0))

    def symbol(self) -> str:
        """Get the symbol of the position.

        Returns:
            str: Symbol name.
        """
        return str(getattr(self._data, "symbol", ""))

    def comment(self) -> str:
        """Get the comment of the position.

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
            1: self.time(),
            2: self.type(),
            3: self.magic(),
            4: self.identifier(),
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
            1: self.price_open(),
            2: self.stop_loss(),
            3: self.take_profit(),
            4: self.price_current(),
            5: self.swap(),
            6: self.profit(),
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
