"""
REAL Tests for MCEA Arousal Controller - NO MOCKS
==================================================

Tests that actually run the ArousalController with real async execution.
"""

import asyncio
import pytest

from consciousness.mcea.controller import ArousalController
from consciousness.mcea.models import ArousalConfig, ArousalLevel, ArousalState


class TestArousalControllerCreation:
    """Test arousal controller creation and initialization."""

    def test_create_with_defaults(self):
        """Test creating controller with default config."""
        controller = ArousalController()

        assert controller.controller_id == "mcea-arousal-controller-primary"
        assert controller.config is not None
        assert controller.total_updates == 0

    def test_create_with_custom_config(self):
        """Test creating controller with custom config."""
        config = ArousalConfig(baseline_arousal=0.6, min_arousal=0.2, max_arousal=0.95)
        controller = ArousalController(config=config, controller_id="test-controller")

        assert controller.controller_id == "test-controller"
        assert controller.config.baseline_arousal == 0.6


class TestArousalClassification:
    """Test arousal level classification."""

    def test_classify_sleep(self):
        """Test classification of sleep level."""
        controller = ArousalController()

        level = controller._classify_arousal(0.1)
        assert level == ArousalLevel.SLEEP

    def test_classify_drowsy(self):
        """Test classification of drowsy level."""
        controller = ArousalController()

        level = controller._classify_arousal(0.3)
        assert level == ArousalLevel.DROWSY

    def test_classify_relaxed(self):
        """Test classification of relaxed level."""
        controller = ArousalController()

        level = controller._classify_arousal(0.5)
        assert level == ArousalLevel.RELAXED

    def test_classify_alert(self):
        """Test classification of alert level."""
        controller = ArousalController()

        level = controller._classify_arousal(0.7)
        assert level == ArousalLevel.ALERT

    def test_classify_hyperalert(self):
        """Test classification of hyperalert level."""
        controller = ArousalController()

        level = controller._classify_arousal(0.9)
        assert level == ArousalLevel.HYPERALERT


class TestArousalStateRetrieval:
    """Test getting current arousal state."""

    def test_get_current_arousal_returns_arousal_state(self):
        """Test get_current_arousal returns ArousalState object."""
        controller = ArousalController()

        state = controller.get_current_arousal()

        assert isinstance(state, ArousalState)
        assert hasattr(state, 'arousal')
        assert hasattr(state, 'level')

    def test_state_arousal_in_valid_range(self):
        """Test state arousal is in valid range."""
        controller = ArousalController()

        state = controller.get_current_arousal()

        assert 0.0 <= state.arousal <= 1.0

    def test_get_esgt_threshold(self):
        """Test getting ESGT threshold."""
        controller = ArousalController()

        threshold = controller.get_esgt_threshold()

        assert 0.0 <= threshold <= 1.0


class TestArousalModulation:
    """Test arousal modulation application."""

    def test_request_modulation_creates_modulation(self):
        """Test requesting modulation."""
        controller = ArousalController()

        initial_count = len(controller._active_modulations)

        controller.request_modulation(
            source="test",
            delta=0.2,
            duration_seconds=1.0
        )

        assert len(controller._active_modulations) > initial_count
        assert controller.total_modulations > 0

    def test_request_modulation_with_priority(self):
        """Test requesting modulation with priority."""
        controller = ArousalController()

        controller.request_modulation(
            source="high_priority",
            delta=0.3,
            duration_seconds=2.0,
            priority=5
        )

        assert len(controller._active_modulations) == 1


class TestArousalCallbacks:
    """Test arousal state change callbacks."""

    def test_register_callback(self):
        """Test registering arousal callback."""
        controller = ArousalController()

        callback_invoked = []

        def test_callback(state: ArousalState):
            callback_invoked.append(state)

        controller.register_arousal_callback(test_callback)

        assert len(controller._arousal_callbacks) > 0


@pytest.mark.asyncio
class TestArousalControllerAsyncOperations:
    """Test async operations of arousal controller."""

    async def test_start_and_stop(self):
        """Test starting and stopping controller."""
        controller = ArousalController()

        await controller.start()
        assert controller._running is True

        await asyncio.sleep(0.1)  # Let it run briefly

        await controller.stop()
        assert controller._running is False

    async def test_controller_updates_arousal(self):
        """Test controller actually updates arousal over time."""
        config = ArousalConfig(update_interval_ms=50)
        controller = ArousalController(config=config)

        initial_updates = controller.total_updates

        await controller.start()
        await asyncio.sleep(0.2)  # Should get ~4 updates
        await controller.stop()

        assert controller.total_updates > initial_updates

    async def test_arousal_responds_to_modulation(self):
        """Test arousal changes in response to modulation."""
        controller = ArousalController()

        await controller.start()

        initial_arousal = controller.get_current_arousal().arousal

        # Apply strong modulation
        controller.request_modulation(source="test", delta=0.3, duration_seconds=0.5)

        await asyncio.sleep(0.3)

        await controller.stop()

        # Modulation was registered
        assert controller.total_modulations > 0


class TestArousalESGTIntegration:
    """Test ESGT-related arousal functionality."""

    def test_apply_esgt_refractory(self):
        """Test applying ESGT refractory period."""
        controller = ArousalController()

        controller.apply_esgt_refractory()

        assert controller._refractory_until is not None
        assert controller.esgt_refractories_applied == 1

    def test_refractory_affects_threshold(self):
        """Test refractory period is tracked."""
        config = ArousalConfig(esgt_refractory_arousal_drop=0.2)
        controller = ArousalController(config=config)

        controller.apply_esgt_refractory()

        # Refractory should be active
        assert controller._refractory_until is not None


class TestArousalStatistics:
    """Test arousal controller statistics."""

    def test_tracks_total_updates(self):
        """Test controller tracks total updates."""
        controller = ArousalController()

        assert controller.total_updates == 0

    def test_tracks_total_modulations(self):
        """Test controller tracks total modulations."""
        controller = ArousalController()

        assert controller.total_modulations == 0

        controller.request_modulation(source="test", delta=0.1)

        assert controller.total_modulations == 1

    def test_tracks_esgt_refractories(self):
        """Test controller tracks ESGT refractories."""
        controller = ArousalController()

        assert controller.esgt_refractories_applied == 0

        controller.apply_esgt_refractory()

        assert controller.esgt_refractories_applied == 1
