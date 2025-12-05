"""Federated Learning Endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.services.ethical_audit_service.auth import TokenData, require_auditor_or_admin, require_soc_or_admin

from ..state import get_app_state_value, set_app_state_value

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fl", tags=["federated-learning"])


def _get_fl_coordinators() -> dict[str, Any]:
    """Get FL coordinators dictionary."""
    coordinators = get_app_state_value("fl_coordinators")
    if coordinators is None:
        coordinators = {}
        set_app_state_value("fl_coordinators", coordinators)
    return coordinators


@router.post("/coordinator/start-round")
async def fl_start_round(
    request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Start a new federated learning training round."""
    try:
        from federated_learning import (
            AggregationStrategy,
            CoordinatorConfig,
            FLConfig,
            FLCoordinator,
            ModelType,
        )
        from federated_learning.model_adapters import create_model_adapter

        model_type_str = request.get("model_type", "threat_classifier")
        model_type = ModelType(model_type_str)

        agg_strategy_str = request.get("aggregation_strategy", "fedavg")
        agg_strategy = AggregationStrategy(agg_strategy_str)

        fl_config = FLConfig(
            model_type=model_type,
            aggregation_strategy=agg_strategy,
            min_clients=request.get("min_clients", 2),
            max_clients=request.get("max_clients", 10),
            local_epochs=request.get("local_epochs", 5),
            local_batch_size=request.get("local_batch_size", 32),
            learning_rate=request.get("learning_rate", 0.001),
            use_differential_privacy=request.get("use_differential_privacy", False),
            dp_epsilon=request.get("dp_epsilon", 8.0),
            dp_delta=request.get("dp_delta", 1e-5),
        )

        coordinator_config = CoordinatorConfig(fl_config=fl_config)
        coordinator = FLCoordinator(coordinator_config)

        model_adapter = create_model_adapter(model_type)
        coordinator.set_global_model(model_adapter.get_weights())

        coordinators = _get_fl_coordinators()
        coordinators[model_type.value] = coordinator

        round_obj = coordinator.start_round()

        logger.info(
            "FL round %d started by %s (%s, %s)",
            round_obj.round_id,
            current_user.user_id,
            model_type.value,
            agg_strategy.value,
        )

        return {
            "round_id": round_obj.round_id,
            "status": round_obj.status.value,
            "selected_clients": round_obj.selected_clients,
            "global_model_version": round_obj.global_model_version,
            "model_type": model_type.value,
            "aggregation_strategy": agg_strategy.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("FL start round failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/coordinator/submit-update")
async def fl_submit_update(
    request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Submit a model update from FL client."""
    try:
        from federated_learning import ModelUpdate
        from federated_learning.communication import FLCommunicationChannel

        model_type_str = request.get("model_type", "threat_classifier")

        coordinators = _get_fl_coordinators()
        if not coordinators:
            raise HTTPException(status_code=404, detail="No FL coordinators active")

        coordinator = coordinators.get(model_type_str)
        if not coordinator:
            raise HTTPException(
                status_code=404, detail=f"No coordinator for model type: {model_type_str}"
            )

        channel = FLCommunicationChannel()
        serialized_weights = request.get("weights", {})
        weights = channel.deserialize_weights(serialized_weights)

        update = ModelUpdate(
            client_id=request.get("client_id"),
            round_id=request.get("round_id"),
            weights=weights,
            num_samples=request.get("num_samples", 0),
            metrics=request.get("metrics", {}),
            differential_privacy_applied=request.get("differential_privacy_applied", False),
            epsilon_used=request.get("epsilon_used", 0.0),
        )

        coordinator.receive_update(update)

        round_status = coordinator.get_round_status()

        logger.info(
            "FL update received from %s for round %d (%d samples, %.1fMB)",
            update.client_id,
            update.round_id,
            update.num_samples,
            update.get_update_size_mb(),
        )

        return {
            "success": True,
            "round_status": round_status["status"],
            "updates_received": round_status["received_updates"],
            "updates_expected": round_status["expected_updates"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("FL submit update failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/coordinator/global-model")
async def fl_get_global_model(
    model_type: str = "threat_classifier",
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Download the current global model."""
    try:
        from federated_learning.communication import FLCommunicationChannel

        coordinators = _get_fl_coordinators()
        if not coordinators:
            raise HTTPException(status_code=404, detail="No FL coordinators active")

        coordinator = coordinators.get(model_type)
        if not coordinator:
            raise HTTPException(
                status_code=404, detail=f"No coordinator for model type: {model_type}"
            )

        global_weights = coordinator.get_global_model()
        if global_weights is None:
            raise HTTPException(status_code=404, detail="Global model not initialized")

        channel = FLCommunicationChannel()
        serialized_weights = channel.serialize_weights(global_weights)

        logger.info(
            "Global model downloaded by %s (type=%s, version=%d)",
            current_user.user_id,
            model_type,
            coordinator.fl_config.model_version,
        )

        return {
            "model_type": model_type,
            "model_version": coordinator.fl_config.model_version,
            "weights": serialized_weights,
            "total_parameters": sum(w.size for w in global_weights.values()),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("FL get global model failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/coordinator/round-status")
async def fl_round_status(
    model_type: str = "threat_classifier",
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get status of current FL round."""
    try:
        coordinators = _get_fl_coordinators()
        if not coordinators:
            return {"status": "no_active_rounds", "timestamp": datetime.utcnow().isoformat()}

        coordinator = coordinators.get(model_type)
        if not coordinator:
            return {"status": "no_coordinator", "timestamp": datetime.utcnow().isoformat()}

        round_status = coordinator.get_round_status()

        if round_status is None:
            return {"status": "no_active_round", "timestamp": datetime.utcnow().isoformat()}

        return {**round_status, "model_type": model_type, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.exception("FL round status failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/metrics")
async def fl_get_metrics(
    model_type: str = "threat_classifier",
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get federated learning metrics and convergence data."""
    try:
        coordinators = _get_fl_coordinators()
        if not coordinators:
            return {"error": "No FL coordinators active", "timestamp": datetime.utcnow().isoformat()}

        coordinator = coordinators.get(model_type)
        if not coordinator:
            return {
                "error": f"No coordinator for model type: {model_type}",
                "timestamp": datetime.utcnow().isoformat(),
            }

        metrics = coordinator.get_metrics()

        return {
            **metrics.to_dict(),
            "model_type": model_type,
        }

    except Exception as e:
        logger.exception("FL metrics failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
