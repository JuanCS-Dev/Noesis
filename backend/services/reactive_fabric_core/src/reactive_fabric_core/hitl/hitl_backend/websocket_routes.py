"""HITL Backend - WebSocket Routes.

Real-time WebSocket endpoint for alerts and subscriptions.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from .auth import get_current_user
from .models import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Import WebSocket manager from parent module
try:
    from ..websocket_manager import AlertType, manager
except ImportError:
    from websocket_manager import AlertType, manager


@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str) -> None:
    """WebSocket endpoint for real-time alerts."""
    try:
        token = None
        if hasattr(websocket, "query_params"):
            token = websocket.query_params.get("token")

        if token:
            import jwt

            secret_key = os.getenv("JWT_SECRET_KEY", "vertice-secret-key")

            try:
                payload = jwt.decode(token, secret_key, algorithms=["HS256"])

                if payload.get("username") != username:
                    await websocket.close(code=1008, reason="Username mismatch")
                    return

                logger.info("JWT validated for user: %s", username)

            except jwt.ExpiredSignatureError:
                await websocket.close(code=1008, reason="Token expired")
                return
            except jwt.InvalidTokenError:
                await websocket.close(code=1008, reason="Invalid token")
                return
        else:
            logger.warning("No JWT token provided for %s, allowing in dev mode", username)

    except Exception as e:
        logger.error("JWT validation error: %s", e)

    await manager.connect(websocket, username)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                alert_types = {AlertType(t) for t in data.get("alert_types", [])}
                manager.subscribe(username, alert_types)

                await manager.send_personal_message(
                    {"type": "subscribed", "alert_types": [t.value for t in alert_types]},
                    websocket,
                )

            elif data.get("type") == "unsubscribe":
                alert_types = {AlertType(t) for t in data.get("alert_types", [])}
                manager.unsubscribe(username, alert_types)

                await manager.send_personal_message(
                    {"type": "unsubscribed", "alert_types": [t.value for t in alert_types]},
                    websocket,
                )

            elif data.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()},
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket disconnected: %s", username)


@router.get("/api/ws/stats")
async def get_websocket_stats(
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get WebSocket connection statistics."""
    return manager.get_stats()
