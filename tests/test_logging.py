import logging

import structlog

from jarvis.core.config import LogFormat, Settings
from jarvis.core.logging import configure_logging, get_logger
import jarvis.core.logging as logging_module


def _reset_logging_state() -> None:
    logging_module._configured = False
    logging.getLogger().handlers = []


def test_configure_logging_sets_root_handler() -> None:
    _reset_logging_state()
    settings = Settings(_env_file=None, log_format=LogFormat.JSON)  # type: ignore[call-arg]

    configure_logging(settings)

    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 1
    assert root_logger.level == logging.INFO


def test_configure_logging_is_idempotent() -> None:
    _reset_logging_state()
    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    configure_logging(settings)
    configure_logging(settings)  # second call must be a no-op

    assert len(logging.getLogger().handlers) == 1


def test_get_logger_emits_structured_output(capsys) -> None:  # type: ignore[no-untyped-def]
    _reset_logging_state()
    settings = Settings(_env_file=None, log_format=LogFormat.JSON)  # type: ignore[call-arg]
    configure_logging(settings)

    logger = get_logger("test.module")
    logger.info("hello_world", key="value")

    captured = capsys.readouterr()
    assert "hello_world" in captured.out
    assert "value" in captured.out


def test_get_logger_returns_bound_logger() -> None:
    logger = get_logger("some.name")
    assert isinstance(logger, structlog.stdlib.BoundLogger) or hasattr(logger, "info")
