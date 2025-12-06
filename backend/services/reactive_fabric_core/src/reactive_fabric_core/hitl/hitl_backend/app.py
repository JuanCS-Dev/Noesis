"""HITL Backend - FastAPI Application.

Main application setup with routers and middleware.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_current_user, router as auth_router
from .database import db
from .decisions import router as decisions_router
from .models import DecisionPriority, UserInDB
from .websocket_routes import router as websocket_router

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="HITL Console API",
    description="Human-in-the-Loop Decision System for Reactive Fabric",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(decisions_router)
app.include_router(websocket_router)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "HITL Console Backend",
    }


@app.get("/api/status")
async def get_status(
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get system status."""
    pending_decisions = db.get_pending_decisions()

    return {
        "timestamp": datetime.now().isoformat(),
        "pending_decisions": len(pending_decisions),
        "critical_pending": len(
            [d for d in pending_decisions if d.priority == DecisionPriority.CRITICAL]
        ),
        "total_users": len(db.users),
        "total_decisions": len(db.decisions),
        "total_responses": len(db.responses),
    }


@app.on_event("startup")
async def startup_event() -> None:
    """Application startup."""
    logger.info("=" * 60)
    logger.info("HITL Console Backend Starting...")
    logger.info("=" * 60)
    logger.info("Default Admin: username='admin', password='ChangeMe123!'")
    logger.info("API Docs: http://localhost:8000/api/docs")
    logger.info("=" * 60)


@app.on_event("startup")
async def start_background_tasks() -> None:
    """Start background tasks."""
    try:
        from ..websocket_manager import heartbeat_task
    except ImportError:
        from websocket_manager import heartbeat_task

    asyncio.create_task(heartbeat_task())
    logger.info("Background tasks started")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("HITL_PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
