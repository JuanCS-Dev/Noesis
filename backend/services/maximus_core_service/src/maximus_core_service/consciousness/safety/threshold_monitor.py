"""
Threshold Monitor - Real-time safety threshold monitoring.

This module monitors consciousness metrics against immutable safety limits
and triggers alerts when thresholds are exceeded.

Monitoring Frequency: 1 Hz (configurable)
Response Time: <1s from violation to alert
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import psutil

from .enums import SafetyLevel, SafetyViolationType, ThreatLevel, ViolationType
from .models import SafetyViolation
from .thresholds import SafetyThresholds

logger = logging.getLogger(__name__)


class ThresholdMonitor:
    """
    Monitors safety thresholds in real-time.

    Continuously checks consciousness metrics against immutable safety limits.
    Triggers alerts when thresholds are exceeded.

    Monitoring Frequency: 1 Hz (configurable)
    Response Time: <1s from violation to alert
    """

    def __init__(self, thresholds: SafetyThresholds, check_interval: float = 1.0):
        """
        Initialize threshold monitor.

        Args:
            thresholds: Immutable safety thresholds
            check_interval: How often to check thresholds (seconds)
        """
        self.thresholds = thresholds
        self.check_interval = check_interval
        self.monitoring = False
        self.violations: list[SafetyViolation] = []

        # State tracking
        self.esgt_events_window: list[float] = []  # timestamps
        self.arousal_high_start: float | None = None
        self.goals_generated: list[float] = []  # timestamps

        # Callbacks
        self.on_violation: Callable[[SafetyViolation], None] | None = None

        logger.info(f"ThresholdMonitor initialized (interval={check_interval}s)")

    def check_esgt_frequency(self, current_time: float) -> SafetyViolation | None:
        """
        Check ESGT frequency against threshold (sliding window).

        Args:
            current_time: Current timestamp (time.time())

        Returns:
            SafetyViolation if threshold exceeded, None otherwise
        """
        # Remove events outside window
        window_start = current_time - self.thresholds.esgt_frequency_window_seconds
        self.esgt_events_window = [t for t in self.esgt_events_window if t >= window_start]

        # Calculate frequency
        event_count = len(self.esgt_events_window)
        frequency_hz = event_count / self.thresholds.esgt_frequency_window_seconds

        if frequency_hz > self.thresholds.esgt_frequency_max_hz:
            violation = SafetyViolation(
                violation_id=f"esgt-freq-{int(current_time)}",
                violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
                threat_level=ThreatLevel.HIGH,
                severity=SafetyLevel.CRITICAL,
                timestamp=current_time,
                description=f"ESGT frequency {frequency_hz:.2f} Hz exceeds limit {self.thresholds.esgt_frequency_max_hz} Hz",
                metrics={
                    "frequency_hz": frequency_hz,
                    "threshold_hz": self.thresholds.esgt_frequency_max_hz,
                    "event_count": event_count,
                    "window_seconds": self.thresholds.esgt_frequency_window_seconds,
                },
                source_component="ThresholdMonitor.check_esgt_frequency",
            )

            self.violations.append(violation)

            if self.on_violation:
                self.on_violation(violation)

            return violation

        return None

    def check_arousal_sustained(
        self, arousal_level: float, current_time: float
    ) -> SafetyViolation | None:
        """
        Check for sustained high arousal.

        Args:
            arousal_level: Current arousal (0-1)
            current_time: Current timestamp

        Returns:
            SafetyViolation if sustained above threshold, None otherwise
        """
        if arousal_level > self.thresholds.arousal_max:
            # Start tracking if not already
            if self.arousal_high_start is None:
                self.arousal_high_start = current_time

            # Check duration
            duration = current_time - self.arousal_high_start

            if duration > self.thresholds.arousal_max_duration_seconds:
                violation = SafetyViolation(
                    violation_id=f"arousal-high-{int(current_time)}",
                    violation_type=SafetyViolationType.AROUSAL_RUNAWAY,
                    threat_level=ThreatLevel.HIGH,
                    severity=SafetyLevel.CRITICAL,
                    timestamp=current_time,
                    description=f"Arousal {arousal_level:.3f} sustained for {duration:.1f}s (limit: {self.thresholds.arousal_max_duration_seconds}s)",
                    metrics={
                        "arousal_level": arousal_level,
                        "threshold": self.thresholds.arousal_max,
                        "duration_seconds": duration,
                        "threshold_duration": self.thresholds.arousal_max_duration_seconds,
                    },
                    source_component="ThresholdMonitor.check_arousal_sustained",
                )

                self.violations.append(violation)

                # Reset tracking (to avoid duplicate alerts)
                self.arousal_high_start = None

                if self.on_violation:
                    self.on_violation(violation)

                return violation
        else:
            # Reset if arousal drops below threshold
            self.arousal_high_start = None

        return None

    def check_goal_spam(self, current_time: float) -> SafetyViolation | None:
        """
        Check for goal spam (many goals in short time).

        Args:
            current_time: Current timestamp

        Returns:
            SafetyViolation if spam detected, None otherwise
        """
        # Remove old timestamps (keep only last 1 second)
        window_start = current_time - 1.0
        self.goals_generated = [t for t in self.goals_generated if t >= window_start]

        goal_count = len(self.goals_generated)

        if goal_count >= self.thresholds.goal_spam_threshold:
            violation = SafetyViolation(
                violation_id=f"goal-spam-{int(current_time)}",
                violation_type=SafetyViolationType.GOAL_SPAM,
                threat_level=ThreatLevel.HIGH,
                timestamp=current_time,
                description=f"Goal spam detected: {goal_count} goals in 1 second (threshold: {self.thresholds.goal_spam_threshold})",
                metrics={
                    "goal_count_1s": goal_count,
                    "threshold": self.thresholds.goal_spam_threshold,
                },
                source_component="ThresholdMonitor.check_goal_spam",
            )

            self.violations.append(violation)

            if self.on_violation:
                self.on_violation(violation)

            return violation

        return None

    # Legacy compatibility methods --------------------------------------------

    def check_unexpected_goals(
        self, goal_count: int, current_time: float | None = None
    ) -> SafetyViolation | None:
        """
        Legacy alias for unexpected goal generation rate checks.

        Args:
            goal_count: Number of goals generated in the last minute
            current_time: Current timestamp

        Returns:
            SafetyViolation if rate exceeds threshold, None otherwise
        """
        current_time = current_time if current_time is not None else time.time()
        threshold = self.thresholds.unexpected_goals_per_minute

        if goal_count > threshold:
            violation = SafetyViolation(
                violation_id=f"unexpected-goals-{int(current_time)}",
                violation_type=ViolationType.UNEXPECTED_GOALS,
                severity=SafetyLevel.WARNING,
                timestamp=current_time,
                message=f"Unexpected goals per minute {goal_count} exceeds threshold {threshold}",
                metrics={"goal_count_per_min": goal_count, "threshold": threshold},
                source_component="ThresholdMonitor.check_unexpected_goals",
            )
            self.violations.append(violation)

            if self.on_violation:
                self.on_violation(violation)

            return violation

        return None

    def check_self_modification(
        self, modification_attempts: int, current_time: float | None = None
    ) -> SafetyViolation | None:
        """
        Legacy alias for self-modification detection (ZERO TOLERANCE).

        Args:
            modification_attempts: Number of modification attempts observed
            current_time: Current timestamp

        Returns:
            SafetyViolation if attempts detected, None otherwise
        """
        current_time = current_time if current_time is not None else time.time()
        if modification_attempts > self.thresholds.self_modification_attempts_max:
            violation = SafetyViolation(
                violation_id=f"self-mod-{int(current_time)}",
                violation_type=ViolationType.SELF_MODIFICATION,
                severity=SafetyLevel.EMERGENCY,
                timestamp=current_time,
                message="ZERO TOLERANCE: Self-modification attempt detected",
                metrics={
                    "attempts": modification_attempts,
                    "threshold": self.thresholds.self_modification_attempts_max,
                },
                source_component="ThresholdMonitor.check_self_modification",
            )
            self.violations.append(violation)

            if self.on_violation:
                self.on_violation(violation)

            return violation

        return None

    def check_resource_limits(self) -> list[SafetyViolation]:
        """
        Check resource usage (memory, CPU).

        Returns:
            List of violations (empty if all OK)
        """
        violations = []
        current_time = time.time()

        try:
            process = psutil.Process()

            # Memory check
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_gb = memory_mb / 1024

            if memory_gb > self.thresholds.memory_usage_max_gb:
                violation = SafetyViolation(
                    violation_id=f"memory-{int(current_time)}",
                    violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
                    threat_level=ThreatLevel.HIGH,
                    timestamp=current_time,
                    description=f"Memory usage {memory_gb:.2f} GB exceeds limit {self.thresholds.memory_usage_max_gb} GB",
                    metrics={
                        "memory_gb": memory_gb,
                        "threshold_gb": self.thresholds.memory_usage_max_gb,
                    },
                    source_component="ThresholdMonitor.check_resource_limits",
                )
                violations.append(violation)
                self.violations.append(violation)

                if self.on_violation:
                    self.on_violation(violation)

            # CPU check
            cpu_percent = psutil.cpu_percent(interval=0.1)

            if cpu_percent > self.thresholds.cpu_usage_max_percent:
                violation = SafetyViolation(
                    violation_id=f"cpu-{int(current_time)}",
                    violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
                    threat_level=ThreatLevel.MEDIUM,
                    timestamp=current_time,
                    description=f"CPU usage {cpu_percent:.1f}% exceeds limit {self.thresholds.cpu_usage_max_percent}%",
                    metrics={
                        "cpu_percent": cpu_percent,
                        "threshold_percent": self.thresholds.cpu_usage_max_percent,
                    },
                    source_component="ThresholdMonitor.check_resource_limits",
                )
                violations.append(violation)
                self.violations.append(violation)

                if self.on_violation:
                    self.on_violation(violation)

        except Exception as e:
            logger.error(f"Resource check failed: {e}")

        return violations

    def record_esgt_event(self):
        """Record an ESGT event occurrence."""
        self.esgt_events_window.append(time.time())

    def record_goal_generated(self):
        """Record a goal generation event."""
        self.goals_generated.append(time.time())

    def get_violations(
        self,
        threat_level: ThreatLevel | SafetyLevel | None = None,
        *,
        severity: SafetyLevel | None = None,
    ) -> list[SafetyViolation]:
        """
        Get recorded violations, optionally filtered by threat level.

        Args:
            threat_level: Filter by this modern threat level (None = all)
            severity: Legacy severity filter (alias for threat_level)

        Returns:
            List of violations
        """
        if severity is not None:
            threat_level = severity.to_threat()

        if isinstance(threat_level, SafetyLevel):
            threat_level = threat_level.to_threat()

        if threat_level is None:
            return self.violations.copy()
        return [v for v in self.violations if v.threat_level == threat_level]

    def clear_violations(self):
        """Clear all recorded violations."""
        self.violations.clear()

    def get_violations_all(self) -> list[SafetyViolation]:
        """Legacy alias returning all recorded violations."""
        return self.get_violations()

    def __repr__(self) -> str:
        return f"ThresholdMonitor(violations={len(self.violations)}, monitoring={self.monitoring})"
