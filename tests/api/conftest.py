import logging

import pytest
from fastapi.testclient import TestClient

import jarvis.core.logging as logging_module
from jarvis.api.app import create_app
from jarvis.core.config import Environment, LogFormat, Settings


@pytest.fixture(autouse=True)
def _reset_logging_state() -> None:
    """Reset structlog/stdlib logging config before each test.

    `configure_logging()` is idempotent by design (safe for repeated
    calls in production), but that means its handler would otherwise
    keep a reference to a *previous* test's `sys.stdout`, which pytest's
    `capsys` swaps out per test. Resetting here ensures each test's
    `create_app()` call reconfigures logging against the current stdout.
    """
    logging_module._configured = False
    logging.getLogger().handlers = []


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        environment=Environment.DEVELOPMENT,
        log_format=LogFormat.JSON,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings=settings)
    with TestClient(app) as test_client:
        yield test_client
