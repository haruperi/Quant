"""Runtime settings support helpers for the utility foundation.

This module contains support helpers, not official AI tools. It exports
immutable runtime settings models plus explicit loading and injection helpers.

Public exports:
    HARUQUANT_HOME, CONFIGURATION_ERROR, HaruQuantConfigurationError,
    LoggingSettings, RuntimeSettings, load_runtime_settings,
    inject_runtime_settings.

Side effects:
    None on import. Environment variables and optional dotenv files are read
    only when ``load_runtime_settings`` is called explicitly.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from app.utils.errors import ConfigurationError
from app.utils.paths import normalize_path

HARUQUANT_HOME = "HARUQUANT_HOME"
CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
HaruQuantConfigurationError = ConfigurationError

EnvironmentMode = Literal["local", "test", "development", "staging", "production"]

_VALID_ENVIRONMENTS = {"local", "test", "development", "staging", "production"}
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    """Immutable logging configuration.

    Args:
        log_dir: Optional directory for explicit file logging.
        enable_file_logging: Whether file logging should be enabled.
        max_bytes: Maximum size for each rotated log file.
        backup_count: Number of rotated files to keep.
        retention_days: Optional retention window for external cleanup policy.
        use_json: Whether structured JSON logging is preferred.
        use_color: Whether human-readable console logs may use color.
    """

    log_dir: Path | None = None
    enable_file_logging: bool = False
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5
    retention_days: int | None = None
    use_json: bool = False
    use_color: bool = True


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Immutable utility runtime settings.

    Args:
        environment: Runtime environment mode.
        log_level: Logging threshold name.
        home_dir: Resolved HaruQuant home directory.
        data_dir: Resolved data directory.
        cache_dir: Resolved cache directory.
        audit_dir: Resolved audit directory.
        timezone: Runtime timezone policy.
        strict_validation: Whether warnings should be escalated by consumers.
        logging: Logging-specific settings.
        auth: Auth helper configuration.
        event_bus: Event Bus helper configuration.
        notifications: Notification helper configuration.
        observability: Observability helper configuration.
        ohlcv: OHLCV validation defaults.
        validation: Schema-validation resource defaults.
    """

    environment: EnvironmentMode
    log_level: str
    home_dir: Path
    data_dir: Path
    cache_dir: Path
    audit_dir: Path
    timezone: str = "UTC"
    strict_validation: bool = True
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    auth: dict[str, object] = field(default_factory=dict)
    event_bus: dict[str, object] = field(default_factory=dict)
    notifications: dict[str, object] = field(default_factory=dict)
    observability: dict[str, object] = field(default_factory=dict)
    ohlcv: dict[str, object] = field(default_factory=dict)
    validation: dict[str, object] = field(default_factory=dict)


def _parse_env_file(env_file: str | Path | None) -> dict[str, str]:
    """Parse a simple dotenv file when explicitly requested."""
    if env_file is None:
        return {}
    path = normalize_path(env_file)
    if not path.exists():
        msg = f"settings env_file does not exist: {path}"
        raise HaruQuantConfigurationError(msg, code=CONFIGURATION_ERROR)
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def _setting(
    key: str,
    *,
    explicit: Mapping[str, object],
    environ: Mapping[str, str],
    dotenv: Mapping[str, str],
    default: object,
) -> object:
    """Return a setting according to explicit, env, dotenv, default precedence."""
    if key in explicit:
        return explicit[key]
    if key in environ:
        return environ[key]
    if key in dotenv:
        return dotenv[key]
    return default


def _as_bool(value: object, *, field_name: str) -> bool:
    """Normalize common boolean setting values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUTHY:
            return True
        if lowered in _FALSY:
            return False
    msg = f"{field_name} must be a boolean."
    raise HaruQuantConfigurationError(msg, code=CONFIGURATION_ERROR)


def _as_int(value: object, *, field_name: str, minimum: int | None = None) -> int:
    """Normalize integer setting values."""
    if not isinstance(value, str | bytes | bytearray | int):
        msg = f"{field_name} must be an integer."
        raise HaruQuantConfigurationError(msg, code=CONFIGURATION_ERROR)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        msg = f"{field_name} must be an integer."
        raise HaruQuantConfigurationError(msg, code=CONFIGURATION_ERROR) from exc
    if minimum is not None and parsed < minimum:
        msg = f"{field_name} must be at least {minimum}."
        raise HaruQuantConfigurationError(msg, code=CONFIGURATION_ERROR)
    return parsed


def _mapping_setting(values: Mapping[str, object], key: str) -> dict[str, object]:
    """Return a shallow dict copy for mapping-valued settings."""
    value = values.get(key)
    if isinstance(value, Mapping):
        return {str(item_key): item_value for item_key, item_value in value.items()}
    return {}


def _as_environment(value: object) -> EnvironmentMode:
    """Validate and normalize the runtime environment."""
    if not isinstance(value, str):
        raise HaruQuantConfigurationError(
            "environment must be a string.", code=CONFIGURATION_ERROR
        )
    environment = value.strip().lower()
    if environment not in _VALID_ENVIRONMENTS:
        msg = f"environment is invalid: {environment}"
        raise HaruQuantConfigurationError(msg, code=CONFIGURATION_ERROR)
    return environment  # type: ignore[return-value]


def _resolve_under_home(value: object, *, home_dir: Path, field_name: str) -> Path:
    """Resolve a directory value under home when relative."""
    if not isinstance(value, str | Path):
        msg = f"{field_name} must be a path."
        raise HaruQuantConfigurationError(msg, code=CONFIGURATION_ERROR)
    raw = Path(value)
    path = raw if raw.is_absolute() else home_dir / raw
    return normalize_path(path, base_dir=home_dir)


def load_runtime_settings(
    values: Mapping[str, object] | None = None,
    *,
    env_file: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> RuntimeSettings:
    """Load immutable runtime settings from explicit inputs.

    Args:
        values: Explicit setting overrides with highest precedence.
        env_file: Optional dotenv-style file read only during this call.
        environ: Optional environment mapping for deterministic tests. Defaults
            to ``os.environ`` at call time.

    Returns:
        RuntimeSettings: Immutable resolved runtime settings.

    Raises:
        HaruQuantConfigurationError: If settings are malformed.
    """
    explicit = values or {}
    env_values = os.environ if environ is None else environ
    dotenv = _parse_env_file(env_file)

    environment = _as_environment(
        _setting(
            "ENVIRONMENT",
            explicit=explicit,
            environ=env_values,
            dotenv=dotenv,
            default="local",
        )
    )
    strict_validation = _as_bool(
        _setting(
            "STRICT_VALIDATION",
            explicit=explicit,
            environ=env_values,
            dotenv=dotenv,
            default=True,
        ),
        field_name="strict_validation",
    )
    home_raw = _setting(
        HARUQUANT_HOME,
        explicit=explicit,
        environ=env_values,
        dotenv=dotenv,
        default=Path.cwd() / ".haruquant",
    )
    if not isinstance(home_raw, str | Path):
        raise HaruQuantConfigurationError(
            "HARUQUANT_HOME must be a path.", code=CONFIGURATION_ERROR
        )
    home_dir = normalize_path(home_raw)
    home_configured = (
        HARUQUANT_HOME in explicit
        or HARUQUANT_HOME in env_values
        or HARUQUANT_HOME in dotenv
    )
    if environment == "production" and not home_configured:
        raise HaruQuantConfigurationError(
            "production deployments must configure HARUQUANT_HOME explicitly.",
            code=CONFIGURATION_ERROR,
        )

    log_level = str(
        _setting(
            "LOG_LEVEL",
            explicit=explicit,
            environ=env_values,
            dotenv=dotenv,
            default="INFO",
        )
    ).upper()
    log_dir_raw = _setting(
        "LOG_DIR",
        explicit=explicit,
        environ=env_values,
        dotenv=dotenv,
        default="logs",
    )
    enable_file_logging = _as_bool(
        _setting(
            "ENABLE_FILE_LOGGING",
            explicit=explicit,
            environ=env_values,
            dotenv=dotenv,
            default=False,
        ),
        field_name="enable_file_logging",
    )
    logging = LoggingSettings(
        log_dir=_resolve_under_home(
            log_dir_raw, home_dir=home_dir, field_name="log_dir"
        )
        if enable_file_logging
        else None,
        enable_file_logging=enable_file_logging,
        max_bytes=_as_int(
            _setting(
                "LOG_MAX_BYTES",
                explicit=explicit,
                environ=env_values,
                dotenv=dotenv,
                default=10 * 1024 * 1024,
            ),
            field_name="log_max_bytes",
            minimum=1,
        ),
        backup_count=_as_int(
            _setting(
                "LOG_BACKUP_COUNT",
                explicit=explicit,
                environ=env_values,
                dotenv=dotenv,
                default=5,
            ),
            field_name="log_backup_count",
            minimum=0,
        ),
        retention_days=None,
        use_json=_as_bool(
            _setting(
                "LOG_USE_JSON",
                explicit=explicit,
                environ=env_values,
                dotenv=dotenv,
                default=environment in {"staging", "production"},
            ),
            field_name="log_use_json",
        ),
        use_color=_as_bool(
            _setting(
                "LOG_USE_COLOR",
                explicit=explicit,
                environ=env_values,
                dotenv=dotenv,
                default=environment not in {"staging", "production"},
            ),
            field_name="log_use_color",
        ),
    )

    return RuntimeSettings(
        environment=environment,
        log_level=log_level,
        home_dir=home_dir,
        data_dir=_resolve_under_home(
            _setting(
                "DATA_DIR",
                explicit=explicit,
                environ=env_values,
                dotenv=dotenv,
                default="data",
            ),
            home_dir=home_dir,
            field_name="data_dir",
        ),
        cache_dir=_resolve_under_home(
            _setting(
                "CACHE_DIR",
                explicit=explicit,
                environ=env_values,
                dotenv=dotenv,
                default="cache",
            ),
            home_dir=home_dir,
            field_name="cache_dir",
        ),
        audit_dir=_resolve_under_home(
            _setting(
                "AUDIT_DIR",
                explicit=explicit,
                environ=env_values,
                dotenv=dotenv,
                default="audit",
            ),
            home_dir=home_dir,
            field_name="audit_dir",
        ),
        timezone=str(
            _setting(
                "TIMEZONE",
                explicit=explicit,
                environ=env_values,
                dotenv=dotenv,
                default="UTC",
            )
        ),
        strict_validation=strict_validation,
        logging=logging,
        auth=_mapping_setting(explicit, "auth"),
        event_bus=_mapping_setting(explicit, "event_bus"),
        notifications=_mapping_setting(explicit, "notifications"),
        observability=_mapping_setting(explicit, "observability"),
        ohlcv=_mapping_setting(explicit, "ohlcv"),
        validation=_mapping_setting(explicit, "validation"),
    )


def inject_runtime_settings(
    target: MutableMapping[str, object],
    settings: RuntimeSettings,
) -> MutableMapping[str, object]:
    """Inject runtime settings into a caller-owned mutable mapping.

    Args:
        target: Mutable mapping to update.
        settings: Resolved runtime settings.

    Returns:
        The same mapping object that was supplied by the caller.

    Side effects:
        Mutates only ``target``.
    """
    target.update(
        {
            "environment": settings.environment,
            "log_level": settings.log_level,
            "home_dir": settings.home_dir,
            "data_dir": settings.data_dir,
            "cache_dir": settings.cache_dir,
            "audit_dir": settings.audit_dir,
            "timezone": settings.timezone,
            "strict_validation": settings.strict_validation,
            "logging": settings.logging,
            "auth": settings.auth,
            "event_bus": settings.event_bus,
            "notifications": settings.notifications,
            "observability": settings.observability,
        }
    )
    return target
