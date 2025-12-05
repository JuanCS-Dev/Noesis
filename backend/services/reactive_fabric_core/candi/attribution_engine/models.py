"""
Models for Attribution Engine.

Data classes for attribution analysis results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AttributionResult:
    """Attribution analysis result."""

    attributed_actor: Optional[str] = None
    confidence: float = 0.0

    # Evidence
    matching_ttps: List[str] = field(default_factory=list)
    matching_tools: List[str] = field(default_factory=list)
    matching_infrastructure: List[str] = field(default_factory=list)

    # Actor characteristics
    actor_type: str = "unknown"
    motivation: Optional[str] = None

    # APT indicators
    apt_indicators: List[str] = field(default_factory=list)

    # Alternative candidates
    alternative_actors: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    confidence_factors: Dict[str, float] = field(default_factory=dict)
