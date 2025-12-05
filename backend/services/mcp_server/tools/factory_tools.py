"""
Tool Factory MCP Tools
======================

MCP tools for tool_factory_service.

Follows CODE_CONSTITUTION: Clarity Over Cleverness.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ToolGenerateRequest(BaseModel):
    """Request model for tool generation."""

    name: str = Field(..., pattern="^[a-z_][a-z0-9_]*$")
    description: str = Field(..., min_length=10, max_length=500)
    examples: List[Dict[str, Any]] = Field(..., min_length=1, max_length=10)


async def factory_generate(
    name: str,
    description: str,
    examples: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Gera nova tool dinamicamente.

    Uses LLM + AST validation + sandbox testing to generate working code.
    Iterative improvement loop (max 3 attempts) fixes bugs automatically.

    Args:
        name: Tool name (snake_case, alphanumeric + underscore)
        description: What the tool does (10-500 chars)
        examples: Test cases with input/expected pairs (1-10 examples)

    Returns:
        ToolSpec with validated code and success_rate

    Example:
        >>> spec = await factory_generate(
        ...     "double",
        ...     "Double a number",
        ...     [{"input": {"x": 2}, "expected": 4}]
        ... )
        >>> spec["success_rate"]
        1.0
    """
    request = ToolGenerateRequest(name=name, description=description, examples=examples)

    from clients.factory_client import FactoryClient
    from config import get_config

    config = get_config()
    client = FactoryClient(config)

    try:
        result = await client.generate_tool(
            request.name, request.description, request.examples
        )
        return result
    finally:
        await client.close()


async def factory_execute(
    tool_name: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Executa tool registrada.

    Args:
        tool_name: Name of registered tool
        params: Parameters for execution

    Returns:
        Execution result with return_value

    Example:
        >>> result = await factory_execute("double", {"x": 5})
        >>> result["return_value"]
        10
    """
    from clients.factory_client import FactoryClient
    from config import get_config

    config = get_config()
    client = FactoryClient(config)

    try:
        result = await client.execute_tool(tool_name, params)
        return result
    finally:
        await client.close()


async def factory_list() -> List[Dict[str, Any]]:
    """
    Lista todas as tools disponíveis.

    Returns:
        List of ToolSpec dicts

    Example:
        >>> tools = await factory_list()
        >>> len(tools)
        15
    """
    from clients.factory_client import FactoryClient
    from config import get_config

    config = get_config()
    client = FactoryClient(config)

    try:
        result = await client.list_tools()
        return result
    finally:
        await client.close()


async def factory_delete(tool_name: str) -> bool:
    """
    Remove tool do registry.

    Args:
        tool_name: Name of tool to delete

    Returns:
        True if deleted successfully

    Example:
        >>> success = await factory_delete("old_tool")
        >>> success
        True
    """
    from clients.factory_client import FactoryClient
    from config import get_config

    config = get_config()
    client = FactoryClient(config)

    try:
        result = await client.delete_tool(tool_name)
        return result
    finally:
        await client.close()
