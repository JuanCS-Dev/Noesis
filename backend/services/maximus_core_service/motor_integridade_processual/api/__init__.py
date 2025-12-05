"""
Motor de Integridade Processual (MIP) API Package.

FastAPI endpoints for ethical evaluation of action plans.

Author: Juan Carlos de Souza
Date: 2025-10-06
"""

from __future__ import annotations

from .app import app, create_mip_app
from .models import (
    ABTestMetricsResponse,
    ABTestResult,
    EvaluationRequest,
    EvaluationResponse,
    FrameworkInfo,
    HealthResponse,
    MetricsResponse,
    PrecedentFeedbackRequest,
    PrecedentMetricsResponse,
    PrecedentResponse,
)

__all__ = [
    # App
    "app",
    "create_mip_app",
    # Request models
    "EvaluationRequest",
    "PrecedentFeedbackRequest",
    # Response models
    "ABTestMetricsResponse",
    "ABTestResult",
    "EvaluationResponse",
    "FrameworkInfo",
    "HealthResponse",
    "MetricsResponse",
    "PrecedentMetricsResponse",
    "PrecedentResponse",
]
