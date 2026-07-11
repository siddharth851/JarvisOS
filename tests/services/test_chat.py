"""Tests for the chat service."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from jarvis.providers.ollama import OllamaConnectionError, OllamaResponseError
from jarvis.services.chat import ChatService


@pytest.fixture
def mock_ollama() -> MagicMock:
    client = MagicMock()
    client.model = "llama3.2"
    client.generate.return_value = "Hello back!"
    return client


def test_chat_returns_response_model_and_timestamp(mock_ollama: MagicMock) -> None:
    service = ChatService(mock_ollama)

    before = datetime.now(UTC)
    result = service.chat("Hello")
    after = datetime.now(UTC)

    assert result.response == "Hello back!"
    assert result.model == "llama3.2"
    assert before <= result.timestamp <= after
    mock_ollama.generate.assert_called_once_with("Hello")


def test_chat_propagates_connection_error(mock_ollama: MagicMock) -> None:
    mock_ollama.generate.side_effect = OllamaConnectionError("unreachable")
    service = ChatService(mock_ollama)

    with pytest.raises(OllamaConnectionError):
        service.chat("Hello")


def test_chat_propagates_response_error(mock_ollama: MagicMock) -> None:
    mock_ollama.generate.side_effect = OllamaResponseError("bad response")
    service = ChatService(mock_ollama)

    with pytest.raises(OllamaResponseError):
        service.chat("Hello")
