"""Tests for tig/sync_models.py"""

import time

from consciousness.tig.sync_models import ClockOffset, ClockRole, SyncResult, SyncState


class TestClockRole:
    """Test ClockRole enum."""

    def test_all_roles_exist(self):
        """Test all clock roles."""
        assert ClockRole.GRAND_MASTER.value == "grand_master"
        assert ClockRole.MASTER.value == "master"
        assert ClockRole.SLAVE.value == "slave"
        assert ClockRole.PASSIVE.value == "passive"


class TestSyncState:
    """Test SyncState enum."""

    def test_all_states_exist(self):
        """Test all sync states."""
        assert SyncState.PASSIVE.value == "passive"
        assert SyncState.INITIALIZING.value == "initializing"
        assert SyncState.LISTENING.value == "listening"
        assert SyncState.UNCALIBRATED.value == "uncalibrated"
        assert SyncState.SLAVE_SYNC.value == "slave_sync"
        assert SyncState.MASTER_SYNC.value == "master_sync"
        assert SyncState.FAULT.value == "fault"


class TestClockOffset:
    """Test ClockOffset dataclass."""

    def test_creation(self):
        """Test creating clock offset."""
        offset = ClockOffset(
            offset_ns=500.0,
            jitter_ns=100.0,
            drift_ppm=10.0,
            last_sync=time.time(),
            quality=0.95,
        )

        assert offset.offset_ns == 500.0
        assert offset.jitter_ns == 100.0
        assert offset.drift_ppm == 10.0
        assert offset.quality == 0.95

    def test_is_acceptable_good_sync(self):
        """Test acceptable sync with good parameters."""
        offset = ClockOffset(
            offset_ns=500.0,
            jitter_ns=800.0,
            drift_ppm=50.0,
            last_sync=time.time(),
            quality=0.90,
        )

        assert offset.is_acceptable_for_esgt() is True

    def test_is_acceptable_high_jitter(self):
        """Test unacceptable sync with high jitter."""
        offset = ClockOffset(
            offset_ns=500.0,
            jitter_ns=2000.0,  # > 1000 threshold
            drift_ppm=50.0,
            last_sync=time.time(),
            quality=0.90,
        )

        assert offset.is_acceptable_for_esgt() is False

    def test_is_acceptable_low_quality(self):
        """Test unacceptable sync with low quality."""
        offset = ClockOffset(
            offset_ns=500.0,
            jitter_ns=800.0,
            drift_ppm=50.0,
            last_sync=time.time(),
            quality=0.10,  # < 0.20 threshold
        )

        assert offset.is_acceptable_for_esgt() is False

    def test_is_acceptable_high_drift(self):
        """Test unacceptable sync with high drift."""
        offset = ClockOffset(
            offset_ns=500.0,
            jitter_ns=800.0,
            drift_ppm=1500.0,  # > 1000 ppm
            last_sync=time.time(),
            quality=0.90,
        )

        assert offset.is_acceptable_for_esgt() is False

    def test_is_acceptable_large_offset(self):
        """Test unacceptable sync with large offset."""
        offset = ClockOffset(
            offset_ns=2_000_000.0,  # > 1M ns
            jitter_ns=800.0,
            drift_ppm=50.0,
            last_sync=time.time(),
            quality=0.90,
        )

        assert offset.is_acceptable_for_esgt() is False

    def test_is_acceptable_custom_thresholds(self):
        """Test with custom thresholds."""
        offset = ClockOffset(
            offset_ns=500.0,
            jitter_ns=1500.0,
            drift_ppm=50.0,
            last_sync=time.time(),
            quality=0.90,
        )

        assert offset.is_acceptable_for_esgt(threshold_ns=2000.0) is True


class TestSyncResult:
    """Test SyncResult dataclass."""

    def test_creation_success(self):
        """Test creating successful sync result."""
        result = SyncResult(
            success=True, offset_ns=100.0, jitter_ns=50.0, message="Sync OK"
        )

        assert result.success is True
        assert result.offset_ns == 100.0
        assert result.jitter_ns == 50.0
        assert result.message == "Sync OK"

    def test_creation_failure(self):
        """Test creating failed sync result."""
        result = SyncResult(success=False, message="Sync failed")

        assert result.success is False
        assert result.offset_ns == 0.0
        assert result.jitter_ns == 0.0
        assert result.message == "Sync failed"
