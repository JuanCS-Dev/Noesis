"""
Comprehensive Tests for Repository
==================================
Goal: >90% coverage for memory/repository.py
"""
import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from services.maximus_core_service.src.consciousness.exocortex.memory.repository import (
    ConstitutionRepository, 
    ConfrontationRepository
)
from services.maximus_core_service.src.consciousness.exocortex.constitution_guardian import (
    PersonalConstitution, 
    ConstitutionRule, 
    OverrideRecord,
    AuditResult,
    ViolationSeverity
)
from services.maximus_core_service.src.consciousness.exocortex.confrontation_engine import (
    ConfrontationTurn,
    ConfrontationStyle
)

# --- ConstitutionRepository Tests ---

def test_repo_initialization_creates_files(tmp_path):
    repo = ConstitutionRepository(tmp_path)
    assert (tmp_path / "personal_constitution.json").exists()
    assert (tmp_path / "overrides_log.json").exists()
    assert (tmp_path / "overrides_log.json").read_text() == "[]"

def test_load_constitution_defaults(tmp_path):
    # Empty dir -> Should create default
    repo = ConstitutionRepository(tmp_path)
    const = repo.load_constitution()
    assert const.owner_id == "user_001"
    assert "genesis" in const.version

def test_load_constitution_existing(tmp_path):
    data = {
        "owner_id": "test_owner",
        "last_updated": datetime.now().isoformat(),
        "core_principles": ["P1"],
        "rules": [{
            "id": "R1",
            "statement": "S1",
            "rationale": "R1",
            "severity": "HIGH",
            "active": True
        }],
        "version": "1.0"
    }
    (tmp_path / "personal_constitution.json").write_text(json.dumps(data))
    
    repo = ConstitutionRepository(tmp_path)
    const = repo.load_constitution()
    assert const.owner_id == "test_owner"
    assert len(const.rules) == 1
    assert const.rules[0].severity == ViolationSeverity.HIGH

def test_save_constitution(tmp_path):
    repo = ConstitutionRepository(tmp_path)
    const = repo.load_constitution()
    const.owner_id = "modified_owner"
    repo._save_constitution(const)
    
    data = json.loads((tmp_path / "personal_constitution.json").read_text())
    assert data["owner_id"] == "modified_owner"

def test_load_corrupted_json_returns_default(tmp_path):
    (tmp_path / "personal_constitution.json").write_text("{bad_json")
    repo = ConstitutionRepository(tmp_path)
    const = repo.load_constitution()
    assert const.version == "0.1.0-genesis" # Fallback

def test_save_override(tmp_path):
    repo = ConstitutionRepository(tmp_path)
    
    audit = AuditResult(
        is_violation=True,
        severity=ViolationSeverity.MEDIUM,
        violated_rules=["R1"],
        reasoning="Testing",
        suggested_alternatives=["Do nothing"],
        timestamp=datetime.now()
    )
    record = OverrideRecord(
        action_audited="rm -rf /",
        audit_result=audit,
        user_justification="I know what I'm doing",
        granted=True,
        granted_at=datetime.now()
    )
    
    repo.save_override(record)
    
    data = json.loads((tmp_path / "overrides_log.json").read_text())
    assert len(data) == 1
    assert data[0]["action_audited"] == "rm -rf /"
    assert data[0]["audit_result"]["reasoning"] == "Testing"

def test_save_override_with_corrupted_log(tmp_path):
    (tmp_path / "overrides_log.json").write_text("not_a_list")
    repo = ConstitutionRepository(tmp_path)
    
    # Needs a dummy record
    audit = AuditResult(False, ViolationSeverity.LOW, [], "OK", [], datetime.now())
    record = OverrideRecord("ls", audit, "Check", datetime.now(), True)
    
    repo.save_override(record)
    
    data = json.loads((tmp_path / "overrides_log.json").read_text())
    assert len(data) == 1


# --- ConfrontationRepository Tests ---

def test_confrontation_init(tmp_path):
    repo = ConfrontationRepository(tmp_path)
    assert (tmp_path / "confrontation_history.json").exists()

def test_save_turn(tmp_path):
    repo = ConfrontationRepository(tmp_path)
    turn = ConfrontationTurn(
        id="t1",
        timestamp=datetime.now(),
        ai_question="Why?",
        style_used=ConfrontationStyle.DIRECT_CHALLENGE,
        user_response="Because",
        response_analysis={}
    )
    repo.save_turn(turn)
    
    data = json.loads((tmp_path / "confrontation_history.json").read_text())
    assert len(data) == 1
    assert data[0]["id"] == "t1"
    assert data[0]["style_used"] == "DIRECT_CHALLENGE"

def test_save_turn_corrupted_history(tmp_path):
    (tmp_path / "confrontation_history.json").write_text("bad")
    repo = ConfrontationRepository(tmp_path)
    turn = ConfrontationTurn("t1", datetime.now(), "Q", ConfrontationStyle.GENTLE_INQUIRY, "A", {})
    repo.save_turn(turn)
    
    data = json.loads((tmp_path / "confrontation_history.json").read_text())
    assert len(data) == 1

@pytest.mark.asyncio
async def test_get_recent_turns(tmp_path):
    repo = ConfrontationRepository(tmp_path)
    entry = {"id": "1", "q": "a"}
    (tmp_path / "confrontation_history.json").write_text(json.dumps([entry]*10))
    
    turns = await repo.get_recent_turns(limit=3)
    assert len(turns) == 3

@pytest.mark.asyncio
async def test_get_recent_turns_error(tmp_path):
    (tmp_path / "confrontation_history.json").write_text("bad_json")
    repo = ConfrontationRepository(tmp_path)
    turns = await repo.get_recent_turns()
    assert turns == []
