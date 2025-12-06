"""
HCL Analyzer Service - API Routes
=================================

FastAPI routes for the service.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..core.analyzer import SystemAnalyzer
from ..models.analysis import AnalysisResult, SystemMetrics
from .dependencies import get_analyzer

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_metrics(
    metrics: SystemMetrics,
    analyzer: SystemAnalyzer = Depends(get_analyzer)
) -> AnalysisResult:
    """
    Analyze system metrics and return health assessment.
    
    Args:
        metrics: System metrics snapshot
        analyzer: Injected analyzer instance
        
    Returns:
        Analysis result
    """
    try:
        return await analyzer.analyze_metrics(metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
