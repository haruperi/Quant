# ruff: noqa: E501, C901, BLE001, PLR0911, EM102, ANN401, S113, N806, TRY201, PERF402, PLR2004
"""Dukascopy broker client service.

This module provides the DukascopyClient class responsible for managing the lifecycle
of connection endpoints for Dukascopy data feeds, and includes the HTTP freeserv scraper
to fetch real tick and bar data.
"""

import json
import random
import string
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from time import sleep
from typing import Any

import pandas as pd
import requests

from app.utils.logger import logger

TIME_UNIT_MONTH = "MONTH"
TIME_UNIT_WEEK = "WEEK"
TIME_UNIT_DAY = "DAY"
TIME_UNIT_HOUR = "HOUR"
TIME_UNIT_MIN = "MIN"
TIME_UNIT_SEC = "SEC"
TIME_UNIT_TICK = "TICK"

INTERVAL_MONTH_1 = f"1{TIME_UNIT_MONTH}"
INTERVAL_WEEK_1 = f"1{TIME_UNIT_WEEK}"
INTERVAL_DAY_1 = f"1{TIME_UNIT_DAY}"
INTERVAL_HOUR_4 = f"4{TIME_UNIT_HOUR}"
INTERVAL_HOUR_1 = f"1{TIME_UNIT_HOUR}"
INTERVAL_MIN_30 = f"30{TIME_UNIT_MIN}"
INTERVAL_MIN_15 = f"15{TIME_UNIT_MIN}"
INTERVAL_MIN_10 = f"10{TIME_UNIT_MIN}"
INTERVAL_MIN_5 = f"5{TIME_UNIT_MIN}"
INTERVAL_MIN_1 = f"1{TIME_UNIT_MIN}"
INTERVAL_SEC_30 = f"30{TIME_UNIT_SEC}"
INTERVAL_SEC_10 = f"10{TIME_UNIT_SEC}"
INTERVAL_SEC_1 = f"1{TIME_UNIT_SEC}"
INTERVAL_TICK = TIME_UNIT_TICK

_interval_units = {
    INTERVAL_MONTH_1: TIME_UNIT_MONTH,
    INTERVAL_WEEK_1: TIME_UNIT_WEEK,
    INTERVAL_DAY_1: TIME_UNIT_DAY,
    INTERVAL_HOUR_4: TIME_UNIT_HOUR,
    INTERVAL_HOUR_1: TIME_UNIT_HOUR,
    INTERVAL_MIN_30: TIME_UNIT_MIN,
    INTERVAL_MIN_15: TIME_UNIT_MIN,
    INTERVAL_MIN_10: TIME_UNIT_MIN,
    INTERVAL_MIN_5: TIME_UNIT_MIN,
    INTERVAL_MIN_1: TIME_UNIT_MIN,
    INTERVAL_SEC_30: TIME_UNIT_SEC,
    INTERVAL_SEC_10: TIME_UNIT_SEC,
    INTERVAL_SEC_1: TIME_UNIT_SEC,
    INTERVAL_TICK: TIME_UNIT_TICK,
}

OFFER_SIDE_BID = "B"
OFFER_SIDE_ASK = "A"


def _resample_to_nearest(
    timestamp: datetime,
    time_unit: str,
    interval_value: int,
) -> datetime:
    """Resample timestamp to nearest time unit.

    Args:
        timestamp: Timestamp to resample.
        time_unit: Time unit to resample to.
        interval_value: Interval value.

    Returns:
        Resampled timestamp.
    """
    if time_unit == TIME_UNIT_SEC:
        subtraction = timestamp.second % interval_value
        return timestamp - timedelta(
            seconds=subtraction,
            microseconds=timestamp.microsecond,
        )
    if time_unit == TIME_UNIT_MIN:
        subtraction = timestamp.minute % interval_value
        return timestamp - timedelta(
            minutes=subtraction,
            seconds=timestamp.second,
            microseconds=timestamp.microsecond,
        )
    if time_unit == TIME_UNIT_HOUR:
        subtraction = timestamp.hour % interval_value
        return timestamp - timedelta(
            hours=subtraction,
            minutes=timestamp.minute,
            seconds=timestamp.second,
            microseconds=timestamp.microsecond,
        )
    if time_unit == TIME_UNIT_DAY:
        subtraction = timestamp.day % interval_value
        return timestamp - timedelta(
            days=subtraction,
            hours=timestamp.hour,
            minutes=timestamp.minute,
            seconds=timestamp.second,
            microseconds=timestamp.microsecond,
        )
    if time_unit == TIME_UNIT_WEEK:
        subtraction = (timestamp.weekday() + 1) % (interval_value * 7)
        return timestamp - timedelta(
            days=subtraction,
            hours=timestamp.hour,
            minutes=timestamp.minute,
            seconds=timestamp.second,
            microseconds=timestamp.microsecond,
        )
    if time_unit == TIME_UNIT_MONTH:
        month = (timestamp.month // interval_value) + 1
        return datetime(timestamp.year, month, 1, 0, 0, 0, 0, timestamp.tzinfo)
    if time_unit == TIME_UNIT_TICK:
        return timestamp

    raise NotImplementedError(f"resampling not implemented for {time_unit}")


def _get_dataframe_columns_for_timeunit(time_unit: str) -> list[str]:
    """Get dataframe columns for time unit.

    Args:
        time_unit: Time unit.

    Returns:
        List of dataframe columns.
    """
    ohlc_df = ["timestamp", "open", "high", "low", "close", "volume"]
    tick_df = ["timestamp", "bidPrice", "askPrice", "bidVolume", "askVolume"]

    return {
        TIME_UNIT_DAY: ohlc_df,
        TIME_UNIT_HOUR: ohlc_df,
        TIME_UNIT_MIN: ohlc_df,
        TIME_UNIT_MONTH: ohlc_df,
        TIME_UNIT_SEC: ohlc_df,
        TIME_UNIT_TICK: tick_df,
        TIME_UNIT_WEEK: ohlc_df,
    }[time_unit]


def _fetch(
    instrument: str,
    interval: str,
    offer_side: str,
    last_update: int,
    limit: int | None = None,
) -> Any:
    """Fetch data from Dukascopy freeserv.

    Args:
        instrument: Instrument name.
        interval: Time interval.
        offer_side: Offer side.
        last_update: Last update timestamp.
        limit: Maximum number of records.

    Returns:
        Fetched data.
    """
    characters = string.ascii_letters + string.digits
    jsonp = f"_callbacks____{''.join(random.choices(characters, k=9))}"

    query_params = {
        "path": "chart/json3",
        "splits": "true",
        "stocks": "true",
        "time_direction": "N",
        "jsonp": jsonp,
        "last_update": f"{int(last_update)}",
        "offer_side": f"{offer_side}",
        "instrument": f"{instrument}",
        "interval": f"{interval}",
    }

    if limit is not None:
        query_params["limit"] = f"{int(limit)}"

    base_url = "https://freeserv.dukascopy.com/2.0/index.php"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
        "Host": "freeserv.dukascopy.com",
        "Referer": "https://freeserv.dukascopy.com/2.0/?path=chart/index&showUI=true&showTabs=true&showParameterToolbar=true&showOfferSide=true&allowInstrumentChange=true&allowPeriodChange=true&allowOfferSideChange=true&showAdditionalToolbar=true&showExportImportWorkspace=true&allowSocialSharing=true&showUndoRedoButtons=true&showDetachButton=true&presentationType=candle&axisX=true&axisY=true&legend=true&timeline=true&showDateSeparators=true&showZoom=true&showScrollButtons=true&showAutoShiftButton=true&crosshair=true&borders=false&freeMode=false&theme=Pastelle&uiColor=%23000&availableInstruments=l%3A&instrument=EUR/USD&period=5&offerSide=BID&timezone=0&live=true&allowPan=true&width=100%25&height=700&adv=popup&lang=en",
    }

    response = requests.get(base_url, headers=headers, params=query_params)
    jsonText = response.text.removeprefix(f"{jsonp}(").removesuffix(");")
    return json.loads(jsonText)


def _stream(
    instrument: str,
    interval: str,
    offer_side: str,
    start: datetime,
    end: datetime | None = None,
    max_retries: int = 7,
    limit: int | None = None,
) -> Generator[list[Any]]:
    """Stream data from Dukascopy freeserv.

    Args:
        instrument: Instrument name.
        interval: Time interval.
        offer_side: Offer side.
        start: Start timestamp.
        end: End timestamp.
        max_retries: Maximum number of retries.
        limit: Maximum number of records.
    """
    no_of_retries = 0
    cursor = int(start.timestamp() * 1000)
    end_timestamp = None
    if end is not None:
        end_timestamp = end.timestamp() * 1000

    is_first_iteration = True

    while True:
        try:
            lastUpdates = _fetch(
                instrument=instrument,
                interval=interval,
                offer_side=offer_side,
                last_update=cursor,
                limit=limit,
            )

            if not is_first_iteration and lastUpdates and lastUpdates[0][0] == cursor:
                lastUpdates = lastUpdates[1:]

            if not lastUpdates or len(lastUpdates) < 1:
                if end is not None:
                    break
                else:
                    sleep(0.5)
                    continue

            for row in lastUpdates:
                if end_timestamp is not None and row[0] > end_timestamp:
                    return
                if interval == INTERVAL_TICK:
                    row[-1] = row[-1] / 1_000_000
                    row[-2] = row[-2] / 1_000_000
                yield row
                cursor = row[0]

            no_of_retries = 0
            is_first_iteration = False

        except Exception as e:
            no_of_retries += 1
            if max_retries is not None and (no_of_retries - 1) > max_retries:
                raise e
            else:
                sleep(1)
            continue


def fetch(
    instrument: str,
    interval: str,
    offer_side: str,
    start: datetime,
    end: datetime,
    max_retries: int = 7,
    limit: int = 30_000,
) -> pd.DataFrame:
    """Fetch data from Dukascopy freeserv.

    Args:
        instrument: Instrument name.
        interval: Time interval.
        offer_side: Offer side.
        start: Start timestamp.
        end: End timestamp.
        max_retries: Maximum number of retries.
        limit: Maximum number of records.

    Returns:
        Fetched data.
    """
    time_unit = _interval_units[interval]
    columns = _get_dataframe_columns_for_timeunit(time_unit)

    data = []
    datafeed = _stream(
        instrument=instrument,
        interval=interval,
        offer_side=offer_side,
        start=start,
        end=end,
        max_retries=max_retries,
        limit=limit,
    )

    for row in datafeed:
        data.append(row)

    df = pd.DataFrame(data=data, columns=columns)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="ms",
        utc=True,
    )
    df = df.set_index("timestamp")
    return df


class DukascopyClient:
    """Client for interacting with the Dukascopy feed interface.

    Handles initialization, connection checking, and lifecycle connection gates.
    """

    _instance: "DukascopyClient | None" = None

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize the Dukascopy client with account credentials.

        Args:
            username: Optional Dukascopy login/account username.
            password: Optional password for user authentication.
        """
        self.username = username
        self.password = password
        self._connected = False

        logger.info(
            "DukascopyClient initialized",
            extra={
                "username": self.username,
            },
        )

    def connect(self) -> bool:
        """Initialize connection to Dukascopy feed.

        Returns:
            bool: True if connection was completed successfully.
        """
        self._connected = True
        logger.info("Dukascopy client connected successfully.")
        return True

    def disconnect(self) -> None:
        """Shutdown the connection and clean up resources."""
        self._connected = False
        logger.info("Dukascopy client disconnected successfully.")

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
        """Get OHLCVS bars from Dukascopy.

        Args:
            symbol: Symbol name (e.g. "EURUSD").
            timeframe: Timeframe string (e.g., "M1", "H1", "D1").
            count: Number of bars to return (used if date_from is None).
            start_pos: Start position index (used if date_from is None).
            date_from: Start date.
            date_to: End date (defaults to now if date_from is set).

        Returns:
            pd.DataFrame with columns:
            ["Timestamp", "Open", "High", "Low", "Close", "Volume", "Spread"]
        """
        if not self.is_connected():
            self.connect()

        # Normalise symbol: e.g. "EURUSD" -> "EUR/USD"
        if len(symbol) == 6 and "/" not in symbol:
            instrument = f"{symbol[:3].upper()}/{symbol[3:].upper()}"
        else:
            instrument = symbol

        # Map standard timeframe to Dukascopy interval
        tf_map = {
            "M1": "1MIN",
            "M5": "5MIN",
            "M15": "15MIN",
            "M30": "30MIN",
            "H1": "1HOUR",
            "H4": "4HOUR",
            "D1": "1DAY",
            "W1": "1WEEK",
            "MN1": "1MONTH",
        }
        tf_upper = timeframe.upper()
        if tf_upper not in tf_map:
            msg = f"Unsupported Dukascopy timeframe: {timeframe}"
            raise ValueError(msg)
        dukas_interval = tf_map[tf_upper]

        # Calculate time range if date_from is not specified
        if date_from is None:
            period_hours = {
                "M1": 1 / 60,
                "M5": 5 / 60,
                "M15": 15 / 60,
                "M30": 30 / 60,
                "H1": 1,
                "H4": 4,
                "D1": 24,
                "W1": 168,
                "MN1": 720,
            }
            hours_needed = (count + start_pos) * period_hours.get(tf_upper, 1)
            # buffer for weekends
            buffer_multiplier = 2.0 if tf_upper in ("D1", "W1") else 1.5
            dt_to = date_to if date_to is not None else datetime.now(UTC)
            dt_from = dt_to - timedelta(hours=hours_needed * buffer_multiplier)
        else:
            dt_from = date_from
            dt_to = date_to if date_to is not None else datetime.now(UTC)

        try:
            df = fetch(
                instrument=instrument,
                interval=dukas_interval,
                offer_side="B",
                start=dt_from,
                end=dt_to,
                limit=30000,
            )
        except Exception as e:
            logger.error("Dukascopy fetch failed: %s", e)
            return pd.DataFrame(
                columns=[
                    "Timestamp",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                    "Spread",
                ]
            )

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "Timestamp",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                    "Spread",
                ]
            )

        df = df.reset_index()
        df = df.rename(
            columns={
                "timestamp": "Timestamp",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )
        df["Spread"] = 0.0002  # standard EURUSD 2-pip spread representation

        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)

        if date_from is None:
            df = df.tail(count)

        return df[["Timestamp", "Open", "High", "Low", "Close", "Volume", "Spread"]]

    def get_ticks(
        self,
        symbol: str,
        count: int = 100,
        start: datetime | None = None,
        end: datetime | None = None,
        as_dataframe: bool = True,
    ) -> pd.DataFrame | list[dict[str, Any]] | None:
        """Get ticks from Dukascopy.

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

        if len(symbol) == 6 and "/" not in symbol:
            instrument = f"{symbol[:3].upper()}/{symbol[3:].upper()}"
        else:
            instrument = symbol

        if start is None:
            dt_end = end if end is not None else datetime.now(UTC)
            dt_start = dt_end - timedelta(hours=1)
        else:
            dt_start = start
            dt_end = end if end is not None else datetime.now(UTC)

        try:
            df = fetch(
                instrument=instrument,
                interval="TICK",
                offer_side="B",
                start=dt_start,
                end=dt_end,
                limit=30000,
            )
        except Exception as e:
            logger.error("Dukascopy tick fetch failed: %s", e)
            return None

        if df.empty:
            return pd.DataFrame() if as_dataframe else []

        df = df.reset_index()
        df = df.rename(
            columns={
                "timestamp": "Timestamp",
                "bidPrice": "bid",
                "askPrice": "ask",
            }
        )
        df["last"] = (df["bid"] + df["ask"]) / 2.0
        df["volume"] = df["bidVolume"]
        df["spread"] = df["ask"] - df["bid"]

        df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)

        res_df = df[["Timestamp", "bid", "ask", "last", "volume", "spread"]]

        if start is None:
            res_df = res_df.tail(count)

        if as_dataframe:
            return res_df
        return res_df.to_dict(orient="records")

    @classmethod
    def get_instance(cls) -> "DukascopyClient":
        """Get the shared singleton instance of DukascopyClient.

        Returns:
            DukascopyClient: The shared DukascopyClient instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_dukascopy_client() -> DukascopyClient:
    """Get the shared singleton instance of DukascopyClient.

    Returns:
        DukascopyClient: The shared DukascopyClient instance.
    """
    return DukascopyClient.get_instance()
