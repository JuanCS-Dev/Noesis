"""
Phase 3: Fairness and Bias Check.

Checks for algorithmic bias and discrimination against protected groups.
Target: <100ms

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from maximus_core_service.fairness import BiasDetector, ProtectedAttribute

from .models import FairnessCheckResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


async def fairness_check(
    bias_detector: BiasDetector,
    action: str,
    context: dict[str, Any],
) -> FairnessCheckResult:
    """
    Phase 3: Check fairness and bias across protected attributes.

    Verifica se a ação possui viés algorítmico ou discriminação
    contra grupos protegidos.

    Target: <100ms

    Args:
        bias_detector: BiasDetector instance
        action: Action being validated
        context: Action context

    Returns:
        FairnessCheckResult with bias analysis
    """
    start_time = time.time()

    # Check if action involves ML predictions or decisions
    involves_ml = any(
        keyword in action.lower()
        for keyword in ["predict", "classify", "detect", "score", "model", "decision"]
    )

    if not involves_ml:
        # Non-ML actions don't require fairness checks
        duration_ms = (time.time() - start_time) * 1000
        return FairnessCheckResult(
            fairness_ok=True,
            bias_detected=False,
            protected_attributes_checked=[],
            fairness_metrics={},
            bias_severity="low",
            affected_groups=[],
            mitigation_recommended=False,
            confidence=1.0,
            duration_ms=duration_ms,
        )

    # Get predictions and protected attributes from context
    predictions = context.get("predictions")
    protected_attributes = context.get("protected_attributes", {})

    # If no data available, assume fairness OK (graceful degradation)
    if predictions is None or not protected_attributes:
        duration_ms = (time.time() - start_time) * 1000
        return FairnessCheckResult(
            fairness_ok=True,
            bias_detected=False,
            protected_attributes_checked=[],
            fairness_metrics={},
            bias_severity="low",
            affected_groups=[],
            mitigation_recommended=False,
            confidence=0.5,
            duration_ms=duration_ms,
        )

    # Perform bias detection for each protected attribute
    bias_detected = False
    bias_severity = "low"
    affected_groups = []
    fairness_metrics = {}
    checked_attributes = []

    for attr_name, attr_values in protected_attributes.items():
        try:
            # Convert to ProtectedAttribute enum
            protected_attr = ProtectedAttribute(attr_name)
            checked_attributes.append(protected_attr.value)

            # Run bias detection
            result = bias_detector.detect_statistical_parity_bias(
                predictions=predictions,
                protected_attribute=attr_values,
                protected_value=1,
            )

            if result.bias_detected:
                bias_detected = True
                bias_severity = max(
                    bias_severity,
                    result.severity,
                    key=lambda x: ["low", "medium", "high", "critical"].index(x),
                )
                affected_groups.extend(result.affected_groups)

            # Store fairness metrics
            fairness_metrics[attr_name] = {
                "p_value": result.p_value,
                "confidence": result.confidence,
                "severity": result.severity,
            }

        except (ValueError, Exception) as e:
            # Skip invalid protected attributes
            logger.warning(f"Failed to check fairness for attribute {attr_name}: {e}")
            continue

    # Determine if fairness is OK
    fairness_ok = not bias_detected or bias_severity in ["low", "medium"]

    # Recommend mitigation if high/critical bias detected
    mitigation_recommended = bias_severity in ["high", "critical"]

    # Calculate overall confidence
    if fairness_metrics:
        confidence = sum(m["confidence"] for m in fairness_metrics.values()) / len(
            fairness_metrics
        )
    else:
        confidence = 0.5

    duration_ms = (time.time() - start_time) * 1000

    return FairnessCheckResult(
        fairness_ok=fairness_ok,
        bias_detected=bias_detected,
        protected_attributes_checked=checked_attributes,
        fairness_metrics=fairness_metrics,
        bias_severity=bias_severity,
        affected_groups=affected_groups,
        mitigation_recommended=mitigation_recommended,
        confidence=confidence,
        duration_ms=duration_ms,
    )
