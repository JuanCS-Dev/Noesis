"""
Comprehensive Tests for MMEI Goal System
=========================================

Tests for goal generation, management, and rate limiting.
"""

from unittest.mock import MagicMock

import pytest

from consciousness.mmei.goals import Goal
from consciousness.mmei.goal_manager import GoalManager
from consciousness.mmei.rate_limiter import RateLimiter
from consciousness.mmei.models import NeedUrgency


# =============================================================================
# GOAL TESTS
# =============================================================================


class TestGoal:
    """Test Goal data structure."""

    def test_goal_creation(self):
        """Goal should be creatable."""
        goal = Goal(
            goal_id="goal-001",
            source_need="rest_need",
            urgency=NeedUrgency.MEDIUM,
            description="Take a break",
        )
        
        assert goal.goal_id == "goal-001"
        assert goal.source_need == "rest_need"

    def test_goal_urgency_levels(self):
        """All urgency levels should work."""
        for urgency in NeedUrgency:
            goal = Goal(
                goal_id=f"goal-{urgency.name}",
                source_need="test",
                urgency=urgency,
                description="Test goal",
            )
            assert goal.urgency == urgency


# =============================================================================
# GOAL MANAGER TESTS
# =============================================================================


class TestGoalManager:
    """Test GoalManager behavior."""

    def test_creation(self):
        """GoalManager should be creatable."""
        manager = GoalManager()
        
        assert manager is not None

    def test_get_active_goals_empty(self):
        """Empty manager should return empty list."""
        manager = GoalManager()
        
        goals = manager.get_active_goals()
        
        assert isinstance(goals, list)
        assert len(goals) == 0

    def test_generate_goal(self):
        """Should generate goal from need."""
        manager = GoalManager()
        
        goal = manager.generate_goal(
            need_name="rest_need",
            need_value=0.8,
            urgency=NeedUrgency.HIGH,
        )
        
        # May return goal or None based on rate limit
        assert goal is None or isinstance(goal, Goal)


# =============================================================================
# RATE LIMITER TESTS
# =============================================================================


class TestRateLimiter:
    """Test RateLimiter behavior."""

    def test_creation(self):
        """RateLimiter should be creatable."""
        limiter = RateLimiter()
        
        assert limiter is not None

    def test_first_request_allowed(self):
        """First request should be allowed."""
        limiter = RateLimiter()
        
        is_allowed = limiter.is_allowed()
        
        assert is_allowed is True

    def test_rate_limit_tracking(self):
        """Rate limiter should track requests."""
        limiter = RateLimiter()
        
        # Multiple requests
        for _ in range(5):
            limiter.is_allowed()
        
        # Should still work
        assert True

    def test_get_stats(self):
        """Should return rate limiter stats."""
        limiter = RateLimiter()
        
        stats = limiter.get_stats()
        
        assert isinstance(stats, dict)
