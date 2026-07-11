from pathlib import Path

from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.core.config import Environment, LogFormat, Settings
import jarvis.database as database


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
