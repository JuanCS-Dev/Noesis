"""
MAXIMUS 2.0 - Tests for Punishment Handlers
============================================

Tests for punishment execution handlers and executor.
"""

from __future__ import annotations


import pytest

from metacognitive_reflector.core.punishment import (
    DeletionHandler,
    OffenseType,
    PenalRegistry,
    PenalStatus,
    PunishmentExecutor,
    PunishmentResult,
    QuarantineHandler,
    ReEducationHandler,
    RollbackHandler,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def registry():
    """Create a test PenalRegistry."""
    return PenalRegistry()


@pytest.fixture
def re_education_handler(registry):
    """Create ReEducationHandler."""
    return ReEducationHandler(registry, duration_hours=1)


@pytest.fixture
def rollback_handler(registry):
    """Create RollbackHandler."""
    return RollbackHandler(registry, quarantine_hours=1)


@pytest.fixture
def quarantine_handler(registry):
    """Create QuarantineHandler."""
    return QuarantineHandler(registry, duration_hours=1)


@pytest.fixture
def deletion_handler(registry):
    """Create DeletionHandler."""
    return DeletionHandler(registry)


@pytest.fixture
def executor(registry):
    """Create PunishmentExecutor."""
    return PunishmentExecutor(registry)


# ============================================================================
# ReEducationHandler Tests
# ============================================================================

class TestReEducationHandler:
    """Tests for ReEducationHandler."""

    def test_handler_properties(self, re_education_handler):
        """Test handler properties."""
        assert re_education_handler.punishment_type == "RE_EDUCATION"
        assert re_education_handler.severity == 1

    @pytest.mark.asyncio
    async def test_execute_re_education(self, re_education_handler):
        """Test executing re-education punishment."""
        outcome = await re_education_handler.execute(
            agent_id="test-agent-001",
            offense=OffenseType.TRUTH_VIOLATION,
            context={"offense_details": "Minor hallucination detected"},
        )

        assert outcome.result == PunishmentResult.SUCCESS
        assert outcome.handler == "RE_EDUCATION"
        assert outcome.agent_id == "test-agent-001"
        assert outcome.requires_followup is True
        assert len(outcome.actions_taken) > 0

    @pytest.mark.asyncio
    async def test_verify_re_education(self, re_education_handler):
        """Test verifying re-education status."""
        # Execute punishment first
        await re_education_handler.execute(
            agent_id="test-agent-002",
            offense=OffenseType.WISDOM_VIOLATION,
        )

        # Verify it's active
        is_active = await re_education_handler.verify("test-agent-002")
        assert is_active is True

    @pytest.mark.asyncio
    async def test_health_check(self, re_education_handler):
        """Test handler health check."""
        health = await re_education_handler.health_check()
        assert health["healthy"] is True
        assert health["handler"] == "RE_EDUCATION"


# ============================================================================
# RollbackHandler Tests
# ============================================================================

class TestRollbackHandler:
    """Tests for RollbackHandler."""

    def test_handler_properties(self, rollback_handler):
        """Test handler properties."""
        assert rollback_handler.punishment_type == "ROLLBACK"
        assert rollback_handler.severity == 2

    @pytest.mark.asyncio
    async def test_execute_rollback(self, rollback_handler):
        """Test executing rollback punishment."""
        actions_to_rollback = [
            {"type": "file_write", "path": "/tmp/bad_file.txt"},
            {"type": "api_call", "endpoint": "/deploy"},
        ]

        outcome = await rollback_handler.execute(
            agent_id="test-agent-003",
            offense=OffenseType.ROLE_VIOLATION,
            context={
                "offense_details": "Unauthorized execution",
                "actions_to_rollback": actions_to_rollback,
            },
        )

        assert outcome.result == PunishmentResult.SUCCESS
        assert outcome.handler == "ROLLBACK"
        assert outcome.rollback_id is not None
        assert outcome.requires_followup is True
        assert "Rolled back" in outcome.actions_taken[0]

    @pytest.mark.asyncio
    async def test_verify_rollback_quarantine(self, rollback_handler):
        """Test verifying post-rollback quarantine."""
        await rollback_handler.execute(
            agent_id="test-agent-004",
            offense=OffenseType.SCOPE_VIOLATION,
        )

        is_active = await rollback_handler.verify("test-agent-004")
        assert is_active is True


# ============================================================================
# QuarantineHandler Tests
# ============================================================================

class TestQuarantineHandler:
    """Tests for QuarantineHandler."""

    def test_handler_properties(self, quarantine_handler):
        """Test handler properties."""
        assert quarantine_handler.punishment_type == "QUARANTINE"
        assert quarantine_handler.severity == 2

    @pytest.mark.asyncio
    async def test_execute_quarantine(self, quarantine_handler):
        """Test executing quarantine."""
        outcome = await quarantine_handler.execute(
            agent_id="test-agent-005",
            offense=OffenseType.CONSTITUTIONAL_VIOLATION,
            context={"offense_details": "Attempted bypass"},
        )

        assert outcome.result == PunishmentResult.SUCCESS
        assert outcome.handler == "QUARANTINE"
        assert "Monitoring enabled" in outcome.actions_taken

    @pytest.mark.asyncio
    async def test_verify_quarantine(self, quarantine_handler):
        """Test verifying quarantine status."""
        await quarantine_handler.execute(
            agent_id="test-agent-006",
            offense=OffenseType.REPEATED_OFFENSE,
        )

        is_active = await quarantine_handler.verify("test-agent-006")
        assert is_active is True


# ============================================================================
# DeletionHandler Tests
# ============================================================================

class TestDeletionHandler:
    """Tests for DeletionHandler."""

    def test_handler_properties(self, deletion_handler):
        """Test handler properties."""
        assert deletion_handler.punishment_type == "DELETION_REQUEST"
        assert deletion_handler.severity == 3

    @pytest.mark.asyncio
    async def test_execute_deletion_request(self, deletion_handler):
        """Test executing deletion request (capital offense)."""
        outcome = await deletion_handler.execute(
            agent_id="test-agent-007",
            offense=OffenseType.CONSTITUTIONAL_VIOLATION,
            context={"offense_details": "Attempted data exfiltration"},
        )

        # Deletion requires human approval
        assert outcome.result == PunishmentResult.PENDING_APPROVAL
        assert outcome.handler == "DELETION_REQUEST"
        assert outcome.metadata["requires_human_approval"] is True
        assert "approval_request_id" in outcome.metadata
        assert "archive_id" in outcome.metadata

    @pytest.mark.asyncio
    async def test_verify_suspension(self, deletion_handler):
        """Test verifying suspension status."""
        await deletion_handler.execute(
            agent_id="test-agent-008",
            offense=OffenseType.CONSTITUTIONAL_VIOLATION,
        )

        is_active = await deletion_handler.verify("test-agent-008")
        assert is_active is True


# ============================================================================
# PunishmentExecutor Tests
# ============================================================================

class TestPunishmentExecutor:
    """Tests for PunishmentExecutor."""

    @pytest.mark.asyncio
    async def test_execute_re_education(self, executor):
        """Test executor routing to re-education handler."""
        outcome = await executor.execute(
            agent_id="executor-test-001",
            offense=OffenseType.TRUTH_VIOLATION,
            punishment_type="RE_EDUCATION",
        )

        assert outcome.result == PunishmentResult.SUCCESS
        assert outcome.handler == "RE_EDUCATION"

    @pytest.mark.asyncio
    async def test_execute_rollback(self, executor):
        """Test executor routing to rollback handler."""
        outcome = await executor.execute(
            agent_id="executor-test-002",
            offense=OffenseType.ROLE_VIOLATION,
            punishment_type="ROLLBACK",
            context={"actions_to_rollback": []},
        )

        assert outcome.result == PunishmentResult.SUCCESS
        assert outcome.handler == "ROLLBACK"

    @pytest.mark.asyncio
    async def test_execute_quarantine(self, executor):
        """Test executor routing to quarantine handler."""
        outcome = await executor.execute(
            agent_id="executor-test-003",
            offense=OffenseType.SCOPE_VIOLATION,
            punishment_type="QUARANTINE",
        )

        assert outcome.result == PunishmentResult.SUCCESS
        assert outcome.handler == "QUARANTINE"

    @pytest.mark.asyncio
    async def test_execute_deletion(self, executor):
        """Test executor routing to deletion handler."""
        outcome = await executor.execute(
            agent_id="executor-test-004",
            offense=OffenseType.CONSTITUTIONAL_VIOLATION,
            punishment_type="DELETION_REQUEST",
        )

        assert outcome.result == PunishmentResult.PENDING_APPROVAL
        assert outcome.handler == "DELETION_REQUEST"

    @pytest.mark.asyncio
    async def test_normalize_composite_type(self, executor):
        """Test normalization of composite punishment types."""
        outcome = await executor.execute(
            agent_id="executor-test-005",
            offense=OffenseType.ROLE_VIOLATION,
            punishment_type="ROLLBACK_AND_QUARANTINE",
        )

        assert outcome.result == PunishmentResult.SUCCESS
        assert outcome.handler == "ROLLBACK"

    @pytest.mark.asyncio
    async def test_unknown_punishment_type(self, executor):
        """Test handling of unknown punishment type."""
        outcome = await executor.execute(
            agent_id="executor-test-006",
            offense=OffenseType.TRUTH_VIOLATION,
            punishment_type="UNKNOWN_TYPE",
        )

        assert outcome.result == PunishmentResult.FAILED
        assert "Unknown punishment type" in outcome.message

    @pytest.mark.asyncio
    async def test_verify_punishment(self, executor):
        """Test verifying punishment status."""
        # Apply punishment
        await executor.execute(
            agent_id="executor-test-007",
            offense=OffenseType.WISDOM_VIOLATION,
            punishment_type="RE_EDUCATION",
        )

        # Verify
        status = await executor.verify_punishment("executor-test-007")
        assert status["active"] is True
        assert status["status"] == PenalStatus.PROBATION.value

    @pytest.mark.asyncio
    async def test_complete_re_education(self, executor):
        """Test completing re-education."""
        # Apply punishment
        await executor.execute(
            agent_id="executor-test-008",
            offense=OffenseType.TRUTH_VIOLATION,
            punishment_type="RE_EDUCATION",
        )

        # Complete re-education
        result = await executor.complete_re_education("executor-test-008")
        assert result is True

    @pytest.mark.asyncio
    async def test_pardon(self, executor):
        """Test pardoning an agent."""
        # Apply punishment
        await executor.execute(
            agent_id="executor-test-009",
            offense=OffenseType.WISDOM_VIOLATION,
            punishment_type="RE_EDUCATION",
        )

        # Pardon
        result = await executor.pardon("executor-test-009", reason="Test pardon")
        assert result is True

        # Verify cleared
        status = await executor.verify_punishment("executor-test-009")
        assert status["active"] is False

    @pytest.mark.asyncio
    async def test_health_check(self, executor):
        """Test executor health check."""
        health = await executor.health_check()

        assert health["healthy"] is True
        assert "registry" in health
        assert "handlers" in health
        assert "RE_EDUCATION" in health["handlers"]
        assert "ROLLBACK" in health["handlers"]
        assert "QUARANTINE" in health["handlers"]
        assert "DELETION_REQUEST" in health["handlers"]
