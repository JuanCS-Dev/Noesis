"""PTP Synchronization Models - Data structures for clock synchronization."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class ClockRole(Enum):
    """Role of a node in PTP clock hierarchy."""

    GRAND_MASTER = "grand_master"  # Primary time source
    MASTER = "master"  # Backup time source
    SLAVE = "slave"  # Synchronized to master
    PASSIVE = "passive"  # Listening only


class SyncState(Enum):
    """Synchronization state of a node."""

    PASSIVE = "passive"
    INITIALIZING = "initializing"
    LISTENING = "listening"
    UNCALIBRATED = "uncalibrated"
    SLAVE_SYNC = "slave_sync"
    MASTER_SYNC = "master_sync"
    FAULT = "fault"


@dataclass
class ClockOffset:
    """Clock offset and quality metrics for ESGT temporal coherence."""

    offset_ns: float  # Nanoseconds offset from master
    jitter_ns: float  # Clock jitter (variation)
    drift_ppm: float  # Drift in parts-per-million
    last_sync: float  # Timestamp of last synchronization
    quality: float  # 0.0-1.0 sync quality

    def is_acceptable_for_esgt(
        self, threshold_ns: float = 1000.0, quality_threshold: float = 0.20
    ) -> bool:
        """Check if synchronization quality is sufficient for ESGT participation."""
        if self.drift_ppm > 1000.0:
            return False
        if abs(self.offset_ns) > 1_000_000:
            return False
        return self.jitter_ns < threshold_ns and self.quality > quality_threshold


@dataclass
class SyncResult:
    """Result of a synchronization operation."""

    success: bool
    offset_ns: float = 0.0
    jitter_ns: float = 0.0
    message: str = ""
    timestamp: float = field(default_factory=time.time)
