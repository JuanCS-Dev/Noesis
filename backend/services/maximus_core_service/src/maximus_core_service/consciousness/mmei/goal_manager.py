"""
MMEI Goal Manager - Goal Generation and Management
==================================================

This module implements goal generation and management for the MMEI system.
It handles:
- Goal generation from needs
- Rate limiting and safety checks
- Goal deduplication
- Active goal management
- Overflow protection

FASE VII (Safety Hardening):
----------------------------
Includes multiple layers of protection to prevent overwhelming downstream
systems (ESGT/HCL) with excessive goal generation.

Safety Features:
- Rate limiting: Max goals per minute
- Deduplication: Prevent redundant goals
- Active goal limit: Cap concurrent goals
- Priority-based pruning: Remove low-priority goals when at capacity
- Overflow detection: Detect system distress conditions
"""

from __future__ import annotations

import time
from collections import deque

from maximus_core_service.consciousness.mmei.models import (
    GOAL_DEDUP_WINDOW_SECONDS,
    MAX_ACTIVE_GOALS,
    MAX_GOAL_QUEUE_SIZE,
    MAX_GOALS_PER_MINUTE,
    AbstractNeeds,
    Goal,
    NeedUrgency,
)
from maximus_core_service.consciousness.mmei.rate_limiter import RateLimiter


class GoalManager:
    """
    Manages goal generation and lifecycle for MMEI system.

    Provides multiple layers of safety:
    1. Rate limiting (max goals per minute)
    2. Deduplication (prevent redundant goals)
    3. Active goal limiting (cap concurrent goals)
    4. Overflow detection (detect system distress)

    Usage:
    ------
        manager = GoalManager()

        # Generate goal from need
        goal = manager.generate_goal_from_need("rest_need", 0.85, NeedUrgency.CRITICAL)

        if goal:
            logger.info("Generated: %s", goal)
            # Execute goal...
            manager.mark_goal_executed(goal.goal_id)

        # Get health metrics
        metrics = manager.get_health_metrics()
        logger.info("Active goals: %s", metrics['active_goals'])
    """

    def __init__(self):
        # FASE VII (Safety Hardening): Goal management & overflow protection
        self.rate_limiter = RateLimiter(max_per_minute=MAX_GOALS_PER_MINUTE)
        self.active_goals: list[Goal] = []  # Currently active goals
        self.goal_queue: deque = deque(maxlen=MAX_GOAL_QUEUE_SIZE)  # Pending goals
        self.goal_hashes: set[str] = set()  # For deduplication
        self.goal_hash_timestamps: dict[str, float] = {}  # Dedup expiry tracking

        # Statistics
        self.total_goals_generated: int = 0
        self.goals_rate_limited: int = 0
        self.goals_deduplicated: int = 0
        self.goals_overflow_dropped: int = 0
        self.need_overflow_events: int = 0  # Count of need overflow detections

    def generate_goal_from_need(
        self,
        need_name: str,
        need_value: float,
        urgency: NeedUrgency,
    ) -> Goal | None:
        """
        Generate a goal from an abstract need with full safety checks.

        This is the bridge from phenomenal experience (needs) to action (goals).
        Includes rate limiting, deduplication, and overflow protection.

        Args:
            need_name: Name of need (e.g., "rest_need")
            need_value: Need value [0-1]
            urgency: Computed urgency level

        Returns:
            Goal object if generated successfully, None if blocked by safety
        """
        # FASE VII: Check 1 - Rate limiter (HARD LIMIT)
        if not self.rate_limiter.allow():
            self.goals_rate_limited += 1
            return None

        # Generate goal description
        description = self._generate_goal_description(need_name, need_value, urgency)

        # Create goal
        goal_id = f"{need_name}_{int(time.time() * 1000)}"
        goal = Goal(
            goal_id=goal_id,
            need_source=need_name,
            description=description,
            priority=urgency,
            need_value=need_value,
        )

        # FASE VII: Check 2 - Deduplication (prevent redundant goals)
        goal_hash = goal.compute_hash()
        if self._is_duplicate_goal(goal_hash):
            self.goals_deduplicated += 1
            return None

        # FASE VII: Check 3 - Active goals limit (HARD LIMIT)
        if len(self.active_goals) >= MAX_ACTIVE_GOALS:
            # Try to prune low-priority goals
            self._prune_low_priority_goals()

            # Still at capacity? Drop this goal
            if len(self.active_goals) >= MAX_ACTIVE_GOALS:
                self.goals_overflow_dropped += 1
                return None

        # Record goal hash for deduplication
        self.goal_hashes.add(goal_hash)
        self.goal_hash_timestamps[goal_hash] = time.time()

        # Add to active goals
        self.active_goals.append(goal)
        self.total_goals_generated += 1

        return goal

    def _generate_goal_description(
        self,
        need_name: str,
        need_value: float,
        urgency: NeedUrgency,
    ) -> str:
        """Generate human-readable goal description from need."""
        descriptions = {
            "rest_need": f"Reduce computational load (load={need_value:.2f})",
            "repair_need": f"Fix system errors (error_rate={need_value:.2f})",
            "efficiency_need": f"Optimize resource usage (inefficiency={need_value:.2f})",
            "connectivity_need": f"Improve network connectivity (latency={need_value:.2f})",
            "curiosity_drive": f"Explore idle capacity (curiosity={need_value:.2f})",
            "learning_drive": f"Acquire new patterns (learning={need_value:.2f})",
        }

        return descriptions.get(need_name, f"{need_name}={need_value:.2f}")

    def _is_duplicate_goal(self, goal_hash: str) -> bool:
        """Check if goal hash exists within deduplication window."""
        if goal_hash not in self.goal_hashes:
            return False

        # Check if hash is still valid (within window)
        timestamp = self.goal_hash_timestamps.get(goal_hash, 0.0)
        if time.time() - timestamp > GOAL_DEDUP_WINDOW_SECONDS:
            # Expired, remove and allow
            self.goal_hashes.discard(goal_hash)
            self.goal_hash_timestamps.pop(goal_hash, None)
            return False

        return True

    def _prune_low_priority_goals(self) -> None:
        """
        Remove lowest-priority active goal to make room.

        Called when active_goals reaches capacity. Removes the goal with
        lowest urgency (SATISFIED < LOW < MODERATE < HIGH < CRITICAL).
        """
        if not self.active_goals:
            return

        # Priority ordering (lower index = lower priority)
        priority_order = {
            NeedUrgency.SATISFIED: 0,
            NeedUrgency.LOW: 1,
            NeedUrgency.MODERATE: 2,
            NeedUrgency.HIGH: 3,
            NeedUrgency.CRITICAL: 4,
        }

        # Find goal with lowest priority
        lowest_goal = min(
            self.active_goals,
            key=lambda g: priority_order.get(g.priority, 0),
        )

        # Remove it
        self.active_goals.remove(lowest_goal)

        # Remove hash tracking
        goal_hash = lowest_goal.compute_hash()
        self.goal_hashes.discard(goal_hash)
        self.goal_hash_timestamps.pop(goal_hash, None)

    def handle_need_overflow(self, needs: AbstractNeeds) -> None:
        """
        Detect and handle need overflow condition.

        Overflow occurs when multiple needs are simultaneously critical (>0.80).
        This indicates system distress and should trigger Safety Core notification.

        Args:
            needs: Current AbstractNeeds
        """
        critical_needs = needs.get_critical_needs(threshold=0.80)

        # FASE VII: Overflow = 3+ critical needs simultaneously
        if len(critical_needs) >= 3:
            self.need_overflow_events += 1
            logger.info("⚠️  MMEI OVERFLOW: %s critical needs: {critical_needs}", len(critical_needs))

            # In production, this would notify Safety Core
            # For now, just log and count

    def mark_goal_executed(self, goal_id: str) -> bool:
        """
        Mark a goal as executed and remove from active goals.

        Args:
            goal_id: ID of goal to mark executed

        Returns:
            True if goal found and marked, False otherwise
        """
        for goal in self.active_goals:
            if goal.goal_id == goal_id:
                goal.executed = True
                self.active_goals.remove(goal)
                return True

        return False

    def get_health_metrics(self) -> dict[str, any]:
        """
        Get goal manager health metrics.

        Returns metrics about goal generation, rate limiting, overflow events.
        Used by Safety Core for monitoring.

        Returns:
            Dict with health metrics
        """
        return {
            # Goal generation metrics
            "total_goals_generated": self.total_goals_generated,
            "goals_rate_limited": self.goals_rate_limited,
            "goals_deduplicated": self.goals_deduplicated,
            "goals_overflow_dropped": self.goals_overflow_dropped,
            "active_goals": len(self.active_goals),
            "current_goal_rate": self.rate_limiter.get_current_rate(),
            # Overflow detection
            "need_overflow_events": self.need_overflow_events,
        }

    def __repr__(self) -> str:
        return (
            f"GoalManager(active_goals={len(self.active_goals)}, "
            f"total_generated={self.total_goals_generated}, "
            f"rate_limited={self.goals_rate_limited})"
        )
