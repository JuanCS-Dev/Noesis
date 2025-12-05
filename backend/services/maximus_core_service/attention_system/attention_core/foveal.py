"""Foveal Analyzer.

Deep, expensive analysis for high-salience targets.
Applies full analytical power when peripheral monitor detects
something worth investigating. Goal: <100ms saccade latency.
"""

from __future__ import annotations

import logging
import time
from collections import deque

from .models import FovealAnalysis, PeripheralDetection

logger = logging.getLogger(__name__)


class FovealAnalyzer:
    """Deep, expensive analysis for high-salience targets.

    Attributes:
        analysis_history: Recent analysis history.
        total_analyses: Total number of analyses performed.
        total_analysis_time_ms: Cumulative analysis time in milliseconds.
    """

    def __init__(self) -> None:
        """Initialize foveal analyzer."""
        self.analysis_history: deque = deque(maxlen=500)
        self.total_analyses = 0
        self.total_analysis_time_ms = 0.0

    async def deep_analyze(
        self, target: PeripheralDetection, full_data: dict | None = None
    ) -> FovealAnalysis:
        """Perform deep analysis on a high-salience target.

        Args:
            target: Detection from peripheral monitor.
            full_data: Complete data for deep analysis (optional).

        Returns:
            FovealAnalysis with detailed findings.
        """
        analysis_start = time.time()

        try:
            logger.info(
                f"Foveal analysis: {target.target_id} ({target.detection_type})"
            )

            if target.detection_type == "statistical_anomaly":
                findings = await self._analyze_statistical_anomaly(target, full_data)
            elif target.detection_type == "entropy_change":
                findings = await self._analyze_entropy_change(target, full_data)
            elif target.detection_type == "volume_spike":
                findings = await self._analyze_volume_spike(target, full_data)
            else:
                findings = await self._generic_deep_analysis(target, full_data)

            threat_level = self._assess_threat_level(findings)
            actions = self._generate_actions(threat_level, findings)

            analysis_time = (time.time() - analysis_start) * 1000

            analysis = FovealAnalysis(
                target_id=target.target_id,
                threat_level=threat_level,
                confidence=target.confidence,
                findings=findings,
                analysis_time_ms=analysis_time,
                timestamp=time.time(),
                recommended_actions=actions,
            )

            self.total_analyses += 1
            self.total_analysis_time_ms += analysis_time
            self.analysis_history.append(analysis)

            if analysis_time > 100:
                logger.warning(
                    f"Foveal analysis slow: {analysis_time:.1f}ms (target <100ms)"
                )

            logger.info(
                f"Foveal complete: {target.target_id} -> "
                f"{threat_level} ({analysis_time:.1f}ms)"
            )

            return analysis

        except Exception as e:
            logger.error(f"Foveal analysis error: {e}")

            return FovealAnalysis(
                target_id=target.target_id,
                threat_level="UNKNOWN",
                confidence=0.0,
                findings=[{"error": str(e)}],
                analysis_time_ms=(time.time() - analysis_start) * 1000,
                timestamp=time.time(),
                recommended_actions=["ESCALATE_TO_HUMAN"],
            )

    async def _analyze_statistical_anomaly(
        self, target: PeripheralDetection, full_data: dict | None
    ) -> list[dict]:
        """Analyze statistical anomaly in detail."""
        findings = []
        z_score = target.metadata.get("z_score", 0)

        findings.append({
            "type": "statistical_deviation",
            "severity": "HIGH" if z_score > 5 else "MEDIUM",
            "details": f"Z-score: {z_score:.2f} (p < 0.001)",
            "value": target.metadata.get("value"),
            "expected_range": (
                f"{target.metadata.get('mean', 0):.2f} ± "
                f"{target.metadata.get('std', 0):.2f}"
            ),
        })

        if z_score > 6:
            findings.append({
                "type": "potential_attack",
                "severity": "CRITICAL",
                "details": (
                    "Extreme deviation suggests possible attack or critical failure"
                ),
            })

        return findings

    async def _analyze_entropy_change(
        self, target: PeripheralDetection, full_data: dict | None
    ) -> list[dict]:
        """Analyze entropy change in detail."""
        findings = []

        current_entropy = target.metadata.get("current_entropy", 0)
        baseline_entropy = target.metadata.get("baseline_entropy", 0)
        deviation = target.metadata.get("deviation", 0)

        findings.append({
            "type": "entropy_anomaly",
            "severity": "HIGH" if deviation > 0.5 else "MEDIUM",
            "details": f"Entropy changed by {deviation * 100:.1f}%",
            "current": current_entropy,
            "baseline": baseline_entropy,
        })

        if current_entropy < 2.0:
            findings.append({
                "type": "low_entropy",
                "severity": "MEDIUM",
                "details": (
                    "Low entropy may indicate encrypted/compressed data "
                    "or homogeneous traffic"
                ),
            })

        if current_entropy > 7.0:
            findings.append({
                "type": "high_entropy",
                "severity": "MEDIUM",
                "details": (
                    "High entropy may indicate encrypted traffic "
                    "or randomized attacks"
                ),
            })

        return findings

    async def _analyze_volume_spike(
        self, target: PeripheralDetection, full_data: dict | None
    ) -> list[dict]:
        """Analyze volume spike in detail."""
        findings = []

        spike_factor = target.metadata.get("spike_factor", 0)
        current_rate = target.metadata.get("current_rate", 0)

        findings.append({
            "type": "volume_anomaly",
            "severity": "CRITICAL" if spike_factor > 10 else "HIGH",
            "details": f"Traffic volume increased {spike_factor:.1f}x baseline",
            "current_rate": current_rate,
            "spike_factor": spike_factor,
        })

        if spike_factor > 10:
            findings.append({
                "type": "ddos_indicator",
                "severity": "CRITICAL",
                "details": "Extreme volume spike consistent with DDoS attack",
            })

        return findings

    async def _generic_deep_analysis(
        self, target: PeripheralDetection, full_data: dict | None
    ) -> list[dict]:
        """Generic deep analysis fallback."""
        return [{
            "type": "generic_analysis",
            "severity": "MEDIUM",
            "details": f"Detection: {target.detection_type}",
            "confidence": target.confidence,
        }]

    def _assess_threat_level(self, findings: list[dict]) -> str:
        """Assess overall threat level from findings.

        Returns:
            Threat level: BENIGN, SUSPICIOUS, MALICIOUS, or CRITICAL.
        """
        if not findings:
            return "BENIGN"

        severities = [f.get("severity", "LOW") for f in findings]
        severity_counts = {
            "CRITICAL": severities.count("CRITICAL"),
            "HIGH": severities.count("HIGH"),
            "MEDIUM": severities.count("MEDIUM"),
        }

        if severity_counts["CRITICAL"] > 0:
            return "CRITICAL"
        if severity_counts["HIGH"] >= 2:
            return "MALICIOUS"
        if severity_counts["HIGH"] >= 1 or severity_counts["MEDIUM"] >= 3:
            return "SUSPICIOUS"
        return "BENIGN"

    def _generate_actions(
        self, threat_level: str, findings: list[dict]
    ) -> list[str]:
        """Generate recommended actions based on threat level."""
        actions = []

        if threat_level == "CRITICAL":
            actions.extend([
                "ACTIVATE_INCIDENT_RESPONSE",
                "ALERT_SECURITY_TEAM",
                "ENABLE_CIRCUIT_BREAKER",
                "ISOLATE_AFFECTED_SERVICES",
            ])
        elif threat_level == "MALICIOUS":
            actions.extend([
                "ALERT_SECURITY_TEAM",
                "INCREASE_MONITORING",
                "PREPARE_COUNTERMEASURES",
            ])
        elif threat_level == "SUSPICIOUS":
            actions.extend([
                "INCREASE_MONITORING",
                "LOG_DETAILED_EVIDENCE",
                "NOTIFY_ON_CALL",
            ])
        else:
            actions.append("CONTINUE_MONITORING")

        return actions

    def get_average_analysis_time(self) -> float:
        """Get average foveal analysis time in milliseconds."""
        if self.total_analyses == 0:
            return 0.0
        return self.total_analysis_time_ms / self.total_analyses
