"""
Autonomous Goal Generation - Need-Based Motivation.

Translates internal needs into actionable goals:
- rest_need > 0.8     → "reduce_computational_load" (CRITICAL)
- repair_need > 0.6   → "diagnose_and_repair_errors" (HIGH)
- efficiency_need > 0.5 → "optimize_resource_usage" (MODERATE)
- connectivity_need > 0.7 → "restore_network_connectivity" (HIGH)
- curiosity_drive > 0.6 → "explore_idle_capacity" (LOW)

Goals flow into execution systems: Needs → Goals → HCL → Actions
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from maximus_core_service.consciousness.mmei.goals_models import Goal, GoalGenerationConfig, GoalPriority, GoalType
from maximus_core_service.consciousness.mmei.monitor import AbstractNeeds, NeedUrgency


class AutonomousGoalGenerator:
    """
    Generates autonomous goals from internal needs.

    The motivational engine - translating phenomenal "feelings" (needs)
    into actionable intentions (goals).
    """

    def __init__(
        self,
        config: GoalGenerationConfig | None = None,
        generator_id: str = "mmei-goal-generator-primary",
    ) -> None:
        self.generator_id = generator_id
        self.config = config or GoalGenerationConfig()

        self._active_goals: list[Goal] = []
        self._completed_goals: list[Goal] = []
        self._expired_goals: list[Goal] = []
        self._last_generation: dict[str, float] = {}
        self._goal_consumers: list[Callable[[Goal], None]] = []

        self.total_goals_generated: int = 0
        self.total_goals_satisfied: int = 0
        self.total_goals_expired: int = 0

    def register_goal_consumer(self, consumer: Callable[[Goal], None]) -> None:
        """Register callback to receive generated goals."""
        self._goal_consumers.append(consumer)

    def generate_goals(self, needs: AbstractNeeds) -> list[Goal]:
        """Generate autonomous goals from current needs."""
        new_goals: list[Goal] = []

        self._update_active_goals(needs)

        if len(self._active_goals) >= self.config.max_concurrent_goals:
            return new_goals

        # REST NEED
        if needs.rest_need >= self.config.rest_threshold and self._should_generate("rest_need"):
            goal = self._create_rest_goal(needs.rest_need)
            new_goals.append(goal)
            self._last_generation["rest_need"] = time.time()

        # REPAIR NEED
        if needs.repair_need >= self.config.repair_threshold and self._should_generate(
            "repair_need"
        ):
            goal = self._create_repair_goal(needs.repair_need)
            new_goals.append(goal)
            self._last_generation["repair_need"] = time.time()

        # EFFICIENCY NEED
        if needs.efficiency_need >= self.config.efficiency_threshold and self._should_generate(
            "efficiency_need"
        ):
            goal = self._create_efficiency_goal(needs.efficiency_need)
            new_goals.append(goal)
            self._last_generation["efficiency_need"] = time.time()

        # CONNECTIVITY NEED
        if needs.connectivity_need >= self.config.connectivity_threshold and self._should_generate(
            "connectivity_need"
        ):
            goal = self._create_connectivity_goal(needs.connectivity_need)
            new_goals.append(goal)
            self._last_generation["connectivity_need"] = time.time()

        # CURIOSITY DRIVE
        if needs.curiosity_drive >= self.config.curiosity_threshold and self._should_generate(
            "curiosity_drive"
        ):
            goal = self._create_exploration_goal(needs.curiosity_drive)
            new_goals.append(goal)
            self._last_generation["curiosity_drive"] = time.time()

        # LEARNING DRIVE
        if needs.learning_drive >= self.config.learning_threshold and self._should_generate(
            "learning_drive"
        ):
            goal = self._create_learning_goal(needs.learning_drive)
            new_goals.append(goal)
            self._last_generation["learning_drive"] = time.time()

        self._active_goals.extend(new_goals)
        self.total_goals_generated += len(new_goals)

        for goal in new_goals:
            self._notify_consumers(goal)

        return new_goals

    def _should_generate(self, need_name: str) -> bool:
        """Check if enough time passed since last goal generation for this need."""
        if need_name not in self._last_generation:
            return True
        elapsed = time.time() - self._last_generation[need_name]
        return elapsed >= self.config.min_goal_interval_seconds

    def _update_active_goals(self, needs: AbstractNeeds) -> None:
        """Update active goals - check satisfaction and expiration."""
        still_active: list[Goal] = []

        for goal in self._active_goals:
            if goal.is_expired():
                goal.is_active = False
                self._expired_goals.append(goal)
                self.total_goals_expired += 1
                continue

            current_need = self._get_need_value(needs, goal.source_need)

            if goal.is_satisfied(current_need):
                goal.mark_satisfied()
                self._completed_goals.append(goal)
                self.total_goals_satisfied += 1
                continue

            still_active.append(goal)

        self._active_goals = still_active

    def _get_need_value(self, needs: AbstractNeeds, need_name: str) -> float:
        """Get current value of specific need."""
        return getattr(needs, need_name, 0.0)

    def _classify_priority(self, need_value: float) -> GoalPriority:
        """Classify goal priority based on need urgency."""
        urgency = self._classify_urgency(need_value)
        mapping = {
            NeedUrgency.SATISFIED: GoalPriority.BACKGROUND,
            NeedUrgency.LOW: GoalPriority.LOW,
            NeedUrgency.MODERATE: GoalPriority.MODERATE,
            NeedUrgency.HIGH: GoalPriority.HIGH,
            NeedUrgency.CRITICAL: GoalPriority.CRITICAL,
        }
        return mapping[urgency]

    def _classify_urgency(self, need_value: float) -> NeedUrgency:
        """Classify need urgency."""
        if need_value < 0.20:
            return NeedUrgency.SATISFIED
        if need_value < 0.40:
            return NeedUrgency.LOW
        if need_value < 0.60:
            return NeedUrgency.MODERATE
        if need_value < 0.80:
            return NeedUrgency.HIGH
        return NeedUrgency.CRITICAL

    def _create_rest_goal(self, need_value: float) -> Goal:
        """Create goal to reduce computational load."""
        priority = self._classify_priority(need_value)
        return Goal(
            goal_type=GoalType.REST,
            priority=priority,
            description="Reduce computational load to recover from fatigue",
            target_component="cpu_scheduler",
            source_need="rest_need",
            need_value=need_value,
            target_need_value=self.config.rest_satisfied,
            timeout_seconds=(
                self.config.critical_timeout
                if priority == GoalPriority.CRITICAL
                else self.config.default_timeout
            ),
            metadata={
                "actions": ["reduce_thread_count", "defer_background_tasks", "enter_low_power_mode"]
            },
        )

    def _create_repair_goal(self, need_value: float) -> Goal:
        """Create goal to diagnose and repair errors."""
        priority = self._classify_priority(need_value)
        return Goal(
            goal_type=GoalType.REPAIR,
            priority=priority,
            description="Diagnose and repair system errors",
            target_component="error_handler",
            source_need="repair_need",
            need_value=need_value,
            target_need_value=self.config.repair_satisfied,
            timeout_seconds=self.config.critical_timeout,
            metadata={"actions": ["run_diagnostics", "apply_fixes", "verify_integrity"]},
        )

    def _create_efficiency_goal(self, need_value: float) -> Goal:
        """Create goal to optimize resource usage."""
        priority = self._classify_priority(need_value)
        return Goal(
            goal_type=GoalType.OPTIMIZE,
            priority=priority,
            description="Optimize resource usage and efficiency",
            target_component="resource_manager",
            source_need="efficiency_need",
            need_value=need_value,
            target_need_value=self.config.efficiency_satisfied,
            timeout_seconds=self.config.default_timeout,
            metadata={
                "actions": ["enable_thermal_throttling", "optimize_power_profile", "cache_warming"]
            },
        )

    def _create_connectivity_goal(self, need_value: float) -> Goal:
        """Create goal to restore network connectivity."""
        priority = self._classify_priority(need_value)
        return Goal(
            goal_type=GoalType.RESTORE,
            priority=priority,
            description="Restore network connectivity and reduce latency",
            target_component="network_manager",
            source_need="connectivity_need",
            need_value=need_value,
            target_need_value=self.config.connectivity_satisfied,
            timeout_seconds=self.config.critical_timeout,
            metadata={
                "actions": ["check_network_health", "reconnect_dropped_links", "optimize_routing"]
            },
        )

    def _create_exploration_goal(self, need_value: float) -> Goal:
        """Create goal to explore idle capacity."""
        return Goal(
            goal_type=GoalType.EXPLORE,
            priority=GoalPriority.LOW,
            description="Explore idle computational capacity",
            target_component="exploration_engine",
            source_need="curiosity_drive",
            need_value=need_value,
            target_need_value=0.0,
            timeout_seconds=self.config.exploration_timeout,
            metadata={"actions": ["run_benchmarks", "test_new_algorithms", "profile_performance"]},
        )

    def _create_learning_goal(self, need_value: float) -> Goal:
        """Create goal to acquire new patterns."""
        return Goal(
            goal_type=GoalType.LEARN,
            priority=GoalPriority.LOW,
            description="Acquire new patterns and improve models",
            target_component="learning_engine",
            source_need="learning_drive",
            need_value=need_value,
            target_need_value=0.0,
            timeout_seconds=self.config.exploration_timeout,
            metadata={"actions": ["analyze_recent_data", "update_models", "identify_patterns"]},
        )

    def _notify_consumers(self, goal: Goal) -> None:
        """Notify all registered consumers of new goal."""
        for consumer in self._goal_consumers:
            try:
                consumer(goal)
            except Exception as e:
                logger.info("⚠️  Goal consumer error: %s", e)

    def get_active_goals(self, sort_by_priority: bool = True) -> list[Goal]:
        """Get all active goals."""
        if sort_by_priority:
            return sorted(self._active_goals, key=lambda g: g.get_priority_score(), reverse=True)
        return self._active_goals.copy()

    def get_critical_goals(self) -> list[Goal]:
        """Get all active goals with CRITICAL priority."""
        return [g for g in self._active_goals if g.priority == GoalPriority.CRITICAL]

    def get_goals_by_type(self, goal_type: GoalType) -> list[Goal]:
        """Get all active goals of specific type."""
        return [g for g in self._active_goals if g.goal_type == goal_type]

    def get_statistics(self) -> dict[str, Any]:
        """Get goal generation statistics."""
        satisfaction_rate = (
            self.total_goals_satisfied / self.total_goals_generated
            if self.total_goals_generated > 0
            else 0.0
        )

        return {
            "generator_id": self.generator_id,
            "active_goals": len(self._active_goals),
            "total_generated": self.total_goals_generated,
            "total_satisfied": self.total_goals_satisfied,
            "total_expired": self.total_goals_expired,
            "satisfaction_rate": satisfaction_rate,
        }

    def __repr__(self) -> str:
        return f"AutonomousGoalGenerator({self.generator_id}, active={len(self._active_goals)}, generated={self.total_goals_generated})"
