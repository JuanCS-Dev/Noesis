"""
API Gateway: API Routes
=======================

FastAPI application for the API Gateway.
Routes external requests to internal microservices.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.proxy import ServiceProxy


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="Maximus 2.0 API Gateway",
    description="Unified entry point for all Maximus services",
    version="1.0.0"
)


# Global state
proxy: ServiceProxy = ServiceProxy()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup resources on shutdown."""
    await proxy.shutdown()


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Service health check.

    Returns:
        Status dictionary.
    """
    return {
        "status": "healthy",
        "service": "api_gateway",
        "timestamp": datetime.now().isoformat()
    }


@app.api_route("/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_proxy(service_name: str, path: str, request: Request) -> Any:
    """
    Forward requests to backend services.

    Args:
        service_name: Name of the target service
        path: Path to forward
        request: The original request

    Returns:
        Response from the backend service
    """
    return await proxy.forward_request(service_name, path, request)


@app.exception_handler(Exception)
async def global_exception_handler(_: Any, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error("Gateway error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Gateway Error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
