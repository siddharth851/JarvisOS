from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import inspect

from jarvis.api.app import create_app
from jarvis.core.config import Environment, LogFormat, Settings
import jarvis.database as database
from jarvis.database.models import ChatMessage, ChatSession


def test_init_db_creates_engine_and_session_local(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment=Environment.DEVELOPMENT,
        log_format=LogFormat.JSON,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )

    database.init_db(settings)

    assert database.engine is not None
    assert database.SessionLocal is not None
    assert hasattr(database.SessionLocal, "configure") or hasattr(
        database.SessionLocal, "__call__"
    )

    database.shutdown_db()


def test_app_startup_initializes_database(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment=Environment.DEVELOPMENT,
        log_format=LogFormat.JSON,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )
    app = create_app(settings=settings)

    with TestClient(app):
        assert app.state.settings is settings
        assert hasattr(app.state, "settings")
        assert app.state.settings.database_url == settings.database_url
        assert app.state.db_engine is not None
        assert app.state.db_session_local is not None
        assert database.engine is not None
        assert database.SessionLocal is not None

    assert database.engine is None
    assert database.SessionLocal is None


def test_database_models_are_created_and_related(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment=Environment.DEVELOPMENT,
        log_format=LogFormat.JSON,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )
    database.init_db(settings)
    assert database.engine is not None

    inspector = inspect(database.engine)
    assert "chat_sessions" in inspector.get_table_names()
    assert "chat_messages" in inspector.get_table_names()

    session = database.SessionLocal()
    try:
        chat_session = ChatSession()
        session.add(chat_session)
        session.flush()

        message = ChatMessage(
            session_id=chat_session.id,
            role="user",
            content="Hello",
        )
        session.add(message)
        session.commit()

        refreshed = session.get(ChatSession, chat_session.id)
        assert refreshed is not None
        assert len(refreshed.messages) == 1
        assert refreshed.messages[0].content == "Hello"
    finally:
        session.close()
        database.shutdown_db()
