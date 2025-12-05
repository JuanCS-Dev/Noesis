"""
Tests for Memory Decay (Ebbinghaus Curve)
=========================================

Scientific tests for decay_importance functionality.

Follows CODE_CONSTITUTION: ≥85% coverage, clear test names.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import pytest

from core.memory_store import MemoryStore
from models.memory import Memory, MemoryType


@pytest.fixture
def store() -> MemoryStore:
    """Create fresh store for each test."""
    return MemoryStore()


class TestDecayImportance:
    """Test Ebbinghaus forgetting curve implementation."""

    @pytest.mark.asyncio
    async def test_decay_reduces_importance_over_time(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: Importance decreases exponentially with time."""
        # Arrange
        memory: Memory = await store.store("Old memory", MemoryType.EPISODIC)
        memory.importance = 1.0
        memory.timestamp = datetime.utcnow() - timedelta(hours=24)

        # Act
        await store.decay_importance(decay_factor=0.995)

        # Assert
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        expected: float = 1.0 * (0.995 ** 24)  # ~0.886
        assert abs(retrieved.importance - expected) < 0.01

    @pytest.mark.asyncio
    async def test_decay_boosts_recently_accessed(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: Recently accessed memories get importance boost."""
        # Arrange
        memory: Memory = await store.store("Accessed memory", MemoryType.EPISODIC)
        memory.importance = 0.5
        memory.timestamp = datetime.utcnow() - timedelta(hours=48)
        memory.last_accessed = datetime.utcnow() - timedelta(hours=1)

        # Act
        result: Dict[str, Any] = await store.decay_importance(boost_recent_access=True)

        # Assert
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        assert result["boosted"] >= 1
        # Decayed but boosted should be higher than just decayed
        just_decayed: float = 0.5 * (0.995 ** 48)
        assert retrieved.importance > just_decayed

    @pytest.mark.asyncio
    async def test_decay_deletes_below_threshold(self, store: MemoryStore) -> None:
        """HYPOTHESIS: Memories below delete_threshold are removed."""
        # Arrange
        memory: Memory = await store.store("Fading memory", MemoryType.EPISODIC)
        memory.importance = 0.01  # Very low
        memory.timestamp = datetime.utcnow() - timedelta(hours=100)

        # Act
        result: Dict[str, Any] = await store.decay_importance(delete_threshold=0.05)

        # Assert
        assert result["deleted"] >= 1
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_decay_skips_vault_memories(self, store: MemoryStore) -> None:
        """HYPOTHESIS: VAULT memories do not decay."""
        # Arrange
        memory: Memory = await store.store("Vault memory", MemoryType.VAULT)
        original_importance: float = 0.9
        memory.importance = original_importance
        memory.timestamp = datetime.utcnow() - timedelta(days=30)

        # Act
        await store.decay_importance()

        # Assert
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        assert retrieved.importance == original_importance

    @pytest.mark.asyncio
    async def test_decay_skips_core_memories(self, store: MemoryStore) -> None:
        """HYPOTHESIS: CORE memories do not decay."""
        # Arrange
        memory: Memory = await store.store("Core identity", MemoryType.CORE)
        original_importance: float = 1.0
        memory.importance = original_importance
        memory.timestamp = datetime.utcnow() - timedelta(days=365)

        # Act
        await store.decay_importance()

        # Assert
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        assert retrieved.importance == original_importance

    @pytest.mark.asyncio
    async def test_decay_returns_correct_stats(self, store: MemoryStore) -> None:
        """HYPOTHESIS: Decay returns accurate statistics."""
        # Arrange
        for i in range(5):
            memory: Memory = await store.store(f"Memory {i}", MemoryType.EPISODIC)
            memory.importance = 0.5
            memory.timestamp = datetime.utcnow() - timedelta(hours=i * 10)

        # Act
        result: Dict[str, Any] = await store.decay_importance()

        # Assert
        assert result["decayed"] == 5
        assert "boosted" in result
        assert "deleted" in result

    @pytest.mark.asyncio
    async def test_decay_with_custom_factor(self, store: MemoryStore) -> None:
        """HYPOTHESIS: Custom decay factor affects decay rate."""
        # Arrange
        memory: Memory = await store.store("Test memory", MemoryType.SEMANTIC)
        memory.importance = 1.0
        memory.timestamp = datetime.utcnow() - timedelta(hours=24)

        # Act - aggressive decay
        await store.decay_importance(decay_factor=0.9)

        # Assert
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        expected: float = 1.0 * (0.9 ** 24)  # Much lower than 0.995
        assert abs(retrieved.importance - expected) < 0.01
        assert retrieved.importance < 0.1  # Very decayed

    @pytest.mark.asyncio
    async def test_decay_boost_proportional_to_recency(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: Boost is proportional to how recently memory was accessed."""
        # Arrange
        recent: Memory = await store.store("Very recent", MemoryType.EPISODIC)
        recent.importance = 0.5
        recent.timestamp = datetime.utcnow() - timedelta(hours=48)
        recent.last_accessed = datetime.utcnow() - timedelta(hours=1)

        older: Memory = await store.store("Less recent", MemoryType.EPISODIC)
        older.importance = 0.5
        older.timestamp = datetime.utcnow() - timedelta(hours=48)
        older.last_accessed = datetime.utcnow() - timedelta(hours=20)

        # Act
        await store.decay_importance(boost_recent_access=True)

        # Assert
        recent_retrieved: Optional[Memory] = await store.get_memory(recent.memory_id)
        older_retrieved: Optional[Memory] = await store.get_memory(older.memory_id)
        assert recent_retrieved is not None
        assert older_retrieved is not None
        # More recent access = higher boost
        assert recent_retrieved.importance > older_retrieved.importance

    @pytest.mark.asyncio
    async def test_decay_no_boost_when_disabled(self, store: MemoryStore) -> None:
        """HYPOTHESIS: No boost applied when boost_recent_access=False."""
        # Arrange
        memory: Memory = await store.store("Accessed memory", MemoryType.EPISODIC)
        memory.importance = 0.5
        memory.timestamp = datetime.utcnow() - timedelta(hours=24)
        memory.last_accessed = datetime.utcnow() - timedelta(hours=1)

        # Act
        result: Dict[str, Any] = await store.decay_importance(boost_recent_access=False)

        # Assert
        assert result["boosted"] == 0
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        expected: float = 0.5 * (0.995 ** 24)  # Pure decay, no boost
        assert abs(retrieved.importance - expected) < 0.01

