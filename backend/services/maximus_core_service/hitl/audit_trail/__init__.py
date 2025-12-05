"""
HITL Audit Trail Package.

Immutable audit trail for all HITL decisions and actions.

This package provides:
- Complete decision history logging
- Compliance reporting
- Forensic investigation support
- PII redaction for privacy compliance
- Time-series analysis

All entries are immutable and timestamped for regulatory compliance.

Compliance Standards:
- SOC 2 Type II
- ISO 27001
- PCI-DSS
- HIPAA (with PII redaction)
- GDPR (with right to erasure)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Refactored: 2025-12-03
"""

from __future__ import annotations

# Core audit trail
from .core import AuditTrail

# Data models
from .models import AuditQuery, ComplianceReport

# Mixins (for advanced usage)
from .compliance import ComplianceReportingMixin
from .event_logger import EventLoggingMixin
from .query_engine import QueryMixin

# PII redaction
from .pii import PIIRedactor

# Storage backends
from .storage import InMemoryStorage, StorageBackend, StorageError

__all__ = [
    # Main classes
    "AuditTrail",
    "AuditQuery",
    "ComplianceReport",
    # Mixins
    "EventLoggingMixin",
    "QueryMixin",
    "ComplianceReportingMixin",
    # PII
    "PIIRedactor",
    # Storage
    "StorageBackend",
    "InMemoryStorage",
    "StorageError",
]
