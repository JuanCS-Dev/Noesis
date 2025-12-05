"""
Integration Test for Event Flow
===============================
Verifies that events flow correctly from components (Thalamus) to the Global Workspace.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from services.maximus_core_service.src.consciousness.exocortex.digital_thalamus import (
    Stimulus, StimulusType, AttentionStatus
)
from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    EventType, ConsciousEvent
)

@pytest.mark.asyncio
async def test_thalamus_publishes_event(test_factory, mock_gemini):
    """
    Testa se o DigitalThalamus publica um evento no GlobalWorkspace
    após processar um estímulo.
    """
    # 1. Setup: Mockar Gemini para retornar uma decisão
    mock_gemini.generate_text.return_value = {
        "text": '{"urgency": 0.8, "dopamine": 0.2, "relevance": 0.9}'
    }

    # 2. Setup: Inscrever um listener de teste no Workspace
    received_events = []
    
    async def test_listener(event: ConsciousEvent):
        received_events.append(event)
    
    test_factory.workspace.subscribe(EventType.STIMULUS_FILTERED, test_listener)

    # 3. Action: Ingestar um estímulo no Tálamo
    stimulus = Stimulus(
        id="test_integ_event",
        type=StimulusType.MESSAGE,
        source="integration_test",
        content="Hello World"
    )
    
    await test_factory.thalamus.ingest(stimulus, AttentionStatus.FOCUS)

    # Allow async loop to process broadcast
    await asyncio.sleep(0.1)

    # 4. Assertion: Verificar se o evento chegou
    assert len(received_events) == 1
    event = received_events[0]
    
    assert event.type == EventType.STIMULUS_FILTERED
    assert event.source == "DigitalThalamus"
    assert event.payload["stimulus_id"] == "test_integ_event"
    # Verificar se a decisão foi propagada (Allow/Block/Batch)
    assert "decision" in event.payload
