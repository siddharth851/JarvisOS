"""Tests for the Ollama provider."""

import json

import httpx
import pytest

from jarvis.core.config import Settings, get_settings
from jarvis.providers.ollama import (
    OllamaClient,
    OllamaConnectionError,
    OllamaResponseError,
    get_ollama_client,
)


@pytest.fixture
def ollama_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.test:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")
    return Settings(_env_file=None)  # type: ignore[call-arg]


def _make_client(
    settings: Settings,
    handler: httpx.MockTransport,
) -> OllamaClient:
    http_client = httpx.Client(
        transport=handler,
        base_url=settings.ollama_host,
    )
    return OllamaClient(settings, http_client=http_client)


def test_settings_read_ollama_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://custom:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "mistral")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.ollama_host == "http://custom:11434"
    assert settings.ollama_model == "mistral"


def test_health_check_returns_healthy(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/"
        return httpx.Response(200, text="Ollama is running")

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    result = client.health_check()

    assert result == {"healthy": True, "host": "http://ollama.test:11434"}


def test_health_check_handles_connection_error(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    result = client.health_check()

    assert result["healthy"] is False
    assert result["host"] == "http://ollama.test:11434"
    assert "connection refused" in result["error"]


def test_health_check_handles_http_error(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    result = client.health_check()

    assert result["healthy"] is False
    assert result["status_code"] == 503


def test_generate_returns_response_text(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        body = json.loads(request.content)
        assert body == {
            "model": "llama3.2",
            "prompt": "Hello",
            "stream": False,
        }
        return httpx.Response(
            200,
            json={"response": "Hi there!", "done": True},
        )

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    assert client.generate("Hello") == "Hi there!"


def test_generate_raises_on_connection_error(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    with pytest.raises(OllamaConnectionError, match="Cannot connect to Ollama"):
        client.generate("Hello")


def test_generate_raises_on_http_error(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    with pytest.raises(OllamaResponseError, match="HTTP 500"):
        client.generate("Hello")


def test_generate_raises_on_invalid_response(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"done": True})

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    with pytest.raises(OllamaResponseError, match="missing 'response' field"):
        client.generate("Hello")


def test_list_models_returns_model_names(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(
            200,
            json={
                "models": [
                    {"name": "llama3.2:latest"},
                    {"name": "mistral:7b"},
                ]
            },
        )

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    assert client.list_models() == ["llama3.2:latest", "mistral:7b"]


def test_list_models_raises_on_connection_error(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    with pytest.raises(OllamaConnectionError, match="Cannot connect to Ollama"):
        client.list_models()


def test_list_models_raises_on_invalid_response(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"tags": []})

    client = _make_client(ollama_settings, httpx.MockTransport(handler))

    with pytest.raises(OllamaResponseError, match="missing 'models' field"):
        client.list_models()


def test_get_ollama_client_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.test:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")
    get_settings.cache_clear()
    get_ollama_client.cache_clear()

    first = get_ollama_client()
    second = get_ollama_client()

    assert first is second
    assert first.host == "http://ollama.test:11434"
    assert first.model == "llama3.2"

    first.close()
    get_ollama_client.cache_clear()
    get_settings.cache_clear()


def test_client_strips_trailing_slash_from_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.test:11434/")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Ollama is running")

    client = _make_client(settings, httpx.MockTransport(handler))

    assert client.host == "http://ollama.test:11434"
