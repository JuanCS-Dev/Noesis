"""
Tests for Memory Consolidation
==============================

Scientific tests for consolidate_to_vault functionality.

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


class TestConsolidateToVault:
    """Test memory consolidation to vault."""

    @pytest.mark.asyncio
    async def test_consolidate_moves_high_importance_to_vault(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: Memories with importance >= threshold move to vault."""
        # Arrange
        memory: Memory = await store.store("Important memory", MemoryType.EPISODIC)
        memory.importance = 0.9
        memory.timestamp = datetime.utcnow() - timedelta(days=10)
        memory.access_count = 3

        # Act
        result: Dict[str, int] = await store.consolidate_to_vault(
            threshold=0.8, min_age_days=7
        )

        # Assert
        assert result.get("episodic", 0) == 1
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        assert retrieved.type == MemoryType.VAULT

    @pytest.mark.asyncio
    async def test_consolidate_preserves_original_type(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: Original type is preserved in context metadata."""
        # Arrange
        memory: Memory = await store.store("Semantic memory", MemoryType.SEMANTIC)
        memory.importance = 0.95
        memory.timestamp = datetime.utcnow() - timedelta(days=14)
        memory.access_count = 5

        # Act
        await store.consolidate_to_vault(threshold=0.8, min_age_days=7)

        # Assert
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        assert retrieved.context["original_type"] == "semantic"
        assert "consolidated_at" in retrieved.context

    @pytest.mark.asyncio
    async def test_consolidate_skips_low_importance(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: Low importance memories are NOT consolidated."""
        # Arrange
        memory: Memory = await store.store("Low importance", MemoryType.EPISODIC)
        memory.importance = 0.5  # Below threshold
        memory.timestamp = datetime.utcnow() - timedelta(days=10)
        memory.access_count = 3

        # Act
        result: Dict[str, int] = await store.consolidate_to_vault(
            threshold=0.8, min_age_days=7
        )

        # Assert
        assert result.get("episodic", 0) == 0
        retrieved: Optional[Memory] = await store.get_memory(memory.memory_id)
        assert retrieved is not None
        assert retrieved.type == MemoryType.EPISODIC

    @pytest.mark.asyncio
    async def test_consolidate_skips_recent_memories(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: Recent memories are NOT consolidated."""
        # Arrange
        memory: Memory = await store.store("Recent memory", MemoryType.EPISODIC)
        memory.importance = 0.9
        memory.timestamp = datetime.utcnow() - timedelta(days=1)  # Too recent
        memory.access_count = 3

        # Act
        result: Dict[str, int] = await store.consolidate_to_vault(
            threshold=0.8, min_age_days=7
        )

        # Assert
        assert result.get("episodic", 0) == 0

    @pytest.mark.asyncio
    async def test_consolidate_skips_vault_and_core(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: VAULT and CORE types are never consolidated."""
        # Arrange
        vault_mem: Memory = await store.store("Vault memory", MemoryType.VAULT)
        vault_mem.importance = 1.0
        vault_mem.timestamp = datetime.utcnow() - timedelta(days=30)
        vault_mem.access_count = 10

        core_mem: Memory = await store.store("Core memory", MemoryType.CORE)
        core_mem.importance = 1.0
        core_mem.timestamp = datetime.utcnow() - timedelta(days=30)
        core_mem.access_count = 10

        # Act
        result: Dict[str, int] = await store.consolidate_to_vault(
            threshold=0.5, min_age_days=1
        )

        # Assert
        assert result == {}  # Nothing consolidated

    @pytest.mark.asyncio
    async def test_consolidate_requires_minimum_access(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: Memories need minimum access_count to consolidate."""
        # Arrange
        memory: Memory = await store.store("Rarely accessed", MemoryType.EPISODIC)
        memory.importance = 0.9
        memory.timestamp = datetime.utcnow() - timedelta(days=10)
        memory.access_count = 1  # Below min_access_count=2

        # Act
        result: Dict[str, int] = await store.consolidate_to_vault(
            threshold=0.8, min_age_days=7, min_access_count=2
        )

        # Assert
        assert result.get("episodic", 0) == 0

    @pytest.mark.asyncio
    async def test_consolidate_multiple_types(self, store: MemoryStore) -> None:
        """HYPOTHESIS: Can consolidate from multiple types in one call."""
        # Arrange
        for mem_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            memory: Memory = await store.store(f"{mem_type.value} memory", mem_type)
            memory.importance = 0.9
            memory.timestamp = datetime.utcnow() - timedelta(days=10)
            memory.access_count = 3

        # Act
        result: Dict[str, int] = await store.consolidate_to_vault(
            threshold=0.8, min_age_days=7
        )

        # Assert
        assert result.get("episodic", 0) == 1
        assert result.get("semantic", 0) == 1
        assert result.get("procedural", 0) == 1

    @pytest.mark.asyncio
    async def test_consolidate_returns_empty_when_no_matches(
        self, store: MemoryStore
    ) -> None:
        """HYPOTHESIS: Returns empty dict when no memories match criteria."""
        # Arrange
        memory: Memory = await store.store("Memory", MemoryType.EPISODIC)
        memory.importance = 0.3  # Low importance

        # Act
        result: Dict[str, int] = await store.consolidate_to_vault(threshold=0.8)

        # Assert
        assert result == {}
