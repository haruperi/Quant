# ruff: noqa: E501, ANN401
"""Result builders and response normalizers.

Defines the normalized trade execution output envelope, masking
provider-specific (MT5, cTrader, Simulator) details from core services.
"""

from typing import Any

from app.utils.logger import logger


class NormalizedTradeResult:
    """Normalized response representation for broker trading operations."""

    def __init__(
        self,
        retcode: int,
        deal: int,
        order: int,
        volume: float,
        price: float,
        bid: float,
        ask: float,
        comment: str,
        filled_volume: float = 0.0,
        average_price: float = 0.0,
        remaining_volume: float = 0.0,
    ) -> None:
        """Initialize NormalizedTradeResult."""
        self.retcode = retcode
        self.deal = deal
        self.order = order
        self.volume = volume
        self.price = price
        self.bid = bid
        self.ask = ask
        self.comment = comment
        self.filled_volume = filled_volume
        self.average_price = average_price
        self.remaining_volume = remaining_volume

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary.

        Returns:
            dict[str, Any]: Dictionary representation of the result.
        """
        return {
            "retcode": self.retcode,
            "deal": self.deal,
            "order": self.order,
            "volume": self.volume,
            "price": self.price,
            "bid": self.bid,
            "ask": self.ask,
            "comment": self.comment,
            "filled_volume": self.filled_volume,
            "average_price": self.average_price,
            "remaining_volume": self.remaining_volume,
        }


class BrokerResponseNormalizer:
    """Normalizes raw broker-specific response objects into provider-agnostic results."""

    @staticmethod
    def normalize_response(provider: str, raw_result: Any) -> NormalizedTradeResult:
        """Normalize raw results from different brokers.

        Args:
            provider: The name of the broker provider ('mt5', 'ctrader', 'sim').
            raw_result: The raw object or dictionary returned by the broker wrapper.

        Returns:
            NormalizedTradeResult: Normalized trade result.
        """
        if raw_result is None:
            return NormalizedTradeResult(
                retcode=10001,  # Error code representing failure
                deal=0,
                order=0,
                volume=0.0,
                price=0.0,
                bid=0.0,
                ask=0.0,
                comment="Received null response from broker.",
            )

        # 1. Normalize based on dict interface or object attributes
        if isinstance(raw_result, dict):
            retcode = int(raw_result.get("retcode", 0))
            deal = int(raw_result.get("deal", 0))
            order = int(raw_result.get("order", 0))
            volume = float(raw_result.get("volume", 0.0))
            price = float(raw_result.get("price", 0.0))
            bid = float(raw_result.get("bid", 0.0))
            ask = float(raw_result.get("ask", 0.0))
            comment = str(raw_result.get("comment", ""))
        else:
            retcode = int(getattr(raw_result, "retcode", 0))
            deal = int(getattr(raw_result, "deal", 0))
            order = int(getattr(raw_result, "order", 0))
            volume = float(getattr(raw_result, "volume", 0.0))
            price = float(getattr(raw_result, "price", 0.0))
            bid = float(getattr(raw_result, "bid", 0.0))
            ask = float(getattr(raw_result, "ask", 0.0))
            comment = str(getattr(raw_result, "comment", ""))

        # 2. Derive partial fill details
        # For simple successful deals: filled volume defaults to total volume, remaining is 0
        is_success = retcode in (10009, 10008, 0)
        filled_vol = volume if (is_success and deal > 0) else 0.0
        rem_vol = 0.0 if (is_success and deal > 0) else volume
        avg_price = price if (is_success and deal > 0) else 0.0

        if isinstance(raw_result, dict):
            filled_vol = float(raw_result.get("filled_volume", filled_vol))
            avg_price = float(raw_result.get("average_price", avg_price))
            rem_vol = float(raw_result.get("remaining_volume", rem_vol))
        else:
            filled_vol = float(getattr(raw_result, "filled_volume", filled_vol))
            avg_price = float(getattr(raw_result, "average_price", avg_price))
            rem_vol = float(getattr(raw_result, "remaining_volume", rem_vol))

        logger.info(
            "Normalized broker response",
            extra={
                "provider": provider,
                "retcode": retcode,
                "deal": deal,
                "order": order,
                "filled_volume": filled_vol,
                "remaining_volume": rem_vol,
            },
        )

        return NormalizedTradeResult(
            retcode=retcode,
            deal=deal,
            order=order,
            volume=volume,
            price=price,
            bid=bid,
            ask=ask,
            comment=comment,
            filled_volume=filled_vol,
            average_price=avg_price,
            remaining_volume=rem_vol,
        )


class ResultBuilder:
    """Helper to build failure/fallback responses without throwing exceptions."""

    @staticmethod
    def success(
        provider: str,
        raw_result: Any,
    ) -> NormalizedTradeResult:
        """Create a successful normalized result wrapper.

        Args:
            provider: The broker provider name.
            raw_result: The raw broker response.

        Returns:
            NormalizedTradeResult: Normalized trade result.
        """
        return BrokerResponseNormalizer.normalize_response(provider, raw_result)

    @staticmethod
    def failure(comment: str, retcode: int = 10001) -> NormalizedTradeResult:
        """Create a failure normalized result wrapper.

        Args:
            comment: Failure explanation comment.
            retcode: Error return code.

        Returns:
            NormalizedTradeResult: Normalized trade result.
        """
        return NormalizedTradeResult(
            retcode=retcode,
            deal=0,
            order=0,
            volume=0.0,
            price=0.0,
            bid=0.0,
            ask=0.0,
            comment=comment,
        )
