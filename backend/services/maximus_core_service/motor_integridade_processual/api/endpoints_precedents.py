"""
Precedent Endpoints.

CRUD operations for precedent database.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from .models import (
    PrecedentFeedbackRequest,
    PrecedentMetricsResponse,
    PrecedentResponse,
)
from .state import (
    cbr_engine,
    cbr_precedents_used_count,
    cbr_shortcut_count,
    evaluation_count,
    precedent_db,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/precedents/feedback", status_code=status.HTTP_200_OK)
async def update_precedent_feedback(
    request: PrecedentFeedbackRequest,
) -> dict[str, str]:
    """Update precedent with outcome feedback."""
    if cbr_engine is None or precedent_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CBR Engine not available",
        )

    try:
        updated = await precedent_db.update_success(
            request.precedent_id, request.success_score
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Precedent {request.precedent_id} not found",
            )

        if request.outcome:
            precedent = await precedent_db.get_by_id(request.precedent_id)
            if precedent:
                precedent.outcome = request.outcome  # type: ignore
                await precedent_db.store(precedent)

        logger.info(
            f"Updated precedent #{request.precedent_id} "
            f"with success={request.success_score}"
        )

        return {
            "status": "success",
            "message": f"Precedent #{request.precedent_id} updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update precedent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update precedent: {str(e)}",
        )


@router.get("/precedents/{precedent_id}", response_model=PrecedentResponse)
async def get_precedent(precedent_id: int) -> PrecedentResponse:
    """Retrieve a specific precedent by ID."""
    if cbr_engine is None or precedent_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CBR Engine not available",
        )

    try:
        precedent = await precedent_db.get_by_id(precedent_id)

        if not precedent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Precedent {precedent_id} not found",
            )

        return PrecedentResponse(
            id=precedent.id,  # type: ignore
            situation=precedent.situation,  # type: ignore
            action_taken=precedent.action_taken,  # type: ignore
            rationale=precedent.rationale,  # type: ignore
            success=precedent.success,  # type: ignore
            created_at=precedent.created_at.isoformat(),  # type: ignore
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve precedent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve precedent: {str(e)}",
        )


@router.get("/precedents/metrics", response_model=PrecedentMetricsResponse)
async def get_precedent_metrics() -> PrecedentMetricsResponse:
    """Get metrics about precedents and CBR usage."""
    if cbr_engine is None or precedent_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CBR Engine not available",
        )

    try:
        all_precedents = await precedent_db.find_similar([0.0] * 384, limit=1000)

        total_precedents = len(all_precedents)

        success_scores = [p.success for p in all_precedents if p.success is not None]
        avg_success = (
            sum(success_scores) / len(success_scores) if success_scores else 0.0
        )

        high_confidence_count = sum(
            1
            for p in all_precedents
            if p.success is not None and p.success * 0.9 > 0.8
        )

        shortcut_rate = (
            (cbr_shortcut_count / evaluation_count * 100) if evaluation_count > 0 else 0.0
        )

        return PrecedentMetricsResponse(
            total_precedents=total_precedents,
            avg_success_score=float(avg_success),
            high_confidence_count=high_confidence_count,
            precedents_used_count=cbr_precedents_used_count,
            shortcut_rate=shortcut_rate,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get precedent metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get precedent metrics: {str(e)}",
        )
