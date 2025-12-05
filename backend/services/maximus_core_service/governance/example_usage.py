"""
Governance Module - Example Usage

Demonstrates 3 practical use cases for the governance module:
1. ERB Meeting & Decision Making
2. Policy Enforcement
3. Whistleblower Report Handling

Run: python example_usage.py

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations


from datetime import datetime, timedelta

from .base import (
    ERBMemberRole,
    GovernanceConfig,
    PolicySeverity,
    PolicyType,
    WhistleblowerReport,
)
from .ethics_review_board import ERBManager
from .policy_engine import PolicyEngine


def print_header(title: str) -> None:
    """Print section header."""
    logger.info("=" * 80)
    logger.info("  %s", title)
    print("=" * 80 + "\n")


def example_1_erb_meeting_decision() -> None:
    """
    Example 1: ERB Meeting & Decision Making

    Scenario: ERB reviews and approves new Ethical Use Policy.
    """
    print_header("EXAMPLE 1: ERB Meeting & Decision Making")

    config = GovernanceConfig()
    erb = ERBManager(config)

    # Step 1: Add ERB members
    logger.info("📋 STEP 1: Adding ERB Members")
    members = [
        ("Dr. Alice Chen", "alice@vertice.ai", ERBMemberRole.CHAIR, ["AI Ethics", "Philosophy"]),
        ("Bob Martinez", "bob@vertice.ai", ERBMemberRole.VICE_CHAIR, ["Legal", "Compliance"]),
        ("Carol Kim", "carol@vertice.ai", ERBMemberRole.TECHNICAL_MEMBER, ["Cybersecurity"]),
        ("David Brown", "david@external.com", ERBMemberRole.EXTERNAL_ADVISOR, ["AI Safety"]),
    ]

    for name, email, role, expertise in members:
        result = erb.add_member(
            name, email, role, "VÉRTICE" if role != ERBMemberRole.EXTERNAL_ADVISOR else "External", expertise
        )
        logger.info("   ✓ Added: %s ({role.value})", name)

    # Step 2: Schedule meeting
    logger.info("\n📅 STEP 2: Scheduling ERB Meeting")
    meeting_date = datetime.utcnow() + timedelta(days=7)
    meeting_result = erb.schedule_meeting(
        scheduled_date=meeting_date,
        agenda=["Review Ethical Use Policy v1.0", "Q4 Ethics Audit Results"],
        duration_minutes=120,
    )
    meeting_id = meeting_result.entity_id
    print(f"   ✓ Meeting scheduled for {meeting_date.strftime('%Y-%m-%d %H:%M')}")

    # Step 3: Record attendance
    logger.info("\n👥 STEP 3: Recording Attendance")
    attendee_ids = [m.member_id for m in erb.get_voting_members()]
    attendance_result = erb.record_attendance(meeting_id, attendee_ids[:3], attendee_ids[3:])
    logger.info("   ✓ Quorum met: %s", attendance_result.metadata.get('quorum_met'))
    logger.info("   ✓ Voting attendees: %s", attendance_result.metadata.get('voting_attendees'))

    # Step 4: Record decision
    logger.info("\n🗳️  STEP 4: Recording Decision")
    decision_result = erb.record_decision(
        meeting_id=meeting_id,
        title="Approve Ethical Use Policy v1.0",
        description="Approve VÉRTICE Ethical Use Policy version 1.0",
        votes_for=3,
        votes_against=0,
        votes_abstain=0,
        rationale="Policy aligns with EU AI Act and organizational values",
        related_policies=[PolicyType.ETHICAL_USE],
    )
    logger.info("   ✓ Decision: %s", erb.decisions[decision_result.entity_id].decision_type.value)
    logger.info("   ✓ Approval rate: %.1f%", decision_result.metadata['approval_percentage'])

    logger.info("\n✅ Example 1 Complete!\n")


def example_2_policy_enforcement() -> None:
    """
    Example 2: Policy Enforcement

    Scenario: Security analyst attempts to execute red team operation.
    Policy engine validates against all policies.
    """
    print_header("EXAMPLE 2: Policy Enforcement")

    config = GovernanceConfig()
    engine = PolicyEngine(config)

    # Scenario 1: Authorized red team operation
    logger.info("🎯 SCENARIO 1: Authorized Red Team Operation")
    result1 = engine.enforce_policy(
        policy_type=PolicyType.RED_TEAMING,
        action="execute_exploit",
        context={
            "written_authorization": True,
            "target_environment": "test",
            "roe_defined": True,
            "logged": True,
        },
        actor="red_team_lead",
    )
    logger.info("   Compliant: %s", result1.is_compliant)
    logger.info("   Checked rules: %s", result1.checked_rules)
    logger.info("   Violations: %s", len(result1.violations))

    # Scenario 2: Unauthorized action
    logger.info("\n🚨 SCENARIO 2: Unauthorized Action (Should Fail)")
    result2 = engine.enforce_policy(
        policy_type=PolicyType.RED_TEAMING,
        action="execute_exploit",
        context={
            "written_authorization": False,
            "target_environment": "production",
        },
        actor="unauthorized_user",
    )
    logger.info("   Compliant: %s", result2.is_compliant)
    logger.info("   Violations: %s", len(result2.violations))
    if result2.violations:
        logger.info("   First violation: %s", result2.violations[0].title)

    # Scenario 3: Data privacy check
    logger.info("\n🔒 SCENARIO 3: Data Privacy Check")
    result3 = engine.enforce_policy(
        policy_type=PolicyType.DATA_PRIVACY,
        action="store_personal_data",
        context={
            "encrypted": True,
            "legal_basis": "consent",
            "logged": True,
        },
        actor="system",
    )
    logger.info("   Compliant: %s", result3.is_compliant)
    logger.info("   Compliance: %.1f%", result3.compliance_percentage())

    logger.info("\n✅ Example 2 Complete!\n")


def example_3_whistleblower_report() -> None:
    """
    Example 3: Whistleblower Report Handling

    Scenario: Anonymous whistleblower reports ethical concern.
    """
    print_header("EXAMPLE 3: Whistleblower Report Handling")

    # Create anonymous whistleblower report
    logger.info("📢 STEP 1: Submitting Anonymous Whistleblower Report")
    report = WhistleblowerReport(
        submission_date=datetime.utcnow(),
        reporter_id=None,  # Anonymous
        is_anonymous=True,
        title="Unauthorized use of offensive tools",
        description="Observed red team tools being used against non-authorized targets",
        alleged_violation_type=PolicyType.RED_TEAMING,
        severity=PolicySeverity.HIGH,
        affected_systems=["offensive_gateway", "c2_orchestration_service"],
        evidence=["logs/2025-10-06-suspicious-activity.log"],
        status="submitted",
        retaliation_concerns=True,
    )
    logger.info("   ✓ Report ID: %s", report.report_id)
    logger.info("   ✓ Anonymous: %s", report.is_anonymous)
    logger.info("   ✓ Severity: %s", report.severity.value)

    # Assign investigator
    logger.info("\n🔍 STEP 2: Assigning Investigator")
    report.status = "under_review"
    report.assigned_investigator = "security_lead@vertice.ai"
    logger.info("   ✓ Status: %s", report.status)
    logger.info("   ✓ Investigator: %s", report.assigned_investigator)

    # Apply protection measures
    logger.info("\n🛡️  STEP 3: Applying Whistleblower Protection")
    report.protection_measures = [
        "Anonymous identity maintained",
        "No retaliation monitoring active",
        "Legal support available if needed",
    ]
    for measure in report.protection_measures:
        logger.info("   ✓ %s", measure)

    # Resolve
    logger.info("\n✅ STEP 4: Investigation Complete")
    report.status = "resolved"
    report.resolution = "Violation confirmed. Tools access revoked. Additional training mandated."
    report.resolution_date = datetime.utcnow()
    report.escalated_to_erb = True
    logger.info("   ✓ Resolution: %s", report.resolution)
    logger.info("   ✓ Escalated to ERB: %s", report.escalated_to_erb)

    logger.info("\n✅ Example 3 Complete!\n")


def run_all_examples() -> None:
    """Run all examples."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "GOVERNANCE MODULE - EXAMPLES" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")

    example_1_erb_meeting_decision()
    example_2_policy_enforcement()
    example_3_whistleblower_report()

    logger.info("=" * 80)
    logger.info("  All examples completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    run_all_examples()
