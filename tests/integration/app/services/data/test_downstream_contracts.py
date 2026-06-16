"""Integration tests checking contract stability for downstream engines."""

import agentic.tools.data as data_service


def test_downstream_simulation_loop_compatibility() -> None:
    """Verify simulation loop compatibility with data fetch, resample, and label."""
    # 1. Fetch synthetic market data (high compatibility)
    res = data_service.get_market_data(
        symbol="EURUSD",
        timeframe="M5",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T02:00:00Z",
        source="synthetic",
    )
    assert res["status"] == "success"
    records = res["data"]
    assert len(records) > 0

    # 2. Resample data
    resample_res = data_service.resample_ohlcv(
        records=records,
        source_timeframe="M5",
        target_timeframe="M15",
    )
    assert resample_res["status"] == "success"
    resampled = resample_res["data"]
    assert len(resampled) > 0

    # 3. Label data
    label_res = data_service.label_market_data(
        records=resampled,
        method="fixed_horizon",
        horizon=1,
    )
    assert label_res["status"] == "success"
    labeled = label_res["data"]
    assert len(labeled) > 0
    assert "label" in labeled[0]
