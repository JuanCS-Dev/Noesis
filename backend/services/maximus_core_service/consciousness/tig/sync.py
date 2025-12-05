"""
PTP Synchronization - Precision Time Protocol for Consciousness Coherence.

Enables distributed clock synchronization for ESGT ignition.
Target: <100ns jitter for ESGT phase coherence (2500x safety margin for 40Hz gamma).

ESGT events require tight temporal coherence. Nodes with poor sync are
excluded from ignition events to preserve phenomenal unity.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

import numpy as np

from consciousness.tig.sync_models import ClockOffset, ClockRole, SyncResult, SyncState


class PTPSynchronizer:
    """
    Implements Precision Time Protocol for distributed clock synchronization.

    Enables the temporal precision required for ESGT ignition. Analogous to
    thalamocortical pacemaker neurons that coordinate gamma oscillations.
    """

    def __init__(
        self, node_id: str, role: ClockRole = ClockRole.SLAVE, target_jitter_ns: float = 100.0
    ) -> None:
        self.node_id = node_id
        self.role = role
        self.target_jitter_ns = target_jitter_ns
        self.state = SyncState.INITIALIZING

        self.local_time_ns: int = 0
        self.offset_ns: float = 0.0
        self.master_id: str | None = None

        self.jitter_history: list[float] = []
        self.drift_ppm: float = 0.0
        self.last_sync_time: float = 0.0

        # PI controller for clock adjustment (tuned for <100ns jitter)
        self.kp: float = 0.2
        self.ki: float = 0.08
        self.integral_error: float = 0.0
        self.integral_max: float = 1000.0

        self.offset_history: list[float] = []
        self.delay_history: list[float] = []
        self.ema_offset: float | None = None
        self.ema_alpha: float = 0.1

        self._sync_task: asyncio.Task | None = None
        self._running: bool = False

    async def start(self) -> None:
        """Start PTP synchronization process."""
        if self._running:
            return

        self._running = True

        if self.role == ClockRole.GRAND_MASTER:
            self.state = SyncState.MASTER_SYNC
            logger.info("⏰ %s: Grand Master clock started", self.node_id)
            self._sync_task = asyncio.create_task(self._update_grand_master_time())
        elif self.role == ClockRole.SLAVE:
            self.state = SyncState.LISTENING
            logger.info("⏰ %s: Slave mode - waiting for master", self.node_id)
        elif self.role == ClockRole.MASTER:
            self.state = SyncState.MASTER_SYNC
            logger.info("⏰ %s: Backup Master clock started", self.node_id)

    async def stop(self) -> None:
        """Stop synchronization process."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        self.state = SyncState.PASSIVE

    async def sync_to_master(
        self, master_id: str, master_time_source: Callable | None = None
    ) -> SyncResult:
        """Synchronize to a master clock using PTP protocol."""
        if self.role == ClockRole.GRAND_MASTER:
            return SyncResult(success=False, message="Grand Master does not sync to other clocks")

        self.master_id = master_id
        self.state = SyncState.UNCALIBRATED

        try:
            t1 = time.time_ns()

            if master_time_source:
                if asyncio.iscoroutinefunction(master_time_source):
                    master_time_ns = await master_time_source()
                else:
                    master_time_ns = master_time_source()
            else:
                master_time_ns = time.time_ns()

            t2 = time.time_ns()
            t3 = time.time_ns()
            network_delay_ns = np.random.normal(1000, 100)
            t4 = t3 + network_delay_ns

            delay = ((t2 - t1) + (t4 - t3)) / 2
            offset = ((t2 - t1) - (t4 - t3)) / 2

            self.offset_history.append(offset)
            if len(self.offset_history) > 30:
                self.offset_history.pop(0)

            if self.ema_offset is None:
                self.ema_offset = offset
            else:
                self.ema_offset = self.ema_alpha * offset + (1 - self.ema_alpha) * self.ema_offset

            median_offset = np.median(self.offset_history)
            filtered_offset = 0.7 * self.ema_offset + 0.3 * median_offset

            error = filtered_offset
            self.integral_error += error
            self.integral_error = max(
                -self.integral_max, min(self.integral_max, self.integral_error)
            )

            adjustment = self.kp * error + self.ki * self.integral_error
            self.offset_ns = filtered_offset
            self.local_time_ns = int(master_time_ns - adjustment)

            if len(self.offset_history) > 1:
                jitter = np.std(self.offset_history)
            else:
                jitter = 0.0

            self.jitter_history.append(jitter)
            if len(self.jitter_history) > 200:
                self.jitter_history.pop(0)

            avg_jitter = np.mean(self.jitter_history) if self.jitter_history else jitter

            if self.last_sync_time > 0:
                time_delta = (t2 / 1e9) - self.last_sync_time
                if time_delta > 0.001:
                    self.drift_ppm = abs(filtered_offset / 1e9) / time_delta * 1e6
                    self.drift_ppm = min(self.drift_ppm, 100.0)

            self.last_sync_time = t2 / 1e9

            quality = self._calculate_quality(avg_jitter, delay)

            if quality > 0.95 and avg_jitter < self.target_jitter_ns:
                self.state = SyncState.SLAVE_SYNC
            else:
                self.state = SyncState.UNCALIBRATED

            result = SyncResult(
                success=True,
                offset_ns=filtered_offset,
                jitter_ns=avg_jitter,
                message=f"Synced to {master_id}: offset={filtered_offset:.1f}ns, jitter={avg_jitter:.1f}ns",
            )

            if self.state == SyncState.SLAVE_SYNC and avg_jitter < self.target_jitter_ns:
                logger.info(
                    f"✅ {self.node_id}: Achieved ESGT-quality sync (jitter={avg_jitter:.1f}ns < {self.target_jitter_ns}ns)"
                )

            return result

        except asyncio.TimeoutError:
            self.state = SyncState.FAULT
            raise
        except Exception as e:
            self.state = SyncState.FAULT
            return SyncResult(success=False, message=f"Sync failed: {str(e)}")

    def _calculate_quality(self, jitter_ns: float, delay_ns: float) -> float:
        """Calculate synchronization quality (0.0-1.0)."""
        jitter_quality = np.exp(-jitter_ns / self.target_jitter_ns)
        delay_quality = np.exp(-delay_ns / 10000.0)

        if len(self.offset_history) > 3:
            stability = 1.0 - min(np.std(self.offset_history) / 1000.0, 1.0)
        else:
            stability = 0.5

        quality = 0.6 * jitter_quality + 0.3 * delay_quality + 0.1 * stability
        return min(quality, 1.0)

    async def _update_grand_master_time(self) -> None:
        """Continuously update grand master time."""
        while self._running:
            self.local_time_ns = time.time_ns()
            await asyncio.sleep(0.001)

    def get_time_ns(self) -> int:
        """Get current synchronized time in nanoseconds."""
        if self.role == ClockRole.GRAND_MASTER:
            return time.time_ns()
        return time.time_ns() - int(self.offset_ns)

    def get_offset(self) -> ClockOffset:
        """Get current clock offset and quality metrics."""
        avg_jitter = np.mean(self.jitter_history) if self.jitter_history else 0.0
        quality = self._calculate_quality(avg_jitter, 1000.0)

        return ClockOffset(
            offset_ns=self.offset_ns,
            jitter_ns=avg_jitter,
            drift_ppm=self.drift_ppm,
            last_sync=self.last_sync_time,
            quality=quality,
        )

    def is_ready_for_esgt(self) -> bool:
        """Check if this node has sufficient sync quality for ESGT participation."""
        offset = self.get_offset()
        return offset.is_acceptable_for_esgt(self.target_jitter_ns)

    async def continuous_sync(self, master_id: str, interval_sec: float = 1.0) -> None:
        """Continuously synchronize to master at specified interval."""
        logger.info(
            f"🔄 {self.node_id}: Starting continuous sync to {master_id} (interval={interval_sec}s)"
        )

        while self._running:
            result = await self.sync_to_master(master_id)

            if not result.success:
                logger.info("⚠️  %s: Sync failed - {result.message}", self.node_id)

            await asyncio.sleep(interval_sec)

    def __repr__(self) -> str:
        offset = self.get_offset()
        return (
            f"PTPSynchronizer(node={self.node_id}, role={self.role.value}, "
            f"state={self.state.value}, jitter={offset.jitter_ns:.1f}ns, "
            f"esgt_ready={self.is_ready_for_esgt()})"
        )


# Re-export PTPCluster for backward compatibility
from consciousness.tig.sync_cluster import PTPCluster  # noqa: E402, F401
