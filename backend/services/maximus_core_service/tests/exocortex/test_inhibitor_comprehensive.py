"""
Comprehensive Tests for ImpulseInhibitor
========================================
Goal: >90% coverage for impulse_inhibitor.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from services.maximus_core_service.src.consciousness.exocortex.impulse_inhibitor import (
    ImpulseInhibitor, ImpulseContext, InterventionLevel, Intervention
)
from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    EventType
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
def inhibitor(mock_gemini, mock_workspace):
    return ImpulseInhibitor(mock_gemini, mock_workspace)

@pytest.fixture
def context():
    return ImpulseContext(
        action_type="send_reply",
        content="I hate you!",
        user_state="Angry",
        platform="Twitter"
    )

# --- Logic Tests ---

@pytest.mark.asyncio
async def test_check_impulse_rage_reply(inhibitor, mock_gemini, mock_workspace, context):
    # Mock Gemini to return RAGE_REPLY
    analysis = {
        "emotional_intensity": 0.9,
        "irreversibility": 0.6,
        "alignment": 0.2,
        "detected_impulse": "RAGE_REPLY",
        "reasoning": "Toxic"
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(analysis)}

    intervention = await inhibitor.check_impulse(context)

    # Verify Intervention
    assert intervention.level == InterventionLevel.PAUSE
    assert "High emotional intensity" in intervention.reasoning
    assert intervention.wait_time_seconds == 30

    # Verify Broadcast
    mock_workspace.broadcast.assert_called_once()
    event = mock_workspace.broadcast.call_args[0][0]
    assert event.type == EventType.IMPULSE_DETECTED
    assert event.payload["level"] == "PAUSE"

@pytest.mark.asyncio
async def test_check_impulse_buy(inhibitor, mock_gemini, context):
    # Mock Gemini to return IMPULSE_BUY
    analysis = {
        "emotional_intensity": 0.5,
        "irreversibility": 0.9,
        "alignment": 0.5,
        "detected_impulse": "IMPULSE_BUY",
        "reasoning": "Unplanned"
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(analysis)}

    context.action_type = "click_buy"
    intervention = await inhibitor.check_impulse(context)

    assert intervention.level == InterventionLevel.PAUSE
    assert "impulse buy" in intervention.reasoning
    assert intervention.wait_time_seconds == 60

@pytest.mark.asyncio
async def test_check_impulse_safe(inhibitor, mock_gemini, mock_workspace, context):
    # Mock Gemini to return SAFE
    analysis = {
        "emotional_intensity": 0.2,
        "irreversibility": 0.1,
        "alignment": 0.9,
        "detected_impulse": "NONE",
        "reasoning": "Chill"
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(analysis)}

    intervention = await inhibitor.check_impulse(context)

    assert intervention.level == InterventionLevel.NONE
    # Should NOT broadcast safe events (only Pause/Lockout)
    mock_workspace.broadcast.assert_not_called()

@pytest.mark.asyncio
async def test_check_impulse_low_alignment(inhibitor, mock_gemini, context):
    # Mock Gemini to return Misaligned but not impulsive
    analysis = {
        "emotional_intensity": 0.3,
        "irreversibility": 0.2,
        "alignment": 0.3, # < 0.4
        "detected_impulse": "NONE",
        "reasoning": "Bad idea"
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(analysis)}

    intervention = await inhibitor.check_impulse(context)

    assert intervention.level == InterventionLevel.NOTICE

@pytest.mark.asyncio
async def test_check_impulse_high_emotion_override(inhibitor, mock_gemini, context):
    # Not detected as RAGE_REPLY explicitly but high metrics
    analysis = {
        "emotional_intensity": 0.9,
        "irreversibility": 0.6,
        "alignment": 0.5,
        "detected_impulse": "NONE",
        "reasoning": "Very angry"
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(analysis)}

    intervention = await inhibitor.check_impulse(context)

    assert intervention.level == InterventionLevel.PAUSE

# --- Error Handling Tests ---

@pytest.mark.asyncio
async def test_analyze_risk_json_error(inhibitor, mock_gemini, context):
    mock_gemini.generate_text.return_value = {"text": "Not JSON"}
    
    # Should fail safe to NONE
    intervention = await inhibitor.check_impulse(context)
    
    assert intervention.level == InterventionLevel.NONE
    assert intervention.reasoning == "Safe."

@pytest.mark.asyncio
async def test_analyze_risk_api_error(inhibitor, mock_gemini, context):
    mock_gemini.generate_text.side_effect = Exception("API Fail")
    
    intervention = await inhibitor.check_impulse(context)
    
    assert intervention.level == InterventionLevel.NONE

# --- Misc Tests ---

@pytest.mark.asyncio
async def test_get_status(inhibitor):
    status = await inhibitor.get_status()
    assert status["active"] is True
