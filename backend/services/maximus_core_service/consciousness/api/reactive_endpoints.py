"""Reactive Fabric Endpoints - Metrics, events, and orchestration."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException


def register_reactive_endpoints(
    router: APIRouter,
    consciousness_system: dict[str, Any],
) -> None:
    """Register reactive fabric endpoints."""

    @router.get("/reactive-fabric/metrics")
    async def get_reactive_fabric_metrics() -> dict[str, Any]:
        """Get latest Reactive Fabric metrics."""
        try:
            system = consciousness_system.get("system")
            if not system or not hasattr(system, "orchestrator"):
                raise HTTPException(
                    status_code=503,
                    detail="Reactive Fabric orchestrator not initialized",
                )
            metrics = await system.orchestrator.metrics_collector.collect()
            return {
                "timestamp": metrics.timestamp,
                "tig": {
                    "node_count": metrics.tig_node_count,
                    "edge_count": metrics.tig_edge_count,
                    "avg_latency_us": metrics.tig_avg_latency_us,
                    "coherence": metrics.tig_coherence,
                },
                "esgt": {
                    "event_count": metrics.esgt_event_count,
                    "success_rate": metrics.esgt_success_rate,
                    "frequency_hz": metrics.esgt_frequency_hz,
                    "avg_coherence": metrics.esgt_avg_coherence,
                },
                "arousal": {
                    "level": metrics.arousal_level,
                    "classification": metrics.arousal_classification,
                    "stress": metrics.arousal_stress,
                    "need": metrics.arousal_need,
                },
                "pfc": {
                    "signals_processed": metrics.pfc_signals_processed,
                    "actions_generated": metrics.pfc_actions_generated,
                    "approval_rate": metrics.pfc_approval_rate,
                },
                "tom": {
                    "total_agents": metrics.tom_total_agents,
                    "total_beliefs": metrics.tom_total_beliefs,
                    "cache_hit_rate": metrics.tom_cache_hit_rate,
                },
                "safety": {
                    "violations": metrics.safety_violations,
                    "kill_switch_active": metrics.kill_switch_active,
                },
                "health_score": metrics.health_score,
                "collection_duration_ms": metrics.collection_duration_ms,
                "errors": metrics.errors,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving reactive fabric metrics: {str(e)}",
            ) from e

    @router.get("/reactive-fabric/events")
    async def get_reactive_fabric_events(limit: int = 20) -> dict[str, Any]:
        """Get recent Reactive Fabric events."""
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400, detail="Limit must be between 1 and 100"
            )
        try:
            system = consciousness_system.get("system")
            if not system or not hasattr(system, "orchestrator"):
                raise HTTPException(
                    status_code=503,
                    detail="Reactive Fabric orchestrator not initialized",
                )
            events = system.orchestrator.event_collector.get_recent_events(limit=limit)
            return {
                "events": [
                    {
                        "event_id": e.event_id,
                        "type": e.event_type.value,
                        "severity": e.severity.value,
                        "timestamp": e.timestamp,
                        "source": e.source,
                        "data": e.data,
                        "salience": {
                            "novelty": e.novelty,
                            "relevance": e.relevance,
                            "urgency": e.urgency,
                        },
                        "processed": e.processed,
                        "esgt_triggered": e.esgt_triggered,
                    }
                    for e in events
                ],
                "total_count": len(events),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving reactive fabric events: {str(e)}",
            ) from e

    @router.get("/reactive-fabric/orchestration")
    async def get_reactive_fabric_orchestration() -> dict[str, Any]:
        """Get Reactive Fabric orchestration status."""
        try:
            system = consciousness_system.get("system")
            if not system or not hasattr(system, "orchestrator"):
                raise HTTPException(
                    status_code=503,
                    detail="Reactive Fabric orchestrator not initialized",
                )
            orchestrator = system.orchestrator
            stats = orchestrator.get_orchestration_stats()
            recent_decisions = orchestrator.get_recent_decisions(limit=10)
            return {
                "status": {
                    "running": orchestrator._running,
                    "collection_interval_ms": orchestrator.collection_interval_ms,
                    "salience_threshold": orchestrator.salience_threshold,
                },
                "statistics": stats,
                "recent_decisions": [
                    {
                        "timestamp": d.timestamp,
                        "should_trigger": d.should_trigger_esgt,
                        "salience": {
                            "novelty": d.salience.novelty,
                            "relevance": d.salience.relevance,
                            "urgency": d.salience.urgency,
                            "total": d.salience.compute_total(),
                        },
                        "reason": d.reason,
                        "confidence": d.confidence,
                        "triggering_events_count": len(d.triggering_events),
                        "health_score": d.metrics_snapshot.health_score,
                    }
                    for d in recent_decisions
                ],
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving orchestration status: {str(e)}",
            ) from e
