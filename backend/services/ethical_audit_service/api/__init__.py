"""Ethical Audit Service - API Package.

This package provides the modular FastAPI application for the
Ethical Audit Service with router-based endpoint organization.

The original monolithic api.py (2770 lines) has been decomposed into:
- app.py: FastAPI application setup and lifecycle
- state.py: Shared application state management
- routers/: Domain-specific endpoint modules
"""

from __future__ import annotations

from .app import app, create_app

__all__ = ["app", "create_app"]
