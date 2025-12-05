"""
API Schemas for Exocortex
=========================
Pydantic models for Input/Output validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ViolationSeveritySchema(str):
    """Schema para severidade de violação."""

class AuditRequest(BaseModel):
    """Request para auditar ação."""
    action: str
    context: Optional[Dict[str, Any]] = {}

class AuditResponse(BaseModel):
    """Response de auditoria."""
    is_violation: bool
    severity: str
    violated_rules: List[str]
    reasoning: str
    suggested_alternatives: List[str]
    timestamp: datetime

class OverrideRequest(BaseModel):
    """Request para override de violação."""
    justification: str
    original_action: str
    original_audit_result: Dict[str, Any]

class OverrideResponse(BaseModel):
    """Response para override registrado."""
    granted: bool
    record_id: str = "logged_in_memory"

class ConfrontationRequest(BaseModel):
    """Request para gatilhar confrontação."""
    trigger_event: str
    violated_rule_id: Optional[str] = None
    shadow_pattern: Optional[str] = None
    user_state: Optional[str] = "NEUTRAL"

class ConfrontationResponse(BaseModel):
    """Response de confrontação gerada."""
    id: str
    ai_question: str
    style: str # Enum value

class UserResponseRequest(BaseModel):
    """Request para resposta do usuário."""
    confrontation_id: str
    response_text: str

class AnalysisResponse(BaseModel):
    """Response da análise de resposta."""
    honesty_score: float
    defensiveness_score: float
    is_deflection: bool
    insight: Optional[str]

class StimulusRequest(BaseModel):
    """Request para ingestão de estímulo no Tálamo."""
    type: str  # Enum value string
    source: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class ThalamusResponse(BaseModel):
    """Response da decisão do Tálamo."""
    action: str
    reasoning: str
    dopamine_score: float
    urgency_score: float

class ImpulseCheckRequest(BaseModel):
    """Request para checagem de impulso."""
    action_type: str
    content: str
    user_state: Optional[str] = None
    platform: str = "unknown"

class InterventionResponse(BaseModel):
    """Resposta do inibidor."""
    level: str # PAUSE, NOTICE, NONE
    reasoning: str
    wait_time_seconds: int
    socratic_question: Optional[str]
