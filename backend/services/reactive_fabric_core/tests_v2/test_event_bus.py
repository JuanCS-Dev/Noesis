"""
Unit tests for EventBus.
"""

from __future__ import annotations


import pytest

from backend.services.reactive_fabric_core.config import ReactiveSettings
from backend.services.reactive_fabric_core.core.event_bus import EventBus
from backend.services.reactive_fabric_core.models.events import (
    EventPriority,
    EventType,
    ReactiveEvent
)


@pytest.fixture(name="settings")
def fixture_settings() -> ReactiveSettings:
    """Reactive settings fixture."""
    return ReactiveSettings(max_events=10, event_ttl=3600)


@pytest.fixture(name="event_bus")
def fixture_event_bus(settings: ReactiveSettings) -> EventBus:
    """Event bus fixture."""
    return EventBus(settings)


@pytest.mark.asyncio
async def test_publish_event(event_bus: EventBus) -> None:
    """Test publishing an event."""
    event = ReactiveEvent(
        event_id="test-1",
        event_type=EventType.SYSTEM,
        source="test",
        priority=EventPriority.HIGH
    )

    await event_bus.publish(event)

    assert len(event_bus.events) == 1
    assert event_bus.events[0].event_id == "test-1"


@pytest.mark.asyncio
async def test_get_events(event_bus: EventBus) -> None:
    """Test getting events from buffer."""
    events_to_publish = [
        ReactiveEvent(
            event_id=f"test-{i}",
            event_type=EventType.USER,
            source="test"
        )
        for i in range(5)
    ]

    for event in events_to_publish:
        await event_bus.publish(event)

    retrieved = await event_bus.get_events()

    assert len(retrieved) == 5


@pytest.mark.asyncio
async def test_get_events_with_limit(event_bus: EventBus) -> None:
    """Test getting events with limit."""
    for i in range(10):
        event = ReactiveEvent(
            event_id=f"test-{i}",
            event_type=EventType.ALERT,
            source="test"
        )
        await event_bus.publish(event)

    retrieved = await event_bus.get_events(limit=3)

    assert len(retrieved) == 3


@pytest.mark.asyncio
async def test_event_buffer_overflow(event_bus: EventBus) -> None:
    """Test event buffer overflow handling."""
    # Publish more than max_events
    for i in range(15):
        event = ReactiveEvent(
            event_id=f"test-{i}",
            event_type=EventType.SYSTEM,
            source="test"
        )
        await event_bus.publish(event)

    # Should keep only last 10
    assert len(event_bus.events) == 10
    assert event_bus.events[0].event_id == "test-5"


@pytest.mark.asyncio
async def test_clear_events(event_bus: EventBus) -> None:
    """Test clearing event buffer."""
    for i in range(5):
        event = ReactiveEvent(
            event_id=f"test-{i}",
            event_type=EventType.USER,
            source="test"
        )
        await event_bus.publish(event)

    count = await event_bus.clear_events()

    assert count == 5
    assert len(event_bus.events) == 0


@pytest.mark.asyncio
async def test_subscribe(event_bus: EventBus) -> None:
    """Test subscribing to events."""
    received_events = []

    def callback(event: ReactiveEvent) -> None:
        received_events.append(event)

    subscription_id = await event_bus.subscribe(callback)

    assert subscription_id is not None
    assert len(event_bus.subscribers) == 1

    # Publish event
    event = ReactiveEvent(
        event_id="test-1",
        event_type=EventType.ALERT,
        source="test"
    )
    await event_bus.publish(event)

    # Check callback was called
    assert len(received_events) == 1
    assert received_events[0].event_id == "test-1"
