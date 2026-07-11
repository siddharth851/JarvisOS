"""ASGI entrypoint.

Run with: `uv run uvicorn jarvis.main:app --reload`
"""

from jarvis.api.app import create_app

app = create_app()
