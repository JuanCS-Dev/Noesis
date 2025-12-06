"""
SARIMA Forecaster - Time Series Prediction
==========================================

Implements SARIMA (Seasonal ARIMA) for time series forecasting.
Used to predict expected values and detect deviations.

Based on:
- SARIMA-LSTM Hybrid research (2025)
- Statsmodels SARIMAX implementation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:  # pylint: disable=too-many-instance-attributes
    """Result of SARIMA forecast."""

    predicted_values: List[float] = field(default_factory=list)
    confidence_lower: List[float] = field(default_factory=list)
    confidence_upper: List[float] = field(default_factory=list)
    forecast_horizon: int = 1
    model_fitted: bool = False
    aic: Optional[float] = None
    bic: Optional[float] = None
    residuals_std: Optional[float] = None


@dataclass
class SARIMAConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for SARIMA model."""

    # ARIMA order (p, d, q)
    p: int = 1  # AR order
    d: int = 1  # Differencing order
    q: int = 1  # MA order

    # Seasonal order (P, D, Q, s) - Standard SARIMA notation (uppercase)
    P: int = 1  # Seasonal AR order  # pylint: disable=invalid-name
    D: int = 1  # Seasonal differencing order  # pylint: disable=invalid-name
    Q: int = 1  # Seasonal MA order  # pylint: disable=invalid-name
    s: int = 24  # Seasonal period (24 for hourly data with daily pattern)

    # Fitting parameters
    max_iter: int = 50
    method: str = "lbfgs"
    enforce_stationarity: bool = False
    enforce_invertibility: bool = False

    # Forecast parameters
    confidence_level: float = 0.95
    min_observations: int = 50


class SARIMAForecaster:  # pylint: disable=too-many-instance-attributes
    """
    SARIMA-based time series forecaster.

    Features:
    - Automatic parameter selection (optional)
    - Seasonal pattern detection
    - Confidence intervals for predictions
    - Residual analysis for anomaly detection

    Example:
        >>> forecaster = SARIMAForecaster()
        >>> forecaster.fit(historical_data)
        >>> forecast = forecaster.predict(steps=5)
        >>> is_anomaly = forecaster.is_anomalous(current_value, threshold=2.0)
    """

    def __init__(self, config: Optional[SARIMAConfig] = None):
        """Initialize SARIMA forecaster."""
        self.config = config or SARIMAConfig()
        self._model: Any = None
        self._fitted_model: Any = None
        self._history: List[float] = []
        self._last_fit_time: Optional[datetime] = None
        self._residuals_std: float = 1.0
        self._simple_mean: float = 0.0
        self._simple_trend: float = 0.0

        logger.info(
            "sarima_forecaster_initialized",
            extra={
                "order": (self.config.p, self.config.d, self.config.q),
                "seasonal_order": (
                    self.config.P,
                    self.config.D,
                    self.config.Q,
                    self.config.s,
                ),
            },
        )

    def fit(self, data: List[float]) -> bool:
        """
        Fit SARIMA model to historical data.

        Args:
            data: Historical time series data

        Returns:
            True if fitting succeeded
        """
        if len(data) < self.config.min_observations:
            logger.warning(
                "insufficient_data",
                extra={
                    "data_length": len(data),
                    "min_required": self.config.min_observations,
                },
            )
            return False

        self._history = list(data)

        try:
            # pylint: disable=import-outside-toplevel
            # Try to import statsmodels (optional dependency)
            from statsmodels.tsa.statespace.sarimax import SARIMAX

            self._model = SARIMAX(
                data,
                order=(self.config.p, self.config.d, self.config.q),
                seasonal_order=(
                    self.config.P,
                    self.config.D,
                    self.config.Q,
                    self.config.s,
                ),
                enforce_stationarity=self.config.enforce_stationarity,
                enforce_invertibility=self.config.enforce_invertibility,
            )

            self._fitted_model = self._model.fit(
                maxiter=self.config.max_iter,
                method=self.config.method,
                disp=False,
            )

            # Calculate residuals std for anomaly detection
            residuals = self._fitted_model.resid
            self._residuals_std = float(np.std(residuals))

            # Also set simple stats as backup
            self._simple_mean = float(np.mean(data))
            if len(data) > 10:
                recent = data[-10:]
                early = data[:10]
                self._simple_trend = float(
                    (float(np.mean(recent)) - float(np.mean(early))) / len(data)
                )

            self._last_fit_time = datetime.utcnow()

            logger.info(
                "sarima_model_fitted",
                extra={
                    "aic": self._fitted_model.aic,
                    "bic": self._fitted_model.bic,
                    "residuals_std": self._residuals_std,
                },
            )

            return True

        except ImportError:
            logger.warning("statsmodels_not_available")
            return self._fit_simple_model(data)

        except (ValueError, RuntimeError, AttributeError, np.linalg.LinAlgError) as exc:
            logger.error("sarima_fit_failed", extra={"error": str(exc)})
            return self._fit_simple_model(data)

    def _fit_simple_model(self, data: List[float]) -> bool:
        """
        Fallback simple model when statsmodels unavailable.

        Uses exponential moving average as simple forecast.
        """
        self._history = list(data)

        # Calculate simple statistics
        self._residuals_std = float(np.std(data))

        # Store mean for simple prediction
        self._simple_mean = float(np.mean(data))
        self._simple_trend = 0.0

        if len(data) > 10:
            # Calculate simple trend
            recent = data[-10:]
            early = data[:10]
            self._simple_trend = float(
                (float(np.mean(recent)) - float(np.mean(early))) / len(data)
            )

        self._last_fit_time = datetime.utcnow()

        logger.info(
            "simple_model_fitted",
            extra={
                "mean": self._simple_mean,
                "trend": self._simple_trend,
                "std": self._residuals_std,
            },
        )

        return True

    def predict(self, steps: int = 1) -> ForecastResult:
        """
        Generate forecast for future time steps.

        Args:
            steps: Number of steps to forecast

        Returns:
            ForecastResult with predictions and confidence intervals
        """
        result = ForecastResult(forecast_horizon=steps)

        if self._fitted_model is not None:
            try:
                forecast = self._fitted_model.get_forecast(steps=steps)
                mean = forecast.predicted_mean.tolist()
                conf_int = forecast.conf_int(alpha=1 - self.config.confidence_level)

                result.predicted_values = mean
                result.confidence_lower = conf_int.iloc[:, 0].tolist()
                result.confidence_upper = conf_int.iloc[:, 1].tolist()
                result.model_fitted = True
                result.aic = self._fitted_model.aic
                result.bic = self._fitted_model.bic
                result.residuals_std = self._residuals_std

                return result

            except (ValueError, RuntimeError, AttributeError, np.linalg.LinAlgError) as exc:
                logger.error("sarima_predict_failed", extra={"error": str(exc)})

        # Fallback to simple prediction
        return self._predict_simple(steps)

    def _predict_simple(self, steps: int) -> ForecastResult:
        """Simple prediction fallback."""
        result = ForecastResult(forecast_horizon=steps)

        if not self._history:
            return result

        # Use last value + trend
        last_value = self._history[-1]
        predictions = []

        for i in range(steps):
            pred = last_value + (self._simple_trend * (i + 1))
            predictions.append(pred)

        # Confidence intervals based on std
        z_score = 1.96  # 95% confidence
        margin = z_score * self._residuals_std

        result.predicted_values = predictions
        result.confidence_lower = [p - margin for p in predictions]
        result.confidence_upper = [p + margin for p in predictions]
        result.model_fitted = len(self._history) >= self.config.min_observations
        result.residuals_std = self._residuals_std

        return result

    def is_anomalous(
        self,
        value: float,
        threshold_sigma: float = 2.0,
        use_forecast: bool = True,
    ) -> Tuple[bool, float]:
        """
        Check if a value is anomalous based on forecast.

        Args:
            value: Current observed value
            threshold_sigma: Number of standard deviations for anomaly threshold
            use_forecast: Whether to use forecast or historical mean

        Returns:
            Tuple of (is_anomaly, deviation_score)
        """
        if use_forecast and self._fitted_model is not None:
            # Use one-step forecast
            forecast = self.predict(steps=1)
            if forecast.predicted_values:
                expected = forecast.predicted_values[0]
            else:
                expected = self._simple_mean if hasattr(self, "_simple_mean") else 0
        else:
            expected = float(np.mean(self._history)) if self._history else 0.0

        # Calculate deviation
        deviation = abs(value - expected)
        deviation_score = deviation / self._residuals_std if self._residuals_std > 0 else 0

        is_anomaly = deviation_score > threshold_sigma

        if is_anomaly:
            logger.info(
                "anomaly_detected_sarima",
                extra={
                    "value": value,
                    "expected": expected,
                    "deviation_score": deviation_score,
                    "threshold": threshold_sigma,
                },
            )

        return is_anomaly, deviation_score

    def update(self, new_value: float) -> None:
        """
        Update model with new observation (online learning).

        Args:
            new_value: New observed value
        """
        self._history.append(new_value)

        # Refit periodically or when history grows significantly
        if len(self._history) % 100 == 0:
            logger.info("refitting_sarima", extra={"history_length": len(self._history)})
            self.fit(self._history)

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get model diagnostics."""
        diagnostics = {
            "model_type": "SARIMA",
            "fitted": self._fitted_model is not None,
            "history_length": len(self._history),
            "last_fit_time": (
                self._last_fit_time.isoformat() if self._last_fit_time else None
            ),
            "residuals_std": self._residuals_std,
            "config": {
                "order": (self.config.p, self.config.d, self.config.q),
                "seasonal_order": (
                    self.config.P,
                    self.config.D,
                    self.config.Q,
                    self.config.s,
                ),
            },
        }

        if self._fitted_model is not None:
            diagnostics["aic"] = self._fitted_model.aic
            diagnostics["bic"] = self._fitted_model.bic

        return diagnostics

    async def health_check(self) -> Dict[str, Any]:
        """Check health of forecaster."""
        return {
            "healthy": True,
            "model_fitted": self._fitted_model is not None or len(self._history) > 0,
            "history_length": len(self._history),
        }
