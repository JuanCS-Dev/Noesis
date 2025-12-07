"""
Phase 6: Compliance Check.

Checks compliance with regulations (GDPR, SOC2, etc).
Target: <100ms

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from maximus_core_service.compliance import ComplianceEngine, RegulationType

from .models import ComplianceCheckResult

if TYPE_CHECKING:
    pass


async def compliance_check(
    compliance_engine: ComplianceEngine,
    action: str,
    context: dict[str, Any],
) -> ComplianceCheckResult:
    """
    Phase 6: Check compliance with regulations.

    Target: <100ms

    Args:
        compliance_engine: ComplianceEngine instance
        action: Action being validated
        context: Action context

    Returns:
        ComplianceCheckResult with regulation compliance status
    """
    start_time = time.time()

    regulations_to_check = [
        RegulationType.GDPR,
        RegulationType.SOC2_TYPE_II,
    ]

    compliance_results = {}
    overall_compliant = True

    for regulation in regulations_to_check:
        try:
            result = compliance_engine.check_compliance(
                regulation=regulation, scope=action
            )

            compliance_results[regulation.value] = {
                "is_compliant": result.is_compliant,
                "compliance_percentage": result.compliance_percentage,
                "controls_checked": result.total_controls,
                "controls_passed": result.passed_controls,
            }

            if not result.is_compliant:
                overall_compliant = False

        except Exception as e:
            compliance_results[regulation.value] = {
                "error": str(e),
                "is_compliant": False,
            }
            overall_compliant = False

    duration_ms = (time.time() - start_time) * 1000

    return ComplianceCheckResult(
        regulations_checked=regulations_to_check,
        compliance_results=compliance_results,
        overall_compliant=overall_compliant,
        duration_ms=duration_ms,
    )
