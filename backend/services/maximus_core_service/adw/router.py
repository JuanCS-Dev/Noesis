"""
ADW Main Router.

Central router that combines all ADW endpoint routers.

Author: MAXIMUS Team
Date: 2025-10-15
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from .endpoints_defensive import get_defensive_status
from .endpoints_defensive import router as defensive_router
from .endpoints_offensive import get_offensive_status
from .endpoints_offensive import router as offensive_router
from .endpoints_osint import router as osint_router
from .endpoints_purple import get_purple_metrics
from .endpoints_purple import router as purple_router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/adw", tags=["AI-Driven Workflows"])

# Include sub-routers
router.include_router(offensive_router)
router.include_router(defensive_router)
router.include_router(purple_router)
router.include_router(osint_router)


@router.get("/overview")
async def get_adw_overview() -> dict[str, Any]:
    """Get unified overview of all AI-Driven Workflows.

    Combines status from Offensive, Defensive, and Purple Team systems
    into single comprehensive view for MAXIMUS AI dashboard.

    Returns:
        Dict with complete ADW system status
    """
    try:
        # Fetch all statuses in parallel
        offensive, defensive, purple = await asyncio.gather(
            get_offensive_status(), get_defensive_status(), get_purple_metrics()
        )

        # Determine overall status
        statuses = [
            offensive.get("status"),
            defensive.get("status"),
            purple.get("status"),
        ]

        overall_status = "operational"
        if any(s in ["degraded", "offline"] for s in statuses):
            overall_status = "degraded"
        if all(s == "offline" for s in statuses):
            overall_status = "offline"

        return {
            "system": "ai_driven_workflows",
            "status": overall_status,
            "offensive": offensive,
            "defensive": defensive,
            "purple": purple,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching ADW overview: {e}")
        raise HTTPException(
            status_code=500, detail=f"Overview query failed: {str(e)}"
        )


@router.get("/health")
async def adw_health_check() -> dict[str, str]:
    """ADW system health check endpoint.

    Returns:
        Dict with health status
    """
    return {"status": "healthy", "message": "AI-Driven Workflows operational"}
