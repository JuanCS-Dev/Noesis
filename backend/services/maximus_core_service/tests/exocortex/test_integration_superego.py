"""
Integration Test: The Superego Loop
===================================
Verifies the chain: Impulse -> Guardian Audit -> Violation -> Confrontation.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime # pylint: disable=unused-import

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
    # Initializes factory with mocked Gemini and real components wired up
    factory = ExocortexFactory(data_dir="/tmp/exocortex_test_superego")
    factory.gemini_client = mock_gemini

    # Re-initialize components to use the mock client and wired workspace
    # Note: Factory __init__ already does this, but we need to ensure
    # the injected gemini_client is used.
    # In the current implementation of Factory, it creates a real GeminiClient.
    # We must patch it or rebuild the components using the mock.

    # Better approach: Manually wire up the components using the mock for precise control
    # reusing the logic from Factory manually or patching.
    # Let's trust Factory structure but swap the client attribute on the instances.
    factory.guardian.gemini_client = mock_gemini
    factory.confrontation_engine.gemini_client = mock_gemini

    return factory

@pytest.mark.asyncio
async def test_superego_loop(test_factory, mock_gemini): # pylint: disable=redefined-outer-name
    """
    Testa o Ciclo do Superego:
    1. Evento de Impulso chega.
    2. Guardião audita e acha violação.
    3. Evento de Violação é publicado.
    4. Motor de Confronto reage e gera pergunta.
    """

    # Configurar Mocks para a sequência de chamadas
    # Call 1: Guardian Audit (Violation detected)
    # Call 2: Confrontation Generation (Question)
    mock_gemini.generate_text.side_effect = [
        {
            "text": '{"is_violation": true, "severity": "HIGH", '
                    '"violated_rule_ids": ["ETHICS_1"], "reasoning": "Unethical"}'
        },
        # Response 2: Confrontation
        {
            "text": "Why is this unethical?"
        }
    ]

    workspace = test_factory.workspace

    # 1. Trigger Impulse Event (simulating Inhibitor)
    impulse_event = ConsciousEvent(
        id="impulse_1",
        type=EventType.IMPULSE_DETECTED,
        source="Inhibitor",
        payload={
            "impulse_type": "Purchase",
            "action": "Buy expensive item",
            "level": "NOTICE" # Not Blocked, just noticed
        }
    )

    # Start the chain
    await workspace.broadcast(impulse_event)

    # Give time for async tasks to propagate
    # Chain: Broadcast(Impulse) -> Guardian.handle -> Broadcast(Violation) -> Confrontation.handle
    await asyncio.sleep(0.1)

    # Verify Gemini Interaction
    # Expect 2 calls
    assert mock_gemini.generate_text.call_count >= 2

    # Check Call 1: Input to Guardian
    # We can check specific prompt args if needed, but call_count proves flow reached Guardian.

    # Check Call 2: Input to Confrontation
    # Flow reached Confrontation?

    # Verify internal state logs or subsequent events?
    # The best proof is that generate_text was called the second time.

    # Additional verification: Check if Confrontation logs were produced?
    # Or strict order validation.
