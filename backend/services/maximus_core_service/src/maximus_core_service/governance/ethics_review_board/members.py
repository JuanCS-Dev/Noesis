"""ERB Member Management.

Mixin providing member management functionality for the Ethics Review Board.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from ..base import (
    ERBMember,
    ERBMemberRole,
    GovernanceResult,
)


class MemberManagementMixin:
    """Mixin providing member management methods.

    Handles adding, removing, and querying ERB members.

    Attributes:
        members: Dict of member_id to ERBMember.
        stats: Statistics dictionary.
    """

    members: dict[str, ERBMember]
    stats: dict[str, Any]

    def add_member(
        self,
        name: str,
        email: str,
        role: ERBMemberRole,
        organization: str,
        expertise: list[str],
        is_internal: bool = True,
        term_months: int | None = None,
        voting_rights: bool = True,
    ) -> GovernanceResult:
        """Add a new ERB member.

        Args:
            name: Member name.
            email: Member email.
            role: ERB role.
            organization: Organization affiliation.
            expertise: Areas of expertise.
            is_internal: Internal vs external member.
            term_months: Term duration in months (None = indefinite).
            voting_rights: Whether member has voting rights.

        Returns:
            GovernanceResult with member_id.
        """
        if not name or not email:
            return GovernanceResult(
                success=False,
                message="Name and email are required",
                entity_type="erb_member",
                errors=["Missing required fields"],
            )

        for member in self.members.values():
            if member.email == email and member.is_active:
                return GovernanceResult(
                    success=False,
                    message=f"Active member with email {email} already exists",
                    entity_type="erb_member",
                    errors=["Duplicate email"],
                )

        term_end_date = None
        if term_months is not None:
            term_end_date = datetime.utcnow() + timedelta(days=term_months * 30)

        member = ERBMember(
            name=name,
            email=email,
            role=role,
            organization=organization,
            expertise=expertise,
            is_internal=is_internal,
            is_active=True,
            appointed_date=datetime.utcnow(),
            term_end_date=term_end_date,
            voting_rights=voting_rights,
        )

        self.members[member.member_id] = member

        self.stats["total_members"] += 1
        self.stats["active_members"] += 1

        return GovernanceResult(
            success=True,
            message=f"ERB member {name} added successfully",
            entity_id=member.member_id,
            entity_type="erb_member",
            metadata={"member": member.to_dict()},
        )

    def remove_member(self, member_id: str, reason: str = "") -> GovernanceResult:
        """Remove (deactivate) an ERB member.

        Args:
            member_id: Member ID to remove.
            reason: Reason for removal.

        Returns:
            GovernanceResult.
        """
        if member_id not in self.members:
            return GovernanceResult(
                success=False,
                message=f"Member {member_id} not found",
                entity_type="erb_member",
                errors=["Member not found"],
            )

        member = self.members[member_id]
        if not member.is_active:
            return GovernanceResult(
                success=False,
                message=f"Member {member.name} is already inactive",
                entity_type="erb_member",
                warnings=["Member already inactive"],
            )

        member.is_active = False
        member.metadata["removal_reason"] = reason
        member.metadata["removal_date"] = datetime.utcnow().isoformat()

        self.stats["active_members"] -= 1

        return GovernanceResult(
            success=True,
            message=f"ERB member {member.name} removed successfully",
            entity_id=member_id,
            entity_type="erb_member",
            metadata={"reason": reason},
        )

    def get_active_members(self) -> list[ERBMember]:
        """Get all active ERB members.

        Returns:
            List of active members.
        """
        return [m for m in self.members.values() if m.is_active]

    def get_voting_members(self) -> list[ERBMember]:
        """Get all members with voting rights.

        Returns:
            List of voting members.
        """
        return [m for m in self.members.values() if m.is_voting_member()]

    def get_member_by_role(self, role: ERBMemberRole) -> list[ERBMember]:
        """Get members by role.

        Args:
            role: ERB member role to filter by.

        Returns:
            List of members with the specified role.
        """
        return [m for m in self.members.values() if m.is_active and m.role == role]

    def get_chair(self) -> ERBMember | None:
        """Get the ERB chair.

        Returns:
            Chair member or None if not found.
        """
        chairs = self.get_member_by_role(ERBMemberRole.CHAIR)
        return chairs[0] if chairs else None
