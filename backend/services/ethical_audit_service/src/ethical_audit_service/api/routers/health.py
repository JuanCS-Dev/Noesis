"""Health & Status Endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from ..state import get_db

router = APIRouter(prefix="/audit", tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    db = get_db()
    return {
        "status": "healthy",
        "service": "ethical_audit_service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db and db.pool else "disconnected",
    }


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """Detailed service status with database stats."""
    db = get_db()
    if not db or not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    async with db.pool.acquire() as conn:
        decisions_count = await conn.fetchval("SELECT COUNT(*) FROM ethical_decisions")
        overrides_count = await conn.fetchval("SELECT COUNT(*) FROM human_overrides")
        compliance_count = await conn.fetchval("SELECT COUNT(*) FROM compliance_logs")
        latest_decision = await conn.fetchval("SELECT MAX(timestamp) FROM ethical_decisions")

    return {
        "service": "ethical_audit_service",
        "status": "operational",
        "database": {
            "connected": True,
            "pool_size": db.pool.get_size(),
            "decisions_logged": decisions_count,
            "overrides_logged": overrides_count,
            "compliance_checks": compliance_count,
            "latest_decision": latest_decision.isoformat() if latest_decision else None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
