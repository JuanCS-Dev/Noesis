"""
NOESIS Memory Fortress - Memory Client
=======================================

Bulletproof memory client with 4-tier architecture.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from metacognitive_reflector.models.reflection import MemoryUpdate
from ..resilience import (
    CircuitBreakerConfig,
    CircuitOpenError,
    L1HotCache,
    MemoryCircuitBreaker,
    VaultBackup,
    WriteAheadLog,
)
from .models import MemoryEntry, MemoryType, SearchResult
from .backends import HTTPBackendMixin, RedisBackendMixin

if TYPE_CHECKING:
    from metacognitive_reflector.config import MemorySettings, RedisSettings

logger = logging.getLogger(__name__)


class MemoryClient(RedisBackendMixin, HTTPBackendMixin):
    """
    Memory Fortress Client - Bulletproof Memory Storage.

    4-Tier Architecture:
    - L1 (Hot Cache): In-memory LRU, <1ms access
    - L2 (Warm Storage): Redis with AOF, <10ms access
    - L3 (Cold Storage): Qdrant via episodic-memory service, <50ms access
    - L4 (Vault): JSON backup with checksums, disaster recovery
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        redis_url: Optional[str] = None,
        timeout_seconds: float = 5.0,
        use_fallback: bool = True,
        cache_max_size: int = 1000,
        cache_ttl_seconds: int = 300,
        wal_enabled: bool = True,
        wal_path: str = "data/wal",
        vault_path: str = "data/vault",
    ) -> None:
        """
        Initialize memory client with all tiers.

        Args:
            base_url: Memory service URL (L3 tier)
            redis_url: Redis URL (L2 tier)
            timeout_seconds: HTTP timeout
            use_fallback: Use in-memory when services unavailable
            cache_max_size: L1 cache max entries
            cache_ttl_seconds: L1 cache TTL
            wal_enabled: Enable write-ahead logging
            wal_path: WAL directory
            vault_path: Vault backup directory
        """
        self._base_url = base_url
        self._redis_url = redis_url
        self._timeout = timeout_seconds
        self._use_fallback = use_fallback
        self._http_client: Optional[Any] = None
        self._redis_client: Optional[Any] = None

        self._l1_cache = L1HotCache(max_size=cache_max_size, ttl_seconds=cache_ttl_seconds)
        self._wal: Optional[WriteAheadLog] = WriteAheadLog(wal_path) if wal_enabled else None
        self._vault = VaultBackup(vault_path)

        self._circuit_l2 = MemoryCircuitBreaker(
            name="redis", config=CircuitBreakerConfig(failure_threshold=3, reset_timeout=15.0)
        )
        self._circuit_l3 = MemoryCircuitBreaker(
            name="http", config=CircuitBreakerConfig(failure_threshold=5, reset_timeout=30.0)
        )

        self._fallback_storage: Dict[str, MemoryEntry] = {}
        self._memory_counter = 0

    @classmethod
    def from_settings(
        cls,
        memory_settings: "MemorySettings",
        redis_settings: Optional["RedisSettings"] = None,
    ) -> "MemoryClient":
        """Create client from settings."""
        return cls(
            base_url=memory_settings.service_url,
            redis_url=redis_settings.url if redis_settings else None,
            timeout_seconds=memory_settings.timeout_seconds,
            use_fallback=memory_settings.fallback_enabled,
            cache_max_size=memory_settings.cache_max_size,
            cache_ttl_seconds=memory_settings.cache_ttl_seconds,
            wal_enabled=memory_settings.wal_enabled,
            wal_path=memory_settings.wal_path,
            vault_path=memory_settings.local_backup_path,
        )

    async def store(
        self,
        content: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        context: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """Store a new memory with write-through to all tiers."""
        self._memory_counter += 1
        memory_id = f"mem_{self._memory_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        entry = MemoryEntry(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            context=context or {},
            timestamp=datetime.now(),
        )

        wal_seq: Optional[int] = None
        if self._wal:
            wal_seq = await self._wal.append("store", {
                "memory_id": entry.memory_id, "content": entry.content,
                "type": entry.memory_type.value, "importance": entry.importance,
                "context": entry.context, "timestamp": entry.timestamp.isoformat(),
            })

        tiers_written: List[str] = []

        await self._l1_cache.set(entry.memory_id, entry.__dict__)
        tiers_written.append("L1")

        try:
            await self._circuit_l2.protected(lambda: self._store_redis(entry), fallback=None)
            tiers_written.append("L2")
        except (CircuitOpenError, Exception):
            pass

        if self._base_url:
            try:
                await self._circuit_l3.protected(
                    lambda: self._store_http(content, memory_type, importance, context),
                    fallback=None,
                )
                tiers_written.append("L3")
            except (CircuitOpenError, Exception):
                pass

        if not tiers_written or self._use_fallback:
            self._fallback_storage[memory_id] = entry

        if self._wal and wal_seq:
            await self._wal.mark_applied(wal_seq)

        return entry

    async def search(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> SearchResult:
        """Search memories with read-through."""
        start_time = datetime.now()

        if self._base_url:
            try:
                result = await self._circuit_l3.protected(
                    lambda: self._search_http(query, memory_types, limit, min_importance),
                    fallback=None,
                )
                if result:
                    result.query_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                    return result
            except (CircuitOpenError, Exception):
                pass

        result = await self._search_fallback(query, memory_types, limit, min_importance)
        result.query_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        return result

    async def _search_fallback(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]],
        limit: int,
        min_importance: float,
    ) -> SearchResult:
        """Search in fallback memory."""
        query_lower = query.lower()
        query_terms = query_lower.split()

        results = []
        for entry in self._fallback_storage.values():
            if memory_types and entry.memory_type not in memory_types:
                continue
            if entry.importance < min_importance:
                continue
            content_lower = entry.content.lower()
            if any(term in content_lower for term in query_terms):
                results.append(entry)

        results.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)

        return SearchResult(memories=results[:limit], total_found=len(results))

    async def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a specific memory by ID with read-through."""
        cached = await self._l1_cache.get(memory_id)
        if cached:
            return MemoryEntry(
                memory_id=cached["memory_id"],
                content=cached["content"],
                memory_type=MemoryType(cached["memory_type"]) if isinstance(cached["memory_type"], str) else cached["memory_type"],
                importance=cached["importance"],
                context=cached["context"],
                timestamp=cached["timestamp"] if isinstance(cached["timestamp"], datetime) else datetime.fromisoformat(cached["timestamp"]),
            )

        try:
            entry = await self._circuit_l2.protected(lambda: self._get_redis(memory_id), fallback=None)
            if entry:
                await self._l1_cache.set(entry.memory_id, entry.__dict__)
                return entry
        except (CircuitOpenError, Exception):
            pass

        if self._base_url:
            try:
                entry = await self._circuit_l3.protected(lambda: self._get_http(memory_id), fallback=None)
                if entry:
                    await self._l1_cache.set(entry.memory_id, entry.__dict__)
                    return entry
            except (CircuitOpenError, Exception):
                pass

        return self._fallback_storage.get(memory_id)

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory from all tiers."""
        wal_seq: Optional[int] = None
        if self._wal:
            wal_seq = await self._wal.append("delete", {"memory_id": memory_id})

        deleted_from: List[str] = []

        if await self._l1_cache.delete(memory_id):
            deleted_from.append("L1")

        try:
            await self._circuit_l2.protected(lambda: self._delete_redis(memory_id), fallback=None)
            deleted_from.append("L2")
        except (CircuitOpenError, Exception):
            pass

        if self._base_url:
            try:
                await self._circuit_l3.protected(lambda: self._delete_http(memory_id), fallback=None)
                deleted_from.append("L3")
            except (CircuitOpenError, Exception):
                pass

        if memory_id in self._fallback_storage:
            del self._fallback_storage[memory_id]
            deleted_from.append("L4")

        if self._wal and wal_seq:
            await self._wal.mark_applied(wal_seq)

        return len(deleted_from) > 0

    async def apply_updates(self, updates: List[MemoryUpdate]) -> Dict[str, Any]:
        """Apply memory updates from reflection."""
        results = []
        for update in updates:
            memory_type = self._map_update_type(update.update_type.value)
            entry = await self.store(
                content=update.content,
                memory_type=memory_type,
                importance=update.confidence,
                context={"source": "reflection", "original_type": update.update_type.value},
            )
            results.append({"memory_id": entry.memory_id, "status": "stored"})

        return {"status": "success", "updates_applied": len(results), "results": results}

    def _map_update_type(self, update_type: str) -> MemoryType:
        """Map MemoryUpdateType to MemoryType."""
        mapping = {
            "NEW_KNOWLEDGE": MemoryType.SEMANTIC,
            "CORRECTION": MemoryType.SEMANTIC,
            "PATTERN": MemoryType.PROCEDURAL,
            "REFLECTION": MemoryType.REFLECTION,
        }
        return mapping.get(update_type, MemoryType.EPISODIC)

    async def store_reflection(
        self,
        agent_id: str,
        reflection_type: str,
        content: str,
        verdict_data: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """Store a reflection memory."""
        return await self.store(
            content=content,
            memory_type=MemoryType.REFLECTION,
            importance=0.7,
            context={
                "agent_id": agent_id,
                "reflection_type": reflection_type,
                "verdict_data": verdict_data or {},
            },
        )

    async def get_agent_history(self, agent_id: str, limit: int = 20) -> List[MemoryEntry]:
        """Get memory history for an agent."""
        result = await self.search(query=agent_id, limit=limit)
        return [m for m in result.memories if m.context.get("agent_id") == agent_id]

    async def backup_to_vault(self) -> Dict[str, Any]:
        """Create a vault backup of all memories."""
        entries = [
            {
                "memory_id": e.memory_id, "content": e.content, "type": e.memory_type.value,
                "importance": e.importance, "context": e.context, "timestamp": e.timestamp.isoformat(),
            }
            for e in self._fallback_storage.values()
        ]

        if not entries:
            return {"status": "skipped", "reason": "no_entries"}

        checksum = await self._vault.backup(entries)
        return {
            "status": "success", "file": checksum.file_path,
            "entry_count": checksum.entry_count, "checksum": checksum.checksum,
        }

    async def restore_from_vault(self) -> Dict[str, Any]:
        """Restore memories from vault backup."""
        try:
            entries = await self._vault.restore(verify_checksum=True)
            restored = 0

            for e in entries:
                entry = MemoryEntry(
                    memory_id=e["memory_id"], content=e["content"],
                    memory_type=MemoryType(e["type"]), importance=e.get("importance", 0.5),
                    context=e.get("context", {}),
                    timestamp=datetime.fromisoformat(e.get("timestamp", datetime.now().isoformat())),
                )
                self._fallback_storage[entry.memory_id] = entry
                await self._l1_cache.set(entry.memory_id, entry.__dict__)
                restored += 1

            return {"status": "success", "restored_count": restored}
        except ValueError as e:
            return {"status": "error", "error": str(e)}

    async def replay_wal(self) -> Dict[str, Any]:
        """Replay unapplied WAL entries for crash recovery."""
        if not self._wal:
            return {"status": "skipped", "reason": "wal_disabled"}

        entries = await self._wal.get_unapplied_entries()
        replayed = 0
        errors = 0

        for entry in entries:
            try:
                if entry.operation == "store":
                    data = entry.data
                    await self.store(
                        content=data["content"], memory_type=MemoryType(data["type"]),
                        importance=data.get("importance", 0.5), context=data.get("context", {}),
                    )
                    replayed += 1
                elif entry.operation == "delete":
                    await self.delete(entry.data["memory_id"])
                    replayed += 1

                await self._wal.mark_applied(entry.sequence_id)
            except Exception as e:
                logger.error(f"WAL replay error for entry {entry.sequence_id}: {e}")
                errors += 1

        return {"status": "success", "replayed": replayed, "errors": errors, "total_entries": len(entries)}

    async def health_check(self) -> Dict[str, Any]:
        """Check memory client health across all tiers."""
        health: Dict[str, Any] = {"healthy": True, "tiers": {}}

        health["tiers"]["l1_cache"] = {"healthy": True, **self._l1_cache.get_status()}

        l2_healthy = False
        if self._redis_url:
            try:
                client = await self._get_redis_client()
                if client:
                    await asyncio.wait_for(client.ping(), timeout=2.0)
                    l2_healthy = True
            except Exception:
                pass

        health["tiers"]["l2_redis"] = {
            "healthy": l2_healthy, "url": self._redis_url, "circuit": self._circuit_l2.get_status()
        }

        l3_healthy = False
        if self._base_url:
            try:
                client = await self._get_http_client()
                if client:
                    response = await asyncio.wait_for(client.get("/health"), timeout=2.0)
                    l3_healthy = response.status_code == 200
            except Exception:
                pass

        health["tiers"]["l3_http"] = {
            "healthy": l3_healthy, "url": self._base_url, "circuit": self._circuit_l3.get_status()
        }

        health["tiers"]["l4_vault"] = {"healthy": True, **self._vault.get_status()}

        if self._wal:
            health["wal"] = self._wal.get_status()

        health["fallback_entries"] = len(self._fallback_storage)
        health["healthy"] = health["tiers"]["l1_cache"]["healthy"] and health["tiers"]["l4_vault"]["healthy"]

        return health

    async def close(self) -> None:
        """Close all connections."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None

