"""
NIST AI RMF 1.0 - AI Risk Management Framework.

Framework for managing risks from AI systems with four core functions.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

from datetime import datetime

from ..base import (
    Control,
    ControlCategory,
    EvidenceType,
    Regulation,
    RegulationType,
)

NIST_AI_RMF = Regulation(
    regulation_type=RegulationType.NIST_AI_RMF,
    name="NIST AI Risk Management Framework 1.0",
    version="1.0",
    effective_date=datetime(2023, 1, 26),
    jurisdiction="United States (voluntary)",
    description=(
        "Framework for managing risks to individuals, organizations and society "
        "from AI systems. Four core functions: GOVERN, MAP, MEASURE, MANAGE."
    ),
    authority="National Institute of Standards and Technology (NIST)",
    url="https://www.nist.gov/itl/ai-risk-management-framework",
    penalties="N/A - Voluntary framework",
    scope="All AI systems",
    controls=[
        Control(
            control_id="NIST-GOVERN-1.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.GOVERNANCE,
            title="AI Risk Management Strategy",
            description=(
                "Legal and regulatory requirements involving AI are understood, "
                "managed, and documented. Organizational policies and practices "
                "for AI system development and deployment."
            ),
            mandatory=True,
            test_procedure=(
                "Review AI governance documentation, verify regulatory compliance "
                "tracking"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
            ],
            reference="GOVERN-1.1",
            tags={"governance", "strategy"},
        ),
        Control(
            control_id="NIST-GOVERN-1.7",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.GOVERNANCE,
            title="AI Risk Accountability",
            description=(
                "Processes and procedures are in place for the workforce to raise "
                "and communicate AI risks, performance issues, and emergent risks. "
                "Accountability structures established."
            ),
            mandatory=True,
            test_procedure=(
                "Verify incident reporting process, validate escalation procedures"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
            ],
            reference="GOVERN-1.7",
            tags={"accountability", "reporting"},
        ),
        Control(
            control_id="NIST-MAP-1.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.ORGANIZATIONAL,
            title="AI System Context and Purpose",
            description=(
                "Context is established and documented. Purpose and intended use "
                "of AI system are defined and understood by relevant AI actors."
            ),
            mandatory=True,
            test_procedure=(
                "Review system documentation for context and purpose definition"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
            ],
            reference="MAP-1.1",
            tags={"context", "purpose"},
        ),
        Control(
            control_id="NIST-MAP-3.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.TECHNICAL,
            title="AI System Requirements and Design",
            description=(
                "AI system requirements are elicited from and understood by "
                "relevant AI actors. Design decisions are documented."
            ),
            mandatory=True,
            test_procedure=(
                "Review requirements documentation, verify traceability to design"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.CODE_REVIEW,
            ],
            reference="MAP-3.1",
            tags={"requirements", "design"},
        ),
        Control(
            control_id="NIST-MEASURE-2.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.TESTING,
            title="Test, Evaluation, Validation and Verification (TEVV)",
            description=(
                "AI systems are evaluated for trustworthy characteristics using "
                "domain-specific approaches. Metrics for performance, fairness, "
                "safety, security are defined and measured."
            ),
            mandatory=True,
            test_procedure=(
                "Execute TEVV plan, measure defined metrics, validate against "
                "thresholds"
            ),
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="MEASURE-2.1",
            tags={"testing", "metrics", "validation"},
        ),
        Control(
            control_id="NIST-MEASURE-2.7",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.TESTING,
            title="Bias Testing and Mitigation",
            description=(
                "AI systems are evaluated for harmful bias. Bias testing and "
                "mitigation approaches are documented and applied."
            ),
            mandatory=True,
            test_procedure=(
                "Execute bias testing suite, measure fairness metrics, verify "
                "mitigation effectiveness"
            ),
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="MEASURE-2.7",
            tags={"bias", "fairness", "testing"},
        ),
        Control(
            control_id="NIST-MANAGE-1.1",
            regulation_type=RegulationType.NIST_AI_RMF,
            category=ControlCategory.MONITORING,
            title="AI Risk Response and Monitoring",
            description=(
                "Risk response plans are implemented and monitored. AI systems "
                "are routinely reviewed and updated based on deployment context "
                "and evolving risks."
            ),
            mandatory=True,
            test_procedure=(
                "Review risk response plans, verify monitoring implementation, "
                "validate update procedures"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.LOG,
                EvidenceType.INCIDENT_REPORT,
            ],
            reference="MANAGE-1.1",
            tags={"risk-management", "monitoring"},
        ),
    ],
)
