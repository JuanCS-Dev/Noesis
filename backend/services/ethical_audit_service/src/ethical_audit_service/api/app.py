"""Ethical Audit Service - FastAPI Application Setup.

This module provides the FastAPI application with all routers integrated.
Decomposes the monolithic 2770-line api.py into modular routers.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from ethical_audit_service.database import EthicalAuditDatabase

from .routers import (
    audit_router,
    certification_router,
    compliance_logs_router,
    fairness_router,
    federated_router,
    health_router,
    hitl_router,
    metrics_router,
    privacy_router,
    xai_router,
)
from .state import set_db, set_limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# CORS configuration
ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8080,http://localhost:4200",
).split(",")

TRUSTED_HOSTS = os.getenv(
    "TRUSTED_HOSTS", "localhost,127.0.0.1,ethical-audit,ethical_audit_service"
).split(",")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="VÉRTICE Ethical Audit Service",
        version="2.0.0",
        description="Comprehensive audit logging and analytics for AI ethical decisions",
    )

    # Add rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    set_limiter(limiter)

    # Add CORS middleware
    logger.info("CORS allowed origins: %s", ALLOWED_ORIGINS)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Add trusted host middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)

    # Include all routers
    app.include_router(health_router)
    app.include_router(audit_router)
    app.include_router(compliance_logs_router)
    app.include_router(metrics_router)
    app.include_router(xai_router)
    app.include_router(fairness_router)
    app.include_router(privacy_router)
    app.include_router(federated_router)
    app.include_router(hitl_router)
    app.include_router(certification_router)

    return app


# Create the application instance
app = create_app()

# Database client
db: Optional[EthicalAuditDatabase] = None


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database connection and schema on startup."""
    global db  # noqa: PLW0603
    logger.info("Starting Ethical Audit Service...")

    db = EthicalAuditDatabase()
    await db.connect()
    await db.initialize_schema()
    set_db(db)

    logger.info("Ethical Audit Service ready")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean shutdown of database connections."""
    global db  # noqa: PLW0603
    logger.info("Shutting down Ethical Audit Service...")

    if db:
        await db.disconnect()

    logger.info("Ethical Audit Service stopped")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8612)
