"""Unit tests for utility runtime settings helpers."""

from pathlib import Path

import pytest
from app.utils import (
    CONFIGURATION_ERROR,
    HARUQUANT_HOME,
    RuntimeSettings,
    inject_runtime_settings,
    load_runtime_settings,
)
from app.utils.errors import ConfigurationError


def test_load_runtime_settings_defaults_under_local_home(tmp_path: Path) -> None:
    """Runtime settings use deterministic local defaults without import side effects."""
    settings = load_runtime_settings(
        {HARUQUANT_HOME: tmp_path, "ENVIRONMENT": "local"},
        environ={},
    )

    assert isinstance(settings, RuntimeSettings)
    assert settings.environment == "local"
    assert settings.home_dir == tmp_path.resolve()
    assert settings.data_dir == tmp_path.resolve() / "data"
    assert settings.cache_dir == tmp_path.resolve() / "cache"
    assert settings.audit_dir == tmp_path.resolve() / "audit"
    assert settings.logging.enable_file_logging is False


def test_load_runtime_settings_precedence_and_injection(tmp_path: Path) -> None:
    """Explicit values override env and dotenv, then inject into mapping."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "ENVIRONMENT=staging\n"
        "LOG_LEVEL=ERROR\n"
        "HARUQUANT_HOME=dotenv_home\n",  # pragma: allowlist secret
        encoding="utf-8",
    )

    settings = load_runtime_settings(
        {
            HARUQUANT_HOME: tmp_path / "explicit_home",
            "ENVIRONMENT": "test",
            "ENABLE_FILE_LOGGING": "true",
            "LOG_DIR": "runtime_logs",
            "auth": {"required": True},
        },
        env_file=env_file,
        environ={"ENVIRONMENT": "production", "LOG_LEVEL": "WARNING"},
    )
    target: dict[str, object] = {"existing": "kept"}

    returned = inject_runtime_settings(target, settings)

    assert settings.environment == "test"
    assert settings.log_level == "WARNING"
    assert settings.logging.log_dir == settings.home_dir / "runtime_logs"
    assert returned is target
    assert target["existing"] == "kept"
    assert target["auth"] == {"required": True}


def test_load_runtime_settings_rejects_invalid_values(tmp_path: Path) -> None:
    """Malformed settings fail with deterministic configuration errors."""
    with pytest.raises(ConfigurationError, match="environment is invalid") as exc_info:
        load_runtime_settings({"ENVIRONMENT": "live"}, environ={})
    assert exc_info.value.code == CONFIGURATION_ERROR

    with pytest.raises(ConfigurationError, match="production deployments"):
        load_runtime_settings({"ENVIRONMENT": "production"}, environ={})

    with pytest.raises(ConfigurationError, match="log_max_bytes"):
        load_runtime_settings(
            {
                HARUQUANT_HOME: tmp_path,
                "LOG_MAX_BYTES": "0",
            },
            environ={},
        )
