"""
Indicator Checkers for Threat Intelligence Collector.

Methods for checking IP, domain, and hash reputation.
"""

from __future__ import annotations

import ipaddress
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import aiohttp

    from .models import ThreatIndicator, ThreatIntelligenceConfig

logger = logging.getLogger(__name__)


class IndicatorCheckerMixin:
    """Mixin providing indicator checking capabilities."""

    config: ThreatIntelligenceConfig
    session: aiohttp.ClientSession
    cache: Dict[str, Any]
    request_times: List[datetime]

    async def check_ip(self, ip_address: str) -> Optional[ThreatIndicator]:
        """Check IP address reputation."""
        from .models import ThreatIndicator

        if not self.config.check_ips:
            return None

        cache_key = f"ip:{ip_address}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return None

        if not await self._check_rate_limit():
            return None

        scores = []
        metadata = {}

        if self.config.virustotal_api_key:
            vt_score = await self._check_ip_virustotal(ip_address)
            if vt_score is not None:
                scores.append(vt_score)
                metadata["virustotal"] = vt_score

        if self.config.abuseipdb_api_key:
            abuse_score = await self._check_ip_abuseipdb(ip_address)
            if abuse_score is not None:
                scores.append(abuse_score)
                metadata["abuseipdb"] = abuse_score

        if not scores:
            return None

        avg_score = sum(scores) / len(scores)

        if avg_score >= self.config.min_reputation_score:
            indicator = ThreatIndicator(
                indicator_type="ip",
                value=ip_address,
                source="multiple",
                severity=self._score_to_severity(avg_score),
                confidence=avg_score,
                metadata=metadata
            )
            self.cache[cache_key] = indicator
            return indicator

        return None

    async def check_domain(self, domain: str) -> Optional[ThreatIndicator]:
        """Check domain reputation."""
        from .models import ThreatIndicator

        if not self.config.check_domains:
            return None

        cache_key = f"domain:{domain}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not await self._check_rate_limit():
            return None

        scores = []
        metadata = {}

        if self.config.virustotal_api_key:
            vt_score = await self._check_domain_virustotal(domain)
            if vt_score is not None:
                scores.append(vt_score)
                metadata["virustotal"] = vt_score

        if not scores:
            return None

        avg_score = sum(scores) / len(scores)

        if avg_score >= self.config.min_reputation_score:
            indicator = ThreatIndicator(
                indicator_type="domain",
                value=domain,
                source="multiple",
                severity=self._score_to_severity(avg_score),
                confidence=avg_score,
                metadata=metadata
            )
            self.cache[cache_key] = indicator
            return indicator

        return None

    async def check_hash(self, file_hash: str) -> Optional[ThreatIndicator]:
        """Check file hash reputation."""
        from .models import ThreatIndicator

        if not self.config.check_hashes:
            return None

        cache_key = f"hash:{file_hash}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not await self._check_rate_limit():
            return None

        scores = []
        metadata = {}

        if self.config.virustotal_api_key:
            vt_score = await self._check_hash_virustotal(file_hash)
            if vt_score is not None:
                scores.append(vt_score)
                metadata["virustotal"] = vt_score

        if not scores:
            return None

        avg_score = sum(scores) / len(scores)

        if avg_score >= self.config.min_reputation_score:
            indicator = ThreatIndicator(
                indicator_type="hash",
                value=file_hash,
                source="multiple",
                severity=self._score_to_severity(avg_score),
                confidence=avg_score,
                metadata=metadata
            )
            self.cache[cache_key] = indicator
            return indicator

        return None

    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]

        if len(self.request_times) >= self.config.requests_per_minute:
            return False

        self.request_times.append(now)
        return True

    async def _check_ip_virustotal(self, ip_address: str) -> Optional[float]:
        """Check IP reputation on VirusTotal."""
        try:
            headers = {"x-apikey": self.config.virustotal_api_key}
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_address}"

            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values())

                if total > 0:
                    return malicious / total

        except Exception as e:
            logger.error("VirusTotal IP check failed: %s", e)

        return None

    async def _check_ip_abuseipdb(self, ip_address: str) -> Optional[float]:
        """Check IP reputation on AbuseIPDB."""
        try:
            headers = {"Key": self.config.abuseipdb_api_key}
            url = "https://api.abuseipdb.com/api/v2/check"
            params = {"ipAddress": ip_address, "maxAgeInDays": 90}

            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                score = data.get("data", {}).get("abuseConfidenceScore", 0)
                return score / 100.0

        except Exception as e:
            logger.error("AbuseIPDB check failed: %s", e)

        return None

    async def _check_domain_virustotal(self, domain: str) -> Optional[float]:
        """Check domain reputation on VirusTotal."""
        try:
            headers = {"x-apikey": self.config.virustotal_api_key}
            url = f"https://www.virustotal.com/api/v3/domains/{domain}"

            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values())

                if total > 0:
                    return malicious / total

        except Exception as e:
            logger.error("VirusTotal domain check failed: %s", e)

        return None

    async def _check_hash_virustotal(self, file_hash: str) -> Optional[float]:
        """Check file hash reputation on VirusTotal."""
        try:
            headers = {"x-apikey": self.config.virustotal_api_key}
            url = f"https://www.virustotal.com/api/v3/files/{file_hash}"

            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values())

                if total > 0:
                    return malicious / total

        except Exception as e:
            logger.error("VirusTotal hash check failed: %s", e)

        return None

    def _score_to_severity(self, score: float) -> str:
        """Convert reputation score to severity level."""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
