"""Differential Privacy Endpoints."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ethical_audit_service.auth import TokenData, require_auditor_or_admin, require_soc_or_admin

from ..state import get_app_state_value

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/privacy", tags=["privacy"])

PRIVACY_PATH = "/home/juan/vertice-dev/backend/services/maximus_core_service"


def _ensure_privacy_path() -> None:
    """Ensure privacy module path is available."""
    if PRIVACY_PATH not in sys.path:
        sys.path.append(PRIVACY_PATH)


@router.post("/dp-query")
async def execute_dp_query(
    request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Execute a differentially private query."""
    try:
        _ensure_privacy_path()

        import pandas as pd
        from privacy import DPAggregator

        query_type = request.get("query_type")
        data = request.get("data")
        epsilon = request.get("epsilon", 1.0)
        delta = request.get("delta", 1e-5)

        if not query_type:
            raise HTTPException(status_code=400, detail="query_type required")
        if not data:
            raise HTTPException(status_code=400, detail="data required")

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise HTTPException(status_code=400, detail="Invalid data format")

        aggregator = DPAggregator(epsilon=epsilon, delta=delta)

        if query_type == "count":
            result = aggregator.count(df)
        elif query_type == "count_by_group":
            group_col = request.get("group_column")
            if not group_col:
                raise HTTPException(
                    status_code=400, detail="group_column required for count_by_group"
                )
            result = aggregator.count_by_group(df, group_column=group_col)
        elif query_type == "sum":
            value_col = request.get("value_column")
            value_range = request.get("value_range", 1.0)
            if not value_col:
                raise HTTPException(status_code=400, detail="value_column required for sum")
            result = aggregator.sum(df, value_column=value_col, value_range=value_range)
        elif query_type == "mean":
            value_col = request.get("value_column")
            value_range = request.get("value_range", 1.0)
            if not value_col:
                raise HTTPException(status_code=400, detail="value_column required for mean")
            result = aggregator.mean(df, value_column=value_col, value_range=value_range)
        elif query_type == "histogram":
            value_col = request.get("value_column")
            bins = request.get("bins", 10)
            result = aggregator.histogram(df, value_column=value_col, bins=bins)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown query type: {query_type}")

        logger.info(
            "DP query executed: type=%s, epsilon=%.2f, delta=%.6e, user=%s",
            query_type,
            result.epsilon_used,
            result.delta_used,
            current_user.username,
        )

        return {
            "query_type": query_type,
            "result": result.to_dict(),
            "privacy_guarantee": {
                "epsilon": result.epsilon_used,
                "delta": result.delta_used,
                "mechanism": result.mechanism,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("DP query failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Query failed: {e!s}") from e


@router.get("/budget")
async def get_privacy_budget(
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get global privacy budget status."""
    try:
        budget = get_app_state_value("privacy_budget")
        if not budget:
            return {"status": "not_configured", "message": "No global privacy budget configured"}

        stats = budget.get_statistics()

        return {"status": "active", "budget": stats}

    except Exception as e:
        logger.exception("Failed to get privacy budget: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get budget: {e!s}") from e


@router.get("/stats")
async def get_privacy_stats(
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get differential privacy statistics."""
    try:
        stats = {
            "budget_configured": get_app_state_value("privacy_budget") is not None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        budget = get_app_state_value("privacy_budget")
        if budget:
            budget_stats = budget.get_statistics()

            stats.update(
                {
                    "total_queries": budget_stats["queries_executed"],
                    "epsilon_used": budget_stats["used_epsilon"],
                    "delta_used": budget_stats["used_delta"],
                    "epsilon_remaining": budget_stats["remaining_epsilon"],
                    "delta_remaining": budget_stats["remaining_delta"],
                    "privacy_level": budget_stats["privacy_level"],
                    "budget_exhausted": budget_stats["budget_exhausted"],
                }
            )

        return stats

    except Exception as e:
        logger.exception("Failed to get privacy stats: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {e!s}"
        ) from e


@router.get("/health")
async def privacy_health_check() -> dict[str, Any]:
    """Differential privacy module health check."""
    try:
        _ensure_privacy_path()

        from privacy import DPAggregator
        from privacy.base import PrivacyBudget, PrivacyParameters

        DPAggregator(epsilon=1.0, delta=1e-5)
        PrivacyBudget(total_epsilon=10.0, total_delta=1e-4)
        PrivacyParameters(epsilon=1.0, delta=1e-5, sensitivity=1.0)

        budget_configured = get_app_state_value("privacy_budget") is not None

        return {
            "status": "healthy",
            "components": {
                "dp_aggregator": "ok",
                "laplace_mechanism": "ok",
                "gaussian_mechanism": "ok",
                "privacy_budget": "ok",
                "global_budget": "configured" if budget_configured else "not_configured",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Privacy health check failed: %s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
