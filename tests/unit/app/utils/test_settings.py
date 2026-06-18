"""Unit tests for Settings model and environment variable loading configuration."""

from pathlib import Path

import pytest
from app.utils.errors import ConfigurationError
from app.utils.settings import CONFIGURATION_ERROR, Settings


def test_settings_load_defaults(tmp_path: Path) -> None:
    """Settings can be loaded with default values."""
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        haruquant_home=tmp_path,
        environment="local",
    )
    assert settings.environment == "local"
    assert settings.haruquant_home == tmp_path.resolve()
    assert settings.data_dir == tmp_path.resolve() / "data"
    assert settings.cache_dir == tmp_path.resolve() / "cache"
    assert settings.audit_dir == tmp_path.resolve() / "audit"
    assert settings.enable_file_logging is False


def test_settings_production_requires_explicit_home() -> None:
    """Production mode requires haruquant_home to be explicitly configured."""
    with pytest.raises(
        ConfigurationError,
        match="production deployments must configure HARUQUANT_HOME",
    ) as exc_info:
        Settings(_env_file=None, environment="production")  # type: ignore[call-arg]
    assert exc_info.value.code == CONFIGURATION_ERROR


def test_settings_invalid_environment() -> None:
    """Invalid environment throws validation error."""
    with pytest.raises(ConfigurationError, match="environment is invalid") as exc_info:
        Settings(_env_file=None, environment="invalid_env")  # type: ignore[call-arg]
    assert exc_info.value.code == CONFIGURATION_ERROR


def test_settings_environment_aliases(tmp_path: Path) -> None:
    """Settings map environment aliases like 'dev' and 'prod' to standard values."""
    settings_dev = Settings(  # type: ignore[call-arg]
        _env_file=None, environment="dev", haruquant_home=tmp_path
    )
    assert settings_dev.environment == "development"

    settings_prod = Settings(  # type: ignore[call-arg]
        _env_file=None, environment="prod", haruquant_home=tmp_path
    )
    assert settings_prod.environment == "production"
