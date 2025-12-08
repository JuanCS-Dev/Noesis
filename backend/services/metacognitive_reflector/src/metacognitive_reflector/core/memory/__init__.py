"""
NOESIS Memory Fortress - Memory Package
========================================

Bulletproof memory client with 4-tier architecture.

Components:
- MemoryClient: Main client class (4-tier persistent storage)
- MemoryEntry, MemoryType: Data models
- SessionMemory: Conversation context management
- Backend operations: Redis, HTTP
"""

from __future__ import annotations

from .client import MemoryClient
from .models import MemoryEntry, MemoryType, SearchResult
from .session import SessionMemory, Turn, create_session, get_or_create_session

__all__ = [
    # Core client
    "MemoryClient",
    # Models
    "MemoryEntry",
    "MemoryType",
    "SearchResult",
    # Session memory
    "SessionMemory",
    "Turn",
    "create_session",
    "get_or_create_session",
]

