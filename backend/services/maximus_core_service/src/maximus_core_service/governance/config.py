"""
Governance Configuration.

Configuration settings for governance module.
"""

from __future__ import annotations

from dataclasses import dataclass

from .enums import AuditLogLevel, PolicySeverity


@dataclass
class GovernanceConfig:
    """Configuration for governance module."""

    # ERB Configuration
    erb_meeting_frequency_days: int = 30  # Monthly meetings
    erb_quorum_percentage: float = 0.6  # 60% quorum required
    erb_decision_threshold: float = 0.75  # 75% approval required

    # Policy Configuration
    policy_review_frequency_days: int = 365  # Annual policy review
    auto_enforce_policies: bool = True
    policy_violation_alert_threshold: PolicySeverity = PolicySeverity.MEDIUM

    # Audit Configuration
    audit_retention_days: int = 2555  # 7 years (GDPR requirement)
    audit_log_level: AuditLogLevel = AuditLogLevel.INFO
    enable_blockchain_audit: bool = False  # Optional Phase 1

    # Whistleblower Configuration
    whistleblower_anonymity: bool = True
    whistleblower_protection_days: int = 365

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "vertice_governance"
    db_user: str = "vertice"
    db_password: str = ""
