"""
Unit tests for SystemMetricsCollector.
"""

import asyncio
from unittest.mock import MagicMock

import pytest

from backend.services.hcl_monitor_service.config import MonitorSettings
from backend.services.hcl_monitor_service.core.collector import SystemMetricsCollector


@pytest.fixture(name="settings")
def fixture_settings() -> MonitorSettings:
    """Monitor settings fixture."""
    return MonitorSettings(collection_interval=0.1, history_max_size=5)


@pytest.fixture(name="collector")
def fixture_collector(settings: MonitorSettings) -> SystemMetricsCollector:
    """Collector fixture."""
    return SystemMetricsCollector(settings)


@pytest.mark.asyncio
async def test_collect_metrics_once(collector: SystemMetricsCollector) -> None:
    """Test single metric collection."""
    await collector._collect_metrics_once()  # pylint: disable=protected-access

    metrics = collector.get_latest_metrics()
    assert metrics is not None
    assert metrics.cpu_usage >= 0.0
    assert metrics.memory_usage >= 0.0
    assert len(collector.get_metrics_history()) == 1


@pytest.mark.asyncio
async def test_metrics_history_limit(collector: SystemMetricsCollector) -> None:
    """Test metrics history limit."""
    # Collect more metrics than history size
    for _ in range(collector.settings.history_max_size + 2):
        await collector._collect_metrics_once()  # pylint: disable=protected-access

    history = collector.get_metrics_history()
    assert len(history) == collector.settings.history_max_size


@pytest.mark.asyncio
async def test_start_stop_collection(collector: SystemMetricsCollector) -> None:
    """Test start and stop collection loop."""
    # Mock _collect_metrics_once to avoid actual system calls and speed up test
    # pylint: disable=protected-access
    collector._collect_metrics_once = MagicMock(  # type: ignore
        side_effect=collector._collect_metrics_once
    )

    task = asyncio.create_task(collector.start_collection())

    # Let it run for a bit
    await asyncio.sleep(0.3)

    assert collector.is_collecting
    await collector.stop_collection()
    await task

    assert not collector.is_collecting
    assert len(collector.get_metrics_history()) > 0
