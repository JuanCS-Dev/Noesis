"""
HCL Planner Service - Entry Point
=================================

FastAPI application for the HCL Planner Service.
Exposes endpoints for generating infrastructure plans.
"""

from __future__ import annotations

import os
import asyncio
from typing import Dict, Any

from fastapi import FastAPI, Depends
from fastapi.responses import PlainTextResponse

from config import get_settings
from core.planner import AgenticPlanner
from api.dependencies import get_planner, initialize_service

# Initialize settings
settings = get_settings()

app = FastAPI(
    title=settings.service.name,  # pylint: disable=no-member
    description="HCL Planner Service (Agentic)",
    version="2.0.0"
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize service on startup."""
    initialize_service()


@app.get("/health")
async def health(
    planner: AgenticPlanner = Depends(get_planner)
) -> Dict[str, Any]:
    """
    Service health check.

    Returns:
        Health status dictionary.
    """
    planner_status = await planner.get_status()
    return {
        "status": "healthy",
        "service": settings.service.name,  # pylint: disable=no-member
        "planner": planner_status
    }


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    """
    Prometheus metrics.

    Returns:
        PlainTextResponse with metrics.
    """
    return PlainTextResponse("# HCL Planner Metrics\nplanner_active 1\n")


@app.post("/plan")
async def generate_plan(
    current_state: Dict[str, Any],
    analysis_result: Dict[str, Any],
    operational_goals: Dict[str, Any],
    planner: AgenticPlanner = Depends(get_planner)
) -> Dict[str, Any]:
    """
    Generate a new infrastructure plan.

    Args:
        current_state: Current system metrics
        analysis_result: Insights from HCL Analyzer
        operational_goals: Desired outcomes
        planner: Injected AgenticPlanner instance

    Returns:
        Generated plan with actions.
    """
    actions = await planner.recommend_actions(
        current_state=current_state,
        analysis_result=analysis_result,
        operational_goals=operational_goals
    )

    return {
        "plan_id": f"plan-{os.urandom(4).hex()}",
        "timestamp": asyncio.get_event_loop().time(),
        "actions": actions
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "HCL Planner Service (Agentic) Operational"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
