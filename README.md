# Jarvis

An offline-first AI Operating System. Local-only AI inference (Ollama), local storage (SQLite), local automation (Playwright) — no cloud dependency.

## Status

Built module-by-module, each one production-ready and fully tested before the next begins.

| Module | Description | Status |
|---|---|---|
| 1 | Core Config & Logging | ✅ Complete |
| 2 | FastAPI Foundation | ✅ Complete |
| 3 | Ollama Provider | ✅ Complete |
| 4 | Chat API | ✅ Complete |
| 5+ | SQLite, Memory, Auth, Browser | Not started |

## Requirements

- Python >= 3.11
- [`uv`](https://docs.astral.sh/uv/) for dependency management

## Setup

```bash
cp .env.example .env      # adjust values as needed
uv sync --dev
```

## Running the server

```bash
uv run uvicorn jarvis.main:app --reload
```

The API is served under `/api/v1`. With defaults:

- `GET http://127.0.0.1:8000/api/v1/health` — service health check
- `GET http://127.0.0.1:8000/api/v1/version` — version info
- `POST http://127.0.0.1:8000/api/v1/chat` — send a message, get an Ollama reply

### Chat

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

Response:

```json
{
  "response": "...",
  "model": "llama3.2",
  "timestamp": "2026-07-11T12:00:00+00:00"
}
```

## Configuration

All configuration is via environment variables with the `JARVIS_` prefix (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `JARVIS_APP_NAME` | `Jarvis` | Application name |
| `JARVIS_ENVIRONMENT` | `development` | `development` \| `staging` \| `production` |
| `JARVIS_DEBUG` | `true` | FastAPI debug mode |
| `JARVIS_LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL` |
| `JARVIS_LOG_FORMAT` | `console` | `console` (colorized, dev) \| `json` (structured, prod) |
| `OLLAMA_HOST` | `http://localhost:11434` | Base URL of the local Ollama server |
| `OLLAMA_MODEL` | `llama3.2` | Default model for text generation |

## Architecture

```
src/jarvis/
├── core/               # Module 1 — config & logging (no HTTP dependency)
│   ├── config.py       # Settings via pydantic-settings, get_settings() DI provider
│   └── logging.py      # structlog configured over stdlib logging
├── providers/          # Module 3 — external service clients
│   └── ollama.py       # OllamaClient: health_check, generate, list_models
├── services/           # Module 4 — business logic
│   └── chat.py         # ChatService: message → Ollama → reply
├── api/                # Module 2 — FastAPI foundation
│   ├── app.py           # create_app() factory + lifespan events
│   ├── middleware.py     # Request ID + Request Logging middleware
│   ├── exceptions.py     # Global exception handlers
│   └── v1/
│       ├── router.py     # Aggregates all /api/v1 routes
│       ├── health.py     # GET /health, GET /version
│       └── chat.py       # POST /chat
└── main.py              # ASGI entrypoint (uvicorn target)
```

**Principles:**
- **Application factory** (`create_app`) instead of a module-level `app` — every test builds its own isolated instance.
- **Dependency injection**: `Settings` is retrieved via `Depends(get_settings)`, never read from `os.environ` directly in route handlers.
- **Structured logging everywhere**: every request gets a correlation ID (`X-Request-ID`) bound into the log context, and third-party library logs (uvicorn, httpx, etc.) are routed through the same structlog pipeline.
- **Consistent error shape**: all errors — validation failures, HTTP exceptions, unhandled exceptions — return `{"error": "...", "detail": ...}` and are logged with full context.
- **API versioning**: all routes live under `/api/v1`; a future `/api/v2` would be a sibling package, leaving `v1` untouched.

## Testing

```bash
uv run pytest -v
```

Test layout mirrors source layout:

```
tests/
├── test_config.py          # Module 1
├── test_logging.py         # Module 1
├── providers/              # Module 3
│   └── test_ollama.py
├── services/               # Module 4
│   └── test_chat.py
└── api/                    # Module 2
    ├── conftest.py          # shared fixtures (settings, TestClient)
    ├── test_health.py
    ├── test_version.py
    ├── test_chat.py
    ├── test_middleware.py
    └── test_exception_handlers.py
```

See `CHANGELOG.md` for a per-module history of what was added and why.
