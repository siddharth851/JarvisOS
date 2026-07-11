"""Application configuration.

All runtime configuration is centralized here and loaded from environment
variables (or a local .env file). Other modules must depend on `Settings`
via `get_settings()` rather than reading `os.environ` directly, so that
configuration stays a single, testable, injectable source of truth.
"""

from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment the application is running in."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Supported logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(StrEnum):
    """Supported log rendering formats."""

    CONSOLE = "console"
    JSON = "json"


class Settings(BaseSettings):
    """Central application settings, populated from environment variables.

    Environment variables are read with the `JARVIS_` prefix, e.g.
    `JARVIS_LOG_LEVEL=DEBUG`. See `.env.example` for the full list.
    """

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Jarvis"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    log_level: LogLevel = LogLevel.INFO
    log_format: LogFormat = LogFormat.CONSOLE

    ollama_host: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_HOST",
    )
    ollama_model: str = Field(
        default="llama3.2",
        validation_alias="OLLAMA_MODEL",
    )

    @property
    def is_production(self) -> bool:
        """Whether the application is running in production."""
        return self.environment is Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached `Settings` instance.

    Cached so `Settings` is parsed from the environment exactly once per
    process. Use as a FastAPI dependency: `Depends(get_settings)`.
    """
    return Settings()
