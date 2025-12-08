"""
NOESIS Memory Fortress - Penal Models
======================================

Data models for punishment persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class PenalStatus(str, Enum):
    """Agent punishment status."""

    CLEAR = "clear"  # No active punishment
    WARNING = "warning"  # Has warning on record
    PROBATION = "probation"  # Under observation
    QUARANTINE = "quarantine"  # Isolated, restricted actions
    SUSPENDED = "suspended"  # Cannot act at all
    DELETED = "deleted"  # Marked for deletion


class OffenseType(str, Enum):
    """Types of offenses."""

    TRUTH_VIOLATION = "truth_violation"
    WISDOM_VIOLATION = "wisdom_violation"
    ROLE_VIOLATION = "role_violation"
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"
    SCOPE_VIOLATION = "scope_violation"
    REPEATED_OFFENSE = "repeated_offense"


class WriteStrategy(str, Enum):
    """Strategy for writing to backends."""

    WRITE_THROUGH = "write_through"  # Write to ALL backends
    WRITE_PRIMARY = "write_primary"  # Write only to primary


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

