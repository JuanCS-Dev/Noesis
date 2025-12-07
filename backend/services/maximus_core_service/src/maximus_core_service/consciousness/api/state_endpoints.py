"""State Endpoints - Consciousness state and metrics."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from maximus_core_service.consciousness.api_schemas import ConsciousnessStateResponse

from .helpers import APIState


def register_state_endpoints(
    router: APIRouter,
    consciousness_system: dict[str, Any],
    api_state: APIState,
) -> None:
    """Register state-related endpoints."""

    @router.get("/state", response_model=ConsciousnessStateResponse)
    async def get_consciousness_state() -> ConsciousnessStateResponse:
        """Get current complete consciousness state."""
        try:
            tig = consciousness_system.get("tig")
            esgt = consciousness_system.get("esgt")
            arousal = consciousness_system.get("arousal")

            if not all([tig, esgt, arousal]):
                raise HTTPException(
                    status_code=503, detail="Consciousness system not fully initialized"
                )

            tig_metrics_raw = (
                tig.get_metrics() if tig and hasattr(tig, "get_metrics") else {}
            )
            tig_metrics = (
                asdict(tig_metrics_raw)
                if hasattr(tig_metrics_raw, "__dataclass_fields__")
                else tig_metrics_raw
            )
            arousal_state = (
                arousal.get_current_arousal()
                if arousal and hasattr(arousal, "get_current_arousal")
                else None
            )

            return ConsciousnessStateResponse(
                timestamp=datetime.now().isoformat(),
                esgt_active=(
                    bool(esgt._running) if esgt and hasattr(esgt, "_running") else False
                ),
                arousal_level=arousal_state.arousal if arousal_state else 0.5,
                arousal_classification=(
                    arousal_state.level.value
                    if arousal_state and hasattr(arousal_state.level, "value")
                    else "UNKNOWN"
                ),
                tig_metrics=tig_metrics,
                recent_events_count=len(api_state.event_history),
                system_health="HEALTHY" if all([tig, esgt, arousal]) else "DEGRADED",
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving state: {str(e)}"
            ) from e

    @router.get("/arousal")
    async def get_arousal_state() -> dict[str, Any]:
        """Get current arousal state."""
        try:
            arousal = consciousness_system.get("arousal")
            if not arousal:
                raise HTTPException(
                    status_code=503, detail="Arousal controller not initialized"
                )
            arousal_state = arousal.get_current_arousal()
            if not arousal_state:
                return {"error": "No arousal state available"}
            return {
                "arousal": arousal_state.arousal,
                "level": (
                    arousal_state.level.value
                    if hasattr(arousal_state.level, "value")
                    else str(arousal_state.level)
                ),
                "baseline": arousal_state.baseline_arousal,
                "need_contribution": arousal_state.need_contribution,
                "temporal_contribution": arousal_state.temporal_contribution,
                "timestamp": datetime.now().isoformat(),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving arousal: {str(e)}"
            ) from e

    @router.get("/metrics")
    async def get_metrics() -> dict[str, Any]:
        """Get consciousness system metrics."""
        try:
            tig = consciousness_system.get("tig")
            esgt = consciousness_system.get("esgt")
            metrics: dict[str, Any] = {}
            if tig and hasattr(tig, "get_metrics"):
                metrics["tig"] = tig.get_metrics()
            if esgt and hasattr(esgt, "get_metrics"):
                metrics["esgt"] = esgt.get_metrics()
            metrics["events_count"] = len(api_state.event_history)
            metrics["timestamp"] = datetime.now().isoformat()
            return metrics
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving metrics: {str(e)}"
            ) from e
