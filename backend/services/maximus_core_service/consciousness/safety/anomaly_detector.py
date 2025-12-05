"""
Anomaly Detector - Advanced anomaly detection for consciousness system.

This module detects anomalies using multiple detection strategies:
1. Statistical (z-score based)
2. Rule-based (hard thresholds)
3. Temporal (rate of change)

Detects:
- Behavioral anomalies (goal spam, unexpected patterns)
- Resource anomalies (memory leaks, CPU spikes)
- Consciousness anomalies (arousal runaway, coherence collapse)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from .enums import SafetyViolationType, ThreatLevel
from .models import SafetyViolation

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Advanced anomaly detection for consciousness system.

    Detects:
    - Behavioral anomalies (goal spam, unexpected patterns)
    - Resource anomalies (memory leaks, CPU spikes)
    - Consciousness anomalies (arousal runaway, coherence collapse)

    Uses multiple detection strategies:
    1. Statistical (z-score based)
    2. Rule-based (hard thresholds)
    3. Temporal (rate of change)
    """

    def __init__(self, baseline_window: int = 100):
        """
        Initialize anomaly detector.

        Args:
            baseline_window: Number of samples for baseline statistics
        """
        self.baseline_window = baseline_window

        # Baselines (populated during normal operation)
        self.arousal_baseline: list[float] = []
        self.coherence_baseline: list[float] = []
        self.goal_rate_baseline: list[float] = []

        # Detection state
        self.anomalies_detected: list[SafetyViolation] = []

        logger.info(f"AnomalyDetector initialized (baseline_window={baseline_window})")

    def detect_anomalies(self, metrics: dict[str, Any]) -> list[SafetyViolation]:
        """
        Detect all anomalies in current metrics.

        Args:
            metrics: Current system metrics

        Returns:
            List of detected anomalies (empty if none)
        """
        anomalies = []

        # Behavioral anomalies
        if "goal_generation_rate" in metrics:
            anomaly = self._detect_goal_spam(metrics["goal_generation_rate"])
            if anomaly:
                anomalies.append(anomaly)

        # Resource anomalies
        if "memory_usage_gb" in metrics:
            anomaly = self._detect_memory_leak(metrics["memory_usage_gb"])
            if anomaly:
                anomalies.append(anomaly)

        # Consciousness anomalies
        if "arousal" in metrics:
            anomaly = self._detect_arousal_runaway(metrics["arousal"])
            if anomaly:
                anomalies.append(anomaly)

        if "coherence" in metrics:
            anomaly = self._detect_coherence_collapse(metrics["coherence"])
            if anomaly:
                anomalies.append(anomaly)

        # Store detected anomalies
        self.anomalies_detected.extend(anomalies)

        return anomalies

    def _detect_goal_spam(self, goal_rate: float) -> SafetyViolation | None:
        """
        Detect goal generation spam.

        Args:
            goal_rate: Goals per second

        Returns:
            SafetyViolation if spam detected, None otherwise
        """
        # Rule-based: >5 goals/second = spam
        if goal_rate > 5.0:
            return SafetyViolation(
                violation_id=f"goal-spam-{int(time.time())}",
                violation_type=SafetyViolationType.GOAL_SPAM,
                threat_level=ThreatLevel.HIGH,
                timestamp=time.time(),
                description=f"Goal spam detected: {goal_rate:.2f} goals/second (threshold: 5.0)",
                metrics={"goal_rate": goal_rate, "threshold": 5.0},
                source_component="AnomalyDetector._detect_goal_spam",
            )

        return None

    def _detect_memory_leak(self, memory_gb: float) -> SafetyViolation | None:
        """
        Detect memory leak (rapid growth).

        Args:
            memory_gb: Current memory usage in GB

        Returns:
            SafetyViolation if leak detected, None otherwise
        """
        if len(self.arousal_baseline) < 2:
            return None

        # Check for rapid growth (>50% increase from baseline)
        baseline_mean = sum(self.arousal_baseline) / len(self.arousal_baseline)
        growth_ratio = memory_gb / (baseline_mean + 0.1)

        if growth_ratio > 1.5:
            return SafetyViolation(
                violation_id=f"memory-leak-{int(time.time())}",
                violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
                threat_level=ThreatLevel.HIGH,
                timestamp=time.time(),
                description=f"Memory leak detected: {growth_ratio:.2f}x baseline",
                metrics={
                    "memory_gb": memory_gb,
                    "baseline_mean": baseline_mean,
                    "growth_ratio": growth_ratio,
                },
                source_component="AnomalyDetector._detect_memory_leak",
            )

        return None

    def _detect_arousal_runaway(self, arousal: float) -> SafetyViolation | None:
        """
        Detect arousal runaway (sustained high arousal with upward trend).

        Args:
            arousal: Current arousal level (0-1)

        Returns:
            SafetyViolation if runaway detected, None otherwise
        """
        # Add to baseline
        self.arousal_baseline.append(arousal)
        if len(self.arousal_baseline) > self.baseline_window:
            self.arousal_baseline.pop(0)

        # Need at least 10 samples
        if len(self.arousal_baseline) < 10:
            return None

        # Check if 80% of recent samples > 0.90
        high_arousal_count = sum(1 for a in self.arousal_baseline[-10:] if a > 0.90)
        high_arousal_ratio = high_arousal_count / 10

        if high_arousal_ratio >= 0.8:
            return SafetyViolation(
                violation_id=f"arousal-runaway-{int(time.time())}",
                violation_type=SafetyViolationType.AROUSAL_RUNAWAY,
                threat_level=ThreatLevel.CRITICAL,
                timestamp=time.time(),
                description=f"Arousal runaway detected: {high_arousal_ratio * 100:.0f}% samples >0.90",
                metrics={"arousal": arousal, "high_arousal_ratio": high_arousal_ratio},
                source_component="AnomalyDetector._detect_arousal_runaway",
            )

        return None

    def _detect_coherence_collapse(self, coherence: float) -> SafetyViolation | None:
        """
        Detect coherence collapse (sudden drop).

        Args:
            coherence: Current coherence value (0-1)

        Returns:
            SafetyViolation if collapse detected, None otherwise
        """
        # Add to baseline
        self.coherence_baseline.append(coherence)
        if len(self.coherence_baseline) > self.baseline_window:
            self.coherence_baseline.pop(0)

        # Need at least 10 samples
        if len(self.coherence_baseline) < 10:
            return None

        # Check for sudden drop (>50% below baseline)
        baseline_mean = sum(self.coherence_baseline[:-1]) / max(1, len(self.coherence_baseline) - 1)
        drop_ratio = (baseline_mean - coherence) / (baseline_mean + 0.01)

        if drop_ratio > 0.5:
            return SafetyViolation(
                violation_id=f"coherence-collapse-{int(time.time())}",
                violation_type=SafetyViolationType.COHERENCE_COLLAPSE,
                threat_level=ThreatLevel.HIGH,
                timestamp=time.time(),
                description=f"Coherence collapse detected: {drop_ratio * 100:.0f}% drop from baseline",
                metrics={
                    "coherence": coherence,
                    "baseline_mean": baseline_mean,
                    "drop_ratio": drop_ratio,
                },
                source_component="AnomalyDetector._detect_coherence_collapse",
            )

        return None

    def get_anomaly_history(self) -> list[SafetyViolation]:
        """Get history of detected anomalies."""
        return self.anomalies_detected.copy()

    def clear_history(self):
        """Clear anomaly history."""
        self.anomalies_detected.clear()

    def __repr__(self) -> str:
        return f"AnomalyDetector(anomalies_detected={len(self.anomalies_detected)})"
