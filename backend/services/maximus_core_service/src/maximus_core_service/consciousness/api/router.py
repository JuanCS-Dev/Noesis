"""Main Router - Assembles all consciousness API endpoints."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter

from maximus_core_service.consciousness.prometheus_metrics import get_metrics_handler

from .esgt_endpoints import register_esgt_endpoints
from .helpers import APIState
from .reactive_endpoints import register_reactive_endpoints
from .safety_endpoints import register_safety_endpoints
from .state_endpoints import register_state_endpoints
from .streaming import create_background_broadcaster, register_streaming_endpoints


def create_consciousness_api(consciousness_system: dict[str, Any]) -> APIRouter:
    """Create consciousness API router with all endpoints.

    Args:
        consciousness_system: Dictionary containing consciousness components.
                            Can be empty dict at router creation time - will be populated
                            by set_consciousness_components() after system initialization.

    Returns:
        Configured APIRouter with all endpoints.
    """
    from . import get_consciousness_dict
    
    router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])
    api_state = APIState()
    background_tasks: list[asyncio.Task[None]] = []

    # FIX: Use getter to access global dict (populated after initialization)
    # If consciousness_system is provided (legacy), use it; otherwise use global
    actual_system = consciousness_system if consciousness_system else get_consciousness_dict()

    # Register all endpoint groups
    register_state_endpoints(router, actual_system, api_state)
    register_esgt_endpoints(router, actual_system, api_state)
    register_safety_endpoints(router, actual_system)
    register_reactive_endpoints(router, actual_system)
    register_streaming_endpoints(router, actual_system, api_state)

    # Prometheus metrics
    router.add_route("/metrics", get_metrics_handler(), methods=["GET"])

    # Background tasks
    broadcaster = create_background_broadcaster(consciousness_system, api_state)

    @router.on_event("startup")
    async def _start_background_tasks() -> None:
        background_tasks.append(asyncio.create_task(broadcaster()))

    @router.on_event("shutdown")
    async def _stop_background_tasks() -> None:
        for task in background_tasks:
            task.cancel()
        background_tasks.clear()

    return router
