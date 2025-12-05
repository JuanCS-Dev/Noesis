"""Evidence Collector Package.

Automated evidence collection system for compliance verification.

Features:
- Multi-source evidence collection (logs, configs, tests, docs)
- Automated evidence discovery
- Evidence integrity verification (SHA-256 hashing)
- Evidence packaging for auditors
- Evidence expiration tracking
"""

from __future__ import annotations

from .collector import EvidenceCollector
from .models import EvidenceItem, EvidencePackage, calculate_file_hash

__all__ = [
    "EvidenceCollector",
    "EvidenceItem",
    "EvidencePackage",
    "calculate_file_hash",
]
