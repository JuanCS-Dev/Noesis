"""
Reactive Fabric Core - Main Application (V2)
============================================

Entry point for refactored Reactive Fabric service.
"""

from __future__ import annotations


from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .api.dependencies import initialize_service
from .api.routes import router as api_router
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

    yield

    # Shutdown (cleanup if needed)


app = FastAPI(
    title=settings.service.name,  # pylint: disable=no-member
    description="Reactive Fabric Core - Event Bus System (V2)",
    version="2.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns:
        Service information
    """
    return {
        "message": "Reactive Fabric Core V2 Operational",
        "service": settings.service.name  # pylint: disable=no-member
    }
