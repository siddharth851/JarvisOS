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
        session_id="123e4567-e89b-12d3-a456-426614174000",
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

    assert body["session_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert body["response"] == "Hi there!"
    assert body["model"] == "llama3.2"
    datetime.fromisoformat(body["timestamp"])


def test_chat_passes_message_to_service(
    chat_client: TestClient,
    mock_chat_service: MagicMock,
) -> None:
    chat_client.post("/api/v1/chat", json={"message": "Hello"})

    mock_chat_service.chat.assert_called_once_with("Hello", session_id=None)


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


def test_tool_browser_open_google_returns_tool_response(
    settings: Settings,
    mock_chat_service: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Ensure browser opening doesn't actually happen.
    import webbrowser

    monkeypatch.setattr(webbrowser, "open", lambda *_args, **_kwargs: True)

    # NOTE: For tool actions, we still override chat_service to ensure
    # we don't touch Ollama for tool flows.
    app = create_app(settings=settings)
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    with TestClient(app) as client:
        res = client.post("/api/v1/chat", json={"message": "Open Google"})
        assert res.status_code == 200
        body = res.json()

    assert body["type"] == "tool"
    assert body["tool"] == "browser"
    assert body["status"] == "success"
    assert body["message"] == "Tool executed successfully."
    assert isinstance(body["session_id"], str)


def test_tool_file_create_file_returns_tool_response(
    settings: Settings,
    mock_chat_service: MagicMock,
    tmp_path: "pytest.TempPathFactory",
) -> None:
    app = create_app(settings=settings)
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    file_path = tmp_path / "notes.txt"
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/chat",
            json={
                "message": f"Create File {file_path}",
            },
        )

        assert res.status_code == 200
        body = res.json()

    assert body["type"] == "tool"
    assert body["tool"] == "file"
    assert body["status"] == "success"
    assert isinstance(body["session_id"], str)
    assert file_path.exists()


def test_tool_terminal_run_pwd_returns_tool_response(
    settings: Settings,
    mock_chat_service: MagicMock,
) -> None:
    app = create_app(settings=settings)
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    with TestClient(app) as client:
        res = client.post("/api/v1/chat", json={"message": "Run pwd"})
        assert res.status_code == 200
        body = res.json()

    assert body["type"] == "tool"
    assert body["tool"] == "terminal"
    assert body["status"] == "success"
    assert isinstance(body["session_id"], str)
    assert body["data"]["result"]["success"] is True


def test_chat_returns_200_when_session_id_missing(
    settings: Settings,
    mock_chat_service: MagicMock,
) -> None:
    app = create_app(settings=settings)
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    with TestClient(app) as client:
        res = client.post("/api/v1/chat", json={"message": "Hello"})
        assert res.status_code == 200
        body = res.json()

    assert body["session_id"] == "123e4567-e89b-12d3-a456-426614174000"


def test_chat_preserves_existing_session_id(
    settings: Settings,
    mock_chat_service: MagicMock,
) -> None:
    app = create_app(settings=settings)
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    with TestClient(app) as client:
        res = client.post(
            "/api/v1/chat",
            json={"message": "Hello", "session_id": "my-session-1"},
        )

        assert res.status_code == 200

    # ChatService is mocked; we just assert correct routing to it.
    mock_chat_service.chat.assert_called_with("Hello", session_id="my-session-1")


def test_unknown_command_falls_back_to_chat(
    settings: Settings,
    mock_chat_service: MagicMock,
) -> None:
    app = create_app(settings=settings)
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    with TestClient(app) as client:
        res = client.post("/api/v1/chat", json={"message": "Explain Binary Search"})

    assert res.status_code == 200
    body = res.json()
    assert body["response"] == "Hi there!"
    assert body["model"] == "llama3.2"


def test_unknown_command_with_non_tool_prefix_still_routes_to_chat(
    settings: Settings,
    mock_chat_service: MagicMock,
) -> None:
    app = create_app(settings=settings)
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    with TestClient(app) as client:
        res = client.post("/api/v1/chat", json={"message": "Write Python code"})

    assert res.status_code == 200
    mock_chat_service.chat.assert_called_once()
