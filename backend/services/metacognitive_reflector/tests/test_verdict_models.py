"""
Tests for verdict models.
"""

from __future__ import annotations


import pytest
from datetime import datetime

from metacognitive_reflector.models.verdict import (
    VerdictType,
    TribunalDecision,
    PunishmentType,
    OffenseLevel,
    EvidenceModel,
    JudgeVerdictModel,
    VoteBreakdownModel,
    TribunalVerdictModel,
    PunishmentRecordModel,
    AppealRequest,
    AppealResponse,
    RestrictionCheckRequest,
    RestrictionCheckResponse,
)


class TestVerdictEnums:
    """Tests for verdict-related enums."""

    def test_verdict_type_values(self):
        """Test VerdictType enum values."""
        assert VerdictType.PASS == "PASS"
        assert VerdictType.REVIEW == "REVIEW"
        assert VerdictType.FAIL == "FAIL"
        assert VerdictType.ABSTAIN == "ABSTAIN"

    def test_tribunal_decision_values(self):
        """Test TribunalDecision enum values."""
        assert TribunalDecision.PASS == "pass"
        assert TribunalDecision.REVIEW == "review"
        assert TribunalDecision.FAIL == "fail"
        assert TribunalDecision.CAPITAL == "capital"
        assert TribunalDecision.UNAVAILABLE == "unavailable"

    def test_punishment_type_values(self):
        """Test PunishmentType enum values."""
        assert PunishmentType.WARNING == "warning"
        assert PunishmentType.RE_EDUCATION_LOOP == "re_education_loop"
        assert PunishmentType.PROBATION == "probation"
        assert PunishmentType.ROLLBACK == "rollback"
        assert PunishmentType.QUARANTINE == "quarantine"
        assert PunishmentType.SUSPENSION == "suspension"
        assert PunishmentType.DELETION_REQUEST == "deletion_request"

    def test_offense_level_values(self):
        """Test OffenseLevel enum values."""
        assert OffenseLevel.NONE == "none"
        assert OffenseLevel.MINOR == "minor"
        assert OffenseLevel.MAJOR == "major"
        assert OffenseLevel.CAPITAL == "capital"


class TestEvidenceModel:
    """Tests for EvidenceModel."""

    def test_create_evidence(self):
        """Test creating evidence model."""
        evidence = EvidenceModel(
            source="test_source",
            content="test content",
            relevance=0.8,
            verified=True,
        )
        assert evidence.source == "test_source"
        assert evidence.content == "test content"
        assert evidence.relevance == 0.8
        assert evidence.verified is True

    def test_evidence_defaults(self):
        """Test evidence default values."""
        evidence = EvidenceModel(
            source="source",
            content="content",
        )
        assert evidence.relevance == 0.5
        assert evidence.verified is False
        assert isinstance(evidence.timestamp, datetime)
        assert evidence.metadata == {}

    def test_evidence_relevance_validation(self):
        """Test relevance must be between 0 and 1."""
        with pytest.raises(ValueError):
            EvidenceModel(
                source="s",
                content="c",
                relevance=1.5,
            )


class TestJudgeVerdictModel:
    """Tests for JudgeVerdictModel."""

    def test_create_verdict(self):
        """Test creating judge verdict model."""
        verdict = JudgeVerdictModel(
            judge_name="VERITAS",
            pillar="Truth",
            verdict=VerdictType.PASS,
            passed=True,
            confidence=0.9,
            reasoning="All checks passed",
        )
        assert verdict.judge_name == "VERITAS"
        assert verdict.pillar == "Truth"
        assert verdict.passed is True
        assert verdict.confidence == 0.9

    def test_verdict_with_evidence(self):
        """Test verdict with evidence list."""
        evidence = EvidenceModel(source="s", content="c")
        verdict = JudgeVerdictModel(
            judge_name="SOPHIA",
            pillar="Wisdom",
            verdict=VerdictType.REVIEW,
            passed=False,
            confidence=0.6,
            reasoning="Needs review",
            evidence=[evidence],
            suggestions=["Consider more context"],
        )
        assert len(verdict.evidence) == 1
        assert len(verdict.suggestions) == 1


class TestVoteBreakdownModel:
    """Tests for VoteBreakdownModel."""

    def test_create_vote_breakdown(self):
        """Test creating vote breakdown."""
        vote = VoteBreakdownModel(
            judge_name="DIKĒ",
            pillar="Justice",
            vote=0.85,
            weight=0.3,
            confidence=0.9,
            weighted_vote=0.255,
            abstained=False,
        )
        assert vote.judge_name == "DIKĒ"
        assert vote.vote == 0.85
        assert vote.abstained is False

    def test_abstained_vote(self):
        """Test abstained vote."""
        vote = VoteBreakdownModel(
            judge_name="SOPHIA",
            pillar="Wisdom",
            vote=None,
            weight=0.3,
            confidence=0.0,
            weighted_vote=0.0,
            abstained=True,
        )
        assert vote.vote is None
        assert vote.abstained is True


class TestTribunalVerdictModel:
    """Tests for TribunalVerdictModel."""

    def test_create_tribunal_verdict(self):
        """Test creating tribunal verdict."""
        verdict = TribunalVerdictModel(
            decision=TribunalDecision.PASS,
            consensus_score=0.85,
            reasoning="All judges approved",
        )
        assert verdict.decision == TribunalDecision.PASS
        assert verdict.consensus_score == 0.85
        assert verdict.offense_level == OffenseLevel.NONE

    def test_tribunal_verdict_with_punishment(self):
        """Test tribunal verdict with punishment recommendation."""
        verdict = TribunalVerdictModel(
            decision=TribunalDecision.FAIL,
            consensus_score=0.3,
            reasoning="Major violations detected",
            offense_level=OffenseLevel.MAJOR,
            requires_human_review=True,
            punishment_recommendation=PunishmentType.ROLLBACK,
        )
        assert verdict.requires_human_review is True
        assert verdict.punishment_recommendation == PunishmentType.ROLLBACK


class TestPunishmentRecordModel:
    """Tests for PunishmentRecordModel."""

    def test_create_punishment_record(self):
        """Test creating punishment record."""
        record = PunishmentRecordModel(
            agent_id="agent_001",
            status="active",
            offense="truth_violation",
        )
        assert record.agent_id == "agent_001"
        assert record.status == "active"
        assert record.re_education_required is False
        assert record.offense_count == 1


class TestAppealModels:
    """Tests for appeal-related models."""

    def test_create_appeal_request(self):
        """Test creating appeal request."""
        request = AppealRequest(
            trace_id="trace_001",
            agent_id="agent_001",
            original_decision=TribunalDecision.FAIL,
            grounds="New evidence available",
        )
        assert request.trace_id == "trace_001"
        assert request.requested_by == "agent"

    def test_create_appeal_response(self):
        """Test creating appeal response."""
        response = AppealResponse(
            trace_id="trace_001",
            appeal_accepted=True,
            reasoning="New evidence validates claim",
        )
        assert response.appeal_accepted is True
        assert response.reviewed_by == "tribunal"


class TestRestrictionCheckModels:
    """Tests for restriction check models."""

    def test_create_restriction_check_request(self):
        """Test creating restriction check request."""
        request = RestrictionCheckRequest(
            agent_id="agent_001",
            proposed_action="execute_task",
        )
        assert request.agent_id == "agent_001"

    def test_create_restriction_check_response(self):
        """Test creating restriction check response."""
        response = RestrictionCheckResponse(
            agent_id="agent_001",
            allowed=False,
            reason="Agent is quarantined",
            current_status="quarantine",
            restrictions=["no_execution", "monitoring_only"],
            monitoring_enabled=True,
        )
        assert response.allowed is False
        assert len(response.restrictions) == 2
