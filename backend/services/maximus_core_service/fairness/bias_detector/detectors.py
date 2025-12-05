"""Bias Detection Methods.

Mixin providing bias detection methods.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy import stats

from ..base import BiasDetectionResult, InsufficientDataException, ProtectedAttribute

if TYPE_CHECKING:
    from .detector import BiasDetector

logger = logging.getLogger(__name__)


class DetectorMixin:
    """Mixin providing detection methods.

    Provides methods for:
    - Statistical parity detection
    - Disparate impact detection
    - Distribution bias detection
    - Performance disparity detection
    """

    min_sample_size: int
    significance_level: float
    disparate_impact_threshold: float
    sensitivity: str

    def detect_statistical_parity_bias(
        self: BiasDetector,
        predictions: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> BiasDetectionResult:
        """Detect bias using statistical parity (chi-square test).

        Args:
            predictions: Model predictions.
            protected_attribute: Protected attribute values.
            protected_value: Value indicating protected group.

        Returns:
            BiasDetectionResult with detection outcome.
        """
        if predictions.dtype == float and np.max(predictions) <= 1.0:
            binary_predictions = (predictions > 0.5).astype(int)
        else:
            binary_predictions = predictions.astype(int)

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        group_0_neg = np.sum((binary_predictions == 0) & group_0_mask)
        group_0_pos = np.sum((binary_predictions == 1) & group_0_mask)
        group_1_neg = np.sum((binary_predictions == 0) & group_1_mask)
        group_1_pos = np.sum((binary_predictions == 1) & group_1_mask)

        contingency_table = np.array([
            [group_0_neg, group_0_pos],
            [group_1_neg, group_1_pos],
        ])

        chi2, p_value, dof, _ = stats.chi2_contingency(contingency_table)

        bias_detected = p_value < self.significance_level

        n_total = n0 + n1
        cramer_v = np.sqrt(chi2 / n_total)

        severity = self._determine_severity(p_value, cramer_v, method="chi_square")
        confidence = 1.0 - p_value if bias_detected else p_value

        pos_rate_0 = group_0_pos / n0
        pos_rate_1 = group_1_pos / n1
        affected_groups = []

        if bias_detected:
            if pos_rate_0 > pos_rate_1:
                affected_groups.append(
                    f"Protected group (lower positive rate: "
                    f"{pos_rate_1:.2%} vs {pos_rate_0:.2%})"
                )
            else:
                affected_groups.append(
                    f"Reference group (lower positive rate: "
                    f"{pos_rate_0:.2%} vs {pos_rate_1:.2%})"
                )

        result = BiasDetectionResult(
            bias_detected=bias_detected,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            detection_method="statistical_parity_chi_square",
            p_value=float(p_value),
            effect_size=float(cramer_v),
            confidence=float(confidence),
            affected_groups=affected_groups,
            severity=severity,
            sample_size=int(n_total),
            metadata={
                "chi2_statistic": float(chi2),
                "degrees_of_freedom": int(dof),
                "contingency_table": contingency_table.tolist(),
                "pos_rate_group_0": float(pos_rate_0),
                "pos_rate_group_1": float(pos_rate_1),
                "cramers_v": float(cramer_v),
            },
        )

        logger.debug(
            "Statistical Parity Test: chi2=%.3f, p=%.4f, bias_detected=%s, severity=%s",
            chi2,
            p_value,
            bias_detected,
            severity,
        )

        return result

    def detect_disparate_impact(
        self: BiasDetector,
        predictions: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> BiasDetectionResult:
        """Detect bias using disparate impact analysis (4/5ths rule).

        Args:
            predictions: Model predictions.
            protected_attribute: Protected attribute values.
            protected_value: Value indicating protected group.

        Returns:
            BiasDetectionResult with detection outcome.
        """
        if predictions.dtype == float and np.max(predictions) <= 1.0:
            binary_predictions = (predictions > 0.5).astype(int)
        else:
            binary_predictions = predictions.astype(int)

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        selection_rate_0 = np.mean(binary_predictions[group_0_mask])
        selection_rate_1 = np.mean(binary_predictions[group_1_mask])

        if selection_rate_0 > 0:
            di_ratio = selection_rate_1 / selection_rate_0
        else:
            di_ratio = 1.0 if selection_rate_1 == 0 else float("inf")

        bias_detected = di_ratio < self.disparate_impact_threshold

        if di_ratio > (1.0 / self.disparate_impact_threshold):
            bias_detected = True

        deviation = abs(di_ratio - 1.0)
        if deviation < 0.1:
            severity = "low"
        elif deviation < 0.3:
            severity = "medium"
        elif deviation < 0.5:
            severity = "high"
        else:
            severity = "critical"

        confidence = min(
            1.0, deviation * np.sqrt(min(n0, n1) / self.min_sample_size)
        )

        affected_groups = []
        if bias_detected:
            if di_ratio < self.disparate_impact_threshold:
                affected_groups.append(
                    f"Protected group (selection rate {selection_rate_1:.2%} is "
                    f"{di_ratio:.1%} of reference group rate {selection_rate_0:.2%})"
                )
            else:
                affected_groups.append(
                    f"Reference group (protected group favored with ratio {di_ratio:.2f})"
                )

        result = BiasDetectionResult(
            bias_detected=bias_detected,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            detection_method="disparate_impact_4_5ths_rule",
            p_value=None,
            effect_size=float(abs(1.0 - di_ratio)),
            confidence=float(confidence),
            affected_groups=affected_groups,
            severity=severity,
            sample_size=int(n0 + n1),
            metadata={
                "disparate_impact_ratio": float(di_ratio),
                "selection_rate_group_0": float(selection_rate_0),
                "selection_rate_group_1": float(selection_rate_1),
                "threshold": self.disparate_impact_threshold,
                "passes_4_5ths_rule": di_ratio >= self.disparate_impact_threshold,
            },
        )

        logger.debug(
            "Disparate Impact: ratio=%.3f, threshold=%.2f, bias_detected=%s, severity=%s",
            di_ratio,
            self.disparate_impact_threshold,
            bias_detected,
            severity,
        )

        return result

    def detect_distribution_bias(
        self: BiasDetector,
        predictions: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> BiasDetectionResult:
        """Detect bias using distribution comparison (KS test).

        Args:
            predictions: Model predictions.
            protected_attribute: Protected attribute values.
            protected_value: Value indicating protected group.

        Returns:
            BiasDetectionResult with detection outcome.
        """
        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        preds_0 = predictions[group_0_mask]
        preds_1 = predictions[group_1_mask]

        ks_statistic, p_value = stats.ks_2samp(preds_0, preds_1)

        bias_detected = p_value < self.significance_level

        mean_0 = np.mean(preds_0)
        mean_1 = np.mean(preds_1)
        std_0 = np.std(preds_0, ddof=1)
        std_1 = np.std(preds_1, ddof=1)

        pooled_std = np.sqrt(
            ((n0 - 1) * std_0**2 + (n1 - 1) * std_1**2) / (n0 + n1 - 2)
        )

        cohens_d = (mean_0 - mean_1) / pooled_std if pooled_std > 0 else 0.0

        severity = self._determine_severity(p_value, abs(cohens_d), method="ks_test")
        confidence = 1.0 - p_value if bias_detected else p_value

        affected_groups = []
        if bias_detected:
            if mean_0 > mean_1:
                affected_groups.append(
                    f"Protected group (lower mean score: {mean_1:.3f} vs {mean_0:.3f})"
                )
            else:
                affected_groups.append(
                    f"Reference group (lower mean score: {mean_0:.3f} vs {mean_1:.3f})"
                )

        result = BiasDetectionResult(
            bias_detected=bias_detected,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            detection_method="distribution_ks_test",
            p_value=float(p_value),
            effect_size=float(abs(cohens_d)),
            confidence=float(confidence),
            affected_groups=affected_groups,
            severity=severity,
            sample_size=int(n0 + n1),
            metadata={
                "ks_statistic": float(ks_statistic),
                "mean_group_0": float(mean_0),
                "mean_group_1": float(mean_1),
                "std_group_0": float(std_0),
                "std_group_1": float(std_1),
                "cohens_d": float(cohens_d),
                "effect_size_category": self._categorize_effect_size(abs(cohens_d)),
            },
        )

        logger.debug(
            "Distribution Test: KS=%.3f, p=%.4f, Cohen's d=%.3f, bias_detected=%s",
            ks_statistic,
            p_value,
            cohens_d,
            bias_detected,
        )

        return result

    def detect_performance_disparity(
        self: BiasDetector,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        protected_attribute: np.ndarray,
        protected_value: Any = 1,
    ) -> BiasDetectionResult:
        """Detect bias through performance disparity across groups.

        Args:
            predictions: Model predictions.
            true_labels: True labels.
            protected_attribute: Protected attribute values.
            protected_value: Value indicating protected group.

        Returns:
            BiasDetectionResult with detection outcome.
        """
        if predictions.dtype == float and np.max(predictions) <= 1.0:
            binary_predictions = (predictions > 0.5).astype(int)
        else:
            binary_predictions = predictions.astype(int)

        binary_labels = true_labels.astype(int)

        group_0_mask = protected_attribute != protected_value
        group_1_mask = protected_attribute == protected_value

        n0 = np.sum(group_0_mask)
        n1 = np.sum(group_1_mask)

        if n0 < self.min_sample_size or n1 < self.min_sample_size:
            raise InsufficientDataException(self.min_sample_size, min(n0, n1))

        accuracy_0 = np.mean(
            binary_predictions[group_0_mask] == binary_labels[group_0_mask]
        )
        accuracy_1 = np.mean(
            binary_predictions[group_1_mask] == binary_labels[group_1_mask]
        )

        f1_0 = self._calculate_f1_score(
            binary_predictions[group_0_mask], binary_labels[group_0_mask]
        )
        f1_1 = self._calculate_f1_score(
            binary_predictions[group_1_mask], binary_labels[group_1_mask]
        )

        accuracy_diff = abs(accuracy_0 - accuracy_1)
        f1_diff = abs(f1_0 - f1_1)

        thresholds = {"low": 0.15, "medium": 0.10, "high": 0.05}
        threshold = thresholds.get(self.sensitivity, 0.10)

        bias_detected = (accuracy_diff > threshold) or (f1_diff > threshold)

        max_diff = max(accuracy_diff, f1_diff)
        if max_diff < 0.05:
            severity = "low"
        elif max_diff < 0.10:
            severity = "medium"
        elif max_diff < 0.20:
            severity = "high"
        else:
            severity = "critical"

        confidence = min(
            1.0, max_diff * 5 * np.sqrt(min(n0, n1) / self.min_sample_size)
        )

        affected_groups = []
        if bias_detected:
            if accuracy_0 > accuracy_1:
                affected_groups.append(
                    f"Protected group (lower accuracy: "
                    f"{accuracy_1:.2%} vs {accuracy_0:.2%})"
                )
            elif accuracy_1 > accuracy_0:
                affected_groups.append(
                    f"Reference group (lower accuracy: "
                    f"{accuracy_0:.2%} vs {accuracy_1:.2%})"
                )

        result = BiasDetectionResult(
            bias_detected=bias_detected,
            protected_attribute=ProtectedAttribute.GEOGRAPHIC_LOCATION,
            detection_method="performance_disparity",
            p_value=None,
            effect_size=float(max_diff),
            confidence=float(confidence),
            affected_groups=affected_groups,
            severity=severity,
            sample_size=int(n0 + n1),
            metadata={
                "accuracy_group_0": float(accuracy_0),
                "accuracy_group_1": float(accuracy_1),
                "accuracy_difference": float(accuracy_diff),
                "f1_group_0": float(f1_0),
                "f1_group_1": float(f1_1),
                "f1_difference": float(f1_diff),
                "threshold": threshold,
            },
        )

        logger.debug(
            "Performance Disparity: acc_diff=%.3f, f1_diff=%.3f, "
            "bias_detected=%s, severity=%s",
            accuracy_diff,
            f1_diff,
            bias_detected,
            severity,
        )

        return result
