"""
Unit tests for Maximus Core Service API.
"""

from __future__ import annotations


from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.services.maximus_core_service.api.dependencies import (
    get_coordinator,
    get_health_aggregator
)
from backend.services.maximus_core_service.core.coordinator import SystemCoordinator
from backend.services.maximus_core_service.core.health_aggregator import (
    HealthAggregator
)
from backend.services.maximus_core_service.main import app
from backend.services.maximus_core_service.models.system import (
    ServiceHealth,
    SystemStatus
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
    assert "Operational" in response.json()["message"]


@pytest.mark.asyncio
async def test_get_system_status() -> None:
    """Test get system status endpoint."""
    # Mock health aggregator
    mock_aggregator = AsyncMock(spec=HealthAggregator)
    mock_status = SystemStatus(
        status="healthy",
        timestamp="2023-01-01T00:00:00",
        services={},
        total_services=0,
        healthy_services=0
    )
    mock_aggregator.get_system_status.return_value = mock_status

    app.dependency_overrides[get_health_aggregator] = lambda: mock_aggregator

    response = client.get("/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_registered_services() -> None:
    """Test get registered services endpoint."""
    # Mock coordinator
    mock_coordinator = AsyncMock(spec=SystemCoordinator)
    mock_coordinator.get_registered_services.return_value = [
        "service-1",
        "service-2"
    ]

    app.dependency_overrides[get_coordinator] = lambda: mock_coordinator

    response = client.get("/v1/services")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "service-1" in data

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_register_service() -> None:
    """Test register service endpoint."""
    # Mock coordinator
    mock_coordinator = AsyncMock(spec=SystemCoordinator)

    app.dependency_overrides[get_coordinator] = lambda: mock_coordinator

    response = client.post("/v1/services/test-service/register")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "registered"
    assert data["service"] == "test-service"

    #  Verify coordinator was called
    mock_coordinator.register_service.assert_called_once_with("test-service")

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_unregister_service() -> None:
    """Test unregister service endpoint."""
    # Mock coordinator
    mock_coordinator = AsyncMock(spec=SystemCoordinator)

    app.dependency_overrides[get_coordinator] = lambda: mock_coordinator

    response = client.delete("/v1/services/test-service")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unregistered"
    assert data["service"] == "test-service"

    # Verify coordinator was called
    mock_coordinator.unregister_service.assert_called_once_with("test-service")

    # Reset overrides
    app.dependency_overrides = {}
