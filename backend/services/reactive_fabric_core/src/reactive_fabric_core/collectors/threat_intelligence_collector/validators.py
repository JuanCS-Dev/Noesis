"""
Source Validators for Threat Intelligence Collector.

Validates connectivity to external threat intelligence sources.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import aiohttp

    from .models import ThreatIntelligenceConfig

logger = logging.getLogger(__name__)


class SourceValidatorMixin:
    """Mixin providing source validation capabilities."""

    config: ThreatIntelligenceConfig
    session: aiohttp.ClientSession

    async def _validate_virustotal(self) -> bool:
        """Validate VirusTotal API connectivity."""
        try:
            headers = {"x-apikey": self.config.virustotal_api_key}
            url = "https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8"

            async with self.session.get(url, headers=headers) as response:
                return response.status == 200
        except Exception as e:
            logger.error("VirusTotal validation failed: %s", e)
            return False

    async def _validate_abuseipdb(self) -> bool:
        """Validate AbuseIPDB API connectivity."""
        try:
            headers = {"Key": self.config.abuseipdb_api_key}
            url = "https://api.abuseipdb.com/api/v2/check"
            params = {"ipAddress": "8.8.8.8"}

            async with self.session.get(url, headers=headers, params=params) as response:
                return response.status == 200
        except Exception as e:
            logger.error("AbuseIPDB validation failed: %s", e)
            return False

    async def _validate_alienvault(self) -> bool:
        """Validate AlienVault OTX API connectivity."""
        try:
            headers = {"X-OTX-API-KEY": self.config.alienvault_api_key}
            url = "https://otx.alienvault.com/api/v1/indicators/IPv4/8.8.8.8/general"

            async with self.session.get(url, headers=headers) as response:
                return response.status == 200
        except Exception as e:
            logger.error("AlienVault validation failed: %s", e)
            return False

    async def _validate_misp(self) -> bool:
        """Validate MISP API connectivity."""
        try:
            headers = {
                "Authorization": self.config.misp_api_key,
                "Accept": "application/json"
            }
            url = f"{self.config.misp_url}/servers/getVersion"

            async with self.session.get(url, headers=headers) as response:
                return response.status == 200
        except Exception as e:
            logger.error("MISP validation failed: %s", e)
            return False
