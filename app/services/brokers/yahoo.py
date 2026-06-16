"""Yahoo Finance broker client service.

This module provides the YahooClient class responsible for managing the connection
to Yahoo Finance via yfinance, fetching real historical bars, and generating
synthetic tick data based on price constraints.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from app.utils.logger import logger


class YahooClient:
    """Client for interacting with the Yahoo Finance interface.

    Handles initialization, connection checking, and lifecycle connection gates.
    """

    _instance: "YahooClient | None" = None

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the Yahoo Finance client.

        Args:
            api_key: Optional API key if using premium endpoints.
        """
        self.api_key = api_key
        self._connected = False

        logger.info(
            "YahooClient initialized",
            extra={
                "has_api_key": self.api_key is not None,
            },
        )

    def connect(self) -> bool:
        """Initialize connection to Yahoo Finance feed.

        Returns:
            bool: True if connection was completed successfully.
        """
        self._connected = True
        logger.info("Yahoo Finance client connected successfully.")
        return True

    def disconnect(self) -> None:
        """Shutdown the connection and clean up resources."""
        self._connected = False
        logger.info("Yahoo Finance client disconnected successfully.")

    def is_connected(self) -> bool:
        """Check if client is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._connected

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100,
        start_pos: int = 0,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> pd.DataFrame:
        """Get OHLCVS bars from Yahoo Finance.

        Args:
            symbol: Symbol name (e.g. "AAPL").
            timeframe: Timeframe string (e.g., "M1", "H1", "D1").
            count: Number of bars to return (used if date_from is None).
            start_pos: Start position (index) for fetching bars
                (used if date_from is None).
            date_from: Start date for fetching bars.
            date_to: End date for fetching bars (defaults to now if date_from is set).

        Returns:
            pd.DataFrame with columns:
            ["Timestamp", "Open", "High", "Low", "Close", "Volume", "Spread"]
        """
        if not self.is_connected():
            self.connect()

        # map timeframe to yfinance interval
        tf_map = {
            "M1": "1m",
            "M2": "2m",
            "M5": "5m",
            "M15": "15m",
            "M30": "30m",
            "H1": "1h",
            "D1": "1d",
            "W1": "1wk",
            "MN1": "1mo",
        }
        tf_upper = timeframe.upper()
        interval = tf_map.get(tf_upper, "1h")

        if date_from is None:
            # Download by period
            period_map = {
                "1m": "1d",
                "2m": "1d",
                "5m": "5d",
                "15m": "5d",
                "30m": "5d",
                "1h": "1mo",
                "1d": "1y",
                "1wk": "5y",
                "1mo": "max",
            }
            period = period_map.get(interval, "1mo")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
        else:
            ticker = yf.Ticker(symbol)
            start_str = date_from.strftime("%Y-%m-%d")
            end_dt = date_to or datetime.now(UTC)
            end_str = end_dt.strftime("%Y-%m-%d")
            df = ticker.history(start=start_str, end=end_str, interval=interval)

        cols = ["Timestamp", "Open", "High", "Low", "Close", "Volume", "Spread"]
        if df.empty:
            return pd.DataFrame(columns=cols)

        df = df.reset_index()
        date_col = (
            "Datetime"
            if "Datetime" in df.columns
            else ("Date" if "Date" in df.columns else df.columns[0])
        )
        df = df.rename(
            columns={
                date_col: "Timestamp",
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Volume": "Volume",
            }
        )
        df["Spread"] = 0.0

        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)

        if date_from is None:
            df = df.tail(count + start_pos).head(count)

        return df[cols]

    def get_ticks(
        self,
        symbol: str,
        count: int = 100,
        start: datetime | None = None,
        end: datetime | None = None,  # noqa: ARG002
        as_dataframe: bool = True,
    ) -> pd.DataFrame | list[dict[str, Any]] | None:
        """Get ticks from Yahoo Finance (mocked/generated from daily bounds).

        Args:
            symbol: Trading symbol.
            count: Number of ticks to retrieve.
            start: Start date/time.
            end: End date/time.
            as_dataframe: Return as DataFrame (True) or list of dicts (False).

        Returns:
            DataFrame or list of dicts containing tick data, or None on error.
        """
        if not self.is_connected():
            self.connect()

        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        last_price = 100.0
        if not history.empty:
            last_price = float(history["Close"].iloc[-1])

        # Generate synthetic tick updates
        from app.services.data.transforms import (
            generate_synthetic_ticks,
        )

        start_str = (start or datetime.now(UTC) - timedelta(minutes=10)).isoformat()
        ticks = generate_synthetic_ticks(
            symbol=symbol,
            start_time=start_str,
            num_ticks=count,
            start_price=last_price,
            average_spread=0.01,
            volatility=0.001,
        )

        df = pd.DataFrame(ticks)
        if df.empty:
            return pd.DataFrame() if as_dataframe else []

        df["Timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.rename(
            columns={"bid": "bid", "ask": "ask", "last": "last", "volume": "volume"}
        )
        df["spread"] = df["ask"] - df["bid"]

        res_df = df[["Timestamp", "bid", "ask", "last", "volume", "spread"]]

        if as_dataframe:
            return res_df
        return res_df.to_dict(orient="records")

    @classmethod
    def get_instance(cls) -> "YahooClient":
        """Get the shared singleton instance of YahooClient.

        Returns:
            YahooClient: The shared YahooClient instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_yahoo_client() -> YahooClient:
    """Get the shared singleton instance of YahooClient.

    Returns:
        YahooClient: The shared YahooClient instance.
    """
    return YahooClient.get_instance()
