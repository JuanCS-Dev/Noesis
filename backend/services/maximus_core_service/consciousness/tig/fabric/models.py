"""
TIG Fabric Models - Data structures and enums
===============================================

This module contains all data classes and enums used throughout the TIG fabric.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeState(Enum):
    """Operational state of a TIG node."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    ESGT_MODE = "esgt_mode"  # High-coherence mode during global sync events
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass
class TIGConnection:
    """
    Represents a bidirectional link between TIG nodes.

    This connection model mirrors synaptic connections in biological neural
    networks, with dynamic weights representing connection strength/importance.
    """

    remote_node_id: str
    bandwidth_bps: int = 10_000_000_000  # 10 Gbps default
    latency_us: float = 1.0  # microseconds
    packet_loss: float = 0.0  # 0.0-1.0
    active: bool = True
    weight: float = 1.0  # Dynamic routing weight (modulated by importance)

    def get_effective_capacity(self) -> float:
        """
        Compute effective capacity considering packet loss and latency.

        Returns:
            Effective capacity in bps, adjusted for quality metrics
        """
        if not self.active:
            return 0.0

        # Account for retransmissions due to packet loss
        loss_factor = 1.0 - self.packet_loss

        # Latency penalty (higher latency reduces effective throughput)
        latency_factor = 1.0 / (1.0 + self.latency_us / 1000.0)

        return self.bandwidth_bps * loss_factor * latency_factor * self.weight


@dataclass
class NodeHealth:
    """
    Health status tracking for a TIG node.

    This enables fault tolerance by monitoring node failures and
    triggering isolation/recovery as needed.

    FASE VII (Safety Hardening):
    Added for production-grade fault tolerance and graceful degradation.
    """

    node_id: str
    last_seen: float = field(default_factory=time.time)
    failures: int = 0
    isolated: bool = False
    degraded: bool = False

    def is_healthy(self) -> bool:
        """Check if node is considered healthy."""
        return not self.isolated and not self.degraded and self.failures < 3


class CircuitBreaker:
    """
    Circuit breaker for TIG node communication.

    Implements the circuit breaker pattern to prevent cascading failures:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold exceeded, requests blocked
    - HALF_OPEN: Recovery attempt, limited requests allowed

    FASE VII (Safety Hardening):
    Critical component for fault isolation and system stability.
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state = "closed"  # closed, open, half_open
        self.failures = 0
        self.last_failure_time: float | None = None

    def is_open(self) -> bool:
        """
        Check if circuit breaker is open (blocking calls).

        Returns:
            True if open and blocking, False otherwise
        """
        if self.state == "open":
            # Check if recovery timeout elapsed
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time > self.recovery_timeout
            ):
                self.state = "half_open"
                return False
            return True
        return False

    def record_success(self):
        """Record successful operation."""
        if self.state == "half_open":
            # Recovery successful - close the breaker
            self.state = "closed"
            self.failures = 0

    def record_failure(self):
        """Record failed operation."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.open()

    def open(self):
        """Open circuit breaker (block calls)."""
        self.state = "open"

    def __repr__(self) -> str:
        return f"CircuitBreaker(state={self.state}, failures={self.failures})"


@dataclass
class ProcessingState:
    """
    Encapsulates the current computational state of a TIG node.

    This state representation enables consciousness-relevant metrics:
    - Attention level: resource allocation for salient information
    - Load metrics: computational capacity and utilization
    - Phase sync: oscillatory synchronization for ESGT coherence
    """

    active_modules: list[str] = field(default_factory=list)
    attention_level: float = 0.5  # 0.0-1.0, modulated by acetylcholine
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0

    # Oscillatory phase for synchronization (complex number representation)
    # Phase coherence across nodes is critical for ESGT ignition
    phase_sync: complex = complex(1.0, 0.0)

    # Information content currently being processed
    processing_content: dict[str, Any] | None = None
