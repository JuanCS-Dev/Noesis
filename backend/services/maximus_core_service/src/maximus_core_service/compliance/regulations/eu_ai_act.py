"""
EU AI Act - High-Risk AI System (Tier I).

Regulation on Artificial Intelligence for High-Risk AI systems.

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

EU_AI_ACT = Regulation(
    regulation_type=RegulationType.EU_AI_ACT,
    name="EU Artificial Intelligence Act - High-Risk AI Systems",
    version="1.0",
    effective_date=datetime(2026, 1, 1),
    jurisdiction="European Union",
    description=(
        "Regulation on Artificial Intelligence. VÉRTICE qualifies as High-Risk "
        "AI (Tier I) due to use in law enforcement, critical infrastructure "
        "protection, and biometric systems."
    ),
    authority="European Commission",
    url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206",
    penalties="Up to €30 million or 6% of global annual turnover",
    scope="High-Risk AI systems as defined in Annex III",
    controls=[
        Control(
            control_id="EU-AI-ACT-ART-9",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.GOVERNANCE,
            title="Risk Management System",
            description=(
                "Establish, implement, document and maintain a risk management "
                "system throughout the AI system's lifecycle. Must identify and "
                "analyze known and foreseeable risks, estimate and evaluate risks "
                "arising from intended use and reasonably foreseeable misuse."
            ),
            mandatory=True,
            test_procedure=(
                "Review risk management documentation, verify continuous risk "
                "assessment process, validate risk mitigation measures"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.RISK_ASSESSMENT,
                EvidenceType.POLICY,
            ],
            reference="Article 9",
            tags={"risk", "governance", "lifecycle"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-10",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.TECHNICAL,
            title="Data and Data Governance",
            description=(
                "Training, validation and testing data sets shall be subject to "
                "appropriate data governance and management practices. Data must "
                "be relevant, representative, free of errors and complete. Account "
                "for characteristics/elements particular to geographic, behavioral "
                "or functional setting."
            ),
            mandatory=True,
            test_procedure=(
                "Audit training data provenance, verify data quality metrics, "
                "validate data governance policies"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TEST_RESULT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="Article 10",
            tags={"data", "quality", "bias"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-11",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.DOCUMENTATION,
            title="Technical Documentation",
            description=(
                "Technical documentation must be drawn up before AI system is "
                "placed on market. Must include: general description, detailed "
                "description of elements, data requirements, information on "
                "monitoring/logging, risk management, changes to the system."
            ),
            mandatory=True,
            test_procedure=(
                "Review technical documentation for completeness per Annex IV "
                "requirements"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.CONFIGURATION,
            ],
            reference="Article 11, Annex IV",
            tags={"documentation", "transparency"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-12",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.MONITORING,
            title="Record-Keeping and Logging",
            description=(
                "High-risk AI systems shall be designed with automatic recording "
                "of events (logs) throughout operation. Logging capabilities must "
                "enable traceability, monitoring and auditability."
            ),
            mandatory=True,
            test_procedure=(
                "Verify automatic logging system, test log retention, validate "
                "log completeness"
            ),
            evidence_required=[
                EvidenceType.LOG,
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="Article 12",
            tags={"logging", "auditability", "traceability"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-13",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.TECHNICAL,
            title="Transparency and Information to Users",
            description=(
                "High-risk AI systems shall be designed and developed with "
                "appropriate transparency to enable users to interpret system "
                "output and use it appropriately. Instructions for use must "
                "include intended purpose, accuracy level, robustness, known "
                "limitations."
            ),
            mandatory=True,
            test_procedure=(
                "Review user documentation, verify transparency of AI decisions, "
                "validate user training materials"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TRAINING_RECORD,
            ],
            reference="Article 13",
            tags={"transparency", "explainability", "users"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-14",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.ORGANIZATIONAL,
            title="Human Oversight",
            description=(
                "High-risk AI systems must be designed to enable effective "
                "oversight by natural persons during use. Human oversight "
                "measures must enable humans to: fully understand AI system "
                "capacities and limitations, remain aware of automation bias, "
                "interpret system outputs, decide not to use system, intervene "
                "or interrupt system."
            ),
            mandatory=True,
            test_procedure=(
                "Verify HITL (Human-in-the-Loop) framework implementation, test "
                "override capabilities, validate oversight effectiveness"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TEST_RESULT,
                EvidenceType.CODE_REVIEW,
            ],
            reference="Article 14",
            tags={"hitl", "oversight", "human-control"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-15",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.TECHNICAL,
            title="Accuracy, Robustness and Cybersecurity",
            description=(
                "High-risk AI systems shall be designed and developed to achieve "
                "appropriate levels of accuracy, robustness and cybersecurity. "
                "Must be resilient to errors, faults, inconsistencies, attempts "
                "to manipulate the system. Technical solutions to address AI "
                "specific vulnerabilities."
            ),
            mandatory=True,
            test_procedure=(
                "Execute accuracy testing, perform adversarial testing, conduct "
                "penetration testing"
            ),
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="Article 15",
            tags={"accuracy", "robustness", "security"},
        ),
        Control(
            control_id="EU-AI-ACT-ART-61",
            regulation_type=RegulationType.EU_AI_ACT,
            category=ControlCategory.MONITORING,
            title="Post-Market Monitoring",
            description=(
                "Providers shall establish and document a post-market monitoring "
                "system proportionate to the nature of the AI technologies and "
                "risks. Must actively and systematically collect, document and "
                "analyze data on performance throughout lifetime."
            ),
            mandatory=True,
            test_procedure=(
                "Review post-market monitoring plan, verify incident collection "
                "system, validate reporting process"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.LOG,
                EvidenceType.INCIDENT_REPORT,
            ],
            reference="Article 61",
            tags={"monitoring", "incident-management"},
        ),
    ],
)
