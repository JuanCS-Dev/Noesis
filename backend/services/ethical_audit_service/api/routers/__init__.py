"""Ethical Audit Service - API Routers Package."""

from __future__ import annotations

from .audit import router as audit_router
from .compliance_logs import router as compliance_logs_router
from .fairness import router as fairness_router
from .federated import router as federated_router
from .health import router as health_router
from .hitl import router as hitl_router
from .metrics import router as metrics_router
from .privacy import router as privacy_router
from .xai import router as xai_router
from .certification import router as certification_router

__all__ = [
    "audit_router",
    "compliance_logs_router",
    "fairness_router",
    "federated_router",
    "health_router",
    "hitl_router",
    "metrics_router",
    "privacy_router",
    "xai_router",
    "certification_router",
]
