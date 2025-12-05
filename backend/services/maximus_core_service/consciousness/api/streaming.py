"""Streaming Endpoints - WebSocket and SSE for real-time updates."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from .helpers import APIState


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
