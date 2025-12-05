"""Fairness & Bias Mitigation Endpoints."""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.services.ethical_audit_service.auth import TokenData, require_auditor_or_admin, require_soc_or_admin

from ..state import get_app_state_value, get_limiter, set_app_state_value

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fairness", tags=["fairness"])

FAIRNESS_PATH = "/home/juan/vertice-dev/backend/services/maximus_core_service"


def _ensure_fairness_path() -> None:
    """Ensure fairness module path is available."""
    if FAIRNESS_PATH not in sys.path:
        sys.path.append(FAIRNESS_PATH)


def _get_fairness_monitor() -> Any:
    """Get or create fairness monitor."""
    monitor = get_app_state_value("fairness_monitor")
    if monitor is None:
        _ensure_fairness_path()
        from fairness.monitor import FairnessMonitor

        monitor = FairnessMonitor({"history_max_size": 1000, "alert_threshold": "medium"})
        set_app_state_value("fairness_monitor", monitor)
    return monitor


def _get_mitigation_engine() -> Any:
    """Get or create mitigation engine."""
    engine = get_app_state_value("mitigation_engine")
    if engine is None:
        _ensure_fairness_path()
        from fairness.mitigation import MitigationEngine

        engine = MitigationEngine(
            {"performance_threshold": 0.75, "max_performance_loss": 0.05}
        )
        set_app_state_value("mitigation_engine", engine)
    return engine


@router.post("/evaluate")
async def evaluate_fairness(
    request: Request,
    fairness_request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Evaluate fairness of model predictions across protected groups."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("50/minute")(request)

    try:
        _ensure_fairness_path()

        import numpy as np
        from fairness.base import ProtectedAttribute

        model_id = fairness_request.get("model_id", "unknown")
        predictions = np.array(fairness_request.get("predictions", []))
        true_labels_list = fairness_request.get("true_labels")
        true_labels = np.array(true_labels_list) if true_labels_list else None
        protected_attribute = np.array(fairness_request.get("protected_attribute", []))
        protected_value = fairness_request.get("protected_value", 1)
        protected_attr_type = fairness_request.get(
            "protected_attr_type", "geographic_location"
        )

        if len(predictions) == 0:
            raise HTTPException(status_code=400, detail="predictions array is required")
        if len(protected_attribute) == 0:
            raise HTTPException(
                status_code=400, detail="protected_attribute array is required"
            )
        if len(predictions) != len(protected_attribute):
            raise HTTPException(
                status_code=400,
                detail="predictions and protected_attribute must have same length",
            )

        try:
            prot_attr = ProtectedAttribute(protected_attr_type)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid protected_attr_type: {[p.value for p in ProtectedAttribute]}",
            ) from e

        monitor = _get_fairness_monitor()

        start_time = time.time()

        snapshot = monitor.evaluate_fairness(
            predictions=predictions,
            true_labels=true_labels,
            protected_attribute=protected_attribute,
            protected_value=protected_value,
            model_id=model_id,
            protected_attr_type=prot_attr,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        fairness_metrics = {}
        for metric, result in snapshot.fairness_results.items():
            fairness_metrics[metric.value] = {
                "is_fair": result.is_fair,
                "difference": result.difference,
                "ratio": result.ratio,
                "threshold": result.threshold,
                "group_0_value": result.group_0_value,
                "group_1_value": result.group_1_value,
                "sample_size_0": result.sample_size_0,
                "sample_size_1": result.sample_size_1,
            }

        bias_results = {}
        for method, result in snapshot.bias_results.items():
            bias_results[method] = {
                "bias_detected": result.bias_detected,
                "severity": result.severity,
                "confidence": result.confidence,
                "p_value": result.p_value,
                "effect_size": result.effect_size,
                "affected_groups": result.affected_groups,
                "metadata": result.metadata,
            }

        logger.info(
            "Fairness evaluation complete: model=%s, latency=%dms, %d metrics",
            model_id,
            latency_ms,
            len(fairness_metrics),
        )

        return {
            "success": True,
            "model_id": model_id,
            "protected_attribute": prot_attr.value,
            "sample_size": snapshot.sample_size,
            "timestamp": snapshot.timestamp.isoformat(),
            "fairness_metrics": fairness_metrics,
            "bias_detection": bias_results,
            "latency_ms": latency_ms,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Fairness evaluation failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to evaluate fairness: {e!s}"
        ) from e


@router.post("/mitigate")
async def mitigate_bias(
    request: Request,
    mitigation_request: dict[str, Any],
    current_user: TokenData = Depends(require_soc_or_admin),
) -> dict[str, Any]:
    """Apply bias mitigation strategy to model predictions."""
    limiter = get_limiter()
    if limiter:
        await limiter.limit("20/minute")(request)

    try:
        _ensure_fairness_path()

        import numpy as np

        strategy = mitigation_request.get("strategy", "auto")
        predictions = np.array(mitigation_request.get("predictions", []))
        true_labels = np.array(mitigation_request.get("true_labels", []))
        protected_attribute = np.array(mitigation_request.get("protected_attribute", []))
        protected_value = mitigation_request.get("protected_value", 1)

        if len(predictions) == 0 or len(true_labels) == 0:
            raise HTTPException(
                status_code=400, detail="predictions and true_labels are required"
            )

        engine = _get_mitigation_engine()

        start_time = time.time()

        if strategy == "auto":
            result = engine.mitigate_auto(
                predictions, true_labels, protected_attribute, protected_value
            )
        elif strategy == "threshold_optimization":
            result = engine.mitigate_threshold_optimization(
                predictions, true_labels, protected_attribute, protected_value
            )
        elif strategy == "calibration_adjustment":
            result = engine.mitigate_calibration_adjustment(
                predictions, true_labels, protected_attribute, protected_value
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid strategy: auto, threshold_optimization, calibration_adjustment",
            )

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Bias mitigation complete: strategy=%s, success=%s, latency=%dms",
            result.mitigation_method,
            result.success,
            latency_ms,
        )

        return {
            "success": result.success,
            "mitigation_method": result.mitigation_method,
            "protected_attribute": result.protected_attribute.value,
            "fairness_before": result.fairness_before,
            "fairness_after": result.fairness_after,
            "performance_impact": result.performance_impact,
            "timestamp": result.timestamp.isoformat(),
            "metadata": result.metadata,
            "latency_ms": latency_ms,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Bias mitigation failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to mitigate bias: {e!s}"
        ) from e


@router.get("/trends")
async def get_fairness_trends(
    model_id: str | None = None,
    metric: str | None = None,
    lookback_hours: int = Query(24, ge=1, le=168),
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get fairness trends over time."""
    try:
        monitor = get_app_state_value("fairness_monitor")
        if not monitor:
            return {"trends": {}, "num_snapshots": 0, "message": "No fairness data available"}

        fairness_metric = None
        if metric:
            _ensure_fairness_path()
            from fairness.base import FairnessMetric

            try:
                fairness_metric = FairnessMetric(metric)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric: {[m.value for m in FairnessMetric]}",
                ) from e

        trends = monitor.get_fairness_trends(
            model_id=model_id, metric=fairness_metric, lookback_hours=lookback_hours
        )

        return trends

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get fairness trends: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {e!s}") from e


@router.get("/drift")
async def detect_fairness_drift(
    model_id: str | None = None,
    metric: str | None = None,
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Detect drift in fairness metrics."""
    try:
        monitor = get_app_state_value("fairness_monitor")
        if not monitor:
            return {"drift_detected": False, "message": "No fairness data available"}

        fairness_metric = None
        if metric:
            _ensure_fairness_path()
            from fairness.base import FairnessMetric

            try:
                fairness_metric = FairnessMetric(metric)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric: {[m.value for m in FairnessMetric]}",
                ) from e

        drift_result = monitor.detect_drift(model_id=model_id, metric=fairness_metric)

        return drift_result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to detect fairness drift: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to detect drift: {e!s}") from e


@router.get("/alerts")
async def get_fairness_alerts(
    severity: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    since_hours: int | None = Query(None, ge=1, le=720),
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get fairness violation alerts."""
    try:
        monitor = get_app_state_value("fairness_monitor")
        if not monitor:
            return {"alerts": [], "total": 0, "message": "No fairness monitoring active"}

        alerts = monitor.get_alerts(severity=severity, limit=limit, since_hours=since_hours)

        alerts_dict = [
            {
                "alert_id": alert.alert_id,
                "timestamp": alert.timestamp.isoformat(),
                "severity": alert.severity,
                "metric": alert.metric.value,
                "protected_attribute": alert.protected_attribute.value,
                "violation_details": alert.violation_details,
                "recommended_action": alert.recommended_action,
                "auto_mitigated": alert.auto_mitigated,
                "metadata": alert.metadata,
            }
            for alert in alerts
        ]

        return {
            "alerts": alerts_dict,
            "total": len(alerts_dict),
            "severity_filter": severity,
            "limit": limit,
        }

    except Exception as e:
        logger.exception("Failed to get fairness alerts: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {e!s}") from e


@router.get("/stats")
async def get_fairness_stats(
    current_user: TokenData = Depends(require_auditor_or_admin),
) -> dict[str, Any]:
    """Get fairness monitoring statistics."""
    try:
        monitor = get_app_state_value("fairness_monitor")
        if not monitor:
            return {
                "total_evaluations": 0,
                "total_violations": 0,
                "violation_rate": 0.0,
                "message": "No fairness monitoring active",
            }

        stats = monitor.get_statistics()

        return stats

    except Exception as e:
        logger.exception("Failed to get fairness stats: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {e!s}"
        ) from e


@router.get("/health")
async def fairness_health_check() -> dict[str, Any]:
    """Fairness module health check."""
    try:
        _ensure_fairness_path()

        from fairness.bias_detector import BiasDetector
        from fairness.constraints import FairnessConstraints
        from fairness.mitigation import MitigationEngine

        FairnessConstraints()
        BiasDetector()
        MitigationEngine()

        monitor = get_app_state_value("fairness_monitor")
        monitor_active = monitor is not None
        monitor_snapshots = len(monitor.history) if monitor_active else 0

        return {
            "status": "healthy",
            "components": {
                "fairness_constraints": "ok",
                "bias_detector": "ok",
                "mitigation_engine": "ok",
                "monitor": "active" if monitor_active else "inactive",
            },
            "monitor_snapshots": monitor_snapshots,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Fairness health check failed: %s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
