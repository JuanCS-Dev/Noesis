"""
Ethics Review Board (ERB) Data Models.

Contains ERB member, meeting, and decision models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..enums import DecisionType, ERBMemberRole, PolicyType


@dataclass
class ERBMember:
    """Ethics Review Board member."""

    member_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    email: str = ""
    role: ERBMemberRole = ERBMemberRole.TECHNICAL_MEMBER
    organization: str = ""  # Internal or external organization
    expertise: list[str] = field(default_factory=list)  # e.g., ["AI ethics", "Legal"]
    is_internal: bool = True
    is_active: bool = True
    appointed_date: datetime = field(default_factory=datetime.utcnow)
    term_end_date: datetime | None = None
    voting_rights: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_voting_member(self) -> bool:
        """Check if member has voting rights and is active."""
        return (
            self.is_active
            and self.voting_rights
            and (self.term_end_date is None or self.term_end_date > datetime.utcnow())
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "member_id": self.member_id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "organization": self.organization,
            "expertise": self.expertise,
            "is_internal": self.is_internal,
            "is_active": self.is_active,
            "appointed_date": self.appointed_date.isoformat(),
            "term_end_date": self.term_end_date.isoformat() if self.term_end_date else None,
            "voting_rights": self.voting_rights,
            "metadata": self.metadata,
        }


@dataclass
class ERBMeeting:
    """Ethics Review Board meeting."""

    meeting_id: str = field(default_factory=lambda: str(uuid4()))
    scheduled_date: datetime = field(default_factory=datetime.utcnow)
    actual_date: datetime | None = None
    duration_minutes: int = 120
    location: str = "Virtual"  # Virtual or physical location
    agenda: list[str] = field(default_factory=list)
    attendees: list[str] = field(default_factory=list)  # member_ids
    absentees: list[str] = field(default_factory=list)  # member_ids
    minutes: str = ""  # Meeting minutes
    decisions: list[str] = field(default_factory=list)  # decision_ids
    quorum_met: bool = False
    status: str = "scheduled"  # scheduled, completed, cancelled
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "meeting_id": self.meeting_id,
            "scheduled_date": self.scheduled_date.isoformat(),
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "duration_minutes": self.duration_minutes,
            "location": self.location,
            "agenda": self.agenda,
            "attendees": self.attendees,
            "absentees": self.absentees,
            "minutes": self.minutes,
            "decisions": self.decisions,
            "quorum_met": self.quorum_met,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class ERBDecision:
    """Ethics Review Board decision."""

    decision_id: str = field(default_factory=lambda: str(uuid4()))
    meeting_id: str = ""
    title: str = ""
    description: str = ""
    decision_type: DecisionType = DecisionType.APPROVED
    votes_for: int = 0
    votes_against: int = 0
    votes_abstain: int = 0
    rationale: str = ""
    conditions: list[str] = field(default_factory=list)  # If conditional approval
    follow_up_required: bool = False
    follow_up_deadline: datetime | None = None
    created_date: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""  # member_id of chair
    related_policies: list[PolicyType] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_approved(self) -> bool:
        """Check if decision is approved (fully or conditionally)."""
        return self.decision_type in [DecisionType.APPROVED, DecisionType.CONDITIONAL_APPROVED]

    def approval_percentage(self) -> float:
        """Calculate approval percentage."""
        total_votes = self.votes_for + self.votes_against + self.votes_abstain
        if total_votes == 0:
            return 0.0
        return (self.votes_for / total_votes) * 100.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "meeting_id": self.meeting_id,
            "title": self.title,
            "description": self.description,
            "decision_type": self.decision_type.value,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "votes_abstain": self.votes_abstain,
            "rationale": self.rationale,
            "conditions": self.conditions,
            "follow_up_required": self.follow_up_required,
            "follow_up_deadline": self.follow_up_deadline.isoformat() if self.follow_up_deadline else None,
            "created_date": self.created_date.isoformat(),
            "created_by": self.created_by,
            "related_policies": [p.value for p in self.related_policies],
            "metadata": self.metadata,
            "is_approved": self.is_approved(),
            "approval_percentage": self.approval_percentage(),
        }
