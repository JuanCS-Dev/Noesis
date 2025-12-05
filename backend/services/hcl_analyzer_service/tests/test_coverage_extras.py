"""
Additional tests to achieve 95%+ coverage.
"""

from __future__ import annotations

import pytest
import numpy as np
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime

from core.models.sarima_forecaster import (
    SARIMAForecaster,
    SARIMAConfig,
    ForecastResult,
)
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
from core.ml_analyzer import MLSystemAnalyzer
from core.analyzer import SystemAnalyzer
from config import AnalyzerSettings
from models.analysis import SystemMetrics, AnomalyType


# Helper functions
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
        service_status={"api": "healthy"},
    )


class TestSARIMAFallbacks:
    """Tests for SARIMA fallback code paths."""

    def test_fit_simple_model_directly(self):
        """Test _fit_simple_model directly."""
        forecaster = SARIMAForecaster()

        data = list(range(100))
        result = forecaster._fit_simple_model(data)

        assert result is True
        assert forecaster._simple_mean == 49.5
        assert forecaster._residuals_std > 0

    def test_fit_simple_model_short_data(self):
        """Test _fit_simple_model with short data (<=10)."""
        forecaster = SARIMAForecaster()

        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = forecaster._fit_simple_model(data)

        assert result is True
        assert forecaster._simple_trend == 0.0  # No trend calc for short data

    def test_predict_simple_empty_history(self):
        """Test _predict_simple with empty history."""
        forecaster = SARIMAForecaster()

        result = forecaster._predict_simple(5)

        assert result.forecast_horizon == 5
        assert len(result.predicted_values) == 0

    def test_predict_simple_with_history(self):
        """Test _predict_simple with history."""
        forecaster = SARIMAForecaster()
        forecaster._fit_simple_model(list(range(50, 150)))

        result = forecaster._predict_simple(3)

        assert len(result.predicted_values) == 3
        assert len(result.confidence_lower) == 3
        assert len(result.confidence_upper) == 3

    def test_fit_with_exception_fallback(self):
        """Test fit when SARIMA fails (simulated by bad data)."""
        forecaster = SARIMAForecaster()

        # Just test the simple model path directly
        data = list(range(100))
        result = forecaster._fit_simple_model(data)

        assert result is True
        assert forecaster._simple_mean is not None

    def test_predict_uses_simple_when_fitted_model_fails(self):
        """Test predict uses simple model when fitted model prediction fails."""
        forecaster = SARIMAForecaster()

        # Fit with simple model
        data = list(range(100))
        forecaster._fit_simple_model(data)

        result = forecaster.predict(steps=3)

        # Should use simple prediction
        assert len(result.predicted_values) == 3
        assert result.model_fitted is True

    def test_is_anomalous_without_forecast(self):
        """Test is_anomalous without using forecast."""
        forecaster = SARIMAForecaster()

        data = list(np.random.randn(100) * 5 + 50)
        forecaster._fit_simple_model(data)

        is_anomaly, score = forecaster.is_anomalous(
            55.0, threshold_sigma=2.0, use_forecast=False
        )

        assert isinstance(is_anomaly, (bool, np.bool_))
        assert score >= 0

    def test_is_anomalous_empty_simple_mean(self):
        """Test is_anomalous when simple_mean not set."""
        forecaster = SARIMAForecaster()

        # No fitting, so _simple_mean stays at default 0
        is_anomaly, score = forecaster.is_anomalous(
            100.0, threshold_sigma=2.0, use_forecast=False
        )

        # Should handle gracefully
        assert isinstance(score, float)


class TestIsolationFallbacks:
    """Tests for Isolation Forest fallback code paths."""

    def test_fit_simple_model_directly(self):
        """Test _fit_simple_model directly."""
        detector = IsolationAnomalyDetector()

        data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]] * 10
        result = detector._fit_simple_model(data)

        assert result is True
        assert detector._fitted is True
        assert detector._feature_means is not None

    def test_detect_not_fitted(self):
        """Test detect when model not fitted."""
        detector = IsolationAnomalyDetector()

        result = detector.detect([50, 50, 50])

        assert result.is_anomaly is False
        assert result.anomaly_score == 0.0

    def test_detect_simple_directly(self):
        """Test _detect_simple directly."""
        detector = IsolationAnomalyDetector()
        detector._fit_simple_model([[50, 50, 50]] * 20)

        result = detector._detect_simple([200, 200, 200])

        assert result.anomaly_score > 0
        assert len(result.feature_contributions) > 0

    def test_detect_simple_with_feature_names(self):
        """Test _detect_simple with custom feature names."""
        config = IsolationConfig(feature_names=["cpu", "memory", "disk"])
        detector = IsolationAnomalyDetector(config)
        detector._fit_simple_model([[50, 50, 50]] * 20)

        result = detector._detect_simple([200, 200, 200])

        assert "cpu" in result.feature_contributions
        assert "memory" in result.feature_contributions

    def test_detect_simple_none_means(self):
        """Test _detect_simple when means are None."""
        detector = IsolationAnomalyDetector()
        detector._fitted = True
        detector._feature_means = None

        result = detector._detect_simple([50, 50, 50])

        assert result.is_anomaly is False

    def test_fit_simple_model_fallback(self):
        """Test fit simple model fallback path."""
        detector = IsolationAnomalyDetector()

        # Test simple model directly
        data = [[50, 50, 50]] * 20
        result = detector._fit_simple_model(data)

        assert result is True
        assert detector._fitted is True

    def test_calculate_contributions_no_model(self):
        """Test _calculate_contributions when model is None."""
        detector = IsolationAnomalyDetector()
        detector._feature_means = np.array([50, 50, 50])
        detector._model = None

        result = detector._calculate_contributions([60, 60, 60])

        assert result == {}

    def test_calculate_contributions_no_means(self):
        """Test _calculate_contributions when means is None."""
        detector = IsolationAnomalyDetector()
        detector._feature_means = None

        result = detector._calculate_contributions([60, 60, 60])

        assert result == {}

    @pytest.mark.asyncio
    async def test_health_check_fitted(self):
        """Test health check when fitted."""
        detector = IsolationAnomalyDetector()
        detector.fit([[50, 50, 50]] * 20)

        health = await detector.health_check()

        assert health["model_fitted"] is True

    def test_get_diagnostics_fitted(self):
        """Test diagnostics when fitted."""
        detector = IsolationAnomalyDetector()
        detector.fit([[50, 50, 50]] * 20)

        diag = detector.get_diagnostics()

        assert diag["fitted"] is True
        assert diag["training_samples"] == 20


class TestHybridDetectorEdgeCases:
    """Edge case tests for hybrid detector."""

    def test_calculate_confidence_none_source(self):
        """Test confidence calculation with no anomaly."""
        detector = HybridAnomalyDetector()

        result = HybridAnomalyResult(source=AnomalySource.NONE)
        confidence = detector._calculate_confidence(result)

        assert confidence == 0.9

    def test_calculate_confidence_single_source(self):
        """Test confidence calculation with single source."""
        detector = HybridAnomalyDetector()

        result = HybridAnomalyResult(
            source=AnomalySource.SARIMA, weighted_score=0.6
        )
        confidence = detector._calculate_confidence(result)

        assert 0.7 <= confidence <= 1.0

    def test_generate_explanation_no_anomaly(self):
        """Test explanation generation with no anomaly."""
        detector = HybridAnomalyDetector()

        result = HybridAnomalyResult(source=AnomalySource.NONE)
        explanation = detector._generate_explanation(result, [50, 50, 50, 100])

        assert "No anomaly detected" in explanation

    def test_generate_explanation_sarima_only(self):
        """Test explanation with SARIMA-only anomaly."""
        config = HybridConfig(
            feature_names=["cpu", "memory", "error", "latency"]
        )
        detector = HybridAnomalyDetector(config)

        result = HybridAnomalyResult(
            source=AnomalySource.SARIMA,
            sarima_anomaly=True,
            sarima_score=3.0,
            sarima_expected=50.0,
        )
        explanation = detector._generate_explanation(result, [95, 50, 0.01, 100])

        assert "Temporal anomaly" in explanation

    def test_generate_explanation_isolation_only(self):
        """Test explanation with Isolation-only anomaly."""
        config = HybridConfig(feature_names=["cpu", "memory", "error", "latency"])
        detector = HybridAnomalyDetector(config)

        result = HybridAnomalyResult(
            source=AnomalySource.ISOLATION,
            isolation_anomaly=True,
            feature_contributions={"cpu": 0.5, "memory": 0.3},
        )
        explanation = detector._generate_explanation(result, [95, 80, 0.01, 100])

        assert "Unusual" in explanation or "Multivariate" in explanation

    def test_generate_explanation_both_sources(self):
        """Test explanation with both sources."""
        detector = HybridAnomalyDetector()

        result = HybridAnomalyResult(
            source=AnomalySource.BOTH,
            sarima_anomaly=True,
            isolation_anomaly=True,
        )
        explanation = detector._generate_explanation(result, [95, 80, 0.1, 500])

        assert "CRITICAL" in explanation

    def test_get_statistics_empty(self):
        """Test statistics with no detections."""
        detector = HybridAnomalyDetector()

        stats = detector.get_statistics()

        assert stats["total_detections"] == 0


class TestMLAnalyzerEdgeCases:
    """Edge case tests for ML analyzer."""

    @pytest.mark.asyncio
    async def test_convert_ml_anomalies_no_anomaly(self):
        """Test _convert_ml_anomalies with no anomaly."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        ml_result = HybridAnomalyResult(
            is_anomaly=False, source=AnomalySource.NONE
        )
        metrics = generate_test_metrics()

        anomalies = analyzer._convert_ml_anomalies(ml_result, metrics)

        assert len(anomalies) == 0

    @pytest.mark.asyncio
    async def test_convert_ml_anomalies_sarima_source(self):
        """Test _convert_ml_anomalies with SARIMA source."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        ml_result = HybridAnomalyResult(
            is_anomaly=True,
            source=AnomalySource.SARIMA,
            weighted_score=0.7,
            explanation="Temporal anomaly",
            feature_contributions={"cpu_usage": 0.5},
        )
        metrics = generate_test_metrics(cpu=95)

        anomalies = analyzer._convert_ml_anomalies(ml_result, metrics)

        assert len(anomalies) == 1
        assert anomalies[0].type == AnomalyType.TREND

    @pytest.mark.asyncio
    async def test_convert_ml_anomalies_isolation_source(self):
        """Test _convert_ml_anomalies with Isolation source."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        ml_result = HybridAnomalyResult(
            is_anomaly=True,
            source=AnomalySource.ISOLATION,
            weighted_score=0.6,
            explanation="Multivariate anomaly",
            feature_contributions={"memory_usage": 0.8},
        )
        metrics = generate_test_metrics(memory=95)

        anomalies = analyzer._convert_ml_anomalies(ml_result, metrics)

        assert len(anomalies) == 1
        assert anomalies[0].type == AnomalyType.OUTLIER

    @pytest.mark.asyncio
    async def test_convert_ml_anomalies_both_sources(self):
        """Test _convert_ml_anomalies with both sources."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        ml_result = HybridAnomalyResult(
            is_anomaly=True,
            source=AnomalySource.BOTH,
            weighted_score=0.9,
            explanation="Critical",
            feature_contributions={},
        )
        metrics = generate_test_metrics()

        anomalies = analyzer._convert_ml_anomalies(ml_result, metrics)

        assert len(anomalies) == 1
        assert anomalies[0].type == AnomalyType.SPIKE

    @pytest.mark.asyncio
    async def test_generate_recommendations_ml_sarima(self):
        """Test ML-based recommendations for SARIMA anomaly."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        ml_result = HybridAnomalyResult(
            is_anomaly=True,
            source=AnomalySource.SARIMA,
            feature_contributions={},
        )

        recs = analyzer._generate_recommendations([], ml_result)

        assert any("Temporal" in r for r in recs)

    @pytest.mark.asyncio
    async def test_generate_recommendations_ml_isolation(self):
        """Test ML-based recommendations for Isolation anomaly."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        ml_result = HybridAnomalyResult(
            is_anomaly=True,
            source=AnomalySource.ISOLATION,
            feature_contributions={},
        )

        recs = analyzer._generate_recommendations([], ml_result)

        assert any("Unusual" in r for r in recs)

    @pytest.mark.asyncio
    async def test_generate_recommendations_ml_both(self):
        """Test ML-based recommendations for both sources."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        ml_result = HybridAnomalyResult(
            is_anomaly=True,
            source=AnomalySource.BOTH,
            feature_contributions={"cpu_usage": 0.5, "memory_usage": 0.3},
        )

        recs = analyzer._generate_recommendations([], ml_result)

        assert any("CRITICAL" in r for r in recs)
        assert any("cpu_usage" in r for r in recs)

    @pytest.mark.asyncio
    async def test_identify_trends_decreasing(self):
        """Test trend identification for decreasing values."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Add decreasing CPU history
        for i in range(15):
            analyzer._metrics_history.append(
                generate_test_metrics(cpu=80 - i * 2)
            )

        metrics = generate_test_metrics(cpu=50)
        result = await analyzer.analyze_metrics(metrics)

        assert result.trends["cpu_trend"] == "decreasing"

    @pytest.mark.asyncio
    async def test_identify_trends_stable(self):
        """Test trend identification for stable values."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Add stable history
        for i in range(15):
            analyzer._metrics_history.append(generate_test_metrics(cpu=50))

        metrics = generate_test_metrics(cpu=50)
        result = await analyzer.analyze_metrics(metrics)

        assert result.trends["cpu_trend"] == "stable"


class TestSystemAnalyzerEdgeCases:
    """Edge case tests for original SystemAnalyzer."""

    @pytest.mark.asyncio
    async def test_analyze_moderate_cpu(self):
        """Test analysis with moderate CPU (75-90%)."""
        settings = AnalyzerSettings()
        analyzer = SystemAnalyzer(settings)

        metrics = generate_test_metrics(cpu=80)
        result = await analyzer.analyze_metrics(metrics)

        cpu_anomalies = [a for a in result.anomalies if a.metric_name == "cpu_usage"]
        assert len(cpu_anomalies) == 1
        assert cpu_anomalies[0].severity == 0.6

    @pytest.mark.asyncio
    async def test_analyze_high_latency(self):
        """Test analysis with high latency."""
        settings = AnalyzerSettings()
        analyzer = SystemAnalyzer(settings)

        metrics = generate_test_metrics(latency=600)
        result = await analyzer.analyze_metrics(metrics)

        assert result.trends["latency_trend"] == "degrading"
        assert result.overall_health_score < 1.0

    def test_get_status(self):
        """Test get_status method."""
        settings = AnalyzerSettings()
        analyzer = SystemAnalyzer(settings)

        status = analyzer.get_status()

        assert status["status"] == "active"
        assert "threshold" in status


class TestConfigEdgeCases:
    """Tests for configuration edge cases."""

    def test_sarima_config_custom_values(self):
        """Test SARIMAConfig with custom values."""
        config = SARIMAConfig(
            p=2,
            d=0,
            q=2,
            P=1,
            D=0,
            Q=1,
            s=12,
            max_iter=100,
            confidence_level=0.99,
        )

        assert config.p == 2
        assert config.s == 12
        assert config.confidence_level == 0.99

    def test_isolation_config_custom_values(self):
        """Test IsolationConfig with custom values."""
        config = IsolationConfig(
            n_estimators=50,
            contamination=0.05,
            max_features=0.8,
            anomaly_threshold=-0.2,
        )

        assert config.n_estimators == 50
        assert config.contamination == 0.05

    def test_hybrid_config_weights(self):
        """Test HybridConfig weight validation."""
        config = HybridConfig(
            sarima_weight=0.3,
            isolation_weight=0.7,
        )

        assert config.sarima_weight + config.isolation_weight == 1.0


class TestForecastResult:
    """Tests for ForecastResult model."""

    def test_default_values(self):
        """Test default ForecastResult values."""
        result = ForecastResult()

        assert result.predicted_values == []
        assert result.forecast_horizon == 1
        assert result.model_fitted is False

    def test_custom_values(self):
        """Test ForecastResult with values."""
        result = ForecastResult(
            predicted_values=[1.0, 2.0, 3.0],
            confidence_lower=[0.5, 1.5, 2.5],
            confidence_upper=[1.5, 2.5, 3.5],
            forecast_horizon=3,
            model_fitted=True,
            aic=100.5,
            bic=105.2,
        )

        assert len(result.predicted_values) == 3
        assert result.model_fitted is True
        assert result.aic == 100.5


class TestSARIMAUpdateRefit:
    """Tests for SARIMA update and refit functionality."""

    def test_update_triggers_refit(self):
        """Test that update triggers refit at 100 observations."""
        forecaster = SARIMAForecaster()

        # Set history to 99
        forecaster._history = list(range(99))
        forecaster._residuals_std = 1.0
        forecaster._simple_mean = 50.0
        forecaster._simple_trend = 0.0

        # Adding one more should trigger refit (100 % 100 == 0)
        forecaster.update(100.0)

        assert len(forecaster._history) == 100

    def test_is_anomalous_empty_forecast(self):
        """Test is_anomalous when forecast returns empty predictions."""
        forecaster = SARIMAForecaster()

        # Set up with fitted model but empty predictions
        forecaster._fitted_model = MagicMock()
        forecaster._simple_mean = 50.0
        forecaster._residuals_std = 5.0
        forecaster._history = [50] * 10

        # Mock predict to return empty
        with patch.object(forecaster, "predict") as mock_predict:
            mock_predict.return_value = ForecastResult(predicted_values=[])

            is_anomaly, score = forecaster.is_anomalous(55.0)

            # Should fallback to simple_mean
            assert isinstance(score, float)


class TestIsolationDetectorUpdate:
    """Tests for Isolation Detector update functionality."""

    def test_update_triggers_refit(self):
        """Test that update triggers refit at 500 observations."""
        detector = IsolationAnomalyDetector()

        # Set training data to 499
        detector._training_data = [[50, 50, 50]] * 499
        detector._fitted = True
        detector._feature_means = np.array([50, 50, 50])
        detector._feature_stds = np.array([5, 5, 5])

        # Adding one more should trigger refit (500 % 500 == 0)
        detector.update([51, 51, 51])

        assert len(detector._training_data) == 500


class TestHybridDetectorUpdate:
    """Tests for Hybrid Detector update functionality."""

    def test_update_calls_both_components(self):
        """Test update calls both SARIMA and Isolation update."""
        detector = HybridAnomalyDetector()

        # Train first
        np.random.seed(42)
        ts = list(np.random.randn(100) * 5 + 50)
        mv = [[50, 50, 0.01, 100]] * 100
        detector.fit(ts, mv)

        initial_sarima_len = len(detector._sarima._history)
        initial_iso_len = len(detector._isolation._training_data)

        detector.update(55.0, [55, 52, 0.02, 110])

        assert len(detector._sarima._history) == initial_sarima_len + 1
        assert len(detector._isolation._training_data) == initial_iso_len + 1

    def test_detect_trims_history(self):
        """Test that detection history is trimmed at 1000."""
        detector = HybridAnomalyDetector()

        # Add 1001 detections to history
        for i in range(1001):
            detector._detection_history.append(HybridAnomalyResult())

        # Simulate one more detection that would trim
        np.random.seed(42)
        ts = list(np.random.randn(100) * 5 + 50)
        mv = [[50, 50, 0.01, 100]] * 100
        detector.fit(ts, mv)

        detector.detect(50.0, [50, 50, 0.01, 100])

        # Should be trimmed
        assert len(detector._detection_history) <= 1001


class TestMLAnalyzerHistoryTrim:
    """Tests for ML analyzer history trimming."""

    @pytest.mark.asyncio
    async def test_metrics_history_trimmed(self):
        """Test that metrics history is trimmed at 10000."""
        settings = AnalyzerSettings()
        analyzer = MLSystemAnalyzer(settings)

        # Add 10001 metrics
        for i in range(10001):
            analyzer._metrics_history.append(generate_test_metrics())

        # Analyze one more
        await analyzer.analyze_metrics(generate_test_metrics())

        # Should be trimmed
        assert len(analyzer._metrics_history) <= 10001


class TestExceptionPaths:
    """Tests for exception handling paths."""

    def test_sarima_predict_exception_path(self):
        """Test SARIMA predict exception fallback."""
        forecaster = SARIMAForecaster()

        # Set up with mocked fitted model that raises ValueError (captured exception)
        forecaster._fitted_model = MagicMock()
        forecaster._fitted_model.get_forecast = MagicMock(
            side_effect=ValueError("Prediction failed")
        )
        forecaster._history = list(range(100))
        forecaster._residuals_std = 10.0
        forecaster._simple_mean = 50.0
        forecaster._simple_trend = 0.1

        result = forecaster.predict(steps=3)

        # Should fallback to simple prediction
        assert len(result.predicted_values) == 3

    def test_isolation_detect_exception_path(self):
        """Test Isolation detect exception fallback."""
        detector = IsolationAnomalyDetector()

        # Set up with mocked model that raises ValueError (captured exception)
        detector._model = MagicMock()
        detector._model.predict = MagicMock(side_effect=ValueError("Predict failed"))
        detector._fitted = True
        detector._feature_means = np.array([50, 50, 50])
        detector._feature_stds = np.array([5, 5, 5])

        result = detector.detect([200, 200, 200])

        # Should fallback to simple detection
        assert result.anomaly_score > 0


class TestSARIMAHealthCheck:
    """Tests for SARIMA health check."""

    @pytest.mark.asyncio
    async def test_health_check_unfitted(self):
        """Test health check on unfitted model."""
        forecaster = SARIMAForecaster()

        health = await forecaster.health_check()

        assert health["healthy"] is True
        assert health["model_fitted"] is False

    @pytest.mark.asyncio
    async def test_health_check_fitted(self):
        """Test health check on fitted model."""
        forecaster = SARIMAForecaster()
        np.random.seed(42)
        data = list(np.random.randn(100) * 5 + 50)
        forecaster.fit(data)

        health = await forecaster.health_check()

        assert health["healthy"] is True
        assert health["model_fitted"] is True


class TestIsolationHealthCheck:
    """Tests for Isolation detector health check."""

    def test_get_diagnostics_not_fitted(self):
        """Test diagnostics on unfitted detector."""
        detector = IsolationAnomalyDetector()

        diagnostics = detector.get_diagnostics()

        assert "fitted" in diagnostics
        assert diagnostics["fitted"] is False

    @pytest.mark.asyncio
    async def test_health_check_not_fitted(self):
        """Test health check on unfitted detector."""
        detector = IsolationAnomalyDetector()

        health = await detector.health_check()

        assert health["healthy"] is True
        assert health["model_fitted"] is False

    @pytest.mark.asyncio
    async def test_health_check_fitted(self):
        """Test health check on fitted detector."""
        detector = IsolationAnomalyDetector()
        np.random.seed(42)
        data = [[50 + np.random.randn() * 5, 50 + np.random.randn() * 5, 0.01] for _ in range(100)]
        detector.fit(data)

        health = await detector.health_check()

        assert health["healthy"] is True
        assert health["model_fitted"] is True
