"""
Ethical Audit Service - API Routes
==================================

FastAPI endpoints for Guardian Agent operations.
"""

from __future__ import annotations


from typing import Any, Dict

from fastapi import APIRouter, Depends

from ethical_audit_service.core.constitutional_validator import ConstitutionalValidator
from ethical_audit_service.core.violation_detector import ViolationDetector
from ethical_audit_service.models.audit import ComplianceReport, Violation
from ethical_audit_service.api.dependencies import get_detector, get_validator

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check() -> dict[str, str]:
    """
    Service health check.

    Returns:
        Basic health status
    """
    return {"status": "healthy", "service": "ethical-audit-service"}


@router.post("/validate", response_model=dict)
async def validate_operation(
    service: str,
    operation: str,
    payload: Dict[str, Any],
    validator: ConstitutionalValidator = Depends(get_validator),
    detector: ViolationDetector = Depends(get_detector)
) -> dict[str, Any]:
    """
    Validate operation against constitutional principles.

    Args:
        service: Service name
        operation: Operation name
        payload: Operation payload
        validator: Constitutional validator instance
        detector: Violation detector instance

    Returns:
        Validation result with violations if any
    """
    is_valid, violations = await validator.validate_operation(
        service,
        operation,
        payload
    )

    # Record violations
    for violation in violations:
        await detector.record_violation(violation)

    return {
        "is_valid": is_valid,
        "violation_count": len(violations),
        "violations": [v.model_dump() for v in violations]
    }


@router.post("/violations", response_model=dict)
async def record_violation(
    violation: Violation,
    detector: ViolationDetector = Depends(get_detector)
) -> dict[str, str]:
    """
    Manually record a constitutional violation.

    Args:
        violation: Violation to record
        detector: Violation detector instance

    Returns:
        Recording confirmation
    """
    await detector.record_violation(violation)
    return {
        "status": "recorded",
        "violation_id": violation.violation_id
    }


@router.get("/compliance/{service}", response_model=ComplianceReport)
async def get_compliance_report(
    service: str,
    detector: ViolationDetector = Depends(get_detector)
) -> ComplianceReport:
    """
    Get compliance report for a service.

    Args:
        service: Service name
        detector: Violation detector instance

    Returns:
        Compliance report
    """
    # Simplified: assume 10 total checks for demo
    total_checks = 10
    return await detector.generate_compliance_report(service, total_checks)


@router.delete("/violations/{service}", response_model=dict)
async def clear_violations(
    service: str,
    detector: ViolationDetector = Depends(get_detector)
) -> dict[str, Any]:
    """
    Clear violation history for a service.

    Args:
        service: Service name
        detector: Violation detector instance

    Returns:
        Clear confirmation with count
    """
    count = await detector.clear_history(service)
    return {"status": "cleared", "count": count}
