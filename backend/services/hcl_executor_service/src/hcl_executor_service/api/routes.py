"""
HCL Executor Service - API Routes
=================================

FastAPI routes for the service.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from ..core.executor import ActionExecutor
from ..models.actions import ExecuteRequest, ActionResult
from .dependencies import get_executor

router = APIRouter()


@router.post("/execute", response_model=List[ActionResult])
async def execute_actions(
    request: ExecuteRequest,
    executor: ActionExecutor = Depends(get_executor)
) -> List[ActionResult]:
    """
    Execute a list of infrastructure actions.

    Args:
        request: Execution request containing plan_id and actions
        executor: Injected executor instance

    Returns:
        List of execution results
    """
    if not request.actions:
        raise HTTPException(status_code=400, detail="No actions provided")

    return await executor.execute_actions(request.plan_id, request.actions)


@router.get("/status")
async def get_status(
    executor: ActionExecutor = Depends(get_executor)
) -> Dict[str, Any]:
    """
    Get executor status.

    Returns:
        Status dictionary
    """
    return await executor.get_status()
