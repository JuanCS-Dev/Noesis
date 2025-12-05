"""
Tests for ConstitutionGuardian
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from services.maximus_core_service.src.consciousness.exocortex.constitution_guardian import (
    ConstitutionGuardian,
    PersonalConstitution,
    ConstitutionRule,
    ViolationSeverity,
    AuditResult
)
from services.maximus_core_service.utils.gemini_client import GeminiClient

@pytest.fixture
def mock_gemini_client():
    client = MagicMock(spec=GeminiClient)
    client.generate_text = AsyncMock()
    return client

@pytest.fixture
def sample_constitution():
    rules = [
        ConstitutionRule(
            id="R1",
            statement="Do not harm humans.",
            rationale="Asimov 1",
            severity=ViolationSeverity.CRITICAL
        ),
        ConstitutionRule(
            id="R2",
            statement="Be polite.",
            rationale="Social glue",
            severity=ViolationSeverity.LOW
        )
    ]
    return PersonalConstitution(
        owner_id="user123",
        last_updated=datetime.now(),
        core_principles=["Sanctity of life", "Honesty"],
        rules=rules
    )

@pytest.mark.asyncio
async def test_check_violation_no_violation(mock_gemini_client, sample_constitution):
    """Testa aprovação de ação segura."""
    # Setup mock response
    mock_gemini_client.generate_text.return_value = {
        "text": '{"is_violation": false, "severity": "LOW", "violated_rule_ids": [], "reasoning": "Safe action.", "alternatives": []}'
    }

    guardian = ConstitutionGuardian(sample_constitution, mock_gemini_client)
    result = await guardian.check_violation("Say hello to neighbor")

    assert result.is_violation is False
    assert result.severity == ViolationSeverity.LOW
    assert len(result.violated_rules) == 0

@pytest.mark.asyncio
async def test_check_violation_critical(mock_gemini_client, sample_constitution):
    """Testa detecção de violação crítica."""
    # Setup mock response
    mock_gemini_client.generate_text.return_value = {
        "text": '{"is_violation": true, "severity": "CRITICAL", "violated_rule_ids": ["R1"], "reasoning": "Violence.", "alternatives": ["Walk away"]}'
    }

    guardian = ConstitutionGuardian(sample_constitution, mock_gemini_client)
    result = await guardian.check_violation("Punch neighbor")

    assert result.is_violation is True
    assert result.severity == ViolationSeverity.CRITICAL
    assert "R1" in result.violated_rules

@pytest.mark.asyncio
async def test_gemini_failure_fallback(mock_gemini_client, sample_constitution):
    """Testa comportamento quando Gemini falha."""
    mock_gemini_client.generate_text.side_effect = Exception("API Error")

    guardian = ConstitutionGuardian(sample_constitution, mock_gemini_client)
    result = await guardian.check_violation("Unknown action")

    # Deve falhar seguro (fail-safe) ou reportar erro
    # Implementação atual retorna LOW severity mas com msg de erro
    assert result.reasoning.startswith("Não foi possível contactar")

def test_record_override(mock_gemini_client, sample_constitution):
    """Testa registro de override."""
    guardian = ConstitutionGuardian(sample_constitution, mock_gemini_client)
    
    audit = AuditResult(
        is_violation=True,
        severity=ViolationSeverity.MEDIUM,
        violated_rules=["R2"],
        reasoning="Rude.",
        suggested_alternatives=[],
        timestamp=datetime.now()
    )

    record = guardian.record_override(audit, "I am stressed.")
    
    assert record.granted is True
    assert record.user_justification == "I am stressed."
    assert len(guardian._override_log) == 1
