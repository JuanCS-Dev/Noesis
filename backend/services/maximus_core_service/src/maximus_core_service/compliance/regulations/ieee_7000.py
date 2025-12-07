"""
IEEE 7000-2021 - Ethical AI Design.

Standard for addressing ethical concerns during system design.

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

IEEE_7000 = Regulation(
    regulation_type=RegulationType.IEEE_7000,
    name="IEEE 7000-2021 - Model Process for Addressing Ethical Concerns",
    version="2021",
    effective_date=datetime(2021, 9, 9),
    jurisdiction="International",
    description=(
        "Standard for addressing ethical concerns during system design. "
        "Value-based engineering approach. Applicable to AI systems with "
        "societal impact."
    ),
    authority="IEEE Standards Association",
    url="https://standards.ieee.org/standard/7000-2021.html",
    penalties="N/A - Voluntary standard",
    scope="Systems with ethical implications",
    controls=[
        Control(
            control_id="IEEE-7000-5.2",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.ORGANIZATIONAL,
            title="Stakeholder Analysis",
            description=(
                "Identify and analyze all stakeholders who may be affected by "
                "the system. Document stakeholder values, concerns, and potential "
                "impacts. Include: direct users, indirect users, affected "
                "communities."
            ),
            mandatory=True,
            test_procedure=(
                "Review stakeholder analysis documentation, verify completeness "
                "of stakeholder identification"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.2",
            tags={"stakeholders", "ethics"},
        ),
        Control(
            control_id="IEEE-7000-5.3",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.ORGANIZATIONAL,
            title="Value Elicitation",
            description=(
                "Elicit values from stakeholders through structured methodology. "
                "Document: core values, value conflicts, value priorities. Values "
                "must be specific, measurable, and actionable."
            ),
            mandatory=True,
            test_procedure=(
                "Review value elicitation process, verify stakeholder "
                "participation, validate value documentation"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.3",
            tags={"values", "stakeholders", "ethics"},
        ),
        Control(
            control_id="IEEE-7000-5.4",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.ORGANIZATIONAL,
            title="Value-Based Requirements",
            description=(
                "Translate stakeholder values into verifiable system requirements. "
                "Requirements must be: traceable to values, testable, prioritized. "
                "Include acceptance criteria."
            ),
            mandatory=True,
            test_procedure=(
                "Review requirements traceability matrix, verify value linkage, "
                "validate testability"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.4",
            tags={"requirements", "values", "traceability"},
        ),
        Control(
            control_id="IEEE-7000-5.5",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.ORGANIZATIONAL,
            title="Ethical Risk Assessment",
            description=(
                "Conduct ethical risk assessment throughout system lifecycle. "
                "Identify: value conflicts, unintended consequences, potential "
                "harms to stakeholders. Document mitigation strategies."
            ),
            mandatory=True,
            test_procedure=(
                "Review ethical risk assessment, verify mitigation strategies, "
                "validate stakeholder review"
            ),
            evidence_required=[
                EvidenceType.RISK_ASSESSMENT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.5",
            tags={"ethics", "risk-assessment"},
        ),
        Control(
            control_id="IEEE-7000-5.7",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.TECHNICAL,
            title="Transparency and Explainability",
            description=(
                "System design must incorporate transparency and explainability "
                "appropriate to stakeholder needs. Users must understand: how "
                "system works, why decisions were made, limitations of system."
            ),
            mandatory=True,
            test_procedure=(
                "Test explainability features, verify transparency documentation, "
                "validate user understanding"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TEST_RESULT,
                EvidenceType.CODE_REVIEW,
            ],
            reference="Section 5.7",
            tags={"transparency", "explainability", "xai"},
        ),
        Control(
            control_id="IEEE-7000-6.1",
            regulation_type=RegulationType.IEEE_7000,
            category=ControlCategory.TESTING,
            title="Value Verification and Validation",
            description=(
                "Verify that system requirements align with stakeholder values. "
                "Validate that implemented system meets value-based requirements. "
                "Conduct stakeholder acceptance testing."
            ),
            mandatory=True,
            test_procedure=(
                "Execute value validation tests, conduct stakeholder acceptance "
                "testing, verify requirement satisfaction"
            ),
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 6.1",
            tags={"testing", "validation", "values"},
        ),
    ],
)
