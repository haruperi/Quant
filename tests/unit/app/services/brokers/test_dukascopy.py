"""Unit tests for the DukascopyClient broker service and HTTP scraper."""

from typing import Any

import pandas as pd
import pytest
from app.services.brokers.dukascopy import DukascopyClient, get_dukascopy_client
from pytest_mock import MockerFixture


def test_dukascopy_client_initialization() -> None:
    client = DukascopyClient(
        username="user",
        password="pwd",  # pragma: allowlist secret
    )
    assert client.username == "user"
    assert client.password == "pwd"  # pragma: allowlist secret
    assert client.is_connected() is False


def test_dukascopy_client_connect_disconnect() -> None:
    client = DukascopyClient()
    assert client.connect() is True
    assert client.is_connected() is True
    client.disconnect()
    assert client.is_connected() is False


def test_get_dukascopy_client_singleton() -> None:
    client1 = get_dukascopy_client()
    client2 = get_dukascopy_client()
    assert client1 is client2
    assert isinstance(client1, DukascopyClient)


def test_dukascopy_fetch_bars(mocker: MockerFixture) -> None:
    # Mock requests.get
    mock_get = mocker.patch("app.services.brokers.dukascopy.requests.get")
    mock_response = mocker.MagicMock()

    # We must match the jsonp callback name to make removeprefix work
    def side_effect(
        url: str, headers: dict[str, str] | None, params: dict[str, Any]
    ) -> Any:
        jsonp = params["jsonp"]
        # Return standard OHLCV array: [[timestamp, open, high, low, close, volume]]
        mock_response.text = (
            f"{jsonp}([[1717200000000, 1.1000, 1.1010, 1.0990, 1.1005, 1000]]);"
        )
        return mock_response

    mock_get.side_effect = side_effect

    client = DukascopyClient()
    df = client.get_bars(symbol="EURUSD", timeframe="H1", count=1)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["Open"] == 1.1000
    assert df.iloc[0]["Volume"] == 1000
    mock_get.assert_called()


def test_dukascopy_fetch_ticks(mocker: MockerFixture) -> None:
    mock_get = mocker.patch("app.services.brokers.dukascopy.requests.get")
    mock_response = mocker.MagicMock()

    def side_effect(
        url: str, headers: dict[str, str] | None, params: dict[str, Any]
    ) -> Any:
        jsonp = params["jsonp"]
        # Return tick data: [[timestamp, bidPrice, askPrice, bidVolume, askVolume]]
        # In TICK mode, prices are scaled by 1,000,000 in scraper,
        # so we supply multiplied values
        mock_response.text = (
            f"{jsonp}([[1717200000000, 1.1000, 1.1010, 10000000, 10000000]]);"
        )
        return mock_response

    mock_get.side_effect = side_effect

    client = DukascopyClient()
    res = client.get_ticks(symbol="EURUSD", count=1, as_dataframe=False)

    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]["bid"] == 1.1000
    assert res[0]["ask"] == 1.1010
    mock_get.assert_called()


def test_dukascopy_get_bars_unsupported_timeframe() -> None:
    client = DukascopyClient()
    with pytest.raises(ValueError, match="Unsupported Dukascopy timeframe"):
        client.get_bars(symbol="EURUSD", timeframe="M10")


def test_dukascopy_fetch_exception_returns_empty(mocker: MockerFixture) -> None:
    mocker.patch(
        "app.services.brokers.dukascopy.requests.get",
        side_effect=Exception("Connection refused"),
    )
    client = DukascopyClient()
    df = client.get_bars(symbol="EURUSD", timeframe="H1", count=1)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
