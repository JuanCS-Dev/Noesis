"""
MAXIMUS 2.0 - DIKĒ (The Justice Judge)
=======================================

Evaluates role adherence and authorization using:
1. Role Authorization Matrix - Dynamic capability checking
2. Constitutional Compliance - Validates against CODE_CONSTITUTION
3. Scope Validation - Ensures actions within authorized boundaries
4. Fairness Assessment - Checks for bias/discrimination

Based on:
- AI Governance research (2024-2025)
- Role-Based Access Control (RBAC) patterns
- Constitutional AI principles
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from ...models.reflection import ExecutionLog
from .base import Evidence, JudgePlugin, JudgeVerdict, VerdictType
from .roles import (
    ACTION_KEYWORDS,
    CONSTITUTIONAL_VIOLATIONS,
    DEFAULT_ROLE_MATRIX,
    RoleCapability,
    VIOLATION_KEYWORDS,
)


class DikeJudge(JudgePlugin):
    """
    DIKĒ - The Justice Judge.

    Implements role-based authorization and constitutional compliance.
    Named after the Greek goddess of justice and moral order.

    Evaluation Criteria:
    1. Is the action within the agent's authorized role?
    2. Does the action violate any constitutional principles?
    3. Is the action scope appropriate for the agent's authority?
    4. Are there any fairness/bias concerns?
    """

    def __init__(
        self,
        constitutional_validator: Optional[Any] = None,
        custom_roles: Optional[Dict[str, RoleCapability]] = None,
    ):
        """
        Initialize DIKĒ.

        Args:
            constitutional_validator: Optional external validator
            custom_roles: Additional role definitions to merge
        """
        self._constitutional_validator = constitutional_validator
        self._role_matrix = {**DEFAULT_ROLE_MATRIX}
        if custom_roles:
            self._role_matrix.update(custom_roles)

    @property
    def name(self) -> str:
        """Judge identifier."""
        return "DIKĒ"

    @property
    def pillar(self) -> str:
        """Philosophical pillar."""
        return "Justice"

    @property
    def weight(self) -> float:
        """Weight in ensemble voting."""
        return 0.30

    @property
    def timeout_seconds(self) -> float:
        """Max evaluation time (fast - rule-based)."""
        return 3.0

    async def evaluate(
        self,
        execution_log: ExecutionLog,
        context: Optional[Dict[str, Any]] = None
    ) -> JudgeVerdict:
        """
        Evaluate justice/authorization of execution.

        Args:
            execution_log: The execution to evaluate
            context: Additional context

        Returns:
            JudgeVerdict with justice evaluation
        """
        start_time = time.time()

        try:
            evidence = await self.get_evidence(execution_log)
            role = self._extract_role(execution_log.agent_id)

            role_check = self._check_role_authorization(execution_log, role)
            const_check = await self._check_constitutional_compliance(execution_log)
            scope_check = self._check_scope_authorization(execution_log, role, context)
            fairness_check = self._check_fairness(execution_log)

            passed = all([
                role_check["passed"],
                const_check["passed"],
                scope_check["passed"],
                fairness_check["passed"],
            ])

            verdict_type, offense_level = self._determine_verdict_and_offense(
                role_check, const_check, scope_check, fairness_check
            )

            confidence = self._calculate_confidence(
                role_check, const_check, scope_check, fairness_check
            )

            reasoning = self._generate_reasoning(
                passed, role_check, const_check, scope_check, fairness_check
            )

            suggestions = self._generate_suggestions(
                role_check, const_check, scope_check, fairness_check
            )

            return JudgeVerdict(
                judge_name=self.name,
                pillar=self.pillar,
                verdict=verdict_type,
                passed=passed,
                confidence=confidence,
                reasoning=reasoning,
                evidence=evidence,
                suggestions=suggestions,
                execution_time_ms=(time.time() - start_time) * 1000,
                metadata={
                    "role": role,
                    "role_check": role_check,
                    "constitutional_check": const_check,
                    "scope_check": scope_check,
                    "fairness_check": fairness_check,
                    "offense_level": offense_level,
                }
            )

        except Exception as e:
            return JudgeVerdict.abstained(
                judge_name=self.name,
                pillar=self.pillar,
                reason=f"Evaluation error: {str(e)}",
            )

    async def get_evidence(self, execution_log: ExecutionLog) -> List[Evidence]:
        """Gather evidence for justice evaluation."""
        evidence = []
        action_lower = (execution_log.action or "").lower()
        agent_lower = execution_log.agent_id.lower()

        if "planner" in agent_lower:
            for verb in ["executed", "deployed", "deleted", "started", "stopped"]:
                if verb in action_lower:
                    evidence.append(Evidence(
                        source="role_violation",
                        content=f"Planner attempted execution: '{verb}'",
                        relevance=1.0,
                        verified=True,
                    ))

        if "executor" in agent_lower:
            for verb in ["planned", "designed", "analyzed strategy", "proposed"]:
                if verb in action_lower:
                    evidence.append(Evidence(
                        source="role_violation",
                        content=f"Executor attempted planning: '{verb}'",
                        relevance=1.0,
                        verified=True,
                    ))

        full_text = f"{execution_log.action} {execution_log.outcome}"
        for keyword, violation in VIOLATION_KEYWORDS.items():
            if keyword in full_text.lower():
                evidence.append(Evidence(
                    source="constitutional_violation",
                    content=f"Possible violation: {violation}",
                    relevance=1.0,
                    verified=True,
                ))

        return evidence

    def _extract_role(self, agent_id: str) -> str:
        """Extract role from agent_id."""
        agent_lower = agent_id.lower()
        for role in self._role_matrix:
            if role in agent_lower:
                return role
        return "unknown"

    def _check_role_authorization(
        self, log: ExecutionLog, role: str
    ) -> Dict[str, Any]:
        """Check if action is authorized for role."""
        if role not in self._role_matrix:
            return {"passed": False, "reason": f"Unknown role: {role}", "severity": "major"}

        capability = self._role_matrix[role]
        action_lower = (log.action or "").lower()

        for forbidden in capability.forbidden_actions:
            if forbidden in action_lower:
                return {
                    "passed": False,
                    "reason": f"Role '{role}' cannot perform '{forbidden}'",
                    "severity": "major",
                    "forbidden_action": forbidden,
                }

        action_type = self._classify_action(action_lower)
        if action_type and action_type not in capability.allowed_actions:
            return {
                "passed": True,
                "reason": f"Action '{action_type}' not explicitly allowed",
                "severity": "minor",
                "warning": True,
            }

        for approval_required in capability.requires_approval:
            if approval_required in action_lower:
                return {
                    "passed": False,
                    "reason": f"Requires approval: {approval_required}",
                    "severity": "minor",
                    "requires_approval": approval_required,
                }

        return {"passed": True, "reason": "Within role authorization", "severity": "none"}

    async def _check_constitutional_compliance(
        self, log: ExecutionLog
    ) -> Dict[str, Any]:
        """Check for constitutional violations."""
        full_text = f"{log.action} {log.outcome} {log.reasoning_trace or ''}".lower()
        violations = []

        for violation in CONSTITUTIONAL_VIOLATIONS:
            if violation in full_text:
                violations.append(violation)

        for keyword, violation in VIOLATION_KEYWORDS.items():
            if keyword in full_text and violation not in violations:
                violations.append(violation)

        if violations:
            return {
                "passed": False,
                "reason": f"Constitutional violations: {', '.join(violations)}",
                "severity": "capital",
                "violations": violations,
            }

        return {"passed": True, "reason": "No violations detected", "severity": "none"}

    def _check_scope_authorization(
        self, log: ExecutionLog, role: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check if action scope is within authorization."""
        if role not in self._role_matrix:
            return {"passed": True, "reason": "Cannot verify unknown role", "severity": "none"}

        capability = self._role_matrix[role]
        action_scope = self._extract_scope(log, context)
        scope_hierarchy = {"own": 1, "team": 2, "global": 3}

        if scope_hierarchy.get(action_scope, 0) > scope_hierarchy.get(capability.max_scope, 3):
            return {
                "passed": False,
                "reason": f"Scope '{action_scope}' exceeds max '{capability.max_scope}'",
                "severity": "major",
            }

        return {"passed": True, "reason": f"Scope '{action_scope}' authorized", "severity": "none"}

    def _check_fairness(self, log: ExecutionLog) -> Dict[str, Any]:
        """Check for bias/fairness issues."""
        bias_keywords = ["discriminate", "exclude", "bias", "unfair", "prejudice"]
        full_text = f"{log.action} {log.outcome}".lower()

        for keyword in bias_keywords:
            if keyword in full_text:
                return {
                    "passed": True,
                    "reason": f"Potential concern: '{keyword}'",
                    "severity": "none",
                    "warning": True,
                }

        return {"passed": True, "reason": "No fairness issues", "severity": "none"}

    def _classify_action(self, action_text: str) -> Optional[str]:
        """Classify action into a category."""
        for category, keywords in ACTION_KEYWORDS.items():
            if any(kw in action_text for kw in keywords):
                return category
        return None

    def _extract_scope(
        self, log: ExecutionLog, context: Optional[Dict[str, Any]]
    ) -> str:
        """Extract scope of action."""
        action_lower = (log.action or "").lower()

        if any(w in action_lower for w in ["global", "all", "cluster", "system"]):
            return "global"
        if any(w in action_lower for w in ["team", "namespace", "group"]):
            return "team"
        return "own"

    def _determine_verdict_and_offense(
        self,
        role_check: Dict[str, Any],
        const_check: Dict[str, Any],
        scope_check: Dict[str, Any],
        fairness_check: Dict[str, Any],
    ) -> tuple[VerdictType, str]:
        """Determine verdict type and offense level."""
        if const_check.get("severity") == "capital":
            return VerdictType.FAIL, "capital"
        if role_check.get("severity") == "major":
            return VerdictType.FAIL, "major"
        if scope_check.get("severity") == "major":
            return VerdictType.FAIL, "major"
        if role_check.get("severity") == "minor":
            return VerdictType.REVIEW, "minor"

        if all([role_check["passed"], const_check["passed"],
                scope_check["passed"], fairness_check["passed"]]):
            return VerdictType.PASS, "none"

        return VerdictType.REVIEW, "none"

    def _calculate_confidence(self, *checks: Dict[str, Any]) -> float:
        """Calculate confidence based on check results."""
        passed_count = sum(1 for c in checks if c["passed"])
        return 0.6 + (passed_count / len(checks)) * 0.4

    def _generate_reasoning(
        self,
        passed: bool,
        role_check: Dict[str, Any],
        const_check: Dict[str, Any],
        scope_check: Dict[str, Any],
        fairness_check: Dict[str, Any],
    ) -> str:
        """Generate reasoning from all checks."""
        if passed:
            return "All justice checks passed. Action within authorization."

        failures = []
        if not role_check["passed"]:
            failures.append(f"Role: {role_check['reason']}")
        if not const_check["passed"]:
            failures.append(f"Constitution: {const_check['reason']}")
        if not scope_check["passed"]:
            failures.append(f"Scope: {scope_check['reason']}")
        if not fairness_check["passed"]:
            failures.append(f"Fairness: {fairness_check['reason']}")

        return f"Justice check failed: {'; '.join(failures)}"

    def _generate_suggestions(self, *checks: Dict[str, Any]) -> List[str]:
        """Generate suggestions from failed checks."""
        suggestions = []
        for check in checks:
            if not check["passed"]:
                reason = check.get("reason", "")
                if "role" in reason.lower():
                    suggestions.append("Action should be performed by appropriate role.")
                elif "constitutional" in reason.lower():
                    suggestions.append("Review CODE_CONSTITUTION for violations.")
                elif "scope" in reason.lower():
                    suggestions.append("Reduce action scope to within authorization.")
        return suggestions

    async def health_check(self) -> Dict[str, Any]:
        """Check DIKĒ health."""
        return {
            "healthy": True,
            "name": self.name,
            "pillar": self.pillar,
            "weight": self.weight,
            "roles_defined": list(self._role_matrix.keys()),
            "violations_monitored": len(CONSTITUTIONAL_VIOLATIONS),
        }
