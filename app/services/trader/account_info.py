# ruff: noqa: PLR2004
"""MQL5-compatible AccountInfo class wrapping broker account properties.

Provides easy access to the currently opened trade account properties.
"""

from typing import Any, cast

from app.routes.brokers import get_broker_module


class AccountInfo:
    """Provides access to properties of the open trading account."""

    def __init__(self) -> None:
        """Initialize the AccountInfo instance."""
        self._data: Any = None

    def _refresh(self) -> None:
        broker = get_broker_module()
        self._data = broker.get_account_info()

    def login(self) -> int:
        """Get account login/number.

        Returns:
            int: Account number.
        """
        self._refresh()
        return cast("int", self._data.login) if self._data else 0

    def trade_mode(self) -> int:
        """Get trading account mode (0=Demo, 1=Contest, 2=Real).

        Returns:
            int: Mode identifier.
        """
        self._refresh()
        if not self._data:
            return 0
        server_str = str(self._data.server).upper()
        if "REAL" in server_str or "LIVE" in server_str:
            return 2
        return 0

    def trade_mode_description(self) -> str:
        """Get trading account mode description.

        Returns:
            str: Description of mode.
        """
        mode = self.trade_mode()
        return "Real" if mode == 2 else "Demo"

    def leverage(self) -> int:
        """Get account leverage.

        Returns:
            int: Leverage ratio.
        """
        self._refresh()
        return cast("int", self._data.leverage) if self._data else 1

    def limit_orders(self) -> int:
        """Get maximum allowed pending orders count.

        Returns:
            int: Limit.
        """
        self._refresh()
        return cast("int", self._data.limit_orders) if self._data else 0

    def trade_allowed(self) -> bool:
        """Check if trading is allowed for this account.

        Returns:
            bool: True if allowed.
        """
        self._refresh()
        return cast("bool", self._data.trade_allowed) if self._data else False

    def trade_expert(self) -> bool:
        """Check if Expert Advisor trading is allowed for this account.

        Returns:
            bool: True if allowed.
        """
        self._refresh()
        return cast("bool", self._data.trade_expert) if self._data else False

    def margin_so_mode(self) -> int:
        """Get stop-out mode.

        Returns:
            int: Stop-out mode (0 = percentage, 1 = money value).
        """
        return 0

    def margin_mode(self) -> int:
        """Get margin calculation mode (0=hedging, 1=netting).

        Returns:
            int: Margin mode identifier.
        """
        self._refresh()
        mode_str = str(getattr(self._data, "margin_mode", "Hedging")).upper()
        if "HEDGING" in mode_str:
            return 0
        return 1

    def margin_mode_description(self) -> str:
        """Get margin mode description string.

        Returns:
            str: Description.
        """
        self._refresh()
        return getattr(self._data, "margin_mode", "Hedging")

    def balance(self) -> float:
        """Get account balance.

        Returns:
            float: Balance in deposit currency.
        """
        self._refresh()
        return cast("float", self._data.balance) if self._data else 0.0

    def credit(self) -> float:
        """Get account credit value.

        Returns:
            float: Credit.
        """
        self._refresh()
        return cast("float", self._data.credit) if self._data else 0.0

    def profit(self) -> float:
        """Get current account floating profit.

        Returns:
            float: Profit.
        """
        self._refresh()
        return cast("float", self._data.profit) if self._data else 0.0

    def equity(self) -> float:
        """Get current account equity.

        Returns:
            float: Equity.
        """
        self._refresh()
        return cast("float", self._data.equity) if self._data else 0.0

    def margin(self) -> float:
        """Get current account used margin.

        Returns:
            float: Margin.
        """
        self._refresh()
        return cast("float", self._data.margin) if self._data else 0.0

    def free_margin(self) -> float:
        """Get account free margin.

        Returns:
            float: Free margin.
        """
        self._refresh()
        return cast("float", self._data.margin_free) if self._data else 0.0

    def free_margin_mode(self) -> int:
        """Get free margin calculation mode.

        Returns:
            int: Mode.
        """
        return 0

    def margin_level(self) -> float:
        """Get account margin level percentage.

        Returns:
            float: Margin level.
        """
        self._refresh()
        return cast("float", self._data.margin_level) if self._data else 0.0

    def margin_so_level(self) -> float:
        """Get stop out level value.

        Returns:
            float: Stop out level value.
        """
        self._refresh()
        return float(getattr(self._data, "margin_so_so", 50.0))

    def name(self) -> str:
        """Get account client name.

        Returns:
            str: Client name.
        """
        self._refresh()
        return cast("str", self._data.name) if self._data else ""

    def server(self) -> str:
        """Get trading server name.

        Returns:
            str: Server name.
        """
        self._refresh()
        return cast("str", self._data.server) if self._data else ""

    def currency(self) -> str:
        """Get account currency name.

        Returns:
            str: Currency.
        """
        self._refresh()
        return cast("str", self._data.currency) if self._data else "USD"

    def company(self) -> str:
        """Get broker company name.

        Returns:
            str: Company name.
        """
        self._refresh()
        return cast("str", self._data.company) if self._data else ""

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
            0: self._data.login,
            1: self.trade_mode(),
            2: self._data.leverage,
            3: self._data.limit_orders,
            4: 1 if self._data.trade_allowed else 0,
            5: 1 if self._data.trade_expert else 0,
            6: self.margin_mode(),
        }
        return int(prop_map.get(prop_id, 0))

    def info_double(self, prop_id: int) -> float:
        """Get generic double property.

        Args:
            prop_id: Property ID identifier.

        Returns:
            float: Value of property.
        """
        self._refresh()
        if not self._data:
            return 0.0
        prop_map = {
            0: self._data.balance,
            1: self._data.credit,
            2: self._data.profit,
            3: self._data.equity,
            4: self._data.margin,
            5: self._data.margin_free,
            6: self._data.margin_level,
        }
        return float(prop_map.get(prop_id, 0.0))

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
            0: self._data.name,
            1: self._data.server,
            2: self._data.currency,
            3: self._data.company,
        }
        return str(prop_map.get(prop_id, ""))
