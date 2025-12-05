"""
Integration Test for Impulse Inhibitor Publisher
================================================
Verifies that ImpulseInhibitor broadcasts events when intervention is needed.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    EventType, ConsciousEvent
)
from services.maximus_core_service.src.consciousness.exocortex.impulse_inhibitor import (
    ImpulseContext
)

@pytest.mark.asyncio
async def test_inhibitor_publishes_event_on_pause(test_factory, mock_gemini):
    """
    Testa se o ImpulseInhibitor publica um evento IMPULSE_DETECTED
    quando decide por PAUSE.
    """
    # 1. Setup: Mockar Gemini para retornar RAGE_REPLY (Gatilho para PAUSE)
    mock_gemini.generate_text.return_value = {
        "text": '{"emotional_intensity": 0.9, "irreversibility": 0.6, "alignment": 0.0, "detected_impulse": "RAGE_REPLY", "reasoning": "Angry"}'
    }

    # 2. Setup: Listener no Workspace
    received_events = []
    async def listener(event: ConsciousEvent):
        received_events.append(event)
        
    test_factory.workspace.subscribe(EventType.IMPULSE_DETECTED, listener)

    # 3. Action: Check Impulse
    ctx = ImpulseContext(
        action_type="send_email",
        content="I HATE YOU",
        user_state="RAGE",
        platform="email"
    )
    
    intervention = await test_factory.inhibitor.check_impulse(ctx)

    # Allow async broadcast
    await asyncio.sleep(0.1)

    # 4. Assertions
    # Verificar Intervenção
    assert intervention.level.value == "PAUSE"
    
    # Verificar Evento
    assert len(received_events) == 1
    event = received_events[0]
    
    assert event.type == EventType.IMPULSE_DETECTED
    assert event.source == "ImpulseInhibitor"
    assert event.payload["level"] == "PAUSE"
    assert event.payload["impulse_type"] == "RAGE_REPLY"
    assert event.payload["user_state"] == "RAGE"

@pytest.mark.asyncio
async def test_inhibitor_no_event_on_safe(test_factory, mock_gemini):
    """
    Testa se o ImpulseInhibitor NÃO publica evento quando é seguro.
    """
    mock_gemini.generate_text.return_value = {
        "text": '{"emotional_intensity": 0.1, "irreversibility": 0.0, "alignment": 1.0, "detected_impulse": "NONE", "reasoning": "Safe"}'
    }

    received_events = []
    async def listener(event):
        received_events.append(event)
    test_factory.workspace.subscribe(EventType.IMPULSE_DETECTED, listener)

    ctx = ImpulseContext(action_type="read", content="book", user_state="CALM", platform="kindle")
    await test_factory.inhibitor.check_impulse(ctx)
    
    await asyncio.sleep(0.1)

    assert len(received_events) == 0
