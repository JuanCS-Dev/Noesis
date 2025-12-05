"""
Unit tests for HCL Planner API.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from main import app
from core.planner import AgenticPlanner
from api.dependencies import get_planner

client = TestClient(app)


@pytest.fixture(name="mock_planner")
def fixture_mock_planner():
    """Mock planner fixture."""
    with patch("api.dependencies.AgenticPlanner") as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance


def test_health_check(mock_planner):  # pylint: disable=unused-argument
    """Test health check endpoint."""
    # Mock dependency injection
    app.dependency_overrides = {}  # Reset

    async def override_get_planner():
        mock = AsyncMock(spec=AgenticPlanner)
        mock.get_status.return_value = {"status": "active", "model": "test"}
        return mock

    app.dependency_overrides[get_planner] = override_get_planner

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["planner"]["status"] == "active"


def test_metrics():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "planner_active 1" in response.text


@pytest.mark.asyncio
async def test_generate_plan_endpoint():
    """Test plan generation endpoint."""
    async def override_get_planner():
        mock = AsyncMock(spec=AgenticPlanner)
        mock.recommend_actions.return_value = [{"type": "scale_up"}]
        return mock

    app.dependency_overrides[get_planner] = override_get_planner

    payload = {
        "current_state": {"cpu": 0.9},
        "analysis_result": {"status": "critical"},
        "operational_goals": {"target": 0.7}
    }

    response = client.post("/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "plan_id" in data
    assert len(data["actions"]) == 1
    assert data["actions"][0]["type"] == "scale_up"
