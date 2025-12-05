"""
Edge Case Tests for Global Workspace
====================================
"""
import pytest
import asyncio
from unittest.mock import AsyncMock

from services.maximus_core_service.src.consciousness.exocortex.global_workspace import (
    GlobalWorkspace, ConsciousEvent, EventType
)

@pytest.fixture
def workspace():
    return GlobalWorkspace()

@pytest.mark.asyncio
async def test_broadcast_without_listeners(workspace):
    """Testa broadcast seguro sem nenhum subscriber."""
    event = ConsciousEvent(id="1", type=EventType.STIMULUS_FILTERED, source="test", payload={})
    # Should not raise exception
    await workspace.broadcast(event)
    assert True

@pytest.mark.asyncio
async def test_subscribe_same_listener_multiple_events(workspace):
    """Testa mesmo listener em múltiplos eventos."""
    mock_listener = AsyncMock()
    
    workspace.subscribe(EventType.STIMULUS_FILTERED, mock_listener)
    workspace.subscribe(EventType.IMPULSE_DETECTED, mock_listener)
    
    event1 = ConsciousEvent(id="1", type=EventType.STIMULUS_FILTERED, source="test", payload={})
    event2 = ConsciousEvent(id="2", type=EventType.IMPULSE_DETECTED, source="test", payload={})
    
    await workspace.broadcast(event1)
    await workspace.broadcast(event2)
    
    assert mock_listener.call_count == 2

@pytest.mark.asyncio
async def test_broadcast_empty_payload(workspace):
    """Testa evento com payload vazio."""
    mock_listener = AsyncMock()
    workspace.subscribe(EventType.IMPULSE_DETECTED, mock_listener)
    
    event = ConsciousEvent(id="1", type=EventType.IMPULSE_DETECTED, source="test", payload={})
    await workspace.broadcast(event)
    
    call_args = mock_listener.call_args[0][0]
    assert call_args.payload == {}

@pytest.mark.asyncio
async def test_history_cap(workspace):
    """Testa se o histórico é limitado (assumindo limite padrão 100)."""
    # Fill history > 100
    for i in range(110):
        event = ConsciousEvent(id=str(i), type=EventType.STIMULUS_FILTERED, source="test", payload={})
        await workspace.broadcast(event)
        
    assert len(workspace._history) <= 100
    # Verifica se os mais antigos foram removidos (id 0 deve ter saido)
    ids = [e.id for e in workspace._history]
    assert "0" not in ids
    assert "109" in ids
