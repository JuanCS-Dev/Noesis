"""
Models for Forensic Analyzer.

Data classes for forensic analysis reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ForensicReport:
    """Complete forensic analysis report."""

    event_id: str
    timestamp: datetime

    # Behavioral Analysis
    behaviors: List[str] = field(default_factory=list)
    attack_stages: List[str] = field(default_factory=list)
    sophistication_score: float = 0.0

    # Network Analysis
    source_ip: str = ""
    source_port: int = 0
    destination_port: int = 0
    protocol: str = ""
    user_agent: Optional[str] = None
    connection_duration: float = 0.0
    bytes_transferred: int = 0

    # Payload Analysis
    malware_detected: bool = False
    malware_family: Optional[str] = None
    file_hashes: List[str] = field(default_factory=list)
    exploit_cves: List[str] = field(default_factory=list)
    suspicious_commands: List[str] = field(default_factory=list)

    # Indicators of Compromise
    network_iocs: List[str] = field(default_factory=list)
    file_iocs: List[str] = field(default_factory=list)

    # Credential Analysis
    credentials_compromised: bool = False
    usernames_attempted: List[str] = field(default_factory=list)
    passwords_attempted: List[str] = field(default_factory=list)

    # Temporal Analysis
    attack_duration: float = 0.0
    request_rate: float = 0.0
    is_automated: bool = False

    # Context
    honeypot_type: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    analysis_confidence: float = 0.0
