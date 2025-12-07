"""
Maximus Core Service - Main Application
=======================================

Entry point for the Maximus Core Service.

PROJETO SINGULARIDADE (06/Dez/2025):
Integração do ConsciousnessSystem com o pipeline de comunicação.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from maximus_core_service.api.dependencies import initialize_service
from maximus_core_service.api.routes import router as api_router
from maximus_core_service.consciousness.exocortex.api.exocortex_router import (
    router as exocortex_router,
    set_consciousness_system,  # SINGULARIDADE
)
from maximus_core_service.consciousness.api import create_consciousness_api
from maximus_core_service.consciousness.api.streaming import set_maximus_consciousness_system
from maximus_core_service.consciousness.exocortex.factory import ExocortexFactory
from maximus_core_service.config import get_settings

# SINGULARIDADE: Import ConsciousnessSystem
from maximus_core_service.consciousness.system import ConsciousnessSystem

logger = logging.getLogger(__name__)
settings = get_settings()

# SINGULARIDADE: Global reference to ConsciousnessSystem
_consciousness_system: ConsciousnessSystem | None = None


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan.

    Args:
        _: FastAPI application instance (unused)

    Yields:
        None during application lifetime
    """
    global _consciousness_system

    # Startup
    initialize_service()
    ExocortexFactory.initialize(data_dir=str(settings.base_path / ".data"))

    # SINGULARIDADE: Initialize and start ConsciousnessSystem
    logger.info("[SINGULARIDADE] Initializing ConsciousnessSystem...")
    _consciousness_system = ConsciousnessSystem()
    await _consciousness_system.start()

    # Register with Exocortex router for /journal endpoint
    set_consciousness_system(_consciousness_system)
    logger.info("[SINGULARIDADE] ConsciousnessSystem integrated with Exocortex")

    # MAXIMUS: Register with streaming endpoint for real-time SSE
    set_maximus_consciousness_system(_consciousness_system)
    logger.info("[MAXIMUS] ConsciousnessSystem integrated with Streaming API")

    # FIX: Populate consciousness_system dict for REST API endpoints
    from maximus_core_service.consciousness.api import set_consciousness_components
    set_consciousness_components(_consciousness_system)
    logger.info("[FIX] ConsciousnessSystem components registered with REST API")

    yield

    # Shutdown
    if _consciousness_system:
        logger.info("[SINGULARIDADE] Stopping ConsciousnessSystem...")
        await _consciousness_system.stop()


app = FastAPI(
    title=settings.service.name,  # pylint: disable=no-member
    description="Maximus Core Service - System Coordination",
    version="3.0.0",
    lifespan=lifespan
)

# TITANIUM PIPELINE: CORS para SSE streaming cross-origin
# Permite conexões do frontend (localhost:3000/3001) para o backend (localhost:8001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir para domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router, prefix="/v1")
app.include_router(exocortex_router, prefix="/v1")

# MAXIMUS: Consciousness API with SSE streaming (will be populated on startup)
# Note: Router created with empty dict, system set via setter during lifespan
_consciousness_api_router = create_consciousness_api({})
app.include_router(_consciousness_api_router)


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns:
        Service information
    """
    return {
        "message": "Maximus Core Service Operational",
        "service": settings.service.name  # pylint: disable=no-member
    }
