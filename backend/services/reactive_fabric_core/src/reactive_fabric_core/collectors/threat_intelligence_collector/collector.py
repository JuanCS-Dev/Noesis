"""
Threat Intelligence Collector for external threat feed integration.

This collector interfaces with various threat intelligence sources including:
- MISP (Malware Information Sharing Platform)
- VirusTotal API
- AbuseIPDB
- AlienVault OTX
- Custom threat feeds

Phase 1: PASSIVE collection only - no automated responses
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional, Set

import aiohttp

from ..base_collector import BaseCollector, CollectedEvent
from .checkers import IndicatorCheckerMixin
from .feed_collectors import FeedCollectorMixin
from .models import ThreatIndicator, ThreatIntelligenceConfig
from .validators import SourceValidatorMixin

logger = logging.getLogger(__name__)


class ThreatIntelligenceCollector(
    SourceValidatorMixin,
    IndicatorCheckerMixin,
    FeedCollectorMixin,
    BaseCollector
):
    """
    Collector for external threat intelligence feeds.

    Integrates with multiple threat intelligence sources to:
    - Validate IP reputation
    - Check domain/URL blocklists
    - Verify file hash indicators
    - Correlate with known threat campaigns

    Phase 1: PASSIVE collection only
    """

    def __init__(self, config: ThreatIntelligenceConfig):
        """Initialize threat intelligence collector."""
        super().__init__(config)
        self.config: ThreatIntelligenceConfig = config
        self.session: Optional[aiohttp.ClientSession] = None

        # Rate limiting
        self.request_times: List[datetime] = []

        # Cache for threat indicators
        self.cache: Dict[str, ThreatIndicator] = {}

        # Tracking false positives
        self.false_positives: Set[str] = set()

    async def initialize(self) -> None:
        """Initialize threat intelligence connections."""
        connector = aiohttp.TCPConnector(ssl=True)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        )

        logger.info("Initialized Threat Intelligence Collector")

    async def validate_source(self) -> bool:
        """Validate connectivity to at least one threat intel source."""
        if not self.session:
            return False

        validations = []

        if self.config.virustotal_api_key:
            validations.append(self._validate_virustotal())

        if self.config.abuseipdb_api_key:
            validations.append(self._validate_abuseipdb())

        if self.config.alienvault_api_key:
            validations.append(self._validate_alienvault())

        if self.config.misp_url and self.config.misp_api_key:
            validations.append(self._validate_misp())

        if not validations:
            logger.warning("No threat intelligence sources configured")
            return False

        results = await asyncio.gather(*validations, return_exceptions=True)
        return any(r is True for r in results if not isinstance(r, Exception))

    async def collect(self) -> AsyncIterator[CollectedEvent]:
        """Collect threat intelligence events."""
        if not self.session:
            return

        self._clean_cache()

        indicators: List[ThreatIndicator] = []

        if self.config.virustotal_api_key:
            vt_indicators = await self._collect_virustotal()
            indicators.extend(vt_indicators)

        if self.config.abuseipdb_api_key:
            abuse_indicators = await self._collect_abuseipdb()
            indicators.extend(abuse_indicators)

        if self.config.alienvault_api_key:
            otx_indicators = await self._collect_alienvault()
            indicators.extend(otx_indicators)

        if self.config.misp_url and self.config.misp_api_key:
            misp_indicators = await self._collect_misp()
            indicators.extend(misp_indicators)

        for indicator in indicators:
            if await self._should_report(indicator):
                event = self._indicator_to_event(indicator)
                self.metrics.events_collected += 1
                yield event

    async def _should_report(self, indicator: ThreatIndicator) -> bool:
        """Check if indicator should be reported."""
        if indicator.value in self.false_positives:
            return False

        if indicator.confidence < self.config.min_reputation_score:
            return False

        return True

    def _indicator_to_event(self, indicator: ThreatIndicator) -> CollectedEvent:
        """Convert threat indicator to collected event."""
        return CollectedEvent(
            collector_type="ThreatIntelligence",
            source=f"threatintel:{indicator.source}",
            severity=indicator.severity,
            raw_data={
                "indicator": indicator.value,
                "type": indicator.indicator_type,
                "confidence": indicator.confidence
            },
            parsed_data={
                "indicator_type": indicator.indicator_type,
                "indicator_value": indicator.value,
                "confidence": indicator.confidence,
                "source": indicator.source,
                "metadata": indicator.metadata
            },
            tags=[
                f"type:{indicator.indicator_type}",
                f"source:{indicator.source}",
                f"confidence:{indicator.confidence:.2f}",
                *indicator.tags
            ]
        )

    def _clean_cache(self) -> None:
        """Remove expired entries from cache."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self.config.cache_ttl_minutes)

        expired_keys = []
        for key, indicator in self.cache.items():
            if isinstance(indicator, ThreatIndicator):
                if indicator.last_seen < cutoff:
                    expired_keys.append(key)
            elif isinstance(indicator, dict):
                timestamp = indicator.get("timestamp") or indicator.get("last_seen")
                if timestamp and timestamp < cutoff:
                    expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

    async def cleanup(self) -> None:
        """Clean up collector resources."""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Cleaned up Threat Intelligence Collector")
