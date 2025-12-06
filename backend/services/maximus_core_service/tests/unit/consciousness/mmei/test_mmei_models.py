"""
Comprehensive tests for MMEI models (goals_models.py, models.py)

Tests cover:
- GoalType enum
- GoalPriority enum
- Goal dataclass with all methods
- GoalGenerationConfig dataclass
- NeedUrgency enum
- PhysicalMetrics dataclass
- AbstractNeeds dataclass
- InteroceptionConfig dataclass
- Goal dataclass (from models.py)
"""

import time

import pytest

from consciousness.mmei.goals_models import (
    Goal as GoalsGoal,
    GoalGenerationConfig,
    GoalPriority,
    GoalType,
)
from consciousness.mmei.models import (
    AbstractNeeds,
    Goal,
    InteroceptionConfig,
    NeedUrgency,
    PhysicalMetrics,
)


# ==================== GOALS MODELS TESTS ====================


class TestGoalType:
    """Test GoalType enum."""

    def test_all_goal_types_exist(self):
        """Test that all expected goal types are defined."""
        assert GoalType.REST.value == "rest"
        assert GoalType.REPAIR.value == "repair"
        assert GoalType.OPTIMIZE.value == "optimize"
        assert GoalType.RESTORE.value == "restore"
        assert GoalType.EXPLORE.value == "explore"
        assert GoalType.LEARN.value == "learn"
        assert GoalType.CREATE.value == "create"

    def test_goal_type_count(self):
        """Test that we have all expected goal types."""
        assert len(GoalType) == 7


class TestGoalPriority:
    """Test GoalPriority enum."""

    def test_all_priorities_exist(self):
        """Test that all expected priorities are defined."""
        assert GoalPriority.BACKGROUND.value == 0
        assert GoalPriority.LOW.value == 1
        assert GoalPriority.MODERATE.value == 2
        assert GoalPriority.HIGH.value == 3
        assert GoalPriority.CRITICAL.value == 4

    def test_priority_ordering(self):
        """Test that priorities are in ascending order."""
        assert GoalPriority.BACKGROUND.value < GoalPriority.LOW.value
        assert GoalPriority.LOW.value < GoalPriority.MODERATE.value
        assert GoalPriority.MODERATE.value < GoalPriority.HIGH.value
        assert GoalPriority.HIGH.value < GoalPriority.CRITICAL.value


class TestGoalsGoal:
    """Test Goal dataclass from goals_models.py."""

    def test_creation_minimal(self):
        """Test creating goal with defaults."""
        goal = GoalsGoal()

        assert goal.goal_type == GoalType.REST
        assert goal.priority == GoalPriority.LOW
        assert goal.is_active is True
        assert goal.satisfied_at is None
        assert goal.execution_attempts == 0

    def test_creation_complete(self):
        """Test creating goal with all fields."""
        goal = GoalsGoal(
            goal_type=GoalType.REPAIR,
            priority=GoalPriority.CRITICAL,
            description="Fix critical bug",
            target_component="database",
            source_need="repair_need",
            need_value=0.9,
            target_need_value=0.2,
            timeout_seconds=60.0,
        )

        assert goal.goal_type == GoalType.REPAIR
        assert goal.priority == GoalPriority.CRITICAL
        assert goal.description == "Fix critical bug"
        assert goal.target_component == "database"
        assert goal.need_value == 0.9

    def test_is_expired_not_active(self):
        """Test that inactive goals are never expired."""
        goal = GoalsGoal()
        goal.is_active = False
        assert goal.is_expired() is False

    def test_is_expired_within_timeout(self):
        """Test that goal within timeout is not expired."""
        goal = GoalsGoal(timeout_seconds=10.0)
        assert goal.is_expired() is False

    def test_is_expired_after_timeout(self):
        """Test that goal after timeout is expired."""
        goal = GoalsGoal(timeout_seconds=0.1)
        time.sleep(0.15)
        assert goal.is_expired() is True

    def test_is_satisfied_below_target(self):
        """Test goal satisfaction when need is below target."""
        goal = GoalsGoal(target_need_value=0.3)
        assert goal.is_satisfied(0.2) is True

    def test_is_satisfied_above_target(self):
        """Test goal not satisfied when need is above target."""
        goal = GoalsGoal(target_need_value=0.3)
        assert goal.is_satisfied(0.5) is False

    def test_is_satisfied_at_target(self):
        """Test goal not satisfied when need equals target."""
        goal = GoalsGoal(target_need_value=0.3)
        assert goal.is_satisfied(0.3) is False

    def test_mark_satisfied(self):
        """Test marking goal as satisfied."""
        goal = GoalsGoal()
        assert goal.is_active is True
        assert goal.satisfied_at is None

        goal.mark_satisfied()

        assert goal.is_active is False
        assert goal.satisfied_at is not None
        assert isinstance(goal.satisfied_at, float)

    def test_record_execution_attempt(self):
        """Test recording execution attempt."""
        goal = GoalsGoal()
        assert goal.execution_attempts == 0
        assert goal.last_execution_at is None

        goal.record_execution_attempt()

        assert goal.execution_attempts == 1
        assert goal.last_execution_at is not None

        goal.record_execution_attempt()
        assert goal.execution_attempts == 2

    def test_get_age_seconds(self):
        """Test getting goal age."""
        goal = GoalsGoal()
        time.sleep(0.1)
        age = goal.get_age_seconds()
        assert age >= 0.1
        assert age < 1.0

    def test_get_priority_score_critical(self):
        """Test priority score for critical goal."""
        goal = GoalsGoal(
            priority=GoalPriority.CRITICAL,
            need_value=0.8,
        )
        score = goal.get_priority_score()
        # CRITICAL = 4 * 100 = 400
        # need_bonus = 0.8 * 50 = 40
        # age_penalty ~= 0 (just created)
        assert score > 430

    def test_get_priority_score_background(self):
        """Test priority score for background goal."""
        goal = GoalsGoal(
            priority=GoalPriority.BACKGROUND,
            need_value=0.1,
        )
        score = goal.get_priority_score()
        # BACKGROUND = 0 * 100 = 0
        # need_bonus = 0.1 * 50 = 5
        assert score < 10

    def test_get_priority_score_with_age_penalty(self):
        """Test that priority score decreases with age."""
        goal = GoalsGoal(
            priority=GoalPriority.MODERATE,
            need_value=0.5,
            timeout_seconds=1.0,
        )
        initial_score = goal.get_priority_score()

        time.sleep(0.5)
        later_score = goal.get_priority_score()

        assert later_score < initial_score

    def test_repr(self):
        """Test string representation."""
        goal = GoalsGoal(
            goal_type=GoalType.REPAIR,
            priority=GoalPriority.HIGH,
            need_value=0.75,
        )
        repr_str = repr(goal)

        assert "repair" in repr_str
        assert "3" in repr_str  # HIGH priority value
        assert "ACTIVE" in repr_str
        assert "0.75" in repr_str

    def test_repr_satisfied(self):
        """Test string representation of satisfied goal."""
        goal = GoalsGoal()
        goal.mark_satisfied()
        repr_str = repr(goal)

        assert "SATISFIED" in repr_str


class TestGoalGenerationConfig:
    """Test GoalGenerationConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = GoalGenerationConfig()

        assert config.rest_threshold == 0.60
        assert config.repair_threshold == 0.40
        assert config.efficiency_threshold == 0.50
        assert config.connectivity_threshold == 0.50

    def test_satisfaction_thresholds(self):
        """Test satisfaction threshold values."""
        config = GoalGenerationConfig()

        assert config.rest_satisfied == 0.30
        assert config.repair_satisfied == 0.20
        assert config.efficiency_satisfied == 0.30
        assert config.connectivity_satisfied == 0.30

    def test_timeouts(self):
        """Test timeout values."""
        config = GoalGenerationConfig()

        assert config.default_timeout == 300.0
        assert config.critical_timeout == 600.0
        assert config.exploration_timeout == 120.0

    def test_limits(self):
        """Test limit values."""
        config = GoalGenerationConfig()

        assert config.max_concurrent_goals == 10
        assert config.min_goal_interval_seconds == 5.0

    def test_custom_configuration(self):
        """Test creating custom configuration."""
        config = GoalGenerationConfig(
            rest_threshold=0.70,
            repair_threshold=0.30,
            max_concurrent_goals=20,
            default_timeout=600.0,
        )

        assert config.rest_threshold == 0.70
        assert config.repair_threshold == 0.30
        assert config.max_concurrent_goals == 20
        assert config.default_timeout == 600.0


# ==================== MODELS TESTS ====================


class TestNeedUrgency:
    """Test NeedUrgency enum."""

    def test_all_urgency_levels_exist(self):
        """Test that all expected urgency levels are defined."""
        assert NeedUrgency.SATISFIED.value == "satisfied"
        assert NeedUrgency.LOW.value == "low"
        assert NeedUrgency.MODERATE.value == "moderate"
        assert NeedUrgency.HIGH.value == "high"
        assert NeedUrgency.CRITICAL.value == "critical"

    def test_urgency_count(self):
        """Test that we have all expected urgency levels."""
        assert len(NeedUrgency) == 5


class TestPhysicalMetrics:
    """Test PhysicalMetrics dataclass."""

    def test_creation_minimal(self):
        """Test creating metrics with defaults."""
        metrics = PhysicalMetrics()

        assert metrics.cpu_usage_percent == 0.0
        assert metrics.memory_usage_percent == 0.0
        assert metrics.error_rate_per_min == 0.0
        assert metrics.exception_count == 0
        assert metrics.temperature_celsius is None
        assert metrics.power_draw_watts is None

    def test_creation_complete(self):
        """Test creating metrics with all fields."""
        metrics = PhysicalMetrics(
            cpu_usage_percent=75.0,
            memory_usage_percent=60.0,
            error_rate_per_min=5.0,
            exception_count=3,
            temperature_celsius=65.0,
            power_draw_watts=150.0,
            network_latency_ms=25.0,
            packet_loss_percent=1.0,
            idle_time_percent=10.0,
            throughput_ops_per_sec=1000.0,
        )

        assert metrics.cpu_usage_percent == 75.0
        assert metrics.memory_usage_percent == 60.0
        assert metrics.temperature_celsius == 65.0
        assert metrics.network_latency_ms == 25.0

    def test_normalize_percentages(self):
        """Test normalization of percentage values."""
        metrics = PhysicalMetrics(
            cpu_usage_percent=75.0,
            memory_usage_percent=60.0,
            packet_loss_percent=2.5,
            idle_time_percent=30.0,
        )

        normalized = metrics.normalize()

        assert normalized.cpu_usage_percent == 0.75
        assert normalized.memory_usage_percent == 0.60
        assert normalized.packet_loss_percent == 0.025
        assert normalized.idle_time_percent == 0.30

    def test_normalize_over_100(self):
        """Test that normalization caps values at 1.0."""
        metrics = PhysicalMetrics(
            cpu_usage_percent=150.0,  # Over 100%
            memory_usage_percent=120.0,
        )

        normalized = metrics.normalize()

        assert normalized.cpu_usage_percent == 1.0
        assert normalized.memory_usage_percent == 1.0

    def test_normalize_preserves_non_percentage_values(self):
        """Test that normalization preserves non-percentage values."""
        metrics = PhysicalMetrics(
            error_rate_per_min=10.0,
            exception_count=5,
            network_latency_ms=50.0,
            throughput_ops_per_sec=500.0,
        )

        normalized = metrics.normalize()

        assert normalized.error_rate_per_min == 10.0
        assert normalized.exception_count == 5
        assert normalized.network_latency_ms == 50.0
        assert normalized.throughput_ops_per_sec == 500.0


class TestAbstractNeeds:
    """Test AbstractNeeds dataclass."""

    def test_creation_minimal(self):
        """Test creating needs with defaults."""
        needs = AbstractNeeds()

        assert needs.rest_need == 0.0
        assert needs.repair_need == 0.0
        assert needs.efficiency_need == 0.0
        assert needs.connectivity_need == 0.0
        assert needs.curiosity_drive == 0.0
        assert needs.learning_drive == 0.0

    def test_creation_complete(self):
        """Test creating needs with all fields."""
        needs = AbstractNeeds(
            rest_need=0.7,
            repair_need=0.3,
            efficiency_need=0.5,
            connectivity_need=0.4,
            curiosity_drive=0.2,
            learning_drive=0.1,
        )

        assert needs.rest_need == 0.7
        assert needs.repair_need == 0.3
        assert needs.efficiency_need == 0.5

    def test_get_most_urgent_rest(self):
        """Test getting most urgent when rest is highest."""
        needs = AbstractNeeds(
            rest_need=0.85,
            repair_need=0.3,
            efficiency_need=0.4,
        )

        name, value, urgency = needs.get_most_urgent()

        assert name == "rest_need"
        assert value == 0.85
        assert urgency == NeedUrgency.CRITICAL

    def test_get_most_urgent_repair(self):
        """Test getting most urgent when repair is highest."""
        needs = AbstractNeeds(
            rest_need=0.3,
            repair_need=0.65,
            efficiency_need=0.4,
        )

        name, value, urgency = needs.get_most_urgent()

        assert name == "repair_need"
        assert value == 0.65
        assert urgency == NeedUrgency.HIGH

    def test_get_most_urgent_curiosity(self):
        """Test getting most urgent when curiosity is highest."""
        needs = AbstractNeeds(
            rest_need=0.1,
            repair_need=0.1,
            curiosity_drive=0.75,
        )

        name, value, urgency = needs.get_most_urgent()

        assert name == "curiosity_drive"
        assert value == 0.75

    def test_get_critical_needs_none(self):
        """Test getting critical needs when none exist."""
        needs = AbstractNeeds(
            rest_need=0.5,
            repair_need=0.3,
        )

        critical = needs.get_critical_needs(threshold=0.80)

        assert len(critical) == 0

    def test_get_critical_needs_one(self):
        """Test getting critical needs with one critical."""
        needs = AbstractNeeds(
            rest_need=0.85,
            repair_need=0.3,
            efficiency_need=0.5,
        )

        critical = needs.get_critical_needs(threshold=0.80)

        assert len(critical) == 1
        assert critical[0] == ("rest_need", 0.85)

    def test_get_critical_needs_multiple(self):
        """Test getting critical needs with multiple critical."""
        needs = AbstractNeeds(
            rest_need=0.90,
            repair_need=0.85,
            efficiency_need=0.95,
            connectivity_need=0.75,
        )

        critical = needs.get_critical_needs(threshold=0.80)

        assert len(critical) == 3
        names = [name for name, _ in critical]
        assert "rest_need" in names
        assert "repair_need" in names
        assert "efficiency_need" in names

    def test_get_critical_needs_custom_threshold(self):
        """Test getting critical needs with custom threshold."""
        needs = AbstractNeeds(
            rest_need=0.60,
            repair_need=0.70,
        )

        critical = needs.get_critical_needs(threshold=0.65)

        assert len(critical) == 1
        assert critical[0] == ("repair_need", 0.70)

    def test_classify_urgency_satisfied(self):
        """Test urgency classification for satisfied."""
        needs = AbstractNeeds()
        urgency = needs._classify_urgency(0.15)
        assert urgency == NeedUrgency.SATISFIED

    def test_classify_urgency_low(self):
        """Test urgency classification for low."""
        needs = AbstractNeeds()
        urgency = needs._classify_urgency(0.30)
        assert urgency == NeedUrgency.LOW

    def test_classify_urgency_moderate(self):
        """Test urgency classification for moderate."""
        needs = AbstractNeeds()
        urgency = needs._classify_urgency(0.50)
        assert urgency == NeedUrgency.MODERATE

    def test_classify_urgency_high(self):
        """Test urgency classification for high."""
        needs = AbstractNeeds()
        urgency = needs._classify_urgency(0.70)
        assert urgency == NeedUrgency.HIGH

    def test_classify_urgency_critical(self):
        """Test urgency classification for critical."""
        needs = AbstractNeeds()
        urgency = needs._classify_urgency(0.90)
        assert urgency == NeedUrgency.CRITICAL

    def test_classify_urgency_boundaries(self):
        """Test urgency classification at boundaries."""
        needs = AbstractNeeds()

        assert needs._classify_urgency(0.20) == NeedUrgency.LOW
        assert needs._classify_urgency(0.40) == NeedUrgency.MODERATE
        assert needs._classify_urgency(0.60) == NeedUrgency.HIGH
        assert needs._classify_urgency(0.80) == NeedUrgency.CRITICAL

    def test_repr(self):
        """Test string representation."""
        needs = AbstractNeeds(
            rest_need=0.75,
            repair_need=0.3,
        )

        repr_str = repr(needs)

        assert "rest_need" in repr_str
        assert "0.75" in repr_str
        assert "high" in repr_str


class TestInteroceptionConfig:
    """Test InteroceptionConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = InteroceptionConfig()

        assert config.collection_interval_ms == 100.0
        assert config.short_term_window_samples == 10
        assert config.long_term_window_samples == 50

    def test_weights(self):
        """Test weight values."""
        config = InteroceptionConfig()

        assert config.cpu_weight == 0.6
        assert config.memory_weight == 0.4
        assert config.cpu_weight + config.memory_weight == 1.0

    def test_thresholds(self):
        """Test threshold values."""
        config = InteroceptionConfig()

        assert config.error_rate_critical == 10.0
        assert config.temperature_warning_celsius == 80.0
        assert config.latency_warning_ms == 100.0

    def test_curiosity_parameters(self):
        """Test curiosity parameter values."""
        config = InteroceptionConfig()

        assert config.idle_curiosity_threshold == 0.70
        assert config.curiosity_growth_rate == 0.01

    def test_custom_configuration(self):
        """Test creating custom configuration."""
        config = InteroceptionConfig(
            collection_interval_ms=50.0,
            cpu_weight=0.7,
            memory_weight=0.3,
            error_rate_critical=20.0,
        )

        assert config.collection_interval_ms == 50.0
        assert config.cpu_weight == 0.7
        assert config.memory_weight == 0.3
        assert config.error_rate_critical == 20.0


class TestGoal:
    """Test Goal dataclass from models.py."""

    def test_creation_complete(self):
        """Test creating goal with all required fields."""
        goal = Goal(
            goal_id="goal-001",
            need_source="rest_need",
            description="Reduce CPU load",
            priority=NeedUrgency.HIGH,
            need_value=0.75,
        )

        assert goal.goal_id == "goal-001"
        assert goal.need_source == "rest_need"
        assert goal.description == "Reduce CPU load"
        assert goal.priority == NeedUrgency.HIGH
        assert goal.need_value == 0.75
        assert goal.executed is False

    def test_compute_hash_same_content(self):
        """Test that same content produces same hash."""
        goal1 = Goal(
            goal_id="goal-001",
            need_source="rest_need",
            description="Reduce load",
            priority=NeedUrgency.HIGH,
            need_value=0.75,
        )
        goal2 = Goal(
            goal_id="goal-002",  # Different ID
            need_source="rest_need",
            description="Reduce load",
            priority=NeedUrgency.HIGH,
            need_value=0.80,  # Different value
        )

        # Hash should be same because it's based on need_source, description, priority
        assert goal1.compute_hash() == goal2.compute_hash()

    def test_compute_hash_different_content(self):
        """Test that different content produces different hash."""
        goal1 = Goal(
            goal_id="goal-001",
            need_source="rest_need",
            description="Reduce load",
            priority=NeedUrgency.HIGH,
            need_value=0.75,
        )
        goal2 = Goal(
            goal_id="goal-001",
            need_source="repair_need",  # Different source
            description="Reduce load",
            priority=NeedUrgency.HIGH,
            need_value=0.75,
        )

        assert goal1.compute_hash() != goal2.compute_hash()

    def test_compute_hash_length(self):
        """Test that hash is 16 characters."""
        goal = Goal(
            goal_id="goal-001",
            need_source="rest_need",
            description="Test",
            priority=NeedUrgency.LOW,
            need_value=0.5,
        )

        hash_value = goal.compute_hash()
        assert len(hash_value) == 16

    def test_repr(self):
        """Test string representation."""
        goal = Goal(
            goal_id="goal-123",
            need_source="repair_need",
            description="Fix error",
            priority=NeedUrgency.CRITICAL,
            need_value=0.9,
        )

        repr_str = repr(goal)

        assert "goal-123" in repr_str
        assert "repair_need" in repr_str
        assert "critical" in repr_str
