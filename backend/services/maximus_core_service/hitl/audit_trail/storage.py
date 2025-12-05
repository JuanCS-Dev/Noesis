"""
Storage Backend Interface for Audit Trail.

Provides abstract interface for audit log storage backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base_pkg import AuditEntry


class StorageBackend(ABC):
    """
    Abstract storage backend for audit logs.

    Implementations can provide database, S3, or other persistence.
    """

    @abstractmethod
    def store(self, entry: AuditEntry) -> None:
        """
        Store audit entry.

        Args:
            entry: Audit entry to store

        Raises:
            StorageError: If storage fails
        """
        pass

    @abstractmethod
    def query(self, filters: dict) -> list[AuditEntry]:
        """
        Query stored audit entries.

        Args:
            filters: Query filters

        Returns:
            Matching audit entries

        Raises:
            StorageError: If query fails
        """
        pass


class InMemoryStorage(StorageBackend):
    """
    In-memory storage backend for testing.

    Not suitable for production - entries lost on restart.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._entries: list[AuditEntry] = []

    def store(self, entry: AuditEntry) -> None:
        """Store entry in memory."""
        self._entries.append(entry)

    def query(self, filters: dict) -> list[AuditEntry]:
        """Query entries in memory."""
        # Simple implementation - can be extended
        return self._entries.copy()


class StorageError(Exception):
    """Exception raised for storage backend errors."""

    pass
