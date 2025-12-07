"""Goal Generation Models - Data structures for autonomous goal generation."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GoalType(Enum):
    """Classification of goal types."""

    # Homeostatic (deficit-reduction)
    REST = "rest"  # Reduce computational load
    REPAIR = "repair"  # Fix errors, restore integrity
    OPTIMIZE = "optimize"  # Improve efficiency
    RESTORE = "restore"  # Restore connectivity/communication
    # Growth (exploration/expansion)
    EXPLORE = "explore"  # Explore new capabilities
    LEARN = "learn"  # Acquire new patterns
    CREATE = "create"  # Generate novel outputs


class GoalPriority(Enum):
    """Goal priority levels."""

    BACKGROUND = 0  # Optional, non-urgent
    LOW = 1  # Should do eventually
    MODERATE = 2  # Should do soon
    HIGH = 3  # Important, do quickly
    CRITICAL = 4  # Urgent, do immediately


@dataclass
class Goal:
    """Autonomous goal generated from internal needs."""

    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal_type: GoalType = GoalType.REST
    priority: GoalPriority = GoalPriority.LOW

    description: str = ""
    target_component: str | None = None

    source_need: str = ""
    need_value: float = 0.0

    target_need_value: float = 0.3
    timeout_seconds: float = 300.0

    created_at: float = field(default_factory=time.time)
    satisfied_at: float | None = None
    is_active: bool = True

    execution_attempts: int = 0
    last_execution_at: float | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if goal has timed out."""
        if not self.is_active:
            return False
        return (time.time() - self.created_at) > self.timeout_seconds

    def is_satisfied(self, current_need_value: float) -> bool:
        """Check if goal satisfied based on current need value."""
        return current_need_value < self.target_need_value

    def mark_satisfied(self) -> None:
        """Mark goal as satisfied."""
        self.satisfied_at = time.time()
        self.is_active = False

    def record_execution_attempt(self) -> None:
        """Record that goal execution was attempted."""
        self.execution_attempts += 1
        self.last_execution_at = time.time()

    def get_age_seconds(self) -> float:
        """Get goal age in seconds."""
        return time.time() - self.created_at

    def get_priority_score(self) -> float:
        """Get numeric priority score for sorting. Higher = more urgent."""
        base_score = self.priority.value * 100.0
        need_bonus = self.need_value * 50.0
        age_penalty = min(self.get_age_seconds() / self.timeout_seconds, 1.0) * 20.0
        return base_score + need_bonus - age_penalty

    def __repr__(self) -> str:
        status = "ACTIVE" if self.is_active else "SATISFIED"
        return f"Goal({self.goal_type.value}, priority={self.priority.value}, status={status}, need={self.need_value:.2f})"


@dataclass
class GoalGenerationConfig:
    """Configuration for autonomous goal generation."""

    # Generation thresholds
    rest_threshold: float = 0.60
    repair_threshold: float = 0.40
    efficiency_threshold: float = 0.50
    connectivity_threshold: float = 0.50
    curiosity_threshold: float = 0.60
    learning_threshold: float = 0.50

    # Satisfaction thresholds
    rest_satisfied: float = 0.30
    repair_satisfied: float = 0.20
    efficiency_satisfied: float = 0.30
    connectivity_satisfied: float = 0.30

    # Timeouts (seconds)
    default_timeout: float = 300.0
    critical_timeout: float = 600.0
    exploration_timeout: float = 120.0

    # Limits
    max_concurrent_goals: int = 10
    min_goal_interval_seconds: float = 5.0
