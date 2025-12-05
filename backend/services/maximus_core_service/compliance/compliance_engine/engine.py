"""Compliance Engine.

Core compliance checking engine for automated compliance validation.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..base import (
    ComplianceConfig,
    ComplianceResult,
    ComplianceStatus,
    ComplianceViolation,
    Control,
    ControlCategory,
    Evidence,
    RegulationType,
    ViolationSeverity,
)
from ..regulations import get_regulation
from .checkers import get_default_category_checkers
from .models import ComplianceCheckResult, ComplianceSnapshot
from .reports import generate_compliance_report

logger = logging.getLogger(__name__)

# Type alias for control checker functions
ControlChecker = Callable[[Control, ComplianceConfig], ComplianceResult]


class ComplianceEngine:
    """Core compliance checking engine.

    Orchestrates automated compliance checks across all supported regulations.
    Extensible through custom control checkers.

    Attributes:
        config: Compliance configuration.
    """

    def __init__(self, config: ComplianceConfig | None = None) -> None:
        """Initialize compliance engine.

        Args:
            config: Compliance configuration (uses default if None).
        """
        self.config = config or ComplianceConfig()
        self._control_checkers: dict[str, ControlChecker] = {}
        self._category_checkers: dict[ControlCategory, ControlChecker] = {}

        self._register_default_checkers()

        logger.info(
            "Compliance engine initialized with %d regulations",
            len(self.config.enabled_regulations),
        )

    def _register_default_checkers(self) -> None:
        """Register default automated checkers for control categories."""
        self._category_checkers = get_default_category_checkers()

    def register_control_checker(
        self,
        control_id: str,
        checker: ControlChecker,
    ) -> None:
        """Register custom checker for specific control.

        Args:
            control_id: Control ID to check.
            checker: Checker function.
        """
        self._control_checkers[control_id] = checker
        logger.info("Registered custom checker for control %s", control_id)

    def register_category_checker(
        self,
        category: ControlCategory,
        checker: ControlChecker,
    ) -> None:
        """Register custom checker for control category.

        Args:
            category: Control category.
            checker: Checker function.
        """
        self._category_checkers[category] = checker
        logger.info("Registered custom checker for category %s", category.value)

    def check_control(
        self,
        control: Control,
        evidence: list[Evidence] | None = None,
    ) -> ComplianceResult:
        """Check compliance for a specific control.

        Args:
            control: Control to check.
            evidence: Optional list of evidence for this control.

        Returns:
            Compliance check result.
        """
        logger.debug("Checking control %s", control.control_id)

        if control.control_id in self._control_checkers:
            result = self._control_checkers[control.control_id](control, self.config)
        elif control.category in self._category_checkers:
            result = self._category_checkers[control.category](control, self.config)
        else:
            result = ComplianceResult(
                control_id=control.control_id,
                regulation_type=control.regulation_type,
                status=ComplianceStatus.PENDING_REVIEW,
                checked_by="compliance_engine",
                automated=False,
                notes="No automated checker available - manual review required",
            )

        if evidence:
            result.evidence.extend(evidence)
            result = self._evaluate_evidence(result, control, evidence)

        return result

    def _evaluate_evidence(
        self,
        result: ComplianceResult,
        control: Control,
        evidence: list[Evidence],
    ) -> ComplianceResult:
        """Evaluate evidence and update result status.

        Args:
            result: Current compliance result.
            control: Control being checked.
            evidence: Provided evidence.

        Returns:
            Updated compliance result.
        """
        if result.status != ComplianceStatus.EVIDENCE_REQUIRED:
            return result

        required_types = set(control.evidence_required)
        provided_types = set(e.evidence_type for e in evidence)

        if required_types.issubset(provided_types):
            expired = [e for e in evidence if e.is_expired()]
            if expired:
                result.status = ComplianceStatus.PARTIALLY_COMPLIANT
                result.notes = f"Some evidence has expired: {len(expired)} items"
            else:
                result.status = ComplianceStatus.COMPLIANT
                result.score = 1.0
                result.notes = "All required evidence provided and verified"
        else:
            missing = required_types - provided_types
            result.status = ComplianceStatus.PARTIALLY_COMPLIANT
            result.score = 0.5
            result.notes = f"Missing evidence types: {[t.value for t in missing]}"

        return result

    def check_compliance(
        self,
        regulation_type: RegulationType,
        evidence_by_control: dict[str, list[Evidence]] | None = None,
    ) -> ComplianceCheckResult:
        """Check compliance for a specific regulation.

        Args:
            regulation_type: Type of regulation to check.
            evidence_by_control: Optional dict mapping control_id -> evidence list.

        Returns:
            Compliance check result for regulation.
        """
        logger.info("Checking compliance for %s", regulation_type.value)

        if not self.config.is_regulation_enabled(regulation_type):
            logger.warning("Regulation %s is not enabled", regulation_type.value)
            return self._empty_check_result(regulation_type)

        regulation = get_regulation(regulation_type)
        evidence_by_control = evidence_by_control or {}

        results: list[ComplianceResult] = []
        violations: list[ComplianceViolation] = []

        for control in regulation.controls:
            control_evidence = evidence_by_control.get(control.control_id, [])
            result = self.check_control(control, control_evidence)
            results.append(result)

            if result.status == ComplianceStatus.NON_COMPLIANT:
                violations.append(self._create_violation(control, result, regulation_type))

        check_result = self._build_check_result(
            regulation_type, regulation, results, violations
        )

        logger.info(
            "Compliance check complete for %s: %.1f%% compliant, %d violations",
            regulation_type.value,
            check_result.compliance_percentage,
            len(violations),
        )

        return check_result

    def _empty_check_result(self, regulation_type: RegulationType) -> ComplianceCheckResult:
        """Create empty check result for disabled regulation.

        Args:
            regulation_type: Regulation type.

        Returns:
            Empty compliance check result.
        """
        return ComplianceCheckResult(
            regulation_type=regulation_type,
            checked_at=datetime.utcnow(),
            total_controls=0,
            controls_checked=0,
            compliant=0,
            non_compliant=0,
            partially_compliant=0,
            not_applicable=0,
            pending_review=0,
            evidence_required=0,
        )

    def _create_violation(
        self,
        control: Control,
        result: ComplianceResult,
        regulation_type: RegulationType,
    ) -> ComplianceViolation:
        """Create violation from non-compliant result.

        Args:
            control: Control that was violated.
            result: Compliance result.
            regulation_type: Regulation type.

        Returns:
            Compliance violation.
        """
        return ComplianceViolation(
            control_id=control.control_id,
            regulation_type=regulation_type,
            severity=self._determine_violation_severity(control),
            title=f"Non-compliance with {control.title}",
            description=f"Control {control.control_id} is not compliant. {result.notes or ''}",
            detected_by="compliance_engine",
        )

    def _build_check_result(
        self,
        regulation_type: RegulationType,
        regulation: Any,
        results: list[ComplianceResult],
        violations: list[ComplianceViolation],
    ) -> ComplianceCheckResult:
        """Build check result from results and violations.

        Args:
            regulation_type: Regulation type.
            regulation: Regulation definition.
            results: List of compliance results.
            violations: List of violations.

        Returns:
            Compliance check result.
        """
        status_counts = {
            ComplianceStatus.COMPLIANT: 0,
            ComplianceStatus.NON_COMPLIANT: 0,
            ComplianceStatus.PARTIALLY_COMPLIANT: 0,
            ComplianceStatus.NOT_APPLICABLE: 0,
            ComplianceStatus.PENDING_REVIEW: 0,
            ComplianceStatus.EVIDENCE_REQUIRED: 0,
        }

        for result in results:
            if result.status in status_counts:
                status_counts[result.status] += 1

        return ComplianceCheckResult(
            regulation_type=regulation_type,
            checked_at=datetime.utcnow(),
            total_controls=len(regulation.controls),
            controls_checked=len(results),
            compliant=status_counts[ComplianceStatus.COMPLIANT],
            non_compliant=status_counts[ComplianceStatus.NON_COMPLIANT],
            partially_compliant=status_counts[ComplianceStatus.PARTIALLY_COMPLIANT],
            not_applicable=status_counts[ComplianceStatus.NOT_APPLICABLE],
            pending_review=status_counts[ComplianceStatus.PENDING_REVIEW],
            evidence_required=status_counts[ComplianceStatus.EVIDENCE_REQUIRED],
            results=results,
            violations=violations,
        )

    def run_all_checks(
        self,
        evidence_by_regulation: dict[RegulationType, dict[str, list[Evidence]]] | None = None,
    ) -> ComplianceSnapshot:
        """Run compliance checks for all enabled regulations.

        Args:
            evidence_by_regulation: Optional nested dict: regulation_type -> control_id -> evidence.

        Returns:
            Compliance snapshot with all results.
        """
        logger.info(
            "Running compliance checks for %d regulations",
            len(self.config.enabled_regulations),
        )

        evidence_by_regulation = evidence_by_regulation or {}
        results: dict[RegulationType, ComplianceCheckResult] = {}

        for regulation_type in self.config.enabled_regulations:
            regulation_evidence = evidence_by_regulation.get(regulation_type, {})
            result = self.check_compliance(regulation_type, regulation_evidence)
            results[regulation_type] = result

        snapshot = ComplianceSnapshot(regulation_results=results)

        logger.info(
            "All compliance checks complete: %.1f%% overall, %d total violations",
            snapshot.overall_compliance_percentage,
            snapshot.total_violations,
        )

        return snapshot

    def get_compliance_status(
        self,
        regulation_type: RegulationType | None = None,
    ) -> dict[str, Any]:
        """Get current compliance status summary.

        Args:
            regulation_type: Optional specific regulation (all if None).

        Returns:
            Compliance status dict.
        """
        if regulation_type:
            result = self.check_compliance(regulation_type)
            return {
                "regulation": regulation_type.value,
                "compliance_percentage": result.compliance_percentage,
                "score": result.score,
                "total_controls": result.total_controls,
                "compliant": result.compliant,
                "non_compliant": result.non_compliant,
                "violations": len(result.violations),
                "critical_violations": len(result.get_critical_violations()),
                "certification_ready": result.is_certification_ready(),
            }

        snapshot = self.run_all_checks()
        return {
            "overall_compliance_percentage": snapshot.overall_compliance_percentage,
            "overall_score": snapshot.overall_score,
            "total_violations": snapshot.total_violations,
            "critical_violations": snapshot.critical_violations,
            "regulations": {
                reg_type.value: {
                    "compliance_percentage": result.compliance_percentage,
                    "score": result.score,
                    "violations": len(result.violations),
                }
                for reg_type, result in snapshot.regulation_results.items()
            },
        }

    def create_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        regulation_types: list[RegulationType] | None = None,
    ) -> dict[str, Any]:
        """Generate compliance report for time period.

        Args:
            start_date: Report start date.
            end_date: Report end date.
            regulation_types: Optional list of regulations (all enabled if None).

        Returns:
            Compliance report dict.
        """
        snapshot = self.run_all_checks()
        return generate_compliance_report(
            snapshot=snapshot,
            start_date=start_date,
            end_date=end_date,
            regulation_types=regulation_types,
            enabled_regulations=self.config.enabled_regulations,
        )

    def _determine_violation_severity(self, control: Control) -> ViolationSeverity:
        """Determine severity of violation based on control characteristics.

        Args:
            control: Control that was violated.

        Returns:
            Violation severity.
        """
        if not control.mandatory:
            return ViolationSeverity.LOW

        if control.category in [ControlCategory.SECURITY, ControlCategory.PRIVACY]:
            return ViolationSeverity.HIGH

        if control.category in [ControlCategory.GOVERNANCE, ControlCategory.TECHNICAL]:
            return ViolationSeverity.MEDIUM

        return ViolationSeverity.LOW
