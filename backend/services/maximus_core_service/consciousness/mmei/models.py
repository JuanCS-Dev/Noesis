"""
MMEI Data Models - Data Classes and Enumerations
=================================================

This module contains all data structures used by MMEI interoception system:
- NeedUrgency: Classification of need urgency levels
- PhysicalMetrics: Raw system metrics
- AbstractNeeds: Phenomenal needs derived from metrics
- InteroceptionConfig: Configuration parameters
- Goal: Autonomous goals generated from needs

These models provide the foundation for translating physical/computational
state into abstract psychological needs.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum


class NeedUrgency(Enum):
    """Classification of need urgency levels."""

    SATISFIED = "satisfied"  # need < 0.20 - no action required
    LOW = "low"  # 0.20 ≤ need < 0.40 - background concern
    MODERATE = "moderate"  # 0.40 ≤ need < 0.60 - should address soon
    HIGH = "high"  # 0.60 ≤ need < 0.80 - requires attention
    CRITICAL = "critical"  # need ≥ 0.80 - immediate action needed


@dataclass
class PhysicalMetrics:
    """
    Raw physical/computational metrics collected from system.

    These are the "receptor signals" analogous to biological interoception.
    Values are normalized to [0, 1] range where possible.
    """

    # Computational load
    cpu_usage_percent: float = 0.0  # 0-100 → normalized to 0-1
    memory_usage_percent: float = 0.0  # 0-100 → normalized to 0-1

    # System health
    error_rate_per_min: float = 0.0  # Errors detected per minute
    exception_count: int = 0  # Recent exceptions

    # Physical state (if available)
    temperature_celsius: float | None = None  # CPU/system temp
    power_draw_watts: float | None = None  # Power consumption

    # Network state
    network_latency_ms: float = 0.0  # Average latency
    packet_loss_percent: float = 0.0  # 0-100 → normalized to 0-1

    # Activity level
    idle_time_percent: float = 0.0  # 0-100 → normalized to 0-1
    throughput_ops_per_sec: float = 0.0  # Operations processed

    # Metadata
    timestamp: float = field(default_factory=time.time)
    collection_latency_ms: float = 0.0  # Time to collect metrics

    def normalize(self) -> "PhysicalMetrics":
        """Ensure all percentage values are in [0, 1] range."""
        return PhysicalMetrics(
            cpu_usage_percent=min(self.cpu_usage_percent / 100.0, 1.0),
            memory_usage_percent=min(self.memory_usage_percent / 100.0, 1.0),
            error_rate_per_min=self.error_rate_per_min,
            exception_count=self.exception_count,
            temperature_celsius=self.temperature_celsius,
            power_draw_watts=self.power_draw_watts,
            network_latency_ms=self.network_latency_ms,
            packet_loss_percent=min(self.packet_loss_percent / 100.0, 1.0),
            idle_time_percent=min(self.idle_time_percent / 100.0, 1.0),
            throughput_ops_per_sec=self.throughput_ops_per_sec,
            timestamp=self.timestamp,
            collection_latency_ms=self.collection_latency_ms,
        )


@dataclass
class AbstractNeeds:
    """
    Abstract psychological/phenomenal needs derived from physical metrics.

    This is the "feeling" layer - the phenomenal experience of bodily state.
    All values normalized to [0, 1] where 1.0 = maximum need.

    Biological Correspondence:
    - rest_need: Fatigue sensation
    - repair_need: Pain/discomfort signaling damage
    - efficiency_need: Thermal discomfort, energy depletion
    - connectivity_need: Social isolation feeling
    - curiosity_drive: Boredom, exploration urge
    """

    # Primary needs (deficit-based)
    rest_need: float = 0.0  # Need to reduce computational load
    repair_need: float = 0.0  # Need to fix errors/integrity issues
    efficiency_need: float = 0.0  # Need to optimize resource usage
    connectivity_need: float = 0.0  # Need to improve communication

    # Growth needs (exploration-based)
    curiosity_drive: float = 0.0  # Drive to explore when idle
    learning_drive: float = 0.0  # Drive to acquire new patterns

    # Metadata
    timestamp: float = field(default_factory=time.time)

    def get_most_urgent(self) -> tuple[str, float, NeedUrgency]:
        """
        Get the most urgent need.

        Returns:
            (need_name, need_value, urgency_level)
        """
        needs = {
            "rest_need": self.rest_need,
            "repair_need": self.repair_need,
            "efficiency_need": self.efficiency_need,
            "connectivity_need": self.connectivity_need,
            "curiosity_drive": self.curiosity_drive,
            "learning_drive": self.learning_drive,
        }

        most_urgent_name = max(needs.keys(), key=lambda k: needs[k])
        most_urgent_value = needs[most_urgent_name]
        urgency = self._classify_urgency(most_urgent_value)

        return (most_urgent_name, most_urgent_value, urgency)

    def get_critical_needs(self, threshold: float = 0.80) -> list[tuple[str, float]]:
        """Get all needs above critical threshold."""
        needs = {
            "rest_need": self.rest_need,
            "repair_need": self.repair_need,
            "efficiency_need": self.efficiency_need,
            "connectivity_need": self.connectivity_need,
        }

        return [(name, value) for name, value in needs.items() if value >= threshold]

    def _classify_urgency(self, need_value: float) -> NeedUrgency:
        """Classify urgency level based on need value."""
        if need_value < 0.20:
            return NeedUrgency.SATISFIED
        if need_value < 0.40:
            return NeedUrgency.LOW
        if need_value < 0.60:
            return NeedUrgency.MODERATE
        if need_value < 0.80:
            return NeedUrgency.HIGH
        return NeedUrgency.CRITICAL

    def __repr__(self) -> str:
        most_urgent, value, urgency = self.get_most_urgent()
        return f"AbstractNeeds(most_urgent={most_urgent}={value:.2f}, urgency={urgency.value})"


@dataclass
class InteroceptionConfig:
    """Configuration for internal state monitoring."""

    # Collection intervals
    collection_interval_ms: float = 100.0  # 10 Hz default

    # Moving average windows
    short_term_window_samples: int = 10  # 1 second at 10 Hz
    long_term_window_samples: int = 50  # 5 seconds at 10 Hz

    # Need computation weights
    cpu_weight: float = 0.6  # CPU contributes 60% to rest_need
    memory_weight: float = 0.4  # Memory contributes 40% to rest_need

    # Thresholds
    error_rate_critical: float = 10.0  # 10 errors/min = critical
    temperature_warning_celsius: float = 80.0
    latency_warning_ms: float = 100.0

    # Curiosity parameters
    idle_curiosity_threshold: float = 0.70  # 70% idle → curiosity activates
    curiosity_growth_rate: float = 0.01  # Per-cycle curiosity increase when idle


@dataclass
class Goal:
    """
    Autonomous goal generated from abstract needs.

    Goals are the action layer - translating needs into concrete objectives
    that can be executed by downstream systems (HCL, ESGT).
    """

    goal_id: str  # Unique identifier
    need_source: str  # Which need generated this (e.g., "rest_need")
    description: str  # Human-readable goal description
    priority: NeedUrgency  # Urgency level
    need_value: float  # Need value that triggered goal (0-1)
    timestamp: float = field(default_factory=time.time)
    executed: bool = False

    def compute_hash(self) -> str:
        """Compute content hash for deduplication."""
        content = f"{self.need_source}:{self.description}:{self.priority.value}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def __repr__(self) -> str:
        return f"Goal({self.goal_id}, {self.need_source}, {self.priority.value})"


# FASE VII: Hard limits for MMEI safety
MAX_GOALS_PER_MINUTE = 5  # Hard limit on goal generation rate
MAX_ACTIVE_GOALS = 10  # Hard limit on concurrent active goals
MAX_GOAL_QUEUE_SIZE = 20  # Hard limit on goal queue size
GOAL_DEDUP_WINDOW_SECONDS = 60.0  # Deduplication window
