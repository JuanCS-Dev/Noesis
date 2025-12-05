"""
Maximus Core Service - Main Application
=======================================

Entry point for the Maximus Core Service.
"""

from __future__ import annotations


from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .api.dependencies import initialize_service
from .api.routes import router as api_router
from .src.consciousness.exocortex.api.exocortex_router import router as exocortex_router
from .src.consciousness.exocortex.factory import ExocortexFactory
from .config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan.

    Args:
        _: FastAPI application instance (unused)

    Yields:
        None during application lifetime
    """
    # Startup
    initialize_service()
    ExocortexFactory.initialize(data_dir=str(settings.base_path / ".data"))

    yield

    # Shutdown (cleanup if needed)


app = FastAPI(
    title=settings.service.name,  # pylint: disable=no-member
    description="Maximus Core Service - System Coordination",
    version="2.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/v1")
app.include_router(exocortex_router, prefix="/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns:
        Service information
    """
    return {
        "message": "Maximus Core Service Operational",
        "service": settings.service.name  # pylint: disable=no-member
    }
