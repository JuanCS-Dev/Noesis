"""Metrics & Analytics Endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.services.ethical_audit_service.auth import TokenData, require_auditor_or_admin
from backend.services.ethical_audit_service.models import (
    EthicalMetrics,
    FrameworkPerformance,
)

from ..state import get_db, get_limiter

router = APIRouter(prefix="/audit", tags=["metrics"])


@router.get("/metrics", response_model=EthicalMetrics)
async def get_metrics() -> EthicalMetrics:
    """Get real-time ethical KPIs and metrics."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        metrics = await db.get_metrics()
        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {e!s}") from e


@router.get("/metrics/frameworks", response_model=list[FrameworkPerformance])
async def get_framework_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back"),
) -> list[FrameworkPerformance]:
    """Get performance metrics for each ethical framework."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        performance = await db.get_framework_performance(hours=hours)
        return performance

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get framework metrics: {e!s}"
        ) from e


@router.get("/analytics/timeline")
async def get_decision_timeline(
    hours: int = Query(default=24, ge=1, le=720, description="Hours to analyze"),
    bucket_minutes: int = Query(
        default=60, ge=5, le=1440, description="Time bucket size in minutes"
    ),
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get time-series analytics of ethical decisions."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                time_bucket($1::text || ' minutes', timestamp) AS bucket,
                COUNT(*) as total_decisions,
                AVG(final_confidence) as avg_confidence,
                AVG(total_latency_ms) as avg_latency,
                SUM(CASE WHEN final_decision = 'APPROVED' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN final_decision = 'REJECTED' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN final_decision = 'ESCALATED_HITL' THEN 1 ELSE 0 END) as escalated
            FROM ethical_decisions
            WHERE timestamp >= NOW() - ($2::text || ' hours')::INTERVAL
            GROUP BY bucket
            ORDER BY bucket ASC
        """,
            str(bucket_minutes),
            str(hours),
        )

    timeline = [
        {
            "timestamp": row["bucket"].isoformat(),
            "total_decisions": row["total_decisions"],
            "avg_confidence": float(row["avg_confidence"] or 0.0),
            "avg_latency_ms": float(row["avg_latency"] or 0.0),
            "approved": row["approved"],
            "rejected": row["rejected"],
            "escalated": row["escalated"],
        }
        for row in rows
    ]

    return {
        "hours_analyzed": hours,
        "bucket_minutes": bucket_minutes,
        "data_points": len(timeline),
        "timeline": timeline,
    }


@router.get("/analytics/risk-heatmap")
async def get_risk_heatmap(
    hours: int = Query(default=24, ge=1, le=720, description="Hours to analyze"),
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get risk heatmap showing decision type vs risk level distribution."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                decision_type,
                risk_level,
                COUNT(*) as count,
                AVG(final_confidence) as avg_confidence
            FROM ethical_decisions
            WHERE timestamp >= NOW() - ($1::text || ' hours')::INTERVAL
            GROUP BY decision_type, risk_level
            ORDER BY decision_type, risk_level
        """,
            str(hours),
        )

    heatmap = [
        {
            "decision_type": row["decision_type"],
            "risk_level": row["risk_level"],
            "count": row["count"],
            "avg_confidence": float(row["avg_confidence"] or 0.0),
        }
        for row in rows
    ]

    return {"hours_analyzed": hours, "heatmap": heatmap}
