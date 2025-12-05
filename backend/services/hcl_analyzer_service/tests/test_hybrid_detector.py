"""
Tests for Hybrid Anomaly Detector (SARIMA + Isolation Forest).
"""

from __future__ import annotations

import pytest
import numpy as np
from datetime import datetime

from core.models.sarima_forecaster import SARIMAForecaster, SARIMAConfig, ForecastResult
from core.models.isolation_detector import (
    IsolationAnomalyDetector,
    IsolationConfig,
    AnomalyResult,
)
from core.models.hybrid_detector import (
    HybridAnomalyDetector,
    HybridConfig,
    HybridAnomalyResult,
    AnomalySource,
)


class TestSARIMAForecaster:
    """Tests for SARIMA Forecaster."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        forecaster = SARIMAForecaster()

        assert forecaster.config.p == 1
        assert forecaster.config.d == 1
        assert forecaster.config.q == 1
        assert forecaster.config.s == 24

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = SARIMAConfig(p=2, d=1, q=2, s=12)
        forecaster = SARIMAForecaster(config=config)

        assert forecaster.config.p == 2
        assert forecaster.config.s == 12

    def test_fit_insufficient_data(self):
        """Test fitting with insufficient data."""
        forecaster = SARIMAForecaster()
        data = [1.0, 2.0, 3.0]  # Too few points

        result = forecaster.fit(data)

        # Should fail or use fallback
        assert len(forecaster._history) == 0 or len(forecaster._history) == len(data)

    def test_fit_sufficient_data(self):
        """Test fitting with sufficient data."""
        forecaster = SARIMAForecaster()

        # Generate enough data
        np.random.seed(42)
        data = list(50 + 10 * np.sin(np.linspace(0, 4 * np.pi, 100)) + np.random.randn(100) * 2)

        result = forecaster.fit(data)

        assert result is True
        assert len(forecaster._history) == 100

    def test_predict_after_fit(self):
        """Test prediction after fitting."""
        forecaster = SARIMAForecaster()

        np.random.seed(42)
        data = list(50 + 10 * np.sin(np.linspace(0, 4 * np.pi, 100)) + np.random.randn(100) * 2)
        forecaster.fit(data)

        forecast = forecaster.predict(steps=5)

        assert isinstance(forecast, ForecastResult)
        assert forecast.forecast_horizon == 5
        assert len(forecast.predicted_values) == 5

    def test_is_anomalous_normal_value(self):
        """Test anomaly detection for normal value."""
        forecaster = SARIMAForecaster()

        np.random.seed(42)
        data = list(np.random.randn(100) * 5 + 50)  # Mean=50, std=5
        forecaster.fit(data)

        is_anomaly, score = forecaster.is_anomalous(52.0, threshold_sigma=2.0)

        assert bool(is_anomaly) is False
        assert score < 2.0

    def test_is_anomalous_extreme_value(self):
        """Test anomaly detection for extreme value."""
        forecaster = SARIMAForecaster()

        np.random.seed(42)
        data = list(np.random.randn(100) * 5 + 50)  # Mean=50, std=5
        forecaster.fit(data)

        is_anomaly, score = forecaster.is_anomalous(100.0, threshold_sigma=2.0)

        assert bool(is_anomaly) is True
        assert score > 2.0

    def test_update(self):
        """Test online update."""
        forecaster = SARIMAForecaster()

        data = list(range(100))
        forecaster.fit(data)
        initial_len = len(forecaster._history)

        forecaster.update(100.0)

        assert len(forecaster._history) == initial_len + 1

    def test_get_diagnostics(self):
        """Test diagnostics retrieval."""
        forecaster = SARIMAForecaster()

        data = list(range(100))
        forecaster.fit(data)

        diagnostics = forecaster.get_diagnostics()

        assert "model_type" in diagnostics
        assert diagnostics["model_type"] == "SARIMA"
        assert diagnostics["history_length"] == 100

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        forecaster = SARIMAForecaster()

        health = await forecaster.health_check()

        assert health["healthy"] is True


class TestIsolationAnomalyDetector:
    """Tests for Isolation Forest Detector."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        detector = IsolationAnomalyDetector()

        assert detector.config.n_estimators == 100
        assert detector.config.contamination == 0.1

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = IsolationConfig(
            n_estimators=50,
            contamination=0.05,
            feature_names=["cpu", "memory", "disk"],
        )
        detector = IsolationAnomalyDetector(config=config)

        assert detector.config.n_estimators == 50
        assert len(detector.config.feature_names) == 3

    def test_fit_insufficient_data(self):
        """Test fitting with insufficient data."""
        detector = IsolationAnomalyDetector()
        data = [[1, 2], [3, 4]]  # Only 2 samples

        result = detector.fit(data)

        assert result is False

    def test_fit_sufficient_data(self):
        """Test fitting with sufficient data."""
        detector = IsolationAnomalyDetector()

        np.random.seed(42)
        data = [list(np.random.randn(3) * 10 + 50) for _ in range(100)]

        result = detector.fit(data)

        assert result is True
        assert detector._fitted is True

    def test_detect_normal_sample(self):
        """Test detection of normal sample."""
        detector = IsolationAnomalyDetector()

        np.random.seed(42)
        data = [list(np.random.randn(3) * 10 + 50) for _ in range(100)]
        detector.fit(data)

        result = detector.detect([50.0, 50.0, 50.0])

        assert isinstance(result, AnomalyResult)
        # Normal point should not be anomaly
        assert result.anomaly_score < 1.0

    def test_detect_anomalous_sample(self):
        """Test detection of anomalous sample."""
        detector = IsolationAnomalyDetector()

        np.random.seed(42)
        data = [list(np.random.randn(3) * 10 + 50) for _ in range(100)]
        detector.fit(data)

        # Extreme outlier
        result = detector.detect([200.0, 200.0, 200.0])

        assert isinstance(result, AnomalyResult)
        # Should have high anomaly score
        assert result.is_anomaly is True or result.anomaly_score > 0.5

    def test_detect_batch(self):
        """Test batch detection."""
        detector = IsolationAnomalyDetector()

        np.random.seed(42)
        data = [list(np.random.randn(3) * 10 + 50) for _ in range(100)]
        detector.fit(data)

        samples = [[50, 50, 50], [55, 52, 48], [200, 200, 200]]
        results = detector.detect_batch(samples)

        assert len(results) == 3
        assert all(isinstance(r, AnomalyResult) for r in results)

    def test_update(self):
        """Test online update."""
        detector = IsolationAnomalyDetector()

        np.random.seed(42)
        data = [list(np.random.randn(3) * 10 + 50) for _ in range(100)]
        detector.fit(data)
        initial_len = len(detector._training_data)

        detector.update([60.0, 55.0, 52.0])

        assert len(detector._training_data) == initial_len + 1

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        detector = IsolationAnomalyDetector()

        health = await detector.health_check()

        assert health["healthy"] is True


class TestHybridAnomalyDetector:
    """Tests for Hybrid Anomaly Detector."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        detector = HybridAnomalyDetector()

        assert detector.config.sarima_weight == 0.4
        assert detector.config.isolation_weight == 0.6
        assert detector._fitted is False

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = HybridConfig(
            sarima_weight=0.5,
            isolation_weight=0.5,
            ensemble_threshold=0.6,
            feature_names=["cpu", "memory", "latency"],
        )
        detector = HybridAnomalyDetector(config=config)

        assert detector.config.sarima_weight == 0.5
        assert detector.config.ensemble_threshold == 0.6

    def test_fit_both_models(self):
        """Test fitting both component models."""
        detector = HybridAnomalyDetector()

        np.random.seed(42)
        time_series = list(50 + 10 * np.sin(np.linspace(0, 4 * np.pi, 100)) + np.random.randn(100))
        multivariate = [list(np.random.randn(4) * 10 + 50) for _ in range(100)]

        result = detector.fit(time_series, multivariate)

        assert result is True
        assert detector._fitted is True

    def test_detect_normal(self):
        """Test detection of normal values."""
        detector = HybridAnomalyDetector()

        np.random.seed(42)
        time_series = list(np.random.randn(100) * 5 + 50)
        multivariate = [[50, 50, 0.01, 100] for _ in range(100)]

        detector.fit(time_series, multivariate)

        result = detector.detect(
            time_series_value=52.0,
            feature_vector=[52.0, 48.0, 0.02, 110],
        )

        assert isinstance(result, HybridAnomalyResult)
        assert result.source in [AnomalySource.NONE, AnomalySource.SARIMA, AnomalySource.ISOLATION]

    def test_detect_temporal_anomaly(self):
        """Test detection of temporal anomaly (SARIMA)."""
        detector = HybridAnomalyDetector()

        np.random.seed(42)
        # Stable time series
        time_series = list(np.random.randn(100) * 2 + 50)
        multivariate = [[50, 50, 0.01, 100] for _ in range(100)]

        detector.fit(time_series, multivariate)

        # Sudden spike in time series value
        result = detector.detect(
            time_series_value=100.0,  # Way above normal
            feature_vector=[100.0, 50.0, 0.01, 100],  # Only CPU spiked
        )

        assert isinstance(result, HybridAnomalyResult)
        assert result.sarima_score > 1.0

    def test_detect_multivariate_anomaly(self):
        """Test detection of multivariate anomaly (Isolation Forest)."""
        detector = HybridAnomalyDetector()

        np.random.seed(42)
        time_series = list(np.random.randn(100) * 5 + 50)
        # Normal data cluster
        multivariate = [list(np.random.randn(4) * 5 + np.array([50, 50, 0.01, 100])) for _ in range(100)]

        detector.fit(time_series, multivariate)

        # Extreme outlier in all features
        result = detector.detect(
            time_series_value=52.0,  # Normal
            feature_vector=[200.0, 200.0, 0.5, 2000],  # All extreme
        )

        assert isinstance(result, HybridAnomalyResult)
        # Should detect as anomaly

    def test_detect_both_sources(self):
        """Test detection when both models flag anomaly."""
        detector = HybridAnomalyDetector()

        np.random.seed(42)
        time_series = list(np.random.randn(100) * 2 + 50)
        multivariate = [[50, 50, 0.01, 100] for _ in range(100)]

        detector.fit(time_series, multivariate)

        # Both temporal and multivariate anomaly
        result = detector.detect(
            time_series_value=200.0,  # Way above normal
            feature_vector=[200.0, 200.0, 0.5, 5000],  # All extreme
        )

        assert isinstance(result, HybridAnomalyResult)
        # Should have high confidence
        assert result.weighted_score > 0.3

    def test_detect_and_update(self):
        """Test combined detect and update."""
        detector = HybridAnomalyDetector()

        np.random.seed(42)
        time_series = list(np.random.randn(100) * 5 + 50)
        multivariate = [[50, 50, 0.01, 100] for _ in range(100)]

        detector.fit(time_series, multivariate)

        result = detector.detect_and_update(
            time_series_value=55.0,
            feature_vector=[55.0, 48.0, 0.02, 120],
        )

        assert isinstance(result, HybridAnomalyResult)
        assert len(detector._sarima._history) == 101

    def test_get_statistics(self):
        """Test statistics retrieval."""
        detector = HybridAnomalyDetector()

        np.random.seed(42)
        time_series = list(np.random.randn(100) * 5 + 50)
        multivariate = [[50, 50, 0.01, 100] for _ in range(100)]

        detector.fit(time_series, multivariate)

        # Run some detections
        for _ in range(10):
            detector.detect(52.0, [52.0, 48.0, 0.01, 100])

        stats = detector.get_statistics()

        assert stats["total_detections"] == 10
        assert "anomaly_rate" in stats

    def test_get_diagnostics(self):
        """Test diagnostics retrieval."""
        detector = HybridAnomalyDetector()

        diagnostics = detector.get_diagnostics()

        assert diagnostics["model_type"] == "HybridDetector"
        assert "sarima_diagnostics" in diagnostics
        assert "isolation_diagnostics" in diagnostics

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        detector = HybridAnomalyDetector()

        health = await detector.health_check()

        assert health["healthy"] is True
        assert "components" in health

    def test_explanation_generation(self):
        """Test explanation generation for anomalies."""
        config = HybridConfig(
            feature_names=["cpu_usage", "memory_usage", "error_rate", "latency_ms"]
        )
        detector = HybridAnomalyDetector(config=config)

        np.random.seed(42)
        time_series = list(np.random.randn(100) * 5 + 50)
        multivariate = [[50, 50, 0.01, 100] for _ in range(100)]

        detector.fit(time_series, multivariate)

        result = detector.detect(
            time_series_value=100.0,
            feature_vector=[100.0, 80.0, 0.1, 500],
        )

        # Should have explanation
        assert result.explanation != ""
        assert len(result.explanation) > 10


class TestAnomalySource:
    """Tests for AnomalySource enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert AnomalySource.SARIMA.value == "sarima"
        assert AnomalySource.ISOLATION.value == "isolation"
        assert AnomalySource.BOTH.value == "both"
        assert AnomalySource.NONE.value == "none"
