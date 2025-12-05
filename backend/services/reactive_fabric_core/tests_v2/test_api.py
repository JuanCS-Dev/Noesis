"""
Unit tests for Reactive Fabric Core API (V2).
"""

from __future__ import annotations


from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.services.reactive_fabric_core.api.dependencies import get_event_bus
from backend.services.reactive_fabric_core.core.event_bus import EventBus
from backend.services.reactive_fabric_core.main_v2 import app
from backend.services.reactive_fabric_core.models.events import (
    EventType,
    ReactiveEvent
)

client = TestClient(app)


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "V2" in response.json()["message"]


@pytest.mark.asyncio
async def test_publish_event() -> None:
    """Test publish event endpoint."""
    # Mock event bus
    mock_bus = AsyncMock(spec=EventBus)

    app.dependency_overrides[get_event_bus] = lambda: mock_bus

    event_data = {
        "event_id": "test-1",
        "event_type": "system",
        "source": "test"
    }

    response = client.post("/v1/events", json=event_data)

    assert response.status_code == 200
    assert response.json()["status"] == "published"

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_events() -> None:
    """Test get events endpoint."""
    # Mock event bus
    mock_bus = AsyncMock(spec=EventBus)
    mock_events = [
        ReactiveEvent(
            event_id="test-1",
            event_type=EventType.SYSTEM,
            source="test"
        )
    ]
    mock_bus.get_events.return_value = mock_events

    app.dependency_overrides[get_event_bus] = lambda: mock_bus

    response = client.get("/v1/events")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["event_id"] == "test-1"

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_clear_events() -> None:
    """Test clear events endpoint."""
    # Mock event bus
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.clear_events.return_value = 10

    app.dependency_overrides[get_event_bus] = lambda: mock_bus

    response = client.delete("/v1/events")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cleared"
    assert data["count"] == 10

    # Reset overrides
    app.dependency_overrides = {}
