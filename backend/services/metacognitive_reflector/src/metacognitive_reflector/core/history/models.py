"""
NOESIS Memory Fortress - Criminal History Models
=================================================

Data models for criminal history tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class Conviction:
    """A single conviction record."""
    
    crime_id: str
    crime_name: str
    sentence_type: str
    severity: str
    pillar: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "crime_id": self.crime_id,
            "crime_name": self.crime_name,
            "sentence_type": self.sentence_type,
            "severity": self.severity,
            "pillar": self.pillar,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conviction":
        """Create from dictionary."""
        return cls(
            crime_id=data["crime_id"],
            crime_name=data.get("crime_name", data["crime_id"]),
            sentence_type=data["sentence_type"],
            severity=data["severity"],
            pillar=data.get("pillar", "UNKNOWN"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=data.get("context", {}),
        )


@dataclass
class CriminalHistory:
    """
    Complete criminal history for an agent.

    Used by SentencingEngine for:
    - Recidivism calculation
    - Pattern detection
    - Aggravating factors
    """
    
    agent_id: str
    convictions: List[Conviction] = field(default_factory=list)
    first_offense_date: Optional[datetime] = None
    last_offense_date: Optional[datetime] = None

    @property
    def prior_offenses(self) -> int:
        """Total number of prior offenses."""
        return len(self.convictions)

    @property
    def is_recidivist(self) -> bool:
        """Check if agent has prior convictions."""
        return self.prior_offenses > 0

    def get_crime_count(self, crime_id: str) -> int:
        """Get number of times a specific crime was committed."""
        return sum(1 for c in self.convictions if c.crime_id == crime_id)

    def get_pillar_violations(self, pillar: str) -> int:
        """Get violations against a specific pillar (VERITAS, SOPHIA, DIKĒ)."""
        return sum(1 for c in self.convictions if c.pillar == pillar)

    def get_recent_convictions(self, days: int = 30) -> List[Conviction]:
        """Get convictions within the last N days."""
        cutoff = datetime.now().replace(microsecond=0) - timedelta(days=days)
        return [c for c in self.convictions if c.timestamp > cutoff]

    def calculate_recidivism_factor(self) -> float:
        """
        Calculate recidivism aggravating factor.

        Formula based on:
        - Number of prior offenses
        - Recency of offenses
        - Severity pattern

        Returns:
            Factor between 1.0 (no aggravation) and 2.0 (max aggravation)
        """
        if not self.convictions:
            return 1.0

        count_factor = min(1.5, 1.0 + (self.prior_offenses * 0.1))
        recent = self.get_recent_convictions(30)
        recency_factor = 1.0 + (len(recent) * 0.15)

        return min(2.0, count_factor * recency_factor)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "agent_id": self.agent_id,
            "convictions": [c.to_dict() for c in self.convictions],
            "first_offense_date": self.first_offense_date.isoformat() if self.first_offense_date else None,
            "last_offense_date": self.last_offense_date.isoformat() if self.last_offense_date else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriminalHistory":
        """Create from dictionary."""
        convictions = [Conviction.from_dict(c) for c in data.get("convictions", [])]
        return cls(
            agent_id=data["agent_id"],
            convictions=convictions,
            first_offense_date=datetime.fromisoformat(data["first_offense_date"]) if data.get("first_offense_date") else None,
            last_offense_date=datetime.fromisoformat(data["last_offense_date"]) if data.get("last_offense_date") else None,
        )

