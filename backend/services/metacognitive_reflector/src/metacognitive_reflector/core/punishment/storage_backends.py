"""
NOESIS Memory Fortress - Penal Registry Storage Backends
=========================================================

Storage backend implementations for punishment persistence.
Part of the Memory Fortress 4-tier architecture.

Contains:
- StorageBackend: Abstract base class
- InMemoryBackend: For testing/development
- RedisBackend: Production storage (L2)
- JSONBackend: Disaster recovery (L4 Vault)
"""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

if TYPE_CHECKING:
    from .models import PenalRecord

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """
    Abstract storage backend for penal records.

    Implementations must provide:
    - get: Retrieve a record by agent_id
    - set: Store a record
    - delete: Remove a record
    - list_active: List all active punishments
    - health_check: Check backend health
    """

    @abstractmethod
    async def get(self, agent_id: str) -> Optional["PenalRecord"]:
        """
        Get penal record for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            PenalRecord if found, None otherwise
        """

    @abstractmethod
    async def set(self, record: "PenalRecord") -> bool:
        """
        Store penal record.

        Args:
            record: Record to store

        Returns:
            True if stored successfully
        """

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """
        Delete penal record.

        Args:
            agent_id: Agent identifier

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    async def list_active(self) -> List["PenalRecord"]:
        """
        List all active punishments.

        Returns:
            List of active PenalRecord instances
        """

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check backend health.

        Returns:
            Health status dictionary
        """


class InMemoryBackend(StorageBackend):
    """
    In-memory storage backend for testing/development.

    Not persistent across restarts. Use for:
    - Unit tests
    - Development
    - Fallback when Redis unavailable
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        # pylint: disable=import-outside-toplevel
        from .models import PenalRecord
        self._record_class = PenalRecord
        self._records: Dict[str, "PenalRecord"] = {}

    async def get(self, agent_id: str) -> Optional["PenalRecord"]:
        """Get penal record, auto-clearing expired."""
        record = self._records.get(agent_id)
        if record and not record.is_active:
            # Auto-clear expired records
            del self._records[agent_id]
            return None
        return record

    async def set(self, record: "PenalRecord") -> bool:
        """Store penal record."""
        self._records[record.agent_id] = record
        return True

    async def delete(self, agent_id: str) -> bool:
        """Delete penal record."""
        if agent_id in self._records:
            del self._records[agent_id]
            return True
        return False

    async def list_active(self) -> List["PenalRecord"]:
        """List all active punishments."""
        return [r for r in self._records.values() if r.is_active]

    async def health_check(self) -> Dict[str, Any]:
        """Check backend health."""
        return {
            "healthy": True,
            "backend": "in_memory",
            "record_count": len(self._records),
        }


class RedisBackend(StorageBackend):
    """
    Redis storage backend for production use.

    Features:
    - TTL-based expiration
    - Index for listing active punishments
    - Connection pooling via aioredis

    Requires:
        pip install redis
    """

    KEY_PREFIX = "maximus:penal:"
    INDEX_KEY = "maximus:penal:index"

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 86400 * 7,  # 7 days
    ) -> None:
        """
        Initialize Redis backend.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (7 days)
        """
        # pylint: disable=import-outside-toplevel
        from .models import PenalRecord
        self._record_class = PenalRecord
        self._redis_url = redis_url
        self._default_ttl = default_ttl
        self._client: Optional[Any] = None

    async def _get_client(self) -> Any:
        """Lazy initialize Redis client."""
        if self._client is None:
            if not HAS_REDIS:
                raise ImportError(
                    "redis package required. Install with: pip install redis"
                )
            self._client = await aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    def _key(self, agent_id: str) -> str:
        """Generate Redis key for agent."""
        return f"{self.KEY_PREFIX}{agent_id}"

    async def get(self, agent_id: str) -> Optional["PenalRecord"]:
        """Get penal record from Redis."""
        client = await self._get_client()
        data = await client.get(self._key(agent_id))
        if not data:
            return None

        record = self._record_class.from_dict(json.loads(data))
        if not record.is_active:
            await self.delete(agent_id)
            return None
        return record

    async def set(self, record: "PenalRecord") -> bool:
        """Store penal record in Redis with TTL."""
        client = await self._get_client()
        key = self._key(record.agent_id)
        data = json.dumps(record.to_dict())

        # Calculate TTL
        if record.until:
            ttl = int((record.until - datetime.now()).total_seconds())
            ttl = max(60, ttl)  # Minimum 60 seconds
        else:
            ttl = self._default_ttl

        # Store record with TTL
        await client.setex(key, ttl, data)

        # Add to index
        await client.sadd(self.INDEX_KEY, record.agent_id)

        return True

    async def delete(self, agent_id: str) -> bool:
        """Delete penal record from Redis."""
        client = await self._get_client()
        await client.delete(self._key(agent_id))
        await client.srem(self.INDEX_KEY, agent_id)
        return True

    async def list_active(self) -> List["PenalRecord"]:
        """List all active punishments from Redis."""
        client = await self._get_client()
        agent_ids = await client.smembers(self.INDEX_KEY)

        records = []
        for agent_id in agent_ids:
            record = await self.get(agent_id)
            if record:
                records.append(record)

        return records

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            client = await self._get_client()
            await client.ping()
            return {
                "healthy": True,
                "backend": "redis",
                "url": self._redis_url,
            }
        except (ConnectionError, TimeoutError, OSError) as e:
            return {
                "healthy": False,
                "backend": "redis",
                "error": str(e),
            }


class JSONBackend(StorageBackend):
    """
    JSON file storage backend for disaster recovery (L4 Vault).

    Features:
    - SHA-256 checksums for data integrity
    - Atomic writes (write to temp, then rename)
    - Human-readable JSON format
    - Backup rotation

    Note: Slower than Redis but survives complete infrastructure failure.
    Use as backup tier, not primary.
    """

    def __init__(
        self,
        file_path: str = "data/penal_registry.json",
        backup_count: int = 3,
    ) -> None:
        """
        Initialize JSON backend.

        Args:
            file_path: Path to JSON file
            backup_count: Number of backup copies to keep
        """
        # pylint: disable=import-outside-toplevel
        from .models import PenalRecord
        self._record_class = PenalRecord
        self._file_path = Path(file_path)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._backup_count = backup_count
        self._cache: Dict[str, "PenalRecord"] = {}
        self._loaded = False

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum for integrity verification."""
        # Exclude checksum field from calculation
        data_copy = {k: v for k, v in data.items() if k != "_checksum"}
        json_str = json.dumps(data_copy, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _load(self) -> Dict[str, Any]:
        """Load data from JSON file with integrity check."""
        if not self._file_path.exists():
            return {"records": {}, "_version": "1.0"}

        try:
            with open(self._file_path, "r") as f:
                data = json.load(f)

            # Verify checksum if present
            stored_checksum = data.get("_checksum")
            if stored_checksum:
                calculated = self._calculate_checksum(data)
                if calculated != stored_checksum:
                    logger.error(
                        f"JSON backend checksum mismatch! "
                        f"Expected {stored_checksum}, got {calculated}"
                    )
                    # Try to recover from backup
                    return self._recover_from_backup()

            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load JSON backend: {e}")
            return self._recover_from_backup()

    def _recover_from_backup(self) -> Dict[str, Any]:
        """Attempt recovery from backup files."""
        for i in range(1, self._backup_count + 1):
            backup_path = self._file_path.with_suffix(f".json.bak{i}")
            if backup_path.exists():
                try:
                    with open(backup_path, "r") as f:
                        data = json.load(f)
                    logger.info(f"Recovered from backup: {backup_path}")
                    return data
                except (json.JSONDecodeError, IOError):
                    continue

        logger.warning("No valid backup found, starting fresh")
        return {"records": {}, "_version": "1.0"}

    def _save(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file with checksum and atomic write."""
        # Rotate backups
        self._rotate_backups()

        # Add checksum
        data["_checksum"] = self._calculate_checksum(data)
        data["_updated_at"] = datetime.now().isoformat()

        # Atomic write: write to temp file, then rename
        temp_path = self._file_path.with_suffix(".json.tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)

        # Rename (atomic on most systems)
        temp_path.rename(self._file_path)

    def _rotate_backups(self) -> None:
        """Rotate backup files."""
        if not self._file_path.exists():
            return

        # Shift existing backups
        for i in range(self._backup_count - 1, 0, -1):
            src = self._file_path.with_suffix(f".json.bak{i}")
            dst = self._file_path.with_suffix(f".json.bak{i + 1}")
            if src.exists():
                src.rename(dst)

        # Create new backup from current file
        backup_path = self._file_path.with_suffix(".json.bak1")
        import shutil
        shutil.copy2(self._file_path, backup_path)

    def _ensure_loaded(self) -> None:
        """Ensure data is loaded from disk."""
        if not self._loaded:
            data = self._load()
            for agent_id, record_data in data.get("records", {}).items():
                self._cache[agent_id] = self._record_class.from_dict(record_data)
            self._loaded = True

    async def get(self, agent_id: str) -> Optional["PenalRecord"]:
        """Get penal record from JSON file."""
        self._ensure_loaded()
        record = self._cache.get(agent_id)
        if record and not record.is_active:
            # Auto-clear expired records
            del self._cache[agent_id]
            self._persist()
            return None
        return record

    async def set(self, record: "PenalRecord") -> bool:
        """Store penal record to JSON file."""
        self._ensure_loaded()
        self._cache[record.agent_id] = record
        self._persist()
        return True

    async def delete(self, agent_id: str) -> bool:
        """Delete penal record from JSON file."""
        self._ensure_loaded()
        if agent_id in self._cache:
            del self._cache[agent_id]
            self._persist()
            return True
        return False

    async def list_active(self) -> List["PenalRecord"]:
        """List all active punishments from JSON file."""
        self._ensure_loaded()
        return [r for r in self._cache.values() if r.is_active]

    def _persist(self) -> None:
        """Persist cache to disk."""
        data = {
            "records": {
                agent_id: record.to_dict()
                for agent_id, record in self._cache.items()
            },
            "_version": "1.0",
        }
        self._save(data)

    async def health_check(self) -> Dict[str, Any]:
        """Check JSON backend health."""
        try:
            self._ensure_loaded()
            return {
                "healthy": True,
                "backend": "json",
                "file_path": str(self._file_path),
                "record_count": len(self._cache),
                "file_exists": self._file_path.exists(),
            }
        except Exception as e:
            return {
                "healthy": False,
                "backend": "json",
                "error": str(e),
            }
