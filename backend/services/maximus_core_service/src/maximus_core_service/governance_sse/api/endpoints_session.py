"""
Session Management Endpoints.

Endpoints for creating and managing operator sessions.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, status
from maximus_core_service.hitl import OperatorInterface

from .models import SessionCreateRequest, SessionCreateResponse

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def create_session_router(
    operator_interface: OperatorInterface,
) -> APIRouter:
    """Create router for session management endpoints."""
    router = APIRouter()

    @router.post("/session/create", response_model=SessionCreateResponse)
    async def create_session(request: SessionCreateRequest):
        """Create new operator session."""
        try:
            session = operator_interface.create_session(
                operator_id=request.operator_id,
                operator_name=request.operator_name,
                operator_role=request.operator_role,
                ip_address=request.ip_address,
                user_agent=request.user_agent,
            )

            return SessionCreateResponse(
                session_id=session.session_id,
                operator_id=session.operator_id,
                expires_at=session.expires_at.isoformat() if session.expires_at else "",
            )

        except Exception as e:
            logger.error(f"Session creation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create session: {str(e)}",
            )

    return router
