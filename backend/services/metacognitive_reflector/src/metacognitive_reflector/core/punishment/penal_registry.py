"""
NOESIS Memory Fortress - Penal Registry (Punishment Persistence)
=================================================================

Persists punishment state with bulletproof redundancy.

Storage Strategy: Write-Through to ALL available backends
Read Strategy: Read from fastest available backend

Based on:
- Write-Ahead Logging patterns
- Multi-tier persistence
- Audit logging best practices
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from .models import OffenseType, PenalRecord, PenalStatus, WriteStrategy
from .storage_backends import InMemoryBackend, JSONBackend, RedisBackend, StorageBackend

if TYPE_CHECKING:
    from metacognitive_reflector.config import RedisSettings

logger = logging.getLogger(__name__)


class PenalRegistry:
    """
    Central registry for agent punishment state with bulletproof persistence.

    Features:
    - Multi-backend write-through (Redis + JSON + InMemory)
    - Automatic fallback chain on read
    - Automatic expiration of punishments
    - Audit logging with persistence
    - Circuit breaker per backend

    Storage Tiers:
    - L2 (Redis): Fast primary storage with TTL
    - L4 (JSON): Vault backup with checksums
    - Fallback (InMemory): Always available

    Usage:
        registry = PenalRegistry.create_with_settings(settings)

        # Check agent status on startup
        record = await registry.get_status("planner-001")
        if record and record.status == PenalStatus.QUARANTINE:
            apply_quarantine_restrictions()

        # Record new punishment
        await registry.punish(
            agent_id="executor-002",
            offense=OffenseType.ROLE_VIOLATION,
            status=PenalStatus.QUARANTINE,
            duration=timedelta(hours=24),
        )
    """

    def __init__(
        self,
        backends: Optional[List[Tuple[str, StorageBackend]]] = None,
        write_strategy: WriteStrategy = WriteStrategy.WRITE_THROUGH,
        enable_audit_log: bool = True,
        audit_log_path: Optional[str] = None,
    ) -> None:
        """
        Initialize registry with multiple backends.

        Args:
            backends: List of (name, backend) tuples in priority order
            write_strategy: How to write to backends
            enable_audit_log: Enable audit logging
            audit_log_path: Path for persistent audit log (optional)
        """
        if backends:
            self._backends = backends
        else:
            self._backends = [("memory", InMemoryBackend())]

        self._write_strategy = write_strategy
        self._enable_audit = enable_audit_log
        self._audit_log: List[Dict[str, Any]] = []
        self._audit_log_path = audit_log_path
        self._primary = self._backends[0][1] if self._backends else InMemoryBackend()
        self._fallback = self._backends[-1][1] if len(self._backends) > 1 else self._primary

    @classmethod
    def create_with_settings(
        cls,
        redis_settings: Optional["RedisSettings"] = None,
        backup_path: str = "data/penal_registry.json",
        audit_log_path: Optional[str] = None,
    ) -> "PenalRegistry":
        """
        Factory method to create registry with proper backend chain.

        Args:
            redis_settings: Redis configuration (optional)
            backup_path: Path for JSON backup
            audit_log_path: Path for audit log

        Returns:
            Configured PenalRegistry
        """
        backends: List[Tuple[str, StorageBackend]] = []

        if redis_settings and redis_settings.url:
            try:
                redis_backend = RedisBackend(
                    redis_url=redis_settings.url,
                    default_ttl=redis_settings.default_ttl_seconds,
                )
                backends.append(("redis", redis_backend))
                logger.info(f"Redis backend configured: {redis_settings.url}")
            except Exception as e:
                logger.warning(f"Redis backend unavailable: {e}")

        json_backend = JSONBackend(file_path=backup_path)
        backends.append(("json", json_backend))
        logger.info(f"JSON backend configured: {backup_path}")

        backends.append(("memory", InMemoryBackend()))

        return cls(
            backends=backends,
            write_strategy=WriteStrategy.WRITE_THROUGH,
            enable_audit_log=True,
            audit_log_path=audit_log_path,
        )

    async def get_status(self, agent_id: str) -> Optional[PenalRecord]:
        """
        Get current punishment status for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            PenalRecord if found, None otherwise
        """
        for name, backend in self._backends:
            try:
                record = await backend.get(agent_id)
                if record:
                    logger.debug(f"Found record for {agent_id} in {name} backend")
                    return record
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.debug(f"Backend {name} failed for get: {e}")
                continue

        return None

    async def punish(  # pylint: disable=too-many-positional-arguments,too-many-arguments
        self,
        agent_id: str,
        offense: OffenseType,
        status: PenalStatus,
        offense_details: str = "",
        duration: Optional[timedelta] = None,
        re_education_required: bool = False,
        judge_verdicts: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PenalRecord:
        """
        Record a punishment for an agent.

        Args:
            agent_id: Agent to punish
            offense: Type of offense
            status: Punishment level
            offense_details: Description of offense
            duration: How long (None = indefinite)
            re_education_required: Needs re-education before return
            judge_verdicts: References to judge verdicts
            metadata: Additional context

        Returns:
            Created PenalRecord
        """
        existing = await self.get_status(agent_id)

        if existing and existing.is_active:
            offense_count = existing.offense_count + 1
            if offense_count >= 3:
                status = PenalStatus.SUSPENDED
            elif offense_count >= 2 and status == PenalStatus.WARNING:
                status = PenalStatus.PROBATION
        else:
            offense_count = 1

        until = None
        if duration:
            until = datetime.now() + duration

        record = PenalRecord(
            agent_id=agent_id,
            status=status,
            offense=offense,
            offense_details=offense_details,
            since=datetime.now(),
            until=until,
            re_education_required=re_education_required,
            offense_count=offense_count,
            judge_verdicts=judge_verdicts or [],
            metadata=metadata or {},
        )

        backends_written = await self._write_to_backends(record)

        if self._enable_audit:
            audit_entry = {
                "action": "punish",
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "status": status.value,
                "offense": offense.value,
                "duration": str(duration) if duration else "indefinite",
                "backends_written": backends_written,
            }
            self._audit_log.append(audit_entry)
            self._persist_audit_entry(audit_entry)

        logger.info(
            f"Punishment recorded: {agent_id} -> {status.value} "
            f"(backends: {backends_written})"
        )
        return record

    async def _write_to_backends(self, record: PenalRecord) -> List[str]:
        """Write record to all backends based on strategy."""
        backends_written: List[str] = []
        for name, backend in self._backends:
            try:
                await backend.set(record)
                backends_written.append(name)
                if self._write_strategy == WriteStrategy.WRITE_PRIMARY:
                    break
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.warning(f"Backend {name} failed for write: {e}")
                continue

        if not backends_written:
            logger.error(f"All backends failed for write: {record.agent_id}")

        return backends_written

    async def pardon(
        self,
        agent_id: str,
        reason: str = "Punishment completed",
    ) -> bool:
        """
        Clear punishment for an agent.

        Args:
            agent_id: Agent to pardon
            reason: Reason for pardon

        Returns:
            True if record existed and was cleared
        """
        record = await self.get_status(agent_id)
        if not record:
            return False

        backends_deleted: List[str] = []
        for name, backend in self._backends:
            try:
                await backend.delete(agent_id)
                backends_deleted.append(name)
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.warning(f"Backend {name} failed for pardon delete: {e}")
                continue

        if self._enable_audit:
            audit_entry = {
                "action": "pardon",
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "reason": reason,
                "previous_status": record.status.value,
                "backends_deleted": backends_deleted,
            }
            self._audit_log.append(audit_entry)
            self._persist_audit_entry(audit_entry)

        logger.info(f"Agent pardoned: {agent_id} (reason: {reason})")
        return True

    async def complete_re_education(self, agent_id: str) -> bool:
        """
        Mark re-education as completed.

        Args:
            agent_id: Agent identifier

        Returns:
            True if record found and updated
        """
        record = await self.get_status(agent_id)
        if not record:
            return False

        record.re_education_completed = True

        if record.status == PenalStatus.QUARANTINE and record.re_education_completed:
            record.status = PenalStatus.PROBATION

        for name, backend in self._backends:
            try:
                await backend.set(record)
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.warning(f"Backend {name} failed for re-education update: {e}")
                continue

        if self._enable_audit:
            audit_entry = {
                "action": "re_education_completed",
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "new_status": record.status.value,
            }
            self._audit_log.append(audit_entry)
            self._persist_audit_entry(audit_entry)

        return True

    async def list_active_punishments(self) -> List[PenalRecord]:
        """List all agents with active punishments."""
        for name, backend in self._backends:
            try:
                records = await backend.list_active()
                logger.debug(f"Listed {len(records)} active punishments from {name}")
                return records
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.debug(f"Backend {name} failed for list_active: {e}")
                continue
        return []

    async def check_restrictions(
        self,
        agent_id: str,
        action: str,
    ) -> Dict[str, Any]:
        """
        Check if agent is allowed to perform action.

        Args:
            agent_id: Agent identifier
            action: Action to check

        Returns:
            Restriction info dictionary
        """
        record = await self.get_status(agent_id)

        if not record or not record.is_active:
            return {"allowed": True}

        restrictions = {
            PenalStatus.WARNING: {
                "allowed": True,
                "warning": "Agent has warning on record",
            },
            PenalStatus.PROBATION: {
                "allowed": True,
                "monitoring": True,
                "warning": "Agent is on probation - all actions monitored",
            },
            PenalStatus.QUARANTINE: {
                "allowed": action in ["re_education", "health_check"],
                "reason": "Agent is quarantined",
                "allowed_actions": ["re_education", "health_check"],
            },
            PenalStatus.SUSPENDED: {
                "allowed": False,
                "reason": "Agent is suspended",
            },
            PenalStatus.DELETED: {
                "allowed": False,
                "reason": "Agent is marked for deletion",
            },
        }

        return restrictions.get(record.status, {"allowed": True})

    def get_audit_log(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries.

        Args:
            agent_id: Filter by agent (None = all)
            limit: Maximum entries to return

        Returns:
            List of audit log entries
        """
        log = self._audit_log
        if agent_id:
            log = [e for e in log if e.get("agent_id") == agent_id]
        return log[-limit:]

    async def health_check(self) -> Dict[str, Any]:
        """Check registry health."""
        backends_health: Dict[str, Any] = {}
        any_healthy = False

        for name, backend in self._backends:
            health = await backend.health_check()
            backends_health[name] = health
            if health.get("healthy"):
                any_healthy = True

        return {
            "healthy": any_healthy,
            "backends": backends_health,
            "write_strategy": self._write_strategy.value,
            "audit_log_size": len(self._audit_log),
        }

    def _persist_audit_entry(self, entry: Dict[str, Any]) -> None:
        """Persist audit entry to file if configured."""
        if not self._audit_log_path:
            return

        try:
            import json
            from pathlib import Path

            path = Path(self._audit_log_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            logger.warning(f"Failed to persist audit entry: {e}")


async def check_agent_punishment(
    registry: PenalRegistry,
    agent_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Check agent punishment status on startup.

    Args:
        registry: PenalRegistry instance
        agent_id: Agent identifier

    Returns:
        Restrictions dict if punished, None if clear
    """
    record = await registry.get_status(agent_id)

    if not record or not record.is_active:
        return None

    return {
        "status": record.status.value,
        "offense": record.offense.value,
        "since": record.since.isoformat(),
        "until": record.until.isoformat() if record.until else None,
        "re_education_required": record.re_education_required,
        "re_education_completed": record.re_education_completed,
    }
