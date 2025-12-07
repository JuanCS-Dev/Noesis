"""
ISO/IEC 27001:2022 - Information Security Management.

International standard for Information Security Management Systems.

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

ISO_27001 = Regulation(
    regulation_type=RegulationType.ISO_27001,
    name="ISO/IEC 27001:2022 - Information Security Management System",
    version="2022",
    effective_date=datetime(2022, 10, 25),
    jurisdiction="International",
    description=(
        "International standard for Information Security Management Systems "
        "(ISMS). Provides requirements for establishing, implementing, "
        "maintaining and continually improving an ISMS."
    ),
    authority="International Organization for Standardization (ISO)",
    url="https://www.iso.org/standard/27001",
    penalties="N/A - Certification standard",
    scope="Information security management",
    controls=[
        Control(
            control_id="ISO-27001-A.5.1",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.GOVERNANCE,
            title="Information Security Policies",
            description=(
                "Information security policy and topic-specific policies shall "
                "be defined, approved by management, published, communicated and "
                "acknowledged by relevant personnel."
            ),
            mandatory=True,
            test_procedure=(
                "Review information security policies, verify approval and "
                "communication"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.POLICY,
            ],
            reference="A.5.1",
            tags={"policy", "governance"},
        ),
        Control(
            control_id="ISO-27001-A.8.1",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.TECHNICAL,
            title="User Endpoint Devices",
            description=(
                "Information stored on, processed by or accessible via user "
                "endpoint devices shall be protected. Implement controls for: "
                "device registration, encryption, remote wipe, secure "
                "configuration."
            ),
            mandatory=True,
            test_procedure=(
                "Test endpoint security controls, verify encryption, validate "
                "device management"
            ),
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.1",
            tags={"endpoint", "encryption"},
        ),
        Control(
            control_id="ISO-27001-A.8.2",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.SECURITY,
            title="Privileged Access Rights",
            description=(
                "Allocation and use of privileged access rights shall be "
                "restricted and managed. Implement: least privilege, separation "
                "of duties, privileged access monitoring, MFA for privileged "
                "accounts."
            ),
            mandatory=True,
            test_procedure=(
                "Review privileged access controls, test access restrictions, "
                "verify monitoring"
            ),
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.LOG,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="A.8.2",
            tags={"access-control", "privilege"},
        ),
        Control(
            control_id="ISO-27001-A.8.10",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.SECURITY,
            title="Information Deletion",
            description=(
                "Information stored in information systems, devices or any other "
                "storage media shall be deleted when no longer required. "
                "Implement secure deletion procedures."
            ),
            mandatory=True,
            test_procedure=(
                "Verify secure deletion procedures, test data sanitization"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.10",
            tags={"data-deletion", "sanitization"},
        ),
        Control(
            control_id="ISO-27001-A.8.16",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.MONITORING,
            title="Monitoring Activities",
            description=(
                "Networks, systems and applications shall be monitored for "
                "anomalous behavior. Security events shall be recorded. Logs "
                "shall be protected and analyzed."
            ),
            mandatory=True,
            test_procedure=(
                "Verify monitoring implementation, test log collection, validate "
                "log protection"
            ),
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.LOG,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.16",
            tags={"monitoring", "logging", "siem"},
        ),
        Control(
            control_id="ISO-27001-A.8.23",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.TECHNICAL,
            title="Web Filtering",
            description=(
                "Access to external websites shall be managed to reduce exposure "
                "to malicious content. Implement web filtering and categorization."
            ),
            mandatory=False,
            test_procedure=(
                "Test web filtering implementation, verify categorization rules"
            ),
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.23",
            tags={"web-filtering", "security"},
        ),
        Control(
            control_id="ISO-27001-A.8.24",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.SECURITY,
            title="Use of Cryptography",
            description=(
                "Rules for the effective use of cryptography shall be defined "
                "and implemented. Include: encryption algorithms, key management, "
                "secure protocols."
            ),
            mandatory=True,
            test_procedure=(
                "Review cryptographic standards, verify algorithm strength, test "
                "key management"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="A.8.24",
            tags={"cryptography", "encryption"},
        ),
    ],
)
