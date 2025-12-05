"""
Integration Tests for Exocortex API
===================================
Tests internal wiring and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from services.maximus_core_service.main import app
from services.maximus_core_service.src.consciousness.exocortex.factory import ExocortexFactory
from services.maximus_core_service.src.consciousness.exocortex.constitution_guardian import AuditResult, ViolationSeverity
from services.maximus_core_service.src.consciousness.exocortex.confrontation_engine import ConfrontationTurn, ConfrontationStyle

client = TestClient(app)

# Fixtures moved to conftest.py

def test_audit_endpoint(test_factory, mock_gemini):
    # Setup Mock
    mock_gemini.generate_text.return_value = {
        "text": '{"is_violation": true, "severity": "MEDIUM", "violated_rule_ids": ["test"], "reasoning": "bad", "alternatives": []}'
    }
    
    response = client.post("/v1/exocortex/audit", json={
        "action": "delete everything",
        "context": {"user": "admin"}
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_violation"] is True
    assert data["severity"] == "MEDIUM"

def test_override_endpoint(test_factory):
    # Create fake audit context
    original_audit = {
        "is_violation": True,
        "severity": "LOW",
        "violated_rules": [],
        "reasoning": "test",
        "timestamp": datetime.now().isoformat()
    }
    
    response = client.post("/v1/exocortex/override", json={
        "justification": "I know what I am doing",
        "original_action": "rm -rf",
        "original_audit_result": original_audit
    })
    
    assert response.status_code == 200
    assert response.json()["granted"] is True
    
    # Verify persistence
    overrides = test_factory.const_repo.overrides_file.read_text()
    assert "I know what I am doing" in overrides

def test_confrontation_flow(test_factory, mock_gemini):
    # 1. Trigger Confrontation
    mock_gemini.generate_text.return_value = {"text": "Why did you do that?"}
    
    resp_conf = client.post("/v1/exocortex/confront", json={
        "trigger_event": "Laziness",
        "shadow_pattern": "Procrastination"
    })
    assert resp_conf.status_code == 200
    conf_id = resp_conf.json()["id"]
    
    # 2. User Reply
    mock_gemini.generate_text.return_value = {"text": '{"honesty_score": 0.9, "defensiveness_score": 0.1, "is_deflection": false, "key_insight": "good"}'}
    
    resp_reply = client.post("/v1/exocortex/reply", json={
        "confrontation_id": conf_id,
        "response_text": "I was tired."
    })
    assert resp_reply.status_code == 200
    assert resp_reply.json()["honesty_score"] == 0.9

def test_repository_error_handling(test_factory, tmp_path):
    """Test repository behavior when files are corrupted."""
    # Corrupt file
    (tmp_path / "personal_constitution.json").write_text("{invalid_json", encoding="utf-8")
    
    # Repository should load default/genesis
    const = test_factory.const_repo.load_constitution()
    assert const.version == "0.1.0-genesis"

    # Corrupt history
    (tmp_path / "confrontation_history.json").write_text("{bad", encoding="utf-8")
    factory_fresh = ExocortexFactory(str(tmp_path))
    repo = factory_fresh.conf_repo
    
    # Turn saving should fail gracefully (log error, not crash)
    # Actually our save_turn swallows/resets if load fails? No, it initializes empty list on JSONDecodeError
    # Let's test save recovery
    turn = ConfrontationTurn(
        id="test", timestamp=datetime.now(), ai_question="q", style_used=ConfrontationStyle.GENTLE_INQUIRY
    )
    repo.save_turn(turn)
    # Should have overwritten the bad file with new list
    assert "test" in (tmp_path / "confrontation_history.json").read_text()

def test_confrontation_fallback(test_factory, mock_gemini):
    """Test engine fallback when Gemini fails."""
    mock_gemini.generate_text.side_effect = Exception("Gemini Down")
    
    response = client.post("/v1/exocortex/confront", json={
        "trigger_event": "Fail"
    })
    
    assert response.status_code == 200
    assert "Percebo uma dissonância" in response.json()["ai_question"]

def test_check_impulse_endpoint(test_factory, mock_gemini):
    """Testa endpoint /inhibitor/check."""
    mock_gemini.generate_text.return_value = {
        "text": '{"emotional_intensity": 0.9, "irreversibility": 0.9, "alignment": 0.0, "detected_impulse": "RAGE_REPLY", "reasoning": "Furious"}'
    }
    
    payload = {
        "action_type": "send_email",
        "content": "I QUIT!",
        "user_state": "ANGRY",
        "platform": "gmail"
    }
    
    response = client.post("/v1/exocortex/inhibitor/check", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "PAUSE"
    assert "High emotional intensity" in data["reasoning"]
