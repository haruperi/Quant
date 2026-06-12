"""
Application configuration

Use this file to:
- load .env
- parse settings
- setup logging

"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    environment: str
    app_name: str
    api_host: str
    api_port: int
    ui_origin: str
    log_level: str
    database_url: str

    # MetaTrader 5
    mt5_enabled: bool
    mt5_login: str
    mt5_password: str
    mt5_server: str
    mt5_terminal_path: str
    mt5_environment: str

    # cTrader
    ctrader_enabled: bool
    ctrader_client_id: str
    ctrader_client_secret: str
    ctrader_access_token: str
    ctrader_refresh_token: str
    ctrader_redirect_url: str
    ctrader_environment: str

    # Gemini / Google AI Studio
    gemini_api_key: str = Field(validation_alias="GOOGLE_API_KEY")
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

    # Tell Pydantic to read from the .env file in the project root
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]


if __name__ == "__main__":
    # Test config
    print("Environment:", settings.environment)
    print("App name:", settings.app_name)
    print("API host:", settings.api_host)
    print("API port:", settings.api_port)
    print("UI origin:", settings.ui_origin)
    print("Log level:", settings.log_level)
    print("Database URL:", settings.database_url)
    print("MT5 enabled:", settings.mt5_enabled)
    print("MT5 login:", settings.mt5_login)
    print("MT5 password:", settings.mt5_password)
    print("MT5 server:", settings.mt5_server)
    print("MT5 terminal path:", settings.mt5_terminal_path)
    print("MT5 environment:", settings.mt5_environment)
