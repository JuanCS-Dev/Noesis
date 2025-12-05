"""PTP Cluster - Manages cluster of PTP-synchronized nodes for consciousness emergence."""

from __future__ import annotations

from typing import Any

import numpy as np

from consciousness.tig.sync_models import ClockRole, SyncResult


class PTPCluster:
    """
    Manages a cluster of PTP-synchronized nodes for consciousness emergence.

    Coordinates multiple PTPSynchronizer instances to create a temporally
    coherent fabric necessary for ESGT ignition.
    """

    def __init__(self, target_jitter_ns: float = 100.0) -> None:
        # Late import to avoid circular dependency
        from consciousness.tig.sync import PTPSynchronizer

        self._synchronizer_class = PTPSynchronizer
        self.target_jitter_ns = target_jitter_ns
        self.synchronizers: dict[str, Any] = {}  # PTPSynchronizer instances
        self.grand_master_id: str | None = None

    async def add_grand_master(self, node_id: str) -> Any:
        """Add a grand master clock to the cluster."""
        if self.grand_master_id is not None:
            raise ValueError(f"Grand master already exists: {self.grand_master_id}")

        sync = self._synchronizer_class(
            node_id, role=ClockRole.GRAND_MASTER, target_jitter_ns=self.target_jitter_ns
        )
        await sync.start()

        self.synchronizers[node_id] = sync
        self.grand_master_id = node_id

        return sync

    async def add_slave(self, node_id: str) -> Any:
        """Add a slave node to the cluster."""
        sync = self._synchronizer_class(
            node_id, role=ClockRole.SLAVE, target_jitter_ns=self.target_jitter_ns
        )
        await sync.start()

        self.synchronizers[node_id] = sync

        return sync

    async def synchronize_all(self) -> dict[str, SyncResult]:
        """Synchronize all slave nodes to grand master."""
        if not self.grand_master_id:
            raise RuntimeError("No grand master configured")

        results = {}

        for node_id, sync in self.synchronizers.items():
            if sync.role == ClockRole.SLAVE:
                result = await sync.sync_to_master(self.grand_master_id)
                results[node_id] = result

        return results

    def is_esgt_ready(self) -> bool:
        """Check if all nodes have sufficient sync quality for ESGT."""
        if not self.grand_master_id:
            return False

        for sync in self.synchronizers.values():
            if sync.role == ClockRole.SLAVE:
                if not sync.is_ready_for_esgt():
                    return False

        return True

    def get_cluster_metrics(self) -> dict[str, Any]:
        """Get cluster-wide synchronization metrics."""
        offsets = []
        jitters = []
        ready_count = 0

        for sync in self.synchronizers.values():
            if sync.role == ClockRole.SLAVE:
                offset = sync.get_offset()
                offsets.append(abs(offset.offset_ns))
                jitters.append(offset.jitter_ns)
                if sync.is_ready_for_esgt():
                    ready_count += 1

        slave_count = sum(1 for s in self.synchronizers.values() if s.role == ClockRole.SLAVE)

        return {
            "node_count": len(self.synchronizers),
            "slave_count": slave_count,
            "esgt_ready_count": ready_count,
            "esgt_ready_percentage": (ready_count / slave_count * 100) if slave_count > 0 else 0,
            "max_offset_ns": max(offsets) if offsets else 0.0,
            "avg_offset_ns": float(np.mean(offsets)) if offsets else 0.0,
            "max_jitter_ns": max(jitters) if jitters else 0.0,
            "avg_jitter_ns": float(np.mean(jitters)) if jitters else 0.0,
            "target_jitter_ns": self.target_jitter_ns,
        }

    async def stop_all(self) -> None:
        """Stop all synchronizers."""
        for sync in self.synchronizers.values():
            await sync.stop()

    def __repr__(self) -> str:
        metrics = self.get_cluster_metrics()
        return (
            f"PTPCluster(nodes={metrics['node_count']}, "
            f"esgt_ready={metrics['esgt_ready_count']}/{metrics['slave_count']}, "
            f"avg_jitter={metrics['avg_jitter_ns']:.1f}ns)"
        )
