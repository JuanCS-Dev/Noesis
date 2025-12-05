"""
Models for Threat Intelligence.

Data classes for threat intelligence reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ThreatIntelReport:
    """Threat intelligence correlation report."""

    event_id: str
    timestamp: datetime

    # Matched intelligence
    known_iocs: List[str] = field(default_factory=list)
    known_tools: List[str] = field(default_factory=list)
    known_exploits: List[str] = field(default_factory=list)
    related_campaigns: List[str] = field(default_factory=list)

    # IOC enrichment
    related_iocs: List[str] = field(default_factory=list)
    ioc_reputation: Dict[str, str] = field(default_factory=dict)

    # Threat context
    threat_tags: List[str] = field(default_factory=list)
    threat_score: float = 0.0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    # MISP events
    misp_events: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    intelligence_sources: List[str] = field(default_factory=list)
    correlation_confidence: float = 0.0
