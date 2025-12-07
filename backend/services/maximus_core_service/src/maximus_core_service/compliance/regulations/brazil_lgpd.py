"""
Brazil LGPD - Lei Geral de Protecao de Dados.

Brazilian General Data Protection Law.

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

BRAZIL_LGPD = Regulation(
    regulation_type=RegulationType.BRAZIL_LGPD,
    name="Lei Geral de Protecao de Dados Pessoais (LGPD)",
    version="Lei no 13.709/2018",
    effective_date=datetime(2020, 9, 18),
    jurisdiction="Brazil",
    description=(
        "Brazilian General Data Protection Law. Regulates processing of personal "
        "data. Similar to GDPR with specific requirements for automated "
        "decision-making."
    ),
    authority="Autoridade Nacional de Protecao de Dados (ANPD)",
    url="https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
    penalties="Up to 2% of revenue (max R$ 50 million per infraction)",
    scope="Processing of personal data in Brazil",
    controls=[
        Control(
            control_id="LGPD-ART-7",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.GOVERNANCE,
            title="Legal Basis for Processing",
            description=(
                "Personal data processing must have legal basis. For sensitive "
                "data, requires explicit consent or legal obligation. Must "
                "document legal basis for each processing activity."
            ),
            mandatory=True,
            test_procedure=(
                "Review legal basis documentation for all processing activities"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
            ],
            reference="Article 7",
            tags={"legal-basis", "consent"},
        ),
        Control(
            control_id="LGPD-ART-18",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.ORGANIZATIONAL,
            title="Data Subject Rights",
            description=(
                "Data subjects have rights to: confirmation of processing, access "
                "to data, correction, anonymization/blocking/deletion, portability, "
                "information about sharing, information about possibility of not "
                "providing consent, revocation of consent."
            ),
            mandatory=True,
            test_procedure=(
                "Verify implementation of data subject rights request process, "
                "test request fulfillment"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
                EvidenceType.TEST_RESULT,
            ],
            reference="Article 18",
            tags={"data-subject-rights", "access"},
        ),
        Control(
            control_id="LGPD-ART-20",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.GOVERNANCE,
            title="Right to Review Automated Decisions",
            description=(
                "Data subject has right to request review of decisions made "
                "solely based on automated processing that affect their interests. "
                "Must provide: information about automated decision-making "
                "criteria, right to contest."
            ),
            mandatory=True,
            test_procedure=(
                "Verify human review process for automated decisions, test review "
                "request handling"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
                EvidenceType.TEST_RESULT,
            ],
            reference="Article 20",
            tags={"automated-decision", "review", "transparency"},
        ),
        Control(
            control_id="LGPD-ART-38",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.ORGANIZATIONAL,
            title="Data Protection Impact Assessment (RIPD)",
            description=(
                "Controller must prepare Data Protection Impact Assessment "
                "(Relatorio de Impacto a Protecao de Dados Pessoais - RIPD) "
                "when requested by ANPD. Must include: description of processing, "
                "legal basis, assessment of necessity and proportionality, "
                "security measures, risk mitigation."
            ),
            mandatory=True,
            test_procedure=(
                "Review RIPD documentation, verify risk assessment methodology"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.RISK_ASSESSMENT,
            ],
            reference="Article 38",
            tags={"ripd", "impact-assessment", "privacy"},
        ),
        Control(
            control_id="LGPD-ART-46",
            regulation_type=RegulationType.BRAZIL_LGPD,
            category=ControlCategory.SECURITY,
            title="Security and Preventive Measures",
            description=(
                "Controllers and operators must adopt security, technical and "
                "administrative measures to protect personal data. Must prevent: "
                "unauthorized access, accidental or unlawful destruction, loss, "
                "alteration, communication or diffusion."
            ),
            mandatory=True,
            test_procedure=(
                "Conduct security audit, test access controls, verify encryption, "
                "validate incident response"
            ),
            evidence_required=[
                EvidenceType.AUDIT_REPORT,
                EvidenceType.TEST_RESULT,
                EvidenceType.CONFIGURATION,
            ],
            reference="Article 46",
            tags={"security", "encryption", "access-control"},
        ),
    ],
)
