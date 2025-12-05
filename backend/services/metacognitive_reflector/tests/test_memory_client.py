"""
MAXIMUS 2.0 - Tests for Memory Client
======================================

Tests for memory client with fallback storage.
"""

from __future__ import annotations


import pytest

from metacognitive_reflector.core.memory_client import MemoryClient
from metacognitive_reflector.core.memory_models import MemoryEntry, MemoryType, SearchResult


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def memory_client():
    """Create a memory client with fallback only."""
    return MemoryClient(base_url=None, use_fallback=True)


# ============================================================================
# MemoryType Tests
# ============================================================================

class TestMemoryType:
    """Tests for MemoryType enum."""

    def test_memory_types_exist(self):
        """Test all memory types are defined."""
        assert MemoryType.SEMANTIC == "semantic"
        assert MemoryType.EPISODIC == "episodic"
        assert MemoryType.PROCEDURAL == "procedural"
        assert MemoryType.REFLECTION == "reflection"


# ============================================================================
# MemoryEntry Tests
# ============================================================================

class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_create_entry(self):
        """Test creating a memory entry."""
        entry = MemoryEntry(
            memory_id="test-001",
            content="Test memory content",
            memory_type=MemoryType.SEMANTIC,
        )

        assert entry.memory_id == "test-001"
        assert entry.content == "Test memory content"
        assert entry.memory_type == MemoryType.SEMANTIC
        assert entry.importance == 0.5  # default
        assert entry.context == {}  # default
        assert entry.embedding is None  # default


# ============================================================================
# SearchResult Tests
# ============================================================================

class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_create_result(self):
        """Test creating a search result."""
        result = SearchResult(
            memories=[],
            total_found=0,
        )

        assert result.memories == []
        assert result.total_found == 0
        assert result.query_time_ms == 0.0  # default


# ============================================================================
# MemoryClient Tests - Storage
# ============================================================================

class TestMemoryClientStorage:
    """Tests for MemoryClient storage operations."""

    @pytest.mark.asyncio
    async def test_store_memory(self, memory_client):
        """Test storing a memory."""
        entry = await memory_client.store(
            content="Agent learned to plan tasks",
            memory_type=MemoryType.SEMANTIC,
            importance=0.8,
        )

        assert entry.memory_id is not None
        assert entry.content == "Agent learned to plan tasks"
        assert entry.memory_type == MemoryType.SEMANTIC
        assert entry.importance == 0.8

    @pytest.mark.asyncio
    async def test_store_with_context(self, memory_client):
        """Test storing memory with context."""
        entry = await memory_client.store(
            content="Completed deployment",
            memory_type=MemoryType.EPISODIC,
            context={"agent_id": "executor-001", "task_id": "task-123"},
        )

        assert entry.context["agent_id"] == "executor-001"
        assert entry.context["task_id"] == "task-123"

    @pytest.mark.asyncio
    async def test_get_memory(self, memory_client):
        """Test retrieving a memory by ID."""
        # Store first
        stored = await memory_client.store(
            content="Test retrieval",
            memory_type=MemoryType.PROCEDURAL,
        )

        # Retrieve
        retrieved = await memory_client.get(stored.memory_id)

        assert retrieved is not None
        assert retrieved.memory_id == stored.memory_id
        assert retrieved.content == "Test retrieval"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, memory_client):
        """Test retrieving nonexistent memory."""
        result = await memory_client.get("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_client):
        """Test deleting a memory."""
        # Store first
        stored = await memory_client.store(
            content="To be deleted",
            memory_type=MemoryType.REFLECTION,
        )

        # Delete
        deleted = await memory_client.delete(stored.memory_id)
        assert deleted is True

        # Verify gone
        retrieved = await memory_client.get(stored.memory_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, memory_client):
        """Test deleting nonexistent memory."""
        result = await memory_client.delete("nonexistent-id")
        assert result is False


# ============================================================================
# MemoryClient Tests - Search
# ============================================================================

class TestMemoryClientSearch:
    """Tests for MemoryClient search operations."""

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, memory_client):
        """Test searching by keyword."""
        # Store test memories
        await memory_client.store(
            content="Agent learned Python programming",
            memory_type=MemoryType.SEMANTIC,
        )
        await memory_client.store(
            content="Agent executed deployment task",
            memory_type=MemoryType.EPISODIC,
        )

        # Search
        result = await memory_client.search("Python")

        assert result.total_found >= 1
        assert any("Python" in m.content for m in result.memories)

    @pytest.mark.asyncio
    async def test_search_by_type(self, memory_client):
        """Test filtering search by memory type."""
        # Store different types
        await memory_client.store(
            content="Semantic knowledge",
            memory_type=MemoryType.SEMANTIC,
        )
        await memory_client.store(
            content="Episodic knowledge",
            memory_type=MemoryType.EPISODIC,
        )

        # Search semantic only
        result = await memory_client.search(
            query="knowledge",
            memory_types=[MemoryType.SEMANTIC],
        )

        assert all(m.memory_type == MemoryType.SEMANTIC for m in result.memories)

    @pytest.mark.asyncio
    async def test_search_with_importance(self, memory_client):
        """Test filtering by importance."""
        # Store with different importance
        await memory_client.store(
            content="Low importance memory",
            memory_type=MemoryType.SEMANTIC,
            importance=0.2,
        )
        await memory_client.store(
            content="High importance memory",
            memory_type=MemoryType.SEMANTIC,
            importance=0.9,
        )

        # Search with min importance
        result = await memory_client.search(
            query="memory",
            min_importance=0.5,
        )

        assert all(m.importance >= 0.5 for m in result.memories)

    @pytest.mark.asyncio
    async def test_search_with_limit(self, memory_client):
        """Test search result limit."""
        # Store multiple
        for i in range(5):
            await memory_client.store(
                content=f"Test memory {i}",
                memory_type=MemoryType.EPISODIC,
            )

        # Search with limit
        result = await memory_client.search(
            query="memory",
            limit=2,
        )

        assert len(result.memories) <= 2

    @pytest.mark.asyncio
    async def test_search_empty_result(self, memory_client):
        """Test search with no matches."""
        result = await memory_client.search("xyznonexistent123")

        assert result.total_found == 0
        assert result.memories == []


# ============================================================================
# MemoryClient Tests - Reflection Storage
# ============================================================================

class TestMemoryClientReflection:
    """Tests for reflection-specific operations."""

    @pytest.mark.asyncio
    async def test_store_reflection(self, memory_client):
        """Test storing a reflection memory."""
        entry = await memory_client.store_reflection(
            agent_id="planner-001",
            reflection_type="tribunal_verdict",
            content="Agent passed truth check with high confidence",
            verdict_data={"score": 0.95, "passed": True},
        )

        assert entry.memory_type == MemoryType.REFLECTION
        assert entry.context["agent_id"] == "planner-001"
        assert entry.context["reflection_type"] == "tribunal_verdict"
        assert entry.context["verdict_data"]["score"] == 0.95

    @pytest.mark.asyncio
    async def test_get_agent_history(self, memory_client):
        """Test getting agent history."""
        # Store memories for different agents (include agent_id in content for search)
        await memory_client.store_reflection(
            agent_id="planner-001",
            reflection_type="action",
            content="planner-001 Planned task A",
        )
        await memory_client.store_reflection(
            agent_id="executor-001",
            reflection_type="action",
            content="executor-001 Executed task A",
        )
        await memory_client.store_reflection(
            agent_id="planner-001",
            reflection_type="action",
            content="planner-001 Planned task B",
        )

        # Get planner history
        history = await memory_client.get_agent_history("planner-001")

        assert len(history) == 2
        assert all(m.context.get("agent_id") == "planner-001" for m in history)


# ============================================================================
# MemoryClient Tests - Health Check
# ============================================================================

class TestMemoryClientHealth:
    """Tests for health check."""

    @pytest.mark.asyncio
    async def test_health_check_fallback_only(self, memory_client):
        """Test health check with fallback only."""
        health = await memory_client.health_check()

        assert health["healthy"] is True
        assert health["http_available"] is False
        assert health["fallback_enabled"] is True
        assert health["base_url"] is None

    @pytest.mark.asyncio
    async def test_health_check_with_entries(self, memory_client):
        """Test health check shows entry count."""
        # Store some entries
        await memory_client.store("Test 1", MemoryType.SEMANTIC)
        await memory_client.store("Test 2", MemoryType.SEMANTIC)

        health = await memory_client.health_check()

        assert health["fallback_entries"] == 2


# ============================================================================
# MemoryClient Tests - Close
# ============================================================================

class TestMemoryClientClose:
    """Tests for client cleanup."""

    @pytest.mark.asyncio
    async def test_close(self, memory_client):
        """Test closing the client."""
        await memory_client.close()
        # Should not raise
        assert True
