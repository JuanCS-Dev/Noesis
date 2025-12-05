"""
MAXIMUS 2.0 - Penal Registry (Punishment Persistence)
======================================================

Persists punishment state across K8s pod restarts.

Storage Hierarchy:
1. Redis (Primary): Fast reads, TTL for quarantine
2. MIRIX (Backup): Audit trail, episodic memory
3. K8s ConfigMap (Fallback): Survives Redis restart

Estado Persistido:
{
    "agent_id": "planner-001",
    "status": "QUARANTINE",
    "offense": "role_violation",
    "since": "2025-12-01T10:00:00Z",
    "until": "2025-12-02T10:00:00Z",
    "re_education_required": true
}

Based on:
- Redis persistence patterns
- Audit logging best practices
- K8s ConfigMap as state store
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from .storage_backends import InMemoryBackend, StorageBackend


class PenalStatus(str, Enum):
    """Agent punishment status."""

    CLEAR = "clear"             # No active punishment
    WARNING = "warning"         # Has warning on record
    PROBATION = "probation"     # Under observation
    QUARANTINE = "quarantine"   # Isolated, restricted actions
    SUSPENDED = "suspended"     # Cannot act at all
    DELETED = "deleted"         # Marked for deletion


class OffenseType(str, Enum):
    """Types of offenses."""

    TRUTH_VIOLATION = "truth_violation"
    WISDOM_VIOLATION = "wisdom_violation"
    ROLE_VIOLATION = "role_violation"
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"
    SCOPE_VIOLATION = "scope_violation"
    REPEATED_OFFENSE = "repeated_offense"


@dataclass
class PenalRecord:  # pylint: disable=too-many-instance-attributes
    """
    Record of an agent's punishment status.

    Persisted to Redis/MIRIX for survival across restarts.

    Attributes:
        agent_id: Unique agent identifier
        status: Current punishment status
        offense: Type of offense committed
        offense_details: Description of the offense
        since: When punishment started
        until: When punishment ends (None = indefinite)
        re_education_required: Whether re-education is needed
        re_education_completed: Whether re-education is done
        offense_count: Number of offenses
        judge_verdicts: References to judge verdicts
        metadata: Additional context
    """

    agent_id: str
    status: PenalStatus
    offense: OffenseType
    offense_details: str = ""
    since: datetime = field(default_factory=datetime.now)
    until: Optional[datetime] = None  # None = indefinite
    re_education_required: bool = False
    re_education_completed: bool = False
    offense_count: int = 1
    judge_verdicts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "offense": self.offense.value,
            "offense_details": self.offense_details,
            "since": self.since.isoformat(),
            "until": self.until.isoformat() if self.until else None,
            "re_education_required": self.re_education_required,
            "re_education_completed": self.re_education_completed,
            "offense_count": self.offense_count,
            "judge_verdicts": self.judge_verdicts,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls: type["PenalRecord"], data: Dict[str, Any]) -> "PenalRecord":
        """
        Create from dictionary.

        Args:
            data: Dictionary with record data

        Returns:
            PenalRecord instance
        """
        return cls(
            agent_id=data["agent_id"],
            status=PenalStatus(data["status"]),
            offense=OffenseType(data["offense"]),
            offense_details=data.get("offense_details", ""),
            since=datetime.fromisoformat(data["since"]),
            until=datetime.fromisoformat(data["until"]) if data.get("until") else None,
            re_education_required=data.get("re_education_required", False),
            re_education_completed=data.get("re_education_completed", False),
            offense_count=data.get("offense_count", 1),
            judge_verdicts=data.get("judge_verdicts", []),
            metadata=data.get("metadata", {}),
        )

    @property
    def is_active(self) -> bool:
        """Check if punishment is still active."""
        if self.status == PenalStatus.CLEAR:
            return False
        if self.until and datetime.now() > self.until:
            return False
        return True

    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get remaining punishment time."""
        if not self.until:
            return None
        remaining = self.until - datetime.now()
        return max(timedelta(0), remaining)


class PenalRegistry:
    """
    Central registry for agent punishment state.

    Provides:
    - Multi-backend persistence (Redis primary, in-memory fallback)
    - Automatic expiration of punishments
    - Audit logging
    - Startup hooks for K8s

    Usage:
        registry = PenalRegistry()

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
        primary_backend: Optional[StorageBackend] = None,
        fallback_backend: Optional[StorageBackend] = None,
        enable_audit_log: bool = True,
    ) -> None:
        """
        Initialize registry.

        Args:
            primary_backend: Primary storage (Redis by default)
            fallback_backend: Fallback storage (in-memory)
            enable_audit_log: Enable audit logging
        """
        self._primary = primary_backend or InMemoryBackend()
        self._fallback = fallback_backend or InMemoryBackend()
        self._enable_audit = enable_audit_log
        self._audit_log: List[Dict[str, Any]] = []

    async def get_status(self, agent_id: str) -> Optional[PenalRecord]:
        """
        Get current punishment status for agent.

        Tries primary backend first, falls back to secondary.

        Args:
            agent_id: Agent identifier

        Returns:
            PenalRecord if found, None otherwise
        """
        try:
            record = await self._primary.get(agent_id)
            if record:
                return record
        except (ConnectionError, TimeoutError, OSError):
            pass  # Primary failed, try fallback below

        # Try fallback
        return await self._fallback.get(agent_id)

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
        # Check for existing record (escalate if repeat)
        existing = await self.get_status(agent_id)

        if existing and existing.is_active:
            # Escalate punishment for repeat offense
            offense_count = existing.offense_count + 1
            if offense_count >= 3:
                status = PenalStatus.SUSPENDED
            elif offense_count >= 2 and status == PenalStatus.WARNING:
                status = PenalStatus.PROBATION
        else:
            offense_count = 1

        # Calculate end time
        until = None
        if duration:
            until = datetime.now() + duration

        # Create record
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

        # Store in both backends
        try:
            await self._primary.set(record)
        except (ConnectionError, TimeoutError, OSError):
            pass  # Primary failed, but we have fallback

        await self._fallback.set(record)

        # Audit log
        if self._enable_audit:
            self._audit_log.append({
                "action": "punish",
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "status": status.value,
                "offense": offense.value,
                "duration": str(duration) if duration else "indefinite",
            })

        return record

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

        # Delete from both backends
        try:
            await self._primary.delete(agent_id)
        except (ConnectionError, TimeoutError, OSError):
            pass  # Primary delete failed, continue with fallback

        await self._fallback.delete(agent_id)

        # Audit log
        if self._enable_audit:
            self._audit_log.append({
                "action": "pardon",
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "reason": reason,
                "previous_status": record.status.value,
            })

        return True

    async def complete_re_education(self, agent_id: str) -> bool:
        """
        Mark re-education as completed.

        May reduce punishment level.

        Args:
            agent_id: Agent identifier

        Returns:
            True if record found and updated
        """
        record = await self.get_status(agent_id)
        if not record:
            return False

        record.re_education_completed = True

        # Potentially reduce punishment
        if record.status == PenalStatus.QUARANTINE and record.re_education_completed:
            record.status = PenalStatus.PROBATION

        # Update in backends
        try:
            await self._primary.set(record)
        except (ConnectionError, TimeoutError, OSError):
            pass  # Primary update failed, continue with fallback

        await self._fallback.set(record)

        return True

    async def list_active_punishments(self) -> List[PenalRecord]:
        """List all agents with active punishments."""
        try:
            return await self._primary.list_active()
        except (ConnectionError, TimeoutError, OSError):
            return await self._fallback.list_active()

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

        # Define restrictions by status
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
        primary_health = await self._primary.health_check()
        fallback_health = await self._fallback.health_check()

        return {
            "healthy": primary_health.get("healthy") or fallback_health.get("healthy"),
            "primary": primary_health,
            "fallback": fallback_health,
            "audit_log_size": len(self._audit_log),
        }


# Convenience functions for startup hooks
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
