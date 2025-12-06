"""Tests for api_schemas.py"""

import pytest
from pydantic import ValidationError

from consciousness.api_schemas import (
    ArousalAdjustment,
    ConsciousnessStateResponse,
    EmergencyShutdownRequest,
    ESGTEventResponse,
    SafetyStatusResponse,
    SafetyViolationResponse,
    SalienceInput,
)


class TestSalienceInput:
    """Test SalienceInput Pydantic model."""

    def test_creation_valid(self):
        """Test creating valid salience input."""
        input_data = SalienceInput(
            novelty=0.8,
            relevance=0.7,
            urgency=0.9,
        )
        
        assert input_data.novelty == 0.8
        assert input_data.relevance == 0.7
        assert input_data.urgency == 0.9
        assert input_data.context == {}

    def test_creation_with_context(self):
        """Test creating with context."""
        ctx = {"source": "visual", "priority": "high"}
        input_data = SalienceInput(
            novelty=0.5,
            relevance=0.6,
            urgency=0.7,
            context=ctx,
        )
        
        assert input_data.context == ctx

    def test_validation_novelty_too_high(self):
        """Test validation fails for novelty > 1.0."""
        with pytest.raises(ValidationError):
            SalienceInput(novelty=1.5, relevance=0.5, urgency=0.5)

    def test_validation_relevance_negative(self):
        """Test validation fails for negative relevance."""
        with pytest.raises(ValidationError):
            SalienceInput(novelty=0.5, relevance=-0.1, urgency=0.5)


class TestArousalAdjustment:
    """Test ArousalAdjustment Pydantic model."""

    def test_creation_valid(self):
        """Test creating valid arousal adjustment."""
        adj = ArousalAdjustment(delta=0.2)
        
        assert adj.delta == 0.2
        assert adj.duration_seconds == 5.0
        assert adj.source == "manual"

    def test_creation_custom(self):
        """Test creating with custom values."""
        adj = ArousalAdjustment(
            delta=-0.3,
            duration_seconds=10.0,
            source="automated",
        )
        
        assert adj.delta == -0.3
        assert adj.duration_seconds == 10.0
        assert adj.source == "automated"

    def test_validation_delta_too_high(self):
        """Test validation fails for delta > 0.5."""
        with pytest.raises(ValidationError):
            ArousalAdjustment(delta=0.6)

    def test_validation_delta_too_low(self):
        """Test validation fails for delta < -0.5."""
        with pytest.raises(ValidationError):
            ArousalAdjustment(delta=-0.6)


class TestConsciousnessStateResponse:
    """Test ConsciousnessStateResponse Pydantic model."""

    def test_creation(self):
        """Test creating consciousness state response."""
        response = ConsciousnessStateResponse(
            timestamp="2025-12-05T10:30:00Z",
            esgt_active=True,
            arousal_level=0.7,
            arousal_classification="focused",
            tig_metrics={"coherence": 0.85},
            recent_events_count=3,
            system_health="healthy",
        )
        
        assert response.timestamp == "2025-12-05T10:30:00Z"
        assert response.esgt_active is True
        assert response.arousal_level == 0.7
        assert response.tig_metrics == {"coherence": 0.85}


class TestESGTEventResponse:
    """Test ESGTEventResponse Pydantic model."""

    def test_creation_success(self):
        """Test creating successful ESGT event."""
        response = ESGTEventResponse(
            event_id="evt-001",
            timestamp="2025-12-05T10:30:00Z",
            success=True,
            salience={"novelty": 0.8, "relevance": 0.9},
            coherence=0.85,
            duration_ms=150.0,
            nodes_participating=12,
            reason=None,
        )
        
        assert response.event_id == "evt-001"
        assert response.success is True
        assert response.coherence == 0.85

    def test_creation_failure(self):
        """Test creating failed ESGT event."""
        response = ESGTEventResponse(
            event_id="evt-002",
            timestamp="2025-12-05T10:31:00Z",
            success=False,
            salience={"novelty": 0.5, "relevance": 0.6},
            coherence=None,
            duration_ms=None,
            nodes_participating=0,
            reason="Insufficient coherence",
        )
        
        assert response.success is False
        assert response.reason == "Insufficient coherence"


class TestSafetyStatusResponse:
    """Test SafetyStatusResponse Pydantic model."""

    def test_creation(self):
        """Test creating safety status response."""
        response = SafetyStatusResponse(
            monitoring_active=True,
            kill_switch_active=False,
            violations_total=5,
            violations_by_severity={"low": 3, "medium": 2},
            last_violation="High arousal",
            uptime_seconds=3600.0,
        )
        
        assert response.monitoring_active is True
        assert response.violations_total == 5
        assert response.uptime_seconds == 3600.0

    def test_creation_no_violations(self):
        """Test creating status with no violations."""
        response = SafetyStatusResponse(
            monitoring_active=True,
            kill_switch_active=False,
            violations_total=0,
            violations_by_severity={},
            last_violation=None,
            uptime_seconds=1800.0,
        )
        
        assert response.violations_total == 0
        assert response.last_violation is None


class TestSafetyViolationResponse:
    """Test SafetyViolationResponse Pydantic model."""

    def test_creation(self):
        """Test creating safety violation response."""
        response = SafetyViolationResponse(
            violation_id="viol-001",
            violation_type="arousal_spike",
            severity="medium",
            timestamp="2025-12-05T10:30:00Z",
            value_observed=0.95,
            threshold_violated=0.90,
            message="Arousal exceeded threshold",
            context={"source": "mcea"},
        )
        
        assert response.violation_id == "viol-001"
        assert response.violation_type == "arousal_spike"
        assert response.severity == "medium"
        assert response.value_observed == 0.95
        assert response.threshold_violated == 0.90


class TestEmergencyShutdownRequest:
    """Test EmergencyShutdownRequest Pydantic model."""

    def test_creation_valid(self):
        """Test creating valid emergency shutdown request."""
        request = EmergencyShutdownRequest(
            reason="Critical safety violation detected",
        )
        
        assert request.reason == "Critical safety violation detected"
        assert request.allow_override is True

    def test_creation_custom(self):
        """Test creating with custom values."""
        request = EmergencyShutdownRequest(
            reason="Manual intervention required immediately",
            allow_override=False,
        )
        
        assert request.allow_override is False

    def test_validation_reason_too_short(self):
        """Test validation fails for short reason."""
        with pytest.raises(ValidationError):
            EmergencyShutdownRequest(reason="Short")
