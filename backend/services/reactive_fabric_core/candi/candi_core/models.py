"""
Models for CANDI Core.

Threat levels, analysis results, and incidents.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..attribution_engine import AttributionResult
from ..forensic_analyzer import ForensicReport
from ..threat_intelligence import ThreatIntelReport

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat classification levels."""

    NOISE = 1           # Automated scans, bots
    OPPORTUNISTIC = 2   # Generic exploits, script kiddies
    TARGETED = 3        # Directed attacks, custom tools
    APT = 4             # Advanced Persistent Threat, nation-state


@dataclass
class AnalysisResult:
    """Complete analysis result from CANDI."""

    analysis_id: str
    timestamp: datetime
    honeypot_id: str
    source_ip: str
    threat_level: ThreatLevel

    # Analysis components
    forensic_report: ForensicReport
    threat_intel: ThreatIntelReport
    attribution: AttributionResult

    # Extracted intelligence
    iocs: List[str] = field(default_factory=list)
    ttps: List[str] = field(default_factory=list)

    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    requires_hitl: bool = False
    confidence_score: float = 0.0

    # Metadata
    processing_time_ms: int = 0
    incident_id: Optional[str] = None


class Incident:
    """Tracked security incident."""

    def __init__(self, incident_id: str, initial_event: Dict[str, Any]) -> None:
        """Initialize incident."""
        self.incident_id = incident_id
        self.created_at = datetime.now()
        self.status = "ACTIVE"
        self.events: List[Dict[str, Any]] = [initial_event]
        self.threat_level = ThreatLevel.NOISE
        self.attributed_actor: Optional[str] = None
        self.assigned_to: Optional[str] = None

    def add_event(self, event: Dict[str, Any]) -> None:
        """Add related event to incident."""
        self.events.append(event)

    def escalate(self, new_level: ThreatLevel) -> None:
        """Escalate incident threat level."""
        if new_level.value > self.threat_level.value:
            self.threat_level = new_level
            logger.warning(
                "Incident %s escalated to %s",
                self.incident_id,
                new_level.name,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert incident to dictionary."""
        return {
            "incident_id": self.incident_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "threat_level": self.threat_level.name,
            "event_count": len(self.events),
            "attributed_actor": self.attributed_actor,
            "assigned_to": self.assigned_to,
        }
