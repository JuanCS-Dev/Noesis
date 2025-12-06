"""Tests for reactive_fabric/orchestration/data_orchestrator_models.py"""

from consciousness.reactive_fabric.orchestration.data_orchestrator_models import (
    OrchestrationDecision,
)


class TestOrchestrationDecision:
    """Test OrchestrationDecision dataclass."""

    def test_creation(self):
        """Test creating orchestration decision."""
        decision = OrchestrationDecision(
            should_trigger_esgt=True,
            salience=None,  # TYPE_CHECKING only
            reason="High salience detected",
            triggering_events=[],
            metrics_snapshot=None,  # TYPE_CHECKING only
            timestamp=1234567890.0,
            confidence=0.95,
        )

        assert decision.should_trigger_esgt is True
        assert decision.reason == "High salience detected"
        assert decision.timestamp == 1234567890.0
        assert decision.confidence == 0.95
        assert decision.triggering_events == []
