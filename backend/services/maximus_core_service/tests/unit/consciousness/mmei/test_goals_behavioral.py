"""
Comprehensive Tests for MMEI Goal System
=========================================

Tests for goal generation, management, and rate limiting.
"""

from unittest.mock import MagicMock

import pytest

from consciousness.mmei.goals import AutonomousGoalGenerator
from consciousness.mmei.goals_models import Goal, GoalPriority, GoalType, GoalGenerationConfig
from consciousness.mmei.rate_limiter import RateLimiter
from consciousness.mmei.models import AbstractNeeds, NeedUrgency


# =============================================================================
# GOAL MODELS TESTS
# =============================================================================


class TestGoalPriority:
    """Test GoalPriority enum."""

    def test_all_priorities_exist(self):
        """All priority levels should exist."""
        assert GoalPriority.BACKGROUND
        assert GoalPriority.LOW
        assert GoalPriority.MODERATE
        assert GoalPriority.HIGH
        assert GoalPriority.CRITICAL


class TestGoalType:
    """Test GoalType enum."""

    def test_all_types_exist(self):
        """All goal types should exist."""
        assert GoalType.REST
        assert GoalType.REPAIR
        assert GoalType.OPTIMIZE
        assert GoalType.EXPLORE


# =============================================================================
# AUTONOMOUS GOAL GENERATOR TESTS
# =============================================================================


class TestAutonomousGoalGeneratorInit:
    """Test AutonomousGoalGenerator initialization."""

    def test_creation(self):
        """Generator should be creatable."""
        generator = AutonomousGoalGenerator()
        
        assert generator is not None

    def test_custom_id(self):
        """Custom ID should be accepted."""
        generator = AutonomousGoalGenerator(generator_id="test-generator")
        
        assert generator.generator_id == "test-generator"


class TestAutonomousGoalGeneratorGoals:
    """Test goal generation."""

    def test_get_active_goals_empty(self):
        """Empty generator should return empty list."""
        generator = AutonomousGoalGenerator()
        
        goals = generator.get_active_goals()
        
        assert isinstance(goals, list)
        assert len(goals) == 0

    def test_generate_goals_from_needs(self):
        """Should generate goals from high needs."""
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(
            rest_need=0.9,
            repair_need=0.1,
            efficiency_need=0.2,
            connectivity_need=0.1,
            curiosity_drive=0.1,
            learning_drive=0.1,
        )
        
        goals = generator.generate_goals(needs)
        
        assert isinstance(goals, list)
        # High rest_need should generate at least one goal
        assert len(goals) >= 1

    def test_get_statistics(self):
        """Should return statistics."""
        generator = AutonomousGoalGenerator()
        
        stats = generator.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_generated" in stats


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
        
        is_allowed = limiter.allow()
        
        assert is_allowed is True

    def test_rate_limit_tracking(self):
        """Rate limiter should track requests."""
        limiter = RateLimiter(max_per_minute=10)
        
        # Multiple requests
        for _ in range(5):
            limiter.allow()
        
        # Should still allow
        assert limiter.allow() is True

    def test_get_current_rate(self):
        """Should return current rate."""
        limiter = RateLimiter()
        
        # Make some requests
        limiter.allow()
        limiter.allow()
        
        rate = limiter.get_current_rate()
        
        assert rate >= 2
