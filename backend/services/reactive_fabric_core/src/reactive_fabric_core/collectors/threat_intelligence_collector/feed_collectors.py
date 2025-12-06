"""
Feed Collectors for Threat Intelligence Collector.

Methods for collecting from external threat intelligence feeds.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    import aiohttp

    from .models import ThreatIndicator, ThreatIntelligenceConfig

logger = logging.getLogger(__name__)


class FeedCollectorMixin:
    """Mixin providing feed collection capabilities."""

    config: ThreatIntelligenceConfig
    session: aiohttp.ClientSession

    async def _collect_virustotal(self) -> List[Any]:
        """Collect recent threat indicators from VirusTotal (if available)."""
        return []

    async def _collect_abuseipdb(self) -> List[Any]:
        """Collect recent threat indicators from AbuseIPDB."""
        return []

    async def _collect_alienvault(self) -> List[Any]:
        """Collect recent threat indicators from AlienVault OTX."""
        from .models import ThreatIndicator

        indicators = []

        try:
            headers = {"X-OTX-API-KEY": self.config.alienvault_api_key}
            url = "https://otx.alienvault.com/api/v1/pulses/subscribed"
            params = {"limit": 10, "page": 1}

            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return indicators

                data = await response.json()

                for pulse in data.get("results", [])[:5]:
                    for indicator in pulse.get("indicators", [])[:10]:
                        ind = ThreatIndicator(
                            indicator_type=indicator.get("type", "unknown"),
                            value=indicator.get("indicator", ""),
                            source="alienvault",
                            severity="medium",
                            confidence=0.7,
                            tags=pulse.get("tags", []),
                            metadata={
                                "pulse_name": pulse.get("name"),
                                "pulse_id": pulse.get("id")
                            }
                        )
                        indicators.append(ind)

        except Exception as e:
            logger.error("AlienVault collection failed: %s", e)

        return indicators

    async def _collect_misp(self) -> List[Any]:
        """Collect recent threat indicators from MISP."""
        from .models import ThreatIndicator

        indicators = []

        try:
            headers = {
                "Authorization": self.config.misp_api_key,
                "Accept": "application/json"
            }

            url = f"{self.config.misp_url}/events/index"
            params = {"limit": 10, "published": 1}

            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return indicators

                data = await response.json()

                for event in data[:5]:
                    event_id = event.get("Event", {}).get("id")
                    if not event_id:
                        continue

                    detail_url = f"{self.config.misp_url}/events/view/{event_id}"

                    async with self.session.get(detail_url, headers=headers) as detail_response:
                        if detail_response.status != 200:
                            continue

                        event_data = await detail_response.json()

                        for attribute in event_data.get("Event", {}).get("Attribute", [])[:10]:
                            ind = ThreatIndicator(
                                indicator_type=attribute.get("type", "unknown"),
                                value=attribute.get("value", ""),
                                source="misp",
                                severity="high",
                                confidence=0.8,
                                tags=[attribute.get("category", "")],
                                metadata={
                                    "event_id": event_id,
                                    "event_info": event_data.get("Event", {}).get("info")
                                }
                            )
                            indicators.append(ind)

        except Exception as e:
            logger.error("MISP collection failed: %s", e)

        return indicators
