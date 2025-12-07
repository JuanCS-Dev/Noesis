"""Safety Endpoints - Safety protocol status and violations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from maximus_core_service.consciousness.api_schemas import (
    EmergencyShutdownRequest,
    SafetyStatusResponse,
    SafetyViolationResponse,
)


def register_safety_endpoints(
    router: APIRouter,
    consciousness_system: dict[str, Any],
) -> None:
    """Register safety-related endpoints."""

    @router.get("/safety/status", response_model=SafetyStatusResponse)
    async def get_safety_status() -> SafetyStatusResponse:
        """Get safety protocol status."""
        try:
            system = consciousness_system.get("system")
            if not system:
                raise HTTPException(
                    status_code=503, detail="Consciousness system not initialized"
                )
            status = system.get_safety_status()
            if not status:
                raise HTTPException(
                    status_code=503, detail="Safety protocol not enabled in this system"
                )
            return SafetyStatusResponse(**status)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving safety status: {str(e)}"
            ) from e

    @router.get("/safety/violations", response_model=list[SafetyViolationResponse])
    async def get_safety_violations(limit: int = 100) -> list[SafetyViolationResponse]:
        """Get recent safety violations."""
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=400, detail="Limit must be between 1 and 1000"
            )
        try:
            system = consciousness_system.get("system")
            if not system:
                raise HTTPException(
                    status_code=503, detail="Consciousness system not initialized"
                )
            violations = system.get_safety_violations(limit=limit)
            return [
                SafetyViolationResponse(
                    violation_id=v.violation_id,
                    violation_type=v.violation_type.value,
                    severity=v.severity.value,
                    timestamp=v.timestamp.isoformat(),
                    value_observed=v.value_observed,
                    threshold_violated=v.threshold_violated,
                    message=v.message,
                    context=v.context,
                )
                for v in violations
            ]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving violations: {str(e)}"
            ) from e

    @router.post("/safety/emergency-shutdown")
    async def execute_emergency_shutdown(
        request: EmergencyShutdownRequest,
    ) -> dict[str, Any]:
        """Execute emergency shutdown (HITL only)."""
        try:
            system = consciousness_system.get("system")
            if not system:
                raise HTTPException(
                    status_code=503, detail="Consciousness system not initialized"
                )
            shutdown_executed = await system.execute_emergency_shutdown(
                reason=request.reason
            )
            return {
                "success": True,
                "shutdown_executed": shutdown_executed,
                "message": (
                    "Emergency shutdown executed"
                    if shutdown_executed
                    else "HITL overrode shutdown"
                ),
                "timestamp": datetime.now().isoformat(),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error executing emergency shutdown: {str(e)}",
            ) from e
