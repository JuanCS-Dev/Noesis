"""
Base HTTP Client
================

Reusable HTTP client with retry logic, connection pooling, and timeouts.

Follows CODE_CONSTITUTION: Safety First, Consistency is King.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import MCPServerConfig


class BaseHTTPClient:
    """Base HTTP client with retry and pooling.

    Provides:
    - Connection pooling (persistent connections)
    - Automatic retries with exponential backoff
    - Timeout configuration
    - Proper resource cleanup

    Example:
        >>> client = BaseHTTPClient(config, "http://localhost:8000")
        >>> result = await client.post("/endpoint", {"key": "value"})
        >>> await client.close()
    """

    def __init__(
        self,
        config: MCPServerConfig,
        base_url: str,
        timeout: Optional[float] = None,
    ):
        """Initialize HTTP client.

        Args:
            config: Service configuration
            base_url: Base URL for all requests
            timeout: Override default timeout (optional)
        """
        self.config = config
        self.base_url = base_url
        self.timeout = timeout or config.http_timeout

        # Create client with connection pooling
        limits = httpx.Limits(
            max_connections=config.http_max_connections,
            max_keepalive_connections=config.http_max_keepalive,
        )

        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(self.timeout),
            limits=limits,
            http2=True,  # Enable HTTP/2 for better performance
        )

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """GET request with retry logic.

        Args:
            path: Request path (relative to base_url)
            params: Query parameters
            headers: Additional headers
            retry: Enable retry logic (default: True)

        Returns:
            Response JSON as dict

        Raises:
            httpx.HTTPStatusError: If response status >= 400
            httpx.TimeoutException: If request times out
        """
        if retry:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(
                    (httpx.TimeoutException, httpx.ConnectError)
                ),
                reraise=True,
            ):
                with attempt:
                    response = await self.client.get(
                        path, params=params, headers=headers
                    )
                    response.raise_for_status()
                    return response.json()
            # Unreachable: reraise=True ensures exception or return
            raise RuntimeError("Retry exhausted")  # pragma: no cover

        response = await self.client.get(path, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """POST request with retry logic.

        Args:
            path: Request path (relative to base_url)
            json: Request body as JSON
            headers: Additional headers
            retry: Enable retry logic (default: True)

        Returns:
            Response JSON as dict

        Raises:
            httpx.HTTPStatusError: If response status >= 400
            httpx.TimeoutException: If request times out
        """
        if retry:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(
                    (httpx.TimeoutException, httpx.ConnectError)
                ),
                reraise=True,
            ):
                with attempt:
                    response = await self.client.post(
                        path, json=json, headers=headers
                    )
                    response.raise_for_status()
                    return response.json()
            # Unreachable: reraise=True ensures exception or return
            raise RuntimeError("Retry exhausted")  # pragma: no cover

        response = await self.client.post(path, json=json, headers=headers)
        response.raise_for_status()
        return response.json()

    async def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = False,
    ) -> Dict[str, Any]:
        """DELETE request (typically no retry).

        Args:
            path: Request path (relative to base_url)
            headers: Additional headers
            retry: Enable retry logic (default: False)

        Returns:
            Response JSON as dict

        Raises:
            httpx.HTTPStatusError: If response status >= 400
            httpx.TimeoutException: If request times out
        """
        response = await self.client.delete(path, headers=headers)
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> bool:
        """Check if service is healthy.

        Returns:
            True if service responds with 200, False otherwise
        """
        try:
            response = await self.client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close HTTP client and cleanup connections.

        Should be called during application shutdown.
        """
        await self.client.aclose()

    async def __aenter__(self) -> BaseHTTPClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
