"""
Comprehensive Tests for MCEA - Arousal Controller
===================================================

Tests for arousal control and stress management.
"""

from unittest.mock import MagicMock, AsyncMock

import pytest

from consciousness.mcea.controller import ArousalController
from consciousness.mcea.models import ArousalConfig, ArousalLevel, ArousalState


# =============================================================================
# AROUSAL CONFIG TESTS
# =============================================================================


class TestArousalConfig:
    """Test ArousalConfig data structure."""

    def test_default_creation(self):
        """Default config should be sensible."""
        config = ArousalConfig()
        
        assert config.baseline_arousal > 0
        assert config.min_arousal >= 0
        assert config.max_arousal <= 1.0


# =============================================================================
# AROUSAL LEVEL TESTS
# =============================================================================


class TestArousalLevel:
    """Test ArousalLevel enum."""

    def test_all_levels_exist(self):
        """All arousal levels should exist."""
        assert ArousalLevel.VERY_LOW
        assert ArousalLevel.LOW
        assert ArousalLevel.OPTIMAL
        assert ArousalLevel.HIGH
        assert ArousalLevel.VERY_HIGH


# =============================================================================
# AROUSAL CONTROLLER INIT TESTS
# =============================================================================


class TestArousalControllerInit:
    """Test ArousalController initialization."""

    def test_creation(self):
        """Controller should be creatable."""
        controller = ArousalController()
        
        assert controller is not None

    def test_custom_config(self):
        """Custom config should be accepted."""
        config = ArousalConfig(baseline_arousal=0.7)
        
        controller = ArousalController(config=config)
        
        assert controller is not None

    def test_custom_id(self):
        """Custom ID should be accepted."""
        controller = ArousalController(controller_id="test-arousal")
        
        assert controller.controller_id == "test-arousal"


# =============================================================================
# AROUSAL CONTROLLER METHODS TESTS
# =============================================================================


class TestArousalControllerMethods:
    """Test controller methods."""

    def test_get_current_arousal(self):
        """Should return current arousal state."""
        controller = ArousalController()
        
        state = controller.get_current_arousal()
        
        assert isinstance(state, ArousalState)

    def test_get_esgt_threshold(self):
        """Should return ESGT threshold."""
        controller = ArousalController()
        
        threshold = controller.get_esgt_threshold()
        
        assert 0 <= threshold <= 1

    def test_get_stress_level(self):
        """Should return stress level."""
        controller = ArousalController()
        
        stress = controller.get_stress_level()
        
        assert stress >= 0

    def test_reset_stress(self):
        """Should reset stress."""
        controller = ArousalController()
        
        controller.reset_stress()
        
        assert controller.get_stress_level() == 0

    def test_get_statistics(self):
        """Should return statistics dict."""
        controller = ArousalController()
        
        stats = controller.get_statistics()
        
        assert isinstance(stats, dict)

    def test_get_health_metrics(self):
        """Should return health metrics."""
        controller = ArousalController()
        
        metrics = controller.get_health_metrics()
        
        assert isinstance(metrics, dict)


class TestArousalControllerRepr:
    """Test string representation."""

    def test_repr(self):
        """Repr should include controller info."""
        controller = ArousalController()
        
        repr_str = repr(controller)
        
        assert "Arousal" in repr_str or "Controller" in repr_str
