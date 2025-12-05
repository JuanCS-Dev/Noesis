"""
Threat Intelligence Collector Package.

External threat feed integration for Reactive Fabric.
"""

from __future__ import annotations

from .collector import ThreatIntelligenceCollector
from .models import ThreatIndicator, ThreatIntelligenceConfig

__all__ = [
    "ThreatIndicator",
    "ThreatIntelligenceCollector",
    "ThreatIntelligenceConfig",
]
