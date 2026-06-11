"""Unit tests for runtime settings helpers."""

from pathlib import Path

import pytest
from tools.utils import ConfigurationError, load_runtime_settings


def test_load_runtime_settings_from_source(tmp_path: Path) -> None:
    """Runtime settings are immutable and do not create directories."""
    settings = load_runtime_settings(
        {
            "HARUQUANT_HOME": str(tmp_path),
            "LOG_LEVEL": "debug",
            "ALLOW_LIVE_MUTATIONS": "false",
            "STRICT_VALIDATION": "true",
        },
    )

    assert settings.home_dir == tmp_path
    assert settings.log_level == "DEBUG"
    assert settings.allow_live_mutations is False


def test_load_runtime_settings_rejects_side_effect_creation() -> None:
    """Directory creation must be explicit through path helpers."""
    with pytest.raises(ConfigurationError):
        load_runtime_settings(create_dirs=True)
