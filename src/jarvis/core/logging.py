"""Structured logging configuration.

Configures `structlog` as the single logging pipeline for the application,
routing standard-library `logging` calls (e.g. from uvicorn, playwright,
third-party libs) through the same processors so every log line — ours or
a dependency's — has consistent structure and formatting.
"""

import logging
import sys

import structlog

from jarvis.core.config import LogFormat, Settings

_configured = False


def configure_logging(settings: Settings) -> None:
    """Configure structlog + stdlib logging according to `settings`.

    Idempotent: safe to call multiple times (e.g. once at app startup,
    again in tests) — only the first call takes effect.
    """
    global _configured
    if _configured:
        return

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_format is LogFormat.JSON:
        renderer: structlog.typing.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.log_level.value)

    _configured = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog-bound logger.

    Call `configure_logging()` once at startup before using this; if not
    yet configured, structlog falls back to its default (unstructured)
    setup so imports never fail.
    """
    return structlog.get_logger(name)
