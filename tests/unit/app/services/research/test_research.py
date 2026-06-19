# ruff: noqa: E501, NPY002
"""Unit tests for Research Edge Lab.

Covers data prep, technical features, data leakage checks, metrics calculators,
edge discovery studies, null models, structure studies, unsupervised learning, and reporting.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from app.services.research.data import (
    PreparedDataset,
    enrich_dataset,
    prepare_research_dataset,
    validate_dataset,
)
from app.services.research.features import (
    active_sessions_for_hour,
    adr,
    atr,
    atr_percent,
    bb_percent_b,
    bb_width,
    bollinger_bands,
    build_market_regime_feature_frame,
    detect_market_regime,
    detect_trend_regime,
    detect_volatility_regime,
    donchian_channel,
    forward_max_adverse_excursion,
    forward_max_favorable_excursion,
    forward_returns,
    hurst_exponent,
    log_returns,
    momentum,
    percent_rank,
    pivot_points,
    rate_of_change,
    rolling_hurst,
    rolling_percentile_rank,
    rsi,
    session_label_for_hour,
    simple_returns,
    zscore,
)
from app.services.research.helpers import (
    ResearchResourceLimits,
    check_sample_size,
    create_news_blackout_windows,
    parse_calendar_events,
)
from app.services.research.leakage import (
    dump_masked_research_json,
    enforce_time_split,
    mask_forward_columns,
    mask_research_artifact,
    validate_no_lookahead_features,
)
from app.services.research.metrics import (
    MetricContext,
    build_default_registry,
)
from app.services.research.reporting import (
    build_dashboard_summary,
    build_edge_profile_snapshot,
    build_profile_summary,
    result_to_markdown,
    result_to_summary,
    save_json,
    save_markdown,
)
from app.services.research.studies.eds import (
    run_eds_mean_reversion,
    run_eds_null_baseline,
    run_eds_trend_persistence,
)
from app.services.research.studies.null_models import (
    benjamini_hochberg,
    block_bootstrap_ci,
    block_bootstrap_distribution,
    holm_bonferroni,
    permutation_test,
)
from app.services.research.studies.structure import (
    build_calibration_grid,
    build_strategy_fit,
    detect_swing_points,
    evaluate_calibration_candidates,
)
from app.services.research.studies.unsupervised import (
    attach_cluster_labels,
    cluster_feature_space,
    identify_pca_risk_factors,
    run_pca,
)
from app.utils.errors import ValidationError
from app.utils.settings import EdgeLabConfig


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Generate a clean sample OHLCV DataFrame for testing."""
    dates = pd.date_range(start="2026-01-01", periods=100, freq="h")
    np.random.seed(42)
    close_prices = 100.0 + np.cumsum(np.random.normal(0, 0.5, 100))
    df = pd.DataFrame(
        {
            "open": close_prices - 0.2,
            "high": close_prices + 0.5,
            "low": close_prices - 0.6,
            "close": close_prices,
            "volume": np.random.randint(100, 1000, 100).astype(float),
            "spread": np.random.uniform(1.0, 5.0, 100),
        },
        index=dates,
    )
    return df


# --- 1. Data Prep and Validation Tests ---
def test_validate_dataset_valid(sample_ohlcv_data: pd.DataFrame) -> None:
    report = validate_dataset(sample_ohlcv_data)
    assert not any(i.severity == "error" for i in report.issues)


def test_validate_dataset_missing_columns() -> None:
    df = pd.DataFrame({"open": [1.0], "close": [1.1]})
    with pytest.raises(ValidationError):
        validate_dataset(df)


def test_validate_dataset_non_monotonic() -> None:
    dates = [
        pd.Timestamp("2026-01-02"),
        pd.Timestamp("2026-01-01"),
    ]
    df = pd.DataFrame(
        {"open": [1, 2], "high": [3, 4], "low": [0, 1], "close": [2, 3]},
        index=dates,
    )
    with pytest.raises(ValidationError):
        validate_dataset(df)


def test_prepare_research_dataset(sample_ohlcv_data: pd.DataFrame) -> None:
    config = EdgeLabConfig()
    dataset = prepare_research_dataset(sample_ohlcv_data, config)
    assert isinstance(dataset, PreparedDataset)
    assert "returns" in dataset.data.columns
    assert "log_returns" in dataset.data.columns
    assert "candle_body" in dataset.data.columns


# --- 2. Feature Extraction Tests ---
def test_technical_features(sample_ohlcv_data: pd.DataFrame) -> None:
    close = sample_ohlcv_data["close"]
    high = sample_ohlcv_data["high"]
    low = sample_ohlcv_data["low"]

    assert len(log_returns(close)) == len(close)
    assert len(simple_returns(close)) == len(close)
    assert len(zscore(close, 10)) == len(close)
    assert len(percent_rank(close, 10)) == len(close)
    assert len(rolling_percentile_rank(close, 10)) == len(close)
    assert len(atr(high, low, close, 10)) == len(close)
    assert len(atr_percent(high, low, close, 10)) == len(close)

    upper, middle, lower = bollinger_bands(close, 10)
    assert len(upper) == len(close)
    assert len(middle) == len(close)
    assert len(lower) == len(close)

    assert len(bb_width(close, 10)) == len(close)
    assert len(bb_percent_b(close, 10)) == len(close)
    assert len(rsi(close, 10)) == len(close)
    assert len(rate_of_change(close, 10)) == len(close)
    assert len(momentum(close, 10)) == len(close)

    up, dn = donchian_channel(high, low, 10)
    assert len(up) == len(close)
    assert len(dn) == len(close)

    assert 0.0 <= hurst_exponent(close) <= 1.0
    assert len(rolling_hurst(close, 60)) == len(close)

    pivots = pivot_points(high, low, close)
    assert "pivot" in pivots
    assert len(pivots["pivot"]) == len(close)

    assert len(adr(high, low, 10)) == len(close)


def test_forward_features(sample_ohlcv_data: pd.DataFrame) -> None:
    close = sample_ohlcv_data["close"]
    high = sample_ohlcv_data["high"]
    low = sample_ohlcv_data["low"]

    fwd_ret = forward_returns(close, 5)
    assert fwd_ret.name == "research_forward_returns"
    assert len(fwd_ret) == len(close)

    mfe = forward_max_favorable_excursion(close, high, 5)
    assert mfe.name == "research_mfe"
    assert len(mfe) == len(close)

    mae = forward_max_adverse_excursion(close, low, 5)
    assert mae.name == "research_mae"
    assert len(mae) == len(close)


def test_regime_features(sample_ohlcv_data: pd.DataFrame) -> None:
    vol_reg = detect_volatility_regime(sample_ohlcv_data, 10)
    assert len(vol_reg) == len(sample_ohlcv_data)

    trend_reg = detect_trend_regime(sample_ohlcv_data, 10, 20)
    assert len(trend_reg) == len(sample_ohlcv_data)

    ff = build_market_regime_feature_frame(sample_ohlcv_data)
    assert not ff.empty

    reg = detect_market_regime(sample_ohlcv_data)
    assert len(reg) == len(sample_ohlcv_data)


def test_sessions() -> None:
    assert "London" in active_sessions_for_hour(10)
    assert "NewYork" in active_sessions_for_hour(14)
    assert "Tokyo" in active_sessions_for_hour(2)
    assert session_label_for_hour(23) == "Asian_Quiet"


# --- 3. Data Leakage and Splits Tests ---
def test_leakage_checks(sample_ohlcv_data: pd.DataFrame) -> None:
    df = sample_ohlcv_data.copy()
    df["research_fwd_ret"] = 0.05
    report = validate_no_lookahead_features(df)
    assert report.severity == "critical"
    assert "research_fwd_ret" in report.suspected_columns

    masked_df = mask_forward_columns(df, report)
    assert "research_fwd_ret" not in masked_df.columns


def test_time_split(sample_ohlcv_data: pd.DataFrame) -> None:
    res = enforce_time_split(sample_ohlcv_data, 0.6, 0.2, 0.2)
    assert res.train_records == 60
    assert res.val_records == 20
    assert res.test_records == 20
    assert len(res.train_df) == 60
    assert len(res.val_df) == 20
    assert len(res.test_df) == 20


def test_mask_research_artifact() -> None:
    art = {"secret_key": "123456", "data": "clean"}
    masked = mask_research_artifact(art)
    assert masked["secret_key"] == "[REDACTED]"
    assert masked["data"] == "clean"

    json_str = dump_masked_research_json(art)
    assert "[REDACTED]" in json_str


# --- 4. Metric Calculator Tests ---
def test_metric_registry(sample_ohlcv_data: pd.DataFrame) -> None:
    df = enrich_dataset(sample_ohlcv_data)
    context = MetricContext(df, EdgeLabConfig())
    registry = build_default_registry()
    results = registry.calculate_all(context)
    assert "volatility" in results
    assert "returns" in results
    assert results["volatility"].value > 0.0


# --- 5. Edge Discovery Studies Tests ---
def test_eds_studies(sample_ohlcv_data: pd.DataFrame) -> None:
    config = EdgeLabConfig()
    dataset = prepare_research_dataset(sample_ohlcv_data, config)

    baseline = run_eds_null_baseline(dataset, config)
    assert baseline["study"] == "null_baseline"
    assert baseline["sample_size"] == 100

    mr_res = run_eds_mean_reversion(dataset, config)
    assert mr_res.study_name == "mean_reversion_fade"

    tp_res = run_eds_trend_persistence(dataset, config)
    assert tp_res.study_name == "trend_persistence_breakout"


# --- 6. Null Models Tests ---
def test_null_models() -> None:
    data = np.random.normal(0, 0.1, 100)
    low, high = block_bootstrap_ci(data, n_iterations=100, block_size=5)
    assert low < high

    dist = block_bootstrap_distribution(data, n_iterations=100, block_size=5)
    assert len(dist) == 100

    p_val = permutation_test(data, data + 0.1, n_permutations=100)
    assert 0.0 <= p_val <= 1.0

    p_vals = [0.01, 0.04, 0.15, 0.80]
    bh = benjamini_hochberg(p_vals)
    assert bh[0] is True
    assert bh[3] is False

    hb = holm_bonferroni(p_vals)
    assert hb[0] is True
    assert hb[3] is False


# --- 7. Structure Studies Tests ---
def test_structure_studies(sample_ohlcv_data: pd.DataFrame) -> None:
    swings = detect_swing_points(sample_ohlcv_data, 5)
    assert isinstance(swings, list)

    grid = build_calibration_grid([3, 5], [0.5, 0.6])
    assert len(grid) == 4

    evaluated = evaluate_calibration_candidates(sample_ohlcv_data, grid)
    assert len(evaluated) == 4

    fit = build_strategy_fit(sample_ohlcv_data)
    assert fit["status"] == "advisory_only"


# --- 8. Unsupervised Tests ---
def test_unsupervised(sample_ohlcv_data: pd.DataFrame) -> None:
    df = build_market_regime_feature_frame(sample_ohlcv_data)
    try:
        import sklearn  # noqa: F401

        has_sklearn = True
    except ImportError:
        has_sklearn = False

    if has_sklearn:
        pca_res = run_pca(df, 2)
        assert "explained_variance" in pca_res

        cluster_res = cluster_feature_space(df, 3)
        assert "labels" in cluster_res

        labeled_df = attach_cluster_labels(df, cluster_res["labels"])
        assert "cluster" in labeled_df.columns

        factors = identify_pca_risk_factors(pca_res, pca_res["columns"])
        assert len(factors) == 2
    else:
        with pytest.raises(ValidationError):
            run_pca(df, 2)
        with pytest.raises(ValidationError):
            cluster_feature_space(df, 3)


# --- 9. Reporting Tests ---
def test_reporting(sample_ohlcv_data: pd.DataFrame, tmp_path: Path) -> None:
    config = EdgeLabConfig()
    dataset = prepare_research_dataset(sample_ohlcv_data, config)
    res = run_eds_mean_reversion(dataset, config)

    md = result_to_markdown(res)
    assert "# Edge Discovery Report" in md

    summary = result_to_summary(res)
    assert summary["study_name"] == "mean_reversion_fade"

    # Save to temp files
    md_file = tmp_path / "report.md"
    json_file = tmp_path / "report.json"

    assert save_markdown(res, str(md_file)) is True
    assert save_json(res, str(json_file)) is True

    snapshot = build_edge_profile_snapshot("EURUSD", "H1", [res])
    assert snapshot["symbol"] == "EURUSD"

    summary_profile = build_profile_summary(snapshot)
    assert summary_profile["symbol"] == "EURUSD"

    dash_summary = build_dashboard_summary(snapshot)
    assert dash_summary["ui_display_type"] == "research_profile"


# --- 10. Helpers Tests ---
def test_helpers() -> None:
    events = [
        {
            "title": "Non-Farm Payrolls",
            "currency": "USD",
            "impact": "high",
            "time": "2026-06-19T13:30:00Z",
        },
        {
            "title": "Low Impact Event",
            "currency": "USD",
            "impact": "low",
            "time": "2026-06-19T14:30:00Z",
        },
    ]
    parsed = parse_calendar_events(events)
    assert len(parsed) == 2

    blackout = create_news_blackout_windows(parsed)
    assert len(blackout) == 1

    assert check_sample_size(50, 30) is True

    # Resource check
    lims = ResearchResourceLimits(max_rows=100)
    with pytest.raises(ValidationError):
        lims.check_limits(150)
