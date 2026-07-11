"""Tests for the chat service."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import jarvis.database as database
from jarvis.core.config import Environment, LogFormat, Settings
from jarvis.database.models import ChatSession
from jarvis.providers.ollama import OllamaConnectionError, OllamaResponseError
from jarvis.services.chat import ChatService


@pytest.fixture
def mock_ollama() -> MagicMock:
    client = MagicMock()
    client.model = "llama3.2"
    client.generate.return_value = "Hello back!"
    return client


@pytest.fixture
def db_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment=Environment.DEVELOPMENT,
        log_format=LogFormat.JSON,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )


@pytest.fixture(autouse=True)
def _init_db(db_settings: Settings) -> None:
    database.init_db(db_settings)
    try:
        yield
    finally:
        database.shutdown_db()


def test_chat_returns_response_model_and_timestamp(
    mock_ollama: MagicMock,
    db_settings: Settings,
) -> None:
    service = ChatService(mock_ollama)

    before = datetime.now(UTC)
    result = service.chat("Hello")
    after = datetime.now(UTC)

    assert result.session_id is not None
    assert result.response == "Hello back!"
    assert result.model == "llama3.2"
    assert before <= result.timestamp <= after
    mock_ollama.generate.assert_called_once_with("Hello")


def test_chat_creates_new_session_and_persists_messages(
    mock_ollama: MagicMock,
    db_settings: Settings,
) -> None:
    service = ChatService(mock_ollama)

    result = service.chat("Hello")
    assert result.session_id is not None

    session = database.SessionLocal()
    try:
        chat_session = session.get(ChatSession, result.session_id)
        assert chat_session is not None
        assert len(chat_session.messages) == 2
        assert chat_session.messages[0].role == "user"
        assert chat_session.messages[0].content == "Hello"
        assert chat_session.messages[1].role == "assistant"
        assert chat_session.messages[1].content == "Hello back!"
    finally:
        session.close()


def test_chat_reuses_existing_session(
    mock_ollama: MagicMock,
    db_settings: Settings,
) -> None:
    service = ChatService(mock_ollama)

    first = service.chat("Hello")
    second = service.chat("Again", session_id=first.session_id)

    assert second.session_id == first.session_id

    session = database.SessionLocal()
    try:
        chat_session = session.get(ChatSession, first.session_id)
        assert chat_session is not None
        assert len(chat_session.messages) == 4
        assert chat_session.messages[-1].role == "assistant"
        assert chat_session.messages[-1].content == "Hello back!"
    finally:
        session.close()


def test_chat_propagates_connection_error(
    mock_ollama: MagicMock,
    db_settings: Settings,
) -> None:
    mock_ollama.generate.side_effect = OllamaConnectionError("unreachable")
    service = ChatService(mock_ollama)

    with pytest.raises(OllamaConnectionError):
        service.chat("Hello")


def test_chat_propagates_response_error(
    mock_ollama: MagicMock,
    db_settings: Settings,
) -> None:
    mock_ollama.generate.side_effect = OllamaResponseError("bad response")
    service = ChatService(mock_ollama)

    with pytest.raises(OllamaResponseError):
        service.chat("Hello")


def test_chat_history_loaded_and_sent_to_ollama(
    mock_ollama: MagicMock,
    db_settings: Settings,
) -> None:
    service = ChatService(mock_ollama)

    first = service.chat("Hello")
    second = service.chat("Who am I?", session_id=first.session_id)

    assert mock_ollama.generate.call_count == 2
    first_call = mock_ollama.generate.call_args_list[0]
    second_call = mock_ollama.generate.call_args_list[1]

    assert first_call[0][0] == "Hello"

    second_prompt = second_call[0][0]
    assert "User: Hello" in second_prompt
    assert "Assistant: Hello back!" in second_prompt
    assert "User: Who am I?" in second_prompt


def test_chat_conversation_ordering(
    mock_ollama: MagicMock,
    db_settings: Settings,
) -> None:
    mock_ollama.generate.side_effect = [
        "Response 1",
        "Response 2",
        "Response 3",
    ]
    service = ChatService(mock_ollama)

    r1 = service.chat("Message 1")
    r2 = service.chat("Message 2", session_id=r1.session_id)
    r3 = service.chat("Message 3", session_id=r1.session_id)

    third_call = mock_ollama.generate.call_args_list[2]
    third_prompt = third_call[0][0]

    lines = third_prompt.split("\n")
    m1_idx = next(i for i, l in enumerate(lines) if "Message 1" in l)
    r1_idx = next(i for i, l in enumerate(lines) if "Response 1" in l)
    m2_idx = next(i for i, l in enumerate(lines) if "Message 2" in l)
    r2_idx = next(i for i, l in enumerate(lines) if "Response 2" in l)
    m3_idx = next(i for i, l in enumerate(lines) if "Message 3" in l)

    assert m1_idx < r1_idx < m2_idx < r2_idx < m3_idx


def test_chat_session_isolation(
    mock_ollama: MagicMock,
    db_settings: Settings,
) -> None:
    service = ChatService(mock_ollama)

    session1_r1 = service.chat("Session 1 Message")
    session2_r1 = service.chat("Session 2 Message")

    session1_r2 = service.chat("Session 1 Again", session_id=session1_r1.session_id)
    session2_r2 = service.chat("Session 2 Again", session_id=session2_r1.session_id)

    session1_call = mock_ollama.generate.call_args_list[2]
    session1_prompt = session1_call[0][0]

    session2_call = mock_ollama.generate.call_args_list[3]
    session2_prompt = session2_call[0][0]

    assert "Session 1" in session1_prompt
    assert "Session 2" not in session1_prompt

    assert "Session 2" in session2_prompt
    assert "Session 1" not in session2_prompt


def test_chat_new_session_history_is_empty(
    mock_ollama: MagicMock,
    db_settings: Settings,
) -> None:
    service = ChatService(mock_ollama)

    service.chat("Hello")

    first_call = mock_ollama.generate.call_args_list[0]
    first_prompt = first_call[0][0]

    assert first_prompt == "Hello"
