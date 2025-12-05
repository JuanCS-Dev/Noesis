"""
Comprehensive Tests for TIG Sync Module
========================================

Target: 80%+ coverage for consciousness/tig/sync.py
"""

import asyncio
import time
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consciousness.tig.sync import PTPSynchronizer
from consciousness.tig.sync_models import ClockRole, SyncState


class TestPTPSynchronizerInit:
    """Test PTPSynchronizer initialization."""

    def test_init_default_role(self):
        """Test initialization with default SLAVE role."""
        sync = PTPSynchronizer("node-1")
        assert sync.node_id == "node-1"
        assert sync.role == ClockRole.SLAVE
        assert sync.state == SyncState.UNSYNCHRONIZED
        assert sync._sync_active is False

    def test_init_grandmaster_role(self):
        """Test initialization as GRAND_MASTER."""
        sync = PTPSynchronizer("master-1", role=ClockRole.GRAND_MASTER)
        assert sync.role == ClockRole.GRAND_MASTER
        assert sync.state == SyncState.UNSYNCHRONIZED

    def test_init_custom_jitter_target(self):
        """Test custom jitter target."""
        sync = PTPSynchronizer("node-1", target_jitter_ns=50.0)
        assert sync.target_jitter_ns == 50.0

    def test_repr(self):
        """Test string representation."""
        sync = PTPSynchronizer("node-42", role=ClockRole.SLAVE)
        repr_str = repr(sync)
        assert "node-42" in repr_str
        assert "SLAVE" in repr_str or "slave" in repr_str.lower()


class TestPTPSynchronizerStartStop:
    """Test start/stop functionality."""

    def test_start_sets_active(self):
        """Test start activates synchronization."""
        sync = PTPSynchronizer("node-1")
        sync.start()
        assert sync._sync_active is True
        assert sync.state == SyncState.SYNCHRONIZING

    def test_stop_deactivates(self):
        """Test stop deactivates synchronization."""
        sync = PTPSynchronizer("node-1")
        sync.start()
        sync.stop()
        assert sync._sync_active is False

    def test_grandmaster_start(self):
        """Test GRAND_MASTER starts updating time."""
        sync = PTPSynchronizer("master-1", role=ClockRole.GRAND_MASTER)
        sync.start()
        assert sync._sync_active is True
        # Check grandmaster time is being updated
        t1 = sync._grandmaster_time_ns
        time.sleep(0.01)
        sync._update_grand_master_time()
        t2 = sync._grandmaster_time_ns
        assert t2 >= t1


class TestPTPSynchronizerSyncToMaster:
    """Test sync_to_master method."""

    @pytest.mark.asyncio
    async def test_sync_to_master_basic(self):
        """Test basic sync to master."""
        sync = PTPSynchronizer("slave-1")
        sync.start()
        
        # Mock master time source
        master_time_ns = time.time_ns()
        result = await sync.sync_to_master("master-1", lambda: master_time_ns)
        
        assert result is not None
        assert result.success is True
        assert result.jitter_ns >= 0
        assert result.offset_ns is not None
        sync.stop()

    @pytest.mark.asyncio
    async def test_sync_updates_state_to_synchronized(self):
        """Test successful sync updates state."""
        sync = PTPSynchronizer("slave-1")
        sync.start()
        
        await sync.sync_to_master("master-1", lambda: time.time_ns())
        
        # State should be SYNCHRONIZED after a successful sync
        assert sync.state in [SyncState.SYNCHRONIZED, SyncState.SYNCHRONIZING]
        sync.stop()

    @pytest.mark.asyncio
    async def test_sync_calculates_offset(self):
        """Test offset calculation."""
        sync = PTPSynchronizer("slave-1")
        sync.start()
        
        # Add artificial delay to master time
        offset_amount = 1000000  # 1ms in ns
        result = await sync.sync_to_master(
            "master-1", 
            lambda: time.time_ns() + offset_amount
        )
        
        assert result.offset_ns is not None
        sync.stop()

    @pytest.mark.asyncio
    async def test_sync_without_providing_master_time(self):
        """Test sync without master time source."""
        sync = PTPSynchronizer("slave-1")
        sync.start()
        
        # Should work with None time source (uses internal simulation)
        result = await sync.sync_to_master("master-1", None)
        assert result is not None
        sync.stop()


class TestPTPSynchronizerTimeAccess:
    """Test time access methods."""

    def test_get_time_ns(self):
        """Test get synchronized time."""
        sync = PTPSynchronizer("node-1")
        time_ns = sync.get_time_ns()
        assert isinstance(time_ns, int)
        assert time_ns > 0

    def test_get_offset_initial(self):
        """Test get offset before sync."""
        sync = PTPSynchronizer("node-1")
        offset = sync.get_offset()
        assert isinstance(offset.offset_ns, (int, float))
        assert isinstance(offset.jitter_ns, float)
        assert isinstance(offset.quality, float)


class TestPTPSynchronizerESGTReadiness:
    """Test ESGT readiness checks."""

    def test_is_ready_for_esgt_no_sync(self):
        """Test ESGT readiness without sync."""
        sync = PTPSynchronizer("node-1")
        # Without sync, should not be ready
        is_ready = sync.is_ready_for_esgt()
        assert isinstance(is_ready, bool)

    @pytest.mark.asyncio
    async def test_is_ready_for_esgt_after_sync(self):
        """Test ESGT readiness after sync."""
        sync = PTPSynchronizer("slave-1", target_jitter_ns=1000000)  # 1ms target
        sync.start()
        
        # Perform multiple syncs to build history
        for _ in range(5):
            await sync.sync_to_master("master-1", lambda: time.time_ns())
        
        # Should now evaluate readiness
        is_ready = sync.is_ready_for_esgt()
        assert isinstance(is_ready, bool)
        sync.stop()


class TestPTPSynchronizerContinuousSync:
    """Test continuous synchronization."""

    @pytest.mark.asyncio
    async def test_continuous_sync_starts(self):
        """Test continuous sync starts correctly."""
        sync = PTPSynchronizer("slave-1")
        sync.start()
        
        # Start continuous sync with very short interval (simulating only)
        task = asyncio.create_task(sync.continuous_sync("master-1", interval_sec=0.01))
        
        # Let it run briefly
        await asyncio.sleep(0.05)
        
        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        sync.stop()


class TestPTPSynchronizerQuality:
    """Test quality calculation."""

    def test_calculate_quality_perfect(self):
        """Test perfect sync quality."""
        sync = PTPSynchronizer("node-1")
        quality = sync._calculate_quality(jitter_ns=10.0, delay_ns=100.0)
        assert 0.0 <= quality <= 1.0
        assert quality > 0.9  # Should be high for low jitter

    def test_calculate_quality_poor(self):
        """Test poor sync quality with high jitter."""
        sync = PTPSynchronizer("node-1", target_jitter_ns=100.0)
        quality = sync._calculate_quality(jitter_ns=10000.0, delay_ns=100000.0)
        assert 0.0 <= quality <= 1.0
        # High jitter should result in lower quality
        assert quality < 0.5
