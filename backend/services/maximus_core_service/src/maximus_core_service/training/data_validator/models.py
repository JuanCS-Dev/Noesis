"""Data Validator Models.

Data models for validation results and issues.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationSeverity(Enum):
    """Validation issue severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """Represents a validation issue.

    Attributes:
        severity: Issue severity level.
        check_name: Name of the check that found the issue.
        message: Issue description.
        details: Additional details.
    """

    severity: ValidationSeverity
    check_name: str
    message: str
    details: dict[str, Any] | None = None

    def __repr__(self) -> str:
        """String representation."""
        return f"[{self.severity.value.upper()}] {self.check_name}: {self.message}"


@dataclass
class ValidationResult:
    """Result of data validation.

    Attributes:
        passed: Whether validation passed.
        issues: List of validation issues.
        statistics: Validation statistics.
    """

    passed: bool
    issues: list[ValidationIssue]
    statistics: dict[str, Any]

    def __repr__(self) -> str:
        """String representation."""
        n_errors = sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        )
        n_warnings = sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING
        )
        n_info = sum(
            1 for issue in self.issues if issue.severity == ValidationSeverity.INFO
        )

        return (
            f"ValidationResult(passed={self.passed}, errors={n_errors}, "
            f"warnings={n_warnings}, info={n_info})"
        )

    def print_report(self) -> None:
        """Print validation report."""
        print("\n" + "=" * 80)
        print("DATA VALIDATION REPORT")
        print("=" * 80)

        status = "PASSED" if self.passed else "FAILED"
        print(f"\nStatus: {status}")

        for severity in [
            ValidationSeverity.ERROR,
            ValidationSeverity.WARNING,
            ValidationSeverity.INFO,
        ]:
            severity_issues = [
                issue for issue in self.issues if issue.severity == severity
            ]

            if severity_issues:
                print(f"\n{severity.value.upper()}: {len(severity_issues)}")
                for issue in severity_issues:
                    print(f"  - {issue.check_name}: {issue.message}")

        print("\nSTATISTICS:")
        for key, value in self.statistics.items():
            print(f"  {key}: {value}")

        print("=" * 80)
