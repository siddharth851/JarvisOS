"""Application factory.

Builds and configures the FastAPI application: config, logging, CORS,
request-tracking middleware, global exception handlers, and versioned
API routers. Keeping this as a factory (`create_app`) rather than a
module-level `app` instance keeps the app testable — each test can build
a fresh instance with its own `Settings` override if needed.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from jarvis import __version__
from jarvis.api.exceptions import register_exception_handlers
from jarvis.api.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from jarvis.api.v1.router import router as v1_router
from jarvis.core.config import Settings, get_settings
from jarvis.core.logging import configure_logging
import jarvis.database as database

logger = structlog.get_logger("jarvis.app")


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown hooks.

    Startup logs that the service is ready; shutdown logs a clean exit.
    Future modules (Ollama client, SQLite connection pool, etc.) will
    initialize and tear down their resources here, attached to
    `app.state` so route handlers can access them via dependency
    injection.
    """
    settings: Settings = app.state.settings
    database.init_db(settings)
    app.state.db_engine = database.engine
    app.state.db_session_local = database.SessionLocal
    logger.info(
        "jarvis_startup",
        app_name=settings.app_name,
        environment=settings.environment.value,
        version=__version__,
    )
    yield
    database.shutdown_db()
    logger.info("jarvis_shutdown", app_name=settings.app_name)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure a `FastAPI` application instance.

    Args:
        settings: Optional explicit `Settings` (primarily for tests).
            Defaults to the cached `get_settings()` singleton.
    """
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
        lifespan=_lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Registered so RequestIDMiddleware.dispatch runs first per request
    # (Starlette executes middleware in reverse of add order), ensuring
    # request_id is bound before RequestLoggingMiddleware logs the line.
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    register_exception_handlers(app)

    app.include_router(v1_router)

    return app
