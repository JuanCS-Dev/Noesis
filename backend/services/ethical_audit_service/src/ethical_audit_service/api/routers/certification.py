"""Compliance & Certification Endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ethical_audit_service.auth import TokenData, require_admin, require_auditor_or_admin, require_soc_or_admin

from ..state import get_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.post("/check")
async def check_compliance(
    request: Request,
    regulation_type: str,
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Check compliance for specific regulation."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("10/minute")(request)

    try:
        from maximus_core_service.compliance import (
            ComplianceConfig,
            ComplianceEngine,
            RegulationType,
        )

        reg_type = RegulationType(regulation_type)

        config = ComplianceConfig(enabled_regulations=[reg_type])
        engine = ComplianceEngine(config)

        result = engine.check_compliance(reg_type)

        return {
            "regulation": regulation_type,
            "compliance_percentage": result.compliance_percentage,
            "score": result.score,
            "total_controls": result.total_controls,
            "compliant": result.compliant,
            "non_compliant": result.non_compliant,
            "violations": len(result.violations),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Compliance check failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/status")
async def get_compliance_status(
    request: Request,
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get overall compliance status for all regulations."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("30/minute")(request)

    try:
        from maximus_core_service.compliance import ComplianceEngine

        engine = ComplianceEngine()

        status = engine.get_compliance_status()

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Get compliance status failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/gaps")
async def analyze_gaps(
    request: Request,
    regulation_type: str,
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Analyze compliance gaps for regulation."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("10/minute")(request)

    try:
        from maximus_core_service.compliance import (
            ComplianceEngine,
            GapAnalyzer,
            RegulationType,
        )

        reg_type = RegulationType(regulation_type)
        engine = ComplianceEngine()
        analyzer = GapAnalyzer()

        compliance_result = engine.check_compliance(reg_type)

        gap_analysis = analyzer.analyze_compliance_gaps(compliance_result)

        return {
            "regulation": regulation_type,
            "total_gaps": len(gap_analysis.gaps),
            "compliance_percentage": gap_analysis.compliance_percentage,
            "estimated_hours": gap_analysis.estimated_remediation_hours,
            "gaps": [
                {
                    "control_id": g.control_id,
                    "title": g.title,
                    "severity": g.severity.value,
                    "priority": g.priority,
                    "effort_hours": g.estimated_effort_hours,
                }
                for g in gap_analysis.gaps[:20]
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Gap analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/remediation")
async def create_remediation_plan(
    request: Request,
    regulation_type: str,
    target_days: int = 180,
    current_user: TokenData = Depends(require_admin),
) -> dict[str, Any]:
    """Create remediation plan for compliance gaps."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("5/minute")(request)

    try:
        from maximus_core_service.compliance import (
            ComplianceEngine,
            GapAnalyzer,
            RegulationType,
        )

        reg_type = RegulationType(regulation_type)
        engine = ComplianceEngine()
        analyzer = GapAnalyzer()

        compliance_result = engine.check_compliance(reg_type)
        gap_analysis = analyzer.analyze_compliance_gaps(compliance_result)

        plan = analyzer.create_remediation_plan(
            gap_analysis,
            target_completion_days=target_days,
            created_by=current_user.user_id,
        )

        return {
            "plan_id": plan.plan_id,
            "regulation": regulation_type,
            "total_actions": len(plan.actions),
            "target_completion": plan.target_completion_date.isoformat(),
            "status": plan.status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Remediation plan creation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/evidence")
async def list_evidence(
    request: Request,
    control_id: str | None = None,
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """List collected compliance evidence."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("20/minute")(request)

    try:
        from maximus_core_service.compliance import ComplianceConfig, EvidenceCollector

        config = ComplianceConfig()
        collector = EvidenceCollector(config)

        if control_id:
            evidence = collector.get_evidence_for_control(control_id)
        else:
            all_evidence = collector.get_all_evidence()
            evidence = [e for items in all_evidence.values() for e in items]

        return {
            "total_evidence": len(evidence),
            "evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "type": e.evidence_type.value,
                    "control_id": e.control_id,
                    "title": e.title,
                    "collected_at": e.collected_at.isoformat(),
                    "verified": e.verified,
                    "expired": e.is_expired(),
                }
                for e in evidence[:50]
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("List evidence failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/evidence/collect")
async def collect_evidence(
    request: Request,
    control_id: str,
    evidence_type: str,
    title: str,
    description: str,
    file_path: str,
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Collect new compliance evidence."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("10/minute")(request)

    try:
        from maximus_core_service.compliance import (
            ComplianceConfig,
            EvidenceCollector,
            EvidenceType,
        )
        from maximus_core_service.compliance.regulations import get_regulation

        config = ComplianceConfig()
        collector = EvidenceCollector(config)

        ev_type = EvidenceType(evidence_type)

        control = None
        for reg_type in config.enabled_regulations:
            regulation = get_regulation(reg_type)
            control = regulation.get_control(control_id)
            if control:
                break

        if not control:
            raise HTTPException(status_code=404, detail=f"Control {control_id} not found")

        if ev_type == EvidenceType.LOG:
            evidence_item = collector.collect_log_evidence(
                control, file_path, title, description
            )
        elif ev_type == EvidenceType.DOCUMENT:
            evidence_item = collector.collect_document_evidence(
                control, file_path, title, description
            )
        elif ev_type == EvidenceType.CONFIGURATION:
            evidence_item = collector.collect_configuration_evidence(
                control, file_path, title, description
            )
        elif ev_type == EvidenceType.POLICY:
            evidence_item = collector.collect_policy_evidence(
                control, file_path, title, description
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported evidence type: {evidence_type}"
            )

        if not evidence_item:
            raise HTTPException(status_code=500, detail="Evidence collection failed")

        return {
            "evidence_id": evidence_item.evidence.evidence_id,
            "control_id": control_id,
            "type": evidence_type,
            "title": title,
            "file_size": evidence_item.file_size,
            "file_hash": evidence_item.evidence.file_hash,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Evidence collection failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/certification")
async def check_certification_readiness(
    request: Request,
    regulation_type: str,
    current_user: TokenData = Depends(require_admin),
) -> dict[str, Any]:
    """Check certification readiness for regulation."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("5/minute")(request)

    try:
        from maximus_core_service.compliance import (
            ComplianceConfig,
            ComplianceEngine,
            EvidenceCollector,
            RegulationType,
        )
        from maximus_core_service.compliance.certifications import (
            IEEE7000Checker,
            ISO27001Checker,
            SOC2Checker,
        )

        reg_type = RegulationType(regulation_type)
        config = ComplianceConfig()
        engine = ComplianceEngine(config)
        collector = EvidenceCollector(config)

        if reg_type == RegulationType.ISO_27001:
            checker = ISO27001Checker(engine, collector)
        elif reg_type == RegulationType.SOC2_TYPE_II:
            checker = SOC2Checker(engine, collector)
        elif reg_type == RegulationType.IEEE_7000:
            checker = IEEE7000Checker(engine, collector)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Certification checker not available for {regulation_type}",
            )

        cert_result = checker.check_certification_readiness()

        return {
            "regulation": regulation_type,
            "certification_ready": cert_result.certification_ready,
            "compliance_percentage": cert_result.compliance_percentage,
            "score": cert_result.score,
            "gaps_to_certification": cert_result.gaps_to_certification,
            "critical_gaps": cert_result.critical_gaps,
            "estimated_days": cert_result.estimated_days_to_certification,
            "recommendations": cert_result.recommendations[:10],
            "summary": cert_result.get_summary(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Certification readiness check failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/dashboard")
async def get_compliance_dashboard(
    request: Request,
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get compliance dashboard data."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("20/minute")(request)

    try:
        from maximus_core_service.compliance import (
            ComplianceConfig,
            ComplianceEngine,
            ComplianceMonitor,
            EvidenceCollector,
        )

        config = ComplianceConfig()
        engine = ComplianceEngine(config)
        collector = EvidenceCollector(config)
        monitor = ComplianceMonitor(engine, collector, config=config)

        monitor._run_monitoring_checks()

        dashboard = monitor.generate_dashboard_data()

        return {
            "dashboard": dashboard,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Get compliance dashboard failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
