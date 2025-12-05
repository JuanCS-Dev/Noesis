"""ERB Meeting Management.

Mixin providing meeting management functionality for the Ethics Review Board.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..base import (
    ERBMeeting,
    GovernanceConfig,
    GovernanceResult,
)


class MeetingManagementMixin:
    """Mixin providing meeting management methods.

    Handles scheduling, recording attendance, and managing ERB meetings.

    Attributes:
        meetings: Dict of meeting_id to ERBMeeting.
        stats: Statistics dictionary.
        config: Governance configuration.
    """

    meetings: dict[str, ERBMeeting]
    stats: dict[str, Any]
    config: GovernanceConfig

    def get_voting_members(self) -> list[Any]:
        """Get voting members. To be implemented by the main class."""
        raise NotImplementedError

    def schedule_meeting(
        self,
        scheduled_date: datetime,
        agenda: list[str],
        duration_minutes: int = 120,
        location: str = "Virtual",
    ) -> GovernanceResult:
        """Schedule an ERB meeting.

        Args:
            scheduled_date: Meeting date and time.
            agenda: Meeting agenda items.
            duration_minutes: Meeting duration.
            location: Meeting location.

        Returns:
            GovernanceResult with meeting_id.
        """
        if scheduled_date < datetime.utcnow():
            return GovernanceResult(
                success=False,
                message="Meeting date must be in the future",
                entity_type="erb_meeting",
                errors=["Invalid date"],
            )

        meeting = ERBMeeting(
            scheduled_date=scheduled_date,
            duration_minutes=duration_minutes,
            location=location,
            agenda=agenda,
            status="scheduled",
        )

        self.meetings[meeting.meeting_id] = meeting
        self.stats["total_meetings"] += 1

        return GovernanceResult(
            success=True,
            message=f"Meeting scheduled for {scheduled_date.strftime('%Y-%m-%d %H:%M')}",
            entity_id=meeting.meeting_id,
            entity_type="erb_meeting",
            metadata={"meeting": meeting.to_dict()},
        )

    def record_attendance(
        self,
        meeting_id: str,
        attendees: list[str],
        absentees: list[str] | None = None,
    ) -> GovernanceResult:
        """Record meeting attendance.

        Args:
            meeting_id: Meeting ID.
            attendees: List of member IDs who attended.
            absentees: List of member IDs who were absent.

        Returns:
            GovernanceResult.
        """
        if meeting_id not in self.meetings:
            return GovernanceResult(
                success=False,
                message=f"Meeting {meeting_id} not found",
                entity_type="erb_meeting",
                errors=["Meeting not found"],
            )

        meeting = self.meetings[meeting_id]
        meeting.attendees = attendees
        meeting.absentees = absentees or []
        meeting.actual_date = datetime.utcnow()

        voting_members = self.get_voting_members()
        voting_member_ids = {m.member_id for m in voting_members}
        voting_attendees = [a for a in attendees if a in voting_member_ids]

        quorum_required = len(voting_members) * self.config.erb_quorum_percentage
        meeting.quorum_met = len(voting_attendees) >= quorum_required

        if not meeting.quorum_met:
            return GovernanceResult(
                success=True,
                message="Attendance recorded, but quorum NOT met",
                entity_id=meeting_id,
                entity_type="erb_meeting",
                warnings=[
                    f"Quorum not met: {len(voting_attendees)}/{len(voting_members)} "
                    f"voting members present (required: {quorum_required:.0f})"
                ],
                metadata={
                    "quorum_met": False,
                    "voting_attendees": len(voting_attendees),
                    "total_voting_members": len(voting_members),
                },
            )

        return GovernanceResult(
            success=True,
            message=(
                f"Attendance recorded, quorum met "
                f"({len(voting_attendees)}/{len(voting_members)})"
            ),
            entity_id=meeting_id,
            entity_type="erb_meeting",
            metadata={
                "quorum_met": True,
                "voting_attendees": len(voting_attendees),
                "total_voting_members": len(voting_members),
            },
        )

    def add_meeting_minutes(
        self,
        meeting_id: str,
        minutes: str,
    ) -> GovernanceResult:
        """Add meeting minutes.

        Args:
            meeting_id: Meeting ID.
            minutes: Meeting minutes text.

        Returns:
            GovernanceResult.
        """
        if meeting_id not in self.meetings:
            return GovernanceResult(
                success=False,
                message=f"Meeting {meeting_id} not found",
                entity_type="erb_meeting",
                errors=["Meeting not found"],
            )

        meeting = self.meetings[meeting_id]
        meeting.minutes = minutes
        meeting.status = "completed"

        return GovernanceResult(
            success=True,
            message="Meeting minutes added successfully",
            entity_id=meeting_id,
            entity_type="erb_meeting",
        )

    def check_quorum(self, attendee_ids: list[str]) -> tuple[bool, dict[str, int]]:
        """Check if quorum is met for a given list of attendees.

        Args:
            attendee_ids: List of member IDs.

        Returns:
            Tuple of (quorum_met, stats_dict).
        """
        voting_members = self.get_voting_members()
        voting_member_ids = {m.member_id for m in voting_members}
        voting_attendees = [a for a in attendee_ids if a in voting_member_ids]

        quorum_required = len(voting_members) * self.config.erb_quorum_percentage
        quorum_met = len(voting_attendees) >= quorum_required

        return quorum_met, {
            "total_voting_members": len(voting_members),
            "voting_attendees": len(voting_attendees),
            "quorum_required": quorum_required,
            "quorum_percentage": self.config.erb_quorum_percentage * 100,
        }
