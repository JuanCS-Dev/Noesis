"""
Tests for ConfrontationEngine
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from services.maximus_core_service.src.consciousness.exocortex.confrontation_engine import (
    ConfrontationEngine,
    ConfrontationContext,
    ConfrontationStyle,
    ConfrontationTurn
)
from services.maximus_core_service.utils.gemini_client import GeminiClient

@pytest.fixture
def mock_gemini_client():
    client = MagicMock(spec=GeminiClient)
    client.generate_text = AsyncMock()
    return client

@pytest.fixture
def engine(mock_gemini_client):
    return ConfrontationEngine(mock_gemini_client)

@pytest.mark.asyncio
async def test_generate_confrontation_direct(engine, mock_gemini_client):
    """Testa geração de confronto direto (violação)."""
    context = ConfrontationContext(
        trigger_event="Delete database",
        violated_rule_id="R_SAFETY_01"
    )
    
    # Mock response
    mock_gemini_client.generate_text.return_value = {
        "text": "Why would you destroy your own memory?"
    }
    
    turn = await engine.generate_confrontation(context)
    
    assert turn.style_used == ConfrontationStyle.DIRECT_CHALLENGE
    assert turn.ai_question == "Why would you destroy your own memory?"
    assert "Delete database" in str(mock_gemini_client.generate_text.call_args)

@pytest.mark.asyncio
async def test_generate_confrontation_gentle(engine, mock_gemini_client):
    """Testa inquérito gentil (sombra)."""
    context = ConfrontationContext(
        trigger_event="Binge watching",
        shadow_pattern_detected="Procrastination"
    )
    
    mock_gemini_client.generate_text.return_value = {
        "text": "What are you avoiding right now?"
    }
    
    turn = await engine.generate_confrontation(context)
    
    assert turn.style_used == ConfrontationStyle.GENTLE_INQUIRY
    assert turn.ai_question == "What are you avoiding right now?"

@pytest.mark.asyncio
async def test_evaluate_response_honest(engine, mock_gemini_client):
    """Testa avaliação de resposta honesta."""
    turn = ConfrontationTurn(
        id="1", timestamp=datetime.now(), 
        ai_question="Why?", style_used=ConfrontationStyle.GENTLE_INQUIRY
    )
    
    mock_gemini_client.generate_text.return_value = {
        "text": '{"honesty_score": 0.9, "defensiveness_score": 0.1, "is_deflection": false}'
    }
    
    analyzed_turn = await engine.evaluate_response(turn, "Because I am afraid.")
    
    assert analyzed_turn.response_analysis["honesty_score"] == 0.9
    assert analyzed_turn.response_analysis["is_deflection"] is False

@pytest.mark.asyncio
async def test_engine_fallback_on_error(engine, mock_gemini_client):
    """Testa tratamento de erro se Gemini falhar."""
    mock_gemini_client.generate_text.side_effect = Exception("API Down")
    
    context = ConfrontationContext(trigger_event="Fail")
    turn = await engine.generate_confrontation(context)
    
    assert turn.id == "error_fallback"
    assert "dissonância" in turn.ai_question
