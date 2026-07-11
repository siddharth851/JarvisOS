"""Aggregates all `/api/v1` routes.

Future v1 route modules (chat, memory, browser, etc.) register here via
`include_router`. This is the single seam Module 3+ plugs into — the
application factory only ever imports this one router for v1.
"""

from fastapi import APIRouter

from jarvis.api.v1.chat import router as chat_router
from jarvis.api.v1.health import router as health_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(chat_router)
