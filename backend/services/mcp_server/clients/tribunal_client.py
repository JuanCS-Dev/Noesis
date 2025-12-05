"""
Tribunal Service Client
=======================

Client for metacognitive_reflector (Tribunal) service.

Follows CODE_CONSTITUTION: Clarity Over Cleverness.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from clients.base_client import BaseHTTPClient
from config import MCPServerConfig


class TribunalClient:
    """Client for Tribunal (metacognitive_reflector) service.

    Provides methods to interact with the Tribunal of Judges.

    Example:
        >>> client = TribunalClient(config)
        >>> verdict = await client.evaluate(execution_log, context)
        >>> print(verdict["decision"])
        PASS
    """

    def __init__(self, config: MCPServerConfig):
        """Initialize Tribunal client.

        Args:
            config: Service configuration
        """
        self.config = config
        self.client = BaseHTTPClient(config, config.tribunal_url)

    async def evaluate(
        self, execution_log: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate execution in Tribunal.

        Args:
            execution_log: Execution log to evaluate
            context: Additional context (optional)

        Returns:
            Tribunal verdict with decision and scores

        Example:
            >>> verdict = await client.evaluate("task: foo\\nresult: bar")
            >>> verdict["decision"]  # PASS, REVIEW, FAIL, or CAPITAL
        """
        payload: Dict[str, Any] = {"execution_log": execution_log}
        if context:
            payload["context"] = context

        result = await self.client.post("/v1/evaluate", json=payload)
        return result

    async def get_health(self) -> Dict[str, Any]:
        """Get Tribunal health status.

        Returns:
            Health status of each judge + metrics
        """
        result = await self.client.get("/health")
        return result

    async def get_stats(self) -> Dict[str, Any]:
        """Get Tribunal statistics.

        Returns:
            Evaluation statistics
        """
        result = await self.client.get("/v1/stats")
        return result

    async def close(self) -> None:
        """Close client connections."""
        await self.client.close()
