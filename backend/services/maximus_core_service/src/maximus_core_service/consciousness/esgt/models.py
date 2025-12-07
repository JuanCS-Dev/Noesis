"""
ESGT Models
===========

Data models for ESGT (Evento de Sincronização Global Transitória) protocol.

This module contains dataclasses representing:
- Salience scoring for trigger evaluation
- Trigger conditions for ignition
- ESGT event lifecycle tracking
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .enums import ESGTPhase, SalienceLevel


@dataclass
class SalienceScore:
    """
    Multi-factor salience score determining ESGT trigger.

    Salience = α(Novelty) + β(Relevance) + γ(Urgency) + δ(Confidence)

    Where coefficients sum to 1.0 and are dynamically adjusted based
    on arousal state (MCEA) and attention parameters (acetylcholine).
    """

    novelty: float = 0.0  # 0-1, how unexpected
    relevance: float = 0.0  # 0-1, goal-alignment
    urgency: float = 0.0  # 0-1, time-criticality
    confidence: float = 1.0  # 0-1, prediction confidence (default: high confidence)

    # Weights (sum to 1.0)
    alpha: float = 0.25  # Novelty weight
    beta: float = 0.30  # Relevance weight
    gamma: float = 0.30  # Urgency weight
    delta: float = 0.15  # Confidence weight

    def compute_total(self) -> float:
        """Compute weighted salience score."""
        return (
            self.alpha * self.novelty
            + self.beta * self.relevance
            + self.gamma * self.urgency
            + self.delta * self.confidence
        )

    def get_level(self) -> SalienceLevel:
        """Classify salience level."""
        total = self.compute_total()
        if total < 0.25:
            return SalienceLevel.MINIMAL
        if total < 0.50:
            return SalienceLevel.LOW
        if total < 0.75:
            return SalienceLevel.MEDIUM
        if total < 0.85:
            return SalienceLevel.HIGH
        return SalienceLevel.CRITICAL


@dataclass
class TriggerConditions:
    """
    Conditions required for ESGT initiation.

    All conditions must be met for ignition to proceed. This prevents
    pathological synchronization and ensures computational resources
    are available.
    """

    # Salience threshold
    min_salience: float = 0.60  # Typical threshold for consciousness

    # Resource requirements
    max_tig_latency_ms: float = 5.0  # TIG must be responsive
    min_available_nodes: int = 8  # Minimum participating nodes
    min_cpu_capacity: float = 0.40  # 40% CPU available

    # Temporal gating
    refractory_period_ms: float = 200.0  # Minimum time between ESGTs
    max_esgt_frequency_hz: float = 5.0  # Maximum sustained rate

    # Arousal requirement (from MCEA)
    min_arousal_level: float = 0.40  # Minimum epistemic openness

    def check_salience(self, score: SalienceScore) -> bool:
        """Check if salience exceeds threshold."""
        return score.compute_total() >= self.min_salience

    def check_resources(
        self, tig_latency_ms: float, available_nodes: int, cpu_capacity: float
    ) -> bool:
        """Check if computational resources are adequate."""
        return (
            tig_latency_ms <= self.max_tig_latency_ms
            and available_nodes >= self.min_available_nodes
            and cpu_capacity >= self.min_cpu_capacity
        )

    def check_temporal_gating(
        self, time_since_last_esgt: float, recent_esgt_count: int, time_window: float = 1.0
    ) -> bool:
        """Check if temporal constraints are satisfied."""
        # Refractory period
        if time_since_last_esgt < (self.refractory_period_ms / 1000.0):
            return False

        # Frequency limit
        recent_rate = recent_esgt_count / time_window
        if recent_rate >= self.max_esgt_frequency_hz:
            return False

        return True

    def check_arousal(self, arousal_level: float) -> bool:
        """Check if arousal is sufficient."""
        return arousal_level >= self.min_arousal_level


@dataclass
class ESGTEvent:
    """
    Represents a single transient global synchronization event.

    This is the computational analog of a conscious moment - a discrete
    episode where distributed information becomes unified, globally
    accessible, and reportable.
    """

    event_id: str
    timestamp_start: float
    timestamp_end: float | None = None

    # Content
    content: dict[str, Any] = field(default_factory=dict)
    content_source: str = ""  # SPM that contributed content

    # Participants
    participating_nodes: set[str] = field(default_factory=set)
    node_count: int = 0

    # Synchronization metrics
    target_coherence: float = 0.70
    achieved_coherence: float = 0.0
    coherence_history: list[float] = field(default_factory=list)
    time_to_sync_ms: float | None = None

    # Phase information
    current_phase: ESGTPhase = ESGTPhase.IDLE
    phase_transitions: list[tuple[ESGTPhase, float]] = field(default_factory=list)

    # Performance metrics
    prepare_latency_ms: float = 0.0
    sync_latency_ms: float = 0.0
    broadcast_latency_ms: float = 0.0
    total_duration_ms: float = 0.0

    # Outcome
    success: bool = False
    failure_reason: str | None = None

    def transition_phase(self, new_phase: ESGTPhase) -> None:
        """Record phase transition."""
        timestamp = time.time()
        self.phase_transitions.append((new_phase, timestamp))
        self.current_phase = new_phase

    def finalize(self, success: bool, reason: str | None = None) -> None:
        """Mark event as complete."""
        self.timestamp_end = time.time()
        self.success = success
        self.failure_reason = reason

        if self.timestamp_start:
            self.total_duration_ms = (self.timestamp_end - self.timestamp_start) * 1000

    def get_duration_ms(self) -> float:
        """Get event duration in milliseconds."""
        if self.timestamp_end:
            return (self.timestamp_end - self.timestamp_start) * 1000
        return (time.time() - self.timestamp_start) * 1000

    def was_successful(self) -> bool:
        """Check if event achieved conscious-level coherence."""
        # SINGULARIDADE: Convert to native bool for JSON serialization (numpy.bool_ fix)
        return bool(self.success and self.achieved_coherence >= self.target_coherence)
