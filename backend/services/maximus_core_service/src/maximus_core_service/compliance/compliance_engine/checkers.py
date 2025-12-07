"""Compliance Control Checkers.

Default checker functions for different control categories.
"""

from __future__ import annotations

from ..base import (
    ComplianceConfig,
    ComplianceResult,
    ComplianceStatus,
    Control,
    ControlCategory,
)


def check_technical_control(
    control: Control,
    config: ComplianceConfig,
) -> ComplianceResult:
    """Check technical controls (encryption, access control, etc).

    Args:
        control: Control to check.
        config: Compliance configuration.

    Returns:
        Compliance check result.
    """
    result = ComplianceResult(
        control_id=control.control_id,
        regulation_type=control.regulation_type,
        status=ComplianceStatus.PENDING_REVIEW,
        checked_by="compliance_engine",
        automated=True,
    )

    if control.evidence_required:
        result.status = ComplianceStatus.EVIDENCE_REQUIRED
        result.notes = f"Evidence required: {[e.value for e in control.evidence_required]}"
    else:
        result.status = ComplianceStatus.PENDING_REVIEW
        result.notes = "Manual review required - no automated check available"

    return result


def check_security_control(
    control: Control,
    config: ComplianceConfig,
) -> ComplianceResult:
    """Check security controls (monitoring, incident response, etc).

    Args:
        control: Control to check.
        config: Compliance configuration.

    Returns:
        Compliance check result.
    """
    result = ComplianceResult(
        control_id=control.control_id,
        regulation_type=control.regulation_type,
        status=ComplianceStatus.PENDING_REVIEW,
        checked_by="compliance_engine",
        automated=True,
    )

    if control.evidence_required:
        result.status = ComplianceStatus.EVIDENCE_REQUIRED
        result.notes = (
            f"Security evidence required: {[e.value for e in control.evidence_required]}"
        )
    else:
        result.status = ComplianceStatus.PENDING_REVIEW
        result.notes = "Security control requires manual review"

    return result


def check_documentation_control(
    control: Control,
    config: ComplianceConfig,
) -> ComplianceResult:
    """Check documentation controls.

    Args:
        control: Control to check.
        config: Compliance configuration.

    Returns:
        Compliance check result.
    """
    return ComplianceResult(
        control_id=control.control_id,
        regulation_type=control.regulation_type,
        status=ComplianceStatus.EVIDENCE_REQUIRED,
        checked_by="compliance_engine",
        automated=True,
        notes="Documentation evidence required",
    )


def check_monitoring_control(
    control: Control,
    config: ComplianceConfig,
) -> ComplianceResult:
    """Check monitoring controls (logging, alerting, etc).

    Args:
        control: Control to check.
        config: Compliance configuration.

    Returns:
        Compliance check result.
    """
    return ComplianceResult(
        control_id=control.control_id,
        regulation_type=control.regulation_type,
        status=ComplianceStatus.EVIDENCE_REQUIRED,
        checked_by="compliance_engine",
        automated=True,
        notes="Monitoring logs/configuration evidence required",
    )


def check_governance_control(
    control: Control,
    config: ComplianceConfig,
) -> ComplianceResult:
    """Check governance controls (policies, procedures, etc).

    Args:
        control: Control to check.
        config: Compliance configuration.

    Returns:
        Compliance check result.
    """
    return ComplianceResult(
        control_id=control.control_id,
        regulation_type=control.regulation_type,
        status=ComplianceStatus.EVIDENCE_REQUIRED,
        checked_by="compliance_engine",
        automated=True,
        notes="Policy/procedure documentation required",
    )


def check_testing_control(
    control: Control,
    config: ComplianceConfig,
) -> ComplianceResult:
    """Check testing controls.

    Args:
        control: Control to check.
        config: Compliance configuration.

    Returns:
        Compliance check result.
    """
    return ComplianceResult(
        control_id=control.control_id,
        regulation_type=control.regulation_type,
        status=ComplianceStatus.EVIDENCE_REQUIRED,
        checked_by="compliance_engine",
        automated=True,
        notes="Test results evidence required",
    )


def check_organizational_control(
    control: Control,
    config: ComplianceConfig,
) -> ComplianceResult:
    """Check organizational controls.

    Args:
        control: Control to check.
        config: Compliance configuration.

    Returns:
        Compliance check result.
    """
    return ComplianceResult(
        control_id=control.control_id,
        regulation_type=control.regulation_type,
        status=ComplianceStatus.PENDING_REVIEW,
        checked_by="compliance_engine",
        automated=True,
        notes="Organizational control requires manual review",
    )


def check_privacy_control(
    control: Control,
    config: ComplianceConfig,
) -> ComplianceResult:
    """Check privacy controls.

    Args:
        control: Control to check.
        config: Compliance configuration.

    Returns:
        Compliance check result.
    """
    return ComplianceResult(
        control_id=control.control_id,
        regulation_type=control.regulation_type,
        status=ComplianceStatus.EVIDENCE_REQUIRED,
        checked_by="compliance_engine",
        automated=True,
        notes="Privacy controls evidence required (DPIA, consent records, etc)",
    )


def get_default_category_checkers() -> dict[ControlCategory, callable]:
    """Get default checkers mapped to control categories.

    Returns:
        Dict mapping ControlCategory to checker function.
    """
    return {
        ControlCategory.TECHNICAL: check_technical_control,
        ControlCategory.SECURITY: check_security_control,
        ControlCategory.DOCUMENTATION: check_documentation_control,
        ControlCategory.MONITORING: check_monitoring_control,
        ControlCategory.GOVERNANCE: check_governance_control,
        ControlCategory.TESTING: check_testing_control,
        ControlCategory.ORGANIZATIONAL: check_organizational_control,
        ControlCategory.PRIVACY: check_privacy_control,
    }
