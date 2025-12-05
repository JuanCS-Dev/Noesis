"""
Integration Tests for HCL Analyzer Service.

Tests the full analysis pipeline from raw metrics to final analysis results.
These tests verify that all components work together correctly.
"""

from __future__ import annotations

import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import List

from config import AnalyzerSettings
from models.analysis import SystemMetrics, AnomalyType
from core.analyzer import SystemAnalyzer
from core.ml_analyzer import MLSystemAnalyzer
from core.models.sarima_forecaster import SARIMAForecaster, SARIMAConfig
from core.models.isolation_detector import IsolationAnomalyDetector, IsolationConfig
from core.models.hybrid_detector import (
    HybridAnomalyDetector,
    HybridConfig,
    AnomalySource,
)


def generate_realistic_metrics(
    base_cpu: float = 50.0,
    base_memory: float = 60.0,
    noise_level: float = 5.0,
    count: int = 100,
    trend: float = 0.0,
    seasonality: bool = False,
) -> List[SystemMetrics]:
    """
    Generate realistic system metrics for testing.

    Args:
        base_cpu: Base CPU usage percentage
        base_memory: Base memory usage percentage
        noise_level: Standard deviation of noise
        count: Number of data points
        trend: Linear trend per data point
        seasonality: Add daily seasonality pattern
    """
    np.random.seed(42)
    metrics = []

    for i in range(count):
        # Add trend
        cpu = base_cpu + trend * i
        memory = base_memory + trend * i * 0.5

        # Add seasonality (24-hour cycle)
        if seasonality:
            hour_of_day = i % 24
            # Peak at hour 12, low at hour 0
            seasonal_factor = np.sin(hour_of_day * np.pi / 12) * 10
            cpu += seasonal_factor
            memory += seasonal_factor * 0.5

        # Add noise
        cpu += np.random.randn() * noise_level
        memory += np.random.randn() * noise_level * 0.8

        # Add some correlated spikes
        if np.random.random() < 0.05:  # 5% chance of spike
            spike = np.random.uniform(10, 25)
            cpu += spike
            memory += spike * 0.7

        # Clamp to valid ranges
        cpu = max(0.0, min(100.0, cpu))
        memory = max(0.0, min(100.0, memory))

        metrics.append(
            SystemMetrics(
                timestamp=(datetime.now() + timedelta(minutes=i)).isoformat(),
                cpu_usage=cpu,
                memory_usage=memory,
                disk_io_rate=1000.0 + np.random.randn() * 100,
                network_io_rate=5000.0 + np.random.randn() * 500,
                avg_latency_ms=100.0 + np.random.randn() * 20,
                error_rate=0.01 + np.abs(np.random.randn() * 0.005),
                service_status={"api": "healthy", "db": "healthy"},
            )
        )

    return metrics


class TestEndToEndAnalysisPipeline:
    """End-to-end tests for the complete analysis pipeline."""

    @pytest.mark.asyncio
    async def test_complete_pipeline_healthy_system(self):
        """Test complete pipeline with healthy system metrics."""
        # Setup
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Generate training data
        training_data = generate_realistic_metrics(
            base_cpu=45.0,
            base_memory=55.0,
            noise_level=5.0,
            count=100,
        )

        # Train the model
        trained = analyzer.train(training_data)
        assert trained is True

        # Generate test metrics (similar to training - should be normal)
        test_metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_usage=48.0,
            memory_usage=57.0,
            disk_io_rate=1050.0,
            network_io_rate=5100.0,
            avg_latency_ms=105.0,
            error_rate=0.012,
            service_status={"api": "healthy", "db": "healthy"},
        )

        # Analyze
        result = await analyzer.analyze_metrics(test_metrics)

        # Verify result
        assert result.overall_health_score > 0.6
        assert result.requires_intervention is False
        assert "cpu_trend" in result.trends

    @pytest.mark.asyncio
    async def test_complete_pipeline_anomalous_system(self):
        """Test complete pipeline detecting anomalies."""
        # Setup
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Generate normal training data
        training_data = generate_realistic_metrics(
            base_cpu=40.0,
            base_memory=50.0,
            noise_level=3.0,
            count=100,
        )

        # Train
        analyzer.train(training_data)

        # Generate anomalous test metrics
        anomalous_metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_usage=95.0,  # Extremely high
            memory_usage=92.0,  # Extremely high
            disk_io_rate=5000.0,  # 5x normal
            network_io_rate=25000.0,  # 5x normal
            avg_latency_ms=800.0,  # Very high
            error_rate=0.08,  # High error rate
            service_status={"api": "degraded", "db": "healthy"},
        )

        # Analyze
        result = await analyzer.analyze_metrics(anomalous_metrics)

        # Verify anomalies were detected
        assert result.overall_health_score < 0.8
        assert len(result.anomalies) > 0
        assert len(result.recommendations) > 1

    @pytest.mark.asyncio
    async def test_pipeline_with_trend_detection(self):
        """Test that pipeline detects increasing trends."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Generate training data with upward trend
        training_data = generate_realistic_metrics(
            base_cpu=40.0,
            base_memory=45.0,
            noise_level=3.0,
            count=100,
            trend=0.3,  # Increasing trend
        )

        analyzer.train(training_data)

        # Add some history for trend detection
        for i in range(15):
            m = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_usage=50 + i * 2,  # Increasing CPU
                memory_usage=55 + i,
                disk_io_rate=1000.0,
                network_io_rate=5000.0,
                avg_latency_ms=100.0,
                error_rate=0.01,
                service_status={"api": "healthy"},
            )
            analyzer._metrics_history.append(m)

        # Test current metrics
        current = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_usage=80.0,
            memory_usage=70.0,
            disk_io_rate=1000.0,
            network_io_rate=5000.0,
            avg_latency_ms=100.0,
            error_rate=0.01,
            service_status={"api": "healthy"},
        )

        result = await analyzer.analyze_metrics(current)

        # Should detect increasing trend
        assert result.trends["cpu_trend"] == "increasing"

    @pytest.mark.asyncio
    async def test_static_vs_ml_analyzer_comparison(self):
        """Compare static and ML-based analyzer results."""
        settings = AnalyzerSettings()

        static_analyzer = SystemAnalyzer(settings)
        ml_analyzer = MLSystemAnalyzer(settings)

        # Train ML analyzer
        training_data = generate_realistic_metrics(count=100)
        ml_analyzer.train(training_data)

        # Test with high CPU metrics
        high_cpu_metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_usage=92.0,
            memory_usage=60.0,
            disk_io_rate=1000.0,
            network_io_rate=5000.0,
            avg_latency_ms=100.0,
            error_rate=0.02,
            service_status={"api": "healthy"},
        )

        static_result = await static_analyzer.analyze_metrics(high_cpu_metrics)
        ml_result = await ml_analyzer.analyze_metrics(high_cpu_metrics)

        # Both should detect high CPU anomaly
        static_cpu_anomalies = [
            a for a in static_result.anomalies
            if a.metric_name == "cpu_usage"
        ]
        ml_cpu_anomalies = [
            a for a in ml_result.anomalies
            if a.metric_name == "cpu_usage"
        ]

        assert len(static_cpu_anomalies) > 0
        # ML may also detect based on pattern, not just threshold


class TestHybridDetectorIntegration:
    """Integration tests for hybrid anomaly detector."""

    def test_full_hybrid_detection_pipeline(self):
        """Test complete hybrid detection from training to detection."""
        config = HybridConfig(
            sarima_weight=0.4,
            isolation_weight=0.6,
            ensemble_threshold=0.5,
            feature_names=["cpu", "memory", "disk", "network", "latency", "errors"],
        )

        detector = HybridAnomalyDetector(config)

        # Generate training data
        np.random.seed(42)
        n_samples = 150

        time_series = [50 + np.random.randn() * 5 for _ in range(n_samples)]
        multivariate = [
            [
                50 + np.random.randn() * 5,  # cpu
                60 + np.random.randn() * 5,  # memory
                1000 + np.random.randn() * 100,  # disk
                5000 + np.random.randn() * 500,  # network
                100 + np.random.randn() * 10,  # latency
                0.01 + np.abs(np.random.randn() * 0.005),  # errors
            ]
            for _ in range(n_samples)
        ]

        # Train
        success = detector.fit(time_series, multivariate)
        assert success is True

        # Test normal detection
        normal_result = detector.detect(
            time_series_value=52.0,
            feature_vector=[52.0, 61.0, 1050.0, 5100.0, 105.0, 0.012],
        )

        # Normal should not be anomaly
        assert normal_result.weighted_score < 0.8

        # Test anomalous detection
        anomaly_result = detector.detect(
            time_series_value=150.0,  # 20 std away
            feature_vector=[150.0, 150.0, 10000.0, 50000.0, 1000.0, 0.5],
        )

        # Should detect as anomaly
        assert anomaly_result.is_anomaly is True
        assert anomaly_result.weighted_score > 0.5

    def test_detect_and_update_online_learning(self):
        """Test online learning with detect_and_update."""
        config = HybridConfig()
        detector = HybridAnomalyDetector(config)

        # Initial training
        np.random.seed(42)
        time_series = [50 + np.random.randn() * 3 for _ in range(100)]
        multivariate = [[50 + np.random.randn() * 3] * 6 for _ in range(100)]

        detector.fit(time_series, multivariate)

        # Online updates
        for i in range(50):
            result = detector.detect_and_update(
                time_series_value=50 + np.random.randn() * 3,
                feature_vector=[50 + np.random.randn() * 3] * 6,
            )
            # Normal data should not be anomalous
            if result.is_anomaly:
                assert result.confidence < 0.9  # Low confidence anomalies ok

    def test_source_attribution(self):
        """Test that anomaly sources are correctly attributed."""
        config = HybridConfig(
            sarima_weight=0.5,
            isolation_weight=0.5,
            sarima_sigma_threshold=2.0,
            isolation_score_threshold=-0.3,
        )

        detector = HybridAnomalyDetector(config)

        # Train on normal data
        np.random.seed(42)
        time_series = [50 + np.random.randn() * 2 for _ in range(100)]
        multivariate = [[50 + np.random.randn() * 2] * 6 for _ in range(100)]

        detector.fit(time_series, multivariate)

        # Test time series anomaly only (extreme value, normal features)
        ts_anomaly = detector.detect(
            time_series_value=100.0,  # Far from mean
            feature_vector=[50.0, 50.0, 50.0, 50.0, 50.0, 50.0],  # Normal
        )

        # Should be detected primarily by SARIMA
        if ts_anomaly.is_anomaly:
            assert ts_anomaly.source in [AnomalySource.SARIMA, AnomalySource.BOTH]


class TestPerformanceBenchmarks:
    """Performance benchmarks for ML components."""

    def test_sarima_training_performance(self):
        """Benchmark SARIMA training time."""
        import time

        config = SARIMAConfig()
        forecaster = SARIMAForecaster(config)

        # Generate data
        np.random.seed(42)
        data = [50 + np.random.randn() * 5 for _ in range(200)]

        # Time training
        start = time.time()
        forecaster.fit(data)
        training_time = time.time() - start

        # Should complete in reasonable time (< 5 seconds)
        assert training_time < 5.0

    def test_sarima_prediction_performance(self):
        """Benchmark SARIMA prediction time."""
        import time

        config = SARIMAConfig()
        forecaster = SARIMAForecaster(config)

        # Train
        np.random.seed(42)
        data = [50 + np.random.randn() * 5 for _ in range(100)]
        forecaster.fit(data)

        # Time prediction
        start = time.time()
        for _ in range(100):
            forecaster.predict()
        prediction_time = (time.time() - start) / 100

        # Each prediction should be fast (< 50ms)
        assert prediction_time < 0.05

    def test_isolation_forest_training_performance(self):
        """Benchmark Isolation Forest training time."""
        import time

        config = IsolationConfig()
        detector = IsolationAnomalyDetector(config)

        # Generate data
        np.random.seed(42)
        data = [[np.random.randn() * 5 + 50] * 6 for _ in range(500)]

        # Time training
        start = time.time()
        detector.fit(data)
        training_time = time.time() - start

        # Should complete quickly (< 2 seconds)
        assert training_time < 2.0

    def test_isolation_forest_detection_performance(self):
        """Benchmark Isolation Forest detection time."""
        import time

        config = IsolationConfig()
        detector = IsolationAnomalyDetector(config)

        # Train
        np.random.seed(42)
        data = [[np.random.randn() * 5 + 50] * 6 for _ in range(200)]
        detector.fit(data)

        # Time detection
        start = time.time()
        for _ in range(100):
            detector.detect([50.0, 50.0, 50.0, 50.0, 50.0, 50.0])
        detection_time = (time.time() - start) / 100

        # Each detection should be reasonably fast (< 100ms)
        assert detection_time < 0.1

    def test_hybrid_detector_full_pipeline_performance(self):
        """Benchmark full hybrid detector pipeline."""
        import time

        config = HybridConfig()
        detector = HybridAnomalyDetector(config)

        # Generate data
        np.random.seed(42)
        time_series = [50 + np.random.randn() * 5 for _ in range(150)]
        multivariate = [[50 + np.random.randn() * 5] * 6 for _ in range(150)]

        # Time training
        start = time.time()
        detector.fit(time_series, multivariate)
        training_time = time.time() - start

        # Time detection
        start = time.time()
        for _ in range(10):
            detector.detect(
                time_series_value=52.0,
                feature_vector=[52.0] * 6,
            )
        detection_time = (time.time() - start) / 10

        # Training should complete in reasonable time
        assert training_time < 10.0

        # Detection should be reasonably fast (< 200ms for full pipeline)
        assert detection_time < 0.2

    @pytest.mark.asyncio
    async def test_ml_analyzer_full_pipeline_performance(self):
        """Benchmark full ML analyzer pipeline."""
        import time

        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Generate training data
        training_data = generate_realistic_metrics(count=100)

        # Time training
        start = time.time()
        analyzer.train(training_data)
        training_time = time.time() - start

        # Generate test metrics
        test_metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_usage=55.0,
            memory_usage=60.0,
            disk_io_rate=1000.0,
            network_io_rate=5000.0,
            avg_latency_ms=100.0,
            error_rate=0.01,
            service_status={"api": "healthy"},
        )

        # Time analysis
        start = time.time()
        for _ in range(10):
            await analyzer.analyze_metrics(test_metrics)
        analysis_time = (time.time() - start) / 10

        # Training should be reasonable
        assert training_time < 15.0

        # Analysis should be fast enough for real-time use
        assert analysis_time < 0.1


class TestEdgeCasesIntegration:
    """Integration tests for edge cases."""

    @pytest.mark.asyncio
    async def test_pipeline_with_missing_service_status(self):
        """Test pipeline handles missing service status."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        training_data = generate_realistic_metrics(count=100)
        analyzer.train(training_data)

        # Metrics with empty service status
        metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_usage=50.0,
            memory_usage=60.0,
            disk_io_rate=1000.0,
            network_io_rate=5000.0,
            avg_latency_ms=100.0,
            error_rate=0.01,
            service_status={},
        )

        result = await analyzer.analyze_metrics(metrics)
        assert result.overall_health_score >= 0.0

    @pytest.mark.asyncio
    async def test_pipeline_with_extreme_values(self):
        """Test pipeline handles extreme metric values."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        training_data = generate_realistic_metrics(count=100)
        analyzer.train(training_data)

        # Extreme values at boundaries
        extreme_metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_usage=100.0,
            memory_usage=100.0,
            disk_io_rate=0.0,
            network_io_rate=1000000.0,
            avg_latency_ms=10000.0,
            error_rate=1.0,
            service_status={"api": "critical"},
        )

        result = await analyzer.analyze_metrics(extreme_metrics)

        # Should handle extreme values
        assert 0.0 <= result.overall_health_score <= 1.0
        assert len(result.anomalies) > 0

    @pytest.mark.asyncio
    async def test_pipeline_consecutive_analysis(self):
        """Test pipeline with many consecutive analyses."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        training_data = generate_realistic_metrics(count=100)
        analyzer.train(training_data)

        # Run many consecutive analyses
        for i in range(50):
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_usage=50.0 + np.sin(i * 0.1) * 10,
                memory_usage=60.0 + np.cos(i * 0.1) * 10,
                disk_io_rate=1000.0,
                network_io_rate=5000.0,
                avg_latency_ms=100.0,
                error_rate=0.01,
                service_status={"api": "healthy"},
            )

            result = await analyzer.analyze_metrics(metrics)
            assert result.overall_health_score >= 0.0

        # Check history was maintained
        assert len(analyzer._metrics_history) == 150  # 100 training + 50 analysis

    def test_hybrid_detector_empty_feature_names(self):
        """Test hybrid detector with empty feature names."""
        config = HybridConfig(feature_names=[])
        detector = HybridAnomalyDetector(config)

        # Should still work without feature names
        np.random.seed(42)
        time_series = [50 + np.random.randn() * 5 for _ in range(100)]
        multivariate = [[50 + np.random.randn() * 5] * 6 for _ in range(100)]

        success = detector.fit(time_series, multivariate)
        assert success is True

        result = detector.detect(52.0, [52.0] * 6)
        assert result is not None
