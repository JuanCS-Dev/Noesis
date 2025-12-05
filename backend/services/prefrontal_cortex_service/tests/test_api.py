"""
Unit tests for Prefrontal Cortex Service API.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from api.dependencies import (
    get_decision_engine,
    get_task_prioritizer,
    initialize_service
)
from core.decision_engine import DecisionEngine
from core.task_prioritizer import TaskPrioritizer
from main import app
from models.cognitive import Decision, Task, TaskPriority, TaskStatus

# Initialize service before creating client
initialize_service()
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
async def test_make_decision() -> None:
    """Test make decision endpoint."""
    # Mock decision engine
    mock_engine = AsyncMock(spec=DecisionEngine)
    mock_decision = Decision(
        decision_id="test-123",
        context={"test": "context"},
        options=["option1", "option2"],
        selected_option="option1",
        confidence=0.8,
        reasoning="Test reasoning"
    )
    mock_engine.make_decision.return_value = mock_decision

    app.dependency_overrides[get_decision_engine] = lambda: mock_engine

    response = client.post(
        "/v1/decide",
        json={
            "context": {"test": "context"},
            "options": ["option1", "option2"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["selected_option"] == "option1"
    assert data["confidence"] == 0.8

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_add_task() -> None:
    """Test add task endpoint."""
    # Mock task prioritizer
    mock_prioritizer = AsyncMock(spec=TaskPrioritizer)
    mock_prioritizer.add_task.return_value = True

    app.dependency_overrides[get_task_prioritizer] = lambda: mock_prioritizer

    task_data = {
        "task_id": "test-task",
        "description": "Test task",
        "priority": "high",
        "status": "pending"
    }

    response = client.post("/v1/tasks", json=task_data)
    assert response.status_code == 200
    assert response.json() is True

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_tasks() -> None:
    """Test get tasks endpoint."""
    # Mock task prioritizer
    mock_prioritizer = AsyncMock(spec=TaskPrioritizer)
    mock_tasks = [
        Task(
            task_id="task1",
            description="Task 1",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING
        )
    ]
    mock_prioritizer.get_prioritized_tasks.return_value = mock_tasks

    app.dependency_overrides[get_task_prioritizer] = lambda: mock_prioritizer

    response = client.get("/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_id"] == "task1"

    # Reset overrides
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_update_task() -> None:
    """Test update task endpoint."""
    # Mock task prioritizer
    mock_prioritizer = AsyncMock(spec=TaskPrioritizer)
    mock_prioritizer.update_task_status.return_value = True

    app.dependency_overrides[get_task_prioritizer] = lambda: mock_prioritizer

    response = client.patch(
        "/v1/tasks/task1",
        params={"status": "completed"}
    )
    assert response.status_code == 200
    assert response.json() is True

    # Reset overrides
    app.dependency_overrides = {}
