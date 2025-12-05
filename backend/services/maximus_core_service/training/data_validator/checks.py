"""Validation Check Methods.

Mixin providing validation check methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .models import ValidationIssue, ValidationSeverity

if TYPE_CHECKING:
    from .validator import DataValidator


class CheckMixin:
    """Mixin providing validation check methods.

    Provides methods for:
    - Missing values check
    - Outlier detection
    - Label distribution analysis
    - Feature distribution analysis
    - Data drift detection
    """

    features: np.ndarray
    labels: np.ndarray
    reference_features: np.ndarray | None
    feature_names: list[str]

    def _check_missing_values(
        self: DataValidator,
        missing_threshold: float,
    ) -> tuple[list[ValidationIssue], dict[str, Any]]:
        """Check for missing values (NaN, Inf).

        Args:
            missing_threshold: Maximum fraction of missing values allowed.

        Returns:
            Tuple of (issues, statistics).
        """
        issues = []
        statistics: dict[str, Any] = {}

        nan_mask = np.isnan(self.features)
        n_nan = nan_mask.sum()
        nan_fraction = n_nan / self.features.size

        statistics["n_nan_values"] = int(n_nan)
        statistics["nan_fraction"] = float(nan_fraction)

        if n_nan > 0:
            nan_features = nan_mask.any(axis=0)
            nan_feature_indices = np.where(nan_features)[0]
            feature_list = [self.feature_names[i] for i in nan_feature_indices]

            severity = (
                ValidationSeverity.ERROR
                if nan_fraction > missing_threshold
                else ValidationSeverity.WARNING
            )
            issues.append(
                ValidationIssue(
                    severity=severity,
                    check_name="missing_values",
                    message=f"Found {n_nan} NaN values ({nan_fraction:.2%})",
                    details={"nan_features": feature_list},
                )
            )

        inf_mask = np.isinf(self.features)
        n_inf = inf_mask.sum()
        inf_fraction = n_inf / self.features.size

        statistics["n_inf_values"] = int(n_inf)
        statistics["inf_fraction"] = float(inf_fraction)

        if n_inf > 0:
            inf_features = inf_mask.any(axis=0)
            inf_feature_indices = np.where(inf_features)[0]
            feature_list = [self.feature_names[i] for i in inf_feature_indices]

            severity = (
                ValidationSeverity.ERROR
                if inf_fraction > missing_threshold
                else ValidationSeverity.WARNING
            )
            issues.append(
                ValidationIssue(
                    severity=severity,
                    check_name="missing_values",
                    message=f"Found {n_inf} Inf values ({inf_fraction:.2%})",
                    details={"inf_features": feature_list},
                )
            )

        if n_nan == 0 and n_inf == 0:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    check_name="missing_values",
                    message="No missing values detected",
                )
            )

        return issues, statistics

    def _check_outliers(
        self: DataValidator,
        outlier_threshold: float,
    ) -> tuple[list[ValidationIssue], dict[str, Any]]:
        """Check for outliers using Z-score.

        Args:
            outlier_threshold: Z-score threshold.

        Returns:
            Tuple of (issues, statistics).
        """
        issues = []
        statistics: dict[str, Any] = {}

        mean = np.nanmean(self.features, axis=0)
        std = np.nanstd(self.features, axis=0)
        std[std == 0] = 1.0

        z_scores = np.abs((self.features - mean) / std)

        outlier_mask = z_scores > outlier_threshold
        n_outliers = outlier_mask.sum()
        outlier_fraction = n_outliers / self.features.size

        statistics["n_outliers"] = int(n_outliers)
        statistics["outlier_fraction"] = float(outlier_fraction)
        statistics["outlier_threshold"] = float(outlier_threshold)

        if n_outliers > 0:
            outliers_per_feature = outlier_mask.sum(axis=0)
            top_outlier_features = np.argsort(outliers_per_feature)[-5:][::-1]

            severity = (
                ValidationSeverity.WARNING
                if outlier_fraction < 0.05
                else ValidationSeverity.ERROR
            )
            issues.append(
                ValidationIssue(
                    severity=severity,
                    check_name="outliers",
                    message=f"Found {n_outliers} outliers ({outlier_fraction:.2%})",
                    details={
                        "top_outlier_features": [
                            (self.feature_names[i], int(outliers_per_feature[i]))
                            for i in top_outlier_features
                        ]
                    },
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    check_name="outliers",
                    message=f"No outliers detected (threshold={outlier_threshold})",
                )
            )

        return issues, statistics

    def _check_labels(
        self: DataValidator,
    ) -> tuple[list[ValidationIssue], dict[str, Any]]:
        """Check label distribution.

        Returns:
            Tuple of (issues, statistics).
        """
        issues = []
        statistics: dict[str, Any] = {}

        labeled_mask = self.labels >= 0
        labeled_labels = self.labels[labeled_mask]

        n_labeled = len(labeled_labels)
        n_unlabeled = len(self.labels) - n_labeled

        statistics["n_labeled"] = int(n_labeled)
        statistics["n_unlabeled"] = int(n_unlabeled)
        statistics["label_fraction"] = float(n_labeled / len(self.labels))

        if n_labeled == 0:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    check_name="labels",
                    message="No labeled samples found",
                )
            )
            return issues, statistics

        unique_labels, label_counts = np.unique(labeled_labels, return_counts=True)
        class_distribution = dict(
            zip(unique_labels.tolist(), label_counts.tolist(), strict=False)
        )

        statistics["class_distribution"] = class_distribution
        statistics["n_classes"] = len(unique_labels)

        max_count = label_counts.max()
        min_count = label_counts.min()
        imbalance_ratio = max_count / min_count

        statistics["imbalance_ratio"] = float(imbalance_ratio)

        if imbalance_ratio > 10:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    check_name="labels",
                    message=f"Severe class imbalance detected (ratio={imbalance_ratio:.1f}:1)",
                    details={"class_distribution": class_distribution},
                )
            )
        elif imbalance_ratio > 3:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    check_name="labels",
                    message=f"Class imbalance detected (ratio={imbalance_ratio:.1f}:1)",
                    details={"class_distribution": class_distribution},
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    check_name="labels",
                    message=f"Balanced classes (ratio={imbalance_ratio:.1f}:1)",
                )
            )

        return issues, statistics

    def _check_distributions(
        self: DataValidator,
    ) -> tuple[list[ValidationIssue], dict[str, Any]]:
        """Check feature distributions.

        Returns:
            Tuple of (issues, statistics).
        """
        issues = []
        statistics: dict[str, Any] = {}

        feature_means = np.nanmean(self.features, axis=0)
        feature_stds = np.nanstd(self.features, axis=0)
        feature_mins = np.nanmin(self.features, axis=0)
        feature_maxs = np.nanmax(self.features, axis=0)

        statistics["feature_mean_range"] = (
            float(feature_means.min()),
            float(feature_means.max()),
        )
        statistics["feature_std_range"] = (
            float(feature_stds.min()),
            float(feature_stds.max()),
        )

        zero_variance_mask = feature_stds < 1e-6
        n_zero_variance = zero_variance_mask.sum()

        statistics["n_zero_variance_features"] = int(n_zero_variance)

        if n_zero_variance > 0:
            zero_variance_indices = np.where(zero_variance_mask)[0]
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    check_name="distributions",
                    message=f"Found {n_zero_variance} zero-variance features",
                    details={
                        "zero_variance_features": [
                            self.feature_names[i] for i in zero_variance_indices
                        ]
                    },
                )
            )

        constant_mask = feature_maxs == feature_mins
        n_constant = constant_mask.sum()

        statistics["n_constant_features"] = int(n_constant)

        if n_constant > 0:
            constant_indices = np.where(constant_mask)[0]
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    check_name="distributions",
                    message=f"Found {n_constant} constant features",
                    details={
                        "constant_features": [
                            self.feature_names[i] for i in constant_indices
                        ]
                    },
                )
            )

        if n_zero_variance == 0 and n_constant == 0:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    check_name="distributions",
                    message="All features have non-zero variance",
                )
            )

        return issues, statistics

    def _check_drift(
        self: DataValidator,
        drift_threshold: float,
    ) -> tuple[list[ValidationIssue], dict[str, Any]]:
        """Check for data drift compared to reference.

        Args:
            drift_threshold: Maximum drift allowed.

        Returns:
            Tuple of (issues, statistics).
        """
        issues = []
        statistics: dict[str, Any] = {}

        if self.reference_features is None:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    check_name="drift",
                    message="No reference features provided for drift detection",
                )
            )
            return issues, statistics

        ref_means = np.nanmean(self.reference_features, axis=0)
        ref_stds = np.nanstd(self.reference_features, axis=0)

        current_means = np.nanmean(self.features, axis=0)

        ref_stds[ref_stds == 0] = 1.0

        mean_shifts = np.abs(current_means - ref_means) / ref_stds
        drift_scores = mean_shifts

        overall_drift = float(drift_scores.mean())

        statistics["overall_drift"] = overall_drift
        statistics["max_drift"] = float(drift_scores.max())
        statistics["drift_threshold"] = float(drift_threshold)

        if overall_drift > drift_threshold:
            top_drift_features = np.argsort(drift_scores)[-5:][::-1]

            severity = (
                ValidationSeverity.WARNING
                if overall_drift < drift_threshold * 2
                else ValidationSeverity.ERROR
            )
            issues.append(
                ValidationIssue(
                    severity=severity,
                    check_name="drift",
                    message=f"Data drift detected (drift={overall_drift:.3f})",
                    details={
                        "top_drift_features": [
                            (self.feature_names[i], float(drift_scores[i]))
                            for i in top_drift_features
                        ]
                    },
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    check_name="drift",
                    message=f"No significant drift detected (drift={overall_drift:.3f})",
                )
            )

        return issues, statistics
