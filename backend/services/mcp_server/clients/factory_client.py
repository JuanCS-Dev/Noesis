"""
Tool Factory Service Client
===========================

Client for tool_factory_service.

Follows CODE_CONSTITUTION: Clarity Over Cleverness.
"""

from __future__ import annotations

from typing import Any, Dict, List, cast

from clients.base_client import BaseHTTPClient
from config import MCPServerConfig


class FactoryClient:
    """Client for Tool Factory service.

    Provides methods to generate, execute, and manage dynamic tools.

    Example:
        >>> client = FactoryClient(config)
        >>> spec = await client.generate_tool("double", "Double a number", examples)
        >>> print(spec["success_rate"])
        0.9
    """

    def __init__(self, config: MCPServerConfig):
        """Initialize Factory client.

        Args:
            config: Service configuration
        """
        self.config = config
        self.client = BaseHTTPClient(config, config.factory_url)

    async def generate_tool(
        self, name: str, description: str, examples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate new tool dynamically.

        Args:
            name: Tool name (snake_case)
            description: What the tool does
            examples: Test cases for validation

        Returns:
            ToolSpec with validated code

        Example:
            >>> spec = await client.generate_tool(
            ...     "double",
            ...     "Double a number",
            ...     [{"input": {"x": 2}, "expected": 4}]
            ... )
        """
        payload = {"name": name, "description": description, "examples": examples}
        result = await self.client.post("/v1/tools/generate", json=payload)
        return result

    async def execute_tool(
        self, tool_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute registered tool.

        Args:
            tool_name: Name of registered tool
            params: Parameters for execution

        Returns:
            Execution result with return value

        Example:
            >>> result = await client.execute_tool("double", {"x": 5})
            >>> result["return_value"]
            10
        """
        result = await self.client.post(
            f"/v1/tools/{tool_name}/execute", json=params
        )
        return result

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools.

        Returns:
            List of ToolSpec dicts
        """
        result = await self.client.get("/v1/tools")
        # API returns {"tools": [...]}
        tools = result.get("tools", [])
        return cast(List[Dict[str, Any]], tools)

    async def get_tool(self, tool_name: str) -> Dict[str, Any]:
        """Get specific tool spec.

        Args:
            tool_name: Name of tool

        Returns:
            ToolSpec dict
        """
        result = await self.client.get(f"/v1/tools/{tool_name}")
        return result

    async def delete_tool(self, tool_name: str) -> bool:
        """Delete tool from registry.

        Args:
            tool_name: Name of tool to delete

        Returns:
            True if deleted successfully
        """
        result = await self.client.delete(f"/v1/tools/{tool_name}")
        return result.get("success", False)

    async def get_stats(self) -> Dict[str, Any]:
        """Get factory statistics.

        Returns:
            Generation and execution stats
        """
        result = await self.client.get("/v1/stats")
        return result

    async def close(self) -> None:
        """Close client connections."""
        await self.client.close()
