"""
HCL Executor Service - Action Models
====================================

Pydantic models for action definitions.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ActionParameters(BaseModel):
    """
    Parameters for an infrastructure action.

    Attributes:
        deployment_name: Name of the target deployment
        namespace: Kubernetes namespace
        replicas: Target replica count (for scaling)
        cpu_limit: CPU resource limit (e.g., "500m")
        memory_limit: Memory resource limit (e.g., "512Mi")
        pod_name: Name of the target pod (for restarts)
    """

    deployment_name: Optional[str] = Field(default=None, description="Target deployment name")
    namespace: Optional[str] = Field(default=None, description="Kubernetes namespace")
    replicas: Optional[int] = Field(default=None, description="Target replica count")
    cpu_limit: Optional[str] = Field(default=None, description="CPU limit")
    memory_limit: Optional[str] = Field(default=None, description="Memory limit")
    pod_name: Optional[str] = Field(default=None, description="Target pod name")


class Action(BaseModel):
    """
    Action definition.

    Attributes:
        type: Action type identifier
        parameters: Action parameters
        priority: Execution priority (higher is more urgent)
    """

    type: str = Field(..., description="Action type identifier")
    parameters: ActionParameters = Field(
        default_factory=ActionParameters,
        description="Action parameters"
    )
    priority: int = Field(default=1, description="Execution priority")


class ActionResult(BaseModel):
    """
    Result of an action execution.

    Attributes:
        action_type: Type of action executed
        status: Execution status ("success", "failed")
        details: Result details or error message
        timestamp: Execution timestamp
    """

    action_type: str = Field(..., description="Executed action type")
    status: str = Field(..., description="Execution status")
    details: str = Field(..., description="Result details")
    timestamp: float = Field(..., description="Execution timestamp")


class ExecuteRequest(BaseModel):
    """
    Request to execute actions.

    Attributes:
        plan_id: ID of the plan
        actions: List of actions to execute
    """

    plan_id: str = Field(..., description="Plan ID")
    actions: list[Action] = Field(..., description="List of actions")
