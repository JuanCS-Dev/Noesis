"""Compliance Logging Endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from backend.services.ethical_audit_service.models import (
    ComplianceCheckRequest,
    ComplianceCheckResponse,
)

from ..state import get_db

router = APIRouter(prefix="/audit", tags=["compliance"])


@router.post("/compliance", response_model=ComplianceCheckResponse)
async def log_compliance_check(check: ComplianceCheckRequest) -> ComplianceCheckResponse:
    """Log a regulatory compliance check.

    Supports multiple regulations:
    - EU AI Act
    - GDPR Article 22
    - NIST AI RMF
    - Tallinn Manual 2.0
    - Executive Order 14110
    - Brazil LGPD
    """
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        compliance_id = await db.log_compliance_check(check)

        return ComplianceCheckResponse(
            compliance_id=compliance_id,
            timestamp=datetime.utcnow(),
            regulation=check.regulation,
            requirement_id=check.requirement_id,
            check_result=check.check_result,
            remediation_required=check.remediation_required,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to log compliance check: {e!s}"
        ) from e
