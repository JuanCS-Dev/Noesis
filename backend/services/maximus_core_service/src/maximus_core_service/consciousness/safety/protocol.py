"""
Safety Protocol - Main coordinator integrating ThresholdMonitor, AnomalyDetector, KillSwitch.
Provides unified safety interface with graceful degradation and HITL notification.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

import psutil

from .anomaly_detector import AnomalyDetector
from .component_health import ComponentHealthMixin
from .enums import ShutdownReason, ThreatLevel
from .kill_switch import KillSwitch
from .models import SafetyViolation
from .threshold_monitor import ThresholdMonitor
from .thresholds import SafetyThresholds

logger = logging.getLogger(__name__)


class ConsciousnessSafetyProtocol(ComponentHealthMixin):
    """
    Main safety protocol coordinator.

    Integrates:
    - ThresholdMonitor (hard limits)
    - AnomalyDetector (statistical detection)
    - KillSwitch (emergency shutdown)

    Provides:
    - Unified safety interface
    - Graceful degradation
    - HITL notification
    - Automated response
    """

    def __init__(
        self, consciousness_system: Any, thresholds: SafetyThresholds | None = None
    ):
        """
        Initialize safety protocol.

        Args:
            consciousness_system: Reference to consciousness system
            thresholds: Safety thresholds (default if None)
        """
        self.consciousness_system = consciousness_system
        self.thresholds = thresholds or SafetyThresholds()

        # Components
        self.threshold_monitor = ThresholdMonitor(self.thresholds)
        self.anomaly_detector = AnomalyDetector()
        self.kill_switch = KillSwitch(consciousness_system)

        # State
        self.monitoring_active = False
        self.monitoring_task: asyncio.Task[None] | None = None
        self.degradation_level = 0  # 0=normal, 1=minor, 2=major, 3=critical

        # Callbacks
        self.on_violation: Callable[[SafetyViolation], None] | None = None

        logger.info("✅ Consciousness Safety Protocol initialized")
        logger.info(
            f"Thresholds: ESGT<{self.thresholds.esgt_frequency_max_hz}Hz, "
            f"Arousal<{self.thresholds.arousal_max}"
        )

    async def start_monitoring(self) -> None:
        """Start continuous safety monitoring."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🔍 Safety monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop safety monitoring."""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Safety monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop (1 Hz)."""
        logger.info("Monitoring loop started")

        while self.monitoring_active:
            try:
                # Check if kill switch is active (system offline)
                if self.kill_switch.is_triggered():
                    logger.warning("System in emergency shutdown - monitoring paused")
                    await asyncio.sleep(5.0)
                    continue

                # Get current metrics
                current_time = time.time()
                metrics = self._collect_metrics()

                # Check thresholds
                violations = self._check_all_thresholds(metrics, current_time)

                # Handle violations by threat level
                await self._handle_violations(violations)

                # Update Prometheus metrics
                if hasattr(self.consciousness_system, "_update_prometheus_metrics"):
                    self.consciousness_system._update_prometheus_metrics()

                # Sleep before next check
                await asyncio.sleep(self.threshold_monitor.check_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    def _check_all_thresholds(
        self, metrics: dict[str, Any], current_time: float
    ) -> list[SafetyViolation]:
        """Check all threshold conditions and return violations."""
        violations: list[SafetyViolation] = []

        # 1. ESGT frequency
        violation = self.threshold_monitor.check_esgt_frequency(current_time)
        if violation:
            violations.append(violation)

        # 2. Arousal sustained high
        if "arousal" in metrics:
            violation = self.threshold_monitor.check_arousal_sustained(
                metrics["arousal"], current_time
            )
            if violation:
                violations.append(violation)

        # 3. Goal spam
        violation = self.threshold_monitor.check_goal_spam(current_time)
        if violation:
            violations.append(violation)

        # 4. Resource limits
        resource_violations = self.threshold_monitor.check_resource_limits()
        violations.extend(resource_violations)

        # 5. Anomaly detection
        anomalies = self.anomaly_detector.detect_anomalies(metrics)
        violations.extend(anomalies)

        return violations

    def _collect_metrics(self) -> dict[str, Any]:
        """Collect current system metrics."""
        metrics: dict[str, Any] = {}

        try:
            # Try to get consciousness component metrics
            if hasattr(self.consciousness_system, "get_system_dict"):
                system_dict = self.consciousness_system.get_system_dict()

                # Arousal
                if "arousal" in system_dict:
                    metrics["arousal"] = system_dict["arousal"].get("arousal", 0.0)

                # Coherence
                if "esgt" in system_dict:
                    metrics["coherence"] = system_dict["esgt"].get("coherence", 0.0)

                # Goals
                if "mmei" in system_dict:
                    active_goals = system_dict["mmei"].get("active_goals", [])
                    metrics["active_goal_count"] = len(active_goals)

            # System resources (always available)
            process = psutil.Process()
            metrics["memory_usage_gb"] = process.memory_info().rss / 1024 / 1024 / 1024
            metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

        return metrics

    async def _handle_violations(self, violations: list[SafetyViolation]) -> None:
        """Handle detected violations by threat level."""
        if not violations:
            return

        # Categorize by threat level
        critical = [v for v in violations if v.threat_level == ThreatLevel.CRITICAL]
        high = [v for v in violations if v.threat_level == ThreatLevel.HIGH]
        medium = [v for v in violations if v.threat_level == ThreatLevel.MEDIUM]
        low = [v for v in violations if v.threat_level == ThreatLevel.LOW]

        # CRITICAL: Trigger kill switch
        if critical:
            logger.critical(f"🚨 {len(critical)} CRITICAL violations - triggering kill switch")
            for v in critical:
                logger.critical(f"  - {v.description}")

            self.kill_switch.trigger(
                reason=ShutdownReason.THRESHOLD,
                context={
                    "violations": violations,
                    "metrics_timeline": [],
                    "notes": f"{len(critical)} CRITICAL violations triggered automatic shutdown",
                },
            )
            return

        # HIGH: Initiate graceful degradation
        if high:
            logger.warning(f"⚠️  {len(high)} HIGH violations - initiating degradation")
            for v in high:
                logger.warning(f"  - {v.description}")
            await self._graceful_degradation()

        # MEDIUM: Alert and monitor
        if medium:
            logger.warning(f"⚠️  {len(medium)} MEDIUM violations")
            for v in medium:
                logger.warning(f"  - {v.description}")

        # LOW: Log only
        if low:
            for v in low:
                logger.info(f"ℹ️  LOW: {v.description}")

        # Invoke callbacks
        if self.on_violation:
            for v in violations:
                self.on_violation(v)

    async def _graceful_degradation(self) -> None:
        """
        Initiate graceful degradation (disable non-critical components).

        Degradation levels:
        1. Minor: Throttle ESGT frequency, reduce goal generation
        2. Major: Stop LRR, pause MMEI
        3. Critical: Trigger kill switch
        """
        self.degradation_level += 1

        if self.degradation_level == 1:
            logger.warning("Degradation Level 1: Throttling ESGT and goal generation")
        elif self.degradation_level == 2:
            logger.warning("Degradation Level 2: Stopping LRR, pausing MMEI")
        elif self.degradation_level >= 3:
            logger.critical("Degradation Level 3: Triggering kill switch")
            self.kill_switch.trigger(
                reason=ShutdownReason.THRESHOLD,
                context={
                    "violations": [],
                    "notes": "Graceful degradation exhausted - proceeding to shutdown",
                },
            )

    def get_status(self) -> dict[str, Any]:
        """Get current safety status."""
        return {
            "monitoring_active": self.monitoring_active,
            "kill_switch_triggered": self.kill_switch.is_triggered(),
            "degradation_level": self.degradation_level,
            "violations_total": len(self.threshold_monitor.violations),
            "violations_critical": len(
                self.threshold_monitor.get_violations(ThreatLevel.CRITICAL)
            ),
            "violations_high": len(
                self.threshold_monitor.get_violations(ThreatLevel.HIGH)
            ),
            "anomalies_detected": len(self.anomaly_detector.get_anomaly_history()),
            "thresholds": {
                "esgt_frequency_max_hz": self.thresholds.esgt_frequency_max_hz,
                "arousal_max": self.thresholds.arousal_max,
                "self_modification": self.thresholds.self_modification_attempts_max,
            },
        }

    def __repr__(self) -> str:
        status = "ACTIVE" if self.monitoring_active else "INACTIVE"
        return (
            f"ConsciousnessSafetyProtocol(status={status}, "
            f"degradation_level={self.degradation_level})"
        )
