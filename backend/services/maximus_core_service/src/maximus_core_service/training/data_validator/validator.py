"""Data Validator.

Main validator for data quality checks.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from .checks import CheckMixin
from .models import ValidationIssue, ValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


class DataValidator(CheckMixin):
    """Validates data quality for training.

    Performs comprehensive checks:
    - Missing values
    - Outliers
    - Label distribution
    - Feature statistics
    - Data drift

    Example:
        ```python
        validator = DataValidator(
            features=features,
            labels=labels,
            reference_features=None,
        )

        result = validator.validate(
            check_missing=True,
            check_outliers=True,
            check_labels=True,
            check_drift=False
        )

        result.print_report()
        ```

    Attributes:
        features: Feature matrix (N x D).
        labels: Label vector (N,).
        reference_features: Reference features for drift detection.
        feature_names: Feature names for reporting.
        n_samples: Number of samples.
        n_features: Number of features.
    """

    def __init__(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        reference_features: np.ndarray | None = None,
        feature_names: list[str] | None = None,
    ) -> None:
        """Initialize data validator.

        Args:
            features: Feature matrix (N x D).
            labels: Label vector (N,).
            reference_features: Reference features for drift detection.
            feature_names: Optional feature names for reporting.
        """
        self.features = features
        self.labels = labels
        self.reference_features = reference_features
        self.feature_names = feature_names or [
            f"feature_{i}" for i in range(features.shape[1])
        ]

        self.n_samples, self.n_features = features.shape

        logger.info(
            "DataValidator initialized: %d samples, %d features",
            self.n_samples,
            self.n_features,
        )

    def validate(
        self,
        check_missing: bool = True,
        check_outliers: bool = True,
        check_labels: bool = True,
        check_distributions: bool = True,
        check_drift: bool = False,
        outlier_threshold: float = 3.0,
        missing_threshold: float = 0.1,
        drift_threshold: float = 0.1,
    ) -> ValidationResult:
        """Run all validation checks.

        Args:
            check_missing: Check for missing values.
            check_outliers: Check for outliers.
            check_labels: Check label distribution.
            check_distributions: Check feature distributions.
            check_drift: Check for data drift.
            outlier_threshold: Z-score threshold for outliers.
            missing_threshold: Maximum fraction of missing values allowed.
            drift_threshold: Maximum drift allowed.

        Returns:
            Validation result with issues and statistics.
        """
        issues: list[ValidationIssue] = []
        statistics: dict = {}

        if check_missing:
            missing_issues, missing_stats = self._check_missing_values(missing_threshold)
            issues.extend(missing_issues)
            statistics.update(missing_stats)

        if check_outliers:
            outlier_issues, outlier_stats = self._check_outliers(outlier_threshold)
            issues.extend(outlier_issues)
            statistics.update(outlier_stats)

        if check_labels:
            label_issues, label_stats = self._check_labels()
            issues.extend(label_issues)
            statistics.update(label_stats)

        if check_distributions:
            dist_issues, dist_stats = self._check_distributions()
            issues.extend(dist_issues)
            statistics.update(dist_stats)

        if check_drift and self.reference_features is not None:
            drift_issues, drift_stats = self._check_drift(drift_threshold)
            issues.extend(drift_issues)
            statistics.update(drift_stats)

        has_errors = any(
            issue.severity == ValidationSeverity.ERROR for issue in issues
        )
        passed = not has_errors

        result = ValidationResult(passed=passed, issues=issues, statistics=statistics)

        logger.info("Validation complete: %s", result)

        return result

    def save_report(self, result: ValidationResult, output_path: Path) -> None:
        """Save validation report to file.

        Args:
            result: Validation result.
            output_path: Path to save report.
        """
        with open(output_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("DATA VALIDATION REPORT\n")
            f.write("=" * 80 + "\n\n")

            status = "PASSED" if result.passed else "FAILED"
            f.write(f"Status: {status}\n\n")

            for severity in [
                ValidationSeverity.ERROR,
                ValidationSeverity.WARNING,
                ValidationSeverity.INFO,
            ]:
                severity_issues = [
                    issue for issue in result.issues if issue.severity == severity
                ]

                if severity_issues:
                    f.write(f"\n{severity.value.upper()}: {len(severity_issues)}\n")
                    for issue in severity_issues:
                        f.write(f"  - {issue.check_name}: {issue.message}\n")
                        if issue.details:
                            for key, value in issue.details.items():
                                f.write(f"      {key}: {value}\n")

            f.write("\n\nSTATISTICS:\n")
            for key, value in result.statistics.items():
                f.write(f"  {key}: {value}\n")

            f.write("\n" + "=" * 80 + "\n")

        logger.info("Validation report saved to %s", output_path)
