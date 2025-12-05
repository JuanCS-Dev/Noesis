"""
Unit tests for Digital Thalamus Service API.
"""

from __future__ import annotations


from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_router
from core.router import RequestRouter
from main import app
from models.gateway import RouteConfig

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
async def test_get_routes() -> None:
    """Test get routes endpoint."""
    # Mock router
    mock_router = AsyncMock(spec=RequestRouter)
    mock_router.routes = {
        "/v1/test": RouteConfig(
            service_name="test-service",
            base_url="http://test:8000",
            timeout=30.0
        )
    }

    app.dependency_overrides[get_router] = lambda: mock_router

    response = client.get("/v1/routes")
    assert response.status_code == 200
    data = response.json()
    assert "/v1/test" in data

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_find_route() -> None:
    """Test find route endpoint."""
    # Mock router
    mock_router = AsyncMock(spec=RequestRouter)
    mock_route = RouteConfig(
        service_name="test-service",
        base_url="http://test:8000",
        timeout=30.0
    )
    mock_router.find_route.return_value = mock_route

    app.dependency_overrides[get_router] = lambda: mock_router

    response = client.get("/v1/routes/v1/test")
    assert response.status_code == 200
    data = response.json()
    assert data["service_name"] == "test-service"

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_find_route_not_found() -> None:
    """Test find route endpoint with no match."""
    # Mock router
    mock_router = AsyncMock(spec=RequestRouter)
    mock_router.find_route.return_value = None

    app.dependency_overrides[get_router] = lambda: mock_router

    response = client.get("/v1/routes/nonexistent")
    assert response.status_code == 404

    # Reset overrides
    app.dependency_overrides = {}
