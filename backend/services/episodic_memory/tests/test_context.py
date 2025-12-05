"""
Tests for Context Builder
==========================

Scientific tests for ContextBuilder and MemoryContext.

Follows CODE_CONSTITUTION: ≥85% coverage, clear test names.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest

from core.memory_store import MemoryStore
from core.context_builder import ContextBuilder, MemoryContext
from models.memory import Memory, MemoryType


@pytest.fixture
def store() -> MemoryStore:
    """Create fresh store for each test."""
    return MemoryStore()


@pytest.fixture
def builder(store: MemoryStore) -> ContextBuilder:
    """Create context builder with store."""
    return ContextBuilder(store)


class TestContextBuilder:
    """Test context building functionality."""

    @pytest.mark.asyncio
    async def test_get_context_returns_all_types(
        self, store: MemoryStore, builder: ContextBuilder
    ) -> None:
        """HYPOTHESIS: Context includes memories from all 6 MIRIX types."""
        # Arrange - use "memory" keyword in all content for matching
        await store.store("Core identity memory", MemoryType.CORE)
        await store.store("Past event memory", MemoryType.EPISODIC)
        await store.store("Knowledge fact memory", MemoryType.SEMANTIC)
        await store.store("Workflow skill memory", MemoryType.PROCEDURAL)
        await store.store("External doc memory", MemoryType.RESOURCE)
        await store.store("Important vault memory", MemoryType.VAULT)

        # Act - search with matching keyword
        context: MemoryContext = await builder.get_context_for_task("memory")

        # Assert
        assert context.total_memories() == 6
        assert len(context.core) == 1
        assert len(context.episodic) == 1
        assert len(context.semantic) == 1
        assert len(context.procedural) == 1
        assert len(context.resource) == 1
        assert len(context.vault) == 1

    @pytest.mark.asyncio
    async def test_context_filters_by_keyword(
        self, store: MemoryStore, builder: ContextBuilder
    ) -> None:
        """HYPOTHESIS: Context only includes memories matching keywords."""
        # Arrange
        await store.store("Python programming skills", MemoryType.PROCEDURAL)
        await store.store("Java development", MemoryType.PROCEDURAL)
        await store.store("Python testing patterns", MemoryType.SEMANTIC)

        # Act
        context: MemoryContext = await builder.get_context_for_task("python programming")

        # Assert
        # Should match Python memories, not Java
        assert context.total_memories() >= 2
        contents: List[str] = [m.content for m in context.procedural + context.semantic]
        assert any("Python" in c for c in contents)

    @pytest.mark.asyncio
    async def test_context_respects_top_k(
        self, store: MemoryStore, builder: ContextBuilder
    ) -> None:
        """HYPOTHESIS: Context respects top-K limit per type."""
        # Arrange
        for i in range(20):
            memory: Memory = await store.store(f"Test memory {i}", MemoryType.EPISODIC)
            memory.importance = 0.5 + (i / 40)  # Varying importance

        # Act
        context: MemoryContext = await builder.get_context_for_task("test memory")

        # Assert - default top-K for episodic is 10
        assert len(context.episodic) <= 10

    @pytest.mark.asyncio
    async def test_context_includes_retrieval_scores(
        self, store: MemoryStore, builder: ContextBuilder
    ) -> None:
        """HYPOTHESIS: Context includes retrieval score for each memory."""
        # Arrange
        memory: Memory = await store.store("Test content", MemoryType.EPISODIC)

        # Act
        context: MemoryContext = await builder.get_context_for_task("test content")

        # Assert
        assert memory.memory_id in context.retrieval_scores
        score: float = context.retrieval_scores[memory.memory_id]
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_context_records_task(
        self, store: MemoryStore, builder: ContextBuilder
    ) -> None:
        """HYPOTHESIS: Context stores the original task query."""
        # Arrange
        task: str = "write unit tests for authentication"

        # Act
        context: MemoryContext = await builder.get_context_for_task(task)

        # Assert
        assert context.task == task

    @pytest.mark.asyncio
    async def test_context_records_memory_access(
        self, store: MemoryStore, builder: ContextBuilder
    ) -> None:
        """HYPOTHESIS: Retrieving context increments access_count."""
        # Arrange
        memory: Memory = await store.store("Important fact", MemoryType.SEMANTIC)
        initial_count: int = memory.access_count

        # Act
        await builder.get_context_for_task("important fact")

        # Assert
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        assert retrieved.access_count > initial_count

    @pytest.mark.asyncio
    async def test_empty_context_when_no_matches(
        self, store: MemoryStore, builder: ContextBuilder
    ) -> None:
        """HYPOTHESIS: Returns empty context when no memories match."""
        # Arrange
        await store.store("Unrelated content", MemoryType.EPISODIC)

        # Act
        context: MemoryContext = await builder.get_context_for_task("xyz123 nonexistent")

        # Assert
        assert context.total_memories() == 0


class TestMemoryContext:
    """Test MemoryContext dataclass."""

    def test_to_prompt_context_formats_sections(self) -> None:
        """HYPOTHESIS: to_prompt_context creates formatted sections."""
        # Arrange
        context: MemoryContext = MemoryContext(
            core=[Memory(memory_id="1", type=MemoryType.CORE, content="I am helpful")],
            episodic=[Memory(memory_id="2", type=MemoryType.EPISODIC, content="User asked about X")],
            semantic=[Memory(memory_id="3", type=MemoryType.SEMANTIC, content="X is a concept")],
            procedural=[],
            resource=[],
            vault=[],
            retrieval_scores={},
            task="test"
        )

        # Act
        formatted: str = context.to_prompt_context()

        # Assert
        assert "[CORE IDENTITY]" in formatted
        assert "[RECENT EXPERIENCES]" in formatted
        assert "[KNOWLEDGE]" in formatted
        assert "I am helpful" in formatted
        assert "User asked about X" in formatted

    def test_total_memories_counts_all(self) -> None:
        """HYPOTHESIS: total_memories sums all type lists."""
        # Arrange
        context: MemoryContext = MemoryContext(
            core=[Memory(memory_id="1", type=MemoryType.CORE, content="a")],
            episodic=[Memory(memory_id="2", type=MemoryType.EPISODIC, content="b"),
                      Memory(memory_id="3", type=MemoryType.EPISODIC, content="c")],
            semantic=[Memory(memory_id="4", type=MemoryType.SEMANTIC, content="d")],
            procedural=[],
            resource=[Memory(memory_id="5", type=MemoryType.RESOURCE, content="e")],
            vault=[],
            retrieval_scores={},
            task="test"
        )

        # Act & Assert
        assert context.total_memories() == 5

    def test_to_dict_serializes_correctly(self) -> None:
        """HYPOTHESIS: to_dict produces valid dictionary for API."""
        # Arrange
        context: MemoryContext = MemoryContext(
            core=[Memory(memory_id="1", type=MemoryType.CORE, content="identity")],
            episodic=[],
            semantic=[],
            procedural=[],
            resource=[],
            vault=[],
            retrieval_scores={"1": 0.85},
            task="test task"
        )

        # Act
        result: Dict[str, Any] = context.to_dict()

        # Assert
        assert result["task"] == "test task"
        assert result["total_memories"] == 1
        assert len(result["core"]) == 1
        assert result["retrieval_scores"]["1"] == 0.85

    def test_empty_context_to_prompt_returns_empty(self) -> None:
        """HYPOTHESIS: Empty context produces empty prompt string."""
        # Arrange
        context: MemoryContext = MemoryContext(
            core=[],
            episodic=[],
            semantic=[],
            procedural=[],
            resource=[],
            vault=[],
            retrieval_scores={},
            task=""
        )

        # Act
        formatted: str = context.to_prompt_context()

        # Assert
        assert formatted == ""


class TestRetrievalScoring:
    """Test retrieval score computation."""

    @pytest.mark.asyncio
    async def test_higher_importance_higher_score(
        self, store: MemoryStore, builder: ContextBuilder
    ) -> None:
        """HYPOTHESIS: Higher importance leads to higher retrieval score."""
        # Arrange
        high: Memory = await store.store("test content high", MemoryType.EPISODIC)
        high.importance = 0.9

        low: Memory = await store.store("test content low", MemoryType.EPISODIC)
        low.importance = 0.3

        # Act
        context: MemoryContext = await builder.get_context_for_task("test content")

        # Assert
        high_score: float = context.retrieval_scores.get(high.memory_id, 0)
        low_score: float = context.retrieval_scores.get(low.memory_id, 0)
        assert high_score > low_score

    @pytest.mark.asyncio
    async def test_more_recent_higher_score(
        self, store: MemoryStore, builder: ContextBuilder
    ) -> None:
        """HYPOTHESIS: More recent memories have higher retrieval score."""
        # Arrange
        recent: Memory = await store.store("test content recent", MemoryType.EPISODIC)
        recent.timestamp = datetime.utcnow()

        old: Memory = await store.store("test content old", MemoryType.EPISODIC)
        old.timestamp = datetime.utcnow() - timedelta(days=30)

        # Act
        context: MemoryContext = await builder.get_context_for_task("test content")

        # Assert
        recent_score: float = context.retrieval_scores.get(recent.memory_id, 0)
        old_score: float = context.retrieval_scores.get(old.memory_id, 0)
        assert recent_score > old_score

