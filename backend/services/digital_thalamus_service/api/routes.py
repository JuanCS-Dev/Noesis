"""
Digital Thalamus Service - API Routes
=====================================

FastAPI endpoints for API Gateway.
"""

from __future__ import annotations


from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from core.router import RequestRouter
from models.gateway import RouteConfig
from api.dependencies import get_router

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check() -> dict[str, str]:
    """
    Service health check.

    Returns:
        Basic health status
    """
    return {"status": "healthy", "service": "digital-thalamus-service"}


@router.get("/routes", response_model=Dict[str, RouteConfig])
async def get_routes(
    req_router: RequestRouter = Depends(get_router)
) -> Dict[str, RouteConfig]:
    """
    Get registered routes.

    Args:
        req_router: Request router instance

    Returns:
        Dictionary of registered routes
    """
    return req_router.routes


@router.get("/routes/{path:path}", response_model=RouteConfig)
async def find_route(
    path: str,
    req_router: RequestRouter = Depends(get_router)
) -> RouteConfig:
    """
    Find route for a given path.

    Args:
        path: Request path
        req_router: Request router instance

    Returns:
        Route configuration

    Raises:
        HTTPException: If no route found
    """
    route = await req_router.find_route(f"/{path}")
    if route is None:
        raise HTTPException(status_code=404, detail="No route found for path")
    return route
