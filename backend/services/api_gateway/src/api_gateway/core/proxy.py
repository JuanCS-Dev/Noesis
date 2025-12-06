"""
API Gateway: Service Proxy
==========================

Core logic for routing and forwarding requests to backend microservices.
"""

import logging
from typing import Dict, Any

import httpx
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


class ServiceProxy:
    """
    Reverse proxy for backend services.

    Manages request forwarding and response handling.
    """

    def __init__(self) -> None:
        """Initialize the proxy with service mappings."""
        import os

        # Check if running in Docker or locally
        is_docker = os.environ.get("DOCKER_ENV", "false").lower() == "true"

        if is_docker:
            # Docker DNS names
            self.services: Dict[str, str] = {
                "maximus_core_service": "http://maximus_core:8000",
                "digital_thalamus_service": "http://digital_thalamus:8000",
                "episodic_memory": "http://episodic_memory:8000",
                "metacognitive_reflector": "http://metacognitive_reflector:8000",
                "prefrontal_cortex_service": "http://prefrontal_cortex:8000",
                "ethical_audit_service": "http://ethical_audit:8000",
            }
        else:
            # Local development - services on localhost with different ports
            self.services: Dict[str, str] = {
                "maximus_core_service": "http://localhost:8001",
                "digital_thalamus_service": "http://localhost:8002",
                "episodic_memory": "http://localhost:8003",
                "metacognitive_reflector": "http://localhost:8004",
                "prefrontal_cortex_service": "http://localhost:8005",
                "ethical_audit_service": "http://localhost:8006",
            }
        self.client = httpx.AsyncClient()
        logger.info("ServiceProxy initialized with %d services", len(self.services))

    async def forward_request(self, service_name: str, path: str, request: Request) -> Any:
        """
        Forward a request to a backend service.

        Args:
            service_name: Target service identifier
            path: URL path to forward
            request: Original FastAPI request

        Returns:
            JSON response from the target service

        Raises:
            HTTPException: If service not found or request fails
        """
        base_url = self.services.get(service_name)
        if not base_url:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

        target_url = f"{base_url}/{path}"

        try:
            # Extract body if present
            body = await request.body()

            # Forward request
            response = await self.client.request(
                method=request.method,
                url=target_url,
                headers=request.headers,
                content=body,
                params=request.query_params
            )

            # Return JSON response
            # Note: For a full gateway, we'd handle other content types and streaming
            return response.json()

        except httpx.RequestError as e:
            logger.error("Proxy request failed: %s", e)
            raise HTTPException(status_code=502, detail="Upstream service unavailable") from e
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Proxy error: %s", e)
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def shutdown(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
