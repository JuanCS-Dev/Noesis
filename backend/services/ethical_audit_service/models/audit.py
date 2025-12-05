"""
Ethical Audit Service - Audit Models
====================================

Pydantic models for constitutional compliance auditing.
"""

from __future__ import annotations


from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ViolationType(str, Enum):
    """Types of constitutional violations."""

    SOVEREIGNTY_VIOLATION = "sovereignty_violation"
    DARK_PATTERN = "dark_pattern"
    FAKE_SUCCESS = "fake_success"
    SILENT_MODIFICATION = "silent_modification"
    PLACEHOLDER_CODE = "placeholder_code"
    MISSING_TYPE_HINTS = "missing_type_hints"


class ViolationSeverity(str, Enum):
    """Severity levels for violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """
    Audit event representation.

    Attributes:
        event_id: Unique event identifier
        timestamp: Event timestamp
        service: Service being audited
        operation: Operation being performed
        metadata: Additional event metadata
    """

    event_id: str = Field(..., description="Event identifier")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Event timestamp"
    )
    service: str = Field(..., description="Service name")
    operation: str = Field(..., description="Operation performed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class Violation(BaseModel):
    """
    Constitutional violation representation.

    Attributes:
        violation_id: Unique violation identifier
        violation_type: Type of violation
        severity: Violation severity
        description: Human-readable description
        service: Service where violation occurred
        timestamp: When violation was detected
        details: Additional violation details
        remediation: Suggested remediation steps
    """

    violation_id: str = Field(..., description="Violation identifier")
    violation_type: ViolationType = Field(..., description="Violation type")
    severity: ViolationSeverity = Field(..., description="Severity level")
    description: str = Field(..., description="Violation description")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Detection timestamp"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details"
    )
    remediation: str | None = Field(
        default=None,
        description="Remediation steps"
    )


class ComplianceReport(BaseModel):
    """
    Constitutional compliance report.

    Attributes:
        report_id: Unique report identifier
        timestamp: Report generation timestamp
        service: Service being reported on
        total_checks: Total compliance checks performed
        passed_checks: Number of checks passed
        violations: List of violations found
        compliance_score: Overall compliance score (0.0 to 1.0)
    """

    report_id: str = Field(..., description="Report identifier")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Report timestamp"
    )
    service: str = Field(..., description="Service name")
    total_checks: int = Field(..., description="Total checks performed")
    passed_checks: int = Field(..., description="Passed checks count")
    violations: List[Violation] = Field(
        default_factory=list,
        description="Violations found"
    )
    compliance_score: float = Field(
        ...,
        description="Compliance score",
        ge=0.0,
        le=1.0
    )
