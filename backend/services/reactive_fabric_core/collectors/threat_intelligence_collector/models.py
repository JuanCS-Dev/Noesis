"""
Models for Threat Intelligence Collector.

Configuration and data models for threat indicators.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..base_collector import CollectorConfig


class ThreatIntelligenceConfig(CollectorConfig):
    """Configuration for Threat Intelligence Collector."""

    # API Keys
    virustotal_api_key: Optional[str] = Field(
        default=None, description="VirusTotal API key"
    )
    abuseipdb_api_key: Optional[str] = Field(
        default=None, description="AbuseIPDB API key"
    )
    alienvault_api_key: Optional[str] = Field(
        default=None, description="AlienVault OTX API key"
    )
    misp_url: Optional[str] = Field(
        default=None, description="MISP instance URL"
    )
    misp_api_key: Optional[str] = Field(
        default=None, description="MISP API key"
    )

    # Collection settings
    check_ips: bool = Field(default=True, description="Check IP addresses")
    check_domains: bool = Field(default=True, description="Check domain names")
    check_hashes: bool = Field(default=True, description="Check file hashes")
    check_urls: bool = Field(default=True, description="Check URLs")

    # Rate limiting
    requests_per_minute: int = Field(
        default=60, description="Max API requests per minute"
    )
    cache_ttl_minutes: int = Field(
        default=60, description="Cache TTL in minutes"
    )

    # Thresholds
    min_reputation_score: float = Field(
        default=0.3, description="Minimum reputation score to flag as threat"
    )
    max_false_positives: int = Field(
        default=5, description="Max false positives before reducing confidence"
    )


class ThreatIndicator(BaseModel):
    """Represents a threat indicator."""

    indicator_type: str  # ip, domain, hash, url
    value: str
    source: str
    severity: str
    confidence: float
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
