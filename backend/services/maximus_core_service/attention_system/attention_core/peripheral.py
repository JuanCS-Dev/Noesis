"""Peripheral Monitor.

Lightweight, broad scanning of all system inputs.
Performs fast statistical checks to detect significant changes.
Goal: <100ms latency.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable

import numpy as np

from .models import PeripheralDetection

logger = logging.getLogger(__name__)


class PeripheralMonitor:
    """Lightweight, broad scanning of all system inputs.

    Performs fast, statistical checks to detect significant changes
    without deep analysis.

    Attributes:
        scan_interval: How often to scan in seconds.
        baseline_stats: Statistical baselines for each source.
        detection_history: Recent detection history.
        running: Whether monitor is running.
    """

    def __init__(self, scan_interval_seconds: float = 1.0) -> None:
        """Initialize peripheral monitor.

        Args:
            scan_interval_seconds: How often to scan (default 1s).
        """
        self.scan_interval = scan_interval_seconds
        self.baseline_stats: dict = {}
        self.detection_history: deque = deque(maxlen=1000)
        self.running = False

    async def scan_all(
        self, data_sources: list[Callable[[], dict]]
    ) -> list[PeripheralDetection]:
        """Scan all data sources for significant changes.

        Args:
            data_sources: List of functions that return current metrics.

        Returns:
            List of detections that warrant attention.
        """
        detections = []
        scan_start = time.time()

        try:
            tasks = [self._scan_source(source) for source in data_sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    detections.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Scan error: {result}")

            scan_time = (time.time() - scan_start) * 1000
            if scan_time > 100:
                logger.warning(
                    f"Peripheral scan slow: {scan_time:.1f}ms (target <100ms)"
                )

            logger.debug(
                f"Peripheral scan: {len(detections)} detections in {scan_time:.1f}ms"
            )

        except Exception as e:
            logger.error(f"Peripheral scan error: {e}")

        return detections

    async def _scan_source(
        self, source: Callable[[], dict]
    ) -> list[PeripheralDetection]:
        """Scan a single data source.

        Args:
            source: Function that returns current metrics.

        Returns:
            List of detections from this source.
        """
        detections = []

        try:
            data = source() if callable(source) else source

            if not data:
                return detections

            source_id = data.get("id", "unknown")

            statistical = self._detect_statistical_anomaly(source_id, data)
            if statistical:
                detections.append(statistical)

            entropy = self._detect_entropy_change(source_id, data)
            if entropy:
                detections.append(entropy)

            volume = self._detect_volume_spike(source_id, data)
            if volume:
                detections.append(volume)

        except Exception as e:
            logger.warning(f"Source scan error: {e}")

        return detections

    def _detect_statistical_anomaly(
        self, source_id: str, data: dict
    ) -> PeripheralDetection | None:
        """Detect statistical anomalies using Z-score.

        Returns detection if |z-score| > 3.0 (99.7% confidence).
        """
        try:
            value = data.get("value", 0)

            if source_id not in self.baseline_stats:
                self.baseline_stats[source_id] = {
                    "values": deque(maxlen=100),
                    "mean": value,
                    "std": 0.0,
                }
                return None

            baseline = self.baseline_stats[source_id]
            baseline["values"].append(value)

            values_array = np.array(baseline["values"])
            baseline["mean"] = np.mean(values_array)
            baseline["std"] = np.std(values_array)

            if baseline["std"] > 0:
                z_score = abs((value - baseline["mean"]) / baseline["std"])
            else:
                z_score = 0.0

            if z_score > 3.0:
                detection = PeripheralDetection(
                    target_id=f"{source_id}_statistical",
                    detection_type="statistical_anomaly",
                    confidence=min(z_score / 6.0, 1.0),
                    timestamp=time.time(),
                    metadata={
                        "z_score": z_score,
                        "value": value,
                        "mean": baseline["mean"],
                        "std": baseline["std"],
                    },
                )
                self.detection_history.append(detection)
                return detection

        except Exception as e:
            logger.debug(f"Statistical anomaly check error: {e}")

        return None

    def _detect_entropy_change(
        self, source_id: str, data: dict
    ) -> PeripheralDetection | None:
        """Detect significant entropy changes.

        Sudden changes in data distribution may indicate attacks or failures.
        """
        try:
            distribution = data.get("distribution", [])

            if not distribution or len(distribution) < 10:
                return None

            distribution = np.array(distribution)
            distribution = distribution / distribution.sum()
            entropy = -np.sum(distribution * np.log2(distribution + 1e-10))

            entropy_key = f"{source_id}_entropy"
            if entropy_key not in self.baseline_stats:
                self.baseline_stats[entropy_key] = {
                    "values": deque(maxlen=50),
                    "mean": entropy,
                }
                return None

            baseline = self.baseline_stats[entropy_key]
            baseline["values"].append(entropy)
            baseline["mean"] = np.mean(baseline["values"])

            if baseline["mean"] > 0:
                deviation = abs(entropy - baseline["mean"]) / baseline["mean"]

                if deviation > 0.30:
                    return PeripheralDetection(
                        target_id=f"{source_id}_entropy",
                        detection_type="entropy_change",
                        confidence=min(deviation / 0.60, 1.0),
                        timestamp=time.time(),
                        metadata={
                            "current_entropy": entropy,
                            "baseline_entropy": baseline["mean"],
                            "deviation": deviation,
                        },
                    )

        except Exception as e:
            logger.debug(f"Entropy check error: {e}")

        return None

    def _detect_volume_spike(
        self, source_id: str, data: dict
    ) -> PeripheralDetection | None:
        """Detect volume spikes (sudden increases in event rate).

        DDoS attacks, port scans, and failures often show volume spikes.
        """
        try:
            count = data.get("event_count", 0)
            time_window = data.get("time_window_seconds", 60)

            rate = count / time_window if time_window > 0 else 0

            rate_key = f"{source_id}_rate"
            if rate_key not in self.baseline_stats:
                self.baseline_stats[rate_key] = {
                    "values": deque(maxlen=100),
                    "mean": rate,
                    "p95": rate,
                }
                return None

            baseline = self.baseline_stats[rate_key]
            baseline["values"].append(rate)
            baseline["mean"] = np.mean(baseline["values"])
            baseline["p95"] = np.percentile(baseline["values"], 95)

            if baseline["mean"] > 0 and rate > baseline["mean"] * 5:
                return PeripheralDetection(
                    target_id=f"{source_id}_volume",
                    detection_type="volume_spike",
                    confidence=min((rate / baseline["mean"]) / 10.0, 1.0),
                    timestamp=time.time(),
                    metadata={
                        "current_rate": rate,
                        "baseline_rate": baseline["mean"],
                        "spike_factor": rate / baseline["mean"],
                    },
                )

        except Exception as e:
            logger.debug(f"Volume spike check error: {e}")

        return None
