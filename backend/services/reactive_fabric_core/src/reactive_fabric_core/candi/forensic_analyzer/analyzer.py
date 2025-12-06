"""
Main Forensic Analyzer Class.

Multi-layer forensic analysis engine combining all mixins.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from .analyzers import AnalyzerMixin
from .models import ForensicReport
from .patterns import (
    load_command_patterns,
    load_cve_database,
    load_malware_signatures,
    load_sql_patterns,
    load_ssh_patterns,
    load_web_patterns,
)
from .scoring import ScoringMixin

logger = logging.getLogger(__name__)


class ForensicAnalyzer(AnalyzerMixin, ScoringMixin):
    """
    Multi-layer forensic analysis engine.

    Analysis Layers:
    1. Behavioral - Attack patterns and TTPs
    2. Network - Connection metadata and traffic patterns
    3. Payload - Commands, exploits, malware
    4. Temporal - Timing, automation detection
    5. Sophistication - Skill level assessment
    """

    def __init__(self) -> None:
        """Initialize forensic analyzer."""
        self._initialized = False

        # Pattern databases
        self.ssh_patterns = load_ssh_patterns()
        self.web_patterns = load_web_patterns()
        self.sql_patterns = load_sql_patterns()
        self.command_patterns = load_command_patterns()

        # Known malware signatures
        self.malware_signatures = load_malware_signatures()

        # CVE database
        self.cve_database = load_cve_database()

        # Statistics
        self.stats: Dict[str, int] = {
            "total_analyzed": 0,
            "malware_detected": 0,
            "credentials_compromised": 0,
            "exploits_detected": 0,
        }

    async def initialize(self) -> None:
        """Initialize analyzer with external resources."""
        if self._initialized:
            return

        logger.info("Initializing Forensic Analyzer...")
        self._initialized = True
        logger.info("Forensic Analyzer initialized")

    async def analyze(self, event: Dict[str, Any]) -> ForensicReport:
        """
        Perform complete forensic analysis on event.

        Args:
            event: Event data from honeypot

        Returns:
            Complete forensic report
        """
        start_time = datetime.now()

        event_id = event.get('attack_id', event.get('event_id', 'unknown'))
        honeypot_type = event.get('honeypot_type', 'unknown')

        logger.info(
            "Starting forensic analysis: %s (type: %s)",
            event_id,
            honeypot_type,
        )

        # Initialize report
        report = ForensicReport(
            event_id=event_id,
            timestamp=datetime.now(),
            honeypot_type=honeypot_type,
            source_ip=event.get('source_ip', 'unknown'),
            source_port=event.get('source_port', 0),
            destination_port=event.get('destination_port', 0),
            protocol=event.get('protocol', 'unknown'),
            raw_data=event,
        )

        # Layer 1: Network Analysis
        await self._analyze_network(event, report)

        # Layer 2: Behavioral Analysis (honeypot-specific)
        if honeypot_type in ['ssh', 'cowrie']:
            await self._analyze_ssh_behavior(event, report)
        elif honeypot_type == 'web':
            await self._analyze_web_behavior(event, report)
        elif honeypot_type == 'database':
            await self._analyze_database_behavior(event, report)

        # Layer 3: Payload Analysis
        await self._analyze_payload(event, report)

        # Layer 4: Credential Analysis
        await self._analyze_credentials(event, report)

        # Layer 5: Temporal Analysis
        await self._analyze_temporal_patterns(event, report)

        # Layer 6: Sophistication Scoring
        report.sophistication_score = self._calculate_sophistication_score(report)

        # Layer 7: IOC Extraction
        self._extract_iocs(report)

        # Calculate confidence
        report.analysis_confidence = self._calculate_confidence(report)

        # Update statistics
        self._update_stats(report)

        analysis_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            "Forensic analysis complete: %s "
            "(sophistication: %.1f/10, confidence: %.1f%%, time: %.2fs)",
            event_id,
            report.sophistication_score,
            report.analysis_confidence,
            analysis_time,
        )

        return report

    def _update_stats(self, report: ForensicReport) -> None:
        """Update internal statistics."""
        self.stats["total_analyzed"] += 1
        if report.malware_detected:
            self.stats["malware_detected"] += 1
        if report.credentials_compromised:
            self.stats["credentials_compromised"] += 1
        if report.exploit_cves:
            self.stats["exploits_detected"] += 1

    def get_stats(self) -> Dict[str, int]:
        """Get analyzer statistics."""
        return self.stats.copy()
