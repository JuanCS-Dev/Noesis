"""
Reactive Fabric Core - Event Models
===================================

Pydantic models for reactive events.
"""

from __future__ import annotations


from datetime import datetime
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types in reactive system."""

    SYSTEM = "system"
    USER = "user"
    ALERT = "alert"
    STATE_CHANGE = "state_change"


class EventPriority(str, Enum):
    """Event priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReactiveEvent(BaseModel):
    """
    Reactive event representation.

    Attributes:
        event_id: Unique event identifier
        event_type: Type of event
        priority: Event priority
        source: Event source identifier
        payload: Event payload data
        timestamp: Event creation timestamp
        metadata: Additional event metadata
    """

    event_id: str = Field(..., description="Event identifier")
    event_type: EventType = Field(..., description="Event type")
    priority: EventPriority = Field(
        default=EventPriority.MEDIUM,
        description="Event priority"
    )
    source: str = Field(..., description="Event source")
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Creation timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
