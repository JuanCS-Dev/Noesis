"""Attention System.

Two-tier attention system with peripheral/foveal processing.
Coordinates lightweight peripheral scanning with deep foveal analysis,
using salience scoring to allocate attention efficiently.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from typing import Any

from ..salience_scorer import SalienceScorer
from .foveal import FovealAnalyzer
from .models import FovealAnalysis
from .peripheral import PeripheralMonitor

logger = logging.getLogger(__name__)


class AttentionSystem:
    """Two-tier attention system with peripheral/foveal processing.

    Attributes:
        peripheral: Peripheral monitor for broad scanning.
        foveal: Foveal analyzer for deep analysis.
        salience_scorer: Scorer for attention allocation.
        running: Whether system is running.
        attention_log: Log of attention events.
    """

    def __init__(
        self, foveal_threshold: float = 0.6, scan_interval: float = 1.0
    ) -> None:
        """Initialize attention system.

        Args:
            foveal_threshold: Minimum salience score for foveal analysis.
            scan_interval: Peripheral scan interval in seconds.
        """
        self.peripheral = PeripheralMonitor(scan_interval_seconds=scan_interval)
        self.foveal = FovealAnalyzer()
        self.salience_scorer = SalienceScorer(foveal_threshold=foveal_threshold)

        self.running = False
        self.attention_log: deque = deque(maxlen=1000)

    async def monitor(
        self,
        data_sources: list[Callable[[], dict]],
        on_critical_finding: Callable[[FovealAnalysis], None] | None = None,
    ) -> None:
        """Continuous attention-driven monitoring.

        Args:
            data_sources: List of data source functions.
            on_critical_finding: Callback for critical findings.
        """
        self.running = True
        logger.info("Attention system started")

        while self.running:
            try:
                detections = await self.peripheral.scan_all(data_sources)
                logger.debug(f"Peripheral scan: {len(detections)} detections")

                scored_targets = []
                for detection in detections:
                    event = {
                        "id": detection.target_id,
                        "value": detection.confidence,
                        "metric": detection.detection_type,
                        "anomaly_score": detection.confidence,
                    }
                    salience = self.salience_scorer.calculate_salience(event)
                    scored_targets.append((detection, salience))

                foveal_analyses = []
                for detection, salience in scored_targets:
                    if salience.requires_foveal:
                        logger.info(
                            f"Foveal saccade: {detection.target_id} "
                            f"(salience={salience.score:.3f})"
                        )

                        analysis = await self.foveal.deep_analyze(detection)
                        foveal_analyses.append(analysis)

                        self.attention_log.append({
                            "timestamp": time.time(),
                            "target": detection.target_id,
                            "salience": salience.score,
                            "threat_level": analysis.threat_level,
                        })

                        if (
                            on_critical_finding
                            and analysis.threat_level == "CRITICAL"
                        ):
                            on_critical_finding(analysis)

                if foveal_analyses:
                    critical_count = sum(
                        1 for a in foveal_analyses if a.threat_level == "CRITICAL"
                    )
                    logger.info(
                        f"Attention cycle: {len(detections)} detections, "
                        f"{len(foveal_analyses)} foveal analyses, "
                        f"{critical_count} critical findings"
                    )

                await asyncio.sleep(self.peripheral.scan_interval)

            except Exception as e:
                logger.error(f"Attention system error: {e}", exc_info=True)
                await asyncio.sleep(self.peripheral.scan_interval)

        logger.info("Attention system stopped")

    async def stop(self) -> None:
        """Stop the attention system."""
        self.running = False
        logger.info("Attention system stop requested")

    def get_performance_stats(self) -> dict[str, Any]:
        """Get attention system performance statistics.

        Returns:
            Dictionary with performance metrics.
        """
        return {
            "peripheral": {
                "detections_total": len(self.peripheral.detection_history)
            },
            "foveal": {
                "analyses_total": self.foveal.total_analyses,
                "avg_analysis_time_ms": self.foveal.get_average_analysis_time(),
            },
            "attention": {
                "events_total": len(self.attention_log),
                "top_targets": self.salience_scorer.get_top_salient_targets(10),
            },
        }
