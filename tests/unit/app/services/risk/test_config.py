"""Unit tests for Risk configuration profile loading and ceiling validation."""

from __future__ import annotations

import tempfile
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from app.services.risk.config import (
    MAX_DAILY_LOSS_PCT,
    MAX_EFFECTIVE_LEVERAGE,
    MAX_MARGIN_UTILIZATION_PCT,
    MAX_RISK_PER_TRADE,
    MAX_TOTAL_LOSS_PCT,
    load_risk_config,
)
from app.services.risk.models import RiskConfig
from app.utils.errors import ValidationError


def test_load_standard_profiles() -> None:
    """Test loading standard YAML configuration profiles successfully."""
    for profile in ("default", "prop_firm_default", "paper", "live_conservative"):
        config = load_risk_config(profile)
        assert isinstance(config, RiskConfig)
        assert config.profile_name == profile
        assert config.contract_hash() is not None


def test_reject_unknown_config_keys() -> None:
    """Test that profile with unknown keys raises ValidationError."""
    with tempfile.NamedTemporaryFile(
        suffix=".yaml", delete=False, mode="w", encoding="utf-8"
    ) as f:
        yaml.dump(
            {
                "profile_name": "unknown_keys",
                "max_daily_loss_pct": 0.05,
                "some_invalid_key": 42,
            },
            f,
        )
        f_path = f.name

    try:
        with pytest.raises(ValidationError) as excinfo:
            load_risk_config(f_path)
        assert "Unknown configuration keys found" in str(excinfo.value)
    finally:
        Path(f_path).unlink()


def test_reject_unsafe_ceilings() -> None:
    """Test that limits exceeding hard ceilings are rejected."""

    def _test_unsafe_key(key: str, val: float) -> None:
        with tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False, mode="w", encoding="utf-8"
        ) as f:
            yaml.dump(
                {
                    "profile_name": "unsafe_ceiling",
                    key: val,
                },
                f,
            )
            f_path = f.name

        try:
            with pytest.raises(ValidationError) as excinfo:
                load_risk_config(f_path)
            assert "Unsafe config" in str(excinfo.value)
        finally:
            Path(f_path).unlink()

    _test_unsafe_key("max_daily_loss_pct", float(MAX_DAILY_LOSS_PCT + Decimal("0.01")))
    _test_unsafe_key("max_total_loss_pct", float(MAX_TOTAL_LOSS_PCT + Decimal("0.01")))
    _test_unsafe_key(
        "max_margin_utilization_pct",
        float(MAX_MARGIN_UTILIZATION_PCT + Decimal("0.01")),
    )
    _test_unsafe_key("max_effective_leverage", float(MAX_EFFECTIVE_LEVERAGE + 1))
    _test_unsafe_key("max_risk_per_trade", float(MAX_RISK_PER_TRADE + Decimal("0.01")))


def test_reject_live_without_authority() -> None:
    """Test that live profile name requires allow_live_execution=true."""
    with tempfile.NamedTemporaryFile(
        suffix=".yaml", delete=False, mode="w", encoding="utf-8"
    ) as f:
        yaml.dump(
            {
                "profile_name": "live_unauthorized",
                "allow_live_execution": False,
            },
            f,
        )
        f_path = f.name

    # Rename tempfile so name contains "live"
    live_temp_path = Path(f_path).parent / "temp_live_profile.yaml"
    Path(f_path).rename(live_temp_path)

    try:
        with pytest.raises(ValidationError) as excinfo:
            load_risk_config(str(live_temp_path))
        assert "must explicitly set allow_live_execution to true" in str(excinfo.value)
    finally:
        if live_temp_path.exists():
            live_temp_path.unlink()


def test_config_hash_stability() -> None:
    """Test that configuration hashes are stable and reproduce correctly."""
    c1 = load_risk_config("default")
    c2 = load_risk_config("default")
    assert c1.contract_hash() == c2.contract_hash()

    # Changing a value should yield a different hash
    with tempfile.NamedTemporaryFile(
        suffix=".yaml", delete=False, mode="w", encoding="utf-8"
    ) as f:
        yaml.dump(
            {
                "profile_name": "default",
                "max_daily_loss_pct": 0.05,
            },
            f,
        )
        p1 = f.name

    with tempfile.NamedTemporaryFile(
        suffix=".yaml", delete=False, mode="w", encoding="utf-8"
    ) as f:
        yaml.dump(
            {
                "profile_name": "default",
                "max_daily_loss_pct": 0.06,
            },
            f,
        )
        p2 = f.name

    try:
        config1 = load_risk_config(p1)
        config2 = load_risk_config(p2)
        assert config1.contract_hash() != config2.contract_hash()
    finally:
        Path(p1).unlink()
        Path(p2).unlink()
