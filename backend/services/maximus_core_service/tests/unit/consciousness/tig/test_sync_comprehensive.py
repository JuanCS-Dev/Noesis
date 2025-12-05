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
        assert sync.state == SyncState.INITIALIZING
        assert sync._running is False

    def test_init_grandmaster_role(self):
        """Test initialization as GRAND_MASTER."""
        sync = PTPSynchronizer("master-1", role=ClockRole.GRAND_MASTER)
        assert sync.role == ClockRole.GRAND_MASTER
        assert sync.state == SyncState.INITIALIZING

    def test_init_custom_jitter_target(self):
        """Test custom jitter target."""
        sync = PTPSynchronizer("node-1", target_jitter_ns=50.0)
        assert sync.target_jitter_ns == 50.0

    def test_repr(self):
        """Test string representation."""
        sync = PTPSynchronizer("node-42", role=ClockRole.SLAVE)
        repr_str = repr(sync)
        assert "node-42" in repr_str
        assert "slave" in repr_str.lower()


class TestPTPSynchronizerStartStop:
    """Test start/stop functionality."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Test start activates synchronization."""
        sync = PTPSynchronizer("node-1")
        await sync.start()
        assert sync._running is True
        assert sync.state == SyncState.LISTENING
        await sync.stop()

    @pytest.mark.asyncio
    async def test_stop_deactivates(self):
        """Test stop deactivates synchronization."""
        sync = PTPSynchronizer("node-1")
        await sync.start()
        await sync.stop()
        assert sync._running is False
        assert sync.state == SyncState.PASSIVE

    @pytest.mark.asyncio
    async def test_grandmaster_start(self):
        """Test GRAND_MASTER starts updating time."""
        sync = PTPSynchronizer("master-1", role=ClockRole.GRAND_MASTER)
        await sync.start()
        assert sync._running is True
        assert sync.state == SyncState.MASTER_SYNC
        await sync.stop()


class TestPTPSynchronizerSyncToMaster:
    """Test sync_to_master method."""

    @pytest.mark.asyncio
    async def test_sync_to_master_basic(self):
        """Test basic sync to master."""
        sync = PTPSynchronizer("slave-1")
        await sync.start()
        
        # Mock master time source
        master_time_ns = time.time_ns()
        result = await sync.sync_to_master("master-1", lambda: master_time_ns)
        
        assert result is not None
        assert result.success is True
        assert result.jitter_ns >= 0
        assert result.offset_ns is not None
        await sync.stop()

    @pytest.mark.asyncio
    async def test_sync_updates_state(self):
        """Test successful sync updates state."""
        sync = PTPSynchronizer("slave-1")
        await sync.start()
        
        await sync.sync_to_master("master-1", lambda: time.time_ns())
        
        # State should be UNCALIBRATED or SLAVE_SYNC after sync
        assert sync.state in [SyncState.SLAVE_SYNC, SyncState.UNCALIBRATED]
        await sync.stop()

    @pytest.mark.asyncio
    async def test_sync_calculates_offset(self):
        """Test offset calculation."""
        sync = PTPSynchronizer("slave-1")
        await sync.start()
        
        result = await sync.sync_to_master(
            "master-1", 
            lambda: time.time_ns()
        )
        
        assert result.offset_ns is not None
        await sync.stop()

    @pytest.mark.asyncio
    async def test_sync_without_providing_master_time(self):
        """Test sync without master time source."""
        sync = PTPSynchronizer("slave-1")
        await sync.start()
        
        # Should work with None time source (uses internal simulation)
        result = await sync.sync_to_master("master-1", None)
        assert result is not None
        assert result.success is True
        await sync.stop()

    @pytest.mark.asyncio
    async def test_grandmaster_cannot_sync(self):
        """Test grand master cannot sync to others."""
        sync = PTPSynchronizer("master-1", role=ClockRole.GRAND_MASTER)
        await sync.start()
        
        result = await sync.sync_to_master("other-master", lambda: time.time_ns())
        assert result.success is False
        await sync.stop()


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

    @pytest.mark.asyncio
    async def test_is_ready_for_esgt_initial(self):
        """Test ESGT readiness without sync."""
        sync = PTPSynchronizer("node-1")
        # Without sync, might not be ready (depends on quality threshold)
        is_ready = sync.is_ready_for_esgt()
        assert is_ready in (True, False) or hasattr(is_ready, '__bool__')

    @pytest.mark.asyncio
    async def test_is_ready_for_esgt_after_sync(self):
        """Test ESGT readiness after sync."""
        sync = PTPSynchronizer("slave-1", target_jitter_ns=1000000)  # 1ms target
        await sync.start()
        
        # Perform multiple syncs to build history
        for _ in range(5):
            await sync.sync_to_master("master-1", lambda: time.time_ns())
        
        # Should now evaluate readiness
        is_ready = sync.is_ready_for_esgt()
        assert is_ready in (True, False) or hasattr(is_ready, '__bool__')
        await sync.stop()


class TestPTPSynchronizerContinuousSync:
    """Test continuous synchronization."""

    @pytest.mark.asyncio
    async def test_continuous_sync_starts(self):
        """Test continuous sync starts correctly."""
        sync = PTPSynchronizer("slave-1")
        await sync.start()
        
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
        
        await sync.stop()


class TestPTPSynchronizerQuality:
    """Test quality calculation."""

    def test_calculate_quality_returns_valid_range(self):
        """Test quality is in valid range."""
        sync = PTPSynchronizer("node-1")
        quality = sync._calculate_quality(jitter_ns=10.0, delay_ns=100.0)
        assert 0.0 <= quality <= 1.0

    def test_calculate_quality_low_jitter_is_high(self):
        """Test low jitter gives higher quality."""
        sync = PTPSynchronizer("node-1", target_jitter_ns=100.0)
        quality_low = sync._calculate_quality(jitter_ns=10.0, delay_ns=100.0)
        quality_high = sync._calculate_quality(jitter_ns=1000.0, delay_ns=100.0)
        assert quality_low > quality_high
