"""Health and version endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from jarvis import __version__
from jarvis.core.config import Environment, Settings, get_settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    """Response body for `GET /health`."""

    status: str = Field(default="healthy")
    version: str
    environment: Environment
    timestamp: datetime


class VersionResponse(BaseModel):
    """Response body for `GET /version`."""

    version: str
    app_name: str
    environment: Environment


@router.get("/health", response_model=HealthResponse)
async def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Report service health, current version, and environment."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )


@router.get("/version", response_model=VersionResponse)
async def get_version(settings: Settings = Depends(get_settings)) -> VersionResponse:
    """Report application version information."""
    return VersionResponse(
        version=__version__,
        app_name=settings.app_name,
        environment=settings.environment,
    )
