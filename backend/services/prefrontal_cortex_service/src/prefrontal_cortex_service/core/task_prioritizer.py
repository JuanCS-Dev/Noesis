"""
Prefrontal Cortex Service - Task Prioritizer
============================================

Task prioritization and scheduling logic.
"""

from __future__ import annotations

from typing import Dict, List

from prefrontal_cortex_service.config import CognitiveSettings
from prefrontal_cortex_service.models.cognitive import Task, TaskPriority, TaskStatus
from prefrontal_cortex_service.utils.logging_config import get_logger

logger = get_logger(__name__)


class TaskPrioritizer:
    """
    Prioritizes and manages cognitive tasks.

    Attributes:
        settings: Cognitive settings
        tasks: Active task list
    """

    def __init__(self, settings: CognitiveSettings):
        """
        Initialize Task Prioritizer.

        Args:
            settings: Cognitive settings
        """
        self.settings = settings
        self.tasks: Dict[str, Task] = {}
        logger.info(
            "task_prioritizer_initialized",
            max_tasks=settings.max_tasks
        )

    async def add_task(self, task: Task) -> bool:
        """
        Add a task to the queue.

        Args:
            task: Task to add

        Returns:
            True if task was added, False if queue is full
        """
        if len(self.tasks) >= self.settings.max_tasks:
            logger.warning(
                "task_queue_full",
                current_count=len(self.tasks),
                max_tasks=self.settings.max_tasks
            )
            return False

        self.tasks[task.task_id] = task
        logger.info(
            "task_added",
            task_id=task.task_id,
            priority=task.priority.value
        )
        return True

    async def get_prioritized_tasks(self) -> List[Task]:
        """
        Get tasks ordered by priority.

        Returns:
            List of tasks sorted by priority (highest first)
        """
        priority_order = {
            TaskPriority.CRITICAL: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1
        }

        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: priority_order.get(t.priority, 0),
            reverse=True
        )

        return sorted_tasks

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus
    ) -> bool:
        """
        Update task status.

        Args:
            task_id: Task identifier
            status: New status

        Returns:
            True if updated, False if task not found
        """
        if task_id not in self.tasks:
            logger.warning("task_not_found", task_id=task_id)
            return False

        self.tasks[task_id].status = status
        logger.info(
            "task_status_updated",
            task_id=task_id,
            status=status.value
        )
        return True

    async def remove_completed_tasks(self) -> int:
        """
        Remove completed tasks from queue.

        Returns:
            Number of tasks removed
        """
        initial_count = len(self.tasks)
        self.tasks = {
            tid: task for tid, task in self.tasks.items()
            if task.status != TaskStatus.COMPLETED
        }
        removed = initial_count - len(self.tasks)

        if removed > 0:
            logger.info("completed_tasks_removed", count=removed)

        return removed
