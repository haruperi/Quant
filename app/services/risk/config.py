"""Risk configuration loaders and validation.

Responsible for loading JSON config profiles, validating against hard ceilings,
computing stable hashes, and enforcing live execution authorization checks.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import Field

from app.services.risk.models import RiskConfig, RiskContract
from app.utils.errors import ValidationError
from app.utils.logger import logger

# Hard ceiling constraints
MAX_DAILY_LOSS_PCT = Decimal("0.20")
MAX_TOTAL_LOSS_PCT = Decimal("0.50")
MAX_MARGIN_UTILIZATION_PCT = Decimal("1.00")
MAX_EFFECTIVE_LEVERAGE = Decimal("500.0")
MAX_RISK_PER_TRADE = Decimal("0.10")
MAX_STRESS_LOSS_PCT = Decimal("0.30")

CONSERVATIVE_DEFAULTS = {
    "max_risk_per_trade": Decimal("0.002"),
    "max_daily_loss_pct": Decimal("0.02"),
    "max_total_loss_pct": Decimal("0.05"),
    "max_margin_utilization_pct": Decimal("0.50"),
    "max_effective_leverage": Decimal("5.0"),
    "max_stress_loss_pct": Decimal("0.08"),
}

CONFIGS_DIR = Path(__file__).resolve().parent / "configs"

# Whitelisted keys that can be overridden via environment variables
APPROVED_OVERRIDE_KEYS = {
    "correlation_threshold",
    "max_risk_per_trade",
    "var_confidence",
    "es_confidence",
    "max_daily_loss_pct",
    "max_total_loss_pct",
    "max_margin_utilization_pct",
    "max_effective_leverage",
}


class RiskConfigHash(RiskContract):
    """Container for a stable configuration profile hash."""

    profile_name: str = Field(..., description="Name of the risk profile.")
    config_hash: str = Field(..., description="Stable SHA256 configuration hash.")


class RiskProfileRegistry:
    """Registry of loaded risk configuration profiles."""

    def __init__(self) -> None:
        self._profiles: dict[str, RiskConfig] = {}

    def register(self, profile_name: str, config: RiskConfig) -> None:
        """Register a profile in the registry."""
        self._profiles[profile_name] = config

    def get(self, profile_name: str) -> RiskConfig | None:
        """Get a registered profile by name."""
        return self._profiles.get(profile_name)

    def clear(self) -> None:
        """Clear all registered profiles."""
        self._profiles.clear()


# Global registry instance
_registry = RiskProfileRegistry()


class RiskConfigLoader:
    """Loader utility for parsing and caching risk configurations."""

    @staticmethod
    def load(profile_name: str) -> RiskConfig:
        """Load configuration profile by name."""
        return load_risk_config(profile_name)

    @staticmethod
    def validate(config: RiskConfig) -> None:
        """Validate configuration object."""
        validate_risk_config(config)


def validate_risk_config(config: RiskConfig) -> None:
    """Validate a loaded RiskConfig object against strict ceilings.

    Also verifies authorization rules.
    """
    raw_dict = config.model_dump()
    _validate_ceilings(raw_dict)
    _validate_live_profile(config.profile_name, raw_dict)


def hash_risk_config(config: RiskConfig) -> str:
    """Compute a stable, deterministic hash for a given RiskConfig profile."""
    return config.contract_hash()


def _read_json_file(file_path: Path) -> dict[str, Any]:
    """Read and parse dictionary content from JSON file."""
    try:
        with file_path.open(encoding="utf-8") as f:
            raw_dict = json.load(f)
    except Exception as e:
        msg = f"Failed to parse JSON config from {file_path}: {e}"
        logger.error(msg)
        raise ValidationError(msg) from e

    if not isinstance(raw_dict, dict):
        msg = f"Configuration content in {file_path} must be a dictionary."
        logger.error(msg)
        raise ValidationError(msg)
    return raw_dict


def _validate_ceiling(raw_dict: dict[str, Any], key: str, ceiling: Decimal) -> None:
    """Validate specific configuration value against a hard ceiling."""
    val = raw_dict.get(key)
    if val is not None:
        try:
            dec_val = Decimal(str(val))
        except Exception as e:
            msg = f"Invalid decimal value for '{key}': {val}"
            raise ValidationError(msg) from e
        if dec_val > ceiling:
            msg = (
                f"Unsafe config: '{key}' value {dec_val} "
                f"exceeds hard ceiling of {ceiling}"
            )
            raise ValidationError(msg)


def _validate_ceilings(raw_dict: dict[str, Any]) -> None:
    """Validate all configured safety limits against hard ceilings."""
    _validate_ceiling(raw_dict, "max_daily_loss_pct", MAX_DAILY_LOSS_PCT)
    _validate_ceiling(raw_dict, "max_total_loss_pct", MAX_TOTAL_LOSS_PCT)
    _validate_ceiling(
        raw_dict, "max_margin_utilization_pct", MAX_MARGIN_UTILIZATION_PCT
    )
    _validate_ceiling(raw_dict, "max_effective_leverage", MAX_EFFECTIVE_LEVERAGE)
    _validate_ceiling(raw_dict, "max_risk_per_trade", MAX_RISK_PER_TRADE)
    _validate_ceiling(raw_dict, "max_stress_loss_pct", MAX_STRESS_LOSS_PCT)


def _validate_live_profile(profile_name: str, raw_dict: dict[str, Any]) -> None:
    """Enforce that live profiles explicitly authorize live execution.

    Also ensures operator approvals are present.
    """
    allow_live = raw_dict.get("allow_live_execution", False)
    if "live" in profile_name.lower() and not allow_live:
        msg = (
            f"Live configuration profile '{profile_name}' must explicitly "
            "set allow_live_execution to true."
        )
        logger.error(msg)
        raise ValidationError(msg)

    if allow_live:
        operator_approval = raw_dict.get("operator_approval_fields")
        if not operator_approval:
            msg = (
                f"Live configuration profile '{profile_name}' requires "
                "explicit operator approval fields to authorize live mode."
            )
            logger.error(msg)
            raise ValidationError(msg)

        # Verify it has operator_id, approved_at, approval_token
        required_approval_keys = {"operator_id", "approved_at", "approval_token"}
        if not isinstance(
            operator_approval, dict
        ) or not required_approval_keys.issubset(operator_approval.keys()):
            msg = (
                f"Live configuration profile '{profile_name}' operator approval fields "
                f"must contain keys: {required_approval_keys}"
            )
            logger.error(msg)
            raise ValidationError(msg)

        _validate_prop_firm_ceilings(profile_name, raw_dict)
        _validate_owner_approval_for_increased_limits(
            profile_name, raw_dict, operator_approval
        )


def _validate_prop_firm_ceilings(profile_name: str, raw_dict: dict[str, Any]) -> None:
    """Enforce that live profiles remain below external prop-firm limits."""
    daily_limit = Decimal("0.04")
    total_limit = Decimal("0.08")
    daily_val = Decimal(str(raw_dict.get("max_daily_loss_pct", 0.0)))
    total_val = Decimal(str(raw_dict.get("max_total_loss_pct", 0.0)))
    if daily_val > daily_limit:
        msg = (
            f"Live configuration '{profile_name}' daily loss limit {daily_val} "
            f"exceeds external prop-firm ceiling of {daily_limit}."
        )
        logger.error(msg)
        raise ValidationError(msg)
    if total_val > total_limit:
        msg = (
            f"Live configuration '{profile_name}' total loss limit {total_val} "
            f"exceeds external prop-firm ceiling of {total_limit}."
        )
        logger.error(msg)
        raise ValidationError(msg)


def _validate_owner_approval_for_increased_limits(
    profile_name: str,
    raw_dict: dict[str, Any],
    operator_approval: dict[str, Any],
) -> None:
    """Require owner/admin approval before increasing limits above defaults."""
    increased_keys = []
    for key, default_val in CONSERVATIVE_DEFAULTS.items():
        val = raw_dict.get(key)
        if val is not None and Decimal(str(val)) > default_val:
            increased_keys.append(key)

    if increased_keys:
        operator_id = operator_approval.get("operator_id", "")
        if operator_id not in {"owner", "admin"}:
            msg = (
                f"Increasing risk thresholds {increased_keys} above conservative "
                f"defaults in live profile '{profile_name}' requires explicit "
                f"owner/admin approval. Current operator: '{operator_id}'."
            )
            logger.error(msg)
            raise ValidationError(msg)


def _resolve_config_path(profile_name: str) -> Path:
    """Resolve configuration profile file path."""
    file_path = CONFIGS_DIR / f"{profile_name}.json"
    if not file_path.exists():
        file_path = Path(profile_name)
        if not file_path.exists():
            msg = f"Configuration profile '{profile_name}' not found."
            logger.error(msg)
            raise ValidationError(msg)
    return file_path


def _check_unknown_keys(profile_name: str, raw_dict: dict[str, Any]) -> None:
    """Check for unknown configuration keys and reject non-experimental ones."""
    allowed_fields = set(RiskConfig.model_fields.keys())
    extra_keys = set(raw_dict.keys()) - allowed_fields
    for key in extra_keys:
        if key.startswith("experimental_") and raw_dict[key] is False:
            continue
        msg = f"Unknown configuration keys found in '{profile_name}': {key}"
        logger.error(msg)
        raise ValidationError(msg)


def _apply_env_overrides(raw_dict: dict[str, Any]) -> None:
    """Apply environment-specific overrides for whitelisted configuration keys."""
    allowed_fields = set(RiskConfig.model_fields.keys())
    for key in allowed_fields:
        env_val = os.getenv(f"HARUQUANT_RISK_{key.upper()}")
        if env_val is not None:
            if key not in APPROVED_OVERRIDE_KEYS:
                msg = f"Environment override not allowed for key: {key}"
                logger.error(msg)
                raise ValidationError(msg)
            # Apply override by coercing type
            field_info = RiskConfig.model_fields[key]
            field_type = field_info.annotation
            try:
                if field_type is Decimal:
                    raw_dict[key] = Decimal(env_val)
                elif field_type is int:
                    raw_dict[key] = int(env_val)
                elif field_type is float:
                    raw_dict[key] = float(env_val)
                elif field_type is bool:
                    raw_dict[key] = env_val.lower() in ("true", "1", "yes")
                else:
                    raw_dict[key] = env_val
            except Exception as e:
                msg = (
                    f"Failed to parse environment override for '{key}': {env_val} ({e})"
                )
                logger.error(msg)
                raise ValidationError(msg) from e


def load_risk_config(profile_name: str) -> RiskConfig:
    """Load, parse, and validate a risk configuration profile by name.

    Args:
        profile_name: Name of the JSON config file without extension (e.g. 'default').

    Returns:
        RiskConfig: The parsed and validated configuration model.

    Raises:
        ValidationError: If parsing fails, unknown keys are present,
                         limits exceed hard ceilings, or live authorization is invalid.
    """
    cached = _registry.get(profile_name)
    if cached is not None:
        return cached

    file_path = _resolve_config_path(profile_name)
    raw_dict = _read_json_file(file_path)

    _check_unknown_keys(profile_name, raw_dict)
    _apply_env_overrides(raw_dict)
    _validate_ceilings(raw_dict)
    _validate_live_profile(profile_name, raw_dict)

    try:
        raw_dict.setdefault("created_at", "2026-06-18T00:00:00Z")
        config = RiskConfig(**raw_dict)
    except Exception as e:
        msg = f"Failed to instantiate RiskConfig model: {e}"
        logger.error(msg)
        raise ValidationError(msg) from e

    _registry.register(profile_name, config)

    return config
