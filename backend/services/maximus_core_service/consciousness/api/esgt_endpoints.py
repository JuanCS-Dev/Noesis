"""ESGT Endpoints - Event triggering and retrieval."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from consciousness.api_schemas import ESGTEventResponse, SalienceInput, ArousalAdjustment

from .helpers import APIState


def register_esgt_endpoints(
    router: APIRouter,
    consciousness_system: dict[str, Any],
    api_state: APIState,
) -> None:
    """Register ESGT-related endpoints."""

    @router.get("/esgt/events", response_model=list[ESGTEventResponse])
    async def get_esgt_events(limit: int = 20) -> list[ESGTEventResponse]:
        """Get recent ESGT events."""
        if limit < 1 or limit > api_state.MAX_HISTORY:
            raise HTTPException(
                status_code=400,
                detail=f"Limit must be between 1 and {api_state.MAX_HISTORY}",
            )
        events = api_state.event_history[-limit:]
        return [
            ESGTEventResponse(
                event_id=evt.get("event_id", "unknown"),
                timestamp=evt.get("timestamp", datetime.now().isoformat()),
                success=evt.get("success", False),
                salience={
                    "novelty": evt.get("salience", {}).get("novelty", 0),
                    "relevance": evt.get("salience", {}).get("relevance", 0),
                    "urgency": evt.get("salience", {}).get("urgency", 0),
                },
                coherence=evt.get("coherence_achieved"),
                duration_ms=evt.get("duration_ms"),
                nodes_participating=len(evt.get("nodes_participating", [])),
                reason=evt.get("reason"),
            )
            for evt in events
        ]

    @router.post("/esgt/trigger")
    async def trigger_esgt(salience: SalienceInput) -> dict[str, Any]:
        """Manually trigger ESGT ignition."""
        try:
            esgt = consciousness_system.get("esgt")
            if not esgt:
                raise HTTPException(
                    status_code=503, detail="ESGT coordinator not initialized"
                )
            from consciousness.esgt.coordinator import SalienceScore

            salience_score = SalienceScore(
                novelty=salience.novelty,
                relevance=salience.relevance,
                urgency=salience.urgency,
            )
            event = await esgt.initiate_esgt(salience_score, salience.context)
            api_state.add_event_to_history(event)
            await api_state.broadcast_to_consumers(
                {
                    "type": "esgt_event",
                    "event": (
                        asdict(event)
                        if hasattr(event, "__dataclass_fields__")
                        else dict(event)
                    ),
                }
            )
            return {
                "success": event.success,
                "event_id": event.event_id,
                "coherence": event.achieved_coherence,
                "duration_ms": event.time_to_sync_ms,
                "reason": getattr(event, "reason", None),
                "timestamp": datetime.now().isoformat(),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error triggering ESGT: {str(e)}"
            ) from e

    @router.post("/arousal/adjust")
    async def adjust_arousal(adjustment: ArousalAdjustment) -> dict[str, Any]:
        """Adjust arousal level."""
        try:
            arousal = consciousness_system.get("arousal")
            if not arousal:
                raise HTTPException(
                    status_code=503, detail="Arousal controller not initialized"
                )
            arousal.request_modulation(
                source=adjustment.source,
                delta=adjustment.delta,
                duration_seconds=adjustment.duration_seconds,
            )
            await asyncio.sleep(0.1)
            new_state = arousal.get_current_arousal()
            await api_state.broadcast_to_consumers(
                {
                    "type": "arousal_change",
                    "arousal": new_state.arousal,
                    "level": (
                        new_state.level.value
                        if hasattr(new_state.level, "value")
                        else str(new_state.level)
                    ),
                }
            )
            return {
                "arousal": new_state.arousal,
                "level": (
                    new_state.level.value
                    if hasattr(new_state.level, "value")
                    else str(new_state.level)
                ),
                "delta_applied": adjustment.delta,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error adjusting arousal: {str(e)}"
            ) from e
