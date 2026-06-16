"""Unit tests for the YahooClient broker service."""

from datetime import UTC, datetime

import pandas as pd
from app.services.brokers.yahoo import YahooClient, get_yahoo_client
from pytest_mock import MockerFixture


def test_yahoo_client_initialization() -> None:
    client = YahooClient(api_key="key")  # pragma: allowlist secret
    assert client.api_key == "key"  # pragma: allowlist secret
    assert client.is_connected() is False


def test_yahoo_client_connect_disconnect() -> None:
    client = YahooClient()
    assert client.connect() is True
    assert client.is_connected() is True
    client.disconnect()
    assert client.is_connected() is False


def test_get_yahoo_client_singleton() -> None:
    client1 = get_yahoo_client()
    client2 = get_yahoo_client()
    assert client1 is client2
    assert isinstance(client1, YahooClient)


def test_yahoo_get_bars_by_count(mocker: MockerFixture) -> None:
    mock_ticker_class = mocker.patch("app.services.brokers.yahoo.yf.Ticker")
    mock_ticker_instance = mock_ticker_class.return_value

    # Mock history dataframe returned by yfinance
    mock_df = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [101.0],
            "Low": [99.0],
            "Close": [100.5],
            "Volume": [1000],
        },
        index=pd.DatetimeIndex(["2026-06-01 10:00:00+00:00"]),
    )
    mock_df.index.name = "Datetime"

    mock_ticker_instance.history.return_value = mock_df

    client = YahooClient()
    df = client.get_bars(symbol="AAPL", timeframe="H1", count=1)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["Open"] == 100.0
    assert df.iloc[0]["Volume"] == 1000
    mock_ticker_class.assert_called_once_with("AAPL")
    mock_ticker_instance.history.assert_called_once()


def test_yahoo_get_bars_by_date(mocker: MockerFixture) -> None:
    mock_ticker_class = mocker.patch("app.services.brokers.yahoo.yf.Ticker")
    mock_ticker_instance = mock_ticker_class.return_value

    mock_df = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [101.0],
            "Low": [99.0],
            "Close": [100.5],
            "Volume": [1000],
        },
        index=pd.DatetimeIndex(["2026-06-01 10:00:00+00:00"]),
    )
    mock_df.index.name = "Datetime"

    mock_ticker_instance.history.return_value = mock_df

    client = YahooClient()
    date_from = datetime(2026, 6, 1, tzinfo=UTC)
    date_to = datetime(2026, 6, 2, tzinfo=UTC)
    df = client.get_bars(
        symbol="AAPL", timeframe="H1", date_from=date_from, date_to=date_to
    )

    assert len(df) == 1
    mock_ticker_instance.history.assert_called_once()


def test_yahoo_get_ticks(mocker: MockerFixture) -> None:
    mock_ticker_class = mocker.patch("app.services.brokers.yahoo.yf.Ticker")
    mock_ticker_instance = mock_ticker_class.return_value
    mock_ticker_instance.history.return_value = pd.DataFrame({"Close": [100.5]})

    mock_generate = mocker.patch(
        "app.services.data.transforms.generate_synthetic_ticks"
    )
    mock_generate.return_value = [
        {
            "timestamp": "2026-06-01T10:00:00Z",
            "bid": 100.4,
            "ask": 100.6,
            "last": 100.5,
            "volume": 10,
        }
    ]

    client = YahooClient()
    res = client.get_ticks(symbol="AAPL", count=1, as_dataframe=False)

    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]["bid"] == 100.4
    mock_ticker_instance.history.assert_called_once_with(period="1d")
    mock_generate.assert_called_once()
