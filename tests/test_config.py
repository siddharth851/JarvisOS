import pytest

from jarvis.core.config import Environment, LogFormat, LogLevel, Settings, get_settings


def test_defaults_when_no_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JARVIS_ENVIRONMENT", raising=False)
    monkeypatch.delenv("JARVIS_DEBUG", raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.app_name == "Jarvis"
    assert settings.environment is Environment.DEVELOPMENT
    assert settings.debug is False
    assert settings.log_level is LogLevel.INFO
    assert settings.log_format is LogFormat.CONSOLE


def test_reads_from_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_APP_NAME", "TestApp")
    monkeypatch.setenv("JARVIS_ENVIRONMENT", "production")
    monkeypatch.setenv("JARVIS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("JARVIS_LOG_FORMAT", "json")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.app_name == "TestApp"
    assert settings.environment is Environment.PRODUCTION
    assert settings.log_level is LogLevel.DEBUG
    assert settings.log_format is LogFormat.JSON


def test_is_production_property(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_ENVIRONMENT", "production")
    assert Settings(_env_file=None).is_production is True  # type: ignore[call-arg]

    monkeypatch.setenv("JARVIS_ENVIRONMENT", "development")
    assert Settings(_env_file=None).is_production is False  # type: ignore[call-arg]


def test_invalid_environment_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_ENVIRONMENT", "not-a-real-env")
    with pytest.raises(ValueError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
