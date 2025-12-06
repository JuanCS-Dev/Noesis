"""
Prefrontal Cortex Service - API Routes
======================================

FastAPI endpoints for executive cognitive functions.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from prefrontal_cortex_service.core.decision_engine import DecisionEngine
from prefrontal_cortex_service.core.task_prioritizer import TaskPrioritizer
from prefrontal_cortex_service.models.cognitive import Decision, Task, TaskStatus
from prefrontal_cortex_service.api.dependencies import get_decision_engine, get_task_prioritizer

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check() -> dict[str, str]:
    """
    Service health check.

    Returns:
        Basic health status
    """
    return {"status": "healthy", "service": "prefrontal-cortex-service"}


@router.post("/decide", response_model=Decision)
async def make_decision(
    context: Dict[str, Any],
    options: List[str],
    engine: DecisionEngine = Depends(get_decision_engine)
) -> Decision:
    """
    Make a decision based on context and options.

    Args:
        context: Decision context
        options: Available options
        engine: Decision engine instance

    Returns:
        Decision with selected option
    """
    return await engine.make_decision(context, options)


@router.post("/tasks", response_model=bool)
async def add_task(
    task: Task,
    prioritizer: TaskPrioritizer = Depends(get_task_prioritizer)
) -> bool:
    """
    Add a task to the queue.

    Args:
        task: Task to add
        prioritizer: Task prioritizer instance

    Returns:
        True if task was added
    """
    return await prioritizer.add_task(task)


@router.get("/tasks", response_model=List[Task])
async def get_tasks(
    prioritizer: TaskPrioritizer = Depends(get_task_prioritizer)
) -> List[Task]:
    """
    Get prioritized task list.

    Args:
        prioritizer: Task prioritizer instance

    Returns:
        List of tasks sorted by priority
    """
    return await prioritizer.get_prioritized_tasks()


@router.patch("/tasks/{task_id}", response_model=bool)
async def update_task(
    task_id: str,
    status: TaskStatus,
    prioritizer: TaskPrioritizer = Depends(get_task_prioritizer)
) -> bool:
    """
    Update task status.

    Args:
        task_id: Task identifier
        status: New status
        prioritizer: Task prioritizer instance

    Returns:
        True if updated
    """
    return await prioritizer.update_task_status(task_id, status)
