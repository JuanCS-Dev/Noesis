"""
US Executive Order 14110 - Safe, Secure AI.

Executive Order on Safe, Secure, and Trustworthy AI.

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

US_EO_14110 = Regulation(
    regulation_type=RegulationType.US_EO_14110,
    name="US Executive Order 14110 - Safe, Secure, and Trustworthy AI",
    version="2023",
    effective_date=datetime(2023, 10, 30),
    jurisdiction="United States",
    description=(
        "Executive Order on Safe, Secure, and Trustworthy Development and Use "
        "of Artificial Intelligence. Applies to dual-use foundation models and "
        "AI systems affecting critical infrastructure or national security."
    ),
    authority="White House Office of Science and Technology Policy (OSTP)",
    url=(
        "https://www.whitehouse.gov/briefing-room/presidential-actions/2023/10/30/"
        "executive-order-on-the-safe-secure-and-trustworthy-development-and-use-"
        "of-artificial-intelligence/"
    ),
    penalties="Federal enforcement actions",
    scope="Dual-use foundation models, critical infrastructure AI",
    controls=[
        Control(
            control_id="US-EO-14110-SEC-4.2-A",
            regulation_type=RegulationType.US_EO_14110,
            category=ControlCategory.TESTING,
            title="Safety Testing and Red-Team Testing",
            description=(
                "Developers of dual-use foundation models must conduct extensive "
                "red-team testing to identify and address potential risks. Must "
                "test for: chemical, biological, radiological, nuclear risks; "
                "cybersecurity vulnerabilities; harmful biases and discrimination."
            ),
            mandatory=True,
            test_procedure=(
                "Execute red-team testing program, document vulnerabilities, "
                "verify remediation"
            ),
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="Section 4.2(a)",
            tags={"red-team", "safety", "testing"},
        ),
        Control(
            control_id="US-EO-14110-SEC-4.2-B",
            regulation_type=RegulationType.US_EO_14110,
            category=ControlCategory.SECURITY,
            title="Cybersecurity and Supply Chain Security",
            description=(
                "AI systems must implement robust cybersecurity measures. Secure "
                "development practices, vulnerability management, supply chain "
                "security for AI models and data."
            ),
            mandatory=True,
            test_procedure=(
                "Conduct cybersecurity audit, verify secure development lifecycle, "
                "test vulnerability management"
            ),
            evidence_required=[
                EvidenceType.AUDIT_REPORT,
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 4.2(b)",
            tags={"cybersecurity", "supply-chain"},
        ),
        Control(
            control_id="US-EO-14110-SEC-5.1",
            regulation_type=RegulationType.US_EO_14110,
            category=ControlCategory.GOVERNANCE,
            title="AI Risk Management for Critical Infrastructure",
            description=(
                "AI systems affecting critical infrastructure must implement "
                "comprehensive risk management. Identify and mitigate risks to "
                "safety, security, and resilience."
            ),
            mandatory=True,
            test_procedure=(
                "Review critical infrastructure risk assessment, verify "
                "mitigation controls"
            ),
            evidence_required=[
                EvidenceType.RISK_ASSESSMENT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 5.1",
            tags={"critical-infrastructure", "risk"},
        ),
        Control(
            control_id="US-EO-14110-SEC-10.1-B",
            regulation_type=RegulationType.US_EO_14110,
            category=ControlCategory.TESTING,
            title="Bias and Discrimination Testing",
            description=(
                "AI systems must be tested for harmful bias and discrimination. "
                "Implement measures to prevent algorithmic discrimination in "
                "areas such as housing, employment, credit, healthcare."
            ),
            mandatory=True,
            test_procedure=(
                "Execute bias testing across protected classes, measure fairness "
                "metrics, validate mitigation"
            ),
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.DOCUMENT,
            ],
            reference="Section 10.1(b)",
            tags={"bias", "fairness", "discrimination"},
        ),
    ],
)
