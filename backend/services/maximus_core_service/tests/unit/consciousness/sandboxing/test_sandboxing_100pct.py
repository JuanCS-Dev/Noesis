"""
Sandboxing Coverage Tests - Audited Version
============================================
Tests aligned with actual API from:
- consciousness/sandboxing/__init__.py (ConsciousnessContainer, ResourceLimits)
- consciousness/sandboxing/kill_switch.py (KillSwitch, TriggerType, KillSwitchTrigger)
- consciousness/sandboxing/resource_limiter.py (ResourceLimiter, ResourceLimits)

Author: Claude Code - Full API Audit
Date: 2025-12-02
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

# Import from actual modules
from consciousness.sandboxing import ResourceLimits, ConsciousnessContainer
from consciousness.sandboxing.kill_switch import KillSwitch, TriggerType
from consciousness.sandboxing.resource_limiter import ResourceLimiter


# =============================================================================
# ResourceLimits Tests (dataclass)
# =============================================================================

class TestResourceLimits:
    """Test ResourceLimits dataclass."""

    def test_default_values(self):
        """Test default values match implementation."""
        limits = ResourceLimits()
        assert limits.cpu_percent == 80.0
        assert limits.memory_mb == 1024
        assert limits.timeout_sec == 300
        assert limits.max_threads == 10
        assert limits.max_file_descriptors == 100

    def test_custom_values(self):
        """Test custom values."""
        limits = ResourceLimits(
            cpu_percent=50.0,
            memory_mb=512,
            timeout_sec=60,
            max_threads=20,
            max_file_descriptors=50
        )
        assert limits.cpu_percent == 50.0
        assert limits.memory_mb == 512
        assert limits.timeout_sec == 60
        assert limits.max_threads == 20
        assert limits.max_file_descriptors == 50


# =============================================================================
# ResourceLimiter Tests
# =============================================================================

class TestResourceLimiter:
    """Test ResourceLimiter class."""

    def test_init(self):
        """Test ResourceLimiter initialization."""
        limits = ResourceLimits(cpu_percent=50.0, memory_mb=512)
        limiter = ResourceLimiter(limits)
        assert limiter.limits == limits
        assert limiter.process is not None

    def test_apply_limits(self):
        """Test apply_limits executes without error."""
        limits = ResourceLimits(memory_mb=1024)
        limiter = ResourceLimiter(limits)
        # Should not raise
        limiter.apply_limits()

    def test_check_compliance_structure(self):
        """Test check_compliance returns expected structure."""
        limits = ResourceLimits(cpu_percent=80.0, memory_mb=1024, max_threads=10)
        limiter = ResourceLimiter(limits)
        compliance = limiter.check_compliance()

        # Check structure
        assert 'cpu' in compliance
        assert 'memory' in compliance
        assert 'threads' in compliance

        # Check cpu structure
        assert 'current' in compliance['cpu']
        assert 'limit' in compliance['cpu']
        assert 'compliant' in compliance['cpu']

        # Check memory structure
        assert 'current' in compliance['memory']
        assert 'limit' in compliance['memory']
        assert 'compliant' in compliance['memory']

        # Check threads structure
        assert 'current' in compliance['threads']
        assert 'limit' in compliance['threads']
        assert 'compliant' in compliance['threads']


# =============================================================================
# KillSwitch Tests
# =============================================================================

class TestKillSwitch:
    """Test KillSwitch class - aligned with actual API."""

    def test_init_default(self):
        """Test KillSwitch initialization with defaults."""
        ks = KillSwitch()
        assert ks.armed is True
        assert len(ks.triggers) == 0
        assert len(ks.activation_history) == 0
        assert ks.monitoring_active is False

    def test_init_with_callback(self):
        """Test KillSwitch initialization with alert callback."""
        callback = MagicMock()
        ks = KillSwitch(alert_callback=callback)
        assert ks.alert_callback == callback

    def test_activate_when_armed(self):
        """Test KillSwitch activation when armed."""
        ks = KillSwitch()
        result = ks.activate("Test reason", trigger_type=TriggerType.MANUAL)
        assert result is True
        assert len(ks.activation_history) == 1
        assert ks.activation_history[0]["reason"] == "Test reason"
        assert ks.activation_history[0]["trigger_type"] == "manual"

    def test_activate_when_disarmed(self):
        """Test KillSwitch activation when disarmed returns False."""
        ks = KillSwitch()
        ks.disarm("test_authorization")  # Requires authorization string
        result = ks.activate("Test reason")
        assert result is False

    def test_add_trigger(self):
        """Test adding a trigger."""
        ks = KillSwitch()
        trigger = ks.add_trigger(
            name="test_trigger",
            trigger_type=TriggerType.SAFETY_PROTOCOL,
            condition=lambda: False,
            description="Test trigger description"
        )
        assert trigger is not None
        assert trigger.name == "test_trigger"
        assert trigger.trigger_type == TriggerType.SAFETY_PROTOCOL
        assert trigger.description == "Test trigger description"
        assert trigger.enabled is True
        assert len(ks.triggers) == 1

    def test_check_triggers_no_triggers(self):
        """Test check_triggers with no triggers returns None."""
        ks = KillSwitch()
        result = ks.check_triggers()
        assert result is None

    def test_check_triggers_condition_false(self):
        """Test check_triggers when condition is False."""
        ks = KillSwitch()
        ks.add_trigger(
            name="never_trigger",
            trigger_type=TriggerType.RESOURCE_SPIKE,
            condition=lambda: False,
            description="Never triggers"
        )
        result = ks.check_triggers()
        assert result is None

    def test_check_triggers_condition_true(self):
        """Test check_triggers when condition is True."""
        ks = KillSwitch()
        ks.add_trigger(
            name="always_trigger",
            trigger_type=TriggerType.ETHICAL_VIOLATION,
            condition=lambda: True,
            description="Always triggers"
        )
        result = ks.check_triggers()
        assert result is not None
        assert result.name == "always_trigger"
        assert result.trigger_count == 1

    def test_arm(self):
        """Test arm() method."""
        ks = KillSwitch()
        ks.disarm("test_auth")  # Disarm first (requires authorization)
        assert ks.armed is False
        ks.arm()  # arm() takes no parameters
        assert ks.armed is True

    def test_disarm_requires_authorization(self):
        """Test disarm() requires authorization string."""
        ks = KillSwitch()
        assert ks.armed is True
        ks.disarm("admin_authorization_code")
        assert ks.armed is False
        # Check audit trail
        assert any(
            record.get("event") == "disarmed"
            for record in ks.activation_history
        )

    def test_get_status(self):
        """Test get_status() returns expected structure."""
        ks = KillSwitch()
        ks.add_trigger(
            name="test",
            trigger_type=TriggerType.MANUAL,
            condition=lambda: False,
            description="Test"
        )
        status = ks.get_status()

        assert "armed" in status
        assert "triggers_count" in status
        assert "activations_count" in status
        assert "triggers" in status
        assert "recent_activations" in status
        assert status["armed"] is True
        assert status["triggers_count"] == 1

    def test_repr(self):
        """Test __repr__ method."""
        ks = KillSwitch()
        repr_str = repr(ks)
        assert "KillSwitch" in repr_str
        assert "ARMED" in repr_str

    def test_repr_disarmed(self):
        """Test __repr__ when disarmed."""
        ks = KillSwitch()
        ks.disarm("auth")
        repr_str = repr(ks)
        assert "DISARMED" in repr_str


# =============================================================================
# ConsciousnessContainer Tests (lightweight - no actual execution)
# =============================================================================

class TestConsciousnessContainer:
    """Test ConsciousnessContainer - lightweight tests only."""

    def test_init(self):
        """Test ConsciousnessContainer initialization."""
        limits = ResourceLimits(timeout_sec=1)
        container = ConsciousnessContainer("test_container", limits)
        assert container.name == "test_container"
        assert container.limits == limits
        assert container.running is False

    def test_init_with_callback(self):
        """Test initialization with alert callback."""
        callback = MagicMock()
        limits = ResourceLimits()
        container = ConsciousnessContainer("test", limits, alert_callback=callback)
        assert container.alert_callback == callback

    def test_get_stats_initial(self):
        """Test get_stats returns initial stats dict."""
        limits = ResourceLimits()
        container = ConsciousnessContainer("test", limits)
        stats = container.get_stats()

        assert "peak_cpu" in stats
        assert "peak_memory_mb" in stats
        assert "violations" in stats
        assert stats["peak_cpu"] == 0.0
        assert stats["peak_memory_mb"] == 0.0

    def test_repr(self):
        """Test __repr__ method."""
        limits = ResourceLimits()
        container = ConsciousnessContainer("test_name", limits)
        repr_str = repr(container)

        assert "ConsciousnessContainer" in repr_str
        assert "test_name" in repr_str
        assert "stopped" in repr_str


# =============================================================================
# Integration Test (lightweight)
# =============================================================================

def test_integration_lightweight():
    """Lightweight integration test without heavy execution."""
    # Test ResourceLimiter
    limits = ResourceLimits(cpu_percent=70.0, memory_mb=2048, timeout_sec=60)
    limiter = ResourceLimiter(limits)
    limiter.apply_limits()
    compliance = limiter.check_compliance()
    assert 'cpu' in compliance
    assert 'memory' in compliance
    assert 'threads' in compliance

    # Test KillSwitch
    ks = KillSwitch()
    assert ks.armed is True
    ks.add_trigger(
        name="integration_test",
        trigger_type=TriggerType.MANUAL,
        condition=lambda: False,
        description="Integration test trigger"
    )
    assert len(ks.triggers) == 1

    # Test ConsciousnessContainer init only
    container = ConsciousnessContainer("integration", limits)
    assert container.name == "integration"
    stats = container.get_stats()
    assert "peak_cpu" in stats
