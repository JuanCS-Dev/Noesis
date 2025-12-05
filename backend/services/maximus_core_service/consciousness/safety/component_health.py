"""Component Health Monitoring - Mixin for consciousness component health checks."""

from __future__ import annotations

import logging
import time
from typing import Any, TYPE_CHECKING

from .enums import ThreatLevel
from .models import SafetyViolation

if TYPE_CHECKING:
    from .protocol import ConsciousnessSafetyProtocol

logger = logging.getLogger(__name__)


class ComponentHealthMixin:
    """Mixin providing component-level health monitoring for SafetyProtocol."""

    def monitor_component_health(
        self: "ConsciousnessSafetyProtocol",
        component_metrics: dict[str, dict[str, Any]],
    ) -> list[SafetyViolation]:
        """
        Monitor health metrics from all consciousness components.

        Integrates with get_health_metrics() from TIG, ESGT, MMEI, MCEA.
        Detects component-level anomalies and safety violations.

        Args:
            component_metrics: Dict mapping component name to health metrics
                Expected keys: "tig", "esgt", "mmei", "mcea"

        Returns:
            List of SafetyViolations detected (empty if all healthy)
        """
        violations: list[SafetyViolation] = []

        # Check each component
        violations.extend(self._check_tig_health(component_metrics.get("tig", {})))
        violations.extend(self._check_esgt_health(component_metrics.get("esgt", {})))
        violations.extend(self._check_mmei_health(component_metrics.get("mmei", {})))
        violations.extend(self._check_mcea_health(component_metrics.get("mcea", {})))

        # Log violations
        for violation in violations:
            logger.warning(f"🚨 Component Health Violation: {violation}")

        return violations

    def _check_tig_health(
        self: "ConsciousnessSafetyProtocol", tig: dict[str, Any]
    ) -> list[SafetyViolation]:
        """Check TIG fabric health metrics."""
        violations: list[SafetyViolation] = []
        if not tig:
            return violations

        # Check connectivity (critical if <50%)
        if tig.get("connectivity", 1.0) < 0.50:
            violations.append(
                SafetyViolation(
                    violation_id=f"tig-connectivity-{int(time.time())}",
                    violation_type="resource_exhaustion",
                    threat_level=ThreatLevel.CRITICAL,
                    timestamp=time.time(),
                    description=f"TIG connectivity critically low: {tig['connectivity']:.1%}",
                    metrics={"connectivity": tig["connectivity"], "threshold": 0.50},
                    source_component="tig_fabric",
                )
            )

        # Check partition
        if tig.get("is_partitioned", False):
            violations.append(
                SafetyViolation(
                    violation_id=f"tig-partition-{int(time.time())}",
                    violation_type="unexpected_behavior",
                    threat_level=ThreatLevel.HIGH,
                    timestamp=time.time(),
                    description="TIG network is partitioned",
                    metrics={"is_partitioned": True},
                    source_component="tig_fabric",
                )
            )

        return violations

    def _check_esgt_health(
        self: "ConsciousnessSafetyProtocol", esgt: dict[str, Any]
    ) -> list[SafetyViolation]:
        """Check ESGT coordinator health metrics."""
        violations: list[SafetyViolation] = []
        if not esgt:
            return violations

        # Check degraded mode
        if esgt.get("degraded_mode", False):
            violations.append(
                SafetyViolation(
                    violation_id=f"esgt-degraded-{int(time.time())}",
                    violation_type="unexpected_behavior",
                    threat_level=ThreatLevel.MEDIUM,
                    timestamp=time.time(),
                    description="ESGT in degraded mode",
                    metrics={"degraded_mode": True},
                    source_component="esgt_coordinator",
                )
            )

        # Check frequency (already monitored, but component-level context)
        freq = esgt.get("frequency_hz", 0.0)
        if freq > 9.0:  # Warning at 90% of hard limit
            violations.append(
                SafetyViolation(
                    violation_id=f"esgt-freq-{int(time.time())}",
                    violation_type="threshold_exceeded",
                    threat_level=ThreatLevel.HIGH,
                    timestamp=time.time(),
                    description=f"ESGT frequency approaching limit: {freq:.1f}Hz",
                    metrics={"frequency_hz": freq, "threshold": 9.0},
                    source_component="esgt_coordinator",
                )
            )

        # Check circuit breaker state
        if esgt.get("circuit_breaker_state") == "open":
            violations.append(
                SafetyViolation(
                    violation_id=f"esgt-breaker-{int(time.time())}",
                    violation_type="threshold_exceeded",
                    threat_level=ThreatLevel.HIGH,
                    timestamp=time.time(),
                    description="ESGT circuit breaker is OPEN",
                    metrics={"circuit_breaker_state": "open"},
                    source_component="esgt_coordinator",
                )
            )

        return violations

    def _check_mmei_health(
        self: "ConsciousnessSafetyProtocol", mmei: dict[str, Any]
    ) -> list[SafetyViolation]:
        """Check MMEI monitor health metrics."""
        violations: list[SafetyViolation] = []
        if not mmei:
            return violations

        # Check overflow events
        overflow_events = mmei.get("need_overflow_events", 0)
        if overflow_events > 0:
            violations.append(
                SafetyViolation(
                    violation_id=f"mmei-overflow-{int(time.time())}",
                    violation_type="resource_exhaustion",
                    threat_level=ThreatLevel.HIGH,
                    timestamp=time.time(),
                    description=f"MMEI need overflow detected ({overflow_events} events)",
                    metrics={"overflow_events": overflow_events, "threshold": 0.0},
                    source_component="mmei_monitor",
                )
            )

        # Check rate limiting
        goals_rate_limited = mmei.get("goals_rate_limited", 0)
        if goals_rate_limited > 10:  # Threshold: >10 rate-limited goals
            violations.append(
                SafetyViolation(
                    violation_id=f"mmei-ratelimit-{int(time.time())}",
                    violation_type="goal_spam",
                    threat_level=ThreatLevel.MEDIUM,
                    timestamp=time.time(),
                    description=f"MMEI excessive rate limiting ({goals_rate_limited} blocked)",
                    metrics={"goals_rate_limited": goals_rate_limited, "threshold": 10.0},
                    source_component="mmei_monitor",
                )
            )

        return violations

    def _check_mcea_health(
        self: "ConsciousnessSafetyProtocol", mcea: dict[str, Any]
    ) -> list[SafetyViolation]:
        """Check MCEA controller health metrics."""
        violations: list[SafetyViolation] = []
        if not mcea:
            return violations

        # Check saturation
        if mcea.get("is_saturated", False):
            violations.append(
                SafetyViolation(
                    violation_id=f"mcea-saturated-{int(time.time())}",
                    violation_type="arousal_runaway",
                    threat_level=ThreatLevel.HIGH,
                    timestamp=time.time(),
                    description="MCEA arousal saturated (stuck at boundary)",
                    metrics={
                        "current_arousal": mcea.get("current_arousal", 0.0),
                        "threshold": 0.01,
                    },
                    source_component="mcea_controller",
                )
            )

        # Check oscillation
        oscillation_events = mcea.get("oscillation_events", 0)
        if oscillation_events > 0:
            violations.append(
                SafetyViolation(
                    violation_id=f"mcea-oscillation-{int(time.time())}",
                    violation_type="arousal_runaway",
                    threat_level=ThreatLevel.MEDIUM,
                    timestamp=time.time(),
                    description=(
                        f"MCEA arousal oscillation detected ({oscillation_events} events)"
                    ),
                    metrics={
                        "arousal_variance": mcea.get("arousal_variance", 0.0),
                        "threshold": 0.15,
                    },
                    source_component="mcea_controller",
                )
            )

        # Check invalid needs
        invalid_needs = mcea.get("invalid_needs_count", 0)
        if invalid_needs > 5:  # Threshold: >5 invalid inputs
            violations.append(
                SafetyViolation(
                    violation_id=f"mcea-invalid-{int(time.time())}",
                    violation_type="unexpected_behavior",
                    threat_level=ThreatLevel.MEDIUM,
                    timestamp=time.time(),
                    description=f"MCEA receiving invalid needs ({invalid_needs} rejected)",
                    metrics={"invalid_needs_count": invalid_needs, "threshold": 5.0},
                    source_component="mcea_controller",
                )
            )

        return violations
