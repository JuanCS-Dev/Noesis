"""
HCL Monitor Service - API Routes
================================

FastAPI endpoints for system monitoring.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..core.collector import SystemMetricsCollector
from ..models.metrics import SystemMetrics
from .dependencies import get_collector

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check() -> dict[str, str]:
    """
    Service health check.
    """
    return {"status": "healthy", "service": "hcl-monitor-service"}


@router.get("/metrics", response_model=SystemMetrics)
async def get_latest_metrics(
    collector: SystemMetricsCollector = Depends(get_collector)
) -> SystemMetrics:
    """
    Get the most recent system metrics.
    """
    metrics = collector.get_latest_metrics()
    if not metrics:
        raise HTTPException(status_code=503, detail="Metrics not yet available")
    return metrics


@router.get("/metrics/history", response_model=List[SystemMetrics])
async def get_metrics_history(
    limit: int = 10,
    collector: SystemMetricsCollector = Depends(get_collector)
) -> List[SystemMetrics]:
    """
    Get historical system metrics.
    """
    return collector.get_metrics_history(limit)
