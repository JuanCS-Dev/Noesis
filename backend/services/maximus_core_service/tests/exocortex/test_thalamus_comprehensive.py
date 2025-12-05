"""
Comprehensive Tests for DigitalThalamus
=======================================
Goal: >90% coverage for digital_thalamus.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json
from datetime import datetime

from services.maximus_core_service.src.consciousness.exocortex.digital_thalamus import (
    DigitalThalamus, Stimulus, StimulusType, AttentionStatus, ThalamusDecision
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
def thalamus(mock_gemini, mock_workspace):
    return DigitalThalamus(mock_gemini, mock_workspace)

@pytest.fixture
def basic_stimulus():
    return Stimulus(
        id="s1",
        type=StimulusType.MESSAGE,
        source="Slack",
        content="Urgent meeting"
    )

# --- Logic Tests ---

@pytest.mark.asyncio
async def test_hard_rule_block_ads_focus(thalamus, mock_gemini):
    stim = Stimulus("s_ad", StimulusType.ADVERTISEMENT, "Web", "Buy now!")
    
    # decision should be hard-coded BLOCK without calling Gemini
    decision = await thalamus.filter_stimulus(stim, AttentionStatus.FOCUS)
    
    assert decision.action == "BLOCK"
    assert "Absolute block" in decision.reasoning
    mock_gemini.generate_text.assert_not_called()

@pytest.mark.asyncio
async def test_filter_focus_high_urgency(thalamus, mock_gemini, basic_stimulus):
    # Mock Gemini High Urgency
    mock_gemini.generate_text.return_value = {"text": json.dumps({
        "urgency": 0.9,
        "dopamine": 0.1,
        "relevance": 0.9,
        "brief_reasoning": "Critical"
    })}
    
    decision = await thalamus.filter_stimulus(basic_stimulus, AttentionStatus.FOCUS)
    
    assert decision.action == "ALLOW" # Urgency > 0.8 passes focus

@pytest.mark.asyncio
async def test_filter_focus_low_urgency(thalamus, mock_gemini, basic_stimulus):
    # Mock Gemini Low Urgency
    mock_gemini.generate_text.return_value = {"text": json.dumps({
        "urgency": 0.3,
        "dopamine": 0.5,
        "relevance": 0.2,
        "brief_reasoning": "Not important"
    })}
    
    decision = await thalamus.filter_stimulus(basic_stimulus, AttentionStatus.FOCUS)
    
    assert decision.action == "BLOCK" # Urgency < 0.4 -> BLOCK

@pytest.mark.asyncio
async def test_filter_flow_medium_urgency(thalamus, mock_gemini, basic_stimulus):
    # Mock Gemini Medium Urgency
    mock_gemini.generate_text.return_value = {"text": json.dumps({
        "urgency": 0.5,
        "dopamine": 0.2,
        "relevance": 0.5,
        "brief_reasoning": "Medium"
    })}
    
    decision = await thalamus.filter_stimulus(basic_stimulus, AttentionStatus.FLOW)
    
    assert decision.action == "BATCH" # < 0.6 in Flow -> Batch

@pytest.mark.asyncio
async def test_filter_resting_high_dopamine(thalamus, mock_gemini, basic_stimulus):
    mock_gemini.generate_text.return_value = {"text": json.dumps({
        "urgency": 0.1,
        "dopamine": 0.9,
        "relevance": 0.1,
        "brief_reasoning": "Fun"
    })}
    
    decision = await thalamus.filter_stimulus(basic_stimulus, AttentionStatus.RESTING)
    
    assert decision.action == "ALLOW"
    assert "Warning: High Dopamine" in decision.reasoning

@pytest.mark.asyncio
async def test_broadcast_decision(thalamus, mock_gemini, mock_workspace, basic_stimulus):
    mock_gemini.generate_text.return_value = {"text": json.dumps({
        "urgency": 0.5, "dopamine": 0.5, "relevance": 0.5, "brief_reasoning": "OK"
    })}
    
    await thalamus.filter_stimulus(basic_stimulus, AttentionStatus.NEUTRAL)
    
    mock_workspace.broadcast.assert_called_once()
    evt = mock_workspace.broadcast.call_args[0][0]
    assert evt.type == EventType.STIMULUS_FILTERED
    assert evt.payload["stimulus_id"] == "s1"
    assert evt.payload["decision"] == "ALLOW"

# --- Error Handling ---

@pytest.mark.asyncio
async def test_analyze_stimulus_json_error(thalamus, mock_gemini, basic_stimulus):
    mock_gemini.generate_text.return_value = {"text": "Bad JSON"}
    
    # Should fallback to safe default (urgency 0.5 -> ALLOW in Neutral?)
    decision = await thalamus.filter_stimulus(basic_stimulus, AttentionStatus.NEUTRAL)
    
    assert decision.reasoning == "Analysis Failed"
    assert decision.urgency_score == 0.5

@pytest.mark.asyncio
async def test_analyze_stimulus_api_error(thalamus, mock_gemini, basic_stimulus):
    mock_gemini.generate_text.side_effect = Exception("API")
    
    decision = await thalamus.filter_stimulus(basic_stimulus, AttentionStatus.NEUTRAL)
    
    assert decision.reasoning == "Analysis Failed"
