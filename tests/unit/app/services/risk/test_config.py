"""Unit tests for Risk configuration profile loading and ceiling validation."""

from __future__ import annotations

import json
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.risk.config import (
    MAX_DAILY_LOSS_PCT,
    MAX_EFFECTIVE_LEVERAGE,
    MAX_MARGIN_UTILIZATION_PCT,
    MAX_RISK_PER_TRADE,
    MAX_TOTAL_LOSS_PCT,
    load_risk_config,
)
from app.services.risk.models import DrawdownSubConfig, RiskConfig, RiskSubConfig
from app.utils.errors import ValidationError


def test_load_standard_profiles() -> None:
    """Test loading standard JSON configuration profiles successfully."""
    for profile in ("default", "prop_firm_default", "paper", "live_conservative"):
        config = load_risk_config(profile)
        assert isinstance(config, RiskConfig)
        assert config.profile_name == profile
        assert config.contract_hash() is not None


def test_reject_unknown_config_keys() -> None:
    """Test that profile with unknown keys raises ValidationError."""
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
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
            suffix=".json", delete=False, mode="w", encoding="utf-8"
        ) as f:
            json.dump(
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
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "live_unauthorized",
                "allow_live_execution": False,
            },
            f,
        )
        f_path = f.name

    # Rename tempfile so name contains "live"
    live_temp_path = Path(f_path).parent / "temp_live_profile.json"
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
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "default",
                "max_daily_loss_pct": 0.05,
            },
            f,
        )
        p1 = f.name

    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
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


def test_config_loader_and_registry() -> None:
    """Test RiskConfigLoader delegates and RiskProfileRegistry caching works."""
    from app.services.risk.config import (
        RiskConfigHash,
        RiskConfigLoader,
        _registry,
        hash_risk_config,
        validate_risk_config,
    )

    # Clean registry cache first
    _registry.clear()

    # Load via Loader
    config = RiskConfigLoader.load("default")
    assert isinstance(config, RiskConfig)

    # Caching verification
    cached = _registry.get("default")
    assert cached is config

    # Validate and Hash functions
    validate_risk_config(config)
    h = hash_risk_config(config)
    assert h == config.contract_hash()

    # RiskConfigHash instantiation
    cfg_hash_container = RiskConfigHash(
        profile_name="default",
        config_hash=h,
    )
    assert cfg_hash_container.profile_name == "default"
    assert cfg_hash_container.config_hash == h


def test_experimental_keys_rejection() -> None:
    """Test that unknown keys starting with experimental_ are accepted if False.

    Otherwise, they are rejected.
    """
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "experimental_ok",
                "experimental_new_limit": False,
            },
            f,
        )
        p_ok = f.name

    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "experimental_fail",
                "experimental_new_limit": True,
            },
            f,
        )
        p_fail = f.name

    try:
        # Should succeed
        cfg = load_risk_config(p_ok)
        assert cfg.profile_name == "experimental_ok"

        # Should fail
        with pytest.raises(ValidationError) as excinfo:
            load_risk_config(p_fail)
        assert "Unknown configuration keys found" in str(excinfo.value)
    finally:
        Path(p_ok).unlink()
        Path(p_fail).unlink()


def test_operator_approval_validation() -> None:
    """Test that live configs require complete operator approval fields."""
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "live_no_approval",
                "allow_live_execution": True,
            },
            f,
        )
        p_no_app = f.name

    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "live_bad_approval",
                "allow_live_execution": True,
                "operator_approval_fields": {"operator_id": "only_id"},
            },
            f,
        )
        p_bad_app = f.name

    try:
        with pytest.raises(ValidationError) as excinfo:
            load_risk_config(p_no_app)
        assert "requires explicit operator approval fields" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            load_risk_config(p_bad_app)
        assert "operator approval fields must contain keys" in str(excinfo.value)
    finally:
        Path(p_no_app).unlink()
        Path(p_bad_app).unlink()


def test_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that approved override keys work from environment, others reject."""
    from app.services.risk.config import _registry

    _registry.clear()
    # Whitelisted override key
    monkeypatch.setenv("HARUQUANT_RISK_CORRELATION_THRESHOLD", "0.65")
    # Non-whitelisted override key
    monkeypatch.setenv("HARUQUANT_RISK_PROFILE_NAME", "evil_override")

    try:
        # Should raise ValidationError due to profile_name override attempt
        with pytest.raises(ValidationError) as excinfo:
            load_risk_config("default")
        assert "Environment override not allowed for key: profile_name" in str(
            excinfo.value
        )
    finally:
        monkeypatch.delenv("HARUQUANT_RISK_PROFILE_NAME")

    _registry.clear()
    # Now load with only approved override
    monkeypatch.setenv("HARUQUANT_RISK_MAX_RISK_PER_TRADE", "0.08")
    monkeypatch.setenv("HARUQUANT_RISK_ALLOW_LIVE_EXECUTION", "true")  # non-whitelisted

    try:
        with pytest.raises(ValidationError) as excinfo:
            load_risk_config("default")
        assert "Environment override not allowed for key: allow_live_execution" in str(
            excinfo.value
        )
    finally:
        monkeypatch.delenv("HARUQUANT_RISK_ALLOW_LIVE_EXECUTION")

    # Clear registry to avoid cache hit
    from app.services.risk.config import _registry

    _registry.clear()

    # Load with only approved overrides
    config = load_risk_config("default")
    assert config.correlation_threshold == Decimal("0.65")
    assert config.max_risk_per_trade == Decimal("0.08")


def test_governed_compatibility_stale_token() -> None:
    """Test that stale tokens are allowed if compatible config hashes are present."""
    from datetime import timedelta

    from app.services.risk.models import RiskApprovalToken
    from app.services.risk.policy import validate_override_token
    from app.utils.normalization import utc_now

    now = utc_now()
    token = RiskApprovalToken(
        token_id="tok_stale",
        request_id="req_stale",
        workflow_id="wf_stale",
        approved_action="trade",
        approver="admin",
        expiry_time=now + timedelta(hours=1),
        config_hash="old_hash",
        decision_hash="dec_hash",
        scope={"compatible_config_hashes": ["new_hash"]},
        nonce="nonce123",
        signature="signature",
    )

    # Matching old_hash -> compatible
    assert (
        validate_override_token(
            token=token, expected_scope={}, active_config_hash="old_hash"
        )
        is True
    )

    # Active is new_hash -> compatible via compatible_config_hashes list override
    assert (
        validate_override_token(
            token=token, expected_scope={}, active_config_hash="new_hash"
        )
        is True
    )

    # Active is other_hash -> incompatible (not in list)
    assert (
        validate_override_token(
            token=token, expected_scope={}, active_config_hash="other_hash"
        )
        is False
    )


def test_nested_config_synchronization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test bi-directional synchronization and overrides for nested/flat fields."""
    # 1. Loading with only flat keys (simulates legacy config)
    cfg_flat = RiskConfig(
        profile_name="flat_only",
        max_risk_per_trade=Decimal("0.02"),
        max_margin_utilization_pct=Decimal("0.55"),
        max_daily_loss_pct=Decimal("0.06"),
        max_total_loss_pct=Decimal("0.11"),
        correlation_threshold=Decimal("0.65"),
        var_confidence=Decimal("0.99"),
        es_confidence=Decimal("0.98"),
        max_stress_loss_pct=Decimal("0.12"),
        m1_spread_to_sigma_ratio_filter=Decimal("1.8"),
    )
    assert cfg_flat.risk.max_risk_per_trade == Decimal("0.02")
    assert cfg_flat.risk.max_margin_usage == Decimal("0.55")
    assert cfg_flat.drawdown.daily_loss_hard_limit == Decimal("0.06")
    assert cfg_flat.drawdown.total_drawdown_hard_limit == Decimal("0.11")
    assert cfg_flat.correlation.reject_threshold == Decimal("0.65")
    assert cfg_flat.tail_risk.var_confidence == Decimal("0.99")
    assert cfg_flat.tail_risk.es_confidence == Decimal("0.98")
    assert cfg_flat.tail_risk.stress_loss_limit == Decimal("0.12")
    assert cfg_flat.execution.max_spread_to_sigma == Decimal("1.8")

    # 2. Loading with nested keys taking precedence
    cfg_nested = RiskConfig(
        profile_name="nested_only",
        risk=RiskSubConfig(
            max_risk_per_trade=Decimal("0.0035"),
            max_margin_usage=Decimal("0.40"),
        ),
        drawdown=DrawdownSubConfig(daily_loss_hard_limit=Decimal("0.03")),
    )
    assert cfg_nested.max_risk_per_trade == Decimal("0.0035")
    assert cfg_nested.max_margin_utilization_pct == Decimal("0.40")
    assert cfg_nested.max_daily_loss_pct == Decimal("0.03")

    # 3. Environment override on flat keys overrides nested too
    from app.services.risk.config import _registry, load_risk_config

    _registry.clear()
    monkeypatch.setenv("HARUQUANT_RISK_MAX_RISK_PER_TRADE", "0.008")

    try:
        config = load_risk_config("default")
        assert config.max_risk_per_trade == Decimal("0.008")
        assert config.risk.max_risk_per_trade == Decimal("0.008")
    finally:
        monkeypatch.delenv("HARUQUANT_RISK_MAX_RISK_PER_TRADE")


def test_live_profile_ceilings_and_approvals() -> None:
    """Test that live profiles enforce prop-firm ceilings and owner approvals."""
    # 1. Reject live profile daily loss > 4%
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "temp_live_high_daily",
                "allow_live_execution": True,
                "max_daily_loss_pct": 0.05,
                "operator_approval_fields": {
                    "operator_id": "admin",
                    "approved_at": "2026-06-19T12:00:00Z",
                    "approval_token": "token123",
                },
            },
            f,
        )
        p_high_daily = f.name

    # 2. Reject live profile total loss > 8%
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "temp_live_high_total",
                "allow_live_execution": True,
                "max_total_loss_pct": 0.09,
                "operator_approval_fields": {
                    "operator_id": "admin",
                    "approved_at": "2026-06-19T12:00:00Z",
                    "approval_token": "token123",
                },
            },
            f,
        )
        p_high_total = f.name

    # 3. Reject live profile exceeding conservative defaults
    # without owner/admin approval
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "temp_live_high_risk_compliance",
                "allow_live_execution": True,
                "max_risk_per_trade": 0.003,
                "operator_approval_fields": {
                    "operator_id": "admin_compliance",
                    "approved_at": "2026-06-19T12:00:00Z",
                    "approval_token": "token123",
                },
            },
            f,
        )
        p_high_risk_bad_op = f.name

    # 4. Accept live profile exceeding conservative defaults with owner/admin approval
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "profile_name": "temp_live_high_risk_owner",
                "allow_live_execution": True,
                "max_risk_per_trade": 0.003,
                "operator_approval_fields": {
                    "operator_id": "owner",
                    "approved_at": "2026-06-19T12:00:00Z",
                    "approval_token": "token123",
                },
            },
            f,
        )
        p_high_risk_ok = f.name

    try:
        # Check daily loss limit breach
        with pytest.raises(ValidationError) as excinfo:
            load_risk_config(p_high_daily)
        assert "exceeds external prop-firm ceiling" in str(excinfo.value)

        # Check total loss limit breach
        with pytest.raises(ValidationError) as excinfo:
            load_risk_config(p_high_total)
        assert "exceeds external prop-firm ceiling" in str(excinfo.value)

        # Check operator role validation for increased risk thresholds
        with pytest.raises(ValidationError) as excinfo:
            load_risk_config(p_high_risk_bad_op)
        assert "requires explicit owner/admin approval" in str(excinfo.value)

        # Accept owner approval
        cfg = load_risk_config(p_high_risk_ok)
        assert cfg.max_risk_per_trade == Decimal("0.003")
    finally:
        Path(p_high_daily).unlink()
        Path(p_high_total).unlink()
        Path(p_high_risk_bad_op).unlink()
        Path(p_high_risk_ok).unlink()
