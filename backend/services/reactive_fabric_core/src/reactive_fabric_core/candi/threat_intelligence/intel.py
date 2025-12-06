"""
Main Threat Intelligence Class.

Threat intelligence correlation engine.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..forensic_analyzer import ForensicReport
from .correlators import CorrelatorMixin
from .databases import (
    load_campaign_database,
    load_exploit_database,
    load_ioc_database,
    load_tool_database,
)
from .misp import MISPMixin
from .models import ThreatIntelReport
from .scoring import ScoringMixin

logger = logging.getLogger(__name__)


class ThreatIntelligence(CorrelatorMixin, MISPMixin, ScoringMixin):
    """
    Threat intelligence correlation engine.

    Intelligence Sources:
    1. MISP Platform (Malware Information Sharing Platform)
    2. Local IOC database
    3. Threat actor profiles
    4. Campaign tracking
    5. CVE database

    Features:
    - Real-time IOC correlation
    - Threat actor tracking
    - Campaign identification
    - IOC enrichment
    - Threat scoring
    """

    def __init__(
        self,
        misp_url: Optional[str] = None,
        misp_key: Optional[str] = None,
    ) -> None:
        """
        Initialize threat intelligence engine.

        Args:
            misp_url: MISP instance URL
            misp_key: MISP API key
        """
        self._initialized = False

        self.misp_url = misp_url or "http://localhost:8080"
        self.misp_key = misp_key
        self.misp_available = False

        # Local intelligence databases
        self.ioc_database = load_ioc_database()
        self.tool_database = load_tool_database()
        self.exploit_database = load_exploit_database()
        self.campaign_database = load_campaign_database()

        # Cache for performance
        self.ioc_cache: Dict[str, Any] = {}
        self.cache_ttl = timedelta(hours=1)

        # Statistics
        self.stats: Dict[str, int] = {
            "total_correlations": 0,
            "ioc_hits": 0,
            "tool_hits": 0,
            "exploit_hits": 0,
            "campaign_hits": 0,
            "misp_queries": 0,
        }

    async def initialize(self) -> None:
        """Initialize threat intelligence engine."""
        if self._initialized:
            return

        logger.info("Initializing Threat Intelligence engine...")

        # Test MISP connectivity
        if self.misp_key:
            self.misp_available = await self._test_misp_connection()
            if self.misp_available:
                logger.info("MISP connection established")
            else:
                logger.warning("MISP connection failed, using local intelligence only")
        else:
            logger.info("No MISP credentials provided, using local intelligence only")

        self._initialized = True
        logger.info("Threat Intelligence engine initialized")

    async def correlate(self, forensic: ForensicReport) -> ThreatIntelReport:
        """
        Correlate forensic findings with threat intelligence.

        Args:
            forensic: Forensic analysis report

        Returns:
            Threat intelligence report
        """
        logger.info(
            "Starting threat intelligence correlation for %s",
            forensic.event_id,
        )

        report = ThreatIntelReport(
            event_id=forensic.event_id,
            timestamp=datetime.now(),
        )

        # 1. IOC Correlation
        await self._correlate_iocs(forensic, report)

        # 2. Tool Identification
        await self._correlate_tools(forensic, report)

        # 3. Exploit Correlation
        await self._correlate_exploits(forensic, report)

        # 4. Campaign Tracking
        await self._correlate_campaigns(forensic, report)

        # 5. MISP Query (if available)
        if self.misp_available:
            await self._query_misp(forensic, report)

        # 6. Enrichment - Get related IOCs
        await self._enrich_iocs(report)

        # 7. Calculate threat score
        report.threat_score = self._calculate_threat_score(report, forensic)

        # 8. Determine intelligence sources used
        report.intelligence_sources = self._get_sources_used(report)

        # 9. Calculate correlation confidence
        report.correlation_confidence = self._calculate_confidence(report)

        # Update statistics
        self._update_stats(report)

        logger.info(
            "Threat intelligence correlation complete: %s "
            "(threat score: %.1f/100, confidence: %.1f%%)",
            forensic.event_id,
            report.threat_score,
            report.correlation_confidence,
        )

        return report

    def _update_stats(self, report: ThreatIntelReport) -> None:
        """Update internal statistics."""
        self.stats["total_correlations"] += 1
        if report.known_iocs:
            self.stats["ioc_hits"] += 1
        if report.known_tools:
            self.stats["tool_hits"] += 1
        if report.known_exploits:
            self.stats["exploit_hits"] += 1
        if report.related_campaigns:
            self.stats["campaign_hits"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get threat intelligence statistics."""
        return {
            **self.stats,
            'misp_available': self.misp_available,
            'ioc_database_size': len(self.ioc_database),
            'tool_database_size': len(self.tool_database),
            'exploit_database_size': len(self.exploit_database),
            'campaign_database_size': len(self.campaign_database),
        }
