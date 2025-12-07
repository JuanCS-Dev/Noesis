"""Streaming Endpoints - WebSocket and SSE for real-time updates.

AURORA STREAMING: Real-time consciousness processing for hackathon-winning UI.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from .helpers import APIState

if TYPE_CHECKING:
    from maximus_core_service.consciousness.system import ConsciousnessSystem

# MAXIMUS: Global reference to consciousness system (set by main.py)
_maximus_consciousness_system: "ConsciousnessSystem | None" = None


def set_maximus_consciousness_system(system: "ConsciousnessSystem") -> None:
    """Set the consciousness system for MAXIMUS streaming.

    Called by main.py after system initialization.
    """
    global _maximus_consciousness_system
    _maximus_consciousness_system = system


def get_maximus_consciousness_system() -> "ConsciousnessSystem | None":
    """Get the consciousness system for MAXIMUS streaming."""
    return _maximus_consciousness_system


def register_streaming_endpoints(
    router: APIRouter,
    consciousness_system: dict[str, Any],
    api_state: APIState,
) -> None:
    """Register streaming endpoints (WebSocket and SSE)."""

    async def _sse_event_stream(
        request: Request, queue: asyncio.Queue[dict[str, Any]]
    ) -> AsyncGenerator[bytes, None]:
        """SSE generator transmitting events while connection is active."""
        heartbeat_interval = 15.0
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(
                        queue.get(), timeout=heartbeat_interval
                    )
                except asyncio.TimeoutError:
                    message = {
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                    }
                yield f"data: {json.dumps(message)}\n\n".encode("utf-8")
        finally:
            if queue in api_state.sse_subscribers:
                api_state.sse_subscribers.remove(queue)

    @router.get("/stream/sse")
    async def stream_sse(request: Request) -> StreamingResponse:
        """SSE endpoint for cockpit and React frontend."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=250)
        api_state.sse_subscribers.append(queue)
        queue.put_nowait(
            {
                "type": "connection_ack",
                "timestamp": datetime.now().isoformat(),
                "recent_events": len(api_state.event_history),
            }
        )
        return StreamingResponse(
            _sse_event_stream(request, queue), media_type="text/event-stream"
        )

    @router.get("/stream/process")
    async def stream_process_input(
        request: Request,
        content: str = Query(..., description="User input to process"),
        depth: int = Query(3, ge=1, le=5, description="Analysis depth (1-5)"),
    ) -> StreamingResponse:
        """
        AURORA STREAMING: Process input with real-time ESGT phase streaming.

        This endpoint connects the React frontend to real consciousness processing,
        streaming events as they happen:

        - `start`: Processing initiated
        - `phase`: ESGT phase transition (prepare → synchronize → broadcast → sustain → dissolve)
        - `coherence`: Kuramoto coherence updates during synchronization
        - `token`: Response narrative tokens (word by word)
        - `complete`: Processing finished
        - `error`: Error occurred

        Args:
            content: User input text to process
            depth: Analysis depth (1=shallow, 5=deep introspection)

        Returns:
            SSE stream with consciousness events
        """
        async def _process_event_stream() -> AsyncGenerator[bytes, None]:
            """Generate SSE events from consciousness processing."""
            # Get consciousness system from MAXIMUS global reference
            system = get_maximus_consciousness_system()

            if not system:
                error_event = {
                    "type": "error",
                    "message": "Consciousness system not available",
                    "timestamp": datetime.now().isoformat(),
                }
                yield f"data: {json.dumps(error_event)}\n\n".encode("utf-8")
                return

            try:
                # Stream events from consciousness processing
                async for event in system.process_input_streaming(content, depth):
                    if await request.is_disconnected():
                        break
                    yield f"data: {json.dumps(event)}\n\n".encode("utf-8")

            except Exception as e:
                error_event = {
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                yield f"data: {json.dumps(error_event)}\n\n".encode("utf-8")

        return StreamingResponse(
            _process_event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "X-Accel-Buffering": "no",
            },
        )

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time consciousness state streaming."""
        await websocket.accept()
        api_state.active_connections.append(websocket)
        try:
            esgt = consciousness_system.get("esgt")
            arousal = consciousness_system.get("arousal")
            if arousal:
                arousal_state = arousal.get_current_arousal()
                await websocket.send_json(
                    {
                        "type": "initial_state",
                        "arousal": arousal_state.arousal if arousal_state else 0.5,
                        "events_count": len(api_state.event_history),
                        "esgt_active": (
                            bool(esgt._running)
                            if esgt and hasattr(esgt, "_running")
                            else False
                        ),
                    }
                )
            while True:
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )
                except TimeoutError:
                    await websocket.send_json(
                        {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
                    )
        except WebSocketDisconnect:
            if websocket in api_state.active_connections:
                api_state.active_connections.remove(websocket)
        except Exception:
            if websocket in api_state.active_connections:
                api_state.active_connections.remove(websocket)


def create_background_broadcaster(
    consciousness_system: dict[str, Any],
    api_state: APIState,
) -> Any:
    """Create periodic state broadcast task."""

    async def _periodic_state_broadcast() -> None:
        """Send periodic state snapshot to consumers."""
        while True:
            await asyncio.sleep(5.0)
            try:
                if not consciousness_system:
                    continue
                arousal = consciousness_system.get("arousal")
                esgt = consciousness_system.get("esgt")
                arousal_state = (
                    arousal.get_current_arousal()
                    if arousal and hasattr(arousal, "get_current_arousal")
                    else None
                )
                await api_state.broadcast_to_consumers(
                    {
                        "type": "state_snapshot",
                        "timestamp": datetime.now().isoformat(),
                        "arousal": getattr(arousal_state, "arousal", None),
                        "esgt_active": getattr(esgt, "_running", False),
                        "events_count": len(api_state.event_history),
                    }
                )
            except Exception:
                continue

    return _periodic_state_broadcast
