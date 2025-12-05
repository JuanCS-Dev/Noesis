"""API Helpers - Shared utilities for consciousness API."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastapi import WebSocket


class APIState:
    """Shared state for API endpoints."""

    MAX_HISTORY = 100

    def __init__(self) -> None:
        """Initialize API state."""
        self.active_connections: list[WebSocket] = []
        self.sse_subscribers: list[asyncio.Queue[dict[str, Any]]] = []
        self.event_history: list[dict[str, Any]] = []

    def add_event_to_history(self, event: Any) -> None:
        """Add ESGT event to history."""
        event_dict = (
            asdict(event) if hasattr(event, "__dataclass_fields__") else dict(event)
        )
        event_dict["timestamp"] = datetime.now().isoformat()
        self.event_history.append(event_dict)
        if len(self.event_history) > self.MAX_HISTORY:
            self.event_history.pop(0)

    async def broadcast_to_consumers(self, message: dict[str, Any]) -> None:
        """Broadcast message to WebSockets and SSE subscribers."""
        dead_connections: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for connection in dead_connections:
            self.active_connections.remove(connection)

        if self.sse_subscribers:
            serialized = message | {
                "timestamp": message.get("timestamp", datetime.now().isoformat())
            }
            for queue in list(self.sse_subscribers):
                try:
                    queue.put_nowait(serialized)
                except asyncio.QueueFull:
                    try:
                        queue.get_nowait()
                        queue.put_nowait(serialized)
                    except (asyncio.QueueEmpty, asyncio.QueueFull):
                        continue
