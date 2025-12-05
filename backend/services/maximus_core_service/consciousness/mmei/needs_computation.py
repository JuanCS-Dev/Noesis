"""
MMEI Needs Computation - Physical to Abstract Translation
==========================================================

This module implements the core interoception computation - translating
physical/computational metrics into abstract phenomenal needs.

Theoretical Foundation:
-----------------------
This is the computational analog of biological interoception, where:
- Sensory signals (glucose, temperature, pressure) are integrated
- In cortical regions (insula, anterior cingulate)
- To produce phenomenal experiences (hunger, fatigue, discomfort)

MMEI performs similar translation:
- Physical metrics (CPU, memory, errors) are collected
- Processed through need computation algorithms
- To produce abstract needs (rest, repair, efficiency)

The result is a "feeling" state that can drive autonomous behavior.

Implementation Notes:
---------------------
- Need values normalized to [0, 1] range
- Multiple physical signals contribute to each need
- Weighted combinations and thresholds determine need levels
- Curiosity drive accumulates during idle periods
"""

from __future__ import annotations

import time

import numpy as np

from consciousness.mmei.models import (
    AbstractNeeds,
    InteroceptionConfig,
    PhysicalMetrics,
)


class NeedsComputation:
    """
    Computes abstract needs from physical metrics.

    This class encapsulates the interoception computation logic,
    translating raw physical/computational state into phenomenal
    "feeling" states.

    The computation maintains state for:
    - Curiosity accumulation (grows during idle periods)
    - Historical context (for future moving average support)
    """

    def __init__(self, config: InteroceptionConfig):
        """
        Initialize needs computation engine.

        Args:
            config: Configuration for need computation
        """
        self.config = config

        # Curiosity state
        self._accumulated_curiosity: float = 0.0
        self._last_curiosity_reset: float = time.time()

    def compute_needs(self, metrics: PhysicalMetrics) -> AbstractNeeds:
        """
        Translate physical metrics to abstract needs.

        This is the core interoception computation - the phenomenal
        translation from physical state to "feeling".

        Args:
            metrics: Current PhysicalMetrics

        Returns:
            AbstractNeeds computed from metrics
        """
        # REST NEED: Computational load/fatigue
        # Weighted combination of CPU and memory pressure
        rest_need = (
            self.config.cpu_weight * metrics.cpu_usage_percent
            + self.config.memory_weight * metrics.memory_usage_percent
        )

        # REPAIR NEED: Error rate and system integrity
        # Normalize error rate to [0, 1] using critical threshold
        error_rate_normalized = min(
            metrics.error_rate_per_min / self.config.error_rate_critical, 1.0
        )

        # Exception count contributes (saturates at 10 exceptions)
        exception_contribution = min(metrics.exception_count / 10.0, 1.0)

        repair_need = max(error_rate_normalized, exception_contribution)

        # EFFICIENCY NEED: Thermal and power state
        efficiency_need = self._compute_efficiency_need(metrics)

        # CONNECTIVITY NEED: Network state
        connectivity_need = self._compute_connectivity_need(metrics)

        # CURIOSITY DRIVE: Idle time → exploration urge
        curiosity_drive = self._compute_curiosity_drive(metrics)

        # LEARNING DRIVE: Low throughput → seek new patterns
        learning_drive = self._compute_learning_drive(metrics)

        return AbstractNeeds(
            rest_need=float(np.clip(rest_need, 0.0, 1.0)),
            repair_need=float(np.clip(repair_need, 0.0, 1.0)),
            efficiency_need=float(np.clip(efficiency_need, 0.0, 1.0)),
            connectivity_need=float(np.clip(connectivity_need, 0.0, 1.0)),
            curiosity_drive=float(np.clip(curiosity_drive, 0.0, 1.0)),
            learning_drive=float(np.clip(learning_drive, 0.0, 1.0)),
            timestamp=time.time(),
        )

    def _compute_efficiency_need(self, metrics: PhysicalMetrics) -> float:
        """
        Compute efficiency need from thermal and power metrics.

        Args:
            metrics: Current PhysicalMetrics

        Returns:
            Efficiency need value [0-1]
        """
        efficiency_need = 0.0

        if metrics.temperature_celsius is not None:
            # Temperature above warning threshold elevates efficiency need
            if metrics.temperature_celsius > self.config.temperature_warning_celsius:
                temp_excess = metrics.temperature_celsius - self.config.temperature_warning_celsius
                temp_contribution = min(temp_excess / 20.0, 1.0)  # Saturate at +20°C
                efficiency_need = max(efficiency_need, temp_contribution)

        if metrics.power_draw_watts is not None:
            # High power draw (>100W as baseline) elevates efficiency need
            if metrics.power_draw_watts > 100.0:
                power_contribution = min((metrics.power_draw_watts - 100.0) / 100.0, 1.0)
                efficiency_need = max(efficiency_need, power_contribution)

        return efficiency_need

    def _compute_connectivity_need(self, metrics: PhysicalMetrics) -> float:
        """
        Compute connectivity need from network metrics.

        Args:
            metrics: Current PhysicalMetrics

        Returns:
            Connectivity need value [0-1]
        """
        # Latency above warning threshold
        latency_contribution = 0.0
        if metrics.network_latency_ms > self.config.latency_warning_ms:
            latency_excess = metrics.network_latency_ms - self.config.latency_warning_ms
            latency_contribution = min(latency_excess / 100.0, 1.0)  # Saturate at +100ms

        # Packet loss
        packet_loss_contribution = metrics.packet_loss_percent

        return max(latency_contribution, packet_loss_contribution)

    def _compute_curiosity_drive(self, metrics: PhysicalMetrics) -> float:
        """
        Compute curiosity drive from idle time.

        Curiosity accumulates when CPU is idle, creating exploration urge.

        Args:
            metrics: Current PhysicalMetrics

        Returns:
            Curiosity drive value [0-1]
        """
        # When CPU is idle, curiosity accumulates over time
        if metrics.idle_time_percent > self.config.idle_curiosity_threshold:
            # Curiosity grows when idle
            self._accumulated_curiosity = min(
                self._accumulated_curiosity + self.config.curiosity_growth_rate, 1.0
            )
        else:
            # Reset when active
            self._accumulated_curiosity = 0.0

        return self._accumulated_curiosity

    def _compute_learning_drive(self, metrics: PhysicalMetrics) -> float:
        """
        Compute learning drive from throughput.

        Low throughput suggests underutilization, creating opportunity to learn.

        Args:
            metrics: Current PhysicalMetrics

        Returns:
            Learning drive value [0-1]
        """
        # Inverse of throughput (normalized)
        # Low throughput suggests underutilization → opportunity to learn
        if metrics.throughput_ops_per_sec < 10.0:  # Arbitrary baseline
            return 0.5  # Moderate drive when throughput low
        else:
            return 0.1  # Low baseline drive

    def reset_curiosity(self) -> None:
        """Reset accumulated curiosity to zero."""
        self._accumulated_curiosity = 0.0
        self._last_curiosity_reset = time.time()

    def get_curiosity_state(self) -> dict[str, float]:
        """Get current curiosity state for debugging."""
        return {
            "accumulated_curiosity": self._accumulated_curiosity,
            "time_since_reset": time.time() - self._last_curiosity_reset,
        }
