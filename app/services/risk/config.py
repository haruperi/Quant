"""Risk configuration loaders and validation.

Responsible for loading YAML config profiles, validating against hard ceilings,
computing stable hashes, and enforcing live execution authorization checks.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from app.services.risk.models import RiskConfig
from app.utils.errors import ValidationError
from app.utils.logger import logger

# Hard ceiling constraints
MAX_DAILY_LOSS_PCT = Decimal("0.20")
MAX_TOTAL_LOSS_PCT = Decimal("0.50")
MAX_MARGIN_UTILIZATION_PCT = Decimal("1.00")
MAX_EFFECTIVE_LEVERAGE = Decimal("500.0")
MAX_RISK_PER_TRADE = Decimal("0.10")

CONFIGS_DIR = Path(__file__).resolve().parent / "configs"


def _read_yaml_file(file_path: Path) -> dict[str, Any]:
    """Read and parse dictionary content from YAML file."""
    try:
        with file_path.open(encoding="utf-8") as f:
            raw_dict = yaml.safe_load(f)
    except Exception as e:
        msg = f"Failed to parse YAML config from {file_path}: {e}"
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


def _validate_live_profile(profile_name: str, raw_dict: dict[str, Any]) -> None:
    """Enforce that live profiles explicitly authorize live execution."""
    allow_live = raw_dict.get("allow_live_execution", False)
    if "live" in profile_name.lower() and not allow_live:
        msg = (
            f"Live configuration profile '{profile_name}' must explicitly "
            "set allow_live_execution to true."
        )
        logger.error(msg)
        raise ValidationError(msg)


def load_risk_config(profile_name: str) -> RiskConfig:
    """Load, parse, and validate a risk configuration profile by name.

    Args:
        profile_name: Name of the YAML config file without extension (e.g. 'default').

    Returns:
        RiskConfig: The parsed and validated configuration model.

    Raises:
        ValidationError: If parsing fails, unknown keys are present,
                         limits exceed hard ceilings, or live authorization is invalid.
    """
    file_path = CONFIGS_DIR / f"{profile_name}.yaml"
    if not file_path.exists():
        # Fallback to absolute or custom path if not found in service configs
        file_path = Path(profile_name)
        if not file_path.exists():
            msg = f"Configuration profile '{profile_name}' not found."
            logger.error(msg)
            raise ValidationError(msg)

    raw_dict = _read_yaml_file(file_path)

    # 1. Reject unknown config keys by default
    allowed_fields = set(RiskConfig.model_fields.keys())
    extra_keys = set(raw_dict.keys()) - allowed_fields
    if extra_keys:
        msg = f"Unknown configuration keys found in '{profile_name}': {extra_keys}"
        logger.error(msg)
        raise ValidationError(msg)

    # 2. Reject unsafe threshold values above configured maximums
    _validate_ceilings(raw_dict)

    # 3. Reject live profiles that lack explicit live authority fields
    _validate_live_profile(profile_name, raw_dict)

    # Load into Pydantic model
    try:
        raw_dict.setdefault("created_at", "2026-06-18T00:00:00Z")
        config = RiskConfig(**raw_dict)
    except Exception as e:
        msg = f"Failed to instantiate RiskConfig model: {e}"
        logger.error(msg)
        raise ValidationError(msg) from e

    return config
