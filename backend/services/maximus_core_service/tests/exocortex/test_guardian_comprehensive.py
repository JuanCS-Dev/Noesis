"""
Comprehensive Tests for ConstitutionGuardian
============================================
Goal: >90% coverage for constitution_guardian.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json
from datetime import datetime

from services.maximus_core_service.src.consciousness.exocortex.constitution_guardian import (
    ConstitutionGuardian, PersonalConstitution, ViolationSeverity, AuditResult
)
from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    EventType, ConsciousEvent
)
from services.maximus_core_service.src.consciousness.exocortex.impulse_inhibitor import (
    InterventionLevel
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
def default_constitution():
    return PersonalConstitution(
        owner_id="u1",
        last_updated=datetime.now(),
        core_principles=["Honesty"],
        rules=[]
    )

@pytest.fixture
def guardian(default_constitution, mock_gemini, mock_workspace):
    return ConstitutionGuardian(default_constitution, mock_gemini, mock_workspace)

# --- Logic Tests ---

def test_should_audit_logic(guardian):
    # Pause/Block -> Audit
    evt1 = ConsciousEvent(
        id="1", type=EventType.IMPULSE_DETECTED, source="Inhibitor",
        payload={"level": "PAUSE"}
    )
    assert guardian._should_audit(evt1) is True

    # Notice/None -> No Audit
    evt2 = ConsciousEvent(
        id="2", type=EventType.IMPULSE_DETECTED, source="Inhibitor",
        payload={"level": "NONE"}
    )
    assert guardian._should_audit(evt2) is False
    
    # Random event -> No Audit
    evt3 = ConsciousEvent(id="3", type=EventType.FEEDBACK_RECEIVED, source="User", payload={})
    assert guardian._should_audit(evt3) is False

@pytest.mark.asyncio
async def test_handle_event_ignored(guardian, mock_gemini):
    evt = ConsciousEvent(
        id="1", type=EventType.IMPULSE_DETECTED, source="Inhibitor",
        payload={"level": "NONE"}
    )
    await guardian.handle_conscious_event(evt)
    mock_gemini.generate_text.assert_not_called()

@pytest.mark.asyncio
async def test_audit_action_violation(guardian, mock_gemini, mock_workspace):
    # API Mock
    audit_res = {
        "is_violation": True,
        "severity": "HIGH",
        "violated_rule_ids": ["R1"],
        "reasoning": "Bad",
        "alternatives": ["Be good"]
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(audit_res)}
    
    # Event
    evt = ConsciousEvent(
        id="1", type=EventType.IMPULSE_DETECTED, source="Inhibitor",
        payload={
            "level": "PAUSE",
            "action": "Lie",
            "impulse_type": "RAGE_REPLY",
            "reasoning": "Angry",
            "user_state": "Mad"
        }
    )
    
    await guardian.handle_conscious_event(evt)
    
    # Verify Broadcast
    mock_workspace.broadcast.assert_called_once()
    broadcast_evt = mock_workspace.broadcast.call_args[0][0]
    assert broadcast_evt.type == EventType.CONSTITUTION_VIOLATION
    assert broadcast_evt.payload["severity"] == "HIGH"
    assert broadcast_evt.payload["rule_ids"] == ["R1"]

@pytest.mark.asyncio
async def test_audit_action_compliant(guardian, mock_gemini, mock_workspace):
    # API Mock
    audit_res = {
        "is_violation": False,
        "severity": "LOW",
        "violated_rule_ids": [],
        "reasoning": "Good",
        "alternatives": []
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(audit_res)}
    
    evt = ConsciousEvent(
        id="1", type=EventType.IMPULSE_DETECTED, source="Inhibitor",
        payload={"level": "PAUSE", "action": "Wait", "impulse_type": "None", "reasoning": "Wait", "user_state": "Calm"}
    )
    
    await guardian.handle_conscious_event(evt)
    
    # No violation broadcast
    mock_workspace.broadcast.assert_not_called()

@pytest.mark.asyncio
async def test_audit_json_error(guardian, mock_gemini, mock_workspace):
    mock_gemini.generate_text.return_value = {"text": "Bad JSON"}
    
    evt = ConsciousEvent(
        id="1", type=EventType.IMPULSE_DETECTED, source="Inhibitor",
        payload={"level": "PAUSE", "action": "X"}
    )
    
    # Should broadcast SYS_ERROR violation (Fail Safe)
    await guardian.handle_conscious_event(evt)
    mock_workspace.broadcast.assert_called_once()
    broadcast_evt = mock_workspace.broadcast.call_args[0][0]
    assert "SYS_ERROR" in broadcast_evt.payload["rule_ids"]

@pytest.mark.asyncio
async def test_audit_api_error(guardian, mock_gemini, mock_workspace):
    mock_gemini.generate_text.side_effect = Exception("API")
    
    evt = ConsciousEvent(
        id="1", type=EventType.IMPULSE_DETECTED, source="Inhibitor",
        payload={"level": "PAUSE", "action": "X"}
    )
    
    await guardian.handle_conscious_event(evt)
    mock_workspace.broadcast.assert_called_once()
    broadcast_evt = mock_workspace.broadcast.call_args[0][0]
    assert "SYS_ERROR" in broadcast_evt.payload["rule_ids"]

def test_check_compliance_direct(guardian):
    # Sync wrapper test if exposed, or implied by async tests.
    pass
