"""
MIP FastAPI Application.

Main application factory and lifecycle events.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .endpoints_abtest import router as abtest_router
from .endpoints_core import router as core_router
from .endpoints_precedents import router as precedents_router
from .state import cbr_engine, evaluation_count, frameworks

logger = logging.getLogger(__name__)


def create_mip_app() -> FastAPI:
    """Create and configure the MIP FastAPI application."""
    application = FastAPI(
        title="Motor de Integridade Processual (MIP)",
        description="Ethical evaluation engine for MAXIMUS AI",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Include routers
    application.include_router(core_router)
    application.include_router(precedents_router)
    application.include_router(abtest_router)

    # Exception handlers
    @application.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions with consistent format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @application.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "status_code": 500,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    # Lifecycle events
    @application.on_event("startup")
    async def startup_event() -> None:
        """Initialize service on startup."""
        logger.info("=== MIP Service Starting ===")
        logger.info(f"Frameworks loaded: {len(frameworks)}")
        logger.info(f"Frameworks: {[f.value for f in frameworks.keys()]}")
        logger.info(f"CBR Engine: {'Active' if cbr_engine else 'Disabled'}")
        logger.info("=== MIP Service Ready ===")

    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        """Cleanup on shutdown."""
        logger.info("=== MIP Service Shutting Down ===")
        logger.info(f"Total evaluations performed: {evaluation_count}")
        logger.info("=== MIP Service Stopped ===")

    return application


# Default app instance
app = create_mip_app()
