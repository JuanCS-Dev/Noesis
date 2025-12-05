"""
Unit Tests for Confrontation Engine Logic
=========================================
Tests the internal logic of style determination and response evaluation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from services.maximus_core_service.src.consciousness.exocortex.confrontation_engine import (
    ConfrontationEngine, ConfrontationContext, ConfrontationStyle, ConfrontationTurn
)

@pytest.fixture
def mock_gemini():
    mock = MagicMock()
    mock.generate_text = AsyncMock()
    return mock

@pytest.fixture
def engine(mock_gemini):
    return ConfrontationEngine(gemini_client=mock_gemini)

def test_determine_style_direct_challenge(engine):
    """Testa se violação de regra aciona desafio direto."""
    ctx = ConfrontationContext(
        trigger_event="Violation",
        violated_rule_id="RULE_001"
    )
    style = engine._determine_style(ctx) # pylint: disable=protected-access
    assert style == ConfrontationStyle.DIRECT_CHALLENGE

def test_determine_style_gentle_inquiry(engine):
    """Testa se padrão de sombra aciona inquérito gentil."""
    ctx = ConfrontationContext(
        trigger_event="Shadow",
        shadow_pattern_detected="Avoidance"
    )
    style = engine._determine_style(ctx) # pylint: disable=protected-access
    assert style == ConfrontationStyle.GENTLE_INQUIRY

def test_determine_style_philosophical(engine):
    """Testa fallback para filosófico."""
    ctx = ConfrontationContext(trigger_event="Random")
    style = engine._determine_style(ctx) # pylint: disable=protected-access
    assert style == ConfrontationStyle.PHILOSOPHICAL

@pytest.mark.asyncio
async def test_generate_confrontation_success(engine, mock_gemini):
    """Testa geração bem sucedida de pergunta."""
    mock_gemini.generate_text.return_value = {"text": "Why?"}
    
    ctx = ConfrontationContext(trigger_event="Test")
    turn = await engine.generate_confrontation(ctx)
    
    assert turn.ai_question == "Why?"
    assert turn.style_used == ConfrontationStyle.PHILOSOPHICAL

@pytest.mark.asyncio
async def test_evaluate_response_parsing(engine, mock_gemini):
    """Testa parsing da análise de resposta."""
    mock_gemini.generate_text.return_value = {
        "text": '{"honesty_score": 0.9, "defensiveness_score": 0.1, "is_deflection": false}'
    }
    
    turn = ConfrontationTurn(
        id="1", timestamp=datetime.now(), 
        ai_question="?", style_used=ConfrontationStyle.GENTLE_INQUIRY
    )
    
    result = await engine.evaluate_response(turn, "Because I wanted to.")
    
    assert result.response_analysis["honesty_score"] == 0.9
    assert result.response_analysis["is_deflection"] is False

@pytest.mark.asyncio
async def test_evaluate_response_json_error(engine, mock_gemini):
    """Testa resiliência a JSON inválido."""
    mock_gemini.generate_text.return_value = {"text": "Invalid JSON"}
    
    turn = ConfrontationTurn(
        id="1", timestamp=datetime.now(), 
        ai_question="?", style_used=ConfrontationStyle.GENTLE_INQUIRY
    )
    
    result = await engine.evaluate_response(turn, "Dunno")
    
    assert result.response_analysis == {} # Should be empty dict on parsing failure
