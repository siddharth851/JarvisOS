"""Tests for the chat API endpoint."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.core.config import Environment, LogFormat, Settings
from jarvis.providers.ollama import OllamaConnectionError, OllamaResponseError
from jarvis.services.chat import ChatResult, ChatService, get_chat_service


@pytest.fixture
def mock_chat_service() -> MagicMock:
    service = MagicMock(spec=ChatService)
    service.chat.return_value = ChatResult(
        response="Hi there!",
        model="llama3.2",
        timestamp=datetime(2026, 7, 11, 12, 0, 0, tzinfo=UTC),
    )
    return service


@pytest.fixture
def chat_client(
    settings: Settings,
    mock_chat_service: MagicMock,
) -> TestClient:
    app = create_app(settings=settings)
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_chat_returns_200(chat_client: TestClient) -> None:
    response = chat_client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 200


def test_chat_response_shape(chat_client: TestClient) -> None:
    response = chat_client.post("/api/v1/chat", json={"message": "Hello"})
    body = response.json()

    assert body["response"] == "Hi there!"
    assert body["model"] == "llama3.2"
    datetime.fromisoformat(body["timestamp"])


def test_chat_passes_message_to_service(
    chat_client: TestClient,
    mock_chat_service: MagicMock,
) -> None:
    chat_client.post("/api/v1/chat", json={"message": "Hello"})

    mock_chat_service.chat.assert_called_once_with("Hello")


def test_chat_empty_message_returns_422(chat_client: TestClient) -> None:
    response = chat_client.post("/api/v1/chat", json={"message": ""})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "Validation failed"


def test_chat_whitespace_message_returns_422(chat_client: TestClient) -> None:
    response = chat_client.post("/api/v1/chat", json={"message": "   "})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "Validation failed"
    assert any(err["loc"][-1] == "message" for err in body["detail"])


def test_chat_missing_message_returns_422(chat_client: TestClient) -> None:
    response = chat_client.post("/api/v1/chat", json={})

    assert response.status_code == 422
    assert response.json()["error"] == "Validation failed"


def test_chat_ollama_connection_error_returns_503(
    settings: Settings,
    mock_chat_service: MagicMock,
) -> None:
    mock_chat_service.chat.side_effect = OllamaConnectionError("unreachable")

    app = create_app(
        settings=Settings(
            _env_file=None,  # type: ignore[call-arg]
            environment=Environment.DEVELOPMENT,
            log_format=LogFormat.JSON,
        )
    )
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    with TestClient(app) as client:
        response = client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 503
    assert response.json() == {"error": "Ollama service unavailable"}


def test_chat_ollama_response_error_returns_502(
    settings: Settings,
    mock_chat_service: MagicMock,
) -> None:
    mock_chat_service.chat.side_effect = OllamaResponseError("bad response")

    app = create_app(
        settings=Settings(
            _env_file=None,  # type: ignore[call-arg]
            environment=Environment.DEVELOPMENT,
            log_format=LogFormat.JSON,
        )
    )
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    with TestClient(app) as client:
        response = client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 502
    assert response.json() == {"error": "Ollama returned an invalid response"}


def test_chat_includes_request_id_header(chat_client: TestClient) -> None:
    response = chat_client.post("/api/v1/chat", json={"message": "Hello"})

    assert "X-Request-ID" in response.headers
