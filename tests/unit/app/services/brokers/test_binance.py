"""Unit tests for the BinanceClient broker service."""

from datetime import UTC, datetime

import pandas as pd
from app.services.brokers.binance import BinanceClient, get_binance_client
from pytest_mock import MockerFixture


def test_binance_client_initialization() -> None:
    client = BinanceClient(
        api_key="key",  # pragma: allowlist secret
        api_secret="secret",  # pragma: allowlist secret
    )
    assert client.api_key == "key"  # pragma: allowlist secret
    assert client.api_secret == "secret"  # pragma: allowlist secret
    assert client.is_connected() is False


def test_binance_client_connect_disconnect() -> None:
    client = BinanceClient()
    assert client.connect() is True
    assert client.is_connected() is True
    client.disconnect()
    assert client.is_connected() is False


def test_get_binance_client_singleton() -> None:
    client1 = get_binance_client()
    client2 = get_binance_client()
    assert client1 is client2
    assert isinstance(client1, BinanceClient)


def test_binance_get_bars_by_count(mocker: MockerFixture) -> None:
    mock_api = mocker.patch("app.services.brokers.binance.BinanceAPIClient")
    mock_instance = mock_api.return_value

    # Mock return value of get_klines
    # format: [time, open, high, low, close, volume, ...]
    mock_instance.get_klines.return_value = [
        [
            1717200000000,
            "1.1000",
            "1.1010",
            "1.0990",
            "1.1005",
            "100.0",
            "0.0",
            "0",
            "0",
            "0",
            "0",
            "0",
        ]
    ]

    client = BinanceClient()
    df = client.get_bars(symbol="BTCUSD", timeframe="H1", count=1)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["Open"] == 1.1000
    assert df.iloc[0]["Volume"] == 100.0
    mock_instance.get_klines.assert_called_once()


def test_binance_get_bars_by_date(mocker: MockerFixture) -> None:
    mock_api = mocker.patch("app.services.brokers.binance.BinanceAPIClient")
    mock_instance = mock_api.return_value
    mock_instance.get_historical_klines.return_value = [
        [
            1717200000000,
            "1.1000",
            "1.1010",
            "1.0990",
            "1.1005",
            "100.0",
            "0.0",
            "0",
            "0",
            "0",
            "0",
            "0",
        ]
    ]

    client = BinanceClient()
    date_from = datetime(2026, 6, 1, tzinfo=UTC)
    date_to = datetime(2026, 6, 2, tzinfo=UTC)
    df = client.get_bars(
        symbol="BTCUSD", timeframe="H1", date_from=date_from, date_to=date_to
    )

    assert len(df) == 1
    mock_instance.get_historical_klines.assert_called_once()


def test_binance_get_ticks_recent(mocker: MockerFixture) -> None:
    mock_api = mocker.patch("app.services.brokers.binance.BinanceAPIClient")
    mock_instance = mock_api.return_value
    mock_instance.get_recent_trades.return_value = [
        {"price": "1.1000", "qty": "10.0", "time": 1717200000000}
    ]

    client = BinanceClient()
    res = client.get_ticks(symbol="BTCUSD", count=1, as_dataframe=False)

    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]["bid"] == 1.1000
    mock_instance.get_recent_trades.assert_called_once()


def test_binance_get_ticks_range(mocker: MockerFixture) -> None:
    mock_api = mocker.patch("app.services.brokers.binance.BinanceAPIClient")
    mock_instance = mock_api.return_value
    mock_instance.get_aggregate_trades.return_value = [
        {"p": "1.1000", "q": "10.0", "T": 1717200000000}
    ]

    client = BinanceClient()
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)
    df = client.get_ticks(symbol="BTCUSD", start=start, end=end, as_dataframe=True)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    mock_instance.get_aggregate_trades.assert_called_once()
