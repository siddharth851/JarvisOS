"""Database foundation for Jarvis.

Provides SQLAlchemy engine/session initialization and a declarative base
for future conversation memory models.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from jarvis.core.config import Settings
from jarvis.core.logging import get_logger

logger = get_logger("jarvis.database")

Base = declarative_base()
engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None

# Import models to ensure they are registered on Base before metadata creation.
from jarvis.database import models  # noqa: F401


def init_db(settings: Settings) -> None:
    """Initialize the SQLAlchemy engine, create tables, and configure sessions."""

    global engine, SessionLocal
    if engine is not None and SessionLocal is not None:
        return

    engine_kwargs: dict[str, object] = {"future": True}
    if settings.database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_engine(settings.database_url, **engine_kwargs)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(
            "database_initialization_failed",
            database_url=settings.database_url,
            error=str(exc),
        )
        raise

    logger.info("database_initialized", database_url=settings.database_url)


def shutdown_db() -> None:
    """Dispose of the SQLAlchemy engine and clear session state."""

    global engine, SessionLocal
    if engine is None:
        return

    engine.dispose()
    engine = None
    SessionLocal = None
    logger.info("database_shutdown")