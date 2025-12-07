"""Configuration classes for HITL module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from .enums import RiskLevel


@dataclass
class SLAConfig:
    """SLA configuration per risk level."""

    low_risk_sla: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    medium_risk_sla: timedelta = field(default_factory=lambda: timedelta(minutes=15))
    high_risk_sla: timedelta = field(default_factory=lambda: timedelta(minutes=10))
    critical_risk_sla: timedelta = field(default_factory=lambda: timedelta(minutes=5))

    def get_sla_for_risk(self, risk: RiskLevel) -> timedelta:
        """Get SLA timeout for risk level."""
        sla_map = {
            RiskLevel.LOW: self.low_risk_sla,
            RiskLevel.MEDIUM: self.medium_risk_sla,
            RiskLevel.HIGH: self.high_risk_sla,
            RiskLevel.CRITICAL: self.critical_risk_sla,
        }
        return sla_map.get(risk, self.medium_risk_sla)


@dataclass
class EscalationConfig:
    """Escalation chain configuration."""

    enable_auto_escalation: bool = True
    escalation_levels: list[str] = field(default_factory=lambda: ["operator", "supervisor", "manager", "executive"])
    escalation_delay_minutes: int = 5


@dataclass
class HITLConfig:
    """Global HITL framework configuration."""

    sla_config: SLAConfig = field(default_factory=SLAConfig)
    escalation_config: EscalationConfig = field(default_factory=EscalationConfig)
    enable_auto_execution: bool = True
    require_dual_approval_critical: bool = True
    audit_all_decisions: bool = True
    retention_days: int = 90
