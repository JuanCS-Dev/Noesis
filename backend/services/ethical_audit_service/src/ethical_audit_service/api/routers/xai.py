"""XAI (Explainability) Endpoints."""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ethical_audit_service.auth import TokenData, require_auditor_or_admin, require_soc_or_admin

from ..state import get_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["xai"])

# Add XAI module path
XAI_PATH = "/home/juan/vertice-dev/backend/services/maximus_core_service"


def _ensure_xai_path() -> None:
    """Ensure XAI module path is available."""
    if XAI_PATH not in sys.path:
        sys.path.append(XAI_PATH)


@router.post("/explain")
async def explain_decision(
    request: Request,
    explanation_request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Generate explanation for a model's prediction or decision."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("30/minute")(request)

    try:
        _ensure_xai_path()

        from xai.base import DetailLevel, ExplanationType
        from xai.engine import DummyModel, get_global_engine

        decision_id = explanation_request.get("decision_id")
        explanation_type = explanation_request.get("explanation_type", "lime")
        detail_level = explanation_request.get("detail_level", "detailed")
        instance = explanation_request.get("instance", {})
        prediction = explanation_request.get("prediction")

        if not instance:
            raise HTTPException(status_code=400, detail="instance is required")
        if prediction is None:
            raise HTTPException(status_code=400, detail="prediction is required")

        try:
            exp_type = ExplanationType(explanation_type)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail="Invalid explanation_type. Must be: lime, shap, counterfactual",
            ) from e

        try:
            det_level = DetailLevel(detail_level)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail="Invalid detail_level. Must be: summary, detailed, technical",
            ) from e

        engine = get_global_engine()
        model = DummyModel()

        if decision_id:
            instance["decision_id"] = decision_id

        start_time = time.time()

        explanation = await engine.explain(
            model=model,
            instance=instance,
            prediction=prediction,
            explanation_type=exp_type,
            detail_level=det_level,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "XAI explanation generated: %s, latency=%dms, confidence=%.2f",
            explanation_type,
            latency_ms,
            explanation.confidence,
        )

        return {
            "success": True,
            "explanation_id": explanation.explanation_id,
            "decision_id": explanation.decision_id,
            "explanation_type": explanation.explanation_type.value,
            "detail_level": explanation.detail_level.value,
            "summary": explanation.summary,
            "top_features": [
                {
                    "feature_name": f.feature_name,
                    "importance": f.importance,
                    "value": str(f.value),
                    "description": f.description,
                    "contribution": f.contribution,
                }
                for f in explanation.top_features
            ],
            "confidence": explanation.confidence,
            "counterfactual": explanation.counterfactual,
            "visualization_data": explanation.visualization_data,
            "model_type": explanation.model_type,
            "latency_ms": explanation.latency_ms,
            "metadata": explanation.metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("XAI explanation failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate explanation: {e!s}"
        ) from e


@router.get("/xai/stats")
async def get_xai_stats(
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get XAI engine statistics."""
    try:
        _ensure_xai_path()

        from xai.engine import get_global_engine

        engine = get_global_engine()
        stats = engine.get_statistics()

        return {"success": True, "stats": stats}

    except Exception as e:
        logger.exception("Failed to get XAI stats: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get XAI statistics: {e!s}"
        ) from e


@router.get("/xai/top-features")
async def get_xai_top_features(
    n: int = Query(default=10, ge=1, le=100, description="Number of top features"),
    hours: int | None = Query(default=None, ge=1, le=720, description="Time window"),
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get top N most important features across all explanations."""
    try:
        _ensure_xai_path()

        from xai.engine import get_global_engine

        engine = get_global_engine()
        top_features = engine.get_top_features(n=n, time_window_hours=hours)

        return {"success": True, "top_features": top_features, "time_window_hours": hours}

    except Exception as e:
        logger.exception("Failed to get top features: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get top features: {e!s}"
        ) from e


@router.get("/xai/drift")
async def get_xai_drift(
    feature_name: str | None = Query(default=None, description="Specific feature"),
    window_size: int = Query(default=100, ge=10, le=1000, description="Window size"),
    threshold: float = Query(default=0.2, ge=0.0, le=1.0, description="Drift threshold"),
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Detect feature importance drift."""
    try:
        _ensure_xai_path()

        from xai.engine import get_global_engine

        engine = get_global_engine()
        drift_result = engine.detect_drift(
            feature_name=feature_name, window_size=window_size, threshold=threshold
        )

        return {"success": True, "drift_result": drift_result}

    except Exception as e:
        logger.exception("Failed to detect drift: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to detect drift: {e!s}") from e


@router.get("/xai/health")
async def xai_health_check() -> dict[str, Any]:
    """XAI engine health check."""
    try:
        _ensure_xai_path()

        from xai.engine import get_global_engine

        engine = get_global_engine()
        health = await engine.health_check()

        return health

    except Exception as e:
        logger.exception("XAI health check failed: %s", e)
        return {"status": "unhealthy", "error": str(e)}
