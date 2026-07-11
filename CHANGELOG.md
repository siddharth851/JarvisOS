# Changelog

All notable changes to Project Jarvis are documented here, module by module.

## [0.2.0] — Module 2: FastAPI Foundation

### Added
- **Application factory** (`jarvis.api.app.create_app`) building a fully configured `FastAPI` instance — enables isolated app instances per test rather than a shared global.
- **Lifespan events** (`jarvis.api.app._lifespan`) logging structured startup/shutdown events; establishes `app.state` as the attachment point for future resources (Ollama client, SQLite connection, etc.).
- **CORS middleware** (permissive defaults, safe for local-first development; revisit before any network-exposed deployment).
- **Request ID middleware** (`jarvis.api.middleware.RequestIDMiddleware`) — generates or reuses an `X-Request-ID`, binds it into structlog's contextvars, and echoes it back on the response.
- **Request logging middleware** (`jarvis.api.middleware.RequestLoggingMiddleware`) — emits one structured `http_request` log line per request with method, path, status code, duration, and client host.
- **Global exception handlers** (`jarvis.api.exceptions.register_exception_handlers`) — consistent `{"error": ..., "detail": ...}` JSON shape for validation errors (422), `HTTPException`s, and unhandled exceptions (500), all logged with context.
- **API v1 router** (`jarvis.api.v1.router`) mounted at `/api/v1`, aggregating versioned route modules.
- **`GET /api/v1/health`** — returns status, version, environment, and current timestamp.
- **`GET /api/v1/version`** — returns version, app name, and environment.
- **ASGI entrypoint** (`jarvis.main:app`) for `uvicorn`.
- 14 new tests covering the app factory, both endpoints, both middleware, and all three exception-handler paths.

### Changed
- `jarvis/__init__.py` now defines `__version__ = "0.2.0"` as the single source of truth, consumed by both `/version` and the FastAPI app's `version` field.
- `pyproject.toml`: added `fastapi`, `uvicorn[standard]` as runtime dependencies and `httpx` as a dev dependency (required for `TestClient`).

### Explicitly not included (by design)
Ollama integration, SQLite persistence, memory, chat, authentication, and browser automation — reserved for later modules.

### Notes
- Middleware registration order matters: `RequestIDMiddleware` is added *after* `RequestLoggingMiddleware` so that, per Starlette's reverse-execution order, the request ID is bound to the logging context before the request logger runs.
- `configure_logging()` remains idempotent (see Module 1) but test fixtures explicitly reset its internal state per test so each test's `TestClient` captures logs against its own isolated stdout/caplog context.

---

## [0.1.0] — Module 1: Core Config & Logging

### Added
- **`Settings`** (`jarvis.core.config`) via `pydantic-settings`, reading all configuration from environment variables under the `JARVIS_` prefix (or a local `.env` file). Includes `Environment`, `LogLevel`, and `LogFormat` as `StrEnum` types, plus an `is_production` convenience property.
- **`get_settings()`** — `lru_cache`d singleton provider, ready for FastAPI's `Depends()` injection in later modules.
- **Structured logging** (`jarvis.core.logging`) via `structlog`, integrated with stdlib `logging` so third-party libraries route through the same pipeline. Supports `console` (colorized, human-readable) and `json` (machine-parseable) rendering, selected via `JARVIS_LOG_FORMAT`.
- **`configure_logging()`** — idempotent setup, safe to call multiple times without duplicating handlers.
- **`get_logger()`** — returns a structlog-bound logger for use throughout the codebase.
- Project scaffolding: `src/` layout, `uv`-managed `pyproject.toml`, `.env.example`, `.gitignore`.
- 9 tests covering settings defaults, environment-variable overrides, cache behavior, and logging configuration/idempotency/output.
