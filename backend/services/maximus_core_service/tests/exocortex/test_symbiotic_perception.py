"""
Unit Tests for SymbioticSelf Perception Updates
===============================================
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import json

from services.maximus_core_service.src.consciousness.exocortex.symbiotic_self import (
    SymbioticSelfConcept, DaimonPerception
)
from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    EventType, ConsciousEvent
)

@pytest.fixture
def mock_gemini():
    mock = MagicMock()
    mock.generate_text = AsyncMock()
    return mock

@pytest.fixture
def mock_workspace():
    mock = MagicMock()
    mock.broadcast = AsyncMock()
    return mock

@pytest.fixture
def symbiotic_self(mock_gemini, mock_workspace):
    self_concept = SymbioticSelfConcept()
    self_concept.set_dependencies(mock_gemini, mock_workspace)
    return self_concept

@pytest.mark.asyncio
async def test_update_perception_success(symbiotic_self, mock_gemini, mock_workspace):
    """Testa atualização de percepção com resposta válida do Gemini."""
    
    # 1. Setup Mock
    mock_response = {
        "perceived_emotional_state": "Anxious",
        "perceived_energy_level": 0.8,
        "perceived_alignment": 0.4,
        "perceived_stress_level": 0.9,
        "confidence_in_perception": 0.95
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(mock_response)}

    # 2. Call Method
    perception = await symbiotic_self.update_perception(
        message="I'm freaking out about this deadline!",
        context={"location": "Work"}
    )

    # 3. Assertions
    assert perception.perceived_emotional_state == "Anxious"
    assert perception.perceived_stress_level == 0.9
    assert symbiotic_self.state.daimon_perception == perception
    
    # Verify Broadcast
    mock_workspace.broadcast.assert_called_once()
    event = mock_workspace.broadcast.call_args[0][0]
    assert event.type == EventType.SELF_UPDATED
    assert event.payload["new_perception"]["perceived_emotional_state"] == "Anxious"

@pytest.mark.asyncio
async def test_handle_feedback_event(symbiotic_self, mock_gemini):
    """Testa se evento FEEDBACK_RECEIVED aciona update_perception."""
    
    # Mock Gemini Response
    mock_gemini.generate_text.return_value = {
        "text": '{"perceived_emotional_state": "Calm"}'
    }

    # Simulate Event
    event = ConsciousEvent(
        id="fb_1",
        type=EventType.FEEDBACK_RECEIVED,
        source="User",
        payload={"text": "I feel better now."}
    )

    await symbiotic_self.handle_conscious_event(event)

    # Verify Gemini called
    mock_gemini.generate_text.assert_called_once()
    
    # Verify State Updated
    assert symbiotic_self.state.daimon_perception.perceived_emotional_state == "Calm"

@pytest.mark.asyncio
async def test_trust_evolution_on_violation(symbiotic_self):
    """Testa se violação reduz confiança (contagem de eventos)."""
    initial_breaking = symbiotic_self.state.trust.trust_breaking_events
    
    event = ConsciousEvent(
        id="vio_1",
        type=EventType.CONSTITUTION_VIOLATION,
        source="Guardian",
        payload={}
    )

    await symbiotic_self.handle_conscious_event(event)

    assert symbiotic_self.state.trust.trust_breaking_events == initial_breaking + 1
