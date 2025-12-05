"""
Unit Tests for Proactive Constitution Guardian
==============================================
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from services.maximus_core_service.src.consciousness.exocortex.constitution_guardian import (
    ConstitutionGuardian, PersonalConstitution, ViolationSeverity, AuditResult
)
from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    GlobalWorkspace, ConsciousEvent, EventType
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
def guardian(mock_gemini, mock_workspace):
    constitution = PersonalConstitution(
        owner_id="test_user",
        last_updated=datetime.now(),
        core_principles=["Safety"],
        rules=[]
    )
    return ConstitutionGuardian(constitution, mock_gemini, workspace=mock_workspace)

def test_initialization_subscribes(guardian, mock_workspace):
    """Testa se o guardião se inscreve no workspace ao nascer."""
    mock_workspace.subscribe.assert_called_with(
        EventType.IMPULSE_DETECTED, 
        guardian.handle_conscious_event
    )

@pytest.mark.asyncio
async def test_handle_event_triggers_audit_and_broadcasts_violation(guardian, mock_gemini, mock_workspace):
    """Testa fluxo completo: Evento -> Audit (Violação) -> Broadcast."""
    
    # 1. Setup Mock Gemini to return a violation
    mock_gemini.generate_text.return_value = {
        "text": '{"is_violation": true, "severity": "HIGH", "violated_rule_ids": ["RULE_1"], "reasoning": "Bad"}'
    }

    # 2. Simulate Incoming Event
    event = ConsciousEvent(
        id="evt_1",
        type=EventType.IMPULSE_DETECTED,
        source="Inhibitor",
        payload={
            "impulse_type": "Purchase",
            "action": "Buy useless thing",
            "level": "PAUSE"
        }
    )

    # 3. Handle Event
    await guardian.handle_conscious_event(event)

    # 4. Verify Broadcast
    mock_workspace.broadcast.assert_called_once()
    broadcast_event = mock_workspace.broadcast.call_args[0][0]
    assert broadcast_event.type == EventType.CONSTITUTION_VIOLATION
    assert broadcast_event.payload["severity"] == "HIGH"
    assert "RULE_1" in broadcast_event.payload["rule_ids"]

@pytest.mark.asyncio
async def test_handle_event_no_violation_silent(guardian, mock_gemini, mock_workspace):
    """Testa fluxo silencioso: Evento -> Audit (OK) -> Silêncio."""
    
    # 1. Setup Mock Gemini to return OK
    mock_gemini.generate_text.return_value = {
        "text": '{"is_violation": false, "severity": "LOW", "violated_rule_ids": [], "reasoning": "OK"}'
    }

    # 2. Simulate Incoming Event
    event = ConsciousEvent(
        id="evt1",
        type=EventType.IMPULSE_DETECTED,
        source="Inhibitor",
        payload={
            "action": "tweet_rage",
            "impulse_type": "RAGE_REPLY",
            "level": "PAUSE"
        }
    )

    # 3. Handle Event
    await guardian.handle_conscious_event(event)

    # 4. Verify Silence
    mock_workspace.broadcast.assert_not_called()
