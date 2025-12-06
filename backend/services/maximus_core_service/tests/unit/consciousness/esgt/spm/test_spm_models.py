"""Tests for esgt/spm/salience_detector_models.py and esgt/spm/metrics_monitor_models.py"""

import time

from consciousness.esgt.models import SalienceScore
from consciousness.esgt.spm.salience_detector_models import (
    SalienceDetectorConfig,
    SalienceEvent,
    SalienceMode,
    SalienceThresholds,
)
from consciousness.esgt.spm.metrics_monitor_models import (
    MetricCategory,
    MetricsMonitorConfig,
    MetricsSnapshot,
)
from consciousness.mmei.models import AbstractNeeds


class TestSalienceMode:
    """Test SalienceMode enum."""

    def test_all_modes_exist(self):
        """Test all salience modes."""
        assert SalienceMode.PASSIVE.value == "passive"
        assert SalienceMode.ACTIVE.value == "active"


class TestSalienceThresholds:
    """Test SalienceThresholds dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        thresholds = SalienceThresholds()
        
        assert thresholds.low_threshold == 0.30
        assert thresholds.medium_threshold == 0.50
        assert thresholds.high_threshold == 0.70
        assert thresholds.critical_threshold == 0.90

    def test_creation_custom(self):
        """Test creating with custom values."""
        thresholds = SalienceThresholds(
            low_threshold=0.25,
            medium_threshold=0.45,
            high_threshold=0.65,
            critical_threshold=0.85,
        )
        
        assert thresholds.low_threshold == 0.25
        assert thresholds.high_threshold == 0.65


class TestSalienceDetectorConfig:
    """Test SalienceDetectorConfig dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        config = SalienceDetectorConfig()
        
        assert config.mode == SalienceMode.ACTIVE
        assert config.update_interval_ms == 50.0
        assert config.novelty_weight == 0.4
        assert config.relevance_weight == 0.4
        assert config.urgency_weight == 0.2
        assert isinstance(config.thresholds, SalienceThresholds)

    def test_creation_custom(self):
        """Test creating with custom values."""
        custom_thresholds = SalienceThresholds(high_threshold=0.75)
        config = SalienceDetectorConfig(
            mode=SalienceMode.PASSIVE,
            update_interval_ms=100.0,
            novelty_weight=0.5,
            relevance_weight=0.3,
            urgency_weight=0.2,
            thresholds=custom_thresholds,
        )
        
        assert config.mode == SalienceMode.PASSIVE
        assert config.update_interval_ms == 100.0
        assert config.thresholds.high_threshold == 0.75

    def test_weights_sum_to_one(self):
        """Test that default weights sum to 1.0."""
        config = SalienceDetectorConfig()
        total = config.novelty_weight + config.relevance_weight + config.urgency_weight
        assert abs(total - 1.0) < 0.01

    def test_all_config_fields(self):
        """Test all configuration fields are accessible."""
        config = SalienceDetectorConfig()
        
        assert config.novelty_baseline_window == 50
        assert config.novelty_change_threshold == 0.15
        assert config.default_relevance == 0.5
        assert config.urgency_decay_rate == 0.1
        assert config.urgency_boost_on_error == 0.3
        assert config.max_history_size == 100


class TestSalienceEvent:
    """Test SalienceEvent dataclass."""

    def test_creation(self):
        """Test creating salience event."""
        score = SalienceScore(novelty=0.8, relevance=0.7, urgency=0.6)
        event = SalienceEvent(
            timestamp=1234567890.0,
            salience=score,
            source="SPM-visual",
            content={"data": "test"},
            threshold_exceeded=0.75,
        )
        
        assert event.timestamp == 1234567890.0
        assert event.salience == score
        assert event.source == "SPM-visual"
        assert event.content == {"data": "test"}
        assert event.threshold_exceeded == 0.75

    def test_creation_with_current_time(self):
        """Test creating event with current timestamp."""
        score = SalienceScore()
        ts = time.time()
        event = SalienceEvent(
            timestamp=ts,
            salience=score,
            source="test",
            content={},
            threshold_exceeded=0.70,
        )
        
        assert abs(event.timestamp - ts) < 0.01


class TestMetricCategory:
    """Test MetricCategory enum."""

    def test_all_categories_exist(self):
        """Test all metric categories."""
        assert MetricCategory.COMPUTATIONAL.value == "computational"
        assert MetricCategory.INTEROCEPTIVE.value == "interoceptive"
        assert MetricCategory.PERFORMANCE.value == "performance"
        assert MetricCategory.HEALTH.value == "health"
        assert MetricCategory.RESOURCES.value == "resources"


class TestMetricsMonitorConfig:
    """Test MetricsMonitorConfig dataclass."""

    def test_creation_defaults(self):
        """Test creating with defaults."""
        config = MetricsMonitorConfig()
        
        assert config.monitoring_interval_ms == 200.0
        assert config.enable_continuous_reporting is True
        assert config.high_cpu_threshold == 0.80
        assert config.high_memory_threshold == 0.75
        assert config.high_error_rate_threshold == 5.0
        assert config.critical_need_threshold == 0.80

    def test_creation_custom(self):
        """Test creating with custom values."""
        config = MetricsMonitorConfig(
            monitoring_interval_ms=100.0,
            enable_continuous_reporting=False,
            high_cpu_threshold=0.90,
            integrate_mmei=False,
        )
        
        assert config.monitoring_interval_ms == 100.0
        assert config.enable_continuous_reporting is False
        assert config.high_cpu_threshold == 0.90
        assert config.integrate_mmei is False

    def test_all_config_fields(self):
        """Test all configuration fields are accessible."""
        config = MetricsMonitorConfig()
        
        assert config.mmei_poll_interval_ms == 100.0
        assert config.report_significant_changes is True
        assert config.change_threshold == 0.15
        assert config.max_report_frequency_hz == 2.0


class TestMetricsSnapshot:
    """Test MetricsSnapshot dataclass."""

    def test_creation_minimal(self):
        """Test creating with minimal fields."""
        snapshot = MetricsSnapshot(timestamp=time.time())
        
        assert snapshot.cpu_usage_percent == 0.0
        assert snapshot.memory_usage_percent == 0.0
        assert snapshot.thread_count == 0
        assert snapshot.needs is None
        assert snapshot.most_urgent_need == "none"
        assert snapshot.most_urgent_value == 0.0

    def test_creation_complete(self):
        """Test creating with all fields."""
        needs = AbstractNeeds(
            rest_need=0.5,
            repair_need=0.3,
            efficiency_need=0.7,
            connectivity_need=0.4,
            curiosity_drive=0.8,
        )
        
        snapshot = MetricsSnapshot(
            timestamp=1234567890.0,
            cpu_usage_percent=75.0,
            memory_usage_percent=60.0,
            thread_count=8,
            needs=needs,
            most_urgent_need="efficiency_need",
            most_urgent_value=0.7,
            avg_latency_ms=15.5,
            error_rate_per_min=2.5,
            warning_count=3,
        )
        
        assert snapshot.cpu_usage_percent == 75.0
        assert snapshot.memory_usage_percent == 60.0
        assert snapshot.needs == needs
        assert snapshot.most_urgent_need == "efficiency_need"
        assert snapshot.avg_latency_ms == 15.5

    def test_to_dict_without_needs(self):
        """Test converting to dict without needs."""
        snapshot = MetricsSnapshot(
            timestamp=1000.0,
            cpu_usage_percent=50.0,
            memory_usage_percent=40.0,
            thread_count=4,
        )
        
        result = snapshot.to_dict()
        
        assert result["timestamp"] == 1000.0
        assert result["cpu_usage_percent"] == 50.0
        assert result["memory_usage_percent"] == 40.0
        assert result["thread_count"] == 4
        assert "needs" not in result

    def test_to_dict_with_needs(self):
        """Test converting to dict with needs."""
        needs = AbstractNeeds(
            rest_need=0.6,
            repair_need=0.4,
            efficiency_need=0.8,
            connectivity_need=0.5,
            curiosity_drive=0.9,
        )
        
        snapshot = MetricsSnapshot(
            timestamp=1000.0,
            cpu_usage_percent=70.0,
            needs=needs,
        )
        
        result = snapshot.to_dict()
        
        assert result["timestamp"] == 1000.0
        assert "needs" in result
        assert result["needs"]["rest_need"] == 0.6
        assert result["needs"]["efficiency_need"] == 0.8
        assert result["needs"]["curiosity_drive"] == 0.9

    def test_to_dict_complete(self):
        """Test converting complete snapshot to dict."""
        needs = AbstractNeeds()
        snapshot = MetricsSnapshot(
            timestamp=2000.0,
            cpu_usage_percent=80.0,
            memory_usage_percent=70.0,
            thread_count=10,
            needs=needs,
            most_urgent_need="rest",
            most_urgent_value=0.85,
            avg_latency_ms=20.0,
            error_rate_per_min=1.5,
            warning_count=5,
        )
        
        result = snapshot.to_dict()
        
        assert result["cpu_usage_percent"] == 80.0
        assert result["most_urgent_need"] == "rest"
        assert result["most_urgent_value"] == 0.85
        assert result["avg_latency_ms"] == 20.0
        assert result["error_rate_per_min"] == 1.5
        assert result["warning_count"] == 5
        assert "needs" in result
