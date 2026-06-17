"""Unit tests for the strategy quality scorecard evaluator in Analytics."""

from __future__ import annotations

from typing import Any

import pytest
from app.services.analytics.scorecard import evaluate_strategy_quality
from app.utils.errors import ValidationError


@pytest.fixture
def mock_good_report() -> dict[str, Any]:
    return {
        "sections": {
            "trade_metrics": {
                "win_rate": 0.60,
                "total_trades": 120,
            },
            "ratio_metrics": {
                "profit_factor": 1.8,
                "sharpe_ratio": 1.6,
            },
            "drawdown_metrics": {
                "max_drawdown_percent": 8.0,
            },
        }
    }


@pytest.fixture
def mock_medium_report() -> dict[str, Any]:
    return {
        "sections": {
            "trade_metrics": {
                "win_rate": 0.50,
                "total_trades": 80,
            },
            "ratio_metrics": {
                "profit_factor": 1.1,
                "sharpe_ratio": 0.8,
            },
            "drawdown_metrics": {
                "max_drawdown_percent": 15.0,
            },
        }
    }


@pytest.fixture
def mock_poor_report() -> dict[str, Any]:
    return {
        "sections": {
            "trade_metrics": {
                "win_rate": 0.40,
                "total_trades": 30,
            },
            "ratio_metrics": {
                "profit_factor": 0.9,
                "sharpe_ratio": 0.4,
            },
            "drawdown_metrics": {
                "max_drawdown_percent": 30.0,
            },
        }
    }


def test_scorecard_evaluation_good(mock_good_report):
    resp = evaluate_strategy_quality(mock_good_report, request_id="req_test")
    assert resp["status"] == "success"
    data = resp["data"]
    assert data["score"] == 100.0
    assert len(data["strengths"]) >= 4
    assert len(data["warnings"]) == 0
    assert "Promote to paper trading" in data["recommended_action"]


def test_scorecard_evaluation_medium(mock_medium_report):
    resp = evaluate_strategy_quality(mock_medium_report, request_id="req_test")
    assert resp["status"] == "success"
    data = resp["data"]
    assert 50.0 <= data["score"] < 80.0
    assert "adjust sizing down" in data["recommended_action"]


def test_scorecard_evaluation_poor(mock_poor_report):
    resp = evaluate_strategy_quality(mock_poor_report, request_id="req_test")
    assert resp["status"] == "success"
    data = resp["data"]
    assert data["score"] < 50.0
    assert len(data["warnings"]) >= 4
    assert "Reject" in data["recommended_action"]


def test_scorecard_validation_errors():
    # Invalid request_id raises ValidationError
    with pytest.raises(ValidationError):
        evaluate_strategy_quality(None, request_id=" ")

    # Invalid report returns error response envelope
    resp = evaluate_strategy_quality(None, request_id="req_test")
    assert resp["status"] == "error"
    assert resp["error"]["code"] == "VALIDATION_FAILED"
