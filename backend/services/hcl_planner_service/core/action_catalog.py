"""
HCL Planner Service - Action Catalog
====================================

Defines all available infrastructure actions that the HCL Planner can recommend.
Actions are organized by category and include full parameter specifications.
"""

from __future__ import annotations

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ActionParameter:
    """
    Specification for an action parameter.

    Attributes:
        name: Parameter name
        type: Parameter type (e.g., "string", "integer")
        description: Human-readable description
        required: Whether parameter is required
        default: Default value if not required
    """

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Action:
    """
    Infrastructure action definition.

    Attributes:
        type: Action type identifier
        description: Human-readable description
        category: Action category (scaling, resources, lifecycle)
        parameters: List of parameter specifications
    """

    type: str
    description: str
    category: str
    parameters: List[ActionParameter] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert action to dictionary format for Gemini API.

        Returns:
            Dictionary representation suitable for prompt
        """
        return {
            "type": self.type,
            "description": self.description,
            "category": self.category,
            "parameters": {
                param.name: f"{param.type} ({'required' if param.required else 'optional'})"
                for param in self.parameters
            }
        }


# Scaling Actions
SCALE_DEPLOYMENT = Action(
    type="scale_deployment",
    description="Scale a Kubernetes deployment up or down",
    category="scaling",
    parameters=[
        ActionParameter(
            name="deployment_name",
            type="string",
            description="Name of the deployment to scale"
        ),
        ActionParameter(
            name="namespace",
            type="string",
            description="Kubernetes namespace",
            required=False,
            default="default"
        ),
        ActionParameter(
            name="replicas",
            type="integer",
            description="Target number of replicas"
        )
    ]
)

# Resource Actions
UPDATE_RESOURCE_LIMITS = Action(
    type="update_resource_limits",
    description="Update CPU/Memory limits for a deployment",
    category="resources",
    parameters=[
        ActionParameter(
            name="deployment_name",
            type="string",
            description="Name of the deployment"
        ),
        ActionParameter(
            name="namespace",
            type="string",
            description="Kubernetes namespace",
            required=False,
            default="default"
        ),
        ActionParameter(
            name="cpu_limit",
            type="string",
            description="CPU limit (e.g., '500m', '2')"
        ),
        ActionParameter(
            name="memory_limit",
            type="string",
            description="Memory limit (e.g., '512Mi', '2Gi')"
        )
    ]
)

# Lifecycle Actions
RESTART_POD = Action(
    type="restart_pod",
    description="Restart a specific pod to resolve stuck states",
    category="lifecycle",
    parameters=[
        ActionParameter(
            name="pod_name",
            type="string",
            description="Name of the pod to restart"
        ),
        ActionParameter(
            name="namespace",
            type="string",
            description="Kubernetes namespace",
            required=False,
            default="default"
        )
    ]
)

# Default action catalog
DEFAULT_HCL_ACTIONS: List[Action] = [
    SCALE_DEPLOYMENT,
    UPDATE_RESOURCE_LIMITS,
    RESTART_POD,
]


def get_action_catalog() -> List[Dict[str, Any]]:
    """
    Get action catalog in format suitable for Gemini prompt.

    Returns:
        List of action dictionaries

    Example:
        >>> catalog = get_action_catalog()
        >>> print(catalog[0]["type"])
        "scale_deployment"
    """
    return [action.to_dict() for action in DEFAULT_HCL_ACTIONS]
