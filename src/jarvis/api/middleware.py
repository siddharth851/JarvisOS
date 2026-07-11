"""HTTP middleware: request correlation IDs and structured request logging."""

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

REQUEST_ID_HEADER = "X-Request-ID"

logger = structlog.get_logger("jarvis.request")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a unique ID to every request.

    Reuses an inbound `X-Request-ID` header if the caller supplied one
    (useful for tracing across services), otherwise generates a new UUID4.
    The ID is bound into structlog's contextvars so every log line emitted
    while handling the request — including by other middleware or route
    handlers — automatically carries it, and it's echoed back on the
    response so clients can correlate their request with server logs.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")

        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log one structured entry per completed HTTP request.

    Emitted after the response is produced so the log line includes the
    resolved status code and total handling duration. Must be registered
    after `RequestIDMiddleware` (i.e. added second) so `request_id` is
    already bound to the logging context when this runs.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client=request.client.host if request.client else None,
        )
        return response
