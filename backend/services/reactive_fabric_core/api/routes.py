"""
Reactive Fabric Core - API Routes
=================================

FastAPI endpoints for reactive event system.
"""

from __future__ import annotations


from typing import List

from fastapi import APIRouter, Depends

from ..core.event_bus import EventBus
from ..models.events import ReactiveEvent
from .dependencies import get_event_bus

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check() -> dict[str, str]:
    """
    Service health check.

    Returns:
        Basic health status
    """
    return {"status": "healthy", "service": "reactive-fabric-core"}


@router.post("/events", response_model=dict)
async def publish_event(
    event: ReactiveEvent,
    event_bus: EventBus = Depends(get_event_bus)
) -> dict[str, str]:
    """
    Publish event to bus.

    Args:
        event: Event to publish
        event_bus: Event bus instance

    Returns:
        Publication confirmation
    """
    await event_bus.publish(event)
    return {"status": "published", "event_id": event.event_id}


@router.get("/events", response_model=List[ReactiveEvent])
async def get_events(
    limit: int | None = None,
    event_bus: EventBus = Depends(get_event_bus)
) -> List[ReactiveEvent]:
    """
    Get recent events from buffer.

    Args:
        limit: Maximum number of events
        event_bus: Event bus instance

    Returns:
        List of events
    """
    return await event_bus.get_events(limit)


@router.delete("/events", response_model=dict)
async def clear_events(
    event_bus: EventBus = Depends(get_event_bus)
) -> dict[str, str | int]:
    """
    Clear event buffer.

    Args:
        event_bus: Event bus instance

    Returns:
        Clear confirmation with count
    """
    count = await event_bus.clear_events()
    return {"status": "cleared", "count": count}
