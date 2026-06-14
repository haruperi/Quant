"""MQL5-compatible TerminalInfo class wrapping broker environment settings.

Provides access to properties of the program environment.
"""

from typing import Any, cast

from app.services.trader.resolver import get_broker_module


class TerminalInfo:
    """Provides access to properties of the program terminal environment."""

    def __init__(self) -> None:
        """Initialize the TerminalInfo instance."""
        self._data: Any = None

    def _refresh(self) -> None:
        broker = get_broker_module()
        self._data = broker.get_terminal_info()

    def language(self) -> str:
        """Get terminal language.

        Returns:
            str: Language string.
        """
        self._refresh()
        return cast("str", self._data.language) if self._data else "Python"

    def company(self) -> str:
        """Get broker company name.

        Returns:
            str: Company name.
        """
        self._refresh()
        return cast("str", self._data.company) if self._data else ""

    def name(self) -> str:
        """Get terminal name.

        Returns:
            str: Terminal name.
        """
        self._refresh()
        return cast("str", self._data.name) if self._data else ""

    def path(self) -> str:
        """Get terminal execution path.

        Returns:
            str: Path.
        """
        self._refresh()
        return cast("str", self._data.path) if self._data else ""

    def data_path(self) -> str:
        """Get terminal data folder path.

        Returns:
            str: Data path.
        """
        self._refresh()
        return cast("str", self._data.data_path) if self._data else ""

    def common_data_path(self) -> str:
        """Get common data folder path.

        Returns:
            str: Common data path.
        """
        self._refresh()
        return cast("str", self._data.commondata_path) if self._data else ""

    def build(self) -> int:
        """Get terminal build number.

        Returns:
            int: Build number.
        """
        self._refresh()
        return cast("int", self._data.build) if self._data else 0

    def connected(self) -> bool:
        """Check if terminal is connected to the trade server.

        Returns:
            bool: True if connected.
        """
        self._refresh()
        return cast("bool", self._data.connected) if self._data else False

    def trade_allowed(self) -> bool:
        """Check if trading is allowed for the terminal.

        Returns:
            bool: True if trading allowed.
        """
        self._refresh()
        return cast("bool", self._data.trade_allowed) if self._data else False

    def dlls_allowed(self) -> bool:
        """Check if DLL imports are allowed.

        Returns:
            bool: True if allowed.
        """
        self._refresh()
        return cast("bool", self._data.dlls_allowed) if self._data else False

    def ping_last(self) -> int:
        """Get last ping time to trade server.

        Returns:
            int: Last ping in microseconds.
        """
        self._refresh()
        return cast("int", self._data.ping_last) if self._data else 0

    def info_integer(self, prop_id: int) -> int:
        """Get generic integer property.

        Args:
            prop_id: Property ID identifier.

        Returns:
            int: Value of property.
        """
        self._refresh()
        if not self._data:
            return 0
        prop_map = {
            0: self._data.build,
            1: 1 if self._data.connected else 0,
            2: 1 if self._data.trade_allowed else 0,
            3: 1 if self._data.dlls_allowed else 0,
            4: self._data.ping_last,
        }
        return int(prop_map.get(prop_id, 0))

    def info_string(self, prop_id: int) -> str:
        """Get generic string property.

        Args:
            prop_id: Property ID identifier.

        Returns:
            str: Value of property.
        """
        self._refresh()
        if not self._data:
            return ""
        prop_map = {
            0: self._data.language,
            1: self._data.company,
            2: self._data.name,
            3: self._data.path,
            4: self._data.data_path,
            5: self._data.commondata_path,
        }
        return str(prop_map.get(prop_id, ""))
