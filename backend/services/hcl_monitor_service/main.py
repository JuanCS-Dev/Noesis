"""
HCL Monitor Service - Main Application
======================================

Entry point for the HCL Monitor Service.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from api.dependencies import get_collector, initialize_service
from api.routes import router as api_router
from config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan.
    """
    # Startup
    initialize_service()
    collector = await get_collector()
    await collector.start_collection()

    yield

    # Shutdown
    await collector.stop_collection()


app = FastAPI(
    title=settings.service.name,  # pylint: disable=no-member
    description="HCL Monitor Service (Agentic)",
    version="2.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "HCL Monitor Service Operational",
        "service": settings.service.name  # pylint: disable=no-member
    }
