"""
HCL Executor Service - Entry Point
==================================

FastAPI application for the HCL Executor Service.
Exposes endpoints for executing infrastructure actions.
"""

from typing import Dict, Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from .config import get_settings
from .api.routes import router as api_router
from .api.dependencies import initialize_service

# Initialize settings
settings = get_settings()

app = FastAPI(
    title=settings.service.name,  # pylint: disable=no-member
    description="HCL Executor Service (Agentic)",
    version="2.0.0"
)

# Include API routes
app.include_router(api_router, prefix="/v1")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize service on startup."""
    initialize_service()


@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Service health check.

    Returns:
        Health status dictionary.
    """
    return {
        "status": "healthy",
        "service": settings.service.name,  # pylint: disable=no-member
    }


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    """
    Prometheus metrics.

    Returns:
        PlainTextResponse with metrics.
    """
    return PlainTextResponse("# HCL Executor Metrics\nexecutor_active 1\n")


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "HCL Executor Service (Agentic) Operational"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
