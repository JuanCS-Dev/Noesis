"""Salience Detector Models - Data structures for salience detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from consciousness.esgt.coordinator import SalienceScore


class SalienceMode(Enum):
    """Operating mode for salience detection."""

    PASSIVE = "passive"  # Only compute when asked
    ACTIVE = "active"  # Continuously monitor and alert


@dataclass
class SalienceThresholds:
    """Thresholds for salience classification."""

    low_threshold: float = 0.30  # Below: unconscious processing
    medium_threshold: float = 0.50  # Peripheral awareness
    high_threshold: float = 0.70  # Conscious access (ESGT trigger)
    critical_threshold: float = 0.90  # Immediate priority


@dataclass
class SalienceDetectorConfig:
    """Configuration for salience detection."""

    mode: SalienceMode = SalienceMode.ACTIVE
    update_interval_ms: float = 50.0  # 20 Hz monitoring

    # Weights (must sum to 1.0)
    novelty_weight: float = 0.4
    relevance_weight: float = 0.4
    urgency_weight: float = 0.2

    thresholds: SalienceThresholds = field(default_factory=SalienceThresholds)

    # Novelty detection
    novelty_baseline_window: int = 50
    novelty_change_threshold: float = 0.15

    # Relevance computation
    default_relevance: float = 0.5

    # Urgency computation
    urgency_decay_rate: float = 0.1  # Per second
    urgency_boost_on_error: float = 0.3

    # History
    max_history_size: int = 100


@dataclass
class SalienceEvent:
    """Record of a high-salience detection."""

    timestamp: float
    salience: SalienceScore
    source: str
    content: dict[str, Any]
    threshold_exceeded: float
