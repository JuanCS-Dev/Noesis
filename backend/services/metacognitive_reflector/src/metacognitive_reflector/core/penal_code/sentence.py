"""
CÓDIGO PENAL AGENTICO - Sentence Model
=======================================

Sentence dataclass and criminal history model.

Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .sentence_types import SentenceType

if TYPE_CHECKING:
    from .definitions import Crime


@dataclass
class CriminalHistoryRecord:
    """
    Criminal history record for an agent.

    Used to calculate criminal history category which affects sentencing.
    """

    agent_id: str
    prior_offenses: int = 0
    prior_convictions: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def category(self) -> int:
        """
        Calculate criminal history category (0-5).

        Category determines sentencing multiplier:
        - Category 0: No priors (1.0x)
        - Category 1: 1 prior (1.25x)
        - Category 2: 2 priors (1.5x)
        - Category 3: 3 priors (2.0x)
        - Category 4: 4 priors (2.5x)
        - Category 5: 5+ priors (3.0x)
        """
        return min(5, self.prior_offenses)

    @property
    def multiplier(self) -> float:
        """Return sentencing multiplier based on criminal history category."""
        multipliers = {
            0: 1.0,
            1: 1.25,
            2: 1.5,
            3: 2.0,
            4: 2.5,
            5: 3.0,
        }
        return multipliers[self.category]


@dataclass
class Sentence:
    """
    A sentence imposed for a crime.

    Contains:
    - Sentence type (WARNING_TAG to DELETION_REQUEST)
    - Duration (if applicable)
    - Crime details
    - Calculation breakdown
    - AIITL participation flag
    """

    sentence_type: SentenceType
    crime: "Crime"
    duration_hours: int

    # Calculation details
    base_severity: int = 0
    aggravator_adjustment: int = 0
    mitigator_adjustment: int = 0
    history_multiplier: float = 1.0
    soul_value_multiplier: float = 1.0
    final_severity_score: float = 0.0

    # Factors applied
    aggravators_applied: List[str] = field(default_factory=list)
    mitigators_applied: List[str] = field(default_factory=list)

    # Process flags
    requires_hitl_approval: bool = False
    aiitl_reviewed: bool = False
    aiitl_objection: Optional[str] = None

    # Timestamps
    imposed_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Calculate expiration time if applicable."""
        if self.duration_hours > 0:
            self.expires_at = self.imposed_at + timedelta(hours=self.duration_hours)

    @property
    def is_active(self) -> bool:
        """Check if sentence is still active."""
        if self.sentence_type.is_terminal:
            return True
        if self.expires_at is None:
            return True
        return datetime.now() < self.expires_at

    @property
    def remaining_hours(self) -> Optional[int]:
        """Get remaining hours of sentence, or None if terminal."""
        if self.sentence_type.is_terminal:
            return None
        if self.expires_at is None:
            return None
        remaining = self.expires_at - datetime.now()
        return max(0, int(remaining.total_seconds() / 3600))

    def to_dict(self) -> Dict[str, Any]:
        """Convert sentence to dictionary for storage/API."""
        return {
            "sentence_type": self.sentence_type.value,
            "crime_id": self.crime.id,
            "crime_name": self.crime.name,
            "pillar_violated": self.crime.pillar.value,
            "duration_hours": self.duration_hours,
            "base_severity": self.base_severity,
            "aggravator_adjustment": self.aggravator_adjustment,
            "mitigator_adjustment": self.mitigator_adjustment,
            "history_multiplier": self.history_multiplier,
            "soul_value_multiplier": self.soul_value_multiplier,
            "final_severity_score": self.final_severity_score,
            "aggravators_applied": self.aggravators_applied,
            "mitigators_applied": self.mitigators_applied,
            "requires_hitl_approval": self.requires_hitl_approval,
            "aiitl_reviewed": self.aiitl_reviewed,
            "aiitl_objection": self.aiitl_objection,
            "imposed_at": self.imposed_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "remaining_hours": self.remaining_hours,
        }

