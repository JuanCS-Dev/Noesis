"""
Unit tests for Episodic Memory Store.

Follows CODE_CONSTITUTION: 100% type hints, Google style.
"""

from __future__ import annotations

from typing import Optional

import pytest

from core.memory_store import MemoryStore
from models.memory import Memory, MemoryType, MemoryQuery, MemorySearchResult


@pytest.mark.asyncio
async def test_store_and_retrieve() -> None:
    """Test storing and retrieving a memory."""
    store: MemoryStore = MemoryStore()
    
    # Store memory
    memory: Memory = await store.store(
        content="Test memory content",
        memory_type=MemoryType.FACT,
        context={"source": "test"}
    )

    assert memory.memory_id is not None
    assert memory.content == "Test memory content"
    assert memory.type == MemoryType.FACT

    # Retrieve memory
    query: MemoryQuery = MemoryQuery(query_text="test memory")
    results: MemorySearchResult = await store.retrieve(query)

    assert results.total_found == 1
    assert results.memories[0].memory_id == memory.memory_id


@pytest.mark.asyncio
async def test_retrieve_filters() -> None:
    """Test retrieving memories with filters."""
    store: MemoryStore = MemoryStore()

    await store.store("Memory 1", MemoryType.FACT)
    await store.store("Memory 2", MemoryType.EXPERIENCE)

    # Filter by type
    query: MemoryQuery = MemoryQuery(query_text="memory", type=MemoryType.FACT)
    results: MemorySearchResult = await store.retrieve(query)

    assert results.total_found == 1
    assert results.memories[0].content == "Memory 1"


@pytest.mark.asyncio
async def test_delete() -> None:
    """Test deleting a memory."""
    store: MemoryStore = MemoryStore()
    memory: Memory = await store.store("To delete", MemoryType.FACT)

    # Verify exists
    retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
    assert retrieved is not None

    # Delete
    success: bool = await store.delete(memory.memory_id)
    assert success is True

    # Verify deleted
    retrieved = await store.get_memory(memory.memory_id)
    assert retrieved is None

    # Delete non-existent
    success = await store.delete("fake_id")
    assert success is False
