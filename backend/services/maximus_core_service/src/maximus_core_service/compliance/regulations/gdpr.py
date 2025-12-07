"""
GDPR - Article 22 Automated Decision-Making.

General Data Protection Regulation for automated individual decision-making.

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

GDPR = Regulation(
    regulation_type=RegulationType.GDPR,
    name="General Data Protection Regulation - Article 22 (Automated Decision-Making)",
    version="2016/679",
    effective_date=datetime(2018, 5, 25),
    jurisdiction="European Union",
    description=(
        "Regulation on automated individual decision-making, including profiling. "
        "VÉRTICE processes personal data for threat detection and automated "
        "response decisions."
    ),
    authority="European Data Protection Board (EDPB)",
    url="https://gdpr-info.eu/",
    penalties="Up to €20 million or 4% of global annual turnover",
    scope="Automated decision-making with legal or similarly significant effects",
    controls=[
        Control(
            control_id="GDPR-ART-22",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.GOVERNANCE,
            title="Right to Human Review of Automated Decisions",
            description=(
                "Data subject has the right not to be subject to decision based "
                "solely on automated processing which produces legal effects or "
                "similarly significantly affects them. Must provide: right to "
                "obtain human intervention, right to express point of view, right "
                "to contest decision."
            ),
            mandatory=True,
            test_procedure=(
                "Verify HITL implementation for decisions affecting individuals, "
                "test human review process, validate appeal mechanism"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
                EvidenceType.TEST_RESULT,
            ],
            reference="Article 22",
            tags={"automated-decision", "human-review", "rights"},
        ),
        Control(
            control_id="GDPR-ART-25",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.TECHNICAL,
            title="Data Protection by Design and by Default",
            description=(
                "Implement appropriate technical and organizational measures to "
                "ensure data processing meets GDPR requirements. Must implement "
                "data minimization, pseudonymization where possible, transparency, "
                "enable data subject rights."
            ),
            mandatory=True,
            test_procedure=(
                "Review system architecture for privacy-by-design, verify data "
                "minimization, test pseudonymization"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.CODE_REVIEW,
                EvidenceType.CONFIGURATION,
            ],
            reference="Article 25",
            tags={"privacy-by-design", "data-minimization"},
        ),
        Control(
            control_id="GDPR-ART-30",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.DOCUMENTATION,
            title="Records of Processing Activities",
            description=(
                "Maintain records of all processing activities under controller's "
                "responsibility. Must include: purposes of processing, categories "
                "of data subjects, categories of personal data, categories of "
                "recipients, transfers to third countries, retention periods, "
                "security measures."
            ),
            mandatory=True,
            test_procedure=(
                "Review processing activity records (ROPA), verify completeness "
                "and accuracy"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="Article 30",
            tags={"documentation", "ropa"},
        ),
        Control(
            control_id="GDPR-ART-32",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.SECURITY,
            title="Security of Processing",
            description=(
                "Implement appropriate technical and organizational measures to "
                "ensure security appropriate to the risk. Must include: "
                "pseudonymization and encryption, ongoing confidentiality/"
                "integrity/availability/resilience, ability to restore "
                "availability after incident, regular testing of measures."
            ),
            mandatory=True,
            test_procedure=(
                "Conduct security audit, test encryption, verify access controls, "
                "validate incident response"
            ),
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.AUDIT_REPORT,
                EvidenceType.CONFIGURATION,
            ],
            reference="Article 32",
            tags={"security", "encryption", "access-control"},
        ),
        Control(
            control_id="GDPR-ART-35",
            regulation_type=RegulationType.GDPR,
            category=ControlCategory.ORGANIZATIONAL,
            title="Data Protection Impact Assessment (DPIA)",
            description=(
                "Conduct DPIA when processing is likely to result in high risk "
                "to rights and freedoms. Required for: systematic and extensive "
                "automated decision-making, large scale processing of special "
                "categories of data, systematic monitoring of publicly accessible "
                "areas."
            ),
            mandatory=True,
            test_procedure=(
                "Review DPIA documentation, verify risk assessment methodology, "
                "validate mitigation measures"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.RISK_ASSESSMENT,
            ],
            reference="Article 35",
            tags={"dpia", "risk-assessment", "privacy"},
        ),
    ],
)
