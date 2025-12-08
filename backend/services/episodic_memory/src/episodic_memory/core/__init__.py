"""
Episodic Memory - Core Module.

Core business logic for memory storage and retrieval.

Components:
- MemoryStore: MIRIX-compatible storage with entity extraction
- ContextBuilder: Multi-type context with associative retrieval
- EntityIndex: Inverted index for connecting memories
- EntityExtractor: Regex-based entity extraction
"""

from __future__ import annotations

from .memory_store import MemoryStore
from .context_builder import ContextBuilder, MemoryContext
from .entity_index import (
    EntityExtractor,
    EntityIndex,
    EntityMatch,
    get_entity_extractor,
    get_entity_index,
    extract_and_index,
)

__all__ = [
    # Memory storage
    "MemoryStore",
    # Context building
    "ContextBuilder",
    "MemoryContext",
    # Entity system
    "EntityExtractor",
    "EntityIndex",
    "EntityMatch",
    "get_entity_extractor",
    "get_entity_index",
    "extract_and_index",
]
