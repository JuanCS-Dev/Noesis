"""
SSE Streaming Endpoints.

Server-Sent Events for real-time decision streaming.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from hitl import DecisionQueue, DecisionStatus, OperatorInterface

from ..sse_server import GovernanceSSEServer, SSEEvent

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def create_streaming_router(
    decision_queue: DecisionQueue,
    operator_interface: OperatorInterface,
    sse_server: GovernanceSSEServer,
) -> APIRouter:
    """Create router for SSE streaming endpoints."""
    router = APIRouter()

    @router.get("/stream/{operator_id}")
    async def stream_governance_events(
        operator_id: str,
        session_id: str = Query(..., description="Active session ID"),
    ):
        """Stream governance events via Server-Sent Events.

        This endpoint provides real-time streaming of pending HITL decisions
        to the operator's TUI.
        """
        # Validate session
        session = operator_interface.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired session: {session_id}",
            )

        if session.operator_id != operator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator ID does not match session",
            )

        logger.info(
            f"SSE stream started for operator {operator_id} (session={session_id})"
        )

        async def event_generator():
            """Generate SSE events."""
            try:
                async for sse_event in sse_server.stream_decisions(
                    operator_id, session_id
                ):
                    yield sse_event.to_sse_format()

            except Exception as e:
                logger.error(f"SSE stream error for {operator_id}: {e}", exc_info=True)
                error_event = SSEEvent(
                    event_type="error",
                    event_id=f"error_{datetime.now(UTC).timestamp()}",
                    timestamp=datetime.now(UTC).isoformat(),
                    data={"error": str(e), "message": "Stream error occurred"},
                )
                yield error_event.to_sse_format()

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @router.get("/decision/{decision_id}/watch")
    async def watch_decision(decision_id: str):
        """Watch a specific decision via SSE stream.

        Provides real-time updates about a specific decision,
        streaming status changes until the decision is resolved.
        """
        logger.info(f"SSE watch stream started for decision {decision_id}")

        async def decision_watch_generator():
            """Generate SSE events for a specific decision."""
            try:
                # Verify decision exists
                decision = decision_queue.get_decision(decision_id)
                if decision is None:
                    error_event = SSEEvent(
                        event_type="error",
                        event_id=f"error_{datetime.now(UTC).timestamp()}",
                        timestamp=datetime.now(UTC).isoformat(),
                        data={"error": "Decision not found", "decision_id": decision_id},
                    )
                    yield error_event.to_sse_format()
                    return

                # Send initial status
                initial_event = SSEEvent(
                    event_type="decision_status",
                    event_id=f"status_{datetime.now(UTC).timestamp()}",
                    timestamp=datetime.now(UTC).isoformat(),
                    data={
                        "decision_id": decision_id,
                        "status": decision.status.value,
                        "risk_level": decision.risk_level.value,
                        "created_at": decision.created_at.isoformat(),
                    },
                )
                yield initial_event.to_sse_format()

                # Poll for status changes
                last_status = decision.status
                poll_count = 0
                max_polls = 600  # 10 minutes at 1s intervals

                while poll_count < max_polls:
                    await asyncio.sleep(1.0)
                    poll_count += 1

                    decision = decision_queue.get_decision(decision_id)

                    if decision is None:
                        resolved_event = SSEEvent(
                            event_type="decision_resolved",
                            event_id=f"resolved_{datetime.now(UTC).timestamp()}",
                            timestamp=datetime.now(UTC).isoformat(),
                            data={
                                "decision_id": decision_id,
                                "status": "completed",
                                "message": "Decision has been resolved and archived",
                            },
                        )
                        yield resolved_event.to_sse_format()
                        break

                    if decision.status != last_status:
                        status_event = SSEEvent(
                            event_type="decision_status",
                            event_id=f"status_{datetime.now(UTC).timestamp()}",
                            timestamp=datetime.now(UTC).isoformat(),
                            data={
                                "decision_id": decision_id,
                                "status": decision.status.value,
                                "previous_status": last_status.value,
                            },
                        )
                        yield status_event.to_sse_format()
                        last_status = decision.status

                        if decision.status != DecisionStatus.PENDING:
                            resolved_event = SSEEvent(
                                event_type="decision_resolved",
                                event_id=f"resolved_{datetime.now(UTC).timestamp()}",
                                timestamp=datetime.now(UTC).isoformat(),
                                data={
                                    "decision_id": decision_id,
                                    "status": decision.status.value,
                                    "resolved_at": (
                                        decision.resolved_at.isoformat()
                                        if decision.resolved_at
                                        else None
                                    ),
                                    "resolved_by": decision.resolved_by,
                                },
                            )
                            yield resolved_event.to_sse_format()
                            break

                    if poll_count % 30 == 0:
                        heartbeat_event = SSEEvent(
                            event_type="heartbeat",
                            event_id=f"heartbeat_{datetime.now(UTC).timestamp()}",
                            timestamp=datetime.now(UTC).isoformat(),
                            data={"decision_id": decision_id, "watching": True},
                        )
                        yield heartbeat_event.to_sse_format()

            except Exception as e:
                logger.error(
                    f"SSE watch stream error for {decision_id}: {e}", exc_info=True
                )
                error_event = SSEEvent(
                    event_type="error",
                    event_id=f"error_{datetime.now(UTC).timestamp()}",
                    timestamp=datetime.now(UTC).isoformat(),
                    data={"error": str(e), "message": "Stream error occurred"},
                )
                yield error_event.to_sse_format()

        return StreamingResponse(
            decision_watch_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return router
