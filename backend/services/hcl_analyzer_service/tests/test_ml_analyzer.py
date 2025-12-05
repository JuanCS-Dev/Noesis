"""
Tests for ML-enhanced System Analyzer.
"""

from __future__ import annotations

import pytest
import numpy as np
from datetime import datetime

from config import AnalyzerSettings
from models.analysis import SystemMetrics, AnomalyType
from core.ml_analyzer import MLSystemAnalyzer
from core.models.hybrid_detector import HybridConfig


def generate_test_metrics(
    cpu: float = 50.0,
    memory: float = 50.0,
    error_rate: float = 0.01,
    latency: float = 100.0,
) -> SystemMetrics:
    """Generate test system metrics."""
    return SystemMetrics(
        timestamp=datetime.now().isoformat(),
        cpu_usage=cpu,
        memory_usage=memory,
        disk_io_rate=1000.0,
        network_io_rate=5000.0,
        avg_latency_ms=latency,
        error_rate=error_rate,
        service_status={"api": "healthy", "db": "healthy"},
    )


def generate_historical_metrics(count: int = 100) -> list:
    """Generate historical metrics for training."""
    np.random.seed(42)
    metrics = []

    for i in range(count):
        metrics.append(
            generate_test_metrics(
                cpu=50 + np.random.randn() * 10,
                memory=50 + np.random.randn() * 10,
                error_rate=0.01 + np.random.randn() * 0.005,
                latency=100 + np.random.randn() * 20,
            )
        )

    return metrics


class TestMLSystemAnalyzer:
    """Tests for MLSystemAnalyzer."""

    def test_init(self):
        """Test analyzer initialization."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        assert analyzer._trained is False
        assert len(analyzer._metrics_history) == 0

    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        settings = AnalyzerSettings()
        config = HybridConfig(
            sarima_weight=0.5,
            isolation_weight=0.5,
        )

        analyzer = MLSystemAnalyzer(settings, hybrid_config=config)

        assert analyzer._detector.config.sarima_weight == 0.5

    def test_train_insufficient_data(self):
        """Test training with insufficient data."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        result = analyzer.train([generate_test_metrics() for _ in range(10)])

        assert result is False
        assert analyzer._trained is False

    def test_train_sufficient_data(self):
        """Test training with sufficient data."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        historical = generate_historical_metrics(100)
        result = analyzer.train(historical)

        assert result is True
        assert analyzer._trained is True

    @pytest.mark.asyncio
    async def test_analyze_without_training(self):
        """Test analysis without training (fallback mode)."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        metrics = generate_test_metrics(cpu=95.0)  # High CPU
        result = await analyzer.analyze_metrics(metrics)

        assert result.overall_health_score <= 1.0
        assert len(result.anomalies) > 0  # Should detect high CPU

    @pytest.mark.asyncio
    async def test_analyze_with_training_normal(self):
        """Test analysis after training with normal metrics."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Train
        historical = generate_historical_metrics(100)
        analyzer.train(historical)

        # Analyze normal metrics
        metrics = generate_test_metrics(cpu=55.0, memory=52.0)
        result = await analyzer.analyze_metrics(metrics)

        assert result.overall_health_score > 0.5
        assert result.requires_intervention is False

    @pytest.mark.asyncio
    async def test_analyze_with_training_anomaly(self):
        """Test analysis after training with anomalous metrics."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Train on normal data
        historical = generate_historical_metrics(100)
        analyzer.train(historical)

        # Analyze anomalous metrics
        metrics = generate_test_metrics(cpu=200.0, memory=200.0, latency=2000.0)
        result = await analyzer.analyze_metrics(metrics)

        # Should detect anomaly
        assert result.overall_health_score < 1.0

    @pytest.mark.asyncio
    async def test_analyze_updates_history(self):
        """Test that analysis updates metrics history."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        historical = generate_historical_metrics(50)
        analyzer.train(historical)
        initial_len = len(analyzer._metrics_history)

        metrics = generate_test_metrics()
        await analyzer.analyze_metrics(metrics)

        assert len(analyzer._metrics_history) == initial_len + 1

    @pytest.mark.asyncio
    async def test_recommendations_generation(self):
        """Test recommendation generation."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # High CPU should generate CPU recommendation
        metrics = generate_test_metrics(cpu=95.0)
        result = await analyzer.analyze_metrics(metrics)

        assert len(result.recommendations) > 0
        assert any("CPU" in r or "cpu" in r for r in result.recommendations)

    @pytest.mark.asyncio
    async def test_trends_identification(self):
        """Test trend identification."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Add history with increasing CPU
        for i in range(15):
            analyzer._metrics_history.append(
                generate_test_metrics(cpu=50 + i * 2)
            )

        metrics = generate_test_metrics(cpu=80)
        result = await analyzer.analyze_metrics(metrics)

        assert result.trends["cpu_trend"] == "increasing"

    def test_get_statistics(self):
        """Test statistics retrieval."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        stats = analyzer.get_statistics()

        assert "trained" in stats
        assert "history_length" in stats
        assert "detector_stats" in stats

    def test_get_status_untrained(self):
        """Test status when untrained."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        status = analyzer.get_status()

        assert status["status"] == "active"
        assert status["mode"] == "static_fallback"

    def test_get_status_trained(self):
        """Test status when trained."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        historical = generate_historical_metrics(100)
        analyzer.train(historical)

        status = analyzer.get_status()

        assert status["mode"] == "ml_hybrid"

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        health = await analyzer.health_check()

        assert health["healthy"] is True
        assert "trained" in health
        assert "detector" in health

    def test_extract_features(self):
        """Test feature extraction."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        metrics = generate_test_metrics(
            cpu=50.0, memory=60.0, latency=100.0, error_rate=0.02
        )
        features = analyzer._extract_features(metrics)

        assert len(features) == 6
        assert features[0] == 50.0  # cpu
        assert features[1] == 60.0  # memory
        assert features[4] == 100.0  # latency
        assert features[5] == 0.02  # error_rate


class TestMLAnalyzerStaticFallback:
    """Tests for static fallback detection."""

    @pytest.mark.asyncio
    async def test_static_high_cpu(self):
        """Test static detection of high CPU."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        metrics = generate_test_metrics(cpu=95.0)
        result = await analyzer.analyze_metrics(metrics)

        cpu_anomalies = [a for a in result.anomalies if a.metric_name == "cpu_usage"]
        assert len(cpu_anomalies) > 0
        assert cpu_anomalies[0].severity >= 0.6

    @pytest.mark.asyncio
    async def test_static_high_memory(self):
        """Test static detection of high memory."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        metrics = generate_test_metrics(memory=95.0)
        result = await analyzer.analyze_metrics(metrics)

        mem_anomalies = [a for a in result.anomalies if a.metric_name == "memory_usage"]
        assert len(mem_anomalies) > 0

    @pytest.mark.asyncio
    async def test_static_high_error_rate(self):
        """Test static detection of high error rate."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        metrics = generate_test_metrics(error_rate=0.1)
        result = await analyzer.analyze_metrics(metrics)

        error_anomalies = [a for a in result.anomalies if a.metric_name == "error_rate"]
        assert len(error_anomalies) > 0
        assert error_anomalies[0].severity == 1.0
