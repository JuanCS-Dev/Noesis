"""
Unit Tests for Global Workspace
"""

import pytest
import asyncio
from datetime import datetime
from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    GlobalWorkspace, ConsciousEvent, EventType
)

@pytest.fixture
def workspace():
    """Fixture para o Global Workspace."""
    return GlobalWorkspace()

@pytest.mark.asyncio
async def test_subscription_and_broadcast(workspace):
    """Testa se um assinante recebe evento."""
    received = []

    async def listener(event: ConsciousEvent):
        received.append(event)

    workspace.subscribe(EventType.STIMULUS_FILTERED, listener)

    event = ConsciousEvent(
        id="test_1",
        type=EventType.STIMULUS_FILTERED,
        source="Test",
        payload={"data": 123}
    )

    await workspace.broadcast(event)

    assert len(received) == 1
    assert received[0].id == "test_1"
    assert received[0].payload["data"] == 123

@pytest.mark.asyncio
async def test_multiple_subscribers(workspace):
    """Testa múltiplos assinantes para o mesmo evento."""
    counter = {"a": 0, "b": 0}

    async def listener_a(event):
        counter["a"] += 1

    async def listener_b(event):
        counter["b"] += 1

    workspace.subscribe(EventType.IMPULSE_DETECTED, listener_a)
    workspace.subscribe(EventType.IMPULSE_DETECTED, listener_b)

    event = ConsciousEvent(
        id="test_multi",
        type=EventType.IMPULSE_DETECTED,
        source="Test",
        payload={}
    )

    await workspace.broadcast(event)

    assert counter["a"] == 1
    assert counter["b"] == 1

@pytest.mark.asyncio
async def test_no_subscribers_safe(workspace):
    """Testa broadcast sem assinantes (não deve falhar)."""
    event = ConsciousEvent(
        id="test_ghost",
        type=EventType.CONFRONTATION_STARTED,
        source="Test",
        payload={}
    )
    # Não deve lançar exceção
    await workspace.broadcast(event)
    assert True

@pytest.mark.asyncio
async def test_broken_subscriber_resiliance(workspace):
    """Testa se o bus sobrevive a um listener com erro."""
    
    async def broken_listener(event):
        raise ValueError("Boom!")

    received = []
    async def working_listener(event):
        received.append(event)

    workspace.subscribe(EventType.CONSTITUTION_VIOLATION, broken_listener)
    workspace.subscribe(EventType.CONSTITUTION_VIOLATION, working_listener)

    event = ConsciousEvent(
        id="test_error",
        type=EventType.CONSTITUTION_VIOLATION,
        source="Test",
        payload={}
    )

    # Deve capturar a exceção e continuar
    await workspace.broadcast(event)

    # O listener funcionando deve ter recebido
    assert len(received) == 1
    assert received[0].id == "test_error"
