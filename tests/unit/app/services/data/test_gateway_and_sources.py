"""Unit tests for gateway routing, fallbacks, licensing rules, and rate limits."""

import sqlite3
from datetime import UTC, datetime

import pandas as pd
import pytest
from app.services.data.gateway import (
    execute_gateway_request,
    get_data,
    get_source_adapter,
    get_symbol_metadata,
)
from app.services.data.validation import register_license
from app.utils.errors import ExternalServiceError, ValidationError
from app.utils.logger import logger
from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def clear_circuit_breakers() -> None:
    """Clear circuit breakers before each test to prevent cross-test contamination."""
    from app.services.data.storage import db_helper

    try:
        with db_helper.get_connection() as conn:
            conn.execute("DELETE FROM circuit_breakers;")
    except sqlite3.Error as e:
        logger.warning("Failed to clear circuit breakers: %s", e)


def test_source_adapter_registry() -> None:
    """Verify adapters are correctly registered and retrieveable."""
    csv_adapter = get_source_adapter("csv")
    assert csv_adapter is not None

    with pytest.raises(ValidationError):
        get_source_adapter("invalid_source_name")


def test_gateway_rate_limit_bucket() -> None:
    """Verify rate limiters trigger BACKPRESSURE_EXCEEDED when empty."""
    from app.services.data.gateway import RATE_LIMITERS

    limiter = RATE_LIMITERS["csv"]

    # Lock limiter tokens/rate to 0 to prevent time-based race conditions
    limiter.tokens = 0.0
    limiter.rate = 0.0

    # The next requests should raise BACKPRESSURE_EXCEEDED immediately
    with pytest.raises(ExternalServiceError) as ex:
        execute_gateway_request(
            source="csv",
            symbol="EURUSD",
            timeframe="M1",
            start_time=pytest.importorskip("pandas").to_datetime(
                "2026-06-01T00:00:00Z"
            ),
            end_time=pytest.importorskip("pandas").to_datetime("2026-06-01T01:00:00Z"),
            data_kind="ohlcv",
        )
    assert ex.value.code == "BACKPRESSURE_EXCEEDED"

    # Reset limiter capacity/rate back to standard
    limiter.rate = 100.0
    limiter.tokens = limiter.capacity


def test_gateway_licensing_restrictions() -> None:
    """Verify that redistribution restrictions fail closed in risk workflows."""
    # Register a redistribution-restricted license for Dukascopy
    register_license(
        source="dukascopy",
        symbol="EURUSD",
        license_type="Restricted",
        redistribution_restricted=True,
        attribution="Dukascopy",
    )

    # Valid in research mode
    res = get_symbol_metadata("EURUSD", "dukascopy")
    assert res["symbol"] == "EURUSD"

    # Fail closed in risk context
    with pytest.raises(ValidationError) as ex:
        execute_gateway_request(
            source="dukascopy",
            symbol="EURUSD",
            timeframe="M1",
            start_time=pytest.importorskip("pandas").to_datetime(
                "2026-06-01T00:00:00Z"
            ),
            end_time=pytest.importorskip("pandas").to_datetime("2026-06-01T01:00:00Z"),
            data_kind="ohlcv",
            workflow_context="risk",
        )
    # The message represents the 'LICENSE_RESTRICTION' constraint
    assert "LICENSE_RESTRICTION" in str(ex.value)


def test_gateway_fallback_sources(mocker: MockerFixture) -> None:
    """Test fallback logic when primary source fails."""
    mocker.patch(
        "app.services.data.gateway.DukascopyAdapter.get_market_data",
        side_effect=Exception("Dukascopy service offline"),
    )
    # Dukascopy is staging and throws service unavailable, fallback should try synthetic
    records = get_data(
        symbol="EURUSD",
        timeframe="M1",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T01:00:00Z",
        data_kind="ohlcv",
        source="dukascopy",
        fallback_sources=["synthetic"],
    )
    assert len(records) > 0
    assert records[0]["source"] == "synthetic"


def test_csv_adapter_retrieval() -> None:
    """Test retrieving and normalizing market data from CSV file."""
    csv_adapter = get_source_adapter("csv")
    start_time = pd.to_datetime("2025-01-02T00:00:00Z").to_pydatetime()
    end_time = pd.to_datetime("2025-01-02T01:00:00Z").to_pydatetime()

    records = csv_adapter.get_market_data("EURUSD", "H1", start_time, end_time)
    assert len(records) > 0
    assert records[0]["symbol"] == "EURUSD"
    assert records[0]["close"] == 1.03552
    assert records[0]["timestamp"].startswith("2025-01-02T00:00:00")


def test_parquet_adapter_retrieval() -> None:
    """Test retrieving and normalizing market data from Parquet file."""
    pq_adapter = get_source_adapter("parquet")
    start_time = pd.to_datetime("2025-01-02T00:00:00Z").to_pydatetime()
    end_time = pd.to_datetime("2025-01-02T01:00:00Z").to_pydatetime()

    records = pq_adapter.get_market_data("EURUSD", "H1", start_time, end_time)
    assert len(records) > 0
    assert records[0]["symbol"] == "EURUSD"
    assert records[0]["close"] == 1.03552
    assert records[0]["timestamp"].startswith("2025-01-02T00:00:00")


def test_file_adapters_discovery() -> None:
    """Test symbol listing and metadata for CSV and Parquet adapters."""
    csv_adapter = get_source_adapter("csv")
    pq_adapter = get_source_adapter("parquet")

    symbols_csv = csv_adapter.list_symbols()
    assert "EURUSD" in symbols_csv

    symbols_pq = pq_adapter.list_symbols()
    assert "EURUSD" in symbols_pq

    meta_csv = csv_adapter.get_symbol_metadata("EURUSD")
    assert meta_csv["source"] == "csv"

    meta_pq = pq_adapter.get_symbol_metadata("EURUSD")
    assert meta_pq["source"] == "parquet"

    now = datetime.now(UTC)
    assert csv_adapter.get_tick_data("EURUSD", now, now) == []
    assert pq_adapter.get_tick_data("EURUSD", now, now) == []


def test_normalize_file_records_std() -> None:
    """Test normalize_file_records helper using standard columns."""
    from app.services.data.gateway import normalize_file_records

    std_records = [
        {
            "timestamp": "2026-06-01T00:00:00Z",
            "open": 1.1,
            "high": 1.2,
            "low": 1.0,
            "close": 1.15,
            "volume": 100,
        }
    ]
    norm = normalize_file_records(std_records, "EURUSD", "H1", "csv")
    assert len(norm) == 1
    assert norm[0]["symbol"] == "EURUSD"
    assert norm[0]["tick_volume"] == 100


def test_gateway_mt5_adapter_direct_bars(mocker: MockerFixture) -> None:
    """Test MT5Adapter gateway methods under mock client conditions."""
    mock_client = mocker.MagicMock()
    mocker.patch("app.services.data.gateway.MT5Adapter.is_ready", return_value=True)
    mocker.patch("app.services.brokers.mt5.get_mt5_client", return_value=mock_client)
    mock_client.is_connected.return_value = True

    mock_client.get_bars.return_value = pd.DataFrame(
        [
            {
                "Timestamp": datetime(2026, 6, 1, tzinfo=UTC),
                "Open": 1.1,
                "High": 1.2,
                "Low": 1.0,
                "Close": 1.15,
                "Volume": 100.0,
                "Spread": 2.0,
            }
        ]
    )
    mock_client.get_ticks.return_value = pd.DataFrame(
        [
            {
                "time_msc": 1717200000000,
                "bid": 1.1,
                "ask": 1.1002,
                "last": 1.1001,
                "volume": 10.0,
            }
        ]
    )

    adapter = get_source_adapter("mt5")
    assert adapter.is_ready() is True
    assert adapter.list_symbols() == [
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "XAUUSD",
        "SPX500",
    ]

    meta = adapter.get_symbol_metadata("EURUSD")
    assert meta["source"] == "mt5"

    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    bars = adapter.get_market_data("EURUSD", "H1", start, end)
    assert len(bars) == 1
    assert bars[0]["close"] == 1.15

    ticks = adapter.get_tick_data("EURUSD", start, end)
    assert len(ticks) == 1
    assert ticks[0]["bid"] == 1.1


def test_gateway_ctrader_adapter_direct_bars(mocker: MockerFixture) -> None:
    """Test CTraderAdapter gateway methods under mock client conditions."""
    mock_client = mocker.MagicMock()
    mocker.patch(
        "app.services.brokers.ctrader.get_ctrader_client", return_value=mock_client
    )
    mock_client.is_connected.return_value = True

    mock_client.get_bars.return_value = pd.DataFrame(
        [
            {
                "Timestamp": datetime(2026, 6, 1, tzinfo=UTC),
                "Open": 1.1,
                "High": 1.2,
                "Low": 1.0,
                "Close": 1.15,
                "Volume": 100.0,
                "Spread": 2.0,
            }
        ]
    )
    mock_client.get_ticks.return_value = pd.DataFrame(
        [
            {
                "Timestamp": datetime(2026, 6, 1, tzinfo=UTC),
                "bid": 1.1,
                "ask": 1.1002,
                "last": 1.1001,
                "volume": 10.0,
                "spread": 0.0002,
            }
        ]
    )

    adapter = get_source_adapter("ctrader")
    assert adapter.is_ready() is True
    assert adapter.list_symbols() == ["EURUSD", "GBPUSD"]

    meta = adapter.get_symbol_metadata("EURUSD")
    assert meta["source"] == "ctrader"

    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    bars = adapter.get_market_data("EURUSD", "H1", start, end)
    assert len(bars) == 1

    ticks = adapter.get_tick_data("EURUSD", start, end)
    assert len(ticks) == 1


def test_gateway_dukascopy_adapter_direct_bars(mocker: MockerFixture) -> None:
    """Test DukascopyAdapter gateway methods under mock client conditions."""
    mock_client = mocker.MagicMock()
    mocker.patch(
        "app.services.brokers.dukascopy.get_dukascopy_client", return_value=mock_client
    )
    mock_client.is_connected.return_value = True

    mock_client.get_bars.return_value = pd.DataFrame(
        [
            {
                "Timestamp": datetime(2026, 6, 1, tzinfo=UTC),
                "Open": 1.1,
                "High": 1.2,
                "Low": 1.0,
                "Close": 1.15,
                "Volume": 100.0,
                "Spread": 2.0,
            }
        ]
    )
    mock_client.get_ticks.return_value = pd.DataFrame(
        [
            {
                "Timestamp": datetime(2026, 6, 1, tzinfo=UTC),
                "bid": 1.1,
                "ask": 1.1002,
                "last": 1.1001,
                "volume": 10.0,
                "spread": 0.0002,
            }
        ]
    )

    adapter = get_source_adapter("dukascopy")
    assert adapter.is_ready() is True
    assert adapter.list_symbols() == ["EURUSD", "GBPUSD", "USDJPY"]

    meta = adapter.get_symbol_metadata("EURUSD")
    assert meta["source"] == "dukascopy"

    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    bars = adapter.get_market_data("EURUSD", "H1", start, end)
    assert len(bars) == 1

    ticks = adapter.get_tick_data("EURUSD", start, end)
    assert len(ticks) == 1


def test_gateway_binance_adapter_direct_bars(mocker: MockerFixture) -> None:
    """Test BinanceAdapter gateway methods under mock client conditions."""
    mock_client = mocker.MagicMock()
    mocker.patch(
        "app.services.brokers.binance.get_binance_client", return_value=mock_client
    )
    mock_client.is_connected.return_value = True

    mock_client.get_bars.return_value = pd.DataFrame(
        [
            {
                "Timestamp": datetime(2026, 6, 1, tzinfo=UTC),
                "Open": 1.1,
                "High": 1.2,
                "Low": 1.0,
                "Close": 1.15,
                "Volume": 100.0,
                "Spread": 2.0,
            }
        ]
    )
    mock_client.get_ticks.return_value = pd.DataFrame(
        [
            {
                "Timestamp": datetime(2026, 6, 1, tzinfo=UTC),
                "bid": 1.1,
                "ask": 1.1002,
                "last": 1.1001,
                "volume": 10.0,
                "spread": 0.0002,
            }
        ]
    )

    adapter = get_source_adapter("binance")
    assert adapter.is_ready() is True
    assert adapter.list_symbols() == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    meta = adapter.get_symbol_metadata("BTCUSDT")
    assert meta["source"] == "binance"

    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    bars = adapter.get_market_data("BTCUSDT", "H1", start, end)
    assert len(bars) == 1

    ticks = adapter.get_tick_data("BTCUSDT", start, end)
    assert len(ticks) == 1


def test_gateway_yahoo_adapter_direct_bars(mocker: MockerFixture) -> None:
    """Test YahooAdapter gateway methods under mock client conditions."""
    mock_client = mocker.MagicMock()
    mocker.patch(
        "app.services.brokers.yahoo.get_yahoo_client", return_value=mock_client
    )
    mock_client.is_connected.return_value = True

    mock_client.get_bars.return_value = pd.DataFrame(
        [
            {
                "Timestamp": datetime(2026, 6, 1, tzinfo=UTC),
                "Open": 1.1,
                "High": 1.2,
                "Low": 1.0,
                "Close": 1.15,
                "Volume": 100.0,
                "Spread": 2.0,
            }
        ]
    )
    mock_client.get_ticks.return_value = pd.DataFrame(
        [
            {
                "Timestamp": datetime(2026, 6, 1, tzinfo=UTC),
                "bid": 1.1,
                "ask": 1.1002,
                "last": 1.1001,
                "volume": 10.0,
                "spread": 0.0002,
            }
        ]
    )

    adapter = get_source_adapter("yahoo")
    assert adapter.is_ready() is True
    assert adapter.list_symbols() == ["AAPL", "MSFT", "SPY"]

    meta = adapter.get_symbol_metadata("AAPL")
    assert meta["source"] == "yahoo"

    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    bars = adapter.get_market_data("AAPL", "H1", start, end)
    assert len(bars) == 1

    ticks = adapter.get_tick_data("AAPL", start, end)
    assert len(ticks) == 1


def test_mt5_adapter_gateway_errors(mocker: MockerFixture) -> None:
    """Test MT5Adapter error paths and empty results."""
    mocker.patch(
        "app.services.brokers.mt5.get_mt5_client", side_effect=RuntimeError("MT5 error")
    )
    adapter = get_source_adapter("mt5")
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)
    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_market_data("EURUSD", "H1", start, end)
    assert ex.value.code == "BROKER_UNAVAILABLE"

    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_tick_data("EURUSD", start, end)
    assert ex.value.code == "BROKER_UNAVAILABLE"

    mock_client = mocker.MagicMock()
    mocker.patch("app.services.brokers.mt5.get_mt5_client", return_value=mock_client)
    mock_client.is_connected.return_value = True
    mock_client.get_bars.return_value = pd.DataFrame()
    mock_client.get_ticks.return_value = pd.DataFrame()
    assert adapter.get_market_data("EURUSD", "H1", start, end) == []
    assert adapter.get_tick_data("EURUSD", start, end) == []


def test_ctrader_adapter_gateway_errors(mocker: MockerFixture) -> None:
    """Test CTraderAdapter error paths and empty results."""
    mocker.patch(
        "app.services.brokers.ctrader.get_ctrader_client",
        side_effect=RuntimeError("cTrader error"),
    )
    adapter = get_source_adapter("ctrader")
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)
    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_market_data("EURUSD", "H1", start, end)
    assert ex.value.code == "BROKER_UNAVAILABLE"

    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_tick_data("EURUSD", start, end)
    assert ex.value.code == "BROKER_UNAVAILABLE"

    mock_client = mocker.MagicMock()
    mocker.patch(
        "app.services.brokers.ctrader.get_ctrader_client", return_value=mock_client
    )
    mock_client.is_connected.return_value = True
    mock_client.get_bars.return_value = None
    mock_client.get_ticks.return_value = None
    assert adapter.get_market_data("EURUSD", "H1", start, end) == []
    assert adapter.get_tick_data("EURUSD", start, end) == []


def test_dukascopy_adapter_gateway_errors(mocker: MockerFixture) -> None:
    """Test DukascopyAdapter error paths and empty results."""
    mocker.patch(
        "app.services.brokers.dukascopy.get_dukascopy_client",
        side_effect=RuntimeError("Dukascopy error"),
    )
    adapter = get_source_adapter("dukascopy")
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)
    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_market_data("EURUSD", "H1", start, end)
    assert ex.value.code == "SERVICE_UNAVAILABLE"

    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_tick_data("EURUSD", start, end)
    assert ex.value.code == "SERVICE_UNAVAILABLE"

    mock_client = mocker.MagicMock()
    mocker.patch(
        "app.services.brokers.dukascopy.get_dukascopy_client", return_value=mock_client
    )
    mock_client.is_connected.return_value = True
    mock_client.get_bars.return_value = None
    mock_client.get_ticks.return_value = None
    assert adapter.get_market_data("EURUSD", "H1", start, end) == []
    assert adapter.get_tick_data("EURUSD", start, end) == []


def test_binance_adapter_gateway_errors(mocker: MockerFixture) -> None:
    """Test BinanceAdapter error paths and empty results."""
    mocker.patch(
        "app.services.brokers.binance.get_binance_client",
        side_effect=RuntimeError("Binance error"),
    )
    adapter = get_source_adapter("binance")
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)
    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_market_data("BTCUSDT", "H1", start, end)
    assert ex.value.code == "SERVICE_UNAVAILABLE"

    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_tick_data("BTCUSDT", start, end)
    assert ex.value.code == "SERVICE_UNAVAILABLE"

    mock_client = mocker.MagicMock()
    mocker.patch(
        "app.services.brokers.binance.get_binance_client", return_value=mock_client
    )
    mock_client.is_connected.return_value = True
    mock_client.get_bars.return_value = None
    mock_client.get_ticks.return_value = None
    assert adapter.get_market_data("BTCUSDT", "H1", start, end) == []
    assert adapter.get_tick_data("BTCUSDT", start, end) == []


def test_yahoo_adapter_gateway_errors(mocker: MockerFixture) -> None:
    """Test YahooAdapter error paths and empty results."""
    mocker.patch(
        "app.services.brokers.yahoo.get_yahoo_client",
        side_effect=RuntimeError("Yahoo error"),
    )
    adapter = get_source_adapter("yahoo")
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)
    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_market_data("AAPL", "H1", start, end)
    assert ex.value.code == "SERVICE_UNAVAILABLE"

    with pytest.raises(ExternalServiceError) as ex:
        adapter.get_tick_data("AAPL", start, end)
    assert ex.value.code == "SERVICE_UNAVAILABLE"

    mock_client = mocker.MagicMock()
    mocker.patch(
        "app.services.brokers.yahoo.get_yahoo_client", return_value=mock_client
    )
    mock_client.is_connected.return_value = True
    mock_client.get_bars.return_value = None
    mock_client.get_ticks.return_value = None
    assert adapter.get_market_data("AAPL", "H1", start, end) == []
    assert adapter.get_tick_data("AAPL", start, end) == []
