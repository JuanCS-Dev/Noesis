"""Article V Guardian Checkers.

Violation checking functions for Article V Guardian.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import ConstitutionalArticle, ConstitutionalViolation, GuardianPriority
from .config import (
    AUTONOMOUS_INDICATORS,
    CRITICAL_ACTIONS,
    CRITICAL_HITL_PATTERNS,
    GOVERNANCE_INDICATORS,
    HITL_INDICATORS,
    KILLSWITCH_PATTERNS,
    POWERFUL_OPERATIONS,
    PROCESS_PATTERNS,
    RESPONSIBILITY_REQUIREMENTS,
    TWOMAN_PATTERNS,
)


async def check_autonomous_governance(
    autonomous_paths: list[str],
    autonomous_systems: dict[str, dict[str, Any]],
) -> list[ConstitutionalViolation]:
    """Check if autonomous systems have proper governance.

    Args:
        autonomous_paths: Paths to check for autonomous systems
        autonomous_systems: Registry to track found systems

    Returns:
        List of violations found
    """
    violations = []

    for base_path in autonomous_paths:
        if not Path(base_path).exists():
            continue

        autonomous_files = []
        governance_files = []

        for py_file in Path(base_path).rglob("*.py"):
            try:
                content = py_file.read_text().lower()

                if any(indicator in content for indicator in AUTONOMOUS_INDICATORS):
                    autonomous_files.append(py_file)

                    system_id = f"{py_file.parent.name}_{py_file.stem}"
                    autonomous_systems[system_id] = {
                        "path": str(py_file),
                        "detected": datetime.utcnow().isoformat(),
                        "has_governance": False,
                    }

                if any(indicator in content for indicator in GOVERNANCE_INDICATORS):
                    governance_files.append(py_file)

            except Exception:
                pass

        for auto_file in autonomous_files:
            has_governance = False
            auto_module = auto_file.parent

            for gov_file in governance_files:
                if (
                    gov_file.parent == auto_module
                    or gov_file.parent == auto_module.parent
                ):
                    has_governance = True
                    break

            if not has_governance:
                violations.append(
                    ConstitutionalViolation(
                        article=ConstitutionalArticle.ARTICLE_V,
                        clause="Section 1",
                        rule="Governance must precede autonomous systems",
                        description=f"Autonomous capability without governance in {auto_file.name}",
                        severity=GuardianPriority.CRITICAL,
                        evidence=[f"Autonomous system at: {auto_file}"],
                        affected_systems=[auto_file.parent.name],
                        recommended_action="Implement governance before enabling autonomy",
                        context={
                            "file": str(auto_file),
                            "module": str(auto_module),
                        },
                    )
                )

    return violations


async def check_responsibility_doctrine(
    powerful_paths: list[str],
) -> list[ConstitutionalViolation]:
    """Check implementation of Responsibility Doctrine (Anexo C).

    Args:
        powerful_paths: Paths to check for powerful operations

    Returns:
        List of violations found
    """
    violations = []

    for base_path in powerful_paths:
        if not Path(base_path).exists():
            continue

        for py_file in Path(base_path).rglob("*.py"):
            if "test" in py_file.name:
                continue

            try:
                content = py_file.read_text()
                has_powerful = any(op in content.lower() for op in POWERFUL_OPERATIONS)

                if has_powerful:
                    missing_requirements = [
                        req
                        for req in RESPONSIBILITY_REQUIREMENTS
                        if req not in content.lower()
                    ]

                    if len(missing_requirements) > 2:
                        violations.append(
                            ConstitutionalViolation(
                                article=ConstitutionalArticle.ARTICLE_V,
                                clause="Section 2",
                                rule="Responsibility Doctrine must be applied",
                                description=f"Missing responsibility controls in {py_file.name}",
                                severity=GuardianPriority.HIGH,
                                evidence=[
                                    f"Missing: {', '.join(missing_requirements[:3])}",
                                    f"Total missing: {len(missing_requirements)} out of {len(RESPONSIBILITY_REQUIREMENTS)}",
                                ],
                                affected_systems=[py_file.parent.name],
                                recommended_action="Implement compartmentalization, Two-Man Rule, and kill switches",
                                context={
                                    "file": str(py_file),
                                    "missing": missing_requirements,
                                },
                            )
                        )

            except Exception:
                pass

    return violations


async def check_hitl_controls(
    hitl_paths: list[str],
) -> list[ConstitutionalViolation]:
    """Check for Human-In-The-Loop controls on critical operations.

    Args:
        hitl_paths: Paths to check for HITL controls

    Returns:
        List of violations found
    """
    violations = []

    for base_path in hitl_paths:
        if not Path(base_path).exists():
            continue

        for py_file in Path(base_path).rglob("*.py"):
            if "test" in py_file.name:
                continue

            try:
                content = py_file.read_text()
                lines = content.splitlines()

                for i, line in enumerate(lines, 1):
                    for pattern in CRITICAL_HITL_PATTERNS:
                        if re.search(pattern, line.lower()):
                            context_start = max(0, i - 10)
                            context_end = min(len(lines), i + 10)
                            context = "\n".join(lines[context_start:context_end]).lower()

                            has_hitl = any(hitl in context for hitl in HITL_INDICATORS)

                            if not has_hitl:
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_V,
                                        clause="Section 2",
                                        rule="Critical operations require HITL",
                                        description=f"Critical operation without HITL in {py_file.name}:{i}",
                                        severity=GuardianPriority.HIGH,
                                        evidence=[f"{py_file}:{i}: {line.strip()}"],
                                        affected_systems=["hitl_controls"],
                                        recommended_action="Add human approval requirement",
                                        context={
                                            "file": str(py_file),
                                            "line": i,
                                            "operation": pattern,
                                        },
                                    )
                                )

            except Exception:
                pass

    return violations


async def check_kill_switches(
    process_paths: list[str],
) -> list[ConstitutionalViolation]:
    """Check for kill switch implementation in autonomous systems.

    Args:
        process_paths: Paths to check for long-running processes

    Returns:
        List of violations found
    """
    violations = []

    for base_path in process_paths:
        if not Path(base_path).exists():
            continue

        for py_file in Path(base_path).rglob("*.py"):
            if "test" in py_file.name:
                continue

            try:
                content = py_file.read_text()

                has_process = any(
                    re.search(pattern, content) for pattern in PROCESS_PATTERNS
                )

                if has_process:
                    has_killswitch = any(
                        ks in content.lower() for ks in KILLSWITCH_PATTERNS
                    )

                    if not has_killswitch:
                        violations.append(
                            ConstitutionalViolation(
                                article=ConstitutionalArticle.ARTICLE_V,
                                clause="Anexo C",
                                rule="Kill switches required for autonomous systems",
                                description=f"Autonomous process without kill switch in {py_file.name}",
                                severity=GuardianPriority.CRITICAL,
                                evidence=[
                                    "Long-running process detected without emergency stop"
                                ],
                                affected_systems=[py_file.parent.name],
                                recommended_action="Implement emergency shutdown capability",
                                context={"file": str(py_file)},
                            )
                        )

            except Exception:
                pass

    return violations


async def check_two_man_rule(
    governance_paths: list[str],
) -> list[ConstitutionalViolation]:
    """Check implementation of Two-Man Rule for critical actions.

    Args:
        governance_paths: Paths to check for Two-Man Rule

    Returns:
        List of violations found
    """
    violations = []

    for base_path in governance_paths:
        if not Path(base_path).exists():
            continue

        for py_file in Path(base_path).rglob("*.py"):
            try:
                content = py_file.read_text()
                lines = content.splitlines()

                for i, line in enumerate(lines, 1):
                    for action in CRITICAL_ACTIONS:
                        if re.search(action, line.lower()):
                            context_start = max(0, i - 15)
                            context_end = min(len(lines), i + 15)
                            context = "\n".join(lines[context_start:context_end]).lower()

                            has_twoman = any(tm in context for tm in TWOMAN_PATTERNS)

                            if not has_twoman:
                                violations.append(
                                    ConstitutionalViolation(
                                        article=ConstitutionalArticle.ARTICLE_V,
                                        clause="Anexo C",
                                        rule="Two-Man Rule for critical actions",
                                        description=f"Critical action without dual approval in {py_file.name}:{i}",
                                        severity=GuardianPriority.HIGH,
                                        evidence=[f"{py_file}:{i}: {line.strip()}"],
                                        affected_systems=["authorization_system"],
                                        recommended_action="Implement dual approval mechanism",
                                        context={
                                            "file": str(py_file),
                                            "line": i,
                                            "action": action,
                                        },
                                    )
                                )

            except Exception:
                pass

    return violations
