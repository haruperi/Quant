# ruff: noqa: BLE001
"""MQL5-compatible SymbolInfo class wrapping symbol specifications.

Provides access to the symbol properties.
"""

from typing import Any, cast

from app.routes.brokers import get_broker_module


class SymbolInfo:
    """Provides access to properties of a financial instrument symbol."""

    def __init__(self, name: str | None = None) -> None:
        """Initialize the SymbolInfo instance.

        Args:
            name: Optional symbol name string.
        """
        self._name: str = name or ""
        self._data: Any = None

    def name(self, name: str | None = None) -> str | bool:
        """Get or set the symbol name.

        Args:
            name: Optional symbol name string to set.

        Returns:
            str | bool: True if setting name, or symbol name string if getting.
        """
        if name is not None:
            self._name = name
            self._data = None
            return True
        return self._name

    def refresh(self) -> bool:
        """Refresh symbol specifications from broker.

        Returns:
            bool: True if refresh succeeded.
        """
        if not self._name:
            return False
        broker = get_broker_module()
        self._data = broker.get_symbol_info(self._name)
        return self._data is not None

    def refresh_rates(self) -> bool:
        """Refresh current prices (bid/ask).

        Returns:
            bool: True if refresh succeeded.
        """
        return self.refresh()

    def select(self, select: bool) -> bool:
        """Add/remove symbol to/from Market Watch.

        Args:
            select: Set flag to True to add.

        Returns:
            bool: True if operation succeeded.
        """
        if not self._name:
            return False
        broker = get_broker_module()
        client = (
            broker.get_ctrader_client()
            if hasattr(broker, "get_ctrader_client")
            else broker.get_mt5_client()
        )
        if hasattr(client, "subscribe_spots") and select:
            try:
                client.subscribe_spots(self._name)
                return True
            except Exception:
                return False
        return True

    def is_synchronized(self) -> bool:
        """Check if symbol rates are synchronized with server.

        Returns:
            bool: True.
        """
        return True

    def digits(self) -> int:
        """Get symbol decimal digits.

        Returns:
            int: Digits count.
        """
        self.refresh()
        return cast("int", self._data.digits) if self._data else 0

    def point(self) -> float:
        """Get symbol point value (1 / 10^digits).

        Returns:
            float: Point.
        """
        self.refresh()
        return cast("float", self._data.point) if self._data else 0.0

    def tick_size(self) -> float:
        """Get symbol tick size.

        Returns:
            float: Tick size.
        """
        self.refresh()
        return cast("float", self._data.trade_tick_size) if self._data else 0.0

    def trade_mode(self) -> int:
        """Get symbol trade mode.

        Returns:
            int: Trade mode identifier.
        """
        self.refresh()
        return cast("int", getattr(self._data, "trade_mode", 0)) if self._data else 0

    def trade_mode_description(self) -> str:
        """Get symbol trade mode description.

        Returns:
            str: Description.
        """
        return "Full Access"

    def contract_size(self) -> float:
        """Get symbol contract size.

        Returns:
            float: Contract size.
        """
        self.refresh()
        return cast("float", self._data.trade_contract_size) if self._data else 0.0

    def volume_min(self) -> float:
        """Get minimum allowed order volume.

        Returns:
            float: Minimum lot volume.
        """
        self.refresh()
        return cast("float", self._data.volume_min) if self._data else 0.0

    def volume_max(self) -> float:
        """Get maximum allowed order volume.

        Returns:
            float: Maximum lot volume.
        """
        self.refresh()
        return cast("float", self._data.volume_max) if self._data else 0.0

    def volume_step(self) -> float:
        """Get minimum lot volume step.

        Returns:
            float: Step volume.
        """
        self.refresh()
        return cast("float", self._data.volume_step) if self._data else 0.0

    def swap_mode(self) -> int:
        """Get symbol swap mode.

        Returns:
            int: Swap mode.
        """
        self.refresh()
        return cast("int", self._data.swap_mode) if self._data else 0

    def swap_long(self) -> float:
        """Get swap value for long positions.

        Returns:
            float: Long swap.
        """
        self.refresh()
        return cast("float", self._data.swap_long) if self._data else 0.0

    def swap_short(self) -> float:
        """Get swap value for short positions.

        Returns:
            float: Short swap.
        """
        self.refresh()
        return cast("float", self._data.swap_short) if self._data else 0.0

    def bid(self) -> float:
        """Get current bid price.

        Returns:
            float: Bid price.
        """
        self.refresh()
        return cast("float", self._data.bid) if self._data else 0.0

    def ask(self) -> float:
        """Get current ask price.

        Returns:
            float: Ask price.
        """
        self.refresh()
        return cast("float", self._data.ask) if self._data else 0.0

    def last(self) -> float:
        """Get current last transaction price.

        Returns:
            float: Last price.
        """
        self.refresh()
        return cast("float", self._data.last) if self._data else 0.0

    def spread(self) -> int:
        """Get current spread in points.

        Returns:
            int: Spread points.
        """
        self.refresh()
        return cast("int", self._data.spread) if self._data else 0

    def info_integer(self, prop_id: int) -> int:
        """Get generic integer property.

        Args:
            prop_id: Property ID identifier.

        Returns:
            int: Value of property.
        """
        self.refresh()
        if not self._data:
            return 0
        prop_map = {
            0: self._data.digits,
            1: getattr(self._data, "trade_mode", 0),
            2: self._data.swap_mode,
            3: self._data.spread,
        }
        return int(prop_map.get(prop_id, 0))

    def info_double(self, prop_id: int) -> float:
        """Get generic double property.

        Args:
            prop_id: Property ID identifier.

        Returns:
            float: Value of property.
        """
        self.refresh()
        if not self._data:
            return 0.0
        prop_map = {
            0: self._data.point,
            1: self._data.trade_tick_size,
            2: self._data.trade_contract_size,
            3: self._data.volume_min,
            4: self._data.volume_max,
            5: self._data.volume_step,
            6: self._data.swap_long,
            7: self._data.swap_short,
            8: self._data.bid,
            9: self._data.ask,
            10: self._data.last,
        }
        return float(prop_map.get(prop_id, 0.0))

    def info_string(self, prop_id: int) -> str:
        """Get generic string property.

        Args:
            prop_id: Property ID identifier.

        Returns:
            str: Value of property.
        """
        self.refresh()
        if not self._data:
            return ""
        prop_map = {
            0: self._data.name,
            1: getattr(self._data, "description", ""),
            2: getattr(self._data, "path", ""),
        }
        return str(prop_map.get(prop_id, ""))
