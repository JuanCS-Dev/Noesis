"""
Governance API Routes Factory.

Creates the main Governance API router by combining all endpoint routers.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from maximus_core_service.hitl import DecisionQueue, OperatorInterface

from ..event_broadcaster import EventBroadcaster
from ..sse_server import GovernanceSSEServer
from .endpoints_decision import create_decision_router
from .endpoints_session import create_session_router
from .endpoints_stats import create_stats_router
from .endpoints_streaming import create_streaming_router

logger = logging.getLogger(__name__)


def create_governance_api(
    decision_queue: DecisionQueue,
    operator_interface: OperatorInterface,
    sse_server: GovernanceSSEServer | None = None,
    event_broadcaster: EventBroadcaster | None = None,
) -> APIRouter:
    """
    Create FastAPI router for Governance API.

    Args:
        decision_queue: HITL DecisionQueue instance
        operator_interface: HITL OperatorInterface instance
        sse_server: GovernanceSSEServer instance (created if None)
        event_broadcaster: EventBroadcaster instance (created if None)

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/governance", tags=["governance"])

    # Initialize SSE server if not provided
    if sse_server is None:
        sse_server = GovernanceSSEServer(
            decision_queue=decision_queue,
            poll_interval=1.0,
            heartbeat_interval=30,
        )
        logger.info("Created new GovernanceSSEServer instance")

    # Initialize event broadcaster if not provided
    if event_broadcaster is None:
        event_broadcaster = EventBroadcaster(sse_server.connection_manager)
        logger.info("Created new EventBroadcaster instance")

    # Include sub-routers
    router.include_router(
        create_streaming_router(decision_queue, operator_interface, sse_server)
    )
    router.include_router(
        create_stats_router(decision_queue, operator_interface, sse_server)
    )
    router.include_router(create_session_router(operator_interface))
    router.include_router(
        create_decision_router(
            decision_queue, operator_interface, sse_server, event_broadcaster
        )
    )

    logger.info("Governance API routes configured")
    return router
