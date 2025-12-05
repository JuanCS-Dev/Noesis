"""
SOC 2 Type II - Trust Services Criteria.

Service Organization Control 2 Type II audit standard.

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

SOC2_TYPE_II = Regulation(
    regulation_type=RegulationType.SOC2_TYPE_II,
    name="SOC 2 Type II - Trust Services Criteria",
    version="2017",
    effective_date=datetime(2017, 1, 1),
    jurisdiction="United States (accepted globally)",
    description=(
        "Service Organization Control 2 Type II audit. Evaluates controls over: "
        "Security (required), Availability, Processing Integrity, Confidentiality, "
        "Privacy. Type II evaluates effectiveness over time (6-12 months)."
    ),
    authority="American Institute of Certified Public Accountants (AICPA)",
    url="https://www.aicpa.org/soc4so",
    penalties="N/A - Audit report standard",
    scope="Service organizations and SaaS providers",
    controls=[
        Control(
            control_id="SOC2-CC6.1",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.SECURITY,
            title="Logical and Physical Access Controls",
            description=(
                "Entity implements logical and physical access controls to meet "
                "security commitments. Controls include: authentication, "
                "authorization, physical security, network security."
            ),
            mandatory=True,
            test_procedure=(
                "Test access control implementation, verify MFA, validate "
                "physical security"
            ),
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
                EvidenceType.AUDIT_REPORT,
            ],
            reference="CC6.1 (Common Criteria)",
            tags={"access-control", "security", "mfa"},
        ),
        Control(
            control_id="SOC2-CC6.6",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.MONITORING,
            title="Security Event Logging and Monitoring",
            description=(
                "Entity implements logging and monitoring to detect anomalous "
                "behavior. Logs are protected from tampering and reviewed "
                "regularly."
            ),
            mandatory=True,
            test_procedure=(
                "Verify log collection, test log protection, validate monitoring "
                "alerts"
            ),
            evidence_required=[
                EvidenceType.LOG,
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="CC6.6",
            tags={"logging", "monitoring", "siem"},
        ),
        Control(
            control_id="SOC2-CC6.7",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.SECURITY,
            title="Security Incident Management",
            description=(
                "Entity has incident response plan. Security incidents are "
                "identified, reported, assessed, responded to and resolved in "
                "timely manner."
            ),
            mandatory=True,
            test_procedure=(
                "Review incident response plan, test incident detection and "
                "response"
            ),
            evidence_required=[
                EvidenceType.DOCUMENT,
                EvidenceType.INCIDENT_REPORT,
                EvidenceType.TEST_RESULT,
            ],
            reference="CC6.7",
            tags={"incident-response", "security"},
        ),
        Control(
            control_id="SOC2-CC7.2",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.MONITORING,
            title="System Monitoring and Alerting",
            description=(
                "Entity monitors system performance and availability. Capacity "
                "planning is performed. Alerts are configured for performance "
                "degradation."
            ),
            mandatory=True,
            test_procedure=(
                "Verify system monitoring, test alerting, review capacity "
                "planning"
            ),
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.LOG,
                EvidenceType.DOCUMENT,
            ],
            reference="CC7.2 (Availability)",
            tags={"monitoring", "availability", "alerting"},
        ),
        Control(
            control_id="SOC2-PI1.4",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.TESTING,
            title="Processing Integrity - Data Validation",
            description=(
                "Entity implements controls to ensure complete, valid, accurate, "
                "timely and authorized processing. Input validation, error "
                "handling, reconciliation."
            ),
            mandatory=True,
            test_procedure=(
                "Test input validation, verify error handling, validate data "
                "integrity controls"
            ),
            evidence_required=[
                EvidenceType.TEST_RESULT,
                EvidenceType.CODE_REVIEW,
            ],
            reference="PI1.4 (Processing Integrity)",
            tags={"data-validation", "integrity"},
        ),
        Control(
            control_id="SOC2-C1.1",
            regulation_type=RegulationType.SOC2_TYPE_II,
            category=ControlCategory.SECURITY,
            title="Confidentiality - Encryption",
            description=(
                "Entity protects confidential information through encryption in "
                "transit and at rest. Encryption keys are properly managed."
            ),
            mandatory=True,
            test_procedure=(
                "Verify encryption implementation, test key management, validate "
                "cipher strength"
            ),
            evidence_required=[
                EvidenceType.CONFIGURATION,
                EvidenceType.TEST_RESULT,
            ],
            reference="C1.1 (Confidentiality)",
            tags={"encryption", "confidentiality"},
        ),
    ],
)
