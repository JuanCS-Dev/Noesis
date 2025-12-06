"""
Comprehensive Tests for System.py - Consciousness System Manager
=================================================================

Tests for ConsciousnessSystem lifecycle and integration.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consciousness.system import ConsciousnessSystem, ConsciousnessConfig, ReactiveConfig


# =============================================================================
# CONFIG TESTS
# =============================================================================


class TestReactiveConfig:
    """Test ReactiveConfig defaults."""

    def test_default_values(self):
        """Default values should be sensible."""
        config = ReactiveConfig()
        
        assert config.collection_interval_ms > 0
        assert 0 < config.salience_threshold < 1


class TestConsciousnessConfig:
    """Test ConsciousnessConfig defaults."""

    def test_default_values(self):
        """Default values should be sensible."""
        config = ConsciousnessConfig()
        
        assert config.tig_node_count > 0
        assert 0 < config.tig_target_density < 1
        assert 0 < config.esgt_min_salience < 1
        assert 0 < config.arousal_baseline < 1

    def test_safety_disabled_by_default(self):
        """Safety should be disabled by default."""
        config = ConsciousnessConfig()
        
        assert config.safety_enabled is False


# =============================================================================
# CONSCIOUSNESS SYSTEM INIT TESTS
# =============================================================================


class TestConsciousnessSystemInit:
    """Test ConsciousnessSystem initialization."""

    def test_init_with_default_config(self):
        """System should initialize with default config."""
        system = ConsciousnessSystem()
        
        assert system.config is not None
        assert system.config.tig_node_count > 0

    def test_init_with_custom_config(self):
        """System should accept custom config."""
        config = ConsciousnessConfig(tig_node_count=50)
        system = ConsciousnessSystem(config)
        
        assert system.config.tig_node_count == 50

    def test_init_not_running(self):
        """System should not be running after init."""
        system = ConsciousnessSystem()
        
        assert system._running is False


# =============================================================================
# CONSCIOUSNESS SYSTEM LIFECYCLE TESTS
# =============================================================================


class TestConsciousnessSystemLifecycle:
    """Test system start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_initializes_components(self):
        """Start should initialize TIG, ESGT, Arousal."""
        config = ConsciousnessConfig(tig_node_count=10)  # Small for speed
        system = ConsciousnessSystem(config)
        
        await system.start()
        
        assert system._running is True
        assert system.tig is not None
        assert system.esgt is not None
        assert system.arousal is not None
        
        await system.stop()

    @pytest.mark.asyncio
    async def test_stop_cleans_up(self):
        """Stop should clean up components."""
        config = ConsciousnessConfig(tig_node_count=10)
        system = ConsciousnessSystem(config)
        
        await system.start()
        await system.stop()
        
        assert system._running is False


# =============================================================================
# CONSCIOUSNESS SYSTEM STATE TESTS
# =============================================================================


class TestConsciousnessSystemState:
    """Test system state retrieval."""

    @pytest.mark.asyncio
    async def test_get_system_dict(self):
        """get_system_dict should return component dict."""
        config = ConsciousnessConfig(tig_node_count=10)
        system = ConsciousnessSystem(config)
        
        await system.start()
        
        state = system.get_system_dict()
        
        assert isinstance(state, dict)
        assert "tig" in state or len(state) >= 1
        
        await system.stop()

    @pytest.mark.asyncio
    async def test_is_healthy_when_running(self):
        """is_healthy should return True when running."""
        config = ConsciousnessConfig(tig_node_count=10)
        system = ConsciousnessSystem(config)
        
        await system.start()
        
        assert system.is_healthy() is True
        
        await system.stop()

    def test_is_healthy_when_not_running(self):
        """is_healthy should return False when not running."""
        system = ConsciousnessSystem()
        
        assert system.is_healthy() is False


# =============================================================================
# CONSCIOUSNESS SYSTEM SAFETY TESTS
# =============================================================================


class TestConsciousnessSystemSafety:
    """Test safety integration."""

    def test_get_safety_status_disabled(self):
        """get_safety_status should return None when disabled."""
        config = ConsciousnessConfig(safety_enabled=False)
        system = ConsciousnessSystem(config)
        
        status = system.get_safety_status()
        
        assert status is None

    def test_get_safety_violations_disabled(self):
        """get_safety_violations should return empty when disabled."""
        config = ConsciousnessConfig(safety_enabled=False)
        system = ConsciousnessSystem(config)
        
        violations = system.get_safety_violations()
        
        assert violations == []


# =============================================================================
# CONSCIOUSNESS SYSTEM REPR TESTS
# =============================================================================


class TestConsciousnessSystemRepr:
    """Test string representation."""

    def test_repr(self):
        """Repr should include system info."""
        system = ConsciousnessSystem()
        
        repr_str = repr(system)
        
        assert "ConsciousnessSystem" in repr_str
