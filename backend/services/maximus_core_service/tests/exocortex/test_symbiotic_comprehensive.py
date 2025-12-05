"""
Comprehensive Tests for SymbioticSelf
=====================================
Goal: >90% coverage for symbiotic_self.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json
from datetime import datetime

from services.maximus_core_service.src.consciousness.exocortex.symbiotic_self import (
    SymbioticSelfConcept, HumanValue, ValuePriority, DaimonPerception
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
    mock.subscribe = MagicMock()
    mock.broadcast = AsyncMock()
    return mock

@pytest.fixture
def self_concept(mock_gemini, mock_workspace):
    # Initialize with dependencies
    s = SymbioticSelfConcept()
    s.set_dependencies(mock_gemini, mock_workspace)
    return s

# --- Logic Tests ---

@pytest.mark.asyncio
async def test_handle_violation_decreases_trust(self_concept):
    initial_trust = self_concept.trust.trust_breaking_events
    
    evt = ConsciousEvent(
        id="1", type=EventType.CONSTITUTION_VIOLATION, source="Guardian", payload={}
    )
    await self_concept.handle_conscious_event(evt)
    
    assert self_concept.trust.trust_breaking_events == initial_trust + 1

@pytest.mark.asyncio
async def test_handle_confrontation_increases_trust(self_concept):
    initial_conf = self_concept.state.meaningful_confrontations
    initial_build = self_concept.trust.trust_building_events
    
    evt = ConsciousEvent(
        id="1", type=EventType.CONFRONTATION_COMPLETED, source="Engine", payload={}
    )
    await self_concept.handle_conscious_event(evt)
    
    assert self_concept.state.meaningful_confrontations == initial_conf + 1
    assert self_concept.trust.trust_building_events == initial_build + 1

@pytest.mark.asyncio
async def test_handle_feedback_triggers_perception(self_concept, mock_gemini, mock_workspace):
    # Mock Gemini
    mock_gemini.generate_text.return_value = {"text": json.dumps({
        "perceived_emotional_state": "Happy",
        "perceived_energy_level": 0.8,
        "perceived_alignment": 0.9,
        "perceived_stress_level": 0.1,
        "confidence_in_perception": 0.9
    })}
    
    evt = ConsciousEvent(
        id="1", type=EventType.FEEDBACK_RECEIVED, source="User", 
        payload={"text": "I feel great!"}
    )
    await self_concept.handle_conscious_event(evt)
    
    # Verify Perception Updated
    assert self_concept.daimon_perception.perceived_emotional_state == "Happy"
    
    # Verify Broadcast
    mock_workspace.broadcast.assert_called_once()
    broadcast_evt = mock_workspace.broadcast.call_args[0][0]
    assert broadcast_evt.type == EventType.SELF_UPDATED
    assert broadcast_evt.payload["new_perception"]["perceived_emotional_state"] == "Happy"

@pytest.mark.asyncio
async def test_update_perception_api_error(self_concept, mock_gemini):
    mock_gemini.generate_text.side_effect = Exception("API Fail")
    
    # Should handle gracefully and return fallback or None
    # Method returns daimon_perception or fallback
    perception = await self_concept.update_perception("msg", {})
    
    assert perception.perceived_emotional_state == "ERROR"

def test_detect_value_conflict_found(self_concept):
    # Setup value
    val = HumanValue(
        name="Honesty", definition="Truth", priority=ValuePriority.CORE,
        examples_positive=["Truth"], examples_negative=["Lie", "Deceive"],
        declared_at=datetime.now(), last_validated=datetime.now()
    )
    self_concept.human_values.append(val)
    
    conflict = self_concept.detect_value_conflict("I will Lie to him")
    assert conflict is not None
    assert conflict["conflicting_value"] == "Honesty"

def test_detect_value_conflict_none(self_concept):
    conflict = self_concept.detect_value_conflict("I will sleep")
    assert conflict is None

def test_generate_report(self_concept):
    # Set dummy perception
    self_concept.daimon_perception = DaimonPerception(
        "Calm", 0.5, 0.5, 0.5, 0.5, datetime.now()
    )
    report = self_concept.generate_symbiotic_report()
    assert "Estabilidade percebida." in report
    assert "=== RELATÓRIO ===" in report

def test_perception_to_narrative():
    p = DaimonPerception("Stress", 0.2, 0.4, 0.8, 1.0, datetime.now())
    narrative = p.to_narrative()
    assert "tensão significativa" in narrative
    assert "desalinhadas" in narrative
    assert "energia parece baixo" in narrative
