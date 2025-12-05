"""ERB Decision Management.

Mixin providing decision management functionality for the Ethics Review Board.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from ..base import (
    DecisionType,
    ERBDecision,
    ERBMeeting,
    ERBMember,
    GovernanceConfig,
    GovernanceResult,
    PolicyType,
)


class DecisionManagementMixin:
    """Mixin providing decision management methods.

    Handles recording decisions, voting calculations, and follow-ups.

    Attributes:
        decisions: Dict of decision_id to ERBDecision.
        meetings: Dict of meeting_id to ERBMeeting.
        stats: Statistics dictionary.
        config: Governance configuration.
    """

    decisions: dict[str, ERBDecision]
    meetings: dict[str, ERBMeeting]
    stats: dict[str, Any]
    config: GovernanceConfig

    def get_chair(self) -> ERBMember | None:
        """Get the ERB chair. To be implemented by the main class."""
        raise NotImplementedError

    def record_decision(
        self,
        meeting_id: str,
        title: str,
        description: str,
        votes_for: int,
        votes_against: int,
        votes_abstain: int = 0,
        rationale: str = "",
        conditions: list[str] | None = None,
        related_policies: list[PolicyType] | None = None,
        follow_up_required: bool = False,
        follow_up_days: int | None = None,
    ) -> GovernanceResult:
        """Record an ERB decision.

        Args:
            meeting_id: Meeting ID where decision was made.
            title: Decision title.
            description: Decision description.
            votes_for: Number of votes in favor.
            votes_against: Number of votes against.
            votes_abstain: Number of abstentions.
            rationale: Rationale for decision.
            conditions: Conditions for conditional approval.
            related_policies: Related policy types.
            follow_up_required: Whether follow-up is required.
            follow_up_days: Days until follow-up deadline.

        Returns:
            GovernanceResult with decision_id.
        """
        if meeting_id not in self.meetings:
            return GovernanceResult(
                success=False,
                message=f"Meeting {meeting_id} not found",
                entity_type="erb_decision",
                errors=["Meeting not found"],
            )

        meeting = self.meetings[meeting_id]

        if not meeting.quorum_met:
            return GovernanceResult(
                success=False,
                message="Cannot record decision: meeting quorum was not met",
                entity_type="erb_decision",
                errors=["Quorum not met"],
            )

        total_votes = votes_for + votes_against + votes_abstain
        if total_votes == 0:
            return GovernanceResult(
                success=False,
                message="Invalid vote count: no votes recorded",
                entity_type="erb_decision",
                errors=["No votes"],
            )

        approval_percentage = (votes_for / total_votes) * 100
        threshold_percentage = self.config.erb_decision_threshold * 100

        decision_type = self._determine_decision_type(
            conditions, approval_percentage, threshold_percentage
        )

        follow_up_deadline = None
        if follow_up_required and follow_up_days is not None:
            follow_up_deadline = datetime.utcnow() + timedelta(days=follow_up_days)

        chair = self.get_chair()
        decision = ERBDecision(
            meeting_id=meeting_id,
            title=title,
            description=description,
            decision_type=decision_type,
            votes_for=votes_for,
            votes_against=votes_against,
            votes_abstain=votes_abstain,
            rationale=rationale,
            conditions=conditions or [],
            follow_up_required=follow_up_required,
            follow_up_deadline=follow_up_deadline,
            created_date=datetime.utcnow(),
            created_by=chair.member_id if chair else "unknown",
            related_policies=related_policies or [],
        )

        self.decisions[decision.decision_id] = decision
        meeting.decisions.append(decision.decision_id)

        self._update_decision_stats(decision, decision_type)

        return GovernanceResult(
            success=True,
            message=(
                f"Decision recorded: {decision_type.value} "
                f"({approval_percentage:.1f}% approval)"
            ),
            entity_id=decision.decision_id,
            entity_type="erb_decision",
            metadata={
                "decision": decision.to_dict(),
                "approval_percentage": approval_percentage,
                "threshold_percentage": threshold_percentage,
            },
        )

    def _determine_decision_type(
        self,
        conditions: list[str] | None,
        approval_percentage: float,
        threshold_percentage: float,
    ) -> DecisionType:
        """Determine decision type based on votes and conditions.

        Args:
            conditions: List of conditions.
            approval_percentage: Approval percentage.
            threshold_percentage: Required threshold.

        Returns:
            DecisionType.
        """
        if conditions and len(conditions) > 0:
            return DecisionType.CONDITIONAL_APPROVED
        if approval_percentage >= threshold_percentage:
            return DecisionType.APPROVED
        return DecisionType.REJECTED

    def _update_decision_stats(
        self,
        decision: ERBDecision,
        decision_type: DecisionType,
    ) -> None:
        """Update statistics after recording a decision.

        Args:
            decision: The recorded decision.
            decision_type: Type of decision.
        """
        self.stats["total_decisions"] += 1
        if decision.is_approved():
            self.stats["decisions_approved"] += 1
        elif decision_type == DecisionType.REJECTED:
            self.stats["decisions_rejected"] += 1

    def get_decision(self, decision_id: str) -> ERBDecision | None:
        """Get decision by ID.

        Args:
            decision_id: Decision ID.

        Returns:
            ERBDecision or None.
        """
        return self.decisions.get(decision_id)

    def get_decisions_by_meeting(self, meeting_id: str) -> list[ERBDecision]:
        """Get all decisions from a meeting.

        Args:
            meeting_id: Meeting ID.

        Returns:
            List of decisions from the meeting.
        """
        return [d for d in self.decisions.values() if d.meeting_id == meeting_id]

    def get_decisions_by_policy(self, policy_type: PolicyType) -> list[ERBDecision]:
        """Get decisions related to a policy type.

        Args:
            policy_type: Policy type to filter by.

        Returns:
            List of related decisions.
        """
        return [d for d in self.decisions.values() if policy_type in d.related_policies]

    def get_pending_follow_ups(self) -> list[ERBDecision]:
        """Get decisions with pending follow-ups.

        Returns:
            List of decisions with pending follow-ups.
        """
        now = datetime.utcnow()
        return [
            d
            for d in self.decisions.values()
            if d.follow_up_required
            and d.follow_up_deadline is not None
            and d.follow_up_deadline > now
        ]

    def get_overdue_follow_ups(self) -> list[ERBDecision]:
        """Get decisions with overdue follow-ups.

        Returns:
            List of decisions with overdue follow-ups.
        """
        now = datetime.utcnow()
        return [
            d
            for d in self.decisions.values()
            if d.follow_up_required
            and d.follow_up_deadline is not None
            and d.follow_up_deadline <= now
        ]

    def calculate_approval(
        self,
        votes_for: int,
        votes_against: int,
        votes_abstain: int,
    ) -> tuple[bool, float]:
        """Calculate if a vote passes the approval threshold.

        Args:
            votes_for: Votes in favor.
            votes_against: Votes against.
            votes_abstain: Abstentions.

        Returns:
            Tuple of (approved, approval_percentage).
        """
        total_votes = votes_for + votes_against + votes_abstain
        if total_votes == 0:
            return False, 0.0

        approval_percentage = (votes_for / total_votes) * 100
        threshold = self.config.erb_decision_threshold * 100

        return approval_percentage >= threshold, approval_percentage
