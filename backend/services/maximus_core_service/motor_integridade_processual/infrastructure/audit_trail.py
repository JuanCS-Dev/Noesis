"""Audit trail logging."""

from __future__ import annotations


from typing import List
from datetime import datetime
from motor_integridade_processual.models.verdict import EthicalVerdict

class AuditLogger:
    """Logs all ethical decisions for auditability."""
    
    def __init__(self) -> None:
        self.log: List[dict] = []
    
    def log_decision(self, verdict: EthicalVerdict) -> None:
        """Log a decision to audit trail."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_plan_id": verdict.action_plan_id,
            "decision": verdict.final_decision.value,
            "score": verdict.confidence,  # Using confidence as score proxy
            "confidence": verdict.confidence
        }
        self.log.append(entry)
    
    def get_history(self) -> List[dict]:
        """Retrieve audit history."""
        return self.log.copy()
