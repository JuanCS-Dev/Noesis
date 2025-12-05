"""
Unit tests for TaskPrioritizer.
"""

from __future__ import annotations

import pytest

from backend.services.prefrontal_cortex_service.config import CognitiveSettings
from backend.services.prefrontal_cortex_service.core.task_prioritizer import (
    TaskPrioritizer
)
from backend.services.prefrontal_cortex_service.models.cognitive import (
    Task,
    TaskPriority,
    TaskStatus
)


@pytest.fixture(name="settings")
def fixture_settings() -> CognitiveSettings:
    """Cognitive settings fixture."""
    return CognitiveSettings(decision_timeout=10.0, max_tasks=3)


@pytest.fixture(name="prioritizer")
def fixture_prioritizer(settings: CognitiveSettings) -> TaskPrioritizer:
    """Task prioritizer fixture."""
    return TaskPrioritizer(settings)


@pytest.mark.asyncio
async def test_add_task(prioritizer: TaskPrioritizer) -> None:
    """Test adding a task."""
    task = Task(task_id="task1", description="Test task")
    result = await prioritizer.add_task(task)

    assert result is True
    assert "task1" in prioritizer.tasks


@pytest.mark.asyncio
async def test_add_task_queue_full(prioritizer: TaskPrioritizer) -> None:
    """Test adding task when queue is full."""
    # Add tasks up to max
    for i in range(3):
        task = Task(task_id=f"task{i}", description=f"Task {i}")
        await prioritizer.add_task(task)

    # Try to add one more
    extra_task = Task(task_id="extra", description="Extra task")
    result = await prioritizer.add_task(extra_task)

    assert result is False
    assert "extra" not in prioritizer.tasks


@pytest.mark.asyncio
async def test_get_prioritized_tasks(prioritizer: TaskPrioritizer) -> None:
    """Test getting prioritized tasks."""
    tasks_data = [
        ("task1", TaskPriority.LOW),
        ("task2", TaskPriority.CRITICAL),
        ("task3", TaskPriority.MEDIUM)
    ]

    for task_id, priority in tasks_data:
        task = Task(task_id=task_id, description=f"Task {task_id}", priority=priority)
        await prioritizer.add_task(task)

    sorted_tasks = await prioritizer.get_prioritized_tasks()

    assert sorted_tasks[0].task_id == "task2"  # CRITICAL first
    assert sorted_tasks[1].task_id == "task3"  # MEDIUM second
    assert sorted_tasks[2].task_id == "task1"  # LOW last


@pytest.mark.asyncio
async def test_update_task_status(prioritizer: TaskPrioritizer) -> None:
    """Test updating task status."""
    task = Task(task_id="task1", description="Test task")
    await prioritizer.add_task(task)

    result = await prioritizer.update_task_status("task1", TaskStatus.IN_PROGRESS)

    assert result is True
    assert prioritizer.tasks["task1"].status == TaskStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_update_nonexistent_task(prioritizer: TaskPrioritizer) -> None:
    """Test updating nonexistent task."""
    result = await prioritizer.update_task_status("nonexistent", TaskStatus.COMPLETED)

    assert result is False


@pytest.mark.asyncio
async def test_remove_completed_tasks(prioritizer: TaskPrioritizer) -> None:
    """Test removing completed tasks."""
    # Add tasks
    task1 = Task(task_id="task1", description="Task 1")
    task2 = Task(task_id="task2", description="Task 2")
    await prioritizer.add_task(task1)
    await prioritizer.add_task(task2)

    # Mark one as completed
    await prioritizer.update_task_status("task1", TaskStatus.COMPLETED)

    # Remove completed
    removed = await prioritizer.remove_completed_tasks()

    assert removed == 1
    assert "task1" not in prioritizer.tasks
    assert "task2" in prioritizer.tasks
