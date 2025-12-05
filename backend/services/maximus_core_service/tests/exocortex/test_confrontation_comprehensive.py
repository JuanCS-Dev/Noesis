"""
Comprehensive Tests for ConfrontationEngine
===========================================
Goal: >90% coverage for confrontation_engine.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import json

from services.maximus_core_service.src.consciousness.exocortex.confrontation_engine import (
    ConfrontationEngine,
    ConfrontationContext,
    ConfrontationStyle,
    ConfrontationTurn
)
from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    EventType,
    ConsciousEvent
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
def engine(mock_gemini, mock_workspace):
    return ConfrontationEngine(mock_gemini, mock_workspace)

# --- Initialization Tests ---
def test_init_registers_subscribers(engine, mock_workspace):
    assert mock_workspace.subscribe.call_count == 2
    # Check calls
    call_args = [c[0][0] for c in mock_workspace.subscribe.call_args_list]
    assert EventType.IMPULSE_DETECTED in call_args
    assert EventType.CONSTITUTION_VIOLATION in call_args

# --- Event Handling Tests ---
@pytest.mark.asyncio
async def test_handle_impulse_event(engine, mock_gemini):
    mock_gemini.generate_text.return_value = {"text": "Why rush?"}
    
    event = ConsciousEvent(
        id="evt1",
        type=EventType.IMPULSE_DETECTED,
        source="Browser",
        payload={
            "level": "BLOCK",
            "impulse_type": "Twitter",
            "user_state": "Bored"
        }
    )
    
    await engine.handle_conscious_event(event)
    
    # Verify Gemini called
    mock_gemini.generate_text.assert_called_once()
    args = mock_gemini.generate_text.call_args.kwargs
    prompt = args["prompt"]
    assert "Twitter" in prompt
    assert "Bored" in prompt

@pytest.mark.asyncio
async def test_handle_violation_event(engine, mock_gemini):
    mock_gemini.generate_text.return_value = {"text": "What rule?"}
    
    event = ConsciousEvent(
        id="evt2",
        type=EventType.CONSTITUTION_VIOLATION,
        source="Guardian",
        payload={"rule_ids": ["R1"]}
    )
    
    await engine.handle_conscious_event(event)

    # Check style in prompt (hard to check directly without refactoring, but prompt contains style)
    prompt = mock_gemini.generate_text.call_args.kwargs["prompt"]
    assert "DIRECT_CHALLENGE" in prompt

@pytest.mark.asyncio
async def test_handle_ignored_events(engine, mock_gemini):
    event = ConsciousEvent(id="e", type=EventType.IMPULSE_DETECTED, source="Test", payload={"level": "ALLOW"})
    await engine.handle_conscious_event(event)
    mock_gemini.generate_text.assert_not_called()

# --- Style Determination Tests ---
def test_determine_style(engine):
    # Rule Violation -> Direct
    ctx1 = ConfrontationContext("trigger", violated_rule_id="R1")
    assert engine._determine_style(ctx1) == ConfrontationStyle.DIRECT_CHALLENGE

    # Shadow -> Gentle
    ctx2 = ConfrontationContext("trigger", shadow_pattern_detected="Ego")
    assert engine._determine_style(ctx2) == ConfrontationStyle.GENTLE_INQUIRY

    # Else -> Philosophical
    ctx3 = ConfrontationContext("trigger")
    assert engine._determine_style(ctx3) == ConfrontationStyle.PHILOSOPHICAL

# --- Generation Tests ---
@pytest.mark.asyncio
async def test_generate_confrontation_success(engine, mock_gemini):
    mock_gemini.generate_text.return_value = {"text": "Why do you feel this way?"}
    
    ctx = ConfrontationContext("trigger", shadow_pattern_detected="Fear")
    turn = await engine.generate_confrontation(ctx)
    
    assert turn.ai_question == "Why do you feel this way?"
    assert turn.style_used == ConfrontationStyle.GENTLE_INQUIRY

@pytest.mark.asyncio
async def test_generate_confrontation_empty_text(engine, mock_gemini):
    mock_gemini.generate_text.return_value = {"text": ""}
    
    ctx = ConfrontationContext("trigger")
    turn = await engine.generate_confrontation(ctx)
    
    assert turn.ai_question == "Por que você escolheu agir assim?" # Fallback

@pytest.mark.asyncio
async def test_generate_confrontation_error(engine, mock_gemini):
    mock_gemini.generate_text.side_effect = Exception("API Error")
    
    ctx = ConfrontationContext("trigger")
    turn = await engine.generate_confrontation(ctx)
    
    assert turn.id == "error_fallback"
    assert "dissonância" in turn.ai_question

# --- Evaluation Tests ---
@pytest.mark.asyncio
async def test_evaluate_response_success(engine, mock_gemini):
    analysis_data = {
        "honesty_score": 0.9,
        "defensiveness_score": 0.1,
        "is_deflection": False,
        "key_insight": "Insight"
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(analysis_data)}
    
    turn = ConfrontationTurn("t1", datetime.now(), "Q", ConfrontationStyle.DIRECT_CHALLENGE)
    
    processed_turn = await engine.evaluate_response(turn, "I made a mistake.")
    
    assert processed_turn.user_response == "I made a mistake."
    assert processed_turn.response_analysis["honesty_score"] == 0.9

@pytest.mark.asyncio
async def test_evaluate_response_json_error(engine, mock_gemini):
    mock_gemini.generate_text.return_value = {"text": "Not JSON"}
    
    turn = ConfrontationTurn("t1", datetime.now(), "Q", ConfrontationStyle.DIRECT_CHALLENGE)
    
    processed_turn = await engine.evaluate_response(turn, "Response")
    
    assert processed_turn.response_analysis == {}

@pytest.mark.asyncio
async def test_evaluate_response_api_error(engine, mock_gemini):
    mock_gemini.generate_text.side_effect = Exception("API Fail")
    
    turn = ConfrontationTurn("t1", datetime.now(), "Q", ConfrontationStyle.DIRECT_CHALLENGE)
    
    processed_turn = await engine.evaluate_response(turn, "Response")
    
    assert "error" in processed_turn.response_analysis
