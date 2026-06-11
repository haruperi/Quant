"""Immutable runtime settings helpers for HaruQuantAI utilities."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from tools.utils.errors import ConfigurationError, ValidationError
from tools.utils.normalization import DEFAULT_TIMEZONE
from tools.utils.paths import normalize_path

DEFAULT_ENVIRONMENT = "local"
DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Immutable runtime settings snapshot."""

    environment: str
    log_level: str
    home_dir: Path
    data_dir: Path
    cache_dir: Path
    audit_dir: Path
    timezone: str
    allow_live_mutations: bool
    strict_validation: bool


def _source_value(
    key: str,
    source: Mapping[str, str] | None,
    default: str,
) -> str:
    """Return setting value from explicit source, environment, or default."""
    if source is not None and key in source:
        return source[key]
    return os.environ.get(key, default)


def _bool_value(value: str, *, field_name: str) -> bool:
    """Parse a deterministic bool setting."""
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    message = f"{field_name} must be boolean-like."
    raise ValidationError(message, code="INVALID_INPUT")


def default_haruquant_home(source: Mapping[str, str] | None = None) -> Path:
    """Return the deterministic HaruQuant home directory path."""
    configured = _source_value("HARUQUANT_HOME", source, "")
    if configured:
        return normalize_path(configured)
    return normalize_path(Path.cwd() / ".haruquant")


def load_runtime_settings(
    source: Mapping[str, str] | None = None,
    *,
    create_dirs: bool = False,
) -> RuntimeSettings:
    """Load immutable runtime settings from explicit source/env/defaults.

    Args:
        source: Optional explicit setting mapping. Values here take precedence
            over environment variables.
        create_dirs: Reserved explicit side-effect switch. Directory creation is
            intentionally not performed in this support helper.

    Returns:
        Immutable runtime settings.
    """
    if create_dirs:
        raise ConfigurationError(
            "load_runtime_settings does not create directories; call path "
            "helpers explicitly.",
        )
    home = default_haruquant_home(source)
    data_dir = normalize_path(
        _source_value("HARUQUANT_DATA_DIR", source, "data"), base_dir=home
    )
    cache_dir = normalize_path(
        _source_value("HARUQUANT_CACHE_DIR", source, "cache"), base_dir=home
    )
    audit_dir = normalize_path(
        _source_value("HARUQUANT_AUDIT_DIR", source, "audit"), base_dir=home
    )
    environment = _source_value("ENVIRONMENT", source, DEFAULT_ENVIRONMENT).strip()
    log_level = _source_value("LOG_LEVEL", source, DEFAULT_LOG_LEVEL).strip().upper()
    timezone = _source_value("DEFAULT_TIMEZONE", source, DEFAULT_TIMEZONE).strip()
    if not environment:
        raise ValidationError("environment must be non-empty.", code="INVALID_INPUT")
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValidationError("log_level is invalid.", code="INVALID_INPUT")
    return RuntimeSettings(
        environment=environment,
        log_level=log_level,
        home_dir=home,
        data_dir=data_dir,
        cache_dir=cache_dir,
        audit_dir=audit_dir,
        timezone=timezone,
        allow_live_mutations=_bool_value(
            _source_value("ALLOW_LIVE_MUTATIONS", source, "false"),
            field_name="ALLOW_LIVE_MUTATIONS",
        ),
        strict_validation=_bool_value(
            _source_value("STRICT_VALIDATION", source, "true"),
            field_name="STRICT_VALIDATION",
        ),
    )
