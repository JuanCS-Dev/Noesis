"""ERB Manager.

Main Ethics Review Board Manager class combining all functionality.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..base import (
    ERBDecision,
    ERBMeeting,
    ERBMember,
    ERBMemberRole,
    GovernanceConfig,
)
from .decisions import DecisionManagementMixin
from .meetings import MeetingManagementMixin
from .members import MemberManagementMixin


class ERBManager(MemberManagementMixin, MeetingManagementMixin, DecisionManagementMixin):
    """Ethics Review Board Manager.

    Manages ERB members, meetings, and decision-making processes.
    Ensures quorum requirements, voting procedures, and governance compliance.

    Attributes:
        config: Governance configuration.
        members: Dict of member_id to ERBMember.
        meetings: Dict of meeting_id to ERBMeeting.
        decisions: Dict of decision_id to ERBDecision.
        stats: Statistics dictionary.
    """

    def __init__(self, config: GovernanceConfig) -> None:
        """Initialize ERB Manager.

        Args:
            config: Governance configuration.
        """
        self.config = config
        self.members: dict[str, ERBMember] = {}
        self.meetings: dict[str, ERBMeeting] = {}
        self.decisions: dict[str, ERBDecision] = {}

        self.stats: dict[str, Any] = {
            "total_members": 0,
            "active_members": 0,
            "total_meetings": 0,
            "total_decisions": 0,
            "decisions_approved": 0,
            "decisions_rejected": 0,
        }

    def get_stats(self) -> dict[str, int]:
        """Get ERB statistics.

        Returns:
            Copy of statistics dictionary.
        """
        return self.stats.copy()

    def get_member_participation(self) -> dict[str, dict[str, Any]]:
        """Get participation statistics for each member.

        Returns:
            Dict mapping member_id to participation stats.
        """
        participation: dict[str, dict[str, Any]] = {}

        for member_id, member in self.members.items():
            if not member.is_active:
                continue

            meetings_attended = sum(
                1 for m in self.meetings.values() if member_id in m.attendees
            )
            meetings_missed = sum(
                1 for m in self.meetings.values() if member_id in m.absentees
            )
            total_meetings = len(
                [m for m in self.meetings.values() if m.status == "completed"]
            )

            attendance_rate = 0.0
            if total_meetings > 0:
                attendance_rate = meetings_attended / total_meetings * 100

            participation[member_id] = {
                "name": member.name,
                "role": member.role.value,
                "meetings_attended": meetings_attended,
                "meetings_missed": meetings_missed,
                "total_meetings": total_meetings,
                "attendance_rate": attendance_rate,
            }

        return participation

    def generate_summary_report(self) -> dict[str, Any]:
        """Generate comprehensive ERB summary report.

        Returns:
            Dict with ERB statistics and summary.
        """
        active_members = self.get_active_members()
        voting_members = self.get_voting_members()
        completed_meetings = [
            m for m in self.meetings.values() if m.status == "completed"
        ]

        approval_rate = 0.0
        if self.stats["total_decisions"] > 0:
            approval_rate = (
                self.stats["decisions_approved"] / self.stats["total_decisions"] * 100
            )

        quorum_met_rate = 0.0
        if completed_meetings:
            quorum_met_count = len([m for m in completed_meetings if m.quorum_met])
            quorum_met_rate = quorum_met_count / len(completed_meetings) * 100

        upcoming_meetings = [
            m
            for m in self.meetings.values()
            if m.status == "scheduled" and m.scheduled_date > datetime.utcnow()
        ]

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "members": {
                "total": self.stats["total_members"],
                "active": self.stats["active_members"],
                "voting": len(voting_members),
                "internal": len([m for m in active_members if m.is_internal]),
                "external": len([m for m in active_members if not m.is_internal]),
                "by_role": {
                    role.value: len(self.get_member_by_role(role))
                    for role in ERBMemberRole
                },
            },
            "meetings": {
                "total": self.stats["total_meetings"],
                "completed": len(completed_meetings),
                "upcoming": len(upcoming_meetings),
                "quorum_met_rate": quorum_met_rate,
            },
            "decisions": {
                "total": self.stats["total_decisions"],
                "approved": self.stats["decisions_approved"],
                "rejected": self.stats["decisions_rejected"],
                "approval_rate": approval_rate,
                "pending_follow_ups": len(self.get_pending_follow_ups()),
                "overdue_follow_ups": len(self.get_overdue_follow_ups()),
            },
            "participation": self.get_member_participation(),
        }
