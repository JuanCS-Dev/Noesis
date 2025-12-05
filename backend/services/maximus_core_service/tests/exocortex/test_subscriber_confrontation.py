"""
Integration Test for Confrontation Subscriber
=============================================
Verifies that ConfrontationEngine reacts to workspace events.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    EventType, ConsciousEvent
)

@pytest.mark.asyncio
async def test_impulse_event_triggers_confrontation(test_factory, mock_gemini):
    """
    Testa se um evento IMPULSE_DETECTED (nível PAUSE) aciona o ConfrontationEngine.
    """
    # 1. Setup: Mockar resposta do Gemini para a confrontação
    # 1. Setup: Mockar resposta do Gemini
    # Agora temos DOIS chamadores: Guardian (Audit) e Confrontation (Question)
    # Call 1: Guardian Audit -> "Correct JSON, No Violation"
    # Call 2: Confrontation -> "Question text"
    mock_gemini.generate_text.side_effect = [
        # Response 1: Guardian Audit (Safe)
        {
            "text": '{"is_violation": false, "severity": "LOW", "violated_rule_ids": [], "reasoning": "Audit OK"}'
        },
        # Response 2: Confrontation Logic
        {
            "text": "Why did you act impulsively?"
        }
    ]

    # 2. Action: Publicar evento no Workspace
    event = ConsciousEvent(
        id="evt_impulse_1",
        type=EventType.IMPULSE_DETECTED,
        source="ImpulseInhibitor",
        payload={
            "level": "PAUSE",
            "impulse_type": "AGRESSION",
            "user_state": "ANGRY"
        }
    )
    
    await test_factory.workspace.broadcast(event)

    # Allow async processing
    await asyncio.sleep(0.1)

    # 3. Assertion: Verificar se generate_confrontation foi chamado
    # O método handle_conscious_event chama generate_confrontation
    # generate_confrontation chama self.gemini_client.generate_text
    
    mock_gemini.generate_text.assert_called()
    
    # Verificar se o prompt contem o contexto do evento
    # Verificar se o prompt contem o contexto do evento
    # Precisamos pegar o SEGUNDO call (o primeiro foi do Guardian)
    assert mock_gemini.generate_text.call_count >= 2
    call_args = mock_gemini.generate_text.call_args_list[1] # Index 1 = Second Call
    
    prompt_used = call_args.kwargs.get("prompt") or call_args.args[0]
    
    assert "Impulse PAUSE: AGRESSION" in prompt_used
    assert "User State: ANGRY" in prompt_used
