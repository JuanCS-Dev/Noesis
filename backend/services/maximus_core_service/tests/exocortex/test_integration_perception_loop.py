"""
Integration Test: Perception Feedback Loop
==========================================
Verifies the cycle: User Feedback -> Self Update -> Workspace Notification.
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
import pytest

from services.maximus_core_service.src.consciousness.exocortex.factory import ExocortexFactory
from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    ConsciousEvent, EventType
)

@pytest.fixture
def mock_gemini():
    """Mock do cliente Gemini."""
    mock = MagicMock()
    mock.generate_text = AsyncMock()
    return mock

@pytest.fixture
def test_factory(mock_gemini): # pylint: disable=redefined-outer-name
    """Factory configurada para teste."""
    factory = ExocortexFactory(data_dir="/tmp/exocortex_test_perception")
    factory.gemini_client = mock_gemini

    # Re-inject mocks into components
    factory.symbiotic_self.gemini_client = mock_gemini

    return factory

@pytest.mark.asyncio
async def test_feedback_loop(test_factory, mock_gemini): # pylint: disable=redefined-outer-name
    """
    Testa o Ciclo de Percepção:
    1. Evento FEEDBACK_RECEIVED é publicado.
    2. SymbioticSelf reage e chama Gemini.
    3. SymbioticSelf publica SELF_UPDATED.
    """

    # 1. Setup Mock Response for Perception Update
    mock_perception = {
        "perceived_emotional_state": "Relieved",
        "perceived_energy_level": 0.7,
        "perceived_alignment": 0.9,
        "perceived_stress_level": 0.2,
        "confidence_in_perception": 0.9
    }
    mock_gemini.generate_text.return_value = {"text": json.dumps(mock_perception)}

    workspace = test_factory.workspace

    # 2. Trigger Event (User Feedback)
    feedback_event = ConsciousEvent(
        id="fb_loop_1",
        type=EventType.FEEDBACK_RECEIVED,
        source="Frontend",
        payload={
            "text": "Thanks for the confrontation, I realized my mistake.",
            "original_confrontation_id": "conf_123"
        }
    )

    # Create a subscriber to catch the result event
    result_future = asyncio.Future()

    async def catch_result(event):
        if event.type == EventType.SELF_UPDATED:
            result_future.set_result(event)

    workspace.subscribe(EventType.SELF_UPDATED, catch_result)

    # 3. Start Loop
    await workspace.broadcast(feedback_event)

    # 4. Wait for Result (with timeout safety)
    try:
        updated_event = await asyncio.wait_for(result_future, timeout=1.0)
    except asyncio.TimeoutError:
        pytest.fail("Timeout waiting for SELF_UPDATED event")

    # 5. Verify
    assert updated_event.type == EventType.SELF_UPDATED
    assert updated_event.payload["new_perception"]["perceived_emotional_state"] == "Relieved"

    # Verify Gemini was called
    mock_gemini.generate_text.assert_called_once()
    args = mock_gemini.generate_text.call_args
    assert "Thanks for the confrontation" in args.kwargs["prompt"]
