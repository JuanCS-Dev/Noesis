"""
OSINT Workflows Endpoints.

AI-driven OSINT automation endpoints.

Author: MAXIMUS Team
Date: 2025-10-15
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from workflows.attack_surface_adw import (
    AttackSurfaceTarget,
    AttackSurfaceWorkflow,
)
from workflows.credential_intel_adw import (
    CredentialIntelWorkflow,
    CredentialTarget,
)
from workflows.target_profiling import (
    ProfileTarget,
    TargetProfilingWorkflow,
)

from .dependencies import (
    get_attack_surface_workflow,
    get_credential_intel_workflow,
    get_target_profiling_workflow,
)
from .models import (
    AttackSurfaceRequest,
    CredentialIntelRequest,
    ProfileTargetRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/workflows/attack-surface")
async def execute_attack_surface_workflow(
    request: AttackSurfaceRequest,
    background_tasks: BackgroundTasks,
    workflow: AttackSurfaceWorkflow = Depends(get_attack_surface_workflow),
) -> dict[str, Any]:
    """Execute Attack Surface Mapping workflow.

    Combines Network Recon + Vuln Intel + Service Detection for comprehensive
    attack surface analysis.

    Args:
        request: Target configuration

    Returns:
        Dict with workflow ID and initial status
    """
    try:
        target = AttackSurfaceTarget(
            domain=request.domain,
            include_subdomains=request.include_subdomains,
            port_range=request.port_range,
            scan_depth=request.scan_depth,
        )

        logger.info(f"Starting attack surface workflow for {request.domain}")

        # Execute workflow
        report = await workflow.execute(target)

        return {
            "workflow_id": report.workflow_id,
            "status": report.status.value,
            "target": report.target,
            "message": "Attack surface mapping initiated",
        }

    except Exception as e:
        logger.error(f"Attack surface workflow failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/workflows/credential-intel")
async def execute_credential_intel_workflow(
    request: CredentialIntelRequest,
    background_tasks: BackgroundTasks,
    workflow: CredentialIntelWorkflow = Depends(get_credential_intel_workflow),
) -> dict[str, Any]:
    """Execute Credential Intelligence workflow.

    Combines Breach Data + Google Dorking + Dark Web + Username Hunter
    for credential exposure analysis.

    Args:
        request: Target configuration

    Returns:
        Dict with workflow ID and initial status
    """
    try:
        if not request.email and not request.username:
            raise HTTPException(
                status_code=400, detail="Must provide email or username"
            )

        target = CredentialTarget(
            email=request.email,
            username=request.username,
            phone=request.phone,
            include_darkweb=request.include_darkweb,
            include_dorking=request.include_dorking,
            include_social=request.include_social,
        )

        logger.info(
            f"Starting credential intelligence workflow for "
            f"{request.email or request.username}"
        )

        # Execute workflow
        report = await workflow.execute(target)

        return {
            "workflow_id": report.workflow_id,
            "status": report.status.value,
            "target_email": report.target_email,
            "target_username": report.target_username,
            "message": "Credential intelligence gathering initiated",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Credential intelligence workflow failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/workflows/target-profile")
async def execute_target_profiling_workflow(
    request: ProfileTargetRequest,
    background_tasks: BackgroundTasks,
    workflow: TargetProfilingWorkflow = Depends(get_target_profiling_workflow),
) -> dict[str, Any]:
    """Execute Deep Target Profiling workflow.

    Combines Social Scraper + Email/Phone Analyzer + Image Analysis +
    Pattern Detection for comprehensive target profiling.

    Args:
        request: Target configuration

    Returns:
        Dict with workflow ID and initial status
    """
    try:
        if not any([request.username, request.email, request.name]):
            raise HTTPException(
                status_code=400, detail="Must provide username, email, or name"
            )

        target = ProfileTarget(
            username=request.username,
            email=request.email,
            phone=request.phone,
            name=request.name,
            location=request.location,
            image_url=request.image_url,
            include_social=request.include_social,
            include_images=request.include_images,
        )

        logger.info(
            f"Starting target profiling workflow for "
            f"{request.username or request.email or request.name}"
        )

        # Execute workflow
        report = await workflow.execute(target)

        return {
            "workflow_id": report.workflow_id,
            "status": report.status.value,
            "target_username": report.target_username,
            "target_email": report.target_email,
            "message": "Target profiling initiated",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Target profiling workflow failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    attack_surface: AttackSurfaceWorkflow = Depends(get_attack_surface_workflow),
    credential_intel: CredentialIntelWorkflow = Depends(get_credential_intel_workflow),
    target_profiling: TargetProfilingWorkflow = Depends(get_target_profiling_workflow),
) -> dict[str, Any]:
    """Get workflow execution status.

    Checks all workflow types for the given ID.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Dict with workflow status

    Raises:
        HTTPException: If workflow not found
    """
    # Try each workflow type
    status = (
        attack_surface.get_workflow_status(workflow_id)
        or credential_intel.get_workflow_status(workflow_id)
        or target_profiling.get_workflow_status(workflow_id)
    )

    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return status


@router.get("/workflows/{workflow_id}/report")
async def get_workflow_report(
    workflow_id: str,
    attack_surface: AttackSurfaceWorkflow = Depends(get_attack_surface_workflow),
    credential_intel: CredentialIntelWorkflow = Depends(get_credential_intel_workflow),
    target_profiling: TargetProfilingWorkflow = Depends(get_target_profiling_workflow),
) -> dict[str, Any]:
    """Get complete workflow report.

    Retrieves full report from any workflow type.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Dict with complete workflow report

    Raises:
        HTTPException: If workflow not found or not completed
    """
    # Try attack surface
    report = attack_surface.active_workflows.get(workflow_id)
    if report:
        if report.status.value != "completed":
            raise HTTPException(
                status_code=409, detail="Workflow not yet completed"
            )
        return report.to_dict()

    # Try credential intel
    report = credential_intel.active_workflows.get(workflow_id)
    if report:
        if report.status.value != "completed":
            raise HTTPException(
                status_code=409, detail="Workflow not yet completed"
            )
        return report.to_dict()

    # Try target profiling
    report = target_profiling.active_workflows.get(workflow_id)
    if report:
        if report.status.value != "completed":
            raise HTTPException(
                status_code=409, detail="Workflow not yet completed"
            )
        return report.to_dict()

    raise HTTPException(status_code=404, detail="Workflow not found")
