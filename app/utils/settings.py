"""Runtime configuration and settings loading using Pydantic.

This module exports the Pydantic-based ``Settings`` class and its global singleton
instance ``settings``, loaded dynamically from environment variables and an
optional ``.env`` file.

Public exports:
    HARUQUANT_HOME, CONFIGURATION_ERROR, HaruQuantConfigurationError,
    Settings, settings, LiveMode, Config, load_config, validate_config.

Side effects:
    None on import. Environment variables and dotenv files are read only when
    the Settings class is instantiated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.errors import ConfigurationError
from app.utils.paths import normalize_path

HARUQUANT_HOME = "HARUQUANT_HOME"
CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
HaruQuantConfigurationError = ConfigurationError

EnvironmentMode = Literal["local", "test", "development", "staging", "production"]

LiveMode = Literal[
    "package_only",
    "paper",
    "shadow",
    "micro_live",
    "full_live",
]


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Core environment
    environment: str = "local"
    app_name: str = "app"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    ui_origin: str = "http://localhost:3000"
    log_level: str = "INFO"
    database_url: str = "sqlite:///data/db.sqlite3"
    active_broker: str = "mt5"  # Currently mt5, ctrader, simulator

    # MetaTrader 5
    mt5_enabled: bool = False
    mt5_login: str = ""
    mt5_password: str = ""
    mt5_server: str = ""
    mt5_terminal_path: str = ""
    mt5_environment: str = "demo"

    # cTrader
    ctrader_enabled: bool = False
    ctrader_client_id: str = ""
    ctrader_client_secret: str = ""
    ctrader_access_token: str = ""
    ctrader_refresh_token: str = ""
    ctrader_redirect_url: str = ""
    ctrader_environment: str = "demo"
    ctrader_account_id: int | None = None

    # Gemini / Google AI Studio
    gemini_api_key: str = Field(default="", validation_alias="GOOGLE_API_KEY")
    gemini_model: str = Field(
        default="gemini-3.5-flash",
        validation_alias="HARUQUANT_AGENT_MODEL",
    )
    gemini_temperature: float = 0.2
    gemini_max_tokens: int = 4096
    gemini_top_p: float = 0.95
    gemini_top_k: int = 40

    # OpenAI (Optional)
    openai_api_key: str | None = None
    openai_model: str | None = "gpt-4o"
    openai_temperature: float = 0.2
    openai_max_tokens: int = 4096
    openai_top_p: float = 0.95
    openai_top_k: int = 40

    # Ollama (Optional)
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    ollama_temperature: float = 0.2
    ollama_max_tokens: int = 4096
    ollama_top_p: float = 0.95
    ollama_top_k: int = 40

    FOREX_SYMBOLS: list[str] = [
        "AUDCAD",
        "AUDCHF",
        "AUDJPY",
        "AUDNZD",
        "AUDUSD",
        "CADCHF",
        "CADJPY",
        "CHFJPY",
        "EURAUD",
        "EURCAD",
        "EURCHF",
        "EURGBP",
        "EURJPY",
        "EURNZD",
        "EURUSD",
        "GBPAUD",
        "GBPCAD",
        "GBPCHF",
        "GBPJPY",
        "GBPNZD",
        "GBPUSD",
        "NZDCAD",
        "NZDCHF",
        "NZDJPY",
        "NZDUSD",
        "USDCHF",
        "USDCAD",
        "USDJPY",
    ]

    COMMODITY_SYMBOLS: list[str] = [
        "XAUUSD",
        "XAUEUR",
        "XAUGBP",
        "XAUJPY",
        "XAUAUD",
        "XAUCHF",
        "XAGUSD",
    ]

    INDICES_SYMBOLS: list[str] = [
        "US500",
        "US30",
        "UK100",
        "GER40",
        "NAS100",
        "USDX",
        "EURX",
        "JPYX",
    ]

    # Combine all symbols
    ALL_SYMBOLS: list[str] = []

    # Runtime Directories & Time
    haruquant_home: Path = Field(
        default_factory=lambda: Path.cwd() / ".haruquant",
        validation_alias="HARUQUANT_HOME",
    )
    data_dir: Path = Field(default=Path("data"), validation_alias="DATA_DIR")
    cache_dir: Path = Field(default=Path("cache"), validation_alias="CACHE_DIR")
    audit_dir: Path = Field(default=Path("audit"), validation_alias="AUDIT_DIR")
    timezone: str = Field(default="UTC", validation_alias="TIMEZONE")
    strict_validation: bool = Field(default=True, validation_alias="STRICT_VALIDATION")

    # File Logging Settings
    log_dir: Path = Field(default=Path("logs"), validation_alias="LOG_DIR")
    enable_file_logging: bool = Field(
        default=False, validation_alias="ENABLE_FILE_LOGGING"
    )
    log_max_bytes: int = Field(
        default=10 * 1024 * 1024, validation_alias="LOG_MAX_BYTES"
    )
    log_backup_count: int = Field(default=5, validation_alias="LOG_BACKUP_COUNT")
    log_use_json: bool | None = Field(default=None, validation_alias="LOG_USE_JSON")
    log_use_color: bool | None = Field(default=None, validation_alias="LOG_USE_COLOR")

    # Mappings for extensible components
    auth: dict[str, object] = Field(default_factory=dict)
    event_bus: dict[str, object] = Field(default_factory=dict)
    notifications: dict[str, object] = Field(default_factory=dict)
    observability: dict[str, object] = Field(default_factory=dict)
    ohlcv: dict[str, object] = Field(default_factory=dict)
    validation: dict[str, object] = Field(default_factory=dict)

    # ── Live Runtime Configuration ────────────────────────────────────────────
    # live_enabled: Master flag. Defaults to False (fail-closed). Live trading
    # requires explicit opt-in via environment/config. Live runtime will reject
    # all broker mutations unless this flag is True.
    live_enabled: bool = Field(default=False, validation_alias="LIVE_ENABLED")

    # live_mode: Current live promotion ladder rung.
    # package_only  - no broker calls; request packages only (default/safe).
    # paper         - canonical execution contracts, no real broker account.
    # shadow        - records intended orders, compares vs. market, no mutation.
    # micro_live    - reduced size, strict daily limits, enhanced monitoring.
    # full_live     - full live broker mutation (requires explicit approval).
    live_mode: str = Field(default="package_only", validation_alias="LIVE_MODE")

    # live_workflow_timeout_seconds: Max seconds before WORKFLOW_TIMEOUT incident.
    live_workflow_timeout_seconds: int = Field(
        default=30, validation_alias="LIVE_WORKFLOW_TIMEOUT_SECONDS"
    )

    # live_max_staleness_seconds: Max allowed age of broker/account/position
    # snapshots before live mutation is blocked.
    live_max_staleness_seconds: int = Field(
        default=10, validation_alias="LIVE_MAX_STALENESS_SECONDS"
    )

    # live_broker_adapter_timeout_seconds: Per-call timeout for broker adapter
    # requests. Timeout → unknown_outcome (never confirmed/rejected).
    live_broker_adapter_timeout_seconds: int = Field(
        default=5, validation_alias="LIVE_BROKER_ADAPTER_TIMEOUT_SECONDS"
    )

    # live_cost_budget_usd: Optional session cost ceiling in USD. If set, the
    # runtime blocks mutations that would exceed the budget.
    live_cost_budget_usd: float | None = Field(
        default=None, validation_alias="LIVE_COST_BUDGET_USD"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    def _validate_live_settings(self) -> None:
        """Validate live runtime settings to reduce complexity in main validator."""
        # Validate live_mode
        valid_live_modes = {
            "package_only",
            "paper",
            "shadow",
            "micro_live",
            "full_live",
        }
        if self.live_mode not in valid_live_modes:
            msg = (
                f"live_mode is invalid: {self.live_mode!r}. "
                f"Must be one of {sorted(valid_live_modes)}."
            )
            raise ConfigurationError(msg, code=CONFIGURATION_ERROR)

        # Validate live timeout/staleness fields
        if self.live_workflow_timeout_seconds <= 0:
            msg = "live_workflow_timeout_seconds must be greater than zero."
            raise ConfigurationError(msg, code=CONFIGURATION_ERROR)
        if self.live_max_staleness_seconds <= 0:
            msg = "live_max_staleness_seconds must be greater than zero."
            raise ConfigurationError(msg, code=CONFIGURATION_ERROR)
        if self.live_broker_adapter_timeout_seconds <= 0:
            msg = "live_broker_adapter_timeout_seconds must be greater than zero."
            raise ConfigurationError(msg, code=CONFIGURATION_ERROR)
        if self.live_cost_budget_usd is not None and self.live_cost_budget_usd <= 0:
            msg = "live_cost_budget_usd must be positive when set."
            raise ConfigurationError(msg, code=CONFIGURATION_ERROR)

    @model_validator(mode="after")
    def _validate_and_resolve_paths(self) -> Settings:
        """Validate environment values and normalize configuration paths.

        Returns:
            Settings: Resolved Settings instance.

        Raises:
            ConfigurationError: If environment parameters are malformed.
        """
        # Validate environment
        env = self.environment.strip().lower()
        if env == "dev":
            env = "development"
        elif env == "prod":
            env = "production"
        valid_envs = {"local", "test", "development", "staging", "production"}
        if env not in valid_envs:
            msg = f"environment is invalid: {env}"
            raise ConfigurationError(msg, code=CONFIGURATION_ERROR)
        self.environment = env

        # Ensure strict validation constraint for production home configuration
        if (
            self.environment == "production"
            and "haruquant_home" not in self.model_fields_set
        ):
            msg = "production deployments must configure HARUQUANT_HOME explicitly."
            raise ConfigurationError(msg, code=CONFIGURATION_ERROR)

        # Validate live settings via helper
        self._validate_live_settings()

        # Upper case log level
        self.log_level = self.log_level.upper()

        # Resolve home directory
        home_path = normalize_path(self.haruquant_home)
        self.haruquant_home = home_path

        # Resolve child directories under home if relative
        def _resolve(p: Path) -> Path:
            resolved = p if p.is_absolute() else home_path / p
            return normalize_path(resolved, base_dir=home_path)

        self.data_dir = _resolve(self.data_dir)
        self.cache_dir = _resolve(self.cache_dir)
        self.audit_dir = _resolve(self.audit_dir)
        self.log_dir = _resolve(self.log_dir)

        # Handle log defaults based on environment mode
        if self.log_use_json is None:
            self.log_use_json = self.environment in {"staging", "production"}
        if self.log_use_color is None:
            self.log_use_color = self.environment not in {"staging", "production"}

        # Populate combined symbols list
        self.ALL_SYMBOLS = (
            self.FOREX_SYMBOLS + self.COMMODITY_SYMBOLS + self.INDICES_SYMBOLS
        )

        return self


settings = Settings()

# ── Live Runtime Config Shims ─────────────────────────────────────────────────
# ``Config`` is a forward-compatible alias used by the live module so it can
# consume the shared Settings instance without coupling to the class name.
Config = Settings


def load_config() -> Settings:
    """Return the application-wide settings singleton.

    This shim allows the live module to call ``load_config()`` without
    importing ``settings`` directly, making it easier to inject test
    configurations via dependency injection in unit tests.

    Returns:
        Settings: The global settings instance.

    Side effects:
        None. Returns the already-constructed singleton; does not re-read
        environment variables or dotenv files.
    """
    return settings


def validate_config(cfg: Settings) -> list[str]:
    """Validate a Settings instance for live runtime readiness.

    Checks live-specific constraints beyond Pydantic field validation:
    - live_enabled/live_mode consistency
    - required live secret references are non-empty when live is enabled
    - staleness/timeout are within safe bounds

    Args:
        cfg: Settings instance to validate.

    Returns:
        List of human-readable validation error strings. Empty list means valid.

    Side effects:
        None. Does not expose secret values in error messages.
    """
    errors: list[str] = []

    # Validate live mode consistency
    live_only_modes = {"micro_live", "full_live"}
    if cfg.live_mode in live_only_modes and not cfg.live_enabled:
        errors.append(f"live_mode={cfg.live_mode!r} requires live_enabled=True.")

    # Validate that an active broker is configured when live is enabled
    if cfg.live_enabled and not cfg.active_broker.strip():
        errors.append("active_broker must be set when live_enabled=True.")

    # Validate MT5 secret references when MT5 is enabled and live is enabled
    if cfg.live_enabled and cfg.mt5_enabled:
        if not cfg.mt5_login.strip():
            errors.append("mt5_login is required when live_enabled and mt5_enabled.")
        if not cfg.mt5_server.strip():
            errors.append("mt5_server is required when live_enabled and mt5_enabled.")
        # Note: password presence is checked but NOT logged (secret value)
        if not cfg.mt5_password:
            errors.append(
                "mt5_password secret reference is missing "
                "when live_enabled and mt5_enabled. [secret value not logged]"
            )

    # Validate cTrader secret references when cTrader is enabled and live is enabled
    if cfg.live_enabled and cfg.ctrader_enabled:
        if not cfg.ctrader_client_id.strip():
            errors.append(
                "ctrader_client_id is required when live_enabled and ctrader_enabled."
            )
        if not cfg.ctrader_access_token:
            errors.append(
                "ctrader_access_token secret reference is missing. "
                "[secret value not logged]"
            )

    return errors
