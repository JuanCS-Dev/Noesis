"""
Prefrontal Cortex Service - Cognitive Models
============================================

Pydantic models for executive cognitive functions.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task status types."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """
    Cognitive task representation.

    Attributes:
        task_id: Unique task identifier
        description: Task description
        priority: Task priority level
        status: Current task status
        created_at: Task creation timestamp
        metadata: Additional task metadata
    """

    task_id: str = Field(..., description="Task identifier")
    description: str = Field(..., description="Task description")
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Task priority"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Task status"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Creation timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class Decision(BaseModel):
    """
    Decision representation.

    Attributes:
        decision_id: Unique decision identifier
        context: Decision context information
        options: Available decision options
        selected_option: Selected option
        confidence: Confidence level (0.0 to 1.0)
        reasoning: Decision reasoning
        timestamp: Decision timestamp
    """

    decision_id: str = Field(..., description="Decision identifier")
    context: Dict[str, Any] = Field(..., description="Decision context")
    options: List[str] = Field(..., description="Available options")
    selected_option: str | None = Field(
        default=None,
        description="Selected option"
    )
    confidence: float = Field(
        default=0.5,
        description="Confidence level",
        ge=0.0,
        le=1.0
    )
    reasoning: str | None = Field(
        default=None,
        description="Decision reasoning"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Decision timestamp"
    )
