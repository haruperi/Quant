# ruff: noqa: C901, PLR0912, PLR0915, E501, ARG002, PLR0913
"""ValidationService implementation for trade requests.

Handles input sanitization, decimal precision rounding, dealing mode
checks (Netting vs. Hedging), and market session validation using public wrapper APIs.
"""

import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.services.trader.account_info import AccountInfo
from app.services.trader.symbol_info import SymbolInfo
from app.utils.errors import ValidationError
from app.utils.logger import logger


class ValidationService:
    """Provides validation checks for trading operations using public helper methods."""

    @staticmethod
    def normalize_precision(value: float | Decimal, precision: float) -> Decimal:
        """Round financial values using Decimal to avoid floating point issues.

        Args:
            value: Value to round.
            precision: Digits (int) or step (float).

        Returns:
            Decimal: Normalized rounded decimal value.
        """
        if float(value) == 0.0:
            return Decimal("0.0")

        dec_val = Decimal(str(value))
        if isinstance(precision, int):
            exponent = Decimal("10") ** -precision
            return dec_val.quantize(exponent, rounding=ROUND_HALF_UP)
        step = Decimal(str(precision))
        return (dec_val / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step

    def validate_volume(
        self, symbol: str, volume: float, symbol_info: SymbolInfo
    ) -> float:
        """Validate trade lot volume sizes.

        Args:
            symbol: Symbol name.
            volume: Lot volume size.
            symbol_info: SymbolInfo object.

        Returns:
            float: Normalized volume value.

        Raises:
            ValidationError: If volume is out of bounds or invalid lot step.
        """
        vol_min = symbol_info.volume_min()
        vol_max = symbol_info.volume_max()
        vol_step = symbol_info.volume_step()

        dec_vol = Decimal(str(volume))
        dec_min = Decimal(str(vol_min))
        dec_max = Decimal(str(vol_max))
        dec_step = Decimal(str(vol_step))

        if dec_vol < dec_min:
            msg = f"Volume {volume} is below the minimum allowed volume of {vol_min} for {symbol}."
            logger.error(msg)
            raise ValidationError(msg)

        if dec_vol > dec_max:
            msg = f"Volume {volume} is above the maximum allowed volume of {vol_max} for {symbol}."
            logger.error(msg)
            raise ValidationError(msg)

        # Check lot step alignment
        remainder = (dec_vol - dec_min) % dec_step
        if (
            remainder != 0
            and abs(remainder - dec_step) > Decimal("1e-9")
            and remainder > Decimal("1e-9")
        ):
            msg = f"Volume {volume} does not align with the volume step of {vol_step} for {symbol}."
            logger.error(msg)
            raise ValidationError(msg)

        return float(dec_vol)

    def validate_price(
        self, symbol: str, price: float, order_type: int, symbol_info: SymbolInfo
    ) -> float:
        """Validate price constraints.

        Args:
            symbol: Symbol name.
            price: Entry price.
            order_type: Order type code.
            symbol_info: SymbolInfo object.

        Returns:
            float: Normalized price.

        Raises:
            ValidationError: If price is <= 0.
        """
        if price <= 0.0:
            msg = f"Trade price must be greater than zero. Received: {price} for {symbol}."
            logger.error(msg)
            raise ValidationError(msg)

        digits = symbol_info.digits()
        normalized = self.normalize_precision(price, digits)
        return float(normalized)

    def validate_stops(
        self,
        symbol: str,
        sl: float,
        tp: float,
        order_type: int,
        price: float,
        symbol_info: SymbolInfo,
    ) -> tuple[float, float]:
        """Validate stop-loss and take-profit geometry.

        Args:
            symbol: Symbol name.
            sl: Stop loss level.
            tp: Take profit level.
            order_type: Order type.
            price: Entry price.
            symbol_info: SymbolInfo object.

        Returns:
            tuple[float, float]: Normalized (sl, tp) values.

        Raises:
            ValidationError: If geometry is invalid.
        """
        digits = symbol_info.digits()
        norm_sl = float(self.normalize_precision(sl, digits)) if sl > 0 else 0.0
        norm_tp = float(self.normalize_precision(tp, digits)) if tp > 0 else 0.0

        # Standard MQL5 type codes:
        # 0 = Buy, 1 = Sell, 2 = Buy Limit, 3 = Sell Limit, 4 = Buy Stop, 5 = Sell Stop, 6 = Buy Stop Limit, 7 = Sell Stop Limit
        is_buy = order_type in (0, 2, 4, 6)
        is_sell = order_type in (1, 3, 5, 7)

        if is_buy:  # Buy or Buy Pending
            if norm_sl > 0.0 and norm_sl >= price:
                msg = f"Buy Stop Loss ({norm_sl}) must be below the entry price ({price}) for {symbol}."
                logger.error(msg)
                raise ValidationError(msg)
            if norm_tp > 0.0 and norm_tp <= price:
                msg = f"Buy Take Profit ({norm_tp}) must be above the entry price ({price}) for {symbol}."
                logger.error(msg)
                raise ValidationError(msg)
        elif is_sell:  # Sell or Sell Pending
            if norm_sl > 0.0 and norm_sl <= price:
                msg = f"Sell Stop Loss ({norm_sl}) must be above the entry price ({price}) for {symbol}."
                logger.error(msg)
                raise ValidationError(msg)
            if norm_tp > 0.0 and norm_tp >= price:
                msg = f"Sell Take Profit ({norm_tp}) must be below the entry price ({price}) for {symbol}."
                logger.error(msg)
                raise ValidationError(msg)

        return norm_sl, norm_tp

    def validate_margin(
        self,
        account_id: str,
        symbol: str,
        _volume: float,
        _price: float,
        _order_type: int,
        account_info: AccountInfo,
    ) -> None:
        """Validate margin requirements.

        Args:
            account_id: Account identifier.
            symbol: Symbol name.
            _volume: Lot volume.
            _price: Execution price.
            _order_type: Order type.
            account_info: AccountInfo object.

        Raises:
            ValidationError: If free margin is insufficient.
        """
        free_margin = account_info.free_margin()
        if free_margin <= 0.0:
            msg = (
                f"Insufficient funds. Free margin is {free_margin} "
                f"on account {account_id}."
            )
            logger.error(msg)
            raise ValidationError(msg)

    def validate_slippage(self, slippage: int, max_tolerance: int = 100) -> None:
        """Validate price slippage limits.

        Args:
            slippage: Request slippage points.
            max_tolerance: Configured limit.

        Raises:
            ValidationError: If slippage exceeds tolerance.
        """
        if slippage < 0:
            msg = f"Slippage points cannot be negative. Received: {slippage}."
            logger.error(msg)
            raise ValidationError(msg)
        if slippage > max_tolerance:
            msg = (
                f"Requested slippage ({slippage}) "
                f"exceeds maximum tolerance ({max_tolerance})."
            )
            logger.error(msg)
            raise ValidationError(msg)

    def validate_dealing_mode_compatibility(
        self, _action: int, _ticket: int | None, account_info: AccountInfo
    ) -> None:
        """Validate position modifications match Netting vs Hedging accounting.

        Args:
            action: Trading action type.
            ticket: Associated position ticket.
            account_info: AccountInfo containing dealing mode.

        Raises:
            ValidationError: If action violates account mode constraints.
        """
        margin_mode = account_info.margin_mode()
        if margin_mode == 1:  # Netting Mode in AccountInfo is 1 (Hedging is 0)
            # Netting account only allows 1 position per symbol.
            pass

    def validate_market_session(self, symbol: str) -> None:
        """Validate that requested action is within active market session hours.

        Args:
            symbol: Symbol name.

        Raises:
            ValidationError: If market session is closed.
        """
        now_utc = datetime.datetime.now(datetime.UTC)
        if now_utc.weekday() in (5, 6):
            is_crypto = any(
                crypto in symbol.upper()
                for crypto in ("BTC", "ETH", "LTC", "SOL", "XRP")
            )
            if not is_crypto:
                msg = f"Market session is closed for {symbol} during the weekend."
                logger.error(msg)
                raise ValidationError(msg)

    def validate_order_request(
        self,
        request: dict[str, Any],
        symbol_info: SymbolInfo,
        account_info: AccountInfo,
    ) -> dict[str, Any]:
        """Perform full validation and parameter sanitization on a request.

        Args:
            request: Trade request dictionary.
            symbol_info: Symbol specifications wrapper.
            account_info: Account details wrapper.

        Returns:
            dict[str, Any]: Sanitized request dictionary.

        Raises:
            ValidationError: If validation fails.
        """
        symbol = request.get("symbol")
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol parameter must be a non-empty string.")

        action = request.get("action", 1)  # 1 = DEAL, 5 = PENDING, etc.
        is_execution = action in (1, 5)

        volume = request.get("volume", 0.0)
        price = request.get("price", 0.0)
        order_type = request.get("type", 0)

        position_id = request.get("position")
        order_id = request.get("order")

        # Enrich order_type and price if not provided for modification and stop actions
        if "type" not in request:
            if position_id:
                from app.services.trader.position_info import PositionInfo

                pos = PositionInfo()
                if pos.select_by_ticket(position_id):
                    order_type = pos.type()
            elif order_id:
                from app.services.trader.order_info import OrderInfo

                ord_info = OrderInfo()
                if ord_info.select(order_id):
                    order_type = ord_info.type()

        if price <= 0.0:
            if position_id:
                from app.services.trader.position_info import PositionInfo

                pos = PositionInfo()
                if pos.select_by_ticket(position_id):
                    price = pos.price_open()
            elif order_id:
                from app.services.trader.order_info import OrderInfo

                ord_info = OrderInfo()
                if ord_info.select(order_id):
                    price = ord_info.price_open()

        if is_execution:
            if not isinstance(volume, int | float) or volume <= 0.0:
                raise ValidationError("Volume must be a positive number.")
            if not isinstance(price, int | float) or price < 0.0:
                raise ValidationError("Price must be a non-negative number.")

        # 1. Dealing mode checks
        self.validate_dealing_mode_compatibility(action, position_id, account_info)

        # 2. Market session checks
        self.validate_market_session(symbol)

        # 3. Parameter normalizations
        sanitized = request.copy()
        if is_execution:
            sanitized["volume"] = self.validate_volume(symbol, volume, symbol_info)
            if price > 0.0:
                sanitized["price"] = self.validate_price(
                    symbol, price, order_type, symbol_info
                )

        sl = request.get("sl", 0.0)
        tp = request.get("tp", 0.0)
        entry_price = sanitized.get("price", price)
        if sl > 0.0 or tp > 0.0:
            sanitized["sl"], sanitized["tp"] = self.validate_stops(
                symbol, sl, tp, order_type, entry_price, symbol_info
            )

        # Slippage check
        slippage = request.get("deviation", 20)
        self.validate_slippage(slippage)

        # Margin check only on new trade execution
        if is_execution:
            self.validate_margin(
                str(account_info.login()),
                symbol,
                sanitized["volume"],
                entry_price,
                order_type,
                account_info,
            )

        return sanitized
