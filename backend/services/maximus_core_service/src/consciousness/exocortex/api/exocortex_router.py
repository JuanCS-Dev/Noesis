"""
Exocortex API Router
====================

Endpoints REST para interagir com o Exocórtex.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from services.maximus_core_service.src.consciousness.exocortex.factory import ExocortexFactory
from services.maximus_core_service.src.consciousness.exocortex.api.schemas import (
    AuditRequest, AuditResponse,
    OverrideRequest, OverrideResponse,
    ConfrontationRequest, ConfrontationResponse,
    UserResponseRequest, AnalysisResponse,
    StimulusRequest, ThalamusResponse,
    ImpulseCheckRequest, InterventionResponse
)
from services.maximus_core_service.src.consciousness.exocortex.confrontation_engine import (
    ConfrontationContext,
    ConfrontationStyle,
    ConfrontationTurn
)
from services.maximus_core_service.src.consciousness.exocortex.constitution_guardian import (
    AuditResult, ViolationSeverity
)

from services.maximus_core_service.src.consciousness.exocortex.digital_thalamus import (
    Stimulus, StimulusType, AttentionStatus
)

from services.maximus_core_service.src.consciousness.exocortex.impulse_inhibitor import (
    ImpulseContext
)

router = APIRouter(prefix="/exocortex", tags=["Exocortex"])

def get_factory():
    """Dependency Provider para a Factory."""
    try:
        return ExocortexFactory.get_instance()
    except RuntimeError:
        # Fallback initialization for dev/test if main hasn't run
        return ExocortexFactory.initialize()

@router.post("/audit", response_model=AuditResponse)
async def audit_action(req: AuditRequest, factory: ExocortexFactory = Depends(get_factory)):
    """Audita uma ação contra a Constituição Pessoal."""
    result = await factory.guardian.check_violation(req.action, req.context)

    return AuditResponse(
        is_violation=result.is_violation,
        severity=result.severity.value,
        violated_rules=result.violated_rules,
        reasoning=result.reasoning,
        suggested_alternatives=result.suggested_alternatives,
        timestamp=result.timestamp
    )

@router.post("/override", response_model=OverrideResponse)
async def conscious_override(
    req: OverrideRequest,
    factory: ExocortexFactory = Depends(get_factory)
):
    """Registra um override consciente."""
    # Reconstruir AuditResult (Simplificado)
    # Em produção real, buscaríamos pelo ID do audit.

    audit_data = req.original_audit_result
    audit_obj = AuditResult(
        is_violation=audit_data.get("is_violation", True),
        severity=ViolationSeverity(audit_data.get("severity", "LOW")),
        violated_rules=audit_data.get("violated_rules", []),
        reasoning=audit_data.get("reasoning", ""),
        suggested_alternatives=[],
        timestamp=datetime.now()
    )

    record = factory.guardian.record_override(audit_obj, req.justification)
    # Adicionar campo 'action' que estava faltando
    record.action_audited = req.original_action

    # Persistir
    factory.const_repo.save_override(record)

    return OverrideResponse(granted=True, record_id="persisted")

@router.post("/confront", response_model=ConfrontationResponse)
async def trigger_confrontation(
    req: ConfrontationRequest,
    factory: ExocortexFactory = Depends(get_factory)
):
    """Gera uma questão socrática manualmente."""
    ctx = ConfrontationContext(
        trigger_event=req.trigger_event,
        violated_rule_id=req.violated_rule_id,
        shadow_pattern_detected=req.shadow_pattern,
        user_emotional_state=req.user_state or "NEUTRAL"
    )

    turn = await factory.confrontation_engine.generate_confrontation(ctx)

    # Persistir Turno
    factory.conf_repo.save_turn(turn)

    return ConfrontationResponse(
        id=turn.id,
        ai_question=turn.ai_question,
        style=turn.style_used.value
    )

@router.post("/reply", response_model=AnalysisResponse)
async def user_reply(req: UserResponseRequest, factory: ExocortexFactory = Depends(get_factory)):
    """Avalia a resposta do usuário a um confronto."""
    # Recuperar Turno (Simplificado para MVP)
    # Lógica Real: factory.conf_repo.get_turn(req.confrontation_id)

    # Tentativa de pegar do histórico recente
    turns = await factory.conf_repo.get_recent_turns(10)
    target_turn_data = next((t for t in turns if t["id"] == req.confrontation_id), None)
    if not target_turn_data:
        raise HTTPException(status_code=404, detail="Confrontation not found in recent memory")

    # Rehidratação
    turn = ConfrontationTurn(
        id=target_turn_data["id"],
        timestamp=datetime.fromisoformat(target_turn_data["timestamp"]),
        ai_question=target_turn_data["ai_question"],
        style_used=ConfrontationStyle(target_turn_data["style_used"])
    )

    # Avaliar
    analyzed_turn = await factory.confrontation_engine.evaluate_response(turn, req.response_text)

    # Persistir atualização
    factory.conf_repo.save_turn(analyzed_turn)

    an = analyzed_turn.response_analysis or {}
    return AnalysisResponse(
        honesty_score=an.get("honesty_score", 0.0),
        defensiveness_score=an.get("defensiveness_score", 0.0),
        is_deflection=an.get("is_deflection", False),
        insight=an.get("key_insight", "")
    )

async def ingest_stimulus(
    req: StimulusRequest,
    factory: ExocortexFactory = Depends(get_factory)
):
    """Submete um estímulo ao Digital Thalamus."""
    # Construir objeto interno
    stim = Stimulus(
        id="api_ingest",
        type=StimulusType(req.type),
        source=req.source,
        content=req.content,
        metadata=req.metadata
    )

    # Determinar estado atual (Mockado/Default para Sprint 5)
    # Futuro: Ler do SymbioticSelf
    current_status = AttentionStatus.FOCUS

    decision = await factory.thalamus.ingest(stim, current_status)

    return ThalamusResponse(
        action=decision.action,
        reasoning=decision.reasoning,
        dopamine_score=decision.dopamine_score,
        urgency_score=decision.urgency_score
    )

@router.post("/inhibitor/check", response_model=InterventionResponse)
async def check_impulse(
    req: ImpulseCheckRequest,
    factory: ExocortexFactory = Depends(get_factory)
):
    """Verifica se uma ação é impulsiva/arriscada."""
    ctx = ImpulseContext(
        action_type=req.action_type,
        content=req.content,
        user_state=req.user_state or "NEUTRAL",
        platform=req.platform
    )

    intervention = await factory.inhibitor.check_impulse(ctx)

    return InterventionResponse(
        level=intervention.level.value,
        reasoning=intervention.reasoning,
        wait_time_seconds=intervention.wait_time_seconds,
        socratic_question=intervention.socratic_question
    )
