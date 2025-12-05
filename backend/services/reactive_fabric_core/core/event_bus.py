"""
Reactive Fabric Core - Event Bus
=================================

Simple event bus for reactive event handling.
"""

from __future__ import annotations


from typing import Callable, List
import uuid

from ..config import ReactiveSettings
from ..models.events import ReactiveEvent
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class EventBus:
    """
    Simple in-memory event bus with publish/subscribe pattern.

    Attributes:
        settings: Reactive settings
        events: Event buffer
        subscribers: Event subscribers
    """

    def __init__(self, settings: ReactiveSettings):
        """
        Initialize Event Bus.

        Args:
            settings: Reactive settings
        """
        self.settings = settings
        self.events: List[ReactiveEvent] = []
        self.subscribers: List[Callable[[ReactiveEvent], None]] = []
        logger.info(
            "event_bus_initialized",
            max_events=settings.max_events
        )

    async def publish(self, event: ReactiveEvent) -> None:
        """
        Publish event to bus.

        Args:
            event: Event to publish
        """
        # Add to event buffer
        self.events.append(event)

        # Trim buffer if needed
        if len(self.events) > self.settings.max_events:
            self.events = self.events[-self.settings.max_events:]

        # Notify subscribers
        for subscriber in self.subscribers:
            try:
                subscriber(event)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "subscriber_error",
                    event_id=event.event_id,
                    error=str(exc)
                )

        logger.info(
            "event_published",
            event_id=event.event_id,
            event_type=event.event_type.value,
            priority=event.priority.value
        )

    async def subscribe(
        self,
        callback: Callable[[ReactiveEvent], None]
    ) -> str:
        """
        Subscribe to events.

        Args:
            callback: Callback function for events

        Returns:
            Subscription ID
        """
        self.subscribers.append(callback)
        subscription_id = str(uuid.uuid4())

        logger.info(
            "subscriber_added",
            subscription_id=subscription_id,
            total_subscribers=len(self.subscribers)
        )

        return subscription_id

    async def get_events(
        self,
        limit: int | None = None
    ) -> List[ReactiveEvent]:
        """
        Get recent events from buffer.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        if limit is None or limit > len(self.events):
            return list(self.events)

        return list(self.events[-limit:])

    async def clear_events(self) -> int:
        """
        Clear event buffer.

        Returns:
            Number of events cleared
        """
        count = len(self.events)
        self.events.clear()

        logger.info("events_cleared", count=count)
        return count
