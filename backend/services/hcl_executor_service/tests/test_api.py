"""
Unit tests for HCL Executor API.
"""

from typing import Generator
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from backend.services.hcl_executor_service.main import app
from backend.services.hcl_executor_service.core.executor import ActionExecutor

client = TestClient(app)

@pytest.fixture(name="mock_executor")
def fixture_mock_executor() -> Generator[AsyncMock, None, None]:
    """Mock executor fixture."""
    with patch("backend.services.hcl_executor_service.api.dependencies.ActionExecutor") as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance

def test_health_check(mock_executor: AsyncMock) -> None:  # pylint: disable=unused-argument
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics() -> None:
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "executor_active 1" in response.text

@pytest.mark.asyncio
async def test_execute_endpoint(mock_executor: AsyncMock) -> None:  # pylint: disable=unused-argument
    """Test execute endpoint."""
    # Mock dependency injection
    async def override_get_executor() -> AsyncMock:
        mock = AsyncMock(spec=ActionExecutor)
        mock.execute_actions.return_value = [{
            "action_type": "scale_deployment",
            "status": "success",
            "details": "Scaled",
            "timestamp": 123.456
        }]
        return mock

    from backend.services.hcl_executor_service.api.dependencies import get_executor  # pylint: disable=import-outside-toplevel
    app.dependency_overrides[get_executor] = override_get_executor

    payload = {
        "plan_id": "plan-1",
        "actions": [{
            "type": "scale_deployment",
            "parameters": {
                "deployment_name": "test",
                "replicas": 3
            }
        }]
    }

    # The payload structure is now correct for ExecuteRequest
    response = client.post("/v1/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "success"

@pytest.mark.asyncio
async def test_status_endpoint(mock_executor: AsyncMock) -> None:  # pylint: disable=unused-argument
    """Test status endpoint."""
    async def override_get_executor() -> AsyncMock:
        mock = AsyncMock(spec=ActionExecutor)
        mock.get_status.return_value = {"status": "active"}
        return mock

    from backend.services.hcl_executor_service.api.dependencies import get_executor  # pylint: disable=import-outside-toplevel
    app.dependency_overrides[get_executor] = override_get_executor

    response = client.get("/v1/status")
    assert response.status_code == 200
    assert response.json()["status"] == "active"
