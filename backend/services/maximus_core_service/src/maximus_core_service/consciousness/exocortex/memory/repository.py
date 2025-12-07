"""
Repositories for Exocortex Data Persistence (JSON Adapter)
==========================================================

Implements simple file-based persistence for Sprint 4.
It handles Constitution loading/saving and Confrontation history.
"""

import json
import logging
from pathlib import Path
from typing import List

from dataclasses import asdict
from datetime import datetime

from maximus_core_service.consciousness.exocortex.constitution_guardian import (
    PersonalConstitution,
    ConstitutionRule,
    OverrideRecord,
    ViolationSeverity
)
from maximus_core_service.consciousness.exocortex.confrontation_engine import (
    ConfrontationTurn
)

logger = logging.getLogger(__name__)

class ConstitutionRepository:
    """Persiste a constituição e os overrides."""

    def __init__(self, data_dir: Path):
        self.constitution_file = data_dir / "personal_constitution.json"
        self.overrides_file = data_dir / "overrides_log.json"
        self._ensure_files()

    def _ensure_files(self):
        """Garante que os arquivos existam."""
        if not self.constitution_file.exists():
            self._save_constitution(self._create_default())
        if not self.overrides_file.exists():
            self.overrides_file.write_text("[]", encoding="utf-8")

    def _create_default(self) -> PersonalConstitution:
        """Cria uma constituição default (Genesis)."""
        return PersonalConstitution(
            owner_id="user_001",
            last_updated=datetime.now(),
            core_principles=[
                "Sovereignty of Intent: My conscious choice is supreme.",
                "Obligation of Truth: Do not deceive or manipulate.",
                "Growth Mindset: Embrace discomfort for evolution."
            ],
            rules=[],
            version="0.1.0-genesis"
        )

    def load_constitution(self) -> PersonalConstitution:
        """Carrega a constituição do disco."""
        try:
            data = json.loads(self.constitution_file.read_text(encoding="utf-8"))

            rules = []
            for r in data.get("rules", []):
                rules.append(ConstitutionRule(
                    id=r["id"],
                    statement=r["statement"],
                    rationale=r["rationale"],
                    severity=ViolationSeverity(r["severity"]),
                    active=r["active"]
                ))

            return PersonalConstitution(
                owner_id=data["owner_id"],
                last_updated=datetime.fromisoformat(data["last_updated"]),
                core_principles=data["core_principles"],
                rules=rules,
                version=data["version"]
            )
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Error loading constitution: %s", e)
            return self._create_default()

    def _save_constitution(self, constitution: PersonalConstitution):
        """Salva a constituição em disco."""
        data = {
            "owner_id": constitution.owner_id,
            "last_updated": constitution.last_updated.isoformat(),
            "core_principles": constitution.core_principles,
            "rules": [
                {
                    "id": r.id,
                    "statement": r.statement,
                    "rationale": r.rationale,
                    "severity": r.severity.value,
                    "active": r.active
                } for r in constitution.rules
            ],
            "version": constitution.version
        }
        self.constitution_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def save_override(self, record: OverrideRecord):
        """Salva um registro de override."""
        try:
            entries = json.loads(self.overrides_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = []

        # Serialize record
        entry = {
            "action_audited": record.action_audited,
            "audit_result": asdict(record.audit_result),
            "user_justification": record.user_justification,
            "granted_at": record.granted_at.isoformat(),
            "granted": record.granted
        }
        # Crude fix for nested datetime in audit_result
        entry["audit_result"]["timestamp"] = record.audit_result.timestamp.isoformat()

        entries.append(entry)
        self.overrides_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


class ConfrontationRepository:
    """Persiste o histórico de confrontações."""

    def __init__(self, data_dir: Path):
        self.history_file = data_dir / "confrontation_history.json"
        if not self.history_file.exists():
            self.history_file.write_text("[]", encoding="utf-8")

    def save_turn(self, turn: ConfrontationTurn):
        """Salva um turno de confrontação."""
        try:
            history = json.loads(self.history_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            history = []

        entry = {
            "id": turn.id,
            "timestamp": turn.timestamp.isoformat(),
            "ai_question": turn.ai_question,
            "style_used": turn.style_used.value,
            "user_response": turn.user_response,
            "response_analysis": turn.response_analysis
        }
        history.append(entry)
        self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

    async def get_recent_turns(self, limit: int = 5) -> List[dict]:
        """Recupera os turnos mais recentes."""
        try:
            history = json.loads(self.history_file.read_text(encoding="utf-8"))
            return history[-limit:]
        except Exception: # pylint: disable=broad-exception-caught
            return []
